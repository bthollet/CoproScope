# -*- coding: utf-8 -*-
"""Ce que CoproScope ecrit lui-meme se declare, au moment de l'ecriture.

`RM-2026-0061`. *Tant que la marque n'existe pas, tout filtre de provenance
retombe sur une liste de chemins, c'est-a-dire sur la convention d'une seule
instance.*

**LES DEUX MARQUES EXISTANTES NE REPONDAIENT PAS, et l'item l'avait mesure.**
`source_kind`/`source_zone` sont derives du CHEMIN et valent `raw` pour **1090
documents sur 1090** chez un cabinet, **22 sur 22** chez l'autre - les deux
instances declarent `workspace` et `raw` sur la meme racine. Et
`action_log.csv` ne connait que les courses journalisees: **aucun des 11
fichiers de travail mal classes n'y figure**, sur 34 cibles ecrites distinctes.

**L'AXE.** Ce qui VARIE: le format ecrit, le module qui ecrit, l'instance, et
le fait qu'une course soit journalisee. Ce qui reste INVARIANT: **ce que
CoproScope ecrit lui-meme n'est pas une piece recue du syndic.** La marque se
pose donc au POINT D'ECRITURE - le seul endroit ou cette verite est certaine.

**HORS DES VALEURS OBSERVEES:** un module ecrit demain est marque le jour de sa
premiere ecriture, sans que personne ajoute rien, parce que la marque vit sous
`write_csv` et `write_text` et non dans une liste d'appelants.

**LA MARQUE NE TOUCHE AUCUN CONTENU.** Un CSV ne recoit pas de colonne, un
Markdown pas d'en-tete: une estampille qui change le fichier qu'elle decrit
rendrait les empreintes incomparables entre coproprietaires, contrainte posee
par `RM-2026-0092`. Le registre est **a cote**, et le fichier reste bit pour
bit celui qui a ete ecrit - ce que le dernier test verifie.

**RESIDU DECLARE, ET IL EST IMPORTANT:** une reponse negative n'est **pas** une
preuve de provenance externe. Un artefact produit avant l'existence de cette
marque n'y figure pas. Un appelant qui conclurait *donc c'est une piece du
syndic* se tromperait sur tout le fonds anterieur - c'est pourquoi le
classement n'est pas encore branche dessus.
"""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from coproscope.core import estampille_artefact as ESTAMPILLE
from coproscope.core.common import write_csv, write_text


class UneInstanceJetable(unittest.TestCase):
    """Chaque test a son instance, creee et jetee ici meme."""

    def setUp(self) -> None:
        self.dossier = tempfile.TemporaryDirectory()
        self.racine = Path(self.dossier.name).resolve()
        (self.racine / "instance.yml").write_text(
            "identifiant_instance: essai\n", encoding="utf-8")
        ESTAMPILLE.oublie_le_cache()

    def tearDown(self) -> None:
        ESTAMPILLE.oublie_le_cache()
        self.dossier.cleanup()


class CE_QUE_LE_PRODUIT_ECRIT_EST_MARQUE(UneInstanceJetable):
    def test_un_csv_ecrit_par_le_produit_est_marque(self) -> None:
        write_csv(self.racine / "outputs" / "rapport.csv", ["a"], [{"a": "1"}])
        self.assertIn("outputs/rapport.csv",
                      ESTAMPILLE.artefacts_produits(self.racine))

    def test_un_texte_ecrit_par_le_produit_est_marque(self) -> None:
        write_text(self.racine / "outputs" / "note.md", "bonjour")
        self.assertTrue(ESTAMPILLE.est_produit_par_coproscope(
            self.racine / "outputs" / "note.md"))

    def test_une_piece_DEPOSEE_n_est_pas_marquee(self) -> None:
        """Le coeur du filtre de provenance: elle n'est pas passee par nous."""
        (self.racine / "raw").mkdir()
        (self.racine / "raw" / "facture.pdf").write_bytes(b"%PDF-1.4")
        self.assertFalse(ESTAMPILLE.est_produit_par_coproscope(
            self.racine / "raw" / "facture.pdf"))

    def test_la_marque_ne_depend_pas_d_une_course_journalisee(self) -> None:
        """C'est la difference avec `action_log.csv`, qui a rate 11 fichiers.

        Aucun contexte de course n'est ouvert ici: l'ecriture suffit.
        """
        write_text(self.racine / "outputs" / "matrice_risques.csv", "x")
        self.assertTrue(ESTAMPILLE.est_produit_par_coproscope(
            self.racine / "outputs" / "matrice_risques.csv"))

    def test_deux_ecritures_du_meme_fichier_ne_font_qu_une_ligne(self) -> None:
        write_text(self.racine / "outputs" / "note.md", "un")
        write_text(self.racine / "outputs" / "note.md", "deux")
        produits = ESTAMPILLE.artefacts_produits(self.racine)
        self.assertEqual(1, sum(1 for p in produits if p == "outputs/note.md"))


class LA_MARQUE_NE_TOUCHE_AUCUN_CONTENU(UneInstanceJetable):
    """Une estampille qui change le fichier rendrait les empreintes

    incomparables entre coproprietaires - contrainte de `RM-2026-0092`."""

    def test_la_marque_ne_change_pas_un_seul_octet(self) -> None:
        """Le fichier estampille est identique a celui qui ne l'est pas.

        **La comparaison se fait contre une ecriture NON marquee du meme
        contenu, et non contre la chaine d'origine** - premier essai du lot, et
        il echouait pour une raison qui n'a rien a voir avec l'estampille:
        `Path.write_text` traduit les fins de ligne sur Windows, donc le
        fichier n'est deja pas l'image exacte de la chaine. Comparer a la
        chaine aurait accuse la marque d'un defaut qui la precede.
        """
        contenu = "ligne une\nligne deux\n"
        marque = self.racine / "outputs" / "note.md"
        write_text(marque, contenu)
        with tempfile.TemporaryDirectory() as ailleurs:
            temoin = Path(ailleurs) / "note.md"
            temoin.write_text(contenu, encoding="utf-8")
            self.assertEqual(
                hashlib.sha256(temoin.read_bytes()).hexdigest(),
                hashlib.sha256(marque.read_bytes()).hexdigest())

    def test_un_csv_ne_recoit_aucune_colonne(self) -> None:
        cible = self.racine / "outputs" / "rapport.csv"
        write_csv(cible, ["a", "b"], [{"a": "1", "b": "2"}])
        premiere = cible.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual("a,b", premiere)


class L_INSTANCE_SE_TROUVE_PAR_SA_FORME(UneInstanceJetable):
    """Jamais par un chemin declare: un dossier deplace reste trouve."""

    def test_un_fichier_profond_retrouve_sa_racine(self) -> None:
        cible = self.racine / "outputs" / "a" / "b" / "c" / "note.md"
        write_text(cible, "x")
        self.assertEqual(self.racine, ESTAMPILLE.racine_d_instance(cible))
        self.assertTrue(ESTAMPILLE.est_produit_par_coproscope(cible))

    def test_une_ecriture_HORS_instance_n_est_pas_marquee(self) -> None:
        """Elle n'appartient a aucun coffre: aucun classement ne la lira."""
        with tempfile.TemporaryDirectory() as ailleurs:
            cible = Path(ailleurs) / "note.md"
            write_text(cible, "x")
            self.assertIsNone(ESTAMPILLE.racine_d_instance(cible))
            self.assertFalse(ESTAMPILLE.est_produit_par_coproscope(cible))

    def test_le_registre_ne_se_marque_pas_lui_meme(self) -> None:
        """Sinon la marque se declencherait sans fin et n'apprendrait rien."""
        write_text(self.racine / "outputs" / "note.md", "x")
        self.assertNotIn("registers/artefacts_produits.csv",
                         ESTAMPILLE.artefacts_produits(self.racine))

    def test_le_refus_du_registre_est_EPROUVE_et_non_suppose(self) -> None:
        """La campagne de mutation a montre que le test precedent ne suffit pas.

        Le registre est ecrit en direct, pas par `write_csv`: retirer son
        exclusion ne changeait donc rien de mesurable, et la branche passait
        pour gardee sans l'etre. On l'appelle ici **directement**, ce qui est
        le seul moyen d'eprouver une protection contre un appel qui n'existe
        pas encore - et qui, s'il existait, ferait tourner la marque sans fin.
        """
        write_text(self.racine / "outputs" / "note.md", "x")
        registre = self.racine / "registers" / "artefacts_produits.csv"
        self.assertTrue(registre.is_file())
        self.assertFalse(ESTAMPILLE.marque_produit(registre))


class LE_RESIDU_EST_DECLARE(UneInstanceJetable):
    """Une reponse negative n'est pas une preuve de provenance externe."""

    def test_un_artefact_ANTERIEUR_a_la_marque_ne_s_y_trouve_pas(self) -> None:
        """Le fonds deja produit reste invisible a ce filtre, et c'est ecrit.

        Un appelant qui lirait `False` comme *piece du syndic* se tromperait
        sur tout ce qui a ete ecrit avant que cette marque n'existe.
        """
        ancien = self.racine / "outputs" / "synthese_2024.md"
        ancien.parent.mkdir(parents=True, exist_ok=True)
        ancien.write_text("produit avant la marque", encoding="utf-8")
        self.assertFalse(ESTAMPILLE.est_produit_par_coproscope(ancien))

    def test_le_module_declare_ce_residu_en_toutes_lettres(self) -> None:
        source = Path(ESTAMPILLE.__file__).read_text(encoding="utf-8")
        self.assertIn("n'est pas une preuve de provenance externe", source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
