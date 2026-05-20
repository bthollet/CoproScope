from __future__ import annotations

from ..core.common import InstanceConfig, RunContext, write_text


STRATEGY_MARKDOWN = """# Strategie CoproScope gestion copro

CoproScope evolue vers un cockpit local-first pour conseil syndical.

Cap produit: preuve, action, memoire, diffusion sure.

- DocOps structure les pieces et les preuves.
- PrivacyOps qualifie la confidentialite et les colleges d'acces.
- BiffageOps prepare les versions biffees ou pseudonymisees.
- SyndicOps suit les demandes, relances, reponses et engagements.
- FactureOps extrait les factures candidates et anomalies de piece.
- ComptaScope reconstitue des ecritures candidates depuis les factures et les annexes.
- AGOps prepare les assemblees generales et doit evoluer vers le suivi post-AG.
- Audit360 controle transversalement faits, risques, preuves et actions.
- WorksOps, IncidentOps, ContractOps et CommsOps sont les prochaines chaines d'action.
- GristOps exporte les registres vers des tableaux collaboratifs locaux.
- EvidenceOps produit des rapports SQL/Markdown reproductibles.

La regle centrale reste la tracabilite: toute ligne structuree doit renvoyer a une source, une politique d'acces et une action attendue.
"""


def export_strategy(instance: InstanceConfig, run: RunContext) -> dict[str, object]:
    reports_dir = instance.artifact("reports_dir")
    path = reports_dir / "strategie_coproscope_gestion_copro.md"
    write_text(path, STRATEGY_MARKDOWN)
    run.log_action("strategy_export", path, "strategy feuille de route exported")
    return {"status": "ok", "path": str(path)}
