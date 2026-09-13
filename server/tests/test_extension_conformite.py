"""Le plugin et CoproScope doivent lire le decret de la meme facon.

Deux implantations de la meme regle divergent toujours. Celle-ci divergerait la
ou ca coute le plus cher: le plugin annoncerait un manque que CoproScope ne
verrait pas, ou l'inverse - et c'est exactement sur ce genre de constat qu'un
conseil syndical ecrit a son syndic.

Le fichier tient donc deux choses:

1. que `clients/extension-navigateur/referentiel.js` porte les **memes 18
   obligations** que `_extranet_referentiel.py`, avec les memes fondements et
   les memes attendus;
2. que sur les memes entrees, les deux implantations rendent les **memes
   etats** - y compris dans les cas ou elles doivent refuser de conclure.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import _extranet_conformite as C
from coproscope.modules import _extranet_referentiel as R

RACINE = Path(__file__).resolve().parents[2] / "clients" / "extension-navigateur"
EXECUTEUR = RACINE / "tests" / "executer-conformite.mjs"
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"


def _rub(code: str, nb: int, presente: bool = True) -> dict:
    return {
        "rubrique_code": code,
        "presente": presente,
        "pieces": [{"groupe": "", "libelle": f"P{i}"} for i in range(nb)],
    }


def _releve(rubriques: list[dict]) -> dict:
    return {"espace": "/espace-copropriete/documents", "rubriques": rubriques}


#: Chaque scenario porte un cas ou les deux implantations pourraient diverger.
SCENARIOS = {
    "editeur_inconnu": {
        "releve": _releve([_rub("QUOI", 40), _rub("BIDULE", 12)]),
        "rattachements": {},
        "attendus": {},
    },
    "reglement_de_copropriete": {
        "releve": _releve([_rub("REG", 18)]),
        "rattachements": {"EXT-A-01": ["REG"]},
        "attendus": {"EXT-A-01": 24},
    },
    "contrats_emplacement_partage": {
        "releve": _releve([_rub("CON", 12)]),
        "rattachements": {
            "EXT-A-05": ["CON"], "EXT-A-06": ["CON"],
            "EXT-A-07": ["CON"], "EXT-A-09": ["CON"],
        },
        "attendus": {"EXT-A-05": 3},
    },
    "banque_dans_le_fourre_tout": {
        "releve": _releve([_rub("DIV", 9)]),
        "rattachements": {"EXT-C-02": ["DIV"]},
        "attendus": {"EXT-C-02": 12},
    },
    "rubrique_non_parcourue": {
        "releve": _releve([_rub("REG", 0, presente=False)]),
        "rattachements": {"EXT-A-01": ["REG"]},
        "attendus": {"EXT-A-01": 24},
    },
    "attendu_du_texte": {
        "releve": _releve([_rub("ASS", 1)]),
        "rattachements": {"EXT-A-08": ["ASS"]},
        "attendus": {},
    },
    "deux_contrats_absents_ne_comptent_qu_une_fois": {
        "releve": _releve([_rub("CON", 0), _rub("MAINT", 0)]),
        "rattachements": {"EXT-A-06": ["CON"], "EXT-A-07": ["MAINT"]},
        "attendus": {},
    },
    # --- les quatre defauts trouves par la verification adverse du 2026-09-07 ---
    "attendu_declare_a_zero": {
        "releve": _releve([_rub("JUS", 0)]),
        "rattachements": {"EXT-C-03": ["JUS"]},
        "attendus": {"EXT-C-03": 0},
    },
    "couverture_incomplete": {
        "releve": _releve([_rub("ARR", 1), _rub("DIV", 0, presente=False)]),
        "rattachements": {"EXT-A-08": ["ARR", "DIV"]},
        "attendus": {},
    },
    "rattachement_declare_deux_fois": {
        "releve": _releve([_rub("ARR", 2)]),
        "rattachements": {"EXT-A-08": ["ARR", "ARR"]},
        "attendus": {},
    },
    "code_editeur_mal_saisi": {
        "releve": _releve([_rub("ARR", 4)]),
        "rattachements": {"EXT-A-01": [" "], "EXT-A-02": [""], "EXT-A-03": [" ARR "]},
        "attendus": {},
    },
    "attendu_vide_ou_decimal": {
        "releve": _releve([_rub("REG", 5)]),
        "rattachements": {"EXT-A-01": ["REG"], "EXT-A-04": ["REG"]},
        "attendus": {"EXT-A-01": "", "EXT-A-04": 7.9},
    },
    # --- ce que l'epreuve sur un SECOND CABINET a mesure, le 2026-09-07 ---
    "trois_justifications_un_seul_contrat": {
        "releve": _releve([_rub("CON", 1)]),
        "rattachements": {"EXT-C-05": ["CON"]},
        "attendus": {},
    },
    "copropriete_sans_fonds_ni_compte_separe": {
        "releve": _releve([_rub("ARR", 0), _rub("DIV", 0)]),
        "rattachements": {"EXT-B-03": ["ARR"], "EXT-C-02": ["DIV"]},
        "attendus": {},
    },
    "une_serie_mensuelle_declaree": {
        "releve": _releve([_rub("DIV", 9)]),
        "rattachements": {"EXT-C-02": ["DIV"]},
        "attendus": {"EXT-C-02": 12},
    },
    "dispense_declaree": {
        "releve": _releve([_rub("ARR", 0)]),
        "rattachements": {"EXT-B-03": ["ARR"]},
        "attendus": {},
        "sans_objet": ["EXT-B-03"],
    },
}

#: Les champs que les deux cotes doivent rendre identiques. `emplacements` et
#: les libelles longs en font partie: c'est ce que l'utilisateur lit.
CHAMPS = (
    "etat", "observe", "attendu", "ecart", "compte", "attendu_source",
    # Ajoutes le 2026-09-07: la verification adverse a montre que les deux
    # implantations divergeaient sur `emplacements` sans que le test le voie.
    "emplacements", "emplacements_parcourus", "emplacements_non_parcourus",
    "ecart_non_calculable", "condition", "reserve_sur_le_compte",
    "partage_avec",
)


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
        raise AssertionError(f"executer-conformite.mjs a echoue:\n{rendu.stderr[:2000]}")
    return json.loads(rendu.stdout)


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class ListeLegaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _executer()

    def test_les_deux_listes_portent_les_memes_obligations(self) -> None:
        du_js = [o["id"] for o in self.js["obligations"]]
        du_py = [o.identifiant for o in R.LISTE_MINIMALE]
        self.assertEqual(du_js, du_py)

    def test_le_fichier_est_bien_CE_QUE_LE_GENERATEUR_PRODUIT(self) -> None:
        """Le test qui manquait a la rectification `baecb2d`.

        Un message de commit avait affirme que `referentiel.js` etait GENERE
        depuis le module Python. C'etait faux au moment ou je l'ai ecrit: le
        fichier avait ete produit une fois par un script jetable, jamais
        commite, puis maintenu a la main - exactement le risque que le reste du
        message decrivait.

        J'ai rendu l'affirmation vraie en ecrivant `tools/generer_referentiel_js.py`,
        mais **sans test**. Rien n'empechait donc le fichier de rederiver, ni la
        meme affirmation fausse de revenir par le meme chemin.

        Les autres tests comparent les CHAMPS un a un: ils verraient une
        obligation qui change, pas un fichier edite a la main dont le contenu
        se trouve coincider. Celui-ci compare les OCTETS, et c'est le
        mecanisme - *ce fichier est genere* - qui est fige, pas les dix-huit
        valeurs.
        """
        import io
        import runpy
        from contextlib import redirect_stdout

        depot = Path(__file__).resolve().parents[2]
        generateur = depot / "tools" / "generer_referentiel_js.py"
        cible = depot / "clients" / "extension-navigateur" / "referentiel.js"
        self.assertTrue(generateur.exists(), "le generateur a disparu")

        avant = cible.read_bytes()
        try:
            with redirect_stdout(io.StringIO()):
                # `run_name` doit rester different de `__main__`, sinon le
                # `raise SystemExit` du generateur remonte ici - mais il faut
                # alors appeler `main()` SOI-MEME. Ma premiere version ne le
                # faisait pas: le generateur ne s'executait jamais, le fichier
                # n'etait jamais reecrit, et le test comparait donc les octets
                # a eux-memes. Une tautologie, ecrite en corrigeant une
                # tautologie - verifiee en collant une ligne a la main dans le
                # fichier: le test passait quand meme.
                espace = runpy.run_path(str(generateur), run_name="__essai__")
                espace["main"]()
            apres = cible.read_bytes()
        finally:
            cible.write_bytes(avant)
        self.assertEqual(
            avant,
            apres,
            "`referentiel.js` n'est plus ce que le generateur produit: il a ete "
            "edite a la main. Relancer `tools/generer_referentiel_js.py`.",
        )

    def test_chaque_obligation_porte_le_meme_fondement_des_deux_cotes(self) -> None:
        """Un fondement qui derive est pire qu'un fondement absent: il serait
        cite devant un syndic sous une version que personne n'a lue."""
        par_id = {o["id"]: o for o in self.js["obligations"]}
        for o in R.LISTE_MINIMALE:
            with self.subTest(obligation=o.identifiant):
                self.assertEqual(par_id[o.identifiant]["fondement"], o.citation())
                self.assertEqual(par_id[o.identifiant]["intitule"], o.intitule)
                self.assertEqual(par_id[o.identifiant]["attendu_source"], o.attendu_source)
                self.assertEqual(par_id[o.identifiant]["attendu"], o.attendu)
                self.assertEqual(
                    tuple(par_id[o.identifiant]["recouvre"]), o.recouvre
                )


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class MemesEtatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _executer()

    def _python(self, nom: str) -> dict[str, dict]:
        s = SCENARIOS[nom]
        etats = C.etat_par_obligation(
            s["releve"],
            rattachements=s.get("rattachements"),
            attendus=s.get("attendus"),
            sans_objet=s.get("sans_objet", ()),
        )
        return {e["identifiant"]: e for e in etats}

    def test_les_deux_implantations_rendent_les_memes_etats(self) -> None:
        for nom in SCENARIOS:
            attendu = self._python(nom)
            obtenu = {e["id"]: e for e in self.js["scenarios"][nom]["etats"]}
            with self.subTest(scenario=nom):
                self.assertEqual(sorted(obtenu), sorted(attendu))
                for identifiant, py in attendu.items():
                    js = obtenu[identifiant]
                    for champ in CHAMPS:
                        self.assertEqual(
                            js.get(champ), py.get(champ),
                            f"{nom}/{identifiant}: champ {champ}",
                        )

    def test_les_memes_manques_deduplication_faite(self) -> None:
        for nom in SCENARIOS:
            attendu = sorted(
                m["identifiant"]
                for m in C.manques(list(self._python(nom).values()))
            )
            with self.subTest(scenario=nom):
                self.assertEqual(
                    sorted(self.js["scenarios"][nom]["manques"]), attendu
                )

    def test_un_editeur_inconnu_ne_produit_aucun_manque_des_deux_cotes(self) -> None:
        """Le test d'acceptation de la regle dure, tenu aussi cote navigateur.

        C'est le plugin qui parle a l'utilisateur; s'il inventait un manquement
        la ou le Python n'en voit pas, la garde du Python ne servirait a rien.
        """
        cas = self.js["scenarios"]["editeur_inconnu"]
        self.assertEqual(cas["manques"], [])
        self.assertTrue(all(e["etat"] == "NON_RATTACHE" for e in cas["etats"]))

    def test_un_emplacement_partage_refuse_de_chiffrer_des_deux_cotes(self) -> None:
        etats = {
            e["id"]: e for e in self.js["scenarios"]["contrats_emplacement_partage"]["etats"]
        }
        self.assertEqual(etats["EXT-A-05"]["compte"], "EMPLACEMENT_PARTAGE")
        self.assertNotIn("ecart", etats["EXT-A-05"])
        self.assertIn("ecart_non_calculable", etats["EXT-A-05"])


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class DefautsTrouvesParVerificationAdverseTests(unittest.TestCase):
    """Quatre defauts trouves le 2026-09-07 par un agent charge de me refuter.

    Les quatre etaient identiques des deux cotes, donc invisibles au test de
    conformite: deux implantations qui se trompent pareil se ressemblent.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _executer()

    def _etat(self, scenario: str, identifiant: str) -> dict:
        return next(
            e for e in self.js["scenarios"][scenario]["etats"] if e["id"] == identifiant
        )

    def test_un_attendu_declare_a_zero_ne_produit_pas_de_manque(self) -> None:
        """*Aucune piece attendue ici* est un renseignement, pas une absence.

        Le compte testait `NON_SERVI or ecart > 0`, jamais l'ecart reel: zero
        observe sur zero attendu ressortait manquant.
        """
        self.assertNotIn("EXT-C-03", self.js["scenarios"]["attendu_declare_a_zero"]["manques"])

    def test_un_ecart_ne_se_chiffre_pas_sur_une_couverture_incomplete(self) -> None:
        """Le module refusait de chiffrer sur un emplacement partage mais
        l'acceptait sur un angle mort - c'est le meme mode de defaillance.

        Chiffrer un manque sur une rubrique qu'on n'a pas ouverte revient a
        compter comme absentes des pieces qu'on n'a pas regardees.
        """
        etat = self._etat("couverture_incomplete", "EXT-A-08")
        self.assertEqual(etat["compte"], "COUVERTURE_INCOMPLETE")
        self.assertNotIn("ecart", etat)
        self.assertIn("DIV", etat["ecart_non_calculable"])
        self.assertEqual(self.js["scenarios"]["couverture_incomplete"]["manques"], [])

    def test_un_rattachement_declare_deux_fois_ne_double_pas_le_compte(self) -> None:
        """Un doublon de saisie faisait passer deux pieces pour quatre, donc
        effacait un manquement reel - sans aucune alerte."""
        etat = self._etat("rattachement_declare_deux_fois", "EXT-A-08")
        self.assertEqual(etat["emplacements"], ["ARR"])
        self.assertEqual(etat["observe"], 2)
        self.assertEqual(etat["ecart"], 1)

    def test_un_code_mal_saisi_dit_je_ne_sais_pas_et_non_je_n_ai_pas_regarde(self) -> None:
        """Un code vide se deguisait en `NON_PARCOURUE`. Les deux etats
        n'appellent pas le meme geste: corriger la saisie, ou aller voir."""
        self.assertEqual(self._etat("code_editeur_mal_saisi", "EXT-A-01")["etat"],
                         "NON_RATTACHE")
        self.assertEqual(self._etat("code_editeur_mal_saisi", "EXT-A-02")["etat"],
                         "NON_RATTACHE")
        # Les espaces autour d'un code valide sont enleves, pas rejetes.
        rogne = self._etat("code_editeur_mal_saisi", "EXT-A-03")
        self.assertEqual(rogne["etat"], "SERVI_EN_APPARENCE")
        self.assertEqual(rogne["observe"], 4)

    def test_un_attendu_vide_ou_decimal_se_lit_pareil_des_deux_cotes(self) -> None:
        """Le Python levait sur une chaine vide la ou le navigateur l'ignorait,
        et les deux arrondissaient differemment un decimal. Une saisie effacee
        est une entree banale: deux lectures qui divergent la-dessus finissent
        par diverger sur un constat."""
        vide = self._etat("attendu_vide_ou_decimal", "EXT-A-01")
        self.assertNotIn("attendu", vide)
        decimal = self._etat("attendu_vide_ou_decimal", "EXT-A-04")
        self.assertEqual(decimal["attendu"], 7)


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class SecondCabinetTests(unittest.TestCase):
    """Ce qu'un second corpus a mesure, et que le premier ne pouvait pas dire.

    `instances/erables_pseudo_test` porte 22 PDF d'un second cabinet. Il ne
    contient aucune page d'extranet, donc il n'eprouve pas le lecteur - mais il
    eprouve le REFERENTIEL, qui est du droit applique par quelqu'un d'autre.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _executer()

    def _etat(self, scenario: str, identifiant: str) -> dict:
        return next(
            e for e in self.js["scenarios"][scenario]["etats"] if e["id"] == identifiant
        )

    def test_trois_justifications_peuvent_tenir_dans_un_seul_document(self) -> None:
        """Le contre-exemple mesure, et il vient du corpus.

        Chez le second cabinet, la carte professionnelle, l'assurance et la
        garantie financiere de `EXT-C-05` sont **trois mentions en tete du
        contrat de syndic**, pas trois fichiers. Compter les fichiers produisait
        un manquement chiffre a deux, sur un emplacement que le module croyait
        exclusif - donc sans aucun garde-fou.

        Le texte fixe trois JUSTIFICATIONS. Le comptage de pieces ne sait pas
        les compter, et il le dit maintenant.
        """
        etat = self._etat("trois_justifications_un_seul_contrat", "EXT-C-05")
        self.assertEqual(etat["observe"], 1)
        self.assertNotIn("ecart", etat)
        self.assertEqual(
            self.js["scenarios"]["trois_justifications_un_seul_contrat"]["manques"], []
        )

    def test_une_obligation_conditionnelle_sans_attendu_n_est_pas_un_manque(self) -> None:
        """Une copropriete sans fonds de travaux et sans compte separe recoltait
        deux lignes rouges **contre un syndic irreprochable**.

        Le texte conditionne les deux: *du seulement si le syndicat dispose d'un
        fonds de travaux*, et *le cas echeant* pour le compte separe. *Je ne
        sais pas combien il en faut* plus *elle n'est pas toujours due* ne font
        pas un manquement - le module distingue partout ailleurs *je n'ai pas
        vu* de *il n'y a rien*.
        """
        cas = self.js["scenarios"]["copropriete_sans_fonds_ni_compte_separe"]
        self.assertEqual(cas["manques"], [])
        for identifiant in ("EXT-B-03", "EXT-C-02"):
            with self.subTest(obligation=identifiant):
                self.assertIn("condition", self._etat(
                    "copropriete_sans_fonds_ni_compte_separe", identifiant))

    def test_une_serie_declaree_se_compte_mais_la_reserve_voyage(self) -> None:
        """La distinction affinee par un test qui a echoue.

        Avoir range les quatre unites non-`TEXTE` ensemble faisait perdre
        *banque*, un des trois manques que Brice avait nommes: un humain peut
        dire *j'attends douze releves mensuels*, et compter douze fichiers a du
        sens. Ce que l'observation ne sait pas y faire, c'est verifier l'absence
        de trou - une reserve a afficher, pas une raison de refuser le compte.
        """
        etat = self._etat("une_serie_mensuelle_declaree", "EXT-C-02")
        self.assertEqual(etat["observe"], 9)
        self.assertEqual(etat["attendu"], 12)
        self.assertEqual(etat["ecart"], 3)
        self.assertIn("sans trou", etat["reserve_sur_le_compte"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
