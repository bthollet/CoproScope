# Checklist runtime ajout document

Date: 2026-05-20
Perimetre: modele pur, sans lecture fichier reel et sans route applicative.

## Intention

Ce modele decrit le parcours runtime minimal pour ajouter un document dans une
instance locale CoproScope. Il ne lit pas le fichier, ne copie pas de brut et ne
publie rien. Il transforme seulement des donnees deja fournies par le depot
local en checklist novice, statut runtime et prochaine action.

Fil cible:

`depot local -> classification -> confidentialite -> rattachement piece -> point -> action -> preuve`

## Sorties runtime

- Checklist novice: une ligne lisible par etape, avec statut et prochaine action.
- Statut runtime: `pret_a_enregistrer`, `a_completer` ou `bloque`.
- Prochaine action: la premiere action concrete qui debloque le parcours.
- Evenements futurs prevus: noms de types d'evenements, sans signature active.

## Etapes

### 1. Depot local

But novice: "Le fichier brut reste dans mon instance locale."

Le modele attend un `doc_id`, une empreinte deja calculee et une reference
opaque. Un chemin absolu, une URL ou une cible cloud brute est masque ou bloque.

Statuts:

- `ok`: document reference localement, empreinte presente.
- `a_completer`: `doc_id`, empreinte ou reference opaque manquante.
- `bloque`: raw demande vers cloud ou synchronisation brute.

Prochaine action type: fournir `doc_id` et empreinte produits par le depot
local, ou retirer toute cible cloud du brut.

### 2. Classification

But novice: "Je sais quel type de document c'est, ou je dis que je ne sais pas."

Le modele garde une classification legere: type documentaire, domaine, periode,
acteur cite, lot, confiance et raison courte.

Statuts:

- `ok`: classification proposee ou acceptee avec type documentaire.
- `a_completer`: type absent, proposition a confirmer ou statut `A_CLASSER`.

Prochaine action type: accepter, corriger ou garder `A_CLASSER` pour revue
humaine.

### 3. Confidentialite

But novice: "Je decide qui peut voir la piece avant tout partage."

Statuts acceptes:

- `DIFFUSABLE_BRUT`
- `A_BIFFER`
- `RESERVE_CS`
- `BLOQUE`
- `A_ARBITRER`

Regles:

- aucun raw dans cloud;
- aucun chemin local dans une sortie partageable;
- une version biffee est un derive, jamais un remplacement du brut;
- `BLOQUE` arrete le runtime;
- `A_ARBITRER` garde le runtime en `a_completer`.

### 4. Rattachement piece -> point -> action -> preuve

But novice: "Je relie ce document a un sujet concret, a une action et a ce que
cela prouvera plus tard."

Chaque rattachement doit contenir:

- piece: libelle metier ou `doc_id`;
- point: sujet concret, par exemple AG, decision, demande, facture, incident,
  chantier ou contentieux;
- action: verifier, demander, relancer, biffer, transmettre ou classer;
- preuve: presence, decision, reception, execution, paiement, refus ou cloture.

Le modele autorise plusieurs rattachements pour un meme document sans dupliquer
le fichier brut.

### 5. Annotation PDF future

L'annotation PDF future ne bloque pas le depot. Elle est seulement preparee
comme evenement separe: `doc_id`, page, zone, auteur futur et hash du document
cible. Le PDF source ne doit pas etre modifie.

### 6. Evenement signe futur

L'evenement signe futur ne pretend pas que la signature est livree. Le modele
prepare les types:

- `document_added`
- `document_classified`
- `document_privacy_reviewed`
- `document_linked_to_point`
- `action_created_from_document`
- `proof_attached`
- `pdf_annotation_created`
- `signed_event_recorded`

Quand la signature existera, chaque evenement devra porter acteur, date UTC,
hash des entrees, hash des sorties, version de schema et statut de verification.

## Invariants testables

- Le modele est pur: pas de lecture fichier reel, pas de route, pas d'ecriture.
- Les sorties sont une checklist novice, un statut runtime et une prochaine
  action.
- Le parcours couvre depot local, classification, confidentialite et
  rattachement piece -> point -> action -> preuve.
- Une cible cloud brute est bloquee.
- Un chemin local ou absolu est masque avant sortie.
- `A_CLASSER` et `A_ARBITRER` gardent le parcours comprehensible pour un novice.
- L'annotation PDF future et l'evenement signe futur sont presents mais non
  annonces comme livres.
