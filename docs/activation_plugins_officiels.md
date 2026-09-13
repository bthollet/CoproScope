# Activation plugins officiels V1

Ce document complete le catalogue des plugins officiels avec un modele
d'activation volontairement leger. Le code de reference est
`server/src/coproscope/plugins/activation.py`.

## Perimetre V1

- Plugins officiels uniquement, issus du catalogue local.
- Pas de plugin communautaire.
- Pas d'auto-update.
- Code plugin local et hors vault.
- Activation preparee pour signature future, sans validation cryptographique
  runtime en V1.
- Revocation bloquante: un manifeste revoque ne peut pas etre active.

## Modele

`PluginActivationRequest` decrit une demande locale:

- `plugin_id`: identifiant du plugin officiel.
- `activated_by`: identite locale ou politique a l'origine de la demande.
- `activated_at`: horodatage fourni par l'appelant.
- `permissions_granted`: permissions explicitement accordees.
- `config_hash`: hash non sensible de la configuration locale.
- `activated_by_policy`: politique d'activation, par defaut
  `explicit_user_activation`.
- `app_version`, `vault_format_version`: versions a verifier.
- `revocation_status`: `valid`, `revoked` ou `unknown`.

`PluginActivationEvent` est le payload historisable et pret pour signature
future:

- `event_type`: `plugin_activated`.
- `plugin_id`, `plugin_version`.
- `manifest_hash`: SHA-256 canonique du manifeste sans le champ `signature`.
- `permissions_granted`.
- `config_hash`.
- `activated_by`, `activated_by_policy`, `activated_at`.
- `activation_status`: `ready_for_signature`, `blocked` ou `revoked`.
- `revocation_status`.
- `signature_status`: `pending_future_signature`.
- `compatibility`: resultat du controle catalogue/app/vault/Python.
- `required_by_vault`, `recommended_by_vault`.
- `errors`: raisons de blocage lisibles.
- `signature_payload`: sous-ensemble canonique a signer plus tard.

## Compatibilite

Le controle de compatibilite compare:

- version du catalogue;
- version app minimale et maximale si declaree;
- version de format vault minimale et maximale si declaree;
- version Python minimale.

Une incompatibilite met `activation_status` a `blocked` et conserve les raisons
dans `errors`. Le modele ne tente pas de resoudre ou d'installer une autre
version.

## Hash manifeste

`hash_plugin_manifest()` calcule un hash `sha256:<hex>` sur le JSON canonique du
manifeste, tri des cles inclus, sans le champ `signature`. Ce choix permet de
changer le placeholder de signature future sans changer l'identite logique du
manifeste a signer.

## Statuts vault

Les sets exposes apres catalogue sont:

- requis: `official.docops`, `official.privacy_biffage`;
- recommandes: `official.docops`, `official.comptascope`,
  `official.privacy_biffage`, `official.evidence_exports`.

`official.docai_ocr` reste optionnel: il porte les traitements OCR lourds et
ne doit pas devenir une dependance implicite du vault.

## Refus V1

Une activation est bloquee si:

- le plugin n'est pas officiel;
- le manifeste autorise un plugin communautaire V1;
- le manifeste demande l'auto-update;
- le code n'est pas declare local et hors vault;
- l'activation ne requiert pas de signature future;
- la revocation est `revoked`, `unknown` ou inconnue;
- une permission accordee n'existe pas dans le manifeste;
- la compatibilite app/vault/Python echoue.

Le modele ne lance aucun plugin, ne telecharge rien, ne met rien a jour, et ne
stocke pas de secret: il prepare seulement le payload que le systeme de
signature pourra couvrir dans une version ulterieure.
