# Reconstruction du 2026-09-06 : completer le coffre, puis reconstruire l'instance

Arbitrage de Brice: pour eprouver les outils, on ne copie pas une instance
existante - **on la reconstruit depuis le coffre**. Et avant de reconstruire, on
verifie que le coffre a bien tout.

## 1. Le coffre ne les avait pas tous

Comparaison par empreinte SHA-256 entre le coffre et le lot de captation
`Captation_coprodirecte_2026-09-02` - capture en lecture seule de l'espace
`coprodirecte.fr` du syndic, faite le 2 septembre sur le compte d'une
conseillere syndicale avec son accord, lot d'origine scelle.

| | |
|---|---:|
| PDF de la captation | 699 |
| deja au coffre | 429 |
| **absents du coffre** | **270** |
| dont justificatifs d'une ligne de depense | 197 |
| dont sans couche texte | 32 |

**Verses** dans `100_Collecte_RAW_non_modifie/105_Captation_coprodirecte_2026-09-02/`,
copies depuis le lot **scelle**, jamais depuis la copie de travail ocerisee.
Empreinte recalculee apres copie et comparee au nom: **zero ecart sur 270**.

Le dossier porte son `LISEZ-MOI.txt` et un `_journal_versement.tsv` qui donne,
pour chaque piece, sa taille, son volume de texte, son adresse d'origine sur le
portail, et - quand elle justifie une depense - l'exercice, la date, le poste,
le libelle et le montant.

**Les fichiers gardent leur nom d'empreinte.** C'est la discipline du lot de
captation et elle est volontaire: le libelle affiche par le portail est une
affirmation du syndic, l'empreinte est un fait verifiable.

## 2. L'axe qui separe une piece d'un artefact

> **Une piece porte l'affirmation d'un tiers. Un artefact porte notre lecture.**

Ni le dossier, ni le type de document, ni le canal d'arrivee ne tranchent. Le
cas d'ecole est dans le coffre, deux fichiers du meme type de part et d'autre:

- `250_.../01_Contentieux_sources/assignation oubar.pdf` - **recue**. Piece.
- `260_.../Word_relecture_QA_render/00_PROJET_assignation_refere_...pdf` -
  **redigee par nous**. Artefact.

**Le producteur du PDF oriente mais ne tranche pas.** Le DTG et les quatre DPE
de WeGroup sont produits sous Word - outil d'auteur - mais l'auteur est un
bureau d'etudes tiers. Inversement une vraie facture imprimee en PDF porte
`Microsoft: Print To PDF`. Trois signaux ont ete croises, par force
decroissante: servi par le portail (certain), chaine metier d'un tiers
(`WinDev`, `Crystal`, `PReS Connect`, `Stimulsoft`, `Aspose`, `RICOH`), puis le
libelle et le dossier.

## 3. Le classement, sur les 1187 PDF du coffre

| Classe | Nombre | Motif dominant |
|---|---:|---|
| `PIECE` | 780 | 731 servies par le portail, 31 emetteur tiers nomme, 13 chaine metier |
| `ARTEFACT` | 362 | **329 sont les sorties de notre propre outil** (`900_Systeme_Audit`) |
| `DERIVE` | 45 | scissions et sections d'une piece identifiee |
| sans signal | **0** | les cinq derniers tranches a la lecture |

Chaque ligne porte sa raison. Le detail est dans
`_classement_source.tsv`, a la racine de l'instance.

Les cinq tranches a la main: deux exemplaires de la **carte professionnelle de
CHAVISSIMMO delivree par la CCI** (piece d'un tiers), un formulaire de pouvoir
scanne, un plan de financement chiffre, et une note de controle des comptes qui
est de notre plume.

## 4. L'instance reconstruite

`instances/tilleul_pseudo_20260906`, 825 fichiers - 780 pieces et 45 derives -
819 Mo. Les 362 artefacts sont exclus.

Resultat de la chaine, compare a l'instance historique:

| | `tilleul_pseudo_reconstruite_20260904` | `tilleul_pseudo_20260906` |
|---|---:|---:|
| lignes au registre | 3447 | 825 |
| `Convocation_AG` | 151 | **12** |
| `PV_AG` | 15 | **10** |
| `A_CLASSER` | 2111 | 99 |
| `Devis` | 40 | 19 |

Le classement ne s'ameliore pas parce qu'il a change: **il n'a pas change**.
C'est l'entree qui a cesse de contenir 2436 sous-produits de notre propre
traitement.

`instances/tilleul_pseudo_test` a ete supprimee, comme demande.

## Reserve

Ce classement est un tri de provenance, pas un etalon de justesse. Il dit d'ou
vient chaque fichier, pas si son type documentaire est juste. Le seul etalon
etabli a la main reste `instances/tests_ux`.
