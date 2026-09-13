"""Le pont entre les registres de gouvernance et le modele relationnel des actes.

**Le verrou que ce module leve.** Le modele relationnel de l'acte d'autorisation
existe depuis `7c2001a`, la typologie de ses onze types depuis `83c79fb`, l'ecran
`/controle-gouvernance` depuis `9ed8bbb`. Aucun des trois n'etait alimente:
mesure du 2026-09-04 sur les deux instances locales, **173 resolutions au
registre et 0 acte verse** pour l'une, 118 et 0 pour l'autre. Rien dans le
produit n'ecrivait dans `actes_autorisation` hors des tests, et l'ecran rendait
donc un etat explicite "le modele relationnel n'a jamais ete alimente" a la
place du tableau.

**Ce que le pont n'est pas.** Ce n'est pas un extracteur. Il ne lit aucun
proces-verbal pour en tirer un fait, sauf la portee - voir
`_pont_actes_source` pour la raison, qui tient a ce que le registre ne stocke
volontairement aucun texte integral. Tous les autres faits viennent des tables
`resolutions` et `devis_cites`, deja ecrites, dans le MEME fichier
`gouvernance.sqlite3`. Aucune quatrieme source de verite n'est creee.

----------------------------------------------------------------------
Ou ce module ecrit, et pourquoi ce n'est pas la base de reconstruction
----------------------------------------------------------------------

Dans `gouvernance.sqlite3`, sous `settings.vault.local_root`, par la couche
partagee `vault.gouvernance_store` - la meme que les resolutions et les
convocations.

**Le piege evite est nomme dans les consignes du depot, avec une raison qui a
ete corrigee le 2026-09-08.** Une table alimentee dans la base de reconstruction
sans passer par le journal d'evenements n'y serait pas effacee au rebuild
suivant: `_reset_schema` est une liste explicite de `DROP TABLE IF EXISTS` et la
base n'est jamais supprimee, donc une table hors liste SURVIT. Le danger est
pire qu'une perte - une perte finit par se voir. C'est une desynchronisation
muette: la table garde ses lignes pendant que tout autour se reconstruit, et
rien ne signale la divergence. La decision reste la meme, sa raison change. Le
fichier `gouvernance.sqlite3` n'est pas reconstruit: il est ecrit et relu tel
quel. Ce pont y ecrit, et nulle part ailleurs.

Deuxieme garde, portee par la couche partagee et non par ce module: une
re-extraction remplace ce qu'elle a produit et **rien d'autre**. Les lignes
d'origine `CORRIGE_HUMAIN` survivent, parce que la clause `DELETE` les exclut et
que `origine` entre dans la cle primaire.

----------------------------------------------------------------------
Ce que le versement rend, et ce qu'il refuse de rendre
----------------------------------------------------------------------

Le resume ne compte pas ce qui est beau, il compte ce qui est verifiable, y
compris quand le chiffre est mauvais. Deux exemples que ce module remonte au
lieu de les lisser:

- `collisions`: un meme `acte_id` revendique par plusieurs documents. Sur
  l'instance a deux exercices, le proces-verbal du 03/07/2024 existe en six
  exemplaires, dont cinq blocs decoupes qui renumerotent chacun a partir de 1.
  Le registre `resolutions` les avait deja ecrases sans le dire - 119 lignes
  ecrites, 63 conservees. Le pont ne fusionne pas: il nomme.
- `actes_sans_date`: les actes dont la date d'assemblee n'a pas ete lue. Leur
  identifiant porte `SANS-DATE`, et `v_constats` en fait une ligne
  `PV_SANS_DATE_LUE` par document - pas une par resolution.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from . import _actes_store as store
from ._actes_schema import (
    MARQUE_SANS_DATE,
    TABLE_ACTES,
    TABLE_ATTRIBUTS,
    TABLE_LIENS,
)
from ._pont_actes_lignes import (
    collisions,
    ligne_acte,
    lignes_attributs,
)
from ._pont_actes_liens import liens_du_devis, liens_seuil, normes_seuil
from ._pont_actes_source import (
    candidats_devis,
    candidats_resolutions,
    registre_documents,
)
from ._resolutions_assemblees import assemblees_sans_date_lue, copies_concurrentes
from ._resolutions_recouvrement import conservation_du_total
from ._resolutions_registre import seuils_en_vigueur
from ..vault import gouvernance_store
from ..vault.gouvernance_store import GouvernanceStoreIndisponible

__all__ = ["build_actes", "verser"]


def _compter(valeurs: Any) -> dict[str, int]:
    return dict(sorted(Counter(valeurs).items()))


def _assemblees(actes: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    """Combien d'actes et combien de documents par assemblee.

    Une assemblee alimentee par plusieurs documents n'est pas anormale - un
    proces-verbal peut arriver en PDF et en texte extrait. Une assemblee qui
    porte une numerotation COMPLETE par document l'est: c'est le meme
    proces-verbal lu plusieurs fois, et l'ecran en fait autant de lignes.
    """
    groupes: dict[str, dict[str, set[str]]] = {}
    for acte in actes:
        ag_id = acte["ag_id"] or "sans_assemblee"
        groupe = groupes.setdefault(ag_id, {"actes": set(), "documents": set()})
        groupe["actes"].add(acte["acte_id"])
        if acte["doc_id"]:
            groupe["documents"].add(acte["doc_id"])
    return {
        ag_id: {"actes": len(g["actes"]), "documents": len(g["documents"])}
        for ag_id, g in sorted(groupes.items())
    }


def verser(instance: Any) -> dict[str, Any]:
    """Construit les actes, leurs attributs et leurs liens, puis les ecrit.

    Rend un resume mesurable. Une instance sans coffre declare, ou sans aucun
    registre de gouvernance, n'est pas une erreur: c'est une instance ou rien
    n'a encore ete lu, et le resume le dit au lieu de rendre un ecran vide.
    """
    _, ambigus = registre_documents(instance)
    candidats = candidats_resolutions(instance) + candidats_devis(instance)
    if not candidats:
        return {
            "registre_vide": True,
            "actes": 0,
            "attributs": 0,
            "liens": 0,
        }

    actes: list[dict[str, str]] = []
    attributs: list[dict[str, str]] = []
    liens: list[dict[str, str]] = []
    for candidat in candidats:
        acte = ligne_acte(candidat)
        actes.append(acte)
        attributs.extend(lignes_attributs(candidat, acte))
        if candidat.source == "DEVIS_CITE":
            liens.extend(liens_du_devis(candidat, acte))

    # Les seuils de l'article 21 se lisent sur le registre des resolutions, une
    # fois par date d'acte. Le module qui les porte est le seul a connaitre les
    # deux nuances qui empechent d'en tirer une conclusion trop vite - un seuil
    # ancien sans terme, et deux seuils actifs a la meme date.
    lignes_resolutions = gouvernance_store.lire(instance)
    dates = sorted({a["date_effet"] for a in actes if a["date_effet"]})
    etats_par_date = {
        date: seuils_en_vigueur(lignes_resolutions, date) for date in dates
    }
    # `normes_seuil` dit LAQUELLE des deux obligations de l'article 21 alinea 2
    # chaque deliberation de seuil arrete - consultation du conseil syndical, ou
    # mise en concurrence. Sans elle, les deux montants du meme jour partaient
    # sur la meme relation et l'ecran les opposait comme s'ils repondaient a la
    # meme question.
    liens.extend(
        liens_seuil(actes, etats_par_date, normes_seuil(candidats, actes))
    )

    doc_ids = sorted({a["doc_id"] for a in actes if a["doc_id"]})
    try:
        store.ecrire(instance, TABLE_ACTES, actes, doc_ids)
        store.ecrire(instance, TABLE_ATTRIBUTS, attributs, doc_ids)
        store.ecrire(instance, TABLE_LIENS, liens, doc_ids)
    except GouvernanceStoreIndisponible as exc:
        return {"coffre_non_declare": str(exc), "actes": 0}

    doublons = collisions(actes)
    concurrents = copies_concurrentes(actes)
    conservation = conservation_du_total(actes)
    return {
        "actes": len(actes),
        # Le meme proces-verbal lu plusieurs fois. Mesure du 2026-09-04 sur
        # l'instance a deux exercices: la table `resolutions` portait TROIS
        # copies de l'assemblee du 03/07/2024, 55 lignes chacune, numerotees 1 a
        # 55, avec trois comptages d'issues differents - et deux d'entre elles
        # avaient perdu la date, donc un `ag_id` derive du document. Rien ne les
        # opposait: les cles different par le `doc_id`, les trois coexistent, et
        # l'ecran affiche trois fois la meme resolution sans jamais dire que
        # c'est le meme document. Le pont ne choisit pas laquelle fait foi -
        # ce serait poser une regle de preuve dans un module de transport, et la
        # mesure dit justement que le choix par defaut serait le mauvais. Il
        # NOMME.
        "assemblees": _assemblees(actes),
        # La FORME de l'identifiant, jamais sa longueur. La premiere ecriture
        # testait `not ag.startswith("AG-2") or len(ag) != 13`. Comparaison des
        # deux regles sur six identifiants, le 2026-09-05: elles s'accordent sur
        # quatre et divergent sur deux, dans les deux sens.
        #   - `AG-1998-07-03` etait range parmi les assemblees SANS date, alors
        #     que sa date est lue. Une copropriete qui verse ses archives
        #     d'avant l'an 2000 voyait chacune de ses assemblees signalee.
        #   - `AG-2XXX-XX-XX` passait pour date, parce qu'il fait treize
        #     caracteres et commence par `AG-2`.
        "assemblees_sans_date_lue": assemblees_sans_date_lue(actes),
        # C054, la moitie que le resume seul ne pouvait pas porter. Combien
        # d'actes occupent un rang de resolution partage avec une assemblee dont
        # la date n'a pas ete lue. L'ecran les nomme ligne a ligne; le journal
        # dit combien il y en a, pour qu'un run se compare a un autre.
        "actes_en_concurrence": len(concurrents),
        # La CONSERVATION que `RM-2026-0077` reclame: un total qui somme des
        # assemblees declare combien de ses lignes existent aussi ailleurs.
        # Ce compte ne depend PAS de la date lue, et c'est tout son interet:
        # la garde precedente s'etait calee sur *au moins une assemblee sans
        # date*, qui etait la forme du defaut sur un corpus, pas le defaut.
        # Le correctif de lecture de date du 2026-09-08 a rendu leur date aux
        # copies et a donc ETEINT cette garde sans faire echouer un test.
        # Mesure du 2026-09-10 sur instance vide, 858 pieces reabsorbees:
        # 238 actes sur 550 portent un objet present sous une autre
        # assemblee, et six des sept paires concernees etaient muettes.
        "actes_partages": conservation["actes_partages"],
        # Une assemblee dont TOUS les objets existent ailleurs n'apporte
        # aucune matiere propre au total. Inclusion stricte des jeux, jamais
        # un seuil - donc rien a calibrer et rien a franchir.
        "assemblees_entierement_partagees":
            conservation["assemblees_entierement_partagees"],
        # Le detail par paire, avec ce qui permet a un humain de trancher ce
        # que le module refuse de trancher: bloc de rangs contigu ou epars,
        # et objets portes par plus de deux assemblees.
        "recouvrements": conservation["recouvrements"],
        "motifs_alerte": _motifs_actes(
            assemblees_sans_date_lue(actes), concurrents, ambigus, conservation),
        # Les `doc_id` que le registre documentaire attribue a plusieurs lignes
        # divergentes. `doc_id` derive du contenu: deux fichiers identiques de
        # noms differents partagent le leur, et 528 lignes sur 3 447 sont dans
        # ce cas. Quand ces lignes ne disent pas le meme `text_path`, le texte
        # relu - donc la portee de toutes les resolutions du document - se
        # decidait sur l'ordre des lignes d'un CSV.
        "doc_ids_ambigus": ambigus,
        # Ce qui a effectivement survecu a la cle primaire (acte_id, origine).
        # L'ecart avec `actes` est la mesure des collisions, et il doit rester
        # lisible: c'est exactement le defaut que le registre amont subissait
        # sans le dire.
        "actes_distincts": len({a["acte_id"] for a in actes}),
        "attributs": len(attributs),
        "liens": len(liens),
        "par_etat": _compter(a["etat"] for a in actes),
        "par_exercice": _compter(a["exercice"] or "sans_exercice" for a in actes),
        "par_portee": _compter(a["portee"] for a in actes),
        "par_resultat": _compter(a["resultat"] for a in actes),
        "liens_par_relation": _compter(l["relation"] for l in liens),
        "attributs_par_nom": _compter(a["nom"] for a in attributs),
        "actes_sans_date": sum(1 for a in actes if MARQUE_SANS_DATE in a["acte_id"]),
        "collisions": {cle: docs for cle, docs in sorted(doublons.items())},
        "documents": len(doc_ids),
    }


def _motifs_actes(sans_date, concurrents, ambigus, conservation=None) -> list[str]:
    """Ce que cette etape n'a pas su trancher, dans ses propres termes."""
    motifs: list[str] = []
    if sans_date:
        motifs.append(
            f"{len(sans_date)} assemblees identifiees par un document faute de date lue: "
            "rien ne les distingue d'une autre assemblee portant les memes rangs"
        )
    if concurrents:
        motifs.append(
            f"{len(concurrents)} actes partagent leur rang avec un autre acte"
        )
    if ambigus:
        motifs.append(f"{len(ambigus)} documents portent un identifiant ambigu")
    if conservation and conservation.get("actes_partages"):
        # Enonce la CONSERVATION, jamais un verdict de doublon: la raison du
        # partage - proces-verbal relu, recueil, convocation suivie de son PV,
        # ou resolution de seance qui revient chaque annee - reste ouverte.
        # Ce qui est vrai dans tous les cas, c'est que la sommation les
        # compte plusieurs fois.
        incluses = conservation.get("assemblees_entierement_partagees") or []
        motif = (
            f'{conservation["actes_partages"]} actes sur {conservation["actes"]} '
            "portent un objet qui existe aussi sous une autre assemblee: "
            "un total obtenu par sommation les compte plusieurs fois"
        )
        if incluses:
            motif += (
                f", et {len(incluses)} assemblees n'apportent aucun objet "
                "qui leur soit propre"
            )
        motifs.append(motif)
    return motifs


def build_actes(instance: Any, run: Any = None) -> dict[str, Any]:
    """Etape de chaine: verse le modele relationnel, et journalise le resume.

    Meme forme que `resolutions.build_register` et
    `convocation.build_register`, pour que `depot._run_step` la traite comme les
    autres et qu'aucun appelant n'ait a connaitre ce module.
    """
    resume = verser(instance)
    if run is not None:
        niveau = "OK"
        if (
            resume.get("collisions")
            or resume.get("coffre_non_declare")
            or resume.get("doc_ids_ambigus")
            or resume.get("assemblees_sans_date_lue")
        ):
            niveau = "WARN"
        run.log_run(niveau, f"pont actes: {resume}")
    return resume
