# -*- coding: utf-8 -*-
"""Une seule facon de jouer la suite, et un verdict qui dit ce qu'il a joue.

**Le fait qui impose cet outil, mesure le 2026-09-10** (`RM-2026-0173`). Sur le
MEME arbre, au meme moment, trois facons de lancer la suite donnent trois
reponses:

| comment                                   | joues | code |
|-------------------------------------------|------:|-----:|
| decouverte en processus (ce fichier)       | 2 533 |    0 |
| `python -m unittest discover -s tests`     | 2 201 |    1 |
| `... discover -s tests -t .`               |     - |    1 |

La troisieme refuse net: *Start directory is not importable* - `server/tests`
n'a pas d'`__init__.py`, donc il ne peut pas etre un paquet sous une racine plus
haute. La deuxieme joue **environ 330 tests de moins** et **sort sur 1 alors
qu'`unittest` imprime `OK`**.

**Ce n'est donc pas le produit qui varie: c'est l'invocation.** Le `CLAUDE.md`
mettait deja en garde - *ce depot joue ses tests de DEUX facons* - mais decrivait
un piege d'import sur quelques modules. Il pese en realite un tiers de la suite
et un code de sortie d'echec.

**Ce que cet outil garantit, et c'est tout ce qu'on lui demande:**

1. **une seule invocation**, donc un seul chiffre a citer dans un `BOT-END`;
2. **le verdict est lu de `unittest` lui-meme**, jamais d'un code de sortie
   compose - le depot a deja paye ce defaut;
3. **les tests collectes et jamais DEMARRES sont NOMMES**, pas seulement
   comptes. Un saut pose au niveau d'une classe appelle `addSkip` sans passer
   par `startTest`: ces tests n'apparaissent nulle part ailleurs.

**Ce qu'il ne fait pas.** Il ne remplace pas `agent-check`, qui joue un chemin
rapide et des controles de securite. Il repond a une seule question: *qu'est-ce
que la suite complete a REELLEMENT joue, et avec quel verdict*.
"""

from __future__ import annotations

import os
import sys
import unittest
from collections import Counter
from pathlib import Path


#: Le dossier des tests, relatif a la racine du depot. Il n'est pas un paquet -
#: pas d'`__init__.py` - et c'est ce qui interdit `-t .`.
DOSSIER_TESTS = "tests"


class _Journal(unittest.TextTestResult):
    """Un resultat qui retient ce qu'il a demarre.

    `startTest` est le seul point ou `unittest` annonce qu'un test COMMENCE.
    Tout ce qui est collecte sans passer par la n'a jamais tourne, et ne se voit
    dans aucun compteur standard.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.demarres: list[str] = []

    def startTest(self, test) -> None:  # noqa: N802 - nom impose par unittest
        self.demarres.append(test.id())
        super().startTest(test)


def _identifiants(suite) -> list[str]:
    for element in suite:
        if isinstance(element, unittest.TestSuite):
            yield from _identifiants(element)
        else:
            yield element.id()


def verdict(collectes: int, demarres: int, absents: int, succes: bool) -> tuple[str, int]:
    """Le verdict, et il ne repose PAS sur le seul `wasSuccessful()`.

    **Le defaut repare le 2026-09-12, mesure et non deduit.** Ce fichier
    imprimait `'OK' if resultat.wasSuccessful() else 'ECHEC'` et rendait le code
    correspondant. Or **`wasSuccessful()` vaut `True` quand ZERO test n'a
    tourne**: sans echec ni erreur, la methode ne distingue pas *tout est passe*
    de *rien n'a ete joue*. Sonde du 2026-09-12 sur une suite vide:
    `testsRun = 0`, `wasSuccessful() = True`, donc **`verdict : OK` et code
    `0`**.

    C'est le pire endroit possible pour ce defaut: chaque verdict publie par ce
    depot passe par ici, et l'en-tete de ce fichier promet precisement *un
    verdict qui dit ce qu'il a joue*. Il comptait `demarres`, il l'imprimait, et
    **il ne s'en servait pas**.

    Les trois regles, et ce qu'elles refusent de confondre:

    - **rien de collecte** -> `ECHEC`. Une collecte vide n'est pas une suite
      saine, c'est une suite introuvable.
    - **rien de demarre** -> `ECHEC`, meme si la collecte a rendu des noms:
      c'est le cas ou tout aurait ete saute, et le silence y ressemble a un
      succes.
    - **des absents** -> ce n'est **pas** un echec en soi. Un saut pose au
      niveau d'une classe appelle `addSkip` sans passer par `startTest`, et
      c'est legitime; l'etat observe ce jour-la est `6 absents` avec verdict
      `OK`. Mais le libelle **porte le compte**, pour qu'un absent ne se lise
      jamais comme un test passe.
    """
    if collectes == 0:
        return "ECHEC - aucun test COLLECTE: la suite est introuvable", 3
    if demarres == 0:
        return ("ECHEC - aucun test DEMARRE sur %d collectes: rien n'a ete joue, "
                "et `wasSuccessful()` seul aurait dit OK" % collectes), 4
    if not succes:
        return "ECHEC", 1
    if absents:
        return ("OK, mais %d test(s) collecte(s) n'ont JAMAIS demarre - "
                "nommes ci-dessus" % absents), 0
    return "OK", 0


def main(argv: list[str], dossier: str = DOSSIER_TESTS) -> int:
    racine = Path(__file__).resolve().parents[1] / "server"
    # **On se place DANS `server`, et on decouvre le chemin relatif `tests`.**
    # C'est la seule combinaison qui marche, et il a fallu la mesurer:
    #   - `top_level_dir=server` -> `ImportError: Start directory is not
    #     importable`, parce que `server/tests` n'a pas d'`__init__.py`;
    #   - `python -m unittest discover -s tests` -> place `server/tests` en
    #     tete de `sys.path`, et joue environ 330 tests de moins.
    # Ici, `sys.path` porte `server` et `server/src`, le repertoire courant est
    # `server`, et la racine de plus haut niveau reste implicite.
    os.chdir(racine)
    for chemin in (str(racine / "src"), str(racine)):
        if chemin not in sys.path:
            sys.path.insert(0, chemin)

    chargeur = unittest.TestLoader()
    # `dossier` est un parametre, et ce n'est pas de la souplesse gratuite: la
    # garde de ce fichier appelle `main` LUI-MEME sur un dossier sans test, au
    # lieu de reimplementer sa logique. Sans cette couture, la garde testerait
    # une copie du verdict et le CABLAGE resterait non mesure - c'est exactement
    # le reproche qui a fait naitre ce lot.
    suite = chargeur.discover(dossier)
    collectes = list(_identifiants(suite))

    if chargeur.errors:
        print("ERREURS DE CHARGEMENT - la collecte est incomplete:", file=sys.stderr)
        for erreur in chargeur.errors:
            print("  " + str(erreur)[:400], file=sys.stderr)
        return 2

    verbosite = 2 if "-v" in argv else 1
    lanceur = unittest.TextTestRunner(resultclass=_Journal, verbosity=verbosite)
    resultat = lanceur.run(suite)

    demarres = set(resultat.demarres)
    absents = [identifiant for identifiant in collectes if identifiant not in demarres]

    print()
    print("=" * 70)
    print(f"collectes : {len(collectes)}")
    print(f"demarres  : {len(resultat.demarres)}")
    print(f"absents   : {len(absents)}")
    if absents:
        print()
        print("Collectes mais JAMAIS demarres - typiquement un saut pose au niveau")
        print("d'une classe, qui appelle `addSkip` sans passer par `startTest`:")
        for module, combien in Counter(i.rsplit(".", 2)[0] for i in absents).most_common():
            print(f"   {combien:5}  {module}")
    libelle, code = verdict(len(collectes), len(resultat.demarres),
                            len(absents), resultat.wasSuccessful())
    print(f"verdict   : {libelle}")
    print("=" * 70)
    return code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
