# Archive et reconstruction coproprietaire

Ce lot decrit le modele leger `coproscope.vault.reconstruction_archive`.
Il formalise l'objectif anti-confiscation: un coproprietaire peut obtenir une
archive complete, verifier qu'elle n'a pas ete amputeee, reconstruire ce que
son role autorise, et voir ce qui existe encore mais reste restreint.

## Intentions

- L'archive est complete: elle contient aussi les payloads chiffres que le
  coproprietaire ne peut pas lire.
- Le manifeste d'integrite liste les entrees, tailles, empreintes et preuves
  d'existence.
- La reconstruction ne rend que les compartiments pour lesquels le role et la
  cle abstraite sont presents.
- Une partie restreinte est prouvable par hash, sans exposer son contenu dans
  le manifeste ni dans le rapport novice.
- Le rapport novice separe trois questions: ce que je peux reconstruire, ce
  qui existe mais reste restreint, qui peut aider a recuperer.

## Modele de donnees

`CorpusPart` represente une piece logique du corpus. Elle porte:

- un identifiant technique stable;
- un type et un libelle public non sensible;
- un compartiment;
- un payload metier;
- les roles autorises;
- les contacts ou groupes qui peuvent aider a recuperer un compartiment.

`DownloadableArchive` represente l'archive remise au coproprietaire. Elle
contient:

- un `ArchiveManifest`;
- les payloads scelles pour toutes les parties du corpus;
- les cles abstraites disponibles pour le destinataire.

Le scellement n'est pas un chiffrement de production. Il sert aux tests et a la
modelisation: le contenu n'apparait pas dans le manifeste, l'integrite est
controlee par SHA-256, et la reconstruction echoue si la cle abstraite ne
correspond pas.

## Manifeste et preuves

Chaque entree du manifeste conserve:

- `sealed_sha256`: empreinte du payload scelle;
- `sealed_size`: taille du payload scelle;
- `payload_commitment_sha256`: engagement sur le payload clair, sans l'exposer;
- `existence_proof_sha256`: preuve derivee de l'archive, du vault, de la partie
  et des empreintes.

Le manifeste lui-meme porte `manifest_sha256`, calcule sur sa forme canonique.
Une modification d'acces, de preuve, de taille ou d'empreinte produit une erreur
de verification.

## Reconstruction autorisee

`reconstruct_authorized_corpus()` commence par verifier l'archive.

Si l'integrite echoue, aucune reconstruction n'est rendue. Si l'integrite est
valide, chaque entree est traitee ainsi:

- entree lisible et cle presente: ouverture du payload, controle de son hash,
  ajout au corpus reconstruit;
- entree restreinte: ajout d'une preuve de presence sans contenu;
- entree annoncee lisible mais cle incorrecte ou payload illisible: bascule en
  preuve restreinte avec raison explicite.

Cette logique evite de confondre telechargement complet et droit de lecture.

## Rapport novice

`build_novice_reconstruction_report()` produit un objet serialisable avec:

- `ce_que_je_peux_reconstruire`: libelles, types et preuves des elements
  lisibles;
- `ce_qui_existe_mais_reste_restreint`: libelles publics, raisons et preuves
  d'existence;
- `qui_peut_aider_a_recuperer`: contacts ou groupes dedoublonnes depuis les
  parties restreintes;
- `summary`: phrase courte comptant les elements reconstructibles, restreints
  et les contacts de recuperation.

Le rapport ne contient pas les payloads restreints. Il doit rester lisible pour
un coproprietaire non technicien: l'information principale est "je peux
reconstruire ceci", "cela existe mais je n'ai pas le droit ou la cle", "voici
qui peut aider".

## Limites assumees

- Le module ne remplace pas le chiffrement fort du vault de production.
- Les cles sont des chaines abstraites destinees aux tests.
- Les payloads sont des objets JSON canoniques, pas encore des blobs physiques.
- Les preuves d'existence prouvent une presence et une integrite, pas un droit
  de diffusion.
- La recuperation est seulement orientee par des `RecoveryHelper`; elle ne
  declenche pas de workflow de quorum.

Ces limites sont volontaires pour garder un noyau metier testable avant de le
brancher au vault chiffre reel.
