# -*- coding: utf-8 -*-
"""Un nombre compose ne perd pas sa source entre sa composition et son affichage.

`RM-2026-0134`. Un `max()` applique a des quantites de sens different rend un
nombre **en effacant la source gagnante**: *reduire a un scalaire ce qui est
une table* (`CLAUDE.md`). Le lot du matin avait corrige trois sites en gardant
la valeur ET tous ses candidats. Cette garde reprend la preuve qui l'annoncait.

----------------------------------------------------------------------
Ce que la preuve precedente gardait, et ce qu'elle ne gardait pas
----------------------------------------------------------------------

`test_un_comptage_compose_dit_d_ou_il_vient.py` portait deux tests de
frontiere, et tous deux lisaient du TEXTE sur un chemin FIGE:

- l'un exigeait que trois noms de cles *apparaissent* dans
  `part_001.pyfrag` - **un commentaire le satisfaisait**;
- l'autre interdisait trois litteraux d'ASSIGNATION, `"invoice_total = max("`
  et deux autres - **une enumeration de modalites**, et elle etait **deja
  defaite dans le fichier qu'elle lisait**: la ligne 274 du meme fragment ecrit
  `"analyzed_posts_count": max(post_count, invoice_count, len(alerts) ...)`,
  un `max()` nu entre un comptage de POSTES, un de FACTURES et un d'ALERTES,
  sous le MEME nom de cle. La forme a deux-points n'appariait pas le litteral:
  garde verte, defaut vivant.

Et la source affichee pouvait etre inventee d'un etage: le candidat
`COMPTAGE_CATEGORIES` de la composition corrigee est la SOMME de ce meme
`analyzed_posts_count` par categorie. `source == "categories"` pouvait donc etre
vrai quand le nombre venait de `len(alerts)`.

----------------------------------------------------------------------
Le predicat, et pourquoi il est un AXE et non une modalite
----------------------------------------------------------------------

**Un appel `max(a1, ..., an)` dont AU MOINS DEUX arguments positionnels ne sont
pas des constantes litterales est une COMPOSITION.** Le nombre d'arguments qui
sont des quantites EST l'axe: une quantite entouree de bornes litterales -
`max(x, 0)`, `max(x, 1)` - est un BORNAGE et ne perd aucune source; deux
quantites ou plus effacent le gagnant. Un quatrieme site ecrit demain, sous un
nom que personne n'a prevu, tombe dedans le jour de sa naissance.

**Le corpus est la source que Python EXECUTE**, pas une extension: les `.py` de
`web/` ET les repertoires de fragments, concatenes comme le chargeur les
concatene (`coproscope.source_fragments`). Un `rglob("*.py")` seul serait
aveugle aux fragments - la ou vit precisement l'un des sites.

**Cas a reponse connue, passe avant d'y croire:** l'instruction adverse avait
enumere a la main quatre compositions nues; ce recensement, ecrit
independamment, rend exactement les quatre, sur 98 unites de compilation et 19
appels `max()`.

----------------------------------------------------------------------
Ce que cette garde NE tranche PAS, et ce qu'elle ne couvre pas
----------------------------------------------------------------------

**Elle ne dit pas si `max()` est la bonne regle de composition.** Le lot du
matin l'a garde deliberement: la changer deplacerait des chiffres affiches sans
qu'aucune mesure ne dise dans quel sens. Cela demande un arbitrage et une
mesure avant/apres. La garde BORNE et NOMME; elle n'arbitre pas.

**Residu nomme et non couvert: la composition par chaine `or`.**
`viewmodels/_pieces_ux.py` ecrit `piece_summary.get("total") or len(items) or
len(examples)` et `... or linked_documents_count`: la premiere quantite non
nulle gagne, par PRESEANCE, et le gagnant est efface de la meme facon. Meme
axe, autre forme. Elle n'est pas dans cette garde, et c'est dit ici plutot que
d'elargir la portee sans mesurer ses faux positifs.

**Le declencheur cote gabarit n'est pas decidable statiquement tel qu'il etait
propose**: aucun gabarit ne nomme ces cles, l'ecran rend des `_label`, des
pourcentages et `counter().value`. Il est remplace par ce qui se mesure: la
provenance VOYAGE jusqu'a la charge utile construite (`paires_de_provenance`,
appliquee dans `test_ui_comptes_guide`).
"""
from __future__ import annotations

import ast
import unittest
import warnings
from pathlib import Path

from coproscope.source_fragments import fragment_sources

WEB = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web"

#: Les suffixes qui disent d'ou vient une valeur, declares a UN SEUL endroit.
#: `ComptageLu.source`, `ComptageLu.phrase()` et `MontantLu.lu_sur` les
#: produisent. Un temoin echoue si une charge utile porte une provenance dont le
#: suffixe n'est pas ici: un quatrieme nom ne naitra pas invisible.
SUFFIXES_DE_PROVENANCE = ("_source", "_provenance", "_lu_sur")

#: Les formes de la cle de VALEUR qu'un tronc de provenance designe.
FORMES_DE_VALEUR = ("", "_count", "_amount")

#: Les compositions nues au 2026-09-12, identifiees par leur UNITE et leur TEXTE
#: d'appel - jamais par un numero de ligne, qui bouge au premier ajout au-dessus.
#: Egalite d'ensembles: une composition nouvelle echoue, une composition reparee
#: qui reste ici echoue aussi.
DETTE_2026_09_12: frozenset[tuple[str, str]] = frozenset({
    ("viewmodels/_comptes_builder_fragments#fragments",
     "max(post_count, invoice_count, len(alerts) if not post_count and (not invoice_count) else 0)"),
    ("viewmodels/_source_models.py",
     "max(invoices.count, matches.count + non_matches.count)"),
    ("viewmodels/_source_models.py",
     "max(len(ok_matches), summary_ok_count)"),
    # Ce texte-ci avait d'abord ete ecrit DE MEMOIRE, depuis une sortie tronquee
    # a 90 caracteres - et mal devine. L'egalite d'ensembles a mordu dans les
    # deux sens au premier passage. Il est recopie de la mesure.
    ("viewmodels/_ux_model.py",
     "max(int(document_summary.get('total') or 0), "
     "int(document_summary.get('present') or 0) + missing_pieces, 1)"),
})


def sources_executees(racine: Path = WEB) -> list[tuple[str, str]]:
    """Toute la source que Python execute sous `racine`, etiquetee.

    Les etiquettes utilisent `/` quel que soit le systeme: une dette ecrite sous
    Windows avec `\\` echouerait en integration continue sous Linux, sans que le
    code ait bouge.
    """
    sources = [
        (chemin.relative_to(racine).as_posix(),
         chemin.read_text(encoding="utf-8", errors="replace"))
        for chemin in sorted(racine.rglob("*.py"))
        if "__pycache__" not in chemin.parts
    ]
    return sources + [(nom.replace("\\", "/"), texte)
                      for nom, texte in fragment_sources(racine)]


def est_une_composition(appel: ast.Call) -> bool:
    return (isinstance(appel.func, ast.Name) and appel.func.id == "max"
            and sum(1 for a in appel.args if not isinstance(a, ast.Constant)) >= 2)


def compositions(sources: list[tuple[str, str]]) -> tuple[set[tuple[str, str]], dict, int]:
    """`(nues, lignes, appels_max)`: les compositions nues, leur ligne, le total."""
    nues: set[tuple[str, str]] = set()
    lignes: dict[tuple[str, str], int] = {}
    appels_max = 0
    for nom, texte in sources:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            arbre = ast.parse(texte)
        parents = {e: n for n in ast.walk(arbre) for e in ast.iter_child_nodes(n)}
        for noeud in ast.walk(arbre):
            if not (isinstance(noeud, ast.Call) and isinstance(noeud.func, ast.Name)
                    and noeud.func.id == "max"):
                continue
            appels_max += 1
            if not est_une_composition(noeud):
                continue
            # Couverte si elle est lexicalement l'argument de `le_plus_grand`,
            # qui garde la valeur ET ses candidats.
            p, couverte = parents.get(noeud), False
            while p is not None:
                if (isinstance(p, ast.Call) and isinstance(p.func, ast.Name)
                        and p.func.id == "le_plus_grand"):
                    couverte = True
                    break
                p = parents.get(p)
            if not couverte:
                cle = (nom, ast.unparse(noeud))
                nues.add(cle)
                lignes[cle] = noeud.lineno
    return nues, lignes, appels_max


def paires_de_provenance(charge: dict) -> tuple[list[tuple[str, str]], list[str]]:
    """`(paires, orphelines)`: chaque provenance appariee a sa valeur, par TRONC.

    L'appariement part des cles de PROVENANCE, pas des cles de valeur: partir de
    `k + "_source"` rendait l'ensemble vide, parce que la valeur s'appelle
    `invoice_total_count` et sa provenance `invoice_total_source`. Une
    provenance dont le tronc ne designe aucune valeur est ORPHELINE, et c'est un
    defaut a nommer, pas un cas a ignorer.
    """
    paires, orphelines = [], []
    for cle in sorted(charge):
        suffixe = next((s for s in SUFFIXES_DE_PROVENANCE if cle.endswith(s)), None)
        if suffixe is None or not isinstance(charge[cle], str):
            continue
        tronc = cle[: -len(suffixe)]
        valeur = next((tronc + f for f in FORMES_DE_VALEUR if tronc + f in charge), None)
        if valeur is None:
            orphelines.append(cle)
        else:
            paires.append((valeur, cle))
    return paires, orphelines


class AUCUNE_COMPOSITION_NUE_N_ENTRE_EN_SILENCE(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.nues, cls.lignes, cls.appels = compositions(sources_executees())

    def test_aucune_composition_NOUVELLE(self) -> None:
        nouvelles = sorted(self.nues - DETTE_2026_09_12)
        self.assertEqual(
            [], nouvelles,
            "des `max()` composent au moins deux quantites et effacent la source "
            "gagnante: %s. Garder la valeur ET ses candidats (`le_plus_grand`, "
            "`ComptageLu`), comme l'a fait RM-2026-0134."
            % ["%s:%d %s" % (n, self.lignes[(n, t)], t[:70]) for n, t in nouvelles])

    def test_la_dette_ne_porte_pas_de_composition_REPAREE(self) -> None:
        reparees = sorted(DETTE_2026_09_12 - self.nues)
        self.assertEqual(
            [], reparees,
            "ces compositions ne sont plus nues: les retirer de la dette, sinon "
            "elle ment sur ce qu'il reste: %r" % reparees)


class LES_TEMOINS_SANS_LESQUELS_LE_RECENSEMENT_MESURERAIT_LE_VIDE(unittest.TestCase):

    def test_le_corpus_inclut_les_FRAGMENTS(self) -> None:
        """Un balayage `*.py` seul manquerait l'un des quatre sites."""
        noms = [n for n, _ in sources_executees()]
        self.assertTrue(any(n.endswith("#fragments") for n in noms),
                        "aucun repertoire de fragments lu: le corpus est aveugle")
        self.assertGreater(len(noms), 40)

    def test_le_recensement_trouve_des_appels(self) -> None:
        _, _, appels = compositions(sources_executees())
        self.assertGreater(appels, 10, "presque aucun `max()` trouve: le "
                                       "recensement ne lit plus le code")

    def test_l_axe_DISCRIMINE_bornage_et_composition(self) -> None:
        """Le temoin qui fait de ce critere un axe et non une liste."""
        def une(texte: str) -> ast.Call:
            return ast.parse(texte, mode="eval").body  # type: ignore[return-value]
        self.assertFalse(est_une_composition(une("max(x, 0)")), "un bornage")
        self.assertFalse(est_une_composition(une("max(x, 1)")), "un bornage")
        self.assertTrue(est_une_composition(une("max(a, b)")))
        self.assertTrue(est_une_composition(une("max(len(a), n + m, 0)")))
        self.assertFalse(est_une_composition(une("min(a, b)")), "hors portee")

    def test_une_composition_ECRITE_DEMAIN_est_vue(self) -> None:
        """Un nom que personne n'a prevu, dans un fichier que personne ne nomme."""
        nues, _, _ = compositions([("un/module/neuf.py",
                                    "total = max(factures, ecritures)\n")])
        self.assertEqual({("un/module/neuf.py", "max(factures, ecritures)")}, nues)

    def test_une_composition_passee_a_le_plus_grand_est_COUVERTE(self) -> None:
        nues, _, _ = compositions([("m.py", "v = le_plus_grand(max(a, b))\n")])
        self.assertEqual(set(), nues)


class LA_PROVENANCE_S_APPARIE_PAR_TRONC(unittest.TestCase):
    """L'instrument du bras applique a la charge utile reelle."""

    def test_trois_formes_de_valeur_et_trois_suffixes(self) -> None:
        charge = {"invoice_total_count": 2, "invoice_total_source": "synthese",
                  "total_charges": 1380.0, "total_charges_lu_sur": "annexe 2",
                  "p1_count": 1}
        paires, orphelines = paires_de_provenance(charge)
        self.assertEqual([("invoice_total_count", "invoice_total_source"),
                          ("total_charges", "total_charges_lu_sur")], paires)
        self.assertEqual([], orphelines)

    def test_une_provenance_ORPHELINE_se_nomme(self) -> None:
        paires, orphelines = paires_de_provenance({"fantome_source": "x"})
        self.assertEqual([], paires)
        self.assertEqual(["fantome_source"], orphelines)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
