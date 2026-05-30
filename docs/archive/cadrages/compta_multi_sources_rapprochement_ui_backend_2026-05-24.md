# Compta multi-sources - rapprochement, suggestion et validation

Date de reference: 2026-05-24.
Rattachement gouvernail: `RM-2026-0030`.
Chantier: `CH-20260524-030432-RM-2026-0030-compta-4-sources-ux`.

## Synthese courte

Les trois concepts valides font evoluer `/comptes` depuis une lecture guidee
des anomalies vers un atelier de reconciliation multi-sources.

Le coeur produit n'est pas un tableau comptable de plus. Le coeur devient:

1. prendre une ligne comptable;
2. regarder ce que disent la banque, les factures et les decisions/devis;
3. proposer un ou plusieurs rapprochements explicables;
4. faire valider, reserver, ecarter ou transformer en question syndic par un
   humain;
5. tracer cette decision sans modifier la comptabilite officielle.

La source minimale n'est donc pas "deux colonnes a comparer". Le modele doit
croiser au moins quatre familles:

- compta: ligne de depense, grand livre, compte et exercice;
- banque: mouvement bancaire, date, montant, libelle, compte;
- facture: facture, fournisseur, date, TTC, piece;
- decision/devis/contrat: PV d'AG, devis, contrat, bon de commande, reception.

## Captures retenues

### Concept 1 - File de validation 4 sources

![Concept 1 - File de validation 4 sources](assets/compta-multisources-2026-05-24/01-file-validation-4-sources.png)

Ce concept place l'utilisateur dans une file de travail. Chaque ligne comptable
affiche directement son etat sur les autres sources.

Implication parcours:

- l'utilisateur commence par les lignes `A traiter` ou `A confirmer`;
- il voit en une ligne si banque, facture et decision/devis existent;
- il ne valide pas un rapprochement abstrait: il valide une ligne avec son
  faisceau de preuves;
- l'action principale peut etre `Valider`, `Valider avec reserve`,
  `Demander piece`, `Demander devis` ou `Reporter AG`.

Implication backend:

- un read model `compta_reconciliation_queue_v1` doit fournir une ligne par
  ligne comptable;
- chaque ligne expose des cellules publiques pour `bank`, `invoice`,
  `decision_evidence`;
- la suggestion porte une raison lisible, pas seulement un score;
- la validation humaine est un evenement append-only distinct de la suggestion
  machine.

### Concept 2 - Matrice de rapprochement

![Concept 2 - Matrice de rapprochement](assets/compta-multisources-2026-05-24/02-matrice-rapprochement.png)

Ce concept rend visible la completude par source. Il est plus proche d'un outil
de controle: une cellule rouge ou orange dit exactement quelle famille de preuve
bloque.

Implication parcours:

- l'utilisateur peut filtrer par manque de banque, facture, decision ou conflit
  montant;
- le clic se fait au niveau cellule, pas seulement au niveau ligne;
- une cellule `Decision a confirmer` ouvre un diagnostic et une question syndic;
- le rapport AG peut etre bloque par les cellules non revues.

Implication backend:

- le moteur doit produire une matrice `line_id x source_family`;
- chaque cellule a un statut `ok`, `missing`, `candidate`, `conflict`,
  `to_review`, `validated`;
- les blocages d'export AG doivent lire ces statuts publics, sans recalculer le
  dashboard complet;
- les cellules doivent pointer vers des objets sources par identifiants stables
  et labels publics, jamais par chemins locaux.

### Concept 3 - Suggestions classees

![Concept 3 - Suggestions classees](assets/compta-multisources-2026-05-24/03-suggestions-classees.png)

Ce concept sert quand une ligne a plusieurs rapprochements possibles. Il ne
montre pas seulement une meilleure suggestion; il montre plusieurs faisceaux
banque + facture + decision avec raisons et actions.

Implication parcours:

- l'utilisateur selectionne une ligne ambigue;
- CoproScope propose plusieurs faisceaux classes;
- l'utilisateur choisit, valide avec reserve, compare, ecarte ou demande une
  decision;
- une note de validation conserve le doute pour le conseil syndical et l'AG.

Implication backend:

- le moteur doit construire des `candidate_bundles`, pas seulement des paires;
- un faisceau peut contenir plusieurs mouvements bancaires ou plusieurs pieces;
- les raisons doivent etre exposees comme faits: montant identique, fournisseur
  proche, decision absente, somme compatible, periode large;
- les rejets humains doivent etre conserves pour eviter de reproposer la meme
  mauvaise combinaison sans contexte.

## Parcours utilisateur cible

1. L'utilisateur ouvre `Controle des comptes`.
2. Il choisit une entree: `A traiter avant AG`, `A confirmer`,
   `Sources orphelines` ou `Conflit montant`.
3. Il selectionne une ligne comptable.
4. Il voit les quatre familles de source, avec un statut par famille.
5. Il ouvre le detail de la suggestion ou la matrice.
6. Il valide, valide avec reserve, ecarte ou cree une question syndic.
7. Si une piece manque, CoproScope prepare une demande sans pretendre envoyer
   le message.
8. La decision humaine alimente le rapport AG, la memoire et les actions.

Ce parcours doit rester comprehensible sans savoir tenir une comptabilite.
Les codes internes restent secondaires. Les libelles humains priment:
`A traiter avant AG`, `A confirmer`, `OK avec preuve`, `Decision absente`,
`Facture absente`, `Debit bancaire candidat`.

## Contrat backend attendu

| Objet | Role | Champs minimaux |
|---|---|---|
| `accounting_line` | Ligne de reference comptable | `line_id`, exercice, compte, libelle, montant, date, source_label |
| `bank_movement` | Preuve de flux bancaire | `movement_id`, date, montant, libelle public, compte bancaire public |
| `invoice_evidence` | Preuve facture | `invoice_id`, `doc_id`, fournisseur, date, montant TTC, statut OCR |
| `decision_evidence` | Justification metier | `decision_id`, type, date, libelle, source publique, statut |
| `reconciliation_cell` | Etat d'une source pour une ligne | `line_id`, `source_family`, statut, raison, href detail |
| `candidate_bundle` | Faisceau propose | `bundle_id`, `line_id`, source_ids, score, raisons, manques |
| `human_validation` | Decision humaine tracee | `validation_id`, `line_id`, `bundle_id`, decision, reserve, acteur, date |
| `syndic_question` | Question derivee | `question_id`, preuve attendue, texte copiable, statut, diffusion |

Le modele relationnel peut rester simple, mais l'UI impose un graphe logique:
une ligne compta peut etre liee a plusieurs mouvements, plusieurs factures et
plusieurs preuves de decision. Le backend ne doit pas forcer une relation
1 ligne = 1 facture = 1 debit.

## Etats et decisions

Statuts machine utiles:

- `missing_source`: une famille manque;
- `candidate`: un indice existe mais doit etre confirme;
- `conflict`: deux sources se contredisent;
- `strong_match`: preuves concordantes;
- `validated`: humain confirme;
- `validated_with_reserve`: humain confirme avec reserve visible;
- `rejected`: humain ecarte la suggestion;
- `question_needed`: une demande syndic doit etre preparee;
- `blocked_for_export`: le point ne doit pas sortir sans revue.

Decisions humaines minimales:

- `Valider`;
- `Valider avec reserve`;
- `Ecarter`;
- `Demander une piece`;
- `Demander une decision ou un devis`;
- `Ajouter au rapport AG`;
- `Laisser ouvert`.

## MVP recommande

Le MVP le plus robuste est une combinaison des trois concepts:

1. utiliser le Concept 1 comme ecran principal de travail;
2. ouvrir le Concept 2 comme vue d'audit ou filtre de completude;
3. utiliser le Concept 3 pour le detail d'une ligne ambigue.

Premiere tranche executable:

- read model public `compta_reconciliation_queue_v1`;
- projection des quatre cellules par ligne;
- generation de suggestions simples par montant/date/fournisseur;
- validation humaine append-only;
- question syndic creee depuis une cellule manquante;
- rapport AG qui affiche seulement les lignes validees ou ouvertes avec reserve.

## Gates UX, privacy et qualite

- Aucun chemin local, dossier `raw`, `restricted`, `logs` ou `file://` dans les
  cellules et details.
- Une suggestion n'est jamais affichee comme verite comptable officielle.
- Toute validation humaine cree une trace datee.
- `Valider avec reserve` reste visible dans le rapport AG.
- Une cellule rouge ou orange bloque ou avertit avant export.
- Les boutons n'impliquent jamais un envoi automatique au syndic.
- Les codes techniques et scores seuls ne suffisent pas: chaque suggestion doit
  afficher une raison novice.

## Trace de chantier

BOT-START - Coordinateur UX/compta - 2026-05-24 03:04 +02:00

Roadmap: `RM-2026-0030`.
Chantier: `CH-20260524-030432-RM-2026-0030-compta-4-sources-ux`.
Conversation: `CONV-2026-1311`.
Role: analyse UX/backend et mise au gouvernail.
Ownership modifiable: cette note, images sous `docs/assets/compta-multisources-2026-05-24/`, `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`.
Fichiers evites: code applicatif, instances privees, sorties comptables reelles.
Tests/preuves attendus: images copiees dans la doc, analyse ecrite, gouvernail et presence mis a jour, verification markdown par recherche locale.

BOT-END - Coordinateur UX/compta - 2026-05-24 03:04 +02:00

Statut: INTEGRE documentaire.
Fichiers modifies: cette note, gouvernail, presence, assets PNG documentaires.
Tests/preuves: verification par lecture des images et references markdown.
Limites: aucun contrat de donnees implemente; aucun test applicatif lance.
Prochain mouvement propose: choisir la tranche MVP et ouvrir un owner back/read model avant tout dev UI.
