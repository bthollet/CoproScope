"""Ce qui distingue - ou ne distingue pas - deux pieces d'assemblee.

Deux sujets, une seule question de fond: quand le produit ne sait pas, il doit
le dire au lieu de trancher en silence.

1. **Le titre du proces-verbal** (regression bloquante du 2026-09-05). Une
   forme de titre non reconnue faisait disparaitre un proces-verbal entier du
   registre, journalise au niveau `OK`.
2. **Les copies concurrentes d'une meme assemblee** (C054). Le meme rang de
   resolution occupe par plusieurs assemblees dont l'une n'a pas de date lue:
   l'ecran l'affichait trois fois sans jamais dire que rien ne les distingue.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coproscope.modules import resolutions as R
from coproscope.modules import _resolutions_assemblees as AS
from coproscope.modules import _resolutions_registre as RG

CLOTURE_OK = "En vertu de quoi cette resolution est adoptee."
CLOTURE_KO = "En vertu de quoi cette resolution est rejetee."

#: La tete d'un proces-verbal qui MET AUX VOIX une demande d'inscription. C'est
#: le cas reel: la meme tete porte le titre de la piece et la mention de la
#: demande, si bien que la lecture du titre decide seule du sort du document.
CORPS_PV = (
    "L'assemblee a examine la demande d'inscription de questions a l'ordre "
    "du jour notifiee par un coproprietaire, et les a mises aux voix.\n"
    f"1 - Constitution du bureau. (Article 24) {CLOTURE_OK}\n"
    f"2 - Election du secretaire. (Article 24) {CLOTURE_OK}\n"
    f"3 - Approbation des comptes. (Article 24) {CLOTURE_KO}\n"
)

DEMANDE_INSCRIPTION = "\n".join((
    "DEMANDE D'INSCRIPTION DE QUESTIONS A L'ORDRE DU JOUR de la prochaine",
    "assemblee generale, en application de l'article 10 du decret 67-223.",
    "Le coproprietaire soussigne demande l'inscription des projets suivants.",
    "",
    f"1° - Projet : mise en concurrence des contrats. (Article 24) {CLOTURE_OK}",
    f"2° - Projet : communication des pieces. (Article 24) {CLOTURE_OK}",
    f"3° - Projet : audit des comptes. (Article 24) {CLOTURE_OK}",
    f"4° - Projet : reprise des parties communes. (Article 25) {CLOTURE_OK}",
    f"5° - Projet : changement de prestataire. (Article 24) {CLOTURE_OK}",
))


class TitreProcesVerbalTests(unittest.TestCase):
    """La regression que ces tests ferment: un proces-verbal entier ecarte.

    `TITRE_PV_RE` n'admettait qu'UN seul caractere entre `proces` et `verbal`.
    Un titre aere - « PROCES - VERBAL DE L'ASSEMBLEE GENERALE », forme courante
    des que l'OCR espace un titre en capitales - n'etait donc plus lu comme un
    titre de proces-verbal. Le document retombait sur la declaration de demande
    d'inscription presente dans la MEME tete, `build_register` faisait
    `continue`, et toutes ses resolutions disparaissaient du coffre.

    Mesure du 2026-09-05 sur six formes de titre relevees: quatre echouaient.

    **L'axe** est la maniere dont le titre separe ses deux mots; ce qui reste
    invariant le long de l'axe, c'est que les deux mots restent contigus.
    """

    def test_le_titre_prime_quel_que_soit_son_separateur(self) -> None:
        titres = (
            "PROCES-VERBAL DE L'ASSEMBLEE GENERALE",
            "PROCES - VERBAL DE L'ASSEMBLEE GENERALE",
            "PROCES  VERBAL DE L'ASSEMBLEE GENERALE",
            "PROCES VERBAL DE L'ASSEMBLEE GENERALE",
            "PROCES-  VERBAL DE L'ASSEMBLEE GENERALE",
            "PROCES\nVERBAL DE L'ASSEMBLEE GENERALE",
        )
        for titre in titres:
            with self.subTest(titre=titre.replace("\n", "\\n")):
                self.assertEqual(R.nature_assemblee(f"{titre}\n{CORPS_PV}"), "PV_AG")

    def test_deux_mots_separes_par_une_phrase_ne_font_pas_un_titre(self) -> None:
        """Garde anti-sur-correction: elargir le separateur ne revient pas a
        chercher les deux mots n'importe ou dans la tete."""
        self.assertIsNone(
            RG.TITRE_PV_RE.search("proces de la copropriete et rapport verbal")
        )

    def test_une_demande_d_inscription_reste_ecartee(self) -> None:
        """Garde anti-sur-correction: la correction du titre ne rouvre pas la
        porte aux votes fabriques a partir d'une lettre."""
        self.assertEqual(R.nature_assemblee(DEMANDE_INSCRIPTION), "DEMANDE_INSCRIPTION")


class _RunEnregistre:
    """Un `run` qui retient les niveaux journalises, sans rien ecrire."""

    def __init__(self) -> None:
        self.lignes: list[tuple[str, str]] = []

    def log_run(self, niveau: str, message: str) -> None:
        self.lignes.append((niveau, message))


class _InstanceAvecCoffre:
    """Une instance minimale: un registre documentaire et un coffre local."""

    def __init__(self, racine: Path) -> None:
        self._racine = racine

    def register(self, name: str) -> Path:
        if name == "documents":
            return self._racine / "registre_documents.csv"
        raise KeyError(name)

    def root(self, name: str) -> Path:
        return self._racine / name

    def settings(self) -> dict:
        return {"vault": {"local_root": "vault_local"}}

    def resolve_path(self, chemin: str) -> Path:
        return self._racine / chemin


def _run_sur_un_document(texte: str) -> tuple[list[tuple[str, str]], dict]:
    """Passe un document unique dans `build_register`, rend le journal et le
    resume. Instance jetable, creee pour l'appel."""
    racine = Path(tempfile.mkdtemp())
    (racine / "workspace" / "text").mkdir(parents=True)
    (racine / "workspace" / "text" / "doc.txt").write_text(texte, encoding="utf-8")
    (racine / "registre_documents.csv").write_text(
        "doc_id,document_type,text_path,suspected_date\n"
        "DOC-TEST-0001,PV_AG,text/doc.txt,2024-07-03\n",
        encoding="utf-8",
    )
    run = _RunEnregistre()
    resume = R.build_register(_InstanceAvecCoffre(racine), run)
    return run.lignes, resume


class NiveauDeJournalTests(unittest.TestCase):
    """Ecarter une piece est une perte: elle ne se journalise pas au niveau OK.

    Le niveau ne passait en `WARN` que sur une collision de cle. Un document
    ecarte comme demande d'inscription - donc, quand la lecture du titre se
    trompe, un proces-verbal entier perdu - etait annonce au meme niveau qu'un
    run sans incident. Le resume nommait bien la piece; le niveau disait que
    tout allait bien, et c'est le niveau qui remonte.
    """

    def test_une_demande_ecartee_passe_le_run_en_WARN(self) -> None:
        lignes, resume = _run_sur_un_document(DEMANDE_INSCRIPTION)
        self.assertEqual(resume["demandes_inscription_ecartees"], ["DOC-TEST-0001"])
        self.assertEqual([niveau for niveau, _ in lignes], ["WARN"])

    def test_le_WARN_nomme_sa_cause_au_lieu_de_la_laisser_chercher(self) -> None:
        lignes, resume = _run_sur_un_document(DEMANDE_INSCRIPTION)
        self.assertEqual(resume["motifs_alerte"], ["1 demandes d'inscription ecartees"])
        self.assertIn("demandes d'inscription ecartees", lignes[0][1])

    def test_un_run_sans_piece_ecartee_reste_au_niveau_OK(self) -> None:
        """Garde anti-sur-correction: si tout passe en WARN, le WARN ne veut
        plus rien dire."""
        texte = (
            "PROCES-VERBAL DE L'ASSEMBLEE GENERALE DU 3 JUILLET 2024\n"
            f"1° - Constitution du bureau. (Article 24) {CLOTURE_OK}\n"
            f"2° - Election du secretaire. (Article 24) {CLOTURE_OK}\n"
            f"3° - Approbation des comptes. (Article 24) {CLOTURE_KO}\n"
        )
        lignes, resume = _run_sur_un_document(texte)
        self.assertEqual(resume["resolutions"], 3)
        self.assertEqual(resume["motifs_alerte"], [])
        self.assertEqual([niveau for niveau, _ in lignes], ["OK"])

    def test_un_pv_au_titre_aere_n_est_plus_perdu_de_bout_en_bout(self) -> None:
        """Le parcours complet de la regression, du registre au coffre."""
        _, resume = _run_sur_un_document(
            f"PROCES - VERBAL DE L'ASSEMBLEE GENERALE DU 3 JUILLET 2024\n{CORPS_PV}"
        )
        self.assertEqual(resume["demandes_inscription_ecartees"], [])
        self.assertEqual(resume["pv_lus"], 1)
        self.assertEqual(resume["resolutions"], 3)


class ComptageStockeTests(unittest.TestCase):
    """Le nombre annonce est celui qui a survecu, pas celui qui a ete soumis.

    Mesure du 2026-09-04: sur l'assemblee de fevrier 2026, un document produit
    neuf resolutions dont deux portent le numero 3. Les deux fabriquent la meme
    cle, `INSERT OR REPLACE` en jette une sans rien lever, le journal ecrivait
    « resolutions: 9 » et le coffre en contenait huit.

    Le calcul vit dans ce module et non dans la couche de stockage - qui
    appartient a une autre zone - parce qu'il ne demande rien de plus a la
    base: le nombre d'ecrasements se deduit des lignes construites.
    """

    def test_deux_lignes_de_meme_cle_ne_comptent_que_pour_une(self) -> None:
        lignes = [
            {"resolution_id": "R003", "etat": "CONSTATEE", "origine": "EXTRAIT"},
            {"resolution_id": "R003", "etat": "CONSTATEE", "origine": "EXTRAIT"},
            {"resolution_id": "R004", "etat": "CONSTATEE", "origine": "EXTRAIT"},
        ]
        ecrasees = RG.collisions_de_cle(lignes)
        self.assertEqual(
            len(lignes) - sum(n - 1 for n in ecrasees.values()),
            2,
            "trois lignes construites, deux cles: le coffre en contiendra deux",
        )

    def test_la_cle_ecrasee_est_nommee_et_pas_seulement_comptee(self) -> None:
        ecrasees = RG.collisions_de_cle([
            {"resolution_id": "R003", "etat": "CONSTATEE", "origine": "EXTRAIT"},
            {"resolution_id": "R003", "etat": "CONSTATEE", "origine": "EXTRAIT"},
            {"resolution_id": "R004", "etat": "CONSTATEE", "origine": "EXTRAIT"},
        ])
        self.assertEqual(list(ecrasees), [("R003", "CONSTATEE", "EXTRAIT")])
        self.assertEqual(ecrasees[("R003", "CONSTATEE", "EXTRAIT")], 2)

    def test_un_etat_different_n_est_pas_une_collision(self) -> None:
        """Ce qui a ete PROPOSE et ce qui a ete VOTE coexistent a dessein:
        l'ecart entre les deux est la matiere meme du controle."""
        self.assertEqual(
            RG.collisions_de_cle([
                {"resolution_id": "R003", "etat": "PROJETEE", "origine": "EXTRAIT"},
                {"resolution_id": "R003", "etat": "CONSTATEE", "origine": "EXTRAIT"},
            ]),
            {},
        )

    def test_un_coffre_qui_refuse_l_ecriture_ne_rend_pas_un_registre_vide(self) -> None:
        """Elargir une table existante appartient a la couche de stockage. Ce
        qui appartient a ce module, c'est de ne pas laisser le refus devenir un
        silence: le lecteur rattrape `OperationalError` et rend une liste, si
        bien que 173 resolutions se lisaient « aucune resolution »."""
        import sqlite3

        from coproscope.vault import gouvernance_store as store

        racine = Path(tempfile.mkdtemp())
        (racine / "workspace" / "text").mkdir(parents=True)
        (racine / "workspace" / "text" / "doc.txt").write_text(
            "PROCES-VERBAL DE L'ASSEMBLEE GENERALE\n"
            f"1° - Constitution du bureau. (Article 24) {CLOTURE_OK}\n"
            f"2° - Election du secretaire. (Article 24) {CLOTURE_OK}\n"
            f"3° - Approbation des comptes. (Article 24) {CLOTURE_KO}\n",
            encoding="utf-8",
        )
        (racine / "registre_documents.csv").write_text(
            "doc_id,document_type,text_path,suspected_date\n"
            "DOC-TEST-0001,PV_AG,text/doc.txt,2024-07-03\n",
            encoding="utf-8",
        )

        # `build_register` importe la fonction au moment de l'appel: c'est donc
        # l'attribut du module de stockage qu'il faut remplacer.
        original = store.remplacer_pour_documents

        def refuse(*_args, **_kw):
            raise sqlite3.OperationalError("no such column: sous_numero")

        store.remplacer_pour_documents = refuse
        try:
            run = _RunEnregistre()
            resume = R.build_register(_InstanceAvecCoffre(racine), run)
        finally:
            store.remplacer_pour_documents = original
        self.assertIn("no such column", resume["coffre_refuse_l_ecriture"])
        self.assertEqual(resume["resolutions"], 0)
        self.assertEqual([niveau for niveau, _ in run.lignes], ["WARN"])


def _acte(acte_id: str, ag_id: str, numero: str, resultat: str, **extra) -> dict:
    ligne = {
        "acte_id": acte_id,
        "nature": "RESOLUTION_AG",
        "ag_id": ag_id,
        "numero": numero,
        "sous_numero": "",
        "doc_id": f"DOC-{acte_id[-4:]}",
        "resultat": resultat,
        "date_effet": ag_id[3:] if AS.date_lue(ag_id) else "",
    }
    ligne.update(extra)
    return ligne


class CopiesConcurrentesTests(unittest.TestCase):
    """C054: nommer les copies concurrentes, sans en elire aucune.

    Mesure d'origine: la table `resolutions` portait trois copies de la meme
    assemblee, 55 lignes chacune, numerotees 1 a 55, avec trois comptages
    d'issues differents; deux avaient perdu leur date, donc un `ag_id` derive du
    document. L'ecran affichait trois fois la resolution n° 7 - avec deux issues
    contradictoires - sans jamais dire que rien ne permettait de les distinguer.
    """

    def test_le_meme_rang_sous_trois_assemblees_dont_deux_sans_date(self) -> None:
        actes = [
            _acte("A1", "AG-2024-07-03", "7", "ADOPTEE"),
            _acte("A2", "AG-DOC-729CCCF88863", "7", "REJETEE"),
            _acte("A3", "AG-DOC-E67768CA7ACD", "7", "ADOPTEE"),
        ]
        copies = AS.copies_concurrentes(actes)
        self.assertEqual(sorted(copies), ["A1", "A2", "A3"])
        self.assertEqual(len(copies["A1"]), 2)
        self.assertEqual(
            sorted(c["resultat"] for c in copies["A1"]), ["ADOPTEE", "REJETEE"]
        )

    def test_deux_assemblees_datees_ne_sont_pas_des_copies(self) -> None:
        """Le faux positif qu'il faut absolument eviter: une copropriete tient
        une assemblee par an, chacune a sa resolution n° 7, et elles n'ont rien
        a voir. Leurs dates les distinguent, donc rien n'est signale."""
        actes = [
            _acte("A1", "AG-2024-07-03", "7", "ADOPTEE"),
            _acte("A2", "AG-2026-02-26", "7", "REJETEE"),
        ]
        self.assertEqual(AS.copies_concurrentes(actes), {})

    def test_un_rang_occupe_une_seule_fois_ne_signale_rien(self) -> None:
        actes = [
            _acte("A1", "AG-2024-07-03", "7", "ADOPTEE"),
            _acte("A2", "AG-DOC-729CCCF88863", "8", "REJETEE"),
        ]
        self.assertEqual(AS.copies_concurrentes(actes), {})

    def test_le_degre_fait_partie_du_rang(self) -> None:
        """`11` et `11.1` sont deux resolutions distinctes, chacune avec son
        devis: les confondre reproduirait exactement la collision de C055."""
        actes = [
            _acte("A1", "AG-2024-07-03", "11", "ADOPTEE"),
            _acte("A2", "AG-DOC-729CCCF88863", "11", "REJETEE", sous_numero="1"),
        ]
        self.assertEqual(AS.copies_concurrentes(actes), {})

    def test_une_assemblee_sans_date_est_reconnue_a_la_forme_pas_a_la_longueur(
        self,
    ) -> None:
        """La forme de l'identifiant, jamais sa longueur.

        La regle d'origine du pont etait `not ag.startswith("AG-2") or
        len(ag) != 13`. Comparaison mesuree le 2026-09-05 sur six identifiants:
        les deux regles s'accordent sur quatre et divergent sur deux, et les
        deux divergences sont des erreurs de l'ancienne regle.

        - `AG-1998-07-03`: l'ancienne le rangeait parmi les assemblees SANS
          date, alors que sa date est lue et ordonnable. Une copropriete qui
          verse ses archives d'avant l'an 2000 aurait vu chacune de ses
          assemblees signalee comme non datee.
        - `AG-2XXX-XX-XX`: l'ancienne le tenait pour date, parce qu'il fait
          treize caracteres et commence par `AG-2`. Une longueur ne dit rien
          d'une date.
        """
        self.assertTrue(AS.date_lue("AG-2024-07-03"))
        self.assertTrue(
            AS.date_lue("AG-1998-07-03"),
            "une date lue reste une date lue quel que soit son siecle",
        )
        self.assertFalse(AS.date_lue("AG-2XXX-XX-XX"))
        self.assertFalse(
            AS.date_lue("AG-2024-7-3"),
            "un mois et un jour non completes ne s'ordonnent pas comme des "
            "chaines, et tout le modele compare des dates comme des chaines",
        )
        self.assertFalse(AS.date_lue("AG-DOC-729CCCF88863"))
        self.assertFalse(AS.date_lue(""))

    def test_la_forme_lue_n_est_pas_un_calendrier_verifie(self) -> None:
        """Limite assumee, ecrite plutot que decouverte: `AG-2024-13-45` passe.

        Ce controle ne demande qu'une chose - que la chaine s'ordonne comme les
        autres - parce que c'est la seule propriete dont ce module a besoin.
        Verifier qu'un mois existe est le travail du module de dates, pas
        d'une regle d'identite d'assemblee.
        """
        self.assertTrue(AS.date_lue("AG-2024-13-45"))

    def test_les_assemblees_sans_date_lue_sont_nommees_une_seule_fois(self) -> None:
        actes = [
            _acte("A1", "AG-DOC-729CCCF88863", "7", "ADOPTEE"),
            _acte("A2", "AG-DOC-729CCCF88863", "8", "ADOPTEE"),
            _acte("A3", "AG-2024-07-03", "7", "ADOPTEE"),
        ]
        self.assertEqual(
            AS.assemblees_sans_date_lue(actes), ["AG-DOC-729CCCF88863"]
        )

    def test_un_acte_qui_n_est_pas_une_resolution_n_entre_pas_dans_le_calcul(
        self,
    ) -> None:
        """Une depense d'urgence porte un rang qui n'est pas un rang de
        resolution: les comparer serait comparer deux echelles differentes."""
        actes = [
            _acte("A1", "AG-2024-07-03", "7", "ADOPTEE"),
            _acte("A2", "AG-DOC-729CCCF88863", "7", "ADOPTEE",
                  nature="URGENCE_SYNDIC"),
        ]
        self.assertEqual(AS.copies_concurrentes(actes), {})


if __name__ == "__main__":
    unittest.main()
