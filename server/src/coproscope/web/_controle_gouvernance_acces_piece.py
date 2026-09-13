# -*- coding: utf-8 -*-
"""Ce qu'une cellule NOMME devient un chemin - et ce que ce chemin montrera.

Instruction de `RM-2026-0157`, et les mots de Brice: *« si je clique sur le
titre de la piece, et ca DANS TOUTES LES CELLULES »*. Une cellule qui sait
nommer une piece sait quelle piece elle designe, et cette designation EST un
chemin.

**Deux proprietes independantes d'une piece, que l'ecran confondait.**
Jusqu'ici la citation ecrivait *« piece que le registre des convocations ne
nomme pas »* des que le `doc_id` manquait a la table des convocations. Un
lecteur y lit *on ne sait pas de quelle piece il s'agit*. C'est faux, et la
mesure le montre: sur le corpus du lot, **400 citations d'acte sur 786 sont
dans ce cas, et les 400 designent un document present au registre
documentaire** - le produit sait exactement quel fichier c'est, il ne sait
pas comment l'appeler.

Nommer et atteindre sont donc deux axes, et ils ne se recoupent pas:

- **nommable**: la table des convocations porte une date lisible pour ce
  document (`nommer_pieces`, ailleurs);
- **atteignable**: le registre documentaire porte une ligne pour ce `doc_id`,
  donc `/documents/<doc_id>` a quelque chose a ouvrir.

**Un troisieme axe, mesure et separe des deux premiers: ce que la destination
a le droit de MONTRER.** La fiche document refuse l'apercu d'une piece brute
tant que son arbitrage de biffage n'est pas fait - c'est
`document_viewer._guard_private_inbox`, et ce garde-fou a raison. Mesure du
2026-09-09 sur le corpus du lot: **les 13 documents que citent les 786
citations de l'ecran sont TOUS en zone brute avec un arbitrage de biffage non
tranche**, donc aucun ne montrera son PDF aujourd'hui. Un lien qui promettrait
*« ouvre la piece »* mentirait 786 fois sur 786.

Le lien existe quand meme, et c'est le choix de fond: une porte qui s'ouvre sur
*« voici la fiche de cette piece, et voici pourquoi son contenu reste
couvert »* n'est pas un chemin mort. Un chemin mort, c'est un lien qui ne dit
rien avant qu'on le suive.

**Ce que ce module ne fait pas, et le dit.** Il juge le REGISTRE, pas le
fichier: il ne l'ouvre pas, il ne verifie pas qu'il est encore la. Une fiche
dont le fichier a disparu s'ouvre et le declare elle-meme. Rendre ce verdict
exact couterait une lecture de disque par cellule, a chaque affichage de
l'ecran.
"""

from __future__ import annotations

from typing import Any, NamedTuple


#: La piece est au registre documentaire et sa fiche montrera son contenu.
OUVRABLE = "ouvrable"
#: La piece est au registre, sa fiche s'ouvre, et le contenu reste couvert par
#: l'arbitrage de biffage. Le lien vaut - la fiche porte le nombre de pages,
#: le type, l'origine - mais il ne faut rien promettre de plus.
RESERVE = "reserve"
#: Aucune ligne du registre documentaire ne porte ce `doc_id`. Il n'y a alors
#: aucun chemin a proposer, plutot qu'un chemin qui rendrait 404.
INCONNU = "inconnu"

#: Ce que le lecteur doit comprendre, par verdict. `OUVRABLE` n'a pas de
#: phrase: un lien qui marche n'a rien a expliquer.
MOTIFS = {
    RESERVE: (
        "La fiche de cette pièce s'ouvre ; son contenu reste couvert tant que "
        "l'arbitrage de biffage n'est pas tranché."
    ),
    INCONNU: (
        "Le contrôle désigne une pièce que le registre documentaire ne porte "
        "pas : il n'y a aucun document à ouvrir."
    ),
}


class Acces(NamedTuple):
    """Le verdict d'atteignabilite d'un document, et ce qu'il faut en dire."""

    verdict: str
    motif: str


def acces_aux_pieces(instance: Any) -> dict[str, Acces]:
    """Le verdict d'atteignabilite de chaque document du registre.

    Lu **une fois par affichage**, comme `nommer_pieces`, et pour la meme
    raison: une cellule ne doit pas ouvrir un registre, et 786 citations qui
    liraient chacune le leur donneraient 786 lectures du meme fichier.

    Un `doc_id` absent du dictionnaire rendu n'a **pas** d'entree, plutot
    qu'une entree `INCONNU`: l'appelant doit pouvoir distinguer *le registre
    ne connait pas cette piece* de *le registre n'a pas ete lu*, et les deux
    donneraient la meme valeur dans un dictionnaire qui comble ses trous.

    Un registre absent ou illisible rend donc `{}`, et **aucune citation ne
    porte alors de lien**: proposer un chemin sans savoir ce qu'il y a au bout
    reviendrait a envoyer chaque clic sur un 404, c'est-a-dire a fabriquer
    exactement le geste qui plante que ce lot corrige.
    """
    from ..core.common import read_csv
    from .document_viewer import _guard_private_inbox  # noqa: PLC0415

    try:
        chemin = instance.register("documents")
    except Exception:  # noqa: BLE001 - registre non declare: on n'invente pas.
        return {}
    try:
        if not chemin or not chemin.exists():
            return {}
        _, lignes = read_csv(chemin)
    except Exception:  # noqa: BLE001 - registre illisible: meme traitement.
        return {}

    verdicts: dict[str, Acces] = {}
    for ligne in lignes:
        doc_id = str(ligne.get("doc_id") or "").strip()
        if not doc_id:
            continue
        if _guard_private_inbox(ligne):
            verdicts[doc_id] = Acces(RESERVE, MOTIFS[RESERVE])
        else:
            verdicts[doc_id] = Acces(OUVRABLE, "")
    return verdicts


def chemin_de_piece(doc_id: str, page: str = "") -> str:
    """Le chemin d'une piece, a sa position quand la position est connue.

    **La position degrade le long de son axe, elle ne se reconstitue pas.**
    Une citation porte trois choses independantes - document, page, ancre - et
    chacune manque separement: mesure du 2026-09-09, 400 citations d'acte sur
    786 portent une ancre (`sous-point 11-1`) sans aucune page. Le chemin
    emporte donc la page quand elle existe, et rien de plus quand elle
    n'existe pas. Fabriquer `page=1` par defaut ferait passer une valeur par
    defaut pour une lecture.

    L'ancre n'entre pas dans le chemin: la fiche document ne sait pas
    aujourd'hui se placer sur un sous-point, et un parametre qu'elle ignorerait
    ferait croire a une precision qu'elle n'a pas.
    """
    identifiant = str(doc_id or "").strip()
    if not identifiant:
        return ""
    from urllib.parse import quote

    chemin = "/documents/" + quote(identifiant, safe="")
    numero = str(page or "").strip()
    return chemin + "?page=" + quote(numero, safe="") if numero else chemin


#: Les trois colonnes de l'ecran qui portent des bulles, donc des citations.
#:
#: **C'est une liste de MODALITES, et elle est declaree comme telle.** Une
#: quatrieme colonne a bulles ajoutee sans etre ajoutee ici ne ferait rien
#: rougir: son resume tomberait a zero en silence. La garde du lot recoupe donc
#: ce resume avec les citations reellement RENDUES par le gabarit, au lieu de
#: faire confiance a cette liste.
COLONNES_A_BULLES = ("fonde", "seuil", "execution")


def resumer_acces(lignes: list[dict[str, Any]], acces: dict[str, Acces]) -> dict[str, Any]:
    """Les pieces que l'ecran cite, et ce que leurs fiches montreront.

    **Dit UNE fois, jamais a chaque cellule.** Mesure du 2026-09-09 sur le
    corpus du lot: 621 citations rendues, et les pieces qu'elles designent
    partagent le meme verdict. Repeter la phrase sous chaque citation en aurait
    fait 621 copies d'un meme paragraphe - le motif repete a l'identique est
    l'un des defauts que ce produit mesure chez lui, et l'information utile
    n'est pas *cette piece est couverte* mais *treize pieces attendent un
    arbitrage*, qui est une tache.
    """
    citees: dict[str, str] = {}
    for ligne in lignes or ():
        for colonne in COLONNES_A_BULLES:
            for bulle in ligne.get(colonne) or ():
                for candidate in [bulle, *(bulle.get("sous") or ())]:
                    citation = candidate.get("citation") or {}
                    doc_id = str(citation.get("doc_id") or "").strip()
                    if not doc_id:
                        continue
                    verdict = acces.get(doc_id)
                    citees[doc_id] = verdict.verdict if verdict else INCONNU
    compte = {etat: sum(1 for v in citees.values() if v == etat)
              for etat in (OUVRABLE, RESERVE, INCONNU)}
    return {
        "citees": len(citees),
        "ouvrables": compte[OUVRABLE],
        "reserve": compte[RESERVE],
        "inconnues": compte[INCONNU],
        "phrase": _phrase_de_resume(len(citees), compte),
    }


def _phrase_de_resume(citees: int, compte: dict[str, int]) -> str:
    """Ce que le lecteur doit savoir des pieces citees, en une phrase ou rien.

    Rien quand il n'y a rien a signaler: une piece ouvrable n'appelle aucun
    commentaire, et une phrase qui se declenche toujours cesse d'etre lue.
    """
    if not citees or (not compte[RESERVE] and not compte[INCONNU]):
        return ""
    morceaux = []
    if compte[RESERVE]:
        n = compte[RESERVE]
        morceaux.append(
            f"{n} attendent un arbitrage de biffage : leurs fiches s'ouvrent, leur "
            "contenu reste couvert"
            if n > 1 else
            f"{n} attend un arbitrage de biffage : sa fiche s'ouvre, son contenu "
            "reste couvert"
        )
    if compte[INCONNU]:
        n = compte[INCONNU]
        morceaux.append(
            f"{n} ne figurent pas au registre documentaire : il n'y a aucun "
            "document à ouvrir"
            if n > 1 else
            f"{n} ne figure pas au registre documentaire : il n'y a aucun "
            "document à ouvrir"
        )
    return (
        f"Cet écran cite {citees} pièce{'s' if citees > 1 else ''}. "
        + " ; ".join(morceaux)
        + "."
    )
