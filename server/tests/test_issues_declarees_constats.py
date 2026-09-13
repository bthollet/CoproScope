"""Une issue qui n'est pas une conclusion lue doit faire une ligne de travail.

Suite de `test_issues_declarees.py`, coupee a 600 lignes par le garde-fou du
depot. Ce fichier prolonge d'une table les quatre que son aine surveille: apres
le pont, le vocabulaire, l'ecran des resolutions et l'ecran de gouvernance,
**la file de travail**.

Pourquoi cette regle n'a pas ete posee avec la valeur qu'elle protege. Le lot
du 2026-09-08 a ajoute `ISSUE_NON_LUE` au vocabulaire des actes, sa traduction
dans le pont, son libelle a l'ecran et sa cellule `AFFIRME_SANS_PIECE` dans la
matrice. Il s'est arrete la. La regle ecrite ici aurait echoue sur la valeur
que ce lot ajoutait, et une garde qu'on pose rouge n'est pas une garde: c'est
une dette avec un nom de test. Elle arrive donc avec le constat qui la
satisfait, et son objet est la SEPTIEME issue, pas la sixieme.

Ce qu'elle empeche exactement. Une cellule de matrice range un acte; elle ne
demande rien a personne. La seule chose qui fasse naitre une ligne de travail
est une branche de `v_constats`. Un etat d'issue qui n'en a aucune produit donc
un « A confirmer » de plus dans une matrice qui en porte des centaines - et le
cas que l'etalon isole a la main traverse tout le modele sans que personne
n'ait rien a faire. Ce defaut s'est produit deux fois de suite, sur les deux
seuls etats ajoutes depuis que la matrice existe: `SANS_ISSUE_TRACEE` jusqu'au
2026-09-04, `ISSUE_NON_LUE` du 2026-09-08 au 2026-09-09.

Ce qui reste expose. La derivation lit des litteraux SQL par expression
reguliere, des deux cotes. Une branche ecrite autrement - un `IN (...)`, une
comparaison portee par une vue intermediaire, un nom de colonne aliase - ne
serait pas vue. Le test exigerait alors un constat qui existe deja, ou
declarerait a couvrir un etat qui l'est: il crie a tort plutot que de se taire
a tort, et c'est le seul sens dans lequel une garde a le droit de se tromper.
`test_la_derivation_des_conclusions_lues_n_a_pas_cesse_de_lire` est le plancher
qui rend cette derive visible au lieu de la laisser vider le fichier.

**La reciproque n'est pas vraie, et elle n'est donc pas gardee ici.** Une
premiere version de ce fichier interdisait tout constat pose sur une conclusion
lue, au motif qu'il reprocherait un silence a un document qui conclut. C'est
faux: `ACTE_SANS_EXECUTION` est pose sur `resultat = 'ADOPTEE'` et ne reproche
aucun silence - il dit qu'aucune depense n'est rattachee a une decision qui en
autorisait une. Le test passait par accident, cette branche-la lisant l'alias
`e` quand la regle lisait `a`. Une garde qui tient par un nom d'alias vaut
moins que pas de garde: elle serait tombee au premier renommage, en accusant
une branche legitime.
"""

from __future__ import annotations

import re
import unittest

from coproscope.modules import _actes_constats as CONSTATS
from coproscope.modules import _actes_vocabulaire as V
from coproscope.modules import _actes_vues as VUES


#: Les trois issues qui disent « le proces-verbal conclut, et nous l'avons lu ».
#: Elles ne sont pas listees: elles sont lues dans les branches de la matrice
#: qui les marquent `PIECE_PRODUITE`. Une quatrieme ajoutee la sortirait d'elle
#: -meme du champ de la regle, sans qu'une ligne d'ici bouge.
def conclusions_lues() -> set[str]:
    sql = "\n".join(VUES.VUES)
    return set(
        re.findall(r"resultat\s*=\s*'([^']*)'\s*THEN\s*'PIECE_PRODUITE'", sql)
    )


#: Les issues sur lesquelles `v_constats` ouvre une branche, donc celles qui
#: peuvent produire une ligne de travail.
def issues_visees_par_un_constat() -> set[str]:
    return set(
        re.findall(r"a\.resultat\s*=\s*'([^']*)'", CONSTATS.vue_constats("1=1"))
    )


class ToutEtatNonConcluantOuvreUneLigneDeTravailTests(unittest.TestCase):
    """La cinquieme table: la file de travail."""

    def test_la_derivation_des_conclusions_lues_n_a_pas_cesse_de_lire(self) -> None:
        """Le plancher. Sans lui, un SQL reecrit rendrait ce fichier vide et vert.

        Si la derivation cesse de mordre, elle rend l'ensemble vide, tout le
        vocabulaire tombe dans « a couvrir », et le test suivant echoue en
        masse au lieu de passer en silence - mais il echoue en accusant les
        mauvaises valeurs. Celui-ci nomme la vraie cause avant lui.

        Trois etats, et trois seulement, disent que le document conclut et que
        nous l'avons lu. Ce jeu est une decision de modele: elle se prend ici,
        pas par accident dans une expression reguliere qui a cesse de mordre.
        """
        self.assertEqual(
            conclusions_lues(),
            {V.RESULTAT_ADOPTEE, V.RESULTAT_REJETEE, V.RESULTAT_PAS_DE_VOTE},
        )

    def test_toute_issue_sans_conclusion_lue_ouvre_une_ligne_de_travail(self) -> None:
        a_couvrir = set(V.RESULTATS) - conclusions_lues()
        self.assertTrue(a_couvrir, "la derivation ne rend plus aucun etat a couvrir")
        visees = issues_visees_par_un_constat()
        for issue in sorted(a_couvrir):
            with self.subTest(issue=issue):
                self.assertIn(
                    issue,
                    visees,
                    f"`{issue}` traverse tout le modele sans produire de ligne "
                    "de travail: la matrice le range dans une cellule, et "
                    "personne n'a rien a faire d'une cellule. Il lui faut une "
                    "branche de `v_constats` - c'est le defaut ferme le "
                    "2026-09-04 pour SANS_ISSUE_TRACEE, puis le 2026-09-09 "
                    "pour ISSUE_NON_LUE.",
                )


if __name__ == "__main__":
    unittest.main()
