"""Ce que le pont LIT: les registres deja ecrits, et le texte qui les a produits.

Le modele relationnel des actes existe depuis `7c2001a`, la typologie depuis
`83c79fb`, et rien n'ecrivait dedans. Mesure du 2026-09-04 sur les deux
instances locales: **173 resolutions au registre et 0 acte verse** pour l'une,
118 et 0 pour l'autre. L'ecran `/controle-gouvernance` rendait donc un etat
explicite "le modele relationnel n'a jamais ete alimente" au lieu du tableau.

Ce module est la moitie lecture du pont. Il ne fabrique aucune donnee: il prend
ce que les voies `resolutions` et `convocations` ont deja ecrit dans le MEME
fichier `gouvernance.sqlite3`, et il y ajoute la seule chose qu'aucune des deux
ne porte - **la portee**, c'est-a-dire le type d'acte au sens de
`_actes_typologie`.

----------------------------------------------------------------------
Pourquoi la portee se relit sur le texte, et pourquoi ce n'est pas une
seconde source de verite
----------------------------------------------------------------------

`portee_resolution` a besoin du SEGMENT de la resolution: la periode d'un
exercice, un montant, une fonction nommee par la loi peuvent tenir n'importe ou
dans le corps. Le registre `resolutions`, lui, ne stocke aucun texte integral -
volontairement: les proces-verbaux du corpus nomment environ cent vingt
coproprietaires avec leurs tantiemes et leur vote, et une colonne `texte` les
aurait aspires dans le magasin de gouvernance sans qu'aucun ecran ne le demande.

Le pont relit donc le document pour la seule portee, et **rien d'autre**. Tous
les faits - numero, issue, majorite, voix, dates de validite - viennent du
registre et de lui seul. Un fait ne peut donc pas prendre deux valeurs selon le
chemin: il n'y a qu'un chemin.

Quand le texte manque - document deplace, couche texte absente - la portee vaut
`ORDINAIRE`, c'est-a-dire **non determinee**, et tous les controles restent
appliques. C'est la degradation que la typologie prescrit deja: ne pas savoir
n'est pas une raison de classer sans suite.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..vault import gouvernance_store
from ._actes_schema import montant_texte
from ._montants import MontantIllisible
from ._actes_vocabulaire import (
    ETAT_CONSTATEE,
    ETAT_PROJETEE,
    MAJORITE_NON_ENONCEE,
    PORTEE_ORDINAIRE,
    RESULTAT_ADOPTEE,
    RESULTAT_ISSUE_NON_LUE,
    RESULTAT_PAS_DE_VOTE,
    RESULTAT_REJETEE,
    RESULTAT_SANS_ISSUE,
    RESULTAT_VOTE_SANS_FORMULE,
)
from ._resolutions_calibrage import _marqueurs
from ._resolutions_qualification import portee_resolution
from .lisibilite import texte_utile

# --------------------------------------------------------------------------
# Vocabulaires d'entree, traduits une seule fois
# --------------------------------------------------------------------------

#: Issue du registre `resolutions` -> issue du modele des actes.
#:
#: Les deux vocabulaires se recouvrent presque, et c'est voulu: la voie
#: resolutions et le modele partagent leurs mots depuis la conception. Deux
#: valeurs ne s'y trouvent pourtant pas, et les taire serait fabriquer un vote.
#:
#: - `SANS_OBJET`: le proces-verbal ecrit que la resolution est sans objet -
#:   aucun candidat a elire, rien a voter. Ce n'est ni une adoption ni un rejet;
#:   c'est une absence de vote que le document enonce, donc `PAS_DE_VOTE`.
#: - `REPORTEE`: l'assemblee a renvoye la question. Meme raisonnement.
#: - `PROJET`: une resolution seulement proposee n'a pas d'issue, et le modele
#:   le dit par `etat = PROJETEE`, pas par une issue inventee.
#: - `ISSUE_NON_RECONNUE` et `ISSUE_ENONCEE_NON_LUE`: le proces-verbal enonce
#:   une issue et la chaine ne sait pas la lire. Les deux etaient ABSENTS de
#:   cette table jusqu'au 2026-09-08 et retombaient sur le defaut
#:   `SANS_ISSUE_TRACEE`, c'est-a-dire sur `le document ne dit rien` - la seule
#:   phrase dont on soit sur qu'elle est fausse. Ils ont desormais leur valeur,
#:   et le defaut a change de sens (voir `issue_acte`).
#:
#: **Cette table doit rester TOTALE sur les etats d'issue de la voie
#: resolutions.** Rien dans le langage ne l'y oblige; c'est
#: `tests/test_issues_declarees.py` qui l'oblige, en derivant les etats de
#: l'extracteur lui-meme plutot que d'une liste tenue a la main.
ISSUES: dict[str, str] = {
    "ADOPTEE": RESULTAT_ADOPTEE,
    "REJETEE": RESULTAT_REJETEE,
    "PAS_DE_VOTE": RESULTAT_PAS_DE_VOTE,
    "SANS_OBJET": RESULTAT_PAS_DE_VOTE,
    "REPORTEE": RESULTAT_PAS_DE_VOTE,
    "VOTE_SANS_FORMULE": RESULTAT_VOTE_SANS_FORMULE,
    "SANS_ISSUE_TRACEE": RESULTAT_SANS_ISSUE,
    "PROJET": RESULTAT_SANS_ISSUE,
    "ISSUE_NON_RECONNUE": RESULTAT_ISSUE_NON_LUE,
    "ISSUE_ENONCEE_NON_LUE": RESULTAT_ISSUE_NON_LUE,
}


def issue_acte(brute: str) -> str:
    """L'issue du modele des actes, pour une issue lue au registre.

    **La degradation est le sujet de cette fonction, pas la traduction.** La
    traduction tient dans `ISSUES`; ce qui manquait etait un defaut qui ne mente
    pas. `ISSUES.get(brute, ISSUES["SANS_ISSUE_TRACEE"])` rendait `le document
    ne dit rien` pour tout jeton non declare - donc pour deux etats reels, et
    pour tout etat que la voie resolutions ajoutera ensuite.

    Les deux cas ne demandent pas le meme defaut, et la colonne vide les separe:

    - **colonne vide**: le registre ne porte rien pour cette resolution. Rien
      n'a ete lu, et `SANS_ISSUE_TRACEE` le dit exactement;
    - **jeton non declare**: la voie resolutions a bien ecrit un etat, et cette
      table ne le connait pas. C'est un defaut de code, jamais un fait sur le
      document. Le rendre en `SANS_ISSUE_TRACEE` affirme que le document est
      muet - une affirmation sur la copropriete, tiree d'un oubli de
      declaration. `ISSUE_NON_LUE` dit la seule chose vraie dans ce cas: le
      document porte quelque chose, il n'a pas ete lu, un humain doit relire.
      L'acte reste hors des issues autorisantes, et il se voit a l'ecran.
    """
    if not brute:
        return RESULTAT_SANS_ISSUE
    return ISSUES.get(brute, RESULTAT_ISSUE_NON_LUE)


#: L'annee d'un exercice se lit dans une date ISO, jamais ailleurs. Une date
#: absente ne rend pas une annee: elle rend une chaine vide, et l'acte est alors
#: hors exercice - ce que `v_taux_gouvernance` groupera a part au lieu de le
#: ranger dans une annee choisie au hasard.
_ANNEE_ISO = re.compile(r"^(\d{4})-\d{2}-\d{2}")

#: L'exercice que la resolution VISE, quand elle le nomme. Il ne se confond pas
#: avec l'exercice auquel l'acte appartient: une assemblee de 2024 arrete des
#: comptes de 2023. Le premier va dans `attributs_acte`, le second dans la
#: colonne `exercice`. Les melanger dans une colonne unique rendrait le cumul
#: d'une delegation faux d'une annee.
_EXERCICE_VISE = re.compile(
    r"(?i)exercice\s+(?:comptable\s+)?(?:\d{4}\s*/\s*)?(\d{4})"
)

#: Les deux cabinets du corpus n'ecrivent pas leur exercice de la meme facon.
#: L'un nomme `exercice 2023`, l'autre borne `du 01/01/2023 au 31/12/2023` sans
#: jamais ecrire le mot suivi d'une annee. Retenir la seule premiere forme
#: revenait a apprendre un cabinet par coeur: mesure du 2026-09-04, un seul
#: attribut `exercice_vise` sortait de cinquante-cinq resolutions, dont deux
#: approbations de comptes et deux budgets. C'est la date de FIN qui nomme
#: l'exercice, la meme que `periode_close` compare a la date d'assemblee.
_PERIODE_VISEE = re.compile(r"du\s+\d{2}/\d{2}/(\d{4})\s+au\s+\d{2}/\d{2}/(\d{4})")


def _lu(valeur: object) -> tuple[str, bool]:
    """Le montant canonique, et s'il etait **ecrit mais illisible**.

    Le pont lit du texte de document: il rencontrera des montants qu'aucune
    regle ne sait lire. Les faire echouer arreterait la construction; les
    remplacer par un nombre les rendrait faux. Ils remontent donc comme un
    troisieme etat, que `montant_source` nomme.
    """
    try:
        return montant_texte(valeur), False
    except MontantIllisible:
        return "", True


def exercice_de(date_iso: str) -> str:
    """L'exercice auquel un acte appartient: l'annee ou il a ete pris."""
    trouve = _ANNEE_ISO.match((date_iso or "").strip())
    return trouve.group(1) if trouve else ""


def exercice_vise(segment: str) -> str:
    """L'exercice que le texte nomme, ou chaine vide s'il n'en nomme aucun.

    Une periode bornee prime sur le mot `exercice` suivi d'une annee: elle est
    plus precise, et c'est elle que le cabinet qui n'ecrit pas le mot emploie.
    Rien n'est deduit quand ni l'une ni l'autre n'est lisible.
    """
    periode = _PERIODE_VISEE.search(segment or "")
    if periode:
        return periode.group(2)
    trouve = _EXERCICE_VISE.search(segment or "")
    return trouve.group(1) if trouve else ""


def majorite_lue(valeur: str) -> str:
    """La majorite annoncee, ou la valeur nommee qui dit qu'il n'y en a pas.

    Le registre `resolutions` laisse la colonne vide quand le proces-verbal
    n'annonce aucun article. Le modele des actes, lui, refuse les colonnes
    vides signifiantes: `v_constats` cherche litteralement `NON_ENONCEE` pour
    produire le constat `MAJORITE_NON_ENONCEE`. Sans cette traduction, le
    constat ne serait jamais rendu - et l'absence de majorite, mesuree une fois
    sur 55 au proces-verbal du 03/07/2024, disparaitrait de l'ecran.
    """
    return (valeur or "").strip() or MAJORITE_NON_ENONCEE


# --------------------------------------------------------------------------
# Le candidat: une ligne de registre, prete a devenir un acte
# --------------------------------------------------------------------------


@dataclass
class Candidat:
    """Une ligne de registre et ce que le pont a pu y ajouter.

    `segment` est vide quand le texte du document n'a pas pu etre relu. Ce n'est
    pas un echec: c'est la raison pour laquelle `portee` vaut `ORDINAIRE`, et
    `portee_indices` le dit en clair a l'ecran.
    """

    ligne: dict[str, str]
    source: str                     # RESOLUTION | DEVIS_CITE
    date_ag: str = ""
    segment: str = ""
    portee: str = PORTEE_ORDINAIRE
    portee_indices: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Lecture des documents, pour la seule portee
# --------------------------------------------------------------------------


def _texte_du_document(instance: Any, ligne_doc: dict[str, str]) -> str:
    """Le texte deja extrait, debarrasse des marqueurs de page vides.

    Meme traitement que la voie resolutions: un scan de vingt-sept pages qui ne
    livre que ses en-tetes `===== PAGE n =====` n'est pas un document lu.
    """
    chemin_relatif = ligne_doc.get("text_path")
    if not chemin_relatif:
        return ""
    chemin = instance.root("workspace") / chemin_relatif
    if not chemin.exists():
        return ""
    return texte_utile(chemin.read_text(encoding="utf-8", errors="ignore"))


def segments_par_position(texte: str) -> dict[str, str]:
    """Le corps de chaque resolution, indexe par sa position dans le document.

    La segmentation est celle de `parse_resolutions`, et elle vient du meme
    appel a `_marqueurs`: si les deux divergeaient, le segment lu ici ne serait
    pas celui d'ou le registre a tire ses champs. La position sert de cle parce
    que c'est elle que le registre a conservee - le numero, lui, peut etre un
    rang deduit, et deux documents peuvent en porter les memes.
    """
    marques = _marqueurs(texte)
    segments: dict[str, str] = {}
    for index, (_, debut) in enumerate(marques):
        fin = marques[index + 1][1] if index + 1 < len(marques) else len(texte)
        segments[str(index + 1)] = texte[debut:fin]
    return segments


#: Les deux champs du registre documentaire dont ce pont depend. `text_path`
#: decide QUEL texte est relu, donc quelle portee sort; `suspected_date` decide
#: la date de l'assemblee quand l'identifiant ne la porte pas. Deux lignes de
#: meme `doc_id` qui divergent sur l'un des deux ne sont pas interchangeables.
CHAMPS_DECISIFS = ("text_path", "suspected_date")


def registre_documents(instance: Any) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Le registre documentaire indexe par `doc_id`, et les `doc_id` ambigus.

    **`doc_id` n'est pas une cle du registre**, et l'indexer comme si c'en etait
    une est une perte silencieuse. Mesure du 2026-09-04: 3 447 lignes pour
    3 105 identifiants distincts, 528 lignes partageant leur `doc_id` avec une
    autre - l'identifiant derive du CONTENU, donc deux fichiers de meme contenu
    et de noms differents produisent deux lignes et un seul `doc_id`. Deux
    d'entre eux portent meme deux types documentaires opposes.

    La version anterieure ecrivait `{doc.get("doc_id"): doc for doc in docs}`:
    la DERNIERE ligne du fichier gagnait, sans que rien ne le dise. Quand les
    deux lignes divergent sur `text_path`, c'est le texte relu - donc la portee
    de toutes les resolutions du document - qui se decidait sur l'ordre des
    lignes d'un CSV.

    Ce qui est fait ici: on retient la premiere ligne qui porte un `text_path`,
    ce qui est un critere du CONTENU et non de l'ordre du fichier; et on NOMME
    les `doc_id` dont les lignes divergent sur un champ decisif, pour que
    l'appelant le rapporte au lieu de trancher a l'aveugle.
    """
    from ..core.common import read_csv

    try:
        _, docs = read_csv(instance.register("documents"))
    except (KeyError, FileNotFoundError):
        return {}, []
    par_id: dict[str, list[dict[str, str]]] = {}
    for doc in docs:
        doc_id = doc.get("doc_id", "")
        if doc_id:
            par_id.setdefault(doc_id, []).append(doc)

    retenus: dict[str, dict[str, str]] = {}
    ambigus: list[str] = []
    for doc_id, lignes in par_id.items():
        retenus[doc_id] = next(
            (d for d in lignes if (d.get("text_path") or "").strip()), lignes[0]
        )
        if len(lignes) > 1 and any(
            len({(d.get(champ) or "").strip() for d in lignes}) > 1
            for champ in CHAMPS_DECISIFS
        ):
            ambigus.append(doc_id)
    return retenus, sorted(ambigus)


def _documents_par_id(instance: Any) -> dict[str, dict[str, str]]:
    return registre_documents(instance)[0]


def _date_ag(ligne: dict[str, str], doc: dict[str, str] | None) -> str:
    """La date de l'assemblee, lue dans l'identifiant puis dans le document.

    `_resolutions_registre._ag_id` ecrit `AG-<date>` quand la date a ete lue, et
    `AG-<doc_id>` sinon. La seconde forme est celle que la decision back n. 3
    interdit de propager: `acte_id_resolution` la marquera `SANS-DATE`, et un
    constat `PV_SANS_DATE_LUE` sortira - une ligne par document, pas une par
    resolution.
    """
    ag_id = (ligne.get("ag_id") or "").strip()
    if _ANNEE_ISO.match(ag_id[3:]) and ag_id.startswith("AG-"):
        return ag_id[3:13]
    if doc:
        return (doc.get("suspected_date") or "")[:10]
    return ""


# --------------------------------------------------------------------------
# Les deux sources
# --------------------------------------------------------------------------


def candidats_resolutions(instance: Any) -> list[Candidat]:
    """Les resolutions constatees ou projetees deja ecrites au registre.

    Le texte de chaque document n'est lu qu'UNE fois, quel que soit le nombre de
    resolutions qu'il porte: sur le proces-verbal etalon, c'est un fichier de
    cinquante-huit mille caracteres relu cinquante-cinq fois si l'on s'y prend
    par ligne.
    """
    lignes = gouvernance_store.lire(
        instance,
        table=gouvernance_store.TABLE_RESOLUTIONS,
        ordre="ag_id, doc_id, CAST(position AS INTEGER)",
    )
    if not lignes:
        return []
    documents = _documents_par_id(instance)
    segments_du_doc: dict[str, dict[str, str]] = {}
    candidats: list[Candidat] = []
    for ligne in lignes:
        doc_id = ligne.get("doc_id", "")
        if doc_id not in segments_du_doc:
            texte = _texte_du_document(instance, documents.get(doc_id, {}))
            segments_du_doc[doc_id] = segments_par_position(texte) if texte else {}
        segment = segments_du_doc[doc_id].get(ligne.get("position", ""), "")
        date_ag = _date_ag(ligne, documents.get(doc_id))
        portee, indices = (
            portee_resolution(segment, date_ag)
            if segment
            else (
                PORTEE_ORDINAIRE,
                [
                    "le corps de la resolution n'a pas pu etre relu: aucun type "
                    "n'est reconnu, et tous les controles restent appliques"
                ],
            )
        )
        candidats.append(
            Candidat(
                ligne=ligne,
                source="RESOLUTION",
                date_ag=date_ag,
                segment=segment,
                portee=portee,
                portee_indices=list(indices),
            )
        )
    return candidats


#: Reconstitution minimale d'un enonce a partir des colonnes du registre des
#: devis cites. Ce n'est pas le texte du document: c'est ce que le registre a
#: retenu, remis dans l'ordre ou `portee_resolution` sait le lire.
#:
#: La difference se paie, et elle est dite: un acte type sur cette base porte
#: `confiance = moyenne`, jamais `forte`. Un objet tronque a trois cents
#: caracteres peut ne pas contenir la periode d'un exercice ou la fonction que
#: la loi nomme, et une portee lue sur un texte partiel se trompe en silence.
def enonce_du_devis(ligne: dict[str, str]) -> str:
    morceaux = [
        ligne.get("objet", ""),
        ligne.get("entreprise", ""),
        f"{ligne.get('montant_ttc', '')} EUR" if ligne.get("montant_ttc") else "",
        ligne.get("cle_repartition", ""),
    ]
    return " ".join(m for m in morceaux if m)


def candidats_devis(instance: Any) -> list[Candidat]:
    """Les projets de resolution lus dans une convocation, un par sous-point.

    **C'est ici que le sous-numero cesse d'etre une decoration.** Ce cabinet
    numerote `11-1`, `11-2`, `11-3`, `11-4`: quatre offres concurrentes sur la
    meme question, quatre projets a voter. Un identifiant derive du seul couple
    (date, numero) les aurait ecrases sur un acte unique - le defaut que la
    decision back n. 3 nomme, et qui est mesure sur ce corpus.

    Rien n'y porte d'issue: une convocation ne vote pas. `etat = PROJETEE`, et
    l'issue reste `SANS_ISSUE_TRACEE`.
    """
    lignes = gouvernance_store.lire(
        instance,
        table="devis_cites",
        ordre="convocation_id, CAST(numero AS INTEGER), CAST(sous_numero AS INTEGER)",
    )
    if not lignes:
        return []
    candidats: list[Candidat] = []
    for ligne in lignes:
        # `convocation_id` porte la date de l'assemblee convoquee: CONV-AAAA-MM-JJ.
        date_ag = (ligne.get("convocation_id", "") or "")[5:15]
        if not _ANNEE_ISO.match(date_ag):
            date_ag = ""
        enonce = enonce_du_devis(ligne)
        portee, indices = portee_resolution(enonce, date_ag)
        candidats.append(
            Candidat(
                ligne=ligne,
                source="DEVIS_CITE",
                date_ag=date_ag,
                segment=enonce,
                portee=portee,
                portee_indices=list(indices),
            )
        )
    return candidats


def etat_du_candidat(candidat: Candidat) -> str:
    """Vote ou seulement propose. Aucune convocation ne rend `CONSTATEE`."""
    if candidat.source == "DEVIS_CITE":
        return ETAT_PROJETEE
    etat = (candidat.ligne.get("etat") or "").strip()
    return ETAT_PROJETEE if etat == ETAT_PROJETEE else ETAT_CONSTATEE
