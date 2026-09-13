# -*- coding: utf-8 -*-
"""La file derive du gouvernail, se plafonne, et ne ferme rien toute seule.

Consigne de Brice du 2026-09-09, apres lecture des pratiques du metier:
*mets en place ces outils*, et *pour la file, c'est toi qui connais les bons
standards*.

**Le defaut mesure ce jour-la:** taux d'arrivee sur taux de fermeture a
**4,8 pour 1**. Un registre dans cet etat n'est plus un outil de pilotage, il
est un journal - et s'en servir pour savoir ou l'on en est donne un chiffre qui
ne veut rien dire.

**Ce que ces tests gardent en priorite, et c'est la lecon du 2026-09-10.** Un
plafond est un **maximum**. Une garde ecrite le matin meme exigeait
`len(mesurees) > 10` sur un ensemble qui ne contient que les P0 encore `ACTIF`:
elle a echoue **le jour ou un chantier a abouti**. Une garde qui exige que le
backlog reste plein est une garde a l'envers, et il y a ici un test dont c'est
le seul objet.

**Ce qu'ils gardent ensuite:** que l'outil ne fabrique pas un comptage
concurrent. Le document porte des lignes `RM-*` dans **quatre sections**; les
additionner donnait 185 items la ou le registre actif en porte 161.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
OUTIL = DEPOT / "tools" / "file_travail.py"


def _charger():
    spec = importlib.util.spec_from_file_location("file_travail", OUTIL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


F = _charger()

_BS = chr(92)


def _ligne(item: str, statut: str, priorite: str = "P1",
           analyse: str = "analyse", date_maj: str = "2026-09-10") -> str:
    return ("| `%s` | titre | domaine | `%s` | %s | owner | origine | %s | "
            "chantier | trace | %s |" % (item, statut, priorite, analyse, date_maj))


def _document(lignes: list[str], titre: str = "## Registre actif par identifiant") -> str:
    return "\n".join([
        "# Gouvernail",
        "",
        "## Hors file d'execution",
        "",
        _ligne("RM-2026-9001", "ACTIF"),   # dans une AUTRE section: ne compte pas
        "",
        titre,
        "",
        "| Item | Titre | Domaine | Statut | Prio | Owner | Origine | Analyse | CH | Trace | MAJ |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
        *lignes,
        "",
        "## Temps humain explicite",
        "",
        _ligne("RM-2026-9002", "ACTIF"),   # encore une autre: ne compte pas
    ])


class _SurUnGouvernailJetable(unittest.TestCase):
    def _ecrire(self, texte: str) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        chemin = Path(temp.name) / "gouvernail.md"
        chemin.write_text(texte, encoding="utf-8")
        return chemin


class L_OUTIL_NE_FABRIQUE_PAS_UN_COMPTAGE_CONCURRENT(_SurUnGouvernailJetable):
    """Quatre sections portent des lignes `RM-*`. Une seule est le registre."""

    def test_seule_la_section_du_registre_actif_est_lue(self) -> None:
        chemin = self._ecrire(_document([
            _ligne("RM-2026-0001", "ACTIF"),
            _ligne("RM-2026-0002", "INTEGRE"),
        ]))
        items = F.lire_items(chemin)
        self.assertEqual(["RM-2026-0001", "RM-2026-0002"],
                         [i["id"] for i in items])

    def test_si_la_section_manque_l_outil_REFUSE_au_lieu_de_compter_le_reste(self) -> None:
        """Rabattre sur le document entier donnerait un chiffre credible et faux.

        C'est ce qui s'est produit a la premiere ecriture: 185 items annonces
        la ou le registre en porte 161.
        """
        chemin = self._ecrire(_document(
            [_ligne("RM-2026-0001", "ACTIF")], titre="## Un autre titre"))
        with self.assertRaises(F.GouvernailIllisible) as leve:
            F.lire_items(chemin)
        self.assertIn("Registre actif par identifiant", str(leve.exception))
        self.assertIn("comptage concurrent", str(leve.exception))


class UNE_CELLULE_QUI_CITE_UNE_BARRE_NE_CREE_PAS_DE_COLONNE(_SurUnGouvernailJetable):
    """Le piege qui m'a donne deux mesures fausses le 2026-09-10.

    Une cellule d'analyse cite parfois un tableau chiffre - `35 \\| 29 \\| -6` -
    avec ses barres echappees. Un decoupage qui ignore l'echappement rend une
    cellule coupee et parfaitement credible.
    """

    def test_le_TITRE_qui_cite_une_barre_n_est_pas_tronque(self) -> None:
        """**Ce test a du etre refait: le premier ne gardait rien.**

        Il verifiait que le STATUT restait lu malgre une barre echappee. Or le
        statut est trouve par balayage de valeur sur toutes les cellules: un
        decoupage naif en produit davantage, et la valeur s'y trouve quand
        meme. La mutation - remplacer le separateur par une barre nue - passait
        au vert. Le test mesurait quelque chose de vrai qui ne dependait pas de
        ce qu'il pretendait garder.

        Ce qui depend vraiment de l'echappement, c'est la cellule lue **par sa
        position**: le titre. Avec une barre nue, il est coupe a la premiere
        barre citee, et le resultat reste parfaitement credible.
        """
        titre_cite = "un ecart de 35 " + _BS + "| 29 " + _BS + "| -6 sur la ligne"
        ligne = ("| `RM-2026-0001` | %s | domaine | `A_ARBITRER` | P1 | owner | "
                 "origine | analyse | chantier | trace | 2026-09-10 |" % titre_cite)
        chemin = self._ecrire(_document([ligne]))
        items = F.lire_items(chemin)
        self.assertEqual(1, len(items))
        self.assertIn("-6 sur la ligne", items[0]["titre"],
                      "le titre est coupe a la premiere barre citee")
        self.assertEqual("A_ARBITRER", items[0]["statut"])
        self.assertEqual(F.ETAT_DECISION, items[0]["etat"])


class LES_PLAFONDS_SONT_DES_MAXIMA_JAMAIS_DES_MINIMA(_SurUnGouvernailJetable):
    """Le test qui existe a cause d'une garde a l'envers ecrite ce matin."""

    def test_un_registre_PRESQUE_VIDE_ne_declenche_rien(self) -> None:
        """Une garde qui rougit quand le travail avance est une garde a l'envers.

        `test_les_references_survivent_a_la_coupure` exigeait `> 10` sur un
        ensemble qui ne contient que les P0 encore `ACTIF`, et a echoue le jour
        ou un chantier a abouti. Ici, vider le registre doit etre **silencieux**.
        """
        chemin = self._ecrire(_document([_ligne("RM-2026-0001", "INTEGRE")]))
        etat = F.etat_de_la_file(F.lire_items(chemin))
        self.assertEqual([], etat["depassements"])
        self.assertEqual(0, len(etat["engages"]))
        self.assertEqual(1, etat["clos"])

    def test_un_registre_ENTIEREMENT_clos_ne_declenche_rien_non_plus(self) -> None:
        chemin = self._ecrire(_document([
            _ligne("RM-2026-000%d" % n, "INTEGRE") for n in range(1, 6)]))
        etat = F.etat_de_la_file(F.lire_items(chemin))
        self.assertEqual([], etat["depassements"])

    def test_le_plafond_d_engagement_se_declenche_AU_DESSUS_seulement(self) -> None:
        for combien, attendu in ((3, 0), (4, 1)):
            with self.subTest(engages=combien):
                chemin = self._ecrire(_document([
                    _ligne("RM-2026-00%02d" % n, "ACTIF") for n in range(1, combien + 1)]))
                etat = F.etat_de_la_file(F.lire_items(chemin))
                self.assertEqual(attendu, len(etat["depassements"]))


class LES_QUATRE_ETATS_NE_SE_RECOUVRENT_PAS(_SurUnGouvernailJetable):
    """Chaque item est dans exactement un etat, et le total se conserve."""

    def setUp(self) -> None:
        self.chemin = self._ecrire(_document([
            _ligne("RM-2026-0001", "ACTIF"),
            _ligne("RM-2026-0002", "A_ARBITRER"),
            _ligne("RM-2026-0003", "EN_ATTENTE_USER"),
            _ligne("RM-2026-0004", "PRET_A_INTEGRER"),
            _ligne("RM-2026-0005", "INTEGRE"),
            _ligne("RM-2026-0006", "ABANDONNE"),
        ]))

    def test_le_total_se_conserve(self) -> None:
        etat = F.etat_de_la_file(F.lire_items(self.chemin))
        somme = (len(etat["engages"]) + len(etat["decisions"])
                 + etat["journal"] + etat["clos"])
        self.assertEqual(etat["items"], somme,
                         "un item est compte deux fois, ou pas du tout")

    def test_PRET_A_INTEGRER_n_est_PAS_du_travail_engage(self) -> None:
        """Du travail fini qui attend une integration n'occupe pas la file."""
        etat = F.etat_de_la_file(F.lire_items(self.chemin))
        self.assertNotIn("RM-2026-0004", etat["engages"])

    def test_les_deux_attentes_humaines_comptent_ensemble(self) -> None:
        etat = F.etat_de_la_file(F.lire_items(self.chemin))
        self.assertEqual(["RM-2026-0002", "RM-2026-0003"], etat["decisions"])

    def test_un_statut_inconnu_tombe_au_JOURNAL_et_non_dans_la_file(self) -> None:
        """Hors des valeurs observees, on degrade vers l'etat qui n'engage rien.

        Ranger un statut inconnu parmi les engages gonflerait la file d'items
        dont personne ne s'occupe - et la file cesserait de dire ce qu'elle dit.
        """
        chemin = self._ecrire(_document([_ligne("RM-2026-0009", "STATUT_DE_DEMAIN")]))
        etat = F.etat_de_la_file(F.lire_items(chemin))
        self.assertEqual([], etat["engages"])
        self.assertEqual(1, etat["journal"])


class LA_POLITIQUE_D_AGE_NOMME_ET_NE_FERME_RIEN(_SurUnGouvernailJetable):
    """Fermer est une decision; un outil qui ferme seul se substitue a l'humain."""

    def setUp(self) -> None:
        self.chemin = self._ecrire(_document([
            _ligne("RM-2026-0001", "PRET_A_INTEGRER", date_maj="2026-01-01"),
            _ligne("RM-2026-0002", "ACTIF", date_maj="2026-09-09"),
            _ligne("RM-2026-0003", "INTEGRE", date_maj="2026-01-01"),
        ]))

    def test_le_dormant_est_NOMME(self) -> None:
        etat = F.etat_de_la_file(F.lire_items(self.chemin),
                                 aujourdhui=date(2026, 9, 10))
        self.assertEqual(["RM-2026-0001"], [d["id"] for d in etat["dormants"]])

    def test_un_item_CLOS_n_est_jamais_dormant(self) -> None:
        """Il est deja tranche: le reveiller n'a pas de sens."""
        etat = F.etat_de_la_file(F.lire_items(self.chemin),
                                 aujourdhui=date(2026, 9, 10))
        self.assertNotIn("RM-2026-0003", [d["id"] for d in etat["dormants"]])

    def test_le_statut_du_dormant_n_est_PAS_change(self) -> None:
        items = F.lire_items(self.chemin)
        F.etat_de_la_file(items, aujourdhui=date(2026, 9, 10))
        self.assertEqual("PRET_A_INTEGRER", items[0]["statut"])


class TROIS_CODES_DE_SORTIE_ET_LE_TROISIEME_N_EST_PAS_UN_FEU_VERT(
        _SurUnGouvernailJetable):
    """*Pas regarde* ne se confond jamais avec *rien a signaler*."""

    def test_gouvernail_absent_rend_2(self) -> None:
        manquant = Path(tempfile.gettempdir()) / "ce-fichier-n-existe-pas-file.md"
        ancien = F.GOUVERNAIL
        F.GOUVERNAIL = manquant
        try:
            self.assertEqual(2, F.main([]))
        finally:
            F.GOUVERNAIL = ancien

    def test_plafonds_tenus_rend_0_et_depasses_rend_1(self) -> None:
        for lignes, attendu in (
            ([_ligne("RM-2026-0001", "ACTIF")], 0),
            ([_ligne("RM-2026-00%02d" % n, "ACTIF") for n in range(1, 6)], 1),
        ):
            with self.subTest(attendu=attendu):
                chemin = self._ecrire(_document(lignes))
                ancien = F.GOUVERNAIL
                F.GOUVERNAIL = chemin
                try:
                    self.assertEqual(attendu, F.main(["--json"]))
                finally:
                    F.GOUVERNAIL = ancien


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
