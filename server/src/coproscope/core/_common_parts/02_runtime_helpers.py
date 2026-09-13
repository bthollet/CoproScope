from __future__ import annotations



def load_instance(instance: str | None, instance_root: str | None) -> InstanceConfig:
    if instance:
        path = Path(instance)
        if path.is_dir():
            path = path / "instance.yml"
    elif instance_root:
        path = Path(instance_root) / "instance.yml"
    else:
        raise SystemExit("Provide --instance or --instance-root.")

    path = path.resolve()
    if not path.exists():
        raise SystemExit(f"Instance file not found: {path}")
    payload = load_structured_file(path)
    if not isinstance(payload, dict):
        raise SystemExit(f"Invalid instance payload in {path}")
    config = InstanceConfig(path=path, payload=payload)
    _refuser_une_instance_synchronisee(config)
    return config


_DEUX_LIGNES = chr(10) + chr(10)


def _refuser_une_instance_synchronisee(config: InstanceConfig) -> None:
    """Une instance ne s'ouvre pas dans un dossier tenu par un nuage.

    **La garde s'arme ici, au moment ou les racines sont resolues**, et pas au
    moment d'ecrire: un `instance.yml` recopie ailleurs suffirait sinon a la
    contourner. Elle refuse a l'ouverture, avec le dossier et le signal nommes,
    parce qu'une instance a moitie ouverte est pire qu'une instance refusee.

    Ce qu'elle protege: les registres, les sorties et le coffre d'une instance
    sont ecrits par CoproScope. Dans un dossier synchronise ils partent chez un
    tiers, sont modifies par une machine que nous ne pilotons pas, et
    reviennent dans un etat que nous n'avons pas ecrit - sans qu'aucune erreur
    ne soit levee.
    """
    # Import absolu et tardif: ce fichier est un FRAGMENT, execute dans les
    # globals de `core/common.py`. Un import relatif y compte les niveaux
    # depuis le module hote, pas depuis ce fichier - il partait donc au-dela du
    # paquet. Tardif aussi, pour ne pas charger les modules metier au seul fait
    # d'ouvrir une instance.
    from coproscope.modules.zone_synchronisee import raison_de_refus

    a_verifier = [config.instance_root]
    for nom in ("workspace", "raw", "system", "outputs", "staging", "logs"):
        try:
            a_verifier.append(config.root(nom))
        except (KeyError, TypeError, ValueError):
            continue
    vus: set[str] = set()
    for chemin in a_verifier:
        cle = str(chemin)
        if cle in vus:
            continue
        vus.add(cle)
        raison = raison_de_refus(chemin)
        if raison:
            raise SystemExit(
                "Cette instance vit dans un dossier synchronise, et"
                " CoproScope n'y ecrira pas." + _DEUX_LIGNES + "  "
                + raison + _DEUX_LIGNES
                + "  Deplacez l'instance sur un disque local non"
                " synchronise, puis relancez."
            )


def relative_to(base: Path, target: Path) -> str:
    try:
        return str(target.relative_to(base))
    except ValueError:
        return str(target)


class RunContext:
    def __init__(self, instance: InstanceConfig, command: str) -> None:
        self.instance = instance
        self.command = command
        self.run_id = f"{slugify(command)}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        self.logs_dir = instance.root("logs")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.note(f"## {self.run_id}\n\n- command: `{command}`\n- instance: `{instance.instance_id}`\n")
        self.log_run("STARTED", "")

    def log_run(self, status: str, details: str) -> None:
        append_csv_row(
            self.logs_dir / "run_log.csv",
            ["timestamp", "run_id", "command", "status", "details"],
            {
                "timestamp": now_iso(),
                "run_id": self.run_id,
                "command": self.command,
                "status": status,
                "details": details,
            },
        )

    def log_action(self, action: str, target: Path, detail: str) -> None:
        append_csv_row(
            self.logs_dir / "action_log.csv",
            ["timestamp", "run_id", "action", "target", "detail"],
            {
                "timestamp": now_iso(),
                "run_id": self.run_id,
                "action": action,
                "target": str(target),
                "detail": detail,
            },
        )

    def log_error(self, error: str) -> None:
        append_csv_row(
            self.logs_dir / "error_log.csv",
            ["timestamp", "run_id", "command", "error"],
            {
                "timestamp": now_iso(),
                "run_id": self.run_id,
                "command": self.command,
                "error": error,
            },
        )

    def note(self, message: str) -> None:
        path = self.logs_dir / "agent_log.md"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip() + "\n\n")

    def finish(self, status: str = "OK", details: str = "") -> None:
        self.log_run(status, details)


def merge_category_rows(
    existing_rows: list[dict[str, str]],
    new_rows: list[dict[str, str]],
    category: str,
) -> list[dict[str, str]]:
    preserved = [row for row in existing_rows if row.get("category") != category]
    return preserved + new_rows


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def env_snapshot(instance: InstanceConfig) -> dict[str, str]:
    combined: dict[str, str] = {}
    for path in instance.env_files():
        combined.update(parse_env_file(path))
    for key in instance.required_env() + instance.optional_env():
        if os.environ.get(key):
            combined[key] = os.environ[key]
    return combined
