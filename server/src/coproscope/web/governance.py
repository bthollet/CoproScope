from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from ..core.common import InstanceConfig, read_csv
from ..modules import accessops, syndicops, timelineops
from ..vault import resilience


ROLE_LABELS: dict[str, tuple[str, str]] = {
    "coproprietaire": ("Coproprietaire", "voit les pieces ouvertes a tous les coproprietaires"),
    "conseil_syndical": ("Conseil syndical", "voit les dossiers utiles a sa mission de controle"),
    "referent_cs": ("Referent du conseil syndical", "suit un sujet et rend compte au conseil syndical"),
    "commission_member": ("Membre de commission", "voit seulement le mandat, le theme et la periode prevus"),
    "external_advisor": ("Conseil externe", "acces limite a une mission precise"),
    "auditor_readonly": ("Lecteur audit", "lecture seule pour verifier sans modifier"),
}

RESOURCE_LABELS = {
    "archive-copro": "Archive ouverte aux coproprietaires",
    "dossier-cs": "Dossier reserve au conseil syndical",
    "prod-travaux-1": "Note de la commission travaux",
}

MEMBER_LABELS = {
    "copro-demo": "Coproprietaire standard",
    "cs-demo": "Membre du conseil syndical",
    "commission-demo": "Membre de la commission travaux",
}

DECISION_REASON_LABELS = {
    "college_allowed": "le role ouvre ce niveau de lecture",
    "insufficient_college": "ce niveau est reserve a un role plus restreint",
    "commission_member_allowed": "mandat actif, theme conforme, periode valide",
    "commission_mandate_allowed": "mandat actif, theme conforme, periode valide",
    "commission_referent_allowed": "referent designe pour cette commission",
    "no_matching_grant": "aucune autorisation active ne couvre ce cas",
    "expired_or_revoked_grant": "autorisation terminee ou retiree",
    "inactive_mandate": "mandat de commission hors periode",
    "missing_active_thematic_mandate": "aucun mandat actif ne couvre ce theme",
    "missing_active_commission_role": "aucun role actif ne couvre cette commission",
    "commission_inactive": "commission inactive",
    "production_outside_commission_theme": "piece hors theme de la commission",
}

STATUS_LABELS = {
    "a_configurer": "a configurer",
    "audit_impossible": "controle impossible",
    "incomplete": "archive incomplete",
    "at_risk": "a surveiller",
    "capture_possible": "reconstruction partielle possible",
    "reconstructible": "reconstructible",
    "inconnu": "etat a confirmer",
}

RISK_LABELS = {
    "no_snapshot": "aucune copie de securite complete lue",
    "single_device": "un seul appareil semble porter l'historique",
    "missing_blob": "une piece attendue manque dans l'archive",
    "forbidden_entries": "des fichiers non prevus sont presents",
    "no_recovery_key": "aucune cle de secours declaree",
    "no_key_quorum": "les cles de secours ne sont pas reparties entre assez de personnes",
    "no_coowner_recovery_guardian": "aucun coproprietaire gardien de secours n'est declare",
    "no_reader_replica": "aucune copie de lecture independante n'est declaree",
    "vault_audit_error": "le controle technique du coffre a echoue",
}

REQUEST_STATUS_LABELS = {
    "todo": "a demander",
    "pending": "en attente",
    "a_relancer": "a relancer",
    "answered": "reponse recue",
    "closed": "preuve recue",
}

REQUEST_CHANNEL_LABELS = {
    "a_definir": "canal a choisir",
    "email": "email",
    "courrier": "courrier",
}


def build_governance_overview(instance: InstanceConfig, year: int) -> dict[str, Any]:
    """Build a read-only governance and piloting view for the local UI."""
    requests = _syndic_requests(instance, year)
    access = _access_preview()
    vault = _vault_resilience(instance)
    shortcuts = _shortcut_preview()
    indicators = _indicator_categories()
    complexity = _complex_governance_preview()
    return {
        "instance": {
            "id": instance.instance_id,
            "name": instance.display_name,
            "year": str(year),
            "scope": instance.scope,
            "entity_id": instance.entity_id,
        },
        "vaults": {
            "status": "coffres_separes",
            "title": "Coffres separes, organisations reliees",
            "summary": (
                "Un coffre est l'armoire numerique d'une copro: preuves, droits, cache local et "
                "cles restent dans le perimetre choisi."
            ),
            "rules": [
                "une meme application peut ouvrir plusieurs coffres de copro, mais ne les fusionne pas",
                "chaque bien ou copro garde son instance, ses cles, ses droits et son cache",
                "aucun role, jeton de session ou document selectionne ne traverse seul un changement de coffre",
                "une recherche entre coffres doit etre volontaire et afficher le coffre source de chaque resultat",
                "la gouvernance complexe relie des organisations; elle ne transforme pas deux coffres en un seul",
            ],
        },
        "complexity": complexity,
        "syndicops": requests,
        "access": access,
        "vault": vault,
        "shortcuts": shortcuts,
        "indicators": indicators,
    }


def _syndic_requests(instance: InstanceConfig, year: int) -> dict[str, Any]:
    path = _safe_register(instance, "requests")
    rows: list[dict[str, str]] = []
    if path and path.exists():
        _, raw_rows = read_csv(path)
        rows = syndicops.normalize_requests(raw_rows, today=f"{year}-12-31")
    by_status = dict(Counter(row.get("status", "todo") or "todo" for row in rows))
    by_channel = dict(Counter(row.get("channel", "a_definir") or "a_definir" for row in rows))
    open_rows = [row for row in rows if row.get("status") != "closed"]
    return {
        "count": len(rows),
        "open_count": len(open_rows),
        "by_status": by_status,
        "status_counts": [
            {"status": status, "label": REQUEST_STATUS_LABELS.get(status, status), "count": count}
            for status, count in by_status.items()
        ],
        "by_channel": by_channel,
        "rows": [_request_display_row(row) for row in open_rows[:8]],
        "source_state": "registre_lu" if path and path.exists() else "registre_absent",
        "source_label": "registre lu" if path and path.exists() else "aucun registre branche",
    }


def _request_display_row(row: dict[str, str]) -> dict[str, str]:
    status = row.get("status", "todo") or "todo"
    channel = row.get("channel", "a_definir") or "a_definir"
    return {
        **row,
        "status_label": REQUEST_STATUS_LABELS.get(status, status),
        "channel_label": REQUEST_CHANNEL_LABELS.get(channel, channel),
    }


def _access_preview() -> dict[str, Any]:
    coowner = accessops.Member("copro-demo", "Coproprietaire", default_college="C2_Coproprietaires")
    cs_member = accessops.Member("cs-demo", "Membre CS", default_college="C2_Coproprietaires")
    commission_member = accessops.Member("commission-demo", "Commission travaux", default_college="C2_Coproprietaires")
    grants = [
        accessops.RoleGrant(cs_member.member_id, accessops.ROLE_CONSEIL_SYNDICAL),
        accessops.RoleGrant(
            commission_member.member_id,
            accessops.ROLE_COMMISSION_MEMBER,
            scope_type=accessops.SCOPE_COMMISSION,
            scope_id="commission-travaux",
            starts_on="2026-01-01",
            expires_on="2026-12-31",
        ),
    ]
    commission = accessops.Commission("commission-travaux", "Commission travaux", "travaux")
    mandate = accessops.CommissionMandate(
        "mandat-travaux-2026",
        commission.commission_id,
        "travaux",
        "2026-01-01",
        "2026-12-31",
        title="Assister le CS sur le suivi travaux",
    )
    production = accessops.CommissionProduction(
        "prod-travaux-1",
        commission.commission_id,
        "Suivi devis toiture",
        "travaux",
        mandate_id=mandate.mandate_id,
        access_college="C4_Conseil_Syndical",
    )
    decisions = [
        accessops.can_access_college(coowner, "C2_Coproprietaires", grants, resource_id="archive-copro"),
        accessops.can_access_college(coowner, "C4_Conseil_Syndical", grants, resource_id="dossier-cs"),
        accessops.can_access_college(cs_member, "C4_Conseil_Syndical", grants, resource_id="dossier-cs"),
        accessops.can_access_production(commission_member, production, grants, [mandate], [commission]),
    ]
    return {
        "roles": [
            {"key": key, "label": label, "help": help_text}
            for key, (label, help_text) in ROLE_LABELS.items()
        ],
        "commissions": [
            {
                "label": commission.label,
                "theme": commission.theme,
                "mandate": mandate.title,
                "access": "reserve au conseil syndical",
            }
        ],
        "decisions": [
            {
                "resource": decision.resource_id,
                "resource_label": RESOURCE_LABELS.get(decision.resource_id, decision.resource_id),
                "member": decision.member_id,
                "member_label": MEMBER_LABELS.get(decision.member_id, decision.member_id),
                "allowed": decision.allowed,
                "reason": decision.reason,
                "reason_label": DECISION_REASON_LABELS.get(decision.reason, decision.reason),
                "role": decision.matched_role,
                "role_label": ROLE_LABELS.get(decision.matched_role or "", ("aucun role actif", ""))[0],
            }
            for decision in decisions
        ],
    }


def _vault_resilience(instance: InstanceConfig) -> dict[str, Any]:
    roots = _configured_vault_roots(instance)
    if roots is None:
        return {
            "configured": False,
            "status": "a_configurer",
            "status_label": STATUS_LABELS["a_configurer"],
            "risks": [
                "no_snapshot",
                "no_reader_replica",
                "no_key_quorum",
                "no_coowner_recovery_guardian",
            ],
            "risk_labels": _risk_labels(
                [
                    "no_snapshot",
                    "no_reader_replica",
                    "no_key_quorum",
                    "no_coowner_recovery_guardian",
                ]
            ),
            "counts": {
                "events": 0,
                "blobs": 0,
                "snapshots": 0,
                "reader_replicas": 0,
            },
            "message": "Le coffre de donnees n'est pas encore declare dans cette instance.",
        }
    local_root, sync_root = roots
    try:
        audit = resilience.audit_survivability(local_root, sync_root)
    except Exception as exc:  # noqa: BLE001 - UI must stay readable even during setup.
        return {
            "configured": True,
            "status": "audit_impossible",
            "status_label": STATUS_LABELS["audit_impossible"],
            "risks": ["vault_audit_error"],
            "risk_labels": _risk_labels(["vault_audit_error"]),
            "counts": {},
            "message": str(exc),
        }
    risks = audit.get("risks", [])
    status = audit.get("status", "inconnu")
    return {
        "configured": True,
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "risks": risks,
        "risk_labels": _risk_labels(risks),
        "counts": audit.get("counts", {}),
        "message": "Archive complete et capacite de reconstruction a verifier regulierement.",
    }


def _shortcut_preview() -> dict[str, Any]:
    shortcuts = [
        timelineops.create_logical_shortcut("DOC-DEMO-AG", "ACTION-DEMO-RELANCE", "ag"),
        timelineops.create_logical_shortcut("DOC-DEMO-FACTURE", "POINT-DEMO-COMPTES", "comptes"),
        timelineops.create_logical_shortcut("DOC-DEMO-DEVIS", "COMMISSION-DEMO-TRAVAUX", "commission"),
    ]
    labels = {
        "DOC-DEMO-AG": "Proces-verbal d'assemblee generale",
        "ACTION-DEMO-RELANCE": "Relance a faire",
        "DOC-DEMO-FACTURE": "Facture controlee",
        "POINT-DEMO-COMPTES": "Point de verification des comptes",
        "DOC-DEMO-DEVIS": "Devis travaux",
        "COMMISSION-DEMO-TRAVAUX": "Dossier de la commission travaux",
    }
    context_labels = {
        "ag": "Assemblee generale",
        "comptes": "Comptes",
        "commission": "Commission",
    }
    return {
        "count": len(shortcuts),
        "rows": [
            {
                **shortcut,
                "context_label": context_labels.get(str(shortcut["context_kind"]), str(shortcut["context_kind"])),
                "source_label": labels.get(str(shortcut["object_id"]), str(shortcut["object_id"])),
                "target_label": labels.get(str(shortcut["target_object_id"]), str(shortcut["target_object_id"])),
            }
            for shortcut in shortcuts
        ],
        "rule": "un raccourci pointe vers une preuve ou une action; il ne duplique jamais le document",
    }


def _complex_governance_preview() -> dict[str, Any]:
    return {
        "summary": (
            "Une copro peut partager des sujets avec d'autres organisations. CoproScope les montre "
            "comme des perimetres de decision relies, sans melanger leurs coffres de donnees."
        ),
        "organizations": [
            {
                "label": "Syndicat primaire",
                "plain": "la copro de rattachement du lot et des decisions principales",
                "example": "budget general, assemblee generale, syndic, conseil syndical",
            },
            {
                "label": "Syndicat secondaire",
                "plain": "un sous-ensemble de la copro, souvent par batiment ou equipement",
                "example": "charges et travaux propres a un batiment",
            },
            {
                "label": "ASL",
                "plain": "association syndicale libre pour des espaces ou services partages hors copro stricte",
                "example": "voirie privee, portail, espaces verts communs a plusieurs ensembles",
            },
            {
                "label": "Union de syndicats",
                "plain": "structure commune entre plusieurs syndicats pour gerer un service partage",
                "example": "chaufferie, gardiennage, reseau ou contrat mutualise",
            },
        ],
        "cross_rights": [
            {
                "case": "Un coproprietaire depend du syndicat primaire et d'une ASL",
                "rule": "il voit chaque piece seulement si une autorisation existe dans le perimetre concerne",
            },
            {
                "case": "Une commission travaux lit une note d'un syndicat secondaire",
                "rule": "le mandat doit nommer le theme, la periode et l'organisation source",
            },
            {
                "case": "Une union produit une facture utile a plusieurs copros",
                "rule": "la piece garde son coffre source et chaque copro recoit un lien ou une copie autorisee",
            },
        ],
        "guardrails": [
            "un droit croise ouvre une lecture precise, pas tout un coffre voisin",
            "la source d'une piece reste visible: primaire, secondaire, ASL ou union",
            "les indicateurs peuvent additionner des chiffres, mais doivent garder le perimetre de preuve",
            "changer de coffre demande une action explicite de l'utilisateur",
        ],
    }


def _indicator_categories() -> list[dict[str, str]]:
    return [
        {
            "theme": "Consommations",
            "signal": "derive eau, energie, chauffage, electricite commune",
            "integration": "factures, releves, contrats, anomalies comptables",
        },
        {
            "theme": "Entretien",
            "signal": "frequence, delai d'intervention, cout par equipement",
            "integration": "contrats, registre des actions, preuves photo, demandes syndic",
        },
        {
            "theme": "Investissements",
            "signal": "reste a financer, age equipement, fonds travaux, arbitrage investissement/entretien",
            "integration": "plan pluriannuel de travaux, devis, assemblees generales, budgets, suivi des decisions",
        },
        {
            "theme": "Espaces verts",
            "signal": "cout au passage, saisonnalite, qualite constatee, eau",
            "integration": "factures, contrats, incidents, observations terrain",
        },
        {
            "theme": "Travaux",
            "signal": "budget vote/engage/paye, reserves, garanties, retards",
            "integration": "devis, proces-verbaux d'assemblee generale, factures, preuves de cloture",
        },
        {
            "theme": "Gouvernance",
            "signal": "decisions sans preuve, delais syndic, participation, commissions",
            "integration": "assemblees generales ordinaires ou extraordinaires, demandes, roles, productions de commission",
        },
    ]


def _risk_labels(risks: list[str]) -> list[str]:
    return [RISK_LABELS.get(risk, risk) for risk in risks]


def _configured_vault_roots(instance: InstanceConfig) -> tuple[Path, Path] | None:
    settings = instance.settings()
    vault = settings.get("vault") if isinstance(settings.get("vault"), dict) else {}
    local_value = vault.get("local_root") or vault.get("local") or vault.get("cache_root")
    sync_value = vault.get("sync_root") or vault.get("sync") or vault.get("cloud_root")
    if not local_value or not sync_value:
        return None
    local_root = instance.resolve_path(str(local_value))
    sync_root = instance.resolve_path(str(sync_value))
    if local_root is None or sync_root is None:
        return None
    return local_root, sync_root


def _safe_register(instance: InstanceConfig, name: str) -> Path | None:
    try:
        return instance.register(name)
    except KeyError:
        return None
