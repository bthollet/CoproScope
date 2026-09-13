# -*- coding: utf-8 -*-
"""Les panneaux de la page du gouvernail, DERIVES du registre.

**Le defaut mesure le 2026-09-09, et Brice l'a vu avant moi:** *« l'artefact a
pas l'air de refresh »*. Le depot produisait deux documents - `registre` et
`pieces` - et la page en lit **sept**. Les cinq autres etaient une couche
**editoriale ecrite a la main** le 2026-09-08: `p0` annonçait 26 items dont le
premier n'est plus P0, `statuts` comptait 55 `ACTIF` la ou le registre en porte
70, `etat` datait son arret a `08/09/2026, 12:40`.

Le registre etait donc frais et **tout ce qu'on voyait de lui datait de la
veille**. C'est `RM-2026-0171` a l'echelle d'une page: l'information exacte
etait dans le magasin, et les panneaux affichaient autre chose.

**Le remede est le (a) du document de doctrine: deriver, ne pas ecrire a cote.**
Un panneau derive du registre change tout seul quand le registre change. Un
panneau ecrit a la main ne change que si quelqu'un y pense - et personne n'y
pense, parce que rien ne le signale.

**Ce qui n'est PAS derivable reste editorial, et c'est dit.** `voies` decrit les
conversations vivantes, `demandes` porte des demandes rendues: aucune des deux
ne se lit dans le registre. Elles gardent leur date propre, et la page peut
ainsi montrer qu'elles sont plus vieilles que le reste.
"""

from __future__ import annotations

#: Ce qu'un item declare de son avancement, lu sur sa colonne `ch` (chantiers).
#: Trois etats, et le troisieme n'est pas une nuance: un item `A_ARBITRER`
#: attend une decision humaine, pas du travail.
ETAT_ARBITRAGE = "arb"
ETAT_OUVERT = "ouvert"
ETAT_JAMAIS = "jamais"


def _etat_de_l_item(item: dict) -> str:
    """En attente d'arbitrage, ou porteur d'un chantier declare.

    **`ETAT_JAMAIS` n'est pas derivable du registre, et il ne faut pas faire
    semblant.** Le panneau ecrit a la main annonçait *12 P0 jamais ouverts*.
    Mesure du 2026-09-09: **la colonne des chantiers est remplie pour les 70
    items ACTIF, sans exception** - un item qui n'a jamais ete travaille y porte
    quand meme l'identifiant du chantier ouvert pour lui. En deriver *jamais
    ouvert* rendrait donc **zero**, c'est-a-dire un chiffre rassurant et faux,
    exactement le defaut que `RM-2026-0171` decrit.

    Ce qu'il faudrait pour le savoir: confronter chaque chantier a une trace de
    travail reelle - un commit, une ligne de presence. C'est un lot en soi, et
    tant qu'il n'existe pas, **la notion se declare indisponible.**
    """
    if item.get("st", "").upper() == "A_ARBITRER":
        return ETAT_ARBITRAGE
    return ETAT_OUVERT


def panneau_statuts(lignes: list[dict], couleurs: dict[str, str]) -> dict:
    """Le compte par statut, dans l'ordre decroissant."""
    compte: dict[str, int] = {}
    for item in lignes:
        statut = (item.get("st") or "?").upper()
        compte[statut] = compte.get(statut, 0) + 1
    ordonne = sorted(compte.items(), key=lambda kv: -kv[1])
    return {
        "lignes": [
            {"label": statut, "n": n, "couleur": couleurs.get(statut, "var(--idle)")}
            for statut, n in ordonne
        ]
    }


def panneau_p0(lignes: list[dict]) -> dict:
    """Les P0 encore ACTIF, avec ce que chacun attend.

    **Aucune liste d'identifiants n'est ecrite ici.** Un item qui devient P0
    demain y entre sans qu'on touche a ce fichier; un item qu'on ferme en sort.
    C'est la difference entre un panneau derive et un panneau recopie.
    """
    retenus = [
        item for item in lignes
        if (item.get("st") or "").upper() == "ACTIF" and (item.get("p") or "").upper() == "P0"
    ]
    return {
        "lignes": [
            {
                "rm": item.get("id", ""),
                "sujet": (item.get("t") or "").strip(),
                "etat": _etat_de_l_item(item),
                "voie": (item.get("ty") or "").split("/")[0].strip().lower(),
            }
            for item in retenus
        ]
    }


def panneau_etat(lignes: list[dict], commit: str, tests: dict | None = None) -> dict:
    """Le bandeau: ce qui reste, ce qui n'a jamais ete ouvert, l'arbre mesure.

    `tests` porte le dernier passage connu - son compte, son verdict et **le
    commit sur lequel il a tourne**. Il est facultatif et **son absence se
    declare**: un bandeau qui tairait qu'aucune suite n'a ete jouee dirait le
    contraire de ce que `RM-2026-0172` demande.
    """
    actifs = [i for i in lignes if (i.get("st") or "").upper() == "ACTIF"]
    p0 = [i for i in actifs if (i.get("p") or "").upper() == "P0"]
    arbitrage = [i for i in lignes if (i.get("st") or "").upper() == "A_ARBITRER"]

    etat = {
        "head": "<b>%s</b>" % commit if commit else "commit inconnu",
        "reste": len(actifs),
        "reste_note": "sur %d items au registre, dont %d en P0" % (len(lignes), len(p0)),
        # **`p0_jamais` a ete RETIRE, il n'est pas passe a zero.** Le panneau
        # ecrit a la main annonçait 12; la colonne des chantiers est remplie
        # pour les 70 items ACTIF, donc en deriver la notion rendrait zero -
        # un chiffre rassurant et faux. Voir `_etat_de_l_item`.
        "bar_note": (
            "%d <code>ACTIF</code>, dont <b style=\"color:var(--crit)\">%d en P0</b>. "
            "%d attendent un arbitrage. "
            "<i>Le compte des items jamais ouverts n'est pas derivable du registre : "
            "la colonne des chantiers est remplie pour tous, y compris ceux qui n'ont "
            "jamais ete travailles. Il faudrait confronter chaque chantier a une trace "
            "reelle.</i>"
            % (len(actifs), len(p0), len(arbitrage))
        ),
    }
    if tests:
        etat["tests"] = tests.get("n", 0)
        etat["tests_note"] = tests.get("note", "")
    else:
        etat["tests"] = 0
        etat["tests_note"] = (
            "AUCUNE suite jouee sur cet arbre: ce depot ne dit rien de l'etat des tests."
        )
    return etat
