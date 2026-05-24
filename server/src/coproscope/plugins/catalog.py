from __future__ import annotations

from dataclasses import asdict, dataclass, field


CATALOG_VERSION = "official-v1"


@dataclass(frozen=True)
class PluginPermission:
    code: str
    scope: str
    reason: str


@dataclass(frozen=True)
class PluginContract:
    name: str
    version: str
    path: str
    required: bool = True


@dataclass(frozen=True)
class PluginSignature:
    status: str
    authority: str
    key_id: str
    digest_sha256: str
    signature: str
    activation_policy: str


@dataclass(frozen=True)
class PluginCompatibility:
    catalog_version: str = CATALOG_VERSION
    app_min_version: str = "0.1.0"
    app_max_version: str | None = None
    vault_format_min: str = "1"
    vault_format_max: str | None = None
    python_min: str = "3.11"


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    summary: str
    modules: tuple[str, ...]
    permissions: tuple[PluginPermission, ...]
    event_types_produced: tuple[str, ...]
    input_contracts: tuple[PluginContract, ...]
    output_contracts: tuple[PluginContract, ...]
    required_by_vault: bool
    recommended_by_vault: bool
    signature: PluginSignature = field(default_factory=lambda: SIGNATURE_PLACEHOLDER)
    compatibility: PluginCompatibility = field(default_factory=PluginCompatibility)
    official: bool = True
    community_allowed_v1: bool = False
    auto_update: bool = False
    local_outside_vault: bool = True
    activation_requires_signature: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


SIGNATURE_PLACEHOLDER = PluginSignature(
    status="placeholder",
    authority="coproscope-official-root-future",
    key_id="COPROSCOPE-OFFICIAL-V1-FUTURE",
    digest_sha256="sha256:pending-packaged-artifact",
    signature="sig:pending-official-release",
    activation_policy="future_signed_activation_required",
)


OFFICIAL_PLUGINS_V1: tuple[PluginManifest, ...] = (
    PluginManifest(
        plugin_id="official.docops",
        name="DocOps",
        version="1.0.0",
        summary="Inventorie, extrait, classe et controle la completude documentaire du vault.",
        modules=("coproscope.modules.docuscope",),
        required_by_vault=True,
        recommended_by_vault=True,
        permissions=(
            PluginPermission("vault.read.raw", "raw/", "Lire les pieces deposees localement."),
            PluginPermission("vault.write.registers", "registers/documents.csv", "Tenir le registre documentaire."),
            PluginPermission("vault.write.reports", "outputs/reports/", "Produire les matrices de completude."),
        ),
        event_types_produced=(
            "document.inventoried",
            "document.text_extracted",
            "document.classified",
            "document.completeness_checked",
        ),
        input_contracts=(
            PluginContract("vault.instance", "1", "instance.yml"),
            PluginContract("document.register", "1", "registers/documents.csv", required=False),
            PluginContract("proof.matrix", "1", "matrices/proofs.csv", required=False),
        ),
        output_contracts=(
            PluginContract("document.register", "1", "registers/documents.csv"),
            PluginContract("document.completeness_matrix", "1", "outputs/reports/matrice_completude_documentaire.csv"),
            PluginContract("document.requests", "1", "outputs/reports/pieces_a_demander.csv"),
        ),
    ),
    PluginManifest(
        plugin_id="official.comptascope",
        name="ComptaScope",
        version="1.0.0",
        summary="Reconstruit les controles comptables locaux et rapproche factures et etat des depenses.",
        modules=("coproscope.modules.accounting", "coproscope.modules.factureops"),
        required_by_vault=False,
        recommended_by_vault=True,
        permissions=(
            PluginPermission("vault.read.documents", "registers/documents.csv", "Relier les factures aux pieces source."),
            PluginPermission("vault.read.accounting", "system/accounting/", "Lire les sources comptables locales."),
            PluginPermission("vault.write.accounting", "outputs/accounting/", "Ecrire les rapprochements et guides de controle."),
        ),
        event_types_produced=(
            "invoice.evidence_extracted",
            "invoice.anomaly_detected",
            "accounting.ledger_reconstructed",
            "accounting.expense_reconciled",
            "supplier.due_diligence_suggested",
        ),
        input_contracts=(
            PluginContract("document.register", "1", "registers/documents.csv"),
            PluginContract("invoice.evidence", "1", "system/accounting/preloaded_invoice_evidence_<year>.csv", required=False),
            PluginContract("expense.statement", "1", "system/accounting/expense_statement_lines_<year>.csv", required=False),
        ),
        output_contracts=(
            PluginContract("invoice.evidence", "1", "outputs/accounting/<year>/invoice_evidence_<year>.csv"),
            PluginContract("invoice.anomalies", "1", "outputs/accounting/<year>/invoice_anomalies_<year>.csv"),
            PluginContract("accounting.reconciliation", "1", "outputs/accounting/<year>/invoice_expense_matches_<year>.csv"),
            PluginContract("accounting.control_guide", "1", "outputs/accounting/<year>/controle_comptes_guide_<year>.csv"),
        ),
    ),
    PluginManifest(
        plugin_id="official.privacy_biffage",
        name="PrivacyOps / BiffageOps",
        version="1.0.0",
        summary="Prepare les exports minimises et les versions biffees sans sortir les secrets du vault local.",
        modules=("coproscope.modules.privacyops", "coproscope.modules.biffageops"),
        required_by_vault=True,
        recommended_by_vault=True,
        permissions=(
            PluginPermission("vault.read.documents", "registers/documents.csv", "Identifier les pieces sensibles."),
            PluginPermission("vault.read.privacy_rules", "configs/privacy_rules.default.yml", "Appliquer les regles de minimisation."),
            PluginPermission("vault.write.sanitized_exports", "outputs/privacy/", "Ecrire les copies biffees et journaux de minimisation."),
        ),
        event_types_produced=(
            "privacy.sensitivity_classified",
            "privacy.redaction_planned",
            "privacy.export_sanitized",
        ),
        input_contracts=(
            PluginContract("document.register", "1", "registers/documents.csv"),
            PluginContract("privacy.rules", "1", "configs/privacy_rules.default.yml"),
        ),
        output_contracts=(
            PluginContract("privacy.audit_log", "1", "outputs/privacy/audit_log.csv"),
            PluginContract("privacy.sanitized_bundle", "1", "outputs/privacy/sanitized/"),
        ),
    ),
    PluginManifest(
        plugin_id="official.docai_ocr",
        name="DocAI / OCR lourd",
        version="1.0.0",
        summary="Option lourde separee pour OCR, structure de document et enrichissements layout locaux.",
        modules=("coproscope.modules.docai",),
        required_by_vault=False,
        recommended_by_vault=False,
        permissions=(
            PluginPermission("vault.read.raw", "raw/", "Lire les scans a enrichir."),
            PluginPermission("vault.write.text", "system/text/", "Ecrire les transcriptions OCR locales."),
            PluginPermission("local.compute.heavy", "local-runtime", "Utiliser les dependances OCR/layout optionnelles."),
        ),
        event_types_produced=(
            "document.ocr_completed",
            "document.layout_enriched",
        ),
        input_contracts=(
            PluginContract("document.register", "1", "registers/documents.csv"),
            PluginContract("document.binary", "1", "raw/<document>", required=False),
        ),
        output_contracts=(
            PluginContract("document.text", "1", "system/text/<doc_id>.txt"),
            PluginContract("document.layout", "1", "system/docai/<doc_id>.json", required=False),
        ),
    ),
    PluginManifest(
        plugin_id="official.evidence_exports",
        name="Evidence / Exports",
        version="1.0.0",
        summary="Produit les dossiers de preuve, exports CSV et rapports partageables depuis les artefacts locaux.",
        modules=("coproscope.modules.evidenceops", "coproscope.modules.gristops"),
        required_by_vault=False,
        recommended_by_vault=True,
        permissions=(
            PluginPermission("vault.read.outputs", "outputs/", "Assembler les preuves deja produites."),
            PluginPermission("vault.write.evidence", "outputs/evidence/", "Ecrire les rapports et index de preuve."),
            PluginPermission("network.optional.disabled_by_default", "external dashboards", "Preparer l'export sans synchronisation automatique."),
        ),
        event_types_produced=(
            "evidence.report_built",
            "export.bundle_prepared",
        ),
        input_contracts=(
            PluginContract("document.register", "1", "registers/documents.csv", required=False),
            PluginContract("invoice.evidence", "1", "outputs/accounting/<year>/invoice_evidence_<year>.csv", required=False),
            PluginContract("privacy.sanitized_bundle", "1", "outputs/privacy/sanitized/", required=False),
        ),
        output_contracts=(
            PluginContract("evidence.report", "1", "outputs/evidence/rapport_preuves_<dataset>_<year>.md"),
            PluginContract("export.bundle", "1", "outputs/exports/<dataset>/"),
        ),
    ),
)


def official_catalog() -> tuple[PluginManifest, ...]:
    return OFFICIAL_PLUGINS_V1


def plugin_ids() -> tuple[str, ...]:
    return tuple(plugin.plugin_id for plugin in OFFICIAL_PLUGINS_V1)


def get_plugin_manifest(plugin_id: str) -> PluginManifest:
    for plugin in OFFICIAL_PLUGINS_V1:
        if plugin.plugin_id == plugin_id:
            return plugin
    raise KeyError(plugin_id)


def required_plugins_for_vault() -> tuple[PluginManifest, ...]:
    return tuple(plugin for plugin in OFFICIAL_PLUGINS_V1 if plugin.required_by_vault)


def recommended_plugins_for_vault() -> tuple[PluginManifest, ...]:
    return tuple(plugin for plugin in OFFICIAL_PLUGINS_V1 if plugin.recommended_by_vault)


def validate_official_catalog() -> tuple[str, ...]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for plugin in OFFICIAL_PLUGINS_V1:
        if plugin.plugin_id in seen_ids:
            errors.append(f"duplicate plugin_id: {plugin.plugin_id}")
        seen_ids.add(plugin.plugin_id)
        if not plugin.official:
            errors.append(f"{plugin.plugin_id}: non-official plugin is not allowed in V1")
        if plugin.community_allowed_v1:
            errors.append(f"{plugin.plugin_id}: community plugins are not allowed in V1")
        if plugin.auto_update:
            errors.append(f"{plugin.plugin_id}: auto-update is forbidden in V1")
        if not plugin.local_outside_vault:
            errors.append(f"{plugin.plugin_id}: plugin code must stay local and outside the vault")
        if not plugin.activation_requires_signature:
            errors.append(f"{plugin.plugin_id}: activation must require a future signature")
        if plugin.signature.status != "placeholder":
            errors.append(f"{plugin.plugin_id}: V1 expects a signature placeholder")
        if not plugin.permissions:
            errors.append(f"{plugin.plugin_id}: permissions are required")
        if not plugin.event_types_produced:
            errors.append(f"{plugin.plugin_id}: produced event types are required")
        if not plugin.input_contracts or not plugin.output_contracts:
            errors.append(f"{plugin.plugin_id}: input and output contracts are required")
    return tuple(errors)
