from __future__ import annotations

from pathlib import Path as _Path

_PART_DIR = _Path(__file__).with_name('_docuscope_parts')
_PART_FILES = (
    '00_source_encoding.py',
    '01_inventory_and_extraction.py',
    # Avant 02: le classement lit les champs d'une regle par cette table, donc
    # elle doit exister quand `_classify` est definie.
    '01b_champs_de_regle.py',
    '02_classification.py',
    # Apres 02: la reconciliation par empreinte confronte les lignes que le
    # classement vient d'ecrire, une fois toutes les lignes traitees.
    '02b_empreintes_concurrentes.py',
    '03_title_signature.py',
    # Avant 04: la mise en forme du rapport est definie quand le module qui
    # mesure l'appelle. Sortie de `04` le 2026-09-11, qui atteignait 602 lignes
    # pour une limite de 600 - decoupage annonce par `RM-2026-0088`.
    '04b_completude_rendu.py',
    '04_completeness_and_kpis.py',
)

for _part_file in _PART_FILES:
    _part_path = _PART_DIR / _part_file
    exec(compile(_part_path.read_text(encoding="utf-8"), str(_part_path), "exec"), globals())

del _Path, _PART_DIR, _PART_FILES, _part_file, _part_path
