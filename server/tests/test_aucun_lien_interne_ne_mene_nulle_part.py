# -*- coding: utf-8 -*-
"""Un lien affiche a un utilisateur mene quelque part.

`RM-2026-0183`. Recette de Brice du 2026-09-13: sur `Pieces manquantes`, un
lien `Detail piece/preuve` menait a `/pieces/` sans identifiant et rendait 404,
alors que chaque test de la page la rendait en 200. Les gardes verifiaient les
pages qu'elles NOMMAIENT; aucune ne suivait ce que ces pages proposent.

Le parcours part de `/` et suit les liens rendus, sans liste de routes: voir
l'axe et le hors-portee dans `coproscope/web/_parcours_liens.py`. Il tourne sur
une COPIE de l'exemple synthetique, qui prouve que les liens tiennent sur cette
matiere-la et vaut pour la non-regression - pas pour une instance reelle, dont
d'autres donnees peuvent rendre d'autres liens.
"""
from __future__ import annotations

import re
import unittest

from coproscope.web._parcours_liens import lien_interne, liens_de, parcourir
from tests._exemple_copie import exemple_copie


def _client(app):
    try:
        from fastapi.testclient import TestClient  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependance UI optionnelle
        raise unittest.SkipTest(f"client de test FastAPI indisponible: {exc}")
    return TestClient(app)


def _obtenir(client):
    def obtenir(chemin: str):
        reponse = client.get(chemin)
        return reponse.status_code, reponse.headers.get("content-type", ""), reponse.text
    return obtenir


class L_INSTRUMENT_REPOND_JUSTE_SUR_UN_CAS_CONNU(unittest.TestCase):
    """Sans ce cas, un parcours qui ne suit rien conclurait `aucun lien mort`."""

    def test_un_lien_mort_fabrique_est_trouve_avec_sa_page(self) -> None:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse

        app = FastAPI()

        @app.get("/", response_class=HTMLResponse)
        def accueil():
            return '<a href="/vivante?token=x">a</a> <a href="/vivante">b</a>'

        @app.get("/vivante", response_class=HTMLResponse)
        def vivante():
            return '<a href="/morte/">vers rien</a> <a href="https://exemple.org/x">dehors</a>'

        parcours = parcourir(_obtenir(_client(app)))
        self.assertEqual({"/": 200, "/vivante": 200, "/morte/": 404}, parcours.pages)
        self.assertEqual([("/morte/", "/vivante", 404)], parcours.liens_morts)
        self.assertFalse(parcours.plafond_atteint)

    def test_le_plafond_se_dit_au_lieu_de_conclure(self) -> None:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse

        app = FastAPI()

        @app.get("/{n}", response_class=HTMLResponse)
        def chaine(n: str):
            return '<a href="/%s">suite</a>' % (n + "x")

        parcours = parcourir(_obtenir(_client(app)), depart="/a", plafond=5)
        self.assertTrue(parcours.plafond_atteint)
        self.assertEqual(5, len(parcours.pages))

    def test_ce_qui_est_un_lien_interne(self) -> None:
        self.assertEqual("/pieces?proof=missing", lien_interne("/pieces?proof=missing&amp;token=abc"))
        self.assertEqual("/documents/d1", lien_interne("http://testserver/documents/d1#page"))
        self.assertIsNone(lien_interne("/static/styles.css"))
        self.assertIsNone(lien_interne("http://testserver/static/app.js"))
        self.assertIsNone(lien_interne("https://www.legifrance.gouv.fr/x"))
        self.assertIsNone(lien_interne("#ancre"))
        self.assertIsNone(lien_interne("//cdn.exemple.org/x"))
        self.assertEqual(["/a", "/b"], liens_de("<a href='/a'>1</a><a href=\"/b\">2</a><a href='/a'>3</a>"))


class UN_LIEN_AFFICHE_MENE_QUELQUE_PART(unittest.TestCase):
    def test_aucun_lien_de_l_interface_ne_mene_a_une_erreur(self) -> None:
        from coproscope.web.app import create_app

        with exemple_copie("liens") as instance:
            client = _client(create_app(instance, 2025))
            accueil = client.get("/")
            parcours = parcourir(_obtenir(client))
        self.assertEqual(200, accueil.status_code)
        self.assertFalse(parcours.plafond_atteint, "plafond atteint: la conclusion porterait sur une partie")
        self.assertGreater(
            len(parcours.pages), len(liens_de(accueil.text)),
            "le parcours ne va pas au-dela des liens de l'accueil: l'instrument ne suit rien")
        self.assertEqual(
            [], parcours.liens_morts,
            "ces liens, affiches par l'interface, menent a une erreur (lien, page qui le porte, statut): %s"
            % parcours.liens_morts)


def _gabarit(chemin: str) -> str:
    """Une page nommee par sa forme: les identifiants de donnees deviennent `<id>`."""
    segments = [s for s in chemin.split("?", 1)[0].split("/") if s]
    return "/" + "/".join(
        "<id>" if (i > 0 and re.search(r"[A-Z0-9]", s)) else s for i, s in enumerate(segments))


#: **DETTE NOMINATIVE DU 2026-09-13, MESUREE ET NON ESTIMEE.** Le jour du retrait
#: de douze ecrans (`RM-2026-0183`), ces pages proposaient encore un lien vers un
#: ecran retire ou debranche - (forme de la page, chemin vise). La neutralisation
#: les rend en TEXTE, donc l'utilisateur ne tombe plus sur une 404; mais le
#: gabarit propose toujours une action qui n'existe plus, et c'est un defaut
#: d'ecran. Egalite d'ensembles: une page reprise qui ne propose plus le lien
#: demande a sortir d'ici, et un NOUVEAU lien vers un ecran retire fait mordre.
DETTE_2026_09_13: frozenset[tuple[str, str]] = frozenset({
    ('/', '/actions'),
    ('/', '/documents/ajouter'),
    ('/chantiers', '/actions'),
    ('/chantiers', '/confidentialite'),
    ('/chantiers', '/depot'),
    ('/chantiers', '/documents/ajouter'),
    ('/chantiers/<id>', '/actions'),
    ('/chantiers/<id>', '/confidentialite'),
    ('/chantiers/<id>', '/depot'),
    ('/chantiers/<id>', '/documents/ajouter'),
    ('/comptes', '/actions'),
    ('/contrats', '/depot'),
    ('/demandes/relance', '/actions'),
    ('/demandes/relance', '/depot'),
    ('/documents', '/actions'),
    ('/documents', '/depot'),
    ('/documents/<id>', '/confidentialite'),
    ('/exports/passation', '/actions'),
    ('/exports/passation', '/confidentialite'),
    ('/exports/passation/blocages/<id>', '/actions'),
    ('/exports/passation/blocages/diffusion-a-verifier', '/actions'),
    ('/exports/passation/blocages/preuves-manquantes', '/actions'),
    ('/incidents', '/actions'),
    ('/incidents', '/depot'),
    ('/pieces', '/actions'),
    ('/pieces', '/depot'),
    ('/pieces/<id>', '/confidentialite'),
    ('/pieces/<id>', '/depot'),
})


class UN_ECRAN_RETIRE_NE_S_OFFRE_PLUS(unittest.TestCase):
    def test_la_neutralisation_repond_juste_sur_un_cas_connu(self) -> None:
        from coproscope.web.debranchement import neutraliser_liens

        html = ('<a class="button-link" href="/actions?scope=x&amp;token=t">Voir</a> '
                '<a href="/actions-bis">garde</a> <a href="/pieces">garde</a> '
                '<a href="http://testserver/depot">Deposer</a>')
        rendu, compte = neutraliser_liens(html, ("/actions", "/depot"))
        self.assertEqual(2, compte)
        self.assertEqual(
            '<span class="cs-lien-retire">Voir</span> <a href="/actions-bis">garde</a> '
            '<a href="/pieces">garde</a> <span class="cs-lien-retire">Deposer</span>', rendu)

    def test_les_liens_bruts_vers_un_ecran_retire_sont_la_dette_declaree(self) -> None:
        from coproscope.web.app import create_app
        from coproscope.web.debranchement import sous

        with exemple_copie("liens-bruts") as instance:
            app = create_app(instance, 2025)
            app.state.neutraliser_liens = False
            client = _client(app)
            textes: dict[str, str] = {}

            def obtenir(chemin: str):
                reponse = client.get(chemin)
                type_contenu = reponse.headers.get("content-type", "")
                textes[chemin] = reponse.text if "html" in type_contenu else ""
                return reponse.status_code, type_contenu, reponse.text

            parcours = parcourir(obtenir)
            prefixes = app.state.liens_non_servis
        mesure = {
            (_gabarit(page), prefixe)
            for page, texte in textes.items() if parcours.pages.get(page, 500) < 400
            for lien in liens_de(texte)
            for prefixe in [sous(lien.split("?", 1)[0], prefixes)] if prefixe
        }
        self.assertTrue(mesure, "aucun lien brut mesure: l'instrument ne voit plus rien, ou toute la dette est resorbee")
        resorbee = sorted(DETTE_2026_09_13 - mesure)
        nouvelle = sorted(mesure - DETTE_2026_09_13)
        self.assertEqual(
            ([], []), (resorbee, nouvelle),
            "RESORBEE - la page ne propose plus ce lien, retirez-la de la dette: %s ; "
            "NOUVELLE - une page propose un lien vers un ecran retire ou debranche: %s" % (resorbee, nouvelle))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
