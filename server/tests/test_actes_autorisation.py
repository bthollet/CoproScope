"""Le modele relationnel actes / depenses / liens, eprouve sur ses promesses.

Chaque test porte le nom de la promesse qu'il tient, pas celui de la fonction
qu'il appelle. Un test qui echoue doit dire ce que le produit ne fait plus.
"""

from __future__ import annotations

import shutil

import tempfile
import unittest
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.modules import _actes_requetes as R
from coproscope.vault import gouvernance_store as G


class _Instance:
    """Instance minimale: seul le coffre local compte pour ce magasin."""

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
        "valide_du": "", "valide_au": "", "majorite_requise": "24",
        "majorite_appliquee": "24", "resultat": "ADOPTEE", "resolution_id": "",
        "page": "4", "ancre": "", "confiance": "forte",
        "doc_id": "DOC-PV", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _dossier(dossier_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "dossier_id": dossier_id, "exercice": "2024",
        "date_depense": "2024-09-15", "montant_ttc": "18240.00",
        "fournisseur": "WE GROUP", "libelle": "Ravalement facade sud",
        "imputation": "VOTE_SEPARE", "imputation_motif": "", "aiguillage": "ART_44",
        "facture_doc_id": "DOC-FAC", "ecriture_ref": "", "page": "",
        "ancre": "", "doc_id": "DOC-FAC", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _lien(source: str, relation: str, cible: str, **kw: str) -> dict[str, str]:
    provenance = kw.pop("provenance", "COPROSCOPE_CALCULE")
    target_kind = kw.pop("target_kind", "dossier")
    ligne = {
        "lien_id": A.lien_id("acte", source, relation, target_kind, cible, provenance),
        "source_kind": "acte", "source_id": source, "relation": relation,
        "target_kind": target_kind, "target_id": cible, "provenance": provenance,
        "force_probatoire": "PIECE_PRODUITE", "motif": "", "doute": "",
        "montant_impute": "", "libelle_cible": "", "echeance": "",
        "constate_le": "2024-09-20", "auteur": "", "page": "", "ancre": "",
        "doc_id": "DOC-FAC", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


class SocleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        # Une connexion non fermee laisse le fichier verrouille sous Windows, et
        # l'erreur sort ici plutot qu'a l'endroit qui la cause.
        shutil.rmtree(self.racine, ignore_errors=False)

    # -- creation et idempotence -------------------------------------------

    def test_la_creation_pose_les_cinq_tables_et_les_vues(self) -> None:
        A.preparer(self.instance)
        with A.connexion(self.instance) as cx:
            noms = {
                r[0] for r in cx.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
                )
            }
        for table in ("actes_autorisation", "attributs_acte", "liens_gouvernance",
                      "dossiers_depense", "traces_controle"):
            self.assertIn(table, noms)
        for vue in ("v_actes", "v_acte_effectif", "v_liens_manquants",
                    "v_cumul_delegation", "v_execution", "v_matrice_gouvernance",
                    "v_constats", "v_taux_gouvernance"):
            self.assertIn(vue, noms)

    def test_preparer_deux_fois_ne_perd_rien(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [_acte("ACTE-1")], ["DOC-PV"])
        A.preparer(self.instance)
        A.preparer(self.instance)
        self.assertEqual(len(A.lire_table(self.instance, A.TABLE_ACTES)), 1)

    def test_les_quatre_tables_existantes_ne_sont_pas_touchees(self) -> None:
        """Migration: les voies resolutions et convocations continuent."""
        champs = ["resolution_id", "ag_id", "doc_id", "position", "etat", "origine"]
        G.remplacer_pour_documents(
            self.instance, champs,
            [{"resolution_id": "R1", "ag_id": "AG-2024-07-03", "doc_id": "DOC-PV",
              "position": "1", "etat": "CONSTATEE", "origine": "EXTRAIT"}],
            ["DOC-PV"],
        )
        A.preparer(self.instance)
        A.ecrire(self.instance, A.TABLE_ACTES, [_acte("ACTE-1")], ["DOC-PV"])
        self.assertEqual(len(G.lire(self.instance)), 1)

    def test_la_base_absente_rend_une_liste_vide_et_non_une_erreur(self) -> None:
        self.assertEqual(A.constats(self.instance), [])

    # -- decision back n. 2: les corrections humaines survivent -------------

    def test_une_ligne_corrigee_survit_a_la_reextraction(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-1", montant_autorise="18240.00"),
            _acte("ACTE-1", origine="CORRIGE_HUMAIN", montant_autorise="22200.00"),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("ACTE-1", montant_autorise="18240.00")], ["DOC-PV"])
        origines = sorted(l["origine"] for l in A.lire_table(self.instance, A.TABLE_ACTES))
        self.assertEqual(origines, ["CORRIGE_HUMAIN", "EXTRAIT"])

    def test_la_correction_humaine_gagne_a_la_lecture(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-1", montant_autorise="18240.00"),
            _acte("ACTE-1", origine="CORRIGE_HUMAIN", montant_autorise="22200.00"),
        ], ["DOC-PV"])
        lignes = A.lire_vue(self.instance, "v_actes", [("origine", "ne", "IMPOSSIBLE")])
        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes[0]["montant_autorise"], "22200.00")

    def test_la_divergence_reste_visible_apres_correction(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-1", montant_autorise="18240.00"),
            _acte("ACTE-1", origine="CORRIGE_HUMAIN", montant_autorise="22200.00"),
        ], ["DOC-PV"])
        with A.connexion(self.instance) as cx:
            lignes = [dict(r) for r in cx.execute("SELECT * FROM v_divergences_humaines")]
        champs = {l["champ"]: (l["valeur_machine"], l["valeur_humaine"]) for l in lignes}
        self.assertEqual(champs["montant_autorise"], ("18240.00", "22200.00"))

    def test_une_trace_humaine_ne_derive_d_aucun_document(self) -> None:
        """Elle s'ecrit sans `doc_ids`, donc rien ne peut l'effacer par document."""
        A.ecrire(self.instance, A.TABLE_TRACES, [{
            "trace_id": "T1", "sujet_kind": "acte", "sujet_id": "ACTE-1",
            "verdict": "CONTROLE_TRACE", "texte": "Verifie contre l'annexe 2.",
            "auteur": "conseil syndical", "constate_le": "2026-09-03",
            "doc_id": "", "origine": "CORRIGE_HUMAIN",
        }], [])
        A.ecrire(self.instance, A.TABLE_ACTES, [_acte("ACTE-1")], ["DOC-PV"])
        self.assertEqual(len(A.lire_table(self.instance, A.TABLE_TRACES)), 1)

    # -- assertions concurrentes -------------------------------------------

    def test_deux_assertions_concurrentes_coexistent_sur_la_meme_paire(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [_acte("ACTE-1")], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [_dossier("DEP-1")], ["DOC-FAC"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("ACTE-1", "AUTORISE", "DEP-1", provenance="SYNDIC_AFFIRME",
                  motif="Le syndic impute cette facture a la resolution 12."),
            _lien("ACTE-1", "AUTORISE", "DEP-1", provenance="COPROSCOPE_CALCULE",
                  doute="Montant paye superieur au montant vote.",
                  motif="Fournisseur identique, montant divergent de 5 220,00 EUR."),
        ], ["DOC-FAC"])
        liens = A.actes_du_dossier(self.instance, "DEP-1")
        self.assertEqual(len(liens), 2)
        self.assertEqual(
            [l["provenance"] for l in liens],
            ["COPROSCOPE_CALCULE", "SYNDIC_AFFIRME"],
        )

    def test_une_contradiction_humaine_neutralise_la_paire_qu_elle_vise(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("DELEG", portee="DELEGATION_CS", montant_autorise="5000.00",
                  valide_du="2023-06-01", valide_au="2025-05-31"),
            _acte("CS-1", nature="DECISION_CS_DELEGUEE", date_effet="2024-03-10",
                  numero="", resultat=""),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("CS-1", "FONDE_PAR", "DELEG", target_kind="acte"),
        ], ["DOC-PV"])
        with A.connexion(self.instance) as cx:
            avant = [dict(r) for r in cx.execute(
                "SELECT relation FROM v_liens_manquants WHERE acte_id='CS-1'")]
            self.assertNotIn("FONDE_PAR", [r["relation"] for r in avant])
            A.ecrire(self.instance, A.TABLE_LIENS, [
                _lien("CS-1", "FONDE_PAR", "DELEG", target_kind="acte",
                      provenance="HUMAIN_CONTREDIT", origine="CORRIGE_HUMAIN"),
            ], [])
        with A.connexion(self.instance) as cx:
            apres = [dict(r) for r in cx.execute(
                "SELECT relation FROM v_liens_manquants WHERE acte_id='CS-1'")]
        self.assertIn("FONDE_PAR", [r["relation"] for r in apres])

    # -- natures derivees et leurs liens obligatoires -----------------------

    def test_une_resolution_d_ag_n_exige_aucun_lien(self) -> None:
        """Une seule nature est autonome, et cela se lit dans le schema."""
        A.ecrire(self.instance, A.TABLE_ACTES, [_acte("ACTE-1")], ["DOC-PV"])
        with A.connexion(self.instance) as cx:
            lignes = [dict(r) for r in cx.execute("SELECT * FROM v_liens_manquants")]
        self.assertEqual(lignes, [])

    def test_un_acte_derive_prive_de_son_lien_arriere_produit_un_constat(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("CS-1", nature="DECISION_CS_DELEGUEE", date_effet="2024-03-10",
                  objet="Remplacement de la pompe du local technique",
                  montant_autorise="3200.00", numero="", resultat=""),
        ], ["DOC-CR"])
        codes = {c["code"] for c in A.constats(self.instance)}
        self.assertIn("ACTE_SANS_FONDEMENT", codes)

    def test_l_obligation_a_echeance_non_tenue_devient_un_manquement_date(self) -> None:
        """Aucun humain ne saisit ce manquement: il tombe de l'absence de lien."""
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("DELEG", portee="DELEGATION_CS", montant_autorise="5000.00",
                  date_effet="2023-06-01", valide_du="2023-06-01",
                  valide_au="2025-05-31"),
            _acte("CS-1", nature="DECISION_CS_DELEGUEE", date_effet="2024-03-10",
                  montant_autorise="3200.00", numero="", resultat=""),
            _acte("AG-COMPTES", portee="APPROBATION_COMPTES",
                  date_effet="2025-06-20", numero="3"),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("CS-1", "FONDE_PAR", "DELEG", target_kind="acte"),
        ], ["DOC-PV"])
        constats = {c["code"]: c for c in A.constats(self.instance, aujourd_hui="2026-09-03")}
        manquement = constats["OBLIGATION_NON_TENUE"]
        self.assertEqual(manquement["date_echeance"], "2025-06-20")
        self.assertEqual(manquement["date_fait"], "2024-03-10")
        self.assertIn("2025-06-20", manquement["motif"])
        self.assertEqual(manquement["anciennete_jours"], 907)

    def test_une_urgence_qui_n_atteint_aucune_assemblee_est_un_manquement(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("URG-1", nature="URGENCE_SYNDIC", date_effet="2025-01-08",
                  objet="Reparation de la colonne d'eau", montant_autorise="480.00",
                  numero="", resultat=""),
        ], ["DOC-FAC"])
        constats = {c["code"] for c in A.constats(self.instance)}
        self.assertIn("URGENCE_JAMAIS_PORTEE", constats)

    def test_une_delegation_expiree_est_nommee_a_part(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("DELEG", portee="DELEGATION_CS", montant_autorise="5000.00",
                  date_effet="2021-06-01", valide_du="2021-06-01",
                  valide_au="2023-05-31"),
            _acte("CS-1", nature="DECISION_CS_DELEGUEE", date_effet="2024-03-10",
                  montant_autorise="900.00", numero="", resultat=""),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("CS-1", "FONDE_PAR", "DELEG", target_kind="acte"),
        ], ["DOC-PV"])
        codes = {c["code"] for c in A.constats(self.instance)}
        self.assertIn("DELEGATION_EXPIREE", codes)
        self.assertNotIn("ACTE_SANS_FONDEMENT", codes)

    # -- decision back n. 1: transverse aux exercices ------------------------

    def test_le_cumul_se_calcule_sur_la_periode_et_traverse_les_exercices(self) -> None:
        """Une delegation votee en 2023 couvre une depense de 2024."""
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("DELEG", portee="DELEGATION_CS", exercice="2023",
                  date_effet="2023-06-01", valide_du="2023-06-01",
                  valide_au="2025-05-31", montant_autorise="5000.00"),
            _acte("CS-1", nature="DECISION_CS_DELEGUEE", exercice="2024",
                  date_effet="2024-03-10", numero="", resultat=""),
            _acte("CS-2", nature="DECISION_CS_DELEGUEE", exercice="2024",
                  date_effet="2024-11-02", numero="", resultat=""),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [
            _dossier("DEP-1", exercice="2024", date_depense="2024-03-20",
                     montant_ttc="3200.00"),
            _dossier("DEP-2", exercice="2024", date_depense="2024-11-10",
                     montant_ttc="2400.00"),
            # Hors periode: postérieure a la fin de la delegation.
            _dossier("DEP-3", exercice="2025", date_depense="2025-09-01",
                     montant_ttc="9999.00"),
        ], ["DOC-FAC"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("CS-1", "FONDE_PAR", "DELEG", target_kind="acte"),
            _lien("CS-2", "FONDE_PAR", "DELEG", target_kind="acte"),
            _lien("CS-1", "AUTORISE", "DEP-1"),
            _lien("CS-2", "AUTORISE", "DEP-2"),
            _lien("CS-2", "AUTORISE", "DEP-3"),
        ], ["DOC-FAC"])
        cumuls = A.cumul_delegations(self.instance)
        self.assertEqual(len(cumuls), 1)
        self.assertAlmostEqual(cumuls[0]["cumul"], 5600.00, places=2)
        self.assertAlmostEqual(cumuls[0]["plafond"], 5000.00, places=2)
        codes = {c["code"] for c in A.constats(self.instance)}
        self.assertIn("PLAFOND_DEPASSE", codes)

    def test_le_depassement_ne_se_voit_pas_ligne_a_ligne(self) -> None:
        """Chaque depense est sous le plafond; seul le cumul le franchit."""
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("DELEG", portee="DELEGATION_CS", date_effet="2023-06-01",
                  valide_du="2023-06-01", valide_au="2025-05-31",
                  montant_autorise="5000.00"),
            _acte("CS-1", nature="DECISION_CS_DELEGUEE", date_effet="2024-03-10",
                  numero="", resultat=""),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [
            _dossier("DEP-1", date_depense="2024-03-20", montant_ttc="2600.00"),
            _dossier("DEP-2", date_depense="2024-04-20", montant_ttc="2700.00"),
        ], ["DOC-FAC"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("CS-1", "FONDE_PAR", "DELEG", target_kind="acte"),
            _lien("CS-1", "AUTORISE", "DEP-1"),
            _lien("CS-1", "AUTORISE", "DEP-2"),
        ], ["DOC-FAC"])
        for dossier in A.lire_vue(self.instance, "v_dossiers",
                                  [("depense_exercice", "eq", "2024")]):
            self.assertLess(float(dossier["montant_ttc"]), 5000.00)
        self.assertIn("PLAFOND_DEPASSE", {c["code"] for c in A.constats(self.instance)})

    # -- l'euro et l'acte ---------------------------------------------------

    def test_un_euro_sans_acte_est_un_constat_chiffre(self) -> None:
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [_dossier("DEP-1")], ["DOC-FAC"])
        constats = {c["code"]: c for c in A.constats(self.instance)}
        self.assertIn("EURO_SANS_ACTE", constats)
        self.assertAlmostEqual(constats["EURO_SANS_ACTE"]["montant_en_jeu"], 18240.0)

    def test_une_resolution_restee_lettre_morte_a_sa_ligne(self) -> None:
        """Arbitrage A du blueprint: la rupture s'exprime aussi dans l'euro absent."""
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("ACTE-1", montant_autorise="18240.00")], ["DOC-PV"])
        constats = {c["code"]: c for c in A.constats(self.instance)}
        self.assertIn("ACTE_SANS_EXECUTION", constats)
        self.assertAlmostEqual(constats["ACTE_SANS_EXECUTION"]["montant_en_jeu"], 18240.0)

    def test_un_montant_paye_different_du_montant_vote_est_chiffre(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("ACTE-1", montant_autorise="18240.00")], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_DOSSIERS,
                 [_dossier("DEP-1", montant_ttc="23460.00")], ["DOC-FAC"])
        A.ecrire(self.instance, A.TABLE_LIENS,
                 [_lien("ACTE-1", "AUTORISE", "DEP-1")], ["DOC-FAC"])
        constats = {c["code"]: c for c in A.constats(self.instance)}
        self.assertIn("MONTANT_DIVERGENT", constats)
        self.assertIn("23460.00", constats["MONTANT_DIVERGENT"]["motif"])
        self.assertIn("18240.00", constats["MONTANT_DIVERGENT"]["motif"])

    def test_deux_constats_du_meme_code_ne_portent_pas_le_meme_motif(self) -> None:
        """Trou T5: le seuil UX `0 motif identique` se joue a la generation."""
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [
            _dossier("DEP-1", libelle="Ravalement facade sud", fournisseur="WE GROUP",
                     montant_ttc="18240.00", date_depense="2024-09-15"),
            _dossier("DEP-2", libelle="Entretien des espaces verts",
                     fournisseur="VERT CITE", montant_ttc="1420.00",
                     date_depense="2024-04-02"),
        ], ["DOC-FAC"])
        motifs = [c["motif"] for c in A.constats(self.instance)
                  if c["code"] == "EURO_SANS_ACTE"]
        self.assertEqual(len(motifs), 2)
        self.assertEqual(len(set(motifs)), 2)

    # -- la matrice et le contrat de filtrage -------------------------------

    def test_chaque_cellule_absente_vaut_ABSENT_et_non_NULL(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [_acte("ACTE-1")], ["DOC-PV"])
        ligne = A.matrice(self.instance)[0]
        for cellule in ("cel_seuil", "cel_avis_cs", "cel_annexe", "cel_devis",
                        "cel_execution"):
            self.assertEqual(ligne[cellule], "ABSENT", cellule)

    def test_l_avis_du_conseil_se_filtre_sur_ses_trois_etats(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-1"), _acte("ACTE-2", numero="13"), _acte("ACTE-3", numero="14"),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("ACTE-1", "AVIS_CS", "DOC-CR", target_kind="document",
                  force_probatoire="PIECE_PRODUITE"),
            _lien("ACTE-2", "AVIS_CS", "declaration", target_kind="document",
                  force_probatoire="AFFIRME_SANS_PIECE", provenance="HUMAIN_CONFIRME",
                  origine="CORRIGE_HUMAIN"),
        ], ["DOC-CR"])
        etats = {l["acte_id"]: l["cel_avis_cs"] for l in A.matrice(self.instance)}
        self.assertEqual(etats["ACTE-1"], "PIECE_PRODUITE")
        self.assertEqual(etats["ACTE-2"], "AFFIRME_SANS_PIECE")
        self.assertEqual(etats["ACTE-3"], "ABSENT")
        filtres = A.matrice(self.instance, [("cel_avis_cs", "eq", "ABSENT")])
        self.assertEqual([l["acte_id"] for l in filtres], ["ACTE-3"])

    def test_un_affirme_sans_piece_n_est_jamais_diffusable(self) -> None:
        self.assertTrue(A.diffusable("PIECE_PRODUITE"))
        self.assertFalse(A.diffusable("AFFIRME_SANS_PIECE"))
        self.assertFalse(A.diffusable("ABSENT"))

    def test_le_contrat_de_filtrage_classe_chaque_colonne(self) -> None:
        groupes = A.filtres_disponibles()
        self.assertIn("exercice", groupes[A.COUT_DIRECT])
        self.assertIn("nature", groupes[A.COUT_DIRECT])
        self.assertIn("imputation", groupes[A.COUT_DIRECT])
        self.assertIn("cel_devis", groupes[A.COUT_JOINTURE])
        self.assertIn("cel_execution", groupes[A.COUT_JOINTURE])
        self.assertIn("cumul_delegation", groupes[A.COUT_AGREGAT])
        self.assertIn("constat", groupes[A.COUT_AGREGAT])
        self.assertEqual(
            sum(len(v) for v in groupes.values()), len(A.FILTRES)
        )

    def test_aucun_filtre_ne_balaie_du_texte(self) -> None:
        """Le contre-exemple a rendre impossible: `_decision_cell_status`.

        La cellule `Decision / devis` de l'ecran comptes cherche aujourd'hui des
        mots dans la concatenation de toutes les valeurs de la ligne. Ici, aucun
        filtre declare ne peut produire un operateur de texte - et ce test est
        ce qu'il faudrait casser pour en reintroduire un.
        """
        for nom in A.FILTRES:
            for operateur, valeur in (("eq", "X"), ("ne", "X"), ("in", ["X", "Y"]),
                                      ("gte", "X"), ("vide", None)):
                sql, _ = R.construire_requete([(nom, operateur, valeur)])
                haut = sql.upper()
                for interdit in R.OPERATEURS_INTERDITS:
                    self.assertNotIn(interdit, haut, f"{nom}/{operateur}: {sql}")

    def test_un_filtre_non_declare_est_refuse(self) -> None:
        with self.assertRaises(A.FiltreInconnu):
            R.construire_requete([("objet_libre", "eq", "facade")])

    def test_melanger_deux_vues_dans_un_filtre_est_refuse(self) -> None:
        with self.assertRaises(A.FiltreInconnu):
            R.construire_requete([("nature", "eq", "RESOLUTION_AG"),
                                  ("constat", "eq", "EURO_SANS_ACTE")])

    def test_la_jointure_de_la_matrice_est_indexee(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [_acte("ACTE-1")], ["DOC-PV"])
        with A.connexion(self.instance) as cx:
            plan = " ".join(
                str(r[3]) for r in cx.execute(
                    "EXPLAIN QUERY PLAN SELECT * FROM liens_gouvernance "
                    "WHERE source_kind='acte' AND source_id=? AND relation=?",
                    ("ACTE-1", "AUTORISE"))
            )
        self.assertIn("idx_liens_source", plan)

    # -- identite -----------------------------------------------------------

    def test_l_identite_derive_de_la_date_et_du_numero_pas_du_texte(self) -> None:
        a = A.acte_id_resolution("2024-07-03", "12")
        b = A.acte_id_resolution("2024-07-03", "12")
        self.assertEqual(a, b)
        self.assertEqual(a, "ACTE-AG-2024-07-03-R12")

    def test_un_sous_numero_distingue_deux_resolutions_du_meme_numero(self) -> None:
        """Corpus n. 2: `resolution 19.2` et `resolution 19.4` sont distinctes."""
        self.assertNotEqual(
            A.acte_id_resolution("2026-06-29", "19", sous_numero="2"),
            A.acte_id_resolution("2026-06-29", "19", sous_numero="4"),
        )
        # Un sous-numero vide ou nul ne change pas l'identifiant deja produit
        # sur le premier corpus.
        self.assertEqual(
            A.acte_id_resolution("2024-07-03", "12"),
            A.acte_id_resolution("2024-07-03", "12", sous_numero="0"),
        )

    def test_un_acte_sans_date_est_marque_et_non_confondu(self) -> None:
        sans = A.acte_id_resolution("", "12", doc_id="DOC-729CCCF88863")
        self.assertIn("SANS-DATE", sans)
        self.assertNotEqual(sans, A.acte_id_resolution("2024-07-03", "12"))

    def test_un_pv_sans_date_produit_un_constat_par_document_et_non_par_ligne(self) -> None:
        """Mesure reelle: 55 resolutions sur une assemblee sans date lue."""
        lignes = [
            _acte(A.acte_id_resolution("", str(n), doc_id="DOC-X"),
                  date_effet="", ag_id="", numero=str(n), doc_id="DOC-X")
            for n in range(1, 56)
        ]
        A.ecrire(self.instance, A.TABLE_ACTES, lignes, ["DOC-X"])
        constats = [c for c in A.constats(self.instance) if c["code"] == "PV_SANS_DATE_LUE"]
        self.assertEqual(len(constats), 1)
        self.assertIn("55", constats[0]["motif"])

    def test_l_identite_d_un_lien_porte_sa_provenance(self) -> None:
        a = A.lien_id("acte", "A1", "AUTORISE", "dossier", "D1", "SYNDIC_AFFIRME")
        b = A.lien_id("acte", "A1", "AUTORISE", "dossier", "D1", "COPROSCOPE_CALCULE")
        self.assertNotEqual(a, b)

    # -- montants -----------------------------------------------------------

    def test_un_montant_absent_n_est_pas_zero(self) -> None:
        self.assertEqual(A.montant_texte(""), "")
        self.assertEqual(A.montant_texte(None), "")
        self.assertIsNone(A.montant_nombre(""))
        self.assertEqual(A.montant_texte("18 240,00 EUR"), "18240.00")
        self.assertEqual(A.montant_texte("22 200,00"), "22200.00")
        self.assertEqual(A.montant_texte(18240), "18240.00")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class UnOperateurSansValeurRefuseQuOnLuiEnDonne(unittest.TestCase):
    """Constat `C092`: la valeur etait jetee sans un mot.

    `construire_requete([("date_effet", "vide", "2024-07-03")])` rendait
    `WHERE "date_effet" = ''` et une liste de parametres VIDE. La date demandee
    disparaissait, et la requete repondait a une autre question que celle
    posee - sans erreur, sans trace, sans rien.

    **L'invariant garde ici:** ce qu'un appelant fournit est employe ou refuse,
    jamais perdu. C'est le meme principe que partout ailleurs dans ce depot -
    une absence de mesure et une mesure conforme ne doivent pas se ressembler.
    """

    def test_UNE_VALEUR_DONNEE_A_UN_OPERATEUR_SANS_VALEUR_EST_REFUSEE(self) -> None:
        from coproscope.modules._actes_requetes import FiltreInconnu, construire_where

        for operateur in ("vide", "non_vide"):
            with self.subTest(operateur=operateur):
                with self.assertRaises(FiltreInconnu) as refus:
                    construire_where([("date_effet", operateur, "2024-07-03")])
                self.assertIn("ignoree en silence", str(refus.exception))

    def test_les_marques_du_rien_restent_acceptees(self) -> None:
        """`None` et la chaine vide disent *je ne fournis rien*, et c'est vrai."""
        from coproscope.modules._actes_requetes import construire_where

        for valeur in (None, ""):
            with self.subTest(valeur=valeur):
                where, params = construire_where([("date_effet", "vide", valeur)])
                self.assertIn("= ''", where)
                self.assertEqual([], params)

    def test_un_operateur_qui_LIT_sa_valeur_la_recoit_toujours(self) -> None:
        """Anti-vacuite: un refus qui refuserait tout ne garderait rien."""
        from coproscope.modules._actes_requetes import construire_where

        where, params = construire_where([("date_effet", "eq", "2024-07-03")])
        self.assertIn("= ?", where)
        self.assertEqual(["2024-07-03"], params)
