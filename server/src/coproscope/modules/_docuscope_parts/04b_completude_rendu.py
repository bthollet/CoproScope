# -*- coding: utf-8 -*-
"""Le RENDU du rapport de completude, sorti de son module le 2026-09-11.

**Decoupage impose par la limite du depot**, et il etait annonce. Le lot
`RM-2026-0088` du meme jour avait laisse `04_completeness_and_kpis.py` a **599
lignes pour une limite de 600** et l'avait ecrit noir sur blanc: *le fichier est
sature, le prochain lot qui y touche devra le decouper avant d'ajouter quoi que
ce soit*. `RM-2026-0056` y a ajoute trois lignes d'import et l'a porte a 602.

**Ce qui est sorti et pourquoi c'est un sujet.** Tout ce qui MET EN FORME le
rapport - echappement des cellules markdown, libelles d'action par statut,
sections du compte rendu, note de fondement juridique. Le module d'origine garde
ce qui MESURE: la lecture des preuves, la fraicheur, les doutes de classement,
les lignes de completude, le verdict et les indicateurs.

**Une frontiere de mise en forme n'est pas un decoupage arbitraire.** Elle a un
effet mesurable: le jour ou le rapport changera de format, un seul fichier
bougera, et aucune mesure ne sera touchee au passage.
"""

from __future__ import annotations


def _md_cell(value: str) -> str:
    return (value or "").replace("|", "\\|").replace("\n", " ")


def _status_action(status: str, expected_label: str) -> tuple[str, str]:
    if status == "PRESENT":
        return "Preuve presente", "Aucune demande documentaire immediate."
    if status == "OBSOLETE":
        return (
            f"Demander une version recente: {expected_label}",
            "Demander au syndic une version recente, puis conserver l'ancienne comme preuve historique.",
        )
    if status == "A_CLASSER":
        return (
            f"Verifier le classement avant demande: {expected_label}",
            "Verifier la piece candidate; si elle ne couvre pas l'attendu, demander la piece au syndic.",
        )
    return f"Demander au syndic: {expected_label}", "Demander la piece au syndic et rattacher sa reponse au registre."


def _unread_section(unread_rows: list[dict[str, str]], total_docs: int) -> list[str]:
    if not unread_rows:
        return []
    counts: dict[str, int] = defaultdict(int)
    for row in unread_rows:
        counts[row["constat"]] += 1
    lines = [
        "",
        "## Documents presents que l'outil n'a pas su lire",
        "",
        f"Ces {len(unread_rows)} documents sur {total_docs} sont bien au dossier. L'outil n'a pas pu",
        "etablir leur nature avec certitude. Il ne faut pas les demander au syndic: ils sont deja la.",
        "La liste complete est dans le fichier documents_non_lus.csv, a cote de ce rapport.",
        "",
        "| Constat | Nombre | Ce que cela veut dire |",
        "|---|---:|---|",
    ]
    for constat, label in READING_GAP_LABELS.items():
        if counts.get(constat):
            lines.append(f"| {_md_cell(constat)} | {counts[constat]} | {_md_cell(label)} |")
    lines += ["", "| Document | Lot enregistre | Constat |", "|---|---|---|"]
    for row in unread_rows[:UNREAD_SAMPLE_LIMIT]:
        lines.append(
            f"| {_md_cell(row['file_name'] or row['doc_id'])} | {_md_cell(row['lot'])} | "
            f"{_md_cell(row['constat'])} |"
        )
    remaining = len(unread_rows) - UNREAD_SAMPLE_LIMIT
    if remaining > 0:
        lines.append(f"| ... et {remaining} autres | | tous nommes dans documents_non_lus.csv |")
    return lines


def _legal_basis_note(matrix_rows: list[dict[str, str]]) -> list[str]:
    """Dit ce qui fonde les exigences, quand elles ne le disent pas elles-memes."""
    if not matrix_rows:
        return []
    cited = sum(1 for row in matrix_rows if row.get("legal_basis"))
    if cited == len(matrix_rows):
        return []
    manquants = len(matrix_rows) - cited
    accord = "ne cite" if manquants <= 1 else "ne citent"
    return [
        "",
        f"Fondement des exigences: sur {len(matrix_rows)} pieces attendues, {manquants} {accord} "
        "aucun texte de reference et sont donc attendues par convention.",
        "Une exigence sans fondement declare se demande au syndic comme une bonne pratique: elle ne",
        "lui est pas opposable, et son absence n'est pas en soi un manquement.",
    ]


def _render_completeness_report(
    instance,
    docs: list[dict[str, str]],
    matrix_rows: list[dict[str, str]],
    action_rows: list[dict[str, str]],
    unread_rows: list[dict[str, str]],
    referential: dict[str, str],
) -> str:
    status_counts: dict[str, int] = defaultdict(int)
    for row in matrix_rows:
        status_counts[row["status"]] += 1

    lines = [
        "# Rapport de completude documentaire",
        "",
        f"- Instance: {instance.display_name}",
        f"- Documents inventories: {len(docs)}",
        f"- Documents dont la nature n'est pas etablie: {len(unread_rows)}",
        f"- Pieces attendues: {len(matrix_rows)}",
        f"- Pieces a traiter: {len(action_rows)}",
        "",
    ]
    lines.extend(_completeness_verdict(matrix_rows, action_rows, unread_rows, len(docs), referential))
    lines += [
        "",
        "## Synthese",
        "",
        "| Statut | Nombre | Lecture CS |",
        "|---|---:|---|",
        f"| PRESENT | {status_counts['PRESENT']} | Piece locale suffisante. |",
        f"| ABSENT | {status_counts['ABSENT']} | Piece a demander au syndic. |",
        f"| OBSOLETE | {status_counts['OBSOLETE']} | Version recente a obtenir. |",
        f"| A_CLASSER | {status_counts['A_CLASSER']} | Classement a verifier avant relance. |",
    ]
    lines.extend(_unread_section(unread_rows, len(docs)))
    lines += [
        "",
        "## Matrice actionnable",
        "",
        "| Statut | Priorite | Lot | Piece attendue | Type source | Fondement | Preuves | Suite |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in matrix_rows:
        evidence = row["evidence_paths"] or row["matched_doc_ids"]
        basis = row.get("legal_basis") or "fondement non declare"
        lines.append(
            f"| {_md_cell(row['status'])} | {_md_cell(row['criticality'])} | {_md_cell(row['lot'])} | "
            f"{_md_cell(row['expected_label'])} | {_md_cell(row['document_type'])} | {_md_cell(basis)} | "
            f"{_md_cell(evidence)} | {_md_cell(row['action'])} |"
        )

    lines.extend(["", "## Pieces a demander"])
    lines.extend(_legal_basis_note(matrix_rows))
    lines += ["", "| Priorite | Statut | Piece | Pourquoi | Diligence proposee |", "|---|---|---|---|---|"]
    if action_rows:
        for row in action_rows:
            lines.append(
                f"| {_md_cell(row['priority'])} | {_md_cell(row['status'])} | {_md_cell(row['expected_piece'])} | "
                f"{_md_cell(row['reason'])} | {_md_cell(row['suggested_diligence'])} |"
            )
    elif matrix_rows:
        lines.append(
            f"| OK | PRESENT | Aucune | Les {len(matrix_rows)} pieces attendues evaluees sont couvertes. | "
            "Aucune relance. |"
        )
    else:
        lines.append(
            "| - | NON_EVALUE | Aucune | Aucune piece attendue n'a ete evaluee: rien n'a ete verifie. | "
            "Fournir le referentiel des pieces attendues, puis relancer. |"
        )
    return "\n".join(lines) + "\n"
