"""Le releve transmis par le plugin, et l'export pour recoupement entre voisins.

Demande de Brice du 2026-09-04: *"je veux que les infos soient exportables, pour
que d'autres voisins puissent monitorer et qu'on puisse recouper les
changements"*.

Aucune donnee reelle: tout est synthetique.
"""

from __future__ import annotations

import base64
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import _extranet_echange as E
from coproscope.modules import _extranet_store as S
from coproscope.modules import extranetops as X
from coproscope.modules._extranet_releve import FORMAT, ReleveInvalide

SEL = "sel-de-la-copro-abc"


class _Instance:
    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()


def _releve(pieces_arr, presente_ass=True, pagination=False) -> dict:
    return {
        "format": FORMAT,
        "type": "documents",
        "editeur": "coprodirecte",
        "espace": "/espace-copropriete/documents",
        "debut": "2026-09-04T09:00:00Z",
        "fin": "2026-09-04T09:01:00Z",
        "pagination": pagination,
        "rubriques": [
            {"rubrique_code": "ARR", "presente": True, "pieces": pieces_arr},
            {"rubrique_code": "ASS", "presente": presente_ass, "pieces": []},
        ],
    }


def _p(groupe: str, libelle: str, nom: str = "") -> dict:
    return {"groupe": groupe, "libelle": libelle, "nom_serveur": nom}


class ReleveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_un_releve_du_plugin_devient_un_passage(self) -> None:
        charge = _releve([_p("Au 31/12/2025", "Annexe 1"), _p("Au 31/12/2024", "Annexe 1")])
        comptes = X.enregistrer_releve(self.instance, charge, "P1")
        self.assertEqual(comptes["pieces"], 2)
        lu = S.lire_passage(self.instance, "P1")
        self.assertEqual(len({p["emplacement"] for p in lu["pieces"]}), 2)

    def test_un_format_inconnu_est_refuse_au_lieu_d_etre_lu_au_mieux(self) -> None:
        """Un releve mal lu ne produit pas une erreur, il produit de faux retraits."""
        charge = _releve([_p("G", "L")])
        charge["format"] = "autre/9"
        with self.assertRaises(ReleveInvalide):
            X.enregistrer_releve(self.instance, charge, "P1")

    def test_une_rubrique_non_declaree_est_refusee(self) -> None:
        charge = _releve([_p("G", "L")])
        charge["rubriques"].append({"rubrique_code": "XXX", "presente": True, "pieces": []})
        with self.assertRaises(ReleveInvalide):
            X.enregistrer_releve(self.instance, charge, "P1")

    def test_une_rubrique_absente_de_la_page_reste_non_exploree(self) -> None:
        charge = _releve([_p("G", "L")], presente_ass=False)
        X.enregistrer_releve(self.instance, charge, "P1")
        etats = {
            r["rubrique_code"]: r["etat"] for r in S.lire_passage(self.instance, "P1")["rubriques"]
        }
        self.assertEqual(etats["ASS"], "NON_EXPLOREE")

    def test_les_lignes_de_depenses_sans_facture_ne_sont_pas_des_pieces(self) -> None:
        charge = {
            "format": FORMAT, "type": "depenses", "editeur": "coprodirecte",
            "espace": "/espace-copropriete/depenses", "debut": "2026-09-04T09:00:00Z",
            "fin": "", "pagination": False,
            "rubriques": [{"rubrique_code": "CHARGES GENERALES", "presente": True, "lignes": [
                {"colonnes": ["12/03/2025", "Entretien", "Prestation", "120,00"],
                 "a_une_facture": True, "nom_serveur": "f1.pdf"},
                {"colonnes": ["15/04/2025", "Eau", "Releve", "80,00"],
                 "a_une_facture": False, "nom_serveur": ""},
            ]}],
        }
        comptes = X.enregistrer_releve(self.instance, charge, "P1")
        self.assertEqual(comptes["pieces"], 1)


class DeuxSelsTests(unittest.TestCase):
    """Deux sels coexistent dans CoproScope, et leurs buts sont OPPOSES.

    Constat du 2026-09-07, ne, comme souvent, d'une question de Brice: *la
    passe d'anonymisation instruit-elle bien un annuaire sale ?* La reponse est
    oui - et la verifier a fait apparaitre que le produit portait desormais
    deux sels que rien ne distinguait.

    Le sel d'alias de BiffageOps est propre a une **instance**, pour que deux
    coffres de coproprietaires voisins ne produisent JAMAIS le meme alias pour
    la meme personne. Le sel d'echange de ce module est partage entre les
    voisins d'une **copropriete**, pour que leurs empreintes COINCIDENT.

    Les confondre casse en silence dans les deux sens, et c'est pour cela que
    la garde est active plutot que documentaire.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _passage(self) -> str:
        X.enregistrer_releve(self.instance, _releve([_p("Au 31/12/2025", "Annexe 1")]), "P1")
        return "P1"

    def test_le_sel_d_alias_de_l_instance_est_refuse_a_l_export(self) -> None:
        from coproscope.modules import biffageops

        alias = biffageops.load_corpus_salt(self.instance)
        passage = self._passage()
        with self.assertRaises(X.SelInterdit):
            X.exporter_passage(
                self.instance,
                passage,
                sel=base64.b64encode(alias).decode("ascii"),
                observateur="voisin A",
            )

    def test_un_sel_choisi_par_le_conseil_syndical_passe(self) -> None:
        from coproscope.modules import biffageops

        biffageops.load_corpus_salt(self.instance)  # l'instance a bien un sel d'alias
        paquet = X.exporter_passage(
            self.instance, self._passage(), sel="secret-du-conseil", observateur="voisin A"
        )
        self.assertTrue(paquet["pieces"])

    def test_exporter_ne_cree_jamais_de_sel_d_alias(self) -> None:
        """Le piege qu'un `create=True` par defaut aurait pose.

        Sans `create=False`, exporter un journal d'extranet **fabriquerait** le
        sel d'alias d'une instance qui n'en a pas - donc le materiau d'une
        pseudonymisation que personne n'a demandee, et sur un geste qui n'a
        aucun rapport.
        """
        from coproscope.modules import biffageops

        chemin = biffageops.corpus_salt_path(self.instance)
        X.exporter_passage(
            self.instance, self._passage(), sel="secret-du-conseil", observateur="voisin A"
        )
        self.assertFalse(chemin.exists(), f"un sel d'alias a ete cree: {chemin}")

    def test_les_deux_mondes_ne_se_citent_jamais(self) -> None:
        """La frontiere, tenue de facon executable.

        Un jour quelqu'un aura besoin d'un sel dans `_extranet_echange` et le
        prendra la ou il en existe deja un. Ce test lui dira pourquoi c'est
        exactement l'inverse de ce qu'il faut faire.

        La frontiere porte sur le **code**, pas sur la prose: la docstring du
        module nomme au contraire `sel_alias.key` et explique l'opposition,
        parce que c'est ce qui empeche la confusion. Interdire de la nommer
        reviendrait a supprimer la seule chose qui previent la faute.
        """
        import ast

        racine = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "modules"
        source = (racine / "_extranet_echange.py").read_text(encoding="utf-8")
        arbre = ast.parse(source)
        arbre.body = [n for n in arbre.body if not (
            isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
        )]
        code = ast.unparse(arbre)
        for interdit in ("load_corpus_salt", "sel_alias", "corpus_caviarde",
                         "RegistrePseudonymes", "biffageops"):
            self.assertNotIn(interdit, code, f"_extranet_echange emploie {interdit}")
        for part in sorted((racine / "_biffageops_parts").glob("*.py")):
            self.assertNotIn("_extranet_echange", part.read_text(encoding="utf-8"), part.name)

    def test_le_domaine_rend_les_deux_familles_inconfondables(self) -> None:
        """Meme a sel egal, une empreinte d'extranet n'est pas un alias.

        C'est la garde qui survit a toutes les autres: si un jour la
        verification active etait contournee, les valeurs produites resteraient
        incapables de relier les deux mondes.
        """
        import hashlib

        sel, valeur = "meme-sel", "meme-valeur"
        nu = hashlib.sha256(f"{sel}\x00{valeur}".encode("utf-8")).hexdigest()[:32]
        self.assertNotEqual(E.empreinte(valeur, sel), nu)
        self.assertIn(b"extranet", E.DOMAINE)


class CompatibiliteExtensionTests(unittest.TestCase):
    """Les empreintes du plugin et celles de CoproScope doivent coincider.

    Deux implantations de la meme fonction divergent toujours, et ici la
    divergence ne se verrait qu'au recoupement, sous la forme d'un zero de
    concordance - que deux voisins liraient comme un desaccord entre eux.

    Ces valeurs ont ete calculees des deux cotes: par ce module, et par
    `clients/extension-navigateur/journal.js`. Elles sont identiques. Toute
    evolution qui les changerait doit changer les deux cotes, et ce test est la
    pour l'imposer.

    **Elles ont change une fois, le 2026-09-07, et volontairement.** Les
    empreintes portent desormais un domaine cryptographique
    (`_extranet_echange.DOMAINE`), pour qu'une empreinte d'extranet ne puisse
    jamais etre confondue avec une valeur produite ailleurs dans le produit -
    en particulier avec un alias de BiffageOps, dont le sel poursuit le but
    exactement OPPOSE. Le format est passe a `observation/2`. La rupture etait
    gratuite: l'extension n'a jamais ete distribuee et aucun export reel n'a
    circule. Elle ne l'aurait plus ete ensuite.
    """

    #: separateur des composantes, et separateur du sel. Ecrits en clair ici
    #: pour que le vecteur reste lisible.
    SEP = chr(31)
    NUL = chr(0)

    def test_le_vecteur_de_reference_ne_bouge_pas(self) -> None:
        cle = self.SEP.join(["ARR", "Au 31/12/2025", "Annexe 1"])
        self.assertEqual(
            E.empreinte(cle, "sel-test"), "ea76ab476af9fc9db7f13815ae4eb630"
        )

    def test_le_temoin_de_sel_ne_bouge_pas(self) -> None:
        self.assertEqual(E.temoin_sel("sel-test"), "8a05629a938645f7")

    def test_le_sel_est_separe_de_la_valeur_par_un_octet_nul(self) -> None:
        """Sans separateur, deux couples (sel, valeur) differents pourraient
        donner la meme empreinte - il suffirait de deplacer la frontiere."""
        self.assertNotEqual(E.empreinte("bc", "a"), E.empreinte("c", "ab"))


class ExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.tmp)
        X.enregistrer_releve(
            self.instance,
            _releve([_p("Au 31/12/2025", "Annexe 1", "f-1.pdf"),
                     _p("Au 31/12/2024", "Annexe 1", "f-2.pdf")]),
            "P1",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_aucun_libelle_ni_nom_de_fichier_ne_sort(self) -> None:
        """La garde qui rend l'export transmissible.

        Un extranet de copropriete porte des donnees de tiers, et un fichier
        d'echange se retrouve toujours quelque part.
        """
        paquet = X.exporter_passage(self.instance, "P1", sel=SEL, observateur="voisin A")
        texte = repr(paquet)
        for interdit in ("Annexe 1", "f-1.pdf", "f-2.pdf", "Au 31/12/2025"):
            self.assertNotIn(interdit, texte)
        self.assertNotIn(SEL, texte)

    def test_deux_observateurs_du_meme_sel_se_recoupent(self) -> None:
        a = X.exporter_passage(self.instance, "P1", sel=SEL, observateur="voisin A")
        b = X.exporter_passage(self.instance, "P1", sel=SEL, observateur="voisin B")
        res = X.recouper(a, b)
        self.assertEqual(res["nb_corrobores"], 2)
        self.assertEqual(res["divergences_dans_couverture_commune"], [])

    def test_deux_sels_differents_le_disent_au_lieu_de_rendre_zero(self) -> None:
        """Un zero de concordance serait lu comme un desaccord entre voisins.

        C'est un probleme de configuration, et le dire vaut mieux que laisser
        deux personnes conclure qu'elles n'ont rien vu de commun.
        """
        a = X.exporter_passage(self.instance, "P1", sel=SEL, observateur="A")
        b = X.exporter_passage(self.instance, "P1", sel="autre-sel", observateur="B")
        with self.assertRaises(E.SelDifferent):
            X.recouper(a, b)

    def test_un_sel_vide_est_refuse(self) -> None:
        """Sans sel, l'export devient un oracle a hypotheses."""
        with self.assertRaises(ValueError):
            X.exporter_passage(self.instance, "P1", sel="", observateur="A")

    def test_un_ecart_hors_couverture_n_est_pas_une_divergence(self) -> None:
        """Le tri entre les deux causes d'ecart se fait par la couverture.

        Un ecart dans une rubrique que l'autre n'a pas parcourue n'apprend rien.
        Le meme ecart dans une rubrique parcourue par les deux est une question.
        """
        a = X.exporter_passage(self.instance, "P1", sel=SEL, observateur="A")
        b = {
            "format": E.FORMAT, "temoin_sel": E.temoin_sel(SEL), "observateur": "B",
            "editeur": "coprodirecte", "espace": "", "debut": "", "fin": "",
            # Depuis le format `/3`, le code de rubrique voyage EMPREINT: sur
            # une page de depenses il porterait sinon un libelle et un montant.
            "rubriques": [{"emp_rubrique": E.empreinte("ARR", SEL),
                           "etat": "NON_EXPLOREE",
                           "cloture": "AUCUNE", "nb_pieces": "0"}],
            "pieces": [],
        }
        res = X.recouper(a, b)
        self.assertEqual(res["divergences_dans_couverture_commune"], [])
        self.assertEqual(len(res["seulement_mien_hors_couverture"]), 2)

    def test_la_couverture_du_groupe_est_l_union_des_couvertures(self) -> None:
        """Le gain immediat du monitorage a plusieurs, avant toute comparaison."""
        a = X.exporter_passage(self.instance, "P1", sel=SEL, observateur="A")
        b = dict(a)
        b["rubriques"] = [{"emp_rubrique": E.empreinte("ASS", SEL),
                           "etat": "PARCOURUE",
                           "cloture": "CONSTATEE", "nb_pieces": "3"}]
        fusion = E.fusionner_couverture([a, b])
        self.assertEqual(fusion[E.empreinte("ARR", SEL)], "PARCOURUE")
        self.assertEqual(fusion[E.empreinte("ASS", SEL)], "PARCOURUE")


class ReservesTests(unittest.TestCase):
    """Ce qui est declare sans etre branche, et qui doit le rester."""

    def test_fusionner_couverture_n_a_aucun_appelant_en_production(self) -> None:
        """La reserve, tenue de facon executable.

        Elle appartient a `RM-2026-0092`, la consolidation entre
        coproprietaires. La brancher aujourd'hui donnerait un gain de
        couverture calcule sur un seul journal, donc toujours egal a ce
        journal: un chiffre juste et inutile, que quelqu'un finirait par citer.

        Le jour ou elle sera branchee, ce test echouera - et c'est exactement
        ce qu'on attend de lui: forcer a relire la reserve avant de la lever.
        """
        racine = Path(__file__).resolve().parents[1] / "src" / "coproscope"
        appels = []
        for chemin in racine.rglob("*.py"):
            texte = chemin.read_text(encoding="utf-8")
            for numero, ligne in enumerate(texte.splitlines(), 1):
                if "fusionner_couverture" not in ligne:
                    continue
                if ligne.lstrip().startswith(("#", "*", '"', "'")):
                    continue
                if "def fusionner_couverture" in ligne:
                    continue
                appels.append(f"{chemin.name}:{numero}")
        self.assertEqual(appels, [], f"appelants trouves: {appels}")


class FuiteExportTests(unittest.TestCase):
    """L'export ne porte ni libelle ni montant - y compris sur les depenses.

    Defaut trouve le 2026-09-07 par une relecture de doctrine. Le code de
    rubrique circulait EN CLAIR. Sur un index c'est anodin - `ARR`, `CON` -
    mais sur une page de depenses ce code est **decouvert** et non declare:
    c'est l'en-tete du groupe de charges, donc un libelle ET un montant.

    La docstring de ce module jurait pourtant, mot pour mot, que les montants
    ne circulent jamais. C'est le fichier destine a partir chez un voisin.
    """

    def test_un_en_tete_de_charges_ne_sort_pas_en_clair(self) -> None:
        import json

        entete = "CHAUFFAGE COLLECTIF 48 217,43 EUR"
        paquet = E.exporter(
            {"editeur": "x", "espace": "/depenses", "debut": "d", "fin": "f"},
            [{"rubrique_code": entete, "etat": "PARCOURUE",
              "cloture": "CONSTATEE", "nb_pieces": "3"}],
            [{"rubrique_code": entete, "emplacement": "e",
              "nom_serveur": "", "empreinte": ""}],
            sel=SEL, observateur="voisin A",
        )
        serialise = json.dumps(paquet)
        for interdit in ("CHAUFFAGE", "48 217,43", "EUR"):
            with self.subTest(fragment=interdit):
                self.assertNotIn(interdit, serialise)

    def test_le_recoupement_fonctionne_a_l_identique(self) -> None:
        """Empreindre le code ne coute rien au recoupement: deux voisins qui
        partagent le sel obtiennent la meme valeur."""
        def paquet(observateur):
            return E.exporter(
                {"editeur": "x", "espace": "/d", "debut": "d", "fin": "f"},
                [{"rubrique_code": "ARR", "etat": "PARCOURUE",
                  "cloture": "CONSTATEE", "nb_pieces": "1"}],
                [{"rubrique_code": "ARR", "emplacement": "meme piece",
                  "nom_serveur": "", "empreinte": ""}],
                sel=SEL, observateur=observateur,
            )
        res = E.recouper(paquet("A"), paquet("B"))
        self.assertEqual(res["nb_corrobores"], 1)
        self.assertEqual(len(res["rubriques_communes"]), 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
