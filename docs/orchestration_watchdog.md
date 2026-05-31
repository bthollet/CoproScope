# Diagnostics orchestration CoproScope

Date de mise a jour: 2026-05-30.

Depuis le recadrage `/objectif`, la continuite normale est portee par l'objectif
actif Codex et par `docs/presence_agents.md`. Il n'y a plus de heartbeat
canonique ni de watchdog permanent a maintenir par defaut.

## Outils

| Commande | Role |
|---|---|
| `tools\orchestration-watch.cmd` | Lit `docs/presence_agents.md` et `docs/roadmap_backlog_central.md`, puis affiche les conversations vivantes, expirees, bloquees, en attente utilisateur et pretes a integrer. |
| `tools\orchestration-watch.cmd --emit-prompt` | Produit un prompt de reprise pour le fil pilote, avec routage automatique d'equipe-type. |
| `tools\orchestration-watch.cmd --team uxui --emit-prompt` | Produit une reprise orientee protocole UX/UI recherche, sans dev. |
| `tools\orchestration-watch.cmd --strict` | Retourne un code d'erreur si une decision, un blocage, une expiration ou une conversation active trop ancienne est detecte. |
| `tools\orchestration-supervise.cmd --emit-recovery-prompt` | Affiche la politique courante, les anciennes heartbeats actives a pauser, les traces ouvertes/pretes et l'hygiene Codex si elle est demandee. |
| `tools\orchestration-supervise.cmd --read-codex-processes` | Diagnostic lecture seule des processus d'outillage Codex, utile si le poste devient lourd. |
| `tools\agent-check.cmd -Orchestration` | Affiche les diagnostics orchestration avant les checks rapides, sans exiger de heartbeat permanente. |

## Regles d'interpretation

- `EN_COURS` avec heartbeat trop ancien: reprendre seulement le role manque,
  idle, bloque ou expire; ne pas dupliquer un role vivant.
- `EN_ATTENTE_USER`: ne pas lancer de nouvelle equipe. Le prompt sert a
  remonter l'arbitrage a Brice.
- `BLOQUE`: ne pas masquer le blocage par une nouvelle equipe artificielle.
- `PRET_A_INTEGRER`: ouvrir un owner unique d'integration seulement si le
  gouvernail ou Brice valide le passage en integration.
- `Orchestrator trace: STALE` signale une trace ancienne; ce n'est plus, seul,
  une raison de reactiver une heartbeat.
- Les anciennes automations `relance-worker-*`, `worker-*`, `ce-*`,
  `relance-ce-*` et `relance-equipe-agile-gouvernail-autonome` doivent rester
  pausees, sauf demande explicite de Brice pour un reveil horodate borne.

## Relance autorisee

Un heartbeat Codex peut etre cree uniquement si Brice demande un reveil date.
Dans ce cas:

- il est borne a un `CH-*` deja declare;
- il ne choisit pas seul un nouveau `ORD-*`;
- il relance seulement les roles manquants, idle, bloques ou expires;
- il laisse une trace dans `docs/presence_agents.md`;
- il est mis en pause des que le besoin de reveil disparait.

## Hygiene CPU/RAM

Par defaut, les diagnostics ne tuent aucun processus. L'option
`--read-codex-processes` lit seulement les processus d'outillage Codex pour
donner un ordre de grandeur. Si le poste est lourd, la correction normale est
manuelle: fermer les anciens outils ou redemarrer Codex, sans toucher aux
serveurs CoproScope reserves.

## Serveurs et recettes live

Les equipes agiles doivent tester l'UI reelle des que possible. Quand un lot
livre une page, une route, une modale, un fragment visible ou une interaction,
QA et novice testent via un serveur local reserve.

Regles serveur:

- reserver le port dans `docs/presence_agents.md` avant demarrage;
- indiquer `CONV-*`, role owner, instance, token de test et commande prevue;
- utiliser `examples/synthetic_copro` pour une preuve partageable, ou
  `beauvallon_test` seulement si le scenario local l'exige;
- garder le serveur dans un PowerShell visible, identifiable par port et
  `CONV-*`;
- arreter par `Ctrl+C`, pas par kill de processus;
- fermer apres recette ou apres merge, sauf demande explicite de Brice de le
  garder ouvert pour un essai immediat; tracer alors le port, l'heure et la
  personne responsable de l'arret;
- ne pas scanner les ports ou processus;
- si un port est douteux, noter le conflit et prendre un autre port documente
  dans `8780` a `8799`;
- citer dans la trace finale l'URL testee, le scenario clique, les captures
  desktop/mobile ou le waiver `RECETTE_PAGE_REELLE_WAIVED`;
- ne jamais brancher une capture diffusable sur une instance privee brute.

Les diagnostics orchestration ne demarrent aucun serveur. Ils lisent seulement
les registres locaux et les automations connues.
