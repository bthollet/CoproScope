"""Deux normes de seuil, deux relations, et un residu qui se nomme.

`RM-2026-0144`, 2026-09-08. L'article 21 alinea 2 de la loi 65-557 fait arreter
par l'assemblee **deux** montants sur des objets differents: celui a partir
duquel la consultation du conseil syndical devient obligatoire, et celui a
partir duquel la mise en concurrence l'est. Le modele les portait sur une
relation UNIQUE, `SEUIL_APPLICABLE`.

**Ce que cela coutait, mesure sur deux coffres reels le 2026-09-08.** 186 actes
portaient au moins un lien de seuil; 121 d'entre eux se declaraient
`non tranche` parce que deux montants du meme jour arrivaient sur la meme
relation et qu'aucun ordre ne pouvait les departager. Le produit criait au
conflit devant une copropriete parfaitement en regle: les deux votes ne
repondaient pas a la meme question.

**L'axe teste ici, et il n'est pas une liste de deux cas.** Ce qui varie est
`ce que le franchissement du montant rend obligatoire`. Ce qui reste invariant
est tout le reste: le montant est arrete par l'assemblee, il porte sur des
marches et des contrats, il a un terme, et un engagement posterieur y est
soumis. Les tests d'attribution bouclent donc sur `NORMES_SEUIL` au lieu de
nommer deux cas: une troisieme norme declaree demain serait couverte le jour de
sa declaration, et une norme dont l'attribution serait cassee tomberait ici
meme si les deux autres marchaient.

**Hors des valeurs observees.** Une deliberation qui arreterait un troisieme
montant sur un objet inconnu ne doit **pas** tomber dans l'une des deux cases.
Elle tombe dans le residu, qui est nomme, compte, et affiche. Le test
`test_un_troisieme_seuil_ne_se_range_pas_dans_une_case_par_defaut` est celui-la,
et c'est le test d'acceptation de la regle des axes.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.modules._actes_citations import (
    CELLULES_LIEES,
    ORDRE_CHRONOLOGIQUE,
    ORDRE_PAR_RELATION,
    ordre_de,
)
from coproscope.modules._actes_seuils_normes import (
    ENTREES_SEUIL,
    NORME_CONCURRENCE,
    NORME_CONSULTATION_CS,
    NORME_NON_ATTRIBUEE,
    NORMES_SEUIL,
    norme_arretee,
)
from coproscope.modules._actes_vocabulaire import RELATIONS
from coproscope.modules._actes_vues_matrice import vue_matrice
from coproscope.modules._pont_actes_liens import liens_seuil, normes_seuil
from coproscope.modules._pont_actes_source import Candidat
from coproscope.modules._resolutions_seuils import SEUILS_SUIVIS
from coproscope.web._controle_gouvernance_cellules import _seuil


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


def _acte(acte_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "acte_id": acte_id, "nature": "RESOLUTION_AG", "etat": "CONSTATEE",
        "portee": "ENGAGEMENT_DEPENSE", "date_effet": "2026-04-29",
        "exercice": "2026", "ag_id": "AG-2026-04-29", "numero": "11",
        "sous_numero": "1", "objet": "Ravalement de la facade sud",
        "montant_autorise": "18240.00", "entreprise": "", "montant_source": "",
        "entreprise_source": "", "valide_du": "", "valide_au": "",
        "majorite_requise": "24", "majorite_appliquee": "24",
        "majorite_annoncee": "24", "resultat": "ADOPTEE", "resolution_id": "",
        "page": "16", "ancre": "sous-point 11-1", "confiance": "forte",
        "doc_id": "DOC-CONVOCATION", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _seuil_vote(acte_id: str, date: str, montant: str, numero: str = "26") -> dict[str, str]:
    """Une deliberation qui arrete un seuil, a une date donnee."""
    return _acte(acte_id, portee="SEUIL", date_effet=date, numero=numero,
                 montant_autorise=montant, valide_du=date or "")


def _candidat(acte: dict[str, str], qualifications: str) -> Candidat:
    """Le candidat dont l'acte est issu, avec ce que le registre a qualifie.

    `qualifications` est la colonne du registre des resolutions, ecrite par
    `_resolutions_registre` en `";".join(...)`. On la pose telle quelle plutot
    que decoupee: c'est cette forme-la que le pont recoit en production.
    """
    ligne = dict(acte)
    ligne["qualifications"] = qualifications
    return Candidat(ligne=ligne, source="RESOLUTION", date_ag=acte["date_effet"],
                    segment="", portee=acte["portee"])


class _Instance:
    display_name = "Copropriete de recette"

    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict[str, object]:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / str(valeur).lstrip("./")).resolve()


class _Socle(unittest.TestCase):
    """Un coffre jetable par mesure, comme dans `test_seuil_chronologie`.

    Deux mesures qui partageraient un coffre additionneraient leurs liens, et la
    seconde compterait la somme des deux sans que rien ne le signale.
    """

    def setUp(self) -> None:
        self._coffres: list[Path] = []

    def tearDown(self) -> None:
        for racine in self._coffres:
            shutil.rmtree(racine, ignore_errors=True)

    def _matrice(self, actes: list[dict[str, str]],
                 liens: list[dict[str, str]]) -> dict[str, dict[str, object]]:
        racine = Path(tempfile.mkdtemp())
        self._coffres.append(racine)
        instance = _Instance(racine)
        A.ecrire(instance, A.TABLE_ACTES, actes,
                 sorted({a["doc_id"] for a in actes}))
        if liens:
            A.ecrire(instance, A.TABLE_LIENS, liens,
                     sorted({l["doc_id"] for l in liens}))
        return {l["acte_id"]: l for l in A.matrice(instance)}


# --------------------------------------------------------------------------
# Gardes STRUCTURELLES - celles qui attrapent une re-fusion des deux normes
# --------------------------------------------------------------------------


class LaSeparationEstStructurelleTests(unittest.TestCase):
    """Ce que le lot precedent a appris: seule une garde structurelle attrape
    le retour du defaut. Une garde de comportement sur un cas de fixture reste
    verte quand les deux normes sont re-fusionnees, tant que le cas teste ne
    porte qu'une seule des deux."""

    def test_le_discriminant_est_celui_que_la_voie_resolutions_ecrit(self):
        """La coupure entre les deux normes n'est pas inventee par ce modele.

        `_resolutions_qualification` distingue deja les deux, sur deux motifs
        distincts, et `_resolutions_seuils` les suit sous ces deux noms. Si l'un
        des deux etait renomme la-bas, TOUTES les deliberations de seuil
        tomberaient ici dans le residu - sans qu'aucun test de comportement ne
        bouge, puisque le residu est un etat legitime. Ce test est la seule
        chose qui le dirait.
        """
        self.assertEqual(
            set(SEUILS_SUIVIS), {n.cle for n in NORMES_SEUIL},
            "les normes declarees ici ne sont plus celles que le registre des "
            "resolutions qualifie: le discriminant a change d'un cote et pas "
            "de l'autre, et tous les seuils tomberaient dans le residu",
        )

    def test_chaque_entree_de_seuil_a_sa_propre_relation_et_sa_propre_colonne(self):
        """L'injectivite, et c'est elle qui empeche la re-fusion.

        Deux normes qui partageraient une relation, ou deux relations qui
        partageraient un prefixe de colonne, reproduiraient exactement le defaut
        du 2026-09-08: les deux montants arriveraient dans la meme cellule et
        l'ecran les opposerait a nouveau.
        """
        relations = [n.relation for n in ENTREES_SEUIL]
        prefixes = [n.prefixe for n in ENTREES_SEUIL]
        self.assertEqual(len(relations), len(set(relations)),
                         "deux entrees de seuil partagent une relation: %s" % relations)
        self.assertEqual(len(prefixes), len(set(prefixes)),
                         "deux entrees de seuil partagent un prefixe: %s" % prefixes)

    def test_chaque_relation_de_seuil_est_declaree_partout_ou_elle_doit_l_etre(self):
        """Une relation qui manquerait a un des trois registres disparaitrait.

        `RELATIONS` la refuserait a l'ecriture, `ORDRE_PAR_RELATION` leverait au
        montage de la vue, `CELLULES_LIEES` la priverait de source et de
        compteur. Les trois sont verifies ensemble parce que l'oubli d'un seul
        suffit a perdre des liens.
        """
        for entree in ENTREES_SEUIL:
            with self.subTest(relation=entree.relation):
                self.assertIn(entree.relation, RELATIONS)
                self.assertIn(entree.relation, ORDRE_PAR_RELATION)
                self.assertEqual(CELLULES_LIEES.get(entree.relation), entree.prefixe)
                self.assertIs(ordre_de(entree.relation), ORDRE_CHRONOLOGIQUE,
                              "un seuil est une NORME votee: il se tranche par "
                              "la date de la deliberation, jamais par la force "
                              "de la piece")

    def test_la_matrice_produit_une_cellule_nommee_par_norme(self):
        """L'ecran doit pouvoir dire LAQUELLE des deux il rapporte.

        Corriger le modele sans corriger l'affichage aurait deplace le defaut
        d'un metre: une colonne `cel_seuil` unique aurait continue de melanger
        les deux.
        """
        sql = vue_matrice("1=1")
        for entree in ENTREES_SEUIL:
            with self.subTest(prefixe=entree.prefixe):
                self.assertIn("AS cel_%s," % entree.prefixe, sql)
                self.assertIn("AS nb_%s," % entree.prefixe, sql)
                self.assertIn("AS cle_%s," % entree.prefixe, sql)

    def test_la_relation_residuelle_garde_la_valeur_deja_ecrite_dans_les_coffres(self):
        """La migration, et c'est la garde principale du lot.

        Toute ligne deja ecrite porte `SEUIL_APPLICABLE`. Changer cette valeur
        aurait orpheline ces lignes: elles auraient disparu de l'ecran sans
        qu'aucun compteur ne bouge, ce qui est la seule chose qu'un lot de
        separation n'a pas le droit de faire. Elles se relisent donc comme ce
        qu'elles sont: un seuil rattache dont la norme n'est pas attribuee.
        """
        self.assertEqual("SEUIL_APPLICABLE", NORME_NON_ATTRIBUEE.relation)
        self.assertEqual("seuil", NORME_NON_ATTRIBUEE.prefixe)


# --------------------------------------------------------------------------
# L'attribution: sur l'axe, pas sur deux cas
# --------------------------------------------------------------------------


class ChaqueNormeEstAtteignableTests(unittest.TestCase):
    def test_chaque_norme_declaree_est_produite_par_son_propre_discriminant(self):
        """Boucle sur `NORMES_SEUIL`, et c'est le point.

        Nommer deux cas laisserait passer la panne qui envoie une seule des deux
        normes au residu. Une troisieme norme declaree demain est couverte le
        jour de sa declaration, sans edition de ce test.
        """
        for norme in NORMES_SEUIL:
            with self.subTest(norme=norme.cle):
                lue, motif = norme_arretee(norme.cle)
                self.assertIs(lue, norme)
                self.assertEqual("", motif, "une norme attribuee n'a pas de motif")

    def test_le_discriminant_se_lit_dans_une_liste_du_registre(self):
        """Le registre ecrit `A;B`, pas une valeur seule."""
        lue, _ = norme_arretee("APPROBATION_COMPTES;%s;MANDAT_SYNDIC"
                               % NORME_CONCURRENCE.cle)
        self.assertIs(lue, NORME_CONCURRENCE)

    def test_un_jeton_n_est_pas_une_sous_chaine(self):
        """Comparer des sous-chaines rendrait vraie une appartenance qui ne
        l'est pas le jour ou une qualification en prefixerait une autre."""
        lue, _ = norme_arretee("%s_BIS" % NORME_CONSULTATION_CS.cle)
        self.assertIs(lue, NORME_NON_ATTRIBUEE)

    def test_un_troisieme_seuil_ne_se_range_pas_dans_une_case_par_defaut(self):
        """**Le test d'acceptation de la regle des axes.**

        Une assemblee arrete demain un montant sur un objet encore different.
        Le code doit se degrader proprement - dire qu'il ne sait pas - et non
        produire une reponse fausse en silence en le rangeant chez le voisin.
        """
        lue, motif = norme_arretee("SEUIL_ASSURANCE_DOMMAGE_OUVRAGE")
        self.assertIs(lue, NORME_NON_ATTRIBUEE)
        self.assertIn("n'est pas etabli", motif)
        for norme in NORMES_SEUIL:
            self.assertIsNot(lue, norme)

    def test_une_deliberation_qui_arrete_les_deux_montants_ne_se_devine_pas(self):
        """L'alinea autorise l'assemblee a arreter les deux `a la meme
        majorite`: une resolution unique peut donc les porter tous les deux.
        Rien ne dit alors quel montant sert quelle obligation, et choisir
        fabriquerait une norme."""
        lue, motif = norme_arretee(";".join(n.cle for n in NORMES_SEUIL))
        self.assertIs(lue, NORME_NON_ATTRIBUEE)
        self.assertIn("2 montants", motif)
        for norme in NORMES_SEUIL:
            self.assertIn(norme.libelle.lower(), motif,
                          "le motif doit NOMMER les normes en concurrence")

    def test_aucune_qualification_lue_tombe_dans_le_residu_avec_son_motif(self):
        lue, motif = norme_arretee("")
        self.assertIs(lue, NORME_NON_ATTRIBUEE)
        self.assertTrue(motif)


# --------------------------------------------------------------------------
# Le pont: aucun lien perdu, chacun sur sa relation
# --------------------------------------------------------------------------


#: Le cas du corpus reel, reduit a l'essentiel: la meme assemblee du meme jour
#: arrete les deux montants par deux resolutions differentes, et un engagement
#: posterieur tombe sous les deux.
def _corpus_deux_normes_le_meme_jour() -> tuple[list, list, dict]:
    engagement = _acte("ACTE-1", date_effet="2026-04-29")
    consultation = _seuil_vote("SEUIL-26", "2024-07-03", "1000.00", numero="26")
    concurrence = _seuil_vote("SEUIL-27", "2024-07-03", "2000.00", numero="27")
    actes = [engagement, consultation, concurrence]
    candidats = [
        _candidat(engagement, "ENGAGEMENT"),
        _candidat(consultation, NORME_CONSULTATION_CS.cle),
        _candidat(concurrence, NORME_CONCURRENCE.cle),
    ]
    return actes, candidats, {}


class LePontEcritSurLaBonneRelationTests(unittest.TestCase):
    def test_les_deux_montants_du_meme_jour_partent_sur_deux_relations(self):
        actes, candidats, etats = _corpus_deux_normes_le_meme_jour()
        liens = liens_seuil(actes, etats, normes_seuil(candidats, actes))
        self.assertEqual(
            {NORME_CONSULTATION_CS.relation: 1, NORME_CONCURRENCE.relation: 1},
            {r: sum(1 for l in liens if l["relation"] == r)
             for r in {l["relation"] for l in liens}},
        )

    def test_aucun_lien_n_est_perdu_a_la_separation(self):
        """**La garde principale du lot, exprimee comme une conservation.**

        Le compte des liens de seuil ne depend pas du classement: il vaut le
        nombre de couples (engagement, seuil applicable a sa date). Un lien qui
        ne trouverait pas sa relation devait etre declare non attribuable, pas
        disparaitre - donc le total est le meme avant et apres, quelle que soit
        la maniere dont il se repartit.
        """
        actes, candidats, etats = _corpus_deux_normes_le_meme_jour()
        attendus = 2  # un engagement, deux seuils actifs a sa date
        for qualifications in (
            [NORME_CONSULTATION_CS.cle, NORME_CONCURRENCE.cle],   # les deux lues
            ["", ""],                                             # aucune lue
            ["SEUIL_INCONNU", NORME_CONCURRENCE.cle],             # une inconnue
        ):
            with self.subTest(qualifications=qualifications):
                cands = [candidats[0]] + [
                    _candidat(a, q) for a, q in zip(actes[1:], qualifications)
                ]
                liens = liens_seuil(actes, etats, normes_seuil(cands, actes))
                self.assertEqual(attendus, len(liens))
                for lien in liens:
                    self.assertIn(lien["relation"],
                                  {n.relation for n in ENTREES_SEUIL})

    def test_un_seuil_sans_norme_lue_va_au_residu_en_disant_pourquoi(self):
        actes, _, etats = _corpus_deux_normes_le_meme_jour()
        candidats = [
            _candidat(actes[0], "ENGAGEMENT"),
            _candidat(actes[1], "SEUIL_INCONNU"),
            _candidat(actes[2], NORME_CONCURRENCE.cle),
        ]
        liens = liens_seuil(actes, etats, normes_seuil(candidats, actes))
        residus = [l for l in liens if l["relation"] == NORME_NON_ATTRIBUEE.relation]
        self.assertEqual(1, len(residus))
        self.assertIn("n'est pas etabli", residus[0]["doute"],
                      "un residu muet se lit comme une attribution")

    def test_une_norme_non_fournie_ne_devient_pas_une_norme_par_defaut(self):
        """`normes_par_acte` vide: la question n'a pas ete posee.

        C'est le cas d'un appelant qui n'aurait pas cable `normes_seuil`. Le
        lien part au residu avec un motif qui le dit, au lieu de se ranger
        silencieusement chez la premiere norme declaree.
        """
        actes, _, etats = _corpus_deux_normes_le_meme_jour()
        liens = liens_seuil(actes, etats, {})
        self.assertEqual({NORME_NON_ATTRIBUEE.relation},
                         {l["relation"] for l in liens})
        for lien in liens:
            self.assertIn("n'a pas ete recherchee", lien["doute"])

    def test_le_motif_du_lien_nomme_l_obligation_declenchee(self):
        """Un motif qui dirait `consultation ou mise en concurrence` laisserait
        le lecteur devant la meme confusion que le modele portait."""
        actes, candidats, etats = _corpus_deux_normes_le_meme_jour()
        liens = liens_seuil(actes, etats, normes_seuil(candidats, actes))
        par_relation = {l["relation"]: l for l in liens}
        self.assertIn(
            "consultation du conseil syndical",
            par_relation[NORME_CONSULTATION_CS.relation]["motif"])
        self.assertIn(
            "mise en concurrence",
            par_relation[NORME_CONCURRENCE.relation]["motif"])
        self.assertNotIn(
            " ou la mise en concurrence",
            par_relation[NORME_CONSULTATION_CS.relation]["motif"])


# --------------------------------------------------------------------------
# De bout en bout: ce que 121 actes cessent de dire
# --------------------------------------------------------------------------


class LaSeparationTrancheSansArbitrerTests(_Socle):
    def _liens_ecrits(self) -> tuple[list, list]:
        actes, candidats, etats = _corpus_deux_normes_le_meme_jour()
        liens = liens_seuil(actes, etats, normes_seuil(candidats, actes))
        return actes, liens

    def test_deux_normes_du_meme_jour_sont_tranchees_chacune_de_son_cote(self):
        """**Le resultat du lot, de bout en bout.**

        Avant la separation, cet acte portait deux liens sur une seule relation,
        `nb_seuil_ex_aequo` valait 2 et l'ecran declarait `non tranche`. Apres,
        chaque norme est seule sur sa relation: `1` de chaque cote, donc
        tranchee - et **aucune regle d'arbitrage n'a ete ajoutee**. Il n'y avait
        pas de conflit a arbitrer, il y avait une question mal posee.
        """
        actes, liens = self._liens_ecrits()
        ligne = self._matrice(actes, liens)["ACTE-1"]
        for norme in NORMES_SEUIL:
            with self.subTest(norme=norme.cle):
                self.assertEqual(1, ligne["nb_%s" % norme.prefixe])
                self.assertEqual(1, ligne["nb_%s_ex_aequo" % norme.prefixe])
                self.assertEqual("2024-07-03", ligne["cle_%s" % norme.prefixe])
        self.assertEqual(0, ligne["nb_seuil"],
                         "rien ne doit rester dans le residu quand les deux "
                         "normes ont ete lues")

    def test_les_deux_bulles_disent_laquelle_des_deux_elles_rapportent(self):
        actes, liens = self._liens_ecrits()
        ligne = self._matrice(actes, liens)["ACTE-1"]
        bulles = _seuil(ligne, "ENGAGEMENT_DEPENSE")
        self.assertEqual(2, len(bulles),
                         "sans residu, deux bulles et pas trois")
        textes = [b["texte"] for b in bulles]
        self.assertIn("Seuil de consultation du conseil syndical", textes)
        self.assertIn("Seuil de mise en concurrence", textes)
        for texte in textes:
            self.assertNotEqual("Seuil applicable", texte,
                                "une cellule qui dit `seuil` sans dire lequel "
                                "reproduit le defaut a l'affichage")
            self.assertNotIn("non tranché", texte)

    def test_la_bulle_du_residu_n_apparait_que_lorsqu_il_y_a_un_residu(self):
        actes, _, etats = _corpus_deux_normes_le_meme_jour()
        candidats = [
            _candidat(actes[0], "ENGAGEMENT"),
            _candidat(actes[1], "SEUIL_INCONNU"),
            _candidat(actes[2], NORME_CONCURRENCE.cle),
        ]
        liens = liens_seuil(actes, etats, normes_seuil(candidats, actes))
        ligne = self._matrice(actes, liens)["ACTE-1"]
        bulles = _seuil(ligne, "ENGAGEMENT_DEPENSE")
        self.assertEqual(3, len(bulles))
        self.assertIn("Seuil rattaché, norme non attribuée",
                      [b["texte"] for b in bulles])

    def test_deux_deliberations_de_la_MEME_norme_le_meme_jour_restent_non_tranchees(self):
        """La separation ne doit pas rendre tranchable ce qui ne l'est pas.

        Deux montants arretes le meme jour pour la MEME obligation sont un vrai
        conflit, et la garde du lot precedent doit continuer de le declarer.
        Sans ce test, il suffirait de tout separer pour faire disparaitre les
        ex aequo - c'est-a-dire de resoudre la mesure au lieu du probleme.
        """
        engagement = _acte("ACTE-1", date_effet="2026-04-29")
        un = _seuil_vote("SEUIL-A", "2024-07-03", "1000.00", numero="26")
        deux = _seuil_vote("SEUIL-B", "2024-07-03", "2000.00", numero="26bis")
        actes = [engagement, un, deux]
        candidats = [
            _candidat(engagement, "ENGAGEMENT"),
            _candidat(un, NORME_CONCURRENCE.cle),
            _candidat(deux, NORME_CONCURRENCE.cle),
        ]
        liens = liens_seuil(actes, {}, normes_seuil(candidats, actes))
        ligne = self._matrice(actes, liens)["ACTE-1"]
        self.assertEqual(2, ligne["nb_%s" % NORME_CONCURRENCE.prefixe])
        self.assertEqual(2, ligne["nb_%s_ex_aequo" % NORME_CONCURRENCE.prefixe])
        bulle = [b for b in _seuil(ligne, "ENGAGEMENT_DEPENSE")
                 if NORME_CONCURRENCE.libelle in b["texte"]][0]
        self.assertIn("non tranché", bulle["texte"])

    def test_toute_entree_declaree_obtient_une_bulle(self):
        """**Aucune norme declaree ne reste invisible a l'ecran.**

        Le premier jet de ce lot enumerait les deux prefixes en dur dans
        `_seuil`. Une troisieme norme declaree aurait recu sa relation, ses
        liens et ses colonnes de matrice - et aucune bulle. Le defaut corrige
        dans le modele serait revenu au dernier metre, sous la forme la plus
        difficile a voir: pas une phrase fausse, une absence.

        Le residu est inclus dans la mesure, en lui donnant de quoi s'afficher:
        il ne se montre que lorsqu'il porte quelque chose, et c'est justement
        ce qu'on veut verifier.
        """
        actes, _, etats = _corpus_deux_normes_le_meme_jour()
        candidats = [
            _candidat(actes[0], "ENGAGEMENT"),
            _candidat(actes[1], "SEUIL_INCONNU"),
            _candidat(actes[2], NORME_CONCURRENCE.cle),
        ]
        liens = liens_seuil(actes, etats, normes_seuil(candidats, actes))
        ligne = self._matrice(actes, liens)["ACTE-1"]
        bulles = _seuil(ligne, "ENGAGEMENT_DEPENSE")
        self.assertEqual(
            [n.prefixe for n in ENTREES_SEUIL], [b["norme"] for b in bulles],
            "une entree declaree sans bulle disparait de l'ecran en silence",
        )
        for bulle, entree in zip(bulles, ENTREES_SEUIL, strict=True):
            with self.subTest(norme=entree.prefixe):
                self.assertTrue(bulle["texte"].strip(),
                                "une bulle sans texte ne nomme aucune norme")

    def test_un_appariement_qui_diverge_leve_au_lieu_de_decaler(self):
        """Une norme attribuee au mauvais acte laisserait tous les comptes justes.

        `normes_seuil` apparie candidats et actes par leur rang. Un appelant qui
        filtrerait l'une des deux listes decalerait les normes d'un cran: le
        nombre de liens resterait exact, leur repartition serait fausse, et
        aucune mesure de ce lot ne le verrait. `strict` en fait une erreur.
        """
        actes, candidats, _ = _corpus_deux_normes_le_meme_jour()
        with self.assertRaises(ValueError):
            normes_seuil(candidats[:-1], actes)

    def test_un_controle_retire_ne_repete_pas_son_motif_par_norme(self):
        """Une designation d'organe ne passe aucun marche: le retrait est unique,
        et une seule phrase le dit. Trois bulles `non exige ici` sur les
        cinquante-cinq designations et modalites d'une assemblee seraient du
        bruit, pas de l'information."""
        actes, liens = self._liens_ecrits()
        ligne = dict(self._matrice(actes, liens)["ACTE-1"])
        for entree in ENTREES_SEUIL:
            ligne["cel_%s" % entree.prefixe] = "NON_APPLICABLE"
        bulles = _seuil(ligne, "DESIGNATION_ORGANE")
        self.assertEqual(1, len(bulles))
        self.assertEqual("non_applicable", bulles[0]["statut"])


if __name__ == "__main__":
    unittest.main()
