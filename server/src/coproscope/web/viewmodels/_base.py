from __future__ import annotations

from ._runtime import *

STATUS_OPERATIONAL = "operationnel"
STATUS_PARTIAL = "partiel"
STATUS_WORKING = "en chantier"
STATUS_NOT_STARTED = "non demarre"
ACTION_EXPORT_FIELDS = [
    "id",
    "priority",
    "status",
    "domain",
    "source",
    "owner",
    "title",
    "detail",
    "next_step",
    "evidence",
    "href",
]
FORBIDDEN_UX_PUBLIC_TOKENS = {"raw", "restricted", "logs", "private"}
FORBIDDEN_UX_PUBLIC_ROOTS = {"users", "home", "var", "tmp", "etc", "opt", "root", "mnt", "volumes"}
UX_REDACTED_REFERENCE = "reference locale masquee"
_FORBIDDEN_UX_PUBLIC_TOKEN_RE = re.compile(r"(?<![0-9a-z_])(?:raw|restricted|logs|private)(?![0-9a-z_])")
_UX_PUBLIC_TOKEN_RE = re.compile(r"[0-9a-z]+")
_UX_PRIVATE_SUBSTRINGS = (
    "100_collecte_raw",
    "200_inbox",
    "220_assemblees",
)
_UX_SUSPICIOUS_SUBSTRINGS = (
    "://",
    "/",
    "\\",
    "raw",
    "restricted",
    "logs",
    "private",
    *_UX_PRIVATE_SUBSTRINGS,
)


class _JinjaItemsProxy:
    def __init__(self, parent: dict[str, Any]) -> None:
        self.parent = parent

    def __iter__(self):
        value = dict.__getitem__(self.parent, "items")
        return iter(value if isinstance(value, list) else [])

    def __call__(self):
        return dict.items(self.parent)


class _JinjaItemsDict(dict[str, Any]):
    def __getattribute__(self, name: str) -> Any:
        if name == "items" and dict.__contains__(self, "items"):
            return _JinjaItemsProxy(self)
        return dict.__getattribute__(self, name)


@dataclass(frozen=True)
class DataTable:
    path: Path
    fields: list[str]
    rows: list[dict[str, str]]

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def count(self) -> int:
        return len(self.rows)


def _read_table(path: Path) -> DataTable:
    fields, rows = read_csv(path)
    return DataTable(path=path, fields=fields, rows=rows)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _rel(instance: InstanceConfig, path: Path) -> str:
    return relative_to(instance.instance_root, path)


def _safe_register(instance: InstanceConfig, name: str) -> Path | None:
    try:
        return instance.register(name)
    except KeyError:
        return None


def _safe_artifact(instance: InstanceConfig, name: str) -> Path | None:
    try:
        return instance.artifact(name)
    except KeyError:
        return None


def _counter(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(Counter(row.get(field, "") or "non renseigne" for row in rows))


def _clip(value: str, length: int = 120) -> str:
    normalized = " ".join((value or "").split())
    if len(normalized) <= length:
        return normalized
    return normalized[: length - 1].rstrip() + "..."


def _amount_value(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    cleaned = (
        text.replace("\u00a0", " ")
        .replace("EUR", "")
        .replace("eur", "")
        .replace("â‚¬", "")
        .replace(" ", "")
    )
    if "," in cleaned and cleaned.rfind(",") > cleaned.rfind("."):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if cleaned in {"", "-", ".", "-."}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _amount_label(value: object, fallback: str = "Montant non charge") -> str:
    amount = _amount_value(value)
    if amount is None:
        return fallback
    return f"{amount:,.2f} EUR".replace(",", " ").replace(".", ",")


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value or "").strip().replace("\u00a0", " ").replace(" ", "")
    if not text:
        return 0
    try:
        return int(float(text.replace(",", ".")))
    except ValueError:
        return 0


def _status(has_data: bool, has_file: bool = False) -> str:
    if has_data:
        return STATUS_OPERATIONAL
    if has_file:
        return STATUS_PARTIAL
    return STATUS_WORKING


def _artifact(instance: InstanceConfig, label: str, path: Path | None, kind: str) -> dict[str, object]:
    if path is None:
        return {
            "label": label,
            "kind": kind,
            "exists": False,
            "count": 0,
            "path": "",
            "state": "absent",
        }
    fields, rows = read_csv(path) if path.suffix.lower() == ".csv" else ([], [])
    return {
        "label": label,
        "kind": kind,
        "exists": path.exists(),
        "count": len(rows),
        "path": _rel(instance, path),
        "state": "pret" if path.exists() else "a generer",
        "fields": fields,
    }


def _accounting_base(instance: InstanceConfig, year: int) -> Path:
    primary = instance.artifact("accounting_dir") / str(year)
    try:
        outputs = instance.root("outputs")
    except KeyError:
        return primary
    alternatives = [
        outputs / f"accounting_{year}_factures",
        primary,
    ]
    for candidate in alternatives:
        if (candidate / f"summary_{year}.json").exists() or (candidate / f"summary_{year}_controlled.json").exists():
            return candidate
    return primary


def _accounting_paths(instance: InstanceConfig, year: int) -> dict[str, Path]:
    base = _accounting_base(instance, year)
    controlled = base / f"summary_{year}_controlled.json"
    return {
        "base": base,
        "summary": controlled if controlled.exists() else base / f"summary_{year}.json",
        "invoice_evidence": base / f"invoice_evidence_{year}_controlled.csv"
        if (base / f"invoice_evidence_{year}_controlled.csv").exists()
        else base / f"invoice_evidence_{year}.csv",
        "invoice_anomalies": base / f"invoice_anomalies_{year}.csv",
        "ledger": base / f"ledger_reconstruction_{year}_controlled.csv"
        if (base / f"ledger_reconstruction_{year}_controlled.csv").exists()
        else base / f"ledger_reconstruction_{year}.csv",
        "expense_statement": base / f"expense_statement_lines_{year}_controlled.csv"
        if (base / f"expense_statement_lines_{year}_controlled.csv").exists()
        else base / f"expense_statement_lines_{year}.csv",
        "controls": base / f"accounting_controls_{year}_controlled.csv"
        if (base / f"accounting_controls_{year}_controlled.csv").exists()
        else base / f"accounting_controls_{year}.csv",
        "matches": base / f"invoice_expense_matches_{year}_controlled.csv"
        if (base / f"invoice_expense_matches_{year}_controlled.csv").exists()
        else base / f"invoice_expense_matches_{year}_explained.csv"
        if (base / f"invoice_expense_matches_{year}_explained.csv").exists()
        else base / f"invoice_expense_matches_{year}.csv",
        "non_matches": base / f"non_rapproches_prioritaires_{year}_explained.csv"
        if (base / f"non_rapproches_prioritaires_{year}_explained.csv").exists()
        else base / f"non_rapproches_prioritaires_{year}.csv",
        "priority_controls": base / f"controles_p1_{year}.csv",
        "aliases": base / f"supplier_alias_suggestions_{year}.csv",
        "supplier_due": base / f"supplier_due_diligence_controls_{year}.csv",
        "report": base / f"rapport_comptascope_{year}_explique.md"
        if (base / f"rapport_comptascope_{year}_explique.md").exists()
        else base / f"rapport_comptascope_{year}.md",
    }


def _privacy_paths(instance: InstanceConfig) -> dict[str, Path]:
    privacy_dir = _safe_artifact(instance, "privacy_dir") or instance.root("staging") / "privacy_dir"
    redacted_dir = _safe_artifact(instance, "redacted_dir") or instance.root("staging") / "redacted_dir"
    return {
        "screening": _safe_register(instance, "privacy_screening")
        or privacy_dir / "registre_screening_confidentialite.csv",
        "redactions": _safe_register(instance, "redactions")
        or privacy_dir / "registre_biffages.csv",
        "queue": privacy_dir / "file_biffage.csv",
        "report": instance.artifact("reports_dir") / "rapport_screening_confidentialite.md",
        "redacted_dir": redacted_dir,
    }


def _read_report(path: Path, max_chars: int = 8000) -> dict[str, str]:
    if not path.exists():
        return {"exists": False, "text": "", "html": ""}
    try:
        text = path.read_text(encoding="utf-8-sig")[:max_chars]
    except OSError:
        return {"exists": False, "text": "", "html": ""}
    escaped = html.escape(text)
    return {"exists": True, "text": text, "html": escaped}


def _module(label: str, status: str, detail: str, href: str) -> dict[str, str]:
    return {"label": label, "status": status, "detail": detail, "href": href}


def _priority(title: str, severity: str, detail: str, href: str) -> dict[str, str]:
    return {"title": title, "severity": severity or "info", "detail": detail, "href": href}


def _action(
    title: str,
    source: str,
    priority: str,
    detail: str,
    href: str,
    *,
    action_id: str = "",
    status: str = "a_traiter",
    domain: str = "general",
    domain_label: str = "General",
    owner: str = "Conseil syndical",
    next_step: str = "",
    evidence: str = "",
    channel: str = "",
) -> dict[str, str]:
    return {
        "id": action_id,
        "title": title,
        "source": source,
        "priority": priority or "P2",
        "detail": detail,
        "href": href,
        "status": status,
        "domain": domain,
        "domain_label": domain_label,
        "owner": owner,
        "next_step": next_step or detail,
        "evidence": evidence,
        "channel": channel,
    }


def _priority_for(row: dict[str, str], default: str = "P2") -> str:
    return row.get("match_priority") or row.get("severity") or row.get("priority") or default
