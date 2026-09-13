"""La liste legale en code, et ce qu'elle refuse de conclure.

Ce fichier tient trois choses que rien ne tenait avant le 2026-09-07:

1. que le code porte **exactement** les obligations du document de reference,
   et pas une transcription approximative qui derivera;
2. qu'un editeur inconnu ne produit **aucun manquement** - le test
   d'acceptation de la regle dure du depot sur les axes de generalisation;
3. qu'aucun producteur n'ecrit `CONFORME`, parce que le dire exige de lire la
   piece et que l'observation ne la lit pas.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import _extranet_conformite as C
from coproscope.modules import _extranet_referentiel as R
from coproscope.modules import extranetops as X

DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "referentiel_conformite_extranet_v1.md"
)


def _releve(rubriques: list[dict]) -> dict:
    return {"espace": "/espace-copropriete/documents", "rubriques": rubriques}


def _rub(code: str, nb: int, presente: bool = True) -> dict:
    return {
        "rubrique_code": code,
        "presente": presente,
        "pieces": [{"groupe": "", "libelle": f"P{i}"} for i in range(nb)],
    }


def _sans_commentaires(chemin: Path) -> str:
    """Le code d'un fichier, sa prose retiree.

    Un scan textuel qui inclut les commentaires flague la documentation qui
    EXPLIQUE l'interdiction - c'est-a-dire exactement ce qui la fait tenir. La
    frontiere porte sur le code, jamais sur la prose.
    """
    source = chemin.read_text(encoding="utf-8")
    if chemin.suffix == ".py":
        import ast

        arbre = ast.parse(source)
        for noeud in ast.walk(arbre):
            if isinstance(noeud, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                  ast.AsyncFunctionDef)) and noeud.body:
                premier = noeud.body[0]
                if isinstance(premier, ast.Expr) and isinstance(
                    premier.value, ast.Constant
                ) and isinstance(premier.value.value, str):
                    noeud.body.pop(0)
        return ast.unparse(arbre) if arbre.body else ""
    # JavaScript et HTML: on retire les blocs et les lignes de commentaire.
    sortie, reste = [], source
    while True:
        debut = reste.find("/*")
        if debut < 0:
            sortie.append(reste)
            break
        sortie.append(reste[:debut])
        fin = reste.find("*/", debut + 2)
        reste = reste[fin + 2:] if fin >= 0 else ""
    texte = "".join(sortie)
    lignes = []
    for ligne in texte.splitlines():
        nu = ligne.strip()
        if nu.startswith("//") or nu.startswith("<!--"):
            continue
        lignes.append(ligne)
    return "\n".join(lignes)


class ReferentielTests(unittest.TestCase):
    def test_les_dix_huit_obligations_sont_declarees(self) -> None:
        self.assertEqual(len(R.LISTE_MINIMALE), 18)
        self.assertEqual(len(R.par_college(R.COLLEGE_A)), 9)
        self.assertEqual(len(R.par_college(R.COLLEGE_B)), 4)
        self.assertEqual(len(R.par_college(R.COLLEGE_C)), 5)

    @unittest.skipUnless(DOC.exists(), "document de reference absent")
    def test_le_code_porte_les_memes_identifiants_que_le_document(self) -> None:
        """Le document reste la source; le code en est la transcription.

        Sans ce test, les deux derivent - et c'est le document qui serait cite
        devant un syndic pendant que le code mesurerait autre chose.
        """
        texte = DOC.read_text(encoding="utf-8")
        # On ne retient que les lignes de tableau dont la PREMIERE cellule est
        # l'identifiant: ce sont les lignes qui definissent une obligation. Les
        # autres mentions du document parlent des identifiants sans les poser -
        # la table des corrections de fond cite `EXT-C-07`, l'etat des impayes,
        # pour dire qu'il est absent des trois listes, et la table des
        # rubriques ecartees fait de meme. Les porter en code fabriquerait des
        # manquements imaginaires.
        coupe = texte.index("## Rubriques ecartees")
        du_doc = set(
            re.findall(
                r"^\| `(EXT-(?:00[0-3]|X-0[1-3]|[ABC]-\d{2}))`",
                texte[:coupe],
                re.MULTILINE,
            )
        )
        du_code = {r.identifiant for r in R.RUBRIQUES}
        self.assertEqual(du_code, du_doc)

    def test_chaque_rubrique_porte_une_base_legale_datee(self) -> None:
        """Crochet direct de `RM-2026-0089`: un controle sans identifiant
        `LEGIARTI` n'entre pas dans la grille."""
        for r in R.RUBRIQUES:
            with self.subTest(rubrique=r.identifiant):
                s = R.source(r.source)
                self.assertTrue(s.legiarti.startswith("LEGIARTI"))
                self.assertTrue(s.lue_le)
                self.assertIn(s.legiarti, r.citation())
                self.assertIn(s.lue_le, r.citation())

    def test_une_source_inconnue_leve_au_lieu_de_rendre_un_controle_nu(self) -> None:
        with self.assertRaises(KeyError):
            R.source("d19.42")

    def test_un_attendu_fixe_par_le_texte_porte_son_nombre(self) -> None:
        """Trois proces-verbaux, et l'unite est l'assemblee des comptes."""
        pv = R.rubrique("EXT-A-08")
        self.assertEqual(pv.attendu_source, R.ATTENDU_TEXTE)
        self.assertEqual(pv.attendu, 3)
        self.assertIn("appelee a connaitre des comptes", pv.critere_complementaire)

    def test_un_attendu_que_seul_l_occupant_connait_reste_ouvert(self) -> None:
        """Le cas de Brice: 24 pieces au reglement, dont 6 manquent. Aucune
        observation ne peut produire ce 24."""
        rc = R.rubrique("EXT-A-01")
        self.assertEqual(rc.attendu_source, R.ATTENDU_DECLARE)
        self.assertIsNone(rc.attendu)

    def test_le_recouvrement_des_contrats_est_declare(self) -> None:
        self.assertIn("EXT-A-07", R.rubrique("EXT-A-06").recouvre)
        self.assertIn("EXT-A-06", R.rubrique("EXT-A-07").recouvre)

    def test_deux_obligations_qui_se_recouvrent_ne_comptent_qu_une_fois(self) -> None:
        garde = R.dedupliquer({"EXT-A-06", "EXT-A-07"})
        self.assertEqual(len(garde), 1)
        self.assertEqual(garde, {"EXT-A-06"})

    def test_la_liste_des_coproprietaires_interdit_de_capturer_son_contenu(self) -> None:
        """`EXT-C-04` porte l'etat civil, le domicile et l'adresse
        electronique de chaque coproprietaire. La rubrique se constate presente
        ou absente; le reste se fait ailleurs, apres pseudonymisation."""
        liste = R.rubrique("EXT-C-04")
        self.assertIn("jamais", liste.critere_presence + liste.critere_complementaire)
        self.assertIn("RM-2026-0095", liste.critere_complementaire)


class DoctrineTests(unittest.TestCase):
    """La doctrine du lot, sous forme executable."""

    def test_les_verdicts_de_conformite_sont_declares_mais_reserves(self) -> None:
        """`assertIn(CONFORME, ETATS_RESERVES)` ne pouvait pas echouer: la
        constante est definie a la ligne d'a cote. Ce qui compte vraiment est
        que les deux ensembles soient DISJOINTS, et que l'observable ne
        contienne aucun verdict."""
        self.assertEqual(
            set(R.ETATS_OBSERVABLES) & set(R.ETATS_RESERVES), set()
        )
        self.assertEqual(len(R.ETATS_OBSERVABLES), 6)
        for valeur in R.ETATS_OBSERVABLES:
            self.assertNotIn("CONFORME", valeur)

    def test_aucun_producteur_n_ecrit_un_verdict_de_conformite(self) -> None:
        """Le garde-fou qui compte le plus.

        `SERVI_EN_APPARENCE` ne dit rien de la validite d'une piece: une
        attestation d'assurance perimee, un projet de contrat au lieu du
        contrat signe, un extrait au lieu du proces-verbal complet occupent la
        rubrique aussi bien que la bonne piece. C'est le faux servi, et le
        trancher exige de lire - `RM-2026-0093`.
        """
        depot = Path(__file__).resolve().parents[2]
        modules = depot / "server" / "src" / "coproscope" / "modules"
        # Le perimetre etait trop etroit: il ne couvrait ni la facade, ni le
        # journal, ni le magasin, ni **une seule ligne de JavaScript** - alors
        # que c'est le plugin qui parle a l'utilisateur.
        fichiers = list(modules.glob("_extranet_*.py"))
        fichiers.append(modules / "extranetops.py")
        fichiers += sorted((depot / "clients").rglob("*.js"))
        fichiers += sorted((depot / "clients").rglob("*.html"))
        self.assertGreater(len(fichiers), 12, "perimetre du scan trop etroit")
        for chemin in fichiers:
            code = _sans_commentaires(chemin)
            for numero, ligne in enumerate(code.splitlines(), 1):
                nu = ligne.strip()
                if "CONFORME" not in nu:
                    continue
                # Seules trois ecritures sont permises: la declaration des
                # constantes, leur regroupement, et la phrase de garde affichee.
                permis = (
                    "CONFORME = " in nu
                    or "ETATS_RESERVES" in nu
                    or "apparence" in nu.lower()
                )
                with self.subTest(fichier=chemin.name, ligne=numero):
                    self.assertTrue(permis, f"{chemin.name}: {nu}")

    def test_aucun_etat_produit_ne_vaut_conforme(self) -> None:
        """La meme garde, mesuree au lieu d'etre grepee.

        Un scan textuel se contourne par la maniere la plus naturelle
        d'ecrire: importer la constante et l'affecter. Celui-ci execute le
        producteur et regarde ce qui en sort.
        """
        from coproscope.modules import _extranet_conformite as C

        releve = {"rubriques": [
            {"rubrique_code": "REG", "presente": True,
             "pieces": [{"groupe": "", "libelle": "A"}]},
        ]}
        for rattachements in ({}, {"EXT-A-01": ["REG"]}, {"EXT-A-01": ["ABSENT"]}):
            etats = C.etat_par_obligation(releve, rattachements=rattachements)
            rendus = {e["etat"] for e in etats}
            with self.subTest(rattachements=rattachements):
                self.assertTrue(rendus <= set(R.ETATS_OBSERVABLES), rendus)


class ConformiteTests(unittest.TestCase):
    """La jointure: observation x rattachement x attendu."""

    def test_un_editeur_sans_rattachement_ne_produit_aucun_manquement(self) -> None:
        """Le test d'acceptation de la regle dure du depot.

        Un troisieme syndic arrive demain avec des rubriques inconnues. Le code
        doit se degrader proprement, pas rendre une reponse fausse en silence.
        Ici: dix-huit obligations `NON_RATTACHE`, zero manque.
        """
        etats = C.etat_par_obligation(
            _releve([_rub("QUOI", 40), _rub("INCONNU", 12)])
        )
        self.assertEqual(len(etats), 18)
        self.assertTrue(all(e["etat"] == R.NON_RATTACHE for e in etats))
        self.assertEqual(C.manques(etats), [])

    def test_le_cas_reel_du_reglement_de_copropriete(self) -> None:
        """18 pieces vues, 24 declarees, 6 manquantes - le cas de Brice."""
        etats = C.etat_par_obligation(
            _releve([_rub("REG", 18)]),
            rattachements={"EXT-A-01": ["REG"]},
            attendus={"EXT-A-01": 24},
        )
        rc = next(e for e in etats if e["identifiant"] == "EXT-A-01")
        self.assertEqual(rc["etat"], R.SERVI_EN_APPARENCE)
        self.assertEqual(rc["observe"], 18)
        self.assertEqual(rc["attendu"], 24)
        self.assertEqual(rc["ecart"], 6)
        self.assertEqual(rc["compte"], C.COMPTE_ATTRIBUABLE)

    def test_un_emplacement_partage_interdit_de_chiffrer_un_ecart(self) -> None:
        """Le fait qui a decide de la conception.

        Douze pieces dans la rubrique des contrats ne disent pas combien sont
        des assurances. Un ecart calcule la-dessus serait un chiffre faux, et
        un chiffre faux se cite - donc il nuit plus qu'une absence de chiffre.
        """
        etats = C.etat_par_obligation(
            _releve([_rub("CON", 12)]),
            rattachements={
                "EXT-A-05": ["CON"], "EXT-A-06": ["CON"],
                "EXT-A-07": ["CON"], "EXT-A-09": ["CON"],
            },
            attendus={"EXT-A-05": 3},
        )
        assurance = next(e for e in etats if e["identifiant"] == "EXT-A-05")
        self.assertEqual(assurance["compte"], C.COMPTE_PARTAGE)
        self.assertEqual(assurance["etat"], R.SERVI_EN_APPARENCE)
        self.assertNotIn("ecart", assurance)
        # La phrase NOMME les autres obligations. Dire *plusieurs* sonnait
        # comme une excuse; la liste se lit comme de l'honnetete - constat
        # d'une qualification novice du 2026-09-07.
        self.assertIn("Contrat de syndic en cours", assurance["ecart_non_calculable"])
        self.assertEqual(
            sorted(assurance["partage_avec"]),
            ["EXT-A-06", "EXT-A-07", "EXT-A-09"],
        )

    def test_la_banque_devient_exprimable(self) -> None:
        """Deuxieme des trois manques nommes par Brice, et inexprimable avant.

        Les releves du compte separe sont ranges dans la categorie fourre-tout
        de l'editeur. Indexes par code d'editeur, ils se melangeaient a tout le
        reste; indexes par obligation, ils se comptent seuls.
        """
        etats = C.etat_par_obligation(
            _releve([_rub("DIV", 9)]),
            rattachements={"EXT-C-02": ["DIV"]},
            attendus={"EXT-C-02": 12},
        )
        banque = next(e for e in etats if e["identifiant"] == "EXT-C-02")
        self.assertEqual(banque["observe"], 9)
        self.assertEqual(banque["ecart"], 3)

    def test_une_rubrique_non_parcourue_ne_produit_aucune_absence(self) -> None:
        """La regle de couverture, la meme que celle du journal: on ne conclut
        que sur ce qu'on a regarde."""
        etats = C.etat_par_obligation(
            _releve([_rub("REG", 0, presente=False)]),
            rattachements={"EXT-A-01": ["REG"]},
            attendus={"EXT-A-01": 24},
        )
        rc = next(e for e in etats if e["identifiant"] == "EXT-A-01")
        self.assertEqual(rc["etat"], R.NON_PARCOURUE)
        self.assertNotIn("ecart", rc)

    def test_une_rubrique_parcourue_et_vide_est_non_servie(self) -> None:
        etats = C.etat_par_obligation(
            _releve([_rub("JUS", 0)]), rattachements={"EXT-C-03": ["JUS"]}
        )
        justice = next(e for e in etats if e["identifiant"] == "EXT-C-03")
        self.assertEqual(justice["etat"], R.NON_SERVI)

    def test_un_attendu_du_texte_s_applique_sans_etre_declare(self) -> None:
        """Trois proces-verbaux: le nombre vient de l'article, pas de l'humain."""
        etats = C.etat_par_obligation(
            _releve([_rub("ASS", 1)]), rattachements={"EXT-A-08": ["ASS"]}
        )
        pv = next(e for e in etats if e["identifiant"] == "EXT-A-08")
        self.assertEqual(pv["attendu"], 3)
        self.assertEqual(pv["attendu_source"], R.ATTENDU_TEXTE)
        self.assertEqual(pv["ecart"], 2)

    def test_une_dispense_declaree_sort_l_obligation_du_compte(self) -> None:
        etats = C.etat_par_obligation(
            _releve([_rub("ARR", 0)]),
            rattachements={"EXT-B-03": ["ARR"]},
            sans_objet=["EXT-B-03"],
        )
        fonds = next(e for e in etats if e["identifiant"] == "EXT-B-03")
        self.assertEqual(fonds["etat"], R.SANS_OBJET)
        self.assertEqual(C.manques(etats), [])

    def test_chaque_etat_porte_son_fondement_et_ce_qui_reste_a_verifier(self) -> None:
        """Le faux servi, rendu visible sans etre calcule: le compte et le
        critere complementaire voyagent cote a cote, et ne fusionnent jamais."""
        etats = C.etat_par_obligation(
            _releve([_rub("CON", 4)]), rattachements={"EXT-A-05": ["CON"]}
        )
        assurance = next(e for e in etats if e["identifiant"] == "EXT-A-05")
        self.assertIn("LEGIARTI", assurance["fondement"])
        self.assertIn("En cours de validite", assurance["reste_a_verifier"])

    def test_un_manque_de_contrats_ne_compte_pas_deux_fois(self) -> None:
        etats = C.etat_par_obligation(
            _releve([_rub("CON", 0), _rub("MAINT", 0)]),
            rattachements={"EXT-A-06": ["CON"], "EXT-A-07": ["MAINT"]},
        )
        identifiants = {m["identifiant"] for m in C.manques(etats)}
        self.assertEqual(identifiants & {"EXT-A-06", "EXT-A-07"}, {"EXT-A-06"})

    def test_une_coquille_dans_sans_objet_est_refusee(self) -> None:
        """Elle etait avalee en silence: une lettre en moins - `EXT-B-3` pour
        `EXT-B-03` - et l'obligation qu'on croyait ecartee produisait un
        manquement chiffre contre un syndic irreprochable. `rubrique()` existait
        deja et levait une erreur nommee; personne ne s'en servait."""
        with self.assertRaises(KeyError):
            C.etat_par_obligation(
                _releve([_rub("ARR", 0)]),
                rattachements={"EXT-B-03": ["ARR"]},
                sans_objet=["EXT-B-3"],
            )

    def test_le_resume_dit_ce_qui_n_a_pas_ete_regarde(self) -> None:
        """Un compte de manques sans son perimetre se lit comme une couverture
        complete."""
        etats = C.etat_par_obligation(
            _releve([_rub("REG", 18)]),
            rattachements={"EXT-A-01": ["REG"]},
            attendus={"EXT-A-01": 24},
        )
        r = C.resume(etats)
        self.assertEqual(r["obligations"], 18)
        self.assertEqual(r["manques"], 1)
        self.assertEqual(r["non_rattachees"], 17)


class FacadeTests(unittest.TestCase):
    """Depuis un passage reellement ecrit dans le coffre, et non un dictionnaire.

    La forme du coffre n'est pas celle du releve: elle dit `etat` et porte un
    compte deja fait, la ou le releve dit `presente` et porte ses pieces en
    liste. Un test qui ne passerait que par la seconde laisserait la premiere
    lire un compte absent comme un zero - donc fabriquer des manquements.
    """

    class _Instance:
        def __init__(self, racine: Path) -> None:
            self.racine = racine

        def settings(self) -> dict:
            return {"vault": {"local_root": "./vault_local"}}

        def resolve_path(self, valeur: str) -> Path:
            return (self.racine / valeur.lstrip("./")).resolve()

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.instance = self._Instance(self.tmp)
        X.enregistrer_releve(
            self.instance,
            {
                "format": "coproscope.extranet.releve/1",
                "type": "documents",
                "editeur": "coprodirecte",
                "espace": "/espace-copropriete/documents",
                "debut": "2026-09-07T09:00:00Z",
                "fin": "2026-09-07T09:02:00Z",
                "pagination": False,
                "rubriques": [
                    {"rubrique_code": "REG", "presente": True, "pieces": [
                        {"groupe": "", "libelle": f"Acte {i}", "nom_serveur": ""}
                        for i in range(18)
                    ]},
                    {"rubrique_code": "ASS", "presente": False, "pieces": []},
                ],
            },
            "P1",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_le_referentiel_est_expose_par_la_facade(self) -> None:
        self.assertEqual(len(X.referentiel()), 18)

    def test_sans_rattachement_la_facade_ne_rend_aucun_manque(self) -> None:
        rendu = X.conformite(self.instance, "P1")
        self.assertEqual(rendu["manques"], [])
        self.assertEqual(rendu["resume"]["non_rattachees"], 18)

    def test_le_cas_de_brice_depuis_le_coffre(self) -> None:
        """18 actes vus, 24 declares: six manquent, et la rubrique des
        assemblees n'ayant pas ete parcourue, elle ne produit aucune absence."""
        rendu = X.conformite(
            self.instance, "P1",
            rattachements={"EXT-A-01": ["REG"], "EXT-A-08": ["ASS"]},
            attendus={"EXT-A-01": 24},
        )
        etats = {e["identifiant"]: e for e in rendu["etats"]}
        self.assertEqual(etats["EXT-A-01"]["observe"], 18)
        self.assertEqual(etats["EXT-A-01"]["ecart"], 6)
        self.assertEqual(etats["EXT-A-08"]["etat"], R.NON_PARCOURUE)
        self.assertEqual([m["identifiant"] for m in rendu["manques"]], ["EXT-A-01"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
