# -*- coding: utf-8 -*-
"""Enregistrer la conclusion d'un controle. Le geste que la page promettait.

**Le defaut repare, et la page le declarait elle-meme.** Sous le tableau de
gouvernance, elle affichait: *« Le geste n'est pas encore cable : la table
traces_controle est lue par la colonne Ma conclusion et aucun geste de
l'application ne l'ecrit. »* La colonne montrait donc **toujours** `A instruire`,
quel que soit le travail fait par un humain devant l'ecran.

Mesure du 2026-09-09, faite par execution avec un autorisateur SQLite pose sur
chaque connexion au coffre: sur les neuf tables du lot gouvernance, **sept sont
ecrites par la chaine de production et deux ne le sont par personne** -
`dossiers_depense` et `traces_controle`. Seuls les tests les remplissaient.

**Arbitrage de Brice le 2026-09-09:** *« bien evidemment on trace le controle »*.

**Ce que ce module ecrit, et pourquoi rien ne peut l'effacer.** Une trace est
une **conclusion humaine**: elle ne derive d'aucun document. `_actes_store.ecrire`
l'anticipait deja - sa clause de suppression porte sur les documents cites, donc
appelee avec une liste de documents VIDE elle n'efface rien, et la garde des
corrections humaines protege le reste. Une re-extraction ne peut donc pas
supprimer une conclusion.

**`auteur` reste vide, et c'est une decision, pas un oubli.** Brice, le meme
jour: *« pour l'instant, pas d'auteur, on le garde pour plus tard »*. La colonne
existe au schema et sera remplie quand `RM-2026-0161` sera instruit - il dit
justement que la conclusion d'un controle a un auteur, et que cet auteur n'est
pas toujours le collectif. **Residu declare:** tant qu'elle est vide, deux
conclusions successives sur le meme sujet sont indiscernables quant a leur
auteur, et la derniere ecrite gouverne l'affichage.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from ..modules import _actes_schema as schema
from ..modules import _actes_store as store

#: Les trois verdicts que la page sait rendre, lus dans le vocabulaire de
#: l'ecran plutot que recopies: une quatrieme valeur ajoutee la-bas doit
#: apparaitre ici sans qu'on y pense, sinon la page saurait afficher ce que le
#: geste ne sait pas ecrire.
from ._controle_gouvernance_vocabulaire import CONCLUSIONS

#: **`a_instruire` n'est pas un verdict, c'est son absence.** Il vit dans le
#: meme dictionnaire parce que la page doit savoir l'AFFICHER, mais l'ecrire
#: reviendrait a enregistrer une conclusion disant qu'il n'y en a pas - et une
#: ligne ainsi ecrite serait indiscernable, a la lecture, d'un controle
#: reellement conclu comme *rien a dire*.
#:
#: Il etait deja refuse, mais **par accident**: la normalisation en majuscules
#: en faisait `A_INSTRUIRE`, absent du dictionnaire. Une justesse obtenue par
#: hasard tombe au premier changement de normalisation, donc on l'ecrit.
PAS_UN_VERDICT = "a_instruire"

#: Ce qu'un humain peut reellement conclure.
VERDICTS_ECRIVABLES = frozenset(CONCLUSIONS) - {PAS_UN_VERDICT}

#: Une conclusion est saisie par un humain. Le magasin refuse toute autre
#: origine sur cette table, et c'est ce refus qui la protege des re-extractions.
ORIGINE_HUMAINE = "CORRIGE_HUMAIN"

#: Ce qu'une conclusion peut porter comme sujet. `acte` est le seul que la
#: matrice sache relier aujourd'hui; les autres se declarent au lieu d'etre
#: acceptes en silence, parce qu'une trace rangee sous un sujet que rien ne lit
#: serait ecrite, invisible, et croirait avoir ete enregistree.
SUJETS_RELIES = ("acte",)

#: Longueur au-dela de laquelle le texte est refuse plutot que tronque. Une
#: conclusion coupee en silence dirait autre chose que ce que l'humain a ecrit.
TEXTE_MAX = 2000


class ConclusionRefusee(ValueError):
    """La conclusion n'a pas ete ecrite, et la raison est dans le message."""


def _horodate() -> str:
    return datetime.now(timezone.utc).astimezone().date().isoformat()


def construire_trace(sujet_kind: str, sujet_id: str, verdict: str, texte: str) -> dict[str, str]:
    """La ligne a ecrire, ou `ConclusionRefusee` avec ce qui manque.

    Toutes les verifications sont ici, avant le magasin: une conclusion refusee
    doit dire ce qui lui manque a l'humain qui vient de l'ecrire, pas rendre une
    erreur de base de donnees quinze couches plus bas.
    """
    sujet_kind = (sujet_kind or "").strip().lower()
    sujet_id = (sujet_id or "").strip()
    verdict = (verdict or "").strip().upper()
    texte = (texte or "").strip()

    if sujet_kind not in SUJETS_RELIES:
        raise ConclusionRefusee(
            "Sujet %r non relie: la conclusion serait ecrite et jamais lue. "
            "Sujets relies aujourd'hui: %s." % (sujet_kind, ", ".join(SUJETS_RELIES))
        )
    if not sujet_id:
        raise ConclusionRefusee("Aucune ligne designee: la conclusion porterait sur rien.")
    if verdict.lower() == PAS_UN_VERDICT:
        raise ConclusionRefusee(
            "« À instruire » est l'absence de conclusion, pas une conclusion: "
            "l'enregistrer rendrait un contrôle non fait indiscernable d'un "
            "contrôle conclu sans réserve."
        )
    if verdict not in VERDICTS_ECRIVABLES:
        raise ConclusionRefusee(
            "Verdict %r inconnu. Conclusions possibles: %s."
            % (verdict, ", ".join(sorted(VERDICTS_ECRIVABLES)))
        )
    if len(texte) > TEXTE_MAX:
        raise ConclusionRefusee(
            "Texte de %d caracteres, maximum %d. Il serait tronque en silence, "
            "donc il est refuse." % (len(texte), TEXTE_MAX)
        )

    return {
        "trace_id": "TRACE-%s" % secrets.token_hex(5).upper(),
        "sujet_kind": sujet_kind,
        "sujet_id": sujet_id,
        "verdict": verdict,
        "texte": texte,
        # Vide par decision du 2026-09-09, voir l'en-tete du module.
        "auteur": "",
        "constate_le": _horodate(),
        # Une trace ne derive d'aucun document: la colonne reste vide, et c'est
        # elle qui fait que rien ne peut l'effacer par re-extraction.
        "doc_id": "",
        "origine": ORIGINE_HUMAINE,
    }


def enregistrer(instance: Any, sujet_kind: str, sujet_id: str,
                verdict: str, texte: str) -> dict[str, str]:
    """Ecrit la conclusion dans le coffre et rend la ligne ecrite.

    **La liste de documents est volontairement vide.** C'est ce qui empeche une
    re-extraction de supprimer une conclusion humaine: la clause de suppression
    du magasin porte sur les documents cites, et il n'y en a aucun.
    """
    ligne = construire_trace(sujet_kind, sujet_id, verdict, texte)
    store.ecrire(instance, schema.TABLE_TRACES, [ligne], [])
    return ligne
