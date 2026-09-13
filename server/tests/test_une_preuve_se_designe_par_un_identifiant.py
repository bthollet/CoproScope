# -*- coding: utf-8 -*-
"""Une preuve designe un document par son identifiant, jamais par son nom.

`RM-2026-0158`. L'invariant de l'item, dans ses termes: **le lien entre un
controle et sa preuve est une ancre - document plus position - jamais un nom de
fichier.**

**MESURE DU 2026-09-12, et l'invariant ne tient NI d'un cote NI de l'autre.**

| ce qui designe la preuve | lignes |
|---|---:|
| un **chemin ou un nom de fichier** | **7** |
| un **identifiant** de document | **20** |
| un identifiant **ET une position** | **0** |

Et les trois tables qui portent un rattachement - `traces_controle`,
`object_links`, `expected_piece` - **ne citent aucune position**.

**MON PREMIER INSTRUMENT ANNONCAIT ZERO, ET IL SE TROMPAIT.** Il ne cherchait
que les champs en `file_name`, `nom_fichier` ou `filename`, et **ignorait les
CHEMINS**. Or `_actions.py` remplit l'`evidence` d'une action avec
`row.get("chemin_piece")` **avant** de retomber sur `doc_id`. Un chemin est un
nom **plus un emplacement**: il change quand on renomme ET quand on deplace, ce
qui le rend pire qu'un nom nu, pas meilleur. J'allais publier *l'invariant
tient* sur une mesure qui ne regardait pas la moitie des facons de nommer un
fichier - troisieme instrument sous-detectant de la journee.

**LA DETTE EST DONC DE SEPT**, bornee et datee, dans cinq modules. Elle ne doit
pas grandir, et elle a vocation a tomber a zero: c'est la moitie negative de
l'invariant.

**LA MOITIE POSITIVE N'EXISTE PAS**, et c'est le contenu de l'item: **une
preuve designe un DOCUMENT, jamais une POSITION dans ce document.** Or un PDF
est un contenant qui peut porter plusieurs pieces ou aucune - une resolution,
une annexe, un devis sont des objets que le dossier designe, le fichier n'en
est que le support. Sans position, deux controles qui citent deux pieces d'un
meme PDF citent **la meme preuve**.

**CE QUE CETTE GARDE NE PEUT PAS FAIRE.** Elle ne pose pas l'ancre: l'item dit
que c'est **un ECRAN, pas un bouton** - *il faut imaginer une interface pour
poser les ancres a la main* - avec deux criteres d'acceptation qui engagent le
modele: une ancre posee a la main **survit a une re-extraction**, et **deux
ancres contradictoires sur le meme couple coexistent en disant qui les
affirme**. Le second interdit une cle unique sur le couple, ce qui est une
decision de schema.

**L'AXE.** Ce qui VARIE: le format du contenant, le nombre de pieces qu'il
porte, la maniere de reperer une position - page, offset, cadre. Ce qui reste
INVARIANT: **une piece logique n'est pas un fichier**, et ce qui la designe
doit survivre au renommage du support.
"""
from __future__ import annotations

import collections
import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "src"

#: Une ligne qui parle de preuve. C'est le perimetre de la mesure: on ne juge
#: pas tout le depot, seulement ce qui pretend rattacher un controle a sa
#: piece.
PREUVE = re.compile(r"preuve|proof|evidence", re.I)

#: Designer par le SUPPORT plutot que par la piece: un nom de fichier, ou un
#: CHEMIN. Les chemins ont ete oublies de la premiere version, et c'est ce qui
#: faisait annoncer un zero: un chemin est un nom **plus un emplacement**, donc
#: il rompt l'invariant deux fois au lieu d'une.
PAR_NOM = re.compile(
    r"[\"'](?:\w*file_name\w*|\w*nom_fichier\w*|\w*filename\w*"
    r"|chemin_\w+|\w*_path|path)[\"']")

#: Designer par l'identifiant du document.
PAR_IDENTIFIANT = re.compile(r"[\"'](?:doc_id|document_id|piece_id)[\"']")

#: Designer une POSITION dans le document.
PAR_POSITION = re.compile(
    r"[\"'](?:page|page_number|numero_page|position|offset|ancre|anchor|"
    r"bbox|ligne_debut)[\"']")

#: Etat mesure le 2026-09-12. **Deux dettes de sens oppose, dans le meme
#: tableau:** les sept designations par le support doivent DESCENDRE a zero,
#: les zero ancres doivent MONTER. Une borne laissee en place quand le compte
#: bouge laisse la frontiere reculer en silence, dans un sens comme dans
#: l'autre - d'ou les deux assertions encadrantes.
DESIGNE_PAR_NOM = 7
AVEC_POSITION = 0


def _compte() -> dict[str, int]:
    trouve: collections.Counter = collections.Counter()
    fichiers = list(RACINE.rglob("*.py")) + list(RACINE.rglob("*.pyfrag"))
    for chemin in fichiers:
        if "__pycache__" in chemin.parts:
            continue
        for ligne in chemin.read_text(encoding="utf-8", errors="replace").splitlines():
            if not PREUVE.search(ligne):
                continue
            if PAR_NOM.search(ligne):
                trouve["par_nom"] += 1
            if PAR_IDENTIFIANT.search(ligne):
                trouve["par_identifiant"] += 1
                if PAR_POSITION.search(ligne):
                    trouve["avec_position"] += 1
    trouve["fichiers"] = len(fichiers)
    return dict(trouve)


class UNE_PREUVE_NE_SE_DESIGNE_PAS_PAR_UN_NOM_DE_FICHIER(unittest.TestCase):
    def test_l_instrument_lit_bien_les_sources(self) -> None:
        """Sans lecture, les zeros ci-dessous ne voudraient rien dire.

        Un zero total est d'abord un symptome d'instrument: on verifie donc
        que le balayage trouve des fichiers ET des designations par
        identifiant, dont on sait qu'elles existent.
        """
        compte = _compte()
        self.assertGreater(compte.get("fichiers", 0), 200)
        self.assertGreater(
            compte.get("par_identifiant", 0), 10,
            "aucune designation par identifiant trouvee: le motif est casse, "
            "et le zero des noms de fichier ne prouverait rien")

    def test_la_dette_des_designations_par_le_support_ne_grandit_pas(self) -> None:
        """Sept lignes designent la preuve par un chemin ou un nom.

        Un nom de fichier change quand on renomme et ne dit pas de quelle
        copie il parle; un CHEMIN change en plus quand on deplace. Les deux
        rompent l'invariant de l'item.
        """
        compte = _compte().get("par_nom", 0)
        self.assertLessEqual(
            compte, DESIGNE_PAR_NOM,
            "une preuve de plus designe son support par son chemin ou son nom "
            "(%d pour une borne de %d). L'invariant de `RM-2026-0158` "
            "l'interdit: le lien entre un controle et sa preuve est une ancre."
            % (compte, DESIGNE_PAR_NOM))
        self.assertGreaterEqual(
            compte, DESIGNE_PAR_NOM,
            "la dette a BAISSE (%d au lieu de %d), et c'est une bonne "
            "nouvelle: abaisser la borne ici, et dire au gouvernail ce qui a "
            "remplace le chemin - sinon la frontiere peut remonter en silence."
            % (compte, DESIGNE_PAR_NOM))


class UNE_PREUVE_NE_PORTE_ENCORE_AUCUNE_POSITION(unittest.TestCase):
    """Le manque, mesure et borne - pas une tolerance, un compte qui doit monter."""

    def test_le_compte_des_ancres_est_celui_qui_a_ete_mesure(self) -> None:
        """Ce test echoue le jour ou la premiere ancre existe, et c'est voulu.

        Il demande alors de redire le compte: une dette qui BAISSE se declare,
        sinon la frontiere recule en silence. Ici la dette est un manque, donc
        elle se comble en MONTANT, et le message le dit.
        """
        self.assertEqual(
            AVEC_POSITION, _compte().get("avec_position", 0),
            "une preuve porte desormais une POSITION, ce que le modele ne "
            "savait pas faire. C'est la moitie manquante de `RM-2026-0158`: "
            "mettre ce compte a jour, et dire au gouvernail quelle ancre a ete "
            "posee, si elle survit a une re-extraction, et si deux ancres "
            "contradictoires peuvent coexister en disant qui les affirme.")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
