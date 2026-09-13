# -*- coding: utf-8 -*-
"""Exporter l'interface en pages statiques, pour la demo en lecture seule.

`RM-2026-0183`, lot 8 du 2026-09-13. Usage:

    python tools/demo_statique/exporter.py --instance-root <instance> --sortie <dossier>

**CE QUI EST EXPORTE, ET POURQUOI CE N'EST PAS UNE LISTE.** Les pages sont celles
qu'un utilisateur atteint en suivant les liens de l'interface depuis `/`, par le
meme moteur que la garde des liens morts (`web/_parcours_liens.py`). Une page
ajoutee demain entre dans la demo le jour ou un lien y mene; une page retiree en
sort le jour ou plus rien n'y mene.

**CE QUE L'EXPORT CHANGE A CHAQUE PAGE, ET RIEN D'AUTRE:**

- chaque adresse `href` ou `src` qui vise le serveur devient un chemin RELATIF
  vers son fichier - le site tient sous n'importe quel prefixe, dont celui de
  GitHub Pages. La forme d'ecriture de l'adresse est un degre de liberte: le
  client de test en ecrit certaines en chemin racine (`/comptes`), d'autres en
  absolu sur son propre hote (`http://testserver/static/styles.css`). Les deux
  sont reecrites;
- une adresse vers une page que l'export n'a pas pu rendre est neutralisee et le
  dit (`data-demo-indisponible`), au lieu de mener a une 404;
- les formulaires ne soumettent rien; le mode recette, qui enregistre des
  annotations, est retire;
- un bandeau dit, en tete de chaque page, que la demo est fictive et en lecture
  seule.

**HORS PORTEE, DECLARE.** Un script qui construit une adresse lui-meme n'est pas
reecrit. Le filtre sur place du controle de gouvernance fonctionne, parce qu'il
charge le `href` deja reecrit de la pastille.

Le rapport `_rapport.json` nomme les pages, les liens neutralises et le plafond.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import shutil
import sys
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit

DEPOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DEPOT / "server" / "src"))

from coproscope.web._parcours_liens import HOTES_INTERNES, lien_interne, parcourir  # noqa: E402

STATIQUE = DEPOT / "server" / "src" / "coproscope" / "web" / "static"
BANDEAU = (
    '<div class="cs-demo-statique" role="note" style="position:fixed;right:16px;bottom:16px;z-index:1000;'
    'max-width:min(420px,calc(100vw - 32px));padding:10px 14px;border-radius:8px;background:#fff7e0;'
    'color:#5c3d00;border:1px solid #e0b84c;box-shadow:0 4px 14px rgba(0,0,0,.18);'
    'font:600 14px/1.4 system-ui,sans-serif">Démo en lecture seule : une copropriété '
    'entièrement fictive. Rien de ce que vous faites ici n\'est enregistré.</div>'
)
INDISPONIBLE = 'href="#" data-demo-indisponible="1" title="Non disponible dans la démo statique"'
RECETTE = [
    re.compile(r'<script id="cs-recette-config"[^>]*>.*?</script>', re.S),
    re.compile(r'<script[^>]*recette_mode\.js[^>]*></script>'),
    re.compile(r'<button id="cs-recette-mode-toggle".*?</button>', re.S),
    re.compile(r'<span id="cs-recette-mode-status"[^>]*></span>'),
]
FORM = re.compile(r"<form\b([^>]*)>", re.I)
ACTION = re.compile(r"""\s(?:action|method)\s*=\s*(["']).*?\1""", re.I | re.S)
ATTRIBUT = re.compile(r"""\b(href|src)\s*=\s*(["'])(.*?)\2""", re.I | re.S)
FEUILLE = re.compile(r"""<link\b[^>]*\brel\s*=\s*["']?stylesheet[^>]*>""", re.I)


def fichier_de(chemin: str) -> str:
    """Le fichier d'une page: deterministe, sans caractere hostile a un hebergeur."""
    base, _, requete = chemin.partition("?")
    dossier = base.strip("/")
    if not requete:
        return posixpath.join(dossier, "index.html") if dossier else "index.html"
    lisible = re.sub(r"[^A-Za-z0-9]+", "-", requete).strip("-")[:60]
    empreinte = hashlib.sha1(requete.encode("utf-8")).hexdigest()[:8]
    nom = "q-%s-%s.html" % (lisible, empreinte)
    return posixpath.join(dossier, nom) if dossier else nom


def relatif(depuis: str, vers: str) -> str:
    return posixpath.relpath(vers, posixpath.dirname(depuis) or ".")


def _interne(valeur: str) -> bool:
    """Vrai si l'adresse vise le serveur d'export: chemin racine, ou hote du client de test."""
    morceaux = urlsplit(valeur)
    if morceaux.scheme or morceaux.netloc:
        return morceaux.scheme in {"http", "https"} and morceaux.hostname in HOTES_INTERNES
    return valeur.startswith("/") and not valeur.startswith("//")


def reecrire(page: str, html: str, exportees: set[str]) -> tuple[str, int]:
    """La page, avec ses adresses relatives, ses formulaires neutralises et son bandeau."""
    neutralises = 0
    profondeur = "../" * page.count("/")

    def attribut(m: re.Match) -> str:
        nonlocal neutralises
        nom = m.group(1)
        valeur = unescape(m.group(3)).strip()
        if not _interne(valeur):
            return m.group(0)
        morceaux = urlsplit(valeur)
        if morceaux.path.startswith("/static/"):
            requete = "?" + morceaux.query if morceaux.query else ""
            return '%s="%s%s%s"' % (nom, profondeur, morceaux.path[1:], requete)
        cible = lien_interne(valeur) if nom.lower() == "href" else None
        if cible is not None and cible in exportees:
            ancre = "#" + morceaux.fragment if morceaux.fragment else ""
            return '%s="%s%s"' % (nom, relatif(page, fichier_de(cible)), ancre)
        neutralises += 1
        return INDISPONIBLE if nom.lower() == "href" else 'src="" data-demo-indisponible="1"'

    html = ATTRIBUT.sub(attribut, html)
    for guillemet in ('"', "'", "("):
        html = html.replace(guillemet + "/static/", guillemet + profondeur + "static/")
    for motif in RECETTE:
        html = motif.sub("", html)
    html = FORM.sub(lambda m: '<form%s data-demo-statique="neutralise" onsubmit="return false;">'
                    % ACTION.sub("", m.group(1)), html)
    html = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + BANDEAU, html, count=1)
    return html, neutralises


def instance_fictive(instance_root: Path) -> bool:
    """Vrai seulement si la configuration dit elle-meme `settings.demo.fictive: true`.

    Le bandeau affirme *une copropriete entierement fictive*. L'affirmation se
    lit dans l'instance, jamais dans l'intention de celui qui lance l'export: une
    configuration illisible ou muette vaut refus.
    """
    try:
        config = json.loads((instance_root / "instance.yml").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    demo = (config.get("settings") or {}).get("demo") or {}
    return demo.get("fictive") is True


def exporter(instance_root: Path, sortie: Path, annee: int = 2025, plafond: int = 3000) -> dict:
    from fastapi.testclient import TestClient

    from coproscope.core.common import load_instance
    from coproscope.web.app import create_app

    if sortie.exists() and any(sortie.iterdir()):
        raise SystemExit("la sortie %s n'est pas vide: rien n'est ecrit" % sortie)
    if not instance_fictive(instance_root):
        raise SystemExit("l'instance %s ne se declare pas fictive (settings.demo.fictive): "
                         "le bandeau de la demo serait faux, rien n'est ecrit" % instance_root)
    client = TestClient(create_app(load_instance(None, str(instance_root)), annee))
    rendus: dict[str, str] = {}

    def obtenir(chemin: str):
        reponse = client.get(chemin)
        type_contenu = reponse.headers.get("content-type", "")
        if reponse.status_code < 400 and "html" in type_contenu:
            rendus[chemin] = reponse.text
        return reponse.status_code, type_contenu, reponse.text

    parcours = parcourir(obtenir, "/", plafond)
    exportees = set(rendus)
    sortie.mkdir(parents=True, exist_ok=True)
    neutralises = {}
    for chemin, html in sorted(rendus.items()):
        page = fichier_de(chemin)
        texte, n = reecrire(page, html, exportees)
        if n:
            neutralises[chemin] = n
        cible = sortie / page
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(texte, encoding="utf-8")
    shutil.copytree(STATIQUE, sortie / "static")
    (sortie / ".nojekyll").write_text("", encoding="utf-8")
    rapport = {
        "pages": len(exportees),
        "fichiers": {chemin: fichier_de(chemin) for chemin in sorted(exportees)},
        "non_exportees": sorted((c, s) for c, s in parcours.pages.items() if c not in exportees),
        "liens_neutralises_par_page": neutralises,
        "plafond_atteint": parcours.plafond_atteint,
    }
    (sortie / "_rapport.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding="utf-8")
    return rapport


def _feuille_chargee(fichier: Path, balise: str) -> bool:
    m = ATTRIBUT.search(balise)
    if not m or m.group(1).lower() != "href":
        return False
    chemin = unescape(m.group(3)).strip().split("#", 1)[0].split("?", 1)[0]
    if not chemin or _interne(chemin) or chemin.startswith(("http:", "https:", "//")):
        return False
    return (fichier.parent / chemin).resolve().is_file()


def verifier_site(sortie: Path) -> list[str]:
    """Ce qui, dans un site exporte, ne tiendrait pas sans serveur.

    Pour chaque page: au moins une feuille de style se charge, tout `href`/`src`
    relatif mene a un fichier existant, aucune adresse ne vise le serveur
    d'export - ni en chemin racine, ni en absolu sur l'hote du client de test -,
    aucun jeton ne subsiste, le bandeau est la, et aucun formulaire ne soumet.
    """
    fautes = []
    for fichier in sorted(sortie.rglob("*.html")):
        page = fichier.relative_to(sortie).as_posix()
        texte = fichier.read_text(encoding="utf-8")
        if "cs-demo-statique" not in texte:
            fautes.append("%s: bandeau absent" % page)
        if not any(_feuille_chargee(fichier, balise) for balise in FEUILLE.findall(texte)):
            fautes.append("%s: aucune feuille de style ne se charge" % page)
        if "token=" in texte:
            fautes.append("%s: un jeton subsiste" % page)
        for m in FORM.finditer(texte):
            if "data-demo-statique" not in m.group(0):
                fautes.append("%s: formulaire actif" % page)
        for _, _, brut in ATTRIBUT.findall(texte):
            valeur = unescape(brut).strip()
            if _interne(valeur):
                fautes.append("%s: adresse du serveur d'export %s" % (page, valeur[:80]))
                continue
            if not valeur or valeur.startswith(("#", "http:", "https:", "//", "mailto:", "tel:", "data:", "javascript:")):
                continue
            chemin = valeur.split("#", 1)[0].split("?", 1)[0]
            if chemin and not (fichier.parent / chemin).resolve().is_file():
                fautes.append("%s: cible absente %s" % (page, valeur[:80]))
    return fautes


def main() -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--instance-root", required=True, type=Path)
    parseur.add_argument("--sortie", required=True, type=Path)
    parseur.add_argument("--annee", type=int, default=2025)
    args = parseur.parse_args()
    rapport = exporter(args.instance_root, args.sortie, args.annee)
    fautes = verifier_site(args.sortie)
    print("pages: %d, non exportees: %d, plafond atteint: %s" % (
        rapport["pages"], len(rapport["non_exportees"]), rapport["plafond_atteint"]))
    for faute in fautes[:40]:
        print("FAUTE", faute)
    print("fautes: %d" % len(fautes))
    return 1 if fautes or rapport["plafond_atteint"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
