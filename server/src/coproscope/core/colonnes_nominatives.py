from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Sequence


"""Une colonne nominative se reconnait a sa REPETITION, jamais a ses mots.

`RM-2026-0068`. Une annexe `etat des soldes` liste les coproprietaires nom par
nom, chacun suivi de son solde individuel, **sans une seule civilite**. Un
patronyme nu n'a aucune forme lexicale: rien, dans la suite de lettres, ne
distingue un nom de famille d'un intitule de poste comptable. Chercher le mot
est mal pose.

**Ce qui a une forme, c'est la COLONNE.** Une liste nominative est une suite de
cellules homogenes, repetee, de meme cardinalite qu'une colonne de quantites.
C'est cette propriete-la que ce module mesure, et c'est la seule.

**L'axe, et il a deja mordu.** Le detecteur precedent ancrait le nom sur ce
qu'un seul cabinet avait rendu: un numero de compte SEUL sur la ligne d'avant,
un montant SEUL sur la ligne d'apres. C'est une modalite, pas un axe. Mesure du
2026-09-09 sur le second cabinet du poste - 16 pieces, 22 documents - les deux
regles structurelles existantes rendent **zero sur 487 identites detectees**;
tout ce qui y est vu l'est par des regles lexicales, donc par chance de casse.
Et sur huit rendus du MEME tableau synthetique, six rendent **0 nom sur 6, en
silence**.

**L'axe est donc: la maniere dont les cellules d'un rang sont rendues dans le
texte extrait est un degre de liberte.** Un rang peut tenir sur une ligne, etre
eclate en une ligne par cellule, etre separe par des barres verticales, ou etre
rendu colonne par colonne. Ce qui reste invariant le long de cet axe:

- les rangs se REPETENT, avec la meme silhouette de cellules;
- une position de cellule porte un nom recevable, une autre porte une quantite;
- une colonne de noms a la MEME CARDINALITE que sa colonne de quantites.

**Hors des valeurs observees**, le module se degrade en rendant moins, jamais en
affirmant a faux: un rendu qu'aucune des deux lectures ne reconnait produit une
liste vide, et l'appelant garde ses regles lexicales.

**Ce que ce module ne voit pas, et il faut le savoir avant de s'y fier.**

- **Une enumeration de noms en PROSE**, du type `Sont presents: X, Y, Z`. Ce
  n'est pas une colonne et aucune repetition ne s'y lit. Mesure du 2026-09-09:
  0 nom sur 6 - et **toute la chaine y est aveugle**, pas seulement ce module,
  parce que `NOM PRENOM` tout en capitales n'apparie ni `nom_prenom`, qui veut
  un prenom en minuscules, ni `prenom_nom`, qui veut un prenom en tete. C'est un
  autre axe - lexical - et il reste ouvert.
- **Une colonne de noms sans aucune colonne de quantites en face.** C'est
  delibere: la quantite est ce qui distingue un annuaire d'une suite de titres.
- **Un tableau dont les rangs sont interrompus par plus de deux lignes.**

Ces trois cas rendent une liste vide. Ils ne rendent jamais un faux nom.
"""


#: La colonne alignee sur les noms porte une QUANTITE, et le genre de quantite
#: est lui-meme un degre de liberte: un solde a deux decimales dans l'annexe des
#: comptes, un nombre ENTIER de tantiemes dans une feuille de presence.
#: `RM-2026-0068` nomme les deux cas - 146 noms suivis d'un solde, et environ 120
#: noms suivis de leurs tantiemes et du sens de leur vote. Exiger deux decimales
#: aurait rendu le second invisible **en silence**, ce qui est exactement la
#: faute que ce module existe pour corriger.
#: Ce n'est pas cette regle qui protege du sur-masquage, c'est `est_nom`.
MOTIF_QUANTITE = re.compile(
    r"^[\s(\[]*[-−+]?\s*\d{1,3}(?:[\s  .,]?\d{3})*(?:[,.]\d{1,4})?\s*\)?\s*(?:%|€|EUR|EUROS)?[\s.]*$",
    flags=re.IGNORECASE,
)

#: Les separateurs de cellules d'un tableau rendu sur une seule ligne. La barre
#: verticale vient des tables docx/xlsx, que le lecteur joint par ` | `.
MOTIF_CELLULES = re.compile(r"\s*\|\s*|\t+|(?<=\S) {2,}(?=\S)")

CELLULE_NOM = "N"
CELLULE_QUANTITE = "Q"
CELLULE_AUTRE = "."

#: Nombre de rangs qu'il faut voir se repeter pour parler d'une colonne. Une
#: liste de coproprietaires en compte des dizaines; quatre suffit a etablir la
#: repetition sans exiger une grande copropriete.
MINIMUM_RANGS = 4

#: Periodes de rang explorees. 1 = un rang par ligne; 2 a 4 = un rang eclate en
#: autant de lignes que de cellules. Au-dela, la repetition ne se distingue plus
#: d'une coincidence de mise en page.
PERIODES = (1, 2, 3, 4)

#: Lignes d'interruption tolerees entre deux rangs d'une meme colonne. Un
#: tableau reel n'est pas une suite parfaite: un intitule de batiment, une
#: entete repetee en haut de page ou un sous-total s'intercalent. Sans cette
#: tolerance, une annexe des soldes decoupee par batiment n'a plus aucun rang
#: consecutif et le detecteur rend zero **en silence** - mesure du 2026-09-09,
#: 0 nom sur 6 avec un intitule tous les deux rangs. Borne a deux lignes: au
#: dela, ce n'est plus une interruption, c'est une autre zone du document.
INTERRUPTION_MAX = 2

#: Signes qu'un nom de personne ne porte jamais. Le trait d'union et
#: l'apostrophe en sont volontairement absents: ils sont dans les patronymes.
CARACTERE_HORS_NOM = re.compile(r"[/+()\[\]{}:;,&_=*%@#<>\"!?\\|~^$]")

#: Une colonne nominative porte des valeurs DISTINCTES: 146 coproprietaires font
#: 146 noms. Une colonne qui repete la meme valeur est une colonne d'etiquette,
#: pas un annuaire. Mesure du 2026-09-09: sans cette regle, une cellule de trois
#: lettres repetee a l'identique sur quatre rangs devenait quatre personnes.
DISTINCTS_MINIMUM = 3


@dataclass(frozen=True)
class ColonneNominative:
    """Une colonne de noms, et la preuve structurelle qui la designe."""

    valeurs: tuple[str, ...]
    lecture: str
    periode: int
    rangs: int

    @property
    def motif(self) -> str:
        return f"colonne_nominative:{self.lecture}"


def _cellules(ligne: str) -> list[str]:
    return [cellule.strip() for cellule in MOTIF_CELLULES.split(ligne) if cellule.strip()]


def _classe(cellule: str, est_nom: Callable[[str], bool]) -> str:
    if MOTIF_QUANTITE.match(cellule):
        return CELLULE_QUANTITE
    if _forme_de_nom(cellule) and est_nom(cellule):
        return CELLULE_NOM
    return CELLULE_AUTRE


def _forme_de_nom(cellule: str) -> bool:
    """Une cellule qui ne peut pas etre un nom de personne, quoi qu'en dise le lexique.

    Mesure du 2026-09-09 sur le corpus etalon: en elargissant la colonne alignee
    aux entiers, une TABLE DES MATIERES - intitule d'annexe puis numero de page -
    a pris la silhouette d'une liste nominative, et neuf intitules sont devenus
    des personnes. Ils portaient tous une marque qu'aucun patronyme ne porte:
    une barre oblique, un signe plus, un point final, une puce en tete.

    Le trait d'union et l'apostrophe restent admis - `DELAVIGNE-PERRIN`, `D'ARVEL`.

    **Les deux clauses sont portantes, et une troisieme a ete retiree pour ne pas
    l'etre.** Controle negatif du 2026-09-09 sur les 29 extraits de l'etalon:
    autoriser la barre oblique et le signe plus fait revenir 10 faux positifs,
    retirer les bornes alphabetiques en fait revenir 5. Une borne sur le NOMBRE
    DE MOTS avait aussi ete posee; portee a 99, elle ne changeait rien - elle ne
    protegeait de rien et n'aurait su que faire disparaitre en silence un
    `DE LA MOTTE BRUNEAU MARIE`. Une regle dont on ne sait pas montrer le
    travail ne se garde pas: elle ne peut que couter des noms non vus.
    """

    if not cellule or CARACTERE_HORS_NOM.search(cellule):
        return False
    return cellule[0].isalpha() and cellule[-1].isalpha()


def _rangs(texte: str, est_nom: Callable[[str], bool]) -> list[tuple[str, list[str]]]:
    """Chaque ligne non vide, reduite a sa silhouette de cellules."""

    lus: list[tuple[str, list[str]]] = []
    for ligne in texte.splitlines():
        if not ligne.strip():
            continue
        cellules = _cellules(ligne)
        if not cellules:
            continue
        silhouette = "".join(_classe(cellule, est_nom) for cellule in cellules)
        lus.append((silhouette, cellules))
    return lus


def _assez_distinctes(valeurs: Sequence[str]) -> bool:
    """Un annuaire nomme des gens differents; une etiquette se repete."""

    if not valeurs:
        return False
    return len({valeur.upper() for valeur in valeurs}) >= min(DISTINCTS_MINIMUM, len(valeurs))


def _mixte(silhouette: str) -> bool:
    return CELLULE_NOM in silhouette and CELLULE_QUANTITE in silhouette


def _noms_du_rang(silhouette: str, cellules: Sequence[str]) -> list[str]:
    return [cellule for classe, cellule in zip(silhouette, cellules) if classe == CELLULE_NOM]


def _lecture_periodique(
    lus: list[tuple[str, list[str]]], periode: int, minimum: int
) -> list[ColonneNominative]:
    """Les rangs de periode `periode` qui se repetent, nom et quantite compris.

    Periode 1: le rang tient sur une ligne. Periode P: le rang est eclate sur P
    lignes consecutives, une par cellule - la forme que rend un extracteur qui
    lit le tableau cellule par cellule.
    """

    trouvees: list[ColonneNominative] = []
    depart = 0
    while depart + periode * minimum <= len(lus):
        gabarit = tuple(silhouette for silhouette, _ in lus[depart : depart + periode])
        if not _mixte("".join(gabarit)):
            depart += 1
            continue
        rangs: list[int] = []
        curseur = depart
        while curseur + periode <= len(lus):
            if tuple(s for s, _ in lus[curseur : curseur + periode]) == gabarit:
                rangs.append(curseur)
                curseur += periode
                continue
            # Une interruption ne met pas fin au tableau: un intitule de
            # batiment, une entete repetee en haut de page ou un sous-total
            # s'intercalent sans que les rangs cessent d'etre des rangs.
            saut = _saut_jusqu_au_gabarit(lus, curseur, periode, gabarit)
            if saut is None:
                break
            curseur = saut
        if len(rangs) >= minimum:
            valeurs: list[str] = []
            for debut_rang in rangs:
                for silhouette, cellules in lus[debut_rang : debut_rang + periode]:
                    valeurs.extend(_noms_du_rang(silhouette, cellules))
            if _assez_distinctes(valeurs):
                trouvees.append(
                    ColonneNominative(tuple(valeurs), "rang", periode, len(rangs))
                )
            depart = curseur
            continue
        depart += 1
    return trouvees


def _saut_jusqu_au_gabarit(
    lus: list[tuple[str, list[str]]],
    curseur: int,
    periode: int,
    gabarit: tuple[str, ...],
) -> int | None:
    """L'indice ou le gabarit reprend, si l'interruption reste breve."""

    for ecart in range(1, INTERRUPTION_MAX + 1):
        reprise = curseur + ecart
        if reprise + periode > len(lus):
            return None
        if tuple(s for s, _ in lus[reprise : reprise + periode]) == gabarit:
            return reprise
    return None


def _blocs(lus: list[tuple[str, list[str]]], classe: str, minimum: int) -> list[tuple[int, int]]:
    """Les suites maximales de lignes a cellule unique, toutes de la meme classe."""

    suites: list[tuple[int, int]] = []
    debut: int | None = None
    for index, (silhouette, _) in enumerate(lus):
        if silhouette == classe:
            debut = index if debut is None else debut
            continue
        if debut is not None and index - debut >= minimum:
            suites.append((debut, index))
        debut = None
    if debut is not None and len(lus) - debut >= minimum:
        suites.append((debut, len(lus)))
    return suites


def _lecture_par_colonne(
    lus: list[tuple[str, list[str]]], minimum: int
) -> list[ColonneNominative]:
    """Le rendu colonne par colonne: tous les noms, puis toutes les quantites.

    Ici aucun rang n'existe dans le texte - c'est justement l'interet de juger
    sur la CARDINALITE. Un bloc de N noms suivi d'un bloc de N quantites est la
    meme table que les autres lectures, ecrite dans un autre ordre.
    """

    noms = _blocs(lus, CELLULE_NOM, minimum)
    quantites = _blocs(lus, CELLULE_QUANTITE, minimum)
    trouvees: list[ColonneNominative] = []
    for debut, fin in noms:
        hauteur = fin - debut
        for autre_debut, autre_fin in quantites:
            if autre_debut < fin:
                continue
            if autre_fin - autre_debut != hauteur:
                continue
            if autre_debut - fin > hauteur:
                # Trop loin: ce n'est plus la meme table.
                continue
            valeurs = [cellules[0] for _, cellules in lus[debut:fin]]
            if _assez_distinctes(valeurs):
                trouvees.append(ColonneNominative(tuple(valeurs), "colonne", 1, hauteur))
            break
    return trouvees


def colonnes_nominatives(
    texte: str,
    est_nom: Callable[[str], bool],
    *,
    minimum: int = MINIMUM_RANGS,
) -> list[ColonneNominative]:
    """Les colonnes de noms alignees sur une colonne de quantites.

    `est_nom` est injecte: ce module possede la STRUCTURE, l'appelant possede le
    LEXIQUE. Les deux ne doivent pas se melanger, sinon la question `qu'est-ce
    qu'un nom` se retrouve repondue a deux endroits qui divergeront.
    """

    lus = _rangs(texte, est_nom)
    if len(lus) < minimum:
        return []
    trouvees: list[ColonneNominative] = []
    for periode in PERIODES:
        trouvees.extend(_lecture_periodique(lus, periode, minimum))
    trouvees.extend(_lecture_par_colonne(lus, minimum))
    return trouvees


def noms_en_colonne(
    texte: str,
    est_nom: Callable[[str], bool],
    *,
    minimum: int = MINIMUM_RANGS,
) -> list[str]:
    """Les valeurs nominatives des colonnes trouvees, dedoublonnees, dans l'ordre."""

    vus: dict[str, None] = {}
    for colonne in colonnes_nominatives(texte, est_nom, minimum=minimum):
        for valeur in colonne.valeurs:
            vus.setdefault(valeur, None)
    return list(vus)
