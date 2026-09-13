"""L'ecran de controle de gouvernance, eprouve sur ses promesses.

Chaque test porte le nom de la promesse qu'il tient. Un test qui echoue doit
dire ce que le produit ne fait plus, pas quelle fonction a change.

La promesse centrale est celle qui a deja attrape deux contradictions de
compteurs pendant la conception: **une seule source calculee, deux rendus,
jamais deux calculs**. Elle est verifiee ici sur chaque constat, pas sur un
echantillon.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.modules import actes_autorisation as A
from coproscope.web import _controle_gouvernance_constats as C
from coproscope.web._controle_gouvernance_etat import (
    COFFRE_ABSENT,
    MODELE_NON_ALIMENTE,
    PRET,
)
from coproscope.web._controle_gouvernance_source import appliquer_filtres
from coproscope.web.controle_gouvernance_view import (
    COLONNES,
    build_controle_gouvernance_view,
)


def _acte(acte_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "acte_id": acte_id, "nature": "RESOLUTION_AG", "etat": "CONSTATEE",
        "portee": "ENGAGEMENT_DEPENSE", "date_effet": "2024-07-03", "exercice": "2024",
        "ag_id": "AG-2024-07-03", "numero": "12", "sous_numero": "",
        "objet": "Ravalement de la facade sud", "montant_autorise": "18240.00",
        "entreprise": "", "montant_source": "", "entreprise_source": "",
        "valide_du": "", "valide_au": "", "majorite_requise": "24",
        "majorite_appliquee": "24", "majorite_annoncee": "24",
        "resultat": "ADOPTEE", "resolution_id": "", "page": "4", "ancre": "",
        "confiance": "forte", "doc_id": "DOC-PV", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


#: Un corpus qui porte au moins un cas de chaque famille: une decision normale,
#: une resolution dont l'issue n'est pas enoncee, un rejet, une designation - qui
#: ne passe aucun marche et doit donc voir ses controles retires - et la
#: resolution qui arrete un seuil, qui est la source du controle et non son sujet.
CORPUS = [
    _acte("ACTE-1"),
    _acte("ACTE-2", numero="13", resultat="VOTE_SANS_FORMULE",
          objet="Budget previsionnel de l'exercice 2025", montant_autorise="280000.00"),
    _acte("ACTE-3", numero="14", resultat="REJETEE", objet="Reprise de toiture",
          montant_autorise="900.00"),
    _acte("ACTE-4", numero="15", portee="DESIGNATION_ORGANE", montant_autorise="",
          objet="Election au conseil syndical"),
    _acte("ACTE-5", numero="16", portee="SEUIL", montant_autorise="1000.00",
          objet="Seuil de mise en concurrence", confiance="faible"),
    _acte("ACTE-6", numero="17", resultat="PAS_DE_VOTE", montant_autorise="",
          objet="Appel de fonds pour l'entree B"),
]


class _Instance:
    """Instance minimale: seul le coffre local compte pour cet ecran."""

    display_name = "Copropriete de recette"

    def __init__(self, racine: Path, *, coffre: bool = True) -> None:
        self.racine = racine
        self._coffre = coffre

    def settings(self) -> dict[str, object]:
        return {"vault": {"local_root": "./vault_local"}} if self._coffre else {}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / str(valeur).lstrip("./")).resolve()


class _Socle(unittest.TestCase):
    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=True)

    def _alimenter(self, lignes: list[dict[str, str]] | None = None) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, lignes or CORPUS, ["DOC-PV"])

    def _vue(self, params: dict[str, str] | None = None) -> dict:
        return build_controle_gouvernance_view(self.instance, 2025, params or {})


class EtatsExplicitesTests(_Socle):
    """Jamais d'ecran vide silencieux.

    Zero rupture et zero preuve produisent le meme ecran vide. Les distinguer
    est la difference entre un outil de controle et un outil qui rassure a tort.
    """

    def test_sans_coffre_declare_l_ecran_dit_le_geste_exact(self) -> None:
        vue = build_controle_gouvernance_view(
            _Instance(self.racine, coffre=False), 2025, {}
        )
        self.assertEqual(vue["diagnostic"]["etat"], COFFRE_ABSENT)
        self.assertIn("local_root", vue["diagnostic"]["geste"])
        self.assertFalse(vue["disponible"])

    def test_un_modele_jamais_alimente_ne_se_lit_pas_comme_aucune_rupture(self) -> None:
        """Le cas reel au 2026-09-04, et le plus facile a rater.

        Le registre porte des resolutions, le modele relationnel n'en a recu
        aucune, et rien dans le produit ne verse de l'un vers l'autre. Un ecran
        qui afficherait `aucune rupture` mentirait sur l'etat du dossier.
        """
        from coproscope.modules.resolutions import RESOLUTION_FIELDS
        from coproscope.vault import gouvernance_store

        gouvernance_store.remplacer_pour_documents(
            self.instance,
            list(RESOLUTION_FIELDS),
            [{champ: "" for champ in RESOLUTION_FIELDS}
             | {"resolution_id": "R-1", "objet": "Ravalement", "doc_id": "DOC-PV",
                "origine": "EXTRAIT", "etat": "CONSTATEE"}],
            ["DOC-PV"],
        )
        vue = self._vue()
        self.assertEqual(vue["diagnostic"]["etat"], MODELE_NON_ALIMENTE)
        self.assertIn("1 résolutions", vue["diagnostic"]["corps"])
        self.assertIn("aucune lecture à contrôler", vue["diagnostic"]["corps"])
        self.assertFalse(vue["disponible"])

    def test_un_filtre_sans_resultat_dit_combien_existent_hors_du_filtre(self) -> None:
        self._alimenter()
        vue = self._vue({"vue": "tableau", "f_issue": "SANS_ISSUE_TRACEE"})
        self.assertEqual(vue["lignes"], [])
        self.assertEqual(vue["total"], len(CORPUS))


class SourceUniqueTests(_Socle):
    """Une seule source calculee, deux rendus, jamais deux calculs."""

    def setUp(self) -> None:
        super().setUp()
        self._alimenter()

    def test_le_nombre_d_un_constat_est_la_longueur_de_ce_que_le_tableau_affiche(self) -> None:
        """L'invariant central, verifie sur CHAQUE constat et pas sur un echantillon."""
        synthese = self._vue()
        for mesure in synthese["constats"]:
            with self.subTest(constat=mesure["constat"]["cle"]):
                params = {"vue": "tableau"}
                for cle, valeur in mesure["constat"]["filtre"].items():
                    params["f_" + cle] = valeur
                tableau = self._vue(params)
                self.assertEqual(
                    mesure["n"], len(tableau["lignes"]),
                    "la synthese et le tableau ont divergé sur ce constat",
                )

    def test_le_lien_d_un_constat_emporte_son_filtre_et_son_nombre(self) -> None:
        synthese = self._vue()
        self.assertTrue(synthese["constats"], "le corpus doit produire des constats")
        for mesure in synthese["constats"]:
            with self.subTest(constat=mesure["constat"]["cle"]):
                self.assertIn("n=" + str(mesure["n"]), mesure["lien"])
                self.assertIn("constat=" + mesure["constat"]["cle"], mesure["lien"])
                for cle in mesure["constat"]["filtre"]:
                    self.assertIn("f_" + cle + "=", mesure["lien"])

    def test_un_nombre_annonce_faux_declenche_l_alarme_au_lieu_de_se_taire(self) -> None:
        """L'alarme est faite pour un dispositif qui ne peut pas echouer.

        C'est le point: le jour ou un second chemin de calcul apparait, l'ecran
        le dit au lieu de mentir. On force ici l'ecart que le predicat unique
        rend impossible.
        """
        vue = self._vue({"vue": "tableau", "f_issue": "REJETEE", "n": "99",
                         "constat": "rejetee"})
        self.assertTrue(vue["provenance"]["divergent"])
        self.assertEqual(vue["provenance"]["attendu"], 99)
        self.assertEqual(vue["provenance"]["trouve"], len(vue["lignes"]))

    def test_le_point_a_instruire_a_une_seule_definition(self) -> None:
        """Une ligne est a instruire si au moins un constat non neutre la marque.

        Une version anterieure en avait deux - un drapeau pose a la main, et le
        comptage des constats - qui donnaient 23 et 59 sur le meme corpus.
        """
        vue = self._vue()
        self.assertEqual(vue["a_demander"], vue["arithmetique"]["lignes"])
        self.assertEqual(vue["a_demander"] + vue["calme"], vue["total"])

    def test_la_somme_des_constats_est_affichee_avec_son_recoupement(self) -> None:
        vue = self._vue()
        self.assertGreaterEqual(vue["arithmetique"]["marques"], vue["arithmetique"]["lignes"])
        if vue["arithmetique"]["marques"] > vue["arithmetique"]["lignes"]:
            self.assertGreater(vue["arithmetique"]["doubles"], 0)


#: 154 resolutions dont l'outil n'a pas reconnu le type, aucune ligne dans
#: `liens_gouvernance`, aucun constat dans `v_constats`. C'est le corpus mesure
#: le 2026-09-04 sur l'instance reelle, reduit a ce qui produit le defaut.
CORPUS_NON_TYPE = [
    _acte(f"ACTE-{n}", numero=str(n), portee="ORDINAIRE", montant_autorise="",
          objet=f"Objet {n}")
    for n in range(1, 155)
]


class ExerciceAfficheTests(_Socle):
    """L'ecran ne nomme pas un exercice qu'il ne filtre pas.

    Defaut mesure le 2026-09-04: le parametre `year` de la route ne filtrait
    rien - memes 141 lignes pour 2024 et pour 2026 - sous le titre « L'exercice
    2026 ». Et il ne DOIT pas filtrer: `liens_seuil` a ete ecrit pour qu'un
    seuil vote en 2024 pour vingt-quatre mois arme le controle d'une depense de
    2026, sans qu'aucune requete ne prenne d'annee en parametre. Ce qui etait
    faux, c'etait le titre.
    """

    def setUp(self) -> None:
        super().setUp()
        self._alimenter([
            _acte("ACTE-2024", date_effet="2024-07-03", exercice="2024"),
            _acte("ACTE-2026", numero="13", date_effet="2026-04-29", exercice="2026"),
        ])

    def test_deux_annees_differentes_rendent_les_memes_lignes(self) -> None:
        for annee in (2024, 2026):
            vue = build_controle_gouvernance_view(self.instance, annee, {"vue": "tableau"})
            self.assertEqual(len(vue["lignes"]), 2)

    def test_le_titre_ne_revendique_aucun_exercice(self) -> None:
        for annee in (2024, 2026):
            vue = build_controle_gouvernance_view(self.instance, annee, {"vue": "tableau"})
            self.assertNotIn(str(annee), vue["titre"])
            vue = build_controle_gouvernance_view(self.instance, annee, {})
            self.assertNotIn(str(annee), vue["titre"])

    def test_les_exercices_reellement_couverts_sont_affiches(self) -> None:
        vue = self._vue()
        self.assertEqual(vue["identite"]["exercices"], ["2024", "2026"])
        self.assertEqual(vue["identite"]["exercice_courant"], "2025")
        self.assertIn("2024", vue["identite"]["couverture"])
        self.assertIn("2026", vue["identite"]["couverture"])


class UneSeuleVueTableauTests(_Socle):
    """Un constat pose un FILTRE, il n'ouvre pas une page."""

    def setUp(self) -> None:
        super().setUp()
        self._alimenter()

    def test_la_configuration_de_page_ne_change_pas_avec_le_constat_clique(self) -> None:
        """Le defaut releve trois fois: la page d'arrivee changeait de forme.

        Memes colonnes, meme barre de filtres, meme comportement. Seuls les
        filtres changent.
        """
        formes = set()
        for constat in C.CONSTATS:
            params = {"vue": "tableau", "constat": constat["cle"]}
            for cle, valeur in constat["filtre"].items():
                params["f_" + cle] = valeur
            vue = self._vue(params)
            formes.add((
                tuple(titre for titre, _ in vue["colonnes"]),
                tuple(champ["cle"] for champ in vue["champs"]),
            ))
        self.assertEqual(len(formes), 1, "la page a changé de configuration selon le constat")

    def test_une_puce_retire_un_seul_filtre_et_garde_les_autres(self) -> None:
        vue = self._vue({"vue": "tableau", "f_issue": "ADOPTEE",
                         "f_type": "ENGAGEMENT_DEPENSE"})
        puces = {puce["cle"]: puce["href"] for puce in vue["provenance"]["puces"]}
        self.assertEqual(set(puces), {"issue", "type"})
        self.assertIn("f_type=ENGAGEMENT_DEPENSE", puces["issue"])
        self.assertNotIn("f_issue=", puces["issue"])
        self.assertIn("f_issue=ADOPTEE", puces["type"])
        self.assertNotIn("f_type=", puces["type"])

    def test_les_deux_sorties_sont_permanentes(self) -> None:
        vue = self._vue({"vue": "tableau", "f_issue": "ADOPTEE"})
        self.assertIn("vue=tableau", vue["provenance"]["tout_href"])
        self.assertNotIn("f_issue", vue["provenance"]["tout_href"])
        self.assertIn("vue=synthese", vue["provenance"]["retour_href"])

    def test_le_filtre_survit_a_l_aller_retour_parce_qu_il_est_dans_l_adresse(self) -> None:
        vue = self._vue({"vue": "tableau", "f_issue": "REJETEE"})
        vers_synthese = next(o for o in vue["onglets"] if o["cle"] == "synthese")
        self.assertIn("f_issue=REJETEE", vers_synthese["href"])
        retour = self._vue({"vue": "synthese", "f_issue": "REJETEE"})
        vers_tableau = next(o for o in retour["onglets"] if o["cle"] == "tableau")
        self.assertIn("f_issue=REJETEE", vers_tableau["href"])


class SixColonnesTests(_Socle):
    """Six colonnes, et l'annexe n'en est pas une."""

    def setUp(self) -> None:
        super().setUp()
        self._alimenter()

    def test_l_ordre_des_six_colonnes_ne_change_jamais(self) -> None:
        self.assertEqual(
            [titre for titre, _ in COLONNES],
            ["Décision", "Montant", "Ce qui la fonde", "Seuils franchis",
             "Exécution", "Ma conclusion"],
        )

    def test_l_annexe_est_une_sous_bulle_de_la_resolution_pas_une_colonne(self) -> None:
        """Une annexe n'existe pas en soi: elle existe parce qu'une resolution
        y renvoie. C'est donc la que le lecteur la cherche."""
        self.assertNotIn("Annexe", [titre for titre, _ in COLONNES])
        ligne = self._vue({"vue": "tableau"})["lignes"][0]
        sous = [s["texte"] for bulle in ligne["fonde"] for s in bulle["sous"]]
        self.assertTrue(any("Annexe" in texte for texte in sous))

    def test_une_annexe_absente_ne_laisse_pas_la_ligne_passer_pour_calme(self) -> None:
        """Les sous-bulles comptent dans le statut de la colonne.

        Les oublier rangerait la ligne parmi celles que rien ne contredit - un
        faux calme, le pire des defauts de cet ecran.
        """
        ligne = self._vue({"vue": "tableau"})["lignes"][0]
        statuts = {s["statut"] for bulle in ligne["fonde"] for s in bulle["sous"]}
        if "manquante" in statuts:
            self.assertEqual(ligne["statut_fonde"], "manquante")

    def test_la_couleur_ne_porte_jamais_l_information_seule(self) -> None:
        for ligne in self._vue({"vue": "tableau"})["lignes"]:
            with self.subTest(ligne=ligne["id"]):
                self.assertTrue(ligne["montant"]["picto"])
                self.assertTrue(ligne["montant"]["verdict"])

    def test_un_seul_arret_de_tabulation_par_ligne(self) -> None:
        """Le tableau montre, le panneau agit.

        Cette regle a fait passer la vue de 304 a 110 arrets de tabulation. Une
        cellule reste lisible et inerte; l'action vit dans le panneau.
        """
        for ligne in self._vue({"vue": "tableau"})["lignes"]:
            with self.subTest(ligne=ligne["id"]):
                self.assertTrue(ligne["href"])
                for colonne in ("fonde", "seuil", "execution"):
                    for bulle in ligne[colonne]:
                        self.assertNotIn("lien", bulle)
                        self.assertNotIn("geste", bulle)


class ControlesApplicablesTests(_Socle):
    """Ce qui ne s'applique pas le dit, et dit pourquoi."""

    def setUp(self) -> None:
        super().setUp()
        self._alimenter()

    def test_une_designation_ne_se_voit_pas_reprocher_un_devis_absent(self) -> None:
        """Reprocher a une election de n'avoir pas retenu de devis produit un
        constat faux, et un constat faux noie les vrais."""
        ligne = next(l for l in self._vue({"vue": "tableau"})["lignes"]
                     if l["portee"] == "DESIGNATION_ORGANE")
        devis = next(b for b in ligne["fonde"] if "Devis" in b["texte"])
        self.assertEqual(devis["statut"], "non_applicable")
        self.assertIn("devis", devis["detail"].lower())
        self.assertEqual(devis["statut_libelle"], "Non exigé ici")

    def test_un_controle_retire_porte_toujours_son_motif_de_droit(self) -> None:
        """Retirer un constat sans dire pourquoi est la meme faute que de
        l'afficher a tort: dans les deux cas on ne peut pas prendre le controle
        en defaut."""
        for ligne in self._vue({"vue": "tableau"})["lignes"]:
            for colonne in ("fonde", "seuil", "execution"):
                for bulle in ligne[colonne]:
                    if bulle["statut"] == "non_applicable":
                        with self.subTest(ligne=ligne["id"], texte=bulle["texte"]):
                            self.assertTrue(bulle["detail"].strip())

    def test_le_seuil_dit_CE_QU_IL_SAIT_du_franchissement(self) -> None:
        """**Ce test exigeait que le defaut survive, jusqu'au 2026-09-10.**

        Il s'appelait `test_le_seuil_dit_qu_aucun_franchissement_n_est_calcule`
        et verifiait la presence de *n'est pas calcule* dans la cellule. Le jour
        ou la comparaison a ete livree, il a echoue - **non parce qu'une
        regression etait survenue, mais parce que le trou qu'il gardait avait
        ete comble.** C'est la forme de garde que ce depot poursuit: un
        compteur de defauts rougit le jour ou le produit va mieux.

        Ce qui reste vrai, et qui est la vraie propriete: la cellule dit
        **l'un des trois etats**, et ne se tait jamais. Elle ne conclut pas non
        plus a une obligation TENUE - savoir si la consultation a eu lieu est
        une autre question, portee par la colonne d'avis.
        """
        vue = self._vue({"vue": "tableau"})
        ligne = next(l for l in vue["lignes"] if l["portee"] == "ENGAGEMENT_DEPENSE")
        detail = ligne["seuil"][0]["detail"]
        self.assertTrue(
            any(dit in detail for dit in ("dépasse", "n'a pas pu être calculé")),
            "la cellule de seuil ne dit rien du franchissement: %r" % detail[-160:])
        self.assertNotIn(
            "n'existe pas encore dans le modèle", detail,
            "la cellule affirme encore que la comparaison n'existe pas")
        limites = " ".join(bout["texte"] for ligne in vue["limites"] for bout in ligne)
        self.assertIn("franchissement", limites)
        self.assertNotIn(
            "Aucun franchissement de seuil n'est calculé", limites,
            "la page declare une limite qu'elle n'a plus")

    def test_ce_qui_manque_au_back_est_nomme_a_l_ecran(self) -> None:
        """Contredit `assertIn("Verser le registre")`, exige ici jusqu'au
        2026-09-09: cette exigence affirmait *rien n'ecrit dans
        « actes_autorisation » hors des tests*, et `RM-2026-0059` a mesure le
        contraire (`test_ecran_promet_ce_que_la_production_produit`)."""
        vue = self._vue()
        titres = " ".join(titre for titre, _ in vue["exigences_back"])
        self.assertIn("Grouper les factures en marchés", titres)
        self.assertNotIn(
            "Verser le registre", titres,
            "cette exigence dit que rien n'ecrit dans `actes_autorisation` hors "
            "des tests: faux, l'ecran s'accuserait d'un trou comble",
        )


class RouteTests(unittest.TestCase):
    """La route existe, elle sert le modele, et elle remplace `/ag-contentieux`."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ImportError:  # pragma: no cover - dependance optionnelle
            raise unittest.SkipTest("FastAPI test client indisponible")

    def setUp(self) -> None:
        depot = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        racine = Path(self.tempdir.name) / "instance"
        shutil.copytree(depot / "examples" / "synthetic_copro", racine)
        config = json.loads((racine / "instance.yml").read_text(encoding="utf-8"))
        config["settings"]["vault"] = {"local_root": "./vault_local"}
        (racine / "instance.yml").write_text(
            json.dumps(config, indent=2), encoding="utf-8"
        )
        self.instance = load_instance(str(racine / "instance.yml"), None)
        A.ecrire(self.instance, A.TABLE_ACTES, CORPUS, ["DOC-PV"])

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self):
        from fastapi.testclient import TestClient

        from coproscope.web.app import create_app

        return TestClient(create_app(self.instance, 2025))

    def test_la_route_repond_et_nomme_la_copropriete_dans_le_corps(self) -> None:
        reponse = self._client().get("/controle-gouvernance")
        self.assertEqual(reponse.status_code, 200)
        self.assertIn("Residence Les Platanes", reponse.text)
        self.assertIn("Volet décisions", reponse.text)

    def test_l_ecran_remplace_ag_contentieux_dans_la_navigation(self) -> None:
        """Decision prise: pas de vingt-sixieme entree. La route
        `/ag-contentieux` continue de repondre, elle n'est plus une destination."""
        client = self._client()
        page = client.get("/controle-gouvernance").text
        self.assertIn('href="/controle-gouvernance"', page)
        self.assertNotIn('href="/ag-contentieux"', page)
        self.assertEqual(client.get("/ag-contentieux").status_code, 200)

    def test_la_bascule_est_faite_de_liens_pas_d_un_motif_aria_a_moitie(self) -> None:
        """Ni `role="tablist"`, ni `role="tab"`, ni `aria-selected`.

        Le depot n'en contient aucune occurrence, et un motif ARIA a moitie
        implemente promet au lecteur d'ecran un comportement qui n'existe pas.
        """
        page = self._client().get("/controle-gouvernance").text
        self.assertNotIn('role="tablist"', page)
        self.assertNotIn('role="tab"', page)
        self.assertNotIn("aria-selected", page)
        self.assertIn('class="cs-comptes-tabs"', page)
        self.assertIn('aria-current="page"', page)

    def test_le_tableau_rend_les_six_colonnes_et_les_lignes_du_modele(self) -> None:
        page = self._client().get("/controle-gouvernance?vue=tableau").text
        for titre, _ in COLONNES:
            self.assertIn(titre, page)
        self.assertIn("Ravalement de la facade sud", page)
        self.assertIn("Résolution 12", page)

    def test_un_constat_de_la_synthese_mene_au_meme_nombre_de_lignes(self) -> None:
        """Bout en bout, a travers la route: le nombre annonce et le nombre
        trouve sont le meme nombre, et aucune divergence n'est signalee.

        `RM-2026-0183`, 2026-09-13: le lien d'un constat filtre desormais la
        liste de l'ACCUEIL. Ce test comptait la chaine `<tr>` - une modalite:
        une ligne `<tr class="is-selected">` n'etait deja pas comptee. Il compte
        le marqueur `data-cs-ligne`, pose sur les lignes des DEUX vues, et exige
        le meme nombre dans l'une et l'autre.
        """
        client = self._client()
        vue = build_controle_gouvernance_view(self.instance, 2025, {})
        mesure = next(m for m in vue["constats"] if m["constat"]["ton"] != "ok")
        page = client.get(mesure["lien"]).text
        tableau = client.get(mesure["lien"].replace("vue=synthese", "vue=tableau")).text
        self.assertEqual(page.count('<li data-cs-ligne="'), mesure["n"])
        self.assertEqual(tableau.count('<tr data-cs-ligne="'), mesure["n"])
        self.assertNotIn("Divergence entre les deux vues", page)

    def test_la_page_ne_defile_pas_lateralement_le_tableau_si(self) -> None:
        """Le defilement interne du tableau est accepte; celui de la page, non."""
        page = self._client().get("/controle-gouvernance?vue=tableau").text
        self.assertIn("cs-rappro-table-scroll", page)
        self.assertIn("la page ne défile jamais latéralement", page)


class PredicatUniqueTests(_Socle):
    """Il n'existe pas de second chemin de calcul."""

    def test_tout_filtre_de_constat_ne_nomme_que_des_champs_declares(self) -> None:
        from coproscope.web._controle_gouvernance_source import CHAMP_PAR_CLE

        for constat in C.CONSTATS:
            for cle in constat["filtre"]:
                with self.subTest(constat=constat["cle"], champ=cle):
                    self.assertIn(cle, CHAMP_PAR_CLE)

    def test_le_predicat_ne_compare_que_des_valeurs_declarees(self) -> None:
        """Aucune recherche de mots dans une phrase, ici comme dans le modele.

        Le contre-exemple est cote comptes: une cellule qui decide son etat en
        cherchant `devis` dans la concatenation de toute la ligne change d'etat
        quand un fournisseur s'appelle `DEVIS SERVICES`, et ne peut etre ni
        filtree ni prise en defaut.
        """
        source = (Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web"
                  / "_controle_gouvernance_source.py").read_text(encoding="utf-8")
        corps = source[source.index("def appliquer_filtres"):]
        for interdit in (" in lu_texte", ".lower()", "startswith", "find("):
            self.assertNotIn(interdit, corps.split("def libelle_filtres")[0])

    def test_sans_filtre_le_tableau_montre_tout_et_ne_tronque_rien(self) -> None:
        self._alimenter()
        vue = self._vue({"vue": "tableau"})
        self.assertEqual(len(vue["lignes"]), len(CORPUS))
        self.assertEqual(len(appliquer_filtres(vue["lignes"], {})), len(CORPUS))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
