# Registre de suivi - livraison interface et copro demo

Date de creation : 2026-05-20

Ce registre suit la mise en oeuvre du plan de livraison centre sur l'interface cible et la copro demo fictive. Il sert a distinguer ce qui est livre, ce qui est branche partiellement, et ce qui reste volontairement affiche comme chantier.

## Objectif court terme

Livrer rapidement une application web locale CoproScope qui montre :

- les priorites du conseil syndical ;
- les controles ComptaScope deja exploitables ;
- les documents, preuves et rapports disponibles ;
- les risques de confidentialite et de diffusion ;
- les modules encore en chantier.

## Suivi des lots

| Lot | Statut | Livrable | Critere de fin | Notes |
|---|---|---|---|---|
| L0 - Publication doc | TERMINE | README, etude utilisateurs, feuille de route, concepts UX pousses sur GitHub | Commit pousse sur `origin/codex/bootstrap-coproscope-server` | Commit `7e137b3`. |
| L1 - Registre de suivi | TERMINE | Present registre | Registre versionne et tenu a jour | Point d'ancrage du plan de livraison. |
| L2 - Interface locale | TERMINE | `coprocs ui serve` | Cinq vues web locales repondent en `200` | Lecture seule au depart ; aucune route ne sert les bruts ni la copro demo. |
| L3 - View model CS | TERMINE | Cartes de priorite, statuts modules, actions | Une instance privee peut etre lue sans adapter les templates | Les modules s'affichent en operationnel ou en chantier selon les registres disponibles. |
| L4 - Copro demo fictive | TERMINE | `coprocs demo build` | Instance demo generee hors Drive, sans reprise de contenu prive | Pseudonymisation seule interdite comme publication ; la demo est une instance a part, pas une vue du cockpit prive. |
| L5 - Confidentialite publication | TERMINE | Checklist CNIL et rapport de validation | Risques individualisation/correlation/inference traites | BiffageOps sert au diagnostic et a la reduction de risque. |
| L6 - Tests livraison | TERMINE | Tests unitaires + py_compile + routes | Interface, demo build et garde-fous valides | 47 tests serveur OK au dernier controle local. |

## Regles de livraison

- Le prive peut guider le produit, mais ne doit pas entrer dans le depot public.
- La copro demo publiable doit etre fictive ou suffisamment transformee pour ne pas permettre de re-identification raisonnable.
- Une pseudonymisation tracee reste une donnee personnelle : elle ne suffit pas a autoriser une publication.
- L'interface locale peut montrer des chantiers incomplets, a condition de les nommer clairement.
- Les premiers boutons peuvent etre des intentions ou exports, pas encore des workflows complets.

## Journal

| Date | Evenement | Decision |
|---|---|---|
| 2026-05-20 | Demande de livraison centree interface | Priorite a une web app locale rapide plutot qu'a une stabilisation exhaustive des modules. |
| 2026-05-20 | Demande de copro fictive/anonymisee | Ajout d'une fabrique de demo fictive derivee, avec PrivacyOps/BiffageOps comme garde-fous et non comme preuve automatique de publication. |
| 2026-05-20 | Push documentation | Documentation UX et feuille de route poussees sur GitHub avant reprise du developpement. |
| 2026-05-20 | Interface locale v0 | Ajout de `coprocs ui serve`, vues web metier, view model CS et garde-fous de routes. |
| 2026-05-20 | Copro demo fictive | Ajout de `coprocs demo build`, generation fictive, validation publication et rapport CNIL simplifie. |
| 2026-05-20 | Verification | `py_compile`, `unittest tests.test_ui_demo`, puis `unittest discover -s tests -v` : tests serveur OK. |
| 2026-05-20 | Passe clarification UI | Retrait de la vue copro demo du cockpit, demo deplacee hors Drive, scan PrivacyOps recentre sur `raw` + restreints, questions syndic reformulees. |
| 2026-05-20 | Verification apres clarification | Routes locales `200`, `/demo` en `404`, `unittest discover -s tests -v` : tests serveur OK. |
| 2026-05-20 | Documentation multi-agents | Ajout d'un contrat `AGENTS.md` et d'une page d'orchestration pour lancer plusieurs agents en parallele via worktrees, ownership et ports separes. |
| 2026-05-20 | Lot 0 Sprint 2 | Ajout de la vue Actions, filtres, exports CSV/Markdown, compteur d'actions structure et tests UI. |
| 2026-05-20 | Lots paralleles A-H | Ajout des briefs ComptaScope, SyndicOps, DocOps, PrivacyOps, Decision-action-preuve, WorksOps, IncidentOps, CommsOps/passation. |
