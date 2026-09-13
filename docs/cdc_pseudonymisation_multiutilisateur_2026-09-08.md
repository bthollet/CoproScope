# Cahier des charges - pseudonymisation multiutilisateur

- Rattachement: `RM-2026-0126` (retrouvabilite contre fuite de nom), suite du POC
  monoutilisateur livre le 2026-09-08.
- Source: arbitrage vocal de Brice du 2026-09-08, verbatim horodate dans
  [`arbitrage_brice_0126_verbatim_2026-09-08.md`](./arbitrage_brice_0126_verbatim_2026-09-08.md).
- Statut: **conception. Rien de ce document n'est developpe.**
- Ce cahier ne remplace pas
  [`cdc_anonymisation_et_annuaire_2026-09-07.md`](./cdc_anonymisation_et_annuaire_2026-09-07.md),
  qui possede le modele d'entites, la banque d'alias et la file d'arbitrage. Il
  s'y appuie et traite ce que l'autre ne traite pas: **les droits, les niveaux
  de diffusion, et la jonction entre le langage reel d'un utilisateur et une
  base ou les patronymes n'existent plus.**

---

## 1. Ce que le POC monoutilisateur a livre, et sur quelle hypothese

Le POC du 2026-09-08 tient parce que CoproScope tourne pour **une seule
personne sur son poste**. L'hypothese est nommee dans le code
(`modules/table_pseudonyme.py`) et non cachee. Trois simplifications en
decoulent:

1. le deposant est l'utilisateur local: il n'y a personne d'autre a distinguer;
2. « l'accuse de depot montre le nom au deposant seul » se ramene a « une seule
   fois, a qui detient le jeton », parce que le seul lecteur possible est celui
   qui vient de deposer;
3. aucun controle de droits n'est ecrit: il n'y a qu'un college de lecture.

**Ce cahier commence exactement la ou ces trois phrases deviennent fausses.**

---

## 2. Le probleme dur, et Brice l'a nomme lui-meme

> « Du coup, quand je demande a l'IA des factures de Tanore, c'est complique,
> ca veut dire que sur les commandes, il faut qu'il y ait une association
> automatique... Ah, putain, c'est pas simple. Puisque l'utilisateur, il va
> parler a l'IA en langage reel, et il faudrait que l'IA traite derriere.
> Bref, ca, c'est le chantier d'apres. »

L'utilisateur parle avec des noms. La base n'en contient plus. Les deux sont
justes et ne peuvent pas se rencontrer sans un traducteur.

### 2.1 L'architecture: traduire aux deux frontieres, jamais au milieu

La table pseudonymisee est **le monde de l'IA**. Le patronyme n'y entre jamais.
La traduction se fait en deux points, tous deux locaux:

```
question humaine            reponse humaine
"factures de Tanore"        "3 factures de Tanore"
        |                            ^
        v  [1] resolution            |  [4] restitution
   annuaire local                annuaire local
        |                            ^
        v                            |
"factures de PERSONNE_CHENE_INDIGO"  |
        |                            |
        +--------> IA / moteur ------+
                (ne voit que des alias)
```

- **[1] Resolution.** Avant tout appel, l'annuaire cherche le patronyme et rend
  l'`entite_id` puis l'alias. C'est un `LEFT JOIN` local, pas une inference.
- **[4] Restitution.** La reponse revient en alias; l'annuaire les retraduit
  pour l'affichage, **et seulement si le lecteur a le droit de voir ce nom**
  (section 4).

### 2.2 L'exigence d'ordre, et c'est elle qu'il faut tester

**La resolution precede tout appel reseau.** Si la question part telle quelle
vers un service distant puis est traduite, la pseudonymisation n'a servi a
rien: le patronyme a deja quitte le poste, dans la question.

C'est une contrainte d'ORDONNANCEMENT, pas de contenu, et elle se teste:
intercaler un mouchard sur la couche de transport et verifier qu'aucune charge
sortante ne contient de patronyme connu de l'annuaire.

### 2.3 La degradation, qui est le vrai critere d'acceptation

Que se passe-t-il quand l'annuaire ne connait pas le nom demande ? Trois
comportements possibles, dont deux sont des fautes:

| Comportement | Verdict |
|---|---|
| Chercher le nom dans le texte brut a la place | **Faute.** Rouvre la fuite que tout le dispositif ferme. |
| Rendre « aucune facture trouvee » | **Faute grave, et c'est la pire.** Une reponse fausse en silence: l'utilisateur conclut que les factures n'existent pas. |
| Rendre « ce nom n'est pas dans l'annuaire; voulez-vous l'y ajouter ? » | **Correct.** Degradation bruyante, et elle propose l'action qui repare. |

C'est le test d'acceptation de la doctrine applique a la lettre: une valeur
inconnue sur l'axe *« ce nom est-il connu de l'annuaire »* doit degrader
proprement, pas produire une reponse fausse en silence.

---

## 3. Niveaux de diffusion: le renversement de perspective

### 3.1 Ce que Brice a dit

> « Un peu comme pour l'extranet, il y a plusieurs niveaux de diffusion. Sauf
> que l'extranet, on va partir du regime obligatoire [...] Alors que sur
> Coproscope, on va reflechir dans l'autre sens, c'est qu'est-ce qui est
> interdit. [...] Par defaut, il n'y a rien qui est interdit aux
> coproprietaires, sauf peut-etre ce qui releve encore des negociations. [...]
> sauf si negociation en cours ou judiciaire, en gros. Tu me confirmeras. »

### 3.2 La confirmation demandee: la doctrine ecrite CONFIRME

[`confidentialite_et_biffage.md`](./confidentialite_et_biffage.md), lignes
14-19, dit presque mot pour mot la meme chose:

> La doctrine produit est l'ouverture par defaut aux coproprietaires. Un
> document n'est pas sensible parce qu'il est technique, volumineux, lie a des
> travaux ou difficile a lire. Il devient restreint seulement si une
> interdiction est etayee ou si un blocage est justifie par le conseil
> syndical, par exemple pour une negociation commerciale en cours ou un
> contentieux.

**La regle est donc confirmee.** Avec trois nuances qui ne sont pas des
details.

### 3.3 Nuance 1 - la doctrine exige une JUSTIFICATION, pas seulement un motif

Brice enonce deux exceptions (negociation, judiciaire). La doctrine ecrite
ajoute une condition de forme: la restriction doit etre **etayee** ou
**justifiee par le conseil syndical**. Appartenir a la categorie « judiciaire »
ne suffit pas: il faut que quelqu'un l'ait dit et que ce soit trace.

C'est plus exigeant que ce que Brice a formule, et c'est dans le bon sens: sans
cette condition, « judiciaire » devient une etiquette commode pour tout fermer.

### 3.4 Nuance 2 - `recouvrement` n'est pas dans la doctrine ecrite, et differe

Brice cite « judiciaire et recouvrement ». La doctrine ecrite dit « negociation
commerciale en cours ou un contentieux ». **Le recouvrement est un ajout.**

Il merite sa propre categorie, parce que son motif n'est pas le meme:

- une negociation se protege pour ne pas affaiblir la copropriete face a un
  tiers - l'interet protege est **collectif**;
- un recouvrement vise un **coproprietaire nomme**. Ce qu'on protege est la vie
  privee d'un membre contre les autres membres. Le secret ne joue pas contre
  l'exterieur, il joue a l'interieur.

Consequence de conception: un document de recouvrement ne se traite pas par une
restriction de college, mais par la regle des pieces individuelles (section 4).
Les fusionner ferait perdre le motif.

### 3.5 Nuance 3 - le CODE ne fait pas ce que la doctrine dit

C'est le point le plus important de cette section, et il est mesure.

- **Branche de repli du code.** `_recommended_review_decision`
  (`modules/_privacyops_parts/01_scan_helpers.py:319-364`) se termine par un
  `return "A_ARBITRER"` motive par « Aucune decision de diffusion robuste n'a
  ete deduite ». Precision qui compte: ce n'est pas le defaut de TOUS les
  documents, c'est ce qui arrive a ceux qu'aucune branche precedente ne
  reconnait - `publication_form` n'est pas `raw`, et aucune transformation
  n'est exigee. Un document que le screening ne sait pas qualifier part donc
  **ferme en attente d'arbitrage**, alors que la doctrine ecrite dit qu'un
  document non qualifie est ouvert. C'est l'inconnu qui est traite a l'envers,
  et l'inconnu est le cas majoritaire sur un corpus reel - voir la mesure
  suivante.
- **Mesure sur corpus reel, deja consignee** dans
  `cdc_anonymisation_et_annuaire_2026-09-07.md` (decision D3): **474 documents
  sur 825 en `C8_Restreint_Critique`**, soit 57%, ce que ce cahier decrit
  lui-meme comme « un classement par prudence plutot qu'un jugement piece par
  piece ».
- **Mesure sur l'instance synthetique, 2026-09-08:** 7 `DIFFUSABLE_BRUT` et 2
  `DIFFUSABLE_APRES_BIFFAGE` sur 9. Elle ne contredit pas: les pieces
  synthetiques ont ete ecrites pour passer, et cette limite se declare au lieu
  de servir de preuve.

**Reponse a « tu me confirmeras »: la regle est confirmee telle qu'elle est
ecrite, et contredite telle qu'elle est implementee.** L'ouverture par defaut
est une doctrine que le produit affiche et que son code n'applique pas. Tant que
57% du corpus reel part en restreint-critique, discuter du niveau des exceptions
est premature: c'est le defaut lui-meme qu'il faut d'abord remettre a l'endroit.

---

## 4. Les pieces individuelles

### 4.1 Ce que Brice a dit

> « s'il pose ses appels de charges, des choses comme ca, ca doit etre
> accessible qu'a lui et au conseil syndical et eventuellement a des personnes
> a qui il donne acces. »

Et, honnetement:

> « Je ne sais pas bien ce qu'un coproprietaire simple pourrait deposer dans
> son Coproscope et qui ne serait pas cense etre accessible au conseil
> syndical. »

**Cette hesitation est conservee telle quelle: elle n'est pas tranchee ici.**

### 4.2 Le modele qui en decoule

Une piece individuelle a un **sujet** - la personne qu'elle concerne - distinct
de son **deposant** et de son **proprietaire de droits**. Trois cercles:

| Cercle | Qui | Fondement |
|---|---|---|
| Le sujet | le coproprietaire concerne | c'est sa piece |
| Le conseil syndical | par defaut, selon Brice | controle de gestion |
| Les delegataires | ceux a qui le sujet donne acces | acte volontaire, date, revocable |

### 4.3 La question a poser a Brice, parce qu'elle n'est pas tranchee

Son « je ne sais pas bien » porte sur le deuxieme cercle. Deux lectures
possibles, et elles ne donnent pas le meme produit:

- **(a) le CS voit par defaut** - coherent avec son role de controle, et avec
  le fait qu'un appel de charges transite deja par lui;
- **(b) le CS voit sur demande motivee** - coherent avec le fait qu'un
  coproprietaire qui depose ses propres pieces dans son espace peut y mettre
  autre chose que des appels de charges: un courrier d'avocat, un certificat
  medical justifiant une demande d'amenagement, un echange avec le syndic sur
  un impaye.

Le cas (b) devient franchement problematique des que le CS est **partie** au
litige - un recouvrement, precisement. Un membre du CS qui lit le dossier de
recouvrement dirige contre lui-meme, ou contre son voisin, n'est pas une
hypothese d'ecole.

**Decision requise de Brice. Elle n'est pas prise ici.**

---

## 5. Le role de l'annuaire

> « il va falloir que l'annuaire fasse la jonction avec les noms
> d'utilisateurs, les eventuels mandats, etc. »

L'annuaire devient le point de rencontre de trois notions aujourd'hui
separees, et qui ne doivent pas fusionner:

| Notion | Ce que c'est | Ou elle vit aujourd'hui |
|---|---|---|
| **Entite** | une personne physique ou morale du corpus | `cdc_anonymisation_et_annuaire_2026-09-07.md`, SQLite du coffre |
| **Compte utilisateur** | quelqu'un qui se connecte | `core/accounts.py` - dataclasses ecrites, **inertes**: un seul importateur, `commissionops.py`, et aucun code web |
| **Mandat / role** | ce que quelqu'un a le droit de faire, et pendant quelle periode | `RoleGrant`, `AccessGrant`, `CommissionMembership` - memes dataclasses, meme inertie |

### 5.1 La regle qui les separe

**Une entite n'est pas un compte, et un compte n'est pas un droit.**

- une entite existe sans compte: le fournisseur cite dans une facture de 2019
  n'ouvrira jamais de session;
- un compte peut ne correspondre a aucune entite du corpus: un gestionnaire
  invite;
- un mandat est **date**. Un president de CS de 2019 n'a pas les droits de 2026,
  et un PV de 2019 se lit contre l'annuaire de 2019 - c'est deja la regle de
  l'assertion datee du cahier annuaire.

Les confondre produirait le defaut numero un du produit dans un nouveau
domaine: plusieurs notions concurrentes pour la meme chose.

### 5.2 Etat reel, a ne pas se raconter

Le vocabulaire existe et est bien concu; **il n'est branche nulle part**.
`web/` ne l'importe pas. L'authentification est un jeton unique partage, sans
session ni utilisateur courant (`_app_fragments/part_003.pyfrag:122-135`). Le
multiutilisateur n'est donc pas « a etendre », il est **a construire**.

---

## 6. Chiffrement des originaux, derives en clair: options et couts

> « il faudra pouvoir mettre les documents originaux dans un conteneur crypte,
> les documents derives ailleurs, ou alors crypter les documents originaux
> individuellement, pour qu'ils soient visibles qu'a l'utilisateur, et garder
> les TXT en clair. »

**Brice ne tranche pas. Ce cahier ne tranche pas non plus.** Voici les options
et ce qu'elles coutent.

### 6.1 L'observation qui reoriente le choix

Avant de comparer: **le derive en clair contient l'essentiel de ce que
l'original contient.** Le TXT d'une assignation porte les memes noms, les memes
montants, les memes faits que le PDF. Chiffrer l'original en laissant le texte
extrait en clair protege donc surtout contre quelqu'un qui voudrait le
*document* - sa mise en forme, son en-tete, sa signature - pas contre quelqu'un
qui veut l'*information*.

Ce n'est pas un argument contre le chiffrement. C'est un argument pour dire
contre QUI il protege, avant de choisir comment.

### 6.2 Les trois options

| Option | Ce que c'est | Ce qu'elle coute |
|---|---|---|
| **A. Conteneur chiffre** | tous les originaux dans un volume, derives a cote | Simple a poser. Tout ou rien: ouvert, tout est lisible. Une sauvegarde du conteneur ouvert annule la protection. |
| **B. Chiffrement par document** | chaque original chiffre pour son ou ses destinataires | Granulaire, colle aux trois cercles de la section 4. Cout reel: gestion de cles par piece, re-chiffrement a chaque changement de droits, et un index qui devient le maillon faible - il faut bien savoir quoi dechiffrer. |
| **C. Pas de chiffrement applicatif** | droits du systeme de fichiers, chiffrement du disque | Cout nul, deja le cas. Ne protege pas entre utilisateurs d'un meme poste, ni dans une sauvegarde en ligne. |

### 6.3 Le cout que les trois partagent, et qu'on oublie toujours

**La recuperation.** Une archive de copropriete doit survivre au president de
CS qui l'a creee, a son ordinateur, et a sa memoire. Une cle perdue est un
fonds documentaire perdu - et les pieces d'une copropriete ont une valeur
juridique qui se mesure en decennies.

Le cahier annuaire prevoit deja `RecoveryShare` et `RecoveryGroup`. **Aucune
option de chiffrement ne doit etre retenue avant que le chemin de recuperation
soit ecrit**, sous peine de construire une perte de donnees a retardement,
exactement le motif de defaut differe que ce depot traque partout ailleurs.

### 6.4 Ce qui est deja tranche, et qui ne se rediscute pas ici

Le sel d'alias (`sel_alias.key`) ne sort jamais de l'instance. Quelle que soit
l'option, il ne va pas dans le meme contenant que ce qu'il protege: un sel
range a cote des alias qu'il derive permet de relier les deux.

---

## 7. Le test en double aveugle: ce qu'il mesure vraiment

### 7.1 Ce que Brice propose

> « le coproscope fait une premiere lecture et un typage, et l'IA, a l'aveugle,
> a partir des documents, des transcripts anonymises, essaye d'identifier le
> type. »

### 7.2 Verdict: **oui, c'est un instrument valable - mais pas de ce qu'on croit**

**Ce qu'il ne mesure PAS: la justesse du typage.** Si CoproScope et l'IA
s'accordent, cela ne prouve pas que le type est bon. Les deux lisent la meme
piece et s'appuient probablement sur le meme signal - le titre
`proces-verbal de l'assemblee` ancre en tete, invariant deja etabli sur 37
documents et deux cabinets. Deux lecteurs qui utilisent le meme indice sont
d'accord meme quand ils ont tort. **L'accord n'est pas la verite.**

Et le desaccord ne prouve rien non plus, faute d'etalon: qui a raison ?

**Ce qu'il mesure REELLEMENT, et qui est precieux: la perte d'information de la
pseudonymisation.** C'est une etude d'ablation. Le montage correct compare
l'IA a **elle-meme**, pas a CoproScope:

| Passage | Entree de l'IA | Ce qu'on lit |
|---|---|---|
| 1 | transcript **brut** | taux de typage de reference |
| 2 | transcript **pseudonymise** | taux de typage apres traitement |

L'ecart entre 1 et 2 est le **cout en information** de la pseudonymisation. S'il
est nul, on a la preuve que remplacer les identites ne detruit rien de ce dont
le typage a besoin - resultat solide, actionnable, et qui ne demande aucun
etalon manuel.

Comparer l'IA a CoproScope mesure autre chose: l'accord entre deux typeurs.
**Confondre les deux est le piege**, parce que le meme montage donne les deux
chiffres et qu'un seul repond a la question.

### 7.3 Le troisieme usage, que Brice n'a pas demande et qui vaut plus

Le meme montage, retourne, donne un test de **re-identification**: on fournit a
l'IA le transcript pseudonymise et on lui demande **qui** est
`PERSONNE_CHENE_INDIGO`. Si elle y arrive - par le contexte, un numero de lot,
un montant singulier, une date - alors la pseudonymisation a echoue, quelle que
soit la qualite des alias.

C'est la mesure qui dit si le dispositif protege quelqu'un. Elle est plus dure
que le typage, et c'est la seule qui adresse le risque reel.

### 7.4 La condition sans laquelle rien de tout cela ne vaut

Les trois passages exigent un corpus dont l'etalon a ete etabli **a la main
avant tout traitement outil** - `instances/tests_ux` et
`docs/etalon_corpus_tests_ux.md` (`RM-2026-0050`). Mene sur une instance
historique, ce test mesurerait la sortie d'une version anterieure du code,
donc son propre ancetre.

---

## 8. Le residu que le POC laisse ouvert, et que ce cahier doit fermer

Chacun de ces points est aujourd'hui un test qui passe en le nommant.

| # | Residu | Ou il est mesure |
|---|---|---|
| R1 | **FERME le 2026-09-09 par `RM-2026-0130`.** `/api/model` rendait le modele verbatim; la mesure a donne **102** colonnes de tiers et non 15 - le 15 etait la portee du temoin, qui n'instrumentait qu'un registre sur dix-huit. La route rend desormais un resume DECLARE et aucune valeur de registre n'en sort. **Ce que la fermeture a casse:** ce cahier ecrivait « aucun gabarit ni script de l'interface ne la consomme », ce qui etait vrai et incomplet - un test produit lisait `payload["ux"]["registre"]` et est tombe en `KeyError`, remis d'aplomb le 2026-09-09. | `test_surface_machine_ne_rend_que_le_declare`, `test_ui_nom_de_fichier_ne_fuit_pas::test_la_surface_machine_ne_rend_plus_...`, `test_ui_registre_actions::test_actions_api_ne_rend_plus_le_namespace_ux_...` |
| R2 | **L'identifiant de depot est devinable** (horodatage UTC a la seconde). Qui le reconstruit consomme l'accuse a la place du deposant. | `test_accuse_depot::test_RESIDU_l_identifiant_de_depot_est_devinable` |
| R3 | **Il n'existe aucune notion de deposant.** « au deposant seul » repose sur l'hypothese monoutilisateur, pas sur du code. | `test_accuse_depot::test_RESIDU_il_n_existe_aucune_notion_de_deposant` |
| R4 | **Deux pieces de la meme personne ne sont pas reliees**: l'alias porte sur la chaine, pas sur l'entite. C'est le « chantier d'apres » de Brice. | `test_table_pseudonyme::test_RESIDU_deux_pieces_...` |
| R5 | **6 routes sur 54 ne sont pas couvertes** par la garde anti-fuite (parametres de chemin inconnus). | `test_ui_nom_de_fichier_ne_fuit_pas::test_RESIDU_certaines_routes_...` |
| R6 | **Le numero de lot sort en clair** sur la fiche document. Exposition acceptee et non arbitree par Brice. | `EXPOSITIONS_HTML_ACCEPTEES` |

**R6 demande un arbitrage.** Un numero de lot ne nomme personne, mais l'annuaire
que la section 5 construit permettra precisement de remonter du lot a son
proprietaire. Le jour ou cette jonction existe, le lot devient un identifiant
indirect, et cette exposition change de nature sans que rien dans le code n'ait
bouge.

---

## 9. Criteres d'acceptation du lot multiutilisateur

Un lot qui pretend traiter ce cahier doit fournir:

1. **Test d'ordonnancement**: aucune charge sortante ne contient un patronyme
   connu de l'annuaire. Mouchard sur la couche de transport, pas revue de code.
2. **Test de degradation**: un nom inconnu de l'annuaire produit un message qui
   le dit, et jamais « aucun resultat ».
3. **Test de re-identification** (section 7.3) sur le corpus etalon, avec son
   taux publie - meme mauvais.
4. **Test d'ablation** (section 7.2), deux passages, ecart publie.
5. **Test de droits**: pour chaque cercle de la section 4, un lecteur autorise
   voit, un lecteur non autorise ne voit pas, et le second ne peut pas
   distinguer « je n'ai pas le droit » de « ca n'existe pas » si la piece est
   une piece individuelle.
6. **Comptage des routes**: la garde anti-fuite couvre toujours au moins 80%
   des routes servies, et les non couvertes sont nommees.
7. **Chemin de recuperation ecrit** avant toute option de chiffrement retenue.

---

## 10. Decisions requises de Brice

| # | Decision | Element de decision |
|---|---|---|
| **D1** | **Le conseil syndical voit-il par defaut les pieces individuelles ?** Section 4.3. | Brice a dit « je ne sais pas bien ». Le cas du recouvrement, ou le CS peut etre partie, penche pour un acces motive plutot que par defaut. |
| **D2** | **Le defaut de diffusion doit-il etre remis a l'endroit ?** Section 3.5. | La doctrine dit ouvert, le code repond `A_ARBITRER`, et 57% du corpus reel part en `C8`. Tant que ce n'est pas corrige, le reglage des exceptions ne change rien. |
| **D3** | **`recouvrement` est-il une categorie a part** de `judiciaire` ? Section 3.4. | Leurs motifs different: interet collectif d'un cote, vie privee d'un membre contre les autres de l'autre. |
| **D4** | **Priorite entre R1 et R3.** | R1 (`/api/model`) est la fuite la plus large et se corrige sans notion d'utilisateur. R3 (pas de deposant) bloque tout le reste du multiutilisateur. R1 est moins cher, R3 est structurant. |
| **D5** | **Option de chiffrement.** Section 6. | Non tranchee ici a dessein. Prerequis: le chemin de recuperation (6.3). |

---

## 11. Ce que ce cahier ne traite pas

- Le modele d'entites, la banque d'alias, la file d'arbitrage et le detecteur
  d'oublis: ils appartiennent a
  [`cdc_anonymisation_et_annuaire_2026-09-07.md`](./cdc_anonymisation_et_annuaire_2026-09-07.md).
- Le seuil de `C8` en tant que tel: il appartient a
  [`confidentialite_et_biffage.md`](./confidentialite_et_biffage.md). Ce cahier
  ne fait que constater son effet sur le defaut de diffusion.
- Le partage hors du poste - Drive, extranet, transmission au syndic. Un cahier
  qui melangerait droits internes et transport melangerait deux menaces.
