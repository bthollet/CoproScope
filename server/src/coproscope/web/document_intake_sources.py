from __future__ import annotations

import re
from typing import Any, Mapping
from urllib.parse import urlencode

from ..core.common import InstanceConfig


SOURCE_ALL = "all"
SOURCE_INBOX = "inbox"
SOURCE_DRAG_DROP = "drag_drop"
SOURCE_LOCAL_FOLDER = "local_folder"
SOURCE_DRIVE_DESKTOP = "drive_desktop"
SOURCE_MAILBOX = "mailbox"
SOURCE_FUTURE = "future_channel"
#: **Ce que le code ne sait pas dire de la provenance d'un document.**
#: `RM-2026-0052`, defaut (1). Avant ce lot, tout ce qui n'etait reconnu
#: par aucune liste etait annonce comme venant de la boite de reception -
#: **858 documents sur 858** sur l'instance reconstruite. Un ecran qui
#: nomme une source pour un document dont il ignore l'origine empeche
#: precisement le controle que l'item demande: distinguer une piece recue
#: d'une sortie que l'outil a produite lui-meme.
SOURCE_PROVENANCE_INDETERMINEE = "provenance_indeterminee"

SOURCE_IDS = {
    SOURCE_ALL,
    SOURCE_INBOX,
    SOURCE_DRAG_DROP,
    SOURCE_LOCAL_FOLDER,
    SOURCE_DRIVE_DESKTOP,
    SOURCE_MAILBOX,
    SOURCE_FUTURE,
    SOURCE_PROVENANCE_INDETERMINEE,
}
# **L'indetermine est un filtre de PLEIN DROIT, et ce n'est pas un detail.**
# Premiere version de ce lot: il n'y figurait pas, et les documents sans
# provenance declaree DISPARAISSAIENT de tous les filtres - un test d'interface
# l'a montre en trouvant une page vide. C'est l'inverse du principe du depot:
# **l'inconnu se signale, il ne s'efface pas**. Un document dont on ignore
# l'origine reste visible, sous une etiquette qui dit la verite.
REGISTER_SOURCE_IDS = {
    SOURCE_INBOX,
    SOURCE_LOCAL_FOLDER,
    SOURCE_DRIVE_DESKTOP,
    SOURCE_MAILBOX,
    SOURCE_PROVENANCE_INDETERMINEE,
}

SOURCE_LABELS = {
    SOURCE_ALL: "Toutes les sources",
    SOURCE_INBOX: "Inbox du coffre",
    SOURCE_DRAG_DROP: "Glisser-deposer",
    SOURCE_LOCAL_FOLDER: "Dossier local",
    SOURCE_DRIVE_DESKTOP: "Drive Desktop",
    SOURCE_MAILBOX: "Mailbox",
    SOURCE_FUTURE: "Autres canaux",
    SOURCE_PROVENANCE_INDETERMINEE: "Provenance indéterminée",
}

STATE_LABELS = {
    "active": "Actif",
    "paused": "En pause",
    "needs_setup": "A configurer",
    "connector_later": "A connecter",
    "future": "Plus tard",
}

STATE_TONES = {
    "active": "ok",
    "paused": "p2",
    "needs_setup": "p2",
    "connector_later": "p2",
    "future": "p2",
}


def normalize_document_intake_source(value: object) -> str:
    token = _token(value)
    aliases = {
        "": SOURCE_ALL,
        "all": SOURCE_ALL,
        "tout": SOURCE_ALL,
        "toutes": SOURCE_ALL,
        "document_intake": SOURCE_DRAG_DROP,
        "upload": SOURCE_DRAG_DROP,
        "depot": SOURCE_DRAG_DROP,
        "depot_local": SOURCE_DRAG_DROP,
        "global_drop": SOURCE_DRAG_DROP,
        "drag": SOURCE_DRAG_DROP,
        "drag_drop": SOURCE_DRAG_DROP,
        "glisser_deposer": SOURCE_DRAG_DROP,
        "vault_inbox": SOURCE_INBOX,
        "inbox_vault": SOURCE_INBOX,
        "physical_inbox": SOURCE_INBOX,
        "dossier_local": SOURCE_LOCAL_FOLDER,
        "local": SOURCE_LOCAL_FOLDER,
        "drive": SOURCE_DRIVE_DESKTOP,
        "drive_desktop": SOURCE_DRIVE_DESKTOP,
        "google_drive_desktop": SOURCE_DRIVE_DESKTOP,
        "mail": SOURCE_MAILBOX,
        "email": SOURCE_MAILBOX,
        "mailbox": SOURCE_MAILBOX,
        "future": SOURCE_FUTURE,
        "canal_futur": SOURCE_FUTURE,
    }
    return aliases.get(token, token if token in SOURCE_IDS else SOURCE_ALL)


def source_id_from_register_row(row: Mapping[str, object]) -> str:
    source_kind = _token(row.get("source_kind"))
    source_zone = _token(row.get("source_zone"))
    if source_kind in {"physical_deposit", "inbox_vault", "vault_inbox", "copie_primaire"}:
        return SOURCE_INBOX
    if "inbox" in source_zone or "depot_physique" in source_zone:
        return SOURCE_INBOX
    if source_kind in {"user_workspace", "local_folder", "dossier_local"}:
        return SOURCE_LOCAL_FOLDER
    if source_kind in {"drive_desktop", "google_drive_desktop", "synced_drive_folder"}:
        return SOURCE_DRIVE_DESKTOP
    if "drive" in source_zone and "cloud" not in source_kind:
        return SOURCE_DRIVE_DESKTOP
    if source_kind in {"mailbox", "email", "imap"}:
        return SOURCE_MAILBOX
    # **`raw` EST la zone des pieces recues, et il faut le DIRE.**
    # `RM-2026-0052`, defaut (1), mesure du 2026-09-11: sur les 858 documents
    # de l'instance reconstruite, **858 tombaient sur le fourre-tout final**.
    # Aucun ne passait par une regle: `raw` - la valeur que `_source_labels`
    # ecrit pour toute piece deposee dans la zone brute - ne figurait dans
    # AUCUNE des listes ci-dessus. L'ecran annoncait donc *boite de reception*
    # pour la totalite du corpus, et il avait raison **par chance**.
    if source_kind == "raw" or "raw" in source_zone:
        return SOURCE_INBOX
    # **CE DEFAUT EST CONSERVE, ET LE RECUL EST MESURE.**
    # `RM-2026-0052`, defaut (1). Ce `return` affirme une provenance que le
    # code ne connait pas, et c'est exactement ce que l'item reproche: *ce que
    # CoproScope produit ne doit jamais etre classe comme piece emise par le
    # syndic*. Un fourre-tout qui nomme une source ne peut pas faire cette
    # distinction, puisqu'il nomme la meme source pour tout ce qu'il ignore.
    #
    # **Le remplacer par `SOURCE_PROVENANCE_INDETERMINEE` a ete essaye le
    # 2026-09-11, et l'essai a ete annule.** Un test d'interface a montre
    # pourquoi: un document depose PAR LE CANAL inbox disparaissait de ce
    # filtre, parce que **le registre ne porte pas la provenance du canal de
    # depot**. L'inconnu doit se signaler, pas s'effacer - et ici il effacait.
    #
    # **Le vrai defaut est donc en amont, et il est nomme:** la chaine de depot
    # connait le canal - le formulaire le transmet - et ne l'ecrit pas dans la
    # ligne. Tant qu'elle ne l'ecrit pas, aucune regle en aval ne peut
    # distinguer une piece recue d'une sortie de l'outil, et ce `return` est le
    # moins mauvais des choix disponibles. La valeur
    # `SOURCE_PROVENANCE_INDETERMINEE` reste declaree et filtrable: elle
    # attend que l'amont la renseigne.
    return SOURCE_INBOX


def select_document_intake_rows(
    upload_rows: list[dict[str, object]],
    register_rows: list[dict[str, object]],
    selected_source: str,
) -> list[dict[str, object]]:
    source = normalize_document_intake_source(selected_source)
    if source == SOURCE_DRAG_DROP:
        return upload_rows
    if source in REGISTER_SOURCE_IDS:
        return [row for row in register_rows if row.get("source_id") == source]
    if source == SOURCE_ALL:
        return _dedupe_rows([*upload_rows, *register_rows])
    return []


def build_document_intake_source_context(
    instance: InstanceConfig,
    *,
    selected_source: str,
    selected_manifest: Mapping[str, object] | None,
    upload_rows: list[dict[str, object]],
    register_rows: list[dict[str, object]],
) -> dict[str, object]:
    selected = normalize_document_intake_source(selected_source)
    counts = _source_counts(upload_rows, register_rows)
    deposit_id = str(selected_manifest.get("deposit_id") or "") if isinstance(selected_manifest, Mapping) else ""
    configured_cards = _configured_source_cards(instance, counts, deposit_id, selected)
    source_cards = [
        _source_card(
            SOURCE_INBOX,
            "Inbox du coffre",
            "Dossier du vault",
            _active_state(instance.physical_deposit_path() is not None, counts[SOURCE_INBOX]),
            counts[SOURCE_INBOX],
            "Fichiers deja repertories dans l'inbox locale.",
            "Proposer type et confidentialite, puis validation humaine.",
            deposit_id,
            selected,
        ),
        _source_card(
            SOURCE_DRAG_DROP,
            "Glisser-deposer",
            "Upload web local",
            "active",
            counts[SOURCE_DRAG_DROP],
            _manifest_time(selected_manifest),
            "Copie dans le coffre local, aucune transmission externe.",
            deposit_id,
            selected,
        ),
        *configured_cards,
        _source_card(
            SOURCE_MAILBOX,
            "Mailbox",
            "Connecteur futur",
            "connector_later",
            counts[SOURCE_MAILBOX],
            "Aucun IMAP/OAuth actif dans ce lot.",
            "Connexion explicite, permissions minimales, revocation visible.",
            deposit_id,
            selected,
        ),
        _source_card(
            SOURCE_FUTURE,
            "Autres canaux",
            "Extension future",
            "future",
            0,
            "Portail, formulaire ou canal externe plus tard.",
            "Toujours passer par la file a qualifier.",
            deposit_id,
            selected,
        ),
    ]
    return {
        "selected_source": selected,
        "selected_label": SOURCE_LABELS.get(selected, SOURCE_LABELS[SOURCE_ALL]),
        "source_cards": source_cards,
        "source_filters": _source_filters(counts, deposit_id, selected),
        "total_to_qualify": counts[SOURCE_ALL],
        "active_source_count": sum(1 for card in source_cards if card["state"] == "active"),
        "configured_source_count": len(configured_cards),
        "human_review_notice": "Prequalification locale: CoproScope propose, vous confirmez avant classement, rattachement ou diffusion.",
    }


def _configured_source_cards(
    instance: InstanceConfig,
    counts: dict[str, int],
    deposit_id: str,
    selected: str,
) -> list[dict[str, object]]:
    configured = _configured_sources(instance)
    if not configured:
        return [
            _source_card(
                SOURCE_LOCAL_FOLDER,
                "Dossier local",
                "Dossier surveille",
                "needs_setup",
                counts[SOURCE_LOCAL_FOLDER],
                "A regler dans les parametres d'instance.",
                "Lecture locale seulement; chemins masques dans l'UI.",
                deposit_id,
                selected,
            ),
            _source_card(
                SOURCE_DRIVE_DESKTOP,
                "Drive Desktop",
                "Dossier synchronise local",
                "needs_setup",
                counts[SOURCE_DRIVE_DESKTOP],
                "Aucun connecteur cloud actif.",
                "Traite comme dossier local; le cloud n'est pas source de verite.",
                deposit_id,
                selected,
            ),
        ]
    cards: list[dict[str, object]] = []
    for item in configured:
        source_id = normalize_document_intake_source(item.get("id") or item.get("kind"))
        if source_id not in {SOURCE_LOCAL_FOLDER, SOURCE_DRIVE_DESKTOP}:
            continue
        state = _state_value(item.get("state") or item.get("status") or "active")
        label = _safe_label(item.get("label")) or SOURCE_LABELS[source_id]
        cards.append(
            _source_card(
                source_id,
                label,
                "Dossier local" if source_id == SOURCE_LOCAL_FOLDER else "Drive Desktop local",
                state,
                counts[source_id],
                "Source configuree sans afficher son chemin.",
                "Regles locales de prequalification, confirmation humaine obligatoire.",
                deposit_id,
                selected,
            )
        )
    return cards or _configured_source_cards_without_settings(counts, deposit_id, selected)


def _configured_source_cards_without_settings(
    counts: dict[str, int],
    deposit_id: str,
    selected: str,
) -> list[dict[str, object]]:
    return [
        _source_card(
            SOURCE_LOCAL_FOLDER,
            "Dossier local",
            "Dossier surveille",
            "needs_setup",
            counts[SOURCE_LOCAL_FOLDER],
            "A regler dans les parametres d'instance.",
            "Lecture locale seulement; chemins masques dans l'UI.",
            deposit_id,
            selected,
        )
    ]


def _configured_sources(instance: InstanceConfig) -> list[Mapping[str, object]]:
    raw = instance.settings().get("intake_sources") or instance.settings().get("sources_absorption") or []
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, Mapping)]


def _source_counts(upload_rows: list[dict[str, object]], register_rows: list[dict[str, object]]) -> dict[str, int]:
    counts = {source_id: 0 for source_id in SOURCE_IDS}
    counts[SOURCE_DRAG_DROP] = len(upload_rows)
    for row in register_rows:
        source_id = normalize_document_intake_source(row.get("source_id"))
        if source_id in counts:
            counts[source_id] += 1
    counts[SOURCE_ALL] = len(_dedupe_rows([*upload_rows, *register_rows]))
    return counts


def _source_filters(counts: dict[str, int], deposit_id: str, selected: str) -> list[dict[str, object]]:
    filters = [SOURCE_ALL, SOURCE_INBOX, SOURCE_DRAG_DROP, SOURCE_LOCAL_FOLDER, SOURCE_DRIVE_DESKTOP, SOURCE_MAILBOX]
    return [
        {
            "id": source_id,
            "label": SOURCE_LABELS[source_id],
            "count": counts.get(source_id, 0),
            "href": _source_href(source_id, deposit_id),
            "selected": source_id == selected,
        }
        for source_id in filters
    ]


def _source_card(
    source_id: str,
    label: str,
    kind_label: str,
    state: str,
    count: int,
    last_absorption: str,
    rule_label: str,
    deposit_id: str,
    selected: str,
) -> dict[str, object]:
    normalized_state = _state_value(state)
    return {
        "id": source_id,
        "label": label,
        "kind_label": kind_label,
        "state": normalized_state,
        "state_label": STATE_LABELS[normalized_state],
        "state_tone": STATE_TONES[normalized_state],
        "count": count,
        "last_absorption": last_absorption,
        "rule_label": rule_label,
        "href": _source_href(source_id, deposit_id),
        "selected": source_id == selected,
    }


def _source_href(source_id: str, deposit_id: str) -> str:
    query: dict[str, str] = {}
    if source_id != SOURCE_ALL:
        query["source"] = source_id
    if deposit_id and source_id in {SOURCE_ALL, SOURCE_DRAG_DROP}:
        query["depot"] = deposit_id
    return f"/documents/ajouter?{urlencode(query)}" if query else "/documents/ajouter"


def _dedupe_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[str] = set()
    result: list[dict[str, object]] = []
    for row in rows:
        key = str(row.get("doc_id") or row.get("local_reference") or len(result))
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _active_state(has_config: bool, count: int) -> str:
    if has_config or count:
        return "active"
    return "needs_setup"


def _manifest_time(manifest: Mapping[str, object] | None) -> str:
    if not isinstance(manifest, Mapping):
        return "Dernier depot web non selectionne."
    return _safe_label(manifest.get("updated_at") or manifest.get("created_at")) or "Depot web recent."


def _state_value(value: object) -> str:
    token = _token(value)
    aliases = {
        "actif": "active",
        "active": "active",
        "paused": "paused",
        "pause": "paused",
        "en_pause": "paused",
        "needs_setup": "needs_setup",
        "a_configurer": "needs_setup",
        "connector_later": "connector_later",
        "a_connecter": "connector_later",
        "future": "future",
        "futur": "future",
    }
    return aliases.get(token, "active")


def _safe_label(value: object) -> str:
    text = " ".join(str(value or "").replace("\x00", " ").split()).strip()
    if not text:
        return ""
    if re.search(r"([A-Za-z]:[\\/]|^/|^\\\\|file://|https?://|@|[\\/])", text, flags=re.IGNORECASE):
        return ""
    return text[:120]


def _token(value: object) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower()).strip("_")
