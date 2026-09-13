# Parcours jour de conseil syndical

Objectif : rendre la page Actions utile juste apres le Cockpit et l'Atelier pieces, pour une reunion courte ou un membre novice doit savoir quoi faire sans relire tout le dossier.

## Sequence courte

1. Demander
   - Utiliser les cartes `a demander` pour transformer une absence de piece ou d'explication en demande au syndic.
   - La carte rappelle pourquoi la demande existe, la preuve ou source attendue, la prochaine action et la prudence diffusion.

2. Verifier
   - Controler les preuves deja presentes avant de les citer comme acquises.
   - La preuve locale doit confirmer le point suivi : date, montant, decision, incident ou document attendu.

3. Rattacher
   - Revenir a l'Atelier pieces quand une preuve existe mais n'est pas encore reliee au bon point.
   - Le rattachement evite de garder une piece utile dans le dossier sans fermer la boucle d'action.

4. Arbitrer
   - Mettre en discussion CS les blocages, conflits, incertitudes de source et restrictions de diffusion.
   - Tant que l'arbitrage n'est pas inscrit, la carte doit rester prudente : pas de diffusion large, pas de cloture.

5. Cloturer
   - Cloturer seulement quand la preuve finale est rattachee, lisible et diffusable au bon public.
   - Les incidents et decisions restent les exemples prioritaires : preuve de cloture, PV, facture, photo, mail syndic ou reference de decision.

## Regle de carte

Chaque carte de travail doit afficher quatre informations dans cet ordre :

- Pourquoi : le contexte metier qui justifie l'action.
- Preuve / source : la piece attendue, le chemin local, la source du registre ou le canal.
- Prochaine action : le geste concret a faire maintenant.
- Prudence diffusion : ce qui peut etre partage, ce qui doit rester interne, ou ce qui attend un arbitrage.

## Limite volontaire

Cette livraison ne modifie pas les routes, le viewmodel ni les styles. Elle reorganise `actions.html` avec les donnees deja disponibles et ajoute des tests statiques pour verrouiller le parcours novice.
