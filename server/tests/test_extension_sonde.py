"""La veille continue, et les trois gardes sans lesquelles elle nuirait.

Arbitrage A2, tranche par Brice le 2026-09-07: *je veux que ca tourne en
continu*. Sans minuterie, la couverture depend de ses habitudes - rien pendant
les vacances, or c'est la que le silence compte.

La conception avait designe une ligne comme **la plus grave et pas encore
traitee**: *la session peut expirer sans que personne le voie*. Un outil de
surveillance qui a cesse de voir, et qui se tait, est pire qu'un outil absent -
son silence se lit *rien n'a change*.

Les trois gardes, et ce fichier les tient une par une:

1. reconnaitre qu'on n'a pas vu l'index, et enregistrer `NON_EXPLORE` au lieu
   de conclure. Sans elle, une session finie produirait *tout a disparu*, le
   pire constat que l'outil sache rendre, sur une simple panne
   d'authentification;
2. afficher la derniere **tentative** ET le dernier **succes**. Deux dates, pas
   une: c'est leur ecart qui dit qu'on est devenu aveugle;
3. presence seulement. La sonde ne releve rien.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2] / "clients" / "extension-navigateur"
EXECUTEUR = RACINE / "tests" / "executer-sonde.mjs"
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"

ANCRE = 'id="documents"'
INDEX = f'<html><body><div {ANCRE}>...</div></body></html>'
CONNEXION = "<html><body><form id='login'>Identifiant</form></body></html>"

SCENARIOS = {
    # --- le jugement, cas par cas -----------------------------------------
    "index_servi": {"statut": 200, "corps": INDEX, "ancre": ANCRE},
    "page_de_connexion": {"statut": 200, "corps": CONNEXION, "ancre": ANCRE},
    "acces_refuse": {"statut": 403, "corps": "", "ancre": ANCRE},
    "serveur_en_panne": {"statut": 502, "corps": "", "ancre": ANCRE},
    "editeur_sans_ancre_declaree": {"statut": 200, "corps": INDEX, "ancre": ""},
    "reseau_injoignable": {"erreur": "getaddrinfo ENOTFOUND", "quand": "2026-09-07T10:00:00Z"},

    "editeur_sans_ancre_aucune_requete": {"compter_requetes": True, "ancre": ""},
    "editeur_connu_une_requete": {"compter_requetes": True, "ancre": ANCRE},

    # --- la vie de l'etat au fil des passages ------------------------------
    "trois_semaines_d_aveuglement": {
        "reponses": [
            {"statut": 200, "corps": INDEX, "quand": "2026-08-17T09:00:00Z"},
            {"statut": 200, "corps": CONNEXION, "quand": "2026-08-24T09:00:00Z"},
            {"statut": 200, "corps": CONNEXION, "quand": "2026-08-31T09:00:00Z"},
            {
                "statut": 200, "corps": CONNEXION, "quand": "2026-09-07T09:00:00Z",
                "maintenant": "2026-09-07T09:00:00Z",
            },
        ],
    },
    "un_incident_isole_puis_ca_repart": {
        "reponses": [
            {"statut": 200, "corps": INDEX, "quand": "2026-09-05T09:00:00Z"},
            {"statut": 502, "corps": "", "quand": "2026-09-06T09:00:00Z"},
            {"statut": 200, "corps": INDEX, "quand": "2026-09-07T09:00:00Z"},
        ],
    },
    "jamais_vu": {
        "reponses": [
            {"statut": 200, "corps": CONNEXION, "quand": "2026-09-07T09:00:00Z"},
        ],
    },
}


def _executer() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        chemin = Path(tmp) / "scenarios.json"
        chemin.write_text(json.dumps(SCENARIOS), encoding="utf-8")
        rendu = subprocess.run(
            [NODE, str(EXECUTEUR), str(chemin)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
    if rendu.returncode != 0:
        raise AssertionError(f"executer-sonde.mjs a echoue:\n{rendu.stderr[:2000]}")
    return json.loads(rendu.stdout)


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class GardeUnTests(unittest.TestCase):
    """Garde 1 - ne jamais conclure a partir d'une reponse qu'on n'a pas lue."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.r = _executer()

    def test_un_index_servi_est_vu(self) -> None:
        self.assertEqual(self.r["index_servi"]["etat"], "VU")

    def test_une_page_de_connexion_n_est_jamais_une_absence(self) -> None:
        """Le defaut que la garde existe pour empecher.

        Sans elle, une session finie aurait produit un releve vide, donc
        *toutes les pieces ont disparu* - et sur l'index reel, cent quinze
        disparitions d'un coup, sur une panne d'authentification.
        """
        cas = self.r["page_de_connexion"]
        self.assertEqual(cas["etat"], "NON_EXPLORE")
        self.assertIn("session", cas["motif"])

    def test_le_mot_reste_prudent(self) -> None:
        """*Probablement*: on constate qu'on n'a pas vu l'index, on ne verifie
        pas que c'est bien une page de connexion - il y en a autant que
        d'editeurs."""
        self.assertIn("probablement", self.r["page_de_connexion"]["motif"])

    def test_un_refus_et_une_panne_se_distinguent(self) -> None:
        """Un compteur d'echecs sans leur cause ne permet aucune action: se
        reconnecter et attendre ne sont pas le meme geste."""
        self.assertEqual(self.r["acces_refuse"]["motif"], "acces refuse")
        self.assertEqual(self.r["serveur_en_panne"]["motif"], "serveur injoignable")
        self.assertEqual(self.r["reseau_injoignable"]["motif"], "serveur injoignable")

    def test_sans_ancre_aucune_requete_ne_part(self) -> None:
        """Le verdict etait connu d'avance, et la requete partait quand meme.

        C'etait du trafic sur la session authentifiee de l'utilisateur, toutes
        les six heures, chez un editeur dont on ne sait rien - a valeur
        informationnelle nulle **par construction**. Une garde qui decide apres
        avoir emis ne protege de rien.
        """
        self.assertEqual(
            self.r["editeur_sans_ancre_aucune_requete"]["requetes_emises"], 0
        )
        self.assertEqual(self.r["editeur_connu_une_requete"]["requetes_emises"], 1)

    def test_un_editeur_sans_ancre_ne_conclut_rien(self) -> None:
        """Hors des valeurs observees: la sonde devient inutile, jamais
        menteuse. C'est le test d'acceptation de la regle des axes."""
        cas = self.r["editeur_sans_ancre_declaree"]
        self.assertEqual(cas["etat"], "NON_EXPLORE")
        self.assertIn("aucune ancre", cas["motif"])


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class GardeDeuxTests(unittest.TestCase):
    """Garde 2 - deux dates, jamais une seule."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.r = _executer()

    def test_la_tentative_et_le_succes_sont_deux_dates_distinctes(self) -> None:
        """Un ecran qui ne montrerait que le dernier succes laisserait croire
        que rien n'a change, alors que plus rien n'est observe."""
        derniere = self.r["trois_semaines_d_aveuglement"]["etapes"][-1]
        self.assertEqual(derniere["derniere_tentative"], "2026-09-07T09:00:00Z")
        self.assertEqual(derniere["dernier_succes"], "2026-08-17T09:00:00Z")

    def test_l_ecart_entre_les_deux_est_ce_qui_alerte(self) -> None:
        derniere = self.r["trois_semaines_d_aveuglement"]["etapes"][-1]
        self.assertEqual(derniere["diagnostic"]["niveau"], "AVEUGLE")
        self.assertEqual(round(derniere["diagnostic"]["jours_sans_succes"]), 21)

    def test_un_incident_isole_n_alarme_pas(self) -> None:
        """Au-dela de deux echecs d'affilee ce n'est plus un incident, c'est un
        etat. En deca, alarmer userait l'alarme."""
        etapes = self.r["un_incident_isole_puis_ca_repart"]["etapes"]
        self.assertEqual(etapes[1]["diagnostic"]["niveau"], "VOIT")
        self.assertEqual(etapes[1]["echecs_consecutifs"], 1)
        self.assertEqual(etapes[2]["echecs_consecutifs"], 0)
        self.assertEqual(etapes[2]["diagnostic"]["niveau"], "VOIT")

    def test_n_avoir_jamais_vu_se_distingue_d_avoir_cesse_de_voir(self) -> None:
        """Les deux appellent des gestes differents: verifier l'adresse, ou se
        reconnecter."""
        etape = self.r["jamais_vu"]["etapes"][0]
        self.assertEqual(etape["diagnostic"]["niveau"], "JAMAIS_VU")
        self.assertIsNone(etape["dernier_succes"])


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class GardeTroisTests(unittest.TestCase):
    """Garde 3 - presence seulement, jamais de contenu."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.r = _executer()

    def test_la_sonde_ne_rend_aucune_piece(self) -> None:
        """Rapatrier des megaoctets sans que personne regarde est un cout
        qu'on ne peut pas justifier - et un risque, sur des donnees de tiers."""
        for nom, cas in self.r.items():
            with self.subTest(scenario=nom):
                serialise = json.dumps(cas)
                for interdit in ("pieces", "libelle", "rubrique_code", "emplacement"):
                    self.assertNotIn(interdit, serialise)

    def test_le_corps_de_la_reponse_n_est_jamais_conserve(self) -> None:
        """Le corps sert a repondre a une seule question, puis il est jete. Le
        garder ferait du stockage du plugin une copie de l'extranet."""
        etat = json.dumps(self.r["trois_semaines_d_aveuglement"]["etat_final"])
        # Le corps servi etait une page de connexion et un index. Ni l'un ni
        # l'autre ne doit se retrouver dans l'etat conserve. L'adresse, elle, y
        # est legitimement - c'est ce qu'on sonde.
        for morceau in ("Identifiant", "<form", "<html", "<div"):
            self.assertNotIn(morceau, etat)


class CablageTests(unittest.TestCase):
    """Ce que le manifeste et le worker doivent porter pour que ca tourne."""

    def setUp(self) -> None:
        if not RACINE.exists():
            self.skipTest("extension absente de cet arbre")
        self.manifeste = json.loads((RACINE / "manifest.json").read_text(encoding="utf-8"))
        self.fond = (RACINE / "fond.js").read_text(encoding="utf-8")
        self.lecteur = (RACINE / "lecteur.js").read_text(encoding="utf-8")

    def test_la_permission_des_minuteries_est_declaree(self) -> None:
        self.assertIn("alarms", self.manifeste["permissions"])
        self.assertIn("chrome.alarms", self.fond)

    def test_la_sonde_ne_regarde_que_les_espaces_deja_visites(self) -> None:
        """Elle ne decouvre jamais une adresse toute seule: elle ne va que la
        ou l'utilisateur l'a deja menee."""
        self.assertIn("veille_etat:", self.fond)
        self.assertNotIn("https://coprodirecte.fr/espace", self.fond)

    def test_l_adresse_conservee_ne_porte_jamais_le_jeton_de_session(self) -> None:
        """Chez l'editeur mesure, l'adresse porte un jeton qui change a chaque
        chargement. Le stocker ecrirait un secret de session dans le stockage
        du plugin, et le ferait ressortir dans le moindre export.
        """
        self.assertIn("location.origin", self.lecteur)
        self.assertIn("location.pathname", self.lecteur)
        self.assertNotIn("location.href", self.lecteur)
        self.assertNotIn("location.search", self.lecteur)

    def test_une_transmission_ne_peut_viser_que_la_machine_locale(self) -> None:
        """Le chemin est inerte - aucun emetteur, permission retiree - mais
        `hote` venait du stockage SANS validation, et le domaine du syndic est
        dans les `host_permissions`. Un hote pointant vers lui aurait fait
        partir en POST la charge complete, libelles compris.

        La ligne rouge tenait sur une inertie; elle tient maintenant sur une
        garde.
        """
        self.assertIn("HOTES_LOCAUX", self.fond)
        self.assertIn("127", self.fond)
        self.assertIn("Rien ne part vers votre syndic", self.fond)

    def test_l_ancre_est_declaree_par_hote_et_non_devinee(self) -> None:
        self.assertIn("ANCRES", self.fond)
        self.assertIn("aucune ancre declaree", (RACINE / "sonde.js").read_text(encoding="utf-8"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
