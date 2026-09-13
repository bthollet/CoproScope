# Journal d'observation de l'extranet - conception

Date: 2026-09-04.
Rattachement: `RM-2026-0091` / `CH-20260903-090000-RM-2026-0047-extranet-conformite` / `CONV-2026-2137`.
Statut: `CONCEPTION`, aucun code ecrit.
Grille de reference: [`referentiel_conformite_extranet_v1.md`](./referentiel_conformite_extranet_v1.md).

## Ce que Brice a demande

> *"Ce qui peut etre interessant c'est de tracer les diffs et telecharger ce qui
> est nouveau. Attention: sur les factures un voisin fait le suivi et il y a des
> ajouts/retraits/modifs de factures."*

Cette phrase deplace le lot. Le referentiel repond a *"le syndic publie-t-il ce
qu'il doit ?"*. Le journal repond a *"qu'est-ce qui a change, et quand ?"*.

La seconde question a une propriete que la premiere n'a pas: **elle produit une
preuve qu'aucun audit ponctuel ne peut produire**. Un audit est une photo. Un
document present en mars et absent en juin ne laisse aucune trace dans une
photo prise en juin.

## Le retrait est l'evenement le plus interessant, et le plus fragile

Trois evenements sont observables: ajout, modification, retrait. Ils n'ont pas
la meme valeur ni le meme cout de preuve.

| Evenement | Ce qu'il vaut | Ce qu'il coute a prouver |
|---|---|---|
| Ajout | Faible seul. Utile pour dater une mise en ligne et mesurer `EXT-X-03` et `EXT-T-01`. | Presque rien: la piece est la, on l'empreinte. |
| Modification | Elevee. Une piece qui change apres avoir ete presentee a l'assemblee est une question legitime. | Moyen: il faut l'empreinte **anterieure**, donc avoir empreinte ce qu'on n'avait pas force de telecharger. |
| **Retrait** | **La plus elevee.** Invisible a tout audit. | **Le plus eleve**, et c'est le piege du lot. |

Un retrait ne s'affirme que si **la page d'index qui enumere la categorie a ete
observee aux deux dates**. Sans cela, la piece n'a pas ete retiree: elle n'a pas
ete vue. C'est la regle de couverture d'exploration du referentiel, etendue au
temps, et elle est ici plus contraignante encore.

Consequence de conception, non negociable: chaque observation enregistre **ce
qui a ete parcouru**, pas seulement ce qui a ete trouve. Un journal qui ne note
que les pieces vues ne peut jamais conclure a une absence.

## Trois regles dures

### 1. L'identite d'un document est son empreinte, jamais son nom

Le nom de fichier, l'URL, la position dans une liste et le libelle affiche sont
tous des **degres de liberte**: ils changent a chaque refonte d'interface, et
d'un syndic a l'autre. Ce qui reste invariant le long de cet axe, c'est qu'un
document a un contenu, et qu'un contenu a une empreinte stable.

Coder l'identite sur le nom de fichier produirait deux fautes silencieuses:

- meme nom, contenu different, lu comme "inchange" - une modification manquee;
- contenu identique, nom nouveau, lu comme "ajout + retrait" - deux faux
  evenements pour un simple reuploadage.

**Epreuve d'acceptation**: si un troisieme syndic nomme ses fichiers autrement,
le journal se degrade-t-il proprement ? Avec l'empreinte, oui: il perd le
libelle, il garde l'identite. Avec le nom, non: il invente des evenements.

**Confirme par la mesure le 2026-09-04, et plus durement que l'argument.** Chez
l'editeur Coprodirecte, l'URL d'un document change integralement entre deux
chargements de la meme page, dans la meme session, a quelques secondes
d'intervalle. Un journal indexe sur l'URL ne produirait pas quelques faux
positifs: il verrait cent pour cent de documents nouveaux a chaque passage.

**Mais la regle demande une nuance, apportee par une mesure suivante.** Dire
*l'identite est l'empreinte* etait juste contre l'URL, et trop absolu: chez cet
editeur, l'en-tete `content-disposition` porte un nom **stable** entre deux
jetons du meme document. Il existe donc une prise intermediaire, moins forte
qu'une empreinte de contenu et beaucoup moins chere. La formulation exacte:

> L'identite d'un document est l'empreinte de son contenu. Un identifiant servi
> par l'editeur peut faire office de **prise provisoire** pour detecter une
> presence ou une absence, jamais pour affirmer qu'un contenu n'a pas change.

Ce que la mesure ajoute a la regle: l'empreinte dit *quoi*, mais elle ne dit pas
*ou*. Pour affirmer un retrait il faut aussi une notion d'**emplacement**,
reconstruite depuis le contexte de la page - categorie, exercice, libelle - et
non depuis le lien. Un retrait est un emplacement observe aux deux dates, occupe
puis vide.

### 2. Empreinter tout ce qui est vu, telecharger ce qui est nouveau ou change

Une modification ne se detecte que contre un etat anterieur. Si le plugin ne
garde que ce qu'il a telecharge, il est aveugle a tout ce qu'il a decide de ne
pas telecharger.

D'ou la separation:

| Geste | Portee | Cout |
|---|---|---|
| Empreinter | **Tout** ce qui est atteignable sans quitter la page. | Faible, et c'est ce qui rend le journal complet. |
| Telecharger | Ce qui est nouveau, ou dont l'empreinte a bouge. | Ce que Brice a demande, et le pont vers CoproScope. |

Limite honnete: sur un extranet ou l'empreinte exige de telecharger le fichier,
les deux gestes se confondent et le cout monte. A mesurer sur le cas reel avant
de trancher; ce n'est pas decidable depuis la doctrine.

### 3. Le journal enregistre un changement d'etat, jamais un auteur

Brice signale qu'**un voisin fait le suivi des factures**. Trois sources de
changement se melangent donc sur la meme categorie: le syndic, ce voisin, et
Brice lui-meme. L'extranet n'expose pas qui a agi.

Un journal qui ecrirait *"le syndic a supprime une facture"* produirait une
accusation qu'il ne peut pas soutenir. C'est exactement ce que l'arbitrage
`instrument de mesure` ecarte.

Formulation retenue, et elle est plus solide:

> Le 2026-03-12, cette piece etait presente a cet emplacement, empreinte `a1b2…`.
> Le 2026-06-04, la page d'index a ete parcourue et la piece n'y figurait plus.

Le fait est verifiable et date. L'explication reste ouverte, et c'est a
l'humain de la demander. Un conseil syndical qui pose cette question avec cette
precision est en position de force; le meme qui accuse est en position de
faute.

Corollaire, et il est devenu un argument pour la suite: le voisin ne partage
pas ses archives - arbitrage de Brice du 2026-09-04 - donc deux personnes
suivent aujourd'hui les memes factures sans rien de commun. Chacun a sa version
de ce qui a bouge, et rien ne les departage. C'est exactement ce que la
consolidation differee en `RM-2026-0092` viendra corriger.

## Le cas des factures, nommement

C'est la categorie que Brice designe comme mouvante, et c'est aussi celle qui
porte le plus d'enjeu comptable. Trois precautions particulieres:

1. **Une facture retiree n'est pas une facture annulee.** Elle peut avoir ete
   remplacee par une version corrigee, deplacee dans un autre exercice, ou
   retiree par erreur. Le journal constate; il ne qualifie pas.
2. **Le rapprochement facture -> ligne de depenses existe deja dans CoproScope**
   et vit en SQLite. Le journal ne doit pas creer un second magasin qui dirait
   autre chose sur les memes pieces.
3. **Une facture porte des donnees de tiers**: fournisseurs, et parfois des
   coproprietaires nommes. Les empreintes et les dates sont publiables; le
   contenu reste local.

## Ou ca s'ecrit

Dans le coffre SQLite local, par le journal d'evenements, conformement a
l'arbitrage du 2026-09-03. **Pas de nouveau registre CSV.**

Deux pieges deja payes ailleurs dans le projet, a ne pas repayer:

- une table ajoutee sans passer par le recorder est effacee au prochain
  `_reset_schema`, et la perte est differee donc invisible;
- une observation d'outil et une correction humaine ne se rangent pas ensemble.
  Une re-observation remplace ce que l'observation precedente avait produit, et
  rien d'autre.

La structure `object_links` convient au besoin: sa contrainte d'unicite porte
l'`event_id`, donc plusieurs assertions peuvent coexister sur la meme piece -
ce que le syndic publie, ce que le journal observe, ce qu'un humain confirme ou
conteste. Une colonne de registre ne sait pas faire cela.

## Ce que ca change pour le referentiel

Trois indicateurs du referentiel etaient declares *"mesurables seulement par
observation repetee"* et n'avaient aucun mecanisme derriere. Le journal est ce
mecanisme:

| Indicateur | Ce que le journal lui apporte |
|---|---|
| `EXT-X-03` actualisation dans les trois mois suivant l'AG des comptes | La date d'apparition de chaque piece, donc le delai reel. |
| `EXT-T-01` derniere AG des comptes -> actualisation | Idem, mesure et non presumee. |
| `EXT-T-02` demande du conseil syndical -> communication | Partiellement: le journal date **l'arrivee** du document. La date de la **demande** doit venir d'ailleurs, elle ne s'observe pas sur l'extranet. |

`EXT-T-02` reste donc incomplet, et c'est structurel: le delai d'un mois de
l'article 21 court a compter d'une demande ecrite. Tant que la demande n'est pas
enregistree quelque part, le journal constate une arrivee sans pouvoir dire si
elle est en retard.

## Ligne rouge

Reformulee apres echange avec Brice le 2026-09-04. La formulation initiale
etait *"lecture seule"*. Elle est remplacee, parce qu'elle protegeait la
mauvaise chose.

Un plugin s'execute dans la session deja authentifiee de l'utilisateur: le
navigateur ne distingue pas ses actions de celles de Brice. Il ne peut
quasiment rien modifier chez le syndic, mais il peut **parler au nom de Brice**.
C'est la le risque reel.

> **Le plugin agit sur la machine de l'utilisateur autant qu'il le faut.
> Tout ce qui sort vers le syndic passe par un clic humain.**

Ce qui est autorise sans clic: parcourir, empreinter, telecharger, journaliser,
alerter. Ce qui exige un clic humain a chaque fois: envoyer un message, deposer
un document, valider, voter, accepter des conditions.

Le cas qui motive la regle: la demande ecrite du conseil syndical declenche le
delai d'un mois de l'article 21, au terme duquel des penalites par jour de
retard s'imputent sur la remuneration du syndic. Un outil qui enverrait cette
demande seul engagerait Brice dans un rapport de force qu'il n'a pas choisi.
Le plugin prepare la demande; Brice l'envoie.

## Ce qui a ete tranche par Brice le 2026-09-04

| Question | Reponse | Ce qu'elle implique |
|---|---|---|
| Le voisin qui suit les factures partage-t-il le journal ? | **Non.** Il garde ses archives et ne les partage pas. | Le journal est **personnel** dans cette version. Pas de format d'echange, pas de fusion, pas de compte partage. |
| Que faire d'un retrait detecte ? | **Alerter.** | L'outil signale et date. Il ne prepare aucune demande, n'ecrit aucun courrier, ne declenche aucun delai. Brice decide de la suite. |
| Consolider les historiques entre coproprietaires ? | **Plus tard**, quand la synchronisation sera en place. | Inscrit au gouvernail, `RM-2026-0092`, adosse a `RM-2026-0033`. Hors perimetre de ce lot. |

### Ce que "alerter" veut dire, et ce que ca ne coute pas

Alerter est le geste minimal, et c'est le bon: il tient entierement du cote
`mesure`. Mais il ne fait perdre aucune capacite. Une alerte qui porte la date,
l'emplacement et l'empreinte anterieure **est deja la matiere d'une demande
ecrite au titre de l'article 21**. Brice l'ecrit s'il le decide; le delai d'un
mois court a partir de son geste a lui, pas de celui de l'outil.

Un point de conception a ne pas rater: une alerte qui se declenche a chaque
remaniement d'interface ne sera plus lue au bout de deux semaines. Le classement
n'est donc pas cosmetique.

| Rang | Evenement | Pourquoi ce rang |
|---|---|---|
| 1 | Retrait d'une piece vue precedemment | Irreversible du point de vue de l'observateur, et invisible autrement. |
| 2 | Modification d'une piece deja presentee a l'assemblee | Change la matiere d'une decision deja prise. |
| 3 | Modification d'une piece courante | A verifier, sans urgence. |
| 4 | Ajout | En general une bonne nouvelle. N'alerte que s'il comble une rubrique attendue, ou s'il arrive hors du delai de trois mois de `EXT-X-03`. |

## Consolidation entre coproprietaires - `RM-2026-0092`, plus tard

Demande de Brice du 2026-09-04, explicitement differee jusqu'a la
synchronisation. Elle est notee ici parce qu'elle **change la valeur de tout le
dispositif**, et qu'une conception qui l'ignore aujourd'hui se fermera la porte.

**Ce qu'elle resout, et que rien d'autre ne resout.** La faiblesse structurelle
du journal est sa couverture: il ne voit que ce que son porteur ouvre. Deux
observateurs independants couvrent plus de pages d'index, plus souvent, et
surtout: si deux personnes detiennent l'empreinte de la meme piece a la meme
date et qu'elle disparait, le retrait cesse d'etre une affirmation isolee. Un
journal seul est une allegation. Deux journaux concordants sont une preuve.

**Ce qui rend la chose faisable sans probleme de confidentialite.** La
consolidation n'a pas besoin des documents. Elle a besoin d'empreintes, de
dates, et du perimetre parcouru. Or les factures portent des donnees de tiers,
et la liste de l'article 32 porte l'etat civil de tous les coproprietaires:
c'est precisement ce qu'il ne faut pas faire circuler. Echanger des empreintes
prouve *"nous avons vu la meme chose"* sans que personne n'envoie quoi que ce
soit.

**Un effet de bord qui vaut d'etre cherche.** Si deux journaux divergent - une
piece vue par l'un, absente chez l'autre au meme moment - ce n'est pas une
erreur a corriger, c'est un constat: l'extranet ne sert pas la meme chose a
tout le monde. Selon la rubrique, cela peut etre normal, ou etre exactement le
manquement que le referentiel cherche.

**Ce que ca impose des aujourd'hui**, et c'est peu: que l'empreinte soit
calculee sur le contenu du document et rien d'autre - pas sur le nom, pas sur la
date de telechargement, pas sur un identifiant de compte. Une empreinte qui
depend du poste qui l'a calculee n'est comparable avec personne. C'est deja la
regle 1 ci-dessus, pour une seconde raison.

## Ce qui reste a trancher

| Question | Etat |
|---|---|
| Empreinter sans telecharger est-il possible sur l'extranet cible ? | **Tranchee le 2026-09-04, et la reponse est en deux temps: oui pour l'identite, non pour le contenu.** L'URL change a chaque chargement, mais l'en-tete `content-disposition` porte un nom de fichier **stable entre deux jetons du meme document**, obtenable par une requete `HEAD`. Donc **ajout et retrait se detectent a bas cout**, et seule la **modification** exige de recuperer les octets, faute d'`etag`, de `last-modified` et de `content-length`. `accept-ranges` est annonce mais **non honore** - une requete partielle rend 200 et le fichier entier - donc aucun raccourci d'empreinte partielle. Voir [`observation_extranet_coprodirecte_2026-09-04.md`](./observation_extranet_coprodirecte_2026-09-04.md). |
| A quelle frequence observer ? | Ouverte, et devenue plus couteuse: puisque empreinter revient a telecharger, la frequence se paie en volume. A calibrer sur le rythme reel de la copropriete. |
| Que surveille-t-on en CONTENU, tout ou un sous-ensemble ? | **Nouvelle**, et mieux cernee qu'annonce: la surveillance de **presence** est bon marche pour tout le stock; seule la surveillance de **modification** impose de rapatrier. L'arbitrage ne porte donc plus sur ce qu'on observe, mais sur ce dont on veut detecter les retouches. |
| Combien de temps un jeton reste-t-il valide ? | **Ouverte, et volontairement non conclue.** Un jeton d'il y a deux chargements repond encore 200 et rend un contenu identique, donc il n'est pas a usage unique. La duree n'a pas ete mesuree: rien ne dit s'il survit a une heure, a une deconnexion ou a un changement de session. Une conception qui differe une recuperation doit le mesurer avant. |

Aucun code applicatif n'a ete ecrit. Aucune page d'extranet n'a ete observee a
ce jour: la session authentifiee n'a pas pu etre atteinte le 2026-09-04.
