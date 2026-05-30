# Roadmap produit fini depuis les visuels d'enquete

> Statut gouvernail: `SOURCE_HISTORIQUE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0003`, `RM-2026-0007`). Convertir toute suite en item `RM-*`.

Date de reference: 2026-05-20

Ce document transforme les visuels de l'etude utilisateurs en plan de developpement executable. Le but n'est pas de recopier des maquettes: le but est d'arriver a un produit local, probatoire et collaboratif ou un conseil syndical voit quoi traiter, pourquoi, avec quelle preuve, et ce qui peut etre partage.

Visuels sources:

- `docs/assets/etude-utilisateurs/cockpit-conseil-syndical.png`
- `docs/assets/etude-utilisateurs/registre-decisions-actions-preuves.png`
- `docs/assets/etude-utilisateurs/controle-comptes-guide.png`
- `docs/assets/etude-utilisateurs/memoire-copropriete.png`

Plans fusionnes dans cette roadmap:

- demandes multicanal: `docs/demandes_coproprietaires_multicanal.md`,
  `docs/demandes_coproprietaires_multicanaux.md`,
  `docs/ui_demandes_coproprietaires.md`;
- preparation AG: `docs/preparation_ag_ux.md`,
  `docs/ag_contentieux_passation.md`,
  `docs/ui_ag_contentieux_passation.md`;
- contentieux: `docs/contentieux_ux.md`,
  `docs/ag_contentieux_passation.md`,
  `docs/resilience_anti_accaparement.md`;
- comptes utilisateurs, roles et commissions:
  `docs/identites_comptes_roles.md`,
  `docs/commissions_thematiques.md`;
- anti-confiscation, archives, multi-coffres et sync:
  `docs/archive_reconstruction_coproprietaire.md`,
  `docs/resilience_anti_accaparement.md`,
  `docs/strategie_obsidian_like_enquete_utilisateur.md`,
  `docs/vault_sync_alerts.md`;
- indicateurs, veille open source, accessibilite et suggestions:
  `docs/indicateurs_pilotage_copro.md`,
  `docs/veille_open_source_integration.md`,
  `docs/accessibilite_registre_langage.md`,
  `docs/suggestions_amelioration.md`.

Regle de fusion: ces plans restent generiques et ne doivent pas embarquer de
donnees Drive privees, noms reels, chemins personnels, exports sensibles ou
captures d'instance. Les exemples doivent rester synthetiques.

## Cap produit

CoproScope doit devenir une application locale installee hors vault, centree sur cinq espaces:

1. Cockpit conseil syndical.
2. Atelier de piece.
3. Registre decisions -> actions -> preuves.
4. Controle des comptes guide.
5. Memoire de copropriete et passation.

Les objectifs ajoutes le 2026-05-20 et deviennent des chantiers de meme niveau:

6. Depot documentaire guide, visualisation PDF et annotations collaboratives.
7. Demandes coproprietaires multi-canaux et suivi syndic/action log.
8. Preparation AG, contentieux et dossiers probatoires sensibles.
9. Comptes utilisateurs, roles copro/CS et commissions thematiques.
10. Raccourcis locaux vers les bons dossiers/docs sans dupliquer la source de verite.
11. Resilience anti-accaparement: aucun membre, administrateur local, CS ou coproprietaire mal intentionne ne doit pouvoir confisquer ou supprimer unilateralement l'information collective.
12. Multi-coffres local: une meme installation sur un poste peut ouvrir plusieurs coffres de copro, comme plusieurs vaults Obsidian, chacun avec instance, vault, cles, roles, exports et caches strictement separes.
13. Pilotage par indicateurs centraux: consommations, entretien, investissements, espaces verts, travaux, gouvernance, risques et demandes doivent devenir des tableaux de suivi relies aux preuves.
14. Veille technologique open source: identifier les briques utiles, evaluer licence, securite, maintenance, integration locale et separation noyau/plugin avant toute adoption.
15. Suggestions d'amelioration: proposer des ameliorations concretes, sourcées et actionnables de gestion copro, sans decision automatique ni recommandation non justifiee.

Le vault signe devient la source de verite collaborative. Les CSV/Markdown/PDF restent des exports derives.

## Etat actuel utile

- UI FastAPI/Jinja locale avec vues metier.
- Vue `/pieces` "Atelier pieces" en lecture prioritaire.
- Prototype vault: `init`, `import`, `status`, `verify`, `snapshot`.
- Reconstruction SQLite locale amorcee dans `coproscope.vault.reconstruction`.
- Registres existants: documents, demandes, AG, decisions/actions/preuves, incidents, compta, confidentialite.
- Tests serveur complets verts: 91 tests au dernier controle local complet.
- Depot local et commande `ui open-test` pour demo visible, sans process cache.

## Garde-fou GitHub

Ce dossier local doit etre rebranche proprement au depot canonique
`github.com/bthollet/coproscope`.

Etat observe le 2026-05-20:

- `origin` pointe vers `https://github.com/bthollet/CoproScope.git`;
- la branche de travail d'integration est `codex/integration-livraisons`;
- aucun dossier d'instance, `.venv`, `.git` externe, cache ou worktree ne doit etre publie.

Livrables:

- verifier que le remote GitHub voulu est bien le depot produit public;
- documenter la strategie dans `README.md`, `docs/README.md` et ce plan;
- pousser seulement code, docs generiques, exemples synthetiques et tests;
- garder les docs d'instance, preuves reelles, passations operationnelles et exports prives hors repo.

## Priorite haute - Comptes utilisateurs

Objectif: rendre CoproScope utilisable par des personnes non techniques sans confondre compte local, identite de signature, role dans la copropriete, droits de lecture et pouvoir de recuperation des cles. La gestion des comptes devient un chantier haut dans la roadmap, car elle conditionne commissions, coffre partage, notifications, anti-confiscation et confiance dans les signatures.

Recherche a mener en premier:

- comparer les strategies `local-only`, compte cloud facultatif, compte par coffre, compte par appareil, et identite membre/appareil separee;
- evaluer les options Windows: mot de passe de coffre, secret membre, Windows Hello/DPAPI en option locale, fichier de secours, QR/invitation hors ligne;
- definir le modele de confiance V1 sans serveur central: le vault connait les membres, appareils, cles publiques, roles et revocations par evenements signes;
- etudier la separation `compte utilisateur` / `profil local` / `membre du vault` / `appareil signeur`;
- prevoir les niveaux coproprietaire, membre CS, referent commission, contributeur ponctuel, administrateur local technique et auditeur lecture seule;
- arbitrer les droits par ressource: piece, preuve, point, action, export, commission, lot privatif, contentieux, finances, donnees personnelles;
- documenter les limites: une revocation bloque les acces futurs mais n'efface pas ce qui a deja ete dechiffre localement;
- definir les notifications minimales V1: notifications dans le coffre par evenement signe, puis connecteurs email/messagerie uniquement en plugin officiel.

Implementation progressive:

- Sprint comptes 0: spec `identites_comptes_roles.md` avec parcours novice, roles, droits, revocation, recuperation, audit;
- Sprint comptes 1: objets noyau `UserAccount`, `LocalProfile`, `VaultMember`, `DeviceIdentity`, `RoleGrant`, `AccessGrant`, `CommissionMembership`, `RecoveryShare`;
- Sprint comptes 2: premier demarrage UI: creer profil local, ouvrir/creer coffre, choisir role initial, generer appareil de signature, afficher phrase de secours;
- Sprint comptes 3: invitations et revocations signees, avec journal lisible et effets sur les futurs droits;
- Sprint comptes 4: ecran `Membres et droits`: coproprietaires, CS, commissions, appareils, cles, dernier evenement signe, risques;
- Sprint comptes 5: tests d'acces par fixture synthetique: coproprietaire simple, CS, commission espaces verts, commission comptes, auditeur;
- Sprint comptes 6: raccordement aux alertes de vault: qui est notifie, qui peut verrouiller, qui peut deverrouiller, qui peut reconstruire.

Critere produit: un novice doit comprendre en moins d'une minute `qui suis-je dans ce coffre`, `ce que je peux voir`, `ce que je peux faire`, `qui peut recuperer si le CS defaille`.

## Principe UX commun

Chaque ecran doit repondre aux quatre questions de l'etude:

- Qu'est-ce qui demande attention ?
- Quelle preuve avons-nous ?
- Quelle action est legitime maintenant ?
- Que peut-on partager, avec qui, et sous quelle forme ?

Chaque ligne importante doit pouvoir ouvrir l'atelier de piece ou une fiche de suivi. Chaque action mutable doit produire un evenement signe.

Publics guides:

- coproprietaire novice, parfois peu familier des notions de syndic, AG, tantiemes, fonds travaux ou conseil syndical;
- membre de conseil syndical benevole, souvent deborde, qui veut savoir quoi faire maintenant;
- referent de commission thematique, utile sur un sujet mais sans acces automatique a tout;
- contributeur avance ou agent technique, qui doit pouvoir verifier sans rendre l'interface illisible pour les autres.

Regle de conception: l'interface doit etre intelligible pour les noobs de la copro. Les mots metier restent possibles, mais ils doivent etre expliques au moment utile par infobulles, micro-definitions, exemples, libelles stables et parcours guides. Les vues avancees ne doivent pas polluer le premier niveau de lecture.

Accessibilite et langage:

- vocabulaire stable: coffre, piece, preuve, point, action, diffusion, restriction, signature, statut, echeance;
- registre de langage documente: un terme = une definition produit, pas trois synonymes selon les ecrans;
- infobulles courtes sur les notions rares: tantiemes, fonds travaux, biffage, quorum, commission, compartiment de cle, vault;
- libelles explicites avant jargon technique: `Coffre de copro` avant `vault`, `preuve verifiee` avant `hash`;
- contrastes suffisants, navigation clavier, etats de focus visibles, textes de boutons actionnables;
- tableaux scannables avec colonnes limitees, tri/filtres simples et details dans une fiche;
- chaque indicateur ou statut doit dire `pourquoi`, `preuve`, `prochaine action`, pas seulement afficher un score.

## Retour testeur UX/UI expert

Diagnostic de la passe agent approfondie du 2026-05-20: la version testable est solide techniquement, mais elle parle encore trop "moteur CoproScope" et pas assez "conseil syndical benevole qui doit decider quoi faire maintenant".

Priorites immediates:

- cockpit: afficher d'abord 3 a 5 cartes `A faire maintenant`, chacune avec pourquoi, preuve/source, prochaine action et prudence de diffusion;
- vocabulaire: baisser `DocOps`, `SyndicOps`, `PrivacyOps`, `BiffageOps`, `DocAI`, `vault`, `hash` au second niveau ou les expliquer;
- navigation: faire emerger un parcours guide `Jour de conseil syndical`, sans demander au novice de comprendre toute l'architecture produit;
- ateliers: concentrer la boucle piece -> point -> action -> preuve dans l'atelier, avec badges de diffusion;
- depot: transformer les pipelines techniques en etapes compréhensibles: recu sur ce PC, classe, verifie confidentialite, rattache a une action;
- confidentialite: afficher le statut de diffusion la ou l'utilisateur agit, pas seulement dans une page separee;
- accessibilite: remplacer les infobulles `title` seules par aides accessibles clavier/tactile pour les termes rares;
- tests: ajouter des contrats UX statiques sur prochaine action visible, vocabulaire defini, `aria-current`, lien d'evitement, labels upload, captions tables et etats vides utiles.

Ce retour devient un critere de priorisation: si deux taches techniques sont possibles, choisir celle qui rend la prochaine action plus visible pour un public novice.

## Bases juridiques et produit a respecter

Sources officielles consultees le 2026-05-20:

- [Loi 65-557, article 21](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000039313574/) : le conseil syndical assiste le syndic, controle sa gestion, peut prendre connaissance et copie des pieces relatives a la gestion et a l'administration de la copropriete, et recoit communication des documents interessant le syndicat.
- [Decret 67-223, article 27](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006488533) : le conseil syndical peut prendre conseil aupres de toute personne de son choix et demander un avis technique a un professionnel de la specialite.
- [Decret 2019-502](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000038501555) et [decret 67-223, article 33-1-1](https://www.legifrance.gouv.fr/loda/id/LEGISCTA000006093863) : l'espace en ligne securise distingue les documents accessibles a tous les coproprietaires, a chaque coproprietaire pour son lot, et aux seuls membres du conseil syndical.
- [Service-Public - conseil syndical](https://www.service-public.fr/particuliers/vosdroits/F2610) : missions d'assistance, controle, mise en concurrence, rapport d'activite, delegation eventuelle, et responsabilite.
- [Service-Public - convocation AG](https://www.service-public.fr/particuliers/vosdroits/F2615) : ordre du jour, pieces utiles, consultation des justificatifs de charges avant AG.

Traduction produit:

- une commission thematique n'est pas automatiquement un membre du conseil syndical;
- elle peut assister le CS sur mandat, sujet et duree explicites;
- ses droits d'acces doivent etre differencies, tracables et proportionnes au besoin;
- toute production de commission doit etre rattachee a un sujet, une preuve, un referent CS et une decision de diffusion;
- CoproScope doit aider a preparer les AG et les contentieux, sans transformer une analyse en avis juridique automatique.

## Jalon de livraison testable 21h15

La livraison de 19h30 puis celle de 20h sont remplacees par un jalon actif a 21h15 le 2026-05-20.

Objectif du jalon:

- ouvrir une version locale testable par `ui open-test`;
- tester uniquement une instance synthetique ou locale non sensible;
- verifier les vues Cockpit, Actions, Comptes, Documents, Atelier pieces, Confidentialite, Chantiers et Depot;
- confirmer que le depot local ne promet pas une sync cloud ni un vault verifie;
- confirmer que les exports et routes ne servent pas de bruts prives;
- documenter les prochaines etapes au lieu d'arreter le developpement.

Apres 20h, le travail continue avec deux priorites:

- integrer les retours du test novice dans l'interface;
- avancer les lots structurants ci-dessous, guides par l'enquete utilisateur et la strategie Obsidian-like.

### Decision QA UI/UX 21h15

La revue `docs/qa_ui_ux_2115.md` confirme un go pour demonstration technique encadree sur instance synthetique, mais un no-go pour test utilisateur novice non accompagne tant que les points suivants ne sont pas clarifies: contexte coffre/role, token et exports, langage novice, aides accessibles, demandes multi-canaux, AG/contentieux, indicateurs.

Priorites sequencees 21h15 -> produit fini, sans remplacer les phases detaillees ci-dessous:

| Ordre | Priorite | Livrable attendu | Critere de sortie |
|---:|---|---|---|
| 1 | Securiser le parcours testable | Regle unique token/routes/exports, liens internes coherents | depot, exports et API ont un comportement explicite avec/sans token |
| 2 | Rendre le cadre novice visible | Bandeau global coffre actif, role courant, niveau d'acces, vault, sync, derniere verification | l'utilisateur sait ou il est et ce qu'il peut faire en moins d'une minute |
| 3 | Abaisser le jargon moteur | Titres UI novice, details techniques replies, aides accessibles non `title` | les noms DocOps/PrivacyOps/vault/hash ne portent plus le premier niveau |
| 4 | Finaliser l'accessibilite minimale | Labels upload, captions de tables, focus aides, etats vides actionnables | test statique accessibilite vert sur les vues principales |
| 5 | Transformer Actions en boite de travail | Fiches action avec contexte, preuve, responsable, echeance, diffusion | chaque action prioritaire a une prochaine etape et une preuve attendue |
| 6 | Creer la boite Demandes | Demandes coproprietaires et syndic multi-canaux avec journal d'actions | canal, emetteur, echeance, statut, relance et preuve sont visibles |
| 7 | Ouvrir les dossiers AG/contentieux | Preparation AG et dossier contentieux/restreint, avec preuves et exports controles | aucune analyse sensible n'est diffusable sans restriction explicite |
| 8 | Passer de gouvernance concept a parcours | `Mes coffres`, `Membres et droits`, `Survie de l'archive`, switcher anti-melange | deux coffres restent isoles en role, cache, cles, exports et sync |
| 9 | Installer les indicateurs actionnables | Cartes periode/source/preuve/seuil/confiance/prochaine action | aucun indicateur cockpit n'apparait sans preuve, periode et action |

## Argument de communication structurant

CoproScope doit pouvoir assumer publiquement cette promesse:

> Personne ne peut confisquer la memoire de la copropriete. Chaque coproprietaire peut telecharger l'archive complete, verifier qu'elle est intacte, reconstruire toute l'information collective qui lui est ouverte, et conserver la preuve que les parties restreintes existent sans pouvoir les lire sans les cles requises.

Cette promesse est aussi importante que la confidentialite. Elle protege contre:

- l'effacement malveillant;
- la retention de donnees par un membre CS, un syndic, un prestataire ou un administrateur local;
- la perte de memoire apres changement de conseil syndical;
- la disparition d'un compte cloud ou d'un appareil;
- l'opacite des zones restreintes.

Formulation produit:

- archive complete telechargeable par les coproprietaires;
- contenu sensible chiffre et compartimente;
- droits lisibles: ce que je peux ouvrir, ce qui existe mais reste restreint, qui a restreint, pourquoi et depuis quand;
- cles avec filets de sauvegarde, pas dependantes d'une seule personne;
- reconstruction testable depuis zero.

## Gestion de plusieurs coffres de copro sur un meme poste

Objectif: permettre a une personne qui possede ou gere plusieurs biens dans plusieurs coproprietes de travailler depuis la meme application locale sans melanger les donnees. Le modele mental vise est celui d'Obsidian: une application installee une fois, puis plusieurs coffres/vaults distincts.

Principes:

- l'application est installee une seule fois hors vault;
- chaque coffre de copro a son `instance_id`, son dossier local, son cache SQLite, ses exports, ses logs, son vault et ses cles;
- ouvrir un autre bien/copro revient a changer de coffre, pas a filtrer une base commune;
- aucun changement de coffre ne doit reutiliser silencieusement un token, une cle, un cache, une configuration de sync, un document selectionne ou un role;
- l'UI affiche toujours le coffre actif, l'exercice et le niveau d'acces courant;
- les recherches transversales sont opt-in et affichent clairement le coffre source de chaque resultat;
- les exports multi-copro sont interdits en V1 sauf rapport technique explicitement anonymise.

UI attendue:

- ecran `Mes coffres de copro`;
- ajout d'une copro locale par selection d'un dossier instance ou d'un vault;
- switcher de coffre avec confirmation quand un traitement est en cours;
- badges visibles: coffre actif, vault connecte/non connecte, role courant, derniere verification;
- diagnostic qui signale deux copros pointant vers le meme dossier sync, le meme cache ou les memes cles.

Piste roadmap separee: explorer les schemas de gouvernance complexe sans les melanger au simple multi-coffres. Cas a etudier: syndicat primaire et syndicats secondaires, ASL, unions de syndicats, ensembles immobiliers complexes, volumes, equipements communs a plusieurs entites, commissions transverses et droits croises. Ces schemas demanderont un modele `OrganizationGraph` ou `GovernanceScope`, mais ils ne doivent pas retarder le cas simple: un utilisateur ouvre plusieurs coffres independants.

Tests:

- deux instances locales restent isolees dans les routes, caches et exports;
- changer de copro ne conserve pas un document selectionne de l'ancienne copro;
- un export d'une copro ne contient pas le nom, les chemins ou les artefacts d'une autre;
- un vault sync ne peut pas etre declare par erreur pour deux coproprietes sans alerte.

## Lots structurants ajoutes

### 0. Pilotage par indicateurs centraux

Objectif: transformer CoproScope en cockpit de gestion, pas seulement en registre documentaire. Les indicateurs doivent etre peu nombreux, puissants, periodises, relies aux preuves, et orienter une action concrete.

Themes prioritaires:

- consommations: eau, electricite des communs, chauffage, energie, evolution par periode, cout unitaire, anomalies et factures manquantes;
- entretien/maintenance: contrats actifs, frequence de passage, delai d'intervention, non-conformites, cout par equipement, preuves de realisation;
- amortissement et investissements: age des equipements, fonds travaux, plan pluriannuel, reste a financer, CAPEX/OPEX, subventions, arbitrages AG;
- espaces verts: cout par passage ou par zone, saisonnalite, consommation d'eau, qualite constatee, incidents, preuves photo;
- travaux: budget vote, engage, facture, paye, reserves, garanties, retard, reception, preuves de cloture;
- gouvernance: decisions AG sans preuve, demandes syndic en retard, participation, delais de reponse, productions de commission, restrictions d'acces;
- demandes/problemes: volume par canal, delai de tri, delai de reponse, recurrence, actions sans prochaine echeance;
- contentieux/risques: echeances, montants exposes, pieces manquantes, niveau de restriction, prochaines actions;
- contrats/fournisseurs: echeance, reconduction, mise en concurrence, ecarts facture/contrat, dependance fournisseur;
- tresorerie/comptes: ecart budget/reel, charges par poste, impayes agreges, factures sans preuve, anomalies P1/P2.

Objets noyau a prevoir:

- `IndicatorDefinition`: nom, domaine, formule, unite, periodicite, source, niveau d'acces;
- `MetricObservation`: valeur, periode, perimetre, preuve, qualite de donnees;
- `TargetThreshold`: cible, seuil attention, seuil alerte, justification;
- `DashboardCard`: titre, tendance, cause probable, prochaine action;
- `EvidenceLink`: lien vers piece, facture, decision, log d'action ou annotation;
- `ManagementQuestion`: question de pilotage a poser au syndic, prestataire, CS ou AG.

Strategie d'integration:

- mettre les objets d'indicateurs dans le noyau, car le pilotage transversal devient universel;
- alimenter d'abord depuis les registres existants: ComptaScope, DocOps, AGOps, DecisionOps, SyndicOps, action log;
- accepter la saisie manuelle pour les observations terrain, avec preuve facultative au debut puis obligatoire pour cloture;
- garder les calculs lourds, connecteurs et analyses avancees en plugins officiels signes;
- afficher peu d'indicateurs en cockpit, puis ouvrir des fiches detaillees par theme;
- ne jamais afficher un score sans periode, source, niveau de confiance et action proposee.

Tests:

- un indicateur sans preuve ou source affiche `a verifier`;
- une valeur agregee ne revele pas de donnee restreinte a un public non autorise;
- les indicateurs restent separes par coffre de copro;
- un changement de formule ou de seuil produit un evenement signe;
- un utilisateur novice comprend la prochaine action sans lire la formule.

### 0 bis. Veille technologique open source

Objectif: maintenir une veille continue sur les briques open source utiles sans fragiliser le noyau probatoire.

Regle d'entree:

- licence compatible avec un produit local distribue;
- projet maintenu, installable sur Windows et testable hors cloud;
- fonctionnement local-first possible;
- donnees sensibles controlables;
- integration possible en plugin officiel signe si la brique est lourde ou risquee;
- desactivation/revocation possible sans casser le vault.

Pistes a surveiller:

- PDF et annotations: PDF.js pour le rendu navigateur; Xournal++/formats d'annotation comme inspiration, sans modifier les PDF sources;
- OCR: Tesseract et OCRmyPDF comme socle local mature; RapidOCR/PyMuPDF selon qualite et poids;
- recherche locale: SQLite FTS5 d'abord, puis moteurs specialises seulement si besoin;
- analytique: DuckDB pour agregats locaux et controles comptables volumineux;
- tableur/base collaborative: Grist comme piste d'exports ou d'interface Evidence, sans devenir source de verite;
- sync: Syncthing, Nextcloud, Google Drive Desktop et OneDrive comme transports de dossier, jamais moteurs metier;
- droits: Casbin ou modele RBAC/ABAC inspire, a evaluer avant adoption;
- packaging: PyInstaller, Briefcase, Tauri ou equivalent, mais seulement apres stabilisation du vault et de l'UI.

Sources de veille initiales consultees le 2026-05-20:

- [Mozilla PDF.js](https://github.com/mozilla/pdf.js/)
- [Tesseract OCR documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html)
- [OCRmyPDF documentation](https://ocrmypdf.readthedocs.io/)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)
- [DuckDB documentation](https://duckdb.org/docs/current/)
- [Grist developers](https://www.getgrist.com/developers/)
- [Syncthing documentation](https://docs.syncthing.net/)
- [Casbin overview](https://casbin.org/docs/overview)

### 0 ter. Modalites de synchronisation

Objectif: permettre plusieurs transports de sync sans changer le modele de confiance. Le vault chiffre reste la seule chose synchronisee; CoproScope reconstruit et verifie localement.

Regle V1:

- pas de connecteur cloud natif obligatoire;
- pas de code, `.git`, `.venv`, caches, logs locaux, exports temporaires ou blobs dechiffres dans la sync;
- chaque transport est traite comme un dossier local non fiable qui peut perdre, dupliquer, retarder ou modifier des fichiers;
- `vault verify` et `vault survivability` detectent les trous, alterations, blobs manquants et risques de capture;
- l'UI affiche le transport comme `Google Drive`, `OneDrive`, `Dropbox`, `Nextcloud`, `Syncthing` ou `Dossier local`, mais le noyau ne lui fait pas confiance.

Modalites a preparer:

| Transport | Mode V1 | Points a verifier | Risques | Test cible |
|---|---|---|---|---|
| Google Drive Desktop | dossier local sync | fichiers temporaires, conflits, latence, noms de dossiers | suppression cloud, doublons, fichiers conflictuels | poste A/B ajoute commentaire et action |
| OneDrive | dossier local sync | Files On-Demand, chemins longs, verrouillages | fichiers non disponibles localement | reconstruction apres telechargement force |
| Dropbox | dossier local sync | conflits `conflicted copy`, synchro selective | doublons d'evenements | verify detecte et garde historique |
| Nextcloud Desktop | dossier local sync auto-heberge | certificats, quotas, conflits serveur | admin serveur unique, versions | survivability signale dependance |
| Syncthing | peer-to-peer dossier | device IDs, versioning, ignore patterns | suppression propagee, appareil compromis | deux postes sans cloud central |
| Support froid chiffre | copie manuelle/backup | age de copie, checksum, procedure | obsolescence | archive complete verifiee hors ligne |

Design UI:

- page `Sync du coffre`;
- choix du transport par selection d'un dossier;
- diagnostic des exclusions obligatoires;
- detection probable d'une application de synchronisation active sur le dossier vault;
- etat `local seulement`, `sync configuree`, `sync a verifier`, `trous detectes`;
- bouton `verifier maintenant`;
- rapport novice: "ce qui est sauvegarde", "ce qui ne l'est pas", "qui peut reconstruire".

Diagnostic application de sync active:

- detecter les emplacements connus: Google Drive, OneDrive, Dropbox, Nextcloud, Syncthing, dossiers reseau et chemins marques par variables/provider quand disponibles;
- detecter les marqueurs de fonctionnement: placeholders, fichiers partiels, fichiers temporaires, copies conflictuelles, metadonnees `.sync`, `.stfolder`, `.dropbox`, `.tmp.drivedownload`, fichiers `~$`;
- ne pas scanner les processus ni les ports par defaut pour eviter alertes antivirus et sur-promesse technique;
- afficher une alerte lisible: `Ce coffre semble synchronise par OneDrive/Dropbox/etc. CoproScope traite ce dossier comme un transport non fiable et verifiera les conflits.`;
- proposer les actions: verifier maintenant, ouvrir le rapport de sync, voir les exclusions, creer une sauvegarde froide;
- si un dossier sync contient `.git`, `.venv`, cache dechiffre ou export temporaire, l'alerte devient prioritaire;
- si la detection est incertaine, afficher `sync possible` et demander confirmation plutot que pretendu diagnostic absolu.

Niveaux d'alerte et reaction:

- `information`: une application de sync semble active; pas de verrouillage, mais affichage du transport et invitation a verifier;
- `attention`: fichiers temporaires, placeholders, conflits ou metadonnees de sync; suspendre les actions risquant d'ecrire plusieurs versions, proposer `verifier maintenant`;
- `protection`: `.git`, `.venv`, cache dechiffre, export temporaire ou index lisible dans le dossier sync; bloquer la publication de nouveaux blobs/evenements tant que l'utilisateur n'a pas corrige ou deplace le dossier;
- `incident`: signature invalide, evenement supprime, blob manquant, chaine rompue, suppression massive ou tentative d'ecriture non conforme; passer le coffre local en lecture seule, creer un rapport signe, emettre un evenement `vault_alert_raised` si possible, et notifier les autres membres au prochain cycle de sync;
- le deverrouillage doit etre un evenement signe `vault_lock_released`, reserve aux roles autorises ou a un quorum de secours selon la politique du coffre;
- les notifications V1 sont internes au coffre: bannieres UI, journal des alertes, evenement signe synchronisable; email, SMS ou messagerie restent des plugins officiels ulterieurs;
- une alerte ne doit jamais effacer l'historique: elle ajoute un fait verifiable et guide la reconstruction.

Peer-to-peer:

- Syncthing est la piste prioritaire pour V1 peer-to-peer, car il synchronise des dossiers entre appareils sans cloud central;
- CoproScope doit fournir des ignore patterns et tests de survie, pas piloter Syncthing comme moteur metier;
- la version P2P doit garder la meme structure `blobs/events/snapshots/keys`;
- une suppression propagee par Syncthing reste detectee par hashes, snapshots, replicas et archives froides.

### 0 quater. Module de suggestions d'amelioration

Objectif: aider le conseil syndical a reperer les ameliorations possibles de gestion sans transformer CoproScope en donneur d'ordres opaque. Une suggestion doit etre une hypothese sourcée, pas une decision automatique.

Exemples de suggestions:

- demander une piece manquante au syndic;
- mettre en concurrence un contrat arrivant a echeance;
- verifier une consommation anormale;
- demander une preuve de cloture de travaux;
- preparer une question d'AG;
- proposer un biffage avant diffusion;
- ouvrir une commission thematique;
- consolider des demandes coproprietaires recurrentes;
- creer un indicateur de suivi quand un sujet revient souvent;
- archiver/verifier un coffre quand le risque de confiscation augmente.

Objets noyau a prevoir:

- `ImprovementSuggestion`: titre, domaine, raison, source, preuve, impact attendu, effort estime, niveau de confiance, public concerne;
- `SuggestionTrigger`: regle ou signal qui a declenche la suggestion;
- `SuggestionReview`: accepte, rejete, transforme en action, reporte, motif;
- `SuggestionOutcome`: action creee, demande syndic, point, indicateur, export, ou aucune suite;
- `SuggestionAudit`: version de la regle, donnees d'entree hashees, auteur ou plugin producteur.

Regles produit:

- chaque suggestion affiche `pourquoi`, `preuve/source`, `ce que cela change`, `prochaine action`;
- aucune suggestion ne modifie l'etat metier sans validation humaine;
- une suggestion rejetee reste historisee avec motif;
- les suggestions doivent etre filtrables par domaine: comptes, travaux, entretien, espaces verts, gouvernance, AG, contentieux, confidentialite, sync;
- les suggestions issues d'un plugin officiel citent version du plugin, parametres et hash des entrees;
- le langage reste novice: `A envisager`, `A verifier`, `Action proposee`, pas `AI recommendation`.

UI cible:

- panneau `Suggestions utiles` dans le cockpit;
- fiche suggestion avec preuves, risques, effort, benefice et bouton `Transformer en action`;
- vue `Suggestions rejetees/reportees` pour eviter les repetitions;
- mode `avant AG` pour transformer les suggestions en questions ou resolutions candidates.

Tests:

- une suggestion sans preuve est affichee `a verifier`;
- une suggestion ne cree pas d'action sans validation explicite;
- rejeter une suggestion cree un historique, pas une suppression silencieuse;
- les suggestions restent separees par coffre de copro;
- une suggestion sensible n'est pas visible au niveau copro si sa preuve est restreinte;
- un utilisateur novice comprend la prochaine action sans lire la regle interne.

### 1. Workflow d'ajout de document

Objectif: transformer le depot de fichier en parcours produit guide, local-first et probatoire.

UI attendue:

- entree unique `Ajouter une piece`;
- drag/drop ou selection fichier;
- etapes visibles: reception locale, empreinte, controle type/taille, classification candidate, rattachement a sujet, verification confidentialite, import vault quand actif;
- choix de destination metier: AG, compte, contrat, incident, travaux, demande, contentieux, commission, memoire;
- proposition de raccourcis locaux vers les dossiers pertinents sans dupliquer le document;
- statut clair: `recu localement`, `a classer`, `a rattacher`, `bloque confidentialite`, `importe vault`, `diffusable apres biffage`.

Evenements cibles:

- `document_added`;
- `document_version_added`;
- `classification_completed`;
- `proof_linked`;
- `diffusion_decided`;
- `shortcut_created`;
- `action_log_added`.

Tests:

- aucun nom reel de document dans le dossier sync vault;
- les titres, chemins, index, apercus PNG et OCR intermediaires sont traites comme potentiellement sensibles;
- un upload sans vault reste local et explicite;
- un document sensible n'apparait pas dans un export diffusable;
- un document peut etre rattache a plusieurs sujets via raccourcis/references, sans copie physique.

### 2. PDF viewer et annotations collaboratives

Objectif: permettre de lire, pointer et discuter une piece sans modifier le PDF source.

UI attendue:

- visualisation PDF/image/texte au centre de l'atelier;
- navigation pages, zoom, recherche locale si OCR disponible;
- annotations separees du fichier source: surlignage, commentaire, point, action, preuve, biffage candidat;
- fil lateral par page et par objet;
- affichage auteur, date, validite signature et statut de diffusion pour chaque annotation.

Modele:

- `Annotation`;
- `DocumentAnchor` avec page, zone, extrait OCR optionnel et hash du document cible;
- `Comment`;
- `Point`;
- `Action`;
- `ProofLink`.

Regle forte: le PDF original reste immuable. Une annotation est un evenement signe, pas une edition du fichier.

Tests:

- modifier le PDF invalide les ancres si le hash ne correspond plus;
- deux annotations concurrentes sont conservees;
- un commentaire supprime devient `annotation_redacted` ou `status_changed`, jamais une suppression silencieuse.

### 3. Demandes coproprietaires multi-canaux

Objectif: capter les demandes et signaux faibles sans imposer un canal unique.

Canaux a couvrir:

- mail;
- courrier;
- extranet syndic;
- formulaire local ou exportable;
- note d'appel;
- message transmis par un membre du CS;
- question d'AG;
- piece deposee dans un dossier local.

Objets noyau:

- `IncomingRequest`;
- `RequestSource`;
- `RequesterIdentity` avec niveau de confiance;
- `TriageDecision`;
- `SyndicRequest` quand la demande doit etre portee au syndic;
- `ActionLogEntry` pour chaque action concrete.

UI attendue:

- boite d'entree `Demandes`;
- qualification: coproprietaire, membre CS, commission, syndic, prestataire, inconnu;
- domaine: AG, comptes, travaux, incident, contentieux, document, confidentialite;
- decision: classer, demander piece, ouvrir point, creer action, repondre, ignorer avec motif, escalader syndic.
- separation entre demande coproprietaire, demande portee au syndic, reponse du syndic et position/analyse du CS.

Tests:

- une demande entrante ne devient pas automatiquement diffusable;
- les pieces jointes passent par le workflow d'ajout de document;
- une demande issue de plusieurs canaux peut etre fusionnee sans perdre l'historique.

### 4. Preparation AG et UX

Objectif: faire de la preparation AG un atelier complet, pas seulement un dossier de fichiers.

Pain points issus de la recherche utilisateur et du Drive historique lu en lecture seule:

- convocation volumineuse difficile a verifier;
- ordre du jour, resolutions, annexes et devis a relier;
- pieces justificatives de charges a consulter avant AG;
- couts individuels ou risques financiers parfois difficiles a comprendre;
- questions au syndic a preparer et historiser;
- suite post-AG souvent perdue.

UI cible:

- `Atelier AG`;
- ligne de temps: demande ODJ, convocation, annexes, questions, AG, PV, delais, actions post-AG;
- annexes scindees/indexees quand la convocation est volumineuse;
- check-list: resolutions, majorites, pieces obligatoires, devis, contrats, budget, votes, PV;
- mode `preparer question` vers SyndicOps;
- mode `apres AG` transformant chaque resolution en decision/action/preuve.

Tests:

- une resolution cree ou met a jour un `DecisionFollowUp`;
- une piece manquante cree une demande syndic;
- un export AG diffusable exclut les donnees individuelles non autorisees.

### 5. Contentieux et dossiers sensibles

Objectif: suivre un contentieux comme un dossier probatoire restreint.

UI cible:

- dossier contentieux avec chronologie;
- parties, objet, statut, echeances, audience ou delai, pieces;
- decisions de diffusion strictes;
- vue `a produire`, `a demander`, `a verifier`, `a ne pas diffuser`;
- distinction analyse CS, document judiciaire, reponse syndic, production avocat/prestataire.

Garde-fous:

- acces restreint par defaut;
- pas de synthese diffusable sans revue confidentialite;
- pas de conseil juridique automatique;
- event log complet des actions et exports.
- ne pas melanger pieces nominatives/contentieuses avec les livrables coproprietaires.

Tests:

- un contentieux reste invisible au niveau copro par defaut;
- une piece judiciaire est liee a un hash, une source et un statut;
- toute exportation cree `export_created` et garde la decision de diffusion.

### 6. Action log des demandes et problemes

Objectif: voir l'avancement concret, pas seulement un statut final.

Objet noyau `ActionLogEntry`:

- `log_id`;
- `object_id`;
- `object_kind`: demande, action, point, document, AG, contentieux, commission, travaux, incident;
- `created_at`;
- `author_id`;
- `channel`;
- `action_kind`: note, appel, mail, relance, piece_recue, verification, decision, export, plugin_result;
- `summary`;
- `proof_ids`;
- `next_due_at`;
- `visibility_level`.

Sources:

- saisie manuelle;
- sortie DocOps;
- resultat ComptaScope;
- resultat AGOps/DecisionOps;
- import de mail ou note d'appel plus tard.

Tests:

- le journal reste append-only;
- un changement de statut doit citer le log ou la preuve qui le justifie;
- le cockpit peut trier par `dernier log` et `prochaine echeance`.

### 7. Comptes utilisateurs, roles et commissions

Objectif: preparer une collaboration reelle avec niveaux copro et CS.

Roles V1:

- `owner_local`: administrateur local du vault;
- `cs_member`: membre conseil syndical;
- `cs_referent`: membre CS referent d'un sujet/commission;
- `commission_member`: contributeur invite sur un mandat precis;
- `coowner`: coproprietaire lecteur/contributeur limite;
- `external_advisor`: intervenant technique ou juridique invite;
- `auditor_readonly`: relecture limitee.

Niveaux:

- niveau copro: documents collectifs, demandes, informations diffusables, productions validees;
- niveau CS: controle, comptes, contentieux, liste coproprietaires, pieces sensibles, brouillons;
- niveau commission: sous-ensemble thematique, limite par mandat, duree, referent CS et type de production.

Objets:

- `Member`;
- `Device`;
- `RoleGrant`;
- `Commission`;
- `CommissionMember`;
- `CommissionMandate`;
- `CommissionProduction`;
- `AccessDecision`.

UI cible:

- page `Membres et acces`;
- page `Commissions`;
- fiche commission: theme, mandat, referent CS, membres, droits, productions, echeances, historique;
- structure proche d'un espace projet thematique: pilotage CS, questions/reponses, alertes, livrables diffusables, conformite;
- badge visible sur chaque production: `brouillon commission`, `valide CS`, `diffusable copro`, `restreint`.

Tests:

- un membre de commission ne voit pas automatiquement tout le CS;
- une production de commission cite ses sources et son referent;
- une revocation bloque les acces futurs sans effacer l'historique signe.

### 8. Raccourcis documents dans les dossiers pertinents

Objectif: retrouver une piece depuis plusieurs angles sans casser l'unicite probatoire.

Decision:

- la source de verite est le document/vault et ses references;
- les raccourcis Windows `.lnk`, fichiers `.url` ou index Markdown ne sont que des aides locales;
- dans le vault, un raccourci devient un evenement `shortcut_created` avec cible hash/object_id, pas une copie du blob.

Cas d'usage:

- meme devis visible depuis AG, travaux, comptes et commission;
- meme reponse syndic visible depuis demande, action, contentieux et memoire;
- meme facture visible depuis ComptaScope, document, preuve et AG.

Tests:

- supprimer un raccourci ne supprime jamais la preuve;
- recreer les raccourcis depuis le cache local est possible;
- aucun raccourci local n'est synchronise comme source de verite dans le vault.

### 9. Resilience anti-accaparement, cles et reconstruction coproprietaire

Objectif: proteger la copropriete contre la confiscation, la retention ou la suppression malveillante des donnees par un membre du CS, un administrateur local, un coproprietaire ou un appareil compromis.

Detail du chantier: [Resilience anti-accaparement et gouvernance des cles](./resilience_anti_accaparement.md).

Principe politique:

- aucun role humain ne doit etre un point de controle unique;
- une suppression metier devient un evenement signe de retrait, jamais une destruction silencieuse;
- un coproprietaire simple doit pouvoir reconstruire toute l'information collective qui lui est ouverte;
- si le vault est configure en mode transparence complete par decision collective, un coproprietaire simple doit pouvoir reconstruire l'integralite du vault depuis sa copie locale et le dossier sync;
- les donnees legalement ou legitimement restreintes restent chiffrees par droits, mais leur existence, leurs hashes, leurs dates et leurs decisions de restriction doivent rester auditables quand cela ne revele pas une donnee sensible.
- un coproprietaire peut telecharger l'archive complete: les parties non autorisees restent chiffrees, mais la presence, l'integrite et la non-suppression sont verifiables.

Architecture de cles:

- cle d'archive coproprietaire: ouvre le corpus collectif diffusable ou accessible aux coproprietaires;
- cle conseil syndical: ouvre les pieces de controle CS;
- cles de compartiments: contentieux, comptes individuels, commissions, prestataires, biffage, exports sensibles;
- enveloppes de cles par membre/appareil/role, jamais de cle unique en clair dans le vault;
- rotation et re-chiffrement des enveloppes lors des changements de roles;
- separation entre droit de telecharger l'archive complete et droit de dechiffrer un compartiment.

Filets de sauvegarde des cles:

- partage de secret par quorum pour les cles critiques, par exemple 3 detenteurs sur 5;
- detenteurs melanges: membres CS, au moins un coproprietaire non CS mandate comme gardien d'archive, ancien referent de passation, et optionnellement tiers de confiance local;
- chaque part de secours est inutilisable seule;
- kit de secours imprime ou fichier chiffre hors cloud courant, avec procedure de verification periodique;
- ceremonie de recuperation signee: motif, quorum, delai d'attente si possible, notification aux membres, nouvel evenement `key_recovery_performed`;
- diagnostic qui alerte si le CS est le seul a pouvoir recuperer une cle collective.

Mecanismes techniques:

- blobs immuables adresses par hash;
- evenements append-only par appareil avec chainage;
- snapshots chiffres reconstructibles;
- journal de tombstones: `object_withdrawn`, `access_revoked`, `export_revoked`, mais pas de delete destructif;
- detection de trous: sequence manquante, device head divergent, blob manquant, snapshot incoherent;
- replication multi-detenteurs: plusieurs membres et au moins un coproprietaire lecteur peuvent conserver une copie locale du vault ou d'un miroir coproprietaire;
- export de reconstruction coproprietaire: pack chiffre/verifiable avec evenements, blobs autorises, snapshots, manifestes, preuves de presence et rapport de ce qui reste restreint;
- export d'archive complete: tous les blobs/evenements/snapshots, avec payloads restreints illisibles sans la bonne cle;
- sauvegardes froides optionnelles: support local chiffre, checksum imprime/exporte, ou depot non modifiable par un seul administrateur;
- gouvernance des cles: rotation, revocation, recuperation par quorum ou cles de secours, pas de dependance a une seule personne;
- diagnostic `vault survivability`: nombre de replicas, age du dernier snapshot, evenements manquants, blobs orphelins, droits sans quorum, risque de capture.

Objets/evenements cibles:

- `replica_registered`;
- `replica_checked`;
- `reconstruction_pack_created`;
- `object_withdrawn`;
- `access_revoked`;
- `key_rotated`;
- `recovery_key_registered`;
- `key_recovery_performed`;
- `archive_downloaded`;
- `archive_integrity_verified`;
- `vault_survivability_checked`;
- `restriction_decision_recorded`.

UI attendue:

- page `Resilience du vault`;
- score lisible: `reconstructible`, `a risque`, `capture possible`, `incomplet`;
- liste des copies connues sans exposer leurs chemins prives;
- bouton de verification locale: reconstruire depuis zero dans un cache temporaire;
- vue coproprietaire: ce que je peux reconstruire, ce qui est restreint, pourquoi, par qui et depuis quand;
- bouton `Telecharger l'archive complete chiffree`;
- panneau `Cles et secours`: quorum requis, detenteurs de parts anonymises ou nommes selon politique, derniere verification du kit de secours;
- alertes: un seul detenteur, pas de snapshot recent, blobs manquants, cles sans secours, droits trop concentres.

Tests:

- supprimer un evenement a la main rend `vault verify` invalide;
- supprimer un blob signale un vault incomplet sans effacer l'historique;
- un coproprietaire lecteur reconstruit tout le corpus autorise depuis une copie neuve;
- un coproprietaire lecteur peut telecharger une archive complete et verifier l'integrite des parties qu'il ne peut pas dechiffrer;
- un membre CS ne peut pas rendre invisible une ancienne action par suppression locale;
- une revocation bloque les acces futurs mais n'efface pas ce qui a deja ete legitiment replique;
- la perte simulee du CS ne bloque pas la recuperation d'une cle collective si le quorum de secours est reuni;
- une seule part de secours ne permet jamais de dechiffrer une cle;
- le rapport de restriction ne revele pas le contenu d'une piece sensible tout en permettant de detecter qu'une decision de restriction existe.

## Phase 1 - Stabiliser l'atelier de piece

Objectif: faire de `/pieces` la surface centrale piece -> point -> action -> preuve.

### UI

- Remplacer la file tabulaire large par un layout 3 zones:
  - gauche: liste filtree des pieces/sujets;
  - centre: apercu document ou resume probatoire;
  - droite: commentaires, points, actions, preuves, historique.
- Ajouter filtres persistants:
  - `A traiter`;
  - `Sans preuve locale`;
  - `Preuve a verifier`;
  - `Diffusion bloquee`;
  - `Conflit`;
  - source DocOps / DecisionOps / IncidentOps / ComptaScope.
- Afficher un etat de signature:
  - valide;
  - non verifie;
  - invalide;
  - evenement manquant.

### Donnees

- Alimenter `piece_workshop` depuis le cache SQLite vault quand disponible.
- Garder un fallback CSV actuel pour les instances classiques.
- Introduire un identifiant stable `object_id` pour chaque piece, point, action et preuve.

### Evenements vault

- `comment_added`
- `point_created`
- `action_created`
- `proof_linked`
- `status_changed`
- `diffusion_decided`

### Tests

- Route `/pieces` en 200.
- Filtres sans chevauchement incoherent.
- Texte long fournisseur/document ne deborde pas.
- Aucun contenu brut servi depuis les racines privees.
- Creation d'une action produit un evenement signe quand le vault est actif.

## Phase 2 - Cockpit conseil syndical

Objectif: reproduire l'intention du visuel "Cockpit conseil syndical": une page de pilotage courte, priorisee, orientee decision.

### UI

- Bandeau de situation:
  - sujets P1 ouverts;
  - pieces a demander;
  - actions syndic en retard;
  - decisions AG sans preuve;
  - diffusions bloquees.
- Colonnes de travail:
  - `A traiter cette semaine`;
  - `En attente syndic`;
  - `Preuves a verifier`;
  - `Risques de diffusion`;
  - `A preparer avant AG`.
- Chaque carte contient:
  - objet concerne;
  - raison;
  - preuve disponible;
  - prochaine action;
  - lien vers atelier de piece.

### Donnees

- Creer un agrégateur `ActionInbox` derive des evenements et registres.
- Prioriser par:
  - criticite;
  - echeance;
  - absence de preuve;
  - blocage diffusion;
  - conflit;
  - relation AG/comptes/travaux.

### Evenements vault

- Le cockpit ne cree pas de type metier propre.
- Il declenche les evenements des objets sous-jacents: action, commentaire, statut, diffusion.

### Tests

- Une instance vide affiche des chantiers explicites sans erreur.
- Une instance synthetique affiche au moins une action par source quand les registres existent.
- Les compteurs du cockpit correspondent aux lignes ouvrables.

## Phase 3 - Registre decisions, actions, preuves

Objectif: faire vivre les decisions AG apres le PV.

### UI

- Vue registre avec colonnes:
  - decision;
  - action attendue;
  - responsable;
  - echeance;
  - statut;
  - preuve attendue;
  - preuve locale;
  - derniere relance;
  - validite historique/signature.
- Filtres:
  - sans preuve;
  - en retard;
  - a relancer;
  - clos avec preuve;
  - conflit.
- Fiche decision:
  - texte source;
  - pieces liees;
  - actions;
  - commentaires;
  - historique;
  - export diffusable.

### Donnees

- Faire de `DecisionFollowUp` un objet noyau.
- Rattacher:
  - AGOps;
  - SyndicOps;
  - WorksOps;
  - IncidentOps;
  - preuves DocOps.

### Evenements vault

- `decision_followup_created`
- `action_created`
- `proof_linked`
- `status_changed`
- `syndic_request_created`
- `export_created`

### Tests

- Une resolution AG cree une action suivie.
- Une preuve ajoutee cloture seulement si le statut est confirme.
- Un statut concurrent reste visible comme conflit.
- Un export ne contient que des champs diffusablement autorises.

## Phase 4 - Controle des comptes guide

Objectif: transformer ComptaScope en parcours pedagogique, pas seulement en table d'anomalies.

### UI

- Vue par priorite:
  - `P1 a traiter`;
  - `P2 a confirmer`;
  - `OK avec preuve`;
  - `hors exercice / ambigu`.
- Fiche controle facture:
  - facture candidate;
  - ligne comptable candidate;
  - motif du rapprochement;
  - preuve locale;
  - question syndic prete a copier/envoyer;
  - statut de verification humaine.
- Synthese AG:
  - points comptes a porter;
  - pieces manquantes;
  - questions ouvertes;
  - exports diffusablement propres.

### Donnees

- Convertir les sorties ComptaScope en `Point`, `Action`, `Proof`.
- Ajouter un objet `AccountingControl`.
- Garder les exports CSV/DuckDB comme derives.

### Evenements vault

- `plugin_result_recorded` pour ComptaScope.
- `point_created` pour anomalie ou verification.
- `action_created` pour question syndic.
- `proof_linked` pour facture/ligne/annexe.
- `status_changed` pour confirmation humaine.

### Tests

- Les `P1` ont une action et une question syndic.
- Les `P2` ne sont pas presentes comme erreur definitive.
- Les `OK` citent leur preuve locale.
- Aucun tableau comptable prive n'est exporte sans controle confidentialite.

## Phase 5 - Memoire de copropriete

Objectif: reproduire le visuel "Memoire de copropriete": une passation lisible pour un nouveau conseil syndical.

### UI

- Vue memoire organisee par:
  - sujets ouverts;
  - decisions non cloturees;
  - contrats et obligations;
  - travaux et garanties;
  - incidents recurrents;
  - comptes et points de vigilance;
  - documents essentiels;
  - elements diffusables / restreints.
- Timeline:
  - AG;
  - demandes syndic;
  - decisions;
  - incidents;
  - exports;
  - biffages;
  - changements membres/appareils.
- Pack passation:
  - resume actionnable;
  - index des preuves;
  - restrictions de diffusion;
  - historique des signatures.

### Donnees

- Creer une vue derivee `MemoryBrief`.
- Ne jamais stocker un pack de passation comme source de verite.
- Le pack est un export signe et historise.

### Evenements vault

- `export_created`
- `diffusion_decided`
- `member_invited`
- `member_revoked`
- `migration_recorded`

### Tests

- Pack reconstruit apres purge cache local.
- Aucun document interdit n'apparait dans une version diffusable.
- Les sujets ouverts sont relies a au moins une action ou justification.

## Phase 6 - Modules metier manquants

Ces modules alimentent les visuels, mais ne doivent pas disperser l'UX.

### SyndicOps

- Objet: `SyndicRequest`.
- Ecran principal: integre au cockpit et aux fiches actions.
- Minimum viable:
  - demande;
  - echeance;
  - relance;
  - reponse;
  - preuve;
  - statut.

### WorksOps

- Objet: `WorksProject`.
- Ecran principal: fiche projet depuis decisions/actions.
- Minimum viable:
  - devis;
  - comparaison;
  - assurance;
  - ordre de service;
  - reception;
  - reserves;
  - garanties.

### ContractOps

- Objet: `ContractRecord`.
- Ecran principal: obligations et echeances.
- Minimum viable:
  - contrat;
  - fournisseur;
  - dates;
  - obligations;
  - renouvellement;
  - mise en concurrence.

### CommsOps

- Objet: `DiffusionDraft`.
- Ecran principal: export depuis n'importe quelle fiche.
- Minimum viable:
  - synthese courte;
  - niveau de diffusion;
  - preuves citees;
  - biffage requis;
  - validation humaine.

## Phase 7 - Sync multi-postes

Objectif: prouver que le vault fonctionne comme support collaboratif.

### Scenario

1. Poste A initialise le vault.
2. Poste A importe documents et cree actions.
3. Dossier sync transporte blobs/evenements via Google Drive Desktop.
4. Poste B reconstruit son cache local.
5. Poste B ajoute commentaire/statut.
6. Poste A voit les changements.
7. Un conflit de statut est cree puis resolu.

### Tests

- Aucun nom de document dans le dossier sync.
- Aucun `.git`, `.venv`, cache ou export temporaire dans le dossier sync.
- Tamper event invalide `verify`.
- Tamper snapshot invalide `verify`.
- Suppression cache local puis reconstruction complete.

## Phase 8 - Produit installe

Objectif: sortir du mode repo/developpeur.

### Installation

- App desktop avec runtime Python embarque.
- Dossier d'installation hors vault.
- Dossier local par utilisateur.
- Dossier sync configurable.

### Mise a jour

- Noyau signe.
- Plugins officiels signes.
- Pas d'auto-update de plugin sans validation.
- Reprise de vault apres upgrade testee.

### Diagnostics

- `coprocs vault doctor`.
- Detection `.git`, `.venv`, caches, exports temporaires dans sync.
- Detection dependances lourdes installees localement.
- Rapport lisible pour non-developpeur.

## Definition du produit fini V1

CoproScope V1 est atteint quand:

- un membre de CS ouvre le cockpit et comprend les 10 sujets prioritaires;
- une piece peut etre reliee a un point, une action et une preuve;
- un document peut etre ajoute, visualise, annote et rattache sans modifier l'original;
- une decision AG devient une action suivie jusqu'a preuve de cloture;
- une demande coproprietaire ou syndic dispose d'un canal, d'une echeance, d'un journal d'actions et d'un statut;
- un controle comptable `P1/P2/OK` produit une question ou une preuve claire;
- un dossier AG ou contentieux rassemble pieces, questions, echeances et restrictions d'acces;
- les roles copro, CS et commissions thematiques sont visibles et differencies;
- un coproprietaire simple peut reconstruire toute l'information collective autorisee, detecter les trous et conserver une preuve de presence des elements restreints sans acceder a leur contenu;
- plusieurs coffres de copro peuvent etre ouverts sur le meme poste sans partage implicite de cache, cles, roles, exports ou dossier sync;
- les schemas de gouvernance complexe sont identifies comme piste de recherche separee: syndicat primaire/secondaire, ASL, union, droits croises;
- les indicateurs centraux de gestion sont relies a leurs preuves, periodes, seuils et prochaines actions;
- l'interface reste comprehensible par les publics novices de l'enquete, avec registre de langage, infobulles, accessibilite et parcours guides;
- la memoire de copropriete peut etre exportee en pack de passation;
- deux postes peuvent collaborer par dossier sync chiffre;
- `vault verify` detecte toute alteration significative;
- les modules actuels continuent de fonctionner en mode instance classique;
- les exports diffusablement propres passent par PrivacyOps/BiffageOps;
- le code, `.git`, `.venv`, caches et worktrees ne sont jamais synchronises dans le vault.

## Sequencement recommande des prochains sprints

| Sprint | Objectif | Livrable principal | Tests de sortie |
|---|---|---|---|
| S0 | Livraison testable 20h | UI visible via `ui open-test`, protocole novice | routes principales + tests UI |
| S1 | Depot document guide | Ajout piece, hash, classification, rattachement | tests depot + anti-fuite |
| S2 | Coffres de copro locaux | Ecran Mes coffres, isolation instances/caches/vaults/cles | tests isolation multi-instance |
| S3 | Resilience anti-accaparement | Archive complete telechargeable, gouvernance des cles, reconstruction coproprietaire | tests verify/tamper/rebuild/key recovery |
| S4 | Indicateurs de pilotage | Definitions, observations, seuils, preuves et cartes cockpit | tests indicateurs + anti-fuite |
| S5 | PDF et annotations | Viewer PDF/image + annotations signees separees | tests anchors + annotations |
| S6 | SyndicOps et demandes multi-canaux | `IncomingRequest`, `SyndicRequest`, action log | tests demandes + exports |
| S7 | Cockpit CS V1 accessible | Inbox priorisee, langage novice, infobulles, prochaine action | tests model + route + accessibilite |
| S8 | AG workshop | Preparation AG, resolutions, pieces, questions syndic | tests AGOps/DecisionOps |
| S9 | Contentieux V1 | Dossiers restreints, chronologie, pieces, exports controles | tests droits + privacy |
| S10 | Comptes utilisateurs et commissions | Roles copro/CS, commissions, referents, productions | tests acces + UI |
| S11 | Gouvernance complexe recherche | Syndicat primaire/secondaire, ASL, unions, droits croises | note recherche + modele exploratoire |
| S12 | Vault local verifiable | Verify/snapshot/reconstruction SQLite | `test_vault*` + reconstruction |
| S13 | Sync deux copies locales | Scenario poste A/B via dossier sync | tests integration manuels + scripts |
| S14 | Plugins officiels + veille OSS | Manifeste, activation signee, radar open source | tests plugin manifest + revue licences |
| S15 | Packaging desktop | App locale hors vault | smoke tests install |
| S16 | Produit fini teste | Parcours bout-en-bout issus recherche utilisateur | tests UX, QA, anti-fuite, reprise |

## Agents paralleles utiles ensuite

Regle de profondeur:

- **Mode tres approfondi** par defaut pour les lots qui engagent le produit fini, la comprehension novice, la securite ou une dependance durable.
- **Mode moyen** pour un module borne avec ownership strict, tests clairs et faible risque d'architecture.
- **Mode rapide** seulement pour lecture, audit ponctuel, correction de libelle ou documentation mecanique.
- Tout agent en mode tres approfondi doit rendre: hypotheses, risques, arbitrages, tests, dette restante et prochaines decisions.

Matrice des modes:

| Lot | Mode conseille | Pourquoi |
|---|---|---|
| UX novice, accessibilite, registre de langage | Tres approfondi | Conditionne l'adoption par les publics de l'enquete et evite le jargon moteur. |
| Cockpit conseil syndical et prochaine action | Tres approfondi | C'est la promesse principale du produit: urgences, preuves, action, diffusion. |
| Vault, signatures, cles, anti-accaparement | Tres approfondi | Risque de perte, confiscation ou fausse promesse de securite. |
| Sync Drive/OneDrive/Dropbox/Nextcloud/Syncthing | Tres approfondi | Les transports sont non fiables et les conflits doivent etre anticipes. |
| Coffres multiples façon Obsidian | Tres approfondi | Le changement de coffre ne doit jamais faire fuiter role, token, document ou cache. |
| Gouvernance complexe: syndicat primaire/secondaire, ASL, unions | Tres approfondi | Modele juridique et droits croises a fort risque de confusion. |
| Indicateurs de pilotage | Tres approfondi | Un mauvais indicateur peut tromper; chaque carte doit citer preuve, periode et action. |
| Veille open source et choix de dependances | Tres approfondi | Licence, maintenance, packaging et securite engagent le produit. |
| PDF/annotations collaboratives | Tres approfondi | Ancres, immutabilite du RAW, accessibilite et diffusion sont critiques. |
| Modules metier bornes: SyndicOps, AccessOps, TimelineOps | Moyen a tres approfondi selon impact | Moyen si pur et teste; tres approfondi si branche UI/vault/droits. |
| Nettoyage docs, liens, tables de matieres | Rapide a moyen | Peu risqué si aucun comportement produit ne change. |
| Tests de regression cibles | Moyen | Chercher des trous concrets sans redessiner l'architecture. |

- Agent Vault Core: verify, snapshots, chainage, reconstruction.
- Agent UI Cockpit: inbox et priorisation.
- Agent UI Atelier: fiche piece et interactions signees.
- Agent Depot/PDF: ajout document, viewer et annotations.
- Agent Demandes/SyndicOps: canaux, relances, action log.
- Agent AG/Contentieux: preparation AG et dossiers sensibles.
- Agent Identite/Commissions: roles, acces, productions.
- Agent Resilience Vault: anti-suppression, replicas, reconstruction coproprietaire, quorum de cles.
- Agent Pilotage/Indicateurs: definitions, seuils, observations, preuves et cockpit de gestion.
- Agent Veille OSS: licences, maintenance, securite, integration plugin des briques open source.
- Agent Accessibilite/Langage: registre de vocabulaire, infobulles, parcours novice, contrastes et navigation clavier.
- Agent Gouvernance complexe: syndicat primaire/secondaire, ASL, unions, droits et perimetres croises.
- Agent Compta UX: controle comptes guide.
- Agent Passation: memoire copro et exports.
- Agent Privacy/Comms: diffusion, biffage, syntheses.
- Agent QA: scenarios bout-en-bout, anti-fuites, tests visuels.

## Quand cette roadmap approche de la fin

Relancer une recherche produit avant de considerer CoproScope "fini":

- refaire des tests novices sur les quatre visuels de l'enquete;
- observer si l'utilisateur trouve seul la prochaine action en moins de 10 minutes;
- tester un cycle complet: ajout document -> annotation -> point -> demande -> relance -> preuve -> export;
- tester un cycle AG: convocation -> questions -> AG -> PV -> actions -> preuves;
- tester un cycle contentieux restreint avec droits differencies;
- tester deux profils: coproprietaire lecteur/contributeur limite et membre CS;
- revisiter la strategie Obsidian-like: ce qui est devenu universel doit passer noyau, ce qui est lourd ou specialise doit rester plugin signe.
- refaire une revue de veille open source avant d'integrer une brique lourde ou un connecteur.
