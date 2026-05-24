# Exports derives passation / AG / contentieux

Ces exports produisent des payloads Markdown et JSON de consultation a partir des objets abstraits deja normalises:

- `agcontentieux`: dossiers AG, questions, pieces, contentieux, preuves, notes de vigilance et packs de passation.
- `requestops`: demandes coproprietaires normalisees et expurgees.
- `timelineops`: entrees chronologiques publiques par objet logique.

Watermark obligatoire: **export dérivé, non source collaborative**.

## Principes

- L'export n'est pas une source de verite collaborative: `source_of_truth` reste toujours `false`.
- Aucun objet source complet n'est transporte: pas de champ `raw`, `payload`, `metadata`, chemin local ou chemin absolu.
- Les chemins locaux et references privees sont retires ou remplaces par `[chemin-retire]`.
- Les demandes `requestops` en visibilite restreinte sont exclues et signalees dans `omissions`.
- Les niveaux de restriction/diffusion sont conserves sous forme de libelles derives: `interne`, `restreint`, `confidentiel`, `conseil_syndical`, `coproprietaires`, `public_apres_expurgation`.
- Chaque carte exportee expose les references de preuve/source diffusable quand elles existent.
- Les prochaines actions sont consolidees dans une section dediee.

## API

Le module `coproscope.modules.passation_exports` expose:

- `build_passation_derived_export(...)`: construit le document JSON en memoire.
- `render_passation_derived_json(document)`: serialise le JSON derive.
- `render_passation_derived_markdown(document)`: produit une vue Markdown lisible.

Exemple minimal:

```python
from coproscope.modules.passation_exports import (
    build_passation_derived_export,
    render_passation_derived_markdown,
)

document = build_passation_derived_export(
    title="Passation CS - AG et contentieux ouverts",
    passation_pack=pack,
    dossiers_ag=[dossier],
    contentieux_cases=[contentieux],
    evidence_bundles=[bundle],
    legal_risk_notes=[note],
    requests=demandes,
    timeline_entries=chronologie,
)

markdown = render_passation_derived_markdown(document)
```

## Structure JSON

Le document contient:

- `schema_version`: version du format derive.
- `watermark`: mention obligatoire.
- `source_of_truth`: toujours `false`.
- `scope`: type d'export, restriction maximale, diffusion minimale.
- `source_refs` et `proof_refs`: references diffusable consolidees.
- `sections`: cartes derivees pour passation, AG, contentieux, preuves, vigilance, demandes et chronologie.
- `next_actions`: prochaines actions dedupliquees.
- `omissions`: elements retires ou incomplets, notamment visibilite restreinte, chemin prive, source/preuve manquante.

## Limites

Le module ne cree pas de ZIP et n'ecrit pas de fichiers. Il fabrique uniquement des payloads en memoire, a laisser sous controle d'une couche appelante si une diffusion ou un stockage est ajoute plus tard.

Le Markdown est une vue de consultation. Le JSON reste un format d'export derive et ne doit pas etre reutilise comme registre de reference pour modifier les objets metier.
