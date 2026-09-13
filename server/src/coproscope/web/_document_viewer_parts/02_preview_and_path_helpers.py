from __future__ import annotations



def _text_preview(path: Path, source_label: str, *, fallback: bool) -> dict[str, object] | None:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
    except OSError:
        return None
    truncated = len(text) > MAX_TEXT_CHARS
    return {
        "kind": "text",
        "kind_label": "texte",
        "source_label": source_label,
        "message": "Apercu media indisponible; affichage du texte extrait." if fallback else "",
        "text": text[:MAX_TEXT_CHARS],
        "truncated": truncated,
        "fallback": fallback,
    }


def _binary_preview(path: Path, kind: str, source_label: str) -> dict[str, object] | None:
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > MAX_INLINE_BYTES:
        return None

    media_type = mimetypes.guess_type(path.name)[0]
    if not media_type:
        media_type = "application/pdf" if kind == "pdf" else "application/octet-stream"
    try:
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError:
        return None
    return {
        "kind": kind,
        "kind_label": "PDF" if kind == "pdf" else "image",
        "source_label": source_label,
        "message": "",
        "data_uri": f"data:{media_type};base64,{payload}",
        "media_type": media_type,
        "truncated": False,
        "fallback": False,
    }


def _safe_existing_path(instance: InstanceConfig, value: str) -> Path | None:
    path = _resolve_under_workspace(instance, value)
    if path is None or not path.is_file():
        return None
    if _is_blocked_direct_path(instance, path):
        return None
    return path


def _resolve_under_workspace(instance: InstanceConfig, value: str) -> Path | None:
    cleaned = (value or "").strip().replace("\\", "/")
    if not cleaned or "\x00" in cleaned:
        return None

    workspace = _workspace_root(instance)
    candidate = Path(cleaned)
    resolved = candidate.resolve() if candidate.is_absolute() else (workspace / candidate).resolve()
    if not _is_relative_to(resolved, workspace):
        return None
    return resolved


def _is_blocked_direct_path(instance: InstanceConfig, path: Path) -> bool:
    workspace = _workspace_root(instance)
    try:
        relative_parts = [part.lower() for part in path.relative_to(workspace).parts]
    except ValueError:
        return True
    if any(part in BLOCKED_PATH_PARTS for part in relative_parts):
        return True
    for root in _restricted_roots(instance):
        if _is_relative_to(path, root):
            return True
    return False


def _storage_summary(instance: InstanceConfig, row: dict[str, str]) -> dict[str, str]:
    original = _resolve_under_workspace(instance, row.get("original_path", ""))
    if original is None:
        status = "source non resolue"
    elif _is_blocked_direct_path(instance, original):
        status = "source locale masquee"
    else:
        status = "source locale hors zone brute"
    return {
        "status": status,
        "note": "La fiche expose seulement des metadonnees et des apercus derives; aucun chemin local n'est publie.",
    }


def _workspace_root(instance: InstanceConfig) -> Path:
    try:
        return instance.root("workspace").resolve()
    except KeyError:
        return instance.instance_root.resolve()


def _restricted_roots(instance: InstanceConfig) -> list[Path]:
    try:
        return [path.resolve() for path in instance.root_list("restricted")]
    except KeyError:
        return []


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _format_size(value: str) -> str:
    try:
        size = int(value)
    except (TypeError, ValueError):
        return "n/a"
    if size < 1024:
        return f"{size} o"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} Ko"
    return f"{size / (1024 * 1024):.1f} Mo"


def _format_chars(value: str) -> str:
    try:
        count = int(value)
    except (TypeError, ValueError):
        return "n/a"
    return f"{count} caracteres"


def page_d_ouverture(demandee: str, page_count: int) -> tuple[str, str]:
    """A quelle page ouvrir le lecteur, et ce qu'il faut dire de la demande.

    Instruction de `RM-2026-0157`: une cellule de controle qui cite `page 18`
    doit pouvoir y mener. Le lecteur ouvrait toujours page 1, quelle que soit
    l'adresse suivie.

    **Une demande hors bornes ne se rabat pas en silence.** Un lot d'extraction
    peut ecrire une page qui n'existe pas dans le document - le registre porte
    `page_count` et le magasin de liens porte `page`, ils sont ecrits par deux
    chemins differents et rien ne les recoupe. Ouvrir page 1 sans rien dire
    ferait croire au lecteur qu'il regarde la page citee. On ouvre page 1 ET on
    nomme l'ecart, avec les deux nombres.

    `page_count` vaut 0 quand le nombre de pages n'a pas ete lu: on honore
    alors la demande sans pouvoir la verifier, et on le declare. Refuser
    reviendrait a punir le lecteur d'une lacune du registre.
    """
    brut = str(demandee or "").strip()
    if not brut:
        return "1", ""
    try:
        numero = int(brut)
    except (TypeError, ValueError):
        return "1", (
            f"La page demandée ({brut}) n'est pas un numéro : le lecteur ouvre page 1."
        )
    if numero < 1:
        return "1", (
            f"La page demandée ({numero}) n'existe pas : le lecteur ouvre page 1."
        )
    if page_count > 0 and numero > page_count:
        combien = "la page unique" if page_count == 1 else f"les {page_count} pages"
        return "1", (
            f"La page demandée ({numero}) dépasse {combien} de ce document : le lecteur "
            "ouvre page 1, et l'écart entre la citation et la pièce reste à trancher."
        )
    if page_count <= 0:
        return str(numero), (
            f"Le lecteur ouvre page {numero} comme demandé, sans pouvoir le vérifier : "
            "le nombre total de pages de ce document n'a pas été lu."
        )
    return str(numero), ""
