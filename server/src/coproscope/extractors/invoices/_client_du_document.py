# -*- coding: utf-8 -*-
"""Ce qui, sur une facture, ne peut pas etre le fournisseur.

**Le defaut corrige le 2026-09-08, et il y en avait deux dans la meme ligne.**
La liste des fragments de rejet portait deux litteraux: **le nom reel d'une
copropriete et celui d'un cabinet**, ecrits en dur dans une regle metier. Ils ne
sont pas recopies ici - une docstring qui explique le retrait d'un nom en le
citant n'a rien retire du tout, et c'est exactement l'erreur que ce fichier a
faite dans sa premiere version.

1. **Une fuite.** Ces deux mots partaient sur GitHub avec le code.
2. **Une modalite codee, et c'est le defaut le plus couteux des deux.** La
   regle vraie est *le CLIENT d'une facture n'en est pas le FOURNISSEUR*.
   Ecrire le nom d'un client particulier ne code pas cette regle: cela code
   **deux clients rencontres**. Une troisieme copropriete voit son propre nom
   accepte comme fournisseur, **sans aucun signal** - une reponse fausse en
   silence, exactement le cas que le test d'acceptation du depot interdit.

**L'axe.** Ce qui varie d'une copropriete a l'autre, c'est **sa designation**.
Ce qui reste invariant tout le long de cet axe, c'est que cette designation,
quelle qu'elle soit, **figure sur ses factures en qualite de destinataire**.
La designation se lit donc dans l'instance, la ou elle est declaree, et jamais
dans le code.

**Ce qui reste legitimement en dur.** Le vocabulaire de FORME d'une facture -
`designation`, `total ht`, `conditions de paiement`, `syndicat` - n'est pas une
modalite: c'est la langue du document commercial, la meme chez tous les
emetteurs. Elle ne depend d'aucune copropriete.

**Degradation hors des valeurs observees.** Une instance qui ne declare aucune
designation n'ajoute aucun fragment: l'extracteur se comporte alors comme s'il
ne connaissait pas son client - ce qui est vrai, et vrai pour TOUTES les
coproprietes de la meme facon. C'est moins bon que de le savoir, mais c'est
uniforme et cela se voit, au lieu de marcher pour deux coproprietes et
d'echouer en silence pour les autres.
"""

from __future__ import annotations

import unicodedata
from typing import Iterable

__all__ = [
    "FRAGMENTS_DE_FORME",
    "designations_declarees",
    "fragments_de_rejet",
    "normalise_pour_comparaison",
]

#: Le vocabulaire de FORME d'une facture. Aucun de ces fragments ne designe une
#: partie: ils nomment des rubriques, des totaux et des mentions legales, donc
#: ils sont les memes chez tous les emetteurs.
FRAGMENTS_DE_FORME: tuple[str, ...] = (
    "designation",
    "quantite",
    "prix uni",
    "montant ht",
    "total ht",
    "total ttc",
    "total tva",
    "net a payer",
    "net à payer",
    "echeance",
    "échéance",
    "reglement",
    "règlement",
    "comptant",
    "date des travaux",
    "bon de commande",
    "logement",
    "payer en ligne",
    "nos references",
    "vos references",
    "numero de contrat",
    "numero de facture",
    "sdc ",
    "syndicat",
    "client",
    # `RM-2026-0151`, 2026-09-12: `immobilier` etait ici et n'y avait pas
    # sa place. Ce n'est pas un mot de FORME - il ne nomme ni rubrique ni
    # total - c'est un mot de PARTIE, et il figure parmi les marqueurs de
    # personne morale du depot. Mesure par le point d'entree: deux factures
    # identiques, seul le nom du fournisseur change, et celle qui porte
    # `AGENCE IMMOBILIERE DU PARC` rend un fournisseur VIDE quand l'autre
    # rend le sien. Une classe entiere de fournisseurs disparaissait.
    "installation de chantier",
    "modes de paiement",
    "conditions de paiement",
    "objet",
    "adresse du chantier",
    "capital",
    "sage",
    "www.",
)


def normalise_pour_comparaison(valeur: str) -> str:
    """Meme normalisation que celle appliquee aux lignes de la facture.

    Une designation comparee autrement que la ligne ne se retrouverait jamais:
    accents, casse et espaces insecables doivent tomber des deux cotes.
    """
    texte = str(valeur or "").replace(chr(0x00A0), " ").replace(chr(0x202F), " ")
    texte = unicodedata.normalize("NFKD", unicodedata.normalize("NFKC", texte).strip()).lower()
    return "".join(c for c in texte if not unicodedata.combining(c)).strip()


#: Une designation trop courte rejetterait des fournisseurs legitimes: `SCI`,
#: `EDF` ou `Le Parc` apparaissent partout. La borne porte sur la longueur du
#: fragment, pas sur son contenu, donc elle ne connait aucun nom.
LONGUEUR_MINIMALE = 6


def designations_declarees(payload: object) -> tuple[str, ...]:
    """Les designations que l'instance declare pour elle-meme.

    Lues, jamais devinees: le nom d'affichage de l'instance, plus les variantes
    que la configuration ajoute sous `settings.factures.designations_du_client`
    - une copropriete peut apparaitre sur ses factures sous plusieurs libelles,
    et c'est a elle de les nommer.
    """
    valeurs: list[str] = []
    nom = getattr(payload, "display_name", "")
    if isinstance(nom, str):
        valeurs.append(nom)
    brut = getattr(payload, "payload", None)
    if isinstance(brut, dict):
        reglages = brut.get("settings")
        if isinstance(reglages, dict):
            factures = reglages.get("factures")
            if isinstance(factures, dict):
                declarees = factures.get("designations_du_client")
                if isinstance(declarees, (list, tuple)):
                    valeurs.extend(str(v) for v in declarees)
    retenues: list[str] = []
    for valeur in valeurs:
        fragment = normalise_pour_comparaison(valeur)
        if len(fragment) >= LONGUEUR_MINIMALE and fragment not in retenues:
            retenues.append(fragment)
    return tuple(retenues)


def fragments_de_rejet(designations_du_client: Iterable[str] = ()) -> list[str]:
    """Le vocabulaire de forme, augmente des designations du client lues.

    L'ordre n'a pas d'importance: l'appelant teste une appartenance de
    sous-chaine. Les designations sont normalisees ici pour que l'appelant
    n'ait pas a savoir comment la comparaison se fait.
    """
    fragments = list(FRAGMENTS_DE_FORME)
    for valeur in designations_du_client:
        fragment = normalise_pour_comparaison(valeur)
        if len(fragment) >= LONGUEUR_MINIMALE and fragment not in fragments:
            fragments.append(fragment)
    return fragments
