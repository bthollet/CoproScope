from __future__ import annotations

import linecache
from pathlib import Path
from typing import Any


def exec_source_fragments(module_globals: dict[str, Any], module_file: str, fragments_dir_name: str) -> None:
    module_path = Path(module_file)
    fragments_dir = module_path.with_name(fragments_dir_name)
    parts = sorted(fragments_dir.glob("*.pyfrag"))
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
