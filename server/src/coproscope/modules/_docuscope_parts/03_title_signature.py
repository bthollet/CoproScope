from __future__ import annotations

import unicodedata

# --- Signature de forme: le titre d'un proces-verbal d'assemblee -------------
#
# Une seule signature est implementee, et c'est delibere. Six signatures de
# forme ont ete mesurees sur deux cabinets de syndic (37 documents). Cinq ne
# tiennent pas: resolution numerotee, issue de vote et votants/pouvoirs sont
# absents chez le premier cabinet, meme sur ses vrais proces-verbaux; tantiemes
# et articles 24/25/26 apparaissent aussi bien sur les convocations et sur des
# annexes, donc ne separent rien. Seul le titre s'est comporte pareil chez les
# deux: 5 vrais positifs, 0 faux positif sur 37 documents. Les cinq autres ne
# sont pas ecrites "au cas ou": une regle qui ne discrimine pas ajoute du bruit,
# pas de la prudence.
#
# Deux etats distincts, et c'est le coeur du controle:
#   - A_RECLASSER       : le texte est exploitable et le titre manque -> doute.
#   - TEXTE_INSUFFISANT : il n'y a pas de texte a juger -> "je ne sais pas".
# Les confondre est la faute a ne pas refaire: un controle anterieur signalait
# 6 documents dont 4 n'etaient que des echecs d'extraction.

CLASSIFICATION_DOUBT_STATUS = "A_RECLASSER"
CLASSIFICATION_NO_TEXT_STATUS = "TEXTE_INSUFFISANT"

# Motif de titre par type de document, en texte normalise (sans accents).
DEFAULT_TITLE_SIGNATURES: dict[str, str] = {
    "PV_AG": r"proces verbal de l assemblee",
}

# Fenetre de tete, en caracteres de texte utile.
# Mesure: le titre apparait aux positions 0, 0, 26 et 94 sur les quatre
# proces-verbaux des deux cabinets; le premier marqueur d'ordre du jour d'une
# convocation apparait au plus tot a 389. 300 tient dans cet intervalle, avec
# de la marge des deux cotes. Chercher le titre partout, et non en tete, ferait
# passer pour un proces-verbal une convocation qui porte "approbation du
# proces-verbal de l'assemblee precedente" a son ordre du jour.
DEFAULT_TITLE_HEAD_CHARS = 300

# Plancher d'extraction, en caracteres de texte utile.
# Mesure: les six echecs d'extraction des deux cabinets tombent a 0 caractere
# utile une fois les marqueurs de pagination retires; ils valaient 13 a 258
# caracteres bruts, ce qui suffisait a tromper un seuil pose sur le texte brut.
# Le plus petit document reellement porteur de texte en compte 251. 200 separe
# les deux. En cas de doute, mieux vaut un plancher trop haut: il fait dire
# "je ne sais pas", alors qu'un plancher trop bas fait dire "ce n'est pas un
# proces-verbal" a une page scannee.
DEFAULT_USEFUL_TEXT_FLOOR = 200

TITLE_SIGNATURE_READ_LIMIT = 200_000

# Marqueurs de pagination injectes par l'extraction, retires avant de mesurer
# la matiere reellement disponible.
_PAGE_MARKER_RE = re.compile(r"\bpage\s+\d+(\s+sur\s+\d+)?\b")


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _signature_text(value: str) -> str:
    """Minuscules, sans accents, tout caractere non alphanumerique en espace."""
    return re.sub(r"[^a-z0-9]+", " ", _strip_accents(value).lower()).strip()


def _useful_text(value: str) -> str:
    """Texte de signature prive de ses marqueurs de pagination."""
    return re.sub(r"\s+", " ", _PAGE_MARKER_RE.sub("", _signature_text(value))).strip()


# --- Un titre NOMME le document; une mention RENVOIE a un autre --------------
#
# **Axe.** La position de la locution dans la tete du texte est un degre de
# liberte: elle depend de l'en-tete du cabinet, de la pagination injectee par
# l'extraction et de la mise en page. Ce n'est donc pas la position qui separe
# un titre d'une mention.
#
# **Ce qui reste vrai le long de cet axe.** Le titre d'un document OUVRE son
# propre enonce - rien ne le gouverne. Une mention est prise dans un enonce
# qui la precede: "approbation du proces-verbal...", "sera envoye avec le
# proces-verbal...", "source=proces-verbal...".
#
# **Mesure du 2026-09-09**, sur les textes extraits des deux cabinets tels
# qu'ils vivent aujourd'hui dans les instances de travail:
#   - quatre proces-verbaux, locution aux positions 25, 25, 26 et 49: les
#     quatre OUVRENT leur enonce, rien de porteur de mot ne les precede;
#   - une occurrence en position 29 656, dans le CORPS d'un de ces memes PV -
#     "le point procedure sera envoye avec le proces-verbal de l assemblee" -
#     gouvernee par ce qui la precede, donc refusee comme titre.
# Soit 4 vrais positifs et 0 faux positif, le meme score que la fenetre de
# tete employee seule.
#
# **Ce que la fenetre seule laissait passer, et c'est le defaut (1) de
# `RM-2026-0052`.** Mesures le meme jour, en jouant `classify` sur une instance
# jetable: une synthese d'audit CoproScope, une matrice de risques et un
# journal de course sortaient tous les trois `PV_AG` en `AUTO_CLASSIFIED`,
# sans note et sans doute - parce que chacun CITE la locution dans ses 300
# premiers caracteres. Le gouvernail comptait 11 fichiers de travail de
# CoproScope ranges comme proces-verbaux: c'est cette mecanique.
#
# **Hors des valeurs observees.** Un cabinet inconnu qui poserait son titre a
# la suite d'un en-tete sur la MEME ligne n'ouvrirait pas son enonce: le
# document devient `A_RECLASSER`, un doute nomme. La degradation est un doute,
# jamais un type affirme faux.

#: Ce qui termine un enonce. Le retour a la ligne en est un; la ponctuation
#: terminale aussi. Tout le reste - tirets, guillemets, tabulations, filets de
#: separation - est de la decoration et ne clot rien.
_BORNE_ENONCE_RE = re.compile(r"[\r\n.;:!?]+")


def _texte_borne(value: str) -> str:
    """Comme `_signature_text`, mais les bornes d'enonce survivent.

    `_signature_text` ecrase TOUT caractere non alphanumerique en espace, y
    compris les retours a la ligne et la ponctuation terminale. Elle efface
    donc la seule chose qui distingue un titre d'une mention. Ici la borne
    devient un saut de ligne, et le reste un espace.
    """
    plat = _BORNE_ENONCE_RE.sub("\n", _strip_accents(value or "").lower())
    plat = re.sub(r"[^a-z0-9\n]+", " ", plat)
    plat = _PAGE_MARKER_RE.sub("", plat)
    plat = re.sub(r"[ \t]+", " ", plat)
    return re.sub(r" ?\n[ \n]*", "\n", plat).strip()


def _ouvre_son_enonce(texte: str, position: int) -> bool:
    """Rien de porteur de mot ne precede cette position dans son enonce."""
    debut = texte.rfind("\n", 0, position) + 1
    return re.search(r"[a-z0-9]", texte[debut:position]) is None


def _titre_en_tete(head: str, pattern: str) -> bool:
    """Le motif apparait-il en tete ET en tete de son propre enonce ?"""
    return any(
        _ouvre_son_enonce(head, found.start())
        for found in re.finditer(pattern, head)
    )


def _title_signature_config(taxonomy: dict) -> dict:
    raw = taxonomy.get("title_signature", taxonomy.get("signature_titre"))
    return raw if isinstance(raw, dict) else {}


def _title_signatures(taxonomy: dict) -> dict[str, str]:
    config = _title_signature_config(taxonomy)
    raw = config.get("patterns", config.get("motifs"))
    if raw is None:
        return dict(DEFAULT_TITLE_SIGNATURES)
    if not isinstance(raw, dict):
        return {}
    return {
        str(doc_type): str(pattern)
        for doc_type, pattern in raw.items()
        if str(pattern).strip()
    }


def _positive_int(value, fallback: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return number if number > 0 else fallback


def _title_head_chars(taxonomy: dict) -> int:
    config = _title_signature_config(taxonomy)
    return _positive_int(
        config.get("head_window", config.get("fenetre_tete")), DEFAULT_TITLE_HEAD_CHARS
    )


def _useful_text_floor(taxonomy: dict) -> int:
    config = _title_signature_config(taxonomy)
    return _positive_int(
        config.get("useful_text_floor", config.get("plancher_texte_utile")),
        DEFAULT_USEFUL_TEXT_FLOOR,
    )


def _extracted_text(instance, row: dict[str, str]) -> str:
    """Texte extrait seul: ni nom de fichier, ni chemin."""
    workspace_root = instance.root("workspace")
    parts: list[str] = []
    for field in ("text_path", "docling_path"):
        relative = row.get(field, "")
        if not relative:
            continue
        path = workspace_root / relative
        if path.exists():
            parts.append(
                path.read_text(encoding="utf-8", errors="ignore")[:TITLE_SIGNATURE_READ_LIMIT]
            )
    return "\n".join(parts)


def title_signature_matches(
    text: str, patterns: dict[str, str], head_chars: int, floor: int
) -> tuple[list[str], str]:
    """(types dont le titre est lu en tete, texte utile).

    Le second membre sert a distinguer deux etats que le produit confondait:
    un texte utile vide veut dire qu'aucune lecture n'a eu lieu, pour n'importe
    quel type; un texte utile court veut seulement dire qu'un titre n'y est pas
    jugeable.
    """
    useful = _useful_text(text)
    if len(useful) < floor:
        return [], useful
    head = _texte_borne(text)[:head_chars]
    return [
        str(doc_type)
        for doc_type, pattern in (patterns or {}).items()
        if str(pattern).strip() and _titre_en_tete(head, str(pattern))
    ], useful


def title_signature_verdict(text: str, pattern: str, head_chars: int, floor: int) -> str:
    """Retourne "" si le titre est en tete, sinon le statut de doute ou de texte absent."""
    useful = _useful_text(text)
    if len(useful) < floor:
        return CLASSIFICATION_NO_TEXT_STATUS
    if _titre_en_tete(_texte_borne(text)[:head_chars], pattern):
        return ""
    return CLASSIFICATION_DOUBT_STATUS
