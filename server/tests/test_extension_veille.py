"""Ce que la veille du plugin compte comme changement, et ce qu'elle refuse.

Ce fichier existe a cause d'une question de Brice, le 2026-09-06: *qu'est-ce
qu'un changement pour lui ?*. Y repondre precisement a fait apparaitre un defaut
que personne n'aurait vu avant qu'il ne produise une fausse alerte.

La comparaison ignorait si une rubrique avait ete parcourue **aux deux dates**.
Une rubrique qui n'aurait pas charge une seule fois aurait fait disparaitre
toutes ses pieces d'un coup - une bouffee de constats faux, et sur ce que
l'outil sait produire de plus accusatoire.

C'est la regle de couverture, la meme que celle du journal de CoproScope,
appliquee ici au niveau pauvre de l'extension: **on ne compare que ce qui a ete
regarde des deux cotes**.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2] / "clients" / "extension-navigateur"
EXECUTEUR = RACINE / "tests" / "executer-veille.mjs"
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"


def _piece(groupe: str, libelle: str) -> dict:
    return {"groupe": groupe, "libelle": libelle, "nom_serveur": ""}


def _releve(rubriques: list[dict]) -> dict:
    return {"espace": "/espace-copropriete/documents", "rubriques": rubriques}


def _rub(code: str, pieces: list[dict], presente: bool = True) -> dict:
    return {"rubrique_code": code, "presente": presente, "pieces": pieces}


A_DEUX = [
    _rub("ARR", [_piece("2025", "Annexe 1"), _piece("2025", "Annexe 2")]),
    _rub("CON", [_piece("", "Mandat")]),
]

SCENARIOS = {
    "une_piece_en_moins": {
        "avant": _releve(A_DEUX),
        "apres": _releve(
            [_rub("ARR", [_piece("2025", "Annexe 1")]), _rub("CON", [_piece("", "Mandat")])]
        ),
    },
    "une_piece_en_plus": {
        "avant": _releve(A_DEUX),
        "apres": _releve(
            [
                _rub(
                    "ARR",
                    [_piece("2025", "Annexe 1"), _piece("2025", "Annexe 2"),
                     _piece("2025", "Annexe 3")],
                ),
                _rub("CON", [_piece("", "Mandat")]),
            ]
        ),
    },
    "un_renommage": {
        "avant": _releve(A_DEUX),
        "apres": _releve(
            [
                _rub("ARR", [_piece("2025", "Annexe 1"), _piece("2025", "Annexe deux")]),
                _rub("CON", [_piece("", "Mandat")]),
            ]
        ),
    },
    "une_rubrique_non_parcourue_au_second_passage": {
        "avant": _releve(A_DEUX),
        "apres": _releve(
            [_rub("ARR", [], presente=False), _rub("CON", [_piece("", "Mandat")])]
        ),
    },
    "un_deplacement_entre_groupes": {
        "avant": _releve(A_DEUX),
        "apres": _releve(
            [
                _rub("ARR", [_piece("2025", "Annexe 1"), _piece("2024", "Annexe 2")]),
                _rub("CON", [_piece("", "Mandat")]),
            ]
        ),
    },
}


def _n(code: str, combien: int, presente: bool = True) -> dict:
    return _rub(code, [_piece("", f"P{i}") for i in range(combien)], presente)


#: Les manques declares. Le premier scenario est le cas reel donne par Brice le
#: 2026-09-06: il sait que son reglement de copropriete compte 24 pieces, et il
#: en manque 6.
SCENARIOS["manques_reglement_de_copropriete"] = {
    "releve": _releve([_n("REG", 18), _n("CON", 12), _n("ARR", 40)]),
    "attendus": {"REG": 24},
}
SCENARIOS["manques_compte_atteint"] = {
    "releve": _releve([_n("REG", 24)]),
    "attendus": {"REG": 24},
}
SCENARIOS["manques_aucun_attendu_declare"] = {
    "releve": _releve([_n("REG", 18)]),
    "attendus": {},
}
SCENARIOS["manques_rubrique_non_parcourue"] = {
    "releve": _releve([_n("REG", 0, presente=False)]),
    "attendus": {"REG": 24},
}
SCENARIOS["manques_zero_attendu_est_un_renseignement"] = {
    "releve": _releve([_n("JUS", 0)]),
    "attendus": {"JUS": 0},
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
        raise AssertionError(f"executer-veille.mjs a echoue:\n{rendu.stderr[:2000]}")
    return json.loads(rendu.stdout)


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class VeilleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.r = _executer()

    def test_une_piece_qui_disparait_compte_pour_un(self) -> None:
        self.assertEqual(self.r["une_piece_en_moins"]["disparus"], 1)
        self.assertEqual(self.r["une_piece_en_moins"]["parus"], 0)

    def test_une_piece_qui_apparait_compte_pour_un(self) -> None:
        self.assertEqual(self.r["une_piece_en_plus"]["parus"], 1)
        self.assertEqual(self.r["une_piece_en_plus"]["disparus"], 0)

    def test_un_renommage_compte_pour_deux(self) -> None:
        """Un seul fait, deux changements - et c'est assume.

        L'extension ne sait pas qu'il s'agit de la meme piece: le dire exige de
        comparer les noms servis par le serveur, ce que fait CoproScope. Compter
        deux vaut mieux que rapprocher a tort deux pieces distinctes.
        """
        self.assertEqual(self.r["un_renommage"]["parus"], 1)
        self.assertEqual(self.r["un_renommage"]["disparus"], 1)

    def test_un_deplacement_entre_groupes_compte_pour_deux(self) -> None:
        self.assertEqual(self.r["un_deplacement_entre_groupes"]["parus"], 1)
        self.assertEqual(self.r["un_deplacement_entre_groupes"]["disparus"], 1)

    def test_une_rubrique_non_parcourue_ne_fait_disparaitre_personne(self) -> None:
        """Le defaut trouve le 2026-09-06, et la raison d'etre de ce fichier.

        Sans cette garde, une rubrique qui n'aurait pas charge une fois aurait
        rendu ici deux disparus - et sur l'index reel, jusqu'a quarante d'un
        coup pour la seule rubrique des arretes de comptes.
        """
        resultat = self.r["une_rubrique_non_parcourue_au_second_passage"]
        self.assertEqual(resultat["disparus"], 0)
        self.assertEqual(resultat["parus"], 0)

    def test_ce_qui_n_a_pas_ete_compare_est_nomme(self) -> None:
        """Un compte de changements sans son perimetre se lit comme une
        couverture complete."""
        resultat = self.r["une_rubrique_non_parcourue_au_second_passage"]
        self.assertEqual(resultat["hors_comparaison"], ["ARR"])

    def test_une_comparaison_complete_ne_laisse_rien_de_cote(self) -> None:
        for nom in ("une_piece_en_moins", "une_piece_en_plus", "un_renommage"):
            with self.subTest(scenario=nom):
                self.assertEqual(self.r[nom]["hors_comparaison"], [])


class ManquesTests(unittest.TestCase):
    """Ce que l'humain sait devoir exister, confronte a ce qui est servi.

    Demande de Brice le 2026-09-06. Aucune observation ne peut produire ce
    renseignement: seul quelqu'un qui connait le dossier sait combien de pieces
    compte un reglement de copropriete. L'attendu declare transforme donc un
    *je ne sais pas* en ecart chiffre.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.r = _executer()

    def _etat(self, scenario: str, code: str) -> dict:
        return next(
            m for m in self.r[scenario]["manques"] if m["code"] == code
        )

    def test_le_cas_reel_du_reglement_de_copropriete(self) -> None:
        """18 pieces vues, 24 attendues, 6 manquantes."""
        etat = self._etat("manques_reglement_de_copropriete", "REG")
        self.assertEqual(etat["etat"], "MANQUE")
        self.assertEqual(etat["observe"], 18)
        self.assertEqual(etat["attendu"], 24)
        self.assertEqual(etat["ecart"], 6)

    def test_une_rubrique_sans_attendu_reste_inconnue(self) -> None:
        """L'outil ne devine pas un attendu, et surtout ne le deduit pas d'un
        passage precedent: une valeur deduite de l'observation ne pourrait, par
        construction, jamais reveler un manque."""
        etat = self._etat("manques_aucun_attendu_declare", "REG")
        self.assertEqual(etat["etat"], "INCONNU")
        self.assertNotIn("attendu", etat)

    def test_les_autres_rubriques_ne_sont_pas_declarees_manquantes(self) -> None:
        etats = {m["code"]: m["etat"] for m in self.r["manques_reglement_de_copropriete"]["manques"]}
        self.assertEqual(etats["CON"], "INCONNU")
        self.assertEqual(etats["ARR"], "INCONNU")

    def test_le_compte_atteint_ne_dit_pas_conforme(self) -> None:
        """La mise en garde de Brice: attention au faux servi.

        L'etat s'appelle COMPLET et non CONFORME. Une rubrique peut porter le
        bon nombre de pieces sans que ce soient les bonnes - une attestation
        perimee, un projet au lieu d'un contrat signe. Trancher exige de lire
        les pieces.
        """
        etat = self._etat("manques_compte_atteint", "REG")
        self.assertEqual(etat["etat"], "COMPLET")
        self.assertNotIn("CONFORME", str(self.r["manques_compte_atteint"]))

    def test_une_rubrique_non_parcourue_ne_produit_aucun_manque(self) -> None:
        """Sinon un chargement rate se lirait comme 24 pieces disparues."""
        etat = self._etat("manques_rubrique_non_parcourue", "REG")
        self.assertEqual(etat["etat"], "NON_PARCOURUE")
        self.assertNotIn("ecart", etat)

    def test_zero_attendu_est_un_renseignement_et_non_une_absence(self) -> None:
        """Zero veut dire *aucune piece attendue ici*. C'est different de
        *je ne sais pas*, et le champ vide sert a le dire."""
        etat = self._etat("manques_zero_attendu_est_un_renseignement", "JUS")
        self.assertEqual(etat["etat"], "COMPLET")
        self.assertEqual(etat["attendu"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
