# -*- coding: utf-8 -*-
"""Une trace qui cite une instance jetable dit qu'elle est jetable.

`RM-2026-0172`, action nommee par l'item lui-meme: *balayer les colonnes
PREUVE du gouvernail a la recherche de chemins d'instance de lot*.

**LE MOTIF, ET IL EST DEJA ETABLI PAR L'ITEM.** La doctrine impose de
**supprimer l'instance de lot a la fin du chantier** - sinon elle devient une
instance historique qu'on prendra pour une reference. Donc **toute mention
d'une instance de lot cesse d'etre verifiable, et c'est une garantie, pas un
oubli**. L'item avait traite le cas des TESTS: 12 sauts sur 18 venaient d'un
seul nom d'instance disparu. Il restait le cas des TRACES, et l'item disait
pourquoi il est pire: *un test saute laisse au moins un `skipped` dans une
sortie, une trace fausse ne signale rien*.

**MESURE DU 2026-09-12.** Le gouvernail porte **21 citations d'instance**, dont
**8 designent une instance jetable** au sens de la convention de nommage.
**Quatre etaient muettes.** Deux d'entre elles nommaient une instance
**absente du poste**; les deux autres une instance encore presente, donc
appelee a disparaitre.

**LA PIRE DES QUATRE EST AU PRESENT.** Une ligne affirmait
*L'INSTANCE DEMANDEE PAR CET ITEM EXISTE*, ce qui etait vrai le jour de
l'ecriture et deviendra faux **sans qu'une lettre du texte ne change**. C'est
la forme la plus couteuse du defaut: une trace au present sur un objet jetable
se perime toute seule, et rien dans la phrase ne dit quand.

**L'AXE, et c'est la doctrine qui le donne.** Ce qui VARIE: le sujet du lot,
sa date, le corpus. Ce qui reste INVARIANT: **le NOM porte la garantie** -
`CLAUDE.md` le dit en propres termes, une instance prefixee `test_`, `dev_` ou
`lot_`, ou datee en suffixe, est un duplicata de travail qui se supprime a la
fin. La garde lit donc la convention de nommage, pas une liste d'instances
rencontrees. **Hors des valeurs observees:** une instance de lot creee demain,
sous un nom que personne ici ne connait, est couverte le jour de sa citation.

**CE QUE LA GARDE N'EST PAS.** Elle ne verifie **pas** qu'une instance existe:
la CI n'a pas le droit de lire une instance privee, et `instances/` vit hors
du depot. Elle verifie que le TEXTE se declare - ce qui est justement ce qui
survit a la disparition du dossier. C'est la lecon de l'item: une garde qui
depend d'une instance de lot meurt avec elle.

**LE VOISINAGE EXCLUT LA CITATION, et cette precaution a deja ete payee.** La
garde soeur `test_gouvernail_ne_cite_pas_de_preuve_absente` s'est trompee deux
fois: d'abord en cherchant la declaration dans TOUTE la ligne - une ligne du
registre fait des milliers de caracteres, si bien qu'un mot ecrit a l'autre
bout exemptait tous ses chemins; ensuite en incluant la citation dans son
propre voisinage, si bien qu'un fichier nomme `absent.md` se declarait absent
tout seul. **Une citation ne peut pas etre son propre temoin.**
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REGISTRE = Path(__file__).resolve().parents[2] / "docs" / "roadmap_backlog_central.md"

_SEP = "[/" + chr(92) * 2 + "]"

#: La convention de nommage de `CLAUDE.md`: un prefixe `test_`, `dev_` ou
#: `lot_`, ou une date en suffixe pour `instances/lot_<sujet>_<date>`. Ce n'est
#: pas une liste d'instances observees: c'est la regle qui dit ce qu'on a le
#: droit de faire du dossier.
INSTANCE_JETABLE = re.compile(
    "instances" + _SEP + r"(?:(?:test|dev|lot)_[A-Za-z0-9_.\-]+"
    r"|[A-Za-z0-9_.\-]*_\d{8})")

#: Les mots par lesquels une trace reconnait que son support a disparu ou va
#: disparaitre. La liste est large a dessein: on garde le sens, pas une
#: formule - exiger une formule serait coder une modalite d'ecriture.
DECLARATION = re.compile(
    r"jetable|supprim|n.existe plus|absente|absent du poste|disparue|"
    r"detruite|plus sur le poste|effacee|n.est plus la|"
    r"non reverifiable|hors du poste", re.I)

#: La citation est EXCLUE de son propre voisinage, et le voisinage est court:
#: une ligne de registre fait des milliers de caracteres.
PORTEE = 200


def _citations() -> list[tuple[str, str, bool]]:
    """Chaque citation d'instance jetable, avec son item et son verdict."""
    texte = REGISTRE.read_text(encoding="utf-8")
    trouves: list[tuple[str, str, bool]] = []
    for trouve in INSTANCE_JETABLE.finditer(texte):
        debut, fin = trouve.start(), trouve.end()
        voisinage = texte[max(0, debut - PORTEE):debut] + texte[fin:fin + PORTEE]
        depart = texte.rfind("\n", 0, debut) + 1
        arrivee = texte.find("\n", fin)
        ligne = texte[depart:arrivee if arrivee != -1 else len(texte)]
        item = ligne.split("`")[1] if ligne.startswith("| `RM-") else "(hors item)"
        trouves.append((trouve.group(0), item, bool(DECLARATION.search(voisinage))))
    return trouves


class UNE_INSTANCE_JETABLE_CITEE_SE_DECLARE(unittest.TestCase):
    def test_l_instrument_trouve_bien_des_citations(self) -> None:
        """Garde de l'instrument: un motif casse rendrait le test vide et VERT.

        C'est la quatrieme forme de la serie A nommee par l'item - celle qui
        ne laisse aucune trace du tout, pas meme un `Ran 0`.
        """
        self.assertGreaterEqual(
            len(_citations()), 5,
            "le motif ne trouve presque aucune citation d'instance jetable: "
            "il est casse, et ce test passerait a vide")

    def test_chaque_citation_dit_que_son_support_est_jetable(self) -> None:
        muettes = [(chemin, item) for chemin, item, declare in _citations()
                   if not declare]
        self.assertEqual(
            [], muettes,
            "ces traces citent une instance de LOT sans dire qu'elle est "
            "jetable. Le nom porte la garantie: un dossier `test_`, `dev_` ou "
            "`lot_` se supprime a la fin du chantier, donc la citation cessera "
            "d'etre verifiable et rien ne le signalera. Ajouter, a moins de "
            "%d caracteres de la citation, que l'instance est jetable ou "
            "absente - et le dire au PASSE, une affirmation au present se "
            "perime sans qu'une lettre ne change. Muettes: %s"
            % (PORTEE, muettes))

    def test_une_instance_DURABLE_n_est_pas_visee(self) -> None:
        """Temoin: la garde ne reclame rien de ce qui a le droit d'etre cite.

        `instances/tests_ux` est le corpus etalon, `erables_pseudo_test` le
        second cabinet: `CLAUDE.md` les nomme comme references durables. Les
        exiger declares les rendrait suspects a tort.
        """
        for durable in ("instances/tests_ux", "instances/erables_pseudo_test"):
            with self.subTest(instance=durable):
                self.assertIsNone(INSTANCE_JETABLE.fullmatch(durable))

    def test_une_citation_n_est_pas_son_propre_temoin(self) -> None:
        """La lecon payee par la garde soeur, rendue executable.

        Un chemin qui porterait un mot de declaration dans son propre nom ne
        doit pas s'exempter: le voisinage exclut la citation.
        """
        piege = "voici instances/test_supprime_20260101 et rien d'autre"
        trouve = INSTANCE_JETABLE.search(piege)
        self.assertIsNotNone(trouve)
        voisinage = (piege[max(0, trouve.start() - PORTEE):trouve.start()]
                     + piege[trouve.end():trouve.end() + PORTEE])
        self.assertIsNone(
            DECLARATION.search(voisinage),
            "le nom de l'instance sert de declaration a lui-meme: le "
            "voisinage n'exclut pas la citation")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
