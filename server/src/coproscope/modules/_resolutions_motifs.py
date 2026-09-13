"""Motifs et vocabulaire de lecture des proces-verbaux.

Separe de l'extraction pour que les motifs se relisent seuls: ce sont eux qui
changent d'un modele de PV a l'autre.

Origine: extraction des resolutions d'un proces-verbal d'assemblee generale.

Ce module lit le texte deja extrait d'un PV et produit une ligne par
resolution, la ou `agscope` ne produit qu'une ligne par document avec un
compteur.

Il n'interprete pas: il constate ce que le PV ecrit. La qualification en acte
d'autorisation, les liens vers une delegation ou une urgence et les controles de
conformite sont hors de ce module.

Regle de prudence: aucune valeur n'est deduite quand le texte ne la porte pas.
Un champ vide est un fait, pas un echec.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

RESOLUTION_FIELDS = [
    "resolution_id",
    "ag_id",
    "doc_id",
    "numero",
    # Le degre de la numerotation hierarchique du second cabinet: 11.1 a 11.8.
    # Sans lui, six sous-resolutions partageaient une seule cle et cinq
    # disparaissaient au stockage. La voie convocations portait deja le couple
    # `numero`/`sous_numero`, et le modele des actes aussi: le registre des
    # resolutions s'aligne au lieu d'inventer une troisieme convention.
    "sous_numero",
    "objet",
    "majorite_annoncee",
    "passerelle_citee",
    "passerelle_utilisee",
    "majorite_appliquee",
    "resultat",
    "voix_relevees",
    "voix_pour",
    "voix_contre",
    "voix_abstention",
    "base_voix",
    "position",
    "numerotation",
    "decision_actee",
    "qualifications",
    "duree_mois",
    "montant_seuil",
    "montant_intitule",
    "duree_intitule",
    "divergences",
    "valide_du",
    "valide_au",
    "etat",
    "origine",
    "confiance",
]

# Une resolution constatee est lue dans un proces-verbal: elle a ete votee.
# Une resolution projetee est lue dans une convocation: elle ne l'a pas ete.
# Les deux vivent dans le meme registre pour que l'ecart entre ce qui etait
# propose et ce qui a ete vote soit un tri, et non une jointure entre fichiers.
ETAT_CONSTATEE = "CONSTATEE"
ETAT_PROJETEE = "PROJETEE"

# Une ligne extraite par la machine, ou corrigee par un humain. Une
# re-extraction n'ecrase jamais une correction humaine.
ORIGINE_EXTRAIT = "EXTRAIT"
ORIGINE_CORRIGE = "CORRIGE_HUMAIN"

# Issue d'une resolution projetee: il n'y en a pas, et il ne peut pas y en
# avoir. Lire une convocation comme un PV rendait quatorze "adoptees"
# inventees; la garde est desormais dans le code, pas dans une consigne.
RESULTAT_PROJET = "PROJET"

# Deux familles de modeles de PV coexistent chez un meme syndic, et l'une n'est
# pas l'evolution de l'autre: mesure faite sur dix assemblees de 2021 a 2026.
#
#   famille A  "12° - objet"      cloture "En vertu de quoi cette resolution est"
#              2022, 2023, 2024 (AGE et AGO)
#   famille B  "12- objet"        cloture "En consequence, cette resolution est"
#              2021, 2025, 2026 (AGE et AG)
#
# Le point d'entree est donc la famille, pas un motif unique.
# Le point entre le numero et le degre est courant: le PV du 20/07/2022 ecrit
# "20.° -". Le lookbehind exclut le chiffre et le point qui precedent, pour ne
# pas prendre le "3" de "10.3 -" pour un numero de resolution.
NUMERO_RE_A = re.compile(r"(?<![\d.])(\d{1,3})\s*\.?\s*°\s*[-–]")

# Titre d'un point d'ordre du jour, en tete de ligne: "16- Fixation d'un
# montant...". Sert au repli par cloture, pour couper au titre plutot qu'au
# milieu de la formule de vote precedente, et pour recuperer le numero ECRIT
# dans le proces-verbal au lieu d'un rang calcule.
TITRE_ODJ_RE = re.compile(r"(?m)^[ \t]*(\d{1,3})\s*(?:°\s*)?[-–.)]\s*(?=[A-Za-zÀ-ÿ«\"])")

# Troisieme forme, mesuree le 2026-09-03 sur un autre syndic: le numero suit le
# mot au lieu de le preceder - "Resolution n°1 : Designation du president".
# Elle est aussi peu ambigue que la forme "12° -" et se retient donc de meme.
NUMERO_RE_PREFIXE = re.compile(r"(?i)r[ée]solution\s*n[°o]\s*(\d{1,3})")

# Le SOUS-numero de la meme forme: "Resolution n°11.2". Mesure du 2026-09-04 sur
# les vingt-deux textes du second cabinet: cinquante-neuf references distinctes,
# dont huit hierarchiques (1.1, 11.1, 11.2, 11.6, 11.7, 11.8, 13.1, 22.1).
# `NUMERO_RE_PREFIXE` ne capture que la partie entiere - c'est voulu, il sert a
# poser les marqueurs de segmentation et un sous-point est bien un segment. Mais
# sans le degre, {11, 11.1, 11.2, 11.6, 11.7, 11.8} rendaient SIX fois la meme
# cle: douze resolutions se reduisaient a quatre, et `INSERT OR REPLACE` jetait
# les huit autres sans rien lever. Le degre se relit donc en tete de segment,
# la ou il a servi a le decouper.
SOUS_NUMERO_RE = re.compile(r"(?i)r[ée]solution\s*n[°o]\s*\d{1,3}\s*\.\s*(\d{1,3})")
NUMERO_RE_B_LIGNE = re.compile(r"(?m)^[ 	]*(\d{1,3})\s*[-–]\s*(?=[A-Za-zÀ-ÿ«\"])")
# Dans un texte aplati, le numero suit un deux-points ou une fin de phrase et
# precede l'objet; l'annonce de majorite qui suit sert de confirmation.
NUMERO_RE_B_FLUX = re.compile(r"(?<![\d,.])(\d{1,3})\s*[-–]\s*(?=[A-Za-zÀ-ÿ«\"])")

NUMERO_RE = NUMERO_RE_A  # conserve pour compatibilite des appels existants

# ANNEAU 1 de l'axe de cloture - voir `_resolutions_cloture` pour l'axe entier.
#
# La formule mesuree sur les deux cabinets connus. Elle sert d'ANCRE de
# segmentation, et c'est pour cela qu'elle reste stricte: une ancre fausse ne
# nomme pas mal une issue, elle deplace la frontiere de deux resolutions. La
# forme large de la meme structure vit dans `_resolutions_cloture` et ne prend
# la main que si celle-ci ne rend rien en serie.
#
# Trois mots sont captures, pas un seul. Mesure du 2026-09-04 sur le second
# corpus: le cabinet B ecrit cinq fois "cette resolution est DEVENUE sans
# objet". En ne capturant que le premier mot, la lecture rendait "devenue", que
# le vocabulaire ne connait pas, et cinq votes sortaient de tous les comptages
# de l'ecran sans un drapeau. Le mot qui porte l'issue n'est pas toujours le
# premier: on lit la locution, et le premier mot reconnu tranche.
CLOTURE_RE = re.compile(
    r"cette r[ée]solution est\s+(?P<issue>[a-zéèêA-ZÉÈÊ]+(?:\s+[a-zéèêA-ZÉÈÊ]+){0,2})",
    re.IGNORECASE,
)

# Passerelle de l'article 25-1: citation, puis usage effectif.
PASSERELLE_CITEE_RE = re.compile(r"25-1")
PASSERELLE_UTILISEE_RE = re.compile(
    r"il est pass[ée] au vote suivant l.article\s*25-1", re.IGNORECASE
)

# "Article 24", "Articles 25 et 25-1", "article n° 26": le pluriel et le numero
# sont courants et ne doivent pas faire manquer la majorite.
#
# **Le suffixe fait partie de l'IDENTITE de l'article, et l'enumerer etait une
# modalite.** Constat `C076`, corrige le 2026-09-10. Le motif s'ecrivait
# `2[3456](?:-1)?`: il connaissait le seul suffixe que quelqu'un avait vu,
# `25-1`, et **effacait tous les autres en silence**. Mesure sur le corpus reel,
# forme par forme: `26-4` x25, `26-5` x4, `26-6` x4 - **33 references lues comme
# un simple `26`**, c'est-a-dire attribuees a la majorite des deux tiers de
# l'article 26 alors que ces articles-la portent l'emprunt collectif et non le
# regime de majorite des modifications statutaires.
#
# L'axe: **un numero d'article peut porter un suffixe, et ce suffixe le
# distingue d'un autre article.** Ce qui reste invariant est la forme
# `<numero>` eventuellement suivie de `-<numero>`. Hors des valeurs observees,
# un suffixe inconnu est desormais RENDU tel quel: `regime_de_majorite` ne le
# reconnait pas et rend `None`, ce qui se declare, au lieu d'etre range sous un
# regime que le texte n'enonce pas.
MAJORITE_RE = re.compile(
    r"articles?\s*(?:n[°o]\s*)?(2[3456](?:\s*-\s*\d{1,2})?)", re.IGNORECASE
)


def article_lu(capture: str) -> str:
    """La reference d'article, sous la forme unique `26-4`.

    Le motif tolere les blancs autour du tiret - un syndic ecrit
    `article 26 - 4` - mais la valeur comparee en aval ne doit exister qu'en UNE
    forme: `_decompte_voix_regimes` cherche `25-1` dans une table, et `25 - 1`
    n'y serait pas. Tolerer a la lecture et normaliser a la sortie, jamais
    l'inverse.
    """
    return re.sub(r"\s*-\s*", "-", str(capture or "").strip())

# Decomptes de voix exprimes en tantiemes, "4 746/10.000".
# La base n'est acceptee que si elle est une base de tantiemes plausible. Sans
# cette contrainte, "01/01/2024" est lu comme 1 voix sur 2024.
BASE_TANTIEMES = r"(?:100[.\s]?000|10[.\s]?000|1[.\s]?000)"
VOIX_RE = re.compile(rf"(\d[\d\s.]{{0,8}})\s*/\s*({BASE_TANTIEMES})(?!\d)")

# Decomptes nommes. Le "contre" et les abstentions sont souvent introduits par
# un "TOTAL :" suivi du detail nominatif, qu'on ne lit pas.
# La base de tantiemes varie d'une copropriete et d'une assemblee a l'autre:
# 10.000, 6340, 5258, 5249, 2222 ont ete rencontrees. On la lit donc dans le
# contexte du vote plutot que dans une liste de valeurs attendues.
POUR_RE = re.compile(
    r"ont vot[ée]s?\s+pour\s*:?\s*(?:TOTAL\s*:)?\s*(\d[\d\s.]*)(?:\s*/\s*(\d[\d\s.]*))?",
    re.IGNORECASE,
)
CONTRE_RE = re.compile(r"ont vot[ée]s?\s+contre\s*:?\s*(?:TOTAL\s*:)?\s*(\d[\d\s.]*)", re.IGNORECASE)
ABSTENTION_RE = re.compile(r"se sont abstenus?\s*:?\s*(?:TOTAL\s*:)?\s*(\d[\d\s.]*)", re.IGNORECASE)

PAS_DE_VOTE_RE = re.compile(r"pas de vote", re.IGNORECASE)

# Vocabulaire releve sur neuf assemblees de 2021 a 2026: adoptee 286,
# rejetee 165, refusee 18, sans objet 1, reportee 1, et un "rejatee" qui est une
# coquille d'oceriser. On reconnait donc par PREFIXE, ce qui absorbe le bruit
# d'OCR sans avoir a lister chaque deformation.
ISSUE_PREFIXES: tuple[tuple[str, str], ...] = (
    ("adopt", "ADOPTEE"),
    ("approuv", "ADOPTEE"),
    ("rejet", "REJETEE"),
    ("rejat", "REJETEE"),   # coquille OCR rencontree
    ("refus", "REJETEE"),
    ("repouss", "REJETEE"),
    ("report", "REPORTEE"),
    ("ajourn", "REPORTEE"),
)

SANS_OBJET = "SANS_OBJET"
REPORTEE = "REPORTEE"

# "sans" seul n'est pas une issue, et l'avoir traite comme un prefixe a produit
# une regression mesuree le 2026-09-05, le jour ou la fenetre de capture est
# passee a trois mots et ou chaque mot a commence a etre essaye:
#
#   "cette resolution est votee sans opposition"  -> SANS_OBJET
#   "cette resolution est acceptee sans reserve"  -> SANS_OBJET
#   "cette resolution est prise sans debat"       -> SANS_OBJET
#
# Le mot qui porte l'issue n'etait pas reconnu, le scan atteignait "sans" et
# tranchait. La ligne entrait alors dans le compteur "sans vote" avec une
# confiance moyenne et hors de la liste de relecture: une resolution votee
# comptee comme non votee, sans drapeau. Avant l'elargissement ces lignes
# etaient invisibles; apres, elles etaient fausses et comptees.
#
# Ce qui est une issue, c'est la locution entiere. On exige donc le mot qui
# suit: chaque entree est une suite de prefixes a reconnaitre sur des mots
# consecutifs.
ISSUE_LOCUTIONS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("sans", "objet"), SANS_OBJET),  # aucun candidat, rien a voter
)

# Une formule de cloture lue, dont aucun mot n'est reconnu. C'est un fait, pas
# une issue: la ligne precedente rendait `mot.upper()`, c'est-a-dire une valeur
# inventee que ni les libelles d'ecran, ni les trois compteurs, ni la liste de
# relecture ne connaissaient. Cinq votes du second cabinet sortaient ainsi de
# tous les comptages - 91 resolutions annoncees, 86 comptees - sans exception et
# sans trace. La valeur brute lue reste accessible dans le segment; ce qui est
# stocke est un etat du vocabulaire, appele a relecture.
ISSUE_NON_RECONNUE = "ISSUE_NON_RECONNUE"

# Quatre absences d'issue, qui ne disent pas la meme chose.
PAS_DE_VOTE = "PAS_DE_VOTE"          # le PV l'ecrit explicitement
VOTE_SANS_FORMULE = "VOTE_SANS_FORMULE"  # des voix sont comptees, aucune adoption enoncee
SANS_ISSUE = "SANS_ISSUE_TRACEE"     # ni vote, ni formule, ni mention

# Le document DIT quelque chose sur cette resolution, et la chaine ne sait pas
# le lire. C'est le quatrieme etat, et il est le seul qui manquait: sans lui,
# un proces-verbal redige autrement rendait `SANS_ISSUE_TRACEE`, c'est-a-dire
# exactement ce que rend un document qui ne dit rien. Un ecran qui affiche zero
# et un document qui ne contient rien devenaient indiscernables.
#
# Il ne se deduit d'aucun vocabulaire: il se deduit de la PRESENCE d'un temoin
# d'issue dans un segment dont aucune formule de cloture n'a ete lue.
ISSUE_ENONCEE_NON_LUE = "ISSUE_ENONCEE_NON_LUE"

# TEMOIN de l'axe de cloture - anneau 3, voir `_resolutions_cloture`.
#
# N'importe quel participe d'issue, sans son entourage. Ce detecteur est
# DELIBEREMENT trop large: il ne cree ni ancre, ni resolution, ni issue. Il ne
# repond qu'a `le document dit-il ici quelque chose que je ne sais pas lire ?`,
# et c'est cette reponse qui rend la degradation bruyante au lieu de muette.
#
# Mesure du 2026-09-08 sur les deux cabinets: dans un proces-verbal lu
# correctement, il reste 4 a 8 temoins non couverts par la formule de cloture -
# `lu et approuve`, `exercice precedent approuve`, `le plan de financement tel
# qu'il vient d'etre adopte`. Le temoin ne sert donc jamais seul: il n'a de
# sens que RAPPORTE au nombre de segments, ce que fait `issues_muettes`.
PARTICIPE_ISSUE_RE = re.compile(
    r"(?i)\b(?:adopt|approuv|rejet|rejat|refus|repouss|report|ajourn)[eéèê]{1,2}s?\b"
)

# Sous ce nombre d'occurrences, une formule n'est pas une SERIE: une lettre peut
# citer une resolution sans en porter la suite. Le seuil vivait en double, dans
# `_resolutions_calibrage` et dans `_resolutions_registre`; il est nomme une
# fois ici parce que les trois anneaux de l'axe s'en servent.
MINIMUM_SERIE = 3

# Part des segments qui doivent enoncer une issue non lue pour qu'on affirme que
# le document VOTE sans qu'on sache le lire. Mesure du 2026-09-08: une
# convocation du second cabinet porte 3 participes pour 77 resolutions
# projetees, soit 4 %; un proces-verbal en porte un par resolution. La moitie
# separe donc les deux avec une marge large, et le seuil n'a pas ete choisi
# pour coller a une valeur observee.
SEUIL_SERIE_ISSUES = 0.5

# Signature typographique d'une numerotation: le nombre, puis le suffixe qui
# le separe de l'objet. C'est sur ce suffixe que porte l'auto-calibrage.
SIGNATURE_RE = re.compile(r"(?<![\d,.])(\d{1,3})(\s*(?:°\s*[-–]|[-–).]))\s*(?=[A-Za-zÀ-ÿ«\"])")


# --------------------------------------------------------------------------
# Comment un document d'assemblee se nomme lui-meme
# --------------------------------------------------------------------------
#
# Deplace ici depuis `_resolutions_registre` le 2026-09-08: l'axe de cloture a
# besoin de cette declaration pour distinguer un proces-verbal illisible d'un
# document qui cite des mots d'issue, et `_resolutions_cloture` ne peut pas
# importer le registre sans cycle. Le motif reste importable depuis le
# registre, ou plusieurs appelants le prennent.

TETE_DOCUMENT = 600

#: Un document qui se declare proces-verbal en tete l'est, quoi qu'il cite
#: ensuite. Il prime sur la declaration de demande, pour le cas reel du
#: proces-verbal qui met aux voix une demande d'inscription.
#:
#: **L'axe: la maniere dont le titre separe ses deux mots.** La premiere
#: ecriture, `[-\s]?`, n'admettait qu'UN caractere - donc `proces-verbal` et
#: `proces verbal`, et rien d'autre. Mesure du 2026-09-05 sur six formes de
#: titre: quatre echouaient, dont « PROCES - VERBAL », forme courante des que
#: l'OCR aere un titre en capitales. La consequence n'etait pas cosmetique: le
#: document retombait sur la declaration de demande d'inscription lue dans la
#: meme tete, `build_register` l'ecartait, et toutes ses resolutions
#: disparaissaient du coffre.
#:
#: **Ce qui reste invariant le long de l'axe**: les deux mots restent contigus.
#: Trois caracteres de separation au plus couvrent le tiret entoure d'espaces,
#: le double espace et la coupure de ligne, sans jamais rapprocher deux mots
#: qu'une phrase separe. **Hors des valeurs observees**: un titre qui espacerait
#: chaque lettre - « P R O C E S - V E R B A L » - n'est pas reconnu, et le
#: document retombe sur la regle des clotures en serie, degradation identique a
#: celle d'un document sans titre.
TITRE_PV_RE = re.compile(r"(?i)proc[eè]s[\s-]{0,3}verbal")
