# Livraison continue post-suite 279 tests

Date de reference: 2026-05-20.

Note 2026-05-21: ce document conserve l'etat historique post-279 tests sur
Platanes. La recette/live locale par defaut est maintenant
`C:\Users\brice\CoproScope\instances\beauvallon_test`.

Ce document fige l'etat testable apres la stabilisation de la suite complete. Il ne remplace pas une recette navigateur: la validation rapportee ici est automatisee, avec **suite complete 279 tests OK**, sans validation manuelle navigateur revendiquee.

## Etat stable

- Suite complete: 279 tests OK.
- Perimetre verifie par tests: noyau metier, routes FastAPI, templates principaux, exports controles, securite des routes sensibles, modules vault/sync et parcours UI synthetiques.
- Donnees de reference live locale: `C:\Users\brice\CoproScope\instances\beauvallon_test`; `examples/synthetic_copro` reste la reference publique/CI.
- Aucun engagement sur donnees reelles, synchronisation cloud fiable, signature collaborative finale ou conseil juridique.

## Lancement serveur visible

Commande recommandee pour ouvrir une instance locale testable avec serveur au premier plan:

```powershell
cd C:\Users\brice\CoproScope\coproscope
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root C:\Users\brice\CoproScope\instances\beauvallon_test --year 2025 --host 127.0.0.1 --port 8766 --token beauvallon-test-local
```

Le serveur reste visible dans le terminal et s'arrete avec `Ctrl+C`. L'URL tokenisee affichee par la commande doit etre ouverte manuellement. Ne pas transformer cette commande en lancement cache, scan de ports ou boucle de probing reseau pendant une demo.

## Routes testables maintenant

Routes nouvelles ou recemment integrees a surveiller en priorite:

- `/documents/{doc_id}`: detail document/viewer.
- `/demandes`: demandes coproprietaires multicanales.
- `/ag-contentieux`: dossiers AG, contentieux et passation.
- `/gouvernance`: roles, droits et commissions.
- `/pilotage`: indicateurs actionnables.
- `/exports/passation.json` et `/exports/passation.txt`: exports derives de passation.
- `/exports/{export_path:path}` et `/{root_name}/{path:path}`: garde-fous contre chemins prives ou exports inattendus.

Routes pages:

- `/`: cockpit local et cartes de priorisation.
- `/actions`: registre actionnable, filtres et exports associes.
- `/comptes`: lecture comptes/roles selon les donnees disponibles.
- `/documents`: liste documentaire.
- `/documents/{doc_id}`: detail document et viewer dedie si l'identifiant existe.
- `/pieces`: atelier pieces, preuves, prudence de diffusion.
- `/demandes`: demandes coproprietaires multicanales, protegee par token.
- `/ag-contentieux`: dossiers AG/contentieux/passation, protegee par token.
- `/gouvernance`: roles, commissions, gouvernance locale.
- `/pilotage`: indicateurs et cartes de pilotage, protegee par token.
- `/confidentialite`: rappels de diffusion et restrictions.
- `/chantiers`: chantiers/prochaines etapes.
- `/depot`: depot local, manifeste et pipelines non lourds, protegee par token.
- `/health`: statut technique minimal.

Routes exports/API:

- `/api/model`: modele dashboard, protegee par token.
- `/exports/actions.csv` et `/exports/actions.md`: exports actionnables filtres.
- `/exports/local.zip`: pack local derive.
- `/exports/passation.json` et `/exports/passation.txt`: exports de passation derives, avec garde-fous de diffusion.
- `/exports/{export_path:path}`: route de blocage pour chemins interdits ou inconnus.
- `/{root_name}/{path:path}`: blocage des racines privees non servies.

## Modules noyau ajoutes ou stabilises

Noyau:

- `core/accounts.py`: comptes, profils locaux, membres de coffre, appareils, roles et droits.
- `core/coffres.py`: normalisation de coffres et risques d'isolation de chemins.
- `core/events_v1.py`: brouillons d'evenements metier, hash stable et filtrage des payloads sensibles.

Modules metier:

- `modules/accessops.py` et `modules/commissionops.py`: roles, mandats, commissions et acces proportionnes.
- `modules/requestops.py`: demandes coproprietaires, canaux, statuts, journal d'action.
- `modules/agcontentieux.py`: dossiers AG/contentieux avec restrictions et garde-fous non juridiques.
- `modules/passation_exports.py`: exports de passation derives, non source collaborative.
- `modules/indicatorops.py` et `modules/pilotageops.py`: definitions d'indicateurs, observations, seuils, cartes de pilotage.
- `modules/suggestionops.py` et `modules/suggestionview.py`: suggestions revues, transformables en cartes sans effet automatique.
- `modules/syndicops.py` et `modules/timelineops.py`: demandes syndic et chronologie normalisee.

Vault/sync:

- `vault/sync_profiles.py`, `vault/sync_alerts.py` et `vault/resilience.py`: audit de transport, alertes, actions de protection et audit de reconstructibilite.
- `vault/notifications.py`: notifications internes derivees d'alertes vault.
- `vault/reconstruction_archive.py`: archive de reconstruction avec parties lisibles/restreintes.
- `vault/sync_alerts.py` ne garantit pas une synchronisation cloud sure; il expose des niveaux d'alerte et actions locales.

Vues web:

- `web/context_banner.py`: bandeau de contexte.
- `web/requests_view.py`, `web/agcontentieux_view.py`, `web/pilotage_view.py`, `web/governance.py`, `web/document_viewer.py`: contextes de templates specialises.

## Ce qui est testable fonctionnellement

- Parcours cockpit: comprendre quoi traiter, pourquoi, avec quelle preuve et quelle prochaine action.
- Parcours actions: filtrer, lire la diffusion, exporter CSV/Markdown.
- Parcours depot: deposer localement, lire le manifeste et lancer les pipelines non lourds.
- Parcours documents/pieces: rattacher une piece a une preuve ou action et signaler la prudence de diffusion.
- Parcours gouvernance: distinguer role copro, conseil syndical, commission, syndic et limites de revocation.
- Parcours demandes: suivre les demandes entrantes, leur canal, leur statut et l'action suivante.
- Parcours AG/contentieux/passation: exposer des dossiers derives avec restrictions, sans promettre un avis juridique.
- Parcours pilotage: afficher peu d'indicateurs avec periode, source, preuve, seuil et action.
- Securite routes: bloquer racines privees, exports inattendus, chemins sensibles et donnees brutes.

## Limites a garder visibles

- Pas de validation navigateur manuelle dans ce rapport.
- Pas de promesse sur un environnement utilisateur reel, des fichiers reels ou une instance non synthetique.
- La sync externe reste non fiable par principe; les modules exposent des alertes et actions, pas une garantie cloud.
- Le vault peut etre audite et documente, mais la signature collaborative finale reste marquee comme future/prototype si elle n'est pas presente.
- Les exports de passation sont derives et ne doivent pas devenir source de verite.
- Les modules AG/contentieux portent une note non juridique: ils organisent constats, preuves et risques operationnels.
- Les suggestions ne creent pas automatiquement d'actions ou demandes sans revue explicite.
- Les routes protegees doivent etre ouvertes avec token; ne pas assouplir cette contrainte pour faciliter une demo.

## Prochaine vague priorisee

1. Recette navigateur explicite sur `beauvallon_test`: ouvrir manuellement l'URL `ui open-test`, verifier les routes principales et consigner les ecarts sans confondre avec la suite de tests.
2. Stabilisation UX novice: vocabulaire, focus, labels, captions, prochaine action visible, differences depot/export/vault/sync.
3. Parcours `Jour de CS`: condenser cockpit, actions, demandes, pieces et pilotage en sequence courte.
4. Viewer documents et annotations: ancres stables, annotations hors original, restrictions visibles.
5. Notifications internes vault: transformer les alertes sync/resilience en bannieres ou journal local sans email/SMS.
6. Pack passation derive: renforcer omissions, restrictions, preuves et filigrane non-source.
7. Integration prudente plugins/suggestions: activation controlee, resultats tracables, aucun effet automatique sans validation.
