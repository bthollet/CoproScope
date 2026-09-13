# QA UI/UX - version testable 21h15

Date de reference: 2026-05-20, passe 21h15.

Contrainte de verification: revue statique uniquement. Aucun serveur lance, aucun navigateur ouvert. Les constats ci-dessous viennent de la lecture des docs produit/QA, des templates Jinja, du CSS, du viewmodel, des routes FastAPI et des tests UI existants.

Fichiers lus en priorite:

- `docs/roadmap_produit_fini_visuels_enquete.md`
- `docs/livraison_test_2000.md`
- `docs/qa_ui_integration_2000.md`
- `docs/strategie_obsidian_like_enquete_utilisateur.md`
- `docs/accessibilite_registre_langage.md`
- `docs/indicateurs_pilotage_copro.md`
- `server/src/coproscope/web/templates/*.html`
- `server/src/coproscope/web/app.py`
- `server/src/coproscope/web/viewmodel.py`
- `server/src/coproscope/web/governance.py`
- `server/src/coproscope/web/static/styles.css`

## Verdict

La version 21h15 est testable comme cockpit local de demonstration, mais elle n'est pas encore testable comme produit novice complet.

Le produit a franchi un palier net depuis la passe 20h:

- le cockpit affiche maintenant des cartes `A faire maintenant` avec pourquoi, preuve/source, prochaine action et prudence de diffusion;
- le depot explique mieux le local, l'absence de sync cloud et l'exclusion des bruts/restreints/secrets dans les exports UI;
- la gouvernance introduit les sujets comptes, droits, commissions, multi-coffres, archive, survivabilite et indicateurs;
- les comptes sont plus pedagogiques avec `P1`, `P2`, `OK` et questions pretes pour le syndic;
- le socle accessibilite existe: `lang=fr`, lien d'evitement, `aria-current`, focus visible, textes qui se cassent sur mots longs.

Les risques bloquants pour un test utilisateur novice sont encore:

- jargon moteur encore visible au premier niveau;
- session/token et exports pas assez coherents;
- comptes, roles et coffre actif pas assez visibles dans le bandeau;
- multi-coffres presentes comme concept mais pas encore comme parcours `Mes coffres`;
- demandes coproprietaires encore absorbees dans syndic/actions au lieu d'une boite de demandes lisible;
- AG/contentieux non encore traites comme dossiers probatoires separes;
- indicateurs encore descriptifs, pas encore periodises avec preuve, seuil et action;
- aides `title` non suffisantes pour clavier/tactile;
- plusieurs ecrans restent des tables denses sans fiche novice.

## Points bloquants et quasi bloquants

### P0 - Aucun P0 confirme sans execution

Je n'ai pas lance la version ni ouvert de navigateur, donc je ne confirme pas l'absence de 500, page blanche ou erreur de rendu. La QA 20h demandait deja une verification HTTP des routes principales; cette passe 21h15 ne la remplace pas.

### P1 - Token et exports incoherents avec la promesse locale prudente

Observation:

- `/depot`, `/api/model` et `/exports/local.zip` exigent le token quand il existe;
- `/actions`, `/exports/actions.csv` et `/exports/actions.md` ne l'exigent pas;
- plusieurs liens internes vers `/actions?...` et exports ne propagent pas `ui_token_query`;
- le cockpit propose `Exporter CSV` sans token.

Risque UX/securite: un novice voit un lien tokenise puis tombe sur des zones non tokenisees ou exporte des actions sans comprendre le perimetre de protection. Meme si l'UI ecoute en loopback, la promesse "local prudent" perd en clarte.

Action recommandee:

- appliquer une regle unique: soit toute l'UI de test est tokenisee, soit le token est reserve aux mutations/exports sensibles et l'interface l'explique clairement;
- propager le token sur tous les liens internes quand un token est actif;
- proteger ou assumer explicitement les exports actions, car ils peuvent contenir titres, preuves, responsables et prochaines etapes.

Critere de sortie:

- un test statique verifie que tous les liens Jinja vers routes protegees conservent le token;
- un test route confirme le statut attendu avec et sans token pour `/depot`, `/exports/local.zip`, `/exports/actions.csv`, `/exports/actions.md`, `/api/model`.

### P1 - Premier niveau encore trop "moteur CoproScope"

Observation:

- la navigation et les titres exposent encore `DocOps`, `SyndicOps`, `AGOps`, `PrivacyOps / BiffageOps`, `ComptaScope`, `DocAI local-heavy`, `vault`, `hash`;
- les ecrans Documents, Pieces, Confidentialite et Depot sont utilisables par un agent QA, mais un coproprietaire novice ne saura pas toujours quelle action concrete faire.

Risque UX: l'utilisateur comprend que l'outil est puissant, mais pas forcement qu'il peut l'aider aujourd'hui.

Action recommandee:

- garder les noms moteurs dans `Details techniques` ou dans des badges secondaires;
- preferer en titre: `Pieces et preuves`, `Demandes au syndic`, `Diffusion et masquage`, `Controle des comptes`, `Coffre de copro`;
- ajouter une micro-definition proche du premier usage de chaque terme rare.

Critere de sortie:

- aucun titre H2/H3 de parcours novice ne commence par un nom d'operation interne;
- chaque terme rare visible a une aide accessible au clavier/tactile.

### P1 - Identite, role et coffre actif manquent dans le cadre global

Observation:

- le header affiche instance et exercice, mais pas le role courant, le coffre actif, le statut vault/sync, ni le niveau d'acces;
- la page Gouvernance explique les concepts, mais le novice ne voit pas partout "qui suis-je, dans quel coffre, qu'ai-je le droit de voir".

Risque produit: les futurs comptes, commissions, droits, multi-coffres et sync peuvent etre techniquement corrects mais rester incompris. C'est aussi un risque de fuite entre coffres si l'utilisateur ne voit pas le contexte actif.

Action recommandee:

- ajouter un bandeau global compact: `Coffre`, `Role`, `Acces`, `Vault`, `Sync`, `Derniere verification`;
- introduire un parcours premier demarrage: profil local, ouvrir/creer coffre, role initial, appareil de signature, phrase/kit de secours;
- distinguer clairement `compte local`, `membre du coffre`, `appareil signeur`, `role copro/CS/commission`.

Critere de sortie:

- en moins d'une minute, un novice sait repondre: qui suis-je dans ce coffre, que puis-je voir, que puis-je faire, qui peut recuperer l'archive.

### P1 - Accessibilite des aides et tables encore fragile

Observation:

- les `help-dot` reposent sur `title`; ce n'est pas suffisant au clavier, au tactile ou pour certains lecteurs d'ecran;
- les tables n'ont pas de `<caption>` visible ou accessible;
- le champ upload n'a pas de label explicite;
- les lignes cliquables de l'atelier utilisent `onclick` sur `<tr>` avec `tabindex=0`; c'est praticable mais fragile, surtout avec liens imbriques.

Risque UX/accessibilite: le produit semble clair a la souris desktop, mais le parcours clavier/tactile et lecteurs d'ecran reste incomplet.

Action recommandee:

- remplacer les aides `title` par un bouton aide avec texte visible au focus/clic ou un `aria-describedby`;
- ajouter des captions aux tables principales;
- ajouter un label visible pour le champ fichier du depot;
- preferer une action explicite `Ouvrir` par ligne, et limiter les `onclick` de ligne aux vues avancees.

Critere de sortie:

- test statique sur captions, labels upload, aide accessible, `aria-current`, lien d'evitement;
- parcours clavier manuel sur cockpit, actions, comptes, depot, gouvernance.

## Revue par surface

### Cockpit

Ce qui marche:

- `A faire maintenant` est la bonne direction: cartes priorisees avec pourquoi/preuve/action/partage;
- les alertes cockpit, preuves, confiance et modules donnent une vue large;
- le message "Jour de conseil syndical" correspond bien a l'enquete utilisateur.

Risques:

- certains liens internes ne propagent pas le token;
- les KPI restent surtout des compteurs, pas encore des indicateurs de gestion avec periode, seuil, preuve et prochaine action;
- le bloc `Confiance, signature, vault` annonce `Pack local pret` et `Vault chiffre/signe a raccorder`, mais le statut de coffre actif n'est pas global.

Actions:

- passer de 3 cartes a 5 cartes max si cela couvre comptes, demandes, diffusion, AG/contentieux, preuve manquante;
- ajouter source, periode et niveau de confiance sur les indicateurs;
- afficher le coffre/role/sync dans le header, pas seulement dans Gouvernance.

### Actions / registre

Ce qui marche:

- l'ecran rassemble decisions, relances, responsables, preuves et conflits;
- les filtres par perimetre et statut sont utiles;
- les exports CSV/Markdown facilitent le travail CS.

Risques:

- l'ecran reste tres tabulaire;
- les statuts `a_demander`, `a_traiter`, `a_verifier`, `a_revoir`, `bloque` doivent etre traduits en langage humain;
- les demandes coproprietaires ne sont pas identifiees comme un canal propre.

Actions:

- ajouter en haut une file `3 relances a faire cette semaine`;
- ajouter une fiche action lisible: contexte, preuve, message pret, responsable, echeance, diffusion;
- separer les demandes coproprietaires entrantes des demandes au syndic, tout en gardant un journal d'actions commun.

### Comptes

Ce qui marche:

- `P1`, `P2`, `OK` sont expliques;
- les questions syndic pretes sont un excellent objet UX;
- les preuves rattachees et blocages sont visibles.

Risques:

- `ComptaScope` reste un nom moteur en premier niveau;
- les tables peuvent intimider un membre CS novice;
- il manque une synthese AG courte: "a poser en AG", "a demander avant AG", "deja justifie".

Actions:

- renommer le premier niveau en `Controle des comptes`;
- ajouter une sortie `Questions a envoyer au syndic`;
- produire une synthese avant AG avec preuves citees et prudence de diffusion.

### Documents et atelier pieces

Ce qui marche:

- la separation present/manquant/obsolete/a demander est claire;
- l'atelier commence a relier piece, point, action et preuve;
- la fiche document introduit apercu, metadonnees, preuve, annotations, ancres, historique et confidentialite.

Risques:

- `Documents`, `Pieces` et `Preuves` restent proches; le novice peut ne pas comprendre la difference;
- le parcours annotation semble surtout informatif;
- les chemins/artefacts techniques peuvent prendre trop de place.

Actions:

- afficher une micro-definition: document = fichier ajoute, piece = document utile a un sujet, preuve = ce que la piece confirme;
- faire de la fiche document le lieu de rattachement `piece -> point -> action -> preuve`;
- masquer les artefacts techniques derriere `Details techniques`.

### Depot

Ce qui marche:

- la page dit explicitement que le depot reste local;
- elle distingue depot, traitement local, rattachement et exports;
- elle rappelle l'exclusion des bruts, secrets, restreints et mappings sensibles.

Risques:

- `DocAI local-heavy`, `DocOps`, `Compta` sont trop techniques;
- pas de garde visible contre double clic ou traitement long;
- le champ upload manque de label explicite;
- les chemins locaux du depot selectionne peuvent inquieter un novice.

Actions:

- renommer les boutons: `Extraire le texte`, `Classer les pieces`, `Controler les comptes`, `Tout traiter sauf IA lourde`;
- ajouter etat en cours/desactivation au clic;
- afficher les chemins en detail technique.

### Gouvernance, comptes, multi-coffres

Ce qui marche:

- les roles copro/CS/commission et les droits croises sont poses;
- la page montre les risques d'archive, les demandes syndic, les indicateurs et l'anti-accaparement;
- les concepts multi-coffres et gouvernance complexe sont separes dans la doc.

Risques:

- l'ecran melange beaucoup de notions avancees;
- ce n'est pas encore un vrai parcours `Mes coffres de copro`;
- pas de tableau `Membres et droits` operationnel;
- les comptes utilisateurs ne sont pas encore une experience de demarrage.

Actions:

- scinder: `Mes coffres`, `Membres et droits`, `Survie de l'archive`, `Organisations liees`;
- ajouter un switcher de coffre et un diagnostic anti-melange;
- afficher pour chaque role: peut voir, peut modifier, peut exporter, peut recuperer.

### Demandes coproprietaires, syndic et alertes

Ce qui marche:

- les demandes syndic existent dans gouvernance et actions;
- les relances et preuves attendues alimentent le cockpit.

Risques:

- la boite de demandes coproprietaires multi-canaux n'est pas encore visible;
- les alertes semblent derivees de registres, pas encore d'un journal signe d'entree/action/reponse;
- pas de distinction claire entre demande d'un coproprietaire, demande au syndic, incident et action interne CS.

Actions:

- creer une boite `Demandes` avec canal, emetteur, sujet, statut, echeance, action log, preuve attendue;
- relier chaque demande a une action syndic, incident, AG, travaux ou diffusion;
- ajouter alertes: en retard, sans responsable, sans preuve, diffusion bloquee, doublon probable.

### AG et contentieux

Ce qui marche:

- DecisionOps et la passation montrent les decisions non cloturees et preuves attendues;
- les restrictions de diffusion sont visibles dans Confidentialite et Memoire.

Risques:

- l'AG n'a pas encore d'atelier dedie: convocation, ordre du jour, questions, pieces, resolutions, suivi post-AG;
- le contentieux est surtout dans la roadmap, pas encore dans l'UI;
- risque de confondre analyse produit et avis juridique.

Actions:

- ajouter un dossier `Preparation AG` avec pieces utiles, questions syndic, points a porter et preuves manquantes;
- ajouter un dossier `Contentieux / risque` restreint: chronologie, echeances, pieces, restrictions, exports controles;
- afficher partout "a valider humainement, ne remplace pas un conseil juridique".

### Indicateurs

Ce qui marche:

- la page Gouvernance liste les themes centraux: consommations, entretien, investissements, espaces verts, travaux, gouvernance;
- la doc indicateurs pose les bons garde-fous.

Risques:

- les indicateurs ne sont pas encore des cartes de pilotage;
- manque periode, source, preuve, seuil, confiance et prochaine action;
- risque d'exposer une donnee restreinte par agregation trop precise.

Actions:

- limiter le cockpit a 6-10 cartes indicateurs maximum;
- chaque carte doit dire: periode, source, preuve, statut, pourquoi, prochaine action;
- ajouter tests anti-fuite sur indicateurs agreges.

## Scenarios de test novice 21h15

### Scenario 1 - Comprendre quoi faire maintenant

But: verifier la promesse cockpit.

Etapes:

1. Ouvrir Cockpit.
2. Demander au testeur de citer les trois sujets prioritaires.
3. Lui demander pour chacun: pourquoi, quelle preuve, quelle prochaine action, partageable ou non.

Go:

- le testeur trouve sans aide au moins trois actions;
- il distingue preuve disponible et preuve a demander;
- il comprend qu'une diffusion doit etre verifiee.

No-go:

- il lit surtout les noms de modules;
- il ne sait pas quoi faire ensuite;
- il pense qu'un export est automatiquement diffusable.

### Scenario 2 - Ajouter une piece sans croire a une sync cloud

But: verifier Depot et langage local.

Etapes:

1. Ouvrir Depot.
2. Demander ce qui se passe si on depose un fichier.
3. Demander si cela publie, synchronise ou ajoute au coffre verifie.

Go:

- le testeur repond: copie locale, traitement local, rattachement, pas de sync automatique.

No-go:

- il pense que le depot publie dans le cloud;
- il pense que le vault signe est deja garanti.

### Scenario 3 - Controle des comptes avant AG

But: verifier pedagogie comptes.

Etapes:

1. Ouvrir Comptes.
2. Demander la difference entre `P1`, `P2`, `OK`.
3. Faire trouver une question a envoyer au syndic.

Go:

- le testeur comprend que `P2` n'est pas une faute definitive;
- il trouve une question prete et une preuve attendue.

No-go:

- il confond score technique et decision humaine.

### Scenario 4 - Qui voit quoi

But: verifier comptes, roles, commissions et coffre.

Etapes:

1. Ouvrir Gouvernance.
2. Demander le role courant, le coffre actif, ce qu'une commission peut voir.
3. Demander qui peut recuperer l'archive si le CS defaille.

Go:

- le testeur comprend les droits differencies et le besoin de gardiens de secours.

No-go:

- il ne sait pas dans quel coffre il est;
- il pense qu'une commission voit tout le CS;
- il pense qu'une seule personne peut confisquer ou recuperer seule.

## Priorites de correction

1. Harmoniser token, routes protegees et exports actions.
2. Ajouter bandeau global coffre/role/acces/vault/sync.
3. Remplacer les titres jargon par langage novice et aides accessibles.
4. Ajouter labels upload, captions de tables et aides non `title`.
5. Transformer Actions en vraie file de travail avec fiches action.
6. Creer la boite Demandes multi-canaux.
7. Creer les parcours AG et Contentieux restreints.
8. Transformer Gouvernance en parcours `Mes coffres`, `Membres et droits`, `Archive`.
9. Faire des indicateurs de vraies cartes preuve/periode/seuil/action.

## Decision QA

Go pour une demonstration technique encadree sur instance synthetique.

No-go pour un test utilisateur novice non accompagne tant que le contexte coffre/role, le langage novice, le token/export, les aides accessibles et la boite demandes ne sont pas clarifies.
