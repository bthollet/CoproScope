"""Le seuil applicable est le dernier vote, et une egalite se declare.

Regle de Brice, donnee deux fois le 2026-09-08 a deux fils independamment:
*la question des seuils, c'est le dernier qu'il faut retenir; la question de
l'ambiguite ne se pose pas, c'est le dernier vote*. Et la degradation qu'elle
exige, qui est le vrai livrable: **deux deliberations a la meme date, ou une
date illisible, ne se departagent pas - elles se declarent non tranchees. Un
identifiant n'est pas une chronologie.**

Ce que ce fichier garde tient en une phrase: **le modele avait un seul ordre
pour deux questions.** `ORDRE_PROBANT` trie par provenance, puis force
probatoire, puis `lien_id`. C'est le bon ordre pour une assertion sur un FAIT -
*quel est le montant de ce devis* se tranche par la qualite de la piece. C'est
le mauvais pour une NORME posee par un vote: une deliberation plus recente
abroge la precedente, meme quand la piece qui atteste l'ancienne est meilleure.
Et sa derniere clause departageait deux seuils egaux par leur identifiant de
lien, c'est-a-dire par le rang de la resolution dans la convocation.

**Pourquoi les cas sont construits ici et non empruntes a une instance.**
Mesure du 2026-09-08 sur les coffres disponibles: 299 liens de seuil, tous
vises sur des deliberations du MEME jour. Le corpus reel ne contient donc
aucun conflit chronologique - il ne contient que des egalites. Un test qui en
dependrait ne mesurerait jamais l'ordre lui-meme. Les deux situations sont
posees a la main, avec l'ecart maximal entre elles.

**Ce que le corpus reel a appris, et qui n'est pas garde ici.** Les deux
seuils du meme jour sont deux resolutions distinctes: l'une fixe le montant a
partir duquel la consultation du conseil syndical devient obligatoire, l'autre
celui a partir duquel la mise en concurrence l'est. Deux normes, pas deux
reponses concurrentes a une meme question. Le modele ne les distingue pas
encore; ces tests garantissent seulement qu'il ne choisit pas entre elles en
silence.
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
    ORDRE_PROBANT,
    RelationSansOrdre,
    ordre_de,
)
from coproscope.modules._actes_seuils_normes import (
    ENTREES_SEUIL,
    NORME_NON_ATTRIBUEE,
)
from coproscope.web._controle_gouvernance_cellules import _seuil


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


def _seuil_vote(acte_id: str, date: str, montant: str) -> dict[str, str]:
    """Une deliberation qui arrete un seuil, a une date donnee."""
    return _acte(acte_id, portee="SEUIL", date_effet=date,
                 montant_autorise=montant, valide_du=date or "")


def _lien(lien_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "lien_id": lien_id, "source_kind": "acte", "source_id": "ACTE-1",
        "relation": "SEUIL_APPLICABLE", "target_kind": "acte",
        "target_id": "SEUIL-ANCIEN", "provenance": "COPROSCOPE_CALCULE",
        "force_probatoire": "PIECE_PRODUITE", "motif": "", "doute": "",
        "montant_impute": "", "libelle_cible": "", "echeance": "",
        "constate_le": "2026-04-29", "auteur": "", "page": "2",
        "ancre": "segment 12", "doc_id": "DOC-CONVOCATION", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _bulle_de(ligne: dict[str, object], prefixe: str = "") -> dict[str, object]:
    """La bulle de seuil d'une norme donnee, designee par son nom.

    La colonne des seuils rend une bulle PAR norme depuis `RM-2026-0144`. Ce
    fichier garde l'ORDRE et non l'attribution, donc ses fixtures alimentent la
    relation residuelle - un seuil rattache dont l'obligation declenchee n'a pas
    ete identifiee - qui se tranche par la meme chronologie que les deux autres.
    La bulle se designe par `norme` et jamais par son rang: l'ajout d'une norme
    ne doit pas deplacer en silence ce que ce fichier croit lire.
    """
    voulu = prefixe or NORME_NON_ATTRIBUEE.prefixe
    return [b for b in _seuil(ligne, "ENGAGEMENT_DEPENSE")
            if b["norme"] == voulu][0]


def _ligne_cellules(**kw: object) -> dict[str, object]:
    """Une ligne de matrice construite a la main, avec TOUTES ses cellules.

    Les cellules absentes valent `ABSENT`, ce qui est un statut a part entiere.
    On les pose explicitement plutot que de rendre `_seuil` tolerant aux
    colonnes manquantes: une colonne renommee doit lever, pas afficher
    `Source manquante` sur une norme qui existe.
    """
    ligne: dict[str, object] = {
        "cel_%s" % n.prefixe: "ABSENT" for n in ENTREES_SEUIL
    }
    ligne.update(kw)
    return ligne


class _Instance:
    display_name = "Copropriete de recette"

    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict[str, object]:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / str(valeur).lstrip("./")).resolve()


class _Socle(unittest.TestCase):
    """Une instance jetable par MESURE, et non par test.

    Un test qui compare deux jeux de liens - c'est le cas de l'egalite lue dans
    les deux sens - les ecrirait sinon dans le meme coffre, et le second
    passage mesurerait la somme des deux. Chaque appel cree donc son coffre et
    l'inscrit au nettoyage.
    """

    def setUp(self) -> None:
        self._coffres: list[Path] = []

    def tearDown(self) -> None:
        for racine in self._coffres:
            shutil.rmtree(racine, ignore_errors=True)

    def _ligne(self, actes: list[dict[str, str]],
               liens: list[dict[str, str]]) -> dict[str, object]:
        racine = Path(tempfile.mkdtemp())
        self._coffres.append(racine)
        instance = _Instance(racine)
        A.ecrire(instance, A.TABLE_ACTES, actes,
                 sorted({a["doc_id"] for a in actes}))
        if liens:
            A.ecrire(instance, A.TABLE_LIENS, liens,
                     sorted({l["doc_id"] for l in liens}))
        return {l["acte_id"]: l for l in A.matrice(instance)}["ACTE-1"]

    def _bulle(self, actes: list[dict[str, str]],
               liens: list[dict[str, str]]) -> dict[str, object]:
        """La bulle de la norme que les fixtures alimentent.

        Depuis la separation des deux normes (`RM-2026-0144`, 2026-09-08), la
        colonne des seuils rend une bulle PAR norme. Les liens montes ici
        portent la relation residuelle - un seuil rattache dont l'obligation
        declenchee n'a pas ete identifiee - et c'est volontaire: ce fichier
        garde l'ORDRE, pas l'attribution, et le residu se tranche par la meme
        chronologie que les deux autres. La bulle est designee par son prefixe
        et non par son rang, pour qu'un ajout de norme ne deplace pas ce test
        sans le casser.
        """
        return _bulle_de(self._ligne(actes, liens))


#: Le cas qui separe les deux ordres, et le seul qui les separe vraiment: le
#: seuil le plus RECENT est le MOINS bien prouve. L'ordre probant retiendrait
#: l'ancien, la chronologie retient le recent. Aucun autre montage ne rend la
#: difference visible.
_LE_RECENT_EST_LE_MOINS_PROUVE = (
    [
        _acte("ACTE-1"),
        _seuil_vote("SEUIL-ANCIEN", "2022-01-10", "1000.00"),
        _seuil_vote("SEUIL-RECENT", "2024-07-03", "5000.00"),
    ],
    [
        _lien("L-ANCIEN", target_id="SEUIL-ANCIEN",
              provenance="HUMAIN_CONFIRME", force_probatoire="PIECE_PRODUITE",
              page="2"),
        _lien("L-RECENT", target_id="SEUIL-RECENT",
              provenance="SYNDIC_AFFIRME", force_probatoire="AFFIRME_SANS_PIECE",
              page="9"),
    ],
)

#: Deux deliberations le meme jour, differentes en tout sauf la date. C'est le
#: cas du corpus reel, et c'est celui ou l'ancien code choisissait par
#: identifiant de lien.
_LE_MEME_JOUR = (
    [
        _acte("ACTE-1"),
        _seuil_vote("SEUIL-A", "2024-07-03", "1000.00"),
        _seuil_vote("SEUIL-B", "2024-07-03", "2000.00"),
    ],
    [
        _lien("L-AAA", target_id="SEUIL-A", force_probatoire="PIECE_PRODUITE",
              page="2"),
        _lien("L-ZZZ", target_id="SEUIL-B",
              force_probatoire="AFFIRME_SANS_PIECE", page="9"),
    ],
)


class LeDernierVoteLEmporteTests(_Socle):
    """La norme se tranche par la date du vote, pas par la qualite du papier."""

    def test_le_seuil_le_plus_recent_bat_le_mieux_prouve(self) -> None:
        """**Le test central du lot.**

        L'ancien seuil est confirme par un humain et produit en piece; le
        recent est seulement affirme par le syndic. L'ordre probant retiendrait
        l'ancien - et le produit annoncerait comme applicable un seuil abroge
        deux ans plus tot, avec l'assurance d'une piece a l'appui.
        """
        actes, liens = _LE_RECENT_EST_LE_MOINS_PROUVE
        ligne = self._ligne(actes, liens)
        self.assertEqual(
            ligne["cle_seuil"], "2024-07-03",
            "la deliberation retenue doit etre la plus recente")
        self.assertEqual(
            ligne["src_seuil_page"], "9",
            "la page citee doit etre celle du seuil retenu, pas du mieux prouve")
        self.assertEqual(
            ligne["cel_seuil"], A.FORCE_AFFIRME,
            "la force affichee est celle de l'assertion retenue: un seuil "
            "recent mal prouve reste mal prouve, et l'ecran doit le dire")

    def test_l_ordre_d_insertion_ne_change_pas_le_seuil_retenu(self) -> None:
        """Sans `ORDER BY`, SQLite rend les lignes dans l'ordre trouve.

        Le meme jeu ecrit dans l'autre sens doit donner exactement la meme
        reponse: sinon le seuil applicable depend de l'ordre d'ecriture, ce qui
        peut basculer a une reconstruction sans changement de code.
        """
        actes, liens = _LE_RECENT_EST_LE_MOINS_PROUVE
        ligne = self._ligne(actes, list(reversed(liens)))
        self.assertEqual(ligne["cle_seuil"], "2024-07-03")
        self.assertEqual(ligne["src_seuil_page"], "9")

    def test_la_cellule_nomme_la_date_qui_a_tranche(self) -> None:
        """`le seuil retenu` ne se verifie pas; `le seuil du 2024-07-03` si.

        Un coproprietaire doit pouvoir aller lire la deliberation nommee. Une
        phrase qui ne nomme pas sa date demande de croire l'outil sur parole.
        """
        actes, liens = _LE_RECENT_EST_LE_MOINS_PROUVE
        bulle = self._bulle(actes, liens)
        self.assertIn("2024-07-03", bulle["detail"])
        self.assertIn("dernier vote", bulle["detail"])
        self.assertNotIn("non tranché", bulle["texte"])


class UnIdentifiantNEstPasUneChronologieTests(_Socle):
    """**La garde nommee par Brice.** Deux egaux ne se departagent pas.

    C'est la regression exacte a empecher: un `ORDER BY` rend toujours une
    ligne, meme quand rien ne la designe. Le tri finissait par `l.lien_id`, si
    bien que le seuil applicable etait celui dont la resolution portait le plus
    petit numero - une regle que personne n'a votee et que rien n'affichait.
    """

    def test_deux_deliberations_du_meme_jour_se_declarent_non_tranchees(self) -> None:
        actes, liens = _LE_MEME_JOUR
        ligne = self._ligne(actes, liens)
        self.assertEqual(ligne["nb_seuil"], 2)
        self.assertEqual(
            ligne["nb_seuil_ex_aequo"], 2,
            "les deux deliberations partagent la date retenue: aucune n'est "
            "designee")
        bulle = _bulle_de(ligne)
        self.assertIn("non tranché", bulle["texte"])
        self.assertEqual(bulle["statut"], "confirmer")
        self.assertIn("2024-07-03", bulle["detail"])
        self.assertIn("ne se départagent pas", bulle["detail"])

    def test_l_egalite_tient_quel_que_soit_l_ordre_des_identifiants(self) -> None:
        """Le verdict ne doit pas dependre de quel identifiant vient en premier.

        Les deux liens sont reecrits avec leurs identifiants echanges. Si un
        departage par identifiant revenait, l'un des deux passages
        presenterait un seuil comme retenu.
        """
        actes, liens = _LE_MEME_JOUR
        echanges = [
            dict(liens[0], lien_id="L-ZZZ"),
            dict(liens[1], lien_id="L-AAA"),
        ]
        for nom, jeu in (("ordre initial", liens),
                         ("identifiants echanges", echanges)):
            with self.subTest(nom):
                bulle = self._bulle(actes, jeu)
                self.assertIn("non tranché", bulle["texte"])
                self.assertEqual(bulle["statut"], "confirmer")

    def test_l_ordre_chronologique_n_a_aucun_departage_de_secours(self) -> None:
        """**La garde structurelle: elle echoue le jour ou `lien_id` revient.**

        Le test de comportement ci-dessus protege le lecteur; celui-ci protege
        la regle. Un tri qui reprendrait une colonne unique par lien -
        `lien_id`, `constate_le`, `doc_id`, `page` - trancherait toujours, et
        `nb_*_ex_aequo` ne verrait plus jamais d'egalite: le defaut
        redeviendrait invisible sans qu'aucun test de comportement ne bouge.
        """
        for colonne in ("lien_id", "constate_le", "doc_id", "page", "rowid"):
            with self.subTest(colonne=colonne):
                self.assertNotIn(
                    colonne, ORDRE_CHRONOLOGIQUE.tri,
                    f"{colonne!r} departagerait deux deliberations que la "
                    "chronologie laisse a egalite. Un identifiant n'est pas "
                    "une chronologie: si un tri stable est necessaire, il ne "
                    "doit pas passer par le tri qui decide.")
                self.assertNotIn(
                    colonne, ORDRE_CHRONOLOGIQUE.cle,
                    f"{colonne!r} dans la cle rendrait toute egalite unique, "
                    "donc tout conflit invisible")


class UneDateQuiManqueNeTranchePasTests(_Socle):
    """Hors des valeurs observees, le code se degrade au lieu de repondre faux."""

    def test_une_deliberation_sans_date_lue_ne_designe_aucun_seuil(self) -> None:
        """Le cas existe dans le corpus: `ACTE-AG-SANS-DATE-...` y est ecrit.

        Deux seuils dont aucune date n'a ete lue ne peuvent pas se classer. La
        cellule doit le dire et nommer la cause - l'absence de date - au lieu
        de retenir le premier venu.
        """
        actes = [_acte("ACTE-1"),
                 _seuil_vote("SEUIL-A", "", "1000.00"),
                 _seuil_vote("SEUIL-B", "", "2000.00")]
        liens = [_lien("L-A", target_id="SEUIL-A"),
                 _lien("L-B", target_id="SEUIL-B")]
        ligne = self._ligne(actes, liens)
        self.assertEqual(ligne["cle_seuil"], "")
        bulle = _bulle_de(ligne)
        self.assertIn("non tranché", bulle["texte"])
        self.assertIn("n'a pas été lue", bulle["detail"])

    def test_une_cible_qui_n_est_pas_un_acte_ne_gagne_pas_par_accident(self) -> None:
        """`target_kind` est polymorphe par conception: la jointure peut rater.

        C'est la valeur inconnue sur l'axe: un lot futur pourrait viser un
        document. La jointure ne trouve alors pas de deliberation, la date vaut
        la chaine vide, et le seuil perd contre toute deliberation datee au
        lieu d'etre retenu sans date.
        """
        actes = [_acte("ACTE-1"),
                 _seuil_vote("SEUIL-DATE", "2024-07-03", "5000.00")]
        liens = [_lien("L-DOC", target_kind="document", target_id="DOC-VOISIN",
                       page="41"),
                 _lien("L-ACTE", target_id="SEUIL-DATE", page="9")]
        ligne = self._ligne(actes, liens)
        self.assertEqual(ligne["cle_seuil"], "2024-07-03")
        self.assertEqual(ligne["src_seuil_page"], "9")
        self.assertEqual(
            ligne["nb_seuil_ex_aequo"], 1,
            "une cible sans date ne partage pas la date retenue")

    def test_un_seul_seuil_sans_date_est_retenu_mais_pas_comme_le_dernier(self) -> None:
        """Un seul seuil n'a personne a departager: il est retenu.

        Mais la phrase ne doit pas lui attribuer une anciennete qu'elle n'a pas
        mesuree. `retenu parce qu'il est seul` et `retenu parce qu'il est le
        plus recent` ne sont pas la meme affirmation devant un syndic.
        """
        actes = [_acte("ACTE-1"), _seuil_vote("SEUIL-A", "", "1000.00")]
        bulle = self._bulle(actes, [_lien("L-A", target_id="SEUIL-A")])
        self.assertNotIn("non tranché", bulle["texte"])
        self.assertIn("parce qu'il est seul", bulle["detail"])
        self.assertNotIn("dernier vote", bulle["detail"])


class LaCelluleNImprimeJamaisUneNonDateTests(unittest.TestCase):
    """Trouve par le controle negatif, et garde depuis.

    En remettant l'ordre probant sur les seuils, la cellule a imprime
    `Seuil arrete par la deliberation du HUMAIN_CONFIRME/PIECE_PRODUITE`. Elle
    recopiait la valeur qui avait tranche en supposant que c'etait une date -
    ce qui est vrai sous l'ordre chronologique et faux sous tout autre. La
    colonne ne porte pas son type; la cellule doit donc le verifier.

    Ces cas s'appellent sur une ligne construite a la main, parce qu'ils
    decrivent ce que la cellule fait d'une valeur que la vue n'est pas censee
    produire. C'est exactement le test d'acceptation du depot: hors des valeurs
    observees, degradation propre ou reponse fausse en silence.
    """

    def _bulle(self, cle: object, nb: int = 1, ex_aequo: int = 1) -> dict[str, object]:
        ligne = _ligne_cellules(
            cel_seuil="PIECE_PRODUITE", nb_seuil=nb,
            nb_seuil_ex_aequo=ex_aequo, cle_seuil=cle)
        return _bulle_de(ligne)

    def test_une_force_probatoire_n_est_pas_presentee_comme_une_date(self) -> None:
        detail = self._bulle("HUMAIN_CONFIRME/PIECE_PRODUITE")["detail"]
        self.assertNotIn("HUMAIN_CONFIRME", detail)
        self.assertIn("n'a pas été lue", detail)

    def test_une_date_ecrite_a_la_francaise_reste_lisible(self) -> None:
        """L'invariant est `un jour, un mois, une annee`, pas un format.

        Un coffre ecrit en `jj/mm/aaaa` ne doit pas perdre sa date: elle est
        normalisee, pas rejetee.
        """
        self.assertIn("2024-07-03", self._bulle("03/07/2024")["detail"])

    def test_une_valeur_vide_fait_dire_que_la_date_manque(self) -> None:
        self.assertIn("n'a pas été lue", self._bulle("")["detail"])

    def test_la_colonne_absente_fait_douter_et_non_conclure(self) -> None:
        """La degradation d'une mesure manquante est le doute, pas la confiance.

        C'est le contrat des appelants qui construisent la ligne eux-memes -
        `test_affirmations_prouvees` en est un. Sans `nb_seuil_ex_aequo`, deux
        seuils rattaches ne peuvent pas etre declares departages.
        """
        bulle = _bulle_de(
            _ligne_cellules(cel_seuil="PIECE_PRODUITE", nb_seuil=2))
        self.assertIn("non tranché", bulle["texte"])
        self.assertEqual(bulle["statut"], "confirmer")


class LaCelluleNAvouePlusUneNonRegleTests(_Socle):
    """Un ecran qui decrit son propre defaut le publie, il ne le corrige pas."""

    def test_aucune_phrase_ne_renvoie_a_un_ordre_d_identifiant(self) -> None:
        for nom, (actes, liens) in (
            ("chronologie tranchee", _LE_RECENT_EST_LE_MOINS_PROUVE),
            ("egalite", _LE_MEME_JOUR),
        ):
            with self.subTest(nom):
                detail = self._bulle(actes, liens)["detail"]
                self.assertNotIn("identifiant", detail)
                self.assertNotIn("n'est pas une règle", detail)

    def test_la_contradiction_n_est_plus_affirmee_sans_mesure(self) -> None:
        """Deux seuils du meme jour ne sont pas forcement contradictoires.

        Mesure du 2026-09-08 sur deux coffres: les deux seuils du meme jour
        sont la consultation du conseil syndical et la mise en concurrence -
        deux normes distinctes. Le modele ne sait pas les distinguer; il n'a
        donc pas le droit de les declarer contradictoires.
        """
        actes, liens = _LE_MEME_JOUR
        detail = self._bulle(actes, liens)["detail"]
        self.assertNotIn("contredisent", detail)
        self.assertNotIn("contradictoire", detail)


class ChaqueRelationDeclareSonOrdreTests(unittest.TestCase):
    """L'ordre est declare relation par relation, jamais herite."""

    def test_les_sept_relations_liees_declarent_un_ordre(self) -> None:
        self.assertEqual(
            set(ORDRE_PAR_RELATION), set(CELLULES_LIEES),
            "une cellule liee sans ordre declare prendrait celui du voisin")

    def test_seul_le_seuil_se_tranche_par_la_chronologie(self) -> None:
        """Les autres relations portent des constats sur des pieces.

        Un devis plus recent n'abroge pas le precedent, et un avis de conseil
        syndical non plus: c'est la meilleure piece qui fait foi. Basculer une
        de ces relations en chronologie changerait la reponse du produit sans
        qu'aucune regle de droit ne le demande.
        """
        # Depuis le 2026-09-08 (`RM-2026-0144`), les relations de seuil sont
        # TROIS: les deux normes de l'article 21 alinea 2 et le residu de
        # celles qu'on n'a pas su attribuer. Elles se lisent au registre au
        # lieu d'etre nommees ici, sinon une quatrieme entree y serait
        # silencieusement attendue probante.
        chronologiques = {n.relation for n in ENTREES_SEUIL}
        for relation in CELLULES_LIEES:
            attendu = (ORDRE_CHRONOLOGIQUE if relation in chronologiques
                       else ORDRE_PROBANT)
            with self.subTest(relation=relation):
                self.assertIs(ordre_de(relation), attendu)

    def test_une_relation_inconnue_leve_au_lieu_de_devenir_probante(self) -> None:
        with self.assertRaises(RelationSansOrdre):
            ordre_de("RELATION_QUI_N_EXISTE_PAS")


class LOrdreProbantDesAutresRelationsEstIntactTests(_Socle):
    """Le lot ne devait toucher que le seuil: voici la preuve qu'il l'a tenu."""

    def test_le_devis_le_mieux_prouve_gagne_encore_sur_le_plus_recent(self) -> None:
        """Le meme montage que pour le seuil, sur `DEVIS_RETENU`.

        Si la chronologie avait debordé sur les autres relations, ce test
        retiendrait le devis seulement affirme par le syndic.
        """
        liens = [
            _lien("L-DEVIS-VIEUX", relation="DEVIS_RETENU",
                  target_kind="devis_cite", target_id="DEVIS-VIEUX",
                  provenance="HUMAIN_CONFIRME", force_probatoire="PIECE_PRODUITE",
                  constate_le="2020-01-01", page="4"),
            _lien("L-DEVIS-NEUF", relation="DEVIS_RETENU",
                  target_kind="devis_cite", target_id="DEVIS-NEUF",
                  provenance="SYNDIC_AFFIRME",
                  force_probatoire="AFFIRME_SANS_PIECE",
                  constate_le="2026-01-01", page="22"),
        ]
        ligne = self._ligne([_acte("ACTE-1")], liens)
        self.assertEqual(ligne["cel_devis"], A.FORCE_PIECE)
        self.assertEqual(ligne["src_devis_page"], "4")
        self.assertEqual(
            ligne["cle_devis"], "HUMAIN_CONFIRME/PIECE_PRODUITE",
            "la cle du devis reste la force probatoire, pas une date")

    def test_deux_devis_egaux_sont_comptes_comme_egaux(self) -> None:
        """L'egalite silencieuse existe aussi sur l'ordre probant.

        Deux devis de meme provenance et de meme force y sont departages par
        `lien_id`. Ce lot ne change pas cet ordre - il rend l'egalite
        mesurable, pour que le prochain lot sache combien de cas sont
        concernes au lieu de l'estimer.
        """
        liens = [
            _lien("L-A", relation="DEVIS_RETENU", target_kind="devis_cite",
                  target_id="DEVIS-A"),
            _lien("L-B", relation="DEVIS_RETENU", target_kind="devis_cite",
                  target_id="DEVIS-B"),
        ]
        ligne = self._ligne([_acte("ACTE-1")], liens)
        self.assertEqual(ligne["nb_devis"], 2)
        self.assertEqual(ligne["nb_devis_ex_aequo"], 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
