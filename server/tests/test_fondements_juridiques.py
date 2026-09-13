# -*- coding: utf-8 -*-
"""Un identifiant Legifrance cite dans le code est declare, avec sa date de version.

Consigne de Brice du 2026-09-08: *garder trace des identifiants Legifrance qui
fondent des choix de code*.

**Pourquoi la date de version fait partie de la citation, et pas seulement
l'identifiant.** Mesure inscrite dans la skill `piste-api`: le meme article
existe en plusieurs versions successives, et **toutes portent `VIGUEUR`** - en
vigueur *a leur date*. Le statut ne dit donc jamais si l'on regarde le bon
texte. Trois versions distinctes de l'article 25 de la loi de 1965 ont ete lues,
de longueurs differentes, toutes `VIGUEUR`. Un identifiant sans date de version
n'est pas une citation, c'est une reference.

**Ce que ce test verifie, et ce qu'il ne verifie pas.** Il verifie qu'aucun
identifiant n'apparait dans le code sans etre declare quelque part. Il ne
verifie PAS que la citation est juste - cela demande d'interroger Legifrance, ce
qui n'a pas sa place dans une suite hors ligne, et c'est l'objet du cache
reglementaire versionne demande par Brice le meme jour.

**L'axe:** le code ne cite pas un texte, il cite une CLE d'un registre; le
registre cite le texte, avec sa version et la date a laquelle elle a ete lue.
Le test balaie tout `server/src` - il ne connait aucune liste de fichiers, donc
un module cree demain est couvert le jour de sa creation.

------------------------------------------------------------------------------
REVISITE LE 2026-09-12 SOUS `RM-2026-0132`, ET LE CHEMIN CODE EN DUR ETAIT UNE
MODALITE
------------------------------------------------------------------------------

Ce test designait **un** registre par son chemin: `_budget_previsionnel_sources`.
Or le depot en porte **deux**. `_extranet_referentiel` declare son propre
`Source`, son propre `SOURCES` et son propre `source()`, avec un espace de cles
qui emploie les memes prefixes - `loi.*`, `d67.*`.

**Consequence mesuree, et elle porte sur le compte lui-meme:** cinq des
vingt-quatre identifiants inscrits dans la dette n'ont jamais ete une dette. Ils
etaient declares, avec leur version ET leur date de lecture, dans le registre
que ce test ne lisait pas. La dette reelle est de **dix-neuf**. Elle n'a pas
diminue par du travail: elle a diminue parce qu'on a regarde au bon endroit,
et c'est la difference qu'il faut dire.

**Ce que la double declaration coute vraiment, et c'est la raison de Brice.**
L'item demande de savoir, quand un texte change, quels choix de code en
dependent. `LEGIARTI000049398867` - article 18 de la loi de 1965 - est declare
**dans les deux registres**, sous deux cles differentes, `loi.18` et
`loi.18-I`. Un mainteneur qui met a jour l'un n'a aujourd'hui aucun moyen
d'apprendre que l'autre depend du meme article. Les deux portent la meme
version, `2024-04-11`: rien n'est faux aujourd'hui, et **c'est exactement
pourquoi le defaut est silencieux**.

**L'AXE, et il n'est pas le domaine.** Ce qui VARIE: le domaine du controle -
budget, extranet, et demain autre chose - donc le nombre de registres. Ce qui
reste INVARIANT: **un identifiant Legifrance a une seule version lue, et
l'ensemble des choix qui en dependent est une seule liste.** Le domaine est un
axe d'EMPLOI, jamais un axe de DECLARATION.

**Ce que le code en fait:** les registres se decouvrent par leur FORME - un
module qui expose un `SOURCES: dict[str, Source]` - et non par un chemin.
**Hors des valeurs observees:** un troisieme registre ecrit demain est lu le
jour de sa creation, sans toucher a ce fichier.

**RESIDU NOMME, et il est le plus gros.** L'item `RM-2026-0132` demande deux
choses: rattacher un choix a son fondement, **ou dire explicitement qu'il n'en
a pas et qu'il repose sur une observation**. Seule la premiere moitie existe.
Une mesure du 2026-09-12: **12 modules** admettent en prose reposer sur une
modalite observee - `usage de cabinet`, `modalite observee`, `habitude d'un
cabinet` - et **aucun ne le declare**. Le premier compte ecrit ici disait
trente: c'etait le nombre de LIGNES trouvees, pas de modules, et deux
modules sur trois y figuraient plusieurs fois. Il n'existe aucun vocabulaire pour cela:
le depot sait citer un article, il ne sait pas citer une observation. Ecrire ce
second versant est un travail de jugement module par module, pas un balayage;
il n'est pas fait ici, et le compte ci-dessus est ce qui le borne.

**Divergence constatee et NON gardee:** les deux registres nomment la date de
lecture differemment - `lu_le` et `lue_le`. Le test exige qu'une date de lecture
existe, sans imposer son orthographe: garder l'une des deux graphies
entérinerait le choix d'un registre contre l'autre sans qu'aucune mesure ne le
justifie.
"""
from __future__ import annotations

import importlib
import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "src"
IDENTIFIANT = re.compile(r"LEGI(?:ARTI|TEXT)\d{12}")

#: La forme d'un registre, et c'est elle qui sert a le trouver - pas son nom de
#: fichier. Un module qui expose cette annotation declare des sources legales.
FORME_DE_REGISTRE = "SOURCES: dict[str, Source]"

#: Les identifiants qui vivent encore en litteraux hors de tout registre, au
#: 2026-09-12. **Ce n'est pas une liste d'exceptions tolerees: c'est une dette,
#: mesuree et bornee.** Elle ne doit jamais grandir; elle a vocation a etre
#: videe en migrant ces modules vers un registre. Un identifiant NEUF hors
#: registre fait echouer le test, ce qui est exactement la consigne demandee.
#:
#: Elle valait 24 au 2026-09-08. Cinq entrees en sont sorties le 2026-09-12
#: sans qu'aucun code ne bouge: elles etaient declarees dans le registre
#: `_extranet_referentiel`, que ce test ne lisait pas.
DETTE_2026_09_12 = frozenset({
    "LEGIARTI000006488509",   # modules/_actes_typologie.py
    "LEGIARTI000006488770",   # modules/_actes_typologie.py
    "LEGIARTI000022124075",   # modules/_actes_typologie.py
    "LEGIARTI000039301559",   # modules/_actes_typologie.py
    "LEGIARTI000039301561",   # modules/_actes_typologie.py
    "LEGIARTI000039301563",   # modules/_actes_typologie.py
    "LEGIARTI000039301567",   # modules/_actes_typologie.py
    "LEGIARTI000039313531",   # modules/_decompte_voix_regimes.py
    "LEGIARTI000039313574",   # modules/_actes_typologie.py
    "LEGIARTI000039313644",   # modules/_decompte_voix_regimes.py
    "LEGIARTI000042076720",   # modules/_decompte_voix_regimes.py
    "LEGIARTI000042076794",   # modules/_resolutions_cloture.py
    "LEGIARTI000042078670",   # modules/_decompte_voix_regimes.py
    "LEGIARTI000042078689",   # modules/_decompte_voix_regimes.py
    "LEGIARTI000043977284",   # modules/_decompte_voix_regimes.py
    "LEGIARTI000049398359",   # modules/_actes_typologie.py
    "LEGIARTI000050623612",   # modules/_decompte_voix_regimes.py
    "LEGIARTI000051749507",   # modules/_actes_typologie.py
    "LEGIARTI000053191360",   # modules/_actes_typologie.py
})


def _modules_de_registre() -> list[str]:
    """Les registres, trouves par leur FORME et jamais par leur chemin."""
    trouves = []
    for chemin in sorted(RACINE.rglob("*.py")):
        if "__pycache__" in chemin.parts:
            continue
        if FORME_DE_REGISTRE in chemin.read_text(encoding="utf-8", errors="replace"):
            relatif = chemin.relative_to(RACINE).with_suffix("")
            trouves.append(".".join(relatif.parts))
    return trouves


def _declarations() -> dict[str, list[tuple[str, str, str]]]:
    """L'index inverse: un identifiant -> (module, cle, version) qui en dependent.

    C'est la reponse a la question de l'item: *quand un texte change, quels
    choix de code en dependent ?* On importe les registres au lieu de les lire
    au motif - un motif se trompe sur les arguments positionnels, un import lit
    les objets reels.
    """
    index: dict[str, list[tuple[str, str, str]]] = {}
    for nom in _modules_de_registre():
        module = importlib.import_module(nom)
        for cle, declaration in getattr(module, "SOURCES").items():
            index.setdefault(declaration.legiarti, []).append(
                (nom, cle, declaration.version_debut))
    return index


def _identifiants_du_code() -> dict[str, list[str]]:
    """Tout identifiant cite dans une source Python, avec ses fichiers."""
    trouves: dict[str, list[str]] = {}
    for chemin in RACINE.rglob("*.py"):
        if "__pycache__" in chemin.parts:
            continue
        texte = chemin.read_text(encoding="utf-8", errors="replace")
        for ident in set(IDENTIFIANT.findall(texte)):
            trouves.setdefault(ident, []).append(str(chemin.relative_to(RACINE)))
    return trouves


class FondementsJuridiques(unittest.TestCase):
    def test_la_collecte_trouve_bien_des_identifiants(self):
        """Garde de l'instrument: un balayage casse rendrait les autres tests vides."""
        self.assertGreater(len(_identifiants_du_code()), 30,
                           "le balayage ne trouve presque rien: il est casse, pas le code")

    def test_les_registres_se_trouvent_par_leur_forme(self):
        """Garde de l'instrument: le jour ou la decouverte casse, la dette

        se remettrait a grandir en silence - tous les identifiants declares
        redeviendraient `neufs`. Le compte attendu n'est pas fige a deux: il
        doit seulement rester non vide et contenir les registres connus.
        """
        noms = _modules_de_registre()
        self.assertGreaterEqual(
            len(noms), 2,
            "la decouverte par forme ne trouve plus les registres connus: %s" % noms)
        self.assertIn("coproscope.modules._budget_previsionnel_sources", noms)
        self.assertIn("coproscope.modules._extranet_referentiel", noms)

    def test_aucun_identifiant_neuf_hors_registre(self):
        """La consigne, appliquee: un identifiant nouveau se declare.

        Le message d'echec nomme l'identifiant ET son fichier, pour que le
        developpeur sache quoi faire sans relire ce test.
        """
        declares = set(_declarations())
        neufs = {}
        for ident, fichiers in sorted(_identifiants_du_code().items()):
            if ident in declares or ident in DETTE_2026_09_12:
                continue
            neufs[ident] = fichiers
        self.assertEqual(
            {}, neufs,
            "identifiant(s) Legifrance cite(s) sans declaration: %s. "
            "Declare-le dans un registre avec sa date de version ET la date a "
            "laquelle tu l'as lu. Un identifiant sans date de version n'est pas "
            "une citation: le meme article a plusieurs versions, toutes marquees VIGUEUR."
            % ", ".join("%s (%s)" % (k, ", ".join(v)) for k, v in neufs.items()),
        )

    def test_chaque_source_declaree_porte_sa_version_et_sa_date_de_lecture(self):
        """Conservation: une declaration incomplete ne vaut pas mieux qu'une absence.

        La date de lecture est exigee sans imposer son orthographe: les deux
        registres la nomment differemment, et trancher ici entérinerait un
        registre contre l'autre sans mesure pour le justifier.
        """
        vus = 0
        for nom in _modules_de_registre():
            module = importlib.import_module(nom)
            for cle, declaration in getattr(module, "SOURCES").items():
                vus += 1
                with self.subTest(registre=nom, cle=cle):
                    self.assertRegex(
                        declaration.version_debut, r"^\d{4}-\d{2}-\d{2}$",
                        "cette declaration ne porte pas de date de version")
                    lectures = [v for c, v in vars(declaration).items()
                                if c.startswith("lu") and re.match(r"^\d{4}-\d{2}-\d{2}$", str(v))]
                    self.assertTrue(
                        lectures,
                        "cette declaration ne dit pas quand sa version a ete lue")
        self.assertGreater(vus, 20, "les registres ne rendent presque rien: format change")

    def test_un_article_declare_deux_fois_porte_la_meme_version(self):
        """La raison de Brice, rendue executable.

        Un identifiant declare dans plusieurs registres vit sous plusieurs
        cles. Rien n'est faux tant que les versions concordent - et c'est
        precisement pourquoi la divergence serait silencieuse: chaque registre
        resterait juste de son cote pendant que deux parties du produit
        raisonneraient sur deux etats du meme article.

        Le message d'echec EST l'index inverse que l'item demande: il nomme le
        texte, et tous les choix de code qui en dependent.
        """
        for ident, portes in sorted(_declarations().items()):
            versions = {version for _, _, version in portes}
            with self.subTest(legiarti=ident):
                self.assertEqual(
                    1, len(versions),
                    "%s est declare a %d versions differentes. Les choix qui en "
                    "dependent: %s" % (
                        ident, len(versions),
                        " ; ".join("%s[%s] version %s" % p for p in portes)),
                )

    def test_RESIDU_la_dette_est_bornee_et_ne_grandit_pas(self):
        """Le residu, rendu executable plutot qu'ecrit dans un document.

        19 identifiants vivent encore en litteraux dans trois modules. Ce test
        echoue si l'un d'eux disparait du code sans etre retire d'ici - donc la
        dette se solde en deux gestes, pas en un oubli - et il fixe le compte.
        """
        cites = set(_identifiants_du_code())
        self.assertEqual(19, len(DETTE_2026_09_12),
                         "le compte de la dette a change sans etre redit")
        fantomes = sorted(DETTE_2026_09_12 - cites)
        self.assertEqual(
            [], fantomes,
            "ces identifiants ne sont plus dans le code: retire-les de DETTE_2026_09_12, "
            "la dette a diminue et le test doit le dire: %s" % ", ".join(fantomes),
        )


if __name__ == "__main__":
    unittest.main()
