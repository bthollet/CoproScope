"""Le produit ne dit pas « piece produite » la ou aucune piece n'est produite.

Trois affirmations mesurees fausses le 2026-09-05 sur le coffre reel, et
corrigees ensemble le 2026-09-06 parce qu'elles partagent une racine: la force
probatoire montait sans qu'aucun document ne soit vise.

| Ce que l'ecran disait | Ce qui etait etabli | Portee |
|---|---|---|
| « Le devis retenu est au dossier. » | un nombre lu dans une phrase de la convocation | 54 actes |
| « UN montant de seuil est rattache » | DEUX seuils contradictoires y etaient rattaches | 65 actes |
| 72 liens d'avis « vers un document » | les 72 visaient le document de leur propre acte | 72 liens |

**Pourquoi ces trois ensemble, et avant tout le reste.** Corriger la phrase sans
corriger la force deplacerait le mensonge de l'ecran vers la base, ou il ne se
voit plus. Et tant que 54 cellules disent deja « disponible », un rapprochement
de devis reussi ne changerait rien de visible: on ne pourrait pas montrer qu'il
a marche. La mesure ne devient nette qu'apres: zero, puis N, et chaque N est un
document reel dont on peut citer la page.

Ces tests ne verifient pas que le rapprochement existe - il n'existe pas
encore. Ils verifient que le produit **cesse d'affirmer qu'il existe**.
"""

from __future__ import annotations

import unittest

from coproscope.modules import _pont_actes_liens as LIENS
from coproscope.modules._actes_seuils_normes import ENTREES_SEUIL, NORME_CONCURRENCE
from coproscope.modules._actes_vocabulaire import FORCE_AFFIRME, FORCE_PIECE
from coproscope.web._controle_gouvernance_cellules import _seuil


class _Candidat:
    """Le minimum qu'attend `liens_du_devis`."""

    def __init__(self, **ligne: str) -> None:
        self.ligne = ligne
        self.source = "DEVIS_CITE"


def _acte() -> dict[str, str]:
    return {"acte_id": "ACTE-AG-2026-04-29-R11-1", "doc_id": "DOC-CONVOC",
            "date_effet": "2026-04-29", "exercice": "2026"}


class UnMontantLuDansUnePhraseNEstPasUnePieceTests(unittest.TestCase):
    def test_un_devis_chiffre_reste_a_confirmer(self) -> None:
        """Le cas des 54: la convocation cite un devis ET son montant."""
        liens = LIENS.liens_du_devis(
            _Candidat(devis_cite_id="D1", entreprise="GTI",
                      montant_ttc="68163.55", numero="11"),
            _acte(),
        )
        devis = [l for l in liens if l["relation"] == "DEVIS_RETENU"]
        self.assertEqual(len(devis), 1)
        self.assertEqual(
            devis[0]["force_probatoire"], FORCE_AFFIRME,
            "un nombre lu dans une phrase de convocation n'est pas une piece "
            "produite: la force ne doit monter que sur un document vise")
        self.assertNotEqual(devis[0]["force_probatoire"], FORCE_PIECE)
        self.assertTrue(
            devis[0]["doute"],
            "le doute doit dire ce qui manque, pas rester vide")

    def test_un_devis_sans_montant_reste_a_confirmer_lui_aussi(self) -> None:
        liens = LIENS.liens_du_devis(
            _Candidat(devis_cite_id="D2", entreprise="KOLER", montant_ttc="",
                      numero="12"),
            _acte(),
        )
        devis = [l for l in liens if l["relation"] == "DEVIS_RETENU"][0]
        self.assertEqual(devis["force_probatoire"], FORCE_AFFIRME)

    def test_les_deux_cas_se_distinguent_par_leur_doute_pas_par_leur_force(self) -> None:
        """Meme force, doutes differents: c'est la ou l'information vit."""
        chiffre = LIENS.liens_du_devis(
            _Candidat(devis_cite_id="D1", entreprise="GTI",
                      montant_ttc="68163.55", numero="11"), _acte())[0]
        muet = LIENS.liens_du_devis(
            _Candidat(devis_cite_id="D2", entreprise="KOLER", montant_ttc="",
                      numero="12"), _acte())[0]
        self.assertEqual(chiffre["force_probatoire"], muet["force_probatoire"])
        self.assertNotEqual(chiffre["doute"], muet["doute"])


class UnLienNeBouclePasSurCeluiQuiLAffirmeTests(unittest.TestCase):
    def test_l_avis_du_conseil_ne_vise_pas_le_document_de_son_propre_acte(self) -> None:
        """Le cas des 72: le lien pointait sur la convocation qui l'affirme."""
        acte = _acte()
        liens = LIENS.liens_du_devis(
            _Candidat(devis_cite_id="D1", entreprise="GTI",
                      montant_ttc="1000.00", numero="11", avis_cs_affirme="oui"),
            acte,
        )
        avis = [l for l in liens if l["relation"] == "AVIS_CS"]
        self.assertEqual(len(avis), 1, "l'affirmation doit rester tracee")
        self.assertNotEqual(
            avis[0]["target_id"], acte["doc_id"],
            "un lien qui vise le document de son propre acte ne mene a aucun "
            "avis: il boucle sur celui qui l'affirme")
        self.assertEqual(
            avis[0]["force_probatoire"], FORCE_AFFIRME,
            "l'avis est affirme, pas produit")

    def test_sans_affirmation_aucun_lien_d_avis_n_est_fabrique(self) -> None:
        liens = LIENS.liens_du_devis(
            _Candidat(devis_cite_id="D1", entreprise="GTI",
                      montant_ttc="1000.00", numero="11"), _acte())
        self.assertEqual([l for l in liens if l["relation"] == "AVIS_CS"], [])


class DeuxSeuilsNeSeDisentPasAuSingulierTests(unittest.TestCase):
    """Le cas des 65: deux seuils votes le meme jour, 1 000 et 2 000 EUR.

    **Une affirmation de cette classe a ete retiree le 2026-09-08, parce
    qu'elle etait fausse.** Elle exigeait que la cellule ecrive que les deux
    seuils `se contredisent`. Mesure du meme jour sur deux coffres reels: les
    299 liens de seuil visent deux resolutions du meme jour, l'une fixant le
    montant a partir duquel la consultation du conseil syndical devient
    obligatoire, l'autre celui a partir duquel la mise en concurrence l'est.
    Deux normes distinctes, pas deux reponses concurrentes.

    **Le modele les distingue depuis `RM-2026-0144`, le 2026-09-08**, et cette
    classe garde ce qui reste vrai apres la separation: deux deliberations
    rattachees a la MEME cellule ne se disent pas au singulier et ne se
    departagent pas en silence. Le cas est monte ici sur le seuil de mise en
    concurrence, parce que deux montants arretes le meme jour pour la MEME
    obligation restent un vrai conflit - c'est ce que la separation ne doit pas
    faire disparaitre. Le detail du departage est garde par
    `test_seuil_chronologie`, l'attribution des normes par
    `test_seuil_deux_normes`.
    """

    #: La cellule mesuree, nommee une fois. Les autres valent `ABSENT`, ce qui
    #: est un statut a part entiere: aucune deliberation ne leur est rattachee.
    PREFIXE = NORME_CONCURRENCE.prefixe

    def _ligne(self, nb: int) -> dict[str, object]:
        ligne: dict[str, object] = {
            "cel_%s" % n.prefixe: "ABSENT" for n in ENTREES_SEUIL
        }
        ligne["cel_%s" % self.PREFIXE] = "PIECE_PRODUITE"
        ligne["nb_%s" % self.PREFIXE] = nb
        return ligne

    def _bulle(self, nb: int) -> dict[str, object]:
        return [b for b in _seuil(self._ligne(nb), "ENGAGEMENT_DEPENSE")
                if b["norme"] == self.PREFIXE][0]

    def test_deux_seuils_rattaches_font_dire_deux(self) -> None:
        bulle = self._bulle(2)
        self.assertIn("2 montants de seuil", bulle["detail"])
        self.assertIn(
            "pas tranché", bulle["detail"],
            "deux seuils non departages ne se presentent pas comme un seuil "
            "retenu")
        self.assertEqual(
            bulle["statut"], "confirmer",
            "deux sources non departagees ne sont pas une source disponible")

    def test_la_contradiction_n_est_pas_affirmee_sans_mesure(self) -> None:
        """Le modele ne compare pas les deux seuils: il ne peut rien en dire."""
        bulle = self._bulle(2)
        self.assertNotIn("contredisent", bulle["detail"])

    def test_un_seul_seuil_ne_declenche_aucun_signalement(self) -> None:
        bulle = self._bulle(1)
        self.assertNotIn("pas tranché", bulle["detail"])

    def test_la_phrase_de_conflit_ne_reaffirme_pas_le_singulier(self) -> None:
        """La correction remplace la phrase, elle ne l'empile pas derriere."""
        bulle = self._bulle(2)
        self.assertNotIn("Un montant de seuil arrêté", bulle["detail"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
