# UI annotations collaboratives

Date: 2026-05-20
Perimetre: modele de vue et template, sans route web, pas de route applicative.

## Intention

Le lot ajoute une couche d'affichage pour les annotations PDF et image
collaboratives. La vue transforme les objets metier de `annotationops` en cartes
lisibles par l'interface: page/zone, commentaire, rattachement
point/action/preuve, confidentialite et evenement futur signe.

## Fichiers

- `server/src/coproscope/web/annotation_view.py`: modele de vue pur.
- `server/src/coproscope/web/templates/annotations.html`: template Jinja pret a
  inclure par une route future.
- `server/tests/test_ui_annotations.py`: tests du modele, du rendu et de la
  frontiere sans route.

`app.py` et `base.html` restent hors perimetre. Aucune route `/annotations`
n'est creee dans ce lot.

## Contrat d'affichage

Chaque annotation affiche:

- une reference opaque de document, jamais un chemin local;
- une ancre page/zone normalisee;
- le commentaire collaboratif, masque si un detail prive est detecte;
- le lien point/action/preuve;
- la confidentialite et la diffusion;
- un sidecar non destructif avec `source_write_allowed=False`;
- un evenement futur signe de type `pdf_annotation_created` avec le statut
  `pending_future_signature`.

## Securite

La vue s'appuie sur `annotationops.validate_annotation`. Les chemins Windows,
`file://`, `raw`, `restricted`, `private`, `secret`, les traversals et les
backslashes sont refuses ou masques. Le template n'affiche aucun chemin prive et
ne propose pas de lien direct vers le PDF ou l'image source.

## Non destructif

Le PDF ou l'image source reste intact. L'annotation est une donnee sidecar et le
lot ne lit pas, ne modifie pas et ne sert pas de fichier source. Une route future
pourra brancher ce template, mais elle devra conserver ces invariants.
