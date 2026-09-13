# -*- coding: utf-8 -*-
"""Sans matiere, l'ecran ne montre rien - il n'invente pas une piece.

`RM-2026-0109`, point (1) de l'ordre d'instruction de Brice: *etablir par quel
chemin ce repli est servi, ou prouver qu'il est mort et le retirer*.

**Ce que le code faisait.** `piece_detail_view._live_contract_fallback_piece`
fabriquait une piece ENTIEREMENT INVENTEE - libelle *« Justificatif comptable -
attestation assurance immeuble recente »*, criticite `Critique`, motif redige,
boutons de demande et de depot - et la marquait `is_fictive: True`. **Ce drapeau
n'atteignait aucun gabarit**: pose trois fois dans le module, rendu zero fois
dans `web/templates/`. Le code savait que la piece etait fausse et ne le disait
nulle part.

**L'item declarait honnetement n'avoir pas reussi a la faire servir. La mesure
du 2026-09-11 leve cette reserve.** Cinq chemins HTTP essayes ne la servaient
pas - parce que sur l'instance d'exemple, l'identifiant privilegie est deja
porte par une VRAIE entree du modele, donc la recherche la trouve avant
d'atteindre le repli. Mais sur un modele **VIDE** - c'est-a-dire toute instance
dont le coffre est absent ou vide - `build_piece_detail` rendait `state:
found` avec `is_fictive: True`, tandis qu'un identifiant quelconque rendait
`missing`. **Le repli n'etait pas mort: il etait atteignable par le cas le plus
COURANT d'une instance mal configuree.**

**La regle appliquee est celle de Brice, et elle renverse le diagnostic
d'origine** - lequel posait le probleme comme *le chemin reel rend moins que son
repli*, en supposant que le repli riche etait la bonne reponse: **une instance
sans coffre doit afficher ZERO octet, parce que l'outillage est independant de
l'instance.** Ce qui etait en cause n'est pas la pauvrete du chemin reel, c'est
que le chemin sans coffre affiche quoi que ce soit.

**L'AXE.** Ce qui VARIE: l'etat de configuration d'une instance - coffre absent,
declare et vide, declare et plein. Ce qui reste INVARIANT: **un ecran sans
matiere le dit; il ne fabrique pas de matiere pour avoir quelque chose a
montrer.** Un identifiant privilegie dans le code est une modalite, pas un axe.
"""

from __future__ import annotations

import ast
import unittest
from contextlib import ExitStack
from pathlib import Path

from coproscope.web.piece_detail_view import (
    LIVE_CONTRACT_FALLBACK_ID,
    build_piece_detail,
)
from tests._exemple_copie import exemple_copie

DEPOT = Path(__file__).resolve().parents[2]
MODULE = DEPOT / "server/src/coproscope/web/piece_detail_view.py"


class _Socle(unittest.TestCase):
    """**L'instance est une COPIE, et ce n'est pas de la prudence de facade.**

    `RM-2026-0107`. Ce socle ouvrait l'instance versionnee sur place. Il n'y
    ecrivait rien aujourd'hui, mais il la mettait a portee de tout code de
    production appele plus tard - et la reference contre laquelle on mesure ne
    se laisse pas ecrire. Le sens de la mesure est intact: ce qui est mesure
    ici est le CONTENU de l'exemple, que `copytree` reproduit a l'octet, jamais
    son emplacement.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._pile = ExitStack()
        cls.instance = cls._pile.enter_context(exemple_copie("piece_detail"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._pile.close()


class SANS_MATIERE_AUCUNE_PIECE_N_EST_SERVIE(_Socle):
    """**Le coeur du lot, et le cas qui prouve.**"""

    def test_l_identifiant_privilegie_ne_trouve_plus_rien_sur_modele_vide(self) -> None:
        detail = build_piece_detail(
            self.instance, 2025, LIVE_CONTRACT_FALLBACK_ID, dashboard_model={})
        self.assertEqual("missing", detail.get("state"))

    def test_il_se_comporte_comme_N_IMPORTE_QUEL_autre_identifiant(self) -> None:
        """Le propre d'un cas particulier est de se distinguer. Ici, plus rien
        ne doit distinguer cet identifiant d'un autre."""
        privilegie = build_piece_detail(
            self.instance, 2025, LIVE_CONTRACT_FALLBACK_ID, dashboard_model={})
        quelconque = build_piece_detail(
            self.instance, 2025, "UX-PIECE-QUI-N-EXISTE-PAS", dashboard_model={})
        self.assertEqual(quelconque.get("state"), privilegie.get("state"))

    def test_ce_qui_est_rendu_dit_qu_il_n_a_RIEN_trouve(self) -> None:
        """**Ce test a du etre recentre, et la nuance compte.**

        Sa premiere version interdisait `is_fictive` sur la piece rendue. Elle
        echouait - et avec raison: l'etat `missing` porte ce drapeau, et **ce
        n'est pas un mensonge**, puisque son libelle dit « introuvable ». Le
        defaut n'etait pas le drapeau: c'etait une piece COMPLETE servie comme
        TROUVEE. Ce qui doit etre garde est donc ce que la page annonce.
        """
        detail = build_piece_detail(
            self.instance, 2025, LIVE_CONTRACT_FALLBACK_ID, dashboard_model={})
        piece = detail.get("piece") or {}
        self.assertIn("introuvable", str(piece.get("label", "")).lower())

    def test_et_il_ne_pretend_pas_savoir_que_le_coffre_est_fictif(self) -> None:
        """Ce libelle sort sur TOUTE instance dont le modele ne porte pas
        l'identifiant, y compris une instance reelle. Dire `coffre local
        fictif` y est faux - meme defaut que `Devis retenu`."""
        detail = build_piece_detail(
            self.instance, 2025, LIVE_CONTRACT_FALLBACK_ID, dashboard_model={})
        piece = detail.get("piece") or {}
        self.assertNotIn("fictif", str(piece.get("label", "")).lower())


class LA_MATIERE_REELLE_EST_TOUJOURS_SERVIE(_Socle):
    """**Le temoin de non-regression, et il est indispensable.**

    Retirer le repli ne devait pas rendre l'ecran muet sur une instance qui
    porte vraiment la piece. Sans ce test, le lot aurait pu "corriger" le
    defaut en cassant le chemin reel.
    """

    def test_un_identifiant_porte_par_le_modele_est_trouve(self) -> None:
        detail = build_piece_detail(
            self.instance, 2025, LIVE_CONTRACT_FALLBACK_ID)
        self.assertEqual("found", detail.get("state"))

    def test_et_la_piece_servie_vient_du_MODELE_et_non_d_une_fabrique(self) -> None:
        detail = build_piece_detail(
            self.instance, 2025, LIVE_CONTRACT_FALLBACK_ID)
        piece = detail.get("piece") or {}
        self.assertNotEqual(True, piece.get("is_fictive"))


class PLUS_AUCUNE_FABRIQUE_DE_PIECE_NE_SUBSISTE(unittest.TestCase):
    """La garde de structure: le motif ne doit pas revenir par une autre porte.

    Elle lit l'ARBRE du module, pas son texte: la docstring ci-dessus cite
    legitimement le libelle de la piece retiree pour expliquer le defaut, et
    une garde qui lirait tout attraperait sa propre explication - faute deja
    commise puis corrigee dans ce depot.
    """

    def _fonctions(self) -> list[str]:
        arbre = ast.parse(MODULE.read_text(encoding="utf-8"))
        return [n.name for n in ast.walk(arbre) if isinstance(n, ast.FunctionDef)]

    def test_la_fabrique_a_disparu(self) -> None:
        self.assertNotIn("_live_contract_fallback_piece", self._fonctions())

    def test_aucune_fonction_du_module_ne_fabrique_un_repli_de_piece(self) -> None:
        suspectes = [
            nom for nom in self._fonctions()
            if "fallback" in nom.lower() and "piece" in nom.lower()
        ]
        self.assertEqual(
            [], suspectes,
            "une fabrique de piece de repli est revenue: sans coffre, l'ecran "
            "doit dire qu'il n'a rien, pas inventer de quoi remplir")

    def test_aucune_piece_COMPLETE_n_est_plus_fabriquee(self) -> None:
        """**Ce test a du etre recentre lui aussi.**

        Sa premiere version interdisait toute occurrence de `is_fictive` dans
        le module. Elle echouait sur l'etat `missing`, qui le porte
        legitimement, et elle aurait aussi condamne les EXEMPLES de
        `viewmodels/_pieces_ux`, qui se declarent dans des champs rendus -
        `status: exemple`, `requires_real_validation`. Ce qui distingue le
        defaut corrige n'est pas le drapeau: c'est qu'une piece portant
        criticite, motif redige et boutons d'action etait servie comme TROUVEE.
        La garde porte donc sur les champs qui font croire a une piece suivie.
        """
        arbre = ast.parse(MODULE.read_text(encoding="utf-8"))
        for noeud in ast.walk(arbre):
            if not isinstance(noeud, ast.Dict):
                continue
            cles = {
                c.value for c in noeud.keys
                if isinstance(c, ast.Constant) and isinstance(c.value, str)
            }
            if not {"is_fictive"} <= cles:
                continue
            with self.subTest(cles=sorted(cles)[:4]):
                self.assertFalse(
                    {"criticality_label", "request_href", "deposit_href"} & cles,
                    "un dictionnaire marque fictif porte encore criticite ou "
                    "boutons d'action: c'est une piece complete inventee")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
