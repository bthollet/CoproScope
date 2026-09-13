"""Ce que le pont VERSE au modele: les faits bruts, et ce qui les a produits.

Suite de `test_pont_actes`, tenue a part pour rester sous la limite de 600
lignes par fichier de code. Les fixtures - instance minimale, ligne de registre,
candidat - sont celles du module principal: les redupliquer ferait diverger deux
corpus de test pour un meme pont.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coproscope.modules import _pont_actes_lignes as L
from coproscope.modules import _pont_actes_source as S

try:  # `discover -s tests` met `tests/` sur le chemin; `-m unittest tests.x` non.
    from test_pont_actes import _Instance, _candidat_resolution, _ecrire_documents
except ImportError:  # pragma: no cover - depend du mode de lancement
    from .test_pont_actes import _Instance, _candidat_resolution, _ecrire_documents


class VoixVerseesTests(unittest.TestCase):
    """Les voix comptees survivent au versement.

    Defaut mesure le 2026-09-04: seize colonnes du registre n'avaient AUCUNE
    destination dans le modele, dont `voix_pour` (129 lignes sur 173),
    `base_voix` (129), `voix_contre` (99) et `passerelle_citee` (173 sur 173).
    `_decompte_voix` les CONSOMMAIT pour produire une part, puis le pont les
    jetait. Consequence: le fait etabli le 2026-09-04 - avec 4 899 presents sur
    10 000, l'article 25 etait arithmetiquement hors d'atteinte, aucune des 21
    resolutions chiffrees n'atteignant 5 001 - restait reconstituable depuis le
    registre et ne l'etait plus depuis le modele. C'est le seul controle qui
    distingue « adoptee » de « declaree adoptee sans atteindre la majorite ».
    """

    def _attributs(self, candidat: S.Candidat) -> dict[str, str]:
        acte = L.ligne_acte(candidat)
        return {a["nom"]: a["valeur"] for a in L.lignes_attributs(candidat, acte)}

    def test_les_voix_enoncees_sont_versees_avec_leur_denominateur(self) -> None:
        attributs = self._attributs(_candidat_resolution())
        self.assertEqual(attributs["voix_pour"], "3000")
        self.assertEqual(attributs["voix_contre"], "500")
        self.assertEqual(attributs["voix_abstention"], "100")
        self.assertEqual(attributs["denominateur_imprime"], "4899")

    def test_une_colonne_vide_n_ecrit_pas_un_zero(self) -> None:
        """Le registre laisse `voix_pour` vide sur 44 lignes sur 173. Ecrire
        « 0 » y transformerait « le PV ne chiffre pas » en « personne n'a vote
        pour »."""
        attributs = self._attributs(_candidat_resolution(voix_pour="", base_voix=""))
        self.assertNotIn("voix_pour", attributs)
        self.assertNotIn("denominateur_imprime", attributs)

    def test_la_passerelle_citee_ne_se_confond_pas_avec_la_passerelle_utilisee(self) -> None:
        """L'une est le regime que le PV ANNONCE, l'autre ce que l'assemblee a
        FAIT. Les confondre perd le seul ecart qui les separe."""
        attributs = self._attributs(
            _candidat_resolution(passerelle_citee="oui", passerelle_utilisee="non")
        )
        self.assertEqual(attributs["passerelle_25_1_citee"], "oui")
        self.assertNotIn("passerelle_25_1_utilisee", attributs)

    def test_un_type_non_reconnu_dit_pourquoi_il_ne_l_est_pas(self) -> None:
        """`ORDINAIRE` garde les sept controles - c'est la bonne regle. Mais la
        RAISON du non-typage etait calculee puis jetee: l'ecran affichait « Type
        non reconnu » sans jamais distinguer un corps non relu d'un marche sans
        montant."""
        candidat = _candidat_resolution(portee="ORDINAIRE")
        candidat.portee = "ORDINAIRE"
        candidat.portee_indices = ["objet de type marche, mais aucun montant lu"]
        attributs = self._attributs(candidat)
        self.assertIn("montant", attributs["portee_non_reconnue_motif"])

    def test_un_type_non_reconnu_sans_indice_n_est_pas_muet(self) -> None:
        candidat = _candidat_resolution(portee="ORDINAIRE")
        candidat.portee = "ORDINAIRE"
        candidat.portee_indices = []
        attributs = self._attributs(candidat)
        self.assertEqual(attributs["portee_non_reconnue_motif"], L.MOTIF_AUCUNE_REGLE)

    def test_un_type_reconnu_ne_porte_aucun_motif_de_non_reconnaissance(self) -> None:
        attributs = self._attributs(_candidat_resolution(portee="ENGAGEMENT_DEPENSE"))
        self.assertNotIn("portee_non_reconnue_motif", attributs)


class RegistreDocumentaireTests(unittest.TestCase):
    """`doc_id` n'est pas une cle du registre documentaire.

    Mesure du 2026-09-04: 3 447 lignes pour 3 105 identifiants distincts, 528
    lignes partageant leur `doc_id` avec une autre - l'identifiant derive du
    CONTENU, donc deux fichiers de meme contenu et de noms differents en
    partagent un. La version anterieure ecrivait `{doc_id: doc for doc in docs}`:
    la DERNIERE ligne gagnait, et quand les deux divergeaient sur `text_path`,
    c'est le texte relu - donc la portee de toutes les resolutions du document -
    qui se decidait sur l'ordre des lignes d'un CSV.
    """

    def test_un_doc_id_partage_par_deux_lignes_divergentes_est_nomme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            instance = _Instance(Path(tmp))
            _ecrire_documents(instance, [
                {"doc_id": "DOC-X", "text_path": "a.txt",
                 "suspected_date": "2024-07-03", "document_type": "PV_AG"},
                {"doc_id": "DOC-X", "text_path": "b.txt",
                 "suspected_date": "2024-07-03", "document_type": "A_CLASSER"},
            ])
            _, ambigus = S.registre_documents(instance)
            self.assertEqual(ambigus, ["DOC-X"])

    def test_la_ligne_retenue_est_celle_qui_porte_un_texte_pas_la_derniere(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            instance = _Instance(Path(tmp))
            _ecrire_documents(instance, [
                {"doc_id": "DOC-X", "text_path": "le_vrai.txt",
                 "suspected_date": "2024-07-03", "document_type": "PV_AG"},
                {"doc_id": "DOC-X", "text_path": "",
                 "suspected_date": "2024-07-03", "document_type": "A_CLASSER"},
            ])
            documents, _ = S.registre_documents(instance)
            self.assertEqual(
                documents["DOC-X"]["text_path"],
                "le_vrai.txt",
                "sinon le document n'est jamais relu et toutes ses resolutions "
                "sortent en type non reconnu, sur un coup de des",
            )

    def test_deux_lignes_identiques_ne_sont_pas_une_ambiguite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            instance = _Instance(Path(tmp))
            _ecrire_documents(instance, [
                {"doc_id": "DOC-X", "text_path": "a.txt",
                 "suspected_date": "2024-07-03", "document_type": "PV_AG"},
                {"doc_id": "DOC-X", "text_path": "a.txt",
                 "suspected_date": "2024-07-03", "document_type": "PV_AG"},
            ])
            self.assertEqual(S.registre_documents(instance)[1], [])

