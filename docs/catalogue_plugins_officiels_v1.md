# Catalogue plugins officiels V1

Ce catalogue pose un modele volontairement leger, proche d'une strategie
Obsidian-like: le vault reste le contenu utilisateur, les plugins restent du
code local hors vault, et l'activation d'un plugin officiel devra etre signee.
La V1 ne couvre pas les plugins communautaires.

## Regles V1

- Plugins officiels uniquement.
- Pas d'auto-update: aucune mise a jour silencieuse d'un plugin actif.
- Code plugin local et hors vault: le vault ne transporte pas d'executable.
- Activation signee future: le manifeste contient un placeholder de signature,
  en attendant l'artefact signe de distribution.
- Permissions explicites: chaque plugin declare les acces lecture/ecriture
  attendus.
- Evenements produits explicites: chaque plugin expose les types d'evenements
  qu'il peut produire.
- Contrats input/output explicites: les fichiers et schemas attendus sont
  visibles avant activation.
- Compatibilite explicite: version du catalogue, version app minimale, format
  vault minimal et version Python minimale.

## Modele de manifeste

Le modele de reference est `PluginManifest` dans
`server/src/coproscope/plugins/catalog.py`.

Champs principaux:

- `plugin_id`: identifiant stable, prefixe `official.` en V1.
- `name`, `version`, `summary`: affichage et version produit.
- `modules`: modules Python locaux associes au plugin.
- `permissions`: liste des permissions demandees, avec scope et justification.
- `event_types_produced`: evenements que le plugin peut emettre.
- `input_contracts`: contrats lus ou attendus.
- `output_contracts`: contrats produits.
- `signature`: placeholder V1 de signature officielle.
- `compatibility`: compatibilite catalogue/app/vault/Python.
- `required_by_vault`: plugin minimal pour un vault CoproScope sain.
- `recommended_by_vault`: plugin conseille pour l'experience standard.
- `auto_update`: toujours `False` en V1.
- `local_outside_vault`: toujours `True` en V1.
- `community_allowed_v1`: toujours `False` en V1.
- `activation_requires_signature`: toujours `True` en V1.

## Plugins initiaux

| Plugin | Statut vault | Role | Modules |
| --- | --- | --- | --- |
| `official.docops` | Requis, recommande | Inventaire, extraction texte, classification et completude documentaire | `coproscope.modules.docuscope` |
| `official.comptascope` | Recommande | Controles comptables, factures, rapprochements et diligences fournisseur | `coproscope.modules.accounting`, `coproscope.modules.factureops` |
| `official.privacy_biffage` | Requis, recommande | Minimisation, biffage et exports assainis | `coproscope.modules.privacyops`, `coproscope.modules.biffageops` |
| `official.docai_ocr` | Optionnel | OCR lourd et enrichissements layout locaux | `coproscope.modules.docai` |
| `official.evidence_exports` | Recommande | Dossiers de preuve, rapports et exports prepares | `coproscope.modules.evidenceops`, `coproscope.modules.gristops` |

## Separation DocOps et DocAI/OCR lourd

DocOps reste le socle documentaire leger. Il peut inventorier, extraire le texte
disponible, classer et produire la matrice de completude.

DocAI/OCR lourd est separe pour eviter d'imposer les dependances OCR, layout ou
vision a tous les vaults. Il porte la permission `local.compute.heavy`, produit
`document.ocr_completed` et `document.layout_enriched`, et n'est ni requis ni
recommande par defaut.

## Signature

La V1 encode un placeholder:

- `status`: `placeholder`
- `authority`: `coproscope-official-root-future`
- `key_id`: `COPROSCOPE-OFFICIAL-V1-FUTURE`
- `digest_sha256`: `sha256:pending-packaged-artifact`
- `signature`: `sig:pending-official-release`
- `activation_policy`: `future_signed_activation_required`

Ce placeholder ne valide pas encore un binaire ou une archive. Il reserve le
contrat de securite: quand l'activation runtime arrivera, elle devra refuser un
plugin non signe ou signe par une autorite inconnue.

## Permissions et contrats

Les permissions restent descriptives en V1. Elles documentent le perimetre
attendu avant l'activation runtime:

- `vault.read.*`: lecture de fichiers ou registres du vault.
- `vault.write.*`: production d'artefacts dans `outputs/`, `system/` ou
  `registers/`.
- `local.compute.heavy`: usage de dependances locales lourdes.
- `network.optional.disabled_by_default`: export prepare sans synchronisation
  automatique.

Les contrats sont nommes et versionnes pour stabiliser les integrations entre
plugins. Un contrat peut etre optionnel lorsque le plugin sait fonctionner en
mode degrade.

## Hors scope V1

- Marketplace communautaire.
- Installation automatique depuis internet.
- Auto-update.
- Execution de code stocke dans le vault.
- Activation runtime complete par signature cryptographique reelle.
- Resolution fine des conflits de version entre plugins tiers.
