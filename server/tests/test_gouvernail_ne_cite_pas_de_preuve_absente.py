# -*- coding: utf-8 -*-
"""Un item du gouvernail ne cite pas comme preuve un fichier introuvable.

**La troisieme forme de la serie A de `RM-2026-0172`: une trace fausse produit
une preuve qui a l'air verifiable.** Et elle est la pire des trois a un egard
que la conversation voisine a nomme: un test saute laisse au moins un
`skipped` dans une sortie; **une trace fausse ne signale rien du tout.** Elle
est lisible, datee, sourcee, et elle designe un fichier qui n'existe pas.

**Mesure du 2026-09-09, et il a fallu deux instruments pour l'obtenir.** Le
premier resolvait chaque chemin depuis la racine du depot et annonçait **38
citations mortes**; une synthese automatique en annonçait 35 par le meme
chemin. Les deux se trompaient de la meme façon: `core/pipeline.py` vit sous
`server/src/coproscope/`, et `staging/privacy_dir/...` est relatif a une
INSTANCE privee, hors depot par construction. **Le compteur mesurait une seule
base pour des chemins ecrits depuis plusieurs** - la variante 4 de la serie B,
dans l'instrument. Le compte reel etait **2** dans les lignes d'item, dont
**une ecrite le soir meme**, dans l'item qui traite justement de la
confidentialite.

**L'axe.** Ce qui varie: la racine depuis laquelle un chemin est ecrit, le
moment ou le fichier disparait, la raison de sa disparition. Ce qui reste
invariant: **une preuve doit etre atteignable, ou declarer qu'elle ne l'est
pas.** La seconde branche compte autant que la premiere - un document reste
souvent cite apres avoir ete ecarte, et l'effacer perdrait la trace.

**Ce que ce garde ne couvre pas, et c'est declare:**

- **le journal** du meme fichier n'est pas examine. Il raconte le passe, et un
  outil supprime a dessein - un superviseur d'orchestration retire le
  2026-09-02 - doit pouvoir y rester nomme. Une consigne se corrige, un
  temoignage ne se reecrit pas;
- les chemins **relatifs a une instance** privee ne sont pas verifiables ici:
  la CI n'a pas le droit de lire une instance;
- les chemins du **workspace parent** sont verifiables sur le poste seulement,
  et ce garde les accepte sans les exiger.

**Cette derniere phrase etait fausse dans le code jusqu'au 2026-09-13.**
`_atteignable` exigeait le fichier sous le dossier parent du depot, partout.
Sur le poste, le parent est le workspace et la garde tenait; depuis un clone
isole - un worktree range ailleurs, la CI de GitHub - le parent ne porte rien, et
quatre citations `dev/...` parfaitement vraies faisaient echouer la suite.
Mesure: suite de l'arbre publie, jouee depuis un worktree, une seule faute, et
c'etait celle-la. **L'axe:** la zone d'un chemin (depot, instance, workspace) et
la presence de cette zone dans l'arbre qui mesure. **L'invariant:** une zone du
depot est toujours la, donc un chemin du depot se verifie partout; une zone du
workspace se verifie la ou le workspace est present. **La presence du workspace
se derive des citations elles-memes** - au moins une zone citee hors du depot
existe sous le parent - et jamais d'un nom de dossier ecrit ici. Hors du poste,
les citations inverifiables ne passent pas en silence: un test les compte et se
declare saute.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
WORKSPACE = DEPOT.parent
GOUVERNAIL = DEPOT / "docs" / "roadmap_backlog_central.md"

TITRE_REGISTRE = "## Registre actif par identifiant"

#: Les racines depuis lesquelles un chemin du depot peut legitimement s'ecrire.
RACINES = (
    DEPOT,
    DEPOT / "server" / "src" / "coproscope",
    DEPOT / "server" / "src",
    DEPOT / "server",
    DEPOT / "server" / "src" / "coproscope" / "modules",
    DEPOT / "server" / "src" / "coproscope" / "web",
)

#: Dossiers de premier niveau d'une instance. Hors depot par construction.
DOSSIERS_D_INSTANCE = ("staging/", "registers/", "vault_local/", "outputs/",
                       "raw/", "restricted/", "logs/", "system/")

EXTENSIONS = ("md", "py", "csv", "json", "yml", "yaml", "html", "js", "css",
              "ps1", "cmd", "sqlite3", "txt", "pyfrag", "mmd", "png", "svg")

#: Un chemin cite: entre accents graves, avec une barre oblique et une
#: extension connue. Plus large, le motif attraperait des identifiants et des
#: noms de branche - le compteur mesurerait sa propre liste de mots.
_CHEMIN = re.compile(
    r"`([A-Za-z0-9_./\-]+/[A-Za-z0-9_.\-]+\.(?:%s))`" % "|".join(EXTENSIONS)
)

_ITEM = re.compile(r"^\| `(RM-\d{4}-\d{4})` \|")

#: Une citation qui DECLARE son absence a le droit d'exister. Radicaux compares
#: sans casse ni apostrophe, lecon du garde des valeurs refutees: une premiere
#: version comparait des tournures exactes et signalait une ligne qui declarait
#: pourtant parfaitement l'absence.
_DECLARE_L_ABSENCE = ("absent", "n exist", "supprim", "disparu", "ecarte",
                      "retire", "jamais integre", "hors depot", "refut")


#: Combien de caracteres autour de la citation forment son voisinage.
#:
#: **Une premiere version cherchait la declaration dans TOUTE la ligne, et le
#: controle negatif ne s'est pas declenche.** Une ligne du registre fait
#: plusieurs milliers de caracteres et onze cellules: le mot `retirees`, ecrit
#: a propos d'autre chose a l'autre bout de la ligne, exemptait **tous** ses
#: chemins. Le garde etait decoratif sur toute ligne contenant un mot courant.
#:
#: **Une declaration doit etre ADJACENTE a ce qu'elle declare.** C'est
#: l'invariant: on ne declare pas l'absence d'un fichier a trois mille
#: caracteres de son nom, et personne ne lirait la declaration la-bas.
VOISINAGE = 200


def _declare_l_absence(fragment: str) -> bool:
    normal = fragment.lower().replace("'", " ").replace("’", " ")
    return any(m in normal for m in _DECLARE_L_ABSENCE)


def _voisinage(ligne: str, debut: int, fin: int) -> str:
    """Ce qui entoure la citation, **la citation exclue**.

    **Second defaut, revele par mon propre test avant le corpus.** Le fragment
    incluait d'abord la citation elle-meme: un fichier nomme `docs/absent.md`
    contenait donc le mot `absent` et **se declarait absent tout seul**. Une
    citation ne peut pas etre son propre temoin - c'est la meme raison qui
    interdit a un verdict de se fonder sur lui-meme.
    """
    avant = ligne[max(0, debut - VOISINAGE):debut]
    apres = ligne[fin:fin + VOISINAGE]
    return avant + " " + apres


def _lignes_d_item() -> list[tuple[int, str, str]]:
    """Les lignes du registre actif seul: le journal raconte le passe."""
    lignes = GOUVERNAIL.read_text(encoding="utf-8").splitlines()
    debut = next(i for i, l in enumerate(lignes) if l.startswith(TITRE_REGISTRE))
    fin = next((i for i, l in enumerate(lignes[debut + 1:], debut + 1)
                if l.startswith("## ")), len(lignes))
    trouvees = []
    for i in range(debut, fin):
        m = _ITEM.match(lignes[i])
        if m:
            trouvees.append((i + 1, m.group(1), lignes[i]))
    return trouvees


def _zone_du_depot(rel: str, racines=RACINES) -> bool:
    """Le premier segment du chemin existe dans le depot: la zone est la partout."""
    premier = Path(rel).parts[0]
    return any((racine / premier).exists() for racine in racines)


def _workspace_present(hors_depot, workspace: Path = WORKSPACE) -> bool:
    """Au moins une zone citee hors du depot existe sous le parent."""
    return any((workspace / Path(rel).parts[0]).is_dir() for rel in hors_depot)


def _classer(rel: str, racines, workspace: Path, workspace_present: bool) -> str:
    """`atteignable`, `faute` ou `inverifiable` - la derniere hors du poste seulement."""
    if _atteignable(rel, racines, workspace):
        return "atteignable"
    if _zone_du_depot(rel, racines) or workspace_present:
        return "faute"
    return "inverifiable"


def _atteignable(rel: str, racines=RACINES, workspace: Path = WORKSPACE) -> bool:
    if rel.startswith(DOSSIERS_D_INSTANCE):
        return True          # instance privee: non verifiable, pas un defaut
    natif = Path(rel)
    if any((racine / natif).exists() for racine in racines):
        return True
    return (workspace / natif).exists()


def _citations_non_declarees() -> list[tuple[int, str, str]]:
    """Chaque chemin introuvable d'une ligne d'item, sans declaration adjacente."""
    trouvees = []
    for numero, rm, ligne in _lignes_d_item():
        for m in _CHEMIN.finditer(ligne):
            rel = m.group(1)
            if _atteignable(rel):
                continue
            if _declare_l_absence(_voisinage(ligne, m.start(), m.end())):
                continue
            trouvees.append((numero, rm, rel))
    return trouvees


class LeGouvernailNeCitePasDePreuveAbsente(unittest.TestCase):
    def test_le_registre_est_trouve_et_cite_des_chemins(self) -> None:
        """Sans cela, un garde qui ne lit rien passerait pour vert."""
        lignes = _lignes_d_item()
        self.assertGreater(len(lignes), 100, "registre suspect: %d lignes" % len(lignes))
        cites = sum(len(_CHEMIN.findall(l)) for _, _, l in lignes)
        self.assertGreater(cites, 50, "seulement %d chemins cites: motif suspect" % cites)

    def test_chaque_chemin_cite_est_atteignable_ou_declare_absent(self) -> None:
        introuvables = _citations_non_declarees()
        present = _workspace_present(rel for _, _, rel in introuvables if not _zone_du_depot(rel))
        fautes = []
        for numero, rm, rel in introuvables:
            if _classer(rel, RACINES, WORKSPACE, present) == "faute":
                fautes.append(
                    "ligne %d, `%s`: la preuve `%s` n'existe nulle part. La corriger, "
                    "ou dire dans la ligne qu'elle est absente - une preuve introuvable "
                    "presentee comme verifiable est pire qu'une preuve manquante."
                    % (numero, rm, rel)
                )
        self.maxDiff = None
        self.assertEqual([], fautes, "\n".join(fautes))

    def test_RESIDU_hors_du_poste_les_chemins_du_workspace_ne_se_verifient_pas(self) -> None:
        """Le silence de la garde hors du poste se dit: un saut, avec son compte."""
        introuvables = _citations_non_declarees()
        hors = [rel for _, _, rel in introuvables if not _zone_du_depot(rel)]
        if hors and not _workspace_present(hors):
            self.skipTest("workspace parent absent: %d citation(s) hors depot non verifiee(s) ici, "
                          "par exemple `%s`" % (len(hors), hors[0]))

    def test_une_zone_du_workspace_se_verifie_la_ou_elle_est(self) -> None:
        """Quatre cas a reponse connue, sur un depot et un workspace fabriques."""
        import tempfile
        with tempfile.TemporaryDirectory() as dossier:
            workspace = Path(dossier)
            depot = workspace / "depot"
            (depot / "docs").mkdir(parents=True)
            (workspace / "atelier" / "outils").mkdir(parents=True)
            (workspace / "atelier" / "outils" / "present.py").write_text("", encoding="utf-8")
            racines = (depot,)
            cas = [
                ("atelier/outils/present.py", True, "atteignable"),
                ("atelier/outils/absent.py", True, "faute"),
                ("atelier/outils/absent.py", False, "inverifiable"),
                ("docs/absent.md", False, "faute"),
            ]
            for rel, present, attendu in cas:
                with self.subTest(rel=rel, workspace_present=present):
                    self.assertEqual(_classer(rel, racines, workspace, present), attendu)
            self.assertTrue(_workspace_present(["atelier/outils/absent.py"], workspace))
            self.assertFalse(_workspace_present(["ailleurs/x.py"], workspace))

    def test_une_racine_de_paquet_ne_compte_pas_pour_un_chemin_mort(self) -> None:
        """La propriete que les deux premiers instruments avaient manquee."""
        self.assertTrue(_atteignable("core/pipeline.py"))          # sous server/src/coproscope
        self.assertTrue(_atteignable("docs/roadmap_backlog_central.md"))
        self.assertTrue(_atteignable("staging/text/quoi_que_ce_soit.txt"))  # instance
        self.assertFalse(_atteignable("docs/ce_fichier_n_existe_pas_du_tout.md"))

    def test_une_declaration_ADJACENTE_est_admise_une_lointaine_non(self) -> None:
        """La propriete qui a manque au premier jet, et que son controle negatif a revelee."""
        self.assertTrue(_declare_l_absence("le document est ABSENT du depot"))
        self.assertTrue(_declare_l_absence("cet outil a ete supprime le 2026-09-02"))
        self.assertFalse(_declare_l_absence("preuve: `docs/quelque_chose.md`, 12 tests verts"))
        # Un mot d'absence a l'autre bout de la ligne ne couvre pas la citation.
        ligne = "les adresses ont ete retirees" + (" x" * 400) + " voir `docs/absent.md` ici"
        debut = ligne.index("`docs/absent.md`")
        self.assertFalse(_declare_l_absence(_voisinage(ligne, debut, debut + 16)))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
