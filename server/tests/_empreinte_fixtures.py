# -*- coding: utf-8 -*-
"""Voir la reference versionnee, et en calculer l'empreinte.

Ce module ne juge rien. Il repond a trois questions, et il les repond en
demandant a la seule autorite qui les connaisse:

1. **Quels fichiers composent la reference ?** Git, parce que la reference est
   ce qui est VERSIONNE. Un parcours de dossiers repondrait faux dans les deux
   sens: il compterait les produits d'execution ignores - une instance
   d'exemple sur laquelle on a lance la chaine porte des sorties, des journaux
   et un coffre local que `.gitignore` ecarte - et il ne saurait pas dire ce qui
   a DISPARU. Une liste ecrite a la main repondrait faux d'une autre facon: elle
   ignorerait le fichier ajoute apres qu'on l'a ecrite.
2. **Que vaut chaque fichier ?** Ses octets, hashes en SHA-256, avec leur
   nombre. La taille est redondante avec le hash et c'est voulu: elle rend le
   message d'echec lisible pour un humain, qui voit tout de suite si un fichier
   a grossi de 12 octets ou a ete remplace.
3. **Qu'est-ce qui s'ajoute a cote ?** Les fichiers non suivis et non ignores.
   C'est le piege reel: un `git add -A` fait entrer d'un geste tout ce qui
   traine, et la reference grandit sans que personne l'ait decide.

**Pourquoi les octets bruts et non un contenu normalise.** Le depot impose
`* text=auto eol=lf` dans `.gitattributes`: l'arbre de travail porte des fins de
ligne LF sur toutes les plateformes. Verifie ici - les neuf empreintes que
l'instance declare dans son propre manifeste correspondent aux octets du disque,
sur Windows. Si une copie de travail produisait un jour des CRLF, cette garde
rougirait sur les 47 fichiers d'un coup. C'est un faux positif bruyant et
diagnosticable en une ligne, et c'est le bon cote de l'erreur: le defaut que
cette garde existe pour attraper est precisement celui qui ne fait pas de bruit.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

RACINE_DEPOT = Path(__file__).resolve().parents[2]

#: La reference versionnee est le dossier des exemples publiables. Ce n'est pas
#: un choix de nom: c'est le seul corpus que la doctrine autorise la CI a lire,
#: donc le seul contre lequel des tests peuvent mesurer sans instance privee.
DOSSIER_REFERENCE = "examples"

#: Le fichier qui fait d'un dossier une instance. Il n'est pas choisi ici par
#: convenance: c'est le fichier que `load_instance` exige, donc la seule marque
#: qui distingue une instance d'un dossier de pieces.
NOM_FICHIER_INSTANCE = "instance.yml"

#: L'empreinte enregistree vit A COTE des tests, jamais dans le dossier qu'elle
#: garde. Une citation ne peut pas etre son propre temoin: une empreinte rangee
#: sous `examples/` devrait s'exclure elle-meme du calcul, et cette exception
#: serait exactement la porte par laquelle une mutation passerait.
CHEMIN_EMPREINTE = Path(__file__).resolve().parent / "empreinte_fixtures_versionnees.json"

SEPARATEUR_NUL = chr(0)

ABSENT = "absent"


class GitIndisponible(RuntimeError):
    """Git n'a pas repondu, donc la portee de la garde est inconnue.

    Cette exception existe pour que l'appelant ECHOUE au lieu de sauter. Une
    garde qui ne peut pas s'executer ne rend pas un succes.
    """


def _git(*arguments: str) -> list[str]:
    """Appel ferme: commande en liste, `shell` absent, sortie separee par NUL.

    Aucune donnee d'utilisateur n'entre dans la ligne de commande - les
    arguments sont des litteraux de ce module.
    """
    try:
        sortie = subprocess.run(
            ["git", *arguments],
            cwd=RACINE_DEPOT,
            capture_output=True,
            check=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as erreur:
        raise GitIndisponible(
            "git n'a pas repondu a `%s` (%s): la portee de la garde est inconnue"
            % (" ".join(arguments), erreur)
        ) from erreur
    return [nom for nom in sortie.stdout.decode("utf-8").split(SEPARATEUR_NUL) if nom]


def fichiers_suivis() -> list[str]:
    """Les chemins, relatifs au depot, que git SUIT sous la reference."""
    return sorted(_git("ls-files", "-z", DOSSIER_REFERENCE))


def instances_versionnees() -> list[Path]:
    """Les racines d'instance que git SUIT sous la reference.

    **Cette fonction existe parce qu'un nom ecrit en dur ne tenait pas.** La
    premiere version du controle d'identite visait `examples/synthetic_copro`,
    ecrit dans une constante, avec le commentaire qu'il ne s'agissait pas d'un
    choix de nom. C'en etait un: mesure du 2026-09-09, une seconde instance
    d'exemple posee sous `examples/` - manifeste declarant un sha256 faux, une
    taille fausse et un identifiant derive qui ne derivait de rien - laissait
    la garde rendre `Ran 8 tests OK` sur 50 fichiers.

    La portee se demande donc a git, comme celle de l'empreinte. Une instance
    ajoutee demain entre dans le controle sans que personne edite ce fichier;
    une instance retiree en sort de la meme facon.
    """
    return sorted(
        {
            (RACINE_DEPOT / chemin).parent
            for chemin in fichiers_suivis()
            if Path(chemin).name == NOM_FICHIER_INSTANCE
        }
    )


def fichiers_non_suivis_non_ignores() -> list[str]:
    """Ce qui s'est pose a cote de la reference sans etre ignore.

    C'est ce qu'un `git add -A` ferait entrer dans le depot au prochain geste.
    """
    return sorted(
        _git("ls-files", "-z", "--others", "--exclude-standard", DOSSIER_REFERENCE)
    )


def empreinte_du_fichier(chemin: Path) -> dict[str, object]:
    """SHA-256 et nombre d'octets, ou le marqueur d'absence."""
    try:
        octets = chemin.read_bytes()
    except OSError:
        return {ABSENT: True}
    return {"sha256": hashlib.sha256(octets).hexdigest(), "octets": len(octets)}


def empreinte_constatee() -> dict[str, dict[str, object]]:
    """L'empreinte de la reference telle qu'elle est sur le disque MAINTENANT."""
    return {
        chemin: empreinte_du_fichier(RACINE_DEPOT / chemin)
        for chemin in fichiers_suivis()
    }


def empreinte_enregistree() -> dict[str, dict[str, object]]:
    """L'empreinte telle qu'elle a ete arretee la derniere fois, deliberement."""
    donnees = json.loads(CHEMIN_EMPREINTE.read_text(encoding="utf-8"))
    fichiers = donnees.get("fichiers")
    if not isinstance(fichiers, dict):
        raise ValueError(
            "%s ne porte pas de section `fichiers`: l'empreinte est illisible, "
            "et une empreinte illisible ne prouve rien"
            % CHEMIN_EMPREINTE.name
        )
    return fichiers


def divergences(
    enregistree: dict[str, dict[str, object]],
    constatee: dict[str, dict[str, object]],
) -> dict[str, list[str]]:
    """Trois familles d'ecart, chacune NOMMANT ses fichiers.

    Le decoupage n'est pas cosmetique: un contenu qui bouge, un fichier qui
    entre et un fichier qui sort sont trois accidents differents, et un message
    qui les melange oblige le lecteur a rouvrir le diff pour savoir lequel il a.
    """
    contenu: list[str] = []
    entres: list[str] = []
    sortis: list[str] = []
    for chemin in sorted(set(enregistree) | set(constatee)):
        avant = enregistree.get(chemin)
        apres = constatee.get(chemin)
        if avant is None:
            entres.append(chemin)
            continue
        if apres is None:
            sortis.append(chemin)
            continue
        if apres.get(ABSENT):
            sortis.append("%s (suivi par git, absent du disque)" % chemin)
            continue
        if avant.get("sha256") == apres.get("sha256") and avant.get("octets") == apres.get("octets"):
            continue
        contenu.append(
            "%s: empreinte %s (%s octets) -> %s (%s octets)"
            % (
                chemin,
                str(avant.get("sha256", "?"))[:12],
                avant.get("octets", "?"),
                str(apres.get("sha256", "?"))[:12],
                apres.get("octets", "?"),
            )
        )
    return {"contenu": contenu, "entres": entres, "sortis": sortis}


def ecrire_empreinte() -> int:
    """Arreter l'empreinte courante comme nouvelle reference. Acte DELIBERE.

    Rien n'appelle cette fonction pendant les tests. Elle s'invoque a la main,
    et son effet se lit dans le diff: c'est la seule facon de changer la
    reference sans que la garde le signale, et il faut l'avoir voulue.
    """
    fichiers = empreinte_constatee()
    charge = {
        "quoi": (
            "Empreinte des fichiers versionnes de %s. Toute divergence est "
            "signalee par server/tests/test_fixtures_versionnees_immuables.py."
        )
        % DOSSIER_REFERENCE,
        "regenerer": "python server/tests/_empreinte_fixtures.py --ecrire",
        "fichiers": fichiers,
    }
    # `newline` explicite: sans lui, Python traduit chaque saut de ligne en
    # CRLF sous Windows, git renormalise en LF au commit suivant, et le fichier
    # reste eternellement `modifie` dans l'arbre de travail. Une garde qui salit
    # `git status` a chaque regeneration entraine exactement le `git add -A`
    # qu'elle existe pour rendre visible.
    CHEMIN_EMPREINTE.write_text(
        json.dumps(charge, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return len(fichiers)


if __name__ == "__main__":  # pragma: no cover
    import sys

    if "--ecrire" not in sys.argv:
        raise SystemExit(
            "usage: python server/tests/_empreinte_fixtures.py --ecrire\n"
            "Reecrit l'empreinte de reference. A ne faire que si le changement "
            "des fixtures est voulu."
        )
    print("empreinte arretee sur %d fichiers" % ecrire_empreinte())
