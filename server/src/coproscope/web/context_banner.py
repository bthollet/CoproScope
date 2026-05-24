from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..core.common import InstanceConfig
from ..vault import core as vault_core
from ..vault.sync_alerts import (
    VaultSyncActionCode,
    VaultSyncAlertLevel,
    evaluate_vault_sync_alerts,
)


ROLE_LABELS = {
    "administrateur_local": "Administrateur local",
    "admin_local": "Administrateur local",
    "conseil_syndical": "Conseil syndical",
    "cs": "Conseil syndical",
    "coproprietaire": "Coproprietaire",
    "commission_member": "Membre de commission",
    "membre_commission": "Membre de commission",
    "syndic": "Syndic",
    "auditor_readonly": "Lecteur audit",
}

ROLE_HELP = {
    "administrateur_local": "peut preparer le poste local, sans donner a lui seul le droit de publier",
    "admin_local": "peut preparer le poste local, sans donner a lui seul le droit de publier",
    "conseil_syndical": "controle les pieces utiles a la mission du conseil syndical",
    "cs": "controle les pieces utiles a la mission du conseil syndical",
    "coproprietaire": "voit les informations ouvertes aux coproprietaires",
    "commission_member": "travaille seulement dans le mandat et le theme de sa commission",
    "membre_commission": "travaille seulement dans le mandat et le theme de sa commission",
    "syndic": "intervient comme gestionnaire, avec des droits a verifier avant chaque partage",
    "auditor_readonly": "lit pour verifier, sans modifier les donnees locales",
}

ROLE_ACCESS_LEVELS = {
    "administrateur_local": "C5_Syndic_Admin",
    "admin_local": "C5_Syndic_Admin",
    "conseil_syndical": "C4_Conseil_Syndical",
    "cs": "C4_Conseil_Syndical",
    "coproprietaire": "C2_Coproprietaires",
    "commission_member": "C3_Commissions",
    "membre_commission": "C3_Commissions",
    "syndic": "C5_Syndic_Admin",
    "auditor_readonly": "C4_Conseil_Syndical",
}

ACCESS_LABELS = {
    "C0_Public": "public",
    "C1_Occupants_Usagers": "occupants et usagers",
    "C2_Coproprietaires": "coproprietaires",
    "C3_Commissions": "commission limitee",
    "C4_Conseil_Syndical": "conseil syndical",
    "C5_Syndic_Admin": "administration locale",
}

@dataclass(frozen=True)
class ContextBannerItem:
    label: str
    value: str
    help: str
    tone: str = "neutral"


@dataclass(frozen=True)
class ContextBanner:
    coffre_id: str
    coffre_label: str
    role: str
    role_label: str
    access_level: str
    access_level_label: str
    vault_state: str
    vault_state_label: str
    sync_state: str
    sync_state_label: str
    last_checked_label: str
    next_action: str
    next_action_href: str
    novice_text: str
    tone: str
    items: tuple[ContextBannerItem, ...]

    def to_template_context(self) -> dict[str, Any]:
        return asdict(self)


def build_context_banner(
    instance: InstanceConfig,
    *,
    role_hint: str | None = None,
    access_level: str | None = None,
    last_checked_at: str | datetime | None = None,
    sync_profile_id: str | None = None,
    next_action_href: str = "/gouvernance",
) -> dict[str, Any]:
    """Build the isolated banner model; callers decide where to include the partial."""
    settings = instance.settings()
    context_settings = _mapping(settings.get("context_banner") or settings.get("ui_context"))
    vault_settings = _mapping(settings.get("vault") or settings.get("coffre"))

    role = _normalize_key(
        role_hint
        or context_settings.get("role")
        or context_settings.get("role_hint")
        or vault_settings.get("role_hint")
        or settings.get("role")
        or ""
    )
    role_label = ROLE_LABELS.get(role, "Role a confirmer")
    role_help = ROLE_HELP.get(role, "confirmez qui utilise l'ecran avant de lire ou partager une piece")

    resolved_access_level = str(
        access_level
        or context_settings.get("access_level")
        or context_settings.get("niveau_acces")
        or ROLE_ACCESS_LEVELS.get(role, "")
        or ""
    ).strip()
    access_label = ACCESS_LABELS.get(resolved_access_level, resolved_access_level or "niveau a confirmer")

    vault_status = _vault_status(instance, vault_settings)
    sync_status = _sync_status(
        vault_status["sync_root"],
        str(sync_profile_id or vault_settings.get("sync_profile") or vault_settings.get("sync_profile_id") or "local_folder"),
    )
    last_checked = _last_checked_label(last_checked_at or vault_settings.get("last_verified_at") or vault_settings.get("last_checked_at"))
    next_action = _next_action(vault_status, sync_status, role)
    tone = _overall_tone(vault_status["tone"], sync_status["tone"], role)

    banner = ContextBanner(
        coffre_id=instance.instance_id,
        coffre_label=instance.display_name,
        role=role or "a_confirmer",
        role_label=role_label,
        access_level=resolved_access_level or "a_confirmer",
        access_level_label=access_label,
        vault_state=str(vault_status["state"]),
        vault_state_label=str(vault_status["label"]),
        sync_state=str(sync_status["state"]),
        sync_state_label=str(sync_status["label"]),
        last_checked_label=last_checked,
        next_action=next_action,
        next_action_href=next_action_href,
        novice_text=(
            "Vous etes dans ce coffre, avec ce role et ce niveau de lecture. "
            "Si un point ne correspond pas a votre situation, arretez-vous et confirmez le contexte avant de partager."
        ),
        tone=tone,
        items=(
            ContextBannerItem("Coffre courant", instance.display_name, f"Identifiant: {instance.instance_id}", "ok"),
            ContextBannerItem("Role", role_label, role_help, "review" if not role else "ok"),
            ContextBannerItem("Niveau acces", access_label, "niveau maximal affiche pour ce contexte local", "review" if not resolved_access_level else "ok"),
            ContextBannerItem("Coffre signe", str(vault_status["label"]), str(vault_status["help"]), str(vault_status["tone"])),
            ContextBannerItem("Sync", str(sync_status["label"]), str(sync_status["help"]), str(sync_status["tone"])),
            ContextBannerItem("Derniere verification", last_checked, "date lue depuis la configuration ou a refaire", "review" if "a faire" in last_checked else "ok"),
        ),
    )
    return banner.to_template_context()


def _vault_status(instance: InstanceConfig, vault_settings: dict[str, Any]) -> dict[str, Any]:
    roots = _configured_vault_roots(instance, vault_settings)
    if roots is None:
        return {
            "state": "not_configured",
            "label": "Coffre signe a declarer",
            "help": "aucun local_root et sync_root ne sont configures pour cette instance",
            "tone": "review",
            "sync_root": None,
        }

    local_root, sync_root = roots
    if not local_root.exists() or not sync_root.exists():
        missing = "cache local" if not local_root.exists() else "dossier sync"
        return {
            "state": "missing_root",
            "label": f"{missing} a creer",
            "help": "le coffre est declare mais un dossier attendu manque encore",
            "tone": "review",
            "sync_root": sync_root,
        }

    try:
        status = vault_core.vault_status(local_root, sync_root)
    except Exception as exc:  # noqa: BLE001 - banner must not break the UI shell.
        return {
            "state": "status_error",
            "label": "Etat du coffre illisible",
            "help": f"controle local impossible: {exc}",
            "tone": "risk",
            "sync_root": sync_root,
        }

    if status.get("forbidden_entries"):
        return {
            "state": "forbidden_entries",
            "label": "Coffre en protection",
            "help": "des fichiers de cache, developpement ou export temporaire sont dans la zone sync",
            "tone": "risk",
            "sync_root": sync_root,
        }
    if status.get("vault_exists") and status.get("local_state_exists"):
        return {
            "state": "ready",
            "label": "Coffre pret localement",
            "help": f"{status.get('events', 0)} evenement(s), {status.get('blobs', 0)} blob(s)",
            "tone": "ok",
            "sync_root": sync_root,
        }
    if status.get("vault_exists"):
        return {
            "state": "needs_local_state",
            "label": "Session locale a reconnecter",
            "help": "le coffre existe, mais l'etat local de cet appareil n'est pas pret",
            "tone": "review",
            "sync_root": sync_root,
        }
    return {
        "state": "needs_init",
        "label": "Coffre a initialiser",
        "help": "le dossier sync existe, mais aucun manifeste de coffre n'a ete lu",
        "tone": "review",
        "sync_root": sync_root,
    }


def _sync_status(sync_root: Path | None, profile_id: str) -> dict[str, str]:
    if sync_root is None:
        return {
            "state": "not_configured",
            "label": "Sync non branchee",
            "help": "aucun dossier sync n'est declare pour ce coffre",
            "tone": "review",
        }
    if not sync_root.exists():
        return {
            "state": "missing_root",
            "label": "Dossier sync absent",
            "help": "cree ou reconnecte le dossier avant toute verification",
            "tone": "review",
        }
    try:
        report = evaluate_vault_sync_alerts(sync_root, profile_id, sync_active=True)
    except Exception as exc:  # noqa: BLE001 - provider profile or filesystem may be partial.
        return {
            "state": "audit_error",
            "label": "Sync a verifier",
            "help": f"audit sync impossible: {exc}",
            "tone": "review",
        }

    if report.level == VaultSyncAlertLevel.INCIDENT:
        return {
            "state": "incident",
            "label": "Sync verrouillee en lecture seule",
            "help": "incident d'integrite: le coffre reste lisible, les publications sont bloquees et les membres doivent etre notifies",
            "tone": "risk",
        }
    if report.level == VaultSyncAlertLevel.PROTECTION:
        action = "publication suspendue"
        if report.has_action(VaultSyncActionCode.NOTIFY_INTERNAL):
            action += ", notification interne a preparer"
        return {
            "state": "protection",
            "label": "Sync en protection",
            "help": f"des fichiers interdits ou temporaires sont dans la zone sync: {action}",
            "tone": "risk",
        }
    if report.level == VaultSyncAlertLevel.ATTENTION:
        return {
            "state": "attention",
            "label": "Sync a surveiller",
            "help": "marqueur de conflit ou metadonnee transport: revue humaine avant publication externe",
            "tone": "review",
        }
    return {
        "state": "information",
        "label": "Sync sans alerte bloquante",
        "help": f"lecture locale du dossier sync ({profile_id}) sans marqueur simple de risque",
        "tone": "ok",
    }


def _configured_vault_roots(instance: InstanceConfig, vault_settings: dict[str, Any]) -> tuple[Path, Path] | None:
    local_value = vault_settings.get("local_root") or vault_settings.get("local") or vault_settings.get("cache_root")
    sync_value = vault_settings.get("sync_root") or vault_settings.get("sync") or vault_settings.get("cloud_root")
    if not local_value or not sync_value:
        return None
    local_root = instance.resolve_path(str(local_value))
    sync_root = instance.resolve_path(str(sync_value))
    if local_root is None or sync_root is None:
        return None
    return local_root, sync_root


def _last_checked_label(value: str | datetime | None) -> str:
    if value is None or str(value).strip() == "":
        return "Derniere verification: a faire"
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return f"Derniere verification: {value.isoformat(timespec='minutes')}"
    return f"Derniere verification: {str(value).strip()}"


def _next_action(vault_status: dict[str, Any], sync_status: dict[str, str], role: str) -> str:
    if vault_status["state"] == "not_configured":
        return "Declarer le cache local et le dossier sync du coffre."
    if vault_status["state"] in {"missing_root", "needs_init", "needs_local_state"}:
        return "Preparer le coffre signe avant de traiter des pieces."
    if vault_status["tone"] == "risk" or sync_status["tone"] == "risk":
        return "Suspendre le partage et verifier le coffre avec une personne habilitee."
    if not role:
        return "Confirmer votre role avant de continuer."
    if sync_status["tone"] == "review":
        return "Verifier la sync avant toute publication externe."
    return "Continuer: lire les actions, puis rattacher chaque piece a sa preuve."


def _overall_tone(vault_tone: str, sync_tone: str, role: str) -> str:
    if "risk" in {vault_tone, sync_tone}:
        return "risk"
    if not role or "review" in {vault_tone, sync_tone}:
        return "review"
    return "ok"


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _normalize_key(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
