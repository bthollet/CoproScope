from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
#: `RM-2026-0106`: l'extraction du texte visible vivait ici, en double
#: avec celle de l'autre garde. Elle est partie dans
#: `tests/_texte_visible.py`, qui reunit les deux. Ne pas la recreer:
#: deux instruments partiels pour une notion, c'est le defaut que ce
#: lot a retire.
WEB_TEMPLATES = ROOT / "server" / "src" / "coproscope" / "web" / "templates"
LANGUAGE_DOC = ROOT / "docs" / "registre_langage_ui.md"
P0_DOC = ROOT / "docs" / "ux_novice_p0.md"

#: `governance.html`, `depot.html` et `actions.html` sont partis avec leurs
#: ecrans, supprimes par la recette de Brice du 2026-09-13 (`RM-2026-0183`).
TEMPLATE_TARGETS = (
    WEB_TEMPLATES / "base.html",
    WEB_TEMPLATES / "_context_banner.html",
    WEB_TEMPLATES / "overview.html",
    WEB_TEMPLATES / "pieces.html",
    WEB_TEMPLATES / "requests.html",
    WEB_TEMPLATES / "agcontentieux.html",
)

EXCLUDED_TEMPLATE = WEB_TEMPLATES / "document_intake.html"



def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class UiNoviceLanguageStaticTests(unittest.TestCase):
    def test_language_register_defines_core_translation_grid(self) -> None:
        doc = _read(LANGUAGE_DOC)

        self.assertIn("| Concept | Dire en premier niveau | Definition novice |", doc)
        for row in (
            "| Coffre | coffre de copro, coffre local, coffre chiffre |",
            "| Sync | synchronisation a verifier, sync externe, dossier de synchronisation |",
            "| Role | role, mandat, qui agit |",
            "| Preuve | preuve, source, justificatif |",
            "| Action | prochaine action, action attendue, relance |",
        ):
            self.assertIn(row, doc)

        self.assertIn("Jargon primaire interdit sans traduction", doc)
        self.assertIn("Infobulles", doc)
        self.assertIn("Registres de langue", doc)
        self.assertIn("Templates hors perimetre de modification L1: `document_intake.html`", doc)

    def test_p0_doc_records_scope_and_static_contract(self) -> None:
        doc = _read(P0_DOC)

        self.assertIn("sans modifier les templates", doc)
        self.assertIn("ne modifie pas `document_intake.html`", doc)
        self.assertIn("ne touche pas `annotationops`", doc)
        self.assertIn("ne modifie pas les tests QA reserves a Sagan", doc)
        self.assertIn("prochaine action concrete", doc)
        self.assertIn("depot, export prepare, sync non automatique", doc)
        self.assertIn("Le code Jinja, les noms de variables, les routes et les chemins techniques", doc)

    def test_existing_templates_keep_core_novice_anchors(self) -> None:
        # `RM-2026-0183`, 2026-09-13: les ancres `Droits, roles et gouvernance`
        # et `Depot local et exports prepares` etaient les libelles du menu vers
        # `/gouvernance` et `/depot`, et les entrees `governance.html`,
        # `depot.html`, `actions.html` portaient sur leurs gabarits: ecrans
        # supprimes, ancres retirees avec eux.
        expected = {
            "base.html": (
                "Contexte du coffre local",
                "Atelier pieces, relier piece, point, action et preuve",
            ),
            "_context_banner.html": (
                "Contexte actif",
                "Voir le contexte",
                "coffre, role et synchronisation",
            ),
            "overview.html": (
                "Statut sync a verifier",
                "aucune synchronisation externe",
                "Partage externe: non lance",
                "Preuve ou source",
                "Prochaine action",
                "Partage autorise",
            ),
            "pieces.html": (
                "Pieces a demander",
                "Preuves locales a verifier",
                "Action primaire",
                "Prochaine etape",
            ),
            "requests.html": (
                "lecture novice",
                "preuve/source",
                "prochaine action",
                "diffusion",
            ),
            "agcontentieux.html": (
                "Parcours AG contentieux passation",
                "Preuve / source",
                "Restriction / diffusion",
                "Prochaine action",
            ),
        }

        missing: list[str] = []
        for template_name, snippets in expected.items():
            source = _read(WEB_TEMPLATES / template_name)
            for snippet in snippets:
                if snippet not in source:
                    missing.append(f"{template_name}: {snippet!r}")

        self.assertEqual([], missing)

    # `RM-2026-0106`, 2026-09-12: la garde `le mot vault ne parait pas devant
    # l'utilisateur` vivait ICI sur neuf gabarits, et AUSSI dans
    # `test_ui_accessibility_language` sur neuf autres, **avec deux
    # extractions differentes** - celle-ci lisait les attributs restitues,
    # l'autre traversait les elements imbriques, et aucune ne contenait
    # l'autre. Deux instruments partiels pour une seule notion: c'est le
    # defaut numero un du produit applique a l'outillage.
    #
    # La notion vit desormais en un seul endroit, avec l'instrument reuni
    # (`tests/_texte_visible.py`) et la portee derivee de l'arborescence, soit
    # les 46 gabarits. **Ce test est retire et non deplace**: garder ici une
    # copie sur un sous-ensemble strict de la meme portee, avec le meme
    # instrument, serait une garde incapable de mordre seule - le depot les
    # retire plutot que de les garder pour la forme.

    # `RM-2026-0183`, 2026-09-13: `test_templates_with_help_dots_explain_jargon_in_short_titles`
    # ne lisait que `governance.html`, gabarit de l'ecran `/gouvernance` supprime.

    def test_static_scope_does_not_target_reserved_document_intake_template(self) -> None:
        self.assertNotIn(EXCLUDED_TEMPLATE, TEMPLATE_TARGETS)
        self.assertTrue(EXCLUDED_TEMPLATE.exists())


if __name__ == "__main__":
    unittest.main()
