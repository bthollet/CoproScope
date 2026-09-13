# -*- coding: utf-8 -*-
"""Une reference doit etre immuable pendant qu'on mesure contre elle.

`RM-2026-0107`. Le fait observe: **trois fichiers SUIVIS de
`examples/synthetic_copro` ont ete trouves modifies** dans l'arbre partage -
un document y basculant de `C1_Occupants_Usagers / raw / none` a
`C4_Conseil_Syndical / redaction_required / RGPD;vie_privee`. **Ni le
signaleur ni le lecteur suivant ne reproduisaient la mutation**, et c'est ce
qui a fait poser la garde qui MANQUE plutot que de chasser le coupable: *la
nuit a montre que le coupable peut ne pas etre reproductible*.

**CETTE GARDE-CI N'EST PAS L'EMPREINTE.**
`test_fixtures_versionnees_immuables` constate qu'un fichier a change - **apres
coup**. Celle-ci ferme le chemin par lequel il peut changer: **un test qui
construit une instance SUR le chemin versionne** met la reference a portee de
tout code de production qui ecrit.

**LE COROLLAIRE DE L'ITEM, ET SON COMPTE A BOUGE.** Il annoncait *les 5
fichiers de test qui la lisent sans la copier*. Mesure du 2026-09-12, et le
chiffre depend entierement du critere, donc le critere est publie avec:

- **11** fichiers **citent** `synthetic_copro` sans copier - mais citer n'est
  pas lire: l'un est cette empreinte elle-meme, un autre verifie l'absence de
  chemins absolus dans les exemples, un troisieme n'en parle que dans un
  commentaire sur les limites de la CI;
- **3** fichiers **construisent une instance sur ce chemin**, ce qui est le
  seul geste par lequel du code de production peut y ecrire;
- **1** de plus lit sans copier et appelle une fonction d'ecriture.

**Le compte qui compte est donc 3**, et c'est lui que ce test borne.

**L'AXE.** Ce qui VARIE: le test, ce qu'il mesure, la fonction qu'il appelle.
Ce qui reste INVARIANT: **une reference contre laquelle on mesure ne se laisse
pas ecrire**. La garde porte sur le GESTE - construire une instance sur ce
chemin - et non sur une liste de fonctions dangereuses, qui serait une
enumeration de modalites.

**LE RESIDU DES TROIS EST FERME, LE 2026-09-12.** Ce paragraphe disait *elle ne
convertit pas les trois en copies*, et c'etait vrai jusqu'a ce jour-la. Les
trois passent desormais par `tests/_exemple_copie.py`. La question du residu
etait la bonne - *basculer sur une copie demande de verifier que la mesure garde
son sens* - et elle a une reponse: **aucune des trois proprietes mesurees ne
depend du CHEMIN**, elles dependent du CONTENU, que `copytree` reproduit a
l'octet.

**CE QU'ELLE NE FAIT TOUJOURS PAS.** Elle ne dit pas que la reference est a
l'abri de tout: elle dit qu'aucun TEST ne l'ouvre. Le fait observe le
2026-09-07 n'a jamais ete reproduit ni explique, et cette garde ne pretend pas
l'avoir ferme.

**ET ELLE A ETE FAIBLE PENDANT UNE HEURE, ce qui vaut d'etre ecrit.** Ses deux
motifs s'appliquaient au fichier ENTIER: ecrire `copytree` dans un commentaire
suffisait a immuniser un test qui ouvrait l'instance sur place. La conversion
de `test_identite_coque` a ajoute un tel commentaire, et la campagne de
mutation a montre que **defaire la conversion ne faisait plus rougir la
garde**. Les motifs tournent maintenant sur le CODE SEUL - docstrings et
commentaires retires - et deux temoins gardent le trou ferme.
"""
from __future__ import annotations

import ast
import re
import unittest
import warnings
from pathlib import Path

#: Un commentaire commence a un `#` qui n'est pas dans une chaine. Le motif est
#: volontairement grossier: il tourne sur du code DEJA prive de ses docstrings,
#: et un `#` dans une chaine courte ne fait que retirer un peu de texte qui
#: n'etait ni un appel ni un chemin.
_COMMENTAIRE = re.compile(r"(?m)#[^\n]*$")

TESTS = Path(__file__).resolve().parent

#: Construire une instance SUR un chemin d'exemple. C'est le geste, pas le
#: nom du fichier: `load_instance` comme `InstanceConfig` mettent la reference
#: a portee d'ecriture.
SUR_PLACE = re.compile(
    r"(?:load_instance|InstanceConfig)\s*\([^)]*"
    r"(?:synthetic_copro|EXEMPLE|EXAMPLE|FIXTURE)", re.S)

#: Ce qui met une instance a l'abri: une copie, un dossier temporaire, ou
#: l'instance de lot du depot.
A_L_ABRI = re.compile(
    r"copytree|shutil\.copy|TemporaryDirectory|mkdtemp|tmp_path"
    r"|instance_de_lot|corpus_portant")

#: **DETTE VIDEE LE 2026-09-12, et c'etait le reste nomme de `RM-2026-0107`.**
#: Les trois fichiers qui ouvraient encore l'instance versionnee sur place -
#: `test_aucune_piece_n_est_inventee_quand_il_n_y_a_rien`,
#: `test_identite_coque`, `test_identite_ecran_source` - passent par
#: `tests/_exemple_copie.py`.
#:
#: **La question que le residu posait etait la bonne, et elle a une reponse.**
#: Chacun des trois mesure quelque chose de l'instance reelle - son nom
#: d'affichage, son identifiant declare, les ecrans qu'elle sert - et il
#: fallait verifier que la mesure garde son sens sur une copie. Elle le garde,
#: pour une raison precise: **aucune des trois proprietes ne depend du CHEMIN,
#: elles dependent du CONTENU**, que `copytree` reproduit a l'octet. Ce qui
#: aurait change de sens serait une mesure portant sur l'emplacement lui-meme;
#: aucune des trois n'en fait.
#:
#: **Ce que la dette vide ne veut PAS dire.** Elle ne dit pas que la reference
#: est desormais a l'abri de tout: elle dit qu'aucun TEST ne l'ouvre. Le fait
#: observe le 2026-09-07 - trois fichiers suivis trouves modifies - n'a jamais
#: ete reproduit ni explique, et cette garde ne pretend pas l'avoir ferme. Elle
#: ferme le GESTE par lequel un test pouvait le produire.
#:
#: Une entree ajoutee ici doit dire **pourquoi la copie changerait le sens de
#: la mesure**. Sans cette raison, ce n'est pas une dette, c'est un
#: contournement.
DETTE_2026_09_12: frozenset[str] = frozenset()


def code_seul(texte: str) -> str:
    """Le fichier prive de ses COMMENTAIRES et de ses DOCSTRINGS.

    **Le trou que cela ferme, trouve par la campagne de mutation du
    2026-09-12.** Les deux motifs etaient appliques au fichier ENTIER. Ecrire le
    mot `copytree` dans un commentaire suffisait donc a immuniser un test qui
    ouvrait l'instance sur place - et c'est exactement ce qui est arrive: la
    conversion de `test_identite_coque` a ajoute un commentaire expliquant que
    *`copytree` reproduit le contenu a l'octet*, et defaire la conversion ne
    faisait plus rougir la garde. Une garde qui se desarme par une phrase de
    prose mesure le vocabulaire du fichier, pas son GESTE - ce que son propre
    en-tete pretendait pourtant faire.

    Les docstrings partent pour la raison symetrique: un module qui DECRIT le
    defaut - celui-ci, par exemple - ne le commet pas.
    """
    try:
        # Analyser une source qui porte une sequence d'echappement douteuse -
        # `\d` dans une chaine non brute - fait emettre un `SyntaxWarning` par
        # le fichier ANALYSE, pas par celui-ci. Le laisser sortir salirait le
        # journal de la suite avec un avertissement dont l'origine est
        # incomprehensible: `<unknown>:500`.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            arbre = ast.parse(texte)
    except SyntaxError:
        return texte
    lignes = texte.splitlines(keepends=True)
    a_blanchir: list[tuple[int, int]] = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                  ast.AsyncFunctionDef)):
            continue
        corps = getattr(noeud, "body", None) or []
        if not corps:
            continue
        premier = corps[0]
        if (isinstance(premier, ast.Expr)
                and isinstance(premier.value, ast.Constant)
                and isinstance(premier.value.value, str)):
            a_blanchir.append((premier.lineno, premier.end_lineno or premier.lineno))
    for debut, fin in a_blanchir:
        for numero in range(debut, fin + 1):
            if 1 <= numero <= len(lignes):
                lignes[numero - 1] = "\n"
    sans_docstring = "".join(lignes)
    return _COMMENTAIRE.sub("", sans_docstring)


def ouvre_sur_place(source: str) -> bool:
    """La decision, pour UN fichier, extraite pour etre eprouvable.

    Sans cette extraction, l'instrument ne pouvait etre eprouve que par des
    fichiers reels - donc pas du tout sur les cas qui n'existent pas encore.
    """
    texte = code_seul(source)
    if "synthetic_copro" not in texte:
        return False
    if A_L_ABRI.search(texte):
        return False
    return bool(SUR_PLACE.search(texte))


def _sur_place() -> set[str]:
    return {
        chemin.name for chemin in sorted(TESTS.glob("test_*.py"))
        if ouvre_sur_place(chemin.read_text(encoding="utf-8", errors="replace"))
    }


class AUCUN_TEST_NEUF_N_OUVRE_L_INSTANCE_VERSIONNEE(unittest.TestCase):
    def test_l_instrument_lit_bien_les_tests(self) -> None:
        """Sans lecture, le compte ci-dessous serait vide et vert."""
        fichiers = list(TESTS.glob("test_*.py"))
        self.assertGreater(len(fichiers), 100)
        citants = [
            c for c in fichiers
            if "synthetic_copro" in c.read_text(encoding="utf-8", errors="replace")
        ]
        self.assertGreater(
            len(citants), 50,
            "presque aucun test ne cite l'instance d'exemple: le balayage est "
            "casse, et l'absence de nouveau contrevenant ne prouverait rien")

    def test_aucun_contrevenant_NEUF(self) -> None:
        neufs = sorted(_sur_place() - DETTE_2026_09_12)
        self.assertEqual(
            [], neufs,
            "ce test construit une instance SUR `examples/synthetic_copro`, "
            "donc il met la reference a portee de tout code de production qui "
            "ecrit - et trois fichiers suivis ont deja ete trouves modifies "
            "de cette facon, sans que personne reproduise la mutation. "
            "Travailler sur une COPIE: `tests/_instance_de_lot.py` ou un "
            "dossier temporaire. Contrevenants: %s" % neufs)

    def test_RESIDU_la_dette_est_bornee_et_se_redit_quand_elle_baisse(self) -> None:
        self.assertEqual(
            DETTE_2026_09_12, _sur_place(),
            "la dette a change. Si elle a MONTE, un test ouvre l'instance "
            "versionnee sur place: le faire passer par "
            "`tests/_exemple_copie.py`, ou declarer ici POURQUOI la copie "
            "changerait le sens de sa mesure - sans cette raison ce n'est pas "
            "une dette, c'est un contournement. Si elle a BAISSE, retirer "
            "l'entree et le dire au gouvernail.")

    def test_l_instrument_RECONNAIT_un_cas_dont_la_reponse_est_connue(self) -> None:
        """La sonde qui manquait, et son absence a failli passer inapercue.

        **Mutation 5 du 2026-09-12: casser le motif de detection rendait la
        garde VERTE.** La dette devient vide, l'egalite `frozenset() ==
        frozenset()` tient, et plus rien ne mesure - c'est la forme exacte du
        `0/7` que le `CLAUDE.md` nomme: *un zero uniforme est un symptome
        d'instrument, pas un resultat; avant de le publier, faire passer a
        l'instrument un cas dont la reponse est connue.*

        Les trois cas sont ceux qui distinguent le geste du nom: un chargement
        sur le chemin versionne, le meme sur une copie, et une simple mention
        en prose.
        """
        sur_place = (
            "from coproscope.core.common import load_instance\n"
            "def charge():\n"
            "    return load_instance(None, 'examples/synthetic_copro')\n"
        )
        self.assertTrue(
            ouvre_sur_place(sur_place),
            "l'instrument ne reconnait plus un chargement sur le chemin "
            "versionne: la dette vide ne prouve alors plus rien")

        sur_copie = (
            "import shutil\n"
            "from tempfile import TemporaryDirectory\n"
            "from coproscope.core.common import load_instance\n"
            "def charge():\n"
            "    with TemporaryDirectory() as d:\n"
            "        shutil.copytree('examples/synthetic_copro', d + '/x')\n"
            "        return load_instance(None, d + '/x')\n"
        )
        self.assertFalse(
            ouvre_sur_place(sur_copie),
            "l'instrument accuse un test qui travaille sur une COPIE: il "
            "mesure le nom de l'instance et non le geste")

        prose_seule = (
            '"""Ce module parle de examples/synthetic_copro et de copytree."""\n'
            "def charge():\n"
            "    return None\n"
        )
        self.assertFalse(
            ouvre_sur_place(prose_seule),
            "une simple mention en prose suffit a declencher la mesure")

    def test_une_PHRASE_ne_desarme_pas_la_garde(self) -> None:
        """Le trou que la mutation 4 a ouvert, garde comme temoin.

        Ecrire `copytree` dans un commentaire immunisait un fichier qui ouvrait
        l'instance sur place. Une garde qui se desarme par une phrase de prose
        mesure le vocabulaire du fichier, pas son geste.
        """
        avec_alibi = (
            "from coproscope.core.common import load_instance\n"
            "# On pourrait utiliser copytree et TemporaryDirectory ici.\n"
            "def charge():\n"
            "    return load_instance(None, 'examples/synthetic_copro')\n"
        )
        self.assertTrue(
            ouvre_sur_place(avec_alibi),
            "un commentaire citant `copytree` desarme la garde: elle est "
            "redevenue une mesure de vocabulaire")

    def test_le_moyen_de_s_en_passer_EXISTE_et_est_utilise(self) -> None:
        """Une garde qui interdit sans offrir d'issue se fait contourner.

        Ce test verifie que l'issue existe et qu'elle est REELLEMENT prise, au
        lieu de supposer que l'interdiction suffit. Sans lui, la dette vide
        pourrait aussi bien signifier *plus personne ne mesure sur l'exemple*,
        ce qui serait une perte et non un progres.
        """
        moyen = TESTS / "_exemple_copie.py"
        self.assertTrue(moyen.is_file(), "%s a disparu" % moyen.name)
        preneurs = sorted(
            chemin.name for chemin in TESTS.glob("test_*.py")
            if "_exemple_copie" in chemin.read_text(encoding="utf-8",
                                                    errors="replace")
        )
        self.assertGreaterEqual(
            len(preneurs), 3,
            "moins de trois tests passent par la copie de l'exemple: soit la "
            "conversion a ete defaite, soit la mesure sur l'exemple a "
            "disparu - et les deux se corrigent differemment. Preneurs: %s"
            % preneurs)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
