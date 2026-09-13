# Blueprint - panneau de conformite de la fenetre du plugin

Rattachement: `RM-2026-0091` / `CH-20260907-002116-RM-2026-0091-liste-legale-et-veille-continue` / `CONV-2026-2144`.
Date: 2026-09-07. Brouillon cliquable associe:
[`assets/brouillon_popup_conformite_2026-09-07.html`](./assets/brouillon_popup_conformite_2026-09-07.html).

## Ce que cet ecran doit faire, en une phrase

Repondre a *"qu'est-ce qui manque chez moi, et sur quel fondement"* sans jamais
affirmer un manque que l'observation ne permet pas d'affirmer.

## Ce qu'il remplace

Le panneau actuel *Ce que vous savez devoir exister* liste les **8 rubriques de
l'editeur** et accepte un nombre par rubrique. Il ne sait pas exprimer deux des
trois manques nommes par Brice le 2026-09-06:

| Manque nomme | Pourquoi il est inexprimable aujourd'hui |
|---|---|
| Reglement de copropriete | Exprimable: la rubrique `REG` sert cette seule obligation. C'est le seul des trois qui marchait. |
| Contrats | La rubrique `CON` agrege **quatre** obligations du decret. Un seul nombre ne peut en designer aucune. |
| Banque | N'est pas une rubrique. Les releves du compte separe sont ranges dans *Documents divers*, la categorie fourre-tout. |

## Structure, du haut vers le bas

```
+--------------------------------------------------+
| Observateur d'extranet                           |
| Lecture seule. Rien n'est envoye a votre syndic. |
+--------------------------------------------------+
| SYNTHESE            <- le "1 coup d'oeil"        |
|   N obligations incompletes sur 18               |
|   espace observe + date du releve                |
|   puces: incompletes / servies / non rattachees  |
|          / non parcourues                        |
+--------------------------------------------------+
| [ College A ]                                    |
|   > obligation .................. [etat]         |
|   > obligation .................. [etat]         |
| [ College B ]  ...                               |
| [ College C ]  ...                               |
+--------------------------------------------------+
| PIED: ce qui n'est pas rattache, et pourquoi     |
|   [Rattacher les N restantes] [Enregistrer]      |
+--------------------------------------------------+
```

Une obligation **repliee** montre trois choses et pas une de plus: son
intitule, son identifiant, son etat. C'est ce qui rend la liste balayable a
dix-huit lignes.

Une obligation **depliee** montre, dans cet ordre:

1. le compte - *N pieces vues sur M attendues, dans la rubrique X*;
2. le rattachement, modifiable;
3. l'attendu, modifiable **seulement** si le texte ne le fixe pas;
4. le fondement, avec `LEGIARTI`, version et date de lecture;
5. ce qui reste a verifier a la main.

## Les quatre etats, et le mot exact

| Etat | Mot a l'ecran | Ce qu'il ne doit jamais laisser croire |
|---|---|---|
| `SERVI_EN_APPARENCE` | *servi en apparence* | jamais *conforme*: une attestation perimee occupe la rubrique aussi bien que la bonne piece |
| `NON_SERVI` / ecart | *N manquent* | rien: c'est le seul etat accusatoire, et il exige un rattachement exclusif |
| `NON_RATTACHE` | *a rattacher* | jamais *manquant*: le plugin ne sait pas ou c'est range, il ne dit pas que ca n'existe pas |
| `NON_PARCOURUE` | *non parcourue* | jamais *absent*: on ne conclut que sur ce qu'on a regarde |

## Trois refus, et ils sont la matiere de l'ecran

**Refus 1 - ne pas chiffrer un ecart sur un emplacement partage.** Douze pieces
dans *Contrats* ne disent pas combien sont des assurances. L'ecran affiche le
compte et **dit pourquoi il ne le repartit pas**. Un chiffre faux se cite; une
absence de chiffre ne nuit pas.

**Refus 2 - ne pas deviner un rattachement.** Aucune page d'extranet ne cite le
decret. A la premiere ouverture chez un syndic inconnu, l'ecran affiche
**18 obligations a rattacher et zero manque affirme**. C'est l'etat B du
brouillon, et c'est le comportement attendu, pas un ecran vide.

**Refus 3 - ne pas lire la liste des coproprietaires.** `EXT-C-04` se constate
presente ou absente. L'ecran le dit en clair, et renvoie la verification de
completude a CoproScope, apres pseudonymisation - `RM-2026-0095`.

## Ce qui est hors de cet ecran

- tout verdict de conformite: il exige de lire les pieces (`RM-2026-0093`);
- tout envoi vers le syndic: la ligne rouge tient, l'ecran ne fait que lire;
- toute integration a CoproScope: reportee par Brice le 2026-09-06.

## Criteres d'acceptation

1. A la premiere ouverture chez un syndic inconnu: 18 lignes, zero manque
   affirme, et une phrase qui dit pourquoi.
2. Le cas reel de Brice - 18 actes vus, 24 declares - affiche *6 manquent* et
   le fondement de l'obligation.
3. Une rubrique non ouverte au dernier passage n'affiche jamais de manque.
4. Le mot `conforme` n'apparait nulle part, sauf dans la phrase qui dit qu'il
   ne s'applique pas.
5. Un ecart n'est chiffre que si l'emplacement sert cette seule obligation.

## Qualification novice

Jouee par le fil pilote, faute de thread disponible, et tracee comme telle.

| Question | Reponse attendue en lisant l'ecran | Verdict |
|---|---|---|
| *Qu'est-ce qui manque chez moi ?* | La synthese en tete le dit en un nombre, et les lignes rouges le detaillent. | GO |
| *Pourquoi certaines lignes ne disent rien ?* | Le pied de l'ecran l'explique en une phrase, sans jargon. | GO |
| *Est-ce que mon syndic est en regle ?* | L'ecran refuse de repondre, et dit ce qui reste a verifier a la main. | GO - c'est le comportement voulu |
| *A quoi sert `EXT-A-01` ?* | L'identifiant est visible mais gris et secondaire; l'intitule porte le sens. | GO avec reserve: a surveiller si le novice le lit comme un code d'erreur |

**Reserve tracee:** l'ecran affiche dix-huit lignes dans une fenetre de 380
pixels. La qualification a ete faite sur le brouillon, pas sur la fenetre
reelle. Si le balayage se revele penible a l'usage, le repli par defaut des
colleges B et C est la premiere correction a essayer.
