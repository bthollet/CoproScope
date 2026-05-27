# Cadrage metier WorksOps travaux

Date: 2026-05-24 09:18 +02:00.
Roadmap: `RM-2026-0032`.
Chantier: `CH-20260524-091853-RM-2026-0032-cadrage-metier-worksops`.
Conversation coordination: `CONV-2026-1367`.
Mode: cadrage metier documentaire, sans dev.

## BOT-START

BOT-START - Coordinateur metier WorksOps - 2026-05-24 09:18 +02:00

Roadmap: `RM-2026-0032`
Chantier: `CH-20260524-091853-RM-2026-0032-cadrage-metier-worksops`
Conversation: `CONV-2026-1367`
Role: Coordinateur metier WorksOps
Mission: verrouiller le modele metier minimal WorksOps avant toute suite dev UI.
Ownership modifiable: `docs/cadrage_metier_worksops_2026-05-24.md`, lignes de presence et gouvernail liees a `RM-2026-0032`.
Fichiers a eviter: code applicatif, routes, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, `RM-2026-0017` bloque.
Passerelle/registre de trace: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/consignes_bots_interconversations.md`, `docs/protocole_roadmap_presence_agents.md`, gouvernail, presence, `docs/recherche_ux_ui_2026-05-24_travaux.md`, `docs/agent_briefs/lot-f-worksops.md`, `docs/fonctions_cibles.md`.
Tests/preuves attendus: cadrage metier source, garde-fous officiels, `git diff --check`; aucun test applicatif car aucun code.
Risque de collision: `CONV-2026-1355` a `CONV-2026-1366` sont deja pris par des relances UX/UI recentes ou actives; WorksOps reprend avec `CONV-2026-1367`.
Lease ownership: 2026-05-24 11:18 +02:00.
Prochaine action: figer objets, statuts, preuves, budgets, gates de diffusion et frontieres avec DecisionOps/ComptaScope/PrivacyOps.

## Synthese

WorksOps n'est pas une vue comptable et n'est pas seulement un tableau de
chantiers. C'est une chaine probatoire pour une operation travaux: decision,
devis, commande, chantier, facture, reception, reserves, garanties,
financement et diffusion.

Le modele minimal doit permettre au conseil syndical de repondre a quatre
questions sans fouiller dans le coffre:

- quel est le chantier suivi;
- ou en est-il;
- quelle preuve bloque la suite;
- quelle action prudente faut-il preparer.

## Sources et garde-fous

Sources officielles verifiees le 2026-05-24:

- Service-Public, assemblee generale des coproprietaires: https://www.service-public.gouv.fr/particuliers/vosdroits/N31341
- Service-Public, regles de vote en AG, verifie le 2026-05-06: https://www.service-public.gouv.fr/particuliers/vosdroits/F2137
- Service-Public, convocation AG, devis joints et documents obligatoires: https://www.service-public.gouv.fr/particuliers/vosdroits/F2615
- Legifrance, article 21 de la loi du 10 juillet 1965, consultation CS, mise en concurrence et acces aux pieces: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000039313574
- Service-Public Entreprendre, garantie decennale, verifie le 2026-04-10: https://entreprendre.service-public.gouv.fr/vosdroits/F2034
- Legifrance, Code civil article 1792-6, reception, reserves et garantie de parfait achevement: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006443552
- Service-Public, fonds de travaux, verifie le 2025-01-01: https://www.service-public.gouv.fr/particuliers/vosdroits/F34026

Ces sources cadrent le produit. Elles ne remplacent pas une validation juridique
au cas par cas.

## Objet metier minimal

Objet principal: `OperationTravaux`.

| Champ | Sens | Regle produit |
|---|---|---|
| `operation_id` | Identifiant stable local | Ne depend pas du chemin fichier. |
| `titre` | Nom comprehensible du chantier | Titre utilisateur: `Travaux`, pas `WorksOps`. |
| `perimetre` | Zone, equipement ou parties communes concernes | Peut rester `A qualifier` si les pieces divergent. |
| `statut` | Etat metier courant | Vient de la chaine de preuves, pas d'une facture seule. |
| `preuve_bloquante` | Piece ou evenement qui manque | Affichee au premier niveau. |
| `prochaine_action` | Demande ou verification a preparer | Pas d'envoi automatique sans validation humaine. |
| `responsable_suivi` | CS, syndic, commission, fournisseur ou non defini | Libelle prudent, pas une accusation. |
| `echeance` | Date utile: AG, devis, chantier, reception, reserve, garantie | Date optionnelle, sourcee si affichee. |
| `decision_ref` | Resolution, PV, notification ou decision urgente | Decision AG et commande restent separees. |
| `devis_refs` | Devis recus, compares, retenus ou rejetes | Plusieurs devis possibles selon seuils. |
| `commande_ref` | Bon de commande, ordre de service, marche ou avenant | `Devis retenu` ne vaut pas commande. |
| `fournisseur_refs` | Entreprise, maitre d'oeuvre, bureau d'etude, assureur | Plusieurs intervenants possibles. |
| `assurance_refs` | Attestations et garanties | Interdire le badge unique `assurance OK`. |
| `facture_refs` | Acompte, situation, solde, regularisation | Une facture ne prouve pas reception. |
| `reception_ref` | PV, date, signataires, avec/sans reserves | Obligatoire avant cloture probatoire. |
| `reserve_refs` | Reserves, delais, levees prouvees | Une reserve ouverte maintient l'operation active. |
| `garantie_refs` | GPA, biennale, decennale si applicable | Surveiller apres reception. |
| `budget` | Vote, engage, facture, paye, reste a financer | Lecture ComptaScope ou saisie prudente sourcee. |
| `diffusion_status` | Diffusable, a arbitrer, bloque | Depend de PrivacyOps et du contexte. |
| `source_quality` | Validee, candidate, contradictoire, manquante | Visible dans la fiche probatoire. |

## Statuts WorksOps

1. `A_QUALIFIER`: des pieces existent, mais l'operation n'est pas fiable.
2. `VOTE_A_RETROUVER`: devis ou facture trouves, decision absente ou non rattachee.
3. `DEVIS_A_COMPARER`: plusieurs devis ou seuil de mise en concurrence a verifier.
4. `DEVIS_RETENU`: fournisseur choisi, mais commande encore a prouver.
5. `COMMANDE_A_CONFIRMER`: ordre de service, bon de commande, assurance ou avenant manque.
6. `TRAVAUX_EN_COURS`: chantier suivi, ecarts et situations possibles.
7. `RECEPTION_A_PROUVER`: travaux annonces termines, PV ou preuve de reception absente.
8. `RESERVES_A_SUIVRE`: reception avec reserves, levee non prouvee.
9. `GARANTIE_A_SURVEILLER`: reception faite, garanties encore utiles.
10. `CLOS_AVEC_PREUVES`: decision, commande, facture, reception, reserves et garantie sont traces.

Etat orthogonal:

- `DIFFUSION_A_ARBITRER`: la synthese existe mais la communication aux coproprietaires doit etre qualifiee.

Interdictions de statut:

- pas de `CLOS_AVEC_PREUVES` sans reception;
- pas de `TRAVAUX_OK`;
- pas de `ASSURANCE_OK`;
- pas de `FACTURE_VALIDEE` comme preuve de chantier termine;
- pas de diffusion automatique depuis une preuve candidate.

## Checklist probatoire

### Decision

- convocation ou ordre du jour;
- projet de resolution si requis;
- devis joints ou justification;
- PV et resultat du vote;
- majorite applicable;
- notification et delai de contestation si disponible;
- montant autorise;
- financement et cle de repartition;
- mandat donne au syndic ou au conseil syndical;
- seuil de consultation du CS et seuil de mise en concurrence si connus.

### Devis et commande

- devis recus, compares, retenus ou rejetes;
- perimetre et lots techniques;
- montant HT/TTC si disponible;
- fournisseur et interlocuteurs;
- validite du devis;
- activites couvertes par assurance;
- attestation decennale ou autre garantie quand applicable;
- avis CS ou trace de comparaison si requis;
- devis signe, bon de commande, ordre de service, marche ou avenant;
- date de demarrage prevue et planning.

### Execution

- compte rendu, photos ou constats;
- incidents et ecarts;
- situations de travaux;
- factures d'acompte ou intermediaires;
- demandes au syndic ou fournisseur;
- liens avec incidents, sinistres ou contrats si necessaire.

### Reception et reserves

- PV de reception;
- date;
- signataires ou trace contradictoire;
- avec ou sans reserves;
- liste des reserves;
- delai de reprise;
- preuve de levee;
- constat de levee ou notification.

### Garanties

- garantie de parfait achevement un an apres reception si applicable;
- garantie biennale si applicable;
- garantie decennale si applicable;
- assureur et attestation;
- periode couverte;
- evenements ou desordres a surveiller.

### Budget et financement

- montant vote;
- montant engage;
- montant facture;
- montant paye;
- reste a financer;
- appels de fonds;
- fonds travaux mobilise ou non;
- subvention, emprunt ou avance si applicable;
- cle de charges ou parties communes speciales.

### Diffusion

- statut PrivacyOps;
- documents communicables aux coproprietaires;
- pieces a biffer ou metadata-only;
- blocages: negociation commerciale, contentieux, donnees personnelles, coordonnees bancaires, secret ou restriction justifiee;
- apercu exportable avant diffusion.

## Frontieres entre modules

| Module | Role dans WorksOps | Ne doit pas faire |
|---|---|---|
| DocOps | Propose les pieces candidates, hash, texte, classement. | Valider seul la chaine travaux. |
| DecisionOps | Lie resolution, action, responsable, preuve attendue. | Remplacer le suivi reception/reserves/garantie. |
| ComptaScope | Fournit factures, paiements, ecarts budgetaires, reste a financer. | Declarer un chantier termine. |
| PrivacyOps | Dit ce qui peut etre diffuse, biffe ou bloque. | Cacher les travaux par prudence generique sans signal. |
| Audit360 | Transforme les anomalies en points a verifier. | Melanger tous les risques dans le premier ecran travaux. |
| IncidentOps | Suit sinistres, incidents, photos, clotures. | Absorber les operations travaux structurees. |

## Contrat UI futur

Premier ecran: page `Travaux`.

Informations obligatoires:

- `Travaux`;
- `Etat`;
- `Preuve manquante`;
- `Prochaine action`.

Fiche laterale ou dessous:

- frise courte `Vote -> Devis -> Commande -> Travaux -> Reception -> Reserves -> Garantie -> Clos`;
- preuves validees, candidates et manquantes;
- budget resume;
- diffusion;
- historique des actions prudentes.

Libelles a garder:

- `Preparer une demande au syndic`;
- `Rattacher une piece`;
- `Verifier la preuve candidate`;
- `Noter une reserve`;
- `Voir l'historique`.

Libelles a eviter:

- `WorksOps` comme titre utilisateur;
- `Travaux OK`;
- `Assurance OK`;
- `Envoyer automatiquement`;
- `Facture validee` pour un chantier.

## No-go avant dev

Une suite dev est bloquee tant que les points suivants ne sont pas acceptes:

- accepter le modele `OperationTravaux`;
- choisir la source du registre travaux: fixture synthetique, derive DocOps ou read model dedie;
- nommer les champs obligatoires de l'ecran `Travaux`;
- definir les statuts migratoires pour pieces contradictoires;
- clarifier travaux urgents hors AG;
- definir comment PrivacyOps arbitre l'export travaux;
- ouvrir un chantier dev separe avec owner code unique.

## Commande dev possible apres arbitrage

Premier lot recommande si Brice donne GO:

- creer un registre synthetique `works_operations_v1`;
- produire un read model travaux sans instance privee;
- afficher la page `Travaux` avec portefeuille + fiche probatoire;
- tester les statuts et les preuves sur corpus fictif;
- conserver les ports et tests selon le protocole agent;
- comparer l'UI livree au blueprint archive dans `docs/assets/ux-ui-recherche-2026-05-24-travaux/01-console-travaux-portefeuille-fiche.svg`.

## Point court

A produire:

- arbitrage Brice sur le modele `OperationTravaux`;
- commande dev separee si le modele est accepte;
- corpus fictif de 3 a 5 operations travaux.

En test:

- rien en execution applicative; lot documentaire seulement.

Images candidates:

- image retenue existante: `docs/assets/ux-ui-recherche-2026-05-24-travaux/01-console-travaux-portefeuille-fiche.svg`;
- aucune nouvelle image creee dans cette relance.

Decisions ouvertes:

- statut des travaux urgents hors AG;
- seuils de consultation CS et mise en concurrence par instance;
- source de verite du budget travaux;
- regle d'export diffusable aux coproprietaires.

Prochain mouvement:

- demander GO sur ce cadrage, puis ouvrir un chantier dev WorksOps distinct si GO.

## BOT-END

BOT-END - Coordinateur metier WorksOps - 2026-05-24 09:18 +02:00

Roadmap: `RM-2026-0032`
Chantier: `CH-20260524-091853-RM-2026-0032-cadrage-metier-worksops`
Conversation: `CONV-2026-1367`
Statut: `CLOTURE`
Fichiers modifies: `docs/cadrage_metier_worksops_2026-05-24.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers volontairement evites: code applicatif, routes, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, `RM-2026-0017` bloque.
Tests/preuves: sources officielles verifiees le 2026-05-24; cadrage metier livre; `git diff --check` OK sur les docs touches.
Limites: pas d'avis juridique, pas de validation utilisateur terrain, pas de dev, pas de serveur, pas d'instance privee.
Questions ouvertes: travaux urgents hors AG, seuils instance, source budget, export diffusable.
Prochain mouvement propose: arbitrer ce cadrage; si GO, ouvrir un chantier dev separe sur corpus synthetique.
