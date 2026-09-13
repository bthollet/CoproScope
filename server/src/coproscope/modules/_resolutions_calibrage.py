"""Auto-calibrage du gabarit d'un proces-verbal.

Trouver comment CE document numerote ses resolutions, sans detecteur ecrit a
la main pour chaque modele de syndic.
"""

from __future__ import annotations

import re

from ._resolutions_cloture import ancres, hors_des_clotures
from ._resolutions_motifs import (
    MAJORITE_RE,
    MINIMUM_SERIE,
    NUMERO_RE_A,
    NUMERO_RE_B_FLUX,
    NUMERO_RE_B_LIGNE,
    NUMERO_RE_PREFIXE,
    TITRE_ODJ_RE,
    PAS_DE_VOTE_RE,
    POUR_RE,
    SIGNATURE_RE,
)

#
# Ecrire un detecteur par modele de PV ne passe pas a l'echelle: dix assemblees
# d'une seule copropriete ont deja produit trois numerotations differentes.
#
# Mais un PV est massivement repetitif - des dizaines de blocs quasi identiques.
# Le document est donc son propre jeu d'etalonnage: on cherche le jeton qui
# COMPTE, c'est-a-dire celui dont la valeur progresse d'un bloc au suivant.
#
# Deux temps:
#   1. les formules de cloture decoupent des blocs approximatifs. Ce module ne
#      choisit pas laquelle: il demande a `_resolutions_cloture.ancres`, qui
#      prefere la formule mesuree des cabinets connus et ne passe a la forme
#      large que si celle-ci ne rend rien en serie;
#   2. dans ces blocs, on cherche la signature typographique dont les nombres
#      forment la plus longue suite croissante. C'est la numerotation.



def _signature(suffixe: str) -> str:
    return re.sub(r"\s+", "", suffixe)


def _plus_longue_suite(valeurs: list[int]) -> int:
    """Longueur de la plus longue progression croissante par pas de 1."""
    meilleure = courante = 1 if valeurs else 0
    for avant, apres in zip(valeurs, valeurs[1:]):
        courante = courante + 1 if apres == avant + 1 else 1
        meilleure = max(meilleure, courante)
    return meilleure


def _blocs(text: str, positions: list[int]) -> list[str]:
    bornes = positions + [len(text)]
    return [text[bornes[i]:bornes[i + 1]] for i in range(len(positions))]


def _bloc_qualifie(bloc: str) -> bool:
    """Un bloc est une resolution s'il annonce une majorite ET tranche.

    C'est le second signal qui separe une vraie numerotation du bruit: une date
    ou un montant precede d'un tiret n'est jamais suivi d'une annonce de
    majorite puis d'un vote.
    """
    if not MAJORITE_RE.search(bloc):
        return False
    return bool(
        ancres(bloc)[0]
        or POUR_RE.search(bloc)
        or PAS_DE_VOTE_RE.search(bloc)
    )


def calibrate(text: str) -> dict[str, object] | None:
    """Deduit du texte lui-meme la signature de sa numerotation.

    Rend None quand le document ne porte pas assez de repetition pour qu'un
    gabarit soit etabli: mieux vaut ne rien affirmer que calibrer sur du bruit.
    """
    ancrages, _ = ancres(text)
    if len(ancrages) < MINIMUM_SERIE:
        return None

    par_signature: dict[str, list[tuple[int, int]]] = {}
    for match in SIGNATURE_RE.finditer(text):
        par_signature.setdefault(_signature(match.group(2)), []).append(
            (int(match.group(1)), match.start())
        )

    meilleur: dict[str, object] | None = None
    for signature, marques in par_signature.items():
        if len(marques) < 3:
            continue
        valeurs = [n for n, _ in marques]
        if min(valeurs) > 3:
            continue
        blocs = _blocs(text, [pos for _, pos in marques])
        qualifies = sum(1 for bloc in blocs if _bloc_qualifie(bloc))
        # Le second signal FILTRE le bruit; il ne classe pas. Une signature
        # frequente produit mecaniquement beaucoup de blocs qualifies sans etre
        # pour autant une numerotation.
        if qualifies < 3 or qualifies / len(marques) < 0.5:
            continue
        candidat = {
            "signature": signature,
            "occurrences": len(marques),
            "qualifies": qualifies,
            "suite": _plus_longue_suite(valeurs),
            "premier": min(valeurs),
            "dernier": max(valeurs),
            "ancres": len(ancrages),
        }
        # Ce qui distingue une numerotation, c'est qu'elle PROGRESSE. La plus
        # longue suite croissante est donc le critere de tri; le taux de blocs
        # qualifies departage a egalite.
        if meilleur is None or (candidat["suite"], candidat["qualifies"]) > (
            meilleur["suite"],
            meilleur["qualifies"],
        ):
            meilleur = candidat
    return meilleur


def _marqueurs_calibres(text: str, signature: str) -> list[tuple[int, int]]:
    motif = re.escape(signature).replace(r"\°", "°")
    regex = re.compile(
        rf"(?<![\d,.])(\d{{1,3}})\s*{motif[1:] if motif.startswith('°') else motif}\s*(?=[A-Za-zÀ-ÿ«\"])"
    )
    return [(int(m.group(1)), m.start()) for m in regex.finditer(text)]


def detect_family(text: str) -> str:
    """Famille de modele du PV, deduite des marqueurs presents.

    On ne devine pas: si aucun marqueur ne domine, on rend "inconnue" et
    l'appelant saura que le document n'a pas ete compris.
    """
    if NUMERO_RE_A.search(text):
        return "A"
    if NUMERO_RE_B_LIGNE.search(text) or NUMERO_RE_B_FLUX.search(text):
        return "B"
    return "inconnue"


def _marqueurs_par_cloture(text: str) -> list[tuple[int, int]]:
    """Repli: une resolution par formule de cloture, numerotee par position.

    Employe quand aucune numerotation credible ne se degage. Le PV du
    20/09/2021 n'en porte aucune de detectable, et ceux de 2025 et 2026 noient
    la leur dans des dizaines de tirets parasites.

    Le numero rendu est alors un RANG, sauf si le document porte sa propre
    numerotation d'ordre du jour, auquel cas elle est preferee - voir plus bas.
    Quand le rang est employe, le registre doit le dire: `numerotation` vaut
    `deduite` et la confiance est plafonnee.

    **Couper apres la cloture, pas avant.** Mesure du 2026-09-03 sur les huit
    assemblees Tilleuls (pseudo): en prenant le DEBUT de la cloture precedente, 337
    intitules sur 432 commencaient par "cette resolution est adoptee" au lieu
    du titre, et 85 n'avaient aucun autre contenu. L'ecran de gouvernance
    affichait donc la formule de vote de la resolution d'avant en guise
    d'intitule.
    """
    ancrages, _ = ancres(text)
    bornes = [(m.start(), m.end()) for m in ancrages]
    if len(bornes) < MINIMUM_SERIE:
        return []
    # Le bloc d'une resolution precede sa formule de cloture: son debut est la
    # FIN de la cloture precedente. Entre les deux subsistent la queue de la
    # formule ("dans les conditions de majorite de l'article 25") et parfois
    # des lignes de vote; TITRE_ODJ_RE les enjambe en visant le titre suivant.
    debuts: list[tuple[int, int]] = []
    numeros: list[int | None] = []
    for rang, depart in enumerate([0] + [fin for _, fin in bornes[:-1]], start=1):
        borne = bornes[rang - 1][0]
        titre = TITRE_ODJ_RE.search(text, depart, borne)
        debuts.append((rang, titre.start() if titre else depart))
        numeros.append(int(titre.group(1)) if titre else None)
    lus = [n for n in numeros if n is not None]
    # La numerotation du document ne remplace le rang que si elle est complete
    # et croissante: un titre isole ne suffit pas a renumeroter le registre.
    if len(lus) >= 0.7 * len(debuts) and lus == sorted(lus) and len(set(lus)) == len(lus):
        return [
            (numero if numero is not None else rang, debut)
            for (rang, debut), numero in zip(debuts, numeros)
        ]
    return debuts


def _marqueurs(text: str) -> list[tuple[int, int]]:
    """Positions numerotees, en preferant la famille qui en rend le plus.

    Un modele B lu avec le motif A rend zero: c'est ce qui faisait manquer
    quatre assemblees sur dix.
    """
    nb_ancres = len(ancres(text)[0])

    def _couvre(marques: list[tuple[int, int]]) -> bool:
        """La numerotation lue explique-t-elle le document.

        Une numerotation qui rend deux fois moins de resolutions qu'il n'y a de
        formules de cloture n'a pas ete comprise: elle en manque la moitie.
        Mesure faite sur le PV du 03/12/2025, 84 clotures espacees de 1134
        caracteres en mediane - donc distinctes - pour 42 numeros lus.
        """
        return nb_ancres == 0 or len(marques) >= 0.7 * nb_ancres

    # Deux formes sont sans ambiguite et suffisent des une occurrence, a
    # condition de couvrir le document: "12° -" et "Resolution n°12". La
    # seconde est la seule qui fonctionne sur une convocation, ou aucune
    # formule de cloture n'existe pour servir d'ancre.
    for regex in (NUMERO_RE_A, NUMERO_RE_PREFIXE):
        marques = [(int(m.group(1)), m.start()) for m in regex.finditer(text)]
        # Un numero cite PAR la formule de vote ferme une resolution, il n'en
        # ouvre pas une. Sans ce filtre, `la resolution n°1 a ete adoptee`
        # ouvrait un second segment qui ne contenait que la fin du premier, et
        # trois resolutions en rendaient six - une sur deux vide.
        marques = hors_des_clotures(marques, text)
        if marques and _couvre(marques):
            return marques

    # Les motifs de la famille B, "12-", sont ambigus: un montant, une date ou une
    # plage horaire y ressemblent. On ne les retient que s'ils forment une
    # numerotation credible - assez nombreux, et commencant bas.
    for regex in (NUMERO_RE_B_LIGNE, NUMERO_RE_B_FLUX):
        trouve = hors_des_clotures(
            [(int(m.group(1)), m.start()) for m in regex.finditer(text)], text
        )
        if len(trouve) >= MINIMUM_SERIE and min(n for n, _ in trouve) <= 3:
            blocs = _blocs(text, [pos for _, pos in trouve])
            qualifie = sum(1 for b in blocs if _bloc_qualifie(b)) / len(trouve) >= 0.5
            if qualifie and _couvre(trouve):
                return trouve
    return _marqueurs_par_cloture(text)


