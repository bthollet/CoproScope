# -*- coding: utf-8 -*-
"""Un titre lu en tete corrige le type au POINT D'ENTREE, et le test le mesure la.

`RM-2026-0076`. **Le defaut que l'item nomme - un proces-verbal classe
convocation - est corrige par la chaine, et le seul test qui devait tomber le
jour de la correction mesurait la mauvaise couche.**

----------------------------------------------------------------------
La mesure, faite aux deux couches sur le meme temoin
----------------------------------------------------------------------

Le PV etalon de l'item (`pv_etalon_de_RM_2026_0076`, fabrique, nom
`doc_0002.pdf`) donne le 2026-09-12:

    couche BAREME   (_classify)  : Convocation_AG
    POINT D'ENTREE  (classify)   : PV_AG - "type retenu contre Convocation_AG"

`test_bareme_deplace_le_classement.DefautNommeParRM20260076` promettait: *le
jour ou quelqu'un rend la signature de titre capable de PROMOUVOIR, ce test
tombera*. La promotion existe (`02_classification.py`, branche
`len(titled) == 1`). Le test n'est pas tombe, parce qu'il interrogeait
`_classify` - le bareme seul - et jamais `classify()`. **Sa promesse etait
nulle**, et la cellule de l'item continuait de decrire comme vivant un defaut
que la chaine corrige. C'est la faute que ce depot nomme *mesurer par une
fonction interne au lieu du point d'entree*.

Le bareme, lui, reste faux de deux points sur ce temoin - et c'est vrai, et
garde ailleurs: la marge est la mesure du bareme, la promotion est celle de la
chaine. Ce sont deux proprietes, et chacune a maintenant son test.

----------------------------------------------------------------------
Ce que cette garde mesure, et comment elle ne code pas de modalite
----------------------------------------------------------------------

Les corrections d'un sceptique charge de detruire la proposition, appliquees:

1. **Le motif est une REGEX, pas un litteral.** La tete du temoin n'est donc
   pas fabriquee depuis le motif: le texte est DECLARE a cote de sa cle, et la
   garde verifie d'abord qu'il est reconnu par `title_signature_matches`. Si un
   motif est affine et que le temoin ne matche plus, elle dit *temoin invalide*
   - jamais *promotion non cablee*, qui accuserait un code qui n'a pas bouge.
2. **Le type concurrent se derive de sa PROPRIETE, pas d'une position**: c'est
   le type que le bareme seul rend sur la piece. S'il est deja le type cible,
   le temoin ne mesure plus une promotion, et la garde le dit.
3. **La note qui DISCRIMINE**: le fragment `type retenu contre <concurrent>`,
   propre a la promotion, ET l'absence de `denominations en conflit`. Le
   prefixe `Titre X lu en tete` est commun aux deux branches; une assertion sur
   lui seul passe sur un conflit.
4. **La taxonomie est lue par l'accesseur du produit**, sur l'instance du test:
   la garde boucle sur ce que `classify()` lira, surcharge comprise.

**La portee se derive des motifs declares**: chaque cle de la signature de
titre doit avoir son temoin, et la garde nomme une cle qui n'en a pas.

----------------------------------------------------------------------
Ce qu'elle ne couvre pas, et comment on l'apprendra
----------------------------------------------------------------------

**La branche a DEUX titres ou plus** (`Plusieurs titres reconnus en tete`)
n'est eprouvee nulle part: la taxonomie livree ne declare qu'UN motif, donc elle
est inatteignable avec la configuration reelle. La garde ne la fabrique pas.
**Elle mord le jour ou elle devient atteignable**: si un second motif est
declare, un test echoue en demandant le temoin par PAIRE.

**L'asymetrie inverse reste un residu d'item, pas un defaut de cette garde**:
`Convocation_AG` n'a aucune route par le titre, donc une convocation que le
bareme prendrait pour un PV ne serait pas corrigee.

**Preuve de non-regression, pas de justesse.** Les pieces sont fabriquees et
l'instance est l'exemple synthetique: ceci garde le CABLAGE de la promotion,
pas son taux de faux positifs, qui ne se mesure que sur un corpus reel.
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import (
    DEFAULT_DOCUMENT_FIELDS,
    RunContext,
    load_instance,
    load_structured_file,
    read_csv,
    write_csv,
)
from coproscope.modules.docuscope import (
    CLASSIFICATION_CONTENT_CHARS,
    _classify,
    _named_types,
    _title_head_chars,
    _title_signatures,
    _useful_text_floor,
    classify,
    title_signature_matches,
)
from tests.test_bareme_deplace_le_classement import TEMOINS, regles_de

EXEMPLE = Path(__file__).resolve().parents[2] / "examples" / "synthetic_copro"

#: Un temoin par TYPE dont la signature de titre est declaree. Le texte est
#: repris du temoin de l'item, source unique: deux copies divergeraient.
_ETALON = next(t for t in TEMOINS if t["id"] == "pv_etalon_de_RM_2026_0076")
TEMOINS_DE_TITRE: dict[str, dict[str, str]] = {
    "PV_AG": {"nom": _ETALON["nom"], "chemin": _ETALON["chemin"],
              "contenu": _ETALON["contenu"]},
}

NOTE_DE_PROMOTION = "type retenu contre %s"
NOTE_DE_CONFLIT = "denominations en conflit"


class _Socle(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._dossier = tempfile.TemporaryDirectory()
        racine = Path(cls._dossier.name) / "instance"
        shutil.copytree(EXEMPLE, racine)
        cls.racine = racine
        cls.instance = load_instance(str(racine / "instance.yml"), None)
        # L'accesseur du produit, pas un chemin ecrit ici.
        cls.taxonomie = load_structured_file(cls.instance.classification_rules_path())
        cls.motifs = _title_signatures(cls.taxonomie)
        cls.regles = regles_de(cls.taxonomie)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._dossier.cleanup()

    def _classer(self, doc_id: str, temoin: dict[str, str]) -> dict[str, str]:
        """Le temoin passe par `classify()`, comme une vraie piece."""
        texte = self.racine / "staging" / "text"
        texte.mkdir(parents=True, exist_ok=True)
        (texte / (doc_id + ".txt")).write_text(temoin["contenu"], encoding="utf-8")
        ligne = {champ: "" for champ in DEFAULT_DOCUMENT_FIELDS}
        ligne.update({"doc_id": doc_id, "instance_id": self.instance.instance_id,
                      "file_name": temoin["nom"], "original_path": temoin["chemin"],
                      "text_path": "staging/text/" + doc_id + ".txt"})
        write_csv(self.instance.register("documents"),
                  list(DEFAULT_DOCUMENT_FIELDS), [ligne])
        classify(self.instance, RunContext(self.instance, "garde-titre"), copy_files=False)
        _, lignes = read_csv(self.instance.register("documents"))
        return next(l for l in lignes if l["doc_id"] == doc_id)


class CHAQUE_MOTIF_DE_TITRE_A_SON_TEMOIN(_Socle):

    def test_la_signature_de_titre_est_lue_et_non_vide(self) -> None:
        self.assertTrue(self.motifs, "aucun motif de titre lu: la garde "
                                     "boucle sur le vide")

    def test_chaque_motif_declare_a_un_temoin(self) -> None:
        manquants = sorted(set(self.motifs) - set(TEMOINS_DE_TITRE))
        self.assertEqual([], manquants,
                         "motifs de titre sans temoin: la promotion de ces "
                         "types n'est mesuree par personne: %r" % manquants)

    def test_la_branche_a_PLUSIEURS_titres_devient_atteignable(self) -> None:
        """Le residu qui mord le jour ou il cesse d'etre un residu."""
        self.assertLess(
            len(self.motifs), 2,
            "la taxonomie declare desormais %d motifs de titre: la branche "
            "`Plusieurs titres reconnus en tete` est atteignable et n'est "
            "eprouvee nulle part. Ecrire un temoin par PAIRE de motifs."
            % len(self.motifs))


class LE_TITRE_PROMEUT_AU_POINT_D_ENTREE(_Socle):

    def test_chaque_temoin_est_une_promotion_et_la_chaine_la_fait(self) -> None:
        tete = _title_head_chars(self.taxonomie)
        plancher = _useful_text_floor(self.taxonomie)
        for n, cible in enumerate(sorted(self.motifs)):
            temoin = TEMOINS_DE_TITRE[cible]
            with self.subTest(type=cible):
                # 1. Le temoin est-il reconnu par la signature ? Sinon c'est le
                #    TEMOIN qui est invalide, pas la promotion.
                titres, _ = title_signature_matches(
                    temoin["contenu"], self.motifs, tete, plancher)
                self.assertEqual([cible], titres,
                                 "temoin invalide pour le motif %s: la signature "
                                 "ne le reconnait pas en tete" % cible)
                # 2. Rien dans le nom ni le chemin ne designe un type, sinon on
                #    mesurerait un CONFLIT et non une promotion.
                nommes = _named_types(self.regles, temoin["nom"].lower(),
                                      temoin["chemin"].lower().replace("\\", "/"))
                self.assertEqual(set(), nommes,
                                 "temoin invalide: son nom designe deja %r" % nommes)
                # 3. Le concurrent, par sa PROPRIETE: ce que le bareme seul rend.
                concurrent = _classify(temoin["contenu"][:CLASSIFICATION_CONTENT_CHARS],
                                       temoin["nom"], temoin["chemin"], self.regles)[1]
                self.assertNotEqual(
                    cible, concurrent,
                    "le bareme seul rend deja %s: ce temoin ne mesure plus une "
                    "promotion. Choisir une piece que le bareme classe autrement."
                    % cible)
                # 4. Le point d'entree.
                ligne = self._classer("DOC-TITRE-%d" % n, temoin)
                self.assertEqual(
                    cible, ligne["document_type"],
                    "le bareme rend %s, le titre %s est lu en tete, rien d'autre "
                    "ne nomme la piece - et classify() ne promeut pas"
                    % (concurrent, cible))
                self.assertIn(NOTE_DE_PROMOTION % concurrent, ligne["notes"],
                              "la promotion n'est pas ecrite avec son concurrent")
                self.assertNotIn(NOTE_DE_CONFLIT, ligne["notes"],
                                 "la chaine a vu un CONFLIT la ou rien ne "
                                 "nommait la piece")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
