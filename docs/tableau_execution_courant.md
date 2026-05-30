# Tableau d'execution courant

Date de creation: 2026-05-28.
Rattachement: `RM-2026-0005`.

Ce fichier est la facade courte du travail en cours. Il evite que les
conversations workers lisent le gouvernail long et piochent chacune un
`ORD-*` different.

## Regle courte

- `docs/roadmap_backlog_central.md` est le backlog long et la source de
  verite strategique.
- `docs/tableau_execution_courant.md` est le tableau d'execution court du
  chantier courant.
- `docs/presence_agents.md` est le registre technique des conversations,
  leases, owners et traces finales.
- Seul l'orchestrateur choisit un `ORD-*` dans le backlog long.
- Les workers prennent seulement un slot `A_PRENDRE` deja publie dans ce
  tableau pour le `CH-*` courant.
- Si aucun slot `A_PRENDRE` n'existe, un worker s'arrete et attend
  l'orchestrateur.

## Vocabulaire humain

| Identifiant | Nom humain | Role |
|---|---|---|
| `RM-*` | Sujet produit | Intention stable, longue duree. |
| `ORD-*` | Tache backlog | Prochaine tranche actionnable, choisie par l'orchestrateur. |
| `CH-*` | Run / chantier | Execution ouverte sur une seule tache backlog. |
| `SLOT-*` | Slot de role | Travail prenable par un worker dans le chantier courant. |
| `CONV-*` | Conversation | Fil Codex qui coordonne ou execute un slot. |

## Etat courant

| Champ | Valeur |
|---|---|
| Dispatch nouveau `ORD-*` | `BLOQUE` |
| Cause | `CONV-2026-1776` en `EN_ATTENTE_USER` et `RM-2026-0041` en incident dispatch. |
| Chantiers DocOps doublons | `CONV-2026-1826`..`CONV-2026-1833` abandonnes/non vivants. |
| Blocage manuel stationne | `CONV-2026-1772`, recharge serveur visible `8788`. |
| Slots workers disponibles | Aucun tant que Brice n'a pas leve le blocage dispatch. |
| Prochain geste | Surveillance heartbeat et arbitrage explicite de Brice avant tout nouveau dispatch produit. |

## Roles de decision

### Orchestrateur

L'orchestrateur est le seul role qui peut:

- lancer `tools/orchestration-watch.cmd --emit-prompt`;
- lire la file `ORD-*` pour choisir le prochain travail;
- ouvrir un nouveau `CH-*`;
- publier ou fermer les slots `SLOT-*`;
- mettre a jour l'objectif actif Codex et les traces de presence;
- consolider les retours workers et choisir le mouvement suivant.

### Worker

Un worker peut:

- lire `AGENTS.md`, ce tableau et sa ligne `CONV-*`;
- prendre un seul slot `A_PRENDRE`;
- passer ce slot en `EN_COURS` avec son `CONV-*`;
- modifier seulement l'ownership du slot;
- livrer les tests/preuves demandes;
- passer le slot en statut final et publier son `BOT-END`.

Un worker ne peut pas:

- choisir un `ORD-*`;
- creer un `CH-*`;
- lancer `orchestration-watch.cmd --emit-prompt`;
- modifier l'objectif actif Codex ou creer une relance automatique;
- prendre un fichier non liste dans son ownership;
- relancer un role vivant ou un lot deja clos.

## Cycle standard

1. L'orchestrateur lit les diagnostics d'orchestration et le gouvernail.
2. S'il n'y a pas d'arbitrage ou de blocage, il choisit un seul `ORD-*`.
3. Il ouvre un seul `CH-*` et trace `ROUTAGE_EQUIPE`.
4. Il publie ici les slots du chantier courant, chacun en `A_PRENDRE`.
5. Les workers prennent les slots disponibles, un par conversation.
6. Les workers rendent leur `BOT-END` et repassent leur slot en statut final.
7. L'orchestrateur integre, ferme le chantier ou publie les slots restants.
8. Le prochain `ORD-*` n'est choisi qu'apres cloture ou arbitrage.

## Statuts de slot

| Statut | Sens |
|---|---|
| `A_PRENDRE` | Role publie par l'orchestrateur, pas encore pris. |
| `EN_COURS` | Worker actif, `CONV-*` renseigne. |
| `BLOQUE` | Worker bloque par source, decision, test ou conflit. |
| `PRET_A_INTEGRER` | Livrable termine, integration ou consolidation requise. |
| `TERMINE` | Role clos et integre dans la synthese du chantier. |
| `ANNULE` | Role retire explicitement par l'orchestrateur. |

## Slots du chantier courant

Il n'y a volontairement aucun slot prenable tant que le dispatch produit reste
bloque.

| Slot | ORD | CH | Role | Statut | Pris par | Ownership | Interdits | Livrable | Tests / preuves | Condition d'arret |
|---|---|---|---|---|---|---|---|---|---|---|
| `SLOT-AUCUN` | n/a | n/a | Aucun role worker ouvert | `ANNULE` | n/a | n/a | Tout dispatch produit | Attendre arbitrage | Watchdog seulement | Brice leve le blocage ou confirme un nouveau lot |

## Template de slots a publier

Quand le dispatch est autorise, l'orchestrateur remplace la ligne
`SLOT-AUCUN` par des slots de ce type:

| Slot | ORD | CH | Role | Statut | Pris par | Ownership | Interdits | Livrable | Tests / preuves | Condition d'arret |
|---|---|---|---|---|---|---|---|---|---|---|
| `SLOT-001` | `ORD-P0-XXX` | `CH-...` | Coordinateur-scribe | `A_PRENDRE` | n/a | Docs de mission et registres declares | Code produit hors slot, instances privees, secrets | Synthese et trace de coordination | Watchdog, diff-check docs | `BOT-END` ou blocage trace |
| `SLOT-002` | `ORD-P0-XXX` | `CH-...` | Owner code unique | `A_PRENDRE` | n/a | Fichiers code explicitement listes | Autres surfaces sensibles | Patch borne | Tests cibles + diff-check | `PRET_A_INTEGRER` ou `BLOQUE` |
| `SLOT-003` | `ORD-P0-XXX` | `CH-...` | QA / privacy | `A_PRENDRE` | n/a | Tests et notes QA declares | Correction code sans ownership | Verdict GO/NO-GO | Tests, captures si live reserve | `TERMINE` ou `BLOQUE` |

## Prompt worker universel

```text
Tu es un worker CoproScope, pas l'orchestrateur. Travaille dans
C:\Users\brice\CoproScope\coproscope. Lis AGENTS.md puis
docs/tableau_execution_courant.md et docs/presence_agents.md.

Ne choisis aucun ORD-*. Ne cree aucun CH-*. Ne lance pas
orchestration-watch.cmd --emit-prompt. Ne modifie pas l'objectif actif Codex et
ne cree pas de relance automatique.

Prends uniquement un slot A_PRENDRE du chantier courant dans
docs/tableau_execution_courant.md. Marque-le EN_COURS avec ton CONV-*,
respecte strictement l'ownership, livre le role demande, lance les
tests/preuves indiques, mets a jour le slot et ta ligne de presence, puis
termine par BOT-END. Si aucun slot A_PRENDRE n'existe, ne cree rien et reponds:
Aucun slot worker disponible; attente orchestrateur.
```

## Garde-fou anti-chevauchement

Si deux workers prennent le meme slot ou le meme ownership:

1. le plus recent repasse en lecture seule;
2. l'orchestrateur marque le doublon `BLOQUE` ou `ANNULE`;
3. aucun autre slot n'est ouvert tant que la collision n'est pas tracee;
4. les diffs existants sont relus avant integration.
