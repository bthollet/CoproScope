# Fondations de la refonte documentaire - nuit du 7 septembre 2026

`RM-2026-0101` / `CH-20260907-0114-RM-2026-0101-fondations-refonte-documentaire`

Quatre lots livres, un non commence. Cette page dit ce que chacun corrige,
comment on le sait, **et ce qu'il ne couvre pas**. Elle existe parce qu'un lot
qui ne vit que dans ses messages de commit oblige le lecteur suivant a refaire
l'enquete.

Etat de la suite apres fusion de la ligne principale, lancee sans pipe avec le
code de sortie controle separement des lignes de verdict :
**1865 tests, `OK`, code 0, 2 ignores.** Aucun fichier de code au-dessus de
600 lignes.

---

## Le fil rouge

Le produit confond **trois absences** sous un meme symbole : absent du
document, absent de ma lecture, absent de mon modele. Les quatre lots
attaquent cette confusion a quatre endroits differents.

Et un second fil est apparu pendant la nuit, transverse aux lots : **une garde
fautive ne casse rien, elle rassure**. Un extracteur qui se trompe rend une
reponse fausse, qui finit par se voir ; une garde qui se trompe rend une fausse
tranquillite, indetectable par construction. D'ou la question posee a chaque
garde de cette page :

> **Quand cette garde cessera d'etre vraie, comment l'apprendra-t-on ?**

---

## L1 - Le code ne nomme plus d'entite reelle, et le biffage ne fuit plus

`2eb1c74`, complete par `ade2c36` et `a781faa`.

**Le defaut.** Une regle de biffage remplacait tout expediteur d'une ligne
`De :` par un jeton, **sauf** un cabinet nomme en clair dans l'expression.

**Ce que la mesure a montre, et qui renverse le probleme.** L'exemption ne
fonctionnait pas : le `\s*` du groupe 1 rebrousse, la sentinelle est evaluee
sur une chaine commencant par une espace, elle passe. Le nom etait donc biffe
comme les autres - sauf dans la seule forme `De:<nom>` sans espace, ou il
**survivait au biffage** et partait dans un document destine a la diffusion.
Elle ne protegeait rien et publiait un nom ; la ou elle agissait, elle fuyait.
Mesure : 1 fuite sur 7 cas avant, 0 apres.

Second defaut sous le premier : la regle n'etait pas idempotente, elle mangeait
une espace a chaque passage.

**La garde de la demo etait du code mort.** Elle cherchait un nom de
copropriete en dur dans une arborescence qu'elle venait d'ecrire depuis ses
propres litteraux : elle ne pouvait pas se declencher. Elle lit desormais
l'identite de l'instance source, **jetonisee** - le `display_name` reel porte
un suffixe technique, donc une comparaison par sous-chaine ne declencherait
jamais - et la detection structurelle passe de deux motifs locaux a sept
categories du detecteur generique du depot.

**Puis la garde elargie a ete elargie encore** (`ade2c36`) : elle validait
l'arborescence **avant** que trois fichiers y soient ecrits, dont deux
manifestes de publication ou `str(exc)` pouvait porter un chemin de l'instance
reelle. Second passage ajoute, sur l'arbre complet.

**Comment on l'apprendra si ca cesse d'etre vrai.** `a781faa` pose un test de
**portee**, pas de comportement : `individualisation` est un mot que seuls les
deux manifestes portent, donc le declarer interdit sonde exactement la zone que
la garde ne voyait pas. Preuve faite dans les deux sens - garde elargie `OK`,
seconde validation retiree `AssertionError: 'APPROVED_FICTIVE_DEMO' !=
'BLOCKED_REVIEW_REQUIRED'`.

**Ce que ce lot NE couvre PAS.**

- **Aucun test n'empeche la reintroduction d'un nom.** Le lot a retire les noms
  du code ; rien n'arrete le prochain qui les remettra. Le garde-fou statique
  reste a ecrire, et il porte un arbitrage : il doit lire ses jetons interdits
  **hors du depot**, sinon le test publie ce qu'il protege - mais sans liste
  configuree il passerait au vert sans rien regarder, la fausse tranquillite
  meme.
- **`origin/main`, la branche publique, porte 311 occurrences de noms reels
  dans 39 fichiers**, dont 29 de documentation. Nettoyer les fichiers actuels
  est faisable ; reecrire un historique deja pousse est irreversible et demande
  un arbitrage explicite.
- Environ 35 occurrences subsistent hors du perimetre du lot : `tools/`,
  fixtures de test, commentaires.

---

## L2 - Le produit cesse d'affirmer que tout est couvert quand il n'a rien evalue

`e434c3d`.

**Le defaut.** `_load_proofs` lisait la cle `proofs` ; le referentiel livre
declare `preuves`. Un mot d'ecart, **zero exigence chargee sur 26**, sur 9
instances de 12. Et la conclusion du rapport, ecrite en dur pour le cas
« rien a demander », affirmait `Toutes les pieces attendues sont couvertes.`
dix-huit lignes sous `- Pieces attendues: 0`. Les deux phrases etaient sur
disque.

Le defaut ne cassait rien : il rendait un rapport muet.

**Ce que le lot ajoute au-dela de la cle.** Les documents que l'outil n'a pas
su lire cessent d'etre invisibles : **191 documents sur 825** n'ont pas de
nature etablie - 99 sans type decide, 89 types sur le seul nom de fichier, 3 a
revoir. Ils sortent dans une section nommee et un fichier compagnon, au lieu
d'etre comptes comme des pieces absentes ou tus.

**Aucun article de loi n'a ete invente.** Les 26 exigences sortent en
« fondement non declare ». Une exigence sans source n'est pas opposable a un
syndic, et le rapport le dit desormais au lieu de la presenter comme un
manquement.

**Comment on l'apprendra si ca cesse d'etre vrai.** Les deux defauts ont ete
**remis en place** puis le fichier restaure, pour verifier que chacun fait
tomber son test. `FAILED (failures=1)` capture pour chacun.

**Ce que ce lot NE couvre PAS.**

- **`OBSOLETE` reste a zero** et ne prouve donc aucune fraicheur : la peremption
  se calcule sur `suspected_date`, qui vaut la **date de reconstruction de
  l'instance** sur 270 documents. Les dix exigences a seuil de fraicheur sont
  structurellement neutralisees. Defaut de donnees en amont, signale, non
  corrige.
- `_classification_doubts` enumere trois statuts douteux et en ignore deux -
  une liste de modalites. Non touche : le corriger deplacerait la semantique
  d'un test existant.

---

## L3 - L'ecran cite sa source au lieu de l'affirmer

`acbe472`.

**Le defaut.** 229 liens sur 229 portaient leur `page` et leur `ancre`. Le mot
`ancre` avait **zero occurrence dans tous les gabarits**. La matiere etait
complete et l'ecran l'ignorait : il affirmait sans jamais dire d'ou il tenait.

**Le piege, et pourquoi la factorisation etait la seule reponse.** La cellule
ne montre pas n'importe quelle assertion : elle montre **la plus probante**,
choisie par un tri suivi de `LIMIT 1`. Une sous-requete ecrite a cote aurait
cite la page d'une assertion **differente** de celle dont la force est
affichee - un mensonge silencieux neuf, dans le lot cense ajouter de
l'honnetete. `lien_retenu()` ecrit donc le choix **une seule fois** : force et
citation sortent du meme sous-select, donc de la meme ligne.

**Ce que l'ecran s'interdit de dire.**

| situation | ce que l'ecran dit |
|---|---|
| le registre ne nomme pas la piece | il le dit ; il n'ecrit pas `convocation du ...` sur un document sans date |
| la page n'a pas ete notee | il le dit ; il ne reconstitue pas une position |
| plusieurs assertions se disputent le controle | il dit laquelle est montree et combien il y en a, jamais **la** source |
| une date est illisible (`2016-00`) | « document dont la date n'a pas pu etre lue », jamais `00/00/2016` |

**Comment on l'apprendra si ca cesse d'etre vrai.** Un test **reinsere les
memes liens dans l'ordre inverse** : si la citation dependait de l'ordre
d'insertion plutot que du tri, il tombe. Le cas a deux assertions concurrentes
est **construit** dans le test, le corpus principal n'en portant aucun.

**Trois premisses du plan corrigees par la mesure.**

- la page n'est **pas** a 100 % : 20 des 280 liens du second coffre ont une
  ancre sans page. Page et ancre manquent independamment ;
- une piece citee sur trois n'a **aucune ligne au registre** : elle ne peut pas
  etre nommee ;
- le premier coffre cite moins que le second parce que ses 157 actes sont tous
  `PROJETEE` - la cellule d'issue y est muette, et c'est correct.

**Ce que ce lot NE couvre PAS.**

- **le conflit a deux seuils n'est pas tranche.** L'ecran dit « 1 assertion sur
  2 » et s'arrete. La regle de rang - a date egale, le rang au proces-verbal
  departage - reste un lot a part ;
- **aucun style CSS.** La classe `.cs-citation` est posee, non stylee ;
- `_actes_vues.py` etait a **600 lignes pour une limite de 600** : extraction
  prealable vers `_actes_citations.py`, qui porte exactement un concept - le
  lien retenu et de quoi le citer.

### Blueprint de l'ecran, et etat du protocole

Brouillon cible archive :
[`assets/fondations-2026-09-07/brouillon_citation_source.html`](./assets/fondations-2026-09-07/brouillon_citation_source.html).
Page autonome, cliquable, avec une bascule **« masquer les citations »** qui
restitue l'ecran d'avant, et un tableau de ce que l'ecran s'interdit de dire.
Copropriete de demonstration, aucune donnee reelle.

Structure livree : sous chaque cellule de controle, un cartouche `Source :`
prefixe en gras, heritant de la bulle existante. Un cartouche par cellule
citable, **jamais plus d'un** ; les cellules sans lien se taisent, sauf celle
qui rapporte le texte de la resolution - l'acte a bien ete lu quelque part, et
c'est le premier endroit que le lecteur veut rouvrir.

**Ecart de protocole, assume et trace.** Le protocole place la qualification
novice **avant** le dev. Elle est passee **apres**, sur arbitrage de Brice du
7 septembre 02:30 : les deux livrables - brouillon cible et page reelle - sont
poses ensemble pour qu'il compare, plutot que de juger sur un brouillon seul.
Ce n'est pas un `VISUEL_IA_WAIVED` : le visuel existe. La qualification novice,
elle, **reste due**.

---

## L4 - Un referentiel de position designe, et un repli qui ne fabriquait qu'une page

`db9c9ea`.

**Le defaut.** Le depot fabrique **sept textes differents** pour un meme PDF.
Mesure sur un proces-verbal reel de dix pages : cinq longueurs distinctes,
trois qui divergent **des le caractere 0**. Aucun n'etait designe comme la
reference - or un decalage de caractere n'a de sens que rapporte a un texte
nomme.

**Pourquoi maintenant.** L'extracteur de resolutions calcule de vrais
decalages puis n'en persiste qu'un **rang ordinal**. Aucun decalage n'est donc
stocke nulle part : le referentiel n'est pas encore trahi par des donnees. Il
le sera au premier ancrage ecrit.

**Le referentiel est le texte persiste sous `text_path`**, marqueurs de page
compris. Trois raisons, verifiees sur les 825 documents : `text_path`
renseigne 825/825, fichier present 825/825, premier marqueur au caractere 0
sur 825/825, et **nombre de marqueurs egal au nombre de pages du registre sur
825/825**.

`texte_utile` cesse d'etre un producteur concurrent : il **appelle** la
projection, donc les deux ne peuvent plus diverger. La projection est
**reversible** - depuis un decalage dans le texte projete on retrouve la
position dans le referentiel, donc la page.

**Le repli decoupait sur un caractere jamais emis.** `\f` n'est ecrit nulle
part par le producteur de texte ; le repli rendait donc **toujours une page
unique** contenant tous les marqueurs.

| | avant | apres |
|---|---:|---:|
| documents rendant une seule page | 57/57 | 0 |
| pagination juste | 0 | 57/57 |
| marqueurs restes dans le texte | 1524 | 0 |
| pages retrouvees | - | +1467 |

Et le `\f` etait doublement faux : quatre fichiers du corpus en portent trois
chacun, venus de leur propre contenu. Un document de 143 pages aurait ete
decoupe en quatre.

**Un second defaut, trouve par le test, et plus grave que le premier.** La
garde voisine mesurait la densite de texte **apres avoir compte les marqueurs
comme du contenu** - le defaut meme que ce module existe pour fermer. Les 57
documents du repli rendaient 60 a 2741 caracteres au `strip()` et **zero
caractere de document**. Ils franchissaient la garde puis etaient lus comme des
convocations a zero devis : **un fait faux sur la convocation, au lieu d'un
fait vrai sur notre lecture.** Le comptage « sans couche texte » passe de 27 a
84 sur 121.

**Comment on l'apprendra si ca cesse d'etre vrai.** 825/825 projections
identiques a la formule historique, et **2628 aller-retours verifies, zero
faux** - le caractere retrouve dans le referentiel est bien celui lu dans la
projection, et la page annoncee le contient.

**Ce que ce lot NE couvre PAS.**

- **Aucun ancrage n'est persiste.** L'outil de conversion existe ; le brancher
  est un autre lot ;
- **`extraction_level` est inutilisable pour distinguer une provenance** : il
  vaut `L1_NATIVE_TEXT_PYMUPDF` sur 825/825, **y compris les 168 documents a
  zero caractere**. L'etiquette enregistre la branche de code prise, jamais le
  resultat obtenu. Le seul couple fiable est (`status_ocr`, `text_quality`) ;
- **un huitieme systeme de coordonnees existe** : `_page_de` ancre dans un
  troisieme texte encore. Signale, non touche ;
- **la detection de frontiere par jeu de polices n'existe pas** dans le produit
  - zero occurrence de `get_fonts`, `fontname`, `get_text("dict")`. Le plan
  initial prevoyait un garde-fou dessus ; il n'avait pas d'objet.

---

## L5 - L'ancre comme objet : NON COMMENCE

Le lot n'a pas ete ouvert. Ce qui est acquis pour celui qui le reprendra :

**La base est tranchee par la mesure, pas par avis** : `gouvernance.sqlite3`.
La base de reconstruction est un cul-de-sac verifie - zero fichier
`vault_reconstruction.sqlite3` sur 14 instances, zero repertoire d'evenements,
`documents` et `event_log` absents des 7 bases existantes, et deux seuls types
d'evenements emis dans tout le produit. Y poser l'ancre reviendrait a ecrire un
enregistreur pour un journal que rien n'alimente.

**Ajouter la table ne coute aucune ligne** dans `vault/gouvernance_store.py` :
la couche est deja parametree par table, cles et colonnes. Le cout est dans
`_actes_schema.py`, qui reste a **589 lignes sur 600** - la scission prealable
est donc toujours due, meme si L3 a deja scinde son voisin.

**Deux contraintes dures, mesurees.**

- **La cle primaire doit etre juste du premier coup.** Une colonne s'ajoute
  gratuitement ; un garde-fou refuse toute ecriture ET toute lecture d'une
  table dont la cle a change, sur les 7 bases existantes.
- **`origine` ne protege pas d'un producteur voisin.** Elle ne vaut que
  `EXTRAIT` ou `CORRIGE_HUMAIN` : elle separe la machine de l'humain, jamais
  deux machines. Mesure : 130 lignes `COPROSCOPE_CALCULE` portent
  `origine = EXTRAIT` et sont donc supprimables par n'importe quel effacement
  par document.

**Decision de conception a reprendre ou a contester** : l'ancre est un fait,
pas une assertion - « page 16, sous-point 11-1 existe » ne depend d'aucun
producteur. La table serait donc en ajout et mise a jour, **jamais en
suppression par rejeu de document**, et l'on prefererait une ancre orpheline a
une reference pendante. Une ancre que plus rien ne cite est inoffensive ; une
adresse effacee sous une conclusion humaine est une corruption.

---

## Ce qui attend un arbitrage

1. **Les 311 occurrences de noms reels sur `origin/main`.** Nettoyer les
   fichiers actuels, oui ; reecrire un historique pousse, non sans decision
   explicite.
2. **Le garde-fou statique des noms** : echouer bruyamment sur un depot
   fraichement clone, ou se taire ? Les deux ont un cout, et le second est la
   fausse tranquillite.
3. **La qualification novice de l'ecran de citation**, due et non faite.
4. **`extraction_level`**, signale par deux lots et corrige par aucun.
