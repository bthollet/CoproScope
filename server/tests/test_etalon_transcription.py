"""L'etalon est LU, il n'est plus recopie a la main.

`docs/etalon_corpus_tests_ux.md` fige, avant tout traitement outil, ce qu'un
lecteur humain a lu dans les pieces. Sa regle de tenue est explicite: *« Un
chiffre etabli par l'outil n'entre jamais ici. Ce document precede l'outil. »*

Mais il denonce lui-meme la derive qui le menace: *« une affirmation chiffree
qui circule de note en note sans etre reverifiee sur la piece source finit par
etre traitee comme un fait »*. Or c'est exactement ce qui lui arrive: mesure du
2026-09-07, AUCUN test ne lisait ce fichier. Ses chiffres etaient transcrits en
dur dans `test_actes_etalon.py`, `test_montants.py` et `test_decompte_voix.py`.
Si le markdown changeait, rien ne cassait; si une transcription derivait, rien
ne le disait non plus.

Ce fichier ferme la boucle. Il ne verifie pas que l'outil trouve les bons
chiffres - c'est le travail d'un autre lot, que l'etalon confie explicitement a
« quelqu'un qui n'a pas etabli l'etalon ». Il verifie que **les chiffres qui
circulent dans les tests sont encore ceux de l'etalon**.

C'est une garde de PORTEE au sens de `RM-2026-0106`: elle mesure le lien entre
la source de verite et ses copies, pas un comportement du produit.
"""

from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
ETALON = DEPOT / "docs" / "etalon_corpus_tests_ux.md"

#: La table `Nº | Majorite (article) | Issue | Objet` du proces-verbal etalon.
#:
#: L'issue est prise comme CELLULE ENTIERE, pas comme un mot. Premiere version
#: de cette garde: `[A-Z_]+`, qui lisait `ADOPTEE` et `REJETEE` et ratait neuf
#: lignes sur cinquante-cinq - `PAS DE VOTE`, `ISSUE NON ENONCEE`. J'avais code
#: les modalites que j'avais vues au lieu de nommer l'axe, dans l'instrument
#: meme qui cherche ce defaut. L'axe est: l'issue est ce que la troisieme
#: colonne dit, quelle que soit sa forme.
LIGNE_RESOLUTION = re.compile(r"^\|\s*(\d+)\s*\|([^|]*)\|([^|]*)\|")


#: Le titre qui ouvre la table. L'ancrer evite de ramasser la table des pieges,
#: dont les lignes commencent aussi par un numero: sans cette borne la garde
#: lisait 60 lignes et melangeait deux sujets.
ANCRE_TABLE = "Detail resolution par resolution"


def _resolutions_de_l_etalon() -> list[tuple[int, str, str]]:
    lignes: list[tuple[int, str, str]] = []
    dans_la_table = False
    for ligne in ETALON.read_text(encoding="utf-8").splitlines():
        if ANCRE_TABLE in ligne:
            dans_la_table = True
            continue
        if not dans_la_table:
            continue
        trouve = LIGNE_RESOLUTION.match(ligne)
        if trouve:
            lignes.append((int(trouve.group(1)), trouve.group(2).strip(), trouve.group(3).strip()))
        elif lignes and not ligne.startswith("|"):
            break  # la table est finie
    return lignes


@unittest.skipUnless(ETALON.exists(), "etalon absent de cet arbre")
class L_etalon_est_lisible_par_machine(unittest.TestCase):
    """Sans cela, aucune garde ne peut s'y adosser: c'est le prealable."""

    def test_la_table_du_proces_verbal_porte_ses_cinquante_cinq_resolutions(self) -> None:
        resolutions = _resolutions_de_l_etalon()
        self.assertEqual(
            len(resolutions),
            55,
            "La table du PV du 03/07/2024 ne rend plus 55 lignes. Soit l'etalon a ete "
            "corrige - alors mettez a jour les tests qui le recopient - soit sa mise en "
            "forme a change et cette garde ne sait plus le lire.",
        )

    def test_les_numeros_vont_de_un_a_cinquante_cinq_sans_trou_ni_doublon(self) -> None:
        numeros = [numero for numero, _, _ in _resolutions_de_l_etalon()]
        self.assertEqual(numeros, list(range(1, 56)))


@unittest.skipUnless(ETALON.exists(), "etalon absent de cet arbre")
class LesChiffresQuiCirculentSontEncoreCeuxDeLEtalon(unittest.TestCase):
    """Le coeur du fichier: la source de verite contre ses propres copies."""

    def test_la_distribution_des_issues_recopiee_dans_les_tests_correspond_a_l_etalon(self) -> None:
        lues = Counter(issue for _, _, issue in _resolutions_de_l_etalon())

        transcription = DEPOT / "server" / "tests" / "test_actes_etalon.py"
        if not transcription.exists():
            self.skipTest("test_actes_etalon.py absent de cet arbre")
        source = transcription.read_text(encoding="utf-8")

        compares = 0
        for issue, attendu in lues.items():
            # L'etalon ecrit `PAS DE VOTE`, le code `PAS_DE_VOTE`: l'espace et le
            # tiret bas sont une modalite d'ecriture, pas une difference d'issue.
            forme = issue.replace(" ", "[ _]")
            motif = re.compile(r'"%s"\s*:\s*(\d+)|\("%s",\s*(\d+)\)' % (forme, forme))
            trouves = {int(a or b) for a, b in motif.findall(source)}
            if not trouves:
                continue
            compares += 1
            self.assertIn(
                attendu,
                trouves,
                msg=(
                    f"`{issue}`: l'etalon compte {attendu}, la transcription de "
                    f"test_actes_etalon.py dit {sorted(trouves)}. Une des deux a derive, "
                    "et jusqu'a present rien ne le disait."
                ),
            )

        self.assertGreaterEqual(
            compares,
            3,
            msg=(
                "Cette garde n'a compare que %d issue(s) sur %d. Un renommage dans la "
                "transcription l'a rendue muette: elle passerait au vert en ne mesurant "
                "rien, ce qui est exactement le defaut qu'elle existe pour empecher."
                % (compares, len(lues))
            ),
        )

    def test_le_total_des_charges_recopie_ailleurs_correspond_a_l_etalon(self) -> None:
        """Le total 2025 circule dans `test_montants.py` sous forme de chaine formatee."""
        texte = ETALON.read_text(encoding="utf-8")
        totaux = set(re.findall(r"\b357[   ]?493[,.]10\b", texte))
        if not totaux:
            self.skipTest("le total de reference n'est plus present dans l'etalon sous cette forme")

        montants = DEPOT / "server" / "tests" / "test_montants.py"
        if not montants.exists():
            self.skipTest("test_montants.py absent de cet arbre")
        recopie = re.search(r'ETALON_CHARGES\s*=\s*"([^"]+)"', montants.read_text(encoding="utf-8"))
        self.assertIsNotNone(recopie, "ETALON_CHARGES a disparu de test_montants.py")

        normalise = lambda valeur: re.sub(r"[^\d,]", "", valeur)  # noqa: E731 - lisible ici
        self.assertIn(
            normalise(recopie.group(1)),
            {normalise(total) for total in totaux},
            msg=(
                "Le total des charges recopie dans test_montants.py ne correspond plus a "
                "l'etalon. C'est precisement la derive que l'etalon denonce: une "
                "affirmation chiffree qui circule de note en note sans etre reverifiee."
            ),
        )


if __name__ == "__main__":
    unittest.main()
