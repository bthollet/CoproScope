# Livraison test 21h15 - cockpit novice

## Objectif

Rendre la page Cockpit directement testable par un conseil syndical novice, sans changer les routes.

## Parcours a tester

1. Ouvrir `/`.
2. Lire les trois cartes de tete:
   - Comptes: signale les points comptables a expliquer, ou affiche un placeholder si aucune donnee comptes n'est chargee.
   - Sync: rappelle que le cockpit ne lance pas de synchronisation externe et marque le statut comme placeholder synthetique.
   - Vault: rappelle le controle du vault chiffre/signe et renvoie vers la gouvernance.
3. Lire les cartes "A faire maintenant":
   - Pourquoi.
   - Preuve ou source.
   - Prochaine action.
   - Diffusion.
4. Ouvrir "Alertes en mots simples" puis cliquer vers la liste d'actions ou les pieces selon l'alerte.

## Critere de succes

Un testeur doit pouvoir dire, en moins de deux minutes:

- ce qui demande une action maintenant;
- quelle preuve regarder;
- qui relancer ou quelle page ouvrir;
- si le sujet peut etre diffuse, ou doit rester limite au conseil syndical.

## Risques restants

- Les statuts Sync et Vault restent des placeholders tant que le viewmodel ne remonte pas de donnees de synchronisation ou de verification vault par instance.
- Les libelles sont simples, mais la priorisation depend toujours de la qualite des registres produits en amont.
