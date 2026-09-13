# -*- coding: utf-8 -*-
"""Une copie caviardee declare l'empreinte de ce dont elle derive.

`RM-2026-0147`. **L'axe:** *tout derive declare l'empreinte de ce dont il
derive, sans quoi il devient une source au premier oubli.*

**CE QUI EXISTAIT ET CE QUI MANQUAIT.** Le chainage etait ecrit **au
registre** - `source_sha256` et `redacted_sha256` - mais **pas sur la copie**.
Separee de son registre, la copie redevenait *indiscernable d'une piece
recue*: elle entrait dans les comptes comme un document de plus, et une
re-extraction ne savait pas quoi remplacer. La verification avait du
**reconstituer** le lien de sept copies par faisceau - meme pagination sept
fois sur sept, meme geometrie, puis 89 a 100 % du texte retrouve mot pour mot
apres retrait des alias. **Le rapprochement a reussi, et c'est ce qui rend le
defaut visible: il a fallu une enquete la ou une colonne aurait suffi.**

**LE BLOCAGE DECLARE PAR L'ITEM EST LEVE, ET PAR UN ARGUMENT, PAS PAR UN
CHOIX.** La cellule disait que la forme *est une decision de conception, pas un
correctif*, parce que `TEXT_EXTENSIONS` couvre neuf extensions dont quatre
structurees: **ajouter un en-tete a un `csv` ou a un `json` casse le fichier**.
Le fichier **a cote** n'a pas ce probleme - il est la meme forme pour les neuf
extensions et pour le PDF - et surtout il est la seule forme **correcte**:
`RM-2026-0092` exige que *l'empreinte soit calculee sur le seul contenu du
document*, sans quoi deux journaux ne seront jamais comparables. **Une
empreinte ecrite DANS la copie changerait la copie qu'elle decrit.**

`06_corpus_markdown` ecrit bien son `source_sha256` dans l'en-tete de son
derive, et ce n'est pas une contradiction: un corpus Markdown est un document
**nouveau**, qu'on lit; une copie caviardee doit rester **comparable** a son
original. **Les deux derives n'ont pas le meme usage.**

**UN SEUL POINT D'ECRITURE.** Le compagnon est pose dans
`_register_redaction`, par ou passent les trois ecrivains - texte, derive,
PDF - donc **aucun format ne peut etre oublie**. C'est la meme forme que celle
retenue le meme jour par `RM-2026-0061` pour les artefacts produits, et pour la
meme raison.
"""
from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path

B = importlib.import_module("coproscope.modules.biffageops")


class UneInstanceJetable(unittest.TestCase):
    def setUp(self) -> None:
        self.dossier = tempfile.TemporaryDirectory()
        self.racine = Path(self.dossier.name).resolve()
        (self.racine / "instance.yml").write_text(
            "identifiant_instance: essai\n", encoding="utf-8")
        self.instance = B.InstanceConfig(
            path=self.racine / "instance.yml",
            payload={
                "instance_id": "essai",
                # `staging` est requis par `redactions_path`: le test du
                # BRANCHEMENT passe par la vraie fonction d'enregistrement, pas
                # par une imitation.
                "roots": {"workspace": ".", "staging": "./staging"},
            })

    def tearDown(self) -> None:
        self.dossier.cleanup()

    def _record(self, relatif: str) -> dict[str, str]:
        return {
            "redaction_id": "RED-1",
            "redacted_path": relatif,
            "source_path": "raw/facture.pdf",
            "source_sha256": "a" * 64,
            "redacted_sha256": "b" * 64,
            "mode": "redaction_reversible",
        }


class LA_COPIE_PORTE_SON_ORIGINE(UneInstanceJetable):
    def test_le_compagnon_est_ecrit_a_COTE_de_la_copie(self) -> None:
        copie = self.racine / "staging" / "redacted" / "DOC-1.redacted.txt"
        copie.parent.mkdir(parents=True, exist_ok=True)
        copie.write_text("texte caviarde", encoding="utf-8")
        rendu = B.ecrire_compagnon_de_provenance(
            self.instance, self._record("staging/redacted/DOC-1.redacted.txt"))
        self.assertIsNotNone(rendu)
        self.assertEqual(copie.parent, rendu.parent)
        self.assertTrue(rendu.name.endswith(B.SUFFIXE_PROVENANCE))

    def test_il_porte_les_deux_empreintes_et_le_mode(self) -> None:
        rendu = B.ecrire_compagnon_de_provenance(
            self.instance, self._record("staging/redacted/DOC-1.redacted.txt"))
        charge = json.loads(rendu.read_text(encoding="utf-8"))
        self.assertEqual("a" * 64, charge["source_sha256"])
        self.assertEqual("b" * 64, charge["redacted_sha256"])
        self.assertEqual("redaction_reversible", charge["mode"])

    def test_il_ne_porte_RIEN_de_plus(self) -> None:
        """Un derive declare de quoi il derive, pas ce qu'il contient.

        Un compagnon bavard redeviendrait une piece a caviarder.
        """
        rendu = B.ecrire_compagnon_de_provenance(
            self.instance, self._record("staging/redacted/DOC-1.redacted.txt"))
        charge = json.loads(rendu.read_text(encoding="utf-8"))
        self.assertEqual(set(B.CHAMPS_PROVENANCE), set(charge))

    def test_il_ne_touche_AUCUN_octet_de_la_copie(self) -> None:
        """La contrainte de `RM-2026-0092`: l'empreinte porte sur le seul

        contenu du document. Une empreinte ecrite dans la copie changerait la
        copie qu'elle decrit, et deux journaux ne seraient plus comparables.
        """
        copie = self.racine / "staging" / "redacted" / "DOC-1.redacted.txt"
        copie.parent.mkdir(parents=True, exist_ok=True)
        copie.write_bytes(b"texte caviarde")
        avant = copie.read_bytes()
        B.ecrire_compagnon_de_provenance(
            self.instance, self._record("staging/redacted/DOC-1.redacted.txt"))
        self.assertEqual(avant, copie.read_bytes())


class LE_BRANCHEMENT_EST_EPROUVE_ET_NON_SUPPOSE(UneInstanceJetable):
    """La campagne de mutation a montre que tester la fonction ne suffit pas.

    Retirer l'appel dans `_register_redaction` ne faisait echouer **aucun**
    test: les autres appellent `ecrire_compagnon_de_provenance` directement.
    **Or le branchement EST l'argument du lot** - un seul point d'ecriture, par
    ou passent les trois ecrivains, donc aucun format ne peut etre oublie. Une
    fonction juste et non branchee ne protege rien, et c'est le meme defaut
    que la branche morte trouvee le matin sous `RM-2026-0061`.
    """

    def test_enregistrer_une_redaction_ECRIT_le_compagnon(self) -> None:
        relatif = "staging/redacted/DOC-9.redacted.txt"
        copie = self.racine / relatif
        copie.parent.mkdir(parents=True, exist_ok=True)
        copie.write_text("texte caviarde", encoding="utf-8")
        B._register_redaction(self.instance, self._record(relatif))
        compagnon = copie.with_name(copie.name + B.SUFFIXE_PROVENANCE)
        self.assertTrue(
            compagnon.is_file(),
            "le registre est ecrit mais la copie ne dit toujours pas d'ou "
            "elle vient: le point d'ecriture unique n'est plus branche")


class ON_N_INVENTE_PAS_UN_CHEMIN(UneInstanceJetable):
    def test_sans_copie_nommee_aucun_compagnon_n_est_ecrit(self) -> None:
        """Un compagnon orphelin serait pire que son absence: il declarerait
        une provenance pour un fichier qui n'existe pas."""
        record = self._record("")
        self.assertIsNone(
            B.ecrire_compagnon_de_provenance(self.instance, record))


class LA_FORME_VAUT_POUR_TOUS_LES_FORMATS(UneInstanceJetable):
    """Le blocage declare par l'item: neuf extensions, dont quatre structurees."""

    def test_un_csv_et_un_json_recoivent_le_meme_compagnon(self) -> None:
        for nom in ("DOC-1.redacted.csv", "DOC-2.redacted.json",
                    "DOC-3.redacted.pdf", "DOC-4.redacted.md"):
            with self.subTest(copie=nom):
                relatif = "staging/redacted/" + nom
                rendu = B.ecrire_compagnon_de_provenance(
                    self.instance, self._record(relatif))
                self.assertTrue(rendu.name.endswith(B.SUFFIXE_PROVENANCE))
                self.assertTrue(rendu.is_file())

    def test_les_extensions_concernees_sont_bien_neuf(self) -> None:
        """Temoin du perimetre mesure par l'item: si la liste grandit, la

        forme choisie doit encore valoir - un fichier a cote vaut pour toute
        extension, c'est ce qui a leve le blocage.
        """
        self.assertEqual(9, len(B.TEXT_EXTENSIONS))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
