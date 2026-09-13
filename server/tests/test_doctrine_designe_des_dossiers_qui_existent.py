# -*- coding: utf-8 -*-
"""Une consigne qui nomme un dossier absent coute plus cher qu'une consigne absente.

**Le motif s'est produit trois fois en deux jours, toujours de la meme facon.**

1. Le 2026-09-08, cinq references d'instance de `CLAUDE.md` designaient un
   dossier supprime. La consigne etait suivie: l'agent qui l'appliquait echouait,
   ou choisissait une autre instance **sans le dire** - ce qui reproduit
   exactement le defaut que la consigne existait pour empecher.
2. Le meme motif avait deja tue le lanceur approuve (`RM-2026-0125`): il mourait
   en silence.
3. Le 2026-09-09, **je l'ai reproduit moi-meme**: l'instance mere a ete renommee
   en `tilleul_pseudo_mere` et le nom `tilleul_source_dev` a survecu au dossier
   dans quatre documents, dont la doctrine - alors que le paragraphe juste
   au-dessus interdit de figer un nom d'instance.

**L'axe, et non les trois cas.** Ce qui varie: quelle instance, quel document,
comment le chemin est ecrit, si le dossier est dans le depot ou hors depot. Ce
qui reste invariant: **une consigne que l'agent doit SUIVRE designe un dossier
qui doit exister au moment ou il la suit.** Le garde ne connait aucune liste de
noms; il lit ce que la doctrine ecrit et va voir.

**Ce que ce garde ne peut PAS tenir, et il faut le dire.** Les instances privees
vivent hors du depot: **la CI n'a pas le droit de les lire**. Le controle des
chemins `instances/...` ne peut donc s'executer que sur le poste, et il
s'annonce comme saute quand la racine est absente - jamais comme reussi. Le
controle des chemins `examples/...`, lui, porte sur le depot et tourne partout.

**Une reference n'est verifiable que si elle est ecrite en chemin.** Un nom nu
entre accents graves obligerait a deviner sa forme, ce qui est precisement la
modalite qui casse au cas suivant. La doctrine ecrit donc `instances/<nom>`.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

#: `server/tests/x.py` -> `server` -> depot -> workspace, qui porte `instances/`.
DEPOT = Path(__file__).resolve().parents[2]
WORKSPACE = DEPOT.parent

#: Les documents que l'agent SUIT. Le journal et les notes datees racontent le
#: passe et ont le droit de nommer un dossier supprime; une consigne, non.
DOCTRINES = ("CLAUDE.md", "../CLAUDE.md")

#: Un chemin d'instance ou d'exemple. Un gabarit porte `<...>` et n'est pas une
#: reference: il decrit comment nommer, il ne designe rien.
_CHEMIN = re.compile(r"`((?:instances|examples)/[^`<>\s]+)`")


def _references(texte: str) -> set[str]:
    return {m.group(1).rstrip("/") for m in _CHEMIN.finditer(texte)}


def _doctrines_lisibles():
    for nom in DOCTRINES:
        chemin = (DEPOT / nom).resolve()
        if chemin.is_file():
            yield chemin


class LaDoctrineDesigneDesDossiersQuiExistent(unittest.TestCase):
    def test_au_moins_une_doctrine_est_lue(self) -> None:
        """Sans cela, un garde qui ne lit rien passerait pour vert."""
        lues = list(_doctrines_lisibles())
        self.assertTrue(lues, "aucun CLAUDE.md lisible depuis %s" % DEPOT)

    def test_les_exemples_du_depot_existent(self) -> None:
        """Ce controle porte sur le depot: il tourne partout, CI comprise."""
        manquants = []
        for chemin in _doctrines_lisibles():
            for ref in sorted(_references(chemin.read_text(encoding="utf-8"))):
                if not ref.startswith("examples/"):
                    continue
                if not (DEPOT / ref).exists():
                    manquants.append("%s designe `%s`, absent du depot" % (chemin.name, ref))
        self.assertEqual([], manquants, "\n".join(manquants))

    def test_les_instances_citees_existent_sur_le_poste(self) -> None:
        """Hors depot, donc **saute en CI** - et le motif du saut est nomme."""
        racine = WORKSPACE / "instances"
        if not racine.is_dir():
            raise unittest.SkipTest(
                "pas d'instances privees ici (%s): la CI n'a pas le droit de les lire, "
                "donc ce controle ne vaut que sur le poste" % racine
            )
        manquants = []
        for chemin in _doctrines_lisibles():
            for ref in sorted(_references(chemin.read_text(encoding="utf-8"))):
                if not ref.startswith("instances/"):
                    continue
                if not (WORKSPACE / ref).exists():
                    manquants.append(
                        "%s designe `%s`, qui n'existe pas sous %s. Renomme ou supprime ? "
                        "Corriger la consigne, ne pas choisir une autre instance en silence."
                        % (chemin.name, ref, WORKSPACE)
                    )
        self.assertEqual([], manquants, "\n".join(manquants))

    def test_un_gabarit_n_est_pas_une_reference(self) -> None:
        """`instances/lot_<sujet>_<date>` dit comment nommer, ne designe rien."""
        self.assertEqual(set(), _references("copier vers `instances/lot_<sujet>_<date>`"))
        self.assertEqual({"instances/tests_ux"}, _references("voir `instances/tests_ux` puis"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
