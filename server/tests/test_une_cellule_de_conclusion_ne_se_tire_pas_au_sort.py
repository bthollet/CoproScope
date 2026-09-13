# -*- coding: utf-8 -*-
"""La cellule `Ma conclusion` ne depend pas de l'ordre de lecture du magasin.

`RM-2026-0161`. **Le verdict affiche a l'ecran de controle de gouvernance
etait tire au sort**, et le test qui pretendait figer ce comportement ne
mesurait pas ce qu'il annoncait.

----------------------------------------------------------------------
Les six faits, tous lus dans le code et non deduits
----------------------------------------------------------------------

1. Plusieurs conclusions coexistent pour un meme acte: une trace ne s'ecrase
   pas, c'est la propriete qui permet a un humain de travailler sans craindre
   le prochain passage de la chaine.
2. `_controle_gouvernance_source.py` repliait ces traces par ecrasement dans
   un `dict[str, str]`: **le dernier itere gagnait**.
3. L'ordre de lecture est `TRACE_ORDRE = "constate_le DESC, trace_id"`
   (`_actes_schema.py:399`), applique tel quel en SQL
   (`gouvernance_store.py:356`). A dates differentes, `DESC` met le plus
   recent en tete, donc le dernier itere - le gagnant - etait **le plus
   ancien**: l'ecran retenait la PREMIERE conclusion ecrite, l'inverse de ce
   qui etait annonce.
4. `_horodate()` rend `.date().isoformat()`: une granularite au **JOUR**. Deux
   conclusions du meme jour portent donc le meme `constate_le`.
5. Le depart tombait alors sur `trace_id`, qui vaut
   `"TRACE-%s" % secrets.token_hex(5).upper()`: **un jeton aleatoire**.
6. Le test `test_deux_conclusions_successives_coexistent_et_la_derniere_gouverne`
   affirmait dans son nom ET sa docstring que l'affichage retient la derniere
   ecrite et qu'il figeait ce comportement. Son corps n'assertait que la
   coexistence des deux identifiants en base: il n'appelait jamais
   `construire_lignes` et ne touchait aucune cellule. **La garde vivait dans
   le seul endroit que personne ne relit: un nom de methode.**

Deux conclusions de sens oppose - `QUESTION_POSEE` puis `RESERVE` - produisaient
donc une cellule qui en montrait une, tiree au sort, sans que le lecteur puisse
savoir qu'une autre existait. C'est le test d'acceptation de `RM-2026-0160`:
deux etats differents du dossier rendent le meme affichage sans qu'on puisse
remonter aux etats. Une TABLE reduite a un SCALAIRE, et ici le scalaire n'etait
meme pas deterministe.

----------------------------------------------------------------------
Ce que cette garde mesure, et ce qu'elle NE fige pas
----------------------------------------------------------------------

**Le predicat, enonce avant tout instrument:** pour tout acte et toute liste de
traces `T`, la cellule rendue par `construire_lignes(matrice, constats, T)` est
egale a celle rendue pour toute permutation de `T`. La cellule est une fonction
de l'ENSEMBLE des traces, jamais de leur ordre de lecture.

**Cette formulation est vraie de tout choix d'affichage futur** - montrer la
plus recente, montrer toutes les conclusions, montrer leur nombre. Elle
n'exige donc pas que le defaut survive, et elle ne fige aucune decision de
produit. C'est exactement ce que l'ancien test faisait de travers: il
pretendait figer un comportement, au lieu de garder une propriete.

Seconde dimension, meme garde: quand plusieurs conclusions existent, la ligne
porte **de quoi remonter a elles** - leur nombre et leurs verdicts - a cote de
la valeur composee.

**Ce que cette garde ne fait pas, et le residu se declare.** `constate_le` a
une granularite au jour: *laquelle est la derniere* reste indecidable a
l'interieur d'une journee a partir de ce qui est ecrit. Le tri rend la reponse
deterministe, il ne la rend pas juste. Passer a un horodatage complet touche
la semantique de donnees deja ecrites, et releve d'un arbitrage.

**La portee est DECLAREE, pas deguisee en decouverte.** Elle couvre UNE cellule
nommee, `conclusion`, du seul ecran de controle de gouvernance. Une premiere
version de ce lot voulait deriver la portee de `_actes_schema.TABLES`; cette
derivation ne derivait rien - elle selectionnait la seule table portant
`sujet_kind`. Mieux vaut une portee etroite et dite qu'une portee large et
fausse.
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.web._controle_gouvernance_source import construire_lignes

#: Les deux verdicts sont de SENS OPPOSE, et c'est voulu: si la cellule bascule
#: de l'un a l'autre selon l'ordre de lecture, le lecteur ne lit pas une nuance,
#: il lit une autre conclusion.
PREMIER = "QUESTION_POSEE"
SECOND = "CONTROLE_TRACE"

#: Le meme jour pour les deux traces: c'est le cas ou `constate_le` ne
#: departage pas, donc celui ou le jeton aleatoire decidait.
LE_MEME_JOUR = "2026-09-12"


def _acte(acte_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "acte_id": acte_id, "nature": "RESOLUTION_AG", "etat": "CONSTATEE",
        "portee": "ENGAGEMENT_DEPENSE", "date_effet": "2026-04-29",
        "exercice": "2026", "ag_id": "AG-2026-04-29", "numero": "11",
        "sous_numero": "1", "objet": "Ravalement de la facade sud",
        "montant_autorise": "18240.00", "entreprise": "", "montant_source": "",
        "entreprise_source": "", "valide_du": "", "valide_au": "",
        "majorite_requise": "24", "majorite_appliquee": "24",
        "majorite_annoncee": "24", "resultat": "ADOPTEE", "resolution_id": "",
        "page": "16", "ancre": "sous-point 11-1", "confiance": "forte",
        "doc_id": "DOC-CONVOCATION", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _trace(trace_id: str, verdict: str, constate_le: str = LE_MEME_JOUR,
           sujet_id: str = "ACTE-1") -> dict[str, str]:
    return {
        "trace_id": trace_id, "sujet_kind": "acte", "sujet_id": sujet_id,
        "verdict": verdict, "texte": "Motif de la conclusion.",
        "auteur": "", "constate_le": constate_le, "doc_id": "",
        "page": "", "ancre": "", "origine": "HUMAIN_CONFIRME",
    }


class _Instance:
    display_name = "Copropriete de recette"

    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict[str, object]:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / str(valeur).lstrip("./")).resolve()


class _Socle(unittest.TestCase):
    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)
        A.ecrire(self.instance, A.TABLE_ACTES, [_acte("ACTE-1")],
                 ["DOC-CONVOCATION"])
        self.matrice = list(A.matrice(self.instance))

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=True)

    def _cellule(self, traces: list[dict[str, str]]) -> dict:
        """La ligne rendue par LE POINT D'ENTREE que la vue appelle.

        `controle_gouvernance_view.py` lit la table puis passe la liste a
        `construire_lignes`. On passe donc par la, et non par une fonction
        interne ni par le magasin: c'est la ou l'ancien test se trompait, il
        mesurait la base et parlait de l'affichage.
        """
        lignes = construire_lignes(self.matrice, [], traces)
        self.assertEqual(1, len(lignes), "socle casse: la matrice a change")
        return lignes[0]


class LA_CELLULE_NE_DEPEND_PAS_DE_L_ORDRE_DE_LECTURE(_Socle):
    """Le predicat lui-meme, et il etait faux jusqu'au 2026-09-12."""

    def test_deux_conclusions_DU_MEME_JOUR_rendent_la_meme_cellule(self) -> None:
        """Le cas ou le jeton aleatoire decidait.

        Meme `constate_le`, verdicts opposes: seul `trace_id` departage, et il
        est tire au sort a chaque ecriture. Si la cellule change quand la liste
        est retournee, alors elle change aussi d'une lecture a l'autre en
        production.
        """
        traces = [_trace("TRACE-AAAAAAAAAA", PREMIER),
                  _trace("TRACE-BBBBBBBBBB", SECOND)]
        dans_un_sens = self._cellule(traces)["conclusion"]
        dans_l_autre = self._cellule(list(reversed(traces)))["conclusion"]
        self.assertEqual(
            dans_un_sens, dans_l_autre,
            "la cellule affichee depend de l'ordre dans lequel le magasin a "
            "rendu les traces. Les deux candidats sont %r et %r, et le seul "
            "critere qui les departage est `trace_id`, un jeton aleatoire: le "
            "verdict lu par un humain est tire au sort."
            % (dans_un_sens, dans_l_autre))

    def test_deux_conclusions_de_DATES_DIFFERENTES_rendent_la_meme_cellule(self) -> None:
        """Le meme predicat, la ou une regle de choix existe pourtant.

        Ici `constate_le` departage, donc une reponse juste EXISTE. La garde ne
        dit pas laquelle: elle dit que la reponse ne doit pas dependre de
        l'ordre de lecture. Sans cela, le defaut se reduirait au seul cas du
        meme jour, alors qu'il portait sur les deux.
        """
        traces = [_trace("TRACE-AAAAAAAAAA", PREMIER, "2026-09-01"),
                  _trace("TRACE-BBBBBBBBBB", SECOND, "2026-09-12")]
        self.assertEqual(self._cellule(traces)["conclusion"],
                         self._cellule(list(reversed(traces)))["conclusion"])

    def test_LA_PLUS_RECENTE_gouverne_quand_les_dates_departagent(self) -> None:
        """Ce que le tri decide, dit ici au lieu d'etre laisse implicite.

        L'ancienne doctrine d'ecran annoncait *la derniere ecrite*; le code
        rendait la plus ANCIENNE. Une garde qui se contenterait de
        l'invariance par permutation laisserait cette inversion vivre, puisque
        l'inverse est aussi stable que l'endroit.
        """
        traces = [_trace("TRACE-AAAAAAAAAA", PREMIER, "2026-09-01"),
                  _trace("TRACE-BBBBBBBBBB", SECOND, "2026-09-12")]
        self.assertEqual(
            SECOND, self._cellule(traces)["conclusion"],
            "la cellule retient la conclusion la plus ANCIENNE: l'ordre "
            "`constate_le DESC` du magasin etait replie par ecrasement, donc "
            "le dernier itere gagnait")


class LA_LIGNE_PORTE_DE_QUOI_REMONTER_AUX_ETATS(_Socle):
    """Sans cela, ce qui manque ne se voit pas - et c'est la faute entiere."""

    def test_le_nombre_de_conclusions_voyage_avec_la_valeur(self) -> None:
        traces = [_trace("TRACE-AAAAAAAAAA", PREMIER),
                  _trace("TRACE-BBBBBBBBBB", SECOND)]
        ligne = self._cellule(traces)
        self.assertEqual(
            2, ligne["conclusions_nombre"],
            "la ligne ne dit pas que DEUX conclusions existent: le lecteur "
            "voit un verdict unique et n'a aucun moyen de savoir qu'une autre "
            "a ete ecrite")

    def test_les_verdicts_CANDIDATS_restent_a_cote_de_la_valeur(self) -> None:
        traces = [_trace("TRACE-AAAAAAAAAA", PREMIER),
                  _trace("TRACE-BBBBBBBBBB", SECOND)]
        candidats = self._cellule(traces)["conclusions_candidates"]
        self.assertEqual({PREMIER, SECOND}, set(candidats),
                         "les candidats sont perdus au repli: on ne peut plus "
                         "remonter de l'affichage aux etats du dossier")

    def test_les_CANDIDATS_ne_dependent_pas_non_plus_de_l_ordre(self) -> None:
        """Reparer la valeur en laissant son detail dependre de l'ordre ne
        reparerait rien: le detail est ce par quoi on remonte."""
        traces = [_trace("TRACE-AAAAAAAAAA", PREMIER),
                  _trace("TRACE-BBBBBBBBBB", SECOND)]
        self.assertEqual(self._cellule(traces)["conclusions_candidates"],
                         self._cellule(list(reversed(traces)))["conclusions_candidates"])


class LES_TEMOINS_SANS_LESQUELS_CETTE_GARDE_MESURERAIT_LE_VIDE(_Socle):
    """Un instrument qui rend le meme verdict a tout ne prouve rien."""

    def test_AUCUNE_trace_rend_a_instruire_et_zero_candidat(self) -> None:
        ligne = self._cellule([])
        self.assertEqual("a_instruire", ligne["conclusion"])
        self.assertEqual(0, ligne["conclusions_nombre"])
        self.assertEqual([], ligne["conclusions_candidates"])

    def test_UNE_SEULE_trace_gouverne_la_cellule(self) -> None:
        """Le cas de loin le plus courant: il doit rester simple et exact."""
        ligne = self._cellule([_trace("TRACE-AAAAAAAAAA", SECOND)])
        self.assertEqual(SECOND, ligne["conclusion"])
        self.assertEqual(1, ligne["conclusions_nombre"])

    def test_une_trace_qui_ne_porte_PAS_sur_un_acte_est_ignoree(self) -> None:
        """Sinon la garde dirait vrai en comptant des traces d'autre chose."""
        ailleurs = _trace("TRACE-CCCCCCCCCC", SECOND)
        ailleurs["sujet_kind"] = "dossier"
        ligne = self._cellule([ailleurs])
        self.assertEqual("a_instruire", ligne["conclusion"])
        self.assertEqual(0, ligne["conclusions_nombre"])

    def test_une_trace_d_un_AUTRE_acte_ne_remplit_pas_cette_cellule(self) -> None:
        ligne = self._cellule([_trace("TRACE-DDDDDDDDDD", SECOND,
                                      sujet_id="ACTE-AUTRE")])
        self.assertEqual("a_instruire", ligne["conclusion"])
        self.assertEqual(0, ligne["conclusions_nombre"])

    def test_un_verdict_HORS_VOCABULAIRE_ne_s_affiche_pas_tel_quel(self) -> None:
        """Une valeur qui ressemble a du vocabulaire sans en etre eteindrait
        en silence les controles qui s'appuient dessus."""
        ligne = self._cellule([_trace("TRACE-EEEEEEEEEE", "PAS_UN_VERDICT")])
        self.assertEqual("a_instruire", ligne["conclusion"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
