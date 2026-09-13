# -*- coding: utf-8 -*-
"""Le registre ne s'annonce pas sous un commit qui n'est pas le sien.

`RM-2026-0139`. La regle de Brice, dans ses mots: *si c'est la source de
verite, elle doit etre commitee a chaque fois qu'elle est modifiee*. Elle
repond a ce que la collision avait appris: **un predicat correct sur des
copies correctes rend quand meme une mauvaise reponse quand deux fils ecrivent
dans la meme fenetre** - un numero verifie libre sur cinq branches l'etait
partout, parce que le commit d'un autre fil n'etait pas encore pousse.

**LE DEFAUT MESURE LE 2026-09-12.** `tools/gouvernail_depot.py` annonce
`registre : N items, commit <sha>` a cote d'un contenu lu **sur le disque**.
Quand le fichier porte des modifications non commitees - ce qui est le cas a
chaque lot, juste avant le commit - **les deux ne decrivent pas le meme etat,
et c'est la ligne de commit qui est lue**. C'est la forme exacte de
`RM-2026-0171`: un verdict pose a cote de ses faits, qui finit par les
contredire.

**CE N'EST PAS UNE INTERDICTION, ET C'EST VOULU.** Modifier le gouvernail
avant de le commiter est le cours normal d'un lot; une garde qui ferait
echouer la suite dans cet etat rendrait le travail impossible. Ce qui est pose
est une **declaration**: l'etat non commite se dit **la ou le commit
s'affiche**, pas dans un journal que personne ne relit.

**L'AXE.** Ce qui VARIE: la branche, le moment du lot, le nombre de fils qui
ecrivent. Ce qui reste INVARIANT: **un contenu lu sur le disque et un
identifiant de commit ne decrivent le meme etat que si le fichier est
propre.** **Hors des valeurs observees:** sans depot git, sans binaire git, la
fonction rend `etat-git-inconnu` - elle ne laisse jamais croire que la
verification a eu lieu.

**RESIDU:** la seconde moitie de l'item - *le refus qu'une branche autre que le
tronc porte une version divergente du registre* - n'est pas faite. Elle demande
un arbitrage: ce depot travaille sur des branches de chantier, et interdire la
divergence y interdirait le travail. La declaration ci-dessus ne la remplace
pas, elle la prepare en rendant l'ecart visible.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
OUTIL = DEPOT / "tools" / "gouvernail_depot.py"


def _charge():
    # **Il y avait ici un `raise unittest.SkipTest` sous `if spec is None`, et
    # c'etait du code MORT qui promettait un comportement impossible.** Sonde
    # du 2026-09-12: pour un fichier ABSENT, `spec_from_file_location` rend un
    # spec et non `None`, et c'est `exec_module` qui leve `FileNotFoundError`.
    # La branche ne pouvait donc jamais s'executer; elle laissait seulement
    # croire qu'un outil renomme retirerait ce fichier de la suite en silence.
    # L'echec est rendu explicite, et il reste BRUYANT: une erreur de
    # chargement fait rendre au lanceur son code d'echec de collecte.
    if not OUTIL.is_file():
        raise FileNotFoundError("outil du gouvernail introuvable: %s" % OUTIL)
    spec = importlib.util.spec_from_file_location("gouvernail_depot_etat", OUTIL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


G = _charge()


class L_ETAT_DU_FICHIER_EST_UN_ETAT_A_TROIS_VALEURS(unittest.TestCase):
    """Commite, modifie, ou *je n'ai pas pu savoir*. Jamais deux."""

    def test_les_trois_valeurs_sont_distinctes(self) -> None:
        self.assertEqual(
            3, len({G.ETAT_COMMITE, G.ETAT_MODIFIE, G.ETAT_INCONNU}),
            "deux etats confondus: un fichier dont on ignore l'etat se lirait "
            "comme un fichier propre")

    def test_l_etat_inconnu_n_est_pas_l_etat_commite(self) -> None:
        """Le coeur de la regle des trois etats: l'ignorance n'est pas une

        conformite, et c'est ici qu'elle compte, parce que la ligne affichee
        sert de preuve dans le gouvernail.
        """
        self.assertNotEqual(G.ETAT_INCONNU, G.ETAT_COMMITE)

    def test_l_etat_se_lit_sans_erreur_sur_ce_depot(self) -> None:
        self.assertIn(
            G.etat_du_gouvernail(),
            {G.ETAT_COMMITE, G.ETAT_MODIFIE, G.ETAT_INCONNU})


class LA_LIGNE_DE_MESURE_PORTE_L_ETAT(unittest.TestCase):
    """L'avertissement vit LA OU le commit s'affiche, pas ailleurs."""

    def test_un_fichier_modifie_fait_sortir_l_avertissement(self) -> None:
        registre = {"n": 3, "commit": "abc1234",
                    "etat_fichier": G.ETAT_MODIFIE,
                    "budget_octets": 1, "cap_cellule": 1, "lignes": []}
        ligne = self._ligne(registre)
        self.assertIn("ATTENTION", ligne)
        self.assertIn(G.ETAT_MODIFIE, ligne)
        self.assertIn("abc1234", ligne)

    def test_un_fichier_propre_n_ajoute_rien(self) -> None:
        """Temoin: la declaration n'est pas bavarde quand tout concorde."""
        registre = {"n": 3, "commit": "abc1234",
                    "etat_fichier": G.ETAT_COMMITE,
                    "budget_octets": 1, "cap_cellule": 1, "lignes": []}
        self.assertNotIn("ATTENTION", self._ligne(registre))

    def test_un_etat_ABSENT_avertit_aussi(self) -> None:
        """Une cle manquante ne doit pas se lire comme un fichier propre.

        C'est le piege symetrique: un registre construit par un chemin qui
        n'aurait pas pose la cle passerait pour commite.
        """
        registre = {"n": 3, "commit": "abc1234",
                    "budget_octets": 1, "cap_cellule": 1, "lignes": []}
        self.assertIn("ATTENTION", self._ligne(registre))

    @staticmethod
    def _ligne(registre: dict) -> str:
        rapport = G.Rapport()
        return G._mesure(rapport, registre).splitlines()[0]


def _cles_lues_par_mesure() -> set[str]:
    """Les cles que `_mesure` LIT sur son registre, decouvertes dans son code.

    Toute lecture `registre["k"]` ou `registre.get("k", ...)` a cle litterale,
    sur le parametre nomme `registre`. **Aucune liste ecrite ici**: le jour ou
    `_mesure` lira une cle de plus, la garde la verra sans qu'une ligne de ce
    fichier bouge.
    """
    arbre = ast.parse(OUTIL.read_text(encoding="utf-8"))
    fonction = next((n for n in arbre.body
                     if isinstance(n, ast.FunctionDef) and n.name == "_mesure"), None)
    if fonction is None:
        return set()
    cles: set[str] = set()
    for noeud in ast.walk(fonction):
        if (isinstance(noeud, ast.Subscript)
                and isinstance(noeud.value, ast.Name) and noeud.value.id == "registre"
                and isinstance(noeud.slice, ast.Constant)
                and isinstance(noeud.slice.value, str)):
            cles.add(noeud.slice.value)
        if (isinstance(noeud, ast.Call)
                and isinstance(noeud.func, ast.Attribute) and noeud.func.attr == "get"
                and isinstance(noeud.func.value, ast.Name)
                and noeud.func.value.id == "registre"
                and noeud.args and isinstance(noeud.args[0], ast.Constant)
                and isinstance(noeud.args[0].value, str)):
            cles.add(noeud.args[0].value)
    return cles


class LE_CABLAGE_ENTRE_GIT_ET_LE_REGISTRE_EST_PINCE(unittest.TestCase):
    """**Les six tests ci-dessus ne passent jamais par `construire()`.**

    Constat de l'instruction du 2026-09-12. Les trois de la classe du dessus
    fabriquent le registre A LA MAIN et n'appellent que le formateur; celui qui
    touche git appelle `etat_du_gouvernail()` hors de sa chaine et se contente
    d'une appartenance a l'ensemble des trois valeurs. Rien ne verifiait donc
    que la valeur lue par git **entre dans le registre reellement rendu**.

    Un `construire()` qui poserait `"etat_fichier": ETAT_COMMITE` en dur
    passerait ces six tests - et la ligne de mesure annoncerait un fichier
    propre a chaque lot, ce qui est exactement le defaut que l'item existe pour
    fermer. *Tester une fonction n'est pas tester son cablage*: `RM-2026-0171`
    l'a appris le meme jour sur le lanceur de la suite.

    **Pourquoi par SUBSTITUTION et non par egalite.** En integration continue
    l'arbre est propre, donc `etat_du_gouvernail()` rend `ETAT_COMMITE`, et une
    egalite entre la valeur rendue et celle du registre serait satisfaite par
    une constante `ETAT_COMMITE` codee en dur. L'egalite mesurerait le vide
    exactement la ou la garde doit tenir. Deux sentinelles ETRANGERES aux trois
    etats ne peuvent, elles, etre satisfaites par aucune constante.
    """

    SENTINELLES = ("SENTINELLE-GARDE-UN", "SENTINELLE-GARDE-DEUX")

    def _registre_avec(self, sentinelle: str) -> dict:
        """`construire()` rendu pendant que la fonction d'etat rend `sentinelle`.

        La substitution porte sur l'objet-module `G`, celui dans lequel
        `construire` resout ses globales. Le temoin de portee du test principal
        le verifie au lieu de le supposer: un patch pose sur un AUTRE objet
        rendrait la valeur reelle, et les deux sentinelles donneraient la meme.
        """
        vraie = G.etat_du_gouvernail
        G.etat_du_gouvernail = lambda: sentinelle
        try:
            registre, _, _ = G.construire()
        finally:
            G.etat_du_gouvernail = vraie
        return registre

    def test_la_valeur_d_etat_du_registre_VIENT_de_git_et_non_d_une_constante(self) -> None:
        un, deux = self.SENTINELLES
        etats = {G.ETAT_COMMITE, G.ETAT_MODIFIE, G.ETAT_INCONNU}
        self.assertNotIn(un, etats, "sentinelle mal choisie: elle coincide avec "
                                    "un etat, donc une constante la satisferait")
        self.assertNotIn(deux, etats)

        premier = self._registre_avec(un)
        second = self._registre_avec(deux)

        # La CLE d'etat n'est pas ecrite dans ce test: elle est trouvee comme
        # celle qui porte la sentinelle. Renommer la cle ne vide pas la garde.
        porteuses = [k for k, v in premier.items() if v == un]
        self.assertEqual(
            1, len(porteuses),
            "la valeur rendue par la fonction d'etat n'entre dans AUCUNE cle du "
            "registre - ou dans plusieurs: `construire()` ne recopie pas ce que "
            "git a mesure. Cles porteuses: %r" % porteuses)
        cle = porteuses[0]
        self.assertEqual(
            deux, second.get(cle),
            "les deux sentinelles ont rendu la MEME valeur de registre: "
            "`construire()` n'appelle pas la fonction d'etat, ou le test l'a "
            "substituee sur un autre objet que celui ou elle est resolue")

    def test_la_cle_d_etat_est_bien_une_cle_que_la_ligne_de_mesure_LIT(self) -> None:
        """Poser la valeur dans une cle que `_mesure` ne lit pas ne sert a rien:
        l'avertissement ne sortirait jamais."""
        registre = self._registre_avec(self.SENTINELLES[0])
        porteuses = [k for k, v in registre.items() if v == self.SENTINELLES[0]]
        self.assertTrue(porteuses, "aucune cle ne porte la sentinelle")
        self.assertIn(
            porteuses[0], _cles_lues_par_mesure(),
            "la valeur d'etat est rangee sous %r, que `_mesure` ne lit pas: la "
            "ligne affichee annoncerait un etat qu'on ne lui a jamais donne"
            % porteuses[0])

    def test_toute_cle_que_la_mesure_LIT_existe_dans_le_registre_RENDU(self) -> None:
        """Le registre passe par `ajuster_au_magasin` avant d'etre rendu, et
        certaines cles lues par `_mesure` - le budget, le plafond de cellule -
        n'existent qu'apres ce passage. Seul le registre RENDU fait foi."""
        lues = _cles_lues_par_mesure()
        registre, _, _ = G.construire()
        manquantes = sorted(k for k in lues if k not in registre)
        self.assertEqual(
            [], manquantes,
            "`_mesure` lit des cles que `construire()` ne rend pas: la ligne "
            "imprimee lirait une valeur par defaut, ou tomberait")

    def test_TEMOIN_la_lecture_de_l_arbre_trouve_des_cles(self) -> None:
        """Un jeu de cles vide est un symptome d'instrument, pas un resultat.

        Sans ce temoin, `_mesure` renomme, deplace dans une classe, ou lu par
        une variable intermediaire rendrait un ensemble vide - et la boucle du
        test precedent passerait au vert en ne mesurant rien.
        """
        lues = _cles_lues_par_mesure()
        self.assertGreaterEqual(
            len(lues), 2,
            "la lecture de l'arbre syntaxique de `_mesure` ne trouve presque "
            "aucune cle: la garde du dessus mesure le vide. Trouvees: %r"
            % sorted(lues))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
