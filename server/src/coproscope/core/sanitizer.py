from __future__ import annotations

import posixpath
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET


CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


DROP_PART_EXACT = {
    "word/comments.xml",
    "word/commentsExtended.xml",
    "word/commentsIds.xml",
    "word/people.xml",
    "word/vbaProject.bin",
}

DROP_PART_PREFIXES = (
    "docProps/",
    "customXml/",
    "word/embeddings/",
    "word/activeX/",
)

DROP_REL_TYPES = {
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/commentsExtended",
    "http://schemas.microsoft.com/office/2011/relationships/commentsExtended",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/people",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/package",
    "http://schemas.microsoft.com/office/2006/relationships/activeXControl",
    "http://schemas.microsoft.com/office/2006/relationships/vbaProject",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate",
    "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties",
}

REMOVE_TAGS = {
    f"{{{W_NS}}}del",
    f"{{{W_NS}}}moveFrom",
    f"{{{W_NS}}}delText",
    f"{{{W_NS}}}commentRangeStart",
    f"{{{W_NS}}}commentRangeEnd",
    f"{{{W_NS}}}commentReference",
    f"{{{W_NS}}}proofErr",
    f"{{{W_NS}}}permStart",
    f"{{{W_NS}}}permEnd",
    f"{{{W_NS}}}bookmarkStart",
    f"{{{W_NS}}}bookmarkEnd",
    f"{{{W_NS}}}fldChar",
    f"{{{W_NS}}}instrText",
}

UNWRAP_TAGS = {
    f"{{{W_NS}}}ins",
    f"{{{W_NS}}}moveTo",
    f"{{{W_NS}}}fldSimple",
    f"{{{W_NS}}}smartTag",
}

TEXT_TAGS = {
    f"{{{W_NS}}}t",
    f"{{{A_NS}}}t",
}

PACKAGE_TEXT_PART_PREFIXES = ("word/", "docProps/", "customXml/")


def replace_values(text: str, replacements: dict[str, str]) -> str:
    redacted = text
    for original, replacement in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        if original:
            redacted = redacted.replace(original, replacement)
    return redacted


def extract_docx_package_text(path: Path, max_chars: int | None = None) -> str:
    parts: list[str] = []
    with zipfile.ZipFile(path) as package:
        for name in package.namelist():
            normalized = _normalize_part_name(name)
            if not normalized.endswith(".xml"):
                continue
            if not normalized.startswith(PACKAGE_TEXT_PART_PREFIXES):
                continue
            try:
                root = ET.fromstring(package.read(name))
            except ET.ParseError:
                continue
            parts.extend(_extract_xml_text_values(root))
            if max_chars is not None and sum(len(part) for part in parts) >= max_chars:
                return "\n".join(parts)[:max_chars]
    text = "\n".join(parts)
    return text[:max_chars] if max_chars is not None else text


def sanitize_docx_package(path: Path, replacements: dict[str, str] | None = None) -> dict[str, object]:
    replacements = replacements or {}
    temp_path = path.with_name(path.name + ".sanitize.tmp")
    dropped_parts: list[str] = []
    removed_relationships = 0

    with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            name = _normalize_part_name(info.filename)
            if _should_drop_part(name):
                dropped_parts.append(name)
                continue

            data = source.read(info)
            if name.endswith(".rels"):
                data, removed = _sanitize_relationships(name, data)
                removed_relationships += removed
            elif name == "[Content_Types].xml":
                data = _sanitize_content_types(data)
            elif name.endswith(".xml"):
                data = _sanitize_xml_part(data, replacements)

            output_info = zipfile.ZipInfo(filename=name, date_time=info.date_time)
            output_info.compress_type = zipfile.ZIP_DEFLATED
            output_info.external_attr = info.external_attr
            target.writestr(output_info, data)

    temp_path.replace(path)
    return {
        "status": "ok",
        "path": str(path),
        "dropped_parts": dropped_parts,
        "removed_relationships": removed_relationships,
    }


def _normalize_part_name(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def _should_drop_part(name: str) -> bool:
    normalized = _normalize_part_name(name)
    return normalized in DROP_PART_EXACT or any(normalized.startswith(prefix) for prefix in DROP_PART_PREFIXES)


def _sanitize_content_types(data: bytes) -> bytes:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return data
    for child in list(root):
        part_name = _normalize_part_name(child.attrib.get("PartName", ""))
        extension = child.attrib.get("Extension", "").lower()
        if _should_drop_part(part_name) or extension in {"bin", "vba", "ole"}:
            root.remove(child)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _sanitize_relationships(name: str, data: bytes) -> tuple[bytes, int]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return data, 0
    removed = 0
    for rel in list(root):
        rel_type = rel.attrib.get("Type", "")
        target = rel.attrib.get("Target", "")
        target_mode = rel.attrib.get("TargetMode", "")
        resolved_target = _resolve_relationship_target(name, target)
        if target_mode.lower() == "external" or rel_type in DROP_REL_TYPES or _should_drop_part(resolved_target):
            root.remove(rel)
            removed += 1
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), removed


def _resolve_relationship_target(rels_name: str, target: str) -> str:
    if not target:
        return ""
    lowered = target.lower()
    if "://" in lowered or lowered.startswith("mailto:"):
        return target
    if target.startswith("/"):
        return _normalize_part_name(target)
    base = ""
    if rels_name != "_rels/.rels" and "/_rels/" in rels_name:
        base = rels_name.split("/_rels/", 1)[0]
    return _normalize_part_name(posixpath.normpath(posixpath.join(base, target)))


def _sanitize_xml_part(data: bytes, replacements: dict[str, str]) -> bytes:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        text = data.decode("utf-8", errors="ignore")
        return replace_values(text, replacements).encode("utf-8")

    _clean_tree(root)
    _sanitize_attributes(root, replacements)
    _replace_text_across_paragraphs(root, replacements)
    _replace_remaining_text_nodes(root, replacements)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _extract_xml_text_values(root: ET.Element) -> list[str]:
    values: list[str] = []
    consumed: set[int] = set()
    for paragraph in root.iter(f"{{{W_NS}}}p"):
        nodes = [node for node in paragraph.iter() if node.tag in TEXT_TAGS and node.text]
        if nodes:
            values.append("".join(node.text or "" for node in nodes).strip())
            consumed.update(id(node) for node in nodes)
    for element in root.iter():
        if element.tag in TEXT_TAGS and id(element) not in consumed and element.text and element.text.strip():
            values.append(element.text.strip())
        for attr_value in element.attrib.values():
            if attr_value and attr_value.strip():
                values.append(attr_value.strip())
    return [value for value in values if value]


def _clean_tree(element: ET.Element) -> None:
    for child in list(element):
        _clean_tree(child)
        if child.tag in REMOVE_TAGS or _is_hidden_run(child):
            element.remove(child)
            continue
        if child.tag in UNWRAP_TAGS:
            index = list(element).index(child)
            element.remove(child)
            for grandchild in reversed(list(child)):
                element.insert(index, grandchild)


def _is_hidden_run(element: ET.Element) -> bool:
    if element.tag != f"{{{W_NS}}}r":
        return False
    properties = element.find(f"{{{W_NS}}}rPr")
    return properties is not None and properties.find(f"{{{W_NS}}}vanish") is not None


def _sanitize_attributes(root: ET.Element, replacements: dict[str, str]) -> None:
    for element in root.iter():
        for attr_name, attr_value in list(element.attrib.items()):
            if attr_name.startswith(f"{{{W_NS}}}rsid"):
                del element.attrib[attr_name]
            else:
                element.attrib[attr_name] = replace_values(attr_value, replacements)


def _replace_text_across_paragraphs(root: ET.Element, replacements: dict[str, str]) -> None:
    for paragraph in root.iter(f"{{{W_NS}}}p"):
        nodes = [node for node in paragraph.iter() if node.tag in TEXT_TAGS and node.text]
        if not nodes:
            continue
        original = "".join(node.text or "" for node in nodes)
        redacted = replace_values(original, replacements)
        if redacted == original:
            continue
        nodes[0].text = redacted
        for node in nodes[1:]:
            node.text = ""


def _replace_remaining_text_nodes(root: ET.Element, replacements: dict[str, str]) -> None:
    for element in root.iter():
        if element.text:
            element.text = replace_values(element.text, replacements)
        if element.tail:
            element.tail = replace_values(element.tail, replacements)
