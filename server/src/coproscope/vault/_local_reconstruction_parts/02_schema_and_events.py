from __future__ import annotations



def _upsert_member(
    connection: sqlite3.Connection,
    *,
    member_id: str | None,
    author_key_id: str | None,
    observed_at: str,
    status: str,
    display_name: str | None = None,
    email: str | None = None,
    role: str | None = None,
    public_key: str | None = None,
    key_type: str | None = None,
    revoked_at: str | None = None,
) -> str:
    normalized_author = _optional_text(author_key_id)
    normalized_member = _optional_text(member_id) or normalized_author
    if not normalized_member:
        return ""
    seen_at = observed_at or _now_iso()
    existing = connection.execute("SELECT * FROM members WHERE member_id = ?", (normalized_member,)).fetchone()
    if existing is None and normalized_author:
        existing = connection.execute("SELECT * FROM members WHERE author_key_id = ?", (normalized_author,)).fetchone()

    if existing is None:
        connection.execute(
            """
            INSERT INTO members(
                member_id, author_key_id, display_name, email, role, status,
                public_key, key_type, first_seen_at, last_seen_at, revoked_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized_member,
                normalized_author,
                display_name,
                email,
                role,
                status,
                public_key,
                key_type,
                seen_at,
                seen_at,
                revoked_at,
            ),
        )
        return normalized_member

    current_member = str(existing["member_id"])
    target_member = normalized_member
    if current_member != target_member:
        collision = connection.execute("SELECT member_id FROM members WHERE member_id = ?", (target_member,)).fetchone()
        if collision is None:
            connection.execute("UPDATE members SET member_id = ? WHERE member_id = ?", (target_member, current_member))
        else:
            target_member = current_member

    current_status = str(existing["status"])
    next_status = current_status if current_status == "revoked" and status == "active" else status
    connection.execute(
        """
        UPDATE members
        SET author_key_id = COALESCE(?, author_key_id),
            display_name = COALESCE(?, display_name),
            email = COALESCE(?, email),
            role = COALESCE(?, role),
            status = ?,
            public_key = COALESCE(?, public_key),
            key_type = COALESCE(?, key_type),
            first_seen_at = ?,
            last_seen_at = ?,
            revoked_at = COALESCE(?, revoked_at)
        WHERE member_id = ?
        """,
        (
            normalized_author,
            display_name,
            email,
            role,
            next_status,
            public_key,
            key_type,
            _earliest(existing["first_seen_at"], seen_at),
            _latest(existing["last_seen_at"], seen_at),
            revoked_at,
            target_member,
        ),
    )
    return target_member


def _upsert_device(
    connection: sqlite3.Connection,
    *,
    device_id: str | None,
    author_key_id: str | None,
    observed_at: str,
    sequence: int,
    event_id: str,
    status: str,
    member_id: str | None = None,
    increment_event_count: bool,
) -> None:
    normalized_device = _optional_text(device_id)
    if not normalized_device:
        return
    normalized_author = _optional_text(author_key_id)
    normalized_member = _optional_text(member_id) or _member_id_for_author(connection, normalized_author)
    seen_at = observed_at or _now_iso()
    existing = connection.execute("SELECT * FROM devices WHERE device_id = ?", (normalized_device,)).fetchone()
    increment = 1 if increment_event_count else 0
    if existing is None:
        connection.execute(
            """
            INSERT INTO devices(
                device_id, member_id, author_key_id, status, first_seen_at, last_seen_at,
                last_sequence, last_event_id, event_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized_device,
                normalized_member,
                normalized_author,
                status,
                seen_at,
                seen_at,
                max(sequence, 0),
                event_id,
                increment,
            ),
        )
        return

    current_status = str(existing["status"])
    next_status = current_status if current_status == "revoked" and status == "active" else status
    connection.execute(
        """
        UPDATE devices
        SET member_id = COALESCE(?, member_id),
            author_key_id = COALESCE(?, author_key_id),
            status = ?,
            first_seen_at = ?,
            last_seen_at = ?,
            last_sequence = MAX(last_sequence, ?),
            last_event_id = COALESCE(?, last_event_id),
            event_count = event_count + ?
        WHERE device_id = ?
        """,
        (
            normalized_member,
            normalized_author,
            next_status,
            _earliest(existing["first_seen_at"], seen_at),
            _latest(existing["last_seen_at"], seen_at),
            max(sequence, 0),
            event_id,
            increment,
            normalized_device,
        ),
    )


def _write_sync_state(
    connection: sqlite3.Connection,
    *,
    events: Sequence[LocalVaultEvent],
    vault_id: str,
    local_root: Path | None,
    sync_root: Path | None,
    rebuilt_at: str,
) -> None:
    latest = events[-1] if events else None
    values = {
        "schema_version": SCHEMA_VERSION,
        "vault_id": vault_id,
        "event_count": str(len(events)),
        "last_event_id": latest.event_id if latest else "",
        "last_event_hash": latest.event_hash if latest else "",
        "last_event_created_at": latest.created_at if latest else "",
        "rebuilt_at": rebuilt_at,
        "source_local_root": str(local_root) if local_root is not None else "",
        "source_sync_root": str(sync_root) if sync_root is not None else "",
    }
    for key, value in sorted(values.items()):
        connection.execute("INSERT INTO sync_state(key, value, updated_at) VALUES (?, ?, ?)", (key, value, rebuilt_at))


def _validate_document_blob(
    sync_root: Path,
    envelope: Mapping[str, Any],
    payload: Mapping[str, Any],
    path: Path,
    errors: list[str],
) -> None:
    if envelope.get("event_type") not in DOCUMENT_EVENT_TYPES:
        return
    blob_id = _optional_text(payload.get("blob_id"))
    if not blob_id:
        return
    if not _is_sha256_hex(blob_id):
        errors.append(f"{path}: invalid blob id {blob_id}")
        return
    blob_path = _safe_sync_path(sync_root, "blobs", blob_id[:2], f"{blob_id}.blob")
    if not blob_path.exists():
        errors.append(f"{path}: missing blob {blob_id}")
        return
    expected = _optional_text(payload.get("blob_sha256"))
    if expected and _sha256_file(blob_path) != expected:
        errors.append(f"{path}: invalid blob hash {blob_id}")


def _verify_signature(sync_root: Path, event: Mapping[str, Any]) -> None:
    crypto = _require_crypto()
    signature = _unb64(str(event["signature"]))
    signed = dict(event)
    signed.pop("signature", None)
    author_key_id = str(event["author_key_id"])
    if not _is_safe_sync_id(author_key_id):
        raise RuntimeError(f"Invalid author_key_id: {author_key_id}")
    key_payload = _read_json(_safe_sync_path(sync_root, "keys", f"{author_key_id}.json"))
    public_key = crypto["ed25519"].Ed25519PublicKey.from_public_bytes(_unb64(str(key_payload["public_key"])))
    try:
        public_key.verify(signature, _canonical_bytes(signed))
    except crypto["InvalidSignature"] as exc:
        raise RuntimeError("Invalid event signature") from exc


def _decrypt_payload(state: Mapping[str, Any], event: Mapping[str, Any]) -> dict[str, Any]:
    crypto = _require_crypto()
    aesgcm = crypto["AESGCM"](_unb64(str(state["vault_key"])))
    plaintext = aesgcm.decrypt(
        _unb64(str(event["payload_nonce"])),
        _unb64(str(event["encrypted_payload"])),
        None,
    )
    payload = json.loads(plaintext.decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid decrypted payload for event {event.get('event_id')}")
    return payload


def _require_crypto() -> dict[str, Any]:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Local vault reconstruction requires the 'cryptography' package.") from exc
    return {"AESGCM": AESGCM, "InvalidSignature": InvalidSignature, "ed25519": ed25519}


def _load_state(local_root: Path) -> dict[str, Any]:
    path = local_root / LOCAL_STATE_FILE
    if not path.exists():
        raise RuntimeError(f"Vault local state not found: {path}")
    state = _read_json(path)
    if not isinstance(state, dict):
        raise RuntimeError(f"Invalid vault local state: {path}")
    return state


def _read_vault_id(sync_root: Path) -> str:
    vault_file = sync_root / "vault.json"
    if not vault_file.exists():
        return ""
    payload = _read_json(vault_file)
    return str(payload.get("vault_id", "")) if isinstance(payload, dict) else ""


def _read_key_records(sync_root: Path) -> list[dict[str, Any]]:
    key_root = sync_root / "keys"
    if not key_root.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(key_root.glob("*.json")):
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Invalid key record: {path}")
        records.append(payload)
    return records


def _event_paths_by_device(sync_root: Path) -> dict[str, list[Path]]:
    event_root = sync_root / "events"
    if not event_root.exists():
        return {}
    paths_by_device: dict[str, list[Path]] = {}
    for path in sorted(event_root.glob("*/*.json")):
        if path.is_file():
            paths_by_device.setdefault(path.parent.name, []).append(path)
    return {device_id: sorted(paths) for device_id, paths in sorted(paths_by_device.items())}


def _event_sort_key(event: LocalVaultEvent) -> tuple[str, str, int, str]:
    return (event.created_at, event.device_id, event.sequence, event.event_id)


def _member_id_from_payload(event: LocalVaultEvent) -> str:
    for key in ("member_id", "target_member_id", "revoked_member_id"):
        value = _optional_text(event.payload.get(key))
        if value:
            return value
    return ""


def _member_author_key_from_payload(event: LocalVaultEvent) -> str:
    for key in ("member_author_key_id", "target_author_key_id", "revoked_author_key_id", "author_key_id"):
        value = _optional_text(event.payload.get(key))
        if value:
            return value
    return ""


def _device_id_from_payload(event: LocalVaultEvent) -> str:
    for key in ("device_id", "target_device_id", "revoked_device_id"):
        value = _optional_text(event.payload.get(key))
        if value:
            return value
    return ""


def _member_id_for_author(connection: sqlite3.Connection, author_key_id: str | None) -> str | None:
    normalized_author = _optional_text(author_key_id)
    if not normalized_author:
        return None
    row = connection.execute("SELECT member_id FROM members WHERE author_key_id = ?", (normalized_author,)).fetchone()
    return str(row["member_id"]) if row is not None else normalized_author


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return bool(SHA256_HEX_RE.fullmatch(value))


def _is_safe_sync_id(value: str) -> bool:
    return bool(SAFE_SYNC_ID_RE.fullmatch(value))


def _safe_sync_path(sync_root: Path, *parts: str) -> Path:
    root = Path(sync_root).expanduser().resolve()
    path = root.joinpath(*parts).resolve()
    if not _is_relative_to(path, root):
        raise RuntimeError(f"Vault sync path escaped sync_root: {path}")
    return path


def _expected_hash_from_filename(path: Path) -> str:
    parts = path.stem.split("_", 1)
    return parts[1] if len(parts) == 2 else ""


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _earliest(left: Any, right: str) -> str:
    left_text = _optional_text(left)
    if not left_text:
        return right
    if not right:
        return left_text
    return min(left_text, right)


def _latest(left: Any, right: str) -> str:
    left_text = _optional_text(left)
    if not left_text:
        return right
    if not right:
        return left_text
    return max(left_text, right)


def _count_rows(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row is not None else 0


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
