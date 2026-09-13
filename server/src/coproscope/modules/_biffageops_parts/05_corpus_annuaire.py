from __future__ import annotations


"""L'annuaire des personnes, et l'appariement de ses variantes.

Reconnaitre un patronyme dans un texte au hasard est mal pose: `M. Dupont`,
`Monsieur Dupont`, `DUPONT Jean` et `Jean Dupont` sont la meme personne, et rien
dans la forme ne dit qu'un mot en majuscules est un nom.

La piece qui porte le plus de risque retourne le probleme. L'annexe des soldes
est un annuaire: une colonne propre, un numero de compte, un nom, un prenom, un
solde. Une fois cette liste extraite, la question devient "retrouver dans un
texte les variantes de N chaines connues" - tractable, et surtout mesurable.
"""


ANNUAIRE_FIELDS = [
    "personne_id",
    "alias",
    "racine",
    "nom_normalise",
    "prenom_normalise",
    "nom_source",
    "prenom_source",
    "compte",
    "source_doc_id",
    "premiere_vue",
]


def annuaire_path(instance: InstanceConfig) -> Path:
    """L'annuaire vit en C8, a cote de la table de correspondance."""

    path = _redaction_map_path(instance).with_name("annuaire_personnes.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _fold_preserving(text: str) -> str:
    """Enleve les accents sans changer les positions de caracteres.

    Necessaire: on cherche sur le texte replie, on remplace sur l'original.
    Une longueur qui change decalerait tous les index.
    """

    sortie: list[str] = []
    for char in text:
        decomposed = unicodedata.normalize("NFKD", char)
        base = next((item for item in decomposed if not unicodedata.combining(item)), char)
        sortie.append(base if len(base) == 1 else char)
    return "".join(sortie)


class RegistrePseudonymes:
    """Attribue et conserve les pseudonymes lisibles d'une instance."""

    def __init__(self, instance: InstanceConfig, salt: bytes) -> None:
        self.instance = instance
        self.salt = salt
        self.path = annuaire_path(instance)
        fields, rows = read_csv(self.path)
        self.fields = list(ANNUAIRE_FIELDS)
        for field in fields:
            if field not in self.fields:
                self.fields.append(field)
        self.rows = rows
        self.dirty = False
        self._par_cle: dict[tuple[str, str], dict[str, str]] = {}
        self._racine_par_nom: dict[str, str] = {}
        self._racines_prises: dict[str, str] = {}
        self._couleurs_prises: dict[tuple[str, str], str] = {}
        for row in rows:
            nom = row.get("nom_normalise", "")
            prenom = row.get("prenom_normalise", "")
            racine = row.get("racine", "")
            self._par_cle[(nom, prenom)] = row
            if racine:
                self._racine_par_nom.setdefault(nom, racine)
                self._racines_prises.setdefault(racine, nom)
                alias = row.get("alias", "")
                if alias.count("_") >= 2:
                    couleur = alias.rsplit("_", 1)[1]
                    self._couleurs_prises.setdefault((racine, couleur), prenom)

    def _racine_pour(self, nom_key: str) -> str:
        existante = self._racine_par_nom.get(nom_key)
        if existante:
            return existante
        for candidat in racine_candidats(self.salt, nom_key):
            proprietaire = self._racines_prises.get(candidat)
            if proprietaire is None or proprietaire == nom_key:
                self._racines_prises[candidat] = nom_key
                self._racine_par_nom[nom_key] = candidat
                return candidat
        raise RuntimeError(
            "Espace de pseudonymes epuise pour cette instance: elargir ARBRES."
        )

    def _couleur_pour(self, racine: str, nom_key: str, prenom_key: str) -> str:
        for candidat in prenom_candidats(self.salt, nom_key, prenom_key):
            proprietaire = self._couleurs_prises.get((racine, candidat))
            if proprietaire is None or proprietaire == prenom_key:
                self._couleurs_prises[(racine, candidat)] = prenom_key
                return candidat
        raise RuntimeError(
            "Espace de pseudonymes epuise pour cette famille: elargir COULEURS."
        )

    def alias_connu(self, nom: str, prenom: str = "") -> str:
        """L'alias d'une entite DEJA connue, ou vide. Ne cree jamais rien.

        C'est la porte que les detections generiques empruntent desormais.
        `alias_pour` cree une entite: elle reste reservee aux deux gestes qui en
        ont le droit - la lecture d'une liste nominative structurelle, qui porte
        un numero de compte donc une preuve de rattachement, et la saisie
        humaine.
        """

        nom_key = normalize_identity_key(nom)
        prenom_key = normalize_identity_key(prenom)
        if not nom_key:
            nom_key, prenom_key = prenom_key, ""
        if not nom_key:
            return ""
        entree = self._par_cle.get((nom_key, prenom_key))
        if entree is not None:
            return entree.get("alias", "")
        # Le patronyme est connu mais pas ce prenom: on rend la racine de
        # famille, qui dit vrai la ou trancher entre homonymes serait faux.
        racine = self._racine_par_nom.get(nom_key)
        return f"PERSONNE_{racine}" if racine else ""

    def retire(self, nom: str, prenom: str = "") -> bool:
        """Retire une entite de l'annuaire. Rend True si elle y etait.

        **Ce chemin n'existait pas**, et c'est ce qui rendait un faux positif
        definitif: une entite creee par erreur etait appliquee a tout le corpus
        a chaque passage, sans aucun moyen de l'en sortir.

        Le retrait est volontairement total: la ligne dispara[i]t, sa racine et
        sa couleur sont liberees. Un alias deja ecrit dans un derive n'est pas
        reecrit - le derive se regenere au passage suivant.
        """

        nom_key = normalize_identity_key(nom)
        prenom_key = normalize_identity_key(prenom)
        entree = self._par_cle.pop((nom_key, prenom_key), None)
        if entree is None:
            return False
        self.rows = [row for row in self.rows if row is not entree]
        racine = entree.get("racine", "")
        if racine and not any(row.get("racine") == racine for row in self.rows):
            self._racines_prises.pop(racine, None)
            self._racine_par_nom.pop(nom_key, None)
        alias = entree.get("alias", "")
        if alias.count("_") >= 2:
            self._couleurs_prises.pop((racine, alias.rsplit("_", 1)[1]), None)
        self.dirty = True
        return True

    def alias_pour(
        self,
        nom: str,
        prenom: str = "",
        *,
        compte: str = "",
        source_doc_id: str = "",
    ) -> str:
        nom_key = normalize_identity_key(nom)
        prenom_key = normalize_identity_key(prenom)
        if not nom_key:
            nom_key, prenom_key = prenom_key, ""
            nom, prenom = prenom, ""
        if not nom_key:
            return ""
        existante = self._par_cle.get((nom_key, prenom_key))
        if existante is not None:
            if compte and not existante.get("compte"):
                existante["compte"] = compte
                self.dirty = True
            return existante.get("alias", "")
        racine = self._racine_pour(nom_key)
        if prenom_key:
            alias = f"PERSONNE_{racine}_{self._couleur_pour(racine, nom_key, prenom_key)}"
        else:
            alias = f"PERSONNE_{racine}"
        row = {
            "personne_id": f"PERS-{len(self.rows) + 1:05d}",
            "alias": alias,
            "racine": racine,
            "nom_normalise": nom_key,
            "prenom_normalise": prenom_key,
            "nom_source": nom,
            "prenom_source": prenom,
            "compte": compte,
            "source_doc_id": source_doc_id,
            "premiere_vue": now_iso(),
        }
        self.rows.append(row)
        self._par_cle[(nom_key, prenom_key)] = row
        self.dirty = True
        return alias

    def entrees(self) -> list[dict[str, str]]:
        return list(self.rows)

    def sauvegarde(self) -> Path | None:
        if not self.dirty:
            return None
        write_csv(self.path, self.fields, self.rows)
        self.dirty = False
        return self.path


#: La modalite refutee ne survit pas en constante morte. `RM-2026-0097`
#: avait remplace le seuil `au moins cinq chiffres` par le role
#: `_MOTIF_COMPTE_ROLE`, qui accepte trois chiffres ou plus - un cabinet
#: numerote sur quatre, un autre sur huit. La constante du seuil est restee
#: dans le module, sans plus aucun appelant: une valeur refutee qui reste
#: ecrite se relit un jour comme une regle. Elle est retiree le 2026-09-12.


#: Un montant: des chiffres avec exactement deux decimales, signe, parentheses
#: comptables et symbole monetaire optionnels.
_MOTIF_MONTANT_ROLE = re.compile(r"[-−(]?\s*\d{1,3}(?:[\s  .]\d{3})*[,.]\d{2}\s*\)?\s*€?")

#: Un identifiant de compte: une suite de chiffres qui n'est pas un montant.
#: Le seuil n'est PAS `au moins cinq chiffres` - c'etait une modalite. Un
#: cabinet numerote ses comptes sur quatre chiffres, un autre sur huit.
_MOTIF_COMPTE_ROLE = re.compile(r"\d{3,}")

#: Distance maximale, en lignes, entre le compte et le montant d'une meme
#: entree. Trois couvre la mise en page la plus etalee observee - compte, nom,
#: montant sur trois lignes - sans apparier deux entrees voisines.
_PORTEE_ENTREE_LIGNES = 3

STATUT_LISTE_TROUVEE = "LISTE_TROUVEE"
STATUT_LISTE_ABSENTE = "LISTE_ABSENTE"
STATUT_LISTE_ILLISIBLE = "LISTE_ILLISIBLE"


def _atomes(text: str) -> list[tuple[str, str, int]]:
    """Le texte reduit a une suite de roles: compte, nom, montant.

    Les barres verticales d'une table deviennent des separateurs: une cellule
    est un fragment comme un autre. C'est ce qui permet de lire une vraie table
    sans en coder la syntaxe.
    """

    atomes: list[tuple[str, str, int]] = []
    for index, ligne in enumerate(text.splitlines()):
        brute = ligne.replace("|", " ")
        if not brute.strip():
            continue
        marques: list[tuple[int, int, str, str]] = []
        for match in _MOTIF_MONTANT_ROLE.finditer(brute):
            marques.append((match.start(), match.end(), "montant", match.group(0).strip()))
        occupe = [False] * len(brute)
        for debut, fin, _role, _valeur in marques:
            for position in range(debut, fin):
                occupe[position] = True
        for match in _MOTIF_COMPTE_ROLE.finditer(brute):
            if any(occupe[position] for position in range(match.start(), match.end())):
                continue
            marques.append((match.start(), match.end(), "compte", match.group(0)))
            for position in range(match.start(), match.end()):
                occupe[position] = True
        curseur = 0
        for debut, fin, _role, _valeur in sorted(marques):
            fragment = brute[curseur:debut]
            if _nom_recevable(fragment):
                marques.append((curseur, debut, "nom", fragment.strip(" \t-–—:;,.")))
            curseur = fin
        reste = brute[curseur:]
        if _nom_recevable(reste):
            marques.append((curseur, len(brute), "nom", reste.strip(" \t-–—:;,.")))
        for debut, _fin, role, valeur in sorted(marques):
            atomes.append((role, valeur, index))
    return atomes


def lit_liste_nominative(text: str) -> dict[str, object]:
    """Lit une liste nominative, quelle que soit sa mise en page.

    **L'axe**: la maniere dont une liste nominative distribue le numero de
    compte, le nom et le montant sur des lignes est un degre de liberte. Un
    cabinet les met sur trois lignes, un autre sur une seule, un troisieme dans
    une table a barres verticales.

    **L'invariant**: les trois se suivent dans cet ORDRE - un identifiant, puis
    un nom, puis un solde - dans une zone de texte contigue. C'est cela qui est
    reconnu, et non un nombre de sauts de ligne.

    **L'ancrage est conserve**: exiger un compte AVANT le nom est ce qui empeche
    `- EAU ARROSAGE` suivi de son montant de passer pour une personne. Un poste
    de depense n'a pas de numero de compte devant lui.

    **Hors des valeurs observees**: une mise en page qui porte des comptes et
    des montants sans qu'aucun nom ne s'intercale rend `LISTE_ILLISIBLE`, avec
    ce qui a ete reconnu - jamais une liste vide, qui se confondrait avec
    `pas de liste du tout` et empecherait de reclamer la bonne piece.
    """

    atomes = _atomes(text)
    entrees: list[tuple[str, str]] = []
    comptes_vus = 0
    index = 0
    while index < len(atomes):
        role, valeur, ligne = atomes[index]
        if role != "compte":
            index += 1
            continue
        comptes_vus += 1
        nom: str | None = None
        suivant = index + 1
        while suivant < len(atomes):
            role_suivant, valeur_suivant, ligne_suivant = atomes[suivant]
            if ligne_suivant - ligne > _PORTEE_ENTREE_LIGNES or role_suivant == "compte":
                break
            if role_suivant == "nom" and nom is None:
                nom = valeur_suivant
            elif role_suivant == "montant" and nom is not None:
                entrees.append((valeur, nom))
                break
            suivant += 1
        index += 1

    if entrees:
        statut = STATUT_LISTE_TROUVEE
        motif = ""
    elif comptes_vus:
        statut = STATUT_LISTE_ILLISIBLE
        motif = (
            f"{comptes_vus} identifiants de compte reconnus, mais aucun nom ne s'intercale "
            "entre un compte et son montant. La piece ressemble a une liste nominative "
            "dont la mise en page n'est pas lue."
        )
    else:
        statut = STATUT_LISTE_ABSENTE
        motif = "Aucun identifiant de compte suivi d'un montant: cette piece n'est pas une liste nominative."
    return {"statut": statut, "entrees": entrees, "motif": motif, "comptes_vus": comptes_vus}


def extrait_entrees_annuaire(text: str) -> list[tuple[str, str]]:
    """Les couples (compte, nom complet) d'une liste nominative.

    Conserve pour les appelants qui n'ont besoin que des entrees. Ceux qui
    doivent distinguer `absente` de `illisible` - la gate d'absorption -
    appellent `lit_liste_nominative`.
    """

    resultat = lit_liste_nominative(text)
    return list(resultat["entrees"])  # type: ignore[arg-type]


def variantes_personne(nom: str, prenom: str) -> list[str]:
    """Les ecritures sous lesquelles une personne connue peut apparaitre.

    On produit des formes repliees sans accent: l'appariement se fait sur un
    texte lui aussi replie.
    """

    nom = _fold_preserving(nom).strip()
    prenom = _fold_preserving(prenom).strip()
    formes: list[str] = []
    if nom and prenom:
        formes.append(f"{nom} {prenom}")
        formes.append(f"{prenom} {nom}")
        initiale = prenom.strip()[:1]
        if initiale:
            formes.append(f"{nom} {initiale}.")
    if nom:
        formes.append(nom)
    vues: set[str] = set()
    uniques: list[str] = []
    for forme in formes:
        cle = forme.upper()
        if cle in vues:
            continue
        vues.add(cle)
        uniques.append(forme)
    return uniques


def _motif_forme(forme: str) -> re.Pattern[str]:
    morceaux = [re.escape(token) for token in forme.split() if token]
    corps = r"[\s  ]+".join(morceaux)
    return re.compile(rf"(?<![A-Za-z0-9_]){corps}(?![A-Za-z0-9_])", flags=re.IGNORECASE)


def formes_seules_retenues(
    text: str,
    entrees: list[dict[str, str]],
    *,
    bas_de_casse_corpus: frozenset[str] | None = None,
) -> dict[str, int]:
    """Les patronymes dont la forme seule a ete RETENUE, et ce qu'ils laissent.

    Le compte rendu est le pendant obligatoire du refus: sans lui, la garde
    redevient ce qu'elle etait, un `continue` silencieux. Ce qui remonte ici est
    le nombre d'occurrences **qui ne sont pas ecrites en minuscules**, donc
    celles qui peuvent encore designer la personne et restent en clair dans le
    derive. Les occurrences en bas de casse ne sont pas comptees: ce sont
    precisement celles dont on affirme qu'elles ne designent personne.

    Ce que `06_corpus_markdown.py` en fait: une ligne par piece et par forme dans
    `corpus_caviarde_suspects.csv`, motif `patronyme_ambigu_lexique`.
    `complete_la_file` y ajoute l'appariement propose, puisque la forme vient de
    l'annuaire et que sa racine y est donc connue.
    """

    if not entrees:
        return {}
    replie = _fold_preserving(text)
    bas_de_casse = mots_en_bas_de_casse(replie)
    if bas_de_casse_corpus:
        bas_de_casse |= bas_de_casse_corpus
    retenues: dict[str, int] = {}
    for entree in entrees:
        if not entree.get("alias", ""):
            continue
        nom = entree.get("nom_source", "") or entree.get("nom_normalise", "")
        forme = _fold_preserving(nom).strip()
        if not forme or forme in retenues:
            continue
        if _forme_seule_applicable(forme, bas_de_casse):
            continue
        en_clair = 0
        for match in _motif_forme(forme).finditer(replie):
            lettres = [char for char in replie[match.start() : match.end()] if char.isalpha()]
            if lettres and not all(char.islower() for char in lettres):
                en_clair += 1
        if en_clair:
            retenues[forme] = en_clair
    return retenues


def applique_annuaire(
    text: str,
    entrees: list[dict[str, str]],
    *,
    bas_de_casse_corpus: frozenset[str] | None = None,
) -> tuple[str, dict[str, int]]:
    """Remplace dans `text` toutes les variantes des personnes connues.

    Les formes longues gagnent sur les courtes: `DUPONT Jean` avant `DUPONT`.
    Le nom seul n'est tente que si la piece ne l'emploie jamais comme un mot du
    lexique commun; sinon il part en arbitrage par `formes_seules_retenues`.
    """

    if not entrees:
        return text, {}
    replie = _fold_preserving(text)
    bas_de_casse = mots_en_bas_de_casse(replie)
    if bas_de_casse_corpus:
        bas_de_casse |= bas_de_casse_corpus
    candidats: list[tuple[int, int, str, str]] = []
    for entree in entrees:
        alias = entree.get("alias", "")
        if not alias:
            continue
        nom = entree.get("nom_source", "") or entree.get("nom_normalise", "")
        prenom = entree.get("prenom_source", "")
        racine = entree.get("racine", "")
        alias_famille = f"PERSONNE_{racine}" if racine else alias
        for forme in variantes_personne(nom, prenom):
            seul = forme.strip().upper() == _fold_preserving(nom).strip().upper()
            if seul and not _forme_seule_applicable(forme, bas_de_casse):
                continue
            cible = alias_famille if seul else alias
            for match in _motif_forme(forme).finditer(replie):
                candidats.append((match.start(), match.end(), cible, forme))
    if not candidats:
        return text, {}
    candidats.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    retenus: list[tuple[int, int, str, str]] = []
    curseur = -1
    for debut, fin, cible, forme in candidats:
        if debut < curseur:
            continue
        retenus.append((debut, fin, cible, forme))
        curseur = fin
    compteurs: dict[str, int] = {}
    morceaux: list[str] = []
    precedent = 0
    for debut, fin, cible, forme in retenus:
        morceaux.append(text[precedent:debut])
        morceaux.append(cible)
        compteurs[forme] = compteurs.get(forme, 0) + 1
        precedent = fin
    morceaux.append(text[precedent:])
    return "".join(morceaux), compteurs
