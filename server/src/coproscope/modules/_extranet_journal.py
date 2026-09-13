"""Derivation des changements entre deux passages d'observation.

Rien ici n'ecrit en base. Ce module lit deux passages et rend des constats. Le
motif est declare dans `_extranet_schema`: un retrait n'est pas une propriete
d'une piece, c'est une propriete d'un **couple de passages**, et une derivation
sait refuser de conclure la ou une colonne ne saurait que se taire.

----------------------------------------------------------------------
La regle qui gouverne tout le module
----------------------------------------------------------------------

**Le mode de defaillance redoute est le faux retrait.** C'est le constat le plus
accusatoire que l'outil sache produire, il vise une personne identifiable - le
syndic - et il detruirait la credibilite du conseil syndical qui s'en sert.

Toute la logique ci-dessous est donc asymetrique, et deliberement:

- un **ajout** se conclut facilement: la piece est la, on la voit;
- un **retrait** ne se conclut que si trois conditions sont reunies **aux deux
  dates**: la rubrique a ete parcourue, sa cloture permet d'affirmer une
  absence, et la cle d'emplacement est injective sur les deux passages;
- dans le doute, `INDETERMINE`, avec le motif ecrit.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

from ._extranet_schema import (
    CLOTURE_AUCUNE,
    CONTENU_VERIFIE,
    EMPLACEMENT_QUALIFIE,
    RUBRIQUE_PARCOURUE,
    composantes,
)

# ---------------------------------------------------------------------------
# Vocabulaire des constats
# ---------------------------------------------------------------------------

AJOUT = "AJOUT"
RETRAIT = "RETRAIT"
MODIFICATION = "MODIFICATION"
#: Contenu compare des deux cotes, et identique.
INCHANGE = "INCHANGE"
#: Presente aux deux dates, contenu non compare. Ce n'est **pas** `INCHANGE`:
#: chez l'editeur mesure aucun en-tete ne revele un changement de contenu, donc
#: sans les octets on ne sait pas. Confondre les deux ferait dire au journal
#: qu'une piece n'a pas bouge alors qu'il ne l'a pas regardee.
PRESENCE_INCHANGEE = "PRESENCE_INCHANGEE"
INDETERMINE = "INDETERMINE"
#: La piece n'est plus a son emplacement, mais le nom que le serveur lui donne
#: se retrouve ailleurs dans l'index. Elle a donc ete deplacee ou renommee, pas
#: retiree. Voir `_verdict_absence`.
DEPLACE = "DEPLACE_OU_RENOMME"

#: Motifs d'indetermination. Ils sont rendus a l'utilisateur tels quels: un
#: "je ne sais pas" sans raison est aussi inutile qu'un faux constat.
MOTIF_NON_PARCOURUE = "RUBRIQUE_NON_PARCOURUE"
MOTIF_CLOTURE = "CLOTURE_INSUFFISANTE"
MOTIF_EMPLACEMENT = "EMPLACEMENT_INDETERMINE"
MOTIF_COLLISION = "CLE_NON_INJECTIVE"

_EXPLICATIONS = {
    MOTIF_NON_PARCOURUE: (
        "La rubrique n'a pas ete parcourue lors d'au moins un des deux passages. "
        "Une piece absente d'un passage ou personne n'est alle n'a pas ete "
        "retiree: elle n'a pas ete vue."
    ),
    MOTIF_CLOTURE: (
        "Rien ne prouve que la liste observee etait complete a l'une des deux "
        "dates: ni total annonce par l'editeur, ni index entier constate. Une "
        "absence peut n'etre qu'une portion non affichee."
    ),
    MOTIF_EMPLACEMENT: (
        "Une composante de la cle manque - rubrique ou libelle. La piece est "
        "journalisee, mais elle ne peut etre comparee a rien."
    ),
    MOTIF_COLLISION: (
        "Plusieurs pieces partagent cet emplacement dans un des deux passages. "
        "La cle ne distingue donc pas ces pieces, et tout verdict les "
        "confondrait."
    ),
}


def explication(motif: str) -> str:
    """La phrase a montrer a un coproprietaire, pour un motif donne."""
    return _EXPLICATIONS.get(motif, motif)


# ---------------------------------------------------------------------------
# Qualification de la cle, refaite a chaque passage
# ---------------------------------------------------------------------------


def collisions(pieces: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Emplacements portes par plus d'une piece dans un meme passage.

    **Cette mesure est refaite a chaque passage, et c'est le point.** La cle a
    ete mesuree injective le 2026-09-04 sur un index reel - 115 pieces, 115
    cles - mais cette mesure vaut pour cet editeur, a cet instant. Rien
    n'empeche un syndic de creer demain deux pieces de meme libelle dans un
    meme groupe.

    Un outil qui aurait pris l'injectivite pour acquise fusionnerait ces deux
    pieces en silence, et ferait disparaitre un retrait reel. Ici, la propriete
    dont depend le verdict est **verifiee a chaque fois qu'on s'en sert**, et
    son echec degrade proprement: les emplacements en collision passent
    `INDETERMINE`, le reste du passage continue de produire des constats.
    """
    compte = Counter(
        piece.get("emplacement", "")
        for piece in pieces
        if piece.get("emplacement_qualite") == EMPLACEMENT_QUALIFIE
        and piece.get("emplacement")
    )
    return {cle: n for cle, n in compte.items() if n > 1}


def _index(pieces: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {
        piece["emplacement"]: piece
        for piece in pieces
        if piece.get("emplacement_qualite") == EMPLACEMENT_QUALIFIE
        and piece.get("emplacement")
    }


def _rubriques(lignes: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {ligne["rubrique_code"]: ligne for ligne in lignes}


def _constat(
    emplacement_cle: str,
    verdict: str,
    *,
    motif: str = "",
    avant: Mapping[str, Any] | None = None,
    apres: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    rubrique, groupe, libelle = composantes(emplacement_cle)
    return {
        "emplacement": emplacement_cle,
        "rubrique_code": rubrique,
        "groupe": groupe,
        "libelle": libelle,
        "verdict": verdict,
        "motif": motif,
        "explication": explication(motif) if motif else "",
        "empreinte_avant": (avant or {}).get("empreinte", ""),
        "empreinte_apres": (apres or {}).get("empreinte", ""),
    }


def _peut_conclure_absence(
    rub_a: Mapping[str, Any] | None, rub_b: Mapping[str, Any] | None
) -> str:
    """Rend un motif d'indetermination, ou la chaine vide si l'on peut conclure."""
    for rubrique in (rub_a, rub_b):
        if rubrique is None or rubrique.get("etat") != RUBRIQUE_PARCOURUE:
            return MOTIF_NON_PARCOURUE
    for rubrique in (rub_a, rub_b):
        if (rubrique or {}).get("cloture", CLOTURE_AUCUNE) == CLOTURE_AUCUNE:
            return MOTIF_CLOTURE
    return ""


def comparer(
    avant: Mapping[str, Any],
    apres: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare deux passages et rend les constats.

    `avant` et `apres` portent chacun `rubriques` et `pieces`, tels que
    `_extranet_store.lire_passage` les rend.

    Le resultat porte les constats **et** le compte de ce qui n'a pas pu etre
    juge. Les deux comptent: une liste de trois changements tiree d'un passage
    ou vingt rubriques n'ont pas ete parcourues n'a pas le meme sens qu'une
    liste de trois changements tiree d'un passage complet, et l'ecran doit
    pouvoir le dire.
    """
    pieces_a = list(avant.get("pieces", ()))
    pieces_b = list(apres.get("pieces", ()))
    rub_a = _rubriques(list(avant.get("rubriques", ())))
    rub_b = _rubriques(list(apres.get("rubriques", ())))

    col_a = collisions(pieces_a)
    col_b = collisions(pieces_b)
    index_a = _index(pieces_a)
    index_b = _index(pieces_b)

    # Index des noms serveur du passage recent. Il ne sert qu'a distinguer un
    # deplacement d'une disparition; il n'est jamais une cle de comparaison, et
    # il ne quitte jamais la machine - chez un autre editeur ce nom peut porter
    # un patronyme.
    noms_b: dict[str, Mapping[str, Any]] = {}
    for piece in pieces_b:
        nom = (piece.get("nom_serveur") or "").strip()
        if nom and nom not in noms_b:
            noms_b[nom] = piece

    constats: list[dict[str, Any]] = []
    non_comparables = 0

    for piece in pieces_a + pieces_b:
        if piece.get("emplacement_qualite") != EMPLACEMENT_QUALIFIE:
            non_comparables += 1

    for cle in sorted(set(index_a) | set(index_b)):
        rubrique = composantes(cle)[0]
        ra, rb = rub_a.get(rubrique), rub_b.get(rubrique)

        if cle in col_a or cle in col_b:
            constats.append(_constat(cle, INDETERMINE, motif=MOTIF_COLLISION))
            continue

        dans_a, dans_b = cle in index_a, cle in index_b

        if dans_a and dans_b:
            pa, pb = index_a[cle], index_b[cle]
            verifie = (
                pa.get("contenu_etat") == CONTENU_VERIFIE
                and pb.get("contenu_etat") == CONTENU_VERIFIE
                and pa.get("empreinte")
                and pb.get("empreinte")
            )
            if not verifie:
                constats.append(
                    _constat(cle, PRESENCE_INCHANGEE, avant=pa, apres=pb)
                )
            elif pa["empreinte"] != pb["empreinte"]:
                constats.append(_constat(cle, MODIFICATION, avant=pa, apres=pb))
            else:
                constats.append(_constat(cle, INCHANGE, avant=pa, apres=pb))
            continue

        if dans_b:
            # Un ajout se conclut des que la rubrique a ete parcourue au
            # passage recent: la piece est la, on l'a vue. Nul besoin de
            # prouver que l'ancien passage etait complet.
            if rb is None or rb.get("etat") != RUBRIQUE_PARCOURUE:
                constats.append(
                    _constat(cle, INDETERMINE, motif=MOTIF_NON_PARCOURUE)
                )
            elif ra is None or ra.get("etat") != RUBRIQUE_PARCOURUE:
                constats.append(
                    _constat(cle, INDETERMINE, motif=MOTIF_NON_PARCOURUE)
                )
            else:
                constats.append(_constat(cle, AJOUT, apres=index_b[cle]))
            continue

        # Reste le cas du retrait, le seul qui exige tout.
        motif = _peut_conclure_absence(ra, rb)
        if motif:
            constats.append(_constat(cle, INDETERMINE, motif=motif, avant=index_a[cle]))
            continue

        # Garde anti-renommage, ajoutee le 2026-09-04 apres mesure.
        #
        # La cle d'emplacement ne protege pas contre le renommage: une piece
        # renommee disparait de son emplacement et reapparait ailleurs, ce qui
        # produirait un faux retrait ET un faux ajout. C'etait la faiblesse
        # nommee de la conception, et elle n'avait d'autre remede que
        # l'empreinte du contenu - donc un telechargement.
        #
        # La mesure a ouvert une voie beaucoup moins chere. Sur l'index reel,
        # le nom servi par `content-disposition` est **injectif sur la totalite
        # de l'index**: 115 pieces, 115 noms, zero collision - et 40 noms
        # distincts la ou le libelle n'en donne que 8. Il s'obtient par une
        # requete HEAD, sans corps de reponse.
        #
        # Deux cles independantes valent donc mieux qu'une: leur accord affermit
        # le constat, et leur desaccord est lui-meme une information. Ici, si le
        # nom reparait ailleurs, la piece a bouge - elle n'a pas disparu.
        nom = (index_a[cle].get("nom_serveur") or "").strip()
        if nom and nom in noms_b:
            constats.append(
                _constat(cle, DEPLACE, avant=index_a[cle], apres=noms_b[nom])
            )
        else:
            constats.append(_constat(cle, RETRAIT, avant=index_a[cle]))

    comptes = Counter(constat["verdict"] for constat in constats)
    return {
        "passage_avant": avant.get("passage", {}).get("passage_id", ""),
        "passage_apres": apres.get("passage", {}).get("passage_id", ""),
        "constats": constats,
        "comptes": dict(comptes),
        "pieces_non_comparables": non_comparables,
        "collisions_avant": col_a,
        "collisions_apres": col_b,
        "rubriques_non_parcourues": sorted(
            code
            for code in set(rub_a) | set(rub_b)
            if (rub_a.get(code) or {}).get("etat") != RUBRIQUE_PARCOURUE
            or (rub_b.get(code) or {}).get("etat") != RUBRIQUE_PARCOURUE
        ),
    }


#: Ordre d'affichage des constats. Il n'est pas cosmetique: une alerte qui se
#: declenche a chaque remaniement d'interface n'est plus lue au bout de deux
#: semaines, et c'est le retrait - l'evenement le plus precieux - qui se perd
#: dans le bruit.
RANG_VERDICT = {
    RETRAIT: 0,
    MODIFICATION: 1,
    DEPLACE: 1,
    INDETERMINE: 2,
    AJOUT: 3,
    PRESENCE_INCHANGEE: 4,
    INCHANGE: 5,
}


def trier(constats: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Les constats, du plus grave au plus anodin."""
    return sorted(
        constats,
        key=lambda c: (
            RANG_VERDICT.get(c.get("verdict", ""), 9),
            c.get("rubrique_code", ""),
            c.get("groupe", ""),
            c.get("libelle", ""),
        ),
    )
