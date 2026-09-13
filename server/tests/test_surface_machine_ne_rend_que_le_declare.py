"""`/api/model` ne rend que ce qu'elle declare, jamais ce que ses tables portent.

**Le defaut, mesure le 2026-09-09 sur `913d744`, instance `examples/synthetic_copro`.**
La route rendait `_dashboard_model()` verbatim: 318 872 octets, 19 branches,
22 tables. Aucun gabarit ni script de l'interface ne la consomme - zero
occurrence de `api/model` dans `templates/` et dans `static/`.

**Le chiffre du gouvernail etait 15; la mesure en donne 102.** `RM-2026-0130`
reprenait le nombre de `test_RESIDU_la_surface_machine_rend_encore_les_valeurs_de_tiers`,
qui n'instrumente qu'`registre_documents.csv`. En posant la sentinelle dans les
**18** CSV de l'instance - 114 colonnes de tiers - il en sortait **102**, dont
`fournisseur`, `numero_facture`, `siren_siret`, `author_label`, `emitter`.
Plus **24 chemins locaux absolus**, dont `model.instance.root`.

**Pourquoi cette garde compare des VALEURS et non des noms de cles.** La meme
mesure a trouve des valeurs de registre arrivees sous des cles qui ne sont pas
des noms de colonnes: `model.ux.comptes.ag_report.p2_points[].explanation`,
`model.accounting.guide.p2[].question`. Une garde qui verifierait la liste des
cles rendues les aurait declarees conformes. La sentinelle suit la **valeur**,
donc elle voit ce qu'un controle de schema ne voit pas - et elle reste vraie si
la reparation change de methode.

**Ce que cette garde ne couvre pas.**

1. Elle ne juge que `/api/model`. Les autres routes sont couvertes par
   `test_ui_nom_de_fichier_ne_fuit_pas`;
2. une fuite n'est vue que si la valeur sort **telle quelle**. Une valeur
   tronquee ou remise en forme passerait. C'est le prix d'une detection par
   egalite exacte, et c'est ce qui la rend sans faux positif;
3. la mesure porte sur `examples/synthetic_copro`, donc elle prouve une
   **non-regression**, pas une justesse: ces pieces ont ete ecrites pour passer.
   Ce que la garde etablit ne depend pourtant pas de la verite des donnees -
   une sentinelle est une chaine que l'on a ecrite soi-meme.
"""

from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.core.provenance_champs import est_texte_de_tiers
from coproscope.web.app import create_app
from coproscope.web.surface_machine import SURFACE_DECLAREE, resume_machine


#: Nom d'une colonne qui n'existe dans aucun registre et qui n'est declaree
#: nulle part. C'est la valeur inconnue de l'axe: le test d'acceptation de la
#: regle des axes demande que le code se degrade proprement devant elle, au lieu
#: de repondre faux en silence.
COLONNE_FICTIVE = "colonne_inventee_par_un_syndic_futur"


def sentinelle(colonne: str) -> str:
    """Une chaine qui ne peut venir que de cette colonne."""

    return "ZQ" + colonne.upper().replace("_", "").replace("-", "") + "QZ"


class SurfaceMachineNeRendQueLeDeclare(unittest.TestCase):
    def setUp(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore  # noqa: F401
        except ImportError:  # pragma: no cover
            self.skipTest("FastAPI test client indisponible")
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)

    # --- instrumentation --------------------------------------------------------

    def _instrumente_tous_les_registres(self, colonne_en_plus: str = "") -> tuple[str, ...]:
        """Pose une sentinelle dans CHAQUE colonne de tiers de CHAQUE CSV.

        **Decouverts, jamais listes.** Le 2026-09-08, une garde soeur nommait
        trois chemins a la main et `registre_ag.csv` n'en faisait pas partie:
        elle parcourait la route et ne voyait rien. Ici on balaie `rglob`, donc
        un registre ajoute demain est instrumente le jour de son ajout.

        `colonne_en_plus`, quand elle est donnee, est AJOUTEE a l'en-tete du
        registre des documents. Elle n'existe nulle part ailleurs dans le depot.
        """

        instrumentees: set[str] = set()
        for chemin in sorted(self.instance_root.rglob("*.csv")):
            try:
                with chemin.open(encoding="utf-8-sig", newline="") as flux:
                    lecteur = csv.DictReader(flux)
                    champs = list(lecteur.fieldnames or [])
                    lignes = list(lecteur)
            except (OSError, UnicodeDecodeError):
                continue
            if not champs or not lignes:
                continue
            if colonne_en_plus and chemin.name == "registre_documents.csv":
                champs = [*champs, colonne_en_plus]
            tiers = [nom for nom in champs if nom and est_texte_de_tiers(nom)]
            if not tiers:
                continue
            # TOUTES les lignes: un ecran qui FILTRE ne voit jamais un temoin
            # pose sur la premiere seule.
            for ligne in lignes:
                for nom in tiers:
                    ligne[nom] = sentinelle(nom)
            with chemin.open("w", encoding="utf-8", newline="") as flux:
                ecrivain = csv.DictWriter(flux, fieldnames=champs)
                ecrivain.writeheader()
                ecrivain.writerows(lignes)
            instrumentees.update(tiers)
        return tuple(sorted(instrumentees))

    def _surface(self):
        from fastapi.testclient import TestClient  # type: ignore

        instance = load_instance(str(self.instance_root / "instance.yml"), None)
        app = create_app(instance, 2025, access_token="local-secret")
        reponse = TestClient(app).get("/api/model?token=local-secret")
        self.assertEqual(reponse.status_code, 200, "/api/model doit rester servie")
        return reponse

    # --- les gardes -------------------------------------------------------------

    def test_aucune_valeur_de_registre_ne_sort_de_la_surface_machine(self) -> None:
        """Zero, et non un budget.

        **Ce test remplace un compteur par une garde.** `RM-2026-0130` notait le
        residu du residu: « le budget est un compteur, pas une garde - il
        empeche d'en ajouter une 16e, il ne retire aucune des 15 ». Un budget
        borne la fuite; il ne la ferme pas.
        """

        instrumentees = self._instrumente_tous_les_registres()
        self.assertGreater(len(instrumentees), 50, "l'instrumentation n'a presque rien pose")
        texte = self._surface().text
        sorties = sorted(nom for nom in instrumentees if sentinelle(nom) in texte)
        self.assertEqual(
            sorties,
            [],
            f"/api/model rend {len(sorties)} colonnes de tiers: {sorties}. "
            "La surface machine doit etre CONSTRUITE a partir de ce qu'elle "
            "declare, jamais filtree depuis le modele: ce qu'on oublie dans un "
            "filtre sort, ce qu'on oublie dans une declaration manque. Voir "
            "web/surface_machine.py.",
        )

    def test_une_colonne_inconnue_ne_sort_pas_par_defaut(self) -> None:
        """Le test d'acceptation de la regle des axes, joue pour de vrai.

        On ajoute au registre une colonne que **personne n'a jamais vue** -
        elle n'est declaree ni dans `provenance_champs.py`, ni dans un gabarit,
        ni dans ce depot. Si la surface machine etait un filtre par noms
        connus, cette colonne sortirait, et elle sortirait **en silence**.
        """

        self._instrumente_tous_les_registres(colonne_en_plus=COLONNE_FICTIVE)
        texte = self._surface().text
        self.assertNotIn(
            sentinelle(COLONNE_FICTIVE),
            texte,
            f"La colonne inconnue '{COLONNE_FICTIVE}' est sortie de "
            "/api/model. Une colonne nouvelle ne doit jamais sortir par "
            "defaut: le defaut doit etre l'absence, qui se voit, et non "
            "l'exposition, qui ne se voit pas.",
        )

    def test_aucun_chemin_local_absolu_ne_sort(self) -> None:
        """La seconde fuite trouvee par la meme mesure, et elle est pire.

        24 chemins absolus sortaient, dont `model.instance.root`: en
        production, c'est le repertoire personnel reel de l'utilisateur, servi
        a une machine, sur une route que personne ne regarde.
        """

        texte = self._surface().text
        racine = str(self.instance_root)
        self.assertNotIn(
            racine,
            texte,
            "/api/model rend le chemin absolu de l'instance. En production "
            "c'est le repertoire personnel de l'utilisateur.",
        )
        for marqueur in (":\\\\", ":/", "/Users/", "/home/"):
            with self.subTest(marqueur=marqueur):
                self.assertNotIn(marqueur, texte, f"chemin local rendu: {marqueur}")

    def test_la_surface_reste_utilisable(self) -> None:
        """Une route qui rend `{}` serait conforme et inutile.

        Sans ce test, la garde du dessus se satisferait d'une reponse vide -
        et le prochain lot croirait la route cassee plutot que reduite.
        """

        charge = json.loads(self._surface().text)
        self.assertEqual(charge.get("surface"), SURFACE_DECLAREE)
        self.assertGreaterEqual(
            len(charge.get("branches") or []),
            10,
            "la surface doit encore nommer les branches du modele",
        )
        tables = charge.get("tables") or {}
        self.assertGreaterEqual(
            len(tables),
            15,
            f"la surface ne recense que {len(tables)} tables. Le modele en "
            "porte une vingtaine: un recensement qui s'effondre signale un "
            "parcours qui ne reconnait plus la forme des tables.",
        )
        self.assertIn("documents.documents", tables)
        self.assertEqual(tables["documents.documents"]["lignes"], 9)
        for nom, compte in tables.items():
            with self.subTest(table=nom):
                self.assertIsInstance(compte["lignes"], int)
                self.assertIsInstance(compte["colonnes"], int)

    def test_le_resume_ne_mute_pas_le_modele_partage(self) -> None:
        """Le modele du tableau de bord est en cache et partage.

        `_dashboard_model()` met son resultat en cache et le sert a 53 autres
        routes HTML. Un resume qui retirerait des champs sur place viderait ces
        pages, et le defaut n'apparaitrait que sur la deuxieme requete.
        """

        instance = load_instance(str(self.instance_root / "instance.yml"), None)
        from coproscope.web.viewmodel import build_dashboard_model

        modele = build_dashboard_model(instance, 2025)
        avant = sorted(modele)
        table_avant = len(modele["documents"]["documents"].rows)
        resume_machine(modele)
        self.assertEqual(sorted(modele), avant, "le resume a retire des branches du modele")
        self.assertEqual(
            len(modele["documents"]["documents"].rows),
            table_avant,
            "le resume a vide les lignes d'une table du modele partage",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
