# Tri du backlog du 2026-09-09

**33 agents, 0 erreur, 73 items soumis.** Chaque verdict *deja fait* devait
etre attaque par un refutateur charge de retrouver la preuve lui-meme.

**Le resultat le plus utile de cette note est qu'elle se declare peu fiable:**
sur cinq verdicts `DEJA_FAIT` contre-enquetes, **trois sont tombes**. Dix
autres n'ont jamais ete contredits et ne doivent donc pas etre fermes.

---

# Note d'eclusage du backlog — ce que le tri permet de fermer, et ce qu'il ne permet pas

## 1. Le compte

**31 items ont ete tries** sur les 79 declares ouverts. 48 n'ont pas ete regardes du tout.

| Verdict rendu | Nombre |
|---|---:|
| `DEJA_FAIT` | 15 |
| `FAIT_SANS_GARDE` | 2 |
| `OUVERT` | 14 |
| `PERIME` | 0 |

**Le chiffre qui compte: 5 verdicts `DEJA_FAIT` ont ete soumis a une contre-enquete, et 3 sont tombes.** Soit 60 %. Les trois abattus sont `RM-2026-0004`, `RM-2026-0049` et `RM-2026-0051`. Les deux confirmes sont `RM-2026-0053` et `RM-2026-0054`.

**Consequence directe: ce tri n'est pas assez fiable pour fermer 15 items.** Il reste dix `DEJA_FAIT` que personne n'a essaye de casser.

**Et la raison des trois chutes est unique, ce qui est une bonne nouvelle.** Dans les trois cas, le tri a verifie que le **livrable existe**, pas que le **mandat** ecrit dans la colonne description etait rempli.

- `0004` — le titre dit *coffre verifiable et evenements signes*: c'est fait, et garde par 18 tests. Mais la colonne description demande une recette navigateur et un profilage de performance. Aucun des deux n'a ete fait, et un NO-GO a 8 secondes est debout depuis le 22 mai.
- `0049` — les cinq livrables existent. Mais le document est bati sur un etalon refute le lendemain de son ecriture: il prescrit encore des ecrans pour *34 resolutions* et une assemblee qui n'existe pas au dossier, alors que la vraie mesure est 55 resolutions.
- `0051` — le mandat demandait de chiffrer **cinq criteres**. Trois l'ont ete. Le tri a lu *cinq defauts* a la place de *cinq criteres*.

Le remede est bon marche: pour chacun des dix `DEJA_FAIT` restants, relire la colonne description de la ligne, pas son titre. Dix minutes par item.

---

## 2. A fermer tout de suite

**Deux items ont un verdict qui a ete attaque et qui a tenu:**

- **`RM-2026-0053`** — decision de ne PAS integrer, verifiee de quatre facons: le commit n'est pas dans HEAD, le fichier livre est absent de l'arbre, aucune trace du contenu par `git log -S`, et le remplacant est en place. Il n'a produit aucun code, donc il n'y a aucune garde a ecrire.
- **`RM-2026-0054`** — merge `7c2001a` present dans HEAD, 52 tests verts que j'ai fait rejouer, cinq modules d'ecran l'importent, et le pont est branche dans la chaine d'absorption. Les quatre decisions back exigees sont tenues une par une.

**Huit autres ont une preuve solide — un test nomme et execute — mais leur mandat n'a pas ete relu:**

| Item | Preuve en une ligne |
|---|---|
| `0056` | 21 tests verts, zero faux positif sur 37 documents et deux cabinets |
| `0057` | 3 tests verts; au passage, la cause annoncee par le titre est fausse — ce n'etait pas l'ordre d'execution mais un checksum finissant par zero une fois sur seize |
| `0059` | garde qui balaie tous les ecrans sans liste en dur, 3 tests verts, huit ecrans aveugles trouves |
| `0062` | 11 tests verts, dont ceux qui prouvent que la detection n'est pas affaiblie |
| `0069` | 8 tests verts, le chemin de retrait d'un alias existe enfin |
| `0070` | 37 tests verts, six colonnes en production |
| `0055` | maquettes livrees, disposition tranchee par la mesure, une cible manquee d'1 px et declaree comme telle |
| `0071` | mesure faite et tracee — mais l'instance a ete supprimee depuis, donc fermeture **sur trace**, pas sur mesure rejouable |

---

## 3. A garder, mais a tenir — la correction existe, le test manque

- **`RM-2026-0050`** (corpus de reference). Corpus et etalon faits. **Manque la reconciliation entre les fichiers sur le disque et le manifeste — et elle echoue deja**: un PDF de 35 pages est present sans aucune ligne de manifeste, donc sans provenance ni statut de pseudonymisation, et c'est justement la piece etalon du parcours comptes. Le document annonce cette piece comme absente alors qu'elle est la. Cout: un petit script d'instance (le corpus est hors Git, ce ne peut pas etre un test de la suite) plus un arbitrage sur la garde de pseudonymisation.
- **`RM-2026-0060`** (regle des axes). Doctrine ecrite, appliquee une fois. **Manque un balayage qui echoue quand un extracteur est livre sans sa section d'axes.** Le patron existe deja deux fois dans le depot. Cout moyen: l'ecriture est simple, le travail est de definir ce qui compte comme extracteur et de borner la dette existante.
- **`RM-2026-0049`** (requalifie par la contre-enquete). Livrables la, contenu a recaler sur le vrai etalon — six passages prescriptifs. **Manque une garde qui echoue quand une valeur refutee reapparait dans `docs/` sans rectification datee.**
- **`RM-2026-0051`** (requalifie). Livrable la, deux criteres sur cinq jamais mesures — precisement les deux qui exigent d'ecrire dans le produit et d'en sortir un livrable, les deux gestes que l'audit s'etait interdits.
- **`RM-2026-0067`** (a requalifier). Le correctif existe et **precede l'item de trois mois**; aucune garde ne le tient.

---

## 4. Perimes et doublons

Aucun verdict `PERIME` n'a ete rendu, mais il y a des morceaux perimes **a l'interieur** d'items ouverts:

- **`0003` et `0008` attendent tous deux « apres la reconstruction »** — c'est-a-dire `RM-2026-0017`, **abandonne depuis le 31 mai**. Deux items attendent depuis trois mois un evenement qui n'arrivera jamais. `0008` est actionnable immediatement et personne ne l'a vu.
- **`0045`** reclame des poignees livrees le jour meme ou la ligne a ete ecrite, et une integration faite le 2 juin.
- **`0004`, `0051`, `0071`** nomment une instance qui n'existe plus sur le poste. C'est exactement le motif deja grave dans les consignes: une consigne qui pointe vers rien coute plus cher qu'une consigne absente.
- **`0067`** — defaut bien mesure, mais sur une maquette autonome et non sur l'application.

Doublons a trancher:

- **`0065` / `0097` / `0099`: trois items pour une seule ligne de code** (la garde du patronyme seul). Aucun chantier ne doit s'ouvrir avant de dire lequel porte la reparation.
- **`0052` se decompose en trois**: defaut 1 couvert par `0056` + `0061`, defaut 2 fait et garde, seul le defaut 3 survit — et il double le defaut D1 de l'audit `0051`. L'item devrait fondre en une seule ligne fusionnee.
- **`0004` (moitie perf), `0006` et `0016`** visent le meme sujet: deux routes lentes et leur read model.
- **`0063` ne couvre qu'une partie du residu de `0049`** — les deux couples fournisseur/montant, pas les 34 resolutions ni l'assemblee fantome. **Le gros du residu n'est porte par aucun item.**

---

## 5. Ce qui reste vraiment ouvert, par sujet

**1. Les documents de reference enseignent un faux etalon.** (`0063` elargi, residu de `0049`, plus la gate de sortie du lot gouvernance encore ecrite contre 34 resolutions.) *En premier parce que* c'est du texte, donc peu cher, et que chaque jour ou ca reste, un nouveau lot repart d'un chiffre faux. Une gate, ca se franchit. Debloque la fermeture de `0049`.

**2. La moitie outillage du caviardage.** (`0068`.) *Tot parce que* elle debloque un push GitHub suspendu, et que la regle a porter existe deja dans le produit — il s'agit de la recopier. A noter: la moitie produit etait reparee depuis cinq jours quand le push a ete suspendu sur sa foi.

**3. Les arbitrages qui n'appartiennent pas a un agent.** (`0059` brancher ou retirer huit ecrans; `0065`/`0097`/`0099`; `0027` la cible syndic benevole; `0048` le contrat de liens.) Zero code, et trois d'entre eux immobilisent du travail. A passer en attente d'arbitrage plutot qu'en P0 actif: sinon ils comptent comme du travail alors qu'ils attendent une phrase.

**4. L'ecran de gouvernance est livre, mais deux de ses cinq tables n'ont aucun producteur en production.** (Residu de `0054`.) Elles ne sont ecrites que par les tests. Consequence mesurable: trois familles de constats ne peuvent rendre aucune ligne. A rapprocher du constat deja commite — l'ecran n'est remplissable par aucun chemin documente. *Ici parce que* c'est le risque d'un ecran qui affiche du vide en silence.

**5. La provenance a l'ecriture.** (`0061`.) Cher, mais c'est la racine: tant que la provenance se deduit du chemin, elle degenere, les documents de travail se melangent aux pieces recues, et la moitie provenance de `0056` reste impossible. **Piege a ne pas rater:** les 53 sites d'ecriture sont eux-memes une enumeration de modalites — passer par un point d'ecriture unique, pas par 53 rappels a la vigilance. Touche la chaine d'absorption, donc epreuve sur instance vide.

**6. Le doute est calcule puis jete.** (Residu de `0053`, a verser dans `0056`.) Le classifieur ecrit deux etats de doute; aucun des deux n'apparait dans la couche web. Une piece douteuse n'entre jamais dans la boite de reception. Petit a moyen, tres visible pour l'utilisateur.

**7. Performance et recette navigateur.** (`0006`, `0016`, moitie perf de `0004`.) **Premier geste obligatoire: remesurer.** Les 22,4 s et 17,2 s viennent d'instances de mai qui n'existent plus. `0016` bloque `0006`.

**8. Packaging.** (`0007`, `0014`.) Avant tout code: **la documentation ment** — le bouton « changer de coffre » appelle une fonction qui n'a aucune implementation, et le pont n'est pas branche. Il affiche « disponible dans la fenetre CoproScope » a l'interieur de cette fenetre. Ensuite seulement, faire trancher si la « vraie coedition » est toujours promise. `0014` bloque `0007`.

**Dependances a retenir:** `0016` → `0006` · `0014` → `0007` · `0061` → moitie provenance de `0056` · `0063` elargi → `0049` · `0068` → push suspendu · et `0017` etant abandonne, **il ne bloque plus ni `0003` ni `0008`**.

---

## 6. Ce que ce tri n'a pas pu decider

1. **Dix `DEJA_FAIT` n'ont jamais ete contredits**: `0055`, `0056`, `0057`, `0059`, `0062`, `0067`, `0069`, `0070`, `0071`, `0076`. Au taux constate, environ six tomberaient. Les deux plus suspects, par leur propre texte: **`0076`**, dont le verdict admet qu'une mesure avant/apres exigee sur 3 447 documents n'a jamais ete produite alors que le bareme a bien ete touche; et **`0067`**, dont le verdict admet qu'aucune garde n'existe. *Pour trancher: relire la colonne description, pas le titre.*
2. **48 items du backlog n'ont pas ete regardes.**
3. **Quatre arbitrages du blueprint** que le document renvoie explicitement a toi — il ecrit « a confirmer par Brice » et « je refuse de trancher dans un blueprint ». Aucune trace d'une confirmation. *Pour trancher: une phrase de toi, ou une convention disant qu'un arbitrage de coordinateur suffit.*
4. **`0047`** est parque volontairement et sa verite vit hors depot: indecidable depuis le depot, par construction. *Pour trancher: nommer dans la ligne une source hors depot et une date de dernier point.*
5. **Trois mesures ne sont plus rejouables** (`0004`, `0051`, `0071`): les instances sont supprimees. *Pour trancher: une instance de lot fraiche et une remesure, ou un classement perime assume avec successeur borne.*
6. **Une incoherence de dates**: un merge date du 3 septembre a 02h40 est motive par un compte rendu date du meme jour a 23h55. Une des deux dates est fausse. Petit, mais il affaiblit tout raisonnement fonde sur la chronologie.

---

**Ce que je ferais de cette note, dans l'ordre:** fermer les deux items confirmes; passer une heure et demie a relire la colonne description des dix `DEJA_FAIT` non contredits; rendre les quatre arbitrages du point 3 de la section 5, qui ne coutent rien et debloquent trois chantiers.
