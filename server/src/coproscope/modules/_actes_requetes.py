"""Le contrat de filtrage: quelle colonne se filtre, et a quel prix.

Brice veut filtrer chaque colonne du tableau de controle independamment. Ce
module dit lesquelles se filtrent sans jointure, lesquelles en exigent une,
lesquelles sont des agregats - et il **interdit structurellement** la seule
chose que le schema existe pour rendre impossible.

----------------------------------------------------------------------
Le contre-exemple, et pourquoi il est interdit ici
----------------------------------------------------------------------

Cote comptes, la cellule `Decision / devis` decide aujourd'hui son statut en
cherchant les mots `decision`, `devis`, `vote` dans la concatenation de TOUTES
les valeurs de la ligne (`web/compta_rapprochement_view.py`,
`_decision_cell_status` alimente par `_row_text`). Trois consequences:

- la cellule change d'etat quand un fournisseur s'appelle `DEVIS SERVICES`;
- elle ne peut pas etre filtree, parce qu'il n'y a rien a filtrer;
- elle ne peut pas etre prise en defaut, parce qu'elle ne cite aucune donnee.

Ici, chaque filtre est declare, associe a une colonne reelle, et n'emet que des
comparaisons d'egalite, d'appartenance, d'ordre ou de nullite. Aucun operateur
de texte n'est atteignable: `LIKE`, `GLOB`, `MATCH`, `REGEXP` et la
concatenation `||` sont absents des operateurs autorises, et un test le verifie
sur **tous** les filtres declares. Un dev qui voudrait reintroduire le balayage
devrait d'abord casser ce test - ce qui est exactement le but.

Une recherche plein texte reste legitime dans une barre de recherche. Elle n'est
simplement pas un filtre de colonne de preuve, et elle ne passe pas par ici.

----------------------------------------------------------------------
Classement par cout, pas par apparence
----------------------------------------------------------------------

`v_matrice_gouvernance` presente les six cellules comme six colonnes. Ce serait
malhonnete de les classer `sans jointure` pour autant: sous la vue, chacune est
une sous-requete correlee sur `liens_gouvernance`. Elles sont donc classees
`JOINTURE`, et l'index `idx_liens_source` existe pour cela. Le classement
ci-dessous decrit ce que la requete coute, pas ce qu'elle a l'air de couter.
"""

from __future__ import annotations

import re

from typing import Any, Iterable, Sequence

# --------------------------------------------------------------------------
# Operateurs autorises - la liste est fermee, et c'est le point
# --------------------------------------------------------------------------

#: Aucun operateur de texte. Ajouter `LIKE` ici casserait le test
#: `test_aucun_filtre_ne_balaie_du_texte`, ce qui est le comportement voulu:
#: la regle est defendue par un test, pas par une convention.
OPERATEURS: dict[str, str] = {
    "eq": "= ?",
    "ne": "<> ?",
    "lt": "< ?",
    "lte": "<= ?",
    "gt": "> ?",
    "gte": ">= ?",
    "vide": "= ''",
    "non_vide": "<> ''",
    "in": None,  # traite a part: nombre de marques variable
}

OPERATEURS_INTERDITS = ("LIKE", "GLOB", "MATCH", "REGEXP", "||")

# --------------------------------------------------------------------------
# Le classement
# --------------------------------------------------------------------------

COUT_DIRECT = "ATTRIBUT_DIRECT"
COUT_JOINTURE = "JOINTURE"
COUT_AGREGAT = "AGREGAT"

#: nom public -> (vue, colonne, cout, ce que la colonne dit)
#:
#: La vue nommee est celle qu'il faut interroger. `v_actes` et `v_dossiers`
#: appliquent deja la regle "la correction humaine gagne a la lecture": un
#: filtre ne doit jamais viser la table nue, sinon il verrait les deux versions.
FILTRES: dict[str, tuple[str, str, str, str]] = {
    # --- Acte: attributs directs -------------------------------------------
    "exercice": ("v_actes", "exercice", COUT_DIRECT,
                 "colonne, jamais un decoupage: decision back n. 1"),
    "nature": ("v_actes", "nature", COUT_DIRECT,
               "RESOLUTION_AG | DECISION_CS_DELEGUEE | URGENCE_SYNDIC"),
    "etat": ("v_actes", "etat", COUT_DIRECT, "CONSTATEE | PROJETEE"),
    # L'axe "sur quoi porte l'acte", a ne pas confondre avec `nature`, qui dit
    # d'ou vient l'autorisation. C'est ce filtre qui repond a la demande de
    # Brice du 2026-09-04 - separer les engagements de depense des elections et
    # des autorisations donnees a un coproprietaire - et c'est le meme qui borne
    # les controles, via `_actes_vocabulaire.HORS_CONTROLE`.
    "portee": ("v_actes", "portee", COUT_DIRECT,
               "designation, engagement de depense, autorisation a un "
               "coproprietaire, delegation, seuil, budget, comptes, modalites"),
    "resultat": ("v_actes", "resultat", COUT_DIRECT, "ADOPTEE | REJETEE | ..."),
    "assemblee": ("v_actes", "ag_id", COUT_DIRECT, "l'assemblee d'origine"),
    "date_effet": ("v_actes", "date_effet", COUT_DIRECT,
                   "date de l'acte; '' signifie date non lue"),
    "montant_autorise": ("v_actes", "montant_autorise", COUT_DIRECT,
                         "montant vote ou plafond de delegation"),
    "origine": ("v_actes", "origine", COUT_DIRECT, "EXTRAIT | CORRIGE_HUMAIN"),
    "document": ("v_actes", "doc_id", COUT_DIRECT, "document d'origine"),

    # --- Depense: attributs directs ----------------------------------------
    "depense_exercice": ("v_dossiers", "exercice", COUT_DIRECT, ""),
    "depense_date": ("v_dossiers", "date_depense", COUT_DIRECT,
                     "c'est elle qui sert au cumul, pas l'exercice"),
    "depense_montant": ("v_dossiers", "montant_ttc", COUT_DIRECT, ""),
    "fournisseur": ("v_dossiers", "fournisseur", COUT_DIRECT,
                    "egalite sur un fournisseur normalise, jamais un LIKE"),
    "imputation": ("v_dossiers", "imputation", COUT_DIRECT,
                   "BUDGET_PREVISIONNEL | VOTE_SEPARE | FONDS_TRAVAUX | INDETERMINE"),
    "aiguillage": ("v_dossiers", "aiguillage", COUT_DIRECT,
                   "articles 44 et 45; NON_TESTE tant que le trou T4 est ouvert"),

    # --- Les cellules de la matrice: une jointure indexee ------------------
    # Les deux normes de l'article 21 alinea 2 se filtrent SEPAREMENT depuis le
    # 2026-09-08. Un filtre unique `cel_seuil` aurait melange le montant qui
    # declenche la consultation du conseil syndical et celui qui declenche la
    # mise en concurrence: une file de travail construite dessus aurait rendu
    # des actes qui manquent l'un ou l'autre sans dire lequel.
    "cel_seuil_consultation_cs": (
        "v_matrice_gouvernance", "cel_seuil_consultation_cs", COUT_JOINTURE,
        "montant a partir duquel la consultation du conseil syndical est "
        "obligatoire (art. 21 al. 2, premiere phrase)"),
    "cel_seuil_concurrence": (
        "v_matrice_gouvernance", "cel_seuil_concurrence", COUT_JOINTURE,
        "montant a partir duquel la mise en concurrence est obligatoire "
        "(art. 21 al. 2, seconde phrase, hors contrat de syndic)"),
    "cel_seuil": ("v_matrice_gouvernance", "cel_seuil", COUT_JOINTURE,
                  "seuil rattache dont l'obligation declenchee n'a pas ete "
                  "identifiee: le residu, filtrable pour etre resorbe"),
    "cel_avis_cs": ("v_matrice_gouvernance", "cel_avis_cs", COUT_JOINTURE,
                    "consultation prealable de l'art. 21 al. 2; "
                    "PIECE_PRODUITE | AFFIRME_SANS_PIECE | ABSENT | NON_APPLICABLE"),
    "cel_rapport_cs": ("v_matrice_gouvernance", "cel_rapport_cs", COUT_JOINTURE,
                       "compte rendu annuel du conseil syndical (decret art. 22 "
                       "al. 2); exigible des comptes et de la delegation seules"),
    "cel_resolution": ("v_matrice_gouvernance", "cel_resolution", COUT_JOINTURE,
                       "l'adoption est-elle enoncee dans le texte"),
    "cel_annexe": ("v_matrice_gouvernance", "cel_annexe", COUT_JOINTURE, ""),
    "cel_devis": ("v_matrice_gouvernance", "cel_devis", COUT_JOINTURE, ""),
    "cel_execution": ("v_matrice_gouvernance", "cel_execution", COUT_JOINTURE,
                      "la sixieme source: ce qui a ete vote a-t-il ete fait"),

    # --- Constats: la file de travail --------------------------------------
    "constat": ("v_constats", "code", COUT_AGREGAT,
                "le nom de la rupture; c'est le tri par defaut de la file"),
    "constat_sujet": ("v_constats", "sujet_kind", COUT_AGREGAT,
                      "acte | dossier | document"),
    "constat_exercice": ("v_constats", "exercice", COUT_AGREGAT, ""),
    "constat_montant": ("v_constats", "montant_en_jeu", COUT_AGREGAT,
                        "l'euro en jeu, ou l'euro vote et jamais paye"),
    "constat_echeance": ("v_constats", "date_echeance", COUT_AGREGAT,
                         "la date que l'obligation devait atteindre"),

    # --- Agregats de periode ------------------------------------------------
    "cumul_delegation": ("v_cumul_delegation", "cumul", COUT_AGREGAT,
                         "somme sur la PERIODE de delegation, pas sur l'exercice"),
    "plafond_delegation": ("v_cumul_delegation", "plafond", COUT_AGREGAT,
                           "article 21-2"),
    "depenses_rattachees": ("v_execution", "depenses_rattachees", COUT_AGREGAT, ""),
    "montant_paye": ("v_execution", "montant_paye", COUT_AGREGAT, ""),
}


class FiltreInconnu(ValueError):
    """Un filtre non declare. On ne devine pas un nom de colonne."""


def filtres_disponibles() -> dict[str, list[str]]:
    """Le contrat, groupe par cout. C'est le livrable lisible du module."""
    groupes: dict[str, list[str]] = {
        COUT_DIRECT: [], COUT_JOINTURE: [], COUT_AGREGAT: []
    }
    for nom, (_, _, cout, _) in sorted(FILTRES.items()):
        groupes[cout].append(nom)
    return groupes


def vue_du_filtre(nom: str) -> str:
    try:
        return FILTRES[nom][0]
    except KeyError as exc:  # pragma: no cover - message, pas logique
        raise FiltreInconnu(f"Filtre non declare: {nom}") from exc


def construire_where(
    criteres: Sequence[tuple[str, str, Any]],
) -> tuple[str, list[Any]]:
    """Rend la clause `WHERE` et ses parametres, ou rien si aucun critere.

    `criteres` est une suite de `(nom_de_filtre, operateur, valeur)`. Tous les
    criteres portent sur la meme vue: melanger deux vues serait une jointure
    implicite, et une jointure implicite est exactement la maniere dont les
    quatre comptages concurrents du produit se sont installes.
    """
    if not criteres:
        return "", []
    vues = {vue_du_filtre(nom) for nom, _, _ in criteres}
    if len(vues) > 1:
        raise FiltreInconnu(
            "Criteres repartis sur plusieurs vues " + ", ".join(sorted(vues))
            + " : construire une requete par vue, puis croiser explicitement."
        )
    morceaux: list[str] = []
    params: list[Any] = []
    for nom, operateur, valeur in criteres:
        _, colonne, _, _ = FILTRES[nom]
        if operateur == "in":
            valeurs = list(valeur) if isinstance(valeur, Iterable) and not isinstance(valeur, str) else [valeur]
            if not valeurs:
                # Un `IN ()` vide est une erreur de syntaxe en SQL et une
                # question sans reponse en metier: on le dit.
                raise FiltreInconnu(f"Filtre '{nom}': liste de valeurs vide.")
            marques = ",".join("?" for _ in valeurs)
            morceaux.append(f'"{colonne}" IN ({marques})')
            params.extend(valeurs)
            continue
        if operateur not in OPERATEURS:
            raise FiltreInconnu(
                f"Operateur non autorise: {operateur}. Autorises: "
                + ", ".join(sorted(OPERATEURS))
            )
        gabarit = OPERATEURS[operateur]
        # **Un operateur qui ne prend pas de valeur REFUSE qu'on lui en donne
        # une.** Constat `C092`. La ligne s'ecrivait `if "?" in gabarit:
        # params.append(valeur)`: pour `vide` et `non_vide`, dont le gabarit ne
        # porte aucune marque, la valeur etait **jetee sans un mot**.
        # `construire_requete([("date_effet", "vide", "2024-07-03")])` rendait
        # `WHERE "date_effet" = ''` et une liste de parametres VIDE - la date
        # demandee disparaissait, et la requete repondait a une autre question
        # que celle posee.
        #
        # L'invariant: **ce qu'un appelant fournit est employe ou refuse, jamais
        # perdu.** `None` et la chaine vide restent acceptes: ce sont les
        # marques naturelles du `je ne fournis rien`, et le seul appelant connu
        # ecrit `("vide", None)`.
        if "?" not in gabarit and valeur not in (None, ""):
            raise FiltreInconnu(
                f"Filtre '{nom}': l'operateur '{operateur}' ne prend aucune "
                f"valeur, et {valeur!r} en est une. Elle serait ignoree en "
                "silence: retirez-la, ou choisissez un operateur qui la lit."
            )
        morceaux.append(f'"{colonne}" {gabarit}')
        if "?" in gabarit:
            params.append(valeur)
    return " WHERE " + " AND ".join(morceaux), params


#: `ordre` etait la seule porte par ou du SQL d'appelant entrait dans la
#: requete: `sql += f" ORDER BY {ordre}"`, sans validation, alors que la liste
#: fermee d'operateurs et son test defendaient tout le reste. La docstring de
#: `lire_vue` affirmait deja "aucune chaine SQL ne vient de l'appelant"; elle
#: dit desormais vrai. On n'accepte qu'un nom de colonne connu du filtre, avec
#: un sens optionnel - jamais une expression.
_SENS = ("ASC", "DESC")

#: Un terme de tri, et rien d'autre: un nom de colonne, eventuellement dans un
#: CAST de type, eventuellement suivi de `IS NULL` pour ranger les vides, et
#: eventuellement d'un sens. Aucune parenthese libre, aucun operateur, aucun
#: guillemet, aucun point-virgule ne franchit ce gabarit.
_TERME_ORDRE = re.compile(
    r"^(?:CAST\(\s*(?P<caste>[A-Za-z_][A-Za-z_0-9]*)\s+AS\s+"
    r"(?:INTEGER|REAL|TEXT|NUMERIC)\s*\)|(?P<nu>[A-Za-z_][A-Za-z_0-9]*))"
    r"(?:\s+IS\s+(?:NOT\s+)?NULL)?"
    r"(?:\s+(?:ASC|DESC))?$",
    re.IGNORECASE,
)


def _ordre_sur(ordre: str) -> str:
    """Un tri valide terme par terme, jamais une chaine SQL libre.

    `ordre` etait la seule porte par ou du SQL d'appelant entrait dans la
    requete - `sql += f" ORDER BY {ordre}"`, sans validation - alors que la
    liste fermee d'operateurs et son test defendaient tout le reste, et que la
    docstring de `lire_vue` affirmait deja qu'aucune chaine SQL ne venait de
    l'appelant. Elle dit desormais vrai.

    On valide la FORME et non un registre de colonnes: une colonne inconnue
    leve une erreur SQL propre et bruyante, alors qu'une expression libre
    passait en silence. C'est le silence qu'on ferme ici.
    """
    termes = [t.strip() for t in ordre.split(",")]
    for terme in termes:
        if not _TERME_ORDRE.match(terme):
            raise FiltreInconnu(
                f"Tri refuse: {terme!r}. Un terme de tri est un nom de colonne, "
                "eventuellement dans un CAST, suivi au plus de `IS NULL` et d'un "
                "sens. Une expression libre ouvrirait la seule porte SQL restante."
            )
    return ", ".join(termes)


def construire_requete(
    criteres: Sequence[tuple[str, str, Any]],
    *,
    vue: str | None = None,
    ordre: str = "",
    limite: int | None = None,
) -> tuple[str, list[Any]]:
    """La requete complete. `vue` est deduite des criteres si elle est omise."""
    if vue is None:
        if not criteres:
            raise FiltreInconnu("Sans critere, la vue doit etre nommee.")
        vue = vue_du_filtre(criteres[0][0])
    where, params = construire_where(criteres)
    sql = f'SELECT * FROM "{vue}"{where}'
    if ordre:
        sql += " ORDER BY " + _ordre_sur(ordre)
    if limite is not None:
        sql += " LIMIT ?"
        params.append(int(limite))
    return sql, params


#: Requete de la charniere: `cet euro, qui l'a autorise ?`. C'est la seule
#: question de l'ecran comptes qui traverse vers l'ecran gouvernance, et elle
#: repond par un `EXISTS` indexe. C'est ce qui remplace le balayage de mots.
SQL_ACTES_DU_DOSSIER = """
SELECT a.*, l.provenance, l.force_probatoire, l.motif, l.doute, l.montant_impute
FROM liens_gouvernance l
JOIN v_actes a ON a.acte_id = l.source_id
WHERE l.relation = 'AUTORISE'
  AND l.target_kind = 'dossier' AND l.target_id = ?
  AND l.provenance <> 'HUMAIN_CONTREDIT'
ORDER BY CASE l.provenance
            WHEN 'HUMAIN_CONFIRME' THEN 0
            WHEN 'COPROSCOPE_CALCULE' THEN 1
            WHEN 'SYNDIC_AFFIRME' THEN 2 ELSE 3 END
"""
