# Evenements de resultats plugins officiels

Ce document decrit le modele pur porte par
`server/src/coproscope/plugins/results.py`. Il complete le catalogue et
l'activation des plugins officiels sans executer de plugin ni toucher au vault.

## Evenement

`PluginResultRecorded` est le journal leger d'un resultat produit par un plugin
officiel:

- `event_type`: toujours `plugin_result_recorded`.
- `plugin_id`, `plugin_version`: issus du catalogue officiel local.
- `result_event_type`: type metier declare dans `event_types_produced` du
  manifeste.
- `input_hashes`: hashes SHA-256 d'entrees logiques, sans chemin.
- `parameters_hash`: hash SHA-256 des parametres, jamais les parametres bruts.
- `result_hash`: hash SHA-256 canonique du resultat.
- `status`: `completed`, `partial`, `failed` ou `blocked`.
- `warnings`: messages courts non sensibles.
- `produced_object_refs`: references logiques d'objets produits.
- `signature_status`: `pending_future_signature`.
- `errors`: raisons generiques de blocage.
- `signature_payload`: sous-ensemble canonique pret a etre signe plus tard.

## References produites

`PluginProducedObjectRef` identifie un objet produit sans exposer son
emplacement local:

- `object_type`: type logique.
- `object_id`: identifiant logique stable.
- `contract_name`: contrat de sortie declare par le manifeste.
- `object_hash`: hash SHA-256 de l'objet produit.

Les chemins comme `raw/...`, les chemins absolus Windows ou POSIX, les dossiers
`restricted` ou `private`, et les cles de type `*_path` sont refuses. Une
reference refusee n'est pas reprise dans le payload de signature.

## Garanties V1

Le modele conserve uniquement des hashes et des references logiques. Il ne
stocke pas:

- chemins bruts de pieces;
- chemins locaux absolus;
- parametres bruts;
- secrets, tokens, mots de passe ou cles API;
- valeurs sensibles dans les warnings.

Si une entree ressemble a un chemin prive ou a un secret, elle est ecartee et
l'evenement passe en `blocked` avec une erreur generique qui ne recopie pas la
valeur dangereuse.

## Plugins couverts

Les tests ciblent les resultats des plugins officiels suivants:

- DocOps: `official.docops`;
- ComptaScope: `official.comptascope`;
- PrivacyOps / BiffageOps: `official.privacy_biffage`;
- DocAI / OCR lourd: `official.docai_ocr`.

Chaque resultat doit utiliser un `result_event_type` declare par son manifeste
et des `produced_object_refs` correspondant a un contrat de sortie declare.

## Hors scope

La V1 ne calcule pas les hashes depuis les fichiers, ne signe pas encore le
payload, ne persiste pas l'evenement et ne lance aucun traitement plugin. Elle
stabilise seulement le contrat de resultat historisable et signable.
