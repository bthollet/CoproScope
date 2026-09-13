from __future__ import annotations

from pathlib import Path as _Path

_PART_DIR = _Path(__file__).with_name("_test_vault_fragments")
_PART_FILES = (
    'part_001.pyfrag',
    'part_002.pyfrag',
)
_source = "".join((_PART_DIR / name).read_text(encoding="utf-8") for name in _PART_FILES)
exec(compile(_source, f"{__file__}#fragments", "exec"), globals(), globals())
del _Path, _PART_DIR, _PART_FILES, _source
