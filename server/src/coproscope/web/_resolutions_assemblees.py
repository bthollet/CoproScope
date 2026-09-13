"""Une assemblee, une ligne: election de l'attestation qui fait foi.

**Le defaut corrige.** Sur l'instance reconstruite du 2026-09-04, le registre
porte 173 lignes de resolutions. 165 d'entre elles sont trois lectures de la
MEME assemblee, rendues cote a cote comme trois assemblees distinctes:

- le proces-verbal d'origine, 55 resolutions, 39 adoptees / 7 rejetees / 8 sans
  vote;
- sa conversion texte, meme serie, memes 55 objets, memes comptages;
- une recomposition a partir de quatre documents partiels couvrant
  respectivement les resolutions 1-7, 8-30, 31-39 et 40-55. Additionnee, elle
  annonce 38 / 7 / 7.

Le lecteur voyait donc trois assemblees, dont une aux comptages faux, et rien
ne lui disait laquelle faisait foi.

**Ce que ce module fait, et ne fait pas.** Il ne supprime aucune ligne. Il
regroupe les documents qui attestent la meme assemblee, en elit un seul, et
declasse les autres en versions ecartees, avec le motif. Le registre reste
entier: une reconstruction le reecrit a l'identique et le regroupement se
refait a la lecture, donc les doublons ne peuvent pas reapparaitre a l'ecran.

**Pourquoi ne pas simplement additionner les fragments.** Parce que c'est ce
qui produit le 38 / 7 / 7. Quatre extractions partielles se recouvrent et se
perdent aux jointures; leur somme n'est pas la serie. Une attestation qui
porte la serie entiere est une preuve, quatre morceaux mis bout a bout sont
une reconstitution.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable

# Formes de fichier qui sont une re-ecriture d'une piece, pas la piece. Le
# depart ne sert que de departage a couverture egale: si l'original et sa
# conversion disent la meme chose, rien n'est perdu; s'ils divergent, c'est
# l'original qui tranche.
FORMES_CONVERTIES = {"md", "markdown", "txt", "html", "htm"}

PIECE_ORIGINE = "origine"
PIECE_CONVERTIE = "convertie"

_DATE_AG_RE = re.compile(r"^AG-(\d{4}-\d{2}-\d{2})$")


def date_de_ag_id(ag_id: str) -> str:
    """Date lue dans l'identifiant d'assemblee, ou chaine vide.

    `_ag_id` du module resolutions retombe sur le `doc_id` quand la date du
    document n'a pas ete extraite. Cette fonction ne reconnait QUE la forme
    datee: tout le reste vaut absence de date, et surtout pas un titre.
    """
    match = _DATE_AG_RE.match((ag_id or "").strip())
    return match.group(1) if match else ""


def normaliser_objet(objet: str) -> str:
    """Objet reduit a sa substance, pour comparer deux lectures d'un meme texte.

    Une conversion markdown et un PDF ne rendent ni les memes espaces ni la
    meme ponctuation. Accents, casse et ponctuation sont donc retires, et la
    comparaison porte sur le debut de l'objet: c'est la ou deux resolutions
    differentes se distinguent, et la ou deux lectures d'une meme resolution
    se rejoignent.
    """
    texte = unicodedata.normalize("NFKD", objet or "")
    texte = "".join(car for car in texte if not unicodedata.combining(car))
    texte = re.sub(r"[^a-z0-9]+", " ", texte.lower()).strip()
    return texte[:80]


@dataclass
class Attestation:
    """Ce qu'un document dit d'une assemblee."""

    doc_id: str
    date: str
    forme: str
    objets: dict[int, str]
    lignes: list[dict[str, str]] = field(default_factory=list)

    @property
    def numeros(self) -> set[int]:
        return set(self.objets)


def meme_assemblee(gauche: Attestation, droite: Attestation) -> bool:
    """Deux documents attestent-ils la meme assemblee.

    Deux signaux, dans cet ordre:

    1. **les dates lues.** Deux dates differentes sont deux assemblees, sans
       discussion. Deux dates identiques sont la meme, c'est ce qui rassemble
       les quatre documents partiels d'un PV scinde;
    2. **les objets, sur les numeros communs.** Quand au moins un des deux
       documents n'a pas de date lue, seul le contenu peut trancher. Deux
       assemblees ont toutes deux une resolution n°1; elles n'ont pas le meme
       objet. Mesure du 2026-09-04: le PV d'origine et sa conversion
       s'accordent sur 55 objets sur 55, chaque fragment s'accorde sur la
       totalite de ce qu'il porte, et l'assemblee de fevrier 2026 diverge sur
       les 8 numeros qu'elle partage avec eux.
    """
    if gauche.date and droite.date:
        return gauche.date == droite.date
    communs = gauche.numeros & droite.numeros
    if not communs:
        return False
    return all(gauche.objets[num] == droite.objets[num] for num in communs)


def regrouper(attestations: list[Attestation]) -> list[list[Attestation]]:
    """Cloture transitive de `meme_assemblee`, en groupes stables.

    La transitivite est necessaire: deux fragments voisins - resolutions 1-7 et
    8-30 - n'ont aucun numero commun et ne se reconnaissent pas directement.
    Ils se rejoignent par leur date, ou par le proces-verbal entier auquel ils
    se rattachent tous les deux.
    """
    groupes: list[list[Attestation]] = []
    for attestation in attestations:
        rattaches = [g for g in groupes if any(meme_assemblee(attestation, a) for a in g)]
        fusion = [attestation]
        for groupe in rattaches:
            fusion.extend(groupe)
        groupes = [g for g in groupes if g not in rattaches]
        groupes.append(fusion)
    return groupes


def _a_relire(lignes: Iterable[dict[str, str]]) -> int:
    return sum(
        1
        for ligne in lignes
        if ligne.get("confiance") == "faible"
        or ligne.get("resultat") in ("VOTE_SANS_FORMULE", "SANS_ISSUE_TRACEE")
    )


def elire(groupe: list[Attestation]) -> tuple[Attestation, list[Attestation]]:
    """Attestation qui fait foi, et celles qui sont ecartees.

    Ordre de preference, du plus decisif au simple departage:

    1. **la couverture de la serie.** Un document qui porte les 55 resolutions
       prime sur un qui en porte 7. C'est le critere qui elimine le comptage
       faux: la somme des fragments n'est pas la serie;
    2. **la forme de la piece.** A couverture egale, l'original prime sur sa
       conversion texte, qui est une re-ecriture;
    3. **la qualite de lecture.** Moins de lignes a relire humainement;
    4. **l'identifiant du document.** Departage purement deterministe, pour
       qu'une reconstruction reelise le meme document et non un autre au
       hasard de l'ordre de lecture.
    """
    serie = len({num for attestation in groupe for num in attestation.numeros}) or 1

    def rang(attestation: Attestation) -> tuple[float, int, int, str]:
        return (
            -len(attestation.numeros) / serie,
            0 if attestation.forme == PIECE_ORIGINE else 1,
            _a_relire(attestation.lignes),
            attestation.doc_id,
        )

    ordonnees = sorted(groupe, key=rang)
    return ordonnees[0], ordonnees[1:]


def motif_ecart(
    ecartee: Attestation,
    retenue: Attestation,
    *,
    taille_serie: int,
    comptages_retenue: dict[str, int],
    comptages_ecartee: dict[str, int],
) -> str:
    """Pourquoi cette version n'est pas celle qui est affichee.

    Le motif est ecrit pour un lecteur qui ne connait ni le coffre ni le
    pipeline: il dit ce que la version contient, pas d'ou elle sort. Aucun
    identifiant technique et aucun nom de fichier n'y figure.
    """
    if len(ecartee.numeros) < taille_serie:
        return (
            f"document partiel: {len(ecartee.numeros)} resolutions sur les "
            f"{taille_serie} de la serie"
        )
    if ecartee.forme == PIECE_CONVERTIE and retenue.forme == PIECE_ORIGINE:
        base = "conversion texte du meme proces-verbal"
    else:
        base = "second exemplaire du meme proces-verbal"
    ecarts = [
        f"{cle} {comptages_ecartee[cle]} au lieu de {comptages_retenue[cle]}"
        for cle in ("adoptees", "rejetees", "sans_vote")
        if comptages_ecartee.get(cle) != comptages_retenue.get(cle)
    ]
    if ecarts:
        return f"{base}, en desaccord sur les comptages: {', '.join(ecarts)}"
    return f"{base}, comptages identiques"


def formes_par_document(instance: Any) -> dict[str, str]:
    """Forme de chaque piece source, lue dans le registre documentaire.

    Le magasin de gouvernance ne porte pas l'extension du fichier d'origine, et
    c'est la seule chose qui distingue un proces-verbal de sa conversion. Une
    absence de registre n'est pas une erreur: tout est alors traite comme une
    piece d'origine, et le departage se fait sur les criteres suivants.
    """
    from ..core.common import read_csv

    try:
        chemin = instance.register("documents")
    except Exception:  # noqa: BLE001 - registre non declare: on n'invente pas.
        return {}
    try:
        if not chemin or not chemin.exists():
            return {}
        _, lignes = read_csv(chemin)
    except Exception:  # noqa: BLE001 - registre illisible: meme traitement.
        return {}
    formes: dict[str, str] = {}
    for ligne in lignes:
        doc_id = str(ligne.get("doc_id") or "")
        if not doc_id:
            continue
        extension = str(ligne.get("extension") or "").strip().lower().lstrip(".")
        formes[doc_id] = PIECE_CONVERTIE if extension in FORMES_CONVERTIES else PIECE_ORIGINE
    return formes


def attestations_depuis(
    lignes: list[dict[str, str]], formes: dict[str, str]
) -> list[Attestation]:
    """Une attestation par document source, dans l'ordre du document."""
    par_doc: dict[str, list[dict[str, str]]] = {}
    for ligne in lignes:
        par_doc.setdefault(str(ligne.get("doc_id") or ligne.get("ag_id") or ""), []).append(ligne)

    attestations: list[Attestation] = []
    for doc_id, brutes in par_doc.items():
        ordonnees = sorted(brutes, key=lambda r: int(r.get("position") or 0))
        objets: dict[int, str] = {}
        for ligne in ordonnees:
            try:
                numero = int(ligne.get("numero") or 0)
            except ValueError:
                continue
            objets.setdefault(numero, normaliser_objet(ligne.get("objet", "")))
        dates = {date_de_ag_id(str(l.get("ag_id") or "")) for l in ordonnees}
        dates.discard("")
        attestations.append(
            Attestation(
                doc_id=doc_id,
                date=sorted(dates)[0] if dates else "",
                forme=formes.get(doc_id, PIECE_ORIGINE),
                objets=objets,
                lignes=ordonnees,
            )
        )
    return attestations
