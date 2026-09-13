"""Lecture des champs d'une resolution, une fois le gabarit connu."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ._resolutions_calibrage import _marqueurs, _marqueurs_par_cloture
from ._resolutions_cloture import ANNEAU_LARGE, locution_de_cloture, porte_un_temoin
from ._resolutions_qualification import decision_actee, qualifications, valeurs_seuil
from ._resolutions_motifs import (
    ABSTENTION_RE,
    CLOTURE_RE,
    CONTRE_RE,
    ISSUE_ENONCEE_NON_LUE,
    ISSUE_NON_RECONNUE,
    ISSUE_LOCUTIONS,
    ISSUE_PREFIXES,
    MAJORITE_RE,
    article_lu,
    NUMERO_RE,
    PASSERELLE_CITEE_RE,
    PASSERELLE_UTILISEE_RE,
    PAS_DE_VOTE,
    PAS_DE_VOTE_RE,
    POUR_RE,
    REPORTEE,
    SANS_ISSUE,
    SANS_OBJET,
    SOUS_NUMERO_RE,
    VOIX_RE,
    VOTE_SANS_FORMULE,
)

@dataclass
class Resolution:
    numero: int
    objet: str
    #: Le degre de la numerotation hierarchique, chaine vide quand il n'y en a
    #: pas. Chez le second cabinet, 11.1 a 11.8 sont huit resolutions distinctes
    #: portant chacune son devis: les confondre sur `numero` en perdait six.
    sous_numero: str = ""
    majorite_annoncee: str = ""
    passerelle_citee: bool = False
    passerelle_utilisee: bool = False
    majorite_appliquee: str = ""
    resultat: str = SANS_ISSUE
    voix_relevees: list[str] = field(default_factory=list)
    voix_pour: str = ""
    voix_contre: str = ""
    voix_abstention: str = ""
    base_voix: str = ""
    position: int = 0
    numerotation: str = "lue"
    decision_actee: str = ""
    qualifications: list[str] = field(default_factory=list)
    duree_mois: int | None = None
    montant_seuil: str = ""
    montant_intitule: str = ""
    duree_intitule: int | None = None
    divergences: list[str] = field(default_factory=list)
    valide_du: str = ""
    valide_au: str = ""
    confiance: str = "moyenne"


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


#: Fenetre de tete dans laquelle un degre de numerotation est encore celui du
#: point courant. Le marqueur de segmentation est a l'offset 0 du segment; le
#: degre, s'il existe, le suit immediatement.
_TETE_SEGMENT = 120


def _sous_numero(segment: str) -> str:
    """Le degre de la numerotation, ou chaine vide quand il n'y en a pas.

    Cherche dans la seule tete du segment. Un `Resolution n°11.2` cite plus loin
    dans le corps parle d'une AUTRE resolution: le lire ici renumeroterait le
    point courant d'apres ce qu'il mentionne.

    **Ce que cette lecture ne couvre pas, et ce qui arrive alors.** L'axe est la
    maniere dont un cabinet ecrit le degre; l'invariant est qu'il suit
    immediatement le numero. `SOUS_NUMERO_RE` ne lit aujourd'hui que la forme
    « Resolution n°X.Y », qui est celle mesuree sur le second corpus. Un cabinet
    qui numeroterait « 11.1 - » en tete de ligne, sans le mot `Resolution`,
    rendrait ici une chaine vide: ses sous-resolutions partageraient alors le
    meme `resolution_id` et `INSERT OR REPLACE` n'en garderait qu'une - la
    collision de C055, a l'identique. La degradation est donc SILENCIEUSE, et
    c'est la seule raison d'ecrire cette limite ici plutot que de la laisser se
    decouvrir sur un troisieme corpus. La lever demande d'elargir
    `SOUS_NUMERO_RE`, qui appartient a `_resolutions_motifs`.
    """
    trouve = SOUS_NUMERO_RE.search(segment[:_TETE_SEGMENT])
    return trouve.group(1) if trouve else ""


def _objet(segment: str) -> str:
    """Premiere phrase du segment, apres le marqueur de numero.

    L'objet d'une resolution tient dans sa premiere phrase. On ne cherche pas
    plus loin: au dela, le PV enchaine sur l'expose et les votes.
    """
    body = NUMERO_RE.sub("", segment, count=1)
    sentence = re.split(r"(?<=[.;])\s", _normalise(body), maxsplit=1)[0]
    return sentence[:300]


def _locution_reconnue(mots: list[str], rang: int, prefixes: tuple[str, ...]) -> bool:
    """La suite de mots a partir de `rang` porte-t-elle cette locution ?

    Chaque prefixe doit etre reconnu sur un mot consecutif. Une locution
    tronquee par la fenetre de capture n'est pas reconnue: elle ressort
    `ISSUE_NON_RECONNUE`, c'est-a-dire appelee a relecture, et non rattachee
    par defaut a son premier mot.
    """
    if rang + len(prefixes) > len(mots):
        return False
    return all(
        mots[rang + ecart].startswith(prefixe)
        for ecart, prefixe in enumerate(prefixes)
    )


#: Une formule qui NIE la tenue d'un vote. Elle n'est pas l'issue: elle dit
#: qu'il n'y en a pas eu, et ce qui la suit en est la CAUSE.
_NEGATION_DE_VOTE = re.compile(r"pas\s+de\s+vote", re.IGNORECASE)

#: Le determinant qui precede la resolution nommee dans la formule de cloture.
#: `cette` la designe elle-meme; `la` sans demonstratif en designe une autre.
_DEMONSTRATIF = re.compile(r"\b(?:cette|ladite|la\s+pr[ée]sente)\s+r[ée]solution", re.I)


def issue_designe_une_autre_resolution(segment: str, brute: str) -> bool:
    """L'issue enoncee porte-t-elle sur une AUTRE resolution que celle-ci ?

    **Deux lectures s'opposaient sur la meme phrase, et la mesure les
    departage.** Le corpus reel ecrit, pour la resolution 37:

        37 - Vote des modalites des Appels de Fonds exceptionnels [...]
        Pas de vote car la resolution est rejetee.

    Un lot de septembre avait decide que cette phrase rend `REJETEE` - *la
    phrase entiere dit qu'elles sont rejetees* - et revendiquait sept
    resolutions gagnees. **Ce test, `test_pas_de_vote_car_la_resolution_est_
    rejetee_rend_rejetee`, est contredit ici, et c'est dit.** La confrontation
    du 2026-09-09 au corpus dont l'etalon est etabli **a la main avant tout
    traitement** montre l'inverse: quatre resolutions sur cinquante-cinq
    etaient rendues `REJETEE` la ou un humain avait lu `PAS_DE_VOTE`, et elles
    portaient **zero voix** - ni pour, ni contre, ni abstention. Dire *rejetee*
    y attribue a l'assemblee un acte qu'elle n'a pas pose.

    **L'axe n'est ni la position ni la presence de `pas de vote`: c'est le
    DETERMINANT.** Mesure sur le corpus etalon, 30 pieces:

        `cette resolution est <issue>` : 92 occurrences
        `la resolution est <issue>`    :  8 occurrences
           dont precedees de `pas de vote`: 8 sur 8
           hors de ce contexte           : 0

    Le redacteur distingue donc sans exception: le demonstratif annonce l'issue
    de la resolution COURANTE, l'article defini apres une negation de vote en
    designe une AUTRE - celle dont le rejet explique l'absence de vote.

    **Ce que cette regle laisse expose, et il faut le dire.** La mesure porte
    sur **un cabinet**. Un redacteur qui ecrirait `la resolution est rejetee`
    pour annoncer sa propre issue serait lu comme un `PAS_DE_VOTE` - mais
    seulement s'il ecrit AUSSI `pas de vote` juste avant, ce qui serait
    contradictoire. La degradation exige donc les deux conditions ensemble, et
    hors d'elles le comportement d'avant est inchange.
    """
    negation = _NEGATION_DE_VOTE.search(segment)
    if negation is None:
        return False
    debut = segment.find(brute)
    if debut < 0 or negation.start() > debut:
        return False
    # **Le determinant precede la locution capturee, il n'est pas dedans.**
    # `locution_de_cloture` rend la formule a partir du verbe ou du participe;
    # `cette` reste en amont. On regarde donc la fenetre qui va de la negation
    # de vote jusqu'a la fin de la formule - c'est la phrase entiere, et c'est
    # elle qui porte le determinant.
    phrase = segment[negation.start():debut + len(brute)]
    return _DEMONSTRATIF.search(phrase) is None


def _issue(segment: str, a_des_voix: bool) -> str:
    """Issue du vote, en distinguant CINQ absences differentes.

    Une resolution explicitement non soumise au vote, une resolution votee dont
    l'adoption n'est pas enoncee, une resolution dont on ne sait rien, une
    formule de cloture dont le vocabulaire n'est pas reconnu et un segment qui
    ENONCE une issue sans qu'aucune formule n'y soit lue ne posent pas le meme
    probleme. Les confondre efface le constat.

    **Le cinquieme etat est celui qui supprime le silence.** Avant lui, un
    proces-verbal redige autrement rendait `SANS_ISSUE_TRACEE` - la meme valeur
    qu'un document qui ne dit rien. La formule de cloture est desormais cherchee
    par deux anneaux (voir `_resolutions_cloture`), et quand aucun des deux ne
    rend rien alors qu'un temoin d'issue est present dans le segment, la valeur
    rendue est `ISSUE_ENONCEE_NON_LUE`: le document a parle, on ne l'a pas lu,
    et c'est dit.

    La locution de cloture est lue en entier, pas seulement son premier mot:
    "cette resolution est devenue sans objet" porte son issue sur le troisieme.
    Quand aucun mot n'est reconnu, la valeur rendue est `ISSUE_NON_RECONNUE` -
    un etat du vocabulaire, appele a relecture - et jamais le mot brut promu au
    rang d'issue.

    Un mot ne suffit pas toujours a faire une issue. "sans" en est le cas
    mesure: il tranchait "votee sans opposition", "acceptee sans reserve" et
    "prise sans debat" en `SANS_OBJET`, c'est-a-dire qu'il comptait des
    resolutions votees comme non votees. Les locutions sont donc essayees
    d'abord, sur des mots consecutifs, et le prefixe seul ensuite.
    """
    brute, anneau = locution_de_cloture(segment)

    if brute and issue_designe_une_autre_resolution(segment, brute):
        return PAS_DE_VOTE

    if brute:
        locution = (
            brute.lower().replace("é", "e").replace("è", "e").replace("ê", "e")
        )
        mots = locution.split()
        for rang, mot in enumerate(mots):
            for prefixes, issue in ISSUE_LOCUTIONS:
                if _locution_reconnue(mots, rang, prefixes):
                    return issue
            for prefixe, issue in ISSUE_PREFIXES:
                if mot.startswith(prefixe):
                    return issue
        # Vocabulaire inconnu. L'anneau strict est la formule mesuree du
        # cabinet: s'il a matche, une issue a bien ete enoncee et c'est son mot
        # qu'on ne connait pas - `ISSUE_NON_RECONNUE`. L'anneau large, lui,
        # attrape aussi des phrases qui ne parlent pas du vote: mesure du
        # 2026-09-08, `La decision est favorable au SDC` et `Cette decision a
        # ete confirme par jugement`. On ne les promeut donc pas au rang de
        # formule de cloture: elles restent un enonce non lu, a relire.
        return ISSUE_NON_RECONNUE if anneau != ANNEAU_LARGE else ISSUE_ENONCEE_NON_LUE
    if PAS_DE_VOTE_RE.search(segment):
        return PAS_DE_VOTE
    if porte_un_temoin(segment):
        # Le segment porte un participe d'issue et aucune formule ne l'encadre.
        # C'est le cas du troisieme cabinet: il enonce, on ne lit pas.
        #
        # **Ce test passe AVANT `a_des_voix`, et l'ordre est le defaut ferme.**
        # `VOTE_SANS_FORMULE` veut dire `des voix sont comptees et aucune
        # adoption n'est enoncee`. Un proces-verbal reel compte ses voix: place
        # apres, le temoin n'aurait jamais ete atteint sur la matiere qui compte,
        # et le cas le plus probable d'un troisieme cabinet - des voix, une
        # issue redigee autrement - serait retombe dans un etat qui affirme
        # qu'aucune adoption n'est enoncee. C'est faux: elle est enoncee, elle
        # n'est pas lue, et les deux phrases ne demandent pas le meme geste.
        return ISSUE_ENONCEE_NON_LUE
    if a_des_voix:
        return VOTE_SANS_FORMULE
    return SANS_ISSUE


def _majorites(segment: str) -> list[str]:
    seen: list[str] = []
    for match in MAJORITE_RE.finditer(segment):
        article = article_lu(match.group(1))
        if article not in seen:
            seen.append(article)
    return seen


def _majorite_appliquee(segment: str, annoncee: str, passerelle: bool) -> str:
    """Majorite reellement appliquee au vote qui a tranche.

    Quand la passerelle de l'article 25-1 a ete utilisee, l'assemblee s'est
    prononcee une seconde fois a la majorite de l'article 24: c'est celle-la qui
    a tranche. Sinon, la majorite appliquee est celle annoncee.

    **Une regex ne tranche plus seule.** La passerelle de l'article 25-1 ne
    s'ouvre que sur une resolution annoncee sous l'article 25: c'est le texte
    meme de l'article. Quand la formule de passage est lue sous une autre
    majorite annoncee - ou sous aucune - la valeur rendue reste la majorite
    annoncee, et l'ecart est signale par `divergence_passerelle`. Le defaut
    ferme: `il est passe au vote suivant l'article 25-1` faisait ecrire `24`
    quelle que soit la majorite annoncee, et deux verdicts opposes pouvaient
    sortir des memes chiffres selon qu'un `re.search` avait matche ou non, sans
    que personne ne le voie.

    **Amplitude exacte du changement**, mesuree le 2026-09-05 sur les dix
    combinaisons possibles de (majorite annoncee, passerelle lue). Trois
    changent, et toutes trois exigent la passerelle:

        annoncee '25-1' + passerelle : '24' -> '25-1'
        annoncee '26'   + passerelle : '24' -> '26'
        annoncee ''     + passerelle : '24' -> ''

    Les sept autres sont inchangees, dont le cas courant du corpus
    (annoncee '25' + passerelle, qui rend '24' avant comme apres).

    **Ce qui n'a pas ete mesure, et doit l'etre avant de conclure.** Le nombre
    de lignes reellement concernees dans un corpus n'a pas ete compte ici: la
    matiere n'est pas dans le depot. Ce qui est verifie, c'est que la formule
    d'annonce du proces-verbal etalon - "articles 25 et 25-1" - est lue `'25'`
    par `_majorites`, donc dans la combinaison inchangee; une resolution
    annoncee `Article 25-1` seul serait, elle, dans la combinaison changee.
    """
    if passerelle and annoncee == "25":
        return "24"
    return annoncee


def divergence_passerelle(annoncee: str, passerelle: bool) -> str:
    """La formule de passage a-t-elle ete lue hors de son cas d'ouverture ?

    Rend une phrase de divergence, ou la chaine vide. La passerelle ne se lit
    que sous l'article 25; toute autre lecture est un fait a verifier sur le
    document, pas une bascule silencieuse de la majorite appliquee.
    """
    if not passerelle or annoncee == "25":
        return ""
    if not annoncee:
        return (
            "la formule de passage a l'article 25-1 est lue alors qu'aucune "
            "majorite n'est annoncee: la majorite appliquee reste non enoncee"
        )
    return (
        f"la formule de passage a l'article 25-1 est lue sous une majorite "
        f"annoncee a l'article {annoncee}: la passerelle ne s'ouvre que sur "
        "l'article 25, la majorite appliquee reste celle qui est annoncee"
    )


def _nombre(match: re.Match[str] | None) -> str:
    return re.sub(r"[\s.]", "", match.group(1)) if match else ""


def _voix(segment: str) -> tuple[list[str], str, str, str, str]:
    """Decomptes bruts, plus les trois decomptes nommes quand le PV les donne."""
    releves: list[str] = []
    base = ""
    for match in VOIX_RE.finditer(segment):
        valeur = re.sub(r"[\s.]", "", match.group(1))
        if valeur:
            releves.append(valeur)
        if not base:
            base = re.sub(r"[\s.]", "", match.group(2))
    pour_match = POUR_RE.search(segment)
    if pour_match and pour_match.group(2):
        # La base lue dans la ligne de vote elle-meme prime sur celle glanee
        # ailleurs dans le segment. Le PV du 03/07/2024 ecrit "4119/4899" pour
        # les presents et representes, et porte par ailleurs des "/10.000":
        # prendre le premier venu affichait deux denominateurs melanges.
        base = re.sub(r"[\s.]", "", pour_match.group(2))
    return (
        releves,
        _nombre(pour_match),
        _nombre(CONTRE_RE.search(segment)),
        _nombre(ABSTENTION_RE.search(segment)),
        base,
    )


def _confiance(res: Resolution) -> str:
    """Confiance dans la ligne extraite, fondee sur des faits verifiables."""
    if res.resultat == SANS_ISSUE:
        return "faible"
    if res.resultat in (ISSUE_NON_RECONNUE, ISSUE_ENONCEE_NON_LUE):
        # Une issue est enoncee et n'est pas lue - soit son vocabulaire est
        # inconnu, soit sa redaction l'est. La ligne demande une relecture
        # humaine, pas une confiance moyenne qui la laisserait passer.
        return "faible"
    if not res.majorite_appliquee:
        return "faible"
    if res.resultat in (PAS_DE_VOTE, VOTE_SANS_FORMULE):
        return "moyenne"
    if res.passerelle_utilisee and len(res.voix_relevees) < 2:
        return "faible"
    if not res.voix_pour:
        return "moyenne"
    return "forte"




def parse_resolutions(text: str) -> list[Resolution]:
    """Segmente un PV et rend une ligne par resolution numerotee."""
    marks = _marqueurs(text)
    deduite = marks == _marqueurs_par_cloture(text) and bool(marks)
    resolutions: list[Resolution] = []
    for index, (numero, start) in enumerate(marks):
        end = marks[index + 1][1] if index + 1 < len(marks) else len(text)
        segment = text[start:end]
        majorites = _majorites(segment)
        annoncee = next((m for m in majorites if m != "25-1"), "")
        utilisee = bool(PASSERELLE_UTILISEE_RE.search(segment))
        voix, pour, contre, abstention, base = _voix(segment)
        res = Resolution(
            numero=numero,
            # Le degre se relit en TETE de segment, la ou le marqueur a coupe:
            # au-dela, le corps cite d'autres resolutions et le premier `n°X.Y`
            # rencontre ne serait plus celui du point courant.
            sous_numero=_sous_numero(segment),
            objet=_objet(segment),
            majorite_annoncee=annoncee,
            passerelle_citee=bool(PASSERELLE_CITEE_RE.search(segment)),
            passerelle_utilisee=utilisee,
            majorite_appliquee=_majorite_appliquee(segment, annoncee, utilisee),
            resultat=_issue(segment, bool(voix)),
            voix_relevees=voix,
            voix_pour=pour,
            voix_contre=contre,
            voix_abstention=abstention,
            base_voix=base,
            position=index + 1,
        )
        res.decision_actee = decision_actee(segment)
        res.qualifications = qualifications(segment)
        valeurs = valeurs_seuil(segment)
        res.montant_seuil = str(valeurs["montant"] or "")
        res.montant_intitule = str(valeurs["montant_intitule"] or "")
        res.duree_mois = valeurs["duree_mois"]
        res.duree_intitule = valeurs["duree_intitule"]
        res.divergences = list(valeurs["divergences"])
        ecart_passerelle = divergence_passerelle(annoncee, utilisee)
        if ecart_passerelle:
            res.divergences.append(ecart_passerelle)
        res.numerotation = "deduite" if deduite else "lue"
        res.confiance = "moyenne" if deduite else _confiance(res)
        resolutions.append(res)
    return resolutions


def sequence_gaps(resolutions: list[Resolution]) -> list[int]:
    """Numeros manquants dans la sequence, signe d'une segmentation incomplete."""
    if not resolutions:
        return []
    numeros = sorted({r.numero for r in resolutions})
    return [n for n in range(numeros[0], numeros[-1] + 1) if n not in numeros]


