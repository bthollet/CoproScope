from __future__ import annotations



def _write_accounting_outputs(source: InstanceConfig, instance_dir: Path, year: int, source_summary: dict[str, Any]) -> None:
    source_base = _source_accounting_dir(source, year)
    accounting_dir = instance_dir / "outputs" / "accounting" / str(year)
    invoice_count = _demo_count(source_summary.get("invoice_count"), 6, 96)
    control_count = _demo_count(source_summary.get("control_count"), 4, 36)
    anomaly_count = _demo_count(source_summary.get("invoice_anomaly_count"), 3, 48)
    statement_count = _demo_count(source_summary.get("expense_statement_line_count"), 8, 120)

    invoice_fields = _fields_from(
        source_base / f"invoice_evidence_{year}.csv",
        ["doc_id", "exercice", "fournisseur", "numero_facture", "date_facture", "ttc", "compte_propose", "famille_charge", "statut_controle", "confidence", "evidence_level"],
    )
    invoices = [
        {
            "doc_id": f"DEMO-FAC-{index:03d}",
            "exercice": str(year),
            "fournisseur": ["JARDINS DES TILLEULS SERVICES", "ATELIER TOITURE DEMO", "NETTOYAGE HORIZON"][index % 3],
            "numero_facture": f"DEMO-{year}-{index:03d}",
            "date_facture": f"{year}-{(index % 9) + 1:02d}-15",
            "ttc": f"{850 + index * 37:.2f}",
            "compte_propose": "615000",
            "famille_charge": "entretien_maintenance",
            "statut_controle": "PROBABLE",
            "confidence": "demo_fictive",
            "evidence_level": "L1_SYNTHETIC_TEXT",
            "source_register": "demo_fictive",
        }
        for index in range(1, min(invoice_count, 18) + 1)
    ]
    write_csv(accounting_dir / f"invoice_evidence_{year}.csv", invoice_fields, _project(invoice_fields, invoices))

    control_fields = _fields_from(
        source_base / f"accounting_controls_{year}.csv",
        ["control_id", "exercice", "severity", "control", "status", "doc_id", "evidence", "action"],
    )
    controls = [
        {
            "control_id": f"CTL-DEMO-{index:03d}",
            "exercice": str(year),
            "severity": "P1" if index in {1, 2} else "P2",
            "control": [
                "Rapprocher facture et etat des depenses",
                "Verifier piece administrative fournisseur",
                "Confirmer ventilation de charge",
                "Preparer question AG",
            ][index % 4],
            "status": "A_TRAITER" if index in {1, 2} else "A_CONFIRMER",
            "doc_id": f"DEMO-FAC-{index:03d}",
            "evidence": "Piece fictive et ligne comptable synthetique",
            "action": "Preparer une question au syndic avec piece attendue.",
        }
        for index in range(1, min(control_count, 12) + 1)
    ]
    write_csv(accounting_dir / f"accounting_controls_{year}.csv", control_fields, _project(control_fields, controls))

    non_match_fields = _fields_from(
        source_base / f"non_rapproches_prioritaires_{year}.csv",
        ["doc_id", "fournisseur", "numero_facture", "ttc", "match_status", "match_priority", "status_label", "match_reason", "next_action"],
    )
    non_matches = [
        {
            "doc_id": "DEMO-FAC-001",
            "fournisseur": "ATELIER TOITURE DEMO",
            "numero_facture": f"DEMO-{year}-001",
            "ttc": "14600.00",
            "match_status": "CANDIDAT_REFERENCE_AMBIGUE",
            "match_priority": "P1",
            "status_label": "Question syndic",
            "match_reason": "La reference comptable ne suffit pas pour rattacher la piece au bon poste.",
            "next_action": "Demander le detail de ligne et la piece justificative associee.",
        },
        {
            "doc_id": "DEMO-FAC-002",
            "fournisseur": "NETTOYAGE HORIZON",
            "numero_facture": f"DEMO-{year}-002",
            "ttc": "960.00",
            "match_status": "CANDIDAT_MONTANT_AMBIGU",
            "match_priority": "P2",
            "status_label": "A confirmer",
            "match_reason": "Plusieurs lignes proches existent dans l'etat de depenses fictif.",
            "next_action": "Confirmer le rattachement avant AG.",
        },
    ]
    write_csv(accounting_dir / f"non_rapproches_prioritaires_{year}.csv", non_match_fields, _project(non_match_fields, non_matches))

    match_fields = _fields_from(
        source_base / f"invoice_expense_matches_{year}.csv",
        ["doc_id", "statement_line_id", "match_status", "match_priority", "match_reason", "next_action"],
    )
    matches = [
        {
            "doc_id": f"DEMO-FAC-{index:03d}",
            "statement_line_id": f"DEP-DEMO-{index:03d}",
            "match_status": "MATCH_AMOUNT_SUPPLIER" if index % 3 else "CANDIDAT_MONTANT_AMBIGU",
            "match_priority": "OK" if index % 3 else "P2",
            "match_reason": "Rapprochement fictif coherent avec l'etat de depenses.",
            "next_action": "Conserver comme preuve candidate.",
        }
        for index in range(1, min(invoice_count, 18) + 1)
    ]
    write_csv(accounting_dir / f"invoice_expense_matches_{year}.csv", match_fields, _project(match_fields, matches))

    anomaly_fields = _fields_from(
        source_base / f"invoice_anomalies_{year}.csv",
        ["doc_id", "anomaly", "severity", "message", "next_action"],
    )
    anomalies = [
        {
            "doc_id": f"DEMO-FAC-{(index % 6) + 1:03d}",
            "anomaly": "PIECE_A_CONFIRMER",
            "severity": "P2",
            "message": "Anomalie fictive pour tester la lecture guidee.",
            "next_action": "Verifier la piece avant restitution.",
        }
        for index in range(1, min(anomaly_count, 12) + 1)
    ]
    write_csv(accounting_dir / f"invoice_anomalies_{year}.csv", anomaly_fields, _project(anomaly_fields, anomalies))

    expense_fields = _fields_from(
        source_base / f"expense_statement_lines_{year}.csv",
        ["statement_line_id", "exercice", "account", "label", "amount", "supplier_hint"],
    )
    expenses = [
        {
            "statement_line_id": f"DEP-DEMO-{index:03d}",
            "exercice": str(year),
            "account": "615000",
            "label": f"Ligne de charge fictive {index:03d}",
            "amount": f"{850 + index * 37:.2f}",
            "supplier_hint": ["JARDINS", "TOITURE", "NETTOYAGE"][index % 3],
        }
        for index in range(1, min(statement_count, 24) + 1)
    ]
    write_csv(accounting_dir / f"expense_statement_lines_{year}.csv", expense_fields, _project(expense_fields, expenses))

    ledger_fields = _fields_from(
        source_base / f"ledger_reconstruction_{year}.csv",
        ["entry_id", "doc_id", "exercice", "account", "label", "debit", "credit", "source"],
    )
    ledger = [
        {
            "entry_id": f"LED-DEMO-{index:03d}",
            "doc_id": f"DEMO-FAC-{index:03d}",
            "exercice": str(year),
            "account": "615000",
            "label": f"Ecriture candidate fictive {index:03d}",
            "debit": f"{850 + index * 37:.2f}",
            "credit": "0.00",
            "source": "demo_fictive",
        }
        for index in range(1, min(invoice_count, 18) + 1)
    ]
    write_csv(accounting_dir / f"ledger_reconstruction_{year}.csv", ledger_fields, _project(ledger_fields, ledger))

    alias_fields = _fields_from(
        source_base / f"supplier_alias_suggestions_{year}.csv",
        ["supplier", "suggested_alias", "evidence_count", "suggestion_status", "next_action"],
    )
    write_csv(
        accounting_dir / f"supplier_alias_suggestions_{year}.csv",
        alias_fields,
        _project(
            alias_fields,
            [
                {
                    "supplier": "JARDINS DES TILLEULS SERVICES",
                    "suggested_alias": "JARDINS TILLEULS",
                    "evidence_count": "3",
                    "suggestion_status": "A_CONFIRMER",
                    "next_action": "Ajouter l'alias si le CS valide le rapprochement.",
                }
            ],
        ),
    )

    due_fields = _fields_from(
        source_base / f"supplier_due_diligence_controls_{year}.csv",
        ["fournisseur", "coverage_status", "controls_to_apply", "existing_result_refs", "next_action"],
    )
    write_csv(
        accounting_dir / f"supplier_due_diligence_controls_{year}.csv",
        due_fields,
        _project(
            due_fields,
            [
                {
                    "fournisseur": "ATELIER TOITURE DEMO",
                    "coverage_status": "A_TRAITER_METHODO_EXISTANTE",
                    "controls_to_apply": "Assurance;qualification;identite juridique",
                    "existing_result_refs": "",
                    "next_action": "Demander les pieces avant engagement.",
                }
            ],
        ),
    )

    summary = {
        "status": "ok",
        "mode": "demo_fictive",
        "year": year,
        "invoice_count": invoice_count,
        "entry_count": min(invoice_count, 18),
        "control_count": control_count,
        "invoice_anomaly_count": anomaly_count,
        "expense_statement_line_count": statement_count,
        "expense_match_counts": {
            "MATCH_AMOUNT_SUPPLIER": max(1, invoice_count - 4),
            "CANDIDAT_MONTANT_AMBIGU": 3,
            "CANDIDAT_REFERENCE_AMBIGUE": 1,
        },
        "publication_note": "Jeu fictif derive par generalisation, sans copie de lignes privees.",
    }
    _json(accounting_dir / f"summary_{year}.json", summary)
    write_text(
        accounting_dir / f"rapport_comptascope_{year}.md",
        "\n".join(
            [
                "# Rapport ComptaScope demo",
                "",
                "Ce rapport est entierement fictif. Il sert a tester l'interface cible sans publier de donnees reelles.",
                "",
                "## Lecture rapide",
                "",
                "- Des rapprochements `OK` montrent la chaine preuve -> controle.",
                "- Des candidats `P2` montrent les confirmations attendues.",
                "- Des `P1` montrent les questions a preparer au syndic.",
                "",
                "## Point prioritaire",
                "",
                "Demander le detail de la ligne travaux et la piece justificative associee.",
            ]
        )
        + "\n",
    )


def _write_reports(instance_dir: Path, year: int, profile: dict[str, str], validation: dict[str, str]) -> None:
    reports = instance_dir / "outputs" / "reports"
    write_text(
        reports / "rapport_completude_documentaire.md",
        "\n".join(
            [
                "# Rapport de completude documentaire demo",
                "",
                "Instance fictive produite pour tester le cockpit CoproScope.",
                "",
                "- Documents presents: facture, annexe comptable, demande syndic, devis, AG, incident.",
                "- Pieces a demander: assurance prestataire, calendrier travaux, preuve de cloture incident.",
            ]
        )
        + "\n",
    )
    write_text(
        reports / "rapport_ag_preparation.md",
        "\n".join(
            [
                "# Rapport AG demo",
                "",
                "- Resolution travaux a relier a une action suivie.",
                "- Annexes a verifier avant diffusion.",
                "- Questions au syndic a preparer depuis ComptaScope.",
            ]
        )
        + "\n",
    )
    demo_dir = instance_dir / "outputs" / "demo"
    write_text(
        demo_dir / "rapport_validation_publication.md",
        "\n".join(
            [
                "# Rapport de validation publication",
                "",
                "## Statut",
                "",
                f"- Decision: {validation['decision']}",
                f"- Individualisation: {validation['individualisation']}",
                f"- Correlation: {validation['correlation']}",
                f"- Inference: {validation['inference']}",
                "",
                "## Source privee",
                "",
                "Les volumes sources ont ete generalises avant generation de la demo.",
                "",
                "| Signal | Niveau generalise |",
                "| --- | --- |",
                *[f"| {key} | {value} |" for key, value in profile.items()],
                "",
                "## Regle",
                "",
                "Une pseudonymisation tracee n'est pas consideree comme une publication suffisante. Cette instance publie une copro fictive.",
            ]
        )
        + "\n",
    )


def _write_instance_config(instance_dir: Path) -> Path:
    payload = {
        "version": 1,
        "instance_id": DEMO_ID,
        "display_name": DEMO_NAME,
        "scope": "copro_demo_fictive",
        "entity_id": "main",
        "roots": {
            "workspace": ".",
            "raw": "./raw",
            "system": "./system",
            "outputs": "./outputs",
            "staging": "./staging",
            "logs": "./logs",
            "restricted": ["./restricted/C8_local_only"],
        },
        "registers": {
            "documents": "./registers/registre_documents.csv",
            "duplicates": "./registers/registre_doublons.csv",
            "manifest": "./registers/manifest_sha256.csv",
            "requests": "./registers/registre_demandes.csv",
            "ag": "./registers/registre_ag.csv",
            "findings": "./registers/constats_diligences.csv",
            "kpi": "./registers/kpi.csv",
            "privacy_screening": "./outputs/privacy/registre_screening_confidentialite.csv",
            "redactions": "./outputs/privacy/registre_biffages.csv",
            "redaction_map": "./restricted/C8_local_only/table_correspondance_biffage.csv",
        },
        "matrices": {
            "proofs": "./system/matrices/matrice_preuves_attendues.csv",
            "extranet": "./system/matrices/matrice_conformite_extranet.csv",
            "due_diligence_dir": "./system/due_diligence",
        },
        "artifacts": {
            "text_dir": "./staging/text",
            "classified_dir": "./staging/classified",
            "reports_dir": "./outputs/reports",
            "docai_dir": "./staging/docai",
            "accounting_dir": "./outputs/accounting",
            "grist_dir": "./outputs/grist",
            "evidence_dir": "./outputs/evidence",
            "privacy_dir": "./outputs/privacy",
            "redacted_dir": "./outputs/redacted",
        },
        "env": {"files": ["./.env.local"], "required": [], "optional": []},
        "settings": {
            "never_modify_raw": True,
            "write_outputs_only": True,
            "demo_publication": {
                "mode": "fictive",
                "source_private_content_copied": False,
                "pseudonymization_only_is_publishable": False,
            },
        },
    }
    path = instance_dir / "instance.yml"
    _json(path, payload)
    return path


def _write_support_files(instance_dir: Path) -> None:
    write_text(
        instance_dir / ".gitignore",
        "\n".join(
            [
                ".env.local",
                "logs/",
                "restricted/",
                "**/table_correspondance*",
                "**/*mapping*",
                "",
            ]
        ),
    )
    matrices = instance_dir / "system" / "matrices"
    write_csv(
        matrices / "matrice_preuves_attendues.csv",
        ["proof_id", "theme", "piece_attendue", "raison", "priorite"],
        [
            {
                "proof_id": "PROOF-DEMO-001",
                "theme": "Travaux",
                "piece_attendue": "Attestation assurance",
                "raison": "Verifier la couverture avant reception.",
                "priorite": "P1",
            }
        ],
    )
    write_csv(
        matrices / "matrice_conformite_extranet.csv",
        ["item_id", "piece", "status", "action"],
        [
            {
                "item_id": "EXT-DEMO-001",
                "piece": "Devis travaux",
                "status": "A_COMPLETER",
                "action": "Demander les annexes manquantes.",
            }
        ],
    )


def _validate_generated_instance(instance_dir: Path) -> dict[str, str]:
    forbidden = re.compile(r"\b(beauvallon|pinede|pin[eè]de)\b", flags=re.IGNORECASE)
    direct_identifier = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|\bFR\d{2}(?:[\s-]?[A-Z0-9]){11,30}\b",
        flags=re.IGNORECASE,
    )
    scanned = 0
    blocked = False
    for path in sorted(instance_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part in {"restricted", "logs"} for part in path.parts):
            continue
        if path.suffix.lower() not in {".txt", ".md", ".csv", ".json", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        if forbidden.search(text) or direct_identifier.search(text):
            blocked = True
            break
    if blocked:
        return {
            "decision": "BLOCKED_REVIEW_REQUIRED",
            "individualisation": "A_REVOIR",
            "correlation": "A_REVOIR",
            "inference": "A_REVOIR",
            "scanned_files": str(scanned),
        }
    return {
        "decision": "APPROVED_FICTIVE_DEMO",
        "individualisation": "OK_GENERALISE",
        "correlation": "OK_IDENTITES_REMPLACEES",
        "inference": "OK_MONTANTS_DATES_FICTIFS",
        "scanned_files": str(scanned),
    }


def _run_source_audit(source: InstanceConfig, run: RunContext, max_text_chars: int) -> dict[str, object]:
    result: dict[str, object] = {"status": "not_run"}
    try:
        privacy_result = privacyops.screen_existing(
            source,
            run,
            include_generated=False,
            max_text_chars=max_text_chars,
            prune_unseen=True,
        )
        queue_result = biffageops.build_redaction_queue(source, run)
        result = {
            "status": "ok",
            "screened_count": privacy_result.get("screened_count", 0),
            "priority_counts": privacy_result.get("priority_counts", {}),
            "queued_count": queue_result.get("queued_count", 0),
            "queue_status_counts": queue_result.get("status_counts", {}),
            "publication_note": "Audit source execute localement; aucune ligne source n'est copiee dans la demo.",
        }
    except Exception as exc:  # noqa: BLE001
        result = {
            "status": "warning",
            "warning": str(exc),
            "publication_note": "La demo peut etre generee, mais l'audit source doit etre repris avant publication externe.",
        }
    return result
