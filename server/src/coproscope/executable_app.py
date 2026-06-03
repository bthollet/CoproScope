from __future__ import annotations

import argparse
import importlib.util
import os
import secrets
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_YEAR = 2025
DISPLAY_WINDOW = "window"
DISPLAY_BROWSER = "browser"
DISPLAY_NONE = "none"
DISPLAY_MODES = {DISPLAY_WINDOW, DISPLAY_BROWSER, DISPLAY_NONE}
ENV_INSTANCE_ROOT = "COPROSCOPE_INSTANCE_ROOT"
ENV_NO_BROWSER = "COPROSCOPE_NO_BROWSER"
ENV_PORT = "COPROSCOPE_UI_PORT"
ENV_TOKEN = "COPROSCOPE_UI_TOKEN"
ENV_UI_MODE = "COPROSCOPE_UI_MODE"
ENV_OPEN_BROWSER = "COPROSCOPE_OPEN_BROWSER"
ENV_LAUNCHER_LOG = "COPROSCOPE_LAUNCHER_LOG"


@dataclass(frozen=True)
class LauncherConfig:
    instance_root: Path
    year: int
    host: str
    port: int
    token: str
    display_mode: str

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/?token={quote(self.token)}"

    @property
    def health_url(self) -> str:
        return f"http://{self.host}:{self.port}/health"

    @property
    def open_browser(self) -> bool:
        return self.display_mode == DISPLAY_BROWSER

    @property
    def open_window(self) -> bool:
        return self.display_mode == DISPLAY_WINDOW


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _env_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name)
    if raw in (None, ""):
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_display_mode(env: Mapping[str, str]) -> str:
    raw = str(env.get(ENV_UI_MODE) or "").strip().lower()
    if raw in DISPLAY_MODES:
        return raw
    if _truthy(env.get(ENV_NO_BROWSER)):
        return DISPLAY_NONE
    if _truthy(env.get(ENV_OPEN_BROWSER)):
        return DISPLAY_BROWSER
    return DISPLAY_WINDOW


def _launcher_log(message: str) -> None:
    raw_path = str(os.environ.get(ENV_LAUNCHER_LOG) or "").strip()
    if not raw_path:
        return
    try:
        log_path = Path(raw_path).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{message}\n")
    except OSError:
        return


def _ensure_standard_streams() -> None:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115


def _runtime_roots(cwd: Path, bundle_root: Path | None = None) -> list[Path]:
    roots = [cwd]
    if bundle_root is not None:
        roots.append(bundle_root)
    if hasattr(sys, "_MEIPASS"):
        roots.append(Path(getattr(sys, "_MEIPASS")))
    try:
        roots.append(Path(__file__).resolve().parents[3])
    except IndexError:
        pass
    roots.append(Path(sys.executable).resolve().parent)
    deduped: list[Path] = []
    for root in roots:
        if root not in deduped:
            deduped.append(root)
    return deduped


def discover_default_instance_root(
    env: Mapping[str, str] | None = None,
    *,
    cwd: Path | None = None,
    bundle_root: Path | None = None,
) -> Path:
    env = os.environ if env is None else env
    explicit = str(env.get(ENV_INSTANCE_ROOT) or "").strip()
    if explicit:
        return Path(explicit).expanduser()

    current = cwd or Path.cwd()
    for root in _runtime_roots(current, bundle_root=bundle_root):
        candidate = root / "examples" / "synthetic_copro"
        if (candidate / "instance.yml").exists():
            return candidate
    return current / "examples" / "synthetic_copro"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="CoproScope",
        description="Lanceur local CoproScope pour executable Windows.",
    )
    parser.add_argument("--instance-root", help="Dossier d'instance a ouvrir.")
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR, help="Exercice affiche.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Adresse locale d'ecoute.")
    parser.add_argument("--port", type=int, help="Port local. Defaut: 8765.")
    parser.add_argument("--token", help="Jeton local de session. Genere si absent.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--window", action="store_const", const=DISPLAY_WINDOW, dest="display_mode", help="Ouvrir une fenetre CoproScope.")
    mode.add_argument("--browser", action="store_const", const=DISPLAY_BROWSER, dest="display_mode", help="Ouvrir dans le navigateur par defaut.")
    mode.add_argument("--no-browser", action="store_const", const=DISPLAY_NONE, dest="display_mode", help="Ne pas ouvrir d'interface.")
    return parser


def config_from_args(
    argv: Sequence[str],
    env: Mapping[str, str] | None = None,
    *,
    cwd: Path | None = None,
    bundle_root: Path | None = None,
) -> LauncherConfig:
    env = os.environ if env is None else env
    args = build_parser().parse_args(list(argv))
    instance_root = Path(args.instance_root).expanduser() if args.instance_root else discover_default_instance_root(env, cwd=cwd, bundle_root=bundle_root)
    port = args.port if args.port is not None else _env_int(env, ENV_PORT, DEFAULT_PORT)
    token = args.token or env.get(ENV_TOKEN) or secrets.token_urlsafe(24)
    display_mode = args.display_mode or _env_display_mode(env)
    return LauncherConfig(
        instance_root=instance_root,
        year=args.year,
        host=args.host,
        port=port,
        token=token,
        display_mode=display_mode,
    )


def _open_browser_later(url: str, opener: Callable[[str], object]) -> None:
    timer = threading.Timer(1.0, lambda: opener(url))
    timer.daemon = True
    timer.start()


def _pywebview_available() -> bool:
    return importlib.util.find_spec("webview") is not None


def _open_pywebview_window(title: str, url: str) -> None:
    import webview  # type: ignore

    webview.create_window(title, url, width=1280, height=820, min_size=(980, 640))
    webview.start()


def _wait_for_server(config: LauncherConfig, timeout_seconds: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urlopen(config.health_url, timeout=1.0) as response:  # noqa: S310 - loopback health check
                if response.status == 200:
                    return True
        except (OSError, URLError):
            time.sleep(0.2)
    return False


def _serve_kwargs(config: LauncherConfig) -> dict[str, object]:
    return {
        "host": config.host,
        "port": config.port,
        "access_token": config.token,
        "unsafe_lan": False,
    }


def _serve_blocking(config: LauncherConfig, instance: object, serve_func: Callable[..., object]) -> None:
    serve_func(instance, config.year, **_serve_kwargs(config))


def _serve_in_background(
    config: LauncherConfig,
    instance: object,
    serve_func: Callable[..., object],
) -> threading.Thread:
    def target() -> None:
        try:
            _serve_blocking(config, instance, serve_func)
        except Exception as exc:  # pragma: no cover - defensive runtime logging
            _launcher_log(f"server failed: {exc!r}")
            raise

    thread = threading.Thread(target=target, name="CoproScope UI server", daemon=True)
    thread.start()
    return thread


def _run_cli_with_args(cli_args: Sequence[str]) -> int:
    from .cli import main as cli_main

    previous_argv = sys.argv[:]
    try:
        sys.argv = [previous_argv[0], *cli_args]
        return int(cli_main())
    finally:
        sys.argv = previous_argv


def run_launcher(
    config: LauncherConfig,
    *,
    load_instance_func: Callable[[str | None, str | None], object] | None = None,
    serve_func: Callable[..., object] | None = None,
    open_browser_func: Callable[[str], object] | None = None,
    open_window_func: Callable[[str, str], object] | None = None,
    wait_for_server_func: Callable[[LauncherConfig], bool] | None = None,
) -> int:
    _ensure_standard_streams()
    _launcher_log(f"instance_root={config.instance_root}")
    if not (config.instance_root / "instance.yml").exists():
        _launcher_log("missing instance.yml")
        print("CoproScope ne trouve pas l'instance locale a ouvrir.")
        print("Indiquez un dossier avec --instance-root ou COPROSCOPE_INSTANCE_ROOT.")
        return 2

    if load_instance_func is None:
        _launcher_log("importing load_instance")
        from .core.common import load_instance as load_instance_func
        _launcher_log("imported load_instance")
    if serve_func is None:
        _launcher_log("importing serve")
        from .web.app import serve as serve_func
        _launcher_log("imported serve")

    _launcher_log("loading instance")
    instance = load_instance_func(None, str(config.instance_root))
    _launcher_log(f"serving {config.host}:{config.port}")
    print("CoproScope demarre en local sur cet ordinateur.")
    print(f"Adresse locale: {config.url}")
    display_mode = config.display_mode
    if display_mode == DISPLAY_WINDOW and open_window_func is None and not _pywebview_available():
        _launcher_log("pywebview missing, falling back to browser mode")
        display_mode = DISPLAY_BROWSER

    if display_mode == DISPLAY_WINDOW:
        _launcher_log("starting background server for desktop window")
        server_thread = _serve_in_background(config, instance, serve_func)
        wait_for_server = wait_for_server_func or _wait_for_server
        if not wait_for_server(config):
            _launcher_log("server did not become ready for desktop window")
            return 3
        _launcher_log("opening desktop window")
        (open_window_func or _open_pywebview_window)("CoproScope", config.url)
        _launcher_log(f"window closed; server_thread_alive={server_thread.is_alive()}")
        return 0

    if display_mode == DISPLAY_BROWSER:
        _open_browser_later(config.url, open_browser_func or webbrowser.open)
    _serve_blocking(config, instance, serve_func)
    _launcher_log("serve returned")
    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    runner: Callable[[Sequence[str]], int] | None = None,
) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["cli"]:
        return (runner or _run_cli_with_args)(args[1:])
    config = config_from_args(args)
    return run_launcher(config)


if __name__ == "__main__":
    raise SystemExit(main())
