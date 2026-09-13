"""Les dates du modele, et pourquoi elles doivent etre ordonnables.

Separe de `_actes_schema` le 2026-09-04, et pas seulement pour la taille du
fichier. Ce module ne declare pas une colonne, il tient une **condition de
validite** des vues: toute regle de droit du modele est une comparaison de
chaines.

    x.date_effet > a.date_effet            -- echeance de l'article 21-5
    dep.date_depense <= d.valide_au        -- plafond de l'article 21-2
    a.date_effet > d.valide_au             -- delegation expiree

Une comparaison de chaines n'est juste que si toutes les chaines sont dans le
meme format ordonnable. Rien ne l'imposait: le commentaire `ISO` de
`ACTE_FIELDS` etait une intention, et `acte_id_resolution` acceptait n'importe
quelle chaine.

**Deux erreurs de sens oppose, mesurees, toutes deux muettes.** Sur des dates
`jj/mm/aaaa`: une depense d'urgence du 15/11/2024 avec une assemblee du
05/01/2025 rendait une echeance vide et le constat accusait le syndic de
n'avoir tenu aucune assemblee depuis - alors qu'une assemblee avait bien eu
lieu. Et une delegation valide jusqu'au 03/07/2026 avec une depense du
15/09/2024 rendait un cumul de 0,00 EUR, donc aucun depassement de plafond,
parce que `'15/09/2024' <= '03/07/2026'` est faux. Le meme jeu de donnees en
ISO donne les bonnes reponses dans les deux cas.

La justesse du modele dependait donc d'une convention qu'aucune couche
n'imposait. Elle est imposee au point d'ecriture, par `_actes_store.ecrire`.

**L'axe, et ce qui reste vrai le long de l'axe.** La maniere dont un cabinet
ecrit une date est un degre de liberte: ordre des composants, separateur,
zeros de tete. Ce qui ne varie pas est qu'une date porte un jour, un mois et
une annee de quatre chiffres. C'est cet invariant qui est lu ici. Hors des
formes reconnues, le code ne devine pas: il leve, ce qui est la degradation
propre exigee - une valeur non ordonnable ne rend pas une comparaison fausse
une fois sur deux, elle la rend fausse toujours.
"""

from __future__ import annotations

import re

_ISO_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_JJMMAAAA_RE = re.compile(r"^(\d{1,2})[/.](\d{1,2})[/.](\d{4})$")


class DateNonOrdonnable(ValueError):
    """Une date qu'aucune comparaison de chaines ne peut ordonner."""


def date_iso(valeur: str) -> str:
    """La date en `AAAA-MM-JJ`, ou `''` si elle est absente. Leve sinon.

    Une date absente reste absente: c'est un fait, et le modele sait le dire -
    `PV_SANS_DATE_LUE`, `ECHEANCE_INCALCULABLE`. Une date illisible est autre
    chose: une erreur d'extraction, que l'appelant doit ecarter ou corriger, et
    que ranger telle quelle rendrait indiscernable d'une date valide.
    """
    texte = str(valeur or "").strip()
    if not texte:
        return ""
    if _ISO_RE.match(texte):
        annee, mois, jour = texte.split("-")
    else:
        franc = _JJMMAAAA_RE.match(texte)
        if not franc:
            raise DateNonOrdonnable(
                f"Date illisible: {valeur!r}. Attendu 'AAAA-MM-JJ' ou "
                "'jj/mm/aaaa'. Toutes les regles de droit du modele comparent "
                "ces chaines entre elles: une forme non ordonnable rend une "
                "echeance ou un plafond faux, en silence."
            )
        jour, mois, annee = franc.groups()
    if not (1 <= int(mois) <= 12 and 1 <= int(jour) <= 31):
        raise DateNonOrdonnable(
            f"Date impossible: {valeur!r} (mois {mois}, jour {jour})."
        )
    return f"{annee}-{int(mois):02d}-{int(jour):02d}"
