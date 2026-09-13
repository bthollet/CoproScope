"""Nomenclature comptable reglementaire du syndicat, et sa reconnaissance.

AXE DE GENERALISATION - a lire avant de toucher a ce fichier.

Ce qui est reglementaire, c'est le NUMERO de compte: l'arrete du 14 mars 2005
fixe la liste, et son article 8 dit que ces comptes "sont les seuls utilisables"
tout en autorisant "toute subdivision necessaire" quand ils ne suffisent pas.

Ce qui varie, c'est tout le reste, et c'est mesure sur deux cabinets:

- le libelle. Le compte 613 est "Locations mobilieres" au texte, "Locations
  compteurs" chez un cabinet. Coder les libelles, c'est coder un cabinet.
- le remplissage. Un cabinet ecrit `450-1`, l'autre `4501`; `501` devient
  `5010`, `12-1` devient `1210`. Le meme compte, quatre ecritures.
- l'agregation. Un cabinet detaille ligne par ligne, l'autre publie `60x`,
  `62... (autres que 621 et 622)`, `671-673`. Ce ne sont pas des comptes: ce
  sont des regroupements de presentation.

La reconnaissance se fonde donc sur le numero normalise, puis, s'il est inconnu,
sur le rattachement par prefixe - qui est la subdivision licite de l'article 8.
Un numero n'est signale que s'il ne se rattache a rien.
"""

from __future__ import annotations

import re

# Liste de l'article 7 de l'arrete du 14 mars 2005 (LEGIARTI000042413155,
# version du 2020-12-31). Le libelle n'est conserve que pour la lisibilite d'un
# rapport: aucun controle ne s'y appuie.
COMPTES: dict[str, str] = {
    "102": "Provisions pour travaux decides",
    "103": "Avances",
    "1031": "Avances de tresorerie",
    "1033": "Autres avances",
    "105": "Fonds de travaux",
    "106": "Provisions pour travaux au titre de la delegation au conseil syndical",
    "12": "Solde en attente sur travaux et operations exceptionnelles",
    "12-1": "Travaux decides par l'assemblee generale",
    "12-2": "Travaux delegues au conseil syndical",
    "13": "Subventions",
    "131": "Subventions accordees en instance de versement",
    "40": "Fournisseurs",
    "401": "Factures parvenues",
    "408": "Factures non parvenues",
    "409": "Fournisseurs debiteurs",
    "42": "Personnel",
    "421": "Remunerations dues",
    "43": "Securite sociale et autres organismes sociaux",
    "431": "Securite sociale",
    "432": "Autres organismes sociaux",
    "44": "Etat et collectivites territoriales",
    "441": "Etat et autres organismes - subventions a recevoir",
    "442": "Etat - impots et versements assimiles",
    "443": "Collectivites territoriales - aides",
    "45": "Collectivite des coproprietaires",
    "450": "Coproprietaire individualise",
    "450-1": "Coproprietaire - budget previsionnel",
    "450-2": "Coproprietaire - travaux article 14-2 et operations exceptionnelles",
    "450-3": "Coproprietaire - avances",
    "450-4": "Coproprietaire - emprunts",
    "450-5": "Coproprietaire - fonds de travaux",
    "459": "Coproprietaire - creances douteuses",
    "46": "Debiteurs et crediteurs divers",
    "461": "Debiteurs divers",
    "462": "Crediteurs divers",
    "47": "Compte d'attente",
    "471": "Compte en attente d'imputation debiteur",
    "472": "Compte en attente d'imputation crediteur",
    "48": "Compte de regularisation",
    "486": "Charges payees d'avance",
    "487": "Produits encaisses d'avance",
    "49": "Depreciation des comptes de tiers",
    "491": "Coproprietaires",
    "492": "Personnes autres que les coproprietaires",
    "50": "Fonds places",
    "501": "Compte a terme",
    "502": "Autre compte",
    "51": "Banques",
    "512": "Banques",
    "514": "Cheques postaux",
    "53": "Caisse",
    "60": "Achats de matieres et fournitures",
    "601": "Eau",
    "602": "Electricite",
    "603": "Chauffage, energie et combustibles",
    "604": "Achats produits d'entretien et petits equipements",
    "605": "Materiel",
    "606": "Fournitures",
    "61": "Services exterieurs",
    "611": "Nettoyage des locaux",
    "612": "Locations immobilieres",
    "613": "Locations mobilieres",
    "614": "Contrats de maintenance",
    "615": "Entretien et petites reparations",
    "616": "Primes d'assurances",
    "62": "Frais d'administration et honoraires",
    "621": "Remunerations du syndic sur gestion copropriete",
    "6211": "Remuneration du syndic",
    "6212": "Debours",
    "6213": "Frais postaux",
    "622": "Autres honoraires du syndic",
    "6221": "Honoraires travaux",
    "6222": "Prestations particulieres",
    "6223": "Autres honoraires",
    "623": "Remunerations de tiers intervenants",
    "624": "Frais du conseil syndical",
    "63": "Impots, taxes et versements assimiles",
    "632": "Taxe de balayage",
    "633": "Taxe fonciere",
    "634": "Autres impots et taxes",
    "64": "Frais de personnel",
    "641": "Salaires",
    "642": "Charges sociales et organismes sociaux",
    "643": "Taxe sur les salaires",
    "644": "Autres frais de personnel",
    "65": "Montant alloue au conseil syndical au sein du budget previsionnel",
    "66": "Charges financieres des emprunts, agios ou autres",
    "661": "Remboursement d'annuites d'emprunt",
    "662": "Autres charges financieres et agios",
    "67": "Charges pour travaux et operations exceptionnelles",
    "671": "Travaux decides par l'assemblee generale",
    "672": "Travaux urgents",
    "673": "Etudes techniques, diagnostic, consultation",
    "674": "Travaux delegues au conseil syndical",
    "677": "Pertes sur creances irrecouvrables",
    "678": "Charges exceptionnelles",
    "68": "Dotations aux depreciations sur creances douteuses",
    "70": "Appels de fonds",
    "701": "Provisions sur operations courantes",
    "702": "Provisions sur travaux du I de l'article 14-2 et operations exceptionnelles",
    "703": "Avances",
    "704": "Remboursements d'annuites d'emprunts",
    "705": "Affectation du fonds de travaux",
    "706": "Provisions au titre de la delegation au conseil syndical",
    "706-1": "Provisions sur operations courantes",
    "706-2": "Provisions sur travaux et operations exceptionnelles",
    "71": "Autres produits",
    "711": "Subventions",
    "712": "Emprunts",
    "713": "Indemnites d'assurances",
    "714": "Produits divers",
    "716": "Produits financiers",
    "718": "Produits exceptionnels",
    "78": "Reprises de depreciations sur creances douteuses",
}

# Le compte 1032 figurait dans la nomenclature; la version en vigueur porte
# "1032 (Supprime)". Un cabinet mesure l'utilise encore. Le rattachement par
# prefixe le rendrait invisible: il faut donc une liste explicite.
COMPTES_SUPPRIMES: dict[str, str] = {
    "1032": "Avances - compte supprime de la nomenclature en vigueur",
}

# Charges qui ne peuvent pas figurer au budget previsionnel: la classe 67 porte
# les travaux de l'article 14-2 et les operations exceptionnelles, la classe 68
# les dotations aux depreciations. Voir la grille, controle B-1.
PREFIXES_CHARGES_HORS_BUDGET: tuple[str, ...] = ("67", "68")

# La classe 66 n'est pas tranchee. Les deux cabinets mesures la rangent
# differemment dans l'annexe 2: l'un porte 662 en operations courantes, l'autre
# porte 661 et 662 avec les travaux. Le modele d'annexe 2 qui trancherait n'est
# pas reproduit sur Legifrance. On ne decide donc pas a la place du texte.
PREFIXES_CHARGES_INDETERMINEES: tuple[str, ...] = ("66",)

PREFIXES_CHARGES_COURANTES: tuple[str, ...] = ("60", "61", "62", "63", "64", "65")

_SEPARATEURS = re.compile(r"[\s.…]+")
_JOKER = re.compile(r"(?:x+|…|\.{2,})$", re.IGNORECASE)


def _candidats(numero: str) -> list[str]:
    """Ecritures possibles d'un meme numero, de la plus fidele a la plus laxiste."""
    vus: list[str] = []

    def ajouter(valeur: str) -> None:
        if valeur and valeur not in vus:
            vus.append(valeur)

    ajouter(numero)
    sans_tiret = numero.replace("-", "")
    ajouter(sans_tiret)
    # `4501` peut etre `450-1`, `1210` peut etre `121` puis `12-1`.
    if len(sans_tiret) >= 3:
        ajouter(f"{sans_tiret[:-1]}-{sans_tiret[-1]}")
    if len(sans_tiret) >= 3 and sans_tiret.endswith("0"):
        court = sans_tiret[:-1]
        ajouter(court)
        if len(court) >= 3:
            ajouter(f"{court[:-1]}-{court[-1]}")
    return vus


def normaliser(brut: str | None) -> str | None:
    """Rend le numero de compte reglementaire, ou None si rien ne s'y rattache.

    Ne regarde jamais le libelle. Un intitule de cabinet n'est pas une preuve
    d'imputation.
    """
    if not brut:
        return None
    tete = _SEPARATEURS.split(brut.strip())[0]
    tete = _JOKER.sub("", tete)
    # `671-673` est un regroupement de presentation: on retient sa borne basse,
    # qui est un compte reel, et le controle de perimetre reste juste.
    tete = tete.split("-")[0] if re.fullmatch(r"\d+-\d{2,}", tete) else tete
    tete = re.sub(r"[^0-9-]", "", tete)
    if not tete or not re.match(r"\d", tete):
        return None
    for candidat in _candidats(tete):
        if candidat in COMPTES or candidat in COMPTES_SUPPRIMES:
            return candidat
    return rattacher(tete)


def rattacher(numero: str) -> str | None:
    """Plus long compte reglementaire dont `numero` serait une subdivision.

    L'article 8 de l'arrete autorise "toute subdivision necessaire": un numero
    inconnu est d'abord une subdivision licite, pas une anomalie.
    """
    chiffres = numero.replace("-", "")
    for taille in range(len(chiffres) - 1, 1, -1):
        prefixe = chiffres[:taille]
        if prefixe in COMPTES:
            return prefixe
    return None


def est_supprime(compte: str | None) -> bool:
    return bool(compte) and compte in COMPTES_SUPPRIMES


def _a_prefixe(compte: str, prefixes: tuple[str, ...]) -> bool:
    return any(compte.startswith(prefixe) for prefixe in prefixes)


def hors_budget_previsionnel(compte: str | None) -> bool:
    return bool(compte) and _a_prefixe(compte, PREFIXES_CHARGES_HORS_BUDGET)


def indetermine_au_budget(compte: str | None) -> bool:
    return bool(compte) and _a_prefixe(compte, PREFIXES_CHARGES_INDETERMINEES)


def charge_courante(compte: str | None) -> bool:
    return bool(compte) and _a_prefixe(compte, PREFIXES_CHARGES_COURANTES)


def libelle(compte: str | None) -> str:
    if not compte:
        return ""
    return COMPTES.get(compte) or COMPTES_SUPPRIMES.get(compte, "")
