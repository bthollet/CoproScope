# Recherche UX/UI - relance alertes et sollicitations coproprietaires

Date: 2026-05-24 09:25 +02:00.
Roadmap: `RM-2026-0031`.
Chantier: `CH-20260524-092539-RM-2026-0031-alertes-sollicitations-relance`.
Conversation coordinatrice: `CONV-2026-1380`.

## BOT-START - Orchestrateur UX/UI - 2026-05-24 09:25 +02:00

Roadmap: `RM-2026-0031`
Chantier: `CH-20260524-092539-RM-2026-0031-alertes-sollicitations-relance`
Conversation: `CONV-2026-1380`
Role: Orchestrateur UX/UI
Mission: relancer une iteration UX/UI sans dev sur les alertes et sollicitations coproprietaires entrantes, a partir du livrable deja cloture `docs/recherche_ux_ui_2026-05-24_alertes-sollicitations-copro.md`.
Ownership modifiable: ce livrable, le dossier `docs/assets/ux-ui-recherche-2026-05-24-alertes-sollicitations-copro-relance/`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers a eviter: code applicatif, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, serveurs locaux, `RM-2026-0017` bloque.
Passerelle/registre de trace: ce livrable, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `docs/point_coordination_live_8766_2026-05-21.md` et `docs/coordination_interconversations_2026-05-21.md` relus le 2026-05-24 09:25 +02:00.
Tests/preuves attendus: pas de test applicatif; preuve attendue = synthese UX/UI, retours des roles, images candidates ou justification d'absence d'image, decisions ouvertes, et marqueur final `UXUI-DONE`.
Risque de collision: equipes UX/UI vivantes sur `RM-2026-0024` et `RM-2026-0033`; cette relance est bornee a `RM-2026-0031` et ne doit pas les dupliquer.
Lease ownership: 2026-05-25 09:25 +02:00.
Prochaine action: lancer les cinq roles lecture seule, consolider leurs sorties, puis cloturer ou relancer selon le marqueur final.

## Objectif de la relance

La premiere recherche a retenu la direction `Messages recus des coproprietaires`: inbox priorisee, panneau de qualification, gates mandat/privacy/preuve/moderation et historique en second niveau.

Cette relance doit pousser le cadrage UX/UI avant tout chantier dev:

- verifier si l'inbox priorisee est encore le meilleur premier ecran;
- clarifier la qualification humaine d'une sollicitation entrante;
- distinguer alerte, demande, signalement, piece recue, reponse syndic et message sensible;
- tester la comprehension novice des termes et des priorites;
- produire une direction visuelle ou un blueprint de decision si utile;
- lister les arbitrages que Brice doit trancher avant dev.

## Roles relances

| Conversation | Role | Mission |
|---|---|---|
| `CONV-2026-1381` | Chercheur utilisateur | Reprendre profils, besoins, irritants et situations d'usage des coproprietaires entrants. |
| `CONV-2026-1382` | Architecte UX | Structurer parcours, etats, tri, qualification et transitions de l'inbox. |
| `CONV-2026-1383` | Designer UI / generateur visuel | Proposer direction UI, prompts et images/blueprints candidats. |
| `CONV-2026-1384` | Testeur metier expert | Challenger mandat, moderation, responsabilite, preuve, diffusion et cas sensibles. |
| `CONV-2026-1385` | Testeur accessibilite / novice | Tester comprehension immediate, jargon, charge cognitive et risque d'action dangereuse. |

## Sources de depart

- `docs/recherche_ux_ui_2026-05-24_alertes-sollicitations-copro.md`
- `docs/assets/ux-ui-recherche-2026-05-24-alertes-sollicitations-copro/blueprint_entrees_coproprietaires.svg`
- `docs/roadmap_backlog_central.md`
- `docs/presence_agents.md`

## Point court initial

A produire: sorties des cinq roles, convergence, eventuelles images candidates, decisions ouvertes et marqueur final.

En test: rien en applicatif; test UX par relecture metier et novice.

Images candidates: a produire ou a justifier; dossier cible `docs/assets/ux-ui-recherche-2026-05-24-alertes-sollicitations-copro-relance/`.

Decisions ouvertes: MVP confirme ou non, vocabulaire `Messages recus`, niveau de priorisation automatique, regles de diffusion, emplacement de l'historique, statut des brouillons/reponses.

Prochain mouvement: lancer les roles en lecture seule et consolider.

## Trace de renumerotation

Collision detectee apres lancement: `CONV-2026-1374`..`CONV-2026-1379` ont aussi ete utilises par une autre relance UX/UI sur `RM-2026-0003`. La relance alertes/sollicitations est donc fixee en `CONV-2026-1380`..`CONV-2026-1385` sans modifier les sorties agents deja recues.

## Sorties des roles

### Chercheur utilisateur - `CONV-2026-1381`

Verdict: le MVP `Messages recus des coproprietaires` couvre les vrais cas si son role reste strict: recevoir, qualifier, rattacher, preparer une suite humaine et tracer. Il ne doit pas devenir une messagerie generale ni un outil d'envoi officiel.

Scenarios prioritaires: alerte, demande, signalement, piece recue, reponse syndic, message sensible, hors mandat, urgence.

Recommandation: garder `Messages recus des coproprietaires`, afficher une raison d'attention lisible au lieu d'une priorite brute, imposer un choix de nature avant toute suite engageante, mettre l'historique en second niveau et exclure en MVP tout envoi automatique, connecteur mail/LRAR ou vue coproprietaire large.

### Architecte UX - `CONV-2026-1382`

Position UX: le MVP reste valide, mais il doit etre cadre comme une boite de traitement, pas comme une messagerie.

Wireflow retenu: arrivee message, tri/priorite, qualification humaine, rattachement, moderation/diffusion, brouillon de reponse, historique secondaire.

No-go UX: envoi/diffusion sans validation humaine, message nominatif diffusable en un clic, priorite rouge sans raison concrete, cloture sans motif ou trace, historique comme ecran principal.

### Designer UI / generateur visuel - `CONV-2026-1383`

Direction recommandee: comparer deux directions, mais privilegier comme hypothese principale une `file de qualification` plutot qu'une simple inbox priorisee.

Composition cible: file compacte a gauche, panneau `Comprendre et classer` au centre avec cinq decisions obligatoires, zone `Suite humaine` a droite separant preuve, diffusion, brouillon, rattachement et journal.

### Testeur metier expert - `CONV-2026-1384`

Verdict: GO conditionnel pour poursuivre le cadrage UX/UI; NO-GO dev tant que les garde-fous mandat, moderation, diffusion, preuve et brouillon ne sont pas arbitres.

Garde-fous obligatoires: mandat, diffusion, moderation, privacy, preuve, urgence, syndic, brouillon, cloture.

### Testeur accessibilite / novice - `CONV-2026-1385`

Verdict novice: NO-GO en l'etat, GO conditionnel si l'ecran rend visibles les cinq decisions avant toute action.

Critere GO 30 secondes: l'utilisateur doit pouvoir dire d'ou vient le message, pourquoi il est montre maintenant, s'il est urgent ou a classer, s'il est sensible ou diffusable, si l'action envoie quelque chose ou prepare seulement un brouillon, et quelle est la prochaine action conseillee.

## Convergence UX/UI

Decision de relance: remplacer la recommandation courte `inbox priorisee` par une direction plus prudente: `file de qualification des messages recus`, tout en conservant le titre novice `Messages recus des coproprietaires`.

Le premier ecran ne doit pas chercher seulement "quoi traiter d'abord". Il doit montrer "quelle decision humaine manque pour agir sans erreur".

## Image candidate retenue

| Fichier | Intention | Statut | Decision |
|---|---|---|---|
| `docs/assets/ux-ui-recherche-2026-05-24-alertes-sollicitations-copro-relance/blueprint_file_qualification_messages.svg` | Blueprint de decision pour comparer l'ancienne inbox priorisee a une file de qualification centree sur les cinq decisions humaines. | retenue | Sert de direction de reference pour arbitrage Brice avant tout chantier dev. |

## Decisions ouvertes pour Brice

- MVP: garder seulement `brouillon + copie manuelle`, ou autoriser la trace d'envois faits hors CoproScope ?
- Vue: MVP interne CS/syndic benevole seulement, ou vue coproprietaire limitee ?
- Droits: quels profils peuvent voir les originaux restreints ?
- Doctrine: les accusations nominatives sont-elles toujours restreintes, meme apres reformulation ?
- File dediee: faut-il une file `A transmettre au syndic` des le premier ecran ?
- Preuve minimale: quel seuil avant de transformer un message en action suivie ?
- Locataires/mandataires/avocats: quel statut et quel gate d'identite/mandat ?

## Recommandation finale

Ouvrir un chantier dev separe seulement si Brice valide la direction suivante:

```text
Messages recus des coproprietaires = file de qualification, pas messagerie.
Action principale = choisir la suite.
Aucun envoi ou diffusion automatique en MVP.
Chaque message doit montrer urgence, sensibilite, preuve, diffusion et suite avant action.
```

## BOT-END - Orchestrateur UX/UI - 2026-05-24 09:30 +02:00

Roadmap: `RM-2026-0031`
Chantier: `CH-20260524-092539-RM-2026-0031-alertes-sollicitations-relance`
Conversation: `CONV-2026-1380`
Statut: `CLOTURE`
Fichiers modifies: ce livrable, `docs/assets/ux-ui-recherche-2026-05-24-alertes-sollicitations-copro-relance/README.md`, `docs/assets/ux-ui-recherche-2026-05-24-alertes-sollicitations-copro-relance/blueprint_file_qualification_messages.svg`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: code applicatif, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, serveurs locaux, `RM-2026-0017`.
Tests/preuves: pas de test applicatif; preuve = sorties des cinq roles, blueprint SVG et verification documentaire.
Limites: aucune recherche terrain reelle; aucun prototype interactif; image candidate = blueprint decisionnel, pas UI livree.
Questions ouvertes: arbitrages Brice ci-dessus.
Prochain mouvement propose: si Brice valide, ouvrir un chantier dev separe sur corpus fictif/demo avec gates mandat, diffusion, moderation, preuve, urgence, syndic, brouillon et cloture.

UXUI-DONE - equipe UX/UI a fini son job
