from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any


ARCHIVE_SCHEMA_VERSION = "coproscope-vault-reconstruction-archive-v1"
READABLE = "readable"
RESTRICTED = "restricted"
SEALED_PREFIX = b"COPROSCOPE-SEALED-V1\n"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _json_bytes(value: Any) -> bytes:
    return _canonical_json(value).encode("utf-8")


def _keystream(key: str, nonce: str, length: int) -> bytes:
    material = key.encode("utf-8") + b"\0" + nonce.encode("ascii")
    chunks: list[bytes] = []
    counter = 0
    while sum(len(chunk) for chunk in chunks) < length:
        chunks.append(hashlib.sha256(material + counter.to_bytes(4, "big")).digest())
        counter += 1
    return b"".join(chunks)[:length]


def _seal_payload(payload: bytes, *, key: str, nonce: str) -> bytes:
    stream = _keystream(key, nonce, len(payload))
    ciphertext = bytes(left ^ right for left, right in zip(payload, stream, strict=True))
    return SEALED_PREFIX + nonce.encode("ascii") + b"\n" + ciphertext


def _open_payload(sealed_payload: bytes, *, key: str) -> bytes:
    if not sealed_payload.startswith(SEALED_PREFIX):
        raise ValueError("Invalid sealed payload prefix")
    rest = sealed_payload[len(SEALED_PREFIX) :]
    nonce_raw, ciphertext = rest.split(b"\n", 1)
    nonce = nonce_raw.decode("ascii")
    stream = _keystream(key, nonce, len(ciphertext))
    return bytes(left ^ right for left, right in zip(ciphertext, stream, strict=True))


@dataclass(frozen=True)
class RecoveryHelper:
    helper_id: str
    label: str
    role: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "helper_id": self.helper_id,
            "label": self.label,
            "role": self.role,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CorpusPart:
    part_id: str
    kind: str
    public_label: str
    compartment_id: str
    compartment_key: str
    payload: Mapping[str, Any]
    readable_by: tuple[str, ...] = ("coowner",)
    recovery_helpers: tuple[RecoveryHelper, ...] = ()
    restriction_reason: str = "Compartiment reserve ou cle absente."


@dataclass(frozen=True)
class ArchiveEntry:
    part_id: str
    kind: str
    public_label: str
    compartment_id: str
    access: str
    restriction_reason: str
    sealed_size: int
    sealed_sha256: str
    payload_commitment_sha256: str
    existence_proof_sha256: str
    recovery_helpers: tuple[RecoveryHelper, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "part_id": self.part_id,
            "kind": self.kind,
            "public_label": self.public_label,
            "compartment_id": self.compartment_id,
            "access": self.access,
            "restriction_reason": self.restriction_reason,
            "sealed_size": self.sealed_size,
            "sealed_sha256": self.sealed_sha256,
            "payload_commitment_sha256": self.payload_commitment_sha256,
            "existence_proof_sha256": self.existence_proof_sha256,
            "recovery_helpers": [helper.as_dict() for helper in self.recovery_helpers],
        }


@dataclass(frozen=True)
class ArchiveManifest:
    archive_id: str
    vault_id: str
    recipient_role: str
    created_at: str
    entries: tuple[ArchiveEntry, ...]
    schema_version: str = ARCHIVE_SCHEMA_VERSION
    manifest_sha256: str = ""

    @classmethod
    def build(
        cls,
        *,
        archive_id: str,
        vault_id: str,
        recipient_role: str,
        created_at: str,
        entries: Iterable[ArchiveEntry],
    ) -> "ArchiveManifest":
        manifest = cls(
            archive_id=archive_id,
            vault_id=vault_id,
            recipient_role=recipient_role,
            created_at=created_at,
            entries=tuple(sorted(entries, key=lambda entry: entry.part_id)),
        )
        return cls(
            archive_id=manifest.archive_id,
            vault_id=manifest.vault_id,
            recipient_role=manifest.recipient_role,
            created_at=manifest.created_at,
            entries=manifest.entries,
            manifest_sha256=_sha256_text(_canonical_json(manifest.as_unsigned_dict())),
        )

    def as_unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "archive_id": self.archive_id,
            "vault_id": self.vault_id,
            "recipient_role": self.recipient_role,
            "created_at": self.created_at,
            "entries": [entry.as_dict() for entry in self.entries],
        }

    def as_dict(self) -> dict[str, Any]:
        payload = self.as_unsigned_dict()
        payload["manifest_sha256"] = self.manifest_sha256
        return payload


@dataclass(frozen=True)
class DownloadableArchive:
    archive_id: str
    vault_id: str
    recipient_role: str
    manifest: ArchiveManifest
    sealed_payloads: Mapping[str, bytes]
    recipient_compartment_keys: Mapping[str, str] = field(default_factory=dict)

    @property
    def download_name(self) -> str:
        return f"{self.archive_id}.coproscope-archive.json"


@dataclass(frozen=True)
class IntegrityFinding:
    severity: str
    code: str
    part_id: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "part_id": self.part_id,
            "message": self.message,
        }


@dataclass(frozen=True)
class IntegrityReport:
    ok: bool
    archive_id: str
    manifest_sha256: str
    findings: tuple[IntegrityFinding, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "archive_id": self.archive_id,
            "manifest_sha256": self.manifest_sha256,
            "findings": [finding.as_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class ReconstructedPart:
    part_id: str
    kind: str
    public_label: str
    compartment_id: str
    payload: Mapping[str, Any]
    payload_commitment_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "part_id": self.part_id,
            "kind": self.kind,
            "public_label": self.public_label,
            "compartment_id": self.compartment_id,
            "payload": dict(self.payload),
            "payload_commitment_sha256": self.payload_commitment_sha256,
        }


@dataclass(frozen=True)
class RestrictedPartProof:
    part_id: str
    kind: str
    public_label: str
    compartment_id: str
    reason: str
    existence_proof_sha256: str
    sealed_sha256: str
    recovery_helpers: tuple[RecoveryHelper, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "part_id": self.part_id,
            "kind": self.kind,
            "public_label": self.public_label,
            "compartment_id": self.compartment_id,
            "reason": self.reason,
            "existence_proof_sha256": self.existence_proof_sha256,
            "sealed_sha256": self.sealed_sha256,
            "recovery_helpers": [helper.as_dict() for helper in self.recovery_helpers],
        }


@dataclass(frozen=True)
class ReconstructionResult:
    archive_id: str
    vault_id: str
    recipient_role: str
    reconstructed: tuple[ReconstructedPart, ...]
    restricted: tuple[RestrictedPartProof, ...]
    integrity: IntegrityReport

    @property
    def ok(self) -> bool:
        return self.integrity.ok


@dataclass(frozen=True)
class NoviceReconstructionReport:
    archive_id: str
    can_reconstruct: tuple[dict[str, str], ...]
    exists_but_restricted: tuple[dict[str, str], ...]
    recovery_helpers: tuple[dict[str, str], ...]
    summary: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "archive_id": self.archive_id,
            "summary": self.summary,
            "ce_que_je_peux_reconstruire": list(self.can_reconstruct),
            "ce_qui_existe_mais_reste_restreint": list(self.exists_but_restricted),
            "qui_peut_aider_a_recuperer": list(self.recovery_helpers),
        }


def build_downloadable_archive(
    *,
    vault_id: str,
    archive_id: str,
    recipient_role: str,
    parts: Iterable[CorpusPart],
    recipient_compartment_keys: Mapping[str, str] | None = None,
    created_at: str = "2026-05-20T00:00:00Z",
) -> DownloadableArchive:
    keys = dict(recipient_compartment_keys or {})
    entries: list[ArchiveEntry] = []
    sealed_payloads: dict[str, bytes] = {}

    for part in sorted(parts, key=lambda item: item.part_id):
        payload_bytes = _json_bytes(dict(part.payload))
        nonce = _sha256_text(f"{archive_id}:{part.part_id}:{part.compartment_id}")[:24]
        sealed_payload = _seal_payload(payload_bytes, key=part.compartment_key, nonce=nonce)
        sealed_payloads[part.part_id] = sealed_payload
        sealed_sha256 = _sha256_bytes(sealed_payload)
        payload_sha256 = _sha256_bytes(payload_bytes)
        access = (
            READABLE
            if recipient_role in part.readable_by and keys.get(part.compartment_id) == part.compartment_key
            else RESTRICTED
        )
        entries.append(
            ArchiveEntry(
                part_id=part.part_id,
                kind=part.kind,
                public_label=part.public_label,
                compartment_id=part.compartment_id,
                access=access,
                restriction_reason="" if access == READABLE else part.restriction_reason,
                sealed_size=len(sealed_payload),
                sealed_sha256=sealed_sha256,
                payload_commitment_sha256=payload_sha256,
                existence_proof_sha256=_existence_proof(
                    archive_id=archive_id,
                    vault_id=vault_id,
                    part_id=part.part_id,
                    sealed_sha256=sealed_sha256,
                    payload_commitment_sha256=payload_sha256,
                ),
                recovery_helpers=part.recovery_helpers if access == RESTRICTED else (),
            )
        )

    manifest = ArchiveManifest.build(
        archive_id=archive_id,
        vault_id=vault_id,
        recipient_role=recipient_role,
        created_at=created_at,
        entries=entries,
    )
    return DownloadableArchive(
        archive_id=archive_id,
        vault_id=vault_id,
        recipient_role=recipient_role,
        manifest=manifest,
        sealed_payloads=sealed_payloads,
        recipient_compartment_keys=keys,
    )


def verify_archive_integrity(archive: DownloadableArchive) -> IntegrityReport:
    findings: list[IntegrityFinding] = []
    expected_manifest_hash = _sha256_text(_canonical_json(archive.manifest.as_unsigned_dict()))
    if expected_manifest_hash != archive.manifest.manifest_sha256:
        findings.append(
            IntegrityFinding(
                severity="error",
                code="manifest_hash_mismatch",
                part_id="",
                message="Le manifeste ne correspond plus a son empreinte.",
            )
        )

    seen: set[str] = set()
    for entry in archive.manifest.entries:
        if entry.part_id in seen:
            findings.append(
                IntegrityFinding(
                    severity="error",
                    code="duplicate_part",
                    part_id=entry.part_id,
                    message="Une entree apparait plusieurs fois dans le manifeste.",
                )
            )
            continue
        seen.add(entry.part_id)
        sealed_payload = archive.sealed_payloads.get(entry.part_id)
        if sealed_payload is None:
            findings.append(
                IntegrityFinding(
                    severity="error",
                    code="missing_payload",
                    part_id=entry.part_id,
                    message="Le payload chiffre annonce par le manifeste est absent.",
                )
            )
            continue
        sealed_sha256 = _sha256_bytes(sealed_payload)
        if sealed_sha256 != entry.sealed_sha256:
            findings.append(
                IntegrityFinding(
                    severity="error",
                    code="sealed_hash_mismatch",
                    part_id=entry.part_id,
                    message="Le payload chiffre ne correspond plus au manifeste.",
                )
            )
        if len(sealed_payload) != entry.sealed_size:
            findings.append(
                IntegrityFinding(
                    severity="error",
                    code="sealed_size_mismatch",
                    part_id=entry.part_id,
                    message="La taille du payload chiffre ne correspond plus au manifeste.",
                )
            )
        proof = _existence_proof(
            archive_id=archive.archive_id,
            vault_id=archive.vault_id,
            part_id=entry.part_id,
            sealed_sha256=entry.sealed_sha256,
            payload_commitment_sha256=entry.payload_commitment_sha256,
        )
        if proof != entry.existence_proof_sha256:
            findings.append(
                IntegrityFinding(
                    severity="error",
                    code="existence_proof_mismatch",
                    part_id=entry.part_id,
                    message="La preuve d'existence ne correspond plus aux empreintes.",
                )
            )

    return IntegrityReport(
        ok=not any(finding.severity == "error" for finding in findings),
        archive_id=archive.archive_id,
        manifest_sha256=expected_manifest_hash,
        findings=tuple(findings),
    )


def reconstruct_authorized_corpus(
    archive: DownloadableArchive,
    *,
    recipient_compartment_keys: Mapping[str, str] | None = None,
) -> ReconstructionResult:
    integrity = verify_archive_integrity(archive)
    if not integrity.ok:
        return ReconstructionResult(
            archive_id=archive.archive_id,
            vault_id=archive.vault_id,
            recipient_role=archive.recipient_role,
            reconstructed=(),
            restricted=(),
            integrity=integrity,
        )

    keys = dict(archive.recipient_compartment_keys)
    if recipient_compartment_keys is not None:
        keys.update(recipient_compartment_keys)

    reconstructed: list[ReconstructedPart] = []
    restricted: list[RestrictedPartProof] = []
    for entry in archive.manifest.entries:
        key = keys.get(entry.compartment_id)
        if entry.access == READABLE and key:
            try:
                payload_bytes = _open_payload(archive.sealed_payloads[entry.part_id], key=key)
                payload_sha256 = _sha256_bytes(payload_bytes)
                if payload_sha256 != entry.payload_commitment_sha256:
                    raise ValueError("Payload commitment mismatch")
                payload = json.loads(payload_bytes.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("Payload is not an object")
            except (KeyError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
                restricted.append(_restricted_from_entry(entry, "Cle presente mais payload illisible."))
            else:
                reconstructed.append(
                    ReconstructedPart(
                        part_id=entry.part_id,
                        kind=entry.kind,
                        public_label=entry.public_label,
                        compartment_id=entry.compartment_id,
                        payload=payload,
                        payload_commitment_sha256=entry.payload_commitment_sha256,
                    )
                )
        else:
            reason = entry.restriction_reason or "Cle de compartiment absente pour ce role."
            restricted.append(_restricted_from_entry(entry, reason))

    return ReconstructionResult(
        archive_id=archive.archive_id,
        vault_id=archive.vault_id,
        recipient_role=archive.recipient_role,
        reconstructed=tuple(reconstructed),
        restricted=tuple(restricted),
        integrity=integrity,
    )


def build_novice_reconstruction_report(result: ReconstructionResult) -> NoviceReconstructionReport:
    helpers: dict[str, RecoveryHelper] = {}
    for proof in result.restricted:
        for helper in proof.recovery_helpers:
            helpers[helper.helper_id] = helper

    can_reconstruct = tuple(
        {
            "part_id": part.part_id,
            "label": part.public_label,
            "type": part.kind,
            "preuve": part.payload_commitment_sha256,
        }
        for part in result.reconstructed
    )
    exists_but_restricted = tuple(
        {
            "part_id": proof.part_id,
            "label": proof.public_label,
            "type": proof.kind,
            "raison": proof.reason,
            "preuve_existence": proof.existence_proof_sha256,
        }
        for proof in result.restricted
    )
    recovery_helpers = tuple(
        helper.as_dict() for helper in sorted(helpers.values(), key=lambda item: item.helper_id)
    )
    summary = (
        f"{len(can_reconstruct)} element(s) reconstructible(s), "
        f"{len(exists_but_restricted)} element(s) present(s) mais restreint(s), "
        f"{len(recovery_helpers)} contact(s) de recuperation."
    )
    return NoviceReconstructionReport(
        archive_id=result.archive_id,
        can_reconstruct=can_reconstruct,
        exists_but_restricted=exists_but_restricted,
        recovery_helpers=recovery_helpers,
        summary=summary,
    )


def _existence_proof(
    *,
    archive_id: str,
    vault_id: str,
    part_id: str,
    sealed_sha256: str,
    payload_commitment_sha256: str,
) -> str:
    return _sha256_text(
        _canonical_json(
            {
                "archive_id": archive_id,
                "vault_id": vault_id,
                "part_id": part_id,
                "sealed_sha256": sealed_sha256,
                "payload_commitment_sha256": payload_commitment_sha256,
            }
        )
    )


def _restricted_from_entry(entry: ArchiveEntry, reason: str) -> RestrictedPartProof:
    return RestrictedPartProof(
        part_id=entry.part_id,
        kind=entry.kind,
        public_label=entry.public_label,
        compartment_id=entry.compartment_id,
        reason=reason,
        existence_proof_sha256=entry.existence_proof_sha256,
        sealed_sha256=entry.sealed_sha256,
        recovery_helpers=entry.recovery_helpers,
    )
