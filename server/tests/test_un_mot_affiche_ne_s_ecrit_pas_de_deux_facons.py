# -*- coding: utf-8 -*-
"""Le produit n'ecrit pas le meme mot affiche avec et sans ses accents.

`RM-2026-0115`. L'item ne demandait pas de tout reecrire - il demandait
l'inverse: *poser la frontiere au lieu de tout reecrire: le code et les docs
peuvent rester sans accents, le texte AFFICHE ne doit pas*, et surtout
**mesurer le volume de chaines utilisateur concernees AVANT de choisir le
moyen**. Sa colonne preuve disait `a produire`. La voici.

**LA METHODE N'EMPLOIE AUCUN DICTIONNAIRE, et c'est deliberé.** Un
dictionnaire dirait ce que le francais veut; on veut savoir ce que le PRODUIT
veut. On le lui demande donc: une classe de mots est fautive quand le texte
affiche porte **ailleurs** le meme mot avec ses accents. Le produit prouve
alors lui-meme quelle forme est la bonne, et **une classe jamais ecrite
accentuee n'est pas accusee** - la mesure se degrade proprement au lieu de
deviner.

**MESURE DU 2026-09-12**, sur les 46 gabarits, avec l'instrument partage
`_texte_visible.py` (`RM-2026-0106`):

- **1 543** fragments de texte visible, **1 007** classes de mots;
- **33** classes seulement sont ecrites au moins une fois AVEC accents;
- **18** classes sont ecrites des DEUX facons, pour **216** occurrences nues.

**LA DISTRIBUTION DIT OU EST LE TRAVAIL, et elle est tres concentree.**
`pieces` (62 nues, 18 gabarits) et `piece` (44 nues, 19 gabarits) font **106
des 216 occurrences, soit la moitie**. Viennent ensuite `controle` (21),
`decision` (20), `decisions` (20), `resolutions` (11), `synthese` (10). La
queue - `depense`, `verifie`, `concernees`, `meme` - tient en une poignee.

**CE QUE CE LOT NE FAIT PAS, ET POURQUOI.** Il ne repare pas les 216
occurrences. L'instrument qui les COMPTE ne sait pas les SITUER: il rend du
texte, pas des positions, et un remplacement au motif dans le fichier brut
toucherait des identifiants - `res_vue.assemblees`, `vue.deja_reconnus`, la
classe CSS `coffre-model` - et des commentaires Jinja qui ne sortent jamais du
gabarit. **Choisir le moyen demande donc un instrument qui garde les offsets**,
et c'est exactement la decision que l'item voulait prendre apres la mesure,
pas avant.

**CE QUE CE LOT FAIT: il pose la frontiere.** Le compte est arrete. Un mot
affiche qui se met a s'ecrire des deux facons fait echouer ce test, donc
l'incoherence ne peut plus **croitre** pendant que la reparation attend. C'est
le sens litteral de la demande de l'item.

**L'AXE.** Ce qui VARIE: les mots, les ecrans, l'orthographe retenue par
chaque auteur. Ce qui reste INVARIANT: **le meme mot, vu par le meme
utilisateur, s'ecrit d'une seule facon.** **Hors des valeurs observees:** un
mot nouveau, dans une langue nouvelle, est couvert le jour ou il apparait sous
deux formes - la garde ne connait aucune liste de mots.
"""
from __future__ import annotations

import collections
import importlib.util
import re
import tempfile
import unicodedata
import unittest
from pathlib import Path

GABARITS = (Path(__file__).resolve().parents[1]
            / "src" / "coproscope" / "web" / "templates")

_SPEC = importlib.util.spec_from_file_location(
    "coproscope_tests_texte_visible",
    Path(__file__).resolve().with_name("_texte_visible.py"))
_TEXTE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_TEXTE)

MOT = re.compile(r"[A-Za-zÀ-ÿ]{3,}")

#: **ETAT DU 2026-09-12, APRES ELARGISSEMENT DE L'INSTRUMENT et non apres
#: reparation.** Les bornes precedentes - 18 classes, 216 occurrences - ont ete
#: mesurees avec un instrument qui ne voyait ni les paragraphes, ni les cellules
#: de tableau, ni les etiquettes de formulaire, ni **le texte porte par les
#: attributs**, c'est-a-dire celui qu'un lecteur d'ecran prononce. Les trois
#: defauts sont corriges dans `_texte_visible.py`; le defaut visible n'a pas
#: grandi, **c'est la mesure qui a cesse de le sous-estimer.**
#:
#: **LA REPARATION A ETE FAITE, MESUREE, PUIS DEFAITE, et le cout est le
#: livrable.** 359 occurrences remplacees dans 35 gabarits, aux positions
#: situees. La suite complete a alors rendu **73 echecs dans 33 fichiers de
#: test**, dont une garde de confidentialite qui annonce elle-meme *la
#: recherche ne filtre pas: le test ne prouve rien*. Ce n'est donc pas une mise
#: a jour d'ancres: c'est un changement transverse du texte affiche, que la
#: doctrine du depot soumet a une recette sur page reelle - port reserve,
#: scenario clique, GO novice. L'arbitrage de l'item disait *mesurer le volume
#: AVANT de choisir le moyen*: le moyen est maintenant chiffre, et le choix
#: appartient a Brice.
#:
#: **POURQUOI LA REGLE DE LA MESURE NE PEUT PAS CONDUIRE LA REPARATION.** La
#: mesure accuse une classe quand le produit ecrit le meme mot plie des deux
#: facons: c'est juste pour DETECTER une incoherence. Mais le pliage des
#: accents **confond des mots differents**. Les classes mixtes contiennent donc
#: deux populations: (a) un seul mot ecrit de deux facons - `piece`/`pièce` -
#: reparable; (b) DEUX mots qui plient pareil, ou aucune regle mecanique ne
#: tranche. C'est la faute que le `CLAUDE.md` nomme *reduire a un scalaire ce
#: qui est une table*: le pliage a efface la dimension *quel mot*, et le compte
#: des classes mixtes fusionnait les deux populations sans qu'on puisse
#: remonter.
#:
#: **`votre` est la preuve que le refus n'est pas de la prudence de facade:**
#: la forme NUE y est le francais CORRECT, et une reparation mecanique
#: introduirait une faute dans un texte juste.
REFUSEES: dict[str, str] = {
    # `comptes` est sorti le 2026-09-13: la seule forme `comptés` affichee vivait
    # dans la note de bas de l'accueil de gouvernance, retiree par la recette
    # (`RM-2026-0183`). La classe n'est plus mixte, le refus n'a plus d'objet.
    "trace": "`une trace` (nom) plie comme `tracé` (participe)",
    "regarde": "`il regarde` (present) plie comme `regardé` (participe)",
    "verifie": "`se verifie` (present) plie comme `vérifié` (participe)",
    "votre": "`votre` est le francais CORRECT; `vôtre` est un autre mot",
}

#: Etat mesure le 2026-09-12 avec l'instrument corrige. Ces bornes ne sont pas
#: des tolerances: elles sont l'etat, et les deux sens rougissent.
#: Remesure le 2026-09-13: 32 -> 31 classes, 453 -> 308 occurrences, 428 -> 298
#: places. **Aucune reparation**: la baisse vient des 12 ecrans SUPPRIMES par la
#: recette de Brice (`RM-2026-0183`), dont les gabarits portaient ces formes.
#: Remesure le meme jour apres le lot 2 (groupe *Contrôle* du menu): 308 -> 305
#: occurrences, places inchangees a 298. Les deux entrees *Controle ...* du menu
#: sont parties, et les libelles neufs sont ecrits accentues.
#: Remesure apres le lot 4 (accueil de gouvernance): 31 -> 27 classes, 305 -> 283
#: occurrences, 298 -> 273 places. Aucune reparation: les notes de bas retirees
#: portaient les seules formes accentuees de `comptes`, `concernees`, `donnee` et
#: `selection`. Les textes neufs evitent d'accentuer `verifier` et `priorite`,
#: que 48 occurrences nues ecrivent sans accent ailleurs: les accentuer ici
#: aurait fait monter la dette de 30. Tour 2 du meme lot (retours novice et
#: expert): 283 -> 282 occurrences, 273 -> 272 places.
CLASSES_MIXTES = 27
OCCURRENCES_NUES = 282
#: Le nombre de PLACES - positions distinctes dans les fichiers - que la
#: localisation rend, c'est-a-dire **ce qu'une reparation devrait toucher**. Il
#: ne vaut pas `OCCURRENCES_NUES`, et la raison est ecrite dans
#: `test_les_deux_instruments_ne_repondent_PAS_a_la_meme_question`.
PLACES_SITUEES = 272


def _plie(mot: str) -> str:
    decompose = unicodedata.normalize("NFKD", mot.lower())
    return "".join(c for c in decompose if not unicodedata.combining(c))


def _mesure() -> tuple[int, int, int, list[str]]:
    """Fragments, classes, et les classes ecrites des deux facons."""
    formes: dict[str, set[str]] = collections.defaultdict(set)
    nues: collections.Counter = collections.Counter()
    fragments = 0
    for gabarit in sorted(GABARITS.glob("*.html")):
        for fragment in _TEXTE.fragments_visibles(gabarit):
            fragments += 1
            for mot in MOT.findall(fragment):
                classe = _plie(mot)
                formes[classe].add(mot.lower())
                if _plie(mot) == mot.lower():
                    nues[classe] += 1
    mixtes = sorted(
        classe for classe, variantes in formes.items()
        if any(_plie(v) != v for v in variantes)
        and any(_plie(v) == v for v in variantes))
    return fragments, len(formes), sum(nues[c] for c in mixtes), mixtes


class UN_MOT_AFFICHE_S_ECRIT_D_UNE_SEULE_FACON(unittest.TestCase):
    def test_l_instrument_lit_bien_les_gabarits(self) -> None:
        """Sans cela, un compte tombe a zero passerait pour une reparation."""
        fragments, classes, _, _ = _mesure()
        self.assertGreater(
            fragments, 1000,
            "l'instrument ne lit presque rien: il est casse, et les comptes "
            "ci-dessous n'auraient aucun sens")
        self.assertGreater(classes, 500)

    def test_la_frontiere_ne_recule_pas(self) -> None:
        """La demande litterale de l'item: poser la frontiere.

        Un mot AFFICHE qui se met a s'ecrire des deux facons fait echouer ce
        test. L'incoherence ne peut donc plus croitre pendant que la
        reparation attend son moyen.
        """
        _, _, occurrences, mixtes = _mesure()
        self.assertLessEqual(
            len(mixtes), CLASSES_MIXTES,
            "un mot affiche de plus s'ecrit maintenant des deux facons, avec "
            "et sans ses accents. Le produit se contredit sur le meme mot "
            "devant le meme lecteur. Classes concernees: %s" % mixtes)
        self.assertLessEqual(
            occurrences, OCCURRENCES_NUES,
            "les occurrences nues de mots que le produit ecrit accentues "
            "ailleurs ont augmente (%d pour une borne de %d)."
            % (occurrences, OCCURRENCES_NUES))

    def test_les_refus_declares_sont_TOUS_encore_mixtes(self) -> None:
        """Une liste de refus se VERIFIE, elle ne se consulte pas.

        Un refus qui cesse d'etre mixte est une declaration perimee: elle dit
        au lecteur qu'un mot est irreparable alors qu'il ne pose plus de
        probleme. Sans ce sens inverse, la liste deviendrait un cimetiere ou
        l'on range ce qui gene.
        """
        _, _, _, mixtes = _mesure()
        perimes = sorted(classe for classe in REFUSEES if classe not in mixtes)
        self.assertEqual(
            [], perimes,
            "ces classes sont declarees irreparables et ne sont plus ecrites "
            "des deux facons: retirer l'entree, sinon le refus survit a son "
            "motif: %s" % perimes)

    def test_chaque_refus_dit_QUELS_deux_mots_le_pliage_confond(self) -> None:
        """Un refus sans raison serait une permission de se taire."""
        for classe, raison in sorted(REFUSEES.items()):
            with self.subTest(classe=classe):
                self.assertGreater(
                    len(raison), 40,
                    "la raison est trop courte pour nommer la confusion")
                self.assertIn(
                    "`", raison,
                    "la raison ne cite aucune des deux formes: on ne pourra "
                    "pas verifier le refus sans refaire l'analyse")

    def test_RESIDU_la_dette_est_bornee_et_se_redit_quand_elle_baisse(self) -> None:
        """Le pendant du test precedent: une dette qui baisse se declare.

        Sans cela, une reparation partielle laisserait la borne haute, et la
        frontiere se remettrait a reculer en silence jusqu'a l'ancien niveau.
        """
        _, _, occurrences, mixtes = _mesure()
        self.assertEqual(
            (CLASSES_MIXTES, OCCURRENCES_NUES), (len(mixtes), occurrences),
            "la dette a baisse: %d classes et %d occurrences au lieu de %d et "
            "%d. Mettre ces bornes a jour, avec la date - sinon la frontiere "
            "peut reculer jusqu'a l'ancien niveau sans que rien ne le dise."
            % (len(mixtes), occurrences, CLASSES_MIXTES, OCCURRENCES_NUES))

    def test_les_PLACES_a_reparer_sont_denombrees(self) -> None:
        """Ce que la reparation devra toucher, position par position.

        C'est ce chiffre-la qui dit le travail restant, et non le compte
        d'occurrences: une occurrence peut apparaitre dans deux fragments qui
        se recouvrent, et un meme libelle repete n'est compte qu'une fois.
        """
        _, _, _, mixtes = _mesure()
        places = sum(
            1
            for gabarit in sorted(GABARITS.glob("*.html"))
            for _ligne, _colonne, texte in _TEXTE.occurrences_situees(gabarit, MOT)
            if _plie(texte) in mixtes and _plie(texte) == texte.lower()
        )
        self.assertEqual(
            PLACES_SITUEES, places,
            "le nombre de PLACES a reparer a change (%d pour %d declarees). "
            "Mettre la borne a jour avec la date, dans les deux sens."
            % (places, PLACES_SITUEES))

    def test_les_deux_instruments_ne_repondent_PAS_a_la_meme_question(self) -> None:
        """Deux comptages pour une notion se COMPARENT, ils ne se supposent pas.

        **Mesure du 2026-09-12, et elle a failli etre publiee a l'envers.** A
        un moment de la reparation les deux totaux sont tombes sur le meme
        chiffre - 117 contre 117 - et j'ai pris cela pour un accord. C'etait
        une COINCIDENCE: les ecarts par fichier vont dans les deux sens et se
        compensaient.

        Les deux instruments repondent a deux questions differentes, et la
        difference est structurelle, pas accidentelle:

        - le comptage parcourt les FRAGMENTS, qui sont dedupliques par leur
          texte: un meme libelle repete dix fois dans un ecran n'est compte
          qu'une fois;
        - la localisation parcourt les POSITIONS: elle voit les dix.

        Et en sens inverse, `CORPS_COURTS` et `CORPS_LARGES` se recouvrent a
        dessein, donc une meme zone peut rendre deux fragments distincts et
        faire compter deux fois un mot qui n'occupe qu'une place.

        Ce test ne les force donc pas a s'accorder: il verifie que l'ecart
        reste celui qui a ete mesure et explique. Un ecart qui bouge est une
        information, pas un detail a lisser.
        """
        _, _, _, mixtes = _mesure()
        en_plus_au_comptage = 0
        en_plus_a_la_localisation = 0
        for gabarit in sorted(GABARITS.glob("*.html")):
            compte = 0
            for fragment in _TEXTE.fragments_visibles(gabarit):
                for mot in MOT.findall(fragment):
                    if _plie(mot) in mixtes and _plie(mot) == mot.lower():
                        compte += 1
            situe = sum(
                1 for _l, _c, texte in _TEXTE.occurrences_situees(gabarit, MOT)
                if _plie(texte) in mixtes and _plie(texte) == texte.lower())
            en_plus_au_comptage += max(0, compte - situe)
            en_plus_a_la_localisation += max(0, situe - compte)

        self.assertGreater(
            en_plus_au_comptage, 0,
            "plus aucun fichier ne fait compter un mot que la localisation ne "
            "situe pas: le recouvrement voulu de `CORPS_COURTS` et "
            "`CORPS_LARGES` a disparu, ou la deduplication des fragments a "
            "change. Ce n'est pas forcement un defaut, mais ce n'est plus "
            "l'instrument mesure ici.")
        self.assertGreater(
            en_plus_a_la_localisation, 0,
            "plus aucun fichier ne fait situer un mot que le comptage ne "
            "compte pas: la deduplication des fragments par leur texte a "
            "disparu. La relire avant de croire que les deux instruments "
            "mesurent la meme chose.")

    def test_un_mot_jamais_ecrit_accentue_n_est_PAS_accuse(self) -> None:
        """Temoin de la methode: elle ne devine pas le francais.

        `resolution` sans accent serait fautif pour un dictionnaire. Ici il
        n'est retenu que parce que le produit ecrit `resolution` accentue
        ailleurs. Un mot comme `depot`, si le produit ne l'accentuait nulle
        part, ne serait pas accuse - et c'est ce qui rend la mesure
        publiable.
        """
        _, _, _, mixtes = _mesure()
        formes: dict[str, set[str]] = collections.defaultdict(set)
        for gabarit in sorted(GABARITS.glob("*.html")):
            for fragment in _TEXTE.fragments_visibles(gabarit):
                for mot in MOT.findall(fragment):
                    formes[_plie(mot)].add(mot.lower())
        for classe in mixtes:
            with self.subTest(classe=classe):
                self.assertTrue(
                    any(_plie(v) != v for v in formes[classe]),
                    "cette classe est accusee sans que le produit ecrive "
                    "jamais le mot accentue: la methode devine")


class L_INSTRUMENT_SITUE_CE_QUE_L_UTILISATEUR_LIT(unittest.TestCase):
    """Temoins des trois defauts corriges le 2026-09-12 dans `_texte_visible`.

    Sans eux, les trois reparations seraient des affirmations. Chacun ECHOUE
    avec la version precedente de l'instrument, et c'est ce qui les rend utiles
    plutot que decoratifs.
    """

    def _situe(self, source: str) -> list[str]:
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "essai.html"
            chemin.write_text(source, encoding="utf-8")
            return [texte for _l, _c, texte
                    in _TEXTE.occurrences_situees(chemin, MOT)]

    def test_le_texte_porte_par_un_ATTRIBUT_est_situe(self) -> None:
        """Le defaut le plus grave: il effacait tout ce qu'un lecteur d'ecran dit.

        Les attributs etaient marques AVANT le retrait des balises, or la
        valeur d'un `aria-label` vit A L'INTERIEUR de la balise: `<[^>]+>` la
        reeffacait aussitot. Mesure du 2026-09-12: `aria-label="Atelier
        pieces, relier piece, point, action et preuve"` dans `base.html`
        n'etait situe nulle part.
        """
        situes = self._situe('<a aria-label="Atelier pieces relier">x</a>')
        self.assertIn("Atelier", situes)
        self.assertIn("pieces", situes)

    def test_une_ENTITE_html_n_est_pas_un_mot(self) -> None:
        """`&nbsp;` parvient au lecteur comme une ESPACE, jamais comme `nbsp`."""
        self.assertNotIn("nbsp", self._situe("<p>a&nbsp;b et aussi ceci</p>"))

    def test_un_paragraphe_et_une_cellule_sont_des_vehicules(self) -> None:
        """La liste des vehicules etait une enumeration de ce qui avait ete vu."""
        situes = self._situe(
            "<p>paragraphe</p><td>cellule</td><label>etiquette</label>"
            "<li>element</li>")
        for attendu in ("paragraphe", "cellule", "etiquette", "element"):
            with self.subTest(mot=attendu):
                self.assertIn(attendu, situes)

    def test_un_identifiant_et_une_classe_CSS_ne_sont_PAS_situes(self) -> None:
        """Le danger que l'item nommait: un remplacement au motif les toucherait.

        C'est ce temoin qui rend la reparation sure, et sans lui les trois
        precedents pousseraient a elargir le masque sans borne.
        """
        situes = self._situe(
            '<span class="coffre-model">{{ res_vue.assemblees }}'
            "{# commentaire avec pieces dedans #}visible</span>")
        self.assertIn("visible", situes)
        for interdit in ("coffre", "model", "res_vue", "assemblees",
                         "commentaire", "pieces", "dedans"):
            with self.subTest(mot=interdit):
                self.assertNotIn(interdit, situes)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
