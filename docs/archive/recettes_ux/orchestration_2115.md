# Orchestration 21h15 - vague produit fini

> Statut gouvernail: `JOURNAL_TRACE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`.
> Ce document de vague ne lance plus de nouveau travail directement.

Date de reference: 2026-05-20, jalon 21h15 Europe/Budapest.

Role de ce document: fournir au superviseur principal une coordination exploitable pour la vague active. L'agent orchestrateur ne dispose pas ici d'un outil dedie pour lancer lui-meme d'autres agents; il fournit donc les specs de lancement, les dependances et les criteres de passage.

Sources prises en compte:

- `docs/roadmap_produit_fini_visuels_enquete.md`
- `docs/plan_directeur_coproscope_local_vault.md`
- `docs/livraison_test_2000.md`
- `docs/qa_ui_integration_2000.md`
- `docs/ux_review_atelier_piece.md`
- `docs/accessibilite_registre_langage.md`
- `docs/resilience_anti_accaparement.md`
- `docs/orchestration_agents.md`

## Cap 21h15

Le jalon 21h15 ne cherche pas a finir CoproScope. Il doit produire une version locale ouvrable, testable sur instance synthetique, et assez honnete pour ne pas confondre:

- depot local;
- export local;
- coffre/vault chiffre et signe;
- sync externe non fiable;
- droits de lecture et role dans la copro.

La promesse utilisateur a verifier reste: un conseil syndical voit quoi traiter maintenant, pourquoi, avec quelle preuve, quelle prochaine action, et quelle prudence de diffusion.

## Etat des chantiers

| Chantier | Etat orchestration | Livrable attendu avant integration | Points de vigilance |
|---|---|---|---|
| Comptes, roles, commissions | Actif, structurant | Parcours lisible `qui suis-je`, role courant, droits visibles, commissions differenciees, limites de revocation documentees | Ne pas melanger compte local, membre du coffre, appareil de signature et role copro/CS. Depend de `AccessOps`/gouvernance et conditionne les alertes vault. |
| Sync alertes / vault survivability | Actif, structurant | Etats `local seulement`, `sync configuree`, `sync a verifier`, `protection`, `incident`; pas de scan process/ports; rapport lisible | Ne promettre aucune sync cloud sure. Le dossier sync ne doit contenir ni `.git`, ni `.venv`, ni cache clair, ni export temporaire. |
| Atelier piece actionnable | Actif, UI prioritaire | Ligne ouvrable piece -> point -> action -> preuve; badges diffusion; statut de confiance/historique si disponible; filtres utiles | Risque de collision fort avec `viewmodel.py`, `pieces.html`, `document_viewer.py` et les tests UI. |
| Cockpit conseil syndical | Actif, UI prioritaire | 3 a 5 cartes `A faire maintenant`; raison, preuve/source, prochaine action, prudence de diffusion; compteurs ouvrables | Ne pas creer de logique metier propre au cockpit: il agrege actions, comptes, documents, incidents, decisions et alertes. |
| UX tester novice/accessibilite | Actif, verification | Revue de navigation 15 min, vocabulaire, prochaine action visible, depot != sync, focus/labels/captions | Doit pouvoir bloquer une integration si le produit parle trop moteur ou cache une limite de confidentialite/sync. |
| Depot/PDF/annotations | Adjacent, a integrer prudemment | Depot guide, viewer document, annotations separees de l'original, exports sans bruts prives | Depend de l'atelier et de PrivacyOps; ne doit pas modifier les originaux. |
| Indicateurs de pilotage | Adjacent, source cockpit | Peu d'indicateurs avec periode, preuve, seuil et action | Un indicateur sans action ne doit pas entrer dans le cockpit principal. |
| Memoire/passation | Adjacent, apres stabilisation action/preuve | Pack de passation derive, restrictions visibles | Ne pas stocker le pack comme source de verite. |

## Dependances entre lots

1. Comptes et roles doivent preceder les droits fins de sync, les invitations, les revocations et les commissions thematiques.
2. Sync alertes depend du noyau vault, mais doit exposer une UI sobre au cockpit: statut, niveau d'alerte, derniere verification, action corrective.
3. Cockpit depend de l'atelier, des comptes, des indicateurs et des alertes sync, mais ne doit pas posseder leurs schemas.
4. Atelier piece depend de Documents, Actions, PrivacyOps/BiffageOps et du viewer document; il est le point d'integration piece -> preuve.
5. UX tester doit passer apres chaque livraison UI et avant merge final 21h15.
6. Depot/PDF/annotations depend de l'anti-fuite: aucune route UI ne sert `raw/`, `restricted/`, logs, secrets, mappings ou chemins prives inattendus.
7. La prochaine vague AG/contentieux/passation depend d'une boucle decision/action/preuve deja lisible.

## Criteres d'integration communs

Un lot peut etre integre dans la branche d'integration seulement si:

- `git status --short` du worktree est fourni et les fichiers modifies sont dans l'ownership annonce;
- aucune modification ne revert explicitement un changement d'un autre agent;
- les tests cibles du lot sont lances ou l'impossibilite est documentee;
- les routes UI concernees repondent en 200 sur l'instance synthetique si le lot touche l'interface;
- la navigation tokenisee ne casse pas les routes protegees, surtout `Depot`;
- le vocabulaire novice est respecte: `coffre`, `preuve`, `action`, `diffusion`, `restriction`, pas seulement `vault`, `hash`, `DocOps`;
- les sorties diffusablement visibles ne contiennent pas de bruts prives, chemins locaux sensibles, mappings de biffage, `.env`, `.git`, `.venv`, caches ou worktrees;
- le lot documente clairement ce qui est livre, ce qui est chantier, et ce qui ne doit pas etre promis au testeur;
- toute action mutable pretendue collaborative est soit un evenement signe, soit marquee comme prototype/local non signe.

## Criteres de passage 21h15

Passage possible si les points suivants sont vrais sur `examples/synthetic_copro`:

- `ui open-test` ouvre une UI locale sur `127.0.0.1` avec token et terminal visible.
- Les pages Cockpit, Actions, Comptes, Documents, Atelier pieces, Confidentialite, Chantiers et Depot sont testees.
- Le cockpit affiche des cartes ou alertes actionnables avec raison, preuve/source et prochaine action.
- Comptes/roles expliquent au moins le role courant et ne confondent pas compte local, membre de coffre et appareil.
- L'atelier permet de comprendre au moins une chaine piece -> point -> action -> preuve et signale la prudence de diffusion.
- Le depot dit explicitement qu'il est local et ne promet ni publication, ni sync cloud, ni vault verifie.
- Les alertes sync/vault, si visibles, parlent de transport non fiable et d'actions de verification, pas de garantie cloud.
- Les exports testables ne contiennent pas `raw/`, `restricted/`, `logs/`, `.git`, `.venv`, `.env`, mappings ou chemins prives inattendus.
- Le testeur UX peut repondre en moins de 10 minutes: trois sujets urgents, preuve disponible, action suivante, partage possible.

No-go si:

- page blanche ou erreur serveur sur une page principale;
- confusion visible depot/export/vault/sync;
- import ou affichage de donnees reelles requis pour la demo;
- route ou export expose un brut prive ou un chemin sensible;
- merge partiel template/viewmodel casse le cockpit;
- deux agents ont modifie la meme zone convergente sans arbitrage d'integration.

## Vague active a integrer

| Agent | Branche/worktree attendu | Ownership modifiable | Hors perimetre | Tests attendus | Livrable final |
|---|---|---|---|---|---|
| Comptes | `codex/vault-comptes-roles` sous `_worktrees` | `server/src/coproscope/modules/accessops.py`, `server/src/coproscope/web/governance.py`, `server/src/coproscope/web/templates/governance.html`, `server/tests/test_accessops_commissions.py`, `server/tests/test_ui_governance.py` | `server/src/coproscope/vault/**` sauf contrat documente, `overview.html`, `pieces.html` | `python -m pytest tests/test_accessops_commissions.py tests/test_ui_governance.py -q` ou unittest equivalent | Roles, droits, commissions et limites de revocation lisibles. |
| Sync alertes | `codex/vault-sync-alertes` sous `_worktrees` | `server/src/coproscope/vault/sync_profiles.py`, `server/src/coproscope/vault/resilience.py`, `server/tests/test_vault_sync_profiles.py`, `server/tests/test_vault_resilience.py` | UI globale sauf note d'integration; pas de scan process/ports | `python -m pytest tests/test_vault_sync_profiles.py tests/test_vault_resilience.py -q` ou unittest equivalent | Etats d'alerte, rapport et reactions protection/incident. |
| Atelier piece | `codex/vault-ui-pieces-actionable` sous `_worktrees` | `server/src/coproscope/web/templates/pieces.html`, `server/tests/test_ui_atelier_piece.py`, eventuellement helpers locaux dedies | `viewmodel.py` sauf accord explicite coordinateur; pas de refonte cockpit | `python -m pytest tests/test_ui_atelier_piece.py -q` ou unittest equivalent | Lignes ouvrables, filtres, badges diffusion, prochaine action. |
| Cockpit | `codex/vault-ui-cockpit` sous `_worktrees` | `server/src/coproscope/web/templates/overview.html`, `server/tests/test_ui_cockpit.py`, helpers de presentation dedies | `viewmodel.py` seulement si l'agent Cockpit en est l'owner unique; pas de schemas metier | `python -m pytest tests/test_ui_cockpit.py tests/test_ui_demo.py -q` ou unittest equivalent | 3 a 5 cartes `A faire maintenant`, compteurs ouvrables, confiance visible. |
| UX tester | `codex/vault-ui-ux-review` sous `_worktrees` | `docs/ux_review_atelier_piece.md`, `docs/qa_ui_integration_2000.md`, notes QA dediees | Code produit, schemas, templates | Revue navigateur manuelle + routes principales; noter tests impossibles | Verdict go/no-go novice, accessibilite et anti-confusion depot/sync. |

Note d'arbitrage: `server/src/coproscope/web/viewmodel.py` est la zone de collision principale. Un seul agent UI doit en etre owner a un instant donne. Les autres doivent produire une note d'integration ou des tests qui echouent proprement.

## Prochaine vague recommandee

Lancer seulement apres retour `PRET_A_INTEGRER` ou integration des lots qui debloquent chaque dependance.

| Declencheur | Agent suivant | Ownership separe | Objectif |
|---|---|---|---|
| Comptes pret | Commissions productions | `server/src/coproscope/modules/accessops.py` extensions bornees, `server/tests/test_accessops_commissions.py`, template commission dedie si cree | Mandat, referent CS, droits proportionnes, productions citees et diffusables. |
| Comptes + sync alertes prets | Notifications internes vault | `server/src/coproscope/vault/resilience.py`, tests alertes dedies, pas d'email/SMS | Bannieres UI/journal/evenement signe `vault_alert_raised`; plugins externes reportes. |
| Sync alertes pret | Archive/reconstruction coproprietaire | `server/src/coproscope/vault/resilience.py`, nouveau test reconstruction pack si besoin | Archive complete chiffree, preuves de presence des restrictions, reconstruction du corpus autorise. |
| Atelier + cockpit prets | Parcours `Jour de CS` | `overview.html`, `actions.html`, tests UI dedies; ownership `viewmodel.py` a reserver explicitement | Parcours court: a demander, verifier, rattacher, arbitrer, cloturer. |
| Atelier pret | PDF/annotations collaboratives | `server/src/coproscope/web/document_viewer.py`, `document_detail.html`, `test_ui_document_viewer.py` | Viewer central, annotations hors original, ancres stables, diffusion controlee. |
| Cockpit + indicateurs prets | Pilotage indicateurs | `server/src/coproscope/modules/indicatorops.py`, `test_indicatorops.py`, carte cockpit si owner cockpit libre | 6 a 10 indicateurs max, periode, preuve, seuil, action. |
| UX tester no-go vocabulaire | Accessibilite/langage | `server/src/coproscope/web/static/styles.css`, templates cibles, tests UI statiques dedies | Focus visible, labels, captions, termes rares expliques, prochain geste evident. |
| Decision/action/preuve stable | AG/contentieux/passation | modules AG/decision existants, tests dedies, template hors ownership cockpit | Dossiers probatoires sensibles, restrictions, questions AG, pack passation derive. |

## Risques Git/worktree

Etat observe dans le repo principal au moment de cette orchestration:

- la branche courante est `codex/integration-livraisons`;
- le worktree principal contient de nombreux fichiers modifies et non suivis, dont plusieurs zones UI, vault, modules et tests;
- `docs/orchestration_agents.md` et ce document sont les seuls fichiers que l'orchestrateur doit modifier;
- plusieurs worktrees existent sous `C:\Users\brice\CoproScope\_worktrees`, ce qui est conforme a la strategie actuelle;
- plusieurs anciens worktrees existent encore sous `G:/Mon Drive/...`, dont certains sont marques `prunable`; ils ne doivent pas etre utilises pour de nouveaux travaux ni integres sans audit explicite;
- les branches Drive historiques peuvent contenir des changements utiles, mais elles violent le garde-fou actuel si elles continuent a travailler dans un dossier synchronise.

Risques de conflit forts:

- `server/src/coproscope/web/viewmodel.py`: convergence cockpit, atelier, comptes, documents, indicateurs.
- `server/src/coproscope/web/app.py`: routes UI et token.
- `server/src/coproscope/web/templates/base.html`: navigation, token, bandeau confiance.
- `server/src/coproscope/web/static/styles.css`: accessibilite et rendu global.
- `server/src/coproscope/cli.py`: commandes partagees, a integrer par agent unique.
- `docs/roadmap_produit_fini_visuels_enquete.md`: doc de cap, ne pas faire modifier en parallele pendant le jalon.

Regle d'integration: integrer une branche a la fois, relire les diffs, privilegier les tests dedies puis le smoke UI. En cas de conflit, garder la fonctionnalite la plus proche des criteres 21h15: prochaine action visible, preuve citee, diffusion prudente, aucune sur-promesse sync/vault.

## Message au superviseur principal

Je ne lance pas les agents depuis cette session. A copier-coller au superviseur principal:

```text
Lancer la vague 21h15 uniquement dans des worktrees sous C:\Users\brice\CoproScope\_worktrees, jamais sous Drive. Chaque agent commence par git status --short, lit docs/orchestration_2115.md et docs/orchestration_agents.md, respecte son ownership, ne revert aucun changement d'autrui, et termine avec fichiers modifies, tests, limites, go/no-go integration. Reserver server/src/coproscope/web/viewmodel.py a un seul owner UI a la fois.
```
