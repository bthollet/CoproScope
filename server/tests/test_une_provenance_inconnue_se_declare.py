# -*- coding: utf-8 -*-
"""Un document dont on ignore l'origine ne se range pas dans une source.

`RM-2026-0052`, defaut (1), reste bloquant releve a la revue d'integration:
*le defaut (1) n'est PAS clos, contrairement a ce que la cellule annonce*. Ce
defaut demandait un **filtre de PROVENANCE**: *ce que CoproScope produit
lui-meme ne doit jamais etre classe comme piece emise par le syndic*.

**Mesure du 2026-09-11 sur l'instance reconstruite a VIDE (858 pieces).**

Le sur-classement d'origine ne se reproduit pas: **10 documents `PV_AG` pour 11
assemblees distinctes au coffre**, tous en provenance `RAW`, tous des PDF -
aucun fichier de travail de CoproScope. **Mais c'est l'instance qui protege, pas
le code**: une reconstruction a vide ne reprend que les formats scelles, donc
les sorties de l'outil n'y entrent jamais. Le filtre demande, lui, **n'existe
nulle part** - zero occurrence de `provenance` dans le module de classement.

**CE QUE LA MESURE A TROUVE A LA PLACE, et c'est pire qu'une absence.** Deux
fourre-tout en serie AFFIRMENT une provenance qu'ils ignorent:

1. `_source_labels` finit par `return "RAW", "raw"` - tout ce qui n'est ni
   depot physique, ni zone brute, ni coffre visible est declare **recu brut**;
2. `source_id_from_register_row` finissait par `return SOURCE_INBOX` - tout ce
   qui n'est reconnu par aucune liste est annonce comme venant de la **boite de
   reception**.

**Et le second etait atteint par TOUT le corpus: 858 sur 858.** Aucun document
ne passait par une regle, parce que `raw` - la valeur que le premier ecrit pour
toute piece deposee dans la zone brute - **ne figurait dans aucune des listes**.
L'ecran annonçait donc *boite de reception* pour la totalite des documents, et
il avait raison **par chance**.

**L'AXE.** Ce qui VARIE: les zones de depot, les noms de dossiers, les modes
d'arrivee d'un document - courriel, dépôt physique, dossier synchronise. Ce qui
reste INVARIANT: **un document dont l'origine n'est pas etablie ne se range pas
dans une source**, parce que nommer une source est une affirmation, et qu'une
affirmation fausse sur l'origine empeche exactement le controle demande.

**Ce que ce lot NE fait pas.** Il ne corrige pas le premier fourre-tout -
`_source_labels` declare toujours `RAW` par defaut. Mesure: **zero fichier du
corpus ne l'atteint**, les 858 venant tous de la zone brute declaree. Le residu
est nomme et reste ouvert.
"""

from __future__ import annotations

import unittest

from coproscope.web.document_intake_sources import (
    SOURCE_INBOX,
    SOURCE_PROVENANCE_INDETERMINEE,
    source_id_from_register_row,
)


class CE_QUI_EST_CONNU_SE_NOMME(unittest.TestCase):
    """La zone brute est la zone des pieces recues, et c'est ecrit."""

    def test_la_zone_brute_donne_la_boite_de_reception(self) -> None:
        """**Le corpus entier passait par le fourre-tout avant ce lot.**"""
        self.assertEqual(
            SOURCE_INBOX,
            source_id_from_register_row({"source_kind": "raw",
                                         "source_zone": "RAW"}))

    def test_la_zone_seule_suffit_si_le_genre_manque(self) -> None:
        self.assertEqual(
            SOURCE_INBOX, source_id_from_register_row({"source_zone": "RAW"}))

    def test_les_autres_sources_connues_ne_bougent_pas(self) -> None:
        """Temoin de non-regression: le lot ne devait pas deplacer ce qui
        etait deja reconnu par une regle."""
        for genre, attendu in (("physical_deposit", SOURCE_INBOX),
                               ("mailbox", "mailbox")):
            with self.subTest(genre=genre):
                self.assertEqual(
                    attendu,
                    source_id_from_register_row({"source_kind": genre}))


class L_INDETERMINE_EXISTE_ET_RESTE_VISIBLE(unittest.TestCase):
    """**Ce que le lot livre vraiment, apres un recul mesure.**

    La valeur `SOURCE_PROVENANCE_INDETERMINEE` a ete creee pour remplacer le
    fourre-tout final. **L'essai a ete annule le meme jour**: un test
    d'interface a montre qu'un document depose PAR LE CANAL inbox disparaissait
    du filtre, parce que **le registre ne porte pas la provenance du canal de
    depot**. L'inconnu doit se signaler, pas s'effacer - et la il effacait.

    Ce qui est acquis et garde ici: la valeur EXISTE, elle est **filtrable de
    plein droit**, et elle porte un libelle. Elle attend que l'amont la
    renseigne. Le `return SOURCE_INBOX` final reste, avec la mesure qui dit
    pourquoi.
    """

    def test_la_valeur_existe_et_se_distingue_de_la_boite_de_reception(self) -> None:
        self.assertNotEqual(SOURCE_PROVENANCE_INDETERMINEE, SOURCE_INBOX)

    def test_elle_est_un_filtre_de_PLEIN_DROIT(self) -> None:
        """**Sans cela, un document indetermine disparaitrait de tous les
        filtres** - c'est le defaut que l'essai annule avait introduit."""
        from coproscope.web.document_intake_sources import (
            REGISTER_SOURCE_IDS,
            SOURCE_IDS,
        )
        self.assertIn(SOURCE_PROVENANCE_INDETERMINEE, SOURCE_IDS)
        self.assertIn(SOURCE_PROVENANCE_INDETERMINEE, REGISTER_SOURCE_IDS)

    def test_elle_porte_un_libelle_lisible(self) -> None:
        from coproscope.web.document_intake_sources import SOURCE_LABELS
        libelle = SOURCE_LABELS.get(SOURCE_PROVENANCE_INDETERMINEE, "")
        self.assertTrue(libelle.strip())
        self.assertIn("ind", libelle.lower())

    def test_le_residu_amont_est_declare_dans_le_code(self) -> None:
        """**Le vrai defaut est en amont**: la chaine de depot connait le canal
        et ne l'ecrit pas dans la ligne. Ce test exige que la raison du recul
        reste lisible la ou quelqu'un la cherchera."""
        from pathlib import Path

        source = (Path(__file__).resolve().parents[1]
                  / "src/coproscope/web/document_intake_sources.py"
                  ).read_text(encoding="utf-8")
        self.assertIn("ne porte pas la provenance du canal de", source)


class LE_RESIDU_EST_NOMME(unittest.TestCase):
    """**Ce que ce lot laisse ouvert, et il faut pouvoir le retrouver.**"""

    def test_le_premier_fourre_tout_subsiste_et_c_est_declare(self) -> None:
        """`_source_labels` declare toujours `RAW` par defaut. Zero fichier du
        corpus ne l'atteint - les 858 viennent de la zone brute declaree -
        donc le corriger ici aurait ete un changement sans mesure. Ce test
        tombera le jour ou quelqu'un le corrigera, et c'est voulu: il faudra
        alors remesurer et retirer ce residu du gouvernail."""
        from pathlib import Path

        source = (Path(__file__).resolve().parents[1]
                  / "src/coproscope/modules/_docuscope_parts"
                  / "01_inventory_and_extraction.py").read_text(encoding="utf-8")
        self.assertIn(
            'return "RAW", "raw"', source,
            "le fourre-tout de `_source_labels` a ete corrige: remesurer son "
            "effet et retirer ce residu de `RM-2026-0052`")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
