# -*- coding: utf-8 -*-
"""Le bareme est une ENTREE qui deplace des SORTIES: y toucher se mesure.

**Le fait qui rend cette garde necessaire.** `RM-2026-0076` exige une mesure
avant/apres a chaque deplacement du bareme, parce qu'un mot-cle deplace des
milliers de lignes. Le 2026-09-09, un verdict de fermeture a ete pose sur cet
item en affirmant *le bareme n'a PAS ete touche*. Le commit cite par ce meme
lecteur comme le correctif, `a56b9fe`, **retire neuf motifs et ajoute un
mot-cle** dans `configs/taxonomy.default.yml`. Le lecteur n'avait regarde que
les deux lignes de priorite, qui n'avaient effectivement pas bouge.

Le defaut n'etait donc pas une erreur de lecture: c'etait l'ABSENCE d'un
instrument. Rien, dans le depot, ne repondait a la question *ce changement
a-t-il deplace un classement, et lequel*. Ce fichier est cet instrument.

**L'axe, et non les mots-cles d'aujourd'hui.** Une garde qui verifierait la
presence de `assemblee generale` ou de `pouvoirs` coderait les modalites
observees le 2026-09-09: elle deviendrait fausse au premier bareme suivant, et
muette sur les regles qu'elle ne nomme pas. Ce qui est garde ici est
l'invariant: **un bareme declare produit des types declares sur des textes
declares.** Deux choses tombent donc ensemble quand le bareme bouge - les
temoins, qui disent QUEL classement s'est deplace, et l'empreinte, qui dit
qu'une regle a bouge meme quand aucun temoin ne le montre.

**Ce que cette garde ne mesure pas, et il faut le dire.** Les temoins sont des
textes FABRIQUES: ils prouvent le sens et la mecanique d'un deplacement, jamais
son ampleur. L'ampleur se mesure sur un corpus, et la CI n'a pas le droit d'en
lire un: `examples/synthetic_copro` deplace 0 type sur 9 pieces, ce qui ne
prouve rien d'autre que la non-regression de neuf pieces. Les chiffres d'ampleur
mesures hors CI le 2026-09-09, sur la base `ffac60c`, sont reportes dans
`_bareme_mesure_reference.txt` a cote de l'empreinte.
"""

from __future__ import annotations

import copy
import difflib
import unittest
from pathlib import Path

from coproscope.core.common import load_structured_file
from coproscope.modules.docuscope import (
    CHAMPS_DOCUMENTAIRES,
    CHAMPS_REGLE,
    CLASSIFICATION_CONTENT_CHARS,
    _champ_regle,
    _classify,
    _rule_score,
    _rule_type,
    empreinte_bareme,
)

RACINE = Path(__file__).resolve().parents[1]
TAXONOMIE_LIVREE = RACINE / "src" / "coproscope" / "configs" / "taxonomy.default.yml"
REFERENCE = Path(__file__).with_name("_bareme_mesure_reference.txt")

#: Ce qui, dans le fichier de reference, separe le compte rendu de mesure de
#: l'empreinte elle-meme. Seule la seconde moitie est comparee: la premiere est
#: la mesure, et elle est faite pour etre lue par un humain.
MARQUEUR = "---8<---\n"

#: Les textes de mesure, un par degre de liberte que `a56b9fe` a touche.
#:
#: Chacun est FABRIQUE et ne porte ni nom de copropriete, ni de personne, ni
#: d'adresse. `type_attendu` est le type mesure sur la base `ffac60c`; `avant`
#: est celui que le bareme d'avant `a56b9fe` rendait sur le meme texte, avec le
#: meme code. La colonne `avant` n'est pas rejouee par les tests - elle porte la
#: mesure, pour que le lecteur voie le deplacement sans relire un diff de git.
TEMOINS: tuple[dict[str, str], ...] = (
    {
        "id": "pv_qui_ecrit_resolution_adoptee",
        "nom": "doc_0001.pdf",
        "chemin": "raw/2024/doc_0001.pdf",
        "contenu": (
            "Proces-verbal de l'assemblee generale ordinaire du 3 juillet 2024."
            " Les coproprietaires se sont reunis sur convocation du syndic."
            " Ordre du jour: approbation des comptes."
            " Resolution 1 - resolution adoptee a l'unanimite."
        ),
        "type_attendu": "PV_AG",
        "avant": "PV_AG",
        "pourquoi": "Le retrait de 'assemblee generale' ote 5 points aux DEUX regles: la marge ne bouge pas.",
    },
    {
        "id": "pv_etalon_de_RM_2026_0076",
        "nom": "doc_0002.pdf",
        "chemin": "raw/2024/doc_0002.pdf",
        "contenu": (
            "Proces-verbal de l'assemblee generale ordinaire du 3 juillet 2024."
            " Les coproprietaires se sont reunis sur convocation du syndic."
            " Ordre du jour: approbation des comptes."
            " Resolution 1 adoptee a l'unanimite des voix exprimees."
        ),
        "type_attendu": "Convocation_AG",
        "avant": "Convocation_AG",
        "pourquoi": "Le PV que l'item nomme est TOUJOURS classe convocation apres a56b9fe. Voir la marge ci-dessous.",
    },
    {
        "id": "convocation_qui_nomme_l_organe",
        "nom": "doc_0003.pdf",
        "chemin": "raw/2024/doc_0003.pdf",
        "contenu": (
            "Convocation a l'assemblee generale ordinaire. Ordre du jour joint."
            " Vous etes prie d'assister a la reunion des coproprietaires."
        ),
        "type_attendu": "Convocation_AG",
        "avant": "Convocation_AG",
        "pourquoi": "Type inchange, score 115 -> 110: un deplacement de score sans deplacement de type.",
    },
    {
        "id": "pouvoirs_du_syndic_et_de_l_assemblee",
        "nom": "doc_0004.pdf",
        "chemin": "raw/2024/doc_0004.pdf",
        "contenu": (
            "Note sur les pouvoirs du syndic. Le syndic administre l'immeuble et"
            " pourvoit a sa conservation. Les pouvoirs de l'assemblee sont rappeles."
        ),
        "type_attendu": "A_CLASSER",
        "avant": "Feuille_Presence_AG",
        "pourquoi": "Le mot 'pouvoirs' de la loi 65-557 art. 18 ne nomme plus une feuille de presence.",
    },
    {
        "id": "pouvoirs_dans_le_nom_du_fichier",
        "nom": "pouvoirs_2024.pdf",
        "chemin": "raw/2024/pouvoirs_2024.pdf",
        "contenu": "Formulaire de mandat pour se faire representer a la reunion des coproprietaires.",
        "type_attendu": "A_CLASSER",
        "avant": "Feuille_Presence_AG",
        "pourquoi": "Le motif de nom de fichier 'pouvoirs' est retire en meme temps que le mot-cle.",
    },
    {
        "id": "feuille_de_presence_nommee",
        "nom": "feuille_presence_2024.pdf",
        "chemin": "raw/2024/feuille_presence_2024.pdf",
        "contenu": "Feuille de presence emargee. Mandats de vote recus.",
        "type_attendu": "Feuille_Presence_AG",
        "avant": "Feuille_Presence_AG",
        "pourquoi": "Temoin de non-regression: ce que le retrait de 'pouvoirs' ne devait PAS casser.",
    },
    {
        "id": "annexe_jointe_a_la_convocation",
        "nom": "annexe_3_projet_resolution.pdf",
        "chemin": "raw/2024/annexe_3_projet_resolution.pdf",
        "contenu": "Document joint a l'envoi. Projet de texte soumis au vote des coproprietaires.",
        "type_attendu": "A_CLASSER",
        "avant": "Annexe_Comptable",
        "pourquoi": "Le motif nu 'annexe' faisait d'une piece jointe a la convocation un etat financier.",
    },
    {
        "id": "annexe_comptable_nommee",
        "nom": "annexe_comptable_2024.pdf",
        "chemin": "raw/2024/annexe_comptable_2024.pdf",
        "contenu": (
            "Annexe comptable de l'exercice. Etat financier apres repartition."
            " Charges et produits de l'exercice."
        ),
        "type_attendu": "Annexe_Comptable",
        "avant": "Annexe_Comptable",
        "pourquoi": "Temoin de non-regression du retrait du motif nu 'annexe'.",
    },
    {
        "id": "identite_bancaire_sans_operation",
        "nom": "rib_syndicat.pdf",
        "chemin": "raw/2024/rib_syndicat.pdf",
        "contenu": (
            "Releve d'identite bancaire du syndicat des coproprietaires."
            " IBAN et code guichet du compte bancaire separe."
        ),
        "type_attendu": "A_CLASSER",
        "avant": "Releve_Bancaire",
        "pourquoi": "Une identite de compte ne releve aucune operation: 'rib' et 'iban' sont retires.",
    },
    {
        "id": "pied_de_facture_qui_porte_un_iban",
        "nom": "doc_0009.pdf",
        "chemin": "raw/2024/doc_0009.pdf",
        "contenu": (
            "Prestation de nettoyage mensuel. Merci de regler par virement sur le"
            " compte bancaire dont l'IBAN figure ci-dessous."
        ),
        "type_attendu": "A_CLASSER",
        "avant": "Releve_Bancaire",
        "pourquoi": "Le faux positif que le retrait visait: un pied de facture devenait un releve bancaire.",
    },
    {
        "id": "releve_de_compte_du_syndicat",
        "nom": "doc_0010.pdf",
        "chemin": "raw/2024/doc_0010.pdf",
        "contenu": (
            "Releve de compte du syndicat des coproprietaires. Operations de la"
            " periode: virement recu, prelevement, solde en fin de periode."
        ),
        "type_attendu": "Releve_Bancaire",
        "avant": "A_CLASSER",
        "pourquoi": "Le SEUL mot-cle ajoute par a56b9fe. Une promotion, pas un retrait.",
    },
)

#: Le duel que `RM-2026-0076` decrit, mesure sur la base `ffac60c`.
#:
#: L'item ecrit: le PV etalon marque 115 pour `Convocation_AG` contre 113 pour
#: `PV_AG`, **il perd de 2 points**. `a56b9fe` retire `assemblee generale` des
#: DEUX regles, donc chacune perd 5 points sur tout document qui nomme l'organe
#: - et l'arbitrage ne se pose que sur ces documents-la. La marge est invariante.
MARGE_CONVOCATION_MOINS_PV = 2


def taxonomie_livree() -> dict:
    return load_structured_file(TAXONOMIE_LIVREE)


def regles_de(taxonomy: dict) -> list[dict]:
    return taxonomy.get("rules", taxonomy.get("regles", []))


def type_du_temoin(temoin: dict, taxonomy: dict) -> str:
    contenu = temoin["contenu"][:CLASSIFICATION_CONTENT_CHARS]
    return _classify(contenu, temoin["nom"], temoin["chemin"], regles_de(taxonomy))[1]


class TemoinsDuBareme(unittest.TestCase):
    """Chaque temoin porte un degre de liberte du bareme, et son type mesure."""

    def setUp(self) -> None:
        self.taxonomy = taxonomie_livree()

    def test_le_corpus_de_temoins_n_est_pas_vide(self) -> None:
        # Une garde qui boucle sur un corpus vide rend vert sans rien mesurer.
        # Vider TEMOINS doit donc echouer ici, avant tout autre test.
        self.assertGreaterEqual(len(TEMOINS), 8)
        self.assertEqual(len({t["id"] for t in TEMOINS}), len(TEMOINS))
        # Un corpus qui n'attendrait qu'un seul type ne discriminerait rien.
        self.assertGreaterEqual(len({t["type_attendu"] for t in TEMOINS}), 3)

    def test_chaque_temoin_garde_le_type_qui_a_ete_mesure(self) -> None:
        for temoin in TEMOINS:
            with self.subTest(temoin=temoin["id"]):
                obtenu = type_du_temoin(temoin, self.taxonomy)
                self.assertEqual(
                    obtenu,
                    temoin["type_attendu"],
                    f"\nLe bareme a deplace le temoin {temoin['id']}:"
                    f" mesure {temoin['type_attendu']}, obtenu {obtenu}."
                    f"\nRaison d'etre du temoin: {temoin['pourquoi']}"
                    "\nRM-2026-0076 exige la mesure avant/apres AVANT d'integrer"
                    " un deplacement de bareme. Refaire la mesure, puis mettre a"
                    " jour ce temoin et _bareme_mesure_reference.txt.",
                )


class TemoinsSensiblesAuBareme(unittest.TestCase):
    """La garde mord-elle ? Un temoin qu'aucun bareme ne deplace ne mesure rien.

    C'est le controle de l'INSTRUMENT, pas du produit. Un temoin peut passer au
    vert pour une mauvaise raison - texte vide, type qui ne depend d'aucune
    regle - et donner l'illusion d'une mesure. Chaque temoin doit donc etre
    DEPLACABLE par une modification du bareme, et les deux mutations ci-dessous
    sont generiques: elles ne nomment aucun mot-cle d'aujourd'hui.
    """

    def setUp(self) -> None:
        self.taxonomy = taxonomie_livree()

    def _sans_les_motifs_du_type(self, document_type: str) -> dict:
        """Le bareme prive de tout ce qui declenche ce type."""
        mutant = copy.deepcopy(self.taxonomy)
        for regle in regles_de(mutant):
            if _rule_type(regle) != document_type:
                continue
            for champ in ("keywords", "mots_cles", "filename_patterns",
                          "motifs_nom_fichier", "path_patterns", "motifs_chemin"):
                if champ in regle:
                    regle[champ] = []
        return mutant

    def _avec_un_mot_cle_qui_capte(self, temoin: dict) -> tuple[dict, str]:
        """Le bareme dont la premiere regle capte le debut du texte du temoin.

        Le mot-cle injecte est DERIVE du temoin, jamais choisi dans la
        taxonomie: la mutation reste valable quel que soit le bareme du jour.
        """
        mutant = copy.deepcopy(self.taxonomy)
        premiere = regles_de(mutant)[0]
        amorce = " ".join(temoin["contenu"].split()[:3])
        premiere["mots_cles"] = list(premiere.get("mots_cles", [])) + [amorce]
        return mutant, _rule_type(premiere)

    def test_chaque_temoin_se_deplace_quand_le_bareme_bouge(self) -> None:
        for temoin in TEMOINS:
            with self.subTest(temoin=temoin["id"]):
                depart = type_du_temoin(temoin, self.taxonomy)
                self.assertEqual(depart, temoin["type_attendu"])
                if depart != "A_CLASSER":
                    mutant = self._sans_les_motifs_du_type(depart)
                    self.assertNotEqual(
                        type_du_temoin(temoin, mutant),
                        depart,
                        f"Le temoin {temoin['id']} garde son type {depart} alors"
                        " que toutes les regles de ce type ont ete videes de"
                        " leurs motifs. Son verdict ne vient donc pas du bareme:"
                        " il ne mesure pas ce que ce fichier pretend mesurer.",
                    )
                else:
                    mutant, capte = self._avec_un_mot_cle_qui_capte(temoin)
                    self.assertEqual(
                        type_du_temoin(temoin, mutant),
                        capte,
                        f"Le temoin {temoin['id']} reste A_CLASSER alors qu'un"
                        " mot-cle tire de son propre texte a ete ajoute a la"
                        " premiere regle du bareme. Il est donc hors de portee"
                        " du bareme et ne mesure aucun deplacement.",
                    )


class EmpreinteDuBareme(unittest.TestCase):
    """Un bareme qui bouge sans que la mesure soit refaite doit echouer ici.

    Les temoins montrent les deplacements qu'ils couvrent. L'empreinte couvre
    le reste: les 38 regles, y compris celles qu'aucun temoin n'exerce. Elle est
    volontairement LISIBLE et non condensee, pour que l'echec nomme la regle.
    """

    def test_l_empreinte_est_celle_qui_a_ete_mesuree(self) -> None:
        brut = REFERENCE.read_text(encoding="utf-8")
        # Le marqueur separe la MESURE, qui se lit, de l'EMPREINTE, qui se
        # compare. S'il manque, la garde le dit au lieu de lever un IndexError
        # que personne ne saurait relier a ce fichier.
        self.assertIn(
            MARQUEUR,
            brut,
            f"{REFERENCE.name} ne porte pas la ligne {MARQUEUR.strip()!r}, qui"
            " separe le compte rendu de mesure de l'empreinte comparee. Le"
            " fichier a ete regenere sans son en-tete, ou tronque.",
        )
        attendue = brut.split(MARQUEUR, 1)[1]
        obtenue = empreinte_bareme(taxonomie_livree())
        if obtenue.strip() == attendue.strip():
            return
        ecart = "\n".join(
            difflib.unified_diff(
                attendue.strip().splitlines(),
                obtenue.strip().splitlines(),
                "bareme mesure",
                "bareme livre",
                lineterm="",
                n=0,
            )
        )
        self.fail(
            "\nLe bareme a bouge depuis la derniere mesure avant/apres.\n"
            f"{ecart}\n\n"
            "RM-2026-0076: un deplacement de bareme deplace des milliers de"
            " lignes, et la mesure avant/apres y est obligatoire. Refaire la"
            " mesure sur les temoins ET sur un corpus, ajouter un temoin pour"
            " chaque degre de liberte touche, puis regenerer"
            f" {REFERENCE.name} en y datant la mesure et sa base."
        )


class DefautNommeParRM20260076(unittest.TestCase):
    """Le defaut que l'item decrit survit-il AU BAREME livre ? Au bareme, oui.

    **Cette docstring promettait: *le jour ou quelqu'un rend la signature de
    titre capable de PROMOUVOIR, ce test tombera*. La promesse etait nulle.**
    Mesure du 2026-09-12: la promotion existe - `02_classification.py`, branche
    `len(titled) == 1` - et ce test n'est pas tombe, parce qu'il interroge
    `_classify`, le bareme SEUL, et jamais `classify()`. Sur le PV etalon, le
    bareme rend `Convocation_AG` et la chaine rend `PV_AG` avec la note *type
    retenu contre Convocation_AG*. Le defaut que l'item nomme est donc corrige
    au point d'entree, et ce test le cachait en continuant de passer.

    Ce qu'il mesure reste VRAI et utile, et il le mesure desormais sous son
    nom: le BAREME perd encore de deux points sur ce temoin. La correction par
    la chaine est gardee la ou elle vit, au point d'entree:
    `test_le_titre_promeut_au_point_d_entree.py`.
    """

    def marges(self, contenu: str) -> tuple[int, int]:
        taxonomy = taxonomie_livree()
        scores: dict[str, int] = {}
        for regle in regles_de(taxonomy):
            atteint, score = _rule_score(regle, contenu, "doc_0002.pdf", "raw/2024/doc_0002.pdf")
            if atteint:
                nom = _rule_type(regle)
                scores[nom] = max(scores.get(nom, 0), score)
        return scores.get("Convocation_AG", 0), scores.get("PV_AG", 0)

    def test_le_pv_etalon_perd_toujours_de_deux_points(self) -> None:
        temoin = next(t for t in TEMOINS if t["id"] == "pv_etalon_de_RM_2026_0076")
        convocation, pv = self.marges(temoin["contenu"])
        self.assertEqual(
            convocation - pv,
            MARGE_CONVOCATION_MOINS_PV,
            "\nLa marge Convocation_AG - PV_AG sur le PV etalon a bouge"
            f" ({convocation} - {pv}). C'est le coeur de RM-2026-0076."
            " Si c'est une correction, la mesurer sur un corpus et fermer l'item"
            " avec cette mesure; si c'est un effet de bord, elle est a expliquer.",
        )

    def test_le_BAREME_seul_classe_encore_le_pv_etalon_en_convocation(self) -> None:
        """Ancien nom: `test_le_pv_etalon_reste_classe_convocation` - faux au
        point d'entree, ou la chaine le classe `PV_AG` par son titre."""
        temoin = next(t for t in TEMOINS if t["id"] == "pv_etalon_de_RM_2026_0076")
        self.assertEqual(type_du_temoin(temoin, taxonomie_livree()), "Convocation_AG")


class EmpreinteInjective(unittest.TestCase):
    """Deux baremes qui classent DIFFEREMMENT ne peuvent pas se rendre pareil.

    **L'invariant, et il est plus fort que la liste des champs empreintes.**
    L'empreinte existe pour qu'un bareme ne bouge pas sans mesure. Elle ne tient
    cette promesse que si elle est INJECTIVE vis-a-vis de ce que `_classify`
    lit: si deux baremes rendent des types differents sur un meme texte et
    portent la meme empreinte, la garde passe au vert sur un deplacement reel.

    **Deux trous mesures le 2026-09-09 sur la base `ffac60c`, tous deux muets.**
    La premiere version de `empreinte_bareme` rendait `sorted(lignes)`, donc
    les regles perdaient leur RANG - alors que son propre `_valeur_stable`
    ecrivait *"l'ordre des regles tranche les egalites de score"*. Deplacer
    `PV_AG` avant `Carnet_Entretien`, sans toucher une seule valeur, faisait
    passer un proces-verbal de `Carnet_Entretien` a `PV_AG` sous une empreinte
    octet pour octet identique, et les six tests de ce fichier restaient verts.
    Second trou: le separateur de liste n'etait pas echappe, donc
    `mots_cles: ["a,b"]` et `["a","b"]` se rendaient tous deux `[a,b]`.

    **Pourquoi ces deux cas sont ecrits comme UNE propriete et non comme deux
    correctifs.** Un test qui verifierait *l'empreinte contient un rang* et
    *l'empreinte echappe la virgule* coderait les deux trous trouves ce jour-la.
    Le troisieme trou - un separateur de champ non echappe, une cle de tete
    ajoutee, une valeur non serialisable rendue par `str` - passerait sans que
    rien ne crie. Ce qui est teste ici est donc la propriete, et les mutations
    ci-dessous en sont des INSTANCES, construites depuis la taxonomie livree.
    Chacune doit d'abord PROUVER qu'elle deplace un classement; une mutation
    inerte fait echouer le test au lieu de le rendre vert par vacuite.
    """

    def _poser(self, regle: dict, champ: str, valeur) -> None:
        """Ecrit un champ sous l'orthographe que la regle emploie deja."""
        for alias in CHAMPS_REGLE[champ]:
            if alias in regle:
                regle[alias] = valeur
                return
        regle[CHAMPS_REGLE[champ][0]] = valeur

    def _deux_regles_isolees(self) -> tuple[list[dict], str, str, str]:
        """Deux regles a egalite parfaite, et le texte qui les declenche.

        Rien n'est code en dur: les deux regles, leurs mots-cles et le texte
        sortent de la taxonomie livree. L'egalite est CONSTRUITE plutot que
        cherchee, pour que la mesure reste possible quels que soient les
        poids du jour.
        """
        taxonomy = taxonomie_livree()
        porteuses = [
            copy.deepcopy(r)
            for r in regles_de(taxonomy)
            if _champ_regle(r, "keywords", []) and r.get("lot")
        ]
        self.assertGreaterEqual(
            len(porteuses), 2,
            "Moins de deux regles portent un mot-cle: l'egalite qui rend"
            " l'ordre decisif ne peut plus etre construite, donc ce fichier ne"
            " mesure plus la sensibilite de l'empreinte a l'ordre.",
        )
        a, b = porteuses[0], porteuses[1]
        mots = []
        for regle in (a, b):
            premier = str(_champ_regle(regle, "keywords", [])[0])
            mots.append(premier)
            self._poser(regle, "priority", 50)
            self._poser(regle, "keywords", [premier])
            self._poser(regle, "filename_patterns", [])
            self._poser(regle, "path_patterns", [])
        return [a, b], f"{mots[0]} et {mots[1]}", _rule_type(a), _rule_type(b)

    def _mutations(self) -> list[tuple[str, dict, dict, str]]:
        """(nom, bareme 1, bareme 2, texte) - deux baremes a comparer."""
        cas: list[tuple[str, dict, dict, str]] = []

        # 1. Une PERMUTATION: aucune valeur ne change, seul le rang change.
        regles, texte, _, _ = self._deux_regles_isolees()
        cas.append((
            "l'ordre des regles, qui tranche les egalites de score",
            {"regles": list(regles)},
            {"regles": list(reversed(regles))},
            texte,
        ))

        # 2. Une valeur qui CONTIENT le separateur du rendu: deux mots-cles
        #    contre un seul qui les porte tous les deux.
        regles, texte, _, _ = self._deux_regles_isolees()
        deux = copy.deepcopy(regles[:1])
        un = copy.deepcopy(regles[:1])
        mots = [str(_champ_regle(deux[0], "keywords", [])[0]), "zzz_absent_du_texte"]
        self._poser(deux[0], "keywords", mots)
        self._poser(un[0], "keywords", [",".join(mots)])
        cas.append((
            "une valeur qui porte le separateur du rendu",
            {"regles": deux},
            {"regles": un},
            texte,
        ))
        return cas

    def test_la_famille_de_mutations_n_est_pas_vide(self) -> None:
        # Une boucle sur une liste vide rend vert sans rien mesurer.
        self.assertGreaterEqual(len(self._mutations()), 2)

    def test_deux_baremes_qui_classent_autrement_ont_deux_empreintes(self) -> None:
        for nom, un, deux, texte in self._mutations():
            with self.subTest(degre=nom):
                t1 = _classify(texte, "doc.pdf", "raw/doc.pdf", regles_de(un))[1]
                t2 = _classify(texte, "doc.pdf", "raw/doc.pdf", regles_de(deux))[1]
                # La mutation doit d'abord PROUVER qu'elle deplace un type,
                # sans quoi l'egalite des empreintes ne prouverait rien.
                self.assertNotEqual(
                    t1, t2,
                    f"La mutation '{nom}' ne deplace plus aucun classement:"
                    " elle ne mesure donc plus rien, et son passage au vert"
                    " est vide. La reconstruire sur le bareme du jour.",
                )
                self.assertNotEqual(
                    empreinte_bareme(un), empreinte_bareme(deux),
                    "Deux baremes rendent des types differents sur le meme"
                    f" texte ({t1} contre {t2}) et portent la MEME empreinte."
                    f" Degre de liberte non empreinte: {nom}."
                    " L'empreinte laisse donc passer un deplacement de bareme"
                    " en silence, ce que RM-2026-0076 lui demande d'empecher.",
                )

    def test_un_champ_qui_ne_promet_aucun_effet_ne_bouge_pas_l_empreinte(self) -> None:
        # L'autre moitie de l'axe: une empreinte qui crie sur une citation
        # finirait desactivee. `fondement` est declare sans effet.
        avant = taxonomie_livree()
        apres = copy.deepcopy(avant)
        for champ in sorted(CHAMPS_DOCUMENTAIRES):
            regles_de(apres)[0][champ] = "texte ajoute par le test"
        self.assertEqual(empreinte_bareme(avant), empreinte_bareme(apres))


if __name__ == "__main__":
    unittest.main()
