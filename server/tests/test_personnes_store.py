from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.modules import _personnes_store as store
from coproscope.modules._personnes_schema import (
    DROIT_INDIVISION,
    DROIT_NUE_PROPRIETE,
    DROIT_USUFRUIT,
    MASQUER,
    NATURE_MORALE,
    NATURE_PHYSIQUE,
    PRESERVER,
    SOURCE_HUMAINE,
    SOURCE_LISTE,
    TABLE_LOTS,
    TABLE_PERSONNES,
    TABLE_RATTACHEMENTS,
)


"""La base des personnes, des lots et des rattachements dates.

Le droit de la copropriete impose ce que l'annuaire plat ne sait pas dire:
plusieurs personnes sur un lot (indivision), deux droits distincts sur un lot
(usufruit et nue-propriete), et une detention indirecte par une SCI.

Donnees entierement fictives.
"""


class BaseDesPersonnes(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self._declare_le_coffre_local()
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def _declare_le_coffre_local(self) -> None:
        """L'instance synthetique ne declare pas de coffre; ces tables y vivent.

        Le magasin `gouvernance.sqlite3` est le seul qui ne soit pas reconstruit.
        Sans `settings.vault.local_root`, il n'a pas de chemin - et le module
        leve plutot que d'ecrire ailleurs en silence, ce qui est le bon reflexe.
        """

        chemin = self.instance_root / "instance.yml"
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
        contenu.setdefault("settings", {})["vault"] = {"local_root": "./vault_local"}
        chemin.write_text(json.dumps(contenu, indent=2), encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _personne(self, personne_id: str, **extra: str) -> dict[str, str]:
        base = {
            "personne_id": personne_id,
            "doc_id": "DOC-ANNEXE",
            "origine": store.ORIGINE_EXTRAIT,
            "nature": NATURE_PHYSIQUE,
            "masquage": MASQUER,
            "source": SOURCE_LISTE,
        }
        base.update(extra)
        return base

    def test_une_base_absente_rend_une_liste_vide_et_non_une_erreur(self) -> None:
        """Aucune liste nominative lue n'est un etat normal, pas une panne."""

        self.assertEqual(store.personnes(self.instance), [])
        self.assertEqual(store.lots(self.instance), [])

    def test_une_valeur_hors_liste_fermee_leve_avant_ecriture(self) -> None:
        with self.assertRaises(store.ValeurHorsListe):
            store.remplacer_pour_documents(
                self.instance,
                TABLE_PERSONNES,
                [self._personne("PERS-1", nature="societe_anonyme")],
                ["DOC-ANNEXE"],
            )

    def test_une_correction_humaine_survit_a_une_re_extraction(self) -> None:
        """La garde de la couche partagee, verifiee de bout en bout."""

        store.remplacer_pour_documents(
            self.instance,
            TABLE_PERSONNES,
            [
                self._personne("PERS-MACHINE", nom_normalise="MARCHAND"),
                self._personne(
                    "PERS-HUMAIN",
                    origine=store.ORIGINE_CORRIGE,
                    nom_normalise="VALLIOT",
                    source=SOURCE_HUMAINE,
                ),
            ],
            ["DOC-ANNEXE"],
        )
        # Une nouvelle extraction du meme document ne rend que la ligne machine.
        store.remplacer_pour_documents(
            self.instance,
            TABLE_PERSONNES,
            [self._personne("PERS-MACHINE", nom_normalise="MARCHAND")],
            ["DOC-ANNEXE"],
        )
        identifiants = {row["personne_id"] for row in store.personnes(self.instance)}
        self.assertIn("PERS-MACHINE", identifiants)
        self.assertIn("PERS-HUMAIN", identifiants)

    def test_une_indivision_garde_tous_ses_detenteurs(self) -> None:
        """Plusieurs personnes sur un lot est normal, jamais une anomalie."""

        self._rattache(
            [
                ("RAT-1", "PERS-A", DROIT_INDIVISION, "1/3"),
                ("RAT-2", "PERS-B", DROIT_INDIVISION, "1/3"),
                ("RAT-3", "PERS-C", DROIT_INDIVISION, "1/3"),
            ]
        )
        detenteurs = store.detenteurs_du_lot(self.instance, "LOT-12")
        self.assertEqual(len(detenteurs), 3)
        self.assertEqual({row["quote_part"] for row in detenteurs}, {"1/3"})

    def test_un_demembrement_garde_les_deux_droits(self) -> None:
        self._rattache(
            [
                ("RAT-U", "PERS-PARENT", DROIT_USUFRUIT, ""),
                ("RAT-N", "PERS-ENFANT", DROIT_NUE_PROPRIETE, ""),
            ]
        )
        droits = {row["droit"] for row in store.detenteurs_du_lot(self.instance, "LOT-12")}
        self.assertEqual(droits, {DROIT_USUFRUIT, DROIT_NUE_PROPRIETE})

    def test_le_rattachement_est_lu_a_la_date_de_la_piece(self) -> None:
        """Un PV de 2019 concerne le proprietaire de 2019, pas celui d'aujourd'hui."""

        self._rattache(
            [("RAT-ANCIEN", "PERS-VENDEUR", DROIT_PLEINE := "pleine_propriete", "")],
            date_piece="2019-06-01",
        )
        self._rattache(
            [("RAT-NEUF", "PERS-ACQUEREUR", DROIT_PLEINE, "")],
            date_piece="2024-07-03",
            doc_id="DOC-PV-2024",
        )
        en_2019 = store.detenteurs_du_lot(self.instance, "LOT-12", a_la_date="2019-12-31")
        self.assertEqual([row["personne_id"] for row in en_2019], ["PERS-VENDEUR"])
        aujourdhui = store.detenteurs_du_lot(self.instance, "LOT-12")
        self.assertEqual([row["personne_id"] for row in aujourdhui], ["PERS-ACQUEREUR"])

    def test_le_masquage_se_decide_par_entite_et_non_par_nature(self) -> None:
        """Une SARL fournisseur se preserve, une SCI patronymique se masque."""

        store.remplacer_pour_documents(
            self.instance,
            TABLE_PERSONNES,
            [
                self._personne(
                    "PERS-SARL", nature=NATURE_MORALE, masquage=PRESERVER, nom_source="BATIPRO"
                ),
                self._personne(
                    "PERS-SCI", nature=NATURE_MORALE, masquage=MASQUER, nom_source="SCI VALLIOT"
                ),
            ],
            ["DOC-ANNEXE"],
        )
        par_id = {row["personne_id"]: row for row in store.personnes(self.instance)}
        self.assertEqual(par_id["PERS-SARL"]["masquage"], PRESERVER)
        self.assertEqual(par_id["PERS-SCI"]["masquage"], MASQUER)
        self.assertEqual(par_id["PERS-SARL"]["nature"], par_id["PERS-SCI"]["nature"])

    def test_le_total_des_tantiemes_est_inconnu_plutot_que_zero(self) -> None:
        """`None` n'est pas zero: c'est ce qui evite un pourcentage faux."""

        self.assertIsNone(store.total_tantiemes(self.instance))
        store.remplacer_pour_documents(
            self.instance,
            TABLE_LOTS,
            [
                {
                    "lot_id": "LOT-12",
                    "doc_id": "DOC-EDD",
                    "origine": store.ORIGINE_EXTRAIT,
                    "reference": "12",
                    "cle_repartition": "generale",
                    "tantiemes": "340",
                    "base_tantiemes": "10000",
                },
                {
                    "lot_id": "LOT-13",
                    "doc_id": "DOC-EDD",
                    "origine": store.ORIGINE_EXTRAIT,
                    "reference": "13",
                    "cle_repartition": "generale",
                    "tantiemes": "660",
                    "base_tantiemes": "10000",
                },
            ],
            ["DOC-EDD"],
        )
        self.assertEqual(store.total_tantiemes(self.instance), 1000)
        self.assertIsNone(store.total_tantiemes(self.instance, "batiment_B"))

    def _rattache(
        self,
        entrees: list[tuple[str, str, str, str]],
        date_piece: str = "2024-07-03",
        doc_id: str = "DOC-ANNEXE",
    ) -> None:
        store.remplacer_pour_documents(
            self.instance,
            TABLE_RATTACHEMENTS,
            [
                {
                    "rattachement_id": rattachement_id,
                    "doc_id": doc_id,
                    "origine": store.ORIGINE_EXTRAIT,
                    "personne_id": personne_id,
                    "lot_id": "LOT-12",
                    "droit": droit,
                    "quote_part": quote_part,
                    "date_piece": date_piece,
                    "source": SOURCE_LISTE,
                }
                for rattachement_id, personne_id, droit, quote_part in entrees
            ],
            [doc_id],
        )


if __name__ == "__main__":
    unittest.main()
