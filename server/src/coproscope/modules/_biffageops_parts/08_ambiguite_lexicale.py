from __future__ import annotations


"""Un patronyme ecrit seul est-il un nom, ou un mot du lexique commun ?

Extrait de `05_corpus_annuaire.py` le 2026-09-09, quand ce fichier a franchi les
600 lignes. La doctrine du depot fait de l'extraction le chantier prioritaire
avant tout ajout, et la coupure tombe juste: l'annuaire et l'appariement de ses
variantes sont un geste, decider si une chaine designe une personne dans une
piece en est un autre.

**L'axe.** Un patronyme n'a pas de forme reconnaissable en soi. Ce qui varie
d'une piece a l'autre - la civilite, la casse, la position, la presence d'un
prenom - ne dit rien de son ambiguite avec le lexique commun.

**L'invariant** est une regle de la langue et non l'habitude d'un cabinet: le
francais ecrit un nom commun en minuscules, et n'ecrit jamais un nom propre en
minuscules. Un mot du lexique laisse donc, quelque part dans le corpus, une
occurrence tout en bas de casse. Un patronyme, non.

**Ce que le code en fait.** Il releve les mots en bas de casse une fois pour le
corpus, puis refuse la forme `patronyme seul` de toute chaine qui y figure - et
il NOMME ce refus dans la file d'arbitrage au lieu de le taire.

**Hors des valeurs observees.** Les trois cas sont ecrits sur
`forme_ambigue_avec_le_lexique`; aucun ne rend une reponse fausse en silence.
"""


#: Une suite maximale de caracteres de mot, apostrophes et traits d'union
#: compris. Les bornes sont celles de `_motif_forme`. La casse est jugee ensuite
#: par `str.islower`, et non par une plage `a-z`: le texte est replie mais pas
#: reduit a l'ASCII, et une plage aurait laisse passer les lettres qui n'y sont
#: pas.
_MOTIF_MOT_BAS_DE_CASSE = re.compile(
    r"(?<![A-Za-z0-9_])(\w[\w'’\-]*)(?![A-Za-z0-9_])"
)

#: Les separateurs internes qu'une suite bas de casse peut contenir et que
#: `_motif_forme` accepte AVANT une forme: `l'annee` contient donc, pour
#: l'apparieur, une occurrence de `annee`.
_SEPARATEURS_INTERNES = re.compile(r"['’\-]+")


def mots_en_bas_de_casse(texte_replie: str) -> frozenset[str]:
    """Tous les mots de la piece ecrits tout en minuscules, en UN balayage.

    **Le cout d'execution fait partie de la conception d'une garde.** La
    premiere version posait la question forme par forme, donc un balayage du
    texte entier par personne de l'annuaire: 15,3 s pour 29 pieces et 327 000
    caracteres, contre 10,7 s pour la chaine sans la garde. Un garde-fou qu'on
    finit par desactiver parce qu'il ralentit la chaine ne garde rien. Le releve
    est donc fait une fois, et l'appartenance se lit ensuite dans un ensemble.

    **Ce releve doit etre un SUR-ensemble de ce que `_motif_forme` peut apparier
    en bas de casse, et une premiere version ne l'etait pas.** Le commentaire
    disait que les deux vues du texte ne pouvaient pas se contredire; la mesure
    du 2026-09-09 a montre que si. `_motif_forme` accepte une apostrophe ou un
    trait d'union juste avant la forme, donc `l'annee` porte pour lui une
    occurrence de `annee` - alors que le releve n'y voyait qu'un seul mot,
    `l'annee`. Une forme jugee non ambigue a tort est masquee a tort. On indexe
    donc la suite entiere ET ses morceaux: si l'apparieur peut le trouver en bas
    de casse, le releve le contient.
    """

    vocabulaire: set[str] = set()
    for match in _MOTIF_MOT_BAS_DE_CASSE.finditer(texte_replie):
        mot = match.group(1)
        if not mot.islower():
            continue
        vocabulaire.add(mot)
        vocabulaire.update(part for part in _SEPARATEURS_INTERNES.split(mot) if part)
    return frozenset(vocabulaire)


def vocabulaire_bas_de_casse_corpus(textes: dict[str, str]) -> frozenset[str]:
    """Le releve de bas de casse de TOUT le corpus, en un seul passage.

    **L'ambiguite d'une chaine avec le lexique est une propriete de la chaine
    dans ce corpus, pas une propriete d'une piece.** Mesure du 2026-09-09 qui a
    impose cette portee: juge piece par piece, le test masquait quand meme 88
    occurrences de trois intitules courants, parce que les pieces ou ils
    paraissent sont des tables tout en capitales, sans une ligne de prose pour
    fournir la contre-preuve. La piece ou le mot se lit en minuscules et la piece
    ou il faut trancher ne sont pas la meme piece.

    Les occurrences de vrais patronymes courts que la portee corpus continue de
    masquer sont, elles, inchangees: aucun d'eux ne se lit en bas de casse nulle
    part.
    """

    vocabulaire: set[str] = set()
    for texte in textes.values():
        vocabulaire |= mots_en_bas_de_casse(_fold_preserving(texte))
    return frozenset(vocabulaire)


def forme_ambigue_avec_le_lexique(forme: str, bas_de_casse: frozenset[str]) -> bool:
    """La forme s'ecrit-elle AUSSI tout en minuscules dans cette piece ?

    **L'axe: un patronyme ecrit seul est ambigu avec le lexique commun.** Ce qui
    varie d'une piece a l'autre - la civilite, la casse, la position, la presence
    d'un prenom - ne dit rien de cette ambiguite. Ce qui reste invariant le long
    de l'axe est une regle de la langue, pas l'habitude d'un cabinet: **le
    francais ecrit un nom commun en minuscules, et n'ecrit jamais un nom propre
    en minuscules.** Un mot du lexique laisse donc, quelque part dans la piece,
    une occurrence tout en bas de casse. Un patronyme, non.

    `bas_de_casse` vient de `mots_en_bas_de_casse`, sur le texte deja passe par
    `_fold_preserving` - comme l'appariement lui-meme: on compare du replie a du
    replie.

    Une forme a plusieurs mots - `DE VERNAZOUX`, `DA SILVA` - est ambigue quand
    **chacun** de ses mots se lit en bas de casse dans la piece. Les particules y
    sont toujours, donc la decision porte en pratique sur le porteur, ce qui est
    exactement ce qu'on veut savoir.

    **Degradation hors des valeurs observees.** Trois cas, aucun muet:

    - une piece entierement en capitales - OCR de table, convocation composee en
      majuscules - ne porte aucune occurrence minuscule, donc aucune
      contre-preuve. La forme est jugee non ambigue et **appliquee**: c'est le
      sens sur, on masque;
    - un patronyme qui apparait aussi en minuscules - dans une adresse
      electronique, dans un index en bas de casse - est juge ambigu, donc **non
      applique**. Ses occurrences en clair ne disparaissent pas du compte:
      `formes_seules_retenues` les remonte en arbitrage. Les adresses completes
      restent par ailleurs traitees par la passe generique, `_MOTIF_EMAIL`;
    - un intitule comptable absent de toute prose de la piece est juge non
      ambigu et **sur-masque**. Le cas est visible dans le derive: un alias de
      personne apparait la ou un lecteur attend un intitule.
    """

    mots = [token for token in forme.split() if token]
    if not mots:
        return False
    return all(token.lower() in bas_de_casse for token in mots)


def _forme_seule_applicable(forme: str, bas_de_casse: frozenset[str]) -> bool:
    """La forme `patronyme seul` peut-elle etre appliquee a cette piece ?

    **Ce que ce test remplace.** Jusqu'au 2026-09-09 la branche `patronyme seul`
    etait gardee par `len(cle) < 4 or cle in VOCABULAIRE_PROTEGE`. Les deux
    clauses codaient des modalites sur des dimensions sans rapport avec le
    risque, et elles echouaient dans les deux sens. Mesure sur le corpus etalon
    de `RM-2026-0050`, 29 pieces, 49 patronymes tires des listes nominatives:

    - `len(cle) < 4` ecartait 12 patronymes. **8 etaient de vrais patronymes de
      trois lettres**, laisses en clair sur **68 occurrences**; les 4 autres
      etaient du bruit d'extraction que le seuil attrapait par hasard. La
      longueur d'une chaine ne dit rien de son ambiguite;
    - `cle in VOCABULAIRE_PROTEGE` a eu prise sur **0 des 49**. Aucun des 11
      patronymes qui sont aussi des mots courants n'y figurait, et leurs **61
      occurrences en minuscules** etaient remplacees par un alias de personne au
      milieu de la prose.

    Le test de casse separe les deux populations sans recouvrement sur ce corpus:
    34 patronymes a zero occurrence minuscule, 15 mots courants a au moins une.

    **Hypothese refutee par la mesure, ecrite ici pour qu'on ne la reprenne
    pas.** Une capitale *en exces de ce que la position impose* - des majuscules
    dans une ligne qui n'est pas toute en majuscules - semblait un meilleur
    signal. Elle tire dans le mauvais sens: 148 occurrences du cote des mots
    courants contre 19 du cote des patronymes.

    `VOCABULAIRE_PROTEGE` survit ici en **filet**, pas en mecanisme. Il couvre le
    troisieme cas de degradation ci-dessus - un intitule dans une piece sans
    prose - et non parce qu'il discrimine. **Allonger cette liste ne repare
    rien**: c'est le geste que ce lot remplace.
    """

    if normalize_identity_key(forme) in VOCABULAIRE_PROTEGE:
        return False
    return not forme_ambigue_avec_le_lexique(forme, bas_de_casse)


