"""Lecture des sources texte: quel encodage, et surtout lequel a servi.

Un fichier depose dans une copropriete n'annonce pas son encodage, et il n'est
presque jamais ecrit par l'outil ni sur la plateforme qui le relira. C'est un
axe permanent, pas un accident: tant qu'il y aura des tableurs, des exports de
syndic et des postes Windows, il arrivera des octets qui ne sont pas de l'UTF-8.

La chaine repond a cet axe par deux regles, et la seconde compte autant que la
premiere:

- **la lecture est declaree, jamais devinee.** L'ordre des encodages essayes est
  ecrit ici, en clair, et il commence par celui qui est attendu;
- **une lecture de repli est un fait, pas un rattrapage.** L'ancienne chaine
  retombait sur un jeu latin qui, par construction, ne peut pas echouer: elle
  rendait donc toujours un texte, parfois faux, et ne laissait aucune trace. Un
  caractere rendu de travers ne se voit qu'a la lecture, des semaines plus tard,
  et a ce moment plus rien ne dit d'ou il vient. Le fait de provenance suit
  desormais le document.
"""

from __future__ import annotations

from pathlib import Path


# `utf-8-sig` est en tete pour deux raisons distinctes: c'est l'encodage attendu,
# et il retire la marque d'ordre d'octets qu'un tableur pose en tete de fichier.
# Lue en `utf-8` simple, cette marque survit dans le texte extrait sous la forme
# d'un caractere invisible: le premier mot du document cesse alors de commencer
# par sa premiere lettre, et toute recherche ancree en debut de texte le manque
# sans rien signaler. Mesure du 2026-09-04 sur cabinet reel: 21 artefacts sur
# 2 209 portaient cette marque residuelle.
SOURCE_ENCODINGS_STRICTS = ("utf-8-sig", "cp1252")

# Dernier recours seulement. Il accepte n'importe quelle suite d'octets, donc il
# ne peut pas alerter: c'est exactement pour cela qu'il doit etre nomme dans la
# fiche du document plutot qu'applique en silence.
SOURCE_ENCODING_DERNIER_RECOURS = "latin-1"

# Ecrit en echappement, pas en clair: un caractere invisible dans un fichier
# source est exactement le defaut que ce module sert a rendre visible ailleurs.
CARACTERE_DE_REMPLACEMENT = "\ufffd"


def decode_source(path: Path) -> tuple[str, str]:
    """Rend le texte de la source, et la note qui dit comment il a ete obtenu.

    La note est vide quand la source etait bien de l'UTF-8. Sinon elle nomme
    l'encodage effectivement employe, pour que le doute voyage avec le document
    au lieu de disparaitre a l'extraction.
    """
    raw = path.read_bytes()
    for encoding in SOURCE_ENCODINGS_STRICTS:
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if encoding == SOURCE_ENCODINGS_STRICTS[0]:
            return text, ""
        return text, (
            f"Source non decodable en UTF-8, relue en {encoding}. "
            "Verifier les caracteres accentues avant toute citation."
        )

    text = raw.decode(SOURCE_ENCODING_DERNIER_RECOURS, errors="replace")
    remplaces = text.count(CARACTERE_DE_REMPLACEMENT)
    return text, (
        "Encodage de la source non identifie, lecture de dernier recours en "
        f"{SOURCE_ENCODING_DERNIER_RECOURS} ({remplaces} caractere(s) remplace(s)). "
        "Le texte extrait peut differer de la source."
    )
