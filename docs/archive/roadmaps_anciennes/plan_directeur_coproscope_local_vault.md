# Plan directeur CoproScope local + vault

> Statut gouvernail: `SOURCE_HISTORIQUE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0004`). Ce plan sert de contexte d'architecture, pas de sprint actif.

Date de reference : 2026-05-20

Ce plan fusionne les plans existants en un seul fil directeur. Il est ecrit pour une personne qui decouvre CoproScope : quoi livrer d'abord, dans quel ordre, avec quels garde-fous, et comment reprendre le travail sans collision entre agents.

## Cap unique

CoproScope doit devenir un **cockpit local de travail pour conseil syndical**.

Le produit ne doit pas seulement ranger des documents. Il doit aider le conseil syndical a voir :

- ce qui demande attention ;
- quelles preuves existent ;
- quelles pieces manquent ;
- quelles questions poser au syndic ;
- quelles decisions d'AG doivent devenir des actions ;
- ce qui peut etre partage sans exposer de donnees sensibles.

La priorite visible est donc l'interface. Le vault et la synchronisation restent essentiels, mais comme support de confiance : ils garantissent que l'interface repose sur une source de verite locale, verifiable et synchronisable plus tard.

## Objectifs ajoutes a la roadmap

Ces objectifs sont integres dans la feuille de route produit, avec priorite a l'usage visible:

- rebrancher proprement le dossier local au GitHub canonique `github.com/bthollet/coproscope`, sans publier instance privee, `.venv`, caches, worktrees ou docs reelles;
- mettre a jour la documentation pour decrire clairement la strategie local-first, vault signe, plugins officiels et separation noyau/instance;
- ameliorer le workflow d'ajout de document: depot guide, hash, classification, rattachement, confidentialite, puis import vault quand actif;
- visualiser les PDF/images et annoter collaborativement sans modifier les originaux;
- integrer les demandes coproprietaires venant de canaux multiples: mail, courrier, extranet, formulaire, appel, AG, piece deposee;
- creer des raccourcis locaux et reconstruisibles vers les dossiers pertinents, sans dupliquer la source de verite;
- approfondir la preparation AG: convocation, ordre du jour, resolutions, annexes, questions syndic, pieces justificatives, suivi post-AG;
- approfondir la gestion des contentieux: chronologie, pieces, echeances, restrictions d'acces, exports controles;
- suivre les demandes/problemes par un journal d'actions concretes, manuel ou produit par DocOps/ComptaScope/AGOps;
- mettre en place les comptes utilisateurs avec niveau copro et niveau conseil syndical;
- prevoir les commissions thematiques d'assistance au CS avec mandat, referent CS, droits differencies, productions visibles et historique;
- securiser contre l'accaparement ou la suppression malveillante: aucun coproprietaire, membre CS, administrateur local ou appareil ne doit pouvoir confisquer seul l'information collective;
- permettre a un coproprietaire de telecharger l'archive complete, avec les parties sensibles chiffrees et inaccessibles sans cles, mais verifiables en presence/integrite;
- mettre en place une gouvernance des cles avec filets de secours: quorum, parts inutilisables seules, gardiens d'archive incluant au moins un coproprietaire non CS, verification periodique, recuperation signee en cas de defaillance du CS;
- gerer plusieurs coffres de copro sur le meme poste, a la maniere de plusieurs vaults Obsidian, avec isolation stricte des instances, vaults, cles, caches, roles, exports et journaux;
- explorer separement les gouvernances complexes: syndicat primaire/secondaire, ASL, unions, droits croises et equipements partages;
- installer les indicateurs centraux de gestion: consommations, entretien, amortissement/investissements, espaces verts, travaux, gouvernance, risques et demandes;
- garder l'accessibilite, les infobulles et le registre de langage comme criteres de qualite, car le produit doit rester intelligible pour les publics novices de l'enquete;
- preparer plusieurs transports de synchronisation: Google Drive Desktop, OneDrive, Dropbox, Nextcloud, support froid chiffre, et une option peer-to-peer de type Syncthing.

## Decisions non negociables

1. **Interface prioritaire** : la prochaine valeur utilisateur est le cockpit conseil syndical, pas une plateforme technique invisible.
2. **Vault source de verite** : a terme, l'etat metier doit etre reconstruit depuis des evenements signes append-only et des blobs chiffres, pas depuis des exports modifies a la main.
3. **Local-first** : l'application travaille dans une copie locale. Le cloud transporte au mieux un dossier de sync chiffre, jamais l'espace de travail en clair.
4. **Pas de Drive en ecriture** : les scripts, agents et prototypes ne doivent pas ecrire directement dans un Drive synchronise.
5. **Instances en Git local, pas GitHub** : chaque instance reelle peut etre un depot Git local pour l'historique prive; seul le noyau `coproscope` reste relie a GitHub.
6. **Pas de `.git` ni `.venv` en sync** : ces dossiers restent hors des dossiers synchronises et hors du vault.
7. **Donnees privees protegees** : les donnees reelles peuvent guider le produit localement, mais la demo et le depot public doivent rester fictifs ou suffisamment transformes.
8. **Anti-accaparement** : aucune personne ne doit etre l'unique gardien du vault. Les suppressions sont des evenements, les copies autorisees doivent pouvoir reconstruire l'historique, les coproprietaires doivent pouvoir telecharger une archive complete chiffree, et les restrictions d'acces doivent etre auditables.
9. **Coffres de copro isoles** : une installation locale peut ouvrir plusieurs coffres de copro, mais jamais partager implicitement cache, cles, sync, roles ou exports entre eux.
10. **Humain responsable** : CoproScope aide a controler, suivre et expliquer. Il ne remplace pas le syndic, le droit, l'expert comptable ni la validation humaine.

## Promesse publique anti-confiscation

Argument de communication a garder haut dans le produit:

- chaque coproprietaire peut conserver l'archive complete de la memoire collective;
- il peut ouvrir ce qui releve de son niveau d'acces;
- il ne peut pas lire les compartiments sensibles sans la bonne cle;
- il peut verifier que les parties chiffrees existent encore et n'ont pas ete alterees;
- la recuperation des cles critiques ne depend pas du seul conseil syndical en place.

## Ce que montrent les visuels cibles

Les images dans `docs/assets/etude-utilisateurs/` donnent la direction produit :

- `cockpit-conseil-syndical.png` : premiere page utile, centree sur priorites, preuves, risques et actions.
- `controle-comptes-guide.png` : ComptaScope doit parler a un conseil syndical, avec statuts `OK`, `P2`, `P1` et questions au syndic.
- `registre-decisions-actions-preuves.png` : chaque decision doit avoir une action, une preuve attendue et un statut.
- `memoire-copropriete.png` : CoproScope doit aider la passation entre conseils syndicaux.

Ces visuels sont des concepts cibles. L'interface locale v0 existe deja, mais elle doit encore rejoindre cette clarte.

## Ordre des sprints

### Sprint 0 - Jalon 20h : livrer une version testable

Objectif : que tout agent puisse reprendre sans deviner le cap.

Livrables :

- ce plan directeur ;
- un lien depuis `docs/README.md` ;
- une priorite explicite : interface d'abord, vault/sync en support ;
- des phrases de reprise simples ;
- une interface locale ouvrable par `ui open-test` ;
- des garde-fous anti-fuite et anti-sync dangereuse ;
- un protocole test novice.

La livraison de 19h30 est annulee au profit du jalon 20h du 20 mai 2026.
Apres 20h, le developpement continue sans reouvrir les questions deja tranchees.

Critere de fin a 20h le 20 mai 2026 :

- le plan est lisible par un novice ;
- il ne contient plus de contradiction entre interface, vault, local-first et sync ;
- les lots agents ont des frontieres claires ;
- les prochains travaux peuvent etre lances dans des worktrees separes ;
- l'UI locale demarre en mode visible compatible antivirus ;
- les prochaines etapes restent guidees par l'enquete utilisateur et la strategie Obsidian-like.

### Sprint 1 - Interface locale testable

Objectif : livrer une version que l'on peut ouvrir et comprendre sans lire les CSV.

Livrables :

- cockpit conseil syndical avec priorites ;
- vue documents : presents, manquants, obsoletes, a demander ;
- vue comptes guidee : `OK`, `P2`, `P1`, questions au syndic, rapport AG ;
- vue confidentialite : diffusable, a biffer, bloque, a revoir ;
- vue actions : decisions AG, demandes syndic, incidents et preuves attendues ;
- copro demo fictive, separee des donnees privees.

Critere de fin :

- l'app locale demarre ;
- les vues principales repondent ;
- une personne non technique comprend quoi traiter ensuite ;
- aucune route ne sert les documents bruts prives.

### Sprint 2 - Chaines metier visibles

Objectif : rendre les parcours critiques vraiment actionnables.

Livrables :

- SyndicOps complet : statuts, echeances, relances, pieces attendues, preuves de reponse ;
- DecisionOps raccorde : resolution AG -> action -> preuve -> statut ;
- WorksOps minimal : devis, travaux, assurances, reception, garanties ;
- IncidentOps enrichi : signalement, priorite, statut, preuve de cloture ;
- CommsOps minimal : syntheses sobres et diffusables.

Critere de fin :

- chaque sujet prioritaire a une prochaine action ;
- les preuves attendues sont visibles ;
- les exports restent locaux, sobres et prudents.

### Sprint 3 - Vault local verifiable

Objectif : stabiliser le support de confiance sans bloquer l'interface.

Livrables :

- format vault V1 confirme ;
- evenements metier signes ;
- commandes `vault init`, `import`, `status`, `verify`, `snapshot` ;
- reconstruction SQLite locale depuis les evenements ;
- regles de confidentialite du dossier sync.

Critere de fin :

- le vault peut etre cree, importe, verifie et snapshotte localement ;
- les exports CSV, Markdown, PDF et bases analytiques sont clairement derives ;
- le dossier sync ne revele ni contenu lisible, ni noms reels, ni chemins utilisateur.

### Sprint 4 - Sync dossier cloud et conflits

Objectif : permettre deux copies locales sans casser la confiance.

Livrables :

- sync par dossier chiffre ;
- detection de divergences ;
- resolution de conflits explicite ;
- identites locales et signatures ;
- interdiction documentee de synchroniser `.git`, `.venv`, caches dechiffres et espaces de travail en clair.

Critere de fin :

- deux copies locales peuvent echanger via un dossier chiffre ;
- un conflit est visible, explicable et resoluble ;
- aucun secret ni cache clair ne part dans le dossier sync.

### Sprint 5 - Plugins signes, packaging et produit fini

Objectif : rendre le produit extensible et distribuable.

Livrables :

- plugins officiels signes pour traitements lourds ;
- permissions, compatibilite et revocation ;
- packaging desktop local ;
- mises a jour signees ;
- documentation de passation et de restauration.

Critere de fin :

- les extensions ne compromettent pas le vault ;
- une installation locale peut etre livree, mise a jour et restauree ;
- le produit reste comprehensible pour un conseil syndical.

## Roles agents

| Role | Mission | Perimetre type |
|---|---|---|
| Agent Plan Directeur/Fusion | Maintenir le cap unique, lever les contradictions, rendre la reprise simple. | Documentation de synthese seulement. |
| Agent Interface | Construire les vues cockpit, documents, comptes, confidentialite et actions. | `server/src/coproscope/web/**` et tests UI dedies. |
| Agent View model CS | Transformer les registres en donnees lisibles par l'interface. | Couche de presentation et tests associes. |
| Agent Demo/Privacy | Garantir une demo fictive et des garde-fous de publication. | Generation demo, validations, rapports privacy. |
| Agent Specs vault | Durcir format, signatures, evenements et plugins. | Docs vault uniquement. |
| Agent Batch transition | Fiabiliser audit local, migration et scripts Windows. | `tools/transition/**` et doc batchs. |
| Agent Tests vault | Couvrir le prototype vault sans modifier l'implementation. | Tests vault. |
| Agent Reconstruction locale | Preparer SQLite reconstruite et conflits, apres specs stabilisees. | Code vault, hors UI. |

Regle commune : un agent recoit une branche `codex/<sujet>`, un worktree local sous `_worktrees`, et une liste courte de fichiers autorises. Il commence par `git status` et termine par les fichiers modifies et les tests pertinents.

## Definition d'une version testable

Une version testable n'est pas encore le produit fini. Elle doit permettre de juger la promesse.

Elle contient :

- une interface locale ouvrable ;
- une copro demo fictive ;
- au moins les vues cockpit, documents, comptes, confidentialite et actions ;
- des statuts clairs : livre, chantier, bloque, a revoir ;
- des exports locaux prudents ;
- des tests serveur ou UI pertinents ;
- une absence de fuite volontaire de donnees brutes privees.

Un novice doit pouvoir repondre apres 10 minutes :

1. Quels sont les trois sujets les plus urgents ?
2. Quelle preuve existe pour chacun ?
3. Quelle action faire ensuite ?
4. Que peut-on partager sans risque evident ?

## Definition du produit fini

Le produit fini est un cockpit local-first pour conseil syndical, appuye sur un vault verifiable.

Il doit fournir :

- un cockpit quotidien ;
- un controle comptes guide ;
- un suivi demandes syndic ;
- un registre decisions-actions-preuves ;
- un dossier travaux ;
- un suivi incidents ;
- une memoire de copropriete transmissible ;
- des syntheses diffusables apres controle confidentialite ;
- une source de verite locale reconstruite depuis le vault ;
- une sync chiffree optionnelle entre copies locales ;
- des plugins officiels signes pour les traitements avances.

Il ne doit pas devenir a court terme :

- un SaaS multi-tenant ;
- une app mobile native complete ;
- un reseau social ;
- un vote electronique complet ;
- un chatbot autonome sans sources citees ;
- un outil qui ecrit directement dans Drive.

## Batches de reprise simples

### Batch A - Interface novice

Phrase de reprise :

```text
Travaille dans un worktree local sur une branche codex/interface-cockpit. Priorite : rendre le cockpit conseil syndical comprehensible par un novice. Ne touche pas au vault, aux scripts de transition, a .git, a .venv ni a un dossier Drive. Termine avec les routes testees et la liste des fichiers modifies.
```

### Batch B - Documents et confidentialite

Phrase de reprise :

```text
Travaille dans un worktree local sur une branche codex/interface-docs-privacy. Objectif : vue documents presents/manquants/obsoletes/a demander et vue diffusion/biffage/bloquage. Aucun document brut prive ne doit etre servi par l'interface. Termine avec les tests et les fichiers modifies.
```

### Batch C - Comptes et AG

Phrase de reprise :

```text
Travaille dans un worktree local sur une branche codex/comptascope-guide-ag. Objectif : rendre ComptaScope lisible pour un conseil syndical avec statuts OK/P2/P1, questions au syndic et sortie AG. Ne modifie pas les specs vault. Termine avec les tests pertinents.
```

### Batch D - Decisions, actions, preuves

Phrase de reprise :

```text
Travaille dans un worktree local sur une branche codex/decision-action-preuve-ui. Objectif : raccorder les decisions AG, demandes syndic, incidents et preuves attendues dans une vue actionnable. Ne change pas le format vault. Termine avec les tests et les fichiers modifies.
```

### Batch E - Vault support

Phrase de reprise :

```text
Travaille dans un worktree local sur une branche codex/vault-support. Objectif : consolider format vault, evenements signes, verification et snapshot comme support de confiance. Ne touche pas a l'interface. Le dossier sync doit rester chiffre et ne jamais contenir .git, .venv, cache dechiffre ou chemins utilisateurs lisibles.
```

### Batch F - Transition locale

Phrase de reprise :

```text
Travaille dans un worktree local sur une branche codex/transition-locale. Objectif : fiabiliser les batchs Windows d'audit, migration et controle local. Les scripts ne doivent jamais ecrire dans Drive ni synchroniser .git ou .venv. Termine avec un rapport relancable.
```

## Lecture recommandee

Pour comprendre le pourquoi :

- `docs/etude_utilisateurs.md`
- `docs/feuille_de_route.md`
- `docs/registre_suivi_livraison_interface.md`

Pour comprendre le support vault :

- `docs/transition_vault_collaboratif.md`
- `docs/vault_format.md`
- `docs/signatures_historique.md`
- `docs/objets_metier_evenements_v1.md`

Pour lancer plusieurs agents :

- `docs/reprise_agents_paralleles_vault.md`
- `docs/orchestration_agents.md`
- `docs/lots_paralleles.md`

## Resume en une phrase

Livrer d'abord un cockpit local utile a un conseil syndical ; construire le vault signe et la sync chiffree comme la colonne de confiance qui permettra ensuite de collaborer sans exposer les donnees.
