from __future__ import annotations

from dataclasses import dataclass

from .base import DocumentExtractionEvidence, provider_key_from_name


@dataclass(frozen=True)
class ProviderExtractorSeed:
    provider_name: str
    provider_key: str
    evidence: DocumentExtractionEvidence
    target_fields: tuple[str, ...] = (
        "fournisseur",
        "siren_siret",
        "numero_facture",
        "date_facture",
        "ht",
        "tva",
        "ttc",
    )


def build_provider_extractor_seed(provider_name: str, evidence: DocumentExtractionEvidence) -> ProviderExtractorSeed:
    return ProviderExtractorSeed(
        provider_name=provider_name.strip(),
        provider_key=provider_key_from_name(provider_name),
        evidence=evidence,
    )


def build_extractor_generation_prompt(seed: ProviderExtractorSeed) -> str:
    evidence_text = seed.evidence.combined_text()
    fields = ", ".join(seed.target_fields)
    return f"""Create a CoproScope invoice provider extractor.

Provider: {seed.provider_name}
Provider key: {seed.provider_key}

Use the evidence in this priority order:
1. Native PDF text from PyMuPDF or pypdf.
2. Local OCR text from RapidOCR, GutenOCR, or sidecar OCR.
3. Docling Markdown/tables.
4. Layout JSON from PyMuPDF/LayoutLMv3/LayoutALM.
5. Qwen VL visual-review notes as evidence only, never as final accounting validation.

Return deterministic Python code compatible with InvoiceExtraction.
Extract only these fields: {fields}.
Do not include private paths, real document names beyond synthetic fixtures, secrets, or model-cache locations.
Keep filename families as routing hints only; provider text patterns must drive extraction.

Evidence:
{evidence_text[:12000]}
"""


def build_provider_extractor_template(seed: ProviderExtractorSeed) -> str:
    class_name = "".join(part.capitalize() for part in seed.provider_key.split("_") if part) + "InvoiceProviderExtractor"
    return f'''from __future__ import annotations

from ..base import DocumentExtractionEvidence, InvoiceExtraction, extract_generic_invoice_from_evidence


class {class_name}:
    """Extractor for {seed.provider_name} invoices."""

    provider_key = "{seed.provider_key}"
    status = "candidate_generalizable"
    supported_inputs = ["pdf_text", "local_ocr", "docling_markdown", "layout_json", "visual_review", "factur-x", "xml", "ubl", "cii"]

    def extract(self, text: str, file_name: str = "") -> InvoiceExtraction:
        # Start from the generic extraction, then replace this with provider-specific
        # regexes backed by synthetic fixtures.
        extraction = extract_generic_invoice_from_evidence(
            DocumentExtractionEvidence(
                file_name=file_name,
                native_text=text,
            )
        )
        extraction.provider_key = self.provider_key
        extraction.confidence = "low"
        return extraction
'''
