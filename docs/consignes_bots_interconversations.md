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
4. le gouvernail unique `docs/roadmap_backlog_central.md`;
5. `docs/presence_agents.md`;
6. le dernier point dans `docs/point_coordination_live_8766_2026-05-21.md`;
7. `docs/coordination_interconversations_2026-05-21.md`;
8. la passerelle du lot: UX, DB, QA, dev ou registre.

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
- Le registre officiel des conversations et chantiers actifs est
  `docs/presence_agents.md`.
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
