# Recherche UX/UI WorksOps travaux - approfondissement

Date de lancement: 2026-05-24 09:41 +02:00.
Date de cloture: 2026-05-24 09:49 +02:00.
Roadmap: `RM-2026-0032`.
Chantier: `CH-20260524-094112-RM-2026-0032-travaux-approfondissement-ux`.
Conversation coordination: `CONV-2026-1500`.
Mode: equipe UX/UI recherche visuelle sans dev.
Statut: cloture sans dev.

## BOT-START

BOT-START - Orchestrateur UX/UI WorksOps approfondissement - 2026-05-24 09:41 +02:00

Roadmap: `RM-2026-0032`
Chantier: `CH-20260524-094112-RM-2026-0032-travaux-approfondissement-ux`
Conversation: `CONV-2026-1500`
Role: Orchestrateur UX/UI
Mission: approfondir la direction WorksOps travaux avant tout dev, en stressant les cas limites, le blueprint, la comprehension novice, les gates metier et les decisions encore ouvertes.
Ownership modifiable: `docs/recherche_ux_ui_2026-05-24_travaux_approfondissement.md`, `docs/assets/ux-ui-recherche-2026-05-24-travaux-approfondissement/`, lignes de presence et gouvernail liees a `RM-2026-0032`.
Fichiers a eviter: code applicatif, routes, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, serveurs locaux, `RM-2026-0017` bloque.
Passerelle/registre de trace: cette mission, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/protocole_equipe_ux_ui_recherche.md`, `docs/consignes_bots_interconversations.md`, `docs/protocole_roadmap_presence_agents.md`, gouvernail, presence, `docs/recherche_ux_ui_2026-05-24_travaux.md`, `docs/cadrage_metier_worksops_2026-05-24.md`, `docs/recherche_ux_ui_2026-05-24_travaux_operation-model.md`.
Tests/preuves attendus: sorties des cinq roles UX/UI, annotations ou variante de blueprint si utile, point court, aucune verification applicative car aucun code.
Risque de collision: les traces WorksOps precedentes `CONV-2026-1331`..`1336`, `CONV-2026-1367` et `CONV-2026-1390`..`1395` sont cloturees; `CONV-2026-1400`..`1401` viennent d'etre pris par ajout-docs et `CONV-2026-1410`..`1415` par Audit360; cette iteration reserve `CONV-2026-1500`..`1505`.
Lease ownership: 2026-05-25 09:41 +02:00.
Prochaine action: lancer les cinq roles en lecture seule et consolider seulement ce qui approfondit les decisions ouvertes.

## Objectif

Cette iteration ne relance pas le cadrage deja stabilise. Elle doit le pousser
plus loin avant tout chantier dev:

- transformer les decisions ouvertes en arbitrages testables;
- detailler les annotations du blueprint retenu;
- identifier les cas limites qui cassent le parcours `portefeuille + fiche probatoire`;
- verifier le langage novice, les etats metier et les risques de mauvais clic;
- dire si une nouvelle image est necessaire ou si le blueprint existant suffit.

## Sources

- `docs/recherche_ux_ui_2026-05-24_travaux.md`
- `docs/cadrage_metier_worksops_2026-05-24.md`
- `docs/recherche_ux_ui_2026-05-24_travaux_operation-model.md`
- `docs/assets/ux-ui-recherche-2026-05-24-travaux/01-console-travaux-portefeuille-fiche.svg`
- `docs/agent_briefs/lot-f-worksops.md`
- `docs/fonctions_cibles.md`

## Questions d'approfondissement

1. Creation: faut-il autoriser `Creer une operation` au premier lot, ou se limiter aux operations detectees/a qualifier ?
2. Seuils: comment afficher la mise en concurrence quand les seuils CS/AG sont absents de l'instance ?
3. Corpus: quels 3 a 5 cas synthetiques couvrent vote, devis, commande, reception, reserve, garantie, budget et diffusion ?
4. Diffusion: quelle regle UX rend visible le statut PrivacyOps sans faire croire a une validation juridique ?
5. Blueprint: quelles annotations sont indispensables pour un futur owner dev ?

## Roles

| Role | Conversation | Statut | Sortie attendue |
|---|---|---|---|
| Orchestrateur UX/UI | `CONV-2026-1500` | `CLOTURE` | Cadrage, relance, synthese et garde-fous. |
| Chercheur utilisateur | `CONV-2026-1501` / Anscombe `019e58f4-1825-7143-91c8-d82b05f6691f` | `CLOTURE` | Scenarios, irritants, arbitrages et criteres de reussite integres. |
| Architecte UX | `CONV-2026-1502` / Rawls `019e58f4-1a40-78b2-af23-08b177d60bbe` | `CLOTURE` | Contrat d'ecran, wireflow, etats et annotations blueprint integres. |
| Designer UI / generateur visuel | `CONV-2026-1503` / Franklin `019e58f4-1ba4-72a2-b849-46a39e21ebb9` | `CLOTURE` | Decision de ne pas creer de nouvelle image; annotations du blueprint integrees. |
| Testeur metier expert | `CONV-2026-1504` / Turing `019e58f4-2154-7693-95fc-66e11ef65cd2` | `CLOTURE` | Cas limites, no-go metier, corpus minimal et libelles integres. |
| Testeur accessibilite / novice | `CONV-2026-1505` / Sartre `019e58f4-2574-74a1-bccb-faf958bf2ea3` | `CLOTURE` | Comprehension 30 secondes, ordre visuel et CTA dangereux integres. |

## Point Court Initial

A produire: arbitrages de creation d'operation, seuils, corpus synthetique,
diffusion et annotations exploitables du blueprint.

En test: rien en execution applicative; tests de comprehension et de coherence
UX/UI en lecture seule.

Images candidates: blueprint existant a annoter en priorite; nouvelle image
seulement si le designer prouve qu'elle clarifie un arbitrage.

Decisions ouvertes: creation vs detection, seuils par instance, corpus minimal,
export diffusable, libelles de preuves et actions prudentes.

Prochain mouvement: attendre les cinq sorties, consolider, puis soit fermer
avec `UXUI-DONE`, soit laisser la heartbeat reprendre les roles manquants.

## Decision UX/UI Approfondie

Decision: conserver `Travaux suivis` en portefeuille + fiche probatoire, sans
nouvelle image candidate. Le blueprint existant reste la reference, mais il doit
etre annote plus strictement avant tout chantier dev.

Arbitrages retenus:

- premier lot prioritaire: operations detectees ou `a qualifier`;
- creation manuelle seulement en action secondaire `Creer une operation a qualifier`;
- une creation manuelle reste un brouillon probatoire: titre, perimetre, source
  et raison de creation, sans validation implicite;
- seuils absents: afficher `Seuil a renseigner` ou `Mise en concurrence a
  verifier`, sans conclure une non-conformite;
- diffusion: `Voir l'apercu avant partage` puis gate `A verifier avant
  partage`; pas d'export direct depuis une preuve candidate;
- budget: resume compact `Vote`, `Commande`, `Facture`, `Paye`, `Reste a
  verifier`; ComptaScope reste la source comptable;
- aucune cloture sur facture seule.

## Synthese Utilisateur

Scenarios critiques:

- devis ou facture detecte sans decision AG: statut `A qualifier`;
- travaux urgents hors AG: `Urgence a qualifier`, pas `vote manquant` par defaut;
- seuils absents: `Mise en concurrence a verifier`;
- facture de solde sans reception: `Reception a prouver`;
- reception avec reserves: operation active jusqu'a preuve de levee;
- export coproprietaires: apercu seulement tant que PrivacyOps n'a pas qualifie
  la diffusion.

Risques de confusion:

- `WorksOps`, `OperationTravaux`, `preuve candidate`, `diffusion a arbitrer`,
  `montant engage`, `reception`, `reserves`, `mise en concurrence` et `seuils`
  sont trop techniques au premier niveau;
- `Ce qui bloque` peut sonner accusatoire; `Ce qui manque pour continuer` est
  plus naturel dans les contextes sensibles;
- un badge vert sur assurance, facture ou reception cree une fausse securite;
- `Ajouter` ou `Creer une operation` en bouton principal peut faire croire que
  l'utilisateur officialise un chantier.

## Architecture UX

Desktop:

- bandeau: `Operations ouvertes`, `Preuves bloquantes`,
  `Receptions/reserves`, `A verifier avant partage`;
- portefeuille: colonnes limitees a `Travaux`, `Ou en est-on ?`, `Ce qui
  manque`, `A faire maintenant`, plus badge diffusion discret;
- fiche probatoire: `Ce qui bloque`, action prudente, chaine `Vote -> Devis ->
  Commande -> Travaux -> Reception -> Reserves -> Garantie`;
- second niveau: budget resume, pieces liees, historique et diffusion.

Mobile:

- cartes empilees, pas de tableau horizontal;
- carte: titre, statut, preuve manquante, prochaine action;
- fiche en page detail, frise transformee en liste verticale;
- CTA prudent sticky: `Preparer une demande`, `Verifier la piece` ou `Rattacher
  une piece`.

Etats operation:

- `A qualifier`;
- `Vote a retrouver`;
- `Mise en concurrence a verifier`;
- `Commande a confirmer`;
- `Travaux en cours`;
- `Reception a prouver`;
- `Reserves a suivre`;
- `Garantie a surveiller`;
- `Clos avec preuves`.

Etats preuve:

- `Manquante`;
- `A verifier`;
- `Confirmee`;
- `Contradictoire`;
- `Non applicable`.

Etats ecran requis:

- vide sans travaux;
- pieces detectees non rattachees;
- seuils inconnus;
- budget indisponible;
- preuves contradictoires;
- diffusion bloquee;
- erreur de chargement;
- droits insuffisants.

## Direction UI Et Blueprint

Nouvelle image candidate: non. Le blueprint source suffit:

- `docs/assets/ux-ui-recherche-2026-05-24-travaux/01-console-travaux-portefeuille-fiche.svg`

Annotations indispensables:

- renommer l'ecran en `Travaux suivis`;
- remplacer `Ajouter` par CTA secondaire `Creer une operation a qualifier`, ou
  retirer le bouton du premier lot;
- remplacer `Preparer relance` par `Preparer une demande`;
- placer `Ce qui bloque` avant la frise;
- grouper les pieces en `Confirmees`, `A verifier`, `Manquantes`;
- ajouter un badge par ligne: `A verifier avant partage`, `Apercu possible`,
  `Bloque`;
- ajouter un bloc `Seuils et mise en concurrence` avec etat inconnu explicite;
- ajouter un mini-budget `Vote`, `Commande`, `Facture`, `Paye`, `Reste a
  verifier`;
- annoter la version mobile: cartes, detail vertical et CTA prudent sticky.

Couleurs:

- rouge pale: preuve manquante;
- ambre: piece a verifier;
- vert: preuve confirmee;
- bleu/gris: budget ou diffusion.

Le statut ne doit jamais reposer sur la couleur seule.

## Test Metier

GO recherche, NO-GO dev direct tant que WorksOps ne verrouille pas statuts
probatoires, seuils, diffusion et corpus fictif.

No-go metier:

- `Clos avec preuves` sans reception et reserves traitees;
- badge `Travaux OK`, `Assurance OK`, `Facture validee`;
- export direct aux coproprietaires sans gate PrivacyOps;
- UI qui laisse croire qu'une facture prouve la fin du chantier;
- creation libre d'operation si le statut initial et les pieces minimales ne
  sont pas cadres.

Corpus synthetique minimal:

1. AG votee, devis retenu, commande manquante.
2. Facture solde presente, reception absente.
3. Reception avec reserves, levee non prouvee.
4. Urgence hors AG avec regularisation a qualifier.
5. Garantie ou assurance incoherente avec date ou activite, diffusion bloquee.

## Test Novice

Verdict: GO conditionnel pour continuer le blueprint; NO-GO dev direct si
creation, cloture ou diffusion deviennent des actions primaires avant preuve,
reception/reserves et arbitrage de partage.

Libelles recommandes:

| Intention | Libelle |
|---|---|
| Titre | `Travaux suivis` ou `Suivi des travaux` |
| Colonnes/cartes | `Ou en est-on ?`, `Ce qui bloque`, `A faire maintenant` |
| Preuves | `Pieces manquantes`, `Pieces a verifier`, `Pieces confirmees` |
| Budget | `Vote`, `Commande`, `Facture`, `Paye`, `Reste a verifier` |
| Diffusion | `A verifier avant partage` |
| Creation | `Ajouter un suivi travaux a verifier` |

CTA dangereux:

- `Cloturer le chantier`;
- `Valider la facture`;
- `Travaux OK`;
- `Assurance OK`;
- `Reception faite`;
- `Diffuser aux coproprietaires`;
- `Envoyer automatiquement`;
- `Creer une operation` en bouton principal.

Critere 30 secondes: un novice doit savoir quel chantier bloque, quelle piece
manque, quoi faire, combien est en jeu et si le partage est possible ou non.

## GO / NO-GO

GO:

- conserver le premier ecran `portefeuille + fiche probatoire`;
- garder le blueprint existant comme reference;
- approfondir par annotations, pas par nouvelle image;
- tester le futur dev uniquement sur corpus synthetique.

NO-GO:

- dev direct avant verrouillage creation/seuils/corpus/diffusion;
- titre utilisateur contenant `WorksOps` ou `OperationTravaux`;
- action primaire de cloture, creation ou diffusion;
- cloture d'une operation sur facture seule;
- export sans apercu et gate PrivacyOps.

## Point Court Final

A produire: seulement si un chantier dev separe est ouvert plus tard, une
version annotee du blueprint et un corpus synthetique de 5 operations.

En test: tests de comprehension et coherence UX/UI faits en lecture seule par
les cinq roles; aucun test applicatif car aucun code.

Images candidates: aucune nouvelle image retenue; blueprint existant conserve a
annoter.

Decisions ouvertes: GO Brice sur le lot dev separe, statut exact de creation
manuelle, source des seuils par instance et regle PrivacyOps d'export.

Prochain mouvement: remettre `RM-2026-0032` en pret a integrer; ouvrir un
chantier dev WorksOps separe seulement apres GO explicite.

## Journal

| Heure | Conversation | Evenement | Note |
|---|---|---|---|
| 2026-05-24 09:41 +02:00 | `CONV-2026-1500` | `BOT-START` | Nouvelle iteration UX/UI WorksOps approfondissement ouverte sans dev, serveur ni instance privee; IDs renumerotes apres collisions avec ajout-docs et Audit360. |
| 2026-05-24 09:47 +02:00 | `relance-ux-ui-travaux-approfondissement` | `AUTOMATION_CREATE` | Heartbeat actif toutes les 10 minutes jusqu'au marqueur `UXUI-DONE - equipe UX/UI a fini son job`. |
| 2026-05-24 09:47 +02:00 | `CONV-2026-1501`..`CONV-2026-1505` | `AGENTS_LAUNCHED` | Agents Anscombe, Rawls, Franklin, Turing et Sartre lances en lecture seule; aucun code, serveur ou instance privee. |
| 2026-05-24 09:49 +02:00 | `CONV-2026-1501`..`CONV-2026-1505` | `AGENTS_DONE` | Les cinq roles ont rendu leurs sorties; convergence sur detection prioritaire, creation secondaire, seuils explicites, gate diffusion et blueprint existant a annoter. |
| 2026-05-24 09:49 +02:00 | `CONV-2026-1500` | `BOT-END` | Recherche cloturee sans dev, serveur ni instance privee; `UXUI-DONE` pose pour arret de la heartbeat. |
| 2026-05-24 09:50 +02:00 | `relance-ux-ui-travaux-approfondissement` | `AUTOMATION_DELETE` | Heartbeat supprimee apres presence du marqueur final `UXUI-DONE - equipe UX/UI a fini son job`. |
| 2026-05-24 09:52 +02:00 | `relance-ux-ui-travaux-approfondissement-2` | `AUTOMATION_DUPLICATE_DELETE` | Heartbeat doublon issue d'une course locale supprimee; aucune relance UX/UI supplementaire conservee pour ce chantier. |

## BOT-END

BOT-END - Orchestrateur UX/UI WorksOps approfondissement - 2026-05-24 09:49 +02:00

Roadmap: `RM-2026-0032`
Chantier: `CH-20260524-094112-RM-2026-0032-travaux-approfondissement-ux`
Conversations: `CONV-2026-1500`..`CONV-2026-1505`
Statut: `CLOTURE`
Fichiers modifies: `docs/recherche_ux_ui_2026-05-24_travaux_approfondissement.md`, `docs/assets/ux-ui-recherche-2026-05-24-travaux-approfondissement/README.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: code applicatif, routes, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, serveurs locaux, `RM-2026-0017` bloque.
Tests/preuves: cinq sorties de roles UX/UI; verification documentaire ciblee par `git diff --check`; aucun test applicatif car aucun code.
Limites: pas de validation juridique, pas de recette UI reelle, pas de corpus travaux execute.
Questions ouvertes: GO Brice pour chantier dev separe, statut exact creation manuelle, source des seuils instance, regle PrivacyOps d'export.
Prochain mouvement propose: ouvrir un chantier dev WorksOps separe seulement apres GO explicite, avec corpus synthetique et blueprint annote.

UXUI-DONE - equipe UX/UI a fini son job
