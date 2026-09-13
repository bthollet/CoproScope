"""`RM-2026-0052` defaut (2): un identifiant technique en face de l'utilisateur.

**Ce qui a ete mesure le 2026-09-03**, sur l'UI reelle de la page de
gouvernance: l'entete affichait `Assemblee du DOC-729CCCF88863` quand la date
de l'assemblee manquait. Un identifiant que le produit s'est mint a lui-meme
tenait lieu de nom d'assemblee.

**L'axe, et pourquoi la garde ne porte pas sur la chaine `Assemblee du`.**
La donnee absente est un degre de liberte: aujourd'hui c'est la date d'une
assemblee, demain ce sera le type d'une piece, l'objet d'une resolution ou le
nom d'un lot. Coder `l'entete d'assemblee ne contient pas DOC-` serait coder la
modalite vue le 2026-09-03, et la garde mourrait au premier autre champ.

**Ce qui reste vrai le long de cet axe**: quand une valeur manque, un libelle
destine a un lecteur le DIT avec des mots. Il ne se replie jamais sur une cle
technique, quelle que soit la valeur manquante et quel que soit l'ecran.

**Comment cette garde le mesure**: elle nourrit chaque fabricant de libelle avec
une ligne dont TOUT champ lisible est vide, et dont les seules valeurs
disponibles sont des identifiants. Si un repli existe quelque part, il ne peut
tomber que sur un identifiant, et le releve le nomme.

**Ce qu'elle ne prouve pas, et il faut le dire.** Elle lit des fonctions de
vue, pas une page rendue dans un navigateur. Aucun moteur de rendu ne vit dans
cette suite (`RM-2026-0111`): une mesure sur la source n'est pas une recette.
Elle prouve que la valeur de repli est une phrase; elle ne prouve pas qu'un
oeil la voit a l'endroit attendu.
"""

from __future__ import annotations

import re
import unittest

from coproscope.core.libelle_public import libelle_public_document
from coproscope.web._controle_gouvernance_cellules import _source_acte, _titre_acte
from coproscope.web.agcontentieux_view import _document_card

#: La forme d'une cle mint par le produit: un prefixe court en capitales, un
#: tiret, puis une serie sans mot dedans. `DOC-729CCCF88863`, `AG-2026-0004`,
#: `RES-12`. La garde ne liste pas les prefixes: c'est la FORME qui dit qu'une
#: chaine est une cle et non un mot, et elle survit a l'ajout d'un prefixe.
CLE_TECHNIQUE = re.compile(r"\b[A-Z]{2,6}-[0-9A-Z]{2,}(?:-[0-9A-Z]+)*\b")

#: Une ligne ou rien n'est lisible: ni type, ni date, ni objet, ni numero.
#: Seules restent les cles. C'est la seule matiere sur laquelle un repli
#: fautif peut tomber.
LIGNE_SANS_RIEN_DE_LISIBLE = {
    "doc_id": "DOC-729CCCF88863",
    "sha256": "0" * 64,
    "document_type": "",
    "suspected_date": "",
    "file_name": "",
    "original_path": "",
    "acte_id": "ACTE-729CCCF88863",
    "nature": "",
    "numero": "",
    "sous_numero": "",
    "date_effet": "",
    "source_doc_id": "DOC-729CCCF88863",
}


class TitreJamaisUnIdentifiantTests(unittest.TestCase):
    """Une cle peut ACCOMPAGNER un libelle; elle ne peut pas EN TENIR LIEU.

    La nuance n'est pas de confort. `Facture (012345)` porte une reference
    entre parentheses depuis toujours, et c'est ce qui distingue deux factures
    de meme date. Interdire toute cle partout condamnerait cette reference,
    donc la garde mesurerait autre chose que le defaut. Ce que le gouvernail
    reproche est un libelle qui EST une cle, sans un mot devant.
    """

    def assertPhrase(self, libelle: str, ou: str) -> None:
        self.assertTrue(libelle.strip(), f"{ou}: libelle vide")
        nu = re.sub(r"\([^)]*\)", " ", libelle).strip()
        debut = CLE_TECHNIQUE.match(libelle.strip())
        self.assertIsNone(
            debut,
            f"{ou}: le libelle destine au lecteur COMMENCE par une cle"
            f" technique - libelle rendu: {libelle!r}",
        )
        self.assertFalse(
            CLE_TECHNIQUE.findall(nu),
            f"{ou}: une cle technique tient lieu de mot dans le libelle"
            f" - libelle rendu: {libelle!r}",
        )
        self.assertTrue(
            re.search(r"[a-zA-Z]{3,}", nu),
            f"{ou}: hors reference entre parentheses, le libelle ne porte"
            f" aucun mot - libelle rendu: {libelle!r}",
        )

    def test_le_libelle_public_d_une_piece_sans_rien_de_lisible(self) -> None:
        self.assertPhrase(
            libelle_public_document(dict(LIGNE_SANS_RIEN_DE_LISIBLE)),
            "libelle_public_document",
        )

    def test_le_titre_de_carte_de_la_page_ag_contentieux(self) -> None:
        # Le point de rendu que le correctif du 2026-09-08 a fait passer par
        # `libelle_public_document`. La garde suit le point de rendu, pas la
        # fonction: c'est lui que le lecteur voit.
        carte = _document_card(dict(LIGNE_SANS_RIEN_DE_LISIBLE))
        self.assertPhrase(carte["title"], "agcontentieux _document_card.title")

    def test_le_titre_et_la_source_d_un_acte_de_la_page_de_gouvernance(self) -> None:
        ligne = dict(LIGNE_SANS_RIEN_DE_LISIBLE)
        self.assertPhrase(_titre_acte(ligne), "controle gouvernance _titre_acte")
        self.assertPhrase(_source_acte(ligne), "controle gouvernance _source_acte")

    def test_une_resolution_sans_numero_ni_date_reste_une_phrase(self) -> None:
        # Meme axe, autre valeur manquante: la nature est lue, le numero ne
        # l'est pas. C'est le cas que la modalite `date d'assemblee` ne couvre
        # pas et que l'axe couvre.
        ligne = dict(LIGNE_SANS_RIEN_DE_LISIBLE, nature="RESOLUTION_AG")
        self.assertPhrase(_titre_acte(ligne), "resolution sans numero")
        self.assertPhrase(_source_acte(ligne), "resolution sans date d'effet")


#: Le cas LITTERAL du gouvernail - l'entete `Assemblee du DOC-729CCCF88863` -
#: est deja garde a son point de rendu, sur une instance et avec le meme
#: identifiant, par
#: `test_ui_resolutions_assemblees.test_sans_aucune_date_le_titre_le_dit_au_lieu_d_afficher_une_reference`.
#: Ce fichier ne le redouble pas: il couvre les AUTRES points de rendu que le
#: meme axe expose, et que ce test-la ne regarde pas.


if __name__ == "__main__":
    unittest.main()
