"""La suite de gouvernance est definie une fois, et elle produit vraiment.

Ces gardes manquaient toutes les quatre. Leur absence est ce qui a permis a deux
orchestrateurs de diverger sans que rien ne rougisse: `web/depot.py` portait la
suite resolutions -> actes, `core/pipeline.py` ne la portait pas, et
`convocation.build_register` n'etait appele par aucun des deux alors que le pont
lit la table `devis_cites` qu'il ecrit.

Aucun test n'exercait la chaine de bout en bout: la mesure croisee du 2026-09-07
n'a trouve AUCUN fichier de `server/tests/` citant a la fois `build_register` et
`pont_actes`. Les tests d'ecran semaient `actes_autorisation` a la main, donc ils
prouvaient que l'ecran sait afficher des actes, jamais que la chaine sait en
produire.
"""

from __future__ import annotations

import io
import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance
from coproscope.core.pipeline import SEQUENCE_GOUVERNANCE, run_pipeline

PV_MINIMAL = """PROCES-VERBAL DE L'ASSEMBLEE GENERALE ORDINAIRE
Assemblee generale du 20 mai 2026

RESOLUTION N1 - Approbation des comptes de l'exercice 2025
Le syndicat approuve les comptes de l'exercice clos le 31 decembre 2025.
Vote a la majorite de l'article 24. POUR: 8500 - CONTRE: 0 - ABSTENTION: 500.
Cette resolution est adoptee.

RESOLUTION N2 - Travaux de refection de la toiture
Le syndicat autorise les travaux de refection de la toiture pour un montant de
42 000,00 EUR, conformement au devis de l'entreprise mandatee.
Vote a la majorite de l'article 25. POUR: 7200 - CONTRE: 1300 - ABSTENTION: 500.
Cette resolution est adoptee.

RESOLUTION N3 - Mandat donne au conseil syndical
Le syndicat donne mandat au conseil syndical pour engager les depenses courantes
dans la limite de 5 000,00 EUR par operation, pour une duree de douze mois.
Vote a la majorite de l'article 25. POUR: 8000 - CONTRE: 500 - ABSTENTION: 500.
Cette resolution est adoptee.
"""


def _instance_vide(avec_coffre: bool) -> tuple[tempfile.TemporaryDirectory, Path]:
    """Une instance construite VIDE, qui reabsorbe ses pieces.

    Pas une copie chargee: une copie chargee porte la sortie de la version
    precedente du code et la fait entrer comme si elle etait une entree.
    Consigne de Brice du 2026-09-07, inscrite dans `CLAUDE.md`.
    """
    depot_racine = Path(__file__).resolve().parents[2]
    source = depot_racine / "examples" / "synthetic_copro"
    tempdir = tempfile.TemporaryDirectory()
    racine = Path(tempdir.name) / "instance"
    racine.mkdir(parents=True)
    shutil.copy(source / "instance.yml", racine / "instance.yml")
    shutil.copytree(source / "raw", racine / "raw")
    shutil.copytree(source / "system", racine / "system")
    for dossier in ("registers", "outputs", "staging", "logs"):
        (racine / dossier).mkdir()
    config = json.loads((racine / "instance.yml").read_text(encoding="utf-8"))
    if avec_coffre:
        config.setdefault("settings", {})["vault"] = {"local_root": "./vault_local"}
    else:
        config.get("settings", {}).pop("vault", None)
    (racine / "instance.yml").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (racine / "raw" / "2026-05-20_pv_assemblee_generale.txt").write_text(PV_MINIMAL, encoding="utf-8")
    return tempdir, racine


def _compte(racine: Path, table: str) -> int:
    """Compte les lignes d'une table du coffre, en FERMANT la connexion.

    `with sqlite3.connect(...)` gere la transaction et non la fermeture: sous
    Windows le fichier reste verrouille et le menage du repertoire temporaire
    echoue, ce qui fait rougir un test dont le sujet n'a rien a voir.
    """
    fichiers = list(racine.glob("**/gouvernance.sqlite3"))
    if not fichiers:
        return 0
    connexion = sqlite3.connect(fichiers[0])
    try:
        return connexion.execute(f'select count(*) from "{table}"').fetchone()[0]
    finally:
        connexion.close()


class LaSuiteEstDefinieUneSeuleFois(unittest.TestCase):
    """Garde de PORTEE, pas de comportement: qui joue la suite, et laquelle.

    Elle rougit si une entree gagne ou perd une etape que l'autre n'a pas. C'est
    exactement ce qui manquait: la divergence s'est installee sans bruit parce
    qu'aucun test ne regardait la liste.
    """

    def test_la_sequence_porte_les_quatre_maillons_dans_l_ordre_de_leurs_dependances(self) -> None:
        noms = [nom for nom, _ in SEQUENCE_GOUVERNANCE]
        self.assertEqual(noms, ["ag", "resolutions", "convocations", "actes"])

    def test_les_deux_entrees_passent_par_la_sequence_partagee_et_non_par_leur_propre_liste(self) -> None:
        depot = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "depot.py"
        source = depot.read_text(encoding="utf-8")
        self.assertIn("run_gouvernance_sequence", source)
        for maillon in ("resolutions.build_register", "pont_actes.build_actes", "agscope.analyze"):
            self.assertNotIn(
                maillon,
                source,
                msg=(
                    f"`{maillon}` est appele directement dans depot.py: la suite y est "
                    "donc redefinie, et elle peut diverger de core.pipeline comme elle "
                    "l'avait deja fait."
                ),
            )


class LaChaineProduitVraimentDesActes(unittest.TestCase):
    def test_une_instance_vide_reabsorbee_rend_resolutions_convocations_et_actes(self) -> None:
        tempdir, racine = _instance_vide(avec_coffre=True)
        self.addCleanup(tempdir.cleanup)
        self.assertEqual(list((racine / "registers").iterdir()), [], "l'instance doit partir vide")

        instance = load_instance(None, str(racine))
        rapport = run_pipeline(instance, RunContext(instance, "test sequence"), copy_classified=False)

        self.assertEqual([e["etape"] for e in rapport["gouvernance"]], ["ag", "resolutions", "convocations", "actes"])
        self.assertGreater(_compte(racine, "resolutions"), 0, "aucune resolution extraite du PV")
        self.assertGreater(_compte(racine, "convocations"), 0, "convocation.build_register n'a rien ecrit")
        self.assertGreater(
            _compte(racine, "actes_autorisation"),
            0,
            "aucun acte verse: c'est l'etat que l'ecran de gouvernance rendait avant ce lot",
        )


class UneChaineSansCoffreLeDitAuLieuDeSeTaire(unittest.TestCase):
    def test_sans_coffre_declare_la_chaine_ne_leve_pas_et_nomme_ce_qui_n_a_pas_pu_se_faire(self) -> None:
        tempdir, racine = _instance_vide(avec_coffre=False)
        self.addCleanup(tempdir.cleanup)

        instance = load_instance(None, str(racine))
        rapport = run_pipeline(instance, RunContext(instance, "test degradation"), copy_classified=False)

        resultats = {e["etape"]: e["resultat"] for e in rapport["gouvernance"]}
        self.assertTrue(
            resultats["resolutions"].get("coffre_non_declare"),
            "une instance sans coffre doit DIRE pourquoi elle ne produit rien",
        )
        self.assertTrue(resultats["actes"].get("registre_vide"))


class L_ecran_rend_ce_que_la_chaine_a_produit(unittest.TestCase):
    """L'axe est `la page rend ce que la chaine a produit`.

    Pas `la page contient telle chaine de caracteres`: une garde ecrite sur une
    chaine mesure la coque autant que la page, defaut recense en `RM-2026-0106`.
    """

    def test_le_controle_de_gouvernance_passe_de_coffre_absent_a_pret_apres_la_chaine(self) -> None:
        from coproscope.web.controle_gouvernance_view import build_controle_gouvernance_view

        tempdir, racine = _instance_vide(avec_coffre=True)
        self.addCleanup(tempdir.cleanup)
        instance = load_instance(None, str(racine))

        avant = build_controle_gouvernance_view(instance, 2026, {}, token="t")
        self.assertNotEqual(avant["diagnostic"]["etat"], "pret", "l'ecran ne peut pas etre pret avant la chaine")

        run_pipeline(instance, RunContext(instance, "test ecran"), copy_classified=False)

        apres = build_controle_gouvernance_view(instance, 2026, {}, token="t")
        self.assertEqual(apres["diagnostic"]["etat"], "pret")
        self.assertGreater(len(apres.get("lignes") or []), 0, "l'ecran est pret mais ne rend aucune ligne")


if __name__ == "__main__":
    unittest.main()
