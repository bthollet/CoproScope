"""Les defauts muets du modele des actes - matrice, typologie et magasin.

Suite de `test_actes_silences.py`, coupee a 600 lignes par le garde-fou du
depot. Meme regle: chaque nom dit le fait que le produit ne doit plus pouvoir
produire, et chacun echoue sur le code d'avant le 2026-09-04.

Ce fichier porte les constats qui ne tiennent pas a une ligne de donnee mais a
une declaration: un nom de controle, un article cite, une vue de la base, une
cle primaire.
"""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from coproscope.modules import _actes_store as S
from coproscope.modules import _actes_typologie as T
from coproscope.modules import actes_autorisation as A
from coproscope.vault import gouvernance_store as G


class _Instance:
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
        "valide_du": "", "valide_au": "", "majorite_annoncee": "24",
        "majorite_requise": "24", "majorite_appliquee": "24",
        "resultat": "ADOPTEE", "resolution_id": "", "page": "4", "ancre": "",
        "confiance": "forte", "doc_id": "DOC-PV", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


class _Coffre(unittest.TestCase):
    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=False)

    def codes(self) -> set[str]:
        return {c["code"] for c in A.constats(self.instance)}

    def motif(self, code: str) -> str:
        return next(c["motif"] for c in A.constats(self.instance)
                    if c["code"] == code)


class UnNomDeControleErroneSArreteTests(unittest.TestCase):
    """C030. Un espace de trop rallumait le controle sur les onze portees."""

    def test_un_controle_hors_liste_leve_au_lieu_de_tout_rallumer(self) -> None:
        for faux in ("AVIS_CS ", "avis_cs", "CONTROLE_QUI_NEXISTE_PAS"):
            with self.subTest(faux=faux), self.assertRaises(ValueError):
                T.portees_soumises(faux)

    def test_les_sept_controles_declares_restent_interrogeables(self) -> None:
        for controle in T.CONTROLES:
            self.assertTrue(T.portees_soumises(controle))


class LeControleDeMajoriteEstBrancheTests(_Coffre):
    """C031 / C063 / C093. `CTRL_MAJORITE` etait declare comme septieme
    controle et consulte nulle part: `portees_soumises('MAJORITE')` rendait
    onze portees sans aucun appelant, et la docstring de `CONTROLES` affirmait
    `Sept, pas plus: un controle qui n'a ni cellule ni constat n'existe pas`.

    Un controle declare et non branche est plus dangereux qu'un controle
    absent: sa declaration fait croire qu'il tourne, et un retrait ecrit dans
    HORS_CONTROLE n'aurait eu aucun effet observable.
    """

    def test_la_vue_des_constats_borne_la_majorite_par_un_retrait(self) -> None:
        """La borne est un RETRAIT, pas une admission. C017.

        Ce test exigeait `a.portee IN (<les onze portees>)`. La liste des onze
        est la totalite du vocabulaire, donc l'`IN` ne retirait rien - sauf un
        cas, et c'est celui qui compte: la portee vide, que `_actes_store`
        admet a l'ecriture parce qu'une portee illisible est un fait et non une
        faute. Le vide n'est dans aucune liste, echouait l'`IN`, et sortait du
        constat sans qu'aucune ligne ne le dise. Le controle s'eteignait sur
        les actes les moins bien lus, c'est-a-dire ceux qu'il vise.

        On verifie donc le comportement, pas la forme de la clause: un acte
        sans portee lue reste constate.
        """
        from coproscope.modules._actes_constats import vue_constats

        sql = vue_constats("1 = 1")
        portees = ", ".join(
            "'{0}'".format(p) for p in T.portees_soumises(T.CTRL_MAJORITE))
        self.assertNotIn(f"a.portee IN ({portees})", sql)

    def test_la_majorite_muette_est_constatee_meme_sans_portee_lue(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("A-VIDE", majorite_annoncee="NON_ENONCEE", portee=""),
        ], ["DOC-PV"])
        self.assertIn("MAJORITE_NON_ENONCEE", self.codes())

    def test_le_constat_de_majorite_est_bien_emis_sur_une_portee_soumise(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", majorite_annoncee="NON_ENONCEE")], ["DOC-PV"])
        self.assertIn("MAJORITE_NON_ENONCEE", self.codes())

    def test_chaque_controle_declare_a_un_consommateur(self) -> None:
        """L'invariant que la docstring de CONTROLES annonce, verifie."""
        from coproscope.modules import _actes_vues

        from coproscope.modules._actes_constats import vue_constats

        sql = "".join(_actes_vues.VUES) + vue_constats("1 = 1")
        for controle in T.CONTROLES:
            # Deux formes de consommation, toutes deux reelles: six controles
            # sont des CELLULES de la matrice et se lisent par leur relation de
            # lien; le septieme, MAJORITE, n'a pas de lien a produire - une
            # majorite est annoncee sur l'acte lui-meme - et se consomme par un
            # CONSTAT. Chercher `IN (<portees>)`, comme ce test le faisait,
            # confondait la consommation avec la borne: une borne qui ne retire
            # rien s'ecrit correctement en ne s'ecrivant pas, et le controle
            # passait alors pour non branche.
            consomme = (
                f"l.relation = '{controle}'" in sql
                or f"'{controle}_" in sql
            )
            with self.subTest(controle=controle):
                self.assertTrue(
                    consomme,
                    f"{controle} est declare et aucune vue ni aucun constat "
                    f"ne le consulte")


class LAvisDuConseilSyndicalResteExigibleSurLeSyndicTests(unittest.TestCase):
    """C029. Le retrait citait `le meme alinea`; l'article dit l'inverse.

    Loi 65-557 art. 21 (LEGIARTI000039313574) porte deux phrases: l'assemblee
    arrete un montant des marches et contrats a partir duquel la consultation
    du conseil syndical est obligatoire, puis un montant des marches et
    contrats AUTRES QUE CELUI DE SYNDIC pour la mise en concurrence.
    L'exclusion ne porte que sur la seconde.
    """

    def test_la_consultation_n_est_pas_retiree_a_la_designation_du_syndic(self) -> None:
        self.assertTrue(
            T.controle_applicable("DESIGNATION_SYNDIC", T.CTRL_AVIS_CS))

    def test_la_mise_en_concurrence_reste_retiree(self) -> None:
        """**Meme propriete, mesuree la ou elle vit depuis `RM-2026-0144`.**

        Ce test mesurait `controle_applicable(DESIGNATION_SYNDIC, CTRL_SEUIL)`,
        c'est-a-dire la granularite du CONTROLE - la seule qui existait. Or
        `CTRL_SEUIL` couvre les TROIS relations de seuil, et la docstring de
        cette classe dit justement que *l'exclusion ne porte que sur la
        seconde*. Le retrait au niveau du controle emportait donc aussi le
        seuil de consultation du conseil syndical, que l'alinea n'excepte pas.

        L'exclusion se declare desormais par RELATION. La propriete gardee est
        inchangee; son lieu de mesure a bouge.
        """
        from coproscope.modules._actes_seuils_applicabilite import portees_exclues
        from coproscope.modules._actes_vocabulaire import REL_SEUIL_CONCURRENCE

        self.assertIn(
            "DESIGNATION_SYNDIC", portees_exclues(REL_SEUIL_CONCURRENCE),
            "l'exclusion de l'article 21 al. 2 a disparu: une designation de "
            "syndic redeviendrait soumise a la mise en concurrence")

    def test_et_le_seuil_de_CONSULTATION_n_est_plus_retire_avec_elle(self) -> None:
        """**Le gain du lot, et l'autre moitie de la meme phrase.**

        La classe cite `LEGIARTI000039313574` et ses deux phrases distinctes
        pour conclure que l'exclusion ne vise que la mise en concurrence. Le
        code retirait pourtant les deux seuils d'un coup. Depuis le deplacement
        de granularite, la consultation du conseil syndical reste exigible sur
        une designation de syndic - ce que l'article prevoit.
        """
        from coproscope.modules._actes_seuils_applicabilite import portees_exclues
        from coproscope.modules._actes_vocabulaire import REL_SEUIL_CONSULTATION_CS

        self.assertNotIn(
            "DESIGNATION_SYNDIC", portees_exclues(REL_SEUIL_CONSULTATION_CS))
        self.assertTrue(
            T.controle_applicable("DESIGNATION_SYNDIC", T.CTRL_SEUIL),
            "le retrait au niveau du CONTROLE est revenu: il emporte a nouveau "
            "une obligation que l'alinea ne retire pas")


class UneVueAbsenteOuPerimeeNEstPasUneBaseVideTests(_Coffre):
    """C002. `no such table` couvrait aussi les VUES, et rien dans le produit
    ne rafraichissait jamais les vues."""

    def _verser(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [_acte("A1")], ["DOC-PV"])

    def _sql(self, *instructions: str) -> None:
        # `with sqlite3.connect(...)` gere la transaction et NON la fermeture:
        # sous Windows le fichier resterait verrouille et l'erreur sortirait au
        # nettoyage, pas ici. C'est le defaut que ce depot a deja paye une fois.
        with closing(sqlite3.connect(str(G.store_path(self.instance)))) as cx:
            for sql in instructions:
                cx.execute(sql)
            cx.commit()

    def test_une_vue_supprimee_ne_fait_pas_disparaitre_les_actes(self) -> None:
        self._verser()
        self._sql("DROP VIEW v_matrice_gouvernance")
        self.assertEqual(len(A.lire_vue(self.instance,
                                        "v_matrice_gouvernance")), 1)

    def test_une_vue_d_une_version_anterieure_est_realignee(self) -> None:
        """Le cas dangereux ne leve rien: la vue repond, et repond faux."""
        self._verser()
        self._sql(
            "DROP VIEW v_matrice_gouvernance",
            "CREATE VIEW v_matrice_gouvernance AS "
            "SELECT acte_id, portee FROM v_actes WHERE 0",
        )
        # `assertEqual` et non `assertIn`: tant que les onze vues etaient jugees
        # perimees en permanence, un `assertIn` passait sans rien discriminer.
        with S.connexion(self.instance) as cx:
            self.assertEqual(S.vues_perimees(cx), ["v_matrice_gouvernance"])
        self.assertEqual(len(A.lire_vue(self.instance,
                                        "v_matrice_gouvernance")), 1)

    def test_une_base_sans_table_versee_rend_toujours_une_liste_vide(self) -> None:
        A.preparer(self.instance)
        self.assertEqual(A.lire_vue(self.instance, "v_matrice_gouvernance"), [])


class UneLectureNeReecritPasLesVuesTests(_Coffre):
    """Le cas negatif de C002, celui qui manquait.

    Le mecanisme de C002 - comparer le texte de `sqlite_master` a celui du code
    - ne discriminait rien: `_forme_comparable` opposait
    `CREATE VIEW IF NOT EXISTS v_actes AS ...` a ce que SQLite range,
    `CREATE VIEW v_actes AS ...`, et rendait donc les onze vues perimees sur
    toute base, y compris fraichement preparee. Les deux tests de C002 passaient
    pour la mauvaise raison: `on reconstruit toujours` donne accidentellement la
    bonne reponse sur une vue reellement perimee.

    Consequence mesuree le 2026-09-05 sur le code d'avant: chaque `lire_vue`
    supprimait et recreait les onze vues, donc une lecture etait devenue une
    ecriture inconditionnelle.
    """

    def test_une_base_fraichement_preparee_ne_porte_aucune_vue_perimee(self) -> None:
        A.preparer(self.instance)
        with S.connexion(self.instance) as cx:
            self.assertEqual(S.vues_perimees(cx), [])

    def test_rien_n_est_recree_quand_rien_n_a_derive(self) -> None:
        A.preparer(self.instance)
        self.assertEqual(S.rafraichir_vues(self.instance), [])

    def test_une_base_en_lecture_seule_se_lit_encore(self) -> None:
        """Mesure du 2026-09-05: `OperationalError: attempt to write a readonly
        database`, sur un chemin qui lisait tres bien avant le lot."""
        A.preparer(self.instance)
        chemin = G.store_path(self.instance)
        chemin.chmod(0o444)
        try:
            self.assertEqual(A.lire_vue(self.instance, "v_matrice_gouvernance"), [])
        finally:
            chemin.chmod(0o666)

    def test_un_verrou_d_ecriture_concurrent_n_empeche_pas_la_lecture(self) -> None:
        """Un autre processus qui ECRIT tient un verrou RESERVED: les lecteurs
        passent. Ils ne passaient plus, puisque la lecture ecrivait aussi.

        Le verrou EXCLUSIVE n'est volontairement pas teste: SQLite y refuse
        aussi un `SELECT` nu, avant ce lot comme apres. Mesure du 2026-09-05.
        """
        A.preparer(self.instance)
        with closing(sqlite3.connect(str(G.store_path(self.instance)),
                                     timeout=0.2)) as autre:
            autre.execute("BEGIN IMMEDIATE")
            try:
                self.assertEqual(
                    A.lire_vue(self.instance, "v_matrice_gouvernance"), [])
            finally:
                autre.rollback()


class LeMagasinPartageNAvalePlusUneDeriveDeSchemaTests(unittest.TestCase):
    """C014 / C079 / C080. `except sqlite3.OperationalError: return []` sans
    distinction du message, dans la couche que quatre appelants traversent."""

    CHAMPS = ["resolution_id", "ag_id", "position", "etat", "doc_id", "origine"]

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)
        G.remplacer_pour_documents(self.instance, self.CHAMPS, [{
            "resolution_id": "R1", "ag_id": "AG1", "position": "1",
            "etat": "CONSTATEE", "doc_id": "D1", "origine": "EXTRAIT",
        }], ["D1"])

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=False)

    def test_une_colonne_renommee_ne_rend_pas_un_registre_vide(self) -> None:
        with closing(sqlite3.connect(str(G.store_path(self.instance)))) as cx:
            cx.execute("ALTER TABLE resolutions RENAME COLUMN position TO rang")
            cx.commit()
        with self.assertRaises(G.SchemaDeGouvernanceDivergent):
            G.lire(self.instance)

    def test_une_table_absente_reste_un_registre_vide(self) -> None:
        self.assertEqual(G.lire(self.instance, table="pas_de_table"), [])

    def test_une_colonne_ajoutee_au_modele_apparait_dans_une_base_ancienne(self) -> None:
        """Point 2 du diff propose: sans lui, le point 3 leverait sur toute
        base creee avant l'ajout d'une colonne citee dans un `ordre`."""
        G.remplacer_pour_documents(
            self.instance, [*self.CHAMPS, "numerotation"], [], [])
        with G.connexion(self.instance) as cx:
            colonnes = {r["name"] for r in
                        cx.execute('PRAGMA table_info("resolutions")')}
        self.assertIn("numerotation", colonnes)

    def test_une_cle_primaire_qui_a_derive_le_dit_au_lieu_d_ecraser(self) -> None:
        """Trou non couvert par le diff: elargir la cle dans le code est
        silencieusement sans effet sur une base deja creee."""
        with self.assertRaises(G.SchemaDeGouvernanceDivergent):
            G.remplacer_pour_documents(
                self.instance, self.CHAMPS, [],
                [], cles=("resolution_id", "origine"))


class AucunMotifDeConstatNeRecopieUnObjetDeResolutionTests(_Coffre):
    """C090. `objet` est du texte libre, et la resolution 35 de l'etalon est
    une demande individuelle dont l'intitule nomme le demandeur et son lot."""

    NOMME = "Demande individuelle de la coproprietaire du lot 214"

    def test_ni_le_fondement_ni_l_execution_ne_recopient_l_objet(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-CS", nature="DECISION_CS_DELEGUEE", objet=self.NOMME),
            _acte("ACTE-EXE", portee="ENGAGEMENT_DEPENSE", numero="13",
                  montant_autorise="1000.00", objet=self.NOMME),
        ], ["DOC-PV"])
        for constat in A.constats(self.instance):
            self.assertNotIn("lot 214", constat["motif"], constat["code"])

    def test_deux_constats_du_meme_code_gardent_des_motifs_distincts(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-A", portee="ENGAGEMENT_DEPENSE",
                  montant_autorise="1000.00"),
            _acte("ACTE-B", portee="ENGAGEMENT_DEPENSE", numero="13",
                  montant_autorise="1000.00"),
        ], ["DOC-PV"])
        motifs = [c["motif"] for c in A.constats(self.instance)
                  if c["code"] == "ACTE_SANS_EXECUTION"]
        self.assertEqual(len(motifs), 2)
        self.assertEqual(len(set(motifs)), 2)


class LaDivergenceHumaineCouvreLeModeleTests(_Coffre):
    """C069. Cinq champs compares sur vingt-six: la promesse `l'ecart entre ce
    que la machine a lu et ce qu'un humain a corrige est lui-meme une
    information` ne valait que pour un cinquieme du modele."""

    def test_une_correction_sur_l_entreprise_ou_la_majorite_est_une_divergence(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", entreprise="LUE PAR LA MACHINE",
                        majorite_annoncee="24")], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", entreprise="CORRIGEE PAR L HUMAIN",
                        majorite_annoncee="25", origine="CORRIGE_HUMAIN")],
                 [])  # une correction humaine ne derive d'aucun document
        champs = {l["champ"] for l
                  in A.lire_vue(self.instance, "v_divergences_humaines")}
        self.assertIn("entreprise", champs)
        self.assertIn("majorite_annoncee", champs)

    def test_les_champs_d_identite_ne_sont_pas_des_divergences(self) -> None:
        from coproscope.modules import _actes_vues

        for champ in ("acte_id", "etat", "origine"):
            self.assertNotIn(champ, _actes_vues.CHAMPS_DIVERGEABLES)


class UneReidentificationHumaineNeSeTaitPasTests(_Coffre):
    """C068. Corriger la date - le defaut que le module documente comme mesure
    et reel - double l'acte au lieu de le reparer."""

    def test_le_doublon_ne_de_la_correction_est_nomme(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte(A.acte_id_resolution("", "12", doc_id="DOC-PV"),
                  date_effet="", ag_id="", resolution_id="RES-12"),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte(A.acte_id_resolution("2024-07-03", "12"),
                  resolution_id="RES-12", origine="CORRIGE_HUMAIN"),
        ], [])
        self.assertEqual(len(A.lire_vue(self.instance, "v_actes")), 2)
        self.assertIn("ACTE_REIDENTIFIE_PAR_HUMAIN", self.codes())
        self.assertIn("c'est a trancher",
                      self.motif("ACTE_REIDENTIFIE_PAR_HUMAIN"))


class UneAssembleeNonTypeeNeVautPasAbsenceDAssembleeTests(_Coffre):
    """C060. La docstring justifiait le silence par `si aucune n'est encore
    lue`, ce qui confond `aucune n'existe` et `aucune n'a ete typee`."""

    def test_l_obligation_de_reddition_le_dit_au_lieu_de_se_taire(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-CS", nature="DECISION_CS_DELEGUEE",
                  date_effet="2024-03-01"),
            _acte("ACTE-AG-NON-TYPEE", date_effet="2025-06-01", numero="13"),
        ], ["DOC-PV"])
        self.assertIn("REDDITION_NON_VERIFIABLE", self.codes())
        self.assertIn("ce n'est pas qu'il n'est pas du",
                      self.motif("REDDITION_NON_VERIFIABLE"))

    def test_une_assemblee_typee_produit_le_vrai_manquement_et_pas_l_aveu(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-CS", nature="DECISION_CS_DELEGUEE",
                  date_effet="2024-03-01"),
            _acte("ACTE-AG-TYPEE", date_effet="2025-06-01", numero="13",
                  portee="APPROBATION_COMPTES"),
        ], ["DOC-PV"])
        self.assertIn("OBLIGATION_NON_TENUE", self.codes())
        self.assertNotIn("REDDITION_NON_VERIFIABLE", self.codes())

if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class UneOrigineHorsVocabulaireFabriqueUnSecondActeTests(_Coffre):
    """C003, branche `origine` - refutee a tort par le lot precedent.

    Sa refutation n'avait rejoue qu'un des quatre cas de la preuve d'origine
    (une `nature` hors vocabulaire, effectivement refusee). `origine` n'etait
    validee nulle part, et le lot venait justement de la faire entrer dans
    `ACTE_CLES`: une colonne en texte libre portait desormais la cle primaire.
    """

    def test_une_origine_inconnue_est_refusee_au_point_d_ecriture(self) -> None:
        with self.assertRaises(ValueError) as capture:
            A.ecrire(self.instance, A.TABLE_ACTES,
                     [_acte("A1", origine="EXTRAIT_V2")], ["DOC-PV"])
        self.assertIn("EXTRAIT_V2", str(capture.exception))

    def test_une_origine_vide_est_refusee_puisqu_elle_est_une_cle(self) -> None:
        """Le vide est admis partout ailleurs; ici il n'est le fait de
        personne, et la garde des corrections humaines l'interroge."""
        with self.assertRaises(ValueError) as capture:
            A.ecrire(self.instance, A.TABLE_ACTES,
                     [_acte("A1", origine="")], ["DOC-PV"])
        self.assertIn("origine", str(capture.exception))

    def test_les_deux_origines_declarees_restent_acceptees(self) -> None:
        """Contre-assertion: la liste fermee ne doit rien refuser de legitime.

        Les deux lignes coexistent parce que `origine` est dans la cle - c'est
        exactement ce que la cle sert a faire: laisser une correction humaine
        et l'extrait de la machine se contredire sans que l'une efface l'autre.
        """
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", origine=origine) for origine in G.ORIGINES],
                 ["DOC-PV"])
        self.assertEqual(
            {ligne["origine"] for ligne in
             A.lire_table(self.instance, A.TABLE_ACTES)},
            set(G.ORIGINES))

    def test_un_acte_reste_un_acte_dans_la_matrice(self) -> None:
        """La mesure de la preuve d'origine, rejouee: sur le code d'avant, deux
        lignes dans `v_actes`, deux dans la matrice, et un euro compte deux
        fois - `montant_paye` a 4000.0 pour une facture unique de 2000.00."""
        with self.assertRaises(ValueError):
            A.ecrire(self.instance, A.TABLE_ACTES,
                     [_acte("A1", portee="ENGAGEMENT_DEPENSE",
                            montant_autorise="2000.00",
                            origine="EXTRAIT_V2", doc_id="DOC-CONVOC")],
                     ["DOC-CONVOC"])
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", portee="ENGAGEMENT_DEPENSE",
                        montant_autorise="2000.00")], ["DOC-PV"])
        self.assertEqual(len(A.lire_vue(self.instance, "v_actes")), 1)
        self.assertEqual(
            len(A.lire_vue(self.instance, "v_matrice_gouvernance")), 1)


class LaDetectionDeCollisionEstPartageeTests(unittest.TestCase):
    """`collisions_de_cle` vit dans la couche partagee, et non en deux copies.

    Le registre des resolutions RAPPORTE les collisions, `_actes_store.ecrire`
    les REFUSE. Deux politiques, une seule detection: deux detections finiraient
    par diverger, et un lot serait accepte d'un cote et compte de l'autre.
    """

    CLES = ("resolution_id", "etat", "origine")

    def test_le_nombre_rendu_est_celui_qui_a_ete_stocke(self) -> None:
        racine = Path(tempfile.mkdtemp())
        try:
            ligne = {"resolution_id": "R3", "etat": "CONSTATEE",
                     "doc_id": "D1", "origine": "EXTRAIT"}
            stockees = G.remplacer_pour_documents(
                _Instance(racine), list(ligne), [dict(ligne), dict(ligne)],
                ["D1"], cles=self.CLES)
            self.assertEqual(stockees, 1)
        finally:
            shutil.rmtree(racine, ignore_errors=False)

    def test_la_cle_en_collision_est_nommee_et_pas_seulement_comptee(self) -> None:
        collisions = G.collisions_de_cle(
            [{"resolution_id": "R3", "etat": "CONSTATEE", "origine": "EXTRAIT"},
             {"resolution_id": "R3", "etat": "CONSTATEE", "origine": "EXTRAIT"},
             {"resolution_id": "R4", "etat": "CONSTATEE", "origine": "EXTRAIT"}],
            self.CLES)
        self.assertEqual(collisions, {("R3", "CONSTATEE", "EXTRAIT"): 2})

    def test_un_lot_sans_collision_ne_nomme_rien(self) -> None:
        self.assertEqual(G.collisions_de_cle([{"resolution_id": "R3"}]), {})


class UnePorteeNonLueEteintLesSeptControlesEnSilenceTests(_Coffre):
    """C003, seconde branche. Le vide reste admis a l'ecriture - une portee que
    le document ne permet pas de lire est un fait - mais il n'etait dit nulle
    part, et un acte muet est indiscernable d'un acte en regle."""

    def test_un_acte_sans_portee_produit_un_constat_au_lieu_de_rien(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", portee="")], ["DOC-PV"])
        self.assertIn("PORTEE_NON_LUE", self.codes())

    def test_le_motif_refuse_l_absence_de_manquement_comme_conformite(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", portee="")], ["DOC-PV"])
        self.assertIn("rien n'a ete verifie", self.motif("PORTEE_NON_LUE"))

    def test_une_portee_lue_ne_declenche_pas_ce_constat(self) -> None:
        """Contre-assertion: `ORDINAIRE` veut dire « portee non determinee » et
        garde les sept controles. Ce n'est pas le cas vise."""
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("A1", portee="ORDINAIRE")], ["DOC-PV"])
        self.assertNotIn("PORTEE_NON_LUE", self.codes())
