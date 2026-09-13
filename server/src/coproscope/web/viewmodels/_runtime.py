from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import quote

from ...core.common import InstanceConfig, read_csv, relative_to
from ...modules import decisionops, incidentops
from ..depot import export_catalog, read_deposit_manifests
from ._comptage_declare import (
    COMPTAGE_CATEGORIES,
    COMPTAGE_ECRITURES,
    COMPTAGE_FACTURES,
    COMPTAGE_LIGNES_ETAT_DEPENSES,
    COMPTAGE_PIECES_DISTINCTES,
    COMPTAGE_PREUVES_VERIFIEES,
    COMPTAGE_RAPPROCHEMENTS,
    COMPTAGE_SYNTHESE,
    le_plus_grand,
)
