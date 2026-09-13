# -*- coding: utf-8 -*-
"""Aucune adresse postale reelle dans les fichiers suivis par Git.

**La regle de Brice est sans marge:** *« sur GitHub, aucune donnee personnelle
ne doit filtrer. Zero, aucun patronyme rien. »*

**Le defaut mesure le 2026-09-09, et c'etait le mien.** Une fixture de test
ecrite la veille portait le titre d'un vrai proces-verbal, **adresse postale
comprise** - numero, voie, code postal, commune. Le nom de la copropriete avait
ete pseudonymise; **l'adresse, elle, avait traverse le pseudonymat intacte**, et
une adresse designe un immeuble bien mieux qu'un nom. Une seconde fixture,
datant du 2026-06-01, portait l'adresse d'un fournisseur dont le telephone et
le courriel avaient pourtant ete remplaces par des valeurs manifestement
fausses: **le caviardage s'etait arrete au milieu de la ligne.**

**Ce que ce garde peut et ne peut pas faire.** Reconnaitre une adresse REELLE
par sa forme est impossible: rien ne distingue une vraie voie d'une fausse. Le
garde retourne donc la charge de la preuve - **une adresse presente dans le
depot doit se declarer fictive**, en employant une commune conventionnelle. La
liste est assumee comme telle, et c'est le seul controle qui degrade
proprement: une valeur inconnue **echoue en nommant le fichier et la ligne**,
elle ne passe jamais en silence.

L'axe retenu pour reperer une adresse est celui de l'adressage francais lui-
meme, pas un vocabulaire de voirie: **un code a cinq chiffres suivi d'un nom de
commune**. Il ne depend ni du type de voie - rue, traverse, chemin, montee -,
ni de la casse, ni du cabinet qui a redige la piece.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]

#: Les communes conventionnelles du depot pour une adresse fabriquee. Pour en
#: ajouter une, l'ecrire ici: c'est une decision, pas un contournement.
COMMUNES_FICTIVES = {"ville", "commune", "exemple", "exemples"}

#: Code postal francais, puis un nom de commune.
#:
#: **Deux resserrements, imposes par une premiere version qui rendait 25
#: fausses alertes.** Cinq chiffres suivis d'un mot quelconque attrapent
#: `12345 octets`, `20000 EUR`, `1200 sur`: le motif mesurait la langue
#: francaise, pas une adresse. Ce qui distingue une commune de tout cela n'est
#: pas un dictionnaire de villes - il en existe 34 000 et il changerait - mais
#: deux proprietes du NOM PROPRE: il porte une majuscule, et il est plus long
#: qu'un symbole d'unite ou de monnaie. D'ou la capitale exigee et le seuil de
#: quatre lettres, qui ecarte `EUR`, `HT`, `TTC`, `Mo`.
#:
#: **Un troisieme defaut, et celui-la rendait un VERT FAUX.** La premiere
#: version bornait le code par `\b`. Or une fixture ecrit son document dans une
#: chaine Python: `"BP 242\nSMA...\n13308 MARSEILLE"`. Les deux caracteres de
#: l'echappement `\n` sont litteraux dans le fichier source, donc le code postal
#: est **colle a la lettre `n`** - et entre `n` et `1` il n'y a aucune frontiere
#: de mot. Le garde passait au vert sur une adresse reelle, dans le seul endroit
#: ou une fixture cache un document entier. Ce n'etait pas un angle mort etroit:
#: c'est la forme normale des fixtures de ce depot.
#:
#: **Le remede a d'abord ete le mauvais.** Remplacer la frontiere de mot par
#: « exactement cinq chiffres » traversait bien l'echappement, mais rendait
#: quatre fausses alertes: les cinq derniers chiffres d'un identifiant -
#: `AG-DOC-729CCCF88863  DOC-...` - devenaient un code postal suivi d'une
#: commune. **La frontiere de mot n'etait pas fausse; c'est l'echappement qui la
#: cassait.** On traite donc l'echappement AVANT de lire, au lieu d'affaiblir la
#: regle: `_deplie` rend ses lignes au document que la fixture represente, et le
#: motif garde sa frontiere. Les deux exigences tiennent alors ensemble.
#:
#: **Ce que le garde laisse passer, et c'est declare:** les rares communes de
#: moins de quatre lettres - Eu, Ay, Oo -, et une adresse dont la commune serait
#: ecrite en minuscules.
_ADRESSE = re.compile(r"\b\d{5}\b[ \t]+([A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’-]{3,})")

#: Les echappements de saut de ligne et de tabulation, ecrits en toutes lettres
#: dans une chaine du code source. Deux caracteres dans le fichier, mais **une
#: fin de ligne dans le document que la fixture represente.**
_ECHAPPEMENTS = re.compile(r"\\[nrt]")


def _deplie(ligne: str) -> list[str]:
    """Les lignes du DOCUMENT que porte une ligne du fichier source.

    **Une premiere version remplacait l'echappement par une espace, et c'etait
    faux.** Recoller les lignes du document en une seule fabrique des voisinages
    qui n'existent pas: `"Facture 12345\\nDate : ..."` devenait `12345 Date`,
    soit un code postal suivi d'un nom propre. Deux fausses alertes.

    Un echappement n'est pas un blanc, **c'est une fin de ligne** - et une
    adresse postale tient sur une ligne. On decoupe donc, et chaque ligne du
    document se lit pour elle-meme.
    """
    return _ECHAPPEMENTS.split(ligne)


def _cherche(ligne: str):
    """La lecture complete d'une ligne source: on deplie, puis on cherche."""
    for segment in _deplie(ligne):
        trouve = _ADRESSE.search(segment)
        if trouve:
            return trouve
    return None


#: Les fichiers dont la RAISON D'ETRE est de porter le motif: ce garde, qui
#: l'explique et le prouve, et le test de l'outil de pre-push, qui verifie la
#: meme regle hors de la suite. Les exclure n'affaiblit rien - ils ne cachent
#: pas une donnee, ils la decrivent - mais l'oubli les ferait crier a chaque
#: passage, et **un garde qui crie toujours finit ignore.**
#:
#: `tools/verifier_avant_push.py` tient la meme liste sous le nom
#: `DECLARENT_LE_MOTIF`. Les deux doivent rester d'accord.
IGNORES = {
    "server/tests/test_aucune_adresse_reelle.py",
    "server/tests/test_verifier_avant_push.py",
}


def _fichiers_suivis() -> list[str]:
    """Les fichiers suivis par Git dans le perimetre diffusable.

    **Echoue plutot que de sauter** si Git est indisponible: un garde qui se
    tait quand il ne peut pas voir est pire que pas de garde du tout.
    """
    sortie = subprocess.run(
        ["git", "ls-files", "server", "docs", "CLAUDE.md", "README.md"],
        cwd=DEPOT, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    return [l for l in sortie.stdout.splitlines() if l.strip()]


class AucuneAdresseReelle(unittest.TestCase):
    def test_git_repond_et_le_perimetre_n_est_pas_vide(self) -> None:
        fichiers = _fichiers_suivis()
        self.assertGreater(len(fichiers), 50, "perimetre suspect: %d fichiers" % len(fichiers))

    def test_toute_adresse_du_depot_emploie_une_commune_fictive(self) -> None:
        fictives = {c.rstrip("s") for c in COMMUNES_FICTIVES}
        fautes = []
        for rel in _fichiers_suivis():
            if rel in IGNORES:
                continue
            try:
                texte = (DEPOT / rel).read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for numero, ligne in enumerate(texte.splitlines(), 1):
                for segment in _deplie(ligne):
                    for m in _ADRESSE.finditer(segment):
                        commune = m.group(1)
                        if commune.lower().rstrip("s") in fictives:
                            continue
                        fautes.append(
                            "%s:%d - `%s` suit un code postal. Si l'adresse est "
                            "reelle, la retirer; si elle est fabriquee, employer "
                            "une commune de COMMUNES_FICTIVES." % (rel, numero, commune)
                        )
        self.maxDiff = None
        self.assertEqual([], fautes, "\n".join(fautes))

    def test_le_motif_reconnait_une_adresse_et_ignore_le_reste(self) -> None:
        """Prouve que le motif porte, au lieu de passer parce qu'il ne voit rien."""
        self.assertTrue(_ADRESSE.search("12 rue Untel 75011 Paris"))
        self.assertTrue(_ADRESSE.search("3 TRAVERSE DU PARC 13009 MARSEILLE"))
        self.assertIsNone(_ADRESSE.search("total 12345 EUR"))            # trois lettres
        self.assertIsNone(_ADRESSE.search("SIRET 12345678900012"))       # pas de frontiere
        self.assertIsNone(_ADRESSE.search("fichier de 12345 octets"))    # minuscule
        self.assertIsNone(_ADRESSE.search("budget 20000 contre 18000"))  # minuscule
        self.assertIsNone(_ADRESSE.search("telephone 0600000000 Contact"))

    def test_LE_VERT_FAUX_une_adresse_derriere_un_echappement_est_vue(self) -> None:
        """Le defaut qui a fait passer ce garde au vert sur une adresse reelle.

        Une fixture ecrit son document dans une chaine Python, donc le code
        postal se retrouve colle a la lettre `n` de l'echappement `\\n`. Un
        motif borne par une frontiere de mot ne le voyait pas - et c'est
        exactement la que les documents se cachent dans ce depot.
        """
        self.assertTrue(_cherche(r"SMA\nBP 242\n13308 MARSEILLE, France"))
        self.assertIsNone(_cherche(r"COGELEC\nSIRET:43418922100022\nFin"))

    def test_LES_CINQ_DERNIERS_CHIFFRES_D_UN_IDENTIFIANT_ne_sont_pas_un_code(self) -> None:
        """Le premier remede etait le mauvais, et ces deux cas l'ont montre.

        Abandonner la frontiere de mot traversait bien l'echappement, mais
        faisait d'`AG-DOC-729CCCF88863  DOC-...` un code postal suivi d'une
        commune. C'est le depliage qui devait ceder, pas la frontiere.
        """
        self.assertIsNone(_cherche("AG-DOC-729CCCF88863  DOC-729CCCF88863"))
        self.assertIsNone(_cherche("NUM_FACTURE:FC12345 DATE_FACTURE:15/04/2025"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
