# Notifications internes vault

Ce lot ajoute un modele de notification interne synchronisable pour le vault. Il depend des rapports produits par `sync_alerts`, sans modifier ce lot ni brancher de canal externe.

## Intention

Une notification vault est un evenement interne futur, destine a etre journalise et synchronise avec le coffre. Elle ne represente pas un envoi email, SMS ou messagerie.

Le modele testable est `VaultNotification`:

- `notification_id`: identifiant stable derive de la source, du vault, de la severite et des destinataires;
- `vault_id`: coffre concerne;
- `severity`: `information`, `attention`, `protection` ou `incident`;
- `recipients`: destinataires par role (`role`) ou membre explicite (`member`);
- `source_event_id`: evenement interne source, typiquement issu de `vault.sync_alert.classified`;
- `source_event_type`: type de l'evenement source;
- `action_required`: indique qu'une action humaine ou vault est attendue;
- `action_code` et `action_label`: action interne attendue;
- `acknowledged_at`: date d'accuse de prise en compte, sans effacer la notification initiale.

`VaultNotification.as_internal_event()` produit un evenement `vault.notification.raised` serialisable et synchronisable.

## Raccordement a sync_alerts

La fonction `notifications_from_sync_alert_report(report, vault_id, ...)` consomme un `VaultSyncAlertReport`.

Elle produit une notification uniquement pour:

- `protection`: suspension de publication ou nettoyage de la surface synchronisee;
- `incident`: controle d'integrite et maintien du vault en lecture seule.

Les niveaux `information` et `attention` restent dans le rapport `sync_alerts` et ne generent pas de notification interne dediee.

Les destinataires par defaut sont:

- role `conseil_syndical`;
- role `administrateur_local`.

Des membres explicites peuvent etre ajoutes via `recipient_member_ids`.

## Hors perimetre

Ce lot ne fait aucun envoi externe. Les connecteurs email, SMS ou messagerie seront des plugins ulterieurs, a partir des evenements internes deja presents dans le vault.
