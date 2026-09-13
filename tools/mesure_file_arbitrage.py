"""Mesure la file d'arbitrage du caviardage: combien de decisions humaines.

Repond au critere `A5bis` de `docs/cadrage_annuaire_verificateur_biffage_2026-09-07.md`:
la file de formes suspectes produite par `suspects_residuels` est-elle
consommable par un humain, et selon quel decoupage.

**Pourquoi ceci est un outil et non un test.** Son entree est
`corpus_caviarde_suspects.csv`, qui vit en C8 d'une instance et contient par
construction des noms NON CAVIARDES. Ce fichier n'entre jamais dans Git, donc la
mesure n'est pas rejouable en CI. Elle est rejouable par quiconque dispose de
l'instance, ce qui est la seule reproductibilite possible ici.

**Garde de confidentialite.** Ce script n'imprime que des entiers et des
libelles fixes. Aucune forme, aucun nom, aucun `doc_id` ne sort. C'est la
condition pour que le resultat soit publiable dans un document de cadrage.

Usage, depuis la racine du depot:

    $env:PYTHONPATH = "server/src"
    server/.venv/Scripts/python.exe tools/mesure_file_arbitrage.py <dossier> [<dossier> ...]

Chaque `<dossier>` porte `corpus_caviarde_suspects.csv` et, si disponible,
`annuaire_personnes.csv`.

Mesure de reference du 2026-09-07, sur les deux corpus du lot
`corpus_caviarde_lot_20260904` - Tilleuls (32 pieces) et Erables (pseudo)
(22 pieces, second cabinet):

| | formes | occurrences | groupes | reduction | >= 2 documents |
|---|---:|---:|---:|---:|---:|
| Tilleuls | 582 | 4 140 | 543 | 7 % | 182 (-66 %) |
| Erables (pseudo) | 1 046 | 5 742 | 952 | 9 % | 346 (-64 %) |

Conclusion qui a refute le critere `A5` initial: le groupement par racine ne
reduit rien, parce que la distribution est plate. C'est la partition sur le
nombre de documents qui rend la file consommable.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

try:
    from coproscope.modules.biffageops import normalize_identity_key
except ImportError:  # noqa: BLE001
    print(
        "Import impossible. Poser le chemin des sources de l'arbre COURANT:\n"
        '    $env:PYTHONPATH = "server/src"\n'
        "Sans chemin explicite rien ne s'importe; avec un chemin explicite c'est\n"
        "forcement l'arbre courant. Voir CLAUDE.md, section venv.",
        file=sys.stderr,
    )
    raise SystemExit(2)


SUSPECTS = "corpus_caviarde_suspects.csv"
ANNUAIRE = "annuaire_personnes.csv"


def _lire(chemin: Path) -> list[dict[str, str]]:
    with chemin.open(encoding="utf-8-sig", newline="") as flux:
        return list(csv.DictReader(flux))


def _racine(forme: str) -> str:
    """Le token le plus long d'une forme, proxy du patronyme."""

    tokens = [cle for cle in (normalize_identity_key(mot) for mot in forme.split()) if cle]
    return max(tokens, key=len) if tokens else ""


def _decisions_pour_couvrir(poids: dict[str, int], fraction: float) -> int:
    """Combien de decisions, prises des plus lourdes, pour couvrir `fraction`."""

    total = sum(poids.values())
    if not total:
        return 0
    cible = total * fraction
    cumul = 0
    for rang, valeur in enumerate(sorted(poids.values(), reverse=True), start=1):
        cumul += valeur
        if cumul >= cible:
            return rang
    return len(poids)


def mesure(dossier: Path) -> dict[str, int] | None:
    """Comptages agreges pour un corpus. Ne rend aucune chaine du corpus."""

    chemin_suspects = dossier / SUSPECTS
    if not chemin_suspects.exists():
        return None

    chemin_annuaire = dossier / ANNUAIRE
    patronymes_connus = set()
    nb_annuaire = 0
    if chemin_annuaire.exists():
        entrees = _lire(chemin_annuaire)
        nb_annuaire = len(entrees)
        patronymes_connus = {row.get("nom_normalise", "") for row in entrees} - {""}

    occurrences: dict[str, int] = defaultdict(int)
    documents: dict[str, set[str]] = defaultdict(set)
    formes_vues: set[str] = set()

    for row in _lire(chemin_suspects):
        forme = row.get("forme", "")
        if not forme:
            continue
        formes_vues.add(forme)
        racine = _racine(forme)
        if not racine:
            continue
        occurrences[racine] += int(row.get("occurrences") or 0)
        documents[racine].add(row.get("doc_id", ""))

    groupes = len(occurrences)
    formes = len(formes_vues)
    return {
        "formes": formes,
        "occurrences": sum(occurrences.values()),
        "groupes": groupes,
        "reduction_groupement": round(100 * (1 - groupes / formes)) if formes else 0,
        "une_seule_occurrence": sum(1 for total in occurrences.values() if total == 1),
        "un_seul_document": sum(1 for cle in occurrences if len(documents[cle]) == 1),
        "deux_documents_ou_plus": sum(1 for cle in occurrences if len(documents[cle]) >= 2),
        "decisions_80": _decisions_pour_couvrir(occurrences, 0.80),
        "decisions_95": _decisions_pour_couvrir(occurrences, 0.95),
        "racines_deja_connues": sum(1 for cle in occurrences if cle in patronymes_connus),
        "annuaire": nb_annuaire,
    }


def main(arguments: list[str]) -> int:
    if not arguments:
        print(__doc__)
        return 2

    entetes = [
        ("formes", "formes"),
        ("occurrences", "occur."),
        ("groupes", "groupes"),
        ("reduction_groupement", "-%"),
        ("deux_documents_ou_plus", ">=2 doc"),
        ("decisions_95", "95%"),
        ("racines_deja_connues", "connues"),
        ("annuaire", "annuaire"),
    ]
    print(f"{'corpus':<24}" + "".join(f"{libelle:>10}" for _, libelle in entetes))
    print("-" * (24 + 10 * len(entetes)))

    manquants = 0
    for argument in arguments:
        dossier = Path(argument)
        resultat = mesure(dossier)
        # Le nom du dossier est un chemin choisi par l'operateur, pas une donnee
        # du corpus. On n'imprime que son dernier segment.
        etiquette = dossier.name[:23]
        if resultat is None:
            print(f"{etiquette:<24}{SUSPECTS} absent")
            manquants += 1
            continue
        print(f"{etiquette:<24}" + "".join(f"{resultat[cle]:>10}" for cle, _ in entetes))

    print()
    print("groupes  = formes regroupees sur le token le plus long (proxy patronyme)")
    print("-%       = reduction apportee par ce groupement seul")
    print(">=2 doc  = groupes vus dans au moins deux pieces: la partition qui tient")
    print("95%      = decisions necessaires pour couvrir 95% des occurrences")
    print("connues  = groupes dont la racine est deja un patronyme de l'annuaire")
    print()
    print("Rappel: la partition sur >=2 documents est un ORDRE DE PASSAGE, jamais un")
    print("filtre. Une fuite dans une seule piece reste une fuite; tant que le second")
    print("lot n'est pas traite, le derive doit le dire dans sa reserve.")
    return 1 if manquants else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
