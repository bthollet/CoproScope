<!-- Aucun nom reel, aucune adresse, aucun montant reel dans ce document. -->

# Quand la conclusion contredit les faits imprimés juste à côté

*2026-09-09. Généralisation née d'un échange entre deux conversations, après
qu'un même motif a été rencontré cinq fois en deux jours par trois lots qui ne
se parlaient pas.*

---

## Le motif, en une phrase

> **L'information exacte est présente. La conclusion tirée à côté d'elle la
> contredit. Et c'est la conclusion qui est lue.**

Ce n'est pas un défaut de mesure : la mesure est juste, elle est écrite, elle
est même souvent écrite *dans la même ligne*. Le défaut est au moment où
quelqu'un — un humain, une agrégation, un calculateur de statut — en tire un
verdict sans le dériver d'elle.

## Cinq occurrences, toutes mesurées

**1. Le pixel que le livrable déclare lui-même manquer.**
`docs/maquettes_controle_2026-09-03.md` ligne 120, dans son propre tableau de
cibles : `| Haut de la matrice | sous 520 px | 521 - manque de 1 px |`. Un
lecteur a cité ce **521** comme *preuve que la mesure avait été faite*, et a
proposé la fermeture de `RM-2026-0055`. Le document disait la vérité, y compris
son échec ; le lecteur a lu le chiffre sans lire la cible d'à côté.

**2. Le verdict qui liste ses pertes et se déclare réussi.**
Le passage d'absorption rendait `status: ok` **en listant 84 clés écrasées** dans
le même objet. Corrigé : `server/src/coproscope/core/_pipeline_verdict.py`
dérive désormais le statut de ce que les étapes déclarent, et **une étape qui ne
déclare rien n'est plus réputée réussie**.

**3. `OK (skipped=4)`.**
Le lanceur de tests imprime exactement le nombre de tests sautés, à côté du mot
`OK`. La confrontation à l'étalon est restée inerte pendant deux jours ainsi :
son instance avait été supprimée, ses quatre tests sautaient, et le module
annonçait `OK`.

**4. `Ran 0 tests — OK (skipped=1)`.**
Le panier de régression live (`RM-2026-0006`) annonce un succès **en ayant joué
zéro test**, parce qu'il s'active par une variable d'environnement que personne
ne pose. Le compte est exact et affiché ; le mot qui est lu est `OK`.

**5. Un fait qui devient une réclamation en montant d'un étage.**
Mesuré par la conversation voisine : une cellule dit *« aucun devis rattaché »*,
ce qui est un **fait**. L'agrégation qui groupe ces cellules et les verse dans un
brouillon de courrier en fait une **exigence**. Sur corpus reconstruit : 400
actes sans devis rattaché, dont **10 seulement** relèvent d'un seuil de mise en
concurrence. Un courrier bâti sur l'agrégation aurait noyé les dix vrais dans un
rapport de bruit de 39 pour 1.

## Ce que ces cinq cas ont en commun, et qui les distingue d'un défaut de mesure

Dans les cinq, **la donnée juste est disponible au moment où le faux jugement se
forme**. Rien n'a été perdu, rien n'a été mal lu, aucun extracteur n'a échoué.
Le verdict a simplement été **calculé à côté** des faits au lieu d'être calculé
**à partir** d'eux.

C'est pourquoi aucune de nos gardes ne l'attrapait : elles vérifient toutes que
la mesure est juste. Aucune ne vérifie que **la conclusion est cohérente avec ce
qui est imprimé à côté d'elle**.

**À ne pas confondre avec la troncature muette**, rencontrée le même jour : la
synthèse automatique du tri du backlog a reçu 73 instructions coupées à 110 000
caractères et a annoncé en couvrir 18, sans dire que 55 manquaient. Là,
l'information **n'était pas présente** au moment de conclure. C'est un cousin,
pas le même défaut, et le remède diffère : déclarer ce qu'on n'a pas vu, contre
dériver ce qu'on affirme.

## Le remède, et il n'y en a que deux

**(a) Dériver le verdict des faits, jamais le calculer en parallèle.**
C'est ce que fait `_pipeline_verdict.py` : le statut n'existe pas comme donnée
propre, il est une fonction de ce que les étapes déclarent. Un fait nouveau
change le verdict sans qu'on ait à y penser.

**(b) Quand la dérivation est impossible, rendre le fait impossible à
contourner.** Un lanceur de tests ne se réécrit pas ; on peut en revanche
refuser qu'un module ne mesure rien, faire dire au motif de saut *ce qui n'a pas
été vérifié*, ou faire échouer un panier qui joue zéro test.

**Ce qui ne marche pas : imprimer le fait plus gros.** Les cinq cas l'imprimaient
déjà, et l'un le mettait même en gras dans son propre tableau.

## Le test d'acceptation, à appliquer à tout verdict

> **Si un fait défavorable apparaissait demain dans les données que ce verdict
> côtoie, le verdict changerait-il tout seul ?**

Si la réponse est non, le verdict est calculé à côté de ses faits, et il finira
par les contredire. Ce n'est pas une question de rigueur du rédacteur : les cinq
occurrences ci-dessus ont été produites par des lots attentifs, dont deux
avaient écrit la mesure exacte de leur propre main.

## Portée

Cette règle s'applique à tout objet qui porte **un jugement et ses pièces au même
endroit** : un statut de passage, une ligne du gouvernail (statut d'un côté,
preuve de l'autre), une cellule de contrôle et son agrégation, un rapport
d'audit, le résultat d'une suite de tests.

Elle est parente de la règle des axes sans s'y réduire. La règle des axes dit :
*ne code pas les valeurs que tu as vues.* Celle-ci dit : *ne conclus pas à côté
des valeurs que tu as sous les yeux.* La première protège l'entrée, la seconde
la sortie.
