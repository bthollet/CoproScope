# Observateur d'extranet

Extension de navigateur, version 0.4.0. Rattachement: `RM-2026-0091`. Son code
vit dans [`clients/extension-navigateur/`](../../clients/extension-navigateur/manifest.json);
cette note en etait le README.

Elle regarde l'extranet de votre syndic **avec vos yeux**: vos droits, votre
session, les pages que vous ouvrez vous-meme. Elle note ce qu'elle voit, elle le
date, et elle vous dit ce qui a bouge depuis la derniere fois.

C'est ce qu'un audit ponctuel ne sait pas faire: un audit est une photo, et une
piece presente en mars puis absente en juin ne laisse aucune trace dans une
photo prise en juin.

## Ce qu'elle fait

**Elle compte ce qui manque, obligation par obligation.** Le referentiel de l'extension
recense dix-huit pieces qu'un syndic professionnel met en ligne: neuf au titre de
l'article 1er du decret 2019-502, quatre de son article 2, quatre de son article 3,
et une au titre de l'article 3 de la loi du 2 janvier 1970. Certaines ne sont dues
que sous condition (un fonds de travaux, un compte bancaire separe). Chaque
fondement porte sa version et sa date de lecture dans `referentiel.js`. Votre
syndic, lui, les range comme il veut: chez celui qui a ete mesure, une seule
rubrique *Contrats* porte quatre obligations differentes, et les releves du
compte bancaire separe sont ranges dans *Documents divers*. Vous indiquez une
fois ou chaque obligation est servie chez vous; l'outil compte ensuite seul.

**Elle surveille en continu.** Une minuterie verifie regulierement que
l'extranet est encore visible, meme sans onglet ouvert - donc pendant vos
vacances, quand le silence compte le plus.

**Elle pose un bandeau dans la page** quand il y a quelque chose a dire, et elle
se tait quand il n'y en a pas.

**Elle produit deux fichiers.** Un journal, qui reste chez vous. Un export
sans libelle ni nom de fichier en clair, que vous pouvez transmettre a un voisin
pour recouper vos observations (voir plus bas ce qu'il transporte).

## Ce qu'elle ne fait pas, et ne fera pas

La regle du chantier, ecrite une fois pour toutes:

> Le module agit sur votre machine autant qu'il le faut. Tout ce qui sort vers
> le syndic passe par un clic humain.

- **Elle n'ecrit rien vers votre syndic.** Pas de message, pas de vote, pas de
  clic automatise, pas de formulaire rempli. Un test le verifie a chaque
  passage sur le script qui lit les pages (`lecteur.js`): il n'y trouve ni
  `form.submit`, ni `.click()`. Les autres scripts ne sont pas couverts par ce
  test.
- **Elle ne conclut pas.** Elle dit *servi en apparence*, jamais *conforme*.
  Une rubrique peut porter le bon nombre de pieces sans que ce soient les
  bonnes: une attestation d'assurance perimee, un projet de contrat au lieu du
  contrat signe, un extrait au lieu du proces-verbal complet. Trancher demande
  de **lire** les pieces, ce que l'observation ne fait pas.
- **Elle n'accuse personne.** Le journal enregistre un changement d'etat, jamais
  un auteur. Trois causes se melangent sur un extranet - le syndic, l'editeur du
  logiciel, le temps - et la page ne dit pas laquelle a agi.
- **Elle ne lit jamais la liste des coproprietaires.** Cette piece porte l'etat
  civil, le domicile et l'adresse electronique de tout le monde. L'outil
  constate qu'elle est presente ou absente, et s'arrete la.
- **Elle ne devine rien.** Une rubrique que vous n'avez pas ouverte est notee
  *non parcourue*, jamais *vide*. La difference est ce qui evite, plus tard, de
  reprocher a votre syndic une disparition qui n'a pas eu lieu.

## Installation

1. ouvrir `chrome://extensions` (ou `edge://extensions`);
2. activer le **mode developpeur**;
3. **Charger l'extension non empaquetee**, et designer le dossier
   `clients/extension-navigateur` du depot;
4. se connecter a l'extranet normalement, puis cliquer sur l'icone.

Elle ne demande que trois autorisations: `storage` pour garder vos releves sur
votre machine, `downloads` pour vous rendre les fichiers, `alarms` pour la
minuterie. Elle ne lit qu'**un seul domaine, ecrit dans son manifeste**: celui
de l'editeur d'extranet sur lequel elle a ete mise au point. Chez un autre
editeur, il faut modifier le manifeste.

## La premiere fois

Tant que vous n'avez rien releve, la fenetre dit *aucun releve enregistre*.
Ouvrez une page de votre extranet et cliquez sur **Relever maintenant**.

Le panneau *Ce que le decret exige* affiche alors **dix-huit obligations** et
cette phrase: *je ne sais pas encore ou votre syndic les range*. C'est normal,
et c'est voulu: aucune page d'extranet ne cite le decret. Affirmer un manque
sans le savoir serait pire que se taire.

Pour chaque obligation, indiquez la ou les rubriques qui la servent chez vous.
Vos reponses sont gardees au fur et a mesure: vous pouvez fermer la fenetre
sans rien perdre. Vous pouvez aussi indiquer combien
de pieces vous savez devoir exister - par exemple 24 actes au reglement de
copropriete. Personne d'autre que vous ne le sait.

Laissez vide ce que vous ignorez: mieux vaut aucun chiffre qu'un chiffre
invente. Certains nombres sont deja remplis parce que le texte les fixe - trois
proces-verbaux d'assemblee, par exemple - et ceux-la ne se saisissent pas.

Quand une rubrique sert **plusieurs** obligations, l'outil affiche le compte
mais refuse de le repartir: douze pieces dans *Contrats* ne disent pas combien
sont des assurances. Un chiffre faux se cite, et nuit plus qu'une absence de
chiffre.

## La surveillance continue

L'interrupteur *Surveillance continue* declenche deux choses.

**A chaque visite**, au plus une fois par intervalle, l'outil releve la page que
vous ouvrez et la compare a la precedente.

**Sans onglet**, la minuterie verifie que l'extranet repond encore et qu'il vous
sert bien vos pages. Elle ne releve pas - un service worker n'a pas de moteur de
rendu - mais elle repond a la question qui compte quand vous n'etes pas la:
*est-ce que je vois encore ?*

L'ecran affiche donc **deux dates**: la derniere tentative et le dernier succes.
S'ils s'ecartent, votre session a expire et la surveillance ne voit plus rien.
Un ecran qui ne montrerait que le dernier succes laisserait croire que rien n'a
change, alors que plus rien n'est observe depuis trois semaines.

Un incident isole ne declenche pas d'alerte. Au-dela de deux echecs d'affilee,
ce n'est plus un incident, c'est un etat - et l'icone le dit.

## Effacer ce que le plugin a garde

Le plugin conserve sur votre machine les douze derniers releves de chaque
espace. Si vous avez releve une page **avant** de lui dire quelles rubriques ne
doivent jamais etre lues, ces releves en portent encore le contenu.

Le volet *Effacer ce que le plugin a garde* supprime les releves, l'historique
et l'etat de la surveillance. Vos rattachements et vos attendus sont conserves:
vous n'aurez pas a tout redeclarer. La commande demande une confirmation, parce
qu'il n'y a pas de corbeille.

## Les deux fichiers, et lequel circule

| Fichier | Contenu | Usage |
|---|---|---|
| `...-journal.json` | libelles, noms de fichiers, rubriques, dates | **reste chez vous** |
| `...-export.json` | empreintes (pieces, rubriques), dates, couverture, chemin des pages, editeur, nom d'observateur | **se transmet** |

L'export ne contient **aucun libelle, aucun nom de fichier, aucun montant** en
clair. Il transporte en revanche, lisibles, **l'adresse des pages relevees** (le
chemin, sans le domaine), **le nom de l'editeur d'extranet** et **le nom
d'observateur que vous avez saisi**: si ce
chemin porte un identifiant de votre copropriete, l'export le transporte aussi.
Ce n'est pas de la prudence excessive: un extranet de copropriete publie la liste
de tous les coproprietaires avec leur etat civil, et un fichier qui circule
finit toujours quelque part.

### Le secret de la copropriete

Pour produire un export, il faut un **secret partage** entre les voisins qui se
recoupent, et par eux seuls. Choisissez-le une fois, ensemble.

Sans lui, les empreintes seraient un **oracle**: quiconque obtiendrait le
fichier pourrait deviner ce qu'il contient en testant des intitules plausibles -
il y en a peu, et l'essai tient sur un ordinateur portable.

Le secret ne s'ecrit nulle part: ni dans l'export, ni dans le stockage du
plugin. Seule son **empreinte** est gardee, pour pouvoir vous dire *ce n'est pas
le secret de vos exports precedents* au lieu de vous laisser decouvrir un zero
de concordance et le lire comme un desaccord avec votre voisin.

**Ce secret n'est pas une cle produite par CoproScope.** Celles-la sont propres
a votre coffre, et servent au contraire a ce que deux voisins ne produisent
jamais la meme valeur pour la meme personne. Les deux poursuivent des buts
opposes, et l'outil refuse activement de les confondre.

Changer de secret rend tout l'historique anterieur incomparable.

## L'etage des noms de fichiers

Le module releve deux noms pour chaque piece, et ils ne disent pas la meme
chose.

Le **libelle affiche** est ecrit pour l'oeil et se repete volontiers: sur
l'index mesure le 4 septembre 2026, 115 pieces ne portaient que 83 intitules
distincts, et une rubrique entiere alignait 40 pieces sous 8 intitules.

Le **nom du fichier**, demande au serveur sans le telecharger, s'est revele
propre a chaque piece: 115 noms pour 115 pieces.

C'est donc une seconde mesure, independante de la premiere. Elle sert a
**reconnaitre une piece renommee** au lieu de croire qu'une a disparu et qu'une
autre est apparue. Le journal affiche la sante de cette mesure a chaque passage
- combien de noms recuperes, combien de doublons - parce qu'une degradation de
ces chiffres se lit mieux ici que plus tard, sur un constat faux.

Vous pouvez decocher ce releve: il coute une requete par piece.

## Une ligne de code inerte, et pourquoi elle est la

`fond.js` contient une fonction qui enverrait un releve vers un CoproScope local
(`127.0.0.1`). **Elle ne s'execute jamais**: la permission d'atteindre cette
adresse a ete retiree du manifeste, aucune commande ne l'appelle, et un test
verifie a chaque passage qu'elle reste sans emetteur.

Elle est conservee parce qu'elle est juste et qu'elle sera rebranchee telle
quelle le jour ou l'integration a CoproScope sera decidee. Le dire ici vaut
mieux que de laisser quelqu'un la decouvrir en lisant le code et se demander ce
qu'elle fait.

## Ce qui reste a faire

- **Le releve complet sans onglet.** La minuterie verifie la connexion, elle ne
  releve pas. Le faire demande un document hors ecran ou un onglet de fond: une
  permission de plus, et un arbitrage.
- **La lecture des pieces**, seule facon de passer de *servi en apparence* a
  *conforme*. C'est le role de CoproScope, pas du plugin.
- **Comparer deux journaux a plusieurs.** Deux journaux concordants valent mieux
  qu'un journal seul, mais la consolidation entre voisins reste a construire.
- **Un second editeur.** Les rubriques connues sont celles d'un seul syndic.
  Chez un autre, le module declarera les rubriques introuvables *non parcourues*
  et les dix-huit obligations *a rattacher*: il se degrade au lieu d'inventer.
- **La stabilite des reperes dans le temps** n'est pas encore mesuree. C'est
  l'objet du prochain releve, a quelques jours d'intervalle.

## Notes liées

- [Carte des notes](carte.md)
- [Confidentialité](confidentialite.md)
- [Pièces manquantes et demandes au syndic](fonction-pieces-et-demandes.md)
- [Architecture](architecture.md)
