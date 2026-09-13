"""Famille P: procedure du vote du budget previsionnel.

Date du vote, regime transitoire, duree de l'exercice, pieces notifiees,
majorite, concertation et archivage. Voir
`docs/grille_budget_previsionnel_2026-09-04.md`.
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
# Famille P - procedure du vote
# --------------------------------------------------------------------------

P1 = "Le budget previsionnel est vote avant le debut de l'exercice qu'il couvre."


def p1_vote_avant_exercice(dossier: Dossier) -> Constat:
    cles = ("d67.43",)
    limite = (
        "Un vote posterieur au debut de l'exercice n'est PAS une irregularite "
        "en soi: le second alinea du meme article 43 organise cette situation. "
        "Ce controle est un aiguillage vers P-2, pas un manquement."
    )
    date_ag = dossier.vote.date_assemblee
    debut = dossier.budget.exercice_debut
    absents = manquantes(vote__date_assemblee=date_ag, budget__exercice_debut=debut)
    if absents:
        return _constat(
            "P-1", P1, INAPPLICABLE,
            "Date d'assemblee ou de debut d'exercice non extraite.", cles, limite,
            entrees_manquantes=tuple(nom.replace("__", ".") for nom in absents),
        )
    if date_ag >= debut:
        return _constat(
            "P-1", P1, A_VERIFIER_HUMAIN,
            f"Budget vote le {date_ag.isoformat()}, apres le debut de l'exercice "
            f"le {debut.isoformat()}. Le regime transitoire de l'alinea 2 "
            "s'applique: voir P-2.", cles, limite,
        )
    return _constat(
        "P-1", P1, CONFORME,
        f"Budget vote le {date_ag.isoformat()}, avant le {debut.isoformat()}.",
        cles, limite,
    )


P2 = "Le vote en cours d'exercice respecte le regime des provisions transitoires."


def p2_provisions_transitoires(dossier: Dossier) -> Constat:
    cles = ("d67.43", "loi.14-1")
    limite = (
        "Ne dit rien des impayes: le meme alinea ecarte la procedure de "
        "l'article 19-2 dans cette situation, et un retard de paiement ne peut "
        "donc pas en etre deduit."
    )
    vote = dossier.vote
    date_ag = vote.date_assemblee
    debut = dossier.budget.exercice_debut
    if date_ag is None or debut is None:
        return _constat(
            "P-2", P2, INAPPLICABLE,
            "Date d'assemblee ou de debut d'exercice non extraite.", cles, limite,
            entrees_manquantes=tuple(
                nom.replace("__", ".")
                for nom in manquantes(vote__date_assemblee=date_ag, budget__exercice_debut=debut)
            ),
        )
    if date_ag < debut:
        return _constat(
            "P-2", P2, CONFORME,
            "Budget vote avant le debut de l'exercice: pas de provision transitoire.",
            cles, limite,
        )
    absents = manquantes(
        vote__autorisation_provisions_transitoires=vote.autorisation_provisions_transitoires,
        vote__provisions_transitoires_appelees=vote.provisions_transitoires_appelees,
        vote__assiette_provisions_transitoires=vote.assiette_provisions_transitoires,
        vote__budget_precedent_vote=vote.budget_precedent_vote,
    )
    if absents:
        return _constat(
            "P-2", P2, INAPPLICABLE,
            "Regime transitoire non documente.", cles, limite,
            entrees_manquantes=tuple(nom.replace("__", ".") for nom in absents),
        )
    griefs: list[str] = []
    if not vote.autorisation_provisions_transitoires:
        griefs.append("aucune autorisation prealable de l'assemblee")
    if vote.provisions_transitoires_appelees > 2:
        griefs.append(
            f"{vote.provisions_transitoires_appelees} provisions appelees, deux au plus"
        )
    attendu = vote.budget_precedent_vote / 4
    if abs(vote.assiette_provisions_transitoires - attendu) > _TOLERANCE:
        griefs.append(
            f"provision de {vote.assiette_provisions_transitoires:.2f} au lieu du quart "
            f"du budget precedemment vote ({attendu:.2f})"
        )
    if griefs:
        return _constat("P-2", P2, ECART, "; ".join(griefs) + ".", cles, limite)
    return _constat(
        "P-2", P2, CONFORME,
        "Autorisation prealable, deux provisions au plus, assises sur le budget "
        "precedemment vote.", cles, limite,
    )


P3 = "Le budget previsionnel couvre un exercice comptable de douze mois."


def p3_duree_exercice(dossier: Dossier) -> Constat:
    cles = ("d67.43", "d05.5")
    limite = (
        "Ne vaut pas pour le premier exercice, que l'article 5 du decret de "
        "2005 laisse aller jusqu'a dix-huit mois. Ne dit rien non plus d'un "
        "changement de date de cloture, licite sur decision motivee."
    )
    debut = dossier.budget.exercice_debut
    fin = dossier.budget.exercice_fin
    absents = manquantes(budget__exercice_debut=debut, budget__exercice_fin=fin)
    if absents:
        return _constat(
            "P-3", P3, INAPPLICABLE,
            "Bornes de l'exercice non extraites.", cles, limite,
            entrees_manquantes=tuple(nom.replace("__", ".") for nom in absents),
        )
    mois = _mois_ecoules(debut, fin) + 1
    if dossier.copropriete.premier_exercice:
        if mois > 18:
            return _constat(
                "P-3", P3, ECART,
                f"Premier exercice de {mois} mois, au-dela du maximum de dix-huit mois.",
                cles, limite,
            )
        return _constat(
            "P-3", P3, CONFORME,
            f"Premier exercice de {mois} mois, dans la limite de dix-huit mois.",
            cles, limite,
        )
    if mois == 12:
        return _constat("P-3", P3, CONFORME, "Exercice de douze mois.", cles, limite)
    if dossier.copropriete.premier_exercice is None:
        # Sans savoir si c'est le premier exercice, une duree autre que douze
        # mois ne se qualifie pas: elle peut relever du plafond de dix-huit.
        return _constat(
            "P-3", P3, INAPPLICABLE,
            f"Exercice de {mois} mois, mais le rang de l'exercice est inconnu: "
            "le premier exercice peut aller jusqu'a dix-huit mois.", cles, limite,
            entrees_manquantes=("copropriete.premier_exercice",),
        )
    return _constat(
        "P-3", P3, ECART, f"Exercice de {mois} mois au lieu de douze.", cles, limite
    )


P4 = "L'assemblee appelee a voter le budget est reunie dans les six mois de la cloture precedente."


def p4_delai_six_mois(dossier: Dossier) -> Constat:
    cles = ("loi.14-1",)
    limite = (
        "Ne prouve pas la nullite de la decision: le texte fixe un delai de "
        "reunion, pas une sanction. Et il n'atteint pas la premiere assemblee "
        "d'une copropriete, qui n'a pas d'exercice precedent."
    )
    date_ag = dossier.vote.date_assemblee
    cloture = dossier.copropriete.cloture_exercice_precedent
    if dossier.copropriete.premier_exercice:
        return _constat(
            "P-4", P4, INAPPLICABLE,
            "Premiere assemblee: aucun exercice precedent a clore.", cles, limite,
            entrees_manquantes=("copropriete.cloture_exercice_precedent",),
        )
    absents = manquantes(
        vote__date_assemblee=date_ag, copropriete__cloture_exercice_precedent=cloture
    )
    if absents:
        return _constat(
            "P-4", P4, INAPPLICABLE,
            "Date d'assemblee ou de cloture precedente non extraite.", cles, limite,
            entrees_manquantes=tuple(nom.replace("__", ".") for nom in absents),
        )
    jours = (date_ag - cloture).days
    if jours > 183:
        return _constat(
            "P-4", P4, ECART,
            f"Assemblee reunie {jours} jours apres la cloture du {cloture.isoformat()}.",
            cles, limite,
        )
    return _constat(
        "P-4", P4, CONFORME,
        f"Assemblee reunie {jours} jours apres la cloture precedente.", cles, limite,
    )


P5 = "Le projet de budget est notifie avec le comparatif du dernier budget previsionnel vote."


def p5_comparatif_dernier_budget(dossier: Dossier) -> Constat:
    cles = ("d67.11", "d05.8")
    limite = (
        "Le comparatif exige est PREVISIONNEL contre PREVISIONNEL. Ce controle "
        "ne dit donc rien de la confrontation au realise de l'exercice "
        "precedent, qui n'est pas une obligation attachee au vote du budget: "
        "le realise n'entre qu'a l'approbation des comptes, article 8 du "
        "decret de 2005. Et il ne prouve pas que le comparatif soit exact."
    )
    conv = dossier.convocation
    absents = manquantes(
        convocation__projet_budget_notifie=conv.projet_budget_notifie,
        convocation__comparatif_dernier_budget_vote_notifie=(
            conv.comparatif_dernier_budget_vote_notifie
        ),
    )
    if absents:
        return _constat(
            "P-5", P5, INAPPLICABLE,
            "Contenu de la notification non extrait.", cles, limite,
            entrees_manquantes=tuple(nom.replace("__", ".") for nom in absents),
        )
    if dossier.copropriete.premier_exercice:
        return _constat(
            "P-5", P5, INAPPLICABLE,
            "Premier budget previsionnel: il n'existe aucun budget "
            "precedemment vote a comparer.", cles, limite,
            entrees_manquantes=("vote.budget_precedent_vote",),
        )
    griefs: list[str] = []
    if not conv.projet_budget_notifie:
        griefs.append("projet de budget non notifie avec l'ordre du jour")
    if not conv.comparatif_dernier_budget_vote_notifie:
        if dossier.copropriete.premier_exercice is None:
            # Un comparatif absent peut etre une piece manquante, ou l'absence
            # de tout budget anterieur. On ne choisit pas.
            return _constat(
                "P-5", P5, INAPPLICABLE,
                "Comparatif absent, mais on ignore s'il existe un budget "
                "precedemment vote a comparer.", cles, limite,
                entrees_manquantes=("copropriete.premier_exercice",),
            )
        griefs.append("comparatif du dernier budget previsionnel vote absent")
    if griefs:
        return _constat(
            "P-5", P5, ECART,
            "; ".join(griefs) + ". L'article 11 range ces pieces parmi celles "
            "notifiees pour la validite de la decision.", cles, limite,
        )
    return _constat(
        "P-5", P5, CONFORME,
        "Projet de budget et comparatif du dernier budget vote notifies.",
        cles, limite,
    )


P6 = "Le projet de budget est presente conformement au modele de l'annexe 2."


def p6_presentation_annexe2(dossier: Dossier) -> Constat:
    cles = ("d67.11", "d05.8", "d05.9", "d05.10", "d05.annexe2")
    limite = (
        "Ne peut pas etre entierement automatise. Les modeles d'annexes ne sont "
        "pas reproduits sur Legifrance, qui renvoie au PDF du Journal officiel: "
        "seules les rubriques nommees par les textes modificatifs sont "
        "verifiables par machine. Le reste releve d'une lecture humaine."
    )
    conforme = dossier.convocation.presentation_conforme_annexe2
    if conforme is None:
        return _constat(
            "P-6", P6, INAPPLICABLE,
            "Conformite de presentation non qualifiee.", cles, limite,
            entrees_manquantes=("convocation.presentation_conforme_annexe2",),
        )
    if not conforme:
        return _constat(
            "P-6", P6, ECART,
            "Presentation non conforme au modele obligatoire de l'annexe 2.",
            cles, limite,
        )
    return _constat("P-6", P6, CONFORME, "Presentation conforme au modele.", cles, limite)


P7 = "Le budget previsionnel est vote a la majorite de l'article 24."


def p7_majorite(dossier: Dossier) -> Constat:
    cles = ("loi.24", "loi.14-1")
    limite = (
        "Ne verifie que l'article vise, pas le decompte des voix. Et il depend "
        "du typage des resolutions, qui n'appartient pas a ce module: la "
        "reconnaissance d'une resolution de vote du budget est tenue ailleurs."
    )
    article = dossier.vote.article_majorite
    if article is None:
        return _constat(
            "P-7", P7, INAPPLICABLE,
            "Majorite visee par la resolution non extraite.", cles, limite,
            entrees_manquantes=("vote.article_majorite",),
        )
    normalise = article.replace(" ", "").lower().lstrip("article")
    if normalise not in {"24", "24i"}:
        return _constat(
            "P-7", P7, ECART,
            f"Budget vote sous la majorite annoncee {article!r} et non celle de "
            "l'article 24.", cles, limite,
        )
    return _constat("P-7", P7, CONFORME, "Majorite de l'article 24.", cles, limite)


P8 = "Le budget previsionnel est etabli en concertation avec le conseil syndical."


def p8_concertation(dossier: Dossier) -> Constat:
    cles = ("loi.18",)
    limite = (
        "Aucune piece standard n'atteste la concertation. Ce controle ne produit "
        "jamais un manquement: il produit une question a poser au syndic. "
        "L'absence de trace n'est pas la preuve d'une absence de concertation."
    )
    trace = dossier.copropriete.concertation_conseil_syndical_tracee
    if trace is None:
        return _constat(
            "P-8", P8, INAPPLICABLE,
            "Aucune trace de concertation recherchee.", cles, limite,
            entrees_manquantes=("copropriete.concertation_conseil_syndical_tracee",),
        )
    if not trace:
        return _constat(
            "P-8", P8, A_VERIFIER_HUMAIN,
            "Aucune trace de concertation avec le conseil syndical au dossier. "
            "A demander au syndic avant toute conclusion.", cles, limite,
        )
    return _constat("P-8", P8, CONFORME, "Concertation tracee au dossier.", cles, limite)


P9 = "Les annexes sont conservees avec copie du proces-verbal qui vote le budget."


def p9_archivage(dossier: Dossier) -> Constat:
    cles = ("d05.12",)
    limite = (
        "Ne prouve rien sur le classement particulier exige par le meme "
        "article, qui est une modalite d'archivage physique ou logique que le "
        "dossier ne porte pas."
    )
    archive = dossier.copropriete.annexes_archivees_avec_pv
    if archive is None:
        return _constat(
            "P-9", P9, INAPPLICABLE,
            "Etat de l'archivage non renseigne.", cles, limite,
            entrees_manquantes=("copropriete.annexes_archivees_avec_pv",),
        )
    if not archive:
        return _constat(
            "P-9", P9, ECART,
            "Annexes non conservees avec la copie du proces-verbal.", cles, limite,
        )
    return _constat("P-9", P9, CONFORME, "Annexes conservees avec le proces-verbal.", cles, limite)
