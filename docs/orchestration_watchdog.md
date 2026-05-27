# Watchdog orchestration CoproScope

Date de creation: 2026-05-25.

Ce document decrit les outils locaux qui evitent que les conversations
agiles/UX s'arretent silencieusement malgre les heartbeats.

## Outils

| Commande | Role |
|---|---|
| `tools\orchestration-watch.cmd` | Lit `docs/presence_agents.md` et `docs/roadmap_backlog_central.md`, puis affiche conversations vivantes, expirees, bloquees, en attente utilisateur et pretes a integrer. |
| `tools\orchestration-watch.cmd --emit-prompt` | Produit un prompt de relance CoproScope avec routage automatique d'equipe-type, reserve a l'orchestrateur. |
| `tools\orchestration-watch.cmd --team uxui --emit-prompt` | Produit une relance orientee protocole UX/UI recherche, sans dev. |
| `tools\orchestration-watch.cmd --strict` | Retourne un code d'erreur si une decision, un blocage, une expiration ou une heartbeat stale est detecte. |
| `tools\orchestration-supervise.cmd --emit-recovery-prompt` | Supervise la heartbeat canonique depuis l'exterieur: automation active, cadence, doublons et trace recente. |
| `tools\orchestration-supervise.cmd --cleanup-codex-tool-processes` | En plus de la supervision, nettoie les processus d'outillage Codex accumules (`node_repl.exe` et petits `codex.exe app-server --listen stdio://`) seulement si les seuils d'alerte sont depasses. |
| `tools\orchestration-supervise.cmd --strict` | Retourne un code d'erreur si la heartbeat canonique est absente, inactive, mal cadencee, dupliquee ou trop silencieuse. |
| `tools\agent-check.cmd -Orchestration` | Affiche le superviseur externe et le watchdog avant les checks rapides, puis repasse les deux en mode strict si les checks amont n'ont pas deja echoue. |

## Regles d'interpretation

- `EN_COURS` avec heartbeat trop ancien: relancer seulement les roles manquants,
  idle, bloques ou expires; ne pas dupliquer un role vivant.
- `EN_ATTENTE_USER`: ne pas lancer de nouvelle equipe. Le prompt emis sert a
  remonter l'arbitrage, pas a redispatcher le backlog.
- `BLOQUE`: ne pas masquer le blocage par une nouvelle equipe artificielle.
- `PRET_A_INTEGRER`: ouvrir un owner unique d'integration seulement si le
  gouvernail ou Brice valide le passage en integration.
- `--emit-prompt` en mode `auto`: la relance applique
  `docs/strategie_equipes_multi_agents.md` avant de choisir une equipe. `auto`
  ne signifie pas "agile standard": il peut produire incident/stationnement,
  fan-in, recherche metier, UX/UI recherche, agile UI produit, backend domaine,
  recette live, integration ou doctrine.
- Le prompt de relance est un outil d'orchestrateur. Les workers ne l'utilisent
  pas pour choisir leur travail. Ils lisent `docs/tableau_execution_courant.md`
  et prennent seulement un slot `A_PRENDRE` deja publie dans le `CH-*`
  courant.
- `--emit-prompt` en mode agile: la premiere relance doit deja inclure la
  composition canonique avec testeur expert metier
  juridique/compta/process chantier/syndic si un thread est disponible; sinon
  QA et coordinateur reprennent explicitement cette checklist.
- `AGILE-DONE`: le lot est ferme; la heartbeat peut passer au prochain `ORD-*`
  actionnable seulement s'il n'y a pas d'arbitrage `EN_ATTENTE_USER`, de
  blocage non stationne ou d'incident de doublon backlog. En cas d'incident,
  elle garde la heartbeat active en mode surveillance/reprise, bloque seulement
  le dispatch de nouveaux `ORD-*` et attend Brice.
- `Orchestrator trace: QUIET`: la derniere trace de stationnement est ancienne,
  mais elle mentionne encore les memes arbitrages, blocages et conversations
  stale/expirees. Ce n'est pas une raison d'ouvrir un role artificiel, mais cet
  etat est limite par une fenetre de grace.
- `Orchestrator trace: STALE`: le superviseur externe doit considerer que le
  heartbeat ne laisse plus de check-in fiable; il faut reparer ou recadrer
  l'automation avant de supposer que tout va bien.

## Supervision externe

Le watchdog appele par la heartbeat ne suffit pas a sauver une conversation qui
s'arrete: il meurt avec le fil qui devait l'appeler. La couche robuste est donc:

```text
cron superviseur externe horaire
  -> tools\orchestration-supervise.cmd --strict --cleanup-codex-tool-processes
  -> repare/recadre la heartbeat si elle est absente, inactive, dupliquee ou
     trop silencieuse

heartbeat canonique 5 minutes
  -> tools\orchestration-watch.cmd --emit-prompt
  -> route l'equipe-type avant tout nouveau CH-*
  -> publie ou maintient docs\tableau_execution_courant.md
  -> laisse toujours une trace persistante, meme en DONT_NOTIFY
  -> relance seulement les roles manquants d'un chantier deja declare si le
     dispatch de nouveaux ORD est bloque
```

Regle importante: un passage quiet doit laisser une trace `HEARTBEAT_CHECKIN`,
`HEARTBEAT_*_STATIONNEMENT` ou `NO_ORD_ACTIONNABLE` dans
`docs/presence_agents.md`. Si aucune trace recente n'apparait apres la fenetre
de grace, le superviseur traite la heartbeat comme stale.

## Hygiene processus Codex

Le superviseur mesure aussi les processus internes Codex cote poste Windows:

- `node_repl.exe` lances par les outils deferres;
- petits `codex.exe app-server --listen stdio://` rattaches a ces outils;
- memoire globale de l'application Codex, pour signaler quand un redemarrage
  manuel de l'application devient raisonnable.

Par defaut, le superviseur ne tue rien: il signale `Codex tool hygiene:
RECOVER` si au moins 20 processus d'outillage ou 1024 MB de working set
accumules sont detectes. Avec `--cleanup-codex-tool-processes`, il arrete
uniquement ces processus d'outillage Codex. Il ne touche pas aux serveurs
CoproScope reserves, aux PowerShell visibles de recette, aux ports locaux, aux
instances, ni aux processus principaux `Codex.exe`.

## Serveurs et recettes live

Le watchdog et le superviseur sont volontairement sans serveur: ils lisent les
registres, les automations et les traces. Ils ne lancent pas d'UI et ne
scannent pas les ports. La seule exception admise est l'option explicite
`--cleanup-codex-tool-processes`, bornee aux processus d'outillage Codex
internes decrits plus haut.

Cette regle ne s'applique pas comme interdiction globale aux equipes agiles
produit, dev ou QA. Quand une mission exige une recette navigateur ou une UI
live, l'equipe peut lancer ou utiliser un serveur local si le port, l'instance
de test, le token et la commande sont reserves dans `docs/presence_agents.md`,
et si le serveur reste dans un terminal PowerShell visible avec arret par
`Ctrl+C`. Ce qui reste interdit est le serveur non reserve, cache, ambigu,
branche sur une instance privee reelle, ou manipule par scan/kill de processus.

## Limite

Le watchdog lit les registres Git locaux. Il ne remplace pas la carte
d'automation Codex: la heartbeat active doit rester
`relance-equipe-agile-gouvernail-autonome`, cadence 5 minutes, destination fil
courant. Si le watchdog signale `STALE`, le coordinateur doit verifier ou mettre
a jour cette automation via l'app Codex. Si le watchdog signale `QUIET` dans la
fenetre de grace, il n'y a pas de nouveau role a ouvrir, mais la prochaine
heartbeat doit tout de meme laisser un check-in.

Si un incident de doublon bloque le dispatch, l'automation canonique ne doit pas
rester en pause: elle doit etre `ACTIVE`, cadence 5 minutes, avec un prompt
surveillance/reprise. `STALE` demande alors de reparer cette heartbeat active,
pas d'ouvrir un nouveau `ORD-*`.
