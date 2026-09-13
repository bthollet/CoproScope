# Campagne de diagnostic du 2026-09-08 - consolidation

Dispositif: 17 items diagnostiques en parallele - les cinq defauts bloquants et
les demandes de la revue vocale de Brice du 2026-09-07, plus les items P0 du
gouvernail. **Chaque diagnostic a ensuite recu un refutateur adverse charge de
le detruire, pas de le confirmer.** 35 agents, lecture seule, zero ecriture,
aucune instance lancee.

Resultat brut: **12 diagnostics tiennent, 5 sont tombes, et les refutateurs
jugent que 15 correctifs sur 16 codaient des modalites observees au lieu de
nommer un axe.** Ce dernier chiffre est le vrai enseignement de la campagne: le
defaut que ce depot combat depuis le 2026-09-04 se reproduit spontanement dans
presque tout correctif ecrit vite.

Ce document est le rendu de l agent de consolidation, repris sans reecriture.

---

**CONSOLIDATION — 16 items, lecture seule, aucune ecriture.**

---

## 1. ORDRE DE TRAVAIL

**PREMIER: B1 (pages blanches) — et le geste C4/R5, pas le geste C1.**
Motif: son `contamine` est le seul qui contamine *l'instrument de mesure lui-meme*. `construire_recette.py` ne peut echouer sur aucun des 21 scenarios; `mesure.js` s'execute meme quand la page a echoue. Tant que la recette rend vert sur une page morte, **aucune preuve produite par cette campagne n'a de valeur**, y compris les captures qui ont servi a M1, M2, B5 et S1. Un instrument qui ne peut pas echouer precede tout defaut produit.

Ensuite, par degat x cout x contamination:

| # | item | pourquoi ce rang |
|---|---|---|
| 1 | **B1** (recette seule, R5) | l'instrument; bloque la valeur de tout le reste |
| 2 | **F1** (etat des depenses) | facteur 1000 silencieux sur les montants; alimente RM-0030, RM-0075, RM-0064, RM-0082 |
| 3 | **B3** (comptes en marches) | le mauvais type est *persiste*, entre dans le rapprochement depense/facture, et fausse un chiffre deja publie (30/173) |
| 4 | **D1** (avis CS) | un faux constat de droit qui, via `pire_statut`, **trie** la colonne — pas seulement une phrase |
| 5 | **C48** (convocation) | 8 consommateurs aval lisent le type affirme sans lire le statut; + un second filtre nu hors classifieur |
| 6 | **B5** (bulles) | le panneau qui peut disparaitre est celui dont la fonction est d'empecher une fausse accusation |
| 7 | **I2** (note humaine) | `acte_id` derive → note orpheline muette; bloque toute saisie humaine future |
| 8 | **B4** (divergence) | soustractif, XS, mais deja *replique* sur l'ecran comptes a naitre |
| 9 | **P1** (vues fictives) | point de passage unique = XS; mais ordre impose (voir §4) |
| 10 | **M2 / A1 / M1 / X1 / I1 / S1 / B2 / V1** | confort, vocabulaire, ou dependants d'un prealable non fait |

**B2 et V1 en dernier**: aucun ne produit de chiffre faux. B2 coute 842 decisions humaines pour une convention qui, uniforme, se lit comme un choix.

---

## 2. CE QUI EST TOMBE

Trois refutations font tomber le diagnostic (`refut_tient: false`): **B2, B5, M2**.

- **B2** — le mecanisme 3 (« l'accueil affiche *a verifier* depuis `_public_status` ») est faux: le fichier cite n'est pas sur le chemin de la route `/`. L'auteur a **raisonne sur un nom de fonction plausible**. La vraie fuite existe ailleurs (`_summaries.py:280`, `agcontentieux_view.py:460`).
- **B5** — la troisieme valeur `non_testable` est declaree « derivee » alors qu'elle exige une table de 14 preconditions ecrites a la main. Et l'axe `source` (SOURCE_PIECES/SOURCE_OUTIL) **existait deja, declare, 30 lignes au-dessus de la ligne citee**.
- **M2** — le placement du filtre transforme un filtre d'affichage en accusation contre le pipeline (`_limites` compare une base filtree a une base complete).

**Ce que cela apprend, et c'est le meme motif trois fois:** l'auteur a lu *jusqu'a* la ligne qui confirmait son hypothese, puis s'est arrete. B2 a verifie deux lignes de tableau sur trois; B5 a cite la ligne 53 sans lire les lignes 24-51; B1 a verifie deux lignes sur quatre du tableau 3.4. **Un diagnostic doit lire le bloc entier qui contient sa citation, pas la citation.** Corollaire: la moitie des « axes » proposes reinventent, en plus etroit, un axe deja declare dans le depot (B5/`source`, I1/`Projection`, A1/`periode_lue`, P1/`identite_coque`, V1/`LIBELLES_QUALIFICATION`, I2/`en_vigueur_le`).

---

## 3. LES CORRECTIFS QUI CODENT DES MODALITES

`refut_modalites: true` sur **15 des 16**. Les huit qui comptent:

| item | modalite codee | axe a nommer a la place |
|---|---|---|
| **F1** | « une cellule par ligne » OU « un rang par ligne » — les deux aplatisseurs vus. Le split sur blanc casse `1 234,56` → facteur 1000 | **la recuperabilite de la frontiere de cellule** (coordonnees x/y → runs de blancs → rien), a niveaux de preuve mesures, jamais declares |
| **B1** | dictionnaires promus en source de verite, alors qu'ils divergent deja du corpus (STATUTS ignore `saisie`, ISSUES declare 4 pour 7 valeurs) | **le corpus ouvre les seaux, le dictionnaire ne fait que les nommer**; l'invariant est la partition (somme = total), pas la liste |
| **B3** | plage d'annees `1965..AG+5` — avale 1965 (la loi) et 1967 (le decret), que toute resolution de comptes cite | **l'atteignabilite par chute**: une branche qui n'a pas su conclure declenche le repli. Tri-etat, aucune valeur inconnue possible |
| **B2** | surface d'affichage declaree par enumeration de cles (`label`, `titre`…): 772 cles sur 781 sont dehors | **la ou la chaine devient des pixels** — rendre la route et inspecter le texte produit |
| **D1** | trois phrases cannees pour `INDETERMINABLE`, dont une inatteignable | **conjonction de termes**: chaque terme du predicat porte son libelle d'absence; un terme ajoute apporte sa phrase |
| **C48** | frontiere de bloc = {ligne vide, retour a la ligne, fin de cellule} — casse le seul titre qui marche; et « denomination en tete du nom de fichier » degrade 9/9 des fichiers de l'instance de reference | **le grade de la preuve** (denominatif vs thematique), declare par terme, defaut = thematique |
| **P1** | ensemble ferme {INSTANCE, DERIVE, DEMONSTRATION} — pas de case pour `CORRIGE_HUMAIN`, que le depot porte deja | **la provenance se derive, elle ne se declare pas** (predicat, jamais colonne — arbitrage deja rendu sur `diffusable()`) |
| **V1** | « une famille lexicale par auteur » — epuise le francais au 4e auteur, et le test est rouge des l'ecriture sur 3 paires | **tout enonce de verdict porte son auteur dans la phrase**; formateur qui exige un jeton, pas une liste de mots |

**Motif transversal, a inscrire en doctrine:** *une garantie ecrite comme une liste de causes de panne est deja perimee. Une garantie ecrite comme une conservation (somme des seaux = total lu) attrape la cinquieme cause que personne n'a imaginee.* Trois refutateurs y sont arrives independamment (B1/R2, B5/point 8, F1/garde-fou d'echelle).

**Et deux tests d'acceptation joues sur le cas favorable** — B5 (teste `avis_manquant` a zero, jamais a n>0 ou il regresse) et B3 (teste l'absence de lecture, jamais la lecture fausse). Choisir son cas, c'est passer le test sans le faire tourner.

---

## 4. LES RESIDUS QUI MERITENT LEUR PROPRE ITEM

Six, par ordre de gravite:

1. **Aucun doute n'a de lecteur.** `classification_status` absent de 4 consommateurs (C48); `A_RECLASSER` a 1 lecteur, et le meme fichier en porte deux notions concurrentes (`:160` vs `:184`); `doute` ecrite par le pont, lue par personne (A1); `discordance_intitule_corps` non affichee (M1). **Produire massivement du doute sans reconciliation aggrave le defaut numero un.** Item prealable a C48, B5, P1.
2. **`acte_id` est derive et change legitimement** (I2). Toute note humaine, tout lien, toute reference y sont exposes. Le decrochage est documente dans le depot et rien ne le detecte.
3. **Aucune garde de diffusion sur le texte libre humain** (I2, residu 3, non traite par les deux agents). Ce champ sera le plus charge en donnee personnelle du modele.
4. **`FONDE_PAR` sans producteur** (X1): `v_liens_manquants`, `v_cumul_delegation` vides, `ACTE_SANS_FONDEMENT` jamais declenchable. Une garantie qui n'a jamais pu tirer.
5. **Ordre impose P1**: le mouvement « identite reelle » livre seul fabrique 8 pages *qui ont l'air vraies* — le nom reel de copropriete au-dessus d'un contenu invente, sur deux pages dont le corps ne porte aucune marque. **Ne jamais livrer 1 sans 2.** A inscrire dans l'item, pas dans un residu.
6. **La section 3.4 du rapport du 09-04** (B1/R6): 3 lignes sur 4 irreproductibles, dont une sur une page qui ne plante pas. Regenerer en entier ou retirer — pas la seule ligne B.

---

## 5. CE QUE CETTE CAMPAGNE N'A PAS PU VOIR

Quatorze items sur seize declarent « aucune instance, aucun serveur, aucun port ». Ce qui echappe structurellement:

- **Le defaut de pixel a compte juste.** Une regle CSS qui ecrase un bloc a zero pixel de haut, une police qui ne charge pas, un contraste insuffisant: le noeud existe, le compte est bon, l'invariant de conservation passe. Nomme trois fois (B1/residu 3, M1/residu 4, S1/R5), jamais mesure. `contenu_blocs` compte des noeuds, pas des pixels.
- **L'erreur avalee par un `try/catch`** ne declenche pas `window.onerror`. Toute recette qui lit `erreurs_js` est aveugle a un echec capture — c'est le retournement du correctif B1 sur lui-meme. Seule une **declaration machine** de la page (`ETAT_RENDU`) la rend visible.
- **La branche non rendue a l'interieur d'une route couverte**: etat d'erreur, coffre vide, permission rare. Une lecture de code ne les distingue pas d'un chemin mort.
- **La chaine empaquetee** (PyInstaller/pywebview, console Windows, `#page=N` sur data-URI): zero item ne l'a eprouvee. Tout est mesure sous Jinja/uvicorn.
- **Et la modalite la plus specifique — celle qui a failli tuer la campagne:** un compteur qui bouge sous l'observateur. Un item (M1) a mesure sur un coffre reel et a du poser sa reserve; les autres ont mesure sur des chaines fabriquees passees a des fonctions pures. **Cela etablit le mecanisme et l'arithmetique, jamais un taux.** Aucun chiffre de cette campagne — 65 actes a deux seuils, 30/173, 154 avis, 261/825 — n'est une mesure de justesse; ce sont des reprises de commentaires ou des structures.

**Consequence dure:** F1, B3, C48, X1 et I2 touchent la chaine d'absorption. Leur livraison exige une instance **VIDE** qui reabsorbe les pieces d'origine des **deux** cabinets, citee avec son nombre de pieces. Une copie chargee y vaudrait uniquement pour la non-regression — et pour I2, elle est *incapable par construction* de montrer le decrochage d'identifiant.