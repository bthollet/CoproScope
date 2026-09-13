# -*- coding: utf-8 -*-
"""Un `max()` entre quantites de sens different ne rend pas un maximum.

`RM-2026-0134`, meme axe que `RM-2026-0075` - *d'ou vient ce nombre* - aux
sites que celui-la n'avait pas traites. Les deux surfaces affichees avaient recu
`MontantLu`; il restait sept sites dans la charge utile `model.ux.comptes`,
dont **trois `max()` sur des quantites qui ne mesurent pas la meme chose**.

**POURQUOI LE `max()` EST LA PIRE FORME SUR CET AXE.** Apres l'operation, la
source gagnante est **irrecuperable**: meme un lot futur ne peut pas dire d'ou
vient le chiffre. Les trois sites, releves le 2026-09-12:

- `invoice_total`: trois comptages de *factures* - pieces distinctes, compteur
  de la synthese, rapprochees plus non rapprochees;
- `invoice_matched`: deux notions de *rapproche*;
- `analyzed_posts_count`: **cinq** quantites, dont un comptage de FACTURES
  compare a des comptages de POSTES.

**CE QUE CE LOT NE CHANGE PAS, ET C'EST DELIBERE.** La regle de composition
reste le `max()`. La changer deplacerait des chiffres affiches **sans qu'aucune
mesure ne dise dans quel sens** - et ce depot a deja paye pour un bareme
deplace sans mesure avant/apres (`RM-2026-0076`). Ce qui change: la source
survit, et la divergence entre sources devient un fait lisible.

**L'AXE.** Ce qui VARIE: le nombre de sources, leur nom, celle qui se trouve
etre la plus grande sur une instance. Ce qui reste INVARIANT: **un nombre
affiche repond a une question, et la source qui l'a produit fait partie de la
reponse.** **Hors des valeurs observees:** une source inconnue se declare sous
son propre identifiant, jamais par une chaine vide qui donnerait l'illusion
d'une lecture directe.
"""
from __future__ import annotations

import unittest

from coproscope.web.viewmodels._comptage_declare import (
    COMPTAGE_AUCUN,
    COMPTAGE_CATEGORIES,
    COMPTAGE_LIGNES_ETAT_DEPENSES,
    COMPTAGE_PIECES_DISTINCTES,
    COMPTAGE_SYNTHESE,
    ComptageLu,
    le_plus_grand,
    libelle_comptage,
)


class LA_SOURCE_SURVIT_A_LA_COMPOSITION(unittest.TestCase):
    """Le coeur du defaut: apres un `max()` nu, elle etait irrecuperable."""

    def test_la_source_gagnante_est_nommee(self) -> None:
        lu = le_plus_grand(
            COMPTAGE_PIECES_DISTINCTES,
            (COMPTAGE_PIECES_DISTINCTES, 3),
            (COMPTAGE_SYNTHESE, 7),
        )
        self.assertEqual(7, lu.valeur)
        self.assertEqual(COMPTAGE_SYNTHESE, lu.source)

    def test_tous_les_candidats_sont_gardes(self) -> None:
        """C'est ce qui rend la composition reversible."""
        lu = le_plus_grand(
            COMPTAGE_PIECES_DISTINCTES,
            (COMPTAGE_PIECES_DISTINCTES, 3),
            (COMPTAGE_SYNTHESE, 7),
        )
        self.assertEqual(
            ((COMPTAGE_PIECES_DISTINCTES, 3), (COMPTAGE_SYNTHESE, 7)), lu.candidats)

    def test_un_nombre_qui_ne_repond_pas_a_la_question_le_dit(self) -> None:
        """`substitue`: il y a un nombre, il est juste pour ce qu'il compte,
        et il ne repond pas a la question posee."""
        lu = le_plus_grand(
            COMPTAGE_PIECES_DISTINCTES,
            (COMPTAGE_PIECES_DISTINCTES, 3),
            (COMPTAGE_SYNTHESE, 7),
        )
        self.assertTrue(lu.substitue)
        self.assertFalse(lu.repond)

    def test_un_nombre_qui_repond_le_dit_aussi(self) -> None:
        lu = le_plus_grand(
            COMPTAGE_SYNTHESE,
            (COMPTAGE_PIECES_DISTINCTES, 3),
            (COMPTAGE_SYNTHESE, 7),
        )
        self.assertTrue(lu.repond)
        self.assertFalse(lu.substitue)


class LA_DIVERGENCE_CESSE_D_ETRE_ABSORBEE(unittest.TestCase):
    """Un `max()` presentait un desaccord comme un resultat."""

    def test_des_sources_qui_se_contredisent_le_disent(self) -> None:
        lu = le_plus_grand(
            COMPTAGE_LIGNES_ETAT_DEPENSES,
            (COMPTAGE_LIGNES_ETAT_DEPENSES, 12),
            (COMPTAGE_CATEGORIES, 4),
        )
        self.assertTrue(lu.diverge)
        self.assertEqual(8, lu.ecart)

    def test_des_sources_qui_s_accordent_ne_declarent_rien(self) -> None:
        """Temoin: la garde n'est pas bavarde quand tout concorde."""
        lu = le_plus_grand(
            COMPTAGE_LIGNES_ETAT_DEPENSES,
            (COMPTAGE_LIGNES_ETAT_DEPENSES, 12),
            (COMPTAGE_CATEGORIES, 12),
        )
        self.assertFalse(lu.diverge)
        self.assertEqual(0, lu.ecart)
        self.assertNotIn("contredisent", lu.phrase())

    def test_la_phrase_nomme_les_sources_et_l_ecart(self) -> None:
        """Ce qu'un gabarit pourra afficher sous le chiffre."""
        phrase = le_plus_grand(
            COMPTAGE_LIGNES_ETAT_DEPENSES,
            (COMPTAGE_LIGNES_ETAT_DEPENSES, 12),
            (COMPTAGE_CATEGORIES, 4),
        ).phrase()
        self.assertIn("8", phrase)
        self.assertIn(libelle_comptage(COMPTAGE_CATEGORIES), phrase)


class AUCUNE_SOURCE_N_EST_UNE_REPONSE(unittest.TestCase):
    """Zero candidat ne doit pas se lire comme un comptage nul mesure."""

    def test_sans_candidat_la_source_est_vide(self) -> None:
        lu = le_plus_grand(COMPTAGE_SYNTHESE)
        self.assertEqual(0, lu.valeur)
        self.assertEqual(COMPTAGE_AUCUN, lu.source)
        self.assertFalse(lu.repond)
        self.assertFalse(lu.substitue)
        self.assertIn("aucune source", lu.phrase())

    def test_un_comptage_negatif_est_refuse(self) -> None:
        """Un comptage negatif n'est pas un comptage.

        **Ce test a d'abord ete ecrit sans discriminer**, et la campagne de
        mutation l'a montre: avec `(-5)` et `(2)` parmi les candidats, un
        `max()` sans filtre rend `2` de toute facon. Le cas qui tranche est
        celui ou TOUS les candidats sont negatifs - sans filtre, le moins
        negatif gagne et sort avec une source, donc un chiffre faux presente
        comme mesure.
        """
        lu = le_plus_grand(
            COMPTAGE_SYNTHESE, (COMPTAGE_SYNTHESE, -5), (COMPTAGE_CATEGORIES, -1))
        self.assertEqual(0, lu.valeur)
        self.assertEqual(COMPTAGE_AUCUN, lu.source)
        self.assertIn("aucune source", lu.phrase())

    def test_un_negatif_n_ecarte_pas_un_candidat_valable(self) -> None:
        """Temoin: le filtre ne retire que ce qui n'est pas un comptage."""
        lu = le_plus_grand(
            COMPTAGE_SYNTHESE, (COMPTAGE_SYNTHESE, -5), (COMPTAGE_CATEGORIES, 2))
        self.assertEqual(2, lu.valeur)
        self.assertEqual(COMPTAGE_CATEGORIES, lu.source)

    def test_une_source_inconnue_se_declare_sous_son_nom(self) -> None:
        """Jamais une chaine vide, qui donnerait l'illusion d'une lecture."""
        self.assertEqual("jamais_vue", libelle_comptage("jamais_vue"))
        self.assertEqual("aucune source", libelle_comptage(""))


class LA_CHARGE_UTILE_PORTE_LA_PROVENANCE(unittest.TestCase):
    """Aucun gabarit ne la rend aujourd'hui; elle ne doit pas manquer le jour ou."""

    @staticmethod
    def _unite_des_fragments() -> "ast.Module":
        """Le repertoire de fragments CONCATENE, tel qu'il s'execute, puis parse.

        **Ces deux tests lisaient du TEXTE sur un chemin fige, et c'etait faux
        deux fois** (`RM-2026-0134`, 2026-09-12). L'un exigeait que trois noms
        de cles APPARAISSENT dans `part_001.pyfrag`: un commentaire le
        satisfaisait. L'autre interdisait trois litteraux d'assignation,
        `"analyzed_posts_count = max("` et deux autres - une enumeration de
        modalites, deja DEFAITE dans le fichier lu: la ligne 274 ecrit
        `"analyzed_posts_count": max(post_count, invoice_count, len(alerts)...)`,
        forme a deux-points que le litteral n'appariait pas. Ce test portait
        donc le nom *aucun max nu ne subsiste* pendant qu'un max nu subsistait.
        Les deux lisent desormais l'ARBRE SYNTAXIQUE; le recensement de toutes
        les compositions nues de `web/` vit dans
        `test_un_nombre_compose_ne_perd_pas_sa_source.py`, ou la ligne 274 est
        nommee en dette.
        """
        import ast
        import warnings
        from pathlib import Path

        from coproscope.source_fragments import fragment_sources

        web = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web"
        texte = next(t for n, t in fragment_sources(web)
                     if n.replace("\\", "/") == "viewmodels/_comptes_builder_fragments#fragments")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            return ast.parse(texte)

    def test_les_trois_comptages_composes_exposent_leur_source(self) -> None:
        """Des CLES de dictionnaire, pas des mots: un commentaire ne compte plus."""
        import ast
        cles = {n.value for d in ast.walk(self._unite_des_fragments())
                if isinstance(d, ast.Dict) for n in d.keys
                if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        for clef in ("analyzed_posts_source", "invoice_total_source",
                     "invoice_matched_source"):
            with self.subTest(clef=clef):
                self.assertIn(clef, cles)

    def test_les_trois_comptages_composes_passent_par_le_plus_grand(self) -> None:
        """Ce que la reparation du matin a reellement fait, mesure dans l'arbre.

        Ancien nom: `test_aucun_max_nu_ne_subsiste_sur_ces_trois_comptages` -
        faux, voir `_unite_des_fragments`. Ce qui est vrai et gardable: les trois
        valeurs composees sont affectees par un appel a `le_plus_grand`, qui
        garde la valeur ET ses candidats.
        """
        import ast
        affectees = {}
        for n in ast.walk(self._unite_des_fragments()):
            if (isinstance(n, ast.Assign) and len(n.targets) == 1
                    and isinstance(n.targets[0], ast.Name)
                    and isinstance(n.value, ast.Call)
                    and isinstance(n.value.func, ast.Name)):
                affectees[n.targets[0].id] = n.value.func.id
        for nom in ("invoice_total_lu", "invoice_matched_lu", "analyzed_posts_lu"):
            with self.subTest(valeur=nom):
                self.assertEqual("le_plus_grand", affectees.get(nom),
                                 "%s n'est plus compose par `le_plus_grand`: "
                                 "la source gagnante serait de nouveau effacee" % nom)


class LE_TYPE_RESTE_UNE_VALEUR(unittest.TestCase):
    """Temoin de conception: un comptage lu ne se modifie pas apres coup."""

    def test_le_comptage_est_immuable(self) -> None:
        lu = ComptageLu(3, COMPTAGE_SYNTHESE, COMPTAGE_SYNTHESE, ())
        with self.assertRaises(Exception):
            lu.valeur = 4  # type: ignore[misc]


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
