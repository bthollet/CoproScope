# Relecture IA - apprentissage DocOps par feedback

Date: 2026-05-24 02:38 +02:00.
Rattachement: `RM-2026-0029`, `CH-20260524-023853-RM-2026-0029-apprentissage-docops-feedback`.

## Synthese

La prochaine marche utile n'est pas d'ajouter une nouvelle heuristique cachee.
Il faut une boucle de feedback visible: DocOps propose, un humain corrige vite,
puis CoproScope enregistre les corrections pour ameliorer les regles locales.

La doctrine de confidentialite vient d'etre recadree: ouverture par defaut aux
coproprietaires, restriction seulement si un motif est etaye ou bloque par le
conseil syndical. L'interface de feedback doit donc rendre visibles les motifs
de restriction, pas seulement des colonnes "sensibles".

## Etat observe

Constat local anonymise sur l'instance de reconstruction:

- 540 documents sont revenus dans le registre apres reamorcage depuis l'inbox.
- 540 documents sont encore en classement `PENDING`.
- 436 documents demandent encore une revue de confidentialite.
- 104 documents ont une politique automatique.
- Aucun nom de fichier, chemin local ou contenu brut n'est repris dans cette
  note.

## Lecture produit

Le parcours actuel permet de deposer, voir une progression DocOps, choisir un
type documentaire, une confidentialite et rattacher une piece a un point/action.
Il reste trop sequentiel pour corriger beaucoup de documents.

Le besoin prioritaire est une interface de tri massif, reversible et tracable:

- une vue "moulinette DocOps" pour lancer ou relancer inventaire, texte local,
  classement et screening;
- une table ou un tableau par colonnes de confidentialite;
- une ligne ou carte par document, identifiee par reference neutre et hash/doc_id;
- deplacement rapide entre colonnes;
- edition rapide du type documentaire;
- justification obligatoire seulement pour restreindre ou bloquer;
- export ou registre local des corrections humaines;
- comparaison avant/apres pour verifier que l'apprentissage a eu un effet.

## Risques

- Trop de colonnes ou de jargon: l'humain doit trier vite, pas comprendre tout
  le moteur.
- Risque de fuite: la vue doit eviter chemins locaux, noms de fichiers trop
  parlants et contenu brut; elle peut afficher une reference neutre et un court
  extrait biffe ou masque si necessaire.
- Risque d'apprentissage opaque: une correction humaine doit produire une trace
  exploitable, pas seulement modifier le CSV courant.
- Risque de temps humain sous-estime: tri, arbitrage de confidentialite,
  validation OAuth et parametres de boite mail doivent etre marques comme
  interventions humaines dans le gouvernail.

## Decision de conception

Demarrer par une interface test locale, sans cloud, sans apprentissage modele
externe:

- `GET /documents/tri-feedback` affiche les documents a corriger.
- Colonnes initiales de confidentialite:
  `C2_Ouvert_coproprietaires`, `A_BIFFER`, `C4_Conseil_syndical`,
  `BLOQUE`, `A_DECIDER`.
- Chaque carte expose: reference neutre, type propose, niveau propose,
  raison courte, confiance, etat du texte local et action attendue.
- `POST /documents/tri-feedback` enregistre les corrections dans un registre
  dedie, puis applique une projection prudente au registre documents.
- Le resultat du tri doit etre recuperable en CSV/JSON local pour audit.

## Critere GO

Un representant novice doit pouvoir corriger dix documents en moins de cinq
minutes, comprendre pourquoi une restriction existe, puis retrouver le resultat
du tri dans un registre local sans chemin prive.
