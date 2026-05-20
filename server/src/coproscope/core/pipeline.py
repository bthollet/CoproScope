from __future__ import annotations

from ..modules import agscope, biffageops, coprolink, docuscope, privacyops
from .due_diligence import summarize_due_diligence


def run_pipeline(instance, run, copy_classified: bool = True, docai_mode: str = "off") -> None:
    coprolink.bootstrap_instance_state(instance, run)
    docuscope.inventory(instance, run)
    docuscope.extract_text(instance, run, docai_mode=docai_mode)
    docuscope.classify(instance, run, copy_files=copy_classified)
    privacyops.screen_existing(instance, run, include_generated=False)
    biffageops.build_redaction_queue(instance, run)
    docuscope.missing_docs(instance, run)
    docuscope.compute_kpis(instance, run)
    agscope.analyze(instance, run)
    summarize_due_diligence(instance, run)
