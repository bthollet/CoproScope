# Ecarts visuels live 8766 vs captures Canva - 2026-05-21

## Perimetre

Comparaison visuelle des 4 blocs primaires demandes, a partir des images Canva dans `docs/assets/etude-utilisateurs/` et des captures live dans `docs/assets/ux-livraison-reelle-2026-05-21-8766/`.

Paires analysees :

| Route / bloc | Cible Canva | Capture live 8766 |
| --- | --- | --- |
| Cockpit Conseil Syndical | `cockpit-conseil-syndical.png` | `01_cockpit.png` |
| Registre decisions / actions / preuves | `registre-decisions-actions-preuves.png` | `02_actions.png` |
| Controle des comptes | `controle-comptes-guide.png` | `03_comptes.png` |
| Memoire de copropriete | `memoire-copropriete.png` | `04_memoire.png` |

Note de cadrage : les cibles sont des vues desktop larges, environ 1672x941 ou 1693x929. Les captures live sont toutes en 999x693. Une part des ecarts de densite vient donc du viewport, mais les ecarts principaux sont structurels : le live affiche une couche locale/contexte qui n'existe pas dans les cibles, repousse les vrais contenus sous la ligne de flottaison, et remplace plusieurs layouts operationnels par des cartes introductives.

## Legende priorites

| Priorite | Definition |
| --- | --- |
| P0 | Bloque la reconnaissance de l'ecran cible ou change le flux principal attendu par l'enquete. |
| P1 | Ecart majeur de proportions, hierarchie, navigation ou composants, visible des la premiere impression. |
| P2 | Ajustement de finition : libelles, densite, etats, micro-alignements. |

## Diagnostic global

### Premiere impression

La cible Canva donne l'impression d'un outil de pilotage de copropriete deja operationnel : navigation stable a gauche, titre de page clair, recherche et actions dans l'en-tete, puis donnees metier immediatement visibles. Le live donne plutot l'impression d'un environnement local/admin a securiser avant usage : "COPROSCOPE LOCAL", chips de coffre, cartes "Contexte actif", "Role", "Sync", "Coffre signe", puis seulement ensuite le contenu metier.

Ecart P0 : le bloc de contexte local occupe le premier ecran sur Cockpit et Registre, et disparait seulement partiellement sur les autres routes. Il doit devenir un statut discret, un tiroir ou une aide repliee, pas le premier objet de la page.

### Proportions et viewport

Les captures live sont beaucoup plus etroites que les cibles : ratio 1.44 contre 1.78/1.82. La sidebar live garde environ 276 px, soit pres de 28% de la largeur, contre environ 16-17% dans Canva. Le contenu principal est donc compresse, les titres wrappent, les boutons se coupent ("Nouvelle deman..."), et les grilles descendent sous le fold.

Recommandation P1 : pour la QA visuelle, recapturer a un viewport desktop proche des Canva, puis corriger le layout responsive a 999 px : sidebar compacte/collapsible, largeur minimale de workspace, boutons non tronques, pas de grille 3 colonnes si l'espace disponible ne le permet pas.

### Navigation / sidebar

La sidebar live ne colle pas aux cibles :

- numerotation 01/02/03 absente des Canva ;
- libelles differents ("Actions" au lieu d'une entree plus metier, "Demandes novice", "AG contentieux novice", "Depot local") ;
- active state tres large, plus proche d'un menu d'onboarding que d'une console de gestion ;
- taxonomie incoherente avec certaines cibles, notamment Memoire ou Canva montre une navigation orientee patrimoine/pilotage ;
- sur la capture Memoire, l'etat actif parait ambigu : "AG contentieux novice" et "Memoire copropriete" ressortent tous deux fortement.

Recommandation P1 : aligner la taxonomie sidebar sur les cibles Canva par famille de route. Supprimer la numerotation visible dans la navigation principale ou la rendre beaucoup moins presente si elle est necessaire en interne.

### En-tete

Les cibles utilisent un en-tete utile et contextualise : titre, recherche, notifications/aide/profil, CTA route-specific ("Nouvelle action", "Exporter", "Ajouter un evenement"). Le live affiche une barre produit locale avec chips techniques et un CTA generique "Nouvelle demande", parfois tronque.

Recommandation P1 : restaurer les en-tetes par route. Les statuts techniques doivent etre secondaires. Les CTA doivent correspondre a l'action metier de la route.

### Zone de travail principale

Dans Canva, le contenu metier est visible au premier regard : KPI, listes, tableau, detail lateral, timeline. Dans le live, le premier ecran est souvent occupe par des cartes de contexte, un bloc "Aide rapide", une introduction ou des KPI zeros. La densite live est plus faible et moins operationnelle.

Recommandation P0 : mettre le "workspace" cible au sommet de chaque route, juste sous l'en-tete. Les blocs d'aide, contexte local et prochaines actions techniques doivent etre replies ou deplaces en panneau secondaire.

## Route 1 - Cockpit Conseil Syndical

### Fidelite structurelle

Fidelite faible. La cible montre immediatement le dashboard : salutation, date de situation, rangee "A traiter" avec 5 KPI, 4 cartes metier en grille, puis table "Alertes et risques". Le live montre d'abord une couche de contexte local et coffre, puis un bloc "Aide rapide", puis seulement le debut du cockpit.

### Ecarts principaux

| Zone | Ecart | Priorite |
| --- | --- | --- |
| Premiere impression | Le live ne ressemble pas a un cockpit, mais a une page de validation de contexte local. | P0 |
| Top content | La rangee KPI "A traiter" n'est pas le premier element visible. | P0 |
| KPI | Les 5 cartes Canva avec valeurs 12 / 18 / 7 / 2 / 5 ne sont pas restaurees dans le premier ecran live. | P1 |
| Modules | Les cartes "Pieces manquantes", "Demandes syndic", "AG", "Controle comptes" ne structurent pas le fold live. | P1 |
| Alertes | La table "Alertes et risques" de la cible est absente du premier ecran live. | P1 |
| Header | Recherche, icones notification/aide/profil et CTA de la cible sont remplaces par chips locales et CTA generique. | P1 |
| Sidebar | Labels et badges differents, numerotation trop visible, section "Parametres" coupee. | P1 |

### Realignement recommande

1. Retirer le bloc "Contexte actif / Coffre / Role / Sync" du haut de route ; le deplacer dans un tiroir "Mode local" ou dans une alerte discrete.
2. Reconstruire le fold selon Canva : titre + "Bonjour" + date, puis container "A traiter" avec 5 KPI horizontaux.
3. Placer les 4 cartes metier en grille sous les KPI, avec les memes types d'information : jauge completude, liste demandes, echeances AG, controle comptes.
4. Reintroduire la table "Alertes et risques" sur toute la largeur sous les cartes.
5. Adapter le responsive : a 999 px, soit la sidebar se compacte, soit la grille passe proprement en 2 colonnes sans masquer les contenus cibles.

## Route 2 - Registre des decisions / actions / preuves

### Fidelite structurelle

Fidelite faible a moyenne uniquement si l'on ignore le haut de page live. La cible est un workspace master-detail : colonne gauche "Toutes les AG" avec resolutions, grande zone detail a droite avec statut, responsable, echeance, tabs, preuves, pieces liees, relances et historique. Le live affiche d'abord le contexte local, puis une introduction de route et des cartes de synthese ; le master-detail cible n'est pas visible dans le fold.

### Ecarts principaux

| Zone | Ecart | Priorite |
| --- | --- | --- |
| Structure | Le layout master-detail Canva n'est pas le layout initial live. | P0 |
| Detail action | Le detail "Travaux etancheite toiture" avec tabs/preuves/pieces/relances n'est pas visible en premier. | P0 |
| Colonne gauche | La liste d'AG et resolutions n'apparait pas au fold live. | P1 |
| Header | Canva a recherche, export registre et nouvelle action ; live a recherche basse, mode prive local, aide, CTA genericise. | P1 |
| Densite | Live introduit du texte explicatif et des cartes de synthese, alors que Canva privilegie l'action selectionnee. | P1 |
| Navigation | L'entree "Actions" live est plus vague que le nom cible "Registre des decisions" et le vocabulaire "preuves". | P2 |

### Realignement recommande

1. Faire du master-detail le premier layout apres l'en-tete : gauche 30-35% pour AG/resolutions, droite 65-70% pour le detail.
2. Selectionner par defaut une resolution active avec statut visible, comme "Resolution AG 3 - Travaux etancheite toiture".
3. Restaurer les tabs metier au-dessus des cartes detail : action en cours, preuves, pieces liees, relance syndic, historique.
4. Mettre "Exporter le registre" et "Nouvelle action" dans l'en-tete, pas sous une couche locale.
5. Deplacer les cartes de synthese live en section secondaire ou les supprimer si elles ne viennent pas de l'enquete Canva.

## Route 3 - Controle des comptes

### Fidelite structurelle

Fidelite moyenne sur l'intention, faible sur la realisation. Le live reprend l'idee de KPI et de filtres, mais la cible est beaucoup plus operationnelle : KPI en haut, grande table "Depenses par categorie", panneau detail permanent a droite. Le live montre des KPI a zero ou "A calculer", un bloc "Prochain geste humain" et pas de panneau detail lateral dans le premier ecran.

### Ecarts principaux

| Zone | Ecart | Priorite |
| --- | --- | --- |
| Panneau droit | Le detail lateral "Entretien & maintenance" de Canva est absent. | P0 |
| Donnees KPI | Canva affiche 128 postes, 86%, 18, 6, 22 ; live affiche 0 / A calculer. | P1 |
| Table | La table cible avec categories, montants, rapprochement, statut et alertes est repoussee sous le fold live. | P1 |
| Hierarchie | Le bloc "Prochain geste humain" prend une place que Canva donne au tableau et au detail. | P1 |
| Header | Export rapport devrait etre dans l'en-tete horizontal comme Canva, pas seulement dans la zone de contenu. | P2 |
| Filtres | Les filtres live sont proches, mais moins alignes avec les libelles et la densite de Canva. | P2 |

### Realignement recommande

1. Construire un layout desktop en 3 zones : sidebar, workspace central, panneau detail fixe a droite.
2. Garder la rangee KPI en haut, avec les valeurs et icones de la cible.
3. Placer la table categories immediatement sous les filtres et visible au fold.
4. Afficher un detail de categorie selectionnee a droite avec tabs "Detail / Pieces / Questions au syndic", alertes, questions, rapport AG.
5. Declasser "Prochain geste humain" en aide contextuelle repliee ou en bandeau compact sous les KPI.

## Route 4 - Memoire de copropriete

### Fidelite structurelle

Fidelite faible. La cible est une timeline patrimoniale : recherche/filtres, choix 5 ans / 10 ans / tout, liste chronologique centrale, puis panneaux lateraux "Passation CS" et "A transmettre". Le live commence par une carte hero "Situation 2025", des KPI, puis une recherche ; la ligne de vie n'arrive qu'en bas du fold.

### Ecarts principaux

| Zone | Ecart | Priorite |
| --- | --- | --- |
| Structure | La timeline n'est pas le coeur immediat de l'ecran live. | P0 |
| Colonne droite | Les panneaux "Passation CS" et "A transmettre" ne sont pas visibles au premier ecran. | P0 |
| KPI | Les cartes 10 / 10 / 5/6 / 0 ne sont pas presentes dans la cible et repoussent le contenu utile. | P1 |
| Recherche/filtres | Dans Canva, recherche et filtres sont juste sous le titre ; dans live, ils arrivent apres hero + KPI. | P1 |
| Navigation | Taxonomie live differente, avec etat actif potentiellement ambigu. | P1 |
| CTA | Canva a "Exporter" et "Ajouter un evenement" en en-tete ; live les met dans une carte hero. | P2 |

### Realignement recommande

1. Supprimer ou reduire fortement la carte hero et les KPI du haut ; la timeline doit commencer dans le premier ecran.
2. Restaurer le bloc recherche + filtres + segment 5 ans / 10 ans / tout au-dessus de la timeline.
3. Remettre une colonne droite desktop avec "Passation CS" et "A transmettre".
4. Garder les actions "Exporter" et "Ajouter un evenement" dans l'en-tete de page.
5. Revoir la sidebar de cette route pour coller a la navigation patrimoine/pilotage de Canva.

## Priorisation transverse

| Priorite | Correction transverse | Routes touchees |
| --- | --- | --- |
| P0 | Enlever du premier ecran la couche locale/contexte/coffre/role/sync, ou la replier par defaut. | Cockpit, Registre, partiellement toutes |
| P0 | Restaurer le layout metier primaire de chaque cible : dashboard, master-detail, table + detail, timeline + rail droit. | 4 routes |
| P0 | Afficher les panneaux droits structurants quand ils existent dans Canva. | Registre, Controle, Memoire |
| P1 | Reprendre la largeur desktop ou adapter la sidebar au viewport live ; la sidebar ne doit pas consommer pres d'un tiers de l'ecran. | 4 routes |
| P1 | Aligner les en-tetes : titre, recherche, icones, CTA route-specific. | 4 routes |
| P1 | Remplacer les valeurs placeholder/zero par les donnees de demonstration Canva lorsque la route cible une enquete visuelle. | Cockpit, Controle, Memoire |
| P1 | Aligner la taxonomie et les libelles sidebar avec les captures cible. | 4 routes |
| P2 | Harmoniser badges, couleurs d'alerte, densite de lignes, icones et libelles courts. | 4 routes |

## Synthese actionnable

Le chantier prioritaire n'est pas le polish graphique : c'est le retour au squelette des ecrans Canva. Aujourd'hui, le live semble superposer une couche de securite/local-first au-dessus d'une refonte metier encore partielle. Pour coller a l'enquete utilisateur, chaque route doit afficher son objet principal des le premier fold :

- Cockpit : KPI et cartes de pilotage.
- Registre : liste AG/resolutions + detail action/preuves.
- Controle : table categories + panneau detail.
- Memoire : timeline + passation/documents a transmettre.

Une fois ces structures restaurees, les ajustements de palette, icones, badges et espacements pourront etre traites efficacement. Tant que le contexte local et les cartes introductives dominent le premier ecran, la fidelite Canva restera faible meme si les composants individuels sont propres.
