# Strategie du lot gouvernance - de l'UX au back-end

Date de creation: 2026-09-02.
Modele de reference: [`modele_gouvernance_decisions.md`](./modele_gouvernance_decisions.md).
Protocole applicable: [`protocole_agents_claude_code.md`](./protocole_agents_claude_code.md).
Statut: proposition de strategie, non validee, non inscrite au gouvernail.

## 1. Le principe strategique

**Construire une tranche verticale mince, pas une couche horizontale complete.**

Ce n'est pas une preference de methode, c'est une reponse au defaut constate. Le
depot porte 25 entrees de navigation, 44 gabarits, 61 693 lignes de source et
30 067 lignes de tests. Et le 2026-09-02, sur l'interface reelle: le cockpit
annonce 93 actions pendant que la page des actions en affiche zero, quatre
comptages differents coexistent pour la meme notion, le total des charges est
faux d'un facteur cent, et des ecrans affichent une identite fictive sur des
donnees reelles.

Ce produit n'a pas manque d'ampleur. Il a manque de **completude verticale**:
aucun parcours ne va d'un bout a l'autre en donnant un resultat juste.

Regle du lot, donc: **une seule depense, du PV au verdict, entierement juste**,
avant toute generalisation. Une tranche qui traverse les trois couches vaut mieux
que trois couches qui ne se rejoignent nulle part.

## 2. La tranche verticale de reference

Le premier livrable, celui qui prouve tout le reste:

> Un membre du conseil syndical importe le PV de l'AGE du 21 fevrier 2024.
> L'ecran lui montre les resolutions adoptees. Il en choisit une. Il voit ce qui
> l'autorise, ce qui l'execute, et ce qui manque. Il clique sur un montant et
> atterrit sur la ligne exacte du PDF qui le porte. Il tranche, et son verdict
> survit a la fermeture de l'application.

Cette tranche a une propriete rare: **son resultat est connu d'avance**, etabli a
la main. On ne juge donc pas a l'allure, on compte les ecarts.

> **Rectification du 2026-09-04** - `RM-2026-0050`, lot `CONV-2026-2121`.
> La version du 2026-09-02 chiffrait ici l'etalon ainsi: trente-quatre
> resolutions, toutes sous la majorite de l'article 24, resolution 29 rejetee,
> resolutions 30 et 33 portant `Pas de vote`, devis BATIMEX 22 200,00 rejete et
> WE GROUP 18 240,00 adopte. **Verification faite sur les sources primaires,
> aucun de ces points ne tient**, et le PV de l'AG du 21/02/2024 n'existe meme
> pas au dossier.
>
> Le principe de la section reste entier, et il en sort renforce: une tranche
> verticale doit se juger contre un etalon, et non a l'allure. Ce qui change est
> que l'etalon de reference devient celui de
> [`etalon_corpus_tests_ux.md`](./etalon_corpus_tests_ux.md), etabli a la main
> avant tout traitement outil, sur des sources primaires: **55 resolutions au PV
> du 03/07/2024**, 39 adoptees, 7 rejetees, 8 `Pas de vote`, et une dont le PV
> n'enonce jamais l'issue. Le **total des charges 2025 est de 357 493,10 EUR**,
> recalcule cle de repartition par cle de repartition.
>
> Il faut en tirer la lecon exacte, parce qu'elle vaut au-dela de ce document:
> l'etalon cite ici avait ete repris d'une note d'audit qui renvoyait a des
> numeros de ligne d'un fichier d'extraction vide. Une reference precise n'est
> pas une preuve. C'est le meme mode de defaillance que celui decrit en section
> 1: **ce qui parait plausible et solidement source peut etre faux.**

Perimetre exclu de la tranche: le budget previsionnel et son aiguillage 44/45,
les urgences, les delegations. Ils entrent dans les tranches suivantes, une par
nature d'acte.

## 3. Couche UX

**L'unite de travail est la depense, jamais le document.** Un document seul ne se
controle pas; il ne prend son sens que comme piece d'un dossier de depense. Toute
la conception decoule de la: si un ecran demande a l'utilisateur de raisonner sur
un document, il est faux.

**Deux sens de lecture, une seule table.** De la depense vers le mandat, c'est
*controler*. Du mandat vers l'execution, c'est *assister*. Ce sont les deux
missions du conseil syndical enoncees a l'article 21, et ce sont les deux
directions du meme objet. L'outil n'impose donc pas de chronologie: il accepte
d'entrer par n'importe quel bout.

**Mais un premier usage a besoin d'un premier pas.** Modele sans chronologie,
parcours d'amorcage avec chronologie. Le premier pas est le PV de l'annee
precedente, parce qu'il pose le mandat avant l'execution et qu'il produit
immediatement quelque chose de visible: une ligne par decision.

**Le rythme du parcours**, en quatre temps dont un cache:

| Temps | Qui agit | Ce qui se passe |
|---|---|---|
| `T1a` | l'utilisateur | il apporte ce qu'il a: le PV, l'annexe comptable |
| `T2` | la machine | lecture, extraction, construction des lignes - **ce temps doit etre visible** |
| `T1b` | la machine | elle dit ce qui manque pour instruire: la liste devient la demande au syndic |
| `T3` | l'utilisateur | instruction: il prend une depense, regarde si les voies se rejoignent, tranche |

`T1b` est le vrai livrable du premier temps. Il soude ce lot au parcours des
pieces manquantes au lieu de le juxtaposer: l'utilisateur fait **un** deplacement
vers le syndic avec une liste fondee, pas douze allers-retours.

**Les trois etats de l'avis du conseil syndical**, parce que la realite est que
beaucoup de conseils n'ont pas de compte rendu: `PIECE_PRODUITE`,
`AFFIRME_SANS_PIECE`, `ABSENT`. Le deuxieme est un champ de saisie libre, avec sa
phrase a la premiere personne et sa consequence affichee. Voir le modele,
section 8.

**Les criteres UX qui font echouer le lot**, et ils sont chiffres:

| Critere | Seuil |
|---|---|
| Points a traiter generes sur le corpus restreint | au plus 20 - une soiree |
| Motifs strictement identiques sur deux lignes | 0 - un texte repete n'est pas un diagnostic |
| Travail retrouve apres redemarrage | integral |
| Ecran affichant une identite fictive sur des donnees reelles | 0 |
| Retouches necessaires avant envoi d'un livrable | 0 |

## 4. Couche front

**L'espace gouvernance absorbe, il ne s'ajoute pas.** Il reprend
`/ag-contentieux` et une partie de `/gouvernance`. Pas de vingt-sixieme entree de
navigation. C'est le seul moment ou reduire la barre laterale sera politiquement
facile, parce que ca se presente comme un regroupement.

**Hypothese de disposition, a eprouver par le designer, pas a decider ici:** cinq
colonnes lues de gauche a droite comme la chronologie d'une decision legitime -
seuils, avis du conseil syndical, resolution, annexes, devis retenu. Un trou dans
chaque colonne porte un nom different. Cette disposition est une entree pour la
conception, pas une conclusion.

**La primitive existe deja.** Le module `pdftrace` ancre une valeur vers une zone
de PDF: pre-annotation, desambiguisation de ligne, file `/pdf-traces`. Ce sont les
trois derniers commits de la branche courante. Le renvoi cliquable vers l'annexe
exacte n'est pas a inventer, il est a brancher.

**Deux regles d'etat, tirees des defauts constates:**

1. **Jamais d'ecran vide silencieux.** Registre absent, extraction non lancee,
   instance non configuree: chaque cas rend un etat **explicite** disant ce qui
   manque et comment le construire. C'est l'inverse exact du defaut ou une source
   absente rend une liste vide et fait croire qu'il n'y a rien a faire.
2. **Jamais d'identite fictive sur des donnees reelles.** Sept vues substituent
   aujourd'hui `Copropriete FICTIVE` quand un modele partiel manque, tout en
   affichant les vraies lignes. Le nouvel espace n'herite pas de ce motif.

**Epreuve de charge obligatoire.** Toute maquette et tout ecran livre est teste au
moins une fois avec trente-quatre resolutions et sept cents factures. Un ecran qui
n'a ete vu qu'avec cinq lignes bien rangees n'a pas ete vu.

## 5. Couche back

**Quatre decisions a figer avant d'ecrire, parce qu'elles coutent cher apres.**
Elles sont independantes du contenu du modele: que l'atome change, que le fonds de
travaux entre, que les cinq bases deviennent sept, elles restent vraies.

1. **Le registre est transverse aux exercices.** Le reste de l'app est scope a
   l'annee - les viewmodels prennent un `year`, le bandeau affiche
   `Exercice 2025`. Or une delegation votee en 2023 couvre une depense de 2024, et
   une urgence de 2024 se ratifie en 2025. Un registre decoupe par exercice tue le
   modele: aucun lien arriere ni avant ne traverserait la frontiere. **Fichier
   unique et cumulatif, l'exercice est une colonne.**
2. **Les corrections humaines survivent a la re-extraction.** Colonne `source`
   valant `EXTRAIT` ou `CORRIGE_HUMAIN`; une re-extraction n'ecrase jamais un
   `CORRIGE_HUMAIN`, elle ecrit a cote et signale la divergence. Cette divergence
   est elle-meme une information.
3. **L'identite d'un acte est stable.** `acte_id` derive du couple (date d'AG,
   numero de resolution), jamais d'une empreinte du texte - sinon un nouvel OCR
   fabrique des doublons, dans un corpus qui en porte deja quatre par document.
4. **Pas de troisieme source de verite.** L'app en a deja deux qui se
   contredisent. Le registre de gouvernance est lu directement par le viewmodel et
   n'entre pas dans le read model tant qu'aucun besoin ne l'exige.

**Points d'insertion:**

| Ou | Quoi | Nature |
|---|---|---|
| `instance.yml` | cle `registers.actes_autorisation` | additive; le motif est etabli, `tilleul_pseudo_test` declare deja trois registres absents de `synthetic_copro` |
| `schemas/` | `acte_autorisation.schema.json` | et corriger `ag_resolution.schema.json`, mal nomme et reference par rien |
| `modules/` | module decoupe des la conception: extraction, predicats, aiguillage, projections | par responsabilite, pas par taille |
| `core/pipeline.py` | une etape apres `classify`, avant `compute_kpis` | 17 lignes aujourd'hui |
| sorties ComptaScope | colonnes `acte_autorisation_id`, `motif_rattachement`, `doute` | additives |
| `registre_ag.csv` | **intouche** | du code et des tests en dependent; il devient la source d'extraction |

**Comportement en l'absence du registre, verifie:** `InstanceConfig.register()`
leve `KeyError` quand la cle manque. C'est le bon comportement - il echoue fort.
Le viewmodel l'attrape et rend l'etat explicite de la section 4.

## 6. L'ordre de preuve

Il ne suit pas l'ordre des couches, et c'est deliberé.

| Rang | Quoi | Pourquoi la |
|---|---|---|
| 1 | **UX sur papier** - blueprint, parcours-evenements | le moins cher, et il contraint tout le reste |
| 2 | **Predicats back, sans interface** | ils prouvent le modele, et ils sont entierement testables sans ecrire un gabarit |
| 3 | **Maquette front reelle**, en pleine charge | elle confronte le blueprint aux vraies donnees avant que le code d'ecran existe |
| 4 | **Ecran livre** | seulement quand les trois precedents ont tenu |

Le point contre-intuitif est le rang 2. L'usage veut qu'on finisse par le
back-end; ici c'est l'inverse, parce que **le risque est dans le modele, pas dans
les pixels**. Un registre et ses predicats se verifient contre un etalon connu
sans qu'aucun ecran existe. Vu l'etat de l'interface actuelle, c'est decisif:
l'ecran est la partie chere, et c'est celle qui porte deja toutes les
incoherences.

## 7. Gates

| Gate | Condition de passage |
|---|---|
| `MODELE` | phase `red-team borne` tenue; les six trous de la section 13 bis du modele instruits; contradictions arbitrees par Brice |
| `DONNEES` | les trois prerequis soldes: deduplication x4, fichiers d'outillage hors registre, `return []` corrige |
| `PREDICATS` | ecart nul contre l'etalon des trente-quatre resolutions |
| `UX` | GO novice sur la maquette en pleine charge, et les cinq criteres chiffres de la section 3 |
| `LIVRAISON` | tests verts, capture de l'ecran reel, comptage 600 lignes |

Aucune gate ne se franchit sur une note. Chacune se franchit sur une preuve
executable: un chiffre, un test, une capture.

## 8. Risques

| Risque | Ou il mord | Attenuation |
|---|---|---|
| Le modele est faux | tout le lot | `red-team borne` avant code; les quatre decisions back sont choisies pour survivre a un changement de modele |
| L'extraction des PV est peu fiable | rang 2 | mesure contre l'etalon connu; un taux d'extraction insuffisant arrete le lot au lieu de le degrader |
| Le corpus reste pollue | rang 2 | gate `DONNEES` bloquante |
| L'ecran noie l'utilisateur | rang 4 | seuil des 20 points, mesure sur corpus restreint |
| Le travail de l'utilisateur ne survit pas | rang 4 | decision back n. 2, verifiee par redemarrage effectif |
| Le lot s'etale horizontalement | partout | une seule nature d'acte par tranche; les urgences et delegations attendent |

## 9. Hors perimetre du lot

La refonte de la navigation au-dela de l'absorption citee; le read model SQLite;
les six autres parcours utilisateur; le rattachement automatique facture vers
decision au-dela d'une proposition avec son doute; la selection automatique du
devis retenu sans confirmation humaine.

## 10. Inscription au gouvernail

Le lot est a inscrire comme un `RM-*` unique, avec une ligne vivante dans
`docs/presence_agents.md`. Le texte propose est tenu pret et n'est pas ecrit tant
que cette strategie n'est pas validee: inscrire au gouvernail une strategie non
eprouvee reviendrait a la graver.
