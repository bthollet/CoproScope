"""Le schema eprouve sur deux corpus de syndics differents et sur l'etalon reel.

Les instances historiques ne sont pas un etalon de justesse: on s'en sert pour
eprouver la FORME - volumes, cardinalites, cas degrades - jamais pour conclure
sur la justesse d'un contenu. L'etalon des issues, lui, a ete etabli a la main
sur la source primaire: `docs/etalon_corpus_tests_ux.md`.
"""

from __future__ import annotations

import shutil

import tempfile
import unittest
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.modules import _actes_requetes as R
from coproscope.vault import gouvernance_store as G


class _Instance:
    """Instance minimale: seul le coffre local compte pour ce magasin."""

    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()


def _acte(acte_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "acte_id": acte_id, "nature": "RESOLUTION_AG", "etat": "CONSTATEE",
        "portee": "ORDINAIRE", "date_effet": "2024-07-03", "exercice": "2024",
        "ag_id": "AG-2024-07-03", "numero": "12", "sous_numero": "",
        "objet": "Ravalement de la facade sud", "montant_autorise": "",
        "entreprise": "", "montant_source": "", "entreprise_source": "",
        "valide_du": "", "valide_au": "", "majorite_requise": "24",
        "majorite_appliquee": "24", "resultat": "ADOPTEE", "resolution_id": "",
        "page": "4", "ancre": "", "confiance": "forte",
        "doc_id": "DOC-PV", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _dossier(dossier_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "dossier_id": dossier_id, "exercice": "2024",
        "date_depense": "2024-09-15", "montant_ttc": "18240.00",
        "fournisseur": "WE GROUP", "libelle": "Ravalement facade sud",
        "imputation": "VOTE_SEPARE", "imputation_motif": "", "aiguillage": "ART_44",
        "facture_doc_id": "DOC-FAC", "ecriture_ref": "", "page": "",
        "ancre": "", "doc_id": "DOC-FAC", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _lien(source: str, relation: str, cible: str, **kw: str) -> dict[str, str]:
    provenance = kw.pop("provenance", "COPROSCOPE_CALCULE")
    target_kind = kw.pop("target_kind", "dossier")
    ligne = {
        "lien_id": A.lien_id("acte", source, relation, target_kind, cible, provenance),
        "source_kind": "acte", "source_id": source, "relation": relation,
        "target_kind": target_kind, "target_id": cible, "provenance": provenance,
        "force_probatoire": "PIECE_PRODUITE", "motif": "", "doute": "",
        "montant_impute": "", "libelle_cible": "", "echeance": "",
        "constate_le": "2024-09-20", "auteur": "", "page": "", "ancre": "",
        "doc_id": "DOC-FAC", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


class GeneralisabiliteTests(unittest.TestCase):
    """Le schema doit tenir chez un second syndic, pas seulement chez le premier.

    Corpus de reference: `instances/erables_pseudo_test`, 22 PDF, exercices 2023 a
    2026. Chez ce syndic, la convocation ne porte aucun corps de resolution:
    l'ordre du jour donne le titre et la majorite, et le devis arrive en fichier
    voisin - `Piece jointe N.10 pour la resolution 19.2 - Devis benjamin ...pdf`.
    """

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=False)

    def test_le_montant_se_lit_du_cote_ou_il_se_trouve(self) -> None:
        """Syndic A: dans le corps. Syndic B: sur le devis joint. Meme predicat."""
        A.ecrire(self.instance, A.TABLE_ACTES, [
            # Syndic A: le corps de la resolution porte le montant.
            _acte("A-R12", montant_autorise="18240.00", entreprise="WE GROUP",
                  montant_source="CORPS_RESOLUTION",
                  entreprise_source="CORPS_RESOLUTION"),
            # Syndic B: rien dans le corps, tout sur le fichier voisin.
            _acte("B-R19-2", date_effet="2026-06-29", exercice="2026",
                  numero="19", sous_numero="2", doc_id="DOC-CONVOC",
                  objet="Remplacement des rambardes"),
        ], ["DOC-PV", "DOC-CONVOC"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("B-R19-2", "DEVIS_RETENU", "DOC-DEVIS", target_kind="document",
                  montant_impute="4820.00", libelle_cible="FC BATIMENT",
                  motif="Devis joint a la convocation pour la resolution 19.2."),
        ], ["DOC-CONVOC"])
        lignes = {l["acte_id"]: l for l in A.matrice(self.instance)}
        self.assertEqual(lignes["A-R12"]["montant_autorise"], "18240.00")
        self.assertEqual(lignes["A-R12"]["montant_lu_sur"], "CORPS_RESOLUTION")
        self.assertEqual(lignes["B-R19-2"]["montant_autorise"], "4820.00")
        self.assertEqual(lignes["B-R19-2"]["montant_lu_sur"], "DEVIS_LIE")
        self.assertEqual(lignes["B-R19-2"]["entreprise_effective"], "FC BATIMENT")

    def test_la_cible_d_un_devis_n_a_pas_la_meme_forme_selon_le_syndic(self) -> None:
        """Une ligne de `devis_cites` chez l'un, un document chez l'autre."""
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("A-R12"), _acte("B-R19-2", numero="19", sous_numero="2"),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("A-R12", "DEVIS_RETENU", "DEVIS-CITE-7", target_kind="devis_cite",
                  montant_impute="18240.00", libelle_cible="WE GROUP"),
            _lien("B-R19-2", "DEVIS_RETENU", "DOC-DEVIS", target_kind="document",
                  montant_impute="4820.00", libelle_cible="FC BATIMENT"),
        ], ["DOC-PV"])
        cellules = {l["acte_id"]: l["cel_devis"] for l in A.matrice(self.instance)}
        self.assertEqual(cellules["A-R12"], "PIECE_PRODUITE")
        self.assertEqual(cellules["B-R19-2"], "PIECE_PRODUITE")

    def test_un_fait_propre_a_un_syndic_ne_prend_pas_de_colonne_du_noyau(self) -> None:
        """`Base de repartition` est enonce par un syndic, absent chez l'autre."""
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("A-R12"), _acte("B-R1", numero="1", doc_id="DOC-PV2"),
        ], ["DOC-PV", "DOC-PV2"])
        A.ecrire(self.instance, A.TABLE_ATTRIBUTS, [{
            "attribut_id": "B-R1|base_repartition", "acte_id": "B-R1",
            "nom": "base_repartition", "valeur": "CHARGES COMMUNES GENERALES",
            "provenance": "SYNDIC_AFFIRME", "page": "1", "ancre": "",
            "doc_id": "DOC-PV2", "origine": "EXTRAIT",
        }], ["DOC-PV2"])
        attributs = A.lire_table(self.instance, A.TABLE_ATTRIBUTS)
        self.assertEqual(len(attributs), 1)
        # L'absence chez le premier syndic n'est pas un defaut: aucun constat.
        codes = {c["code"] for c in A.constats(self.instance)}
        self.assertNotIn("ATTRIBUT_MANQUANT", codes)
        self.assertEqual(
            set(A.lire_table(self.instance, A.TABLE_ACTES)[0]) & {"base_repartition"},
            set(),
        )

    def test_le_noyau_ne_porte_aucune_colonne_de_texte_integral(self) -> None:
        """Les PV du corpus n. 2 nomment opposants et abstentionnistes.

        Une colonne `texte` aurait aspire ces noms dans le magasin de
        gouvernance chez tous les syndics, sans qu'aucun ecran ne le demande.
        """
        colonnes = set()
        for champs, _, _ in __import__(
            "coproscope.modules._actes_schema", fromlist=["TABLES"]
        ).TABLES.values():
            colonnes |= set(champs)
        for interdit in ("texte_integral", "corps", "texte_source", "votants",
                         "opposants", "abstentionnistes"):
            self.assertNotIn(interdit, colonnes)

    def test_les_deux_corpus_se_rangent_dans_le_meme_registre(self) -> None:
        """Un registre unique, l'exercice en colonne: quatre exercices coexistent."""
        lignes = []
        for annee, date_ag in (("2023", "2023-06-19"), ("2024", "2024-06-17"),
                               ("2025", "2025-06-30"), ("2026", "2026-06-29")):
            for numero in ("1", "5", "19"):
                lignes.append(_acte(
                    A.acte_id_resolution(date_ag, numero),
                    date_effet=date_ag, exercice=annee, ag_id=f"AG-{date_ag}",
                    numero=numero, doc_id=f"DOC-PV-{annee}",
                ))
        A.ecrire(self.instance, A.TABLE_ACTES, lignes,
                 [f"DOC-PV-{a}" for a in ("2023", "2024", "2025", "2026")])
        self.assertEqual(len(A.lire_table(self.instance, A.TABLE_ACTES)), 12)
        de_2024 = A.matrice(self.instance, [("exercice", "eq", "2024")])
        self.assertEqual(len(de_2024), 3)
        # Et une reextraction du seul PV 2026 ne touche pas les trois autres.
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [l for l in lignes if l["exercice"] == "2026"], ["DOC-PV-2026"])
        self.assertEqual(len(A.lire_table(self.instance, A.TABLE_ACTES)), 12)


class FormeSurDonneesReellesTests(unittest.TestCase):
    """La forme du schema, eprouvee contre les volumes deja produits.

    Les instances historiques ne sont pas un etalon de justesse: on s'en sert
    pour eprouver la FORME - volumes, cardinalites, cas degrades - jamais pour
    conclure sur la justesse d'un contenu.
    """

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=False)

    def test_la_charge_mesuree_tient_et_la_file_reste_bornee(self) -> None:
        """118 actes, 78 devis, 700 depenses: la file ne doit pas exploser."""
        actes = [
            _acte(f"ACTE-{n:03d}", numero=str(n), montant_autorise="1000.00",
                  objet=f"Resolution {n} - travaux et contrats")
            for n in range(1, 119)
        ]
        A.ecrire(self.instance, A.TABLE_ACTES, actes, ["DOC-PV"])
        dossiers = [
            _dossier(f"DEP-{n:04d}", montant_ttc=f"{100 + n}.00",
                     fournisseur=f"FOURNISSEUR {n % 40}",
                     libelle=f"Prestation {n}")
            for n in range(1, 701)
        ]
        A.ecrire(self.instance, A.TABLE_DOSSIERS, dossiers, ["DOC-FAC"])
        # 118 resolutions adoptees sans execution + 700 euros sans acte.
        tous = A.constats(self.instance)
        self.assertEqual(len(tous), 818)
        # La file bornee ne rend que les vingt plus chers, et rien n'est cache
        # en silence: l'appelant connait les deux nombres.
        vingt = A.constats(self.instance, limite=20)
        self.assertEqual(len(vingt), 20)
        self.assertGreaterEqual(vingt[0]["montant_en_jeu"], vingt[-1]["montant_en_jeu"])

    def test_deux_assemblees_de_meme_cardinalite_ne_sont_pas_reputees_identiques(self) -> None:
        """Mesure reelle: 55 lignes datees et 55 lignes sans date lue.

        Le schema ne les fusionne pas - conclure sur une ressemblance est le
        defaut que ce lot combat - mais il les distingue et il le dit.
        """
        datees = [
            _acte(A.acte_id_resolution("2024-07-03", str(n)), numero=str(n),
                  doc_id="DOC-7139EDAD85E4")
            for n in range(1, 56)
        ]
        sans_date = [
            _acte(A.acte_id_resolution("", str(n), doc_id="DOC-729CCCF88863"),
                  numero=str(n), date_effet="", ag_id="", doc_id="DOC-729CCCF88863")
            for n in range(1, 56)
        ]
        A.ecrire(self.instance, A.TABLE_ACTES, datees + sans_date,
                 ["DOC-7139EDAD85E4", "DOC-729CCCF88863"])
        self.assertEqual(len(A.lire_table(self.instance, A.TABLE_ACTES)), 110)
        constats = [c for c in A.constats(self.instance) if c["code"] == "PV_SANS_DATE_LUE"]
        self.assertEqual(len(constats), 1)
        self.assertEqual(constats[0]["sujet_id"], "DOC-729CCCF88863")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
