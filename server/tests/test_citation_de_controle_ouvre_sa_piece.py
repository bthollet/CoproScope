# -*- coding: utf-8 -*-
"""Ce qu'une cellule de controle NOMME, on peut l'ouvrir - ou personne ne le promet.

Instruction de `RM-2026-0157`, mots de Brice le 2026-09-08 `[00:05:11]`:
*« si je clique sur le titre de la piece, et ca DANS TOUTES LES CELLULES »*.
Et l'ordre de priorite qu'il donne `[00:04:59]`: *« voir le devis retenu, ca a
plante »* - **un geste qui echoue detruit la confiance dans les autres**, donc
il se corrige avant qu'on en ajoute.

**Ce que la mesure a trouve, et ce n'etait pas une exception.** Sur le corpus
du lot, 786 citations nomment un document; les 13 documents qu'elles designent
sont **tous** presents au registre documentaire - aucun lien mort - et **tous**
en zone brute avec un arbitrage de biffage non tranche, donc **aucun** ne
montre son contenu. Le geste ne levait pas d'exception: il ouvrait une page qui
annonce *« Aucun apercu exploitable »*. C'est la meme chose du point de vue du
lecteur, et c'est pire du point de vue de la confiance, parce que rien ne
prevenait.

**Les trois proprietes gardees ici, et pourquoi chacune existe:**

1. **une citation qui designe une piece connue porte un lien, et ce lien
   repond** - eprouve en le SUIVANT, pas en verifiant qu'il ressemble a une
   adresse. Un lien qui rend 404 est exactement le defaut a corriger;
2. **une citation qui designe une piece inconnue du registre ne porte AUCUN
   lien** - un chemin mort coute plus cher qu'un chemin absent, et l'ecran dit
   alors ce qu'il ne peut pas faire;
3. **la page citee est la page ouverte, et un ecart se DIT** - une demande hors
   bornes ramenee page 1 en silence ferait lire la mauvaise page en croyant
   lire la bonne.

**Ce corpus n'est pas celui de la mesure, et la difference se declare.**
`examples/synthetic_copro` est l'instance partageable: ses neuf documents
portent **les deux verdicts** - sept ouvrables, deux sous reserve de biffage -
ce qui suffit a eprouver les deux branches. Il ne prouve rien sur la justesse
des citations d'un vrai coffre: ses pieces ont ete ecrites pour passer.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.modules import actes_autorisation as A
from coproscope.web._controle_gouvernance_acces_piece import (
    INCONNU,
    OUVRABLE,
    RESERVE,
    Acces,
    acces_aux_pieces,
    _phrase_de_resume,
    chemin_de_piece,
    resumer_acces,
)
from coproscope.web.document_viewer import page_d_ouverture


#: Un `doc_id` qu'aucun registre ne porte. Il est ecrit ici en clair pour que
#: la garde reste lisible: c'est le cas `piece designee, jamais identifiee`.
DOC_ABSENT = "DOC-JAMAIS-IDENTIFIE"


def _acte(acte_id: str, doc_id: str, page: str, numero: str) -> dict[str, str]:
    return {
        "acte_id": acte_id, "nature": "RESOLUTION_AG", "etat": "CONSTATEE",
        "portee": "ENGAGEMENT_DEPENSE", "date_effet": "2025-07-03", "exercice": "2025",
        "ag_id": "AG-2025-07-03", "numero": numero, "sous_numero": "",
        "objet": "Ravalement de la facade sud", "montant_autorise": "18240.00",
        "entreprise": "", "montant_source": "", "entreprise_source": "",
        "valide_du": "", "valide_au": "", "majorite_requise": "24",
        "majorite_appliquee": "24", "majorite_annoncee": "24",
        "resultat": "ADOPTEE", "resolution_id": "", "page": page, "ancre": "",
        "confiance": "forte", "doc_id": doc_id, "origine": "EXTRAIT",
    }


class UnCheminSeCalculeSansOuvrirLeMoindreRegistre(unittest.TestCase):
    """Les fonctions pures, eprouvees sans instance ni disque."""

    def test_le_chemin_emporte_la_page_quand_la_page_existe(self) -> None:
        self.assertEqual("/documents/DOC-A?page=18", chemin_de_piece("DOC-A", "18"))

    def test_une_citation_sans_page_ne_fabrique_pas_page_1(self) -> None:
        """Une valeur par defaut passee pour une lecture est un faux.

        400 citations d'acte sur 786, sur le corpus du lot, portent une ancre
        sans page. Leur ecrire `page=1` ferait ouvrir la premiere page comme si
        c'etait la page citee.
        """
        self.assertEqual("/documents/DOC-A", chemin_de_piece("DOC-A", ""))

    def test_sans_document_il_n_y_a_pas_de_chemin(self) -> None:
        self.assertEqual("", chemin_de_piece("", "18"))

    def test_la_page_demandee_est_la_page_ouverte(self) -> None:
        self.assertEqual(("18", ""), page_d_ouverture("18", 140))

    def test_UNE_PAGE_HORS_BORNES_NE_SE_RABAT_PAS_EN_SILENCE(self) -> None:
        """Et le message NOMME les deux nombres, sinon il n'aide personne.

        Le registre porte `page_count`, le magasin de liens porte `page`: deux
        chemins d'ecriture differents que rien ne recoupe. L'ecart doit donc
        pouvoir arriver, et se voir.
        """
        page, ecart = page_d_ouverture("9999", 140)
        self.assertEqual("1", page)
        self.assertIn("9999", ecart)
        self.assertIn("140", ecart)

    def test_une_page_illisible_le_dit_au_lieu_d_ouvrir_page_1_muette(self) -> None:
        page, ecart = page_d_ouverture("page dix-huit", 140)
        self.assertEqual("1", page)
        self.assertIn("page dix-huit", ecart)

    def test_un_document_d_une_seule_page_s_accorde(self) -> None:
        """`les 1 pages` a ete livre a l'ecran, et vu la seule fois ou on a regarde."""
        _, ecart = page_d_ouverture("4242", 1)
        self.assertIn("la page unique", ecart)
        self.assertNotIn("les 1 pages", ecart)

    def test_un_document_sans_nombre_de_pages_est_honore_ET_declare(self) -> None:
        """Refuser reviendrait a punir le lecteur d'une lacune du registre."""
        page, ecart = page_d_ouverture("18", 0)
        self.assertEqual("18", page)
        self.assertIn("n'a pas été lu", ecart)

    def test_aucune_demande_ouvre_page_1_sans_rien_signaler(self) -> None:
        self.assertEqual(("1", ""), page_d_ouverture("", 140))

    def test_un_resume_sans_rien_a_signaler_ne_dit_RIEN(self) -> None:
        """Un avertissement qui se declenche toujours cesse d'etre lu."""
        lignes = [{"fonde": [{"citation": {"doc_id": "DOC-A"}, "sous": []}]}]
        resume = resumer_acces(lignes, {"DOC-A": Acces(OUVRABLE, "")})
        self.assertEqual(1, resume["citees"])
        self.assertEqual("", resume["phrase"])

    def test_un_resume_compte_les_pieces_et_non_les_citations(self) -> None:
        """Treize pieces a arbitrer est une tache; 621 rappels sont du bruit."""
        ligne = {"fonde": [{"citation": {"doc_id": "DOC-A"}, "sous": []}],
                 "seuil": [{"citation": {"doc_id": "DOC-A"}, "sous": []}],
                 "execution": [{"citation": {"doc_id": DOC_ABSENT}, "sous": []}]}
        resume = resumer_acces([ligne, ligne], {"DOC-A": Acces(RESERVE, "x")})
        self.assertEqual(2, resume["citees"])
        self.assertEqual(1, resume["reserve"])
        self.assertEqual(1, resume["inconnues"])
        self.assertIn("2 pièces", resume["phrase"])

    def test_LA_PHRASE_S_ACCORDE_AU_SINGULIER_COMME_AU_PLURIEL(self) -> None:
        """Elle a ete livree fausse une fois, et vue seulement a l'ecran.

        La premiere version ecrivait *« 1 attendent un arbitrage »*: le defaut
        n'apparaissait sur aucun test - tous portaient sur des comptes
        pluriels - et il se lisait en trois secondes sur la page reelle. C'est
        la raison pour laquelle une livraison qui touche un bout de page se
        regarde, et pas seulement se mesure.
        """
        une = _phrase_de_resume(1, {OUVRABLE: 0, RESERVE: 1, INCONNU: 0})
        self.assertIn("1 attend un arbitrage", une)
        self.assertIn("sa fiche s'ouvre", une)
        plusieurs = _phrase_de_resume(3, {OUVRABLE: 0, RESERVE: 3, INCONNU: 0})
        self.assertIn("3 attendent un arbitrage", plusieurs)
        self.assertIn("leurs fiches s'ouvrent", plusieurs)
        seule = _phrase_de_resume(1, {OUVRABLE: 0, RESERVE: 0, INCONNU: 1})
        self.assertIn("1 ne figure pas", seule)
        self.assertIn("Cet écran cite 1 pièce.", seule)

    def test_une_sous_bulle_compte_comme_une_bulle(self) -> None:
        """L'annexe est une sous-bulle, et sa piece est une piece."""
        lignes = [{"fonde": [{"citation": None,
                              "sous": [{"citation": {"doc_id": "DOC-SOUS"}}]}]}]
        resume = resumer_acces(lignes, {})
        self.assertEqual(1, resume["citees"])
        self.assertEqual(1, resume["inconnues"])


class _SurInstancePartageable(unittest.TestCase):
    """Une copie jetable de l'instance partageable, avec son coffre pose."""

    @classmethod
    def setUpClass(cls) -> None:
        depot = Path(__file__).resolve().parents[2]
        cls._tempdir = tempfile.TemporaryDirectory()
        racine = Path(cls._tempdir.name) / "instance"
        shutil.copytree(depot / "examples" / "synthetic_copro", racine)
        # L'exemple partageable ne declare aucun coffre local: sans lui, l'ecran
        # de gouvernance n'a ni a lire ni a ecrire. Ce n'est pas un defaut de
        # l'exemple - un coffre est une donnee de travail.
        fichier = racine / "instance.yml"
        texte = fichier.read_text(encoding="utf-8")
        marque = '"settings": {'
        assert marque in texte, "forme de instance.yml inattendue"
        fichier.write_text(
            texte.replace(marque, marque + '\n    "vault": {"local_root": "./vault_local"},', 1),
            encoding="utf-8",
        )
        cls.instance = load_instance(str(fichier), None)

        # Les deux verdicts existent dans ce registre, et c'est ce qui rend le
        # corpus utilisable: on prend un document de chaque famille plutot que
        # de fabriquer une ligne de registre pour les besoins de la garde.
        verdicts = acces_aux_pieces(cls.instance)
        cls.doc_ouvrable = next(d for d, a in verdicts.items() if a.verdict == OUVRABLE)
        cls.doc_reserve = next(d for d, a in verdicts.items() if a.verdict == RESERVE)

        A.ecrire(cls.instance, A.TABLE_ACTES, [
            _acte("ACTE-OUVRABLE", cls.doc_ouvrable, "1", "11"),
            _acte("ACTE-RESERVE", cls.doc_reserve, "", "12"),
            _acte("ACTE-ORPHELIN", DOC_ABSENT, "3", "13"),
        ], [cls.doc_ouvrable, cls.doc_reserve, DOC_ABSENT])

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tempdir.cleanup()

    def setUp(self) -> None:
        from fastapi.testclient import TestClient

        from coproscope.web.app import create_app

        self.client = TestClient(create_app(self.instance, 2025))
        self.html = self.client.get("/controle-gouvernance?vue=tableau").text

    def _citations(self) -> list[str]:
        return re.findall(r'<small class="cs-citation">.*?</small>', self.html, re.S)


class LeRegistreDitCeQueLaDestinationMontrera(_SurInstancePartageable):
    """Trois verdicts, et aucun n'est devine."""

    def test_les_deux_verdicts_existent_dans_le_corpus_partageable(self) -> None:
        """Sans quoi la garde n'eprouverait qu'une seule branche.

        Une garde qui ne voit qu'un verdict passe au vert le jour ou l'autre
        branche casse - c'est la forme la plus commune de garde creuse.
        """
        verdicts = acces_aux_pieces(self.instance)
        self.assertIn(OUVRABLE, {a.verdict for a in verdicts.values()})
        self.assertIn(RESERVE, {a.verdict for a in verdicts.values()})

    def test_une_piece_absente_du_registre_n_a_PAS_d_entree(self) -> None:
        """Distinguer `le registre ne la connait pas` de `pas de registre lu`."""
        self.assertNotIn(DOC_ABSENT, acces_aux_pieces(self.instance))

    def test_une_instance_sans_registre_declare_ne_propose_aucun_chemin(self) -> None:
        """Proposer un lien enverrait chaque clic sur un 404."""

        class _SansRegistre:
            def register(self, _nom: str) -> Path:
                raise KeyError("documents")

        self.assertEqual({}, acces_aux_pieces(_SansRegistre()))


class UneCitationMeneAOuElleDit(_SurInstancePartageable):
    """La promesse centrale du lot, eprouvee sur l'ecran REELLEMENT rendu."""

    def test_l_ecran_rend_bien_des_citations(self) -> None:
        """Anti-vacuite: sans citation, tout le reste passerait pour rien."""
        self.assertGreaterEqual(len(self._citations()), 3)

    def test_TOUTE_CITATION_D_UNE_PIECE_CONNUE_PORTE_UN_LIEN(self) -> None:
        """« et ca DANS TOUTES LES CELLULES ». Aucune exception toleree.

        Recoupe le MODELE avec l'ECRAN: une citation sans lien ne montre pas son
        `doc_id`, donc l'HTML seul ne peut pas dire quelle piece elle nomme. On
        part donc des bulles construites, et on exige que le chemin de chacune
        se retrouve dans la page rendue.
        """
        from coproscope.web.controle_gouvernance_view import build_controle_gouvernance_view

        connues = set(acces_aux_pieces(self.instance))
        vue = build_controle_gouvernance_view(self.instance, 2025, {"vue": "tableau"})
        attendus, vus = set(), 0
        for ligne in vue["lignes"]:
            for colonne in ("fonde", "seuil", "execution"):
                for bulle in ligne.get(colonne) or ():
                    for candidate in [bulle, *(bulle.get("sous") or ())]:
                        citation = candidate.get("citation") or {}
                        doc_id = str(citation.get("doc_id") or "")
                        if not doc_id:
                            continue
                        vus += 1
                        if doc_id in connues:
                            attendus.add(str(citation.get("href") or ""))
        self.assertGreater(vus, 0, "aucune citation ne nomme de piece: garde creuse")
        self.assertTrue(attendus, "aucune piece connue citee: garde creuse")
        manquants = [href for href in attendus if not href or f'href="{href}"' not in self.html]
        self.assertEqual([], manquants, "une citation nomme une piece connue sans y mener")

    def test_CHAQUE_LIEN_REPOND_QUAND_ON_LE_SUIT(self) -> None:
        """Le defaut a corriger en premier: un geste qui plante.

        Eprouve en SUIVANT le lien, pas en verifiant qu'il ressemble a une
        adresse. C'est la difference entre une garde et une impression.
        """
        # **Le selecteur porte la classe de la citation, et pas seulement le
        # prefixe `/documents/`.** Mesure du 2026-09-09 en cassant le gabarit
        # pour de vrai: sans la classe, cette garde restait VERTE alors que
        # plus aucune citation ne portait de lien - l'ecran porte d'autres
        # liens vers `/documents/`, et ils suffisaient a la satisfaire.
        liens = sorted(set(re.findall(
            r'<a class="cs-citation-lien" href="(/documents/[^"]+)"', self.html)))
        self.assertGreaterEqual(len(liens), 1, "aucune citation ne porte de lien")
        echecs = {lien: self.client.get(lien).status_code
                  for lien in liens if self.client.get(lien).status_code != 200}
        self.assertEqual({}, echecs, "un clic depuis une cellule de controle echoue")

    def test_une_piece_inconnue_du_registre_NE_porte_pas_de_lien(self) -> None:
        """Un chemin mort coute plus cher qu'un chemin absent."""
        self.assertNotIn(f"/documents/{DOC_ABSENT}", self.html)
        orphelines = [c for c in self._citations() if DOC_ABSENT in c]
        self.assertIn(
            "pièce absente du registre documentaire",
            self.html,
            "l'ecran ne dit pas qu'il ne peut pas ouvrir cette piece",
        )
        for citation in orphelines:
            self.assertNotIn("cs-citation-lien", citation)

    def test_la_page_citee_voyage_dans_le_lien(self) -> None:
        avec_page = [l for l in re.findall(
            r'<a class="cs-citation-lien" href="(/documents/[^"]+)"', self.html)
            if "page=" in l]
        self.assertTrue(avec_page, "aucune citation ne transporte sa page")

    def test_LE_LECTEUR_S_OUVRE_A_LA_PAGE_DEMANDEE(self) -> None:
        """Le lecteur ouvrait toujours page 1, quelle que soit l'adresse suivie."""
        from coproscope.web.document_viewer import build_document_detail

        detail = build_document_detail(self.instance, self.doc_ouvrable, "1")
        self.assertEqual("1", detail["pdf_trace"]["current_page"])
        hors = build_document_detail(self.instance, self.doc_ouvrable, "4242")
        self.assertEqual("1", hors["pdf_trace"]["current_page"])
        self.assertIn("4242", hors["pdf_trace"]["page_ecart"])

    def test_LA_RESERVE_EST_DITE_UNE_FOIS_ET_NON_SOUS_CHAQUE_CELLULE(self) -> None:
        """Le motif repete a l'identique est un defaut mesure de ce produit.

        La phrase entiere sort une fois, avec son nombre de pieces - qui est une
        tache. Sous les cellules, il ne reste qu'une etiquette de deux mots.
        """
        self.assertEqual(1, self.html.count("data-cs-acces-pieces"))
        self.assertNotIn("arbitrage de biffage n'est pas tranché", self.html)
        self.assertIn("contenu couvert", self.html)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
