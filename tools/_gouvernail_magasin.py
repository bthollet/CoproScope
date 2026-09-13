# -*- coding: utf-8 -*-
"""Ce que le magasin de la page accepte, et comment un document s'y plie.

**Extrait de `gouvernail_depot.py` le 2026-09-09**, qui passait a 607 lignes
alors que la limite du depot est 600. L'unite est coherente: trois constantes
et trois fonctions, toutes sur la meme question - **combien d'octets le magasin
prend, et ce qu'un document doit declarer quand il n'y tient pas.**

Le mot d'ordre commun aux trois fonctions: **une coupure se declare.** Un
document qui deborde en silence est rejete par le magasin bien plus tard, sans
que personne sache pourquoi; un document tronque sans le dire fait lire un
mandat coupe comme un mandat entier.
"""

from __future__ import annotations

import json

#: Un document du magasin de la page est borne. Le depot precedent coupait deja
#: la colonne `Prochaine action` - en silence, par des points de suspension. Une
#: coupure qui ne se declare pas fait lire un mandat tronque comme un mandat
#: entier: c'est la meme faute que le lot corrige a l'ecran.
OCTETS_MAX_DOCUMENT = 262_144
CHAMPS_COUPABLES = ("a", "preuve", "src", "t", "ch")
#: Descendante. On garde le plus grand palier qui tient, jamais un palier choisi
#: d'avance: le registre grossit, et un nombre fige aujourd'hui mentirait demain.
PALIERS_CELLULE = (100_000, 6_000, 4_000, 3_000, 2_000, 1_500, 1_200, 900, 700, 500, 350)


def octets(document: dict) -> int:
    return len(json.dumps(document, ensure_ascii=False).encode("utf-8"))


def ajuster_au_magasin(registre: dict, budget: int = OCTETS_MAX_DOCUMENT) -> dict:
    """Coupe les cellules au plus grand palier qui tient, et DECLARE la coupure.

    **Deux populations, et la difference est DECLAREE ligne par ligne.** Une
    ligne portant `detail` a `true` est rendue en entier par la page: ses
    cellules ne sont jamais coupees. Une ligne a `false` ne nourrit que des
    compteurs - statuts, ages, presence de chantier - et sa prose n'est affichee
    nulle part; c'est celle-la qu'on raccourcit.

    **Pourquoi le drapeau, plutot qu'un accord tacite.** Le jour ou la page
    rendra en detail une ligne de comptage, elle lira `detail === false` et le
    dira, au lieu d'afficher une cellule coupee comme si elle etait entiere.
    Sans ce drapeau, le meme changement produirait un mandat tronque presente
    comme un mandat complet - exactement le defaut que ce lot corrige.

    Chaque ligne coupee porte `coupe`, un dictionnaire champ -> longueur reelle.
    Si aucun palier ne tient, la fonction leve: un depot qui deborde en silence
    serait rejete par le magasin bien plus tard, sans que personne sache
    pourquoi.
    """
    for palier in PALIERS_CELLULE:
        essai = dict(registre)
        lignes = []
        for item in registre["lignes"]:
            copie = dict(item)
            coupe = {}
            if not copie.get("detail"):
                for champ in CHAMPS_COUPABLES:
                    valeur = str(copie.get(champ, ""))
                    if len(valeur) > palier:
                        copie[champ] = valeur[:palier]
                        coupe[champ] = len(valeur)
            if coupe:
                copie["coupe"] = coupe
            lignes.append(copie)
        essai["lignes"] = lignes
        essai["cap_cellule"] = palier
        essai["budget_octets"] = budget
        if octets(essai) <= budget:
            return essai
    raise ValueError(
        "aucun palier de %s ne fait tenir %d lignes sous %d octets. Les lignes "
        "rendues en detail ne sont jamais coupees: si elles seules depassent le "
        "budget, c'est le decoupage du depot qu'il faut revoir, pas le palier."
        % (str(PALIERS_CELLULE), len(registre["lignes"]), budget)
    )


def borner_les_pieces(depot: dict, budget: int = OCTETS_MAX_DOCUMENT) -> dict:
    """Le document des pieces tient dans le magasin, et DIT ce qu'il a laisse.

    **Le defaut repare, mesure le 2026-09-09.** Le registre etait borne par
    `ajuster_au_magasin`; **le document des pieces ne l'etait par rien** - et
    c'est lui qui porte les notes, donc l'objet du mandat. Son seul garde-fou
    etait `CAR_MAX_TOTAL = 600 000`, exprime en **caracteres** face a une limite
    de magasin de 262 144 **octets** ecrite six lignes plus haut. **Un budget
    qui ne parle pas l'unite de sa contrainte ne la respecte que par chance:**
    un document de 597 592 octets a ete construit, 2,28 fois la limite, et les
    28 tests passaient.

    Consequence si rien ne borne: le magasin refuse l'ecriture, la page perd ses
    boutons `Lire ici` et affiche un motif faux. Une bombe a retardement, pas
    une panne - le document tient aujourd'hui a environ six notes pres.

    On retire depuis la fin, et chaque piece retiree **passe dans
    `non_embarques` avec son motif**: une piece qui disparait en silence de la
    page serait exactement le defaut que ce depot corrige a l'ecran.
    """
    depot = dict(depot)
    depot["budget_octets"] = budget
    lignes = list(depot["lignes"])
    ecartes = list(depot["non_embarques"])
    while lignes and octets({**depot, "lignes": lignes, "non_embarques": ecartes}) > budget:
        perdue = lignes.pop()
        ecartes.append({
            "chemin": perdue["chemin"],
            "motif": "budget du magasin atteint (%d octets): piece non embarquee" % budget,
        })
    if not lignes and octets({**depot, "lignes": [], "non_embarques": ecartes}) > budget:
        raise ValueError(
            "le document des pieces depasse %d octets sans aucune piece: ce n'est "
            "plus un probleme de budget, c'est le decoupage du depot." % budget
        )
    depot["lignes"] = lignes
    depot["non_embarques"] = ecartes
    return depot
