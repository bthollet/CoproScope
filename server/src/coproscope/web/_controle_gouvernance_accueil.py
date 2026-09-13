"""L'accueil du controle de gouvernance: des pastilles qui filtrent la liste sur place.

`RM-2026-0183`, recette de Brice du 2026-09-13: *la liste des operations sur la
page d'accueil*, *des boites de constats compactes qui filtrent sur place*, et
*un seul bloc etabli / pas etabli, avec des codes*.

**AUCUN NOMBRE NOUVEAU.** Ce module ne compte rien. Le nombre d'une pastille
reste `mesurer()`, et les signaux d'une ligne sont obtenus en appelant **le
meme predicat** `appliquer_filtres` une fois par constat: la pastille et la
ligne ne peuvent donc pas diverger. Le JavaScript de la page ne recalcule rien
non plus - il recharge l'adresse que le serveur a construite.

**DEUX AXES, UN CANAL CHACUN** (`RM-2026-0118`, memoire *alerte machine et
verdict humain*):

- *qui l'etablit* - les pieces ou l'outil - est porte par `data-etabli`, et la
  feuille ne lui donne qu'une FORME: trait plein ou tirets, `!` ou `?`;
- *faut-il agir* est porte par `data-alerte`, et la feuille ne lui donne
  qu'une COULEUR: rouge, orange, gris.

Le verdict humain ne passe par aucun de ces deux canaux: il vit dans la marge.
"""

from __future__ import annotations

from typing import Any

from . import _controle_gouvernance_constats as C
from ._controle_gouvernance_source import appliquer_filtres

#: Le niveau d'alerte, derive du `ton` du constat. Une table, pas un calcul:
#: un ton inconnu demain tombe sur `non`, et la pastille reste grise et
#: sans signe au lieu d'inventer une alerte.
ALERTE_PAR_TON: dict[str, str] = {"danger": "forte", "warn": "oui", "info": "non", "ok": "non"}
RANG_ALERTE: dict[str, int] = {"forte": 0, "oui": 1, "non": 2}

#: Le texte d'action, en toutes lettres: il double la couleur.
GESTE_PAR_ALERTE: dict[str, str] = {
    "forte": "à instruire d'abord", "oui": "à examiner", "non": "rien à signaler par l'outil",
}

#: Habillage court d'une pastille, repris du brouillon du designer. Une table
#: qui HABILLE: un constat qu'elle ne nomme pas garde son titre long et le
#: geste de son niveau d'alerte, il ne disparait pas.
TITRE_COURT: dict[str, str] = {
    "acte_sans_fondement": "Décision sans délégation",
    "urgence_jamais_portee": "Urgence jamais ratifiée",
    "issue_non_enoncee": "Issue du vote non énoncée",
    "plafond_depasse": "Plafond de délégation franchi",
    "delegation_expiree": "Délégation expirée",
    "obligation_non_tenue": "Obligation non tenue",
    "montant_divergent": "Payé autrement que voté",
    "majorite_non_enoncee": "Majorité non énoncée",
    "acte_sans_execution": "Aucune dépense rattachée",
    "avis_manquant": "Avis du conseil non rattaché",
    "avis_sans_exigence": "Avis du conseil : aucun seuil établi",
    "type_non_reconnu": "Nature de la décision non reconnue",
    "issue_non_lue_a_relire": "Issue non lue par l'outil",
    "rejetee": "Résolution rejetée",
    "pas_de_vote": "Résolution non votée",
    "adoptee": "Adoptée, rien ne la contredit",
}
GESTE: dict[str, str] = {
    "acte_sans_fondement": "à réclamer au syndic",
    "urgence_jamais_portee": "à réclamer au syndic",
    "issue_non_enoncee": "question au syndic",
    "plafond_depasse": "à porter en assemblée",
    "delegation_expiree": "à vérifier dans les comptes",
    "obligation_non_tenue": "à réclamer au syndic",
    "montant_divergent": "à réclamer au syndic",
    "majorite_non_enoncee": "question au syndic",
    "acte_sans_execution": "à vérifier dans les comptes",
    "avis_manquant": "à relire par vous",
    "avis_sans_exigence": "rien à réclamer à ce stade",
    "type_non_reconnu": "à relire par vous",
    "issue_non_lue_a_relire": "à relire par vous",
    "rejetee": "à rapprocher des dépenses",
    "pas_de_vote": "à vérifier dans les comptes",
    "adoptee": "rien à signaler par l'outil",
}


def alerte_de(constat: dict[str, Any]) -> str:
    return ALERTE_PAR_TON.get(str(constat.get("ton") or ""), "non")


def signe_de(constat: dict[str, Any]) -> str:
    """`!` quand les pieces l'etablissent, `?` quand l'outil ne sait pas; aucun
    signe sans alerte - la presence du signe double la couleur."""
    if alerte_de(constat) == "non":
        return ""
    return "!" if constat.get("source") == C.SOURCE_PIECES else "?"


def _habiller(constat: dict[str, Any]) -> dict[str, str]:
    alerte = alerte_de(constat)
    return {
        "cle": constat["cle"],
        "titre": TITRE_COURT.get(constat["cle"], constat["titre"]),
        "etabli": str(constat.get("source") or ""),
        "alerte": alerte,
        "signe": signe_de(constat),
        "geste": GESTE.get(constat["cle"], GESTE_PAR_ALERTE[alerte]),
    }


def poser_signaux(lignes: list[dict[str, Any]]) -> None:
    """`l["signaux"]`: les constats dont le filtre retient la ligne.

    Le meme predicat que la pastille, appele une fois par constat. Une ligne
    que la pastille *Rejetees* compte porte donc le signal *Rejetee*, par
    construction et non par une seconde regle.
    """
    for ligne in lignes:
        ligne["signaux"] = []
    par_id = {ligne["id"]: ligne for ligne in lignes}
    for constat in C.CONSTATS:
        habit = _habiller(constat)
        for retenue in appliquer_filtres(lignes, constat["filtre"]):
            par_id[retenue["id"]]["signaux"].append(habit)
    for ligne in lignes:
        ligne["signaux"].sort(key=lambda s: (RANG_ALERTE[s["alerte"]], s["etabli"] != C.SOURCE_PIECES))


def habiller_pastilles(
    mesures: list[dict[str, Any]], constat_actif: str, filtres: dict[str, str]
) -> list[dict[str, Any]]:
    """Chaque mesure recoit ses deux axes, son geste, et l'etat *filtre pose*.

    Une pastille n'est active que si l'adresse porte SON constat ET exactement
    ses filtres: un filtre retouche a la main dans le tableau ne laisse pas une
    pastille pretendre qu'elle est la selection affichee.

    L'ordre suit l'alerte - une pastille grise ne passe plus devant une orange -
    et, a alerte egale, l'ordre de `CONSTATS`.
    """
    rang = {constat["cle"]: i for i, constat in enumerate(C.CONSTATS)}
    for mesure in mesures:
        mesure.update(_habiller(mesure["constat"]))
        mesure["actif"] = (mesure["constat"]["cle"] == constat_actif
                           and dict(filtres) == dict(mesure["constat"]["filtre"]))
    return sorted(mesures, key=lambda m: (RANG_ALERTE[m["alerte"]], rang[m["constat"]["cle"]]))
