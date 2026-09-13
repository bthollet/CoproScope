# -*- coding: utf-8 -*-
"""Le vocabulaire de FORME d'une facture ne nomme jamais une PARTIE.

`RM-2026-0151`. L'item disait le defaut corrige et **sa recurrence non
corrigee**: `FRAGMENTS_DE_FORME` avait porte le nom reel d'une copropriete et
celui d'un cabinet - *le CLIENT d'une facture n'en est pas le FOURNISSEUR*
code comme **deux clients rencontres**. Les litteraux sont partis, la
designation du client se lit dans l'instance, et l'item concluait: *rien de
STRUCTUREL n'empeche un lot futur d'ajouter un nom de client a ce
vocabulaire*.

**LA PROPRIETE QUE L'ITEM NOMMAIT N'EST PAS MESURABLE EN CI, ET C'EST VRAI.**
Elle disait: *un fragment de forme apparait chez TOUS les emetteurs, un nom de
client chez un seul*. Cela demande un corpus de factures de plusieurs
emetteurs; la CI n'a pas le droit de lire une instance privee, et le corpus
public `examples/synthetic_copro` ne porte **qu'une seule facture**. Mesure du
2026-09-12, et elle confirme la reserve de l'item.

**MAIS UNE AUTRE PROPRIETE L'EST, et elle attrape le meme defaut.** Un mot de
FORME nomme une rubrique, un total, une mention legale. Un mot de PARTIE porte
une **forme juridique ou un mot de raison sociale** - `SCI`, `SARL`,
`CABINET`, `AGENCE`, `IMMOBILIER`. Le depot tient deja cette liste, pour le
biffage, sous `MARQUEURS_PERSONNE_MORALE`: la garde la reutilise au lieu d'en
ecrire une seconde.

**ET LA GARDE A MORDU LE JOUR OU ELLE A ETE ECRITE.** `immobilier` figurait
dans le vocabulaire de forme. Mesure par le point d'entree
`extract_generic_invoice_fields`, deux factures identiques dont seul le nom du
fournisseur change:

- `AGENCE IMMOBILIERE DU PARC` -> fournisseur **vide**;
- `ENTRETIEN DES JARDINS DU PARC` -> fournisseur **trouve**.

**Une classe entiere de fournisseurs disparaissait en silence** - agences et
societes immobilieres - et c'est bien le defaut que l'item decrit, a l'envers:
non pas un nom de client precis, mais un mot de partie promu mot de forme.
`immobilier` est retire; le client, lui, continue d'etre rejete par les
designations que l'instance declare, ce que le dernier test verifie.

**L'AXE.** Ce qui VARIE: les emetteurs, leurs raisons sociales, la mise en
page de leurs factures. Ce qui reste INVARIANT: **un mot qui decrit la facture
ne peut pas etre un mot qui designe une partie**, et une raison sociale se
reconnait a sa forme juridique, pas a sa presence dans une liste de clients
rencontres. **Hors des valeurs observees:** un cabinet inconnu portant `SCPI`
ou `GIE` dans son nom est protege le jour ou il arrive, sans que personne
ajoute rien.
"""
from __future__ import annotations

import importlib
import unittest

CLIENT = importlib.import_module(
    "coproscope.extractors.invoices._client_du_document")
BIFFAGE = importlib.import_module("coproscope.modules.biffageops")
BASE = importlib.import_module("coproscope.extractors.invoices.base")

#: Le vocabulaire arrete au 2026-09-12. **Ce n'est pas une copie defensive:
#: c'est l'obstacle structurel que l'item reclamait.** Toute croissance fait
#: echouer le test, avec le message qui dit ce qu'il faut prouver avant de
#: l'accepter.
VOCABULAIRE_ARRETE = 33


def _facture(fournisseur: str) -> str:
    return (
        f"{fournisseur}\n"
        "12 rue des Lilas\n"
        "Facture n. F-2025-118\n"
        "Designation   Quantite   Prix uni   Montant HT\n"
        "Gestion locative   1   500,00   500,00\n"
        "Total TTC   600,00\n"
    )


class UN_MOT_DE_FORME_NE_PORTE_PAS_DE_FORME_JURIDIQUE(unittest.TestCase):
    """La propriete mesurable en CI, a defaut de celle qui demande un corpus."""

    def test_aucun_fragment_ne_nomme_une_partie(self) -> None:
        marqueurs = BIFFAGE.MARQUEURS_PERSONNE_MORALE
        fautifs = [
            (fragment, jeton)
            for fragment in CLIENT.FRAGMENTS_DE_FORME
            for jeton in fragment.upper().split()
            if jeton in marqueurs
        ]
        self.assertEqual(
            [], fautifs,
            "ce fragment porte un marqueur de personne morale: c'est un mot de "
            "PARTIE, pas un mot de FORME. Il fera disparaitre tout fournisseur "
            "dont la raison sociale le contient. Si le besoin est de rejeter le "
            "CLIENT, la designation du client se declare dans l'instance sous "
            "`settings.factures.designations_du_client`. Fautifs: %s" % fautifs)

    def test_l_instrument_a_de_quoi_mordre(self) -> None:
        """Sans marqueurs ni fragments, le test ci-dessus passerait a vide."""
        self.assertGreater(len(BIFFAGE.MARQUEURS_PERSONNE_MORALE), 10)
        self.assertGreater(len(CLIENT.FRAGMENTS_DE_FORME), 20)

    def test_le_vocabulaire_est_arrete_et_toute_croissance_se_justifie(self) -> None:
        """L'obstacle structurel que l'item reclamait.

        La propriete vraie - *un fragment de forme apparait chez tous les
        emetteurs* - ne se mesure pas en CI. A defaut, le vocabulaire est
        **arrete**: on ne l'agrandit pas sans le dire.
        """
        self.assertEqual(
            VOCABULAIRE_ARRETE, len(CLIENT.FRAGMENTS_DE_FORME),
            "le vocabulaire de forme a change de taille. Avant d'ajouter un "
            "fragment, prouver sur un corpus de PLUSIEURS emetteurs qu'il "
            "apparait chez tous - c'est ce qui distingue un mot de forme d'un "
            "nom rencontre une fois. Cette mesure ne se fait pas en CI, qui "
            "n'a pas le droit de lire une instance privee: elle se fait dans "
            "le lot, et son resultat s'ecrit dans le gouvernail. Puis mettre "
            "ce compte a jour, avec la date.")


class LA_DISTINCTION_TIENT_PAR_LE_POINT_D_ENTREE(unittest.TestCase):
    """Le temoin de comportement: la garde ci-dessus protege quelque chose."""

    def test_un_fournisseur_immobilier_est_trouve(self) -> None:
        trouve = BASE.extract_generic_invoice_fields(
            _facture("AGENCE IMMOBILIERE DU PARC"), "f.pdf").fournisseur
        self.assertEqual("AGENCE IMMOBILIERE DU PARC", trouve)

    def test_un_fournisseur_quelconque_l_est_aussi(self) -> None:
        """Temoin: sans lui, le test precedent ne dirait pas d'ou vient l'effet."""
        trouve = BASE.extract_generic_invoice_fields(
            _facture("ENTRETIEN DES JARDINS DU PARC"), "f.pdf").fournisseur
        self.assertEqual("ENTRETIEN DES JARDINS DU PARC", trouve)

    def test_le_CLIENT_declare_reste_rejete(self) -> None:
        """Conservation: retirer un mot de partie ne rend pas le client visible.

        C'est le coeur de l'item - *le client d'une facture n'en est pas le
        fournisseur* - et il tient par ce que l'instance DECLARE, jamais par
        un mot grave dans le code.
        """
        nom = "SDC RESIDENCE IMMOBILIERE DU PARC"
        trouve = BASE.extract_generic_invoice_fields(
            _facture(nom), "f.pdf", (nom,)).fournisseur
        self.assertEqual("", trouve)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
