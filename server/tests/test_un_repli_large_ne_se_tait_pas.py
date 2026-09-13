# -*- coding: utf-8 -*-
"""Chaque repli est correct isolement; leur somme est un silence.

`RM-2026-0086`, axe **(B)**: *un `except Exception` nu degrade en silence*.
L'item le range dans la meme famille que `RM-2026-0106` et que les quatre
degradations propres de `RM-2026-0110`, et il en donne la formule: **chaque
repli est correct isolement, leur somme est un silence.**

**LE CAS PHARE DE L'AXE EST DEJA CORRIGE, verifie le 2026-09-12.**
`actes_autorisation` rendait une liste vide **quelle que soit la cause** -
table absente, base abimee, fichier verrouille, colonne disparue, erreur de
disque - et l'ecran affichait *aucune autorisation identifiee*, une phrase qui
affirme quelque chose **sur la copropriete**, la ou la verite etait *la
question n'a pas pu etre posee*. Le repli nu a ete retire le 2026-09-10
(constat `C085`), et avec une finesse qui vaut d'etre notee: SQLite dit
`no such table` pour une VUE manquante comme pour une table, donc le nom
manquant est confronte a `NOMS_VUES` - sans quoi le correctif aurait reproduit
le defaut qu'il corrigeait.

**CE QUE CETTE GARDE AJOUTE: la frontiere sur la FAMILLE.** Mesure du
2026-09-12 sur tout `server/src`, par lecture d'arbre syntaxique et non au
motif: **72 replis larges** - `except`, `except Exception`, `except
BaseException` - dont **58 MUETS**, c'est-a-dire dont le corps ne journalise
rien, ne releve rien et ne nomme la cause d'aucune facon.

**L'AXE.** Ce qui VARIE: la raison pour laquelle une lecture echoue - un
disque, un verrou, un schema, un encodage. Ce qui reste INVARIANT: **repondre
et ne pas pouvoir repondre ne sont pas le meme etat**, et un seul des deux se
resume par une valeur vide. **Hors des valeurs observees:** un repli ecrit
demain, dans un module qui n'existe pas encore, est compte le jour de sa
creation - la garde lit l'arbre syntaxique de tout `src`, sans liste de
fichiers.

**CE QUE LA GARDE NE FAIT PAS.** Elle ne corrige pas les 58: chacun demande de
savoir ce que son appelant fait d'une valeur vide, et certains sont
legitimes - un repli qui protege une mesure accessoire n'a rien a dire. Elle
**borne** le compte, pour que la somme cesse de grandir, et c'est exactement
ce que l'item reclame.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "src"

#: Ce qui, dans le corps d'un repli, dit quelque chose de la cause.
PAROLES = ("log", "raise", "print", "journal", "warn", "constat", "anomalie")

#: Etat mesure le 2026-09-12. **Dette bornee et datee, pas une tolerance.**
#: Le second compte est celui qui importe: un repli large qui PARLE n'est pas
#: un silence.
#: Remesure le 2026-09-13: 72 -> 71 et 58 -> 57. **Aucun repli n'a ete
#: restreint**: celui qui manque vivait dans une vue SUPPRIMEE par la recette de
#: Brice (`RM-2026-0183`).
REPLIS_LARGES = 71
REPLIS_MUETS = 57


def _replis() -> tuple[int, int]:
    larges = muets = 0
    for chemin in sorted(RACINE.rglob("*.py")):
        if "__pycache__" in chemin.parts:
            continue
        try:
            arbre = ast.parse(chemin.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:  # pragma: no cover - une source cassee se voit ailleurs
            continue
        for noeud in ast.walk(arbre):
            if not isinstance(noeud, ast.ExceptHandler):
                continue
            cible = noeud.type
            if cible is not None and not (
                isinstance(cible, ast.Name)
                and cible.id in ("Exception", "BaseException")
            ):
                continue
            larges += 1
            corps = ast.dump(ast.Module(body=noeud.body, type_ignores=[])).lower()
            if not any(mot in corps for mot in PAROLES):
                muets += 1
    return larges, muets


class UN_REPLI_LARGE_QUI_SE_TAIT_NE_SE_MULTIPLIE_PAS(unittest.TestCase):
    def test_l_instrument_lit_bien_les_sources(self) -> None:
        """Sans lecture, les comptes seraient nuls et le test vert."""
        larges, _ = _replis()
        self.assertGreater(
            larges, 20,
            "presque aucun repli large trouve: la lecture d'arbre est cassee, "
            "et l'absence de nouveau silence ne prouverait rien")

    def test_le_compte_des_replis_larges_ne_grandit_pas(self) -> None:
        larges, _ = _replis()
        self.assertLessEqual(
            larges, REPLIS_LARGES,
            "un repli large de plus (%d pour une borne de %d). Chacun est "
            "correct isolement; leur somme est un silence - c'est la formule "
            "de l'axe (B) de `RM-2026-0086`." % (larges, REPLIS_LARGES))

    def test_le_compte_des_replis_MUETS_ne_grandit_pas(self) -> None:
        """Le compte qui importe: un repli qui parle n'est pas un silence."""
        _, muets = _replis()
        self.assertLessEqual(
            muets, REPLIS_MUETS,
            "un repli large et MUET de plus (%d pour une borne de %d): son "
            "corps ne journalise rien et ne nomme la cause d'aucune facon, "
            "donc `ne pas pouvoir repondre` sortira comme `repondre vide`. "
            "Nommer la cause, ou restreindre l'exception attrapee."
            % (muets, REPLIS_MUETS))

    def test_RESIDU_les_deux_comptes_se_redisent_quand_ils_BAISSENT(self) -> None:
        """Une borne laissee haute laisse la frontiere reculer en silence."""
        self.assertEqual(
            (REPLIS_LARGES, REPLIS_MUETS), _replis(),
            "les comptes ont baisse, et c'est une bonne nouvelle: mettre ces "
            "bornes a jour, avec la date, et dire au gouvernail quel repli a "
            "ete restreint ou a trouve sa parole.")


class LE_CRITERE_DISCRIMINE(unittest.TestCase):
    """Temoins: sans eux, la mesure ne voudrait rien dire."""

    def test_un_repli_qui_releve_n_est_pas_muet(self) -> None:
        arbre = ast.parse(
            "try:\n    pass\nexcept Exception as exc:\n    raise ValueError from exc\n")
        handler = [n for n in ast.walk(arbre) if isinstance(n, ast.ExceptHandler)][0]
        corps = ast.dump(ast.Module(body=handler.body, type_ignores=[])).lower()
        self.assertTrue(any(mot in corps for mot in PAROLES))

    def test_un_repli_qui_rend_None_est_muet(self) -> None:
        arbre = ast.parse("try:\n    pass\nexcept Exception:\n    x = None\n")
        handler = [n for n in ast.walk(arbre) if isinstance(n, ast.ExceptHandler)][0]
        corps = ast.dump(ast.Module(body=handler.body, type_ignores=[])).lower()
        self.assertFalse(any(mot in corps for mot in PAROLES))

    def test_un_repli_ETROIT_n_est_pas_compte(self) -> None:
        """Restreindre l'exception attrapee est precisement la reparation:

        elle ne doit pas rester comptee comme un defaut.
        """
        arbre = ast.parse("try:\n    pass\nexcept OSError:\n    x = None\n")
        handler = [n for n in ast.walk(arbre) if isinstance(n, ast.ExceptHandler)][0]
        cible = handler.type
        self.assertFalse(
            isinstance(cible, ast.Name)
            and cible.id in ("Exception", "BaseException"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
