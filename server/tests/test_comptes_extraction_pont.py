"""Le pont n'admet un document que s'il ferme ses propres comptes.

Lot `RM-2026-0074`, avec la regle d'admission de `RM-2026-0058`.

Deux familles de tests ici, et elles ne prouvent pas la meme chose.

`ConservationEtAdmission` construit ses gabarits et tourne partout, CI comprise.
Elle prouve que la REGLE tient - jamais que la lecture est juste sur du reel.

`CorpusReelDeuxCabinets` lit l'instance de lot, qui est une donnee privee locale
absente de la CI, et se saute d'elle-meme ailleurs. C'est la seule des deux qui
dise quelque chose sur la justesse, et elle ne dit rien tant qu'elle est sautee.
Cette asymetrie est declaree plutot que masquee: une suite verte sur gabarits
synthetiques prouve que la chaine tourne, pas ce qu'elle lit.
"""

from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from coproscope.modules._comptes_extraction_etat import lire_etat_depenses
from coproscope.modules._comptes_extraction_pont import (
    ADMIS,
    REFUS_AUCUNE_LIGNE,
    REFUS_CONSERVATION,
    REFUS_TOTAL_ABSENT,
    absorber,
    admettre,
    admettre_texte,
    lignes_csv,
)

# Import absolu, comme les autres modules de tests du depot qui partagent des
# gabarits. L'import RELATIF, lui, ne tient qu'en invocation paquet
# (`-m unittest tests.X`) et casse sous `discover -s tests`: le module passait
# isolement pendant que la suite complete echouait a le charger.
from tests.test_comptes_extraction import ETAT_POINT, ETAT_VIRGULE
from tests._instance_de_lot import corpus_portant

# Instance VIDE du lot, reconstruite a partir des pieces sources le 2026-09-08.
# Elle ne contient ni registre ni sortie: seulement la configuration et les PDF
# d'origine, plus la couche de texte que le lot a lui-meme extraite.
#: **Le nom de l'instance etait grave ici, et la doctrine impose de la
#: supprimer** - donc cette garde etait morte d'avance. On cherche ce que
#: l'instance PORTE. Voir `_instance_de_lot.py` pour la mesure et l'axe.
#: **Selection et consommation different, et c'est voulu.** La mesure oppose
#: deux cabinets: le premier est reconnu par ses redditions, le second est
#: *tout le reste* du meme dossier. Selectionner sur `*REDDITION*` ecarte les
#: corpus etrangers - dont celui de 858 pieces qui avait fait rendre 11 echecs
#: a une version anterieure - tandis que la lecture prend bien tous les `.txt`.
_ANCRE = "staging/text/*REDDITION*.txt"
_TOUS = "staging/text/*.txt"
CORPUS = corpus_portant(
    _ANCRE, mesure="le pont entre l'extraction et les comptes, sur corpus reel")


class ConservationEtAdmission(unittest.TestCase):
    """La regle, sur gabarits construits. Vaut en CI, ne prouve pas la justesse."""

    def test_un_etat_qui_ferme_ses_comptes_est_admis(self) -> None:
        admission = admettre_texte(ETAT_VIRGULE)
        self.assertTrue(admission.admis)
        self.assertEqual(admission.motif, ADMIS)
        self.assertEqual(admission.ecart, Decimal("0.00"))

    def test_un_document_sans_total_general_est_refuse_meme_s_il_rend_des_lignes(self) -> None:
        """Le cas mesure sur le second cabinet: des lignes, aucun total."""

        admission = admettre_texte(ETAT_POINT)
        self.assertFalse(admission.admis)
        self.assertEqual(admission.motif, REFUS_TOTAL_ABSENT)
        # Le refus est chiffre: il dit combien de lignes il ecarte, et pour combien.
        self.assertGreater(admission.nombre_lignes, 0)
        self.assertGreater(admission.somme_lignes, Decimal("0.00"))

    def test_un_document_refuse_ne_rend_aucune_ligne_csv(self) -> None:
        """La garantie doit etre une garantie, pas une consigne de prudence."""

        admission = admettre_texte(ETAT_POINT)
        self.assertEqual(lignes_csv(admission, 2030), [])

    def test_un_document_admis_rend_des_lignes_au_format_du_contrat(self) -> None:
        rows = lignes_csv(admettre_texte(ETAT_VIRGULE), 2030, source="GABARIT")
        self.assertTrue(rows)
        attendus = {
            "statement_line_id",
            "date",
            "account",
            "account_label",
            "reference",
            "supplier_hint",
            "label",
            "amount",
            "source",
        }
        self.assertEqual(set(rows[0]), attendus)

    def test_le_fournisseur_n_est_jamais_devine(self) -> None:
        """`RM-2026-0058`: 69 pour cent d'une colonne fournisseur devinee etait faux."""

        rows = lignes_csv(admettre_texte(ETAT_VIRGULE), 2030)
        self.assertTrue(all(row["supplier_hint"] == "" for row in rows))

    def test_texte_vide_refuse_sans_lever(self) -> None:
        admission = admettre_texte("")
        self.assertFalse(admission.admis)
        self.assertEqual(admission.motif, REFUS_AUCUNE_LIGNE)

    def test_conservation_admis_plus_ecarte_egale_lu(self) -> None:
        """L'egalite est verifiee, pas postulee."""

        lignes, bilan = absorber({"admis": ETAT_VIRGULE, "refuse": ETAT_POINT}, 2030)
        self.assertTrue(bilan.tient)
        self.assertEqual(bilan.total_admis + bilan.total_ecarte, bilan.total_lu)
        self.assertEqual(bilan.documents_admis, 1)
        self.assertEqual(bilan.documents_ecartes, 1)
        self.assertTrue(lignes)

    def test_chaque_piece_ecartee_porte_son_motif(self) -> None:
        _, bilan = absorber({"admis": ETAT_VIRGULE, "refuse": ETAT_POINT}, 2030)
        motifs = dict(bilan.motifs)
        self.assertEqual(motifs["admis"], ADMIS)
        self.assertEqual(motifs["refuse"], REFUS_TOTAL_ABSENT)

    def test_identifiants_uniques_a_travers_le_sac(self) -> None:
        """Deux pieces numerotees chacune a partir de 1 se masqueraient l'une l'autre."""

        lignes, _ = absorber({"a": ETAT_VIRGULE, "b": ETAT_VIRGULE}, 2030)
        ids = [row["statement_line_id"] for row in lignes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_conservation_non_tenue_est_refusee_et_chiffree(self) -> None:
        """Hors valeurs observees: un total present mais qui ne retombe pas."""

        etat = lire_etat_depenses(ETAT_VIRGULE)
        fausse = type(etat)(
            lignes=etat.lignes[:1],  # on ampute la lecture, le total reste entier
            totaux=etat.totaux,
            profil=etat.profil,
            constats=etat.constats,
        )
        admission = admettre(fausse)
        self.assertFalse(admission.admis)
        self.assertEqual(admission.motif, REFUS_CONSERVATION)
        self.assertIsNotNone(admission.ecart)
        self.assertIn("Ecart mesure", admission.explication)


@unittest.skipUnless(CORPUS.mesurable, CORPUS.motif_de_saut)
class CorpusReelDeuxCabinets(unittest.TestCase):
    """L'epreuve sur pieces reelles, deux cabinets. Sautee hors du poste local."""

    @classmethod
    def setUpClass(cls) -> None:
        # Relu MAINTENANT, et non vide par construction.
        textes = CORPUS.textes(_TOUS)
        cls.cabinet1 = {k: v for k, v in textes.items() if "REDDITION" in k or k.startswith("05_Etat")}
        cls.cabinet2 = {k: v for k, v in textes.items() if k not in cls.cabinet1}
        # La mesure OPPOSE deux cabinets: un cote vide ferait passer ses boucles
        # sans une seule assertion, et le lanceur afficherait `Ran N tests, OK`.
        # Le saut nomme le cote manquant au lieu de mesurer a moitie.
        for nom, lot in (("1", cls.cabinet1), ("2", cls.cabinet2)):
            if not lot:
                raise unittest.SkipTest(
                    "MESURE NON FAITE: %s ne porte aucune piece de cabinet %s. "
                    "Ce qui n'est donc PAS verifie ici: l'opposition entre les "
                    "deux cabinets, dont depend toute la mesure."
                    % (CORPUS.identite, nom)
                )

    def test_cabinet_un_tous_les_exercices_sont_admis(self) -> None:
        for nom, texte in self.cabinet1.items():
            with self.subTest(piece=nom):
                admission = admettre_texte(texte)
                self.assertTrue(admission.admis, f"{nom}: {admission.explication}")
                self.assertEqual(admission.ecart, Decimal("0.00"))

    def test_l_exercice_2025_retombe_sur_l_etalon_releve_a_la_main(self) -> None:
        """`RM-2026-0064`: etalon comptable etabli avant tout traitement outil."""

        cible = next(k for k in self.cabinet1 if k.startswith("2025-12-31_REDDITION"))
        admission = admettre_texte(self.cabinet1[cible])
        self.assertEqual(admission.total_imprime, Decimal("357493.10"))
        self.assertEqual(admission.somme_lignes, Decimal("357493.10"))

    def test_cabinet_deux_aucun_document_n_est_admis(self) -> None:
        """Aucune de ses 22 pieces n'est un etat des depenses. Aucune ne passe."""

        for nom, texte in self.cabinet2.items():
            with self.subTest(piece=nom):
                self.assertFalse(admettre_texte(texte).admis)

    def test_cabinet_deux_les_lignes_parasites_sont_ecartees_avec_leur_motif(self) -> None:
        """Le coeur de l'epreuve: sans regle d'admission, ces lignes passaient."""

        lignes, bilan = absorber(self.cabinet2, 2025)
        self.assertEqual(lignes, [])
        self.assertEqual(bilan.documents_admis, 0)
        # Des lignes ONT ete lues - un contrat de syndic et des devis en rendent -
        # et c'est bien pour cela que le refus doit etre explicite.
        self.assertGreater(bilan.total_ecarte, Decimal("1000000"))
        self.assertTrue(bilan.tient)
        self.assertTrue(all(motif != ADMIS for _, motif in bilan.motifs))


if __name__ == "__main__":
    unittest.main()
