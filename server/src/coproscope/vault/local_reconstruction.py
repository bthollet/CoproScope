from __future__ import annotations

from pathlib import Path as _Path

_PART_DIR = _Path(__file__).with_name('_local_reconstruction_parts')
_PART_FILES = (
    '01_load_and_rebuild.py',
    '02_schema_and_events.py',
)

for _part_file in _PART_FILES:
    _part_path = _PART_DIR / _part_file
    exec(compile(_part_path.read_text(encoding="utf-8"), str(_part_path), "exec"), globals())

del _Path, _PART_DIR, _PART_FILES, _part_file, _part_path
