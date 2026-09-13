# -*- coding: utf-8 -*-
"""Aucune reference du gouvernail publie n'est rendue comme un lien sans preuve.

`RM-2026-0128`. L'artefact du gouvernail s'execute dans un bac a sable
navigateur. Brice, le 2026-09-08: *« depuis l'artefact du gouvernail, il y a les
liens des notes MD, mais je ne peux pas les ouvrir »*.

**L'axe garde ici.** Une reference n'est ouvrable que si la page peut elle-meme
produire ce qu'elle promet: une adresse que le navigateur atteint, ou un texte
qu'elle a embarque. Ce qui varie est la FORME de la reference - adresse web,
chemin de depot, chemin Windows, chemin reseau, hote local, schema inconnu,
prose a barre oblique. Ce qui reste invariant: **tout ce qui n'est ni atteignable
ni embarque est cite en clair avec son motif**.

**Ce que le test refuse explicitement de faire.** Il ne verifie pas une liste de
schemas connus. Il verifie la DEGRADATION: on lui donne des formes que le code
n'a jamais vues - `ipfs://`, un chemin UNC, un jeton nu - et il exige qu'elles
tombent du cote sur. Une valeur inconnue qui deviendrait un lien serait une
reponse fausse en silence, exactement le defaut d'origine.

**Non-vacuite.** Un garde qui classe zero reference rendrait `OK` et ne
garderait rien. Chaque test compte ce qu'il a mesure et echoue si le compte est
nul; le test sur le gouvernail reel exige plus de cent references classees.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
OUTIL = DEPOT / "tools" / "gouvernail_depot.py"


def _charger():
    spec = importlib.util.spec_from_file_location("gouvernail_depot", OUTIL)
    if spec is None or spec.loader is None:
        raise RuntimeError("outil introuvable: %s" % OUTIL)
    module = importlib.util.module_from_spec(spec)
    # Sans cet enregistrement, `dataclasses` ne retrouve pas le module de la
    # classe et leve un AttributeError opaque a l'import.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


G = _charger()


class LaLectureDuRegistreEstReelle(unittest.TestCase):
    """Un parseur qui rend zero ligne rendrait tout le reste vert pour rien."""

    def test_le_registre_est_trouve_et_peuple(self) -> None:
        lignes = G.lire_registre((DEPOT / "docs" / "roadmap_backlog_central.md")
                                 .read_text(encoding="utf-8"))
        self.assertGreater(len(lignes), 100, "registre suspect: %d lignes" % len(lignes))

    def test_chaque_ligne_porte_les_onze_sens_dont_la_preuve(self) -> None:
        """La colonne `Preuve/livrable` porte le mandat, et elle etait absente du depot.

        Quatre verdicts de fermeture sont tombes le 2026-09-09 parce que leur
        lecteur avait lu le titre et pas le mandat. Un depot qui laisse tomber
        cette colonne reproduit la cause a l'ecran.
        """
        lignes = G.lire_registre((DEPOT / "docs" / "roadmap_backlog_central.md")
                                 .read_text(encoding="utf-8"))
        for item in lignes[:40]:
            for champ in G.CHAMPS:
                self.assertIn(champ, item, "champ %s absent de %s" % (champ, item.get("id")))
        avec_preuve = [o for o in lignes if o["preuve"].strip()]
        self.assertGreater(len(avec_preuve), 50,
                           "seulement %d lignes portent une preuve" % len(avec_preuve))

    def test_les_accents_graves_ne_sont_pas_du_contenu(self) -> None:
        lignes = G.lire_registre((DEPOT / "docs" / "roadmap_backlog_central.md")
                                 .read_text(encoding="utf-8"))
        statuts = {o["st"] for o in lignes}
        self.assertIn("ACTIF", statuts, "statuts lus: %s" % sorted(statuts))
        self.assertFalse([s for s in statuts if "`" in s], "statuts encore entoures: %s" % statuts)


class UneFormeInconnueNeDevientJamaisUnLien(unittest.TestCase):
    """Le coeur de l'axe: la degradation, mesuree sur des formes non prevues."""

    FORMES_QUI_DOIVENT_SE_DEGRADER = (
        "ipfs://QmXyz/note.md",
        "ftp://ailleurs.example/note.md",
        "mailto:quelquun@example.org",
        "file:///C:/Users/x/note.md",
        "\\\\serveur\\partage\\note.md",
        "C:\\Users\\x\\note.md",
        "/mnt/ailleurs/note.md",
        "docs/ce_fichier_nexiste_pas_2026.md",
        "jeton-sans-forme.md",
    )

    def test_chaque_forme_inconnue_est_citee_avec_un_motif(self) -> None:
        mesurees = 0
        for brut in self.FORMES_QUI_DOIVENT_SE_DEGRADER:
            ref = G.classer_reference(brut, set())
            mesurees += 1
            self.assertEqual(ref.classe, "citee",
                             "%r est devenu %s au lieu d'etre cite" % (brut, ref.classe))
            self.assertTrue(ref.motif.strip(),
                            "%r est cite sans motif: la page dirait seulement non" % brut)
        self.assertEqual(mesurees, len(self.FORMES_QUI_DOIVENT_SE_DEGRADER))

    def test_un_hote_local_n_est_jamais_une_adresse_atteignable(self) -> None:
        for brut in ("http://localhost:8780/documents",
                     "http://127.0.0.1:8786/",
                     "https://192.168.1.20/rapport.html",
                     "http://poste.localhost/x"):
            ref = G.classer_reference(brut, set())
            self.assertEqual(ref.classe, "citee", "%r rendu comme lien" % brut)
            self.assertIn("poste", ref.motif, "motif muet sur le poste: %r" % ref.motif)

    def test_une_adresse_vers_cette_page_meme_n_apporte_aucune_piece(self) -> None:
        brut = "https://claude.ai/code/artifact/" + G.PAGE_GOUVERNAIL
        ref = G.classer_reference(brut, set())
        self.assertEqual(ref.classe, "citee")
        self.assertIn("lecture", ref.motif)

    def test_une_adresse_web_ordinaire_reste_ouvrable(self) -> None:
        ref = G.classer_reference("https://www.legifrance.gouv.fr/x", set())
        self.assertEqual(ref.classe, "distante")

    def test_un_chemin_depose_devient_ouvrable_sur_place(self) -> None:
        ref = G.classer_reference("docs/roadmap_backlog_central.md",
                                  {"docs/roadmap_backlog_central.md"})
        self.assertEqual(ref.classe, "embarquee")
        self.assertEqual(ref.chemin, "docs/roadmap_backlog_central.md")


class LaProseABarreObliqueN_estPasUneReference(unittest.TestCase):
    """51 fausses references sur 274 avant correction, toutes affirmant un chemin."""

    PROSE = ("UX/UI", "go/no-go", "piece/preuve", "mail/email/e-mail/courriel",
             "decisions/incidents", "smoke/security")
    VRAIS = ("docs/roadmap_backlog_central.md", "server/tests/test_gouvernail_depot.py",
             "tools/gouvernail_depot.py")

    def test_la_prose_n_est_pas_extraite(self) -> None:
        for mot in self.PROSE:
            self.assertEqual(G.references_de("suite %s ensuite" % mot), [],
                             "%r pris pour une reference" % mot)

    def test_un_chemin_de_fichier_est_extrait(self) -> None:
        for chemin in self.VRAIS:
            self.assertIn(chemin, G.references_de("voir %s pour la suite" % chemin))

    def test_un_dossier_existant_est_extrait_meme_sans_suffixe(self) -> None:
        self.assertIn("server/tests", G.references_de("les tests vivent dans server/tests"))

    def test_une_date_n_est_pas_un_chemin(self) -> None:
        self.assertEqual(G.references_de("mesure du 08/09/2026"), [])


class UnEcarteDitPourquoiEtUneSeuleFoisLeMeme(unittest.TestCase):
    """Deux mesureurs pour un meme chemin se contredisent; il n'y en a qu'un."""

    def test_un_dossier_est_ecarte_comme_dossier_et_pas_comme_introuvable(self) -> None:
        pieces, ecartes = G.embarquer(["server/tests"])
        self.assertEqual(pieces, [])
        self.assertEqual(len(ecartes), 1)
        self.assertIn("dossier", ecartes[0].motif)
        motifs = {e.chemin: e.motif for e in ecartes}
        ref = G.classer_reference("server/tests", set(), motifs)
        self.assertEqual(ref.motif, ecartes[0].motif,
                         "deux motifs pour le meme chemin: la page en afficherait un faux")

    def test_un_format_non_affichable_le_dit(self) -> None:
        _, ecartes = G.embarquer(["tools/gouvernail_depot.py"])
        self.assertEqual(len(ecartes), 1)
        self.assertIn(".py", ecartes[0].motif)

    def test_un_texte_du_depot_est_reellement_embarque(self) -> None:
        pieces, ecartes = G.embarquer(["docs/roadmap_backlog_central.md"])
        self.assertEqual(ecartes, [])
        self.assertEqual(len(pieces), 1)
        self.assertTrue(pieces[0].texte, "piece embarquee vide")
        self.assertTrue(pieces[0].tronque, "ce fichier depasse le budget: la troncature doit se dire")
        self.assertGreater(pieces[0].car_total, len(pieces[0].texte))


class UneCoupureSeDeclare(unittest.TestCase):
    """Le depot precedent coupait la colonne `Prochaine action` en silence.

    Une cellule coupee sans le dire fait lire un mandat tronque comme un mandat
    entier - la meme faute, dans le depot, que celle que le lot corrige a
    l'ecran.
    """

    @staticmethod
    def _registre(n: int, longueur: int) -> dict:
        return {
            "n": n,
            "lignes": [
                {"id": "RM-2026-%04d" % i, "t": "titre", "ty": "t", "st": "ACTIF",
                 "p": "P0", "o": "o", "src": "s", "a": "x" * longueur, "ch": "c",
                 "preuve": "y" * longueur, "maj": "2026-09-09", "refs": []}
                for i in range(n)
            ],
        }

    def test_ce_qui_tient_n_est_pas_coupe(self) -> None:
        ajuste = G.ajuster_au_magasin(self._registre(3, 50))
        self.assertEqual(ajuste["cap_cellule"], G.PALIERS_CELLULE[0])
        self.assertFalse([o for o in ajuste["lignes"] if o.get("coupe")])

    def test_ce_qui_deborde_est_coupe_et_dit_sa_longueur_reelle(self) -> None:
        ajuste = G.ajuster_au_magasin(self._registre(200, 4000))
        self.assertLessEqual(G.octets(ajuste), G.OCTETS_MAX_DOCUMENT)
        coupees = [o for o in ajuste["lignes"] if o.get("coupe")]
        self.assertEqual(len(coupees), 200, "aucune ligne coupee: la mesure n'a rien fait")
        for item in coupees:
            self.assertEqual(item["coupe"]["a"], 4000,
                             "la longueur reelle n'est pas declaree")
            self.assertEqual(len(item["a"]), ajuste["cap_cellule"])

    def test_un_budget_intenable_leve_au_lieu_de_deborder(self) -> None:
        with self.assertRaises(ValueError):
            G.ajuster_au_magasin(self._registre(500, 5000), budget=1000)

    def test_une_ligne_rendue_en_detail_n_est_jamais_coupee(self) -> None:
        """Sinon la page afficherait un mandat tronque comme un mandat entier."""
        brut = self._registre(200, 4000)
        brut["lignes"][0]["detail"] = True
        ajuste = G.ajuster_au_magasin(brut)
        self.assertEqual(len(ajuste["lignes"][0]["a"]), 4000)
        self.assertNotIn("coupe", ajuste["lignes"][0])
        self.assertIn("coupe", ajuste["lignes"][1], "les lignes de comptage doivent, elles, etre coupees")


class LeDepotConstruitNePrometRien_QuIlNeTientPas(unittest.TestCase):
    """Le controle final, sur le gouvernail reel."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.registre, cls.pieces, cls.rapport = G.construire()

    def test_la_mesure_a_bien_eu_lieu(self) -> None:
        classees = (len(self.rapport.non_embarques) + len(self.rapport.distantes)
                    + len(self.rapport.pieces))
        self.assertGreater(classees, 100,
                           "seulement %d references classees: le garde ne mesure rien" % classees)

    def test_aucun_lien_mort(self) -> None:
        mortes = self.rapport.mortes()
        self.assertEqual(mortes, [], "references promises ouvrables sans piece: %s"
                         % [r.brut for r in mortes])

    def test_toute_piece_promise_ouvrable_a_son_texte_dans_le_depot(self) -> None:
        deposes = {p["chemin"]: p for p in self.pieces["lignes"]}
        promises = [r for r in self.rapport.affichees if r.classe == "embarquee"]
        self.assertGreater(len(promises), 0,
                           "aucune piece promise: le controle ne mesurerait rien")
        for ref in promises:
            piece = deposes.get(ref.chemin)
            self.assertIsNotNone(piece, "%s promis ouvrable, absent du depot" % ref.chemin)
            self.assertTrue(piece["texte"], "%s depose vide" % ref.chemin)

    def test_toute_reference_citee_porte_son_motif(self) -> None:
        citees = [r for r in self.rapport.affichees if r.classe == "citee"]
        self.assertGreater(len(citees), 0, "aucune reference citee: residu non mesure")
        for ref in citees:
            self.assertTrue(ref.motif.strip(), "%s cite sans motif" % ref.brut)

    def test_le_depot_declare_lui_meme_ce_qu_il_n_embarque_pas(self) -> None:
        """Le residu voyage AVEC le depot: la page peut le dire sans le deviner."""
        declares = self.pieces.get("non_embarques", [])
        self.assertGreater(len(declares), 0, "residu non declare dans le depot")
        for entree in declares:
            self.assertTrue(entree.get("chemin"))
            self.assertTrue(entree.get("motif"))

    def test_les_references_survivent_a_la_coupure(self) -> None:
        """Mesure: relire les cellules RECUES faisait tomber 11 pieces a 8, en silence.

        Les references sont relevees sur le texte entier, avant coupure, et
        voyagent avec la ligne. Une piece citee au-dela du palier reste donc
        atteignable.

        **UN SEUIL A ETE RETIRE ICI LE 2026-09-10, et il exigeait que le
        backlog reste plein.** Le temoin de sante s'ecrivait
        `assertGreater(len(mesurees), 10)`. Or les lignes rendues en detail sont
        exactement les **P0 encore `ACTIF`**: le nombre de references mesurees
        decroit donc a mesure que les P0 se ferment. Le jour ou un P0 est passe
        de `ACTIF` a `A_ARBITRER`, le compte est tombe de 11 a 10 et ce test a
        echoue - **non pas parce qu'une reference avait ete perdue, mais parce
        qu'un chantier avait abouti**.

        C'est le meme defaut que ce depot poursuit ailleurs: un seuil cale sur
        une valeur observee au lieu de la propriete gardee. La propriete est
        *aucune reference mesuree ne manque aux lignes deposees*; le temoin de
        sante doit seulement empecher que l'egalite soit vide de sens. Il porte
        donc desormais sur la PRESENCE de references, pas sur leur nombre, et il
        reste vrai quel que soit l'etat du backlog.
        """
        detail = [o for o in self.registre["lignes"] if o.get("detail")]
        self.assertGreater(len(detail), 0, "aucune ligne rendue en detail: rien de mesure")
        portees = {r["brut"] for o in detail for r in o.get("refs_pieces", [])}
        mesurees = {r.brut for r in self.rapport.affichees}
        self.assertGreater(
            len(mesurees), 0,
            "aucune reference mesuree: l'egalite qui suit ne garderait rien")
        self.assertEqual(mesurees - portees, set(),
                         "references mesurees mais absentes des lignes deposees")

    def test_une_ligne_de_comptage_ne_porte_pas_de_pieces_et_l_annonce(self) -> None:
        """L'autre moitie du contrat: la page lit `detail` et refuse de deviner.

        Une ligne de comptage a des cellules coupees; y relire des references
        rendrait une liste incomplete sans le dire. Elle n'en porte donc aucune,
        et son drapeau permet a la page de l'annoncer au lieu de l'ignorer.
        """
        comptage = [o for o in self.registre["lignes"] if not o.get("detail")]
        self.assertGreater(len(comptage), 50, "population de comptage suspecte")
        self.assertFalse([o for o in comptage if o.get("refs_pieces")])
        self.assertTrue([o for o in comptage if o.get("coupe")],
                        "aucune ligne de comptage coupee: le drapeau ne sert a rien")

    def test_le_document_tient_dans_le_magasin(self) -> None:
        taille = G.octets(self.registre)
        self.assertLessEqual(taille, G.OCTETS_MAX_DOCUMENT,
                             "document de %d octets: le magasin le refusera" % taille)
        self.assertIn("cap_cellule", self.registre)

    def test_une_piece_tronquee_le_dit(self) -> None:
        for piece in self.pieces["lignes"]:
            if piece["tronque"]:
                self.assertIn("tronque", piece["sous_titre"])
                self.assertGreater(piece["car_total"], len(piece["texte"]))

    def test_LE_DOCUMENT_DES_PIECES_AUSSI_tient_dans_le_magasin(self) -> None:
        """Le test voisin ne regardait que le registre, et c'etait le defaut.

        **Mesure du 2026-09-09.** Le registre etait borne; le document des
        pieces ne l'etait par rien - et c'est LUI qui porte les notes, donc
        l'objet du mandat. Son seul garde-fou etait un budget en CARACTERES
        (600 000) face a une limite de magasin en OCTETS (262 144), six lignes
        plus haut. Un document de 597 592 octets - 2,28 fois la limite - a ete
        construit, et les 28 tests passaient: celui-ci chargeait `self.pieces`
        et ne le regardait jamais.
        """
        taille = G.octets(self.pieces)
        self.assertLessEqual(
            taille, G.OCTETS_MAX_DOCUMENT,
            "document des pieces de %d octets: le magasin le refusera, et la page "
            "perdra ses boutons `Lire ici` en affichant un motif faux" % taille,
        )
        self.assertEqual(G.OCTETS_MAX_DOCUMENT, self.pieces["budget_octets"])

    def test_une_piece_ecartee_par_le_budget_le_DIT(self) -> None:
        """Une piece qui disparait en silence est le defaut que ce depot corrige."""
        minuscule = G.borner_les_pieces(self.pieces, budget=4_000)
        self.assertLessEqual(G.octets(minuscule), 4_000)
        self.assertLess(len(minuscule["lignes"]), len(self.pieces["lignes"]))
        motifs = [e["motif"] for e in minuscule["non_embarques"]]
        budgetes = [m for m in motifs if "budget du magasin" in m]
        self.assertEqual(
            len(self.pieces["lignes"]) - len(minuscule["lignes"]), len(budgetes),
            "des pieces ont disparu sans que le document dise pourquoi",
        )

    def test_un_budget_impossible_leve_au_lieu_de_rendre_un_document_vide(self) -> None:
        with self.assertRaises(ValueError):
            G.borner_les_pieces(self.pieces, budget=10)


class UnPrefixeN_estPasUnJeuDeCaracteres(unittest.TestCase):
    """`lstrip("./")` retire TOUS les points et barres de tete, pas le prefixe.

    Defaut mesure le 2026-09-09: `./.gitignore` devenait `gitignore`, donc une
    reference vers un fichier cache ne retrouvait jamais sa piece. C'est la
    faute des modalites appliquee a une chaine: on visait un prefixe, on a
    ecrit un jeu de caracteres.
    """

    def test_un_fichier_cache_garde_son_point(self) -> None:
        ref = G.classer_reference("./.gitignore", set(), {})
        self.assertEqual(".gitignore", ref.chemin or ref.brut.removeprefix("./"))

    def test_le_prefixe_courant_est_bien_retire(self) -> None:
        ref = G.classer_reference("./docs/roadmap_backlog_central.md", set(), {})
        self.assertEqual("docs/roadmap_backlog_central.md", ref.chemin)


if __name__ == "__main__":
    unittest.main()
