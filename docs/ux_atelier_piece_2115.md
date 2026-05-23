# Atelier piece / PDF / annotations collaboratives

Date: 2026-05-20
Perimetre: fiche document locale, sans modification de PDF et sans service de fichiers bruts.

## Intention UX

La fiche document devient un atelier novice oriente `piece -> point -> action -> preuve`.
L'utilisateur voit d'abord:

1. la piece ouverte;
2. le point metier auquel la rattacher;
3. l'action prudente selon la diffusion;
4. la preuve a conserver sans reecrire la source.

## Principes retenus

- Aucun chemin local brut n'est affiche dans la page.
- Les apercus restent limites aux contenus resolus hors zones brutes/restreintes ou aux extraits derives autorises.
- Les annotations collaboratives sont presentees comme des evenements futurs separes du PDF.
- La signature est visible comme statut de confiance, meme quand elle est encore "a venir".
- L'historique est affiche comme journal lisible: moment, etat, confiance.

## Points d'attention restants

- Les signatures ne sont pas encore verifiees cryptographiquement dans cette page.
- Les actions sont des orientations UX, pas encore des formulaires collaboratifs.
- L'annotation reste un modele d'evenements futurs; aucun journal append-only n'est ecrit par la fiche.
