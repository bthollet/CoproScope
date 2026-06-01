# Equipe reconstruction - DOC-0147 energie

BOT-START - Coordinateur-scribe reconstruction P0 - 2026-06-01 16:18 +02:00

Roadmap: `RM-2026-0017`
Ordre: `ORD-P0-990`
Chantier: `CH-20260601-161800-RM-2026-0017-doc147-energy`
Conversation: `CONV-2026-1981`
Mission: traiter `DOC-0147` dans le protocole reconstruction avec retours expert, designer, novice, CoproScope et QA, sans publier le contenu brut.

## Synthese

`DOC-0147` est une facture energie scannee. CoproScope la lit en OCR local et retrouve les champs comptables principaux. Le document reste toutefois en statut prudent: il est exploitable en interne pour la reconstruction, mais il n'est pas valide comptablement ni diffusable tel quel.

## Retours roles

- Expert metier: GO prudent pour continuer; garder l'alerte d'identification fournisseur, rapprocher le prelevement bancaire et suivre la periode de charge a cheval.
- Designer: l'UI doit dire en mots simples: ce qui est lu, ce qui manque, ce qu'il faut verifier.
- Novice: `INCERTAIN` doit etre explique par une phrase lisible, pas par du jargon OCR.
- CoproScope: la file factures affiche date, montant, compte energie, famille energie et statut incertain; la fiche document protegee reste consultable.
- QA privacy: NO-GO diffusion large; usage interne protege seulement. Les donnees de livraison, references contractuelles, contacts et references bancaires doivent etre biffees avant tout partage.

## Decisions

Avant document suivant: aucun point bloquant reste ouvert. Les champs utiles sont lus et les pages protegees ne montrent pas de contenu brut sensible.

Backlog immediat:

- expliquer le statut `INCERTAIN` par une phrase novice;
- proposer `Confirmer le fournisseur` ou `Laisser a verifier`;
- conserver la correspondance entre compte source detecte et compte CoproScope propose.

Futur:

- tableau energie par serie avec periode, consommation, puissance, montant et evolution;
- rapprochement automatique des prelevements;
- regles de biffage dediees aux factures energie.

## Preuves

- protocole prive: gate `DOC-0147` OK et document ferme;
- TestClient prive: fiche document, file factures et inbox en 200 sans email, telephone, IBAN, chemin local, nom brut ou OCR brut;
- smokes executable sur le dernier build OCR/energie: file factures et fiche document OK;
- SHA-256 executable: `2E9E5780265743B0B68A388BFA06603BC9334DF173A3665FFD7708F61470BFAF`.

BOT-END - Coordinateur-scribe reconstruction P0 - 2026-06-01 16:26 +02:00

Statut: `PRET_A_INTEGRER`
Fichiers modifies: cette trace et journal prive protocole.
Fichiers volontairement evites: documents bruts, OCR brut, chemins locaux, Drive, references bancaires ou contractuelles completes.
Limites: les donnees energie fines et le rapprochement bancaire restent en backlog.
