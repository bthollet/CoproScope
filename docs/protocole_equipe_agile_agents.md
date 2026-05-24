# Protocole equipe agile multi-agents

Date de creation: 2026-05-21.
Rattachement: `RM-2026-0005`.

Ce protocole s'applique quand Brice demande une "equipe agile", une equipe
multi-agents, une equipe UX/dev/QA, ou un fonctionnement par cycles rapides.
Il transforme la conversation en petite equipe cadree, avec utilisateurs,
facilitateurs/designers, devs et QA, sans casser les regles de presence.

Regle produit ajoutee: l'equipe travaille systematiquement sur de l'UI reelle.
Une discussion, une note ou une commande ne suffit pas: chaque cycle doit nommer
la route, l'ecran, la modale, l'artefact HTML ou le parcours local vise. Si
cette UI n'existe pas encore, le premier livrable est de la rendre testable.
Des que le sujet est visuel, nouveau, ambigu, dense ou sensible pour un membre
CS novice, le designer genere une image ou un blueprint, puis le novice le
qualifie en GO/NO-GO avant que le developpement commence.

## Regle de demarrage

Avant de lancer l'equipe, le coordinateur doit:

1. rattacher le travail a un `RM-*` dans `docs/roadmap_backlog_central.md`;
2. creer ou reprendre un `CH-*` dans `docs/presence_agents.md`;
3. declarer son propre `CONV-*` avec ownership, fichiers evites, trace, tests
   attendus, lease et dernier point lu;
4. ouvrir une ligne `CONV-*` par role actif;
5. attribuer un ownership disjoint a chaque role;
6. garder les devs en lecture si la commande produit ou le contrat de donnees
   n'est pas stable.
7. bloquer tout dev UI tant que la cible UI reelle, l'image/blueprint pertinent
   et la qualification novice ne sont pas explicites.

Sans ces elements, l'equipe reste en cadrage lecture seule.

## Roles standards

| Role | Fonction | Peut modifier |
|---|---|---|
| Coordinateur-scribe | Gouvernail, presence, decoupage, arbitrages, integration | Registres et points de coordination declares |
| Designer service / facilitateur | Enquete, blueprint image, commande dev, langage novice | Visuels, commandes, notes UX declares |
| Utilisateur novice | Test des routes livrees et attentes naturelles | Notes de test uniquement |
| Dev front | Templates, CSS `cs-*`, responsive, accessibilite | Templates/CSS declares apres commande validee |
| Dev back / viewmodel | Routes, projections `model.ux.*`, compteurs, donnees fictives | Modules/routes/viewmodels declares, owner unique sur fichiers sensibles |
| QA securite / regression | Tests, non-fuite, token, responsive, captures | Notes QA et tests declares; pas de correction sans ownership |

Roles optionnels:

- integration lead, quand front/back livrent des branches separees;
- DB/data designer, quand une autre conversation travaille la base de donnees;
- privacy/docops, quand les exports ou pieces peuvent contenir des donnees
  sensibles.

## Double flux rapide

Le coordinateur garde au maximum trois flux decales:

| Flux | Etat | Responsable |
|---|---|---|
| `N-1` | Test produit livre, corrections mineures | QA + utilisateur novice |
| `N` | Dev front/back depuis commande validee | Dev front + dev back |
| `N+1` | Enquete image, blueprint, commande suivante | Designer + utilisateur novice |

Un role qui devient idle est bascule vers:

- QA d'un ecran livre;
- preparation de la commande suivante;
- documentation de passation;
- controle de coherence;
- generalisation ou side-quest bornee demandee par orientation ponctuelle;
- analyse lecture seule d'un risque;
- integration, si son ownership est declare.

Quand la conversation poursuit un but principal, le coordinateur garde la piste
critique. Les demandes ponctuelles de generalisation, doctrine, exploration
transverse ou side-quest ne doivent pas interrompre le flux principal si un
thread/sub-agent peut les absorber. Le sub-agent recoit un objectif borne, un
ownership explicite, les fichiers a eviter, une trace attendue et un critere de
fin. Si la capacite de threads manque, la demande est notee pour reprise ou
arbitrage, sauf blocage direct du but principal.

## Gate UI reelle avant dev

Ce gate est obligatoire pour toute equipe agile.

1. **UI cible nommee**: le point de coordination cite une route, un ecran, une
   modale, un artefact HTML ou un parcours local. Si rien n'existe, la commande
   dit explicitement quelle UI minimale sera livree pour test.
2. **Image/blueprint designer**: requis des qu'il faut inventer, reorganiser ou
   rendre comprehensible une surface UI. Une capture annotee suffit pour une
   correction mineure; une image generee ou un blueprint structure est attendu
   pour un nouvel ecran, un changement de parcours, une zone dense ou une action
   sensible.
3. **Qualification novice**: le membre novice donne un GO/NO-GO sur l'image, le
   blueprint ou la route existante avant lancement dev. Son retour nomme ce
   qu'il comprend, ce qu'il croit pouvoir cliquer, ce qui le bloque et les mots
   naturels a utiliser.
4. **Commande dev stabilisee**: le coordinateur transforme le GO novice en
   commande front/back avec donnees, interactions, etats vides, garde-fous
   privacy et tests.

No-go immediat:

- dev lance depuis une intention abstraite sans UI cible;
- dev qui invente la structure d'une vue pertinente sans designer;
- image/blueprint non qualifie par le novice alors que l'ecran est nouveau,
  visuel, dense ou sensible;
- test qui valide une maquette sans route, ecran ou artefact livre.

## Cycle type

1. Cadrage de l'UI reelle cible: route, ecran, modale, artefact ou parcours.
2. Enquete sur UI existante, image generee, blueprint ou capture livree.
3. Qualification novice de l'image/blueprint ou de l'UI existante.
4. Commande dev au format obligatoire.
5. Developpement front/back sur ownership explicite.
6. Test de la route, de l'ecran ou de l'artefact reel livre.
7. Correction mineure ou retour designer si l'intention change.
8. Cloture par preuves: UI reelle, captures, tests, go/no-go novice.

La commande dev doit contenir:

- objectif utilisateur;
- UI cible reelle et route ou artefact a tester;
- structure visuelle;
- composants;
- donnees necessaires;
- interactions;
- etats vides;
- criteres d'acceptation;
- tests attendus.

## Garde-fous

- Aucun dev ne demarre sans commande validee.
- Aucun visuel manquant n'est invente directement par les devs.
- Aucun dev UI ne demarre sans UI reelle cible.
- Aucun dev ne demarre sur une UI nouvelle, visuelle, dense ou sensible sans
  image/blueprint designer qualifie par le novice.
- Aucun testeur ne valide une intention abstraite: il teste une route, un ecran
  ou un artefact reel.
- Un fichier sensible a un seul owner a la fois.
- Les donnees privees ne sont pas ajoutees a Git.
- Les donnees fictives doivent etre marquees comme fictives ou demo.
- Un changement d'intention retourne au designer, pas directement au dev.
- Les tests rouges sont classes: regression produit, test obsolete, ou dette
  connue. Ils ne sont pas masques.

## Point de coordination

Chaque point de coordination utilise ce format:

- A tester maintenant
- En dev maintenant
- En enquete maintenant
- Commande prete
- Agents idle a relancer
- Decision requise
- Prochain mouvement
- Tests/preuves

Le coordinateur donne un prochain mouvement concret. S'il n'y a pas
d'arbitrage impossible, l'equipe continue.

## Contrat court a copier a un agent

```text
Mission: <bloc ou sprint>
Role/filiere: <coordinateur | designer | utilisateur novice | front | back | QA>
Roadmap/chantier/conversation: RM-YYYY-NNNN / CH-YYYY-NNNN / CONV-YYYY-NNNN
Tu n'es pas seul dans le codebase. Ne revert jamais les changements des autres.
Ownership modifiable: <fichiers/dossiers>
Fichiers a eviter: <fichiers/dossiers>
Passerelle/registre de trace: <fichier>
Dernier point coordination lu: <fichier + heure>
Lease ownership: <expiration + fuseau>
Donnees: pas de donnees privees dans Git; fictif explicite pour demo/test.
Verification attendue: <tests, route, capture, go/no-go>
Livrable final: resume, fichiers modifies, fichiers evites, limites, tests.
```

## Quand l'utilisateur dit "equipe agile"

Le comportement attendu est:

1. le coordinateur lit `AGENTS.md`, ce protocole, la roadmap et la presence;
2. il declare un `BOT-START`;
3. il ouvre les roles standards utiles, pas plus;
4. il nomme l'UI reelle cible du cycle courant;
5. il demande au designer une image ou un blueprint des que c'est pertinent,
   puis fait qualifier cette sortie par le novice avant dev;
6. il garde le flux decale actif;
7. il travaille localement sur la piste critique pendant que les agents
   traitent les pistes paralleles;
8. il delegue aux sub-agents les generalisations et side-quests bornees si les
   threads disponibles le permettent;
9. il integre uniquement apres preuves et ownership clair;
10. il publie un `BOT-END` ou un point de reprise exploitable.
