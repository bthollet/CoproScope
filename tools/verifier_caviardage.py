# -*- coding: utf-8 -*-
"""Une copie dite caviardee l'est-elle, et comment le saurait-on ?

Question de Brice du 2026-09-12: *« les documents caviardes, ca, ce n'est pas
bon du tout. Mais bon, je voudrais quand meme qu'on verifie que tu m'expliques
comment verifier. Si les versions textes, elles existent bien, et si elles sont
caviardees ? »*

**Trois questions, et elles ne se confondent pas.**

1. La version texte **existe**-t-elle sur le disque ?
2. Le fichier lu est-il **celui qui a ete enregistre** (empreinte) ?
3. **Est-il caviarde**, c'est-a-dire: les regles de detection trouvent-elles
   encore des identifiants dedans ?

Chacune se repond separement, parce qu'elles echouent separement. Un registre
peut annoncer une copie que personne n'a ecrite; une copie peut exister et
avoir ete remplacee depuis; une copie peut exister, avoir la bonne empreinte,
**et porter encore les identifiants en clair**.

**CE QUI COMPTE, ET C'EST LE POINT DE L'OUTIL: on ne croit pas le producteur.**
Le registre porte un `match_count` ecrit par le caviardeur lui-meme. Un nombre
qu'un producteur ecrit sur son propre travail ne prouve rien: il dit ce que le
producteur a CRU faire. L'outil rejoue donc **les regles sur la sortie**, et
c'est la seule des trois questions dont la reponse ne vienne pas du registre.

**LE PLAFOND DE CET OUTIL SE DECLARE, PARCE QU'IL EST LA VRAIE REPONSE A
« CE N'EST PAS BON DU TOUT ».** Les regles rejouees ici sont **les memes
regles** que celles du caviardage. Un identifiant qu'une regle ne sait pas voir
a l'entree, elle ne le voit pas davantage a la sortie. Donc:

    zero signal residuel NE VEUT PAS DIRE que la copie est propre.
    Cela veut dire: RIEN DE CE QUE LES REGLES SAVENT VOIR n'y reste.

C'est pour cela que l'outil compte a part les copies declarees `REDACTED`
**dont le `match_count` vaut zero**: une copie dont rien n'a ete retire est le
texte d'origine, sous un nom qui promet le contraire. Ce compte-la est le
symptome d'une couverture de regles insuffisante, et il n'est pas une erreur de
l'outil de caviardage: c'est la limite de ce qu'il sait reconnaitre.

**TROIS ETATS, ET L'ETAT 2 N'EST JAMAIS UN FEU VERT.** 0 rien a verifier (le
registre ne promet aucune copie), 1 verifie, 2 **le controle n'a pas pu etre
fait** - copie absente, illisible, empreinte manquante. Une copie qu'on n'a pas
pu ouvrir n'est pas une copie propre.

**AUCUNE VALEUR N'EST AFFICHEE.** L'outil rend des comptes, des categories
(`EMAIL`, `IBAN`, `PERSON_NAME`...) et des `doc_id`. Jamais un identifiant
trouve: afficher la donnee qu'on protege serait la fuite qu'on mesure.

Usage, depuis la racine du depot:

    python tools/verifier_caviardage.py --instance <racine de l'instance>
    python tools/verifier_caviardage.py --instance <racine> --detail
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
from dataclasses import dataclass
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[1]
if str(DEPOT / "server" / "src") not in sys.path:
    sys.path.insert(0, str(DEPOT / "server" / "src"))

from coproscope.core.common import load_instance  # noqa: E402
from coproscope.core.privacy import redaction_signals  # noqa: E402

#: Les trois etats. `IMPOSSIBLE` n'est pas un echec de l'outil: c'est un
#: resultat, et il se compte a part de `VERIFIE` pour ne jamais passer pour lui.
RIEN = "rien a verifier"
VERIFIE = "verifie"
IMPOSSIBLE = "controle impossible"


@dataclass
class Constat:
    doc_id: str
    etat: str
    motif: str
    #: Categories encore detectees dans la COPIE. Jamais les valeurs.
    residu: tuple[str, ...] = ()
    #: Ce que le producteur a declare avoir retire. Non verifiable en soi.
    declare: int = 0
    empreinte_concorde: bool | None = None


def _empreinte(chemin: Path) -> str:
    h = hashlib.sha256()
    with io.open(chemin, "rb") as flux:
        for bloc in iter(lambda: flux.read(65536), b""):
            h.update(bloc)
    return h.hexdigest()


def _lignes_du_registre(chemin: Path) -> list[dict[str, str]]:
    if not chemin.exists():
        return []
    with io.open(chemin, encoding="utf-8", newline="") as flux:
        return list(csv.DictReader(flux))


def examiner(ligne: dict[str, str], racine_copies: Path) -> Constat:
    """Une ligne du registre, confrontee au fichier qu'elle promet."""
    doc_id = (ligne.get("doc_id") or "?").strip()
    statut = (ligne.get("status") or "").strip()
    relatif = (ligne.get("redacted_path") or "").strip()
    try:
        declare = int((ligne.get("match_count") or "0").strip() or "0")
    except ValueError:
        declare = 0

    if not relatif:
        return Constat(doc_id, RIEN,
                       "le registre ne promet aucune copie (statut %s)" % (statut or "?"),
                       declare=declare)

    copie = racine_copies / relatif
    if not copie.exists():
        return Constat(doc_id, IMPOSSIBLE,
                       "le registre promet une copie que le disque ne porte pas",
                       declare=declare)

    attendue = (ligne.get("redacted_sha256") or "").strip()
    try:
        obtenue = _empreinte(copie)
    except OSError as erreur:
        return Constat(doc_id, IMPOSSIBLE,
                       "copie illisible (%s)" % erreur.__class__.__name__,
                       declare=declare)
    concorde = None if not attendue else (attendue == obtenue)

    try:
        texte = io.open(copie, encoding="utf-8", errors="replace").read()
    except OSError as erreur:
        return Constat(doc_id, IMPOSSIBLE,
                       "copie non decodable (%s)" % erreur.__class__.__name__,
                       declare=declare, empreinte_concorde=concorde)

    if not texte.strip():
        return Constat(doc_id, IMPOSSIBLE,
                       "copie vide: il n'y a rien a controler, donc rien de prouve",
                       declare=declare, empreinte_concorde=concorde)

    residu = tuple(sorted({signal.category for signal in redaction_signals(texte)}))
    return Constat(doc_id, VERIFIE, "", residu, declare, concorde)


def rapport(constats: list[Constat], detail: bool) -> str:
    lignes: list[str] = []
    par_etat: dict[str, int] = {}
    for c in constats:
        par_etat[c.etat] = par_etat.get(c.etat, 0) + 1

    avec_residu = [c for c in constats if c.etat == VERIFIE and c.residu]
    propres = [c for c in constats if c.etat == VERIFIE and not c.residu]
    rien_retire = [c for c in constats if c.etat == VERIFIE and c.declare == 0]
    empreinte_fausse = [c for c in constats if c.empreinte_concorde is False]
    sans_empreinte = [c for c in constats if c.etat == VERIFIE and c.empreinte_concorde is None]

    lignes.append("registre de biffage : %d lignes" % len(constats))
    for etat in (VERIFIE, IMPOSSIBLE, RIEN):
        lignes.append("  %-22s : %d" % (etat, par_etat.get(etat, 0)))
    lignes.append("")
    lignes.append("1. LA VERSION TEXTE EXISTE-T-ELLE ?")
    lignes.append("   copies promises et trouvees   : %d"
                  % sum(1 for c in constats if c.etat in (VERIFIE, )
                        or (c.etat == IMPOSSIBLE and "disque" not in c.motif)))
    lignes.append("   promises et INTROUVABLES      : %d"
                  % sum(1 for c in constats if c.etat == IMPOSSIBLE and "disque" in c.motif))
    lignes.append("")
    lignes.append("2. LE FICHIER LU EST-IL CELUI QUI A ETE ENREGISTRE ?")
    lignes.append("   empreinte concordante         : %d"
                  % sum(1 for c in constats if c.empreinte_concorde is True))
    lignes.append("   empreinte DIFFERENTE          : %d" % len(empreinte_fausse))
    lignes.append("   aucune empreinte au registre  : %d" % len(sans_empreinte))
    lignes.append("")
    lignes.append("3. EST-ELLE CAVIARDEE ? (regles rejouees sur la SORTIE)")
    lignes.append("   aucun signal residuel         : %d" % len(propres))
    lignes.append("   IDENTIFIANTS ENCORE PRESENTS  : %d" % len(avec_residu))
    if avec_residu:
        categories: dict[str, int] = {}
        for c in avec_residu:
            for cat in c.residu:
                categories[cat] = categories.get(cat, 0) + 1
        for cat, n in sorted(categories.items(), key=lambda kv: (-kv[1], kv[0])):
            lignes.append("      %-18s dans %d copies" % (cat, n))
    lignes.append("")
    lignes.append("CE QUE CE CHIFFRE NE DIT PAS, et c'est la vraie question:")
    lignes.append("   copies dont RIEN n'a ete retire (match_count = 0) : %d" % len(rien_retire))
    lignes.append("   Une copie dont rien n'a ete retire est le texte d'origine.")
    lignes.append("   Les regles rejouees ici sont LES MEMES que celles du")
    lignes.append("   caviardage: un identifiant qu'elles ne savent pas voir a")
    lignes.append("   l'entree, elles ne le voient pas a la sortie. Zero signal")
    lignes.append("   residuel ne prouve donc pas qu'une copie est propre.")

    if detail:
        lignes.append("")
        lignes.append("DETAIL (doc_id, etat, categories residuelles - jamais de valeur)")
        for c in constats:
            if c.etat == VERIFIE and not c.residu and c.declare:
                continue
            lignes.append("   %-28s %-22s %s%s"
                          % (c.doc_id, c.etat,
                             ",".join(c.residu) or c.motif,
                             "" if c.declare else "  [rien retire]"))
    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--instance", required=True,
                         help="racine de l'instance a examiner, LUE SEULEMENT")
    parseur.add_argument("--detail", action="store_true",
                         help="une ligne par document non conforme")
    args = parseur.parse_args(argv)

    instance = load_instance(None, args.instance)
    from coproscope.modules.privacyops import redactions_path

    registre = redactions_path(instance)
    lignes = _lignes_du_registre(registre)
    if not lignes:
        print("registre de biffage vide ou absent: %s" % registre.name)
        print("Aucun caviardage n'a ete enregistre sur cette instance. Ce n'est")
        print("pas un feu vert: c'est l'absence de la matiere du controle.")
        return 0

    racine_copies = instance.root("workspace")
    constats = [examiner(ligne, racine_copies) for ligne in lignes]
    print(rapport(constats, args.detail))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
