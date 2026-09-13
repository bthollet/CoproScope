"""Famille B: contenu et arithmetique du budget previsionnel.

Perimetre de l'article 44, nomenclature, egalite d'annexes, planchers et
plafonds chiffres. Voir `docs/grille_budget_previsionnel_2026-09-04.md`.
"""

from __future__ import annotations

from . import _budget_previsionnel_nomenclature as N
from ._budget_previsionnel_modele import (
    A_VERIFIER_HUMAIN,
    CONFORME,
    Constat,
    ECART,
    INAPPLICABLE,
    Dossier,
    manquantes,
)
from ._budget_previsionnel_socle import _TOLERANCE, _constat, _mois_ecoules

# --------------------------------------------------------------------------
# Famille B - contenu et arithmetique du budget previsionnel
# --------------------------------------------------------------------------

B1 = "Aucune depense de l'article 44 ne figure au budget previsionnel."


def b1_perimetre_article_44(dossier: Dossier) -> Constat:
    cles = ("loi.14-1", "d67.44", "d05.2", "d05.9")
    limite = (
        "Ne prouve rien sur la qualification des lignes retenues. La frontiere "
        "entre la maintenance, qui est au budget, et la conservation ou "
        "l'entretien de l'article 44 1., qui n'y est pas, se juge sur la nature "
        "des travaux, pas sur un numero de compte. Une facture de reprise de "
        "toiture imputee en 615 passe ce controle."
    )
    lignes = dossier.budget.lignes
    if not lignes:
        return _constat(
            "B-1", B1, INAPPLICABLE,
            "Aucune ligne de budget fournie.", cles, limite,
            entrees_manquantes=("budget.lignes",),
        )
    if all(ligne.montant is None for ligne in lignes):
        # Des lignes sans montant ne prouvent pas un perimetre propre: elles
        # prouvent qu'on n'a pas lu les montants.
        return _constat(
            "B-1", B1, INAPPLICABLE,
            "Lignes de budget sans aucun montant lu.", cles, limite,
            entrees_manquantes=("budget.lignes[].montant",),
        )
    exclus: list[str] = []
    indetermines: list[str] = []
    for ligne in lignes:
        if ligne.montant in (None, 0):
            continue
        compte = N.normaliser(ligne.compte_brut)
        if N.hors_budget_previsionnel(compte):
            exclus.append(f"{ligne.compte_brut} -> {compte}")
        elif N.indetermine_au_budget(compte):
            indetermines.append(f"{ligne.compte_brut} -> {compte}")
    if exclus:
        return _constat(
            "B-1", B1, ECART,
            "Comptes de charges pour travaux ou operations exceptionnelles "
            f"portes au budget previsionnel: {', '.join(exclus)}.",
            cles, limite,
        )
    if indetermines:
        return _constat(
            "B-1", B1, A_VERIFIER_HUMAIN,
            "Comptes de la classe 66 portes au budget previsionnel: "
            f"{', '.join(indetermines)}. Les deux cabinets mesures les rangent "
            "differemment et le modele d'annexe 2 qui trancherait n'est pas "
            "reproduit sur Legifrance.",
            cles, limite,
        )
    return _constat(
        "B-1", B1, CONFORME,
        "Aucun compte de la classe 67 ou 68 au budget previsionnel.",
        cles, limite,
    )


B2 = "Tout compte porte au budget appartient a la nomenclature ou en est une subdivision."


def b2_nomenclature(dossier: Dossier) -> Constat:
    cles = ("a05.6", "a05.7", "a05.8")
    limite = (
        "Ne prouve pas que le libelle soit exact ni que l'imputation soit "
        "juste. L'article 8 autorisant toute subdivision necessaire, un numero "
        "inconnu rattachable par prefixe est licite: le controle ne signale que "
        "ce qui ne se rattache a rien."
    )
    lignes = dossier.budget.lignes
    if not lignes:
        return _constat(
            "B-2", B2, INAPPLICABLE,
            "Aucune ligne de budget fournie.", cles, limite,
            entrees_manquantes=("budget.lignes",),
        )
    orphelins = [ligne.compte_brut for ligne in lignes if N.normaliser(ligne.compte_brut) is None]
    if orphelins:
        return _constat(
            "B-2", B2, ECART,
            f"Numeros hors nomenclature et non rattachables: {', '.join(orphelins)}.",
            cles, limite,
        )
    return _constat(
        "B-2", B2, CONFORME,
        f"{len(lignes)} lignes rattachees a la nomenclature.", cles, limite,
    )


B3 = "Aucun compte retire de la nomenclature en vigueur n'est utilise."


def b3_compte_supprime(dossier: Dossier) -> Constat:
    cles = ("a05.7", "a05.8")
    limite = (
        "Ne prouve pas que l'operation soit irreguliere: seul le compte l'est. "
        "Et le controle ne couvre que les suppressions connues du module; une "
        "suppression posterieure a la version lue passerait inapercue."
    )
    lignes = dossier.budget.lignes
    if not lignes:
        return _constat(
            "B-3", B3, INAPPLICABLE,
            "Aucune ligne de budget fournie.", cles, limite,
            entrees_manquantes=("budget.lignes",),
        )
    supprimes = [
        f"{ligne.compte_brut} -> {N.normaliser(ligne.compte_brut)}"
        for ligne in lignes
        if N.est_supprime(N.normaliser(ligne.compte_brut))
    ]
    if supprimes:
        return _constat(
            "B-3", B3, ECART,
            f"Comptes supprimes de la nomenclature encore utilises: {', '.join(supprimes)}.",
            cles, limite,
        )
    return _constat("B-3", B3, CONFORME, "Aucun compte supprime utilise.", cles, limite)


B4 = "Le total des charges courantes de l'annexe 3 egale le total des charges de l'annexe 2."


def b4_egalite_annexes(dossier: Dossier) -> Constat:
    cles = ("d05.10", "d05.9", "d05.annexe2")
    limite = (
        "Ne porte que sur le vote du budget: l'annexe 4 n'y entre pas, l'article "
        "10 ne l'appelle que pour l'approbation des comptes. Et l'egalite porte "
        "sur deux totaux: deux ventilations fausses qui se compensent la "
        "passent."
    )
    a2 = dossier.annexes.total_charges_annexe2_courantes
    a3 = dossier.annexes.total_charges_annexe3_courantes
    absents = manquantes(
        annexes__total_charges_annexe2_courantes=a2,
        annexes__total_charges_annexe3_courantes=a3,
    )
    if absents:
        return _constat(
            "B-4", B4, INAPPLICABLE,
            "Totaux d'annexes non extraits.", cles, limite,
            entrees_manquantes=tuple(nom.replace("__", ".") for nom in absents),
        )
    ecart = round(abs(a2 - a3), 2)
    if ecart > _TOLERANCE:
        return _constat(
            "B-4", B4, ECART,
            f"Ecart de {ecart:.2f} entre le total de l'annexe 3 et celui de l'annexe 2.",
            cles, limite,
        )
    return _constat("B-4", B4, CONFORME, "Les deux totaux coincident.", cles, limite)


B5 = "La cotisation au fonds de travaux atteint le plancher legal."


def b5_plancher_fonds_travaux(dossier: Dossier) -> Constat:
    cles = ("loi.14-2-1", "loi.14-2", "loi.14-1")
    limite = (
        "Ne dit rien de l'exercice auquel le plancher se rapporte: l'article "
        "14-2-1 vise 'le budget previsionnel mentionne a l'article 14-1' sans "
        "designer l'exercice, et le module n'a pas a trancher ce que le texte "
        "laisse ouvert. Ne dit rien non plus du versement effectif sur le "
        "compte separe, qui releve de l'article 18."
    )
    copro = dossier.copropriete
    cotisation = copro.cotisation_fonds_travaux_votee
    budget = dossier.budget.total_charges
    absents = manquantes(
        copropriete__destination_habitation=copro.destination_habitation,
        copropriete__date_reception_travaux_construction=copro.date_reception_travaux_construction,
        copropriete__cotisation_fonds_travaux_votee=cotisation,
        budget__total_charges=budget,
        copropriete__plan_pluriannuel_adopte=copro.plan_pluriannuel_adopte,
    )
    if absents:
        return _constat(
            "B-5", B5, INAPPLICABLE,
            "Contexte du fonds de travaux incomplet.", cles, limite,
            entrees_manquantes=tuple(nom.replace("__", ".") for nom in absents),
        )
    if not copro.destination_habitation:
        return _constat(
            "B-5", B5, INAPPLICABLE,
            "L'obligation ne vise que les immeubles a destination totale ou "
            "partielle d'habitation.", cles, limite,
            entrees_manquantes=("copropriete.destination_habitation",),
        )
    debut = dossier.budget.exercice_debut
    if debut is None:
        return _constat(
            "B-5", B5, INAPPLICABLE,
            "Sans date de debut d'exercice, le terme de dix ans depuis la "
            "reception des travaux n'est pas verifiable.", cles, limite,
            entrees_manquantes=("budget.exercice_debut",),
        )
    if _mois_ecoules(copro.date_reception_travaux_construction, debut) < 120:
        return _constat(
            "B-5", B5, INAPPLICABLE,
            "Le fonds de travaux n'est constitue qu'au terme de dix ans depuis "
            "la reception des travaux de construction.", cles, limite,
            entrees_manquantes=("copropriete.date_reception_travaux_construction",),
        )
    planchers = [("5 % du budget previsionnel", 0.05 * budget)]
    if copro.plan_pluriannuel_adopte:
        montant_plan = copro.montant_travaux_plan_adopte
        if montant_plan is None:
            return _constat(
                "B-5", B5, INAPPLICABLE,
                "Un plan pluriannuel est adopte mais son montant n'est pas connu: "
                "le second plancher de 2,5 % ne peut pas etre calcule.",
                cles, limite,
                entrees_manquantes=("copropriete.montant_travaux_plan_adopte",),
            )
        planchers.append(("2,5 % des travaux du plan adopte", 0.025 * montant_plan))
    insuffisants = [
        f"{intitule} = {valeur:.2f}"
        for intitule, valeur in planchers
        if cotisation + _TOLERANCE < valeur
    ]
    if insuffisants:
        return _constat(
            "B-5", B5, ECART,
            f"Cotisation votee {cotisation:.2f}, inferieure a: {'; '.join(insuffisants)}.",
            cles, limite,
        )
    return _constat(
        "B-5", B5, CONFORME,
        f"Cotisation votee {cotisation:.2f}, au moins egale a chaque plancher.",
        cles, limite,
    )


B6 = "L'avance constituant la reserve n'excede pas le sixieme du budget previsionnel."


def b6_avance_reserve(dossier: Dossier) -> Constat:
    cles = ("d67.35",)
    limite = (
        "Ne dit rien de l'exigibilite de l'avance, qui suppose en outre que le "
        "reglement de copropriete la prevoie. Un plafond respecte n'est pas une "
        "autorisation d'appeler."
    )
    avance = dossier.copropriete.avance_reserve_prevue_reglement
    budget = dossier.budget.total_charges
    absents = manquantes(
        copropriete__avance_reserve_prevue_reglement=avance,
        budget__total_charges=budget,
    )
    if absents:
        return _constat(
            "B-6", B6, INAPPLICABLE,
            "Montant de l'avance de reserve ou total du budget non extrait.",
            cles, limite,
            entrees_manquantes=tuple(nom.replace("__", ".") for nom in absents),
        )
    plafond = budget / 6
    if avance > plafond + _TOLERANCE:
        return _constat(
            "B-6", B6, ECART,
            f"Avance de reserve {avance:.2f}, superieure au sixieme du budget "
            f"({plafond:.2f}).", cles, limite,
        )
    return _constat(
        "B-6", B6, CONFORME,
        f"Avance de reserve {avance:.2f}, sous le plafond de {plafond:.2f}.",
        cles, limite,
    )


B7 = "L'assemblee se prononce sur la suspension des cotisations quand le fonds excede le budget."


def b7_suspension_cotisation(dossier: Dossier) -> Constat:
    cles = ("loi.14-2-1",)
    limite = (
        "Ne prejuge pas du sens de la decision: le texte impose que la question "
        "soit posee, pas que la suspension soit votee. Et il ajoute un second "
        "seuil, 50 % des travaux du plan, quand un plan est adopte."
    )
    solde = dossier.annexes.solde_fonds_travaux
    budget = dossier.budget.total_charges
    inscrite = dossier.convocation.question_suspension_cotisation_inscrite
    absents = manquantes(
        annexes__solde_fonds_travaux=solde,
        budget__total_charges=budget,
        convocation__question_suspension_cotisation_inscrite=inscrite,
    )
    if absents:
        return _constat(
            "B-7", B7, INAPPLICABLE,
            "Solde du fonds, budget ou ordre du jour non extraits.", cles, limite,
            entrees_manquantes=tuple(nom.replace("__", ".") for nom in absents),
        )
    if solde <= budget:
        return _constat(
            "B-7", B7, CONFORME,
            "Le fonds n'excede pas le budget previsionnel: la question n'a pas "
            "a etre posee.", cles, limite,
        )
    if not inscrite:
        return _constat(
            "B-7", B7, ECART,
            f"Fonds de travaux {solde:.2f} superieur au budget {budget:.2f}, "
            "sans question de suspension a l'ordre du jour.", cles, limite,
        )
    return _constat(
        "B-7", B7, CONFORME,
        "Le fonds excede le budget et la question de la suspension est inscrite.",
        cles, limite,
    )
