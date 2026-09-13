# Recherche UX/UI WorksOps apres cadrage metier

Date de lancement: 2026-05-24 09:26 +02:00.
Date de cloture: 2026-05-24 09:34 +02:00.
Roadmap: `RM-2026-0032`.
Chantier: `CH-20260524-092657-RM-2026-0032-travaux-operation-ux-ui`.
Conversation coordination: `CONV-2026-1390`.
Mode: equipe UX/UI recherche visuelle sans dev.
Statut: cloture sans dev.

## BOT-START

BOT-START - Orchestrateur UX/UI WorksOps - 2026-05-24 09:26 +02:00

Roadmap: `RM-2026-0032`
Chantier: `CH-20260524-092657-RM-2026-0032-travaux-operation-ux-ui`
Conversation: `CONV-2026-1390`
Role: Orchestrateur UX/UI
Mission: relancer une equipe UX/UI sans dev pour transformer le cadrage `OperationTravaux` en parcours, ecrans, microcopy et gates novice/metier.
Ownership modifiable: `docs/recherche_ux_ui_2026-05-24_travaux_operation-model.md`, `docs/assets/ux-ui-recherche-2026-05-24-travaux-operation-model/`, lignes de presence et gouvernail liees a `RM-2026-0032`.
Fichiers a eviter: code applicatif, routes, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, serveurs locaux, `RM-2026-0017` bloque.
Passerelle/registre de trace: cette mission, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/protocole_equipe_ux_ui_recherche.md`, `docs/consignes_bots_interconversations.md`, `docs/protocole_roadmap_presence_agents.md`, gouvernail, presence, `docs/recherche_ux_ui_2026-05-24_travaux.md`, `docs/cadrage_metier_worksops_2026-05-24.md`.
Tests/preuves attendus: sorties des roles UX/UI, image ou blueprint utile si retenu, point court, aucune verification applicative car aucun code.
Risque de collision: plusieurs equipes UX/UI vivantes utilisent `CONV-2026-1361` a `CONV-2026-1379`; WorksOps reprend sur `CONV-2026-1390` a `CONV-2026-1395`.
Lease ownership: 2026-05-25 09:26 +02:00.
Prochaine action: lancer les cinq roles en lecture seule et consolider leurs arbitrages.

## Objectif

Repartir du cadrage metier `OperationTravaux` pour verifier si la direction
`Travaux - portefeuille + fiche probatoire` tient encore quand les statuts,
preuves et frontieres modules sont explicites.

La recherche devait trancher:

- comment afficher `OperationTravaux` sans jargon;
- quelles informations tiennent au premier niveau;
- comment faire comprendre `preuve candidate`, `preuve validee` et `preuve manquante`;
- comment montrer budget et diffusion sans dupliquer ComptaScope ni PrivacyOps;
- quel blueprint ou image doit guider un futur chantier dev separe.

## Sources de cadrage

- `docs/recherche_ux_ui_2026-05-24_travaux.md`
- `docs/cadrage_metier_worksops_2026-05-24.md`
- `docs/assets/ux-ui-recherche-2026-05-24-travaux/01-console-travaux-portefeuille-fiche.svg`
- `docs/agent_briefs/lot-f-worksops.md`
- `docs/fonctions_cibles.md`

## Roles

| Role | Conversation | Statut | Sortie integree |
|---|---|---|---|
| Orchestrateur UX/UI | `CONV-2026-1390` | `CLOTURE` | Cadrage, synthese, arbitrages, image retenue et cloture. |
| Chercheur utilisateur | `CONV-2026-1391` / Huygens `019e58e5-1e88-7913-9331-58ca4a0906ad` | `CLOTURE` | Scenarios post-cadrage, irritants, criteres de reussite et risques d'incomprehension. |
| Architecte UX | `CONV-2026-1392` / Mill `019e58e5-1f8b-7313-91a5-49dca0bc7261` | `CLOTURE` | Wireflow, hierarchie, etats d'ecran, variantes desktop/mobile. |
| Designer UI / generateur visuel | `CONV-2026-1393` / Lorentz `019e58e5-20ce-7031-b910-ad44e0b74b48` | `CLOTURE` | Direction visuelle, blueprint de reference et annotations. |
| Testeur metier expert | `CONV-2026-1394` / Godel `019e58e5-25bf-7973-8431-2328deabf7ff` | `CLOTURE` | Challenge statuts, preuves, budget, reception, reserves, garanties et diffusion. |
| Testeur accessibilite / novice | `CONV-2026-1395` / Aristotle `019e58e5-2af6-7230-9c59-1977f8c42477` | `CLOTURE` | Comprehension sous 30 secondes, jargon, ordre visuel, CTA non trompeurs. |

## Decision UX/UI

Decision retenue: conserver la direction `Travaux - portefeuille + fiche
probatoire`, mais la rendre plus probatoire et moins technique.

Le premier ecran reste un portefeuille d'operations, trie par preuve bloquante.
Il doit afficher seulement quatre informations fortes:

- `Travaux`;
- `Ou en est-on ?`;
- `Ce qui manque`;
- `A faire maintenant`.

Le terme `OperationTravaux` reste un nom de modele interne. Le titre utilisateur
recommande est `Suivi des travaux`, avec le sous-titre `Voir l'etat, la preuve
manquante et la prochaine demande`.

La fiche probatoire ne doit pas commencer par la frise complete. Elle commence
par:

1. `Ce qui bloque`;
2. l'action prudente a preparer;
3. la chaine de preuves `Vote -> Devis -> Commande -> Travaux -> Reception -> Reserves -> Garantie`;
4. les documents classes en `Confirmees`, `A verifier`, `Manquantes`;
5. budget resume et diffusion en second niveau.

## Synthese Utilisateur

Profils prioritaires:

- referent travaux CS qui veut savoir quoi relancer cette semaine;
- syndic benevole qui doit prouver decision, devis, commande ou reception;
- coproprietaire novice qui veut comprendre pourquoi il paie et ce qui manque;
- conseil en passation qui cherche reserves, garanties et preuves.

Scenarios critiques:

- facture trouvee mais reception absente: ne jamais conclure `chantier clos`;
- reception avec reserves: garder l'operation active jusqu'a preuve de levee;
- synthese partageable: afficher ce qui est diffusable, a biffer, bloque ou a
  arbitrer.

Criteres de reussite:

- en moins de 30 secondes, un novice sait quel chantier prioriser, quelle preuve
  manque, qui relancer et ce que le bouton va faire;
- une operation ne peut pas apparaitre close sur facture seule;
- les preuves sont separees visuellement: manquante, a verifier, confirmee;
- le budget reste un resume de pilotage, pas un module comptable;
- la diffusion est visible sans bloquer toute lecture.

## Architecture UX

Wireflow retenu:

`Cockpit` -> carte `Travaux a suivre` -> page `Travaux` -> filtre
`Preuves bloquantes d'abord` -> selection d'une operation -> fiche probatoire
-> action prudente -> retour portefeuille.

Actions de fiche:

- `Preparer une demande au syndic`;
- `Rattacher une piece`;
- `Verifier la piece a verifier`;
- `Noter une reserve`;
- `Voir l'historique`.

L'export reste secondaire: fiche -> `Apercu synthese travaux` -> gate
`A verifier avant partage` -> export seulement si la diffusion est validee.

Desktop:

- tableau dense limite a quatre colonnes metier;
- fiche laterale persistante;
- action primaire dans la fiche, pas dans toutes les lignes;
- filtres horizontaux discrets.

Mobile:

- cartes empilees;
- chaque carte montre titre, statut, preuve manquante et prochaine action;
- fiche en ecran detail;
- frise compressee en liste verticale;
- pas de tableau horizontal.

Etats recommandes:

- `A qualifier`;
- `Vote a retrouver`;
- `Commande a confirmer`;
- `Reception a prouver`;
- `Reserves a suivre`;
- `Garantie a surveiller`;
- `Clos avec preuves`;
- `A verifier avant partage`.

## Direction UI

Le blueprint de reference reste:

- `docs/assets/ux-ui-recherche-2026-05-24-travaux/01-console-travaux-portefeuille-fiche.svg`

Pas de nouvelle image produite: le designer recommande d'annoter le blueprint
existant plutot que de generer une variante, car la structure de base reste
bonne.

Annotations retenues:

- remplacer `Operations travaux` par `Travaux suivis`;
- remplacer `Ajouter` par `Creer une operation a qualifier`, ou retirer ce
  bouton du premier lot si la creation n'est pas cadree;
- ajouter un resume budget compact sous le titre: `Vote`, `Commande`, `Facture`,
  `Paye`, `Reste a verifier`;
- ajouter un badge de diffusion discret: `A verifier avant partage`,
  `Apercu possible`, `Bloque`;
- regrouper les preuves en trois etats: `Confirmee`, `A verifier`,
  `Manquante`;
- remplacer `Preparer relance` par `Preparer une demande`.

Couleurs et priorites:

- preuve manquante: priorite visuelle maximale, rouge pale avec libelle texte;
- piece a verifier: ambre;
- preuve confirmee: vert;
- budget: compact, non comptable;
- diffusion: badge secondaire, jamais CTA principal.

## Test Metier

Verdict metier: GO pour continuer le cadrage UX/UI, NO-GO pour dev direct tant
que les cas limites ne sont pas explicitement couverts.

Garde-fous metier:

- urgence hors AG: afficher `urgence a qualifier`, pas `vote manquant` par defaut;
- devis ou facture sans decision AG: operation `a qualifier`, demande syndic
  preparee;
- plusieurs devis requis mais seuil inconnu: `mise en concurrence a verifier`;
- devis retenu sans commande signee: ne pas passer en `travaux commandes`;
- facture de solde sans reception: garder `reception a prouver`;
- reception sans preuve ou avec preuve contradictoire: validation humaine
  obligatoire;
- reserves levees par simple mail fournisseur: piece a verifier seulement;
- garantie decennale presente mais activite ou date non coherente: alerte
  metier, jamais badge `assurance OK`;
- budget paye superieur au vote ou a la commande: signal d'ecart, pas
  accusation;
- export coproprietaires avec contentieux, coordonnees, RIB, negociation ou
  donnees personnelles: `a verifier avant partage`.

Budget a separer:

- vote;
- commande;
- facture;
- paye;
- reste a financer;
- fonds travaux;
- subvention ou emprunt;
- cle de repartition.

La page WorksOps ne remplace pas ComptaScope.

## Test Novice

Verdict novice: GO conditionnel si l'ecran reste centre sur `ce qui manque` et
`quoi faire maintenant`.

Libelles recommandes:

| Libelle interne | Libelle novice |
|---|---|
| `OperationTravaux` | `Suivi des travaux` ou `Travaux suivis` |
| `preuve candidate` | `piece a verifier` |
| `preuve validee` | `preuve confirmee` |
| `diffusion a arbitrer` | `a verifier avant partage` |
| `reception` | `fin de travaux acceptee ou avec reserves` |
| `reserves` | `problemes a corriger apres reception` |
| `montant engage` | `montant commande` |
| `garantie a surveiller` | `garantie a surveiller jusqu'au ...` |

CTA a eviter:

- `Envoyer automatiquement`;
- `Valider la facture`;
- `Cloturer le chantier`;
- `Assurance OK`;
- `Diffuser aux coproprietaires`;
- `Travaux OK`;
- `Reception faite` sans preuve visible.

Alternatives:

- `Preparer une demande`;
- `Verifier la piece`;
- `Rattacher une piece`;
- `Noter une reserve`;
- `Voir l'apercu avant partage`.

## GO / NO-GO

GO recherche:

- le premier ecran peut rester `portefeuille + fiche probatoire`;
- le blueprint existant reste la reference;
- le vocabulaire novice est assez clair si les libelles ci-dessus sont appliques;
- les statuts probatoires sont explicites.

NO-GO dev direct:

- si le terme `OperationTravaux` apparait dans l'interface;
- si l'ecran commence par une frise longue avant la preuve bloquante;
- si un badge `OK` laisse croire qu'une facture, une assurance ou une reception
  suffit;
- si un export est possible sans revue de diffusion;
- si le budget devient un tableau comptable complet;
- si une operation peut etre close sur facture seule.

## Questions Ouvertes

- Faut-il autoriser la creation d'une operation depuis ce premier lot, ou
  seulement afficher les operations detectees et a qualifier ?
- Ou fixer les seuils de mise en concurrence quand l'instance ne les donne pas ?
- Quel corpus synthetique minimal utiliser pour tester vote, devis, commande,
  reception, reserve, garantie et diffusion ?
- Quelle regle PrivacyOps doit bloquer ou biffer les pieces travaux avant
  partage coproprietaires ?

## Point Court Final

A produire: rien de plus dans cette relance UX/UI; la decision est stabilisee.

En test: pas de test applicatif; controle documentaire et `git diff --check`
cible OK.

Images candidates: blueprint source conserve et annote dans cette trace;
aucune nouvelle image requise.

Decisions ouvertes: creation d'operation, seuils, corpus synthetique et regle
PrivacyOps d'export.

Prochain mouvement: arbitrer un chantier dev separe, borne a `Suivi des
travaux`, ou garder `RM-2026-0032` en pret a integrer.

## Journal

| Heure | Conversation | Evenement | Note |
|---|---|---|---|
| 2026-05-24 09:26 +02:00 | `CONV-2026-1390` | `BOT-START` | Relance UX/UI WorksOps post-cadrage metier ouverte sans dev. |
| 2026-05-24 09:27 +02:00 | `relance-ux-ui-travaux-operation-model` | `AUTOMATION_CREATE` | Heartbeat actif toutes les 10 minutes jusqu'au marqueur `UXUI-DONE - equipe UX/UI a fini son job`. |
| 2026-05-24 09:27 +02:00 | `CONV-2026-1391`..`CONV-2026-1395` | `AGENTS_LAUNCHED` | Agents Huygens, Mill, Lorentz, Godel et Aristotle lances en lecture seule; aucun code, serveur ou instance privee. |
| 2026-05-24 09:34 +02:00 | `CONV-2026-1391`..`CONV-2026-1395` | `AGENTS_DONE` | Les cinq roles ont rendu leurs sorties; convergence sur portefeuille + fiche probatoire, preuve bloquante d'abord, vocabulary novice. |
| 2026-05-24 09:34 +02:00 | `CONV-2026-1390` | `BOT-END` | Recherche cloturee sans dev, serveur ni instance privee; blueprint existant retenu avec annotations. |

## BOT-END

BOT-END - Orchestrateur UX/UI WorksOps - 2026-05-24 09:34 +02:00

Roadmap: `RM-2026-0032`
Chantier: `CH-20260524-092657-RM-2026-0032-travaux-operation-ux-ui`
Conversations: `CONV-2026-1390`..`CONV-2026-1395`
Resultat: recherche UX/UI post-cadrage WorksOps cloturee sans dev.
Livrables: cette trace, annotations de blueprint, reference `docs/assets/ux-ui-recherche-2026-05-24-travaux/01-console-travaux-portefeuille-fiche.svg`.
Tests/preuves: `git diff --check` cible OK; aucun test applicatif car aucun code, serveur, template, CSS ou instance privee n'a ete modifie.
Limites: pas de validation juridique, pas de recette UI reelle, pas de corpus travaux synthetique execute.
Prochain mouvement: ouvrir un chantier dev separe seulement apres arbitrage sur creation d'operation, seuils, corpus synthetique et regle PrivacyOps d'export.

UXUI-DONE - equipe UX/UI a fini son job
