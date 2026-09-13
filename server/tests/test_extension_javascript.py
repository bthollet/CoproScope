"""Le JavaScript du plugin, eprouve et confronte au lecteur Python.

======================================================================
Ce que ce fichier ferme comme trou
======================================================================

Jusqu'ici, tout ce qui etait teste automatiquement etait ecrit en Python. Le
JavaScript du plugin - celui qui lit reellement la page chez l'utilisateur -
n'avait ete eprouve qu'une fois, a la main, injecte dans une page reelle. Une
verification qui ne se rejoue pas ne protege de rien: elle dit que le code
marchait ce jour-la.

Ces tests l'executent sous Node, sur des gabarits controles, a chaque
execution de la suite.

======================================================================
Et surtout: ils confrontent les deux implantations
======================================================================

Le plugin lit la page, CoproScope raisonne. Deux endroits, deux langages, et un
risque repete tout au long du lot: **deux implantations de la meme logique
divergent toujours, et la divergence se voit le jour ou l'on en a le plus
besoin**. Ici, elle se verrait au recoupement entre voisins, sous la forme d'un
zero de concordance que deux personnes liraient comme un desaccord entre elles.

Chaque gabarit passe donc dans les deux lecteurs, et les resultats doivent
coincider - meme decoupage en rubriques, memes groupes, memes libelles.

Les gabarits reproduisent les pieges **mesures** sur un extranet en service le
2026-09-04, pas des cas imagines: huit libelles repetes sur cinq exercices,
deux liens par piece, des lignes de sous-total a quatre cellules, des depenses
avant tout en-tete.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from coproscope.modules._extranet_adaptateur import PROFIL_COPRODIRECTE, lire_index
from coproscope.modules._extranet_depenses import lire_depenses
from coproscope.modules._extranet_echange import empreinte, exporter, temoin_sel
from coproscope.modules._extranet_releve import convertir

RACINE = Path(__file__).resolve().parents[2] / "clients" / "extension-navigateur"
EXECUTEUR = RACINE / "tests" / "executer.mjs"
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"


def _piece(groupe: str, libelle: str) -> str:
    """Une piece telle que l'editeur la sert: DEUX liens, une icone et un libelle."""
    return (
        "<tr class='just'>"
        "<td class='tdPdf'><a class='pj pdf' href='documents/ICONE'></a></td>"
        f"<td class='pl2'><a href='documents/{libelle}'>{libelle}</a></td>"
        "</tr>"
    )


def _groupe(titre: str) -> str:
    return f"<tr><td colspan='2'>{titre}</td></tr>"


def _bloc(code: str, contenu: str) -> str:
    return (
        f"<div class='{code} mt3'><table class='tableDoc'><tbody>"
        f"{contenu}</tbody></table></div>"
    )


def _page(blocs: str, pagination: bool = False) -> str:
    nav = "<div class='pagination'><span>suivant</span></div>" if pagination else ""
    return f"<html><body><div id='documents'>{blocs}{nav}</div></body></html>"


def _depense(cells: list[str], facture: bool = True) -> str:
    lien = "<a class='pj pdf' href='documents/F'></a>" if facture else ""
    tds = "".join(f"<td>{c}</td>" for c in cells)
    return f"<tr class='just'>{tds}<td>{lien}</td></tr>"


#: Le secret partage des gabarits. Il ne protege rien ici - il sert a faire
#: EXISTER la branche export du harnais, restee morte sous test jusqu'au
#: 2026-09-07, ce qui a laisse passer trois constructions de cle divergentes.
SEL = "sel-de-gabarit-sans-valeur"

#: Les quatre gabarits, chacun portant un piege reellement mesure.
GABARITS = {
    "index_avec_exercices_repetes": {
        "html": _page(
            _bloc(
                "ARR",
                _groupe("Au 31/12/2025") + _piece("", "Annexe 1") + _piece("", "Annexe 2")
                + _groupe("Au 31/12/2024") + _piece("", "Annexe 1") + _piece("", "Annexe 2"),
            )
            + _bloc("CON", _piece("", "Mandat"))
        ),
        "chemin": "/espace-copropriete/documents",
        "sel": SEL,
    },
    "index_pagine": {
        "html": _page(_bloc("ARR", _piece("", "Annexe 1")), pagination=True),
        "chemin": "/espace-copropriete/documents",
        "sel": SEL,
    },
    "depenses_avec_totaux": {
        "html": (
            "<html><body><table><tbody>"
            + "<tr><td colspan='2'>CHARGES GENERALES</td></tr>"
            + _depense(["12/03/2025", "Entretien", "Prestation", "120,00"])
            + "<tr class='tot'><td></td><td>TOTAL ENTRETIEN</td><td></td><td>120,00</td></tr>"
            + _depense(["02/04/2025", "Eau", "Releve", "60,00"])
            + "<tr><td colspan='2'>ASCENSEUR 23</td></tr>"
            + _depense(["02/02/2025", "Maintenance", "Contrat", "900,00"], facture=False)
            + "</tbody></table></body></html>"
        ),
        "chemin": "/espace-copropriete/depenses",
        "sel": SEL,
    },
    "depenses_avant_tout_en_tete": {
        "html": (
            "<html><body><table><tbody>"
            + _depense(["01/01/2025", "Divers", "Avant groupe", "10,00"])
            + "<tr><td colspan='2'>CHARGES GENERALES</td></tr>"
            + _depense(["05/01/2025", "Eau", "Apres groupe", "20,00"])
            + "</tbody></table></body></html>"
        ),
        "chemin": "/espace-copropriete/depenses",
        "sel": SEL,
    },
}


def _executer_js() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        chemin = Path(tmp) / "gabarits.json"
        chemin.write_text(json.dumps(GABARITS), encoding="utf-8")
        rendu = subprocess.run(
            [NODE, str(EXECUTEUR), str(chemin)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
    if rendu.returncode != 0:
        raise AssertionError(f"executer.mjs a echoue:\n{rendu.stderr[:2000]}")
    return json.loads(rendu.stdout)


def _emplacements_python(nom: str) -> list[str]:
    """Le gabarit lu **directement** par le lecteur Python."""
    g = GABARITS[nom]
    if "depenses" in g["chemin"]:
        lu = lire_depenses(g["html"], PROFIL_COPRODIRECTE, "P")
    else:
        lu = lire_index(g["html"], PROFIL_COPRODIRECTE, "P")
    return [p["emplacement"] for p in lu["pieces"]]


def _emplacements_via_plugin(releve_brut: dict) -> list[str]:
    """Le meme gabarit, lu par le plugin, puis converti par la chaine Python.

    C'est le chemin reel du produit: le plugin rend une structure neutre, et
    CoproScope en tire les cles. Comparer ce bout-la a la lecture directe
    compare ce qui compte - la cle qui servira aux verdicts - et non deux mises
    en forme, ce qui ne prouverait rien.
    """
    converti = convertir(releve_brut, PROFIL_COPRODIRECTE, "P")
    return [p["emplacement"] for p in converti["pieces"]]


@unittest.skipUnless(EXECUTEUR.exists(), "extension absente de cet arbre")
@unittest.skipUnless(Path(NODE).exists(), "Node.js absent de ce poste")
class JavaScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _executer_js()

    # ---------------------------------------------------------------- index

    def test_deux_liens_par_piece_ne_font_qu_une_piece(self) -> None:
        """Mesure: 230 liens pour 115 pieces sur l'index reel."""
        self.assertEqual(len(self.js["index_avec_exercices_repetes"]["pieces"]), 5)

    def test_le_groupe_distingue_deux_exercices_homonymes(self) -> None:
        """Mesure: 32 collisions sur 115 si l'on prend le libelle pour cle."""
        pieces = self.js["index_avec_exercices_repetes"]["pieces"]
        libelles = {p["libelle"] for p in pieces}
        cles = {(p["rubrique"], p["groupe"], p["libelle"]) for p in pieces}
        self.assertEqual(len(libelles), 3)
        self.assertEqual(len(cles), 5)

    def test_les_rubriques_absentes_restent_non_explorees(self) -> None:
        releve = self.js["index_avec_exercices_repetes"]
        self.assertEqual(releve["rubriques_parcourues"], 2)
        self.assertIn("ASS", releve["non_explorees"])

    def test_une_pagination_interdit_de_conclure_a_une_liste_complete(self) -> None:
        self.assertEqual(self.js["index_pagine"]["cloture"], "AUCUNE")
        self.assertEqual(self.js["index_avec_exercices_repetes"]["cloture"], "CONSTATEE")

    # -------------------------------------------------------------- depenses

    def test_un_sous_total_ne_devient_pas_une_cle_de_charges(self) -> None:
        """Le defaut le plus grave du lot, tenu ici cote JavaScript.

        Une ligne de total prise pour un en-tete faisait passer 42 cles a 340,
        et rattachait les depenses suivantes a une cle **portant un montant** -
        donc changeante a chaque passage, donc un retrait et un ajout pour
        chaque piece du groupe.
        """
        cles = dict(self.js["depenses_avec_totaux"]["lignes_par_cle"])
        self.assertEqual(set(cles), {"CHARGES GENERALES", "ASCENSEUR 23"})

    def test_une_depense_avant_tout_en_tete_recoit_une_cle_nommee(self) -> None:
        cles = dict(self.js["depenses_avant_tout_en_tete"]["lignes_par_cle"])
        self.assertIn("(hors groupe)", cles)

    def test_seules_les_lignes_avec_facture_sont_des_pieces(self) -> None:
        pieces = self.js["depenses_avec_totaux"]["pieces"]
        self.assertEqual(len(pieces), 2)
        self.assertTrue(all(p["rubrique"] == "CHARGES GENERALES" for p in pieces))

    # ----------------------------------------------------------- conformite

    def test_les_deux_lecteurs_rendent_la_meme_chose(self) -> None:
        """Le test qui compte le plus de ce fichier.

        Si le plugin et l'application cessaient de lire une page de la meme
        facon, le defaut ne paraitrait qu'au recoupement entre voisins - sous la
        forme d'un zero de concordance, que deux personnes liraient comme un
        desaccord entre elles.
        """
        for nom in GABARITS:
            with self.subTest(gabarit=nom):
                self.assertEqual(
                    _emplacements_via_plugin(self.js[nom]["releve_brut"]),
                    _emplacements_python(nom),
                    f"les deux lecteurs divergent sur le gabarit {nom!r}",
                )

    def test_l_etage_des_noms_compte_ce_qu_il_a_obtenu(self) -> None:
        noms = self.js["index_avec_exercices_repetes"]["noms"]
        self.assertEqual(noms["pieces"], 5)
        self.assertEqual(noms["avec_nom"], 0)
        self.assertEqual(noms["sans_nom"], 5)
        self.assertEqual(noms["couverture"], 0)

    # ------------------------------------------------- l'export vers le voisin

    def _export_python(self, nom: str) -> dict:
        """Ce que la chaine Python transmettrait, sur le meme releve."""

        converti = convertir(self.js[nom]["releve_brut"], PROFIL_COPRODIRECTE, "P")
        return exporter(
            converti["passage"],
            converti["rubriques"],
            converti["pieces"],
            sel=SEL,
            observateur="test",
        )

    def test_le_temoin_de_sel_est_le_meme_des_deux_cotes(self) -> None:
        """Sinon deux voisins liraient *vous n'employez pas le meme secret*
        alors qu'ils l'emploient."""
        for nom in GABARITS:
            with self.subTest(gabarit=nom):
                self.assertEqual(
                    self.js[nom]["export"]["temoin_sel"], temoin_sel(SEL)
                )

    def test_les_empreintes_du_plugin_et_de_python_coincident(self) -> None:
        """Le test qui manquait, et l'absence qui a laisse passer le defaut.

        Aucun gabarit ne portait de sel jusqu'au 2026-09-07, donc la branche
        export du harnais ne s'executait jamais. Trois constructions de cle
        coexistaient pour une ligne de depenses - `_extranet_releve` joignait
        toutes les colonnes, `veille.js` en faisait trois composantes,
        `journal.js` comptait la premiere colonne DEUX FOIS - et rien ne le
        disait.

        Le defaut n'aurait pas produit d'erreur: il aurait produit **zero
        concordance** entre un export d'extension et un export CoproScope sur
        les lignes de depenses, c'est-a-dire exactement la matiere que le
        voisin qui suit les factures met en commun. Deux personnes auraient lu
        ce zero comme un desaccord entre elles.
        """
        for nom in GABARITS:
            with self.subTest(gabarit=nom):
                attendu = [
                    p["emp_emplacement"]
                    for p in self._export_python(nom)["pieces"]
                    if p.get("emp_emplacement")
                ]
                obtenu = [e for e in self.js[nom]["export"]["empreintes"] if e]
                self.assertEqual(
                    obtenu,
                    attendu,
                    f"les empreintes divergent sur le gabarit {nom!r}",
                )

    def test_une_empreinte_ne_se_calcule_pas_sans_sel(self) -> None:
        with self.assertRaises(ValueError):
            empreinte("Annexe 1", "")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
