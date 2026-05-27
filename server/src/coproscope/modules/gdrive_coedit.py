from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable, Mapping


COEDIT_PROTOCOL = "coproscope-drive-coedit-v1"
CHANGE_DIR = "changes"
CHANGE_SUFFIX = ".change"
MAX_PARENT_COUNT = 32
MERGE_POLICY = "crdt-local-merge-or-human-conflict"
CONFLICT_POLICY = "no-silent-overwrite"
INTENT_DISCLOSURE = "synthetic-logical-targets-only"

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_CHANGE_DIR_RE = re.compile(r"^[0-9a-f]{2}$")
_FORBIDDEN_SEGMENTS = {
    ".git",
    ".venv",
    "__pycache__",
    "cache",
    "decrypted",
    "exports",
    "logs",
    "private",
    "raw",
    "restricted",
    "staging",
    "temp",
    "tmp",
}
_FORBIDDEN_INTENT_KEYS = {
    "body",
    "cleartext",
    "content",
    "diff",
    "document",
    "patch",
    "plaintext",
    "raw",
    "text",
}


def prepare_encrypted_change_packet(
    *,
    sync_root: str | Path,
    encrypted_change_path: str | Path | None = None,
    object_sha256: str,
    actor_key_sha256: str,
    device_key_sha256: str,
    parents: Iterable[str] | None = None,
    sequence: int = 1,
) -> dict[str, object]:
    root = Path(sync_root).expanduser().resolve()
    candidate = (
        _candidate_from_argument(root, encrypted_change_path)
        if encrypted_change_path is not None
        else _first_change_candidate(root)
    )
    normalized = {
        "object_sha256": _normalize_sha256(object_sha256, "object"),
        "actor_key_sha256": _normalize_sha256(actor_key_sha256, "actor key"),
        "device_key_sha256": _normalize_sha256(device_key_sha256, "device key"),
        "parents": _normalize_parents(parents),
        "sequence": _normalize_sequence(sequence),
    }
    if candidate is None:
        gate = _blocked_gate("missing_change_packet", "Coedition packet blocked before Drive: no encrypted change packet is available.")
    else:
        gate = guard_encrypted_change_packet_candidate(sync_root=root, encrypted_change_path=candidate)

    return {
        "status": "prepared" if gate.get("ok") else "blocked",
        "protocol": COEDIT_PROTOCOL,
        "upload_attempted": False,
        "gate": gate,
        "change_packet": _change_manifest(gate, normalized),
        "merge_contract": _merge_contract(gate, normalized),
        "next_action": _next_action(bool(gate.get("ok"))),
    }


def simulate_two_device_coedition(
    *,
    first_packet: Mapping[str, object],
    first_intent: Mapping[str, object],
    second_packet: Mapping[str, object],
    second_intent: Mapping[str, object],
) -> dict[str, object]:
    first_summary, first_blockers = _packet_summary(first_packet, "first")
    second_summary, second_blockers = _packet_summary(second_packet, "second")
    first_components, first_intent_blockers, first_intent_conflicts = _intent_components(first_intent, "first")
    second_components, second_intent_blockers, second_intent_conflicts = _intent_components(second_intent, "second")
    blockers = [
        *first_blockers,
        *second_blockers,
        *first_intent_blockers,
        *second_intent_blockers,
    ]

    object_sha256 = None
    branch = None
    if first_summary and second_summary:
        if first_summary["object_sha256"] != second_summary["object_sha256"]:
            blockers.append({"side": "pair", "code": "object_sha256_mismatch"})
        else:
            object_sha256 = str(first_summary["object_sha256"])
            branch = _branch_metadata(first_summary, second_summary)

    base = _simulation_base(object_sha256, first_summary, second_summary, branch)
    if blockers:
        return {
            **base,
            "status": "blocked",
            "blockers": blockers,
            "merge": None,
            "conflict": None,
            "ordered_result": None,
            "next_action": "Prepare valid encrypted change packets for the same object before merge planning.",
        }

    intent_conflicts = [*first_intent_conflicts, *second_intent_conflicts]
    if intent_conflicts:
        return _conflict_result(
            base,
            "intent_metadata_missing",
            intent_conflicts,
            "Add synthetic component hashes before local merge planning.",
        )

    first_set = set(first_components)
    second_set = set(second_components)
    same_packet = bool(first_summary and second_summary and first_summary["packet_sha256"] == second_summary["packet_sha256"])
    if same_packet:
        return {
            **base,
            "status": "noop",
            "blockers": [],
            "merge": None,
            "conflict": None,
            "ordered_result": {
                "type": "idempotent_same_packet",
                "packet_sha256": first_summary["packet_sha256"] if first_summary else None,
                "component_sha256s": sorted(first_set | second_set),
            },
            "next_action": "Duplicate packet already represented locally; no merge or upload was attempted.",
        }

    if branch and branch["relation"] == "linear":
        return {
            **base,
            "status": "ordered",
            "blockers": [],
            "merge": None,
            "conflict": None,
            "ordered_result": {
                "type": "causal_packet_order",
                "order": _causal_packet_order(first_summary, second_summary),
                "component_sha256s": sorted(first_set | second_set),
            },
            "next_action": "Apply the causal packet order locally; this is not a concurrent merge.",
        }

    if not branch or not branch.get("shared_parent_sha256s"):
        return _conflict_result(
            base,
            "ambiguous_parentage",
            [{"side": "pair", "code": "shared_base_parent_required"}],
            "Publish a change packet with shared parent metadata before claiming a merge.",
        )

    overlap = sorted(first_set & second_set)
    if overlap:
        return {
            **base,
            "status": "conflict",
            "blockers": [],
            "merge": None,
            "conflict": {
                "type": "overlapping_component_hashes",
                "component_sha256s": overlap,
                "resolution": "human-review-required",
            },
            "ordered_result": None,
            "next_action": "Resolve the overlapping logical targets before publishing a merged state.",
        }

    return {
        **base,
        "status": "merged",
        "blockers": [],
        "merge": {
            "type": "concurrent_disjoint_component_hashes",
            "component_sha256s": sorted(first_set | second_set),
            "proof": "shared-parent-and-disjoint-synthetic-components",
        },
        "conflict": None,
        "ordered_result": None,
        "next_action": "Local merge plan is valid for these synthetic targets; no upload was attempted.",
    }


def guard_encrypted_change_packet_candidate(
    *,
    sync_root: str | Path,
    encrypted_change_path: str | Path,
) -> dict[str, object]:
    root = Path(sync_root).expanduser().resolve()
    candidate = Path(encrypted_change_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return _blocked_gate("missing_sync_root", "Coedition packet blocked before Drive: encrypted sync surface is not ready.")
    if not candidate.exists() or not candidate.is_file():
        return _blocked_gate("missing_change_packet", "Coedition packet blocked before Drive: encrypted change packet is not available.")
    if not _is_relative_to(candidate, root):
        return _blocked_gate("outside_sync_root", "Coedition packet blocked before Drive: packet is outside the encrypted sync surface.")

    relative = candidate.relative_to(root)
    if _contains_forbidden_segment(relative):
        return _blocked_gate("forbidden_source_location", "Coedition packet blocked before Drive: packet is not in the encrypted change log.")
    if not _is_allowed_change_packet(relative):
        return _blocked_gate("not_encrypted_change_log", "Coedition packet blocked before Drive: packet does not match the encrypted change log.")

    packet_hash = _sha256_file(candidate)
    if candidate.stat().st_size == 0:
        return _blocked_gate("empty_change_packet", "Coedition packet blocked before Drive: encrypted change packet is empty.")
    if Path(relative.name).stem != packet_hash:
        return _blocked_gate("hash_name_mismatch", "Coedition packet blocked before Drive: packet name does not match its hash.")

    return {
        "ok": True,
        "code": "encrypted_coedit_change",
        "relative_path": relative.as_posix(),
        "size_bytes": candidate.stat().st_size,
        "sha256": packet_hash,
        "path_disclosure": "relative-vault-path-only",
    }


def _candidate_from_argument(sync_root: Path, encrypted_change_path: str | Path) -> Path:
    candidate = Path(encrypted_change_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return sync_root / candidate


def _first_change_candidate(sync_root: Path) -> Path | None:
    for path in sorted(sync_root.glob(f"{CHANGE_DIR}/*/*{CHANGE_SUFFIX}")):
        if path.is_file():
            return path
    return None


def _normalize_sha256(value: str, label: str) -> str:
    normalized = str(value or "").strip().lower()
    if not _SHA256_HEX_RE.fullmatch(normalized):
        raise ValueError(f"Coedition {label} must be a sha256 hex value.")
    return normalized


def _normalize_parents(parents: Iterable[str] | None) -> list[str]:
    normalized: list[str] = []
    for parent in parents or ():
        parent_hash = _normalize_sha256(parent, "parent")
        if parent_hash not in normalized:
            normalized.append(parent_hash)
    if len(normalized) > MAX_PARENT_COUNT:
        raise ValueError("Coedition parent list is too large.")
    return normalized


def _normalize_sequence(sequence: int) -> int:
    if not isinstance(sequence, int) or sequence < 1:
        raise ValueError("Coedition sequence must be a positive integer.")
    return sequence


def _blocked_gate(code: str, message: str) -> dict[str, object]:
    return {
        "ok": False,
        "code": code,
        "message": message,
        "path_disclosure": "blocked",
    }


def _contains_forbidden_segment(relative_path: Path) -> bool:
    return any(part.lower() in _FORBIDDEN_SEGMENTS for part in relative_path.parts)


def _is_allowed_change_packet(relative_path: Path) -> bool:
    parts = relative_path.parts
    if len(parts) != 3 or parts[0] != CHANGE_DIR:
        return False
    file_name = Path(parts[2])
    return bool(
        _CHANGE_DIR_RE.fullmatch(parts[1])
        and _SHA256_HEX_RE.fullmatch(file_name.stem)
        and file_name.suffix == CHANGE_SUFFIX
    )


def _change_manifest(gate: dict[str, object], normalized: dict[str, object]) -> dict[str, object] | None:
    if not gate.get("ok"):
        return None
    packet_hash = str(gate["sha256"])
    return {
        "protocol": COEDIT_PROTOCOL,
        "packet_kind": "encrypted_change",
        "relative_path": gate["relative_path"],
        "size_bytes": gate["size_bytes"],
        "sha256": packet_hash,
        "remote_name": _remote_change_name(packet_hash),
        "object_sha256": normalized["object_sha256"],
        "actor_key_sha256": normalized["actor_key_sha256"],
        "device_key_sha256": normalized["device_key_sha256"],
        "parents": normalized["parents"],
        "sequence": normalized["sequence"],
        "cleartext_content": "forbidden",
        "identity_disclosure": "pseudonymous-key-fingerprints-only",
    }


def _merge_contract(gate: dict[str, object], normalized: dict[str, object]) -> dict[str, object] | None:
    if not gate.get("ok"):
        return None
    return {
        "mode": "append-only-encrypted-change-log",
        "merge_policy": MERGE_POLICY,
        "conflict_policy": CONFLICT_POLICY,
        "parent_count": len(normalized["parents"]),
        "allows_parallel_parents": True,
        "silent_overwrite": "forbidden",
    }


def _next_action(gate_ok: bool) -> str:
    if not gate_ok:
        return "Use only encrypted coedition change packets before enabling Drive transport."
    return "Ready for local coedition merge planning; no Drive upload was attempted."


def _remote_change_name(packet_hash: str) -> str:
    return f"coproscope-coedit-change-{packet_hash[:12]}{CHANGE_SUFFIX}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _packet_summary(
    prepared_packet: Mapping[str, object],
    side: str,
) -> tuple[dict[str, object] | None, list[dict[str, str]]]:
    if not isinstance(prepared_packet, Mapping):
        return None, [{"side": side, "code": "packet_not_mapping"}]
    if prepared_packet.get("protocol") != COEDIT_PROTOCOL:
        return None, [{"side": side, "code": "protocol_mismatch"}]
    if prepared_packet.get("status") != "prepared":
        return None, [{"side": side, "code": "packet_blocked", "gate_code": _gate_code(prepared_packet)}]
    gate = prepared_packet.get("gate")
    if not isinstance(gate, Mapping) or gate.get("ok") is not True:
        return None, [{"side": side, "code": "packet_gate_blocked", "gate_code": _gate_code(prepared_packet)}]
    change_packet = prepared_packet.get("change_packet")
    if not isinstance(change_packet, Mapping):
        return None, [{"side": side, "code": "missing_change_packet_manifest"}]
    if change_packet.get("protocol") != COEDIT_PROTOCOL:
        return None, [{"side": side, "code": "change_packet_protocol_mismatch"}]

    try:
        packet_hash = _normalize_sha256(str(change_packet.get("sha256", "")), "packet")
        object_hash = _normalize_sha256(str(change_packet.get("object_sha256", "")), "object")
        actor_hash = _normalize_sha256(str(change_packet.get("actor_key_sha256", "")), "actor key")
        device_hash = _normalize_sha256(str(change_packet.get("device_key_sha256", "")), "device key")
        parents = _normalize_parents(_sequence_of_strings(change_packet.get("parents")))
        display_sequence = _normalize_sequence(change_packet.get("sequence"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None, [{"side": side, "code": "invalid_change_packet_manifest"}]

    return {
        "side": side,
        "packet_sha256": packet_hash,
        "object_sha256": object_hash,
        "actor_key_sha256": actor_hash,
        "device_key_sha256": device_hash,
        "parents": parents,
        "display_sequence": display_sequence,
        "intent_disclosure": INTENT_DISCLOSURE,
    }, []


def _gate_code(prepared_packet: Mapping[str, object]) -> str:
    gate = prepared_packet.get("gate")
    if isinstance(gate, Mapping):
        code = gate.get("code")
        if isinstance(code, str) and code:
            return code
    return "unavailable"


def _sequence_of_strings(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise TypeError("Expected a sequence.")
    return [str(item) for item in value]


def _intent_components(
    intent: Mapping[str, object],
    side: str,
) -> tuple[list[str], list[dict[str, str]], list[dict[str, str]]]:
    if not isinstance(intent, Mapping):
        return [], [{"side": side, "code": "intent_not_mapping"}], []
    if any(str(key).lower() in _FORBIDDEN_INTENT_KEYS for key in intent):
        return [], [{"side": side, "code": "cleartext_intent_forbidden"}], []

    raw_components = _raw_component_hashes(intent)
    if raw_components is None:
        return [], [], [{"side": side, "code": "component_hashes_required"}]

    components: list[str] = []
    for component in raw_components:
        try:
            normalized = _normalize_sha256(str(component or ""), "component")
        except ValueError:
            return [], [{"side": side, "code": "invalid_component_hash"}], []
        if normalized not in components:
            components.append(normalized)
    if not components:
        return [], [], [{"side": side, "code": "component_hashes_required"}]
    return sorted(components), [], []


def _raw_component_hashes(intent: Mapping[str, object]) -> list[object] | None:
    for key in ("component_sha256s", "component_hashes"):
        value = intent.get(key)
        if isinstance(value, (list, tuple, set)):
            return list(value)
        if isinstance(value, str):
            return [value]
    for key in ("component_sha256", "component_hash"):
        value = intent.get(key)
        if isinstance(value, str):
            return [value]
    return None


def _branch_metadata(first: Mapping[str, object], second: Mapping[str, object]) -> dict[str, object]:
    first_hash = str(first["packet_sha256"])
    second_hash = str(second["packet_sha256"])
    first_parents = list(first["parents"])  # type: ignore[arg-type]
    second_parents = list(second["parents"])  # type: ignore[arg-type]
    first_depends_on_second = second_hash in first_parents
    second_depends_on_first = first_hash in second_parents
    shared_parent_sha256s = sorted(set(first_parents) & set(second_parents))
    parent_sets_match = set(first_parents) == set(second_parents)
    if first_depends_on_second or second_depends_on_first:
        relation = "linear"
        branch_detected = False
    elif shared_parent_sha256s:
        relation = "parallel-shared-parent"
        branch_detected = True
    else:
        relation = "ambiguous-parents"
        branch_detected = False
    return {
        "branch_detected": branch_detected,
        "relation": relation,
        "shared_parent_sha256s": shared_parent_sha256s,
        "parent_sets_match": parent_sets_match,
        "parent_counts": {
            "first": len(first_parents),
            "second": len(second_parents),
        },
        "display_sequence": {
            "first": first["display_sequence"],
            "second": second["display_sequence"],
        },
        "causal_links": {
            "first_depends_on_second": first_depends_on_second,
            "second_depends_on_first": second_depends_on_first,
        },
    }


def _causal_packet_order(
    first: Mapping[str, object] | None,
    second: Mapping[str, object] | None,
) -> list[dict[str, object]]:
    if not first or not second:
        return []
    second_hash = str(second["packet_sha256"])
    if second_hash in first["parents"]:  # type: ignore[operator]
        ordered = (second, first)
    else:
        ordered = (first, second)
    return [
        {
            "packet_sha256": packet["packet_sha256"],
            "actor_key_sha256": packet["actor_key_sha256"],
            "device_key_sha256": packet["device_key_sha256"],
            "display_sequence": packet["display_sequence"],
        }
        for packet in ordered
    ]


def _simulation_base(
    object_sha256: str | None,
    first_summary: Mapping[str, object] | None,
    second_summary: Mapping[str, object] | None,
    branch: Mapping[str, object] | None,
) -> dict[str, object]:
    return {
        "protocol": COEDIT_PROTOCOL,
        "object_sha256": object_sha256,
        "participants": [summary for summary in (first_summary, second_summary) if summary],
        "branch": branch,
        "silent_overwrite": "forbidden",
        "cleartext_content": "forbidden",
        "identity_disclosure": "pseudonymous-key-fingerprints-only",
        "network_attempted": False,
        "upload_attempted": False,
        "transport": {
            "network_attempted": False,
            "upload_attempted": False,
            "remote_reference": "not-required",
        },
    }


def _conflict_result(
    base: Mapping[str, object],
    conflict_type: str,
    reasons: list[dict[str, str]],
    next_action: str,
) -> dict[str, object]:
    return {
        **base,
        "status": "conflict",
        "blockers": [],
        "merge": None,
        "conflict": {
            "type": conflict_type,
            "reasons": reasons,
            "resolution": "human-review-required",
        },
        "ordered_result": None,
        "next_action": next_action,
    }
