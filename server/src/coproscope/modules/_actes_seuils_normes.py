"""Les normes de seuil: deux montants, deux obligations, deux relations.

Cree le 2026-09-08 pour `RM-2026-0144`. Jusqu'a ce jour, la relation
`SEUIL_APPLICABLE` portait indifferemment **deux normes distinctes**, arretees
le meme jour par deux resolutions differentes de la meme assemblee: l'une fixe
le montant a partir duquel la consultation du conseil syndical est obligatoire,
l'autre celui a partir duquel la mise en concurrence l'est.

**Deux questions, deux reponses, une seule relation pour les porter.** La
consequence n'etait pas theorique: sur les deux coffres mesures le 2026-09-08,
186 actes portaient au moins un lien de seuil, et 121 d'entre eux se declaraient
`non tranche` alors qu'aucun vote ne s'opposait a un autre. Ils etaient
indecidables parce que **la question melangeait deux normes**, pas parce que la
reponse manquait - et aucune regle d'ordre ne pouvait les trancher: la
chronologie posee la veille n'en a departage aucun, les deux montants etant du
meme jour.

----------------------------------------------------------------------
L'axe, et ce qui reste vrai le long de l'axe
----------------------------------------------------------------------

**L'axe est `ce que le franchissement du montant rend obligatoire`.** Ce n'est
pas une enumeration de deux cas rencontres: c'est un degre de liberte de
l'article 21 alinea 2 lui-meme, qui confie a l'assemblee le soin d'arreter des
montants **et** designe, pour chacun, l'obligation qu'il declenche.

**Ce qui reste invariant le long de l'axe:** une assemblee arrete un montant,
il porte sur des marches et des contrats, il vaut jusqu'a son terme, et un
engagement de depense posterieur y est soumis. Le calendrier, la validite et le
rattachement se calculent identiquement quelle que soit l'obligation. **Seule
l'obligation nommee varie** - et deux obligations differentes ne se departagent
pas entre elles: chacune a son propre `dernier vote`.

**Hors des valeurs observees.** Une deliberation qui arreterait un troisieme
montant sur un objet encore different ne tombe dans aucune des deux cases: elle
tombe dans `NORME_NON_ATTRIBUEE`, qui est nommee, comptee et affichee. Le code
se degrade en disant qu'il ne sait pas, jamais en rangeant par defaut. Le meme
sort attend une deliberation qui arreterait les DEUX montants d'un coup - cas
que l'alinea autorise expressement, en disant `a la meme majorite` - parce que
rien ne dirait alors quel montant sert quelle obligation.

----------------------------------------------------------------------
Le fondement, et ce qu'il ne distingue PAS
----------------------------------------------------------------------

Les deux montants sont arretes sur le meme fondement: la loi 65-557, article 21
alinea 2, dont l'identifiant Legifrance est declare une seule fois dans
`_actes_typologie.FONDEMENT_PORTEE[PORTEE_SEUIL]` - ce module le lit la et n'en
recopie aucun.

**Ce n'est donc pas le fondement qui separe les deux normes**, et une separation
fondee sur deux articles differents serait fausse. Ce qui les separe est qu'il
s'agit de **deux arretes distincts de l'assemblee sur des objets differents**,
portes par deux phrases distinctes du meme alinea. C'est `phrase` qui le dit,
norme par norme.

L'alinea porte en outre une exclusion qui ne vaut que pour la SECONDE: la mise
en concurrence vise les marches et contrats *autres que celui de syndic*, la
consultation prealable ne connait pas cette reserve. Le champ `exclut` la
transporte. Ce lot ne s'en sert pas encore pour retirer un controle - voir le
residu nomme dans le `BOT-END` - mais il cesse de la perdre.
"""

from __future__ import annotations

from typing import Iterable, NamedTuple

from ._actes_typologie import FONDEMENT_PORTEE
from ._actes_vocabulaire import (
    PORTEE_SEUIL,
    REL_SEUIL_CONCURRENCE,
    REL_SEUIL_CONSULTATION_CS,
    REL_SEUIL_NON_ATTRIBUE,
)


class NormeSeuil(NamedTuple):
    """Un montant arrete par l'assemblee, et l'obligation qu'il declenche.

    - `cle` est le **discriminant lu sur le registre**, dans la colonne
      `qualifications`. Il n'est pas invente ici: la voie resolutions distingue
      deja les deux normes depuis `_resolutions_qualification`, et le modele des
      actes les ecrasait en aval. Une chaine vide veut dire *aucun discriminant
      ne designe cette entree*, ce qui est le cas de la seule entree residuelle;
    - `relation` est la relation du modele qui porte le lien. Deux normes, deux
      relations: c'est le livrable du lot;
    - `prefixe` nomme les colonnes de `v_matrice_gouvernance` et les cellules de
      l'ecran. Il doit dire LAQUELLE des normes la cellule rapporte, sans quoi
      le defaut corrige dans le modele reviendrait a l'affichage;
    - `libelle` est ce qu'un coproprietaire lit;
    - `phrase` est la phrase de l'alinea qui arrete ce montant-la. C'est elle,
      et non l'article, qui distingue les deux normes;
    - `exclut` est ce que l'alinea sort du champ de cette norme, ou la chaine
      vide quand il n'en sort rien.
    """

    cle: str
    relation: str
    prefixe: str
    libelle: str
    phrase: str
    exclut: str


#: Le montant a partir duquel la **consultation prealable du conseil syndical**
#: devient obligatoire. Premiere phrase de l'alinea. Aucune exclusion: le meme
#: article ajoute au contraire que le conseil syndical peut se prononcer, par un
#: avis ecrit, sur tout projet de contrat de syndic.
NORME_CONSULTATION_CS = NormeSeuil(
    cle="SEUIL_CONSULTATION_CS",
    relation=REL_SEUIL_CONSULTATION_CS,
    prefixe="seuil_consultation_cs",
    libelle="Seuil de consultation du conseil syndical",
    phrase=(
        "l'assemblee arrete un montant des marches et des contrats a partir "
        "duquel la consultation du conseil syndical est rendue obligatoire"
    ),
    exclut="",
)

#: Le montant a partir duquel la **mise en concurrence** devient obligatoire.
#: Seconde phrase du meme alinea, votee `a la meme majorite`, et seule des deux
#: a porter une exclusion.
NORME_CONCURRENCE = NormeSeuil(
    cle="SEUIL_MISE_EN_CONCURRENCE",
    relation=REL_SEUIL_CONCURRENCE,
    prefixe="seuil_concurrence",
    libelle="Seuil de mise en concurrence",
    phrase=(
        "l'assemblee arrete, a la meme majorite, un montant des marches et des "
        "contrats a partir duquel la mise en concurrence est rendue obligatoire"
    ),
    exclut="les marches et contrats autres que celui de syndic",
)

#: **Le residu, nomme.** Un montant de seuil est rattache et l'obligation qu'il
#: declenche n'a pas ete identifiee.
#:
#: Sa valeur de relation reste `SEUIL_APPLICABLE`, et **ce n'est pas un reste
#: de l'ancien nom: c'est la migration**. Toute ligne deja ecrite dans un coffre
#: porte cette valeur, et c'est exactement ce qu'elle veut dire - un seuil
#: rattache dont personne n'a dit lequel. Changer la valeur aurait orpheline ces
#: lignes: elles auraient disparu de l'ecran sans qu'aucun compteur ne bouge.
#: Un re-versement reclasse ce qu'il peut et laisse ici ce qu'il ne peut pas.
NORME_NON_ATTRIBUEE = NormeSeuil(
    cle="",
    relation=REL_SEUIL_NON_ATTRIBUE,
    prefixe="seuil",
    libelle="Seuil rattache, norme non attribuee",
    phrase=FONDEMENT_PORTEE[PORTEE_SEUIL][0],
    exclut="",
)

#: Les normes DECLAREES, dans l'ordre de l'alinea. Le residu n'en fait pas
#: partie: il n'est pas une troisieme norme, il est l'absence de reponse.
NORMES_SEUIL: tuple[NormeSeuil, ...] = (NORME_CONSULTATION_CS, NORME_CONCURRENCE)

#: Toutes les entrees qui portent une cellule d'ecran, residu compris. L'ordre
#: est celui de l'affichage: les deux normes d'abord, ce qu'on n'a pas su
#: attribuer ensuite.
ENTREES_SEUIL: tuple[NormeSeuil, ...] = NORMES_SEUIL + (NORME_NON_ATTRIBUEE,)

#: relation -> entree, pour les vues et les cellules.
PAR_RELATION: dict[str, NormeSeuil] = {n.relation: n for n in ENTREES_SEUIL}

#: Le fondement commun aux deux normes, lu une fois et jamais recopie.
FONDEMENT_COMMUN = FONDEMENT_PORTEE[PORTEE_SEUIL][1]

#: Le separateur de la colonne `qualifications` du registre des resolutions,
#: ecrit par `_resolutions_registre` en `";".join(...)`. On compare des JETONS
#: et non des sous-chaines: `SEUIL_CONSULTATION_CS` n'est pas contenu dans
#: `SEUIL_MISE_EN_CONCURRENCE` aujourd'hui, mais une troisieme valeur dont l'une
#: serait le prefixe rendrait vraie une appartenance qui ne l'est pas.
SEPARATEUR_QUALIFICATIONS = ";"


def jetons(qualifications: str | Iterable[str]) -> frozenset[str]:
    """Les qualifications lues, en jetons exacts.

    Accepte la chaine du registre comme une suite deja decoupee: les tests
    posent des listes, le registre pose une chaine, et la fonction ne doit pas
    obliger l'appelant a savoir lequel il tient.
    """
    if isinstance(qualifications, str):
        brut: Iterable[str] = qualifications.split(SEPARATEUR_QUALIFICATIONS)
    else:
        brut = qualifications
    return frozenset(x.strip() for x in brut if x and x.strip())


def norme_arretee(qualifications: str | Iterable[str]) -> tuple[NormeSeuil, str]:
    """Quelle norme cette deliberation arrete, et pourquoi quand on ne sait pas.

    Rend `(norme, motif)`. Le motif est vide quand la norme est attribuee, et
    il NOMME la raison sinon: c'est lui qui va a l'ecran a la place d'une
    attribution inventee.

    Les trois issues, et aucune n'est un choix par defaut:

    - une seule norme declaree est lue: c'est elle;
    - aucune n'est lue: la deliberation arrete un montant que l'outil ne sait
      pas rattacher a une obligation connue. C'est le cas d'un troisieme
      montant, et le cas d'un corps de resolution qui n'a pas pu etre relu;
    - plusieurs sont lues: l'alinea autorise l'assemblee a arreter les deux
      montants `a la meme majorite`, donc une seule resolution peut porter les
      deux. Rien ne dit alors quel montant sert quelle obligation, et deviner
      reviendrait a fabriquer une norme.
    """
    lues = jetons(qualifications)
    trouvees = [n for n in NORMES_SEUIL if n.cle in lues]
    if len(trouvees) == 1:
        return trouvees[0], ""
    if not trouvees:
        return NORME_NON_ATTRIBUEE, (
            "aucune des deux obligations de l'article 21 alinea 2 n'a ete lue "
            "sur cette deliberation: le montant est arrete, ce qu'il declenche "
            "n'est pas etabli"
        )
    return NORME_NON_ATTRIBUEE, (
        "cette deliberation arrete "
        + str(len(trouvees))
        + " montants de l'article 21 alinea 2 a la fois ("
        + ", ".join(n.libelle.lower() for n in trouvees)
        + "): rien ne dit lequel s'applique a quelle obligation"
    )
