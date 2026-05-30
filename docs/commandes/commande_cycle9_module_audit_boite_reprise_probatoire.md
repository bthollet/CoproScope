# Commande Cycle 9 - Module audit et boite de reprise probatoire

Date de reprise: 2026-05-22.
Rattachement: `RM-2026-0008` / `CH-2026-0009`.
Statut: commande reconstruite depuis `docs/audit360.md`, les schemas Audit360 et la demande "module d'audit"; Cycle 9A technique livre.

## Objectif utilisateur

Permettre a un membre de conseil syndical de transformer des constats epars en une boite de reprise prudente:

- ce qui est constate;
- pourquoi cela compte;
- quelle preuve est attendue;
- quelle action humaine reste a faire;
- quelles limites de diffusion ou de certitude s'appliquent.

Le module ne doit pas juger definitivement, envoyer automatiquement, ni exposer une donnee brute privee. Il prepare une reprise probatoire lisible.

## Briques deja presentes

- Note de cadrage: `docs/audit360.md`.
- Schemas publics:
  - `server/src/coproscope/schemas/audit360_normalized_finding.schema.json`;
  - `server/src/coproscope/schemas/audit360_control_repository_item.schema.json`;
  - `server/src/coproscope/schemas/audit360_control_summary.schema.json`.
- Import technique deja teste: `coproscope.vault.reconstruction.import_audit360_rows`.
- Frontiere publication: `coproscope.core.share.audit_repo` et commande CLI `share-audit`.

## Trou courant

La roadmap pointait vers cette commande Cycle 9, mais le fichier etait absent. Avant tout dev, l'equipe doit donc garder ce document comme source prudente et le corriger si les agents produit, architecture ou QA identifient une meilleure coupe.

## Premier increment candidat

Brancher un lot minimal "reprise Audit360 locale" sans interface lourde:

1. accepter un fichier de lignes Audit360 fictives ou publiques;
2. importer ces lignes dans la reconstruction locale via `import_audit360_rows`;
3. produire un resume JSON/texte avec:
   - nombre de points de controle crees;
   - nombre d'actions creees;
   - nombre de pieces attendues creees;
   - sources importees;
   - limites et avertissements de diffusion;
4. refuser ou masquer toute fuite evidente: chemin local absolu, `raw`, `restricted`, `logs`, `file://`, donnee personnelle non fictive.

Commande technique retenue pour Cycle 9A:

```powershell
.\.venv\Scripts\python.exe -m coproscope.cli vault import-audit360-rows --local-root <local> --sync-root <sync> --path <audit360.csv-or-json>
```

Ce lot ajoute un adaptateur local et une commande CLI. Il ne cree pas encore de route web `/audit/reprise`.

## Criteres d'acceptation produit

- Le vocabulaire visible parle de "constat", "preuve attendue", "action a faire", "limite", pas de verdict juridique ou comptable definitif.
- Chaque action issue de l'audit reste une action humaine a verifier.
- Les donnees de test sont fictives ou publiques.
- La sortie rappelle que le rapport est un derive de reprise, pas une source de verite.
- Un membre CS peut comprendre en moins d'une minute quoi reprendre et quoi demander.

## Criteres QA/securite

- Aucun chemin local absolu dans les sorties.
- Aucun contenu `raw`, `restricted`, `logs` ou `file://` rendu.
- Import idempotent: relancer le meme lot ne double pas les points/actions/pieces.
- Les tests existants `test_vault` autour d'`import_audit360_rows` restent verts.
- Les tests `test_pipeline`, `test_privacy` et `test_invoice_extractors` restent verts pour la frontiere `share-audit`.

## Fichiers a eviter tant que la commande n'est pas stabilisee

- `server/src/coproscope/web/viewmodel.py`;
- routes et templates web, sauf si un blueprint UI dedie est ajoute;
- donnees privees, captures locales, exports bruts, instances `beauvallon_test`.

## Prochain mouvement

Cycle 9A a choisi le lot CLI minimal:

- `server/src/coproscope/modules/audit360.py`: charge CSV/JSON/JSONL, refuse les chemins/tokens/bruts sensibles, puis appelle l'import local existant;
- `vault import-audit360-rows`: expose une sortie prudente sans chemin local;
- `server/tests/test_audit360_import.py`: couvre import CSV, idempotence, refus anti-fuite et sortie CLI sanitisee.

Prochaine tranche possible:

- durcir `share-audit`/`share-export` sur le scan de contenu avant publication large;
- puis seulement ouvrir une fiche web `/audit/reprise?constat=<id>` pour reprendre un constat unique, avec gate navigateur novice.
