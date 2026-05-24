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
- En local, l'environnement de test par defaut pour recette live et agents est
  `C:\Users\brice\Documents\CoproScope\instances\beauvallon_test`; l'instance
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
- Quand Brice demande une "equipe agile" ou une equipe multi-agents, appliquer
  [`docs/protocole_equipe_agile_agents.md`](./docs/protocole_equipe_agile_agents.md):
  coordinateur-scribe, designer/facilitateur, utilisateur novice, dev front,
  dev back/viewmodel et QA, avec flux decale UI reelle -> image/blueprint si
  pertinent -> qualification novice -> dev -> test produit, et comparaison
  reguliere avec les visuels de l'enquete utilisateur.
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
- `.\tools\agent-check.cmd -Full` pour lancer toute la suite `unittest`.

Le check rapide ne remplace pas la verification d'integration complete quand le
coordinateur integre une branche, mais il donne un signal fiable avant de rendre
un lot.

## Contrat a donner a chaque agent

Copier-coller un contrat court au lancement :

```text
Mission: Sprint <numero> - <objectif>
Role/filiere: <UX | DB | QA | front | back | docs | coordinateur>
Roadmap/chantier/conversation: RM-YYYY-NNNN / CH-YYYY-NNNN / CONV-YYYY-NNNN
Branche/worktree: <branche> / <chemin>
Tu n'es pas seul dans le codebase. Ne revert jamais les changements des autres.
Ownership fichiers: <liste de dossiers/fichiers modifiables>
Fichiers a eviter: <liste>
Passerelle/registre de trace: <fichier>
Dernier point coordination lu: <fichier + heure>
Lease ownership: <expiration + fuseau> ; heartbeat dans docs/presence_agents.md
Donnees: pas de donnees privees dans Git ; instance privee uniquement en lecture locale.
Donnees de test locales par defaut: `C:\Users\brice\Documents\CoproScope\instances\beauvallon_test`.
Verification attendue: <commandes de test ou checks UI>
Livrable final: resume, fichiers modifies, limites, tests lances.
```

## Methode equipe agile multi-agents

La methode canonique est
[`docs/protocole_equipe_agile_agents.md`](./docs/protocole_equipe_agile_agents.md).
Elle est obligatoire quand une conversation demande une equipe agile,
des agents UX/dev/QA, ou des iterations rapides avec utilisateurs.

Resume d'execution:

1. le coordinateur rattache le travail au gouvernail `RM-*` et cree un `CH-*`;
2. il publie son `BOT-START`, puis une ligne `CONV-*` par role actif;
3. les roles standards sont coordinateur-scribe, designer/facilitateur,
   utilisateur novice, dev front, dev back/viewmodel et QA;
4. le travail tourne en double flux: `N-1` teste le produit livre, `N`
   developpe la commande validee, `N+1` prepare le visuel et la commande
   suivante;
5. chaque cycle nomme une UI reelle: route, ecran, modale, artefact HTML ou
   parcours local. Si l'UI manque, le premier objectif est de la rendre
   testable, pas de raisonner sur une intention abstraite;
6. des que le sujet est visuel, nouveau, ambigu ou sensible pour un novice, le
   designer produit une image ou un blueprint, puis le novice donne un
   GO/NO-GO avant tout dev;
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

## Ports locaux

Ne pas lancer deux interfaces sur le meme port. Choisir le port explicitement dans le brief agent; ne pas scanner les ports ou les processus, et ne pas arreter automatiquement un serveur par PID. Pour une verification UI, utiliser un terminal visible et `Ctrl+C` pour l'arret.

| Agent | Port conseille |
|---|---:|
| Coordinateur | 8765 |
| UI/actions | 8766 |
| ComptaScope | 8767 |
| Privacy/DocOps | 8768 |
| Demo/docs | 8769 |

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
