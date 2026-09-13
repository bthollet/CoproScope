"""Aucun module n'utilise un nom qu'il n'a ni defini ni recu.

**Le defaut que ce test ferme, constate quatre fois le meme jour.** Decouper un
module laisse derriere lui des noms orphelins: la fonction part dans le nouveau
fichier, l'import reste dans l'ancien. Python ne dit rien au chargement - un
nom global n'est resolu qu'a l'appel - donc le module s'importe, la suite
demarre, et l'erreur ne sort qu'en traversant la ligne fautive. Peut-etre
jamais en test.

Le 2026-09-06, l'extraction de l'ecran de gouvernance en trois modules a produit
quatre noms orphelins d'affilee - `A`, `controle_applicable`, `euros`,
`_nombre` - et chacun a coute un passage complet de la suite pour etre trouve.
Chacun se voyait en une seconde par lecture statique. Ce depot decoupe beaucoup,
a cause de la limite de 600 lignes: le defaut reviendra.

**Les trois facons dont un nom arrive legitimement dans un module ici**, et que
ce test doit connaitre sous peine d'accuser a tort:

1. l'import ordinaire;
2. **l'espace de noms partage de paquet** - `web/viewmodels/__init__.py` fait
   `module.__dict__.update(_namespace)`, donc ses fragments se citent
   mutuellement sans s'importer;
3. **les fragments `.pyfrag`** - `_exec_source_fragments(globals(), __file__,
   "<dossier>")` execute des morceaux DANS le module. Un `.pyfrag` n'est pas
   analysable seul: ce sont des morceaux, et il faut les concatener dans
   l'ordre comme le fait le mecanisme reel;
4. **les sources numerotees d'un dossier de concatenation** - `_*_parts/00_x.py`,
   `01_y.py`... sont les SOURCES editables de ces fragments. Elles ne
   s'importent pas seules et se lisent comme une unite, dans l'ordre de leur
   numero. C'est la convention qui rend la limite de 600 lignes tenable.

**Limite assumee.** Ce test ne voit pas les noms crees dynamiquement -
`globals()[...] = `, `setattr`, import conditionnel. Un module qui en use
legitimement se declare dans `TOLERES` avec sa raison, jamais en silence.
"""

from __future__ import annotations

import ast
import builtins
import io
import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent / "src" / "coproscope"

#: Ce que Python pose lui-meme dans tout module.
_DUNDERS = {
    "__file__", "__name__", "__doc__", "__package__", "__spec__",
    "__loader__", "__path__", "__builtins__", "__all__", "__dict__",
}

_APPEL_FRAGMENTS = re.compile(
    r"_exec_source_fragments\(\s*globals\(\)\s*,\s*__file__\s*,\s*[\"']([^\"']+)[\"']"
)

#: Nom de module -> raison. Un module n'entre ici qu'avec une raison ecrite.
TOLERES: dict[str, str] = {}


def _noms_definis_dans(source: str) -> set[str]:
    definis: set[str] = set()
    for noeud in ast.walk(ast.parse(source)):
        if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definis.add(noeud.name)
        elif isinstance(noeud, ast.Name) and isinstance(noeud.ctx, ast.Store):
            definis.add(noeud.id)
        elif isinstance(noeud, ast.arg):
            definis.add(noeud.arg)
        elif isinstance(noeud, (ast.Import, ast.ImportFrom)):
            for alias in noeud.names:
                definis.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(noeud, ast.ExceptHandler) and noeud.name:
            definis.add(noeud.name)
        elif isinstance(noeud, ast.Global):
            definis.update(noeud.names)
    return definis


def _lire(chemin: Path) -> str:
    return io.open(chemin, encoding="utf-8", errors="replace").read()


def _noms_definis(chemin: Path) -> set[str]:
    return _noms_definis_dans(_lire(chemin))


def _noms_des_fragments(chemin: Path) -> set[str]:
    """Les noms poses par les `.pyfrag` qu'un module execute dans ses globals.

    Les fragments sont concatenes dans l'ordre des noms de fichier, comme le
    fait `_exec_source_fragments`: pris un par un ils ne se compilent pas.
    """
    noms: set[str] = set()
    for dossier in _APPEL_FRAGMENTS.findall(_lire(chemin)):
        parts = sorted((chemin.parent / dossier).glob("*.pyfrag"))
        if not parts:
            continue
        source = "\n".join(_lire(p) for p in parts)
        try:
            noms |= _noms_definis_dans(source)
        except SyntaxError:  # pragma: no cover - un fragment isole reste partiel
            pass
    return noms


_SOURCE_NUMEROTEE = re.compile(r"^\d\d_")


def _dossiers_de_concatenation(racine: Path) -> set[str]:
    """Les dossiers dont les sources sont numerotees, donc concatenees."""
    dossiers = set()
    for chemin in racine.rglob("*.py"):
        if "__pycache__" in chemin.parts:
            continue
        if _SOURCE_NUMEROTEE.match(chemin.name):
            dossiers.add(str(chemin.parent.relative_to(racine.parent)))
    return dossiers


def _paquets_a_espace_partage() -> set[str]:
    """Les paquets dont l'`__init__` injecte ses noms dans chaque membre."""
    partages = set()
    for init in RACINE.rglob("__init__.py"):
        if "__dict__.update(" in _lire(init):
            partages.add(str(init.parent.relative_to(RACINE.parent)))
    return partages


def _modules(racine: Path):
    for chemin in sorted(racine.rglob("*.py")):
        if "__pycache__" not in chemin.parts:
            yield chemin


class AucunNomOrphelinTests(unittest.TestCase):
    def test_chaque_module_definit_ou_recoit_ce_qu_il_utilise(self) -> None:
        partages = _paquets_a_espace_partage() | _dossiers_de_concatenation(RACINE)
        union: dict[str, set[str]] = {}
        for chemin in _modules(RACINE):
            paquet = str(chemin.parent.relative_to(RACINE.parent))
            if paquet in partages:
                union.setdefault(paquet, set()).update(
                    _noms_definis(chemin) | _noms_des_fragments(chemin))

        fautifs = []
        for chemin in _modules(RACINE):
            nom = str(chemin.relative_to(RACINE.parent))
            if nom in TOLERES:
                continue
            paquet = str(chemin.parent.relative_to(RACINE.parent))
            utilises = {
                n.id for n in ast.walk(ast.parse(_lire(chemin)))
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
            }
            connus = (_noms_definis(chemin) | _noms_des_fragments(chemin)
                      | union.get(paquet, set()) | set(dir(builtins)) | _DUNDERS)
            manquants = sorted(utilises - connus)
            if manquants:
                fautifs.append(nom + ": " + ", ".join(manquants))

        self.assertEqual(
            fautifs, [],
            "\n\n  Des modules utilisent un nom qu'ils n'ont ni defini ni recu.\n"
            "  Python ne le dira qu'en traversant la ligne, donc peut-etre\n"
            "  jamais en test:\n\n    " + "\n    ".join(fautifs) + "\n",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
