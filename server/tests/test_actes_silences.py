"""Les defauts muets du modele des actes, chacun avec sa mesure.

Ces tests sont ecrits contre l'audit du 2026-09-04. Chaque nom dit le fait que
le produit ne doit plus pouvoir produire, et chacun echoue sur le code
d'avant - c'est la seule facon de savoir qu'une correction corrige au lieu de
deplacer.

Le fil commun des onze defauts couverts ici: aucun ne levait d'exception.
Ils rendaient tous une valeur plausible - une vraie date d'assemblee, un vrai
montant du document, un ecran vert, une liste vide - et c'est ce qui les
rendait couteux.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.vault import gouvernance_store as G


class _Instance:
    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()


def _acte(acte_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "acte_id": acte_id, "nature": "RESOLUTION_AG", "etat": "CONSTATEE",
        "portee": "ORDINAIRE", "date_effet": "2024-07-03", "exercice": "2024",
        "ag_id": "AG-2024-07-03", "numero": "12", "sous_numero": "",
        "objet": "Ravalement de la facade sud", "montant_autorise": "",
        "entreprise": "", "montant_source": "", "entreprise_source": "",
        "valide_du": "", "valide_au": "", "majorite_annoncee": "24",
        "majorite_requise": "24", "majorite_appliquee": "24",
        "resultat": "ADOPTEE", "resolution_id": "", "page": "4", "ancre": "",
        "confiance": "forte", "doc_id": "DOC-PV", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _dossier(dossier_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "dossier_id": dossier_id, "exercice": "2024",
        "date_depense": "2024-09-15", "montant_ttc": "2000.00",
        "fournisseur": "WE GROUP", "libelle": "Ravalement",
        "imputation": "VOTE_SEPARE", "imputation_motif": "",
        "aiguillage": "ART_44", "facture_doc_id": "", "ecriture_ref": "",
        "page": "", "ancre": "", "doc_id": "DOC-FAC", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _lien(source: str, relation: str, cible: str, **kw: str) -> dict[str, str]:
    provenance = kw.pop("provenance", "COPROSCOPE_CALCULE")
    target_kind = kw.pop("target_kind", "dossier")
    ligne = {
        "lien_id": A.lien_id("acte", source, relation, target_kind, cible,
                             provenance),
        "source_kind": "acte", "source_id": source, "relation": relation,
        "target_kind": target_kind, "target_id": cible, "provenance": provenance,
        "force_probatoire": "PIECE_PRODUITE", "motif": "", "doute": "",
        "montant_impute": "", "libelle_cible": "", "echeance": "",
        "constate_le": "2024-09-20", "auteur": "", "page": "", "ancre": "",
        "doc_id": "DOC-FAC", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


class _Coffre(unittest.TestCase):
    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=False)

    def codes(self) -> set[str]:
        return {c["code"] for c in A.constats(self.instance)}

    def motif(self, code: str) -> str:
        return next(c["motif"] for c in A.constats(self.instance)
                    if c["code"] == code)


class UneDateAbsenteNeFabriquePasUneEcheanceTests(_Coffre):
    """C032. `x.date_effet > a.date_effet` avec `a.date_effet` vide rendait
    toute date superieure, donc MIN() rendait la premiere assemblee CONNUE."""

    def _base(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-AG-2019", portee="APPROBATION_COMPTES",
                  date_effet="2019-06-01"),
            _acte("ACTE-AG-2025", portee="APPROBATION_COMPTES",
                  date_effet="2025-06-01", numero="13"),
            _acte("ACTE-CS-SANS-DATE", nature="DECISION_CS_DELEGUEE",
                  date_effet="", numero="14"),
        ], ["DOC-PV"])

    def test_l_echeance_d_un_acte_sans_date_n_est_pas_la_plus_ancienne_assemblee(self) -> None:
        self._base()
        echeances = {
            l["acte_id"]: l["echeance"]
            for l in A.lire_vue(self.instance, "v_liens_manquants")
            if l["regle"] == "AG_APPROBATION_COMPTES"
        }
        self.assertEqual(echeances["ACTE-CS-SANS-DATE"], "")

    def test_aucun_manquement_n_est_date_avant_l_acte_qui_le_porterait(self) -> None:
        self._base()
        self.assertNotIn("OBLIGATION_NON_TENUE", self.codes())
        self.assertIn("ECHEANCE_INCALCULABLE", self.codes())
        self.assertIn("n'a pas ete lue", self.motif("ECHEANCE_INCALCULABLE"))

    def test_une_urgence_sans_date_n_accuse_pas_le_syndic(self) -> None:
        """Le motif sortait troue - `engagee en urgence le  :` - et affirmait
        qu'aucune assemblee ne s'etait tenue depuis une date qu'il n'avait pas."""
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-URG-SANS-DATE", nature="URGENCE_SYNDIC", date_effet=""),
        ], ["DOC-PV"])
        self.assertNotIn("URGENCE_JAMAIS_PORTEE", self.codes())
        self.assertIn("ECHEANCE_INCALCULABLE", self.codes())

    def test_aucun_motif_de_constat_ne_porte_de_date_vide(self) -> None:
        self._base()
        for constat in A.constats(self.instance):
            self.assertNotIn(" du  ", constat["motif"], constat["code"])
            self.assertNotIn(" le  ", constat["motif"], constat["code"])


class UnActeProjeteNePorteAucunManquementTests(_Coffre):
    """C067. Une convocation ne vote pas: une resolution seulement proposee ne
    peut pas avoir manque a une obligation qu'elle n'a pas encore creee."""

    def test_une_decision_projetee_ne_produit_ni_fondement_ni_obligation(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-CS-PROJ", nature="DECISION_CS_DELEGUEE",
                  etat="PROJETEE", date_effet="2026-05-01"),
            _acte("ACTE-AG-COMPTES", portee="APPROBATION_COMPTES",
                  date_effet="2026-06-01", numero="13"),
        ], ["DOC-PV"])
        self.assertEqual(self.codes() & {"ACTE_SANS_FONDEMENT",
                                         "OBLIGATION_NON_TENUE"}, set())


class LaCleDesActesPorteLEtatTests(_Coffre):
    """C024. `acte_id_resolution` derive le meme identifiant pour le projet lu
    dans la convocation et le constat lu dans le proces-verbal."""

    def test_le_proces_verbal_n_ecrase_pas_le_projet_de_la_convocation(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-AG-2024-07-03-R12", etat="PROJETEE",
                  montant_autorise="18240.00", resultat="",
                  doc_id="DOC-CONVOC"),
        ], ["DOC-CONVOC"])
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-AG-2024-07-03-R12", etat="CONSTATEE",
                  montant_autorise="", resultat="ADOPTEE", doc_id="DOC-PV"),
        ], ["DOC-PV"])
        par_etat = {l["etat"]: l for l in A.lire_table(self.instance,
                                                       A.TABLE_ACTES)}
        self.assertEqual(set(par_etat), {"PROJETEE", "CONSTATEE"})
        self.assertEqual(par_etat["PROJETEE"]["montant_autorise"], "18240.00")

    def test_la_matrice_ne_confond_pas_les_deux_etats_du_meme_acte(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-AG-2024-07-03-R12", etat="PROJETEE", resultat="",
                  doc_id="DOC-CONVOC"),
        ], ["DOC-CONVOC"])
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-AG-2024-07-03-R12", etat="CONSTATEE", doc_id="DOC-PV"),
        ], ["DOC-PV"])
        lignes = A.lire_vue(self.instance, "v_matrice_gouvernance")
        self.assertEqual(len(lignes), 2)
        self.assertEqual({l["etat"] for l in lignes},
                         {"PROJETEE", "CONSTATEE"})


class LIdentiteNeDependPasDeLEcritureDeLaDateTests(unittest.TestCase):
    """C025. `03/07/2024` et `2024-07-03` fabriquaient deux actes pour une
    seule resolution, donc une assemblee de plus dans tous les comptages."""

    def test_deux_ecritures_de_la_meme_date_donnent_le_meme_acte(self) -> None:
        self.assertEqual(A.acte_id_resolution("03/07/2024", "12"),
                         A.acte_id_resolution("2024-07-03", "12"))

    def test_une_date_illisible_ne_devient_pas_un_identifiant(self) -> None:
        with self.assertRaises(ValueError):
            A.acte_id_resolution("3 juillet 2024", "12")


class LesReglesDeDroitComparentDesDatesOrdonnablesTests(_Coffre):
    """C035. Toute regle du modele est une comparaison de chaines, et rien
    n'imposait un format: le commentaire `ISO` etait une intention."""

    def test_une_date_francaise_est_rangee_en_iso(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", date_effet="15/11/2024")], ["DOC-PV"])
        self.assertEqual(
            A.lire_table(self.instance, A.TABLE_ACTES)[0]["date_effet"],
            "2024-11-15")

    def test_une_date_non_ordonnable_est_refusee_au_lieu_d_etre_rangee(self) -> None:
        with self.assertRaises(ValueError):
            A.ecrire(self.instance, A.TABLE_ACTES,
                     [_acte("A1", date_effet="le 15 novembre")], ["DOC-PV"])

    def test_une_urgence_datee_a_la_francaise_trouve_son_assemblee(self) -> None:
        """Mesure d'origine: '05/01/2025' > '15/11/2024' est faux en
        comparaison textuelle, donc le constat accusait le syndic de n'avoir
        tenu aucune assemblee alors qu'une assemblee avait eu lieu."""
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-URG", nature="URGENCE_SYNDIC", date_effet="15/11/2024"),
            _acte("ACTE-AG-SUIV", date_effet="05/01/2025", numero="13"),
        ], ["DOC-PV"])
        self.assertNotIn("URGENCE_JAMAIS_PORTEE", self.codes())
        self.assertIn("2025-01-05", self.motif("OBLIGATION_NON_TENUE"))


class DeuxLignesDeMemeCleNeSEcrasentPasEnSilenceTests(_Coffre):
    """C044 / C055. `INSERT OR REPLACE` en gardait une et jetait l'autre, et le
    journal rapportait le nombre soumis."""

    def test_deux_lignes_du_meme_lot_de_meme_cle_sont_refusees(self) -> None:
        with self.assertRaises(ValueError) as leve:
            A.ecrire(self.instance, A.TABLE_ACTES,
                     [_acte("A1"), _acte("A1", objet="Autre resolution")],
                     ["DOC-PV"])
        self.assertIn("meme lot", str(leve.exception))

    def test_le_magasin_rend_le_nombre_stocke_et_non_le_nombre_soumis(self) -> None:
        champs = ["resolution_id", "etat", "doc_id", "origine"]
        ligne = {"resolution_id": "R3", "etat": "CONSTATEE",
                 "doc_id": "D1", "origine": "EXTRAIT"}
        rendu = G.remplacer_pour_documents(
            self.instance, champs, [ligne, dict(ligne)], ["D1"])
        self.assertEqual(rendu, 1)


class LeDevisRetenuEstLePlusProbantTests(_Coffre):
    """C034. `LIMIT 1` sans ORDER BY: la cellule disait `confirme par un
    humain` a cote d'un montant pris chez le syndic."""

    def test_l_acte_effectif_et_la_cellule_designent_la_meme_assertion(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", portee="ENGAGEMENT_DEPENSE")], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("A1", "DEVIS_RETENU", "DEV-CHER", target_kind="document",
                  provenance="SYNDIC_AFFIRME",
                  force_probatoire="AFFIRME_SANS_PIECE",
                  montant_impute="22200.00", libelle_cible="ENTREPRISE CHERE"),
            _lien("A1", "DEVIS_RETENU", "DEV-RETENU", target_kind="document",
                  provenance="HUMAIN_CONFIRME",
                  force_probatoire="PIECE_PRODUITE",
                  montant_impute="18240.00", libelle_cible="ENTREPRISE RETENUE"),
        ], ["DOC-FAC"])
        effectif = A.lire_vue(self.instance, "v_acte_effectif")[0]
        self.assertEqual(effectif["montant_effectif"], "18240.00")
        self.assertEqual(effectif["entreprise_effective"], "ENTREPRISE RETENUE")


class UnControleQuiNePeutPasSExercerLeDitTests(_Coffre):
    """C020. Une file de travail vide se lisait `tout a ete execute`."""

    def test_une_resolution_sans_montant_lu_sort_du_controle_en_le_disant(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", portee="ENGAGEMENT_DEPENSE",
                        montant_autorise="")], ["DOC-PV"])
        self.assertNotIn("ACTE_SANS_EXECUTION", self.codes())
        self.assertIn("EXECUTION_NON_CONTROLABLE", self.codes())
        self.assertIn("pas l'absence de manquement",
                      self.motif("EXECUTION_NON_CONTROLABLE"))

    def test_une_resolution_chiffree_reste_un_vrai_manquement(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", portee="ENGAGEMENT_DEPENSE",
                        montant_autorise="18240.00")], ["DOC-PV"])
        self.assertIn("ACTE_SANS_EXECUTION", self.codes())
        self.assertNotIn("EXECUTION_NON_CONTROLABLE", self.codes())


class LaDelegationEstBorneeParSaPeriodeTests(_Coffre):
    """C028 et C065. Le motif du retrait du controle de seuil promettait
    `deux ans au plus (art. 21-3)`; aucune comparaison de duree n'existait."""

    def _delegation(self, **kw: str) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("DEL", portee="DELEGATION_CS", date_effet="2023-01-15",
                  montant_autorise="5000.00", **kw),
            _acte("DEC", nature="DECISION_CS_DELEGUEE",
                  date_effet="2024-03-01", numero="13"),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_DOSSIERS,
                 [_dossier("D1", date_depense="2024-06-01")], ["DOC-FAC"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("DEC", "FONDE_PAR", "DEL", target_kind="acte"),
            _lien("DEC", "AUTORISE", "D1"),
        ], ["DOC-FAC"])

    def test_une_delegation_de_plus_de_deux_ans_est_un_constat(self) -> None:
        self._delegation(valide_du="2023-01-15", valide_au="2026-01-15")
        self.assertIn("DELEGATION_TROP_LONGUE", self.codes())
        self.assertIn("21-3", self.motif("DELEGATION_TROP_LONGUE"))

    def test_une_delegation_de_deux_ans_ne_l_est_pas(self) -> None:
        self._delegation(valide_du="2023-01-15", valide_au="2025-01-15")
        self.assertNotIn("DELEGATION_TROP_LONGUE", self.codes())

    def test_une_periode_non_lue_est_nommee_au_lieu_d_etre_ignoree(self) -> None:
        self._delegation()
        self.assertIn("DELEGATION_SANS_PERIODE", self.codes())
        self.assertIn("sans borne de date",
                      self.motif("DELEGATION_SANS_PERIODE"))

    def test_un_depassement_ne_dit_sur_la_periode_que_s_il_en_a_une(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("DEL", portee="DELEGATION_CS", date_effet="2023-01-15",
                  montant_autorise="1000.00"),
            _acte("DEC", nature="DECISION_CS_DELEGUEE",
                  date_effet="2024-03-01", numero="13"),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [_dossier("D1")], ["DOC-FAC"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("DEC", "FONDE_PAR", "DEL", target_kind="acte"),
            _lien("DEC", "AUTORISE", "D1"),
        ], ["DOC-FAC"])
        motif = self.motif("PLAFOND_DEPASSE")
        self.assertIn("faute de periode lue", motif)
        self.assertNotIn("sur la periode du", motif)


class UneIssueNonTraceeNEstPasUnePieceManquanteTests(_Coffre):
    """C066. Le cinquieme etat de resultat tombait dans l'`ELSE 'ABSENT'`."""

    def test_sans_issue_tracee_a_sa_cellule_et_son_constat(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", resultat="SANS_ISSUE_TRACEE")], ["DOC-PV"])
        ligne = A.lire_vue(self.instance, "v_matrice_gouvernance")[0]
        self.assertNotEqual(ligne["cel_resolution"], "ABSENT")
        self.assertIn("ISSUE_NON_TRACEE", self.codes())
        self.assertIn("constat sur le document", self.motif("ISSUE_NON_TRACEE"))


class UneIssueNonLueAppelleUneRelectureEtNonUneQuestionTests(_Coffre):
    """Le sixieme etat de resultat, et le seul dont la reparation est chez nous.

    `ISSUE_NON_LUE` dit que le proces-verbal ENONCE une issue et que la chaine
    n'a pas su la lire. Le lot qui l'a introduit lui a donne sa cellule
    `AFFIRME_SANS_PIECE` et s'est arrete la: l'acte produisait un « A confirmer »
    de plus dans une matrice qui en porte des centaines, et **aucune ligne de
    travail**. C'est le defaut que la classe precedente decrit pour le cinquieme
    etat, repose tel quel un etat plus loin.

    Ces trois tests tiennent les trois choses qui le distinguent de ses voisins:
    il existe, il n'accuse personne, et il ne parle pas d'un document a venir.
    """

    def test_une_issue_non_lue_fait_naitre_une_ligne_de_travail(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", resultat="ISSUE_NON_LUE")], ["DOC-PV"])
        ligne = A.lire_vue(self.instance, "v_matrice_gouvernance")[0]
        self.assertEqual(ligne["cel_resolution"], "AFFIRME_SANS_PIECE")
        self.assertIn("ISSUE_NON_LUE_A_RELIRE", self.codes())

    def test_le_motif_met_le_defaut_a_notre_charge_et_pas_a_celle_du_syndic(
        self,
    ) -> None:
        """Le motif est lu par un coproprietaire qui n'a pas ecrit ce logiciel.

        Il doit pouvoir en tirer le geste juste - relire la piece qu'il a - et
        surtout pas le geste faux, reclamer au syndic une conclusion qui est
        deja au proces-verbal.
        """
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", resultat="ISSUE_NON_LUE")], ["DOC-PV"])
        motif = self.motif("ISSUE_NON_LUE_A_RELIRE")
        self.assertIn("le logiciel n'a pas su lire sa conclusion", motif)
        self.assertIn("relecture humaine", motif)
        self.assertIn("ni une piece manquante", motif)
        self.assertIn("ni un silence du syndic", motif)

    def test_une_resolution_seulement_projetee_n_a_rien_dont_la_lecture_ait_echoue(
        self,
    ) -> None:
        """La garde `etat <> PROJETEE`, celle des deux branches voisines.

        Une convocation ne conclut pas: il n'y a pas de conclusion qu'on aurait
        mal lue, et reclamer une relecture reviendrait a envoyer un
        coproprietaire chercher dans un proces-verbal qui n'existe pas encore.
        """
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("A-PROJET", etat="PROJETEE", resultat="ISSUE_NON_LUE"),
        ], ["DOC-CONVOC"])
        self.assertNotIn("ISSUE_NON_LUE_A_RELIRE", self.codes())


class LaFileEstTrieeParMontantEnJeuTests(_Coffre):
    """C059. L'ecart signe mettait -99 000 apres +200."""

    def test_le_plus_gros_ecart_arrive_en_premier(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("A-PETIT", portee="ENGAGEMENT_DEPENSE",
                  montant_autorise="500.00"),
            _acte("A-GROS", portee="ENGAGEMENT_DEPENSE",
                  montant_autorise="100000.00", numero="13"),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [
            _dossier("D-PETIT", montant_ttc="700.00"),
            _dossier("D-GROS", montant_ttc="1000.00"),
        ], ["DOC-FAC"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("A-PETIT", "AUTORISE", "D-PETIT"),
            _lien("A-GROS", "AUTORISE", "D-GROS"),
        ], ["DOC-FAC"])
        divergents = [c for c in A.constats(self.instance)
                      if c["code"] == "MONTANT_DIVERGENT"]
        self.assertEqual(divergents[0]["sujet_id"], "A-GROS")

if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class UnProjetDeResolutionNAPasDeProcesVerbalATenirTests(_Coffre):
    """Un acte PROJETEE ne se voit pas reprocher ce qu'un PV aurait du dire.

    Defaut mesure le 2026-09-05 sur le coffre reel, effet de bord de la
    fermeture de C061: sur 22 constats `MAJORITE_NON_ENONCEE` emis, 18
    portaient sur un acte dont le seul etat est `PROJETEE` - un projet de
    resolution lu dans une CONVOCATION. Le motif rendu disait pourtant
    « aucune majorite n'est enoncee par le proces-verbal », a propos d'un
    document qui n'existe pas encore.

    Les trois branches voisines du meme SQL - PORTEE_NON_LUE,
    ISSUE_NON_ENONCEE, ISSUE_NON_TRACEE - portent la garde `etat <> PROJETEE`
    depuis leur ecriture. Celle de la majorite ne l'avait pas. Fermer C061 n'a
    pas cree ce manque: il l'a rendu nuisible, en faisant passer le compteur de
    zero a vingt-deux.

    Apres correction, la meme base rend 4 constats au lieu de 22.
    """

    def test_un_acte_projete_ne_produit_aucun_constat_de_majorite(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("A-PROJET", etat="PROJETEE", majorite_annoncee="NON_ENONCEE"),
        ], ["DOC-CONVOC"])
        self.assertNotIn("MAJORITE_NON_ENONCEE", self.codes())

    def test_le_meme_acte_constate_le_produit(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("A-TENUE", etat="CONSTATEE", majorite_annoncee="NON_ENONCEE"),
        ], ["DOC-PV"])
        self.assertIn("MAJORITE_NON_ENONCEE", self.codes())
