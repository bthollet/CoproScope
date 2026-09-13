# -*- coding: utf-8 -*-
"""Un chantier cite par le gouvernail designe quelque chose.

`RM-2026-0070`. **Le predicat, enonce avant tout instrument:** pour toute ligne
du registre actif du gouvernail, tout identifiant de chantier `CH-*` cite dans
N'IMPORTE QUELLE cellule apparait dans au moins un registre de coordination du
depot. Sinon la citation ne designe rien, et une preuve ou un renvoi qui s'y
appuie ne peut pas etre suivi.

----------------------------------------------------------------------
Ce que cette garde a trouve LE JOUR DE SA CREATION, et c'est son argument
----------------------------------------------------------------------

**40 citations orphelines, 38 identifiants distincts. 23 d'entre eux ont ete
ecrits le jour meme, par le passage qui ecrit cette garde**, dans le commit
`dae3aff` (2026-09-12 19:36) intitule *un chantier ne s'invente pas, il se
derive de git: la dette des 25 est videe*.

Ce commit vidait la dette de `test_une_preuve_livree_suppose_un_chantier.py`,
qui demande qu'une preuve livree cite un chantier. Il l'a videe **en derivant
des identifiants de l'horodatage des commits** - et aucun de ces identifiants
n'existe dans un registre de coordination. La garde voisine a donc ete
satisfaite par une citation, pas par un chantier: **la dette est tombee a zero
sans qu'un defaut bouge**, la faute exacte que ce depot nomme *un proxy de garde
se satisfait sans rien reparer*. Le titre du commit disait qu'un chantier ne
s'invente pas; un identifiant qui ne designe rien, vu du registre, est invente.

**Et ce passage en a d'abord EFFACE deux sans les resoudre.** Ses scripts de
cellule du soir ecrivaient la colonne `Chantiers lies` par REMPLACEMENT au lieu
d'y ajouter. Sur `RM-2026-0137` et `RM-2026-0139`, ils ont ecrase un identifiant
forge par `dae3aff` avec la phrase qui en disait la provenance; sur
`RM-2026-0171`, quatre renvois `RM-*`. Le compte de la garde est donc d'abord
sorti a 21 forges au lieu de 23: **deux orphelins avaient quitte la mesure par
suppression, pas par resolution**. Les quatre cellules ont ete restaurees a
l'identique depuis git, le chantier du lot ajoute a la suite.

Le meme passage a ecrit quatre autres identifiants orphelins dans ses propres
lots de la soiree. Ceux-la sont **resolus**, par quatre lignes de presence
reelles - ils designent des chantiers menes et commites. Les 23 ne le sont
pas, et c'est voulu: leur ecrire une ligne de presence apres coup serait
satisfaire CETTE garde par le meme geste que celui qu'elle denonce.

----------------------------------------------------------------------
Les quatre corrections du sceptique, toutes appliquees
----------------------------------------------------------------------

La proposition d'origine a ete eprouvee par un agent charge de la detruire. Il
a rejoue l'algorithme a la main et trouve deux defauts deja effectifs:

1. **Une declaration bornee par une FENETRE DE CARACTERES traverse la barre.**
   Avec `VOISINAGE = 200`, la citation de `RM-2026-0071` etait exemptee par un
   mot du nom d'instance ecrit dans la cellule VOISINE, un caractere apres
   elle. Cette garde n'a donc **aucune fenetre**: elle ne lit pas de
   declaration en prose du tout. Une explication ecrite a cote d'une citation
   ne la fait pas designer quelque chose; seule une ligne de registre le fait.
2. **Les citations se lisent sur TOUTE la ligne, pas sur la seule colonne
   `Chantiers lies`.** Six citations orphelines vivaient dans
   `Preuve/livrable` - une preuve qui repose sur un identifiant qui ne designe
   rien - et une garde limitee a une colonne ne les voyait pas.
3. **Un registre se reconnait par sa FORME de registre**: une ligne d'en-tete
   portant `Chantier` ET `Statut`. Le seul mot `Chantier` retenait trois tables
   d'archive ou il nomme un travail en prose.
4. **Un identifiant sans aucun chiffre est un gabarit**, pas un chantier. Critere
   de forme, pas liste de gabarits.

Et une cinquieme, qui vient du depot: **la colonne est prise par son NOM dans
l'en-tete, jamais par son index.**

----------------------------------------------------------------------
Quand cette garde cessera d'etre vraie, comment l'apprendra-t-on ?
----------------------------------------------------------------------

Par elle. Une citation nouvelle qui ne designe rien fait echouer
`test_aucune_citation_NOUVELLE_...` en la nommant. Une citation de la dette qui
se met a designer quelque chose fait echouer `test_la_dette_ne_porte_...`: la
dette doit rapetisser par un geste ecrit, jamais en silence. Et si la
decouverte des registres, l'extraction des citations ou la lecture du
gouvernail tombent a vide, un temoin de sante echoue au lieu de laisser un vert
parfait.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests import _chantier_cite as C

DETTE_2026_09_12: dict[str, frozenset[tuple[str, str]]] = {
    'Chantiers lies': frozenset({
        # FORGES PAR dae3aff (2026-09-12 19:36), ce passage-ci: derives de
        # l'horodatage des commits pour vider la dette d'une AUTRE garde, et
        # presents dans AUCUN registre de coordination. Voir l'en-tete.
        ('RM-2026-0061', 'CH-20260912-093546-RM-2026-0061-estampille-provenance-ecriture-que'),
        ('RM-2026-0067', 'CH-20260912-055504-RM-2026-0067-rappro-action-sans-repli'),
        ('RM-2026-0080', 'CH-20260912-083244-RM-2026-0080-une-assemblee-isolee-sans'),
        ('RM-2026-0092', 'CH-20260912-185516-RM-2026-0092-consolider-entre-coproprietaires-historique'),
        ('RM-2026-0093', 'CH-20260912-185516-RM-2026-0093-distinguer-une-piece-servie'),
        ('RM-2026-0094', 'CH-20260912-080200-RM-2026-0094-porter-les-cinq-annexes'),
        ('RM-2026-0097', 'CH-20260912-044229-RM-2026-0097-deux-extracteurs-personnes-codent'),
        ('RM-2026-0098', 'CH-20260912-045404-RM-2026-0098-derive-pseudonymise-dit-pas'),
        ('RM-2026-0107', 'CH-20260912-115340-RM-2026-0107-une-execution-tests-peut'),
        ('RM-2026-0115', 'CH-20260912-074809-RM-2026-0115-les-accents-manquent-dans'),
        ('RM-2026-0116', 'CH-20260912-021115-RM-2026-0116-sais-pas-est-traite'),
        ('RM-2026-0118', 'CH-20260912-101506-RM-2026-0118-grille-semiotique-controle-gouvernance'),
        ('RM-2026-0129', 'CH-20260912-111208-RM-2026-0129-lire-issue-vote-par'),
        ('RM-2026-0134', 'CH-20260912-085913-RM-2026-0134-sept-montants-franchissent-encore'),
        ('RM-2026-0135', 'CH-20260912-121103-RM-2026-0135-corpus-facture-compte-deux'),
        ('RM-2026-0137', 'CH-20260912-185516-RM-2026-0137-zero-donnee-personnelle-sur'),
        ('RM-2026-0139', 'CH-20260912-094743-RM-2026-0139-gouvernail-est-source-verite'),
        ('RM-2026-0143', 'CH-20260912-060637-RM-2026-0143-une-absence-mesure-une'),
        ('RM-2026-0147', 'CH-20260912-114217-RM-2026-0147-une-copie-caviardee-dit'),
        ('RM-2026-0151', 'CH-20260912-072135-RM-2026-0151-vocabulaire-forme-des-factures'),
        ('RM-2026-0168', 'CH-20260912-112430-RM-2026-0168-connecteur-navigateur-sait-lire'),
        ('RM-2026-0174', 'CH-20260912-052049-RM-2026-0174-test-ecran-drive-echoue'),
        ('RM-2026-0175', 'CH-20260912-001056-RM-2026-0175-controle-confidentialite-rendait-son'),
        # Historiques, anterieurs a ce passage.
        ('RM-2026-0052', 'CH-20260903-0930-RM-2026-0052-defauts-page-gouvernance'),
        ('RM-2026-0068', 'CH-20260904-0500-RM-2026-0068-sous-detection-patronymes'),
        ('RM-2026-0070', 'CH-20260904-1000-RM-2026-0070-synthese-gouvernance'),
        ('RM-2026-0071', 'CH-20260904-1000-RM-2026-0071-instance-reconstruite'),
        ('RM-2026-0122', 'CH-20260908-0100-RM-2026-0122-etiquette-nature-donnees'),
        ('RM-2026-0128', 'CH-20260908-1130-RM-2026-0128-priorites-et-liens-gouvernail'),
        ('RM-2026-0141', 'CH-20260908-1800-RM-2026-0141-retours-carte-annee'),
        ('RM-2026-0142', 'CH-20260908-1830-RM-2026-0142-doctrine-sans-instance-figee'),
        ('RM-2026-0145', 'CH-20260908-1420-RM-2026-0145-coffre-contient-tout'),
        ('RM-2026-0149', 'CH-20260908-2200-RM-2026-0149-menage-instances'),
        ('RM-2026-0157', 'CH-20260909-2200-RM-2026-0157-citation-ouvre-sa-piece'),
    }),
    'Preuve/livrable': frozenset({
        # Historiques, anterieurs a ce passage.
        ('RM-2026-0058', 'CH-20260908-1200-RM-2026-0074-voie-factures'),
        ('RM-2026-0059', 'CH-20260908-1400-RM-2026-0059-garde-ecrans-sans-canal'),
        ('RM-2026-0074', 'CH-20260908-1200-RM-2026-0074-voie-factures'),
        ('RM-2026-0075', 'CH-20260908-1200-RM-2026-0074-voie-factures'),
        ('RM-2026-0110', 'CH-20260908-1200-RM-2026-0110-cloture-resolution-axe'),
        ('RM-2026-0126', 'CH-20260908-1130-RM-2026-0126-poc-monoutilisateur-pseudonymisation'),
    }),
}


#: Les chantiers FORGES par dae3aff, a part: la raison de ce fichier.
FORGES_PAR_DAE3AFF = frozenset(
    ch for couples in DETTE_2026_09_12.values() for _, ch in couples
    if ch.startswith("CH-20260912-")
)


class AUCUNE_CITATION_DE_CHANTIER_NE_DESIGNE_RIEN(unittest.TestCase):
    """Le predicat, table par table - une colonne n'a pas le cout d'une autre."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.orphelines = C.citations_orphelines()

    def test_aucune_citation_NOUVELLE_ne_designe_rien(self) -> None:
        nouvelles = {
            nom: sorted(couples - DETTE_2026_09_12.get(nom, frozenset()))
            for nom, couples in self.orphelines.items()
        }
        nouvelles = {nom: c for nom, c in nouvelles.items() if c}
        self.assertEqual(
            {}, nouvelles,
            "des chantiers sont cites sans apparaitre dans AUCUN registre de "
            "coordination - la citation ne designe rien. Ecrire la ligne de "
            "presence du chantier reellement mene; ne pas deriver un "
            "identifiant pour satisfaire une garde, c'est le geste que ce "
            "fichier existe pour denoncer: %r" % nouvelles)

    def test_la_dette_ne_porte_pas_de_citation_deja_RESOLUE(self) -> None:
        """La dette rapetisse par un geste ecrit, jamais en silence.

        **Et une citation qui sort de la dette n'est pas forcement resolue: elle
        peut avoir DISPARU.** C'est arrive le jour de la creation de cette garde:
        des scripts de cellule qui ecrivaient `Chantiers lies` par remplacement
        ont efface deux identifiants de la dette, qui ont quitte la mesure par
        suppression. Les deux cas se disent donc separement - une resolution se
        retire de la dette, une suppression se restaure.
        """
        _, items = C.lignes_d_item()
        textes = {m[1].strip("`"): " ".join(m) for m in items}
        resolues, disparues = {}, {}
        for nom, couples in DETTE_2026_09_12.items():
            for rm, ch in sorted(couples - self.orphelines.get(nom, frozenset())):
                if ch in textes.get(rm, ""):
                    resolues.setdefault(nom, []).append((rm, ch))
                else:
                    disparues.setdefault(nom, []).append((rm, ch))
        self.assertEqual(
            {}, disparues,
            "ces citations de la dette ont DISPARU de leur ligne: ce n'est pas "
            "une resolution, c'est une suppression. Restaurer la cellule depuis "
            "git - un identifiant efface quitte la mesure sans que rien ne soit "
            "repare: %r" % disparues)
        self.assertEqual(
            {}, resolues,
            "ces citations de la dette designent desormais quelque chose: les "
            "retirer de `DETTE_2026_09_12`, sinon la dette ment sur ce qu'il "
            "reste a faire: %r" % resolues)

    def test_les_23_identifiants_FORGES_restent_nommes_a_part(self) -> None:
        """L'argument de ce fichier ne doit pas se dissoudre dans la dette."""
        self.assertEqual(23, len(FORGES_PAR_DAE3AFF),
                         "le compte des identifiants forges par dae3aff a "
                         "change: si certains sont resolus, le dire en tete")


class LES_TEMOINS_SANS_LESQUELS_CETTE_GARDE_MESURERAIT_LE_VIDE(unittest.TestCase):
    """Cette garde peut mesurer le vide de trois cotes independants."""

    def _cites(self) -> set[str]:
        _, items = C.lignes_d_item()
        cites: set[str] = set()
        for morceaux in items:
            for cellule in morceaux:
                cites |= C.chantiers_de(cellule)
        return cites

    def test_le_gouvernail_est_lu_et_peuple(self) -> None:
        entete, items = C.lignes_d_item()
        self.assertGreater(len(items), 100, "section du gouvernail introuvable "
                                            "ou renommee: zero ligne lue")
        self.assertIn("Chantiers lies", entete)
        self.assertIn("Preuve/livrable", entete)

    def test_le_motif_de_citation_MORD_encore(self) -> None:
        self.assertGreater(len(self._cites()), 100,
                           "le motif ne reconnait presque plus aucun chantier: "
                           "le vocabulaire a change")

    def test_la_decouverte_des_registres_TROUVE_la_table_de_presence(self) -> None:
        """Le temoin central: une decouverte vide ferait tout accuser."""
        registres = C.registres_de_coordination()
        self.assertIn("docs/presence_agents.md", registres)
        self.assertGreater(len(set().union(*registres.values())), 100)

    def test_l_instrument_DISCRIMINE(self) -> None:
        """Un 0/N comme un N/N est un symptome d'instrument, pas un resultat."""
        cites = self._cites()
        orphelins = {ch for couples in C.citations_orphelines().values()
                     for _, ch in couples}
        self.assertLess(0, len(cites - orphelins),
                        "aucune citation ne se resout: la decouverte est cassee")
        self.assertLess(0, len(orphelins),
                        "toutes les citations se resolvent alors que la dette "
                        "en nomme: l'instrument ne voit plus")

    def test_un_gabarit_sans_chiffre_n_est_pas_un_chantier(self) -> None:
        self.assertEqual(set(), C.chantiers_de("format `CH-YYYY-NNNN` en prose"))
        self.assertEqual({"CH-2026-0042"}, C.chantiers_de("voir `CH-2026-0042`"))


class LA_DECOUVERTE_SE_FAIT_PAR_LA_FORME_ET_NON_PAR_LE_NOM(unittest.TestCase):
    """Eprouve sur une arborescence FABRIQUEE, ou la reponse est connue."""

    RESOLU = "CH-20260101-000000-RM-2026-9001-resolu"
    ORPHELIN = "CH-20260101-000000-RM-2026-9002-orphelin"
    PREUVE = "CH-20260101-000000-RM-2026-9002-preuve-orpheline"

    def _arbre(self, dossier: Path) -> tuple[Path, Path]:
        docs = dossier / "docs"
        (docs / "sous" / "dossier").mkdir(parents=True)
        gouvernail = docs / "gouvernail.md"
        gouvernail.write_text("\n".join([
            "## Registre actif par identifiant",
            "",
            "| ID | Titre | Chantiers lies | Preuve/livrable |",
            "|---|---|---|---|",
            "| `RM-2026-9001` | x | `%s` | - |" % self.RESOLU,
            "| `RM-2026-9002` | y | `%s` | `%s` |" % (self.ORPHELIN, self.PREUVE),
            "",
        ]), encoding="utf-8")
        # Un registre qu'AUCUN nom ne designe, range ou personne ne le cherche.
        (docs / "sous" / "dossier" / "un_nom_quelconque.md").write_text("\n".join([
            "| Conversation | Chantier | Statut |",
            "|---|---|---|",
            "| `CONV-X` | `%s` | `EN_COURS` |" % self.RESOLU,
            "",
        ]), encoding="utf-8")
        # Une table qui porte le mot Chantier SANS aucun etat de coordination.
        (docs / "archive_prose.md").write_text("\n".join([
            "| Chantier | Commentaire |",
            "|---|---|",
            "| `%s` | cite en prose |" % self.ORPHELIN,
            "",
        ]), encoding="utf-8")
        return docs, gouvernail

    def _table(self) -> dict:
        with tempfile.TemporaryDirectory() as brut:
            docs, gouvernail = self._arbre(Path(brut))
            return C.citations_orphelines(gouvernail, docs)

    def test_un_registre_que_rien_ne_nomme_est_LU_le_jour_de_sa_creation(self) -> None:
        tout = {ch for couples in self._table().values() for _, ch in couples}
        self.assertNotIn(self.RESOLU, tout,
                         "un registre range sous un nom et un dossier "
                         "quelconques n'est pas lu: la portee vient d'un nom")

    def test_une_table_SANS_statut_ne_resout_rien(self) -> None:
        self.assertIn(("RM-2026-9002", self.ORPHELIN),
                      self._table().get("Chantiers lies", frozenset()),
                      "une table d'archive qui cite un chantier en prose a "
                      "suffi a le resoudre: le mot Chantier ne fait pas un "
                      "registre")

    def test_une_citation_dans_la_PREUVE_est_mesuree_aussi(self) -> None:
        self.assertIn(("RM-2026-9002", self.PREUVE),
                      self._table().get("Preuve/livrable", frozenset()),
                      "la colonne Preuve n'est pas lue: une preuve qui repose "
                      "sur un identifiant qui ne designe rien passerait")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
