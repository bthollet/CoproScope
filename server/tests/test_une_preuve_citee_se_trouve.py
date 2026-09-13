# -*- coding: utf-8 -*-
"""Une preuve citee par le gouvernail se trouve, ou se declare absente.

**LE DEFAUT VISE, ET IL A DEJA EU LIEU.** `RM-2026-0001` porte la mention
`PREUVE MORTE constatee le 2026-09-04`: sa colonne preuve citait `AGENTS.md`,
renomme en `CLAUDE.md` deux jours plus tot par un commit qui annoncait avoir mis
a jour les references. La doctrine avait survecu; **la citation etait morte**, et
rien ne l'a signale pendant deux jours. Le cout n'est pas la citation: c'est
qu'un item dont la preuve est introuvable sera classe mort par le prochain
auditeur, faute de preuve - ce que `RM-2026-0047` nomme explicitement comme le
*manque de structure a corriger avant reprise*.

----------------------------------------------------------------------
Axe, invariant, et ce qui se passe hors des valeurs observees
----------------------------------------------------------------------

- **L'axe.** *Un chemin cite appartient au depot, ou a un autre monde.* Le degre
  de liberte est le MONDE: le depot produit, le workspace local `dev/`, une
  instance privee, une branche ecartee, le coffre. Le gouvernail cite les
  quatre, et c'est legitime.
- **L'invariant le long de l'axe.** Une citation qui designe le depot doit y
  etre trouvable. Une citation qui designe un autre monde n'a pas a l'etre.
- **Ce que le code en fait.** Il ne demande a personne de declarer le monde: il
  le LIT sur le chemin. Le premier segment d'un chemin du depot est un dossier
  de premier niveau du depot, et cette liste est **derivee de `git ls-files`**,
  jamais ecrite ici. Un dossier de premier niveau ajoute demain entre dans la
  mesure sans edition.
- **Hors des valeurs observees.** Un monde inconnu - `coffre/`, `sync/`, un
  prefixe jamais vu - tombe du cote NON verifie, donc du cote sur: la garde ne
  fabrique pas d'alerte sur ce qu'elle ne sait pas situer. La degradation est
  silencieuse mais elle est dans le bon sens, et elle se voit: le compte de
  citations verifiees est affiche par le test de l'instrument.

**LES CITATIONS SONT ABREGEES, ET C'EST CE QUI A REFUTE MON PREMIER
INSTRUMENT.** Une premiere mesure joignait la citation a la racine et annoncait
**31 items citant un chemin absent**. Faux: le gouvernail ecrit `web/depot.py`
pour `server/src/coproscope/web/depot.py`. L'instrument mesurait donc le **style
d'abreviation**, pas l'existence - *le chiffre changerait-il si la chose comptee
disparaissait ?* Non. Une citation est desormais trouvee si elle est un
**suffixe de segments** d'un fichier suivi, ce qui ne suppose aucun prefixe.

**CE QUE CETTE GARDE NE FAIT PAS.** Elle ne verifie pas que le fichier trouve
PROUVE quoi que ce soit - un chemin qui existe peut pointer sur un fichier vide
ou hors sujet. Elle repond a une seule question, celle qui a manque pendant deux
jours: *ce que la cellule cite existe-t-il encore ?*
"""
from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
GOUVERNAIL = DEPOT / "docs" / "roadmap_backlog_central.md"
TITRE_REGISTRE = "## Registre actif par identifiant"

#: Une barre NUE separe deux cellules du gouvernail; une barre echappee est du
#: texte. Meme regle que `tools/gouvernail_depot.py`.
_BARRE_NUE = re.compile(r"(?<!\\)\|")
#: Une citation est un jeton entre accents graves qui porte au moins un `/`.
_CITATION = re.compile(r"`([^`\s]+/[^`\s]+)`")
#: Ce qui ressemble a un fichier. Sans extension, `docs/` ou `web/viewmodels`
#: designent un dossier ou une idee, pas une preuve a ouvrir.
EXTENSIONS = (
    ".py", ".md", ".csv", ".html", ".css", ".js", ".yml", ".yaml", ".json",
    ".toml", ".cmd", ".ps1", ".sqlite3", ".txt", ".svg", ".png", ".pdf",
)

#: Les citations connues comme ABSENTES du depot, avec la raison.
#: **Cette liste est VERIFIEE, pas consultee.** Une entree qui redevient
#: trouvable fait rougir `test_aucune_absence_declaree_n_est_revenue`: sans ce
#: sens inverse, la liste deviendrait un cimetiere ou l'on range ce qui gene.
ABSENTES_DECLAREES: dict[str, str] = {
    "docs/coherence_type_contenu_docuscope.md":
        "RM-2026-0053: ce document ne vit que sur la branche ECARTEE `ef51256`, "
        "ce que la decision de non-integration implique. La cellule le dit "
        "deja en clair; l'entree ici est ce qui rend la declaration verifiable.",
    "registers/artefacts_produits.csv":
        "RM-2026-0061: ce registre est PRODUIT au runtime dans une instance, "
        "par l'estampille de provenance. Le dossier `registers/` est commite "
        "pour l'instance synthetique publique, mais ce fichier-la ne l'est "
        "jamais - il n'existe qu'apres une absorption. La citation est donc "
        "legitime et son absence du depot est normale, pas une preuve morte.",
    "web/coffre_partage_view.py":
        "RM-2026-0033: l'ecran `/coffre/partage` est SUPPRIME par la recette de "
        "Brice du 2026-09-13 (`RM-2026-0183`). La cellule garde la citation "
        "historique et dit la suppression a cote.",
    "tests/test_ui_coffre_partage.py":
        "RM-2026-0033: test dedie de l'ecran `/coffre/partage`, supprime avec "
        "lui le 2026-09-13 (`RM-2026-0183`).",
}


def _fichiers_suivis() -> list[str]:
    """Les fichiers qui APPARTIENNENT au depot: suivis, ou presents et non ignores.

    **`git ls-files` seul ne suffit pas, et le defaut est immediat.** Un lot qui
    ecrit un test et cite son chemin dans le gouvernail avant de commiter
    verrait la garde declarer sa propre preuve morte. Inversement, la seule
    presence sur le disque ferait entrer les instances privees et les sorties
    locales, que `.gitignore` exclut justement. Le critere est donc
    **appartenir au depot**: `--cached` pour ce qui y est deja, `--others
    --exclude-standard` pour ce qui y entre et n'est pas ignore.
    """
    sortie = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=str(DEPOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout
    return [ligne.strip() for ligne in sortie.splitlines() if ligne.strip()]


def _suffixes(chemins: list[str]) -> set[str]:
    """Tous les suffixes de segments des fichiers suivis.

    C'est ce qui rend la mesure independante du prefixe: `web/depot.py` est
    trouve par `server/src/coproscope/web/depot.py` sans qu'aucun prefixe soit
    ecrit ici.
    """
    trouvables: set[str] = set()
    for chemin in chemins:
        parts = chemin.replace("\\", "/").split("/")
        for i in range(len(parts)):
            trouvables.add("/".join(parts[i:]))
    return trouvables


def _mondes_du_depot(chemins: list[str]) -> set[str]:
    """Les DOSSIERS du depot, par tous leurs suffixes de segments.

    **Premiere version refutee par sa propre campagne de mutation.** Elle ne
    retenait que les dossiers de PREMIER NIVEAU - `server`, `docs`, `tools`. Or
    le gouvernail cite ses preuves abregees, et la forme la plus courante est
    `tests/test_x.py`: son premier segment n'est pas un dossier de premier
    niveau, donc **la citation d'un test supprime ne mordait pas**. C'est
    exactement le defaut de `RM-2026-0001` que la garde existe pour attraper,
    et la mutation 2 l'a montre en une ligne.

    Un dossier est donc situe dans le depot si **un fichier suivi vit sous un
    dossier dont le chemin cite est un suffixe de segments**. `tests/` est
    reconnu par `server/tests/`, `web/viewmodels/` par
    `server/src/coproscope/web/viewmodels/`. Rien n'est enumere.
    """
    dossiers: set[str] = set()
    for chemin in chemins:
        parts = chemin.replace("\\", "/").split("/")[:-1]
        for i in range(len(parts)):
            dossiers.add("/".join(parts[i:]))
    return dossiers


def _citations_du_registre() -> list[tuple[str, str]]:
    """`(identifiant, citation)` pour chaque chemin cite dans le registre."""
    texte = GOUVERNAIL.read_text(encoding="utf-8")
    lignes = texte.splitlines()
    debut = next((i for i, l in enumerate(lignes)
                  if l.startswith(TITRE_REGISTRE)), None)
    if debut is None:
        raise LookupError(
            "titre %r introuvable: le registre a ete renomme ou deplace, et une "
            "mesure qui rendrait zero citation passerait pour un registre sain"
            % TITRE_REGISTRE)
    fin = next((i for i, l in enumerate(lignes[debut + 1:], debut + 1)
                if l.startswith("## ")), len(lignes))

    citations: list[tuple[str, str]] = []
    for ligne in lignes[debut:fin]:
        if not ligne.startswith("| `RM-"):
            continue
        cellules = _BARRE_NUE.split(ligne)
        if len(cellules) < 12:
            continue
        identifiant = cellules[1].strip().strip("`")
        corps = " ".join(cellules[7:11])
        for brut in _CITATION.findall(corps):
            chemin = brut.strip().rstrip(".,;:)").replace("\\", "/")
            if chemin.startswith("http") or re.match(r"^[A-Za-z]:", chemin):
                continue
            if not chemin.lower().endswith(EXTENSIONS):
                continue
            citations.append((identifiant, chemin))
    return citations


class UNE_PREUVE_CITEE_SE_TROUVE(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suivis = _fichiers_suivis()
        cls.trouvables = _suffixes(cls.suivis)
        cls.mondes = _mondes_du_depot(cls.suivis)
        cls.citations = _citations_du_registre()
        cls.du_depot = [
            (ident, chemin) for ident, chemin in cls.citations
            if chemin.rsplit("/", 1)[0] in cls.mondes
            or chemin in cls.trouvables
        ]

    def test_l_instrument_a_vraiment_lu_le_registre(self) -> None:
        """Sans ce controle, une mesure a vide passerait les tests suivants.

        Le motif est celui du `0/7` du 2026-09-12: un instrument casse
        n'epargne aucun cas, alors qu'un defaut reel en epargne.
        """
        self.assertGreater(len(self.suivis), 500,
                           "git ls-files rend trop peu de fichiers")
        self.assertGreater(len(self.citations), 100,
                           "moins de 100 citations lues: l'extraction est cassee")
        self.assertGreater(len(self.du_depot), 100,
                           "moins de 100 citations situees dans le depot")
        self.assertIn("docs", self.mondes)
        self.assertIn("server", self.mondes)

    def test_toute_preuve_du_depot_s_y_trouve(self) -> None:
        """Le defaut de `RM-2026-0001`: une citation qui a survecu a son fichier."""
        mortes = sorted({
            (ident, chemin) for ident, chemin in self.du_depot
            if chemin not in self.trouvables
            and chemin not in ABSENTES_DECLAREES
        })
        self.assertEqual(
            [], mortes,
            "ces preuves sont citees comme si elles etaient dans le depot et "
            "n'y sont pas. Deux issues, jamais une troisieme: corriger le "
            "chemin, ou declarer l'absence et sa raison dans "
            "`ABSENTES_DECLAREES`. Un item dont la preuve est introuvable sera "
            "classe mort par le prochain auditeur: %s" % mortes)

    def test_aucune_absence_declaree_n_est_revenue(self) -> None:
        """Le sens inverse, sans lequel la liste deviendrait un cimetiere.

        Une absence declaree qui redevient trouvable est une declaration
        perimee: elle dit au lecteur qu'une preuve manque alors qu'elle est la.
        """
        revenues = sorted(chemin for chemin in ABSENTES_DECLAREES
                          if chemin in self.trouvables)
        self.assertEqual(
            [], revenues,
            "ces chemins sont declares absents du depot et s'y trouvent "
            "desormais: retirer l'entree de `ABSENTES_DECLAREES`, sinon le "
            "gouvernail continue d'annoncer un trou comble: %s" % revenues)

    def test_une_absence_declaree_est_bien_citee_par_un_item(self) -> None:
        """Une declaration qui ne correspond a aucune citation est du bruit."""
        citees = {chemin for _ident, chemin in self.citations}
        orphelines = sorted(chemin for chemin in ABSENTES_DECLAREES
                            if chemin not in citees)
        self.assertEqual(
            [], orphelines,
            "ces absences sont declarees et plus aucun item ne cite le chemin: "
            "l'entree ne protege plus rien et doit partir: %s" % orphelines)

    def test_chaque_absence_declaree_dit_POURQUOI(self) -> None:
        """Une raison vide reduirait la liste a une permission de se taire."""
        for chemin, raison in sorted(ABSENTES_DECLAREES.items()):
            with self.subTest(chemin=chemin):
                self.assertRegex(
                    raison, r"RM-\d{4}-\d{4}",
                    "la raison ne rattache l'absence a aucun item: on ne "
                    "pourra pas savoir qui l'a decidee")
                self.assertGreater(
                    len(raison), 60,
                    "une raison d'un mot n'est pas une raison")


class UN_MONDE_HORS_DEPOT_N_EST_PAS_VERIFIE(unittest.TestCase):
    """Temoins: sans eux, la garde du dessus serait un `assertEqual([], [])`.

    Le premier prouve qu'une citation du depot introuvable MORD. Le second
    prouve qu'une citation d'un autre monde ne mord PAS - sinon la garde
    exigerait que le workspace local et les instances privees entrent dans Git,
    ce que la doctrine interdit.
    """

    def setUp(self) -> None:
        self.suivis = _fichiers_suivis()
        self.trouvables = _suffixes(self.suivis)
        self.mondes = _mondes_du_depot(self.suivis)

    def _situee_dans_le_depot(self, chemin: str) -> bool:
        return chemin.rsplit("/", 1)[0] in self.mondes or chemin in self.trouvables

    def test_une_preuve_du_depot_introuvable_serait_vue(self) -> None:
        faux = "docs/ce_document_n_existe_pas_20260912.md"
        self.assertTrue(self._situee_dans_le_depot(faux))
        self.assertNotIn(faux, self.trouvables)

    def test_un_chemin_du_workspace_local_n_est_pas_exige(self) -> None:
        """`dev/` est le workspace local, hors du depot produit par construction."""
        self.assertFalse(
            self._situee_dans_le_depot("dev/tooling/scripts/un_outil_local.cmd"),
            "un chemin du workspace local est traite comme une preuve du "
            "depot: la garde exigerait que `dev/` entre dans Git")

    def test_un_chemin_d_instance_n_est_pas_exige(self) -> None:
        """Une instance privee n'est jamais commitee, sa citation est legitime.

        **Ce temoin s'est trompe une fois, et le corriger a appris quelque
        chose.** Il citait `staging/privacy_dir/file_biffage.csv` comme exemple
        de chemin hors depot: **il est trouvable**, parce que l'instance
        synthetique `examples/synthetic_copro` EST commitee et porte ce
        fichier. La garde a donc raison contre le temoin - une citation
        abregee d'instance se resout sur l'exemple public, et c'est exactement
        ce qu'on veut. Restent hors depot les chemins qu'aucune instance
        publique ne porte.
        """
        for chemin in ("vault_local/gouvernance.sqlite3",
                       "coffre/un_document_recu.pdf"):
            with self.subTest(chemin=chemin):
                self.assertFalse(self._situee_dans_le_depot(chemin))

    def test_un_dossier_commite_dont_le_fichier_est_PRODUIT_se_declare(self) -> None:
        """La frontiere fine, et elle a coute une entree de declaration.

        `registers/` est commite pour l'instance synthetique publique, donc la
        garde SITUE `registers/artefacts_produits.csv` dans le depot - alors que
        ce fichier-la est produit au runtime et n'y sera jamais. Le cas ne se
        resout pas par un affinage de regle: il se DECLARE, sinon la garde
        fabrique une alerte sur une citation legitime.
        """
        chemin = "registers/artefacts_produits.csv"
        self.assertTrue(self._situee_dans_le_depot(chemin))
        self.assertIn(chemin, ABSENTES_DECLAREES)

    def test_un_chemin_d_instance_PUBLIQUE_est_bien_trouve(self) -> None:
        """Le pendant du temoin corrige ci-dessus, garde pour ne pas l'oublier."""
        self.assertTrue(
            self._situee_dans_le_depot("staging/privacy_dir/file_biffage.csv"),
            "l'instance synthetique est commitee: une citation abregee de ses "
            "fichiers doit se resoudre, sinon la garde laisse passer des "
            "citations mortes en les prenant pour des chemins d'instance privee")

    def test_une_citation_abregee_du_depot_est_bien_trouvee(self) -> None:
        """Le defaut qui a refute le premier instrument, garde comme temoin."""
        self.assertIn("web/depot.py", self.trouvables)
        self.assertIn("core/pipeline.py", self.trouvables)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
