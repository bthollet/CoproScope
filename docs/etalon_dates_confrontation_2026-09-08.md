# Etalon des dates: ce que l'extracteur lit vraiment

**Campagne du 2026-09-08.** Brice avait demande un etalon; a la question *veux-tu
les lire toi-meme*, il a repondu **non, lis les toi**. Dix lecteurs ont donc lu
80 documents **en aveugle de l'extracteur** - sans jamais voir le registre ni la
colonne `suspected_date` - puis un second lecteur a repris 20 d'entre eux sans
voir la premiere lecture.

**Le resultat en une ligne: 12 % de justesse mesuree, et zero document date
correctement a partir d'une date ecrite dans son propre texte.**

Cette note porte des extraits de pieces reelles. L'identite est pseudonymisee,
le contenu ne l'est pas: elle releve de `RM-2026-0137` comme les deux autres
notes du jour.

---

J'ai retrouvé les lectures complètes des lecteurs (les 80 de la première lecture et les relectures) dans les journaux de sous-agents, et je les ai confrontées à l'extracteur du produit.

---

# 1. Accord entre lecteurs

**26 documents ont été lus par au moins deux lecteurs différents. 25 donnent exactement la même date. 1 seul écart, et ce n'est pas un écart de lecture.**

Le détail :

| Ce qui a été fait | Nombre |
|---|---|
| Documents de l'étalon (10 lecteurs, 8 documents chacun) | 80 |
| Documents relus par un second lecteur indépendant | 20 |
| Documents lus par **cinq** lecteurs au total (une première vague de 4 + l'étalon) | 8 |
| Documents distincts lus au moins deux fois | **26** |
| Lectures au total | **132** |

**Résultat : 25 accords parfaits sur 26.** Sur les 8 documents lus cinq fois, les cinq lecteurs donnent la même date à chaque fois, y compris pour dire « aucune date » sur le document scanné dont l'extraction ne rend aucun caractère.

**Le seul écart** porte sur `DOC-F3981D97DE50`, un projet de résolutions annexé à une convocation d'assemblée. Les deux lecteurs voient exactement la même chose : le document n'écrit nulle part sa propre date, et l'assemblée qu'il prépare est le 3 décembre 2025. L'un refuse de retenir cette date (« ce n'est pas une date d'émission »), l'autre l'accepte. C'est un **désaccord de convention, pas de lecture** : ils ne lisent pas deux choses différentes, ils tranchent différemment la même ambiguïté.

**Ce que cet accord prouve, et ce qu'il ne prouve pas.** Il prouve que la lecture est reproductible : deux lecteurs qui n'ont pas communiqué arrivent au même chiffre. Il ne prouve pas qu'elle est juste. Si les lecteurs partagent le même biais, ils s'accordent sur la même erreur. J'y reviens en partie 4.

---

# 2. Confrontation avec l'extracteur

Fonction mesurée : `coproscope.core.date_du_document`, appelée sur le même texte que celui que les lecteurs ont lu. C'est bien la fonction vivante du produit : elle est appelée par le classement (`modules/_docuscope_parts/02_classification.py`) et par la construction des assemblées (`modules/agscope.py`, qui en fait l'identifiant `AG-<date>`).

| Verdict | Nombre |
|---|---:|
| **JUSTE** (même date que l'étalon) | **9** |
| **FAUSSE** (une autre date) | **28** |
| **MANQUÉE** (l'étalon a une date, le code rend vide) | **38** |
| **INVENTÉE** (le code rend une date, l'étalon dit AUCUNE) | **2** |
| **ACCORD SUR L'ABSENCE** | **2** |
| Contesté entre lecteurs (non comptabilisé) | 1 |
| **Total** | **80** |

**Taux de justesse sur les 75 documents où l'étalon a une date : 9 justes, soit 12,0 %.**

(Si l'on adopte la convention du second lecteur pour le document contesté, cela fait 10 sur 76, soit 13,2 %. Environ un document sur huit, dans les deux cas.)

**Le chiffre qui compte davantage que le taux.** Les 9 réussites viennent **toutes** d'un nom de fichier écrit au format `2026-05-23_...` — six lues directement dans le nom du fichier, trois lues dans le texte parce que le nom du fichier d'origine y était recopié en tête de page.

> **Zéro document sur 75 a été daté correctement à partir d'une date écrite dans le corps du document.**

Pire, une des 9 est juste par accident : sur `DOC-C65A50F1E7DC`, la chaîne que le code a attrapée est le nom d'un **autre** document cité dans le texte, qui portait par chance la même date.

---

# 3. Les fausses, une par une

## La cause unique, en amont de tout le reste

Le code ne cherche qu'une seule forme de date : **année, mois, jour, dans cet ordre** (`2026-05-23`, `2026.05.23`, `2026 05 23`). Il ne reconnaît **aucune** des formes que les documents emploient réellement :

- `23/06/2026` (la forme de presque toutes les factures),
- `Marseille, le 13 avril 2026` (la forme des courriers),
- `1 septembre 2025` (la forme des factures d'énergie),
- `05.08.2025` (la forme d'un opérateur télécom).

De là découlent les deux moitiés du problème : **38 dates manquées** (il ne trouve rien et le dit — c'est le comportement honnête du module), et **28 dates fausses**, parce que faute de reconnaître la vraie date il attrape la première suite de chiffres qui *ressemble* à une date ISO, où qu'elle soit dans la page.

## Groupe A — Le numéro d'un décret : 8 documents

Mention légale en bas de facture : « en application du décret n° 2012-1115 ». Le code lit `2012-11` et date la facture de **novembre 2012**.

Documents touchés : `01F54764F559`, `58A14726DF25`, `A0C270D8CCA8`, `B3E72C9D0265`, `C216854B352E`, `CD636165ECF8`, `DE4FF069B449`, `E6FB2F8A78D4` — des factures de 2025 et 2026, toutes renvoyées en 2012.

## Groupe B — Un numéro de devis en forme de date : 10 documents

Deux prestataires numérotent leurs devis d'une façon qui a exactement la forme d'une date.

- « Selon Devis n° **2018-10-20** PH » → 7 factures datées du 20 octobre 2018 (`14AE609F58E5`, `194759A8BA81`, `5C6714775DB2`, `6286AD2774D9`, `7A4A1256D41A`, `8910C3691014`, `FA57B8D00C59`).
- « Devis n° **2016-01-06** du 25 Janvier 2016 » → 3 factures datées du 6 janvier 2016 (`0EF63F3B0D0A`, `4C8DE36FCF84`, `A6F7FD3541AA`).

**À noter : trois chaînes de caractères, présentes dans des modèles de facture répétés tous les mois, expliquent à elles seules 18 des 30 dates fausses ou inventées.** Un seul motif dans un gabarit de fournisseur empoisonne toute une série.

## Groupe C — Un numéro de facture ou de devis : 3 documents

- `264F687460AD` : « FACTURE N° **F2026-04-058** » → le code lit `2026-04-05`. La vraie date est le 13 avril 2026.
- `1A3BE747CBEE` : « Devis N° : JR **D2025.04.26** / Date : 25/04/2025 » → le code lit `2025-04-26`. **La vraie date est le 25/04/2025, un jour avant.** C'est l'erreur la plus dangereuse du lot : elle est juste assez proche pour ne jamais être remarquée.
- `4E67E59351D2` : « Ref : **PH2024-01** » → le code lit `2024-01`, un mois sans jour, alors que le courrier dit « Marseille, 11 janvier 2024 ».

## Groupe D — L'heure d'un courriel prise pour un mois : 3 documents

Ces PDF agrafent une facture (page 1) et le courriel de commande (page 2). Le courriel porte « Le : 20/03/2025 **08:56:39** ». Le code lit `2025 08` : il prend l'année et **l'heure comme mois**. La facture de mars 2025 est donc datée d'août 2025.

Documents : `7FA4EE66E639` (mars → août), `8E64E643EECE` (février → octobre), `96B59613F08F` (avril → octobre).

## Groupe E — Le nom du fichier porte l'exercice comptable : 3 documents

Trois états de consommation d'eau s'appellent `2025-12-31_consommation_H22.pdf`. Le code lit `2025-12-31`. Or le document dit « Édité le 05/05/2026 » : `2025-12-31` est la **clôture de l'exercice** dont l'état rend compte, pas le jour où il a été fait. Écart de plus de quatre mois, et l'exercice de rattachement change.

Documents : `09FC6F2AE59A`, `3040666B1280`, `4088BAD9B1DD`.

## Groupe F — Une cellule de tableur : 2 documents (dont 2 inventées)

- `9AF01E9627FD` : classeur de pilotage. Le code attrape la première valeur d'une colonne **« échéance »** (`2026-04-29`) et en fait la date du classeur.
- `67EEF8FCD64A` : classeur d'audit. Le code attrape une cellule `updated_at 2026-05-04`. **INVENTÉE** : les deux lecteurs disent que ce classeur n'énonce nulle part sa propre date.

## Groupe G — Le nom du fichier d'une page isolée : 1 document (inventée)

`6B9B16DAD9C6` est la seule page de signatures d'un procès-verbal, détachée du reste. Le fichier s'appelle `2024-07-03_pv__cloture_et_signatures.pdf`, le code en tire `2024-07-03`. Soyons honnêtes : la valeur est très probablement la bonne dans les faits. Mais elle vient du nom, pas de la pièce, et la pièce ne porte aucune date. C'est classé INVENTÉE parce que c'est bien le nom du rangement qui parle, pas le document.

## Par quoi commencer

Le classement ci-dessus le dit tout seul : **corriger les motifs un par un serait refaire l'erreur des modalités**. Le décret 2012-1115, le devis 2018-10-20 et le devis 2016-01-06 sont trois valeurs observées chez trois fournisseurs ; un quatrième cabinet en apportera d'autres. Le seul travail qui tienne est celui de la partie 3 en amont : **savoir lire une date française là où le document la met, et savoir dire à quel titre elle est là** (date d'émission, échéance, période, texte de loi, numéro de pièce). Tant que le code prend la première suite de chiffres qui a la bonne forme, il continuera de dater des factures avec des numéros de décret.

---

# 4. Ce que cet étalon ne prouve pas

**Il n'a pas été établi par Brice.** Il a été établi par 10 lecteurs automatiques, en aveugle de l'extracteur — ils n'ont jamais vu le registre ni la colonne `suspected_date`, et le tirage leur cachait ce que le code trouve. La contre-lecture (26 documents relus, 25 accords) montre que la lecture est **reproductible**. Elle ne montre pas qu'elle est **vraie** : deux lecteurs qui partagent le même biais s'accordent sur la même erreur. Personne n'a rouvert un seul PDF d'origine.

**Il porte sur 80 documents sur 858, soit 9,3 % du corpus.**

**Et le tirage n'était pas représentatif — c'est la limite la plus importante.** L'échantillon a été construit exprès moitié-moitié : 40 documents où le code trouve quelque chose, 40 où il ne trouve rien. Or dans le corpus réel, ce n'est pas moitié-moitié :

| | Échantillon | Corpus lisible réel |
|---|---:|---:|
| Le code trouve une date | 40 (50 %) | 180 (25 %) |
| Le code ne trouve rien | 40 (50 %) | 538 (75 %) |

L'échantillon **sur-représente donc la moitié où le code s'en sort le moins mal**. En repondérant les résultats par les vraies proportions, on obtiendrait sur les 718 documents lisibles environ **40 dates justes, 126 fausses, 9 inventées et 511 manquées**, soit un taux de justesse projeté d'environ **6 %**, la moitié des 12 % mesurés. C'est une **projection à partir de 80 lectures**, pas une mesure : je la donne pour dire que le 12 % est un plafond, pas un plancher.

**Il ne couvre que les documents qui ont du texte.** 140 documents sur 858 (16 %) n'ont pas 200 caractères exploitables — des scans sans reconnaissance de caractères. Ils ont été exclus du tirage. Sur ceux-là, personne ne sait rien : ni les lecteurs, ni le code, qui rend vide.

**Il n'y avait pas de règle de convention écrite d'avance.** Huit documents sur 80 portent une réserve explicite du lecteur, et ce sont de vraies questions auxquelles l'étalon lui-même ne répond pas fermement : un état de comptes se date-t-il au jour de son édition ou à la clôture de l'exercice ? Un duplicata se date-t-il à la facture d'origine ou au tirage ? Une facture avec un courriel agrafé derrière, est-ce un document ou deux ? Un projet de résolutions se date-t-il par l'assemblée qu'il prépare ? Tant que la règle n'est pas fixée avant la lecture, ces cas restent des désaccords de convention déguisés en erreurs.

**Il ne vaut que pour un fonds.** Le corpus vient d'une seule copropriété et d'un petit nombre de cabinets. Le décret 2012-1115 et les deux numéros de devis piégeux viennent de trois fournisseurs. Un autre cabinet apporterait d'autres pièges — et, conformément à la règle des axes, il faudrait éprouver sur le second corpus (`instances/erables_pseudo_test`) avant de conclure quoi que ce soit sur la généralité de ces causes.

## Ce qu'il faudrait pour un étalon qui vaudrait pour la justesse

1. **Un humain ouvre les PDF d'origine** — pas le texte extrait — et écrit la date à la main, avant tout traitement outil. C'est ce que dit déjà la doctrine du dépôt pour `instances/tests_ux`.
2. **Une règle de convention écrite avant la lecture**, tranchant les cinq cas ci-dessus, pour qu'un désaccord de convention ne soit plus compté comme une erreur.
3. **Un tirage au hasard, non stratifié**, ou alors stratifié en le déclarant et en repondérant les résultats — ce que je viens de faire, mais après coup.
4. **Les documents sans texte inclus**, avec une décision claire : soit on les passe à la reconnaissance de caractères, soit on les déclare hors mesure. Aujourd'hui ils sont simplement absents, et leur absence gonfle discrètement toutes les statistiques.

---

## Fichiers produits (données de mesure, réutilisables)

Tous dans `C:\Users\brice\AppData\Local\Temp\claude\C--Users-brice-CoproScope-coproscope\5476f3b8-1df3-462d-a0b8-770e4a24bc55\scratchpad\` :

- `x_etalon.json` — les 80 lectures de l'étalon, avec nature, chaîne littérale, contexte, confiance
- `x_contre.json` — les 20 relectures indépendantes
- `x_quad.json` — les 8 documents lus par 4 lecteurs supplémentaires
- `x_verdicts.json` — le verdict document par document (étalon, valeur du code, source, classement)
- `x_confronte.py`, `x_cause.py`, `x_strate.py` — les scripts de mesure, rejouables
