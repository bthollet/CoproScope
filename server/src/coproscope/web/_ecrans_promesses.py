# -*- coding: utf-8 -*-
"""Les tables qu'un ecran montre et qu'aucun chemin du produit ne remplit.

Instruction de `RM-2026-0059`. L'item disait *huit ecrans se declarent vides,
mais rien ne permet de les remplir*. La garde soeur
`test_ecrans_sans_instance_declarent_leur_nature` couvre les ecrans qui n'ont
**aucun canal d'entree** - leur constructeur ne prend que des scalaires, donc
ils ne peuvent rien lire. Ce module-ci couvre l'autre moitie, et c'est la plus
sournoise: un ecran qui **a** un canal d'entree, qui lit vraiment une table, et
dont la table ne sera jamais remplie parce qu'aucun chemin du produit ne l'ecrit.

**La difference se voit a l'ecran, et elle ne se voit pas.** Un ecran sans canal
affiche une maquette, et la maquette se reconnait. Un ecran branche sur une
table vide affiche `aucune depense rattachee` ou `A instruire`, ce qui a la
forme exacte d'un CONSTAT sur la copropriete. Le lecteur lit un fait; la verite
est un etat de l'outil. C'est le meme defaut que les quatre `REJETEE` du
2026-09-09, qui etaient des absences de vote.

**Ce que ce module declare, et ce qu'il ne declare pas.** Il nomme les tables
LUES par un ecran et ECRITES par personne. Il ne nomme pas les tables vides: une
table vide dont le chemin existe est une copropriete sans matiere, ce qui est un
fait sur la copropriete et non un trou du produit. La distinction est mesurable
et elle a ete mesuree: sur l'instance etalon du 2026-09-09,
`liens_gouvernance` porte **zero ligne** alors que `pont_actes.verser` l'ecrit a
chaque absorption. Compter les lignes aurait donc range cette table parmi les
orphelines, a tort. Ce qui se mesure est l'ECRITURE, pas le resultat.

**Une entree d'ici n'est pas une dette qu'on tolere: c'est une phrase montree a
l'utilisateur.** Elle sort sous le tableau de l'ecran concerne, dans la liste
des exigences back, pour qu'une limite se voie au lieu d'etre devinee.

**Sortir d'ici est le but.** Le jour ou un geste du produit ecrit la table, la
ligne doit disparaitre - et la garde le fait rougir toute seule, parce qu'elle
compare cette liste a ce que la chaine de production ecrit REELLEMENT.
"""

from __future__ import annotations

from typing import NamedTuple


class PromesseSansChemin(NamedTuple):
    """Une table qu'un ecran montre et qu'aucun chemin du produit n'ecrit."""

    #: Le nom reel de la table dans `gouvernance.sqlite3`. C'est par lui que la
    #: garde recoupe cette declaration avec ce que SQLite voit ecrire.
    table: str
    #: Le titre de l'exigence, tel qu'il sort a l'ecran.
    titre: str
    #: Ce que le lecteur doit comprendre. Il nomme la table, parce qu'une limite
    #: qui ne dit pas sur quoi elle porte ne se leve jamais.
    corps: str


#: Mesure du 2026-09-09 sur `913d744`, par observation SQLite d'une absorption
#: complete: la chaine de production ecrit `actes_autorisation`,
#: `attributs_acte`, `convocations`, `declarations_ag`, `devis_cites`,
#: `liens_gouvernance` et `resolutions`. Elle n'ecrit ni `dossiers_depense` ni
#: `traces_controle`, que seuls les tests remplissent - et l'ecran de controle
#: de gouvernance lit les deux.
SANS_CHEMIN_DE_PRODUCTION: tuple[PromesseSansChemin, ...] = (
    PromesseSansChemin(
        table="dossiers_depense",
        titre="Rattacher un acte à un euro",
        corps=(
            "Aucun geste de l'application n'écrit dans « dossiers_depense », et le lien "
            "« AUTORISE » qui relierait un acte à une dépense n'est posé par aucun chemin. "
            "Tant que c'est le cas, « aucune dépense rattachée » est un état de l'outil et "
            "non un constat sur la copropriété."
        ),
    ),
    # **`traces_controle` est SORTIE d'ici le 2026-09-09, et c'etait le but.**
    # Ce module ecrivait: *« Sortir d'ici est le but. Le jour ou un geste du
    # produit ecrit la table, la ligne doit disparaitre. »* Ce jour est arrive
    # le jour meme, sur l'arbitrage de Brice - « bien evidemment on trace le
    # controle » - et `web/_controle_gouvernance_conclusion.py` l'ecrit.
    #
    # **MAIS LA GARDE NE L'AURAIT PAS VU, et c'est un residu a nommer.** Elle
    # compare cette liste a ce que la CHAINE DE PRODUCTION ecrit, mesure en
    # jouant `core.pipeline.run_pipeline`. Or ce producteur-ci n'est pas dans la
    # chaine: c'est une ROUTE, declenchee par un humain devant l'ecran. Une
    # table ecrite par un geste et non par la chaine serait donc restee declaree
    # orpheline indefiniment, et l'ecran aurait continue d'annoncer un trou
    # comble - exactement le defaut que ce module a trouve sur
    # `actes_autorisation` cinq jours durant.
    #
    # **Ce qui restait a faire a ete fait, et ce commentaire disait faux depuis
    # le 2026-09-09.** Il annoncait que la mesure ne couvrait que la chaine.
    # Elle joue en realite le GESTE aussi: `setUpClass` de la garde appelle
    # `_controle_gouvernance_conclusion.enregistrer`, exactement le remede que
    # ce paragraphe reclamait - *le corpus doit porter la piece qui le
    # declenche*. Corrige le 2026-09-12.
    #
    # **Ce qui reste vrai, et qui est plus etroit:** chaque geste neuf doit
    # etre ajoute a la main a cette mesure. Rien ne rougit si on l'oublie, et
    # l'axe reste *un chemin du PRODUIT ecrit la table*. La difference avec la
    # version precedente de ce commentaire n'est pas cosmetique: elle distingue
    # *le remede n'est pas applique* de *le remede s'applique un cas a la
    # fois*. Le premier invite a refaire ce qui existe.
    #
    # **Et une limite de CHAMP a ete levee le 2026-09-12**, celle-la vraie:
    # l'instrument n'armait son autorisateur SQLite que sur
    # `gouvernance.sqlite3`, donc tout `vault_reconstruction.sqlite3` - ou
    # vivent `points`, `actions`, `expected_pieces` - etait hors de sa vue.
    # Mesure faite: une seule base est ouverte par la chaine, les gestes et les
    # ecrans, donc le defaut etait **latent**; il ne se serait pas signale
    # (`RM-2026-0008`).
)

#: Index par table, pour la garde et pour les ecrans.
PAR_TABLE: dict[str, PromesseSansChemin] = {
    promesse.table: promesse for promesse in SANS_CHEMIN_DE_PRODUCTION
}


def exigences() -> tuple[tuple[str, str], ...]:
    """Les promesses sans chemin, dans la forme (titre, corps) des ecrans."""
    return tuple((promesse.titre, promesse.corps) for promesse in SANS_CHEMIN_DE_PRODUCTION)
