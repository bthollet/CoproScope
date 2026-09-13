# -*- coding: utf-8 -*-
"""Le controle de confidentialite regarde CE QUE LE PUSH ENVOIE.

**Le garde-fou existait, il etait actif, il s'executait - et il regardait
ailleurs.** `tools/verifier_avant_push.py` annoncait son axe correctement, puis
posait le long de cet axe un invariant faux: *ce que `git push` envoie est
exactement ce que Git suit*. Il controlait donc `git ls-files`, c'est-a-dire
l'arbre courant.

**Deux contre-exemples mesures le 2026-09-12 sur ce depot, tous deux
atteignables aujourd'hui:**

1. `git push origin main` depuis une autre branche. `git ls-files` rend l'arbre
   COURANT; la reference poussee n'est jamais lue. `main` portait 41 constats,
   la branche courante zero, et le controle repondait *aucun constat*.
2. **Un nom efface dans un commit reste entierement lisible dans le precedent,
   et un push publie les deux.** L'arbre peut donc etre propre pendant que
   l'historique ne l'est pas - c'etait exactement l'etat de la branche: 0
   constat sur l'arbre, 44 sur ce que son push aurait envoye.

Le depot etant PUBLIC, ce n'etait pas une precaution theorique.

----------------------------------------------------------------------
Pourquoi ces tests fabriquent un depot au lieu de mesurer celui-ci
----------------------------------------------------------------------

Une garde qui compterait les constats du depot reel mesurerait **l'etat du
jour**: elle passerait au vert le jour ou quelqu'un nettoie, et elle ne dirait
jamais si l'INSTRUMENT sait voir. Elle tomberait aussi le jour ou un autre lot
commite un nom, en accusant ce fichier-ci.

Ces tests construisent donc un depot minuscule ou **la reponse est connue
d'avance**, avec un terme fabrique qui n'existe nulle part ailleurs. Le cas
central reproduit le defaut: l'arbre est PROPRE, l'historique est SALE. Un
instrument qui ne distingue pas les deux rend le meme verdict aux deux, et
c'est ce que le depot a paye.

Le temoin inverse compte autant: sur un depot sans aucun terme, les deux modes
doivent rendre ZERO. Sans lui, une garde qui crie toujours passerait pour une
garde qui voit.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

DEPOT = Path(__file__).resolve().parents[2]
OUTIL = DEPOT / "tools" / "verifier_avant_push.py"

#: Un terme qui n'existe dans aucun fichier de ce depot, et qui ne ressemble a
#: rien de reel. La garde ne doit JAMAIS avoir besoin d'un terme veritable.
FABRIQUE = "ZZTERMEFABRIQUE"


def _outil():
    spec = importlib.util.spec_from_file_location("_verif_sous_test", OUTIL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _git(dossier: Path, *arguments: str) -> str:
    p = subprocess.run(("git",) + arguments, cwd=str(dossier), check=True,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return p.stdout.strip()


def _depot_neuf(dossier: Path) -> None:
    _git(dossier, "init", "-q")
    _git(dossier, "config", "user.email", "garde@exemple.invalid")
    _git(dossier, "config", "user.name", "garde")
    _git(dossier, "config", "commit.gpgsign", "false")


def _commit(dossier: Path, message: str) -> None:
    _git(dossier, "add", "-A")
    _git(dossier, "commit", "-q", "-m", message)


class L_ARBRE_PROPRE_NE_PROUVE_PAS_UN_HISTORIQUE_PROPRE(unittest.TestCase):
    """Le cas central, et c'est celui qui mentait."""

    def _fabrique(self, dossier: Path) -> tuple[object, list[str], str]:
        """Un depot ou le terme a ete efface par un second commit."""
        _depot_neuf(dossier)
        (dossier / "note.md").write_text(
            "le dossier %s porte les pieces\n" % FABRIQUE, encoding="utf-8")
        _commit(dossier, "premier: le nom est la")
        (dossier / "note.md").write_text(
            "le dossier `Tilleuls (pseudo)` porte les pieces\n", encoding="utf-8")
        _commit(dossier, "second: le nom est pseudonymise")

        outil = _outil()
        outil.DEPOT = dossier
        return outil, [FABRIQUE], _git(dossier, "rev-parse", "HEAD")

    def test_le_mode_ARBRE_ne_voit_rien_et_c_est_exact(self) -> None:
        """L'arbre EST propre: ce mode a raison, et c'est le piege.

        Son verdict est juste pour la question qu'il pose - *qu'est-ce que je
        suis en train de commiter*. Il etait faux comme reponse a *qu'est-ce
        que ce push va publier*, et c'est a cette seconde question que le
        crochet `pre-push` le posait.
        """
        with TemporaryDirectory() as brut:
            outil, termes, _ = self._fabrique(Path(brut))
            constats, _, _ = outil.controler(None, termes)
        self.assertEqual(
            [], constats,
            "l'arbre fabrique est pseudonymise: un constat ici voudrait dire "
            "que le temoin lui-meme est mal construit")

    def test_le_mode_PUSH_le_voit_et_nomme_le_fichier(self) -> None:
        with TemporaryDirectory() as brut:
            outil, termes, tete = self._fabrique(Path(brut))
            constats, lus = outil.controler_le_push("origin", [tete], termes)

        self.assertTrue(
            constats,
            "le controle ne voit RIEN dans ce que le push enverrait, alors que "
            "le premier commit publie le terme en clair. C'est le defaut "
            "mesure le 2026-09-12: l'arbre propre passait pour une preuve.")
        self.assertTrue(any("note.md" in c for c in constats), constats)
        self.assertTrue(any("version" in c for c in constats), constats)
        self.assertGreater(lus, 0, "aucun blob lu: l'instrument mesure le vide")

    def test_il_ne_recopie_JAMAIS_le_terme_dans_son_constat(self) -> None:
        """Un rapport de fuite qui recopie la fuite est une fuite."""
        with TemporaryDirectory() as brut:
            outil, termes, tete = self._fabrique(Path(brut))
            constats, _ = outil.controler_le_push("origin", [tete], termes)
        for c in constats:
            self.assertNotIn(FABRIQUE, c, "le constat recopie le terme cherche")


class LE_NOM_D_UN_FICHIER_EST_PUBLIE_COMME_SON_CONTENU(unittest.TestCase):
    """Trouve en livrant, et aucun controle de CONTENU ne peut le voir.

    `main` porte le terme dans le nom d'un dossier d'images. Les binaires ne
    sont jamais lus - a juste titre - donc leur nom est la seule chose qui les
    trahit, et c'etait le seul endroit que rien ne regardait.
    """

    def _fabrique_un_nom(self, dossier: Path) -> tuple[object, list[str], str]:
        _depot_neuf(dossier)
        (dossier / ("piece-%s-2026.bin" % FABRIQUE)).write_bytes(b"\x00\x01\x02")
        _commit(dossier, "un binaire dont le NOM porte le terme")
        outil = _outil()
        outil.DEPOT = dossier
        return outil, [FABRIQUE], _git(dossier, "rev-parse", "HEAD")

    def test_le_mode_PUSH_nomme_le_fichier_par_son_NOM(self) -> None:
        with TemporaryDirectory() as brut:
            outil, termes, tete = self._fabrique_un_nom(Path(brut))
            constats, _ = outil.controler_le_push("origin", [tete], termes)
        self.assertTrue(any("NOM DU FICHIER" in c for c in constats), constats)
        for c in constats:
            self.assertNotIn(FABRIQUE, c)

    def test_le_mode_ARBRE_le_voit_AUSSI(self) -> None:
        """Le meme trou existait dans le mode arbre: il ne lisait que du texte."""
        with TemporaryDirectory() as brut:
            outil, termes, _ = self._fabrique_un_nom(Path(brut))
            constats, _, _ = outil.controler(None, termes)
        self.assertTrue(any("NOM DU FICHIER" in c for c in constats), constats)


class LE_TEMOIN_INVERSE_ET_LES_CAS_LIMITES(unittest.TestCase):
    """Sans eux, une garde qui refuse tout passerait pour une garde qui voit."""

    def test_un_depot_SANS_AUCUN_TERME_rend_zero_dans_les_deux_modes(self) -> None:
        with TemporaryDirectory() as brut:
            dossier = Path(brut)
            _depot_neuf(dossier)
            (dossier / "note.md").write_text(
                "le dossier `Tilleuls (pseudo)` porte les pieces\n",
                encoding="utf-8")
            _commit(dossier, "rien a cacher")
            outil = _outil()
            outil.DEPOT = dossier
            tete = _git(dossier, "rev-parse", "HEAD")
            pousse, lus = outil.controler_le_push("origin", [tete], [FABRIQUE])
            arbre, _, _ = outil.controler(None, [FABRIQUE])
        self.assertEqual([], pousse, "l'instrument crie sur un depot propre")
        self.assertEqual([], arbre)
        self.assertGreater(lus, 0, "zero blob lu: l'instrument n'a rien regarde, "
                                   "et son zero ne prouve donc rien")

    def test_une_SUPPRESSION_de_reference_n_envoie_aucun_objet(self) -> None:
        """Une empreinte tout a zero cote local: rien ne part, rien a lire."""
        with TemporaryDirectory() as brut:
            dossier = Path(brut)
            _depot_neuf(dossier)
            (dossier / "note.md").write_text("%s\n" % FABRIQUE, encoding="utf-8")
            _commit(dossier, "le terme est la")
            outil = _outil()
            outil.DEPOT = dossier
            constats, _ = outil.controler_le_push("origin", ["0" * 40], [FABRIQUE])
        self.assertEqual([], constats,
                         "une suppression de reference ne publie rien, et le "
                         "controle ne doit pas la refuser")

    def test_une_ENTREE_VIDE_rend_le_code_DEUX_et_non_zero(self) -> None:
        """*Pas regarde* n'est pas *rien trouve*, et le crochet doit refuser.

        `main` lit `sys.stdin`: on l'appelle donc en sous-processus, seule
        facon de lui donner une entree REELLEMENT vide - ce qu'un `StringIO`
        ne reproduit pas depuis ce processus de test.
        """
        with TemporaryDirectory() as brut:
            termes = Path(brut) / "termes.txt"
            termes.write_text("%s\n" % FABRIQUE, encoding="utf-8")
            p = subprocess.run(
                [sys.executable, str(OUTIL), "--pousse", "origin"],
                cwd=str(DEPOT), input="", capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                env={"PATH": "", "SYSTEMROOT": "", "PYTHONIOENCODING": "utf-8",
                     "COPROSCOPE_NOMS_INTERDITS": str(termes)})
        self.assertEqual(2, p.returncode, p.stdout + p.stderr)
        self.assertIn("CONTROLE IMPOSSIBLE", p.stderr)
        self.assertIn("RIEN N'A ETE CONTROLE", p.stderr)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
