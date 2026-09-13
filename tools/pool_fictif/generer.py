# -*- coding: utf-8 -*-
"""Fabriquer le pool fictif: une instance VIDE, des pieces au format scelle.

Usage: `python tools/pool_fictif/generer.py <dossier-cible>` puis
`coproscope pipeline run --instance-root <dossier-cible>` - la chaine du produit
reconstruit registres, textes et coffre depuis les pieces. Rien n'est ecrit a la
main en aval des pieces: c'est ce qui rend la demo *branchee*.

Le generateur est deterministe: memes pieces, memes octets, a chaque passage.
Il refuse d'ecrire dans un dossier non vide, pour ne jamais melanger une sortie
precedente a une entree neuve.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pieces import COPRO, PIECES  # type: ignore
else:  # pragma: no cover
    from .pieces import COPRO, PIECES

#: Date figee des metadonnees: une date du jour changerait les octets.
DATE_PDF = "D:20250101000000Z"
INSTANCE_ID = "demo-glycines-fictive"


def instance_yml() -> dict:
    return {
        "version": 1,
        "instance_id": INSTANCE_ID,
        "display_name": COPRO,
        "scope": "copro_simple",
        "entity_id": "main",
        "roots": {"workspace": ".", "raw": "./raw", "system": "./system", "outputs": "./outputs",
                  "staging": "./staging", "logs": "./logs", "restricted": []},
        "registers": {
            "documents": "./registers/registre_documents.csv",
            "duplicates": "./registers/registre_doublons.csv",
            "manifest": "./registers/manifest_sha256.csv",
            "requests": "./registers/registre_demandes.csv",
            "ag": "./registers/registre_ag.csv",
            "findings": "./registers/constats_diligences.csv",
            "kpi": "./registers/kpi.csv",
        },
        "artifacts": {"text_dir": "./staging/text", "classified_dir": "./staging/classified",
                      "reports_dir": "./outputs/reports", "docai_dir": "./staging/docai",
                      "accounting_dir": "./outputs/accounting"},
        "settings": {
            "never_modify_raw": True,
            "write_outputs_only": True,
            "demo": {"fictive": True, "libelle": "Copropriete fictive de demonstration"},
            "vault": {"local_root": "./vault_local"},
            "docai": {"mode": "off", "privacy": "local_only"},
        },
    }


def ecrire_pdf(chemin: Path, texte: str) -> None:
    import textwrap

    import pymupdf  # extra `accounting`

    doc = pymupdf.open()
    lignes = texte.split("\n")
    par_page = 52
    for debut in range(0, len(lignes), par_page):
        page = doc.new_page(width=595, height=842)
        y = 56
        for ligne in lignes[debut:debut + par_page]:
            # Retour a la ligne simple, a largeur fixe: la mise en page n'est pas le sujet.
            morceaux = textwrap.wrap(ligne, 95, break_long_words=False) or [""]
            for morceau in morceaux:
                page.insert_text((56, y), morceau, fontname="helv", fontsize=9.5)
                y += 13.5
    doc.set_metadata({"title": chemin.stem, "author": "CoproScope demo (fictive)", "creator": "tools/pool_fictif",
                      "producer": "CoproScope", "creationDate": DATE_PDF, "modDate": DATE_PDF})
    doc.save(str(chemin), garbage=4, deflate=True, no_new_id=True)
    doc.close()


def generer(cible: Path) -> list[Path]:
    cible = Path(cible)
    if cible.exists() and any(cible.iterdir()):
        raise SystemExit("le dossier cible n'est pas vide: %s" % cible)
    (cible / "raw").mkdir(parents=True, exist_ok=True)
    for dossier in ("registers", "staging", "outputs", "logs", "system", "vault_local"):
        (cible / dossier).mkdir(exist_ok=True)
    (cible / "instance.yml").write_text(json.dumps(instance_yml(), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    ecrits = []
    for nom, texte in PIECES:
        chemin = cible / "raw" / nom
        ecrire_pdf(chemin, texte)
        ecrits.append(chemin)
    return ecrits


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: generer.py <dossier-cible-vide>")
    for chemin in generer(Path(sys.argv[1])):
        print(chemin.name)
