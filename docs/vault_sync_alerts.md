# Vault sync alerts

Ce lot ajoute une couche de decision au-dessus de l'audit de dossier synchronise. Elle ne scanne ni processus, ni ports: elle classe uniquement des donnees testables en memoire (`SyncAudit`, constats d'integrite simules, ou erreurs d'un rapport de verification).

## Niveaux

- `information`: synchronisation active propre, sans marqueur de conflit, entree interdite ni risque transport.
- `attention`: conflit fournisseur ou metadata de transport a revoir, sans preuve que le vault signe est corrompu.
- `protection`: surface synchronisee dangereuse pour une publication externe, par exemple `.git`, `.venv`, caches, exports temporaires, placeholders ou ecritures partielles.
- `incident`: integrite vault atteinte ou non verifiable, par exemple signature invalide/manquante, hash invalide, cle publique manquante ou blob manquant.

La precedence est stricte: `incident` > `protection` > `attention` > `information`.

## Actions

- `no_lock`: aucune mise en lecture seule pour une simple synchronisation active propre ou en attention.
- `suspend_publication`: publication externe suspendue au niveau `protection`; le vault reste modifiable pour permettre le nettoyage.
- `lock_readonly`: verrouillage en lecture seule au niveau `incident`, jusqu'a resolution de l'integrite.
- `notify_internal`: emission d'un evenement abstrait interne a chaque evaluation.

L'evenement abstrait est `vault.sync_alert.classified`. Il transporte le profil, le chemin de sync, le niveau, les codes d'alerte et les codes d'action. Il ne depend d'aucun canal concret de notification.

## API

- `evaluate_vault_sync_alerts(sync_root, profile_id, integrity_findings=(), integrity_report=None, sync_active=True)`: lance `audit_sync_folder` puis classe le resultat.
- `classify_vault_sync_audit(sync_audit, integrity_findings=(), integrity_report=None, sync_active=True)`: classe un audit deja construit, utile pour les tests purs.

Le retour est un `VaultSyncAlertReport` fige avec:

- `level`
- `sync_audit`
- `alerts`
- `actions`
- `internal_events`
- proprietes derivees `lock_mode`, `publication_suspended`, `notification_required`

## Scenarios couverts

- Dossier sync propre via fournisseur connu: `information`, `no_lock`, notification interne.
- Fichiers de conflit fournisseur: `attention`, pas de lock.
- `.git`, `.venv`, `.cache`, `tmp_exports`, `exports_tmp`, `.tmp`, `.partial`: `protection`, publication suspendue.
- Signature, hash ou blob manquant/invalide simule: `incident`, lecture seule.
