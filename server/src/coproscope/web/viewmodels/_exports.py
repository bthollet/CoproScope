from __future__ import annotations

from ._runtime import *

def filter_action_items(
    actions: list[dict[str, str]],
    *,
    scope: str = "",
    priority: str = "",
    status: str = "",
) -> list[dict[str, str]]:
    scope = (scope or "").strip().lower()
    priority = (priority or "").strip().upper()
    status = (status or "").strip().lower()
    filtered = actions
    if scope and scope != "tous":
        filtered = [
            action
            for action in filtered
            if action.get("domain") == scope
            or action.get("channel") == scope
            or action.get("source", "").lower() == scope
        ]
    if priority and priority != "TOUS":
        filtered = [action for action in filtered if action.get("priority", "").upper() == priority]
    if status and status != "tous":
        filtered = [action for action in filtered if action.get("status") == status]
    if not filtered and (scope or priority or status):
        label = "Aucune fiche ne correspond a ces filtres."
        if status == "a_demander":
            label = "Aucune preuve a demander dans ce filtre."
        elif scope == "syndic":
            label = "Aucune relance syndic n'est en attente dans ce filtre."
        elif priority == "P1":
            label = "Aucune action prioritaire dans ce filtre."
        return [
            _action(
                label,
                "Registre Actions",
                priority or "P2",
                "Changer de filtre ou revenir au cockpit pour choisir une autre priorite.",
                "/actions",
                action_id=_stable_action_id("EMPTY-ACTION", 0, scope, priority, status),
                status=status or "a_traiter",
                domain=scope or "general",
                domain_label="Etat vide",
                owner="Conseil syndical",
                next_step="Changer de filtre ou ajouter une action avec une preuve attendue.",
                evidence="Aucune preuve attendue pour cet etat vide.",
            )
        ]
    return filtered


def actions_to_csv(actions: list[dict[str, str]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=ACTION_EXPORT_FIELDS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for action in actions:
        writer.writerow(action)
    return output.getvalue()


def _md_cell(value: str) -> str:
    return (value or "").replace("|", "\\|").replace("\n", " ").strip()


def actions_to_markdown(actions: list[dict[str, str]], title: str = "Actions CoproScope") -> str:
    lines = [
        f"# {title}",
        "",
        f"- Actions exportees: {len(actions)}",
        "",
        "| Priorite | Statut | Domaine | Titre | Prochaine etape | Preuve |",
        "|---|---|---|---|---|---|",
    ]
    for action in actions:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(action.get("priority", "")),
                    _md_cell(action.get("status", "")),
                    _md_cell(action.get("domain_label", "")),
                    _md_cell(action.get("title", "")),
                    _md_cell(action.get("next_step", "")),
                    _md_cell(action.get("evidence", "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"
