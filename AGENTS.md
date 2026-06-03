# Consignes agents CoproScope

Ce depot peut etre travaille par plusieurs agents en parallele, a condition de ne pas partager le meme arbre de travail pour des modifications concurrentes.

## Regle courte

- Un agent = une branche `codex/<sprint>-<scope>` = un worktree dedie.
- Un agent possede un perimetre de fichiers explicite.
- Aucun fichier de code ne doit depasser 600 lignes. Cette limite s'applique
  aux sources applicatives, tests, templates, CSS, scripts et configurations
  maintenus dans le depot. Si un fichier depasse 600 lignes, le chantier
  prioritaire est de l'extraire en modules/includes/helpers coherents avant
  d'ajouter de nouvelles fonctionnalites. Les documents historiques longs et
  assets binaires ne sont pas du code, mais tout nouveau document de pilotage
  doit rester aussi decoupe que possible.
- Tout BOT-END de refactor ou de livraison code doit inclure un comptage final
  prouvant qu'aucun fichier code suivi par le garde-fou local ne depasse 600
  lignes, ou signaler explicitement le reliquat et son `RM-*`.
- Les instances privees restent hors depot et ne sont jamais commitees.
- Les sorties publiables utilisent l'instance synthetique ou une copro demo fictive hors Drive.
- Le packaging desktop courant est un executable Windows PyInstaller avec
  pywebview: `CoproScope.exe` ouvre une fenetre CoproScope dediee, tout en
  gardant `--browser` comme secours et `--no-browser` pour les smokes. Ne pas
  migrer vers Electron/Tauri ni restructurer le repo sans arbitrage explicite.
  La reference dev est `docs/runbook_packaging_noob_windows.md`.
- En local, l'environnement de test par defaut pour recette live et agents est
  `C:\Users\brice\CoproScope\instances\beauvallon_test`; l'instance
  Platanes `examples/synthetic_copro` reste reservee aux tests publics/CI et
  aux exemples partageables.
- Le coordinateur integre les branches une par une et relance les tests.
- Le gouvernail roadmap unique est
  [`docs/roadmap_backlog_central.md`](./docs/roadmap_backlog_central.md).
  Toute demande "ajoute ceci a la roadmap" y est inscrite en `RM-*`.
  Les anciennes roadmaps/backlogs ne sont plus des sources de pilotage actives.
- Tout chantier actif doit avoir une ligne vivante dans
  [`docs/presence_agents.md`](./docs/presence_agents.md), avec owner,
  worktree/branche, heartbeat et statut.
- Le tableau de travail quotidien est
  [`docs/tableau_execution_courant.md`](./docs/tableau_execution_courant.md).
  Le gouvernail `ORD-*` reste reserve a l'orchestrateur. Les workers ne
  choisissent jamais dans le backlog long: ils prennent seulement un slot
  `A_PRENDRE` publie dans le tableau d'execution du `CH-*` courant.
- Quand Brice demande une equipe multi-agents, appliquer d'abord
  [`docs/strategie_equipes_multi_agents.md`](./docs/strategie_equipes_multi_agents.md):
  preflight anti-collision, choix automatique de l'equipe-type
  `INCIDENT_STATIONNEMENT`, `FANIN_CONSOLIDATION`, `RECHERCHE_METIER`,
  `UXUI_RECHERCHE`, `AGILE_UI_PRODUIT`, `BACKEND_DOMAINE`,
  `RECETTE_LIVE_QA`, `INTEGRATION_RELEASE` ou `DOCTRINE_SIDEQUEST`, puis un
  seul `CH-*`, des owners vivants uniques et des slots workers publies dans
  `docs/tableau_execution_courant.md`. Si le routeur choisit
  `AGILE_UI_PRODUIT`, appliquer
  [`docs/protocole_equipe_agile_agents.md`](./docs/protocole_equipe_agile_agents.md):
  coordinateur-scribe, designer/facilitateur, utilisateur novice, dev front,
  dev back/viewmodel, QA et, si la capacite de threads le permet, testeur
  expert metier juridique/compta/process chantier/syndic, avec flux decale UI
  reelle -> visuel IA et blueprint designer -> qualification novice -> dev ->
  test produit. A chaque iteration UI, le designer/facilitateur produit un
  visuel genere par IA et un blueprint visuel avant le dev. Le visuel IA est une
  image bitmap de l'ecran complet (`.png` ou `.jpg`), pas un SVG, pas une icone
  et pas un schema partiel; le blueprint est le livrable structurel separe. Les
  screenshots de livraison servent seulement de preuve QA apres dev et ne
  remplacent jamais ces livrables cibles. Le coordinateur peut annuler le
  visuel, le blueprint, ou les deux, uniquement avec justification tracee:
  `VISUEL_IA_WAIVED`, `BLUEPRINT_WAIVED`, ou les deux. Les agents comparent
  regulierement avec les visuels de l'enquete utilisateur. Au lancement
  effectif, mettre a jour la heartbeat canonique
  `relance-equipe-agile-gouvernail-autonome` toutes les 5 minutes sur le fil
  courant, plutot que creer une heartbeat concurrente; tout doublon actif doit
  etre mis en pause. La heartbeat canonique doit laisser un check-in persistant
  dans `docs/presence_agents.md`, meme en `DONT_NOTIFY`, sans dupliquer les
  roles vivants. Quand un lot contient
  `AGILE-DONE - equipe agile a fini son job` et que ses roles sont clos, la
  heartbeat peut ouvrir le prochain `ORD-*` seulement si aucun arbitrage
  `EN_ATTENTE_USER`, blocage non stationne ou incident de doublon n'est actif.
  Si Brice signale que plusieurs conversations prennent la meme tache, tout
  chainage automatique s'arrete, mais la heartbeat canonique reste active en
  mode surveillance/reprise: pause des dispatchers concurrents, abandon/attente
  des lots ouverts par course, check-in persistant, reprise seulement des roles
  manquants d'un `CH-*` deja declare, puis nouveau dispatch uniquement apres
  arbitrage explicite de Brice.
- Quand Brice dit "lance une equipe UX/UI" avec ou sans accent sur `equipe`,
  appliquer
  [`docs/protocole_equipe_ux_ui_recherche.md`](./docs/protocole_equipe_ux_ui_recherche.md):
  equipe de recherche sans dev, 6 roles maximum dont Testeur metier expert et
  Testeur accessibilite/novice, generation d'images, images retenues archivees
  dans la doc de mission, et relance heartbeat toutes les 10 minutes jusqu'au
  marqueur `UXUI-DONE - equipe UX/UI a fini son job`.
- Dans une conversation orientee vers un but, comme un audit ou une livraison,
  le coordinateur garde le chemin critique. Les demandes ponctuelles de
  generalisation, doctrine, cadrage transverse ou side-quest bornee sont
  confiees a des sub-agents si la capacite de threads le permet.

## Rapports d'audit et notes coproprietaires

Tout rapport ou note d'audit destine au dossier de copropriete doit etre
redige pour un coproprietaire novice: phrases courtes, vocabulaire explique,
sigles developpes a la premiere occurrence, et distinction nette entre ce qui
est constate, ce qui est seulement suppose, et ce qui reste a verifier.

Structure minimale obligatoire:

- synthese en tete, lisible sans connaissance comptable, juridique ou
  informatique;
- methode employee, avec les controles realises et les limites du controle;
- sources utilisees, datees et identifiables;
- constats, separes des interpretations;
- conclusions et questions/actions proposees pour le conseil syndical ou l'AG.
- impact concret pour les coproprietaires, notamment sur les appels de fonds,
  les budgets, le fonds travaux, les impayes, la tresorerie et les risques de
  rattrapage ou d'appel exceptionnel.

Le detail technique peut etre mis plus bas ou en annexe, mais le corps du
rapport doit rester comprehensible par un coproprietaire qui decouvre le sujet.

Lorsqu'une demande d'audit inclut une nouvelle convocation d'assemblee generale,
la partie comptabilite doit etre traitee systematiquement: annexes comptables,
comptes a approuver, budgets votes ou proposes, fonds travaux, impayes,
fournisseurs, travaux et operations exceptionnelles, ainsi que les ecarts avec
les audits ou documents comptables deja connus.

Lorsque des montants globaux peuvent toucher le portefeuille des
coproprietaires, le rapport doit les traduire en consequences pratiques:
hausse probable des appels, reste a financer, risque de tension de tresorerie,
avance temporaire possible, et ordre de grandeur par tantiemes ou par 1 % des
charges, en precisant toujours que le montant exact depend des cles de
repartition du lot.

Toute comparaison doit nommer explicitement les deux references comparees:
document, date, montant ou etat "avant / apres". Eviter les formulations comme
"plus lourd", "en baisse", "plus eleve" ou "ameliore" si les deux bases de
comparaison ne sont pas affichees dans le rapport.

Garde de confidentialite conversationnelle pour audits et notes sensibles:

- structurer le raisonnement en `fait -> preuve -> regle -> action`;
- remplacer les personnes, organisations, lots et lieux par des roles ou alias
  stables des la premiere reformulation, sauf necessite explicite;
- ne pas recopier emails, telephones, adresses completes, chemins locaux, noms
  de fichiers bruts, OCR brut, logs, secrets, tables alias -> identite ou
  correspondances nominatives;
- afficher un montant ou une identite seulement si c'est indispensable au
  controle ou a une diligence concrete, puis revenir aux alias;
- bloquer le rendu final si une donnee personnelle inutile, une piece brute, un
  chemin local ou une allegation non sourcee reste dans le texte.

Pour une nouvelle convocation d'AG, la comparaison principale doit etre faite
entre l'AG precedente disponible au dossier et l'AG actuelle. Les documents de
travail du conseil syndical peuvent etre cites comme pieces de circulation ou de
controle, mais ils doivent etre presentes comme references secondaires et ne
doivent jamais etre confondus avec une convocation officielle ou un document
soumis au vote.

## Regle zero interconversations

Tout bot doit lire [`docs/consignes_bots_interconversations.md`](./docs/consignes_bots_interconversations.md)
avant de modifier le depot.

Il lit aussi
[`docs/protocole_roadmap_presence_agents.md`](./docs/protocole_roadmap_presence_agents.md)
pour rattacher son travail a un item `RM-*`, un chantier `CH-*` et une
conversation `CONV-*`.

Tout nouveau chantier doit suivre le format anti-collision
`CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug-court`. Le format historique
`CH-YYYY-NNNN` est conserve uniquement pour les chantiers deja ouverts.

Avant toute modification, il declare:

- identifiants `RM-*`, `CH-*` et `CONV-*`;
- role et mission;
- ownership modifiable;
- fichiers a eviter;
- passerelle ou registre de trace;
- dernier point de coordination lu;
- tests ou preuves attendus.
- lease d'ownership et prochaine action.

Sans declaration claire, le bot reste en lecture seule et publie une question de
coordination. Les passerelles UX/DB restent separees: UX ecrit dans
`docs/passerelle_ux_vers_db_2026-05-21.md`, DB repond dans
`docs/passerelle_db_vers_ux_2026-05-21.md`, le coordinateur consolide dans
`docs/coordination_interconversations_2026-05-21.md`.

## Demarrage recommande

Depuis la racine du depot principal, apres avoir stabilise ou commite les changements en cours :

```powershell
git fetch origin
git switch codex/bootstrap-coproscope-server
git pull --ff-only

git worktree add ..\coproscope-agent-sprint2-actions -b codex/sprint2-actions
git worktree add ..\coproscope-agent-sprint3-compta -b codex/sprint3-compta
git worktree add ..\coproscope-agent-sprint4-privacy -b codex/sprint4-privacy
```

Si une branche existe deja, retirer `-b <branche>` et indiquer la branche existante a la fin de la commande.

## Check rapide agent

Pour une reprise ou une fin de lot courte, lancer depuis la racine du depot:

```powershell
.\tools\agent-check.cmd
```

Options utiles:

- `.\tools\agent-check.cmd -Ui` pour ajouter les smoke tests UI et routes de
  securite;
- `.\tools\agent-check.cmd -Security` pour ajouter Bandit haute severite et
  pip-audit;
- `.\tools\agent-check.cmd -Orchestration` pour verifier heartbeats,
  conversations expirees, blocages, arbitrages et relance gouvernail;
- `.\tools\agent-check.cmd -Full` pour lancer toute la suite `unittest`.

Pour surveiller seulement l'orchestration sans tests applicatifs:

```powershell
.\tools\orchestration-watch.cmd
.\tools\orchestration-watch.cmd --emit-prompt
.\tools\orchestration-supervise.cmd --emit-recovery-prompt
```

Le check rapide ne remplace pas la verification d'integration complete quand le
coordinateur integre une branche, mais il donne un signal fiable avant de rendre
un lot.

## Contrat a donner a chaque agent

Copier-coller un contrat court au lancement :

```text
Mission: Sprint <numero> - <objectif>
Role/filiere: <UX | DB | QA | front | back | docs | coordinateur>
Roadmap/chantier/conversation: RM-YYYY-NNNN / CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug-court / CONV-YYYY-NNNN
Branche/worktree: <branche> / <chemin>
Tu n'es pas seul dans le codebase. Ne revert jamais les changements des autres.
Ownership fichiers: <liste de dossiers/fichiers modifiables>
Fichiers a eviter: <liste>
Passerelle/registre de trace: <fichier>
Dernier point coordination lu: <fichier + heure>
Lease ownership: <expiration + fuseau> ; heartbeat dans docs/presence_agents.md
Donnees: pas de donnees privees dans Git ; instance privee uniquement en lecture locale.
Donnees de test locales par defaut: `C:\Users\brice\CoproScope\instances\beauvallon_test`.
Verification attendue: <commandes de test ou checks UI>
Livrable final: resume, fichiers modifies, limites, tests lances.
```

## Methode equipe agile multi-agents

Avant de supposer qu'une equipe agile standard est le bon format, appliquer le
routeur de [`docs/strategie_equipes_multi_agents.md`](./docs/strategie_equipes_multi_agents.md).
L'equipe agile UI produit est un cas de routage, pas le mode par defaut pour
toute demande multi-agents.

La methode canonique est
[`docs/protocole_equipe_agile_agents.md`](./docs/protocole_equipe_agile_agents.md).
Elle est obligatoire quand une conversation demande une equipe agile,
des agents UX/dev/QA, ou des iterations rapides avec utilisateurs.

Au lancement effectif, le coordinateur met a jour la heartbeat canonique
`relance-equipe-agile-gouvernail-autonome` toutes les 5 minutes sur le fil
courant. Il ne cree une heartbeat separee que si Brice le demande
explicitement; sinon tout doublon actif est mis en pause. La heartbeat canonique
laisse un check-in persistant dans `docs/presence_agents.md`, meme en
`DONT_NOTIFY`, et relance les roles manquants, idle, bloques ou expires sans
dupliquer un role vivant.
`AGILE-DONE - equipe agile a fini son job` ferme seulement le lot courant: si
tous les roles du lot sont clos, la heartbeat choisit le prochain `ORD-*`
actionnable du gouvernail uniquement quand aucun arbitrage `EN_ATTENTE_USER`,
blocage non stationne ou incident de doublon n'est actif. En mode incident
anti-chevauchement, elle ne lance aucune nouvelle equipe et reste active en
mode surveillance/reprise: elle met en pause les dispatchers concurrents, marque
les lots ouverts par course `ABANDONNE` ou `EN_ATTENTE_USER`, trace le verrou
dans `docs/presence_agents.md`, relance seulement les roles manquants d'un
`CH-*` deja declare et attend un arbitrage explicite de Brice avant tout nouveau
`ORD-*`. Elle ne se supprime que sur demande explicite de Brice ou si le
gouvernail ne contient vraiment plus aucun `ORD-*` actionnable, auquel cas elle
trace le no-go et reste recadrable.

Resume d'execution:

1. le coordinateur rattache le travail au gouvernail `RM-*` et cree un `CH-*`
   horodate selon `docs/protocole_roadmap_presence_agents.md`;
2. il publie son `BOT-START`, remplit
   `docs/tableau_execution_courant.md` avec les slots `A_PRENDRE` du chantier,
   puis une ligne `CONV-*` par role effectivement pris;
3. les roles standards sont coordinateur-scribe, designer/facilitateur,
   utilisateur novice, dev front, dev back/viewmodel et QA; si le budget de
   threads le permet, ajouter un testeur expert metier
   juridique/compta/process chantier/syndic, sinon faire reprendre sa checklist
   par QA et le coordinateur;
4. le travail tourne en double flux: `N-1` teste le produit livre avec
   screenshots/captures de recette, `N` developpe la commande validee, `N+1`
   produit le visuel IA, le blueprint cible et la commande suivante;
5. chaque cycle nomme une UI reelle: route, ecran, modale, artefact HTML ou
   parcours local. Si l'UI manque, le premier objectif est de la rendre
   testable, pas de raisonner sur une intention abstraite;
6. a chaque iteration UI, le designer produit une image IA bitmap de l'ecran
   complet et un blueprint visuel cible, puis le novice donne un GO/NO-GO avant
   tout dev; l'un et/ou l'autre peuvent etre annules seulement avec
   justification tracee, et une capture de livraison ne remplace pas cette
   etape;
7. le designer, le novice et la QA comparent souvent l'UI reelle aux visuels
   d'enquete utilisateur ou au visuel designer derive, et tracent les ecarts
   acceptes/refuses avant GO;
8. les devs restent en lecture tant que le blueprint, la commande dev, la
   qualification novice et le contrat `model.ux.*` ne sont pas stabilises;
9. chaque point annonce: a tester, en dev, en enquete, commande prete, agents
   idle, decision requise, prochain mouvement et preuves.

Dans ce cadre, le coordinateur ne quitte pas la piste critique pour traiter une
generalisation ou une side-quest nee d'une orientation ponctuelle. Si un thread
est disponible, il lance un sub-agent avec objectif borne, ownership explicite,
fichiers evites, trace et critere de fin. Si aucun thread n'est disponible, il
note la demande comme reprise ulterieure ou question d'arbitrage, sauf si elle
bloque directement le but principal.

## Methode equipe UX/UI sans dev

Quand la commande naturelle est `lance une equipe UX/UI`, avec ou sans accent
sur `equipe`, utiliser
[`docs/protocole_equipe_ux_ui_recherche.md`](./docs/protocole_equipe_ux_ui_recherche.md).
Cette equipe ne code pas: elle produit recherche, parcours, wireflows,
directions UI, images generees et decisions UX/UI. Le Designer UI / generateur
visuel produit les images candidates; seules les images retenues ou utiles a
une decision sont archivees dans `docs/assets/...` et referencees dans la doc
de mission.

Au lancement effectif, le coordinateur cree une heartbeat automation Codex
toutes les 10 minutes sur le fil courant. Elle relance les roles idle ou
bloques sans les dupliquer, puis s'arrete quand la trace finale contient
`UXUI-DONE - equipe UX/UI a fini son job`.

## Ports locaux

Ne pas lancer deux interfaces sur le meme port. Le port fait partie de
l'ownership de l'agent au meme titre que les fichiers: il est annonce dans le
contrat agent, reporte dans `docs/presence_agents.md`, puis libere explicitement
dans le `BOT-END`.

Regles obligatoires:

- Pour les lots desktop, packaging, installable ou recette utilisateur generale,
  tester en priorite l'executable avec
  `server\packaging\windows\smoke-executable.ps1`. Le serveur PowerShell visible
  reste l'outil de developpement web fin, pas la recette cible par defaut.
- Le smoke executable peut choisir un port loopback libre fourni par Windows,
  lancer son propre processus `CoproScope.exe`, puis fermer uniquement ce
  processus. Il ne doit jamais tuer un PID qu'il n'a pas cree.
- reserver un port avant de demarrer un serveur, avec `CONV-*`, role, instance,
  token de test et commande prevue;
- quand un serveur de developpement est lance manuellement, le garder dans un
  terminal PowerShell visible; arret par `Ctrl+C` uniquement;
- ne pas scanner les ports ou processus, ne pas tuer de PID, ne pas utiliser
  `taskkill`, `Start-Process` cache ou ouverture navigateur automatique;
- si le port prevu est occupe ou douteux, ne pas enqueter par scan: publier le
  conflit dans la trace, choisir un autre port documente dans la plage de
  secours, et mettre a jour `presence_agents.md`;
- une URL live citee dans un test doit toujours indiquer port, instance cible et
  token attendu;
- a la fin du lot, dire si le serveur a ete arrete ou s'il reste volontairement
  ouvert pour recette.

Ports reserves par defaut:

| Usage | Port conseille |
|---|---:|
| Coordinateur | 8765 |
| UI/actions | 8766 |
| ComptaScope | 8767 |
| Privacy/DocOps | 8768 |
| Demo/docs | 8769 |
| SyndicOps | 8770 |
| DocOps actionnable | 8771 |
| Decision-action-preuve | 8772 |
| WorksOps | 8773 |
| IncidentOps | 8774 |
| Comms/passation | 8775 |

La plage `8780` a `8799` est reservee aux recettes temporaires, gates live et
serveurs de comparaison. Chaque utilisation de cette plage doit etre nommee
dans le point de coordination ou la trace `CONV-*`; elle ne devient jamais un
defaut implicite.

## Perimetres qui se parallelisent bien

| Agent | Ownership principal |
|---|---|
| UI/actions | `server/src/coproscope/web/`, `server/tests/test_ui_demo.py` |
| ComptaScope guide | `server/src/coproscope/web/viewmodel.py`, templates comptes, docs ComptaScope |
| Privacy/DocOps | `server/src/coproscope/modules/privacyops.py`, templates confidentialite/documents, tests privacy |
| Decision-action-preuve | nouveau module/registre dedie, tests dedies, docs fonctions cibles |
| Documentation/orchestration | `docs/`, `README.md`, registres de suivi |

Quand deux agents doivent toucher `viewmodel.py`, le coordinateur tranche avant lancement : un seul agent possede ce fichier, les autres produisent une note d'integration ou travaillent sur des templates/tests.

## Refonte UX depuis les visuels d'enquete

La refonte UX Canva suit le protocole
[`docs/refonte_ux_cycles_image_dev_test.md`](./docs/refonte_ux_cycles_image_dev_test.md):
enquete sur image, commande dev, developpement, test produit livre, correction
ou cloture.

Regles supplementaires:

- garder un bloc en test, un bloc en dev et un bloc en enquete quand c'est possible;
- ne pas demarrer le dev sans commande validee;
- ne pas laisser les devs inventer une vue manquante sans blueprint designer;
- ne pas lancer un dev UI sans route/ecran/artefact reel cible et, si pertinent,
  sans image designer qualifiee par le novice;
- produire un visuel IA et un blueprint designer pour chaque iteration UI avant
  le dev; le visuel IA est une image bitmap de l'ecran complet, jamais un SVG;
  l'un et/ou l'autre peuvent etre annules seulement avec justification tracee;
  les screenshots de livraison sont des preuves de recette, pas la source
  d'intention UX;
- comparer regulierement l'UI livree aux visuels de l'enquete utilisateur ou au
  visuel designer derive; un GO UI sans comparaison explicite est refuse sauf
  justification de non-pertinence;
- tester une route livree, pas une intention abstraite;
- tenir [`docs/registre_cycles_refonte_ux.md`](./docs/registre_cycles_refonte_ux.md)
  et utiliser les prompts de
  [`docs/prompts_agents_refonte_ux.md`](./docs/prompts_agents_refonte_ux.md).

## Integration

Le coordinateur :

1. verifie `git status --short` dans chaque worktree ;
2. relit les diffs ;
3. integre une branche a la fois ;
4. resout les conflits sans supprimer le travail d'un autre agent ;
5. lance au minimum `.\server\.venv\Scripts\python.exe -m unittest discover -s tests -v` depuis `server/` ;
6. met a jour le gouvernail `docs/roadmap_backlog_central.md` et `docs/presence_agents.md` ;
7. pousse seulement les changements genericisables.

Voir aussi : [`docs/orchestration_agents.md`](./docs/orchestration_agents.md).
