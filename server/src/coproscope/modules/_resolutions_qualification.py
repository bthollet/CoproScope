"""Ce qu'une resolution decide vraiment, et ce qu'elle engage dans le temps.

Trois choses que la seule lecture de l'intitule manque:

1. **La decision actee.** L'intitule est souvent une enveloppe procedurale.
   Releve sur l'AG du 17/06/2026: `Vote de la Resolution n°13 conformement a la
   demande de M. X, et telle qu'elle est ecrite` - l'objet reel est cite apres.
   Prendre l'intitule pour la decision donne alors un contresens.

2. **La duree.** Un seuil de l'article 21 est vote pour une periode; une
   delegation de l'article 21-1 pour deux ans au maximum. Savoir quel seuil
   etait en vigueur A LA DATE d'une decision est le coeur du controle, et ce
   n'est pas calculable sans la fenetre de validite. Releve: seuil de mise en
   concurrence a 1.000 EUR vote le 28/06/2023 pour 14 mois, donc en vigueur
   lors de l'AG du 03/07/2024 - et non les 2.000 EUR votes ce jour-la.

3. **Le mandat d'execution au syndic.** `L'assemblee generale confere au syndic
   tout pouvoir a l'effet de...` n'est pas la delegation au conseil syndical de
   l'article 21-1. C'est une autorite d'execution attachee a une resolution.
   Les confondre melange deux objets juridiques distincts.
"""

from __future__ import annotations

import datetime as dt
import re

from ._resolutions_periode import EXERCICE_RE, PERIODE_RE, periode_close
from ._actes_vocabulaire import (
    PORTEE_APPROBATION_COMPTES,
    PORTEE_AUTORISATION_COPROPRIETAIRE,
    PORTEE_BUDGET,
    PORTEE_DELEGATION_CS,
    PORTEE_DESIGNATION_ORGANE,
    PORTEE_DESIGNATION_SYNDIC,
    PORTEE_ENGAGEMENT_DEPENSE,
    PORTEE_FONDS_TRAVAUX,
    PORTEE_MODALITES,
    PORTEE_ORDINAIRE,
    PORTEE_SEUIL,
)

# L'assemblee "decide", "autorise", "confere", "fixe": la clause operatoire
# commence par le sujet et son verbe.
DEBUT_CLAUSE_RE = re.compile(
    # "L'AG" abrege est employe aussi bien que la forme longue: la resolution
    # 27 du 03/07/2024 ecrit "L'AG annuelle pour satisfaire aux dispositions".
    r"l[’']?\s*(?:assembl[ée]e\s+g[ée]n[ée]rale|AG)\b.{0,600}?"
    r"\b(?:d[ée]cide|autorise|conf[èe]re|fixe|arr[êe]te|approuve|mandate|donne pouvoir)\b",
    re.IGNORECASE | re.DOTALL,
)

# La borne de fin n'est PAS la ponctuation. Le texte juridique est plein de
# points - "2.000,00 EUR", "n°65/557", "10/07/1965" - et couper au premier point
# tronquait la clause avant le montant qu'elle fixe: la resolution 26 du
# 03/07/2024 fixe 1.000 EUR dans son corps, la ou son intitule annonce 2.000.
# La borne est structurelle: le debut du bloc de vote.
FIN_CLAUSE_RE = re.compile(
    r"(?i)ont\s+vot[ée]s?\s+(?:pour|contre)|se sont abstenus|vote aux tanti[èe]mes"
    r"|en vertu de quoi|en cons[ée]quence, cette r[ée]solution|pas de vote"
)

# Objet cite entre guillemets, forme rencontree quand l'intitule renvoie a une
# demande exterieure: `... telle qu'elle est ecrite. "delegation limitee..."`.
OBJET_CITE_RE = re.compile(r"[«\"“]([^»\"”]{15,300})[»\"”]")

# Qualifications: racine puis confirmation.
#
# Ni la racine seule ni la phrase entiere ne suffisent, et les deux echecs sont
# mesures sur le corpus:
#
# - la racine seule est trop large. Sur neuf PV, "deleg" apparait huit fois:
#   six fois pour deleguer a une banque le benefice d'une assurance ou d'une
#   subvention, une fois pour le vote par pouvoir, et UNE SEULE fois pour la
#   delegation de l'article 21-1;
# - la phrase entiere est trop etroite. "mise en concurrence est obligatoire" et
#   "est rendue obligatoire" disent la meme chose, et il a fallu elargir deux
#   fois avant de le comprendre.
#
# D'ou deux temps: une racine bon marche qui propose, un contexte qui confirme.
QUALIFICATIONS: tuple[tuple[str, re.Pattern[str], re.Pattern[str], re.Pattern[str] | None], ...] = (
    (
        "SEUIL_CONSULTATION_CS",
        re.compile(r"(?i)consult\w*"),
        re.compile(r"(?i)conseil syndical[^.]{0,120}?obligatoire|obligatoire[^.]{0,120}?conseil syndical"),
        None,
    ),
    (
        "SEUIL_MISE_EN_CONCURRENCE",
        # "jusqu'a concurrence de" veut dire "a hauteur de" et n'a rien a voir
        # avec la mise en concurrence: quatre faux positifs sur le corpus.
        re.compile(r"(?i)concurrenc\w*"),
        re.compile(r"(?i)obligatoire|a partir (?:duquel|de laquelle)|montant|march[ée]s?\b"),
        # "jusqu'a concurrence de" veut dire "a hauteur de": homographe, sans
        # rapport avec la mise en concurrence. Quatre occurrences sur le corpus.
        re.compile(r"(?i)(?:jusqu.\s*[aà]|[aà])\s+concurrence\s+d"),
    ),
    (
        "MISE_EN_CONCURRENCE_PRODUITE",
        # Fait distinct du seuil: la resolution montre que la concurrence a eu
        # lieu, plusieurs devis ayant ete presentes.
        re.compile(r"(?i)(?:plusieurs|deux|trois|quatre|\d)\s+devis"),
        re.compile(r"(?i)devis"),
        None,
    ),
    (
        "DELEGATION_CS",
        re.compile(r"(?i)d[ée]l[ée]g\w*"),
        re.compile(r"(?i)conseil syndical"),
        # "exercent par delegation les votes" est du vote par pouvoir, et
        # "deleguer a la banque le benefice" une cession de creance.
        re.compile(r"(?i)par d[ée]l[ée]gation les votes|d[ée]l[ée]guer\s+[aà]\s+la\s+(?:caisse|banque|soci[ée]t[ée])"),
    ),
    (
        "MANDAT_SYNDIC",
        re.compile(r"(?i)pouvoirs?|mandat\w*"),
        re.compile(r"(?i)(?:conf[èe]re|donne|mandate)[^.]{0,60}?syndic|syndic[^.]{0,60}?tout pouvoir"),
        None,
    ),
    (
        "APPROBATION_COMPTES",
        re.compile(r"(?i)approu\w*|approb\w*"),
        re.compile(r"(?i)comptes|charges|exercice clos"),
        None,
    ),
    (
        "BUDGET_PREVISIONNEL",
        re.compile(r"(?i)budget\w*"),
        re.compile(r"(?i)pr[ée]visionnel|de l.exercice"),
        None,
    ),
    (
        "FONDS_TRAVAUX",
        re.compile(r"(?i)fonds\s+(?:de\s+)?travaux"),
        re.compile(r"(?i)."),
        None,
    ),
)


# "pour une duree de 24 mois", "pour une periode de 14 MOIS", "durant 2 ans".
DUREE_MOIS_RE = re.compile(
    r"(?i)(?:pour|durant|pendant)\s+une?\s+(?:dur[ée]e|p[ée]riode)?\s*(?:de\s+)?(\d{1,3})\s*mois"
)
DUREE_ANS_RE = re.compile(
    r"(?i)(?:pour|durant|pendant)\s+une?\s+(?:dur[ée]e|p[ée]riode)?\s*(?:de\s+)?(\d{1,2})\s*an"
)


def decision_actee(segment: str) -> str:
    """Clause operatoire de la resolution, ou chaine vide si elle n'y est pas.

    On prefere l'objet cite entre guillemets quand il existe: c'est la forme
    employee lorsque l'intitule n'est qu'un renvoi.
    """
    cite = OBJET_CITE_RE.search(segment)
    if cite:
        return re.sub(r"\s+", " ", cite.group(1)).strip()[:400]
    debut = DEBUT_CLAUSE_RE.search(segment)
    if not debut:
        return ""
    reste = segment[debut.start():]
    fin = FIN_CLAUSE_RE.search(reste, debut.end() - debut.start())
    clause = reste[: fin.start()] if fin else reste
    return re.sub(r"\s+", " ", clause).strip()[:600]


FENETRE_CONFIRMATION = 220


def qualifications(segment: str) -> list[str]:
    """Ce que la resolution engage, au-dela de son objet litteral.

    Une racine propose, un contexte confirme. Sans le second temps, "deleguer a
    la banque le benefice de l'assurance" passerait pour une delegation de
    pouvoirs au conseil syndical.
    """
    trouve: list[str] = []
    for nom, racine, contexte, exclusion in QUALIFICATIONS:
        for candidat in racine.finditer(segment):
            # La confirmation doit etre PROCHE de la racine. Cherchee dans tout
            # le bloc, elle rattachait une delegation bancaire au conseil
            # syndical nomme trois cents mots plus loin.
            fenetre = segment[max(0, candidat.start() - FENETRE_CONFIRMATION):
                              candidat.end() + FENETRE_CONFIRMATION]
            if exclusion is not None and exclusion.search(fenetre):
                continue
            if contexte.search(fenetre):
                trouve.append(nom)
                break
    return trouve


def duree_mois(segment: str) -> int | None:
    """Duree de validite en mois, quand la resolution l'enonce.

    Rend None quand aucune duree n'est ecrite. Un seuil sans terme est un fait a
    signaler - le PV du 20/07/2022 en porte un - pas une duree a supposer.
    """
    mois = DUREE_MOIS_RE.search(segment)
    if mois:
        return int(mois.group(1))
    ans = DUREE_ANS_RE.search(segment)
    if ans:
        return int(ans.group(1)) * 12
    return None


def _ajoute_mois(depart: dt.date, mois: int) -> dt.date:
    total = depart.month - 1 + mois
    annee = depart.year + total // 12
    mois_final = total % 12 + 1
    jour = min(depart.day, [31, 29 if annee % 4 == 0 and (annee % 100 != 0 or annee % 400 == 0) else 28,
                            31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mois_final - 1])
    return dt.date(annee, mois_final, jour)


def fenetre_validite(date_ag: str, mois: int | None) -> tuple[str, str]:
    """Fenetre de validite d'une decision a duree limitee.

    Rend (valide_du, valide_au). `valide_au` est vide quand la duree n'est pas
    enoncee: on ne devine pas un terme.
    """
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", date_ag or "")
    if not match:
        return "", ""
    depart = dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    if mois is None:
        return depart.isoformat(), ""
    return depart.isoformat(), _ajoute_mois(depart, mois).isoformat()


def en_vigueur_le(valide_du: str, valide_au: str, date: str) -> bool | None:
    """La decision etait-elle en vigueur a cette date.

    Rend None quand la reponse n'est pas calculable - terme absent, ou dates
    illisibles. Un `None` se remonte a l'utilisateur; il ne se remplace pas par
    un `False` qui aurait l'air d'une conclusion.
    """
    if not valide_du or not date:
        return None
    if not valide_au:
        return None
    return valide_du <= date <= valide_au


# Montant d'un seuil, tel qu'ecrit: "500,00 € T.T.C.", "1.000 € TTC", "2.000 €".
# Formes rencontrees: "Montant propose 2.000,00 EUR T.T.C", "decide de fixer a
# 1.000 EUR TTC", "au-dela d'un seuil de 1000EUR TTC". Le montant suit un verbe
# de fixation ou le mot "seuil", jamais isole - sinon toute somme du corps de la
# resolution serait prise pour le seuil.
MONTANT_SEUIL_RE = re.compile(
    r"(?i)(?:fixer|fixe|montant\s+propos[ée]|seuil|montant)\s*"
    r"(?:[àa]|de|d[’'])?\s*(?:un\s+)?(?:seuil\s+de\s+)?"
    r"(\d[\d\s.]{2,9}(?:,\d{2})?)\s*(?:€|EUR|euros)"
)


def montant_seuil(segment: str) -> str:
    """Montant du seuil vote, tel qu'ecrit dans la resolution.

    Rendu en chaine normalisee sans separateur de milliers. Chaine vide quand la
    resolution n'enonce pas de montant.
    """
    match = MONTANT_SEUIL_RE.search(segment)
    if not match:
        return ""
    brut = match.group(1).replace(" ", "").replace(".", "")
    return brut.replace(",", ".")


def valeurs_seuil(segment: str) -> dict[str, object]:
    """Montant et duree du seuil, lus dans le corps ET dans l'intitule.

    L'intitule annonce, le corps decide. Quand les deux different, c'est un
    CONSTAT et non une ambiguite a trancher: le proces-verbal du 03/07/2024
    porte deux discordances, la resolution 26 annoncant 2.000 EUR pour en fixer
    1.000, la resolution 27 annoncant 24 mois pour en decider 36.

    Le corps fait foi. L'intitule est conserve pour que la divergence se voie.
    """
    corps = decision_actee(segment)
    montant_corps = montant_seuil(corps) if corps else ""
    duree_corps = duree_mois(corps) if corps else None
    montant_titre = montant_seuil(segment)
    duree_titre = duree_mois(segment)

    divergences: list[str] = []
    if montant_corps and montant_titre and _nombre_egal(montant_corps, montant_titre):
        pass
    elif montant_corps and montant_titre:
        divergences.append(f"montant: intitule {montant_titre} / corps {montant_corps}")
    if duree_corps and duree_titre and duree_corps != duree_titre:
        divergences.append(f"duree: intitule {duree_titre} mois / corps {duree_corps} mois")

    return {
        "montant": montant_corps or montant_titre,
        "montant_intitule": montant_titre,
        "duree_mois": duree_corps if duree_corps is not None else duree_titre,
        "duree_intitule": duree_titre,
        "divergences": divergences,
    }


def _nombre_egal(a: str, b: str) -> bool:
    try:
        return abs(float(a) - float(b)) < 0.005
    except ValueError:
        return a == b


# --------------------------------------------------------------------------
# La portee: sur quoi la resolution porte, et donc ce qui la controle
# --------------------------------------------------------------------------
#
# Regle de conception appliquee ici, posee par Brice le 2026-09-04: **on concoit
# sur des axes de generalisation, jamais sur des modalites observees.**
#
# Le piege est visible a l'oeil nu sur le corpus. Un cabinet ecrit `Election du
# syndic`, l'autre `Designation du syndic`. Un cabinet ecrit `Vote du montant
# des marches et contrats a partir desquels la consultation du Conseil Syndical
# est obligatoire`, l'autre `Fixation du montant des marches et contrats, a
# partir duquel la consultation...`. Retenir le verbe reviendrait a apprendre un
# cabinet par coeur, et a se tromper au troisieme.
#
# Ce qui ne varie pas est ce que le texte impose:
#
# - la FONCTION est nommee par la loi. Syndic (art. 25 c), conseil syndical
#   (art. 21), president de seance et scrutateurs (decret art. 15), representant
#   du syndicat secondaire (decret art. 24). Les deux cabinets doivent l'ecrire,
#   parce que c'est elle que l'assemblee designe.
# - l'OBJET est nomme par la loi. `budget previsionnel` (art. 14-1 I), `fonds de
#   travaux` (art. 14-2), `mise en concurrence` (art. 21 al. 2), `appels de
#   fonds` (art. 14-1 I al. 3, decret art. 35).
# - la STRUCTURE tranche ce que les mots laissent ambigu. Un exercice clos avant
#   la date de l'assemblee ne peut pas etre un budget; un exercice qui court
#   apres elle ne peut pas etre une approbation des comptes. Aucun mot n'est
#   requis pour cela: seulement deux dates.
#
# Un fait mesure qui justifie le second temps: sur le proces-verbal du
# 03/07/2024, `qualifications` range `Modalites de recouvrement des charges` en
# APPROBATION_COMPTES, parce que le corps dit `approuve` et `charges`. La
# confirmation par la periode close supprime ce faux positif sans rien ajouter
# au vocabulaire.
# Les verbes de designation. Ce sont ceux du texte - l'article 25 c dit
# `designation`, l'article 21 dit `designes par l'assemblee generale` - et non
# ceux d'un cabinet. `candidature` y figure parce qu'une candidature soumise au
# vote EST la voie par laquelle une personne accede a la fonction.
VERBE_DESIGNATION_RE = re.compile(
    r"(?i)\b(?:[ée]lection|[ée]lire|[ée]lu[es]?|d[ée]signation|d[ée]signe\w*|"
    r"nomination|nomme\w*|renouvellement|candidat\w*)"
)

# `syndic` et non `syndical`: la limite de mot suffit, `syndical` ne la franchit
# pas. Sans elle, toute election de conseil syndical serait lue comme une
# designation de syndic - l'erreur exacte que l'article 21 al. 2 punit, puisque
# le contrat de syndic est le seul exclu du seuil de mise en concurrence.
FONCTION_SYNDIC_RE = re.compile(r"(?i)\bsyndics?\b")

# Le bureau de l'assemblee est teste AVANT le syndic, et ce n'est pas une
# preference de style: le decret art. 15 fait du syndic le secretaire de seance
# de plein droit. Le proces-verbal du 03/07/2024 ecrit donc, sous l'intitule
# `election du Secretaire`, `Elle nomme LE SYNDIC Mme X`. Chercher `syndic`
# d'abord rangeait cette resolution en designation de syndic, et lui retirait le
# controle de seuil au nom d'une exception - l'art. 21 al. 2 - qui ne la vise
# pas. La fonction designee prime sur la personne designee.
FONCTION_BUREAU_RE = re.compile(
    r"(?i)pr[ée]sident\w*\s+de\s+s[ée]ance|scrutateur|secr[ée]tai\w*|"
    r"bureau\s+de\s+(?:s[ée]ance|la\s+s[ée]ance|l[’']assembl[ée]e)"
)

FONCTION_ORGANE_RE = re.compile(
    r"(?i)conseil\s+syndical|repr[ée]sentant\w*\s+d\w*\s+(?:SDC|syndicat)"
)

# Article 25 b: l'autorisation donnee a certains coproprietaires d'effectuer A
# LEURS FRAIS des travaux affectant les parties communes. Trois elements du
# texte, tous requis: une autorisation, des travaux, et un beneficiaire qui est
# un coproprietaire et non une entreprise du syndicat.
AUTORISATION_RE = re.compile(r"(?i)autoris\w*|demande\s+d[’']autorisation")
TRAVAUX_PRIVATIFS_RE = re.compile(
    r"(?i)travaux\s+privatifs|installer|installation|pose\s+de|"
    r"travaux\s+affectant\s+les\s+parties\s+communes"
)
BENEFICIAIRE_COPRO_RE = re.compile(
    r"(?i)[àa]\s+ses\s+frais|[àa]\s+leurs\s+frais|[àa]\s+la\s+demande\s+de\s+"
    r"(?:M\.|Mme|Mlle|M\s)|coproprietaire|copropri[ée]taire"
)
# L'autorisation permanente de penetrer dans les parties communes releve de
# l'article 24 II h et n'emporte aucun travaux: elle ne doit pas etre lue comme
# une autorisation de l'article 25 b.
AUTORISATION_ACCES_RE = re.compile(r"(?i)p[ée]n[ée]trer|police|gendarmerie")

# Objets nommes par la loi. Aucun de ces mots n'est un choix de redaction: ils
# sont le nom que le texte donne a la chose.
COMPTES_RE = re.compile(r"(?i)\bcomptes?\b")
APPROBATION_RE = re.compile(r"(?i)approb\w*|approuv\w*|arr[êe]t[ée]\s+des\s+comptes")
BUDGET_RE = re.compile(r"(?i)\bbudget\w*")
FONDS_TRAVAUX_RE = re.compile(
    r"(?i)fonds\s+(?:de\s+)?travaux|plan\s+pluriannuel|cotisation\s+annuelle"
)
MODALITES_RE = re.compile(
    r"(?i)appels?\s+de\s+fonds|exigib\w*|provisions?|[ée]ch[ée]ancier|"
    r"recouvrement|pi[èe]ces\s+justificatives|clause\s+d[’']aggravation|"
    r"agir\s+en\s+justice|habilit\w*|autorisation\s+permanente|"
    r"tout\s+pouvoir|pleins?\s+pouvoirs?"
)
# Article 44 du decret: travaux, marches, contrats, etudes techniques. C'est la
# liste du texte, pas celle d'un syndic.
ENGAGEMENT_RE = re.compile(
    r"(?i)\btravaux\b|march[ée]s?\b|\bcontrat\w*|\bdevis\b|"
    r"[ée]tudes?\s+techniques?|diagnostic\w*"
)
# Un montant en euros, quelle que soit sa forme d'ecriture. Sert de confirmation
# structurelle a l'engagement: l'article 11 I 3 du decret exige les conditions
# essentielles du contrat, donc un engagement porte un prix.
MONTANT_RE = re.compile(r"\d[\d\s.]*(?:,\d{2})?\s*(?:€|EUR\b|euros)")

def _proche(segment: str, gauche: re.Pattern[str], droite: re.Pattern[str],
            fenetre: int = FENETRE_CONFIRMATION) -> bool:
    """Les deux motifs apparaissent-ils a portee l'un de l'autre.

    Meme mecanique que `qualifications`, et pour la meme raison mesuree: un
    `conseil syndical` nomme trois cents mots plus loin n'a rien a voir avec le
    verbe qu'on lui rattachait.
    """
    for candidat in gauche.finditer(segment):
        voisinage = segment[max(0, candidat.start() - fenetre):
                            candidat.end() + fenetre]
        if droite.search(voisinage):
            return True
    return False


def portee_resolution(segment: str, date_ag: str = "") -> tuple[str, list[str]]:
    """Sur quoi cette resolution porte, et ce qui a permis de le dire.

    Rend `(portee, indices)`. `indices` nomme les elements de texte legal qui
    ont decide, pour qu'un utilisateur puisse prendre la reponse en defaut sans
    relire le code - et pour qu'une portee ne soit jamais une affirmation nue.

    L'ordre des regles n'est pas un ordre de frequence: il va **du plus specifie
    par la loi au moins specifie**. Une delegation de l'article 21-1 et un seuil
    de l'article 21 al. 2 sont des objets a regime propre; ils passent avant
    l'engagement de depense, qui est le cas general de l'article 44 du decret.

    Quand rien ne decide, la portee est `ORDINAIRE`, c'est-a-dire **non
    determinee**, et tous les controles continuent de s'appliquer. Ne pas savoir
    n'est pas une raison de classer sans suite.
    """
    indices: list[str] = []
    quals = qualifications(segment)

    if "DELEGATION_CS" in quals:
        return PORTEE_DELEGATION_CS, ["delegation au conseil syndical (art. 21-1)"]

    if "SEUIL_CONSULTATION_CS" in quals or "SEUIL_MISE_EN_CONCURRENCE" in quals:
        return PORTEE_SEUIL, [
            "montant des marches et contrats arrete par l'assemblee (art. 21 al. 2)"
        ]

    if (AUTORISATION_RE.search(segment)
            and TRAVAUX_PRIVATIFS_RE.search(segment)
            and BENEFICIAIRE_COPRO_RE.search(segment)
            and not AUTORISATION_ACCES_RE.search(segment)):
        return PORTEE_AUTORISATION_COPROPRIETAIRE, [
            "autorisation de travaux affectant les parties communes, au profit "
            "d'un coproprietaire et a ses frais (art. 25 b)"
        ]

    if _proche(segment, VERBE_DESIGNATION_RE, FONCTION_BUREAU_RE):
        return PORTEE_DESIGNATION_ORGANE, [
            "bureau de l'assemblee, fonction nommee par le decret art. 15"
        ]

    if _proche(segment, VERBE_DESIGNATION_RE, FONCTION_SYNDIC_RE):
        return PORTEE_DESIGNATION_SYNDIC, [
            "designation du syndic, fonction nommee par l'art. 25 c"
        ]

    if _proche(segment, VERBE_DESIGNATION_RE, FONCTION_ORGANE_RE):
        return PORTEE_DESIGNATION_ORGANE, [
            "designation a une fonction nommee par la loi ou le decret "
            "(art. 21; decret art. 15 et 24)"
        ]

    close = periode_close(segment, date_ag)
    if COMPTES_RE.search(segment) and APPROBATION_RE.search(segment) and close:
        indices.append("comptes d'un exercice clos avant l'assemblee (art. 24 I)")
        return PORTEE_APPROBATION_COMPTES, indices

    if BUDGET_RE.search(segment) and close is False:
        return PORTEE_BUDGET, [
            "budget d'un exercice qui court apres l'assemblee (art. 14-1 I)"
        ]

    if FONDS_TRAVAUX_RE.search(segment):
        return PORTEE_FONDS_TRAVAUX, ["fonds de travaux (art. 14-2)"]

    if MODALITES_RE.search(segment):
        return PORTEE_MODALITES, [
            "modalite d'exigibilite, de recouvrement ou d'organisation, sans "
            "engagement propre (art. 14-1 I al. 2 et 3; decret art. 35 et 55)"
        ]

    if ENGAGEMENT_RE.search(segment) and MONTANT_RE.search(segment):
        return PORTEE_ENGAGEMENT_DEPENSE, [
            "travaux, marche ou contrat portant un montant (decret art. 44)"
        ]

    # Deux cas ou l'on refuse de conclure, et ou le dire vaut mieux que le type:
    # un `budget` ou des `comptes` sans periode lisible, et un objet qui ressemble
    # a un engagement sans montant. Dans les deux cas la loi n'a pas tranche, le
    # texte non plus, et une portee inventee retirerait des controles.
    if BUDGET_RE.search(segment) or COMPTES_RE.search(segment):
        indices.append("periode de l'exercice non lisible: comptes ou budget indecidable")
    elif ENGAGEMENT_RE.search(segment):
        indices.append("objet de type marche ou travaux, mais aucun montant lu")
    return PORTEE_ORDINAIRE, indices
