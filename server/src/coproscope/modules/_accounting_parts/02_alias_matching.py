from __future__ import annotations



def _load_configured_supplier_due_invoice_triggers(
    instance: InstanceConfig,
    year: int,
    existing_doc_ids: set[str],
) -> list[dict[str, str]]:
    settings = _comptascope_settings(instance)
    if not _as_bool(settings.get("include_cross_year_supplier_due_diligence"), True):
        return []
    candidates = _configured_paths(
        instance,
        settings,
        "invoice_evidence_csv",
        "pre_accounting_invoices",
        "pre_compta_invoices",
        year=year,
    )
    rows: list[dict[str, str]] = []
    seen_doc_ids = set(existing_doc_ids)
    for path in candidates:
        if not path.exists():
            continue
        _, loaded = read_csv(path)
        for index, row in enumerate(loaded, start=1):
            doc_id = row.get("doc_id") or f"INV-{year}-DILIGENCE-{len(rows) + index:04d}"
            if doc_id in seen_doc_ids:
                continue
            anomalies = (row.get("anomalies") or "").replace(" | ", "|")
            candidate = {
                "doc_id": doc_id,
                "sha256": row.get("sha256", ""),
                "source_path": row.get("source_path") or row.get("chemin_piece") or row.get("original_path") or "",
                "file_name": row.get("file_name") or row.get("aliases") or "",
                "exercice": row.get("exercice") or row.get("year") or str(year),
                "fournisseur": row.get("fournisseur") or row.get("supplier") or "",
                "siren_siret": row.get("siren_siret") or row.get("siret") or row.get("siren") or "",
                "numero_facture": row.get("numero_facture") or row.get("invoice_number") or "",
                "date_facture": row.get("date_facture") or row.get("invoice_date") or "",
                "ht": row.get("ht") or row.get("amount_ht") or "",
                "tva": row.get("tva") or row.get("vat") or "",
                "ttc": _money(_decimal(row.get("ttc") or row.get("amount_ttc") or row.get("montant_ttc"))),
                "compte_propose": row.get("compte_propose") or row.get("account") or "",
                "famille_charge": row.get("famille_charge") or row.get("control_family") or "",
                "statut_controle": row.get("statut_controle") or "",
                "confidence": row.get("confidence") or row.get("confiance") or "preloaded",
                "anomalies": anomalies,
                "extraction_method": row.get("extraction_method") or row.get("source_register") or "preloaded_csv",
            }
            if _invoice_is_supplier_due_diligence_trigger(candidate):
                seen_doc_ids.add(doc_id)
                rows.append(candidate)
    return rows


def _supplier_aliases_for(invoice: dict[str, str], aliases: dict[str, set[str]]) -> set[str]:
    supplier = _normal(invoice.get("fournisseur"))
    values = set(aliases.get(supplier, set()))
    if supplier:
        values.add(supplier)
    return values


def _significant_supplier_tokens(value: str) -> set[str]:
    stopwords = {
        "a",
        "au",
        "aux",
        "de",
        "des",
        "du",
        "et",
        "la",
        "le",
        "les",
        "l",
        "sa",
        "sas",
        "sarl",
        "services",
        "service",
        "societe",
    }
    return {token for token in re.split(r"[^a-z0-9]+", _normal(value)) if len(token) >= 3 and token not in stopwords}


def _supplier_match_score(left: str, right: str) -> Decimal:
    left_norm = _normal(left)
    right_norm = _normal(right)
    if not left_norm or not right_norm:
        return Decimal("0")
    if left_norm == right_norm:
        return Decimal("1")
    if left_norm in right_norm or right_norm in left_norm:
        return Decimal("0.95")
    left_tokens = _significant_supplier_tokens(left)
    right_tokens = _significant_supplier_tokens(right)
    if not left_tokens or not right_tokens:
        return Decimal("0")
    overlap = Decimal(len(left_tokens & right_tokens))
    if not overlap:
        return Decimal("0")
    if overlap and len(left_tokens) == 1:
        return Decimal("0.90")
    token_score = overlap / Decimal(max(len(left_tokens), len(right_tokens)))
    left_coverage = overlap / Decimal(len(left_tokens))
    if len(left_tokens) <= 2:
        token_score = max(token_score, left_coverage)
    sequence_score = Decimal(str(SequenceMatcher(None, left_norm, right_norm).ratio()))
    return max(token_score, sequence_score)


def _supplier_text_match_score(supplier: str, text: str) -> Decimal:
    supplier_norm = _normal(supplier)
    text_norm = _normal(text)
    if not supplier_norm or not text_norm:
        return Decimal("0")
    if supplier_norm in text_norm:
        return Decimal("0.95")
    supplier_tokens = _significant_supplier_tokens(supplier)
    supplier_tokens_for_text = supplier_tokens - {"renovation"} if len(supplier_tokens) > 1 else supplier_tokens
    text_tokens = _significant_supplier_tokens(text)
    if not supplier_tokens_for_text or not text_tokens:
        return Decimal("0")
    overlap = len(supplier_tokens_for_text & text_tokens)
    if not overlap:
        return Decimal("0")
    if overlap == len(supplier_tokens_for_text):
        return Decimal("0.90")
    if len(supplier_tokens_for_text) <= 2:
        return Decimal(str(overlap / len(supplier_tokens_for_text)))
    return Decimal(str(overlap / max(len(supplier_tokens_for_text), len(text_tokens))))


def _row_actor(row: dict[str, str]) -> str:
    return (
        row.get("acteur")
        or row.get("cible")
        or row.get("producteur_piece")
        or row.get("supplier")
        or row.get("fournisseur")
        or ""
    )


def _row_search_text(row: dict[str, str]) -> str:
    fields = [
        "acteur",
        "cible",
        "producteur_piece",
        "supplier",
        "fournisseur",
        "fact_summary",
        "extract",
        "expected_evidence",
        "next_action",
        "notes",
        "chantier",
        "fait",
        "en_cours",
        "prochaine_action",
        "documents_attendus",
        "sortie_attendue",
        "lot",
        "procedure_id",
        "diligence_id",
    ]
    return " ".join(str(row.get(field) or "") for field in fields)


def _row_reference(row: dict[str, str]) -> str:
    identifier = (
        row.get("resultat_id")
        or row.get("controle_id")
        or row.get("constat_id")
        or row.get("procedure_id")
        or row.get("id")
        or row.get("acteur")
        or row.get("cible")
        or row.get("producteur_piece")
        or row.get("_source_file")
        or ""
    )
    source = row.get("_source_file", "")
    if source and source not in identifier:
        return f"{identifier} ({source})"
    return identifier


def _matching_rows(
    supplier: str,
    rows: list[dict[str, str]],
    threshold: Decimal = Decimal("0.72"),
    aliases: set[str] | None = None,
) -> list[dict[str, str]]:
    candidate_names = {supplier, *(aliases or set())}
    candidate_names = {name for name in candidate_names if name}
    matches: list[tuple[Decimal, dict[str, str]]] = []
    for row in rows:
        actor = _row_actor(row)
        search_text = _row_search_text(row)
        actor_score = max((_supplier_match_score(name, actor) for name in candidate_names), default=Decimal("0"))
        text_score = max(
            (_supplier_text_match_score(name, search_text) for name in candidate_names),
            default=Decimal("0"),
        )
        score = max(actor_score, text_score)
        if score >= threshold:
            matches.append((score, row))
    matches.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in matches]


def _invoice_is_supplier_due_diligence_trigger(row: dict[str, str]) -> bool:
    anomalies = row.get("anomalies", "")
    return any(token in anomalies for token in ("DILIGENCE_REQUISE", "DILIGENCE_A_EVALUER"))


def _invoice_due_diligence_codes(row: dict[str, str]) -> list[str]:
    supplier = row.get("fournisseur", "")
    haystack = _normal(
        " ".join(
            [
                supplier,
                row.get("famille_charge", ""),
                row.get("compte_propose", ""),
                row.get("numero_facture", ""),
                row.get("anomalies", ""),
            ]
        )
    )
    codes = ["DIL-DD-003"]
    if "siren_siret_absent" in haystack:
        codes.append("DIL-DD-003")
    if any(token in haystack for token in ["ripert", "assur", "orias", "courtier"]):
        codes.extend(["DIL-DD-007", "DIL-DD-009", "DIL-DD-011", "DIL-DD-016"])
    if any(
        token in haystack
        for token in [
            "travaux",
            "plomberie",
            "ascenseur",
            "omega",
            "vincentelli",
            "services",
            "elagage",
            "maintenance",
        ]
    ):
        codes.extend(["DIL-DD-005", "DIL-DD-009", "DIL-DD-015", "DIL-DD-017"])
    return list(dict.fromkeys(codes))


def _admin_controls_for_codes(admin_rows: list[dict[str, str]], codes: list[str]) -> list[dict[str, str]]:
    wanted = set(codes)
    selected: list[dict[str, str]] = []
    for row in admin_rows:
        linked = {item.strip() for item in re.split(r"[;|]", row.get("diligence_liee", "")) if item.strip()}
        if wanted & linked:
            selected.append(row)
    selected.sort(key=lambda row: (row.get("priorite", "P9"), row.get("controle_id", "")))
    return selected


def _supplier_dd_action(row: dict[str, str], codes: list[str]) -> str:
    supplier = _normal(row.get("fournisseur", ""))
    if "ripert" in supplier or "assur" in supplier:
        return (
            "Rattacher contrat/police, RIB et paiement; verifier ORIAS/mandat si intermediation, "
            "commissions/remunerations et information CS/AG."
        )
    if any(code in codes for code in ["DIL-DD-005", "DIL-DD-017"]):
        return (
            "Rattacher decision/devis ou urgence, consultation CS/mise en concurrence, service fait, "
            "assurance/qualification, reception si applicable, RIB et paiement."
        )
    return "Verifier identite juridique, SIREN/SIRET, RNE/INPI, RIB, paiement et piece primaire fournisseur."


def build_supplier_due_diligence_controls(
    instance: InstanceConfig,
    invoices: list[dict[str, str]],
    year: int,
) -> list[dict[str, str]]:
    settings = _supplier_due_diligence_settings(instance)
    method_paths = _configured_paths_no_year(instance, settings, "method_plan", "plan", "methodology")
    worklist_rows = _load_rows_with_source(
        _configured_paths_no_year(instance, settings, "worklist_csv", "worklists", "worklist")
    )
    result_rows = _load_rows_with_source(
        _configured_paths_no_year(instance, settings, "result_csv", "result_csvs", "results")
    )
    admin_rows = _load_rows_with_source(
        _configured_paths_no_year(instance, settings, "admin_controls_csv", "admin_controls", "control_matrix")
    )
    supplier_aliases = _load_supplier_aliases(instance)
    try:
        result_threshold = Decimal(str(settings.get("result_match_threshold", "0.50")))
    except Exception:
        result_threshold = Decimal("0.50")

    rows: list[dict[str, str]] = []
    for invoice in invoices:
        if not _invoice_is_supplier_due_diligence_trigger(invoice):
            continue
        supplier = invoice.get("fournisseur", "") or "FOURNISSEUR_A_IDENTIFIER"
        codes = _invoice_due_diligence_codes(invoice)
        aliases = supplier_aliases.get(_normal(supplier), set())
        matching_worklist = _matching_rows(supplier, worklist_rows, aliases=aliases)
        matching_results = _matching_rows(supplier, result_rows, threshold=result_threshold, aliases=aliases)
        controls = _admin_controls_for_codes(admin_rows, codes)
        if matching_results:
            coverage = "COUVERT_RECENT_A_RECOUPER"
        elif matching_worklist:
            coverage = "DANS_PLAN_EXISTANT_A_COMPLETER"
        else:
            coverage = "A_TRAITER_METHODO_EXISTANTE"

        controls_summary = "; ".join(
            f"{row.get('controle_id', '')}: {row.get('controle_a_produire', '')}".strip(": ")
            for row in controls[:8]
        )
        if not controls_summary and codes:
            controls_summary = "Appliquer les controles du plan existant lies a " + "; ".join(codes)
        method_sources = "; ".join(path.name for path in method_paths if path.exists())
        if admin_rows:
            admin_sources = sorted({row.get("_source_file", "") for row in admin_rows if row.get("_source_file")})
            if admin_sources:
                method_sources = "; ".join([item for item in [method_sources, *admin_sources] if item])

        rows.append(
            {
                "doc_id": invoice.get("doc_id", ""),
                "exercice": str(year),
                "fournisseur": supplier,
                "siren_siret": invoice.get("siren_siret", ""),
                "numero_facture": invoice.get("numero_facture", ""),
                "date_facture": invoice.get("date_facture", ""),
                "ttc": invoice.get("ttc", ""),
                "trigger_anomalies": invoice.get("anomalies", ""),
                "coverage_status": coverage,
                "diligence_liee": "; ".join(codes),
                "method_sources": method_sources,
                "existing_worklist_refs": "; ".join(_row_reference(row) for row in matching_worklist[:5]),
                "existing_result_refs": "; ".join(_row_reference(row) for row in matching_results[:5]),
                "controls_to_apply": controls_summary,
                "next_action": _supplier_dd_action(invoice, codes),
            }
        )
    rows.sort(
        key=lambda row: (
            {"COUVERT_RECENT_A_RECOUPER": 2, "DANS_PLAN_EXISTANT_A_COMPLETER": 1}.get(
                row.get("coverage_status", ""), 0
            ),
            -(_decimal(row.get("ttc")) or Decimal("0")),
            row.get("fournisseur", ""),
        )
    )
    return rows


def _line_text(line: dict[str, str]) -> str:
    return " ".join(
        [
            line.get("supplier_hint", ""),
            line.get("reference", ""),
            line.get("label", ""),
            line.get("account", ""),
            line.get("account_label", ""),
        ]
    )


def _statement_alias_candidate_with_source(line: dict[str, str]) -> tuple[str, str]:
    hint = normalize_statement_alias(line.get("supplier_hint", ""))
    if hint:
        return hint, "supplier_hint"
    label = line.get("label", "")
    if "/" in label:
        left = label.split("/", 1)[0]
        left = re.sub(r"^\s*[A-Z0-9._-]{3,24}\s+", "", left)
        alias = normalize_statement_alias(left)
        if alias:
            return alias, "label_prefix"
    return "", ""


def _statement_alias_candidate(line: dict[str, str]) -> str:
    return _statement_alias_candidate_with_source(line)[0]


def normalize_statement_alias(value: str) -> str:
    text = re.sub(r"\s+", " ", value or "").strip(" -_/")
    normalized = _normal(text)
    if not normalized:
        return ""
    weak = {
        "assur",
        "assurance",
        "avoir",
        "cb",
        "cheque",
        "const",
        "demeure",
        "dos",
        "dossier",
        "facture",
        "honoraires",
        "mise",
        "paiement",
        "prelevement",
        "rar",
        "reglement",
        "suivi",
        "vac",
        "vacation",
        "virement",
    }
    tokens = [token for token in re.split(r"[^a-z0-9]+", normalized) if token]
    if not tokens or all(token in weak or token.isdigit() for token in tokens):
        return ""
    return text


def _supplier_match_kind(invoice: dict[str, str], line: dict[str, str], aliases: dict[str, set[str]]) -> str:
    haystack = _normal(_line_text(line))
    supplier = _normal(invoice.get("fournisseur"))
    if supplier and supplier in haystack:
        return "supplier"
    supplier_tokens = _significant_supplier_tokens(invoice.get("fournisseur", ""))
    if supplier_tokens and len(supplier_tokens) <= 2 and supplier_tokens.issubset(set(re.split(r"[^a-z0-9]+", haystack))):
        return "supplier"
    for alias in _supplier_aliases_for(invoice, aliases):
        if alias and alias != supplier and alias in haystack:
            return "alias"
    return ""


def _supplier_similarity(left: str, right: str) -> Decimal:
    left_norm = _normal(left)
    right_norm = _normal(right)
    if not left_norm or not right_norm:
        return Decimal("0")
    if left_norm in right_norm or right_norm in left_norm:
        return Decimal("1")
    left_tokens = _significant_supplier_tokens(left_norm)
    right_tokens = _significant_supplier_tokens(right_norm)
    token_score = Decimal("0")
    if left_tokens and right_tokens:
        common = left_tokens & right_tokens
        token_score = Decimal(len(common) * 2) / Decimal(len(left_tokens) + len(right_tokens))
    sequence_score = Decimal(str(SequenceMatcher(None, left_norm, right_norm).ratio()))
    return max(token_score, sequence_score)


def _similar_supplier_evidence(invoice: dict[str, str], line: dict[str, str]) -> tuple[str, Decimal]:
    candidates = [
        line.get("supplier_hint", ""),
        _statement_alias_candidate(line),
    ]
    label = line.get("label", "")
    if "/" in label:
        candidates.append(label.split("/", 1)[0])
    best_name = ""
    best_score = Decimal("0")
    for candidate in candidates:
        score = _supplier_similarity(invoice.get("fournisseur", ""), candidate)
        if score > best_score:
            best_score = score
            best_name = candidate
    return best_name, best_score


def _family_matches(invoice: dict[str, str], line: dict[str, str]) -> bool:
    account = re.sub(r"\D", "", line.get("account", ""))
    proposed = re.sub(r"\D", "", invoice.get("compte_propose", ""))
    family = invoice.get("famille_charge", "")
    if account and proposed and account[:3] == proposed[:3]:
        return True
    prefixes = {
        "energie_eau": ("601", "602", "606"),
        "entretien_maintenance": ("611", "614", "615"),
        "honoraires_syndic": ("622",),
        "assurance": ("616",),
        "charges_exceptionnelles": ("671",),
    }
    return bool(account and family in prefixes and account.startswith(prefixes[family]))


def _invoice_duplicate_key(invoice: dict[str, str]) -> str:
    return f"{_normal(invoice.get('fournisseur'))}|{_money(_decimal(invoice.get('ttc')))}"
