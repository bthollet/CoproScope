# Revue Brice des 57 captures - 2026-09-07

Source: enregistrement vocal de 21,2 minutes, fait le 2026-09-07 a 22:43 juste
apres la livraison des 57 captures. Transcrit en local le 2026-09-08
(`large-v3-turbo`, francais, filtre VAD), 144 segments, **zero segment a faible
confiance**. L'audio reste hors depot; la transcription horodatee vit dans le
scratchpad de session.

Les horodatages `[mm:ss]` renvoient a l'enregistrement. Les captures sont
designees comme Brice les designe: par jeu et par rang de livraison.

**Nature de cette revue: PRODUIT et UX.** Brice n'aborde a aucun moment la
question de la publication sur GitHub ni celle des donnees personnelles. Cette
revue ne vaut donc pas arbitrage sur le tri de confidentialite, qui reste
ouvert et documente ailleurs.

## 1. Defauts bloquants

| # | Constat | Horodatage | Nature |
|---|---|---|---|
| B1 | **Trois captures montrent une page blanche** (5, 6, 7 sur 12 du premier jeu). « Donc ca, c'est pas bon. » | `[00:58]` | Ecran vide |
| B2 | **Les accents manquent dans l'interface.** Brice suppose un choix delibere pour eviter les problemes d'encodage, et tranche: « dans les pages publiques, c'est pas bon. » | `[02:58]` | Vocabulaire / rendu |
| B3 | **Le vote des comptes est range dans les marches.** « Ca suffit, ca. Il ne peut pas etre dans les marches. On ne peut pas dire que c'est au-dessus du seuil. Il faut le sortir, c'est a part. » | `[05:45]` | Modele metier |
| B4 | **« Divergence entre deux vues » ressort a l'utilisateur.** « Ce n'est pas possible. Ou alors vraiment sous forme de message d'erreur, que l'instance est cassee, il faut la refaire. » | `[12:08]` | Contrat d'affichage |
| B5 | **Le nombre de bulles est variable** d'une capture a l'autre. « Ce que je n'avais pas repere. » | `[02:21]` | Coherence |

B3 et B4 sont des defauts de fond. B4 rejoint directement le constat C095 de
`RM-2026-0086`: le desaccord entre deux sources n'a pas de sortie concue, donc
il fuit dans l'ecran au lieu d'etre traite.

## 2. Semiotique et code couleur

Brice donne une grille complete, la voici telle qu'il l'enonce.

| Situation | Couleur demandee | Horodatage |
|---|---|---|
| Marche paye qu'aucune decision ne fonde | **Rouge**, avec un pictogramme d'alerte | `[03:37]` |
| Decision d'urgence dont la ratification manque | **Rouge** | `[03:51]` |
| Resolutions que l'assemblee n'a pas votees | **Rouge**, plus une infobulle qui propose des suites | `[05:13]` |
| Absence d'avis du conseil syndical | **Orange** | `[04:02]` |
| Seuils a valider | Orange, « peut-etre a mettre en rouge » | `[04:08]`, `[04:17]` |
| Decision sans montant | **Orange** | `[04:19]` |
| Depense urgente sans avis rattache | **Gris « non concerne »**, plus un petit warning rouge et une infobulle au survol: « aucun avis du conseil syndical si la depense est confirmee urgente » | `[10:30]` |

Deux critiques du code couleur existant:

- les etapes 1 et 2 portent **la meme mise en forme que l'urgence**, donc on ne
  comprend pas que ce sont les etapes de la verification (`[07:20]`);
- « le code couleur, je ne comprends pas du tout son sens » (`[07:34]`).

## 3. Interactions manquantes

- **Cliquer sur « urgence declaree par le syndic a confirmer »** et pouvoir y
  noter quelque chose, par exemple « mail de X au syndic a telle heure, tel
  jour » (`[06:08]`). C'est une demande d'ecriture humaine sur la ligne, et elle
  rejoint le constat C083: l'ecran promet une conclusion qu'aucune route
  n'ecrit.
- **Cliquer sur une facture ouvre le lecteur PDF sur cette facture**, idem pour
  la preuve d'execution (`[08:17]`).

## 4. Mise en page

- Format PC: **equilibrer les deux lignes** de la synthese et ajouter le code
  couleur (`[01:21]`).
- **L'exercice doit devenir un menu deroulant** pour pouvoir choisir (`[01:34]`).
- Format mobile « un peu ecrase » (`[00:31]`).
- **Les seuils prennent trop de hauteur.** Ils doivent tenir **sur une ligne en
  mode ordinateur**, sous forme de **pastille** et en plus petit: « au-dessus de
  1 000 euros, avis du conseil syndical obligatoire », « au-dessus de tel
  montant, mise en concurrence obligatoire » (`[13:01]`, `[13:24]`).
- Les cases « avis du conseil syndical » et « mise en concurrence non exigee »
  sont rangees dans *ce qui la fonde*; elles doivent aller **dans la colonne des
  seuils** (`[09:21]`).

## 5. Vocabulaire

- « Decisions au coffre »: « je pense que ca va pas parler a tout le monde »
  (`[01:54]`).
- « Conclu »: « c'est le mot conclu qui est peut-etre un peu bizarre »
  (`[17:09]`).

## 6. Point de droit a trancher

`[07:47]` - « L'avis du conseil syndical, il est **facultatif pour les
travaux**. Verifiez, mais il me semble que meme si on est au-dessus du seuil. »

Formulation explicitement donnee comme a verifier, pas comme acquise. A
trancher sur la source, comme C081, et non de memoire.

## 7. Metier: le budget previsionnel est un cas particulier

`[19:26]` a `[20:01]`. Le champ « ce qui la fonde, une decision peut en fonder
une autre » n'est « vraiment pas du tout clair ». Brice comprend en cours de
lecture qu'il s'agit de **rattacher le budget previsionnel de l'annee
precedente**, et tranche: il faut **prevoir un cas specifique** pour le budget
previsionnel et la validation du budget de l'annee d'avant, puis **chercher
s'il existe d'autres decisions dans ce cas** - une decision de l'annee d'avant
qui en fonde une de l'annee courante.

## 8. Arbitrage rendu

`[20:43]` - Sur l'ambiguite entre deux resolutions du conseil syndical portant
un seuil de consultation: il est interessant de pouvoir valider quand
l'ambiguite est reelle, **mais en l'occurrence c'est le plus recent qui
compte**.

C'est une regle de decision, pas un avis. Elle sert directement `RM-2026-0072`.

## 9. Coherence d'ensemble des captures

Remarque qui revient quatre fois et qui porte sur le corpus lui-meme, pas sur
un ecran:

- « Je ne comprends pas bien tes captures, comment c'est cense fonctionner,
  est-ce que c'est des propositions differentes ? » (`[11:12]`)
- « Ca ne correspond pas a ta mise en page de tout a l'heure » (`[11:58]`)
- « Je pense que je ne les comprends pas bien, tes propositions de capture »
  (`[12:01]`)
- « Il y a une coherence interne a retravailler » (`[16:19]`)

Les captures ne se lisent pas comme un jeu coherent de propositions. Elles
melangent des etats successifs d'un meme ecran et des variantes concurrentes,
sans que rien ne dise lequel est quoi.

## 10. Ce que Brice retient de positif

- La synthese en un texte: « pas mal » (`[01:21]`).
- « Avis du conseil syndical non exige »: bonne idee, mais mal placee (`[09:15]`).
- La proposition graphique sur « decision et marche de l'exercice »: « elle me
  parait pas mal » (`[11:24]`).
- L'edition du montant: « pas mal » (`[17:24]`).
- Le rattachement: « ok » (`[20:18]`).
- « La proposition est interessante », meme si le chemin qui y mene n'est pas
  evident (`[15:22]`).

## Ce que cette revue ne dit pas

Elle ne se prononce **ni sur la publication sur GitHub, ni sur les donnees
personnelles**. Le tri de confidentialite des memes captures reste ouvert, et
un defaut structurel y a ete mesure depuis: l'ecran affiche « copropriete de
demonstration » sur un jeu de donnees que son propre fichier source declare
reel. Voir la trace `LE_LABEL_DEMONSTRATION_EST_FAUX_ET_IL_DESARME_LE_RELECTEUR`
dans `docs/presence_agents.md`.
