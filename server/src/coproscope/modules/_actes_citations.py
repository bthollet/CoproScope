"""Le lien retenu par une cellule, l'ordre qui le retient, et de quoi le citer.

Extrait de `_actes_vues` le 2026-09-07. Ce module-la etait a 600 lignes
exactement pour une limite dure de 600: la citation de source ne pouvait pas y
entrer sans la depasser, et la regle du depot est d'extraire avant d'ajouter.

**Pourquoi l'ordre de probation et la citation vivent dans le meme module.**
Une cellule de `v_matrice_gouvernance` n'affiche pas la force probatoire d'un
lien quelconque: elle affiche celle du lien RETENU, designe par un `ORDER BY`
suivi d'un `LIMIT 1`. Une citation ecrite avec une seconde requete, meme tres
proche, citerait la page d'une assertion DIFFERENTE de celle dont l'ecran
affiche la force. L'ecran dirait alors `devis au dossier` en pointant la page
d'un devis seulement affirme - un mensonge silencieux, et precisement dans le
lot charge d'ajouter de l'honnetete.

Ici la designation est ecrite une fois, dans `lien_retenu`. La force affichee et
la page citee sortent forcement du meme sous-select, et rien n'est laisse au
soin de recopier l'ordre correctement.

**Ce module ne connait aucune modalite observee.** Il ne suppose ni qu'une page
est renseignee, ni qu'une ancre l'est, ni que le document qui porte l'assertion
est celui d'ou l'acte a ete lu. Mesure du 2026-09-07 sur deux coffres: sur 280
liens, 20 n'ont pas de page et ont une ancre; l'inverse est possible et n'a pas
ete rencontre. Les colonnes rendent une chaine vide dans les deux cas, et
l'ecran dit ce qui manque au lieu de le combler.

----------------------------------------------------------------------
Deux questions differentes appellent deux ordres differents
----------------------------------------------------------------------

Ajoute le 2026-09-08 (`RM-2026-0072`). Le module n'avait qu'un ordre, et il
servait aux cinq relations.

Cet ordre unique est **le bon** pour une assertion sur un FAIT: *quel est le
montant de ce devis* se tranche par la force de la preuve, parce qu'une piece
produite en dit plus long qu'une affirmation sans piece. Il est **le mauvais**
pour une NORME posee par un vote: *quel est le seuil applicable* ne se tranche
pas par la qualite du papier. Arbitrage de Brice, donne deux fois le
2026-09-08 a deux fils independamment: *la question des seuils, c'est le
dernier qu'il faut retenir; la question de l'ambiguite ne se pose pas, c'est le
dernier vote*.

**L'axe, et il est plus large que les seuils.** Ce que la relation porte est un
degre de liberte: un CONSTAT sur une piece, ou une NORME votee. Ce qui reste
vrai le long de l'axe est qu'une relation appartient a l'une ou a l'autre, et
que l'ordre suit ce que la relation porte - jamais l'inverse. D'ou
`ORDRE_PAR_RELATION`, qui declare les sept **explicitement**: aucune relation
n'herite d'un defaut, et une relation ajoutee sans y figurer est refusee au
lieu de prendre l'ordre du voisin en silence.

**Ce qu'un ordre chronologique exige de plus.** La date qui compte est celle de
la DELIBERATION, et le lien ne la porte pas: `constate_le` est la date a
laquelle l'assertion a ete enregistree. La date du vote vit sur l'acte VISE,
en `date_effet`. L'ordre chronologique porte donc sa propre jointure, et cette
jointure peut ne rien trouver - `target_kind` est polymorphe par conception.

**La garde, et c'est elle le livrable.** Un `ORDER BY` rend toujours une ligne,
meme quand rien ne la designe. L'ancien ordre finissait par `l.lien_id`: deux
assertions egales sur tout le reste etaient donc departagees par un
identifiant, c'est-a-dire par le rang de la resolution dans la convocation.
Un identifiant n'est pas une chronologie. L'ordre chronologique n'a **aucun**
departage de secours, et `combien_ex_aequo` compte combien de cibles distinctes
restent a egalite au sommet. Deux, ou une date illisible, et l'ecran declare
`non tranche` au lieu de choisir.
"""

from __future__ import annotations

from typing import NamedTuple

from ._actes_seuils_normes import ENTREES_SEUIL


class Ordre(NamedTuple):
    """Ce qui designe le lien retenu, et de quoi mesurer s'il est seul.

    Quatre morceaux qui vont ensemble et ne se recopient pas separement:

    - `jointure` est ce qu'il faut aller chercher hors du lien pour trancher.
      Vide quand le lien se suffit;
    - `cle` est **la valeur qui decide**, rendue en texte. Deux liens de meme
      cle sont a egalite: c'est la definition de l'ex aequo, et elle est
      exacte, pas approchee;
    - `tri` est l'`ORDER BY`. Il ne contient jamais de departage de secours:
      un ordre qui tranche toujours empeche de savoir qu'il n'a rien tranche;
    - `nom` sert aux messages et aux tests, pour que l'ecart entre l'intention
      et le SQL se lise.
    """

    nom: str
    jointure: str
    cle: str
    tri: str


#: **L'ordre d'une assertion sur un FAIT.** Quand plusieurs assertions portent
#: sur le meme couple, celle qui fait foi est la plus probante: un humain avant
#: CoproScope avant le syndic, puis une piece produite avant une affirmation
#: sans piece.
#:
#: Il etait ecrit dans `_cellule()` et nulle part ailleurs. `v_acte_effectif`
#: prenait son devis par un `LIMIT 1` **sans ORDER BY**, c'est-a-dire dans
#: l'ordre ou SQLite se trouvait rendre les lignes. Mesure du 2026-09-04 sur
#: les deux devis de l'etalon: un `SYNDIC_AFFIRME` / `AFFIRME_SANS_PIECE` a
#: 22 200,00 et un `HUMAIN_CONFIRME` / `PIECE_PRODUITE` a 18 240,00 sur le meme
#: acte donnaient `montant_effectif = 22200.00` et `entreprise = CHER`, pendant
#: que `cel_devis` de la MEME ligne affichait `PIECE_PRODUITE`. Deux ordres de
#: tri pour un meme ensemble de liens dans une meme vue: la cellule disait
#: `confirme par un humain` a cote d'un montant pris chez le syndic, et le
#: choix pouvait basculer a une reconstruction sans changement de code.
#:
#: `l.lien_id` reste en fin de tri ici, et ce n'est pas un oubli: il rend le
#: resultat stable d'une reconstruction a l'autre. Mais il departage bel et
#: bien deux assertions egales, donc `combien_ex_aequo` compte aussi sur cet
#: ordre-la, et l'egalite s'y voit au lieu d'etre absorbee.
ORDRE_PROBANT = Ordre(
    nom="probant",
    jointure="",
    cle="l.provenance || '/' || l.force_probatoire",
    tri="""
        ORDER BY CASE l.provenance
                    WHEN 'HUMAIN_CONFIRME' THEN 0
                    WHEN 'COPROSCOPE_CALCULE' THEN 1
                    WHEN 'SYNDIC_AFFIRME' THEN 2 ELSE 3 END,
                 CASE l.force_probatoire
                    WHEN 'PIECE_PRODUITE' THEN 0
                    WHEN 'AFFIRME_SANS_PIECE' THEN 1 ELSE 2 END,
                 l.lien_id
""",
)

#: **L'ordre d'une NORME posee par un vote.** La derniere deliberation abroge
#: la precedente, quelle que soit la qualite de la piece qui atteste l'ancienne.
#:
#: La jointure va chercher `date_effet` sur l'acte VISE, parce que le lien ne
#: porte pas la date du vote. Elle est un `LEFT JOIN` garde par
#: `l.target_kind = 'acte'`: un lien qui viserait un document - `target_kind`
#: est polymorphe par conception - ne trouve rien, sa cle vaut la chaine vide,
#: et il perd contre toute deliberation datee au lieu de gagner par accident.
#:
#: Le tri s'arrete a la date. Une egalite reste une egalite, et c'est
#: `combien_ex_aequo` qui la rend visible.
ORDRE_CHRONOLOGIQUE = Ordre(
    nom="chronologique",
    jointure=(
        " LEFT JOIN v_actes t"
        " ON t.acte_id = l.target_id AND l.target_kind = 'acte' "
    ),
    cle="COALESCE(t.date_effet, '')",
    tri="ORDER BY COALESCE(t.date_effet, '') DESC",
)

#: Ce qui situe une assertion dans une piece: quelle piece, quelle page, quel
#: endroit dans la page. Les trois sont des degres de precision distincts et
#: manquent independamment - une piece connue sans page reste citable, une page
#: sans piece ne l'est pas.
COLONNES_SOURCE: tuple[str, ...] = ("doc_id", "page", "ancre")

#: relation du modele -> prefixe de colonne, et ce prefixe est deja celui de la
#: cellule (`cel_seuil`, `cel_avis_cs`, ...). Une meme cellule porte un meme
#: mot dans les quatre familles de colonnes: `cel_*` la force, `src_*_*` la
#: source, `nb_*` le nombre d'assertions concurrentes, `cle_*` / `nb_*_ex_aequo`
#: ce qui a tranche et s'il a tranche.
#:
#: Les sept relations y sont, pas seulement celles qu'un coffre s'est trouve
#: porter. Au 2026-09-07, `RAPPORT_CS` et `ANNEXE_VISEE` n'ont aucune ligne dans
#: les deux coffres mesures: les omettre coderait une modalite observee, et le
#: premier lot qui les alimenterait rendrait une cellule sans source, en
#: silence.
#: Les trois entrees de seuil - les deux normes et le residu - sont GENEREES
#: depuis `_actes_seuils_normes` et jamais recopiees ici. Une quatrieme entree
#: declaree la-bas entrerait dans la matrice sans edition de ce module, et
#: l'ecart entre le registre des normes et les colonnes de la vue ne peut donc
#: pas s'installer. C'est le meme motif que `colonnes_citation` plus bas.
CELLULES_LIEES: dict[str, str] = {
    **{n.relation: n.prefixe for n in ENTREES_SEUIL},
    "AVIS_CS": "avis_cs",
    "RAPPORT_CS": "rapport_cs",
    "ANNEXE_VISEE": "annexe",
    "DEVIS_RETENU": "devis",
}

#: **Chaque relation declare son ordre; aucune ne l'herite.** Une relation
#: absente d'ici leve, au lieu de prendre l'ordre du voisin: c'est le seul
#: moyen qu'une sixieme relation ne devienne pas probante par defaut le jour ou
#: elle porterait une norme.
#:
#: Seules les relations de seuil portent une norme votee aujourd'hui, et elles
#: sont TROIS depuis le 2026-09-08: les deux normes de l'article 21 alinea 2 et
#: le residu de celles qu'on n'a pas su attribuer. Les trois se tranchent par la
#: date de la deliberation, et le residu comme les autres: un montant dont on
#: ignore ce qu'il declenche reste un montant vote, donc c'est le dernier qui
#: vaut. `AVIS_CS`, `RAPPORT_CS`, `ANNEXE_VISEE` et `DEVIS_RETENU` portent des
#: constats sur des pieces: le meilleur document gagne, et un document plus
#: recent n'abroge rien.
#:
#: **Ce que la separation change, et c'est le livrable du lot.** L'ordre
#: chronologique s'applique desormais A L'INTERIEUR de chaque norme. Deux
#: montants du meme jour qui repondaient a deux questions differentes ne sont
#: plus mis en concurrence: chacun est seul sur sa relation, donc tranche.
ORDRE_PAR_RELATION: dict[str, Ordre] = {
    **{n.relation: ORDRE_CHRONOLOGIQUE for n in ENTREES_SEUIL},
    "AVIS_CS": ORDRE_PROBANT,
    "RAPPORT_CS": ORDRE_PROBANT,
    "ANNEXE_VISEE": ORDRE_PROBANT,
    "DEVIS_RETENU": ORDRE_PROBANT,
}


class RelationSansOrdre(KeyError):
    """Une relation dont personne n'a dit comment elle se tranche."""


def ordre_de(relation: str) -> Ordre:
    """L'ordre declare pour cette relation, ou une erreur qui la nomme."""
    try:
        return ORDRE_PAR_RELATION[relation]
    except KeyError:  # pragma: no cover - garde de conception
        raise RelationSansOrdre(
            f"La relation {relation!r} ne declare aucun ordre. Une relation qui "
            "porte un CONSTAT sur une piece se tranche par la force probatoire; "
            "une relation qui porte une NORME votee se tranche par la date de la "
            "deliberation. Choisir n'est pas un detail d'implementation: "
            "l'inscrire dans ORDRE_PAR_RELATION."
        ) from None


def _base(relation: str, *, lien_vivant: str) -> str:
    """Les liens de cet acte, pour cette relation, encore vivants."""
    return (
        "l.source_kind = 'acte' AND l.source_id = a.acte_id "
        f"AND l.relation = '{relation}' AND ({lien_vivant})"
    )


def lien_retenu(
    relation: str,
    colonne: str,
    *,
    table: str,
    lien_vivant: str,
    ordre: Ordre,
    defaut: str = "",
) -> str:
    """LE sous-select qui designe le lien retenu, pour n'importe quelle colonne.

    Un seul endroit ecrit `ORDER BY ... LIMIT 1` sur les liens d'un acte. La
    cellule y prend `force_probatoire`, la citation y prend `doc_id`, `page` et
    `ancre`: quatre colonnes, une seule ligne choisie.

    `ordre` est **obligatoire et nomme**: l'appelant dit par quoi il tranche au
    lieu d'en heriter. Un defaut ici rendrait probante, sans un mot, toute
    relation qu'un lot futur ajouterait.

    `defaut` est la valeur d'une absence de lien. Elle vaut `ABSENT` pour une
    force probatoire - une absence est une information de premier niveau, pas un
    NULL - et la chaine vide pour une source, qui n'a alors rien a nommer.

    **`colonne` peut etre QUALIFIEE**, et c'est ce qui permet de lire une valeur
    de la CIBLE et non du lien: `t.montant_effectif` va chercher le montant de
    l'acte vise par le lien retenu, quand l'ordre joint cette cible. Sans cela
    il faudrait un second sous-select, avec son propre `ORDER BY` - et deux
    `ORDER BY` sur la meme population finissent par retenir deux lignes
    differentes, ce qui est exactement le defaut que cette fonction existe pour
    empecher. Une colonne sans point reste prefixee par `l.`, donc aucun
    appelant existant ne change de sens.
    """
    lue = colonne if "." in colonne else f"l.{colonne}"
    return f"""COALESCE((
        SELECT {lue} FROM {table} l{ordre.jointure}
        WHERE {_base(relation, lien_vivant=lien_vivant)}
        {ordre.tri}
        LIMIT 1), '{defaut}')"""


def cle_retenue(relation: str, *, table: str, lien_vivant: str, ordre: Ordre) -> str:
    """**La valeur qui a tranche**, rendue telle quelle a l'ecran.

    Pour un ordre chronologique c'est la date de la deliberation retenue, et
    l'ecran en a besoin: `le seuil arrete le 2024-07-03` se verifie, `le seuil
    retenu` ne se verifie pas. La chaine vide dit que rien n'a tranche - date
    absente, illisible, ou cible qui n'est pas un acte - et l'ecran doit alors
    se taire sur la date au lieu d'en inventer une.
    """
    return f"""COALESCE((
        SELECT {ordre.cle} FROM {table} l{ordre.jointure}
        WHERE {_base(relation, lien_vivant=lien_vivant)}
        {ordre.tri}
        LIMIT 1), '')"""


def combien(relation: str, *, table: str, lien_vivant: str) -> str:
    """Combien d'assertions VIVANTES portent ce controle sur cet acte.

    `lien_retenu` s'arrete a la premiere, donc se tait quand plusieurs se
    presentent: 65 actes d'un coffre mesure portent deux seuils. Cette colonne
    ne tranche rien, elle rend la pluralite visible - et c'est ce qui permet a
    l'ecran d'ecrire `une assertion sur deux` au lieu de laisser croire qu'elle
    est seule.
    """
    return f"""(SELECT COUNT(*) FROM {table} l
        WHERE {_base(relation, lien_vivant=lien_vivant)})"""


def combien_ex_aequo(
    relation: str, *, table: str, lien_vivant: str, ordre: Ordre
) -> str:
    """Combien de CIBLES DISTINCTES restent a egalite au sommet de cet ordre.

    C'est la mesure qui manquait. `combien` dit qu'il y a deux assertions;
    elle ne dit pas si l'ordre les a departagees. Deux assertions sur le meme
    devis ne sont pas un conflit, deux devis differents a la meme force en sont
    un - d'ou le comptage sur `target_kind:target_id`, l'identite de la cible,
    et non sur le nombre de lignes.

    `1` veut dire tranche. `2` ou plus veut dire que l'ordre n'a pas separe, et
    que la ligne rendue par `LIMIT 1` est un tirage: l'ecran doit le dire.
    `0` veut dire qu'aucune assertion vivante ne porte ce controle.

    La cle comparee est celle de l'ordre lui-meme, ce qui rend l'egalite exacte
    plutot qu'approchee: on ne devine pas ce qui aurait pu departager, on
    compare ce qui a effectivement servi a trancher.
    """
    base = _base(relation, lien_vivant=lien_vivant)
    return f"""COALESCE((
        SELECT COUNT(DISTINCT l.target_kind || ':' || l.target_id)
        FROM {table} l{ordre.jointure}
        WHERE {base} AND ({ordre.cle}) = (
            SELECT {ordre.cle} FROM {table} l{ordre.jointure}
            WHERE {base}
            {ordre.tri}
            LIMIT 1)), 0)"""


def colonnes_citation(*, table: str, lien_vivant: str) -> str:
    """Les colonnes de source, de concurrence et de departage des sept cellules.

    Generees, jamais recopiees: une relation ajoutee a `CELLULES_LIEES` entre
    dans la vue sans edition, et l'ecart entre la liste et la vue ne peut pas
    s'installer. C'est le meme motif que `_divergence`, qui suit `ACTE_FIELDS`.

    Les colonnes de departage sont generees pour les sept et pas seulement pour
    les seuils. N'en produire que la ou un conflit a deja ete rencontre serait
    coder une modalite observee: l'egalite silencieuse existe aussi sur l'ordre
    probant - deux devis de meme provenance et de meme force y sont departages
    par `lien_id` - et une colonne qui la compte la rend mesurable le jour ou
    quelqu'un la regarde.

    Rendu: un fragment de liste de colonnes SQL, virgule finale comprise, a
    inserer dans le `SELECT` de `v_matrice_gouvernance`.
    """
    bouts: list[str] = []
    for relation, prefixe in CELLULES_LIEES.items():
        ordre = ordre_de(relation)
        for colonne in COLONNES_SOURCE:
            bouts.append(
                lien_retenu(relation, colonne, table=table,
                            lien_vivant=lien_vivant, ordre=ordre)
                + f" AS src_{prefixe}_{colonne}"
            )
        bouts.append(
            combien(relation, table=table, lien_vivant=lien_vivant)
            + f" AS nb_{prefixe}"
        )
        bouts.append(
            combien_ex_aequo(relation, table=table,
                             lien_vivant=lien_vivant, ordre=ordre)
            + f" AS nb_{prefixe}_ex_aequo"
        )
        bouts.append(
            cle_retenue(relation, table=table,
                        lien_vivant=lien_vivant, ordre=ordre)
            + f" AS cle_{prefixe}"
        )
    return "".join("    " + bout + ",\n" for bout in bouts)
