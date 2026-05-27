# Equipe agile - Travail en arriere-plan visible

Date de lancement: 2026-05-24 22:13 +02:00.
Roadmap: `RM-2026-0012`.
Chantier: `CH-20260524-221300-RM-2026-0012-background-visible`.
Conversations: `CONV-2026-1607` a `CONV-2026-1611`.
Mode: cadrage agile sans dev, sans serveur, sans instance privee.
Statut: pret a integrer.

## BOT-START

BOT-START - Coordinateur-scribe activite arriere-plan - 2026-05-24
22:13 +02:00.

Mission: definir une surface novice qui montre les travaux en cours:
automations, equipes, dernier passage, prochaine relance, progression,
blocages, erreurs et traces consultables, sans fuite de secrets ni chemins.

Ownership modifiable:

- ce document;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers a eviter: code applicatif, automations app, serveurs, instances
privees, exports bruts, secrets et `RM-2026-0017`.

## Roles

| Conversation | Role | Sortie |
|---|---|---|
| `CONV-2026-1607` | Coordinateur-scribe | Decision produit et commande future. |
| `CONV-2026-1608` | Designer service | Parcours et surface UI. |
| `CONV-2026-1609` | Utilisateur novice | GO/NO-GO comprehension. |
| `CONV-2026-1610` | Data/agents | Contrat `agent_activity_v1`. |
| `CONV-2026-1611` | QA privacy | Anti-fuite et tests futurs. |

## Decision produit

Verdict: `GO_CADRAGE`, `NO-GO_DEV_IMMEDIAT`.

Le nom novice recommande est `Activite en cours`. La promesse n'est pas de
montrer des logs techniques, mais de repondre a quatre questions:

- qu'est-ce qui travaille encore?
- quand est-ce passe pour la derniere fois?
- qu'est-ce qui bloque ou attend?
- que puis-je verifier sans ouvrir un terminal?

Cette surface doit etre utile quand Brice n'est pas devant son poste. Elle doit
eviter les chemins locaux, tokens, noms de fichiers bruts, donnees d'instance,
prompts complets et traces trop bavardes.

## Surface cible

Route future: `/pilotage/activite`.

Emplacements:

- bandeau compact dans le cockpit;
- page detail depuis `A surveiller`;
- export derive optionnel seulement apres PrivacyOps.

Structure:

1. `Maintenant`: equipes actives, terminees, bloquees.
2. `Dernier passage`: heure, resultat court, tests ou preuves.
3. `Prochaine relance`: cadence, cible, condition d'arret.
4. `Blocages`: ce qui attend Brice, un secret, un port, une instance ou un
   arbitrage.
5. `Traces`: liens vers docs de mission, presence et gouvernail.

## Contrat minimal

`agent_activity_v1`:

| Champ | Sens | Anti-fuite |
|---|---|---|
| `conversation_id` | `CONV-*`, automation ou role | Pas de prompt complet. |
| `roadmap_id` | `RM-*` principal | Aucun nom d'instance privee. |
| `status` | actif, pret, integre, bloque, cloture | Liste fermee. |
| `last_heartbeat_at` | dernier passage local | Date seulement, pas log brut. |
| `next_check_at` | prochaine relance prevue | Peut etre vide si termine. |
| `current_step` | prochain geste en langage novice | 180 caracteres max. |
| `blocked_by` | user, secret, port, instance, test, collision | Pas de details sensibles. |
| `proof_summary` | tests OK, doc livree, diff-check | Resume derive. |
| `trace_href` | lien repo vers doc ou presence | Pas de chemin `instances/`. |

Statuts UI:

- `Travaille`;
- `A relire`;
- `Integre`;
- `Bloque`;
- `Termine`;
- `Expire`.

## GO/NO-GO novice

GO si un membre CS comprend que CoproScope continue un travail local, voit le
dernier resultat et sait quoi regarder ensuite.

NO-GO si la surface ressemble a un journal technique, expose des chemins
locaux, affiche des prompts longs ou donne l'impression qu'une action externe
est partie automatiquement.

Microcopy:

- `Travaille`: un agent ou une automation a encore une action prevue.
- `A relire`: le travail est pret, mais pas encore fusionne ou valide.
- `Bloque`: une decision, un secret, un port ou une preuve manque.
- `Integre`: le lot est dans la base locale verifiee.

## Commande future

```text
Construire `agent_activity_v1`:
- route future `/pilotage/activite`;
- builder dedie qui lit uniquement `docs/presence_agents.md` et le gouvernail;
- aucune lecture de logs bruts, d'automations privees ou d'instances;
- carte cockpit compacte + page detail;
- filtres actif / bloque / a relire / termine;
- tests anti-fuite sur chemins, tokens, secrets, raw/restricted/logs;
- tests ligne 600 et `git diff --check`.
```

## Questions ouvertes

- Faut-il lire directement les automations app ou seulement la presence?
- Quelle duree avant de marquer `Expire` dans l'UI si le registre dit deja
  `EN_COURS`?
- Est-ce que les cycles termines doivent rester 24h visibles ou seulement les
  trois derniers?
- Faut-il un export de synthese pour Brice quand il revient au poste?

## BOT-END

BOT-END - Coordinateur-scribe activite arriere-plan - 2026-05-24
22:16 +02:00.

Statut: `PRET_A_INTEGRER`.

Fichiers modifies: ce document, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`.

Fichiers evites: code, automations app, serveurs, instances privees, exports
bruts, secrets et `RM-2026-0017`.

Tests/preuves: cadrage documentaire; `git diff --check` documentaire a lancer
apres mise a jour des registres.

AGILE-DONE - equipe agile a fini son job.
