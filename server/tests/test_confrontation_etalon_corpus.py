"""La chaine, confrontee a ce qu'un humain a lu dans les pieces.

C'est la confrontation que `docs/etalon_corpus_tests_ux.md` confie explicitement
a « un autre lot, par quelqu'un qui n'a pas etabli l'etalon ». Elle n'avait
jamais eu lieu: `instances/tests_ux` etait posee depuis le 2026-09-03 avec tous
ses registres a zero.

Ces tests s'ignorent hors du poste de Brice: le corpus est prive et n'entrera
jamais dans le depot. Ils ne portent que des COMPTES, jamais de contenu.

Resultat du premier passage, 2026-09-07:

- les issues tombent EXACTEMENT sur l'etalon - 39 adoptees, 7 rejetees, 8 sans
  vote, 1 sans formule de vote. C'est la premiere preuve de justesse de la
  chaine contre une verite etablie a la main;
- la majorite de l'article 24 tombe juste, 30 sur 30;
- l'article 25B est EFFACE: l'etalon distingue 23 resolutions `25 et 25-1` d'une
  resolution `25B`, la chaine rend 24 fois `25`. Elle perd la lettre. C'est le
  constat C076 du gouvernail, mesure ici pour la premiere fois;
- l'assemblee est comptee DEUX fois, 110 resolutions au lieu de 55, parce que le
  corpus contient le PV et sa propre extraction de texte - piege delibere de
  l'etalon, axe (A) de `RM-2026-0086`.
"""

from __future__ import annotations

import collections
import re
import sqlite3
import unittest
from pathlib import Path

from tests._instance_de_lot import corpus_portant

DEPOT = Path(__file__).resolve().parents[2]
ETALON = DEPOT / "docs" / "etalon_corpus_tests_ux.md"

#: **Le nom de l'instance de lot etait GRAVE ici, et l'instance a ete supprimee**
#: - la doctrine imposait sa suppression, et elle a ete appliquee. Resultat
#: mesure le 2026-09-09: les quatre tests sautaient et le module rendait
#: `OK (skipped=4)`. **Une garde verte qui ne mesure rien**, et la confrontation
#: du 2026-09-07 etait redevenue une trace au lieu d'une preuve rejouable.
#:
#: C'est le meme motif que les cinq references d'instance mortes de `CLAUDE.md`
#: et que le lanceur qui mourait en silence (`RM-2026-0125`): **un nom
#: d'instance ecrit en dur survit au dossier.** On ne le remplace donc pas par
#: un autre nom - on cherche ce qui porte la PROPRIETE voulue: une instance
#: derivee du corpus etalon, qui a deja ete absorbee.
#: **Ce que la mesure EXIGE, et rien de plus large.**
#:
#: Une premiere version cherchait un prefixe de nom, `tests_ux` - ma propre
#: modalite, prise en defaut le soir meme: le corpus a ete absorbe dans une
#: instance nommee `test_etalon_20260909`, et la garde a continue de sauter.
#:
#: Un selecteur doit etre **aussi specifique que la dependance de la mesure**,
#: ni plus ni moins. Cette mesure depend de deux choses: le manifeste du corpus
#: etalon - c'est lui qui identifie CE corpus et pas un autre - et un coffre
#: bati. Le nom n'entre pas dedans.
MANIFESTE_ETALON = "registers/manifeste_corpus_tests_ux.csv"

#: Le coffre bati: la seconde piece dont la mesure depend. La confrontation lit
#: la table `resolutions`, donc une instance sans coffre n'est pas *une autre
#: version* du corpus - il n'y a rien a confronter.
COFFRE = "**/gouvernance.sqlite3"

#: **Ce module trouvait son instance tout seul, et il triait par date.** Sa
#: propre fonction disait: *« rend les candidates de la plus recente a la plus
#: ancienne »*, puis prenait la premiere. **Cette phrase est ici contredite.**
#: Releve du 2026-09-09, et c'est une observation datee, pas un invariant: DEUX
#: instances du poste portent le manifeste de l'etalon, une seule porte aussi un
#: coffre bati - l'autre n'a jamais ete ingeree, par construction, pour ne pas
#: la muter. Il n'y a donc qu'une candidate, et le tri par date ne se voit pas.
#: Le jour ou l'on rebatit la seconde pour la confronter, elles seront deux, et
#: **la date de derniere ecriture designerait la preuve de justesse du
#: produit**. Une ambiguite se declare, elle ne se tranche pas au mtime.
#: Voir `_instance_de_lot.py`.
CORPUS = corpus_portant(
    MANIFESTE_ETALON,
    COFFRE,
    mesure=("que les issues lues tombent sur celles qu'un humain a relevees a "
            "la main, et que l'assemblee ne soit pas comptee deux fois"),
)

LIGNE_RESOLUTION = re.compile(r"^\|\s*(\d+)\s*\|([^|]*)\|([^|]*)\|")
ANCRE_TABLE = "Detail resolution par resolution"

#: L'etalon et le code nomment la meme issue differemment. Ce n'est pas un
#: desaccord de fond: c'est une modalite d'ecriture, et la table le dit.
MEMES_ISSUES = {
    "ADOPTEE": "ADOPTEE",
    "REJETEE": "REJETEE",
    "PAS DE VOTE": "PAS_DE_VOTE",
    "ISSUE NON ENONCEE": "VOTE_SANS_FORMULE",
}


def _etalon() -> list[tuple[int, str, str]]:
    lignes: list[tuple[int, str, str]] = []
    dans = False
    for ligne in ETALON.read_text(encoding="utf-8").splitlines():
        if ANCRE_TABLE in ligne:
            dans = True
            continue
        if not dans:
            continue
        trouve = LIGNE_RESOLUTION.match(ligne)
        if trouve:
            lignes.append((int(trouve.group(1)), trouve.group(2).strip(), trouve.group(3).strip()))
        elif lignes and not ligne.startswith("|"):
            break
    return lignes


def _coffre() -> sqlite3.Connection:
    """Ouvert MAINTENANT. `fichiers[0]` rendait un `IndexError` nu quand
    l'instance disparaissait entre le chargement du module et la mesure."""
    return sqlite3.connect(CORPUS.une_piece(COFFRE))


def _assemblee_la_plus_fournie(connexion: sqlite3.Connection) -> str:
    return connexion.execute(
        "select ag_id from resolutions group by ag_id order by count(*) desc limit 1"
    ).fetchone()[0]


class LEtalonSeLitToujours(unittest.TestCase):
    """Ce que ce module mesure MEME sans instance, donc partout, CI comprise.

    Ecrit parce que les quatre tests de confrontation ne peuvent pas tourner
    sans corpus prive: si le module ne portait qu'eux, il rendrait `OK` en
    n'ayant rien lu du tout. Ici, au moins, la table de l'etalon est lue et sa
    forme est verifiee - la partie qui vit dans le depot.
    """

    def test_la_table_de_l_etalon_se_lit_et_ne_saute_aucun_numero(self) -> None:
        lignes = _etalon()
        self.assertGreater(len(lignes), 50, "table de l'etalon illisible ou tronquee")
        numeros = [n for n, _, _ in lignes]
        self.assertEqual(sorted(numeros), numeros, "numeros de resolution desordonnes")
        self.assertEqual(len(set(numeros)), len(numeros), "numero de resolution en double")
        self.assertEqual(list(range(numeros[0], numeros[-1] + 1)), numeros,
                         "trou dans la numerotation des resolutions")

    def test_chaque_issue_de_l_etalon_a_son_equivalent_dans_le_code(self) -> None:
        """Une issue inconnue ferait echouer la confrontation pour rien.

        **La troisieme colonne porte l'issue, la deuxieme porte la majorite.**
        Une premiere version de ce test lisait la deuxieme et reprochait a
        l'etalon des issues nommees `24`, `25B`, `25 ET 25-1` - c'est-a-dire des
        articles de la loi. Le test avait tort, pas l'etalon.
        """
        inconnues = sorted({i.upper() for _, _, i in _etalon()} - set(MEMES_ISSUES))
        self.assertEqual([], inconnues, "issues de l'etalon sans equivalent: %s" % inconnues)


@unittest.skipUnless(CORPUS.mesurable and ETALON.exists(), CORPUS.motif_de_saut)
class LaChaineTrouveCeQueLHumainALu(unittest.TestCase):
    def setUp(self) -> None:
        self.connexion = _coffre()
        self.addCleanup(self.connexion.close)
        self.assemblee = _assemblee_la_plus_fournie(self.connexion)

    def test_la_distribution_des_issues_tombe_exactement_sur_l_etalon(self) -> None:
        attendu = collections.Counter(
            MEMES_ISSUES.get(issue, issue) for _, _, issue in _etalon()
        )
        lu = collections.Counter(
            ligne[0]
            for ligne in self.connexion.execute(
                "select resultat from resolutions where ag_id=?", (self.assemblee,)
            )
        )
        self.assertEqual(
            dict(lu),
            dict(attendu),
            msg=(
                "La chaine ne lit plus les memes issues que l'humain. Avant de corriger "
                "le code, verifiez lequel des deux a change: l'etalon precede l'outil et "
                "fait foi, mais il a deja ete refute une fois."
            ),
        )

    def test_la_majorite_de_l_article_24_tombe_juste(self) -> None:
        attendu = sum(1 for _, majorite, _ in _etalon() if majorite == "24")
        lu = self.connexion.execute(
            "select count(*) from resolutions where ag_id=? and majorite_annoncee='24'",
            (self.assemblee,),
        ).fetchone()[0]
        self.assertEqual(lu, attendu)

    def test_CARACTERISATION_la_lettre_du_25B_est_effacee(self) -> None:
        """Constat C076 du gouvernail, mesure ici pour la premiere fois.

        L'etalon distingue 23 resolutions `25 et 25-1` d'une resolution `25B`.
        La chaine rend 24 fois `25`: elle a perdu la lettre, donc elle ne peut
        plus distinguer une majorite de l'article 25 d'une majorite de l'article
        25B, qui n'ont pas les memes consequences.

        Quand ce test echouera, la lettre est conservee: supprimez-le et
        remplacez-le par une egalite stricte sur les majorites.
        """
        vingt_cinq_etalon = sum(1 for _, majorite, _ in _etalon() if majorite.startswith("25"))
        lu = self.connexion.execute(
            "select count(*) from resolutions where ag_id=? and majorite_annoncee='25'",
            (self.assemblee,),
        ).fetchone()[0]
        self.assertEqual(
            lu,
            vingt_cinq_etalon,
            "Le compte des majorites 25 a change; ce n'est plus le simple effacement de la lettre.",
        )
        distinctes = {
            ligne[0]
            for ligne in self.connexion.execute(
                "select distinct majorite_annoncee from resolutions where ag_id=?", (self.assemblee,)
            )
        }
        self.assertNotIn(
            "25B",
            distinctes,
            "La chaine distingue enfin le 25B: le defaut est corrige, ce test doit etre supprime.",
        )

    def test_CARACTERISATION_le_derive_du_pv_est_absorbe_en_ecrasant_l_original(self) -> None:
        """Le piege de l'etalon a change de FORME, il n'a pas disparu.

        **Ce test attendait `[55, 55]` - deux assemblees portant les memes 55
        resolutions - et c'est ce qu'il mesurait jusqu'au 2026-09-08.** Le
        corpus porte le proces-verbal ET sa propre extraction de texte, dont le
        nom contient le `doc_id` du PDF; leurs empreintes different, donc la
        deduplication par empreinte ne voit rien.

        **Mesure du 2026-09-09, sur le corpus reabsorbe a vide.** Les deux
        pieces sont bien absorbees et toutes deux classees `PV_AG` - verifie au
        registre, 59 611 et 60 264 caracteres. Mais le coffre ne porte plus
        qu'**une** assemblee, `AG-2024-07-03`, **tiree d'UN SEUL document
        source**. Le doublon n'a pas ete resolu: **l'un a ecrase l'autre**, et
        c'est ce que le verdict du passage declare au meme instant -
        `55 cles de resolution ecrasees`.

        **Pourquoi ce test reste, au lieu d'etre supprime.** Son ancien message
        disait *si une seule assemblee porte 55 resolutions, le defaut est
        corrige*. C'etait trop optimiste, et le remplacer par un test vert
        aurait efface un defaut vivant: **deux exemplaires d'un meme document se
        comparent, ils ne se remplacent pas.** Un avoir, une facture
        rectificative, un PV signe contre son brouillon: l'ecrasement silencieux
        perdrait la difference.

        Ce que ce test fige aujourd'hui: **une seule assemblee, un seul document
        source, et une perte declaree**. Le jour ou les deux exemplaires seront
        confrontes au lieu d'etre ecrases, il faudra le reecrire - pas avant.
        """
        par_assemblee = dict(
            self.connexion.execute("select ag_id, count(*) from resolutions group by ag_id")
        )
        self.assertEqual(
            sorted(par_assemblee.values()), [55],
            msg="La forme du doublon a encore change: remesurer avant de conclure.",
        )
        sources = dict(
            self.connexion.execute(
                "select ag_id, count(distinct doc_id) from resolutions group by ag_id"
            )
        )
        self.assertEqual(
            sorted(sources.values()), [1],
            msg=(
                "L'assemblee est desormais construite sur plusieurs documents: c'est "
                "peut-etre la confrontation attendue, peut-etre une fragmentation. "
                "Mesurer avant de rendre ce test vert."
            ),
        )


if __name__ == "__main__":
    unittest.main()
