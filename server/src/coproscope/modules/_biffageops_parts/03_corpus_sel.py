from __future__ import annotations

import base64
import hashlib
import secrets
import unicodedata


"""Sel d'instance et derivation des alias du corpus caviarde.

Le sel est un secret local propre a une instance. Il ne vit jamais dans Git et
ne se copie pas d'une instance a l'autre: c'est ce qui empeche deux coffres de
coproprietaires differents de produire le meme alias pour la meme personne.
"""


CORPUS_SALT_FILENAME = "sel_alias.key"
CORPUS_SALT_BYTES = 32
CORPUS_SALT_HEADER = (
    "# CoproScope - sel de derivation des alias du corpus caviarde.\n"
    "# Secret local d'instance. Ne jamais commiter, ne jamais copier vers une\n"
    "# autre instance, ne jamais publier: il permet de relier deux alias.\n"
)
ALIAS_SCHEMA = "personne-sel-v1"


def _corpus_settings(instance: InstanceConfig) -> dict:
    settings = instance.settings()
    value = settings.get("corpus_caviarde")
    return dict(value) if isinstance(value, dict) else {}


def _corpus_vault_root(instance: InstanceConfig) -> Path | None:
    settings = instance.settings()
    vault = settings.get("vault")
    if not isinstance(vault, dict):
        return None
    raw = vault.get("local_root") or vault.get("local") or vault.get("cache_root")
    if not raw:
        return None
    return instance.resolve_path(str(raw))


def corpus_salt_path(instance: InstanceConfig) -> Path:
    """Ou vit le sel de cette instance, par ordre de preference."""

    configured = _corpus_settings(instance).get("salt_path")
    if configured:
        resolved = instance.resolve_path(str(configured))
        if resolved is not None:
            return resolved
    vault_root = _corpus_vault_root(instance)
    if vault_root is not None:
        return vault_root / "corpus_caviarde" / CORPUS_SALT_FILENAME
    restricted = instance.root_list("restricted")
    if restricted:
        return restricted[0] / "corpus_caviarde" / CORPUS_SALT_FILENAME
    return instance.root("workspace") / "system" / "private" / CORPUS_SALT_FILENAME


def _decode_salt(raw: str) -> bytes | None:
    for line in raw.splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith("#"):
            continue
        try:
            decoded = base64.b64decode(candidate, validate=True)
        except Exception:  # noqa: BLE001
            return None
        return decoded if len(decoded) >= 16 else None
    return None


def load_corpus_salt(instance: InstanceConfig, *, create: bool = True) -> bytes:
    """Lit le sel de l'instance, et le cree au premier appel si autorise."""

    path = corpus_salt_path(instance)
    if path.exists():
        decoded = _decode_salt(path.read_text(encoding="utf-8"))
        if decoded is not None:
            return decoded
        raise RuntimeError(
            f"Le sel du corpus caviarde est illisible: {path}. "
            "Ne pas le regenerer sans decision explicite: les alias deja "
            "produits deviendraient incoherents."
        )
    if not create:
        raise FileNotFoundError(path)
    salt = secrets.token_bytes(CORPUS_SALT_BYTES)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        CORPUS_SALT_HEADER + base64.b64encode(salt).decode("ascii") + "\n",
        encoding="utf-8",
    )
    try:
        path.chmod(0o600)
    except OSError:  # noqa: BLE001 - Windows n'applique pas toujours le mode POSIX
        pass
    return salt


def corpus_salt_fingerprint(salt: bytes) -> str:
    """Empreinte publiable du sel: elle identifie le sel sans le reveler."""

    return hashlib.sha256(b"coproscope-sel-empreinte-v1" + salt).hexdigest()[:12]


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_identity_key(value: str) -> str:
    """Forme canonique d'un fragment d'identite: sans accent, sans ponctuation."""

    cleaned = strip_accents(value).upper()
    return re.sub(r"[^A-Z0-9]+", "", cleaned)


ARBRES = """
ABRICOTIER ACACIA AGAVE AJONC ALISIER ALOES AMANDIER ANEMONE ANETH ANGELIQUE
ANIS ARBOUSIER ARGOUSIER ARMOISE ARNICA ASPERGE ASTER AUBEPINE AUBIER AULNE
AURONE AVOCATIER AVOINE AZALEE BAMBOU BANANIER BARDANE BASILIC BEGONIA
BERGAMOTE BETULE BIGNONE BLEUET BOULEAU BOURDAINE BOURRACHE BRUGNON BRUYERE
BUGLE BUIS CACAOYER CAMELIA CAMOMILLE CANNELLE CAPUCINE CARDAMINE CAROUBIER
CARVI CASSIS CEDRAT CEDRE CELERI CERFEUIL CERISIER CHANVRE CHARDON CHARME
CHATAIGNIER CHENE CHEVREFEUILLE CHICOREE CIBOULETTE CIGUE CISTE CITRONNIER
CLEMATITE COGNASSIER COLZA CONCOMBRE CORIANDRE CORMIER CORNOUILLER COTONNIER
COUDRIER COURGE CRESSON CUMIN CYCLAMEN CYPRES DAHLIA DATTIER DIGITALE DOUGLAS
DRAGONNIER EGLANTIER EPICEA EPINE ERABLE ESTRAGON EUCALYPTUS FENOUIL FEVIER
FIGUIER FOUGERE FRAISIER FRAMBOISIER FRENE FUSAIN GARDENIA GENET GENEVRIER
GENTIANE GERANIUM GINKGO GIROFLEE GLAIEUL GLYCINE GRENADIER GROSEILLIER
HELIANTHE HELLEBORE HETRE HIBISCUS HORTENSIA HOUBLON HOUX HYSOPE IGNAME IRIS
IVRAIE JACINTHE JASMIN JONC JONQUILLE JUJUBIER LAURIER LENTISQUE LIERRE LISERON
LOTUS LUPIN LUZERNE MACRE MAGNOLIA MAHONIA MARJOLAINE MARRONNIER MELEZE MELILOT
MELISSE MENTHE MERISIER MICOCOULIER MILLEPERTUIS MIMOSA MIRABELLIER MOLENE
MOUSSE MUGUET MURIER MUSCARI MYOSOTIS MYRTE MYRTILLE NEFLIER NENUPHAR NERPRUN
NOISETIER NOYER OEILLET OLIVIER ONAGRE ORCHIDEE ORIGAN ORME ORTIE OSEILLE OSIER
PAQUERETTE PASSIFLORE PAULOWNIA PECHER PEUPLIER PIMPRENELLE PISTACHIER PLANTAIN
PLATANE POIRIER POMMIER PRIMEVERE PRUNELLIER PRUNIER QUINQUINA RAIFORT
RENONCULE RESEDA RHUBARBE ROBINIER ROMARIN RONCE ROSEAU ROSIER SAPIN SARRIETTE
SAULE SCABIEUSE SEIGLE SEQUOIA SORBIER SOUCI SUREAU SYCOMORE TAMARIS TANAISIE
THYM TILLEUL TREFLE TROENE TULIPE VALERIANE VANILLE VERVEINE VESCE VIGNE
VIOLETTE VIORNE YUCCA ZINNIA
""".split()

COULEURS = """
ABRICOT ACAJOU AMBRE AMETHYSTE ANTHRACITE ARDOISE ARGENT AUBERGINE AURORE AZUR
BEIGE BISTRE BLEU BLOND BORDEAUX BRIQUE BRONZE BRUN CAFE CANARI CARAMEL CARMIN
CELADON CENDRE CERISE CHAMOIS CHOCOLAT CITRON COBALT COQUELICOT CORAIL CRAIE
CREME CUIVRE CYAN ECARLATE ECRU EMERAUDE FAUVE FRAISE GRENAT GRIS INDIGO
IVOIRE JADE JAUNE MAGENTA MARINE MARRON MIEL MOUTARDE NACRE NOISETTE NOIR OCRE
OLIVE OPALE ORANGE OUTREMER PAILLE PASTEL PECHE PERLE POURPRE PRUNE QUARTZ
REGLISSE ROSE ROUGE ROUILLE RUBIS SABLE SANGUINE SAPHIR SEPIA SOUFRE TAUPE
TOPAZE TURQUOISE VERMILLON VERT VIOLET ZINC
""".split()

MOTS_PSEUDONYMES = frozenset(ARBRES) | frozenset(COULEURS)


def _alias_digest(salt: bytes, kind: str, key: str, size: int) -> str:
    mac = hashlib.blake2b(
        f"{kind}::{key}".encode("utf-8"),
        key=salt,
        digest_size=size,
        person=b"coproscope-alias",
    )
    return mac.hexdigest().upper()


def _rang(salt: bytes, kind: str, key: str) -> int:
    return int(_alias_digest(salt, kind, key, 8), 16)


def racine_candidats(salt: bytes, nom_key: str, essais: int = 6000):
    """Les racines possibles pour un nom de famille, par ordre de preference.

    Le sel decide du mot; l'ordre est deterministe. Le deuxieme candidat ne sert
    que si le premier est deja pris par une autre famille de l'instance.
    """

    depart = _rang(salt, "personne.nom", nom_key)
    taille = len(ARBRES)
    for tentative in range(essais):
        mot = ARBRES[(depart + tentative) % taille]
        suffixe = tentative // taille
        yield mot if not suffixe else f"{mot}{suffixe + 1}"


def prenom_candidats(salt: bytes, nom_key: str, prenom_key: str, essais: int = 4000):
    depart = _rang(salt, "personne.prenom", f"{nom_key}::{prenom_key}")
    taille = len(COULEURS)
    for tentative in range(essais):
        mot = COULEURS[(depart + tentative) % taille]
        suffixe = tentative // taille
        yield mot if not suffixe else f"{mot}{suffixe + 1}"


def person_alias(salt: bytes, surname: str, given: str = "") -> str:
    """Alias sans registre: le premier candidat, sans arbitrage de collision.

    La chaine de production passe par `RegistrePseudonymes`, qui tranche les
    collisions et garde la trace. Cette fonction reste le chemin court des
    tests et des appels ponctuels.
    """

    nom_key = normalize_identity_key(surname)
    if not nom_key:
        nom_key = normalize_identity_key(given)
        given = ""
    racine = next(iter(racine_candidats(salt, nom_key)))
    prenom_key = normalize_identity_key(given)
    if not prenom_key:
        return f"PERSONNE_{racine}"
    return f"PERSONNE_{racine}_{next(iter(prenom_candidats(salt, nom_key, prenom_key)))}"


def value_alias(salt: bytes, category: str, value: str) -> str:
    """Alias des identifiants techniques.

    Email, telephone, IBAN et secrets gardent une empreinte hexadecimale: ce
    sont des chaines techniques, un lecteur n'a pas besoin de les prononcer, et
    la forme hexadecimale dit d'un coup d'oeil qu'il ne s'agit pas d'un nom.
    """

    prefix = {
        "EMAIL": "EMAIL",
        "TELEPHONE": "TELEPHONE",
        "IBAN": "IBAN",
        "SECRET": "SECRET",
    }.get(category, category)
    if category == "EMAIL":
        key = strip_accents(value).strip().lower()
    elif category == "TELEPHONE":
        key = re.sub(r"\D+", "", value)
    elif category == "IBAN":
        key = re.sub(r"[^A-Z0-9]+", "", value.upper())
    else:
        key = normalize_identity_key(value)
    return f"{prefix}_{_alias_digest(salt, f'valeur.{category}', key, 4)}"


def alias_ephemere(salt: bytes, doc_id: str, nom: str, prenom: str = "") -> str:
    """L'alias d'une personne que l'annuaire ne connait pas.

    **Ephemere veut dire: propre a ce document, et a lui seul.** Le meme nom
    dans une autre piece recevra un autre alias, et c'est voulu.

    La stabilite d'un alias est une propriete de l'ENTITE, pas de la chaine de
    caracteres. Un alias stable attribue a une chaine que personne n'a reconnue
    recreerait le defaut central du cahier des charges d'origine - `l'alias est
    attache a une valeur, pas a une entite` - et propagerait un faux positif a
    tout le corpus sans qu'aucun humain l'ait valide.

    La contrepartie est assumee: deux mentions du meme inconnu dans deux pieces
    restent non reliees jusqu'a ce qu'un humain cree l'entite.
    """

    cle = f"{normalize_identity_key(nom)}.{normalize_identity_key(prenom)}"
    empreinte = _alias_digest(salt, f"ephemere.{doc_id}", cle, 4)
    return f"PERSONNE_NON_RECONNUE_{empreinte}"


ALIAS_PATTERN = re.compile(
    r"\b(?:PERSONNE_[A-Z]{3,}\d?(?:_[A-Z]{3,}\d?)?"
    r"|(?:EMAIL|TELEPHONE|IBAN|SECRET)_[0-9A-F]{8})\b"
)


def is_alias(value: str) -> bool:
    return bool(ALIAS_PATTERN.fullmatch(value.strip()))
