# -*- coding: utf-8 -*-
"""La conclusion d'un controle s'ecrit, et la colonne cesse de mentir.

**Ce que la page promettait sans l'offrir.** Sous le tableau de gouvernance,
elle affichait: *« Le geste n'est pas encore cable : la table traces_controle
est lue par la colonne Ma conclusion et aucun geste de l'application ne
l'ecrit. »* La colonne montrait donc **toujours** `A instruire`, quel que soit
le travail fait par un humain devant l'ecran.

Mesure du 2026-09-09, par execution avec un autorisateur SQLite pose sur chaque
connexion: sur les neuf tables du lot gouvernance, **sept sont ecrites par la
chaine de production et deux ne le sont par personne** - `dossiers_depense` et
`traces_controle`. Arbitrage de Brice le meme jour: *« bien evidemment on trace
le controle »*.

**Ce que ce module garde, et pourquoi chaque garde existe:**

1. une conclusion ecrite **se relit**, et la colonne change - sans quoi le geste
   serait cable et invisible, ce qui est pire que pas de geste;
2. **`a_instruire` est refuse**: c'est l'absence de conclusion. L'ecrire rendrait
   un controle non fait indiscernable d'un controle conclu sans reserve. Il
   etait deja refuse, mais **par accident** - la normalisation en majuscules en
   faisait un mot inconnu - et une justesse obtenue par hasard tombe au premier
   changement de normalisation;
3. **une re-extraction n'efface pas une conclusion**: c'est la propriete qui
   fait qu'un humain peut travailler sans craindre le prochain passage de la
   chaine. Elle est eprouvee ici en rejouant une ecriture derivee apres coup;
4. un verdict hors vocabulaire **est refuse avec son motif**, jamais ecrit tel
   quel: une valeur qui ressemble a du vocabulaire sans en etre eteint en
   silence les controles qui s'appuient dessus.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.modules import _actes_schema as schema
from coproscope.modules import _actes_store as store
from coproscope.web._controle_gouvernance_etat import EXIGENCES_BACK
from coproscope.web._controle_gouvernance_conclusion import (
    ConclusionRefusee,
    PAS_UN_VERDICT,
    VERDICTS_ECRIVABLES,
    construire_trace,
    enregistrer,
)


class UneConclusionSeRefuseAvantD_etreEcrite(unittest.TestCase):
    """Les refus, mesures sans toucher a une instance."""

    def test_les_trois_verdicts_de_la_page_sont_ecrivables(self) -> None:
        self.assertEqual(
            {"CONTROLE_TRACE", "QUESTION_POSEE", "RESERVE"}, set(VERDICTS_ECRIVABLES)
        )

    def test_a_instruire_est_refuse_EXPLICITEMENT(self) -> None:
        """Il l'etait par accident: la mise en majuscules le rendait inconnu.

        Ce test porte sur la valeur telle que la page l'ecrit - minuscules - et
        exige que le refus nomme la raison, pas qu'il tombe sur un dictionnaire.
        """
        with self.assertRaises(ConclusionRefusee) as refus:
            construire_trace("acte", "ACTE-1", PAS_UN_VERDICT, "")
        self.assertIn("absence de conclusion", str(refus.exception))

    def test_un_verdict_inconnu_est_refuse_en_nommant_les_possibles(self) -> None:
        with self.assertRaises(ConclusionRefusee) as refus:
            construire_trace("acte", "ACTE-1", "VALIDE", "")
        self.assertIn("CONTROLE_TRACE", str(refus.exception))

    def test_un_sujet_non_relie_est_refuse_au_lieu_d_etre_ecrit_invisible(self) -> None:
        """Une trace rangee sous un sujet que rien ne lit serait ecrite, jamais
        montree, et croirait avoir ete enregistree."""
        with self.assertRaises(ConclusionRefusee) as refus:
            construire_trace("facture", "F-1", "CONTROLE_TRACE", "")
        self.assertIn("jamais lue", str(refus.exception))

    def test_une_ligne_sans_sujet_est_refusee(self) -> None:
        with self.assertRaises(ConclusionRefusee):
            construire_trace("acte", "   ", "CONTROLE_TRACE", "texte")

    def test_un_texte_trop_long_est_refuse_et_non_tronque(self) -> None:
        """Une conclusion coupee en silence dirait autre chose que l'humain."""
        with self.assertRaises(ConclusionRefusee) as refus:
            construire_trace("acte", "ACTE-1", "RESERVE", "x" * 5000)
        self.assertIn("tronque", str(refus.exception))

    def test_la_ligne_porte_l_origine_humaine_et_aucun_document(self) -> None:
        """Les deux champs qui la protegent d'une re-extraction."""
        ligne = construire_trace("acte", "ACTE-1", "CONTROLE_TRACE", "Verifie.")
        self.assertEqual("CORRIGE_HUMAIN", ligne["origine"])
        self.assertEqual("", ligne["doc_id"])
        # Decision du 2026-09-09: pas d'auteur pour l'instant.
        self.assertEqual("", ligne["auteur"])


class L_ECRAN_NE_DIT_PLUS_QUE_LE_GESTE_MANQUE(unittest.TestCase):
    """La prose de l'ecran suit le code, sinon elle ment a l'utilisateur."""

    def test_ENREGISTRER_LA_CONCLUSION_N_EST_PLUS_UNE_EXIGENCE_MANQUANTE(self) -> None:
        """**Ce test exigeait le contraire, et la phrase contredite est citee.**

        Il affirmait `self.assertIn("Enregistrer la conclusion", titres)` -
        c'est-a-dire que l'ecran devait annoncer a l'utilisateur que le geste
        n'existait pas. L'exigence disait: *« La table traces_controle est lue
        par la colonne Ma conclusion et aucun geste de l'application ne
        l'ecrit. La colonne montre donc toujours A instruire. »*

        **Le geste existe depuis le 2026-09-09**, sur l'arbitrage de Brice:
        *« bien evidemment on trace le controle »*. Laisser cette exigence
        affichee ferait lire a l'utilisateur qu'il ne peut pas conclure alors
        qu'il le peut - exactement la prose perimee que le lot `RM-2026-0059` a
        trouvee sur `actes_autorisation`, qui annonçait *rien n'ecrit hors des
        tests* alors que la chaine l'ecrivait a chaque passage.

        Ce qui la remplace n'est pas un vide: **la colonne `auteur` reste vide
        par decision**, et l'ecran doit le dire.
        """
        titres = " ".join(titre for titre, _ in EXIGENCES_BACK)
        textes = " ".join(texte for _, texte in EXIGENCES_BACK)
        self.assertNotIn("Enregistrer la conclusion", titres)
        self.assertIn("auteur", titres.lower() + textes.lower())
        self.assertNotIn(
            "aucun geste de l'application ne l'écrit", textes,
            "l'ecran annonce encore que le geste n'existe pas",
        )


class UneConclusionEcriteSeRelit(unittest.TestCase):
    """De bout en bout, sur une copie jetable de l'instance partageable."""

    def setUp(self) -> None:
        racine = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        cible = Path(self.tempdir.name) / "instance"
        shutil.copytree(racine / "examples" / "synthetic_copro", cible)
        # **L'instance partageable ne declare AUCUN coffre local**, mesure le
        # 2026-09-09: `settings.vault.local_root` y est absent, donc l'ecran de
        # gouvernance ne peut y ecrire ni y lire quoi que ce soit. Ce n'est pas
        # un defaut de l'exemple - un coffre est une donnee de travail - mais
        # ça veut dire que **la copie de test doit le poser elle-meme**, et
        # qu'aucune mesure de cet ecran ne tourne sur l'exemple tel quel.
        fichier = cible / "instance.yml"
        texte = fichier.read_text(encoding="utf-8")
        marque = '"settings": {'
        assert marque in texte, "forme de instance.yml inattendue"
        fichier.write_text(
            texte.replace(marque, marque + '\n    "vault": {"local_root": "./vault_local"},', 1),
            encoding="utf-8",
        )
        self.instance = load_instance(str(fichier), None)

    def _traces(self) -> list[dict[str, str]]:
        return store.lire_table(self.instance, schema.TABLE_TRACES)

    def test_une_conclusion_ecrite_se_relit(self) -> None:
        avant = len(self._traces())
        ligne = enregistrer(self.instance, "acte", "ACTE-EPREUVE",
                            "CONTROLE_TRACE", "Verifie contre l'annexe 2.")
        apres = self._traces()
        self.assertEqual(avant + 1, len(apres))
        relue = [t for t in apres if t["trace_id"] == ligne["trace_id"]]
        self.assertEqual(1, len(relue), "la conclusion ecrite ne se relit pas")
        self.assertEqual("ACTE-EPREUVE", relue[0]["sujet_id"])
        self.assertEqual("CONTROLE_TRACE", relue[0]["verdict"])

    def test_UNE_REEXTRACTION_N_EFFACE_PAS_UNE_CONCLUSION(self) -> None:
        """La propriete qui permet a un humain de travailler sans crainte.

        Le magasin supprime les lignes **derivees des documents cites**. Une
        conclusion humaine ne cite aucun document, donc aucune re-extraction ne
        porte sur elle. On l'eprouve au lieu de le croire: on ecrit une
        conclusion, puis on rejoue une ecriture derivee qui cite des documents,
        et on verifie que la conclusion est toujours la.
        """
        ligne = enregistrer(self.instance, "acte", "ACTE-SURVIT",
                            "RESERVE", "A confirmer avec le syndic.")
        store.ecrire(
            self.instance, schema.TABLE_TRACES, [], ["DOC-QUELCONQUE", "DOC-AUTRE"]
        )
        restantes = {t["trace_id"] for t in self._traces()}
        self.assertIn(
            ligne["trace_id"], restantes,
            "une re-extraction a efface une conclusion humaine: le travail de "
            "l'utilisateur disparaitrait au prochain passage de la chaine",
        )

    def test_deux_conclusions_successives_COEXISTENT_en_base(self) -> None:
        """Une trace ne s'ecrase pas: les deux lignes vivent.

        **Ce test a ete renomme le 2026-09-12, et son ancien nom est la lecon.**
        Il s'appelait `..._et_la_derniere_gouverne`, et sa docstring affirmait
        *l'affichage retient la derniere ecrite. Ce test fige ce comportement
        pour qu'il ne change pas sans qu'on le decide*. Son corps - inchange
        ici - n'assert que la coexistence des deux `trace_id` dans la table:
        il n'appelle jamais `construire_lignes` et ne touche aucune cellule
        d'ecran. **Il ne figeait donc rien de ce qu'il annoncait**, et la garde
        vivait dans le seul endroit que personne ne relit, un nom de methode.

        Pire, la propriete annoncee etait FAUSSE: le repli gagnait par
        ecrasement dans l'ordre `constate_le DESC`, donc le PLUS ANCIEN
        l'emportait, et deux conclusions du meme jour se departageaient sur
        `trace_id`, un jeton aleatoire. Le verdict affiche etait tire au sort -
        dans ce scenario meme, qui ecrit deux conclusions a la suite.

        Ce que la cellule d'ecran fait est desormais mesure la ou cela vit, par
        le point d'entree: `test_une_cellule_de_conclusion_ne_se_tire_pas_au_sort.py`.
        Ici, une seule question, et ce test y repond vraiment: les deux lignes
        coexistent-elles ?
        """
        premiere = enregistrer(self.instance, "acte", "ACTE-DEUX",
                               "QUESTION_POSEE", "Demande envoyee.")
        seconde = enregistrer(self.instance, "acte", "ACTE-DEUX",
                              "CONTROLE_TRACE", "Reponse recue, verifie.")
        ids = {t["trace_id"] for t in self._traces()}
        self.assertIn(premiere["trace_id"], ids)
        self.assertIn(seconde["trace_id"], ids)
        self.assertNotEqual(premiere["trace_id"], seconde["trace_id"],
                            "les deux traces portent le meme identifiant: "
                            "l'une ecrase l'autre et la coexistence mesuree "
                            "ici serait une illusion")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
