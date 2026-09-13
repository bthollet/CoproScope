# -*- coding: utf-8 -*-
"""Construit le depot que lit l'artefact du gouvernail, et classe ses references.

`RM-2026-0128`. L'artefact de suivi est une page publiee: elle s'execute dans un
bac a sable navigateur, ou un chemin `C:\\...` ou `docs/note.md` **n'est pas une
adresse**. Brice, le 2026-09-08: *« depuis l'artefact du gouvernail, il y a les
liens des notes MD, mais je ne peux pas les ouvrir »*.

**L'axe, et il vaut au-dela de ce cas.** Une reference n'est ouvrable que si la
page peut **elle-meme produire ce qu'elle promet**. Ce qui varie d'une reference
a l'autre est sa forme - adresse web, chemin de depot, chemin Windows, hote
local, jeton sans forme reconnue, schema qu'on n'a jamais vu. Ce qui reste
invariant le long de cet axe: **la page ne produit que deux choses** - une
adresse que le navigateur atteint, ou un texte qu'elle a embarque. Toute
reference qui n'est ni l'une ni l'autre est **citee en clair avec son motif**,
jamais rendue comme un lien.

**Degradation hors des valeurs observees.** La classe par defaut de
`classer_reference` est `citee`. Une forme inconnue - `ipfs://`, un chemin UNC
`\\\\serveur\\part`, un jeton sans separateur - tombe donc du cote sur, avec un
motif nomme. Aucune enumeration de schemas n'est ecrite ici: on ne reconnait que
`http`/`https`, et tout le reste se degrade.

**Ce que cet outil ne fait pas.** Il ne publie rien. Il ecrit deux fichiers JSON
que l'agent televerse ensuite dans le magasin de la page
(`dashboard/registre`, `dashboard/pieces`). La page, elle, ne lit jamais le
depot: elle lit son magasin. C'est pour cela qu'un depot vieux se voit dans
l'en-tete au lieu de passer pour une lecture fraiche.

Usage, depuis la racine du depot:

    python tools/gouvernail_depot.py --mesure
    python tools/gouvernail_depot.py --ecrire <dossier de sortie>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
# Ce module est charge de deux facons: comme script (`python tools/x.py`, ou le
# dossier du script est sur le chemin) et **par specification de fichier**,
# depuis les tests, ou il ne l'est pas. Le second cas cassait l'import du
# voisin. Le module se rend donc autonome au lieu de l'exiger de ses appelants:
# une dependance qui ne tient que dans un mode de chargement n'en est pas une.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from _gouvernail_magasin import (  # noqa: E402,F401 - re-exportes pour les appelants
    CHAMPS_COUPABLES,
    OCTETS_MAX_DOCUMENT,
    PALIERS_CELLULE,
    ajuster_au_magasin,
    borner_les_pieces,
    octets,
)

DEPOT = Path(__file__).resolve().parents[1]
GOUVERNAIL = DEPOT / "docs" / "roadmap_backlog_central.md"

TITRE_REGISTRE = "## Registre actif par identifiant"

#: L'artefact publie du gouvernail. Une reference qui pointe dessus ne rapporte
#: aucune piece: elle renvoie a la page qu'on est en train de lire.
PAGE_GOUVERNAIL = "9d6c4c65-0423-45bd-a2f5-6bfe9a187ee6"

#: Une barre NUE separe deux cellules; une barre echappee est du texte.
_BARRE_NUE = re.compile(r"(?<!\\)\|")
_ITEM = re.compile(r"^\| `(RM-\d{4}-\d{4})` \|")
_RM = re.compile(r"RM-\d{4}-\d{4}")

#: Onze colonnes, dans l'ordre de l'en-tete du registre. `test_gouvernail_colonnes`
#: garde ce nombre; ici on garde la CORRESPONDANCE entre position et sens.
CHAMPS = ("id", "t", "ty", "st", "p", "o", "src", "a", "ch", "preuve", "maj")

#: Budget de depot. Un magasin de page n'est pas un disque: une piece trop longue
#: se depose tronquee ET le dit, au lieu d'etre promise entiere puis coupee en
#: silence.
CAR_MAX_PIECE = 40_000
CAR_MAX_TOTAL = 600_000

#: Ce que la page sait afficher comme texte. Le reste est cite en clair.
SUFFIXES_LISIBLES = (".md", ".txt", ".csv", ".json", ".yml", ".yaml", ".toml")



# --------------------------------------------------------------------------
# lecture du registre
# --------------------------------------------------------------------------
def cellules(ligne: str) -> list[str]:
    """Les cellules d'une ligne de tableau, barres echappees rendues telles quelles."""
    brut = _BARRE_NUE.split(ligne)
    if len(brut) < 3:
        return []
    # Les accents graves sont la mise en forme Markdown du gouvernail, pas du
    # contenu: `ACTIF` et ACTIF designent le meme statut.
    return [c.strip().replace("\\|", "|").replace("`", "").strip() for c in brut[1:-1]]


def _bloc_registre(texte: str) -> list[str]:
    lignes = texte.splitlines()
    debut = next((i for i, l in enumerate(lignes) if l.startswith(TITRE_REGISTRE)), None)
    if debut is None:
        raise LookupError(
            "titre %r introuvable: le registre a ete renomme ou deplace, et une "
            "mesure qui rendrait zero ligne passerait pour un registre vide"
            % TITRE_REGISTRE
        )
    fin = next(
        (i for i, l in enumerate(lignes[debut + 1:], debut + 1) if l.startswith("## ")),
        len(lignes),
    )
    return lignes[debut:fin]


def lire_registre(texte: str) -> list[dict]:
    """Les lignes d'item du registre, une par identifiant `RM-*`."""
    sorties: list[dict] = []
    for ligne in _bloc_registre(texte):
        if not _ITEM.match(ligne):
            continue
        cel = cellules(ligne)
        if len(cel) != len(CHAMPS):
            # Une ligne mal formee ne se devine pas: elle se signale. Le garde de
            # colonnes vit dans server/tests/test_gouvernail_colonnes.py.
            raise ValueError(
                "ligne de registre a %d cellules au lieu de %d: %s"
                % (len(cel), len(CHAMPS), ligne[:120])
            )
        item = {champ: valeur for champ, valeur in zip(CHAMPS, cel)}
        item["refs"] = sorted(set(_RM.findall(item["preuve"] + " " + item["a"])) - {item["id"]})
        sorties.append(item)
    return sorties


# --------------------------------------------------------------------------
# references
# --------------------------------------------------------------------------
_URL = re.compile(r"https?://[^\s)\"'<>\]]+")
_CHEMIN = re.compile(r"[A-Za-z0-9_.~-]+(?:[\\/][A-Za-z0-9_.~-]+)+")
_HOTE_LOCAL = re.compile(
    r"^(localhost|::1|0\.0\.0\.0|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)"
    r"|\.localhost$"
)
_LETTRE_LECTEUR = re.compile(r"^[a-zA-Z]:[\\/]")


def nomme_un_fichier(brut: str) -> bool:
    """Ce jeton a-t-il barre oblique DESIGNE quelque chose, ou est-ce de la prose ?

    **Axe.** Le gouvernail est ecrit en francais, et le francais met des barres
    obliques partout: `UX/UI`, `go/no-go`, `piece/preuve`,
    `mail/email/e-mail/courriel`. Une premiere version les rendait toutes comme
    des references non ouvrables - 51 fausses references sur 274, chacune
    accompagnee d'un motif qui affirmait faussement *chemin du depot*.

    Ce qui reste invariant: une reference **designe quelque chose**. Deux facons
    de le prouver, aucune enumeration d'extensions: le dernier segment porte un
    point, donc le jeton nomme un fichier; ou bien le chemin **existe** dans le
    depot au moment de la mesure.

    **Residu, et il est volontaire:** un chemin sans point qui a ete SUPPRIME du
    depot n'est plus reconnu comme reference. Il reste affiche dans sa cellule,
    en prose, exactement comme aujourd'hui - la page ne perd rien, elle
    s'abstient de promettre. `test_gouvernail_depot` le fige.
    """
    dernier = re.split(r"[\\/]", brut)[-1]
    if "." in dernier:
        return True
    return (DEPOT / brut.replace("\\", "/")).exists()


def references_de(valeur: str) -> list[str]:
    """Les references citees par une cellule, adresses d'abord, chemins ensuite."""
    texte = str(valeur or "")
    vues: dict[str, None] = {}

    def pousse(brut: str) -> None:
        brut = brut.strip("`").rstrip(".,;:)]")
        if brut:
            vues.setdefault(brut, None)

    for adresse in _URL.findall(texte):
        pousse(adresse)
    reste = _URL.sub(" ", texte)
    for chemin in _CHEMIN.findall(reste):
        # `08/09/2026` n'est pas un chemin; `docs/note.md` en est un.
        if re.search(r"[A-Za-z]", chemin) and nomme_un_fichier(chemin):
            pousse(chemin)
    return list(vues)


@dataclass
class Reference:
    """Une reference et l'issue que la page lui reserve."""

    brut: str
    classe: str  # "distante" | "embarquee" | "citee"
    motif: str = ""
    chemin: str = ""


def _hote(adresse: str) -> str:
    reste = adresse.split("://", 1)[1] if "://" in adresse else adresse
    return reste.split("/", 1)[0].split("@")[-1].split(":")[0].lower()


def classer_reference(
    brut: str, deposes: set[str], motifs: dict[str, str] | None = None
) -> Reference:
    """Classe une reference le long de l'axe: la page peut-elle la produire ?

    La classe par defaut est `citee`. C'est la degradation voulue: une forme
    jamais rencontree ne devient pas un lien, elle devient un texte a copier
    accompagne de son motif.

    `motifs` porte les raisons MESUREES par `embarquer`. Sans lui, deux endroits
    decideraient du meme chemin et pourraient se contredire - ce qui s'est
    produit: un dossier existant etait dit *introuvable* d'un cote et *non
    embarque* de l'autre. Un seul mesureur, une seule raison.
    """
    motifs = motifs or {}
    brut = str(brut or "").strip()
    if not brut:
        return Reference(brut, "citee", "reference vide")

    minuscule = brut.lower()
    if minuscule.startswith(("http://", "https://")):
        if PAGE_GOUVERNAIL in brut:
            return Reference(
                brut, "citee",
                "cette adresse renvoie a la page en cours de lecture: aucune piece apportee",
            )
        hote = _hote(brut)
        if _HOTE_LOCAL.search(hote):
            return Reference(
                brut, "citee",
                "serveur local (%s): cette adresse designe ton poste, qu'une page "
                "publiee n'atteint pas" % hote,
            )
        return Reference(brut, "distante", chemin=brut)

    if "://" in brut or minuscule.startswith("mailto:"):
        schema = brut.split(":", 1)[0]
        return Reference(
            brut, "citee",
            "schema %r: la page n'ouvre que des adresses http et https" % schema,
        )

    if _LETTRE_LECTEUR.match(brut) or brut.startswith("\\\\") or brut.startswith("//"):
        return Reference(
            brut, "citee", "chemin sur ton poste ou ton reseau: la page ne peut ni le lire ni l'ouvrir"
        )

    # `removeprefix`, pas `lstrip`: `lstrip("./")` retire TOUS les points et
    # barres de tete, donc `./.gitignore` devenait `gitignore`. Un seul prefixe
    # est vise, pas un jeu de caracteres.
    normal = brut.replace("\\", "/").removeprefix("./")
    if normal in deposes:
        return Reference(brut, "embarquee", chemin=normal)

    if normal in motifs:
        return Reference(brut, "citee", motifs[normal], chemin=normal)

    if "/" in normal:
        return Reference(
            brut, "citee",
            "chemin du depot non embarque: son texte n'a pas ete depose dans la page",
            chemin=normal,
        )

    return Reference(brut, "citee", "forme non reconnue: la page ne l'ouvre pas plutot que d'en faire un lien mort")


# --------------------------------------------------------------------------
# pieces embarquees
# --------------------------------------------------------------------------
CHAMPS_A_REFERENCES = ("src", "a", "ch", "preuve")


def chemins_cites(lignes: list[dict], seulement: set[str] | None = None) -> list[str]:
    """Les chemins de depot cites par les lignes retenues, dans l'ordre de citation."""
    vus: dict[str, None] = {}
    for item in lignes:
        if seulement is not None and item["id"] not in seulement:
            continue
        for champ in CHAMPS_A_REFERENCES:
            for brut in references_de(item.get(champ, "")):
                ref = classer_reference(brut, set())
                if ref.chemin and not ref.chemin.startswith(("http://", "https://")):
                    vus.setdefault(ref.chemin, None)
    return list(vus)


@dataclass
class Piece:
    chemin: str
    texte: str
    car_total: int
    tronque: bool


@dataclass
class Rapport:
    """Ce que le lot a mesure, et ce qu'il laisse expose.

    `affichees` ne retient que les references des lignes que la page MONTRE -
    les `P0` encore `ACTIF`. C'est la seule population sur laquelle « zero lien
    mort » veut dire quelque chose: une reference d'une ligne jamais rendue
    n'est ni morte ni vivante, elle est absente de l'ecran.
    """

    pieces: list[Piece] = field(default_factory=list)
    non_embarques: list[Reference] = field(default_factory=list)
    distantes: list[Reference] = field(default_factory=list)
    affichees: list[Reference] = field(default_factory=list)

    def mortes(self) -> list[Reference]:
        """Les references rendues comme un lien sans pouvoir tenir la promesse.

        Par construction elle est vide: `classer_reference` ne rend `distante`
        ou `embarquee` que sur une preuve. La garde existe pour que le jour ou
        cette construction change, l'ecart se voie au lieu de se supposer.
        """
        return [
            r for r in self.affichees
            if r.classe == "embarquee" and r.chemin not in {p.chemin for p in self.pieces}
        ]


def embarquer(chemins: list[str]) -> tuple[list[Piece], list[Reference]]:
    """Embarque ce qui est lisible et tient dans le budget; nomme le reste."""
    pieces: list[Piece] = []
    ecartes: list[Reference] = []
    total = 0
    for chemin in chemins:
        cible = DEPOT / chemin
        if not cible.exists():
            ecartes.append(Reference(
                chemin, "citee",
                "chemin du depot introuvable a la mesure: rien a embarquer", chemin=chemin,
            ))
            continue
        if cible.is_dir():
            ecartes.append(Reference(
                chemin, "citee",
                "dossier du depot: la page affiche des textes, pas des arborescences",
                chemin=chemin,
            ))
            continue
        if cible.suffix.lower() not in SUFFIXES_LISIBLES:
            ecartes.append(Reference(
                chemin, "citee",
                "format %s non affichable comme texte par la page" % (cible.suffix or "sans suffixe"),
                chemin=chemin,
            ))
            continue
        try:
            texte = cible.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as erreur:
            ecartes.append(Reference(
                chemin, "citee", "illisible en UTF-8 (%s)" % type(erreur).__name__, chemin=chemin
            ))
            continue
        if total + min(len(texte), CAR_MAX_PIECE) > CAR_MAX_TOTAL:
            ecartes.append(Reference(
                chemin, "citee",
                "budget de depot atteint (%d caracteres deja embarques)" % total,
                chemin=chemin,
            ))
            continue
        coupe = len(texte) > CAR_MAX_PIECE
        pieces.append(Piece(chemin, texte[:CAR_MAX_PIECE], len(texte), coupe))
        total += min(len(texte), CAR_MAX_PIECE)
    return pieces, ecartes


# --------------------------------------------------------------------------
# depot
# --------------------------------------------------------------------------
def _git(*args: str) -> str:
    try:
        return subprocess.run(  # noqa: S603 - arguments fixes, sans shell
            ["git", "-C", str(DEPOT), *args],
            capture_output=True, text=True, timeout=20, check=False,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


#: `RM-2026-0139`. Le registre annoncait *commit <sha>* a cote d'un contenu lu
#: SUR LE DISQUE. Quand le fichier porte des modifications non commitees, les
#: deux ne decrivent pas le meme etat, et **c'est la ligne de commit qui est
#: lue** - un verdict pose a cote de ses faits, forme exacte de `RM-2026-0171`.
#:
#: La regle de Brice: *si c'est la source de verite, elle doit etre commitee a
#: chaque fois qu'elle est modifiee*. Elle repond a ce que la collision avait
#: appris: un predicat correct sur des copies correctes rend quand meme une
#: mauvaise reponse quand deux fils ecrivent dans la meme fenetre.
#:
#: Ce n'est pas une interdiction - modifier avant de commiter est le cours
#: normal d'un lot. C'est une **declaration**: l'etat non commite se dit, la ou
#: le commit s'affiche.
ETAT_COMMITE = "commite"
ETAT_MODIFIE = "modifie-non-commite"
ETAT_INCONNU = "etat-git-inconnu"


def etat_du_gouvernail() -> str:
    """Le gouvernail sur le disque est-il celui du commit annonce ?

    `git status --porcelain` sur le seul fichier du registre. Une sortie vide
    veut dire *identique au commit*; une sortie non vide, *modifie*. Quand git
    ne repond pas - pas de depot, pas de binaire - on rend `ETAT_INCONNU`
    plutot que de laisser croire que la verification a eu lieu.
    """
    if not _git("rev-parse", "--git-dir"):
        return ETAT_INCONNU
    sortie = _git("status", "--porcelain", "--", "docs/roadmap_backlog_central.md")
    return ETAT_MODIFIE if sortie.strip() else ETAT_COMMITE


def construire(maintenant: datetime | None = None) -> tuple[dict, dict, Rapport]:
    texte = GOUVERNAIL.read_text(encoding="utf-8")
    lignes = lire_registre(texte)

    p0_actifs = {o["id"] for o in lignes if o["st"] == "ACTIF" and o["p"] == "P0"}
    pieces, ecartes = embarquer(chemins_cites(lignes, seulement=p0_actifs))
    deposes = {p.chemin for p in pieces}
    motifs = {e.chemin or e.brut: e.motif for e in ecartes}

    rapport = Rapport(pieces=pieces, non_embarques=list(ecartes))
    deja = {e.brut for e in ecartes}
    for item in lignes:
        # Le detail est ce que la page rend en entier. Le drapeau voyage AVEC la
        # ligne pour que la page n'ait pas a redeviner la regle.
        item["detail"] = item["id"] in p0_actifs
        # Les references sont extraites du texte ENTIER, avant toute coupure:
        # sinon une piece citee au-dela du palier disparaitrait de l'ecran sans
        # que rien ne le signale.
        citees, vues = [], set()
        for champ in CHAMPS_A_REFERENCES:
            for brut in references_de(item.get(champ, "")):
                ref = classer_reference(brut, deposes, motifs)
                if item["detail"]:
                    rapport.affichees.append(ref)
                if brut not in vues:
                    vues.add(brut)
                    citees.append({"brut": ref.brut, "classe": ref.classe,
                                   "motif": ref.motif, "chemin": ref.chemin})
                if ref.classe == "distante":
                    rapport.distantes.append(ref)
                elif ref.classe == "citee" and ref.brut not in deja:
                    deja.add(ref.brut)
                    rapport.non_embarques.append(ref)
        if citees and item["detail"]:
            item["refs_pieces"] = citees

    horodate = (maintenant or datetime.now(timezone.utc).astimezone()).isoformat(timespec="seconds")
    registre = {
        "source": "docs/roadmap_backlog_central.md",
        "branche": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "commit": _git("rev-parse", "--short", "HEAD"),
        "etat_fichier": etat_du_gouvernail(),
        "commit_date": _git("log", "-1", "--format=%cI"),
        "mesure_le": horodate,
        "methode": "tools/gouvernail_depot.py, onze colonnes lues par position",
        "n": len(lignes),
        "lignes": lignes,
    }
    registre = ajuster_au_magasin(registre)
    depot_pieces = {
        "mesure_le": horodate,
        "lignes": [
            {
                "chemin": p.chemin,
                "titre": Path(p.chemin).name,
                "sous_titre": (
                    "%d caracteres, %s" % (
                        p.car_total,
                        "tronque a %d pour tenir dans le magasin" % CAR_MAX_PIECE
                        if p.tronque else "depose en entier",
                    )
                ),
                "tronque": p.tronque,
                "car_total": p.car_total,
                "depose_le": horodate,
                "texte": p.texte,
            }
            for p in pieces
        ],
        "non_embarques": [
            {"chemin": r.chemin or r.brut, "motif": r.motif} for r in ecartes
        ],
    }
    return registre, borner_les_pieces(depot_pieces), rapport


def _mesure(rapport: Rapport, registre: dict) -> str:
    affichees = rapport.affichees
    par_classe: dict[str, int] = {}
    for ref in affichees:
        par_classe[ref.classe] = par_classe.get(ref.classe, 0) + 1
    lignes = [
        "registre : %d items, commit %s%s"
        % (registre["n"], registre["commit"] or "?",
           "" if registre.get("etat_fichier") == ETAT_COMMITE
           else " - ATTENTION, le fichier lu n'est PAS celui de ce commit (%s)"
           % registre.get("etat_fichier", ETAT_INCONNU)),
        "  document : %d octets sur %d, cellules coupees a %d caracteres (%d lignes coupees)"
        % (octets(registre), registre["budget_octets"], registre["cap_cellule"],
           sum(1 for o in registre["lignes"] if o.get("coupe"))),
        "pieces embarquees : %d (%d caracteres deposes)"
        % (len(rapport.pieces), sum(len(p.texte) for p in rapport.pieces)),
        "",
        "references des lignes AFFICHEES par la page (P0 encore ACTIF) : %d" % len(affichees),
        "  ouvrables sur place (texte embarque) : %d" % par_classe.get("embarquee", 0),
        "  ouvrables par le navigateur (http)   : %d" % par_classe.get("distante", 0),
        "  citees en clair avec leur motif      : %d" % par_classe.get("citee", 0),
        "  LIENS MORTS                          : %d" % len(rapport.mortes()),
        "",
        "residu, motif par motif (tout le registre):",
    ]
    motifs: dict[str, int] = {}
    for ref in rapport.non_embarques:
        cle = ref.motif.split(":")[0].split("(")[0].strip()
        motifs[cle] = motifs.get(cle, 0) + 1
    for cle, n in sorted(motifs.items(), key=lambda kv: -kv[1]):
        lignes.append("  %3d  %s" % (n, cle))
    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--mesure", action="store_true", help="imprime le comptage et le residu")
    parseur.add_argument("--ecrire", metavar="DOSSIER", help="ecrit registre.json et pieces.json")
    args = parseur.parse_args(argv)

    registre, pieces, rapport = construire()
    if args.ecrire:
        sortie = Path(args.ecrire)
        sortie.mkdir(parents=True, exist_ok=True)
        (sortie / "registre.json").write_text(
            json.dumps(registre, ensure_ascii=False), encoding="utf-8")
        (sortie / "pieces.json").write_text(
            json.dumps(pieces, ensure_ascii=False), encoding="utf-8")
        print("ecrit: %s" % sortie)
    if args.mesure or not args.ecrire:
        print(_mesure(rapport, registre))
    return 0


if __name__ == "__main__":
    sys.exit(main())
