# -*- coding: utf-8 -*-
"""Un ecran promet ce qu'un chemin du produit peut produire.

Instruction de `RM-2026-0059`. La garde soeur
`test_ecrans_sans_instance_declarent_leur_nature` couvre les huit ecrans qui
n'ont **aucun canal d'entree**: leur constructeur ne prend que des scalaires,
donc ils ne peuvent rien lire, et ils le declarent. Ce fichier couvre l'autre
moitie de l'item, et c'est la plus sournoise.

**Le defaut vise.** Un ecran qui a bien un canal d'entree, qui lit vraiment une
table, et dont la table ne sera jamais remplie parce qu'AUCUN chemin du produit
ne l'ecrit. Un ecran sans canal affiche une maquette, et une maquette se
reconnait. Un ecran branche sur une table que personne n'ecrit affiche
`aucune depense rattachee` ou `A instruire`: la forme exacte d'un CONSTAT sur la
copropriete. Le lecteur lit un fait, la verite est un etat de l'outil.

**Un chemin qui n'existe que dans un test n'est pas un chemin.** C'est le
critere de l'item, et c'est lui qui commande la forme de l'instrument.

----------------------------------------------------------------------
L'instrument, et pourquoi il n'est pas un grep
----------------------------------------------------------------------

La question *quel chemin du produit ecrit cette table* a une reponse textuelle
tentante: chercher `ecrire(`, ou le nom de la table, dans `src/`. Ce serait
coder des ORTHOGRAPHES - un nom construit par f-string, une table ecrite par une
couche partagee, un `executescript` disparaitraient sans un mot, et le compteur
rendrait un chiffre qui a l'air d'une preuve.

Ici c'est **SQLite qui repond**. Un autorisateur (`set_authorizer`) est pose sur
toute connexion ouverte vers le coffre de gouvernance, puis:

- la chaine de production reelle est jouee - `core.pipeline.run_pipeline`, le
  point d'entree que le produit utilise - et l'instrument note toute table
  visee par un INSERT, un UPDATE ou un DELETE. Ce sont les tables que le produit
  SAIT remplir;
- chaque ecran est ensuite construit, et l'instrument note toute table visee par
  un READ. SQLite deplie les vues jusqu'a leurs tables de base, donc lire
  `v_matrice_gouvernance` compte comme lire `actes_autorisation`,
  `liens_gouvernance` et `dossiers_depense`, sans que rien ait a le declarer.

Aucun nom de table, aucun nom de fonction et aucune orthographe de requete
n'entre dans la mesure. Une table renommee, une requete reecrite, une couche
d'ecriture deplacee: la mesure suit, parce qu'elle observe le moteur.

**Ce que l'instrument ne compte pas, et c'est deliberé.** Il ne compte pas les
LIGNES. Une table vide dont le chemin existe est une copropriete sans matiere -
un fait sur la copropriete, pas un trou du produit. La distinction n'est pas
theorique: sur l'instance etalon du 2026-09-09, `liens_gouvernance` porte zero
ligne alors que `pont_actes.verser` l'ecrit a chaque absorption. Un instrument
qui aurait compte les lignes l'aurait declaree orpheline, a tort.

----------------------------------------------------------------------
Axe, invariant, et ce qui se passe hors des valeurs observees
----------------------------------------------------------------------

- **L'axe.** *Un ecran promet ce qu'un chemin du produit peut produire.* Le
  degre de liberte est le chemin: quel module ecrit, sous quel nom, par quelle
  couche, a partir de quelle piece. Rien de tout cela n'est code ici.
- **L'invariant le long de l'axe.** Toute table qu'un ecran montre est soit
  atteignable par une ecriture du produit, soit NOMMEE comme ne l'etant pas.
- **Ce que le code en fait.** Il mesure les deux ensembles et compare. Les deux
  sens rougissent: une table lue, non ecrite et non declaree; et une table
  declaree sans chemin que la chaine ecrit en fait - c'est-a-dire une limite
  perimee, encore affichee a l'utilisateur.
- **Hors des valeurs observees.** Une table AJOUTEE demain au coffre et lue par
  un ecran est mesuree sans edition de ce fichier. Un ECRAN ajoute demain est
  mesure aussi, tant que son constructeur se contente de l'instance et de
  l'annee - **et depuis le 2026-09-09 seulement, ou qu'il vive dans `web/`.**
  Un constructeur qui exige un autre argument ne peut pas etre appele ici: il
  n'est pas ignore en silence, il doit figurer dans `HORS_PORTEE`, donc
  l'auteur d'un nouvel ecran de cette forme est force de le declarer.

**Cette phrase a ete FAUSSE, et c'est instructif.** Elle promettait deja qu'un
ecran ajoute demain serait mesure, pendant que la collecte ne regardait que les
modules dont le nom finit par `_view`. Mesure du 2026-09-09, fonction identique
au bit pres lisant une table orpheline non declaree: rouge dans
`temoin_refutateur_view.py`, **vert dans `governance.py`**. Six `build_*`
vivaient deja dans cet angle mort, dont `build_governance_overview(instance,
year)` - exactement la forme que ce fichier pretendait couvrir. Un instrument
qui se degrade faux en silence produit un chiffre credible, ce qui est pire que
pas de chiffre du tout.

Deux choses ont change. La collecte porte sur le PAQUET `coproscope.web`,
recursivement, sans regarder le nom des fichiers. Et surtout,
`test_aucun_constructeur_d_ecran_n_echappe_a_la_mesure` recoupe cette collecte
avec un balayage AST des sources: **les trois listes exactes qui existaient ne
pouvaient pas attraper ce defaut**, parce qu'elles recoupent toutes ce que la
collecte a RENDU, jamais ce qu'elle n'a pas atteint.

**Le residu, nomme au lieu d'etre lisse.** La mesure d'ecriture vaut pour les
chemins que ce corpus EXERCE. Un chemin qui n'ecrirait que sur une matiere
absente de `examples/synthetic_copro` serait vu comme inexistant, et sa table
serait signalee orpheline a tort. Le cout d'un tel faux positif est une ligne de
declaration a ecrire, jamais un affaiblissement de la garde - et le message
d'echec dit explicitement les deux lectures possibles, pour qu'on tranche au
lieu de faire taire.

**Deuxieme residu, mesure le 2026-09-09.** L'appel de chaque ecran est
enveloppe d'un `except Exception` muet. Un ecran qui casserait AVANT de lire ses
tables serait donc enregistre comme *ne lit rien*, ce qui est une reponse fausse
en silence. Compte effectif a cette date: **zero ecran casse sur les 25
mesures**, donc le defaut est latent et non actif - mais il ne se signalera pas
tout seul le jour ou il s'activera.

**La limite de corpus se declare.** Cette mesure tourne sur
`examples/synthetic_copro`, instance publique: la CI n'a pas le droit de lire
une instance privee. Elle prouve donc quels chemins d'ecriture EXISTENT, ce qui
est exactement sa question - elle ne prouve rien sur la justesse de ce qui est
ecrit.
"""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance
from coproscope.core.pipeline import run_pipeline
from coproscope.vault.gouvernance_store import GOUVERNANCE_DB_FILE
from coproscope.web._ecrans_promesses import PAR_TABLE, SANS_CHEMIN_DE_PRODUCTION
from tests._mesure_ecrans import (
    RACINE_WEB,
    _arguments_requis,
    _constructeurs_dans_les_sources,
    _constructeurs_de_vue,
    _instance_vide,
    _Mouchard,
)

#: Les constructeurs d'ecran qu'aucune instance seule ne suffit a appeler: ils
#: exigent l'identifiant d'un objet, ou recoivent leurs lignes toutes faites.
#: Cette liste est VERIFIEE, pas consultee: un constructeur qui la quitte ou qui
#: y entre fait rougir `test_la_liste_des_ecrans_hors_portee_est_exacte`. Sans
#: ce recoupement, un nouvel ecran non appelable serait ignore en silence, et
#: c'est precisement le trou que cette garde existe pour fermer.
HORS_PORTEE: frozenset[str] = frozenset({
    "build_annotations_view_from_rows",
    # Les trois suivants vivaient dans l'angle mort de la collecte jusqu'au
    # 2026-09-09: leur module ne finit pas par `_view`, donc rien ne les
    # mesurait NI ne les declarait. Ils entrent ici parce qu'ils exigent des
    # arguments qu'une instance seule ne fournit pas.
    "build_document_detail",
    "build_document_intake_source_context",
    "build_local_export_zip",
    "build_memory_event_detail",
    "build_passation_blocker_detail",
    "build_piece_detail",
    # `build_pilotage_view_from_rows` est sorti le 2026-09-13 avec l'ecran
    # `/pilotage`, supprime par la recette de Brice (`RM-2026-0183`).
})

#: Les constructeurs qui n'acceptent aucun parametre `instance`, meme optionnel:
#: ils ne peuvent recevoir aucune copropriete, donc ils ne promettent rien sur
#: une table. Remplie a la mesure du 2026-09-09 et verifiee a chaque passage.
SANS_CANAL_INSTANCE: frozenset[str] = frozenset({
    "build_annotations_view",
    "build_document_intake_view",
})


class LEcranPrometCeQueLaProductionProduit(unittest.TestCase):
    """La mesure est faite UNE fois, en `setUpClass`: elle joue une absorption."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tempdir = tempfile.TemporaryDirectory()
        racine = _instance_vide(Path(cls._tempdir.name) / "instance")
        mouchard = _Mouchard()
        with mouchard:
            instance = load_instance(None, str(racine))
            mouchard.mode = "ecriture"
            run_pipeline(instance, RunContext(instance, "garde RM-2026-0059"), copy_classified=False)

            # **Les gestes de l'utilisateur font partie de la production, et
            # cette garde ne les jouait pas.** Elle mesurait la seule chaine,
            # donc une table ecrite par une ROUTE - declenchee par un humain
            # devant l'ecran - lui restait invisible et serait restee declaree
            # orpheline indefiniment. C'est le cas de `traces_controle`, cablee
            # le 2026-09-09 sur l'arbitrage de Brice.
            #
            # **La garde nomme elle-meme le remede, et c'est celui-ci:** *un
            # chemin l'ecrit, mais ce corpus ne l'exerce pas - alors le corpus
            # doit porter la piece qui le declenche.* On l'exerce donc, plutot
            # que d'affaiblir la comparaison.
            #
            # L'axe reste *un chemin du PRODUIT ecrit la table*: un geste neuf
            # ajoute ici est du meme ordre qu'une etape ajoutee a la chaine.
            from coproscope.web._controle_gouvernance_conclusion import enregistrer

            enregistrer(instance, "acte", "ACTE-GARDE-0059",
                        "CONTROLE_TRACE", "Geste joue par la garde.")

            fichiers = list(racine.glob("**/%s" % GOUVERNANCE_DB_FILE))
            connexion = mouchard.connexion_directe(fichiers[0]) if fichiers else None
            try:
                cls.tables_du_coffre = (
                    {
                        row[0]
                        for row in connexion.execute(
                            "select name from sqlite_master where type='table'"
                        )
                    }
                    if connexion is not None
                    else set()
                )
            finally:
                if connexion is not None:
                    connexion.close()

            # Les vues et `sqlite_master` sont vus en ecriture au moment ou les
            # vues sont (re)creees. Seules les vraies tables nous interessent.
            cls.ecrites = {t for t in mouchard.ecrites if t in cls.tables_du_coffre}

            mouchard.mode = "lecture"
            cls.lectures: dict[str, set[str]] = {}
            cls.hors_portee_mesure: set[str] = set()
            cls.sans_canal_mesure: set[str] = set()
            # La collecte porte desormais sur tout le paquet, sous-paquets
            # compris: deux modules peuvent y definir le meme nom. Les mesures
            # sont rangees par nom, donc un homonyme ecraserait l'autre sans
            # bruit. On le note pour le faire rougir au lieu de le subir.
            cls.doublons: set[str] = set()
            vus_une_fois: set[str] = set()
            for nom, fonction in _constructeurs_de_vue():
                if nom in vus_une_fois:
                    cls.doublons.add(nom)
                vus_une_fois.add(nom)
                requis = _arguments_requis(fonction)
                if set(requis) - {"instance", "year"}:
                    cls.hors_portee_mesure.add(nom)
                    continue
                parametres = inspect.signature(fonction).parameters
                if "instance" not in parametres:
                    # Aucun parametre `instance`, meme optionnel: cet ecran ne
                    # peut recevoir aucune copropriete, donc il ne promet rien
                    # sur une table. C'est le domaine de la garde soeur.
                    cls.sans_canal_mesure.add(nom)
                    continue
                mouchard.lues.clear()
                try:
                    fonction(**cls._appel(parametres, instance))
                except Exception:  # noqa: BLE001 - un ecran qui casse se voit ailleurs
                    pass
                cls.lectures[nom] = {t for t in mouchard.lues if t in cls.tables_du_coffre}
        cls.connexions_vues = mouchard.connexions_vues
        cls.bases_vues = set(mouchard.bases_vues)
        cls.par_base = {
            nom: {cle: set(valeurs) for cle, valeurs in entree.items()}
            for nom, entree in mouchard.par_base.items()
        }

    def test_la_mesure_declare_les_magasins_qu_elle_a_ouverts(self) -> None:
        """Un magasin qu'aucun chemin exerce n'ouvre se DIT, au lieu de se supposer.

        **Constat du 2026-09-12, et c'est le fond de `RM-2026-0008`:** la chaine
        d'absorption, le geste de l'ecran de controle et les ecrans mesures
        n'ouvrent qu'UNE base. `vault_reconstruction.sqlite3` n'est ouvert par
        aucun d'eux - il ne l'est que par les commandes CLI `vault rebuild` et
        `vault import-audit360-rows`. Les objets qu'`audit360` produit -
        `points`, `actions`, `expected_pieces` - sont donc ecrits dans un
        magasin que **rien dans `web/` ne lit**.

        Ce test n'interdit rien: il AFFIRME l'etat, pour que la ligne bouge le
        jour ou un chemin du produit ouvrira ce magasin. C'est ce qui distingue
        un constat date d'une supposition reconduite.
        """
        self.assertIn(
            GOUVERNANCE_DB_FILE, self.bases_vues,
            "la mesure n'a ouvert aucun magasin de gouvernance: elle est a vide",
        )
        self.assertEqual(
            {GOUVERNANCE_DB_FILE}, self.bases_vues,
            "un magasin de plus a ete ouvert par la chaine, un geste ou un "
            "ecran. Ce n'est pas un defaut: c'est la fin d'un constat. Verifier "
            "que la comparaison de tables porte bien sur le bon magasin, puis "
            "mettre ce test a jour en disant lequel et par quel chemin.",
        )

    @staticmethod
    def _appel(parametres, instance) -> dict[str, object]:
        """Les arguments a passer, lus sur la signature et non sur une liste.

        Un ecran recoit sa copropriete par un parametre `instance`, requis ou
        optionnel - la difference ne dit rien sur ce que l'ecran promet, elle
        dit seulement si l'auteur lui a donne une valeur par defaut. La mesure
        passe donc l'instance des que le parametre existe, et l'annee quand
        elle est acceptee.
        """
        arguments: dict[str, object] = {"instance": instance}
        if "year" in parametres:
            arguments["year"] = 2026
        return arguments

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tempdir.cleanup()

    # ------------------------------------------------------------------
    # Gardes de l'instrument: un compteur faux rend un chiffre credible.
    # ------------------------------------------------------------------

    def test_l_instrument_a_vraiment_observe_le_coffre(self) -> None:
        """Sans ce controle, une mesure a vide passerait tous les tests suivants.

        Si le coffre changeait de nom de fichier, si la chaine cessait de
        l'ouvrir, ou si `set_authorizer` devenait inoperant, les ensembles
        seraient vides et *aucune table lue non ecrite* serait trivialement
        vrai. C'est le defaut que ce depot appelle l'instrument qui ne peut pas
        echouer.
        """
        self.assertGreater(
            self.connexions_vues, 0,
            "aucune connexion au coffre de gouvernance n'a ete observee: "
            "l'interception est cassee, pas le produit",
        )
        self.assertTrue(
            self.tables_du_coffre,
            "le coffre ne porte aucune table: l'absorption n'a rien construit",
        )
        self.assertTrue(
            self.ecrites,
            "aucune ecriture observee dans le coffre: la chaine de production "
            "n'a rien ecrit, ou l'autorisateur ne voit pas les ecritures",
        )
        self.assertTrue(
            any(self.lectures.values()),
            "aucun ecran n'a ete vu lire le coffre: la mesure de lecture est "
            "cassee, et la comparaison qui suit serait vide de sens",
        )

    def test_la_liste_des_ecrans_hors_portee_est_exacte(self) -> None:
        """Un ecran non appelable ne doit pas etre saute en silence.

        C'est le trou par lequel la garde se viderait: il suffirait d'ajouter un
        argument requis a un constructeur pour qu'il sorte de la mesure sans que
        rien ne bouge. Ici, entrer ou sortir de la liste force une edition.
        """
        self.assertEqual(
            self.hors_portee_mesure, set(HORS_PORTEE),
            "la liste des constructeurs non appelables depuis une instance a "
            "change. Mesure: %s. Declare: %s. Mets `HORS_PORTEE` a jour, et "
            "verifie au passage que le nouvel ecran ne montre pas une table que "
            "personne n'ecrit."
            % (sorted(self.hors_portee_mesure), sorted(HORS_PORTEE)),
        )

    def test_la_liste_des_ecrans_sans_canal_est_exacte(self) -> None:
        """Les ecrans qui ne peuvent recevoir aucune copropriete, denombres.

        **Mesure du 2026-09-09, et elle corrige l'item.** `RM-2026-0059` parle
        de *huit ecrans sans canal d'entree*, et la garde soeur
        `test_ecrans_sans_instance_declarent_leur_nature` les cherche par le
        critere *tous les parametres du constructeur sont des scalaires*. Sur
        `913d744`, ce critere ne designe plus AUCUN constructeur: les seize
        constructeurs sans argument requis ont tous gagne un parametre
        `instance: Any | None = None`. La garde soeur collecte donc zero ecran
        et son propre controle d'instrument la fait rougir - verifie sur la base
        vierge, avant toute modification de ce lot.

        Consequence a ne pas escamoter: les huit ecrans de l'item **ont
        desormais un canal**. Savoir s'ils s'en servent est une autre question,
        et c'est celle que mesure `test_aucun_ecran_ne_montre_une_table_que_rien_n_ecrit`,
        qui les appelle avec une vraie instance.
        """
        self.assertEqual(
            self.sans_canal_mesure, set(SANS_CANAL_INSTANCE),
            "la liste des constructeurs qui n'acceptent aucune `instance` a "
            "change. Mesure: %s. Declare: %s."
            % (sorted(self.sans_canal_mesure), sorted(SANS_CANAL_INSTANCE)),
        )

    def test_aucun_constructeur_d_ecran_n_echappe_a_la_mesure(self) -> None:
        """Tout `build_*` de web/ est mesure, declare hors portee, ou declare
        sans canal. Jamais ignore.

        **C'est la garde de la collecte, et elle manquait.** Les trois listes
        exactes qui la precedent recoupent chacune ce que la collecte a RENDU;
        aucune ne pouvait voir ce que la collecte n'avait jamais atteint. Un
        constructeur pose hors des modules `*_view` sortait donc de la garde
        sans qu'aucun test ne bouge - verifie par A/B le 2026-09-09, fonction
        identique lisant une table orpheline: rouge dans un module `_view`,
        vert ailleurs.

        L'axe: *un ecran de la couche web est mesure ou declare*. Le degre de
        liberte est l'endroit ou le code vit - nom de fichier, sous-paquet,
        profondeur. Rien de tout cela n'entre ici: la comparaison se fait entre
        deux instruments independants, l'import et le texte.
        """
        sources = _constructeurs_dans_les_sources()
        self.assertTrue(
            sources,
            "aucun `def build_*` trouve dans les sources de web/: le balayage "
            "AST est casse, pas le produit",
        )
        collectes = set(self.lectures) | self.hors_portee_mesure | self.sans_canal_mesure
        echappes = sorted(set(sources) - collectes)
        self.assertFalse(
            echappes,
            "ces constructeurs d'ecran sont ecrits dans web/ et ne sont PAS "
            "atteints par la collecte, donc rien ne verifie ce qu'ils "
            "promettent: %s. Ils ne peuvent pas etre ignores en silence - "
            "corrige la collecte, ou declare-les."
            % ", ".join("%s (%s)" % (nom, sources[nom]) for nom in echappes),
        )

    def test_aucun_constructeur_ne_porte_le_nom_d_un_autre(self) -> None:
        """Deux ecrans homonymes: la seconde mesure ecraserait la premiere."""
        self.assertFalse(
            sorted(self.doublons),
            "deux modules de web/ definissent le meme constructeur %s. Les "
            "mesures sont rangees par nom, donc l'un des deux ecrans n'est pas "
            "mesure - et rien ne le dirait." % sorted(self.doublons),
        )

    # ------------------------------------------------------------------
    # LA garde, dans ses deux sens.
    # ------------------------------------------------------------------

    def test_aucun_ecran_ne_montre_une_table_que_rien_n_ecrit(self) -> None:
        for ecran in sorted(self.lectures):
            orphelines = sorted(self.lectures[ecran] - self.ecrites - set(PAR_TABLE))
            with self.subTest(ecran=ecran):
                self.assertFalse(
                    orphelines,
                    "`%s` lit %s, et la chaine de production n'ecrit dans aucune "
                    "de ces tables. Deux lectures possibles, et il faut trancher "
                    "l'une ou l'autre, jamais affaiblir cette garde:\n"
                    "  1. aucun geste du produit ne remplit cette table - alors "
                    "l'ecran promet ce qu'il ne peut pas tenir, et l'absence se "
                    "declare dans `web/_ecrans_promesses.py` en attendant d'etre "
                    "comblee;\n"
                    "  2. un chemin l'ecrit, mais ce corpus ne l'exerce pas - "
                    "alors le corpus de cette garde doit porter la piece qui le "
                    "declenche." % (ecran, orphelines),
                )

    def test_aucune_absence_declaree_n_est_en_fait_comblee(self) -> None:
        """Le sens inverse, et c'est celui qui a mordu le 2026-09-09.

        Une limite affichee a l'utilisateur apres avoir ete levee est un mensonge
        de sens oppose: l'ecran s'accuse d'un trou qui n'existe plus. La ligne
        *rien n'ecrit dans `actes_autorisation` hors des tests* est restee cinq
        jours a l'ecran apres que `pont_actes.verser` s'est mis a l'ecrire,
        parce qu'aucune garde ne comparait la prose au produit.
        """
        for promesse in SANS_CHEMIN_DE_PRODUCTION:
            with self.subTest(table=promesse.table):
                self.assertNotIn(
                    promesse.table, self.ecrites,
                    "`%s` est declaree sans chemin de production dans "
                    "`web/_ecrans_promesses.py`, et la chaine y ECRIT vraiment. "
                    "L'ecran affiche donc a l'utilisateur une limite qui est "
                    "levee. Retire cette entree." % promesse.table,
                )

    def test_une_absence_declaree_porte_sur_une_table_qu_un_ecran_montre(self) -> None:
        """Une declaration qui ne correspond a rien d'affiche est du bruit."""
        montrees = set().union(*self.lectures.values()) if self.lectures else set()
        for promesse in SANS_CHEMIN_DE_PRODUCTION:
            with self.subTest(table=promesse.table):
                self.assertIn(
                    promesse.table, self.tables_du_coffre,
                    "`%s` est declaree sans chemin mais n'existe pas dans le "
                    "coffre: la declaration nomme une table fantome" % promesse.table,
                )
                self.assertIn(
                    promesse.table, montrees,
                    "`%s` est declaree sans chemin mais aucun ecran ne la lit: "
                    "la declaration avertit d'un trou que personne ne voit"
                    % promesse.table,
                )

    def test_l_absence_declaree_atteint_l_ecran(self) -> None:
        """Une limite connue du code et absente de la page ne protege personne.

        C'est le defaut corrige le 2026-09-08 sur le panneau coffre: la page
        avait la verite sous la main et affichait autre chose.
        """
        from coproscope.web._controle_gouvernance_etat import EXIGENCES_BACK

        gabarit = (RACINE_WEB / "templates" / "controle_gouvernance.html").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "exigences_back", gabarit,
            "le gabarit ne rend plus `exigences_back`: les limites declarees "
            "n'atteignent plus l'ecran",
        )
        corps_affiches = {corps for _titre, corps in EXIGENCES_BACK}
        for promesse in SANS_CHEMIN_DE_PRODUCTION:
            with self.subTest(table=promesse.table):
                self.assertIn(
                    promesse.corps, corps_affiches,
                    "l'absence declaree pour `%s` ne sort pas dans les exigences "
                    "de l'ecran" % promesse.table,
                )
                self.assertIn(
                    promesse.table, promesse.corps,
                    "la phrase montree pour `%s` ne nomme pas la table: le "
                    "lecteur ne peut pas relier l'avertissement a ce qu'il voit"
                    % promesse.table,
                )


class LE_CHAMP_DE_VISION_DE_L_INSTRUMENT_SE_DERIVE(unittest.TestCase):
    """Ou l'autorisateur SQLite regarde, et comment on le saurait s'il loupait.

    **LE DEFAUT REPARE LE 2026-09-12.** `_Mouchard` n'armait son autorisateur
    que si le fichier ouvert s'appelait `gouvernance.sqlite3`. Or le depot porte
    **deux** magasins: celui-la, et `vault_reconstruction.sqlite3`, ou vivent
    les objets reconstruits - `points`, `actions`, `expected_pieces`,
    `object_links`, `event_log`, `source_import_map`. Le second etait
    integralement hors du champ, en lecture comme en ecriture.

    **Et la mesure dit que cela ne changeait rien aujourd'hui**, ce qui doit
    etre dit avec le reste: une seule base est ouverte pendant toute la mesure.
    Le defaut etait **latent**. Mais il ne se serait pas signale: le jour ou un
    ecran lirait `points`, la garde soeur aurait continue de rendre OK sans
    jamais voir cette lecture. *Le silence d'une garde n'est une preuve que si
    l'on sait ou elle regarde.*
    """

    def test_l_instrument_voit_un_SECOND_magasin_des_qu_on_en_ouvre_un(self) -> None:
        """Le temoin qui prouve que le champ de vision n'est plus une liste.

        Sans lui, la reparation serait une affirmation. Ce test ECHOUE avec le
        filtre par nom de fichier, et il ne cite le nom du second magasin que
        pour fabriquer le temoin - la mesure, elle, n'en enumere aucun.
        """
        import sqlite3
        import tempfile

        from tests._mesure_ecrans import _Mouchard

        mouchard = _Mouchard()
        with tempfile.TemporaryDirectory() as tmp:
            autre = Path(tmp) / "vault_reconstruction.sqlite3"
            with mouchard:
                connexion = sqlite3.connect(str(autre))
                try:
                    connexion.execute("create table points(point_id text)")
                    connexion.execute("insert into points values ('P1')")
                    connexion.commit()
                finally:
                    connexion.close()

        self.assertIn(
            "vault_reconstruction.sqlite3", mouchard.bases_vues,
            "l'instrument n'a pas vu s'ouvrir un second magasin: son champ de "
            "vision est de nouveau une liste de noms de fichiers, donc tout un "
            "magasin peut etre lu ou ecrit sans qu'il en sache rien",
        )
        self.assertIn(
            "points", mouchard.par_base.get("vault_reconstruction.sqlite3", {}).get("ecrites", set()),
            "le second magasin est vu s'ouvrir mais ses ecritures ne sont pas "
            "notees: la garde croirait qu'aucun chemin ne le remplit",
        )

    def test_un_magasin_en_memoire_n_est_pas_un_magasin(self) -> None:
        """Temoin inverse: ce qui ne survit pas ne peut etre montre a personne.

        Sans ce temoin, le test precedent passerait sur un instrument qui note
        tout, y compris ce dont aucun ecran ne pourra jamais rien dire.
        """
        import sqlite3

        from tests._mesure_ecrans import _Mouchard

        mouchard = _Mouchard()
        with mouchard:
            connexion = sqlite3.connect(":memory:")
            try:
                connexion.execute("create table t(x text)")
                connexion.execute("insert into t values ('x')")
            finally:
                connexion.close()

        self.assertEqual(set(), mouchard.bases_vues)

if __name__ == "__main__":
    unittest.main()
