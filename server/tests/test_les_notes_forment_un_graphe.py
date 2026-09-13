# -*- coding: utf-8 -*-
"""Un seul accueil, des notes qui se tiennent: le graphe de la documentation publique.

`RM-2026-0183`, lot 8 du 2026-09-13. Le depot avait onze fichiers `README.md`,
qui se renvoyaient les uns aux autres et se contredisaient sur la commande qui
joue la suite. Il n'en garde qu'un, l'accueil, et des notes dans `docs/notes/`.

**LE PREDICAT, ENONCE AVANT DE CHERCHER.** *Depuis le `README.md` racine, en
suivant les liens, on atteint chaque note de `docs/notes/`; chaque lien relatif
de l'accueil et des notes mene a un fichier present; chaque note porte une
section « Notes liees » qui renvoie a au moins une autre note; chaque `RM-*`
cite par une note existe au registre; et aucun autre `README.md` n'existe dans
le depot que l'accueil et la fixture nommee.*

**OU LA GARDE REGARDE.** Les notes se decouvrent dans le dossier, jamais dans une
liste: une note ajoutee demain est lue le jour de sa creation, et une note que
rien ne relie echoue. Les `README.md` se cherchent dans l'arborescence reelle,
dossiers caches exclus. Chaque clause a son temoin fabrique, qui la fait mordre.
"""
from __future__ import annotations

import os
import re
import tempfile
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
NOTES = "docs/notes"
REGISTRE = "docs/roadmap_backlog_central.md"

#: La fixture des tests porte un README: elle decrit une instance, pas le depot.
READMES_ADMIS = {"README.md", "examples/synthetic_copro/README.md"}

LIEN = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
RM = re.compile(r"RM-\d{4}-\d{4}")
SECTION = re.compile(r"^## Notes li(?:é|e)es\s*$", re.M)


def _liens(fichier: Path) -> list[str]:
    return [m.group(1) for m in LIEN.finditer(fichier.read_text(encoding="utf-8"))]


def _local(cible: str) -> str | None:
    if cible.startswith(("http:", "https:", "mailto:", "#")):
        return None
    return cible.split("#", 1)[0] or None


def fautes_de_liens(racine: Path) -> list[str]:
    fautes = []
    for fichier in [racine / "README.md", *sorted((racine / NOTES).glob("*.md"))]:
        for cible in _liens(fichier):
            chemin = _local(cible)
            if chemin and not (fichier.parent / chemin).resolve().exists():
                fautes.append("%s: lien mort %s" % (fichier.relative_to(racine).as_posix(), cible))
    return fautes


def notes_orphelines(racine: Path) -> list[str]:
    notes = {p.resolve() for p in (racine / NOTES).glob("*.md")}
    vues, pile = set(), [(racine / "README.md").resolve()]
    while pile:
        courant = pile.pop()
        if courant in vues:
            continue
        vues.add(courant)
        for cible in _liens(courant):
            chemin = _local(cible)
            if chemin:
                suite = (courant.parent / chemin).resolve()
                if suite in notes and suite not in vues:
                    pile.append(suite)
    return sorted(p.name for p in notes - vues)


def notes_sans_voisines(racine: Path) -> list[str]:
    fautes = []
    for note in sorted((racine / NOTES).glob("*.md")):
        texte = note.read_text(encoding="utf-8")
        m = SECTION.search(texte)
        if not m:
            fautes.append("%s: pas de section « Notes liées »" % note.name)
            continue
        section = texte[m.end():].split("\n## ", 1)[0]
        voisines = [c for c in (m2.group(1) for m2 in LIEN.finditer(section))
                    if _local(c) and _local(c).endswith(".md") and (note.parent / _local(c)).resolve().parent == note.parent.resolve()]
        if not voisines:
            fautes.append("%s: « Notes liées » ne renvoie à aucune note" % note.name)
    return fautes


def rm_inconnus(racine: Path) -> list[str]:
    connus = set(RM.findall((racine / REGISTRE).read_text(encoding="utf-8")))
    fautes = []
    for fichier in [racine / "README.md", *sorted((racine / NOTES).glob("*.md"))]:
        for rm in sorted(set(RM.findall(fichier.read_text(encoding="utf-8"))) - connus):
            fautes.append("%s cite %s, absent du registre" % (fichier.name, rm))
    return fautes


#: Sorties de fabrication, jamais suivies: l'executable PyInstaller y recopie ses
#: propres fichiers. Les dossiers caches (`.venv`, `.git`, worktrees) sont exclus
#: par leur forme. **Residu declare:** un README pose dans un dossier non suivi
#: d'un autre nom serait signale a tort sur le poste - jamais en CI.
SORTIES = ("node_modules", "__pycache__", "dist", "build")


def readmes_en_trop(racine: Path) -> list[str]:
    trouves = []
    for dossier, sous, fichiers in os.walk(racine):
        sous[:] = [d for d in sous if not d.startswith(".") and d not in SORTIES]
        trouves += [Path(dossier, f).relative_to(racine).as_posix() for f in fichiers if f.lower() == "readme.md"]
    return sorted(set(trouves) - READMES_ADMIS)


class LA_DOCUMENTATION_DU_DEPOT(unittest.TestCase):
    def test_des_notes_sont_lues(self) -> None:
        """Sans cela, une garde qui ne lit rien passerait pour verte."""
        self.assertGreaterEqual(len(list((DEPOT / NOTES).glob("*.md"))), 10)

    def test_aucun_lien_relatif_ne_mene_nulle_part(self) -> None:
        fautes = fautes_de_liens(DEPOT)
        self.assertEqual([], fautes, "\n".join(fautes))

    def test_chaque_note_est_atteinte_depuis_l_accueil(self) -> None:
        self.assertEqual([], notes_orphelines(DEPOT))

    def test_chaque_note_renvoie_a_ses_voisines(self) -> None:
        fautes = notes_sans_voisines(DEPOT)
        self.assertEqual([], fautes, "\n".join(fautes))

    def test_chaque_rm_cite_existe(self) -> None:
        fautes = rm_inconnus(DEPOT)
        self.assertEqual([], fautes, "\n".join(fautes))

    def test_un_seul_readme(self) -> None:
        self.assertEqual([], readmes_en_trop(DEPOT))


class LES_TEMOINS_FONT_MORDRE_CHAQUE_CLAUSE(unittest.TestCase):
    def _depot(self, fichiers: dict[str, str]) -> Path:
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        racine = Path(dossier.name)
        base = {
            "README.md": "[a](docs/notes/a.md)\n",
            REGISTRE: "| `RM-2026-0001` |\n",
            NOTES + "/a.md": "# A\n`RM-2026-0001`\n## Notes liées\n- [b](b.md)\n",
            NOTES + "/b.md": "# B\n## Notes liées\n- [a](a.md)\n",
        }
        base.update(fichiers)
        for chemin, texte in base.items():
            if texte is None:
                continue
            (racine / chemin).parent.mkdir(parents=True, exist_ok=True)
            (racine / chemin).write_text(texte, encoding="utf-8")
        return racine

    def test_le_depot_temoin_est_propre(self) -> None:
        racine = self._depot({})
        self.assertEqual(([], [], [], [], []), (fautes_de_liens(racine), notes_orphelines(racine),
                         notes_sans_voisines(racine), rm_inconnus(racine), readmes_en_trop(racine)))

    def test_un_lien_mort_est_vu(self) -> None:
        self.assertTrue(fautes_de_liens(self._depot({NOTES + "/b.md": "# B\n[x](absent.md)\n## Notes liées\n- [a](a.md)\n"})))

    def test_une_note_que_rien_ne_relie_est_vue(self) -> None:
        racine = self._depot({NOTES + "/c.md": "# C\n## Notes liées\n- [a](a.md)\n"})
        self.assertEqual(["c.md"], notes_orphelines(racine))

    def test_une_note_sans_voisines_est_vue(self) -> None:
        self.assertTrue(notes_sans_voisines(self._depot({NOTES + "/b.md": "# B\n[a](a.md)\n"})))
        self.assertTrue(notes_sans_voisines(self._depot({NOTES + "/b.md": "# B\n## Notes liées\n- [site](https://x)\n"})))

    def test_un_rm_inconnu_est_vu(self) -> None:
        self.assertTrue(rm_inconnus(self._depot({NOTES + "/b.md": "# B\n`RM-2026-9999`\n## Notes liées\n- [a](a.md)\n"})))

    def test_un_second_readme_est_vu(self) -> None:
        self.assertEqual(["server/README.md"], readmes_en_trop(self._depot({"server/README.md": "# x\n"})))


if __name__ == "__main__":
    unittest.main()
