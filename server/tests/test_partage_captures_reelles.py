"""Le partage GitHub ne doit pas emporter les captures faites sur donnees reelles.

Contexte du 2026-09-08. Le tri des 57 captures a montre qu'un ecran affichait
`copropriete de demonstration` sur un jeu que son propre fichier source declare
`reelle: true`. L'etiquette fausse a desarme trois relecteurs sur quatre. La
cause est corrigee a la source, mais les captures deja produites restent sur
disque et `docs/` est autorise en bloc au partage.

Ce module verifie deux choses, et la seconde compte autant que la premiere:
la garde mord sur ce qu'elle couvre, et elle NE couvre PAS ce qu'elle ne couvre
pas. Une garde dont on ignore le bord se prend pour une garantie.
"""

import json
import unittest
from pathlib import Path

from coproscope.core.share import audit_repo

RACINE = Path(__file__).resolve().parents[2]
CONFIG = RACINE / "server" / "src" / "coproscope" / "configs" / "github_sharing.default.yml"

# Campagnes de captures produites sur des donnees reelles ou derivees d'une
# instance reelle. Ce sont des CHEMINS, donc des modalites observees.
CAMPAGNES_REELLES = (
    "docs/assets/synthese-gouvernance-2026-09-04/",
    "docs/assets/edition-2026-09-04/",
    "docs/assets/audit-pages-controle-2026-09-03/",
    "docs/assets/comptes-2026-09-04/",
    "docs/assets/maquettes-controle-2026-09-03/",
)


class PartageCapturesReellesTests(unittest.TestCase):
    def setUp(self):
        self.audit = audit_repo(RACINE, CONFIG)
        self.partageable = [str(x).replace("\\", "/") for x in self.audit.get("shareable", [])]

    def test_aucune_capture_de_campagne_reelle_n_est_partageable(self):
        fuites = [
            chemin
            for chemin in self.partageable
            if any(chemin.startswith(prefixe) for prefixe in CAMPAGNES_REELLES)
        ]
        self.assertEqual(
            fuites,
            [],
            "Ces fichiers partiraient sur le depot PUBLIC alors qu'ils viennent "
            "d'une campagne de captures sur donnees reelles:\n  "
            + "\n  ".join(fuites[:20]),
        )

    def test_les_cinq_campagnes_sont_bien_declarees_dans_la_config(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        declares = set(config.get("prefixes_jamais_partager", []))
        manquants = [c for c in CAMPAGNES_REELLES if c not in declares]
        self.assertEqual(
            manquants,
            [],
            "Campagnes retirees de la config sans que ce test soit mis a jour: "
            + ", ".join(manquants),
        )

    def test_la_garde_est_une_liste_de_chemins_et_ne_couvre_pas_une_campagne_future(self):
        """Le residu, rendu executable au lieu d'etre seulement ecrit en prose.

        La garde reconnait des prefixes constants. Une campagne de captures
        creee demain sous un nom neuf sera partageable tant que personne ne
        l'ajoute a la main. Ce test ECHOUE le jour ou quelqu'un rend la garde
        sensible a la provenance - et ce jour-la, il faut le supprimer en
        gardant les deux autres. Tant qu'il passe, la garde est incomplete et
        on le sait.
        """
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        prefixes = config.get("prefixes_jamais_partager", [])
        campagne_future = "docs/assets/captures-2027-01-15/"
        self.assertNotIn(
            campagne_future,
            prefixes,
            "Ce chemin fictif ne devrait exister nulle part.",
        )
        self.assertTrue(
            all("*" not in p and "?" not in p for p in prefixes),
            "Si la config accepte desormais des motifs, la garde a change de "
            "nature: relire ce test au lieu de le faire passer.",
        )
        self.assertIn(
            "residu_non_couvert",
            config,
            "Le bord de la garde doit rester nomme dans la config: une garde "
            "dont on ignore le bord se prend pour une garantie.",
        )


if __name__ == "__main__":
    unittest.main()
