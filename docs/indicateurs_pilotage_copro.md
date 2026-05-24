# Indicateurs centraux de pilotage copro

Date de reference: 2026-05-20

Ce document cadre les indicateurs a mettre au coeur de CoproScope. Un bon indicateur n'est pas un chiffre decoratif: il explique une situation, pointe une preuve, donne une periode, signale une incertitude et propose une prochaine action comprehensible par un utilisateur novice.

## Principes

- Peu d'indicateurs en cockpit, des details dans les fiches.
- Toujours afficher periode, source, niveau de confiance et preuve.
- Ne jamais melanger deux coffres de copro.
- Ne jamais exposer une donnee restreinte via une agregation trop precise.
- Tout changement de formule, seuil ou cible devient un evenement signe.
- Le vocabulaire doit rester stable: alerte, attention, conforme, preuve, action, echeance.

## Themes V1

| Theme | Indicateurs puissants | Sources | Prochaine action type |
|---|---|---|---|
| Consommations | eau, electricite, chauffage, cout unitaire, derive mensuelle, facture manquante | factures, releves, contrats, ComptaScope | demander releve, verifier contrat, ouvrir point |
| Entretien | delai d'intervention, frequence de passage, cout par equipement, non-conformite | contrats, factures, action log, preuves photo | relancer syndic ou prestataire |
| Investissements | age equipement, reste a financer, fonds travaux, CAPEX/OPEX, subventions | PPT, devis, budget, AG, factures | preparer arbitrage AG |
| Espaces verts | cout par passage, saisonnalite, eau, incident, preuve terrain | factures, contrat, demandes, photos | controler prestation ou ajuster contrat |
| Travaux | vote/engage/facture/paye, reserves, garanties, retard, reception | PV AG, devis, factures, preuves | demander preuve de cloture |
| Gouvernance | decisions sans preuve, demandes syndic en retard, productions de commission | AGOps, SyndicOps, AccessOps | relancer ou valider diffusion |
| Demandes | volume par canal, delai de tri, recurrence, prochaine echeance absente | boite de demandes, action log | qualifier, fusionner, escalader |
| Risques/contentieux | echeance, montant expose, piece manquante, restriction | dossier contentieux, documents, logs | revue humaine restreinte |
| Contrats | echeance, reconduction, mise en concurrence, ecart facture/contrat | contrats, factures, AG | preparer consultation |
| Comptes | ecart budget/reel, P1/P2, facture sans contrat, anomalie fournisseur | ComptaScope | question syndic |

## Objets noyau

- `IndicatorDefinition`: identifiant, theme, nom, formule, unite, periodicite, niveau d'acces.
- `MetricObservation`: valeur, periode, perimetre, source, preuve, qualite de donnees.
- `TargetThreshold`: cible, seuil attention, seuil alerte, justification.
- `DashboardCard`: lecture novice, tendance, cause probable, prochaine action.
- `ManagementQuestion`: question formalisable vers syndic, AG, commission ou prestataire.

## Strategie d'integration

1. Lire les registres actuels et produire des observations simples.
2. Afficher 6 a 10 cartes maximum dans le cockpit.
3. Ouvrir une fiche par theme avec preuve, tendance, seuil et action.
4. Ecrire les changements de formule/seuil en evenements signes.
5. Deplacer les calculs lourds ou connecteurs en plugins officiels signes.

## Garde-fous UX

- Un novice doit comprendre la carte sans connaitre la formule.
- Les infobulles expliquent les termes: fonds travaux, CAPEX/OPEX, reserve, tantiemes, mise en concurrence.
- Les statuts restent constants: `OK`, `attention`, `alerte`, `a verifier`.
- Une carte sans action proposee n'entre pas dans le cockpit principal.

## Veille open source liee

- SQLite FTS5 pour chercher dans les observations et preuves locales.
- DuckDB pour agregats et controles analytiques volumineux.
- Grist comme cible d'export ou interface tabulaire experimentee, pas comme source de verite.
- PDF.js, Tesseract et OCRmyPDF pour relier indicateurs et pieces lisibles localement.
- Casbin ou un modele RBAC/ABAC equivalent pour verifier que les tableaux n'exposent pas trop.
