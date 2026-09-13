# -*- coding: utf-8 -*-
"""Un test qui lit un etat hors de l'arbre de travail rend le vert illusoire.

`RM-2026-0174`, cause trouvee le 2026-09-11. L'item constatait que
`test_drive_real_sync_blocks_public_google_folder_without_upload` **echouait
dans une suite complete de 2 601 tests puis passait dans une autre**, sans
qu'une ligne du code Drive ait change - et declarait la cause non cherchee,
*parce que trouver le test qui laisse l'etat demande une bissection de la suite
complete, soit plusieurs passages de quatorze minutes*.

**Aucune bissection n'etait necessaire: la cause est dans le code.**
`drive_local_setup._local_base` et `_profile_root` retombent, quand leurs
variables d'environnement sont absentes, sur `%LOCALAPPDATA%/CoproScope/coffres`
et `%APPDATA%/CoproScope` - **des chemins du POSTE, hors de l'arbre de travail,
qui survivent d'une execution de la suite a l'autre**. Mesure: le profil
`%APPDATA%/CoproScope` **existe** sur ce poste.

**Un seul test du fichier posait ces deux variables**, dans un `try/finally`
qui les RESTAURE ensuite; les neuf autres lisaient donc le profil reel, et
l'ordre d'execution decidait de la branche prise. L'echec observe - `Droits
Google a verifier` au lieu de `a corriger` - n'etait pas un libelle qui avait
bouge: c'etait un POST arrete plus tot, faute de surface chiffree locale.

**C'EST LE MOTIF QUE CE DEPOT A DEJA PAYE TROIS FOIS**, et sa doctrine le dit:
le `.pth` du venv qui testait l'arbre principal depuis un worktree, le code de
sortie lu a travers un pipe, le module qui passait seul pendant que la suite
cassait. **Un test qui echoue une fois sur deux fait pire que rater un defaut:
il apprend a ne pas croire le rouge.**

**L'AXE.** Ce qui VARIE: le systeme, les variables d'environnement, l'ordre des
tests, ce qu'un passage precedent a laisse. Ce qui reste INVARIANT: **un test ne
mesure que ce qu'il a lui-meme mis en place.** Tout etat qu'il lit sans l'avoir
pose est un parametre cache de sa mesure.

**Ce que cette garde fait.** Elle verifie que les modules qui resolvent une
racine hors de l'arbre le font **par une variable d'environnement**, et que les
tests qui les exercent posent cette variable. Elle ne verifie pas l'absence
d'acces disque - ce serait une autre mesure, et elle demanderait un instrument.
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
TESTS = DEPOT / "server/tests"
SRC = DEPOT / "server/src/coproscope"

#: Les racines hors arbre que le produit sait resoudre, et la variable qui doit
#: pouvoir les deplacer. Une racine sans variable serait indeplaceable, donc
#: impossible a isoler dans un test.
RACINES_HORS_ARBRE = {
    "modules/drive_local_setup.py": (
        "COPROSCOPE_DRIVE_LOCAL_ROOT", "COPROSCOPE_DRIVE_PROFILE_ROOT"),
}

#: Les variables d'environnement du poste dont un repli hors arbre depend.
VARIABLES_DU_POSTE = ("LOCALAPPDATA", "APPDATA")


class UNE_RACINE_HORS_ARBRE_EST_TOUJOURS_DEPLACABLE(unittest.TestCase):
    """Sinon aucun test ne peut l'isoler, et tous mesurent le poste."""

    def test_chaque_module_declare_sa_variable_de_deplacement(self) -> None:
        for relatif, variables in RACINES_HORS_ARBRE.items():
            source = (SRC / relatif).read_text(encoding="utf-8")
            for variable in variables:
                with self.subTest(module=relatif, variable=variable):
                    self.assertIn(
                        variable, source,
                        "ce module resout une racine hors de l'arbre sans "
                        "variable pour la deplacer: aucun test ne pourra "
                        "l'isoler, et tous mesureront le poste")

    def test_le_repli_sur_le_poste_est_bien_un_REPLI(self) -> None:
        """La variable doit etre lue AVANT le chemin du poste: l'inverse
        rendrait la variable inoperante."""
        for relatif, variables in RACINES_HORS_ARBRE.items():
            source = (SRC / relatif).read_text(encoding="utf-8")
            for variable in variables:
                with self.subTest(module=relatif, variable=variable):
                    for poste in VARIABLES_DU_POSTE:
                        if poste not in source:
                            continue
                        self.assertLess(
                            source.index(variable), source.rindex(poste),
                            "le chemin du poste est lu avant la variable de "
                            "deplacement: la variable ne sert plus a rien")


class LES_TESTS_QUI_EXERCENT_CES_RACINES_LES_POSENT(unittest.TestCase):
    """**Le coeur du lot.** Un test qui ne les pose pas lit le poste."""

    #: Les fichiers de test qui font agir un module a racine hors arbre.
    def _fichiers_concernes(self) -> list[Path]:
        concernes = []
        for chemin in sorted(TESTS.glob("test_*drive*.py")):
            texte = chemin.read_text(encoding="utf-8", errors="ignore")
            if "drive_local_setup" in texte or "drive_mvp" in texte:
                concernes.append(chemin)
        return concernes

    def test_des_fichiers_sont_bien_concernes(self) -> None:
        """Temoin de sante: sans cela, la garde passerait sur une liste vide."""
        self.assertTrue(self._fichiers_concernes())

    #: **Deux facons legitimes de deplacer une racine, et la garde accepte les
    #: deux.** Premiere version de ce test: elle n'acceptait que la variable
    #: d'environnement, et a signale `test_drive_local_setup.py` a tort - ce
    #: fichier passe `base_root=` et `profile_root=` en ARGUMENTS, ce qui isole
    #: tout aussi bien et plus explicitement. Ce qui compte est que la racine
    #: soit deplacee, pas la maniere dont elle l'est.
    MARQUES_D_ISOLEMENT = (
        "COPROSCOPE_DRIVE_LOCAL_ROOT", "COPROSCOPE_DRIVE_PROFILE_ROOT",
        "LOCAL_ROOT_ENV", "PROFILE_ENV",
        "base_root=", "profile_root=",
    )

    def test_chacun_deplace_ses_racines_d_une_facon_ou_d_une_autre(self) -> None:
        manquants = []
        for chemin in self._fichiers_concernes():
            texte = chemin.read_text(encoding="utf-8", errors="ignore")
            if not any(marque in texte for marque in self.MARQUES_D_ISOLEMENT):
                manquants.append(chemin.name)
        self.assertEqual(
            [], manquants,
            "ces tests exercent une racine hors arbre sans la deplacer - ni "
            "par variable d'environnement, ni par argument: ils lisent le "
            "profil REEL du poste, et leur vert depend de ce qu'un passage "
            "precedent y a laisse")

    def test_la_garde_reconnait_bien_les_DEUX_facons(self) -> None:
        """Temoin: sans cela, elle pourrait n'en reconnaitre aucune."""
        for marque in ("COPROSCOPE_DRIVE_PROFILE_ROOT", "profile_root="):
            with self.subTest(marque=marque):
                self.assertIn(marque, self.MARQUES_D_ISOLEMENT)


class LE_PROFIL_DU_POSTE_N_EST_PAS_TOUCHE_PENDANT_CE_TEST(unittest.TestCase):
    """**La mesure directe**, qui ne repose sur aucune lecture de source.

    Elle ne prouve pas qu'aucun test n'ecrit jamais hors de l'arbre - il
    faudrait un instrument. Elle etablit le fait qui a permis de trouver la
    cause: ce repli existe, il pointe vers le poste, et il est atteignable.
    """

    def test_le_repli_du_poste_est_bien_un_chemin_reel(self) -> None:
        from coproscope.modules import drive_local_setup

        ancien = {v: os.environ.pop(v, None)
                  for v in ("COPROSCOPE_DRIVE_PROFILE_ROOT",)}
        try:
            racine = drive_local_setup._profile_root(None)
        finally:
            for nom, valeur in ancien.items():
                if valeur is not None:
                    os.environ[nom] = valeur
        attendu = Path(os.environ.get("APPDATA") or Path.home()).resolve()
        self.assertTrue(
            str(racine).startswith(str(attendu)),
            "le repli ne pointe plus vers le profil du poste: remesurer, la "
            "cause de `RM-2026-0174` a peut-etre change de nature")

    def test_la_variable_le_deplace_vraiment(self) -> None:
        """Sans cela, poser la variable dans un `setUp` ne servirait a rien."""
        from coproscope.modules import drive_local_setup

        ailleurs = Path(__file__).resolve().parent / "_racine_qui_n_existe_pas"
        ancien = os.environ.get("COPROSCOPE_DRIVE_PROFILE_ROOT")
        os.environ["COPROSCOPE_DRIVE_PROFILE_ROOT"] = str(ailleurs)
        try:
            racine = drive_local_setup._profile_root(None)
        finally:
            if ancien is None:
                os.environ.pop("COPROSCOPE_DRIVE_PROFILE_ROOT", None)
            else:
                os.environ["COPROSCOPE_DRIVE_PROFILE_ROOT"] = ancien
        self.assertEqual(ailleurs.resolve(), racine)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
