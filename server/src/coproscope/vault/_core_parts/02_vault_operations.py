from __future__ import annotations



def vault_verify(local_root: Path, sync_root: Path) -> dict[str, Any]:
    roots = VaultRoots(local_root=local_root.resolve(), sync_root=sync_root.resolve())
    errors: list[str] = []
    state: dict[str, Any] | None = None
    state_vault_id = ""
    try:
        state = _load_state(roots.local_root)
        state_vault_id = str(state.get("vault_id", ""))
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))

    vault_file = roots.sync_root / "vault.json"
    vault_id = ""
    if not vault_file.exists():
        errors.append(f"Missing vault.json: {vault_file}")
    else:
        try:
            vault_payload = _read_json(vault_file)
            if not isinstance(vault_payload, dict):
                raise RuntimeError("Invalid vault.json payload")
            vault_id = str(vault_payload.get("vault_id", ""))
            if not vault_id:
                errors.append(f"{vault_file}: missing vault_id")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{vault_file}: {exc}")
    expected_vault_id = vault_id or state_vault_id
    if vault_id and state_vault_id and vault_id != state_vault_id:
        errors.append(f"{vault_file}: vault_id does not match local state")
    for forbidden in _forbidden_sync_entries(roots.sync_root):
        errors.append(f"Forbidden development/runtime entry in sync root: {forbidden}")

    events_by_device: dict[str, list[Path]] = {}
    for path in _all_event_files(roots.sync_root):
        events_by_device.setdefault(path.parent.name, []).append(path)

    event_count = 0
    for device_id, files in sorted(events_by_device.items()):
        expected_prev = ""
        expected_sequence = 1
        for path in sorted(files):
            event_count += 1
            try:
                raw = path.read_bytes()
                file_hash = _sha256_bytes(raw)
                expected_file_hash = _expected_hash_from_filename(path)
                if expected_file_hash and file_hash != expected_file_hash:
                    errors.append(f"{path}: event hash does not match filename")
                event = json.loads(raw.decode("utf-8"))
                if event.get("device_id") != device_id:
                    errors.append(f"{path}: device_id does not match directory")
                if event.get("sequence") != expected_sequence:
                    errors.append(f"{path}: expected sequence {expected_sequence}, got {event.get('sequence')}")
                if event.get("prev_device_event_hash") != expected_prev:
                    errors.append(f"{path}: invalid previous event hash")
                ciphertext = _unb64(str(event.get("encrypted_payload", "")))
                if _sha256_bytes(ciphertext) != event.get("encrypted_payload_hash"):
                    errors.append(f"{path}: invalid encrypted payload hash")
                _verify_signature(roots.sync_root, event)
                if state is not None:
                    payload = _decrypt_payload(state, event)
                    if event.get("event_type") in {"document_added", "document_version_added"}:
                        blob_id = str(payload.get("blob_id", ""))
                        blob_path = _blob_path(roots.sync_root, blob_id)
                        if not blob_path.exists():
                            errors.append(f"{path}: missing blob {blob_id}")
                        elif _sha256_file(blob_path) != payload.get("blob_sha256"):
                            errors.append(f"{path}: invalid blob hash {blob_id}")
                expected_prev = file_hash
                expected_sequence += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path}: {exc}")

    snapshot_count = 0
    for path in _all_snapshot_files(roots.sync_root):
        snapshot_count += 1
        try:
            raw = path.read_bytes()
            file_hash = _sha256_bytes(raw)
            expected_file_hash = _expected_hash_from_filename(path)
            if expected_file_hash and file_hash != expected_file_hash:
                errors.append(f"{path}: snapshot hash does not match filename")
            snapshot = json.loads(raw.decode("utf-8"))
            if not isinstance(snapshot, dict):
                raise RuntimeError("Invalid snapshot JSON payload")
            if expected_vault_id and snapshot.get("vault_id") != expected_vault_id:
                errors.append(f"{path}: vault_id does not match vault")
            ciphertext = _unb64(str(snapshot.get("encrypted_payload", "")))
            if _sha256_bytes(ciphertext) != snapshot.get("encrypted_payload_hash"):
                errors.append(f"{path}: invalid encrypted payload hash")
            if state is not None:
                try:
                    _decrypt_payload(state, snapshot)
                except Exception as exc:  # noqa: BLE001
                    raise RuntimeError("snapshot encrypted payload is not decryptable") from exc
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: {exc}")
    return {
        "ok": not errors,
        "valid": not errors,
        "command": "vault verify",
        "local_root": str(roots.local_root),
        "sync_root": str(roots.sync_root),
        "events": event_count,
        "snapshots": snapshot_count,
        "errors": errors,
    }


def vault_snapshot(local_root: Path, sync_root: Path) -> dict[str, Any]:
    roots = VaultRoots(local_root=local_root.resolve(), sync_root=sync_root.resolve())
    state = _load_state(roots.local_root)
    summary = vault_status(roots.local_root, roots.sync_root)
    summary["created_at"] = _now_iso()
    nonce, ciphertext, encrypted_hash = _encrypt_payload(state, summary)
    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "vault_id": state["vault_id"],
        "created_at": summary["created_at"],
        "payload_nonce": nonce,
        "encrypted_payload": ciphertext,
        "encrypted_payload_hash": encrypted_hash,
    }
    snapshot_id = _sha256_bytes(_canonical_bytes(snapshot))
    snapshot_path = roots.sync_root / "snapshots" / f"{summary['created_at'].replace(':', '').replace('+', 'Z')}_{snapshot_id}.snapshot"
    _write_json(snapshot_path, snapshot, canonical=True)
    return {
        "ok": True,
        "command": "vault snapshot",
        "snapshot_path": str(snapshot_path),
        "snapshot_hash": _sha256_file(snapshot_path),
    }


def vault_export_debug_payload(local_root: Path, sync_root: Path, event_path: Path) -> dict[str, Any]:
    """Test helper for local verification; never writes decrypted content to sync."""
    roots = VaultRoots(local_root=local_root.resolve(), sync_root=sync_root.resolve())
    state = _load_state(roots.local_root)
    event = _read_json(event_path)
    return _decrypt_payload(state, event)


def reset_vault_for_tests(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
