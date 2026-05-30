# Consignes bots interconversations

Ce document est la regle commune pour tout bot ou conversation qui travaille sur CoproScope. Il complete `AGENTS.md`, `docs/orchestration_agents.md`, `docs/protocole_roadmap_presence_agents.md` et les passerelles UX/DB.

## Regle zero

Aucun bot ne demarre une modification sans avoir declare:

- l'item roadmap `RM-*` rattache;
- le chantier `CH-*` et la conversation `CONV-*`;
- son role;
- son ownership modifiable;
- les fichiers qu'il evite;
- la passerelle ou le registre ou il laissera sa trace;
- les tests ou preuves attendus;
- le dernier point de coordination lu.
- le lease d'ownership et la prochaine action.

Si ces informations ne sont pas claires, le bot travaille en lecture seule et publie une question de coordination.

## Demarrage obligatoire

Avant toute modification, lire dans cet ordre:

1. `AGENTS.md`;
2. `docs/orchestration_agents.md`;
3. `docs/protocole_roadmap_presence_agents.md`;
4. `docs/tableau_execution_courant.md`;
5. le gouvernail unique `docs/roadmap_backlog_central.md` seulement si le bot
   est l'orchestrateur ou si son slot le cite comme contexte;
6. `docs/presence_agents.md`;
7. le dernier point dans `docs/point_coordination_live_8766_2026-05-21.md`;
8. `docs/coordination_interconversations_2026-05-21.md`;
9. la passerelle du lot: UX, DB, QA, dev ou registre.

Un worker ne choisit jamais son travail dans le gouvernail. Il prend seulement
un slot `A_PRENDRE` publie dans `docs/tableau_execution_courant.md`. S'il n'y
en a pas, il reste en lecture seule et attend l'orchestrateur.

Puis publier ou ajouter dans le livrable un bloc court:

```text
BOT-START - <role> - <heure +02:00>
Roadmap:
Chantier:
Conversation:
Role:
Mission:
Ownership modifiable:
Fichiers a eviter:
Passerelle/registre de trace:
Dernier point lu:
Tests/preuves attendus:
Risque de collision:
Lease ownership:
Prochaine action:
```

## Roadmap, chantier et presence

- Le gouvernail unique des demandes, priorites et imports d'anciens plans est
  `docs/roadmap_backlog_central.md`. Aucun autre document ne fait roadmap.
- Le tableau de travail courant est `docs/tableau_execution_courant.md`. Il ne
  contient pas une deuxieme backlog; il contient seulement les slots de role du
  `CH-*` actif.
- Le registre officiel des conversations et chantiers actifs est
  `docs/presence_agents.md`.
- Les nouveaux chantiers utilisent le format anti-collision
  `CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug-court`. Le format historique
  `CH-YYYY-NNNN` est accepte seulement pour les chantiers deja ouverts.
- Un worktree ou une branche ne prouve pas a lui seul qu'un chantier est actif:
  la ligne `CONV-*` fait foi pour la coordination.
- Si une conversation commence a modifier le depot sans `RM-*`, `CH-*` et
  `CONV-*`, elle cree d'abord les entrees minimales ou reste en lecture seule.
- Le statut `EXPIRE` libere l'ownership seulement apres relecture par le
  coordinateur des traces, diffs et fichiers touches.

## Ownership

- Un fichier sensible a un seul owner a la fois.
- `server/src/coproscope/web/viewmodel.py`, `server/src/coproscope/cli.py`, routes web, schemas vault, registres partages et docs de synthese demandent un owner explicite.
- Un bot qui n'est pas owner propose une note d'integration au lieu de modifier le fichier.
- Les changements hors ownership sont des no-go de coordination, sauf correction minime explicitement demandee par le coordinateur.

## Passerelles

- UX ecrit dans `docs/passerelle_ux_vers_db_2026-05-21.md`.
- DB repond dans `docs/passerelle_db_vers_ux_2026-05-21.md`.
- Le coordinateur consolide dans `docs/coordination_interconversations_2026-05-21.md` et le point live.
- QA et novice ecrivent dans le journal ou le registre de cycle, avec routes reelles et preuves.
- Aucun fil ne reecrit la passerelle d'un autre fil sans demande explicite.

Identifiants recommandes:

- `UXDB-YYYYMMDD-NN` pour une question UX vers DB;
- `DBUX-YYYYMMDD-NN` pour une question DB vers UX;
- `POINT-YYYYMMDD-HHMM` pour un point coordinateur;
- `GO-YYYYMMDD-HHMM` ou `NO-GO-YYYYMMDD-HHMM` pour une decision test.

## Go/no-go

Un bot ne marque pas un bloc comme accepte sans:

- route ou artefact reel livre;
- tests cibles ou justification de non-execution;
- absence de fuite `raw`, `restricted`, `logs`, chemin local et donnee personnelle;
- token conserve sur les routes locales;
- langage comprehensible pour un membre de conseil syndical novice.

## Donnees

- Ne jamais publier de donnees reelles dans Git.
- Les donnees fictives doivent etre marquees `FICTIF` ou `demo`.
- Les chemins locaux absolus, raw/restricted, OCR/logs, emails personnels et pieces jointes brutes restent hors projections publiques.
- Un export passation est un derive, jamais une source de verite.

## Confidentialite conversationnelle

Pour tout audit, contentieux, coproprietaire, AG, travaux sensibles ou document
brut, le bot applique la chaine `fait -> preuve -> regle -> action`.

Regles:

- parler en roles, pieces, periodes, statuts et montants agreges par defaut;
- utiliser des alias stables dans la conversation: `PERS-01`, `CS-01`,
  `SYNDIC-01`, `PREST-01`, `LOT-01`, `PIECE-AG-001`;
- ne garder une identite reelle que si elle est indispensable a une diligence
  concrete, locale et privee;
- ne jamais recopier chemin local, email, telephone, IBAN/RIB, token, secret,
  nom de fichier brut, extrait OCR brut, table de correspondance, log,
  `raw`, `restricted`, `private` ou `file://`;
- distinguer explicitement `constate`, `suppose` et `a verifier`.

Checklist avant rendu final:

- aucune donnee personnelle inutile;
- aucune piece brute ou citation longue de source brute;
- aucune allegation sans source ou reserve;
- chaque diffusion dit `CS seulement`, `a verifier avant partage`, `bloquee`
  ou `diffusable apres controle`;
- si une fuite reste visible, le livrable reste brouillon local et le statut
  doit etre `BLOQUE` ou `EN_ATTENTE_USER`.

## Livrable de fin

Chaque bot termine avec:

```text
BOT-END - <role> - <heure +02:00>
Roadmap:
Chantier:
Conversation:
Statut: PRET_A_INTEGRER | INTEGRE | BLOQUE | EN_ATTENTE_USER | EXPIRE | CLOTURE | ABANDONNE | NOTE_SEULE
Fichiers modifies:
Fichiers volontairement evites:
Tests/preuves:
Limites:
Questions ouvertes:
Prochain mouvement propose:
```

Le `BOT-END` doit etre reporte dans `docs/presence_agents.md` avant de
considerer la conversation fermee.

## Role de la veille

La veille coordination signale:

- un bot qui modifie une passerelle ou un fichier sensible sans ownership visible;
- un point de tests plus recent que le dernier point coordinateur;
- une decision ouverte qui bloque le cycle suivant;
- une divergence entre `tests OK` annonces, routes a tester et go/no-go publie.
