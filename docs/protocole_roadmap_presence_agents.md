# Protocole roadmap, backlog et presence agents

Date de creation: 2026-05-21.

Ce protocole relie quatre choses qui ne doivent pas etre confondues:

| Niveau | Role | Registre |
|---|---|---|
| Gouvernail roadmap | Source de verite unique des intentions officielles | `docs/roadmap_backlog_central.md` |
| Chantier | Travail ouvert sur une intention | `docs/presence_agents.md` |
| Conversation/agent | Fil vivant qui execute ou coordonne | `docs/presence_agents.md` |
| Worktree/branche | Isolation technique Git | Git + registre de presence |

## Ajouter a la roadmap

Le fichier `docs/roadmap_backlog_central.md` fait foi. Les anciennes feuilles de
route, backlogs, journaux de cycle et commandes dev ne sont que des sources
rattachees tant qu'une ligne `RM-*` ne reprend pas leur intention.

Quand Brice dit "ajoute ceci a la roadmap":

1. Ajouter une ligne `RM-YYYY-NNNN` dans `docs/roadmap_backlog_central.md`.
2. Mettre le statut `A_QUALIFIER`, sauf instruction contraire.
3. Renseigner la source: conversation, fichier, issue, piece ou demande orale.
4. Renseigner une prochaine action courte.
5. Ajouter une ligne au journal append-only.

Le backlog n'est pas une promesse de livraison. La roadmap est une intention
retenue. Un chantier actif commence seulement quand un owner et un perimetre
sont declares.

## Demarrer un chantier

Avant toute edition, l'agent ou la conversation:

1. lit `AGENTS.md`, `docs/consignes_bots_interconversations.md`, ce protocole,
   `docs/roadmap_backlog_central.md` et `docs/presence_agents.md`;
2. rattache son travail a un `RM-*`;
3. cree ou met a jour un `CH-*` et un `CONV-*`;
4. declare ownership, fichiers evites, worktree/branche, tests attendus;
5. fixe un lease d'ownership et une prochaine action.

Sans `RM-*` clair, l'agent cree d'abord une entree `A_QUALIFIER` ou reste en
lecture seule.

## Pendant le travail

- Mettre a jour le heartbeat si le travail dure.
- Ne jamais supposer qu'un worktree suffit a prouver l'activite.
- Ne pas toucher un fichier sensible sans ownership explicite.
- Si une autre conversation modifie un fichier hors ownership, continuer.
- Si une autre conversation modifie le meme fichier ou le meme chemin
  semantique, marquer le chantier `BLOQUE` et demander coordination.

## Arreter une conversation

Une conversation s'arrete par un statut explicite dans `docs/presence_agents.md`:

- `PRET_A_INTEGRER` si elle a livre un diff, une doc ou une decision a relire;
- `INTEGRE` si le coordinateur a integre et verifie;
- `EN_ATTENTE_USER` si Brice doit arbitrer;
- `BLOQUE` si une dependance empeche de finir;
- `EXPIRE` si le lease est depasse sans heartbeat;
- `CLOTURE` si rien ne reste a reprendre;
- `ABANDONNE` si le chantier est arrete sans suite.

La trace finale doit lister les fichiers modifies, fichiers evites,
tests/preuves et limites. Une conversation sans trace finale n'est pas une
source de verite suffisante.

## Cloture UI/UX et preuve novice

Pour tout chantier qui modifie une route, un template, un parcours ou un
contrat UX, une route en 200 et des assertions de libelles ne suffisent pas a
declarer un GO produit.

La trace de fin doit indiquer:

- le scenario utilisateur vise;
- les routes et parametres verifies;
- le comportement attendu au clic ou a la saisie;
- la preuve navigateur desktop/mobile, ou la raison explicite de non-execution;
- le verdict GO/NO-GO novice;
- les limites restantes: CTA trompeur, H1/menu incoherent, aide seulement en
  `title`, jargon moteur visible, action sans preuve/diffusion/trace.

Si cette preuve manque, le chantier peut etre `PRET_A_INTEGRER`, mais pas
declare comme validation novice finale.

## Doctrine worktrees

Le worktree isole l'execution. Il ne dit pas a lui seul:

- pourquoi le chantier existe;
- quelle roadmap il sert;
- quelle conversation le pilote;
- si le travail est encore vivant;
- quels fichiers sont reserves;
- si le resultat est integre.

Le registre de presence fait foi pour l'activite. Git fait foi pour les diffs.
Le journal append-only fait foi pour les decisions de suivi.

## Sources et principes retenus

- Git worktree: isolation de plusieurs arbres de travail, pas pilotage de
  l'intention: https://git-scm.com/docs/git-worktree
- GitHub Issues/Projects: relier idee, branche, PR, statut, owner et champs:
  https://docs.github.com/en/issues
- Codex worktrees: un thread peut etre associe a un worktree, mais il faut
  garder la supervision claire: https://developers.openai.com/codex/app/worktrees
- Codex AGENTS.md: les consignes persistantes donnent les regles communes:
  https://developers.openai.com/codex/guides/agents-md
- Kanban: limiter le travail en cours et rendre les regles explicites:
  https://resources.kanban.university/wp-content/uploads/2021/06/The-Official-Kanban-Guide_US.pdf
- ADR: une decision conserve son statut et peut etre remplacee sans effacement:
  https://faq.arc42.org/questions/C-9-3/
