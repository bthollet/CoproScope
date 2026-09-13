# -*- coding: utf-8 -*-
"""Proposer des candidats de date, puis dire a quel titre chacun est la.

**Ce module existe a cause d'une mesure, pas d'une intuition.** L'etalon du
2026-09-08 (`docs/etalon_dates_confrontation_2026-09-08.md`) a confronte
80 documents lus a l'aveugle avec ce que le produit lisait: **9 justes sur 75**,
et surtout **zero document date correctement a partir d'une date ecrite dans son
propre texte**. Les neuf reussites venaient toutes d'un nom de fichier.

**Le resultat qui commande l'ordre des travaux, et il est contre-intuitif.**
Ajouter des formes AGGRAVE tant qu'on ne sait pas a quel titre un nombre est la:
etendre l'ancien lecteur a la forme a points changeait 41 reponses, dont dix
devenaient une **citation juridique** - trois proces-verbaux dates au 14 mars
2005, le decret comptable. Deux remplacaient une date correcte par une fausse,
et aucun test ne tombait.

On fait donc le **role d'abord**, les formes ensuite.

---

## L'axe

Ce qui varie: la maniere d'ecrire une date - separateur, ordre des champs,
largeur, mois en chiffres ou en lettres, granularite.

Ce qui reste invariant, et ce module ne repose que la-dessus:

1. une date est un triplet ordonne (quantieme, mois, millesime) dont des champs
   peuvent manquer, jamais se repeter ni s'inverser entre eux;
2. le domaine de chaque champ est **ferme par le calendrier** - un mois va de 1
   a 12, et le 31 fevrier n'existe pas. C'est le seul filtre qui n'a pas besoin
   d'avoir vu le corpus;
3. un mot de mois est toujours un **prefixe** d'un des douze noms du calendrier,
   accents et casse mis de cote. Un cabinet qui ecrirait `sep.` ou `juill.`
   tombe dedans sans qu'on ait rien ajoute;
4. **un jeton n'est une date que si rien dans son voisinage ne le designe comme
   autre chose.** Cet invariant se formule en negatif a dessein: on ne peut pas
   enumerer tout ce qu'un numero peut etre, mais on peut exiger qu'un candidat
   ne soit ni colle a d'autres chiffres, ni annonce comme un numero, ni suivi
   d'une minute.

## Ce qui reste une modalite, et comment on la tient

Les deux vocabulaires de disqualification - la **numerotation** (`n°`, `ref`,
`facture n`) et les **actes juridiques** (`decret`, `loi`, `article`) - sont des
listes de mots. Ce sont des mots de la LANGUE administrative francaise, pas des
valeurs observees chez un cabinet: c'est ce qui les distingue de
`["ARR","ASS","CON"]`. Mais ils restent une liste, et une liste se refute.

**La garde est donc le comptage.** Chaque disqualification est comptee et rendue
a l'appelant. Le jour ou un cabinet numerote autrement, le signal attendu est
une hausse du nombre de documents **sans candidat** - une absence visible -
jamais une date fausse rendue en silence.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

from ._date_en_lettres import date_en_toutes_lettres

__all__ = [
    "MOIS_DU_CALENDRIER",
    "Candidat",
    "candidats_du_texte",
    "normalise",
    "role_du_candidat",
]

MOIS_DU_CALENDRIER: tuple[str, ...] = (
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
)

#: Les mois dont le nom est trop court pour qu'un prefixe soit discriminant.
#: `ma` designe mars ou mai; on exige alors le nom entier.
_MOIS_COURTS = {"mai", "juin", "mars", "aout"}

#: Longueur minimale d'un prefixe de mois. Trois lettres separent les douze
#: noms sauf `mar`/`mai`, traites par `_MOIS_COURTS`.
_PREFIXE_MINIMAL = 3

_JOURS_PAR_MOIS = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def normalise(valeur: str) -> str:
    """Accents retires, casse abaissee, espaces insecables ramenes a l'espace.

    La longueur est **conservee caractere pour caractere**: les positions
    trouvees dans le texte normalise designent les memes caracteres dans le
    texte d'origine, ce qui permet de citer la chaine telle qu'elle est ecrite.
    """
    texte = str(valeur or "").replace(chr(0x00A0), " ").replace(chr(0x202F), " ")
    decompose = unicodedata.normalize("NFD", texte)
    sans_accent = "".join(c for c in decompose if not unicodedata.combining(c))
    if len(sans_accent) != len(texte):
        # Une decomposition qui change la longueur casserait la correspondance
        # des positions. On retombe alors sur un remplacement caractere par
        # caractere, moins fin mais qui preserve l'alignement.
        sans_accent = "".join(
            "".join(c for c in unicodedata.normalize("NFD", ch) if not unicodedata.combining(c))[:1] or ch
            for ch in texte
        )
    return sans_accent.lower()


def _mois_depuis_mot(mot: str) -> int:
    """Le rang du mois quand le mot est un prefixe non ambigu d'un nom.

    Rend 0 quand aucun nom ne commence par ce mot, ou quand plusieurs le font.
    """
    mot = mot.strip(". ").lower()
    if len(mot) < _PREFIXE_MINIMAL:
        return 0
    correspondances = [i for i, nom in enumerate(MOIS_DU_CALENDRIER, start=1) if nom.startswith(mot)]
    if len(correspondances) != 1:
        return 0
    nom = MOIS_DU_CALENDRIER[correspondances[0] - 1]
    if nom in _MOIS_COURTS and mot != nom:
        return 0
    return correspondances[0]


def _date_existe(jour: int, mois: int, annee: int) -> bool:
    if not 1 <= mois <= 12:
        return False
    if jour == 0:
        return True
    plafond = _JOURS_PAR_MOIS[mois - 1]
    if mois == 2 and jour == 29:
        return annee % 4 == 0 and (annee % 100 != 0 or annee % 400 == 0)
    return 1 <= jour <= plafond


class Candidat:
    """Une suite de caracteres qui a la FORME d'une date, avec sa position."""

    __slots__ = ("debut", "fin", "chaine", "champs", "ordre_possible")

    def __init__(self, debut: int, fin: int, chaine: str, champs: tuple[int, int, int],
                 ordre_possible: str) -> None:
        self.debut = debut
        self.fin = fin
        self.chaine = chaine
        #: (quantieme, mois, millesime); un quantieme a 0 quand il n'est pas dit.
        self.champs = champs
        #: `jma`, `amj`, ou `ambigu` quand les deux lectures restent possibles.
        self.ordre_possible = ordre_possible

    @property
    def valeur(self) -> str:
        jour, mois, annee = self.champs
        return "%04d-%02d-%02d" % (annee, mois, jour) if jour else "%04d-%02d" % (annee, mois)

    @property
    def granularite(self) -> str:
        return "jour" if self.champs[0] else "mois"

    def __repr__(self) -> str:  # pragma: no cover
        return "Candidat(%s, %r)" % (self.valeur, self.chaine)


#: Trois champs separes par ce que l'on voudra: le separateur se CAPTURE, il ne
#: se choisit pas dans une liste. C'est l'axe numero un.
_SEPARATEUR = r"[-/. _]"
_NUMERIQUE = re.compile(
    r"(?<![0-9])(\d{1,4})" + _SEPARATEUR + r"{1,2}(\d{1,2})(?:" + _SEPARATEUR + r"{1,2}(\d{2,4}))?(?![0-9])"
)
_EN_LETTRES = re.compile(
    r"(?<![0-9a-z])(?:(\d{1,2})(?:er)?\s+)?([a-z]{3,10})\.?\s+((?:19|20)\d{2})(?![0-9])"
)


def _annee_pleine(valeur: int) -> int:
    """Une annee a deux chiffres n'est PAS completee: on refuse le pivot.

    Mesure du 2026-09-08: le corpus melange des millesimes 2015-2027 et 1965,
    1967, 1985 dans la meme forme. `la loi du 10/07/65` deviendrait 2065.
    **Tout pivot de siecle est une modalite**, donc on rend 0 - le candidat est
    ecarte, et son ecartement est compte.
    """
    return valeur if 1900 <= valeur <= 2199 else 0


def _candidats_numeriques(texte: str) -> list[Candidat]:
    trouves: list[Candidat] = []
    for m in _NUMERIQUE.finditer(texte):
        a, b, c = m.group(1), m.group(2), m.group(3)
        if c is None:
            # **La forme numerique a DEUX champs n'est pas reconnue, et c'est
            # une decision.** `48/1995`, dans une liste d'opposants a une
            # assemblee, est un TANTIEME de copropriete, pas un mois/annee -
            # mesure du 2026-09-08. Aucun signal de forme ne les separe. On
            # perd donc `12/2025` pour ne pas fabriquer une date a partir d'un
            # tantieme, et cette perte est comptee comme une absence.
            #
            # Effet de bord heureux, verifie: le bug de l'heure disparait par
            # la meme porte. `20/03/2025 08:56:39` rendait `2025 08`; cette
            # paire n'est plus un candidat du tout.
            continue
        x, y, z = int(a), int(b), int(c)
        lectures = []
        if len(a) == 4:                       # annee en tete
            annee = _annee_pleine(x)
            if annee and _date_existe(z, y, annee):
                lectures.append(((z, y, annee), "amj"))
        if len(c) >= 2:                       # annee en queue
            annee = _annee_pleine(z if len(c) == 4 else 0)
            if annee and _date_existe(x, y, annee):
                lectures.append(((x, y, annee), "jma"))
        if not lectures:
            continue
        if len(lectures) == 1:
            champs, ordre = lectures[0]
        else:
            champs, ordre = lectures[-1], "ambigu"
            champs = lectures[-1][0]
        trouves.append(Candidat(m.start(), m.end(), m.group(0), champs, ordre))
    return trouves


def _candidats_en_lettres(texte: str) -> list[Candidat]:
    trouves: list[Candidat] = []
    for m in _EN_LETTRES.finditer(texte):
        mois = _mois_depuis_mot(m.group(2))
        if not mois:
            continue
        jour = int(m.group(1)) if m.group(1) else 0
        annee = _annee_pleine(int(m.group(3)))
        if annee and _date_existe(jour, mois, annee):
            trouves.append(Candidat(m.start(), m.end(), m.group(0), (jour, mois, annee), "jma"))
    return trouves


def _candidats_en_toutes_lettres(texte: str) -> list[Candidat]:
    """Les dates ecrites entierement en mots - la forme des actes.

    `Ce jour MERCREDI TROIS JUILLET DEUX MILLE VINGT QUATRE`. Sans cette
    lecture, sept proces-verbaux sur dix n'avaient AUCUN candidat portant leur
    propre date, et retombaient sur un identifiant de document.
    """
    trouves = []
    for debut, fin, (jour, mois, annee) in date_en_toutes_lettres(texte):
        if _date_existe(jour, mois, annee):
            trouves.append(Candidat(debut, fin, texte[debut:fin], (jour, mois, annee), "jma"))
    return trouves


def candidats_du_texte(texte_normalise: str) -> list[Candidat]:
    """Tous les candidats bien formes ET possibles au calendrier, dans l'ordre."""
    trouves = (_candidats_numeriques(texte_normalise)
               + _candidats_en_lettres(texte_normalise)
               + _candidats_en_toutes_lettres(texte_normalise))
    trouves.sort(key=lambda c: c.debut)
    return trouves


# --------------------------------------------------------------------------
# Le role: a quel titre ce jeton est-il la ?
# --------------------------------------------------------------------------

#: Le vocabulaire de la NUMEROTATION. Mots de la langue administrative, pas
#: valeurs observees chez un cabinet. Compte a chaque rejet.
_NUMEROTATION = (
    "n°", "n o", "no ", "num", "numero", "ref", "reference", "facture n", "devis n",
    "bon n", "commande n", "dossier n", "contrat n", "police n", "siret", "siren",
)
#: Le vocabulaire des ACTES JURIDIQUES. Une date qui suit l'un de ces mots date
#: le texte cite, jamais le document qui le cite.
_ACTES = (
    "decret", "loi ", "loi n", "arrete", "ordonnance", "circulaire", "article",
    "art.", "art ", "code ", "reglement ce", "directive",
)
#: Ce qui ANNONCE une date d'emission. Sert a preferer, jamais a exclure.
_ETIQUETTES_EMISSION = (
    "date", "le ", "fait a", "fait le", "etabli le", "edite le", "emis le",
    "arrete le", "signe le", "l'an ", "ce jour",
)

ROLE_DATE = "date"
ROLE_NUMERO = "numero"
ROLE_ACTE_CITE = "acte_cite"
ROLE_COLLE = "colle_a_des_chiffres"


def role_du_candidat(texte: str, candidat: Candidat, fenetre: int = 40) -> str:
    """A quel titre ce jeton figure dans la phrase.

    Trois regles structurelles - qui ne connaissent aucun mot - puis deux
    vocabulaires generiques. L'ordre compte: le structurel d'abord, parce qu'il
    ne peut pas etre refute par un cabinet inconnu.
    """
    avant = texte[max(0, candidat.debut - fenetre): candidat.debut]
    apres = texte[candidat.fin: candidat.fin + 8]

    # 1. Structurel: colle a d'autres chiffres. `F2026-04-058` n'est pas une date.
    if avant[-1:].isdigit() or apres[:1].isdigit():
        return ROLE_COLLE
    # **Il n'y a pas de regle pour l'heure, et c'est voulu.** Une premiere
    # version en portait une; elle etait INATTEIGNABLE, parce que la paire
    # `2025 08` qui produisait le bug n'est plus proposee comme candidat (voir
    # `_candidats_numeriques`). Une garde qui ne peut pas se declencher donne
    # l'illusion d'une protection: on la retire plutot que de la garder pour
    # la forme.
    # 2. Lexical, vocabulaire de la numerotation.
    queue = avant[-18:]
    if any(mot in queue for mot in _NUMEROTATION):
        return ROLE_NUMERO
    # 3. Lexical, vocabulaire des actes juridiques - ET la preposition qui
    #    introduit la date d'un acte. `decret n 2012-1115 DU 2 octobre 2012`
    #    cite un texte; `arrete AU 31/12/2025` cloture un exercice. Sans cette
    #    seconde condition, le seul mot `arrete` dans les 40 caracteres
    #    precedents disqualifiait une date legitime - defaut mesure le
    #    2026-09-09 sur `Etat au 01/01/2025 puis arrete au 31/12/2025`.
    if avant.rstrip().endswith(" du") or avant.endswith("du "):
        if any(mot in avant for mot in _ACTES):
            return ROLE_ACTE_CITE
    return ROLE_DATE


def annonce_une_emission(texte: str, candidat: Candidat, fenetre: int = 26) -> bool:
    """Le candidat est-il annonce par une etiquette d'emission ?"""
    avant = texte[max(0, candidat.debut - fenetre): candidat.debut]
    return any(mot in avant for mot in _ETIQUETTES_EMISSION)


def ordre_du_document(candidats: Iterable[Candidat]) -> str:
    """L'ordre jour/mois se decide par l'ARITHMETIQUE, pas par une convention.

    Un champ superieur a 12 est forcement un quantieme. Mesure du 2026-09-08:
    6 269 occurrences dans 553 documents le prouvent, **zero prouve l'inverse**.
    Quand rien ne tranche - 107 documents - on rend `presume`, et l'appelant
    doit dire que c'est une hypothese.
    """
    for c in candidats:
        if c.ordre_possible in ("jma", "amj") and c.ordre_possible != "ambigu":
            if c.ordre_possible == "jma" and c.champs[0] > 12:
                return "jma"
            if c.ordre_possible == "amj":
                return "amj"
    return "presume"


def compte_par_role(texte: str, candidats: Iterable[Candidat]) -> dict[str, int]:
    """Le comptage qui tient lieu de garde sur les deux vocabulaires."""
    compte: dict[str, int] = {}
    for c in candidats:
        role = role_du_candidat(texte, c)
        compte[role] = compte.get(role, 0) + 1
    return compte
