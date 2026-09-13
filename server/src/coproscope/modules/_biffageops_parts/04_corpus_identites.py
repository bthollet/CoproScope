from __future__ import annotations

from dataclasses import dataclass

from ..core.colonnes_nominatives import noms_en_colonne


"""Detection des identites dans un texte, et rien d'autre.

Regle du lot: on ne remplace que des identites. Le vocabulaire juridique, les
montants, les dates, les numeros d'article et les raisons sociales doivent
survivre au caviardage, sinon le derive n'est plus analysable. L'incident du
2026-09-03 - environ 5 400 etiquettes sur 6 099, dont `Article 24`, `Article 25`
et `Vote` - est exactement ce que ce module refuse de refaire.
"""


_MAJ = "A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸÆŒ"
_MIN = "a-zàâäçéèêëîïôöùûüÿæœ"

CIVILITES = r"(?:M\.|MM\.|Mr\.?|Mme\.?|Mmes\.?|Mlle\.?|Monsieur|Madame|Mesdames|Messieurs|Mademoiselle|Me\.?|Ma[iî]tre|Dr\.?|Docteur)"

# Mots qui ne sont jamais un nom de personne. Normalises sans accent, en
# majuscules, comme `normalize_identity_key`.
_VOCABULAIRE_PROTEGE = """
PERSONNE PERSONNES EMAIL TELEPHONE IBAN SECRET ALIAS PSEUDONYME
M MM MR MME MMES MLLE MONSIEUR MADAME MESDAMES MESSIEURS MADEMOISELLE ME
MAITRE DR DOCTEUR VEUVE VVE HERITIERS INDIVISION CONSORTS SUCCESSION
ARTICLE ARTICLES ALINEA RESOLUTION RESOLUTIONS QUESTION QUESTIONS POINT POINTS
VOTE VOTES VOTANT VOTANTS VOTANTES VOIX MAJORITE MAJORITES UNANIMITE QUORUM
POUR CONTRE ABSTENTION ABSTENTIONS ADOPTEE ADOPTE REJETEE REJETE AJOURNEE
ASSEMBLEE ASSEMBLEES GENERALE GENERALES ORDINAIRE EXTRAORDINAIRE ORDRE JOUR
PROCES VERBAL PV CONVOCATION CONVOCATIONS FEUILLE PRESENCE EMARGEMENT
COPROPRIETE COPROPRIETES COPROPRIETAIRE COPROPRIETAIRES SYNDIC SYNDICAT
CONSEIL SYNDICAL PRESIDENT PRESIDENTE SECRETAIRE SCRUTATEUR SCRUTATEURS
MANDATAIRE MANDATAIRES POUVOIR POUVOIRS DELEGATION DELEGATIONS
TANTIEMES MILLIEMES QUOTEPART QUOTESPARTS REPARTITION CLE CLES
CHARGES CHARGE BUDGET BUDGETS PREVISIONNEL EXERCICE EXERCICES ANNEXE ANNEXES
COMPTE COMPTES COMPTABLE COMPTABILITE BILAN BALANCE GRAND LIVRE JOURNAL
TOTAL TOTAUX SOUSTOTAL SOLDE SOLDES DEBIT DEBITS CREDIT CREDITS MONTANT
MONTANTS SOMME SOMMES REPORT REPORTS AVOIR AVOIRS
FONDS TRAVAUX PROVISION PROVISIONS APPEL APPELS AVANCE AVANCES TRESORERIE
IMPAYE IMPAYES RECOUVREMENT CONTENTIEUX DEBITEUR DEBITEURS CREANCIER
FACTURE FACTURES DEVIS CONTRAT CONTRATS MANDAT HONORAIRES PRESTATION
ASSURANCE ASSURANCES ENTRETIEN MAINTENANCE ASCENSEUR ASCENSEURS CHAUFFAGE
EAU EAUX ELECTRICITE GAZ NETTOYAGE GARDIENNAGE ESPACES VERTS RAMONAGE
DIAGNOSTIC DIAGNOSTICS AMIANTE PLOMB TERMITES ENERGIE DPE CARNET
LOT LOTS BATIMENT BATIMENTS ETAGE ETAGES ESCALIER CAVE CAVES PARKING GARAGE
IMMEUBLE IMMEUBLES RESIDENCE ADRESSE RUE AVENUE BOULEVARD PLACE CHEMIN
ALLEE IMPASSE ROUTE VILLE CODE POSTAL
LOI DECRET ARRETE CIVIL COMMERCE CONSTRUCTION HABITATION JURISPRUDENCE
TRIBUNAL COUR APPEL CASSATION AVOCAT HUISSIER COMMISSAIRE JUSTICE
ETAT ETATS SITUATION DEPENSE DEPENSES RECETTE RECETTES PRODUIT PRODUITS
CHARGE REDDITION RAPPORT RAPPORTS NOTE NOTES LISTE LISTES TABLEAU TABLEAUX
PERIODE PERIODES DATE DATES DUREE PAGE PAGES SUITE FIN DEBUT OBJET
EURO EUROS EUR TVA HT TTC HTVA REMISE ACOMPTE
JANVIER FEVRIER MARS AVRIL MAI JUIN JUILLET AOUT SEPTEMBRE OCTOBRE NOVEMBRE
DECEMBRE LUNDI MARDI MERCREDI JEUDI VENDREDI SAMEDI DIMANCHE
PRESENT PRESENTS PRESENTE PRESENTES ABSENT ABSENTS REPRESENTE REPRESENTES
OUI NON AUCUN AUCUNE TOUS TOUTES CHAQUE MEME MEMES AUTRE AUTRES
LE LA LES UN UNE DES DU DE DA AU AUX ET OU OUX EN PAR POUR SUR SOUS AVEC SANS
DANS CE CET CETTE CES SON SA SES LEUR LEURS NOTRE NOS VOTRE VOS IL ELLE ILS
ELLES NOUS VOUS QUI QUE QUOI DONT SI NE PAS PLUS MOINS TRES BIEN
SARL SAS SASU SA SCI SCP SCPI SNC EURL SELARL SCCV GIE CABINET SOCIETE
SOCIETES ENTREPRISE ENTREPRISES ETABLISSEMENT ETABLISSEMENTS ETS GROUPE
ASSOCIATION AGENCE COMPAGNIE MUTUELLE BANQUE ASSUREUR IMMOBILIER IMMOBILIERE
GESTION ADMINISTRATION FONCIER FONCIERE SERVICES SERVICE CONSEILS EXPERT
EXPERTISE BUREAU BUREAUX
"""

VOCABULAIRE_PROTEGE = frozenset(_VOCABULAIRE_PROTEGE.split())

# Particules de nom. Elles figurent aussi dans le vocabulaire protege, parce
# qu'isolees ce sont des mots vides; mais `DE VERNAZOUX`, `EL ORFA` ou
# `DA SILVA` sont des noms. Sans cette liste, un patronyme a particule est
# rejete en bloc - c'etait la cause des 11 lignes ratees de l'annexe des soldes.
PARTICULES = frozenset(
    """DE DU DES DA DI DO DAS DOS D L LE LA LES EL AL VAN VON VAN DEN DER TER
    TEN BEN BIN MAC MC O SAINT SAINTE ST STE Y I""".split()
)

# Marqueurs de personne morale: si le candidat en contient un, on preserve.
MARQUEURS_PERSONNE_MORALE = frozenset(
    """SARL SAS SASU SA SCI SCP SCPI SNC EURL SELARL SCCV GIE CABINET SOCIETE
    ENTREPRISE ETABLISSEMENT ETABLISSEMENTS ETS GROUPE ASSOCIATION AGENCE
    COMPAGNIE MUTUELLE BANQUE ASSUREUR SYNDIC IMMOBILIER IMMOBILIERE""".split()
)

# Garde de sortie: une valeur qui ressemble a ceci n'est jamais remplacee,
# quelle que soit la regle qui l'a proposee.
GARDE_VOCABULAIRE = re.compile(
    r"^(?:"
    r"\d[\d\s.,' -]*"          # nombres, montants, dates numeriques
    r"|(?:article|articles|alinea|resolution|resolutions|vote|votes|majorite"
    r"|loi|decret|arrete|annexe|lot|batiment|page|compte)\b.*"
    r")$",
    flags=re.IGNORECASE,
)

_MOTIF_CIVILITE = re.compile(
    rf"(?<![{_MAJ}{_MIN}]){CIVILITES}\s+"
    rf"((?:[{_MAJ}][{_MAJ}'’\-]+|[{_MAJ}][{_MIN}'’\-]+)"
    rf"(?:[ \-][{_MAJ}][{_MAJ}{_MIN}'’\-]+){{0,3}})",
)

# Nom et prenom se lisent sur une meme ligne. Un saut de ligne separe deux
# entrees d'une liste, pas un prenom de son nom: `\s+` apparierait la derniere
# ligne d'un bloc avec la premiere du suivant.
_ESPACE = r"[   \t]+"

_MOTIF_NOM_PRENOM = re.compile(
    rf"\b([{_MAJ}]{{2,}}(?:[ \-'’][{_MAJ}]{{2,}}){{0,2}}){_ESPACE}([{_MAJ}][{_MIN}]{{1,}}(?:[ \-][{_MAJ}][{_MIN}]+)?)\b"
)

_MOTIF_PRENOM_NOM = re.compile(
    rf"\b([{_MAJ}][{_MIN}]{{1,}}){_ESPACE}([{_MAJ}]{{2,}}(?:[ \-'’][{_MAJ}]{{2,}}){{0,2}})\b"
)

# Ligne de type annexe des soldes: un nom en tete de ligne, un montant ensuite.
_MOTIF_LIGNE_MONTANT = re.compile(
    rf"^[\s|]*([{_MAJ}][{_MAJ}{_MIN}'’\-]+(?:[ \-'’][{_MAJ}][{_MAJ}{_MIN}'’\-]+){{0,3}})"
    r"[\s|]{2,}.*?[-−(]?\d{1,3}(?:[\s  .]\d{3})*[,.]\d{2}",
)

# Liste nominative tabulaire: un identifiant de compte sur une ligne, le nom
# du coproprietaire sur la suivante, les montants apres. C'est la forme de
# l'annexe des soldes - 146 lignes chez un cabinet - ou aucun nom ne porte de
# civilite. Sans cette regle structurelle, pas un seul de ces noms n'est vu.
_MOTIF_COMPTE_NU = re.compile(r"^\s*\d{5,}\s*$")
_MOTIF_MONTANT_NU = re.compile(
    r"^\s*[-−(]?\d{1,3}(?:[\s  .]\d{3})*[,.]\d{2}\s*\)?\s*€?\s*$"
)
_MOTIF_LIGNE_MAJUSCULES = re.compile(
    rf"^\s*([{_MAJ}][{_MAJ}'’]*(?:[ \-'’]+[{_MAJ}][{_MAJ}'’]*){{0,5}})\s*$"
)

_MOTIF_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_MOTIF_TELEPHONE = re.compile(
    r"(?<!\d)(?:\+33|0)[1-9](?:[ .  \-]?\d{2}){4}(?!\d)"
)
_MOTIF_IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:[  \-]?[A-Z0-9]){11,30}\b")
_MOTIF_SECRET = re.compile(
    r"\b(?:mot de passe|password|code portail|code badge|code vigik|vigik|cl[eé] d'acc[eè]s)\s*[:=]\s*([A-Za-z0-9#*@._\-]{3,40})",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class IdentiteCandidate:
    categorie: str
    valeur: str
    nom: str = ""
    prenom: str = ""
    motif: str = ""


def _tokens_proteges(value: str) -> bool:
    tokens = [normalize_identity_key(token) for token in re.split(r"[\s\-'’]+", value) if token]
    tokens = [token for token in tokens if token]
    if not tokens:
        return True
    if all(token in VOCABULAIRE_PROTEGE for token in tokens):
        return True
    if any(token in MARQUEURS_PERSONNE_MORALE for token in tokens):
        return True
    return False


def _nom_recevable(value: str) -> bool:
    value = value.strip(" \t|-–—:;,.")
    if len(value) < 3:
        return False
    # Un pseudonyme deja pose n'est pas un nom a caviarder une seconde fois.
    if "_" in value or ALIAS_PATTERN.search(value):
        return False
    if GARDE_VOCABULAIRE.match(value.strip()):
        return False
    if any(char.isdigit() for char in value):
        return False
    if _tokens_proteges(value):
        return False
    tokens = [normalize_identity_key(token) for token in re.split(r"[\s\-'’]+", value)]
    tokens = [token for token in tokens if token]
    if not tokens:
        return False
    # Les particules ne comptent pas: `DE VERNAZOUX` est un nom, `DE CHARGES`
    # n'en est pas un. On juge donc sur les tokens qui restent.
    porteurs = [token for token in tokens if token not in PARTICULES]
    if not porteurs or not any(len(token) >= 3 for token in porteurs):
        return False
    # Un token protege parmi les porteurs suffit a disqualifier le candidat:
    # `Article Un` ou `TOTAL General` ne sont pas des personnes.
    if any(token in VOCABULAIRE_PROTEGE for token in porteurs):
        return False
    return True


def _nom_en_tete(tokens: list[str]) -> tuple[str, str]:
    """Le nom de famille est en tete, particules et trait d'union compris."""

    pris: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        cle = normalize_identity_key(token)
        pris.append(token)
        index += 1
        if not cle:
            # Un separateur seul, comme `-`: le nom continue apres.
            continue
        if cle in PARTICULES:
            continue
        suivant = tokens[index] if index < len(tokens) else ""
        if suivant and not normalize_identity_key(suivant):
            continue
        break
    if index >= len(tokens):
        return " ".join(pris), ""
    return " ".join(pris), " ".join(tokens[index:])


def _decoupe_nom(value: str) -> tuple[str, str]:
    """Separe nom de famille et prenoms dans un candidat deja recevable."""

    tokens = [token for token in re.split(r"\s+", value.strip()) if token]
    if not tokens:
        return "", ""
    # Un separateur (`-`) ou une initiale ne pesent pas dans la decision: seuls
    # les mots d'au moins deux lettres disent si le candidat est mixte.
    mots = [token for token in tokens if len(re.sub(r"[^A-Za-zÀ-ÿ]", "", token)) >= 2]
    majuscules = [token for token in mots if strip_accents(token).isupper()]
    minuscules = [token for token in mots if token not in majuscules]
    if majuscules and minuscules:
        nom = " ".join(majuscules)
        prenom = " ".join(token for token in tokens if token not in majuscules)
        return nom, prenom
    if majuscules and len(tokens) > 1:
        # Tout en majuscules: convention administrative francaise, le nom de
        # famille est en tete. `BERTOZI JEAN MARC` donne BERTOZI + JEAN MARC.
        # Le nom emporte ses particules et son trait d'union: sans cela,
        # `DE VERNAZOUX MARIE` donnerait le nom `DE`, et aucune variante de
        # cette personne ne serait plus retrouvable ailleurs.
        return _nom_en_tete(tokens)
    if len(tokens) == 1:
        return tokens[0], ""
    return tokens[-1], " ".join(tokens[:-1])


def _ajoute(candidats: dict[str, IdentiteCandidate], candidat: IdentiteCandidate) -> None:
    existant = candidats.get(candidat.valeur)
    if existant is None or (not existant.prenom and candidat.prenom):
        candidats[candidat.valeur] = candidat


def _masque_alias(text: str) -> str:
    """Neutralise les pseudonymes deja poses, sans decaler les positions.

    Sans ce masque, `M.PERSONNE_MELISSE` fait lire `PERSONNE` comme un nom de
    personne apres une civilite, et l'alias se replie sur lui-meme.
    """

    return ALIAS_PATTERN.sub(lambda match: "·" * len(match.group(0)), text)


def detecte_identites(text: str) -> list[IdentiteCandidate]:
    """Toutes les identites du texte, et seulement les identites."""

    text = _masque_alias(text)
    candidats: dict[str, IdentiteCandidate] = {}

    for match in _MOTIF_EMAIL.finditer(text):
        _ajoute(candidats, IdentiteCandidate("EMAIL", match.group(0), motif="email"))
    for match in _MOTIF_TELEPHONE.finditer(text):
        _ajoute(candidats, IdentiteCandidate("TELEPHONE", match.group(0), motif="telephone"))
    for match in _MOTIF_IBAN.finditer(text):
        _ajoute(candidats, IdentiteCandidate("IBAN", match.group(0).strip(), motif="iban"))
    for match in _MOTIF_SECRET.finditer(text):
        _ajoute(candidats, IdentiteCandidate("SECRET", match.group(1), motif="secret"))

    def _personne(valeur: str, motif: str) -> None:
        valeur = valeur.strip(" \t|-–—:;,.")
        if not _nom_recevable(valeur):
            return
        nom, prenom = _decoupe_nom(valeur)
        if not normalize_identity_key(nom):
            return
        _ajoute(candidats, IdentiteCandidate("PERSONNE", valeur, nom, prenom, motif))

    for match in _MOTIF_CIVILITE.finditer(text):
        _personne(match.group(1), "civilite")
    for match in _MOTIF_NOM_PRENOM.finditer(text):
        _personne(f"{match.group(1)} {match.group(2)}", "nom_prenom")
    for match in _MOTIF_PRENOM_NOM.finditer(text):
        _personne(f"{match.group(1)} {match.group(2)}", "prenom_nom")
    for ligne in text.splitlines():
        match = _MOTIF_LIGNE_MONTANT.match(ligne)
        if match:
            _personne(match.group(1), "ligne_montant")
    for valeur in _lignes_liste_nominative(text):
        _personne(valeur, "liste_nominative")
    # `liste_nominative` ci-dessus ne reconnait qu'UN rendu de tableau, celui
    # d'un cabinet. `colonne_nominative` juge sur la repetition et couvre les
    # autres rendus du meme tableau. Les deux coexistent: la premiere accepte un
    # rang isole, la seconde exige une colonne. Voir `core/colonnes_nominatives`.
    for valeur in noms_en_colonne(text, _nom_recevable):
        _personne(valeur, "colonne_nominative")

    personnes = [item for item in candidats.values() if item.categorie == "PERSONNE"]
    for nom_nu in _noms_nus(text, personnes):
        _ajoute(candidats, nom_nu)
    return list(candidats.values())


def _lignes_liste_nominative(text: str) -> list[str]:
    """Les noms d'une liste tabulaire, la ou aucune civilite ne les annonce.

    On n'accepte une ligne tout en majuscules comme nom que si elle est ancree:
    un numero de compte juste avant, un montant juste apres. Sans cet ancrage,
    `EAU ARROSAGE` d'un etat des depenses passerait pour une personne, et le
    derive perdrait le vocabulaire comptable qu'il doit garder.
    """

    lignes = text.splitlines()
    utiles = [(index, ligne) for index, ligne in enumerate(lignes) if ligne.strip()]
    trouves: list[str] = []
    for position, (_, ligne) in enumerate(utiles):
        match = _MOTIF_LIGNE_MAJUSCULES.match(ligne)
        if not match:
            continue
        precedente = utiles[position - 1][1] if position else ""
        suivante = utiles[position + 1][1] if position + 1 < len(utiles) else ""
        if not _MOTIF_COMPTE_NU.match(precedente):
            continue
        if not _MOTIF_MONTANT_NU.match(suivante):
            continue
        trouves.append(match.group(1).strip())
    return trouves


#: Motifs qui n'etablissent rien sur le mot lui-meme: ils ne constatent qu'une
#: REPETITION DE FORME. `_noms_nus` demande explicitement l'inverse - un nom
#: `vu accompagne ailleurs` - et ce qu'il fait d'un nom depasse de loin la
#: detection: il masque CHAQUE occurrence isolee du patronyme dans tout le
#: document. Une detection de forme seule qui l'alimente transforme donc une
#: hypothese non corroboree en remplacement generalise, ce qui est le mecanisme
#: exact de l'incident du 2026-09-03 - 5 400 etiquettes sur 6 099.
#: Mesure du 2026-09-09 sur la convocation de 143 pages, rendue par l'extracteur
#: de premier choix du depot: `colonne_nominative` y ajoute 12 valeurs, et
#: `_noms_nus` en fabrique 5 de plus a partir d'elles - 17 au total la ou la
#: base 913d744 en ajoutait 0.
MOTIFS_SANS_APPUI_LEXICAL = frozenset({"colonne_nominative"})


def _noms_nus(text: str, personnes: list[IdentiteCandidate]) -> list[IdentiteCandidate]:
    """Le nom de famille seul, une fois qu'on l'a vu accompagne ailleurs.

    `Mme DUPONT` etablit que `DUPONT` est un nom; les occurrences isolees de
    `DUPONT` dans le meme document doivent tomber aussi, sinon le caviardage
    laisse le nom en clair a la ligne suivante.

    **`accompagne ailleurs` est la condition, pas une figure de style.** Un
    motif de `MOTIFS_SANS_APPUI_LEXICAL` n'a jamais vu le mot accompagne: il a
    vu une forme se repeter. Il n'ouvre donc pas ce droit-la.
    """

    trouves: list[IdentiteCandidate] = []
    vus: set[str] = set()
    for personne in personnes:
        if personne.motif in MOTIFS_SANS_APPUI_LEXICAL:
            continue
        for token in re.split(r"[\s\-'’]+", personne.nom):
            token = token.strip()
            # **LE SEUIL DE LONGUEUR A ETE RETIRE, et la mesure l'exigeait.**
            # `RM-2026-0097`: *l'invariant se teste sur le voisinage [...] pas
            # en allongeant une liste de mots ni en abaissant un seuil de
            # longueur*. Ce `len(token) < 4` etait exactement ce seuil.
            #
            # **Ce qu'il faisait, mesure le 2026-09-11.** Un patronyme de moins
            # de quatre lettres, **pourtant etabli par une civilite**, ne
            # voyait PAS ses occurrences isolees caviardees: `Mme KIM Sophie`
            # etablissait `KIM`, et `KIM` restait en clair a la ligne suivante -
            # exactement ce que la docstring de cette fonction dit vouloir
            # empecher. Verifie sur cinq noms: `VANDERSTOCKE` (12) et `DUPONT`
            # (6) tombent, `KIM` (3), `NGO` (3) et `LI` (2) ne tombent pas.
            #
            # **Et le seuil etait REDONDANT avec le lexique.** Mesure des mots
            # courts que l'on craignait de masquer: `RUE`, `TVA`, `LOT`, `EUR`,
            # `TTC`, `HT` sont **deja refuses par `_nom_recevable`**, qui
            # impose par ailleurs trois caracteres - donc `LI` et `WU` restent
            # exclus sans lui. Ce que le seuil excluait EN PLUS du lexique
            # n'etait donc que des patronymes recevables: `KIM`, `NGO`, `BUI`,
            # `DUC`. **Une garde qui ne retire plus que des vrais noms ne
            # protege plus rien; elle laisse fuir.**
            #
            # **Le residu, et il est etroit.** `BIS` passe le lexique. Il ne
            # sera caviarde que si une civilite l'a etabli comme nom - `Mme
            # BIS` - ce que `_noms_nus` exige avant tout. Le risque existe et
            # il est nomme; le laisser fuir des patronymes courants coutait
            # plus cher.
            if not _nom_recevable(token):
                continue
            cle = normalize_identity_key(token)
            if cle in vus:
                continue
            vus.add(cle)
            motif = re.compile(rf"(?<![{_MAJ}{_MIN}_]){re.escape(token)}(?![{_MAJ}{_MIN}_])")
            if motif.search(text):
                trouves.append(IdentiteCandidate("PERSONNE", token, token, "", "nom_nu"))
    return trouves


def applique_alias(text: str, remplacements: dict[str, str]) -> tuple[str, dict[str, int]]:
    """Remplace les identites par leurs alias, sans toucher au reste.

    Les valeurs les plus longues passent d'abord: `DUPONT Jean` avant `DUPONT`.
    Les bornes de mot evitent de mordre sur `DUPONTEL`.
    """

    compteurs: dict[str, int] = {}
    redige = text
    ordre = sorted(remplacements.items(), key=lambda item: len(item[0]), reverse=True)
    for original, alias in ordre:
        if not original:
            continue
        # Derniere garde, la ou l'incident du 2026-09-03 a eu lieu: un alias de
        # personne ne recouvre jamais un montant, une date ou un mot du
        # vocabulaire juridique. Les autres categories (email, telephone, IBAN)
        # sont numeriques par nature et ne passent pas par cette garde.
        if alias.startswith("PERSONNE_") and GARDE_VOCABULAIRE.match(original.strip()):
            continue
        motif = re.compile(
            rf"(?<![{_MAJ}{_MIN}0-9_]){re.escape(original)}(?![{_MAJ}{_MIN}0-9_])"
        )
        redige, nombre = motif.subn(alias, redige)
        if nombre:
            compteurs[original] = nombre
    return redige, compteurs
