# Equipe agile - Messages recus - tests utilisateur

Date: 2026-06-02 11:12 +02:00.

## BOT-START

Roadmap: `RM-2026-0031` / `ORD-P1-040`.
Chantier: `CH-20260602-111251-RM-2026-0031-messages-tests-utilisateur`.
Conversation: `CONV-2026-2059`.
Worktree: `C:\Users\brice\CoproScope\dev\worktrees\coproscope-messages-tests-utilisateur-20260602`.
Branche: `codex/20260602-messages-tests-utilisateur`.

Brice a leve le `blocked` pour les tests utilisateur hors reconstruction. Le lot reste hors reconstruction, hors cockpit, hors `/comptes`, hors Zotero, sans donnees Beauvallon privees, sans serveur durable et sans push.

## Anti-doublon

Controle avant edition produit:

- `main` propre.
- Worktree courant: seule modification initiale = presence du lot.
- Aucune ligne vivante concurrente trouvee sur `Messages recus` dans le registre courant.
- `main` a avance de `4b9331b` a `8d2ed72`, sans diff sur `messages_entrants_view.py`, `messages_entrants.html`, `styles_part_19.css` ou `test_ui_messages_entrants.py`.
- Un autre fil avait produit un visuel exploratoire, mais aucune presence active ni ownership produit concurrent n'a ete detecte.

## Routage equipe

Equipe-type: `AGILE_UI_PRODUIT`.
Orchestration: pipeline decale.
UI reelle: route tokenisee `/messages/entrants`.
Owner code unique: fil pilote `CONV-2026-2059`.

Roles rendus:

- Designer/facilitateur: lecture seule, blueprint cible et prompt IA.
- Utilisateur expert-auditeur novice: lecture seule, verdict de comprehension.
- QA privacy/regression: lecture seule, panier de tests et risques.
- Dev front/back: fil pilote seulement, correction courte apres commande.

## Visuel IA

Mode: imagegen integre.
Chemin retenu: `docs/assets/ux-cibles-2026-06-02-messages/messages-recues-cible-ia.png`.

Intention: page complete, dense et lisible, avec liste de messages a gauche, detail du message a droite, et avertissement visible: rien n'est envoye depuis CoproScope.

Verdict novice sur la cible: GO comme direction de correction, car elle montre la priorite, le detail, la preuve attendue, la diffusion et les actions bloquees sans laisser croire a un envoi.

## Blueprint cible

Objectif: transformer la page en file de tri humaine, pas en tableau technique.

Structure cible:

1. Bandeau haut clair: demonstration locale, aucun vrai message lu, aucune reponse ni publication.
2. Trois compteurs courts: messages a verifier, sensibles, preuves attendues.
3. Liste priorisee de messages fictifs: sujet, raison, statut, preuve, partage.
4. Detail du message selectionne: resume prudent, origine sans nom, preuve attendue, qui peut lire, suite humaine.
5. Decisions avant action: lire, verifier preuve, choisir qui peut voir, noter la suite.
6. Actions sensibles en cartes non cliquables: reponse automatique, publication et compte exterieur restent bloquees.

## Verdict utilisateur actuel

NO-GO comprehension en 30 secondes.

Raisons:

- `Qualifier maintenant` descend dans la page mais ressemble a une action.
- Les boutons `Disponible` semblent actifs alors qu'aucune suite produit n'est branchee.
- Mots trop techniques: `Source rolee`, `Moderation`, `Diffusion`, `Cloture`, `journal de diligence`, `connecteur`, `qualification`.
- Sur mobile, le tableau empile les valeurs sans libelle visible.

## Commande dev courte

Modifier uniquement:

- `server/src/coproscope/web/messages_entrants_view.py`
- `server/src/coproscope/web/templates/messages_entrants.html`
- `server/src/coproscope/web/static/styles_part_19.css`
- `server/tests/test_ui_messages_entrants.py`

Changements attendus:

- Remplacer les termes techniques par des mots simples.
- Remplacer les boutons d'action par des cartes non cliquables.
- Ajouter une fiche detail pour le message prioritaire.
- Sur mobile, afficher les libelles de chaque champ au lieu d'empiler des valeurs anonymes.
- Renforcer les tests: actions sensibles bloquees, anti-fuite, token, texte clair.

Fichiers evites: `main`, reconstruction, cockpit, `/comptes`, Zotero, incidents integre, instances privees, Drive, documents bruts, OCR/logs, secrets, serveurs durables, scan/kill et push GitHub.

## Tests attendus

Depuis `server/`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONPATH='src'
python -B -m unittest tests.test_ui_messages_entrants tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v
```

Depuis la racine du worktree:

```powershell
python -B tools\check_code_line_limit.py
git diff --check
```

Preuve visuelle attendue: capture desktop et mobile sur HTML rendu a partir de donnees synthetiques, sans serveur durable.

## BOT-END

Heure: 2026-06-02 11:35 +02:00.

Statut: `PRET_A_INTEGRER`.

Corrections livrees:

- `/messages/entrants` parle maintenant de `Messages recus a traiter`, `Qui parle, sans nom`, `Preuve attendue`, `Qui peut lire`, `Suite humaine`.
- Le grand tableau est remplace par une liste de cartes et une fiche detail du message prioritaire.
- Les actions ne sont plus des boutons trompeurs: elles deviennent des cartes d'etat non cliquables.
- Les suites sensibles restent explicitement bloquees: reponse automatique, publication et compte exterieur.
- La page cache la recherche globale et le bouton `Nouvelle demande` sur cette route, car ils ne sont pas branches au flux Messages.
- Le mobile garde des libelles champ par champ et une navigation de page moins large.

Fichiers modifies:

- `docs/presence_agents.md`
- `docs/archive/equipes_agiles/equipe_agile_2026-06-02_messages-tests-utilisateur-protocole.md`
- `docs/assets/ux-cibles-2026-06-02-messages/`
- `server/src/coproscope/web/messages_entrants_view.py`
- `server/src/coproscope/web/templates/messages_entrants.html`
- `server/src/coproscope/web/static/styles_part_19.css`
- `server/tests/test_ui_messages_entrants.py`

Fichiers volontairement evites: `main`, reconstruction, cockpit, `/comptes`, Zotero, incidents integre, instances privees, documents bruts, OCR/logs, secrets, Drive, serveurs durables, scan/kill et push GitHub.

Preuves:

- Visuel IA cible: `docs/assets/ux-cibles-2026-06-02-messages/messages-recues-cible-ia.png`.
- HTML de recette synthetique: `docs/assets/ux-cibles-2026-06-02-messages/messages-recues-livraison.html`.
- Capture desktop: `docs/assets/ux-cibles-2026-06-02-messages/messages-recues-livraison-desktop.png`.
- Capture mobile: `docs/assets/ux-cibles-2026-06-02-messages/messages-recues-livraison-mobile.png`.
- `python -B -m unittest tests.test_ui_messages_entrants tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v`: 23 tests OK.
- `python -B tools\check_code_line_limit.py`: OK.
- `git diff --check`: OK.

Limites:

- Aucun serveur durable n'a ete lance.
- Captures faites via Edge headless sur HTML local synthetique, pas via serveur live reserve.
- Aucune vraie boite mail, aucun connecteur et aucun vrai message ne sont branches.

Question ouverte: les actions `Lire`, `Rattacher une preuve`, `Noter la suite humaine` restent a construire comme vraies interactions dans un futur lot dedie, avec validation humaine et anti-fuite.
