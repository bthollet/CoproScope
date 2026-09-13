# -*- coding: utf-8 -*-
"""Le franchissement d'un seuil se calcule, ou se declare non calculable.

**Le trou T9**, ouvert depuis le blueprint et ecrit a l'ecran dans une phrase
ajoutee a chaque cellule de seuil: *le franchissement lui-meme n'est pas
calcule; la comparaison du montant au seuil n'existe pas encore dans le
modele*.

**Cette phrase etait devenue fausse de deux facons.** La comparaison existe
desormais - la matrice porte le montant arrete par la deliberation retenue a
cote de celui de l'acte. Et surtout, ce qui manquait n'etait pas le calcul:
**c'etaient les montants**.

**Mesure sur instance VIDE reabsorbant 858 pieces sources, 550 liens de
seuil:** 62 lignes ou l'obligation s'applique, **212 ou le montant de la
DECISION n'est pas lisible**, zero ou le seuil n'est pas atteint. Dire *le
modele ne compare pas* laissait croire a un manque de code la ou il y a un
manque de donnee - et un lecteur qui reclame du code n'obtiendra jamais le
montant qui manque.

**Ce que ces tests gardent avant tout.** Un montant illisible ne se lit JAMAIS
comme *sous le seuil*: ce serait affirmer qu'aucune obligation ne s'applique,
sur une ligne ou l'on ne sait rien. Trois etats, et le troisieme n'est jamais un
feu vert.
"""

from __future__ import annotations

import unittest

from coproscope.web._controle_gouvernance_franchissement import (
    FRANCHI,
    MANQUE_ACTE,
    MANQUE_LES_DEUX,
    MANQUE_SEUIL,
    NON_COMPARABLE,
    NON_FRANCHI,
    franchissement,
    phrase_de_franchissement,
)


class DEUX_NOMBRES_LUS_DONNENT_UNE_REPONSE(unittest.TestCase):
    """Le cas ordinaire, et il doit rester simple."""

    def test_au_dessus_du_seuil_l_obligation_s_applique(self) -> None:
        etat, motif = franchissement("2500,00", "1000,00")
        self.assertEqual(FRANCHI, etat)
        self.assertEqual("", motif)

    def test_en_dessous_du_seuil_elle_ne_s_applique_pas_de_ce_fait(self) -> None:
        etat, motif = franchissement("800,00", "1000,00")
        self.assertEqual(NON_FRANCHI, etat)
        self.assertEqual("", motif)

    def test_les_ecritures_courantes_d_un_montant_sont_lues(self) -> None:
        """Espace fine, espace ordinaire, virgule ou point: c'est de la mise en
        forme, pas du sens. Le lecteur de montants du depot les absorbe deja, et
        ce module ne s'en ecrit pas un second."""
        for ecriture in ("2 500,00", "2 500,00", "2500.00", "2500"):
            with self.subTest(ecriture=ecriture):
                self.assertEqual(FRANCHI, franchissement(ecriture, "1000,00")[0])


class LE_CAS_LIMITE_EST_TRANCHE_PAR_LE_DROIT(unittest.TestCase):
    """L'article 21 alinea 2 vise les marches dont le montant EXCEDE le seuil."""

    def test_un_montant_EGAL_au_seuil_ne_l_excede_pas(self) -> None:
        """Zero egalite sur les 124 comparables du corpus, donc aucune ligne
        n'en depend aujourd'hui - raison de plus pour l'ecrire maintenant,
        tant que cela ne coute rien, plutot que le jour ou cela decidera d'une
        obligation."""
        self.assertEqual(NON_FRANCHI, franchissement("1000,00", "1000,00")[0])

    def test_un_centime_au_dessus_l_excede(self) -> None:
        self.assertEqual(FRANCHI, franchissement("1000,01", "1000,00")[0])


class UN_MONTANT_QU_ON_NE_LIT_PAS_N_EST_JAMAIS_UN_NON(unittest.TestCase):
    """Le coeur de ce module, et le temoin de sante de l'instrument."""

    def test_montant_de_l_acte_absent_rend_NON_COMPARABLE_et_le_NOMME(self) -> None:
        for absent in ("", "   ", None):
            with self.subTest(absent=absent):
                etat, motif = franchissement(absent, "1000,00")
                self.assertEqual(NON_COMPARABLE, etat)
                self.assertEqual(MANQUE_ACTE, motif)

    def test_montant_du_seuil_absent_rend_NON_COMPARABLE_et_le_NOMME(self) -> None:
        etat, motif = franchissement("2500,00", "")
        self.assertEqual(NON_COMPARABLE, etat)
        self.assertEqual(MANQUE_SEUIL, motif)

    def test_les_deux_absents_le_disent_aussi(self) -> None:
        etat, motif = franchissement("", "")
        self.assertEqual(NON_COMPARABLE, etat)
        self.assertEqual(MANQUE_LES_DEUX, motif)

    def test_un_montant_ILLISIBLE_ne_devient_pas_un_NON_FRANCHI(self) -> None:
        """La faute qui compte: lire *illisible* comme *sous le seuil* affirme
        qu'aucune obligation ne s'applique, sur une ligne ou l'on ne sait rien.
        """
        for illisible in ("environ mille", "n/a", "-", "deux mille euros"):
            with self.subTest(illisible=illisible):
                etat, motif = franchissement(illisible, "1000,00")
                self.assertEqual(NON_COMPARABLE, etat)
                self.assertEqual(MANQUE_ACTE, motif)

    def test_un_seuil_a_ZERO_n_est_pas_une_absence(self) -> None:
        """Un seuil a zero euro voudrait dire que tout y est soumis; une
        absence ne veut rien dire du tout. Les confondre effacerait une regle."""
        etat, _motif = franchissement("10,00", "0")
        self.assertEqual(FRANCHI, etat)


class LES_PHRASES_NE_CONCLUENT_PAS_A_LA_PLACE_DU_LECTEUR(unittest.TestCase):
    """Un seuil franchi rend une obligation exigible; il ne dit pas qu'elle a
    ete tenue. Confondre les deux ferait reclamer une piece qui existe deja."""

    def test_la_phrase_du_NON_COMPARABLE_refuse_d_etre_lue_comme_un_non(self) -> None:
        texte = phrase_de_franchissement(NON_COMPARABLE, MANQUE_ACTE)
        self.assertIn("n'a pas pu être calculé", texte)
        self.assertIn("ce n'est pas un « non »", texte.lower())
        self.assertIn(MANQUE_ACTE, texte)

    def test_aucune_phrase_ne_dit_que_l_obligation_a_ete_TENUE(self) -> None:
        for etat, motif in ((FRANCHI, ""), (NON_FRANCHI, ""),
                            (NON_COMPARABLE, MANQUE_ACTE)):
            with self.subTest(etat=etat):
                texte = phrase_de_franchissement(etat, motif).lower()
                for interdit in ("a été consulté", "conforme", "respectée",
                                 "rien à redire"):
                    self.assertNotIn(interdit, texte)

    def test_le_franchi_dit_que_l_obligation_s_APPLIQUE(self) -> None:
        self.assertIn("l'obligation s'applique",
                      phrase_de_franchissement(FRANCHI, ""))


class LA_BULLE_DE_SEUIL_PORTE_REELLEMENT_L_ETAT(unittest.TestCase):
    """**Ce test existe parce que sans lui, le cablage n'est pas garde.**

    Tous les tests ci-dessus appellent la fonction en direct: retirer l'appel de
    la bulle les laisserait au vert. C'est la faute que ce depot a commise deux
    fois le meme jour - garder le calcul et pas le cablage.
    """

    def _bulle(self, montant_acte: str, montant_seuil: str) -> dict:
        from coproscope.modules._actes_seuils_normes import ENTREES_SEUIL
        from coproscope.web._controle_gouvernance_cellules import _bulle_seuil

        entree = ENTREES_SEUIL[0]
        ligne = {
            f"cel_{entree.prefixe}": "AU_DOSSIER",
            f"nb_{entree.prefixe}": "1",
            f"nb_{entree.prefixe}_ex_aequo": "0",
            f"cle_{entree.prefixe}": "2024-07-03",
            f"montant_{entree.prefixe}": montant_seuil,
            "montant_autorise": montant_acte,
        }
        return _bulle_seuil(ligne, "ENGAGEMENT_DEPENSE", entree.prefixe,
                            {"nom": "Seuil", "disponible": "d", "confirmer": "c",
                             "manquante": "m"})

    def test_la_bulle_porte_l_etat_et_la_phrase(self) -> None:
        bulle = self._bulle("2500,00", "1000,00")
        self.assertEqual(FRANCHI, bulle["franchissement"])
        self.assertIn("dépasse", bulle["detail"])

    def test_sans_montant_la_bulle_declare_ce_qui_manque(self) -> None:
        bulle = self._bulle("", "1000,00")
        self.assertEqual(NON_COMPARABLE, bulle["franchissement"])
        self.assertIn(MANQUE_ACTE, bulle["detail"])

    def test_l_ancienne_phrase_a_disparu(self) -> None:
        """Elle disait que la comparaison n'existait pas dans le modele."""
        bulle = self._bulle("2500,00", "1000,00")
        self.assertNotIn("n'existe pas encore dans le modèle", bulle["detail"])


class LA_MATRICE_PORTE_LE_MONTANT_DU_SEUIL(unittest.TestCase):
    """**Ce test existe parce qu'une cinquieme mutation NE MORDAIT PAS.**

    Tout ce qui precede s'exerce sur des valeurs passees a la main. Remplacer,
    dans le SQL de la matrice, le montant du seuil par une DATE laissait donc
    tous les tests au vert - l'ecran aurait compare un montant a une date, et
    rendu *non comparable* partout sans que rien ne le signale. La vue ne se
    verifie que sur une vraie base.
    """

    def setUp(self) -> None:
        import tempfile
        from pathlib import Path

        from coproscope.modules import actes_autorisation as A
        from coproscope.modules._actes_seuils_normes import ENTREES_SEUIL

        self.A = A
        self.entree = ENTREES_SEUIL[0]
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self._temp.cleanup)
        racine = Path(self._temp.name)
        (racine / "vault_local").mkdir()

        class _Instance:
            def __init__(self, r):
                self.racine = r

            def settings(self):
                return {"vault": {"local_root": "./vault_local"}}

            def resolve_path(self, valeur):
                return (self.racine / valeur.lstrip("./")).resolve()

        self.instance = _Instance(racine)
        A.preparer(self.instance)

    def _acte(self, acte_id: str, **kw) -> dict:
        ligne = {
            "acte_id": acte_id, "nature": "RESOLUTION_AG", "etat": "CONSTATEE",
            "portee": "ORDINAIRE", "date_effet": "2024-07-03", "exercice": "2024",
            "ag_id": "AG-2024-07-03", "numero": "12", "sous_numero": "",
            "objet": "Objet de test", "montant_autorise": "", "entreprise": "",
            "montant_source": "", "entreprise_source": "", "valide_du": "",
            "valide_au": "", "majorite_requise": "24", "majorite_appliquee": "24",
            "resultat": "ADOPTEE", "resolution_id": "", "page": "1", "ancre": "",
            "confiance": "forte", "doc_id": "DOC-PV", "origine": "EXTRAIT",
        }
        ligne.update(kw)
        return ligne

    def test_le_montant_ARRETE_par_la_deliberation_arrive_dans_la_matrice(self) -> None:
        import sqlite3

        A, prefixe = self.A, self.entree.prefixe
        A.ecrire(self.instance, A.TABLE_ACTES, [
            self._acte("ACTE-DEPENSE", portee="ENGAGEMENT_DEPENSE",
                       montant_autorise="2500.00"),
            self._acte("ACTE-SEUIL", portee="SEUIL", montant_autorise="1000.00",
                       valide_du="2024-07-03"),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_LIENS, [{
            "lien_id": A.lien_id("acte", "ACTE-DEPENSE", self.entree.relation,
                                 "acte", "ACTE-SEUIL", "COPROSCOPE_CALCULE"),
            "source_kind": "acte", "source_id": "ACTE-DEPENSE",
            "relation": self.entree.relation, "target_kind": "acte",
            "target_id": "ACTE-SEUIL", "provenance": "COPROSCOPE_CALCULE",
            "force_probatoire": "PIECE_PRODUITE", "motif": "", "doute": "",
            "montant_impute": "", "libelle_cible": "", "echeance": "",
            "constate_le": "2024-07-03", "auteur": "", "page": "", "ancre": "",
            "doc_id": "DOC-PV", "origine": "EXTRAIT",
        }], ["DOC-PV"])

        cx = sqlite3.connect(A.store_path(self.instance))
        try:
            cx.row_factory = sqlite3.Row
            ligne = cx.execute(
                "SELECT montant_autorise, montant_%s FROM v_matrice_gouvernance "
                "WHERE acte_id = 'ACTE-DEPENSE'" % prefixe).fetchone()
        finally:
            cx.close()

        self.assertIsNotNone(ligne, "la depense n'apparait pas dans la matrice")
        self.assertEqual("1000.00", ligne["montant_%s" % prefixe],
                         "la matrice ne porte pas le montant ARRETE par le seuil")
        etat, _motif = franchissement(ligne["montant_autorise"],
                                      ligne["montant_%s" % prefixe])
        self.assertEqual(FRANCHI, etat,
                         "2 500 EUR devraient depasser un seuil de 1 000 EUR")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
