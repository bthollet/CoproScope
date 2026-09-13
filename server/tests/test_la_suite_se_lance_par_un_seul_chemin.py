# -*- coding: utf-8 -*-
"""La suite complete se lance par UN chemin, et c'est le lanceur canonique.

`RM-2026-0173`. Sur le MEME arbre, au meme moment, deux invocations donnaient
deux reponses: la decouverte en processus jouait 2 533 tests et sortait sur 0;
`python -m unittest discover -s tests` en jouait **environ 330 de moins** et
sortait sur **1 pendant qu'unittest imprimait `OK`**. Ce n'est pas le produit
qui variait, c'est l'invocation - elle place `server/tests` en tete de
`sys.path` et change le nom d'import des modules.

**Pourquoi cette garde existe, et elle vient d'un refus.** Le correctif -
`tools/lancer_la_suite.py` - avait ete livre le 2026-09-10 au matin. La revue
d'integration du meme jour l'a **refuse**: le fichier existait et **n'etait
adopte nulle part**, ni dans `agent-check`, ni dans la CI. Le defaut restait
donc atteignable par le chemin exact que le depot prescrit a ses agents.
**Livrer un correctif et l'adopter sont deux choses**, et seule la seconde
ferme un defaut.

**L'axe.** Ce qui varie: l'endroit d'ou l'on lance, l'outil qui lance, les
options passees. Ce qui reste invariant: **une suite doit avoir une seule
maniere d'etre jouee, sans quoi son verdict ne designe rien.** La garde porte
donc sur les LANCEURS DU DEPOT, pas sur une ligne de commande particuliere.

**Ce que cette garde ne fait pas.** Elle n'interdit a personne de taper
`python -m unittest` a la main pour un module isole - le `CLAUDE.md` le
recommande meme pour un chemin rapide. Elle porte sur les deux endroits qui
pretendent jouer la suite COMPLETE et dont le verdict est cite comme preuve.
"""

from __future__ import annotations

import importlib.util
import io
import os
import re
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

DEPOT = Path(__file__).resolve().parents[2]
LANCEUR = DEPOT / "tools" / "lancer_la_suite.py"

#: Les deux endroits qui jouent la suite COMPLETE et dont le verdict fait
#: preuve. Ils sont nommes, parce qu'ils sont deux et qu'on veut les deux;
#: un troisieme qui apparaitrait sans etre ajoute ici ne serait pas garde, et
#: c'est la limite declaree de cette liste.
LANCEURS_DE_SUITE_COMPLETE = (
    Path("tools") / "agent-check.ps1",
    Path(".github") / "workflows" / "ci.yml",
)

#: L'invocation refutee. La comparaison porte sur la SUITE `discover -s tests`
#: quels que soient les blancs: c'est elle qui deplace `sys.path`, et non le
#: mot `unittest`, qui apparait legitimement ailleurs.
INVOCATION_REFUTEE = re.compile(r"discover\W+-s\W+tests", re.IGNORECASE)


class LE_LANCEUR_CANONIQUE_EXISTE(unittest.TestCase):
    """Temoin de sante: sans lui, tout ce qui suit garderait le vide."""

    def test_le_fichier_est_la(self) -> None:
        self.assertTrue(LANCEUR.is_file(), "%s a disparu" % LANCEUR)

    def test_il_nomme_les_tests_collectes_et_jamais_demarres(self) -> None:
        """Un saut pose au niveau d'une classe appelle `addSkip` sans passer
        par `startTest`: ces tests n'apparaissent dans aucun compteur."""
        source = LANCEUR.read_text(encoding="utf-8")
        self.assertIn("absents", source)
        self.assertIn("startTest", source)


#: Deux modules de test fabriques, identiques en tout sauf leur RESULTAT.
#: C'est cette seule difference qui doit faire bouger le code du lanceur.
_QUI_PASSE = (
    "import unittest\n"
    "class Passe(unittest.TestCase):\n"
    "    def test_passe(self):\n"
    "        self.assertTrue(True)\n"
)
_QUI_ECHOUE = (
    "import unittest\n"
    "class Echoue(unittest.TestCase):\n"
    "    def test_echoue(self):\n"
    "        self.fail('echec fabrique pour mesurer le verdict du lanceur')\n"
)


class LE_VERDICT_DEPEND_REELLEMENT_DE_CE_QUI_A_ETE_JOUE(unittest.TestCase):
    """**Troisieme ecriture de cette garde, et les deux premieres mesuraient
    une FORME.**

    - La premiere cherchait la chaine `resultat.wasSuccessful()` dans le
      fichier. Elle y apparaissait deux fois - le code de sortie et la ligne
      imprimee - donc remplacer le retour par un `return 0` nu laissait la
      garde verte pendant que le lanceur certifiait le succes quoi qu'il
      arrive.
    - La seconde, du 2026-09-11, lisait l'AST et exigeait qu'un `return` de
      `main` MENTIONNE `wasSuccessful`. Plus fine, mais toujours une forme:
      **elle a mordu le 2026-09-12 sur une reparation qui renforcait
      precisement la propriete qu'elle croyait garder.** `RM-2026-0171` a
      deplace la decision dans une fonction `verdict(collectes, demarres,
      absents, succes)` et fait rendre a `main` la valeur qu'elle decide; la
      dependance existait toujours, mais par une variable, et la garde ne
      voyait plus le mot.

    **La forme du retour est un degre de liberte; ce qui reste invariant est
    la DEPENDANCE.** Cette garde la mesure donc par le point d'entree: deux
    dossiers identiques, un seul test dedans, et la seule difference est que
    ce test passe ou echoue. Si le code rendu ne bouge pas, le lanceur ne lit
    pas le resultat de ce qu'il a joue - quelle que soit la facon dont il
    l'ecrit.

    **Quand cette garde cessera-t-elle d'etre vraie, et comment l'apprendra-t-on ?**
    Au premier passage ou le lanceur rendrait un code constant. Les deux tests
    se tiennent par les deux bouts: l'un refuse un `return 1` fixe, l'autre un
    `return 0` fixe. Aucun des deux seul ne suffit, et c'est voulu.
    """

    def _main_sur(self, fichiers: dict[str, str]) -> tuple[int, str]:
        """Joue `main` sur un dossier fabrique, et rend `(code, journal)`.

        Le lanceur est charge par son CHEMIN: `tools/` n'est pas un paquet
        importable depuis la suite. `main` recoit son parametre `dossier`, la
        couture ouverte par `RM-2026-0171` pour que ses gardes l'appellent
        lui-meme au lieu de recopier sa logique.
        """
        spec = importlib.util.spec_from_file_location("_lanceur_mesure", LANCEUR)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        # `main` fait `os.chdir`, et `discover` insere le dossier decouvert
        # dans `sys.path` puis y importe des modules. On rend les trois etats
        # tels qu'on les a trouves: une garde qui laisse un `sys.modules` sali
        # deplace le resultat des tests joues apres elle.
        cwd, chemins, modules = os.getcwd(), list(sys.path), set(sys.modules)
        try:
            with TemporaryDirectory() as dossier:
                for nom, source in fichiers.items():
                    (Path(dossier) / nom).write_text(source, encoding="utf-8")
                journal = io.StringIO()
                with redirect_stdout(journal), redirect_stderr(io.StringIO()):
                    code = module.main([], dossier=dossier)
                return code, journal.getvalue()
        finally:
            os.chdir(cwd)
            sys.path[:] = chemins
            for nom in set(sys.modules) - modules:
                del sys.modules[nom]

    def test_un_test_qui_PASSE_rend_un_code_nul_et_le_verdict_OK(self) -> None:
        code, journal = self._main_sur({"test_passe_fabrique.py": _QUI_PASSE})
        self.assertEqual(
            0, code,
            "un dossier dont le seul test PASSE fait rendre au lanceur un "
            "code d'echec: son verdict ne suit pas ce qu'il a joue")
        self.assertIn("verdict   : OK", journal)
        self.assertIn("demarres  : 1", journal,
                      "le lanceur n'annonce pas avoir demarre le test qu'il "
                      "a pourtant joue")

    def test_un_test_qui_ECHOUE_rend_un_code_non_nul_et_le_verdict_ECHEC(self) -> None:
        code, journal = self._main_sur({"test_echoue_fabrique.py": _QUI_ECHOUE})
        self.assertNotEqual(
            0, code,
            "un dossier dont le seul test ECHOUE fait rendre au lanceur un "
            "code de succes: c'est exactement le defaut que ce fichier "
            "existe pour empecher, et il serait invisible dans tous les "
            "`BOT-END` du depot")
        self.assertIn("ECHEC", journal)

    def test_les_deux_cas_ne_rendent_PAS_le_meme_code(self) -> None:
        """La dependance elle-meme, enoncee sans passer par une valeur attendue.

        Les deux tests ci-dessus comparent a `0`. Celui-ci ne compare a rien
        de connu: il verifie seulement que **le resultat des tests joues
        change la reponse du lanceur**. C'est la propriete, debarrassee de la
        convention de codes.
        """
        passe, _ = self._main_sur({"test_passe_fabrique.py": _QUI_PASSE})
        echoue, _ = self._main_sur({"test_echoue_fabrique.py": _QUI_ECHOUE})
        self.assertNotEqual(
            passe, echoue,
            "le lanceur rend le meme code que ses tests passent ou echouent: "
            "son verdict est une constante deguisee")


class LES_DEUX_LANCEURS_DU_DEPOT_L_ADOPTENT(unittest.TestCase):
    """Le refus du 2026-09-10 portait exactement la-dessus."""

    def test_chacun_existe(self) -> None:
        for relatif in LANCEURS_DE_SUITE_COMPLETE:
            with self.subTest(fichier=str(relatif)):
                self.assertTrue((DEPOT / relatif).is_file())

    def test_chacun_appelle_le_lanceur_canonique(self) -> None:
        for relatif in LANCEURS_DE_SUITE_COMPLETE:
            with self.subTest(fichier=str(relatif)):
                texte = (DEPOT / relatif).read_text(encoding="utf-8")
                self.assertIn(
                    "lancer_la_suite.py", texte,
                    "%s joue la suite complete sans passer par le lanceur "
                    "canonique: son verdict ne designe rien" % relatif)

    def test_aucun_ne_porte_plus_l_invocation_REFUTEE(self) -> None:
        """`discover -s tests` joue environ 330 tests de moins, en silence."""
        for relatif in LANCEURS_DE_SUITE_COMPLETE:
            with self.subTest(fichier=str(relatif)):
                texte = (DEPOT / relatif).read_text(encoding="utf-8")
                # Les commentaires CITENT l'invocation pour expliquer pourquoi
                # elle a ete retiree. On ne mesure donc que les lignes de
                # COMMANDE - c'est la lecon du matin: une garde qui cherche le
                # motif dans un texte explicatif attrape la mention, pas le
                # motif.
                commandes = [
                    ligne for ligne in texte.splitlines()
                    if not ligne.lstrip().startswith(("#", "//"))
                ]
                trouve = [l for l in commandes if INVOCATION_REFUTEE.search(l)]
                self.assertEqual(
                    [], trouve,
                    "%s lance encore la suite par l'invocation refutee" % relatif)


class LA_DOCTRINE_PRESCRIT_LE_MEME_CHEMIN(unittest.TestCase):
    """**Le dernier endroit qui disait encore de faire autrement.**

    Le 2026-09-11, `agent-check` et la CI appelaient deja le lanceur canonique -
    et `CLAUDE.md`, la consigne que tout agent lit avant de travailler,
    prescrivait toujours `-m unittest discover -s tests` a l'etape
    d'integration, sans mentionner le lanceur une seule fois. **Corriger les
    outils sans corriger la consigne laisse le defaut atteignable par le chemin
    que le depot enseigne.**

    **La garde distingue une COMMANDE d'une MENTION**, et cette distinction est
    tout l'interet. La consigne cite maintenant l'invocation refutee en prose,
    pour expliquer pourquoi elle a ete retiree; l'interdire partout ferait
    echouer la garde sur sa propre explication - le defaut attrape le matin
    meme sur une autre garde, qui cherchait `except Exception` dans une
    docstring qui racontait son retrait. **En markdown, une commande vit dans un
    bloc de code.** La garde ne lit donc que ces blocs.
    """

    DOCTRINE = DEPOT / "CLAUDE.md"

    def _blocs_de_code(self) -> list[str]:
        lignes = self.DOCTRINE.read_text(encoding="utf-8").splitlines()
        blocs, dedans = [], False
        for ligne in lignes:
            if ligne.lstrip().startswith("```"):
                dedans = not dedans
                continue
            if dedans:
                blocs.append(ligne)
        return blocs

    def test_la_doctrine_NOMME_le_lanceur_canonique(self) -> None:
        texte = self.DOCTRINE.read_text(encoding="utf-8")
        self.assertIn(
            "lancer_la_suite.py", texte,
            "la consigne que tout agent lit ne nomme pas le lanceur de la suite")

    def test_aucune_COMMANDE_de_la_doctrine_ne_porte_l_invocation_refutee(self) -> None:
        fautives = [l for l in self._blocs_de_code() if INVOCATION_REFUTEE.search(l)]
        self.assertEqual(
            [], fautives,
            "la doctrine prescrit encore l'invocation qui joue 330 tests de moins")

    def test_la_garde_lit_bien_les_blocs_de_code_et_pas_la_prose(self) -> None:
        """Temoin de sante: sans cela, les deux tests ci-dessus pourraient
        passer parce qu'ils ne lisent rien du tout."""
        blocs = self._blocs_de_code()
        self.assertTrue(blocs, "aucun bloc de code lu dans la doctrine")
        self.assertTrue(
            any("lancer_la_suite.py" in l for l in blocs),
            "le lanceur doit etre donne comme une COMMANDE, pas seulement cite")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
