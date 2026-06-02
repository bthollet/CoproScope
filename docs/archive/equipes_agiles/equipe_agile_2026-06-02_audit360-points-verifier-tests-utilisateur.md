# Tests utilisateur Audit360 - Points a verifier

Date: 2026-06-02 12:49 +02:00
Conversation: `CONV-2026-2063`
Chantier: `CH-20260602-122944-RM-2026-0008-audit360-points-verifier`
Roadmap: `RM-2026-0008` / `ORD-P1-110`
Worktree: branche dediee `codex/20260602-audit360-points-tests-utilisateur`

## Decision

NO-GO dev dans ce lot.

La vraie page `Point a verifier` n'existe pas encore. Les ecrans voisins
permettent de lire des signaux, actions ou preuves, mais ils ne permettent pas
a un membre du conseil syndical de transformer clairement un signal Audit360 en
point a verifier complet.

Le resultat est donc renvoye au backlog, sans correction applicative.

## Scenario joue

Un membre du conseil syndical lit un signal issu d'un audit ou d'une revue
documentaire. Il veut noter ce qui est observe, dire quelle preuve manque,
choisir qui valide, limiter la diffusion et lancer une suite humaine. Il ne
veut pas que CoproScope conclue automatiquement.

Routes voisines inspectees:

- `/suggestions`: suggestions sourcees, preuve, revue humaine, destination
  possible.
- `/actions?status=a_verifier`: registre generique des actions et preuves a
  verifier.
- `/pieces?proof=missing`: pieces ou preuves attendues.

## Retours des roles

Organisateur de test:
la vraie route `/audit360/points/{point_id}` manque. Les ecrans voisins sont
utiles pour preparer le dev, pas pour une recette utilisateur complete.

Utilisateur expert-auditeur novice CoproScope:
les bons morceaux existent, mais pas l'entree naturelle `Creer un point a
verifier`. Les mots `Audit360`, `SuggestionOps`, `registre`, `destination` et
`preuve candidate` restent trop internes.

Dev front:
`/actions?status=a_verifier` peut servir de base de lecture, mais modifier
directement `/actions` risquerait de perturber decisions, incidents, demandes
syndic et exports. Une vraie UI Audit360 doit etre dediee.

Dev back/viewmodel:
le stockage et l'import Audit360 existent, mais les donnees sont aplaties en
actions ou pieces attendues. Il manque un contrat public dedie a la fiche
`Point a verifier`.

Designer:
un visuel cible mobile a ete produit pour cadrer l'intention future, sans
pretendre que cette page est livree.

## Captures et visuel

- Capture actuelle desktop: `docs/assets/audit360-points-verifier-20260602/suggestions-current-desktop.png`
- Capture actuelle mobile: `docs/assets/audit360-points-verifier-20260602/suggestions-current-mobile.png`
- Visuel cible mobile: `docs/assets/audit360-points-verifier-20260602/audit360-point-verifier-mobile-target.png`

## Backlog clair

Creer une vraie fiche `Point a verifier`, par exemple
`/audit360/points/{point_id}`, avec:

- fait observe;
- preuve actuelle, si elle existe;
- preuve attendue;
- validateur humain ou role validateur;
- reserve et statut `a verifier`;
- limite de diffusion;
- historique court;
- action suivante: demander une preuve, rattacher une piece, limiter la
  diffusion;
- etat vide avec donnees fictives ou instance de test;
- tests token, anti-fuite, mobile sans tableau horizontal et non-creation
  automatique.

La page doit dire explicitement: `Ce n'est pas une conclusion`.

## Fichiers modifies

- `docs/presence_agents.md`
- `docs/roadmap_backlog_central.md`
- `docs/archive/equipes_agiles/equipe_agile_2026-06-02_audit360-points-verifier-tests-utilisateur.md`
- `docs/assets/audit360-points-verifier-20260602/`

## Fichiers evites

`main`, reconstruction, `/comptes`, factures, dashboard-routes, messages,
instances privees, documents bruts, OCR/logs, secrets, Drive, serveurs
durables, scan/kill et push GitHub.

## Tests et preuves

Preuves produites:

- test utilisateur multi-roles en lecture;
- captures desktop/mobile de `/suggestions` via HTML TestClient local;
- visuel cible mobile genere par IA et archive;
- pas de serveur durable.

Tests applicatifs non lances: aucun code applicatif n'a ete modifie.
