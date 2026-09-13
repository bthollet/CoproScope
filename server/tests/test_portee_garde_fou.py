"""Le garde-fou des 600 lignes regarde-t-il la ou le code est ecrit ?

Ce fichier existe a cause d'un trou dans ma propre correction.

Le 2026-09-07, `clients/` a ete ajoute a `SCOPED_ROOTS`: 1941 lignes de
JavaScript, de HTML et de CSS vivaient hors du regard du garde-fou, qui rendait
*conforme* depuis des semaines - et c'etait vrai **de ce qu'il regardait**.

La correction est partie **sans test**. Si `clients` disparaissait demain de la
liste, rien ne tomberait: le garde-fou rendrait de nouveau *conforme*, a
l'identique, et personne ne verrait la difference. Une session voisine l'a
releve, et elle avait raison.

C'est le mode de panne propre aux GARDES, et il differe de celui des
extracteurs. Un extracteur fautif rend une reponse fausse, qui finit par se
voir. Une garde fautive rend une **fausse tranquillite**, indetectable par
construction: son silence est identique a une reussite.

D'ou la question qu'il faut poser a toute garde, et que la regle des axes ne
pose pas: *quand cette garde cessera d'etre vraie, comment l'apprendra-t-on ?*
Si la reponse est *un autre test tombera* ou *quelqu'un le remarquera*, la
garde code des modalites.

Le test qui manquait n'est donc pas un test de comportement - un autre verifie
deja que la limite est respectee - c'est un test de **portee**.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
OUTIL = RACINE / "tools" / "check_code_line_limit.py"


def _charger():
    spec = importlib.util.spec_from_file_location("check_code_line_limit", OUTIL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"garde-fou introuvable: {OUTIL}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


garde = _charger()

#: Les racines qui portent des fichiers aux suffixes surveilles et qui restent
#: DELIBEREMENT hors de la portee, avec leur raison.
#:
#: Cette liste est le pendant necessaire du test derive ci-dessous. Sans elle,
#: le test signalerait des exclusions voulues et finirait par etre desarme -
#: c'est-a-dire par redevenir le silence qu'il existe pour empecher. Avec elle,
#: un dossier NOUVEAU tombe, et quelqu'un doit trancher: dans la portee, ou
#: dans cette liste avec un motif.
HORS_PORTEE_ASSUMEES = {
    "docs": "documentation et brouillons: la regle du depot les exclut nommement",
    "examples": "instances d'exemple, donnees et non code maintenu",
}


class PorteeTests(unittest.TestCase):
    def test_toute_racine_qui_porte_du_code_est_regardee(self) -> None:
        """La portee se DERIVE de l'arborescence reelle, au lieu d'etre relue.

        Une liste ecrite une fois ne se met pas a jour quand un dossier
        apparait - c'est precisement ce qui est arrive a `clients/`. Ce test
        cherche donc lui-meme les dossiers de premier niveau qui portent des
        fichiers aux suffixes surveilles, et exige qu'ils soient dans la portee.

        Il tombera le jour ou quelqu'un creera un dossier de code sans y penser.
        C'est le but: la prochaine fois, personne n'aura a le remarquer.
        """
        suffixes = {s.lower() for s in garde.SCOPED_SUFFIXES}
        exclus = set(garde.EXCLUDED_DIR_NAMES)
        portant_du_code: set[str] = set()

        for dossier in sorted(p for p in RACINE.iterdir() if p.is_dir()):
            if dossier.name in exclus:
                continue
            if dossier.name.startswith(".") and dossier.name != ".github":
                continue
            for fichier in dossier.rglob("*"):
                if not fichier.is_file():
                    continue
                if fichier.suffix.lower() not in suffixes:
                    continue
                if any(part in exclus for part in fichier.parts):
                    continue
                portant_du_code.add(dossier.name)
                break

        oublies = sorted(
            portant_du_code - set(garde.SCOPED_ROOTS) - set(HORS_PORTEE_ASSUMEES)
        )
        self.assertEqual(
            oublies,
            [],
            f"Ces dossiers portent du code que le garde-fou ne regarde pas: "
            f"{oublies}. Son silence ressemblerait a une reussite. Mettez-les "
            f"dans `SCOPED_ROOTS`, ou dans `HORS_PORTEE_ASSUMEES` avec un motif.",
        )

    def test_les_exclusions_assumees_le_sont_encore(self) -> None:
        """Une exclusion voulue ne doit pas se transformer en inclusion muette.

        Si `docs` entrait un jour dans la portee, le motif ecrit ici
        deviendrait faux et personne ne s'en apercevrait. Le test tient les
        deux sens.
        """
        for nom in HORS_PORTEE_ASSUMEES:
            with self.subTest(racine=nom):
                self.assertNotIn(nom, garde.SCOPED_ROOTS)

    def test_clients_est_nomme_dans_la_portee(self) -> None:
        """La regle derivee ci-dessus suffirait, mais elle ne dirait pas
        POURQUOI si elle tombait. Celle-ci nomme la trouvaille et son chiffre,
        pour que la prochaine personne comprenne l'enjeu sans relire un
        journal."""
        self.assertIn("clients", garde.SCOPED_ROOTS)

    def test_le_code_du_plugin_est_reellement_compte(self) -> None:
        """Etre dans la liste ne prouve pas etre compte: le suffixe compte
        aussi. Ce test mesure ce que le garde-fou voit vraiment dans
        `clients/`."""
        suffixes = {s.lower() for s in garde.SCOPED_SUFFIXES}
        lignes = 0
        for fichier in (RACINE / "clients").rglob("*"):
            if fichier.is_file() and fichier.suffix.lower() in suffixes:
                lignes += len(
                    fichier.read_text(encoding="utf-8", errors="ignore").splitlines()
                )
        self.assertGreater(
            lignes,
            1000,
            "Le garde-fou ne compte presque rien dans `clients/`: soit le code "
            "a disparu, soit ses suffixes sont sortis de la surveillance.",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
