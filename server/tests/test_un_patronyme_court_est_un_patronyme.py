# -*- coding: utf-8 -*-
"""Un patronyme etabli par une civilite tombe, quelle que soit sa longueur.

`RM-2026-0097`, qualifie et repare le 2026-09-11. L'item demandait de
*remplacer la garde par liste par une garde par CONTEXTE*, et nommait
explicitement ce qu'il ne fallait pas faire: *ni en allongeant une liste de
mots ni en abaissant un seuil de longueur*.

**LA LIGNE VISEE PORTAIT CE SEUIL.** `_noms_nus` ecartait tout token de moins
de quatre caracteres: `if len(token) < 4 or not _nom_recevable(token)`.

**Ce qu'il faisait, mesure sur le point d'entree `detecte_identites`.** Un
patronyme de moins de quatre lettres, **pourtant etabli par une civilite**, ne
voyait PAS ses occurrences isolees caviardees. `Mme KIM Sophie` etablissait
`KIM`, et `KIM` restait **en clair a la ligne suivante** - exactement ce que la
docstring de `_noms_nus` dit vouloir empecher: *sinon le caviardage laisse le
nom en clair a la ligne suivante*.

| nom | longueur | occurrences isolees caviardees, avant |
|---|---:|---|
| `VANDERSTOCKE` | 12 | oui |
| `DUPONT` | 6 | oui |
| `KIM` | 3 | **non** |
| `NGO` | 3 | **non** |
| `LI` | 2 | non |

**ET LE SEUIL ETAIT REDONDANT AVEC LE LEXIQUE.** Mesure des mots courts que
l'on pouvait craindre de masquer: `RUE`, `TVA`, `LOT`, `EUR`, `TTC`, `HT` sont
**deja refuses par `_nom_recevable`**, qui impose par ailleurs trois
caracteres - donc `LI` et `WU` restent exclus sans lui. **Ce que le seuil
excluait EN PLUS du lexique n'etait donc que des patronymes recevables**:
`KIM`, `NGO`, `BUI`, `DUC`. Une garde qui ne retire plus que des vrais noms ne
protege plus rien: elle laisse fuir.

**L'AXE.** Ce qui VARIE: la longueur d'un patronyme, son origine, sa
frequence. Ce qui reste INVARIANT: **ce n'est pas la longueur qui distingue un
patronyme d'un mot courant, c'est le fait qu'une civilite l'ait etabli** - et
`_noms_nus` ne traite QUE des noms deja etablis ainsi. La longueur n'apportait
donc aucune information que le contexte ne donnait deja.

**Le residu est etroit et nomme.** `BIS` passe le lexique. Il ne sera caviarde
que si une civilite l'a etabli comme nom - `Mme BIS` - ce que cette fonction
exige avant tout. Le risque existe; laisser fuir des patronymes courants
coutait plus cher.

**DOUBLON TRANCHE.** La cellule signalait que `RM-2026-0065`, `RM-2026-0097` et
`RM-2026-0099` visent une seule ligne de code, et interdisait d'ouvrir un
chantier avant d'avoir dit lequel porte la reparation. **C'est `RM-2026-0097`**,
parce que c'est lui qui nomme l'axe et le seuil. `RM-2026-0065` est deja
`INTEGRE`; `RM-2026-0099` porte un autre sujet - la boucle de correction
humaine de l'annuaire - qui n'est pas touche ici.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import coproscope.modules.biffageops as biffageops

DEPOT = Path(__file__).resolve().parents[2]
MODULE = (DEPOT / "server/src/coproscope/modules/_biffageops_parts"
          / "04_corpus_identites.py")


def _motifs(nom: str) -> list[str]:
    """Les motifs rendus pour un nom etabli par une civilite puis repete."""
    texte = (
        "Le mandat est donne a Mme %s Sophie pour cet exercice.\n"
        "%s prendra part au vote de la resolution suivante.\n" % (nom, nom)
    )
    return [c.motif for c in biffageops.detecte_identites(texte)
            if c.categorie == "PERSONNE"]


class UN_PATRONYME_COURT_TOMBE_COMME_LES_AUTRES(unittest.TestCase):
    """**Le defaut repare, et il frappait une classe entiere de noms.**"""

    def test_un_patronyme_de_trois_lettres_voit_ses_occurrences_tomber(self) -> None:
        for nom in ("KIM", "NGO", "BUI", "DUC"):
            with self.subTest(nom=nom):
                self.assertIn(
                    "nom_nu", _motifs(nom),
                    "ce patronyme est etabli par une civilite et ses "
                    "occurrences isolees restent en clair")

    def test_les_patronymes_longs_tombent_toujours(self) -> None:
        """Temoin de non-regression: retirer le seuil ne devait rien casser."""
        for nom in ("VANDERSTOCKE", "DUPONT"):
            with self.subTest(nom=nom):
                self.assertIn("nom_nu", _motifs(nom))


class LE_LEXIQUE_RESTE_LA_SEULE_BORNE(unittest.TestCase):
    """**Une notion, un endroit** - le principe de la journee entiere."""

    def test_les_mots_courants_courts_restent_refuses(self) -> None:
        """Ce sont eux que le seuil pretendait proteger; le lexique les
        refusait deja."""
        for mot in ("RUE", "TVA", "LOT", "EUR", "TTC", "HT"):
            with self.subTest(mot=mot):
                self.assertFalse(biffageops._nom_recevable(mot))

    def test_les_tokens_de_deux_lettres_restent_exclus_SANS_le_seuil(self) -> None:
        """`_nom_recevable` impose deja trois caracteres: le seuil de quatre
        n'ajoutait rien de ce cote."""
        for mot in ("LI", "WU"):
            with self.subTest(mot=mot):
                self.assertFalse(biffageops._nom_recevable(mot))
                self.assertNotIn("nom_nu", _motifs(mot))

    def test_la_fonction_ne_porte_plus_de_seuil_de_longueur(self) -> None:
        """**La garde d'axe.** Un seuil de longueur reintroduit ici exclurait a
        nouveau des patronymes que le lexique accepte."""
        source = MODULE.read_text(encoding="utf-8")
        corps = source[source.index("def _noms_nus("):]
        corps = corps[:corps.index("\ndef ")]
        lignes = [l for l in corps.splitlines()
                  if not l.lstrip().startswith("#")]
        fautives = [l for l in lignes if re.search(r"len\(token\)\s*<\s*\d", l)]
        self.assertEqual(
            [], fautives,
            "un seuil de longueur est revenu dans `_noms_nus`: c'est "
            "exactement ce que `RM-2026-0097` interdit, et il exclut des "
            "patronymes que `_nom_recevable` accepte")


class LA_CONDITION_DE_CONTEXTE_EST_INTACTE(unittest.TestCase):
    """**Ce que le lot ne devait PAS relacher.**

    `_noms_nus` n'ouvre le masquage generalise qu'a un nom *vu accompagne
    ailleurs*. Retirer le seuil de longueur ne devait pas toucher a cette
    condition - c'est elle qui empeche qu'une forme repetee devienne un
    remplacement dans tout le document, mecanisme de l'incident du 2026-09-03.
    """

    def test_un_mot_jamais_accompagne_ne_devient_pas_un_nom(self) -> None:
        texte = "La resolution PORTE sur le ravalement. PORTE est adoptee.\n"
        motifs = [c.motif for c in biffageops.detecte_identites(texte)
                  if c.categorie == "PERSONNE"]
        self.assertNotIn("nom_nu", motifs)

    def test_les_motifs_sans_appui_lexical_restent_ecartes(self) -> None:
        self.assertIn("colonne_nominative", biffageops.MOTIFS_SANS_APPUI_LEXICAL)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
