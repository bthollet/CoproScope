from __future__ import annotations

import unittest

from coproscope.modules import resolutions as R


CLOTURE_OK = "En vertu de quoi cette resolution est adoptee."
CLOTURE_KO = "En vertu de quoi cette resolution est rejetee."
PASSERELLE = (
    "Il est passe au vote suivant l'article 25-1 : lorsque l'assemblee generale "
    "n'a pas decide a la majorite de l'article 25 mais que le projet a recueilli "
    "au moins le tiers des voix, la meme assemblee peut decider a la majorite "
    "prevue a l'article 24 en procedant immediatement a un second vote."
)


def pv(*blocs: str) -> str:
    return "\n".join(blocs)


class SousNumeroTests(unittest.TestCase):
    """Le degre de la numerotation hierarchique du second cabinet.

    Mesure du 2026-09-04 sur ses vingt-deux textes: cinquante-neuf references
    « Resolution n°X[.Y] » distinctes, dont huit hierarchiques. Le registre n'a
    eu longtemps aucune colonne `sous_numero`, si bien que 11, 11.1, 11.2, 11.6,
    11.7 et 11.8 fabriquaient SIX fois le meme identifiant: douze resolutions se
    reduisaient a quatre, et `INSERT OR REPLACE` jetait les huit autres sans
    lever d'erreur. Ce sont precisement les sous-resolutions qui portent chacune
    leur devis, donc les seules capables de repondre a « cet euro, qui l'a
    autorise ».
    """

    def test_le_degre_est_lu_et_ne_se_confond_pas_avec_le_numero(self) -> None:
        texte = pv(
            "Resolution n°11 : choix du prestataire de ravalement. (Article 24)",
            "Resolution n°11.1 : offre de la premiere entreprise. (Article 24)",
            "Resolution n°11.2 : offre de la deuxieme entreprise. (Article 24)",
        )
        res = R.parse_resolutions(texte)
        self.assertEqual([r.numero for r in res], [11, 11, 11])
        self.assertEqual([r.sous_numero for r in res], ["", "1", "2"])

    def test_les_sous_resolutions_ne_partagent_pas_leur_identifiant(self) -> None:
        texte = pv(
            "Resolution n°11 : choix du prestataire. (Article 24)",
            "Resolution n°11.1 : offre A. (Article 24)",
            "Resolution n°11.2 : offre B. (Article 24)",
            "Resolution n°11.6 : offre C. (Article 24)",
        )
        rows = R.to_rows(
            R.parse_resolutions(texte), ag_id="AG-2026-06-29", doc_id="DOC-CONV"
        )
        identifiants = [r["resolution_id"] for r in rows]
        self.assertEqual(
            len(set(identifiants)),
            4,
            "quatre projets a voter, quatre cles: sans le degre, trois "
            "disparaissent au stockage sans qu'aucune erreur ne soit levee",
        )
        self.assertIn("AG-2026-06-29-R011", identifiants)
        self.assertIn("AG-2026-06-29-R011.01", identifiants)

    def test_un_degre_cite_dans_le_corps_ne_renumerote_pas_le_point_courant(self) -> None:
        """La fenetre de lecture est bornee a la tete du segment: au-dela, le
        corps cite d'AUTRES resolutions."""
        texte = pv(
            "Resolution n°7 : approbation des comptes. (Article 24) "
            + "Le conseil rappelle les termes de la resolution n°11.4 votee en 2025. "
            + CLOTURE_OK,
            f"Resolution n°8 : quitus au syndic. (Article 24) {CLOTURE_OK}",
        )
        res = R.parse_resolutions(texte)
        self.assertEqual(res[0].sous_numero, "")


class SegmentationTests(unittest.TestCase):
    def test_numerotation_et_ordre(self) -> None:
        texte = pv(
            f"1° - Constitution du bureau. (Article 24) {CLOTURE_OK}",
            f"2° - Election du secretaire. (Article 24) {CLOTURE_OK}",
            f"3° - Approbation des comptes. (Article 24) {CLOTURE_KO}",
        )
        res = R.parse_resolutions(texte)
        self.assertEqual([r.numero for r in res], [1, 2, 3])
        self.assertEqual([r.position for r in res], [1, 2, 3])

    def test_trou_de_sequence_signale(self) -> None:
        texte = pv(f"1° - Un. {CLOTURE_OK}", f"4° - Quatre. {CLOTURE_OK}")
        res = R.parse_resolutions(texte)
        self.assertEqual(R.sequence_gaps(res), [2, 3])

    def test_objet_limite_a_la_premiere_phrase(self) -> None:
        texte = f"7° - Vote des travaux de toiture. L'assemblee expose ensuite le detail. {CLOTURE_OK}"
        res = R.parse_resolutions(texte)
        self.assertEqual(res[0].objet, "Vote des travaux de toiture.")

    def test_texte_sans_resolution_ne_produit_rien(self) -> None:
        self.assertEqual(R.parse_resolutions("Aucune numerotation ici."), [])


class IssueTests(unittest.TestCase):
    def test_adoptee_et_rejetee(self) -> None:
        res = R.parse_resolutions(pv(f"1° - Un. {CLOTURE_OK}", f"2° - Deux. {CLOTURE_KO}"))
        self.assertEqual([r.resultat for r in res], ["ADOPTEE", "REJETEE"])

    def test_pas_de_vote_explicite(self) -> None:
        res = R.parse_resolutions("5° - Election du president du conseil syndical. Pas de vote.")
        self.assertEqual(res[0].resultat, R.PAS_DE_VOTE)

    def test_vote_compte_mais_adoption_non_enoncee(self) -> None:
        texte = (
            "28° - Vote du budget previsionnel. (Article 24) "
            "Ont vote pour : 4746/10.000 Ont vote contre : TOTAL : 105"
        )
        res = R.parse_resolutions(texte)
        self.assertEqual(res[0].resultat, R.VOTE_SANS_FORMULE)
        self.assertEqual(res[0].voix_pour, "4746")
        self.assertEqual(res[0].voix_contre, "105")

    def test_ni_vote_ni_formule(self) -> None:
        res = R.parse_resolutions("9° - Question diverse sans suite.")
        self.assertEqual(res[0].resultat, R.SANS_ISSUE)
        self.assertEqual(res[0].confiance, "faible")

    def test_les_trois_absences_ne_sont_pas_confondues(self) -> None:
        res = R.parse_resolutions(
            pv(
                "1° - Sans suite.",
                "2° - Non soumise. Pas de vote.",
                "3° - Votee. (Article 24) Ont vote pour : 4000/10.000",
            )
        )
        self.assertEqual(
            [r.resultat for r in res],
            [R.SANS_ISSUE, R.PAS_DE_VOTE, R.VOTE_SANS_FORMULE],
        )


class MajoriteTests(unittest.TestCase):
    def test_majorite_annoncee_sans_passerelle(self) -> None:
        res = R.parse_resolutions(f"3° - Travaux. (Article 25) {CLOTURE_OK}")
        self.assertEqual(res[0].majorite_annoncee, "25")
        self.assertEqual(res[0].majorite_appliquee, "25")
        self.assertFalse(res[0].passerelle_utilisee)

    def test_passerelle_utilisee_bascule_la_majorite_appliquee(self) -> None:
        texte = f"4° - Travaux. (Article 25) Ont vote pour : 4000/10.000 {PASSERELLE} {CLOTURE_OK}"
        res = R.parse_resolutions(texte)
        self.assertEqual(res[0].majorite_annoncee, "25")
        self.assertEqual(res[0].majorite_appliquee, "24")
        self.assertTrue(res[0].passerelle_utilisee)

    def test_passerelle_citee_sans_etre_utilisee(self) -> None:
        texte = f"5° - Travaux. (Articles 25 et 25-1) {CLOTURE_OK}"
        res = R.parse_resolutions(texte)
        self.assertTrue(res[0].passerelle_citee)
        self.assertFalse(res[0].passerelle_utilisee)
        self.assertEqual(res[0].majorite_appliquee, "25")

    def test_larticle_25_1_nest_jamais_la_majorite_annoncee(self) -> None:
        texte = f"6° - Travaux. (Article 25-1 puis Article 25) {CLOTURE_OK}"
        self.assertEqual(R.parse_resolutions(texte)[0].majorite_annoncee, "25")


class VoixTests(unittest.TestCase):
    def test_decomptes_nommes(self) -> None:
        texte = (
            "2° - Travaux. (Article 24) Ont vote pour : 4 746/10.000 "
            "Ont vote contre : TOTAL : 105 Se sont abstenus : 57 " + CLOTURE_OK
        )
        res = R.parse_resolutions(texte)[0]
        self.assertEqual(res.voix_pour, "4746")
        self.assertEqual(res.voix_contre, "105")
        self.assertEqual(res.voix_abstention, "57")
        self.assertEqual(res.base_voix, "10000")

    def test_une_date_nest_pas_une_base_de_tantiemes(self) -> None:
        """Regression: "du 01/01/2024" etait lu comme 1 voix sur 2024."""
        texte = f"8° - Budget de l'exercice du 01/01/2024 au 31/12/2024. (Article 24) {CLOTURE_OK}"
        res = R.parse_resolutions(texte)[0]
        self.assertEqual(res.base_voix, "")
        self.assertEqual(res.voix_relevees, [])

    def test_base_millieme_acceptee(self) -> None:
        texte = f"9° - Travaux. (Article 24) Ont vote pour : 600/1.000 {CLOTURE_OK}"
        self.assertEqual(R.parse_resolutions(texte)[0].base_voix, "1000")


class SortieTests(unittest.TestCase):
    def test_lignes_completes_et_identifiants(self) -> None:
        res = R.parse_resolutions(f"12° - Travaux. (Article 24) {CLOTURE_OK}")
        rows = R.to_rows(res, ag_id="AG-2024-07-03", doc_id="DOC-TEST")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["resolution_id"], "AG-2024-07-03-R012")
        self.assertEqual(sorted(rows[0]), sorted(R.RESOLUTION_FIELDS))

    def test_resume_compte_chaque_categorie(self) -> None:
        res = R.parse_resolutions(
            pv(
                f"1° - Un. (Article 24) {CLOTURE_OK}",
                f"2° - Deux. (Article 24) {CLOTURE_KO}",
                "3° - Trois. Pas de vote.",
            )
        )
        resume = R.summarize(res)
        self.assertEqual(resume["total"], 3)
        self.assertEqual(resume["adoptees"], 1)
        self.assertEqual(resume["rejetees"], 1)
        self.assertEqual(resume["pas_de_vote"], 1)
        self.assertEqual(resume["trous_sequence"], [])


class CoffreNonDeclareTests(unittest.TestCase):
    def test_instance_sans_coffre_le_dit_au_lieu_dechouer(self) -> None:
        """Depuis la bascule SQLite du 2026-09-03, c'est le coffre qui manque."""
        import tempfile
        from pathlib import Path

        entrepot = Path(tempfile.mkdtemp())
        registre = entrepot / "registre_documents.csv"
        registre.write_text("doc_id,document_type,text_path\n", encoding="utf-8")

        class InstanceSansCoffre:
            def register(self, name: str):
                if name == "documents":
                    return registre
                raise KeyError(name)

            def settings(self):
                return {}

        resume = R.build_register(InstanceSansCoffre(), None)
        self.assertTrue(resume["coffre_non_declare"])
        self.assertEqual(resume["resolutions"], 0)


class CalibrageEtRepliTests(unittest.TestCase):
    def test_calibrage_retrouve_la_signature_sans_qu_on_l_ecrive(self) -> None:
        texte = pv(*[f"{n}° - Objet {n}. (Article 24) {CLOTURE_OK}" for n in range(1, 8)])
        calibre = R.calibrate(texte)
        self.assertIsNotNone(calibre)
        self.assertEqual(calibre["signature"], "°-")
        self.assertEqual(calibre["suite"], 7)

    def test_calibrage_refuse_plutot_que_d_inventer(self) -> None:
        self.assertIsNone(R.calibrate("Un texte sans la moindre resolution."))

    def test_repli_par_cloture_quand_aucune_numerotation(self) -> None:
        texte = pv(*[f"Objet sans numero. (Article 24) {CLOTURE_OK}" for _ in range(4)])
        res = R.parse_resolutions(texte)
        self.assertEqual(len(res), 4)
        self.assertEqual([r.numerotation for r in res], ["deduite"] * 4)
        self.assertEqual([r.numero for r in res], [1, 2, 3, 4])

    def test_numerotation_deduite_plafonne_la_confiance(self) -> None:
        texte = pv(*[f"Objet. (Article 24) Ont vote pour : 4000/10.000 {CLOTURE_OK}" for _ in range(4)])
        res = R.parse_resolutions(texte)
        self.assertTrue(all(r.confiance == "moyenne" for r in res))

    def test_numerotation_qui_ne_couvre_pas_le_document_cede_au_repli(self) -> None:
        """Regression: 42 numeros lus pour 84 clotures, la moitie du PV manquait."""
        blocs = []
        for n in range(1, 9):
            blocs.append(f"{n}- Objet numerote. (Article 24) {CLOTURE_OK}")
            blocs.append(f"Objet non numerote. (Article 24) {CLOTURE_OK}")
        res = R.parse_resolutions(pv(*blocs))
        self.assertEqual(len(res), 16)
        self.assertEqual(res[0].numerotation, "deduite")


class EtatEtOrigineTests(unittest.TestCase):
    """Colonnes demandees par la conversation convocations, le 2026-09-02."""

    def _une(self, **kw):
        res = R.parse_resolutions(f"3° - Travaux de toiture. (Article 24) "
                                  f"Ont vote pour : 4000/10.000 {CLOTURE_OK}")
        return R.to_rows(res, ag_id="AG-2024-07-03", doc_id="DOC-T", **kw)[0]

    def test_constatee_par_defaut(self) -> None:
        ligne = self._une()
        self.assertEqual(ligne["etat"], "CONSTATEE")
        self.assertEqual(ligne["origine"], "EXTRAIT")
        self.assertEqual(ligne["resultat"], "ADOPTEE")
        self.assertEqual(ligne["voix_pour"], "4000")

    def test_projetee_ne_porte_jamais_d_issue(self) -> None:
        """La garde qui manquait: une convocation rendait 14 "adoptees"."""
        ligne = self._une(etat="PROJETEE")
        self.assertEqual(ligne["etat"], "PROJETEE")
        self.assertEqual(ligne["resultat"], "PROJET")

    def test_projetee_ne_porte_jamais_de_voix(self) -> None:
        ligne = self._une(etat="PROJETEE")
        for champ in ("voix_pour", "voix_contre", "voix_abstention", "base_voix", "voix_relevees"):
            self.assertEqual(ligne[champ], "", champ)

    def test_origine_corrigee_se_declare(self) -> None:
        self.assertEqual(self._une(origine="CORRIGE_HUMAIN")["origine"], "CORRIGE_HUMAIN")

    def test_les_deux_colonnes_sont_au_schema(self) -> None:
        self.assertIn("etat", R.RESOLUTION_FIELDS)
        self.assertIn("origine", R.RESOLUTION_FIELDS)


class SeuilsEnVigueurTests(unittest.TestCase):
    """Controle calendaire de l'article 21: quel seuil s'applique a quelle date."""

    def _ligne(self, seuil, du, au, montant, resultat="ADOPTEE"):
        return {
            "qualifications": seuil, "resultat": resultat, "valide_du": du,
            "valide_au": au, "montant_seuil": montant,
        }

    def test_seuil_en_vigueur_a_la_date(self) -> None:
        lignes = [self._ligne("SEUIL_MISE_EN_CONCURRENCE", "2023-06-28", "2024-08-28", "1000")]
        etat = R.seuils_en_vigueur(lignes, "2024-07-03")[1]
        self.assertTrue(etat["en_vigueur"])
        self.assertEqual(etat["montant"], "1000")

    def test_le_seuil_vote_le_jour_meme_ne_regit_pas_le_passe(self) -> None:
        """Le coeur du controle: 1 000 EUR de 2023, pas 2 000 EUR votes ce jour-la."""
        lignes = [
            self._ligne("SEUIL_MISE_EN_CONCURRENCE", "2023-06-28", "2024-08-28", "1000"),
            self._ligne("SEUIL_MISE_EN_CONCURRENCE", "2024-07-03", "2027-07-03", "2000"),
        ]
        self.assertEqual(R.seuils_en_vigueur(lignes, "2024-07-01")[1]["montant"], "1000")

    def test_expiration_sans_renouvellement_est_signalee(self) -> None:
        lignes = [self._ligne("SEUIL_CONSULTATION_CS", "2024-07-03", "2026-07-03", "1000")]
        etat = R.seuils_en_vigueur(lignes, "2026-09-03")[0]
        self.assertFalse(etat["en_vigueur"])
        self.assertTrue(etat["expire_sans_renouvellement"])
        self.assertEqual(etat["expire_le"], "2026-07-03")

    def test_un_seuil_rejete_ne_compte_pas(self) -> None:
        lignes = [self._ligne("SEUIL_CONSULTATION_CS", "2021-09-20", "2023-09-20", "1000", "REJETEE")]
        self.assertFalse(R.seuils_en_vigueur(lignes, "2022-01-01")[0]["en_vigueur"])

    def test_sans_terme_le_doute_remonte(self) -> None:
        lignes = [self._ligne("SEUIL_MISE_EN_CONCURRENCE", "2022-07-20", "", "1000")]
        etat = R.seuils_en_vigueur(lignes, "2024-07-03")[1]
        self.assertTrue(etat["sans_terme"])
        self.assertFalse(etat["expire_sans_renouvellement"])


class NumerotationPrefixeTests(unittest.TestCase):
    """Troisieme forme, mesuree sur un autre syndic le 2026-09-03."""

    def test_resolution_n_numero_est_reconnue(self) -> None:
        texte = pv(
            "Resolution n°1 : Designation du president de seance (Article 24)",
            "Resolution n°2 : Designation du scrutateur (Article 24)",
            "Resolution n°3 : Designation du secretaire (Article 24)",
        )
        res = R.parse_resolutions(texte)
        self.assertEqual([r.numero for r in res], [1, 2, 3])

    def test_une_convocation_ne_produit_aucune_issue(self) -> None:
        """Elle porte des projets: sans formule de cloture, aucune adoption."""
        texte = pv(
            "Resolution n°1 : Designation du president (Article 24) "
            "L'assemblee generale designe En qualite de",
            "Resolution n°2 : Approbation des comptes (Article 24) "
            "L'assemblee generale approuve",
        )
        res = R.parse_resolutions(texte)
        self.assertEqual(len(res), 2)
        self.assertEqual(R.summarize(res)["adoptees"], 0)
        self.assertEqual(R.summarize(res)["rejetees"], 0)

    def test_la_forme_prefixe_marche_sans_ancre_de_cloture(self) -> None:
        """Le calibrage s'ancre sur les clotures; une convocation n'en a pas."""
        texte = pv(*[f"Resolution n°{n} : Objet {n} (Article 24)" for n in range(1, 6)])
        self.assertIsNone(R.calibrate(texte))
        self.assertEqual(len(R.parse_resolutions(texte)), 5)


if __name__ == "__main__":
    unittest.main()


class ReplideClotureTests(unittest.TestCase):
    """Le repli par cloture, employe quand aucune numerotation ne se degage.

    Mesure du 2026-09-03 sur les huit assemblees Tilleuls: en coupant au
    DEBUT de la formule de cloture, chaque resolution heritait de l'issue de la
    precedente. 112 issues sur 432 etaient fausses, dont 102 inversions
    adoptee/rejetee, et 337 intitules sur 432 affichaient la formule de vote de
    la resolution d'avant a la place du titre.
    """

    # Sans numerotation exploitable en tete de bloc, seules les clotures
    # peuvent servir d'ancre - c'est la situation du repli.
    TEXTE = (
        "13 - Vote du montant a partir duquel le conseil est consulte.\n"
        "Pas de candidat. En vertu de quoi cette resolution est sans objet\n"
        "14 - Vote du seuil de consultation du conseil syndical.\n"
        "L'assemblee generale decide de fixer a 500 euros TTC le seuil.\n"
        "Ont vote pour : 5586/10000\n"
        "En vertu de quoi cette resolution est adoptee.\n"
        "15 - Fixation du montant de mise en concurrence.\n"
        "L'assemblee generale decide de fixer a 2000 euros TTC le montant.\n"
        "Ont vote contre : 6000/10000\n"
        "En vertu de quoi cette resolution est rejetee.\n"
    )

    def test_chaque_resolution_porte_sa_propre_issue(self) -> None:
        issues = [r.resultat for r in R.parse_resolutions(self.TEXTE)]
        self.assertEqual(issues, ["SANS_OBJET", "ADOPTEE", "REJETEE"])

    def test_l_intitule_est_le_titre_et_non_la_cloture_precedente(self) -> None:
        res = R.parse_resolutions(self.TEXTE)
        for resolution in res:
            self.assertNotIn("cette resolution est", (resolution.objet or "").lower())
        self.assertIn("seuil de consultation", res[1].objet)
        self.assertIn("mise en concurrence", res[2].objet)

    def test_le_montant_lu_est_celui_de_la_bonne_resolution(self) -> None:
        res = R.parse_resolutions(self.TEXTE)
        self.assertEqual(res[1].montant_seuil, "500")
        self.assertEqual(res[2].montant_seuil, "2000")


class RepriseSeuilAnterieurTests(unittest.TestCase):
    """Un seuil ancien sans terme, exhume par l'expiration d'un seuil recent.

    Cas reel Tilleuls: 500 EUR votes en 2022 sans terme, 1 000 EUR votes en
    2024 pour 24 mois. Passe le 03/07/2026, le calendrier seul rend le seuil de
    2022 "en vigueur" - ce qui revient a decider qu'il reprend la main. La
    question est juridique; la fonction la signale au lieu de la trancher.
    """

    def _ligne(self, du, au, montant):
        return {
            "qualifications": "SEUIL_CONSULTATION_CS", "resultat": "ADOPTEE",
            "valide_du": du, "valide_au": au, "montant_seuil": montant,
        }

    LIGNES = property(lambda self: [
        self._ligne("2022-07-20", "", "500"),
        self._ligne("2024-07-03", "2026-07-03", "1000"),
    ])

    def test_avant_expiration_le_seuil_recent_prime(self) -> None:
        etat = R.seuils_en_vigueur(self.LIGNES, "2026-06-16")[0]
        self.assertEqual(etat["montant"], "1000")
        self.assertFalse(etat["reprise_seuil_anterieur"])

    def test_apres_expiration_la_reprise_est_signalee(self) -> None:
        etat = R.seuils_en_vigueur(self.LIGNES, "2026-09-03")[0]
        self.assertEqual(etat["montant"], "500")
        self.assertTrue(etat["reprise_seuil_anterieur"])
        self.assertEqual(etat["expire_le"], "2026-07-03")

    def test_sans_seuil_anterieur_il_n_y_a_pas_de_reprise(self) -> None:
        etat = R.seuils_en_vigueur([self._ligne("2024-07-03", "2026-07-03", "1000")], "2026-09-03")[0]
        self.assertFalse(etat["reprise_seuil_anterieur"])
        self.assertTrue(etat["expire_sans_renouvellement"])


class SeuilsConcurrentsTests(unittest.TestCase):
    """Deux seuils adoptes actifs a la meme date.

    Signale le 2026-09-03 par la conversation factures: la question ne commence
    pas a l'expiration du seuil recent, mais des son vote. Sur le corpus
    Tilleuls, 500 EUR sans terme et 1 000 EUR pour 24 mois sont actifs
    ensemble du 04/07/2024 au 03/07/2026 - deux exercices ou le montant retenu
    resulte d'un choix tacite.
    """

    def _ligne(self, du, au, montant):
        return {
            "qualifications": "SEUIL_CONSULTATION_CS", "resultat": "ADOPTEE",
            "valide_du": du, "valide_au": au, "montant_seuil": montant,
        }

    def _corpus(self):
        return [self._ligne("2022-07-20", "", "500"),
                self._ligne("2024-07-03", "2026-07-03", "1000")]

    def test_le_seuil_ancien_sans_terme_reste_signale(self) -> None:
        etat = R.seuils_en_vigueur(self._corpus(), "2025-06-01")[0]
        self.assertEqual(etat["montant"], "1000")
        self.assertEqual(
            etat["seuils_concurrents"],
            [{"montant": "500", "valide_du": "2022-07-20", "valide_au": ""}],
        )

    def test_un_seul_seuil_actif_ne_signale_aucune_concurrence(self) -> None:
        lignes = [self._ligne("2024-07-03", "2026-07-03", "1000")]
        self.assertEqual(R.seuils_en_vigueur(lignes, "2025-06-01")[0]["seuils_concurrents"], [])

    def test_avant_le_second_vote_il_n_y_a_pas_de_concurrence(self) -> None:
        etat = R.seuils_en_vigueur(self._corpus(), "2023-01-01")[0]
        self.assertEqual(etat["montant"], "500")
        self.assertEqual(etat["seuils_concurrents"], [])


class NatureAssembleeTests(unittest.TestCase):
    """Le tri se fait sur le contenu, pas sur l'etiquette `document_type`.

    Mesure du 2026-09-03 sur `tilleuls_test`: parmi 15 documents etiquetes
    `PV_AG`, onze etaient des fichiers de travail de CoproScope, et trois quarts
    du seul proces-verbal reel etaient etiquetes ailleurs - un morceau en
    `Devis`, un autre en `A_CLASSER`. Le tri par contenu remonte de 4 a 9
    documents lus et rejette les onze.
    """

    def test_une_serie_de_clotures_est_un_proces_verbal(self) -> None:
        texte = pv(
            f"1° - Constitution du bureau. (Article 24) {CLOTURE_OK}",
            f"2° - Election du secretaire. (Article 24) {CLOTURE_OK}",
            f"3° - Approbation des comptes. (Article 24) {CLOTURE_KO}",
        )
        self.assertEqual(R.nature_assemblee(texte), "PV_AG")

    def test_des_projets_sans_aucune_cloture_sont_une_convocation(self) -> None:
        texte = pv(*[f"Resolution n°{n} : Objet {n} (Article 24)" for n in range(1, 6)])
        self.assertEqual(R.nature_assemblee(texte), "CONVOCATION")

    def test_un_document_sans_resolution_n_est_ni_l_un_ni_l_autre(self) -> None:
        self.assertEqual(R.nature_assemblee("Facture n°42 du 3 mars, 1 200 euros."), "AUTRE")

    def test_une_seule_cloution_ne_suffit_pas(self) -> None:
        """Une lettre peut citer une resolution sans en porter la serie."""
        texte = "Je conteste la resolution 12. En vertu de quoi cette resolution est adoptee."
        self.assertEqual(R.nature_assemblee(texte), "AUTRE")


DEMANDE_INSCRIPTION = pv(
    "DEMANDE D'INSCRIPTION DE QUESTIONS A L'ORDRE DU JOUR de la prochaine",
    "assemblee generale, en application de l'article 10 du decret 67-223.",
    "Le coproprietaire soussigne demande l'inscription des projets suivants.",
    "",
    f"1° - Projet : mise en concurrence des contrats. (Article 24) {CLOTURE_OK}",
    f"2° - Projet : communication des pieces. (Article 24) {CLOTURE_OK}",
    f"3° - Projet : audit des comptes. (Article 24) {CLOTURE_OK}",
    f"4° - Projet : reprise des parties communes. (Article 25) {CLOTURE_OK}",
    f"5° - Projet : changement de prestataire. (Article 24) {CLOTURE_OK}",
)


class DemandeInscriptionTests(unittest.TestCase):
    """Une demande d'inscription n'est pas un proces-verbal, meme quand elle
    redige le texte qu'elle veut faire voter.

    **L'axe**: la maniere dont une piece d'assemblee se nomme elle-meme en tete.
    Le decret 67-223 fait dresser un proces-verbal (art. 17), porter un ordre du
    jour a la convocation (art. 9 et 11) et notifier par un coproprietaire une
    demande d'inscription de questions a cet ordre du jour (art. 10).

    **L'invariant**: le corps peut CITER n'importe quelle formule; la tete dit
    ce que la piece EST. Mesure du 2026-09-04: une demande de cinq questions qui
    redige ses projets formule de cloture comprise rendait `PV_AG`, cinq
    resolutions et cinq `ADOPTEE`, qui remontaient a l'ecran de controle en
    actes CONSTATES - cinq votes qui n'avaient jamais eu lieu.

    **Hors des valeurs observees**: un cabinet qui ne se declarerait pas en tete
    retombe sur la regle des clotures en serie. La degradation est celle
    d'aujourd'hui, pas pire.
    """

    def test_une_demande_d_inscription_n_est_pas_un_proces_verbal(self) -> None:
        self.assertEqual(R.nature_assemblee(DEMANDE_INSCRIPTION), "DEMANDE_INSCRIPTION")

    def test_un_proces_verbal_qui_vote_sur_une_demande_reste_un_proces_verbal(self) -> None:
        """Le cas reel qui interdit de chercher la declaration ailleurs qu'en
        tete: une assemblee met aux voix la demande d'un coproprietaire."""
        texte = pv(
            "PROCES-VERBAL DE L'ASSEMBLEE GENERALE DU 3 JUILLET 2024",
            "Etaient soumises les questions dont un coproprietaire avait demande",
            "l'inscription a l'ordre du jour.",
            f"1° - Constitution du bureau. (Article 24) {CLOTURE_OK}",
            f"2° - Election du secretaire. (Article 24) {CLOTURE_OK}",
            f"3° - Approbation des comptes. (Article 24) {CLOTURE_KO}",
        )
        self.assertEqual(R.nature_assemblee(texte), "PV_AG")
