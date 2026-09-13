# Blueprint de la chaine, du depot au controle

Date de creation: 2026-09-03.
Auteur: designer service, voie UX `RM-2026-0049`.
Rang: **1 de l'ordre de preuve** de
[`strategie_lot_gouvernance.md`](./strategie_lot_gouvernance.md) section 6 -
l'UX sur papier, et rien de plus.
Statut: **proposition de conception soumise a contradiction.** Ni maquette, ni
gabarit, ni code. Aucun dev n'est autorise par ce document.

> **Rectification du 2026-09-09** - `RM-2026-0063` et `RM-2026-0049`, lot
> `CONV-2026-2172`. **Ce document s'appuyait sur un etalon refute le
> 2026-09-04**, et la rectification d'alors le nommait explicitement parmi les
> documents adosses a cet etalon. Il n'avait jamais recu son encadre: pendant
> cinq jours, il a continue de prescrire des valeurs qui ne tiennent pas.
>
> Ce qui ne tient pas, verifie sur les sources primaires:
>
> - **le proces-verbal de l'assemblee du 21/02/2024 n'existe pas au dossier**,
>   ni en source primaire ni ailleurs; le registre de constats du coffre le
>   reclame lui-meme comme piece a demander au syndic. Les ~~34 resolutions~~ ne
>   reposent donc sur rien. Le seul PV reellement disponible, celui du
>   03/07/2024, en porte **55**, confirme independamment par la chaine;
> - les montants ~~22 200,00~~ et ~~18 240,00~~ ne figurent dans **aucun** PV.
>   Ils proviennent d'une convocation scannee **sans aucune couche de texte**, et
>   la note d'audit qui les cite renvoie a des numeros de ligne d'un fichier
>   d'extraction qui ne contient aucun texte extrait. C'est une citation sans
>   source lisible.
>
> **Deux gestes differents ont ete appliques ci-dessous, et la difference
> compte.** Les affirmations de fait - le nombre de resolutions, l'identite de
> l'assemblee - sont corrigees en gardant l'ancienne valeur **barree**, parce
> que le mandat de `RM-2026-0063` demande de tracer la provenance fautive et non
> de l'effacer. Les **exemples de format**, eux, ont ete remplaces par des
> valeurs neutres: ils n'avaient besoin d'aucun montant particulier, et c'est
> precisement parce que ceux-la trainaient comme exemples qu'ils ont ete
> recopies dans un artefact ecrit le **2026-09-07**, soit trois jours apres leur
> refutation. Un chiffre faux laisse en exemple se propage tout seul.

Sources lues: `strategie_lot_gouvernance.md`, `modele_gouvernance_decisions.md`,
`parcours_utilisateur_tests_ux.md`, `parcours_b_controle_comptes.md`,
`protocole_agents_claude_code.md`, `CLAUDE.md`, le corpus de conception
`docs/dossiers_p0_reprise_2026-05-28/01-controle-comptes/` (**34 iterations
`CC-IT-016` a `CC-IT-049`**, trois jours de test utilisateur, un blueprint HTML
rendu), `docs/comptascope.md` a partir de la ligne 165, et le code reel des
ecrans concernes au 2026-09-03.

Schemas: `docs/assets/blueprint-chaine-2026-09-03/`
- `parcours-evenements.mmd` - section 1
- `blueprint-service.mmd` - section 2
- `chaine-legitimite.mmd` - sections 3 et 5

---

## 0. Ce que ce document decide, et ce qu'il refuse de decider

**Note de revision, ecrite apres coup et gardee expres.** Une premiere version de
ce blueprint refusait l'hypothese des cinq colonnes de la strategie section 4,
en la lisant comme cinq colonnes d'un tableau de liste. Le corpus `CC-IT` a
ete verse ensuite. Cette lecture etait fausse: les cinq colonnes sont la
transposition, a l'acte d'autorisation, de la **matrice quatre sources** deja
concue, testee et livree sur `/comptes/rapprochement`. Le verdict revise est en
section 5. La regle anti-complaisance du protocole vaut dans les deux sens: un
designer qui ne revise pas devant une mesure ne vaut pas mieux qu'un designer
qui valide tout.

Ce document decide quatre choses.

**Un.** Les deux ecrans **ne sont pas a concevoir**: ils sont a **transposer**.
La grammaire est fixee par les 34 iterations `CC-IT`. Toute invention de forme
sur cette voie est une regression, pas une contribution.

**Deux.** La matrice de gouvernance porte **six sources**, pas cinq: les cinq de
l'hypothese, plus l'execution. Motif en section 5. Sans la sixieme, l'ecran de
gouvernance ne peut pas repondre a sa premiere question.

**Trois.** Les deux matrices partagent **une charniere**: la cellule
`Decision / devis` des comptes et la cellule `Resolution` de la gouvernance
designent le meme objet. C'est le seul point de contact des deux ecrans, et
c'est ce qui les empeche de devenir deux produits.

**Quatre.** L'unite de ligne des deux files est **la rupture de chaine**,
chiffree en euros - un euro paye sans mandat, ou un euro vote qui n'a jamais ete
paye.

Il refuse d'en decider cinq autres, listees en section 6 comme arbitrages.

---

## 1. Parcours-evenements

Schema: `assets/blueprint-chaine-2026-09-03/parcours-evenements.mmd`.

Convention: `[U]` l'utilisateur emet, `[M]` la machine emet. Un evenement porte
un participe passe parce qu'il constate un fait accompli, jamais une intention.
La colonne **Existe** dit si le chemin est cable dans le code au 2026-09-03.

### 1.1 Depot et lecture

| Evenement | Emis par | Ce qu'il produit | Existe |
|---|---|---|---|
| `PIECE_DEPOSEE` | U | un fichier sous `raw/`, un manifeste de depot | oui |
| `INVENTAIRE_FAIT` | M | une ligne au registre documents | oui |
| `TEXTE_EXTRAIT` | M | un `text_path` | oui |
| `TEXTE_ABSENT` | M | un PV illisible **compte a part** - un fait a remonter, jamais une absence de resolutions | oui |
| `DOCUMENT_QUALIFIE` | M | un `document_type` | oui, **et il se trompe**: voir trou T12 |
| `QUALIFICATION_CORRIGEE` | U | le meme champ, `origine = CORRIGE_HUMAIN` | partiel |

### 1.2 Construction du mandat

| Evenement | Emis par | Ce qu'il produit | Existe |
|---|---|---|---|
| `RESOLUTIONS_LUES` | M | n lignes `CONSTATEE` au coffre gouvernance, une par resolution | oui |
| `PROJETS_LUS` | M | n lignes `PROJETEE` et les devis cites par la convocation | **non cable** |
| `EXTRACTION_REFUTEE` | M | clotures perdues, segments fusionnes, trous de sequence, taux de quantification | oui |
| `SEUILS_DATES` | M | seuils en vigueur, concurrents, expires, a une date | oui |

`EXTRACTION_REFUTEE` merite d'etre nomme comme un evenement de premier rang et
non comme un journal technique. C'est le seul moment ou la machine dit contre
quoi elle peut etre prise en defaut. L'ecran doit l'afficher; le cacher
reproduirait le defaut d'`agscope`, qui compte sans rien contre quoi se verifier.

### 1.3 Construction de l'execution

| Evenement | Emis par | Ce qu'il produit | Existe |
|---|---|---|---|
| `FACTURES_EXTRAITES` | M | n lignes de preuve facture | oui |
| `RAPPROCHEMENT_PROPOSE` | M | un statut, un motif, un doute - **jamais un rattachement muet** | oui, motif non distinctif |

### 1.4 Jonction - le tronc manquant

| Evenement | Emis par | Ce qu'il produit | Existe |
|---|---|---|---|
| `DOSSIER_CONSTITUE` | M | un `dossier_depense_id` qui tient ensemble euro, acte, devis, annexe, avis | **non** |
| `IMPUTATION_AIGUILLEE` | M | budget previsionnel, ou vote separe au sens des articles 44 et 45 | **non** |
| `CHAINE_EVALUEE` | M | 0..n ruptures, chacune **nommee, datee et chiffree** | **non** |
| `MANQUE_NOMME` (`T1b`) | M | la liste de ce qu'il faut demander au syndic, **une seule fois** | **non** |
| `POINT_OUVERT` | M | une ligne de file, ordonnee par cout du doute | partiel |

Ces cinq evenements sont le tronc. Tout le reste existe deja de part et d'autre
et ne se rejoint nulle part - le constat de completude verticale de la strategie,
verifie ligne a ligne.

### 1.5 Instruction et conclusion locale

| Evenement | Emis par | Ce qu'il produit | Existe |
|---|---|---|---|
| `DOSSIER_OUVERT` | U | rien: c'est une lecture, et elle ne doit rien ecrire | non |
| `MONTANT_ANCRE` | U | une trace vers la zone exacte du PDF | primitive oui, branchement non |
| `AVIS_CS_DECLARE` | U | `PIECE_PRODUITE` / `AFFIRME_SANS_PIECE` / `ABSENT`, avec auteur et date | **non** |
| `RATTACHEMENT_CONFIRME` / `RATTACHEMENT_ECARTE` | U | le lien acte-euro, ou son refus motive | non |
| `CONTROLE_TRACE` | U | une trace locale qui survit au redemarrage | oui, cote comptes seulement |
| `DEMANDE_CONSTITUEE` | U | un courrier envoyable **sans retouche** | oui, mais 14 891 lignes |
| `REPONSE_RATTACHEE` | U | le statut de la ligne d'origine change | non depuis les comptes |

**Le nom de l'evenement suit `CC-IT-046`:** `CONTROLE_TRACE`, jamais
`VERDICT_POSE` ni `VALIDATION`. Le mot `validation` est reserve a ce qui valide
vraiment quelque chose; le conseil syndical produit une conclusion locale, un
avis local, une trace ou une reserve.

**Regle de boucle.** `REPONSE_RATTACHEE` reboucle sur `POINT_OUVERT`, jamais sur
`PIECE_DEPOSEE`. Une reponse du syndic est une piece deposee, mais l'utilisateur
qui la rattache ne recommence pas son parcours: il ferme un point.

---

## 2. Blueprint de service en couloirs

Schema: `assets/blueprint-chaine-2026-09-03/blueprint-service.mmd`.

Les quatre temps `T1a`, `T2`, `T1b`, `T3` de la strategie section 3 sont imposes.
Voici ou ils tombent.

### T1a - l'utilisateur apporte ce qu'il a

| Couloir | Contenu |
|---|---|
| Il voit | `/documents/ajouter`. Il depose le PV, la convocation, l'annexe comptable. Il n'a rien a classer. |
| L'interface fait | accepte le lot entier, annonce ses 4 etapes, ne demande aucune decision avant d'avoir lu |
| Le back fait | `inventory`, `extract_text`, `classify`, `privacy`, `biffage` |
| Ce qui est stocke | `raw/` **jamais modifie**, registre documents |

Le depot ne demande pas a l'utilisateur de dire ce qu'est le document. Il le lit,
puis lui montre ce qu'il a compris, et accepte d'etre corrige. Demander la
qualification avant lecture, c'est demander a un benevole de faire le travail de
la machine.

### T2 - la machine travaille, et **ce temps doit etre visible**

| Couloir | Contenu |
|---|---|
| Il voit | une ligne par etape et par piece: ce qui a ete lu, ce qui a ete refuse, avec le motif du refus |
| L'interface fait | rend le journal de traitement lisible par un non-informaticien, pas un rond qui tourne |
| Le back fait | construction des registres resolutions et convocations, extraction factures, controles |
| Ce qui est stocke | coffre gouvernance SQLite, tables de preuve comptable |

`T2` n'est pas une attente a masquer, c'est le **premier livrable de confiance**.
Un PV sans couche texte, une numerotation non reconnue, une cloture perdue,
**un fichier de travail pris pour un proces-verbal**: chacun de ces faits est
affiche ici, dans les mots de l'utilisateur.

Formulation retenue, appliquant `CC-IT-027` - aucun nom de fichier brut, aucun
identifiant technique au premier niveau:

> 15 documents ont ete lus comme proces-verbaux. 4 sont des proces-verbaux
> d'assemblee. Les 11 autres sont des fichiers de travail produits par
> CoproScope: ils sont ecartes du controle.

### T1b - la machine dit ce qui manque pour instruire

| Couloir | Contenu |
|---|---|
| Il voit | **une** liste, sur les deux ecrans, qui produit **un** courrier |
| L'interface fait | un volet `Ce qu'il faut demander au syndic`, present sur les deux ecrans, alimente par la meme source |
| Le back fait | `CHAINE_EVALUEE` puis `MANQUE_NOMME` |
| Ce qui est stocke | rien de nouveau: la liste est derivee, elle se recalcule |

**Decision de conception, et c'est la plus importante du document.** Le volet
`T1b` est **partage entre les deux ecrans, pas duplique**. Deux volets alimentes
par deux calculs produiraient deux listes qui divergent, donc deux courriers,
donc douze allers-retours - ce que `T1b` existe pour eviter. Si un dev livre deux
volets, la voie a echoue meme si chaque volet est juste.

`CC-IT-043` en fixe la regle de contenu: **on ne demande que la piece que le
parcours reel permet d'obtenir.** Les sources hors d'atteinte se signalent comme
limites du controle, pas comme option principale. C'est ce qui a fait retirer le
grand livre des demandes cote comptes; la meme discipline s'applique au releve
de deliberations et aux annexes.

### T3 - l'utilisateur instruit et conclut localement

| Couloir | Contenu |
|---|---|
| Il voit | un **poste de travail**: file bornee a scroll interne, detail a cote |
| L'interface fait | file -> detail -> geste -> retour, la ligne traitee ayant quitte la file |
| Le back fait | rien, sinon enregistrer; aucun calcul n'est declenche par une conclusion |
| Ce qui est stocke | la trace, l'ancre PDF, l'avis du conseil, la piece rattachee |

Une ligne conclue **sort de la file** et ne revient pas au passage suivant.

---

## 3. Contrat des deux ecrans

### 3.0 La grammaire commune, heritee et non negociable

Ces regles ne sont pas proposees ici. Elles sont **acquises** par 34 iterations
et trois jours de test utilisateur. Les redecider serait detruire le seul capital
de conception que ce produit possede.

| Regle | Origine | Ce qu'elle impose aux deux ecrans |
|---|---|---|
| Matrice de sources, **ordre stable** | `CC-IT-020` | l'ordre des cellules ne change jamais, quel que soit l'etat |
| Une absence est une information de **premier niveau** | `CC-IT-020` | `Banque non fournie` a la meme taille que `Facture fournie` |
| Refus de conclure sur une seule source | `CC-IT-020`, `CC-IT-049` | `Facture seule: paiement non prouve.` |
| Priorite visuelle: **action -> preuves -> contexte** | `CC-IT-022`, `CC-IT-024`, `CC-IT-028` | l'action immediate precede la matrice, qui precede la fiche de piece |
| Poste de travail: file bornee + detail | `CC-IT-021` | la file ne doit **jamais** enterrer la ligne selectionnee; en largeur etroite, le detail passe avant la file |
| **Le premier viewport est un critere de recette** | `CC-IT-023`, `CC-IT-031` | mesure dans `CoproScope.exe`, pas dans un serveur web, et en pleine charge |
| Statuts publics | `CC-IT-036`, `CC-IT-038` | `Source disponible` / `A confirmer` / `Source manquante`. Jamais `missing_source`, `candidate`, `strong_match` |
| Aucun libelle brut au premier niveau | `CC-IT-027`, `CC-IT-036` | ni `*.pdf`, ni `DOC-*`, ni `L1_NATIVE_TEXT`, ni colonne technique |
| Lien seulement sur une cellule qui porte une piece | `CC-IT-033`, `CC-IT-037` | pas de bouton mort, pas de negation repetee |
| Le verbe court sur le bouton, le pourquoi a cote | `CC-IT-039`, `CC-IT-040` | `Ouvrir la piece`, et le contexte dans le texte voisin |
| Densite egale entre les cellules | `CC-IT-041` | une cellule dit ce que sa source prouve ou ne prouve pas, pas toute l'action |
| Le mot `validation` est interdit | `CC-IT-046` | `conclusion`, `avis local`, `trace`, `reserve`, `controle` |
| Ne demander que la piece obtenable | `CC-IT-043` | les sources hors parcours sont des limites, pas des options |

**Consequence de composants.** Il n'y a pas de famille `cs-gouvernance-*` a
creer. Le poste de travail existe deja sous `cs-rappro-*`
(`cs-rappro-workbench`, `cs-rappro-matrix`, `cs-rappro-matrix-grid`,
`cs-rappro-source-cell`, `cs-rappro-queue-panel`, `cs-rappro-action`). C'est le
**meme composant**, avec un autre jeu de cellules. Le systeme porte deja 354
classes `cs-*` et trois familles de ton concurrentes - `cs-tone-*`,
`cs-card-tone-*`, `cs-reprise-tone-*`. En ajouter une quatrieme pour un ecran
qui reutilise un composant existant serait une faute nette.

### 3.1 Ecran CONTROLE DE GOUVERNANCE

Sens de lecture: **du mandat vers l'execution** - la mission `assister` de
l'article 21.

**Les questions auxquelles l'ecran repond.** Trois, et pas une de plus.

1. Ce qui a ete vote a-t-il ete fait ?
2. Ce qui a ete fait l'a-t-il ete comme il avait ete vote - meme entreprise,
   meme montant, meme objet ?
3. Ce qui autorise aujourd'hui - seuils, delegations - est-il encore en vigueur ?

**Unite de ligne de la file: une rupture entre un acte d'autorisation et son
execution.** Pas une resolution. Sur ~~34~~ **55** resolutions, celles qui sont executees
conformement ne produisent aucune ligne, et une resolution d'ordre interne -
designation du president de seance - n'en produit jamais. L'inventaire des 34
reste accessible, il n'est pas la surface par defaut.

**Colonnes de la file** - la file est un panneau borne, ses cartes sont courtes:

| Element de carte | Contenu | Regle |
|---|---|---|
| Cout | l'euro en jeu, ou `-` quand rien n'a ete paye | formate `12 345,00 EUR`, jamais `12345.0` |
| Objet controle | `Assemblee du 03/07/2024, resolution 12` *(~~21/02/2024~~: PV inexistant au dossier)* + objet tronque a 90 caracteres | `CC-IT-044`: l'identite avant les preuves |
| Ce qui s'est passe | phrase courte et **distinctive**, citant la piece et le montant | 2 lignes maximum |
| Depuis | anciennete en clair: `il y a 287 jours` | jamais une date brute seule |
| Etat | `A instruire` / `Question posee` / `Controle trace` | pastille `cs-status-badge` |

Il n'y a **pas de colonne majorite** dans la file. La majorite appliquee contre
la majorite requise est un controle du detail, pas un tri de liste, et la
passerelle de l'article 25-1 en fait un generateur de faux positifs - trou n. 3
du modele. La sortir en colonne, c'est promettre un verdict qu'on ne peut pas
tenir.

**La matrice du detail: six sources.** Ordre stable, jamais modifie:

`Seuil applicable | Avis du conseil | Resolution | Annexe visee | Devis retenu | Execution`

Chaque cellule porte, dans l'ordre impose par `CC-IT-035` et `CC-IT-041`: le nom
de la source, le statut public, un libelle metier, une phrase de contexte courte,
et un lien **seulement si une piece existe**.

| Cellule | Source disponible | A confirmer | Source manquante |
|---|---|---|---|
| Seuil applicable | `Montant arrete par l'assemblee du 03/07/2024` | `Deux montants actifs a cette date: 500 et 1 000 EUR` | `Aucun montant arrete a cette date` |
| Avis du conseil | `Compte rendu fourni` (`PIECE_PRODUITE`) | `Declare sans piece` (`AFFIRME_SANS_PIECE`) | `Aucun avis rattache` (`ABSENT`) |
| Resolution | `Resolution 12, adoptee` | `Adoption non enoncee dans le texte` | `Aucun acte d'autorisation trouve` |
| Annexe visee | `Annexe 4 fournie` | `Annexe citee, correspondance a confirmer` | `Annexe visee absente du dossier` |
| Devis retenu | `Devis retenu: <entreprise>, 12 345,00 EUR` | `Un seul devis pour un montant au-dessus du seuil` | `Aucun devis rattache` |
| Execution | `Facture rattachee, 12 345,00 EUR` | `Paye 14 000,00 EUR pour 12 345,00 EUR votes` | `Rien de paye a ce jour` |

Les trois etats de l'avis du conseil syndical du modele - `PIECE_PRODUITE`,
`AFFIRME_SANS_PIECE`, `ABSENT` - se projettent **exactement** sur les trois
statuts publics deja livres. Cette coincidence n'est pas fortuite: les deux ont
ete concus pour dire la meme chose, la force probatoire d'une source. C'est
l'argument le plus fort en faveur de la transposition.

**Aide de matrice**, sur le modele de `CC-IT-049`:

> Resolution seule: execution non prouvee.

**Etats vides explicites.** Jamais d'ecran vide silencieux, et jamais une
negation repetee (`CC-IT-037`). Cinq cas, cinq textes distincts:

| Cas | Ce qui est affiche |
|---|---|
| Coffre non declare | `Le coffre local n'est pas configure pour cette copropriete.` + le geste exact |
| Aucun PV depose | `Aucun proces-verbal n'a encore ete depose. Deposez celui de la derniere assemblee: c'est lui qui pose le mandat.` |
| PV depose, sans couche texte | `Le proces-verbal du 03/07/2024 a ete depose mais n'a pas de texte lisible. Il est probablement scanne sans reconnaissance de caracteres.` |
| Resolutions lues, aucune rupture | `55 resolutions lues, aucun ecart entre ce qui a ete vote et ce qui a ete paye. Ce n'est pas une conclusion de conformite: 12 resolutions n'ont aucune facture rattachee, faute de pieces.` |
| Filtre sans resultat | `Aucune rupture ne correspond a ce filtre. 7 ruptures existent hors de ce filtre.` |

Le quatrieme est le plus important et le plus facile a rater. **Zero rupture et
zero preuve produisent le meme ecran vide.** Les distinguer est la difference
entre un outil de controle et un outil qui rassure a tort.

**Gestes offerts**, tous depuis le detail, jamais depuis la file: demander la
piece qui manque, declarer l'avis du conseil syndical, confirmer ou ecarter un
rattachement propose, poser une reserve, `Noter ce controle apres verification`
(libelle exact de `CC-IT-048`).

**Hors ecran, explicitement.** L'aiguillage 44/45 - il vit sur l'ecran comptes.
Les urgences et les delegations - tranches suivantes. Le vote de l'assemblee a
venir. L'envoi: l'ecran constitue la demande, il n'envoie jamais rien.

### 3.2 Ecran CONTROLE DES COMPTES

Sens de lecture: **de l'euro vers le mandat** - la mission `controler`.
Cet ecran **existe et il est bon**. Ce qui suit n'est pas une refonte: c'est la
liste bornee de ce que la chaine de gouvernance y ajoute.

**Les questions auxquelles l'ecran repond.** Quatre.

1. Combien a-t-on depense, et ce total est-il juste ?
2. Cet euro-la, qui l'a autorise ?
3. Cette depense avait-elle sa place dans le budget courant, ou exigeait-elle un
   vote separe ?
4. Qu'est-ce que je demande au syndic avant l'assemblee ?

**Unite de ligne: une depense dont la chaine est rompue.** Pas une facture, pas
un compte, pas un `point de controle`. Une facture en double, un devis pris pour
une facture et une ligne d'en-tete de CSV lue comme un fournisseur ne sont pas
trois depenses: ce sont trois defauts de corpus, et ils appartiennent au journal
de `T2`, pas a la file de travail de `T3`. Les melanger est exactement ce qui
produit 2 349 points.

**La matrice reste a quatre sources et n'est pas touchee.** Trois changements
seulement, tous a l'interieur des cellules existantes:

1. **La cellule `Decision / devis` cesse d'etre un balayage de mots-cles** et
   designe l'acte reel. C'est la charniere avec l'autre ecran. Voir trou T2.
2. Quand un acte existe, la cellule porte un lien vers **le detail gouvernance de
   cet acte**, pas vers un document. Verbe court: `Voir la decision`.
3. Le verdict d'imputation - articles 44 et 45 - entre dans le bloc
   `Action immediate`, **pas dans la matrice**: ce n'est pas une source, c'est un
   calcul. Formulation: `Cette depense releve de l'article 44: elle exigeait un
   vote separe, elle est imputee au budget courant.`

**Le total en tete est un objet de premiere classe**, avec sa methode affichee:
`Total des charges 2025: 128 430,12 EUR - somme de 214 lignes de l'etat des
depenses, annexe 2, page 4.` Un total sans sa methode ne peut pas etre pris en
defaut, et celui du 2026-09-02 etait faux d'un facteur cent sans que rien ne le
signale.

**Etats vides explicites**, meme discipline, cinq cas:

| Cas | Ce qui est affiche |
|---|---|
| Aucune annexe comptable | `L'annexe comptable de l'exercice 2025 n'a pas ete deposee. Sans elle, les factures n'ont rien contre quoi se rapprocher.` |
| Annexe presente, aucune facture | `L'annexe est lue: 214 lignes, 128 430,12 EUR. Aucune facture n'a encore ete deposee. Le rapprochement commence a la premiere.` |
| Exercice sans donnee | `Aucune donnee comptable pour 2024. Les exercices disponibles sont 2025 et 2023.` |
| Tout rapproche | `12 factures sur 12 se rattachent a une ligne de l'annexe. 3 d'entre elles n'ont pas d'acte d'autorisation identifie: voir le controle de gouvernance.` |
| Filtre sans resultat | `Aucune depense ne correspond a ce filtre. 9 depenses existent hors de ce filtre.` |

**Gestes offerts.** Les cinq gestes existants sont conserves tels quels, avec
leur mention exacte: cette action ajoute seulement une trace locale, elle ne
valide pas la comptabilite officielle.

**Hors ecran.** L'ecart poste par poste et les provisions au quart - tranche
budgetaire ulterieure. La repartition des charges par cle - trou n. 2 du modele,
dimension entiere, non traitee. Le fonds de travaux - trou n. 1, le plus grave.
Toute conclusion de conformite.

### 3.3 La charniere, et pourquoi elle vaut le lot

Les deux matrices se touchent en un seul point, et ce point existe deux fois:

| Matrice des comptes | Matrice de gouvernance | Meme objet |
|---|---|---|
| cellule `Decision / devis` | cellule `Resolution` | l'acte d'autorisation |
| cellule `Facture` | cellule `Execution` | l'euro paye |

Depuis les comptes, cliquer `Voir la decision` ouvre le detail de gouvernance de
cet acte. Depuis la gouvernance, cliquer sur l'execution ouvre le detail comptes
de cette depense. **C'est le meme dossier, vu du cote de l'euro ou du cote du
mandat.**

Sans cette charniere, le lot livre deux listes, et le produit gagne un cinquieme
comptage concurrent pour la meme notion. Avec elle, il livre pour la premiere
fois un parcours qui traverse.

### 3.4 Transporter la solution du poste de travail, pas seulement constater le defaut

**Mesure du 2026-09-03, recette live sur `tilleul_pseudo_test`, port 8803:**
`/ag-contentieux` fait **58 709 px** de haut, la section des resolutions commence
a **40 120 px**, et le rendu navigateur devient blanc des qu'on quitte le haut de
page. La fonctionnalite est livree et correcte, et elle est **inatteignable**.

Cause structurelle verifiee dans le gabarit: la section des resolutions est la
**neuvieme et derniere** de la page, ouverte a la ligne 287 sur 354, apres huit
autres sections dont trois grilles a deux colonnes et un tableau.

C'est exactement le defaut que `CC-IT-021` et `CC-IT-023` ont deja resolu cote
comptes. La solution est donc connue; il faut la transporter, dans cet ordre:

| Etape | Ce qu'on transporte | Origine |
|---|---|---|
| 1 | **Sortir le controle de gouvernance de `/ag-contentieux`** vers sa propre route. Une page de 58 709 px ne se corrige pas par reordonnancement. | `CC-IT-019`: une iteration utile peut retirer des blocs |
| 2 | Le poste de travail passe **avant** les indicateurs et les definitions. La file devient un panneau borne a scroll interne. | `CC-IT-021` |
| 3 | En largeur etroite, **le detail reste avant la file**. En desktop, file et detail cote a cote. | `CC-IT-021` |
| 4 | L'en-tete de travail nomme l'objet courant - `Resolution selectionnee et sources` - et ne repete pas le titre de page. Cible mesuree: 61 px. | `CC-IT-025`, `CC-IT-031` |
| 5 | La barre du haut sert le controle en cours: `Tracer le controle`, pas l'action globale. | `CC-IT-032` |
| 6 | Les indicateurs descendent **sous** le poste de travail. | `CC-IT-021` |
| 7 | Recette du premier viewport dans `CoproScope.exe`, en pleine charge, avec la position mesuree de la matrice et l'absence de scroll horizontal. | `CC-IT-023`, `CC-IT-029`, `CC-IT-031` |

**Cible de recette proposee, calquee sur celle de `CC-IT-031` et `CC-IT-046`:**
a 716 x 695 dans l'executable, en-tete de travail au plus 61 px, matrice visible
sous 520 px, six colonnes sans debordement horizontal, `Action immediate`
presente au premier ecran, aucun identifiant `DOC-*` visible.

### 3.5 La charge: ~~34~~ **55** resolutions et 700 factures

L'ecran est concu pour ce volume. La recette de `CC-IT-021` s'est faite a 827
lignes; celle-ci doit se faire au moins a la meme echelle.

| Regle | Consequence de conception |
|---|---|
| La file n'est jamais l'inventaire | l'inventaire des 34 et des 700 existe derriere un geste explicite, jamais par defaut |
| La file est bornee et **dit ce qu'elle cache** | `20 points affiches sur 214, tries par montant en jeu. Voir les 194 autres.` Une file qui tronque en silence ment |
| Le tri est nomme et modifiable | `par montant en jeu` par defaut, jamais un tri implicite |
| Le regroupement precede la troncature | 40 factures du meme fournisseur sans acte forment **une** ligne portant 40 pieces, pas 40 lignes |
| Les defauts de corpus ne sont pas des points de travail | doublons, non-factures, fichiers de travail: journal de `T2` |

Le regroupement est la seule regle qui fasse passer 700 a moins de 20 sans rien
cacher. C'est un choix de conception a eprouver au rang 3, et c'est celui qui a
le plus de chances de casser.

---

## 4. Les trous

Ce que l'ecran exige et que le back ne fournit pas. C'est le livrable qui soude
cette voie aux voies back. Ranges du plus couteux au moins couteux. Les
references `fichier:ligne` sont relatives a `server/src/coproscope/`.

### T1 - L'objet `dossier de depense` n'existe pas, et le lien acte-euro non plus

Il existe une preuve facture, une ecriture comptable, une file de rapprochement.
Il n'existe **rien** qui tienne ensemble un euro, l'acte qui l'autorise, le devis
retenu, l'annexe visee et l'avis du conseil sous un identifiant adressable.
Verifie: aucun `resolution_id`, `acte_id` ou `devis_id` dans le viewmodel comptes
ni dans ses trois gabarits.

Consequence UX: **la charniere de la section 3.3 n'a rien a relier.** Sans `T1`,
ce lot livre deux listes et un cinquieme comptage concurrent. C'est le trou de
tete, et il commande les quatre suivants.

### T2 - La quatrieme source du rapprochement est un mirage

La cellule `Decision / devis` ne lit aucun champ structure. Elle applique un
balayage de mots-cles sur la concatenation de **toutes** les valeurs de la ligne
(`web/compta_rapprochement_view.py:337-345`, texte construit par `_row_text` en
`:599`). Elle rend `candidate` ou `missing_source` selon la presence des mots
`decision`, `devis`, `vote` n'importe ou dans la ligne.

Consequence UX: l'ecran designe comme `le meilleur ecran du produit` porte une
cellule dont la valeur ne provient d'aucune donnee. Et c'est precisement la
cellule qui doit devenir la charniere. **Corriger T2, c'est livrer la moitie du
lot.**

Corollaire mesure au meme endroit: la source `Banque` lit trois champs
(`mouvement_bancaire`, `bank_reference`, `releve_bancaire`) qui **n'existent dans
aucun schema de la file de revue**. Elle est donc structurellement toujours
`Source manquante`. C'est defendable au titre de `CC-IT-020` - une absence est un
fait actionnable - mais il faut le savoir: la cellule ne peut pas changer d'etat,
quoi qu'on depose.

### T3 - Le devis n'existe pas comme objet du cote proces-verbal

L'objet `DevisCite` existe, avec entreprise, montant TTC, etat du prix,
discordance intitule/corps - mais **uniquement pour les convocations**. Cote PV,
l'objet `Resolution` porte `montant_seuil` et n'a ni entreprise ni montant vote.

Consequence UX: la cellule `Devis retenu` de la matrice de gouvernance ne peut
pas etre remplie, et l'etalon de la tranche verticale de reference - deux devis dont l'un rejete
et l'autre adopte - a ete **REFUTE le 2026-09-04**: ces montants ne figurent
dans aucun proces-verbal (voir la rectification en tete). La cellule reste
infaisable, mais pour une raison plus forte que l'etat de l'objet. Le rang 2 de l'ordre de preuve ne peut pas conclure sans cet objet.

### T4 - Rien n'aiguille une facture entre budget previsionnel et vote separe

Le modele designe ce test comme celui qui vaut le plus. Le vocabulaire de
qualification porte `BUDGET_PREVISIONNEL` et `FONDS_TRAVAUX` **cote resolution**;
rien ne teste une facture au sens des articles 44 et 45. Le cas du remplacement
assimile a de la maintenance seulement si son prix est compris forfaitairement au
contrat exige en outre de lire le contrat.

Consequence UX: la question 3 de l'ecran comptes reste sans reponse, et le moyen
le plus simple de depenser sans faire voter reste invisible.

### T5 - Les motifs sont des constantes, donc le critere `zero motif identique` est inatteignable

Le motif d'une ligne provient d'une phrase codee en dur par classe de statut
(une par branche dans `modules/_accounting_parts/03_invoice_reconciliation.py`).
Rien n'y interpole le montant, le fournisseur ni la ligne en cause.

Consequence UX: la gate `UX` porte le seuil `0 motif strictement identique sur
deux lignes`. Elle **ne peut pas etre franchie** sans reecrire la generation des
motifs. Ce n'est pas un defaut d'affichage a corriger cote front.

### T6 - L'avis du conseil syndical n'a ni stockage, ni formulaire, ni frontiere

Les trois etats sont specifies dans le modele et se projettent exactement sur les
trois statuts publics deja livres. Aucune table, aucun champ, aucune route. La
regle dure - un `AFFIRME_SANS_PIECE` ne franchit jamais la frontiere vers une
sortie destinee a un tiers - n'a donc rien a garder aujourd'hui, et devra etre
appliquee dans **chaque** export le jour ou le champ existera.

C'est aussi une **surface de fuite nouvelle**: champ de saisie libre, avec auteur
nomme. Relecture QA privacy obligatoire avant tout dev.

### T7 - Le renvoi vers la zone du PDF a un emetteur et pas de recepteur

La file de rapprochement produit des liens de la forme
`/documents/{doc_id}?source=compta&evidence=montant&value=...`
(`web/compta_rapprochement_view.py:284`, meme motif en
`web/factures_review_view.py:210`). La route qui les recoit ne lit jamais les
parametres de requete (`web/_app_fragments/part_003.pyfrag:324-336`).

`CC-IT-033` l'avait deja dit sans ambiguite: le lien donne le montant a chercher,
`cela n'autorise pas encore une zone PDF automatique`. Le contrat etait donc
honnete cote UI. Ce qui manque est le recepteur, et la primitive `pdftrace` qui
le ferait existe et n'est branchee que sur le detail document.

### T8 - La lecture des convocations n'est appelee par aucun pipeline

Le depot n'appelle que la construction du registre des resolutions
(`web/depot.py:410` et `:453`). La construction du registre des convocations
n'est appelee que par les tests.

Consequence UX: la moitie `PROJETEE` du modele - ce que le conseil a propose
contre ce que l'assemblee a vote - n'entre jamais dans le coffre par l'interface.
Cout de correction: faible. Cout de l'absence: eleve.

### T9 - Le seuil est calcule mais jamais compare a un montant

La fonction qui rend l'etat des seuils de l'article 21 a une date existe, avec
ses drapeaux d'ambiguite (`seuils_concurrents`, `reprise_seuil_anterieur`). Rien
ne compare le montant d'une depense a ce seuil.

Consequence UX: la cellule `Seuil applicable` existe en donnee et pas en constat.

### T10 - Cote comptes, l'absence de source et l'absence de resultat sont indiscernables

La lecture d'un fichier absent rend une liste vide, exactement comme un fichier
present et vide (`core/_common_parts/01_io_and_instance_config.py:189-190`, et
son enveloppe en `web/viewmodels/_base.py:78-80`).

Le cote gouvernance a deja resolu le probleme: `web/resolutions_view.py` rend
`registre_absent` et `registre_vide` avec leur message et leur geste. **La forme
est bonne, elle est a reprendre telle quelle cote comptes.** C'est le seul point
ou la gouvernance a de l'avance sur les comptes.

### T11 - Deux pieges pour le dev, a signaler avant qu'il ne s'y perde

1. Un modele UX comptes riche - categories, pieces, alertes, questions, facettes,
   douze etats vides - est **construit et jamais rendu**: le gabarit consomme un
   autre modele. Un dev qui lit le viewmodel croira le contrat deja livre.
2. La route `/comptes` ne recoit aucun parametre de requete
   (`web/_app_fragments/part_003.pyfrag:227`), alors que le viewmodel produit des
   liens de filtre et d'export. Tous ces liens sont morts.

### T12 - La qualification verse des fichiers de travail dans les proces-verbaux

Mesure du 2026-09-03: **15 documents classes `PV_AG` pour une seule assemblee
reelle, dont 11 fichiers de travail produits par CoproScope lui-meme.**

Consequence UX directe: la file de gouvernance affichera quinze assemblees. Le
compte affiche sera faux d'un facteur quinze, et l'utilisateur perdra confiance
avant d'avoir lu une seule resolution - le meme mecanisme exact que les quatre
pseudo-factures a 5 285 937,26 EUR extraites d'un CSV de tableau de bord, qui
faisaient 96 pour cent du total des charges.

C'est le prerequis `DONNEES` de la strategie, et il est **bloquant pour cette
voie**: aucun ecran ne rattrape un corpus de cette qualite.

### T13 - Un identifiant technique apparait comme titre d'assemblee

Mesure du 2026-09-03: l'en-tete affiche `Assemblee du DOC-729CCCF88863` quand la
date manque.

Cause verifiee, et elle est structurelle, pas cosmetique. L'identifiant
d'assemblee retombe sur le `doc_id` quand la date suspectee est vide
(`modules/_resolutions_registre.py`, fonction `_ag_id`), puis la vue fabrique la
date affichee en retirant le prefixe (`web/resolutions_view.py`, champ `date` de
l'assemblee). **Le `doc_id` arrive donc dans le libelle par construction**, pas
par accident d'affichage.

`CC-IT-027` et `CC-IT-036` ont deja tranche la regle: les identifiants `DOC-*`
restent utiles aux liens, aux tests et aux traces internes, jamais au premier
niveau. Libelle de remplacement propose:
`Assemblee sans date lue - proces-verbal du 12/03/2024 (date de depot)`.

### T14 - Le poste de travail n'est pas transporte, et la page est inatteignable

58 709 px, resolutions a 40 120 px, rendu blanc au-dela du haut de page. Detail
et remede en section 3.4. Ce trou est le moins couteux de la liste - la solution
est ecrite et livree ailleurs - et c'est celui qui rend la fonctionnalite
utilisable ou non.

---

## 5. Verdict sur l'hypothese des cinq colonnes

**Verdict: retenue.** Les cinq colonnes de la strategie section 4 sont la
transposition correcte, a l'acte d'autorisation, de la matrice quatre sources de
`CC-IT-020`. Je la retiens avec **un ajout et deux reserves mesurees**.

### Pourquoi la transposition est correcte, et pas seulement plausible

Quatre convergences, chacune verifiable dans le corpus.

**Un. Meme grammaire de cellule.** `CC-IT-020` fixe la forme: une source, un
statut, un libelle metier, une phrase courte, un lien seulement s'il y a piece.
Les cinq colonnes decrivent exactement cinq sources de cette forme. `Seuils`
n'est pas une exception apparente: le modele est explicitement recursif - les
seuils sont eux-memes une resolution de l'assemblee anterieure. C'est donc une
source, avec sa piece, comme les autres.

**Deux. Meme doctrine de l'absence.** `CC-IT-020`: une absence est une
information de premier niveau, jamais une note de bas de page. La strategie:
`un trou dans chaque colonne porte un nom different`. C'est la meme phrase, dite
deux fois a quatre mois d'ecart par deux chemins independants.

**Trois. Les trois etats de l'avis du conseil syndical se projettent exactement
sur les trois statuts publics.** `PIECE_PRODUITE` sur `Source disponible`,
`AFFIRME_SANS_PIECE` sur `A confirmer`, `ABSENT` sur `Source manquante`. Un
modele juridique ecrit sans connaissance de l'UI et une UI ecrite sans
connaissance du modele tombent sur la meme partition a trois classes. Ce n'est
pas une coincidence: les deux mesurent la force probatoire d'une source.

**Quatre. Le modele donne la raison de fond.** L'atome est l'acte d'autorisation,
et **les natures derivees valent par leurs liens**, pas par une propriete propre.
Une matrice de sources est la forme exacte pour afficher des liens obligatoires
dont l'absence est un constat nomme. Ce n'est pas une analogie: c'est le meme
objet.

### Ce que j'ajoute: une sixieme source

**Les cinq colonnes ne portent pas l'execution.** Or la premiere question de
l'ecran de gouvernance est `ce qui a ete vote a-t-il ete fait ?`, et la sortie
propre du modele est le `taux d'execution des resolutions`. Cinq colonnes toutes
tournees vers la legitimite de la decision ne peuvent y repondre.

Sans sixieme cellule, deux consequences se produisent ensemble: l'ecran de
gouvernance ne repond pas a sa question principale, et les deux matrices ne se
touchent nulle part - donc deux produits.

La sixieme est `Execution`, et c'est elle qui porte les constats les plus chers
du produit: `votee, rien de paye`, `paye 14 000 pour 12 345 votes`, `paye a une
autre entreprise que celle votee`.

### Reserve mesuree n. 1 - la sixieme colonne a un cout, et il est chiffre

`CC-IT-031` mesure quatre colonnes de **155,3 px** a 716 px de fenetre dans
`CoproScope.exe`. Six colonnes a la meme largeur utile donnent environ **103 px**
par cellule. Et a 155 px il avait deja fallu, en trois iterations successives,
raccourcir `Voir la piece dans DocOps` en `Ouvrir la piece` (`CC-IT-039`),
remplacer le detail long par `DocOps: piece a controler.` (`CC-IT-040`), puis
compacter les details `Banque` et `Decision / devis` (`CC-IT-041`).

Autrement dit: la matrice a quatre colonnes etait **deja a sa limite de densite**
a 716 px. Six colonnes ne tiennent pas par simple division.

Ce que je propose, et qui reste dans la doctrine: **deux rangees nommees de trois
cellules**, jamais un repli a deux colonnes que `CC-IT-029` reserve aux largeurs
tres etroites.

> Ce qui autorisait: `Seuil applicable | Avis du conseil | Resolution`
> Ce qui a ete engage: `Annexe visee | Devis retenu | Execution`

L'ordre reste stable, la lecture reste de gauche a droite, la chronologie de la
legitimite est preservee, et chaque cellule retrouve 155 px. Le decoupage n'est
pas arbitraire: il separe le mandat de son execution, c'est-a-dire exactement les
deux missions de l'article 21.

**Ceci est une proposition a mesurer, pas une conclusion.** La preuve est une
mesure dans `CoproScope.exe` a 716 x 695, comme `CC-IT-029` et `CC-IT-031`.

### Reserve mesuree n. 2 - deux cellules du dossier ne sont pas des sources

`L'obligation declenchee` - ce que le montant impose au vu du seuil - et
`l'imputation` au sens des articles 44 et 45 sont des **verdicts calcules**, pas
des sources. Les mettre en cellule violerait `CC-IT-038`: un statut court dit
l'etat de decision attendu, pas la categorie interne qui a servi a colorer la
carte. Un statut `Source manquante` sur une case qui n'est pas une source est un
contresens.

Leur place est le bloc `Action immediate`, qui porte deja par contrat la raison
courte du doute (`CC-IT-022`). Formulations proposees:

> Au-dessus du seuil de consultation du conseil syndical arrete a 1 000 EUR.
> Cette depense releve de l'article 44: elle exigeait un vote separe.

### Ce que je retire de ma premiere version

Ma premiere lecture proposait sept stations verticales au lieu d'une matrice
horizontale, en argumentant que la largeur d'ecran est une ressource rare. Cet
argument est **faux ici, et le corpus le prouve**: `CC-IT-028` et `CC-IT-029` ont
mesure que la matrice horizontale tient, et `CC-IT-021` a mesure que c'est la
**hauteur** qui est la ressource rare - une file trop longue enterre la ligne
selectionnee. Concevoir en vertical aurait reproduit le defaut des 58 709 px que
l'on cherche precisement a corriger.

Ce qui survit de cette premiere version: les deux cellules qui ne sont pas des
sources, la sixieme source, et le fait que la matrice appartient au detail et
jamais a la file.

---

## 6. Ce que je n'ai pas pu trancher

Cinq arbitrages. Aucun n'est un detail de mise en page; chacun change ce que le
back doit produire.

**A. La resolution restee lettre morte n'a pas d'euro.** La contrainte `l'unite
de travail est la depense` rend invisible une resolution votee et jamais
executee - or le `taux d'execution des resolutions` est l'une des deux sorties
propres du modele. Ma proposition: l'unite devient **la rupture, exprimee en
euros ou dans l'absence de l'euro qui avait ete vote**. C'est une reformulation
de la contrainte, pas une exception. **A confirmer par Brice.**

**B. Ou vit le controle de gouvernance.** La strategie dit que l'espace
gouvernance **absorbe** `/ag-contentieux` et une partie de `/gouvernance`, sans
vingt-sixieme entree de navigation. Mais `/ag-contentieux` fait 58 709 px et la
section resolutions y est neuvieme sur neuf: le poste de travail ne peut pas y
tenir sans en retirer huit sections. Absorber ou extraire n'est pas la meme
decision politique. **Je recommande d'extraire** - une route dediee, et
`/ag-contentieux` garde la passation - mais c'est un arbitrage de navigation.

**C. Six cellules en deux rangees, ou cinq en une.** Ma reserve n. 1 propose deux
rangees de trois. L'alternative est de garder une rangee unique de cinq et de
laisser l'execution hors matrice. Elle est plus fidele a la lettre de la
strategie et plus proche de la forme livree; elle coute la reponse a la premiere
question de l'ecran. **La mesure a 716 px doit trancher, pas une preference.**

**D. Les seuils concurrents.** Deux seuils adoptes actifs sur la meme periode,
500 EUR sans terme et 1 000 EUR pour 24 mois. Le back refuse deliberement de
trancher. Mais la cellule `Seuil applicable` doit afficher **un** montant pour
dire si une depense le depasse. Afficher les deux est honnete et illisible;
afficher le plus recent, c'est faire trancher une question de droit par une
regle d'affichage. Le statut `A confirmer` permet de tenir sans conclure, mais
il ne dit toujours pas quel montant sert au calcul. **Je refuse de trancher dans
un blueprint.**

**E. Le plafond des 20 points.** Le seuil est defini `sur le corpus restreint`.
Sur 700 factures il n'est pas defini, et c'est precisement la que se joue le
produit. Trois lectures: plafond de generation, plafond d'affichage, ou objectif
de qualite de regle. Ma conception suppose la deuxieme, avec le nombre cache
affiche. **A confirmer**, parce que la premiere obligerait le back a classer
avant de produire, ce qui est un tout autre travail.

---

## 7. Condition d'arret

Le blueprint est ecrit, les trous sont listes. Aucun gabarit, aucun CSS, aucune
route n'a ete ecrit et aucun ne doit l'etre sur la base de ce document seul: le
rang 2 - predicats back sans interface - et le rang 3 - maquette reelle en pleine
charge, mesuree dans `CoproScope.exe` - sont devant.
