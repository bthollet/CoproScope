# Conception du systeme de surveillance d'extranet

Date: 2026-09-06.
Rattachement: `RM-2026-0091`, avec `RM-2026-0092` en dependance aval.
Statut: `CONCEPTION`. Ce document tranche ce qui peut l'etre sur mesures, et
nomme ce qui reste a arbitrer par Brice.

Amont: [`cartographie_extranet_coprodirecte_2026-09-04.md`](./cartographie_extranet_coprodirecte_2026-09-04.md),
[`journal_observation_extranet.md`](./journal_observation_extranet.md),
[`referentiel_conformite_extranet_v1.md`](./referentiel_conformite_extranet_v1.md).

---

## 1. Ce que le systeme doit faire

### Fonctionnel

1. **Constater** ce qu'un syndic publie sur son espace en ligne, a une date.
2. **Detecter** ce qui change entre deux dates: ajout, retrait, modification.
3. **Qualifier** ces changements au regard du droit - la liste minimale du
   decret 2019-502 - sans jamais accuser a tort.
4. **Exporter** de quoi recouper avec un autre coproprietaire, sans faire
   circuler de contenu.

### Non fonctionnel, avec les chiffres mesures

| Grandeur | Valeur mesuree le 2026-09-04 |
|---|---:|
| Pieces a l'index documents | 115 (230 liens) |
| Rubriques | 8 |
| Lignes de depenses | 872, dont 729 avec facture |
| Cles de charges | 42 |
| Poids d'une piece (un echantillon) | ~50 ko |
| Cout d'une sonde de presence | **0 octet** - `HEAD` rend un corps vide |
| Cout d'une sonde de contenu | le fichier entier - `Range` annonce mais **non honore** |

Ce que ces chiffres imposent, et qui structure tout le reste:

- **la presence est quasi gratuite** - 115 requetes sans corps;
- **le contenu est cher** - environ 6 Mo pour l'index documents, et de l'ordre
  de 70 Mo si l'on voulait les 729 factures;
- **rien dans les en-tetes ne revele un changement de contenu**: ni `etag`, ni
  `last-modified`, ni `content-length`.

Il n'existe donc pas de position intermediaire. Toute conception qui pretendrait
surveiller le contenu "a bas cout" se trompe.

### Contraintes non negociables

| Contrainte | Origine |
|---|---|
| Tout ce qui sort vers le syndic passe par un clic humain | ligne rouge, Brice, 2026-09-04 |
| L'outil mesure et date, il n'accuse pas | doctrine `mesure`, Brice, 2026-09-04 |
| Verdict par defaut `INDETERMINE` | referentiel V1 |
| Aucune donnee de tiers ne circule | decret 67-223 art. 32: l'extranet publie l'etat civil de tous les coproprietaires |
| Un seul endroit sait raisonner | evite deux implantations divergentes |

---

## 2. Vue d'ensemble

```
   NAVIGATEUR                        POSTE LOCAL                  ENTRE VOISINS
 ┌───────────────────┐          ┌──────────────────────┐        ┌─────────────┐
 │ lecteur (page)    │          │ CoproScope           │        │ voisin B    │
 │  - parcourt       │ releve   │  - convertit         │ export │             │
 │  - HEAD noms      ├─────────►│  - cle d'emplacement ├───────►│ recoupement │
 │  - AUCUN verdict  │  neutre  │  - couverture        │ salee  │             │
 ├───────────────────┤          │  - VERDICTS          │        └─────────────┘
 │ veille            │          │  - droit (2019-502)  │
 │  - temporisation  │          ├──────────────────────┤
 │  - diff pauvre    │          │ gouvernance.sqlite3  │
 │  - pastille       │          │  journal append-only │
 └───────────────────┘          └──────────────────────┘
```

**La ligne de partage est la seule decision d'architecture qui compte.** Le
navigateur *voit*, le poste *juge*. Le lecteur ne calcule aucune cle, n'applique
aucune regle de droit, ne rend aucun verdict.

Motif: deux implantations de la meme logique divergent toujours, et ici la
divergence se verrait au recoupement entre voisins - sous la forme d'un zero de
concordance que deux personnes liraient comme un desaccord entre elles.

L'extension porte malgre tout une comparaison *pauvre* - presence seulement -
pour pouvoir alerter sans CoproScope. Elle est bornee a une difference
d'ensembles et n'emploie aucun mot de verdict.

---

## 3. Approfondissements

### 3.1 Identite: deux cles, aucune suffisante seule

| Cle | Obtention | Cout | Injectivite mesuree | Stabilite |
|---|---|---|---|---|
| Emplacement (rubrique, groupe, libelle) | lecture du DOM | nul | **115/115** | **non mesuree** |
| Nom servi (`content-disposition`) | `HEAD` | nul | **115/115** | **non mesuree** |
| Empreinte du contenu | `GET` complet | eleve | par construction | par construction |

Les deux premieres sont injectives et aucune n'est qualifiee dans le temps.
Elles se corrigent mutuellement: quand l'emplacement conclurait au retrait, si
le nom reparait ailleurs, la piece a **bouge** et n'a pas disparu.

**Ce que l'URL n'est pas.** Elle change integralement a chaque chargement de la
meme page. Un journal indexe dessus verrait cent pour cent de documents nouveaux
a chaque passage.

### 3.2 Stockage: qui garde quoi, et pourquoi si peu cote navigateur

| Emplacement | Contenu | Duree |
|---|---|---|
| Extension | dernier releve par espace, historique borne a 12, changements | glissant |
| `gouvernance.sqlite3` | journal append-only, couverture, verdicts derives | permanent |

Le stockage d'une extension est limite - de l'ordre de 10 Mo. Un releve pese
environ 20 ko, donc l'annee tient a peu pres... et c'est precisement le piege:
**une conception qui tient "a peu pres" echoue en silence le jour du quota**,
et la perte differee est le defaut que tout ce lot combat.

L'histoire longue appartient donc au poste. On ne demande pas
`unlimitedStorage`: une permission pour un besoin qu'on n'a pas est une
permission de trop.

### 3.3 Le contenu: le trou assume, et comment le boucher partiellement

Un remplacement a place et nom constants est **invisible**. C'est le seul mode
de changement que le systeme ne voit pas.

Trois options, et leurs couts reels:

| Option | Cout par passage | Ce qu'elle donne |
|---|---:|---|
| Ne rien faire | 0 | le trou reste |
| Tout empreindre | ~6 Mo (documents), ~70 Mo (factures) | couverture totale |
| **Empreindre une liste choisie** | ~1 Mo | les pieces qui portent une decision |

**Recommandation: la troisieme.** Les pieces dont un remplacement silencieux
serait grave sont peu nombreuses et identifiables: les proces-verbaux
d'assemblee, les annexes comptables de l'exercice en cours, les contrats en
vigueur. Une quinzaine de pieces sur 115.

Surveiller tout couterait douze fois plus pour proteger des pieces dont le
remplacement n'apprendrait rien.

### 3.4 Consolidation entre voisins

Ce qui circule: empreintes salees, codes de rubrique, dates, **et la
couverture**. Cette derniere n'est pas un ornement: sans elle, un ecart entre
deux voisins ne peut pas etre trie entre *"il n'a pas regarde la"* et
*"l'extranet ne lui sert pas la meme chose"* - et seul le second est un constat.

Le sel est partage par les observateurs d'une meme copropriete. Sans lui, une
empreinte serait un **oracle**: qui detient le fichier pourrait tester une
hypothese sur un intitule en calculant son empreinte, et les intitules
plausibles sont peu nombreux.

Deux sels differents ne se recoupent pas: le systeme le **dit** au lieu de
rendre zero concordance, qui serait lu comme un desaccord entre voisins.

Compatibilite verifiee sur vecteur fige: les empreintes du plugin et celles de
CoproScope coincident.

---

## 4. Charge et fiabilite

### Estimation, par passage

| Operation | Requetes | Octets | Duree |
|---|---:|---:|---:|
| Page d'index | 1 | ~200 ko | < 1 s |
| Sondes de presence | 115 | ~0 | ~5 s |
| Sondes de nom | inclus ci-dessus | 0 | - |
| Contenu, liste choisie | ~15 | ~1 Mo | ~10 s |

A quatre passages par jour, la presence coute environ 460 requetes sans corps.
C'est modeste, et comparable a une navigation humaine attentive.

### Modes de defaillance, par gravite

| Defaillance | Consequence si non traitee | Garde |
|---|---|---|
| **Session expiree** | l'extranet rend la page de connexion; l'index parait vide; **tout disparait d'un coup** | reconnaitre la page de connexion et refuser le passage |
| Rubrique non chargee | ses pieces comptent comme disparues | ne comparer que les rubriques parcourues **des deux cotes** - fait |
| Cle non injective | deux pieces fusionnees, un retrait perdu | injectivite reverifiee **a chaque passage** - fait |
| Editeur remanie sa page | rubriques introuvables | `NON_EXPLORE`, jamais `ABSENT` - fait |
| Quota de stockage | perte differee, invisible | historique borne, histoire longue cote poste - fait |

La premiere ligne est la plus grave et **n'est pas encore traitee**. Elle le
devient si la surveillance passe en h24 sans onglet, ou la session peut expirer
sans que personne le voie.

---

## 5. Les trois arbitrages ouverts

### A. La surveillance h24 sans onglet

| Option | Ce qu'elle donne | Ce qu'elle coute |
|---|---|---|
| **A1. Au fil des visites** (actuel) | zero empreinte supplementaire; aucune requete quand Brice n'est pas la | la couverture depend de ses habitudes; rien pendant les vacances - or c'est la que le silence compte |
| **A2. Minuterie dans le service worker** | vraie periodicite, sans onglet | l'extension parle au serveur du syndic pendant qu'il dort; la session peut expirer en silence |

**Recommandation: A2, sous trois gardes fermes**, et pas sans elles.

1. **Reconnaitre la page de connexion.** Si la reponse n'est pas un index, le
   passage est refuse et enregistre comme `NON_EXPLORE`. Sans cette garde, une
   session expiree produit un evenement "tout a disparu" - le pire constat que
   l'outil sache produire, sur une panne d'authentification.
2. **Afficher la derniere tentative ET le dernier succes.** Un ecran qui ne
   montre que le dernier succes laisse croire que rien n'a change alors que
   plus rien n'est observe depuis trois semaines.
3. **Presence seulement.** Le contenu reste sur geste humain: rapatrier des
   megaoctets sans que personne regarde est un cout qu'on ne peut pas justifier.

A2 reste dans la ligne rouge - ce sont des lectures - mais elle change la
nature de l'outil, et c'est pour cela qu'elle demande un arbitrage explicite.

### B. L'integration a CoproScope

Reportee par Brice le 2026-09-06. Le code de reception existe et est teste; il
manque trois gestes: reintroduire la permission `127.0.0.1`, rappeler l'action
`transmettre` depuis la fenetre, verifier que le serveur local accepte.

Tant qu'elle n'est pas faite, **les verdicts ne sont jamais calcules**:
l'extension compte des mouvements, personne ne les qualifie au regard du decret.
C'est un systeme qui alerte sans conclure - utile, incomplet.

### C. Un second editeur

Le profil est declaratif et les six axes de generalisation sont nommes. Rien ne
prouve qu'ils suffisent: la seule epreuve est un second extranet reel.

Comportement attendu hors des valeurs observees: rubriques introuvables,
`NON_EXPLORE`, aucune absence affirmable. Degradation propre, pas de reponse
fausse.

---

## 5 bis. Deux sels, et leurs buts sont opposes

Constat du 2026-09-07, ne d'une question de Brice: *la passe d'anonymisation
instruit-elle bien un annuaire sale ?*

La reponse est **oui**. `_biffageops_parts/06_corpus_markdown.py` charge le sel
de l'instance, construit un `RegistrePseudonymes`, y inscrit chaque personne
rencontree avec son compte et le document ou elle a ete vue, sauvegarde
l'annuaire, et fait voyager l'empreinte du sel avec le rapport - de sorte que
deux passes faites sous des sels differents ne puissent pas etre confondues.

Mais verifier cela a fait apparaitre autre chose: le produit porte desormais
**deux sels que rien ne distinguait**, et leurs buts sont exactement opposes.

| | `sel_alias.key` (BiffageOps) | le sel d'echange (extranet) |
|---|---|---|
| Portee | une **instance** | une **copropriete**, partage entre voisins |
| But | que deux coffres produisent des alias **differents** pour la meme personne | que deux voisins produisent des empreintes **identiques** pour la meme piece |
| Ou il vit | `vault.local_root/corpus_caviarde/sel_alias.key`, 32 octets sur le disque, hors Git | nulle part: choisi par le conseil syndical, jamais ecrit par le produit |

Les confondre ne leve aucune erreur, et casse dans les deux sens:

- le sel d'instance employe pour l'echange: **aucun voisin ne se recoupe
  jamais**. Le rendu est un zero de concordance, que deux personnes lisent
  comme un desaccord entre elles, sur des donnees ou elles etaient d'accord;
- le sel partage employe pour les alias: deux coffres de coproprietaires
  voisins produisent le meme alias pour la meme personne, donc **deviennent
  chainables**. La garantie que BiffageOps existe pour tenir tombe, sans qu'un
  seul message ne le dise.

Trois gardes, parce qu'aucune ne suffit seule:

1. **Separation de domaine.** Les empreintes d'extranet portent un prefixe
   constant. Meme a sel egal, elles ne peuvent pas etre confondues avec une
   valeur de BiffageOps ni servir a relier les deux mondes. C'est la garde qui
   survit aux deux autres.
2. **Refus actif**, dans `extranetops.exporter_passage` - la seule couche qui
   voit a la fois l'instance et le sel. Un sel egal a celui de l'instance leve
   `SelInterdit`, avec un message qui dit les deux buts et pas seulement
   *interdit*. La lecture se fait en `create=False`: sans cela, exporter un
   journal d'extranet **fabriquerait** le sel d'alias d'une instance qui n'en a
   pas, donc le materiau d'une pseudonymisation que personne n'a demandee.
3. **Frontiere de citation**, tenue par un test qui lit le code sans sa
   docstring: le module d'echange n'emploie jamais BiffageOps, et
   reciproquement. La prose, elle, doit nommer l'autre sel - c'est ce qui
   previent la faute.

Cote fenetre, le plugin ne peut pas voir `sel_alias.key`, et deviner a la forme
du secret serait coder une modalite. Il fait donc deux choses mesurables: il dit
en une phrase que ce secret n'est pas une cle produite par CoproScope, et il
memorise le **temoin** du sel - jamais le sel - pour annoncer *"ce n'est pas le
secret de vos exports precedents"* au lieu de laisser decouvrir un zero.

**Consequence assumee:** le format d'export passe a
`coproscope.extranet.observation/2`, toutes les empreintes changent. La rupture
etait gratuite le 2026-09-07 - l'extension n'a jamais ete distribuee, aucun
export reel n'a circule - et elle ne l'aurait plus ete ensuite.


## 6. Ce que je reverrais quand ca grossit

| Seuil | Ce qui casse | Ce qu'il faudra |
|---|---|---|
| Plusieurs coproprietes par utilisateur | l'espace est identifie par le chemin d'URL seul | une cle d'instance explicite |
| Plus de trois observateurs | le recoupement deux a deux ne suffit plus | une consolidation n-aire, et un arbitrage sur qui detient le journal commun |
| Historique au-dela d'un an | la comparaison ne regarde que le passage precedent | des series temporelles, et la question *depuis quand* plutot que *qu'est-ce qui a bouge* |
| Un editeur qui pagine | la cloture `CONSTATEE` devient fausse | detecter la pagination et refuser de conclure a une absence |

---

## 7. Ce qui reste vrai quoi qu'il arrive

Le systeme repose sur une asymetrie deliberee, et elle survit a tous les
arbitrages ci-dessus:

> **Un ajout se conclut facilement. Un retrait exige tout.**

Rubrique parcourue aux deux dates, cloture permettant d'affirmer une absence,
cle injective verifiee. Faute d'une seule: `INDETERMINE`, avec son motif.

Le mode de defaillance redoute n'est pas de rater un changement. C'est d'en
inventer un - parce qu'il vise une personne identifiable, et qu'il detruirait la
credibilite du conseil syndical qui s'en sert.
