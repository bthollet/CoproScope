from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

from .core.common import RunContext, load_instance
from .core.doctor import run_doctor
from .core.due_diligence import summarize_due_diligence
from .core.pipeline import run_pipeline
from .core.share import audit_repo, export_shareable
from .vault import core as vault_core
from .modules import (
    accounting,
    agscope,
    audit360,
    biffageops,
    demoops,
    docai,
    decisionops,
    docuscope,
    evidenceops,
    factureops,
    drive_sync_now,
    drive_watch,
    drive_watch_loop,
    gdrive_rights,
    gdrive_transport,
    gdriveops,
    gristops,
    incidentops,
    instance_layout,
    instancegit,
    privacyops,
    strategy,
    tools,
    workers,
)


COMMAND_ALIASES = {
    "diagnostic": "doctor",
    "inventaire": "inventory",
    "extraire-texte": "extract-text",
    "classer": "classify",
    "pieces-manquantes": "missing-docs",
    "indicateurs": "kpi",
    "assemblee-generale": "ag",
    "diligence": "due-diligence",
    "chaine": "pipeline",
    "ia-doc": "docai",
    "factures": "invoices",
    "outils": "tools",
    "compta": "accounting",
    "confidentialite": "privacy",
    "interface": "ui",
    "demonstration": "demo",
    "decisions": "decisions",
    "signalements": "incidents",
    "strategie": "strategy",
    "coffre": "vault",
    "audit": "audit360",
    "audit-partage": "share-audit",
    "export-partage": "share-export",
    "lecteur": "drive",
    "instances": "instance",
}

SUBCOMMAND_ALIASES = {
    "ag_command": {"analyser": "analyze"},
    "dd_command": {"synthese": "summarize"},
    "pipeline_command": {"executer": "run"},
    "tools_command": {"statut": "status"},
    "accounting_command": {"reconstituer": "reconstruct", "controles": "controls"},
    "invoices_command": {"extraire": "extract"},
    "grist_command": {"synchroniser": "sync"},
    "evidence_command": {"construire": "build"},
    "workers_command": {"executer": "run"},
    "privacy_command": {
        "screening-existant": "screen-existing",
        "scanner-existant": "screen-existing",
        "biffer": "redact",
        "file-biffage": "redaction-queue",
        "biffer-requis": "redact-required",
    },
    "strategy_command": {"exporter": "export"},
    "ui_command": {"servir": "serve"},
    "demo_command": {"construire": "build"},
    "decisions_command": {"construire": "build"},
    "incidents_command": {"construire": "build"},
    "vault_command": {
        "initialiser": "init",
        "importer": "import",
        "importer-audit360-lignes": "import-audit360-rows",
        "statut": "status",
        "verifier": "verify",
    },
    "audit360_command": {"preparer-anonymise": "prepare-anonymized"},
    "drive_command": {"authentifier": "auth", "statut": "status", "fumee": "smoke"},
    "instance_command": {"initialiser-git": "git-init", "statut-git": "git-status", "arborescence": "layout"},
    "instance_layout_command": {"planifier": "plan"},
}


def _ui_open_test_notice() -> str:
    return (
        "Mode test visible AV-safe: serveur au premier plan, arret avec Ctrl+C.\n"
        "Ne pas lancer de scan de ports, taskkill, Start-Process cache ou ouverture navigateur automatique."
    )


def _instance_parent() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--instance", help="Chemin vers un fichier instance.yml ou un dossier d'instance.")
    parent.add_argument("--instance-root", help="Chemin vers un dossier d'instance contenant instance.yml.")
    return parent


def _vault_parent() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--local-root", required=True, help="Racine locale jetable/reconstructible du vault.")
    parent.add_argument("--sync-root", required=True, help="Racine synchronisable chiffree du vault.")
    return parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="coprocs", description="CLI CoproScope")
    subparsers = parser.add_subparsers(dest="command", required=True)
    instance_parent = _instance_parent()

    subparsers.add_parser("doctor", aliases=["diagnostic"], parents=[instance_parent], help="Diagnostiquer une instance et ses dependances.")
    subparsers.add_parser("inventory", aliases=["inventaire"], parents=[instance_parent], help="Inventorier les documents bruts.")

    extract = subparsers.add_parser("extract-text", aliases=["extraire-texte"], parents=[instance_parent], help="Extraire le texte natif.")
    extract.add_argument("--doc-id", help="Limiter l'extraction a un identifiant documentaire.")
    extract.add_argument(
        "--docai",
        choices=["off", "local-basic", "local-heavy"],
        default="off",
        help="Activer la couche Document Intelligence apres extraction native.",
    )

    classify = subparsers.add_parser("classify", aliases=["classer"], parents=[instance_parent], help="Classer les documents.")
    classify.add_argument("--no-copy", action="store_true", help="Ne pas copier les fichiers dans la zone de classement.")

    subparsers.add_parser("missing-docs", aliases=["pieces-manquantes"], parents=[instance_parent], help="Produire le rapport de completude.")
    subparsers.add_parser("kpi", aliases=["indicateurs"], parents=[instance_parent], help="Calculer les indicateurs documentaires.")

    tools_parser = subparsers.add_parser("tools", aliases=["outils"], help="Verifier les outils systeme et modules Python.")
    tools_subparsers = tools_parser.add_subparsers(dest="tools_command", required=True)
    tools_subparsers.add_parser("status", aliases=["statut"], help="Afficher les outils disponibles.")

    accounting_parser = subparsers.add_parser("accounting", aliases=["compta"], parents=[instance_parent], help="Commandes ComptaScope.")
    accounting_subparsers = accounting_parser.add_subparsers(dest="accounting_command", required=True)
    accounting_reconstruct = accounting_subparsers.add_parser(
        "reconstruct",
        aliases=["reconstituer"],
        parents=[instance_parent],
        help="Reconstituer une comptabilite candidate depuis les factures.",
    )
    accounting_reconstruct.add_argument("--year", "--annee", dest="year", type=int, required=True)
    accounting_controls = accounting_subparsers.add_parser(
        "controls",
        aliases=["controles"],
        parents=[instance_parent],
        help="Synthese des controles comptables.",
    )
    accounting_controls.add_argument("--year", "--annee", dest="year", type=int, required=True)

    invoices_parser = subparsers.add_parser("invoices", aliases=["factures"], parents=[instance_parent], help="Commandes FactureOps.")
    invoices_subparsers = invoices_parser.add_subparsers(dest="invoices_command", required=True)
    invoices_extract = invoices_subparsers.add_parser(
        "extract",
        aliases=["extraire"],
        parents=[instance_parent],
        help="Extraire et analyser les factures candidates via FactureOps.",
    )
    invoices_extract.add_argument("--year", "--annee", dest="year", type=int, required=True)

    grist_parser = subparsers.add_parser("grist", parents=[instance_parent], help="Exports et synchronisation Grist.")
    grist_subparsers = grist_parser.add_subparsers(dest="grist_command", required=True)
    grist_sync = grist_subparsers.add_parser("sync", aliases=["synchroniser"], parents=[instance_parent], help="Exporter les tables Grist.")
    grist_sync.add_argument("--target", choices=["local", "self-hosted"], default="local")
    grist_sync.add_argument("--dataset", choices=["demo", "private"], default="demo")
    grist_sync.add_argument("--year", "--annee", dest="year", type=int, default=2025)

    evidence_parser = subparsers.add_parser("evidence", parents=[instance_parent], help="Rapports Evidence locaux.")
    evidence_subparsers = evidence_parser.add_subparsers(dest="evidence_command", required=True)
    evidence_build = evidence_subparsers.add_parser("build", aliases=["construire"], parents=[instance_parent], help="Construire un rapport Evidence.")
    evidence_build.add_argument("--dataset", choices=["demo", "private"], default="demo")
    evidence_build.add_argument("--year", "--annee", dest="year", type=int, default=2025)

    workers_parser = subparsers.add_parser("workers", parents=[instance_parent], help="Executer des workers CoproScope.")
    workers_subparsers = workers_parser.add_subparsers(dest="workers_command", required=True)
    workers_run = workers_subparsers.add_parser("run", aliases=["executer"], parents=[instance_parent], help="Executer un groupe de workers.")
    workers_run.add_argument("--scope", choices=["inventory", "documents", "syndic", "ag", "invoices", "accounting", "dashboards", "all"], default="all")
    workers_run.add_argument("--year", "--annee", dest="year", type=int, default=2025)

    privacy_parser = subparsers.add_parser("privacy", aliases=["confidentialite"], parents=[instance_parent], help="Screening, politique d'acces et BiffageOps.")
    privacy_subparsers = privacy_parser.add_subparsers(dest="privacy_command", required=True)
    privacy_screen = privacy_subparsers.add_parser(
        "screen-existing",
        aliases=["screening-existant", "scanner-existant"],
        parents=[instance_parent],
        help="Scanner les documents deja deposes et enrichir le registre confidentialite.",
    )
    privacy_screen.add_argument("--skip-generated", action="store_true", help="Ne pas scanner outputs/staging.")
    privacy_screen.add_argument("--max-text-chars", type=int, default=50000, help="Nombre maximum de caracteres lus localement par document.")
    privacy_screen.add_argument("--prune-unseen", action="store_true", help="Remplacer le registre par le perimetre scanne au lieu de conserver les anciennes lignes.")
    privacy_screen.add_argument(
        "--scan-workspace-prefixes",
        action="store_true",
        help="Inclure explicitement les dossiers metier 100_, 200_, 220_, etc. en plus du brut/restreint.",
    )
    privacy_queue = privacy_subparsers.add_parser(
        "redaction-queue",
        aliases=["file-biffage"],
        parents=[instance_parent],
        help="Construire la file BiffageOps sans biffer les sources.",
    )
    privacy_redact = privacy_subparsers.add_parser("redact", aliases=["biffer"], parents=[instance_parent], help="Biffer un document par doc_id.")
    privacy_redact.add_argument("--doc-id", required=True)
    privacy_redact.add_argument("--mode", choices=["redaction_irreversible", "pseudonymisation_tracee"], default="redaction_irreversible")
    privacy_redact.add_argument("--target-college", default="C2_Coproprietaires")
    privacy_required = privacy_subparsers.add_parser(
        "redact-required",
        aliases=["biffer-requis"],
        parents=[instance_parent],
        help="Biffer les documents de la file qui sont prets pour un biffage local.",
    )
    privacy_required.add_argument("--mode", choices=["redaction_irreversible", "pseudonymisation_tracee"], default="redaction_irreversible")
    privacy_required.add_argument("--target-college", default="C2_Coproprietaires")
    privacy_required.add_argument("--limit", type=int, default=None)

    ui_parser = subparsers.add_parser("ui", aliases=["interface"], parents=[instance_parent], help="Interface web locale CoproScope.")
    ui_subparsers = ui_parser.add_subparsers(dest="ui_command", required=True)
    ui_serve = ui_subparsers.add_parser("serve", aliases=["servir"], parents=[instance_parent], help="Servir le cockpit web local.")
    ui_serve.add_argument("--year", "--annee", dest="year", type=int, default=2025)
    ui_serve.add_argument("--host", default="127.0.0.1")
    ui_serve.add_argument("--port", type=int, default=8765)
    ui_serve.add_argument(
        "--unsafe-lan",
        action="store_true",
        help="Autoriser explicitement une ecoute hors loopback; protege par jeton local.",
    )
    ui_open_test = ui_subparsers.add_parser(
        "open-test",
        aliases=["test-visible"],
        parents=[instance_parent],
        help="Lancer un serveur de test visible, au premier plan, sans process cache.",
    )
    ui_open_test.add_argument("--year", "--annee", dest="year", type=int, default=2025)
    ui_open_test.add_argument("--host", default="127.0.0.1")
    ui_open_test.add_argument("--port", type=int, default=8765)
    ui_open_test.add_argument("--token", default="qa-2000-local", help="Jeton local affiche dans l'URL de test.")
    ui_open_test.add_argument(
        "--unsafe-lan",
        action="store_true",
        help="Autoriser explicitement une ecoute hors loopback; a eviter pour les tests.",
    )

    demo_parser = subparsers.add_parser("demo", aliases=["demonstration"], help="Fabrique de copro demo fictive.")
    demo_subparsers = demo_parser.add_subparsers(dest="demo_command", required=True)
    demo_build = demo_subparsers.add_parser("build", aliases=["construire"], help="Generer une instance demo fictive partageable.")
    demo_build.add_argument("--source-instance", help="Chemin vers instance.yml source ou dossier source.")
    demo_build.add_argument("--source-instance-root", help="Dossier source contenant instance.yml.")
    demo_build.add_argument("--output-instance", required=True, help="Dossier ou fichier instance.yml de sortie.")
    demo_build.add_argument("--mode", choices=["fictive"], default="fictive")
    demo_build.add_argument("--year", "--annee", dest="year", type=int, default=2025)
    demo_build.add_argument("--skip-source-audit", action="store_true", help="Ne pas lancer PrivacyOps/BiffageOps sur la source.")
    demo_build.add_argument("--max-text-chars", type=int, default=12000)

    decisions_parser = subparsers.add_parser("decisions", parents=[instance_parent], help="Registre decisions-actions-preuves.")
    decisions_subparsers = decisions_parser.add_subparsers(dest="decisions_command", required=True)
    decisions_build = decisions_subparsers.add_parser(
        "build",
        aliases=["construire"],
        parents=[instance_parent],
        help="Construire le registre decisions-actions-preuves depuis AGOps et les preuves locales.",
    )
    decisions_build.add_argument("--no-ag-analyze", action="store_true", help="Ne pas relancer AGOps si le registre AG est vide.")
    decisions_build.add_argument("--doc-id", help="Limiter la construction a un document AG.")

    incidents_parser = subparsers.add_parser("incidents", aliases=["signalements"], parents=[instance_parent], help="Registre IncidentOps.")
    incidents_subparsers = incidents_parser.add_subparsers(dest="incidents_command", required=True)
    incidents_subparsers.add_parser(
        "build",
        aliases=["construire"],
        parents=[instance_parent],
        help="Construire le registre incidents, l'export des ouverts et le rapport IncidentOps.",
    )

    strategy_parser = subparsers.add_parser("strategy", aliases=["strategie"], parents=[instance_parent], help="Strategie et feuille de route produit.")
    strategy_subparsers = strategy_parser.add_subparsers(dest="strategy_command", required=True)
    strategy_subparsers.add_parser("export", aliases=["exporter"], parents=[instance_parent], help="Exporter une strategie locale.")

    vault_parent = _vault_parent()
    vault_parser = subparsers.add_parser("vault", aliases=["coffre"], help="Vault local chiffre, signe et synchronisable.")
    vault_subparsers = vault_parser.add_subparsers(dest="vault_command", required=True)
    vault_subparsers.add_parser("init", aliases=["initialiser"], parents=[vault_parent], help="Initialiser un vault local et son dossier sync.")
    vault_import = vault_subparsers.add_parser("import", aliases=["importer"], parents=[vault_parent], help="Importer un fichier dans le vault.")
    vault_import.add_argument("--path", required=True, help="Fichier local a importer.")
    vault_audit360 = vault_subparsers.add_parser(
        "import-audit360-rows",
        aliases=["importer-audit360-lignes"],
        parents=[vault_parent],
        help="Importer des lignes Audit360 fictives/publiques dans la reconstruction locale.",
    )
    vault_audit360.add_argument("--path", required=True, help="Fichier CSV, JSON ou JSONL Audit360 a importer.")
    vault_audit360.add_argument("--db-path", help="Cache de reconstruction local; doit rester sous --local-root.")
    vault_audit360.add_argument("--source-kind", default="audit360", help="Type source a inscrire dans la reconstruction.")
    vault_audit360.add_argument("--import-run-id", default="manual-audit360-import", help="Identifiant local de reprise.")
    vault_audit360.add_argument("--imported-at", help="Horodatage ISO de l'import; par defaut, maintenant en UTC.")
    vault_subparsers.add_parser("status", aliases=["statut"], parents=[vault_parent], help="Afficher le statut du vault.")
    vault_subparsers.add_parser("verify", aliases=["verifier"], parents=[vault_parent], help="Verifier les evenements, signatures et blobs.")
    vault_subparsers.add_parser("snapshot", parents=[vault_parent], help="Creer un snapshot chiffre de reconstruction rapide.")

    drive_parser = subparsers.add_parser("drive", aliases=["lecteur"], help="Bootstrap Google Drive pour transport chiffre.")
    drive_subparsers = drive_parser.add_subparsers(dest="drive_command", required=True)
    drive_status = drive_subparsers.add_parser("status", aliases=["statut"], help="Verifier les fichiers OAuth locaux sans afficher de secrets.")
    drive_status.add_argument("--client-secrets", help="Chemin du JSON OAuth Desktop app, hors Git.")
    drive_status.add_argument("--token-path", help="Chemin du token utilisateur local, hors Git.")
    drive_auth = drive_subparsers.add_parser("auth", aliases=["authentifier"], help="Ouvrir le consentement Google Drive dans le navigateur.")
    drive_auth.add_argument("--client-secrets", help="Chemin du JSON OAuth Desktop app, hors Git.")
    drive_auth.add_argument("--token-path", help="Chemin du token utilisateur local, hors Git.")
    drive_auth.add_argument("--no-browser", action="store_true", help="Afficher l'URL au lieu d'ouvrir automatiquement le navigateur.")
    drive_smoke = drive_subparsers.add_parser(
        "smoke",
        aliases=["fumee"],
        help="Preparer ou executer un smoke Drive chiffre.",
    )
    drive_smoke.add_argument("--sync-root", required=True, help="Surface vault chiffree candidate pour Drive.")
    drive_smoke.add_argument("--encrypted-path", help="Fichier chiffre candidat; par defaut, premier blob/snapshot trouve.")
    drive_smoke.add_argument("--token-path", help="Chemin du token utilisateur local, hors Git.")
    drive_smoke.add_argument("--upload", action="store_true", help="Executer l'upload Drive apres le gate anti-fuite.")
    drive_smoke.add_argument("--folder-name", default=gdriveops.DEFAULT_SMOKE_FOLDER_NAME, help="Dossier Drive smoke a creer/reutiliser.")
    drive_smoke.add_argument("--cleartext-canary", help="Marqueur clair a refuser dans le candidat chiffre; jamais affiche.")
    drive_smoke.add_argument(
        "--generation",
        type=int,
        default=gdriveops.DEFAULT_SYNC_GENERATION,
        help="Generation du paquet chiffre pour detection de conflit collaboratif.",
    )
    drive_smoke.add_argument(
        "--parent-sha256",
        help="Hash parent attendu; vide pour la premiere generation, jamais un chemin ou un secret.",
    )
    drive_pull = drive_subparsers.add_parser(
        "pull-package",
        aliases=["recuperer-paquet", "readback"],
        help="Telecharger le dernier paquet chiffre visible dans le dossier Drive choisi.",
    )
    drive_pull.add_argument("--folder-id", required=True, help="ID du dossier Google Drive partage; jamais affiche dans la sortie.")
    drive_pull.add_argument("--sync-root", required=True, help="Surface locale qui recevra uniquement les paquets chiffres.")
    drive_pull.add_argument("--token-path", help="Chemin du token utilisateur local, hors Git.")
    drive_sync = drive_subparsers.add_parser(
        "sync-now",
        aliases=["synchroniser-maintenant", "sync"],
        parents=[instance_parent],
        help="Lire Drive puis publier ce poste en une action manuelle.",
    )
    drive_sync.add_argument("--folder-id", required=True, help="ID du dossier Google Drive partage; jamais affiche dans la sortie.")
    drive_sync.add_argument("--sync-root", required=True, help="Surface locale qui contient uniquement les paquets chiffres.")
    drive_sync.add_argument("--local-state-root", required=True, help="Etat local de ce poste; doit rester hors Drive et hors Git.")
    drive_sync.add_argument("--token-path", help="Chemin du token utilisateur local, hors Git.")
    drive_watch_once = drive_subparsers.add_parser(
        "watch-once",
        aliases=["surveiller-une-fois"],
        parents=[instance_parent],
        help="Faire un tour de surveillance Drive sans boucle permanente.",
    )
    drive_watch_once.add_argument("--folder-id", required=True, help="ID du dossier Google Drive partage; jamais affiche dans la sortie.")
    drive_watch_once.add_argument("--sync-root", required=True, help="Surface locale qui contient uniquement les paquets chiffres.")
    drive_watch_once.add_argument("--local-state-root", required=True, help="Etat local de ce poste; doit rester hors Drive et hors Git.")
    drive_watch_once.add_argument("--local-change-marker", help="Marqueur local opaque; jamais affiche, seulement compare par empreinte.")
    drive_watch_once.add_argument("--token-path", help="Chemin du token utilisateur local, hors Git.")
    drive_watch_loop_parser = drive_subparsers.add_parser(
        "watch-loop",
        aliases=["surveiller"],
        parents=[instance_parent],
        help="Surveiller Drive en cycles bornes; Ctrl+C pour arreter en usage interactif.",
    )
    drive_watch_loop_parser.add_argument("--folder-id", required=True, help="ID du dossier Google Drive partage; jamais affiche dans la sortie.")
    drive_watch_loop_parser.add_argument("--sync-root", required=True, help="Surface locale qui contient uniquement les paquets chiffres.")
    drive_watch_loop_parser.add_argument("--local-state-root", required=True, help="Etat local de ce poste; doit rester hors Drive et hors Git.")
    drive_watch_loop_parser.add_argument("--local-change-marker", help="Marqueur local opaque; jamais affiche, seulement compare par empreinte.")
    drive_watch_loop_parser.add_argument("--interval-seconds", type=float, default=15.0, help="Delai entre deux controles Drive.")
    drive_watch_loop_parser.add_argument("--max-cycles", type=int, help="Nombre de tours a executer; omis = boucle jusqu'a arret manuel.")
    drive_watch_loop_parser.add_argument("--token-path", help="Chemin du token utilisateur local, hors Git.")
    drive_folder_rights = drive_subparsers.add_parser(
        "folder-rights",
        aliases=["droits-dossier", "share-status"],
        help="Verifier les droits Google du dossier choisi sans afficher les comptes.",
    )
    drive_folder_rights.add_argument("--folder-id", required=True, help="ID du dossier Google Drive partage; jamais affiche dans la sortie.")
    drive_folder_rights.add_argument("--token-path", help="Chemin du token utilisateur local, hors Git.")

    instance_parser = subparsers.add_parser("instance", aliases=["instances"], parents=[instance_parent], help="Gestion locale d'une instance CoproScope.")
    instance_subparsers = instance_parser.add_subparsers(dest="instance_command", required=True)
    instance_git_init = instance_subparsers.add_parser(
        "git-init",
        aliases=["initialiser-git"],
        parents=[instance_parent],
        help="Initialiser la racine d'instance comme depot Git local sans remote GitHub.",
    )
    instance_git_init.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Ne pas ajouter les garde-fous .gitignore d'instance.",
    )
    instance_git_init.add_argument(
        "--force-nested",
        action="store_true",
        help="Autoriser l'initialisation si l'instance est deja sous un autre worktree Git.",
    )
    instance_subparsers.add_parser(
        "git-status",
        aliases=["statut-git"],
        parents=[instance_parent],
        help="Verifier qu'une instance est un depot Git local sans remote GitHub.",
    )
    instance_layout_parser = instance_subparsers.add_parser(
        "layout",
        aliases=["arborescence"],
        parents=[instance_parent],
        help="Planifier une arborescence d'instance novice sans modifier les fichiers.",
    )
    instance_layout_subparsers = instance_layout_parser.add_subparsers(dest="instance_layout_command", required=True)
    instance_layout_subparsers.add_parser(
        "plan",
        aliases=["planifier"],
        parents=[instance_parent],
        help="Afficher le dry-run JSON de l'arborescence novice recommandee.",
    )

    ag_parser = subparsers.add_parser("ag", aliases=["assemblee-generale"], parents=[instance_parent], help="Commandes du module AG.")
    ag_subparsers = ag_parser.add_subparsers(dest="ag_command", required=True)
    ag_subparsers.add_parser(
        "analyze",
        aliases=["analyser"],
        parents=[instance_parent],
        help="Analyser les documents AG et creer un registre de preparation.",
    )

    dd_parser = subparsers.add_parser("due-diligence", aliases=["diligence"], parents=[instance_parent], help="Commandes de diligence.")
    dd_subparsers = dd_parser.add_subparsers(dest="dd_command", required=True)
    dd_subparsers.add_parser(
        "summarize",
        aliases=["synthese"],
        parents=[instance_parent],
        help="Resumer les recherches publiques de diligence deja en cache.",
    )

    audit360_parser = subparsers.add_parser("audit360", aliases=["audit"], parents=[instance_parent], help="Preparation Audit360 et frontiere anonymisee.")
    audit360_subparsers = audit360_parser.add_subparsers(dest="audit360_command", required=True)
    audit360_prepare = audit360_subparsers.add_parser(
        "prepare-anonymized",
        aliases=["preparer-anonymise"],
        parents=[instance_parent],
        help="Preparer un manifeste d'audit IA/cloud sans references aux pieces brutes.",
    )
    audit360_prepare.add_argument("--doc-id", help="Limiter la preparation a un document.")
    audit360_prepare.add_argument("--all", action="store_true", help="Inclure tous les documents du registre.")

    pipeline = subparsers.add_parser("pipeline", aliases=["chaine"], parents=[instance_parent], help="Executer la chaine CoproScope v1.")
    pipeline_subparsers = pipeline.add_subparsers(dest="pipeline_command", required=True)
    run_parser = pipeline_subparsers.add_parser("run", aliases=["executer"], parents=[instance_parent], help="Executer la chaine sur l'instance.")
    run_parser.add_argument("--no-copy", action="store_true", help="Ne pas preparer de copies classees.")
    run_parser.add_argument(
        "--docai",
        choices=["off", "local-basic", "local-heavy"],
        default="off",
        help="Activer Document Intelligence dans le pipeline.",
    )

    docai_parser = subparsers.add_parser("docai", aliases=["ia-doc"], parents=[instance_parent], help="Commandes Document Intelligence locales.")
    docai_subparsers = docai_parser.add_subparsers(dest="docai_command", required=True)
    docai_ocr = docai_subparsers.add_parser("ocr", parents=[instance_parent], help="Executer l'OCR local sur les documents OCR_REQUIRED.")
    docai_ocr.add_argument("--doc-id", help="Limiter l'OCR a un identifiant documentaire.")
    docai_ocr.add_argument("--engine", choices=["sidecar-ocr", "rapidocr", "gutenocr"], help="Forcer un moteur OCR local.")
    docai_ocr.add_argument("--mode", choices=["local-basic", "local-heavy"], default="local-basic", help="Mode DocAI a utiliser.")

    docai_enrich = docai_subparsers.add_parser("enrich", parents=[instance_parent], help="Enrichir des documents via un backend DocAI.")
    docai_enrich.add_argument("--doc-id", help="Limiter l'enrichissement a un identifiant documentaire.")
    docai_enrich.add_argument("--backend", required=True, choices=["docling", "qwen-vl", "layoutlmv3", "layoutalm"], help="Backend d'enrichissement.")
    docai_enrich.add_argument("--mode", choices=["local-basic", "local-heavy"], default="local-basic", help="Mode DocAI a utiliser.")

    docai_status = docai_subparsers.add_parser("status", parents=[instance_parent], help="Afficher les backends DocAI disponibles.")
    docai_status.add_argument("--mode", choices=["off", "local-basic", "local-heavy"], default=None, help="Mode DocAI a evaluer.")

    mcp_parser = subparsers.add_parser("mcp", help="Serveur stdio minimal compatible MCP.")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command", required=True)
    mcp_subparsers.add_parser("serve", help="Servir les messages JSON-RPC sur stdio.")

    share_parser = subparsers.add_parser("share-audit", aliases=["audit-partage"], help="Auditer ce qui peut etre publie sur GitHub.")
    share_parser.add_argument("--repo-root", default="..", help="Racine du depot a auditer.")
    share_parser.add_argument(
        "--config",
        default="src/coproscope/configs/github_sharing.default.yml",
        help="Chemin vers le fichier de politique de partage.",
    )
    share_export = subparsers.add_parser("share-export", aliases=["export-partage"], help="Copier le sous-ensemble publiable dans un dossier propre.")
    share_export.add_argument("--repo-root", default="..", help="Racine du depot a auditer puis exporter.")
    share_export.add_argument(
        "--config",
        default="src/coproscope/configs/github_sharing.default.yml",
        help="Chemin vers le fichier de politique de partage.",
    )
    share_export.add_argument("--output-dir", required=True, help="Dossier destination pour l'export public.")
    share_export.add_argument("--clean", action="store_true", help="Supprimer le dossier d'export avant la copie.")

    return parser


def _normaliser_commandes(args: argparse.Namespace) -> None:
    args.command = COMMAND_ALIASES.get(args.command, args.command)
    for field_name, aliases in SUBCOMMAND_ALIASES.items():
        current = getattr(args, field_name, None)
        if current is not None:
            setattr(args, field_name, aliases.get(current, current))
