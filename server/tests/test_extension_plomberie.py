"""La plomberie de l'extension, verifiee sans navigateur.

Une extension ne se teste vraiment qu'installee. Mais la classe de defauts que
l'installation revele en premier - un fichier absent, un identifiant qui n'existe
pas, un message que personne n'ecoute, une permission demandee pour rien - se
verifie sans navigateur, et donc a chaque execution de la suite.

Ce fichier existe parce qu'un tel defaut a ete trouve: apres le report de
l'integration a CoproScope, la fenetre du plugin n'emettait plus l'action
`transmettre`, alors que le manifeste continuait de demander l'acces a
`127.0.0.1`. **Une extension ne doit pas demander un acces dont elle ne se sert
pas** - c'est la premiere chose qu'un utilisateur prudent regarde, et la
premiere qu'un examen refuse.
"""

from __future__ import annotations

import json
import shutil
import re
import unittest
from pathlib import Path

#: Le chemin d'installation habituel sous Windows, quand `PATH` ne le porte
#: pas. Ecrit ici une seule fois: chaque tentative de le glisser dans une
#: chaine litterale cette nuit a produit une echappement casse.
_NODE_PAR_DEFAUT = 'C:\\Program Files\\nodejs\\node.exe'

RACINE = Path(__file__).resolve().parents[2] / "clients" / "extension-navigateur"


def _lire(nom: str) -> str:
    return (RACINE / nom).read_text(encoding="utf-8")


@unittest.skipUnless(RACINE.is_dir(), "extension absente de cet arbre")
class PlomberieTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifeste = json.loads(_lire("manifest.json"))
        cls.html = _lire("popup.html")
        cls.popup = _lire("popup.js")
        cls.journal = _lire("journal.js")
        cls.lecteur = _lire("lecteur.js")
        cls.fond = _lire("fond.js")
        cls.veille = _lire("veille.js")
        cls.cle = _lire("cle.js")
        cls.panneau = _lire("panneau.js")
        cls.referentiel = _lire("referentiel.js")
        cls.code = cls.popup + cls.journal + cls.lecteur + cls.fond + cls.veille

    def test_tous_les_fichiers_du_manifeste_existent(self) -> None:
        cites = [
            self.manifeste["background"]["service_worker"],
            self.manifeste["action"]["default_popup"],
        ]
        for bloc in self.manifeste.get("content_scripts", []):
            cites += bloc.get("js", []) + bloc.get("css", [])
        for nom in cites:
            self.assertTrue((RACINE / nom).exists(), nom)

    def test_le_popup_charge_journal_avant_popup(self) -> None:
        """Sinon `construireJournal` n'existe pas au moment ou on l'appelle."""
        scripts = re.findall(r'<script src="([^"]+)"', self.html)
        self.assertIn("journal.js", scripts)
        self.assertLess(scripts.index("journal.js"), scripts.index("popup.js"))

    def test_chaque_element_appele_existe_dans_la_page(self) -> None:
        ids = set(re.findall(r'\bid="([^"]+)"', self.html))
        for ident in set(re.findall(r'\$\("([^"]+)"\)', self.popup)):
            self.assertIn(ident, ids, f"#{ident} appele mais absent de popup.html")

    def test_node_est_present_sinon_soixante_dix_tests_se_taisent(self) -> None:
        """Le trou a l'endroit exact ou j'avais pose la garde.

        Cinq modules du lot - `test_extension_javascript`, `_veille`,
        `_bandeau`, `_conformite`, `_sonde` - sont gardes par `skipUnless` sur
        la presence de Node. Sans lui, environ **soixante-dix tests
        disparaissent**, dont toute la comparaison entre le lecteur JavaScript
        et l'etalon Python, et la garde qui verifie qu'un editeur inconnu ne
        produit aucun manque cote navigateur.

        `unittest` affiche bien `skipped=N`, mais il affiche aussi `OK`, et
        c'est `OK` que l'on retient. Un silence qui ressemble a une reussite est
        precisement le mode de panne que ce lot a passe sa nuit a corriger
        ailleurs - il serait malvenu de le laisser ici.

        Ce test ne saute pas. S'il tombe, la suite n'a pas mesure ce qu'elle
        pretend mesurer, et on l'apprend tout de suite.
        """
        chemin = shutil.which("node") or _NODE_PAR_DEFAUT
        self.assertTrue(
            Path(chemin).exists(),
            "Node.js est absent: environ 70 tests du lot extranet vont se taire, "
            "dont la comparaison entre les deux lecteurs. Installez Node, ou "
            "sachez que le vert de cette suite ne couvre pas le JavaScript.",
        )

    def test_tout_fichier_cite_par_le_manifeste_existe(self) -> None:
        """Rien ne verifiait que l'extension chargerait.

        Un script cite et absent ne casse pas les tests - ils chargent les
        fichiers eux-memes - mais le navigateur refuse l'extension entiere au
        chargement. Le lot a ajoute quatre fichiers cette nuit; c'est le genre
        d'oubli qui ne se voit qu'en installant.
        """
        manquants = []
        for js in self.manifeste["content_scripts"][0]["js"]:
            if not (RACINE / js).exists():
                manquants.append(f"content_script: {js}")
        for cle, valeur in (
            ("service_worker", self.manifeste["background"]["service_worker"]),
            ("default_popup", self.manifeste["action"]["default_popup"]),
        ):
            if not (RACINE / valeur).exists():
                manquants.append(f"{cle}: {valeur}")
        for src in re.findall(r'src="([^"]+)"', self.html):
            if not (RACINE / src).exists():
                manquants.append(f"popup script: {src}")
        for href in re.findall(r'href="([^"]+)"', self.html):
            if not (RACINE / href).exists():
                manquants.append(f"popup style: {href}")
        for imp in re.findall(r'importScripts\("([^"]+)"\)', self.fond):
            if not (RACINE / imp).exists():
                manquants.append(f"importScripts: {imp}")
        self.assertEqual(manquants, [])

    def test_aucune_permission_n_est_demandee_pour_rien(self) -> None:
        """Le defaut qui a motive ce fichier."""
        for perm, api in (("downloads", "chrome.downloads"), ("storage", "chrome.storage")):
            declaree = perm in self.manifeste.get("permissions", [])
            employee = api in self.code
            self.assertEqual(declaree, employee, f"permission '{perm}'")

    def test_chrome_tabs_est_employe_sans_etre_declare_et_c_est_voulu(self) -> None:
        """L'exception est NOMMEE, sur le modele de `transmettre`.

        `chrome.tabs.query`, `tabs.sendMessage` et la lecture de `tab.url`
        fonctionnent en MV3 sur les onglets couverts par `host_permissions` -
        ici le seul domaine du syndic. Declarer `tabs` donnerait en plus le
        titre et l'adresse de TOUS les onglets ouverts, dont le plugin n'a
        aucun besoin.

        Le test existe pour que ce soit une decision ecrite et non un oubli:
        s'il echoue un jour, c'est que quelqu'un a ajoute la permission, et il
        devra dire pourquoi.
        """
        self.assertIn("chrome.tabs", self.popup)
        self.assertNotIn("tabs", self.manifeste.get("permissions", []))
        self.assertIn("host_permissions", self.popup)

    def test_aucun_acces_hote_n_est_demande_pour_rien(self) -> None:
        """Le defaut qui a motive ce fichier: `127.0.0.1` etait demande alors que
        plus personne ne l'appelait depuis le report de l'integration."""
        # Le code ecrit le domaine dans des expressions regulieres, donc avec des
        # echappements: on compare sur une forme normalisee plutot que sur la
        # chaine brute - sinon le test echoue sur sa propre naivete, ce qu'il a
        # fait a sa premiere execution.
        code = self.code.replace("\\", "")
        for hote in self.manifeste.get("host_permissions", []):
            domaine = hote.split("://")[-1].rstrip("/*").removeprefix("www.")
            self.assertIn(domaine, code, f"acces '{hote}' demande, jamais employe")

    def test_toute_action_ecoutee_est_emise_par_quelqu_un(self) -> None:
        """Une action orpheline signale un cablage a moitie fait.

        C'est ce controle qui a trouve, apres le report de l'integration, que
        `transmettre` n'etait plus emis alors que sa permission restait demandee.
        """
        emises = set(re.findall(r'action:\s*"(\w+)"', self.popup + self.lecteur))
        ecoutees = set(
            re.findall(r'message\.action === "(\w+)"', self.lecteur + self.fond)
        )
        # `transmettre` est volontairement inerte: son emetteur reviendra avec
        # l'integration a CoproScope. Il est nomme ici pour que l'exception soit
        # une decision ecrite, et non un oubli silencieux.
        self.assertEqual(ecoutees - emises, {"transmettre"})

    def test_le_lecteur_n_emet_que_des_requetes_de_lecture(self) -> None:
        """La ligne rouge, verifiee dans le code et pas seulement promise."""
        methodes = set(re.findall(r'method:\s*"(\w+)"', self.lecteur))
        self.assertTrue(methodes <= {"HEAD", "GET"}, methodes)
        for interdit in ("form.submit", ".click()", "requestSubmit"):
            self.assertNotIn(interdit, self.lecteur)

    def test_le_service_worker_ne_touche_pas_au_dom(self) -> None:
        self.assertIsNone(re.search(r"\bdocument\.", self.fond))

    def test_aucune_api_incompatible_mv3(self) -> None:
        for interdit in (
            "chrome.extension.getBackgroundPage",
            "chrome.browserAction",
            "chrome.tabs.executeScript",
            "eval(",
        ):
            self.assertNotIn(interdit, self.code)

    def test_aucun_caractere_de_controle_brut_dans_les_sources(self) -> None:
        """Un separateur ecrit en caractere brut se perd au premier outil qui
        reformate le fichier, et git le classe en binaire."""
        for nom in ("popup.js", "journal.js", "lecteur.js", "fond.js", "veille.js", "cle.js",
                    "panneau.js", "referentiel.js"):
            source = _lire(nom)
            mauvais = [c for c in source if ord(c) < 32 and c not in "\n\r\t"]
            self.assertEqual(mauvais, [], nom)

    def test_le_secret_de_copropriete_n_est_jamais_ecrit_sur_le_disque(self) -> None:
        """Le sel d'echange ne doit exister que le temps d'un export.

        Ce qui est memorise est son **temoin** - une empreinte publique - pour
        pouvoir dire *"ce n'est pas le secret de vos exports precedents"* au
        lieu de laisser un voisin decouvrir un zero de concordance et le lire
        comme un desaccord entre eux.
        """
        motif = re.compile(r"storage\.local\.set\(([^)]*)\)")
        for ecriture in motif.findall(self.popup):
            # `temoin_sel` est une empreinte publique: elle a le droit d'etre
            # ecrite. C'est le sel nu qui ne l'a pas.
            reste = ecriture.replace("temoin_sel", "")
            self.assertNotIn("sel", reste, ecriture)
        self.assertIn("temoin_sel: paquet.temoin_sel", self.popup)

    def test_l_ecran_ne_dit_jamais_conforme(self) -> None:
        """La mise en garde de Brice, tenue sur la surface qu'il lit.

        Une rubrique peut porter le bon nombre de pieces sans que ce soient les
        bonnes. Le mot `conforme` n'apparait donc a l'ecran que dans la phrase
        qui dit qu'il ne s'applique pas - *servi en apparence n'est pas
        conforme* - et jamais comme etiquette d'etat.
        """
        for nom, source in (("panneau.js", self.panneau), ("popup.html", self.html)):
            with self.subTest(fichier=nom):
                for ligne in source.splitlines():
                    nu = ligne.strip()
                    # Les commentaires expliquent la regle: ils ont le droit de
                    # nommer le mot qu'ils interdisent.
                    if nu.startswith(("*", "/*", "//", "<!--")):
                        continue
                    if "conforme" not in nu.lower():
                        continue
                    self.assertIn(
                        "apparence", nu.lower(),
                        f"{nom}: `conforme` employe hors de la phrase de garde: {nu}",
                    )

    def test_l_ecran_de_conformite_est_cable(self) -> None:
        scripts = re.findall(r'src="([^"]+)"', self.html)
        for attendu in ("referentiel.js", "panneau.js"):
            self.assertIn(attendu, scripts)
        # Le referentiel avant le panneau qui l'emploie, comme au manifeste.
        self.assertLess(scripts.index("referentiel.js"), scripts.index("panneau.js"))
        self.assertIn('id="conformite"', self.html)

    def test_les_separateurs_sont_ceux_de_coproscope(self) -> None:
        """Sinon un voisin sous plugin et un voisin sous l'application ne se
        recouperaient jamais, et le defaut ne paraitrait qu'au recoupement."""
        from coproscope.modules._extranet_schema import SEPARATEUR_EMPLACEMENT

        self.assertEqual(ord(SEPARATEUR_EMPLACEMENT), 31)
        # Un seul fichier declare le separateur, depuis le 2026-09-07: les
        # autres l'empruntent a `cle.js`. Une verification adverse avait montre
        # que `lecteur.js` en portait une seconde declaration, invisible a la
        # garde d'unicite qui est purement textuelle.
        self.assertIn("String.fromCharCode(31)", self.cle)
        self.assertNotIn("String.fromCharCode(31)", self.lecteur)
        self.assertIn("CS_CLE.SEP", self.lecteur)
        self.assertIn("String.fromCharCode(0)", self.journal)

    def test_la_cle_d_emplacement_ne_se_construit_qu_a_un_seul_endroit(self) -> None:
        """Le defaut du 2026-09-07, tenu de facon executable.

        Trois constructions coexistaient pour une meme ligne de depenses, et
        celle de `journal.js` comptait la premiere colonne deux fois. Comme les
        trois coincidaient sur les documents, rien ne le disait - et c'est
        `journal.js` qui produit les empreintes destinees au voisin.

        La garde ne verifie pas le resultat, elle verifie qu'il n'y a qu'un
        seul producteur: une deuxieme construction reintroduirait la
        possibilite de la divergence, meme si elle etait juste le jour ou elle
        est ecrite.
        """
        for nom in ("journal.js", "veille.js", "lecteur.js", "popup.js"):
            with self.subTest(fichier=nom):
                self.assertNotIn("join(SEP)", _lire(nom))
        self.assertIn("CS_CLE.emplacementDe", self.journal)
        self.assertIn("CS_CLE.emplacementDe", self.veille)

    def test_le_manifeste_charge_la_cle_avant_ce_qui_l_emploie(self) -> None:
        scripts = self.manifeste["content_scripts"][0]["js"]
        self.assertEqual(scripts[0], "cle.js")
        html = self.html.index('src="cle.js"')
        self.assertLess(html, self.html.index('src="journal.js"'))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
