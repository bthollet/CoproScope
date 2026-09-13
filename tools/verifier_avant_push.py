# -*- coding: utf-8 -*-
"""Ce que `git push` enverrait porte-t-il une donnee personnelle ?

**Le defaut que cet outil existe pour reparer, et il est nomme par le
gouvernail lui-meme** (`RM-2026-0137`): la garde de partage du produit gouverne
le module de PUBLICATION, et **rien ne relie `git push` a la doctrine**. Le
2026-09-09, une adresse postale reelle a traverse le pseudonymat et s'est
retrouvee dans un fichier suivi (`RM-2026-0170`); une autre est publique depuis
le 2026-06-01. Aucun controle ne se declenchait au moment ou la donnee part.

**L'axe, et il decide de toute la conception.** Ce qui varie: quelle donnee,
quel fichier, quelle branche, quel oubli. Le controle ne porte donc ni sur un
diff, ni sur une liste de dossiers sensibles, ni sur une convention de
nommage: un fichier nouveau, deplace ou renomme doit y entrer tout seul.

**L'INVARIANT ANNONCE ICI ETAIT FAUX, et il l'est reste trois jours.** Ce
paragraphe affirmait que *ce que `git push` envoie est exactement ce que Git
suit*, et en tirait un controle porte sur `git ls-files`. Deux contre-exemples
mesures le 2026-09-12:

1. `git push origin main` depuis une autre branche. `git ls-files` rend l'arbre
   COURANT; la reference poussee n'est jamais lue. Mesure: `main` portait 41
   constats, la branche courante zero, et le controle repondait *aucun
   constat*.
2. **Un nom efface dans un commit reste entierement lisible dans le precedent,
   et un push publie les deux.** L'arbre peut donc etre propre pendant que
   l'historique ne l'est pas: 45 chemins de blobs portaient le terme parmi les
   objets que le push de la branche aurait envoyes, pour *aucun constat* sur
   l'arbre.

C'est la forme la plus couteuse de la faute que ce depot nomme: l'axe etait
bien nomme, et l'invariant pose le long de l'axe ne tenait pas. Le garde-fou
existait, il etait actif, il s'executait - et il regardait ailleurs.

**L'invariant qui tient:** un push envoie les objets atteignables depuis les
references poussees et absents du distant. `--pousse` les enumere par
`git rev-list --objects <cibles> --not --remotes=<distant>`, controle le
contenu des blobs ET les chemins eux-memes - `origin/main` porte le nom reel
dans deux NOMS de fichiers, donc lisible sans ouvrir quoi que ce soit.
Le controle de l'arbre suivi reste disponible: il repond a l'autre question,
*qu'est-ce que je suis en train de commiter*.

**Les termes interdits ne sont pas dans le depot, et ne peuvent pas y etre.**
Ecrire le nom reel d'une copropriete dans le fichier qui interdit de l'ecrire
serait la premiere fuite. Ils vivent donc dans un fichier LOCAL, hors depot,
dont le chemin se donne par `COPROSCOPE_NOMS_INTERDITS` ou se cherche a cote du
depot. **Si ce fichier manque, l'outil ECHOUE au lieu de certifier**: un
controle qui se tait faute de matiere est pire qu'aucun controle, parce qu'il
laisse croire qu'il a regarde.

**Cet outil n'affiche jamais le terme cherche.** Il rend un chemin, un numero
de ligne et un compte. Un rapport de fuite qui recopie la fuite est une fuite.

Usage:

    python tools/verifier_avant_push.py
    python tools/verifier_avant_push.py --ref origin/main

Code de sortie: 0 si rien, 1 si quelque chose a ete trouve, 2 si le controle
n'a PAS pu etre fait - trois etats distincts, parce que *rien trouve* et *pas
regarde* ne doivent jamais se confondre.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

DEPOT = Path(__file__).resolve().parent.parent

#: Ou chercher les termes interdits, dans l'ordre. Aucun n'est dans le depot.
VARIABLE = "COPROSCOPE_NOMS_INTERDITS"
DEFAUTS = ("../noms_interdits.txt", "../dev/noms_interdits.txt")

#: Code postal puis nom de commune. Meme axe que
#: `server/tests/test_aucune_adresse_reelle.py`, ou il est explique en detail:
#: c'est la juxtaposition qui fait une adresse, et un nom propre porte une
#: majuscule et plus de trois lettres.
ADRESSE = re.compile(r"\b\d{5}\b[ \t]+([A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’-]{3,})")

#: Les communes conventionnelles pour une adresse fabriquee.
COMMUNES_FICTIVES = {"ville", "commune", "exemple", "exemples"}

#: Un echappement est une fin de LIGNE dans le document qu'une fixture porte.
ECHAPPEMENTS = re.compile(r"\\[nrt]")

#: Les fichiers dont la RAISON D'ETRE est de porter le motif interdit: le garde
#: de test qui l'explique, et le garde-fou d'instance ou le nom EST la regle
#: (`RM-2026-0152`). Les exclure n'affaiblit rien - ils ne cachent pas une
#: donnee, ils la decrivent - mais l'oubli les ferait crier a chaque passage,
#: et un garde qui crie toujours finit ignore.
#: `server/tests/test_aucune_adresse_reelle.py` tient la meme liste sous le nom
#: `IGNORES`, et un test verifie que les deux gardes restent d'accord.
DECLARENT_LE_MOTIF = {
    "server/tests/test_aucune_adresse_reelle.py",
    "server/tests/test_verifier_avant_push.py",
    "tools/verifier_avant_push.py",
}

#: Un fichier binaire n'est pas lu; il est compte a part et annonce.
SUFFIXES_BINAIRES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".ico",
                     ".zip", ".xlsx", ".docx", ".sqlite3", ".db", ".lock"}


def fichier_des_termes() -> Path | None:
    """Le fichier local des termes interdits, ou None s'il est introuvable."""
    donne = os.environ.get(VARIABLE)
    if donne:
        chemin = Path(donne)
        return chemin if chemin.is_file() else None
    for relatif in DEFAUTS:
        chemin = (DEPOT / relatif).resolve()
        if chemin.is_file():
            return chemin
    return None


def termes_interdits(chemin: Path) -> list[str]:
    """Un terme par ligne; `#` commente; la casse est ignoree a la recherche."""
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lignes if l.strip() and not l.startswith("#")]


def fichiers_suivis(ref: str | None) -> list[str]:
    """Ce que Git suit - donc exactement ce qu'un push enverrait."""
    if ref:
        commande = ["git", "ls-tree", "-r", "--name-only", ref]
    else:
        commande = ["git", "ls-files"]
    sortie = subprocess.run(commande, cwd=DEPOT, capture_output=True,
                            text=True, encoding="utf-8", check=True)
    return [l for l in sortie.stdout.splitlines() if l.strip()]


def _textes_de_la_reference(ref: str, relatifs: list[str]):
    """Le contenu de chaque fichier d'une reference, en UN seul sous-processus.

    **Une premiere version appelait `git show` par fichier.** Sur 1 600 fichiers
    et sous Windows, ou lancer un processus est cher, le controle ne finissait
    pas en deux minutes - donc personne ne l'aurait branche sur un `git push`.
    Un garde trop lent pour etre lance ne garde rien: le cout d'execution fait
    partie de sa conception, pas de son reglage.

    `git cat-file --batch` lit une liste d'objets sur son entree et rend leurs
    contenus a la suite, precedes d'un en-tete `<empreinte> <type> <taille>`.
    """
    lisibles = [r for r in relatifs if Path(r).suffix.lower() not in SUFFIXES_BINAIRES]
    if not lisibles:
        return
    demande = "".join("%s:%s\n" % (ref, r) for r in lisibles)
    p = subprocess.run(["git", "cat-file", "--batch"], cwd=DEPOT, check=True,
                       input=demande.encode("utf-8"), stdout=subprocess.PIPE)
    flux, position = p.stdout, 0
    for rel in lisibles:
        fin_entete = flux.find(b"\n", position)
        if fin_entete < 0:
            return
        entete = flux[position:fin_entete].split()
        if len(entete) < 3:            # `<objet> missing`
            position = fin_entete + 1
            continue
        taille = int(entete[2])
        brut = flux[fin_entete + 1:fin_entete + 1 + taille]
        position = fin_entete + 1 + taille + 1   # le saut de ligne final
        try:
            yield rel, brut.decode("utf-8")
        except UnicodeDecodeError:
            continue


def _textes_de_l_arbre(relatifs: list[str]):
    """Le contenu de chaque fichier suivi, lu sur le disque."""
    for rel in relatifs:
        if Path(rel).suffix.lower() in SUFFIXES_BINAIRES:
            continue
        try:
            yield rel, (DEPOT / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue


def _masque(chemin: str, termes_bas: list[str]) -> str:
    """Le chemin, avec tout terme interdit remplace par son rang.

    **Necessaire, et decouvert en livrant:** quand le terme est dans le NOM du
    fichier, nommer le fichier recopie la fuite - ce que l'en-tete de cet outil
    interdit en toutes lettres. Le reste du chemin suffit a agir: le dossier,
    la date, l'objet du document restent lisibles.
    """
    sortie = chemin
    for i, terme in enumerate(termes_bas):
        if not terme:
            continue
        motif = re.compile(re.escape(terme), re.I)
        sortie = motif.sub("<TERME-%d>" % (i + 1), sortie)
    return sortie


def objets_pousses(distant: str, cibles: list[str]) -> list[tuple[str, str]]:
    """Les objets NOMMES que ce push enverrait, et rien de plus.

    **C'est ici que cet outil corrige son propre invariant, et il etait faux.**
    L'en-tete de ce fichier affirmait: *ce que `git push` envoie est exactement
    ce que Git suit*, d'ou un controle porte sur `git ls-files`. L'axe etait
    bien nomme - quelle donnee, quel fichier, quelle branche, quel oubli - mais
    **l'invariant choisi le long de cet axe ne tient pas**, et il a fallu le
    mesurer pour s'en apercevoir.

    Deux contre-exemples mesures le 2026-09-12, tous deux atteignables:

    1. `git push origin main` depuis une autre branche. `git ls-files` rend
       l'arbre COURANT; la reference poussee n'est jamais regardee. Constate:
       `main` portait 41 constats, la branche courante zero, et le controle
       repondait *aucun constat*.
    2. **Un nom efface dans un commit reste entierement lisible dans le
       precedent, et un push publie les deux.** L'arbre peut donc etre propre
       pendant que l'historique ne l'est pas - c'etait le cas ici: 45 chemins
       de blobs portaient le terme parmi les objets que ce push aurait envoyes,
       pour *aucun constat* sur l'arbre.

    **L'invariant qui tient:** un push envoie les objets atteignables depuis
    les references poussees et absents du distant. C'est exactement ce que
    `git rev-list --objects <cibles> --not --remotes=<distant>` enumere, et
    c'est ce que cette fonction rend.

    Les empreintes tout a zero sont ecartees: elles designent une SUPPRESSION
    de reference, qui n'envoie aucun objet.
    """
    vivants = [s for s in cibles if s and set(s) != {"0"}]
    if not vivants:
        return []
    commande = (["git", "rev-list", "--objects"] + vivants
                + ["--not", "--remotes=" + distant])
    p = subprocess.run(commande, cwd=DEPOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError((p.stderr or "").strip()[:300]
                           or "git rev-list a echoue sans message")
    objets = []
    for ligne in p.stdout.splitlines():
        empreinte, _, chemin = ligne.partition(" ")
        if chemin:                 # un commit n'a pas de chemin: on l'ignore
            objets.append((empreinte, chemin))
    return objets


def _textes_des_objets(objets: list[tuple[str, str]]):
    """Le contenu des BLOBS d'une liste d'objets, en un seul sous-processus.

    Le type est lu dans l'en-tete rendu par `git cat-file --batch`: les arbres
    sont ecartes ici, parce que leur contenu brut est une suite d'entrees
    binaires et qu'un compte d'occurrences n'y voudrait rien dire. Le nom d'un
    dossier se controle par son CHEMIN, que `controler` examine a part.
    """
    lisibles = [(s, c) for s, c in objets
                if Path(c).suffix.lower() not in SUFFIXES_BINAIRES]
    if not lisibles:
        return
    demande = b"".join(s.encode("utf-8") + b"\n" for s, _ in lisibles)
    p = subprocess.run(["git", "cat-file", "--batch"], cwd=DEPOT, check=True,
                       input=demande, stdout=subprocess.PIPE)
    flux, position = p.stdout, 0
    for empreinte, chemin in lisibles:
        fin_entete = flux.find(b"\n", position)
        if fin_entete < 0:
            return
        entete = flux[position:fin_entete].split()
        if len(entete) < 3:                  # `<objet> missing`
            position = fin_entete + 1
            continue
        taille = int(entete[2])
        brut = flux[fin_entete + 1:fin_entete + 1 + taille]
        position = fin_entete + 1 + taille + 1
        if entete[1] != b"blob":
            continue
        try:
            yield chemin, empreinte, brut.decode("utf-8")
        except UnicodeDecodeError:
            continue


def controler_le_push(distant: str, cibles: list[str],
                      termes: list[str]) -> tuple[list[str], int]:
    """Les constats sur CE QUE LE PUSH ENVOIE, et le nombre de blobs lus.

    Un chemin revient autant de fois qu'il a de versions publiees. Les constats
    sont donc regroupes par chemin, avec le nombre de VERSIONS concernees:
    nommer trente mille occurrences reparties sur un fichier ne dit rien de
    plus que *ce fichier, dans trente versions*, et noierait le reste.

    **Le chemin lui-meme est controle a part**, et ce n'est pas une precaution
    theorique: `origin/main` porte le nom reel dans deux NOMS de fichiers, donc
    lisible dans l'arborescence publique sans ouvrir quoi que ce soit.
    """
    bas = [t.lower() for t in termes]
    objets = objets_pousses(distant, cibles)

    par_chemin: dict[tuple[str, int], set[str]] = {}
    noms: dict[int, set[str]] = {}
    for _, chemin in objets:
        minuscule = chemin.lower()
        for i, terme in enumerate(bas):
            if terme in minuscule:
                noms.setdefault(i, set()).add(_masque(chemin, bas))

    lus = 0
    for chemin, empreinte, texte in _textes_des_objets(objets):
        lus += 1
        minuscule = texte.lower()
        for i, terme in enumerate(bas):
            if terme in minuscule:
                par_chemin.setdefault((chemin, i), set()).add(empreinte)

    constats = []
    for i, chemins in sorted(noms.items()):
        for chemin in sorted(chemins):
            constats.append("%s - terme interdit n %d dans le NOM DU FICHIER"
                            % (chemin, i + 1))
    for (chemin, i), versions in sorted(par_chemin.items(),
                                        key=lambda kv: (-len(kv[1]), kv[0])):
        constats.append("%s - terme interdit n %d, dans %d version(s) que ce "
                        "push publierait"
                        % (_masque(chemin, bas), i + 1, len(versions)))
    return constats, lus


def lignes_de_push(flux) -> list[str]:
    """Les empreintes locales annoncees par `git push` sur l'entree standard.

    Format d'une ligne: `<ref locale> <sha local> <ref distante> <sha distant>`.
    On ne retient que le sha local: c'est ce qui part.
    """
    cibles = []
    for ligne in flux:
        morceaux = ligne.split()
        if len(morceaux) >= 2:
            cibles.append(morceaux[1])
    return cibles


def controler(ref: str | None, termes: list[str]) -> tuple[list[str], int, int]:
    """Les constats, le nombre de fichiers lus, le nombre non lus."""
    bas = [t.lower() for t in termes]
    fictives = {c.rstrip("s") for c in COMMUNES_FICTIVES}
    constats, lus = [], 0
    relatifs = fichiers_suivis(ref)

    # **Le NOM d'un fichier suivi est publie comme son contenu**, et ce mode ne
    # lisait que les contenus. `origin/main` porte le nom reel dans deux noms de
    # fichiers, lisibles dans l'arborescence publique sans ouvrir quoi que ce
    # soit; un binaire, jamais lu ici, suffirait a porter la fuite dans son nom.
    for rel in relatifs:
        minuscule = rel.lower()
        for i, terme in enumerate(bas):
            if terme in minuscule:
                constats.append("%s - terme interdit n %d dans le NOM DU FICHIER"
                                % (_masque(rel, bas), i + 1))

    source = _textes_de_la_reference(ref, relatifs) if ref else _textes_de_l_arbre(relatifs)
    for rel, texte in source:
        lus += 1
        minuscule = texte.lower()
        for i, terme in enumerate(bas):
            n = minuscule.count(terme)
            if n:
                constats.append("%s - terme interdit n %d, %d occurrence(s)"
                                % (_masque(rel, bas), i + 1, n))
        if rel in DECLARENT_LE_MOTIF:
            continue
        for numero, ligne in enumerate(texte.splitlines(), 1):
            for segment in ECHAPPEMENTS.split(ligne):
                for m in ADRESSE.finditer(segment):
                    if m.group(1).lower().rstrip("s") in fictives:
                        continue
                    constats.append("%s:%d - adresse postale (commune non fictive)" % (rel, numero))
    return constats, lus, len(relatifs) - lus


def main(argv: list[str]) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--ref", help="controler une reference Git plutot que l'arbre courant")
    parseur.add_argument("--pousse", metavar="DISTANT",
                         help="controler CE QUE LE PUSH ENVOIE: les lignes de "
                              "`git push` sont lues sur l'entree standard")
    args = parseur.parse_args(argv)

    chemin = fichier_des_termes()
    if chemin is None:
        print("CONTROLE IMPOSSIBLE: aucun fichier de termes interdits.", file=sys.stderr)
        print("  Poser %s, ou creer l'un de: %s"
              % (VARIABLE, ", ".join(DEFAUTS)), file=sys.stderr)
        print("  Ce fichier ne doit JAMAIS entrer dans le depot.", file=sys.stderr)
        return 2

    termes = termes_interdits(chemin)
    if not termes:
        print("CONTROLE IMPOSSIBLE: le fichier de termes est vide (%s)." % chemin, file=sys.stderr)
        return 2

    if args.pousse:
        cibles = lignes_de_push(sys.stdin)
        if not cibles:
            print("CONTROLE IMPOSSIBLE: aucune reference annoncee sur l'entree "
                  "standard.", file=sys.stderr)
            print("  `--pousse` attend les lignes que `git push` donne a son "
                  "crochet. Rien n'a ete lu, donc RIEN N'A ETE CONTROLE.",
                  file=sys.stderr)
            return 2
        try:
            constats, lus = controler_le_push(args.pousse, cibles, termes)
        except RuntimeError as souci:
            print("CONTROLE IMPOSSIBLE: %s" % souci, file=sys.stderr)
            return 2
        print("controle de ce que le push enverrait vers %s: %d blob(s) lu(s), "
              "%d reference(s) annoncee(s), %d terme(s) interdit(s) charge(s)"
              % (args.pousse, lus, len(cibles), len(termes)))
    else:
        constats, lus, sautes = controler(args.ref, termes)
        cible = args.ref or "l'arbre suivi"
        print("controle de %s: %d fichiers lus, %d non lus (binaires), %d terme(s) interdit(s) charge(s)"
              % (cible, lus, sautes, len(termes)))
    if constats:
        print("\n%d CONSTAT(S) - ne pas pousser en l'etat:" % len(constats))
        for c in constats[:200]:
            print("  " + c)
        if len(constats) > 200:
            print("  ... et %d autres" % (len(constats) - 200))
        return 1
    print("aucun constat. Les termes eux-memes ne sont jamais affiches.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
