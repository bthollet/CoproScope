# -*- coding: utf-8 -*-
"""L'issue d'un vote se pose SOUS un titre, et pas seulement dans une phrase.

`RM-2026-0129`. Le droit rend ce residu ordinaire, pas exotique. **Decret
67-223 art. 17**, cle `d67.17` du registre - *le proces-verbal comporte, **sous
l'intitule de chaque question inscrite a l'ordre du jour**, le resultat du
vote*. Le CONTENU est norme, la REDACTION ne l'est pas, et le mot `resolution`
ne figure meme pas a l'article.

**CONSEQUENCE:** un proces-verbal qui ecrit l'intitule puis
`Resultat du vote : adoptee` est **parfaitement conforme** et n'etait lu par
aucun des deux anneaux livres - ils lisent tous deux une PREDICATION
(*cette resolution est adoptee*), la ou l'article decrit une POSITION.

**L'AXE.** Ce qui VARIE: la redaction - avec ou sans designation, avec ou sans
lead-in, `Resultat du vote :`, `Vote :`, ou rien du tout. Ce qui reste
INVARIANT: **l'issue se pose sous le titre de la question**, ce qui en fait un
fait de POSITION et non de vocabulaire. On borne donc **la ligne**, jamais les
mots: une ligne qui n'enonce QUE le resultat.

**MESURE SUR LES DEUX CABINETS, 2026-09-12.**

| | cabinet A (858 doc.) | cabinet B (22 doc.) |
|---|---:|---:|
| ancres AVANT | 391 | 95 |
| ancres APRES | 489 | 137 |
| documents qui changent | **15** | **3** |
| dont un anneau existant perd la main | **0** | **0** |

**Les dix-huit documents qui changent passaient tous de `aucune` a
`position`.** L'anneau n'enleve donc la main a personne: il lit la ou rien
n'etait lu. C'est le resultat le plus sur qu'un deplacement de bareme puisse
avoir, et c'est ce que `RM-2026-0076` exigeait de mesurer avant d'y toucher.

**CE QUI PROTEGE DES FAUX POSITIFS, et c'est le defaut qui a coute `a56b9fe`:**

- la **serie** - trois lignes au moins - car un document qui cite une issue en
  passant n'en aligne pas trois seules sur leur ligne;
- le **singulier** - `resolutions adoptees` est un titre de section, pas un
  constat de vote. Mesure: **zero ligne au pluriel** dans les deux corpus,
  donc l'exclusion ne coute rien et protege d'un faux positif connu;
- l'**ordre des anneaux** - la position passe en dernier, apres les deux
  formules predicatives, donc la redaction mesuree d'un cabinet garde la main
  quand elle est presente.
"""
from __future__ import annotations

import unittest

from coproscope.modules._resolutions_cloture import (
    ANNEAU_AUCUN,
    ANNEAU_LARGE,
    ANNEAU_POSITION,
    ANNEAU_STRICT,
    ancres,
    locution_de_cloture,
    positions,
)

#: La forme que le decret decrit, ecrite ici a la main: un intitule, puis le
#: resultat. Aucune designation, aucune predication.
SOUS_LE_TITRE = """Question 1 - Approbation des comptes de l'exercice
Resultat du vote : adoptee

Question 2 - Budget previsionnel
Vote : adoptee

Question 3 - Travaux de toiture
Rejetee
"""


class L_ISSUE_SE_LIT_SOUS_LE_TITRE(unittest.TestCase):
    def test_les_trois_issues_sont_lues(self) -> None:
        self.assertEqual(3, len(positions(SOUS_LE_TITRE)))

    def test_l_anneau_retenu_est_celui_de_la_POSITION(self) -> None:
        marques, anneau = ancres(SOUS_LE_TITRE)
        self.assertEqual(ANNEAU_POSITION, anneau)
        self.assertEqual(3, len(marques))

    def test_le_segment_rend_son_issue_et_son_anneau(self) -> None:
        issue, anneau = locution_de_cloture(
            "Question 2 - Budget\nResultat du vote : adoptee")
        self.assertEqual("adoptee", issue.strip().lower())
        self.assertEqual(ANNEAU_POSITION, anneau)

    def test_sans_lead_in_l_issue_seule_suffit(self) -> None:
        """L'article norme le contenu, pas la redaction: `Rejetee` seul est
        un resultat de vote pose sous son titre."""
        issue, anneau = locution_de_cloture("Question 3 - Toiture\nRejetee")
        self.assertEqual("rejetee", issue.strip().lower())
        self.assertEqual(ANNEAU_POSITION, anneau)


class CE_QUI_PROTEGE_DES_FAUX_POSITIFS(unittest.TestCase):
    def test_un_titre_de_section_au_PLURIEL_n_est_pas_un_vote(self) -> None:
        """`resolutions adoptees` figure dans les deux corpus comme titre."""
        self.assertEqual([], positions("Resolutions adoptees"))
        self.assertEqual([], positions("Decisions approuvees\nAutre ligne"))

    def test_une_issue_NOYEE_dans_la_prose_n_est_pas_lue(self) -> None:
        """C'est le defaut qui a coute `a56b9fe`: un ordre du jour qui CITE
        une issue sans en constater aucune."""
        prose = ("Le conseil rappelle que la resolution a ete adoptee l'an "
                 "dernier par l'assemblee generale des coproprietaires.")
        self.assertEqual([], positions(prose))

    def test_une_issue_ISOLEE_ne_fait_pas_serie(self) -> None:
        """Une lettre peut citer une issue sans en porter la suite.

        Sans la serie, un seul `Adoptee` sur sa ligne suffirait a faire
        basculer un document entier dans l'anneau de position.
        """
        _, anneau = ancres("Objet du courrier\nAdoptee\nCordialement")
        self.assertNotEqual(ANNEAU_POSITION, anneau)

    def test_une_redaction_predicative_garde_la_main(self) -> None:
        """L'ordre des anneaux: la position passe en dernier.

        Un document qui ecrit la formule mesuree d'un cabinet ne doit pas
        basculer dans l'anneau le moins specifique.
        """
        predicatif = ("Cette resolution est adoptee.\n"
                      "Cette resolution est adoptee.\n"
                      "Cette resolution est rejetee.\n"
                      "Adoptee\nAdoptee\nRejetee\n")
        _, anneau = ancres(predicatif)
        self.assertIn(anneau, (ANNEAU_STRICT, ANNEAU_LARGE))


class LE_SILENCE_RESTE_DU_SILENCE(unittest.TestCase):
    """Temoin: l'anneau n'invente rien la ou il n'y a rien."""

    def test_un_texte_sans_issue_ne_rend_aucune_ancre(self) -> None:
        marques, anneau = ancres(
            "Ordre du jour\nPoint 1 - presentation\nPoint 2 - questions\n")
        self.assertEqual([], marques)
        self.assertEqual(ANNEAU_AUCUN, anneau)

    def test_un_texte_vide_ne_leve_pas(self) -> None:
        self.assertEqual(([], ANNEAU_AUCUN), ancres(""))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
