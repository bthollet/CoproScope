"""L'axe: le texte enonce-t-il l'issue du vote pour CETTE resolution ?

Ce module ne connait qu'une question, et il la pose de trois manieres de plus en
plus larges. Il est separe de `_resolutions_motifs` parce que ce qui est ecrit
ici n'est pas un motif de plus: c'est la maniere dont on choisit entre les
motifs, et cette maniere doit se relire seule.

--------------------------------------------------------------------------
L'AXE, ET CE QUI RESTE VRAI LE LONG DE L'AXE
--------------------------------------------------------------------------

**L'axe.** `Le texte enonce-t-il l'issue du vote pour cette resolution ?` Les
redactions qui l'expriment sont les MODALITES de cet axe, et elles varient d'un
cabinet a l'autre. Mesure du 2026-09-08 sur deux cabinets et 360 pieces
sources: les deux ecrivent `cette resolution est <issue>`, et les deux ecrivent
aussi, plus rarement, autre chose - `la resolution est rejetee` huit fois,
`Cette resolution sera reportee` une fois. La formule unique n'etait donc deja
pas une description juste de la matiere disponible.

**Ce qui reste invariant le long de l'axe.** L'issue est PREDIQUEE d'une
designation qui POINTE la resolution courante. Trois parts, dont une seule est
libre:

1. une designation deictique - `cette`, `ladite`, `la presente`, `la ... n°3` -
   qui distingue le constat (`cette resolution est adoptee`) de la mention
   (`l'une des decisions adoptees`, `en cas de decision regulierement adoptee`).
   Les deux mentions existent dans les corpus et une regle sans deixis les
   compterait comme des votes;
2. un mot de liaison, qui est le degre de liberte reel: `est`, `sera`, `a ete`,
   `fut`, `demeure`;
3. un participe d'issue, dont le vocabulaire est traite ailleurs
   (`ISSUE_PREFIXES`) et dont le residu est deja nomme (`ISSUE_NON_RECONNUE`).

**Ce que le code en fait: trois anneaux, du plus sur au plus large.**

- `ANNEAU_STRICT`  la formule mesuree sur les deux cabinets. Sert d'ANCRE de
  segmentation, parce qu'une ancre fausse deplace toutes les frontieres.
- `ANNEAU_LARGE`   la meme structure, liaison libre. Sert d'ancre SEULEMENT si
  l'anneau strict ne rend rien en serie, et sert toujours de LECTEUR a
  l'interieur d'un segment deja delimite - la, un faux positif nomme mal une
  issue, il ne casse pas la segmentation.
- `TEMOIN`         n'importe quel participe d'issue. Ne cree JAMAIS ni ancre ni
  resolution. Il ne sert qu'a une chose: dire que le document enonce des issues
  que la chaine ne sait pas lire, au lieu de rendre zero en silence.

**Hors des valeurs observees.** Un cabinet qui ecrirait l'issue sans designation
- un `ADOPTEE` seul en fin de bloc, une colonne `Resultat : rejetee` - n'est
  reconnu par aucun des deux anneaux. Ce n'est pas un oubli: la deixis est ce
  qui separe le constat de la mention, et l'abandonner ferait entrer les
  mentions. Ce cas-la tombe donc sur le TEMOIN, qui le NOMME
  (`ISSUE_ENONCEE_NON_LUE`, `issues_muettes`) et fait passer le run en `WARN`.
  La degradation est bruyante, et c'est tout ce qu'on lui demande.
  **Lire la section sur le droit, plus bas, avant de considerer ce residu comme
  marginal: c'est la forme que le decret decrit.**

**Mesure du cout de l'elargissement**, faite avant de l'ecrire, sur les 360
pieces des deux cabinets: l'anneau large ajoute 15 correspondances a l'anneau
strict. Neuf sont de vraies issues manquees (`la resolution est rejetee` x8,
`Cette resolution sera reportee` x1). Six n'en sont pas: `La decision est
favorable au SDC` x3, `Cette decision a ete confirme par jugement` x2, `la
question est portee` x1 - toutes des mentions de justice, aucune d'un vote. Ces
six ne portent aucun mot du vocabulaire d'issue: elles ressortent donc
`ISSUE_ENONCEE_NON_LUE`, c'est-a-dire appelees a relecture, jamais comptees.
C'est cette mesure, et non un principe, qui interdit d'employer l'anneau large
comme ancre quand l'anneau strict suffit.

--------------------------------------------------------------------------
CE QUE LE DROIT DIT, VERIFIE A SA DATE DE VERSION
--------------------------------------------------------------------------

Verifie sur Legifrance le 2026-09-08, textes consolides lus a cette date.

**Le CONTENU est norme, la REDACTION est libre.** Decret 67-223 article 17,
`LEGIARTI000042078689`, en vigueur au 2026-09-08: « Le proces-verbal comporte,
sous l'intitule de chaque question inscrite a l'ordre du jour, le resultat du
vote. » L'obligation porte sur la PRESENCE du resultat, jamais sur les mots qui
l'expriment. Aucun texte reglementaire n'impose de formule; l'article 17-1 du
meme decret, `LEGIARTI000042076794`, le confirme a l'envers en validant un
proces-verbal formellement irregulier « des lors qu'il est possible de
reconstituer le sens du vote ». Le pouvoir reglementaire sait normer une forme
quand il le veut - il l'a fait pour le formulaire de vote par correspondance,
arrete du 2 juillet 2020 - et ne l'a pas fait pour le proces-verbal.

**Consequence directe: `cette resolution est adoptee` est un usage de cabinet.**
Le mot `resolution` ne figure meme pas a l'article 17. Dans la loi 65-557, le
mot dominant est `decision` - 95 occurrences dans 49 articles, contre 11 pour
`resolution` dans 8 articles. C'est exactement une modalite observee, et c'est
pourquoi la designation admise ici couvre `resolution`, `decision`, `question`
et `motion` plutot que le seul mot d'un cabinet.

**Et voici ce que le droit apprend sur le RESIDU, qui change son importance.**
L'article 17 rattache le resultat a `l'intitule de chaque question inscrite a
l'ordre du jour`: legalement, l'issue se pose SOUS un titre, et rien n'oblige a
la prediquer d'une designation. Un proces-verbal qui ecrirait le titre du point
puis, dessous, `Resultat du vote : adoptee` est donc PARFAITEMENT CONFORME - et
il n'est lu par aucun des deux anneaux, parce qu'aucune deixis n'y accompagne
l'issue. Le residu declare plus bas n'est donc pas un cas exotique: c'est la
forme que le decret decrit. Le chemin qui compte pour ce cas est le TEMOIN et
`issues_muettes`, qui le nomment et font passer le run en `WARN`.

La suite - lire l'issue par sa POSITION sous l'intitule du point d'ordre du
jour, ce qui serait l'invariant fonde en droit plutot qu'en usage - n'est pas
faite ici et demande son propre lot.

**Limite de ce controle.** Aucune recherche de jurisprudence n'a ete menee:
seuls les textes reglementaires ont ete lus. Ceci restitue ce que disent les
textes et n'est pas un conseil juridique.
"""

from __future__ import annotations

import re

from ._resolutions_motifs import (
    CLOTURE_RE,
    ISSUE_ENONCEE_NON_LUE,
    MINIMUM_SERIE,
    PARTICIPE_ISSUE_RE,
    SEUIL_SERIE_ISSUES,
    TETE_DOCUMENT,
    TITRE_PV_RE,
)

ANNEAU_STRICT = "stricte"
ANNEAU_LARGE = "large"
#: `RM-2026-0129`. Le troisieme anneau ne lit pas une PREDICATION mais une
#: POSITION. Decret 67-223 art. 17: *le proces-verbal comporte, sous l'intitule
#: de chaque question inscrite a l'ordre du jour, le resultat du vote.* Le
#: CONTENU est norme, la REDACTION ne l'est pas - un cabinet qui ecrit
#: l'intitule puis une ligne `Resultat du vote : adoptee` est parfaitement
#: conforme, et aucun des deux premiers anneaux ne le lit.
ANNEAU_POSITION = "position"
ANNEAU_AUCUN = "aucune"

#: Ce qui pointe la resolution courante. Sans deixis, `en cas de decision
#: regulierement adoptee` - lue dans un contrat du second cabinet - deviendrait
#: un vote.
_DESIGNATION = r"(?:cette|ladite|ledit|la\s+pr[ée]sente|le\s+pr[ée]sent|la|le|ce)\s+"

#: Ce sur quoi une assemblee se prononce. Le pluriel est EXCLU a dessein:
#: `l'une des decisions adoptees par cette assemblee` figure dans les deux
#: corpus et n'est pas un constat de vote.
_OBJET_VOTE = r"(?:r[ée]solution|d[ée]cision|question|motion)"

#: Le numero, quand la formule le rappelle: `la resolution n°3 est rejetee`.
_NUMERO = r"(?:\s*n\s*[°o]\s*\d{1,3}(?:\s*[.,]\s*\d{1,3})?)?"

#: Le degre de liberte reel de l'axe. `sera` vient du proces-verbal du second
#: cabinet, `a ete` et `fut` sont les formes composees de la meme predication.
_LIAISON = r"\s*(?:est|sera|fut|a\s+[ée]t[ée]|demeure|reste)\s+"

#: La fenetre d'issue, identique a celle de l'anneau strict: trois mots, parce
#: que le mot qui porte l'issue n'est pas toujours le premier - `est devenue
#: sans objet` le porte sur le troisieme.
_FENETRE = r"(?P<issue>[a-zéèêA-ZÉÈÊ]+(?:\s+[a-zéèêA-ZÉÈÊ]+){0,2})"

CLOTURE_LARGE_RE = re.compile(
    _DESIGNATION + _OBJET_VOTE + _NUMERO + _LIAISON + _FENETRE,
    re.IGNORECASE,
)


#: L'issue au SINGULIER. Le pluriel est exclu pour la meme raison que dans
#: l'anneau large: `resolutions adoptees` est un titre de section, pas un
#: constat de vote. Mesure du 2026-09-12 sur les deux cabinets: **zero ligne
#: au pluriel**, donc l'exclusion ne coute rien et protege d'un faux positif
#: connu.
_ISSUE_SINGULIERE = re.compile(
    r"(?i)\b(?:adopt|approuv|rejet|refus|repouss|report|ajourn)[e\u00e9\u00e8\u00ea]{1,2}(?!s)\b")

#: Une LIGNE qui n'enonce QUE le resultat. On borne la ligne, jamais le
#: vocabulaire: l'article norme ce qui doit figurer, pas les mots employes. Le
#: lead-in optionnel fait trois mots au plus - `Resultat du vote :`, `Vote :`,
#: `Decision -` - et il n'est pas une liste fermee, seulement une borne de
#: longueur.
CLOTURE_POSITION_RE = re.compile(
    r"^[ \t\-*\u2022]*"
    r"(?:[A-Za-z\u00c0-\u00ff']+(?:[ \t]+[A-Za-z\u00c0-\u00ff']+){0,2}[ \t]*[:\-\u2013][ \t]*)?"
    r"(?P<issue>[A-Za-z\u00c0-\u00ff]+(?:[ \t]+[A-Za-z\u00c0-\u00ff]+){0,2})"
    r"[ \t]*[.;]?[ \t]*$",
    re.MULTILINE)


def positions(text: str) -> list[re.Match[str]]:
    """Les lignes qui n'enoncent qu'un resultat de vote, au singulier.

    Le motif de ligne est large a dessein - il accepte toute ligne courte - et
    c'est le filtre d'issue qui tranche. Les separer rend la regle lisible:
    **la POSITION dit ou regarder, l'ISSUE dit si c'est un vote.**
    """
    return [m for m in CLOTURE_POSITION_RE.finditer(text)
            if _ISSUE_SINGULIERE.search(m.group("issue"))]


def ancres(text: str) -> tuple[list[re.Match[str]], str]:
    """Les formules de cloture du document, et l'anneau qui les a rendues.

    L'anneau strict a la priorite des qu'il rend une SERIE. Le motif est
    mesure et non theorique: sur les deux cabinets, l'anneau large ajoute six
    correspondances qui ne sont pas des votes, et une ancre fausse ne nomme pas
    mal une issue - elle deplace la frontiere de deux resolutions.

    Quand l'anneau strict ne rend rien en serie, l'anneau large prend la main:
    c'est le seul chemin par lequel un troisieme cabinet, qui ecrirait
    `la resolution n°3 est rejetee` sans jamais ecrire `cette resolution est`,
    peut etre lu du tout.
    """
    strictes = list(CLOTURE_RE.finditer(text))
    if len(strictes) >= MINIMUM_SERIE:
        return strictes, ANNEAU_STRICT
    larges = list(CLOTURE_LARGE_RE.finditer(text))
    if len(larges) >= MINIMUM_SERIE:
        return larges, ANNEAU_LARGE
    # `RM-2026-0129`: l'anneau de POSITION passe en dernier des trois, et
    # seulement en SERIE. Il est le moins specifique - il ne demande aucune
    # designation - donc une ancre fausse y coute le plus cher: elle deplace la
    # frontiere de deux resolutions. La serie est ce qui le protege: un
    # document qui cite une issue en passant n'en aligne pas trois seules sur
    # leur ligne.
    posees = positions(text)
    if len(posees) >= MINIMUM_SERIE:
        return posees, ANNEAU_POSITION
    if strictes:
        return strictes, ANNEAU_STRICT
    if larges:
        return larges, ANNEAU_LARGE
    return [], ANNEAU_AUCUN


def hors_des_clotures(
    marques: list[tuple[int, int]], text: str
) -> list[tuple[int, int]]:
    """Retire les marqueurs de numerotation qui tombent DANS une cloture.

    **Un numero cite par la formule de vote n'ouvre pas une resolution: il
    ferme celle qu'on lit.** Le cas apparait des qu'un cabinet rappelle le
    numero en concluant - `la resolution n°1 a ete adoptee` - et il DOUBLE
    alors le compte: le titre `Resolution n°1` ouvre le segment, la conclusion
    en ouvre un second qui ne contient que la fin du premier. Trois resolutions
    en rendaient six, une sur deux vide.

    Le defaut ne se voyait pas sur les deux cabinets connus, dont la formule ne
    cite aucun numero. Il apparait des que la liaison devient libre, c'est-a-dire
    des le premier cabinet qui ecrit autrement - ce que ce lot existe pour
    permettre. La regle est structurelle et ne nomme aucune redaction: ce qui
    est a l'interieur d'une formule d'issue appartient a cette formule.
    """
    spans = [(m.start(), m.end()) for m in ancres(text)[0]]
    if not spans:
        return marques
    return [
        (numero, position)
        for numero, position in marques
        if not any(debut <= position < fin for debut, fin in spans)
    ]


def locution_de_cloture(segment: str) -> tuple[str, str]:
    """La locution d'issue enoncee dans CE segment, et son anneau.

    Le segment est deja delimite quand cette fonction est appelee: un faux
    positif y nomme mal une issue, il ne casse rien. L'anneau large est donc
    toujours essaye ici, apres l'anneau strict - et jamais avant, pour que la
    formule mesuree du cabinet garde la main quand elle est presente.
    """
    stricte = CLOTURE_RE.search(segment)
    if stricte:
        return stricte.group("issue"), ANNEAU_STRICT
    large = CLOTURE_LARGE_RE.search(segment)
    if large:
        return large.group("issue"), ANNEAU_LARGE
    # Le segment est deja delimite: l'anneau de position s'y essaie en dernier,
    # apres les deux formules predicatives, pour que la redaction mesuree d'un
    # cabinet garde la main quand elle est presente.
    posees = positions(segment)
    if posees:
        return posees[0].group("issue"), ANNEAU_POSITION
    return "", ANNEAU_AUCUN


def porte_un_temoin(segment: str) -> bool:
    """Le segment enonce-t-il quelque chose qui RESSEMBLE a une issue ?

    Detecteur volontairement large, et volontairement impuissant: il ne cree ni
    ancre ni resolution, et il ne nomme aucune issue. Il repond a une seule
    question - `le document dit-il quelque chose ici que je ne sais pas lire ?`
    - dont la reponse separe deux etats que le registre confondait:
    `SANS_ISSUE_TRACEE`, ou le document ne dit rien, et
    `ISSUE_ENONCEE_NON_LUE`, ou il dit quelque chose.
    """
    return bool(PARTICIPE_ISSUE_RE.search(segment))


def issues_muettes(
    text: str,
    marqueurs: list[tuple[int, int]],
    resultats: list[str],
) -> dict[str, object]:
    """Le document enonce-t-il des issues que la chaine ne sait pas lire ?

    **C'est la fonction qui supprime le silence.** Rendre `0 resolution` sur un
    proces-verbal qui en porte douze et afficher `0` sur un document qui n'en
    porte aucune sont, pour le lecteur, le meme ecran. Ce qui les separe n'est
    pas une issue de plus dans le vocabulaire: c'est le fait que le document
    ENONCE des issues en serie sans qu'on sache les lire.

    Le critere est STRUCTUREL, pas lexical, et c'est ce qui le rend
    generalisable: un proces-verbal enonce une issue par resolution, en serie.
    On compare donc le nombre de segments dont l'issue n'est pas lue au nombre
    de segments tout court. Une convocation echoue a ce test par construction -
    mesure sur le second cabinet: 77 resolutions projetees, 3 participes
    d'issue, soit 4 % des segments - et un proces-verbal illisible le passe.

    Rend un constat nomme, jamais une correction. `mutisme` vaut `partiel`,
    `total` ou la chaine vide, et `verdict` porte la phrase a publier.
    """
    ancrages, anneau = ancres(text)
    temoins = len(PARTICIPE_ISSUE_RE.findall(text))
    non_lus = sum(1 for r in resultats if r == ISSUE_ENONCEE_NON_LUE)
    segments = len(marqueurs)
    taux = non_lus / segments if segments else 0.0

    # **Deux formes de mutisme, mesurees le 2026-09-08 sur de la vraie matiere.**
    # Les deux proces-verbaux reels des deux cabinets ont ete reabsorbes apres
    # qu'on eut reecrit LEUR SEULE formule de cloture en une redaction que ni
    # l'un ni l'autre anneau ne lit. Ils ne se sont pas casses de la meme facon,
    # et une seule regle les aurait manques tous les deux.
    #
    # 1. PARTIEL - le document se segmente encore, et la plupart de ses issues
    #    ne sont plus lues. 55 resolutions, 46 non lues, quatre formules
    #    survivantes. Une condition `aucune ancre` aurait rendu `False` sur ce
    #    document a cause de ces quatre-la, et 46 votes seraient repartis en
    #    silence. C'est le TAUX qui tranche, jamais la presence d'une ancre.
    partiel = (
        segments >= MINIMUM_SERIE
        and non_lus >= MINIMUM_SERIE
        and taux >= SEUIL_SERIE_ISSUES
    )
    # 2. TOTAL - le document ne se segmente plus du tout. Le second cabinet
    #    numerotait ses resolutions PAR sa formule de cloture: en la reecrivant,
    #    54 resolutions sont devenues zero segment, zero ligne, nature `AUTRE`,
    #    et le document a disparu du registre sans un compteur. C'est le defaut
    #    dans sa forme pure.
    #    Ce qui le separe d'un contrat qui cite onze fois `approuve`: le
    #    document SE DECLARE proces-verbal en tete. C'est l'invariant deja
    #    etabli dans ce depot - fonde sur le titre et non sur l'habitude d'un
    #    cabinet, zero faux positif sur 37 documents et deux cabinets - et on le
    #    reemploie ici plutot que d'inventer un seuil de plus.
    total = (
        not segments
        and temoins >= MINIMUM_SERIE
        and bool(TITRE_PV_RE.search(text[:TETE_DOCUMENT]))
    )
    muet = partiel or total
    return {
        "mutisme": "total" if total else ("partiel" if partiel else ""),
        "anneau_cloture": anneau,
        "clotures_reconnues": len(ancrages),
        "temoins_d_issue": temoins,
        "segments": segments,
        "segments_issue_non_lue": non_lus,
        "taux_issue_non_lue": round(taux, 3),
        "muet": muet,
        "verdict": _verdict(total, partiel, anneau, segments, non_lus, temoins),
    }


def _verdict(
    total: bool,
    partiel: bool,
    anneau: str,
    segments: int,
    non_lus: int,
    temoins: int,
) -> str:
    """Une phrase qui dit ce qui s'est passe, lisible sans lire le code."""
    if total:
        return (
            f"ce document se declare proces-verbal et enonce {temoins} issues, "
            "et aucune de ses resolutions n'a pu etre delimitee: ni sa "
            "numerotation ni sa formule de cloture ne sont lues. Le registre "
            "n'en portera aucune ligne, et ce zero n'est pas un constat sur "
            "l'assemblee"
        )
    if partiel:
        return (
            f"le document enonce une issue dans {non_lus} de ses {segments} "
            "resolutions sans qu'elle y soit lue: la redaction de ce cabinet "
            "n'est comprise qu'en partie, et les comptages d'adoptees et de "
            "rejetees sont incomplets d'autant"
        )
    if non_lus:
        return (
            f"{non_lus} resolutions sur {segments} enoncent quelque chose qui "
            "n'est pas lu comme une issue: a relire sur la piece"
        )
    if anneau == ANNEAU_LARGE:
        return (
            "les issues ont ete lues par la forme large de la formule de "
            "cloture, pas par celle mesuree sur les cabinets connus: le "
            "resultat tient, la lecture demande un controle"
        )
    return ""
