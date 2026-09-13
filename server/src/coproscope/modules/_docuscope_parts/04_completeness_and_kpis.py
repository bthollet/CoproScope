from __future__ import annotations

from ..core.classement_etabli import (
    doit_remonter_a_l_humain,
    type_doit_remonter_a_l_humain,
)
from ..core.common import _first_present

# --- Completude et indicateurs ----------------------------------------------
#
# Ce que le classement a produit se lit ici: quelles pieces attendues manquent,
# et ce que les indicateurs en disent. Separe du classement lui-meme, qui
# decide du type d'une piece et n'a pas a connaitre la matrice de preuves.


# Le referentiel se declare dans deux langues, et la clef racine du fichier en
# fait partie au meme titre que les champs d'une exigence. `MATRIX_KEY_ALIASES`
# resout deja `preuves` / `proofs` pour une matrice CSV, et `_proof_value`
# resout les champs; seule la racine du referentiel embarque restait litterale.
# Mesure du 2026-09-06, instance reelle de 825 documents sans section
# `matrices`: la branche CSV n'etait pas prise, la branche fichier cherchait
# `proofs` la ou le fichier declare `preuves`, et 0 exigence sur 26 etait
# chargee. Le rapport ecrivait "Pieces attendues: 0" puis, deux sections plus
# bas, "toutes les pieces attendues sont couvertes".
PROOFS_ROOT_KEYS = ("preuves", "proofs")


def _load_proofs(instance) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Rend les exigences attendues, et d'ou elles viennent. L'origine voyage
    avec elles parce que "zero exigence" ne se lit pas tout seul: sans elle, un
    referentiel introuvable et un referentiel vide rendent le meme rapport muet.
    """
    proofs_path = instance.matrix("proofs")
    if proofs_path and proofs_path.exists():
        _, rows = read_csv(proofs_path)
        return rows, {"origine": "matrice declaree par l'instance", "trouve": "oui"}
    rules_path = instance.completeness_rules_path()
    if not rules_path.exists():
        return [], {"origine": "referentiel embarque de CoproScope", "trouve": "non"}
    data = load_structured_file(rules_path)
    rows = _first_present(data, PROOFS_ROOT_KEYS, [])
    return list(rows or []), {"origine": "referentiel embarque de CoproScope", "trouve": "oui"}


def _proof_value(proof: dict[str, str], *names: str) -> str:
    aliases = {
        "proof_id": ("proof_id", "preuve_id", "id"),
        "lot": ("lot", "scope", "perimetre"),
        "expected_label": ("expected_label", "libelle_attendu", "preuve_attendue", "document_attendu"),
        "document_type": ("document_type", "type_document", "document_source"),
        "criticality": ("criticality", "criticite", "priorite", "priority"),
        "freshness_months": ("freshness_months", "validity_months", "max_age_months", "fraicheur_mois", "validite_mois"),
        # Ce qui fonde l'exigence. Champ facultatif, et c'est pour cela qu'il
        # doit etre lu: une exigence qui ne cite aucun texte n'est pas opposable
        # au syndic, et le rapport ne doit pas la presenter comme un manquement.
        # Aucun article n'est devine ici; sans champ, le rapport ecrit
        # "fondement non declare".
        "legal_basis": (
            "legal_basis", "fondement", "fondement_juridique",
            "base_legale", "reference_legale", "article",
        ),
    }
    candidates: list[str] = []
    for name in names:
        candidates.extend(aliases.get(name, (name,)))
    for candidate in candidates:
        value = proof.get(candidate)
        if value not in (None, ""):
            return str(value)
    return ""


def _parse_partial_date(value: str) -> date | None:
    match = re.search(r"(20\d{2})(?:[-_/ .]([01]\d)(?:[-_/ .]([0-3]\d))?)?", value or "")
    if not match:
        return None
    year, month, day = match.groups()
    try:
        return date(int(year), int(month or "1"), int(day or "1"))
    except ValueError:
        return None


def _months_between(older: date, newer: date) -> int:
    months = (newer.year - older.year) * 12 + newer.month - older.month
    if newer.day < older.day:
        months -= 1
    return max(0, months)


def _freshness_months(proof: dict[str, str]) -> int | None:
    raw = _proof_value(proof, "freshness_months")
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _tokenize_for_doubt(*values: str) -> set[str]:
    ignored = {"doc", "document", "documents", "piece", "pieces", "attendu", "attendue", "dossier"}
    tokens: set[str] = set()
    for value in values:
        normalized = re.sub(r"[^a-z0-9]+", " ", value.lower())
        tokens.update(token for token in normalized.split() if len(token) >= 4 and token not in ignored)
    return tokens


# --- Ce que l'outil n'a pas su lire -----------------------------------------
#
# "La piece n'est pas au dossier" et "je n'ai pas su lire la piece" sont deux
# constats differents, et un seul des deux se demande au syndic. Les confondre
# fabrique des relances injustifiees et, surtout, fait disparaitre du rapport
# des documents que la copropriete possede deja.
#
# Mesure du 2026-09-06, instance reelle de 825 documents: 99 portent
# `lot = "A_CLASSER"`, qui n'est le lot d'aucune exigence. Ils n'apparaissaient
# donc nulle part: ni presents, ni manquants, ni meme en doute de classement.
#
# AXE: sur quoi repose le type d'un document.
# INVARIANT: un document inventorie est une piece que la copropriete possede.
#   Seule la solidite de son type varie le long de l'axe; son existence, jamais.
# CE QUE LE CODE EN FAIT: il lit deux champs distincts. `document_type` vide ou
#   portant la valeur reservee de la taxonomie dit qu'aucun type n'a ete decide;
#   `classification_status` dit sur quoi la decision repose - contenu lu, nom de
#   fichier faute de texte, ou doute declare.
# HORS DES VALEURS OBSERVEES: un statut que cette version ne sait pas
#   interpreter n'est pas range en silence dans "classe". Il est nomme
#   "statut inconnu" et ressort a verifier: la degradation va vers le
#   signalement, jamais vers une couverture affirmee a tort.
UNCLASSIFIED_DOCUMENT_TYPE = "A_CLASSER"

# Le seul statut qui affirme les deux a la fois: contenu lu, et type decide.
CLASSIFICATION_READ_STATUS = "AUTO_CLASSIFIED"

READING_GAP_LABELS = {
    "TYPE_NON_DECIDE": "Aucun type n'a pu etre decide. Piece a identifier a la main.",
    "TYPE_SUR_NOM_DE_FICHIER": "Type deduit du seul nom du fichier: le contenu n'a pas pu etre lu.",
    "TYPE_A_REVOIR": "Contenu lu, mais le titre attendu manque. Type a confirmer.",
    "STATUT_INCONNU": "Statut de classement non interprete par cette version. A verifier.",
}

UNREAD_DOCUMENT_FIELDS = [
    "doc_id", "file_name", "lot", "document_type",
    "classification_status", "constat", "explication", "original_path",
]

# Combien de documents non lus le rapport nomme en toutes lettres. Au-dela il
# dit combien il en reste et renvoie au fichier qui les nomme tous: deux cents
# lignes de liste cachent le reste du rapport au lieu de l'eclairer.
UNREAD_SAMPLE_LIMIT = 20


def _reading_gap(doc: dict[str, str]) -> str:
    """Rend le constat de lecture d'un document, ou une chaine vide s'il est lu."""
    doc_type = (doc.get("document_type") or "").strip()
    status = (doc.get("classification_status") or "").strip()
    if not doc_type or doc_type == UNCLASSIFIED_DOCUMENT_TYPE:
        return "TYPE_NON_DECIDE"
    if status == CLASSIFICATION_NO_TEXT_STATUS:
        return "TYPE_SUR_NOM_DE_FICHIER"
    if status == CLASSIFICATION_DOUBT_STATUS:
        return "TYPE_A_REVOIR"
    if status != CLASSIFICATION_READ_STATUS:
        return "STATUT_INCONNU"
    return ""


def _unread_documents(docs: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for doc in docs:
        gap = _reading_gap(doc)
        if not gap:
            continue
        row = {name: doc.get(name, "") for name in UNREAD_DOCUMENT_FIELDS}
        row["constat"] = gap
        row["explication"] = READING_GAP_LABELS[gap]
        rows.append(row)
    return rows


def _classification_doubts(docs: list[dict[str, str]], lot: str, document_type: str, expected_label: str) -> list[dict[str, str]]:
    tokens = _tokenize_for_doubt(lot, document_type, expected_label)
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for doc in docs:
        if doc.get("doc_id") in seen:
            continue
        same_lot = bool(lot and doc.get("lot") == lot)
        haystack = " ".join([doc.get("file_name", ""), doc.get("original_path", ""), doc.get("notes", "")]).lower()
        token_hit = bool(tokens and any(token in haystack for token in tokens))
        # Meme inversion qu'a la boite de reception, et pour la meme raison: la
        # liste `{"", "PENDING", "A_CLASSER"}` qui vivait ici enumerait des
        # modalites, donc une piece mise en doute par le classement ne pouvait
        # pas etre proposee comme la piece manquante - exactement le cas ou elle
        # a le plus de chances de l'etre.
        uncertain = doit_remonter_a_l_humain(doc.get("classification_status", "")) or type_doit_remonter_a_l_humain(doc.get("document_type", ""))
        if (same_lot or token_hit) and uncertain:
            candidates.append(doc)
            seen.add(doc.get("doc_id", ""))
    return candidates


def _evidence_paths(matches: list[dict[str, str]]) -> str:
    values: list[str] = []
    for match in matches:
        path = match.get("original_path") or match.get("text_path") or match.get("file_name", "")
        if path:
            values.append(f"{match.get('doc_id', '')}:{path}")
    return "; ".join(values)


def _matched_doc_ids(matches: list[dict[str, str]]) -> str:
    return "; ".join(match.get("doc_id", "") for match in matches if match.get("doc_id"))


def _build_completeness_rows(docs: list[dict[str, str]], proofs: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    by_lot: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_type: dict[str, list[dict[str, str]]] = defaultdict(list)
    for doc in docs:
        by_lot[doc.get("lot", "")].append(doc)
        by_type[doc.get("document_type", "")].append(doc)

    today = datetime.now(timezone.utc).date()
    matrix_rows: list[dict[str, str]] = []
    action_rows: list[dict[str, str]] = []
    for index, proof in enumerate(proofs, start=1):
        proof_id = _proof_value(proof, "proof_id") or f"PRV-{index:03d}"
        lot = _proof_value(proof, "lot")
        expected_label = _proof_value(proof, "expected_label") or proof_id
        doc_type = _proof_value(proof, "document_type")
        criticality = _proof_value(proof, "criticality") or "P2"
        freshness = _freshness_months(proof)
        matches = by_type.get(doc_type, []) if doc_type else by_lot.get(lot, [])
        dated_matches = [(parsed, match) for match in matches if (parsed := _parse_partial_date(match.get("suspected_date", "")))]
        newest_date = max((parsed for parsed, _ in dated_matches), default=None)

        if matches:
            if freshness and newest_date and _months_between(newest_date, today) > freshness:
                status = "OBSOLETE"
            else:
                status = "PRESENT"
            reason = ""
            if status == "OBSOLETE":
                reason = f"Derniere piece datee {newest_date.isoformat()} au-dela du seuil {freshness} mois."
            else:
                reason = "Piece presente dans le registre documentaire."
        else:
            doubt_matches = _classification_doubts(docs, lot, doc_type, expected_label)
            if doubt_matches:
                matches = doubt_matches
                status = "A_CLASSER"
                reason = "Piece candidate trouvee, mais classement documentaire insuffisant ou incertain."
            else:
                status = "ABSENT"
                reason = "Aucune piece locale ne correspond au type attendu."

        subject, action = _status_action(status, expected_label)
        matrix_row = {
            "proof_id": proof_id,
            "lot": lot,
            "expected_label": expected_label,
            "document_type": doc_type,
            "status": status,
            "criticality": criticality,
            "freshness_months": str(freshness or ""),
            "legal_basis": _proof_value(proof, "legal_basis"),
            "matched_doc_ids": _matched_doc_ids(matches),
            "evidence_paths": _evidence_paths(matches),
            "newest_date": newest_date.isoformat() if newest_date else "",
            "reason": reason,
            "action": action,
        }
        matrix_rows.append(matrix_row)
        if status != "PRESENT":
            action_rows.append(
                {
                    "request_id": f"REQ-DOC-{proof_id}",
                    "source_ref": proof_id,
                    "priority": criticality,
                    "status": status,
                    "subject": subject,
                    "expected_piece": expected_label,
                    "reason": reason,
                    "related_doc_ids": matrix_row["matched_doc_ids"],
                    "evidence_paths": matrix_row["evidence_paths"],
                    "suggested_diligence": action,
                }
            )
    return matrix_rows, action_rows


def _completeness_verdict(
    matrix_rows: list[dict[str, str]],
    action_rows: list[dict[str, str]],
    unread_rows: list[dict[str, str]],
    total_docs: int,
    referential: dict[str, str],
) -> list[str]:
    """Dit ce que le rapport a mesure, avant de dire ce qu'il a trouve.

    Trois cas, pas deux. L'ancienne redaction jugeait sur la seule condition
    "aucune piece a traiter": elle ecrivait donc "toutes les pieces attendues
    sont couvertes" aussi bien quand les exigences etaient satisfaites que
    quand aucune n'avait ete evaluee.
    """
    origine = referential.get("origine", "referentiel non identifie")
    lines: list[str] = ["## Ce que ce rapport a mesure", ""]
    if not matrix_rows:
        cause = (
            "est introuvable"
            if referential.get("trouve") != "oui"
            else "a bien ete trouve, mais il ne declare aucune piece attendue"
        )
        lines += [
            f"**Aucune piece attendue n'a ete evaluee.** Le referentiel utilise ({origine}) {cause}.",
            "",
            "Ce rapport ne dit donc rien sur ce qui manque au dossier. Il ne dit surtout pas que le",
            "dossier est complet: la liste des pieces a demander est vide parce que rien n'a ete",
            "verifie, et non parce que tout serait present.",
        ]
    elif not action_rows:
        lines += [
            f"**{len(matrix_rows)} pieces attendues ont ete evaluees, et les {len(matrix_rows)} sont "
            f"couvertes** par au moins un document du dossier (referentiel utilise: {origine}).",
            "",
            "Ce constat porte sur ces pieces attendues uniquement. Une piece qui ne figure pas dans le",
            "referentiel n'a pas ete cherchee, donc son absence eventuelle n'apparait pas ici.",
        ]
    else:
        covered = len(matrix_rows) - len(action_rows)
        lines.append(
            f"**{len(matrix_rows)} pieces attendues ont ete evaluees: {covered} sont couvertes et "
            f"{len(action_rows)} restent a traiter** (referentiel utilise: {origine})."
        )
    if unread_rows:
        lines += [
            "",
            f"Par ailleurs, {len(unread_rows)} documents sur {total_docs} n'ont pas pu etre lus ou",
            "classes avec certitude. Ils sont nommes plus bas. Ce sont des pieces que la copropriete",
            "possede deja: elles ne comptent ni comme presentes, ni comme absentes, tant que leur",
            "nature n'est pas confirmee.",
        ]
    return lines


def missing_docs(instance, run: RunContext) -> Path:
    _, docs = read_csv(instance.register("documents"))
    proofs, referential = _load_proofs(instance)
    unread_rows = _unread_documents(docs)
    reports_dir = instance.artifact("reports_dir")
    findings_path = instance.register("findings")
    _, existing_findings = read_csv(findings_path)
    report_path = reports_dir / "rapport_completude_documentaire.md"
    matrix_path = reports_dir / "matrice_completude_documentaire.csv"
    requests_path = reports_dir / "pieces_a_demander.csv"
    unread_path = reports_dir / "documents_non_lus.csv"
    matrix_rows, action_rows = _build_completeness_rows(docs, proofs)
    finding_rows: list[dict[str, str]] = []
    for row in matrix_rows:
        if row["status"] != "PRESENT":
            finding_rows.append(
                {
                    "finding_id": f"FDG-{row['proof_id']}",
                    "category": "completeness",
                    "severity": row["criticality"],
                    "source_ref": row["proof_id"],
                    "fact": f"{row['status']}: {row['expected_label']}",
                    "diligence": row["action"],
                    "status": "OPEN",
                }
            )

    lines = _render_completeness_report(
        instance, docs, matrix_rows, action_rows, unread_rows, referential
    ).splitlines()
    extranet_path = instance.matrix("extranet")
    if extranet_path and extranet_path.exists():
        _, extranet_rows = read_csv(extranet_path)
        lines += [
            "",
            "## Matrice extranet reference",
            "",
            "| Scope | Document attendu | Present extranet | Qualification |",
            "|---|---|---|---|",
        ]
        for row in extranet_rows[:30]:
            lines.append(
                f"| {row.get('scope', '')} | {row.get('document_attendu', '')} | "
                f"{row.get('present_extranet', '') or 'A_VERIFIER'} | {row.get('qualification', '')} |"
            )

    write_csv(matrix_path, COMPLETENESS_FIELDS, matrix_rows)
    # UNE file, deux sources (`RM-2026-0088`): voir `demandes_de_divergence`.
    write_csv(requests_path, DOCUMENT_REQUEST_FIELDS, action_rows + demandes_de_divergence(docs))
    write_csv(unread_path, UNREAD_DOCUMENT_FIELDS, unread_rows)
    write_text(report_path, "\n".join(lines) + "\n")
    merged = [row for row in existing_findings if row.get("category") != "completeness"] + finding_rows
    write_csv(findings_path, FINDING_FIELDS, merged)
    run.log_action("write", matrix_path, f"document completeness rows={len(matrix_rows)}")
    run.log_action("write", requests_path, f"document requests rows={len(action_rows)}")
    run.log_action("write", unread_path, f"documents non lus rows={len(unread_rows)}")
    run.log_action("write", report_path, f"missing docs report rows={len(proofs)}")
    run.log_action("write", findings_path, f"findings merged={len(merged)}")
    return report_path


def _pct(part: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{(part / total) * 100:.1f}%"


def compute_kpis(instance, run: RunContext) -> Path:
    kpi_path = instance.register("kpi")
    if kpi_path.exists():
        fields, rows = read_csv(kpi_path)
    else:
        template = instance.register("kpi")
        template.parent.mkdir(parents=True, exist_ok=True)
        template.write_text(load_template_csv("kpi.csv"), encoding="utf-8")
        fields, rows = read_csv(template)
        run.log_action("write", template, "bootstrap kpi register")

    _, docs = read_csv(instance.register("documents"))
    total_docs = len(docs)
    ocr_required = sum(1 for doc in docs if doc.get("status_ocr") == "OCR_REQUIRED")
    # Un document dont aucun texte utile n'a ete lu n'est pas classe: son type
    # ne repose que sur un nom de fichier. Le compter comme classe ferait
    # baisser l'indicateur sans qu'aucune piece ait ete lue.
    # **Troisieme liste de modalites du meme fichier, et la derniere.** Deux
    # avaient ete inversees; celle-ci restait, 380 lignes plus bas, si bien que
    # l'indicateur publie comptait comme CLASSES des documents que la boite de
    # reception montrait comme douteux. Deux comptages concurrents pour la meme
    # notion, dans un seul fichier: le defaut numero un du produit.
    unclassified = sum(
        1 for doc in docs
        if doit_remonter_a_l_humain(doc.get("classification_status", ""))
    )
    request_stats = request_metrics(instance)

    values = {
        "KPI-001": _pct(ocr_required, total_docs),
        "KPI-002": _pct(unclassified, total_docs),
        "KPI-011": _pct(request_stats["traced"], request_stats["total"]),
        "KPI-012": _pct(request_stats["complete"], request_stats["total"]),
    }
    for row in rows:
        kpi_id = row.get("kpi_id", "")
        if kpi_id in values:
            row["value"] = values[kpi_id]
            row["valeur"] = values[kpi_id]
            row["status"] = "CALCULATED"
            row["statut"] = "CALCULE"
    write_csv(kpi_path, list(fields or rows[0].keys() if rows else []), rows)
    run.log_action("write", kpi_path, f"kpi updated ids={','.join(values)}")
    return kpi_path
