"""L'etat de depenses, ou le syndic declare lui-meme ses rattachements.

Les mesures citees viennent de l'observation du 2026-09-04 d'un extranet en
service: 1 286 lignes, 729 portant exactement une facture, cle a quatre
colonnes laissant 21 collisions, cle avec le montant en laissant zero.

Aucune donnee reelle: tout le HTML de ce fichier est synthetique.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import extranetops as X
from coproscope.modules import _extranet_journal as J
from coproscope.modules import _extranet_store as S
from coproscope.modules._extranet_adaptateur import PROFIL_COPRODIRECTE
from coproscope.modules._extranet_depenses import (
    PROVENANCE_SYNDIC,
    lignes_sans_facture,
    lire_depenses,
)
from coproscope.modules._extranet_schema import ORIGINE_EXTRAIT


class _Instance:
    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()


def _cle_charge(nom: str) -> str:
    return f"<tr><td colspan='2'>{nom}</td></tr>"


def _depense(date: str, nature: str, libelle: str, montant: str, facture: bool = True) -> str:
    lien = (
        "<a class='pj pdf' href='documents/JETON' target='_blank'></a>" if facture else ""
    )
    return (
        f"<tr class='just'><td>{date}</td><td>{nature}</td>"
        f"<td>{libelle}</td><td>{montant}</td><td>{lien}</td></tr>"
    )


def _total(intitule: str, montant: str) -> str:
    """Une ligne de sous-total, a la forme mesuree sur la page reelle.

    **Deux valeurs remplies, et quatre cellules** - la ou une depense en a cinq.
    C'est ce qui la distingue, et c'est ce que la premiere version du lecteur
    ratait: elle comptait les cellules remplies, voyait deux, et concluait a un
    en-tete de groupe. 348 lignes de ce genre sur l'etat reel.
    """
    return (
        f"<tr class='tot'><td></td><td>TOTAL {intitule}</td>"
        f"<td></td><td>{montant}</td></tr>"
    )


def _page(contenu: str, pagination: bool = False) -> str:
    nav = "<div class='pagination'>suivant</div>" if pagination else ""
    return f"<html><body><table><tbody>{contenu}</tbody></table>{nav}</body></html>"


#: Reproduit le piege mesure: deux lignes identiques sur date, nature et
#: libelle, et distinctes par le seul montant.
PAGE = _page(
    _cle_charge("CHARGES GENERALES")
    + _depense("12/03/2025", "Entretien", "Prestation mensuelle", "120,00")
    + _depense("12/03/2025", "Entretien", "Prestation mensuelle", "240,00")
    + _depense("15/04/2025", "Eau", "Releve", "80,00", facture=False)
    + _cle_charge("ASCENSEUR 23")
    + _depense("02/02/2025", "Maintenance", "Contrat annuel", "900,00")
)


class LectureTests(unittest.TestCase):
    def test_seules_les_lignes_avec_facture_deviennent_des_pieces(self) -> None:
        lu = lire_depenses(PAGE, PROFIL_COPRODIRECTE, "P1")
        self.assertEqual(len(lu["pieces"]), 3)
        self.assertEqual(len(lu["liens"]), 4)

    def test_le_montant_est_ce_qui_evite_la_collision(self) -> None:
        """Mesure: 21 collisions sans le montant, zero avec, sur 729 lignes.

        Deux lignes de meme date, meme nature et meme libelle existent
        reellement. Une cle qui ignorerait le montant les fusionnerait, et
        ferait disparaitre un retrait sur l'une des deux.
        """
        lu = lire_depenses(PAGE, PROFIL_COPRODIRECTE, "P1")
        emplacements = [p["emplacement"] for p in lu["pieces"]]
        self.assertEqual(len(set(emplacements)), 3)
        sans_montant = {"\x1f".join(e.split("\x1f")[:4]) for e in emplacements}
        self.assertEqual(
            len(sans_montant), 2, "le piege doit bien etre present dans le gabarit"
        )

    def test_les_cles_de_charges_sont_decouvertes_et_non_declarees(self) -> None:
        """Axe 6: ferme et declarable pour les documents, ouvert pour les depenses."""
        lu = lire_depenses(PAGE, PROFIL_COPRODIRECTE, "P1")
        codes = {r["rubrique_code"] for r in lu["rubriques"]}
        self.assertEqual(codes, {"CHARGES GENERALES", "ASCENSEUR 23"})

    def test_une_ligne_sans_facture_est_enregistree_quand_meme(self) -> None:
        """Sinon une piece apparue serait indiscernable d'une depense nouvelle.

        Ce ne sont pas les memes faits: la premiere comble une lacune, la
        seconde est une depense de plus.
        """
        lu = lire_depenses(PAGE, PROFIL_COPRODIRECTE, "P1")
        manquantes = lignes_sans_facture(lu["liens"])
        self.assertEqual(len(manquantes), 1)
        self.assertIn("Releve", manquantes[0]["colonnes"])

    def test_le_rattachement_porte_la_provenance_du_syndic(self) -> None:
        """C'est la provenance manquante du modele, pas une donnee de plus."""
        lu = lire_depenses(PAGE, PROFIL_COPRODIRECTE, "P1")
        self.assertTrue(all(l["provenance"] == PROVENANCE_SYNDIC for l in lu["liens"]))
        self.assertTrue(all(l["origine"] == ORIGINE_EXTRAIT for l in lu["liens"]))

    def test_une_pagination_interdit_de_conclure_a_une_liste_complete(self) -> None:
        lu = lire_depenses(_page(_cle_charge("A") + _depense("1", "b", "c", "1,00"),
                                 pagination=True), PROFIL_COPRODIRECTE, "P1")
        self.assertEqual(lu["rubriques"][0]["cloture"], "AUCUNE")


class LignesDeServiceTests(unittest.TestCase):
    """Le defaut le plus grave du lot, trouve en executant le lecteur en vrai.

    Sur l'etat de depenses reel, 348 lignes de totaux portent exactement deux
    valeurs. Reconnues comme en-tetes de groupe, elles faisaient passer 42 cles
    de charges a 340 - et les depenses suivantes se rattachaient a une cle
    fantome **portant un montant**, qui change a chaque passage. Le journal
    aurait rendu un retrait et un ajout pour chaque piece du groupe.
    """

    PAGE = _page(
        _cle_charge("CHARGES GENERALES")
        + _depense("12/03/2025", "Entretien", "Prestation", "120,00")
        + _total("ENTRETIEN", "120,00")
        + _depense("02/04/2025", "Eau", "Releve", "60,00")
        + _cle_charge("ASCENSEUR 23")
        + _depense("02/02/2025", "Maintenance", "Contrat", "900,00")
    )

    def test_un_total_ne_devient_pas_une_cle_de_charges(self) -> None:
        lu = lire_depenses(self.PAGE, PROFIL_COPRODIRECTE, "P1")
        codes = {r["rubrique_code"] for r in lu["rubriques"]}
        self.assertEqual(codes, {"CHARGES GENERALES", "ASCENSEUR 23"})

    def test_la_depense_qui_suit_un_total_garde_sa_vraie_cle(self) -> None:
        """C'est la consequence qui compte: sans cela, l'emplacement embarquait
        un montant de total, et changeait donc a chaque passage."""
        lu = lire_depenses(self.PAGE, PROFIL_COPRODIRECTE, "P1")
        apres = [p for p in lu["pieces"] if "Releve" in p["libelle"]]
        self.assertEqual(len(apres), 1)
        self.assertEqual(apres[0]["rubrique_code"], "CHARGES GENERALES")

    def test_un_total_n_est_pas_compte_comme_depense_sans_facture(self) -> None:
        lu = lire_depenses(self.PAGE, PROFIL_COPRODIRECTE, "P1")
        self.assertEqual(len(lu["liens"]), 3)

    def test_une_depense_avant_tout_en_tete_recoit_une_cle_nommee(self) -> None:
        """Mesuree sur la page reelle: ces lignes existent.

        Une rubrique sans nom ne se lit pas a l'ecran, ne se cite pas dans une
        question au syndic, et se confondrait avec une lecture ratee.
        """
        page = _page(_depense("01/01/2025", "Divers", "Avant groupe", "10,00"))
        lu = lire_depenses(page, PROFIL_COPRODIRECTE, "P1")
        self.assertEqual(lu["rubriques"][0]["rubrique_code"], "(hors groupe)")

    def test_les_lignes_ignorees_sont_comptees_et_non_jetees(self) -> None:
        """Leur nombre est le temoin que la largeur modale est la bonne."""
        lu = lire_depenses(self.PAGE, PROFIL_COPRODIRECTE, "P1")
        self.assertEqual(lu["lignes_ignorees"], 1)
        self.assertEqual(lu["largeur_donnees"], 5)


class JournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ecrire(self, page: str, ident: str, debut: str) -> None:
        lu = lire_depenses(page, PROFIL_COPRODIRECTE, ident)
        S.ecrire_passage(
            self.instance,
            {"passage_id": ident, "editeur": "coprodirecte", "espace": "depenses",
             "debut": debut, "fin": "", "profil": "coprodirecte", "doc_id": "",
             "origine": ORIGINE_EXTRAIT},
            lu["rubriques"],
            lu["pieces"],
        )

    def test_une_facture_retiree_d_une_ligne_est_un_retrait(self) -> None:
        """Le cas que Brice a signale: les factures bougent, un voisin en fait le suivi."""
        apres = _page(
            _cle_charge("CHARGES GENERALES")
            + _depense("12/03/2025", "Entretien", "Prestation mensuelle", "120,00")
            + _depense("12/03/2025", "Entretien", "Prestation mensuelle", "240,00",
                       facture=False)
            + _depense("15/04/2025", "Eau", "Releve", "80,00", facture=False)
            + _cle_charge("ASCENSEUR 23")
            + _depense("02/02/2025", "Maintenance", "Contrat annuel", "900,00")
        )
        self._ecrire(PAGE, "P1", "2026-03-12T09:00")
        self._ecrire(apres, "P2", "2026-06-04T09:00")
        ecart = J.comparer(
            S.lire_passage(self.instance, "P1"), S.lire_passage(self.instance, "P2")
        )
        retraits = [c for c in ecart["constats"] if c["verdict"] == J.RETRAIT]
        self.assertEqual(len(retraits), 1)
        self.assertIn("240,00", retraits[0]["libelle"])

    def test_une_cle_de_charges_disparue_ne_produit_pas_de_retrait(self) -> None:
        """Axe 6 hors des valeurs observees, et c'est le comportement voulu.

        Une cle absente du second passage peut vouloir dire *plus aucune depense
        dessus* ou *cle supprimee*. Rien dans la page ne tranche, donc le
        journal ne tranche pas non plus.
        """
        apres = _page(
            _cle_charge("CHARGES GENERALES")
            + _depense("12/03/2025", "Entretien", "Prestation mensuelle", "120,00")
            + _depense("12/03/2025", "Entretien", "Prestation mensuelle", "240,00")
        )
        self._ecrire(PAGE, "P1", "2026-03-12T09:00")
        self._ecrire(apres, "P2", "2026-06-04T09:00")
        ecart = J.comparer(
            S.lire_passage(self.instance, "P1"), S.lire_passage(self.instance, "P2")
        )
        ascenseur = [c for c in ecart["constats"] if c["rubrique_code"] == "ASCENSEUR 23"]
        self.assertEqual(len(ascenseur), 1)
        self.assertEqual(ascenseur[0]["verdict"], J.INDETERMINE)
        self.assertEqual(ascenseur[0]["motif"], J.MOTIF_NON_PARCOURUE)


class SansJustificatifTests(unittest.TestCase):
    """Le seul manque que l'observation sait produire sans rien declarer.

    Il ne demande ni rattachement, ni nombre attendu: il suffit de lire la
    page. C'est ce qui en fait le premier constat utilisable, et c'est pour
    cela que `lignes_sans_facture` a ete branchee a la facade plutot que
    supprimee comme code mort.
    """

    def test_le_compte_voyage_avec_son_perimetre(self) -> None:
        """Un compte de lignes sans justificatif, sans le nombre de lignes
        lues, se lit comme une couverture complete."""
        rendu = X.depenses_sans_justificatif(PAGE)
        self.assertEqual(rendu["lignes_lues"], 4)
        self.assertEqual(rendu["sans_justificatif"], 1)
        self.assertEqual(rendu["cles_de_charges"], ["CHARGES GENERALES"])

    def test_une_page_sans_depense_ne_rend_pas_un_faux_zero(self) -> None:
        """Zero ligne sans justificatif sur zero ligne lue n'est pas un bon
        resultat: c'est une absence de mesure, et les deux comptes le disent."""
        rendu = X.depenses_sans_justificatif("<html><body></body></html>")
        self.assertEqual(rendu["lignes_lues"], 0)
        self.assertEqual(rendu["sans_justificatif"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
