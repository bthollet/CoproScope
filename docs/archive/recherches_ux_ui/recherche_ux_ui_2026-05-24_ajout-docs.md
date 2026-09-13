# Recherche UX/UI - parcours ajout docs

Date de lancement: 2026-05-24 03:21 +02:00.
Mode: equipe UX/UI recherche visuelle sans dev.

## BOT-START

```text
BOT-START - Orchestrateur UX/UI - 2026-05-24 03:21 +02:00
Roadmap: RM-2026-0003 principal; liens RM-2026-0006, RM-2026-0010, RM-2026-0029. RM-2026-0017 reste bloque et n'est pas relance.
Chantier: CH-20260524-032123-RM-2026-0003-ajout-docs-ux-ui
Conversation: CONV-2026-1313
Role: Orchestrateur UX/UI
Mission: lancer une recherche UX/UI sans dev sur le parcours d'ajout de documents.
Ownership modifiable: docs/recherche_ux_ui_2026-05-24_ajout-docs.md; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs/; docs/presence_agents.md.
Fichiers a eviter: code applicatif, tests, instances privees, secrets, exports bruts, passerelles hors mission, chantier reconstruction bloque RM-2026-0017.
Passerelle/registre de trace: ce document et docs/presence_agents.md.
Dernier point lu: AGENTS.md, docs/orchestration_agents.md, docs/protocole_equipe_ux_ui_recherche.md, docs/protocole_roadmap_presence_agents.md, docs/roadmap_backlog_central.md, docs/presence_agents.md, docs/coordination_interconversations_2026-05-21.md.
Tests/preuves attendus: synthese multi-roles, wireflow/image de decision, retours metier et novice, mention explicite qu'aucun code n'a ete produit.
Risque de collision: depot deja charge; rester en documentation uniquement et append-only autant que possible.
Lease ownership: jusqu'au 2026-05-25 03:21 +02:00.
Prochaine action: lancer les roles UX/UI en sous-agents de lecture/recherche.
```

## Objectif de la recherche

Clarifier le parcours d'ajout de documents pour un membre de conseil syndical ou un coproprietaire novice: depot local, comprehension de ce que CoproScope a compris, arbitrage de confidentialite, puis rattachement a un point, une action et une preuve.

La recherche ne doit pas produire de patch applicatif ni de ticket dev detaille. Elle doit produire une decision produit documentee, des images ou wireflows utiles, des arbitrages et des questions ouvertes.

## Sources lues au lancement

- `docs/ux_workflow_ajout_document.md`
- `docs/integration_route_ajout_document.md`
- `docs/integration_ui_ajout_document.md`
- `docs/checklist_ajout_document_runtime.md`
- `docs/commandes/commande_interface_tri_docops_feedback_2026-05-24.md`
- `server/src/coproscope/web/templates/document_intake.html`
- `docs/roadmap_backlog_central.md`
- `docs/presence_agents.md`

## Roles actifs

| Conversation | Role | Mission | Statut |
|---|---|---|---|
| `CONV-2026-1313` | Orchestrateur UX/UI | Cadre, trace, arbitre et livre la synthese. | En cours |
| `CONV-2026-1314` | Chercheur utilisateur | Profils, besoins, irritants, scenarios et criteres. | En cours |
| `CONV-2026-1315` | Architecte UX | Parcours, etats, hierarchie et wireflows. | En cours |
| `CONV-2026-1316` | Designer UI / generateur visuel | Directions UI, images candidates et principes d'interaction. | En cours |
| `CONV-2026-1317` | Testeur metier expert | Justesse copro/DocOps/privacy, cas limites et vocabulaire. | En cours |
| `CONV-2026-1318` | Testeur accessibilite / novice | Comprehension immediate, lisibilite, charge cognitive et blocages. | En cours |

## Cadrage initial

### Publics cibles

- Membre de conseil syndical qui depose des pieces pour garder une trace probatoire.
- Coproprietaire novice qui ajoute une piece recue et veut comprendre ce qui va se passer.
- Utilisateur avance qui traite une file DocOps et corrige des propositions sans terminal.

### Contraintes

- Local first: le brut reste dans l'instance locale.
- Pas de chemin local, nom prive, raw, restricted, logs, URL brute ou secret dans l'UI partageable.
- L'utilisateur peut dire `A_CLASSER` ou `A_ARBITRER` sans etre bloque par une fausse certitude.
- La confidentialite vient avant tout partage.
- Le rattachement `piece -> point -> action -> preuve` doit rester comprehensible et utile.

## Profils et scenarios prioritaires

### Profils

- Coproprietaire novice: ajoute une piece ponctuelle, doit comprendre sans jargon ce qui reste local, ce qui est confidentiel et ce qui reste a faire.
- Membre de conseil syndical ou syndic benevole: traite plusieurs documents, corrige vite les types, la confidentialite et les rattachements.
- Referent confidentialite: arbitre les statuts de diffusion et documente les motifs.
- Responsable preuve/action: relie chaque piece a un sujet concret, une action et une preuve attendue.

### Taches utilisateur

- Ajouter un ou plusieurs fichiers depuis ce poste.
- Verifier que rien n'est partage et qu'aucun chemin prive n'est affiche.
- Confirmer ou corriger le type documentaire, ou garder `A_CLASSER`.
- Decider la confidentialite avant toute sortie.
- Rattacher le document a un sujet, une action et ce qu'il doit prouver.
- Relire un recapitulatif: ajoute localement, confidentialite, reste a faire.

## Parcours principal et variantes

### Parcours principal retenu

1. Ouvrir `Ajouter depuis mon ordinateur`.
2. Ajouter un fichier localement.
3. Voir une confirmation simple: le fichier est ajoute localement, rien n'est partage.
4. Qualifier le type documentaire, avec une option normale `Je ne sais pas encore`.
5. Decider qui pourra voir le document.
6. Rattacher a un sujet, une action et ce que le document doit prouver.
7. Fermer sur un recapitulatif operationnel et une prochaine action.

### Variante de lot

Le traitement massif DocOps ne doit pas etre le premier ecran novice. Il devient une variante separee: tri par colonnes de confidentialite, compteurs, corrections rapides, justification obligatoire pour les restrictions fortes et compteur de modifications non enregistrees.

## Problemes UX/UI priorises

| Priorite | Probleme | Decision |
|---|---|---|
| P0 | Confusion entre "depose localement" et "diffusable". | Afficher la confidentialite comme barriere avant toute sortie. |
| P0 | Ecran trop dense pour les 5 premieres minutes. | Retenir une piece active a la fois, une prochaine action dominante. |
| P0 | `point -> action -> preuve` est abstrait. | Renommer en `document -> sujet -> action -> ce que cela doit prouver` au premier niveau. |
| P0 | `DIFFUSABLE_BRUT` peut etre compris comme autorisation automatique. | Preferer `Diffusable sans biffage apres verification`. |
| P1 | `A_CLASSER` et `A_ARBITRER` ressemblent a des erreurs. | Les presenter comme `Je ne sais pas encore` et `A decider`. |
| P1 | Justification metier absente pour restrictions. | Motif obligatoire pour `Reserve CS`, `Non diffusable`, et idealement `A masquer`. |
| P2 | Table dense et cartes detaillees font doublon. | Table pour le scan de lot; carte pour l'action sur une piece. |

## Recommandations classees par impact

1. Separer le parcours novice du tri de lot DocOps.
2. Garder le parcours novice en quatre decisions visibles: ajouter, qualifier, decider qui voit, rattacher.
3. Apres depot, envoyer le focus et la lecture screen-reader sur le premier document a completer.
4. Remplacer les libelles techniques visibles par des libelles humains:
   - `Depot local` -> `Ajouter depuis mon ordinateur`
   - `DocOps local` -> `Analyse locale du document`
   - `Confidentialite avant partage` -> `Qui pourra voir ce document ?`
   - `Point concerne` -> `Sujet concerne`
   - `Preuve attendue` -> `Ce que ce document doit prouver`
5. Faire de la prochaine action l'element dominant de chaque carte.
6. Ne jamais presenter classification, OCR ou hash comme validation juridique.
7. Replier les details techniques: empreinte complete, OCR, checklist longue et details de runtime.

## Images retenues

### Image retenue: atelier de qualification novice

- Chemin: `docs/assets/ux-ui-recherche-2026-05-24-ajout-docs/01-atelier-qualification-novice.svg`
- Statut: `retenue`
- Intention: une interface de qualification guidee, une piece active a la fois, avec file de documents a gauche, document actif au centre et decisions a droite.
- Decision associee: utiliser ce blueprint comme direction UX principale pour le parcours d'ajout de documents.
- Retour metier: GO conditionnel, a condition de verrouiller le vocabulaire de diffusion, les motifs et le recapitulatif.
- Retour novice/accessibilite: GO conditionnel, a condition de reduire les decisions initiales et de decouper le rattachement.

### Image rejetee mais instructive: tri DocOps par lot

- Chemin: `docs/assets/ux-ui-recherche-2026-05-24-ajout-docs/02-tri-docops-lot-rejete-instructif.svg`
- Statut: `rejetee mais instructive`
- Intention: vue en colonnes de confidentialite pour corriger beaucoup de documents apres passage DocOps.
- Decision associee: ne pas en faire le premier parcours novice; conserver comme variante de traitement de lot.
- Retour metier: utile pour dix documents ou plus si les justifications et gates privacy sont obligatoires.
- Retour novice/accessibilite: trop dense pour les 5 premieres minutes.

## Retours testeurs

### Testeur metier expert

Verdict: GO conditionnel sur le concept UX, NO-GO pour usage metier/probatoire reel sans verrouillage des regles de confidentialite.

Conditions:

- Confidentialite obligatoire avant sortie.
- Motif obligatoire pour `Reserve CS`, `Non diffusable` et idealement `A masquer`.
- Ne pas faire croire que le hash, l'OCR ou la classification prouvent le contenu.
- Traiter les documents mixtes: pages diffusables et pages sensibles dans un meme PDF.
- Garder une trace locale: acteur, date, hash, statut choisi, justification et rattachements.

### Testeur accessibilite / novice

Verdict: GO conditionnel sur la logique, NO-GO pour mise en main novice si l'ecran reste aussi dense.

Conditions:

- Une seule action primaire au depart: ajouter un fichier.
- Apres depot: confirmation claire et une seule prochaine etape.
- Aucun code technique au premier niveau.
- Rattachement decoupe en questions simples avec exemples.
- Parcours clavier et lecteur d'ecran lineaire, sans double lecture table plus cartes.
- Recapitulatif final: ajoute, confidentialite choisie, reste a faire.

## Decisions prises

- Direction retenue: atelier guide, une piece active a la fois.
- Variante conservee: tri DocOps par colonnes, mais seulement pour traitement de lot.
- Le mot "preuve" doit rester prudent: preferer "ce que ce document doit prouver" ou "preuve attendue".
- Le statut "pret" doit toujours dire "pret a enregistrer localement", pas "pret a partager".
- L'option "je ne sais pas encore" est une decision UX valide.
- Aucun dev n'est lance depuis cette recherche.

## Questions ouvertes

- Quels types documentaires afficher en premier sans produire une liste trop longue ?
- La justification doit-elle etre obligatoire aussi pour `A_BIFFER` / `A masquer` ?
- Quel extrait neutre est acceptable pour aider au tri sans exposer de contenu sensible ?
- Faut-il une session de traitement reutilisable pour auditer les corrections de lot ?
- Comment traiter un PDF dont seules certaines pages sont diffusables ?

## BOT-END

```text
BOT-END - Orchestrateur UX/UI - 2026-05-24 03:31 +02:00
Roadmap: RM-2026-0003 principal; liens RM-2026-0006, RM-2026-0010, RM-2026-0029.
Chantier: CH-20260524-032123-RM-2026-0003-ajout-docs-ux-ui
Conversation: CONV-2026-1313
Statut: CLOTURE
Fichiers modifies: docs/recherche_ux_ui_2026-05-24_ajout-docs.md; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs/01-atelier-qualification-novice.svg; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs/02-tri-docops-lot-rejete-instructif.svg; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs/.gitkeep; docs/presence_agents.md.
Fichiers volontairement evites: code applicatif, tests, instances privees, secrets, exports bruts, passerelles hors mission, RM-2026-0017 bloque.
Tests/preuves: syntheses Boole, Wegener, Bacon, Hegel et Bohr; deux blueprints SVG archives; aucune execution applicative car recherche sans dev.
Limites: pas de test navigateur ni modification UI; verdict produit = GO conditionnel recherche, pas GO livraison.
Questions ouvertes: types documentaires de premier niveau, justification `A masquer`, extraits neutres, session d'audit de lot, PDF partiellement diffusable.
Prochain mouvement propose: si Brice valide, ouvrir un chantier dev separe pour simplifier le parcours novice autour de l'atelier guide.
```

Aucun code applicatif n'a ete produit. Aucun serveur local n'a ete lance. Aucune instance privee n'a ete modifiee.

UXUI-DONE - equipe UX/UI a fini son job
