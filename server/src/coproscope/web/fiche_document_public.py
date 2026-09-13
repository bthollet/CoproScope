"""Ce qu'une fiche document a le droit de montrer, et sous quelle forme.

Extrait de `_document_viewer_parts/01_detail_sections.py` le 2026-09-08, quand
les correctifs de `RM-2026-0127` ont pousse ce fichier a 663 lignes, au-dessus
de la limite de 600 du depot. Le decoupage n'est pas cosmetique: les deux
fonctions reunies ici repondent a une seule question - *quelle forme d'une
donnee du registre peut sortir vers un lecteur* - alors que le fichier d'origine
repond a *comment assembler une fiche*.

Les deux fonctions appliquent le meme invariant par deux moyens:

- `libelle_de_fiche` DERIVE une valeur affichable de ce que le document est;
- `pseudonymise_identites` REMPLACE une identite par son alias d'instance.

Dans les deux cas, ce qui sort n'est jamais la chaine que le tiers a ecrite.
"""

from __future__ import annotations

from typing import Any

from ..core.libelle_public import libelle_public_document


#: Colonnes du registre qui portent une PERSONNE, physique ou morale.
#:
#: **Ce n'est pas la garde, c'est le moyen de la satisfaire.** La garde est
#: `test_ui_nom_de_fichier_ne_fuit_pas`, qui verifie qu'aucune valeur de tiers
#: ne sort, sur toutes les routes servies et toutes les colonnes du registre.
#: Oublier une colonne ici ne fait donc pas fuiter en silence: la garde le dit.
#: C'est la difference entre une liste qui PROTEGE - dangereuse quand elle est
#: incomplete - et une liste qui CORRIGE, adossee a une conservation.
COLONNES_IDENTITE: tuple[tuple[str, str], ...] = (("privacy_review_owner", "REVISEUR"),)


def pseudonymise_identites(instance: Any, row: dict[str, str]) -> dict[str, str]:
    """Remplace les identites du registre par leur alias, une fois pour toutes.

    Arbitrage de Brice du 2026-09-08 (`RM-2026-0126`): « tout ce qui est
    identifiant est remplace par le pseudonyme ». Applique en UN point, celui
    ou l'instance - donc le sel - est disponible, plutot qu'a chaque point de
    rendu: la fiche compte deux lecteurs de `privacy_review_owner`, et deux
    corrections separees derivent tot ou tard l'une de l'autre.

    Mesure du 2026-09-08 qui a motive ce correctif: sur `/documents/{doc_id}`,
    la valeur de `privacy_review_owner` sortait telle quelle comme libelle de
    signataire. C'est le nom d'une personne, en clair, sur une page diffusable.

    Si le sel est indisponible - instance sans coffre local declare - on vide la
    valeur au lieu de la laisser passer: pas de sel, pas d'alias, donc pas
    d'affichage.
    """

    from ..modules.table_pseudonyme import pseudonymiser_valeur

    copie = dict(row)
    try:
        from ..modules.biffageops import load_corpus_salt

        sel = load_corpus_salt(instance)
    except Exception:  # noqa: BLE001 - voir docstring: sans sel, on n'affiche rien
        sel = None
    for colonne, categorie in COLONNES_IDENTITE:
        valeur = (copie.get(colonne) or "").strip()
        if not valeur:
            continue
        copie[colonne] = pseudonymiser_valeur(sel, categorie, valeur) if sel else ""
    return copie


def libelle_de_fiche(row: dict[str, str]) -> str:
    """Le libelle de la fiche, derive de ce que le document EST.

    **Corrige `RM-2026-0127`, 2026-09-08.** Cette fonction rendait le nom de
    fichier brut, sauf si `_guard_private_inbox` disait le contraire. La fiche
    `/documents/{doc_id}` l'imprimait donc trois fois - attribut `title`, titre
    visible, attribut `alt` - pour tout document normalement classe.

    **Pourquoi la condition a disparu, et n'est pas remplacee par une autre.**
    `_guard_private_inbox` teste des MODALITES: la zone vaut `200_INBOX` ou
    `RAW`, le statut appartient a un ensemble observe. Un document range
    ailleurs, ou portant un statut ajoute demain, sort de tous les cas et
    obtient le nom brut - une reponse fausse en silence, sur une page
    diffusable. La zone d'un document ne dit rien de ce que son nom contient:
    c'est un tiers qui a ecrit ce nom, dans tous les cas.

    L'invariant est donc inconditionnel, et c'est celui que
    `libelle_public_document` porte deja. Sa propre docstring l'annoncait: un
    appelant qui veut le nom d'origine doit le demander explicitement et assumer
    sa restriction, pas l'obtenir par defaut au detour d'un libelle. La fiche de
    detail etait precisement l'appelant qui l'obtenait par defaut.

    Le nom depose reste lisible cote serveur: la recherche `/documents?q=` le
    lit toujours, et c'est ce qui garde la piece retrouvable sans la nommer.
    """

    return libelle_public_document(row)
