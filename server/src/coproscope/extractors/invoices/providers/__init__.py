"""Provider-specific invoice extractors."""

from .access_automation import AccessAutomationInvoiceProviderExtractor
from .asv import AsvInvoiceProviderExtractor
from .cogelec import CogelecInvoiceProviderExtractor
from .oderan import OderanInvoiceProviderExtractor
from .engie import EngieInvoiceProviderExtractor
from .generic import GenericInvoiceProviderExtractor
from .insurance_notice import InsuranceNoticeProviderExtractor
from .omega_ascenseur import OmegaAscenseurInvoiceProviderExtractor
from .orange import OrangeInvoiceProviderExtractor
from .phocea import PhoceaInvoiceProviderExtractor

__all__ = [
    "AccessAutomationInvoiceProviderExtractor",
    "AsvInvoiceProviderExtractor",
    "CogelecInvoiceProviderExtractor",
    "OderanInvoiceProviderExtractor",
    "EngieInvoiceProviderExtractor",
    "GenericInvoiceProviderExtractor",
    "InsuranceNoticeProviderExtractor",
    "OmegaAscenseurInvoiceProviderExtractor",
    "OrangeInvoiceProviderExtractor",
    "PhoceaInvoiceProviderExtractor",
]
