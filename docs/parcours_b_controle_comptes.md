# Parcours B - Controler les comptes avant l'AG

Date de creation: 2026-09-02.
Parent: [`parcours_utilisateur_tests_ux.md`](./parcours_utilisateur_tests_ux.md).
Priorite Brice au 2026-09-02.

## Qui est l'utilisateur, et ce qu'il veut vraiment

Un membre du conseil syndical. Benevole, pas comptable. Il vient de recevoir la
convocation et les annexes. Il dispose de la fenetre de consultation des pieces
justificatives ouverte par l'article 18-1 de la loi 65-557, et de quelques
soirees.

Son objectif n'est pas d'utiliser CoproScope. Il est d'arriver a l'assemblee
avec quelques questions solides et fondees sur pieces, et de savoir lesquelles
des depenses sont justifiees. Trois questions precises et tenues valent mieux
que deux mille points ouverts.

Ce cadrage commande toutes les mesures qui suivent: un ecran qui produit 2 349
points a traiter a echoue, meme si chaque point est exact.

## Corpus du parcours

15 pieces, choisies pour que la verite soit calculable a la main:

- 1 etat des depenses 2025 (annexe comptable) - c'est l'etalon;
- 12 factures qui se rapprochent d'une ligne de cet etat;
- 3 factures sans ligne correspondante.

Pieges deliberes a inserer dans les 15, un par cas, pour construire la matrice
de confusion:

1. une meme facture presente deux fois, en PDF et en `.md` converti;
2. un devis, pas une facture;
3. une facture d'un autre exercice;
4. une facture sans SIREN ni SIRET;
5. un montant abime a la lecture (chiffre des milliers perdu).

Etalon a etablir AVANT de lancer l'outil, et a figer dans un fichier a part:
total des charges, montant de chaque ligne, et la reponse attendue pour chacun
des cinq pieges.

## Le cheminement, moment par moment

### Moment 1 - Le premier chiffre

Il ouvre `/comptes`. La premiere chose qu'il lit est le total des charges.

Etat au 2026-09-02: `21 994 060,46 EUR`. Somme du grand livre reconstitue:
`22 368 660,47 EUR` sur 601 lignes. Deux totaux differents pour la meme chose,
et les deux sont faux d'un facteur cent.

A tester:

- le total affiche est-il egal au total calcule a la main sur les 15 pieces;
- le total du cockpit est-il egal a celui du grand livre reconstitue;
- une piece qui n'est pas une facture peut-elle entrer dans le total.

Seuil: egalite au centime. Ce n'est pas une exigence de purete, c'est la
condition pour que l'ecran serve a quelque chose. Un total faux invalide tout
ce qui est en dessous, et l'utilisateur ferme l'outil.

Cause connue a verifier sur le nouveau corpus: quatre pseudo-factures de
`5 285 937,26 EUR` extraites d'un CSV de tableau de bord et d'un rapport
markdown, dont le champ fournisseur contient la ligne d'en-tete
`axe_id,axe,qualification_provisoir`. A elles seules 96 pour cent du total.

### Moment 2 - Le volume qu'on lui demande de traiter

Il regarde combien de travail l'attend.

Etat au 2026-09-02: 2 349 points `P1 a traiter`, 827 `P2 a confirmer`, et sur
`/comptes/factures-a-revoir`, 790 factures dont 684 `anomalies critiques` et
535 `incertaines`.

A tester, et c'est la mesure la plus importante du parcours:

- combien de points sortent sur 15 pieces;
- combien de ces points meritent d'etre poses a un syndic.

Seuil propose: **au plus 20 points**, soit une soiree de travail. Au dela,
l'ecran ne trie plus, il deverse. Si 15 pieces produisent encore des dizaines
de points, le probleme n'est pas le volume d'entree mais la regle de generation.

Verifier aussi la coherence interne des compteurs: au 2026-09-02,
`254 a controler` plus `535 incertaines` font 789 et non 790, et les
`684 anomalies critiques` depassent les `254 a controler`.

### Moment 3 - Comprendre pourquoi une ligne est la

Il ouvre une ligne. Il veut savoir ce qu'on lui reproche.

Etat au 2026-09-02: 24 points affichent le meme texte a l'identique,
`ETAT_DEPENSES_A_FOURNIR`, `Controle comptable`, meme motif, meme suite a
donner. Zero information distinctive. Cote factures, la colonne
`FACTURE DETECTEE` affiche des titres markdown: `# Approfondissement anomalies
prioritaires`, `# Demande de pieces priorisee`, rattaches au compte
`622000 honoraires_syndic`.

A tester:

- deux lignes differentes portent-elles deux motifs differents;
- le motif nomme-t-il la piece et le montant en cause, ou reste-t-il generique;
- une ligne dont le motif est identique a une autre est-elle un doublon.

Seuil: aucun motif strictement identique sur deux lignes distinctes. Un texte
repete a l'identique n'est pas un diagnostic, c'est un remplissage.

### Moment 4 - Le rapprochement quatre sources

C'est le meilleur ecran du produit et il faut le dire: comptabilite, banque,
facture, decision ou devis, avec pour chacune un statut explicite et le refus
de conclure sur la facture seule. La doctrine de preuve est juste.

Etat au 2026-09-02, sur `/comptes/rapprochement`:

- le titre de la page devient `CoproScope - Copropriete FICTIVE` alors que les
  lignes affichees sont les vraies factures de l'instance;
- le montant s'affiche `73333.05 EUR`, non formate, quand la ligne voisine
  affiche `180,00`;
- une ligne porte `Designation` comme libelle et `180,00` comme valeur.

A tester:

- les quatre sources sont-elles renseignees a partir des vraies pieces du
  corpus;
- un rapprochement propose est-il exact, verifie a la main;
- l'identite de la copropriete affichee est-elle toujours la bonne.

Seuil sur le dernier point: aucune page ne doit afficher `Copropriete FICTIVE`
en presentant des donnees reelles. Sept vues portent cette substitution:
`activity_view.py:273`, `coffre_partage_view.py:108`,
`compta_rapprochement_fallback.py:50`, `contractops_view.py:394`,
`courriers_preuves_view.py:150`, `governance_atelier_ag_view.py:152`,
`governance_cr_cs_view.py:116`. Pour un outil de preuve, melanger une etiquette
fictive et un contenu reel est un defaut de surete, pas de presentation.

### Moment 5 - Trancher

Il decide. Les gestes offerts sont bons: marquer comme relu, garder une reserve,
preparer une question au syndic, demander une decision ou un devis, ecarter le
rapprochement. Et la mention est juste: cette action ajoute seulement une trace
locale, elle ne valide pas la comptabilite officielle.

A tester:

- les cinq gestes enregistrent-ils reellement quelque chose;
- la trace survit-elle a la fermeture du navigateur, puis a l'arret du serveur;
- une ligne tranchee sort-elle de la file, ou revient-elle a chaque passage;
- deux gestes contradictoires sur la meme ligne sont-ils possibles.

Seuil: apres redemarrage du serveur, l'utilisateur retrouve exactement l'etat de
son travail. Un controle de comptes se fait sur plusieurs soirees. Si le travail
ne survit pas, personne ne le commence.

### Moment 6 - Le livrable

Il veut sortir la liste des questions a poser au syndic.

Etat au 2026-09-02: `questions_syndic_comptascope_2025.md` fait **14 891
lignes**. On y lit un fournisseur nomme
`"resultat_id","acteur","controle","sources_utilisees",...`, des montants
`- EUR`, et des phrases mal formees:
`Pouvez-vous transmettre l'piece comptable (73333.05 EUR) ?`, sous un objet
`Controle comptes 2025 - piece comptable - Vid`.

A tester:

- longueur du livrable sur 15 pieces;
- le texte est-il envoyable tel quel a un professionnel, sans reecriture;
- montants formates, elisions correctes, aucun fragment technique visible;
- le livrable cite-t-il la piece source de chaque question.

Seuil: **un document qu'on peut envoyer sans le retoucher**. C'est le seul test
qui compte a ce moment. Un livrable qu'il faut reecrire n'a rien fait gagner, et
un livrable de 14 891 lignes ne sera pas relu, donc pas envoye.

### Moment 7 - Le retour

Il envoie hors CoproScope, le syndic repond, il rattache la reponse.

A tester:

- le chemin de retour existe-t-il depuis le controle des comptes;
- la reponse rattachee change-t-elle le statut de la ligne d'origine;
- la ligne peut-elle etre close avec preuve.

Ce moment recoupe le Parcours C. Verifier surtout qu'il n'y a pas de rupture:
une question posee depuis les comptes doit se retrouver dans les demandes.

### Moment 8 - Ce qui ne doit jamais arriver

- aucun envoi automatique vers le syndic ou l'exterieur;
- aucune conclusion de conformite sans preuve rattachee;
- aucun chemin local, nom brut ou identifiant interne visible dans une sortie
  destinee a etre diffusee;
- aucune piece du corpus modifiee dans `raw/`.

A verifier apres chaque execution: comparer les empreintes de `raw/` avant et
apres.

## Ce que le parcours mesure, en resume

| Mesure | Seuil |
|---|---|
| Ecart du total affiche au total calcule a la main | 0,00 EUR |
| Points a traiter generes sur 15 pieces | au plus 20 |
| Motifs strictement identiques sur deux lignes | 0 |
| Non-factures entrees dans le total | 0 |
| Pieges detectes sur les 5 poses | 5 |
| Pages affichant `Copropriete FICTIVE` avec des donnees reelles | 0 |
| Travail retrouve apres redemarrage | integral |
| Retouches necessaires avant envoi du livrable | 0 |
| Pieces de `raw/` modifiees | 0 |

## Ordre d'execution

1. Etablir l'etalon a la main et le figer, avant toute execution de l'outil.
2. Construire l'instance `tests_ux` avec les 15 pieces et les 5 pieges.
3. Executer le pipeline, puis parcourir les moments 1 a 8 en `Mode test`, en
   annotant chaque ecran.
4. Exporter les annotations et les confronter a l'etalon.
