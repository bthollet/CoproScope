"""Lecture d'un index d'extranet: du HTML vers des observations.

C'est **la partie fragile** du dispositif, et elle est isolee ici pour cela. Le
referentiel de conformite decrit la norme attendue et ne bouge qu'avec le
droit; ce module decrit comment lire une page chez un editeur donne, et change
a chaque refonte d'interface. Les melanger produirait un outil dont on ne
saurait plus si une erreur vient du droit ou de la lecture.

Aucun acces reseau ici. Ce module recoit du HTML deja obtenu et rend des
structures. C'est ce qui le rend testable sans extranet, sans session et sans
donnee reelle.

======================================================================
Axes de generalisation
======================================================================

Livrable obligatoire de tout lot d'extraction. Pour chaque difference
constatee entre editeurs: l'axe, ce qui reste invariant le long de l'axe, ce
que le code en fait, et ce qui se passe hors des valeurs observees.

----------------------------------------------------------------------
Axe 1 - comment une rubrique est delimitee dans la page
----------------------------------------------------------------------

*Valeurs observees*: chez l'editeur mesure, un bloc par rubrique, identifie par
une **classe CSS** portant un code court, les huit blocs coexistant dans le DOM
et un seul etant visible.

*Invariant*: une piece appartient a une rubrique, et cette appartenance est
lisible dans la page - sinon l'utilisateur lui-meme ne saurait pas ou il est.

*Ce que le code en fait*: le profil declare l'attribut porteur et la liste des
codes. Aucun code n'est devine.

*Hors des valeurs observees*: un editeur qui servirait une rubrique par URL, ou
qui les chargerait a la demande, ne rendrait aucun bloc connu. Les rubriques
declarees absentes de la page sont alors `NON_EXPLOREE`, jamais vides - donc
aucune absence n'y est affirmable. Degradation propre.

----------------------------------------------------------------------
Axe 2 - comment le libelle d'une piece est porte
----------------------------------------------------------------------

*Valeurs observees*: **deux liens par piece** chez l'editeur mesure - une icone
sans texte, et un libelle. Mesure du 2026-09-04: 230 liens pour 115 pieces.

*Invariant*: une piece qu'un humain peut ouvrir porte quelque part de quoi la
nommer, sinon l'interface serait inutilisable.

*Ce que le code en fait*: les liens sans texte sont ecartes par une classe
declaree au profil, et les doublons restants sont fusionnes sur l'emplacement.

*Hors des valeurs observees*: un editeur qui ne servirait qu'un lien sans texte
produirait des pieces sans libelle. Elles sont journalisees avec un emplacement
`INDETERMINE`: comptees, jamais comparees. Le journal dit alors "j'ai vu des
pieces que je ne sais pas nommer", ce qui est vrai et utile, plutot que d'en
inventer les noms.

----------------------------------------------------------------------
Axe 3 - ou vit la composante qui distingue deux pieces homonymes
----------------------------------------------------------------------

*Valeurs observees*: chez l'editeur mesure, l'exercice comptable est porte par
une **ligne d'en-tete de groupe** et non par le libelle. Consequence mesuree
sur l'index entier: le libelle seul donne 32 collisions sur 115 pieces.

*Invariant*: si une interface montre deux pieces homonymes, elle donne
forcement a l'oeil de quoi les distinguer - sinon l'utilisateur ne pourrait pas
choisir.

*Ce que le code en fait*: il retient la derniere ligne sans lien rencontree
avant la piece, sous le nom de groupe, et l'integre a la cle.

*Hors des valeurs observees*: un editeur qui distinguerait par une colonne
plutot que par un en-tete produirait un groupe vide et des libelles homonymes.
La collision est alors **detectee a chaque passage** par `_extranet_journal` et
les emplacements concernes passent `INDETERMINE`. Le journal se degrade sur ces
pieces-la et continue sur les autres.

----------------------------------------------------------------------
Axe 4 - ce qui prouve qu'une liste est complete
----------------------------------------------------------------------

*Valeurs observees*: aucun total annonce, aucun controle de pagination, et
l'index entier deja present dans le DOM.

*Invariant*: une absence ne se conclut que d'une liste dont on sait qu'elle est
close.

*Ce que le code en fait*: il cherche d'abord un total annonce - `ATTESTEE`. A
defaut, il cherche des marqueurs de pagination declares au profil: s'il n'en
trouve aucun, il conclut `CONSTATEE`, cloture plus faible mais reelle. S'il en
trouve, `AUCUNE`.

*Hors des valeurs observees*: un editeur paginant sans marqueur reconnu serait
lu comme `CONSTATEE` a tort. C'est le risque residuel de ce module, il est
nomme, et il se reduit en ajoutant des marqueurs au profil - pas en changeant
le code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Sequence

from ._extranet_schema import (
    CLOTURE_ATTESTEE,
    CLOTURE_AUCUNE,
    CLOTURE_CONSTATEE,
    CONTENU_NON_VERIFIE,
    ORIGINE_EXTRAIT,
    RUBRIQUE_ECHEC,
    RUBRIQUE_NON_EXPLOREE,
    RUBRIQUE_PARCOURUE,
    emplacement as construire_emplacement,
)

# ---------------------------------------------------------------------------
# Un arbre minimal, sans dependance
# ---------------------------------------------------------------------------

_AUTO_FERMANTS = {"br", "hr", "img", "input", "meta", "link", "source"}


@dataclass
class Noeud:
    tag: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    enfants: list["Noeud"] = field(default_factory=list)
    texte: str = ""
    parent: "Noeud | None" = None

    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())

    def texte_total(self) -> str:
        morceaux = [self.texte] + [e.texte_total() for e in self.enfants]
        return " ".join(m for m in " ".join(morceaux).split() if m)

    def descendants(self, tag: str = "") -> list["Noeud"]:
        trouves: list[Noeud] = []
        for enfant in self.enfants:
            if not tag or enfant.tag == tag:
                trouves.append(enfant)
            trouves.extend(enfant.descendants(tag))
        return trouves


class _Arbre(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.racine = Noeud(tag="#racine")
        self._pile = [self.racine]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        noeud = Noeud(tag=tag, attrs={k: (v or "") for k, v in attrs}, parent=self._pile[-1])
        self._pile[-1].enfants.append(noeud)
        if tag not in _AUTO_FERMANTS:
            self._pile.append(noeud)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self._pile) - 1, 0, -1):
            if self._pile[i].tag == tag:
                del self._pile[i:]
                return

    def handle_data(self, data: str) -> None:
        if data.strip():
            self._pile[-1].enfants.append(Noeud(tag="#texte", texte=data, parent=self._pile[-1]))


def analyser(html: str) -> Noeud:
    """Rend l'arbre d'un document HTML."""
    parseur = _Arbre()
    parseur.feed(html or "")
    parseur.close()
    return parseur.racine


# ---------------------------------------------------------------------------
# Profil d'editeur
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProfilEditeur:
    """Tout ce qui est propre a un editeur, et rien d'autre.

    Un nouvel editeur s'ajoute en ecrivant un profil, pas en modifiant
    l'algorithme. Si un editeur ne rentre pas dans ce profil, il faut un axe de
    plus - pas une exception dans le code.
    """

    code: str
    #: code de rubrique -> libelle affiche. Les deux sont declares parce qu'ils
    #: **divergent**: chez l'editeur mesure la rubrique intitulee "Documents
    #: techniques" porte le code `DIA`. Deduire l'un de l'autre se tromperait
    #: des la premiere rubrique, et en silence.
    rubriques: dict[str, str]
    #: fragment qui identifie le lien d'une piece dans son adresse
    marqueur_lien: str = "documents/"
    #: classe des liens sans texte, doublons de ceux qui portent le libelle
    classe_icone: str = "pj"
    #: au-dela de ce nombre de cellules, une ligne sans lien n'est pas un
    #: en-tete de groupe mais une ligne de donnees sans piece jointe
    cellules_max_groupe: int = 2
    #: fragments de classe qui trahissent une pagination
    marqueurs_pagination: Sequence[str] = ("pagin", "suivant", "page-suiv")


#: Profil de l'editeur observe le 2026-09-04. Les codes viennent de la page,
#: pas d'une convention devinee.
PROFIL_COPRODIRECTE = ProfilEditeur(
    code="coprodirecte",
    rubriques={
        "ARR": "Arrete des comptes",
        "ASS": "Assemblees generales",
        "CON": "Contrats",
        "DIV": "Documents divers",
        "JUS": "Assignations en justice",
        "REU": "Reunion du conseil syndical",
        "REG": "Reglement de copropriete",
        "DIA": "Documents techniques",
    },
)

PROFILS = {PROFIL_COPRODIRECTE.code: PROFIL_COPRODIRECTE}


# ---------------------------------------------------------------------------
# Lecture d'un index
# ---------------------------------------------------------------------------


def _liens(noeud: Noeud, profil: ProfilEditeur) -> list[Noeud]:
    return [
        a
        for a in noeud.descendants("a")
        if profil.marqueur_lien in (a.attrs.get("href") or "")
    ]


def _pagine(racine: Noeud, profil: ProfilEditeur) -> bool:
    for noeud in racine.descendants():
        classe = (noeud.attrs.get("class") or "").lower()
        if any(marqueur in classe for marqueur in profil.marqueurs_pagination):
            return True
    return False


def _total_annonce(racine: Noeud) -> bool:
    """Un total explicite du type `43 documents`, servi par l'editeur.

    **Le motif ne s'applique plus a la page entiere.** Mesure du 2026-09-07: un
    seul libelle de piece contenant *Bordereau 12 pieces jointes* suffisait a
    faire basculer TOUTES les rubriques en `CLOTURE_ATTESTEE` - la cloture la
    plus forte, celle qui autorise a conclure a une absence. Une phrase ecrite
    par le syndic dans le TITRE d'un document devenait ainsi une garantie
    d'exhaustivite donnee par l'outil.

    On ne regarde donc que le texte situe **hors des lignes de liste**: un
    total annonce est une mention de l'editeur au-dessus de sa liste, jamais le
    titre d'une piece qui s'y trouve.
    """
    import re

    dans_les_lignes = set()
    for ligne in racine.descendants("tr"):
        dans_les_lignes.add(id(ligne))
        for enfant in ligne.descendants():
            dans_les_lignes.add(id(enfant))
    hors_liste = " ".join(
        n.texte for n in racine.descendants()
        if n.texte and id(n) not in dans_les_lignes
    )
    return bool(
        re.search(
            r"\b\d+\s*(documents?|pi[eè]ces?|r[eé]sultats?)\b",
            hors_liste,
            re.I,
        )
    )


def lire_index(
    html: str,
    profil: ProfilEditeur,
    passage_id: str,
    *,
    rubriques_visitees: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Analyse une page d'index et rend `rubriques` et `pieces`.

    `rubriques_visitees` borne ce que l'on ose declarer parcouru. Par defaut,
    toute rubrique dont le bloc est present dans la page est consideree
    parcourue - c'est vrai chez un editeur qui sert tout le DOM d'un coup, et
    c'est **faux** chez un editeur qui charge a la demande. L'appelant qui
    n'est pas sur passe la liste de ce qu'il a reellement ouvert.
    """
    racine = analyser(html)
    pagine = _pagine(racine, profil)
    if _total_annonce(racine):
        cloture = CLOTURE_ATTESTEE
    elif pagine:
        cloture = CLOTURE_AUCUNE
    else:
        cloture = CLOTURE_CONSTATEE

    blocs: dict[str, Noeud] = {}
    for noeud in racine.descendants():
        for code in profil.rubriques:
            if code in noeud.classes() and code not in blocs:
                blocs[code] = noeud

    rubriques: list[dict[str, str]] = []
    pieces: list[dict[str, str]] = []
    rang = 0

    for code, libelle_rubrique in profil.rubriques.items():
        bloc = blocs.get(code)
        visitee = rubriques_visitees is None or code in rubriques_visitees
        if bloc is None or not visitee:
            rubriques.append(
                {
                    "passage_id": passage_id,
                    "rubrique_code": code,
                    "rubrique_libelle": libelle_rubrique,
                    "etat": RUBRIQUE_NON_EXPLOREE,
                    "cloture": CLOTURE_AUCUNE,
                    "nb_pieces": "0",
                    "motif": "bloc absent de la page" if bloc is None else "non visitee",
                    "doc_id": "",
                    "origine": ORIGINE_EXTRAIT,
                }
            )
            continue

        vues = _lire_bloc(bloc, profil, code, passage_id, depart=rang)
        rang += len(vues)
        pieces.extend(vues)
        etat, motif = _etat_du_bloc(bloc, vues, profil.marqueur_lien)
        rubriques.append(
            {
                "passage_id": passage_id,
                "rubrique_code": code,
                "rubrique_libelle": libelle_rubrique,
                "etat": etat,
                "cloture": cloture if etat == RUBRIQUE_PARCOURUE else CLOTURE_AUCUNE,
                "nb_pieces": str(len(vues)),
                "motif": motif,
                "doc_id": "",
                "origine": ORIGINE_EXTRAIT,
            }
        )

    return {"rubriques": rubriques, "pieces": pieces}


def _etat_du_bloc(
    bloc: Noeud, vues: list[dict[str, str]], marqueur_lien: str = "documents/"
) -> tuple[str, str]:
    """Distingue une rubrique vide d'une rubrique illisible.

    **Le defaut que cette fonction repare.** Jusqu'au 2026-09-07, un bloc
    present mais dont aucune ligne n'etait comprise ressortait `PARCOURUE` avec
    zero piece - c'est-a-dire un faux *rubrique vide*, indiscernable d'une
    rubrique reellement vide. Et une rubrique vide autorise `_peut_conclure_absence`
    a conclure: un changement de gabarit chez l'editeur aurait donc produit,
    en silence, le retrait de toutes les pieces de la rubrique.

    AXE. La maniere dont un editeur affiche une rubrique servie et vide est un
    degre de liberte: un tableau aux en-tetes seuls, une ligne *aucun
    document*, un paragraphe, une illustration.

    INVARIANT le long de l'axe: **une rubrique servie affiche toujours quelque
    chose**, ne serait-ce que la charpente de sa liste. Un bloc qui ne porte ni
    ligne ni texte n'est pas une rubrique vide - c'est une rubrique qu'on n'a
    pas su lire.

    HORS DES VALEURS OBSERVEES: un editeur qui servirait une rubrique vide sous
    une forme inconnue mais non muette ressort `PARCOURUE` avec zero piece et
    son motif. Un editeur dont le gabarit a change au point de ne plus rien
    rendre ressort `ECHEC`, et l'absence cesse d'etre affirmable. La
    degradation va donc toujours vers le doute, jamais vers l'affirmation.
    """
    if vues:
        return RUBRIQUE_PARCOURUE, ""
    lignes = bloc.descendants("tr")
    texte = bloc.texte_total()
    # Des liens de document mais aucune ligne lue: le bloc sert des pieces sous
    # une forme que le lecteur ne connait pas - une liste `ul`, par exemple.
    # Mesure du 2026-09-07 sur l'epreuve d'un second corpus: cela ressortait
    # `PARCOURUE` avec zero piece ET la cloture `CONSTATEE`, donc une absence
    # AFFIRMABLE. Un editeur qui sert ses listes autrement, ou un gabarit qui
    # change entre deux passages, produisait le retrait silencieux de toutes
    # les pieces de la rubrique.
    if not lignes and any(
        marqueur_lien in (a.attrs.get("href") or "")
        for a in bloc.descendants("a")
    ):
        return (
            RUBRIQUE_ECHEC,
            "des liens de document sont presents mais aucune ligne n'a ete lue: "
            "la rubrique sert des pieces sous une forme inconnue, aucune "
            "absence n'est affirmable ici",
        )
    if not lignes and not texte:
        return (
            RUBRIQUE_ECHEC,
            "bloc present mais ni ligne ni texte: rubrique non lue, "
            "aucune absence n'est affirmable ici",
        )
    if not lignes:
        return RUBRIQUE_PARCOURUE, "aucune ligne, texte present"
    return RUBRIQUE_PARCOURUE, "lignes presentes, aucune piece reconnue"


def _lire_bloc(
    bloc: Noeud,
    profil: ProfilEditeur,
    code: str,
    passage_id: str,
    *,
    depart: int,
) -> list[dict[str, str]]:
    """Les pieces d'une rubrique, groupes resolus et doublons fusionnes."""
    groupe = ""
    vues: dict[str, dict[str, str]] = {}
    ordre: list[str] = []
    sans_libelle = 0

    for ligne in bloc.descendants("tr"):
        liens = _liens(ligne, profil)
        cellules = [e for e in ligne.enfants if e.tag in ("td", "th")]
        if not liens:
            if len(cellules) <= profil.cellules_max_groupe:
                texte = ligne.texte_total()
                if texte:
                    groupe = texte
            continue

        nommes = [a for a in liens if profil.classe_icone not in a.classes()]
        libelle = ""
        for a in nommes:
            texte = a.texte_total()
            if texte:
                libelle = texte
                break

        cle, qualite = construire_emplacement(code, groupe, libelle)
        if not libelle:
            sans_libelle += 1
            # Sans libelle, deux pieces d'un meme groupe auraient la meme cle
            # vide: on les distingue par leur rang pour ne pas les fusionner,
            # tout en gardant la qualite `INDETERMINE` qui les exclut de toute
            # comparaison.
            cle = f"{code}#{depart + len(ordre)}"

        if cle in vues:
            # Deux liens de la meme piece - le cas mesure, icone plus libelle.
            continue
        vues[cle] = {
            "passage_id": passage_id,
            "rubrique_code": code,
            "rang": str(depart + len(ordre)),
            "groupe": groupe,
            "libelle": libelle,
            "emplacement": cle if qualite != "INDETERMINE" else "",
            "emplacement_qualite": qualite,
            "nom_serveur": "",
            "empreinte": "",
            "contenu_etat": CONTENU_NON_VERIFIE,
            "doc_id": "",
            "origine": ORIGINE_EXTRAIT,
        }
        ordre.append(cle)

    return [vues[cle] for cle in ordre]
