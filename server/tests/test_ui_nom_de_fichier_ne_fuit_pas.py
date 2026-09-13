from __future__ import annotations

import csv
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.core.provenance_champs import colonnes_de_tiers, colonnes_non_declarees
from coproscope.web.app import create_app


"""Aucune valeur ecrite par un tiers ne sort d'une page servie.

**Le constat d'origine, 2026-09-07.** L'instance servie en `8788` affichait
`assignation oubar.pdf` sur la premiere carte P0 du cockpit - un patronyme
reel, sur l'ecran qui decide de la diffusion.

**Le constat sur la garde elle-meme, 2026-09-08, `RM-2026-0127`.** La premiere
version de ce fichier protegeait SIX ecrans, ecrits a la main dans un tuple
`ECRANS`. Mesure faite le jour de la refonte, en enumerant `create_app`:
l'application sert **54 routes en GET**. La garde en couvrait 6, soit 11%.

Ce que l'enumeration a laisse passer, et qui a ete trouve en une mesure des que
la garde a compte les routes au lieu de les nommer:

- `/api/model` rendait les colonnes de tiers du registre, d'un coup, en JSON.
  C'est la surface la plus exposee de l'application, et c'est aussi celle
  qu'une IA lirait. **Ce fichier a longtemps annonce 15; c'etait sa propre
  portee.** Il n'instrumente qu'`registre_documents.csv`; la mesure faite sur
  les 18 CSV de l'instance le 2026-09-09 en donne **102**. Ferme depuis, voir
  `test_surface_machine_ne_rend_que_le_declare.py`;
- `/documents/{doc_id}` rendait `file_name` trois fois - `title`, titre
  visible, `alt` - plus `lot` et `privacy_review_owner`;
- `/documents/non-lus` rendait le nom de base de `original_path`.

Aucune des trois n'etait dans les six. Ce n'est pas de l'inattention: une liste
d'ecrans code les pages qui existaient le jour ou elle a ete ecrite, et la
septieme passe.

**Ce que la garde verifie maintenant, et pourquoi ce n'est plus une liste.**
Deux enumerations ont ete remplacees par deux lectures du systeme reel:

1. *quelles pages* - on parcourt `app.routes`. Une route ajoutee demain est
   couverte le jour de son ajout, sans edition de ce fichier;
2. *quels champs* - on lit l'en-tete reel du registre et on demande a
   `core/provenance_champs.py` lesquels sont du texte de tiers. Le defaut y est
   `oui`: une colonne 55 inconnue est reputee dangereuse.

Puis on injecte une sentinelle par colonne de tiers et on verifie qu'aucune ne
ressort. La sentinelle est improbable: si elle sort, elle ne peut venir que de
la colonne qui la porte, et le message nomme la colonne ET la route.

**Le residu est nomme, et il est teste** - deux tests `RESIDU_*` plus bas. Ils
etaient trois; le troisieme portait sur `/api/model`, ferme le 2026-09-09 par
`RM-2026-0130`. Les deux qui restent sont mesures, et chacun echoue s'il empire.

**Ce que cette garde ne couvre PAS, et qu'il ne faut pas se raconter.** Trois
limites qui ne sont pas dans les tests `RESIDU_*` parce qu'elles portent sur la
methode elle-meme:

1. **La sentinelle n'est posee que sur la PREMIERE ligne du registre.** Un
   ecran qui ne rendrait que les lignes suivantes - un filtre, une deuxieme
   page, un tri qui relegue cette ligne - ne serait pas eprouve. Poser la
   sentinelle partout rendrait les lignes indistinguables et casserait les
   ecrans pour une autre raison que celle qu'on mesure;
2. **seul `registre_documents.csv` est instrumente.** Le registre de screening
   et la file de biffage portent aussi `file_name`; ils ne recoivent que le
   patronyme piege, pas les 15 sentinelles;
3. **une fuite n'est vue que si la valeur sort TELLE QUELLE.** Une valeur
   tronquee, decoupee, ou remise en forme - initiales, nom de base sans
   extension - passerait sous le radar. C'est le prix d'une detection par
   egalite exacte, et c'est aussi ce qui la rend sans faux positif.
"""


PATRONYME = "KERMOVAN"
NOM_DE_FICHIER = f"assignation {PATRONYME} lot B12.pdf"


def sentinelle(colonne: str) -> str:
    """Une chaine qui ne peut venir que de cette colonne."""

    return "ZQ" + colonne.upper().replace("_", "") + "QZ"


#: **Les valeurs de tiers qu'on rend SCIEMMENT, avec leur motif.**
#:
#: C'est le residu de la garde, ecrit en code plutot qu'en prose. Une fuite
#: constatee hors de cette table fait echouer le test; une entree de cette table
#: qui ne fuit plus le fait echouer aussi, pour qu'une exception cesse de vivre
#: apres sa cause.
#:
#: La difference avec l'ancien tuple `ECRANS` tient en une phrase: `ECRANS`
#: disait ce qu'on REGARDE - donc son oubli etait muet; ceci dit ce qu'on
#: ACCEPTE - donc son oubli est bruyant.
EXPOSITIONS_HTML_ACCEPTEES: dict[tuple[str, str], str] = {
    ("lot", "/documents/{doc_id}"): (
        "Le numero de lot est ecrit par le syndic, donc du texte de tiers, mais "
        "il designe un bien et non une personne, et c'est une information que la "
        "fiche doit porter. Exposition acceptee et non arbitree par Brice: a "
        "reexaminer si l'annuaire permet un jour de remonter du lot a son "
        "proprietaire, ce qui la transformerait en identifiant indirect."
    ),
}

#: **Le budget de fuite de la surface machine est supprime, parce que la fuite
#: l'est.** Il valait 15 et se defendait ainsi: « une seizieme colonne exposee
#: fait echouer, et une correction qui en supprime fait echouer aussi ».
#:
#: Il a tenu sa promesse - c'est lui qui a signale sa propre peremption le
#: 2026-09-09 - mais il portait deux defauts que sa disparition doit laisser
#: en memoire:
#:
#: 1. **un budget borne une fuite, il ne la ferme pas.** `RM-2026-0130` le
#:    disait deja: « le budget est un compteur, pas une garde - il empeche d'en
#:    ajouter une 16e, il ne retire aucune des 15 »;
#: 2. **son chiffre mesurait l'instrument.** 15 etait le nombre de colonnes de
#:    tiers d'`registre_documents.csv`, le seul registre que ce fichier
#:    instrumente. La sentinelle posee dans les 18 CSV de l'instance en donne
#:    **102**. Un compteur faux produit un chiffre qui a l'air d'une preuve, et
#:    celui-la est passe tel quel dans le gouvernail.
#:
#: Ce que rend `/api/model` est desormais construit, pas filtre: voir
#: `web/surface_machine.py` et `test_surface_machine_ne_rend_que_le_declare.py`.


class NomDeFichierNeFuitPas(unittest.TestCase):
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
        self._injecte_le_patronyme()
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    # --- injections ------------------------------------------------------------

    def _registre_documents(self) -> Path:
        return self.instance_root / "registers" / "registre_documents.csv"

    def _registres_portant_un_nom_de_fichier(self):
        """Tous les fichiers de l'instance qui portent une colonne `file_name`.

        **Decouverts, jamais listes.** La version precedente nommait trois
        chemins a la main. Mesure du 2026-09-08: `registre_ag.csv` n'en faisait
        pas partie, `/ag-contentieux` le lit, et il rendait son nom de fichier -
        la garde parcourait la route et ne voyait rien, parce que son temoin
        n'etait jamais pose la.

        Une liste de chemins couvre ce qu'on avait vu le jour ou on l'a ecrite.
        Un registre ajoute demain n'y serait pas, et **personne ne le saurait**:
        c'est precisement le silence que cette garde existe pour supprimer, et
        elle le reproduisait chez elle.
        """
        trouves = []
        for chemin in sorted(self.instance_root.rglob("*.csv")):
            try:
                with chemin.open(encoding="utf-8-sig", newline="") as flux:
                    entete = csv.DictReader(flux).fieldnames or []
            except OSError:
                continue
            if "file_name" in entete:
                trouves.append(chemin)
        return trouves

    def _lit_registre(self, chemin: Path) -> tuple[list[str], list[dict[str, str]]]:
        with chemin.open(encoding="utf-8-sig", newline="") as flux:
            lecteur = csv.DictReader(flux)
            return list(lecteur.fieldnames or []), list(lecteur)

    def _ecrit_registre(self, chemin: Path, champs: list[str], lignes: list[dict[str, str]]) -> None:
        with chemin.open("w", encoding="utf-8", newline="") as flux:
            ecrivain = csv.DictWriter(flux, fieldnames=champs)
            ecrivain.writeheader()
            ecrivain.writerows(lignes)

    def _injecte_le_patronyme(self) -> None:
        """Pose le nom de fichier piege sur la premiere ligne de chaque registre."""

        for chemin in self._registres_portant_un_nom_de_fichier():
            champs, lignes = self._lit_registre(chemin)
            if not lignes or "file_name" not in champs:
                continue
            # TOUTES les lignes, pas la premiere: un ecran qui FILTRE les
            # documents ne voit jamais un temoin pose sur une seule d'entre elles.
            for ligne in lignes:
                ligne["file_name"] = NOM_DE_FICHIER
                if "original_path" in champs:
                    ligne["original_path"] = f"raw\\{NOM_DE_FICHIER}"
            self._ecrit_registre(chemin, champs, lignes)

    def _injecte_les_sentinelles(self) -> tuple[tuple[str, ...], str]:
        """Une sentinelle par colonne de tiers. Rend les colonnes et le doc_id."""

        chemin = self._registre_documents()
        champs, lignes = self._lit_registre(chemin)
        tiers = colonnes_de_tiers(champs)
        # **Sur TOUTES les lignes ET dans TOUS les registres qui portent la
        # colonne.** Le lot POC avait declare deux residus - temoin sur une
        # seule ligne, un seul registre instrumente - et le MEME cas les a
        # demontres tous les deux le 2026-09-08: apres avoir etendu le temoin
        # a toutes les lignes du registre des documents, `/ag-contentieux`
        # rendait encore un nom brut, venu de `registre_ag.csv`.
        # **Sur TOUTES les lignes.** Le lot qui a ecrit cette garde n'en
        # marquait qu'une, et l'avait declare comme residu. La mesure du
        # 2026-09-08 lui donne raison de facon spectaculaire: `/ag-contentieux`
        # FILTRE les documents, donc il ne rendait jamais la ligne temoin - et
        # il rendait pourtant un nom de fichier brut et un identifiant
        # technique. La garde parcourait la route et ne voyait rien.
        #
        # Une garde ne couvre pas ce qu'elle parcourt: elle couvre ce que son
        # temoin atteint. Les deux etaient confondus.
        for ligne in lignes:
            for nom in tiers:
                ligne[nom] = sentinelle(nom)
        self._ecrit_registre(chemin, champs, lignes)
        return tiers, lignes[0]["doc_id"]

    def _client(self, app=None):
        from fastapi.testclient import TestClient  # type: ignore

        return TestClient(app if app is not None else self._app())

    def _app(self):
        return create_app(self.instance, 2025, access_token="local-secret")

    # --- parcours de TOUTES les routes servies ---------------------------------

    def _parcours_complet(self):
        """Sert chaque route GET et rend fuites, non instanciables et non servies.

        Rend un triplet:
        - `fuites`: {(colonne, route): type de contenu}
        - `non_instanciables`: routes dont un parametre de chemin est inconnu
        - `non_servies`: routes qui n'ont pas rendu 200
        """

        tiers, doc_id = self._injecte_les_sentinelles()
        app = self._app()
        client = self._client(app)
        routes = sorted(
            {r.path for r in app.routes if "GET" in (getattr(r, "methods", None) or set())}
        )
        self.assertGreater(len(routes), 20, "l'enumeration des routes n'a rien trouve")

        connus = {"doc_id": doc_id}
        fuites: dict[tuple[str, str], str] = {}
        non_instanciables: list[str] = []
        non_servies: list[str] = []

        for chemin in routes:
            concret, manquant = self._instancie(chemin, connus)
            if manquant:
                non_instanciables.append(chemin)
                continue
            try:
                reponse = client.get(f"{concret}?token=local-secret")
            except Exception:  # noqa: BLE001
                non_servies.append(chemin)
                continue
            if reponse.status_code != 200:
                non_servies.append(chemin)
                continue
            type_contenu = reponse.headers.get("content-type", "")
            for nom in tiers:
                if sentinelle(nom) in reponse.text:
                    fuites[(nom, chemin)] = type_contenu
        return fuites, tuple(non_instanciables), tuple(non_servies), routes

    @staticmethod
    def _instancie(chemin: str, connus: dict[str, str]) -> tuple[str, bool]:
        """Remplace les parametres de chemin connus. Dit si l'un manque."""

        concret = chemin
        while "{" in concret:
            debut = concret.index("{")
            fin = concret.index("}", debut)
            nom = concret[debut + 1 : fin].split(":")[0]
            if nom not in connus:
                return chemin, True
            concret = concret[:debut] + connus[nom] + concret[fin + 1 :]
        return concret, False

    # --- la garde ---------------------------------------------------------------

    def test_aucune_valeur_de_tiers_ne_sort_d_une_page_html(self) -> None:
        """La conservation qui remplace la liste de six ecrans.

        Toute fuite constatee sur une reponse HTML doit etre declaree dans
        `EXPOSITIONS_HTML_ACCEPTEES`, avec son motif. Le message d'echec nomme la
        colonne et la route, donc il dit quoi corriger sans enquete.
        """

        fuites, _, _, _ = self._parcours_complet()
        html = {
            cle for cle, type_contenu in fuites.items() if "html" in type_contenu.lower()
        }
        non_declarees = sorted(html - set(EXPOSITIONS_HTML_ACCEPTEES))
        self.assertEqual(
            non_declarees,
            [],
            "Une valeur ecrite par un tiers atteint une page HTML: "
            + "; ".join(f"colonne '{c}' sur {r}" for c, r in non_declarees)
            + ". C'est la fuite du 2026-09-07 revenue par une autre porte. "
            "Soit la valeur doit etre derivee ou aliasee avant rendu, soit "
            "l'exposition est un choix et se declare dans "
            "EXPOSITIONS_HTML_ACCEPTEES avec son motif.",
        )

    def test_les_expositions_acceptees_existent_encore(self) -> None:
        """Une exception qui ne sert plus doit mourir, pas dormir.

        Sans ce test, `EXPOSITIONS_HTML_ACCEPTEES` deviendrait une liste de
        pardons accumules, dont plus personne ne saurait lesquels sont encore
        justifies - exactement le defaut de l'ancien tuple `ECRANS`, dans
        l'autre sens.
        """

        fuites, _, _, _ = self._parcours_complet()
        html = {
            cle for cle, type_contenu in fuites.items() if "html" in type_contenu.lower()
        }
        perimees = sorted(set(EXPOSITIONS_HTML_ACCEPTEES) - html)
        self.assertEqual(
            perimees,
            [],
            "Ces expositions sont declarees acceptees mais ne se produisent "
            f"plus: {perimees}. Elles ont ete corrigees: retirez-les de "
            "EXPOSITIONS_HTML_ACCEPTEES pour que la garde redevienne stricte.",
        )

    def test_la_surface_machine_ne_rend_plus_aucune_valeur_de_tiers(self) -> None:
        """Le residu `RM-2026-0130` est ferme. Ce test garde l'acquis ici.

        **Ce test a remplace un budget, sur l'instruction du budget lui-meme.**
        La version precedente s'appelait
        `test_RESIDU_la_surface_machine_rend_encore_les_valeurs_de_tiers` et
        exigeait `len(machine) == BUDGET_FUITES_API_MODEL`, avec ce message:
        « Baissez BUDGET_FUITES_API_MODEL pour que l'acquis soit garde, ou
        supprimez ce test s'il tombe a zero. » Il est tombe a zero le
        2026-09-09; c'est donc sa propre consigne qui est appliquee.

        **Et le chiffre qu'il portait etait faux d'un facteur sept.** Il
        annoncait 15 colonnes parce qu'il n'instrumente qu'`registre_documents.csv`.
        La sentinelle posee dans les 18 CSV de l'instance en a trouve **102**.
        Le 15 n'etait pas une erreur de calcul: c'etait la portee du temoin
        prise pour la taille du defaut - la lecon du 2026-09-08 appliquee a un
        CHIFFRE au lieu d'une route.

        La garde complete, avec la colonne fictive et les chemins locaux, vit
        dans `test_surface_machine_ne_rend_que_le_declare.py`. Ce test-ci reste
        parce qu'il mesure par un chemin different - le parcours de TOUTES les
        routes - donc il verrait une reapparition que l'autre pourrait manquer.
        """

        fuites, _, _, _ = self._parcours_complet()
        machine = sorted(
            colonne
            for (colonne, route), type_contenu in fuites.items()
            if route == "/api/model" and "html" not in type_contenu.lower()
        )
        self.assertEqual(
            machine,
            [],
            f"/api/model rend de nouveau {len(machine)} colonnes de tiers "
            f"({machine}). Cette route doit rendre un resume DECLARE et non le "
            "modele verbatim: voir web/surface_machine.py.",
        )

    def test_RESIDU_certaines_routes_ne_sont_pas_couvertes(self) -> None:
        """Ce que la garde ne SAIT PAS servir, nomme au lieu d'etre saute.

        Une route dont le parametre de chemin est inconnu de ce test n'est pas
        verifiee. Le taire recreerait le defaut corrige ici: une garde qui
        parait couvrir tout et couvre une partie.

        Le compte est fige pour qu'une huitieme route a parametre ne s'ajoute
        pas en silence.
        """

        _, non_instanciables, non_servies, routes = self._parcours_complet()
        self.assertEqual(
            len(non_instanciables),
            # 6 -> 5 le 2026-09-13: `/actions/{action_id}` est supprimee avec
            # l'ecran `/actions` (`RM-2026-0183`), pas couverte.
            5,
            "Le nombre de routes que la garde ne sait pas instancier a change: "
            f"{list(non_instanciables)}. Si c'est une route neuve, ajoutez son "
            "parametre aux valeurs connues de `_parcours_complet` plutot que "
            "d'ajuster ce compte.",
        )
        couvertes = len(routes) - len(non_instanciables) - len(non_servies)
        self.assertGreaterEqual(
            couvertes / len(routes),
            # 0,8 -> 0,75 le 2026-09-13, sur mesure: 29/37. Le numerateur n'a
            # perdu que des routes COUVERTES, supprimees avec leurs ecrans par
            # la recette de Brice (`RM-2026-0183`); les 8 non couvertes sont
            # celles d'avant, moins `/actions/{action_id}`.
            0.75,
            f"La garde ne couvre plus que {couvertes}/{len(routes)} routes. "
            f"Non instanciables: {list(non_instanciables)}. Non servies: "
            f"{list(non_servies)}.",
        )

    def test_RESIDU_des_colonnes_du_registre_ne_sont_pas_declarees(self) -> None:
        """Les colonnes que `provenance_champs` ne connait pas encore.

        Elles sont deja PROTEGEES - le defaut de `est_texte_de_tiers` est `oui`.
        Ce test ne signale donc pas un danger, il rend visible le travail de
        relecture qui reste: dire, pour chacune, si sa valeur est derivee par
        CoproScope et peut donc s'afficher.

        Il echoue si le registre gagne une colonne, pour que l'arrivee de la
        55e soit une decision et non un evenement.
        """

        champs, _ = self._lit_registre(self._registre_documents())
        non_declarees = colonnes_non_declarees(champs)
        self.assertEqual(
            len(champs),
            54,
            f"Le registre porte {len(champs)} colonnes au lieu de 54. Les "
            "nouvelles sont protegees par defaut; classez-les dans "
            "`core/provenance_champs.py` puis ajustez ce compte.",
        )
        self.assertEqual(
            len(non_declarees),
            15,
            f"Colonnes reputees ecrites par un tiers: {list(non_declarees)}. "
            "Le compte a change.",
        )

    # --- ce que la premiere version gardait deja, et qui reste vrai -------------

    def test_chercher_le_patronyme_le_retrouve_sans_jamais_le_reecrire(self) -> None:
        """La recherche lit le nom de fichier cote serveur sans jamais le rendre.

        Deux portes de derriere sont fermees ici: reafficher la requete dans le
        champ de recherche, et laisser fuir le nom par la ligne retrouvee. Le
        terme cherche est le patronyme lui-meme, cas le plus defavorable.

        C'est ce test qui montre que la retrouvabilite et la non-fuite ne se
        contredisent pas: `retrouver` n'est pas `afficher`.
        """

        client = self._client()
        reponse = client.get(f"/documents?q={PATRONYME}&token=local-secret")
        self.assertEqual(reponse.status_code, 200)
        trouvees = re.search(r"Recherche en cours:\s*(\d+) piece", reponse.text)
        self.assertIsNotNone(trouvees, "la recherche ne filtre pas: le test ne prouve rien")
        self.assertGreater(
            int(trouvees.group(1)),
            0,
            "la piece n'est pas retrouvee par son nom de fichier: le test ne "
            "prouve rien sur l'absence de fuite.",
        )
        self.assertNotIn(
            PATRONYME,
            reponse.text,
            "le terme cherche revient dans la page: la recherche a rouvert la "
            "fuite qu'elle etait censee contourner.",
        )

    def test_les_ecrans_restent_utilisables(self) -> None:
        """Masquer ne doit pas vider: chaque piece garde un libelle lisible.

        Une correction qui rendrait les pages muettes serait une regression
        d'usage, pas une protection.
        """

        from coproscope.web.viewmodel import build_dashboard_model

        privacy = build_dashboard_model(self.instance, 2025)["privacy"]
        libelles = [row.get("display_file_name", "") for row in privacy["queue"].rows]
        self.assertTrue(libelles, "la file de biffage est vide: le test ne prouve rien")
        for libelle in libelles:
            with self.subTest(libelle=libelle):
                self.assertTrue(libelle.strip(), "libelle vide")
                self.assertNotIn(PATRONYME, libelle)
        self.assertEqual(
            len(set(libelles)),
            len(libelles),
            "deux pieces portent le meme libelle: masquer ne doit pas rendre "
            "les pieces indistinguables.",
        )

    def test_la_fiche_document_reste_lisible_sans_le_nom_de_fichier(self) -> None:
        """`RM-2026-0127`: la fiche ne nomme plus le fichier, et reste utile.

        Le correctif serait creux s'il avait remplace le nom par un vide: le
        libelle derive doit identifier la piece.
        """

        _, doc_id = self._injecte_les_sentinelles()
        page = self._client().get(f"/documents/{doc_id}?token=local-secret").text
        self.assertNotIn(sentinelle("file_name"), page, "le nom de fichier brut revient")
        self.assertIn(doc_id, page, "la fiche n'identifie plus la piece")

    def test_l_api_model_reste_du_json_lisible(self) -> None:
        """Le budget de fuite serait trompeur si la route ne rendait plus rien."""

        reponse = self._client().get("/api/model?token=local-secret")
        self.assertEqual(reponse.status_code, 200)
        self.assertIsInstance(json.loads(reponse.text), dict)


if __name__ == "__main__":
    unittest.main()
