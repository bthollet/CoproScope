"""Le journal d'observation d'un extranet, eprouve sur ses promesses.

Chaque test porte le nom de la promesse qu'il tient, pas celui de la fonction
qu'il appelle. Plusieurs encodent un piege **reellement mesure** le 2026-09-04
sur un extranet en service; ils portent la mesure dans leur docstring, pour
qu'un echec dise ce que le produit ne fait plus et pourquoi cela comptait.

Aucune donnee reelle: tout le HTML de ce fichier est synthetique.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import _extranet_journal as J
from coproscope.modules._extranet_schema import RUBRIQUE_ECHEC as S_RUBRIQUE_ECHEC
from coproscope.modules._extranet_schema import RUBRIQUE_PARCOURUE as S_RUBRIQUE_PARCOURUE
from coproscope.modules import _extranet_store as S
from coproscope.modules import extranetops as X
from coproscope.modules._extranet_adaptateur import PROFIL_COPRODIRECTE, lire_index
from coproscope.modules._extranet_schema import (
    CLOTURE_AUCUNE,
    CLOTURE_CONSTATEE,
    CONTENU_VERIFIE,
    EMPLACEMENT_INDETERMINE,
    EMPLACEMENT_QUALIFIE,
    ORIGINE_CORRIGE,
    RUBRIQUE_NON_EXPLOREE,
)


class _Instance:
    """Instance minimale: seul le coffre local compte pour ce magasin."""

    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()


def _ligne_piece(libelle: str) -> str:
    """Une piece telle que l'editeur mesure la sert: DEUX liens, icone et libelle."""
    return (
        "<tr class='just'>"
        "<td class='tdPdf'><a class='pj pdf' href='documents/JETON-A' target='_blank'></a></td>"
        f"<td class='pl2'><a href='documents/JETON-B' target='_blank'>{libelle}</a></td>"
        "</tr>"
    )


def _groupe(titre: str) -> str:
    return f"<tr><td colspan='2'>{titre}</td></tr>"


def _page(blocs: str, pagination: bool = False) -> str:
    nav = "<div class='pagination'><a href='#'>suivant</a></div>" if pagination else ""
    return f"<html><body><div id='documents'>{blocs}{nav}</div></body></html>"


def _bloc(code: str, contenu: str) -> str:
    return f"<div class='{code} mt3'><table class='tableDoc'><tbody>{contenu}</tbody></table></div>"


#: Un index qui reproduit le piege mesure: huit libelles identiques repetes sur
#: plusieurs exercices, l'exercice n'etant porte que par l'en-tete de groupe.
INDEX_ARRETES = _page(
    _bloc(
        "ARR",
        _groupe("Au 31/12/2025")
        + _ligne_piece("Annexe 1")
        + _ligne_piece("Annexe 2")
        + _groupe("Au 31/12/2024")
        + _ligne_piece("Annexe 1")
        + _ligne_piece("Annexe 2"),
    )
)


class AdaptateurTests(unittest.TestCase):
    def test_deux_liens_par_piece_ne_font_qu_une_piece(self) -> None:
        """Mesure du 2026-09-04: 230 liens pour 115 pieces sur l'index reel.

        Une icone et un libelle designent la meme piece. Les compter deux fois
        doublerait tout l'index et ferait apparaitre des ajouts fantomes.
        """
        lu = lire_index(INDEX_ARRETES, PROFIL_COPRODIRECTE, "P1")
        self.assertEqual(len(lu["pieces"]), 4)

    def test_le_libelle_seul_ne_suffit_pas_a_distinguer_deux_exercices(self) -> None:
        """Mesure: le libelle seul donne 32 collisions sur 115 pieces, soit 28 %.

        L'exercice vit dans l'en-tete de groupe. Une cle qui l'ignore fusionne
        cinq exercices d'annexes comptables **en silence**, et fait donc
        disparaitre des retraits reels.
        """
        lu = lire_index(INDEX_ARRETES, PROFIL_COPRODIRECTE, "P1")
        libelles = [p["libelle"] for p in lu["pieces"]]
        emplacements = [p["emplacement"] for p in lu["pieces"]]
        self.assertEqual(len(set(libelles)), 2, "le piege doit bien etre present")
        self.assertEqual(len(set(emplacements)), 4, "la cle doit les distinguer")

    def test_le_groupe_entre_dans_la_cle(self) -> None:
        lu = lire_index(INDEX_ARRETES, PROFIL_COPRODIRECTE, "P1")
        groupes = {p["groupe"] for p in lu["pieces"]}
        self.assertEqual(groupes, {"Au 31/12/2025", "Au 31/12/2024"})

    def test_une_rubrique_absente_de_la_page_est_non_exploree_et_non_vide(self) -> None:
        """La distinction qui rend un retrait affirmable.

        Sept rubriques ne figurent pas dans cet index. Les declarer vides
        autoriserait a conclure que toutes leurs pieces ont ete retirees.
        """
        lu = lire_index(INDEX_ARRETES, PROFIL_COPRODIRECTE, "P1")
        etats = {r["rubrique_code"]: r["etat"] for r in lu["rubriques"]}
        self.assertEqual(etats["ASS"], RUBRIQUE_NON_EXPLOREE)
        self.assertEqual(len(etats), len(PROFIL_COPRODIRECTE.rubriques))

    def test_le_code_de_rubrique_ne_se_deduit_pas_du_libelle(self) -> None:
        """Mesure: la rubrique intitulee *Documents techniques* porte le code `DIA`.

        Un adaptateur qui deduirait l'un de l'autre se tromperait des la
        premiere categorie, et silencieusement.
        """
        self.assertEqual(PROFIL_COPRODIRECTE.rubriques["DIA"], "Documents techniques")
        self.assertNotIn("TEC", PROFIL_COPRODIRECTE.rubriques)

    def test_une_piece_sans_libelle_est_journalisee_mais_jamais_comparee(self) -> None:
        """Axe 2 hors des valeurs observees: un editeur qui ne sert qu'une icone.

        Le journal dit *j'ai vu des pieces que je ne sais pas nommer*, ce qui
        est vrai, plutot que d'inventer leur nom.
        """
        page = _page(
            _bloc(
                "CON",
                "<tr><td><a class='pj pdf' href='documents/X'></a></td></tr>",
            )
        )
        lu = lire_index(page, PROFIL_COPRODIRECTE, "P1")
        self.assertEqual(len(lu["pieces"]), 1)
        self.assertEqual(lu["pieces"][0]["emplacement_qualite"], EMPLACEMENT_INDETERMINE)

    def test_une_pagination_interdit_de_conclure_a_une_liste_complete(self) -> None:
        avec = lire_index(_page(_bloc("ARR", _ligne_piece("A")), pagination=True),
                          PROFIL_COPRODIRECTE, "P1")
        sans = lire_index(_page(_bloc("ARR", _ligne_piece("A"))), PROFIL_COPRODIRECTE, "P1")
        self.assertEqual(avec["rubriques"][0]["cloture"], CLOTURE_AUCUNE)
        self.assertEqual(sans["rubriques"][0]["cloture"], CLOTURE_CONSTATEE)


def _passage(pieces: list[dict], rubriques: list[dict], ident: str = "P") -> dict:
    return {
        "passage": {"passage_id": ident},
        "rubriques": rubriques,
        "pieces": pieces,
    }


def _piece(cle: str, empreinte: str = "", **kw) -> dict:
    ligne = {
        "emplacement": cle,
        "emplacement_qualite": EMPLACEMENT_QUALIFIE,
        "rubrique_code": cle.split("\x1f")[0],
        "empreinte": empreinte,
        "contenu_etat": CONTENU_VERIFIE if empreinte else "NON_VERIFIE",
        "nom_serveur": "",
    }
    ligne.update(kw)
    return ligne


def _rub(code: str, etat: str = "PARCOURUE", cloture: str = CLOTURE_CONSTATEE) -> dict:
    return {"rubrique_code": code, "etat": etat, "cloture": cloture}


class DerivationTests(unittest.TestCase):
    def test_une_piece_disparue_dans_une_rubrique_couverte_est_un_retrait(self) -> None:
        avant = _passage([_piece("ARR\x1f2025\x1fAnnexe 1")], [_rub("ARR")])
        apres = _passage([], [_rub("ARR")])
        res = J.comparer(avant, apres)
        self.assertEqual(res["comptes"].get(J.RETRAIT), 1)

    def test_sans_couverture_aux_deux_dates_aucun_retrait_n_est_affirme(self) -> None:
        """Le mode de defaillance redoute: le faux retrait.

        Une piece absente d'un passage ou personne n'est alle n'a pas ete
        retiree - elle n'a pas ete vue.
        """
        avant = _passage([_piece("ARR\x1f2025\x1fAnnexe 1")], [_rub("ARR")])
        apres = _passage([], [_rub("ARR", etat=RUBRIQUE_NON_EXPLOREE)])
        res = J.comparer(avant, apres)
        self.assertNotIn(J.RETRAIT, res["comptes"])
        self.assertEqual(res["constats"][0]["motif"], J.MOTIF_NON_PARCOURUE)

    def test_sans_cloture_aucun_retrait_n_est_affirme(self) -> None:
        """Une liste dont rien ne prouve qu'elle etait complete ne prouve aucune absence."""
        avant = _passage([_piece("ARR\x1f2025\x1fA")], [_rub("ARR", cloture=CLOTURE_AUCUNE)])
        apres = _passage([], [_rub("ARR", cloture=CLOTURE_AUCUNE)])
        res = J.comparer(avant, apres)
        self.assertEqual(res["constats"][0]["verdict"], J.INDETERMINE)
        self.assertEqual(res["constats"][0]["motif"], J.MOTIF_CLOTURE)

    def test_un_ajout_ne_demande_pas_que_l_ancien_passage_ait_ete_complet(self) -> None:
        """L'asymetrie est deliberee: on voit la piece, elle est la."""
        avant = _passage([], [_rub("ARR", cloture=CLOTURE_AUCUNE)])
        apres = _passage([_piece("ARR\x1f2025\x1fA")], [_rub("ARR", cloture=CLOTURE_AUCUNE)])
        res = J.comparer(avant, apres)
        self.assertEqual(res["comptes"].get(J.AJOUT), 1)

    def test_presente_aux_deux_dates_sans_empreinte_n_est_pas_inchange(self) -> None:
        """Aucun en-tete ne revele un changement de contenu chez l'editeur mesure.

        Confondre *presente* et *inchangee* ferait dire au journal qu'une piece
        n'a pas bouge alors qu'il ne l'a pas regardee.
        """
        avant = _passage([_piece("ARR\x1f2025\x1fA")], [_rub("ARR")])
        apres = _passage([_piece("ARR\x1f2025\x1fA")], [_rub("ARR")])
        res = J.comparer(avant, apres)
        self.assertEqual(res["constats"][0]["verdict"], J.PRESENCE_INCHANGEE)

    def test_deux_empreintes_differentes_font_une_modification(self) -> None:
        avant = _passage([_piece("ARR\x1f2025\x1fA", "aaa")], [_rub("ARR")])
        apres = _passage([_piece("ARR\x1f2025\x1fA", "bbb")], [_rub("ARR")])
        res = J.comparer(avant, apres)
        self.assertEqual(res["constats"][0]["verdict"], J.MODIFICATION)

    def test_une_collision_de_cle_suspend_le_verdict_sans_arreter_le_reste(self) -> None:
        """L'injectivite est reverifiee a chaque passage, pas supposee acquise.

        Elle a ete mesuree vraie le 2026-09-04 sur un index reel; rien
        n'empeche un syndic de creer demain deux pieces homonymes dans un meme
        groupe. La degradation doit rester locale.
        """
        avant = _passage(
            [_piece("ARR\x1f2025\x1fA"), _piece("ARR\x1f2025\x1fA"), _piece("ARR\x1f2025\x1fB")],
            [_rub("ARR")],
        )
        apres = _passage([_piece("ARR\x1f2025\x1fB")], [_rub("ARR")])
        res = J.comparer(avant, apres)
        verdicts = {c["emplacement"]: c["verdict"] for c in res["constats"]}
        self.assertEqual(verdicts["ARR\x1f2025\x1fA"], J.INDETERMINE)
        self.assertEqual(verdicts["ARR\x1f2025\x1fB"], J.PRESENCE_INCHANGEE)

    def test_le_retrait_arrive_en_tete_du_tri(self) -> None:
        constats = [
            {"verdict": J.AJOUT, "rubrique_code": "A", "groupe": "", "libelle": ""},
            {"verdict": J.RETRAIT, "rubrique_code": "B", "groupe": "", "libelle": ""},
            {"verdict": J.INCHANGE, "rubrique_code": "C", "groupe": "", "libelle": ""},
        ]
        self.assertEqual(J.trier(constats)[0]["verdict"], J.RETRAIT)

    def test_tout_motif_d_indetermination_porte_une_explication_lisible(self) -> None:
        for motif in (J.MOTIF_NON_PARCOURUE, J.MOTIF_CLOTURE, J.MOTIF_EMPLACEMENT,
                      J.MOTIF_COLLISION):
            self.assertGreater(len(J.explication(motif)), 40, motif)


class RenommageTests(unittest.TestCase):
    """La garde anti-renommage, ouverte par la mesure du nom serveur.

    Mesure du 2026-09-04 sur l'index reel: le nom servi par
    `content-disposition` est injectif sur la **totalite** de l'index - 115
    pieces, 115 noms, zero collision - et il distingue 40 pieces la ou le
    libelle n'en distingue que 8. Il s'obtient par une requete HEAD, sans corps.
    """

    def test_une_piece_renommee_n_est_pas_un_retrait(self) -> None:
        """C'etait la faiblesse nommee de la conception, et elle est levee.

        Sans cette garde, un renommage produisait un faux retrait ET un faux
        ajout. Le seul remede envisage jusque-la etait l'empreinte du contenu,
        donc un telechargement complet.
        """
        avant = _passage(
            [_piece("ARR2025Ancien nom", nom_serveur="fichier-42.pdf")],
            [_rub("ARR")],
        )
        apres = _passage(
            [_piece("ARR2025Nouveau nom", nom_serveur="fichier-42.pdf")],
            [_rub("ARR")],
        )
        res = J.comparer(avant, apres)
        verdicts = {c["verdict"] for c in res["constats"]}
        self.assertIn(J.DEPLACE, verdicts)
        self.assertNotIn(J.RETRAIT, verdicts)

    def test_une_piece_vraiment_partie_reste_un_retrait(self) -> None:
        """La garde ne doit pas avaler les vrais retraits."""
        avant = _passage(
            [_piece("ARR2025A", nom_serveur="fichier-42.pdf")], [_rub("ARR")]
        )
        apres = _passage([], [_rub("ARR")])
        res = J.comparer(avant, apres)
        self.assertEqual(res["constats"][0]["verdict"], J.RETRAIT)

    def test_sans_nom_serveur_la_garde_ne_change_rien(self) -> None:
        """Chez un editeur qui ne sert aucun nom, on retombe sur le cas nu.

        Degradation propre: le journal perd la distinction deplacement /
        retrait, il ne se met pas a inventer.
        """
        avant = _passage([_piece("ARR2025A")], [_rub("ARR")])
        apres = _passage([_piece("ARR2025B")], [_rub("ARR")])
        res = J.comparer(avant, apres)
        verdicts = {c["verdict"] for c in res["constats"]}
        self.assertIn(J.RETRAIT, verdicts)
        self.assertIn(J.AJOUT, verdicts)


class LisibiliteTests(unittest.TestCase):
    def test_une_cle_longue_ne_perd_rien_en_devenant_lisible(self) -> None:
        """Defaut trouve par les tests de l'etat de depenses.

        Une ligne de depenses porte cinq composantes, dont le montant en
        derniere position - et c'est le montant qui distingue deux lignes de
        meme date, meme nature et meme libelle. Une troncature a trois aurait
        affiche deux constats rigoureusement identiques pour deux lignes
        differentes.
        """
        from coproscope.modules._extranet_schema import composantes

        cle = "".join(["CHARGES", "12/03/2025", "Entretien", "Prestation", "240,00"])
        rubrique, groupe, libelle = composantes(cle)
        self.assertEqual(rubrique, "CHARGES")
        self.assertEqual(groupe, "12/03/2025")
        self.assertIn("240,00", libelle)


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_un_second_passage_n_efface_pas_le_premier(self) -> None:
        """Un journal dont le passage du 15 disparait le 22 n'est pas un journal."""
        X.enregistrer_index(self.instance, INDEX_ARRETES, "P1", debut="2026-03-12T09:00")
        X.enregistrer_index(self.instance, INDEX_ARRETES, "P2", debut="2026-06-04T09:00")
        self.assertEqual(len(S.lister_passages(self.instance)), 2)
        self.assertEqual(len(S.lire_passage(self.instance, "P1")["pieces"]), 4)

    def test_une_correction_humaine_survit_a_une_re_observation(self) -> None:
        X.enregistrer_index(self.instance, INDEX_ARRETES, "P1", debut="2026-03-12T09:00")
        S.ecrire_passage(
            self.instance,
            {"passage_id": "P1", "editeur": "coprodirecte", "espace": "", "debut": "2026-03-12T09:00",
             "fin": "", "profil": "coprodirecte", "doc_id": "", "origine": ORIGINE_CORRIGE},
            [{"passage_id": "P1", "rubrique_code": "ARR", "rubrique_libelle": "",
              "etat": "PARCOURUE", "cloture": CLOTURE_CONSTATEE, "nb_pieces": "0",
              "motif": "verifie a la main", "doc_id": "", "origine": ORIGINE_CORRIGE}],
            [],
        )
        X.enregistrer_index(
            self.instance, INDEX_ARRETES, "P1", debut="2026-03-12T09:00", remplacer=True
        )
        origines = {r["origine"] for r in S.lire_passage(self.instance, "P1")["rubriques"]}
        self.assertIn(ORIGINE_CORRIGE, origines)

    def test_un_passage_sans_couverture_est_refuse(self) -> None:
        with self.assertRaises(ValueError):
            S.ecrire_passage(self.instance, {"passage_id": "P9"}, [], [])

    def test_le_premier_passage_ne_produit_aucun_ajout(self) -> None:
        """Sans cela, l'ecran presenterait tout l'index comme des ajouts, jour un."""
        X.enregistrer_index(self.instance, INDEX_ARRETES, "P1", debut="2026-03-12T09:00")
        ecart = X.dernier_ecart(self.instance)
        self.assertTrue(ecart.get("reference_seule"))
        self.assertEqual(ecart["constats"], [])

    def test_une_instance_sans_passage_le_dit_au_lieu_d_afficher_du_vide(self) -> None:
        etat = X.etat(self.instance)
        self.assertTrue(etat["disponible"])
        self.assertEqual(etat["nb_passages"], 0)

    def test_un_profil_inconnu_est_refuse_avec_la_liste_des_profils_connus(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            X.enregistrer_index(self.instance, INDEX_ARRETES, "P1", profil="inexistant", debut="2026-03-12T09:00")
        self.assertIn("coprodirecte", str(ctx.exception))

    def test_reecrire_un_passage_par_megarde_est_refuse(self) -> None:
        """Un journal ne s'ecrase pas sans qu'on l'ait demande."""
        X.enregistrer_index(self.instance, INDEX_ARRETES, "P1", debut="2026-03-12T09:00")
        with self.assertRaises(ValueError) as ctx:
            X.enregistrer_index(self.instance, INDEX_ARRETES, "P1", debut="2026-03-12T09:00")
        self.assertIn("remplacer", str(ctx.exception))

    def test_une_reprise_qui_trouve_moins_ne_laisse_pas_de_pieces_fantomes(self) -> None:
        """Sinon les surnumeraires deviendraient de faux retraits au passage suivant.

        L'axe de remplacement de la couche partagee est le document; celui du
        journal est le passage. La clause est donc ecrite dans ce module, avec
        la meme protection des corrections humaines.
        """
        X.enregistrer_index(self.instance, INDEX_ARRETES, "P1", debut="2026-03-12T09:00")
        court = _page(_bloc("ARR", _groupe("Au 31/12/2025") + _ligne_piece("Annexe 1")))
        X.enregistrer_index(
            self.instance, court, "P1", debut="2026-03-12T09:00", remplacer=True
        )
        self.assertEqual(len(S.lire_passage(self.instance, "P1")["pieces"]), 1)

    def test_un_passage_sans_horodatage_est_refuse(self) -> None:
        """Defaut trouve par le test de bout en bout, garde comme regle.

        Sans horodatage, deux passages ne sont pas ordonnables: `les deux plus
        recents` n'a plus de sens et la comparaison peut partir a l'envers,
        rendant un retrait la ou il y a eu un ajout. Un journal n'est rien
        d'autre qu'un placement dans le temps.
        """
        with self.assertRaises(ValueError) as ctx:
            X.enregistrer_index(self.instance, INDEX_ARRETES, "P1")
        self.assertIn("debut", str(ctx.exception))

    def test_l_ordre_des_passages_suit_l_horodatage_et_non_l_identifiant(self) -> None:
        X.enregistrer_index(self.instance, INDEX_ARRETES, "ZZZ", debut="2026-01-01T08:00")
        X.enregistrer_index(self.instance, INDEX_ARRETES, "AAA", debut="2026-08-01T08:00")
        avant, apres = S.deux_derniers(self.instance)
        self.assertEqual((avant, apres), ("ZZZ", "AAA"))

    def test_le_parcours_complet_detecte_un_retrait_reel(self) -> None:
        """Le scenario du produit, de bout en bout, sur deux index synthetiques."""
        reduit = _page(
            _bloc("ARR", _groupe("Au 31/12/2025") + _ligne_piece("Annexe 1")
                  + _groupe("Au 31/12/2024") + _ligne_piece("Annexe 1")
                  + _ligne_piece("Annexe 2"))
        )
        X.enregistrer_index(self.instance, INDEX_ARRETES, "P1", debut="2026-03-12T09:00")
        X.enregistrer_index(self.instance, reduit, "P2", debut="2026-06-04T09:00")
        ecart = X.dernier_ecart(self.instance)
        retraits = [c for c in ecart["constats"] if c["verdict"] == J.RETRAIT]
        self.assertEqual(len(retraits), 1)
        self.assertEqual(retraits[0]["libelle"], "Annexe 2")
        self.assertEqual(retraits[0]["groupe"], "Au 31/12/2025")


class BlocIllisibleTests(unittest.TestCase):
    """Une rubrique vide et une rubrique illisible ne sont pas la meme chose.

    Defaut trouve le 2026-09-07. Un bloc present mais dont aucune ligne n'etait
    comprise ressortait `PARCOURUE` avec zero piece - donc un faux *rubrique
    vide*, indiscernable d'une rubrique reellement vide. Or une rubrique vide
    autorise a conclure a une absence: un simple changement de gabarit chez
    l'editeur aurait produit, **en silence**, le retrait de toutes les pieces
    de la rubrique.

    C'est exactement le constat le plus accusatoire que l'outil sache rendre,
    produit par une panne de lecture.
    """

    def _rubrique(self, html: str, code: str = "ARR") -> dict:
        lu = lire_index(html, PROFIL_COPRODIRECTE, "P1")
        return next(r for r in lu["rubriques"] if r["rubrique_code"] == code)

    def test_un_bloc_muet_est_un_echec_et_non_une_rubrique_vide(self) -> None:
        rubrique = self._rubrique(_page("<div class='ARR mt3'></div>"))
        self.assertEqual(rubrique["etat"], S_RUBRIQUE_ECHEC)
        self.assertEqual(rubrique["nb_pieces"], "0")
        self.assertIn("aucune absence", rubrique["motif"])

    def test_une_rubrique_qui_dit_qu_elle_est_vide_reste_parcourue(self) -> None:
        """L'invariant: une rubrique servie affiche toujours quelque chose."""
        rubrique = self._rubrique(
            _page("<div class='ARR mt3'><p>Aucun document disponible</p></div>")
        )
        self.assertEqual(rubrique["etat"], S_RUBRIQUE_PARCOURUE)
        self.assertIn("texte present", rubrique["motif"])

    def test_un_tableau_aux_en_tetes_seuls_reste_parcouru(self) -> None:
        rubrique = self._rubrique(
            _page(
                "<div class='ARR mt3'><table class='tableDoc'><tbody>"
                "<tr><th>Document</th><th>Date</th></tr>"
                "</tbody></table></div>"
            )
        )
        self.assertEqual(rubrique["etat"], S_RUBRIQUE_PARCOURUE)
        self.assertIn("aucune piece reconnue", rubrique["motif"])

    def test_des_liens_sans_ligne_lue_sont_un_echec_et_non_une_rubrique_vide(self) -> None:
        """Trouve par l'epreuve sur un second corpus, le 2026-09-07.

        Un editeur qui sert ses listes en `ul` au lieu de `table` produisait
        `PARCOURUE`, zero piece, **et la cloture CONSTATEE** - donc une absence
        AFFIRMABLE. Un changement de gabarit entre deux passages aurait suffi a
        retirer, en silence, toutes les pieces de la rubrique.

        Des liens de document presents et aucune ligne lue: c'est une panne de
        lecture, pas une rubrique vide.
        """
        liste = _page(
            "<div class='ARR mt3'><ul>"
            + "".join(f"<li><a href='documents/{i}'>PV {i}</a></li>" for i in range(5))
            + "</ul></div>"
        )
        rubrique = self._rubrique(liste)
        self.assertEqual(rubrique["etat"], S_RUBRIQUE_ECHEC)
        self.assertEqual(rubrique["cloture"], CLOTURE_AUCUNE)
        self.assertIn("forme inconnue", rubrique["motif"])

    def test_un_libelle_de_piece_ne_vaut_pas_total_annonce(self) -> None:
        """Un seul titre contenant *12 pieces jointes* faisait basculer TOUTES
        les rubriques en `ATTESTEE` - la cloture la plus forte, celle qui
        autorise a conclure a une absence.

        Une phrase ecrite par le syndic dans le titre d'un document devenait
        ainsi une garantie d'exhaustivite donnee par l'outil.
        """
        piege = _page(_bloc("ARR", _ligne_piece("Bordereau 12 pieces jointes")))
        self.assertEqual(self._rubrique(piege)["cloture"], CLOTURE_CONSTATEE)

        vrai = _page(
            "<p>43 documents</p>" + _bloc("ARR", _ligne_piece("Annexe 1"))
        )
        self.assertEqual(self._rubrique(vrai)["cloture"], "ATTESTEE")

    def test_un_bloc_illisible_rend_toute_absence_indeterminee(self) -> None:
        """Le bout de la chaine, et la raison d'etre de la correction.

        Sans elle, ce scenario aurait rendu un RETRAIT: la rubrique aurait ete
        lue `PARCOURUE` avec zero piece aux deux dates, et le journal aurait
        conclu que la piece avait disparu.
        """
        avec = _page(_bloc("ARR", _groupe("Au 31/12/2025") + _ligne_piece("Annexe 1")))
        muet = _page("<div class='ARR mt3'></div>")

        a = lire_index(avec, PROFIL_COPRODIRECTE, "P1")
        b = lire_index(muet, PROFIL_COPRODIRECTE, "P2")
        ecart = J.comparer(
            {"passage": {"passage_id": "P1", "debut": "2026-09-01T09:00:00Z"},
             "rubriques": a["rubriques"], "pieces": a["pieces"]},
            {"passage": {"passage_id": "P2", "debut": "2026-09-07T09:00:00Z"},
             "rubriques": b["rubriques"], "pieces": b["pieces"]},
        )
        verdicts = {c["verdict"] for c in ecart["constats"]}
        self.assertNotIn(J.RETRAIT, verdicts)
        self.assertIn(J.INDETERMINE, verdicts)


class GardesDeValeurTests(unittest.TestCase):
    """Une enumeration declaree et non gardee ne protege de rien.

    Le magasin refusait deja une COLONNE non declaree, parce qu'elle serait
    ecrite nulle part et que la perte ne se verrait qu'a l'ecran, plus tard,
    sur un champ vide inexplicable. Le meme raisonnement vaut pour les
    VALEURS: un etat hors enumeration ne serait refuse par personne en aval.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _passage(self, etat: str = "PARCOURUE", cloture: str = CLOTURE_CONSTATEE) -> dict:
        return {
            "passage": {"passage_id": "P1", "editeur": "e", "espace": "/x",
                        "debut": "2026-09-07T09:00:00Z", "fin": "2026-09-07T09:01:00Z",
                        "profil": "coprodirecte", "doc_id": "", "origine": "EXTRAIT"},
            "rubriques": [{"passage_id": "P1", "rubrique_code": "ARR",
                           "rubrique_libelle": "Arrete", "etat": etat,
                           "cloture": cloture, "nb_pieces": "0", "motif": "",
                           "doc_id": "", "origine": "EXTRAIT"}],
            "pieces": [],
        }

    def test_un_etat_de_rubrique_inconnu_est_refuse(self) -> None:
        with self.assertRaises(ValueError) as e:
            S.ecrire_passage(self.instance, **self._passage(etat="A_MOITIE_LU"))
        self.assertIn("A_MOITIE_LU", str(e.exception))

    def test_une_cloture_inconnue_est_refusee(self) -> None:
        with self.assertRaises(ValueError):
            S.ecrire_passage(self.instance, **self._passage(cloture="PEUT_ETRE"))

    def test_les_valeurs_declarees_passent(self) -> None:
        S.ecrire_passage(self.instance, **self._passage())
        self.assertEqual(len(S.lire_passage(self.instance, "P1")["rubriques"]), 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
