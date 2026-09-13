"""Declarations du journal d'observation d'un extranet de syndic.

Ce module ne contient que des **declarations**: noms de tables, colonnes, cles,
ordres de lecture, et le vocabulaire des etats. L'analyse d'une page est dans
`_extranet_adaptateur`, l'ecriture dans `_extranet_store`, la derivation des
changements dans `_extranet_journal`.

Il sert `RM-2026-0091`. Conception:
`docs/journal_observation_extranet.md`. Mesures qui la fondent:
`docs/cartographie_extranet_coprodirecte_2026-09-04.md`.

----------------------------------------------------------------------
La decision de structure: un retrait ne se stocke pas, il se deduit
----------------------------------------------------------------------

Aucune table ne porte de colonne `evenement`, `ajout` ou `retrait`. Le journal
enregistre **ce qui a ete observe** et **ou l'on a regarde**; les trois
evenements sont calcules a la lecture, en comparant deux passages.

Trois raisons, et la troisieme est la vraie.

1. Un evenement stocke fige une conclusion tiree avec la comprehension du jour.
   Le 2026-09-04, la cle d'emplacement a ete mesuree **injective mais pas
   stable**: sa stabilite entre deux passages exige un second passage a
   plusieurs jours, qui n'a pas eu lieu. Si cette mesure devait montrer un
   defaut, des verdicts `RETRAIT` deja ecrits resteraient faux dans la base,
   alors qu'une derivation se recalcule.
2. Un retrait n'est pas une propriete d'une piece, c'est une propriete d'un
   **couple de passages**. Le stocker sur la piece attribue a un objet ce qui
   appartient a une comparaison.
3. Le mode de defaillance redoute est le **faux retrait**, et c'est le constat
   le plus accusatoire que l'outil sache produire. La derivation permet de
   refuser de conclure quand la couverture manque. Une colonne ne sait pas se
   taire.

----------------------------------------------------------------------
Ce que le journal n'ecrit jamais
----------------------------------------------------------------------

**Aucun auteur.** Trois sources de changement se melangent sur un extranet - le
syndic, un autre coproprietaire qui suit les factures, l'utilisateur lui-meme -
et l'extranet n'expose pas qui a agi. Ecrire "le syndic a supprime" serait une
accusation que le journal ne peut pas soutenir. Il ecrit un etat, date.

**Aucune adresse de document.** Chez l'editeur mesure, l'URL d'une piece est un
jeton opaque **re-chiffre a chaque chargement de page** et neanmoins valide
apres coup: c'est donc une adresse porteuse d'un droit d'acces, l'equivalent
d'un identifiant. Elle ne va ni en base, ni dans un journal, ni dans Git.

**Aucun contenu.** Le journal porte des empreintes et des emplacements. Les
pieces d'un extranet de copropriete contiennent des donnees de tiers - la liste
des coproprietaires de l'article 32 du decret 67-223 porte l'etat civil de
tous.

----------------------------------------------------------------------
Pourquoi ces tables vivent dans `gouvernance.sqlite3`
----------------------------------------------------------------------

Meme fichier que `resolutions`, `convocations`, `actes_autorisation`, sous
`settings.vault.local_root`, par la meme couche `vault.gouvernance_store`.
Rien n'est ajoute a la base de reconstruction. Raison corrigee le 2026-09-08:
une table posee la sans recorder n'y est PAS effacee - `_reset_schema` est une
liste explicite de `DROP TABLE IF EXISTS` et la base n'est jamais supprimee,
donc une table hors liste survit a tous les rebuilds. Ce n'est pas une perte
differee, c'est une desynchronisation muette, et elle est pire: une perte finit
par se voir.

**Consequence de l'append-only.** L'ecriture passe par
`gouvernance_store.remplacer_pour_documents` avec une liste de documents
**vide**. Ce n'est pas un contournement, c'est le chemin documente par cette
couche pour les lignes qui ne derivent d'aucun document: rien n'est efface. Un
journal dont le passage du 15 disparaitrait a l'ecriture du 22 ne serait pas un
journal.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Vocabulaire
# ---------------------------------------------------------------------------

#: Une rubrique a ete reellement parcourue pendant le passage.
RUBRIQUE_PARCOURUE = "PARCOURUE"
#: L'observateur n'y est pas alle. Ce n'est **pas** "vide": c'est "pas regarde".
RUBRIQUE_NON_EXPLOREE = "NON_EXPLOREE"
#: L'adaptateur a echoue sur cette rubrique - structure inattendue, erreur.
RUBRIQUE_ECHEC = "ECHEC"

ETATS_RUBRIQUE = (RUBRIQUE_PARCOURUE, RUBRIQUE_NON_EXPLOREE, RUBRIQUE_ECHEC)

#: L'editeur annonce lui-meme un total ou une fin de liste.
CLOTURE_ATTESTEE = "ATTESTEE"
#: Aucun total annonce, mais l'index entier etait dans la page: ni pagination,
#: ni chargement paresseux. Cloture constatee par l'observateur, plus faible
#: qu'une attestation et suffisante pour conclure a une absence.
CLOTURE_CONSTATEE = "CONSTATEE"
#: Ni l'un ni l'autre. Aucune absence n'est affirmable dans cette rubrique.
CLOTURE_AUCUNE = "AUCUNE"

CLOTURES = (CLOTURE_ATTESTEE, CLOTURE_CONSTATEE, CLOTURE_AUCUNE)

#: L'emplacement a toutes ses composantes: il peut servir a comparer.
EMPLACEMENT_QUALIFIE = "QUALIFIE"
#: Une composante manque. La piece est journalisee, mais elle ne participe a
#: aucun verdict d'ajout ni de retrait. On ne devine pas une cle.
EMPLACEMENT_INDETERMINE = "INDETERMINE"

#: L'empreinte du contenu a ete calculee sur les octets recus.
#: **Declare, sans producteur, et c'est une reserve et non un oubli.**
#: Aucun des trois lecteurs ne l'ecrit: tous rendent `CONTENU_NON_VERIFIE` avec
#: une empreinte vide. La consequence est que `MODIFICATION` et `INCHANGE` sont
#: inatteignables en production - tout ce qui est present aux deux dates
#: ressort `PRESENCE_INCHANGEE`.
#:
#: Ce n'est pas une lacune: emettre cet etat suppose de TELECHARGER les octets
#: d'une piece pour en calculer l'empreinte, ce que l'arbitrage A3 de la
#: conception exclut - *presence seulement, le contenu reste sur geste humain*.
#: Rapatrier des megaoctets de donnees de tiers sans que personne regarde est
#: un cout qu'on ne peut pas justifier.
#:
#: `server/tests/test_extranet_referentiel.py` verifie qu'aucun producteur ne
#: l'ecrit, pour que la reserve reste une decision et ne devienne pas un oubli.
CONTENU_VERIFIE = "VERIFIE"
#: Aucune empreinte. Ne signifie **jamais** "contenu inchange": chez l'editeur
#: mesure, ni `etag`, ni `last-modified`, ni `content-length` ne sont servis, et
#: `accept-ranges` est annonce sans etre honore. Sans les octets, on ne sait pas.
CONTENU_NON_VERIFIE = "NON_VERIFIE"

ORIGINE_EXTRAIT = "EXTRAIT"
ORIGINE_CORRIGE = "CORRIGE_HUMAIN"

#: Separateur des composantes de l'emplacement. Choisi hors des jeux de
#: caracteres observes dans les libelles, pour qu'une composante contenant le
#: separateur ne puisse pas fabriquer une fausse egalite de cles.
SEPARATEUR_EMPLACEMENT = "\x1f"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

#: Un passage: une campagne d'observation, bornee dans le temps.
COLONNES_PASSAGES = (
    "passage_id",
    "editeur",
    "espace",
    "debut",
    "fin",
    "profil",
    "doc_id",
    "origine",
)
CLES_PASSAGES = ("passage_id", "origine")

#: La couverture. **C'est la table qui rend un retrait affirmable.**
#:
#: Un journal qui n'enregistrerait que les pieces trouvees ne pourrait jamais
#: conclure a une absence: rien ne distinguerait "la rubrique etait vide" de
#: "personne n'y est alle". Cette table dit ou l'on a regarde, meme - et
#: surtout - quand on n'y a rien trouve.
COLONNES_RUBRIQUES = (
    "passage_id",
    "rubrique_code",
    "rubrique_libelle",
    "etat",
    "cloture",
    "nb_pieces",
    "motif",
    "doc_id",
    "origine",
)
CLES_RUBRIQUES = ("passage_id", "rubrique_code", "origine")

#: Une piece observee a un emplacement, pendant un passage.
#:
#: `rang` entre dans la cle primaire et **pas** dans l'emplacement. La
#: distinction est deliberee et vient d'une mesure: sur la page des depenses de
#: l'editeur observe, la cle par rang est injective *sans etre stable* - une
#: ligne inseree en tete decale toutes les suivantes, et le journal verrait un
#: remaniement complet la ou rien n'a bouge. Le rang sert donc a identifier une
#: **observation** dans son passage; l'emplacement seul sert a comparer deux
#: passages.
COLONNES_PIECES = (
    "passage_id",
    "rubrique_code",
    "rang",
    "groupe",
    "libelle",
    "emplacement",
    "emplacement_qualite",
    "nom_serveur",
    "empreinte",
    "contenu_etat",
    "doc_id",
    "origine",
)
CLES_PIECES = ("passage_id", "rubrique_code", "rang", "origine")

TABLES: dict[str, tuple[tuple[str, ...], tuple[str, ...], str]] = {
    "extranet_passages": (COLONNES_PASSAGES, CLES_PASSAGES, "debut DESC, passage_id DESC"),
    "extranet_rubriques": (
        COLONNES_RUBRIQUES,
        CLES_RUBRIQUES,
        "passage_id DESC, rubrique_code",
    ),
    "extranet_pieces": (
        COLONNES_PIECES,
        CLES_PIECES,
        "passage_id DESC, rubrique_code, CAST(rang AS INTEGER)",
    ),
}

INDEX: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("extranet_pieces", "idx_extranet_pieces_emp", ("emplacement",)),
    ("extranet_pieces", "idx_extranet_pieces_passage", ("passage_id", "rubrique_code")),
    ("extranet_rubriques", "idx_extranet_rubriques_passage", ("passage_id",)),
)


def emplacement(rubrique_code: str, groupe: str, libelle: str) -> tuple[str, str]:
    """Construit la cle d'emplacement, et dit si elle est exploitable.

    Rend `(cle, qualite)`. La qualite vaut `EMPLACEMENT_INDETERMINE` des qu'une
    composante indispensable manque, et la cle n'est alors utilisee pour aucune
    comparaison.

    **Pourquoi trois composantes, et pas le libelle seul.** Mesure du
    2026-09-04 sur l'index entier d'un extranet reel: le libelle seul donne
    **32 collisions sur 115 pieces, soit 28 % de l'index**. Toutes dans la
    rubrique des arretes de comptes, ou huit libelles - les cinq annexes
    comptables et les etats de depenses - se repetent a l'identique sur cinq
    exercices. L'exercice ne figure pas dans le libelle: il est porte par
    l'en-tete de groupe. La cle a trois composantes rend, sur le meme index,
    **115 cles distinctes pour 115 pieces**.

    Une confusion de cle ici ne produit pas une erreur visible: elle fusionne
    cinq exercices d'annexes comptables en silence, et fait donc disparaitre
    des retraits reels.

    **Le groupe est facultatif.** Sur l'index mesure, une seule rubrique sur
    huit emploie des groupes; dans les sept autres le libelle est deja injectif
    en interne. Un groupe vide est donc normal et ne degrade rien - c'est la
    rubrique et le libelle qui sont indispensables.
    """
    rubrique_code = (rubrique_code or "").strip()
    groupe = (groupe or "").strip()
    libelle = (libelle or "").strip()
    if not rubrique_code or not libelle:
        return "", EMPLACEMENT_INDETERMINE
    cle = SEPARATEUR_EMPLACEMENT.join((rubrique_code, groupe, libelle))
    return cle, EMPLACEMENT_QUALIFIE


def composantes(cle: str) -> tuple[str, str, str]:
    """L'inverse de `emplacement`, pour rendre un constat lisible.

    Rend toujours trois valeurs - rubrique, groupe, libelle - **quelle que soit
    la longueur de la cle**. Les composantes au-dela de la deuxieme sont
    rejointes dans le libelle.

    Ce detail n'est pas cosmetique, et un test l'a montre. Une ligne de depenses
    porte cinq composantes, dont le **montant** en derniere position - et c'est
    precisement le montant qui distingue deux lignes de meme date, meme nature
    et meme libelle. Une troncature a trois aurait affiche deux constats
    rigoureusement identiques pour deux lignes differentes: l'utilisateur aurait
    vu l'outil se repeter, alors qu'il aurait eu raison.

    Une cle ne doit jamais perdre d'information en devenant lisible.
    """
    morceaux = [m for m in (cle or "").split(SEPARATEUR_EMPLACEMENT)]
    while len(morceaux) < 3:
        morceaux.append("")
    return morceaux[0], morceaux[1], " | ".join(m for m in morceaux[2:] if m)
