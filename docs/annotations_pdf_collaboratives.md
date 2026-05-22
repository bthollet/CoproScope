# Annotations PDF et image collaboratives

Date: 2026-05-20
Perimetre: modele metier pur, sans UI, sans route, sans modification du PDF ou de l'image source.

## Intention

Le lot definit un objet d'annotation collaborative non destructif. Une
annotation relie une page et une zone d'un PDF ou d'une image a un commentaire,
un point metier, une action et une preuve. Le modele produit des donnees
validables et un brouillon d'evenement signe futur, mais ne signe pas encore et
n'ecrit jamais dans le fichier source.

## Objet metier

Champs principaux:

- `annotation_id`: identifiant opaque.
- `document_ref`: reference logique du document, jamais un chemin local.
- `document_hash`: empreinte `sha256` deja calculee en amont.
- `anchor`: page, zone normalisee `x/y/width/height`, type `pdf` ou `image`.
- `comment`: commentaire collaboratif.
- `point_ref`, `action_ref`, `proof_ref`: rattachement point -> action -> preuve.
- `status`: `brouillon`, `ouverte`, `revue`, `resolue` ou `archivee`.
- `diffusion`: `conseil_syndical`, `copro`, `public_apres_expurgation` ou `non_diffusable`.
- `confidentiality`: `interne`, `reserve_cs`, `a_biffer`, `confidentiel` ou `bloque`.

## Invariants

- Modele pur: pas de lecture fichier reel, pas d'ecriture fichier, pas de route.
- Ancrage obligatoire: une annotation a une page a partir de 1 et une zone
  normalisee entre 0 et 1.
- Chemin prive interdit: chemin absolu Windows, `file://`, `raw`,
  `restricted`, `private`, `secret`, traversal et backslash sont bloques.
- Non destructif: le PDF ou l'image source reste source de verite et n'est
  jamais modifie. Les annotations sont des donnees sidecar.
- Confidentialite forte: `confidentiel` et `bloque` imposent `non_diffusable`.
- Pas de donnee de contact brute dans les commentaires d'evenement.

## Sidecar non destructif

Le plan sidecar annonce explicitement:

- `source_write_allowed: false`
- `source_mutation: forbidden`
- `source_document_ref`
- `source_document_hash`
- `sidecar_object_ref`

Ce plan est une description metier. L'ecriture concrete, si elle existe un jour,
devra rester hors du PDF source et hors de ce module.

## Evenement signe futur

Le module prepare un brouillon `pdf_annotation_created` compatible avec le
noyau d'evenements metier. Le statut de signature reste
`pending_future_signature`: cela indique que l'evenement est pret a etre signe
plus tard, pas que la signature est livree.

Le payload d'evenement contient seulement:

- reference logique du document et hash;
- ancre page/zone;
- liens point/action/preuve;
- statut, diffusion et confidentialite;
- politique non destructive.

Il ne contient aucun chemin local et aucune copie du PDF ou de l'image source.

## Hors perimetre

- Pas d'UI de dessin ou de visualisation.
- Pas de route web.
- Pas d'OCR ou lecture PDF.
- Pas de biffage effectif.
- Pas de signature cryptographique active.
