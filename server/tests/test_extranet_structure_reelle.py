"""L'adaptateur confronte a la structure d'un extranet reellement en service.

======================================================================
Ce que ce fichier contient, et ce qu'il ne contient pas
======================================================================

Il contient **la structure** d'un index d'extranet observe le 2026-09-04:
combien de rubriques, combien de groupes, combien de pieces par rubrique, et
surtout **quels libelles se repetent ou non**.

Il ne contient **aucune donnee reelle**. Les libelles ont ete remplaces dans le
navigateur, avant tout transfert, par des pseudonymes stables `L1..L83`, et les
en-tetes de groupe par `G1..G5`. Le remplacement est fait **par valeur**: deux
libelles identiques dans la page rendent le meme pseudonyme, et deux libelles
differents rendent des pseudonymes differents. Le motif de collisions est donc
integralement preserve alors qu'aucun mot de la copropriete n'est ici.

C'est le meilleur des deux: une epreuve contre la realite, sans la realite.

======================================================================
Pourquoi cette epreuve compte plus que les tests synthetiques
======================================================================

Les autres tests du lot verifient que l'adaptateur fait ce que j'ai voulu qu'il
fasse. Celui-ci verifie qu'il fait ce qu'il faut **sur une page que je n'ai pas
ecrite**. Les gabarits synthetiques sont ecrits par la meme personne que le
code: ils partagent ses angles morts.

Trois grandeurs mesurees le 2026-09-04 sur l'index reel doivent se retrouver
ici, et elles sont reproduites exactement:

- **115 pieces** pour 230 liens, soit deux liens par piece;
- **83 libelles distincts**, donc **32 collisions** si l'on prend le libelle
  pour cle - 28 % de l'index, en silence;
- **zero collision** avec la cle a trois composantes.
"""

from __future__ import annotations

import unittest

from coproscope.modules._extranet_adaptateur import PROFIL_COPRODIRECTE, lire_index
from coproscope.modules._extranet_journal import collisions
from coproscope.modules._extranet_schema import RUBRIQUE_PARCOURUE

#: La structure relevee, pseudonymisee dans le navigateur avant tout transfert.
#: `#Gn` marque un en-tete de groupe, `Ln` une piece.
#:
#: Noter `ARR`: cinq groupes portant **les memes huit libelles**. C'est le
#: piege, et il est reel - ce sont les cinq annexes comptables, la liste de
#: l'annexe 1, l'etat des depenses et l'etat detaille, pour cinq exercices.
PLAN: dict[str, list[str]] = {
    "ARR": (
        ["#G1"] + [f"L{i}" for i in range(1, 9)]
        + ["#G2"] + [f"L{i}" for i in range(1, 9)]
        + ["#G3"] + [f"L{i}" for i in range(1, 9)]
        + ["#G4"] + [f"L{i}" for i in range(1, 9)]
        + ["#G5"] + [f"L{i}" for i in range(1, 9)]
    ),
    "ASS": [f"L{i}" for i in range(9, 35)],
    "CON": [f"L{i}" for i in range(35, 47)],
    "DIV": [f"L{i}" for i in range(47, 55)],
    "JUS": [f"L{i}" for i in range(55, 57)],
    "REU": [f"L{i}" for i in range(57, 60)],
    "REG": [f"L{i}" for i in range(60, 78)],
    "DIA": [f"L{i}" for i in range(78, 84)],
}


def _html(plan: dict[str, list[str]]) -> str:
    """Reconstruit un index a la forme de l'editeur observe.

    Deux liens par piece - l'icone sans texte et le libelle - parce que c'est
    ce que sert l'editeur, et que le nombre de pieces en depend.
    """
    blocs = []
    for code, sequence in plan.items():
        lignes = []
        for entree in sequence:
            if entree.startswith("#"):
                lignes.append(f"<tr><td colspan='2'>{entree[1:]}</td></tr>")
            else:
                lignes.append(
                    "<tr class='just'>"
                    "<td class='tdPdf'><a class='pj pdf' href='documents/T'></a></td>"
                    f"<td class='pl2'><a href='documents/T'>{entree}</a></td>"
                    "</tr>"
                )
        blocs.append(
            f"<div class='{code} mt3'><table class='tableDoc'><tbody>"
            + "".join(lignes)
            + "</tbody></table></div>"
        )
    return "<html><body><div id='documents'>" + "".join(blocs) + "</div></body></html>"


class StructureReelleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lu = lire_index(_html(PLAN), PROFIL_COPRODIRECTE, "P-REEL")

    def test_le_compte_de_pieces_est_celui_mesure(self) -> None:
        """115 pieces pour 230 liens: deux liens par piece, fusionnes."""
        self.assertEqual(len(self.lu["pieces"]), 115)

    def test_les_huit_rubriques_sont_parcourues(self) -> None:
        etats = [r["etat"] for r in self.lu["rubriques"]]
        self.assertEqual(etats.count(RUBRIQUE_PARCOURUE), 8)

    def test_la_repartition_par_rubrique_est_celle_mesuree(self) -> None:
        attendu = {"ARR": 40, "ASS": 26, "REG": 18, "CON": 12,
                   "DIV": 8, "DIA": 6, "REU": 3, "JUS": 2}
        obtenu = {
            r["rubrique_code"]: int(r["nb_pieces"])
            for r in self.lu["rubriques"]
            if int(r["nb_pieces"])
        }
        self.assertEqual(obtenu, attendu)

    def test_le_libelle_seul_perdrait_trente_deux_pieces(self) -> None:
        """La mesure qui justifie toute la conception de la cle.

        83 libelles distincts pour 115 pieces. Une cle fondee sur le libelle
        fusionnerait 32 pieces - 28 % de l'index - **sans erreur visible**, et
        ferait donc disparaitre des retraits reels.
        """
        libelles = [p["libelle"] for p in self.lu["pieces"]]
        self.assertEqual(len(libelles), 115)
        self.assertEqual(len(set(libelles)), 83)
        self.assertEqual(len(libelles) - len(set(libelles)), 32)

    def test_la_cle_a_trois_composantes_est_injective_sur_l_index_entier(self) -> None:
        """Le resultat principal du lot, verifie ici sur la structure reelle."""
        emplacements = [p["emplacement"] for p in self.lu["pieces"]]
        self.assertEqual(len(set(emplacements)), 115)
        self.assertEqual(collisions(self.lu["pieces"]), {})

    def test_seule_la_rubrique_des_comptes_emploie_des_groupes(self) -> None:
        """La composante groupe est facultative, et le reste doit le supporter."""
        avec = {p["rubrique_code"] for p in self.lu["pieces"] if p["groupe"]}
        self.assertEqual(avec, {"ARR"})

    def test_les_cinq_exercices_sont_distingues(self) -> None:
        groupes = {p["groupe"] for p in self.lu["pieces"] if p["rubrique_code"] == "ARR"}
        self.assertEqual(len(groupes), 5)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
