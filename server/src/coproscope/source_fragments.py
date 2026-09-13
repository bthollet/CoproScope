from __future__ import annotations

import linecache
from pathlib import Path
from typing import Any

#: Suffixe des fichiers de source executes par `exec_source_fragments`.
#:
#: Il est expose parce qu'il ne concerne pas que le chargeur: tout outil qui
#: pretend balayer "le code d'un paquet" doit balayer ces fichiers aussi, sans
#: quoi il rend un verdict sur une partie du code en laissant croire qu'il l'a
#: vu en entier. Mesure du 2026-09-09 sur `web/`: 2956 lignes executees vivent
#: dans ces fragments, invisibles a un `rglob("*.py")`.
FRAGMENT_SUFFIX = ".pyfrag"


def fragment_sources(package_dir: Path) -> list[tuple[str, str]]:
    """Les sources de fragments de `package_dir`, telles qu'elles s'executent.

    Un fragment n'est PAS parsable seul: le decoupage tombe au milieu des
    expressions - `_app_fragments/part_001.pyfrag` se termine sur une accolade
    ouverte. L'unite de compilation est le repertoire, concatene dans l'ordre,
    exactement comme le fait `exec_source_fragments`. Un outil qui parserait
    fichier par fichier leverait `SyntaxError` et pourrait conclure a tort que
    ce code est illisible.
    """
    sources: list[tuple[str, str]] = []
    for directory in sorted({p.parent for p in package_dir.rglob("*" + FRAGMENT_SUFFIX)}):
        parts = sorted(directory.glob("*" + FRAGMENT_SUFFIX))
        source = "".join(part.read_text(encoding="utf-8") for part in parts)
        sources.append((f"{directory.relative_to(package_dir)}#fragments", source))
    return sources


def exec_source_fragments(module_globals: dict[str, Any], module_file: str, fragments_dir_name: str) -> None:
    module_path = Path(module_file)
    fragments_dir = module_path.with_name(fragments_dir_name)
    parts = sorted(fragments_dir.glob("*" + FRAGMENT_SUFFIX))
    if not parts:
        raise ImportError(f"No source fragments found in {fragments_dir}")

    source = "".join(part.read_text(encoding="utf-8") for part in parts)
    virtual_filename = f"{module_path}#fragments"
    linecache.cache[virtual_filename] = (
        len(source),
        None,
        source.splitlines(keepends=True),
        virtual_filename,
    )
    exec(compile(source, virtual_filename, "exec"), module_globals, module_globals)
