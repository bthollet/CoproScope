"""Modele relationnel de l'acte d'autorisation, de la depense, et de leur lien.

Ce module ne contient que des **declarations**: le nom des tables, leurs
colonnes, leur cle, leur ordre de lecture, le vocabulaire des liens, et la
derivation des identifiants. Les vues sont dans `_actes_vues`, les filtres dans
`_actes_requetes`, l'ecriture dans `_actes_store`.

Il repond au trou T1 du blueprint de la chaine: *l'objet dossier de depense et
le lien acte-euro n'existent pas*.

----------------------------------------------------------------------
Les quatre decisions back de `strategie_lot_gouvernance.md` section 5
----------------------------------------------------------------------

1. **Registre transverse aux exercices.** `exercice` est une colonne de
   `actes_autorisation` et de `dossiers_depense`, jamais un decoupage de
   fichier ni de table. Aucune requete de ce lot ne prend un `year` obligatoire.
   Le seul critere de periode qui fait foi est **la date**: le cumul d'une
   delegation se calcule sur `dossiers_depense.date_depense` compare a
   `valide_du`/`valide_au` de la delegation, pas sur l'exercice. Une delegation
   votee en 2023 couvre donc une depense de 2024 sans rien de special a ecrire.

2. **Les corrections humaines survivent a la re-extraction.** `origine` entre
   dans la **cle primaire** de chaque table, comme la voie convocations l'a
   deja fait. Une ligne `CORRIGE_HUMAIN` et une ligne `EXTRAIT` du meme objet
   coexistent; la couche partagee `gouvernance_store` ne detruit jamais la
   premiere. Ce qui manquait, et qui est ici: **quelle ligne est lue**. La vue
   `v_actes` repond une fois pour toutes - la correction humaine gagne a la
   lecture - et `v_divergences_humaines` garde la divergence visible, parce que
   l'ecart entre ce que la machine a lu et ce qu'un humain a corrige est
   lui-meme une information.

3. **L'identite d'un acte est stable.** `acte_id` derive du couple
   (date d'assemblee, numero de resolution). Jamais d'une empreinte du texte.
   Voir `acte_id_resolution` pour le cas ou la date manque - il est mesure sur
   donnees reelles et il n'est pas theorique.

4. **Pas de troisieme source de verite.** Ces tables vivent dans le MEME
   fichier `gouvernance.sqlite3` que `resolutions`, `convocations`,
   `devis_cites` et `declarations_ag`, sous `settings.vault.local_root`, et
   passent par la MEME couche `vault.gouvernance_store`. Rien n'est ajoute a la
   base de reconstruction. Raison corrigee le 2026-09-08: une table posee la
   sans recorder n'y est PAS effacee - `_reset_schema` est une liste explicite
   de `DROP TABLE IF EXISTS`. Elle survit, desynchronisee, pendant que tout
   autour se reconstruit depuis les evenements, et rien ne le signale.

----------------------------------------------------------------------
Invariants et variants
----------------------------------------------------------------------

Critere pose par Brice le 2026-09-03: le but n'est pas de traiter parfaitement
le PDF d'un syndic, c'est de savoir **ou il y a de la variation et ou il y a des
invariants**, pour que les traitements tournent en local chez le syndic suivant.

Ce qui structure les tables du noyau est **impose par la loi 65-557 et le decret
67-223**, donc vrai chez tous les syndics:

- une resolution a un numero, une majorite requise et une issue;
- une delegation au conseil syndical a une duree bornee et un plafond
  (art. 21-2, 21-3), et ne peut porter sur trois matieres (art. 21-1);
- une depense engagee en urgence appelle une assemblee (decret art. 37);
- une depense a un montant et une date, et elle est autorisee ou elle ne l'est
  pas.

Ce qui n'existe que parce qu'un syndic le produit est un **variant**, et un
variant ne prend jamais une colonne du noyau: il va dans `attributs_acte`, et
son absence n'est pas un defaut. Exemples deja mesures sur deux corpus:
`Base de repartition : CHARGES COMMUNES GENERALES` enonce par resolution chez un
syndic et absent chez l'autre; une reference de dossier `S.0209.AG5999`; un
libelle de majorite ecrit `Article24` sans espace.

**Le variant le plus couteux, et il est mesure.** Chez le syndic A, le devis vit
dans le corps de la resolution; chez le syndic B, la convocation ne porte aucun
corps de resolution et le devis arrive en fichier voisin
(`.../2026/2026-06-29_AG_Convoc-Devis.pdf`, et la convocation dit
`Piece jointe N.10 pour la resolution 19.2 - Devis benjamin 2026 04 15 SVLM.pdf`).
La MEME information vit donc **des deux cotes du lien** selon le syndic.

Deux consequences tenues par le schema:

1. `liens_gouvernance.target_kind` est **polymorphe**. Un `DEVIS_RETENU` vise
   une ligne de `devis_cites` quand le devis est cite dans la convocation, et un
   `document` quand il arrive en fichier voisin. Aucune contrainte de cle
   etrangere ne fige ce choix, et c'est deliberé.
2. La vue `v_acte_effectif` resout `entreprise` et `montant` **sans supposer de
   quel cote ils se trouvent**: la colonne de l'acte d'abord, le devis lie
   ensuite. Aucun predicat ne lit directement `actes_autorisation.entreprise`.

**Ce que le noyau refuse de porter, et c'est aussi de la generalisabilite.** Il
n'y a aucune colonne de texte integral. Les proces-verbaux du second corpus
nomment les opposants et les abstentionnistes ligne a ligne, avec leurs
tantiemes. Une colonne `texte` aurait aspire ces noms dans le magasin de
gouvernance, chez tous les syndics, sans qu'aucun ecran ne le demande.

----------------------------------------------------------------------
Ce que le schema doit rendre impossible
----------------------------------------------------------------------

La cellule `Decision / devis` de l'ecran comptes decide aujourd'hui son statut
en cherchant les mots `decision`, `devis`, `vote` dans la concatenation de
TOUTES les valeurs de la ligne (`web/compta_rapprochement_view.py`,
`_decision_cell_status` et `_row_text`). Une cellule de preuve dont la valeur ne
provient d'aucune donnee.

Le remede n'est pas de mieux ecrire ce balayage: c'est que la question
`cet euro, qui l'a autorise ?` ait une reponse **structurelle**, un
`EXISTS` sur `liens_gouvernance`. `_actes_requetes` en fait un contrat teste.
"""

from __future__ import annotations

import re
import unicodedata

from ._actes_dates import (  # noqa: F401 - re-export volontaire
    DateNonOrdonnable,
    date_iso,
)
from ._montants import (  # noqa: F401 - re-export volontaire
    MontantIllisible,
    montant_decimal,
    montant_normalise,
    sql_reel,
    sql_taux,
    taux_normalise,
)
from ._actes_vocabulaire import *  # noqa: F401,F403 - re-export volontaire
from ._actes_vocabulaire import (
    NATURE_DECISION_CS,
    NATURE_URGENCE,
    REL_FONDE_PAR,
    REL_RATIFIE_PAR,
    REL_REND_COMPTE_A,
)

# --------------------------------------------------------------------------
# Les exigences de lien - c'est ici que la nature derivee porte son lien
# --------------------------------------------------------------------------

#: (nature, relation, sens, regle d'echeance).
#:
#: **C'est la reponse a la question "comment un acte de nature derivee porte son
#: lien arriere obligatoire".** Pas par une colonne `fonde_par_acte_id`: une
#: colonne ne peut porter qu'une assertion, et son absence est un NULL que rien
#: ne nomme. Ici l'exigence est une donnee jointe a l'acte, donc:
#:
#: - l'absence du lien est une **ligne** de `v_liens_manquants`, pas un trou;
#: - elle porte le nom de sa relation, donc un constat different par relation;
#: - plusieurs liens concurrents peuvent la satisfaire, avec leur provenance;
#: - aucune branche Python par nature: le predicat est une jointure.
#:
#: `RESOLUTION_AG` n'y figure pas. C'est ainsi que "une seule nature est
#: autonome" est ecrit dans le schema plutot que dans un commentaire.
EXIGENCES_LIEN: tuple[tuple[str, str, str, str], ...] = (
    (NATURE_DECISION_CS, REL_FONDE_PAR, "ARRIERE", "DELEGATION_EN_VIGUEUR"),
    (NATURE_DECISION_CS, REL_REND_COMPTE_A, "AVANT", "AG_APPROBATION_COMPTES"),
    (NATURE_URGENCE, REL_RATIFIE_PAR, "AVANT", "AG_SUIVANTE"),
)

# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------

TABLE_ACTES = "actes_autorisation"
ACTE_FIELDS = [
    "acte_id",
    "nature",
    "etat",
    "portee",
    "date_effet",       # ISO. '' quand elle n'a pas ete lue: voir acte_id_resolution
    "exercice",         # colonne, jamais un decoupage
    "ag_id",
    "numero",
    # La numerotation est hierarchique chez au moins un syndic du corpus:
    # `resolution 5.0`, `19.2`, `22.5`. Un `numero` unique aurait ecrase 19.0,
    # 19.2 et 19.4 sur le meme acte des le premier tri `CAST(numero AS INTEGER)`.
    # La voie convocations portait deja `numero`/`sous_numero`: le noyau s'aligne
    # plutot que d'inventer une troisieme convention.
    "sous_numero",
    "objet",
    "montant_autorise",
    "entreprise",
    # Ou l'affirmation a ete lue. C'est la reponse a "ne pas supposer de quel
    # cote du lien une information se trouve": le fait est un invariant, sa
    # localisation est un variant, et une colonne qui **nomme** la localisation
    # vaut mieux qu'une colonne qui la presume.
    "montant_source",     # CORPS_RESOLUTION | ORDRE_DU_JOUR | DEVIS_LIE | ANNEXE | ABSENT
    "entreprise_source",  # meme vocabulaire
    "valide_du",        # fenetre de validite: art. 21-3, deux ans au plus
    "valide_au",
    # Trois majorites, et ce ne sont pas la meme chose. `annoncee` est ce que le
    # document ecrit - vocabulaire de la voie resolutions, y compris sa valeur
    # `NON_ENONCEE`, mesuree une fois sur 55 au 03/07/2024. `requise` est ce que
    # la loi exige pour cet objet. `appliquee` est ce que l'assemblee a fait.
    # Les confondre rendrait impossible le seul controle qui en sort: annoncee
    # contre requise, avec la passerelle de l'article 25-1 pour ne pas crier au
    # faux positif.
    "majorite_annoncee",
    "majorite_requise",
    "majorite_appliquee",
    "resultat",
    "resolution_id",    # provenance dans la table `resolutions`, '' sinon
    "page",
    "ancre",
    "confiance",
    "doc_id",           # exige par gouvernance_store: document d'origine
    "origine",          # exige par gouvernance_store: EXTRAIT | CORRIGE_HUMAIN
]
#: **`etat` est dans la cle.** Corrige le 2026-09-04. Le vocabulaire declare
#: deux etats - `PROJETEE`, lu dans une convocation, et `CONSTATEE`, lu dans un
#: proces-verbal - et `acte_id_resolution` derive le MEME identifiant pour les
#: deux, puisque ce sont la meme date d'assemblee et le meme numero. Sans
#: `etat` dans la cle, l'`INSERT OR REPLACE` de la couche partagee faisait
#: ecraser le premier par le second.
#:
#: Mesure: ecriture du projet depuis la convocation - une ligne, `PROJETEE`,
#: montant 18 240,00 issu du devis; puis ecriture du constat depuis le
#: proces-verbal - une seule ligne en table, `CONSTATEE`, montant vide. Le
#: montant du devis etait perdu, et `v_divergences_humaines` ne montrait rien
#: puisqu'elle ne compare que EXTRAIT contre CORRIGE_HUMAIN. Ce n'etait pas la
#: suppression par `doc_id` - les deux doc_id different - c'etait la cle.
#:
#: L'ecart entre ce qui etait propose et ce qui a ete vote devenait donc
#: structurellement impossible, alors que la table voisine `resolutions` le
#: tient depuis toujours par exactement le meme moyen: `CLES_RESOLUTIONS =
#: ('resolution_id', 'etat', 'origine')`, "pour que l'ecart entre ce qui etait
#: propose et ce qui a ete vote soit un tri". Chez le cabinet ou le devis n'est
#: nomme que par la convocation, c'etait le montant lui-meme qui disparaissait
#: a la lecture du proces-verbal.
#:
#: Consequence portee par les vues: `v_actes` rend desormais jusqu'a deux
#: lignes par `acte_id`, une par etat. Les vues qui reduisent a une ligne par
#: acte groupent et joignent donc sur le couple `(acte_id, etat)`.
ACTE_CLES = ("acte_id", "etat", "origine")
ACTE_ORDRE = (
    "date_effet DESC, CAST(numero AS INTEGER), CAST(sous_numero AS INTEGER), acte_id"
)

TABLE_ATTRIBUTS = "attributs_acte"
#: **La zone d'extension.** Tout fait qu'un syndic enonce et qu'un autre n'enonce
#: pas se range ici, avec sa provenance et son ancrage. Rien n'y est obligatoire,
#: et une absence n'y est jamais un defaut - c'est la difference exacte entre un
#: variant et un invariant.
#:
#: L'alternative aurait ete d'ajouter une colonne au noyau a chaque syndic
#: nouveau. Au troisieme syndic, la table porterait des colonnes vides pour les
#: deux premiers, et plus personne ne saurait dire si un vide est une absence de
#: donnee ou une absence de sens. Ici, la question ne se pose pas: une ligne
#: absente est une chose que ce syndic n'ecrit pas.
#:
#: Ce n'est pas un fourre-tout: un fait qui devient invariant - present chez tous
#: les syndics observes ET requis par un controle legal - doit **migrer** vers
#: une colonne du noyau. `nom` est donc un vocabulaire, pas un champ libre.
ATTRIBUT_FIELDS = [
    "attribut_id",
    "acte_id",
    "nom",              # vocabulaire, pas texte libre
    "valeur",
    "provenance",
    "page",
    "ancre",
    "doc_id",
    "origine",
]
ATTRIBUT_CLES = ("attribut_id", "origine")
ATTRIBUT_ORDRE = "acte_id, nom"

#: Vocabulaire des attributs variants deja observes sur les deux corpus. La
#: liste n'est pas fermee - c'est le propre d'une zone d'extension - mais elle
#: est nommee, pour qu'un meme fait ne soit pas range sous deux noms.
ATTRIBUTS_CONNUS = (
    "base_repartition",      # "CHARGES COMMUNES GENERALES", enonce par resolution
    "cle_repartition",       # cle de charges citee par le projet de resolution
    "reference_dossier",     # "S.0209.AG5999" cote syndic
    "libelle_majorite_brut", # "Article24" sans espace, tel qu'ecrit
    "piece_jointe_nommee",   # "Piece jointe N.10 pour la resolution 19.2 - ..."
    "penalite_retard",
    "duree_contrat",
    # Ajoutes le 2026-09-04 par le pont registre -> modele, qui est le premier
    # ecrivain reel de cette zone. Les trois premiers sont des variants au sens
    # d'origine: un cabinet les enonce, l'autre non.
    "exercice_vise",         # l'exercice que la resolution ARRETE ou VOTE, qui
                             # n'est pas celui ou elle est prise: une assemblee
                             # de 2024 arrete des comptes de 2023
    "discordance_intitule_corps",  # l'intitule annonce un montant ou une duree,
                                   # le corps en decide un autre
    "analyse_offres_affirmee",     # la convocation affirme qu'une analyse des
                                   # offres a eu lieu, sans la joindre
    "passerelle_25_1_utilisee",    # l'assemblee a procede au second vote
    # Les trois suivants ne sont PAS des variants d'ecriture: ce sont des
    # valeurs derivees, ecrites avec `provenance = COPROSCOPE_CALCULE` et
    # produites par `_decompte_voix`, seul module autorise a rapporter des voix
    # a une assiette. Les ranger ici etend l'intention de la zone, et c'est
    # assume: l'alternative etait d'ajouter au noyau une colonne par valeur
    # derivee, donc de figer dans le schema ce qui doit pouvoir changer avec la
    # regle. Le jour ou l'une d'elles devient un controle exige partout, elle
    # migre vers une colonne - c'est la regle deja posee plus haut.
    "assiette_du_decompte",
    "part_des_voix_pour",
    "denominateur_imprime_divergent",
    # Les voix TELLES QUE LE PROCES-VERBAL LES ECRIT, nommees ici a la demande
    # du lot registre qui en est l'ecrivain. Enoncees par la piece, donc de
    # provenance SYNDIC_AFFIRME et non derivees. Sans elles, le controle qui
    # distingue « adoptee » de « declaree adoptee sans atteindre la majorite »
    # se reconstituait depuis le registre et pas depuis le modele. Elles
    # restent en zone d'extension: un cabinet du corpus ne chiffre aucune voix
    # sur une resolution sur deux, et une colonne de noyau vide sur la moitie
    # des actes ferait croire a un manquement la ou il n'y a qu'un cabinet qui
    # n'ecrit pas ses decomptes.
    "voix_pour",
    "voix_contre",
    "voix_abstention",
    "denominateur_imprime",
    "voix_relevees_brutes",
    "passerelle_25_1_citee",
    # Pourquoi le type n'a pas ete reconnu. `ORDINAIRE` veut dire « portee non
    # determinee » et garde les sept controles - c'est la bonne regle. Mais la
    # RAISON du non-typage etait jetee au versement: l'ecran affichait « Type
    # non reconnu » sans dire si le corps n'avait pas pu etre relu, si la
    # periode etait illisible ou si un marche n'avait pas de montant. Trois
    # causes tres differentes, un seul mot a l'ecran.
    "portee_non_reconnue_motif",
)

TABLE_LIENS = "liens_gouvernance"
LIEN_FIELDS = [
    "lien_id",
    "source_kind",
    "source_id",
    "relation",
    "target_kind",
    "target_id",
    "provenance",
    "force_probatoire",
    "motif",            # phrase interpolee et distinctive: reponse au trou T5
    "doute",
    "montant_impute",   # l'euro que ce lien impute a l'acte, pour le cumul
    # Libelle court de la cible, porte par le lien et non par la cible.
    # Motif: la cible n'a pas la meme forme selon le syndic - une ligne de
    # `devis_cites` quand le devis est cite dans la convocation, un `document`
    # quand il arrive en fichier voisin. Une cellule de matrice ne peut pas
    # dependre de la forme de la cible pour afficher `WE GROUP, 18 240,00 EUR`.
    "libelle_cible",
    "echeance",         # date limite d'un lien AVANT, '' pour un lien ARRIERE
    "constate_le",
    "auteur",
    "page",
    "ancre",
    "doc_id",
    "origine",
]
#: `lien_id` porte deja la provenance, donc deux assertions concurrentes ont
#: deux cles distinctes sans qu'aucune contrainte ne les oppose. `origine`
#: complete la cle pour la meme raison que partout ailleurs.
LIEN_CLES = ("lien_id", "origine")
LIEN_ORDRE = "source_id, relation, provenance"

TABLE_DOSSIERS = "dossiers_depense"
DOSSIER_FIELDS = [
    "dossier_id",
    "exercice",         # colonne, jamais un decoupage
    "date_depense",     # c'est ELLE qui sert au cumul, pas l'exercice
    "montant_ttc",
    "fournisseur",
    "libelle",
    "imputation",
    "imputation_motif",
    # T.V.A.: ce que la comptabilite a retenu et ce que la piece annonce, cote a
    # cote. Jamais fusionnes: l'ecart entre les deux est le livrable, et une
    # colonne unique le ferait disparaitre en le corrigeant.
    "montant_ht",
    "taux_tva_annonce",   # taux porte par la PIECE
    "tva_annoncee",       # T.V.A. retenue par la LIGNE COMPTABLE
    "tva_regime",         # NORMAL | NON_APPLICABLE | EXONERE
    "aiguillage",       # ART_44 | ART_45_MAINTENANCE | NON_TESTE
    "facture_doc_id",
    "ecriture_ref",
    "page",
    "ancre",
    "doc_id",
    "origine",
]
DOSSIER_CLES = ("dossier_id", "origine")
DOSSIER_ORDRE = "date_depense DESC, dossier_id"

TABLE_TRACES = "traces_controle"
TRACE_FIELDS = [
    "trace_id",
    "sujet_kind",
    "sujet_id",
    "verdict",          # CONTROLE_TRACE | RESERVE | QUESTION_POSEE
    "texte",
    "auteur",
    "constate_le",
    "doc_id",           # '' le plus souvent: une trace ne derive pas d'un document
    "origine",          # toujours CORRIGE_HUMAIN
]
TRACE_CLES = ("trace_id", "origine")
TRACE_ORDRE = "constate_le DESC, trace_id"

#: Les quatre tables du lot, dans la forme attendue par `_actes_store`.
TABLES: dict[str, tuple[list[str], tuple[str, ...], str]] = {
    TABLE_ACTES: (ACTE_FIELDS, ACTE_CLES, ACTE_ORDRE),
    TABLE_ATTRIBUTS: (ATTRIBUT_FIELDS, ATTRIBUT_CLES, ATTRIBUT_ORDRE),
    TABLE_LIENS: (LIEN_FIELDS, LIEN_CLES, LIEN_ORDRE),
    TABLE_DOSSIERS: (DOSSIER_FIELDS, DOSSIER_CLES, DOSSIER_ORDRE),
    TABLE_TRACES: (TRACE_FIELDS, TRACE_CLES, TRACE_ORDRE),
}

#: Index a poser en plus de ceux que `gouvernance_store.ensure_schema` derive
#: seul (`doc_id`, `ag_id`). Ils existent pour une raison precise: le contrat de
#: filtrage de `_actes_requetes` promet qu'aucune colonne de la matrice ne coute
#: un balayage. Une jointure non indexee tiendrait la promesse a 34 lignes et la
#: romprait a 700.
INDEX: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (TABLE_LIENS, "idx_liens_source", ("source_kind", "source_id", "relation")),
    (TABLE_LIENS, "idx_liens_target", ("target_kind", "target_id", "relation")),
    (TABLE_ACTES, "idx_actes_nature", ("nature", "etat")),
    (TABLE_ACTES, "idx_actes_portee", ("portee", "date_effet")),
    (TABLE_DOSSIERS, "idx_dossiers_date", ("date_depense",)),
    (TABLE_TRACES, "idx_traces_sujet", ("sujet_kind", "sujet_id")),
    (TABLE_ATTRIBUTS, "idx_attributs_acte", ("acte_id", "nom")),
)

# --------------------------------------------------------------------------
# Identite
# --------------------------------------------------------------------------

_NON_ALNUM = re.compile(r"[^A-Za-z0-9]+")

#: Les colonnes de date du lot, par table. La regle qu'elles doivent tenir -
#: toute comparaison de droit du modele est une comparaison de chaines, donc
#: toutes les chaines doivent etre ordonnables - est portee par
#: `_actes_dates`, avec les deux erreurs de sens oppose qui l'ont motivee.
COLONNES_DATE: dict[str, tuple[str, ...]] = {
    TABLE_ACTES: ("date_effet", "valide_du", "valide_au"),
    TABLE_LIENS: ("echeance", "constate_le"),
    TABLE_DOSSIERS: ("date_depense",),
    TABLE_TRACES: ("constate_le",),
}


#: Marque des actes dont la date d'assemblee n'a pas ete lue. Elle est dans
#: l'identifiant a dessein: un acte degrade ne doit jamais pouvoir etre confondu
#: avec un acte date, y compris dans un journal ou une trace de test.
MARQUE_SANS_DATE = "SANS-DATE"


def _jeton(valeur: str) -> str:
    texte = unicodedata.normalize("NFKD", str(valeur or ""))
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    return _NON_ALNUM.sub("-", texte).strip("-").upper()


def acte_id_resolution(
    date_ag: str, numero: str, *, sous_numero: str = "", doc_id: str = ""
) -> str:
    """Identifiant d'un acte de nature `RESOLUTION_AG`.

    Decision back n. 3: derive du couple (date d'AG, numero), **jamais** d'une
    empreinte du texte. Un nouvel OCR qui change une virgule ne doit pas
    fabriquer un doublon.

    **Correction imposee par le second corpus.** Un syndic numerote ses
    resolutions `5.0`, `19.2`, `22.5`. Le couple (date, numero) seul aurait
    donne le meme identifiant a `19.0`, `19.2` et `19.4` - trois resolutions
    distinctes, dont deux portant chacune leur devis en piece jointe nommee. Le
    sous-numero entre donc dans l'identite. Il est vide chez le syndic qui ne
    sous-numerote pas, et un sous-numero vide ne change pas l'identifiant: les
    identifiants deja produits sur le premier corpus restent valides.

    **Le cas ou la date manque n'est pas theorique, il est mesure.** Dans
    `gouvernance.sqlite3` de `tilleuls_test` au 2026-09-03, la table
    `resolutions` porte 118 lignes reparties ainsi:

        AG-2024-07-03        DOC-7139EDAD85E4   55 lignes
        AG-DOC-729CCCF88863  DOC-729CCCF88863   55 lignes
        AG-2026-02-26        DOC-E67768CA7ACD    8 lignes

    Deux assemblees de 55 resolutions, dont une identifiee par un `doc_id`
    parce que sa date n'a pas ete lue. C'est exactement le repli que la decision
    n. 3 interdit, et il est deja dans la base: l'identifiant redevient
    document-dependant des que la date manque, donc le meme proces-verbal relu
    autrement fabriquerait une troisieme assemblee.

    Ce que fait cette fonction a la place: elle **admet** l'acte sans date, mais
    elle marque son identifiant `SANS-DATE`, ce qui a trois consequences.
    L'acte ne peut pas etre pris pour un acte date. Il produit un constat
    `PV_SANS_DATE_LUE` au niveau du document - une ligne, pas cinquante-cinq.
    Et le jour ou un humain corrige la date, l'acte date s'ecrit **a cote**,
    la divergence reste lisible, et rien n'est promu en silence.

    Ce que cette fonction ne fait pas: deviner. Deux assemblees de meme
    cardinalite ne sont pas reputees identiques - ce serait conclure sur une
    ressemblance, c'est-a-dire le defaut que tout ce lot combat.
    """
    numero_norme = _jeton(numero) or "0"
    suffixe = _jeton(sous_numero)
    if suffixe and suffixe != "0":
        numero_norme = f"{numero_norme}-{suffixe}"
    # La date est ramenee a l'ISO avant d'entrer dans l'identifiant. Sans cela,
    # `03/07/2024` rendait ACTE-AG-03-07-2024-R12 et `2024-07-03` rendait
    # ACTE-AG-2024-07-03-R12: deux actes pour une seule resolution, une
    # assemblee de plus dans tous les comptages, aucune erreur levee. Mesure du
    # 2026-09-04.
    date_norme = date_iso(date_ag)
    if date_norme:
        return f"ACTE-AG-{_jeton(date_norme)}-R{numero_norme}"
    return f"ACTE-AG-{MARQUE_SANS_DATE}-{_jeton(doc_id)}-R{numero_norme}"


def acte_id_decision_cs(date_decision: str, rang: int, *, doc_id: str = "") -> str:
    """Identifiant d'une decision du conseil syndical prise sur delegation.

    Meme principe: la date de la decision et son rang dans la seance. Le rang
    remplace le numero de resolution, qui n'existe pas ici.
    """
    date_norme = date_iso(date_decision)
    if date_norme:
        return f"ACTE-CS-{_jeton(date_norme)}-D{rang:03d}"
    return f"ACTE-CS-{MARQUE_SANS_DATE}-{_jeton(doc_id)}-D{rang:03d}"


def acte_id_urgence(date_engagement: str, rang: int, *, doc_id: str = "") -> str:
    """Identifiant d'une depense engagee en urgence par le syndic."""
    date_norme = date_iso(date_engagement)
    if date_norme:
        return f"ACTE-URG-{_jeton(date_norme)}-U{rang:03d}"
    return f"ACTE-URG-{MARQUE_SANS_DATE}-{_jeton(doc_id)}-U{rang:03d}"


def lien_id(
    source_kind: str,
    source_id: str,
    relation: str,
    target_kind: str,
    target_id: str,
    provenance: str,
) -> str:
    """Identifiant d'une assertion de lien.

    Lisible et non hache, a dessein: un identifiant de lien se lit dans un
    journal, dans un test et dans un message d'erreur.

    La provenance entre dans l'identifiant. C'est ce qui fait coexister
    plusieurs assertions concurrentes sur la MEME paire sans qu'aucune
    contrainte ne les oppose: le syndic affirme que la facture releve de la
    resolution 12, CoproScope calcule le contraire, un humain tranche. Trois
    lignes, trois identifiants, aucun ecrasement.

    Deriver l'identite d'un lien de ses extremites n'est pas contraire a la
    decision n. 3: elle interdit de deriver l'identite d'une **empreinte de
    texte**, parce que le texte bouge a chaque OCR. Les extremites d'un lien ne
    bougent pas - si elles bougent, ce n'est plus le meme lien.
    """
    return f"{source_kind}:{source_id}|{relation}|{target_kind}:{target_id}|{provenance}"


# --------------------------------------------------------------------------
# Montants
# --------------------------------------------------------------------------

def montant_texte(valeur: object) -> str:
    """Forme canonique d'un montant, pour une colonne TEXT.

    La couche partagee stocke tout en TEXT. Les vues comparent donc ce TEXT a
    un nombre, et cette fonction garantit que la comparaison porte sur ce qu'on
    croit: `18 240,00 EUR` devient `18240.00`.

    Un montant absent rend la chaine vide, jamais `0`. La difference est
    exactement celle que le blueprint demande de tenir: `rien de paye a ce jour`
    n'est pas `paye zero euro`, et un `0` implicite fausserait le cumul.

    **Un montant ecrit et illisible leve `MontantIllisible`.** La version
    precedente rendait `2.50` pour `2.500` et `""` pour `abc`: un plafond de
    2 500 EUR devenait 2,50 EUR, le controle de l'article 21-2 ne se
    declenchait plus, et rien ne le disait. La regle unique vit desormais dans
    `_montants`, et elle refuse ce qu'elle ne sait pas lire.
    """
    return montant_normalise(valeur)


def montant_nombre(valeur: object) -> float | None:
    """Le montant en flottant, ou `None` s'il est **absent**.

    Leve `MontantIllisible` comme `montant_texte`. Un appelant qui affiche un
    nombre doit pouvoir separer "aucun montant" de "un montant que je n'ai pas
    su lire": ce sont deux phrases differentes a l'ecran.
    """
    montant = montant_decimal(valeur)
    return float(montant) if montant is not None else None
