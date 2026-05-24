# Cycles refonte UX - Image -> Dev -> Test produit

> Statut gouvernail: `REFERENCE_ACTIVE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0003`, `RM-2026-0005`, `RM-2026-0006`). Ce protocole organise les cycles, il ne priorise pas seul.

Date de reference: 2026-05-21.

Ce document met en oeuvre le protocole de refonte UX issu des visuels
d'enquete utilisateur. Il sert de mode operatoire pour garder trois flux actifs
en permanence:

- une UI reelle livree a tester;
- un bloc en developpement;
- le visuel ou blueprint suivant en enquete.

Source de verite UX:

- `docs/assets/etude-utilisateurs/cockpit-conseil-syndical.png`
- `docs/assets/etude-utilisateurs/registre-decisions-actions-preuves.png`
- `docs/assets/etude-utilisateurs/controle-comptes-guide.png`
- `docs/assets/etude-utilisateurs/memoire-copropriete.png`

## Principe de pipeline

Le travail n'avance jamais en file unique. A chaque point de coordination, les
trois niveaux suivants doivent etre renseignes:

| Niveau | Objet | Owner principal | Sortie attendue |
|---|---|---|---|
| Cycle N-1 | Test du produit livre | QA + membre CS novice | Acceptation, corrections mineures ou retour dev |
| Cycle N | Developpement | Front + back/viewmodel | Route livree, tests cibles, limites connues |
| Cycle N+1 | Enquete sur image | Designer de service + membre CS novice | Commande dev validee pour le bloc suivant |

Objectif operationnel: les testeurs ont toujours quelque chose sous la dent
pendant que les devs travaillent, et les devs ont toujours une commande
stabilisee pendant que le designer prepare la suivante.

Regle obligatoire: le cycle ne part jamais d'une intention abstraite. Il nomme
une route, un ecran, une modale, un artefact HTML ou un parcours local. Si le
sujet est visuel, nouveau, ambigu ou sensible pour le novice, le designer
genere une image ou un blueprint et le membre CS novice le qualifie avant tout
developpement.

## Cadence obligatoire

Point de coordination toutes les 10 minutes, dans ce format exact:

- **A tester maintenant**: route livree, scenario novice, criteres critiques.
- **En dev maintenant**: bloc, owners front/back, risque principal.
- **En enquete maintenant**: image ou visuel recree, questions utilisateur.
- **Commande prete**: ticket dev valide pour le prochain bloc.
- **Decision requise**: arbitrage produit, UX, donnees ou securite.
- **Prochain mouvement**: action concrete avant le prochain point.

Le heartbeat Codex actif `coordination-refonte-ux-coproscope` utilise ce format.

## Definition d'un cycle

### 1. Enquete sur image

Entree:

- capture Canva existante ou visuel recree par le designer;
- contexte metier de copropriete;
- conclusions d'enquete utilisateur: preuve + action + memoire.

Deroule:

- le designer guide bouton par bouton, carte par carte, onglet par onglet;
- le membre CS novice dit ce qu'il croit pouvoir faire et ce qu'il attend au
  clic;
- le scribe capture attentes, confusions, mots naturels, parcours attendu.

Sortie:

- intention utilisateur confirmee;
- composants compris sans aide;
- composants a corriger;
- vocabulaire a utiliser et vocabulaire a bannir;
- parcours nominal et parcours d'echec;
- premiere version de la commande dev.

### 2. Commande dev

La commande dev est obligatoire avant tout developpement. Elle contient:

- objectif utilisateur;
- UI reelle cible: route, ecran, modale, artefact ou parcours;
- structure visuelle;
- composants;
- donnees necessaires;
- interactions;
- etats vides;
- criteres d'acceptation;
- tests attendus.

Le front et le back peuvent travailler en parallele seulement quand le contrat
`model.ux.*` du bloc est stabilise.

### 3. Developpement

Responsabilites:

- dev front: template Jinja, classes `cs-*`, responsive, accessibilite;
- dev back/viewmodel: projection `model.ux.*`, compteurs, listes, details,
  liens tokenises;
- QA: tests routes, securite, langage novice, DOM, responsive.

Garde-fous:

- ne pas inventer un visuel manquant cote dev;
- ne pas revenir a l'ancienne UX par facilite technique;
- ne pas afficher un compteur non cliquable;
- ne pas livrer une carte critique sans preuve/source, prochaine action et
  statut de diffusion;
- conserver les routes et protections token existantes.

### 4. Test du produit livre

Le test porte sur une route ou un ecran reel, jamais sur une intention abstraite.

Controle QA:

- route 200 avec token et refus correct sans token si attendu;
- liens internes tokenises;
- absence de fuite `raw`, `restricted`, `logs`, `file://`, chemin absolu prive;
- structure DOM attendue;
- langage novice;
- accessibilite minimale;
- comparaison visuelle par blocs avec l'image cible.

Controle membre CS novice:

- "je clique ici, je m'attends a voir cela";
- "je comprends pourquoi c'est la";
- "je sais quelle preuve manque ou existe";
- "je sais quoi faire maintenant";
- "je sais si je peux partager".

### 5. Cloture du bloc

Un bloc est accepte si:

- il ressemble au visuel cible par structure, densite et hierarchie;
- il repond au besoin metier;
- chaque compteur ou carte mene a une action utile;
- aucune fuite ou rupture token n'est detectee;
- le langage est comprehensible par un membre CS novice;
- les corrections restantes sont classees P2 ou documentees comme limites.

Un changement d'intention retourne au designer et relance une enquete image.
Une correction mineure retourne au dev du meme cycle.

## Pipeline initial

| Cycle | Enquete image | Dev | Test produit | Etat initial |
|---|---|---|---|---|
| 1 | Cockpit Canva | `/` Cockpit complet | Route `/` livree | Commande dev a lancer |
| 2 | Registre decisions/actions/preuves | `/actions` | Decision -> action -> preuve -> relance | Enquete parallele pendant dev cockpit |
| 3 | Controle comptes | `/comptes` | Anomalie -> question syndic -> preuve attendue | Enquete parallele pendant dev registre |
| 4 | Memoire copropriete | `/chantiers` affiche `Memoire de copropriete` | Evenement -> documents -> sujets ouverts -> passation | Enquete parallele pendant dev comptes |

Cycles suivants a designer avant dev:

- toutes les actions en retard;
- pieces manquantes;
- relance syndic;
- detail action;
- detail evenement memoire;
- export passation.

## Commande dev - Cycle 1 Cockpit complet

Objectif utilisateur:

- un membre de conseil syndical arrive sur CoproScope et sait en moins d'une
  minute quoi traiter, pourquoi, avec quelle preuve, et ou cliquer.

Structure visuelle:

- shell Canva: sidebar sombre fixe `276px`, topbar compacte `58px`, canvas clair;
- titre `Cockpit Conseil Syndical`;
- rang `A traiter` avec cinq cartes cliquables;
- quatre panneaux: pieces manquantes, demandes syndic, AG, controle comptes;
- table basse `Alertes et risques`.

Composants:

- `cs-shell`, `cs-sidebar`, `cs-topbar`, `cs-canvas`;
- `cs-kpi-card`, `cs-panel`, `cs-list-row`, `cs-badge`, `cs-data-table`;
- liens complets, focus visible, captions de table.

Donnees:

- `model.ux.cockpit.summary_cards`;
- `model.ux.cockpit.now`;
- `model.ux.cockpit.missing_pieces`;
- `model.ux.cockpit.syndic_followups`;
- `model.ux.cockpit.ag`;
- `model.ux.cockpit.accounting`;
- `model.ux.cockpit.risk_alerts`.

Interactions:

- chaque carte ouvre une liste ou une vue filtree;
- les liens conservent le token;
- les etats vides expliquent l'absence et proposent l'action suivante.

Tests attendus:

- route `/` 200 avec token;
- presence sidebar/topbar/cinq cartes;
- chaque carte a un `href` local;
- aucun jargon primaire non traduit;
- aucun marqueur prive;
- capture desktop comparee par blocs avec `cockpit-conseil-syndical.png`.

## Commande dev - Cycle 2 Registre

Objectif utilisateur:

- suivre une decision d'AG jusqu'a son action, sa preuve, sa relance et son
  historique.

Structure:

- liste AG/resolutions a gauche;
- fiche decision/action a droite;
- onglets `Action`, `Preuves`, `Pieces`, `Relance syndic`, `Historique`;
- timeline ou journal en bas.

Donnees:

- `model.ux.registre.items`;
- `model.ux.registre.selected`;
- `model.ux.registre.facets`;
- `model.ux.registre.journal`.

Acceptance:

- toute resolution ouverte montre responsable, echeance, statut humain,
  prochaine etape, preuve attendue et diffusion.

## Commande dev - Cycle 3 Controle comptes

Objectif utilisateur:

- transformer une anomalie ou incertitude comptable en question claire au
  syndic avant AG.

Structure:

- KPI en haut;
- categories au centre;
- inspecteur droit avec details, pieces et questions syndic.

Donnees:

- `model.ux.comptes.before_ag`;
- `model.ux.comptes.controls`;
- `model.ux.comptes.questions_syndic`;
- `model.ux.comptes.ag_brief`.

Acceptance:

- P1 signifie `a traiter`, P2 `a confirmer`, OK `conforme avec preuve`;
- chaque P1 a une action ou question syndic et une preuve attendue.

## Commande dev - Cycle 4 Memoire

Objectif utilisateur:

- comprendre l'histoire utile de la copropriete et transmettre les sujets
  ouverts au prochain conseil syndical.

Structure:

- timeline centrale;
- panneau `Passation CS`;
- liste `A transmettre`;
- fiche evenement ouverte au clic.

Donnees:

- `model.ux.memoire.timeline`;
- `model.ux.memoire.open_topics`;
- `model.ux.memoire.handover_checklist`;
- `model.ux.memoire.essential_proofs`;
- `model.ux.memoire.pack`.

Acceptance:

- un nouveau membre comprend les 10 evenements majeurs, les sujets ouverts, les
  preuves disponibles et les restrictions de diffusion.

## Roles de coordination

| Role | Responsibility | Output |
|---|---|---|
| Integrateur-scribe | tient le pipeline, tranche les owners, publie les points 10 min | registre a jour, commandes dev pretes |
| Designer service | enquete image, recree les visuels manquants | blueprint teste, commande UX |
| Membre CS novice | verbalise les attentes et confusions | criteres utilisateur |
| Dev front | shell, templates, CSS `cs-*` | route visible et accessible |
| Dev back/viewmodel | projection `model.ux.*` | donnees stables et token-safe |
| QA UX/visuelle | tests automatises et manuels | go/no-go bloc |

## No-go

- Aucun developpement ne demarre sans commande dev validee.
- Aucun developpement UI ne demarre sans UI reelle cible.
- Une UI nouvelle, visuelle, dense ou sensible part en dev sans image/blueprint
  designer qualifie par le novice.
- Testeur teste une maquette au lieu d'une route livree.
- Designer laisse les devs inventer une vue manquante.
- Un compteur n'ouvre rien.
- Une relance ne dit pas si elle est envoyee, copiee ou seulement tracee.
- Une page promet sync cloud, conseil juridique ou diffusion publique non
  controles.
