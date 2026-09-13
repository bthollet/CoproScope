# Pilotage: donnees locales et exemples synthetiques

La route `/pilotage` conserve son branchement existant. Quand elle appelle la vue sans cartes explicites, `pilotage_view.py` cherche l'instance locale courante et lit son registre `kpi` / `indicateurs` si le fichier existe.

## Priorite aux registres existants

Chaque ligne KPI exploitable est convertie en carte via `pilotageops`, avec:

- un domaine de pilotage deduit du theme, de la famille, du libelle ou de la source;
- une source affichee sous la forme `Registre KPI local - ...`;
- une preuve issue de la ligne si elle existe, sinon une reference stable `kpi.csv:<kpi_id>` pour les valeurs calculees;
- une prochaine action lisible par le conseil syndical.

Les lignes `TO_FILL` ou sans valeur calculee restent visibles mais sont marquees a verifier, avec une preuve manquante explicite.

## Fallback exemple local

Si aucun registre KPI exploitable n'est trouve, la vue affiche exactement trois cartes synthetiques marquees `Exemple local`:

- consommations: derive eau froide;
- entretien: controle contrat entretien;
- gouvernance: decision AG sans suite.

Ces cartes ne pretendent pas representer la copropriete. Elles servent seulement de demonstration locale en attendant de brancher un registre reel. Chaque carte contient une source `Exemple local CoproScope`, une reference de preuve `DEMO-LOCAL-*` et une prochaine action demandant de remplacer l'exemple par une piece ou un registre reel.

## Limite volontaire

La logique reste dans `server/src/coproscope/web/pilotage_view.py`: aucune route, aucun template global et aucun layout commun ne sont modifies.
