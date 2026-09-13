# Resilience anti-accaparement et gouvernance des cles

Date de reference : 2026-05-20

## Promesse

CoproScope doit proteger la copropriete contre deux risques symetriques :

- la fuite de donnees sensibles ;
- la confiscation ou suppression de la memoire collective par une personne, un groupe, un compte cloud ou un appareil.

La promesse produit est donc :

> Chaque coproprietaire peut telecharger l'archive complete, verifier son integrite, reconstruire toute l'information qui lui est ouverte, et conserver la preuve que les compartiments restreints existent sans pouvoir les lire sans les cles requises.

Ce point doit devenir un argument de communication central. CoproScope n'est pas seulement un coffre : c'est une memoire collective verifiable et non confisquable.

## Modele d'archive

Un coproprietaire doit pouvoir obtenir un paquet complet contenant :

- `vault.json` non sensible ;
- tous les evenements append-only ;
- tous les blobs chiffres ;
- tous les snapshots chiffres ;
- les manifestes de cles et enveloppes ;
- un rapport de verification ;
- un rapport des restrictions d'acces.

Le paquet complet ne signifie pas acces complet au contenu. Les parties non autorisees restent chiffrees. En revanche, le coproprietaire peut verifier :

- que les objets existent ;
- que les hashes correspondent ;
- que l'historique n'a pas de trou visible ;
- qu'une decision de restriction existe ;
- que la restriction a un auteur, une date, un motif et une signature.

## Compartiments de cles

V1 doit prevoir au minimum :

- cle coproprietaires : corpus collectif accessible aux coproprietaires ;
- cle conseil syndical : controle CS, brouillons, documents de gestion sensibles ;
- cle contentieux : pieces judiciaires ou precontentieuses ;
- cle comptes individuels : donnees nominatives de charges, impayes, aides ;
- cle commission : documents accessibles a une commission thematique ;
- cle exports/biffage : productions diffusablement controlees.

Chaque cle est enveloppee pour les membres/appareils/roles autorises. Le vault ne stocke jamais une cle en clair.

## Filets de sauvegarde

Les cles critiques ne doivent pas dependre du seul CS en place.

Mecanismes a specifier :

- partage de secret par quorum, par exemple 3 parts sur 5 ;
- parts inutilisables seules ;
- gardiens melanges : membres CS, coproprietaire non CS mandate comme gardien d'archive, ancien referent de passation, tiers de confiance optionnel ;
- kit de secours papier ou fichier chiffre hors cloud courant ;
- verification periodique du kit de secours ;
- rotation des parts apres depart, revocation ou perte ;
- ceremonie de recuperation signee, historisee et notifiee.

Une recuperation de cle doit produire un evenement `key_recovery_performed` avec motif, quorum, date, participants, nouvelle enveloppe de cle et statut de notification. Elle ne doit pas etre silencieuse.

## UX attendue

Page `Resilience du vault` :

- score : `reconstructible`, `a risque`, `capture possible`, `incomplet` ;
- bouton `Telecharger l'archive complete chiffree` ;
- bouton `Verifier cette archive` ;
- bouton `Reconstruire mon corpus autorise` ;
- panneau `Ce que je peux ouvrir` ;
- panneau `Ce qui existe mais reste restreint` ;
- panneau `Cles et secours` ;
- alertes : pas de gardien coproprietaire, quorum absent, snapshot trop ancien, blob manquant, device chain rompue, cle sans rotation.

## Tests d'acceptation

- Un coproprietaire lecteur peut telecharger une archive complete.
- Il peut verifier les hashes des objets restreints sans les dechiffrer.
- Il reconstruit tout le corpus autorise dans un cache local neuf.
- La suppression d'un evenement ou d'un blob est detectee.
- Une seule part de secours ne permet pas de recuperer une cle.
- Un quorum de secours recupere une cle collective si le CS est defaillant.
- La recuperation de cle est visible dans l'historique.
- Une revocation bloque les acces futurs sans effacer l'historique deja replique.

## Limites a annoncer

CoproScope ne peut pas promettre de recuperer une cle si toutes les parts de secours sont perdues ou detruites. Il doit en revanche detecter ce risque avant qu'il ne devienne irreversible.

CoproScope ne doit pas contourner les restrictions legitimes de confidentialite. Le droit de telecharger l'archive complete donne un droit de verification et de preservation, pas un droit automatique de lecture de tous les compartiments.
