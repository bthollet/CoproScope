"""Chaque module du pont s'importe seul, dans n'importe quel ordre.

**Le defaut que ce test ferme.** En decoupant `_pont_actes_lignes` pour
repasser sous 600 lignes le 2026-09-05, un cycle d'import a ete introduit:
`_pont_actes_liens` importait un aide de `_pont_actes_lignes`, qui reexportait
en retour les fonctions de liens. `import _pont_actes_liens` seul levait
`ImportError`, et **les 1610 tests passaient quand meme** - parce que
`pont_actes` importe toujours `_pont_actes_lignes` en premier, ce qui amorcait
le module dans le bon ordre par accident.

Un decoupage suivant, ou un simple changement d'ordre d'import chez un
appelant, aurait casse la chaine sans qu'aucun test ne le dise. C'est le mode
de defaillance que ce depot combat, applique a son propre outillage.

La correction de fond a ete de rendre le sens des imports unique: l'aide
partage `_lu` vit dans `_pont_actes_source`, dont les deux autres dependent
deja. Ce test empeche le cycle de revenir.

Le second test vise l'autre moitie du meme defaut: `Iterable` et `Any` etaient
utilises dans une signature sans etre importes. `from __future__ import
annotations` garde les annotations sous forme de chaines, donc l'erreur dort
jusqu'a ce que quelqu'un les lise.
"""

from __future__ import annotations

import importlib
import sys
import typing
import unittest

MODULES = (
    "coproscope.modules._pont_actes_source",
    "coproscope.modules._pont_actes_lignes",
    "coproscope.modules._pont_actes_liens",
    "coproscope.modules.pont_actes",
)

_PREFIXE = "coproscope.modules._pont_actes"
_ENTIER = "coproscope.modules.pont_actes"


class ChaqueModuleDuPontSImporteSeulTests(unittest.TestCase):
    def test_chacun_s_importe_sans_qu_un_autre_l_amorce(self) -> None:
        """Un `import` isole, hors de tout ordre etabli par un autre module.

        On vide les modules du pont de `sys.modules` avant chaque essai: dans
        l'interprete courant ils sont deja tous charges, et un cycle ne se voit
        plus. Pas de sous-processus: le garde-fou d'injection de code les
        refuse dans les tests, a juste titre.
        """
        for nom in MODULES:
            with self.subTest(module=nom):
                sauvegarde = {
                    cle: mod for cle, mod in sys.modules.items()
                    if cle.startswith(_PREFIXE) or cle == _ENTIER
                }
                for cle in sauvegarde:
                    del sys.modules[cle]
                try:
                    importlib.import_module(nom)
                except ImportError as exc:
                    self.fail(
                        "\n\n  `import " + nom + "` echoue quand il est le "
                        "premier charge.\n"
                        "  C'est un cycle d'import: il ne se verra pas dans la "
                        "suite complete,\n"
                        "  parce qu'un autre module l'amorce dans le bon "
                        "ordre.\n\n"
                        "  " + str(exc) + "\n"
                    )
                finally:
                    sys.modules.update(sauvegarde)


class LesAnnotationsDuPontSontResolvablesTests(unittest.TestCase):
    def test_les_signatures_publiques_se_resolvent(self) -> None:
        for nom in MODULES:
            module = importlib.import_module(nom)
            for attribut in dir(module):
                if attribut.startswith("_"):
                    continue
                objet = getattr(module, attribut)
                if not callable(objet):
                    continue
                if getattr(objet, "__module__", "") != nom:
                    continue
                with self.subTest(fonction=nom + "." + attribut):
                    try:
                        typing.get_type_hints(objet)
                    except NameError as exc:
                        self.fail(
                            nom + "." + attribut
                            + " est annote avec un nom jamais importe: "
                            + str(exc)
                        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
