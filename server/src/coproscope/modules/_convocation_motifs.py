"""Motifs de lecture d'une convocation d'assemblee generale.

Une convocation n'est pas un proces-verbal degrade. Elle porte trois choses que
le PV ne porte pas, et aucune ne se lit avec les motifs du PV:

1. **deux enumerations du meme ensemble** - l'ordre du jour, puis les projets de
   resolution developpes. C'est un controle croise natif: la convocation se
   verifie elle-meme, sans etalon manuel;
2. **des projets**, jamais des votes. Aucune issue, aucun decompte de voix. La
   garde est portee par `resolutions.to_rows(..., etat=ETAT_PROJETEE)`, qui vide
   structurellement les colonnes de voix;
3. **des declarations sur d'autres assemblees** - contestation, rejeu, renvoi.
   Le preambule du 29/04/2026 nomme seize questions attaquees de l'assemblee du
   03/12/2025, et convoque pour en rejouer quarante-sept. Les deux portees sont
   differentes et aucune ne se deduit de l'autre.

Regle de prudence commune au lot: aucune valeur n'est deduite quand le texte ne
la porte pas. Un champ vide est un fait, pas un echec.
"""

from __future__ import annotations

import re

CONVOCATION_FIELDS = [
    "convocation_id",
    "doc_id",
    "ag_date",
    "points_ordre_du_jour",
    "sous_points",
    "devis_cites",
    "devis_quantifies",
    "annexes_citees",
    "declarations",
    "extraction_complete",
    "origine",
]

DEVIS_CITE_FIELDS = [
    "devis_cite_id",
    "convocation_id",
    "doc_id",
    "numero",
    "sous_numero",
    "objet",
    "entreprise",
    "montant_ttc",
    "etat_prix",
    "majorite_annoncee",
    "cle_repartition",
    "avis_cs_affirme",
    "analyse_offres_affirmee",
    "montant_intitule",
    "discordance_intitule_corps",
    "page",
    "origine",
]

DECLARATION_FIELDS = [
    "declaration_id",
    "convocation_id",
    "doc_id",
    "nature",
    "ag_visee",
    "questions_visees",
    "portee",
    "page",
    "origine",
]

# --- etats du prix d'un devis cite -----------------------------------------
#
# Trois etats, et le deuxieme est un constat et non un echec: une assemblee qui
# retient une entreprise sans prix global vote sans montant. Le modele appelle
# cette mesure le taux de resolutions quantifiees.
PRIX_QUANTIFIE = "QUANTIFIE"
PRIX_NON_QUANTIFIE = "NON_QUANTIFIE"
PRIX_NON_LU = "NON_LU"

NATURE_CONTESTATION = "CONTESTATION"
NATURE_REJEU = "REJEU"

PORTEE_PARTIELLE = "PARTIELLE"
PORTEE_TOTALE = "TOTALE"

ORIGINE_EXTRAIT = "EXTRAIT"
ORIGINE_CORRIGE = "CORRIGE_HUMAIN"

# --- ordre du jour et projets ----------------------------------------------

ORDRE_DU_JOUR_RE = re.compile(r"ordre\s+du\s+jour", re.IGNORECASE)

# Le separateur entre le numero et l'objet change d'un syndic a l'autre, et il
# n'y a aucune raison qu'il se stabilise: mesure sur deux copropietes.
#
#   CabinetAlfa (pseudo)   "12- objet"   "12.3- objet"   "12 . 3 - objet"
#   CabinetBeta      "12)"         "12.3) objet"   le numero seul sur sa ligne
#
# On accepte donc la famille de separateurs plutot qu'un seul, et l'objet peut
# etre vide: il est alors sur la ligne suivante.
SEPARATEUR = r"[-–.)\]]"
SOUS_POINT_RE = re.compile(
    rf"(?m)^\s*(\d{{1,3}})\s*[.\s]\s*(\d{{1,2}})\s*{SEPARATEUR}\s*(.{{0,160}}?)\s*$"
)
POINT_RE = re.compile(rf"(?m)^\s*(\d{{1,3}})\s*{SEPARATEUR}\s*(.{{0,180}}?)\s*$")

# Troisieme forme, et elle se passe de separateur: le mot porte le numero.
#
#   D4 immobilier   "Resolution n°1 : Designation du president (Article 24 - General)"
#
# Deux proprietes utiles. Elle est sans ambiguite en elle-meme, donc elle calibre
# un document sans avoir besoin d'une formule de cloture - ce qu'une convocation
# n'a jamais, puisque le vote n'a pas eu lieu. Et elle porte la majorite dans son
# intitule, entre parentheses, la ou les deux autres gabarits la mettent sur une
# ligne separee.
#
# Limite connue: l'OCR de ce corpus rend "Resolution n°S" pour "n°5". Un numero
# illisible n'est pas devine, la resolution est simplement absente du compte -
# et l'ecart avec l'enumeration annoncee le signale.
RESOLUTION_PREFIXE_RE = re.compile(
    r"(?mi)^\s*r[ée]solution\s*n[°o]\s*(\d{1,3})\s*:?\s*(.{0,180}?)\s*$"
)

# Un point peut n'etre soumis a aucun vote: "Sans vote" chez CabinetBeta marque une
# information, "Titre" un intitule de groupe qui coiffe des sous-points. Les
# compter comme des resolutions gonflerait le denominateur de tous les taux.
SANS_VOTE_RE = re.compile(r"^\s*(?:sans\s+vote|titre)\s*$", re.IGNORECASE)

# --- devis cites ------------------------------------------------------------
#
# Deux motifs distincts, jamais un groupe optionnel: rendu optionnel, le montant
# laisse le nom d'entreprise l'avaler quand il ne correspond pas. Mesure faite
# sur la convocation du 29/04/2026, ou l'optionnel rendait "PFM pour 520" comme
# raison sociale.
#
# Le PDF plie ses phrases n'importe ou: tout espace doit accepter un saut de
# ligne, sans quoi une phrase sur deux echappe au motif.
ENTREPRISE_AVEC_PRIX_RE = re.compile(
    r"par\s+l[’']entreprise\s+(?P<entreprise>[^.;•\n]{1,50}?)\s+pour\s+"
    # Ni le separateur decimal ni le symbole monetaire ne sont garantis: le meme
    # document ecrit "520.556,90" et "290 117.06", et un autre gabarit ecrira
    # EUR au lieu du symbole.
    r"(?P<montant>\d[\d\s.,\n]{2,16}[.,]\d{2})\s*(?:€|EUR)",
    re.IGNORECASE,
)
ENTREPRISE_SANS_PRIX_RE = re.compile(
    r"par\s+l[’']entreprise\s+(?P<entreprise>[^.;•\n\d]{2,50}?)\s*[.;]",
    re.IGNORECASE,
)
# Second gabarit de devis cite, et il est d'une autre nature.
#
# CabinetAlfa developpe un corps de resolution qui nomme l'entreprise ET son
# prix. CabinetBeta ne developpe rien: l'ordre du jour porte `20.2) CHOIX DE
# L'ENTREPRISE : SIMPLEX`, et le devis lui-meme arrive dans un fichier voisin.
#
# Consequence pour le modele: la meme information existe des deux cotes du lien
# selon le syndic. Chez l'un le devis CITE est riche et la PIECE muette - un
# scan sans couche texte; chez l'autre la citation est reduite a une raison
# sociale et c'est la piece qui porte le numero, la date et les montants. Aucun
# des deux ne donne tout dans un seul objet.
CHOIX_ENTREPRISE_RE = re.compile(
    r"choix\s+de\s+l['’]entreprise\s*:\s*(?P<entreprise>[^\n:]{2,60}?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# "1.700 EUR TTC l'unite": un prix au detail, aucun total soumis au vote.
PRIX_UNITAIRE_RE = re.compile(r"(?:€|EUR)\s*TTC\s*l[’']unit[ée]", re.IGNORECASE)

# Ou commencent les projets developpes. La frontiere ne peut pas etre la
# pagination: une convocation deposee en texte brut n'a qu'une page, et exclure
# "la page de l'ordre du jour" y exclurait tout le document. La frontiere est
# structurelle - le premier corps de resolution -, et elle vaut quel que soit le
# support.
CORPS_RESOLUTION_RE = re.compile(
    r"(?:retient\s+la\s+proposition"
    r"|assembl[ée]e\s+g[ée]n[ée]rale[^.]{0,300}?d[ée]lib[ée]r"
    r"|projets?\s+de\s+r[ée]solutions?)",
    re.IGNORECASE,
)

# Le montant porte par l'INTITULE d'un projet, a comparer a celui du corps.
# L'intitule annonce, le corps decide: sur le PV du 03/07/2024, deux resolutions
# portent des valeurs differentes aux deux endroits - 2.000 EUR annonces contre
# 1.000 EUR decides, et 24 mois annonces contre 3 ans decides. Lire l'un des deux
# sans verifier l'autre donne un contresens qui ne se voit pas.
MONTANT_INTITULE_RE = re.compile(
    r"pour\s+(?P<montant>\d[\d\s.,]{2,16}[.,]\d{2})\s*(?:€|EUR)", re.IGNORECASE
)

# Voir `_resolutions_motifs.MAJORITE_RE`: le suffixe fait partie de l'identite
# de l'article, et l'enumerer effacait 33 references en silence (`C076`).
MAJORITE_RE = re.compile(
    r"articles?\s*(?:n[°o]\s*)?(2[3456](?:\s*-\s*\d{1,2})?)", re.IGNORECASE
)
CLE_REPARTITION_RE = re.compile(r"cl[ée]\s+([A-Z0-9]{2,6})\s+du\s+Syndic", re.IGNORECASE)

# Deux formules de style, systematiques chez ce syndic: 64 occurrences sur 64
# projets, mot pour mot. Elles affirment sans produire la piece, et c'est le
# syndic qui affirme sa propre conformite. On enregistre donc l'affirmation
# comme un fait mesurable, jamais comme une preuve.
AVIS_CS_AFFIRME_RE = re.compile(r"avis\s+du\s+conseil\s+syndical", re.IGNORECASE)
ANALYSE_OFFRES_RE = re.compile(r"analyse\s+des\s+offres", re.IGNORECASE)
CONDITIONS_ESSENTIELLES_RE = re.compile(r"conditions\s+essentielles", re.IGNORECASE)

# --- annexes ----------------------------------------------------------------

ANNEXE_NUMEROTEE_RE = re.compile(r"annexes?\s*(?:n[°o]\s*)?(\d{1,2})\b", re.IGNORECASE)
# "total de l'annexe 3" precede d'un montant: la resolution annonce elle-meme ce
# que l'annexe doit porter. C'est une reference qui doit resoudre.
#
# Le meme document ecrit "520.556,90" pour un devis et "290 117.06" pour un
# total d'annexe: le point ET la virgule y servent tour a tour de separateur
# decimal. Un motif qui n'accepte qu'une convention manque l'autre en silence.
MONTANT = r"\d[\d\s., ]{2,16}[.,]\d{2}"
TOTAL_ANNEXE_RE = re.compile(
    rf"(?P<montant>{MONTANT})\s*(?:€|EUR)?[^;]{{0,90}}?total\s+de\s+l['’]annexe\s+(?P<annexe>\d{{1,2}})",
    re.IGNORECASE,
)

# --- declarations sur d'autres assemblees -----------------------------------
#
# La source declare le lien elle-meme. Le suivre coute moins cher et se trompe
# moins qu'un appariement par ressemblance de libelle.
DATE_AG_RE = re.compile(r"(\d{2})[/.-](\d{2})[/.-](\d{4})")

# Une borne au premier point coupe le texte juridique n'importe ou: "2.000,00 EUR",
# "n°65/557", "10.07.1965" en portent tous. La borne exclut donc les points de
# fin de phrase, mais laisse passer ceux places entre deux chiffres.
HORS_FIN_DE_PHRASE = r"(?:[^.]|(?<=\d)\.(?=\d))"
CONTESTATION_RE = re.compile(
    rf"(?:proc[ée]dure|action|recours){HORS_FIN_DE_PHRASE}{{0,80}}?"
    r"(?:en\s+)?(?:nulit[ée]|nullit[ée]|annulation|contestation)"
    rf"(?P<suite>{HORS_FIN_DE_PHRASE}{{0,400}})",
    re.IGNORECASE,
)
REJEU_RE = re.compile(
    rf"(?:faire\s+)?re-?voter(?P<suite>{HORS_FIN_DE_PHRASE}{{0,240}})", re.IGNORECASE
)
REJEU_TOTAL_RE = re.compile(
    r"toutes\s+les\s+questions\s+de\s+l[’']ordre\s+du\s+jour", re.IGNORECASE
)
# "N°5, 6, 11-2, 12-2 et 46-2": la liste des questions visees, sous-numeros
# compris. Le "-2" n'est pas une plage, c'est une sous-resolution.
# La liste doit etre ANNONCEE. Sans introducteur, tout nombre du voisinage etait
# pris pour un numero de question: mesure sur la convocation Erables (pseudo) de
# 2023, ou six declarations de rejeu ont ete inventees a partir de dates et de
# references de dossier. Une declaration fausse coute plus cher qu'une
# declaration absente.
INTRODUCTEUR_QUESTIONS_RE = re.compile(
    r"(?:questions?|r[ée]solutions?|points?)\s*(?:n[°o]\s*)?", re.IGNORECASE
)
QUESTIONS_VISEES_RE = re.compile(r"\b(\d{1,3}(?:-\d{1,2})?)\b")
