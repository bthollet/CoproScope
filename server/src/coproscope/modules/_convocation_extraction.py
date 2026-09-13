"""Lecture d'une convocation: objets en memoire, aucune ecriture.

L'extracteur est pur - il recoit le texte page par page et rend des objets. La
pagination est conservee parce qu'elle EST l'ancre: la decision de Brice est un
PDF unique avec des renvois cliquables, donc chaque objet doit savoir de quelle
page il vient.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ._convocation_calibrage import Signature, calibrer
from ._convocation_motifs import (
    ANALYSE_OFFRES_RE,
    ANNEXE_NUMEROTEE_RE,
    AVIS_CS_AFFIRME_RE,
    CHOIX_ENTREPRISE_RE,
    CLE_REPARTITION_RE,
    CONTESTATION_RE,
    INTRODUCTEUR_QUESTIONS_RE,
    CORPS_RESOLUTION_RE,
    DATE_AG_RE,
    ENTREPRISE_AVEC_PRIX_RE,
    ENTREPRISE_SANS_PRIX_RE,
    MAJORITE_RE,
    MONTANT_INTITULE_RE,
    NATURE_CONTESTATION,
    NATURE_REJEU,
    ORDRE_DU_JOUR_RE,
    POINT_RE,
    PORTEE_PARTIELLE,
    PORTEE_TOTALE,
    PRIX_NON_LU,
    PRIX_NON_QUANTIFIE,
    PRIX_QUANTIFIE,
    PRIX_UNITAIRE_RE,
    QUESTIONS_VISEES_RE,
    RESOLUTION_PREFIXE_RE,
    REJEU_RE,
    REJEU_TOTAL_RE,
    SOUS_POINT_RE,
    TOTAL_ANNEXE_RE,
)


@dataclass(frozen=True)
class Point:
    """Un point de l'ordre du jour, ou un de ses sous-points."""

    numero: int
    sous_numero: int | None
    objet: str
    page: int

    @property
    def reference(self) -> str:
        return f"{self.numero}-{self.sous_numero}" if self.sous_numero else str(self.numero)


@dataclass
class DevisCite:
    """Un devis nomme par un projet de resolution.

    L'identite n'a pas besoin d'etre conventionnelle: la source numerote
    elle-meme ses sous-resolutions. Le rang ne sert que si elle ne le fait pas.
    """

    numero: int
    sous_numero: int
    objet: str
    entreprise: str
    montant_ttc: str
    etat_prix: str
    # L'intitule annonce, le corps decide. Les deux sont lus separement pour
    # que leur ecart soit un constat au lieu d'un contresens silencieux.
    montant_intitule: str
    discordance_intitule_corps: bool
    majorite_annoncee: str
    cle_repartition: str
    avis_cs_affirme: bool
    analyse_offres_affirmee: bool
    page: int

    @property
    def reference(self) -> str:
        return f"{self.numero}-{self.sous_numero}"


@dataclass(frozen=True)
class DeclarationSurAG:
    """Ce que la convocation dit d'une AUTRE assemblee.

    La contestation et le rejeu ne portent pas sur le meme perimetre et aucun ne
    se deduit de l'autre: le 29/04/2026 conteste seize questions et en rejoue
    quarante-sept.
    """

    nature: str
    ag_visee: str
    questions_visees: tuple[str, ...]
    portee: str
    page: int


@dataclass(frozen=True)
class TotalAnnonce:
    """Un total qu'une resolution attribue a une annexe, donc verifiable."""

    annexe: int
    montant: str
    page: int


@dataclass
class Convocation:
    ag_date: str = ""
    points: list[Point] = field(default_factory=list)
    devis: list[DevisCite] = field(default_factory=list)
    declarations: list[DeclarationSurAG] = field(default_factory=list)
    annexes_citees: tuple[int, ...] = ()
    totaux_annonces: list[TotalAnnonce] = field(default_factory=list)
    points_ordre_du_jour: int = 0
    sous_points_ordre_du_jour: int = 0
    # Faux quand la frontiere ordre du jour / projets n'a pas ete trouvee:
    # l'enumeration se compare alors en partie a elle-meme et ne prouve rien.
    projets_delimites: bool = True
    # La convention de numerotation trouvee dans le document lui-meme.
    # `None` dit qu'aucune enumeration n'a ete reconnue - un fait a
    # remonter, jamais une absence de resolutions.
    signature: str = ""

    @property
    def sous_points(self) -> list[Point]:
        return [p for p in self.points if p.sous_numero]


def _normalise(valeur: str) -> str:
    return re.sub(r"\s+", " ", valeur or "").strip()


def _montant(brut: str) -> str:
    """Normalise un montant sans presumer de la convention decimale.

    Le meme document ecrit "520.556,90" et "290 117.06". Une regle fixe -
    "le point separe les milliers" - transforme donc silencieusement 290 117,06
    en 29 011 706. Le seul repere fiable est positionnel: le dernier separateur
    suivi d'exactement deux chiffres en fin de nombre est le separateur decimal,
    tous les autres separent les milliers.
    """
    compact = re.sub(r"[\s\xa0]", "", brut or "")
    decimal = re.search(r"[.,](\d{2})$", compact)
    if not decimal:
        return re.sub(r"[.,]", "", compact)
    entier = re.sub(r"[.,]", "", compact[: decimal.start()])
    return f"{entier}.{decimal.group(1)}"


def _numeros_de(texte: str, signature: Signature | None = None) -> list[int]:
    """Les numeros de point d'une page, quelle que soit la forme employee.

    Trois gabarits mesures sur deux coproprietes et trois syndics: `12- objet`,
    `12)` avec l'objet a la ligne, et `Resolution n°12 : objet`. Ne connaitre
    que le premier rendait zero point sur les quatre convocations Erables (pseudo).

    Quand une signature a ete calibree sur le document, elle seule fait foi:
    c'est la convention que le document declare, et les motifs generiques ne
    servent plus que de repli pour un document qu'on n'a pas su calibrer.
    """
    if signature is not None:
        return [int(m.group(1)) for m in signature.motif.finditer(texte)]
    prefixes = [int(m.group(1)) for m in RESOLUTION_PREFIXE_RE.finditer(texte)]
    if prefixes:
        return prefixes
    return [int(m.group(1)) for m in POINT_RE.finditer(texte)]


def _pages_ordre_du_jour(pages: list[str], signature: Signature | None = None) -> list[int]:
    """Les pages qui portent l'enumeration annoncee.

    Trois conditions, et les deux dernieres ne sont pas du confort. Une page qui
    nomme l'ordre du jour ne l'enumere pas forcement: la lettre de convocation
    le mentionne aussi. Et un document de 140 pages est plein de nombres en tete
    de ligne - montants, numeros d'article, references de devis - qui ressemblent
    a des points.

    L'ordre du jour se reconnait donc a sa forme propre: il commence a 1 et il
    progresse. Des qu'une page ne prolonge plus la progression, l'enumeration
    est finie, et ce qui suit appartient a autre chose.
    """
    debut = None
    for index, texte in enumerate(pages):
        if ORDRE_DU_JOUR_RE.search(texte) and 1 in _numeros_de(texte, signature):
            debut = index
            break
    if debut is None:
        return []
    suite = [debut]
    sommet = max(_numeros_de(pages[debut], signature) or [0])
    for index in range(debut + 1, len(pages)):
        numeros = _numeros_de(pages[index], signature)
        if not numeros:
            break
        # La page prolonge l'enumeration si elle depasse le sommet atteint et si
        # la PLUPART de ses numeros le prolongent aussi. Un redepart franc -
        # beaucoup de petits numeros - signale les projets developpes et arrete
        # l'ordre du jour.
        #
        # La majorite, et non le minimum: un seul numero aberrant suffisait a
        # tout arreter. Sur la convocation de 2023, un `1` isole en page 4
        # coupait une enumeration saine qui allait jusqu'a 54, et cinq points
        # etaient lus au lieu de cinquante et un.
        prolongent = [n for n in numeros if n >= sommet - 2]
        if max(numeros) > sommet and len(prolongent) * 2 >= len(numeros):
            suite.append(index)
            sommet = max(numeros)
        else:
            break
    return suite



def _objet_valide(objet: str) -> bool:
    """Un point d'ordre du jour porte un libelle, pas un chiffre nu.

    Elargir les separateurs a `)` a fait entrer des cellules de tableau: dans un
    devis scanne de la convocation du 29/04/2026, page 116, `1)` et `2)` suivis
    d'une cellule `1` produisaient deux sous-points `1-1` et `2-2` inexistants.
    Le libelle est la seule chose qui distingue une resolution d'un numero de
    ligne, et une lettre suffit a faire la difference.
    """
    return len(objet) >= 3 and any(caractere.isalpha() for caractere in objet)


def _objet_suivant(lignes: list[str], depart: int) -> str:
    """L'objet d'un point quand le numero est seul sur sa ligne.

    Chez CabinetBeta, l'ordre du jour ecrit `20)` puis l'intitule sur la ligne
    d'apres, et la majorite encore en dessous. Chercher l'objet sur la seule
    ligne du numero ne rend alors rien du tout - c'est ce qui donnait zero point
    sur les quatre convocations Erables (pseudo).
    """
    for ligne in lignes[depart + 1: depart + 3]:
        candidat = _normalise(ligne)
        if len(candidat) < 3:
            continue
        if POINT_RE.match(ligne) or SOUS_POINT_RE.match(ligne):
            break  # le point suivant commence: cet objet n'existe pas
        return candidat
    return ""


def points_annonces(pages: list[str], signature: Signature | None = None) -> list[Point]:
    """L'enumeration de l'ordre du jour: ce que la convocation promet de traiter.

    La lecture est faite ligne a ligne, et non par recherche sur la page, parce
    que l'objet d'un point n'est pas toujours sur la ligne de son numero.
    """
    trouves: dict[tuple[int, int | None], Point] = {}
    motif_point = signature.motif if signature is not None else POINT_RE
    for index in _pages_ordre_du_jour(pages, signature):
        lignes = pages[index].splitlines()
        for rang, ligne in enumerate(lignes):
            sous_point = SOUS_POINT_RE.match(ligne)
            if sous_point:
                numero = int(sous_point.group(1))
                sous = int(sous_point.group(2))
                objet = _normalise(sous_point.group(3)) or _objet_suivant(lignes, rang)
                if not _objet_valide(objet):
                    continue
                cle = (numero, sous)
                if cle not in trouves or len(objet) > len(trouves[cle].objet):
                    trouves[cle] = Point(numero, sous, objet, index + 1)
                continue
            point = motif_point.match(ligne) or RESOLUTION_PREFIXE_RE.match(ligne)
            if not point:
                continue
            numero = int(point.group(1))
            objet = _normalise(point.group(2)) or _objet_suivant(lignes, rang)
            if not _objet_valide(objet):
                continue
            if re.match(r"^\d{1,2}\s*[-–)]", objet):
                continue  # c'est un sous-point, deja capte
            cle = (numero, None)
            if cle not in trouves or len(objet) > len(trouves[cle].objet):
                trouves[cle] = Point(numero, None, objet, index + 1)
    return sorted(trouves.values(), key=lambda p: (p.numero, p.sous_numero or 0))


def _page_de(pages: list[str], position: int) -> int:
    """Page portant ce decalage dans le texte concatene."""
    curseur = 0
    for index, texte in enumerate(pages):
        curseur += len(texte) + 1
        if position < curseur:
            return index + 1
    return len(pages)


def debut_des_projets(pages: list[str]) -> int:
    """Decalage, dans le texte concatene, ou l'ordre du jour cede aux projets.

    Le premier corps de resolution fait foi. A defaut, on retombe sur la fin des
    pages d'ordre du jour, qui suppose une pagination. A defaut encore, zero: on
    lit tout, et le controle d'enumeration perd sa force - c'est un fait a
    remonter, pas un silence.
    """
    plein = "\n".join(pages)
    marqueur = CORPS_RESOLUTION_RE.search(plein)
    if marqueur:
        return marqueur.start()
    pages_odj = _pages_ordre_du_jour(pages)
    if pages_odj and pages_odj[-1] + 1 < len(pages):
        return sum(len(texte) + 1 for texte in pages[: pages_odj[-1] + 1])
    return 0


def devis_cites(pages: list[str], depuis: int = 0) -> list[DevisCite]:
    """Un devis par sous-resolution, avec ce que le texte porte et rien de plus.

    `depuis` est le decalage ou commencent les projets, et exclure l'ordre du
    jour n'est pas un detail de performance. L'ordre du jour porte les memes
    lignes `11.2- ...` que les projets: les lire des deux cotes ferait comparer
    l'enumeration annoncee a elle-meme, et le controle rendrait `complete` quoi
    qu'il arrive. Un controle qui ne peut pas echouer ne controle rien.
    """
    plein = "\n".join(pages)
    debut_projets = depuis
    clotures = [
        (int(m.group(1)), int(m.group(2)), _normalise(m.group(3)), m.start(), m.end())
        for m in SOUS_POINT_RE.finditer(plein)
        if m.start() >= debut_projets and _objet_valide(_normalise(m.group(3)))
    ]
    vus: dict[tuple[int, int], DevisCite] = {}
    for rang, (numero, sous, objet, position, _fin) in enumerate(clotures):
        # La FIN de l'intitule precedent, pas son debut. Couper au debut fait
        # heriter chaque sous-resolution du contenu de la precedente: chez un
        # syndic ou chaque intitule porte `CHOIX DE L'ENTREPRISE : X`, le bloc
        # contient deux entreprises et la recherche retient la premiere, donc la
        # mauvaise. La conversation resolutions a mesure la meme erreur sur ses
        # formules de cloture: 112 issues fausses sur 432, dont 102 inversions
        # adoptee/rejetee, avec tous les indicateurs de volume au vert.
        debut = clotures[rang - 1][4] if rang else 0
        bloc = plein[debut:position + 200]
        entreprise, montant, etat = _lire_prix(bloc, objet)
        cle = (numero, sous)
        if cle in vus and vus[cle].etat_prix != PRIX_NON_LU:
            continue
        majorite = MAJORITE_RE.search(plein[position:position + 300])
        repartition = CLE_REPARTITION_RE.search(bloc)
        annonce = MONTANT_INTITULE_RE.search(objet)
        montant_intitule = _montant(annonce.group("montant")) if annonce else ""
        vus[cle] = DevisCite(
            numero=numero,
            sous_numero=sous,
            objet=objet,
            entreprise=entreprise,
            montant_ttc=montant,
            etat_prix=etat,
            montant_intitule=montant_intitule,
            discordance_intitule_corps=bool(
                montant and montant_intitule and montant != montant_intitule
            ),
            majorite_annoncee=majorite.group(1) if majorite else "",
            cle_repartition=repartition.group(1) if repartition else "",
            avis_cs_affirme=bool(AVIS_CS_AFFIRME_RE.search(bloc)),
            analyse_offres_affirmee=bool(ANALYSE_OFFRES_RE.search(bloc)),
            page=_page_de(pages, position),
        )
    return sorted(vus.values(), key=lambda d: (d.numero, d.sous_numero))


def _lire_prix(bloc: str, objet: str = "") -> tuple[str, str, str]:
    """Entreprise, montant, etat. Des motifs successifs, jamais un optionnel.

    Un groupe optionnel laisse le nom d'entreprise avaler le montant quand
    celui-ci ne correspond pas: "PFM pour 520" rendu comme raison sociale.

    Trois gabarits, du plus riche au plus pauvre. Le dernier lit l'intitule
    lui-meme, parce qu'un syndic peut ne developper aucun corps de resolution:
    l'ordre du jour porte alors `CHOIX DE L'ENTREPRISE : SIMPLEX`, sans prix.
    """
    avec = ENTREPRISE_AVEC_PRIX_RE.search(bloc)
    if avec:
        return _normalise(avec.group("entreprise")), _montant(avec.group("montant")), PRIX_QUANTIFIE
    sans = ENTREPRISE_SANS_PRIX_RE.search(bloc)
    if sans:
        return _normalise(sans.group("entreprise")), "", PRIX_NON_QUANTIFIE
    # L'intitule SEUL, jamais le bloc. Le bloc s'etend vers l'avant pour
    # attraper une phrase pliee, et il attrape alors l'intitule SUIVANT: sur
    # Erables (pseudo) 2026, `19.1) VOTE DU PRINCIPE DES TRAVAUX` - qui ne nomme
    # aucune entreprise - recevait celle de `19.2) CHOIX DE L'ENTREPRISE :
    # BENJAMIN ELEC`. Une entreprise attribuee a la mauvaise resolution est
    # invisible dans les comptages: le nombre de devis lus augmente, et il est
    # faux.
    choix = CHOIX_ENTREPRISE_RE.search(objet)
    if choix:
        return _normalise(choix.group("entreprise")), "", PRIX_NON_QUANTIFIE
    return "", "", PRIX_NON_LU


def declarations_sur_ag(pages: list[str]) -> list[DeclarationSurAG]:
    """Ce que la convocation declare d'une autre assemblee.

    Contestation et rejeu sont lus separement parce qu'ils n'ont ni la meme
    portee ni la meme consequence.
    """
    trouvees: list[DeclarationSurAG] = []
    for index, texte in enumerate(pages):
        aplati = re.sub(r"\s+", " ", texte)
        for correspondance in CONTESTATION_RE.finditer(aplati):
            suite = correspondance.group("suite")
            questions = _questions_visees(suite)
            if not questions:
                continue
            trouvees.append(
                DeclarationSurAG(
                    nature=NATURE_CONTESTATION,
                    ag_visee=_date_visee(suite),
                    questions_visees=questions,
                    portee=PORTEE_PARTIELLE,
                    page=index + 1,
                )
            )
        for correspondance in REJEU_RE.finditer(aplati):
            suite = correspondance.group("suite")
            totale = bool(REJEU_TOTAL_RE.search(suite))
            questions = () if totale else _questions_visees(suite)
            if not totale and not questions:
                continue
            trouvees.append(
                DeclarationSurAG(
                    nature=NATURE_REJEU,
                    ag_visee=_date_visee(suite),
                    questions_visees=questions,
                    portee=PORTEE_TOTALE if totale else PORTEE_PARTIELLE,
                    page=index + 1,
                )
            )
    return trouvees


def _questions_visees(fragment: str) -> tuple[str, ...]:
    """Les numeros ANNONCES comme questions, sous-numeros compris.

    L'introducteur est obligatoire. Sans lui, tout nombre du voisinage passait
    pour un numero de question: six declarations de rejeu inventees sur la
    convocation Erables (pseudo) de 2023, a partir de dates et de references. Une
    declaration fausse coute plus cher qu'une declaration absente.
    """
    annonce = INTRODUCTEUR_QUESTIONS_RE.search(fragment)
    if not annonce:
        return ()
    apres = fragment[annonce.end():]
    avant_date = DATE_AG_RE.split(apres)[0]
    brut = QUESTIONS_VISEES_RE.findall(avant_date)
    # Un numero de question tient sur trois chiffres au plus; une annee non.
    return tuple(dict.fromkeys(n for n in brut if len(n.split("-")[0]) <= 3))


def _date_visee(fragment: str) -> str:
    correspondance = DATE_AG_RE.search(fragment)
    if not correspondance:
        return ""
    jour, mois, annee = correspondance.groups()
    return f"{annee}-{mois}-{jour}"


def annexes_citees(pages: list[str]) -> tuple[int, ...]:
    """Les numeros d'annexe que le texte nomme, dedoublonnes et ordonnes."""
    vus: set[int] = set()
    for texte in pages:
        for correspondance in ANNEXE_NUMEROTEE_RE.finditer(texte):
            numero = int(correspondance.group(1))
            if 1 <= numero <= 20:
                vus.add(numero)
    return tuple(sorted(vus))


def totaux_annonces(pages: list[str]) -> list[TotalAnnonce]:
    """Les totaux qu'une resolution attribue nommement a une annexe."""
    trouves: list[TotalAnnonce] = []
    for index, texte in enumerate(pages):
        aplati = re.sub(r"\s+", " ", texte)
        for correspondance in TOTAL_ANNEXE_RE.finditer(aplati):
            trouves.append(
                TotalAnnonce(
                    annexe=int(correspondance.group("annexe")),
                    montant=_montant(correspondance.group("montant")),
                    page=index + 1,
                )
            )
    return trouves


def parse_convocation(pages: list[str], ag_date: str = "") -> Convocation:
    """Lecture complete. Les comptages de l'ordre du jour servent au controle."""
    signature = calibrer(pages)
    annonces = points_annonces(pages, signature)
    frontiere = debut_des_projets(pages)
    return Convocation(
        ag_date=ag_date,
        points=annonces,
        devis=devis_cites(pages, depuis=frontiere),
        declarations=declarations_sur_ag(pages),
        annexes_citees=annexes_citees(pages),
        totaux_annonces=totaux_annonces(pages),
        points_ordre_du_jour=len([p for p in annonces if not p.sous_numero]),
        sous_points_ordre_du_jour=len([p for p in annonces if p.sous_numero]),
        projets_delimites=frontiere > 0,
        signature=str(signature) if signature else "",
    )
