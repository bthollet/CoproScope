from __future__ import annotations

import re


"""Le libelle public d'un document, et la raison pour laquelle il n'est jamais
son nom de fichier.

**Le constat.** Sur l'instance mesuree le 2026-09-07, la page qui decide de la
diffusion affichait `assignation oubar.pdf` - un patronyme reel, en clair, sur
l'ecran dont c'est precisement le metier de proteger. Une dizaine de points de
rendu faisaient la meme chose. Le garde-fou existant ne bloquait que les
CHEMINS - `C:\\...`, les dossiers `raw`, `restricted`, `private` - et laissait
passer un nom de fichier nu.

**L'axe, et pourquoi ce n'est pas `detecter un patronyme dans un nom de
fichier`.** Chercher un nom de personne dans une chaine est mal pose: rien dans
la forme d'un mot ne dit qu'il designe quelqu'un, et coder les formes observees
chez un cabinet casse au suivant. L'axe est ailleurs.

Un nom de fichier est **ecrit par un tiers** - le syndic, un fournisseur, un
scanner - et il peut contenir n'importe quoi: un patronyme, un numero de lot, un
motif de contentieux. Il n'est donc pas une donnee de l'application, c'est une
donnee du corpus, au meme titre que le contenu du document.

**L'invariant**: le libelle d'un document se derive de ce que le document EST -
son type, sa date, sa reference - jamais de la maniere dont quelqu'un a nomme
son fichier.

**Ce que ca donne hors des valeurs observees**: un type de document inconnu se
degrade en `Document`, une date absente disparait du libelle, et le document
reste identifiable par sa reference courte. Aucun cas ne produit un libelle
vide, et aucun ne laisse passer une chaine non controlee.

Effet secondaire voulu: `Proces-verbal d'AG - 03/07/2024` se lit mieux qu'un
`DIVERS_pv  03072024.pdf` pour un coproprietaire qui decouvre le dossier.
"""


#: Une reference courte, tiree de l'empreinte du contenu. Elle distingue deux
#: pieces de meme type et de meme date sans rien reveler: `doc_id` est deja
#: l'empreinte du document, pas un nom.
_REFERENCE_RE = re.compile(r"[A-Z0-9]{4,}$")

_DATE_ISO_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")

LIBELLE_PAR_DEFAUT = "Document"


def _type_lisible(valeur: object) -> str:
    """`Annexe_Comptable` devient `Annexe comptable`.

    Transformation generique, et c'est volontaire: une table de correspondance
    serait une liste de modalites observees, qui casserait au premier type
    ajoute. Ici un type inconnu reste lisible.
    """

    texte = str(valeur or "").strip()
    if not texte:
        return ""
    mots = [mot for mot in re.split(r"[_\s]+", texte) if mot]
    if not mots:
        return ""
    premier, *suite = mots
    return " ".join([premier.replace("-", "-"), *(mot.lower() for mot in suite)])


def _date_lisible(valeur: object) -> str:
    """`2024-07-03` devient `03/07/2024`. Toute autre forme est ignoree."""

    match = _DATE_ISO_RE.match(str(valeur or "").strip())
    if not match:
        return ""
    annee, mois, jour = match.groups()
    return f"{jour}/{mois}/{annee}"


def reference_courte(doc_id: object) -> str:
    """Les derniers caracteres du `doc_id`, qui est deja une empreinte."""

    texte = str(doc_id or "").strip().upper()
    if not texte:
        return ""
    fin = texte.rsplit("-", 1)[-1]
    return fin[-6:] if _REFERENCE_RE.fullmatch(fin) else ""


def libelle_public_document(row: dict[str, str]) -> str:
    """Le libelle affichable d'un document, derive de ce qu'il est.

    Ne lit JAMAIS `file_name` ni `original_path`. Si un appelant a besoin du
    nom de fichier d'origine - la page de detail d'une piece, par exemple - il
    doit le demander explicitement et assumer sa restriction, pas l'obtenir par
    defaut au detour d'un libelle.
    """

    morceaux: list[str] = []
    type_lisible = _type_lisible(row.get("document_type"))
    if type_lisible:
        morceaux.append(type_lisible)
    date_lisible = _date_lisible(row.get("suspected_date"))
    if date_lisible:
        morceaux.append(f"du {date_lisible}")

    doc_id = str(row.get("doc_id") or "").strip()
    if not morceaux:
        # Sans type ni date, le `doc_id` ENTIER accompagne le libelle: il est
        # publiable - l'interface l'affiche deja ailleurs - et il identifie la
        # piece. Une reference tronquee donnerait `Document TIEUX`, qui
        # n'identifie rien et ne se recherche pas.
        #
        # **Mais il ne tient pas lieu de libelle a lui seul** (`RM-2026-0052`
        # defaut 2). Le reproche du gouvernail est litteralement *un
        # identifiant technique en face de l'utilisateur*, et un `doc_id` nu
        # rendu en titre de carte est exactement cela. Le docstring de ce
        # module l'annoncait deja - *un type de document inconnu se degrade en
        # `Document`* - pendant que cette ligne rendait autre chose: la
        # declaration et le code se contredisaient.
        #
        # L'argument ecrit ici ne portait que contre la TRONCATURE, et il est
        # conserve entier: l'identifiant reste complet, donc cherchable. Seule
        # change la forme du libelle, qui commence maintenant par un mot.
        return f"{LIBELLE_PAR_DEFAUT} ({doc_id})" if doc_id else LIBELLE_PAR_DEFAUT
    libelle = " ".join(morceaux)
    reference = reference_courte(doc_id)
    return f"{libelle} ({reference})" if reference else libelle
