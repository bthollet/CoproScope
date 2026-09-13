# Equipe agile - Arborescence instance novice

Date de lancement: 2026-05-24 21:52 +02:00.
Roadmap: `RM-2026-0022`.
Chantier: `CH-20260524-215300-RM-2026-0022-arborescence-instance-novice`.
Conversation coordination: `CONV-2026-1586`.
Mode: cadrage agile sans dev.
Statut: pret a integrer.

## BOT-START

BOT-START - Coordinateur-scribe arborescence instance novice -
2026-05-24 21:52 +02:00.

Mission: transformer `RM-2026-0022` en commande exploitable pour une instance
CoproScope lisible par un novice, avec dossiers visibles simples et dossiers
techniques renvoyes sous `.coproscope/`.

Ownership modifiable: ce document, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`.

Fichiers evites: code applicatif, tests, schemas, instances privees, dossiers
reels, documents bruts, exports, secrets, serveurs, ports locaux et
`RM-2026-0017`.

## Roles

| Role | Conversation | Statut | Sortie |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1586` | `PRET_A_INTEGRER` | Commande consolidee et traces gouvernail. |
| Designer service | `CONV-2026-1587` | `CLOTURE` | Structure visible cible et vocabulaire novice. |
| Utilisateur novice | `CONV-2026-1588` | `CLOTURE` | GO conditionnel sur dossiers simples, NO-GO sur noms techniques visibles. |
| Dev filesystem lecture | `CONV-2026-1589` | `CLOTURE` | Contrat futur et points d'integration sans patch. |
| QA privacy / migration | `CONV-2026-1590` | `CLOTURE` | Gates non destructifs, anti-fuite et rollback. |

## Decision Produit

Commande future: `instance_layout_novice_v1`.

Objectif: l'utilisateur voit des dossiers metier stables; CoproScope garde ses
index, registres, caches et journaux dans `.coproscope/`. Les dossiers visibles
ne deviennent pas la source de verite: le `doc_id` et le hash restent les
ancres techniques.

Structure visible recommandee pour une nouvelle instance:

```text
01 - Deposez les nouveaux fichiers ici/
02 - Documents classes/
03 - Rapports et exports/
04 - A verifier/
README - utiliser cette instance.md
.coproscope/
```

Structure interne recommandee sous `.coproscope/`:

```text
.coproscope/config/
.coproscope/registers/
.coproscope/cache/
.coproscope/generated/
.coproscope/logs/
.coproscope/migrations/
```

Regles:

- pas de deplacement automatique destructif dans ce cycle;
- pas de renommage d'instances existantes sans plan sec et rollback;
- pas de symlink, jonction Windows ou dossier magique requis pour le novice;
- pas de chemin absolu visible dans UI, exports ou rapports;
- les dossiers techniques restent lisibles par l'outil mais non presentes comme
  etapes utilisateur;
- l'inbox visible reste un point d'entree, pas une zone de stockage canonique.

## Commande Dev Future

Owner futur unique, dans un worktree propre:

- etendre `settings.layout` avec `mode: novice_v1`;
- ajouter une commande de planification type `coprocs instance layout plan`,
  sortie dry-run uniquement;
- ajouter ensuite une commande appliquee seulement avec confirmation explicite,
  journal de migration et rollback;
- adapter `doctor` pour signaler les ecarts sans deplacer de fichiers;
- garder la compatibilite avec les instances legacy;
- tester uniquement sur instances synthetiques ou temporaires.

Fichiers candidats a owner futur:

- `server/src/coproscope/core/_common_parts/01_io_and_instance_config.py`;
- `server/src/coproscope/core/doctor.py`;
- `server/src/coproscope/schemas/instance.schema.json`;
- `server/src/coproscope/modules/_docuscope_parts/01_inventory_and_extraction.py`;
- tests de layout instance dedies.

## Gates QA

- dry-run obligatoire avant toute migration;
- manifeste avant/apres avec hash et `doc_id`;
- rollback documente et teste;
- aucun contenu brut, nom reel, chemin absolu, secret ou export prive dans les
  traces;
- tests sur instance fictive et repertoire temporaire;
- le scan par hash doit tolerer les deplacements utilisateur;
- les anciens chemins restent supportes au moins en lecture.

## Verdict

`GO_CADRAGE`, `NO_GO_DEV_IMMEDIAT` dans le worktree principal sale.

Prochain mouvement: ouvrir un chantier dev separe seulement si cette commande
devient prioritaire apres les lots P0 deja prets a integrer. Aucun serveur,
instance privee, secret, export brut ou `RM-2026-0017` n'a ete utilise.

AGILE-DONE - equipe agile a fini son job

## Journal

| Heure | Acteur | Evenement | Detail |
|---|---|---|---|
| 2026-05-24 21:52 +02:00 | `CONV-2026-1586`..`CONV-2026-1590` | `START_AND_DONE` | Cycle agile documentaire consolide localement apres renumerotation anti-collision: structure novice, `.coproscope/`, contrat futur, gates migration et no-go dev immediat; aucun code, serveur, instance privee, secret, export brut ni `RM-2026-0017`. |
