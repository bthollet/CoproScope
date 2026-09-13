"""Le vocabulaire d'une regle de classement, et la garde qui le tient.

Separe de `02_classification.py` le 2026-09-05 pour deux raisons.

La premiere est mesurable: le fichier de classement passait a 608 lignes, au
dela de la limite de 600 du depot.

La seconde compte davantage. `02_classification.py` est le fichier de la voie
classement - le bareme, la taxonomie, les signatures de titre y vivent. Ce qui
est ici n'est pas du classement: c'est la garde qui verifie que les cles ecrites
dans la configuration sont bien celles que le code lit, et elle appartient a la
voie vocabulaire. Les tenir dans deux fichiers laisse les deux voies avancer
sans se marcher dessus, et rend visible ce que chacune possede.

Les parties de `_docuscope_parts` sont executees dans l'ordre du nom, dans un
seul espace de noms: ce fichier est charge avant `02`, donc `CHAMPS_REGLE` et
`_champ_regle` existent quand `_classify` est definie.
"""

import json

#: Les champs d'une regle de classement, et les deux orthographes de chacun.
#:
#: **Le fichier livre est ecrit en francais.** Un champ dont l'alias francais
#: manque ici n'est donc lu chez personne: il est present dans la
#: configuration, il a l'air de compter, et il vaut sa valeur par defaut.
#: Mesure du 2026-09-04: `priority` n'avait pas son alias `priorite`, que
#: `taxonomy.default.yml` ecrit sur ses 38 regles. Les 38 priorites valaient 0,
#: et le seul mecanisme d'arbitrage entre regles concurrentes etait mort - 271
#: lignes du registre reel (7,9 %) etaient departagees par la position de la
#: regle dans le fichier, pas par le droit.
#:
#: Cette table est la liste fermee: `_champ_regle` ne lit rien d'autre, et
#: `_verifier_regles` signale une regle qui porte un nom absent d'ici. Il le
#: signale sans lever: d'autres voies ajoutent des champs a la taxonomie pour
#: leur propre usage, et refuser le fichier entier pour un champ qui ne
#: concerne pas le classement rendrait le classement indisponible sur une
#: question qui ne le regarde pas.
CHAMPS_REGLE: dict[str, tuple[str, ...]] = {
    "lot": ("lot",),
    "document_type": ("document_type", "type_document"),
    "priority": ("priority", "priorite"),
    "filename_patterns": ("filename_patterns", "motifs_nom_fichier"),
    "path_patterns": ("path_patterns", "motifs_chemin"),
    "keywords": ("keywords", "mots_cles"),
    "filename_weight": ("filename_weight", "poids_nom_fichier"),
    "path_weight": ("path_weight", "poids_chemin"),
    "keyword_weight": ("keyword_weight", "poids_mot_cle"),
}

#: Les champs qui sont la pour etre LUS PAR UN HUMAIN, jamais par le code.
#:
#: La distinction n'est pas un assouplissement de la garde, c'est la question
#: qu'elle pose, posee correctement. `priorite` etait un REGLAGE ignore: il
#: promettait d'agir et n'agissait pas, et c'est le defaut C009. `fondement`
#: est une CITATION - l'article du decret qui justifie une regle de
#: classement. Elle ne promet aucun effet, donc son absence d'effet n'est pas
#: un defaut. Les confondre ferait crier la garde sur la seule categorie de
#: champ qui a le droit de ne rien declencher, et la ferait desactiver.
#:
#: Ce qui reste interdit est le troisieme cas: un champ ni lu, ni declare ici.
#: Celui-la n'est ni un reglage ni une justification, il est un oubli.
#:
#: Mesure du 2026-09-05 sur `chantier/fix-classement`: `fondement` est ecrit
#: sur cinq regles de la taxonomie et `git grep` ne trouve aucun lecteur dans
#: `server/src`. Il est declare ici pour ce qu'il est.
CHAMPS_DOCUMENTAIRES = frozenset({"fondement"})

#: Tous les noms acceptes, toutes orthographes confondues.
NOMS_CHAMPS_REGLE = frozenset(
    nom for alias in CHAMPS_REGLE.values() for nom in alias
) | CHAMPS_DOCUMENTAIRES

#: Les cles de premier niveau du fichier de taxonomie. `version` est declaree
#: ici bien qu'aucun code ne la lise: elle est un marqueur, pas un reglage, et
#: la nommer evite de la confondre avec un reglage mort.
CHAMPS_TAXONOMIE = frozenset(
    {"rules", "regles", "title_signature", "signature_titre", "version"}
)


def _champ_regle(rule: dict, champ: str, defaut):
    """La valeur du champ, quelle que soit son orthographe declaree."""
    for alias in CHAMPS_REGLE[champ]:
        if alias in rule:
            return rule[alias]
    return defaut


def _verifier_taxonomie(taxonomy: dict, journal=None) -> list[str]:
    """Signale une cle de premier niveau que le classement ne lit pas.

    Meme severite que `_verifier_regles` sur les champs inconnus, et pour la
    meme raison: le fichier de taxonomie est partage. Une autre voie peut y
    ecrire une cle de tete pour son propre usage, et lever ici rendrait le
    classement indisponible sur un reglage qui ne le concerne pas. Le silence
    n'est pas une option pour autant - une cle que PERSONNE ne lit a l'air de
    regler quelque chose et ne regle rien. Elle est donc nommee.
    """
    inconnues = sorted(set(taxonomy) - CHAMPS_TAXONOMIE)
    if not inconnues:
        return []
    message = (
        f"fichier de taxonomie: cles de tete non lues par le classement "
        f"{inconnues}. Attendu l'une de {sorted(CHAMPS_TAXONOMIE)}. Si l'une "
        "d'elles doit regler le classement, il faut la declarer dans "
        "CHAMPS_TAXONOMIE; sinon elle appartient a une autre voie."
    )
    if journal is not None:
        journal(message)
    return [message]


#: Les champs sans lesquels une regle ne peut pas conclure. `lot` nomme le
#: dossier ou la piece est rangee, `document_type` ce qu'elle est: une regle qui
#: gagne le score sans les porter fait ranger un document quelque part sans
#: pouvoir dire ou ni pourquoi. Les 38 regles du fichier livre les portent
#: toutes les deux.
CHAMPS_REQUIS = ("lot", "document_type")


def _nom_regle(rule: dict) -> str:
    """De quoi nommer la regle fautive dans un message d'erreur."""
    return str(_champ_regle(rule, "document_type", "") or "?")


def _verifier_regles(rules: list[dict], journal=None) -> list[str]:
    """Refuse une regle qui ne peut pas conclure, signale un champ non lu.

    Deux severites, et la difference est deliberee.

    **Fatal - un champ requis absent.** Mesure du 2026-09-05: une regle sans
    `lot` faisait rendre a `_classify` le triplet ('A_CLASSER', 'PV_AG', 5),
    c'est-a-dire un type documentaire affirme range dans un lot invente, sans
    erreur. Le code d'avant levait un `KeyError` sur cette regle; la garde qui
    devait durcir le chargement laissait passer exactement le cas qu'elle
    existait pour attraper. Une regle amputee ne se rattrape pas plus loin: on
    la refuse ici.

    **Signale, pas fatal - un champ inconnu.** Une cle que `CHAMPS_REGLE` ne
    connait pas ne provoque rien: elle est ignoree, et la regle se comporte
    comme si le reglage n'avait pas ete ecrit. C'est le meme silence, donc il
    faut le dire - mais le dire en levant refuserait aussi les champs que les
    AUTRES voies ajoutent legitimement a la taxonomie sans passer par ce
    module, et une erreur au chargement rendrait alors le classement
    indisponible pour un champ qui ne le concerne pas. Le defaut est nomme,
    ecrit au journal quand un journal est fourni, et rendu a l'appelant.

    Rend la liste des signalements, vide quand tout est lu.
    """
    signalements: list[str] = []
    for numero, rule in enumerate(rules, start=1):
        manquants = [c for c in CHAMPS_REQUIS if _champ_regle(rule, c, None) is None]
        if manquants:
            raise ValueError(
                f"regle de classement n°{numero} ({_nom_regle(rule)}): champs "
                f"requis absents {manquants}. Une regle qui gagne le score sans "
                "eux fait ranger une piece dans un lot que personne n'a ecrit."
            )
        inconnues = sorted(set(rule) - NOMS_CHAMPS_REGLE)
        if inconnues:
            signalements.append(
                f"regle de classement n°{numero} ({_nom_regle(rule)}): champs "
                f"non lus par le classifieur {inconnues}. Attendu l'un de "
                f"{sorted(NOMS_CHAMPS_REGLE)}. Le classement ignore ces champs: "
                "s'ils doivent peser, il faut les declarer dans CHAMPS_REGLE."
            )
    if journal is not None:
        for message in signalements:
            journal(message)
    return signalements


#: Les cles de tete que le classement LIT, donc qui peuvent deplacer un type.
#:
#: `version` en est retiree, et c'est la seule exception: elle est declaree
#: plus haut comme un marqueur que personne ne lit. Tout le reste de
#: `CHAMPS_TAXONOMIE` entre dans l'empreinte, `signature_titre` compris - la
#: fenetre de tete et le plancher de texte utile promeuvent et declassent des
#: lignes, ils pesent donc autant qu'un mot-cle.
CHAMPS_TAXONOMIE_SANS_EFFET = frozenset({"version"})

#: Marqueur d'un champ absent de la regle. Il n'est PAS remplace par la valeur
#: par defaut du calcul de score: ces defauts vivent dans le code, et les
#: recopier ici ferait qu'un changement de CODE se lirait comme un changement
#: de BAREME. Une regle qui omet un champ s'empreinte comme l'omettant.
CHAMP_ABSENT = "(absent)"


def empreinte_bareme(taxonomy: dict) -> str:
    """Empreinte de tout ce qui, dans la taxonomie, peut deplacer un type.

    **L'axe, et pourquoi ce n'est pas une somme de controle du fichier.** Un
    bareme est une ENTREE qui deplace des SORTIES: en toucher une ligne bouge
    des milliers de documents, et cela s'est produit sans mesure - `a56b9fe` a
    retire NEUF motifs et ajoute un mot-cle pendant qu'un lecteur affirmait que
    le bareme n'avait pas ete touche (`RM-2026-0076`). Une empreinte du fichier
    brut aurait crie sur une virgule de mise en forme et sur l'ajout d'un
    `fondement`, donc elle aurait fini desactivee; elle aurait aussi manque le
    cas inverse, un fichier reformate dont un poids a change.

    Ce qui est empreinte est donc exactement ce que le classifieur LIT:
    `CHAMPS_REGLE` pour les regles, `CHAMPS_TAXONOMIE` pour la tete. Les deux
    sont declares au-dessus, et l'empreinte les PARCOURT au lieu de nommer les
    champs d'aujourd'hui. Consequence voulue: le jour ou un reglage est ajoute
    a `CHAMPS_REGLE`, il entre dans l'empreinte sans qu'une ligne soit ecrite
    ici. Un champ purement documentaire - `fondement` - n'y entre jamais, parce
    qu'il ne promet aucun effet.

    Rend une chaine lisible, pas un condensat: c'est ce qui permet a l'echec
    de dire QUELLE regle a bouge, au lieu de dire que quelque chose a bouge.

    **Ce que la premiere version de cette fonction laissait passer en
    silence**, mesure le 2026-09-09 sur la base `ffac60c`. Elle rendait
    ses lignes par `sorted(lignes)`, donc les lignes de REGLE etaient triees
    alphabetiquement, et son propre `_valeur_stable` ecrivait pourtant:
    *"Une liste garde son ORDRE: l'ordre des regles tranche les egalites de
    score"*. La propriete etait affirmee dans un docstring et detruite deux
    lignes plus bas. Deplacer `PV_AG` avant `Carnet_Entretien` - aucune valeur
    modifiee - fait passer un proces-verbal de `Carnet_Entretien` a `PV_AG`
    (egalite a 113, `_classify` compare avec `score > best[2]`, donc la
    premiere regle ecrite gagne) et rendait une empreinte OCTET POUR OCTET
    identique. C'est le mecanisme que `RM-2026-0076` nomme lui-meme: *"
    Convocation_AG est ecrite avant PV_AG dans le fichier, elle gagne
    l'egalite"*.

    D'ou les deux proprietes que cette version tient, et qui sont l'axe:

    1. **Une sequence s'empreinte comme une sequence.** Les regles portent leur
       RANG. La tete est un mapping: ses lignes restent triees, parce que rien
       dans le classement ne depend de l'ordre des cles d'un dictionnaire.
    2. **Le rendu est injectif.** Les valeurs passent par `json.dumps`, donc
       une valeur qui contient le separateur ne peut plus se lire comme deux
       valeurs. Avant, `mots_cles: ["a,b"]` et `["a","b"]` rendaient tous deux
       `[a,b]` - deux baremes qui classent le meme texte differemment sous une
       empreinte identique.
    """
    lignes: list[str] = []
    tete = (set(taxonomy) & CHAMPS_TAXONOMIE) - CHAMPS_TAXONOMIE_SANS_EFFET
    for cle in sorted(tete - {"rules", "regles"}):
        lignes.append(f"tete/{cle}={_valeur_stable(taxonomy[cle])}")
    lignes.sort()
    regles = list(taxonomy.get("rules", taxonomy.get("regles", [])))
    # Ligne de lecture: un pur deplacement de regle s'y voit d'un coup d'oeil,
    # la ou les rangs ci-dessous decalent tout un bloc. Elle est redondante
    # avec les rangs, et c'est voulu: les rangs portent la garantie, celle-ci
    # porte le diagnostic.
    lignes.append(
        "ordre/types=" + _valeur_stable([_rule_type_empreinte(r) for r in regles])
    )
    for rang, rule in enumerate(regles):
        champs = ";".join(
            f"{champ}={_valeur_stable(_champ_regle(rule, champ, CHAMP_ABSENT))}"
            for champ in sorted(CHAMPS_REGLE)
        )
        lignes.append(f"regle[{rang:03d}]/" + champs)
    return "\n".join(lignes)


def _rule_type_empreinte(rule: dict) -> str:
    """Le type d'une regle, pour la seule ligne de lecture de l'empreinte."""
    return str(_champ_regle(rule, "document_type", CHAMP_ABSENT))


def _valeur_stable(valeur) -> str:
    """Rendu deterministe ET INJECTIF d'une valeur de configuration.

    Une liste garde son ORDRE: l'ordre des motifs decide lequel s'ecrit en
    premier. Un dictionnaire est trie, parce que rien dans le classement ne
    depend de l'ordre de ses cles. `json.dumps` fait les deux, et il fait en
    plus ce que la version precedente ne faisait pas: il DELIMITE les valeurs.
    Sans delimiteur, le separateur de liste appartenait a la fois a la
    structure et aux valeurs, et deux baremes differents se rendaient pareil.

    `default=str` couvre ce que JSON ne sait pas ecrire - une date rendue par
    le lecteur YAML, par exemple. Une valeur inconnue se degrade donc en son
    texte au lieu de lever une exception que personne ne saurait rattacher au
    bareme.
    """
    return json.dumps(valeur, ensure_ascii=False, sort_keys=True, default=str)
