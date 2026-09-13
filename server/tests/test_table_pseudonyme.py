from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.modules import table_pseudonyme
from coproscope.modules.biffageops import load_corpus_salt
from coproscope.vault import gouvernance_store


"""La table pseudonymisee: ce que l'IA lit, et la preuve qu'elle survit.

Arbitrage de Brice du 2026-09-08, `RM-2026-0126`: le nom de fichier stocke
devient non explicite, une table porte le typage et les champs extraits, et
tout ce qui identifie y est remplace par un pseudonyme.

**Trois choses sont prouvees ici, et une quatrieme est refusee.**

1. l'invariant de contenu: aucune valeur de la table n'est du texte de tiers.
   Verifie sur TOUTES les colonnes, pas sur une liste - une colonne ajoutee
   demain qui porterait un nom brut fait echouer ce test;
2. la survie: la table n'est pas effacee par une reconstruction du coffre. Le
   piege est nomme dans les consignes du depot, et il est ici MESURE au lieu
   d'etre suppose;
3. la trace du deposant, que Brice demande de conserver.

Ce qui n'est PAS prouve, et le test `RESIDU` le dit: que deux mentions de la
meme personne dans deux pieces recoivent le meme pseudonyme. Elles ne le
recoivent pas, parce que le nom de fichier est aliase en bloc.
"""


class TablePseudonyme(unittest.TestCase):
    def setUp(self) -> None:
        depot_racine = Path(__file__).resolve().parents[2]
        source = depot_racine / "examples" / "synthetic_copro"
        self.pile = tempfile.TemporaryDirectory()
        self.addCleanup(self.pile.cleanup)
        self.racine = Path(self.pile.name) / "instance"
        shutil.copytree(source, self.racine)
        config = json.loads((self.racine / "instance.yml").read_text(encoding="utf-8"))
        config.setdefault("settings", {})["vault"] = {"local_root": "./vault_local"}
        (self.racine / "instance.yml").write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.instance = load_instance(str(self.racine / "instance.yml"), None)
        self.sel = load_corpus_salt(self.instance)

    def _ligne_piegee(self) -> dict[str, str]:
        """Une ligne de registre dont chaque champ de tiers porte un patronyme."""

        return {
            "doc_id": "DOC-TEST00000001",
            "file_name": "assignation KERMOVAN lot B12.pdf",
            "original_path": r"raw\assignation KERMOVAN lot B12.pdf",
            "emitter": "Cabinet TANORE et Associes",
            "document_type": "Assignation",
            "suspected_date": "2024-07-03",
            "first_seen": "2026-09-08T10:00:00Z",
            "notes": "dossier KERMOVAN",
        }

    def _ecrit_une_ligne(self, **extra) -> dict[str, str]:
        ligne = table_pseudonyme.ligne_pour_document(self.sel, self._ligne_piegee(), **extra)
        stockees = table_pseudonyme.enregistrer(self.instance, [ligne], [ligne["doc_id"]])
        self.assertEqual(stockees, 1)
        return ligne

    # --- l'invariant de contenu -------------------------------------------------

    def test_aucune_valeur_de_la_table_ne_porte_un_patronyme(self) -> None:
        """L'invariant, verifie sur toutes les colonnes de la ligne stockee.

        On ne cherche pas `le patronyme est-il absent de la colonne X`: on
        parcourt la ligne entiere. Une colonne ajoutee demain qui recopierait
        `file_name` ou `emitter` sans alias tomberait ici.
        """

        self._ecrit_une_ligne()
        lignes = table_pseudonyme.lire(self.instance)
        self.assertEqual(len(lignes), 1, "la table est vide: le test ne prouve rien")

        for colonne, valeur in lignes[0].items():
            with self.subTest(colonne=colonne):
                for interdit in ("KERMOVAN", "TANORE", "assignation ", ".pdf", "raw\\"):
                    self.assertNotIn(
                        interdit,
                        valeur,
                        f"la colonne '{colonne}' rend '{valeur}', qui contient "
                        f"'{interdit}'. C'est du texte ecrit par un tiers: la "
                        "table que lit l'IA ne doit en porter aucun.",
                    )

    def test_le_nom_depose_devient_un_alias_stable(self) -> None:
        """Non explicite ne veut pas dire perdu: le meme nom rend le meme alias."""

        ligne = self._ecrit_une_ligne()
        self.assertTrue(ligne["nom_depose_pseudo"], "le nom depose n'a pas d'alias")
        encore = table_pseudonyme.ligne_pour_document(self.sel, self._ligne_piegee())
        self.assertEqual(
            ligne["nom_depose_pseudo"],
            encore["nom_depose_pseudo"],
            "deux lectures du meme nom rendent deux alias: la table ne permet "
            "plus de reconnaitre qu'il s'agit de la meme piece.",
        )

    def test_le_typage_et_la_date_restent_lisibles(self) -> None:
        """Pseudonymiser ne doit pas rendre la table muette.

        Brice demande que le typage et les champs extraits soient DANS la
        table. Une table qui n'aurait que des alias serait conforme a la lettre
        et inutile: l'IA ne pourrait rien y chercher.
        """

        ligne = self._ecrit_une_ligne()
        self.assertEqual(ligne["type_document"], "Assignation")
        self.assertEqual(ligne["date_presumee"], "2024-07-03")
        self.assertIn("Assignation", ligne["libelle_public"])
        self.assertIn("03/07/2024", ligne["libelle_public"])

    def test_la_trace_du_deposant_est_conservee_des_deux_facons(self) -> None:
        """Brice: « soit par son pseudo, soit par son identifiant [...] peut-etre les deux ».

        Les deux colonnes existent des maintenant. Les ajouter plus tard a une
        table deja ecrite est le piege que `_rattraper_colonnes` a du corriger
        le 2026-09-04.
        """

        ligne = self._ecrit_une_ligne(depose_par="local")
        self.assertEqual(ligne["depose_par_utilisateur"], "local")
        self.assertTrue(ligne["depose_par_pseudo"], "le deposant n'a pas de pseudonyme")
        self.assertNotEqual(ligne["depose_par_pseudo"], ligne["depose_par_utilisateur"])

    # --- la survie a la reconstruction, mesuree ---------------------------------

    def test_la_table_survit_a_une_reconstruction_du_coffre(self) -> None:
        """Le piege nomme dans les consignes, verifie - et corrige au passage.

        **Ce que les consignes disent:** `_reset_schema` est appele a chaque
        reconstruction, donc une table ajoutee a la base de reconstruction sans
        recorder est effacee au rebuild suivant, et la perte est differee donc
        invisible.

        **Ce que la mesure du 2026-09-08 montre, et c'est different.**
        `_reset_schema` n'efface pas tout: c'est une LISTE EXPLICITE de `DROP
        TABLE IF EXISTS` - 5 tables cote coffre local
        (`_local_reconstruction_parts/01_load_and_rebuild.py:216`), une
        vingtaine cote reconstruction principale
        (`_reconstruction_parts/02_schema.py:5`). Mesure faite: une table
        `documents_pseudonymes` creee a la main dans la base reconstruite
        contenait encore sa ligne apres DEUX rebuilds.

        **La conclusion ne change pas, le motif si - et le vrai motif est
        pire.** Une table etrangere n'est pas effacee, elle est OUBLIEE: tout
        le reste de la base est refait depuis les evenements pendant qu'elle
        garde ses lignes d'avant. On n'obtient pas une perte visible, on obtient
        une desynchronisation muette. Et le jour ou quelqu'un range en ajoutant
        son nom a la liste de DROP, elle disparait pour de bon.

        **Et la liste de DROP est elle-meme une enumeration de modalites**,
        exactement le defaut que `RM-2026-0127` corrige ailleurs: elle nomme les
        tables connues le jour ou elle a ete ecrite.

        Ce test verifie donc ce qui compte vraiment: la table vit dans une base
        SEPAREE, que la reconstruction n'ouvre pas.
        """

        self._ecrit_une_ligne()
        self.assertEqual(len(table_pseudonyme.lire(self.instance)), 1)

        chemin_gouvernance = gouvernance_store.store_path(self.instance)
        self.assertTrue(chemin_gouvernance.exists(), "la base de gouvernance n'a pas ete creee")
        avant = chemin_gouvernance.read_bytes()

        from coproscope.vault.local_reconstruction import (
            rebuild_local_reconstruction_from_events,
            resolve_db_path,
        )

        racine_coffre = chemin_gouvernance.parent
        # On appelle la reconstruction PAR LES EVENEMENTS plutot que par
        # `rebuild_local_reconstruction`: c'est le chemin qui execute
        # `_reset_schema` sans exiger l'etat de coffre, les cles ni la crypto.
        # Un test doit echouer pour SA raison, pas parce qu'un fichier d'etat
        # sans rapport avec la question manquait.
        base_reconstruite = resolve_db_path(racine_coffre, None)
        rebuild_local_reconstruction_from_events([], base_reconstruite)
        self.assertTrue(
            base_reconstruite.exists(),
            "la reconstruction n'a pas produit sa base: le test ne prouve rien "
            "sur la survie de la table a cote d'elle.",
        )
        self.assertNotEqual(
            base_reconstruite,
            chemin_gouvernance,
            "les deux bases sont le meme fichier: la separation qui protege la "
            "table n'existe pas.",
        )
        # Second passage: `_reset_schema` droppe les tables d'une base qui
        # existe DEJA. C'est ce passage-la qui effacerait une table mal rangee,
        # et le premier ne le prouverait pas.
        rebuild_local_reconstruction_from_events([], base_reconstruite)

        apres = table_pseudonyme.lire(self.instance)
        self.assertEqual(
            len(apres),
            1,
            "La table pseudonymisee a disparu apres une reconstruction. C'est "
            "exactement le piege `_reset_schema` decrit dans les consignes du "
            "depot: la perte est differee, donc invisible en usage normal.",
        )
        self.assertNotEqual(avant, b"", "lecture de controle vide")

    def test_une_reextraction_epargne_une_correction_humaine(self) -> None:
        """Une donnee saisie par un humain et une donnee derivee ne se rangent pas ensemble.

        Regle du magasin partage: une re-extraction remplace ce qu'elle a
        produit et rien d'autre.
        """

        self._ecrit_une_ligne()
        corrigee = table_pseudonyme.ligne_pour_document(
            self.sel,
            self._ligne_piegee(),
            origine=gouvernance_store.ORIGINE_CORRIGE,
        )
        corrigee["type_document"] = "Proces-verbal"
        table_pseudonyme.enregistrer(self.instance, [corrigee], [])

        self._ecrit_une_ligne()  # re-extraction

        lignes = table_pseudonyme.lire(self.instance)
        humaines = [l for l in lignes if l["origine"] == gouvernance_store.ORIGINE_CORRIGE]
        self.assertEqual(
            len(humaines),
            1,
            "la re-extraction a efface la correction humaine",
        )
        self.assertEqual(humaines[0]["type_document"], "Proces-verbal")

    # --- le residu --------------------------------------------------------------

    def test_RESIDU_deux_pieces_de_la_meme_personne_ne_sont_pas_reliees(self) -> None:
        """L'alias porte sur la CHAINE, pas sur l'entite. C'est la limite du POC.

        Le nom de fichier est aliase en bloc, sans y chercher de patronyme -
        choix delibere, parce que chercher un nom de personne dans une chaine
        est mal pose et casse au syndic suivant (`core/libelle_public.py`).

        Consequence: `assignation KERMOVAN lot B12.pdf` et
        `courrier KERMOVAN 2024.pdf` recoivent deux alias sans rapport. La
        question de Brice - « quand je demande a l'IA des factures de Tanore » -
        n'a donc PAS de reponse dans ce POC, et il l'avait dit lui-meme:
        « Bref, ca, c'est le chantier d'apres. »

        Relier ces mentions est le travail de l'annuaire d'entites, decrit dans
        `docs/cdc_anonymisation_et_annuaire_2026-09-07.md`.
        """

        premiere = table_pseudonyme.ligne_pour_document(self.sel, self._ligne_piegee())
        autre_piece = dict(self._ligne_piegee())
        autre_piece["doc_id"] = "DOC-TEST00000002"
        autre_piece["file_name"] = "courrier KERMOVAN 2024.pdf"
        seconde = table_pseudonyme.ligne_pour_document(self.sel, autre_piece)

        self.assertNotEqual(
            premiere["nom_depose_pseudo"],
            seconde["nom_depose_pseudo"],
            "Deux pieces de la meme personne recoivent le meme alias: la "
            "jonction par entite a ete construite. Relisez ce test et le CDC "
            "multiutilisateur, dont c'est le sujet principal.",
        )


if __name__ == "__main__":
    unittest.main()
