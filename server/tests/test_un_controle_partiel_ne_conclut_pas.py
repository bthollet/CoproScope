# -*- coding: utf-8 -*-
"""Un controle de confidentialite qui n'a pas tout lu ne rend pas un verdict.

`RM-2026-0146`, lot du 2026-09-11. **L'item disait autre chose, et il disait
faux** - il annoncait qu'une sortie d'extraction de 72 Mo pour un tableur de
37,8 Mo revelait un defaut de lecteur. Mesure: ce fichier a un taux d'expansion
de **x1,87**, quand deux autres tableurs du meme corpus font **x2,43** et
**x2,13**. Il n'est pas mal lu, il est gros a la source. Et ses *« dix pages
declaree »* sont dix FEUILLES de classeur, pas dix pages de papier.

**Ce que la mesure a trouve a la place est plus grave.** Le classement de
diffusabilite - celui qui decide si une piece peut sortir et sous quelle forme -
est rendu a partir d'un ECHANTILLON, par trois plafonds superposes dont aucun
ne laissait de trace:

1. `_read_pdf_text` s'arretait a `min(page_count, 10)`;
2. `_read_sample` tronquait a 50 000 caracteres;
3. `build_access_policy` retronquait a 50 000 caracteres, meme quand
   l'appelant lui passait tout.

**Le cout, mesure par le point d'entree reel** - `_read_sample`, le lecteur que
`screen_existing` appelle - sur une instance VIDE reabsorbant 858 pieces
sources. Sur les **64 PDF de plus de dix pages**: **19 portent au moins une
categorie de donnee personnelle absente de l'echantillon**, dont **12 une
categorie CRITIQUE**. Deux documents de 140 et 143 pages sont classes sur
**3,6 %** de leur texte et laissent hors du verdict `HEALTH`, `IBAN`, `IMPAID`,
`CONTENTIOUS`, `CONFIDENTIAL`, `LOT`, `NEGOTIATION`. **Quatre etaient declares
`nominative` sans relecture humaine exigee** alors qu'ils relevent de
l'article 9 du RGPD.

**Une premiere mesure a ete refutee par la seconde, et il faut le dire.** Le
premier passage comparait *« ce que le scan lit »* a *« tout le texte »* et
trouvait 12 verdicts changeants. Il etait faux: `build_access_policy` retronque
a 50 000 caracteres, donc le second terme n'etait pas *tout le texte* mais un
autre echantillon du meme debut. La mesure refaite confronte les detecteurs au
document entier, par tranches - et trouve 19, pas 12.

**L'AXE.** Ce qui VARIE: la longueur des pieces, leur format, la valeur des
plafonds. Ce qui reste INVARIANT: **un controle qui n'a pas lu tout son objet
ne peut pas rendre le meme « rien trouve » qu'un controle complet.**

**Ce lot ne remonte aucun plafond**, et c'est deliberé: passer dix a cinquante
pages deplacerait le defaut au document de cinquante et une pages, c'est-a-dire
coderait une modalite. Les plafonds restent; ils cessent d'etre muets.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from coproscope.core._privacy_couverture import (
    CHAMP,
    COMPLETE,
    INDETERMINEE,
    PARTIELLE,
    conclut,
    couverture_lue,
    la_plus_prudente,
    lisible,
)
from coproscope.core.privacy import (
    POLICY_FIELDS,
    SCREENING_FIELDS,
    build_access_policy,
)

DEPOT = Path(__file__).resolve().parents[2]
SCAN = (DEPOT / "server/src/coproscope/modules/_privacyops_parts"
        / "01_scan_helpers.py")

BASE = {
    "doc_id": "DOC-TEST",
    "original_path": "staging/piece.pdf",
    "extension": "pdf",
    "document_type": "",
}


class LES_TROIS_ETATS_SE_DISTINGUENT(unittest.TestCase):
    """Et le troisieme n'est jamais un feu vert."""

    def test_tout_lu_conclut(self) -> None:
        self.assertEqual(COMPLETE, couverture_lue(1200, 1200))
        self.assertTrue(conclut(COMPLETE))

    def test_une_partie_lue_ne_conclut_pas(self) -> None:
        self.assertEqual(PARTIELLE, couverture_lue(500, 1200))
        self.assertFalse(conclut(PARTIELLE))

    def test_ne_pas_savoir_ce_qu_on_a_lu_ne_conclut_pas_davantage(self) -> None:
        """`INDETERMINEE` n'est pas un synonyme de `COMPLETE`."""
        self.assertEqual(INDETERMINEE, couverture_lue(500, None))
        self.assertFalse(conclut(INDETERMINEE))

    def test_rien_a_lire_n_est_pas_une_troncature(self) -> None:
        """Un verdict rendu sans texte - l'inventaire le fait - ne subit
        aucune coupe. Le confondre avec une troncature mettrait les 858 pieces
        en relecture des le premier passage, et un signal qui se leve partout
        finit eteint."""
        self.assertEqual(COMPLETE, couverture_lue(0, 0))

    def test_les_trois_etats_se_disent_a_un_humain(self) -> None:
        for etat in (COMPLETE, PARTIELLE, INDETERMINEE):
            with self.subTest(etat=etat):
                self.assertTrue(lisible(etat).strip())
        self.assertNotEqual(lisible(COMPLETE), lisible(PARTIELLE))


class LA_COMPOSITION_RETIENT_LE_PLUS_PRUDENT(unittest.TestCase):
    """Une lecture complete en aval ne repare pas une troncature en amont."""

    def test_partielle_l_emporte_sur_complete(self) -> None:
        self.assertEqual(PARTIELLE, la_plus_prudente(COMPLETE, PARTIELLE))
        self.assertEqual(PARTIELLE, la_plus_prudente(PARTIELLE, COMPLETE))

    def test_partielle_l_emporte_sur_indeterminee(self) -> None:
        self.assertEqual(PARTIELLE, la_plus_prudente(INDETERMINEE, PARTIELLE))

    def test_indeterminee_l_emporte_sur_complete(self) -> None:
        """Ne pas savoir est moins bon que savoir qu'on a tout lu."""
        self.assertEqual(INDETERMINEE, la_plus_prudente(COMPLETE, INDETERMINEE))

    def test_un_etat_inconnu_ne_vaut_pas_une_lecture_complete(self) -> None:
        self.assertEqual(INDETERMINEE, la_plus_prudente("", "n'importe quoi"))


class LE_VERDICT_PORTE_SA_RESERVE(unittest.TestCase):
    """Le coeur du lot: la troncature atteint le classement de diffusabilite."""

    def test_une_lecture_tronquee_exige_la_relecture_humaine(self) -> None:
        verdict = build_access_policy(dict(BASE, **{CHAMP: PARTIELLE}), "texte")
        self.assertEqual(PARTIELLE, verdict[CHAMP])
        self.assertEqual("YES", verdict["review_required"])
        self.assertEqual("A_REVOIR", verdict["privacy_review_status"])

    def test_une_lecture_complete_ne_l_exige_pas_par_elle_meme(self) -> None:
        """Sans quoi la garde se declencherait partout et ne designerait rien."""
        verdict = build_access_policy(dict(BASE, **{CHAMP: COMPLETE}), "texte")
        self.assertEqual(COMPLETE, verdict[CHAMP])
        self.assertEqual("", verdict["review_required"])

    def test_le_VERDICT_tronque_lui_meme_ce_qu_on_lui_donne_et_le_dit(self) -> None:
        """**Le troisieme plafond, le plus discret.** Meme avec une couverture
        `COMPLETE` declaree en amont, confronter 60 000 caracteres a un
        detecteur qui n'en lit que 50 000 est une lecture partielle."""
        verdict = build_access_policy(dict(BASE, **{CHAMP: COMPLETE}), "a" * 60000)
        self.assertEqual(PARTIELLE, verdict[CHAMP])
        self.assertEqual("YES", verdict["review_required"])

    def test_l_exigence_ne_depend_pas_de_ce_qui_a_ete_trouve(self) -> None:
        """C'est tout son interet: un document dont l'echantillon revele deja
        des noms peut porter un IBAN trente pages plus loin. Le verdict reste
        ouvert dans les deux cas."""
        for texte in ("rien de notable", "contact: jean.exemple@exemple.fr"):
            with self.subTest(texte=texte[:20]):
                verdict = build_access_policy(
                    dict(BASE, **{CHAMP: PARTIELLE}), texte)
                self.assertEqual("YES", verdict["review_required"])

    def test_un_appelant_muet_obtient_INDETERMINEE_et_non_COMPLETE(self) -> None:
        """Trois des quatre chemins qui appellent ce verdict ne declarent
        encore rien. Ils ne doivent pas passer pour des lectures completes."""
        verdict = build_access_policy(dict(BASE), "texte")
        self.assertEqual(INDETERMINEE, verdict[CHAMP])


class LA_COUVERTURE_ATTEINT_LES_REGISTRES(unittest.TestCase):
    """Un etat qui ne s'ecrit nulle part n'est pas mesurable."""

    def test_le_champ_est_une_colonne_de_politique(self) -> None:
        self.assertIn(CHAMP, POLICY_FIELDS)

    def test_le_champ_est_une_colonne_de_screening(self) -> None:
        self.assertIn(CHAMP, SCREENING_FIELDS)


class LES_LECTEURS_DISENT_CE_QU_ILS_ONT_LAISSE(unittest.TestCase):
    """**Chaque lecteur connait sa troncature; aucun ne la transmettait.**"""

    def _lecteurs(self) -> dict[str, ast.FunctionDef]:
        arbre = ast.parse(SCAN.read_text(encoding="utf-8"))
        return {
            n.name: n for n in arbre.body
            if isinstance(n, ast.FunctionDef) and n.name.startswith("_read_")
        }

    def test_chaque_lecteur_rend_un_couple_texte_et_couverture(self) -> None:
        for nom, noeud in self._lecteurs().items():
            with self.subTest(lecteur=nom):
                rendu = ast.unparse(noeud.returns) if noeud.returns else ""
                self.assertIn(
                    "tuple[str, str]", rendu,
                    "%s rend un texte nu: sa troncature se perd en chemin" % nom)

    def test_aucun_lecteur_ne_rend_un_texte_vide_comme_lecture_complete(self) -> None:
        """Un format inconnu, un fichier illisible: zero caractere lu sur un
        document qui existe est l'etat `PARTIELLE`, jamais un silence."""
        for nom, noeud in self._lecteurs().items():
            with self.subTest(lecteur=nom):
                for retour in [n for n in ast.walk(noeud)
                               if isinstance(n, ast.Return) and n.value is not None]:
                    rendu = ast.unparse(retour.value)
                    if rendu.startswith("('',") or rendu.startswith("(''"):
                        self.assertIn(
                            "PARTIELLE", rendu,
                            "%s rend un texte vide sans dire que rien n'a "
                            "ete lu" % nom)

    def test_le_plafond_de_dix_pages_est_TOUJOURS_la_et_c_est_voulu(self) -> None:
        """**Cette garde protege une DECISION, pas un defaut.**

        Le remonter a cinquante deplacerait le probleme au document de
        cinquante et une pages: une modalite a la place d'un axe. Si un jour
        le lecteur devient capable de tout lire, ce test doit etre retire
        SCIEMMENT, avec la mesure qui le justifie - et non contourne.
        """
        source = SCAN.read_text(encoding="utf-8")
        # `assertIn` sur un fichier entier deverse le fichier dans le rapport
        # d'echec. On teste donc un booleen, et on redige le message.
        self.assertTrue(
            "min(total_pages, 10)" in source,
            "le plafond de dix pages a disparu: si c'est voulu, retirer ce "
            "test avec la mesure qui le justifie")
        self.assertTrue(
            "couverture_lue(lues, total_pages)" in source,
            "le lecteur PDF ne compare plus les pages lues au total: sa "
            "troncature redevient muette")


class LE_SCAN_DECLARE_TOUJOURS_SA_COUVERTURE(unittest.TestCase):
    """La propriete qui doit survivre: le chemin MESURE, lui, ne se tait pas.

    Les trois autres appelants rendent `INDETERMINEE` aujourd'hui, et ce test
    ne l'exige pas d'eux - le leur imposer maintenant ferait rougir la garde
    sur du travail non fait plutot que sur une regression.
    """

    CHEMIN = (DEPOT / "server/src/coproscope/modules/_privacyops_parts"
              / "02_report_and_runtime.py")

    def test_screen_existing_pose_la_couverture_avant_le_verdict(self) -> None:
        source = self.CHEMIN.read_text(encoding="utf-8")
        pose = source.index("row[CHAMP_COUVERTURE] = couverture")
        verdict = source.index("apply_access_policy(row, text=text")
        self.assertLess(
            pose, verdict,
            "la couverture est posee APRES le verdict: elle n'y entre pas")

    def test_le_repli_declare_SA_couverture_et_non_celle_qui_a_echoue(self) -> None:
        """Reporter la premiere ferait dire a ce verdict qu'il repose sur une
        lecture qui n'a rien ramene."""
        source = self.CHEMIN.read_text(encoding="utf-8")
        self.assertIn(
            "text, couverture = _read_existing_text_artifact", source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
