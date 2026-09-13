from __future__ import annotations

from collections import defaultdict

# --- Ce qu'une empreinte identifie, et ce qu'elle n'identifie pas ------------
#
# Une empreinte identifie un CONTENU. Elle n'identifie ni un fichier, ni une
# denomination, ni un instrument juridique. Le registre des documents, lui,
# garde une ligne par CHEMIN: un meme contenu absorbe sous deux noms y occupe
# deux lignes, et `classify` les traite l'une apres l'autre sans jamais les
# regarder ensemble.
#
# Le module de classement enonce deja la bonne regle - le nom d'un fichier est
# une denomination, au meme titre qu'un titre lu en tete du texte, et quand les
# deux se contredisent aucune ne tranche seule - mais il ne la tient que DANS
# une ligne. Ce fichier la tient ENTRE les lignes de meme empreinte.
#
# L'AXE, et non les deux cas observes. Le degre de liberte est le nombre de
# denominations sous lesquelles un meme contenu est absorbe: un, deux, ou N.
# Ce qui reste vrai tout le long de l'axe: le contenu, lui, reste UN. Donc tout
# champ qui est un verdict SUR LE CONTENU n'a qu'une valeur legitime par
# empreinte, quel que soit N.
#
# Trois etats se distinguent, et ils n'ont pas le meme remede:
#
#   1. ACCORD - les denominations disent la meme chose. C'est un doublon franc:
#      il se deduplique, et `registre_doublons.csv` l'enregistre deja.
#   2. DESACCORD - deux valeurs NON VIDES s'opposent sur un meme contenu. Il ne
#      se deduplique pas: il se garde et s'affiche. Elire une copie ici serait
#      trancher sans preuve.
#   3. LECTURE PARTIELLE - une denomination porte une valeur, l'autre n'en
#      porte aucune. Ce n'est PAS un desaccord, et c'est la distinction que
#      l'enonce de `RM-2026-0088` fusionne en disant "deux dates": la mesure
#      montre une date et une ABSENCE. Une absence n'est pas une seconde
#      valeur. Elle ne se compte pas comme un conflit, et surtout elle ne
#      s'herite pas - la valeur manquante se demande.
#
# --- Pourquoi la liste des champs confrontes n'est PAS une liste ------------
#
# Premiere ecriture de ce module: trois champs nommes en dur - `lot`,
# `document_type`, `suspected_date` - c'est-a-dire exactement les trois que
# l'enonce de l'item citait. C'etait une enumeration de modalites, et elle
# rendait un chiffre faux sans faire echouer un seul test.
#
# MESURE DU 2026-09-09, sur `ffac60c` augmente du lot mesure. `classify` ecrit
# 18 colonnes du registre, pas trois: `apply_access_policy(row, ...)` fait
# `row.update(build_access_policy(...))` et pose a lui seul 13 champs de plus.
# Et `build_access_policy` construit son foin a partir de `file_name`,
# `original_path` et `document_type` - trois DENOMINATIONS. Deux exemplaires du
# meme contenu en sortent donc avec des politiques d'acces differentes. Mesure
# faite sur une course reelle, deux lignes de meme SHA-256 et meme texte:
#
#     raw_max_college        C2_Coproprietaires   /  C8_Restreint_Critique
#     publication_form       raw                  /  aggregation_required
#     ai_processing_ceiling  local_only           /  no_ai
#     review_required        (vide)               /  YES
#     personal_data_level    none                 /  nominative
#
# Les deux lignes sortaient `AUTO_CLASSIFIED`, sans une note, et le journal de
# la course annoncait `desaccords_empreinte=0`. Le champ qui decide QUI a le
# droit de voir la piece divergeait en silence, et le compteur disait que tout
# allait bien.
#
# DONC: un champ est confronte PAR DEFAUT. Il n'y echappe que s'il figure dans
# l'une des deux listes d'exemption ci-dessous, chacune avec sa raison. Un
# champ ajoute demain - par `row[...] = `, par `row.update(...)`, par une cle
# variable ou par un helper, la maniere d'ecrire n'entrant pas dans la regle -
# tombe du cote bruyant: il est confronte. C'est la degradation propre qu'exige
# la regle des axes.
#
# RESIDU NOMME, non traite ici. Nommer une divergence de college ne dit pas
# laquelle des deux valeurs gouverne la publication. Retenir la plus
# restrictive serait une ELECTION, que l'item interdit; ne rien retenir laisse
# un chemin de diffusion libre de lire la ligne permissive. C'est une decision
# produit, et elle est posee au fil pilote au lieu d'etre tranchee ici.

#: Ce qui decrit l'EXEMPLAIRE DEPOSE, ou porte une cle d'identite, jamais un
#: verdict sur le contenu. Deux denominations d'un meme contenu en different
#: par construction: c'est precisement ce qui fait qu'il y a deux lignes.
CHAMPS_DE_LA_DENOMINATION = (
    # Cles: identiques par construction pour un meme contenu, et de toute facon
    # ce ne sont pas des jugements.
    "doc_id",
    "instance_id",
    "entity_id",
    "sha256",
    # L'exemplaire: ou il a ete trouve, sous quel nom, quand.
    "original_path",
    "file_name",
    "extension",
    "size_bytes",
    "last_modified",
    "first_seen",
    "source_zone",
    "source_kind",
    "scope",
)

#: Ce qui decrit la TENUE DE LA LIGNE: l'etat de sa lecture, l'etat de son
#: traitement, ou une decision humaine portee sur elle. Deux lignes de meme
#: empreinte peuvent legitimement en differer - l'une a pu etre lue, l'autre
#: non - et c'est exactement ce que le module de classement dit deja.
CHAMPS_DE_TENUE_DE_LIGNE = (
    "classification_status",
    "notes",
    # L'etat de lecture d'un exemplaire.
    "status_ocr",
    "text_path",
    "page_count",
    "text_char_count",
    "extraction_level",
    "text_quality",
    "ocr_engine",
    "docling_path",
    "layout_path",
    # Decisions humaines et etats de traitement portes sur une ligne. La
    # doctrine du depot separe une donnee derivee d'une donnee saisie par un
    # humain: les confronter ici les melangerait.
    "ai_review_status",
    "privacy_review_status",
    "redaction_status",
    "redaction_mode",
    "redacted_path",
    "redacted_sha256",
    "redaction_map_id",
)

CHAMPS_EXEMPTES = frozenset(CHAMPS_DE_LA_DENOMINATION) | frozenset(CHAMPS_DE_TENUE_DE_LIGNE)

#: TEMOIN, et non moteur. La confrontation, elle, se calcule par soustraction
#: des exemptions: c'est ce qui fait qu'une colonne inconnue est confrontee au
#: lieu d'etre oubliee. Cette liste-ci ne pilote rien; elle enregistre l'etat du
#: registre au 2026-09-09 pour qu'une colonne AJOUTEE demain fasse tomber
#: `test_toute_colonne_du_registre_a_une_nature_declaree` en se nommant, et
#: soit rangee d'un cote ou de l'autre par un humain.
#:
#: Sans ce temoin la garde etait une TAUTOLOGIE, verifiee le 2026-09-09: elle
#: comparait la soustraction a elle-meme et rendait `OK` sur une colonne neuve
#: non declaree. Une garde qui ne mesure rien est pire que pas de garde.
CHAMPS_DU_VERDICT_CONNUS = frozenset({
    "lot",
    "document_type",
    "suspected_date",
    "emitter",
    "sensitivity",
    "raw_max_college",
    "derivative_max_college",
    "publication_form",
    "restriction_reasons",
    "personal_data_level",
    "ip_status",
    "ai_processing_ceiling",
    "derivative_ai_ceiling",
    "review_required",
    "policy_confidence",
    "required_transformations",
    "screening_signals",
})

MENTION_DESACCORD = "Desaccord entre denominations de meme empreinte"
MENTION_LECTURE_PARTIELLE = "Lecture partielle entre denominations de meme empreinte"


def champs_du_verdict_sur_le_contenu(colonnes) -> tuple[str, ...]:
    """Les colonnes confrontees: tout ce qui n'est pas explicitement exempte.

    L'ordre suit celui des colonnes recues, pour qu'un meme groupe rende
    toujours ses notes dans le meme ordre.
    """
    return tuple(colonne for colonne in colonnes if colonne not in CHAMPS_EXEMPTES)


def _colonnes(rows: list[dict]) -> list[str]:
    vues: list[str] = []
    connues: set[str] = set()
    for row in rows:
        for colonne in row:
            if colonne not in connues:
                connues.add(colonne)
                vues.append(colonne)
    return vues


def _empreinte(row: dict) -> str:
    return (row.get("sha256") or "").strip().lower()


def grouper_par_empreinte(rows: list[dict]) -> dict[str, list[dict]]:
    """Les groupes de plus d'une ligne, par empreinte de contenu."""
    groupes: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        empreinte = _empreinte(row)
        if empreinte:
            groupes[empreinte].append(row)
    return {e: g for e, g in sorted(groupes.items()) if len(g) > 1}


def _denominations(groupe: list[dict]) -> str:
    noms = sorted({(r.get("file_name") or r.get("original_path") or "?") for r in groupe})
    return ", ".join(noms)


def reconcilier_par_empreinte(rows: list[dict]) -> dict[str, object]:
    """Confronte les lignes qui partagent une empreinte, sans elire de copie.

    N'ecrit jamais une valeur d'une ligne dans une autre: reconcilier ici veut
    dire NOMMER l'ecart, pas le resorber. Le seul champ modifie hors `notes`
    est `classification_status`, et seulement pour retirer une AFFIRMATION -
    jamais pour en poser une.
    """
    sans_empreinte = sum(1 for row in rows if not _empreinte(row))
    groupes = grouper_par_empreinte(rows)
    confrontes = champs_du_verdict_sur_le_contenu(_colonnes(rows))
    desaccords = 0
    lectures_partielles = 0
    champs_en_desaccord: set[str] = set()

    for empreinte, groupe in groupes.items():
        court = empreinte[:12]
        noms = _denominations(groupe)
        for champ in confrontes:
            valeurs = [(row.get(champ) or "").strip() for row in groupe]
            pleines = sorted({valeur for valeur in valeurs if valeur})
            if len(pleines) > 1:
                desaccords += 1
                champs_en_desaccord.add(champ)
                note = (
                    f"{MENTION_DESACCORD}: {champ} vaut "
                    + " / ".join(pleines)
                    + f" selon la denomination ({len(groupe)} lignes pour l'empreinte"
                    f" {court}: {noms}). Une empreinte identifie un contenu, pas une"
                    " denomination: aucune ne tranche seule, et rien n'est elu ici."
                )
                for row in groupe:
                    row["notes"] = append_note(row.get("notes", ""), note)
                    # On ne retire qu'une AFFIRMATION. Un statut qui doute deja
                    # - texte insuffisant, a reclasser, a classer - dit quelque
                    # chose de plus precis sur SA ligne: l'ecraser perdrait de
                    # l'information au lieu d'en ajouter.
                    if row.get("classification_status") == "AUTO_CLASSIFIED":
                        row["classification_status"] = CLASSIFICATION_DOUBT_STATUS
            elif pleines and "" in valeurs:
                lectures_partielles += 1
                lues = sum(1 for valeur in valeurs if valeur)
                note = (
                    f"{MENTION_LECTURE_PARTIELLE}: {champ} lu ({pleines[0]}) sur"
                    f" {lues} des {len(groupe)} denominations de l'empreinte {court}"
                    f" ({noms}), absent sur les autres. Une absence n'est pas une"
                    " seconde valeur et ne s'herite pas d'une denomination a"
                    " l'autre: la valeur manquante se demande."
                )
                for row in groupe:
                    if not (row.get(champ) or "").strip():
                        row["notes"] = append_note(row.get("notes", ""), note)

    return {
        "groupes": len(groupes),
        "desaccords": desaccords,
        "lectures_partielles": lectures_partielles,
        "lignes_sans_empreinte": sans_empreinte,
        # NOMMER ce qui diverge, pas seulement compter. Un compteur seul ne dit
        # pas si le desaccord porte sur le type du document ou sur le college de
        # confidentialite, et les deux n'appellent pas la meme suite.
        "champs_en_desaccord": ";".join(sorted(champs_en_desaccord)),
    }

#: La priorite d'une demande nee d'une divergence. **Haute pour un desaccord,
#: normale pour une lecture partielle**, et la difference n'est pas de confort:
#: un desaccord signifie que deux valeurs incompatibles sont affirmees sur le
#: MEME contenu - une au moins est fausse, et on ignore laquelle. Une lecture
#: partielle signifie qu'une valeur est lue d'un cote et absente de l'autre:
#: rien n'est faux, il manque quelque chose.
PRIORITE_DESACCORD = "P1"
PRIORITE_LECTURE_PARTIELLE = "P2"

#: Le statut d'une demande qui n'a pas encore trouve son destinataire. Il vaut
#: `A_CLASSER` comme les autres demandes de la file: une piece candidate existe
#: - ici deux exemplaires du meme contenu - mais leur rangement est incertain.
STATUT_DEMANDE = "A_CLASSER"


def demandes_de_divergence(rows: list[dict]) -> list[dict[str, str]]:
    """Les demandes a poser pour les divergences d'empreinte de ce registre.

    **C'EST LE CHEMIN QUI MANQUAIT, et son absence a fait refuser le lot.**
    `reconcilier_par_empreinte` nomme l'ecart dans une note dont le texte dit
    *« la valeur manquante se demande »*. Le sceptique a releve, mot pour mot,
    que c'etait **un enonce, pas un chemin**: rien, nulle part, ne produisait
    la demande annoncee. La doctrine de l'item la reclamait pourtant
    explicitement - *« Ne PAS heriter une date d'un document a l'autre: LA
    DEMANDER, comme /documents/non-lus demande deja l'accord OCR »*.

    **Aucun registre nouveau n'est cree, et c'est deliberé.** La file
    `pieces_a_demander.csv` existe, elle porte deja les pieces manquantes de la
    completude, et l'ecran des courriers la lit. Un second registre de demandes
    reproduirait le defaut numero un du produit - plusieurs comptages
    concurrents pour la meme notion. Cette fonction rend donc des lignes au
    format `DOCUMENT_REQUEST_FIELDS`, que `04_completeness_and_kpis` fusionne
    dans la file unique.

    **Elle ne recalcule rien.** Elle rejoue `grouper_par_empreinte` et
    `champs_du_verdict_sur_le_contenu` - les memes fonctions que la
    reconciliation - au lieu de relire les notes en texte. Deriver une demande
    de la PROSE d'une note ferait du libelle une interface, et le premier
    reformulateur casserait la file en silence.

    **Ce qu'elle NE fait pas: elire.** La demande nomme les valeurs en presence
    et demande laquelle vaut. Elle ne suggere pas de reponse: si le produit
    savait laquelle est la bonne, il n'y aurait pas de divergence.
    """
    demandes: list[dict[str, str]] = []
    confrontes = champs_du_verdict_sur_le_contenu(_colonnes(rows))
    for empreinte, groupe in grouper_par_empreinte(rows).items():
        court = empreinte[:12]
        noms = _denominations(groupe)
        ids = ";".join(sorted((row.get("doc_id") or "").strip()
                              for row in groupe if (row.get("doc_id") or "").strip()))
        for champ in confrontes:
            valeurs = [(row.get(champ) or "").strip() for row in groupe]
            pleines = sorted({valeur for valeur in valeurs if valeur})
            if len(pleines) > 1:
                demandes.append({
                    "request_id": f"DIV-{court}-{champ}",
                    "source_ref": court,
                    "priority": PRIORITE_DESACCORD,
                    "status": STATUT_DEMANDE,
                    "subject": (
                        f"Deux valeurs incompatibles pour « {champ} » sur un "
                        "seul et même contenu"
                    ),
                    "expected_piece": (
                        f"la valeur de « {champ} » qui fait foi, parmi : "
                        + " / ".join(pleines)
                    ),
                    "reason": (
                        f"{len(groupe)} dénominations portent le même contenu "
                        f"({noms}) et n'en donnent pas la même lecture. Une "
                        "empreinte identifie un contenu, pas une dénomination : "
                        "aucune ne tranche seule, et rien n'est élu ici."
                    ),
                    "related_doc_ids": ids,
                    "evidence_paths": "",
                    "suggested_diligence": (
                        "Faire trancher par une personne : dire laquelle des "
                        "valeurs vaut, et sur quelle pièce elle se fonde."
                    ),
                })
            elif pleines and "" in valeurs:
                lues = sum(1 for valeur in valeurs if valeur)
                demandes.append({
                    "request_id": f"PAR-{court}-{champ}",
                    "source_ref": court,
                    "priority": PRIORITE_LECTURE_PARTIELLE,
                    "status": STATUT_DEMANDE,
                    "subject": (
                        f"« {champ} » n'est lu que sur une partie des "
                        "dénominations d'un même contenu"
                    ),
                    "expected_piece": f"la valeur de « {champ} » pour ce contenu",
                    "reason": (
                        f"Lu ({pleines[0]}) sur {lues} des {len(groupe)} "
                        f"dénominations de l'empreinte {court} ({noms}), absent "
                        "sur les autres. Une absence n'est pas une seconde "
                        "valeur et ne s'hérite pas d'une dénomination à l'autre."
                    ),
                    "related_doc_ids": ids,
                    "evidence_paths": "",
                    "suggested_diligence": (
                        "Demander la valeur manquante plutôt que de la reprendre "
                        "de l'autre dénomination."
                    ),
                })
    return demandes
