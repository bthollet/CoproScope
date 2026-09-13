from __future__ import annotations

from typing import Any, Callable

from ..modules import (
    agscope,
    biffageops,
    convocation,
    coprolink,
    docuscope,
    pont_actes,
    privacyops,
    resolutions,
)
from .due_diligence import summarize_due_diligence

# La suite qui va de l'assemblee lue jusqu'aux actes verses, ecrite UNE fois.
#
# Elle etait ecrite deux fois et les deux copies divergeaient: `web/depot.py` la
# portait, cette chaine-ci ne la portait pas, et `convocation.build_register`
# n'etait appele par aucune des deux. Une reabsorption par le CLI - la voie que
# la doctrine recommande pour eprouver un gros changement sur une instance vide -
# ne remplissait donc jamais l'ecran de gouvernance.
#
# L'ordre porte deux dependances reelles: le pont lit ce que les deux registres
# precedents ont ecrit, et `agscope` reconnait l'assemblee dont ils ont besoin.
# Les quatre fonctions ont deja la meme forme `(instance, run)`, ce que la
# docstring de `pont_actes.build_actes` dit explicitement.
SEQUENCE_GOUVERNANCE: tuple[tuple[str, Callable[..., Any]], ...] = (
    ("ag", agscope.analyze),
    ("resolutions", resolutions.build_register),
    ("convocations", convocation.build_register),
    ("actes", pont_actes.build_actes),
)


def run_gouvernance_sequence(
    instance,
    run,
    *,
    step: Callable[[str, Callable[[], Any]], Any] | None = None,
) -> list[dict[str, Any]]:
    """Joue la suite de gouvernance, quel que soit l'appelant.

    `step` permet a un appelant d'envelopper chaque etape sans redefinir la
    suite: `web/depot.py` y passe son `_run_step`, qui rattrape par etape et
    ecrit un manifeste. Sans `step`, les etapes sont appelees directement et une
    exception remonte, comme partout ailleurs dans cette chaine.

    Rend un compte-rendu par etape. Une etape qui ne peut rien faire le DIT -
    `coffre_non_declare`, `registre_vide` - au lieu de laisser croire a un
    succes: c'est ce silence qui rendait l'ecran vide sans explication.
    """
    rapport: list[dict[str, Any]] = []
    for nom, fonction in SEQUENCE_GOUVERNANCE:
        if step is not None:
            resultat = step(nom, lambda fonction=fonction: fonction(instance, run))
        else:
            resultat = fonction(instance, run)
        rapport.append({"etape": nom, "resultat": resultat if isinstance(resultat, dict) else {}})
    return rapport


def run_pipeline(
    instance,
    run,
    copy_classified: bool = True,
    docai_mode: str = "off",
) -> dict[str, Any]:
    """Absorbe une instance entiere, du document brut jusqu'aux actes.

    Rend un compte-rendu au lieu de `None`: la commande qui l'appelle imprimait
    `status: ok` en dur, donc une chaine qui ne produisait rien repondait
    exactement comme une chaine qui avait tout produit.
    """
    coprolink.bootstrap_instance_state(instance, run)
    docuscope.inventory(instance, run)
    docuscope.extract_text(instance, run, docai_mode=docai_mode)
    docuscope.classify(instance, run, copy_files=copy_classified)
    privacyops.screen_existing(instance, run, include_generated=False)
    biffageops.build_redaction_queue(instance, run)
    biffageops.build_markdown_corpus_if_enabled(instance, run)
    docuscope.missing_docs(instance, run)
    docuscope.compute_kpis(instance, run)
    gouvernance = run_gouvernance_sequence(instance, run)
    summarize_due_diligence(instance, run)
    return {"status": "ok", "gouvernance": gouvernance}
