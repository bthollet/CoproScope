"""Un etat d'issue ajoute en amont, et quatre tables aval qui l'ignorent.

Ce fichier ne defend pas une fonctionnalite. Il defend **la totalite d'une
traduction**: la voie `resolutions` produit des etats d'issue, quatre tables
aval doivent les declarer, et rien dans le langage ne relie les cinq.

Ce qui a ete mesure le 2026-09-08. `ISSUE_ENONCEE_NON_LUE` etait defini, produit
par l'extracteur, compte par `summarize` - et declare nulle part en aval: ni
dans la table du pont, ni dans les libelles de l'ecran des resolutions, ni dans
sa liste de relecture, ni dans les libelles de l'ecran de gouvernance. Le
vocabulaire des actes, lui, ne portait meme pas la valeur d'arrivee dont il
avait besoin. `ISSUE_NON_RECONNUE`, ajoute plus tot, avait deja les memes trous
sauf le libelle de l'ecran des resolutions.

Aucun test ne tombait, et c'est le point: **le defaut d'une table de traduction
n'est pas une erreur, c'est une valeur plausible.**
`ISSUES.get(brute, ISSUES["SANS_ISSUE_TRACEE"])` rendait `le document ne dit
rien` pour deux etats dont le sens est exactement l'inverse - le document DIT
quelque chose, et la chaine ne sait pas le lire. La perte etait totale et
silencieuse: l'ecran affichait `Issue non tracee`, le modele des actes ecrivait
`SANS_ISSUE_TRACEE`, et plus aucun chemin ne menait au fait constate.

Un test qui listerait les etats a la main aurait le meme defaut que les tables
qu'il surveille: il faudrait penser a l'y ajouter. **Les etats sont donc DERIVES
de l'extracteur lui-meme** - de ce que `_issue` peut rendre et de ce que
`to_rows` peut ecrire sous la colonne `resultat`.

Ce qui reste expose. La derivation lit du code, pas des donnees: elle suit les
`return` de `_issue`, les boucles sur `ISSUE_PREFIXES` et `ISSUE_LOCUTIONS`, et
la valeur ecrite par `to_rows`. Une reecriture de `_issue` dans une forme
qu'elle ne sait pas suivre lui ferait rendre moins d'etats - c'est-a-dire
garder moins, sans le dire. C'est le seul mode de defaillance qui rendrait ce
fichier inutile, et il est ferme par deux regles:

- **toute expression non resolue leve, jamais ne s'ignore** (`_Irresoluble`);
- **tout site qui ecrit une issue est nomme** (`SitesDEcritureTests`): un
  nouveau producteur fait tomber le test qui liste les producteurs, et non pas
  silencieusement passer celui qui verifie les tables.
"""

from __future__ import annotations

import ast
import dataclasses
import re
import unittest
from pathlib import Path

from coproscope.modules import _actes_vocabulaire as V
from coproscope.modules import _actes_vues as VUES
from coproscope.modules import _pont_actes_source as PONT
from coproscope.modules import _resolutions_extraction as EXTRACTION
from coproscope.modules import _resolutions_registre as REGISTRE
from coproscope.web import _controle_gouvernance_vocabulaire as ECRAN_ACTES
from coproscope.web import resolutions_view as ECRAN_RESOLUTIONS

RACINE = Path(__file__).resolve().parents[1] / "src" / "coproscope"
MODULES = RACINE / "modules"


class _Irresoluble(Exception):
    """La derivation ne sait plus lire le code qu'elle surveille.

    Elle leve au lieu d'ignorer. Une expression sautee rendrait un inventaire
    incomplet, donc des tables declarees completes a tort - exactement le
    silence que ce fichier existe pour supprimer.
    """


# --------------------------------------------------------------------------
# Deriver les etats d'issue du code qui les produit
# --------------------------------------------------------------------------


def _arbre(chemin: Path) -> ast.Module:
    return ast.parse(chemin.read_text(encoding="utf-8"))


def _fonction(arbre: ast.Module, nom: str) -> ast.FunctionDef:
    for node in ast.walk(arbre):
        if isinstance(node, ast.FunctionDef) and node.name == nom:
            return node
    raise _Irresoluble(f"fonction `{nom}` introuvable")


def _lier(
    liaisons: dict[str, frozenset[str]], nom: str, valeurs: object
) -> None:
    """Ajoute a ce qu'un nom peut valoir, sans jamais remplacer.

    Deux boucles de `_issue` nomment leur variable `issue` - l'une parcourt
    `ISSUE_LOCUTIONS`, l'autre `ISSUE_PREFIXES`. Ecraser la premiere liaison
    faisait disparaitre `SANS_OBJET` de l'inventaire, c'est-a-dire qu'un etat
    reel cessait d'etre exige des quatre tables **sans que rien ne le dise**.
    C'est le defaut meme que ce fichier surveille, reproduit dans l'instrument.

    L'union sur-approxime quand deux variables homonymes n'ont rien a voir:
    elle exigerait alors une declaration de trop. Une declaration de trop se
    voit et se corrige; une declaration manquante, non.
    """
    liaisons[nom] = liaisons.get(nom, frozenset()) | frozenset(valeurs)


def _liaisons_de_boucle(
    fonction: ast.FunctionDef, module: object
) -> dict[str, frozenset[str]]:
    """Ce qu'une variable de boucle peut valoir, lu dans la table parcourue.

    `for prefixe, issue in ISSUE_PREFIXES: return issue` rend un etat par
    entree de la table. Sans cette resolution, `ADOPTEE`, `REJETEE` et
    `REPORTEE` sortiraient de l'inventaire, et ce sont les trois issues les
    plus courantes du corpus.

    Une boucle dont la source n'est pas une table du module - `enumerate(mots)`
    - ne lie rien, et c'est sans danger: la variable reste inconnue, donc un
    `return` qui la rendrait leverait au lieu de passer. Ce qui n'est pas lie
    ici n'est pas ignore, il est seulement resolu plus tard, ou pas du tout.
    """
    liaisons: dict[str, frozenset[str]] = {}
    for node in ast.walk(fonction):
        if not isinstance(node, ast.For):
            continue
        if not isinstance(node.iter, ast.Name):
            continue
        table = getattr(module, node.iter.id, None)
        if not isinstance(table, (tuple, list, set, frozenset)):
            continue
        cible = node.target
        if isinstance(cible, ast.Name):
            _lier(liaisons, cible.id, (x for x in table if isinstance(x, str)))
        elif isinstance(cible, ast.Tuple):
            for rang, element in enumerate(cible.elts):
                if not isinstance(element, ast.Name):
                    raise _Irresoluble(f"cible de boucle, ligne {node.lineno}")
                _lier(
                    liaisons,
                    element.id,
                    (
                        ligne[rang]
                        for ligne in table
                        if isinstance(ligne[rang], str)
                    ),
                )
        else:
            raise _Irresoluble(f"cible de boucle, ligne {node.lineno}")
    return liaisons


def _valeurs(
    expr: ast.expr,
    module: object,
    liaisons: dict[str, frozenset[str]],
    attributs: dict[str, frozenset[str]],
) -> frozenset[str]:
    """Toutes les chaines qu'une expression peut valoir. Leve si elle ne sait pas."""
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return frozenset({expr.value})
    if isinstance(expr, ast.Name):
        if expr.id in liaisons:
            return liaisons[expr.id]
        valeur = getattr(module, expr.id, None)
        if isinstance(valeur, str):
            return frozenset({valeur})
        raise _Irresoluble(f"nom `{expr.id}` non resolu, ligne {expr.lineno}")
    if isinstance(expr, ast.IfExp):
        return _valeurs(expr.body, module, liaisons, attributs) | _valeurs(
            expr.orelse, module, liaisons, attributs
        )
    if isinstance(expr, ast.Attribute) and expr.attr in attributs:
        return attributs[expr.attr]
    raise _Irresoluble(
        f"expression {type(expr).__name__} non resolue, ligne {expr.lineno}"
    )


def etats_de_l_extracteur() -> frozenset[str]:
    """Tout ce que `_issue` peut rendre, plus le defaut du champ."""
    fonction = _fonction(_arbre(MODULES / "_resolutions_extraction.py"), "_issue")
    liaisons = _liaisons_de_boucle(fonction, EXTRACTION)
    etats: set[str] = set()
    retours = 0
    for node in ast.walk(fonction):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        retours += 1
        trouves = _valeurs(node.value, EXTRACTION, liaisons, {})
        if not trouves:
            raise _Irresoluble(f"`return` sans valeur lisible, ligne {node.lineno}")
        etats |= trouves
    if retours < 2:
        raise _Irresoluble("`_issue` ne rend plus la forme attendue")
    champ = next(
        c for c in dataclasses.fields(EXTRACTION.Resolution) if c.name == "resultat"
    )
    if not isinstance(champ.default, str) or not champ.default:
        raise _Irresoluble("le champ `resultat` n'a plus de defaut nomme")
    return frozenset(etats | {champ.default})


def _valeur_sous_la_cle(fonction: ast.FunctionDef, cle: str) -> ast.expr:
    trouvees = [
        valeur
        for node in ast.walk(fonction)
        if isinstance(node, ast.Dict)
        for nom, valeur in zip(node.keys, node.values)
        if isinstance(nom, ast.Constant) and nom.value == cle
    ]
    if len(trouvees) != 1:
        raise _Irresoluble(f"{len(trouvees)} ecritures de la cle `{cle}`, une attendue")
    return trouvees[0]


def etats_du_registre() -> frozenset[str]:
    """Tout ce qui peut atterrir dans la colonne `resultat` d'une ligne stockee.

    Le registre ajoute un etat que l'extracteur ne produit pas: une resolution
    seulement projetee n'a pas d'issue, et `to_rows` ecrit `PROJET`.
    """
    de_l_extracteur = etats_de_l_extracteur()
    fonction = _fonction(_arbre(MODULES / "_resolutions_registre.py"), "to_rows")
    valeur = _valeur_sous_la_cle(fonction, "resultat")
    etats = _valeurs(valeur, REGISTRE, {}, {"resultat": de_l_extracteur})
    if not etats >= de_l_extracteur:
        raise _Irresoluble("`to_rows` ne reecrit plus l'issue de l'extracteur")
    return etats


#: Les etats d'issue, derives. Calcules une fois: toute erreur de derivation
#: doit tomber a la collecte, pas se repartir sur les tests qui s'en servent.
ETATS = etats_du_registre()

#: L'issue du modele des actes que chacun devient, par la table du pont.
#:
#: Lue dans `ISSUES` et non par `issue_acte`: le defaut d'`issue_acte` est une
#: degradation de production, pas une declaration. Le faire entrer ici
#: rangerait un etat non declare parmi les lectures manquees, et les tests
#: suivants le trouveraient partout ou il faut - en cascade, autour d'un fait
#: qui n'a jamais ete decide. Un etat non declare doit faire tomber UN test,
#: celui qui dit qu'il n'est pas declare.
ACTES_PAR_ETAT = {
    etat: PONT.ISSUES[etat] for etat in sorted(ETATS) if etat in PONT.ISSUES
}

#: Les etats qui disent `le document conclut, la chaine n'a pas lu`. Derives eux
#: aussi: ce sont ceux que le pont traduit en `ISSUE_NON_LUE`.
NON_LUS = frozenset(
    etat for etat, acte in ACTES_PAR_ETAT.items() if acte == V.RESULTAT_ISSUE_NON_LUE
)


class DerivationTests(unittest.TestCase):
    """La derivation elle-meme, avant ce qu'elle sert a verifier.

    Un inventaire qui retrecit sans le dire rendrait tous les autres tests de ce
    fichier verts et vides. Ces trois-la sont ce qui l'empeche.
    """

    def test_l_inventaire_couvre_les_etats_connus_du_corpus(self) -> None:
        """Le plancher mesure. Il ne remplace pas la derivation: il la borne.

        Ces dix-la sont ceux que les deux cabinets du corpus ont produits. S'ils
        ne sortent plus de la derivation, c'est elle qui a cesse de lire, pas le
        code qui a cesse de les produire.
        """
        for etat in (
            "ADOPTEE",
            "REJETEE",
            "REPORTEE",
            "SANS_OBJET",
            "PAS_DE_VOTE",
            "VOTE_SANS_FORMULE",
            "SANS_ISSUE_TRACEE",
            "ISSUE_NON_RECONNUE",
            "ISSUE_ENONCEE_NON_LUE",
            "PROJET",
        ):
            with self.subTest(etat=etat):
                self.assertIn(etat, ETATS)

    def test_une_expression_non_lisible_leve_au_lieu_de_passer(self) -> None:
        """Le comportement qui rend l'inventaire fiable, teste sur du faux code."""
        expr = ast.parse("f(x)", mode="eval").body
        with self.assertRaises(_Irresoluble):
            _valeurs(expr, EXTRACTION, {}, {})

    def test_les_deux_etats_de_lecture_manquee_sont_derives_et_non_listes(
        self,
    ) -> None:
        """`NON_LUS` se deduit de la table du pont, il n'est ecrit nulle part.

        Un troisieme etat de meme nature entrera dans ce jeu le jour ou il sera
        traduit, sans qu'aucune ligne de ce fichier soit modifiee.
        """
        self.assertEqual(NON_LUS, {"ISSUE_NON_RECONNUE", "ISSUE_ENONCEE_NON_LUE"})


class SitesDEcritureTests(unittest.TestCase):
    """Qui, dans la voie resolutions, peut ecrire une issue.

    La derivation lit deux endroits. Si un troisieme se met a ecrire la colonne
    `resultat`, elle ne le verra pas - et c'est ici que ca doit tomber, avec le
    nom du site, plutot que dans un ecran six mois plus tard.
    """

    #: (fichier, portee) -> ce que le site fait. Un site absent de cette table
    #: fait tomber le test; un site de cette table qui disparait aussi.
    SITES = {
        ("_resolutions_extraction.py", "Resolution"): "defaut du champ",
        ("_resolutions_extraction.py", "parse_resolutions"): "resultat=_issue(...)",
        ("_resolutions_registre.py", "to_rows"): "cle 'resultat' de la ligne",
        ("_resolutions_assemblees.py", "copies_concurrentes"): "recopie d'une ligne lue",
    }

    def sites_reels(self) -> set[tuple[str, str]]:
        trouves: set[tuple[str, str]] = set()

        def parcourir(node: ast.AST, fichier: str, portee: str) -> None:
            for enfant in ast.iter_child_nodes(node):
                nom = portee
                if isinstance(enfant, (ast.FunctionDef, ast.ClassDef)):
                    nom = enfant.name
                if isinstance(enfant, ast.keyword) and enfant.arg == "resultat":
                    trouves.add((fichier, nom))
                if (
                    isinstance(enfant, ast.AnnAssign)
                    and isinstance(enfant.target, ast.Name)
                    and enfant.target.id == "resultat"
                ):
                    trouves.add((fichier, nom))
                if isinstance(enfant, ast.Dict):
                    for cle in enfant.keys:
                        if isinstance(cle, ast.Constant) and cle.value == "resultat":
                            trouves.add((fichier, nom))
                parcourir(enfant, fichier, nom)

        for fichier in sorted(MODULES.glob("_resolutions_*.py")) + [
            MODULES / "resolutions.py"
        ]:
            parcourir(_arbre(fichier), fichier.name, "<module>")
        return trouves

    def test_seuls_les_sites_nommes_ecrivent_une_issue(self) -> None:
        self.assertEqual(
            sorted(self.sites_reels()),
            sorted(self.SITES),
            "un site d'ecriture a ete ajoute ou retire: la derivation "
            "d'`etats_de_l_extracteur` doit etre revue avant d'ajuster cette liste",
        )


# --------------------------------------------------------------------------
# Les quatre tables aval
# --------------------------------------------------------------------------


class TableDuPontTests(unittest.TestCase):
    """Table 1: `_pont_actes_source.ISSUES`, registre -> modele des actes."""

    def test_chaque_etat_est_traduit_explicitement(self) -> None:
        for etat in sorted(ETATS):
            with self.subTest(etat=etat):
                self.assertIn(
                    etat,
                    PONT.ISSUES,
                    "sans entree, le pont rabat cet etat sur une valeur "
                    "approchante et la distinction est perdue en entrant "
                    "dans le modele des actes",
                )

    def test_le_defaut_n_affirme_plus_que_le_document_est_muet(self) -> None:
        """Le mecanisme du defaut, sur un jeton qu'aucune table ne connait.

        C'est la forme exacte du defaut mesure: un etat non declare devenait
        `SANS_ISSUE_TRACEE`, c'est-a-dire une affirmation sur la copropriete -
        `ce proces-verbal ne conclut pas` - tiree d'un oubli de declaration.
        """
        self.assertEqual(
            PONT.issue_acte("ETAT_QUE_PERSONNE_N_A_DECLARE"),
            V.RESULTAT_ISSUE_NON_LUE,
        )

    def test_une_colonne_vide_reste_une_absence_et_non_une_lecture_manquee(
        self,
    ) -> None:
        """Le registre qui ne porte rien n'accuse pas la chaine de mal lire."""
        self.assertEqual(PONT.issue_acte(""), V.RESULTAT_SANS_ISSUE)


class VocabulaireDesActesTests(unittest.TestCase):
    """Table 2: `_actes_vocabulaire.RESULTATS`, la liste fermee de la colonne."""

    def test_toute_traduction_atterrit_dans_le_vocabulaire_ferme(self) -> None:
        """`_actes_store` refuse a l'ecriture ce qui n'est pas dans cette liste."""
        for etat, acte in sorted(ACTES_PAR_ETAT.items()):
            with self.subTest(etat=etat):
                self.assertIn(acte, V.RESULTATS)
                self.assertTrue(V.resultat_valide(acte))

    def test_les_lectures_manquees_ne_reutilisent_aucune_valeur_qui_dit_autre_chose(
        self,
    ) -> None:
        """Le point du lot: aucune des cinq valeurs d'origine ne pouvait servir.

        `SANS_ISSUE_TRACEE` dit que le document ne dit rien, `VOTE_SANS_FORMULE`
        qu'aucune issue n'est enoncee. Les deux sont faux ici, et les deux
        etaient des reponses plausibles - c'est pour cela que la sixieme valeur
        existe.
        """
        self.assertTrue(NON_LUS)
        for etat in sorted(NON_LUS):
            with self.subTest(etat=etat):
                self.assertNotIn(
                    ACTES_PAR_ETAT[etat],
                    (
                        V.RESULTAT_SANS_ISSUE,
                        V.RESULTAT_VOTE_SANS_FORMULE,
                        V.RESULTAT_ADOPTEE,
                        V.RESULTAT_REJETEE,
                    ),
                )


class EcranDesResolutionsTests(unittest.TestCase):
    """Table 3: `resolutions_view`, ce que le coproprietaire lit."""

    def test_chaque_etat_a_un_libelle(self) -> None:
        for etat in sorted(ETATS):
            with self.subTest(etat=etat):
                self.assertIn(
                    etat,
                    ECRAN_RESOLUTIONS.LIBELLES_RESULTAT,
                    "sans libelle, l'ecran affiche le jeton brut",
                )

    def test_aucun_libelle_n_en_double_un_autre(self) -> None:
        """Deux etats sous le meme mot valent un etat manquant.

        Le libelle est le seul endroit ou la distinction atteint un lecteur.
        Recopier celui du voisin la supprime aussi surement que l'oubli.
        """
        libelles = [
            ECRAN_RESOLUTIONS.LIBELLES_RESULTAT[etat]
            for etat in sorted(ETATS)
            if etat in ECRAN_RESOLUTIONS.LIBELLES_RESULTAT
        ]
        self.assertEqual(len(libelles), len(set(libelles)))

    def test_le_document_muet_et_la_lecture_manquee_ne_se_disent_pas_pareil(
        self,
    ) -> None:
        muet = ECRAN_RESOLUTIONS.LIBELLES_RESULTAT["SANS_ISSUE_TRACEE"]
        for etat in sorted(NON_LUS):
            with self.subTest(etat=etat):
                self.assertNotEqual(
                    ECRAN_RESOLUTIONS.LIBELLES_RESULTAT.get(etat), muet
                )

    def test_une_lecture_manquee_est_appelee_a_relecture(self) -> None:
        """La liste de relecture est le seul chemin de reparation.

        `ISSUE_ENONCEE_NON_LUE` en etait absent: la ligne s'affichait avec un
        jeton brut et n'entrait dans aucun compteur - invisible deux fois.
        """
        for etat in sorted(NON_LUS):
            with self.subTest(etat=etat):
                self.assertIn(etat, ECRAN_RESOLUTIONS.RESULTATS_A_RELIRE)


class EcranDeGouvernanceTests(unittest.TestCase):
    """Table 4: `_controle_gouvernance_vocabulaire.RESULTATS`.

    Cet ecran affiche la colonne `a.resultat` du modele des actes, pas le
    registre. La chaine complete se verifie donc en bout: etat de la voie
    resolutions -> table du pont -> libelle lu par l'utilisateur.
    """

    def test_chaque_etat_reste_nomme_jusqu_a_l_ecran(self) -> None:
        for etat, acte in sorted(ACTES_PAR_ETAT.items()):
            with self.subTest(etat=etat, acte=acte):
                self.assertIn(
                    acte,
                    ECRAN_ACTES.RESULTATS,
                    "l'ecran de gouvernance perd cet etat au dernier metre",
                )

    def test_le_vocabulaire_affiche_couvre_le_vocabulaire_ecrit(self) -> None:
        """Aucune valeur ecrite en colonne ne doit rester sans libelle."""
        self.assertEqual(set(ECRAN_ACTES.RESULTATS), set(V.RESULTATS))

    def test_aucun_libelle_n_en_double_un_autre(self) -> None:
        libelles = list(ECRAN_ACTES.RESULTATS.values())
        self.assertEqual(len(libelles), len(set(libelles)))


# --------------------------------------------------------------------------
# Aucune vue ne compte ces etats parmi les adoptees ou les rejetees
# --------------------------------------------------------------------------


class ComptagesTests(unittest.TestCase):
    """Une issue non lue comptee comme adoptee fonderait une depense.

    Les compteurs comparent par egalite, jamais par prefixe - c'est ce qui rend
    la confusion impossible aujourd'hui. Ces tests fixent cette propriete au
    lieu de la laisser tenir par accident.
    """

    def test_les_compteurs_de_l_ecran_ne_prennent_que_l_etat_exact(self) -> None:
        self.assertEqual(set(ECRAN_RESOLUTIONS.COMPTES["adoptees"]), {"ADOPTEE"})
        self.assertEqual(set(ECRAN_RESOLUTIONS.COMPTES["rejetees"]), {"REJETEE"})

    def test_aucune_lecture_manquee_n_entre_dans_un_compteur_de_vote(self) -> None:
        for cle, valeurs in ECRAN_RESOLUTIONS.COMPTES.items():
            for etat in sorted(NON_LUS):
                with self.subTest(compteur=cle, etat=etat):
                    self.assertNotIn(etat, valeurs)

    def test_une_lecture_manquee_tombe_dans_hors_comptage(self) -> None:
        """Elle n'est pas comptee, et l'addition retombe quand meme juste."""
        lignes = [
            {"resultat": "ADOPTEE"},
            {"resultat": "ISSUE_ENONCEE_NON_LUE"},
            {"resultat": "ISSUE_NON_RECONNUE"},
        ]
        comptages = ECRAN_RESOLUTIONS._comptages(lignes)
        self.assertEqual(comptages["adoptees"], 1)
        self.assertEqual(comptages["rejetees"], 0)
        self.assertEqual(comptages["hors_comptage"], 2)

    def test_le_registre_ne_compte_aucune_lecture_manquee_comme_un_vote(self) -> None:
        resolutions = [
            EXTRACTION.Resolution(numero=rang + 1, objet="", resultat=etat)
            for rang, etat in enumerate(sorted(NON_LUS))
        ]
        comptes = REGISTRE.summarize(resolutions)
        self.assertEqual(comptes["adoptees"], 0)
        self.assertEqual(comptes["rejetees"], 0)
        self.assertEqual(comptes["total"], len(NON_LUS))

    def test_aucune_lecture_manquee_n_autorise_une_depense(self) -> None:
        for etat in sorted(NON_LUS):
            with self.subTest(etat=etat):
                self.assertNotIn(ACTES_PAR_ETAT[etat], V.RESULTATS_AUTORISANTS)

    def test_le_sql_des_vues_n_assimile_aucune_lecture_manquee_a_un_vote(
        self,
    ) -> None:
        """Les vues comparent `a.resultat` a des litteraux. On les relit tous.

        Une issue non lue ne doit apparaitre dans aucune branche qui conclut a
        une piece produite: la piece existe, mais elle ne conclut rien de lu.
        """
        sql = "\n".join(VUES.VUES)
        produites = set(
            re.findall(r"resultat\s*=\s*'([^']*)'\s*THEN\s*'PIECE_PRODUITE'", sql)
        )
        self.assertTrue(produites, "les branches attendues ont disparu du SQL")
        for etat in sorted(NON_LUS):
            with self.subTest(etat=etat):
                self.assertNotIn(ACTES_PAR_ETAT[etat], produites)

    def test_une_lecture_manquee_ne_s_affiche_pas_comme_une_piece_manquante(
        self,
    ) -> None:
        """Le document existe et il conclut. Lui reprocher une absence est faux.

        Sans branche dediee, `ISSUE_NON_LUE` tombait dans l'`ELSE 'ABSENT'` et
        l'ecran annoncait un proces-verbal manquant - le defaut deja corrige le
        2026-09-04 pour `SANS_ISSUE_TRACEE`, qui se serait repose tel quel.
        """
        sql = "\n".join(VUES.VUES)
        self.assertIn(
            f"resultat = '{V.RESULTAT_ISSUE_NON_LUE}' THEN 'AFFIRME_SANS_PIECE'",
            sql,
        )


if __name__ == "__main__":
    unittest.main()
