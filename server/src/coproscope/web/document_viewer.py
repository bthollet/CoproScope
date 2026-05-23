from __future__ import annotations

from coproscope.source_fragments import exec_source_fragments as _exec_source_fragments


_exec_source_fragments(globals(), __file__, "_document_viewer_fragments")
del _exec_source_fragments
