"""Export et recoupement d'observations entre coproprietaires.

Demande de Brice du 2026-09-04: *"je veux que les infos soient exportables, pour
que d'autres voisins puissent monitorer et qu'on puisse recouper les
changements"*. Anticipe `RM-2026-0092`.

======================================================================
Pourquoi le recoupement vaut mieux qu'un journal solitaire
======================================================================

La faiblesse structurelle d'un journal d'observation est **sa couverture**: il
ne voit que ce que son porteur ouvre. Deux personnes qui observent
independamment couvrent plus de rubriques, plus souvent.

Et surtout: si deux coproprietaires detiennent la meme empreinte pour la meme
piece a la meme date, et qu'elle disparait ensuite, **le retrait cesse d'etre
une affirmation isolee**. Un journal seul est une allegation; deux journaux
concordants sont une preuve.

Un desaccord n'est pas non plus une panne a corriger: si une piece est vue par
l'un et pas par l'autre au meme moment, c'est un **constat** - l'extranet ne
sert pas la meme chose a tout le monde. Selon la rubrique, cela peut etre normal
ou etre precisement le manquement que le referentiel cherche.

======================================================================
Ce qui circule, et ce qui ne circule jamais
======================================================================

**Ne circulent jamais**: les documents, les libelles, les noms de fichiers, les
montants, les adresses des pieces. Un extranet de copropriete porte des donnees
de tiers - la liste de l'article 32 du decret 67-223 porte l'etat civil de tous
les coproprietaires - et un fichier d'echange se retrouve toujours quelque part.

**Circulent**: des empreintes, des dates, et la couverture. Le code de rubrique
lui-meme est empreint depuis le 2026-09-07: sur un index il serait anodin, mais
sur une page de depenses il est DECOUVERT et non declare - c'est l'en-tete du
groupe de charges, donc un libelle et un montant. Le recoupement n'y perd rien:
deux voisins qui partagent le sel obtiennent la meme valeur. Cela suffit a repondre a *"avons-nous vu la meme chose ?"* sans que
personne n'envoie quoi que ce soit.

----------------------------------------------------------------------
Le sel, et pourquoi une empreinte nue ne suffirait pas
----------------------------------------------------------------------

Une empreinte non salee serait un **oracle**: n'importe qui mettant la main sur
le fichier pourrait tester une hypothese - *"cette copropriete detient-elle un
document intitule ainsi ?"* - en calculant l'empreinte de sa supposition et en
la cherchant dans le fichier. Le nombre de libelles plausibles est petit; une
telle attaque tient sur un ordinateur portable.

Le sel est un secret **partage par les observateurs d'une meme copropriete** et
par eux seuls. Il ne rend pas les empreintes incomparables entre voisins - c'est
tout l'objet - mais il rend le fichier muet pour qui ne l'a pas.

Consequences a tenir, et elles sont exigeantes:

- le sel ne s'ecrit **jamais** dans un export, ni dans Git, ni dans un journal;
- deux exports de sels differents ne se recoupent pas, et le dire est mieux que
  de rendre zero concordance sans explication: c'est a cela que sert
  `temoin_sel`;
- changer de sel rend tout l'historique anterieur incomparable. C'est un choix
  a faire une fois, au depart, par le conseil syndical.

----------------------------------------------------------------------
Deux sels coexistent dans CoproScope, et leurs buts sont OPPOSES
----------------------------------------------------------------------

Constat du 2026-09-07, ne pas le perdre.

============ ==================================== ==============================
             `sel_alias.key` (BiffageOps)          le sel de ce module
============ ==================================== ==============================
Portee       une **instance**                     une **copropriete**, partage
                                                  entre voisins
But          que deux coffres produisent des      que deux voisins produisent
             alias **differents** pour la meme    des empreintes **identiques**
             personne - non-chainabilite          pour la meme piece
Ou il vit    `vault.local_root/corpus_caviarde/`  nulle part: choisi par le
             `sel_alias.key`, 32 octets, ecrit    conseil syndical, jamais
             sur le disque, hors Git              ecrit par le produit
============ ==================================== ==============================

Les confondre casse en **silence**, et dans les deux sens:

- employer le sel d'instance pour l'echange: aucun voisin ne se recoupe jamais.
  Le rendu est un zero de concordance, que deux personnes lisent comme un
  desaccord entre elles;
- employer le sel partage pour les alias: deux coffres de coproprietaires
  voisins produisent le meme alias pour la meme personne, et deviennent donc
  chainables. La garantie que BiffageOps existe pour tenir tombe, sans qu'aucun
  message ne le dise.

Trois gardes tiennent la distinction, et il en faut trois parce qu'aucune ne
suffit seule:

1. **Separation de domaine.** Les empreintes de ce module portent un prefixe
   constant qui n'existe nulle part ailleurs. Meme si quelqu'un fournissait le
   sel d'alias, les valeurs produites ne pourraient jamais etre confondues avec
   celles de BiffageOps, ni servir a relier les deux mondes.
2. **Refus actif**, dans `extranetops.exporter_passage`, qui est la seule
   couche a voir a la fois l'instance et le sel: un sel egal a celui de
   l'instance leve `SelInterdit`.
3. **Frontiere de citation**, tenue par un test: ce module ne cite jamais
   BiffageOps, et BiffageOps ne cite jamais ce module.

----------------------------------------------------------------------
Ce qui entre dans une empreinte, et ce qui n'y entre pas
----------------------------------------------------------------------

Contrainte posee des la conception, et **elle a une raison mecanique**: une
empreinte doit dependre de ce que deux observateurs voient **pareillement**.

N'y entrent donc pas: la date de l'observation, l'identifiant du compte, le
jeton d'URL - qui change a chaque chargement de page chez l'editeur mesure - ni
rien qui soit propre au poste qui calcule. Une empreinte qui en dependrait ne
serait comparable avec personne, et le defaut ne se verrait qu'au moment du
recoupement, sous la forme d'un zero inexplicable.
"""

from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping, Sequence

#: `/3`, meme jour, apres une relecture de doctrine: le code de rubrique
#: circulait EN CLAIR. Sur un index c'est anodin - `ARR`, `CON` - mais sur une
#: page de depenses le code est DECOUVERT et non declare: c'est l'en-tete du
#: groupe de charges, donc un libelle **et un montant**. La docstring de ce
#: module jurait pourtant que les montants ne circulent jamais. Le code de
#: rubrique est desormais empreint comme le reste; le recoupement fonctionne a
#: l'identique puisque deux voisins qui partagent le sel obtiennent la meme
#: valeur.
#:
#: Le format avait deja change le 2026-09-07 en passant a `/2`: les empreintes portent
#: desormais un domaine, ce qui les rend toutes differentes. La rupture est
#: gratuite aujourd'hui - l'extension n'a jamais ete distribuee, aucun export
#: reel n'a circule - et elle aurait coute un tour de migration plus tard.
FORMAT = "coproscope.extranet.observation/3"

#: Longueur d'empreinte retenue. 32 caracteres hexadecimaux, soit 128 bits:
#: aucune collision fortuite a l'echelle d'une copropriete, et un fichier qui
#: reste lisible par un humain.
#: Le domaine cryptographique de ce module. Il rend une empreinte d'extranet
#: impossible a confondre avec une empreinte produite ailleurs dans le produit,
#: meme a sel egal. Ce n'est pas un secret: c'est une etiquette, et sa valeur
#: n'a d'importance que par son unicite.
DOMAINE = b"coproscope-extranet-recoupement-v1\x00"

LONGUEUR = 32


def empreinte(valeur: str, sel: str) -> str:
    """Empreinte salee d'une valeur, stable entre postes et entre observateurs."""
    if not sel:
        raise ValueError(
            "Un sel est obligatoire. Sans lui, l'export devient un oracle: "
            "quiconque obtient le fichier peut tester une hypothese sur un "
            "libelle en calculant son empreinte."
        )
    brut = DOMAINE + f"{sel}\x00{valeur}".encode("utf-8")
    return hashlib.sha256(brut).hexdigest()[:LONGUEUR]


def temoin_sel(sel: str) -> str:
    """Marqueur public du sel, pour detecter deux sels differents.

    Ce n'est pas le sel: c'est son empreinte sous une constante fixe. Il permet
    de dire *"vos deux exports n'emploient pas le meme secret"* au lieu de
    rendre zero concordance sans explication - ce qui serait interprete comme
    *"nous n'avons rien vu de commun"*, et donc comme un desaccord entre
    voisins, alors que c'est un probleme de configuration.
    """
    return hashlib.sha256(
        DOMAINE + f"temoin\x00{sel}".encode("utf-8")
    ).hexdigest()[:16]


def exporter(
    passage: Mapping[str, Any],
    rubriques: Sequence[Mapping[str, Any]],
    pieces: Sequence[Mapping[str, Any]],
    *,
    sel: str,
    observateur: str,
) -> dict[str, Any]:
    """Le paquet transmissible d'un passage.

    `observateur` est un **pseudonyme choisi par la personne** - "voisin A",
    "conseil 2" - jamais un nom, jamais une adresse electronique. Il sert
    seulement a ne pas confondre deux journaux au recoupement.
    """
    return {
        "format": FORMAT,
        "temoin_sel": temoin_sel(sel),
        "observateur": observateur,
        "editeur": passage.get("editeur", ""),
        "espace": passage.get("espace", ""),
        "debut": passage.get("debut", ""),
        "fin": passage.get("fin", ""),
        "rubriques": [
            {
                "emp_rubrique": empreinte(r.get("rubrique_code", ""), sel),
                "etat": r.get("etat", ""),
                "cloture": r.get("cloture", ""),
                "nb_pieces": r.get("nb_pieces", "0"),
            }
            for r in rubriques
        ],
        "pieces": [
            {
                "emp_rubrique": empreinte(p.get("rubrique_code", ""), sel),
                "emp_emplacement": empreinte(p.get("emplacement", ""), sel)
                if p.get("emplacement")
                else "",
                "emp_nom": empreinte(p["nom_serveur"], sel)
                if (p.get("nom_serveur") or "").strip()
                else "",
                "emp_contenu": empreinte(p["empreinte"], sel)
                if (p.get("empreinte") or "").strip()
                else "",
            }
            for p in pieces
        ],
    }


class SelDifferent(ValueError):
    """Les deux exports n'emploient pas le meme secret de copropriete."""


def _controler(paquets: Iterable[Mapping[str, Any]]) -> None:
    temoins = {p.get("temoin_sel", "") for p in paquets}
    if len(temoins) > 1:
        raise SelDifferent(
            "Ces observations n'emploient pas le meme sel de copropriete. "
            "Elles ne peuvent pas etre recoupees, et un zero de concordance "
            "serait ici un artefact de configuration, pas un desaccord."
        )


def recouper(mien: Mapping[str, Any], sien: Mapping[str, Any]) -> dict[str, Any]:
    """Confronte deux observations de la meme copropriete, faites en parallele.

    Rend quatre choses, et les quatre comptent:

    - `corrobores`: vus par les deux. C'est ce qui transforme une allegation en
      preuve, le jour ou l'un d'eux disparait;
    - `seulement_mien` / `seulement_sien`: **pas des erreurs**. Un ecart peut
      venir d'une couverture differente - l'un a ouvert une rubrique que l'autre
      n'a pas ouverte - ou d'un extranet qui ne sert pas la meme chose aux deux
      comptes. Le premier cas est banal, le second est un constat de premier
      ordre;
    - `couverture_gagnee`: les rubriques que l'autre a parcourues et pas moi.
      C'est le benefice immediat du recoupement, avant meme toute comparaison
      dans le temps.

    Le tri entre les deux causes d'ecart se fait par la couverture, et c'est
    pour cela qu'elle voyage avec les pieces: un ecart dans une rubrique que
    l'autre n'a pas parcourue n'apprend rien; le meme ecart dans une rubrique
    que les deux ont parcourue est une question a poser.
    """
    _controler((mien, sien))

    cov_a = {r["emp_rubrique"]: r for r in mien.get("rubriques", ())}
    cov_b = {r["emp_rubrique"]: r for r in sien.get("rubriques", ())}
    parcourues_a = {c for c, r in cov_a.items() if r.get("etat") == "PARCOURUE"}
    parcourues_b = {c for c, r in cov_b.items() if r.get("etat") == "PARCOURUE"}
    communes = parcourues_a & parcourues_b

    def _index(paquet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
        return {
            p["emp_emplacement"]: p
            for p in paquet.get("pieces", ())
            if p.get("emp_emplacement")
        }

    ia, ib = _index(mien), _index(sien)
    corrobores = sorted(set(ia) & set(ib))

    def _ecarts(source, autre, cov_autre_parcourues):
        vus, contradictoires = [], []
        for cle, piece in source.items():
            if cle in autre:
                continue
            (contradictoires if piece.get("emp_rubrique") in cov_autre_parcourues
             else vus).append(cle)
        return sorted(vus), sorted(contradictoires)

    hors_a, contra_a = _ecarts(ia, ib, parcourues_b)
    hors_b, contra_b = _ecarts(ib, ia, parcourues_a)

    return {
        "observateurs": [mien.get("observateur", ""), sien.get("observateur", "")],
        "corrobores": corrobores,
        "nb_corrobores": len(corrobores),
        "rubriques_communes": sorted(communes),
        "couverture_gagnee": sorted(parcourues_b - parcourues_a),
        "couverture_apportee": sorted(parcourues_a - parcourues_b),
        # Hors couverture de l'autre: banal, il n'a pas regarde la.
        "seulement_mien_hors_couverture": hors_a,
        "seulement_sien_hors_couverture": hors_b,
        # Dans une rubrique que l'autre A parcourue: c'est un constat.
        "divergences_dans_couverture_commune": sorted(contra_a + contra_b),
    }


def fusionner_couverture(paquets: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """Ce que le groupe a collectivement parcouru, rubrique par rubrique.

    Une rubrique est `PARCOURUE` des qu'**un** observateur l'a ouverte. C'est le
    gain principal du monitorage a plusieurs: aucun d'eux n'a besoin de tout
    ouvrir a chaque fois pour que le groupe puisse conclure a une absence.

    **Reservee, et sans appelant en production - c'est une decision.** Elle
    appartient a `RM-2026-0092`, la consolidation entre coproprietaires, qui
    depend elle-meme de `RM-2026-0033`. La brancher aujourd'hui donnerait un
    gain de couverture calcule sur un seul journal, donc toujours egal a ce
    journal: un chiffre juste et inutile, que quelqu'un finirait par citer.

    `test_extranet_echange.py` verifie qu'elle n'a effectivement aucun
    appelant, pour que la reserve reste visible au lieu de se transformer en
    oubli.
    """
    _controler(paquets)
    etat: dict[str, str] = {}
    for paquet in paquets:
        for rubrique in paquet.get("rubriques", ()):
            code = rubrique.get("emp_rubrique", "")
            if not code:
                continue
            if rubrique.get("etat") == "PARCOURUE" or code not in etat:
                etat[code] = rubrique.get("etat", "")
    return etat
