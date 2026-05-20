from __future__ import annotations

from ..core.common import InstanceConfig, RunContext, write_text


STRATEGY_MARKDOWN = """# Strategie CoproScope gestion copro

CoproScope evolue vers un cockpit local-first pour conseil syndical:

- DocOps structure les pieces et les preuves.
- SyndicOps suit les demandes, relances, reponses et engagements.
- ComptaScope reconstitue des ecritures candidates depuis les factures et les annexes.
- AGOps suit les resolutions et leurs suites.
- WorksOps suit devis, travaux, receptions et garanties.
- Audit360 controle transversalement les risques, anomalies et preuves.
- GristOps exporte les registres vers des tableaux collaboratifs locaux.
- EvidenceOps produit des rapports SQL/Markdown reproductibles.

La regle centrale reste la tracabilite: toute ligne structuree doit renvoyer a une source.
"""


def export_strategy(instance: InstanceConfig, run: RunContext) -> dict[str, object]:
    reports_dir = instance.artifact("reports_dir")
    path = reports_dir / "strategie_coproscope_gestion_copro.md"
    write_text(path, STRATEGY_MARKDOWN)
    run.log_action("strategy_export", path, "strategy roadmap exported")
    return {"status": "ok", "path": str(path)}
