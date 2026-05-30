# Ecarts UX entre l'enquete utilisateur et le produit actuel

Date de reference : 2026-05-20

Objectif : comparer les concepts proposes pendant l'enquete utilisateurs avec l'interface actuelle CoproScope, puis proposer des pistes de realignement qui repartent explicitement de ces concepts cibles. La cible UX n'est pas le produit actuel : ce sont les quatre propositions faites au moment de l'enquete, structurees autour de **preuve + action + memoire**.

## Conclusion courte

Le produit actuel a deja rattrape une partie importante de l'intention UX : cockpit, actions, demandes, comptes guides, atelier pieces, AG/contentieux, pilotage, contexte coffre/role/sync et memoire de copropriete existent comme surfaces visibles.

L'ecart principal n'est donc plus "il manque toutes les pages". L'ecart est plus fin : l'UI expose encore beaucoup la structure interne du moteur, les ecrans restent tres tabulaires, et plusieurs parcours critiques sont encore des vues de lecture plutot que des boucles de travail completes.

Le realignement doit maintenant passer de :

- "montrer les registres et modules disponibles" ;
- vers "faire avancer un sujet avec une preuve, une prochaine action, une decision de diffusion et une trace transmissible".

## Ce que disait l'enquete

Les conclusions utiles a garder comme grille de lecture :

- le besoin n'est pas seulement documentaire ;
- les utilisateurs veulent savoir quoi faire maintenant ;
- chaque sujet doit etre relie a une piece, une demande, une decision, une depense, une preuve, une action et une restitution ;
- le conseil syndical doit pouvoir travailler sans se surexposer juridiquement ou diffuser trop largement ;
- la memoire de copropriete doit survivre aux changements de personnes, d'appareils ou de comptes.

Quatre questions produit doivent rester visibles sur chaque ecran important :

1. Qu'est-ce qui demande attention ?
2. Quelle preuve avons-nous ?
3. Quelle action est legitime maintenant ?
4. Que peut-on partager, avec qui, et sous quelle forme ?

## Etat actuel observe

Le produit actuel contient deja :

- un cockpit avec cartes `A faire maintenant` ;
- un bandeau de contexte actif pour coffre, role et synchronisation ;
- une boite `Actions` qui rassemble decisions, preuves, responsables, arbitrages et diffusion ;
- une page `Demandes` multi-canaux ;
- un controle des comptes guide avec P1, P2, OK et questions syndic ;
- une page `AG contentieux` ;
- un atelier pieces et une fiche document ;
- un depot local guide ;
- une page pilotage indicateurs ;
- une page memoire/passation.

Les tests de routes UI elargies passent sur l'instance synthetique : `tests.test_ui_smoke_routes_expanded`.

## Ecarts par concept d'enquete

| Concept cible | Produit actuel | Ecart UX principal | Realignement prioritaire |
|---|---|---|---|
| Cockpit conseil syndical | Present et oriente `A faire maintenant`. | Encore des KPI de stock, des placeholders et des liens vers modules. | Faire du cockpit une inbox de 5 cartes maximum, chacune avec raison, preuve, action, diffusion, echeance. |
| Registre decisions, actions, preuves | Page Actions solide, filtres et exports. | Beaucoup de tableau, peu de fiche action mutable, decision AG pas toujours au centre. | Ajouter une fiche action standard : contexte, message pret, responsable, echeance, preuve attendue, diffusion, journal. |
| Controle des comptes guide | Tres proche de l'intention : P1/P2/OK, questions syndic, preuves. | `ComptaScope` reste visible, les tableaux dominent, pas assez de synthese AG. | Renommer premier niveau en `Controle des comptes`, puis produire une vue `A demander avant AG / A poser en AG / Deja justifie`. |
| Memoire de copropriete | Page passation avec sujets ouverts, decisions, incidents, preuves, diffusion. | Memoire encore listee par registres, pas assez ligne de vie ni pack transmissible. | Construire une timeline passation : decisions, demandes, incidents, contrats, travaux, restrictions, dernier etat. |
| Atelier piece | Present avec documents, apercu, preuve, point, action, diffusion. | La difference document / piece / preuve reste mentale, annotations et rattachements sont surtout prepares. | Passer en layout 3 zones : file a gauche, preuve au centre, action/diffusion a droite. |
| Demandes multi-canaux | Page dediee maintenant visible. | Modele local, sans vrai cycle entree -> tri -> relance -> reponse -> preuve. | Faire de la demande un objet de travail qui cree ou rattache une action. |
| AG/contentieux | Route dediee avec prudence non juridique. | Encore lecture de dossiers plus que parcours AG complet. | Parcours `Avant AG`, `Pendant AG`, `Apres PV`, avec preuves et restrictions. |
| Droits / coffres / roles | Bandeau et gouvernance existent. | Pas encore un vrai switcher `Mes coffres`; aides `title` encore presentes. | Mettre `Coffre`, `Role`, `Acces`, `Sync`, `Derniere verification` dans un contexte global actionnable. |
| Depot local | Explique bien que rien n'est synchronise. | Boutons techniques (`DocAI`, `DocOps`) et upload encore assez moteur. | Renommer par consequence utilisateur : `Extraire le texte`, `Classer`, `Verifier diffusion`, `Rattacher aux actions`. |
| Pilotage indicateurs | Cartes avec periode, source, seuil, action. | Encore une page separee, pas assez injectee dans cockpit et decisions. | Les indicateurs ne doivent exister que s'ils ont preuve, periode, seuil et prochaine action. |

## Ecarts transverses

### 1. Le produit est large, mais le parcours est encore fragmente

La navigation couvre presque tout le champ issu de l'enquete. Le risque est maintenant inverse : l'utilisateur voit trop de portes. Il faut faire emerger trois entrees stables :

- `Aujourd'hui` : cockpit et priorites ;
- `Travailler un sujet` : piece, action, demande, decision ;
- `Transmettre` : diffusion, memoire, pack de passation.

### 2. La boucle de travail n'est pas encore assez unifiee

Les ecrans ont chacun de bonnes briques, mais chaque brique devrait porter le meme contrat :

- pourquoi ce sujet est la ;
- preuve ou source ;
- prochaine action ;
- responsable et echeance ;
- diffusion autorisee ;
- trace ou journal.

### 3. Le jargon a recule, mais il reste en premier niveau

Exemples encore visibles : `DocOps`, `ComptaScope`, `PrivacyOps / BiffageOps`, `DocAI local-heavy`, `hash`, `vault` selon les zones.

Recommandation : garder les noms moteur dans `Details techniques`, jamais dans le titre principal d'un parcours novice.

### 4. Les aides sont utiles, mais pas encore assez accessibles

Les `help-dot` en `title` aident a la souris, mais pas assez au clavier ou au tactile.

Recommandation : remplacer par des boutons d'aide avec texte au focus/clic, ou par des micro-definitions visibles.

### 5. Les tableaux restent trop souvent l'interface primaire

Les tableaux sont utiles au CS expert, mais l'enquete pointe aussi le CS fatigue, captif ou novice.

Recommandation : chaque table dense doit etre precedee d'une fiche de travail courte, puis la table devient le mode detail ou audit.

## Pistes de realignement depuis la cible d'enquete

Les visuels de cette section ne sont pas des wireframes generiques. Ils reprennent la grammaire des propositions d'enquete :

- sidebar sombre et navigation par domaines ;
- surface principale claire ;
- cartes de synthese en haut ;
- listes metier lisibles ;
- panneau de detail ou de decision ;
- mode de partage local visible ;
- actions, preuves, relances et passation dans le meme ecran.

### Piste 1 - Repartir du Cockpit Conseil Syndical

La proposition d'enquete montrait deja une vraie page d'accueil de travail : compteurs `A traiter`, quatre cartes metier, puis tableau `Alertes et risques`.

Le realignement consiste a brancher le produit actuel sur cette structure, plutot qu'a empiler toutes les routes :

- piece manquante critique ;
- relance syndic ;
- preuve a verifier ;
- decision AG sans cloture ;
- risque de diffusion.

Chaque carte doit reprendre le contrat : pourquoi, preuve, prochaine action, diffusion.

Visuel source : `docs/assets/ux-realignement-2026-05-20/01_cockpit_realigne.svg`
Rendu PNG : `docs/assets/ux-realignement-2026-05-20/01_cockpit_realigne.png`

### Piste 2 - Repartir du Registre des decisions

La proposition d'enquete etait plus forte que l'ecran actuel `Actions` : a gauche, les AG et resolutions ; a droite, la resolution choisie avec responsable, echeance, statut, pieces, preuves, relances et historique.

Le realignement consiste a faire de cette fiche decision-action-preuve la forme canonique de suivi :

- titre humain ;
- contexte ;
- decision ou demande source ;
- message pret a envoyer ;
- preuve attendue ;
- responsable ;
- echeance ;
- journal ;
- statut de diffusion.

Visuel source : `docs/assets/ux-realignement-2026-05-20/02_registre_decisions_actions_preuves.svg`
Rendu PNG : `docs/assets/ux-realignement-2026-05-20/02_registre_decisions_actions_preuves.png`

### Piste 3 - Repartir du Controle des comptes guide

La proposition d'enquete n'etait pas seulement un tableau de controles : elle ajoutait un panneau lateral de lecture pour la categorie selectionnee, avec alertes, questions au syndic et inclusion dans le rapport AG.

Le realignement consiste a rendre cette logique prioritaire :

- au centre : categories et statuts P1/P2/OK ;
- a droite : detail de la categorie, alertes, questions syndic, decision de rapport AG ;
- en bas ou en export : rapport AG lisible et prudent.

Visuel source : `docs/assets/ux-realignement-2026-05-20/03_controle_comptes_guide.svg`
Rendu PNG : `docs/assets/ux-realignement-2026-05-20/03_controle_comptes_guide.png`

### Piste 4 - Repartir de la Memoire de copropriete

La proposition d'enquete structurait la memoire comme une timeline centrale, avec un panneau droit de passation et une liste `A transmettre`. C'est plus actionnable qu'un simple regroupement de registres.

Le realignement consiste a faire de la memoire une ligne de vie transmissible :

- decisions AG ;
- demandes et relances ;
- contrats ;
- travaux ;
- incidents ;
- comptes ;
- restrictions ;
- exports de passation.

Visuel source : `docs/assets/ux-realignement-2026-05-20/04_memoire_ligne_de_vie.svg`
Rendu PNG : `docs/assets/ux-realignement-2026-05-20/04_memoire_ligne_de_vie.png`

## Priorisation recommandee

| Horizon | Priorite | Pourquoi |
|---|---|---|
| Maintenant | Harmoniser le contrat de carte/action partout. | C'est le plus fort levier pour coller a l'enquete sans casser l'architecture. |
| Maintenant | Abaisser le jargon visible et ajouter aides accessibles. | Rend le produit testable avec des novices non accompagnes. |
| Court terme | Fiche action mutable + journal. | Transforme la lecture des registres en travail CS reel. |
| Court terme | Demande -> action -> preuve. | Couvre un besoin tres fort de l'enquete : suivi syndic et demandes multi-canaux. |
| Court terme | Synthese AG pour comptes et decisions. | Aligne ComptaScope et DecisionOps avec le moment utilisateur le plus critique. |
| Moyen terme | Memoire timeline + pack passation. | Repond au CS fatigue et a la perte de memoire. |
| Moyen terme | Mes coffres / membres / droits. | Rend credible le local-first multi-coffres et l'anti-accaparement. |

## Definition d'une UI realignee

Une page CoproScope est realignee avec l'enquete si, sans lire la documentation, un membre de conseil syndical peut repondre :

- je sais dans quel coffre et quel role je suis ;
- je vois le sujet prioritaire ;
- je sais quelle preuve regarder ;
- je sais quelle action faire maintenant ;
- je sais si je peux partager, a qui, et avec quelle prudence ;
- je peux transmettre la trace a quelqu'un d'autre plus tard.
