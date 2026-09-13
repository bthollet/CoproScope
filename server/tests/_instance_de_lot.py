# -*- coding: utf-8 -*-
"""Trouver une instance de travail par ce qu'elle PORTE, jamais par son nom.

**Deux regles du depot se contredisaient, et la contradiction eteignait des
tests en silence.**

- La doctrine impose de **supprimer l'instance de lot a la fin du chantier**:
  *une instance de lot qui survit devient, quelques semaines plus tard, une
  instance historique que quelqu'un prendra pour une reference.*
- Plusieurs gardes nommaient cette instance **en dur** pour decider si elles
  pouvaient mesurer.

Consequence mecanique: **toute garde qui nomme une instance de lot est morte le
jour ou la doctrine est appliquee.** Ce n'est pas un oubli, c'est une garantie.

**Mesure du 2026-09-09.** `instances/lot_factures_20260908` n'existe plus, et
quatre modules en dependaient: **12 tests sur 35 sautaient**, les modules
rendant `OK (skipped=12)`. Sur les 18 sauts de toute la suite, **12 venaient de
ce seul motif**.

**L'axe.** Ce qui varie: le nom du lot, sa date, son sujet, combien de temps il
survit. Ce qui reste invariant: **une instance utilisable se reconnait a ce
qu'elle CONTIENT**, pas a son nom. On cherche donc les pieces que la mesure va
lire, exprimees par le motif que le test globe ensuite.

---

# Ce que la premiere reparation laissait passer, mesure sur `913d744`

`RM-2026-0150` dit que **le verdict de la suite depend de l'instant ou l'on
efface un dossier**. Chercher par les pieces au lieu du nom a supprime la
premiere forme du defaut - le dossier VIDE qui laissait passer la garde - mais
**trois autres formes survivaient, et toutes ont ete reproduites**.

**(A) La garde est evaluee a l'IMPORT, la piece est lue a l'EXECUTION.**
`_INSTANCE = instance_portant(...)` s'evalue au chargement du module; le
`setUpClass` globe des minutes plus tard. Une instance effacee dans cet
intervalle - et la suite dure une dizaine de minutes, pendant qu'un autre lot
applique la doctrine - ne donne pas un saut: elle donne un `StopIteration` nu.
**Reproduit:** `lecture a l'execution: StopIteration -> ERREUR, et non un saut`.
C'est mot pour mot l'incident d'origine, resserre de deux passages a un seul.

**(B) L'ancienne selection tranchait l'ambiguite au lieu de la declarer.**
La version precedente finissait par `max(candidates, key=mtime)` et son
docstring l'assumait: *« on prend la plus recemment ecrite de celles qui les
portent »*. **Cette phrase est ici contredite, et c'est deliberé.** Deux
instances portant les memes pieces sont deux corpus differents; prendre la plus
recente **repond a une question qu'on n'a pas posee**. Reproduit sur deux
corpus bidons: un simple `touch` sur le perdant deplace la mesure de `CORPUS B`
a `CORPUS A`, **sans qu'une ligne de test ait change**. C'est la serie B de
`RM-2026-0172` - *sur quoi la mesure a-t-elle reellement porte ?* - et la
reponse etait: sur le dossier touche en dernier.

Le poste porte deja le cas: **trois instances** rendent des fichiers pour
`staging/text/*.txt`, dont celle de 858 pieces d'un tout autre corpus qui avait
fait rendre 11 echecs et 3 erreurs a la premiere version.

**(C) La garde exige UNE piece, la mesure en consomme N.**
`_porte_tout` se contentait de `any(...glob(motif))`. Une copie interrompue -
un exercice sur quatre - passe la garde, et la mesure tourne sur un corpus
incomplet **en silence**, ce qui est pire qu'un saut: le chiffre a l'air d'une
preuve. Serie A de `RM-2026-0172`.

**Ce defaut-la n'est PAS ferme ici, et il faut le dire.** Un module ne peut pas
savoir combien de pieces *devraient* exister sans qu'on le lui declare, et un
plancher chiffre code dans cette aide serait une modalite qui pourrira au
premier corpus different. Ce qui est fait est le remede (b) du document
`docs/verdict_contredit_par_ses_propres_faits_2026-09-09.md`: **rendre le fait
impossible a contourner**. Le compte de pieces retenues est imprime au journal
a cote du verdict, si bien qu'un corpus a 3 pieces la ou le lecteur en attend
341 se voit. C'est un fait affiche, pas une garantie, et c'est le residu connu
de ce lot.

**CE PARAGRAPHE DISAIT FAUX, ET LA MESURE QUI LE REFUTE EST DATEE DU
2026-09-09.** Le compte imprime n'etait PAS celui des pieces retenues: c'etait
celui des motifs de **SELECTION**, et deux modules selectionnent sur un motif
puis lisent sur un autre. Une instance portant **une** reddition et **cent**
pieces etrangeres annoncait au journal `staging/text/*REDDITION*.txt: 1`
pendant que la mesure en lisait **101**. Le remede propose ne couvrait donc pas
le cas qu'il pretendait rendre visible - c'est-a-dire justement le corpus
etranger de 858 pieces cite deux paragraphes plus haut. **Corrige:** `pieces()`
imprime maintenant `[lu] ... <motif>: N` au moment ou elle lit, avec le compte
reellement consomme. Le residu qui subsiste est plus etroit et se nomme: un
corpus qui RETRECIT entre l'import et la lecture voit son compte de selection
imprime avant, et son compte de lecture imprime apres - les deux lignes sont au
journal, rien ne les reconcilie automatiquement.

**(D) Le saut declare, la reussite se tait.**
Le motif de saut nommait ce qui n'avait pas ete verifie - c'etait juste. Mais le
chemin qui MESURE ne disait pas **sur quoi**. `RM-2026-0172` conclut pourtant:
*toute mesure doit porter l'identite de sa base, pas seulement son resultat.*
La garde respectait la regle du cote de l'echec et la violait du cote du succes.

# Ce que ce module garantit maintenant

**Le verdict ne depend plus de l'instant.** Efface avant l'import, pendant la
mesure ou apres: on obtient toujours une **non-mesure declaree**, jamais une
erreur opaque et jamais un vert muet. Les deux passages du meme code rendent le
meme verdict, et ce verdict nomme ce qui n'a pas ete verifie.

**L'ambiguite est declaree, pas tranchee.** Plusieurs instances portent les
pieces: la mesure ne sait pas de quel corpus elle parle, donc elle ne mesure
pas, et elle nomme les candidates.

**Et on peut lui DIRE laquelle**, sans rien supprimer. Declarer l'ambiguite
sans offrir ce geste rendait la mesure otage du menage: mesure du 2026-09-09,
deux copies de l'etalon sous la racine font tomber `test_confrontation_etalon_corpus`
de `Ran 6, OK` a `OK (skipped=4)`, alors que `RM-2026-0150` demande justement
d'en rebatir une seconde pour la confronter. `COPROSCOPE_TEST_INSTANCE` tranche;
`COPROSCOPE_TEST_INSTANCES` deplace la racine. Une designation qui echoue **ne
retombe jamais** sur la decouverte automatique: elle se declare.

**La reussite porte l'identite de sa base**, imprimee au journal a cote du `OK`,
et le compte des pieces **lues** est imprime au moment ou elles sont lues.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

#: La racine des instances privees du poste. Hors depot: la CI n'y a pas acces,
#: et c'est pour cela que ces mesures ne peuvent pas etre des preuves de CI.
RACINE_INSTANCES = Path.home() / "CoproScope" / "instances"

#: **On peut DIRE a la mesure ou sont les donnees.** Orientation de Brice,
#: citee dans `RM-2026-0150`: *"il faut parametriser l'instance sur laquelle
#: les tests se deroulent. Quand c'est pertinent."* et *"Un test ne devrait
#: pas savoir OU sont les donnees: on devrait pouvoir le lui dire, et il se
#: tait proprement - en le disant - quand on ne le lui dit pas."*
#:
#: **Ce que la decouverte automatique seule ne peut pas faire.** Elle refuse de
#: trancher entre deux instances portant les memes pieces - et elle a raison,
#: deux corpus ne se departagent pas au hasard. Mais les seuls gestes qu'elle
#: laissait alors etaient *supprimer un corpus* ou *modifier le test*. Mesure du
#: 2026-09-09: deux copies de l'etalon sous la racine font passer
#: `test_confrontation_etalon_corpus` de `Ran 6, OK` a `OK (skipped=4)` - et
#: `RM-2026-0150` demande justement d'en rebatir une seconde pour la confronter.
#: Le troisieme geste manquait: **dire laquelle**.
VAR_INSTANCE = "COPROSCOPE_TEST_INSTANCE"
VAR_RACINE = "COPROSCOPE_TEST_INSTANCES"


def _pieces_de(instance: Path, motif: str) -> list[Path]:
    """Les fichiers que ce motif rend dans cette instance, a CET instant."""
    try:
        return sorted(p for p in instance.glob(motif) if p.is_file())
    except OSError:
        return []


def _candidates(
    racine: Path, motifs: tuple[str, ...], designee: Path | None = None
) -> list[Path]:
    """Les instances qui portent AU MOINS une piece pour CHACUN des motifs.

    Quand une instance est DESIGNEE, elle est la seule examinee: une
    designation explicite qui echoue ne se rattrape jamais par une decouverte
    automatique. Retomber sur une autre instance ferait mesurer un corpus que
    personne n'a demande, sans le dire - le defaut meme de `RM-2026-0150`.
    """
    if not motifs:
        return []
    if designee is not None:
        return [designee] if all(_pieces_de(designee, m) for m in motifs) else []
    try:
        if not racine.is_dir():
            return []
        enfants = sorted(d for d in racine.iterdir() if d.is_dir())
    except OSError:
        return []
    return [d for d in enfants if all(_pieces_de(d, m) for m in motifs)]


class Corpus:
    """Une instance resolue, qui **se relit au moment ou la mesure la lit**.

    Le point important n'est pas ce qu'elle rend quand tout va bien: c'est
    qu'elle rend la MEME chose - une non-mesure declaree - que le dossier ait
    disparu avant l'import ou pendant la mesure.
    """

    def __init__(
        self,
        racine: Path,
        motifs: tuple[str, ...],
        mesure: str,
        designee: Path | None = None,
    ) -> None:
        self.racine = racine
        self.motifs = motifs
        self.mesure = mesure
        self.designee = designee
        self._candidates = _candidates(racine, motifs, designee)
        self.instance: Path | None = (
            self._candidates[0] if len(self._candidates) == 1 else None
        )
        #: Les motifs deja annonces au journal, pour ne pas repeter la ligne.
        self._annonces: set[str] = set()

    # -- decider ----------------------------------------------------------
    @property
    def mesurable(self) -> bool:
        """Une et une seule instance porte les pieces que la mesure exige."""
        return self.instance is not None

    @property
    def motif_de_saut(self) -> str:
        """Ce qui n'a PAS ete verifie, et pourquoi. Jamais un `OK` muet.

        Deux causes distinctes, parce qu'elles appellent deux gestes
        differents: *aucune instance ne porte les pieces* se repare en
        absorbant un corpus; *plusieurs les portent* se repare en disant
        laquelle, ou en resserrant le motif.
        """
        pieces = " et ".join("`%s`" % m for m in self.motifs)
        if self.designee is not None:
            return (
                "MESURE NON FAITE, INSTANCE DESIGNEE INSUFFISANTE: `%s=%s` ne "
                "porte pas %s. Aucune autre instance n'est cherchee: une "
                "designation explicite qui echoue ne se rattrape pas en "
                "silence, sinon la mesure porterait sur un corpus que personne "
                "n'a demande. Ce qui n'est donc PAS verifie ici: %s."
                % (VAR_INSTANCE, self.designee, pieces, self.mesure)
            )
        if len(self._candidates) > 1:
            noms = ", ".join(d.name for d in self._candidates)
            return (
                "MESURE NON FAITE, BASE AMBIGUE: %d instances de %s portent %s "
                "(%s). Deux instances portant les memes pieces sont deux corpus "
                "differents: prendre la plus recente repondrait a une question "
                "qu'on n'a pas posee. Ce qui n'est donc PAS verifie ici: %s. "
                "Pour le mesurer, DIRE laquelle avec `%s=<chemin>`: c'est le "
                "geste que l'orientation de `RM-2026-0150` demande, et il ne "
                "detruit ni ne renomme rien."
                % (len(self._candidates), self.racine, pieces, noms,
                   self.mesure, VAR_INSTANCE)
            )
        return (
            "MESURE NON FAITE: aucune instance de %s ne porte %s. Ce qui n'est "
            "donc PAS verifie ici: %s. Pour le mesurer, absorber le corpus voulu "
            "dans une instance de travail portant ces pieces."
            % (self.racine, pieces, self.mesure)
        )

    @property
    def identite(self) -> str:
        """La base de la mesure, a mettre a cote de son resultat.

        `RM-2026-0172`: *toute mesure doit porter l'identite de sa base, pas
        seulement son resultat.* Un `OK` qui ne dit pas sur quel corpus il porte
        n'est pas refutable.
        """
        if self.instance is None:
            return "aucune"
        compte = ", ".join(
            "%s: %d" % (m, len(_pieces_de(self.instance, m))) for m in self.motifs
        )
        return "instance `%s` (%s)" % (self.instance.name, compte)

    # -- lire -------------------------------------------------------------
    def pieces(self, motif: str) -> list[Path]:
        """Les fichiers, **reglobes maintenant**, jamais une liste vide muette.

        C'est ici que se ferme le trou (A): entre la garde et cet appel, le
        dossier a pu disparaitre. Il en sort un saut qui NOMME la disparition -
        distincte d'une absence ordinaire, parce qu'elle n'arrive jamais par
        hasard - au lieu d'un `StopIteration` nu.

        Elle ferme aussi le cas VIDE: une liste vide a la lecture n'est pas un
        corpus qu'on parcourt sans assertion, c'est une non-mesure. Elle ne
        ferme pas le cas PARTIEL - voir (C) en tete de module.
        """
        if self.instance is None:
            raise unittest.SkipTest(self.motif_de_saut)
        trouves = _pieces_de(self.instance, motif)
        if trouves and motif not in self._annonces:
            # **Le compte annonce doit etre celui que la mesure CONSOMME.**
            # `identite` ne compte que les motifs de SELECTION, et deux modules
            # selectionnent sur un motif puis lisent sur un autre. Mesure du
            # 2026-09-09: une instance portant une reddition et cent pieces
            # etrangeres annoncait `*REDDITION*.txt: 1` au journal pendant que
            # la mesure en lisait 101. Le fait affiche n'etait pas le fait
            # consomme - or c'est ce fait-la qui devait rendre visible un
            # corpus a 3 pieces la ou le lecteur en attend 341.
            self._annonces.add(motif)
            print(
                "[lu] %s: instance `%s` %s: %d"
                % (self.mesure, self.instance.name, motif, len(trouves)),
                file=sys.stderr,
            )
        if not trouves:
            raise unittest.SkipTest(
                "MESURE INTERROMPUE: `%s` ne rend plus aucune piece dans `%s`, "
                "alors que la garde en avait trouve au chargement du module. Le "
                "corpus a disparu ou change PENDANT la mesure - c'est le defaut "
                "de `RM-2026-0150`, pas un alea. Ce qui n'est donc PAS verifie "
                "ici: %s." % (motif, self.instance.name, self.mesure)
            )
        return trouves

    def une_piece(self, motif: str) -> Path:
        """La piece unique attendue par la mesure. Plusieurs = base ambigue."""
        trouves = self.pieces(motif)
        if len(trouves) > 1:
            raise unittest.SkipTest(
                "MESURE NON FAITE, PIECE AMBIGUE: `%s` rend %d fichiers dans "
                "`%s` (%s) alors que la mesure en attend un seul. Ce qui n'est "
                "donc PAS verifie ici: %s."
                % (motif, len(trouves), self.instance.name,
                   ", ".join(p.name for p in trouves), self.mesure)
            )
        return trouves[0]

    def textes(self, motif: str) -> dict[str, str]:
        """`{stem: contenu}`, non vide par construction."""
        return {p.stem: p.read_text(encoding="utf-8") for p in self.pieces(motif)}


def corpus_portant(*motifs: str, mesure: str) -> Corpus:
    """Le corpus que cette mesure exige - ou une non-mesure qui se declare.

    `mesure` dit **ce qui ne sera pas verifie** si le corpus manque. Ce n'est
    pas un commentaire: c'est ce qui empeche un `OK (skipped=N)` de passer pour
    un succes.

    **Une version anterieure demandait des DOSSIERS non vides, et c'etait trop
    faible.** `staging/text` a designe une instance de 858 fichiers d'un tout
    autre corpus: les modules degeles ont rendu **11 echecs et 3 erreurs**. Le
    nom designait trop peu d'instances, le dossier en designait trop. Ce qui
    identifie une instance utilisable, c'est **la piece que la mesure va
    chercher** - et le test la connait deja, puisqu'il la globe ensuite.
    """
    designee = os.environ.get(VAR_INSTANCE) or None
    racine = os.environ.get(VAR_RACINE) or None
    corpus = Corpus(
        Path(racine) if racine else RACINE_INSTANCES,
        motifs,
        mesure,
        designee=Path(designee) if designee else None,
    )
    if corpus.mesurable:
        # La base, au journal, a cote du `OK`. Sur stderr, la ou unittest ecrit.
        print("[base] %s: %s" % (mesure, corpus.identite), file=sys.stderr)
    return corpus


def instances_portant(*motifs: str) -> list[Path]:
    """Toutes les candidates, pour un appelant qui veut trancher lui-meme."""
    return _candidates(RACINE_INSTANCES, motifs)


__all__ = [
    "Corpus",
    "corpus_portant",
    "instances_portant",
    "RACINE_INSTANCES",
    "VAR_INSTANCE",
    "VAR_RACINE",
]
