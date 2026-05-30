# -*- mode: python ; coding: utf-8 -*-

import sys
import ast
import importlib.util
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


SPEC_DIR = Path(globals()["SPECPATH"]).resolve()
SERVER_ROOT = SPEC_DIR.parents[1]
REPO_ROOT = SERVER_ROOT.parent
sys.path.insert(0, str(SERVER_ROOT / "src"))

datas, binaries, hiddenimports = collect_all("coproscope")
try:
    webview_datas, webview_binaries, webview_hiddenimports = collect_all("webview")
except Exception:
    webview_datas, webview_binaries, webview_hiddenimports = [], [], []
datas += webview_datas
binaries += webview_binaries
hiddenimports += webview_hiddenimports


def source_declared_imports(source_root):
    imports = set()
    source_texts = [path.read_text(encoding="utf-8") for path in source_root.rglob("*.py")]
    for fragments_dir in sorted(path for path in source_root.rglob("*") if path.is_dir()):
        fragments = sorted(fragments_dir.glob("*.pyfrag"))
        if fragments:
            source_texts.append("".join(fragment.read_text(encoding="utf-8") for fragment in fragments))
    for source_text in source_texts:
        try:
            tree = ast.parse(source_text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module and node.module != "__future__":
                imports.add(node.module)
    return sorted(imports)


def available_imports(imports):
    available = set()
    for name in imports:
        try:
            spec = importlib.util.find_spec(name)
        except (ImportError, ModuleNotFoundError, ValueError):
            spec = None
        if spec is not None:
            available.add(name)
    return available


manual_hiddenimports = {
    "fastapi.responses",
    "fastapi.staticfiles",
    "fastapi.templating",
    "html.parser",
    "webview",
    "webview.platforms.edgechromium",
    "webview.platforms.winforms",
}
hiddenimports = sorted(
    available_imports(
        set(hiddenimports)
        | manual_hiddenimports
        | set(source_declared_imports(SERVER_ROOT / "src" / "coproscope"))
    )
)

synthetic_instance = REPO_ROOT / "examples" / "synthetic_copro"
if synthetic_instance.exists():
    datas.append((str(synthetic_instance), "examples/synthetic_copro"))

a = Analysis(
    [str(SPEC_DIR / "coproscope_launcher.py")],
    pathex=[str(SERVER_ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CoproScope",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CoproScope",
)
