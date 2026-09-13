<!-- Cette note porte des MONTANTS reels de la copropriete de travail.
     L'identite est pseudonymisee, les chiffres ne le sont pas. Elle elargit
     donc la surface de `RM-2026-0137` (zero donnee personnelle sur GitHub) et
     doit etre traitee avec les autres avant tout push. -->

# Note pour Brice — page de contrôle des comptes : trois concepts, ce qui tient et ce qui tombe

**Avertissement sur ce que j'ai reçu.** J'ai reçu en entier le concept 1 (« Le trajet de l'euro ») avec ses deux critiques, celle du novice et celle de l'expert-comptable. Pour le concept 2 (« Le mur des désaccords ») je n'ai reçu que son principe et le début de ses colonnes, **sans aucune critique**. Pour le concept 3 (« Approuver l'exercice ») je n'ai retrouvé que les notes de travail de son auteur, **sans critique non plus**. Je le dis parce que la consigne demande de rapporter les mots des critiques : je ne peux les rapporter que pour le concept 1. Pour compenser, j'ai refait moi-même les mesures qui décident, en lecture seule sur le corpus `C:\Users\brice\CoproScope\instances\test_identite_ag_20260908`, et j'ai ouvert le corpus du second cabinet, `C:\Users\brice\CoproScope\instances\erables_pseudo_test`, que personne n'avait ouvert.

Aucun fichier du dépôt n'a été modifié. Rien n'a été écrit dans les corpus. La base a été ouverte en lecture seule (`mode=ro`). La suite de tests n'a pas été lancée.

---

## 1. La frontière, en une phrase

**La page des comptes demande : « de l'argent est sorti, où est-il allé, et qu'est-ce qui prouve qu'il devait sortir ? » La page des décisions demande : « un pouvoir a été exercé au nom du syndicat, qui l'avait autorisé, et à quelles conditions ? »**

Ce ne sont pas la même question parce qu'elles ne partent pas du même bout, et surtout parce que **l'une des deux peut afficher une ligne que l'autre ne peut pas faire exister**. Une dépense qu'aucune décision n'explique produit une ligne sur la page des comptes ; sur la page des décisions elle ne produit rien, faute d'objet. C'est exactement ce que vous avez dit : « on peut avoir des travaux exécutés mais pas décidés ». C'est cette phrase, et elle seule, qui justifie deux pages plutôt qu'une.

La règle de partage qui en découle tient en une question à poser avant d'ajouter la moindre colonne : **de quel objet cette colonne est-elle une propriété ?** Propriété d'un euro (sur quel compte il est rangé, quelle pièce le justifie) → page des comptes. Propriété d'un acte d'autorisation (le texte voté, la majorité, l'avis du conseil syndical, le devis retenu, les seuils) → page des décisions. Propriété d'autre chose (l'assurance décennale d'une entreprise, par exemple) → ni l'une ni l'autre. C'est la force de cette règle : elle a le droit de répondre « aucune des deux », et c'est ce qui empêche les deux pages de gonfler sans fin.

---

## 2. Ce qui doit disparaître de la page des comptes

**La colonne « Décision / devis » est supprimée, pas renommée.** Aujourd'hui elle décide de son état en collant bout à bout toutes les valeurs de sa propre ligne et en y cherchant neuf mots français. J'ai relu le code : `_decision_cell_status`, ligne 344 de `C:\Users\brice\CoproScope\coproscope\server\src\coproscope\web\compta_rapprochement_view.py`, teste la présence de `manquant, manquante, demander, absence`, puis de `decision, devis, commande, vote, reception`. Deux de ces mots se trouvent dans des phrases que l'outil a lui-même écrites plus haut dans la ligne. **La colonne relit sa propre prose et en tire un constat sur la copropriété.** Et elle parle d'un objet dont elle n'a pas la référence : les 24 champs qui alimentent cette page ne portent aucun numéro de résolution, aucune date d'assemblée.

**Ce qui la remplace : une colonne qui ne dit qu'une chose et qui la dit avec sa référence.** Quatre valeurs, pas une phrase à lire. Le conseiller qui veut savoir *pourquoi* clique et arrive sur la page des décisions. Rien du contenu de la décision n'est recopié.

**Disparaissent aussi, définitivement, de la page des comptes** : le texte de la résolution, l'annexe visée, l'avis du conseil syndical, le rapport annuel du conseil syndical, le devis retenu, le seuil de consultation du conseil syndical, le seuil de mise en concurrence. Sept preuves qui n'ont rien à faire sur une ligne de facture. Le mot « devis » cesse de figurer des deux côtés.

**Disparaît la file de vignettes.** Mesuré : dans `templates\compta_rapprochement.html`, **0 occurrence** de `<table`, `<select` ou « filtre ». Dans `templates\controle_gouvernance.html`, **12**. La forme homogène que vous demandez entre les deux pages n'existe aujourd'hui que d'un côté.

**Disparaît le second magasin pour la trace humaine.** Aujourd'hui la page des comptes écrit la conclusion du conseil dans un fichier tableur posé à côté des sorties comptables, pendant que la table `traces_controle` du coffre existe et contient **0 ligne**. Deux endroits pour la même notion.

**Ne disparaît pas, et c'est délibéré : la colonne bancaire.** Elle est légitime, elle est sans source. Son libellé change : au lieu de « source manquante », qui accuse le syndic, elle dit « aucun relevé bancaire fourni au produit » et nomme la pièce à demander.

**Symétriquement, côté décisions** : la colonne « Exécution » cesse de prétendre montrer une preuve de paiement et devient un renvoi qui compte. Mesuré : elle est vide sur **557 lignes sur 557**, et ce vide produit **83 des 96 alertes** de la page (73 `EXECUTION_NON_CONTROLABLE` + 10 `ACTE_SANS_EXECUTION`), soit 86 %. La page des décisions passe donc l'essentiel de son temps à signaler qu'elle ignore ce que la page des comptes devrait lui dire.

---

## 3. Les trois concepts

### Concept 1 — « Le trajet de l'euro »
**Principe :** une ligne = un euro qui bouge, lu de gauche à droite, de ce qui l'autorise jusqu'à la pièce qui prouve qu'il est sorti. Sept colonnes.
**À l'arrivée :** quatre encadrés (quel document je regarde, le total imprimé n'est pas la dépense, où va l'argent des travaux, ce que la page ne sait pas), puis un tableau filtré par défaut sur les sorties de plus de 1 000 EUR.
**Coût :** faible au départ — le lecteur d'état des dépenses fonctionne déjà et n'est appelé par aucun programme du produit.
**Faiblesse :** **abattu par l'expert, et je confirme.** Son unité est fausse : la comptabilité de copropriété est une comptabilité d'engagement, une ligne est un engagement, jamais un mouvement d'argent. L'annexe 1 au 31/12/2025 porte 152 728,51 EUR de dettes fournisseurs : ces charges sont enregistrées et pas payées. Deux de ses sept colonnes tombent avec l'unité.

### Concept 2 — « Le mur des désaccords »
**Principe :** une ligne n'existe que si deux pièces ne disent pas la même chose. Une dépense sur laquelle tout concorde est comptée, pas affichée.
**À l'arrivée :** une liste de constats avec leur nombre, chacun ouvrant le tableau filtré — exactement la forme de la page des décisions, ce qui rend les deux pages homogènes.
**Coût :** modéré, la mécanique de filtrage existe déjà côté décisions.
**Faiblesse :** il ne répond pas à la question qu'un conseil syndical doit trancher en assemblée. Avant de lever la main pour approuver les comptes, il faut pouvoir dire poste par poste où est parti l'argent — y compris là où tout concorde. Or **le résultat rassurant est un résultat** : réalisé 2025 des charges courantes 295 349,10 EUR contre budget voté 300 000,00 EUR, budget non dépassé. Une page qui n'affiche que les désaccords ne peut pas montrer cela. Second risque : il hérite des mêmes fausses accusations que le concept 1, puisqu'un « désaccord » calculé sur une donnée mal lue est une accusation.

### Concept 3 — « Approuver l'exercice »
**Principe :** la colonne vertébrale est **l'annexe comptable**, pas l'état des dépenses. Une ligne = un poste de charges. Huit colonnes : poste, ce qui l'autorise, budget voté, dépensé, appelé, reste à financer, pièces au dossier, ma conclusion.
**À l'arrivée :** un bandeau de trois lignes, les égalités du décret une ligne chacune, puis dix-huit lignes de postes avec les totaux imprimés par le syndic.
**Coût :** le plus élevé des trois, parce qu'il demande un lecteur d'annexe en plus du lecteur d'état des dépenses.
**Faiblesse :** son auteur la nomme lui-même, et elle est juste : fonder « ce qui l'autorise » sur les intitulés de compte 671000 et 672000 est **une modalité d'un cabinet déguisée en invariant**, et produirait une réponse fausse en silence chez un autre syndic.

---

## 4. Ce que le novice n'a pas compris

**Sur le concept 1, j'ai ses mots.** Il est retraité, membre du conseil syndical, ni comptable ni informaticien.

Sur les intitulés : « **Marché** — le pire de tous. Pour moi un marché, c'est le marché du samedi. » « **Imputation** — le mot me fait penser à *imputer une faute à quelqu'un*, donc j'y entends une accusation. » « **Exécution** — je comprends *exécution des travaux*, c'est-à-dire : est-ce que le chantier a été fait. Or on me dit que la colonne montre la facture. J'aurais lu cette colonne de travers pendant des mois. » « **Sens** — j'ai lu *Sens et montant* comme *ce que ça veut dire, et combien*. » « **Pièce** — dans un immeuble, c'est une chambre. »

Sur ce qu'on lui demande : « Je vous le dis franchement : **je ne le ferai pas.** » Il parle du rattachement manuel de chaque dépense à sa décision, sur 587 lignes. « Si la colonne qui fait tout l'intérêt de la page ne se remplit que si je passe des soirées à la remplir, alors cette colonne n'existe pas. »

Sur les deux documents contradictoires : « **Je suis incapable de choisir.** Ce n'est pas ma compétence, et si je choisis mal, tout ce qui suit est faux. » Il propose lui-même la sortie : « Ce qu'il me faudrait n'est pas un bouton : c'est **la liste des lignes qui diffèrent entre les deux**. »

Sur les colonnes vides : « Un tableau où presque une colonne sur deux répète le même mot sur 587 lignes, **je le crois cassé.** Vous appelez ça de l'honnêteté ; moi je vois un logiciel qui ne marche pas. » Et sur la colonne d'autorisation : « **La même phrase pour le banal et pour l'inquiétant, c'est une phrase inutile.** »

Sur ce qui lui fait peur : « Si l'outil est capable d'imprimer trente millions sans broncher, **pourquoi est-ce que je croirais le 92 401,65 ?** »

Son verdict : **GO**, sous quatre conditions bloquantes — renommer quatre colonnes en français de tous les jours, séparer l'appel de fonds du paiement au fournisseur (« deux poches différentes, dont une seule est la mienne »), ne pas ouvrir la page sur trois colonnes vides et trois « aucun », et donner à la colonne d'autorisation la valeur « pas de décision nécessaire ».

**Sur les concepts 2 et 3, je n'ai pas ses mots.** Mais quatre de ses objections sont transférables telles quelles, parce qu'elles portent sur la forme et non sur le concept : le jargon (le concept 3 emploie « poste », « clé de répartition », « opérations exceptionnelles », « granularité »), les colonnes vides (le concept 3 en a deux : « appelé » n'est lisible qu'au compte 702, « payé en banque » n'a aucune source), la peur des chiffres invraisemblables, et l'impossibilité de trancher entre deux documents. Le concept 2 échappe à la troisième mais aggrave la première : « désaccord » n'est pas un mot que le novice emploie.

---

## 5. Ce que l'expert a réfuté

L'expert-comptable a rendu un **NO-GO** sur le concept 1. J'ai revérifié ses trois refus principaux, moi-même, et ils tiennent. J'ai aussi trouvé une erreur chez lui.

**Réfutation 1 — six fausses accusations sur six, sur la seule chose que cette copropriété fait de façon irréprochable.** Une assemblée a voté, entrée par entrée, le remplacement des boîtes aux lettres : **six résolutions adoptées, quatre rejetées** (requête sur `actes_autorisation`, objet contenant `BOITES AUX LETTRES`, colonne `resultat`). Les comptes 2025 portent **six lignes** au compte 671000 « travaux décidés par l'assemblée générale », 17 013,70 EUR, dont **quatre totaux imprimés à 2 907,30 EUR** — le montant même du devis voté. Aucune ligne ne correspond aux quatre résolutions rejetées. La chaîne est complète, six fois. **La colonne « Autorisation » du concept 1 écrirait « aucune autorisation rattachée » sur ces six lignes.** Une colonne vide n'est pas neutre quand elle s'appelle *Autorisation*.

**Réfutation 2 — la mesure qui fondait cette faiblesse est fausse.** Le concept 1 écrit : « aucun des 81 montants portés par les décisions ne se retrouve dans l'état des dépenses. Zéro sur 81. » J'ai cherché `2907` dans le coffre : **0 occurrence** dans `devis_cites.montant_ttc`, `devis_cites.montant_intitule`, `actes_autorisation.montant_autorise` et `attributs_acte.valeur`. Le montant existe dans le monde réel et se trouve quatre fois dans l'état des dépenses ; il n'est pas dans les 81 parce que le produit ne lit les devis que dans les convocations, pas dans les procès-verbaux. **Le « zéro sur 81 » décrit un défaut d'extraction, pas le monde.** Une décision de conception majeure — le rattachement à la main, pour toujours — était bâtie dessus.

Et les 81 montants ne sont pas tous des euros : **4 valent exactement 30 000 000,00 EUR, 8 dépassent le million, 20 dépassent 400 000 EUR**, pour une copropriété qui dépense 357 493,10 EUR par an. Ce sont très probablement des voix ou des tantièmes lus comme des sommes.

**Réfutation 3 — l'encadré d'accueil « 84 % des travaux sans vote » est démenti par le document qu'il cite.** La section travaux compte **trois** comptes, pas deux : 671000 travaux décidés 17 013,70 EUR (6 lignes), 672000 travaux urgents 92 401,65 EUR (67 lignes), 702000 provisions appelées **−55 943,62 EUR** (19 lignes). Somme : **53 471,73 EUR**, qui est exactement le total « TOTAL CHARGES TRAVAUX ET OPERATIONS EXCEPTIONNELLES » imprimé par le syndic. Le 84 % est le rapport de deux des trois termes. En outre, le compte 672 est une catégorie de la nomenclature comptable, pas une confidence du syndic : lire son intitulé libre au lieu de son numéro normé, c'est coder une modalité.

**Réfutation 4 — les sources déclarées absentes sont au dossier, mal classées.** J'ai cherché l'en-tête « ANNEXE N° 1 à 5 » dans les 4 000 premiers caractères de chaque document : **32 documents**. Or le registre n'en étiquette que **6** comme `Annexe_Comptable`, toutes des annexes 1. Les autres sont rangées sous six étiquettes différentes : annexe 2 → `Contrat_Syndic` (4) et `Budget_Previsionnel` (2) ; annexe 3 → `Budget_Previsionnel` (3) et `CR_CS` (1) ; annexe 4 → `Budget_Previsionnel` (4) et `Dossier_Travaux` (2) ; annexe 5 → `Marche_Travaux` (2), `Note_Honoraires` (2), `Dossier_Travaux` (2) ; et 4 annexes 1 restent en `A_CLASSER`. **Dire « pas de source » d'une pièce présente et complète sur quatre exercices est une accusation à l'envers, et elle est plus difficile à rattraper**, parce que le conseiller n'ira pas chercher ce que la page lui dit qui n'existe pas.

**Réfutation 5 — des factures réclamées à des lignes qui n'en ont pas à avoir.** Le compteur « 189 lignes sans référence de pièce, 45 186,80 EUR » mélange des natures. 19 de ces lignes sont des appels de provisions (compte 702000) : un appel n'a pas de facture fournisseur. Et **20 790,11 EUR** sont une quote-part versée au syndicat principal (total imprimé « TOTAL CHARGES SYND. PRINCIPAL ») : ni facture fournisseur, ni résolution de cette assemblée-ci. Au moins 24 alertes garanties fausses.

**Réfutation 6 — la taxe.** Le concept 1 écrit « Facture, montant TTC ». L'extracteur du dépôt expose pourtant l'axe : la convention peut être `TTC_TAXE_INCLUSE`, `HT_TAXE_AJOUTEE` ou `CONVENTION_INCONNUE`. Chez un cabinet qui édite en hors taxes, la page signalerait un écart **sur chaque ligne d'une copropriété parfaitement en règle**.

**Là où l'expert se trompe, et je le corrige.** Il écrit que « l'annexe 1 ne porte plus rien au compte 102 provisions pour travaux à la clôture 2025 » et en tire une question sur le financement. Le compte 102 est effectivement vide (17 443,80 EUR à l'exercice précédent, rien à la clôture), **mais l'annexe 1 porte le compte 105 « Fonds de Travaux » à 36 361,98 EUR puis 49 863,12 EUR à la clôture.** Le fonds de travaux n'est pas vide : il a augmenté de 13 501,14 EUR. Publier « le fonds de travaux ne porte plus rien » serait exactement le type d'accusation fausse que tout ce chapitre cherche à empêcher. (Détail mineur : les 7 869,09 EUR de comptes de régularisation qu'il cite sont du côté des dettes, pas des créances.)

**Un défaut que je n'ai vu nulle part et qui touche les deux pages.** Les dix résolutions « boîtes aux lettres » apparaissent dans **trois documents différents** : dix lignes dans l'un, huit dans un deuxième, deux dans un troisième — **vingt lignes en base pour dix votes réels**. Le compteur « 557 actes » surcompte donc, d'un facteur inconnu. Tout chiffre affiché en tête de la page des décisions hérite de ce défaut.

---

## 6. Les contrôles à faire

**Réserve sur les sources.** Les identifiants et dates de version ci-dessous ont été lus sur Legifrance via l'interface PISTE **le 2026-09-08 par un autre agent** ; je ne les ai pas relus dans cette session. Toutes les versions citées portent l'état `VIGUEUR`, ce qui veut dire « en vigueur à la date demandée » et jamais « à jour » : **la date de version fait partie de la citation**. Le registre du dépôt (`server\src\coproscope\modules\_budget_previsionnel_sources.py`) porte déjà 16 de ces 24 identifiants, sans divergence ; 8 manquent.

### Contrôles alimentés dès aujourd'hui

| Contrôle | Fondement | Version lue | Ce que ça donne sur le corpus |
|---|---|---|---|
| **Les totaux se recoupent** (annexes 2, 3, 4) | décret 2005-240, art. 10 — LEGIARTI000006239518 | 2005-03-18 | Vérifié par moi : l'état des dépenses à 591 lignes donne 295 349,10 EUR de charges courantes, **exactement** le sous-total de l'annexe 2 soumise au vote |
| **Réalisé contre budget voté** | loi 65-557, art. 14-1 — LEGIARTI000043977299 | 2023-01-01 | 295 349,10 réalisé contre 300 000,00 voté : **budget non dépassé**, sous-consommé de 1,55 % |
| **Périmètre du budget prévisionnel** | décret 67-223, art. 44 — LEGIARTI000006488761 | 2004-06-04 | Déjà codé (`b1_perimetre_article_44`), affiché nulle part |
| **Complétude du dossier de convocation**, avec la distinction *validité de la décision* / *information des copropriétaires* | décret 67-223, art. 11 — LEGIARTI000053191281 | 2025-12-25 | 39 convocations, 12 budgets, 32 annexes au dossier |
| **Fenêtre de consultation des pièces** | loi 65-557 art. 18-1 (LEGIARTI000042120918, 2020-10-25) ; décret 67-223 art. 9-1 (LEGIARTI000038702079, 2019-06-29) et art. 9 (LEGIARTI000042078632, 2020-07-04) | — | Se lit sur la convocation seule |
| **Calendrier de l'exercice** (12 mois, 18 au premier) | décret 2005-240, art. 5 — LEGIARTI000006239513 | 2005-03-18 | Les 9 états lus portent tous 01/01 → 31/12 |
| **Seuils d'alerte : impayés et retard d'approbation** | loi 65-557, art. 29-1 A — LEGIARTI000049397770 | 2024-04-11 | Annexe 1 : 115 629,04 EUR de sommes exigibles restant à recevoir, contre 40 611,67 un an plus tôt |

### Contrôles partiellement alimentés

- **Qualité de la pièce justificative** (original, références du syndicat, daté, conservé dix ans) — décret 2005-240 art. 6, LEGIARTI000006239514, version du 2005-03-18. **398 lignes sur 587 portent une référence de pièce** ; vérifier qu'elle nomme le syndicat demande de lire la facture. *Cet article ne figure pas dans le registre de sources du dépôt.*
- **Vote du budget avant le début de l'exercice, assemblée dans les six mois de la clôture** — décret 67-223 art. 43, LEGIARTI000006488753, version du 2004-06-04 ; loi 65-557 art. 14-1. **Non calculable pour 7 assemblées sur 10**, qui ne portent aucune date lue.
- **Plancher du fonds de travaux (5 % du budget)** — loi 65-557 art. 14-2-1, LEGIARTI000043967792, version du 2023-01-01. Le solde est lisible (49 863,12 EUR) ; **le texte porte sur la cotisation annuelle, qui n'est pas lue.**
- **Taux d'impayés contre le seuil de 25 %** — le rapport 115 629,04 / 357 493,10 = 32,3 % circule dans les notes de travail, **mais son dénominateur n'est pas celui du texte** (« les sommes exigibles »), et le seuil bascule à 15 % au-delà de deux cents lots : **le nombre de lots n'est pas mesuré**. À afficher comme « à établir », jamais comme un dépassement constaté.

### Contrôles sans aucune source aujourd'hui

- **Compte bancaire séparé et remise des relevés au conseil syndical** — loi 65-557 art. 18, II, LEGIARTI000049398867, version du 2024-04-11. **1 seul document sur 858 est étiqueté « relevé bancaire », et c'est un courrier commercial de bienvenue.** Aucun lecteur bancaire n'existe dans le code.
- **Appels de fonds autorisés, plafond de l'avance de réserve à un sixième** — décret 67-223 art. 35, LEGIARTI000053191341, version du 2025-12-25. **14 appels de fonds au dossier, aucun lecteur dans le produit** — et l'expert relève que ces 14 documents sont adressés à un copropriétaire nommé : les lire donnerait le compte d'une personne, pas les appels du syndicat.

### Contrôles cités **sans source vérifiée** — à ne pas coder en l'état

L'expert les cite explicitement de mémoire professionnelle, sans les avoir contrôlés sur Legifrance : travaux urgents et leur ratification (décret de 1967, art. 37), syndicats secondaires (loi de 1965, art. 27), honoraires du syndic et contrat type (art. 18-1 A), charges récupérables (décret de 1987). **Ils doivent passer par le registre du dépôt, avec identifiant et date de version, avant d'entrer dans du code.** Les faits, eux, sont mesurés : 20 790,11 EUR de quote-part au syndicat principal, 26 326,80 EUR de rémunération du syndic sur deux lignes, 226 213,47 EUR de charges locatives lues sur 397 lignes.

---

## 7. Ma recommandation

**Je retiens le concept 3, « Approuver l'exercice », comme structure de la page, avec la règle de frontière du concept 1 et le bandeau du concept 2. Le concept 1 est abattu comme page ; sa règle de partage survit.**

**Pourquoi le concept 3, et pas les deux autres — la raison est une mesure que personne n'avait faite.** J'ai ouvert le corpus du second cabinet, `instances\erables_pseudo_test` : **22 documents, ZÉRO état des dépenses**, l'expression n'apparaît dans aucun texte. En revanche, **les cinq annexes 1 à 5 y sont présentes**, regroupées dans trois documents (classés `CR_CS`). Autrement dit : la pièce sur laquelle les concepts 1 et 2 posent toute leur page **n'existe pas chez le second syndic**, tandis que la pièce sur laquelle le concept 3 pose la sienne est imposée par décret et se retrouve chez les deux. C'est exactement le test d'acceptation de la règle du dépôt : un troisième syndic arrive demain, le concept 1 rend une page vide en silence, le concept 3 se dégrade proprement en disant « le détail par ligne n'est pas publié par ce syndic ».

**Deuxième raison : le concept 3 tranche ce que le novice disait ne pas savoir trancher.** L'écart de 8 672,27 EUR entre les deux états des dépenses 2025 n'est pas un mystère à arbitrer. Je l'ai localisé : il porte sur **quatre comptes seulement sur dix-huit** — entretien et petites réparations +7 802,50, eau +547,77, électricité +200,00, locations immobilières +122,00 — et **à 0,00 sur les travaux**. Et l'état à 591 lignes concorde **au centime** avec l'annexe 2 soumise à l'approbation (295 349,10 EUR de charges courantes ; eau 52 764,36 ; électricité 9 622,41). La bonne phrase n'est donc pas « le produit ne sait pas lequel fait foi », c'est : **« un état des dépenses circule avec 8 672,27 EUR de plus que l'annexe soumise au vote, dont 7 802,50 sur un seul poste. »** Ça, un conseil syndical le porte en assemblée. Cette mesure n'a été possible que parce que l'annexe sert d'arbitre — c'est-à-dire par la structure du concept 3.

Précision utile : les six autres états des dépenses ne se contredisent pas. Pour 2022, 2023 et 2024, les deux exemplaires ont des nombres de lignes très différents (499 contre 169, 421 contre 123, 540 contre 178) **mais des sommes identiques au centime**. Ce sont deux niveaux de détail du même document. **Seul 2025 porte un vrai désaccord.**

**Troisième raison : c'est le seul des trois qui produit les nombres du risque.** Annexe 1 au 31/12/2025 : trésorerie disponible **28 417,81 EUR** (contre 70 658,41 un an plus tôt), dettes fournisseurs **152 728,51 EUR** (contre 124 985,86), sommes exigibles restant à recevoir **115 629,04 EUR** (contre 40 611,67, soit ×2,85 en un an). Reste à appeler aux copropriétaires : 11 168,12 sur les opérations courantes + 53 471,73 sur les travaux = **64 639,85 EUR**. Une page qui s'appelle « contrôle des comptes » et qui ouvre sur autre chose que ces cinq nombres contrôle le détail pendant que le risque est dans l'annexe.

**Ce que je prends au concept 1 :** sa règle de partage — « de quel objet cette colonne est-elle une propriété ? » —, sa cellule-passerelle unique (un identifiant, un libellé court, un nombre ; jamais un texte de résolution ni un devis), et sa distinction entre « le syndic n'a pas fourni » et « l'outil ne sait pas lire ». **À laquelle j'ajoute une troisième valeur, obligatoire au vu de la mesure : « la pièce est au dossier, l'outil ne l'a pas reconnue »** — c'est le cas des 26 annexes mal étiquetées.

**Ce que je prends au concept 2 :** son premier écran, pas son unité de ligne. Les désaccords deviennent des **compteurs cliquables en tête de page** (même forme que la page des décisions), pas des lignes de tableau. La page reste capable d'afficher les postes où tout concorde, parce que c'est cela qu'on approuve en assemblée.

**Ce que je change au concept 3, et c'est non négociable :** sa colonne « ce qui l'autorise » ne se lit pas sur l'intitulé du compte. Elle se lit sur le **numéro** — 60 à 64 charge courante couverte par le budget voté, 671 travaux décidés par l'assemblée, 672 travaux engagés par le syndic seul, 702 appel de provision, ce qui n'est pas une dépense. La nomenclature fixe le numéro ; l'intitulé est libre et change d'un cabinet à l'autre. Un compte `67x` inconnu se dégrade en « régime non déterminé, compte 674 non répertorié ». **Et la colonne ne dit jamais « non voté » : elle dit ce qu'elle sait, jamais ce qu'elle ignore.**

**Ordre de réalisation.** D'abord le bandeau (annexe 1, annexe 2, écart entre exemplaires) : il tient avec les 32 annexes déjà au dossier, dès que celles-ci reçoivent un type documentaire propre. Ensuite le tableau des dix-huit postes. Le rattachement à un acte vient en dernier, et jamais comme colonne par défaut.

---

## 8. Ce qui reste à décider par vous

**Question 1 — Quelle pièce est la colonne vertébrale : l'état des dépenses, ou l'annexe comptable ?**
*Ma recommandation : l'annexe.* L'état des dépenses est plus détaillé et se lit parfaitement chez ce syndic (9 documents, 4 exercices), **mais le second cabinet n'en publie aucun** : 22 documents, zéro. Les cinq annexes, elles, sont présentes chez les deux. L'état des dépenses devient le niveau de détail — affiché quand il existe, annoncé comme absent quand il ne l'est pas — et jamais la fondation.

**Question 2 — Quand deux exemplaires du même exercice ne concordent pas, la page laisse-t-elle choisir, ou tranche-t-elle ?**
*Ma recommandation : elle tranche, et elle montre pourquoi.* L'annexe soumise au vote est l'arbitre. La page affiche : quel exemplaire concorde avec l'annexe, de combien l'autre s'en écarte, et sur quels postes. Sur 2025 : quatre postes, 8 672,27 EUR, dont 7 802,50 sur un seul. Le novice l'a demandé dans ces termes : « la liste des lignes qui diffèrent entre les deux ». Laisser le choix à un conseiller bénévole, c'est lui demander un arbitrage comptable qu'il ne peut pas rendre.

**Question 3 — La colonne « ce qui autorise » : rattachement manuel à une décision, ou régime d'engagement lu sur le numéro de compte ?**
*Ma recommandation : les deux, dans cet ordre, et jamais le rattachement seul.* Le régime d'engagement se remplit **sur toutes les lignes, tout de suite**, sans qu'on demande rien à personne ; le rattachement à un acte vient par-dessus quand il existe. Le rattachement seul ouvrirait la colonne vide sur 587 lignes — ce que le novice refuse de remplir, et ce qui produirait six fausses alertes sur les six résolutions les mieux exécutées du dossier. Corollaire de la question 3, à trancher aussi : la conclusion du conseil syndical va dans **un seul magasin**, la table `traces_controle` du coffre, avec le même vocabulaire des deux côtés. Elle est aujourd'hui dans deux endroits, et le geste ne marche que d'un côté.

---

## Limites de cette note

Tous mes chiffres portent sur la **structure** — combien de lignes, quel champ est rempli, quelle table est vide, quel document porte quel en-tête — jamais sur la **justesse** des montants lus. Cette instance est une instance de travail, pas un étalon : elle ne prouve rien sur l'exactitude d'un total ni sur la vérité d'un classement.

Le fichier de base du corpus porte une date de dernière modification du 2026-09-08 à 19 h 47, écrite par un autre lot que le mien : mes comptages sont une photographie, pas une constante.

Les critiques novice et expert des concepts 2 et 3 ne m'ont pas été transmises. Ce que j'écris sur ces deux concepts vient de mes propres mesures et des objections transférables du concept 1, pas d'une critique dédiée.

Les identifiants Legifrance et leurs dates de version viennent d'une lecture faite le 2026-09-08 par un autre agent ; je ne les ai pas relus. Quatre références de l'expert-comptable sont explicitement données de mémoire et **ne doivent pas entrer dans du code** avant vérification.

Enfin, la copropriété de travail est désignée ici par son pseudonyme, `Tilleuls (pseudo)`, et le second corpus par « le second cabinet ». Aucun nom réel, aucune adresse et aucun nom de cabinet ne figure dans cette note, bien qu'ils soient lisibles dans les documents mesurés.

**Scripts de mesure** (lecture seule, hors dépôt) : `C:\Users\brice\AppData\Local\Temp\claude\C--Users-brice-CoproScope-coproscope\5476f3b8-1df3-462d-a0b8-770e4a24bc55\scratchpad\synth_v1.py` à `synth_v11.py`, joués par `cd C:\Users\brice\CoproScope\coproscope\server` puis `PYTHONPATH=src .venv\Scripts\python.exe <script>`.
