# Orchestration live continue

> Statut gouvernail: `SOURCE_HISTORIQUE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0005`, `RM-2026-0006`). Ne pas lancer de lot hors `RM-*` et `CH-*`.

Date de reference: 2026-05-20.

Role de ce document: maintenir une coordination durable de la prochaine vague
CoproScope. La strategie n'est plus bornee par un jalon horaire: elle organise
un flux continu de lots terminables, integres un par un, avec au moins cinq
files de travail utiles ouvertes en permanence.

Base actuelle documentee: **suite complete 279 tests OK**, sans recette
navigateur manuelle revendiquee ici. Toute nouvelle livraison doit distinguer
tests automatises, recette navigateur et limites non livrees.

## Invariants live

- Ne jamais reverter les changements d'autres agents.
- Commencer tout lot par `git status --short` et declarer l'ownership avant
  edition.
- Integrer une zone convergente a la fois.
- Garder `ui open-test` comme chemin serveur visible pour les demos locales.
- Toute route protegee reste protegee par token.
- Les exports restent derives, controles et non sources collaboratives.
- La sync/vault ne doit jamais etre presentee comme une garantie cloud.
- Toute mutation collaborative doit etre signee ou marquee prototype/local non
  signe.
- Les surfaces novices parlent de `coffre`, `preuve`, `action`, `diffusion`,
  `restriction`, pas seulement de concepts internes.
- Les lots doivent finir avec fichiers modifies, tests lances ou blocage,
  limites, et go/no-go integration.

## Cadence continue

La vague suivante fonctionne en boucle courte:

1. choisir un lot terminable sans decision humaine;
2. reserver son ownership, surtout sur `app.py`, `viewmodel.py`, `base.html` et
   `styles.css`;
3. livrer un comportement observable ou une documentation de contrat;
4. lancer les tests dedies puis, si l'interface change, une recette navigateur
   explicite;
5. integrer un seul lot a la fois;
6. reconstituer aussitot la file avec un nouveau lot utile.

Un lot est "terminable sans decision humaine" si le comportement attendu, les
garde-fous, les fichiers modifiables et les tests cibles sont deja decrits dans
les docs existantes. Les lots qui changent une promesse produit, un modele
cryptographique, un statut juridique ou une politique de diffusion restent en
attente d'arbitrage.

## Cadence refonte UX Image -> Dev -> Test

La refonte UX issue des captures Canva utilise un flux dedie decrit dans
[`refonte_ux_cycles_image_dev_test.md`](./refonte_ux_cycles_image_dev_test.md).
Ce flux maintient en parallele:

- un cycle N-1 en test produit livre;
- un cycle N en developpement front/back;
- un cycle N+1 en enquete sur image ou visuel recree.

Le registre courant est
[`registre_cycles_refonte_ux.md`](./registre_cycles_refonte_ux.md). Les prompts
de lancement par role sont dans
[`prompts_agents_refonte_ux.md`](./prompts_agents_refonte_ux.md).

Le format du point de coordination toutes les 10 minutes est fixe: `A tester
maintenant`, `En dev maintenant`, `En enquete maintenant`, `Commande prete`,
`Decision requise`, `Prochain mouvement`.

## Files de travail utiles

Maintenir au minimum cinq files ouvertes. Les files ci-dessous sont
independantes autant que possible et ordonnees par valeur produit.

| File | Priorite | Definition de fini | Collision principale | Tests/verification |
|---|---:|---|---|---|
| UX novice et accessibilite | P0 | Le prochain geste est visible, les libelles sont metier, focus/labels/captions couvrent les pages principales | `base.html`, `styles.css`, templates cibles | Tests UI statiques + recette clavier courte |
| Atelier piece-point-action-preuve | P0 | Chaque ligne relie piece, point, action, preuve, statut de diffusion et prochaine action | `pieces.html`, `viewmodel.py` si necessaire | `test_ui_atelier_piece.py` + route `/pieces` |
| Workflow ajout de document | P0 | Depot local, classification, confidentialite, rattachement et recapitulatif sont lisibles sans promettre annotation/sync livrees | `depot.html`, `document_viewer.py`, templates documents | tests depot/documents + invariants docs |
| Coffre signe anti-confiscation | P1 | Statut de coffre, verification, historique, signatures/prototype et reconstructibilite sont visibles sans sur-promesse | `vault/**`, bandeau contexte, gouvernance | tests vault resilience/reconstruction + UI si expose |
| Sync transport | P1 | Transport classe en information/attention/protection/incident, actions locales explicites, pas de garantie cloud | `vault/sync_*`, notifications | tests sync profiles/alerts/notifications |
| Comptes et commissions | P1 | Un novice comprend qui il est, ses droits, la commission, le referent, la validation et la revocation | gouvernance, accessops, commissionops | tests comptes/commissions/gouvernance |
| Indicateurs actionnables | P2 | 6 a 10 cartes max avec periode, preuve, seuil, confiance et action | indicatorops, pilotageops, pilotage UI | tests indicateurs/pilotage + route `/pilotage` |
| Suggestions sous revue | P2 | Suggestions sourcees, prouvees, acceptables uniquement apres revue humaine, sans effet automatique | suggestionops/view + cockpit si owner libre | tests suggestionops/suggestionview |

## Surface actuellement ouverte

Routes nouvelles ou recemment integrees a garder sous observation:

- `/documents/{doc_id}`
- `/demandes`
- `/ag-contentieux`
- `/gouvernance`
- `/pilotage`
- `/exports/passation.json`
- `/exports/passation.txt`
- routes de blocage `/exports/{export_path:path}` et `/{root_name}/{path:path}`

Pages stables a coordonner:

- `/`
- `/actions`
- `/comptes`
- `/documents`
- `/documents/{doc_id}`
- `/pieces`
- `/demandes`
- `/ag-contentieux`
- `/gouvernance`
- `/pilotage`
- `/confidentialite`
- `/chantiers`
- `/depot`
- `/health`

Exports/API a surveiller:

- `/api/model`
- `/exports/actions.csv`
- `/exports/actions.md`
- `/exports/local.zip`
- `/exports/passation.json`
- `/exports/passation.txt`
- routes de blocage `/exports/{export_path:path}` et `/{root_name}/{path:path}`

## Zones de collision

| Zone | Risque | Regle live |
|---|---|---|
| `server/src/coproscope/web/app.py` | Routes, token, exports, blocage racines privees | Un seul owner route/export a la fois. |
| `server/src/coproscope/web/viewmodel.py` | Convergence cockpit, actions, pieces, demandes, indicateurs | Owner unique explicite avant changement. |
| `server/src/coproscope/web/templates/base.html` | Navigation, token, contexte, vocabulaire novice | Changements courts, verifies sur toutes les pages principales. |
| `server/src/coproscope/web/static/styles.css` | Accessibilite et rendu global | Pas de refonte globale pendant integration fonctionnelle. |
| `server/src/coproscope/vault/**` | Promesse sync/coffre, restrictions, reconstruction | Documenter toute garantie, tout statut prototype et tout fallback. |
| `server/src/coproscope/modules/**` | Schemas metier partages | Tests unitaires dedies avant branche UI dependante. |

## Commande demo visible

```powershell
cd C:\Users\brice\CoproScope\coproscope
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root C:\Users\brice\CoproScope\instances\beauvallon_test --year 2025 --host 127.0.0.1 --port 8766 --token beauvallon-test-local
```

Le terminal qui lance cette commande est la preuve serveur visible. Le navigateur
est ouvert manuellement sur l'URL tokenisee. Tout compte rendu doit separer
clairement "tests automatises OK" et "recette navigateur effectuee".

## Roadmap operationnelle

| Ordre | Lot terminable | Objectif | Ownership conseille | Validation attendue |
|---:|---|---|---|---|
| 1 | UX novice P0 | Nettoyer vocabulaire, captions, focus visible, prochain geste, limites depot/export/coffre/sync | templates cibles + CSS global si owner unique | Tests UI statiques + recette novice 10 min |
| 2 | Atelier actionnable | Rendre les lignes ouvrables, filtrables, avec badges diffusion et action primaire | `pieces.html`, tests atelier; `viewmodel.py` seulement owner unique | `test_ui_atelier_piece.py`, route `/pieces` |
| 3 | Ajout document guide | Transformer depot en parcours local -> classification -> confidentialite -> rattachement -> recapitulatif | `depot.html`, docs/tests depot, viewer seulement si necessaire | tests depot/document + invariants workflow |
| 4 | Coffre anti-confiscation visible | Exposer verification, reconstructibilite, restrictions, recuperation par quorum, sans promettre lecture complete | vault resilience/reconstruction + contexte UI si owner libre | tests vault + libelles "coffre" |
| 5 | Sync transport lisible | Afficher information/attention/protection/incident et actions no_lock/suspend/readonly/notify | `vault/sync_*`, notifications, bandeau si owner libre | tests sync alerts/notifications |
| 6 | Comptes/commissions novice | Clarifier compte local, membre coffre, appareil, role, commission, validation, revocation | gouvernance + accessops/commissionops | tests comptes/commissions/gouvernance |
| 7 | Indicateurs utiles | Garder peu de cartes, chacune avec periode, preuve, seuil, confiance et action | indicatorops/pilotageops/pilotage UI | tests pilotage + route `/pilotage` |
| 8 | Suggestions controlees | Afficher des suggestions prouvees et acceptees, jamais transformees automatiquement | suggestionops/suggestionview + cockpit si owner libre | tests suggestionops/suggestionview |

## Lots a ne pas lancer sans arbitrage

- Changement de modele de signature cryptographique ou promesse de signature
  finale.
- Synchronisation cloud presentee comme fiable ou automatique.
- Conseil juridique contentieux/AG.
- Export public contenant bruts, chemins locaux, caches, mappings de biffage ou
  donnees reelles.
- Refonte simultanee de `viewmodel.py`, `app.py`, `base.html` et `styles.css`.
- Creation d'un compte cloud ou d'un serveur central obligatoire.

## Criteres go/no-go vague continue

Go si:

- suite automatisee reste verte apres integration;
- ownership et fichiers modifies sont listes par lot;
- route nouvelle ou modifiee a un test dedie;
- limite utilisateur visible quand une garantie manque;
- exports ne contiennent pas de bruts prives, chemins locaux sensibles, `.env`,
  `.git`, `.venv`, caches ou mappings de biffage;
- au moins cinq files utiles restent pretes apres integration.

No-go si:

- une route principale devient blanche, 500 ou non tokenisee par erreur;
- une page promet sync cloud, signature collaborative finale ou conseil
  juridique;
- un export derive devient source de verite implicite;
- `viewmodel.py`, `app.py`, `base.html` ou `styles.css` sont modifies par
  plusieurs lots sans arbitrage;
- une correction revert un changement d'autrui.

## Message de lancement pour agents

```text
Travailler dans C:\Users\brice\CoproScope\coproscope. Commencer par git status --short. Ne reverter aucune modification d'autrui. Declarer ownership avant edition. Base stable documentee: suite complete 279 tests OK, aucune validation navigateur a inventer. Choisir un lot terminable depuis docs/agent_backlog_continu.md, respecter son ownership, garder les limites coffre/sync/export visibles, et terminer avec fichiers modifies, tests, limites et go/no-go integration.
```
