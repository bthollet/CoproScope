# -*- coding: utf-8 -*-
"""La derive de schema ne se produit plus, et le magasin ne la tait plus.

**`RM-2026-0066`, defaut mesure le 2026-09-04 puis corrige le meme jour - mais
laisse SANS GARDE jusqu'au 2026-09-09.** Le correctif tenait par trois
docstrings et rien d'autre; ces tests sont ce qui l'empeche de repartir.

**Le defaut, et il etait differe.** `CREATE TABLE IF NOT EXISTS` ne rattrape
rien: une colonne ajoutee au modele APRES qu'une base locale a ete ecrite
n'apparaissait jamais dans cette base. **Invisible en test**, parce que la base
y est neuve a chaque fois; visible seulement chez quelqu'un qui met a jour le
logiciel sur une base existante. C'est exactement pour cela que ce fichier
fabrique une base **ancienne** avant de la relire.

**Le second etage etait pire.** `except sqlite3.OperationalError: return []`,
sans distinction du message, confondait trois situations dans une seule valeur:
rien n'a encore ete lu, la colonne du tri n'existe plus, la colonne demandee a
ete renommee. Mesure pendant le lot: **0 constat au lieu de 818, en silence**,
et l'ecran envoyait l'utilisateur verifier la qualite d'extraction d'un
document parfaitement lisible.
"""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from coproscope.vault import gouvernance_store as G

TABLE = G.TABLE_RESOLUTIONS
#: Le modele d'AVANT: c'est la base que possede quelqu'un qui n'a pas encore
#: mis a jour le logiciel.
CHAMPS_ANCIENS = ["resolution_id", "ag_id", "doc_id", "position", "objet", "etat", "origine"]
#: Le modele d'APRES, avec deux colonnes de plus.
CHAMPS_NEUFS = CHAMPS_ANCIENS + ["numero", "sous_numero"]


class _Instance:
    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()


class DeriveDeSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)
        # Une base ECRITE AVEC L'ANCIEN MODELE, comme celle d'un utilisateur
        # dont l'installation date d'avant l'ajout des colonnes.
        with G.connexion(self.instance) as connection:
            G.ensure_schema(connection, CHAMPS_ANCIENS, table=TABLE,
                            cles=G.CLES_RESOLUTIONS)
            connection.execute(
                'INSERT INTO "%s" (resolution_id, ag_id, doc_id, position, objet, etat, origine) '
                "VALUES (?, ?, ?, ?, ?, ?, ?)" % TABLE,
                ("R-1", "AG-2024-07-03", "DOC-1", "1", "Approbation des comptes",
                 "CONSTATEE", G.ORIGINE_EXTRAIT),
            )
            # `connexion()` ferme a coup sur mais ne valide pas: la validation
            # appartient a l'appelant. Sans ce `commit`, le schema survit - le
            # DDL se valide seul en SQLite - et la LIGNE disparait. Un test qui
            # l'oublierait mesurerait une base vide en croyant mesurer une
            # migration.
            connection.commit()

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=False)

    def _colonnes(self) -> set[str]:
        with closing(sqlite3.connect(G.store_path(self.instance))) as c:
            return {r[1] for r in c.execute('PRAGMA table_info("%s")' % TABLE)}

    def test_la_base_ancienne_n_a_pas_les_colonnes_neuves(self) -> None:
        """Garde de l'instrument: sans cela, les tests suivants ne prouvent rien.

        Si la mise en place fabriquait deja une base a jour, le rattrapage
        n'aurait rien a rattraper et le test passerait au vert sans mesurer.
        """
        self.assertNotIn("numero", self._colonnes())
        self.assertNotIn("sous_numero", self._colonnes())

    def test_une_colonne_ajoutee_au_modele_apparait_dans_une_base_ancienne(self) -> None:
        """Le coeur de `RM-2026-0066`. La colonne se rattrape, sans edition."""
        with G.connexion(self.instance) as connection:
            G.ensure_schema(connection, CHAMPS_NEUFS, table=TABLE, cles=G.CLES_RESOLUTIONS)
        self.assertIn("numero", self._colonnes())
        self.assertIn("sous_numero", self._colonnes())

    def test_le_rattrapage_ne_perd_aucune_ligne(self) -> None:
        """Une migration qui perdrait les donnees serait pire que le defaut."""
        with G.connexion(self.instance) as connection:
            G.ensure_schema(connection, CHAMPS_NEUFS, table=TABLE, cles=G.CLES_RESOLUTIONS)
        lignes = G.lire(self.instance, table=TABLE, ordre="position")
        self.assertEqual(1, len(lignes))
        self.assertEqual("Approbation des comptes", lignes[0]["objet"])
        self.assertEqual("", lignes[0]["numero"])

    def test_une_base_absente_rend_une_liste_vide_et_ne_leve_pas(self) -> None:
        """Une instance ou rien n'a ete lu n'est pas une erreur."""
        vierge = _Instance(Path(tempfile.mkdtemp()))
        try:
            self.assertEqual([], G.lire(vierge, table=TABLE))
        finally:
            shutil.rmtree(vierge.racine, ignore_errors=True)

    def test_une_table_absente_rend_une_liste_vide(self) -> None:
        self.assertEqual([], G.lire(self.instance, table="table_qui_n_existe_pas"))

    def test_une_colonne_de_tri_disparue_LEVE_au_lieu_de_rendre_vide(self) -> None:
        """Le point 3 du correctif, et le plus important des trois.

        Une liste vide serait **indiscernable d'un registre vide**, et l'ecran
        accuserait la source au lieu du schema. Mesure du 2026-09-04: apres un
        simple renommage de la colonne du tri, l'ecran passait de deux
        assemblees a *registre vide* alors que la table portait toujours ses
        173 lignes.
        """
        with self.assertRaises(G.SchemaDeGouvernanceDivergent) as leve:
            G.lire(self.instance, table=TABLE, ordre="colonne_qui_n_existe_pas")
        message = str(leve.exception)
        self.assertIn(TABLE, message)
        self.assertIn("colonne_qui_n_existe_pas", message)

    def test_le_message_dit_ce_qu_une_liste_vide_aurait_cache(self) -> None:
        """Un message qui ne nomme pas le piege laisse refaire l'erreur."""
        with self.assertRaises(G.SchemaDeGouvernanceDivergent) as leve:
            G.lire(self.instance, table=TABLE, ordre="tri_absent")
        self.assertIn("indiscernable", str(leve.exception))

    def test_une_cle_primaire_qui_a_change_est_refusee(self) -> None:
        """Elargir la cle dans le code est SANS EFFET sur une table deja creee.

        Trou mesure le 2026-09-04 et non couvert par le correctif propose:
        `CREATE TABLE IF NOT EXISTS` ne recree rien, donc la contrainte reste
        celle d'origine et les collisions changent de nature en silence.
        """
        with G.connexion(self.instance) as connection:
            with self.assertRaises(G.SchemaDeGouvernanceDivergent):
                G.ensure_schema(
                    connection, CHAMPS_NEUFS, table=TABLE,
                    cles=("resolution_id", "doc_id", "ag_id"),
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
