# Equipe agile - Coffre et partage

Date de lancement: 2026-05-24 20:10 +02:00.
Roadmap: `RM-2026-0033`.
Chantier: `CH-20260524-201048-RM-2026-0033-coffre-partage-agile`.
Conversation coordination: `CONV-2026-1540`.
Mode: equipe agile gouvernail, cadrage UI reelle avant dev.
Statut: pret a integrer - no-go dev immediat.

## BOT-START

BOT-START - Coordinateur-scribe agile - 2026-05-24 20:10 +02:00

Roadmap: `RM-2026-0033`.
Chantier: `CH-20260524-201048-RM-2026-0033-coffre-partage-agile`.
Conversation: `CONV-2026-1540`.
Role: Coordinateur-scribe agile.
Mission: lancer une equipe agile guidee par le gouvernail sur le prochain P0 exploitable, l'ecran `Coffre et partage`, pour transformer la recherche UX/UI cloturee en commande UI/dev verifiable sans demarrer de patch tant que la cible UI, le blueprint, la qualification novice, le contrat front/back et le panier QA ne sont pas stabilises.
Ownership modifiable: ce document, `docs/presence_agents.md`, ligne gouvernail `RM-2026-0033`.
Fichiers a eviter: code applicatif, routes, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, serveurs locaux, donnees reelles, `RM-2026-0017` bloque et le serveur UI local `CONV-2026-1525`.
Passerelle/registre de trace: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/orchestration_agents.md`, `docs/protocole_equipe_agile_agents.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/consignes_bots_interconversations.md`, `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`, `docs/recherche_ux_ui_2026-05-24_comptes-sync-collaboration_approfondissement.md` au 2026-05-24 20:10 +02:00.
Tests/preuves attendus: point court, cible UI nommee, comparaison au blueprint, GO/NO-GO novice, cartographie front/back, panier QA anti-fuite; aucun test applicatif tant que le dev n'est pas ouvert.
Risque de collision: `CONV-2026-1519` reste bloque sur ajout-docs/tri-feedback; `CONV-2026-1526`..`1531` sont clos ou prets sur compta; `CONV-2026-1532`..`1537` viennent d'etre pris par un verrouillage compta; `CONV-2026-1525` garde un serveur local; cette vague reserve `CONV-2026-1540`..`1545`.
Lease ownership: 2026-05-24 22:10 +02:00.
Prochaine action: lancer cinq roles en lecture seule et recadrer la heartbeat 10 minutes.

## Choix Gouvernail

Le lot P0 `RM-2026-0003` / `RM-2026-0029` reste bloque par collision de
worktree. La vague compta `RM-2026-0030` est deja reprise par un verrouillage
dedie sur `CONV-2026-1532`..`1537`. Le prochain P0 exploitable est donc
`RM-2026-0033`, avec une recherche UX/UI cloturee et un blueprint retenu.

## UI Cible

- Ecran cible: `Coffre et partage`.
- Route candidate a confirmer par cartographie: `/coffre/partage`.
- Blueprint de reference:
  `docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration-approfondissement/01-coffre-et-partage-approfondissement.svg`.
- Source UX/UI:
  `docs/recherche_ux_ui_2026-05-24_comptes-sync-collaboration_approfondissement.md`.

Si la route candidate n'existe pas, le premier objectif futur sera de rendre une
UI minimale testable sur donnees fictives ou demo. Aucun dev ne demarre dans
cette vague tant que les roles n'ont pas stabilise la commande.

## Roles

| Role | Conversation | Statut | Ownership |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1540` | `PRET_A_INTEGRER` | Registres, synthese et arbitrage; equipe cloturee. |
| Designer service / facilitateur | `CONV-2026-1541` | `CLOTURE` | Agent fork Laplace `019e5b32-4e4c-70a0-8ffb-70acef18b465`; retour integre; aucun fichier modifie. |
| Utilisateur novice / representant CS | `CONV-2026-1542` | `CLOTURE` | Agent fork Hypatia `019e5b32-50c6-7d91-9cfa-a7e75deac206`; GO novice conditionnel integre; aucun fichier modifie. |
| Dev front lecture | `CONV-2026-1543` | `CLOTURE` | Agent fork Dewey `019e5b32-5160-7b62-8880-4dd0a6741253`; cartographie front integree; aucun fichier modifie. |
| Dev back / viewmodel lecture | `CONV-2026-1544` | `CLOTURE` | Agent fork Aquinas `019e5b32-5273-7cc2-a25a-533f8f93759c`; contrat model/viewmodel integre; aucun fichier modifie. |
| QA privacy / regression | `CONV-2026-1545` | `CLOTURE` | Agent fork Socrates `019e5b32-53aa-7070-a002-c6c374e068c4`; panier QA integre; aucun fichier modifie. |

## Point Court Initial

A tester maintenant: rien en UI live; la vague stabilise d'abord la commande et
les risques.

En dev maintenant: rien. Les devs sont en lecture.

En enquete maintenant: comparer `Coffre et partage` au blueprint retenu et a la
recherche UX/UI.

Commande prete: oui cote cadrage. Elle contient cible UI, structure, contrat
donnees, interactions bloquees, etats critiques, criteres d'acceptation et
tests; le dev reste hors de cette vague.

Comparaison visuels enquete: obligatoire sur le blueprint `01-coffre-et-partage-approfondissement.svg`.

Agents idle a relancer: aucun; tous les roles sont clotures.

Decision requise: ouvrir ou non un chantier dev separe avec owner unique et
worktree propre.

Prochain mouvement: ouvrir un chantier dev separe seulement si Brice valide la
commande, un owner code unique et un worktree propre.

Tests/preuves: `git diff --check` sur docs apres lancement; pas de test
applicatif tant qu'aucun code n'est touche.

## Retours Consolides Partiels

### Designer service / facilitateur

Commande UI proposee: construire l'ecran `Coffre et partage`, route candidate
`/coffre/partage`, a partir du blueprint
`01-coffre-et-partage-approfondissement.svg`. Si la route n'existe pas, livrer
d'abord une UI minimale testable sur donnees fictives, token-gated, sans action
reelle d'invitation ou d'export.

Structure retenue: en-tete `Coffre et partage` avec statut de verification et
CTA `Verifier avant partage`; bloc modele mental `Coffre local`, `Transport
chiffre`, `Personnes`, `Postes autorises`, `Referent de secours`; bloc central
`Avant de partager`; actions bloquees ou de relecture; liste personnes avec
capacites visibles; etats sensibles; pied de preuve `qui, quand, poste, effet,
limites`.

Comparaison blueprint: conserver titre, priorite a la verification, invitation
bloquee, modele mental, retrait honnete, droit sensible, referent de secours et
trace minimale. Accepter une pile mobile a la place des trois colonnes. Refuser
un renommage generique `Comptes`, un premier niveau Drive/sync/admin, une
invitation active avant verification ou une promesse d'effacement des copies
deja obtenues. Reporter le detail complet recuperation/contestation/durees.

No-go designer: pas de dev si le novice n'a pas valide les libelles, si le
contrat `model.ux.coffre_partage` n'est pas borne, si QA n'a pas liste les
tests anti-fuite/token/conflit/retrait/recuperation/responsive, ou si le dev
doit inventer les promesses produit.

### Utilisateur novice / representant CS

GO novice conditionnel: la direction est comprehensible si le premier ecran
explique en moins de 30 secondes le coffre local, le transport chiffre, les
droits concrets, le referent de secours, l'invitation bloquee avant verification
et les limites du retrait.

Libelles compris: `Coffre et partage`, `Verifier avant partage`, `Relire
droits`, `Referent de secours`, `Lire`, `Ajouter`, `Valider`, `Exporter`, `Peut
gerer les acces`, `Droit sensible`, `Deux versions du coffre existent`.

Libelles a retravailler: `Coffre local` et `fait foi ici` doivent preciser le
lieu de reference; `Transport chiffre` reste technique; preferer `Invitation
bloquee` a `Inviter bloque`; remplacer ou expliquer `Poste autorise` par
`ordinateur reconnu`.

Actions sensibles a proteger: inviter, gerer les acces, exporter, retirer un
acces, autoriser un poste, choisir la version de reference, demander ou valider
une recuperation. Risques: croire que le retrait efface les copies, que le
cloud decide les droits, confondre personne/compte/poste, donner trop vite
`Peut gerer les acces`, ou resoudre un conflit sans comprendre l'effet.

Conditions minimales avant dev: route cible confirmee, premier ecran centre sur
verification avant partage, invitation desactivee tant que coffre non verifie,
microcopy novice validee, etats critiques prevus, aucun role `admin`, aucune
promesse d'effacement retroactif, donnees fictives uniquement, contrat
`model.ux.*` defini, panier QA pret.

### QA privacy / regression

Panier QA prioritaire: anti-fuite, token, droits, recuperation, invitation,
revocation, conflit de version, exports/Drive chiffre et test novice.

Scenarios bloquants: aucun document lisible, secret, export brut, OCR, chemin
local prive ou donnee reelle ne doit sortir vers Drive, logs, DOM, traces,
erreurs ou exports. Les invitations sont bloquees si coffre non verifie,
contenu lisible detecte, poste inconnu ou conflit. Les tokens ne doivent pas
etre persistants en clair dans UI, logs, URL, exports ou stockage navigateur.

Matrice droits: `Lire`, `Ajouter`, `Valider`, `Exporter`, `Peut gerer les
acces`, independants, sans role `admin` global. `Peut gerer les acces` ne donne
ni mandat juridique, ni recuperation seule, ni pouvoir absolu de retirer tout
le monde.

Etats a tester: recuperation avec motif et validation visible, invitation en
brouillon puis envoi bloque jusqu'a relecture, revocation honnete, conflit de
version bloquant validation/invitation/export, Drive comme transport chiffre
uniquement, fichier corrompu, mauvaise cle, nom de fichier trop revelateur,
lien Drive partage sans droits CoproScope.

No-go QA immediat: refuser l'UI si elle affiche d'abord `sync`, `vault`,
`OAuth`, `scope`, `token`, `admin` ou `device`, ou si elle permet
d'inviter/exporter pendant un etat non verifie, un conflit de version, une
recuperation contestee ou une detection de contenu lisible cote Drive.

### Dev front lecture

Cartographie front: l'app web est FastAPI + Jinja. `app.py` charge des
fragments via `source_fragments.py`. Les routes HTML principales sont dans
`server/src/coproscope/web/_app_fragments/part_003.pyfrag`; la route
`/coffre/partage` n'existe pas et tomberait aujourd'hui sur le catch-all 404 de
`part_004.pyfrag`.

Candidats d'implementation future: enregistrer `GET /coffre/partage` avant le
catch-all; garder une route tres courte dans le fragment coordonne; isoler la
construction dans `server/src/coproscope/web/coffre_partage_view.py`; creer
`server/src/coproscope/web/templates/coffre_partage.html`; rattacher la
navigation via `base.html` cote `Parametres` ou nouvelle section `Coffre`.

CSS: reutiliser `.band`, `.grid.two`, `.panel`, `.module-grid`, `.badge`. Si un
style specifique est necessaire, preferer un nouveau `styles_part_13.css`
importe par `styles.css` plutot que grossir les parts existantes.

Contraintes 600 lignes: `part_003.pyfrag` est proche du plafond avec 544
lignes; ne pas y ajouter lourdement. Autres fichiers proches signales:
`workstreams.html` 526 lignes et `document_intake_view.py` 516 lignes.

Collisions a surveiller avant tout chantier dev: nombreux fichiers sales; pour
ce chantier, surveiller surtout `part_001.pyfrag`, `part_003.pyfrag`,
`part_004.pyfrag`, `base.html`, `styles_part_12.css`,
`document_intake_view.py`, `depot.py`, plusieurs tests UI, et fichiers non
suivis proches du routing/intake. Garder `CONV-2026-1525` serveur local et
`RM-2026-0017` hors perimetre.

Ownership recommande: front = route courte, template, navigation, CSS et tests
UI/smoke; back/viewmodel = contrat `coffre_partage_view` si donnees au-dela de
`context_banner`, `governance`, privacy ou memoire; QA = matrice token/no-leak
et checks novice.

Tests probables: ajouter `/coffre/partage` dans
`server/tests/test_ui_smoke_routes_expanded.py`; verifier la route token-gated
dans `server/tests/test_security_no_private_sync_leaks.py`; creer un test
dedie `server/tests/test_ui_coffre_partage.py` pour 200/403, texte `Coffre et
partage`, partage bloque et absence de chemin prive; inclure le template dans
`server/tests/test_ui_accessibility_language.py`.

### Dev back / viewmodel lecture

Contrat model/viewmodel recommande:

- `coffre`: identifiant opaque, libelle, role visible, niveau d'acces, derniere
  verification;
- `etat`: coffre local, transport chiffre, verification avant partage, conflit,
  blocage;
- `membres`: identifiant opaque, nom fictif ou sur, statut, droits separes
  `lire`, `ajouter`, `valider`, `exporter`, `gerer_acces`, portee et expiration;
- `invitations`, `revocations`, `recuperation`, `audit_trail` et `actions`
  avec `enabled` et `disabled_reason`.

Donnees fictives minimales: un acces actif, une invitation bloquee, un acces
revoque, un referent de secours, un conflit de version et deux lignes d'audit.
Ne pas exposer email reel, chemin local, token, blob id, hash complet, nom de
fichier prive, payload, log, OCR brut ou secret.

Route future: `GET /coffre/partage` comme ecran dedie, avec viewmodel separe.
Les actions d'invitation, export, gestion d'acces, recuperation et revocation
restent bloquees tant que les gates securite et persistance ne sont pas fixes.

Tests back attendus: rendu sans marqueurs prives, etats coffre absent/local
seul/transport non verifie/verifie/conflit/incident, droits separes sans acces
contenu implicite, anti-fuite chemins/tokens/cles/payloads/emails, revocation,
reconstruction locale, incident sync et recuperation avec quorum au moins deux.

No-go back: pas de vraie invitation, revocation, recuperation, export ou
persistance tant que le contrat securite, les regles de persistance et les
tests anti-fuite ne sont pas verrouilles.

## Decision Consolidee

Verdict: equipe agile cloturee en cadrage. Direction retenue:
`Coffre et partage` sur route future `/coffre/partage`, avec donnees fictives,
partage bloque avant verification, droits separes et preuve honnete des limites.

GO novice: conditionnel. Le modele est compris si le premier ecran explique le
coffre local, le transport chiffre, les droits concrets, le referent de secours
et les limites du retrait sans jargon technique.

NO-GO dev immediat: aucun patch dans ce run. Le futur chantier dev doit avoir
un owner unique, un worktree propre, une route courte avant le catch-all, un
builder `coffre_partage_view.py`, un template dedie, un panier anti-fuite et des
donnees synthetiques.

A produire avant dev: commande dev courte, contrat `model.ux.coffre_partage`,
etat des actions desactivees, tests `test_ui_coffre_partage.py`, smoke route,
anti-fuite et accessibilite.

AGILE-DONE - equipe agile a fini son job

## BOT-END

BOT-END - Coordinateur-scribe agile - 2026-05-24 20:25 +02:00

Roadmap: `RM-2026-0033`.
Chantier: `CH-20260524-201048-RM-2026-0033-coffre-partage-agile`.
Conversation: `CONV-2026-1540`.
Statut: PRET_A_INTEGRER.
Livrable: commande UI/dev de cadrage pour `Coffre et partage`, GO novice
conditionnel, cartographie front, contrat back/viewmodel, panier QA anti-fuite
et no-go dev immediat.
Fichiers modifies: `docs/equipe_agile_2026-05-24_coffre-partage.md`,
`docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers evites: code applicatif, tests applicatifs, serveurs, instances
privees, secrets, exports bruts, donnees reelles, `RM-2026-0017` et serveur
local `CONV-2026-1525`.
Preuves: cinq roles lances et consolides; aucun agent n'a modifie de fichier;
`git diff --check` documentaire OK.

## Journal

| Heure | Conversation | Evenement | Note |
|---|---|---|---|
| 2026-05-24 20:10 +02:00 | `CONV-2026-1540` | `BOT-START` | Vague agile gouvernail ouverte sur `RM-2026-0033`; code, serveur, instance privee, `RM-2026-0017` et chantiers concurrents evites. |
| 2026-05-24 20:14 +02:00 | `relance-equipe-agile-gouvernail-2` | `AUTOMATION_UPDATE` | Heartbeat active toutes les 10 minutes sur `RM-2026-0033` / `CH-20260524-201048-RM-2026-0033-coffre-partage-agile`; stop sur marqueur `AGILE-DONE - equipe agile a fini son job`; aucune reprise de `RM-2026-0017`, ajout-docs bloque, compta vivante, serveur local ou instance privee. |
| 2026-05-24 20:14 +02:00 | `CONV-2026-1541`..`CONV-2026-1545` | `AGENTS_LAUNCHED` | Agents Laplace, Hypatia, Dewey, Aquinas et Socrates lances en lecture seule; aucun code, serveur, instance privee ou donnee reelle. |
| 2026-05-24 20:15 +02:00 | `CONV-2026-1541`, `CONV-2026-1542`, `CONV-2026-1545` | `PARTIAL_RETURNS_INTEGRATED` | Designer, novice et QA integres; GO novice conditionnel, commande UI et panier QA disponibles; front/back restent en cours. |
| 2026-05-24 20:16 +02:00 | hors registre canonique | `DUPLICATE_AGENTS_CLOSED` | Doublons Heisenberg, Raman, Beauvoir, Kierkegaard et Hegel fermes sans integration canonique; les seuls roles vivants restent Laplace, Hypatia, Dewey, Aquinas et Socrates. |
| 2026-05-24 20:21 +02:00 | `CONV-2026-1543` | `FRONT_RETURN_INTEGRATED` | Cartographie front integree: `/coffre/partage` absente, route a brancher avant catch-all, builder/template dedies recommandes, `part_003.pyfrag` proche plafond; Aquinas reste en cours. |
| 2026-05-24 20:24 +02:00 | `CONV-2026-1544` | `BACK_RETURN_INTEGRATED` | Contrat model/viewmodel, donnees fictives, risques backend et tests back integres; aucun code, serveur ou instance privee. |
| 2026-05-24 20:24 +02:00 | `CONV-2026-1540`..`CONV-2026-1545` | `AGILE_DONE` | Equipe cloturee: commande UI/dev cadrage prete, GO novice conditionnel, no-go dev immediat, prochain geste = chantier dev separe si Brice valide. |
| 2026-05-24 20:23 +02:00 | `CONV-2026-1540` | `USER_RELANCE_CONFIRMED` | Nouvelle demande de lancement/relance: equipe deja vivante, heartbeat 10 minutes active, aucun role duplique; attente du retour back/viewmodel `CONV-2026-1544`. |
| 2026-05-24 20:25 +02:00 | `CONV-2026-1540` | `FINAL_RECONCILE` | Le retour back/viewmodel est desormais integre; la ligne `USER_RELANCE_CONFIRMED` est depassee par `AGILE_DONE`; heartbeat supprimee. |
| 2026-05-24 20:25 +02:00 | `relance-equipe-agile-gouvernail-2` | `AUTOMATION_DELETE_NOT_FOUND` | Suppression verifiee apres marqueur `AGILE-DONE`: l'app repond `not_found`, donc aucune heartbeat vivante ne reste pour cette vague. |
