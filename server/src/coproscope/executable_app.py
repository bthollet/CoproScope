from __future__ import annotations

import argparse
import importlib.util
import json
import os
import secrets
import socket
import subprocess
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
ENV_DESKTOP_CONFIG = "COPROSCOPE_DESKTOP_CONFIG"
DESKTOP_CONFIG_FILENAME = "desktop.json"
ENV_RECETTE_MODE = "COPROSCOPE_RECETTE_MODE"


@dataclass(frozen=True)
class LauncherConfig:
    instance_root: Path
    year: int
    host: str
    port: int
    token: str
    display_mode: str
    recette_mode: bool

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


def _is_valid_instance_root(path: Path) -> bool:
    return path.is_dir() and (path / "instance.yml").is_file()


def _desktop_config_path(env: Mapping[str, str]) -> Path | None:
    explicit = str(env.get(ENV_DESKTOP_CONFIG) or "").strip()
    if explicit:
        return Path(explicit).expanduser()
    app_root = str(env.get("APPDATA") or env.get("LOCALAPPDATA") or "").strip()
    if app_root:
        return Path(app_root).expanduser() / "CoproScope" / DESKTOP_CONFIG_FILENAME
    profile_root = str(env.get("USERPROFILE") or "").strip()
    if profile_root:
        return Path(profile_root).expanduser() / ".coproscope" / DESKTOP_CONFIG_FILENAME
    return None


def _read_last_instance_root(env: Mapping[str, str]) -> Path | None:
    config_path = _desktop_config_path(env)
    if config_path is None or not config_path.exists():
        return None
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    raw_path = str(data.get("last_instance_root") or "").strip()
    if not raw_path:
        return None
    instance_root = Path(raw_path).expanduser()
    return instance_root if _is_valid_instance_root(instance_root) else None


def _write_last_instance_root(instance_root: Path, env: Mapping[str, str]) -> None:
    config_path = _desktop_config_path(env)
    if config_path is None:
        return
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"last_instance_root": str(instance_root)}
        config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        _launcher_log(f"desktop config save failed: {exc!r}")


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

    saved_instance_root = _read_last_instance_root(env)
    if saved_instance_root is not None:
        return saved_instance_root

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
    parser.add_argument("--recette", action="store_true", help="Activer le mode local de remarques de test.")
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
        recette_mode=bool(args.recette or _truthy(env.get(ENV_RECETTE_MODE))),
    )


def _open_browser_later(url: str, opener: Callable[[str], object]) -> None:
    timer = threading.Timer(1.0, lambda: opener(url))
    timer.daemon = True
    timer.start()


def _pywebview_available() -> bool:
    return importlib.util.find_spec("webview") is not None


def _new_free_loopback_port() -> int:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind((DEFAULT_HOST, 0))
    try:
        return int(listener.getsockname()[1])
    finally:
        listener.close()


def _runtime_launcher_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, "-m", "coproscope.executable_app"]


def _build_switch_command(
    config: LauncherConfig,
    instance_root: Path,
    *,
    port: int | None = None,
    token: str | None = None,
) -> list[str]:
    command = [
        *_runtime_launcher_command(),
        "--instance-root",
        str(instance_root),
        "--year",
        str(config.year),
        "--host",
        config.host,
        "--port",
        str(port or _new_free_loopback_port()),
        "--token",
        token or secrets.token_urlsafe(24),
        "--window",
    ]
    if config.recette_mode:
        command.append("--recette")
    return command


def _spawn_desktop_process(command: Sequence[str]) -> None:
    subprocess.Popen(list(command), close_fds=True)  # noqa: S603 - local relaunch command


def _schedule_instance_restart(
    config: LauncherConfig,
    instance_root: Path,
    *,
    env: Mapping[str, str] | None = None,
    delay_seconds: float = 0.35,
    spawn_func: Callable[[Sequence[str]], object] = _spawn_desktop_process,
    exit_func: Callable[[int], object] = os._exit,
) -> None:
    command = _build_switch_command(config, instance_root)

    def target() -> None:
        time.sleep(delay_seconds)
        try:
            spawn_func(command)
            _launcher_log(f"restarted desktop instance_root={instance_root}")
        except OSError as exc:
            _launcher_log(f"desktop restart failed: {exc!r}")
            return
        exit_func(0)

    _write_last_instance_root(instance_root, os.environ if env is None else env)
    thread = threading.Thread(target=target, name="CoproScope instance switch", daemon=True)
    thread.start()


def _selected_folder_path(selected: object) -> Path | None:
    if not selected:
        return None
    if isinstance(selected, (str, os.PathLike)):
        return Path(selected).expanduser()
    if isinstance(selected, Sequence) and selected:
        return Path(str(selected[0])).expanduser()
    return None


class DesktopSwitchApi:
    def __init__(
        self,
        config: LauncherConfig,
        *,
        env: Mapping[str, str] | None = None,
        folder_selector: Callable[[], object] | None = None,
        restart_func: Callable[[Path], object] | None = None,
    ) -> None:
        self._config = config
        self._env = os.environ if env is None else env
        self._folder_selector = folder_selector
        self._restart_func = restart_func

    def choose_instance_root(self) -> dict[str, object]:
        selected = (self._folder_selector or self._select_folder)()
        selected_path = _selected_folder_path(selected)
        if selected_path is None:
            return {"ok": False, "status": "cancelled", "message": "Aucun dossier choisi."}
        return self._switch_to_instance_root(selected_path)

    def _select_folder(self) -> object:
        import webview  # type: ignore

        windows = getattr(webview, "windows", [])
        if not windows:
            return None
        file_dialog = getattr(webview, "FileDialog", None)
        dialog_kind = file_dialog.FOLDER if file_dialog is not None else webview.FOLDER_DIALOG
        start_dir = str(self._config.instance_root.parent)
        return windows[0].create_file_dialog(dialog_kind, directory=start_dir)

    def _switch_to_instance_root(self, instance_root: Path) -> dict[str, object]:
        resolved_root = instance_root.expanduser()
        if not _is_valid_instance_root(resolved_root):
            return {
                "ok": False,
                "status": "invalid",
                "message": "Ce dossier n'est pas un coffre CoproScope: instance.yml manque.",
            }

        _write_last_instance_root(resolved_root, self._env)
        if self._restart_func is None:
            _schedule_instance_restart(self._config, resolved_root, env=self._env)
        else:
            self._restart_func(resolved_root)
        return {
            "ok": True,
            "status": "restarting",
            "message": "CoproScope ouvre ce coffre dans une nouvelle fenetre.",
        }


DESKTOP_SWITCHER_SCRIPT = r"""
(() => {
  if (window.__coproscopeDesktopSwitcher || !window.pywebview) return;
  window.__coproscopeDesktopSwitcher = true;
  const style = document.createElement('style');
  style.textContent = `
    .cs-desktop-switcher {
      position: fixed;
      left: 14px;
      bottom: 14px;
      z-index: 2147483000;
      display: flex;
      gap: 8px;
      align-items: center;
      font: 13px/1.3 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .cs-desktop-switcher button {
      border: 1px solid #1f2937;
      border-radius: 6px;
      background: #111827;
      color: #fff;
      padding: 9px 12px;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
      cursor: pointer;
    }
    .cs-desktop-switcher button:disabled {
      cursor: wait;
      opacity: 0.72;
    }
    .cs-desktop-switcher__status {
      max-width: 280px;
      border-radius: 6px;
      background: #fff;
      color: #111827;
      padding: 8px 10px;
      box-shadow: 0 8px 22px rgba(15, 23, 42, 0.14);
    }
  `;
  document.head.appendChild(style);
  const root = document.createElement('div');
  root.className = 'cs-desktop-switcher';
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = 'Changer de coffre';
  button.title = 'Choisir un autre dossier de coffre local';
  const status = document.createElement('div');
  status.className = 'cs-desktop-switcher__status';
  status.hidden = true;
  root.append(button, status);
  document.body.appendChild(root);
  const showStatus = (message) => {
    status.textContent = message || '';
    status.hidden = !message;
  };
  button.addEventListener('click', async () => {
    button.disabled = true;
    showStatus('Choisissez un dossier...');
    try {
      const result = await window.pywebview.api.choose_instance_root();
      showStatus(result && result.message ? result.message : '');
      if (!result || !result.ok) button.disabled = false;
    } catch (error) {
      showStatus('Selection impossible depuis cette fenetre.');
      button.disabled = false;
    }
  });
})();
"""


def _open_pywebview_window(title: str, url: str, config: LauncherConfig) -> None:
    import webview  # type: ignore

    api = DesktopSwitchApi(config)
    window = webview.create_window(title, url, width=1280, height=820, min_size=(980, 640), js_api=api)
    window.events.loaded += lambda: window.evaluate_js(DESKTOP_SWITCHER_SCRIPT)
    _launcher_log("desktop switcher enabled")
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
        "recette_mode": config.recette_mode,
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
        if open_window_func is None:
            _open_pywebview_window("CoproScope", config.url, config)
        else:
            open_window_func("CoproScope", config.url)
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
