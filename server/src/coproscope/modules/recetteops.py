from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import secrets
from pathlib import Path
from typing import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit

from ..core.common import InstanceConfig, append_csv_row, now_iso


REGISTER_FILENAME = "registre_recette_annotations.csv"
WATERMARK = "DERIVED_RECETTE_QA"
FIELDS = [
    "annotation_id",
    "created_at",
    "route",
    "query",
    "viewport_width",
    "viewport_height",
    "scroll_x",
    "scroll_y",
    "target_kind",
    "target_label",
    "target_role",
    "target_selector",
    "target_text",
    "box_x",
    "box_y",
    "box_width",
    "box_height",
    "severity",
    "comment",
    "status",
    "source",
]
EXPORT_FIELDS = ["source_of_truth", "dataset_kind", "watermark", *FIELDS]
SEVERITIES = {"bloquant", "important", "detail"}
KINDS = {"object", "zone"}
TOKEN_KEYS = {"token", "access_token", "x-coproscope-token"}
PRIVATE_MARKERS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"\\\\"),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?:^|[\\/\s])(?:raw|restricted|logs|private|system|staging)(?:[\\/\s]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])(?:Users|home)(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:token|access_token)=", re.IGNORECASE),
)
MEMORY_ROWS: dict[str, list[dict[str, str]]] = {}


def save_annotation(instance: InstanceConfig, payload: Mapping[str, object]) -> dict[str, str]:
    row = validated_annotation(payload)
    path = register_path(instance)
    if path is None:
        memory_rows(instance).append(row)
        return {**row, "storage": "memory"}
    append_csv_row(path, FIELDS, row)
    return {**row, "storage": "csv", "storage_name": REGISTER_FILENAME}


def list_annotations(instance: InstanceConfig) -> list[dict[str, str]]:
    path = register_path(instance)
    if path is None or not path.exists():
        return [dict(row) for row in memory_rows(instance)]
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def render_json_export(instance: InstanceConfig) -> str:
    payload = {
        "export_type": "recette_annotations",
        "source_of_truth": False,
        "watermark": WATERMARK,
        "dataset_kind": "derived_recette_register",
        "rows": [export_row(row) for row in list_annotations(instance)],
    }
    return json.dumps(payload, ensure_ascii=True, indent=2) + "\n"


def render_markdown_export(instance: InstanceConfig) -> str:
    rows = [export_row(row) for row in list_annotations(instance)]
    lines = [
        "# Recette CoproScope - annotations",
        "",
        f"Watermark: `{WATERMARK}`",
        "",
        "Ce fichier est une aide de test. Il ne remplace pas les registres metier.",
        "",
    ]
    if not rows:
        return "\n".join([*lines, "Aucune annotation enregistree.", ""])
    for index, row in enumerate(rows, start=1):
        title = row.get("target_label") or row.get("route") or "Annotation"
        lines.extend(
            [
                f"## {index}. {title}",
                "",
                f"- Gravite: {row.get('severity', 'detail')}",
                f"- Ecran: `{row.get('route', '')}`",
                f"- Cible: {row.get('target_kind', '')} - {row.get('target_selector', '')}",
                f"- Zone: x={row.get('box_x', '')}, y={row.get('box_y', '')}, w={row.get('box_width', '')}, h={row.get('box_height', '')}",
                f"- Note: {row.get('comment', '')}",
                "",
            ]
        )
    return "\n".join(lines)


def render_csv_export(instance: InstanceConfig) -> str:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=EXPORT_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in list_annotations(instance):
        writer.writerow(export_row(row))
    return stream.getvalue()


def validated_annotation(payload: Mapping[str, object]) -> dict[str, str]:
    route, query = route_and_query(payload.get("url") or payload.get("route"))
    severity = clean_choice(payload.get("severity"), SEVERITIES, "detail")
    kind = clean_choice(payload.get("target_kind"), KINDS, "object")
    return {
        "annotation_id": f"REC-{secrets.token_hex(4).upper()}",
        "created_at": now_iso(),
        "route": route,
        "query": query,
        "viewport_width": clean_number(payload.get("viewport_width")),
        "viewport_height": clean_number(payload.get("viewport_height")),
        "scroll_x": clean_number(payload.get("scroll_x")),
        "scroll_y": clean_number(payload.get("scroll_y")),
        "target_kind": kind,
        "target_label": clean_text(payload.get("target_label"), 120),
        "target_role": clean_text(payload.get("target_role"), 40),
        "target_selector": clean_text(payload.get("target_selector"), 180),
        "target_text": clean_text(payload.get("target_text"), 180),
        "box_x": clean_number(payload.get("box_x")),
        "box_y": clean_number(payload.get("box_y")),
        "box_width": clean_number(payload.get("box_width")),
        "box_height": clean_number(payload.get("box_height")),
        "severity": severity,
        "comment": clean_text(payload.get("comment"), 500),
        "status": "ouvert",
        "source": "recette_ui",
    }


def route_and_query(value: object) -> tuple[str, str]:
    raw = str(value or "/").strip()
    parts = urlsplit(raw)
    route = "/" if parts.scheme and parts.scheme not in {"http", "https"} else parts.path or "/"
    if contains_private_marker(route):
        route = "/"
    if not route.startswith("/"):
        route = f"/{route}"
    safe_pairs = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=False)
        if key.lower() not in TOKEN_KEYS and not contains_private_marker(key) and not contains_private_marker(val)
    ]
    return clean_text(route, 160) or "/", urlencode(safe_pairs)


def export_row(row: Mapping[str, str]) -> dict[str, str]:
    exported = {field: clean_export_value(row.get(field, "")) for field in FIELDS}
    return {
        "source_of_truth": "false",
        "dataset_kind": "derived_recette_register",
        "watermark": WATERMARK,
        **exported,
    }


def register_path(instance: InstanceConfig) -> Path | None:
    try:
        base = instance.register("documents").parent.resolve()
        root = instance.instance_root.resolve()
    except (KeyError, OSError):
        return None
    target = (base / REGISTER_FILENAME).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


def memory_rows(instance: InstanceConfig) -> list[dict[str, str]]:
    key = memory_key(instance)
    return MEMORY_ROWS.setdefault(key, [])


def memory_key(instance: InstanceConfig) -> str:
    try:
        return hashlib.sha256(str(instance.instance_root.resolve()).encode("utf-8", "surrogatepass")).hexdigest()
    except OSError:
        return str(id(instance))


def clean_choice(value: object, allowed: set[str], fallback: str) -> str:
    text = clean_text(value, 40).lower()
    return text if text in allowed else fallback


def clean_number(value: object) -> str:
    try:
        number = float(str(value or "0").strip())
    except ValueError:
        number = 0.0
    if number < 0 or number > 99999:
        number = 0.0
    return f"{number:.1f}"


def clean_text(value: object, max_length: int) -> str:
    text = " ".join(str(value or "").strip().split())[:max_length]
    if contains_private_marker(text):
        return ""
    return text


def clean_export_value(value: object) -> str:
    return clean_text(value, 500)


def contains_private_marker(value: object) -> bool:
    text = str(value or "")
    return any(pattern.search(text) for pattern in PRIVATE_MARKERS)
