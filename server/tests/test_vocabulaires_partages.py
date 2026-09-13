"""Un module ecrit une valeur, un autre en cherche une differente.

Ce fichier ne defend pas une fonctionnalite: il defend une **classe de defaut**,
relevee quatre fois le 2026-09-04 sur quatre couches sans rapport entre elles.

- le bareme de classement lisait `priority`, le fichier livre ecrit `priorite`
  sur ses 38 regles: les 38 priorites valaient 0, et le seul mecanisme
  d'arbitrage entre regles concurrentes etait mort;
- une faute de frappe d'un caractere sur un nom de controle - `'AVIS_CS '` -
  rendait 11 portees au lieu de 3, ce qui rallume le controle partout et rend
  l'ecran d'avant le lot avec l'apparence de l'ecran d'apres;
- `MAJORITE` etait declare parmi les sept controles, discute portee par portee
  dans les motifs de retrait, et consulte nulle part;
- l'ecran des seuils testait `confiance not in ('haute', '')`, mot qu'aucun
  extracteur n'ecrit: les six seuils reels, tous lus `forte`, portaient
  l'avertissement du montant mal lu.

Aucun des quatre ne levait d'erreur. Aucun ne cassait un test. Chacun eteignait
un mecanisme entier en rendant une valeur plausible - le mode de defaillance le
plus couteux du produit.

Les tests generiques de ce fichier repondent donc a une seule question, posee de
quatre facons: **toute cle lue existe-t-elle chez celui qui l'ecrit, et tout ce
qui est declare a-t-il un consommateur ?**
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.modules import _actes_constats as K
from coproscope.modules import _actes_typologie as T
from coproscope.modules import _actes_vocabulaire as V
from coproscope.modules import _actes_vues as W
from coproscope.modules import docuscope
from coproscope.web import _controle_gouvernance_constats as C
from coproscope.web._controle_gouvernance_source import CONSTATS_HORS_ECRAN

RACINE = Path(__file__).resolve().parents[1] / "src" / "coproscope"
TAXONOMIE = RACINE / "configs" / "taxonomy.default.yml"


def _regles_livrees() -> list[dict]:
    taxonomie = json.loads(TAXONOMIE.read_text(encoding="utf-8"))
    return taxonomie.get("rules", taxonomie.get("regles", []))


class _InstanceTemporaire:
    """Instance minimale: seul le coffre local compte pour ce magasin."""

    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()


def _acte_minimal(acte_id: str, **kw: str) -> dict[str, str]:
    """Un acte dont seule la portee change d'un cas de mesure a l'autre."""
    ligne = {
        "acte_id": acte_id, "nature": V.NATURE_RESOLUTION_AG,
        "etat": V.ETAT_CONSTATEE, "portee": V.PORTEE_ORDINAIRE,
        "date_effet": "2024-07-03", "exercice": "2024",
        "ag_id": "AG-2024-07-03", "numero": "12", "sous_numero": "",
        "objet": "Ravalement de la facade sud", "montant_autorise": "",
        "entreprise": "", "montant_source": "", "entreprise_source": "",
        "valide_du": "", "valide_au": "",
        "majorite_annoncee": V.MAJORITE_NON_ENONCEE,
        "majorite_requise": "24", "majorite_appliquee": "24",
        "resultat": V.RESULTAT_ADOPTEE, "resolution_id": "", "page": "4",
        "ancre": "", "confiance": V.CONFIANCE_FORTE,
        "doc_id": "DOC-PV", "origine": V.ORIGINE_EXTRAIT,
    }
    ligne.update(kw)
    return ligne


class BaremeDeClassementTests(unittest.TestCase):
    """C009: la cle de priorite du bareme, ecrite en francais, n'etait pas lue."""

    def test_la_priorite_departage_deux_regles_a_egalite_de_score(self) -> None:
        """Sans priorite, l'egalite est tranchee par la position dans le fichier.

        Mesure du 2026-09-04 sur le registre reel: 271 lignes (7,9 %) avaient au
        moins deux regles a egalite au sommet. Le vainqueur etait celui qui
        etait ecrit le plus haut dans `taxonomy.default.yml`, pas celui que le
        droit designe.
        """
        regles = [
            {"lot": "AG", "type_document": "Convocation_AG", "priorite": 100,
             "mots_cles": ["assemblee generale"]},
            {"lot": "AG", "type_document": "PV_AG", "priorite": 115,
             "mots_cles": ["assemblee generale"]},
        ]
        # Indice plutot que depaquetage: la voie classement ajoute une
        # quatrieme valeur de retour a `_classify`, et un test de vocabulaire
        # n'a pas a echouer sur la longueur du tuple d'une autre voie.
        verdict = docuscope._classify(
            "assemblee generale ordinaire", "piece.pdf", "/piece.pdf", regles
        )
        self.assertEqual(verdict[1], "PV_AG")

    def test_les_deux_orthographes_de_la_priorite_donnent_le_meme_verdict(self) -> None:
        regles_fr = [{"lot": "AG", "type_document": "PV_AG", "priorite": 40,
                      "mots_cles": ["assemblee generale"]}]
        regles_en = [{"lot": "AG", "type_document": "PV_AG", "priority": 40,
                      "keywords": ["assemblee generale"]}]
        self.assertEqual(
            docuscope._classify("assemblee generale", "p.pdf", "/p.pdf", regles_fr),
            docuscope._classify("assemblee generale", "p.pdf", "/p.pdf", regles_en),
        )

    def test_toute_cle_du_fichier_livre_est_lue_ou_declaree_documentaire(self) -> None:
        """Le garde-fou de classe, cote configuration.

        Une cle presente dans le fichier, absente de `CHAMPS_REGLE` et absente
        de `CHAMPS_DOCUMENTAIRES`, n'est lue par personne et ne dit rien a
        personne: elle a l'air de regler quelque chose et ne regle rien.
        """
        regles = _regles_livrees()
        self.assertTrue(regles, "le fichier livre doit porter des regles")
        presentes = set()
        for regle in regles:
            presentes |= set(regle)
        inconnues = sorted(presentes - docuscope.NOMS_CHAMPS_REGLE)
        self.assertEqual(inconnues, [], f"cles ecrites et jamais lues: {inconnues}")

    def test_chaque_cle_reglante_du_fichier_livre_est_effectivement_atteinte(
        self,
    ) -> None:
        """La declaration ne suffit pas: la valeur d'un REGLAGE doit remonter.

        Les champs documentaires sont exclus a dessein: ils ne remontent nulle
        part, c'est leur definition. Ce test porte sur ceux qui promettent
        d'agir.
        """
        presentes = set()
        for regle in _regles_livrees():
            presentes |= set(regle)
        reglantes = sorted(presentes - docuscope.CHAMPS_DOCUMENTAIRES)
        self.assertTrue(reglantes)
        for alias in reglantes:
            champ = next(
                nom for nom, alias_connus in docuscope.CHAMPS_REGLE.items()
                if alias in alias_connus
            )
            with self.subTest(alias=alias):
                self.assertEqual(
                    docuscope._champ_regle({alias: "SENTINELLE"}, champ, "DEFAUT"),
                    "SENTINELLE",
                )

    def test_un_champ_documentaire_ne_regle_rien_et_ne_pretend_pas_le_contraire(
        self,
    ) -> None:
        """La distinction doit rester verifiable, pas seulement declaree.

        Un nom range dans `CHAMPS_DOCUMENTAIRES` ne doit surtout pas etre
        AUSSI un reglage lu: il serait alors dispense de la garde tout en
        agissant, ce qui est la pire combinaison des deux.
        """
        for nom in docuscope.CHAMPS_DOCUMENTAIRES:
            with self.subTest(nom=nom):
                self.assertNotIn(nom, docuscope.CHAMPS_REGLE)
                for alias in docuscope.CHAMPS_REGLE.values():
                    self.assertNotIn(nom, alias)

    def test_le_fichier_livre_ne_porte_aucune_cle_de_tete_morte(self) -> None:
        taxonomie = json.loads(TAXONOMIE.read_text(encoding="utf-8"))
        self.assertEqual(docuscope._verifier_taxonomie(taxonomie), [])

    def test_une_cle_de_tete_inconnue_est_nommee_sans_bloquer_le_classement(
        self,
    ) -> None:
        """Le fichier de taxonomie est partage: une autre voie peut y ecrire."""
        journal: list[str] = []
        signalements = docuscope._verifier_taxonomie(
            {"regles": [], "reglages": {}}, journal=journal.append
        )
        self.assertEqual(len(signalements), 1)
        self.assertIn("reglages", signalements[0])
        self.assertEqual(journal, signalements)

    def test_un_champ_inconnu_est_nomme_au_chargement(self) -> None:
        """Nomme, pas fatal - voir `ChampsDeRegleDeClassementTests` pour le motif."""
        signalements = docuscope._verifier_regles(
            [{"lot": "AG", "type_document": "PV_AG", "priorite_max": 115}]
        )
        self.assertEqual(len(signalements), 1)
        self.assertIn("priorite_max", signalements[0])


class NomDeControleTests(unittest.TestCase):
    """C030: un nom de controle errone rallumait le controle sur onze portees."""

    def test_un_nom_de_controle_mal_orthographie_leve_au_lieu_de_tout_rallumer(self) -> None:
        for nom in ("AVIS_CS ", "avis_cs", "CONTROLE_QUI_NEXISTE_PAS", ""):
            with self.subTest(nom=nom):
                with self.assertRaises(ValueError):
                    T.portees_soumises(nom)
                with self.assertRaises(ValueError):
                    T.controle_applicable(V.PORTEE_DESIGNATION_SYNDIC, nom)
                with self.assertRaises(ValueError):
                    T.motif_hors_controle(V.PORTEE_DESIGNATION_SYNDIC, nom)

    def test_le_nom_juste_rend_les_portees_que_la_matrice_ne_retire_pas(self) -> None:
        """La garde ne doit pas changer la reponse quand le nom est correct.

        Ce test portait un compte en dur, `3`. Il a casse le 2026-09-05 sur un
        arbitrage de droit qui ne le concernait pas: le retrait de
        `CTRL_AVIS_CS` sur la designation du syndic a ete leve, la reponse est
        passee a quatre, et un test de *garde sur le nom* a signale un faux
        defaut. Un test ne doit pas detenir une doctrine que la matrice detient
        deja: il verifie ici l'accord entre la fonction et `HORS_CONTROLE`,
        quel que soit le compte du jour.
        """
        attendues = {
            portee for portee in V.PORTEES
            if T.CTRL_AVIS_CS not in T.HORS_CONTROLE.get(portee, {})
        }
        self.assertEqual(set(T.portees_soumises(T.CTRL_AVIS_CS)), attendues)
        self.assertTrue(attendues, "un controle sans aucune portee ne mesure rien")

    def test_la_matrice_des_retraits_ne_porte_que_du_vocabulaire_declare(self) -> None:
        for portee, retraits in T.HORS_CONTROLE.items():
            self.assertIn(portee, V.PORTEES)
            for controle in retraits:
                self.assertIn(controle, T.CONTROLES)


class ControleSansConsommateurTests(unittest.TestCase):
    """C031, C063, C093: `MAJORITE` etait declare et branche nulle part."""

    #: Un controle est branche s'il borne une cellule de la matrice ou un
    #: constat - c'est-a-dire si son nom est passe a `_cellule`, a
    #: `portees_soumises` ou a `portees_retirees` dans le code des vues ou des
    #: constats. Les deux dernieres sont les deux facons de traduire la matrice
    #: en SQL; `portees_retirees` est celle qui laisse une portee inconnue dans
    #: le controle, donc celle que les constats emploient.
    #: `_actes_vues_matrice` s'est detache de `_actes_vues` le 2026-09-08. Sans
    #: cette ligne, ce test rendait les CINQ controles orphelins d'un coup: un
    #: balayage qui n'accuse plus personne en particulier est casse.
    SOURCES = (
        RACINE / "modules" / "_actes_vues.py",
        RACINE / "modules" / "_actes_vues_matrice.py",
        RACINE / "modules" / "_actes_constats.py",
    )

    def controles_consultes(self) -> set[str]:
        noms: set[str] = set()
        for chemin in self.SOURCES:
            texte = chemin.read_text(encoding="utf-8")
            # `cellule(` et `_cellule(` - le nom a perdu son underscore en
            # devenant public a l'extraction - et l'argument nomme `controle=`,
            # par lequel les cellules generees passent leur controle.
            for brut in re.findall(r"cellule\(\s*'([A-Z_]+)'", texte):
                noms.add(brut)
            for brut in re.findall(r"controle=(CTRL_[A-Z_]+)", texte):
                noms.add(getattr(T, brut))
            for brut in re.findall(
                r"(?:portees_soumises|portees_retirees|_hors_controle)\("
                r"[^)]*?(CTRL_[A-Z_]+|'[A-Z_]+')\s*\)",
                texte,
            ):
                if brut.startswith("CTRL_"):
                    noms.add(getattr(T, brut))
                else:
                    noms.add(brut.strip("'"))
        return noms

    def test_chaque_controle_declare_borne_une_cellule_ou_un_constat(self) -> None:
        """Un controle declare et non branche est pire qu'un controle absent.

        Sa declaration fait croire qu'il tourne, et son absence ne se voit pas:
        il n'y a pas de cellule vide a regarder, il n'y a pas de cellule.
        """
        orphelins = sorted(set(T.CONTROLES) - self.controles_consultes())
        self.assertEqual(
            orphelins, [],
            f"controles declares sans consommateur: {orphelins}. Un retrait "
            "ecrit dans HORS_CONTROLE n'aurait sur eux aucun effet observable.",
        )

    def test_un_retrait_de_majorite_se_voit_dans_le_sql_du_constat(self) -> None:
        """La preuve que le branchement est reel et pas seulement declaratif.

        Aucune portee n'est retiree de MAJORITE aujourd'hui: le predicat est
        donc vide, et une assertion sur les portees SOUMISES ne prouverait
        rien - elle passerait aussi bien sans branchement. Ce qui se mesure est
        l'effet d'un retrait: on en ecrit un, et il doit apparaitre en `NOT IN`.
        """
        sql_sans_retrait = K.vue_constats("1=1")
        self.assertIn("MAJORITE_NON_ENONCEE", sql_sans_retrait)
        self.assertNotIn("a.portee NOT IN", sql_sans_retrait)

        portee = V.PORTEE_MODALITES
        retraits = T.HORS_CONTROLE.setdefault(portee, {})
        retraits[T.CTRL_MAJORITE] = "retrait temporaire, pour la mesure du test"
        try:
            sql_avec_retrait = K.vue_constats("1=1")
        finally:
            del retraits[T.CTRL_MAJORITE]
            if not retraits:
                T.HORS_CONTROLE.pop(portee, None)
        self.assertIn(f"a.portee NOT IN ('{portee}')", sql_avec_retrait)

    def test_le_constat_de_majorite_est_borne_par_retrait_et_non_par_admission(
        self,
    ) -> None:
        """C017: `IN (soumises)` eteint le controle sur la portee non lue.

        Une portee vide n'est ni soumise ni retiree: elle echoue tout `IN` et
        satisfait tout `NOT IN`. Borner par admission la sortait donc du
        constat en silence, ce qui est l'inverse de ce que promet
        `controle_applicable`.
        """
        sql = K.vue_constats("1=1")
        self.assertNotIn("a.portee IN (", sql)
        self.assertNotIn("e.portee IN (", sql)


class CodesDeConstatTests(unittest.TestCase):
    """Tout code que l'ecran filtre doit avoir un producteur."""

    def codes_produits(self) -> set[str]:
        sql = K.vue_constats("1=1")
        return set(re.findall(r"SELECT '([A-Z_]+)'", sql))

    def codes_consommes(self) -> set[str]:
        codes = {
            str(constat["filtre"]["constat"])
            for constat in C.CONSTATS
            if "constat" in constat["filtre"]
        }
        return codes | set(CONSTATS_HORS_ECRAN)

    def test_chaque_code_affiche_par_l_ecran_est_produit_par_la_vue(self) -> None:
        orphelins = sorted(self.codes_consommes() - self.codes_produits())
        self.assertEqual(
            orphelins, [],
            f"codes cherches par l'ecran et jamais produits: {orphelins}. La "
            "pastille afficherait zero sans jamais pouvoir afficher autre chose.",
        )


class VocabulaireDesVuesTests(unittest.TestCase):
    """Toute valeur comparee en SQL doit appartenir au vocabulaire de sa colonne."""

    #: colonne -> liste fermee. Les colonnes libres (objet, libelle, dates,
    #: montants) ne sont pas ici: elles n'ont pas de vocabulaire.
    COLONNES = {
        "nature": V.NATURES,
        "etat": V.ETATS,
        "portee": V.PORTEES,
        "resultat": V.RESULTATS,
        "origine": (V.ORIGINE_EXTRAIT, V.ORIGINE_CORRIGE),
        "provenance": V.PROVENANCES,
        "relation": V.RELATIONS,
        "force_probatoire": V.FORCES,
        "imputation": V.IMPUTATIONS,
        "tva_regime": V.TVA_REGIMES,
        "confiance": V.CONFIANCES,
    }

    def sql_complet(self) -> str:
        return "\n".join(W.VUES)

    def test_aucune_comparaison_ne_cherche_une_valeur_hors_vocabulaire(self) -> None:
        """C021 et C022, en garde generique.

        `WHERE a.majorite_annoncee = 'NON_ENONCEE'` etait juste; ce qui manquait
        etait le producteur. Une faute de frappe au meme endroit -
        `'NON_ENONCE'` - aurait rendu zero constat exactement de la meme facon,
        sans erreur et sans trace. Ce test rend cette faute-la impossible.
        """
        sql = self.sql_complet()
        for colonne, vocabulaire in self.COLONNES.items():
            for valeur in re.findall(
                rf"\b{colonne}\s*(?:=|<>|!=)\s*'([^']*)'", sql
            ):
                with self.subTest(colonne=colonne, valeur=valeur):
                    self.assertIn(valeur, vocabulaire)
            for groupe in re.findall(
                rf"\b{colonne}\s+(?:NOT\s+)?IN\s*\(([^)]*)\)", sql
            ):
                if "SELECT" in groupe.upper():
                    continue
                for valeur in re.findall(r"'([^']*)'", groupe):
                    with self.subTest(colonne=colonne, valeur=valeur):
                        self.assertIn(valeur, vocabulaire)


class MajoriteNonEnonceeTests(unittest.TestCase):
    """C021 et C022: le producteur ecrivait la chaine vide, le consommateur
    cherchait `NON_ENONCEE`.

    Le pont registre -> actes traduit desormais l'un dans l'autre. Ces tests
    tiennent les deux bouts ensemble, pour qu'un cote ne puisse plus bouger
    sans l'autre.
    """

    def test_le_pont_traduit_la_colonne_vide_en_valeur_nommee(self) -> None:
        from coproscope.modules._pont_actes_source import majorite_lue

        self.assertEqual(majorite_lue(""), V.MAJORITE_NON_ENONCEE)
        self.assertEqual(majorite_lue("   "), V.MAJORITE_NON_ENONCEE)
        self.assertEqual(majorite_lue("25"), "25")

    def test_le_constat_cherche_la_valeur_du_vocabulaire_et_non_un_litteral(self) -> None:
        sql = K.vue_constats("1=1")
        self.assertIn(f"a.majorite_annoncee = '{V.MAJORITE_NON_ENONCEE}'", sql)
        source = (RACINE / "modules" / "_actes_constats.py").read_text(encoding="utf-8")
        self.assertNotIn(
            "'NON_ENONCEE'", source,
            "la valeur cherchee doit venir du vocabulaire, pas d'une chaine "
            "recopiee: une lettre de moins rendrait zero constat en silence.",
        )


class PorteeProduiteTests(unittest.TestCase):
    """Le qualificateur et le modele des actes ne parlent pas le meme dialecte.

    `_resolutions_qualification.QUALIFICATIONS` nomme ce qu'un texte de
    resolution laisse reconnaitre; `_actes_vocabulaire.PORTEES` nomme les onze
    types que la matrice des controles sait borner. Les deux listes ne se
    recouvrent qu'a moitie, et c'est normal: la traduction est le travail de
    `portee_resolution`. Ce qui ne serait pas normal, c'est qu'elle rende un
    mot que la matrice ne connait pas - il ne serait dans aucune liste
    `IN (...)`, donc l'acte sortirait de tous les controles en affichant
    « Ne s'applique pas », le message le plus rassurant du produit.
    """

    def test_le_qualificateur_ne_rend_que_des_portees_declarees(self) -> None:
        from coproscope.modules import _resolutions_qualification as Q

        source = (RACINE / "modules" / "_resolutions_qualification.py").read_text(
            encoding="utf-8"
        )
        debut = source.index("def portee_resolution(")
        rendues = set(re.findall(r"return (PORTEE_[A-Z_]+)", source[debut:]))
        self.assertTrue(rendues, "la fonction doit rendre des portees nommees")
        for nom in sorted(rendues):
            with self.subTest(portee=nom):
                self.assertIn(getattr(Q, nom), V.PORTEES)


class ConfianceLueEtAfficheeTests(unittest.TestCase):
    """C084: l'ecran cherchait `haute`, l'extracteur ecrit `forte`."""

    def test_l_extracteur_ne_produit_que_le_vocabulaire_declare(self) -> None:
        source = (RACINE / "modules" / "_resolutions_extraction.py").read_text(
            encoding="utf-8"
        )
        debut = source.index("def _confiance(")
        fin = source.index("\ndef ", debut + 1)
        produites = set(re.findall(r'return "([a-z]+)"', source[debut:fin]))
        self.assertTrue(produites)
        self.assertLessEqual(produites, set(V.CONFIANCES))

    def test_le_seuil_le_mieux_lu_ne_porte_pas_l_avertissement_du_mal_lu(self) -> None:
        from coproscope.web.controle_gouvernance_view import _a_valider_seuil

        self.assertEqual(_a_valider_seuil(V.CONFIANCE_FORTE), "")
        for moindre in (V.CONFIANCE_MOYENNE, V.CONFIANCE_FAIBLE):
            self.assertIn("relisez la résolution", _a_valider_seuil(moindre))

    def test_une_confiance_jamais_lue_ne_passe_pas_pour_confirmee(self) -> None:
        from coproscope.web.controle_gouvernance_view import _a_valider_seuil

        message = _a_valider_seuil("")
        self.assertNotEqual(message, "")
        self.assertIn("pas noté", message)


class PorteeNonRenseigneeTests(unittest.TestCase):
    """C017: la portee qu'on ne sait pas lire ne doit pas sortir du controle.

    Mesure du 2026-09-05 sur un coffre temporaire, deux actes identiques a
    `majorite_annoncee='NON_ENONCEE'`, l'un `portee='ORDINAIRE'` l'autre
    `portee=''`: le bornage par `portee IN (portees soumises)` en rendait un,
    le bornage par `portee NOT IN (portees retirees)` rend les deux. Le vide
    est une valeur atteignable - `_actes_store._valider_vocabulaire` l'admet
    explicitement, « une colonne non renseignee est un fait, pas une faute ».
    """

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)
        self.instance = _InstanceTemporaire(self.racine)

    def _codes(self, code: str) -> set[str]:
        return {
            str(ligne["sujet_id"])
            for ligne in A.constats(self.instance)
            if ligne["code"] == code
        }

    def test_un_acte_sans_portee_lue_garde_le_constat_de_majorite(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte_minimal("ACTE-PORTEE-LUE", portee=V.PORTEE_ORDINAIRE),
            _acte_minimal("ACTE-PORTEE-VIDE", portee=""),
        ], ["DOC-PV"])
        self.assertEqual(
            self._codes("MAJORITE_NON_ENONCEE"),
            {"ACTE-PORTEE-LUE", "ACTE-PORTEE-VIDE"},
            "une portee non renseignee ne doit pas eteindre le constat: rien "
            "n'a ete lu, donc rien n'autorise a lever le controle.",
        )

    def test_un_acte_sans_portee_lue_garde_le_constat_d_execution(self) -> None:
        """Meme demonstration sur le controle qui a des retraits reels.

        `PORTEE_SEUIL` est retiree de EXECUTION avec son motif: elle doit
        rester dehors. `portee=''` n'est retiree de rien: elle doit rester
        dedans.
        """
        self.assertIn(V.PORTEE_SEUIL, T.portees_retirees(T.CTRL_EXECUTION))
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte_minimal("ACTE-EXEC-VIDE", portee="", montant_autorise="9000"),
            _acte_minimal(
                "ACTE-EXEC-RETIREE", portee=V.PORTEE_SEUIL, montant_autorise="9000"
            ),
        ], ["DOC-PV"])
        self.assertEqual(self._codes("ACTE_SANS_EXECUTION"), {"ACTE-EXEC-VIDE"})


class ChampsDeRegleDeClassementTests(unittest.TestCase):
    """La garde du chargement: fatale sur l'amputation, parlante sur l'inconnu."""

    def test_une_regle_sans_lot_est_refusee_au_lieu_d_en_inventer_un(self) -> None:
        """Mesure du 2026-09-05: elle rendait ('A_CLASSER', 'PV_AG', 5).

        Un type documentaire affirme, range dans un lot que personne n'a
        ecrit, sans exception. Le code d'avant la garde levait un `KeyError`:
        la garde avait donc rendu muet le cas qu'elle existait pour attraper.
        """
        sans_lot = {"type_document": "PV_AG", "mots_cles": ["assemblee generale"]}
        with self.assertRaises(ValueError) as leve:
            docuscope._verifier_regles([sans_lot])
        self.assertIn("lot", str(leve.exception))
        with self.assertRaises(KeyError):
            docuscope._classify("assemblee generale", "p.pdf", "/p.pdf", [sans_lot])

    def test_un_champ_inconnu_est_signale_sans_rendre_le_classement_indisponible(
        self,
    ) -> None:
        """Signale, pas fatal: les autres voies ajoutent des champs a la taxonomie.

        Lever refuserait la taxonomie entiere pour un champ qui ne concerne pas
        le classement. Se taire reproduirait le defaut du lot. Le champ est
        donc nomme, rendu a l'appelant, et ecrit au journal de la course.
        """
        regle = {
            "lot": "AG", "type_document": "PV_AG", "priorite": 10,
            "poids_maximal": 3, "mots_cles": ["assemblee generale"],
        }
        journal: list[str] = []
        signalements = docuscope._verifier_regles([regle], journal=journal.append)
        self.assertEqual(len(signalements), 1)
        self.assertIn("poids_maximal", signalements[0])
        self.assertEqual(journal, signalements)
        self.assertEqual(
            docuscope._classify("assemblee generale", "p.pdf", "/p.pdf", [regle])[0],
            "AG",
            "le champ non lu ne doit pas non plus changer le verdict",
        )

    def test_un_champ_declare_documentaire_passe_sans_signalement(self) -> None:
        """`fondement` cite l'article qui justifie la regle: il n'agit pas.

        Il est ecrit sur cinq regles de la taxonomie par la voie classement, et
        aucun code ne le lit - ce qui est normal pour une citation. La garde ne
        doit ni le refuser, ni le signaler comme un reglage mort.
        """
        regle = {
            "lot": "AG", "type_document": "PV_AG", "priorite": 10,
            "fondement": "decret 67-223 art. 17", "mots_cles": ["assemblee generale"],
        }
        self.assertEqual(docuscope._verifier_regles([regle]), [])
        self.assertEqual(
            docuscope._classify("assemblee generale", "p.pdf", "/p.pdf", [regle])[0],
            "AG",
        )

    def test_le_fichier_livre_ne_declenche_aucun_signalement(self) -> None:
        self.assertEqual(docuscope._verifier_regles(_regles_livrees()), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
