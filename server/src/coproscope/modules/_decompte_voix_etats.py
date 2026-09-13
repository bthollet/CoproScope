"""Les etats rendus par le decompte des voix, et le verdict qui les porte.

Extrait de `_decompte_voix` le 2026-09-04 pour tenir la limite de taille du
depot. Aucun de ces etats n'est un pourcentage tant que l'assiette n'est pas
nommee, et cinq d'entre eux sont des refus assumes: **un refus qui nomme la
donnee manquante est plus utile qu'un pourcentage tire d'un denominateur
d'imprimeur.**
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

#: Le seuil de la majorite annoncee est atteint sur l'assiette de cette
#: majorite. Quand l'issue proclamee au proces-verbal est fournie et concorde,
#: `CONFIRMEE` porte bien une confrontation; quand elle n'est pas fournie, le
#: module ne peut pas confronter et l'etat ne dit que le seuil.
ETAT_ADOPTEE_CONFIRMEE = "ADOPTEE_CONFIRMEE"

#: Le seuil n'est pas atteint et la resolution est annoncee rejetee: les
#: chiffres confirment le proces-verbal.
ETAT_REJET_CONFIRME = "REJET_CONFIRME"

#: Le seuil de la majorite annoncee n'est pas atteint, mais le projet a
#: recueilli au moins le tiers des voix de tous les coproprietaires: la
#: passerelle de l'article 25-1 explique une adoption, a condition qu'un second
#: vote ait eu lieu.
ETAT_PASSERELLE_25_1_REQUISE = "PASSERELLE_25_1_REQUISE"

#: Un second vote a la majorite de l'article 24 a ete applique alors que le
#: premier vote n'a pas recueilli le tiers des voix de tous les coproprietaires:
#: la passerelle n'etait pas ouverte, la loi interdisait ce second vote.
ETAT_PASSERELLE_25_1_NON_OUVERTE = "PASSERELLE_25_1_NON_OUVERTE"

#: Proclamee adoptee alors que le seuil de la majorite annoncee n'est pas
#: atteint - et, sous l'article 25, que la passerelle ne l'est pas non plus.
ETAT_DECOMPTE_INSUFFISANT = "ADOPTEE_MAIS_DECOMPTE_INSUFFISANT"

#: Le seuil est atteint et le proces-verbal conclut au rejet. C'est le constat
#: le plus utile qu'un outil de controle puisse produire, et il n'existait
#: jusqu'ici sous aucune majorite.
ETAT_ISSUE_CONTREDITE = "ISSUE_CONTREDITE"

#: Les nombres lus ne peuvent pas etre tous vrais en meme temps. Ce n'est pas
#: une donnee manquante: c'est une donnee fausse, et le pourcentage qu'elle
#: aurait produit aurait eu l'air normal.
ETAT_DECOMPTE_INCOHERENT = "DECOMPTE_INCOHERENT"

#: Une valeur de voix est **ecrite** et n'est pas un nombre de voix. Ce n'est
#: ni une absence, ni une incoherence: c'est un refus de lecture, et il doit
#: rester distinct des deux. Avant qu'il existe, ces valeurs prenaient trois
#: chemins tous mauvais - une `ValueError` sur la chaine vide, une `TypeError`
#: sur un total ecrit en chaine, et une troncature silencieuse d'un nombre a
#: virgule. Le motif nomme le champ et restitue la valeur lue.
ETAT_DECOMPTE_ILLISIBLE = "DECOMPTE_ILLISIBLE"

#: Il manque une donnee sans laquelle le controle n'a pas d'objet.
ETAT_ASSIETTE_INDETERMINEE = "ASSIETTE_INDETERMINEE"

#: Le proces-verbal enonce que la question n'a pas ete mise aux voix. L'absence
#: de decompte est alors constatee sur le document, et n'est pas une
#: irregularite du syndic.
ETAT_SANS_VOTE = "SANS_VOTE_ENONCE"

#: Le proces-verbal ne publie pas les voix alors qu'un vote a eu lieu ou que
#: rien ne dit le contraire. C'est une irregularite au regard de l'article 17 du
#: decret, et c'est surtout l'aveu que le controle ne peut pas etre conduit.
ETAT_DECOMPTE_ABSENT = "DECOMPTE_ABSENT"


@dataclass
class Verdict:
    """Ce que l'ecran a le droit d'afficher pour une resolution.

    `pourcentage` vaut `None` tant que l'assiette n'est pas nommee. C'est la
    promesse centrale du module: **aucun pourcentage ne sort d'une assiette
    inconnue.**

    `denominateur_ecrit` est restitue par **tous** les verdicts, y compris les
    refus. Mesure du 2026-09-04 sur la piece etalon: sur les 24 resolutions qui
    ne rendaient aucun chiffre, 12 portaient un denominateur imprime
    correctement extrait, que les returns de refus jetaient. Il n'est pas une
    assiette et ne fonde aucun pourcentage; il reste une piste que le lecteur a
    le droit de voir.
    """

    etat: str
    assiette: Optional[str] = None
    base_retenue: Optional[int] = None
    seuil_requis: Optional[int] = None
    voix_pour: Optional[int] = None
    pourcentage: Optional[float] = None
    motif: str = ""
    constats: list = field(default_factory=list)
    sources: tuple = ()
    denominateur_ecrit: Optional[int] = None

    @property
    def affichable(self) -> bool:
        """Un pourcentage n'est affichable que si une base a ete nommee."""

        return self.pourcentage is not None
