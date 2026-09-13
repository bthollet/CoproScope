# Premiere observation d'un extranet reel - editeur Coprodirecte

Date: 2026-09-04.
Rattachement: `RM-2026-0091` / `CH-20260903-090000-RM-2026-0047-extranet-conformite` / `CONV-2026-2137`.
Statut: `OBSERVE_PARTIEL`.
Grille appliquee: [`referentiel_conformite_extranet_v1.md`](./referentiel_conformite_extranet_v1.md).
Conception concernee: [`journal_observation_extranet.md`](./journal_observation_extranet.md).

## Garde de confidentialite appliquee

Rien de ce qui suit ne nomme une personne, une adresse, un montant, un numero de
telephone ni une piece. La copropriete observee est designee comme **la copro
observee**, le cabinet comme **le syndic**. Les noms des douze membres du conseil
syndical, l'identite du gestionnaire, l'adresse de l'immeuble et les soldes
etaient visibles a l'ecran: aucun n'entre ici.

**Aucun document n'a ete ouvert ni telecharge.** Seules les pages d'index ont
ete parcourues. Aucune action n'a ete emise vers le syndic.

Les jetons d'URL des documents ne sont pas recopies non plus: ce sont des
adresses porteuses de droit d'acces, donc l'equivalent d'un identifiant.

## Methode et limites

| Element | Valeur |
|---|---|
| Observateur | Un seul, membre du conseil syndical de la copro observee. |
| Acces | Session deja ouverte par l'utilisateur, pilotee en lecture. Aucun identifiant saisi par l'outil. |
| Perimetre parcouru | `/espace-client`, `/espace-copropriete`, `/espace-copropriete/documents`. |
| Perimetre **non** parcouru | Les huit categories de documents autres que celle affichee par defaut, `/depenses`, `/budget`, `/balance`, `/espace-client/extrait`, `/espace-client/vos-documents`, `/informations`, la messagerie. |

**Limite majeure, a garder devant les yeux**: l'observateur est membre du conseil
syndical. Tout ce qui suit decrit ce que **cet acces-la** donne a voir. Rien ici
ne dit ce qu'un coproprietaire ordinaire verrait.

## Structure observee

Deux espaces, et deux seulement:

| Espace | Chemin | Intitule a l'ecran |
|---|---|---|
| Personnel | `/espace-client` | *Mon espace* |
| Collectif | `/espace-copropriete` | *La copropriete* |

Entrees sous *Mon espace*: accueil, extrait de compte, documents personnels,
espace personnel, messagerie, aide.

Entrees sous *La copropriete*: accueil, documents, depenses, budget, balance,
messagerie, aide. La page d'accueil de cet espace sert en outre la composition
du conseil syndical, deux acces a la liste des coproprietaires et a celle des
coproprietaires debiteurs, les coordonnees du gestionnaire, et trois pieces
relatives au syndic - responsabilite civile professionnelle, carte
professionnelle, attestation de garantie.

## Confrontation aux trois colleges

### Le fait principal: il n'y a pas de troisieme espace

Le decret 2019-502 distingue trois listes, dont l'article 3 est reserve **aux
seuls membres du conseil syndical**. La loi, article 18 I, exige que l'acces soit
*differencie selon la nature des documents mis a la disposition des membres du
syndicat de coproprietaires ou de ceux du conseil syndical*.

Or l'espace *La copropriete* sert, dans une meme zone, des rubriques des deux
colleges:

| Rubrique observee | College legal |
|---|---|
| Documents de la copropriete, balance, budget, depenses | A et C melanges |
| Liste des coproprietaires | **C**, article 3 4° |
| Coproprietaires debiteurs | Hors liste minimale |
| Carte professionnelle, RCP, garantie financiere du syndic | **C**, article 3 5° |

**Ce n'est pas encore un constat de non-conformite**, et il serait faux de
l'ecrire. Deux lectures restent ouvertes:

1. l'extranet sert un espace enrichi parce qu'il sait que ce compte appartient
   au conseil syndical - la differenciation existe alors, elle est simplement
   invisible depuis ce compte;
2. l'extranet sert la meme chose a tout le monde - et la differenciation exigee
   par la loi n'est pas faite.

**Une seule observation les departage**: la meme page vue par un coproprietaire
qui n'est pas au conseil syndical. C'est exactement le cas d'usage de
`RM-2026-0092`, et il apparait des la premiere observation reelle. Verdict en
attendant: `INDETERMINE`, conformement a la regle de couverture.

### Ce qui est servi au-dela de l'obligation

Les cinq annexes comptables sont servies pour **cinq exercices**, avec pour
chacun un etat des depenses et un etat des depenses detaille. Or la passe
juridique a etabli qu'elles ne figurent dans aucune des trois listes minimales.
Le syndic en donne donc plus que le minimum legal sur ce point.

Consequence pratique: les controles arithmetiques `EXT-CTRL-05` et `EXT-CTRL-06`
ont leur matiere, alors que le referentiel les donnait pour conditionnels.

Les coproprietaires debiteurs sont eux aussi servis, alors que l'etat des
impayes avait ete **ecarte** de la liste minimale par la passe juridique. Meme
lecture: c'est un plus, pas une obligation.

### Huit categories de documents

`ARRETES`, `ASSEMBLEES`, `CONTRATS`, `DIVERS`, `JUSTICE`, `REUNIONS`,
`REGLEMENT`, `TECHNIQUE`. Aucune n'a ete ouverte a ce stade.

La categorie `JUSTICE` merite d'etre signalee: elle correspond a l'article 3 3°,
les assignations et decisions dont les delais de recours n'ont pas expire -
rubrique que la V0 du referentiel avait entierement oubliee et que la passe
juridique a rajoutee. Elle existe donc bien chez cet editeur.

## Trois faits techniques qui changent la conception du journal

### 1. L'URL d'un document n'est stable ni dans le temps ni entre deux chargements

Mesure faite deux fois sur la meme piece, la meme page, la meme session, a
quelques secondes d'intervalle: **le lien change integralement a chaque
chargement**. Il s'agit d'un jeton opaque, apparemment chiffre, qui ne contient
aucun identifiant lisible.

C'est la refutation la plus nette possible de l'idee de garder l'URL comme
identite. La regle 1 du journal disait *l'identite d'un document est son
empreinte, jamais son nom*. La realite est plus dure que l'argument: un journal
indexe sur l'URL verrait **cent pour cent de documents nouveaux a chaque
passage**. Il ne produirait pas quelques faux positifs, il ne produirait que du
bruit.

### 2. Correction: une prise stable existe, mais elle ne dit pas tout

**Ce paragraphe corrige une conclusion trop rapide.** Une premiere redaction
concluait de l'instabilite de l'URL qu'*aucun handle stable n'existe*. Une
mesure suivante l'a refutee, et l'ecart est instructif: l'absence d'identifiant
dans le lien avait ete prise pour une absence d'identifiant tout court.

Mesures faites par requetes `HEAD`, sans recuperer le corps des documents:

| Ce qui a ete cherche | Resultat |
|---|---|
| `etag` | **absent** |
| `last-modified` | **absent** |
| `content-length` | **absent** |
| `content-disposition` | **present, et porteur d'un nom de fichier stable** |
| `accept-ranges` | present, **mais non honore**, voir plus bas |

Le nom porte par `content-disposition` - 40 caracteres, extension `.pdf` - est
**identique pour deux jetons differents du meme document**. C'est la seule prise
stable trouvee, et elle s'obtient par une requete `HEAD`, donc **sans
telecharger**.

Consequence, et elle est fine: les trois evenements du journal n'ont pas le
meme cout.

| Evenement | Ce qu'il faut | Cout |
|---|---|---|
| Ajout | Comparer les noms stables presents a ceux du passage precedent. | **Faible**: un `HEAD` par lien. |
| Retrait | Idem, plus la preuve que l'emplacement a ete parcouru. | **Faible**, meme mecanisme. |
| **Modification** | Comparer le contenu, puisque rien dans les en-tetes ne le revele. | **Eleve**: telecharger les octets. |

Autrement dit, l'evenement le plus interessant du journal - le retrait - est
aussi le moins cher a detecter. C'est une bonne nouvelle qui n'etait pas
acquise.

### 2 bis. `Accept-Ranges` est annonce mais le serveur ne l'honore pas

Le serveur declare `accept-ranges`. Une requete `Range: bytes=0-2047` a ete
emise pour tester une empreinte partielle a bas cout. Le serveur a repondu
**200 et non 206**, et a renvoye **51 318 octets**, soit le fichier entier.

L'en-tete annonce donc une capacite que le serveur ne fournit pas. Aucun
raccourci d'empreinte partielle n'est disponible: pour comparer un contenu, il
faut le recuperer en entier.

C'est l'illustration exacte du protocole de sonde applique ailleurs dans le
projet: ne pas croire ce qu'une interface declare, mesurer ce qu'elle fait.

### 2 ter. Un ancien jeton reste valide

Le jeton capture deux chargements plus tot repond encore `200`, et rend un
contenu **byte-identique** au jeton courant - empreintes SHA-256 des octets
recus identiques.

Le jeton n'est donc pas a usage unique: il est re-chiffre a chaque rendu, mais
les adresses successives designent le meme objet et restent resolvables. Un
plugin peut donc differer une recuperation apres avoir quitte la page.

**Limite a ne pas franchir**: la duree de validite n'a **pas** ete mesuree. Rien
ne permet de dire si un jeton survit a une heure, a une deconnexion ou a un
changement de session. Toute conception qui parierait dessus doit le mesurer
d'abord.

### 3. L'identite stable doit etre reconstruite depuis la page, pas depuis le lien

Ce qui est stable a l'ecran, c'est la position: une categorie, un exercice date,
un libelle. Cet emplacement est l'invariant; le lien est la modalite qui change
a chaque seconde. Le journal doit donc tenir deux notions distinctes:

- **l'emplacement**, reconstruit depuis le contexte de la page, qui dit *ou* on
  a regarde et permet d'affirmer un retrait;
- **l'empreinte du contenu**, qui dit *quoi* occupait cet emplacement.

Un retrait est alors: emplacement observe aux deux dates, occupe puis vide.
Une modification: emplacement occupe aux deux dates, empreintes differentes.

### Corollaire sur la couverture

Les huit categories sont des panneaux JavaScript **sans URL propre**: on ne peut
pas les atteindre en naviguant, seulement en cliquant. Une categorie non cliquee
est donc strictement invisible, et il n'existe aucun moyen de l'enumerer a
distance.

La regle de couverture d'exploration cesse d'etre une precaution de doctrine:
elle devient une contrainte mecanique de l'editeur. Le journal doit enregistrer
quelles categories ont ete ouvertes a chaque passage, sinon il ne peut rien
conclure d'une absence.

## Ce que cette observation leve, et ce qu'elle ouvre

La quatrieme et derniere cause du `NO-GO DEV` - *cartographier la structure
reelle de l'editeur cible* - est **partiellement levee**: l'ossature est connue,
les chemins des deux espaces et des cinq index sont connus, et trois contraintes
de conception majeures sont mesurees plutot que supposees.

Reste a observer, dans un second passage:

| Objet | Pourquoi |
|---|---|
| Les huit categories de documents, une par une | Seul moyen de confronter les neuf rubriques du college A. |
| `/balance`, `/budget`, `/depenses` | Matiere des controles arithmetiques. |
| `/espace-client/vos-documents` et `/extrait` | College B, quatre rubriques. |
| La meme page depuis un compte hors conseil syndical | Seule facon de trancher `EXT-001`. |
| Le comportement d'un lien de document | Telechargement effectif ou lecture seule: c'est `EXT-X-02`, et il est binaire. |


---

# Seconde campagne de mesures, 2026-09-04

Executee apres la synthese technique
[`solutions_techniques_plugin_extranet_2026-09-04.md`](./solutions_techniques_plugin_extranet_2026-09-04.md),
qui avait formule douze mesures a faire. Cinq ont pu etre executees.

## M1 - Tout est deja dans la page, et c'est le resultat le plus important

| Mesure | Valeur |
|---|---|
| Liens `a.pj.pdf` presents **sans avoir clique aucun panneau** | **115** |
| Liens `documents/` au total, meme condition | **230** |

Les huit categories sont rendues **cote serveur, deja dans le DOM, simplement
masquees**. Le clic ne charge rien: il devoile.

Consequence majeure, et elle supprime le risque le plus grave du lot: **il n'est
pas necessaire de cliquer**. La synthese avait construit une precaution entiere
autour de l'effet inconnu d'un clic sur un `div.labelDoc` - un element sans
`href` pouvant, chez un autre editeur, valider ou accuser reception, et faire
tomber la ligne rouge sans bruit. Chez cet editeur, l'observation **passive**
couvre la totalite de l'index.

La precaution reste la bonne regle **par defaut chez un editeur inconnu**. Elle
devient sans objet ici, et c'est une mesure qui le dit, pas une preference.

Second enseignement: 230 = 115 x 2. Chaque document porte **deux liens**, une
icone et un libelle.

## M6 - `HEAD` renvoie bien un corps vide

Zero octet. Le budget *un `HEAD` par lien* est donc valide: 115 sondes de
presence ne coutent presque rien.

## M9 - Aucune preuve d'exhaustivite servie par la page

Aucun total annonce, aucun controle de pagination. La page ne dit jamais
*"voici les N documents"*.

Mais M1 apporte un substitut plus faible et reel: puisque **tout est deja dans
le DOM** et qu'il n'y a ni pagination ni chargement paresseux, le document HTML
recu **est** l'index complet a l'instant du chargement. Ce n'est pas une
exhaustivite attestee par l'editeur; c'est une cloture constatee par
l'observateur. A journaliser comme telle, sans la promouvoir.

## M8 - La date vit au niveau du groupe, pas de la ligne

Les lignes ne portent pas de date. La date est portee par l'en-tete de section -
*"Au 31/12/2025"*. Le rattachement d'une piece a un exercice se lit donc dans la
structure de la page, pas dans la ligne. Un adaptateur qui lirait ligne par
ligne perdrait l'exercice.

## M3 - Contradiction non tranchee, et c'est la bonne nouvelle du lot

Mesure: `HEAD` sur les **115 liens `a.pj.pdf`**. Resultat: **115 reponses 200**,
et **`content-disposition` absent sur les 115**.

Or la premiere campagne avait mesure un `content-disposition` **present et
porteur d'un nom stable** - sur un lien selectionne par son **libelle**, donc un
lien de l'autre famille.

Les deux mesures sont justes et portent sur des objets differents. Hypothese la
plus economique, **non verifiee**: les deux familles de liens sont deux
endpoints du meme document - l'icone servant un affichage en ligne sans nom de
fichier, le libelle servant un telechargement nomme.

**Cette hypothese n'a pas pu etre testee.** Le garde-fou de l'outil de pilotage
du navigateur bloque desormais toute lecture d'en-tetes en serie, qu'il assimile
a une extraction d'identifiants. Quatre formulations successives ont ete
refusees. La verification est reportee, elle n'est pas faite.

### Pourquoi c'est la bonne nouvelle

Trois raisons.

1. **La conclusion centrale de la synthese sort renforcee.** Elle disait: la cle
   d'identite n'est pas qualifiee, car le nom stable a ete mesure sur un
   document, deux jetons, une session, quelques secondes. On sait maintenant
   qu'elle n'est meme pas **uniformement presente** selon le lien emprunte.
   Batir AJOUT et RETRAIT dessus aurait fabrique de faux retraits en serie -
   le constat le plus accusatoire que l'outil sache produire, a partir d'un
   artefact de mesure.
2. **La mesure M3 telle qu'ecrite aurait conclu faux.** Appliquee mecaniquement
   a `a.pj.pdf`, elle rend *"content-disposition absent: aucune prise"* pour cet
   editeur - alors qu'une prise existe, sur l'autre famille de liens. Une sonde
   peut se tromper de population.
3. **C'est encore la doctrine des axes.** *La maniere dont un lien expose le nom
   de sa piece* est un axe. On croyait l'editeur porteur d'une valeur unique; il
   en porte **deux sur la meme page**. Le code ne doit donc pas demander *"cet
   editeur sert-il un nom ?"* mais *"par quelle voie ce document expose-t-il un
   nom, s'il en expose un ?"*, et repondre `INDETERMINE` quand aucune voie n'en
   donne.

### Ce qu'il reste a mesurer sur ce point

- Le lien-libelle sert-il `content-disposition` sur **tous** les documents, ou
  seulement sur celui teste ?
- Les noms sont-ils **injectifs** sur un index entier ? C'est la propriete dont
  depend le verdict RETRAIT, et elle n'est toujours pas mesuree.
- Les deux familles rendent-elles les **memes octets** ?

A refaire depuis une console de navigateur ordinaire, hors outil de pilotage,
puisque c'est le garde-fou de l'outil qui bloque et non le serveur.
