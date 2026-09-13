# Recherche UX/UI - Gouvernance CR CS valide en interne

Date de lancement: 2026-05-24 09:16 +02:00
Date de cloture: 2026-05-24 09:25 +02:00
Statut: cloture sans dev
Rattachement: `RM-2026-0024`
Chantier: `CH-20260524-091633-RM-2026-0024-gouvernance-cr-cs`
Conversation coordinatrice: `CONV-2026-1361`
Assets mission: `docs/assets/ux-ui-recherche-2026-05-24-gouvernance-cr-cs/`

## BOT-START

```text
BOT-START - Orchestrateur UX/UI - 2026-05-24 09:16 +02:00
Roadmap: RM-2026-0024
Chantier: CH-20260524-091633-RM-2026-0024-gouvernance-cr-cs
Conversation: CONV-2026-1361
Role: Orchestrateur UX/UI
Mission: relancer la recherche UX/UI gouvernance sur le MVP recommande `Compte rendu CS valide en interne`.
Ownership modifiable: docs/recherche_ux_ui_2026-05-24_gouvernance_cr_cs.md, docs/assets/ux-ui-recherche-2026-05-24-gouvernance-cr-cs/, docs/presence_agents.md, docs/roadmap_backlog_central.md.
Fichiers a eviter: code applicatif, templates, CSS, tests, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, RM-2026-0017 bloque.
Passerelle/registre de trace: ce livrable de mission et docs/presence_agents.md.
Dernier point lu: AGENTS.md, docs/protocole_equipe_ux_ui_recherche.md, docs/consignes_bots_interconversations.md, docs/protocole_roadmap_presence_agents.md, docs/roadmap_backlog_central.md, docs/presence_agents.md, docs/recherche_ux_ui_2026-05-24_gouvernance.md.
Tests/preuves attendus: preuve documentaire, images/blueprints retenus, retours metier et novice; pas de test applicatif car aucun code ne doit etre modifie.
Risque de collision: autres equipes UX/UI cloturees ou paralleles; plage initiale CONV-2026-1355 a CONV-2026-1360 collisionnee avec ajout-docs, relance gouvernance renumerotee en CONV-2026-1361 a CONV-2026-1366.
Lease ownership: jusqu'au 2026-05-25 09:16 +02:00.
Prochaine action: lancer les roles UX/UI en lecture seule, cadrer le parcours CR CS, produire direction UI et criteres de GO/NO-GO.
```

## Objectif

Transformer la recommandation de la recherche gouvernance en decision UX/UI
plus operationnelle pour un MVP: `Compte rendu CS valide en interne`.

La sortie reste une recherche sans dev: parcours, structure d'ecran, statuts,
libelles, blueprint utile a decision, retours metier et retours novice. Aucune
route, template, CSS, test applicatif ou commande dev detaillee n'a ete produit
dans cette mission.

## Roles

| Conversation | Role | Statut | Agent / source | Sortie integree |
|---|---|---|---|---|
| `CONV-2026-1361` | Orchestrateur UX/UI | `CLOTURE` | fil courant | Cadrage, consolidation, heartbeat, synthese finale. |
| `CONV-2026-1362` | Chercheur utilisateur | `CLOTURE` | Ramanujan `019e58da-22da-78d2-bf1c-fdd6cfb81f13` | Profils, besoins, irritants, scenarios et criteres de reussite CR CS. |
| `CONV-2026-1363` | Architecte UX | `CLOTURE` | Huygens `019e58da-23e9-7fe1-a55b-9f9cb45d1df9` | Wireflow, etats, priorites d'information, variantes desktop/mobile. |
| `CONV-2026-1364` | Designer UI / generateur visuel | `CLOTURE` | Goodall `019e58da-2472-7432-a516-d66e36e89c33` | Direction UI et blueprint retenu. |
| `CONV-2026-1365` | Testeur metier expert | `CLOTURE` | Aquinas `019e58da-2520-78b2-bddd-b178720d0947` | No-go metier, cas limites et vocabulaire prudent. |
| `CONV-2026-1366` | Testeur accessibilite / novice | `CLOTURE` | Poincare `019e58da-25fc-74c3-b7dd-f328dcb68ab5` | Test comprehension, libelles simples et criteres d'acceptation. |

## Sources

| Source | Usage |
|---|---|
| `docs/recherche_ux_ui_2026-05-24_gouvernance.md` | Recherche precedente et recommandation MVP. |
| `docs/enquete_collaboration_coedition_impact_2026-05-24.md` | Hypotheses terrain gouvernance. |
| `docs/ag_contentieux_passation.md` | Objets et garde-fous AG/contentieux/passation. |
| `docs/ui_ag_contentieux_passation.md` | Surface UI existante et limites. |
| `docs/ux_ecarts_enquete_vs_produit_2026-05-20.md` | Ecarts connus sur decisions, preuves et AG. |
| `docs/test_novice_live_8766_2026-05-21.md` | Confusions novice deja observees. |

## Synthese Utilisateur

Le MVP vise d'abord le president ou secretaire du conseil syndical, puis un
membre CS novice qui relit et valide en interne. Le besoin central n'est pas de
"signer" un document, mais de transformer une reunion CS en memoire fiable:
presents, sujets, constats, decisions, actions, pieces source, version validee
et diffusion controlee.

Le premier ecran doit repondre en moins de 30 secondes a six questions:

1. Quel est le statut du compte rendu ?
2. Quelle est la prochaine action ?
3. Quelles decisions ou actions manquent de preuve ?
4. Qui doit relire ou valider ?
5. Quelle version est la reference ?
6. Qui pourra voir le document apres export ou partage ?

Le parcours P0 retenu est:

1. creer ou ouvrir le compte rendu de reunion CS;
2. confirmer presents, excuses et roles;
3. renseigner les sujets traites;
4. rattacher a chaque sujet un constat, une decision, une action et une preuve;
5. demander une relecture CS;
6. valider la version interne;
7. verifier la diffusion avant tout export;
8. archiver la version et le journal.

## Architecture UX

La structure recommandee est un ecran de travail dense mais lisible.

Sur desktop:

- bandeau persistant: titre, statut, version, avertissement `Validation interne CS - ne vaut pas signature qualifiee`;
- colonne gauche: reunion, presents, excuses, ordre du jour et completude des sujets;
- zone centrale: tableau editorial par sujet avec `Sujet`, `Constat`, `Decision CS`, `Action`, `Responsable`, `Echeance`, `Preuve`;
- rail droit: validateurs, blocages, restriction/diffusion, prochaine action, export/revue de diffusion;
- bas de page ou panneau secondaire: journal de versions et validations.

Sur mobile:

- premier bloc: statut, prochaine action, preuve manquante, version et diffusion;
- navigation par onglets: `Sujets`, `Decisions`, `Actions`, `Preuves`, `Validation`;
- bouton principal limite a l'action suivante, jamais a une publication externe.

Etats retenus:

- `Brouillon interne`;
- `En relecture`;
- `Pret a valider`;
- `Bloque - preuve ou diffusion a clarifier`;
- `Valide en interne par le conseil syndical`;
- `Revue diffusion`;
- `Export confirme`;
- `Nouvelle version ouverte apres correction`.

## Direction UI

Direction retenue: console de validation interne, pas document officiel.

Le libelle visible doit etre `Compte rendu du conseil syndical`. Le bandeau
doit rappeler que le document est interne et ne vaut pas PV d'AG, convocation
officielle ni signature qualifiee. Les boutons doivent privilegier:

- `Demander relecture`;
- `Valider version interne`;
- `Verifier avant partage`;
- `Preparer revue diffusion`.

Termes a eviter au premier niveau: `Signer`, `Publier`, `Envoyer officiel`,
`PV AG`, `Resolution adoptee`, `signature qualifiee`. Un export peut produire
un fichier, mais il ne doit jamais laisser croire a un envoi automatique ou a
une notification officielle.

Image retenue:

| Fichier | Statut | Usage |
|---|---|---|
| `docs/assets/ux-ui-recherche-2026-05-24-gouvernance-cr-cs/cr-cs-validation-interne-blueprint.svg` | retenu | Blueprint desktop de la console CR CS: bandeau de prudence, table decisions/actions/preuves, rail validation/diffusion. |

## Test Metier

Verdict metier: GO recherche pour ouvrir une revue produit, NO-GO dev tant que
la frontiere juridique n'est pas explicite dans la future specification.

No-go metier:

- l'interface laisse croire qu'un CR CS vaut PV d'AG, convocation officielle,
  decision d'AG ou acte externe;
- `Valider` est interpretable comme signature qualifiee;
- une version validee reste modifiable sans creer de nouvelle version;
- export ou partage possible sans revue de diffusion;
- une decision ou action est validee sans preuve, ou avec une preuve encore
  marquee `Preuve a verifier`;
- une opinion individuelle ou reserve devient la position du CS;
- une action impose une obligation sans distinguer `a demander`, `a proposer`
  ou `a suivre`;
- les restrictions sensibles ne bloquent pas diffusion ou biffage.

Cas limites a garder dans la prochaine spec: membre CS aussi syndic benevole,
CR qui prepare une question d'AG, correction apres validation, preuve
confidentielle, commentaire d'expert externe, action adressee au syndic ou a un
tiers, reserve d'un membre, accord par mail/SMS, export deja transmis.

## Test Novice

Verdict novice: GO conditionnel si les libelles sont simplifies et si les
preuves/diffusion ne sont pas cachees.

Libelles recommandes:

| Libelle technique | Libelle novice |
|---|---|
| `CR CS` | `Compte rendu du conseil syndical` |
| `Valide CS` | `Valide en interne par le conseil syndical` |
| `Validation interne CS` | `Validation interne, sans signature juridique` |
| `Diffusion` | `Qui pourra voir ce document` |
| `Revue diffusion` | `Verifier avant partage` |
| `Export confirme` | `Fichier cree, non envoye automatiquement` |
| `Piece source` | `Document qui justifie cette decision` |
| `Preuve a verifier` | `Document a verifier avant validation` |

Conditions d'acceptation novice:

- identifier statut, prochaine action, preuve manquante, version, validation et diffusion en moins de 30 secondes;
- aucune confusion entre CR CS, PV d'AG et signature qualifiee;
- validation bloquee si preuve ou diffusion restent ambigues;
- correction apres validation ouvre une nouvelle version;
- export indique qui pourra voir le fichier et ne declenche aucun envoi officiel.

## Decision UX/UI

Decision: direction `Compte rendu du conseil syndical - validation interne`
retenue comme prochaine base de cadrage produit.

GO pour une suite de cadrage/dev separee seulement si la commande suivante
reste bornee a un MVP documentaire interne:

- creation/edition d'un CR CS;
- presents, sujets, decisions, actions et preuves;
- statuts de validation interne;
- journal de versions;
- revue de diffusion avant export;
- aucune signature qualifiee, aucune publication AG, aucun envoi officiel.

Le parcours Atelier AG reste en suite de roadmap, mais ne doit pas etre mele au
premier MVP CR CS.

## Questions Ouvertes

- Quelle regle exacte distingue `Preuve a verifier` et `Preuve acceptee` ?
- Combien de validateurs CS sont requis pour marquer `Valide en interne` ?
- Le partage doit-il etre limite a un export fichier ou inclure une diffusion
  interne CoproScope dans une iteration ulterieure ?
- Comment representer les reserves individuelles sans les transformer en
  position collective ?
- Quelle integration future avec `RM-2026-0026` fichier coproprietaires / AG et
  `RM-2026-0028` communication officielle ?

## BOT-END

```text
BOT-END - Orchestrateur UX/UI - 2026-05-24 09:25 +02:00
Roadmap: RM-2026-0024
Chantier: CH-20260524-091633-RM-2026-0024-gouvernance-cr-cs
Conversations: CONV-2026-1361..CONV-2026-1366
Resultat: recherche UX/UI CR CS valide en interne cloturee sans dev.
Livrables: cette synthese et le blueprint docs/assets/ux-ui-recherche-2026-05-24-gouvernance-cr-cs/cr-cs-validation-interne-blueprint.svg.
Tests/preuves: verification documentaire et git diff --check OK; pas de test applicatif car aucun code, serveur, template, CSS ou instance privee n'a ete modifie.
Limites: pas de validation juridique, pas de signature qualifiee, pas de test UI reelle, pas de donnees privees.
Prochain mouvement: arbitrer un chantier dev separe pour le MVP CR CS interne, ou garder RM-2026-0024 en attente produit.
```

UXUI-DONE - equipe UX/UI a fini son job
