# Strategie equipes multi-agents et routage automatique

Date de creation: 2026-05-28.
Rattachement: `RM-2026-0005`.

Ce document ajoute une couche au protocole agile existant: avant de lancer une
equipe, l'orchestrateur choisit automatiquement le type d'equipe et la strategie
d'orchestration. Le but est d'eviter le reflexe "equipe agile standard pour
tout", qui cree des chevauchements quand le sujet demande plutot du fan-in, une
recherche metier, une recette live ou un owner backend unique.

## Principe court

Le routage se fait dans cet ordre:

1. **Preflight anti-collision**: lire `docs/presence_agents.md` et
   `docs/roadmap_backlog_central.md`; si `EN_ATTENTE_USER`, incident doublon ou
   `BLOQUE` non stationne existe, ne pas choisir de nouveau `ORD-*`.
2. **Reprise avant dispatch**: si un `CH-*` vivant existe, relancer seulement
   ses roles manquants, idle, bloques ou expires, sans changer d'objectif.
3. **Classification du travail**: classer l'objectif par nature dominante:
   recherche, UX/UI, dev UI, backend/data, integration, recette, incident ou
   doctrine.
4. **Verrou unique**: declarer un seul `CH-*`, un coordinateur et les owners
   sensibles avant tout lancement de role.
5. **Tableau d'execution**: publier les slots workers du chantier dans
   `docs/tableau_execution_courant.md`; les workers ne lisent pas le backlog
   long pour choisir leur travail.
6. **Orchestration adaptee**: choisir fan-out/fan-in, pipeline decale, owner
   unique, serie stricte, monitor-only ou red-team selon le type d'equipe.

Un `ORD-*` n'est jamais pris directement par plusieurs conversations. Le
routeur choisit d'abord l'equipe-type, puis seulement il ouvre le chantier.
Les workers prennent ensuite des `SLOT-*` du tableau d'execution courant, pas
des `ORD-*`.

## Equipes-types

| Type | Quand le choisir | Roles usuels | Orchestration | Livrable attendu |
|---|---|---|---|---|
| `INCIDENT_STATIONNEMENT` | Doublon detecte, arbitrage ouvert, blocage non stationne, heartbeat a reparer. | Coordinateur-scribe, superviseur/watchdog. | Monitor-only: check-in persistant, aucun nouveau role, aucun nouveau `ORD-*`. | Trace de blocage, etat sain de la heartbeat, question d'arbitrage. |
| `FANIN_CONSOLIDATION` | Plusieurs conversations ont travaille le meme sujet ou des retours arrivent en decalage. | Coordinateur-scribe, eventuellement un QA privacy en lecture. | Collecte par angle stable, dedoublonnage, contradictions conservees comme arbitrages. | Synthese convergence/divergence, un seul prochain dispatch propose. |
| `RECHERCHE_METIER` | Question juridique, syndic, compta, travaux, CS, SHS, veille, challenge sans dev. | Juriste/syndic, compta, travaux/process, CS/usage, privacy/QA novice, coordinateur. | Fan-out/fan-in borne: chaque expert rend son angle, le coordinateur consolide. | Note ou matrice `fait -> preuve -> regle/process -> action`; aucun code. |
| `UXUI_RECHERCHE` | Recherche UX/UI sans dev, parcours a explorer, directions visuelles, images candidates. | Orchestrateur UX/UI, chercheur utilisateur, architecte UX, designer visuel, testeur metier, novice/accessibilite. | Divergence puis convergence: images candidates, tests, selection, decisions. | Doc de mission, images retenues, decisions UX/UI, marqueur `UXUI-DONE`. |
| `AGILE_UI_PRODUIT` | Ecran, route, parcours ou interaction a concevoir puis livrer. | Coordinateur, designer/facilitateur, novice, dev front, dev back/viewmodel, QA, expert metier si possible. | Pipeline decale `N-1/N/N+1`: QA livre, dev commande validee, designer prepare la suite. | Route/artefact testable, visuel IA bitmap plein ecran, blueprint, GO/NO-GO novice, tests. |
| `BACKEND_DOMAINE` | Schema, vault, read model, extracteur, sync, Drive, contrat de donnees, API interne. | Coordinateur, owner backend/data unique, expert metier, QA privacy/regression, integration lead si besoin. | Hub-and-spoke: un owner code ecrit; les autres challengent en lecture ou notes. | Contrat de donnees, patch borne, tests cibles, anti-fuite, note d'integration. |
| `RECETTE_LIVE_QA` | Serveur reserve, verification navigateur, captures desktop/tablette/mobile, token 200/403. | QA live, novice, designer/readiness, coordinateur; dev en lecture sauf correctif decide. | Gate serie: serveur visible reserve -> checks -> captures -> verdict -> commande corrective eventuelle. | GO/NO-GO live, captures de recette, liste de corrections bornees. |
| `INTEGRATION_RELEASE` | Branches ou worktrees a relire, conflits, tests de convergence, livrables `PRET_A_INTEGRER`. | Coordinateur integration, QA regression, owners d'origine consultes en lecture. | Serie stricte: une branche a la fois, diff, tests, resolution, trace. | Integration verifiee ou blocage explicite; aucun dispatch produit simultane. |
| `DOCTRINE_SIDEQUEST` | Regle transverse, documentation d'orchestration, clarification non bloquante. | Coordinateur doctrine ou sub-agent docs. | Travail borne hors chemin critique; pas de code applicatif sauf demande explicite. | Protocole, ADR, note de cadrage, mise a jour AGENTS/docs. |

Ces equipes ne sont pas toutes des "standards" au sens Scrum strict. Elles
reprennent des formes connues: squad de livraison, equipe discovery UX, groupe
d'experts domaine, red-team/revue d'architecture, equipe QA/release et cellule
incident. CoproScope les nomme explicitement pour que le routage soit testable.

## Classification automatique

Le routeur applique d'abord les overrides de securite, puis une classification
par signaux. Le premier signal fort gagne; en cas d'ambiguite, choisir le mode
le moins dangereux, donc recherche ou fan-in plutot que dev.

| Signal dominant | Equipe-type | Strategie |
|---|---|---|
| `EN_ATTENTE_USER`, `BLOQUE incident dispatch`, doublon backlog | `INCIDENT_STATIONNEMENT` | Monitor-only, aucune lecture de la file `ORD-*` pour dispatch. |
| Plusieurs retours sur le meme sujet, conversations fermees par Brice, WIP concurrent | `FANIN_CONSOLIDATION` | Fan-in obligatoire avant tout nouveau lot. |
| Mots `veille`, `challenge`, `cadrage`, `juridique`, `syndic`, `compta`, `travaux`, `SHS`, `sources`, et pas de patch attendu | `RECHERCHE_METIER` | Fan-out expert puis synthese. |
| Commande explicite `equipe UX/UI`, `recherche UX`, `images candidates`, `parcours`, sans dev | `UXUI_RECHERCHE` | Divergence visuelle puis convergence. |
| Route, ecran, template, CSS, parcours novice, cockpit, UI ou interaction utilisateur | `AGILE_UI_PRODUIT` | Pipeline decale avec visuel IA et blueprint avant dev. |
| Vault, DB, schema, read model, extraction, sync, Drive, API, recorder, taxonomie config | `BACKEND_DOMAINE` | Owner code unique, experts en lecture, tests cibles. |
| Serveur reserve, `8788`, token, captures, navigateur, desktop/tablette/mobile | `RECETTE_LIVE_QA` | Gate live serie, pas de serveur non reserve. |
| `PRET_A_INTEGRER`, worktree, branche, conflit, panier de tests global | `INTEGRATION_RELEASE` | Integration une par une. |
| Doctrine, protocole, AGENTS, watchdog, gouvernail, regle transverse | `DOCTRINE_SIDEQUEST` | Patch documentaire borne. |

Le routeur ne se contente pas du mot cle. Il relit aussi le gate de l'`ORD-*`,
les owners vivants, le statut du `RM-*`, le dernier check-in et les interdits
explicites de Brice.

## Patterns d'orchestration

| Pattern | Usage | Regle anti-chevauchement |
|---|---|---|
| `monitor-only` | Incident, arbitrage, heartbeat, blocage. | Aucun nouveau `CH-*`, aucun nouveau `ORD-*`; check-in seulement. |
| `fan-out/fan-in` | Recherche metier, veille, challenge, plusieurs angles. | Les agents ont des angles stables; le coordinateur consolide avant dispatch. |
| `pipeline decale` | UI produit. | `N+1` design, `N` dev, `N-1` QA; dev attend visuel IA + blueprint + GO novice. |
| `hub-and-spoke owner` | Backend/data/Drive/DB. | Un seul owner ecrit le code; experts et QA rendent des notes ou tests. |
| `serie stricte` | Integration, release, recette live. | Une branche, un serveur ou un verdict a la fois. |
| `red-team borne` | Cadrage sensible, securite, modele metier. | Lecture seule, objections sourcees, puis arbitrage. |

## Sortie obligatoire du routeur

Avant de lancer des roles, le coordinateur trace:

```text
ROUTAGE_EQUIPE
Preflight: OK | INCIDENT | FANIN | REPRISE_CH_EXISTANT
Equipe-type:
Orchestration:
Roadmap / ORD:
Chantier:
Coordinateur:
Owner code unique:
Roles a lancer:
Roles explicitement non lances:
Gates avant dev:
Livrable attendu:
Condition d'arret:
Tableau execution: slots `SLOT-*` publies dans docs/tableau_execution_courant.md
```

Si `Preflight` vaut `INCIDENT`, `FANIN` ou `REPRISE_CH_EXISTANT`, le routeur
n'a pas le droit d'ouvrir un nouveau `ORD-*`. Il doit reprendre ou stationner.

## Regles specifiques UI

Pour `AGILE_UI_PRODUIT`, le routeur applique les regles du protocole agile:

- visuel IA bitmap de l'ecran complet, chemin reference, jamais SVG;
- blueprint structurel separe, chemin reference;
- qualification novice du visuel, du blueprint et de l'UI existante;
- dev seulement apres commande stabilisee;
- `VISUEL_IA_WAIVED` et/ou `BLUEPRINT_WAIVED` possibles seulement avec
  justification tracee;
- screenshots de livraison seulement comme preuve QA aval.

Pour `UXUI_RECHERCHE`, les images candidates servent a decider une direction,
pas a prouver une livraison. Les images retenues sont archivees uniquement si
elles portent une decision, un test ou un apprentissage.

## Regles specifiques backend/data

Pour `BACKEND_DOMAINE`, le routeur limite le parallele:

- un seul owner code sur le schema, le vault, les configs ou le read model;
- les experts metier ne patchent pas; ils rendent des invariants, cas limites
  et no-go;
- QA privacy teste anti-fuite, compatibilite et regression;
- le coordinateur refuse tout patch qui modifie plusieurs surfaces sensibles
  sans contrat de donnees et tests cibles.

## Heuristique de prudence

Si le routeur hesite entre deux equipes:

1. incident ou arbitrage gagne toujours sur tout;
2. fan-in gagne sur nouveau dispatch;
3. recherche gagne sur dev si le besoin ou la source est instable;
4. backend owner unique gagne sur equipe agile complete si le fichier sensible
   est le centre du travail;
5. UI agile gagne seulement si une UI reelle, un visuel IA, un blueprint et un
   GO novice peuvent exister;
6. integration gagne si un livrable `PRET_A_INTEGRER` attend deja.

Cette prudence est volontaire: elle sacrifie un peu de vitesse pour eviter les
lots concurrents sur le meme `ORD-*`.
