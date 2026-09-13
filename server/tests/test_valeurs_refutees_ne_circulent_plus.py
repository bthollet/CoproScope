# -*- coding: utf-8 -*-
"""Une valeur refutee ne se remet pas a circuler, meme comme exemple.

**Le fait mesure le 2026-09-09.** Un etalon a ete refute le 2026-09-04: le
proces-verbal auquel il attribuait 34 resolutions **n'existe pas au dossier**,
et les deux montants qu'il citait ne figurent dans aucun proces-verbal - ils
viennent d'une convocation scannee sans aucune couche de texte, citee par des
numeros de ligne d'un fichier d'extraction qui ne contient aucun texte.

La rectification d'alors **nommait** le blueprint parmi les documents adosses a
cet etalon. Cinq jours plus tard, ce blueprint n'avait toujours pas son encadre
et prescrivait encore ces valeurs en dix endroits. Pire, et c'est le fait qui
justifie ce garde: **un artefact ecrit le 2026-09-07, trois jours APRES la
refutation, reprenait le montant comme exemple.**

**L'axe.** Ce qui varie: quelle valeur, quel document, quel auteur, quelle date.
Ce qui reste invariant: **une valeur declaree refutee ne doit plus etre affirmee
ni servir d'exemple.** Un chiffre faux laisse en exemple se propage tout seul,
parce que rien dans sa forme ne dit qu'il est faux - c'est meme sa
vraisemblance qui le fait recopier.

**Ce que ce garde ne peut pas faire, et il faut le dire.** Il ne DECOUVRE pas
qu'une valeur est fausse: aucune forme ne distingue un montant juste d'un
montant faux. Le registre ci-dessous est declaratif, et c'est assume. Ce que le
garde tient, c'est l'etape suivante, celle qui a echoue quatre fois: **une fois
qu'on sait qu'une valeur est fausse, elle cesse de circuler.**

**Les contextes ou elle a le droit d'apparaitre** sont ceux qui la DECLARENT
fausse: un texte barre, une ligne qui dit qu'elle est refutee, ou un fichier
dont le role est de porter la rectification. Partout ailleurs, echec, en nommant
le fichier et la ligne.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]

#: Les valeurs refutees, avec l'item qui porte leur rectification.
#:
#: **Registre declaratif.** Une valeur y entre quand une mesure l'a refutee; on
#: ne devine pas. Ajouter une entree est une decision tracee, pas une rustine.
VALEURS_REFUTEES = {
    "18 240,00": "RM-2026-0063 - montant absent de tout proces-verbal",
    "22 200,00": "RM-2026-0063 - montant absent de tout proces-verbal",
    "23 460,00": "RM-2026-0063 - montant absent de tout proces-verbal",
    "34 resolutions": "RM-2026-0063 - le PV cite n'existe pas au dossier; le PV reel en porte 55",
}

#: Une ligne qui DECLARE la valeur fausse a le droit de la citer. Ces marques
#: sont des formes d'ecriture, pas une liste de fichiers: n'importe quel
#: document peut porter une rectification, et doit pouvoir la porter.
#:
#: **Ce garde a enumere des modalites a son premier passage, et s'est fait
#: prendre par sa propre premiere mesure.** Une ligne qui declarait pourtant
#: parfaitement la refutation - `Le proces-verbal du 21/02/2024 et ses "34
#: resolutions" N EXISTENT PAS au dossier` - a ete signalee, parce que la liste
#: portait `n'existe pas` au singulier et en minuscules. Les marques sont donc
#: des RADICAUX, compares sans casse et sans apostrophe.
#:
#: **La degradation reste sure, et c'est ce qui rend cette liste acceptable.**
#: Une tournure de refutation inconnue produit une **fausse ALARME**, jamais un
#: faux silence: l'auteur voit son fichier nomme et choisit d'employer une
#: tournure connue ou d'en declarer une ici. Un garde de veracite peut crier a
#: tort; il ne peut pas se taire a tort.
_MARQUES_BRUTES = ("~~", "refut", "rectif", "n exist", "ne figure", "aucun proces-verbal",
                   "exemple", "barre", "ne sont pas employes")
MARQUES_DE_DECLARATION = _MARQUES_BRUTES


def _declare_la_refutation(ligne: str) -> bool:
    """La ligne dit-elle elle-meme que la valeur est fausse ?"""
    normal = ligne.lower().replace("'", " ").replace("’", " ")
    return any(m in normal for m in _MARQUES_BRUTES)

#: Les documents dont le ROLE est de porter la refutation et son histoire. Ils
#: citent la valeur des dizaines de fois, ligne par ligne, et c'est leur objet.
PORTEURS_DE_LA_RECTIFICATION = {
    "docs/parcours_utilisateur_tests_ux.md",
    "docs/strategie_lot_gouvernance.md",
    "docs/etalon_corpus_tests_ux.md",
    "docs/maquettes_controle_2026-09-03.md",
    "server/tests/test_valeurs_refutees_ne_circulent_plus.py",
}

#: Les notes d'audit et les journaux datent d'AVANT la refutation ou racontent
#: des mesures faites sur des donnees de test portant ces valeurs. On ne
#: reecrit pas le passe: un journal est un temoignage, pas une prescription.
ZONES_HISTORIQUES = ("docs/finition-", "docs/verifications-", "docs/constats_audit_",
                     "docs/presence_agents.md", "docs/roadmap_backlog_central.md",
                     "docs/modele_gouvernance_decisions.md", "docs/tri_backlog_")


def _fichiers_suivis() -> list[str]:
    """**Echoue plutot que de sauter** si Git ne repond pas."""
    sortie = subprocess.run(["git", "ls-files", "docs"], cwd=DEPOT, check=True,
                            capture_output=True, text=True, encoding="utf-8")
    return [l for l in sortie.stdout.splitlines() if l.strip()]


def _concerne(rel: str) -> bool:
    if rel in PORTEURS_DE_LA_RECTIFICATION:
        return False
    return not any(rel.startswith(z) for z in ZONES_HISTORIQUES)


class UneValeurRefuteeNeCirculePlus(unittest.TestCase):
    def test_le_perimetre_n_est_pas_vide(self) -> None:
        """Sans cela, un garde qui ne lit rien passerait pour vert."""
        concernes = [f for f in _fichiers_suivis() if _concerne(f)]
        self.assertGreater(len(concernes), 20, "perimetre suspect: %d" % len(concernes))

    def test_aucune_valeur_refutee_dans_un_document_vivant(self) -> None:
        fautes = []
        for rel in _fichiers_suivis():
            if not _concerne(rel):
                continue
            try:
                texte = (DEPOT / rel).read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for numero, ligne in enumerate(texte.splitlines(), 1):
                if _declare_la_refutation(ligne):
                    continue
                for valeur, motif in VALEURS_REFUTEES.items():
                    if valeur in ligne:
                        fautes.append(
                            "%s:%d - `%s` a ete refute (%s) et cette ligne ne le "
                            "declare pas. Barrer la valeur, dire qu'elle est refutee, "
                            "ou employer un exemple neutre." % (rel, numero, valeur, motif)
                        )
        self.maxDiff = None
        self.assertEqual([], fautes, "\n".join(fautes))

    def test_une_ligne_qui_DECLARE_la_valeur_fausse_est_admise(self) -> None:
        """La propriete qui porte le garde, prouvee sur les deux cas."""
        self.assertTrue(_declare_la_refutation("les montants ~~18 240,00~~ sont refutes"))
        # La tournure qui a pris ce garde en defaut a son premier passage.
        self.assertTrue(_declare_la_refutation('ses "34 resolutions" N EXISTENT PAS au dossier'))
        nue = "| Cout | formate `18 240,00 EUR`, jamais `18240.0` |"
        self.assertFalse(_declare_la_refutation(nue))
        self.assertIn("18 240,00", nue)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
