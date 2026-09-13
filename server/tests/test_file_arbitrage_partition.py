from __future__ import annotations

import unittest

from coproscope.modules.biffageops import complete_la_file, racine_de_forme


"""La file d'arbitrage se partitionne par diffusion, pas par ressemblance.

**Mesure du 2026-09-07**, `tools/mesure_file_arbitrage.py`, sur les deux corpus
du lot `corpus_caviarde_lot_20260904`:

- regrouper les formes par racine ne reduit la file que de 7 % (582 -> 543) et
  9 % (1 046 -> 952). La distribution est plate: il faut encore 336 et 665
  decisions pour couvrir 95 % des occurrences;
- la partition sur `nb_documents >= 2` la reduit de 66 % (543 -> 182) et 64 %
  (952 -> 346), soit environ un quart d'heure et une demi-heure d'arbitrage.

Le motif n'est pas arbitraire: une personne recurre de piece en piece, un
intitule comptable ponctuel non.

Donnees entierement fictives.
"""


class RacineDeForme(unittest.TestCase):
    def test_les_variantes_d_un_nom_partagent_leur_racine(self) -> None:
        racines = {
            racine_de_forme("MARCHAND Etienne"),
            racine_de_forme("Etienne MARCHAND"),
            racine_de_forme("MARCHAND E."),
        }
        self.assertEqual(
            len(racines),
            2,
            "Les deux formes completes se groupent; la forme abregee `MARCHAND E.` "
            "non, son token differe. La mesure dit que ce n'est pas le levier.",
        )
        self.assertEqual(racine_de_forme("MARCHAND Etienne"), racine_de_forme("Etienne MARCHAND"))
        self.assertEqual(racine_de_forme("MARCHAND Etienne"), "ETIENNE|MARCHAND")

    def test_le_patronyme_n_est_pas_devine_par_la_longueur(self) -> None:
        """Premiere version fausse: le token le plus long.

        Elle rendait `CLEMENCE` pour `VALLIOT Clemence` - un prenom plus long
        que son patronyme. Il n'existe pas de moyen fiable de designer le
        patronyme dans une chaine isolee; la cle renonce a le deviner.
        """

        self.assertEqual(racine_de_forme("VALLIOT Clemence"), "CLEMENCE|VALLIOT")

    def test_une_forme_vide_ne_casse_pas(self) -> None:
        self.assertEqual(racine_de_forme(""), "")
        self.assertEqual(racine_de_forme("   "), "")


class PartitionDeLaFile(unittest.TestCase):
    def _forme(self, doc_id: str, forme: str, occurrences: int = 1) -> dict[str, str]:
        return {
            "doc_id": doc_id,
            "genere_le": "2026-09-07",
            "forme": forme,
            "occurrences": str(occurrences),
            "motif": "suspect_non_caviarde",
            "racine_normalisee": racine_de_forme(forme),
            "nb_documents": "",
            "appariement_propose": "",
        }

    def test_nb_documents_compte_les_pieces_et_non_les_lignes(self) -> None:
        lignes = complete_la_file(
            [
                self._forme("DOC-A", "MARCHAND Etienne", 4),
                self._forme("DOC-B", "Etienne MARCHAND", 2),
                self._forme("DOC-A", "VALLIOT Clemence", 9),
            ],
            [],
        )
        par_racine = {row["racine_normalisee"]: row["nb_documents"] for row in lignes}
        self.assertEqual(par_racine["ETIENNE|MARCHAND"], "2")
        self.assertEqual(
            par_racine["CLEMENCE|VALLIOT"],
            "1",
            "Neuf occurrences dans une seule piece restent une seule piece: "
            "c'est le nombre de documents qui partitionne, pas le volume.",
        )

    def test_un_appariement_unique_est_propose(self) -> None:
        lignes = complete_la_file(
            [self._forme("DOC-A", "MARCHAND Etienne")],
            [{"nom_normalise": "MARCHAND", "alias": "PERSONNE_PLATANE_INDIGO"}],
        )
        self.assertEqual(lignes[0]["appariement_propose"], "PERSONNE_PLATANE_INDIGO")

    def test_deux_homonymes_ne_produisent_aucune_proposition(self) -> None:
        """Proposer l'un des deux serait trancher entre homonymes."""

        lignes = complete_la_file(
            [self._forme("DOC-A", "MARCHAND Etienne")],
            [
                {"nom_normalise": "MARCHAND", "alias": "PERSONNE_PLATANE_INDIGO"},
                {"nom_normalise": "MARCHAND", "alias": "PERSONNE_PLATANE_OCRE"},
            ],
        )
        self.assertEqual(lignes[0]["appariement_propose"], "")

    def test_une_racine_inconnue_de_l_annuaire_ne_propose_rien(self) -> None:
        lignes = complete_la_file([self._forme("DOC-A", "NOIRET Bastien")], [])
        self.assertEqual(lignes[0]["appariement_propose"], "")
        self.assertEqual(lignes[0]["nb_documents"], "1")

    def test_la_partition_isole_bien_le_premier_lot(self) -> None:
        """Ce que la mesure a montre: le premier lot est celui des recurrentes."""

        lignes = complete_la_file(
            [
                self._forme("DOC-A", "MARCHAND Etienne"),
                self._forme("DOC-B", "MARCHAND Etienne"),
                self._forme("DOC-A", "TOTAL CHARGES"),
                self._forme("DOC-A", "EAU ARROSAGE"),
            ],
            [],
        )
        premier_lot = [row for row in lignes if int(row["nb_documents"]) >= 2]
        second_lot = [row for row in lignes if int(row["nb_documents"]) < 2]
        self.assertEqual({row["racine_normalisee"] for row in premier_lot}, {"ETIENNE|MARCHAND"})
        self.assertEqual(len(second_lot), 2)
        self.assertTrue(
            second_lot,
            "Le second lot n'est jamais vide par construction: une fuite dans "
            "une seule piece reste une fuite, la partition n'exclut rien.",
        )


if __name__ == "__main__":
    unittest.main()
