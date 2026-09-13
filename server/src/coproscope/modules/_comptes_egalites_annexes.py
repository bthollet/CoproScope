# -*- coding: utf-8 -*-
"""Les quatre egalites de controle des annexes comptables, executables.

`RM-2026-0094`. Le decret 2005-240 n'impose pas une opinion: il impose des
**totaux qui doivent coincider**. Trois egalites viennent de l'article 10, une
de l'annexe 5. Elles sont ici des fonctions, et non plus une phrase dans un
document.

**LA SOURCE EST CITEE PAR SA CLE, jamais par un numero recopie.** Les cles
`d05.10` et `d05.annexe2` vivent dans
`_budget_previsionnel_sources.py`, qui porte l'identifiant `LEGIARTI`, la
version et la date de lecture. Un identifiant sans date de version n'est pas
une citation: le meme article a plusieurs versions, toutes marquees `VIGUEUR`.

**L'AUTO-LIMITATION QUI EXISTAIT ICI EST LEVEE, ET IL FAUT DIRE POURQUOI.**
Les lecteurs d'annexes declaraient, a juste titre, que *les modeles d'annexes
ne sont pas reproduits au Journal officiel accessible par machine*. C'etait
vrai des trois voies numeriques tentees le 2026-09-06 - l'API rend `Annexe non
reproduite`, la page du JO renvoie au tableau papier, le PDF est refuse en 401
et 403. **La structure a ete obtenue autrement: Brice a depose lui-meme le
fichier officiel**, `joe_20050318_0065_0007.pdf`, Journal officiel du 18 mars
2005, texte 7 sur 102, NOR `SOCU0412534D`, lu page par page. La limitation
portait sur l'ACCES, pas sur l'existence de la source; l'acces a ete comble, et
`docs/annexes_comptables_decret_2005-240.md` porte le releve.
**Ce qui reste vrai et n'est pas leve:** les rubriques de ventilation des
annexes 3 et 4 sont *arretees en fonction des clauses du reglement de
copropriete*. Elles ne sont donc **pas** universelles, et aucun controle ne
doit les coder.

**TROIS ETATS, ET LE TROISIEME N'EST PAS UN FEU VERT.** Une egalite rend
`CONFORME`, `ECART`, ou `INDETERMINE` - *le controle n'a pas pu etre fait*. Un
total absent ne vaut jamais conformite: c'est la regle du depot sur les
controles partiels, et c'est ici qu'elle compte le plus, parce qu'un rapport
comptable se lit comme une attestation.

**LA RESERVE DE LECTURE EST PORTEE PAR LE CODE, pas seulement par le
document.** Le texte ecrit deux fois *le total des charges de l'annexe n° 2*
sans dire lequel des deux blocs, alors que l'annexe 2 en porte deux, nettement
separes: operations courantes d'une part, travaux de l'article 14-2 et
operations exceptionnelles de l'autre. La lecture retenue - **chaque annexe se
compare au bloc de meme nature** - est la seule qui ait un sens comptable, et
elle reste une lecture. Les fonctions exigent donc **le bloc nomme**, jamais un
total d'annexe 2 indifferencie: un appelant qui ne sait pas de quel bloc il
parle obtient `INDETERMINE`, et non une comparaison au hasard.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ._budget_previsionnel_sources import source

CONFORME = "CONFORME"
ECART = "ECART"
INDETERMINE = "INDETERMINE"

#: Les deux moments ou le decret exige une egalite. Ce n'est pas un detail de
#: presentation: l'article 10 pose la meme egalite aux deux, et une seule de
#: plus a l'approbation.
APPROBATION_DES_COMPTES = "APPROBATION_DES_COMPTES"
VOTE_DU_BUDGET = "VOTE_DU_BUDGET"

#: Les deux blocs de l'annexe 2, qui sont la raison de la reserve de lecture.
BLOC_COURANTES = "OPERATIONS_COURANTES"
BLOC_TRAVAUX_EXCEPTIONNELLES = "TRAVAUX_14_2_ET_EXCEPTIONNELLES"

#: Tolerance d'arrondi. Deux presentations du meme total peuvent differer du
#: centime par arrondi de ventilation; au-dela, c'est un chiffre a expliquer.
TOLERANCE = Decimal("0.01")


@dataclass(frozen=True)
class Egalite:
    """Le resultat d'une egalite, avec de quoi le citer dans un rapport."""

    controle: str
    etat: str
    moment: str
    motif: str
    attendu: Decimal | None = None
    constate: Decimal | None = None
    source_cle: str = "d05.10"

    def citation(self) -> str:
        """Le fondement, lu dans le registre et jamais recopie ici."""
        return source(self.source_cle).citation()

    def conclut(self) -> bool:
        """Seul `CONFORME` conclut. `INDETERMINE` n'est pas un feu vert."""
        return self.etat == CONFORME


def _compare(controle: str, moment: str, gauche: Decimal | None,
             droite: Decimal | None, manquant: str,
             source_cle: str = "d05.10") -> Egalite:
    if gauche is None or droite is None:
        return Egalite(controle, INDETERMINE, moment, manquant,
                       source_cle=source_cle)
    ecart = abs(gauche - droite)
    if ecart <= TOLERANCE:
        return Egalite(controle, CONFORME, moment,
                       "les deux totaux coincident", droite, gauche,
                       source_cle)
    return Egalite(
        controle, ECART, moment,
        "les deux presentations du meme total different de %s" % ecart,
        droite, gauche, source_cle)


def egalite_courantes(total_annexe3: Decimal | None,
                      total_annexe2_bloc: Decimal | None,
                      bloc_annexe2: str,
                      moment: str) -> Egalite:
    """`CTRL-A10-1` a l'approbation, `CTRL-A10-3` au vote du budget.

    **Une seule arithmetique pour deux controles**, parce que le decret pose la
    meme egalite aux deux moments. Les dupliquer aurait cree deux endroits ou
    la regle peut diverger.
    """
    controle = ("CTRL-A10-1" if moment == APPROBATION_DES_COMPTES
                else "CTRL-A10-3")
    if bloc_annexe2 != BLOC_COURANTES:
        return Egalite(
            controle, INDETERMINE, moment,
            "le total d'annexe 2 fourni n'est pas designe comme le bloc des "
            "operations courantes: l'annexe 2 en porte deux, et le texte ne "
            "dit pas lequel il vise - comparer au hasard produirait un ecart "
            "faux")
    return _compare(controle, moment, total_annexe3, total_annexe2_bloc,
                    "un des deux totaux d'operations courantes n'a pas ete lu")


def egalite_travaux_et_exceptionnelles(
        total_annexe4: Decimal | None,
        total_annexe2_bloc: Decimal | None,
        bloc_annexe2: str) -> Egalite:
    """`CTRL-A10-2`, exige a l'approbation des comptes seulement."""
    if bloc_annexe2 != BLOC_TRAVAUX_EXCEPTIONNELLES:
        return Egalite(
            "CTRL-A10-2", INDETERMINE, APPROBATION_DES_COMPTES,
            "le total d'annexe 2 fourni n'est pas designe comme le bloc des "
            "travaux de l'article 14-2 et operations exceptionnelles")
    return _compare(
        "CTRL-A10-2", APPROBATION_DES_COMPTES, total_annexe4,
        total_annexe2_bloc,
        "un des deux totaux de travaux et operations exceptionnelles n'a pas "
        "ete lu")


def egalite_solde_en_attente(total_colonne_e_annexe5: Decimal | None,
                             solde_compte_12_annexe1: Decimal | None) -> Egalite:
    """`CTRL-A5-1`: le solde en attente sur travaux, vu de deux endroits.

    L'annexe 5 le porte en colonne `E = D - C`, et sa note dit que *ce solde
    correspond au solde du compte 12 dans l'annexe n° 1*. Deux expressions du
    meme objet, qui coincident par construction.
    """
    return _compare(
        "CTRL-A5-1", APPROBATION_DES_COMPTES, total_colonne_e_annexe5,
        solde_compte_12_annexe1,
        "le solde en attente sur travaux n'a pas ete lu dans l'une des deux "
        "annexes",
        source_cle="d05.annexe2")


def toutes_les_egalites(
        *,
        total_annexe3_courantes: Decimal | None = None,
        total_annexe2_courantes: Decimal | None = None,
        total_annexe4_travaux: Decimal | None = None,
        total_annexe2_travaux: Decimal | None = None,
        total_colonne_e_annexe5: Decimal | None = None,
        solde_compte_12_annexe1: Decimal | None = None,
        moment: str = APPROBATION_DES_COMPTES) -> tuple[Egalite, ...]:
    """Les egalites exigibles AU MOMENT donne, et elles ne sont pas les memes.

    Au vote du budget previsionnel, le decret n'exige que l'egalite des
    operations courantes. Rendre les quatre a tous les moments inventerait des
    obligations, ce qui est le defaut symetrique de n'en verifier aucune.
    """
    courantes = egalite_courantes(
        total_annexe3_courantes, total_annexe2_courantes, BLOC_COURANTES,
        moment)
    if moment == VOTE_DU_BUDGET:
        return (courantes,)
    return (
        courantes,
        egalite_travaux_et_exceptionnelles(
            total_annexe4_travaux, total_annexe2_travaux,
            BLOC_TRAVAUX_EXCEPTIONNELLES),
        egalite_solde_en_attente(
            total_colonne_e_annexe5, solde_compte_12_annexe1),
    )


def la_plus_prudente(*egalites: Egalite) -> str:
    """L'etat d'ensemble: un `ECART` domine, et un `INDETERMINE` aussi.

    Composer en prenant le meilleur etat ferait disparaitre un controle non
    fait derriere trois controles reussis - c'est le motif mesure sous
    `RM-2026-0175` et grave en memoire: chainer des controles masque leur
    echec.
    """
    etats = {egalite.etat for egalite in egalites}
    if not etats:
        return INDETERMINE
    for pire in (ECART, INDETERMINE, CONFORME):
        if pire in etats:
            return pire
    return INDETERMINE
