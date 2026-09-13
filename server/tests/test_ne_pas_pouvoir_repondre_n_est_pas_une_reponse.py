# -*- coding: utf-8 -*-
"""Une liste vide dit *rien trouve*, jamais *je n'ai pas pu chercher*.

Axe B de `RM-2026-0086`, dans les mots de l'item: *un `except Exception` nu rend
`aucune autorisation identifiee` pour toute depense quelle que soit la cause*.

**Ce que la phrase affirme, et pourquoi c'est grave.** `aucune autorisation
identifiee` est une affirmation SUR LA COPROPRIETE: elle dit qu'on a cherche et
qu'on n'a rien trouve, ce qui alimente le constat `EURO_SANS_ACTE` - *depenses
hors budget previsionnel qu'aucun acte ne couvre*. Quand la lecture a echoue
parce que la base etait abimee, verrouillee ou incomplete, la verite est *la
question n'a pas pu etre posee*, et les deux se ressemblent a l'ecran.

**L'axe.** Ce qui varie, c'est la raison de l'echec: table absente, colonne
disparue, base abimee, fichier verrouille, erreur de disque. Ce qui reste
invariant, c'est que **repondre et ne pas pouvoir repondre ne sont pas le meme
etat**, et qu'un seul des deux se resume par une liste vide.

**La doctrine existait deja a cote.** `_actes_store.lire_vue` distingue depuis
le 2026-09-04 la table absente - une instance ou rien n'a encore ete verse - de
tout le reste, apres qu'une colonne manquante eut rendu **zero constat au lieu
de 818**, en silence. `actes_du_dossier` etait la derniere fonction du modele
restee en arriere.

**Ce que ces tests ne demandent pas:** que la lecture reussisse. Ils demandent
que l'echec se distingue du vide.
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.modules._actes_store import SchemaDeGouvernanceDivergent


class _Instance:
    """Instance minimale: seul le coffre local compte pour ce magasin.

    Meme forme que dans `test_actes_autorisation`, volontairement: deux facons
    de fabriquer la meme fausse instance finiraient par diverger.
    """

    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()


class _SurUnCoffreJetable(unittest.TestCase):
    """Chaque test possede son coffre: aucune instance partagee, aucun etat commun."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.racine = Path(self._temp.name)
        (self.racine / "vault_local").mkdir(parents=True, exist_ok=True)
        self.instance = _Instance(self.racine)


class UNE_TABLE_ABSENTE_EST_LE_SEUL_VIDE_QUI_DIT_VRAI(_SurUnCoffreJetable):
    """Rien n'a encore ete verse: la liste vide est la bonne reponse."""

    def test_un_coffre_neuf_rend_une_liste_vide_sans_lever(self) -> None:
        A.preparer(self.instance)
        cx = sqlite3.connect(A.store_path(self.instance))
        try:
            cx.execute("DROP TABLE IF EXISTS actes_autorisation")
            cx.commit()
        finally:
            cx.close()
        self.assertEqual([], A.actes_du_dossier(self.instance, "DEP-1"))


class TOUTE_AUTRE_PANNE_REMONTE_AU_LIEU_DE_SE_TAIRE(_SurUnCoffreJetable):
    """Le temoin qui manquait: le critere doit savoir dire *je n'ai pas pu*."""

    def _abimer(self, sql: str) -> None:
        """Abime le coffre, puis FERME la connexion.

        `with sqlite3.connect(...)` valide la transaction mais ne ferme pas:
        sous Windows, le fichier reste verrouille et le dossier temporaire ne
        peut plus etre supprime. Cinq erreurs de nettoyage, aucune liee au
        correctif teste - mais un test qui echoue pour une raison etrangere a
        son sujet est aussi inutilisable qu'un test faux.
        """
        A.preparer(self.instance)
        cx = sqlite3.connect(A.store_path(self.instance))
        try:
            cx.execute(sql)
            cx.commit()
        finally:
            cx.close()

    def test_une_VUE_disparue_ne_passe_pas_pour_une_instance_neuve(self) -> None:
        """**SQLite ne distingue pas une vue d'une table dans son message.**

        Il dit `no such table: v_actes` pour une vue manquante comme pour une
        table manquante. Un premier jet de ce correctif s'arretait a `no such
        table` et aurait donc rendu une liste vide ici - reproduisant a
        l'identique le defaut que `lire_vue` avait corrige le 2026-09-04, ou
        rendre `[]` affichait *aucun acte n'est encore verse* sur une base qui
        en portait 173. Ce test existe parce que ce jet-la a ete ecrit.
        """
        self._abimer("DROP VIEW IF EXISTS v_actes")
        with self.assertRaises(SchemaDeGouvernanceDivergent) as leve:
            A.actes_du_dossier(self.instance, "DEP-1")
        message = str(leve.exception)
        self.assertIn("DEP-1", message, "le message doit nommer ce qui etait demande")
        self.assertIn("aucune autorisation identifiee", message,
                      "le message doit dire QUELLE phrase fausse aurait ete affichee")

    def test_une_COLONNE_disparue_ne_passe_plus_pour_une_absence_d_acte(self) -> None:
        """C'est le defaut exact mesure a cote: zero au lieu de 818, en silence.

        **Le temoin est ecrit dans le test, et il a fallu en changer.** Un
        premier jet retirait la colonne de la base par `ALTER TABLE ... DROP
        COLUMN`; SQLite le refuse des qu'une vue en depend, et le test echouait
        sur son propre montage sans rien dire du correctif. La requete de
        production est donc remplacee, le temps d'un appel, par une requete qui
        nomme une colonne absente - ce qui produit exactement l'erreur visee,
        `no such column`, sans abimer quoi que ce soit.
        """
        A.preparer(self.instance)
        avec_colonne_absente = (
            "SELECT l.colonne_qui_n_existe_pas FROM liens_gouvernance l "
            "WHERE l.target_id = ?"
        )
        with mock.patch.object(A, "SQL_ACTES_DU_DOSSIER", avec_colonne_absente):
            with self.assertRaises(SchemaDeGouvernanceDivergent) as leve:
                A.actes_du_dossier(self.instance, "DEP-1")
        self.assertIn("no such column", str(leve.exception))

    def test_le_message_dit_la_difference_entre_les_deux_etats(self) -> None:
        self._abimer("DROP VIEW IF EXISTS v_actes")
        with self.assertRaises(SchemaDeGouvernanceDivergent) as leve:
            A.actes_du_dossier(self.instance, "DEP-1")
        self.assertIn("n'a pas pu etre posee", str(leve.exception))


class LE_CAS_ORDINAIRE_N_EST_PAS_TOUCHE(_SurUnCoffreJetable):
    """Une garde qui casse le chemin nominal n'est pas une garde."""

    def test_un_coffre_prepare_et_vide_rend_une_liste_vide(self) -> None:
        A.preparer(self.instance)
        self.assertEqual([], A.actes_du_dossier(self.instance, "DEP-INCONNU"))

    def test_aucun_except_nu_ne_subsiste_dans_cette_fonction(self) -> None:
        """La garde porte sur la PROPRIETE, pas sur une ligne particuliere.

        Un lot suivant qui reintroduirait un `except Exception` ici le ferait
        sans reveiller les tests de comportement ci-dessus s'il rendait `[]`
        pour la table absente. Cette verification lit le CODE de la fonction.

        **La docstring en est retiree, et il a fallu s'y reprendre.** Le premier
        jet lisait le source entier et echouait: la docstring EXPLIQUE qu'un
        `except Exception` a ete retire, donc elle contient les deux mots. La
        garde attrapait la MENTION du motif au lieu du motif - le meme defaut,
        en miniature, que celui qu'elle surveille.
        """
        import ast
        import inspect

        arbre = ast.parse(inspect.getsource(A.actes_du_dossier).lstrip())
        fonction = arbre.body[0]
        if (fonction.body and isinstance(fonction.body[0], ast.Expr)
                and isinstance(fonction.body[0].value, ast.Constant)):
            corps = fonction.body[1:]
        else:  # pragma: no cover - une fonction sans docstring
            corps = fonction.body
        code = "\n".join(ast.unparse(n) for n in corps)
        self.assertNotIn("except Exception", code)
        self.assertIn("sqlite3.OperationalError", code)
        self.assertIn("NOMS_VUES", code,
                      "une vue absente doit rester distinguee d'une table absente")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
