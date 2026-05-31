# Protocole equipe agile multi-agents

Date de creation: 2026-05-21.
Rattachement: `RM-2026-0005`.

Ce protocole s'applique quand Brice demande une "equipe agile", une equipe
multi-agents, une equipe UX/dev/QA, ou un fonctionnement par cycles rapides.
Il transforme la conversation en petite equipe cadree, avec utilisateurs,
facilitateurs/designers, devs et QA, sans casser les regles de presence.

Pour une demande generique d'equipe multi-agents ou pour le chainage autonome
depuis le gouvernail, l'orchestrateur applique d'abord
[`strategie_equipes_multi_agents.md`](./strategie_equipes_multi_agents.md).
Le present protocole est lance seulement si le routeur choisit
`AGILE_UI_PRODUIT` ou si Brice demande explicitement une equipe agile
UX/dev/QA.

Pour une nouvelle feature produit ou transverse, le passage par une equipe
d'agents est obligatoire apres le cadrage, meme si le routeur choisit
`BACKEND_DOMAINE` plutot que `AGILE_UI_PRODUIT`. Un owner code unique peut
implementer, mais il ne suffit pas a valider le lot: les roles experts, QA,
novice ou designer prevus par le routeur doivent rendre un retour trace avant
le statut `PRET_A_INTEGRER`.

Regle produit ajoutee: l'equipe travaille systematiquement sur de l'UI reelle.
Une discussion, une note ou une commande ne suffit pas: chaque cycle doit nommer
la route, l'ecran, la modale, l'artefact HTML ou le parcours local vise. Si
cette UI n'existe pas encore, le premier livrable est de la rendre testable.
Des que le sujet est visuel, nouveau, ambigu, dense ou sensible pour un membre
CS novice, le designer genere une image IA et un blueprint, puis le novice les
qualifie en GO/NO-GO avant que le developpement commence.

Regle de visuel amont: pour chaque iteration UI, le designer/facilitateur doit
produire un visuel genere par IA et un blueprint visuel avant le dev. Un
screenshot de livraison, meme annote, est une preuve QA aval: il ne remplace
pas ces livrables cibles. Le coordinateur peut annuler le visuel IA, le
blueprint, ou les deux, uniquement avec justification tracee:
`VISUEL_IA_WAIVED`, `BLUEPRINT_WAIVED`, ou les deux. Le point de coordination
cite le chemin du visuel retenu sous `docs/assets/...` et le chemin de la
note/blueprint; les variantes non retenues ne sont archivees que si elles
justifient une decision. Le visuel IA est une image bitmap de l'ecran complet
(`.png` ou `.jpg`), pas un SVG, pas une icone, pas une illustration abstraite et
pas un schema partiel. Le blueprint est le livrable structurel separe.

Les visuels de l'enquete utilisateur et les visuels designer derives sont des
references actives, pas des archives. Les agents comparent regulierement l'UI
reelle a ces references pendant le cadrage, apres livraison et avant tout GO UI.

## Serveurs live autorises sous reservation

Une equipe agile produit ou QA peut lancer ou utiliser un serveur local quand
sa mission l'exige: recette navigateur, captures desktop/tablette/mobile,
verification de token `200/403`, parcours utilisateur ou comparaison visuelle
sur UI reelle. Ce n'est pas une relance automatique qui lance ce serveur; c'est le
coordinateur ou l'owner declare du lot.

Avant tout lancement, le contrat d'equipe doit nommer le port, l'instance de
test, le token, la commande, le terminal PowerShell visible et la condition
d'arret. Un serveur non reserve, cache, branche sur une instance privee reelle,
ou manipule par scan/kill de processus reste interdit.

## Regle de demarrage

Avant de lancer l'equipe, le coordinateur doit:

1. rattacher le travail a un `RM-*` dans `docs/roadmap_backlog_central.md`;
2. creer ou reprendre un `CH-*` dans `docs/presence_agents.md`; pour tout
   nouveau chantier, utiliser le format
   `CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug-court`;
3. tracer `ROUTAGE_EQUIPE` dans `docs/presence_agents.md`, puis ouvrir une
   ligne `CONV-*` ou `SUBAGENT-*` pour chaque role actif. Les agents recoivent
   leur mission du fil pilote; ils ne choisissent pas dans la file `ORD-*`;
4. declarer son propre `CONV-*` avec ownership, fichiers evites, trace, tests
   attendus, lease et dernier point lu;
5. s'appuyer sur l'objectif actif Codex (`/objectif`) et sur
   `docs/presence_agents.md` pour la continuite. Ne pas creer ni reparer de
   heartbeat canonique ou de watchdog permanent par defaut. Un heartbeat Codex
   ne revient que sur demande explicite de Brice pour un reveil horodate et
   borne a un `CH-*` existant. Quand la trace finale contient
   `AGILE-DONE - equipe agile a fini son job`, elle ferme seulement le lot
   courant; le fil pilote reprend ensuite le gouvernail seulement si aucun
   arbitrage `EN_ATTENTE_USER`, blocage non stationne ou incident de doublon
   n'est actif. Si Brice signale que plusieurs conversations prennent la meme
   tache, aucun nouveau `CH-*` n'est cree avant arbitrage explicite;
6. ouvrir une ligne `CONV-*` par role actif;
7. attribuer un ownership disjoint a chaque role;
8. garder les devs en lecture si la commande produit ou le contrat de donnees
   n'est pas stable.
9. bloquer tout dev UI tant que la cible UI reelle, le visuel IA, le blueprint
   et la qualification novice ne sont pas explicites, ou que les waivers
   `VISUEL_IA_WAIVED` / `BLUEPRINT_WAIVED` ne sont pas justifies.
10. nommer le visuel d'enquete ou le visuel designer derive qui servira de
   reference, ou justifier pourquoi la comparaison n'est pas pertinente.

Sans ces elements, l'equipe reste en cadrage lecture seule.

## Roles standards

| Role | Fonction | Peut modifier |
|---|---|---|
| Coordinateur-scribe | Gouvernail, presence, decoupage, arbitrages, integration | Registres et points de coordination declares |
| Designer service / facilitateur | Enquete, visuel IA et blueprint, commande dev, langage novice | Visuels cibles, blueprints, commandes, notes UX declares |
| Utilisateur novice | Test des routes livrees et attentes naturelles | Notes de test uniquement |
| Dev front | Templates, CSS `cs-*`, responsive, accessibilite | Templates/CSS declares apres commande validee |
| Dev back / viewmodel | Routes, projections `model.ux.*`, compteurs, donnees fictives | Modules/routes/viewmodels declares, owner unique sur fichiers sensibles |
| QA securite / regression | Tests, non-fuite, token, responsive, captures | Notes QA et tests declares; pas de correction sans ownership |

Roles optionnels:

- integration lead, quand front/back livrent des branches separees;
- DB/data designer, quand une autre conversation travaille la base de donnees;
- privacy/docops, quand les exports ou pieces peuvent contenir des donnees
  sensibles.
- testeur expert metier, quand le budget de threads le permet: il contre-teste
  juridique, compta, process chantier et syndic en lecture seule, sans avis
  juridique/comptable definitif, avec une sortie `fait -> preuve attendue ->
  regle/process -> action`. Si aucun thread n'est disponible, QA et le
  coordinateur reprennent explicitement cette checklist.

Ces roles sont optionnels seulement pour une equipe agile generique. Quand le
routeur, le gate nouvelle feature ou un risque privacy/metier les exige, ils
deviennent des retours attendus avant dev ou avant `PRET_A_INTEGRER`.

## Double flux rapide

Le coordinateur garde au maximum trois flux decales:

| Flux | Etat | Responsable |
|---|---|---|
| `N-1` | Test produit livre, screenshots/captures de recette, corrections mineures | QA + utilisateur novice |
| `N` | Dev front/back depuis commande validee | Dev front + dev back |
| `N+1` | Visuel IA et blueprint cible, enquete image, commande suivante | Designer + utilisateur novice |

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
2. **Visuel IA ET blueprint designer**: requis pour chaque iteration UI avant dev.
   Une capture annotee suffit seulement pour une correction mineure d'une UI
   deja livree, et elle reste une preuve QA aval, pas le visuel cible de
   l'iteration suivante. Le visuel IA est une image bitmap de l'ecran complet
   attendu; il ne doit pas etre un SVG. Le blueprint structure le parcours, les
   zones, composants et etats. Ces deux livrables sont attendus pour tout nouvel
   ecran, changement de parcours, zone dense, action sensible ou reorganisation
   de surface UI; annuler l'un, l'autre ou les deux exige
   `VISUEL_IA_WAIVED` et/ou `BLUEPRINT_WAIVED` avec justification.
3. **Qualification novice**: le membre novice donne un GO/NO-GO sur l'image IA,
   le blueprint et la route existante avant lancement dev. Son retour nomme ce
   qu'il comprend, ce qu'il croit pouvoir cliquer, ce qui le bloque et les mots
   naturels a utiliser.
4. **Commande dev stabilisee**: le coordinateur transforme le GO novice en
   commande front/back avec donnees, interactions, etats vides, garde-fous
   privacy et tests.

No-go immediat:

- dev lance depuis une intention abstraite sans UI cible;
- dev qui invente la structure d'une vue pertinente sans designer;
- visuel IA et/ou blueprint non qualifie par le novice alors que l'ecran est
  nouveau, visuel, dense ou sensible;
- screenshot de livraison utilise comme substitut au visuel IA et/ou au
  blueprint amont d'une iteration UI;
- visuel IA livre en SVG, en illustration partielle ou en schema au lieu d'une
  image bitmap de l'ecran complet;
- test qui valide une maquette sans route, ecran ou artefact livre.

## Gate privacy conversationnelle

Ce gate est obligatoire des qu'une equipe manipule audit, contentieux,
coproprietaires, AG, travaux sensibles, demandes nominatives ou documents bruts.

1. **Minimisation**: la synthese et les prompts de role suivent
   `fait -> preuve -> regle -> action`; les noms propres restent hors fil sauf
   necessite documentee.
2. **Alias stables**: personnes, organisations, lots, lieux et pieces sont
   remplaces par des alias locaux (`PERS-01`, `SYNDIC-01`, `LOT-01`,
   `PIECE-AG-001`) des la premiere reformulation.
3. **Sortie diffusable**: aucune sortie de l'equipe ne contient chemin local,
   email, telephone, IBAN/RIB, token, secret, nom de fichier brut, OCR brut,
   log, table alias -> identite ou marqueur `raw/restricted/private`.
4. **Reserve lisible**: toute conclusion distingue `constate`, `suppose`,
   `a verifier`, preuve attendue et action proposee.

No-go immediat:

- identite ou donnee personnelle non indispensable dans un livrable;
- allegation non sourcee formulee comme certitude;
- citation longue issue d'une piece brute;
- demande de publication d'une table alias -> identite reelle;
- sortie qui ne dit pas qui peut voir le resultat.

## Comparaison aux visuels d'enquete

Cette comparaison est recurrente pour tout travail UI.

- **Avant dev**: le designer rattache la commande a un visuel source
  (`docs/assets/etude-utilisateurs/...`) ou a un visuel designer derive. Il
  nomme les elements a conserver: structure, hierarchie, densite, vocabulaire,
  gestes attendus et signaux de confiance.
- **Pendant dev**: les devs verifient que les compromis techniques ne cassent
  pas ces reperes. Si l'ecart change l'intention utilisateur, le bloc retourne
  au designer.
- **En QA/novice**: le test de la route reelle inclut une comparaison par blocs
  avec le visuel de reference: premier viewport, CTA, cartes, tableaux,
  statuts, preuves, prochaine action, diffusion et etats vides.
- **En cloture**: le GO/NO-GO cite les ecarts acceptes, refuses ou reportes. Si
  aucune comparaison n'est pertinente, la trace l'explique.

Un agent idle cote UX/QA peut etre relance uniquement sur cette comparaison,
meme sans nouveau code a produire.

## Cycle type

1. Cadrage de l'UI reelle cible: route, ecran, modale, artefact ou parcours.
2. Generation par le designer d'une image IA et d'un blueprint cible; si l'un
   des deux est annule, tracer `VISUEL_IA_WAIVED` et/ou `BLUEPRINT_WAIVED` avec
   justification.
3. Comparaison avec les visuels d'enquete ou le visuel designer derive.
4. Qualification novice du visuel IA, du blueprint et de l'UI existante.
5. Commande dev au format obligatoire.
6. Developpement front/back sur ownership explicite.
7. Test de la route, de l'ecran ou de l'artefact reel livre.
8. Comparaison QA/novice de l'UI livree avec le visuel de reference.
9. Correction mineure ou retour designer si l'intention change.
10. Cloture par preuves: UI reelle, captures/screenshots de recette, tests, comparaison visuelle,
    go/no-go novice.

La commande dev doit contenir:

- objectif utilisateur;
- UI cible reelle et route ou artefact a tester;
- visuel d'enquete ou visuel designer derive de reference;
- chemin du visuel IA cible bitmap (`.png` ou `.jpg`) montrant l'ecran complet,
  ou `VISUEL_IA_WAIVED` justifie;
- chemin du blueprint cible produit pour l'iteration, ou `BLUEPRINT_WAIVED`
  justifie;
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
- Aucun dev UI ne demarre sans visuel IA et blueprint designer produits en
  amont et qualifies par le novice, sauf annulation explicite de l'un et/ou de
  l'autre par `VISUEL_IA_WAIVED` et/ou `BLUEPRINT_WAIVED`.
- Aucun dev ne demarre sur une UI nouvelle, visuelle, dense ou sensible sans
  image IA et blueprint designer qualifies par le novice, sauf waiver justifie.
- Aucun screenshot de livraison ne remplace le visuel cible designer; il sert
  seulement a la recette et a la comparaison apres dev.
- Aucun testeur ne valide une intention abstraite: il teste une route, un ecran
  ou un artefact reel.
- Aucun GO UI ne sort sans comparaison aux visuels d'enquete ou justification
  explicite de non-pertinence.
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
- Visuel IA et blueprint N+1
- Commande prete
- Comparaison visuels enquete
- Agents idle a relancer
- Decision requise
- Prochain mouvement
- Tests/preuves

Le coordinateur donne un prochain mouvement concret. S'il n'y a pas
d'arbitrage impossible, l'equipe continue.

## Transition entre lots avec `/objectif`

`AGILE-DONE - equipe agile a fini son job` ferme le lot courant. Il ne cree pas
de relance permanente. Au passage suivant, le fil pilote doit:

0. si necessaire, lancer un diagnostic manuel depuis la racine du depot pour
   verifier les conversations vivantes, expirees, bloquees et en attente
   utilisateur, par exemple `.\tools\agent-check.cmd -Orchestration` ou
   `.\tools\orchestration-supervise.cmd --read-codex-processes`;
1. si le diagnostic remonte `EN_ATTENTE_USER`, un incident de doublon backlog ou
   un blocage non stationne, ne pas lire la file `ORD-*` pour dispatch: remonter
   seulement l'arbitrage, laisser un check-in et attendre Brice; si un `CH-*`
   est deja declare avec roles manquants, idle, bloques ou expires, relancer
   uniquement ces roles dans le meme `CH-*` et sans changer d'`ORD-*`;
2. verifier que tous les `CONV-*` du lot sont `CLOTURE`, `INTEGRE`,
   `PRET_A_INTEGRER` ou un statut final explicite;
3. ne pas relancer ces roles termines;
4. lire la file `ORD-*` dans `docs/roadmap_backlog_central.md`;
5. choisir le plus petit `ORD-*` actionnable de la priorite la plus haute, en
   excluant les items bloques, deja actifs avec roles vivants, `PRET_A_INTEGRER`
   sans integration decidee, ou interdits par une consigne explicite comme
   `RM-2026-0017`;
6. appliquer le routeur d'equipes-types pour decider si ce `ORD-*` demande
   `AGILE_UI_PRODUIT`, `BACKEND_DOMAINE`, `RECHERCHE_METIER`,
   `RECETTE_LIVE_QA`, `INTEGRATION_RELEASE` ou un autre mode;
7. creer un nouveau `CH-*` horodate et un coordinateur uniquement apres ce
   routage;
8. tracer les roles a lancer ou a reprendre dans `docs/presence_agents.md`,
   sans recreer de slots ni de file intermediaire;
9. tracer le point de reprise dans `docs/presence_agents.md`.

Si aucun `ORD-*` actionnable n'existe, le fil trace `NO_ORD_ACTIONNABLE` dans
`docs/presence_agents.md` avec la raison concrete. Il ne cree pas de heartbeat
de substitution.

## Contrat court a copier a un agent

```text
Mission: <bloc ou sprint>
Role/filiere: <coordinateur | designer | utilisateur novice | front | back | QA>
Roadmap/chantier/conversation: RM-YYYY-NNNN / CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug-court / CONV-YYYY-NNNN
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

1. le coordinateur lit `AGENTS.md`, `strategie_equipes_multi_agents.md`, ce
   protocole, la roadmap et la presence;
2. il declare un `BOT-START`;
3. il s'appuie sur l'objectif actif Codex et sur `docs/presence_agents.md`;
   aucun heartbeat canonique n'est cree par defaut. Si Brice demande un reveil
   horodate, celui-ci reste borne au `CH-*` courant et ne choisit pas seul un
   nouveau `ORD-*`;
4. il confirme que le routage retenu est bien `AGILE_UI_PRODUIT` ou une equipe
   agile explicitement demandee, sinon il applique le protocole du type choisi;
5. il ouvre les roles standards utiles, pas plus; si le nombre de threads le
   permet, il ajoute le testeur expert metier
   juridique/compta/process chantier/syndic, sans dupliquer un role vivant;
6. il nomme l'UI reelle cible du cycle courant;
7. il demande au designer un visuel IA et un blueprint a chaque iteration UI,
   puis fait qualifier ces sorties par le novice avant dev; l'un et/ou l'autre
   peuvent etre annules seulement avec justification tracee; les screenshots de
   livraison restent reserves a la QA apres dev;
8. il fait comparer regulierement l'UI reelle au visuel d'enquete ou au visuel
   designer derive, et trace les ecarts;
9. il garde le flux decale actif;
10. il travaille localement sur la piste critique pendant que les agents
   traitent les pistes paralleles;
11. il delegue aux sub-agents les generalisations et side-quests bornees si les
   threads disponibles le permettent;
12. il integre uniquement apres preuves et ownership clair;
13. il publie un `BOT-END` ou un point de reprise exploitable.
