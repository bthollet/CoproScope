# -*- coding: utf-8 -*-
"""Le gouvernail est un JOURNAL. Ce qui est engage tient dans une file courte.

**Le defaut mesure le 2026-09-09, et il est arithmetique.** Le taux d'arrivee
sur le taux de fermeture valait **4,8 pour 1**. Au-dessus de 1 soutenu, un
registre cesse d'etre un outil de pilotage et devient un journal - ce qui n'est
pas un defaut en soi, un defaut connu valant mieux qu'un defaut invisible. Le
defaut est de s'en servir pour savoir ou l'on en est.

Consigne de Brice du 2026-09-09, apres avoir lu les pratiques du metier:
*mets en place ces outils*, et *pour la file, c'est toi qui connais les bons
standards*.

**Ce que cet outil fait, et surtout ce qu'il ne fait pas.**

Il ne cree **aucun second registre**. Ecrire les items ailleurs reproduirait le
defaut numero un du produit - plusieurs comptages concurrents pour la meme
notion, constate le 2026-09-02 sur l'interface reelle avec quatre comptages
pour une seule notion. La file est donc **derivee** du gouvernail: elle se
recalcule a chaque appel, et il n'existe qu'une seule source.

Il ne remplit pas la file a votre place. Un item entre dans la file parce qu'un
humain l'y engage, pas parce qu'un statut le suggere. **Une file se decide et
se plafonne; elle ne se derive pas d'une intention ecrite dans une colonne.**
Mesure du 2026-09-09 qui l'impose: 55 items sur 70 portaient une *prochaine
action* renseignee - la colonne mesurait une intention, pas un engagement.

**Les quatre etats, et pourquoi ils ne se recouvrent pas.**

- `ENGAGE` - quelqu'un y travaille maintenant. C'est cela qui se plafonne.
- `DECISION` - la balle est chez l'humain, l'outil ne peut rien.
- `JOURNAL` - un defaut connu, tenu par une garde, que personne ne traite.
- `CLOS` - tranche, dans un sens ou dans l'autre.

Le troisieme etat est celui qui manquait. Sans lui, tout defaut connu compte
comme du travail en retard, et le compte d'`ACTIF` devient ininterpretable.

**Les deux plafonds, et le second est le vrai goulot.**

Trois items engages a la fois - standard du kanban personnel pour une personne
seule. Cinq decisions en attente au maximum: mesure du 2026-09-09, **13
decisions attendaient Brice**, et aucun debit de developpement ne rattrape
cela. Au-dela d'un plafond, **rien n'entre tant que rien ne sort**.

**La politique d'age.** Un item que personne n'a touche depuis 90 jours est
revu ou ferme. La regle du metier est: *si ca n'a pas valu la peine en trois
mois, ca se ferme - ca reviendra si ca compte*. Cet outil ne ferme rien tout
seul: il **nomme** les items concernes. Fermer est une decision.

**Ce que cet outil REFUSE de faire, et c'est la lecon du jour.** Il ne verifie
jamais qu'un compte reste au-dessus d'un seuil. Une garde ecrite ce matin
exigeait `len(mesurees) > 10` sur un ensemble qui ne contient que les P0 encore
`ACTIF`: **elle a echoue le jour ou un chantier a abouti**. Une garde qui exige
que le backlog reste plein est une garde a l'envers. Ici, tous les plafonds sont
des maxima, jamais des minima.

Usage:

    python tools/file_travail.py            # l'etat de la file
    python tools/file_travail.py --age 90   # + les items dormants
    python tools/file_travail.py --json     # pour un autre outil

Code de sortie: 0 si les plafonds sont tenus, 1 si l'un est depasse, 2 si le
gouvernail n'a pas pu etre lu - trois etats, parce que *pas regarde* n'est
jamais *rien a signaler*.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

DEPOT = Path(__file__).resolve().parent.parent
GOUVERNAIL = DEPOT / "docs" / "roadmap_backlog_central.md"

#: Plafonds. Ce sont des MAXIMA. Aucun n'est un minimum, et aucun controle de
#: cet outil ne devient faux quand le backlog se vide.
PLAFOND_ENGAGE = 3
PLAFOND_DECISION = 5
AGE_DORMANT_JOURS = 90

#: Un separateur de cellule qui respecte l'echappement. **Deux mesures fausses
#: le 2026-09-10 sont venues d'un `split` sur la barre nue:** une cellule
#: complete de 1 052 caracteres lue comme tronquee a 751, parce que la cellule
#: citait elle-meme un tableau chiffre a barres echappees. Un decoupage qui
#: ignore l'echappement rend une cellule coupee et parfaitement credible.
_BS = chr(92)
SEPARATEUR = re.compile("(?<!" + _BS + _BS + ")" + _BS + "|")

ETAT_ENGAGE = "ENGAGE"
ETAT_DECISION = "DECISION"
ETAT_JOURNAL = "JOURNAL"
ETAT_CLOS = "CLOS"

#: Comment un statut du gouvernail se lit en etat de file. Le tableau est
#: explicite parce que la correspondance est une DECISION, pas une evidence:
#: `PRET_A_INTEGRER` n'est pas du travail engage, c'est du travail fini qui
#: attend une integration - le compter comme engage gonflerait la file de tout
#: ce qui a deja abouti.
ETAT_PAR_STATUT = {
    "ACTIF": ETAT_ENGAGE,
    "BACKLOG": ETAT_JOURNAL,
    "ROADMAP": ETAT_JOURNAL,
    "CLOTURE": ETAT_CLOS,
    "SUPERSEDE": ETAT_CLOS,
    "A_ARBITRER": ETAT_DECISION,
    "EN_ATTENTE_USER": ETAT_DECISION,
    "PRET_A_INTEGRER": ETAT_JOURNAL,
    "A_QUALIFIER": ETAT_JOURNAL,
    "BLOQUE": ETAT_JOURNAL,
    "INTEGRE": ETAT_CLOS,
    "ABANDONNE": ETAT_CLOS,
}
STATUTS = tuple(ETAT_PAR_STATUT)
PRIORITES = ("P0", "P1", "P2", "P3")

_DATE = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")


class GouvernailIllisible(RuntimeError):
    """Le gouvernail n'a pas pu etre lu. Ce n'est pas *rien a signaler*."""


def _nu(cellule: str) -> str:
    return cellule.strip().strip("`").strip()


#: Le titre de la section qui porte le registre actif. **Lire tout le document
#: donnait 185 items la ou le registre en porte 161:** quatre sections
#: differentes alignent des lignes `RM-*` - le registre actif, mais aussi
#: `Hors file d'execution`, `Temps humain explicite` et une synthese de mai.
#: Un outil qui les additionne fabrique un cinquieme comptage concurrent, ce
#: qu'il existe precisement pour eviter.
SECTION_REGISTRE = "Registre actif par identifiant"


def _lignes_du_registre(texte: str) -> list[str]:
    """Les lignes d'item de la SEULE section du registre actif.

    Refuse au lieu de rabattre sur le document entier: si le titre change, le
    bon comportement est de le dire, pas de compter autre chose.
    """
    dedans = False
    lignes: list[str] = []
    for ligne in texte.splitlines():
        if ligne.startswith("#"):
            dedans = SECTION_REGISTRE.lower() in ligne.lower()
            continue
        if dedans and ligne.startswith("| `RM-"):
            lignes.append(ligne)
    return lignes


def lire_items(chemin: Path | None = None) -> list[dict]:
    """Les items du registre actif, un dictionnaire par ligne `RM-*`."""
    chemin = chemin or GOUVERNAIL
    try:
        texte = chemin.read_text(encoding="utf-8")
    except OSError as exc:
        raise GouvernailIllisible(f"{chemin}: {exc}") from exc

    items: list[dict] = []
    for ligne in _lignes_du_registre(texte):
        cellules = [c.strip() for c in SEPARATEUR.split(ligne)]
        nus = [_nu(c) for c in cellules]
        statut = next((v for v in nus if v in STATUTS), "")
        priorite = next((v for v in nus if v in PRIORITES), "")
        items.append({
            "id": nus[1] if len(nus) > 1 else "",
            "titre": cellules[2] if len(cellules) > 2 else "",
            "statut": statut,
            "priorite": priorite,
            "etat": ETAT_PAR_STATUT.get(statut, ETAT_JOURNAL),
            "derniere_date": _derniere_date(ligne),
        })
    if not items:
        raise GouvernailIllisible(
            f"{chemin}: aucune ligne lue dans la section "
            f"'{SECTION_REGISTRE}'. Le titre a change, le tableau a change de "
            "forme, ou le decoupage des cellules ne le reconnait plus. "
            "Compter les autres sections a la place fabriquerait un comptage "
            "concurrent, ce que cet outil existe pour eviter."
        )
    return items


def _derniere_date(ligne: str) -> str:
    """La date la plus recente citee sur la ligne, ou une chaine vide.

    Le gouvernail n'a pas de colonne *derniere touche* fiable: la date de
    derniere mise a jour est en fin de ligne, mais l'analyse en cite beaucoup
    d'autres. Prendre la PLUS RECENTE est le choix prudent pour une politique
    d'age: il sous-estime le dormant, donc il ne reveille personne pour rien.
    """
    trouvees = _DATE.findall(ligne)
    if not trouvees:
        return ""
    return max("-".join(t) for t in trouvees)


def etat_de_la_file(items: list[dict], age_jours: int = AGE_DORMANT_JOURS,
                    aujourdhui: date | None = None) -> dict:
    """Ce que la file dit, plafonds compris. Ne ferme rien, ne decide rien."""
    aujourdhui = aujourdhui or date.today()
    par_etat: dict[str, list[dict]] = {ETAT_ENGAGE: [], ETAT_DECISION: [],
                                       ETAT_JOURNAL: [], ETAT_CLOS: []}
    for item in items:
        par_etat[item["etat"]].append(item)

    dormants = []
    for item in items:
        if item["etat"] == ETAT_CLOS or not item["derniere_date"]:
            continue
        try:
            vue = datetime.strptime(item["derniere_date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        if (aujourdhui - vue).days >= age_jours:
            dormants.append({**item, "jours": (aujourdhui - vue).days})

    depassements = []
    if len(par_etat[ETAT_ENGAGE]) > PLAFOND_ENGAGE:
        depassements.append(
            "%d items engages pour un plafond de %d: rien de neuf n'entre tant "
            "que rien ne sort" % (len(par_etat[ETAT_ENGAGE]), PLAFOND_ENGAGE))
    if len(par_etat[ETAT_DECISION]) > PLAFOND_DECISION:
        depassements.append(
            "%d decisions en attente pour un plafond de %d: le goulot n'est pas "
            "le developpement" % (len(par_etat[ETAT_DECISION]), PLAFOND_DECISION))

    return {
        "items": len(items),
        "engages": [i["id"] for i in par_etat[ETAT_ENGAGE]],
        "decisions": [i["id"] for i in par_etat[ETAT_DECISION]],
        "journal": len(par_etat[ETAT_JOURNAL]),
        "clos": len(par_etat[ETAT_CLOS]),
        "plafond_engage": PLAFOND_ENGAGE,
        "plafond_decision": PLAFOND_DECISION,
        "depassements": depassements,
        "dormants": sorted(dormants, key=lambda d: -d["jours"]),
        "age_jours": age_jours,
    }


def _rendre(etat: dict) -> None:
    print("Le gouvernail est un JOURNAL. Voici la FILE qui en derive.")
    print()
    print("  items au registre        : %d" % etat["items"])
    print("  ENGAGE   (on y travaille): %d / %d  %s"
          % (len(etat["engages"]), etat["plafond_engage"],
             " ".join(etat["engages"]) or "-"))
    print("  DECISION (la balle chez toi): %d / %d  %s"
          % (len(etat["decisions"]), etat["plafond_decision"],
             " ".join(etat["decisions"]) or "-"))
    print("  JOURNAL  (connu, tenu, non traite): %d" % etat["journal"])
    print("  CLOS                     : %d" % etat["clos"])
    print()
    if etat["depassements"]:
        print("PLAFONDS DEPASSES:")
        for d in etat["depassements"]:
            print("  - " + d)
    else:
        print("Plafonds tenus.")
    if etat["dormants"]:
        print()
        print("DORMANTS depuis %d jours ou plus - a revoir ou a fermer, "
              "et fermer est une DECISION:" % etat["age_jours"])
        for d in etat["dormants"][:20]:
            print("  %-16s %4d jours  %s" % (d["id"], d["jours"], d["statut"]))
        if len(etat["dormants"]) > 20:
            print("  ... et %d autres" % (len(etat["dormants"]) - 20))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="La file de travail derivee du gouvernail.")
    parser.add_argument("--age", type=int, default=AGE_DORMANT_JOURS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        items = lire_items()
    except GouvernailIllisible as exc:
        print("file_travail: le gouvernail n'a PAS PU etre lu - %s" % exc,
              file=sys.stderr)
        return 2

    etat = etat_de_la_file(items, age_jours=args.age)
    if args.json:
        print(json.dumps(etat, ensure_ascii=False, indent=2))
    else:
        _rendre(etat)
    return 1 if etat["depassements"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
