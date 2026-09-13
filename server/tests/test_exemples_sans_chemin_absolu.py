# -*- coding: utf-8 -*-
"""L'instance partageable ne porte aucun chemin absolu de machine.

**Le fait mesure le 2026-09-08.** Trois sorties SUIVIES PAR GIT de
`examples/synthetic_copro` citaient un chemin absolu de 120 caracteres qui
nommait **deux fois la copropriete reelle**, son organisation de stockage et sa
numerotation interne de dossier. Treize occurrences. L'instance synthetique est
celle que la doctrine designe comme la seule publiable: c'est le pire endroit
possible pour une donnee de ce genre, parce que c'est celui ou personne ne
regarde.

**L'axe, et il n'est pas le nom.** Ecrire une garde sur le nom de cette
copropriete-la coderait une modalite: elle protegerait une copropriete et
laisserait passer la suivante. Ce qui se generalise est plus simple et plus
fort - **un chemin absolu est une donnee de MACHINE, jamais une donnee de
copropriete**. Un artefact destine a etre partage se refere a l'instance, donc
relativement a sa racine. La garde porte sur cette propriete-la, et elle
attrape le nom d'utilisateur, le lecteur reseau, l'arborescence de stockage et
le nom de la copropriete d'un seul geste, quels qu'ils soient.

**Ce qui se degrade proprement.** Une forme de chemin absolu inconnue - un
schema `file://`, un montage exotique - ne serait pas vue. La garde ne pretend
donc pas prouver l'absence de toute donnee de machine: elle prouve l'absence
des trois formes qu'elle sait nommer, et elle les nomme.

**Le residu, et il est volontaire.** La garde couvre ce que git SUIT, c'est-a-dire
exactement ce qui partirait sur GitHub. Les journaux locaux de l'instance
d'exemple sont ignores par git et en portent encore 186: ils ne sont pas
publiables, donc ils ne sont pas le sujet. Cette limite est mesuree, pas
supposee.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

RACINE_DEPOT = Path(__file__).resolve().parents[2]
DOSSIER = "examples"

#: Une lettre de lecteur est une lettre SEULE avant les deux-points. Sans cette
#: borne, `https:` se lit comme un lecteur `s:` - faux positif rencontre en
#: ecrivant cette garde, sur le `public_repo_url` de l'instance d'exemple.
FORMES_ABSOLUES: dict[str, "re.Pattern[str]"] = {
    "lettre de lecteur": re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[/\\]"),
    "racine d'utilisateur POSIX": re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/"),
    "partage reseau UNC": re.compile(r"\\\\[A-Za-z0-9._-]+\\[A-Za-z0-9._-]+"),
}

SEPARATEUR_NUL = chr(0)


class ExemplesSansCheminAbsolu(unittest.TestCase):
    def _fichiers_publies(self) -> list[Path]:
        """Ce que git SUIT sous `examples/`, c'est-a-dire ce qui serait publie.

        **Si git ne repond pas, cette methode echoue au lieu de sauter.** Une
        garde qui ne peut pas s'executer ne doit pas rendre un succes: c'est la
        confusion, mesuree ailleurs dans ce depot le meme jour, entre une
        absence de mesure et une mesure conforme.
        """
        try:
            sortie = subprocess.run(
                ["git", "ls-files", "-z", DOSSIER],
                cwd=RACINE_DEPOT,
                capture_output=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as erreur:  # pragma: no cover
            self.fail(
                "la garde n'a pas pu lister les fichiers publies (%s): elle ne "
                "peut donc rien prouver, et ne rend pas un succes" % erreur
            )
        noms = [n for n in sortie.stdout.decode("utf-8").split(SEPARATEUR_NUL) if n]
        self.assertTrue(
            noms, "aucun fichier suivi sous %s: la garde ne mesure rien" % DOSSIER
        )
        return [RACINE_DEPOT / n for n in noms]

    def test_aucun_chemin_absolu_dans_les_fichiers_publiables(self) -> None:
        fautes: list[str] = []
        lus = 0
        for chemin in self._fichiers_publies():
            try:
                texte = chemin.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lus += 1
            for forme, motif in FORMES_ABSOLUES.items():
                trouve = motif.search(texte)
                if trouve is None:
                    continue
                extrait = texte[trouve.start(): trouve.start() + 60]
                fautes.append(
                    "%s: %s -> %r"
                    % (chemin.relative_to(RACINE_DEPOT).as_posix(), forme, extrait)
                )
        self.assertGreater(lus, 0, "aucun fichier lisible: la garde ne mesure rien")
        self.assertEqual(
            [],
            fautes,
            "un artefact partageable porte un chemin absolu de machine:\n  "
            + "\n  ".join(fautes),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
