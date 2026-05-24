from __future__ import annotations

from coproscope.source_fragments import exec_source_fragments as _exec_source_fragments
from ._runtime import *


_exec_source_fragments(globals(), __file__, "_comptes_builder_fragments")
del _exec_source_fragments
