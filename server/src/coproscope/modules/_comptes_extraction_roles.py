# -*- coding: utf-8 -*-
"""Le ROLE d'une colonne d'annexe se lit dans ses mots, jamais dans sa position.

**Le constat `C037`, et pourquoi sa formulation d'origine etait a cote.** Il
disait: *le total des charges est pris dans la derniere colonne, donc souvent un
budget a venir au lieu du realise de l'exercice*. La ligne visee est
`total_charges = totaux[-1]`. Une instruction du 2026-09-10 a montre que le seul
consommateur de ce champ **veut** un budget, donc que remplacer la valeur par le
realise casserait l'appelant au lieu de le reparer.

**Ce que la mesure sur les DEUX cabinets a trouve a la place, et c'est pire.**
Sur 39 documents d'annexe - 36 chez le premier cabinet, 3 chez le second -
`lire_annexe` rend un total dans 16 documents ou **aucune colonne n'est
identifiee**: `colonnes=0` et pourtant `total_charges` renseigne, elu parmi 1,
2, 4 ou 8 valeurs sans nom. Chez le second cabinet, **tous** les documents qui
portent un total sont dans ce cas. Trois autres documents annoncent dix colonnes
pour cinq totaux - une repetition d'entete que le comptage des millesimes n'a
pas absorbee. Le defaut n'est donc pas *on prend la mauvaise colonne*, c'est
**on elit une valeur dans une liste dont on ignore la structure**.

**Deuxieme correction, et elle porte sur une affirmation du gouvernail.** Il
etait ecrit que `_USAGES` ne connait *que deux libelles compactes qu'aucun des
deux cabinets mesures n'ecrit*. **C'est faux, mesure le 2026-09-10:** les deux
cabinets ecrivent `Pour approbation des comptes` - 70 fois chez l'un, 30 chez
l'autre - et `Pour le vote du budget` - 70 et 10. Ce qui est vrai, c'est
qu'**aucun usage n'est jamais attribue**: `_usage_de` n'attribue que s'il y a
exactement autant d'usages annonces que de colonnes, et deux usages sur cinq
colonnes ne disent pas ou passe la frontiere. Le refus est fonde. Sa
consequence ne l'est pas: le module refuse de nommer les colonnes, **puis en
elit une par sa position**.

**L'AXE.** Ce qui varie d'un cabinet a l'autre, c'est la formulation et la mise
en page: `Exercice clos realise a approuver`, `Exercice clos realise`, un renvoi
`(N)`, un `N + 2` sur sa propre ligne, un libelle coupe en trois par le retour a
la ligne. Ce qui reste INVARIANT, c'est qu'un entete de colonne d'annexe situe
la colonne sur **deux dimensions independantes**:

1. **la nature** - un montant CONSTATE (`realise`) ou un montant PREVU
   (`budget`, `previsionnel`);
2. **le statut** - deja arrete (`approuve`, `vote`) ou soumis maintenant
   (`a approuver`, `a voter`, `propose`).

Les quatre combinaisons existent et se rencontrent: realise arrete (l'exercice
precedent), realise soumis (l'exercice clos a approuver), budget arrete (le
budget vote de l'exercice clos ou de l'exercice en cours), budget soumis (le
budget a voter). C'est pour cela que ce sont deux axes et non une liste de cinq
libelles: **une enumeration de cinq casse au sixieme, deux axes binaires ne
cassent pas, ils rendent `inconnu` sur la dimension qu'ils n'ont pas lue.**

**HORS DES VALEURS OBSERVEES.** Un entete dont la nature ne se lit pas rend
`NATURE_INCONNUE`; un entete dont le statut ne se lit pas rend
`STATUT_INCONNU`. Les deux se declarent, aucun ne se devine, et un role
incomplet **n'est jamais elu** par `colonne_du_role`. Un cabinet qui ecrirait
`estimatif` la ou les deux mesures ecrivent `previsionnel` obtiendrait donc une
colonne sans nature, declaree comme telle - pas une colonne rangee au hasard.

**CE QUE CE MODULE NE FAIT PAS.** Il ne decide pas quelle colonne un appelant
veut: il rend les roles, et `colonne_du_role` repond a une demande NOMMEE. C'est
exactement ce que le docstring de `_comptes_extraction_annexe` promettait deja -
*c'est a l'appelant de designer la colonne qu'il veut, en la nommant* - et que
`totaux[-1]` contredisait dans le meme fichier.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

__all__ = [
    "BUDGET",
    "entetes_de_colonnes",
    "NATURE_INCONNUE",
    "REALISE",
    "RoleColonne",
    "SOUMIS",
    "STATUT_INCONNU",
    "ARRETE",
    "colonne_du_role",
    "role_de_l_entete",
    "roles_des_entetes",
]

#: Axe 1 - la nature du montant.
REALISE = "REALISE"
BUDGET = "BUDGET"
NATURE_INCONNUE = "NATURE_INCONNUE"

#: Axe 2 - le statut de la colonne dans la seance.
ARRETE = "ARRETE"
SOUMIS = "SOUMIS"
STATUT_INCONNU = "STATUT_INCONNU"


class RoleColonne:
    """Le role d'une colonne, sur les deux axes, plus l'entete qui l'a produit."""

    __slots__ = ("nature", "statut", "entete")

    def __init__(self, nature: str, statut: str, entete: str) -> None:
        self.nature = nature
        self.statut = statut
        self.entete = entete

    @property
    def complet(self) -> bool:
        """Vrai quand les DEUX dimensions ont ete lues.

        Un role incomplet n'est pas une approximation utilisable: il manque de
        quoi distinguer un budget vote d'un budget a voter, c'est-a-dire
        exactement ce qui separe un montant deja acquis d'un montant soumis au
        vote de ce soir.
        """
        return self.nature != NATURE_INCONNUE and self.statut != STATUT_INCONNU

    def __eq__(self, autre: object) -> bool:
        if not isinstance(autre, RoleColonne):
            return NotImplemented
        return (self.nature, self.statut) == (autre.nature, autre.statut)

    def __repr__(self) -> str:  # pragma: no cover - confort de lecture
        return "RoleColonne(%s, %s)" % (self.nature, self.statut)


def _sans_accent(brut: str) -> str:
    decompose = unicodedata.normalize("NFD", str(brut or ""))
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def _normalise(brut: str) -> str:
    """Minuscules, sans accent, blancs reduits.

    La normalisation porte sur ce qui n'est PAS du sens: la casse, l'accent et
    l'espacement varient d'un cabinet et d'un OCR a l'autre. Les mots, eux, sont
    compares entiers.
    """
    return re.sub(r"\s+", " ", _sans_accent(brut).lower()).strip()


#: Axe 1. Chaque entree est un mot, pas un libelle entier: c'est ce qui permet
#: a `Exercice clos realise a approuver` et a `realises (N)` de rendre la meme
#: nature sans qu'aucun des deux ne soit enumere.
_MOTS_REALISE = ("realise", "realises", "realisee", "constate", "constates")
_MOTS_BUDGET = ("budget", "previsionnel", "previsionnelle", "prevu", "previsions")

#: Axe 2. `a approuver` et `a voter` portent la preposition: elle est ce qui
#: distingue le soumis de l'arrete, et la perdre inverserait le sens.
_MARQUES_SOUMIS = ("a approuver", "a voter", "a approbation", "propose",
                   "proposes", "soumis", "pour approbation", "pour le vote")
_MOTS_ARRETE = ("approuve", "approuves", "vote", "votes", "arrete", "arretes")


def role_de_l_entete(entete: str) -> RoleColonne:
    """Le role que porte un entete de colonne, sur les deux axes.

    L'ordre de lecture du statut n'est pas indifferent: `a approuver` CONTIENT
    `approuver`, et `budget vote` contient `vote`. Les marques du soumis sont
    donc cherchees d'abord, parce qu'une marque de soumission est plus
    specifique qu'un participe d'arrete - et se tromper de sens ici transforme
    un montant soumis au vote de ce soir en un montant deja acquis.
    """
    texte = _normalise(entete)
    mots = set(re.findall(r"[a-z0-9+-]+", texte))

    if mots & set(_MOTS_REALISE):
        nature = REALISE
    elif mots & set(_MOTS_BUDGET):
        nature = BUDGET
    else:
        nature = NATURE_INCONNUE

    if any(marque in texte for marque in _MARQUES_SOUMIS):
        statut = SOUMIS
    elif mots & set(_MOTS_ARRETE):
        statut = ARRETE
    else:
        statut = STATUT_INCONNU

    return RoleColonne(nature, statut, re.sub(r"\s+", " ", str(entete or "")).strip())


def roles_des_entetes(entetes: Iterable[str]) -> list[RoleColonne]:
    """Les roles, dans l'ordre des entetes recus."""
    return [role_de_l_entete(e) for e in entetes]


def colonne_du_role(
    colonnes: Iterable[Any],
    nature: str,
    statut: str,
) -> int | None:
    """L'index de LA colonne qui porte ce role, ou `None`.

    Rend `None` dans trois cas, et les trois se valent: aucune colonne ne porte
    ce role, plusieurs le portent, ou la colonne trouvee a un role incomplet.

    **Le cas *plusieurs* n'est pas un detail de robustesse.** Une annexe dont
    l'entete est repete par l'aplatissement porte deux fois chaque colonne;
    prendre la premiere ou la derniere serait de nouveau une election par
    position. Une demande qui ne designe pas une colonne unique n'est pas
    satisfaite, et cela se dit.
    """
    trouves = [
        i for i, colonne in enumerate(colonnes)
        if getattr(colonne, "role", None) is not None
        and colonne.role.complet
        and colonne.role.nature == nature
        and colonne.role.statut == statut
    ]
    if len(trouves) != 1:
        return None
    return trouves[0]


#: Un repere d'exercice en tete de colonne. **Deux formes, un seul axe.** Le
#: premier cabinet mesure ecrit le millesime (`2029`); le second ecrit le repere
#: RELATIF du modele reglementaire (`N`, `N + 1`, `N - 1`, `N + 2`). Ce qui
#: varie est la maniere de designer l'exercice, ce qui reste invariant est
#: qu'une colonne en porte un. Une seule des deux formes aurait manque tout un
#: cabinet: mesure du 2026-09-10, le localisateur limite aux millesimes trouvait
#: **zero bloc** chez le second, et vingt-huit une fois les reperes relatifs
#: admis.
REPERE_EXERCICE = re.compile(r"^(?:(?:19|20)\d{2}|N(?:\s*[+-]\s*\d)?)$", re.IGNORECASE)
_PORTE_UN_CHIFFRE = re.compile(r"\d")


def entetes_de_colonnes(lignes: Iterable[str]) -> list[str]:
    """Les entetes de colonnes, un par colonne, ou une liste VIDE.

    **Ou ils se trouvent.** Un tableau d'annexe aplati en texte pose les
    libelles de colonnes, puis les reperes d'exercice, puis les chiffres. Le
    bloc d'entetes est donc la suite de lignes non chiffrees qui precede
    immediatement une suite d'au moins deux reperes d'exercice.

    **Comment ils se separent.** Un libelle trop long pour la largeur de la
    colonne est coupe par le retour a la ligne, et la coupure ne met pas de
    majuscule: une ligne qui commence en minuscule CONTINUE le libelle
    precedent, une ligne qui commence par une majuscule en OUVRE un nouveau.
    C'est une propriete de la mise en page d'un tableau, pas un libelle observe.

    **Le refus, et il est la moitie utile de cette fonction.** Si le decoupage
    ne rend pas exactement autant d'entetes que de reperes, la fonction rend une
    liste VIDE. Attribuer quand meme reviendrait a deviner ou passe la
    frontiere - c'est la regle que `_usage_de` applique deja, et pour la meme
    raison.

    **Mesure du 2026-09-10, et elle borne la portee.** Concordant sur 52 blocs
    du premier cabinet et sur la fixture du depot; **non concordant sur les 28
    blocs du second cabinet**, dont la mise en page intercale les reperes
    autrement. Le second obtient donc une liste vide, c'est-a-dire aucun role -
    ce qui est le comportement voulu, mais **cette fonction n'est pas prouvee
    sur les deux cabinets** et ne doit pas etre presentee comme telle.
    """
    nus = [re.sub(r"\s+", " ", str(l or "").strip()) for l in lignes]
    for i, ligne in enumerate(nus):
        if not REPERE_EXERCICE.match(ligne):
            continue
        fin = i
        while fin < len(nus) and REPERE_EXERCICE.match(nus[fin]):
            fin += 1
        if fin - i < 2:
            continue
        amont: list[str] = []
        j = i - 1
        while (j >= 0 and nus[j] and not _PORTE_UN_CHIFFRE.search(nus[j])
               and not REPERE_EXERCICE.match(nus[j])):
            amont.append(nus[j])
            j -= 1
        entetes = _recoller(reversed(amont))
        if len(entetes) == fin - i:
            return entetes
    return []


def _recoller(amont: Iterable[str]) -> list[str]:
    """Recolle les lignes de continuation sur l'entete qu'elles prolongent."""
    entetes: list[str] = []
    for ligne in amont:
        if not ligne:
            continue
        if entetes and ligne[:1].islower():
            entetes[-1] += " " + ligne
        else:
            entetes.append(ligne)
    return entetes
