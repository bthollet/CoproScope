# Le droit, jusque dans le code

Un contrôle de CoproScope qui s'appuie sur un texte ne devrait jamais recopier un
numéro d'article. Il cite une **clé**, et la clé renvoie à un registre qui dit quel
article a été lu, dans quelle version, et quand. Cette note montre la chaîne, puis
ce qu'elle ne couvre pas encore.

## La chaîne, sur un exemple du dépôt

1. **Le contrôle.** Dans
   [`_comptes_egalites_annexes.py`](../../server/src/coproscope/modules/_comptes_egalites_annexes.py),
   les égalités entre annexes comptables que le module rattache à l'article 10 du
   décret du 14 mars 2005 citent la clé `d05.10`. Leur méthode `citation()` ne
   contient aucun texte de loi : elle demande la source au registre.
2. **Le registre.**
   [`_budget_previsionnel_sources.py`](../../server/src/coproscope/modules/_budget_previsionnel_sources.py)
   déclare chaque source avec son article, son identifiant Légifrance
   (`LEGIARTI…`), la date de début de la version lue et la date de lecture. Un
   second registre, pour l'observateur d'extranet, a la même forme.
3. **La garde.**
   [`test_fondements_juridiques.py`](../../server/tests/test_fondements_juridiques.py)
   lit les fichiers Python de `server/src`, sans liste de fichiers. Un identifiant
   Légifrance qui n'est déclaré dans aucun registre, et qui ne figure pas dans la
   dette nommée, fait échouer la suite en nommant le fichier. Les registres sont
   trouvés par leur **forme** (un module qui expose `SOURCES: dict[str, Source]`),
   pas par leur chemin.

**Un doute ouvert sur cet exemple même.** La quatrième égalité du module, sur le
solde des travaux en attente, cite la clé `d05.annexe2`, alors que son commentaire
la fonde sur l'annexe 5. La clé est à vérifier sur Légifrance, et l'annexe 5 n'est
déclarée dans aucun registre.

## Pourquoi la date de version fait partie de la citation

Consulté à une date donnée, Légifrance marque l'article rendu `VIGUEUR`, même si
cette version a été remplacée depuis : le mot veut dire *en vigueur à la date
demandée*, jamais *à jour*. Un identifiant sans date de version n'est donc pas une
citation, c'est une référence. Le registre porte les deux.

## État mesuré le 2026-09-13

| Mesure | Valeur |
|---|---|
| Registres découverts par leur forme | 2 |
| Déclarations, avec version et date de lecture | 26 (20 + 6), pour 25 identifiants distincts |
| Identifiants Légifrance distincts présents dans le code | 44 |
| Identifiants recopiés en dur hors des registres | 28 |
| … dont absents de tout registre (dette nommée, qui ne doit pas grandir) | 19 |
| … dont déclarés, mais recopiés quand même | 9 |

## Ce que la garde ne voit pas

- **Un identifiant déclaré mais recopié ailleurs passe.** La garde vérifie qu'un
  identifiant est connu, pas qu'il est cité par sa clé : 9 cas aujourd'hui.
- **Elle ne lit que les fichiers Python.** Gabarits HTML, fichiers de
  configuration ou de données, extension de navigateur : hors de sa portée.
- **Un article cité en toutes lettres lui échappe.** Un libellé qui nomme un
  article sans identifiant n'est contrôlé par rien.
- **La découverte d'un troisième registre n'est pas éprouvée.** Le test vérifie
  que les deux registres connus sont trouvés ; aucun témoin ne fabrique un
  registre inconnu pour vérifier qu'il serait lu.

## Comment ajouter une source

Aucune règle de droit ne s'écrit de mémoire. Une nouvelle source se lit sur
Légifrance via l'API PISTE, **à une date posée explicitement**, puis s'inscrit
au registre avec son identifiant, sa version et sa date de lecture. Si la
lecture échoue ou si l'API élargit la requête, le contrôle n'est pas écrit :
il reste « à vérifier ».

CoproScope restitue ce que disent les textes. Il ne donne pas de conseil
juridique : l'interprétation d'un dossier relève d'un professionnel du droit.

## Notes liées

- [Carte des notes](carte.md)
- [Contrôle des comptes et de la gouvernance](fonction-controle.md)
- [Architecture](architecture.md)
- [Confidentialité](confidentialite.md)
