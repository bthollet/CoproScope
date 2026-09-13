# UX workflow ajout de document

Date: 2026-05-20
Perimetre: exploration UX et contrat produit, sans code applicatif.

## Intention

L'ajout de document doit devenir un parcours de travail, pas seulement un
televersement. L'utilisateur depose une piece dans l'instance locale, comprend
ce que CoproScope en a deduit, arbitre la confidentialite, puis rattache la
piece a un point, une action et une preuve.

Le fil conducteur est:

`depot local -> classification -> confidentialite -> piece -> point -> action -> preuve`

## Principes non negociables

- Depot local d'abord: le brut entre dans l'instance locale, jamais dans un
  service distant.
- Aucun raw dans cloud: les dossiers de synchronisation, exports partageables et
  espaces collaboratifs ne recoivent pas de fichier brut, de nom original
  sensible, ni de chemin local.
- La source de verite reste le document local et ses empreintes; les vues
  metier manipulent des references, raccourcis et derives.
- La classification aide, mais ne decide pas seule: l'utilisateur peut corriger
  type documentaire, exercice, lot, fournisseur et statut.
- La confidentialite est traitee avant tout partage: diffusible brut, a biffer,
  reserve conseil syndical, bloque ou a arbitrer.
- Le rattachement probatoire est explicite: une piece peut servir plusieurs
  points, mais chaque lien porte son intention.
- Les futures annotations PDF et signatures sont des evenements separes; elles
  ne modifient pas le PDF source.

## Parcours cible

### 1. Depot local

L'ecran accepte un glisser-deposer ou une selection de fichier. Il montre une
file courte avec nom affiche, taille, format, statut de lecture et avertissement
si le fichier semble deja present.

Actions attendues:

- calculer une empreinte locale du fichier;
- creer ou reutiliser un `doc_id`;
- conserver le brut uniquement dans la zone locale prevue;
- enregistrer la provenance utilisateur sans exposer le chemin absolu;
- signaler les doublons par hash, pas par copie supplementaire.

Etat UX attendu:

- `pret a analyser`;
- `doublon possible`;
- `format non lu`;
- `depot local bloque`.

### 2. Classification assistee

Apres depot, CoproScope propose une classification lisible: type documentaire,
periode, domaine, acteur cite, lot ou theme, confiance, et raison courte.

L'utilisateur doit pouvoir:

- accepter la proposition;
- corriger le type documentaire;
- marquer `A_CLASSER` si la piece est ambigue;
- declarer qu'il s'agit d'une nouvelle version d'un document connu;
- orienter la piece vers AG, comptes, travaux, incident, contentieux ou demande.

La classification ne doit jamais entrainer de diffusion automatique.

### 3. Confidentialite avant sortie

Avant tout rattachement visible dans une restitution, le parcours demande un
arbitrage de confidentialite.

Statuts proposes:

| Statut | Effet UX |
|---|---|
| `DIFFUSABLE_BRUT` | La piece peut etre citee ou montree telle quelle dans un espace autorise. |
| `A_BIFFER` | Une version derivee doit etre preparee avant diffusion. |
| `RESERVE_CS` | Visible seulement dans le contexte conseil syndical. |
| `BLOQUE` | Aucune sortie ni export ne peut l'utiliser directement. |
| `A_ARBITRER` | L'utilisateur doit trancher avant partage. |

Garde-fous:

- aucun raw dans cloud;
- aucun chemin local dans une page partageable;
- aucun document sensible dans un export diffusable;
- les versions biffees sont des derives, jamais des remplacements du brut;
- les cartes de pseudonymisation restent locales et non publiees.

### 4. Rattachement piece -> point -> action -> preuve

Le coeur de l'UX est un panneau de rattachement en quatre colonnes.

| Niveau | Question utilisateur | Donnee attendue |
|---|---|---|
| Piece | Qu'est-ce que ce fichier apporte ? | `doc_id`, type, extrait ou ancre locale. |
| Point | A quel sujet concret le rattacher ? | AG, decision, demande, facture, incident, chantier, contentieux. |
| Action | Que faut-il faire maintenant ? | verifier, demander, relancer, biffer, transmettre, classer. |
| Preuve | Que prouvera ce lien plus tard ? | presence, decision, reception, execution, paiement, refus, cloture. |

Regles:

- un document peut alimenter plusieurs preuves sans duplication physique;
- chaque lien doit avoir un libelle metier, pas seulement un identifiant;
- l'action doit rester visible tant que la preuve attendue manque;
- une preuve ne doit pas exposer un brut interdit;
- les raccourcis de dossiers pointent vers la reference, pas vers une copie raw.

### 5. Validation humaine

Avant fermeture du parcours, CoproScope affiche un recapitulatif:

- fichier ajoute ou doublon reutilise;
- classification retenue;
- niveau de confidentialite;
- rattachements crees;
- actions ouvertes;
- preuves attendues ou deja couvertes;
- limites connues: OCR absent, signature non verifiee, biffage a produire.

Le bouton de sortie ne dit pas seulement `Terminer`; il nomme l'effet reel:
`Enregistrer la piece`, `Enregistrer et demander une preuve`, ou
`Enregistrer et preparer une version biffee`.

## Annotation PDF future

L'annotation PDF est un objectif futur. Le contrat UX est deja fixe:

- une annotation ne modifie pas le fichier PDF source;
- une annotation est un evenement separe lie a `doc_id`, page, zone, auteur,
  horodatage et hash du document cible;
- une annotation peut creer un point, une action ou une preuve;
- une annotation peut etre masquee dans un export si la confidentialite l'exige;
- l'absence de moteur d'annotation ne bloque pas le depot local ni le
  rattachement probatoire.

## Evenement signe futur

La signature est egalement future pour ce workflow. Le parcours doit toutefois
preparer les bons objets:

- `document_added`;
- `document_classified`;
- `document_privacy_reviewed`;
- `document_linked_to_point`;
- `action_created_from_document`;
- `proof_attached`;
- `pdf_annotation_created` quand l'annotation sera disponible;
- `signed_event_recorded` quand la signature sera disponible.

Chaque evenement signe futur devra porter au minimum: identifiant logique,
type d'evenement, acteur, date UTC, hash des entrees, hash des sorties, version
de schema et statut de verification.

## Donnees derivees autorisees

Les espaces collaboratifs ou exports ne peuvent recevoir que des derives
controles:

- identifiants opaques;
- hash courts ou complets selon le contexte;
- resume non sensible;
- extrait OCR autorise;
- version biffee;
- statut de preuve;
- statut de confidentialite;
- evenement signe ou journalise.

Ce qui reste interdit hors local:

- fichier raw;
- chemin absolu;
- nom original sensible;
- cache dechiffre;
- carte de pseudonymisation;
- annotation contenant une donnee bloquee;
- export qui reconstruit indirectement le document brut.

## Criteres d'acceptation UX

- Un novice comprend la difference entre document, piece, point, action et
  preuve.
- Un fichier depose localement peut etre classe, arbitre en confidentialite et
  rattache sans quitter le parcours.
- Le parcours permet de dire "je ne sais pas encore" via `A_CLASSER` ou
  `A_ARBITRER`.
- Une piece sensible ne peut pas glisser silencieusement vers le cloud, un
  export ou une vue diffusable.
- Le workflow prepare l'annotation PDF future et l'evenement signe futur sans
  les presenter comme deja livres.
- Le test documentaire statique peut verifier les invariants: depot local,
  classification, confidentialite, chaine `piece -> point -> action -> preuve`,
  annotation PDF future, evenement signe futur, aucun raw dans cloud.
