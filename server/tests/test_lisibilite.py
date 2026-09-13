"""Un document a-t-il ete lu, ou seulement traverse."""

from __future__ import annotations

import unittest

from coproscope.modules import lisibilite as L

SCAN_27_PAGES = "\n".join(f"===== PAGE {n} =====\n\n" for n in range(1, 28))

# Un referentiel de trois pages, au format exact que `_write_page_text` produit:
# un marqueur par page, puis le texte de la page, puis une ligne vide.
REFERENTIEL_3_PAGES = "\n".join(
    ligne
    for numero, contenu in enumerate(("Alpha un.", "Beta deux.", "Gamma trois."), start=1)
    for ligne in (f"===== PAGE {numero} =====", contenu, "")
)


class TexteUtileTests(unittest.TestCase):
    def test_un_fichier_de_marqueurs_ne_contient_rien(self) -> None:
        """584 caracteres sur le disque, zero caractere de document.

        Mesure du 2026-09-03: c'est le fichier produit pour la convocation du
        21/02/2024, 27 pages scannees. `strip()` le declare non vide.
        """
        self.assertTrue(SCAN_27_PAGES.strip())
        self.assertEqual(L.texte_utile(SCAN_27_PAGES), "")

    def test_le_contenu_reel_survit_au_retrait_des_marqueurs(self) -> None:
        brut = "===== PAGE 1 =====\nResolution 1 adoptee.\n===== PAGE 2 =====\nFin."
        self.assertEqual(L.texte_utile(brut), "Resolution 1 adoptee.\n\nFin.")

    def test_un_texte_sans_marqueur_est_rendu_tel_quel(self) -> None:
        self.assertEqual(L.texte_utile("  Facture 42  "), "Facture 42")


class VerdictTests(unittest.TestCase):
    def test_un_scan_de_27_pages_est_illisible(self) -> None:
        self.assertEqual(L.verdict(SCAN_27_PAGES, 27), L.ILLISIBLE)
        self.assertEqual(L.densite(SCAN_27_PAGES, 27), 0.0)

    def test_un_proces_verbal_dense_est_lisible(self) -> None:
        brut = "===== PAGE 1 =====\n" + ("Resolution adoptee. " * 200)
        self.assertEqual(L.verdict(brut, 1), L.LISIBLE)

    def test_le_meme_volume_de_texte_change_de_verdict_selon_la_pagination(self) -> None:
        """La question n'est pas s'il y a du texte, mais s'il y en a assez."""
        brut = "===== PAGE 1 =====\n" + ("mot " * 60)  # 240 caracteres
        self.assertEqual(L.verdict(brut, 1), L.LISIBLE)
        self.assertEqual(L.verdict(brut, 30), L.ILLISIBLE)

    def test_sans_pagination_on_ne_tranche_pas(self) -> None:
        self.assertEqual(L.verdict("", 0), L.INDETERMINE)
        self.assertEqual(L.verdict(SCAN_27_PAGES, 0), L.INDETERMINE)


class DemandeUtilisateurTests(unittest.TestCase):
    def test_le_message_explique_sans_jargon(self) -> None:
        d = L.demande_utilisateur("convocation_AGO.pdf", 27, SCAN_27_PAGES)
        self.assertIn("27 pages", d["constat"])
        self.assertIn("scanné", d["constat"])
        self.assertEqual(d["caracteres_trouves"], 0)
        # Le sigle est developpe a sa premiere occurrence.
        self.assertIn("reconnaissance optique de caractères", d["remede"])
        self.assertIn("OCR", d["remede"])
        # Le document d'origine n'est jamais modifie, et on le dit.
        self.assertIn("jamais", d["remede"])
        # Local-first: la question de la confidentialite est repondue d'avance.
        self.assertIn("votre ordinateur", d["confidentialite"])
        self.assertIn("?", d["question"])

    def test_la_duree_suit_le_nombre_de_pages(self) -> None:
        self.assertIn("moins d'une minute", L.demande_utilisateur("a.pdf", 2)["duree"])
        self.assertIn("minute", L.demande_utilisateur("b.pdf", 40)["duree"])


class ReferentielTests(unittest.TestCase):
    """Le referentiel est designe, et la designation est verifiable."""

    def test_le_referentiel_est_la_colonne_text_path(self) -> None:
        self.assertEqual(L.COLONNE_REFERENTIEL, "text_path")
        self.assertIn("text_path", L.REFERENTIEL)
        # Marqueurs COMPRIS: c'est ce qui distingue le referentiel de sa
        # projection, et c'est ce qui lui laisse la frontiere de page.
        self.assertIn("marqueurs", L.REFERENTIEL)


class ProjectionTests(unittest.TestCase):
    """`texte_utile` est une projection, et une projection sait revenir."""

    def test_le_texte_projete_est_celui_de_texte_utile(self) -> None:
        """La formule historique et la projection ne peuvent pas diverger.

        Verifie sur les 825 documents de `tilleuls_20260906` le 2026-09-07:
        825 sur 825 identiques. Ici on garde la garde en dur, pour que la
        moindre reecriture de `projeter` se signale.
        """
        for brut in (
            REFERENTIEL_3_PAGES,
            SCAN_27_PAGES,
            "  Facture 42  ",
            "",
            "===== PAGE 1 =====\n\n\n===== PAGE 2 =====\n  x  ",
        ):
            with self.subTest(brut=brut[:30]):
                attendu = L.MARQUEUR_PAGE_RE.sub("", brut).strip()
                self.assertEqual(L.projeter(brut).texte, attendu)
                self.assertEqual(L.texte_utile(brut), attendu)

    def test_un_decalage_projete_retrouve_son_caractere_dans_le_referentiel(self) -> None:
        """Le point du contrat: la projection n'est plus un cul-de-sac."""
        projection = L.projeter(REFERENTIEL_3_PAGES)
        for decalage in range(len(projection.texte)):
            position = projection.position_referentiel(decalage)
            self.assertEqual(REFERENTIEL_3_PAGES[position], projection.texte[decalage])

    def test_un_decalage_projete_nomme_la_page_du_referentiel(self) -> None:
        projection = L.projeter(REFERENTIEL_3_PAGES)
        self.assertEqual(projection.page(projection.texte.index("Alpha")), 1)
        self.assertEqual(projection.page(projection.texte.index("Beta")), 2)
        self.assertEqual(projection.page(projection.texte.index("Gamma")), 3)

    def test_le_strip_global_decale_des_le_caractere_zero(self) -> None:
        """Le decalage que le `strip()` introduit est celui qu'on sait defaire.

        Sans la table, `texte[0]` est le caractere 19 du referentiel et rien ne
        le dit. C'est exactement la mesure du proces-verbal `DOC-7139EDAD85E4`:
        trois textes concurrents qui divergent au caractere 0.
        """
        projection = L.projeter(REFERENTIEL_3_PAGES)
        self.assertNotEqual(projection.position_referentiel(0), 0)
        self.assertEqual(REFERENTIEL_3_PAGES[projection.position_referentiel(0)], "A")

    def test_la_fin_d_un_segment_est_convertible_comme_son_debut(self) -> None:
        """`parse_resolutions` calcule un couple (start, end): les deux doivent passer."""
        projection = L.projeter(REFERENTIEL_3_PAGES)
        fin = projection.position_referentiel(len(projection.texte))
        self.assertLessEqual(fin, len(REFERENTIEL_3_PAGES))
        with self.assertRaises(ValueError):
            projection.position_referentiel(len(projection.texte) + 1)
        with self.assertRaises(ValueError):
            projection.position_referentiel(-1)

    def test_une_projection_vide_ne_pretend_a_aucune_position(self) -> None:
        """27 pages de marqueurs ne designent aucun point du document."""
        projection = L.projeter(SCAN_27_PAGES)
        self.assertEqual(projection.texte, "")
        with self.assertRaises(ValueError):
            projection.position_referentiel(0)

    def test_sans_borne_la_page_reste_inconnue(self) -> None:
        """On ne repond pas 1 a un texte qui ne dit pas ou commencent ses pages."""
        projection = L.projeter("Facture 42")
        self.assertEqual(projection.page(0), L.PAGE_INCONNUE)
        self.assertEqual(L.PAGE_INCONNUE, 0)


class PagesDuReferentielTests(unittest.TestCase):
    def test_le_decoupage_suit_les_marqueurs(self) -> None:
        pages = L.pages_du_referentiel(REFERENTIEL_3_PAGES)
        self.assertEqual(len(pages), 3)
        self.assertIn("Alpha", pages[0])
        self.assertIn("Beta", pages[1])
        self.assertIn("Gamma", pages[2])

    def test_aucun_marqueur_ne_survit_dans_les_pages(self) -> None:
        """Le repli rendait le document entier, marqueurs compris: texte pollue."""
        for page in L.pages_du_referentiel(REFERENTIEL_3_PAGES):
            self.assertIsNone(L.MARQUEUR_PAGE_RE.search(page))

    def test_le_saut_de_page_n_est_pas_une_frontiere(self) -> None:
        r"""Mesure du 2026-09-07: quatre fichiers du corpus portent un `\f`.

        L'extraction n'en ecrit jamais. Quand il est present il vient du
        contenu, et decouper dessus rendait 4 pages pour un document de 143.
        """
        brut = (
            "===== PAGE 1 =====\nAlpha\f encore page 1\n"
            "===== PAGE 2 =====\nBeta\n"
        )
        pages = L.pages_du_referentiel(brut)
        self.assertEqual(len(pages), 2)
        self.assertIn("encore page 1", pages[0])

    def test_un_referentiel_sans_marqueur_degrade_a_une_page(self) -> None:
        self.assertEqual(L.pages_du_referentiel("Facture 42"), ["Facture 42"])
        self.assertEqual(L.pages_du_referentiel(""), [])

    def test_du_contenu_avant_la_premiere_borne_degrade_au_lieu_de_le_perdre(self) -> None:
        """Ce contenu n'appartient a aucune page declaree.

        L'attribuer a la premiere inventerait une borne; l'ecarter perdrait du
        texte. On rend une page unique, degradation que l'appelant sait nommer.
        Aucun des 825 fichiers mesures n'est dans ce cas.
        """
        brut = "En-tete hors page\n===== PAGE 1 =====\nAlpha\n"
        self.assertEqual(L.pages_du_referentiel(brut), [brut])

if __name__ == "__main__":
    unittest.main()
