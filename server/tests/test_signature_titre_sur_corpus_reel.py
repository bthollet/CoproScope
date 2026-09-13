# -*- coding: utf-8 -*-
"""Le titre d'un proces-verbal ne se reconnait sur rien d'autre - mesure.

**Ce que `RM-2026-0056` reclamait, dans ses propres mots:** *« le chiffrage de
la colonne preuve - 5 vrais positifs, 0 faux positif sur 37 documents et deux
cabinets - n'est porte par aucun test: les positions sont des fixtures ecrites a
la main et les chiffres vivent en commentaires. C'est une phrase, pas un residu
executable, et c'est pour cela que la ligne reste ACTIF. Prochaine action:
rendre ce chiffrage executable. »* Ce module est cette action.

**Ce qui est epingle, et ce qui ne l'est pas.** L'invariant est *aucun document
qui n'est pas un proces-verbal ne porte le titre d'un proces-verbal en tete*.
Il ne depend d'aucun corpus, donc il s'epingle. Les nombres absolus, eux,
dependent du corpus present sur le poste: ils sont MESURES et ecrits au journal,
jamais figes - une preuve qui fige `9` meurt le jour ou l'on absorbe une piece
de plus, et le depot a deja paye ce defaut.

**Mesure du 2026-09-10. Le poste porte TROIS corpus, pas deux, et la garde
les mesure tous plutot que d'en elire un:**

| corpus                  | documents | titre reconnu sur un PV | faux positif | PV sans titre |
|-------------------------|----------:|------------------------:|-------------:|--------------:|
| second cabinet          |        22 |                       2 |            0 |             0 |
| etalon etabli a la main |        29 |                       2 |            0 |             0 |
| corpus de travail       |       858 |                       7 |            0 |             3 |
| **total**               |   **909** |                  **11** |        **0** |         **3** |

Le chiffrage de l'item annonçait *5 vrais positifs, 0 faux positif sur 37
documents et deux cabinets*; la mesure executable en donne **11 sur 909**, avec
**zero faux positif** - vingt-cinq fois plus de matiere, meme invariant.

**Un fait que l'item n'avait pas, et qui n'est PAS un echec de la signature:**
trois documents typés `PV_AG` ne portent pas ce titre dans leur tete. La
signature les envoie a la relecture, ce qui est son travail; savoir s'ils sont
mal typés ou si leur titre est ailleurs demande de les ouvrir, et ce n'est pas
la question de ce module.

**Ce corpus est prive, et la garde le declare au lieu de mentir.** Sur une
machine qui ne le porte pas - la CI, par construction - la mesure ne se fait
pas et le dit: un `OK (skipped=N)` qui ne nomme pas ce qui n'a pas ete mesure
est le defaut que `RM-2026-0150` a corrige.
"""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

from coproscope.modules.docuscope import (
    DEFAULT_TITLE_HEAD_CHARS,
    DEFAULT_TITLE_SIGNATURES,
    DEFAULT_USEFUL_TEXT_FLOOR,
    title_signature_verdict,
)
from tests._instance_de_lot import instances_portant

#: Les deux pieces que la mesure va REELLEMENT chercher - c'est ce qui
#: identifie une instance utilisable, pas son nom.
_REGISTRE = "registers/registre_documents.csv"
_TEXTES = "staging/text/*.txt"

#: Le type dont la signature de titre repond, et le seul.
_TYPE_CIBLE = "PV_AG"

#: Verdict rendu quand le titre est bien en tete. La chaine vide est le
#: `pas de doute` de `title_signature_verdict`; elle est nommee ici pour qu'on
#: ne la lise pas comme un oubli.
_TITRE_RECONNU = ""


#: Assez d'octets pour trancher, et pas un de plus.
#:
#: `title_signature_verdict` cherche le titre dans les 300 premiers caracteres
#: et exige 200 caracteres utiles pour ne pas repondre `TEXTE_INSUFFISANT`.
#: Huit kilo-octets couvrent les deux largement. **Et la troncature ne peut
#: changer aucun des trois comptes:** le titre reconnu se decide dans la tete,
#: donc `vrais` est identique; et `TEXTE_INSUFFISANT` comme `A_RECLASSER`
#: tombent tous deux dans `sans_titre`, donc basculer de l'un a l'autre ne
#: deplace rien. Lire les fichiers en entier coutait **275 secondes** a la
#: suite, pour le meme resultat.
_OCTETS_LUS = 8192

#: La mesure, faite UNE fois pour le module. Deux classes de test la lisent, et
#: `setUpClass` tourne une fois par classe: sans ce cache, tout etait mesure
#: deux fois - visible au journal, qui imprimait deux fois les memes lignes.
_CACHE: dict[str, object] = {}


class _Mesure(unittest.TestCase):
    """Compte, sur toutes les instances portant le corpus, sans en elire une.

    **On ne DESIGNE pas une instance ici, et c'est voulu.** La question de
    l'item porte sur *deux cabinets*: elire l'une des deux rendrait un chiffre
    qui ne repond pas a la question posee. Toutes les candidates sont donc
    mesurees, et chacune est nommee au journal.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.motif = DEFAULT_TITLE_SIGNATURES[_TYPE_CIBLE]
        if "corpus" in _CACHE:
            cls.corpus = _CACHE["corpus"]
            cls.resultats = _CACHE["resultats"]
            return
        cls.corpus = instances_portant(_REGISTRE, _TEXTES)
        cls.resultats = [cls._mesurer(racine) for racine in cls.corpus]
        _CACHE["corpus"] = cls.corpus
        _CACHE["resultats"] = cls.resultats
        for r in cls.resultats:
            print(
                "[base] signature de titre: %s | %s documents | %s reconnus | "
                "%s faux positifs | %s PV sans titre"
                % (r["nom"], r["documents"], r["vrais"], r["faux"], r["sans_titre"]),
                file=sys.stderr,
            )

    @classmethod
    def _mesurer(cls, racine: Path) -> dict[str, object]:
        chemin = racine / _REGISTRE
        with chemin.open(encoding="utf-8-sig", newline="") as flux:
            lignes = list(csv.DictReader(flux))
        vrais = faux = sans_titre = examines = 0
        for ligne in lignes:
            piece = racine / str(ligne.get("text_path") or "")
            if not piece.is_file():
                continue
            examines += 1
            with piece.open(encoding="utf-8", errors="ignore") as flux:
                texte = flux.read(_OCTETS_LUS)
            verdict = title_signature_verdict(
                texte, cls.motif, DEFAULT_TITLE_HEAD_CHARS, DEFAULT_USEFUL_TEXT_FLOOR
            )
            est_cible = str(ligne.get("document_type") or "") == _TYPE_CIBLE
            if verdict == _TITRE_RECONNU and est_cible:
                vrais += 1
            elif verdict == _TITRE_RECONNU:
                faux += 1
            elif est_cible:
                sans_titre += 1
        # Le nom du dossier, jamais son contenu: aucune donnee de copropriete
        # ne sort d'ici, ni patronyme, ni libelle de piece.
        return {"nom": racine.name, "documents": examines, "vrais": vrais,
                "faux": faux, "sans_titre": sans_titre}

    def _exige_un_corpus(self) -> None:
        if not self.corpus:
            self.skipTest(
                "MESURE NON FAITE: aucune instance ne porte a la fois `%s` et `%s`. "
                "Ce qui n'est donc PAS verifie ici: qu'aucun document autre qu'un "
                "proces-verbal ne porte le titre d'un proces-verbal en tete, sur "
                "corpus reel. Pour le mesurer, absorber un corpus dans une instance "
                "portant ces pieces." % (_REGISTRE, _TEXTES)
            )


class AucuneAutrePieceNePorteLeTitreDUnProcesVerbal(_Mesure):
    """L'invariant. Il ne depend d'aucun corpus, donc il s'epingle."""

    def test_ZERO_FAUX_POSITIF_SUR_TOUT_CE_QUI_EST_PRESENT(self) -> None:
        self._exige_un_corpus()
        coupables = [r for r in self.resultats if r["faux"]]
        self.assertEqual(
            [], coupables,
            "un document qui n'est pas un proces-verbal porte le titre d'un "
            "proces-verbal en tete: la signature n'ancre plus rien",
        )

    def test_la_mesure_a_bien_examine_quelque_chose(self) -> None:
        """Anti-vacuite: zero faux positif sur zero document ne prouve rien."""
        self._exige_un_corpus()
        self.assertGreater(sum(int(r["documents"]) for r in self.resultats), 0)

    def test_AU_MOINS_UN_PROCES_VERBAL_EST_RECONNU(self) -> None:
        """L'autre moitie de l'anti-vacuite, et elle manquait a l'item.

        Une signature qui ne reconnait RIEN a elle aussi zero faux positif.
        Les deux controles se tiennent: l'un interdit de reconnaitre a tort,
        l'autre interdit de ne rien reconnaitre du tout.
        """
        self._exige_un_corpus()
        self.assertGreater(sum(int(r["vrais"]) for r in self.resultats), 0)


class LeChiffrageEstMESURE_ET_NON_FIGE(_Mesure):
    """Ce qui est corpus-dependant se rapporte, ne s'epingle pas."""

    def test_chaque_corpus_present_rend_un_compte_coherent(self) -> None:
        self._exige_un_corpus()
        for r in self.resultats:
            with self.subTest(corpus=r["nom"]):
                total = int(r["vrais"]) + int(r["faux"]) + int(r["sans_titre"])
                self.assertLessEqual(total, int(r["documents"]))
                self.assertGreaterEqual(int(r["documents"]), 1)

    def test_les_corpus_mesures_sont_nommes_au_journal(self) -> None:
        """Une mesure sans base nommee n'est pas une mesure (`RM-2026-0150`)."""
        self._exige_un_corpus()
        for r in self.resultats:
            self.assertTrue(str(r["nom"]).strip())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
