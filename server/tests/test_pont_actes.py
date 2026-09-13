"""Le pont registre -> modele, eprouve sur ses promesses.

Chaque test porte le nom de la promesse qu'il tient. Un test qui echoue doit
dire ce que le produit ne fait plus, pas quelle fonction a change de signature.

Le verrou que ce pont leve est mesure: au 2026-09-04, deux instances locales
portaient 173 et 118 resolutions au registre, et **zero acte** dans
`actes_autorisation`. L'ecran de controle de gouvernance rendait donc un etat
"le modele relationnel n'a jamais ete alimente" a la place du tableau.
"""

from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import pont_actes
from coproscope.modules import _actes_store as store
from coproscope.modules import _pont_actes_lignes as L
from coproscope.modules import _pont_actes_liens as LIENS
from coproscope.modules import _pont_actes_source as S
from coproscope.modules._actes_schema import TABLE_ACTES, TABLE_ATTRIBUTS, TABLE_LIENS
from coproscope.modules._actes_seuils_normes import NORME_CONSULTATION_CS
from coproscope.modules._resolutions_motifs import RESOLUTION_FIELDS
from coproscope.modules._convocation_motifs import DEVIS_CITE_FIELDS
from coproscope.vault import gouvernance_store as G


# --------------------------------------------------------------------------
# Instance minimale
# --------------------------------------------------------------------------


class _Instance:
    """Le strict necessaire: un coffre local, un registre, un espace de travail."""

    def __init__(self, racine: Path) -> None:
        self.racine = racine
        (racine / "workspace").mkdir(parents=True, exist_ok=True)
        (racine / "registers").mkdir(parents=True, exist_ok=True)

    def settings(self) -> dict:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()

    def root(self, nom: str) -> Path:
        return self.racine / "workspace"

    def register(self, nom: str) -> Path:
        return self.racine / "registers" / "documents.csv"


COLONNES_DOC = ["doc_id", "text_path", "suspected_date", "document_type"]


#: Un proces-verbal minuscule, mais complet: deux resolutions numerotees, une
#: majorite annoncee pour chacune, une formule de cloture, et des voix. Il porte
#: la meme forme que le corpus reel - c'est ce qui permet a `_marqueurs` de le
#: segmenter comme il segmente un vrai document.
PV = """
PROCES-VERBAL DE L'ASSEMBLEE GENERALE DU 3 JUILLET 2024

12° - Ravalement de la facade sud, marche de travaux pour 18 240,00 EUR TTC.
L'assemblee decide de retenir le devis presente.
Majorite de l'article 24
Pour : 3 000 / 4 899 Contre : 500 Abstention : 100
En vertu de quoi cette resolution est adoptee.

13° - Vote du montant des marches et contrats a partir desquels la consultation
du Conseil Syndical est obligatoire par le Syndic.
L'assemblee fixe ce montant a 1 000,00 EUR pour une duree de 24 mois.
Majorite de l'article 25
Pour : 4 000 / 10 000 Contre : 200 Abstention : 0
En vertu de quoi cette resolution est adoptee.
"""


def _ligne_resolution(**kw: str) -> dict[str, str]:
    ligne = {champ: "" for champ in RESOLUTION_FIELDS}
    ligne.update(
        {
            "resolution_id": "AG-2024-07-03-R012",
            "ag_id": "AG-2024-07-03",
            "doc_id": "DOC-PV",
            "numero": "12",
            "objet": "Ravalement de la facade sud",
            "majorite_annoncee": "24",
            "majorite_appliquee": "24",
            "resultat": "ADOPTEE",
            "voix_pour": "3000",
            "voix_contre": "500",
            "voix_abstention": "100",
            "base_voix": "4899",
            "position": "1",
            "etat": "CONSTATEE",
            "origine": "EXTRAIT",
            "confiance": "forte",
        }
    )
    ligne.update(kw)
    return ligne


def _ligne_devis(**kw: str) -> dict[str, str]:
    ligne = {champ: "" for champ in DEVIS_CITE_FIELDS}
    ligne.update(
        {
            "devis_cite_id": "CONV-2026-04-29-D11-1",
            "convocation_id": "CONV-2026-04-29",
            "doc_id": "DOC-CONV",
            "numero": "11",
            "sous_numero": "1",
            "objet": "choix du devis de ravalement des facades",
            "entreprise": "ENTREPRISE ALPHA",
            "montant_ttc": "400000.00",
            "majorite_annoncee": "25",
            "avis_cs_affirme": "oui",
            "origine": "EXTRAIT",
        }
    )
    ligne.update(kw)
    return ligne


def _candidat_devis(**kw: str) -> S.Candidat:
    ligne = _ligne_devis(**kw)
    enonce = S.enonce_du_devis(ligne)
    portee, indices = ("ENGAGEMENT_DEPENSE", [])
    return S.Candidat(
        ligne=ligne, source="DEVIS_CITE", date_ag="2026-04-29",
        segment=enonce, portee=portee, portee_indices=indices,
    )


def _candidat_resolution(segment: str = "", **kw: str) -> S.Candidat:
    return S.Candidat(
        ligne=_ligne_resolution(**kw), source="RESOLUTION",
        date_ag=kw.get("date_ag", "2024-07-03"), segment=segment,
        portee=kw.get("portee", "ENGAGEMENT_DEPENSE"), portee_indices=[],
    )


# --------------------------------------------------------------------------
# L'identite d'un acte
# --------------------------------------------------------------------------


class IdentiteDesActes(unittest.TestCase):
    def test_le_sous_numero_separe_deux_projets_du_meme_point(self) -> None:
        """Quatre offres concurrentes sur le point 11 font quatre actes.

        Sans le sous-numero, `11-1` et `11-2` recevraient le meme identifiant.
        Le second ecraserait le premier a l'insertion, et un montant de plusieurs
        centaines de milliers d'euros disparaitrait sans qu'aucun ecran ne le
        signale. C'est la decision back n. 3 du modele, et elle est mesuree sur
        le corpus reel: 78 sous-points sur une seule convocation.
        """
        un = L.acte_id_du_candidat(_candidat_devis(sous_numero="1"))
        deux = L.acte_id_du_candidat(_candidat_devis(sous_numero="2"))
        self.assertNotEqual(un, deux)
        self.assertTrue(un.endswith("R11-1"), un)

    def test_un_sous_numero_vide_ne_change_pas_l_identifiant(self) -> None:
        """Les identifiants deja produits sur le premier corpus restent valides."""
        self.assertEqual(
            L.acte_id_du_candidat(_candidat_resolution()),
            "ACTE-AG-2024-07-03-R12",
        )

    def test_une_date_d_assemblee_absente_marque_l_identifiant(self) -> None:
        """Un acte sans date ne doit jamais pouvoir passer pour un acte date."""
        candidat = _candidat_resolution()
        candidat.date_ag = ""
        self.assertIn("SANS-DATE", L.acte_id_du_candidat(candidat))

    def test_les_collisions_sont_nommees_et_non_fusionnees(self) -> None:
        """Deux documents qui revendiquent le meme acte sont un fait a remonter.

        Le registre `resolutions` amont les ecrase deja en silence par sa cle
        primaire: sur l'instance a deux exercices, 119 lignes ecrites, 63
        conservees, parce que le meme proces-verbal existe en six exemplaires
        dont cinq blocs qui renumerotent chacun a partir de 1. Le pont ne choisit
        pas a la place d'un humain: il nomme.
        """
        a = L.ligne_acte(_candidat_resolution())
        b = L.ligne_acte(_candidat_resolution(doc_id="DOC-PV-BLOC-2"))
        trouvees = L.collisions([a, b])
        self.assertEqual(list(trouvees), ["ACTE-AG-2024-07-03-R12"])
        self.assertEqual(trouvees["ACTE-AG-2024-07-03-R12"], ["DOC-PV", "DOC-PV-BLOC-2"])


# --------------------------------------------------------------------------
# Les valeurs nommees, jamais les colonnes vides signifiantes
# --------------------------------------------------------------------------


class ValeursNommees(unittest.TestCase):
    def test_une_majorite_absente_devient_une_valeur_nommee(self) -> None:
        """Sans cette traduction, le constat MAJORITE_NON_ENONCEE ne sort jamais.

        `v_constats` cherche litteralement `NON_ENONCEE`. Le registre amont, lui,
        laisse la colonne vide. L'absence de majorite - mesuree une fois sur 55
        au proces-verbal du 03/07/2024 - disparaitrait de l'ecran.
        """
        acte = L.ligne_acte(_candidat_resolution(majorite_annoncee=""))
        self.assertEqual(acte["majorite_annoncee"], "NON_ENONCEE")

    def test_une_resolution_sans_objet_n_est_ni_adoptee_ni_rejetee(self) -> None:
        """`SANS_OBJET` et `REPORTEE` sont des absences de vote, pas des issues."""
        for issue in ("SANS_OBJET", "REPORTEE"):
            acte = L.ligne_acte(_candidat_resolution(resultat=issue))
            self.assertEqual(acte["resultat"], "PAS_DE_VOTE", issue)

    def test_un_projet_de_convocation_n_a_jamais_d_issue_ni_d_etat_constate(self) -> None:
        """Lire une convocation comme un vote fabriquerait des adoptions."""
        acte = L.ligne_acte(_candidat_devis())
        self.assertEqual(acte["etat"], "PROJETEE")
        self.assertEqual(acte["resultat"], "SANS_ISSUE_TRACEE")

    def test_l_exercice_vise_ne_se_confond_pas_avec_celui_de_l_acte(self) -> None:
        """Une assemblee de 2024 arrete des comptes de 2023: deux annees vraies."""
        candidat = _candidat_resolution(
            segment="Approbation des comptes de l'exercice du 01/01/2023 au 31/12/2023."
        )
        acte = L.ligne_acte(candidat)
        noms = {a["nom"]: a["valeur"] for a in L.lignes_attributs(candidat, acte)}
        self.assertEqual(acte["exercice"], "2024")
        self.assertEqual(noms["exercice_vise"], "2023")


# --------------------------------------------------------------------------
# Les voix
# --------------------------------------------------------------------------


class DecompteDesVoix(unittest.TestCase):
    def test_un_pourcentage_sort_quand_l_assiette_est_nommee(self) -> None:
        """Article 24: l'assiette est les voix exprimees, donc pour + contre."""
        candidat = _candidat_resolution()
        attributs = {
            a["nom"]: a["valeur"]
            for a in L.lignes_attributs(candidat, L.ligne_acte(candidat))
        }
        self.assertEqual(attributs["assiette_du_decompte"], "VOIX_EXPRIMEES")
        # 3000 sur 3500 exprimees. Le denominateur imprime, 4899, ne fonde rien.
        self.assertEqual(attributs["part_des_voix_pour"], "85.71")
        self.assertIn("denominateur_imprime_divergent", attributs)

    def test_aucun_pourcentage_quand_l_assiette_reste_inconnue(self) -> None:
        """Article 25: l'assiette est le total des voix du syndicat.

        Le registre ne le porte pas, et le denominateur imprime n'en tient pas
        lieu. Le pont n'ecrit alors aucun pourcentage - c'est la promesse
        centrale de `_decompte_voix`, et le pont n'a pas le droit de la
        contourner en divisant lui-meme deux nombres.
        """
        candidat = _candidat_resolution(
            majorite_annoncee="25", majorite_appliquee="25", base_voix="10000"
        )
        attributs = {
            a["nom"]: a["valeur"]
            for a in L.lignes_attributs(candidat, L.ligne_acte(candidat))
        }
        self.assertEqual(attributs["assiette_du_decompte"], "TOUTES_LES_VOIX")
        self.assertNotIn("part_des_voix_pour", attributs)

    def test_la_passerelle_de_l_article_25_1_reste_visible(self) -> None:
        """Dix-huit adoptions de l'assemblee etalon ne s'expliquent que par elle.

        Avec 4 899 voix presentes sur 10 000, l'article 25 etait arithmetiquement
        hors d'atteinte toute la seance. La seule trace de la passerelle serait
        sinon l'ecart entre deux colonnes de majorite, qu'aucun filtre ne nomme.
        """
        candidat = _candidat_resolution(
            majorite_annoncee="25", majorite_appliquee="24", passerelle_utilisee="oui"
        )
        acte = L.ligne_acte(candidat)
        noms = {a["nom"] for a in L.lignes_attributs(candidat, acte)}
        self.assertIn("passerelle_25_1_utilisee", noms)
        self.assertEqual(acte["majorite_annoncee"], "25")
        self.assertEqual(acte["majorite_appliquee"], "24")


# --------------------------------------------------------------------------
# Les liens
# --------------------------------------------------------------------------


class ForceProbatoireDesLiens(unittest.TestCase):
    def test_un_avis_affirme_sans_piece_ne_devient_jamais_une_preuve(self) -> None:
        """Mesure sur la convocation reelle: 64 avis affirmes, 0 piece produite."""
        candidat = _candidat_devis()
        liens = {
            l["relation"]: l for l in LIENS.liens_du_devis(candidat, L.ligne_acte(candidat))
        }
        self.assertEqual(liens["AVIS_CS"]["force_probatoire"], "AFFIRME_SANS_PIECE")
        self.assertEqual(liens["AVIS_CS"]["provenance"], "SYNDIC_AFFIRME")

    def test_un_devis_sans_montant_lu_reste_a_confirmer(self) -> None:
        candidat = _candidat_devis(montant_ttc="")
        liens = {
            l["relation"]: l for l in LIENS.liens_du_devis(candidat, L.ligne_acte(candidat))
        }
        self.assertEqual(liens["DEVIS_RETENU"]["force_probatoire"], "AFFIRME_SANS_PIECE")
        self.assertTrue(liens["DEVIS_RETENU"]["doute"])

    def test_le_libelle_de_la_cible_est_porte_par_le_lien(self) -> None:
        """La cellule ne doit pas dependre de la forme de la cible pour s'ecrire."""
        candidat = _candidat_devis()
        lien = LIENS.liens_du_devis(candidat, L.ligne_acte(candidat))[0]
        self.assertIn("ENTREPRISE ALPHA", lien["libelle_cible"])
        self.assertEqual(lien["montant_impute"], "400000.00")

    def test_un_seuil_vote_en_2024_couvre_un_engagement_de_2026(self) -> None:
        """Le registre est transverse aux exercices: c'est la premiere decision back.

        Le seuil de l'article 21 est vote le 03/07/2024 pour vingt-quatre mois.
        L'engagement soumis a l'assemblee du 29/04/2026 tombe dans la fenetre.
        Aucune requete ne prend d'annee en parametre pour l'etablir - seule la
        date compte.
        """
        seuil = L.ligne_acte(
            _candidat_resolution(
                numero="26", portee="SEUIL", valide_du="2024-07-03",
                valide_au="2026-07-03", montant_seuil="1000",
            )
        )
        seuil["portee"] = "SEUIL"
        engagement = L.ligne_acte(_candidat_devis())
        liens = LIENS.liens_seuil([seuil, engagement], {}, {})
        self.assertEqual(len(liens), 1)
        self.assertEqual(liens[0]["source_id"], engagement["acte_id"])
        self.assertEqual(liens[0]["target_id"], seuil["acte_id"])
        self.assertEqual(liens[0]["provenance"], "COPROSCOPE_CALCULE")

    def test_un_engagement_hors_fenetre_ne_recoit_aucun_seuil(self) -> None:
        """Un seuil expire n'est pas un seuil applicable, et on ne l'invente pas."""
        seuil = L.ligne_acte(
            _candidat_resolution(
                numero="26", valide_du="2020-01-01", valide_au="2022-01-01",
            )
        )
        seuil["portee"] = "SEUIL"
        engagement = L.ligne_acte(_candidat_devis())
        self.assertEqual(LIENS.liens_seuil([seuil, engagement], {}, {}), [])


# --------------------------------------------------------------------------
# La portee
# --------------------------------------------------------------------------


class PorteeDesActes(unittest.TestCase):
    def test_un_corps_illisible_laisse_tous_les_controles_appliques(self) -> None:
        """Ne pas savoir n'est pas une raison de classer sans suite."""
        with tempfile.TemporaryDirectory() as tmp:
            instance = _Instance(Path(tmp))
            _ecrire_documents(instance, [{"doc_id": "DOC-PV", "text_path": "",
                                          "suspected_date": "2024-07-03",
                                          "document_type": "PV_AG"}])
            G.remplacer_pour_documents(
                instance, RESOLUTION_FIELDS, [_ligne_resolution()], ["DOC-PV"]
            )
            candidats = S.candidats_resolutions(instance)
            self.assertEqual(len(candidats), 1)
            self.assertEqual(candidats[0].portee, "ORDINAIRE")
            self.assertTrue(candidats[0].portee_indices)

    def test_la_segmentation_est_celle_du_registre(self) -> None:
        """Le segment lu ici doit etre celui d'ou le registre a tire ses champs."""
        segments = S.segments_par_position(PV)
        self.assertEqual(sorted(segments), ["1", "2"])
        self.assertIn("Ravalement", segments["1"])
        self.assertIn("consultation", segments["2"])


# --------------------------------------------------------------------------
# Le versement complet
# --------------------------------------------------------------------------


def _ecrire_documents(instance: _Instance, lignes: list[dict[str, str]]) -> None:
    chemin = instance.register("documents")
    with chemin.open("w", encoding="utf-8", newline="") as fichier:
        graveur = csv.DictWriter(fichier, fieldnames=COLONNES_DOC)
        graveur.writeheader()
        graveur.writerows(lignes)


class VersementComplet(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.tmp)
        (self.tmp / "workspace" / "pv.txt").write_text(PV, encoding="utf-8")
        _ecrire_documents(
            self.instance,
            [
                {"doc_id": "DOC-PV", "text_path": "pv.txt",
                 "suspected_date": "2024-07-03", "document_type": "PV_AG"},
                {"doc_id": "DOC-CONV", "text_path": "",
                 "suspected_date": "2026-04-29", "document_type": "Convocation_AG"},
            ],
        )
        G.remplacer_pour_documents(
            self.instance, RESOLUTION_FIELDS,
            [
                _ligne_resolution(),
                _ligne_resolution(
                    resolution_id="AG-2024-07-03-R013", numero="13", position="2",
                    objet="Vote du montant des marches et contrats",
                    qualifications="SEUIL_CONSULTATION_CS",
                    montant_seuil="1000", valide_du="2024-07-03",
                    valide_au="2026-07-03", majorite_annoncee="25",
                    majorite_appliquee="25", voix_pour="4000", voix_contre="200",
                    base_voix="10000",
                ),
            ],
            ["DOC-PV"],
        )
        G.remplacer_pour_documents(
            self.instance, DEVIS_CITE_FIELDS,
            [_ligne_devis(), _ligne_devis(
                devis_cite_id="CONV-2026-04-29-D11-2", sous_numero="2",
                entreprise="ENTREPRISE BETA", montant_ttc="380000.00")],
            ["DOC-CONV"], table="devis_cites",
            cles=("devis_cite_id", "origine"),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_le_modele_relationnel_est_alimente(self) -> None:
        """La condition d'arret du lot: `actes_autorisation` cesse d'etre vide."""
        resume = pont_actes.verser(self.instance)
        self.assertEqual(resume["actes"], 4)
        self.assertEqual(resume["par_etat"], {"CONSTATEE": 2, "PROJETEE": 2})
        self.assertEqual(resume["par_exercice"], {"2024": 2, "2026": 2})
        self.assertEqual(resume["collisions"], {})
        self.assertTrue(store.lire_table(self.instance, TABLE_ACTES))
        self.assertTrue(store.lire_table(self.instance, TABLE_ATTRIBUTS))
        self.assertTrue(store.lire_table(self.instance, TABLE_LIENS))

    def test_l_ecran_recoit_des_lignes_par_la_vue_du_modele(self) -> None:
        """Le tableau doit sortir de `v_matrice_gouvernance`, pas d'un comptage."""
        pont_actes.verser(self.instance)
        lignes = store.lire_vue(self.instance, "v_matrice_gouvernance")
        self.assertEqual(len(lignes), 4)
        projetes = [l for l in lignes if l["etat"] == "PROJETEE"]
        self.assertEqual(len(projetes), 2)
        # Une convocation ne vote pas: sa cellule d'issue ne reclame aucune
        # piece, et sa cellule d'execution ne reproche aucun impaye.
        for ligne in projetes:
            self.assertEqual(ligne["cel_resolution"], "NON_APPLICABLE")
            self.assertEqual(ligne["cel_execution"], "NON_APPLICABLE")

    def test_une_re_extraction_epargne_une_correction_humaine(self) -> None:
        """La garde vit dans la couche partagee; ce test verifie qu'elle tient."""
        pont_actes.verser(self.instance)
        corrige = dict(store.lire_table(self.instance, TABLE_ACTES)[0])
        corrige["origine"] = "CORRIGE_HUMAIN"
        corrige["objet"] = "Objet retabli a la main"
        store.ecrire(self.instance, TABLE_ACTES, [corrige], [])
        pont_actes.verser(self.instance)
        objets = [
            a["objet"] for a in store.lire_table(self.instance, TABLE_ACTES)
            if a["origine"] == "CORRIGE_HUMAIN"
        ]
        self.assertEqual(objets, ["Objet retabli a la main"])

    def test_le_seuil_traverse_les_deux_exercices(self) -> None:
        """Le seuil de 2024 doit couvrir l'engagement soumis en 2026."""
        pont_actes.verser(self.instance)
        # La resolution de seuil de la fixture est qualifiee
        # `SEUIL_CONSULTATION_CS`: depuis `RM-2026-0144` le lien part donc sur
        # la relation de CETTE norme et non plus sur la relation generique, qui
        # ne porte plus que ce qu'on n'a pas su attribuer. Lire encore
        # `SEUIL_APPLICABLE` ici rendrait zero ligne, donc un test vert sur un
        # ensemble vide.
        liens = [
            l for l in store.lire_table(self.instance, TABLE_LIENS)
            if l["relation"] == NORME_CONSULTATION_CS.relation
        ]
        # Trois liens: les deux engagements de 2026, et le marche de travaux
        # vote le meme jour que le seuil - un seuil s'applique aussi a son
        # propre exercice, et l'oublier serait le rendre inoperant l'annee ou il
        # est arrete.
        self.assertEqual(len(liens), 3)
        traversants = [l for l in liens if "2026-04-29" in l["source_id"]]
        self.assertEqual(len(traversants), 2)
        for lien in traversants:
            self.assertIn("2024-07-03", lien["target_id"])


class InstanceSansRien(unittest.TestCase):
    def test_un_registre_vide_se_dit_au_lieu_de_planter(self) -> None:
        """Une instance ou rien n'a ete lu n'est pas une erreur."""
        with tempfile.TemporaryDirectory() as tmp:
            instance = _Instance(Path(tmp))
            _ecrire_documents(instance, [])
            resume = pont_actes.verser(instance)
            self.assertTrue(resume["registre_vide"])
            self.assertEqual(resume["actes"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
