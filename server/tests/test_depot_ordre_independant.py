"""L'etat final ne doit pas dependre de l'ordre d'arrivee des documents.

Idee de Brice du 2026-09-07: plusieurs instances vierges, le meme lot de pieces,
deposees dans des ordres differents. C'est un AXE au sens de `CLAUDE.md` -
`l'ordre d'arrivee est un degre de liberte` - et son invariant est que l'etat
final n'en depende pas.

Sa force tient a ce qu'il **ne demande aucune verite terrain**. On ne compare
pas l'outil a un etalon, on le compare a lui-meme: toute difference entre deux
ordres est un defaut, meme quand personne ne sait quel etat serait le bon. C'est
donc le seul controle de justesse qui tourne en CI sans corpus prive.

Ce que la lecture du code laisse attendre: `run_light_pipeline` ne joue la suite
de gouvernance que si le depot COURANT porte de la matiere d'assemblee. Une
piece deposee apres cette passe ne la redeclenche pas, donc les liens qui
auraient du se former vers elle ne se forment jamais - et rien ne le signale.
"""

from __future__ import annotations

import csv
import io
import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.app import create_app

JETON = "ordre-local"

CONVOCATION = (
    "convocation_ag_2026.txt",
    b"CONVOCATION A L'ASSEMBLEE GENERALE ORDINAIRE\n"
    b"Assemblee generale du 20 mai 2026, premiere convocation.\n"
    b"ORDRE DU JOUR\n"
    b"PROJET DE RESOLUTION N1 - Approbation des comptes de l'exercice 2025.\n"
    b"PROJET DE RESOLUTION N2 - Travaux de refection de la toiture, 42 000,00 EUR.\n",
)

PV = (
    "pv_assemblee_2026.txt",
    b"PROCES-VERBAL DE L'ASSEMBLEE GENERALE ORDINAIRE\n"
    b"Assemblee generale du 20 mai 2026\n"
    b"RESOLUTION N1 - Approbation des comptes de l'exercice 2025\n"
    b"Vote a la majorite de l'article 24. POUR: 8500 - CONTRE: 0 - ABSTENTION: 500.\n"
    b"Cette resolution est adoptee.\n"
    b"RESOLUTION N2 - Travaux de refection de la toiture\n"
    b"Le syndicat autorise les travaux pour un montant de 42 000,00 EUR.\n"
    b"Vote a la majorite de l'article 25. POUR: 7200 - CONTRE: 1300 - ABSTENTION: 500.\n"
    b"Cette resolution est adoptee.\n"
    b"RESOLUTION N3 - Mandat au conseil syndical\n"
    b"Vote a la majorite de l'article 25. POUR: 8000 - CONTRE: 500 - ABSTENTION: 500.\n"
    b"Cette resolution est adoptee.\n",
)

DEVIS = (
    "devis_toiture_2026.txt",
    b"DEVIS - Refection de la toiture\n"
    b"Montant total: 42 000,00 EUR TTC.\n"
    b"Reference au vote de l'assemblee generale du 20 mai 2026, resolution N2.\n",
)

#: Les trois ordres, choisis pour toucher les dependances connues.
ORDRES = {
    "convocation_puis_pv": [CONVOCATION, PV, DEVIS],
    "pv_puis_convocation": [PV, CONVOCATION, DEVIS],
    "devis_avant_assemblee": [DEVIS, PV, CONVOCATION],
}

#: Ce qu'on compare. Des comptes, pas du contenu: aucune donnee ne sort d'ici.
TABLES = ("resolutions", "actes_autorisation", "attributs_acte", "convocations", "devis_cites", "liens_gouvernance")


def _instance_vierge(pile: tempfile.TemporaryDirectory) -> Path:
    """Une instance VIDE qui declare son coffre, jamais une copie chargee."""
    depot_racine = Path(__file__).resolve().parents[2]
    source = depot_racine / "examples" / "synthetic_copro"
    racine = Path(pile.name) / "instance"
    racine.mkdir(parents=True)
    shutil.copy(source / "instance.yml", racine / "instance.yml")
    shutil.copytree(source / "system", racine / "system")
    for dossier in ("raw", "registers", "outputs", "staging", "logs"):
        (racine / dossier).mkdir()
    config = json.loads((racine / "instance.yml").read_text(encoding="utf-8"))
    config.setdefault("settings", {})["vault"] = {"local_root": "./vault_local"}
    (racine / "instance.yml").write_text(json.dumps(config, indent=2), encoding="utf-8")
    return racine


def _etat(racine: Path) -> dict[str, object]:
    """L'etat final observable: des comptes, et les identites d'assemblee."""
    etat: dict[str, object] = {}
    registre = racine / "registers" / "registre_documents.csv"
    if registre.exists():
        with io.open(registre, encoding="utf-8") as fichier:
            etat["documents"] = sum(1 for _ in csv.DictReader(fichier))
    else:
        etat["documents"] = 0
    fichiers = list(racine.glob("**/gouvernance.sqlite3"))
    if not fichiers:
        return etat | {table: 0 for table in TABLES} | {"assemblees": []}
    connexion = sqlite3.connect(fichiers[0])
    try:
        presentes = {nom for (nom,) in connexion.execute("select name from sqlite_master where type='table'")}
        for table in TABLES:
            etat[table] = (
                connexion.execute(f'select count(*) from "{table}"').fetchone()[0] if table in presentes else 0
            )
        etat["assemblees"] = (
            sorted(ligne[0] or "" for ligne in connexion.execute("select distinct ag_id from resolutions"))
            if "resolutions" in presentes
            else []
        )
    finally:
        connexion.close()
    return etat


class L_ordre_de_depot_ne_change_pas_l_etat_final(unittest.TestCase):
    def _deposer_dans_l_ordre(self, pieces) -> dict[str, object]:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:  # pragma: no cover - depend de l'environnement
            self.skipTest("FastAPI test client indisponible")
        pile = tempfile.TemporaryDirectory()
        self.addCleanup(pile.cleanup)
        racine = _instance_vierge(pile)
        client = TestClient(create_app(load_instance(None, str(racine)), 2026, access_token=JETON, rebrancher=frozenset({"ajouter_document"})))
        for nom, contenu in pieces:
            reponse = client.post(
                f"/depot?token={JETON}",
                data={"intent": "document", "return": "document_intake", "source": "test-ordre"},
                files=[("files", (nom, contenu, "text/plain"))],
                follow_redirects=False,
            )
            self.assertEqual(reponse.status_code, 303, f"le depot de {nom} n'a pas abouti")
        return _etat(racine)

    def test_trois_ordres_de_depot_rendent_le_meme_etat_final(self) -> None:
        etats = {nom: self._deposer_dans_l_ordre(pieces) for nom, pieces in ORDRES.items()}

        reference_nom, reference = next(iter(etats.items()))
        ecarts: list[str] = []
        for nom, etat in etats.items():
            if nom == reference_nom:
                continue
            for cle, valeur in reference.items():
                if etat[cle] != valeur:
                    ecarts.append(f"{cle}: {reference_nom}={valeur!r} mais {nom}={etat[cle]!r}")

        self.assertEqual(
            ecarts,
            [],
            msg=(
                "L'etat final depend de l'ordre de depot. Ce n'est pas un desaccord de "
                "comptage: les memes pieces produisent deux verites selon l'ordre ou "
                "elles sont arrivees, et l'ecran n'en signale aucune.\n  "
                + "\n  ".join(ecarts)
            ),
        )

    def test_le_meme_ordre_rejoue_rend_le_meme_etat(self) -> None:
        """Garde de la garde: sans elle, un test instable passerait pour un defaut d'ordre."""
        pieces = ORDRES["convocation_puis_pv"]
        self.assertEqual(self._deposer_dans_l_ordre(pieces), self._deposer_dans_l_ordre(pieces))

    def test_le_lot_atteint_les_tables_qu_il_pretend_couvrir(self) -> None:
        """Nomme le residu: ce controle vert couvre moins qu'il n'en a l'air.

        Un vert dont la portee n'est pas dite est le defaut recense en
        `RM-2026-0106`. Mesure du 2026-09-07 sur ce lot: les resolutions, les
        actes, les attributs et les convocations sont bien produits, mais
        `devis_cites` et `liens_gouvernance` restent a ZERO - le devis de la
        fixture n'est pas cite sous la forme structuree que
        `convocation.build_register` sait lire (numero, sous-numero, entreprise,
        montant TTC).

        Consequence a assumer: l'independance a l'ordre est prouvee sur
        l'extraction, PAS sur le rattachement - qui est justement la zone ou la
        lecture du code la donne pour douteuse, une piece deposee apres la passe
        de gouvernance ne la redeclenchant pas.

        Ce test echouera le jour ou quelqu'un enrichira la fixture, et c'est le
        but: il rend la limite visible au lieu de la laisser en commentaire.
        """
        etat = self._deposer_dans_l_ordre(ORDRES["convocation_puis_pv"])
        couvertes = {table for table in TABLES if etat[table]}
        self.assertEqual(
            couvertes,
            {"resolutions", "actes_autorisation", "attributs_acte", "convocations"},
            msg=(
                "La couverture de ce lot a change. Si elle s'est ELARGIE, mettez a jour "
                "cette attente et supprimez la reserve de la docstring: le controle "
                "d'ordre porte alors aussi sur le rattachement. Si elle s'est RETRECIE, "
                "c'est une regression de la chaine."
            ),
        )


if __name__ == "__main__":
    unittest.main()
