"""Confronte ce qui a ete observe a ce que le decret exige.

Sert `RM-2026-0091`. Ce module ne lit aucune page, n'ouvre aucun fichier et
n'emet aucune requete: il joint trois choses deja etablies ailleurs.

    ce qui a ete vu           (un releve, `_extranet_releve`)
  x ou chaque obligation vit  (un rattachement, DECLARE par un humain)
  x combien il en faut        (un attendu, du texte ou declare)
  ----------------------------------------------------------------
  = un etat par obligation, et jamais un verdict

======================================================================
Le fait qui a decide de la conception
======================================================================

Un editeur ne range pas ses pieces par obligation legale, et il n'a aucune
raison de le faire. Chez l'editeur observe le 2026-09-04, huit rubriques
d'interface portent dix-huit obligations, et la relation n'est ni injective ni
surjective:

- `CON` porte **quatre** obligations - assurances, contrats et marches en
  cours, contrats d'entretien, contrat de syndic;
- les releves du compte separe sont ranges dans **Documents divers**, la
  categorie fourre-tout;
- `REU` ne porte **aucune** obligation de la liste minimale.

Consequence directe, et c'est la partie qu'il serait facile de rater: **un
compte de pieces n'est attribuable a une obligation que si l'emplacement qui la
sert ne sert qu'elle.** Douze pieces dans `CON` ne disent pas combien sont des
assurances. Ce module le mesure au lieu de le supposer, et refuse de calculer
un ecart quand l'emplacement est partage - un ecart faux serait pire qu'une
absence d'ecart, parce qu'il serait chiffre.

======================================================================
Ce qui est declare, et pourquoi ce n'est pas un aveu de faiblesse
======================================================================

Le rattachement obligation -> emplacement **n'est pas observable**: aucune page
d'extranet ne cite le decret. Le deviner reviendrait a coder les huit modalites
d'un editeur, ce que la regle du depot interdit, et a casser au deuxieme
syndic.

Il est donc declare, exactement comme le nombre de pieces attendu l'est deja.
Un editeur sans rattachement declare ne produit **aucun manquement**: les dix-
huit obligations ressortent `NON_RATTACHE`, qui veut dire *je ne sais pas ou
cette obligation est servie ici* et jamais *elle n'est pas servie*.

======================================================================
La limite de la garantie, et elle est conditionnelle
======================================================================

Le partage d'un emplacement est mesure **sur la declaration fournie**, pas sur
la realite de l'extranet. Declarer que la rubrique des contrats sert les
assurances, et rien d'autre, alors qu'elle sert aussi trois autres obligations,
donne un ecart chiffre sur un emplacement que le module croit exclusif.

Ce n'est pas rattrapable ici: le module ne voit que ce qu'on lui dit. La
conclusion pratique est que **la valeur d'un ecart chiffre depend de la
completude de la declaration**, et l'ecran doit le rappeler la ou il l'affiche.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

from ._extranet_schema import RUBRIQUE_PARCOURUE
from ._extranet_referentiel import (
    ATTENDU_DECLARE,
    ATTENDU_TEXTE,
    ATTENDUS_AVEC_RESERVE,
    ATTENDUS_NON_COMPTABLES,
    INDETERMINE,
    LISTE_MINIMALE,
    NON_PARCOURUE,
    NON_RATTACHE,
    NON_SERVI,
    SANS_OBJET,
    SERVI_EN_APPARENCE,
    Rubrique,
    dedupliquer,
    rubrique as _rubrique,
)

#: Pourquoi un compte n'est pas attribuable a une obligation.
COMPTE_PARTAGE = "EMPLACEMENT_PARTAGE"
COMPTE_ATTRIBUABLE = "EMPLACEMENT_EXCLUSIF"
COMPTE_ABSENT = "AUCUN_EMPLACEMENT"
#: Ajoute le 2026-09-07 apres une verification adverse. Le module refusait de
#: chiffrer un ecart sur un emplacement PARTAGE mais l'acceptait sur une
#: couverture INCOMPLETE - or c'est le meme mode de defaillance: dans les deux
#: cas le compte observe ne represente pas ce qu'il pretend representer.
COMPTE_INCOMPLET = "COUVERTURE_INCOMPLETE"


def _qui_partage(
    rattachements: Mapping[str, Sequence[str]], codes: Sequence[str], sauf: str
) -> list[str]:
    """Les autres obligations servies aux memes emplacements.

    Dire *cet emplacement sert plusieurs obligations* sonne comme une excuse.
    Dire lesquelles - assurances, contrats en cours, entretien, contrat de
    syndic - se lit comme de l'honnetete. Constat d'une qualification novice du
    2026-09-07, qui trouvait la phrase du brouillon meilleure que celle du
    produit.
    """
    voisines = []
    for identifiant, autres in rattachements.items():
        if identifiant == sauf:
            continue
        if any(c in codes for c in autres):
            voisines.append(identifiant)
    return voisines


def _emplacements_partages(rattachements: Mapping[str, Sequence[str]]) -> set[str]:
    """Les codes d'editeur qui servent plus d'une obligation.

    Mesure, pas hypothese: la meme declaration qui dit ou vivent les
    obligations dit aussi lesquelles se partagent un emplacement.
    """
    compte: Counter[str] = Counter()
    for codes in rattachements.values():
        for code in set(codes):
            compte[code] += 1
    return {code for code, n in compte.items() if n > 1}


def _observation(rubriques: Iterable[Mapping[str, Any]]) -> dict[str, dict]:
    """Indexe par code d'editeur, qu'on vienne d'un releve ou du coffre.

    Deux formes portent la meme chose et ne se ressemblent pas: un releve frais
    du plugin dit `presente` et porte ses pieces en liste; un passage relu du
    coffre dit `etat` et porte un compte deja fait. Les distinguer ici evite de
    convertir en amont, et surtout evite qu'un appelant lise un compte absent
    comme un zero.

    Une rubrique absente de l'index n'a pas ete vue; une rubrique vue mais non
    parcourue mene a `NON_PARCOURUE`. Ni l'une ni l'autre ne mene a une
    absence: c'est la regle de couverture du lot.
    """
    vu: dict[str, dict] = {}
    for r in rubriques:
        code = str(r.get("rubrique_code", "") or "").strip()
        if not code:
            continue
        if "etat" in r:  # forme du coffre
            parcourue = r.get("etat") == RUBRIQUE_PARCOURUE
            nb = int(r.get("nb_pieces") or 0)
        else:  # forme du releve
            parcourue = bool(r.get("presente", False))
            pieces = r.get("pieces")
            if pieces is None:
                pieces = [l for l in (r.get("lignes") or []) if l.get("a_une_facture")]
            nb = len(pieces or [])
        vu[code] = {"parcourue": parcourue, "nb_pieces": nb}
    return vu


def _attendu_de(
    obligation: Rubrique, attendus: Mapping[str, int]
) -> tuple[int | None, str]:
    """Le nombre attendu, et d'ou il vient.

    Un attendu du texte n'est pas saisissable: on ne laisse pas declarer cinq
    proces-verbaux la ou l'article en exige trois. Un attendu declare n'est pas
    devinable: personne d'autre que l'occupant ne sait combien d'actes ont ete
    publies pour son immeuble.
    """
    if obligation.attendu_source == ATTENDU_TEXTE and obligation.attendu is not None:
        return obligation.attendu, ATTENDU_TEXTE
    if obligation.attendu_source in ATTENDUS_NON_COMPTABLES:
        # L'observation ne sait pas compter cette unite - une duree, une serie
        # sans trou, des justifications qui peuvent tenir dans un seul
        # document. Accepter un attendu declare ici produirait un ecart chiffre
        # sur un comptage qui ne mesure pas la bonne chose. La docstring du
        # module annoncait deja cette degradation; le code ne la faisait pas.
        return None, obligation.attendu_source
    declare = attendus.get(obligation.identifiant)
    if declare is None or str(declare).strip() == "":
        # Un champ vide veut dire *je ne sais pas*, et non zero. Lever ici
        # ferait planter un ecran sur une saisie effacee - et le cote
        # navigateur, lui, se gardait deja de la chaine vide: deux lectures qui
        # divergent sur une entree aussi banale finissent par diverger sur un
        # constat.
        return None, obligation.attendu_source
    try:
        return int(float(declare)), ATTENDU_DECLARE
    except (TypeError, ValueError):
        return None, obligation.attendu_source


def etat_par_obligation(
    releve: Mapping[str, Any],
    *,
    rattachements: Mapping[str, Sequence[str]] | None = None,
    attendus: Mapping[str, int] | None = None,
    sans_objet: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Un etat par obligation de la liste minimale.

    Aucun verdict de conformite n'est produit ici, et ce n'est pas une lacune:
    `CONFORME` exige de **lire la piece**, ce que l'observation ne fait pas. Le
    critere complementaire voyage donc avec chaque etat, en clair, pour que le
    lecteur sache ce qui reste a verifier a la main.
    """
    rattachements = dict(rattachements or {})
    attendus = dict(attendus or {})
    # Un identifiant inconnu dans `sans_objet` etait avale en silence: une
    # lettre en moins - `EXT-B-3` pour `EXT-B-03` - et l'obligation qu'on
    # croyait ecartee produisait un manquement chiffre contre un syndic
    # irreprochable. `rubrique()` existe et leve une erreur nommee: on s'en
    # sert.
    dispenses = set()
    for identifiant in sans_objet:
        _rubrique(identifiant)
        dispenses.add(identifiant)
    vu = _observation(releve.get("rubriques") or ())
    partages = _emplacements_partages(rattachements)

    sortie: list[dict[str, Any]] = []
    for obligation in LISTE_MINIMALE:
        ligne: dict[str, Any] = {
            "identifiant": obligation.identifiant,
            "college": obligation.college,
            "intitule": obligation.intitule,
            "fondement": obligation.citation(),
            "reste_a_verifier": obligation.critere_complementaire,
            "emplacements": list(rattachements.get(obligation.identifiant, ())),
        }

        if obligation.identifiant in dispenses:
            ligne["etat"] = SANS_OBJET
            sortie.append(ligne)
            continue

        # Nettoyage de la declaration humaine. Un code vide ou entoure
        # d'espaces se serait deguise en *non parcourue* - donc *je n'ai pas
        # regarde* - alors que c'est *je ne sais pas ou c'est servi*. Et un
        # code declare deux fois aurait double le compte observe, ce qui efface
        # un manquement reel sans aucune alerte.
        codes = []
        for brut in ligne["emplacements"]:
            propre = str(brut or "").strip()
            if propre and propre not in codes:
                codes.append(propre)
        ligne["emplacements"] = codes
        if not codes:
            ligne["etat"] = NON_RATTACHE
            ligne["compte"] = COMPTE_ABSENT
            sortie.append(ligne)
            continue

        parcourus = [c for c in codes if vu.get(c, {}).get("parcourue")]
        if not parcourus:
            ligne["etat"] = NON_PARCOURUE
            ligne["compte"] = COMPTE_ABSENT
            sortie.append(ligne)
            continue

        observe = sum(vu[c]["nb_pieces"] for c in parcourus)
        ligne["observe"] = observe
        ligne["emplacements_parcourus"] = parcourus
        if len(parcourus) < len(codes):
            ligne["emplacements_non_parcourus"] = [c for c in codes if c not in parcourus]

        partage = any(c in partages for c in parcourus)
        incomplet = len(parcourus) < len(codes)
        if partage:
            ligne["compte"] = COMPTE_PARTAGE
        elif incomplet:
            ligne["compte"] = COMPTE_INCOMPLET
        else:
            ligne["compte"] = COMPTE_ATTRIBUABLE
        ligne["etat"] = SERVI_EN_APPARENCE if observe else NON_SERVI
        if obligation.condition:
            ligne["condition"] = obligation.condition

        attendu, origine = _attendu_de(obligation, attendus)
        if attendu is not None:
            ligne["attendu"] = attendu
            ligne["attendu_source"] = origine
            if ligne["compte"] == COMPTE_ATTRIBUABLE:
                ligne["ecart"] = max(0, attendu - observe)
                reserve = ATTENDUS_AVEC_RESERVE.get(obligation.attendu_source)
                if reserve:
                    # Le compte est juste, il ne dit simplement pas tout. Le
                    # taire laisserait croire qu'un ecart nul vaut conformite.
                    ligne["reserve_sur_le_compte"] = reserve
            elif partage:
                # Un ecart calcule sur un emplacement partage serait un chiffre
                # faux, et un chiffre faux est plus nuisible qu'une absence de
                # chiffre: il se cite.
                voisines = _qui_partage(
                    rattachements, parcourus, obligation.identifiant
                )
                noms = [_rubrique(v).intitule for v in voisines]
                ligne["partage_avec"] = voisines
                detail = (
                    " Cette rubrique sert aussi: " + "; ".join(noms) + "."
                    if noms else ""
                )
                ligne["ecart_non_calculable"] = (
                    f"On ne peut pas dire combien des {observe} pieces vues "
                    f"relevent de cette obligation." + detail
                )
            else:
                # La regle de couverture du lot, appliquee a l'ecart. Chiffrer
                # un manque sur une rubrique qu'on n'a pas ouverte revient a
                # compter comme absentes des pieces qu'on n'a pas regardees.
                manquants = ", ".join(c for c in codes if c not in parcourus)
                ligne["ecart_non_calculable"] = (
                    "Une partie des emplacements n'a pas ete parcourue "
                    f"({manquants}): le compte observe est incomplet."
                )
        sortie.append(ligne)
    return sortie


def manques(etats: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Les obligations dont il manque des pieces, deduplication faite.

    Le referentiel impose la deduplication: un contrat d'entretien etant aussi
    un contrat en cours, une seule piece absente compterait sinon deux
    manquements. Un compte gonfle detruit la credibilite de celui qui s'en sert
    devant un syndic, ce qui est l'inverse du but poursuivi.

    **Une obligation que le texte conditionne ne devient un manque que si
    l'humain a declare un attendu.** Sans cela, *je ne sais pas combien il en
    faut* se transformait en manquement - alors que le module distingue partout
    ailleurs *je n'ai pas vu* de *il n'y a rien*.
    """
    # Un attendu declare a ZERO veut dire *aucune piece attendue ici*: c'est un
    # renseignement, pas une absence de renseignement. Zero observe sur zero
    # attendu est donc satisfait, et `NON_SERVI` seul ne suffit pas a conclure.
    candidats = set()
    for e in etats:
        # Une obligation que le texte CONDITIONNE, et dont rien n'a ete vu, ne
        # devient jamais un manque. La condition - un fonds de travaux, un
        # compte separe, des actes publies - ne s'observe pas: seul l'occupant
        # la connait.
        #
        # La preuve que la condition s'applique est **la presence d'au moins une
        # piece**: on ne sert pas la part d'un fonds de travaux qui n'existe
        # pas. Des qu'il y en a une, l'ecart redevient un constat.
        if e.get("condition") and not e.get("observe", 0):
            continue
        if e.get("ecart", 0) > 0:
            candidats.add(e["identifiant"])
            continue
        if e.get("etat") != NON_SERVI:
            continue
        attendu = e.get("attendu")
        if attendu is not None:
            if attendu <= e.get("observe", 0):
                continue
            candidats.add(e["identifiant"])
            continue
        # Aucun attendu, et le texte CONDITIONNE l'obligation. *Je ne sais pas
        # combien il en faut* + *le texte ne la doit pas toujours* ne font pas
        # un manquement: une copropriete sans fonds de travaux et sans compte
        # separe recoltait ainsi deux lignes rouges contre un syndic
        # irreprochable. Mesure du 2026-09-07 sur un second cabinet.
        if e.get("condition"):
            continue
        candidats.add(e["identifiant"])
    gardes = dedupliquer(candidats)
    return [e for e in etats if e["identifiant"] in gardes]


def resume(etats: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """De quoi tenir un bandeau: des comptes, et ce qui n'a pas ete regarde."""
    par_etat: Counter[str] = Counter(e.get("etat", INDETERMINE) for e in etats)
    return {
        "obligations": len(etats),
        "par_etat": dict(par_etat),
        "manques": len(manques(etats)),
        "non_rattachees": par_etat.get(NON_RATTACHE, 0),
        "non_parcourues": par_etat.get(NON_PARCOURUE, 0),
    }
