"""L'ecran cite sa source au lieu de l'affirmer.

Constat du 2026-09-07 qui ouvre ce lot: sur un coffre reel, 229 liens sur 229
portaient une `page` ET une `ancre` - par exemple `('DOC-E836DAFE1565', '14',
'sous-point 11-1')` - et le mot `ancre` n'apparaissait dans AUCUN gabarit. La
matiere etait complete, la tuyauterie s'arretait avant l'ecran: chaque cellule
affirmait sans jamais dire d'ou.

Chaque test porte le nom de la promesse qu'il tient. La promesse centrale n'est
pas `une page s'affiche`, c'est **la page affichee est celle de l'assertion dont
la force est affichee**. Une citation prise sur un autre lien serait un nouveau
mensonge silencieux, dans le lot precisement charge d'ajouter de l'honnetete.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.web._controle_gouvernance_cellules import citation
from coproscope.web._controle_gouvernance_etat import nommer_pieces
from coproscope.web._controle_gouvernance_source import construire_lignes


def _acte(acte_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "acte_id": acte_id, "nature": "RESOLUTION_AG", "etat": "CONSTATEE",
        "portee": "ENGAGEMENT_DEPENSE", "date_effet": "2026-04-29", "exercice": "2026",
        "ag_id": "AG-2026-04-29", "numero": "11", "sous_numero": "1",
        "objet": "Ravalement de la facade sud", "montant_autorise": "18240.00",
        "entreprise": "", "montant_source": "", "entreprise_source": "",
        "valide_du": "", "valide_au": "", "majorite_requise": "24",
        "majorite_appliquee": "24", "majorite_annoncee": "24",
        "resultat": "ADOPTEE", "resolution_id": "", "page": "16",
        "ancre": "sous-point 11-1", "confiance": "forte",
        "doc_id": "DOC-CONVOCATION", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _lien(lien_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "lien_id": lien_id, "source_kind": "acte", "source_id": "ACTE-1",
        "relation": "DEVIS_RETENU", "target_kind": "devis", "target_id": "DEVIS-1",
        "provenance": "SYNDIC_AFFIRME", "force_probatoire": "AFFIRME_SANS_PIECE",
        "motif": "", "doute": "", "montant_impute": "", "libelle_cible": "",
        "echeance": "", "constate_le": "2026-04-29", "auteur": "",
        "page": "16", "ancre": "sous-point 11-1",
        "doc_id": "DOC-CONVOCATION", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


#: **Le cas a deux assertions, CONSTRUIT et non emprunte.** Sur l'instance
#: principale mesuree le 2026-09-07, chaque acte ne porte qu'une assertion par
#: relation: le conflit n'y est pas reproductible. Il existe sur un second
#: coffre - 65 actes y portent deux `SEUIL_APPLICABLE` - mais un test qui
#: dependrait d'une instance ne mesurerait plus rien le jour ou elle change.
#: Le voici donc pose a la main, avec l'ecart maximal entre les deux liens:
#: pas la meme provenance, pas la meme force, pas la meme page.
DEUX_DEVIS = [
    _lien("L-SYNDIC", provenance="SYNDIC_AFFIRME",
          force_probatoire="AFFIRME_SANS_PIECE",
          target_id="DEVIS-CHER", page="22", ancre="sous-point 18-2"),
    _lien("L-HUMAIN", provenance="HUMAIN_CONFIRME",
          force_probatoire="PIECE_PRODUITE",
          target_id="DEVIS-RETENU", page="4", ancre="sous-point 2-1"),
]


class _Instance:
    display_name = "Copropriete de recette"

    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict[str, object]:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / str(valeur).lstrip("./")).resolve()


class _Socle(unittest.TestCase):
    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=True)

    def _matrice(self, actes: list[dict[str, str]], liens: list[dict[str, str]]):
        A.ecrire(self.instance, A.TABLE_ACTES, actes,
                 sorted({a["doc_id"] for a in actes}))
        if liens:
            A.ecrire(self.instance, A.TABLE_LIENS, liens,
                     sorted({l["doc_id"] for l in liens}))
        return {ligne["acte_id"]: ligne for ligne in A.matrice(self.instance)}

    def _bulles(self, actes, liens) -> dict[str, dict]:
        """Les bulles de la colonne `Ce qui la fonde`, par intitule de cellule."""
        matrice = list(self._matrice(actes, liens).values())
        ligne = construire_lignes(matrice, [], [])[0]
        return {b["texte"]: b for b in ligne["fonde"] + ligne["seuil"]}


class LaCitationSuitLeLienRetenuTests(_Socle):
    """**La page affichee est celle de l'assertion dont la force est affichee.**

    C'est le seul piege serieux du lot. `_cellule` ne rend pas la force d'un
    lien quelconque: elle rend celle du lien le plus probant, choisi par un
    `ORDER BY ... LIMIT 1`. Une citation ecrite avec une seconde requete, meme
    tres proche, pourrait retenir l'autre lien - et l'ecran dirait alors
    `Le devis retenu est au dossier` en pointant la page du devis que seul le
    syndic affirme.
    """

    def test_deux_devis_concurrents_citent_la_page_du_plus_probant(self) -> None:
        ligne = self._matrice([_acte("ACTE-1")], DEUX_DEVIS)["ACTE-1"]
        self.assertEqual(ligne["cel_devis"], A.FORCE_PIECE)
        self.assertEqual(ligne["src_devis_page"], "4")
        self.assertEqual(ligne["src_devis_ancre"], "sous-point 2-1")

    def test_l_ordre_inverse_ne_change_pas_le_lien_cite(self) -> None:
        """Sans `ORDER BY`, SQLite rend les lignes dans l'ordre ou il les trouve.

        Le meme jeu ecrit dans l'autre sens doit donner exactement la meme
        citation: si ce test passe dans un sens et pas dans l'autre, la
        citation depend de l'ordre d'insertion et non de la force probatoire.
        """
        ligne = self._matrice([_acte("ACTE-1")], list(reversed(DEUX_DEVIS)))["ACTE-1"]
        self.assertEqual(ligne["cel_devis"], A.FORCE_PIECE)
        self.assertEqual(ligne["src_devis_page"], "4")

    def test_un_humain_qui_contredit_le_lien_retire_aussi_sa_citation(self) -> None:
        """Un lien contredit ne fait plus foi: il ne doit plus etre cite non plus.

        C'est la meme regle de vie que la force probatoire, et l'oublier
        laisserait l'ecran pointer une page au nom d'une assertion qu'un humain
        a explicitement ecartee.
        """
        liens = DEUX_DEVIS + [
            _lien("L-HUMAIN-KO", provenance="HUMAIN_CONTREDIT",
                  force_probatoire="AFFIRME_SANS_PIECE",
                  target_id="DEVIS-RETENU", page="4", ancre="sous-point 2-1"),
        ]
        ligne = self._matrice([_acte("ACTE-1")], liens)["ACTE-1"]
        self.assertEqual(ligne["cel_devis"], A.FORCE_AFFIRME)
        self.assertEqual(ligne["src_devis_page"], "22")


class LaConcurrenceEstDiteTests(_Socle):
    """Une assertion parmi N ne se presente jamais comme seule."""

    def test_deux_assertions_vivantes_sont_annoncees_comme_deux(self) -> None:
        ligne = self._matrice([_acte("ACTE-1")], DEUX_DEVIS)["ACTE-1"]
        self.assertEqual(ligne["nb_devis"], 2)
        self.assertEqual(citation(ligne, "devis")["concurrentes"], 2)

    def test_une_seule_assertion_ne_declenche_aucune_mention(self) -> None:
        ligne = self._matrice([_acte("ACTE-1")], [_lien("L-1")])["ACTE-1"]
        self.assertEqual(citation(ligne, "devis")["concurrentes"], 1)

    def test_aucune_assertion_n_a_rien_a_citer(self) -> None:
        """`None`, et surtout pas une citation vide.

        Une cellule sans lien n'a aucune source a montrer; une source dont la
        page n'a pas ete notee en a une. Les confondre ferait afficher un
        cartouche `Source :` la ou il n'y a rien, ce qui se lit comme une
        preuve.
        """
        ligne = self._matrice([_acte("ACTE-1")], [])["ACTE-1"]
        self.assertIsNone(citation(ligne, "devis"))


class LaPositionNeSeReconstitueJamaisTests(_Socle):
    """Page et ancre manquent independamment, et aucune n'est devinee.

    Mesure du 2026-09-07 sur un second coffre: 10 des 65 seuils retenus n'ont
    pas de page et ont une ancre (`segment 38`). Un ecran qui exigerait les deux
    perdrait ces dix citations; un ecran qui recopierait la page de l'acte en
    inventerait dix.
    """

    def test_une_ancre_sans_page_reste_citable(self) -> None:
        ligne = self._matrice([_acte("ACTE-1")], [_lien("L-1", page="", ancre="segment 38")])["ACTE-1"]
        self.assertEqual(citation(ligne, "devis")["situe"], "segment 38")

    def test_une_page_sans_ancre_reste_citable(self) -> None:
        ligne = self._matrice([_acte("ACTE-1")], [_lien("L-1", page="14", ancre="")])["ACTE-1"]
        self.assertEqual(citation(ligne, "devis")["situe"], "page 14")

    def test_sans_page_ni_ancre_la_citation_ne_situe_rien(self) -> None:
        ligne = self._matrice([_acte("ACTE-1")], [_lien("L-1", page="", ancre="")])["ACTE-1"]
        self.assertEqual(citation(ligne, "devis")["situe"], "")

    def test_la_position_citee_n_est_pas_celle_de_l_acte(self) -> None:
        """L'acte est page 16, son devis page 4: la citation suit le LIEN.

        Aujourd'hui les deux coincident sur les deux coffres mesures - c'est une
        modalite du pont qui les ecrit ensemble, pas un invariant. Un avis de
        conseil syndical assert par un compte rendu de conseil vivra ailleurs
        que la resolution qu'il vise.
        """
        actes = [_acte("ACTE-1", page="16", ancre="sous-point 11-1")]
        ligne = self._matrice(actes, [_lien("L-1", page="4", ancre="sous-point 2-1")])["ACTE-1"]
        self.assertEqual(citation(ligne, "devis")["situe"], "page 4, sous-point 2-1")


class LeTexteDeLaResolutionCiteSaProprePieceTests(_Socle):
    """La cellule qui rapporte le texte ne cite pas un lien, elle cite l'acte.

    Elle n'est pas un des sept controles: elle ne verifie rien. Sa source est
    donc le document ou l'acte a ete lu, avec la page et l'ancre de l'ACTE - et
    surtout pas celles d'un devis qui vit ailleurs dans la piece.
    """

    def test_la_cellule_du_texte_cite_la_position_de_l_acte(self) -> None:
        actes = [_acte("ACTE-1", page="16", ancre="sous-point 11-1")]
        liens = [_lien("L-1", page="4", ancre="sous-point 2-1")]
        bulles = self._bulles(actes, liens)
        texte = next(b for b in bulles.values() if b["texte"].startswith("Résolution"))
        self.assertEqual(texte["citation"]["situe"], "page 16, sous-point 11-1")
        # **Le libelle est DERIVE, pas recopie.** Ce test portait
        # `bulles["Devis retenu"]` en dur et a casse le 2026-09-11 quand
        # `RM-2026-0164` a renomme la cellule - Brice ayant releve que `retenu`
        # presuppose un choix entre plusieurs devis, alors que le devis n'est
        # pas obligatoire. Un test qui recopie un libelle d'interface en fait
        # une interface, et casse a la premiere reformulation.
        from coproscope.web._controle_gouvernance_cellules import _L_DEVIS

        self.assertEqual(
            bulles[_L_DEVIS["nom"]]["citation"]["situe"], "page 4, sous-point 2-1")

    def test_un_projet_de_resolution_ne_cite_rien(self) -> None:
        """Une convocation ne vote pas: la cellule d'issue est retiree, donc muette."""
        actes = [_acte("ACTE-1", etat="PROJETEE", resultat="")]
        bulles = self._bulles(actes, [])
        texte = next(b for b in bulles.values() if "résolution" in b["texte"].lower())
        self.assertEqual(texte["statut"], "non_applicable")
        self.assertIsNone(texte["citation"])


class LaCelluleNonExigeeNeCiteRienTests(_Socle):
    """Un controle retire n'a pas de source: la question ne se pose pas.

    Une citation a cote de `non exige ici` se lirait comme une exigence, et
    c'est exactement la faute que la typologie a corrigee en retirant le
    controle plutot qu'en ecrivant `absent`.
    """

    def test_un_controle_retire_par_la_portee_porte_une_citation_nulle(self) -> None:
        actes = [_acte("ACTE-1", portee="DESIGNATION_ORGANE", montant_autorise="")]
        bulles = self._bulles(actes, [_lien("L-1")])
        retirees = [b for b in bulles.values() if b["statut"] == "non_applicable"]
        self.assertTrue(retirees, "cette portee doit retirer au moins un controle")
        for bulle in retirees:
            self.assertIsNone(bulle["citation"])


class LesPiecesSontNommeesOuDitesInconnuesTests(unittest.TestCase):
    """**Une absence de date est une information, pas un trou a combler.**

    Mesure du 2026-09-07 sur le registre d'un coffre reel: 32 lignes, dont 24
    sans date - des reglements de copropriete, des contrats, des annexes de
    reddition, dont l'identifiant est de la forme `CONV-DOC-<empreinte>`. Une
    ligne porte meme `2016-00`, qui n'est pas une date. Ecrire `convocation du
    ...` pour ces lignes-la fabriquerait un fait.
    """

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)
        from coproscope.vault import gouvernance_store

        self.chemin = gouvernance_store.store_path(self.instance)
        gouvernance_store.remplacer_pour_documents(
            self.instance,
            ["convocation_id", "doc_id", "ag_date", "sous_points", "origine"],
            [
                {"convocation_id": "CONV-2026-04-29", "doc_id": "DOC-LUE",
                 "ag_date": "2026-04-29", "sous_points": "78", "origine": "EXTRAIT"},
                {"convocation_id": "CONV-2026-05-22", "doc_id": "DOC-MUETTE",
                 "ag_date": "2026-05-22", "sous_points": "0", "origine": "EXTRAIT"},
                {"convocation_id": "CONV-DOC-1A4D", "doc_id": "DOC-SANS-DATE",
                 "ag_date": "", "sous_points": "0", "origine": "EXTRAIT"},
                {"convocation_id": "CONV-2016-00", "doc_id": "DOC-DATE-ILLISIBLE",
                 "ag_date": "2016-00", "sous_points": "0", "origine": "EXTRAIT"},
            ],
            ["DOC-LUE", "DOC-MUETTE", "DOC-SANS-DATE", "DOC-DATE-ILLISIBLE"],
            table="convocations",
            cles=("convocation_id", "origine"),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=True)

    def test_une_convocation_datee_et_lue_porte_sa_date(self) -> None:
        self.assertEqual(nommer_pieces(self.chemin)["DOC-LUE"], "convocation du 29/04/2026")

    def test_une_piece_datee_dont_rien_n_a_ete_lu_le_dit(self) -> None:
        self.assertEqual(
            nommer_pieces(self.chemin)["DOC-MUETTE"],
            "convocation du 22/05/2026, dont rien n'a été lu",
        )

    def test_une_piece_sans_date_ne_devient_pas_une_convocation_datee(self) -> None:
        nom = nommer_pieces(self.chemin)["DOC-SANS-DATE"]
        self.assertEqual(nom, "document non daté, dont rien n'a été lu")
        self.assertNotIn("convocation", nom)

    def test_une_date_illisible_n_est_pas_mise_en_forme(self) -> None:
        """`2016-00` ne doit surtout pas devenir `00/00/2016`."""
        nom = nommer_pieces(self.chemin)["DOC-DATE-ILLISIBLE"]
        self.assertEqual(nom, "document dont la date n'a pas pu être lue, dont rien n'a été lu")
        self.assertNotIn("2016", nom)

    def test_une_piece_absente_du_registre_n_a_pas_d_entree(self) -> None:
        """Et non une entree vide: l'appelant doit pouvoir dire `inconnue`."""
        self.assertNotIn("DOC-JAMAIS-VU", nommer_pieces(self.chemin))

    def test_un_registre_absent_ne_casse_rien(self) -> None:
        """Une copropriete dont aucune convocation n'a ete lue garde son ecran.

        Le registre des convocations est ecrit par un autre lot que le modele
        d'actes: sa table peut ne pas exister. L'ecran doit continuer a montrer
        ses cellules en disant qu'il ne sait pas nommer la piece.
        """
        vierge = _Instance(Path(tempfile.mkdtemp()))
        try:
            from coproscope.vault import gouvernance_store

            A.preparer(vierge)
            self.assertEqual(nommer_pieces(gouvernance_store.store_path(vierge)), {})
        finally:
            shutil.rmtree(vierge.racine, ignore_errors=True)


class LaCitationArriveDansLaPageTests(unittest.TestCase):
    """Le modele de vue ne suffit pas: la citation doit etre AFFICHEE.

    Une cle correcte dans un dictionnaire qu'aucun gabarit ne lit est
    exactement le defaut d'origine - `page` et `ancre` etaient renseignes sur
    229 liens sur 229, et le mot `ancre` n'apparaissait dans aucun gabarit.
    """

    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ImportError:  # pragma: no cover - dependance optionnelle
            raise unittest.SkipTest("FastAPI test client indisponible")

    def setUp(self) -> None:
        from coproscope.core.common import load_instance

        depot = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        racine = Path(self.tempdir.name) / "instance"
        shutil.copytree(depot / "examples" / "synthetic_copro", racine)
        config = json.loads((racine / "instance.yml").read_text(encoding="utf-8"))
        config["settings"]["vault"] = {"local_root": "./vault_local"}
        (racine / "instance.yml").write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.instance = load_instance(str(racine / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _page(self, liens: list[dict[str, str]], *, convocation: bool = True) -> str:
        from fastapi.testclient import TestClient

        from coproscope.vault import gouvernance_store
        from coproscope.web.app import create_app

        actes = [_acte("ACTE-1")]
        A.ecrire(self.instance, A.TABLE_ACTES, actes, ["DOC-CONVOCATION"])
        A.ecrire(self.instance, A.TABLE_LIENS, liens,
                 sorted({l["doc_id"] for l in liens}))
        if convocation:
            gouvernance_store.remplacer_pour_documents(
                self.instance,
                ["convocation_id", "doc_id", "ag_date", "sous_points", "origine"],
                [{"convocation_id": "CONV-2026-04-29", "doc_id": "DOC-CONVOCATION",
                  "ag_date": "2026-04-29", "sous_points": "78", "origine": "EXTRAIT"}],
                ["DOC-CONVOCATION"],
                table="convocations",
                cles=("convocation_id", "origine"),
            )
        client = TestClient(create_app(self.instance, 2026))
        return client.get("/controle-gouvernance?vue=tableau").text

    def test_la_cellule_nomme_la_piece_sa_page_et_son_endroit(self) -> None:
        page = self._page([_lien("L-1")])
        self.assertIn("cs-citation", page)
        self.assertIn("convocation du 29/04/2026", page)
        self.assertIn("page 16", page)
        self.assertIn("sous-point 11-1", page)

    def test_la_page_ne_montre_jamais_la_reference_interne_du_fichier(self) -> None:
        """T13: aucun libelle brut au premier niveau, identifiant de piece compris.

        **La regle porte sur ce qui se LIT, et il faut le dire depuis
        `RM-2026-0157`.** Une citation mene desormais a sa piece, et l'adresse
        de cette piece est `/documents/<doc_id>` - la meme que sur l'ecran des
        comptes et sur celui des factures a revoir. L'identifiant vit donc dans
        un `href`, jamais dans une phrase.

        **Ce test passait pour une raison qui ne tiendra pas toujours:** cette
        instance de recette ne declare aucun registre documentaire, donc aucune
        citation n'y porte de lien. Le corps du test ne peut pas s'appuyer
        la-dessus sans devenir vide au premier registre ajoute - il exclut donc
        explicitement les attributs d'adresse et mesure le texte.
        """
        page = self._page([_lien("L-1")])
        lisible = re.sub(r'href="[^"]*"', "", page)
        self.assertNotIn("DOC-CONVOCATION", lisible)

    def test_deux_assertions_concurrentes_sont_ecrites_comme_telles(self) -> None:
        page = self._page(DEUX_DEVIS)
        self.assertIn("1 assertion sur 2", page)
        self.assertIn("il ne tranche pas entre elles", page)

    def test_une_assertion_seule_ne_parle_pas_de_concurrence(self) -> None:
        self.assertNotIn("assertion sur", self._page([_lien("L-1")]))

    def test_une_piece_hors_registre_est_nommee_comme_inconnue(self) -> None:
        """**Ce test exigeait une autre phrase, et elle est citee ici.**

        Il affirmait `assertIn("pièce que le registre des convocations ne nomme
        pas", page)`, c'est-a-dire que la citation devait s'ouvrir sur cette
        phrase. Elle etait EXACTE et elle se lisait de travers: un lecteur y
        comprend *on ne sait pas de quelle piece il s'agit*.

        **Mesure du 2026-09-09 qui a impose le changement** (`RM-2026-0157`):
        sur le corpus du lot, **400 citations d'acte sur 786 sont dans ce cas,
        et les 400 designent un document present au registre documentaire**. Le
        produit sait exactement quel fichier c'est. Nommer et atteindre sont
        deux axes, et cette phrase les confondait.

        Le fait n'est pas supprime - il reste ecrit, hors du lien, la ou il ne
        peut plus se lire comme une ignorance.
        """
        page = self._page([_lien("L-1")], convocation=False)
        self.assertIn("le registre des convocations ne la nomme pas", page)
        self.assertNotIn("convocation du", page)

    def test_sans_page_ni_ancre_l_ecran_dit_qu_il_ne_situe_rien(self) -> None:
        page = self._page([_lien("L-1", page="", ancre="")])
        self.assertIn("L'endroit exact dans la pièce n'a pas été noté", page)

    def test_sans_aucun_lien_seule_la_cellule_du_texte_cite(self) -> None:
        """Le silence est la bonne reponse **pour les controles**, et pour eux seuls.

        Sans aucun lien, les cinq cellules de controle n'ont rien a citer et se
        taisent. La cellule qui rapporte le texte de la resolution, elle, a bien
        une source: l'acte a ete lu quelque part, et c'est le premier endroit que
        le lecteur veut pouvoir rouvrir. Un seul cartouche, donc, et c'est
        celui-la.
        """
        page = self._page([])
        # **Le compte porte sur la classe, pas sur la sous-chaine.** Le
        # 2026-09-09, `RM-2026-0157` a ajoute `cs-citation-lien` et
        # `cs-citation-reserve`: un `count("cs-citation")` s'est mis a compter
        # trois choses pour un seul cartouche. Le defaut n'etait pas dans le
        # produit, il etait ici - un selecteur de mesure trop large echoue
        # exactement comme une enumeration, dans l'autre sens.
        self.assertEqual(page.count('class="cs-citation"'), 1)
        self.assertIn("convocation du 29/04/2026, page 16, sous-point 11-1", page)


if __name__ == "__main__":
    unittest.main()
