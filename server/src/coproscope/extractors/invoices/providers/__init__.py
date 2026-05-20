"""Provider-specific invoice extractors."""

from .cogelec import CogelecInvoiceProviderExtractor
from .edelen import EdelenInvoiceProviderExtractor
from .engie import EngieInvoiceProviderExtractor
from .generic import GenericInvoiceProviderExtractor
from .omega_ascenseur import OmegaAscenseurInvoiceProviderExtractor
from .phocea import PhoceaInvoiceProviderExtractor

__all__ = [
    "CogelecInvoiceProviderExtractor",
    "EdelenInvoiceProviderExtractor",
    "EngieInvoiceProviderExtractor",
    "GenericInvoiceProviderExtractor",
    "OmegaAscenseurInvoiceProviderExtractor",
    "PhoceaInvoiceProviderExtractor",
]
