# Commande interface test - tri DocOps par feedback

Date: 2026-05-24.
Rattachement: `RM-2026-0029`.

## Objectif

Creer une interface locale de test pour corriger rapidement les propositions
DocOps apres passage a la moulinette: classement documentaire, confidentialite
et resultat de tri recuperable.

## Utilisateur cible

Un coproprietaire ou membre de conseil syndical qui veut corriger beaucoup de
documents sans terminal et sans ouvrir les fichiers bruts.

## Route cible

Route proposee: `/documents/tri-feedback`.

La route doit rester locale, token-safe, sans chemin prive et sans cloud.

## Structure UI

Vue principale:

- bandeau compact: nombre de documents, a corriger, ouverts, a biffer,
  reserves CS, bloques, a decider;
- commandes: relancer DocOps localement, enregistrer les corrections, exporter
  le resultat du tri;
- tableau par colonnes de confidentialite;
- une carte par document.

Colonnes initiales:

- Ouvert coproprietaires;
- A masquer avant partage;
- Reserve conseil syndical;
- Bloque;
- A decider.

Carte document:

- reference neutre `doc_id` court ou alias local;
- type documentaire propose;
- niveau de confidentialite propose;
- raison DocOps courte;
- etat texte local;
- confiance;
- selecteur de type documentaire;
- selecteur de confidentialite;
- champ justification, obligatoire si reserve CS ou bloque.

## Interaction

La version test peut commencer avec des selecteurs et boutons `Deplacer`.
Le drag-and-drop peut venir ensuite si les tests navigateur sont stables.

Chaque correction enregistre:

- `doc_id`;
- `sha256`;
- type propose avant/apres;
- confidentialite proposee avant/apres;
- justification;
- reviewer;
- horodatage;
- source `tri_feedback_ui`;
- statut d'application.

## Resultat recuperable

Registre local propose:

```text
registers/registre_feedback_docops.csv
```

Export test:

```text
outputs/reports/docops_feedback_tri.csv
outputs/reports/docops_feedback_tri.json
```

Ces sorties ne doivent contenir ni chemin absolu, ni contenu brut, ni table de
correspondance.

## Apprentissage local

Premiere version:

- enregistrer les corrections humaines;
- appliquer les corrections au registre documents;
- produire un comparatif avant/apres.

Version suivante:

- proposer des regles locales candidates;
- demander validation humaine avant activation;
- mesurer le taux de corrections repetees.

## Temps humain explicite

Cette fonctionnalite contient un temps humain incompressible:

- tri et arbitrage de documents;
- justification des restrictions;
- validation des regles locales candidates.

Ce temps doit apparaitre dans la roadmap et les compteurs UI. Il ne doit pas
etre presente comme automatisable a 100 %.

## Gates

- Aucun nom de fichier prive dans la page si le mode privacy strict est actif.
- Aucun chemin local, `raw`, `restricted`, `logs`, `file://` ou secret visible.
- La restriction CS ou le blocage demande une justification.
- Le resultat du tri est recuperable en registre local.
- Un testeur representant Brice peut corriger dix documents sans terminal.

## Retours equipe agile initiale

### Testeur representant Brice

Verdict: `NO-GO` pour declarer l'interface existante, `GO_CONDITIONNEL`
pour lancer un prototype testable.

Points a integrer avant dev:

- ajouter une regle courte de decision pour distinguer `A masquer`, `Reserve
  CS` et `Bloque`;
- reduire les cartes aux informations utiles a la decision rapide;
- fournir un indice neutre suffisant: type, date approximative, origine
  neutralisee, extrait masque seulement si autorise;
- afficher un compteur de modifications non enregistrees;
- prevoir annuler/revoir avant application definitive;
- apres enregistrement, afficher un resume de lot, un identifiant de session,
  les corrections appliquees, les erreurs et les liens CSV/JSON.

### QA privacy

Gates obligatoires:

- token requis sur la route et les exports;
- aucun champ interdit dans HTML, CSV, JSON ou messages d'erreur: chemin local,
  `file://`, `raw`, `restricted`, `logs`, nom prive, contenu brut, OCR brut,
  secret ou table de correspondance;
- validation serveur de `doc_id`, `sha256`, type documentaire, confidentialite
  et reviewer;
- justification serveur obligatoire pour `Reserve CS` ou `Bloque`;
- refus d'une ouverture brute si PrivacyOps exige biffage, aggregation ou
  `metadata_only`;
- test export: dix corrections visibles dans le resultat sans fuite.

### Cartographie technique minimale

Premier lot recommande:

- nouveau helper `server/src/coproscope/web/docops_feedback_route.py` pour lire
  le registre documents, valider les corrections et ecrire
  `registre_feedback_docops.csv`;
- nouveau helper `server/src/coproscope/web/docops_feedback_view.py` pour
  produire une vue sans noms de fichiers ni chemins;
- nouveau template `server/src/coproscope/web/templates/docops_feedback.html`;
- branchement GET/POST dans les fragments web existants, en evitant
  `viewmodel.py` et `depot.py`;
- tests dedies `server/tests/test_ui_docops_feedback_route.py`.

Fichiers a eviter pour le premier lot: instance reelle Beauvallon, `viewmodel.py`,
`depot.py`, passation, read models publics, secrets/OAuth.
