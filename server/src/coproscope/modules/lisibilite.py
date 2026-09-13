"""Un document a-t-il ete lu, ou seulement traverse.

**Le defaut que ce module ferme.** L'extraction ecrit un fichier texte par
document, avec un marqueur `===== PAGE n =====` par page, **emis meme quand la
page ne livre rien**. Un scan de 27 pages produit donc 584 caracteres de purs
marqueurs. Tout consommateur qui teste `texte.strip()` conclut alors qu'il a lu
le document, et travaille sur du vide sans le savoir.

Mesure du 2026-09-03 sur l'instance `chaine_decision`, 35 pieces reelles:

    document                              pages   car. reels   fichier texte
    2024-02-21_convocation_AGO.pdf           27            0        584 car.
    06_Dossier_devis_travaux_scan_image       28            0        606 car.
    2024-02-21_projet_de_resolutions.pdf       4            0         83 car.

Le registre, lui, comptait juste: `text_char_count` valait 0 et `status_ocr`
valait `OCR_REQUIRED`. La perte se produisait en aval, chez les lecteurs.

**Deux mesures, deux usages.** `texte_utile` sert a lire; `densite` sert a
decider. Un document peut porter quelques mots vrais et rester illisible: la
question n'est pas "y a-t-il du texte" mais "y en a-t-il assez pour ce nombre
de pages".

**Ce module designe aussi le referentiel de position du depot** - voir la
section suivante. Un decalage de caractere n'a de sens que rapporte a un texte
nomme, et le depot en fabrique plusieurs pour un meme PDF.

Ce module ne lance aucun traitement. Il constate, et laisse l'utilisateur
decider - voir `demande_utilisateur`.
"""

from __future__ import annotations

import re

from . import _marqueur_page
from bisect import bisect_right
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# LE REFERENTIEL DE POSITION
# ---------------------------------------------------------------------------
#
# Le depot fabrique plusieurs textes pour un meme PDF. Mesure du 2026-09-06 sur
# un proces-verbal de dix pages, `DOC-7139EDAD85E4`:
#
#     docuscope `text_path`   59023 car.   debut `===== PAGE 1 =====` puis
#                                           `PROCES-VERBAL DE L...`
#     biffage `_pdf_text`     59035 car.   debut deux lignes blanches puis
#                                           `PROCES-VERBAL DE L...`
#     `texte_utile`           58840 car.   debut `PROCES-VERBAL DE L...`
#     audit360                59044 car.   debut deux lignes blanches puis
#                                           `PROCES-VERBAL DE L...`
#
# Trois de ces textes divergent des le caractere 0. Tant qu'aucun n'est DESIGNE,
# un decalage stocke est ininterpretable, et le premier ancrage ecrit sera faux
# en silence. La fenetre est encore ouverte: `parse_resolutions` calcule de
# vrais decalages mais ne persiste qu'un rang ordinal, donc aucun decalage n'est
# aujourd'hui stocke nulle part.
#
# Le referentiel est le fichier designe par la colonne `text_path` du registre
# `documents`, MARQUEURS DE PAGE COMPRIS. Trois raisons mesurees, pas une
# preference:
#
#   1. c'est le seul des textes concurrents qui soit persiste et adressable par
#      un chemin - les autres sont recalcules en memoire a chaque lecture;
#   2. il est present sur 825 documents sur 825 de `tilleuls_20260906`, et
#      825 sur 825 portent au moins un marqueur, dont le premier au caractere 0;
#   3. il est le seul qui porte encore la frontiere de page. Le nombre de
#      marqueurs egale `page_count` du registre sur 825 documents sur 825.
#
# Tout autre texte du produit est une PROJECTION de celui-ci. Une projection
# qui ne sait pas revenir au referentiel ne peut porter aucun ancrage.

#: La colonne du registre `documents` qui designe le referentiel.
COLONNE_REFERENTIEL = "text_path"

#: Le referentiel, dit en une ligne, pour les traces et les messages d'erreur.
REFERENTIEL = "staging/text/<doc_id>.native.txt (colonne `text_path`), marqueurs compris"

# Le marqueur ecrit par l'extraction. Il n'appartient pas au document: c'est
# une commodite de lecture, et il ne doit jamais compter comme du contenu.
# Il fait en revanche partie du referentiel, parce qu'il en porte les bornes de
# page: c'est la seule frontiere de page que le referentiel connaisse.
MARQUEUR_PAGE_RE = _marqueur_page.MARQUEUR_RE

#: Rendu par `Projection.page` quand le referentiel ne porte aucune borne avant
#: le point demande. On ne devine pas un numero de page qu'on n'a pas.
PAGE_INCONNUE = 0

# Caracteres utiles par page en dessous desquels un document n'a pas ete lu.
# La distribution mesuree est bimodale avec un gouffre: 20 a 22 caracteres par
# page pour les documents scannes, 949 et au-dela pour les autres. N'importe
# quelle valeur dans cet intervalle convient, donc le seuil ne demande pas
# d'arbitrage fin. 150 est pris au large du bord bas.
SEUIL_CAR_PAR_PAGE = 150

LISIBLE = "LISIBLE"
ILLISIBLE = "ILLISIBLE"
INDETERMINE = "INDETERMINE"


@dataclass(frozen=True)
class Projection:
    """Un texte derive du referentiel, et de quoi y revenir.

    `texte` est exactement ce que rend `texte_utile`. Ce qui s'ajoute est la
    table des tranches conservees: chaque tranche dit ou elle commence dans la
    projection, ou elle commencait dans le referentiel, et sa longueur. Cela
    suffit a reconvertir n'importe quel decalage, donc a nommer une page.

    Sans cette table, une projection est un cul-de-sac: `texte_utile` retire les
    marqueurs puis applique un `strip()` global, si bien que son resultat est
    decale des le caractere 0 et qu'aucun retour n'est possible.
    """

    texte: str
    #: (debut dans la projection, debut dans le referentiel, longueur)
    tranches: tuple[tuple[int, int, int], ...]
    #: Decalage, dans le referentiel, du marqueur qui ouvre chaque page.
    bornes_de_page: tuple[int, ...]

    def position_referentiel(self, decalage: int) -> int:
        """Le meme point, exprime dans le referentiel.

        `decalage` va de 0 a `len(self.texte)` inclus, pour qu'une fin de
        segment soit convertible au meme titre qu'un debut.
        """
        if not 0 <= decalage <= len(self.texte):
            raise ValueError(
                f"decalage {decalage} hors de la projection (0 a {len(self.texte)})"
            )
        if not self.tranches:
            raise ValueError(
                "projection vide: aucune position du referentiel ne lui correspond"
            )
        debuts = [tranche[0] for tranche in self.tranches]
        rang = bisect_right(debuts, decalage) - 1
        debut_projete, debut_referentiel, _ = self.tranches[rang]
        return debut_referentiel + (decalage - debut_projete)

    def page(self, decalage: int) -> int:
        """La page du referentiel qui porte ce point de la projection.

        Rend `PAGE_INCONNUE` si aucune borne ne precede le point. On ne devine
        pas: un referentiel sans marqueur ne dit pas ou commencent ses pages, et
        repondre 1 serait une reponse fausse en silence pour un document qui en
        compte quarante.
        """
        return self.page_du_referentiel(self.position_referentiel(decalage))

    def page_du_referentiel(self, position: int) -> int:
        """La page qui porte ce decalage du referentiel, 1 pour la premiere."""
        rang = bisect_right(self.bornes_de_page, position)
        return rang if rang else PAGE_INCONNUE


def projeter(brut: str) -> Projection:
    """Projette le referentiel sur son texte utile, sans perdre le chemin retour.

    Le texte rendu est identique au caractere pres a `texte_utile(brut)` - c'est
    d'ailleurs cette fonction qui appelle celle-ci, pour que les deux ne
    puissent pas diverger.
    """
    source = brut or ""
    conservees: list[tuple[int, int]] = []
    bornes_de_page: list[int] = []
    curseur = 0
    for marqueur in MARQUEUR_PAGE_RE.finditer(source):
        bornes_de_page.append(marqueur.start())
        if marqueur.start() > curseur:
            conservees.append((curseur, marqueur.start()))
        curseur = marqueur.end()
    if curseur < len(source):
        conservees.append((curseur, len(source)))

    # Le `strip()` global de la projection, reporte sur les tranches. C'est lui
    # qui decale le resultat des le caractere 0, donc lui qu'il faut suivre.
    concatene = "".join(source[debut:fin] for debut, fin in conservees)
    if not concatene.strip():
        return Projection("", (), tuple(bornes_de_page))
    a_rogner = len(concatene) - len(concatene.lstrip())
    for index, (debut, fin) in enumerate(conservees):
        if a_rogner < fin - debut:
            conservees = [(debut + a_rogner, fin), *conservees[index + 1 :]]
            break
        a_rogner -= fin - debut
    a_rogner = len(concatene) - len(concatene.rstrip())
    for index in range(len(conservees) - 1, -1, -1):
        debut, fin = conservees[index]
        if a_rogner < fin - debut:
            conservees = [*conservees[:index], (debut, fin - a_rogner)]
            break
        a_rogner -= fin - debut

    tranches: list[tuple[int, int, int]] = []
    curseur_projete = 0
    for debut, fin in conservees:
        tranches.append((curseur_projete, debut, fin - debut))
        curseur_projete += fin - debut
    return Projection(
        "".join(source[debut:fin] for debut, fin in conservees),
        tuple(tranches),
        tuple(bornes_de_page),
    )


def pages_du_referentiel(brut: str) -> list[str]:
    """Le referentiel decoupe sur SES bornes a lui, une chaine par page.

    Une page est ce qui suit un marqueur, jusqu'au marqueur suivant. Rien
    d'autre ne fait frontiere. En particulier pas le saut de page `\f`: quand il
    est present il appartient au contenu, et decouper dessus fabrique une
    pagination fausse - mesure du 2026-09-07 sur les 825 documents de
    `tilleuls_20260906`, quatre fichiers en portent trois chacun, dont un
    document de 143 pages qu'un tel decoupage reduirait a 4.

    Deux degradations, toutes deux visibles plutot que silencieuses:

    - un referentiel sans aucun marqueur rend une page unique. L'appelant doit
      la nommer comme un ancrage degrade, pas la presenter comme une page;
    - un referentiel qui porte du contenu AVANT son premier marqueur rend lui
      aussi une page unique. Ce contenu n'appartient a aucune page declaree:
      l'attribuer a la premiere inventerait une borne, l'ecarter perdrait du
      texte. Mesure du 2026-09-07: aucun des 825 fichiers n'est dans ce cas,
      tous ouvrent sur un marqueur au caractere 0.
    """
    source = brut or ""
    if not source:
        return []
    bornes = list(MARQUEUR_PAGE_RE.finditer(source))
    if not bornes or source[: bornes[0].start()].strip():
        return [source]
    return [
        source[borne.end() : bornes[rang + 1].start() if rang + 1 < len(bornes) else len(source)]
        for rang, borne in enumerate(bornes)
    ]


def texte_utile(brut: str) -> str:
    """Le texte du document, marqueurs de page retires.

    A employer partout ou l'on teste si un document a du contenu. `brut.strip()`
    rend vrai sur un fichier de marqueurs; celui-ci rend faux.

    Le resultat est inchange depuis toujours. Ce qui a change est qu'il vient
    desormais de `projeter`, qui sait revenir au referentiel: employer
    `projeter(brut)` plutot que cette fonction des qu'un decalage doit etre
    conserve, cite ou affiche.
    """
    return projeter(brut).texte


def densite(brut: str, pages: int) -> float:
    """Caracteres utiles par page, ou 0.0 si le nombre de pages est inconnu."""
    if not pages or pages < 1:
        return 0.0
    return len(texte_utile(brut)) / pages


def verdict(brut: str, pages: int) -> str:
    """LISIBLE, ILLISIBLE, ou INDETERMINE quand la pagination manque.

    Sans nombre de pages, la densite n'est pas calculable. On ne tranche pas:
    un document d'une page et un document de trente ne se jugent pas au meme
    volume de texte.
    """
    utile = texte_utile(brut)
    if not pages or pages < 1:
        return LISIBLE if utile else INDETERMINE
    return LISIBLE if densite(brut, pages) >= SEUIL_CAR_PAR_PAGE else ILLISIBLE


# Mesure du 2026-09-03, moteur tesseract sur ce poste: 3 pages en 15,3 secondes,
# demarrage du processus compris. La premiere valeur annoncee, 3 secondes par
# page, venait d'un document d'une seule page et sous-estimait d'un facteur deux.
SECONDES_PAR_PAGE = 5


def _duree_estimee(pages: int) -> str:
    """Ordre de grandeur, pas une promesse."""
    secondes = max(pages, 1) * SECONDES_PAR_PAGE
    if secondes < 60:
        return "moins d'une minute"
    minutes = round(secondes / 60)
    return f"environ {minutes} minute{'s' if minutes > 1 else ''}"


def demande_utilisateur(nom: str, pages: int, brut: str = "") -> dict[str, object]:
    """Le texte a montrer pour demander l'accord, en francais courant.

    Trois choses qu'un novice doit pouvoir comprendre sans savoir ce qu'est
    l'OCR: ce qui ne va pas, ou le traitement a lieu, et combien de temps il
    prend. Le sigle est developpe a sa premiere occurrence, comme l'exige la
    consigne du depot sur les documents destines aux coproprietaires.

    On ne dit pas "le document est vide": il ne l'est pas, il est en image. La
    nuance compte, parce qu'elle explique pourquoi le traitement peut reussir.
    """
    car = len(texte_utile(brut))
    return {
        # Ces chaines sont lues par un coproprietaire, pas par un agent: elles
        # portent donc les accents, comme les libelles de `resolutions_view`.
        "titre": f"« {nom} » n'a pas pu être lu",
        "constat": (
            f"Ce document fait {pages} page{'s' if pages > 1 else ''} et CoproScope "
            f"n'y a trouvé aucun texte exploitable ({car} caractères). "
            "Il s'agit très probablement d'un document scanné : les pages "
            "sont des images, pas du texte."
        ),
        "remede": (
            "La reconnaissance optique de caractères, ou OCR, transforme ces "
            "images en texte lisible par la machine. Le document d'origine n'est "
            "jamais modifié : le texte reconnu est écrit à côté."
        ),
        "confidentialite": (
            "Le traitement se fait entièrement sur votre ordinateur. Aucun "
            "document n'est envoyé sur internet."
        ),
        "duree": f"Cela prendra {_duree_estimee(pages)} pour ce document.",
        "question": "Voulez-vous lancer la reconnaissance de texte ?",
        "pages": pages,
        "caracteres_trouves": car,
    }


TABLE_DECISIONS = "lisibilite_decisions"
CLES_DECISIONS = ("doc_id", "origine")
CHAMPS_DECISIONS = (
    "doc_id",
    "origine",
    "decision",
    "decide_le",
    "pages",
    "caracteres_avant",
    "nom",
)

ACCEPTE = "ACCEPTE"
REFUSE = "REFUSE"


def enregistrer_decision(instance, doc_id: str, decision: str, *, nom: str = "",
                         pages: int = 0, caracteres: int = 0, horodatage: str = "") -> None:
    """Garde la reponse de l'utilisateur, pour ne plus la lui redemander.

    Ecrite avec `origine = CORRIGE_HUMAIN`: c'est ce qui la protege du
    remplacement lors d'une nouvelle extraction. Un refus doit survivre aussi
    longtemps qu'un accord - redemander a chaque passage serait harceler
    l'utilisateur pour une question a laquelle il a repondu.
    """
    from datetime import datetime, timezone

    from ..vault.gouvernance_store import ORIGINE_CORRIGE, remplacer_pour_documents

    ligne = {
        "doc_id": doc_id,
        "origine": ORIGINE_CORRIGE,
        "decision": decision,
        "decide_le": horodatage or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pages": str(pages),
        "caracteres_avant": str(caracteres),
        "nom": nom,
    }
    remplacer_pour_documents(
        instance, CHAMPS_DECISIONS, [ligne], [doc_id],
        table=TABLE_DECISIONS, cles=CLES_DECISIONS,
    )


def decisions(instance) -> dict[str, str]:
    """Les reponses deja donnees, par document."""
    from ..vault.gouvernance_store import lire

    lignes = lire(instance, table=TABLE_DECISIONS, ordre="decide_le DESC")
    return {ligne["doc_id"]: ligne.get("decision", "") for ligne in lignes if ligne.get("doc_id")}
