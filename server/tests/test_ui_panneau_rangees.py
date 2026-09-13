"""Un gabarit de rangees ne doit pas enumerer les blocs presents le jour ou il a ete ecrit.

Defaut mesure le 2026-09-07, signale par Brice en ces termes: *du contenu reste
affiche derriere les grands tableaux coulissants*.

`.cs-rappro-queue-panel` declarait `grid-template-rows: auto minmax(0, 1fr)`,
soit exactement les DEUX blocs que `compta_rapprochement.html` lui donnait.
`controle_gouvernance.html` a reutilise la meme classe avec TROIS blocs. Le
troisieme a cree une rangee implicite, la barre de filtres a herite de la rangee
`1fr` que le `max-height` du panneau ecrase a zero, et ses 82 px de filtres, de
comptes et de consignes se sont peints par-dessus le tableau. Rien n'a echoue:
la page s'affichait, illisible.

C'est la regle des axes de `CLAUDE.md` appliquee a une mise en page. L'axe est
*le nombre de blocs que le panneau porte*; ce qui reste vrai le long de l'axe est
*chaque bloc garde sa hauteur propre et un seul bloc, nomme, absorbe le reste*.
Le correctif dit cela en flex et cesse de compter les enfants.

Cette garde protege l'axe et non le cas: elle rougit pour TOUT conteneur dont le
gabarit de rangees enumere moins de pistes que le gabarit HTML ne lui donne
d'enfants, y compris ceux qui n'existent pas encore.

**Portee, dite explicitement.** Elle lit le CSS et le HTML, elle ne rend rien -
la suite n'a aucun moteur de rendu, cf. `RM-2026-0111`. Elle ne voit donc pas
une superposition produite autrement que par ce mecanisme. Et parce qu'elle
compte les enfants STATIQUES apres retrait des balises Jinja, une boucle qui
repete un enfant est comptee pour un: elle peut sous-compter, jamais
sur-compter, donc elle ne produit pas de faux echec.

**Population reelle, mesuree avant d'ecrire la garde.** Apres le correctif,
`grid-template-rows` n'apparait plus NULLE PART dans la feuille: le panneau de
file etait le seul conteneur du produit a enumerer ses rangees. La garde du
premier test est donc vide aujourd'hui, et le dire vaut mieux que de le cacher.
C'est pourquoi le plancher anti-mutisme ne porte pas sur le nombre d'infractions
- il serait alors impossible a satisfaire - mais sur l'INSTRUMENT: on verifie
qu'il a vraiment lu des regles et des gabarits. Une garde qui ne trouve rien
parce qu'il n'y a rien, et une garde qui ne trouve rien parce qu'elle est
cassee, sont deux etats differents; celle-ci les distingue.
"""

from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web"
STATIQUE = RACINE / "static"
GABARITS = RACINE / "templates"

#: Une regle CSS `selecteur { corps }`, sans imbrication.
REGLE = re.compile(r"([^{}]+)\{([^{}]*)\}")
PISTES = re.compile(r"grid-template-rows\s*:\s*([^;}]+)")
JINJA = re.compile(r"\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}", re.DOTALL)

#: Un selecteur de la forme `.classe` seule, la seule que cette garde sait
#: rattacher a un element de gabarit sans se mentir. Tout le reste est compte
#: comme non mesure et annonce.
CLASSE_SEULE = re.compile(r"^\.([A-Za-z0-9_-]+)$")

#: Compteurs de l'instrument, remplis par `_classes_a_gabarit_fixe`. Ils servent
#: a distinguer `rien a signaler` de `la garde ne lit plus rien`.
REGLES_LUES = 0
SELECTEURS_LUS = 0


def _compte_pistes(valeur):
    """Combien de rangees ce gabarit declare-t-il, ou None s'il n'enumere pas."""
    valeur = valeur.strip()
    if valeur in {"none", "initial", "inherit", "unset"}:
        return None
    if "auto-fit" in valeur or "auto-fill" in valeur:
        return None  # le gabarit s'adapte deja au nombre d'enfants
    repete = re.search(r"repeat\(\s*(\d+)\s*,([^)]*)\)", valeur)
    if "repeat(" in valeur and not repete:
        return None  # forme de `repeat` que cette garde ne sait pas compter
    pistes, profondeur, courant = 0, 0, ""
    for caractere in valeur:
        if caractere == "(":
            profondeur += 1
        elif caractere == ")":
            profondeur -= 1
        if caractere.isspace() and profondeur == 0:
            if courant:
                pistes += 1
                courant = ""
            continue
        courant += caractere
    if courant:
        pistes += 1
    if repete:
        pistes += int(repete.group(1)) * max(1, len(repete.group(2).split())) - 1
    return pistes or None


def _classes_a_gabarit_fixe():
    """Les classes dont le CSS enumere les rangees, et les selecteurs non mesures."""
    fixes = {}
    non_mesures = []
    global REGLES_LUES, SELECTEURS_LUS
    REGLES_LUES = SELECTEURS_LUS = 0
    for feuille in sorted(STATIQUE.glob("styles_part_*.css")):
        texte = feuille.read_text(encoding="utf-8")
        for regle in REGLE.finditer(texte):
            REGLES_LUES += 1
            SELECTEURS_LUS += len(regle.group(1).split(","))
            trouve = PISTES.search(regle.group(2))
            if not trouve:
                continue
            pistes = _compte_pistes(trouve.group(1))
            if pistes is None:
                continue
            for selecteur in regle.group(1).split(","):
                selecteur = " ".join(selecteur.split())
                classe = CLASSE_SEULE.match(selecteur)
                if not classe:
                    non_mesures.append(feuille.name + ": " + selecteur)
                    continue
                # La derniere declaration l'emporte, comme dans le navigateur.
                fixes[classe.group(1)] = (pistes, feuille.name + ": " + selecteur)
    return fixes, non_mesures


class _Enfants(HTMLParser):
    """Compte les enfants directs de chaque element portant une des classes visees."""

    VIDES = {"br", "hr", "img", "input", "link", "meta", "source", "col", "area"}

    def __init__(self, classes):
        super().__init__(convert_charrefs=True)
        self._classes = classes
        self._pile = []
        self.trouves = []

    def handle_starttag(self, tag, attrs):
        if self._pile:
            self._pile[-1]["enfants"] += 1
        if tag in self.VIDES:
            return
        portees = set((dict(attrs).get("class") or "").split()) & self._classes
        self._pile.append({"tag": tag, "enfants": 0, "portees": portees})

    def handle_endtag(self, tag):
        for rang in range(len(self._pile) - 1, -1, -1):
            if self._pile[rang]["tag"] == tag:
                ferme = self._pile[rang]
                del self._pile[rang:]
                for classe in ferme["portees"]:
                    self.trouves.append((classe, ferme["enfants"]))
                return


class UnGabaritDeRangeesNEnumerePasLesEnfants(unittest.TestCase):
    def setUp(self):
        self.fixes, self.non_mesures = _classes_a_gabarit_fixe()

    def test_aucun_conteneur_ne_recoit_plus_d_enfants_que_son_gabarit_de_rangees(self):
        trop_pleins = []
        mesures = 0
        for gabarit in sorted(GABARITS.rglob("*.html")):
            analyseur = _Enfants(set(self.fixes))
            analyseur.feed(JINJA.sub("", gabarit.read_text(encoding="utf-8")))
            for classe, enfants in analyseur.trouves:
                mesures += 1
                pistes, source = self.fixes[classe]
                if enfants > pistes:
                    trop_pleins.append(
                        "`." + classe + "` declare " + str(pistes) + " rangee(s) dans "
                        + source + ", mais " + gabarit.name + " lui donne " + str(enfants)
                        + " blocs. Le bloc en trop herite d'une rangee qui peut s'ecraser a "
                        "zero, et son contenu se peint alors par-dessus le suivant."
                    )

        self.assertEqual(
            trop_pleins,
            [],
            msg=(
                "Un gabarit de rangees enumere moins de pistes qu'il ne recoit de blocs. "
                "Ne rallongez pas la liste: c'est encore compter les enfants. Nommez le "
                "bloc qui absorbe la place restante - une colonne flex ou une piste "
                "explicite sur ce bloc - pour que le nombre de blocs cesse d'etre une "
                "hypothese du style.\n  " + "\n  ".join(trop_pleins)
            ),
        )

    def test_l_instrument_lit_vraiment_les_feuilles_et_les_gabarits(self):
        """Distinguer `rien a signaler` de `la garde ne lit plus rien`.

        Le test precedent est vide aujourd'hui, et c'est le bon etat: plus aucun
        conteneur n'enumere ses rangees. Un plancher pose sur ses infractions
        serait donc impossible a satisfaire. Le plancher porte ici sur ce que
        l'instrument a REELLEMENT parcouru, seule facon de savoir qu'un vert
        signifie quelque chose.
        """
        self.assertGreaterEqual(
            REGLES_LUES,
            300,
            "La garde ne lit plus les feuilles de style: elle passerait au vert sans rien "
            "regarder. Verifiez l'emplacement des `styles_part_*.css` ou le decoupage des "
            "regles.",
        )
        gabarits = list(GABARITS.rglob("*.html"))
        self.assertGreaterEqual(
            len(gabarits),
            20,
            "La garde ne trouve plus les gabarits: meme vert, elle ne prouve rien.",
        )
        avec_panneau = [
            g for g in gabarits if "cs-rappro-queue-panel" in g.read_text(encoding="utf-8")
        ]
        self.assertGreaterEqual(
            len(avec_panneau),
            2,
            "Le panneau de file n'est plus partage par deux ecrans. Le defaut d'origine "
            "venait precisement de ce partage: si le partage disparait, dites-le ici "
            "plutot que de laisser la garde suggerer qu'elle protege encore ce cas.",
        )

    def test_le_panneau_de_file_ne_compte_plus_ses_blocs(self):
        """Le cas d'origine, garde nommement pour qu'une regression se lise vite."""
        self.assertNotIn(
            "cs-rappro-queue-panel",
            self.fixes,
            msg=(
                "`.cs-rappro-queue-panel` enumere de nouveau ses rangees. C'est le defaut "
                "du 2026-09-07: la barre de filtres de l'ecran de gouvernance se peignait "
                "par-dessus le tableau parce que le gabarit comptait deux blocs quand la "
                "page lui en donnait trois."
            ),
        )

    def test_le_bloc_qui_absorbe_la_place_restante_est_nomme(self):
        """La contrepartie du test precedent, et sans elle il serait piegeux.

        Retirer le gabarit de rangees suffirait a rendre le test ci-dessus vert,
        en laissant le tableau sans hauteur imposee - il ne defilerait plus dans
        son cadre, il s'etirerait et serait coupe. Ce qui doit tenir n'est pas
        l'absence de gabarit, c'est que le bloc absorbant soit DESIGNE par son
        nom au lieu d'etre repere par son rang. On verifie donc qu'une regle du
        style le nomme comme enfant du panneau.
        """
        feuilles = "\n".join(
            f.read_text(encoding="utf-8") for f in sorted(STATIQUE.glob("styles_part_*.css"))
        )
        nommes = [
            bloc
            for bloc in ("cs-rappro-table-scroll", "cs-rappro-queue-list")
            if re.search(r"\.cs-rappro-queue-panel\s*>\s*\." + bloc + r"\b", feuilles)
        ]
        self.assertEqual(
            sorted(nommes),
            ["cs-rappro-queue-list", "cs-rappro-table-scroll"],
            msg=(
                "Les blocs qui defilent ne sont plus designes comme enfants du panneau. "
                "Sans cette designation, la place restante revient au bloc qui se trouve "
                "la, et non a celui qui doit la prendre: c'est le rang qui decide, ce que "
                "ce lot a justement corrige."
            ),
        )


if __name__ == "__main__":
    unittest.main()
