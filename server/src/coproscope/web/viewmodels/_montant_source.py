"""Un montant qui porte sa provenance, ou qui refuse de se rendre. Lot `RM-2026-0075`.

======================================================================
L'axe: d'ou vient ce nombre
======================================================================

Le defaut mesure le 2026-09-04 n'est pas une erreur de calcul. Chaque source
prise separement rendait le total qu'elle savait rendre. Le defaut est que le
resultat traversait la frontiere du module **sans sa provenance**: un `float`
nu, accompagne au mieux d'un booleen de presence. Un booleen distingue *pas de
nombre* de *un nombre*; il ne distingue jamais *quel* nombre.

L'ecran affichait donc `24 397 501,24` sous le libelle `Total charges /
Exercice 2025` alors que la valeur reelle est `357 493,10`, facteur 68. La
page signalait bien `ETAT_DEPENSES_A_FOURNIR` plus bas, mais un chiffre de tete
se lit comme un fait, et aucune mention plus bas ne defait cela.

*Invariant le long de l'axe*: **une reponse ne vaut que par la question a
laquelle elle repond.** Un module qui ne peut pas nommer la source d'un nombre
ne doit pas rendre ce nombre sous le libelle de la question posee. La regle ne
depend d'aucun cabinet, d'aucune annee et d'aucun format: elle porte sur la
frontiere entre le calcul et l'affichage.

*Ce que le code en fait*: un montant traverse cette frontiere sous la forme
`MontantLu`, qui transporte ensemble la valeur, la source qui l'a produite et
la source qui aurait repondu a la question. Quand les deux different, la valeur
existe toujours - elle n'est pas detruite - mais elle **change de libelle**.
C'est la correction exacte du defaut constate: le substitut etait affiche sous
le libelle du demande.

*Hors des valeurs observees*: une source inconnue de cette enumeration se
declare avec son identifiant technique en clair plutot que de se faire passer
pour une autre. `libelle_source` d'une source non repertoriee rend
l'identifiant tel quel, jamais une chaine vide qui donnerait l'illusion d'une
lecture directe.

======================================================================
Pourquoi une forme et non un correctif ponctuel
======================================================================

Le meme motif a ete releve a neuf endroits du perimetre comptable, dont trois
`max()` appliques a des quantites semantiquement differentes - un `max()` est
la pire forme sur cet axe, parce que la source gagnante n'est pas seulement
non documentee, elle est **irrecuperable apres coup**.

La forme retenue existe deja dans le depot: `controle_gouvernance_view` rend un
montant comme un dictionnaire portant `valeur`, `etat`, `lu_sur` et `verdict`,
et son gabarit affiche la provenance sous le chiffre. Ce module n'invente donc
pas une convention, il en generalise une.
"""

from __future__ import annotations

from dataclasses import dataclass

# Sources connues du total des charges, du plus direct au plus reconstruit.
SOURCE_ETAT_DEPENSES = "expense_statement"
SOURCE_GRAND_LIVRE = "ledger"
SOURCE_FACTURES = "invoice"
SOURCE_AUCUNE = ""

# Libelles humains. La cle est l'identifiant technique porte par `MontantLu`.
_LIBELLES_SOURCE = {
    SOURCE_ETAT_DEPENSES: "etat des depenses",
    SOURCE_GRAND_LIVRE: "grand livre reconstitue",
    SOURCE_FACTURES: "factures rapprochees",
}

# Ce que l'ecran affiche quand la source demandee n'a rien rendu. Le texte est
# impose par `RM-2026-0075`: il nomme la piece manquante, il ne dit pas
# seulement que le calcul a echoue.
NON_CALCULABLE = "non calculable - etat des depenses non charge"


def libelle_source(source: str) -> str:
    """Le nom lisible d'une source, ou son identifiant technique s'il est inconnu.

    Ne rend jamais une chaine vide pour une source non repertoriee: un libelle
    vide se lirait comme une lecture directe et reintroduirait le defaut que ce
    module corrige.
    """

    if not source:
        return "aucune source"
    return _LIBELLES_SOURCE.get(source, source)


@dataclass(frozen=True)
class MontantLu:
    """Un montant, la source qui l'a produit, et la source qui repondrait.

    `valeur` peut etre `None`: c'est le cas ou aucune source n'a rien rendu.
    `source` est vide dans ce cas. `demande` nomme toujours la source qui
    repondrait a la question posee, meme lorsqu'elle est absente - c'est ce qui
    permet a l'appelant de dire *ce qui manque* et non seulement *que ca
    manque*.
    """

    valeur: float | None = None
    source: str = SOURCE_AUCUNE
    demande: str = SOURCE_ETAT_DEPENSES
    lignes: int = 0

    @property
    def repond(self) -> bool:
        """Vrai seulement si un nombre existe ET vient de la source demandee."""

        return self.valeur is not None and self.source == self.demande

    @property
    def substitue(self) -> bool:
        """Vrai quand un nombre existe mais vient d'une autre source.

        C'est l'etat exact du defaut `RM-2026-0075`: il y a un nombre, il est
        juste pour ce qu'il mesure, et il ne repond pas a la question posee.
        """

        return self.valeur is not None and self.source != self.demande

    @property
    def lu_sur(self) -> str:
        """Le nom lisible de la source effective."""

        return libelle_source(self.source)

    @property
    def attendu_sur(self) -> str:
        """Le nom lisible de la source qui repondrait a la question."""

        return libelle_source(self.demande)

    def libelle(self, formate) -> str:
        """Le libelle a afficher sous le nom de la question posee.

        `formate` met en forme un nombre. La valeur n'est rendue que si elle
        repond; sinon l'ecran recoit `NON_CALCULABLE`, jamais un nombre.
        """

        if self.repond:
            return formate(self.valeur)
        return NON_CALCULABLE

    def mention_substitut(self, formate) -> str:
        """Ce que le substitut vaut, sous SON propre nom. Vide s'il n'y en a pas.

        Le nombre n'est pas detruit: il est renomme. Un total de grand livre
        reconstitue reste une information utile a qui sait ce qu'il regarde -
        il n'est faux que sous le libelle de l'etat des depenses.
        """

        if not self.substitue:
            return ""
        return f"{formate(self.valeur)} lu sur {self.lu_sur}"

    def as_dict(self, formate) -> dict[str, object]:
        """La forme rendue au gabarit, calquee sur `controle_gouvernance_view`."""

        return {
            "valeur": self.libelle(formate),
            "repond": self.repond,
            "substitue": self.substitue,
            "lu_sur": self.lu_sur if self.valeur is not None else "",
            "attendu_sur": self.attendu_sur,
            "lignes": self.lignes,
            "substitut": self.mention_substitut(formate),
        }
