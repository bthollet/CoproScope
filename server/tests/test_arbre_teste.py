"""Le code teste est-il celui de CET arbre de travail ?

**Le piege.** `server/.venv` porte un install editable dont le `.pth` code en
dur un chemin absolu vers `server/src` de l'arbre PRINCIPAL. Un agent qui
travaille dans un worktree et lance `python -m unittest` depuis son propre
`server/` obtient donc une suite verte qui a teste le code de l'arbre
principal, pas le sien. Ses modifications ne sont ni executees ni couvertes, et
rien ne le dit.

Constate le 2026-09-05 par un agent de la campagne de finition, dans ses
propres mots: « mes premiers passages verts etaient donc faux ». Le defaut ne
casse aucun test - il en fait passer.

**Ce que ce module verifie.** Que le paquet `coproscope` importe vient bien de
l'arbre ou vivent ces tests. La correction, quand ce test echoue, tient en une
variable:

    cd <ton arbre>/server
    PYTHONPATH=src .venv/Scripts/python.exe -m unittest discover -s tests

**Depuis la purge du 2026-09-05, le venv n'installe plus le paquet du tout.**
Le piege n'est donc plus seulement detecte, il est impossible: sans chemin
explicite rien ne s'importe, et avec un chemin explicite c'est forcement l'arbre
courant.

Ce test reste, pour deux raisons. Il donne un message qui prescrit la correction
plutot qu'un `ModuleNotFoundError` nu. Et il rattraperait une reinstallation
editable faite par megarde - ce qui est exactement la facon dont le defaut est
apparu la premiere fois.
"""

from __future__ import annotations

import pathlib
import unittest

import coproscope


class LeCodeTesteEstCeluiDeCetArbreTests(unittest.TestCase):
    def test_le_paquet_importe_vient_de_l_arbre_qui_porte_ces_tests(self) -> None:
        # tests/ -> server/ -> <arbre>
        arbre = pathlib.Path(__file__).resolve().parent.parent.parent
        attendu = (arbre / "server" / "src" / "coproscope").resolve()
        importe = pathlib.Path(coproscope.__file__).resolve().parent

        self.assertEqual(
            importe,
            attendu,
            "\n\n"
            "  La suite teste le code d'un AUTRE arbre de travail.\n\n"
            f"    ces tests vivent dans : {arbre}\n"
            f"    le code importe vient de : {importe.parent.parent.parent}\n\n"
            "  Cause: server/.venv porte un install editable dont le .pth code\n"
            "  en dur un chemin absolu. Il ne peut pointer que sur un arbre.\n\n"
            "  Correction, depuis ton propre server/ :\n"
            "    PYTHONPATH=src .venv/Scripts/python.exe -m unittest discover -s tests\n\n"
            "  Tant que ce test echoue, aucun resultat vert de cette suite ne\n"
            "  dit quoi que ce soit de tes modifications.\n",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
