# Backlog produit fini refonte UX

> Statut gouvernail: `SOURCE_HISTORIQUE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0003`). Utiliser ce fichier comme reserve UX, pas comme file active.

Date de creation: 2026-05-21.
Derniere mise a jour: 2026-05-21 06:12 +02:00.

Ce backlog anticipe l'apres Cycle 7. Il ne lance pas de developpement hors
cadence: il nomme les vues, contrats et tests encore manquants pour tendre vers
un produit fini CoproScope V1, puis sert de file ordonnee pour les roles liberes.

Regle de lecture: chaque ligne doit rester testable par route reelle, contrat
`model.ux.*` ou objet noyau nomme, et test produit. Une vue sans contrat ou sans
test reste en `FILE_ATTENTE`.

## Ordre produit fini

| Ordre | Chantier | Vues manquantes ou a finir | Contrats a stabiliser | Tests attendus | Critere de sortie |
|---:|---|---|---|---|---|
| 1 | Comptes | `/comptes` avec detail de ligne, synthese AG, questions syndic et preuves lisibles | `model.ux.comptes`, `AccountingControl`, liens token-safe, statut P1/P2/OK en mots humains | Route 200 avec token, filtres P1/P2/OK, detail ligne, export prudent, jargon primaire absent | Un membre CS prepare une question syndic ou justifie un OK sans etre comptable |
| 2 | Memoire | `/chantiers` en timeline de passation avec sujets ouverts, restrictions et dernier etat | `model.ux.memoire`, `MemoryBrief`, liens vers decisions, demandes, incidents, contrats et preuves | Route 200, timeline ordonnee, sujet ouvert rattache a action/preuve, pack derive sans brut interdit | Un nouveau CS comprend l'historique utile et ce qui reste a transmettre |
| 3 | Vues manquantes | `Mes coffres`, `Membres et droits`, demandes detaillees, AG avant/pendant/apres, pilotage injecte dans cockpit | `model.ux.coffres`, `model.ux.access`, `model.ux.requests`, `model.ux.ag`, `model.ux.pilotage` | Smoke routes, isolation coffre/role/cache/export, droits par profil synthetique, aucune fuite inter-coffre | Les portes produit restantes existent sans obliger le novice a comprendre le moteur |
| 4 | Detail piece/preuve | Fiche piece/preuve depuis `/pieces` et `/documents`: apercu, preuve de quoi, rattachements, historique, diffusion | `model.ux.piece_detail`, `ProofRef`, `EvidenceRef`, `object_id` stable, statut signature/verif | Clic ligne -> detail, texte long stable, raw non servi, preuve differenciee de piece candidate | Une piece ouverte dit pourquoi elle compte, quelle preuve elle porte et quoi faire |
| 5 | Arbitrage diffusion | Revue de diffusion depuis action, piece, demande, memoire et export | `model.ux.diffusion_review`, `DiffusionDecision`, niveaux brut/biffage/agregation/bloque/a arbitrer | Tests anti-fuite, biffage requis visible, blocage export sans decision, libelle "qui peut voir" | Aucun utilisateur ne partage un brut sensible sans decision explicite |
| 6 | Export passation | `/exports/passation.*` avec apercu, restrictions, index des preuves et mention derivee | `PassationPack`, `build_passation_derived_export`, `source_of_truth: false`, hash exporte | Export sans source privee, restrictions conservees, replay apres purge cache, token maintenu | Le pack transmet la memoire sans devenir source de verite ni fuite de donnees |
| 7 | Tests navigateur | Parcours bout-en-bout sur routes reelles desktop/mobile/tablette | Scenario navigateur: cockpit -> comptes -> memoire -> piece -> diffusion -> passation | Screenshots, clics filtres/details, responsive, navigation retour, absence chevauchement texte | La version produit est verifiee comme experience, pas seulement par tests unitaires |

## Contrats transverses manquants

| Contrat | Sert a | Condition avant dev |
|---|---|---|
| `model.ux.selected_item` | Ouvrir un detail coherent depuis les listes: action, piece, preuve, demande, evenement memoire | Chaque liste prioritaire expose un identifiant stable et un lien token-safe |
| `model.ux.diffusion_badge` | Afficher partout le statut de partage avant action ou export | Les niveaux de diffusion sont nommes en langage utilisateur |
| `model.ux.passation_preview` | Previsualiser ce qui sort du coffre avant export | Le pack declare sources, restrictions et exclusions |
| `model.ux.browser_acceptance` | Piloter les tests navigateur sans improviser | Les routes, filtres, clics et tailles d'ecran sont listes |

## Cadence anti-idle

| Role qui se libere | Reprise automatique | Sortie horodatable |
|---|---|---|
| Front | Prendre le premier item ordonne dont le blueprint est pret: Comptes puis Memoire puis detail piece/preuve | Route visible ou fiche detail testable |
| Back/viewmodel | Stabiliser le contrat `model.ux.*` du meme item que le front | Donnees synthetiques, liens token-safe, aucune fuite raw/restricted |
| QA/Test produit | Tester la route livree puis ouvrir le scenario navigateur du prochain item | Go/no-go par route reelle, avec P0/P1/P2 |
| Designer | Garder une commande d'avance: Cycle 7 puis backlog Cycle 8 | Blueprint, criteres novice et tests attendus |
| Novice | Lire les mots et les attentes au clic du prochain item | Verbatims, doutes de vocabulaire, no-go utilisateur |
| Coordinateur | Tenir registre, backlog et prochains mouvements | Point 10 min sans champ vide, role idle remplace |

## Garde-fous produit fini

- Une vue "presque finie" sans detail ouvrable reste incomplete.
- Une preuve ne doit jamais etre confondue avec une piece candidate.
- Un export est derive, jamais source de verite.
- Une decision de diffusion doit dire qui peut voir, sous quelle forme, et ce qui
  reste exclu.
- Les tests navigateur deviennent obligatoires des qu'une route sert a valider
  un parcours utilisateur, meme si les tests unitaires sont verts.
