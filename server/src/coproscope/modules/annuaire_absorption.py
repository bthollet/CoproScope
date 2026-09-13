from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..vault.gouvernance_store import ORIGINE_CORRIGE, lire, remplacer_pour_documents
from .biffageops import (
    STATUT_LISTE_ABSENTE,
    STATUT_LISTE_ILLISIBLE,
    STATUT_LISTE_TROUVEE,
    lit_liste_nominative,
)


"""La porte d'absorption: reclamer la liste nominative quand elle manque.

**Le constat qui la motive**, mesure le 2026-09-07. Une instance de 825
documents affichait 539 pieces marquees a masquer, zero masquee, et zero
pseudonyme sur 2 449 fichiers. Le corpus n'avait aucune liste nominative, donc
l'annuaire etait vide, donc le caviardage n'avait rien a appliquer - et rien, a
aucun ecran, ne le disait.

**Ce module ne lance aucun traitement.** Il constate et il demande. C'est la
meme doctrine que `lisibilite.py`, qui demande l'accord OCR: on demande, on ne
fait pas; on explique avant de demander; une reponse donnee ne se redemande
jamais.

**Pourquoi trois statuts et pas deux.** `Je n'ai pas trouve de liste` et
`j'en ai trouve une que je ne sais pas lire` appellent deux demandes
differentes: la premiere reclame une piece, la seconde signale un defaut de
lecture. Les confondre, c'est ce que faisait l'ancien extracteur en rendant une
liste vide dans les deux cas - et c'est pourquoi la porte ne pouvait pas
reclamer la bonne chose.
"""


TABLE_DECISIONS = "annuaire_decisions"
CLES_DECISIONS = ("doc_id", "origine")
CHAMPS_DECISIONS = ("doc_id", "origine", "decision", "decide_le", "constat")

#: L'utilisateur fournira la piece. On ne redemande plus pour ce corpus.
ATTENDU = "ATTENDU"
#: L'utilisateur dit qu'il n'y en a pas. On ne redemande plus, et le derive le
#: dit dans sa reserve au lieu de faire comme si de rien n'etait.
SANS_LISTE = "SANS_LISTE"
DECISIONS = (ATTENDU, SANS_LISTE)

#: Identifiant de la demande portant sur le corpus entier. La question ne porte
#: pas sur une piece: elle porte sur ce qui MANQUE au corpus, ce qui n'a par
#: definition aucun `doc_id`.
PORTEE_CORPUS = "CORPUS"


def constat(textes: dict[str, str]) -> dict[str, Any]:
    """Ce que le corpus dit de sa propre liste nominative.

    `textes` associe un `doc_id` a son texte. Rendre un constat plutot qu'un
    booleen: l'appelant doit pouvoir DIRE a l'utilisateur ce qui a ete vu.
    """

    trouvees: list[str] = []
    illisibles: list[dict[str, str]] = []
    personnes = 0
    for doc_id, texte in textes.items():
        resultat = lit_liste_nominative(texte)
        statut = resultat["statut"]
        if statut == STATUT_LISTE_TROUVEE:
            trouvees.append(doc_id)
            personnes += len(resultat["entrees"])  # type: ignore[arg-type]
        elif statut == STATUT_LISTE_ILLISIBLE:
            illisibles.append({"doc_id": doc_id, "motif": str(resultat["motif"])})

    if trouvees:
        etat = STATUT_LISTE_TROUVEE
    elif illisibles:
        etat = STATUT_LISTE_ILLISIBLE
    else:
        etat = STATUT_LISTE_ABSENTE
    return {
        "etat": etat,
        "documents_avec_liste": trouvees,
        "documents_illisibles": illisibles,
        "personnes_lues": personnes,
        "documents_examines": len(textes),
    }


def demande_utilisateur(constat_courant: dict[str, Any]) -> dict[str, str] | None:
    """La question a poser, en langage de coproprietaire. None si rien a demander.

    Deux questions distinctes, parce que deux situations distinctes. Les
    confondre empeche l'utilisateur de savoir quoi faire.
    """

    etat = constat_courant.get("etat")
    if etat == STATUT_LISTE_TROUVEE:
        return None

    if etat == STATUT_LISTE_ILLISIBLE:
        nombre = len(constat_courant.get("documents_illisibles", []))
        return {
            "titre": "Une liste de coproprietaires n'a pas pu etre lue",
            "constat": (
                f"{nombre} piece(s) ressemblent a une liste de coproprietaires - on y "
                "reconnait des numeros de compte et des montants - mais la mise en page "
                "n'a pas permis d'y lire les noms."
            ),
            "consequence": (
                "Sans cette liste, l'outil ne connait aucun nom a masquer. Il masque "
                "quand meme ce qu'il reconnait tout seul, mais il en laisse passer."
            ),
            "remede": (
                "Signalez-le: cette mise en page merite d'etre ajoutee. En attendant, "
                "vous pouvez fournir la meme liste dans un autre format."
            ),
            "question": "Voulez-vous fournir cette liste sous une autre forme ?",
        }

    return {
        "titre": "Il manque la liste des coproprietaires",
        "constat": (
            "Aucune piece du dossier ne contient de liste nominative - typiquement "
            "l'annexe des soldes, ou l'etat des comptes individuels que votre syndic "
            "produit chaque annee."
        ),
        "consequence": (
            "Sans elle, l'outil ne sait pas quels noms masquer. Il masque ce qu'il "
            "reconnait par lui-meme, ce qui est nettement moins fiable: sur un dossier "
            "sans cette liste, aucun nom n'est masque de facon sure."
        ),
        "remede": (
            "Ajoutez l'annexe des soldes ou l'etat des comptes individuels au dossier. "
            "Une seule piece suffit, et elle profite a tout le corpus."
        ),
        "question": "Pouvez-vous ajouter cette piece au dossier ?",
    }


def enregistrer_decision(instance: Any, decision: str, constat_courant: dict[str, Any]) -> None:
    """Garde la reponse de l'utilisateur, pour ne plus la lui redemander.

    Ecrite avec `origine = CORRIGE_HUMAIN`: c'est ce qui la protege du
    remplacement lors d'une nouvelle absorption. Un `il n'y en a pas` doit
    survivre aussi longtemps qu'un `je vais la fournir`.
    """

    if decision not in DECISIONS:
        raise ValueError(
            f"decision {decision!r} inconnue. Valeurs possibles: {', '.join(DECISIONS)}."
        )
    ligne = {
        "doc_id": PORTEE_CORPUS,
        "origine": ORIGINE_CORRIGE,
        "decision": decision,
        "decide_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "constat": str(constat_courant.get("etat", "")),
    }
    remplacer_pour_documents(
        instance,
        CHAMPS_DECISIONS,
        [ligne],
        [PORTEE_CORPUS],
        table=TABLE_DECISIONS,
        cles=CLES_DECISIONS,
    )


def decision_enregistree(instance: Any) -> str:
    """La reponse deja donnee pour ce corpus, ou chaine vide."""

    lignes = lire(instance, table=TABLE_DECISIONS, ordre="decide_le DESC")
    for ligne in lignes:
        if ligne.get("doc_id") == PORTEE_CORPUS:
            return ligne.get("decision", "")
    return ""
