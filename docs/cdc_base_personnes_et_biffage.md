# Cahier des charges - base des personnes et moteur de biffage

Date de creation: 2026-09-02.
Origine: dictee Brice du 2026-09-02, consolidee.
Statut: **cahier des charges mis de cote**. Non implemente, hors du lot
gouvernance en cours. A reprendre quand la chaine de decision sera stabilisee.

Complete [`confidentialite_et_biffage.md`](./confidentialite_et_biffage.md), qui
decrit l'existant et n'est pas remplace.

## 1. Ce qui existe deja

A ne pas reconstruire.

| Brique | Etat |
|---|---|
| 17 regles de detection dans `core/privacy.py` | en production |
| Screening des documents, registre enrichi, rapport | en production |
| File de revue humaine, file de biffage | en production |
| Caviardage reel texte / PDF / DOCX | en production - `apply_redactions` efface aussi les pixels |
| Table de correspondance tracee | en production |
| Alias par categorie (`PERSONNE-1`, `EMAIL-2`, ...) | en production |

Categories couvertes: `EMAIL`, `PHONE`, `IBAN`, `SIRET`, `LOT`,
`ACCOUNT_INDIVIDUAL`, `IMPAID`, `CONTENTIOUS`, `HEALTH` (article 9 RGPD),
`REVENUE`, `SECURITY_SECRET`, `SECURITY`, `CONFIDENTIAL`, `NEGOTIATION`,
`IP_PLAN`, `PERSON_NAME`.

## 2. Le manque central

**L'alias est attache a une valeur, pas a une entite.**

La table de correspondance porte `doc_id`, `category`, `original_value`, `alias`.
L'allocation se fait par valeur rencontree. Consequences:

- deux graphies d'une meme personne recoivent deux alias distincts;
- rien ne relie un alias a des tantiemes, a un lot, a un role;
- on ne peut pas repondre a "toutes les pieces ou cette personne apparait";
- un agent qui lit le texte caviarde voit `PERSONNE-7` et `PERSONNE-23` sans
  savoir qu'il s'agit du meme copropriétaire.

## 3. Ce qui est demande

### 3.1 Une base des personnes physiques et morales

Une entite = une ligne stable, avec un identifiant derive d'un **sel** propre a
l'instance. Le sel ne quitte jamais l'instance; il permet qu'un meme alias
designe la meme personne d'un document a l'autre sans exposer son identite.

Deux populations, d'importance inegale:

**Les coproprietaires - prioritaires.** Parce qu'ils portent le lien aux
**tantiemes**, donc aux cles de repartition, aux majorites et aux quotes-parts.
Sans ce lien, aucun controle de majorite ni de repartition n'est possible.

**Les autres personnes** - syndic, fournisseurs, prestataires, avocats,
conseils, tiers. Moins structurantes, mais elles doivent exister pour que la
detection soit complete et pour distinguer une personne morale d'une personne
physique.

### 3.2 Le decalage temporel, et c'est la vraie difficulte

Le fichier des coproprietaires **n'est pas aligne** sur l'etat de la
copropriete a la date de l'assemblee traitee. Un PV peut donc nommer:

- un coproprietaire qui n'est pas encore dans la base (acquisition recente);
- un ancien coproprietaire qui n'y est plus (vente);
- un **representant** votant pour un autre, qui n'est pas lui-meme
  coproprietaire.

La base doit donc etre **datee**, et la detection doit tolerer l'inconnu: une
personne detectee et non rattachee est un cas normal, pas une erreur. Elle recoit
un alias provisoire et entre dans une file de rattachement humain.

Ne jamais rejeter une detection au motif qu'elle n'est pas dans la base. Ne
jamais rattacher automatiquement sur une ressemblance de nom.

### 3.3 Le moteur de biffage lie au sel

Quand le moteur detecte une donnee, il applique l'alias **de l'entite**, pas un
numero de rencontre. Le meme copropriétaire porte le meme alias dans tout le
corpus.

Finalite a garder en tete, et elle change les priorites: **la couche texte
caviardee est produite pour que des agents IA tournent dessus.** Le livrable
n'est pas d'abord un PDF diffusable a un tiers - l'outil est destine aux
coproprietaires eux-memes, qui detiennent deja les pieces. Un alias stable rend
le texte caviarde exploitable par un modele; un alias instable le rend
inutilisable.

Corollaire mesure le 2026-09-02: un document sans couche texte ne produit pas de
donnees non masquees, il ne produit **rien**. C'est un angle mort, pas une fuite.
L'ajout systematique d'une couche texte a l'ingestion le supprime.

## 4. Strategie de detection - etat de la reflexion

**Ce qui est facile**, et deja fait: adresses electroniques, telephones, IBAN,
SIRET. Precaution deja prise sur les telephones - le motif exige un `0` ou `+33`
initial suivi de quatre groupes de deux chiffres, ce qui evite de confondre avec
un montant.

**Ce qui est difficile**: les noms. La regle actuelle `PERSON_NAME` n'attrape que
les noms precedes d'une civilite (`M.`, `Mme`, `Monsieur`, `Madame`). Un
coproprietaire nomme sans civilite passe au travers. C'est le point ou la base des
personnes apporte le plus: elle fournit une liste de noms a chercher, au lieu de
deviner.

**Ce qui depend du contexte**: la meme donnee n'a pas le meme statut selon le
document. Un nom d'entreprise sur un devis est une information de mise en
concurrence, utile et legitime; le meme nom ailleurs peut relever du secret des
affaires. Il faut donc des **regles par type de document**, pas une politique
unique.

**Non tranche a ce jour**: la strategie generale de detection des noms hors
civilite. Reconnaissance d'entites nommees locale, appariement sur la base,
dictionnaire de prenoms, ou combinaison. A instruire.

## 4 bis. Critique des regles existantes - arbitrage Brice du 2026-09-02

**Principe directeur, et il commande le reste: une donnee n'est confidentielle
que si elle est rattachee a une personne.** Detecter un sujet de sante par un
simple traitement local est impossible: la regle `HEALTH` attrape le mot
`sante`, pas une information de sante. Dans un PV de copropriete, `impayes`,
`recouvrement`, `procedure` ou `sante` apparaissent en permanence dans des
contextes generiques - un point d'ordre du jour, une ligne de budget - sans
designer personne.

Ces regles produisent donc du bruit sans proteger quoi que ce soit. Elles font
partie de **ce qui a ete construit en trop** et sont a deconstruire.

| Regle | Arbitrage |
|---|---|
| `EMAIL`, `PHONE`, `IBAN`, `SIRET` | garder - detectables localement et fiables |
| `PERSON_NAME` | garder, et renforcer par la base des personnes |
| `CONTENTIOUS` | **garder, mais anonymiser** - le contenu contentieux reste utile, ce sont les personnes qui doivent disparaitre |
| `NEGOTIATION` | garder si elle porte sur des noms d'entreprises; sans nom rattache, sans objet |
| `IP_PLAN` | a revoir - vaut pour un plan joint, pas pour le mot `architecte` dans une phrase |
| `HEALTH`, `REVENUE`, `IMPAID`, `ACCOUNT_INDIVIDUAL`, `SECURITY`, `CONFIDENTIAL` | **a deconstruire** en tant que detections par mot-cle: indetectables localement, et sans rattachement a une personne elles ne designent aucune donnee personnelle |

Piste ouverte a l'inverse: detecter un **logo d'entreprise** dans une piece et
traiter le nom qu'il porte comme une donnee rattachee. A instruire.

## 4 ter. Homonymies et alias - le sujet le plus difficile

C'est le point qui justifie a lui seul la base des personnes, et il ne se resout
pas par une expression reguliere.

**Cas reel: plusieurs `M.` et `Mme Rouve` dans la meme copropriete.** Un PV peut
ecrire `M. Rouve`, `Mme Rouve`, `Rouve`, ou une graphie fautive. Rattacher au
mauvais homonyme est pire que ne pas rattacher: cela attribue un vote, une
opposition ou un impaye a la mauvaise personne.

La base doit donc porter, pour chaque entite, une **banque d'alias attendus** -
graphies, variantes, formes abregees - et surtout **signaler l'ambiguite au lieu
de la trancher**. Quand deux entites peuvent correspondre a une meme detection,
le rattachement remonte a l'humain. Jamais de choix automatique entre homonymes.

**Cas symetrique, personnes physiques et morales: `T Services` et `Tanore`.**
`T Services` est le nom commercial de l'entreprise individuelle `Tanore`, et les
deux graphies apparaissent dans le corpus. Il faut donc que les personnes
physiques puissent etre **rattachees aux personnes morales**, avec le type de
lien: nom commercial, gerant, associe, representant.

Meme besoin pour les **SCI**: un lot detenu par une SCI dont le gerant est une
personne physique nommee ailleurs dans le corpus.

Consequence de modele: la base n'est pas une liste de noms, c'est un **graphe
d'entites et de liens**, avec une banque d'alias par entite et une file
d'ambiguites a arbitrer.

## 5. Ce qu'il ne faut pas faire

- rattacher automatiquement une detection a une entite sur une simple
  ressemblance de nom, ni trancher seul entre deux homonymes;
- traiter une personne non trouvee dans la base comme une absence de donnee
  personnelle;
- faire sortir le sel ou la table de correspondance de l'instance;
- considerer qu'un document est caviarde parce qu'il porte le suffixe
  `.redacted` - verifier qu'une couche texte existait.

## 6. Points ouverts

- Detection des noms sans civilite: methode a choisir.
- Deconstruction des regles par mot-cle indetectables localement: perimetre et
  effet sur les registres deja produits.
- Banque d'alias par entite et file d'arbitrage des ambiguites.
- Graphe personnes physiques / personnes morales: types de liens a retenir.
- Detection de logo et rattachement du nom qu'il porte.
- Source et format du fichier des coproprietaires, et sa mise a jour.
- Historisation de la base: version a la date de chaque assemblee.
- Traitement des representants et des pouvoirs.
- Regles de biffage par type de document.
- Articulation avec les colleges d'acces deja decrits dans
  `confidentialite_et_biffage.md`.

## 7. Rattachement

Ce cahier des charges ne fait pas partie du lot gouvernance decrit dans
[`strategie_lot_gouvernance.md`](./strategie_lot_gouvernance.md). Il en est un
voisin: la chaine de decision a besoin des tantiemes pour controler les
majorites, et les tantiemes viennent de la base des coproprietaires. Le lien
existe, la dependance n'est pas bloquante a court terme - les decomptes de voix
figurent en clair dans les PV.
