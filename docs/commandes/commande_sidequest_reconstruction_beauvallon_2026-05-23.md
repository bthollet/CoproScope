# Commande sidequest - reconstruction progressive Beauvallon

Rattachement: `RM-2026-0017` / `CH-2026-0017`.
Date: 2026-05-23 18:51 +02:00.
Priorite: P0 sidequest prioritaire.

## Intention

Simuler, dans une instance specifique vide, la reconstruction progressive de la
base de connaissance CoproScope a partir des pieces primaires d'une copie du
dossier Beauvallon. La simulation doit aller jusqu'a l'integration complete de
toutes les pieces primaires du dossier Beauvallon reel.

La sortie obligatoire est une comparaison documentee entre:

- le dossier actuel reel: `<instance-privee-source-hors-git>`;
- le dossier test reconstruit: `<instance-simulation-hors-git>`.

Aucun verdict de succes ne peut etre donne sans rapport de comparaison reel/test.

## Instance et sources

Conteneur de simulation cible:

```text
<conteneur-simulation-hors-git>
```

Instance CoproScope cible:

```text
<instance-simulation-hors-git>
```

Docs de travail, manifests et matrices:

```text
<docs-travail-simulation-hors-git>
```

Copie de travail des pieces primaires creee par l'equipe:

```text
<copie-primaire-simulation-hors-git>
```

Source reelle a traiter en lecture seule:

```text
<instance-privee-source-hors-git>
```

Sont exclus de la copie primaire sauf decision explicite du coordinateur:

- `.git`, `.venv`, caches, worktrees, `_transition_reports`, `_archives`;
- `coproscope/` code produit, tests et docs generiques;
- `900_Systeme_Audit/coproscope_runtime/outputs`, `staging`, `logs`, caches et exports derives;
- rapports, projections, OCR derives et biffages si leur parent primaire existe;
- secrets, `.env.local`, cles, tables de correspondance non necessaires a la simulation.

Le principe: copier les sources probatoires primaires, puis laisser CoproScope
recreer inventaires, textes, registres, projections, rapports et read models.
Pour la simulation, les documents ne sont pas preclasses dans l'instance: ils
entrent dans `instance\200_INBOX`, puis CoproScope refait le tri.

## Definition de fini

- Instance test initialement vide et identifiee comme simulation, hors depot Git.
- Manifeste SHA-256 avant copie pour le reel et pour la copie primaire.
- Integration progressive en lots, avec journal horodate de chaque lot.
- Pipeline documentaire et modules metier relances apres chaque lot utile.
- Integration complete de toutes les pieces primaires selectionnees.
- Comparaison finale reel actuel vs test: fichiers, hashes, registres,
  classifications, textes/OCR, confidentialite, AG, demandes/actions/preuves,
  compta, KPI, rapports et read models publics.
- Rapport final avec deltas expliques: attendu, acceptable, anomalie, ou blocage.

## No-Go

- Ne jamais modifier le dossier reel.
- Ne jamais supprimer dans l'instance test sans sauvegarde et trace.
- Ne jamais copier de secrets, cles, `.env.local`, mappings de biffage sensibles
  ou exports prives vers Git.
- Ne pas utiliser de cloud ni d'OCR externe.
- Ne pas declarer "equivalent au reel" si la comparaison n'a pas ete produite.
- Ne pas melanger les outputs derives du reel avec les outputs reconstruits du test.

## Plan de lots

### Lot 0 - Preflight et instance vide

- Verifier que l'instance cible est vide ou neuve.
- Creer le squelette minimal `instance.yml`, dossiers `raw`, `registers`,
  `system`, `staging`, `outputs`, `logs`.
- Produire le manifeste initial vide.
- Fixer le journal `journal_integration_progressive.csv`.

### Lot 1 - Inventaire des pieces primaires

- Scanner le dossier reel en lecture seule.
- Marquer chaque fichier: primaire, derive, secret, cache, code, a_exclure,
  a_arbitrer.
- Produire `manifest_reel_pieces_primaires.csv`.
- Creer la copie primaire avec hashes verifies.

Racines primaires candidates a manifester en premier:

- `100_Collecte_RAW_non_modifie`;
- `200_INBOX/201_Docs_a_trier`;
- `200_INBOX/bvl.25`;
- `200_INBOX/IMPORT_920_Classement_unique_a_traiter`;
- `210_Referentiel_copropriete`;
- `220_Assemblees_generales`;
- `230_Comptes_finances_banque`;
- `250_Projets_collectifs/251_Renovation_energetique_ITE`;
- `270_Conseil_syndical_controle_syndic/271_Controle_des_comptes`;
- `270_Conseil_syndical_controle_syndic/272_Fichier_coproprietaires_RESTREINT`,
  en lot restreint trace privacy;
- `280_Reponses_syndic_CS_diffusables`.

Exclusions absolues de la copie primaire: code produit, `.git`, `.venv`,
caches, worktrees, `_transition_reports`, `_archives`, runtime derive
`900_Systeme_Audit/coproscope_runtime/outputs`, `staging`, `logs`,
`vault_local`, `vault_sync_chiffre_test_local`, OCR/textes derives,
redactions/biffages derives, secrets, `.env*`, credentials, OAuth, tokens,
tables de correspondance et mappings de biffage.

Arbitrages avant copie: `000_LIRE_AVANT_USAGE`, `010_Pilotage_Audit`,
`201_Dossiers_du_moment`, `290_Audit_360`, quarantaine doublons, registres
humains, et `Affiche Beauvallon.pdf`.

### Lot 2 - Referentiel et gouvernance copro

- Reglements, EDD, modifications, fiche synthetique, carnet entretien,
  contrats syndic et pieces de gouvernance.
- Verifier inventaire, extraction texte, classification et confidentialite.

### Lot 3 - AG, votes et demandes

- Convocations, PV, annexes, resolutions, demandes d'ordre du jour, votes,
  correspondances rattachees.
- Regenerer AGScope, DecisionOps et demandes/actions/preuves si applicable.

### Lot 4 - Comptes, factures et banque

- Redditions, annexes comptables, grands livres si presents, factures, impayes,
  consommation, rapprochements et pieces bancaires disponibles.
- Relancer ComptaScope seulement apres verification du perimetre primaire.

### Lot 5 - Travaux, ITE, diagnostics et financement

- Devis, diagnostics, PPPT/DTG/DPE, plans de financement, assurances travaux,
  offres et pieces de suivi.
- Produire les controles et matrices de coherence derivees depuis le test.

### Lot 6 - Contentieux, due diligence et correspondances

- Pieces contentieuses, demandes/reponses syndic, due diligence tiers,
  courriers et traces locales primaires.
- Respecter les niveaux de confidentialite; sorties partageables uniquement
  apres biffage ou synthese.

### Lot 7 - Integration complete et comparaison

- Relancer les projections finales utiles.
- Produire:
  - `rapport_comparaison_reconstruction_beauvallon_2026-05-23.md`;
  - `comparaison_manifestes_reel_vs_test.csv`;
  - `comparaison_registres_reel_vs_test.csv`;
  - `journal_integration_progressive.csv`.

Ordre de lancement recommande:

1. `100_Collecte_RAW_non_modifie`;
2. `200_INBOX` hors quarantaine;
3. referentiel copro `210`;
4. AG `220`;
5. finances `230`;
6. ITE/travaux `250/251`;
7. controle syndic/restreint/reponses `270` et `280`;
8. arbitrages `290`, quarantaine doublons, registres humains et fichiers racine;
9. comparaison finale reel/test.

## Comparaison obligatoire

Comparer au minimum:

- nombre de pieces primaires et total octets par famille;
- couverture hash: present reel, present copie, present test;
- documents indexes, types, statuts d'extraction et classification;
- files sans texte, OCR requis, OCR produit, OCR bloque;
- registres documents, demandes, AG, constats, diligences, tiers;
- screening confidentialite et file de biffage;
- sorties comptables 2025 si le lot compta est dans le perimetre;
- KPI/completude et missing docs;
- read models publics: `pieces?proof=missing`, actions si disponible;
- rapports reconstruits vs rapports reels: presence, origine, statut derive.

Chaque ecart doit etre qualifie:

- `ATTENDU`: derive volontairement non recopie;
- `A_CORRIGER`: piece primaire manquante, classification ou extraction divergente;
- `A_ARBITRER`: ambiguite primaire/derive ou confidentialite;
- `BLOQUANT`: impossible de comparer ou perte de preuve.

### Gabarits obligatoires

`journal_integration_progressive.csv` doit rester lisible par un conseil
syndical novice:

```csv
date_heure,lot,ce_qui_a_ete_ajoute,nombre_pieces,controles_realises,resultat_simple,ecarts_detectes,impact_conseil_syndical,prochaine_action,preuve_associee
```

`comparaison_manifestes_reel_vs_test.csv`:

```csv
scope,root_alias,rel_path_norm,family,selection_status,exclusion_reason,bytes,sha256,present_reel,present_primary_copy,present_test,hash_match_copy,hash_match_test,delta_class,delta_reason
```

`comparaison_registres_reel_vs_test.csv`:

```csv
register_name,key,metric,reel_value,test_value,match_status,delta_class,delta_reason,source_refs_count,privacy_status
```

Le rapport final `rapport_comparaison_reconstruction_beauvallon_2026-05-23.md`
doit commencer par:

- verdict `GO`, `GO sous reserve` ou `NO-GO`;
- reponse en une phrase a la question: l'instance test reconstruit-elle
  correctement le dossier Beauvallon reel ?
- cinq chiffres cles: pieces primaires attendues, pieces copiees, pieces
  integrees, textes extraits, ecarts bloquants;
- trois impacts conseil syndical: confiance documentaire, trous de preuve,
  limites de diffusion/confidentialite.

### Anti faux-GO

Pas de `GO` si:

- le rapport de comparaison reel/test est absent;
- les manifestes SHA-256 sont absents, incomplets ou divergents sans raison;
- une famille majeure n'est pas comparee sans justification;
- un output derive du reel peut etre confondu avec un output reconstruit du test;
- une piece primaire selectionnee manque sans qualification;
- un OCR/texte bloque porte sur un document essentiel sans statut clair;
- la confidentialite et la file de biffage ne sont pas controlees;
- les deltas ne sont pas classes entre `ATTENDU`, `A_CORRIGER`,
  `A_ARBITRER` et `BLOQUANT`;
- une fuite est detectee dans un rapport, CSV ou export: chemin absolu local,
  `file://`, token, `.env`, cle, mapping de biffage, log, raw/restricted prive,
  email/personne non biffee quand biffage requis.

Le `GO` exige `BLOQUANT = 0`, `A_CORRIGER = 0`, et `A_ARBITRER = 0` ou arbitrage
explicite du coordinateur.

## Equipe agile lancee

Roles initiaux:

- `CONV-2026-0120` coordinateur-scribe: gouvernail, presence, arbitrage lots.
- `CONV-2026-0121` source inventory: lecture seule du reel, manifeste primaire.
- `CONV-2026-0122` instance/pipeline: squelette test et commandes de reconstruction.
- `CONV-2026-0123` QA comparaison/privacy: gates anti-fuite et rapport reel/test.
- `CONV-2026-0124` produit/novice: lisibilite du journal et du rapport final.

Tous les agents doivent respecter:

- ils ne sont pas seuls dans le codebase;
- ne jamais revert les changements des autres;
- ne modifier que leur ownership declare;
- garder les donnees privees hors Git;
- finir par fichiers modifies/evites, tests ou preuves, limites et prochain geste.
