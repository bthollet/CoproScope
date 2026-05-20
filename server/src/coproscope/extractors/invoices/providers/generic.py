from __future__ import annotations

from ..base import InvoiceExtraction, extract_generic_invoice_fields


class GenericInvoiceProviderExtractor:
    """Fallback extractor used before a provider-specific parser exists."""

    provider_key = "generic"
    status = "generalizable"
    supported_inputs = ["pdf_text", "factur-x", "xml", "ubl", "cii"]

    def extract(self, text: str, file_name: str = "") -> InvoiceExtraction:
        return extract_generic_invoice_fields(text, file_name=file_name)
