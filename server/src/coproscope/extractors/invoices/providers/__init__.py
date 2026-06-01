"""Provider-specific invoice extractors."""

from .cogelec import CogelecInvoiceProviderExtractor
from .asv import AsvInvoiceProviderExtractor
from .edelen import EdelenInvoiceProviderExtractor
from .engie import EngieInvoiceProviderExtractor
from .generic import GenericInvoiceProviderExtractor
from .insurance_notice import InsuranceNoticeProviderExtractor
from .omega_ascenseur import OmegaAscenseurInvoiceProviderExtractor
from .orange import OrangeInvoiceProviderExtractor
from .phocea import PhoceaInvoiceProviderExtractor

__all__ = [
    "CogelecInvoiceProviderExtractor",
    "AsvInvoiceProviderExtractor",
    "EdelenInvoiceProviderExtractor",
    "EngieInvoiceProviderExtractor",
    "GenericInvoiceProviderExtractor",
    "InsuranceNoticeProviderExtractor",
    "OmegaAscenseurInvoiceProviderExtractor",
    "OrangeInvoiceProviderExtractor",
    "PhoceaInvoiceProviderExtractor",
]
