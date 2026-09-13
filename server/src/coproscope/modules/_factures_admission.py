"""Ce qui fait qu'un document est une facture. Lot `RM-2026-0058`.

======================================================================
Le defaut corrige
======================================================================

`_looks_like_invoice` admettait un document si son debut contenait l'annee et
l'un des mots `facture`, `invoice`, `avoir`, `note d'honoraires`, `total ttc`.
C'est un **temoin de vocabulaire**, et la doctrine du depot le nomme: un
variant deguise en invariant. Un proces-verbal d'assemblee parle de factures.
Un tableau de bord parle de factures. Aucun des deux n'en est une.

Constat qui a ouvert l'item: 4 lignes sur 601 portaient 5 285 937,26 EUR, soit
94,5 pour cent du total, et venaient de deux documents comptes deux fois, d'un
tableur de tableau de bord et d'un rapport d'assemblee.

Mesure du 2026-09-08 sur 341 pieces reelles d'un extranet de syndic, nommees
par empreinte donc sans vocabulaire exploitable dans le nom: la regle de
vocabulaire admet 29 pieces sur les exercices 2022 a 2025. Sur ces 29, **10 ne
portent pas la forme d'une facture**, dont 5 qui ne portent qu'une date - ni
numero, ni identifiant d'emetteur, ni structure de totaux.

======================================================================
L'axe, et l'invariant retenu
======================================================================

*L'axe*: **ce qui fait qu'un document est une facture**. Les modalites
observees - le mot `facture`, la mise en page d'un fournisseur, la mention
`TOTAL TTC` - sont des habitudes de redaction. Un fournisseur etranger, une
note d'honoraires, un avoir ou un appel de cotisation se placent ailleurs sur
cet axe sans cesser d'etre des pieces payables.

*L'invariant*: une facture est une **obligation de paiement identifiee et
chiffree**. Ce qui reste vrai le long de l'axe ne vient pas de l'usage mais du
droit - article 242 nonies A du code general des impots et article L441-9 du
code de commerce imposent un numero, une date, l'identite des parties et le
montant du, avec sa decomposition de taxe. Deux proprietes en decoulent, et
elles ne dependent d'aucun cabinet:

1. la piece est **identifiable**: elle porte un numero et une date;
2. son chiffrage **se ferme**: hors taxes plus taxe egale toutes taxes, au
   centime.

*Ce que le code en fait*: la seconde propriete est une **conservation**, et
c'est elle qui porte la decision. Une conservation signale sa propre panne, la
ou une liste de mots ne le fait jamais. Un proces-verbal ou un tableur ne la
satisfont pas par accident.

*Hors des valeurs observees*: trois degradations, toutes **nommees et
comptees**, jamais silencieuses.

- Une facture sans taxe applicable - auto-entrepreneur, exoneration - donne
  hors taxes egal toutes taxes et taxe nulle. La conservation tient
  trivialement, et la piece est admise: le mode degrade est correct.
- Une piece dont la couche de texte est illisible - 61 des 341 pieces du
  corpus mesure, soit 18 pour cent - ne peut pas fermer son chiffrage. Elle est
  refusee avec le motif `MONTANTS_ILLISIBLES` et **comptee**. C'est un progres
  sur l'etat anterieur, qui les ignorait en silence: l'operateur apprend qu'il
  lui manque une reconnaissance de caracteres, au lieu de croire son corpus
  complet.
- Un gabarit inconnu qui ferme son chiffrage passe sans que rien n'ait ete code
  pour lui. S'il ne le ferme pas, il est refuse en nommant ce qui manque.

Ce module ne devine jamais de fournisseur. `RM-2026-0058` a mesure que 69 pour
cent des valeurs distinctes d'une colonne fournisseur deduite n'etaient pas des
noms d'entreprise - le mot `TTC` seul sur 94 lignes, une ligne d'en-tete de
tableur, des montants, une adresse. Un champ que l'on ne sait pas remplir reste
vide et se voit; rempli au hasard, il se propage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

#: Tolerance de fermeture du chiffrage. Une facture arrondit au centime; au dela
#: ce n'est plus un arrondi, c'est une lecture qui n'a pas compris le document.
TOLERANCE = Decimal("0.02")

ADMISE = "ADMISE"
#: Admise, mais sur une base plus faible: la piece porte un total du sans en
#: imprimer la decomposition, donc la conservation n'a pas pu la controler. Le
#: motif est distinct pour que ce niveau de preuve reste comptable a part.
ADMISE_SANS_DECOMPOSITION = "ADMISE_SANS_DECOMPOSITION"
REFUS_SANS_IDENTIFICATION = "REFUS_SANS_IDENTIFICATION"
REFUS_MONTANTS_ILLISIBLES = "REFUS_MONTANTS_ILLISIBLES"
REFUS_CHIFFRAGE_NON_FERME = "REFUS_CHIFFRAGE_NON_FERME"

_MOTIFS_LISIBLES = {
    ADMISE: "La piece porte un numero, une date, et son chiffrage se ferme.",
    ADMISE_SANS_DECOMPOSITION: (
        "La piece porte un numero, une date et un montant du, mais n'imprime pas "
        "sa decomposition de taxe: le chiffrage n'a pas pu etre controle."
    ),
    REFUS_SANS_IDENTIFICATION: (
        "La piece ne porte pas de quoi l'identifier comme facture: il lui manque "
        "un numero, une date, ou les deux."
    ),
    REFUS_MONTANTS_ILLISIBLES: (
        "Les montants de la piece n'ont pas pu etre lus. La couche de texte est "
        "probablement absente ou degradee: une reconnaissance de caracteres est "
        "necessaire avant de conclure."
    ),
    REFUS_CHIFFRAGE_NON_FERME: (
        "Hors taxes plus taxe ne retombe pas sur le total toutes taxes. La piece "
        "n'est pas une facture, ou sa lecture est incomplete."
    ),
}

# Un numero de piece: un libelle de numerotation suivi d'une valeur. Le libelle
# est un AXE - `facture`, `fact`, `n`, `invoice`, `avoir` - et non une liste
# fermee de gabarits de fournisseurs.
_NUMERO = re.compile(
    r"(?:factur\w*|fact\.?|invoice|avoir|note\s+d[e']\s*honoraires?|pi[eè]ce)"
    r"[^\n\r:]{0,24}?[:. ]\s*(?:n[°oº]\s*)?([A-Z]{0,5}[-/ ]?\d+[A-Z0-9-]*)",
    re.IGNORECASE,
)
_NUMERO_NU = re.compile(r"\bn[°oº]\s*[:.]?\s*([A-Z]{0,5}[-/ ]?\d+[A-Z0-9-]*)", re.IGNORECASE)

_DATE = re.compile(r"\b(\d{1,2})[/.\- ](\d{1,2}|[a-zéû]{3,9})[/.\- ](\d{2,4})\b", re.IGNORECASE)

# Montants etiquetes. Le libelle est encore un axe: `TTC`, `toutes taxes`,
# `total a payer`, `net a payer` designent la meme grandeur.
_MONTANT = r"(-?\d{1,3}(?:[\u00a0\u202f .]\d{3})*(?:[.,]\d{2})|-?\d+[.,]\d{2})"

#: Fenetre de lecture apres un libelle. Le montant suit son libelle dans l'ordre
#: de lecture, pas forcement sur la meme ligne: la couche de texte d'un PDF
#: aplatit le tableau, un jeton par ligne. Exiger la meme ligne aurait code une
#: modalite de mise en page - mesure: cette seule exigence rejetait la totalite
#: des 81 factures reelles admises du corpus.
_FENETRE = 80

# Les sigles sont bornes des DEUX cotes. Sans la borne de gauche, `h\.?\s?t\.?\b`
# reconnait le `ht` final de `night`, `acht`, `recht`: sur une prose de 185 000
# caracteres cela fabrique des centaines de faux libelles, qui coutent en temps
# et surtout en montants ramasses au hasard. Le sigle est un mot, pas une suite
# de lettres.
_LIBELLE_TTC = re.compile(
    r"\bt\.?t\.?c\.?(?![a-z])|\btoutes\s+taxes|\b(?:total|net|montant)\s+(?:a\s+)?payer",
    re.IGNORECASE,
)
_LIBELLE_HT = re.compile(r"\bh\.?\s?t\.?(?![a-z])|\bhors\s+taxes?", re.IGNORECASE)
_LIBELLE_TVA = re.compile(r"\bt\.?v\.?a\.?(?![a-z])|\btaxe\s+sur\s+la\s+valeur", re.IGNORECASE)

#: Un nombre suivi d'un pourcent est un TAUX, jamais un montant. Confondre les
#: deux faisait lire `TVA 20,00 % / 200,00` comme une taxe de 20,00 et refusait
#: la facture pour chiffrage non ferme.
_SUIVI_DE_POURCENT = re.compile(r"\s*%")
_NOMBRE = re.compile(_MONTANT)


_TVA_ABSENTE = re.compile(
    r"tva\s+non\s+applicable|exon[ée]r\w*\s+de\s+tva|autoliquidation|article\s+293\s*b",
    re.IGNORECASE,
)


def _nombre(texte: str) -> Decimal | None:
    nettoye = texte.replace(" ", "").replace(" ", "").replace(" ", "")
    if "," in nettoye:
        nettoye = nettoye.replace(".", "").replace(",", ".")
    try:
        return Decimal(nettoye)
    except (InvalidOperation, ValueError):
        return None


def _montants(libelle: re.Pattern[str], texte: str) -> list[Decimal]:
    """Les montants qui suivent un libelle, dans sa fenetre de lecture.

    Rend tous les candidats plutot que le premier: une facture imprime des
    lignes, des sous-totaux et un report, et supposer que le bon montant est le
    premier - ou le dernier - dependrait de l'ordre de lecture du PDF, qui est
    un artefact de l'outil. C'est la fermeture du chiffrage qui tranche ensuite.
    """

    valeurs: list[Decimal] = []
    for trouve in libelle.finditer(texte):
        fenetre = texte[trouve.end() : trouve.end() + _FENETRE]
        for nombre in _NOMBRE.finditer(fenetre):
            if _SUIVI_DE_POURCENT.match(fenetre[nombre.end() :]):
                continue
            valeur = _nombre(nombre.group(1))
            if valeur is not None and valeur not in valeurs:
                valeurs.append(valeur)
    return valeurs


@dataclass(frozen=True)
class AdmissionFacture:
    """Le verdict d'admission d'une piece, avec de quoi le contester."""

    admise: bool = False
    motif: str = REFUS_SANS_IDENTIFICATION
    numero: str = ""
    date: str = ""
    ht: Decimal | None = None
    tva: Decimal | None = None
    ttc: Decimal | None = None
    ecart: Decimal | None = None

    @property
    def explication(self) -> str:
        base = _MOTIFS_LISIBLES.get(self.motif, self.motif)
        if self.motif == REFUS_CHIFFRAGE_NON_FERME and self.ecart is not None:
            return f"{base} Ecart mesure: {self.ecart} EUR."
        return base


def _identification(texte: str) -> tuple[str, str]:
    numero = ""
    trouve = _NUMERO.search(texte) or _NUMERO_NU.search(texte)
    if trouve:
        numero = trouve.group(1).strip()
    date = ""
    trouve_date = _DATE.search(texte)
    if trouve_date:
        date = trouve_date.group(0).strip()
    return numero, date


def _chiffrage_ferme(
    ht_values: list[Decimal], tva_values: list[Decimal], ttc_values: list[Decimal]
) -> tuple[Decimal, Decimal, Decimal] | None:
    """Le premier triplet (ht, tva, ttc) qui se ferme, ou `None`.

    Une facture imprime souvent plusieurs montants - lignes, sous-totaux,
    report. Chercher un triplet qui se ferme, plutot que de supposer que le
    dernier montant lu est le bon, evite de dependre de l'ordre de lecture du
    PDF, qui est un artefact de l'outil et non une propriete du document.
    """

    for ttc in ttc_values:
        for ht in ht_values:
            for tva in tva_values:
                if abs((ht + tva) - ttc) <= TOLERANCE:
                    return ht, tva, ttc
    return None


def admettre_facture(texte: str) -> AdmissionFacture:
    """Dit si un document est une facture, et sinon pourquoi il ne l'est pas."""

    numero, date = _identification(texte)
    if not numero or not date:
        return AdmissionFacture(motif=REFUS_SANS_IDENTIFICATION, numero=numero, date=date)

    ttc_values = _montants(_LIBELLE_TTC, texte)
    ht_values = _montants(_LIBELLE_HT, texte)
    tva_values = _montants(_LIBELLE_TVA, texte)

    if not ttc_values and not ht_values:
        return AdmissionFacture(motif=REFUS_MONTANTS_ILLISIBLES, numero=numero, date=date)

    # Piece sans taxe applicable - franchise en base, exoneration,
    # autoliquidation. L'emetteur le DECLARE, et une declaration explicite pese
    # plus qu'un nombre ramasse au voisinage du mot `TVA`: sur une facture en
    # franchise, le montant le plus proche de la mention est le total lui-meme.
    # La taxe nulle est donc ajoutee aux candidats, jamais substituee a eux.
    if _TVA_ABSENTE.search(texte):
        tva_values = [Decimal("0.00"), *tva_values]
    if ttc_values and ht_values and not tva_values:
        tva_values = [Decimal("0.00")]

    # Une decomposition qui n'est pas imprimee ne peut pas se fermer. Exiger
    # qu'elle se ferme quand meme reviendrait a coder une modalite: `toute
    # facture imprime son hors taxes`. C'est faux - une facture au forfait, un
    # ticket, une note simple n'affichent qu'un total du.
    #
    # La conservation est donc un test de REFUTATION, pas une condition
    # d'entree. Quand la decomposition est imprimee et ne se ferme pas, c'est
    # une preuve CONTRE la piece et elle est refusee. Quand elle est absente, la
    # conservation est muette, et l'admission retombe sur ce qui reste verifie:
    # une piece identifiee qui porte un montant du. L'absence de preuve n'est
    # pas une preuve d'absence.
    if ttc_values and not ht_values and not tva_values:
        return AdmissionFacture(
            admise=True,
            motif=ADMISE_SANS_DECOMPOSITION,
            numero=numero,
            date=date,
            ttc=ttc_values[0],
        )

    ferme = _chiffrage_ferme(ht_values, tva_values, ttc_values)
    if ferme is None:
        ecart = None
        if ttc_values and ht_values:
            ecart = (ht_values[0] + (tva_values[0] if tva_values else Decimal("0.00"))) - ttc_values[0]
        return AdmissionFacture(
            motif=REFUS_CHIFFRAGE_NON_FERME,
            numero=numero,
            date=date,
            ht=ht_values[0] if ht_values else None,
            tva=tva_values[0] if tva_values else None,
            ttc=ttc_values[0] if ttc_values else None,
            ecart=ecart,
        )

    ht, tva, ttc = ferme
    return AdmissionFacture(
        admise=True,
        motif=ADMISE,
        numero=numero,
        date=date,
        ht=ht,
        tva=tva,
        ttc=ttc,
        ecart=(ht + tva) - ttc,
    )


@dataclass(frozen=True)
class BilanAdmission:
    """Le bilan d'un corpus, verifiable par soustraction.

    `admises + refusees == lues` tient par construction, et le bilan existe pour
    que cette egalite soit affichable donc contestable. Les refus sont ventiles
    par motif: un corpus ou 18 pour cent des pieces sont illisibles n'est pas le
    meme probleme qu'un corpus ou 18 pour cent ne sont pas des factures.
    """

    lues: int = 0
    admises: int = 0
    refusees: int = 0
    total_admis: Decimal = Decimal("0.00")
    par_motif: tuple[tuple[str, int], ...] = ()

    @property
    def tient(self) -> bool:
        return self.admises + self.refusees == self.lues


def bilan(pieces: dict[str, str]) -> tuple[dict[str, AdmissionFacture], BilanAdmission]:
    """Admet un sac de pieces et rend le verdict de chacune avec le bilan."""

    verdicts: dict[str, AdmissionFacture] = {}
    motifs: dict[str, int] = {}
    admises = 0
    total = Decimal("0.00")
    for identifiant in sorted(pieces):
        verdict = admettre_facture(pieces[identifiant])
        verdicts[identifiant] = verdict
        motifs[verdict.motif] = motifs.get(verdict.motif, 0) + 1
        if verdict.admise:
            admises += 1
            if verdict.ttc is not None:
                total += verdict.ttc
    return verdicts, BilanAdmission(
        lues=len(pieces),
        admises=admises,
        refusees=len(pieces) - admises,
        total_admis=total,
        par_motif=tuple(sorted(motifs.items())),
    )
