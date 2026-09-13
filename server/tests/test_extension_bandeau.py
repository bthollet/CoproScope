"""Le bandeau pose dans la page - la seule surface visible sans ouvrir le plugin.

Ce fichier existe a cause d'un defaut trouve le 2026-09-07: le code du bandeau
n'avait **jamais** ete execute sous test. `mini-dom.mjs` ne fabriquait ni
`body`, ni `createElement`, ni `attachShadow`, de sorte que `poserBandeau`
sortait a chaque passage par sa propre garde - celle qui protege la production,
et qui masquait donc l'absence totale de couverture.

C'est le pire endroit ou avoir un angle mort: le bandeau est ce que
l'utilisateur voit sans rien ouvrir, et un bandeau muet se lit *tout va bien*.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2] / "clients" / "extension-navigateur"
EXECUTEUR = RACINE / "tests" / "executer-bandeau.mjs"
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"


#: La structure reellement servie par l'editeur, relevee le 2026-09-04: deux
#: liens par piece, le bloc porte le code en classe, la page porte `#documents`.
#: Un gabarit invente ne prouverait rien.
def _piece(libelle: str) -> str:
    return (
        "<tr class='just'>"
        "<td class='tdPdf'><a class='pj pdf' href='documents/ICONE'></a></td>"
        f"<td class='pl2'><a href='documents/{libelle}'>{libelle}</a></td>"
        "</tr>"
    )


def _bloc(code: str, contenu: str) -> str:
    return (
        f"<div class='{code} mt3'><table class='tableDoc'><tbody>"
        f"{contenu}</tbody></table></div>"
    )


def _page(blocs: str) -> str:
    return f"<html><body><div id='documents'>{blocs}</div></body></html>"


#: Dix-huit pieces dans la rubrique du reglement de copropriete: le cas reel de
#: Brice, qui sait qu'il en manque six sur vingt-quatre.
_REG = _page(_bloc("REG", "".join(_piece(f"Acte {i}") for i in range(18))))

SCENARIOS = {
    "un_manque_declare": {
        "html": _REG,
        "reglages": {
            "active": True,
            "rattachements": {"EXT-A-01": ["REG"]},
            "attendus": {"EXT-A-01": 24},
        },
    },
    "aucun_rattachement_declare": {
        "html": _REG,
        "reglages": {"active": True, "rattachements": {}, "attendus": {}},
    },
    "rien_a_annoncer": {
        "html": _REG,
        "reglages": {
            "active": True,
            "rattachements": {"EXT-A-01": ["REG"]},
            "attendus": {"EXT-A-01": 18},
            "sans_objet": [
                # Toutes les autres obligations sont declarees sans objet: il
                # ne reste donc rien a annoncer, et le bandeau doit se taire.
                o for o in (
                    "EXT-A-02", "EXT-A-03", "EXT-A-04", "EXT-A-05", "EXT-A-06",
                    "EXT-A-07", "EXT-A-08", "EXT-A-09",
                    "EXT-B-01", "EXT-B-02", "EXT-B-03", "EXT-B-04",
                    "EXT-C-01", "EXT-C-02", "EXT-C-03", "EXT-C-04", "EXT-C-05",
                )
            ],
        },
    },
    # --- le biffage de la liste des coproprietaires ---
    #
    # Le contenu est ici synthetique. Il reproduit la demonstration faite le
    # 2026-09-07 par un agent charge de me refuter: l'interdiction de relever
    # cette liste n'existait qu'en prose, et le lecteur conservait les libelles
    # en clair, plus douze passages d'historique, sans qu'aucun clic soit
    # necessaire.
    "liste_des_coproprietaires_rattachee": {
        "html": _page(_bloc("DIV", "".join(
            _piece(nom) for nom in (
                "MARTIN Jean - Lot 12 - 7 rue des Lilas - jean.martin@exemple.fr",
                "DUPONT Alice - Lot 3 - 9 rue des Lilas - alice.dupont@exemple.fr",
            )
        ))),
        "reglages": {"active": True, "rattachements": {"EXT-C-04": ["DIV"]}},
    },
    "liste_non_rattachee": {
        "html": _page(_bloc("DIV", _piece("MARTIN Jean - Lot 12"))),
        "reglages": {"active": True, "rattachements": {}},
    },
    # --- ce que la relecture de doctrine a mesure le 2026-09-07 ---
    "rattachement_saisi_en_minuscules": {
        "html": _page(_bloc("DIV", _piece("MARTIN Jean - Lot 12 - 7 rue des Lilas"))),
        "reglages": {"active": True, "rattachements": {"EXT-C-04": ["div"]}},
    },
    "un_manque_et_des_rubriques_non_regardees": {
        "html": _REG,
        "reglages": {
            "active": True,
            "rattachements": {
                "EXT-A-01": ["REG"], "EXT-A-08": ["ASS"],
                "EXT-A-05": ["CON"], "EXT-C-03": ["JUS"],
            },
            "attendus": {"EXT-A-01": 24},
        },
    },
    "une_fuite_anterieure_a_la_declaration_puis_effacement": {
        # Le cas que la relecture de doctrine a nomme: un passage ecrit AVANT
        # que l'utilisateur ne declare quelles rubriques ne se lisent pas garde
        # les noms en clair, et rien ne permettait de les reprendre.
        "html": _page(_bloc("DIV", _piece("MARTIN Jean - 7 rue des Lilas"))),
        "reglages": {"active": True, "rattachements": {}},
        "effacer": True,
    },
    "espace_non_reconnu": {
        "html": _REG,
        "chemin": "/portail/mes-documents",
        "reglages": {
            "active": True,
            "rattachements": {"EXT-A-01": ["REG"]},
            "attendus": {"EXT-A-01": 24},
        },
    },
    "espace_personnel": {
        "html": _REG,
        "chemin": "/espace-client/documents",
        "reglages": {
            "active": True,
            "rattachements": {"EXT-A-01": ["REG"]},
            "attendus": {"EXT-A-01": 24},
        },
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
        raise AssertionError(f"executer-bandeau.mjs a echoue:\n{rendu.stderr[:2000]}")
    return json.loads(rendu.stdout)


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class BandeauTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.r = _executer()

    def test_le_bandeau_est_reellement_pose(self) -> None:
        """Le test qui n'existait pas, et qui aurait du exister en premier.

        Tant que le mini-DOM ne fabriquait pas d'elements, cette assertion
        aurait echoue - et personne ne l'avait ecrite.
        """
        self.assertTrue(self.r["un_manque_declare"]["presence"])
        self.assertEqual(self.r["un_manque_declare"]["noeuds_ajoutes"], 1)

    def test_il_nomme_l_obligation_et_pas_seulement_le_code(self) -> None:
        """`REG: 18 vues` ne dit pas de quoi il manque. L'intitule le dit."""
        texte = self.r["un_manque_declare"]["texte"]
        self.assertIn("Reglement de copropriete", texte)
        self.assertIn("18", texte)
        self.assertIn("24", texte)

    def test_il_dit_le_type_d_espace_detecte(self) -> None:
        """Demande de Brice du 2026-09-06. Deux espaces distincts servent des
        choses differentes: un constat sans son espace est inutilisable."""
        self.assertIn("La copropriete", self.r["un_manque_declare"]["texte"])
        self.assertIn("Mon espace", self.r["espace_personnel"]["texte"])

    def test_il_porte_la_phrase_de_prudence(self) -> None:
        for nom in ("un_manque_declare", "aucun_rattachement_declare"):
            with self.subTest(scenario=nom):
                self.assertIn("apparence", self.r[nom]["texte"])

    def test_il_ne_dit_jamais_conforme_tout_court(self) -> None:
        """La mise en garde de Brice: attention au faux servi."""
        for nom, cas in self.r.items():
            with self.subTest(scenario=nom):
                for morceau in cas["texte"].split("."):
                    if "conforme" in morceau.lower():
                        self.assertIn("apparence", morceau.lower(), morceau)

    def test_sans_rattachement_il_explique_au_lieu_d_accuser(self) -> None:
        """Le premier passage chez un syndic inconnu. Un bandeau muet se lirait
        *tout va bien*; un bandeau qui annoncerait 18 manques mentirait."""
        texte = self.r["aucun_rattachement_declare"]["texte"]
        self.assertIn("18 obligations a rattacher", texte)
        self.assertNotIn("incomplete", texte)

    def test_il_se_tait_quand_il_n_a_rien_a_dire(self) -> None:
        """Un bandeau permanent qui repete *tout va bien* cesse d'etre lu en
        deux jours, et emporte avec lui les fois ou il avait raison."""
        self.assertFalse(self.r["rien_a_annoncer"]["presence"])
        self.assertEqual(self.r["rien_a_annoncer"]["noeuds_ajoutes"], 0)

    def test_il_vit_dans_une_ombre_fermee(self) -> None:
        """La page du syndic ne doit pouvoir ni lire ni styler ce que le plugin
        affiche par-dessus elle."""
        self.assertTrue(self.r["un_manque_declare"]["ombre"])


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class BiffageTests(unittest.TestCase):
    """La liste de tous les coproprietaires ne se releve jamais.

    `EXT-C-04` porte l'etat civil, le domicile et l'adresse electronique de
    chacun. Le referentiel l'ecrivait depuis le debut - *a constater comme
    presente ou absente; son contenu ne se capture jamais* - mais **rien ne
    l'appliquait**. Une verification adverse du 2026-09-07 a exécuté le chemin
    de capture et montre que les libelles etaient conserves en clair, plus
    douze passages d'historique, sans qu'aucun clic soit necessaire.

    Une interdiction que seul un humain peut lire n'est pas une garde.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.r = _executer()

    def test_aucun_nom_ne_survit_dans_le_stockage(self) -> None:
        stockage = self.r["liste_des_coproprietaires_rattachee"]["stockage"]
        for interdit in ("MARTIN", "DUPONT", "Alice", "rue des Lilas", "exemple.fr"):
            with self.subTest(fragment=interdit):
                self.assertNotIn(interdit, stockage)

    def test_le_compte_survit_lui(self) -> None:
        """C'est tout ce dont la conformite a besoin: la liste est due ou elle
        ne l'est pas. Sa completude se verifie ailleurs, apres
        pseudonymisation, sur des alias."""
        stockage = self.r["liste_des_coproprietaires_rattachee"]["stockage"]
        self.assertIn("(contenu non releve)", stockage)
        self.assertIn("contenu_biffe", stockage)

    def test_sans_rattachement_declare_la_garde_ne_s_applique_pas(self) -> None:
        """Assume, et dit a l'ecran: le plugin ne peut pas deviner ou son
        syndic range cette liste. Ce test existe pour que la limite soit
        visible plutot que decouverte."""
        stockage = self.r["liste_non_rattachee"]["stockage"]
        self.assertIn("MARTIN", stockage)


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class DoctrineTests(unittest.TestCase):
    """Ce qu'une relecture de doctrine a franchi, et qui est referme."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.r = _executer()

    def test_un_espace_inconnu_ne_se_deguise_pas_en_espace_collectif(self) -> None:
        """Le ternaire d'origine ne testait que `personnel`: un espace inconnu -
        le cas d'un second editeur - s'affichait *La copropriete*.

        C'est une reponse fausse en silence, dans un module dont la doctrine dit
        qu'un constat lu sans savoir ou il a ete pris est inutilisable.
        """
        texte = self.r["espace_non_reconnu"]["texte"]
        self.assertIn("Espace non reconnu", texte)
        self.assertNotIn("La copropriete", texte)

    def test_une_declaration_en_minuscules_arme_quand_meme_la_garde(self) -> None:
        """`div` au lieu de `DIV` desarmait le biffage en silence, et aucun
        ecran ne disait que le rattachement n'avait pris sur rien."""
        stockage = self.r["rattachement_saisi_en_minuscules"]["stockage"]
        self.assertNotIn("MARTIN", stockage)
        self.assertNotIn("rue des Lilas", stockage)
        self.assertIn("contenu_biffe", stockage)

    def test_une_fuite_anterieure_peut_enfin_etre_effacee(self) -> None:
        """Le plugin savait ecrire douze passages d'historique et n'avait
        AUCUNE commande pour les reprendre.

        C'etait la garantie que toute fuite passee restait permanente, y
        compris pour quelqu'un qui decouvrirait apres coup que la liste de ses
        coproprietaires y dormait.
        """
        cas = self.r["une_fuite_anterieure_a_la_declaration_puis_effacement"]
        # Le nom etait bien la avant: sans cela le test ne prouverait rien.
        self.assertIn("MARTIN", cas["stockage"])
        self.assertNotIn("MARTIN", cas["apres_effacement"])
        self.assertNotIn("rue des Lilas", cas["apres_effacement"])

    def test_l_effacement_garde_les_reponses_de_l_utilisateur(self) -> None:
        """Effacer les releves ne doit pas obliger a redeclarer dix-huit
        rattachements: personne ne le ferait deux fois."""
        cas = self.r["une_fuite_anterieure_a_la_declaration_puis_effacement"]
        self.assertIn("veille_reglages", cas["apres_effacement"])

    def test_un_bandeau_qui_annonce_un_manque_dit_ce_qu_il_n_a_pas_regarde(self) -> None:
        """Un compte de manques sans son perimetre se lit comme une couverture
        complete.

        La branche des non-parcourues ne s'executait jamais des qu'il existait
        un manque: le bandeau rouge annoncait un chiffre en taisant qu'il
        n'avait pas tout regarde. `veille.js` fait pourtant exactement l'effort
        inverse pour les changements.
        """
        texte = self.r["un_manque_et_des_rubriques_non_regardees"]["texte"]
        self.assertIn("incomplete", texte)
        self.assertIn("n'ont pas ete regardees", texte)
        self.assertIn("aucune absence", texte)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
