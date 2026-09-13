"""`RM-2026-0052` defaut (3): la section utile est enterree sous les listes.

**Ce qui a ete mesure le 2026-09-03**, sur l'UI reelle: `/ag-contentieux` fait
58 709 px, la section des resolutions commence a 40 120 px, et le rendu
navigateur devient blanc des qu'on quitte le haut de page. Le gouvernail le dit
lui-meme: *la fonctionnalite est livree et correcte, mais pas atteignable*.

**Ce que cette garde ne peut pas faire, et il faut le dire en premier.** Elle ne
mesure aucun pixel. La suite ne contient aucun moteur de rendu - c'est le
constat de `RM-2026-0111` - donc aucune hauteur n'y est calculable. Une mesure
sur la source n'est pas une recette. Le verdict en pixels demande un oeil devant
une fenetre.

**Ce qu'elle mesure a la place, et pourquoi c'est la bonne grandeur.** Une
hauteur est le resultat; ce qui la produit est une STRUCTURE. Un bloc dont la
hauteur suit le nombre de lignes d'un registre pousse vers le bas tout ce qui le
suit, et cette dependance-la se lit dans le gabarit et la feuille de style.

**L'axe.** Le nombre de lignes d'un registre est un degre de liberte: un coffre
porte 30 pieces ou 3 000, et personne ne choisit ce nombre. Plafonner l'affichage
a 80 lignes - ce que cette page faisait deja le 2026-09-03 - rend la hauteur
FINIE sans la rendre BORNEE: cinq tableaux a 80 lignes empilaient toujours des
dizaines de milliers de pixels au-dessus de la section utile.

**Ce qui reste vrai le long de cet axe**: une liste qui a du contenu APRES elle
occupe une hauteur qui ne depend pas du registre qui la remplit. Une liste que
rien ne suit n'enterre rien, et n'a donc rien a borner - c'est le cas des
resolutions elles-mêmes, qui sont la derniere section de la page.

**Pourquoi la garde ne nomme pas les six tableaux.** Les nommer serait coder les
blocs presents le jour ou elle a ete ecrite - exactement le defaut de
`RM-2026-0112`, ou un gabarit enumerait ses rangees. Elle les TROUVE: elle lit
le gabarit, releve chaque boucle qui repete un bloc, remonte la pile des
elements qui l'englobent, et demande a la feuille de style si l'un d'eux est
borne en hauteur.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web"
GABARIT = RACINE / "templates" / "agcontentieux.html"
FEUILLES = sorted((RACINE / "static").glob("styles_part_*.css"))

#: Elements qui ne referment rien: ils ne peuvent pas englober une boucle.
SANS_FERMETURE = {"br", "hr", "img", "input", "meta", "link", "col", "source"}

#: Blocs qu'une boucle REPETE verticalement. Un `<span>` ou un `<td>` repete ne
#: rallonge pas la page; une rangee, un article ou un item de liste, si.
BLOCS_EMPILES = ("<tr", "<article", "<li")

#: Ce qui compte comme SECTION, ici et pour les ancres. Un seul nom pour la
#: meme notion: mesure du 2026-09-09, quatre des six sections ancrees de cette
#: page sont des `<div id=...>` et non des `<section>`. Deux definitions
#: concurrentes de `section` dans un meme fichier, c'est le defaut numero un
#: du produit applique a l'instrument.
_SECTION_RE = re.compile(r'<(?:section|div)[^>]*\sid="([^"]+)"')

#: Une borne verticale est une LONGUEUR, donc elle porte une grandeur chiffree.
#:
#: **L'axe**: la valeur d'une declaration est un degre de liberte, et la
#: presence du NOM de la propriete ne dit rien de ce qu'elle FAIT.
#: **Ce qui reste vrai le long de l'axe**: borner, c'est poser une longueur.
#: `520px`, `min(520px, 62vh)` et `calc(100vh - 96px)` en sont; `none`,
#: `unset`, `initial`, `inherit` n'en sont pas - ils DEBORNENT.
#:
#: **Mesure du 2026-09-09 qui impose cette lecture**: la feuille porte deja
#: quatre `max-height: none`, tous dans des media queries, sur `.cs-ag-list`,
#: `.cs-sidebar`, `.cs-rappro-detail` et `.cs-rappro-queue-panel`. La version
#: precedente de cet instrument testait `"max-height" not in corps`: elle
#: lisait donc ces quatre RETRAITS de borne comme des bornes. Aucune des sept
#: listes de cette page n'en dependait le jour de la mesure - ce n'etait pas
#: un faux vert actif - mais le jour ou `.table-scroll` recoit l'override
#: responsive que quatre autres classes de cette meme feuille portent deja,
#: l'instrument aurait continue de dire vert.
_GRANDEUR_RE = re.compile(r"[0-9]")


def _sans_jinja(texte: str) -> str:
    """Le meme texte, les zones Jinja blanchies - les positions sont gardees."""
    def blanchir(found: re.Match[str]) -> str:
        return " " * len(found.group(0))
    return re.sub(r"\{[%{#].*?[%}#]\}", blanchir, texte, flags=re.S)


def _classes_bornees_en_hauteur() -> set[str]:
    """Classes auxquelles la feuille de style donne une borne verticale."""
    bornees: set[str] = set()
    for feuille in FEUILLES:
        css = re.sub(r"/\*.*?\*/", " ", feuille.read_text(encoding="utf-8"), flags=re.S)
        for selecteur, corps in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            valeurs = re.findall(r"max-height\s*:\s*([^;}]+)", corps)
            if not any(_GRANDEUR_RE.search(valeur) for valeur in valeurs):
                continue
            bornees.update(re.findall(r"\.([A-Za-z0-9_-]+)", selecteur))
    return bornees


def _pile_englobante(texte_nu: str, position: int) -> list[tuple[str, list[str]]]:
    """(balise, classes) des elements ouverts a cette position, du plus externe."""
    pile: list[tuple[str, list[str]]] = []
    for found in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*)>", texte_nu[:position]):
        fermante, nom, attributs = found.group(1), found.group(2).lower(), found.group(3)
        if nom in SANS_FERMETURE or attributs.rstrip().endswith("/"):
            continue
        if fermante:
            for rang in range(len(pile) - 1, -1, -1):
                if pile[rang][0] == nom:
                    del pile[rang:]
                    break
            continue
        classes = re.search(r'class\s*=\s*"([^"]*)"', attributs)
        pile.append((nom, re.findall(r"[A-Za-z0-9_-]+", classes.group(1)) if classes else []))
    return pile


def _boucles_qui_empilent(source: str, nu: str) -> list[dict[str, object]]:
    """Chaque boucle du gabarit qui repete un bloc, avec ce qui la suit."""
    trouvees: list[dict[str, object]] = []
    for found in re.finditer(r"\{%-?\s*for\s+(.+?)\s*-?%\}", source, re.S):
        fin = source.find("{% endfor %}", found.end())
        if fin < 0:
            fin = source.find("endfor", found.end())
        corps = source[found.end():fin]
        if not any(bloc in corps for bloc in BLOCS_EMPILES):
            continue
        trouvees.append({
            "expression": " ".join(found.group(1).split()),
            "debut": found.start(),
            "fin": fin,
            "enterre": bool(_SECTION_RE.search(nu[fin:])),
            "pile": _pile_englobante(nu, found.start()),
        })
    return trouvees


class ListeBorneeSurLaPageAgTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = GABARIT.read_text(encoding="utf-8")
        self.nu = _sans_jinja(self.source)
        self.bornees = _classes_bornees_en_hauteur()
        self.boucles = _boucles_qui_empilent(self.source, self.nu)

    def test_l_instrument_lit_quelque_chose(self) -> None:
        """Plancher anti-mutisme: un vert doit vouloir dire `rien a signaler`,
        jamais `la garde ne lit plus rien`. Si le gabarit est renomme ou si la
        feuille change de forme, c'est ICI que ca se voit."""
        self.assertGreaterEqual(len(FEUILLES), 20, "feuille de style introuvable")
        self.assertGreaterEqual(
            len(self.bornees), 1, "aucune classe bornee en hauteur dans la feuille"
        )
        self.assertGreaterEqual(
            len(self.boucles), 5,
            f"le gabarit ne rend plus que {len(self.boucles)} boucles empilantes:"
            " la garde ne mesure plus la page qu'elle croit mesurer",
        )
        self.assertTrue(
            any(b["enterre"] for b in self.boucles),
            "aucune boucle n'est suivie d'une section: la garde n'a rien a prouver",
        )

    def test_l_instrument_ne_lit_pas_un_retrait_de_borne_comme_une_borne(self) -> None:
        """Controle negatif de l'instrument lui-meme.

        Une media query qui pose `max-height: none` DEBORNE le conteneur.
        L'instrument doit repondre `non bornee` sur cette feuille-la, sinon un
        vert de la garde ci-dessous ne veut plus rien dire. La feuille reelle
        porte deja quatre regles de cette forme.
        """
        with tempfile.TemporaryDirectory() as dossier:
            feuille = Path(dossier) / "styles_part_99.css"
            sauvegarde = list(FEUILLES)
            FEUILLES[:] = [feuille]
            try:
                feuille.write_text(
                    "@media (max-width: 768px) { .table-scroll {"
                    " max-height: none; overflow: visible; } }",
                    encoding="utf-8",
                )
                self.assertNotIn(
                    "table-scroll", _classes_bornees_en_hauteur(),
                    "un RETRAIT de borne est lu comme une borne: l'instrument"
                    " dirait vert sur une page debornee",
                )
                feuille.write_text(
                    ".table-scroll { max-height: min(520px, 62vh); overflow: auto; }",
                    encoding="utf-8",
                )
                self.assertIn(
                    "table-scroll", _classes_bornees_en_hauteur(),
                    "une borne chiffree n'est plus reconnue: l'instrument"
                    " crierait au loup sur une page bornee",
                )
            finally:
                FEUILLES[:] = sauvegarde

    def test_toute_liste_suivie_de_contenu_est_bornee_en_hauteur(self) -> None:
        fautives = []
        for boucle in self.boucles:
            if not boucle["enterre"]:
                continue
            classes = {c for _, cs in boucle["pile"] for c in cs}
            if not (classes & self.bornees):
                fautives.append((boucle["expression"], sorted(classes)))
        self.assertFalse(
            fautives,
            "des listes rallongent la page sans borne, et enterrent ce qui les"
            " suit (RM-2026-0052 defaut 3). Pour chacune: (expression iteree,"
            f" classes englobantes): {fautives}",
        )

    def test_un_conteneur_de_defilement_declare_existe_dans_la_feuille(self) -> None:
        """Le gabarit declarait `.table-scroll` autour du tableau des
        resolutions et AUCUNE regle de la feuille ne repondait a ce nom: le
        conteneur annoncait un defilement qu'il ne faisait pas. Un nom de classe
        n'est pas une garantie tant que la feuille ne repond pas."""
        toutes = set()
        for attributs in re.findall(r'class\s*=\s*"([^"]*)"', self.nu):
            toutes.update(re.findall(r"[A-Za-z0-9_-]+", attributs))
        declarees = {c for c in toutes if "scroll" in c}
        self.assertTrue(declarees, "le gabarit ne declare plus aucun conteneur de defilement")
        muettes = sorted(c for c in declarees if c not in self.bornees)
        self.assertFalse(
            muettes,
            f"conteneur(s) de defilement sans borne verticale dans la feuille: {muettes}",
        )


class SectionUtileAtteignableTests(unittest.TestCase):
    """Le gouvernail dit *livree et correcte, mais pas atteignable*. Une
    section que le bandeau de parcours ne nomme pas ne s'atteint qu'au
    defilement."""

    def setUp(self) -> None:
        self.source = GABARIT.read_text(encoding="utf-8")
        self.nu = _sans_jinja(self.source)

    def test_chaque_section_ancree_est_nommee_par_le_bandeau_de_parcours(self) -> None:
        ancres = set(_SECTION_RE.findall(self.nu))
        vises = set(re.findall(r'<a[^>]*class="[^"]*next-action-card[^"]*"[^>]*href="#([^"]+)"',
                               self.nu))
        self.assertTrue(ancres, "la page ne porte plus aucune section ancree")
        self.assertTrue(vises, "le bandeau de parcours ne vise plus aucune ancre")
        self.assertFalse(
            vises - ancres, f"le bandeau vise des ancres qui n'existent pas: {sorted(vises - ancres)}"
        )
        self.assertFalse(
            ancres - vises,
            "des sections de la page ne sont nommees par aucune carte de"
            f" parcours, donc atteignables au seul defilement: {sorted(ancres - vises)}",
        )


if __name__ == "__main__":
    unittest.main()
