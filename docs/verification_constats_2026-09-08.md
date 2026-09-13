# Les 16 constats declares ouverts sont-ils encore ouverts ? - verification du 2026-09-08

`RM-2026-0086` / `CH-20260908-1730-RM-2026-0086-verifier-avant-de-decouper`

Ce document repond a une consigne de Brice, enregistrement 7 du 2026-09-08,
avant toute decoupe de l'item en lots:

> « Pour le 0.86, c'est penible. Je pense qu'on a deja traite plusieurs fois les
> sujets. Donc OK pour le dedoubler, mais **verifie que ce n'est pas deja fait
> avant**. J'ai l'impression qu'on a vraiment travaille tous les points deja.
> Donc je pense que **c'est une scorie d'un git mal gere**. »

Chaque constat a ete **rejoue contre le code du jour**, jamais relu contre le
document de verdicts. Le present lot ne corrige rien: il mesure.

---

## 1. Le chiffre que Brice attend

**Zero.**

Sur les 16 constats, **aucun n'etait deja corrige avant le 2026-09-05 tout en
etant declare ouvert**. L'hypothese de la scorie de git n'est pas confirmee pour
ces 16 constats, et elle est refutee par une mesure directe et non par une
impression.

La mesure qui tranche: pour chaque ligne de code mise en cause, la pioche
`git log --all -S'<ligne>' -- <fichier>` - donc **toutes branches confondues, y
compris celles qui ne sont pas ancetres de la branche courante** - ne rend
qu'**un seul commit**, celui qui a introduit la ligne les 2 et 3 septembre.
Aucun commit ne l'a jamais modifiee, nulle part.

| Constat | Ligne de defaut | Commits l'ayant touchee, toutes branches |
|---|---|---|
| C037 | `totaux[-1]` | `7153d91` 2026-09-03 - et rien d'autre |
| C076 | regex `2[3456]` | `e2b6244` 2026-09-02 - et rien d'autre |
| C077 | `except Exception  # base sans schema` | `794b492` 2026-09-03 - et rien d'autre |
| C092 | `"vide": "= ''"` | `794b492` 2026-09-03 - et rien d'autre |
| C099 | `except Exception  # registre illisible` | `1b9b766` 2026-09-03 - et rien d'autre |
| C053 | toute mention de `010_Pilotage` dans `src/` | **aucun commit, jamais** |
| C095 | `doute` dans `_actes_vues.py` | **aucun commit, jamais** |

Un correctif ne peut pas etre invisible s'il n'a jamais ete ecrit. Ces sept
lignes n'ont pas ete « corrigees sur une branche perdue »: elles n'ont jamais
ete retouchees par personne.

### Ce qui est vrai dans l'intuition de Brice, et qui merite d'etre dit

Son impression - « on a vraiment travaille tous les points deja » - **est
exacte**, mais elle porte sur l'ensemble de la campagne, pas sur ce residu.
La campagne du 2026-09-04 a rendu **55 verdicts: 14 fermes et 24 partiels**.
Trente-huit constats sur cinquante-cinq ont donc bel et bien ete travailles, et
plusieurs branches `chantier/fix-*` en portent la trace. Les 16 qui restent sont
precisement **ceux qu'aucun lot n'a jamais touches**. Le sentiment de deja-vu
vient du volume de travail reel accompli a cote, pas d'un travail perdu.

### Deux branches ne sont effectivement pas ancetres de la branche courante

`chantier/fix-voix` (`caf53a5`) et `chantier/fix-classement` (`f333147`), toutes
deux du 2026-09-04, ne sont pas ancetres de `chantier/recentrage-architecture`.
C'est un vrai desordre de git, et il justifiait la question. Mais **leur contenu
est present dans la branche courante par une autre voie**: verifie sur le
classement, la branche courante porte une version *posterieure* du correctif
(lecture des priorites via `_champ_regle`, retrait de `assemblee generale` des
mots-cles) que la branche `fix-classement` ne porte pas. Et aucun des 14 commits
identifies par l'enquete d'historique n'est exclusif a ces deux branches.

**Conclusion sur l'hypothese: le desordre de git est reel, la perte de travail
ne l'est pas.**

---

## 2. Methode, et garde de l'instrument

Chaque constat a ete rejoue par execution, pas par recherche de chaine. Les
mesures tournent sur l'arbre `chantier/recentrage-architecture`, interpreteur
`server/.venv`, `PYTHONPATH=src`, avec le chemin du module imprime a chaque fois
pour prouver quel arbre est mesure.

**L'instrument sait rendre plusieurs verdicts.** Il a rendu `ENCORE_OUVERT` 14
fois, `CORRIGE_DEPUIS` une fois et `CADUC` une fois. Il s'est aussi trompe deux
fois en cours de route, et les deux erreurs sont instructives:

1. **Un grep sans accent.** J'ai d'abord cherche `21 alinea 2` et conclu que la
   chaine avait disparu de la couche web. Elle s'ecrit `alinéa` **avec
   accent**: elle est toujours la, en 6 occurrences. Une recherche de chaine
   avait failli fermer un constat a tort.
2. **Un classifieur nourri de texte vide.** Mon premier rejeu du classement sur
   le second cabinet rendait `A_CLASSER` score 0 pour les 22 pieces - donc
   « plus de defaut ». En verifiant, les PDF sont des images scannees et
   l'extraction directe rendait **1 a 2 caracteres**. En passant par le texte
   reellement extrait (`staging/text`, colonne `text_path`) puis par la vraie
   commande `classify`, le constat se reproduit **exactement**.

Ces deux erreurs sont la raison pour laquelle un verdict `CORRIGE_DEPUIS` n'est
rendu ici qu'avec le commit qui corrige, nomme et date.

**Instances du lot**, creees pour ce lot et non mutees ailleurs:

- `instances/verif_constats_20260908_erables_pseudo` - copie de
  `instances/erables_pseudo_test`, 22 pieces, second cabinet;
- `instances/verif_constats_20260908_tilleul_pseudo` - copie de
  `instances/tilleul_pseudo_reconstruite_20260904`, 3447 lignes de registre.

Aucune donnee d'instance n'est recopiee dans ce document: seuls des comptages,
des types documentaires et des noms de fichiers de travail y figurent.

---

## 3. Les 16 constats, un par un

Colonne « axe »: renvoie aux trois axes deja nommes par le gouvernail -
**(A)** le registre ne distingue pas une piece recue d'un derive de traitement,
**(B)** un `except` nu degrade en silence, **(C)** le desaccord entre deux
sources n'a aucune sortie, **(D)** reliquat isole.

| # | Ce qu'il affirme, en une phrase | Verdict | Preuve rejouee / commit | Axe |
|---|---|---|---|---|
| C037 | Le total des charges d'une annexe comptable est pris dans la derniere colonne du tableau, quelle qu'elle soit - donc souvent un budget a venir au lieu du realise de l'exercice. | `ENCORE_OUVERT` | Rejeu sur la fixture du depot: exercice couvert 01/01/2029 -> 31/12/2029, colonnes `[1000, 1100, 1050, 1200, 1300]`, **total retenu 1300.00** alors que le realise 2029 vaut 1050.00. Ligne `_comptes_extraction_annexe.py:136` inchangee depuis `7153d91` (2026-09-03). | D |
| C048 | Le type « convocation d'assemblee » absorbe 151 pieces dont 15 seulement portent le mot dans leur nom, et un echantillon ouvert n'en contient aucune vraie. | `ENCORE_OUVERT` | Etat stocke: **151 lignes** typees `Convocation_AG`, **15** dont le nom porte `convocation`. **Rejeu de la vraie commande `classify` sur la copie du lot: 143** - le chiffre exact publie par les verdicts. Echantillon aleatoire de 20 (graine 7) apres rejeu: fiches de controle, bordereaux de pieces, pages OCR, notes de strategie, CSV de travail - **zero convocation**, et la liste recoupe celle des verdicts piece par piece. Sur les 143, **6 PDF seulement** sont des convocations plausibles. Extensions du type apres rejeu: 67 `.md`, 24 `.pdf`, 21 `.csv`, 16 `.txt`, 12 `.docx`, 3 `.xlsx`. | A |
| C049 | Le meme document, sur quatre exercices consecutifs d'un second cabinet, tombe dans deux types differents. | `ENCORE_OUVERT` | Vraie commande `classify` sur la copie du second cabinet: 2023 -> `Annexe_Comptable`, 2024 / 2025 / 2026 -> `CR_CS`. **Une serie de quatre exercices coupee en deux types, tous `AUTO_CLASSIFIED`, sans aucun signal.** Mesure au passage: les trois convocations nues partent en `Reglement_Copropriete`. | A |
| C051 | Les deux tiers du registre sont des derives du traitement de CoproScope, pas des pieces recues, et des centaines portent quand meme un type documentaire affirme. | `ENCORE_OUVERT` | Comptage sur 3447 lignes: `page_NNN.*` 2290, `pNN.png` 28, conversions `.pdf.md`/`.docx.md` 26, `.ocr.txt` 18 = **2362 lignes, 68,5 %**. **374 derives portent un type affirme** hors `A_CLASSER` dans l'etat stocke; **apres rejeu du classifieur, 419, dont 394 en `AUTO_CLASSIFIED`** - les deux chiffres exacts publies par les verdicts. Rien ne distingue une piece d'un fragment: `source_kind` vaut `raw` pour les 3447 lignes, `source_zone` vaut `RAW` pour les 3447. | A |
| C053 | Deux registres documentaires concurrents coexistent dans l'instance; le code n'en ouvre qu'un, et 99 annexes d'assemblee vivent dans celui qu'il n'ouvre jamais. | `ENCORE_OUVERT` | Canonique 3447 lignes / 47 colonnes; orphelin 309 lignes / 20 colonnes. `instance.yml` ne declare que le premier. **`010_Pilotage` n'apparait dans aucun fichier de `src/`, et n'y est jamais apparu.** `Annexe_AG`: **1** ligne dans le registre lu, **99** dans le registre ignore. 7 types n'existent que dans l'orphelin. | A |
| C057 | Une note du depot affirme que les deux cabinets soumettent au vote les modalites de consultation des pieces; c'est faux pour le second depuis 2024. | `ENCORE_OUVERT` | Phrase intacte dans `docs/typologie_resolutions_2026-09-04.md`. **Le fichier n'a qu'un seul commit, `a0a1e87` du 2026-09-03** - anterieur aux verdicts, et aucune correction n'a suivi. | D |
| C076 | La lettre qui distingue les regimes de l'article 25 (le « 25B ») est effacee sans trace: 25B, 25 b et 25c deviennent tous « 25 ». | `ENCORE_OUVERT` | Rejeu de la regex reelle: `Article 25B)` -> `'25'`, `article 25 b)` -> `'25'`, `Article 25c` -> `'25'`. Le groupe capture ne peut pas contenir de lettre. Regex **identique octet pour octet dans les 13 commits du fichier**, depuis `e2b6244` (2026-09-02). | D |
| C077 | Un `except Exception` nu rend « aucune autorisation identifiee » pour toute depense, quelle que soit la panne - et une simple lecture cree la base. | `ENCORE_OUVERT` | Volet 1: apres renommage d'une colonne, le SQL brut leve `OperationalError: no such column: l.motif`, mais `actes_du_dossier` rend **`[]` sans lever**. Volet 2: base absente -> une lecture la cree (`existe ? False` -> `True`, taille 0). Les modules voisins refusent ce repli; celui-ci ne l'a jamais fait. | B |
| C078 | `_reset_schema` n'efface pas une table etrangere, donc le motif ecrit dans la doctrine du depot est faux. | `CORRIGE_DEPUIS` | **Commit `1247f78`, 2026-09-08 - POSTERIEUR aux verdicts.** La doctrine est corrigee aux quatre endroits (`CLAUDE.md`, `gouvernance_store.py`, `_actes_schema.py`, `pont_actes.py`): elles disent maintenant que la table **survit** et se desynchronise. Le comportement, lui, est inchange et c'est desormais **conforme a ce qui est ecrit**: rejeu, la table etrangere et sa ligne survivent au rebuild complet; `_reset_schema` reste une liste fermee de 24 `DROP TABLE IF EXISTS`, sans balayage de `sqlite_master`. | - |
| C081 | L'alinea juridique cite est faux dans toutes ses occurrences, y compris dans le renvoi affiche a l'ecran. | `CADUC` (premisse refutee) | **Refute a la source le 2026-09-07 sur Legifrance (`LEGIARTI000039313574`): l'article 21 alinea 2 porte bien les deux seuils.** Le code a raison, l'audit avait tort; il n'y a rien a corriger. Le code porte toujours 6 occurrences de `alinéa 2` (dont le renvoi ecran `controle_gouvernance_view.py:173`), **et elles sont justes**. Voir la reserve au chapitre 6. | - |
| C082 | Le dedoublonnage des lectures concurrentes d'un meme proces-verbal vit dans une seule vue, pas dans le magasin. | `ENCORE_OUVERT` | Rejeu de bout en bout: trois documents portant chacun 55 resolutions de la meme assemblee. **Le magasin rend 165 lignes, l'ecran en montre 55** - un rapport de 3. Neuf consommateurs hors couche web lisent ce brut. La mitigation de `copies_concurrentes` nomme les copies sans choisir, et vit toujours dans la vue. | C |
| C083 | La table qui porte « Ma conclusion » est lue par l'ecran mais aucune route n'ecrit dedans: la boucle de travail n'a pas de sortie. | `ENCORE_OUVERT` | Balayage de tout `src/`: **0 ecrivain**, 1 lecteur (`controle_gouvernance_view.py:97`). Les 5 routes de gouvernance sont **toutes des `GET`**; les 18 `POST` du depot concernent le Drive, l'entree de documents, la compta - **aucune** la gouvernance. L'ecran nomme lui-meme le manque, depuis `c759740` (2026-09-03), soit avant les verdicts. | C |
| C085 | Le garde-fou « pas de citation de memoire » ne verifie que la forme de l'identifiant, et les motifs de retrait n'en portent aucun. | `ENCORE_OUVERT` | Volet 1: `test_resolutions_typage.py:486` porte toujours `re.compile(r"LEGIARTI\d{12}")` non ancre, employe l.495 - `XXLEGIARTI999999999999YY` passe. Volet 2: **44 motifs `HORS_CONTROLE`, 0 portant un identifiant.** Fichier jamais modifie depuis `a0a1e87` (2026-09-03). Nuance: le meme fichier porte une version ancree l.53, sur un autre jeu de valeurs. | D |
| C092 | Les operateurs « vide » et « non vide » d'un filtre ignorent silencieusement la valeur fournie. | `ENCORE_OUVERT` | Rejeu: `construire_requete([('date_effet','vide','2024-07-03')])` rend `WHERE "date_effet" = ''` et **une liste de parametres vide**. La date est jetee sans erreur ni trace. Ligne inchangee depuis `794b492` (2026-09-03); aucun commit n'a jamais ajoute de refus. | D |
| C095 | Aucune vue n'expose le desaccord entre deux assertions, et la colonne qui porte le doute n'est lue par aucune vue. | `ENCORE_OUVERT` | Rejeu sur base fraiche: deux assertions divergentes sur la meme paire, l'une `PIECE_PRODUITE` par le syndic, l'autre `ABSENT` calculee. **11 vues, 0 citant `doute`, 0 exposant une colonne `doute`.** L'ecran rend un statut unique, `ABSENT`; rien ne dit que le syndic affirmait le contraire. `v_divergences_humaines` rend 0 ligne: elle porte le desaccord sur un acte, pas sur un lien. | C |
| C099 | Deux `except Exception` et un `except ValueError` degradent l'election de la version qui fait foi. | `ENCORE_OUVERT` | Mesure 1: registre lisible -> le PDF d'origine est elu; **registre illisible -> la conversion texte l'emporte, et s'affiche « origine »**. Mesure 2: une resolution numerotee « 5 bis » est jetee par l'`except ValueError`, les couvertures s'egalisent, et **le document le MOINS complet est elu**. Trois replis inchanges depuis `1b9b766` (2026-09-03). | B |

---

## 4. Le compte par verdict

| Verdict | Nombre |
|---|---:|
| `ENCORE_OUVERT` | **14** |
| `CORRIGE_DEPUIS` | **1** (C078, et le correctif est **posterieur** aux verdicts) |
| `CADUC` | **1** (C081, premisse refutee le 2026-09-07, **posterieur** aux verdicts) |
| `NON_REPRODUCTIBLE` | **0** |

**Constats deja corriges AVANT le 2026-09-05 tout en etant declares ouverts: 0.**

Les deux constats qui ne sont plus ouverts ont ete traites **les 7 et 8
septembre**, c'est-a-dire *apres* le document de verdicts. Ils ne peuvent donc
pas expliquer une erreur de ce document: ils sont la preuve que le travail a
continue apres lui, pas qu'il lisait un mauvais arbre.

---

## 5. Ce que cela dit de la fiabilite du document de verdicts

**Le document du 2026-09-05 est fiable sur son perimetre.** 14 de ses 16
constats ouverts se reproduisent aujourd'hui, souvent au chiffre pres: 68,5 %,
151 et 15, 3447 et 309, 1 et 99, 44 et 0, un rapport de 3 entre le magasin et
l'ecran. Les deux qui ont bouge ont bouge apres lui.

**Le test le plus dur qu'il ait passe est le rejeu du classement.** Sur un
corpus de 3447 lignes, en repassant la vraie commande `classify`, il rend
**143**, **419** et **394** - les trois chiffres qu'il publiait, a l'unite - et
son echantillon aleatoire a graine 7 ressort piece par piece. Un document ecrit
trois jours plus tot qui se reproduit a l'unite sur un corpus de cette taille
n'a pas ete ecrit contre un autre arbre.

Deux reserves, qui ne sont pas des erreurs mais des limites a garder:

1. **Il melange des constats de nature differente sous un meme statut.** C081
   n'etait pas un defaut du code mais une accusation portee contre lui, et le
   document la classait « ouvert » alors que sa verification propre disait
   explicitement n'avoir pas pu re-mesurer le fait juridique. Un constat dont la
   premisse n'est pas verifiee ne devrait pas porter le meme statut qu'un
   defaut rejoue.
2. **`ouvert` y designe parfois « le code n'a pas bouge » plutot que « le defaut
   nuit ».** C078 en est le cas net: le comportement decrit est reel, mais ce
   qu'il fallait corriger etait la phrase de doctrine, pas le code - et c'est
   bien la phrase qui a ete corrigee.

Ce que le document **ne dit pas et qu'il faudrait ajouter au gouvernail**: ces
16 constats ne sont pas un reste de travail perdu, ce sont les constats
**qu'aucun lot n'a jamais pris**. C'est une information de pilotage differente,
et plus actionnable.

---

## 6. Les constats reellement ouverts, groupes par axe

### Axe A - le registre ne distingue pas une piece recue d'un derive de son traitement (4 constats)

`C051`, `C053`, `C048`, `C049`. C'est l'axe le plus lourd et il conditionne la
justesse de tout ce qui compte des pieces.

**Pour les fermer il faut**, et aucun de ces points n'est engage a ce jour:

- une colonne de derivation dans le registre, ecrite a l'inventaire, qui
  distingue une piece recue d'un fragment produit par CoproScope. Aujourd'hui
  `source_kind` vaut `raw` pour les 3447 lignes, ce qui ne distingue rien;
- une decision sur le second registre: l'absorber ou le declarer mort. Tant
  qu'il existe sans etre lu, 99 annexes d'assemblee sont invisibles;
- pour le classement, un travail **par axes de generalisation** et non par
  modalites, au sens de la regle du depot: la serie de quatre exercices coupee
  en deux types se rejoue a l'identique, et le second cabinet est deja
  disponible pour l'epreuve.

### Axe B - un `except` nu degrade en silence (2 constats)

`C077`, `C099`. Meme famille que `RM-2026-0106` et `RM-2026-0110`.

**Pour les fermer il faut** que chaque repli distingue la panne attendue de la
panne inattendue, comme `_actes_store.lire_vue` et `gouvernance_store.lire` le
font deja pour eux-memes: `no such table` rend une liste vide, tout le reste
leve. Le modele existe dans le depot, a deux fichiers de distance; il n'a jamais
ete applique a ces trois endroits. Un test de derive de schema doit accompagner
chacun.

### Axe C - le desaccord entre deux sources n'a aucune sortie (3 constats)

`C095`, `C082`, `C083`.

**Pour les fermer il faut** une vue qui expose la contradiction au lieu de la
trancher par `LIMIT 1`, un dedoublonnage qui vive dans le magasin plutot que
dans une seule vue, et un canal d'ecriture pour la conclusion humaine.

**Attention, un arbitrage recent modifie cet axe.** `RM-2026-0124` (retour vocal
de Brice du 2026-09-08) pose que le geste « comparer les deux assertions de
seuil » **tombe**: c'est le dernier vote qui compte, et non une ambiguite a
arbitrer. Cela ne supprime pas C095 - deux sources peuvent toujours se
contredire sur autre chose qu'un seuil - mais **cela change ce qu'il faut
construire**, et l'axe C ne doit pas etre lance sans relire cet arbitrage
d'abord.

### Axe D - reliquats isoles (5 constats)

`C037`, `C076`, `C092`, `C085`, `C057`. A traiter au fil de l'eau, chacun etant
borne a un fichier.

- `C037` et `C076` sont les deux plus graves de ce groupe: ils produisent un
  **chiffre faux en silence**, l'un sur un total de charges, l'autre en effacant
  la lettre qui separe deux regimes de majorite. `C076` est de surcroit un cas
  d'ecole de la regle du depot sur les axes: la regex enumere `2[3456]`, donc
  des modalites observees;
- `C092` et `C085` sont des garde-fous qui ne gardent pas;
- `C057` est une phrase fausse dans un document, corrigeable en une ligne.

---

## 7. Le residu - ce que ce lot n'a pas su etablir

**Nommer le residu est une exigence du depot, et voici le sien.**

1. **Le verdict `CADUC` de C081 n'est pas un verdict propre.** Les quatre
   verdicts disponibles supposaient qu'un constat caduc l'est parce que son code
   a disparu. Ici le code est intact et c'est l'**accusation** qui est fausse.
   J'ai retenu `CADUC` faute de mieux et je le signale plutot que de le masquer:
   il faudrait un cinquieme verdict, `PREMISSE_REFUTEE`. Je n'ai pas relu
   moi-meme l'article sur Legifrance - je m'appuie sur la refutation tracee au
   gouvernail le 2026-09-07 - donc ce point reste une **verification de seconde
   main**.

2. ~~Le rejeu du classement de C048 sur les 3447 lignes n'est pas dans ce
   tableau.~~ **Ce residu est leve.** Le rejeu a ete fait apres la premiere
   redaction, par la vraie commande `classify` sur la copie du lot. Il rend
   **143** pour `Convocation_AG`, **419** derives a type affirme et **394** en
   `AUTO_CLASSIFIED` - les trois chiffres exacts publies par les verdicts du
   2026-09-05, et l'echantillon a graine 7 recoupe le leur piece par piece. Il
   ne reste de residu ici que ceci: je n'ai pas ouvert les 143 pieces une a une,
   j'ai lu l'echantillon de 20 et compte les 6 PDF plausibles.

3. **Je n'ai pas lance la suite de tests complete.** Consigne explicite du fil
   pilote: deux suites concurrentes dans cet arbre se bloquent sans verdict. Les
   mesures sont donc des rejeux cibles, module par module. **Aucune de mes
   mesures n'est une preuve de non-regression du depot**, et ce lot ne
   revendique pas d'en etre une.

4. **La gravite et le caractere silencieux des constats n'ont pas ete
   re-evalues.** Je reprends ceux du document de verdicts sans les remesurer.

5. **Les instances du lot sont laissees en place** pour permettre a un autre lot
   de rejouer sans refaire les copies:
   `instances/verif_constats_20260908_erables_pseudo` et
   `instances/verif_constats_20260908_tilleul_pseudo`. Elles sont hors Git.

6. **Deux branches restent non fusionnees** - `chantier/fix-voix` et
   `chantier/fix-classement`. J'ai verifie que leur contenu utile est present
   par une autre voie sur le classement, **je ne l'ai pas verifie sur le
   decompte des voix** (`caf53a5`, 11 fichiers, 1883 insertions). Ce point
   merite son propre passage et n'entre pas dans les 16 constats.

---

## 8. Ce qu'il faut inscrire au gouvernail

`RM-2026-0086` doit perdre la mention « 16 constats ouverts » et porter le
resultat mesure: **14 ouverts, 1 corrige le 2026-09-08, 1 caduc par refutation
de sa premisse, et zero correctif anterieur perdu**. La decoupe en trois axes
plus reliquats reste valable et peut etre lancee - la verification demandee par
Brice avant la decoupe est faite.

Deux precisions a porter dans l'item:

- l'axe C doit etre relu a la lumiere de `RM-2026-0124` avant tout lot;
- C081 sort du perimetre: il n'y a rien a corriger, le gouvernail le disait deja
  et ce lot le confirme.
