# -*- coding: utf-8 -*-
"""Un comptage qui franchit la frontiere du viewmodel dit d'ou il vient.

`RM-2026-0134`, meme axe que `RM-2026-0075` - *d'ou vient ce nombre* - aux
sites que celui-la n'a pas traites. Le balayage avait trouve neuf sites; les
deux surfaces reellement affichees ont ete corrigees par `MontantLu`. Restaient
sept sites dans la charge utile `model.ux.comptes`, dont **trois `max()`
appliques a des quantites de sens different**.

**POURQUOI LE `max()` EST LA PIRE FORME SUR CET AXE.** Un `max()` entre deux
quantites qui ne mesurent pas la meme chose **ne rend pas un maximum, il rend
un nombre**. Et apres l'operation, la source gagnante est **irrecuperable**:
meme un lot futur ne pourra pas dire d'ou vient le chiffre affiche. Les trois
sites mesures le 2026-09-12:

- `invoice_total`: trois comptages de *factures* - clefs de pieces distinctes,
  compteur de la synthese, rapprochees plus non rapprochees;
- `invoice_matched`: deux notions de *rapproche* - pieces a preuve verifiee, et
  le compteur d'appariement de la synthese;
- `analyzed_posts_count`: **cinq** quantites, dont un nombre de lignes d'etat
  des depenses, un nombre d'ecritures, un nombre de categories **et
  `invoice_total` lui-meme** - donc un comptage de factures compare a des
  comptages de postes.

**L'AXE.** Ce qui VARIE: le nombre de sources disponibles, leur nom, celle qui
se trouve etre la plus grande sur une instance donnee. Ce qui reste INVARIANT:
**un nombre affiche repond a une question, et la source qui l'a produit fait
partie de la reponse.** **Hors des valeurs observees:** une source nouvelle
s'ajoute a la liste des candidats et se declare sous son propre nom; elle ne
se fait jamais passer pour une autre.

**LES NOMS NE COLLISIONNENT PAS AVEC CEUX DES MONTANTS, et il a fallu une
suite rouge pour l'apprendre.** Ce module avait d'abord nomme ses constantes
`SOURCE_*`, dont `SOURCE_FACTURES` et `SOURCE_AUCUNE`, ainsi qu'un
`libelle_source` - **trois collisions avec `_montant_source`**. Comme les
fragments recoivent ces noms par un `from ._runtime import *`, mes constantes
**ecrasaient** celles des montants la ou les deux etaient importees, et
`test_total_charges_provenance` a echoue en lisant `invoice` la ou il
attendait `factures`. J'avais recree, en une heure, le defaut que
`RM-2026-0106` venait de retirer: deux definitions concurrentes pour une seule
notion. Le prefixe `COMPTAGE_` porte desormais la distinction dans le nom -
**ce ne sont pas des sources de montant, ce sont des manieres de compter** - et
`libelle_comptage` ne peut plus etre pris pour `libelle_source`.

**CE MODULE N'INVENTE PAS UNE CONVENTION, il en generalise une.** `MontantLu`
porte deja `valeur`, `source`, `demande` pour les MONTANTS, avec `repond` et
`substitue`. Ici la meme forme s'applique aux COMPTAGES, dont les sources ne
sont pas celles d'un montant - d'ou un type distinct plutot qu'un champ
detourne.

**CE QUE CE MODULE NE FAIT PAS.** Il ne choisit pas a la place du produit: il
garde le `max()` comme regle de composition, parce que le changer deplacerait
des chiffres affiches sans qu'aucune mesure ne dise dans quel sens. Il rend la
source **recuperable**, et il rend la DIVERGENCE visible - c'est ce qui manque
aujourd'hui, et c'est ce qui permettra de trancher plus tard sur des faits.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Les sources de comptage rencontrees dans le perimetre comptable. Ce ne sont
#: pas des modalites d'une instance: chacune nomme une MANIERE DE COMPTER, et
#: c'est cette maniere que l'appelant doit pouvoir citer.
COMPTAGE_PIECES_DISTINCTES = "pieces_distinctes"
COMPTAGE_SYNTHESE = "synthese"
COMPTAGE_RAPPROCHEMENTS = "rapprochements"
COMPTAGE_PREUVES_VERIFIEES = "preuves_verifiees"
COMPTAGE_LIGNES_ETAT_DEPENSES = "lignes_etat_depenses"
COMPTAGE_ECRITURES = "ecritures"
COMPTAGE_CATEGORIES = "categories"
COMPTAGE_FACTURES = "factures"
COMPTAGE_AUCUN = ""

_LIBELLES = {
    COMPTAGE_PIECES_DISTINCTES: "pieces distinctes",
    COMPTAGE_SYNTHESE: "compteur de la synthese",
    COMPTAGE_RAPPROCHEMENTS: "rapprochements et non-rapprochements",
    COMPTAGE_PREUVES_VERIFIEES: "pieces a preuve verifiee",
    COMPTAGE_LIGNES_ETAT_DEPENSES: "lignes de l'etat des depenses",
    COMPTAGE_ECRITURES: "ecritures",
    COMPTAGE_CATEGORIES: "categories",
    COMPTAGE_FACTURES: "comptage de factures",
}


def libelle_comptage(source: str) -> str:
    """Le nom lisible d'une source, ou son identifiant technique en clair.

    Une source inconnue de l'enumeration se declare sous son propre nom plutot
    que de rendre une chaine vide, qui donnerait l'illusion d'une lecture
    directe. Meme regle que `_montant_source.libelle_comptage`.
    """
    if not source:
        return "aucune source"
    return _LIBELLES.get(source, source)


@dataclass(frozen=True)
class ComptageLu:
    """Un comptage, la source qui l'a produit, et celle qui repondrait.

    `candidats` garde TOUS les comptages proposes, avec leur source: c'est ce
    qui rend la composition reversible, alors qu'un `max()` nu efface tout sauf
    son resultat.
    """

    valeur: int = 0
    source: str = COMPTAGE_AUCUN
    demandee: str = COMPTAGE_AUCUN
    candidats: tuple[tuple[str, int], ...] = ()

    @property
    def repond(self) -> bool:
        """Vrai seulement si le nombre vient de la source demandee."""
        return bool(self.source) and self.source == self.demandee

    @property
    def substitue(self) -> bool:
        """Un nombre existe, il est juste pour ce qu'il compte, et il ne

        repond pas a la question posee. C'est l'etat exact du defaut.
        """
        return bool(self.source) and self.source != self.demandee

    @property
    def diverge(self) -> bool:
        """Les sources ne comptent pas la meme chose, et le disent.

        Sans cela, `max()` presente un desaccord comme un resultat.
        """
        valeurs = {valeur for _source, valeur in self.candidats}
        return len(valeurs) > 1

    @property
    def ecart(self) -> int:
        """De combien les sources se contredisent. Zero si elles s'accordent."""
        valeurs = [valeur for _source, valeur in self.candidats]
        return max(valeurs) - min(valeurs) if valeurs else 0

    def phrase(self) -> str:
        """Ce qu'un gabarit peut afficher sous le chiffre."""
        if not self.candidats:
            return "aucune source de comptage"
        base = "lu sur %s" % libelle_comptage(self.source)
        if not self.diverge:
            return base
        return "%s; les sources se contredisent de %d (%s)" % (
            base, self.ecart,
            ", ".join("%s %d" % (libelle_comptage(s), v)
                      for s, v in self.candidats))


def le_plus_grand(demandee: str, *candidats: tuple[str, int]) -> ComptageLu:
    """Le plus grand comptage propose, **en gardant qui l'a produit**.

    La regle de composition reste celle du produit - le plus grand l'emporte -
    parce que la changer deplacerait des chiffres affiches sans qu'aucune
    mesure ne dise dans quel sens. Ce qui change est que la source survit.

    Les candidats a valeur negative sont refuses: un comptage negatif n'est pas
    un comptage, et l'accepter ferait gagner un zero par defaut.
    """
    retenus = tuple((str(source), int(valeur))
                    for source, valeur in candidats if int(valeur) >= 0)
    if not retenus:
        return ComptageLu(0, COMPTAGE_AUCUN, demandee, ())
    # `max` sur la valeur seule: a egalite, le PREMIER candidat gagne, donc
    # l'ordre d'appel exprime la preference de l'appelant au lieu de dependre
    # du nom des sources.
    source, valeur = max(retenus, key=lambda couple: couple[1])
    for candidat_source, candidat_valeur in retenus:
        if candidat_valeur == valeur:
            source, valeur = candidat_source, candidat_valeur
            break
    return ComptageLu(valeur, source, demandee, retenus)
