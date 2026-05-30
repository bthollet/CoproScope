# Registre cycles refonte UX

> Statut gouvernail: `JOURNAL_TRACE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0003`, `RM-2026-0005`, `RM-2026-0006`). Les nouvelles vagues passent par le gouvernail.

Date de creation: 2026-05-21.
Derniere mise a jour: 2026-05-21 21:24 +02:00.

Ce registre suit le pipeline `Enquete -> Commande -> Dev -> Test produit` de la
refonte UX CoproScope. Il est le support des points d'avancement toutes les 10
minutes et la table de coordination des 6 agents actifs en cadence quinconce:
pendant que le Cycle N est en dev, le Cycle N-1 est teste, le Cycle N+1 est
commande et le Cycle N+2 est enquete.

Cycle 8 est ouvert comme anticipation produit fini apres Cycle 7: il ne lance
pas de code applicatif, il ordonne les vues, contrats et tests restants dans
`docs/archive/roadmaps_anciennes/backlog_produit_fini_refonte_ux.md`.

## Regle interconversations obligatoire

Chaque agent actif doit appliquer `docs/consignes_bots_interconversations.md`
avant de toucher au code, aux passerelles ou au registre. Le point de cycle doit
permettre d'identifier son role, son ownership, sa passerelle de trace, les
fichiers evites et le dernier point de coordination lu. Sans cette declaration,
l'agent reste en lecture seule ou demande un arbitrage.

## Configuration 6 agents

| Agent | Role | Flux principal | Etat courant | Sortie attendue au prochain point |
|---|---|---|---|---|
| Front Memoire | Templates `/chantiers`, memoire, passation, responsive | Cycle 4 | EN_DEV_FRONT | Premiere tranche Memoire visible et testable |
| Back vues manquantes | Contrats `model.ux.*`, inventaire vues, donnees synthetiques | Cycle 5 | EN_DEV_BACK | Vues manquantes priorisees et contrat testable |
| QA/Test produit | Routes reelles, securite token, langage novice, comparaison visuelle | Base 24 verts + nouvelles tranches | EN_QA | Go/no-go par route reelle; Memoire des que visible |
| Designer Cycle 8 | Enquete produit fini, blueprint, vocabulaire utilisateur | Cycle 8 | COMMANDE_PRETE | Commande `Cycle 8A - Boite de reprise` disponible pour reprise front/back |
| Novice transversal | Tests continus de comprehension, mots naturels, attentes au clic | Cycles 4 a 8 | EN_QA / EN_ENQUETE | Novice peripherique relance: no-go vocabulaire/attentes au clic sur Memoire, vues manquantes, demandes et Cycle 8A |
| Coordinateur | Cadence, registre, decisions, anti-idle, passage de relais | Tous flux | Cadence active | Point 10 min publie, blocages, roles idle et prochain mouvement traces |

## Point d'avancement maintenant - 2026-05-21 06:27 +02:00

Etat reel connu a integrer: 33 tests UX principaux verts. Les demandes ont ete
nettoyees des chemins locaux, `base.html` est rendu robuste aux vues isolees, et
le lot peripherique est presque vert. Seule correction active connue:
`/actions?status=a_demander` avec selection vide. Les couloirs Memoire front,
vues manquantes back et QA restent actifs; Designer Cycle 8 a livre la commande
`Cycle 8A - Boite de reprise`; novice peripherique est relance.

| Flux | Etat reel connu | Owner actif | Sortie attendue avant prochain point |
|---|---|---|---|
| Livre/test | 33 tests UX principaux verts; demandes nettoyees des chemins locaux; `base.html` robuste aux vues isolees | QA routes reelles + novice tests continus | Conserver cette base comme reference regression et signaler seulement les ecarts P0/P1/P2 constates sur routes reelles |
| Lot peripherique | Quasiment vert; correction en cours sur `/actions?status=a_demander` quand aucune action n'est selectionnee | QA peripherique + dev Registre au besoin | Relancer le lot peripherique apres correction et fermer le point Registre selection vide |
| En dev front | Cycle 4 front Memoire toujours actif | Front Memoire | Premiere tranche `/chantiers` visible: memoire, passation, sujets ouverts, liens locaux token-safe |
| En dev back | Cycle 5 back vues manquantes toujours actif | Back vues manquantes | Inventaire priorise et contrats `model.ux.*` des vues manquantes, avec donnees synthetiques testables |
| En enquete / commande | Designer Cycle 8 a livre `Cycle 8A - Boite de reprise`; novice peripherique relance | Designer Cycle 8 + novice transversal | Servir Cycle 8A au premier couloir libre; produire no-go utilisateur si reprise, preuve, action ou diffusion restent floues |
| Commande prete | Cycle 4 Memoire en cours; Cycle 6 Pieces manquantes reste en file; Cycle 8A Boite de reprise disponible | Coordinateur + designer | Donner une commande courte a chaque couloir libere, sans laisser d'agent attendre |
| Decisions requises | Aucun arbitrage bloquant hors correction Registre selection vide | Coordinateur + QA | Produire go/no-go du lot peripherique apres `/actions?status=a_demander`; produire go/no-go Memoire des que la tranche front est visible |
| Prochain mouvement | Verrouiller la correction Registre selection vide, relancer QA peripherique, maintenir front Memoire/back vues manquantes/QA actifs, distribuer Cycle 8A au premier role libre | Tous couloirs | Tout role termine prend la premiere commande du backlog court ci-dessous |

## Prochaines commandes dev anti-idle

| Priorite | Commande prete | Couloir | Declencheur | Sortie attendue |
|---:|---|---|---|---|
| 1 | Cycle 4 Memoire `/chantiers` - tranche front | Front | Front disponible ou renfort front Memoire | Timeline/passation/sujets ouverts responsive, token-safe, sans jargon primaire |
| 2 | Cycle 4 Memoire `model.ux.memoire` | Back | Back libere apres tranche Cycle 5 ou besoin front Memoire | Contrat memoire, evenements, preuves, restrictions et liens token-safe |
| 3 | Cycle 5 vues manquantes | Back puis front | Back Cycle 5 deja lance; front prend la premiere vue des que le contrat est nomme | Vue prioritaire parmi coffres, droits, demandes detaillees, AG ou pilotage, avec test route reelle |
| 4 | Correction Registre selection vide `/actions?status=a_demander` | Dev Registre + QA | Lot peripherique presque vert mais bloque sur ce cas | Etat vide sans erreur, selection par defaut explicite, hrefs locaux token-safe |
| 5 | QA routes reelles et lot peripherique | QA navigateur | A chaque livraison front/back et apres correction Registre | Parcours Cockpit -> Registre -> Docs -> Comptes -> Memoire + lot peripherique, captures/ecarts P0/P1/P2 |
| 6 | Cycle 6 Pieces manquantes `/pieces?proof=missing` | Front/back | Premier couloir libere apres Memoire ou Cycle 5 | Ligne piece manquante actionnable: demander, lier, prouver, verifier anti-fuite |
| 7 | Cycle 8A - Boite de reprise | Front/back + novice | Premier couloir libre apres correction ou tranche Memoire/Cycle 5 | Boite de reprise actionnable, vocabulaire novice, preuves/actions/diffusion explicites |

## Commandes pretes a diffuser

Ces commandes sont documentaires: elles servent a relancer les roles sans
toucher au code depuis ce point de coordination.

```text
Front Memoire:
Continuer Cycle 4 `/chantiers`; livrer la premiere tranche visible Memoire +
passation + sujets ouverts, responsive, liens locaux token-safe, sans chemins
locaux ni jargon primaire.

Back vues manquantes:
Continuer Cycle 5; nommer l'inventaire priorise et les contrats `model.ux.*`
testables pour coffres, droits, demandes detaillees, AG ou pilotage.

QA peripherique:
Apres correction `/actions?status=a_demander`, relancer le lot peripherique et
publier GO/NO-GO en isolant les ecarts P0/P1/P2.

Designer/novice:
Servir `Cycle 8A - Boite de reprise` au premier couloir libere; no-go novice si
la reprise, l'action suivante, la preuve ou la diffusion ne sont pas evidentes.
```

## Agents actifs

| Agent actif | Cycle pilote | Etat reel | Mission immediate | Prochain mouvement si le role finit |
|---|---|---|---|---|
| front Memoire | Cycle 4 | EN_DEV_FRONT | Livrer la premiere tranche `/chantiers`: memoire, passation, sujets ouverts, responsive et liens token-safe | Basculer sur Cycle 5 premiere vue manquante ou Cycle 6 pieces manquantes selon contrat disponible |
| back vues manquantes | Cycle 5 | EN_DEV_BACK | Nommer l'inventaire priorise et les contrats `model.ux.*` des vues manquantes | Basculer sur `model.ux.memoire` si front Memoire a besoin de contrat, sinon Cycle 6 pieces manquantes |
| QA/Test produit | QA routes reelles | EN_QA | Verifier la base 33 tests UX principaux verts et ouvrir les parcours reels Cockpit/Registre/Docs/Comptes/Demandes/Memoire | Basculer sur go/no-go lot peripherique, Memoire, puis tests Cycle 5 |
| designer Cycle 8 | Cycle 8A | COMMANDE_PRETE | Commande `Cycle 8A - Boite de reprise` livree | Servir Cycle 8A au premier couloir libre puis preparer l'item suivant du backlog produit fini |
| novice transversal | Tests continus peripheriques | EN_QA / EN_ENQUETE | Relire routes livrees, demandes nettoyees, correction Registre selection vide, Memoire, vues manquantes et Cycle 8A en mots utilisateur | Produire no-go vocabulaire ou attentes au clic pour Memoire, vues manquantes et boite de reprise |
| coordinateur | Tous cycles | Cadence active | Tenir registre, backlog produit fini, anti-idle, remplacement des roles sortants | Rebasculer tout role termine dans le meme couloir sur le cycle suivant |

## Roles idle / reserve anti-idle

Principe: un role est dit idle uniquement s'il n'a pas encore de livrable route,
contrat ou test dans le point courant. Il doit alors prendre automatiquement la
premiere sortie disponible du meme couloir, sans toucher au code applicatif tant
que la commande n'est pas prete.

| Role de reserve | Etat | Reprise automatique | Sortie attendue |
|---|---|---|---|
| Front Cycle 5/6 | IDLE_SUR_COMMANDE | Prendre la premiere vue manquante ou Pieces manquantes si le front Memoire finit | Route visible et responsive, avec detail ou action claire |
| Back Memoire/Cycle 6 | IDLE_SUR_COMMANDE | Prendre `model.ux.memoire` si Memoire bloque, sinon contrat Pieces manquantes | Contrat token-safe avec preuves, restrictions et donnees synthetiques |
| QA navigateur | IDLE_SUR_ROUTE | Tester routes reelles puis Memoire/Cycle 5 des livraison exploitable | Go/no-go par route reelle, captures et P0/P1/P2 |
| Designer produit fini | IDLE_SUR_DEV | Tenir Cycle 8A comme commande de reprise active | Commande `Cycle 8A - Boite de reprise` servie au premier role libre |
| Novice produit fini | IDLE_SUR_DEV | Relire les libelles et attentes au clic du backlog Cycle 8A et des routes livre/test | No-go utilisateur explicite si reprise/preuve/action/diffusion floues |
| Coordinateur reserve | IDLE_INTERDIT | Replacer tout role termine avant le point suivant | Point 10 min sans champ vide et role idle remplace |

## Decalage de cycle

| Decalage | Fonction | Cycle actuel | Agents responsables | Sortie attendue |
|---|---|---|---|---|
| Livre/test | Fermer le bloc precedent sans bloquer les suivants | Cockpit + Registre + Docs + Comptes + demandes/base isolee | QA routes reelles + coordinateur | Base 33 tests UX principaux verts conservee |
| QA courante | Tester les routes reelles et les nouvelles tranches | Base verte puis Memoire | QA/Test produit + novice transversal | Go/no-go par route reelle |
| Dev front | Produire le bloc front en cours | Cycle 4 Memoire copropriete | front Memoire | Tranche `/chantiers` testable |
| Dev back | Produire le bloc back en cours | Cycle 5 vues manquantes | back vues manquantes | Contrats/inventaire testables |
| Commande prete | Garder une commande exploitable pour le prochain role libre | Cycle 6 Pieces manquantes | designer + coordinateur | Commande Cycle 6 prete |
| Enquete active | Preparer le produit fini sans toucher au code applicatif | Cycle 8 Produit fini | designer Cycle 8 + novice transversal | Backlog ordonne vues/contrats/tests pret a servir les roles liberes |

## Flux permanent en quinconce

| Niveau | Objet | Cycle courant | Agents moteurs | Statut | Sortie attendue |
|---|---|---|---|---|---|
| Livre/test | Base acceptee | Cockpit + Registre + Docs + Comptes + demandes/base isolee | QA routes reelles + novice transversal | ACCEPTE / EN_QA | 33 tests UX principaux verts conserves comme reference regression |
| Dev front | Bloc en cours | Cycle 4 - Memoire copropriete `/chantiers` | front Memoire | EN_DEV_FRONT | Tranche Memoire visible et testable |
| Dev back | Bloc en cours | Cycle 5 - vues manquantes | back vues manquantes | EN_DEV_BACK | Inventaire et contrats `model.ux.*` testables |
| QA routes | Test produit courant | Routes reelles, puis Memoire des livraison | QA/Test produit | EN_QA | Go/no-go par clics, tokens, anti-fuite et jargon primaire |
| Commande d'avance | Commande prete | Cycle 6 - Pieces manquantes `/pieces?proof=missing` | designer + coordinateur | COMMANDE_PRETE | Commande Cycle 6 prete a prendre |
| Enquete active | Anticipation produit fini | Cycle 8 - backlog produit fini | coordinateur + designer Cycle 8 + novice transversal | EN_ENQUETE | Ordre vues, contrats, detail piece/preuve, diffusion, export, tests navigateur maintenu |

## Tableau de flux

| Flux | Bloc courant | Owner | Statut | Sortie attendue |
|---|---|---|---|---|
| Livre/test maintenant | 33 tests UX principaux verts; demandes nettoyees des chemins locaux; `base.html` robuste aux vues isolees | QA routes reelles + novice transversal | ACCEPTE / EN_QA | Base regression conservee, ecarts uniquement par routes reelles P0/P1/P2 |
| Lot peripherique maintenant | Quasiment vert sauf `/actions?status=a_demander` selection vide en correction | QA peripherique + dev Registre | CORRECTION / EN_QA | Relancer le lot peripherique apres correction et publier GO/NO-GO |
| En dev maintenant | Cycle 4 front Memoire `/chantiers`; Cycle 5 back vues manquantes | front Memoire + back vues manquantes | EN_DEV_FRONT / EN_DEV_BACK | Tranche Memoire visible et contrats vues manquantes nommes |
| QA en cours maintenant | QA routes reelles et peripheriques lancee sur la base verte et les nouvelles tranches | QA/Test produit | EN_QA | Go/no-go Registre peripherique, Memoire puis Cycle 5 par clics/routes reelles |
| Commande maintenant | Cycle 4 Memoire exploite en front; Cycle 6 Pieces manquantes reste pret; Cycle 5 est pris en back; Cycle 8A Boite de reprise est livre | designer + coordinateur | COMMANDE_PRETE / EN_DEV_BACK | Servir la prochaine commande courte a chaque couloir libere |
| Preparation suivante | Cycle 8A - Boite de reprise | designer Cycle 8 + novice transversal | COMMANDE_PRETE | Commande exploitable et criteres novice prets, sans code applicatif |
| Anticipation produit fini | Backlog produit fini apres Cycle 7 | coordinateur + designer Cycle 8 + novice transversal | FILE_ATTENTE / EN_ENQUETE | Detail piece/preuve, diffusion, export et tests navigateur prets a distribuer |
| Commande reference | Cycle 2 - Registre decisions/actions/preuves | Designer service + integrateur-scribe | PRETE | Voir `docs/commandes/commande_cycle2_registre_actions_preuves.md` |
| Decision requise | Aucun arbitrage bloquant identifie | Coordinateur + QA | OUVERT | Go/no-go Memoire attendu des que la route visible existe |

## Vague actuelle

| Cycle | Etat de vague | Coordination immediate |
|---:|---|---|
| 1 | Cockpit livre/test | Inclus dans la base connue 33 tests UX principaux verts |
| 2 | Registre livre/test | Inclus dans la base connue 33 tests UX principaux verts; garder `/actions` comme route temoin et corriger `/actions?status=a_demander` selection vide |
| 3 | Comptes livre/test | Inclus dans la base connue 33 tests UX principaux verts; ne plus bloquer les couloirs dev |
| Docs | Docs livre/test | Inclus dans la base connue 33 tests UX principaux verts; surveiller en regression routes reelles |
| 4 | Memoire front lance | Front livre `/chantiers`; QA prepare go/no-go route reelle |
| 5 | Vues manquantes back lance | Back nomme contrats et inventaire priorise pour servir front ensuite |
| 6 | Pieces manquantes commande prete | Rester en file de commande apres Cycle 5 |
| 7 | Relance syndic en file design/reference | Ne relancer que si une commande courte explicite est demandee |
| 8 | Designer Cycle 8A livre | Commande `Cycle 8A - Boite de reprise` disponible; tenir l'item suivant du backlog produit fini |

## Volée d'instructions active

| Agent | Couloir | Tâche courante | Tâche suivante automatique |
|---|---|---|---|
| Front Memoire | front en dev | Livrer Cycle 4 `/chantiers` avec memoire, passation, sujets ouverts et responsive | Basculer Cycle 5 premiere vue manquante ou Cycle 6 pieces manquantes |
| Back vues manquantes | back en dev | Lancer Cycle 5: inventaire vues manquantes, contrats `model.ux.*`, donnees synthetiques testables | Basculer `model.ux.memoire` si Memoire bloque, sinon Cycle 6 |
| QA/Test produit | QA routes reelles | Verifier base 33 tests UX principaux verts et tester les routes reelles nouvelles | Basculer au lot peripherique corrige, puis au premier livrable Memoire et Cycle 5 |
| Designer Cycle 8 | commande produit fini | `Cycle 8A - Boite de reprise` livre et pret a distribuer | Servir Cycle 8A aux roles liberes puis preparer detail piece/preuve, diffusion, export ou tests navigateur |
| Novice transversal | tests continus peripheriques | Relire routes livrees, demandes nettoyees, Memoire, vues manquantes et Cycle 8A en langage utilisateur | Produire no-go vocabulaire/attentes au clic pour chaque nouvelle tranche |
| Coordinateur | coordinateur | Tenir registre, backlog produit fini, point 10 min, anti-idle et passage de relais | Rebasculer tout agent termine dans le meme couloir sur le cycle suivant |

## Cycles

| Cycle | Bloc | Image/visuel | Route | Etat | Critere de sortie |
|---:|---|---|---|---|---|
| 1 | Cockpit conseil syndical | `cockpit-conseil-syndical.png` | `/` | GO_CIBLE | Cockpit GO; un novice sait quoi traiter en moins d'une minute |
| 2 | Registre decisions/actions/preuves | `registre-decisions-actions-preuves.png` | `/actions` | ACCEPTE | Registre tests OK; action, preuve, relance et historique restent surveilles |
| 3 | Controle comptes guide | `controle-comptes-guide.png` | `/comptes` | ACCEPTE / TESTS_VERTS | Une anomalie devient une question syndic claire; inclus dans les 33 tests UX principaux verts connus |
| 4 | Memoire copropriete | `memoire-copropriete.png` | `/chantiers` | EN_DEV_FRONT | Un nouveau CS comprend historique, sujets ouverts et passation |
| 5 | Vues manquantes apres Memoire | Inventaire priorise | `A_DEFINIR` | EN_DEV_BACK | Premiere vue manquante priorisee avec blueprint et criteres QA |
| 6 | Pieces manquantes | Commande prete | `/pieces?proof=missing` | COMMANDE_PRETE | Demander ou lier une piece depuis chaque ligne |
| 7 | Relance syndic | Design en cours | `/demandes` | EN_ENQUETE | Message prepare, statut d'envoi ou copie explicite |
| 8 | Anticipation produit fini apres Cycle 7 | Backlog ordonne | `docs/archive/roadmaps_anciennes/backlog_produit_fini_refonte_ux.md` | COMMANDE_PRETE | `Cycle 8A - Boite de reprise` livre; vues, contrats et tests manquants priorises sans toucher au code applicatif |
| 9 | Detail piece/preuve | Visuel a recreer | `/pieces?selected=...` ou `/documents?selected=...` | FILE_ATTENTE | Fiche piece/preuve avec apercu, rattachements, historique et diffusion |
| 10 | Detail action/memoire | Captures finales cycle memoire | `/actions/{id}` et `/chantiers/{event_id}` | ACCEPTE / EN_QA | Decision/action/evenement relie aux documents, preuves et restrictions, avec etats introuvables token-safe |
| 11 | Arbitrage diffusion | Visuel a recreer | `/privacy?review=...` | FILE_ATTENTE | Dire qui peut voir, sous quelle forme, et bloquer les bruts interdits |
| 12 | Export passation | `10_export_passation_n2_apercu_verifiable.png` | `/exports/passation.*` | LIVRE_2026-05-21_21:30 | Apercu verifiable, restrictions, pack derive non source de verite, TXT/JSON tokenises |
| 13 | Tests navigateur produit fini | Scenario a ecrire | Routes reelles desktop/mobile/tablette | FILE_ATTENTE | Parcours bout-en-bout verifie par clics, captures et absence de chevauchement |

## Backlog produit fini - Cycle 8

Source detaillee: `docs/archive/roadmaps_anciennes/backlog_produit_fini_refonte_ux.md`.

| Ordre | Objet | Vue/contrat/test manquant | Role qui peut prendre si libere |
|---:|---|---|---|
| 1 | Comptes | Detail ligne, synthese AG, `model.ux.comptes`, tests route/filtres/export | Front/back si reprise detail, QA regression |
| 2 | Memoire | Timeline passation, `model.ux.memoire`, tests sujets ouverts/preuves/restrictions | Front Memoire, Back Memoire, QA |
| 3 | Vues manquantes | Mes coffres, droits, demandes detaillees, AG, pilotage injecte | Designer, Front, Back |
| 4 | Detail piece/preuve | Fiche detail, `model.ux.piece_detail`, tests clic ligne et anti-fuite raw | Front, Back, QA navigateur |
| 5 | Arbitrage diffusion | Revue de diffusion, `model.ux.diffusion_review`, tests blocage export | Privacy/Comms, QA, novice |
| 6 | Export passation | Apercu pack derive, `PassationPack`, tests restrictions/source_of_truth false | Passation, Back, QA |
| 7 | Tests navigateur | Scenario cockpit -> comptes -> memoire -> piece -> diffusion -> passation | QA navigateur, novice, coordinateur |

## Journal de coordination

| Date | Point | A tester maintenant | En dev maintenant | En enquete maintenant | Decision | Prochain mouvement |
|---|---|---|---|---|---|---|
| 2026-05-21 | Initialisation | Aucun bloc nouveau livre | Cycle 1 Cockpit a lancer | Cycle 2 Registre a lancer | Pas de blocage | Demarrer `model.ux.cockpit` puis shell `cs-*` |
| 2026-05-21 | Cycle 2 pret | Aucun bloc nouveau livre | Cycle 1 Cockpit en cours | Cycle 3 Controle comptes a lancer | Pas de blocage | Integrer Cockpit puis lancer dev `/actions` apres QA Cycle 1 |
| 2026-05-21 | Configuration 6 agents | QA Cockpit/Registre | Front Cockpit en cours, Back Cycle 2 a lancer | Design Cycle 3 en cours, user novice mobilise | Go/no-go a produire au point 10 min | Publier point cadence, livrer Cockpit, lancer `model.ux.registre` |
| 2026-05-21 | Quinconce 6 agents anti-idle | N-1: QA Cockpit + Registre disponible | N: front/back Registre `/actions` | N+1: commande Comptes, N+2: enquete Memoire | Aucun agent ne reste idle apres livraison | Remplacer tout agent termine par cycle suivant ou QA/doc du prochain cycle |
| 2026-05-21 01:02 +02:00 | Vague actuelle anti-idle | Cycle 1 Cockpit GO cible; Cycle 2 Registre QA apres correction | Cycle 3 Comptes front/back en cours avec QA partielle | Cycle 4 Memoire design + novice; Cycle 5 vues manquantes en preparation | Aucun idle attendu; bascule meme couloir obligatoire | Rejouer Registre, avancer Comptes, convertir Memoire en commande |
| 2026-05-21 06:08 +02:00 | Correction coordination anti-idle | Cockpit GO; Registre tests OK; Cycle 3 Comptes en reprise QA | Cycle 3 Comptes reprise front/back | Cycle 7 design en cours; Memoire + Cycles 5/6 commandes pretes | Ajouter alias historique `ENQUETE_A_LANCER` sans changer le statut canonique `EN_ENQUETE` | Finir reprise Comptes; lancer Memoire des qu'un couloir front/back/QA se libere |
| 2026-05-21 06:12 +02:00 | Cycle 8 anticipation produit fini | Cycle 3 Comptes reste a tester; Cockpit/Registre en regression | Cycle 3 Comptes reprise front/back | Cycle 7 design; Cycle 8 backlog produit fini ouvert | Aucun code applicatif a toucher pour Cycle 8; backlog documentaire seulement | Servir aux roles liberes l'ordre Comptes, Memoire, vues, detail piece/preuve, diffusion, export, tests navigateur |
| 2026-05-21 06:18 +02:00 | Double flux anti-idle | 24 tests verts Cockpit + Registre + Docs + Comptes; QA routes reelles lancee | Cycle 4 front Memoire lance; Cycle 5 back vues manquantes lance | Designer Cycle 8 lance; novice tests continus lance | Aucun arbitrage bloquant; go/no-go Memoire attendu par route reelle | Avancer Memoire/front, vues/back, QA routes; servir le backlog court a tout role libere |
| 2026-05-21 06:27 +02:00 | Point courant anti-idle | 33 tests UX principaux verts; demandes nettoyees des chemins locaux; `base.html` robuste vues isolees; lot peripherique presque vert sauf `/actions?status=a_demander` selection vide | Cycle 4 front Memoire actif; Cycle 5 back vues manquantes actif; correction Registre selection vide en cours | Designer Cycle 8 a livre `Cycle 8A - Boite de reprise`; novice peripherique relance | Aucun arbitrage bloquant hors correction Registre; QA doit relancer le lot peripherique apres correction | Fermer `/actions?status=a_demander`, relancer QA peripherique, maintenir Memoire/back vues/QA, distribuer Cycle 8A au premier role libre |
| 2026-05-21 21:13 +02:00 | Final cycle memoire, export passation suivant | 34 tests cibles OK; suite UI complete 155 OK; captures finales dans `docs/assets/ux-livraison-reelle-2026-05-21-8766-final-cycle-memoire/` | Cycle N export passation apercu verifiable a lancer front/back | Designer image N+1 sur `10_export_passation_n2_apercu_verifiable.png`; QA/novice ferment N-1 | Arbitrer GO final memoire et comportement principal de `/exports/passation` | Fermer tests N-1 puis lancer `/exports/passation` en apercu HTML token-safe |

## Point 10 minutes actuel - 2026-05-21 06:27 +02:00

| Champ | Etat actuel | Actions avant prochain point |
|---|---|---|
| Livre/test maintenant | 33 tests UX principaux verts; demandes nettoyees des chemins locaux; `base.html` robuste aux vues isolees | QA routes reelles conserve cette base comme regression et note seulement les ecarts P0/P1/P2 |
| Lot peripherique maintenant | Quasiment vert; correction en cours sur `/actions?status=a_demander` quand aucune selection n'existe | Relancer le lot peripherique immediatement apres correction et publier GO/NO-GO |
| En dev maintenant | Cycle 4 front Memoire actif; Cycle 5 back vues manquantes actif | Front livre `/chantiers`; back nomme contrats/inventaire vues manquantes |
| En enquete maintenant | Designer Cycle 8 a livre `Cycle 8A - Boite de reprise`; novice peripherique relance | Servir Cycle 8A au premier role libre; novice publie no-go si reprise/preuve/action/diffusion floues |
| Commande prete | Cycle 4 Memoire en execution front; Cycle 6 Pieces manquantes reste pret; Cycle 5 est pris cote back; Cycle 8A est pret | Servir une commande courte au prochain front/back/QA libere |
| Roles idle | Aucun role ne doit attendre: chaque couloir a une sortie horodatable | Front -> Memoire/Cycle 5/Cycle 6/Cycle 8A; back -> Cycle 5/Memoire/Cycle 6/Cycle 8A; QA -> lot peripherique/routes reelles; designer/novice -> item Cycle 8 suivant |
| Decisions requises | Correction Registre selection vide a fermer; aucun autre arbitrage bloquant identifie | Go/no-go lot peripherique apres correction; go/no-go Memoire des que la route visible existe; no-go immediat si fuite privee, rupture token, chemin local ou jargon primaire |
| Go/no-go | GO base 33 tests UX principaux verts; NO-GO cible uniquement sur `/actions?status=a_demander` selection vide tant que la correction n'est pas relancee; Memoire et Cycle 5 restent actifs | Publier decision explicite par route reelle, pas par intention |
| Prochain mouvement | Fermer `/actions?status=a_demander`, relancer QA peripherique, maintenir front Memoire/back vues manquantes/QA routes, distribuer `Cycle 8A - Boite de reprise` au premier role libre | Tout role termine prend la premiere ligne disponible dans `Prochaines commandes dev anti-idle` |

## Point 10 minutes courant - 2026-05-21 21:13 +02:00

| Champ | Etat actuel | Actions avant prochain point |
|---|---|---|
| A tester maintenant | Cycle memoire/actions/pieces/relance livre sur live `8766`, PID `7352`, health OK; `34 tests cibles OK`; suite UI complete `155 tests OK` | QA + novice ferment le N-1 sur routes reelles et captures finales |
| En dev maintenant | Cycle N a lancer: export passation avec apercu verifiable | Front/back livrent `/exports/passation` comme apercu HTML, avec liens `/exports/passation.txt` et `/exports/passation.json` token-safe |
| En enquete maintenant | Cycle N+1: image export passation | Designer/service s'appuie sur `docs/assets/ux-visuels-fictifs-2026-05-21/10_export_passation_n2_apercu_verifiable.png` et garde `06_export_passation.png` comme reference courte |
| Commande prete | Export passation: pack derive, sections incluses/exclues, restrictions, watermark, absence de bruts prives | Convertir cette commande en criteres front/back + QA avant changement applicatif |
| Roles idle | Aucun role ne doit attendre | QA/novice testent N-1; front/back prennent N; designer image prend N+1; coordinateur consigne les decisions |
| Go/no-go | GO technique possible sur memoire/actions/pieces/relance; GO utilisateur a confirmer par test novice final | Publier GO/NO-GO explicitement apres les points exacts ci-dessous |
| Prochain mouvement | Lancer le double flux export passation sans toucher aux routes deja vertes | N-1 QA/novice, N dev front/back, N+1 designer image |

## Cycle suivant - Export passation apercu verifiable

| Flux | Agents | Travail | Critere de sortie |
|---|---|---|---|
| N-1 test | QA + membre CS novice | Routes actions/comptes/relance/pieces/memoire/export actuel | Toutes les routes listees ci-dessous verifiees en live, sans fuite ni rupture token |
| N dev | Front + back | `/exports/passation` devient l'apercu HTML avant telechargement | Apercu lisible, sections incluses/exclues, restrictions, watermark derive, liens TXT/JSON token-safe |
| N+1 image | Designer service + designer visuel/data | Image cible export passation | Image/commande valides avant iterations front/back suivantes |

### Points exacts a tester

- `GET /actions/__COPROSCOPE_TEST_ACTION_MISSING_999__?token=local-secret` puis `GET /actions?action_missing=__COPROSCOPE_TEST_ACTION_MISSING_999__&token=local-secret`.
- `GET /actions?scope=comptes&token=local-secret`.
- `GET /demandes/relance?token=local-secret&request_id=REQ-FICTIF-ASSURANCE-B12`.
- `GET /pieces?proof=missing&token=local-secret`.
- `GET /chantiers?token=local-secret`.
- `GET /chantiers/{event_id}?token=local-secret`, avec `{event_id}` releve dans la timeline live.
- `GET /chantiers/MEM-UNKNOWN-404?token=local-secret`.
- `GET /chantiers/C:%5CUsers%5Cbrice%5Craw%5Cmemoire-privee.pdf?token=local-secret`.
- `GET /exports/passation?token=local-secret&scope=event&selected=MEM-DOC-7D412766`.
- `GET /exports/passation.json?token=local-secret`.
- `GET /exports/passation.txt?token=local-secret`.

### Decisions requises

- Valider ou non le GO final memoire/actions/pieces/relance avec `34 tests cibles OK`, `155 tests UI OK` et captures finales.
- Choisir si `/exports/passation` devient l'apercu HTML principal ou reste une redirection texte.
- Choisir le scope par defaut: passation globale conseil syndical ou evenement selectionne.
- Confirmer les formats exposes: TXT + JSON minimum; Markdown uniquement avec test anti-fuite dedie.
- Confirmer que les exclusions de diffusion sont visibles dans l'apercu mais jamais exportees comme sources brutes.

## Format du point d'avancement 10 minutes

Chaque point doit etre publie dans ce format, sans champ vide:

```text
Point 10 min - HH:MM
A tester maintenant:
En dev maintenant:
En enquete maintenant:
Commande prete:
Decision requise:
Go/no-go:
Prochain mouvement:
```

Regles de cadence:

- `A tester maintenant` pointe toujours vers une route reelle livree ou dit
  explicitement `A_ATTENDRE`.
- `En dev maintenant` separe le front et le back quand leurs etats divergent.
- `En enquete maintenant` maintient le Cycle N+1 actif meme si le Cycle N bloque.
- `Cadence quinconce` garde au moins quatre plans ouverts: N-1 test, N dev,
  N+1 commande, N+2 enquete; Cycle 8 ajoute une anticipation produit fini sans
  lancer de code applicatif.
- `Anti-idle`: quand un agent termine son livrable, il est immediatement
  remplace par le cycle suivant; s'il ne peut pas prendre le dev suivant, il
  bascule sur QA/doc du prochain cycle avec une sortie horodatable.
- `Decision requise` nomme un arbitre et une heure limite quand le statut est
  `BLOQUE`.
- `Prochain mouvement` tient en une action executable avant le point suivant.

## Criteres go/no-go

| Decision | Go | No-go |
|---|---|---|
| Lancer dev front/back | Commande dev validee, image ou blueprint disponible, contrat `model.ux.*` nomme | Vue inventee par les devs, donnees non stabilisees, criteres absents |
| Passer en QA | Route livree, token conserve, tests cibles executables, limites connues | Route non accessible, liens morts, compteur sans destination, erreur serveur |
| Accepter bloc | Besoin novice compris, preuve/action visibles, aucune fuite privee, ecarts P2 documentes | Fuite `raw`/`restricted`/chemin prive, rupture token, jargon primaire, action impossible |
| Lancer cycle suivant | Cycle N a une commande claire et Cycle N+1 a une enquete active | Plus de commande prete, image manquante non assumee, arbitrage produit ouvert |

## Statuts autorises

- `A_LANCER`
- `EN_ENQUETE`
- `ENQUETE_A_LANCER`
- `COMMANDE_PRETE`
- `EN_DEV_FRONT`
- `EN_DEV_BACK`
- `EN_QA`
- `CORRECTION`
- `GO_CIBLE`
- `ACCEPTE`
- `BLOQUE`
- `FILE_ATTENTE`
- `PRETE`
- `OUVERT`
- `IDLE_SUR_COMMANDE`
- `IDLE_SUR_ROUTE`
- `IDLE_SUR_DEV`
- `IDLE_INTERDIT`

## Compatibilite statuts historiques

| Marqueur historique | Statut canonique actuel | Regle d'usage |
|---|---|---|
| `ENQUETE_A_LANCER` | `EN_ENQUETE` | Alias documentaire conserve pour les tests historiques; ne pas l'utiliser comme nouveau statut de cadence quinconce. |

## Garde-fous de registre

- Ne jamais marquer un bloc `ACCEPTE` sans route livree.
- Ne jamais marquer une commande `PRETE` sans criteres d'acceptation et tests.
- Ne jamais faire demarrer les devs sur une vue manquante sans visuel ou
  blueprint designer.
- Ne jamais transformer le backlog Cycle 8 en dev applicatif sans commande,
  contrat et tests de sortie nommes.
- Noter explicitement les ruptures token, les fuites privees et le jargon
  primaire comme blocages P0.
