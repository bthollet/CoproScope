# -*- coding: utf-8 -*-
"""Hors du champ d'une norme, un acte ne la franchit pas: elle ne le vise pas.

`RM-2026-0144`, residu du refus d'integration. Le lot avait separe deux normes
que le modele ecrasait en une - le seuil de consultation du conseil syndical et
le seuil de mise en concurrence - et l'avait fait proprement, **jusqu'aux
relations**. Le sceptique a refuse sur un motif d'une ligne: *la separation
s'arrete aux relations, elle n'atteint pas le CONTROLE qui decide de leur
applicabilite*. Le lot l'ecrivait lui-meme: *« Ce lot ne s'en sert pas encore
pour retirer un controle. »*

**Mesure du 2026-09-11, et elle confirme le refus a la lettre.** Le champ
`exclut` de `NormeSeuil` porte le texte de l'exclusion depuis sa creation.
Grep sur tout `server/src` et `server/tests`: **zero lecture hors du module qui
le declare.**

**CE CONTROLE NE RETIRE AUCUN LIEN SUR LE CORPUS, et c'est mesure.** Sur 550
actes: **12 relevent du contrat de syndic**, classes `ORDINAIRE` (7),
`DESIGNATION_SYNDIC` (2), `SEUIL` (2), `DESIGNATION_ORGANE` (1). **Aucun n'est
un `ENGAGEMENT_DEPENSE`**, et sur les **282 engagements de depense**, **zero**
releve du contrat de syndic. Comme `liens_seuil` ne rattache que des
engagements de depense, l'exclusion ne mord sur aucune des 276 lignes de mise
en concurrence.

**Mais elle est respectee par ACCIDENT.** Ce qui protege n'est pas la regle de
l'alinea: c'est qu'une AUTRE classification range le contrat de syndic
ailleurs. Le jour ou un renouvellement de contrat est classe
`ENGAGEMENT_DEPENSE`, l'exclusion tombe **en silence** et le produit affirme
une obligation que la loi ne prevoit pas. Meme choix que le cas d'egalite de
`franchissement`: l'ecrire tant qu'il ne coute rien.

**L'AXE.** Ce qui VARIE: la maniere dont une resolution nomme le contrat de
syndic, le cabinet, la redaction. Ce qui reste INVARIANT: **une exclusion
legale porte sur la NATURE de l'acte, pas sur les mots qui la disent.** Le
controle ne lit donc aucun intitule: il compare la PORTEE - le vocabulaire dont
le modele dispose deja - au champ d'exclusion de la norme.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from coproscope.modules._actes_seuils_applicabilite import (
    APPLICABLE,
    HORS_CHAMP,
    PORTEE_INCONNUE,
    PORTEES_EXCLUES,
    applicabilite,
    portees_exclues,
    phrase_d_applicabilite,
)
from coproscope.modules._actes_seuils_normes import (
    NORME_CONCURRENCE,
    NORME_CONSULTATION_CS,
    NORME_NON_ATTRIBUEE,
    NORMES_SEUIL,
)
from coproscope.modules._actes_vocabulaire import (
    PORTEE_DESIGNATION_SYNDIC,
    PORTEE_ENGAGEMENT_DEPENSE,
    PORTEES,
)

DEPOT = Path(__file__).resolve().parents[2]


class L_ALINEA_NE_DIT_PAS_LA_MEME_CHOSE_DES_DEUX_NORMES(unittest.TestCase):
    """La consultation du conseil syndical ne connait aucune reserve."""

    def test_la_mise_en_concurrence_EXCEPTE_le_contrat_de_syndic(self) -> None:
        etat, motif = applicabilite(NORME_CONCURRENCE, PORTEE_DESIGNATION_SYNDIC)
        self.assertEqual(HORS_CHAMP, etat)
        self.assertTrue(motif, "hors champ sans raison est un refus muet")

    def test_la_consultation_du_conseil_syndical_ne_l_excepte_PAS(self) -> None:
        """L'article ajoute au contraire que le conseil peut se prononcer sur
        tout projet de contrat de syndic. Les deux normes doivent donc repondre
        DIFFEREMMENT a la meme portee - sans quoi la separation du lot ne sert
        a rien au-dela des relations."""
        etat, _motif = applicabilite(NORME_CONSULTATION_CS, PORTEE_DESIGNATION_SYNDIC)
        self.assertEqual(APPLICABLE, etat)

    def test_les_deux_normes_repondent_DIFFEREMMENT_a_la_meme_portee(self) -> None:
        """**Le coeur du lot, en une assertion.**

        Si les deux normes rendaient la meme chose ici, le controle
        d'applicabilite serait decoratif et le refus du sceptique tiendrait
        encore.
        """
        self.assertNotEqual(
            applicabilite(NORME_CONCURRENCE, PORTEE_DESIGNATION_SYNDIC)[0],
            applicabilite(NORME_CONSULTATION_CS, PORTEE_DESIGNATION_SYNDIC)[0],
            "les deux normes traitent le contrat de syndic a l'identique: la "
            "separation ne va toujours pas jusqu'au controle")


class CE_QUI_EST_VISE_RESTE_VISE(unittest.TestCase):
    """L'exclusion ne doit pas devenir une porte de sortie generale."""

    def test_un_engagement_de_depense_ordinaire_reste_soumis(self) -> None:
        for norme in NORMES_SEUIL:
            with self.subTest(norme=norme.cle):
                etat, _ = applicabilite(norme, PORTEE_ENGAGEMENT_DEPENSE)
                self.assertEqual(APPLICABLE, etat)

    def test_toute_portee_connue_hors_exclusion_reste_soumise(self) -> None:
        exclues = portees_exclues(NORME_CONCURRENCE.relation)
        for portee in PORTEES:
            if portee in exclues:
                continue
            with self.subTest(portee=portee):
                self.assertEqual(
                    APPLICABLE, applicabilite(NORME_CONCURRENCE, portee)[0])


class UNE_PORTEE_INCONNUE_NE_TRANCHE_NI_DANS_UN_SENS_NI_DANS_L_AUTRE(unittest.TestCase):
    """Le troisieme etat, et il n'est jamais un feu vert."""

    def test_une_portee_absente_du_vocabulaire_ne_conclut_pas(self) -> None:
        etat, motif = applicabilite(NORME_CONCURRENCE, "PORTEE_QUE_PERSONNE_NE_CONNAIT")
        self.assertEqual(PORTEE_INCONNUE, etat)
        self.assertTrue(motif)

    def test_une_portee_vide_ne_conclut_pas_davantage(self) -> None:
        self.assertEqual(
            PORTEE_INCONNUE, applicabilite(NORME_CONCURRENCE, "")[0])

    def test_l_inconnu_n_est_ni_applicable_ni_hors_champ(self) -> None:
        """Le dire autrement reviendrait a trancher a la place du lecteur."""
        self.assertNotIn(PORTEE_INCONNUE, (APPLICABLE, HORS_CHAMP))

    def test_une_norme_SANS_reserve_conclut_meme_sur_l_inconnu(self) -> None:
        """Et c'est juste: l'alinea ne donne aucune reserve a la consultation
        du conseil syndical, donc il n'y a rien a verifier. Rendre
        `PORTEE_INCONNUE` ici fabriquerait un doute que le droit ne porte pas.
        """
        self.assertEqual(
            APPLICABLE,
            applicabilite(NORME_CONSULTATION_CS, "PORTEE_INCONNUE_DU_MODELE")[0])


class LE_RESIDU_N_EST_PAS_UNE_NORME(unittest.TestCase):
    """Un seuil rattache dont la norme n'a pas ete attribuee."""

    def test_le_residu_ne_porte_aucune_exclusion(self) -> None:
        """On ignore quelle obligation il declenche: en deduire un champ
        d'exclusion serait inventer une reponse."""
        self.assertEqual(
            APPLICABLE,
            applicabilite(NORME_NON_ATTRIBUEE, PORTEE_DESIGNATION_SYNDIC)[0])


class L_EXCLUSION_SE_DIT_EN_PORTEES_ET_JAMAIS_EN_MOTS(unittest.TestCase):
    """**La garde d'axe: elle interdit de recoder des modalites ici.**

    Enumerer `contrat de syndic`, `mandat du syndic`, `honoraires de gestion`
    reviendrait a lister les tournures d'un cabinet, et a casser au troisieme
    syndic. C'est exactement la faute que la regle des axes proscrit, et elle
    est facile a commettre dans ce module precis, puisque le champ `exclut`
    porte justement une phrase en francais.
    """

    MODULE = (DEPOT / "server/src/coproscope/modules"
              / "_actes_seuils_applicabilite.py")

    def test_chaque_valeur_exclue_est_une_PORTEE_du_vocabulaire(self) -> None:
        for cle, portees in PORTEES_EXCLUES.items():  # cle = relation
            for portee in portees:
                with self.subTest(norme=cle, portee=portee):
                    self.assertIn(
                        portee, PORTEES,
                        "l'exclusion designe une valeur qui n'est pas une "
                        "portee du modele: elle ne pourra jamais etre "
                        "rapprochee d'un acte")

    def test_le_controle_ne_lit_AUCUN_intitule_d_acte(self) -> None:
        """Le module ne doit toucher ni `objet`, ni `libelle`, ni `intitule`.

        La verification porte sur les CHAINES du code, pas sur le fichier
        entier: la docstring parle legitimement du contrat de syndic pour
        expliquer l'alinea, et une garde qui lirait tout attraperait sa propre
        explication - defaut deja rencontre dans ce depot.
        """
        arbre = ast.parse(self.MODULE.read_text(encoding="utf-8"))
        # **Les docstrings s'excluent par leur NOEUD, pas par leur valeur.**
        # Premiere ecriture de ce test: comparer `ast.Constant.value` a
        # `ast.get_docstring(...)`. Les deux ne sont PAS egaux - get_docstring
        # nettoie l'indentation - donc le filtre ne retirait rien et la garde
        # a attrape sa propre explication. C'est le defaut que cette docstring
        # decrit, commis en l'ecrivant.
        docstrings = set()
        for noeud in ast.walk(arbre):
            corps = getattr(noeud, "body", None)
            if not isinstance(noeud, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                continue
            if corps and isinstance(corps[0], ast.Expr)                     and isinstance(corps[0].value, ast.Constant)                     and isinstance(corps[0].value.value, str):
                docstrings.add(id(corps[0].value))
        code = [
            n.value.lower() for n in ast.walk(arbre)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and id(n) not in docstrings
        ]
        for interdit in ("objet", "libelle", "intitule", "honoraire", "mandat"):
            with self.subTest(motif=interdit):
                fautives = [s[:60] for s in code if interdit in s]
                self.assertEqual(
                    [], fautives,
                    "le controle d'applicabilite lit un intitule: il code des "
                    "modalites de redaction au lieu d'une nature d'acte")

    def test_la_garde_lit_bien_des_CHAINES_de_code(self) -> None:
        """Temoin de sante: sans lui, le test ci-dessus pourrait passer parce
        qu'il ne lit rien du tout - ce qui est arrive a sa premiere version,
        dans l'autre sens."""
        arbre = ast.parse(self.MODULE.read_text(encoding="utf-8"))
        chaines = [n for n in ast.walk(arbre)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        self.assertGreater(
            len(chaines), 5, "aucune chaine lue dans le module")


class CE_QUI_SE_DIT_A_L_ECRAN(unittest.TestCase):
    """Un etat sans phrase laisse le lecteur devant un code."""

    def test_hors_champ_dit_POURQUOI(self) -> None:
        etat, motif = applicabilite(NORME_CONCURRENCE, PORTEE_DESIGNATION_SYNDIC)
        phrase = phrase_d_applicabilite(etat, motif)
        self.assertIn("ne vise pas", phrase)
        self.assertIn(motif, phrase)

    def test_portee_inconnue_ne_se_lit_pas_comme_une_dispense(self) -> None:
        """*Hors champ* et *on ne sait pas* doivent se distinguer a l'oeil."""
        inconnue = phrase_d_applicabilite(
            *applicabilite(NORME_CONCURRENCE, "INCONNUE"))
        hors = phrase_d_applicabilite(
            *applicabilite(NORME_CONCURRENCE, PORTEE_DESIGNATION_SYNDIC))
        self.assertNotEqual(inconnue, hors)
        self.assertIn("pas établie", inconnue)

    def test_applicable_ne_dit_rien(self) -> None:
        """Le cas normal n'a pas a se commenter."""
        self.assertEqual("", phrase_d_applicabilite(APPLICABLE, ""))


class LE_GATE_DE_VUE_COMPOSE_LES_DEUX_GRANULARITES(unittest.TestCase):
    """**Le controle atteint enfin l'ecran, et c'est tout l'objet du refus.**

    `HORS_CONTROLE` retire un CONTROLE a une portee. Les trois relations de
    seuil partagent `CTRL_SEUIL` - `_actes_vues_matrice.cellule` l'ecrit noir
    sur blanc: *sans ce parametre, chaque relation aurait du etre son propre
    controle*. Le retrait valait donc pour les trois d'un coup.

    **Mesure du 2026-09-11, et le motif ecrit trahissait deja le probleme.**
    `HORS_CONTROLE[DESIGNATION_SYNDIC][CTRL_SEUIL]` portait: *l'article 21
    al. 2 exclut expressement le contrat de syndic du seuil de MISE EN
    CONCURRENCE*. Une seule des deux normes - et le retrait emportait aussi le
    seuil de consultation du conseil syndical, que l'alinea n'excepte pas.
    **Le retrait etait plus large que sa propre justification.**

    Comparer avec `PORTEE_DESIGNATION_ORGANE`, dont le motif dit explicitement
    *les deux seuils*: celui-la reste au niveau du controle, parce qu'il y est
    vrai. La difference entre les deux motifs est la preuve que la granularite
    manquait, et non une preference de style.

    **Le meme raisonnement avait deja ete tenu au meme endroit pour
    `CTRL_AVIS_CS` le 2026-09-04**, en citant `LEGIARTI000039313574` et ses
    deux phrases distinctes. Ce lot applique au seuil la lecture qui avait ete
    retenue pour l'avis.
    """

    def _portees_du_gate(self, relation: str) -> str:
        from coproscope.modules._actes_typologie import CTRL_SEUIL
        from coproscope.modules._actes_vues_matrice import cellule
        return cellule(relation, lien_vivant="1=1", controle=CTRL_SEUIL)

    def test_une_designation_de_syndic_reste_soumise_au_seuil_de_CONSULTATION(self) -> None:
        from coproscope.modules._actes_vocabulaire import REL_SEUIL_CONSULTATION_CS
        self.assertIn(
            PORTEE_DESIGNATION_SYNDIC,
            self._portees_du_gate(REL_SEUIL_CONSULTATION_CS),
            "le seuil de consultation du conseil syndical est retire sur une "
            "designation de syndic: l'alinea ne l'excepte pas, et le produit "
            "empeche de poser la question")

    def test_elle_reste_hors_du_seuil_de_MISE_EN_CONCURRENCE(self) -> None:
        from coproscope.modules._actes_vocabulaire import REL_SEUIL_CONCURRENCE
        self.assertNotIn(
            PORTEE_DESIGNATION_SYNDIC,
            self._portees_du_gate(REL_SEUIL_CONCURRENCE),
            "l'exclusion de l'alinea a ete perdue en deplacant le retrait")

    def test_les_deux_gates_DIFFERENT_sur_cette_portee(self) -> None:
        """S'ils redevenaient identiques, la separation serait a nouveau
        arretee aux relations - exactement le motif du refus."""
        from coproscope.modules._actes_vocabulaire import (
            REL_SEUIL_CONCURRENCE,
            REL_SEUIL_CONSULTATION_CS,
        )
        self.assertNotEqual(
            PORTEE_DESIGNATION_SYNDIC in self._portees_du_gate(REL_SEUIL_CONSULTATION_CS),
            PORTEE_DESIGNATION_SYNDIC in self._portees_du_gate(REL_SEUIL_CONCURRENCE))

    def test_le_retrait_par_CONTROLE_survit_la_ou_il_est_VRAI(self) -> None:
        """`DESIGNATION_ORGANE` reste hors des DEUX seuils: son motif dit *les
        deux seuils*, et une designation de personne n'est ni un marche ni un
        contrat. Ce lot ne devait pas l'emporter au passage."""
        from coproscope.modules._actes_vocabulaire import (
            PORTEE_DESIGNATION_ORGANE,
            REL_SEUIL_CONCURRENCE,
            REL_SEUIL_CONSULTATION_CS,
        )
        for relation in (REL_SEUIL_CONSULTATION_CS, REL_SEUIL_CONCURRENCE):
            with self.subTest(relation=relation):
                self.assertNotIn(
                    PORTEE_DESIGNATION_ORGANE, self._portees_du_gate(relation))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
