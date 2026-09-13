"""Qui a ECRIT la valeur d'un champ, et pourquoi c'est la bonne question.

**Le defaut que ce module remplace.** `RM-2026-0127`, 2026-09-08. La garde
anti-fuite `test_ui_nom_de_fichier_ne_fuit_pas` protegeait SIX ecrans, nommes a
la main. L'application en sert 54 en GET, mesure faite le meme jour sur
`create_app`. La page `/documents/{doc_id}` n'etait dans la liste d'aucun des
six, et elle rendait le nom de fichier brut trois fois - attribut `title`, titre
visible, attribut `alt`. La garde n'a rien vu parce qu'elle ne regardait pas.

Une liste de six ecrans est une **enumeration de modalites**: elle code les
pages qui existaient le jour ou elle a ete ecrite. La septieme page passe.

**L'axe.** Il n'est ni `quel ecran` ni `quelle colonne`, mais **d'ou vient la
valeur**. Le registre documentaire porte 54 colonnes. Elles se separent en deux
provenances, et une seule est dangereuse:

- une valeur **derivee**: CoproScope la calcule, depuis un vocabulaire ferme
  (`status_ocr`), un algorithme (`sha256`, `doc_id`) ou un comptage
  (`page_count`). Elle ne peut pas porter un patronyme, parce qu'aucun humain
  exterieur ne l'a ecrite;
- une valeur **de tiers**: un syndic, un fournisseur, un scanner ou un
  coproprietaire l'a saisie en texte libre. `file_name`, `notes`, `emitter`,
  `restriction_reasons` peuvent contenir n'importe quoi - un patronyme, un
  numero de lot, un motif de contentieux.

C'est le meme axe que `libelle_public.py` a deja nomme pour le seul nom de
fichier: *une donnee du corpus, pas une donnee de l'application*. Ce module
l'etend aux 54 colonnes.

**L'invariant**: une valeur de tiers ne traverse jamais une reponse servie. Ce
qui s'affiche est derive de ce que le document EST.

**Ce qui se passe hors des valeurs observees - et c'est le point.** La colonne
55 arrive demain, ecrite par un lot qui ne connait pas ce fichier. Elle n'est
declaree nulle part, donc `est_texte_de_tiers` rend `True`: elle est reputee
ecrite par un tiers, et la garde exige qu'elle ne s'affiche pas. Le systeme se
degrade du cote sur. Il ne rend pas une reponse fausse en silence: la garde
NOMME la colonne inconnue, et le developpeur la declare s'il veut l'afficher.

Le sens du defaut est choisi, pas subi. Une colonne derivee oubliee coute un
libelle absent, qu'on voit. Une colonne de tiers oubliee coute un patronyme
affiche sur une page diffusable, qu'on ne voit pas.
"""

from __future__ import annotations

from collections.abc import Iterable


#: Colonnes dont CoproScope ECRIT la valeur lui-meme.
#:
#: **Liste ouverte par le bas, fermee par le haut**: y ajouter une colonne est
#: une decision qui autorise son affichage, donc elle se prend ici et se motive.
#: Ne pas l'ajouter n'expose rien - c'est l'oubli sans consequence.
#:
#: Le critere d'entree est unique et verifiable: *aucun humain exterieur a
#: CoproScope ne peut choisir cette chaine*. Une colonne dont la valeur vient
#: d'un vocabulaire ferme du code, d'une empreinte, d'un comptage ou d'une date
#: normalisee le satisfait. Une colonne de texte libre ne le satisfait jamais,
#: meme si en pratique elle est souvent vide.
CHAMPS_DERIVES: frozenset[str] = frozenset(
    {
        # Identite calculee
        "doc_id",
        "sha256",
        "instance_id",
        "entity_id",
        "redacted_sha256",
        "redaction_map_id",
        # Comptages et tailles
        "size_bytes",
        "page_count",
        "text_char_count",
        # Dates normalisees par le code
        "first_seen",
        "last_modified",
        "suspected_date",
        "privacy_reviewed_at",
        # Vocabulaires fermes: la valeur appartient a un ensemble du code
        "scope",
        "extension",
        "source_zone",
        "source_kind",
        "document_type",
        "status_ocr",
        "classification_status",
        "extraction_level",
        "text_quality",
        "ocr_engine",
        "ai_review_status",
        "sensitivity",
        "raw_max_college",
        "derivative_max_college",
        "publication_form",
        "personal_data_level",
        "ip_status",
        "ai_processing_ceiling",
        "review_required",
        "policy_confidence",
        "required_transformations",
        "privacy_review_status",
        "review_status_recommendation",
        "review_justification_required",
        "redaction_status",
        "redaction_mode",
    }
)


def est_texte_de_tiers(colonne: str) -> bool:
    """`True` si la valeur a pu etre ecrite par quelqu'un hors de CoproScope.

    **Le defaut est `True`, et c'est la seule chose qui rend cette garde
    generalisable.** Une colonne inconnue est reputee dangereuse.
    """

    return (colonne or "").strip() not in CHAMPS_DERIVES


def colonnes_de_tiers(colonnes: Iterable[str]) -> tuple[str, ...]:
    """Les colonnes de l'en-tete reel dont la valeur vient d'un tiers.

    On lit l'en-tete du registre plutot qu'une liste ecrite ici: c'est ce qui
    fait que la colonne 55 est couverte le jour ou elle apparait, sans edition.
    """

    return tuple(nom for nom in colonnes if nom and est_texte_de_tiers(nom))


def colonnes_non_declarees(colonnes: Iterable[str]) -> tuple[str, ...]:
    """Les colonnes que ce module ne connait pas encore.

    Ce n'est PAS une erreur: elles sont deja protegees par le defaut. C'est le
    RESIDU rendu visible - la liste de ce qu'un humain devrait relire pour dire
    si la valeur est derivee, et donc affichable.
    """

    return tuple(sorted({nom for nom in colonnes if nom and nom not in CHAMPS_DERIVES}))
