# Recette visuelle refonte UX - Cycle 8

Date de reference: 2026-05-21.

Perimetre: recette visuelle navigateur du produit fini, sans modification du
code applicatif. Cette recette sert a comparer les routes livrees avec les
visuels Canva et les blueprints de realignement, en acceptant des ecarts
raisonnables de donnees, de libelles et de responsive.

Routes couvertes:

- Cockpit: `/`
- Registre decisions/actions/preuves: `/actions`
- Controle des comptes: `/comptes`
- Memoire de copropriete: `/chantiers`
- Vues manquantes prioritaires:
  - actions en retard: `/actions?view=retards` ou fallback actuel
    `/actions?priority=P1`
  - pieces manquantes: `/pieces?proof=missing`
  - relance syndic: `/actions?scope=syndic&tab=relance`
  - echeances AG: `/chantiers?section=ag` tant qu'aucune route dediee n'est
    arbitree

Sources visuelles:

| Surface | Source Canva | Source de realignement |
|---|---|---|
| Cockpit | `docs/assets/etude-utilisateurs/cockpit-conseil-syndical.png` | `docs/assets/ux-realignement-2026-05-20/01_cockpit_realigne.png` |
| Registre | `docs/assets/etude-utilisateurs/registre-decisions-actions-preuves.png` | `docs/assets/ux-realignement-2026-05-20/02_registre_decisions_actions_preuves.png` |
| Comptes | `docs/assets/etude-utilisateurs/controle-comptes-guide.png` | `docs/assets/ux-realignement-2026-05-20/03_controle_comptes_guide.png` |
| Memoire | `docs/assets/etude-utilisateurs/memoire-copropriete.png` | `docs/assets/ux-realignement-2026-05-20/04_memoire_ligne_de_vie.png` |
| Vues manquantes | Pas de Canva dedie | Deriver de Cockpit + Registre + Memoire |

Les sources Canva font environ `1672x941`. Les rendus de realignement font
`1440x900`. La comparaison de reference se fait donc en `1440x900`, zoom 100%,
puis en largeur compacte et mobile.

## Definition de la recette

La recette visuelle valide une route reelle dans un navigateur. Elle ne valide
pas une intention, un template isole ou une capture Canva seule.

Pour chaque route, produire au minimum:

- une capture desktop reference en `1440x900`;
- une capture desktop compacte en `1366x768`;
- une capture mobile en `390x844`;
- une note go/no-go avec les ecarts P0/P1/P2;
- si la page scrolle, une capture du premier viewport et une capture full page.

Viewports cibles:

| Usage | Taille | Objectif |
|---|---:|---|
| Desktop reference | `1440x900` | Comparaison principale avec les rendus de realignement |
| Desktop compact | `1366x768` | Verifier le premier pli et la densite de travail |
| Tablette | `768x1024` | Verifier empilement, tiroirs et zones de detail |
| Mobile | `390x844` | Verifier parcours sans chevauchement |
| Mobile etroit optionnel | `360x800` | Traquer debordements de libelles longs |

Tolerances non pixel-perfect:

- Les dimensions exactes, ombres, icones et rayons peuvent varier si la
  hierarchie reste identique.
- Les libelles peuvent etre adaptes au vocabulaire CoproScope si le sens reste
  novice, actionnable et non technique.
- Les donnees, compteurs, dates et ordres de lignes peuvent varier selon
  l'instance, mais les blocs de travail attendus doivent exister.
- Un ecart de spacing ou de largeur de colonne est acceptable si l'ecran reste
  dense, lisible et stable.
- Le shell existant peut garder sa largeur et sa navigation, tant que l'entree
  active et la page cible sont immediatement reconnaissables.
- Une page peut scroller si le premier viewport garde le titre, l'action
  principale et au moins le debut du bloc metier.
- Sur mobile, les blocs peuvent s'empiler et les inspecteurs devenir tiroirs ou
  pages detail, mais aucune information critique ne doit disparaitre.

No-go transverses:

- route en erreur, 404/500, stacktrace, template error ou etat vide illisible;
- rupture de token sur un lien interne quand la route est protegee;
- fuite visible: `raw`, `restricted`, `logs`, `file://`, chemin Windows absolu,
  chemin `/Users/...`, chemin `/home/...`, secret ou contenu brut sensible;
- compteur ou carte non cliquable alors qu'il promet une action;
- action primaire qui ne dit pas sa consequence;
- titre principal qui contredit la cible, par exemple `Chantiers` au lieu de
  `Memoire de copropriete`;
- tableau brut comme interface primaire quand la cible demande une lecture
  guidee;
- statut porte uniquement par la couleur;
- texte coupe, bouton illisible, cartes qui se chevauchent, scroll horizontal
  global sur mobile;
- promesse d'envoi automatique de mail ou de diffusion sans confirmation;
- jargon primaire non traduit: `vault`, `hash`, `ACL`, `RBAC`, `workstreams`,
  `raw`, `pipeline`, `module` en titre ou CTA utilisateur.

## Tester sans Playwright

Si Playwright n'est pas installe ou pas disponible, la recette reste possible
par capture manuelle ou avec le Browser app.

Preparation recommandee:

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root "$env:USERPROFILE\CoproScope\instances\beauvallon_test" --year 2025 --port 8766 --token beauvallon-test-local
```

La commande affiche une URL locale tokenisee. Ouvrir cette URL, puis tester les
routes avec le meme token ou le cookie local pose par la premiere entree.

Mode Browser app:

1. Ouvrir l'URL tokenisee dans le navigateur integre.
2. Regler le viewport demande si l'outil le permet; sinon noter la largeur
   reelle dans la fiche de recette.
3. Capturer le viewport visible, puis la page complete si le contenu scrolle.
4. Ouvrir l'image Canva correspondante dans un onglet ou une visionneuse.
5. Comparer par blocs avec les checklists ci-dessous, pas au pixel.
6. Reporter chaque ecart en P0/P1/P2.

Mode manuel sans Browser app:

1. Ouvrir Chrome, Edge ou Firefox a zoom `100%`.
2. Utiliser les DevTools et le mode device toolbar pour entrer `1440x900`,
   `1366x768`, `768x1024` et `390x844`.
3. Utiliser `Ctrl+Shift+P` dans les DevTools puis `Capture screenshot`, ou
   `Win+Shift+S` si la capture navigateur n'est pas disponible.
4. Nommer les captures avec route, viewport et date, par exemple
   `cycle8-cockpit-1440x900-2026-05-21.png`.
5. Noter explicitement si la capture inclut la barre du navigateur.

Points a verifier meme sans outillage automatise:

- le premier viewport montre la bonne page et la bonne action principale;
- les liens de cartes gardent le token ou fonctionnent via cookie local;
- la navigation active correspond a la route;
- aucun contenu prive ou chemin local n'est visible;
- au clavier, les controles principaux ont un focus visible;
- sur mobile, les zones de detail ne chevauchent pas les listes.

## Cockpit `/`

Source: `cockpit-conseil-syndical.png`.

Viewport de reference: `1440x900`. Controle compact obligatoire:
`1366x768`. Mobile obligatoire: `390x844`.

Blocs a comparer:

| Bloc | Attendu visuel | Tolerance |
|---|---|---|
| Shell | Sidebar sombre, topbar compacte, canvas clair | Largeur de sidebar ajustable si navigation lisible |
| Header | `Cockpit Conseil Syndical`, contexte local, recherche ou action globale | Sous-titre et contexte peuvent varier |
| Rang `A traiter` | Environ cinq cartes priorisees, chacune avec raison et href | Nombre data-driven acceptable entre 4 et 6 si priorite claire |
| Pieces manquantes | Panneau de travail avec preuve attendue et prochain geste | Peut renvoyer vers `/pieces?proof=missing` |
| Demandes syndic | Panneau ou carte de relance/demande avec statut | Ne doit pas promettre envoi automatique |
| AG/echeances | Bloc dates, decisions ou points AG a reprendre | Peut pointer vers memoire tant que route dediee absente |
| Controle comptes | Bloc P1/P2/OK avec action vers `/comptes` | P1/P2 accompagnes de texte humain |
| Alertes/risques | Tableau ou liste basse sobre, pas dominante | Les donnees peuvent etre vides si etat vide utile |

Checklist desktop:

- le titre et le rang `A traiter` sont visibles sans scroll;
- chaque carte prioritaire a un href local ou un bouton actionnable;
- les panneaux bas ne dominent pas les cartes prioritaires;
- les compteurs ouvrent des vues filtrees coherentes;
- le cockpit ne ressemble pas a un inventaire de modules.

Checklist mobile:

- la navigation se replie ou passe sous forme compacte;
- les cartes `A traiter` apparaissent avant les panneaux secondaires;
- chaque carte tient en largeur sans texte coupe;
- les panneaux s'empilent dans un ordre de travail: urgent, preuve, relance,
  AG, comptes;
- aucun tableau ne force un scroll horizontal global.

No-go Cockpit:

- une carte critique n'ouvre rien;
- `Actions en retard`, `Pieces manquantes` ou `Demandes syndic` menent a une
  erreur ou une vue non filtree sans titre cible;
- plus de deux cartes affichent seulement un compteur sans raison ni prochaine
  action;
- le premier pli ne permet pas de comprendre quoi faire maintenant.

## Registre `/actions`

Source: `registre-decisions-actions-preuves.png`.

Viewport de reference: `1440x900`. Controle compact obligatoire:
`1366x768`. Mobile obligatoire: `390x844`.

Routes de recette:

- `/actions`
- `/actions?priority=P1`
- `/actions?status=a_demander`
- `/actions?scope=syndic`
- `/actions?selected_item_id=<id>` si une action seed existe

Blocs a comparer:

| Bloc | Attendu visuel | Tolerance |
|---|---|---|
| Shell + header | Navigation stable, titre registre, recherche, export/creation | Les actions globales peuvent etre regroupees |
| Colonne AG | Liste groupee par AG/resolutions, largeur stable | Sur desktop, elle ne doit pas disparaitre |
| Fiche decision | En-tete avec resolution, titre, statut, date, synthese | Selection par defaut ou etat vide utile accepte |
| Cartes resume | Responsable, echeance, statut, priorite | Labels data-driven acceptes |
| Onglets | `Action`, `Preuves`, `Pieces liees`, `Relance syndic`, `Historique` | Ordre proche attendu; onglet actif explicite |
| Contenu onglet | Action courante, preuves, pieces, relance ou journal | Peut etre vide si l'etat explique quoi faire |
| Historique | Timeline ou journal de preuve en bas ou panneau | Doit rester lisible et relie a l'action |

Checklist desktop:

- `/actions` rend une fiche stable sans selection manuelle prealable;
- la colonne AG et la fiche decision sont visibles ensemble;
- l'onglet actif est identifiable sans couleur seule;
- les preuves distinguent document candidat, piece utile et preuve validee;
- `Relance syndic` affiche un brouillon prudent ou un etat vide utile;
- l'historique garde date, source et effet de chaque evenement.

Checklist mobile:

- la liste AG devient section repliee, tiroir ou page de selection;
- la fiche decision reste prioritaire;
- les onglets tiennent en scroll horizontal controle ou en menu sans couper les
  libelles;
- les cartes resume s'empilent sans perdre responsable/echeance/statut;
- les CTA `Ajouter une preuve`, `Preparer une relance`, `Rattacher comme preuve`
  restent visibles.

No-go Registre:

- `/actions` ou une variante filtree retourne une erreur serveur;
- le template affiche une absence de champ au lieu d'un etat vide;
- une resolution ouverte n'a ni responsable, ni echeance, ni preuve attendue;
- l'onglet `Relance syndic` marque une relance comme envoyee sans confirmation;
- un export ou une preuve expose un chemin prive.

## Controle des comptes `/comptes`

Source: `controle-comptes-guide.png`.

Viewport de reference: `1440x900`. Controle compact obligatoire:
`1366x768`. Mobile obligatoire: `390x844`.

Routes de recette:

- `/comptes`
- `/comptes?statut=p1`
- `/comptes?statut=p2`
- `/comptes?tab=questions`
- `/comptes?tab=rapport-ag`
- `/comptes?categorie=<id>` si une categorie seed existe

Blocs a comparer:

| Bloc | Attendu visuel | Tolerance |
|---|---|---|
| Header | Titre `Controle des comptes`, exercice, export | `ComptaScope` peut exister en secondaire, pas en titre primaire |
| KPI | Cartes cliquables P1/P2/OK/pieces/questions | Compteurs variables mais hrefs obligatoires |
| Filtres | Exercice, statut, fournisseur, pieces, categories | Des filtres peuvent etre menus si la densite reste lisible |
| Bloc central | `Depenses par categorie`, table ou liste guidee | Tableau accepte s'il reste actionnable et non brut |
| Inspecteur droit | Detail categorie, alertes, pieces, questions | Peut etre drawer sur tablette/mobile |
| Rapport AG | Carte ou onglet visible avec export prudent | Export doit annoncer limites et omissions |
| Legende | P1/P2/OK expliques en langage humain | Couleur seule interdite |

Checklist desktop:

- les KPI sont visibles avant la table;
- la categorie selectionnee ouvre un inspecteur utile;
- P1 signifie `a traiter`, P2 `a confirmer`, OK `conforme avec preuve`;
- chaque anomalie P1 a une question syndic ou une preuve attendue;
- le rapport AG n'inclut que les points selectionnes ou signale les limites.

Checklist mobile:

- les KPI restent en haut;
- les categories deviennent des cartes/lignes empilees;
- l'inspecteur droit devient detail plein ecran ou tiroir;
- les boutons `Copier la question`, `Voir les pieces`, `Exporter le rapport`
  restent lisibles;
- aucune ligne comptable ne force un scroll horizontal global.

No-go Comptes:

- le premier niveau est un tableau brut de sorties comptables;
- P1/P2 sont affiches sans explication humaine;
- une question syndic est presentee comme envoyee;
- `Exporter le rapport` ne precise pas le statut prudent ou les omissions;
- une categorie P1 n'a ni action, ni preuve attendue, ni question.

## Memoire `/chantiers`

Source: `memoire-copropriete.png`.

Viewport de reference: `1440x900`. Controle compact obligatoire:
`1366x768`. Mobile obligatoire: `390x844`.

Routes de recette:

- `/chantiers`
- `/chantiers?periode=5ans`
- `/chantiers?periode=10ans`
- `/chantiers?periode=tout`
- `/chantiers?q=ascenseur` ou requete seed equivalente
- `/chantiers?selected=<event_id>` si un evenement seed existe
- `/chantiers?panel=passation`
- `/chantiers?panel=export`

Blocs a comparer:

| Bloc | Attendu visuel | Tolerance |
|---|---|---|
| Navigation active | Entree active `Memoire de copropriete` ou proche | URL `/chantiers` peut rester technique |
| Header | Titre `Memoire de copropriete`, sous-titre, `Exporter`, `Ajouter un evenement` | Creation peut etre non persistante si expliquee |
| Toolbar | Recherche, `Filtres`, segments `5 ans`, `10 ans`, `Tout` | `10 ans` ou periode courante visible |
| Timeline | Ligne de vie centrale, dates, points, categories, chevrons | Couleurs/icones variables si categorie lisible |
| Passation CS | Panneau progression, sujets ouverts, checklist | Doit etre visible sans scroll desktop standard |
| A transmettre | Documents essentiels, type, fraicheur, diffusion | Telechargement direct interdit si restreint |
| Details | Detail evenement, pack passation, export passation | Peut etre panneau, drawer ou route query |

Checklist desktop:

- le titre `Memoire de copropriete` remplace visuellement `Chantiers`;
- la timeline est le bloc central, pas une liste de modules;
- `Passation CS` et `A transmettre` sont visibles dans la colonne droite;
- chaque evenement a une categorie, une date ou `date a confirmer`, et un href;
- l'export passation mentionne qu'il est derive et non source collaborative.

Checklist mobile:

- le header reste compact;
- recherche, filtres et periode precede la timeline;
- la timeline est pleine largeur;
- les panneaux passation viennent sous la timeline ou en onglets;
- le detail evenement occupe un tiroir ou une page sans chevauchement.

No-go Memoire:

- `Chantiers` ou `Workstreams` reste le titre principal visible;
- la page ne montre pas de timeline ou de vraie passation;
- un document restreint a un bouton de telechargement direct;
- le pack passation masque les omissions ou les restrictions;
- la page confond memoire et stockage documentaire brut.

## Vues manquantes prioritaires

Ces vues n'ont pas encore de Canva dedie. La comparaison se fait contre la
grammaire des quatre visuels: shell calme, cartes actionnables, liste de travail,
detail lisible, preuve/action/memoire toujours relies.

### Actions en retard

Route cible: `/actions?view=retards`.

Fallback tolerable pour compatibilite: `/actions?priority=P1`, uniquement si le
titre visible devient `Toutes les actions en retard` ou equivalent.

Viewport de reference: `1440x900`. Mobile: `390x844`.

Blocs attendus:

- header `Toutes les actions en retard`;
- sous-titre expliquant retard, echeance ou preuve bloquante;
- cartes resume: `En retard`, `Critiques`, `Sans preuve`, `Relance syndic prete`;
- filtres priorite, domaine, responsable, retard, preuve;
- liste priorisee avec echeance, retard, responsable, preuve attendue;
- detail ou drawer avec historique court et CTA;
- liens `Preparer relance`, `Rattacher une piece`, `Voir dans la memoire`.

No-go:

- la route filtree casse;
- la vue reste un registre generique sans titre retard;
- une action en retard n'explique pas depuis quand ni quoi faire;
- aucune sortie vers relance, preuve ou memoire.

Checklist mobile:

- les cartes resume tiennent en grille ou pile compacte;
- chaque ligne affiche titre, retard et prochaine action avant les details;
- le detail s'ouvre sans masquer le retour a la liste.

### Pieces manquantes

Route cible: `/pieces?proof=missing`.

Viewport de reference: `1440x900`. Mobile: `390x844`.

Blocs attendus:

- header `Pieces manquantes`;
- sous-titre `Les pieces a obtenir, verifier ou rattacher comme preuve.`;
- indicateur de completude;
- regroupements AG, contrats, travaux, comptes/factures, sinistres,
  contentieux, passation;
- filtres criticite, rubrique, source attendue, demande syndic prete, diffusion;
- liste de pieces avec raison, preuve visee, source probable, action conseillee;
- detail distinguant piece utile, document candidat, preuve validee et
  restriction;
- CTA `Demander au syndic`, `Rattacher une piece existante`, `Ajouter depuis
  depot`, `Marquer non applicable`.

No-go:

- le filtre `proof=missing` affiche seulement l'atelier general sans titre cible;
- une piece candidate est presentee comme preuve validee sans validation;
- aucun lien ne permet de demander, rattacher ou deposer;
- un document restreint est telechargeable directement.

Checklist mobile:

- les groupes se replient ou s'empilent proprement;
- la raison du manque et l'action conseillee restent visibles dans la ligne;
- le CTA principal est accessible sans scroll horizontal.

### Relance syndic

Route cible: `/actions?scope=syndic&tab=relance`.

Route detail: `/actions?selected=<id>&tab=relance`.

Viewport de reference: `1440x900`. Mobile: `390x844`.

Blocs attendus:

- header `Relance syndic`;
- sous-titre `Brouillons, relances a envoyer et reponses a verifier.`;
- onglets `A preparer`, `Pretes a envoyer`, `Envoyees hors CoproScope`,
  `Reponses a verifier`, `Cloturees`;
- liste de demandes avec objet, preuve attendue, canal, priorite et statut;
- panneau de brouillon copiable;
- historique de relance;
- action de suivi apres envoi externe.

No-go:

- la route filtree casse;
- une relance est marquee envoyee sans confirmation utilisateur;
- le brouillon inclut une note interne ou une donnee restreinte;
- CoproScope semble envoyer un mail automatiquement;
- demande coproprietaire entrante et demande au syndic sont confondues.

Checklist mobile:

- les onglets restent lisibles ou deviennent un select/menu;
- le brouillon est copiable mais ne masque pas la preuve attendue;
- les actions disabled donnent une raison.

### Echeances AG

Route actuelle: `/chantiers?section=ag`.

Route cible a arbitrer: vue dediee sous `/actions`, `/chantiers` ou `/ag-contentieux`
si elle devient plus qu'un filtre memoire.

Viewport de reference: `1440x900`. Mobile: `390x844`.

Blocs attendus:

- header `Echeances AG` ou `Decisions AG a reprendre`;
- liste des decisions/echeances avec date, preuve attendue, statut et prochain
  geste;
- lien vers la fiche registre;
- lien vers la memoire/passation;
- etat vide qui explique quoi importer ou verifier.

No-go:

- `section=ag` ne change rien visuellement;
- les echeances AG sont cachees dans une timeline sans action;
- les boutons pointent vers une route `/actions` fragile;
- aucune preuve attendue n'est indiquee.

Checklist mobile:

- les dates et statuts restent visibles dans chaque ligne;
- le lien vers registre ou memoire ne sort pas du viewport;
- la chronologie ne remplace pas la liste de travail.

## Matrice go/no-go visuelle

Decision par route:

| Route | GO visuel | GO avec reserves | NO-GO visuel |
|---|---|---|---|
| `/` | Les 5 priorites, panneaux et liens cibles sont lisibles desktop/mobile | Un bloc secondaire est bas dans la page mais actionnable | Une carte critique n'ouvre rien ou le premier pli ne dit pas quoi faire |
| `/actions` | Registre AG + fiche decision + onglets + preuves/relance/historique stables | Une variante filtree a un etat vide perfectible mais route 200 | Route simple ou filtree en erreur, selection absente non geree |
| `/comptes` | KPI + categories + inspecteur + questions syndic + rapport AG visibles | Inspecteur en dessous sur desktop compact mais coherent | Tableau brut, P1/P2 non expliques, aucune question/action |
| `/chantiers` | Memoire titree, timeline centrale, passation et transmission visibles | Detail/pack/export en panneau simple mais comprehensible | Titre `Chantiers`, pas de timeline, restrictions masquees |
| `/actions?view=retards` | Liste de travail retard avec preuve, responsable, action et detail | Fallback `/actions?priority=P1` acceptable avec titre cible | Route casse ou vue generique sans retard/action |
| `/pieces?proof=missing` | Vue filtree avec raison, preuve visee, source et CTA | Etat vide solide mais pas encore donnees seed | Atelier general non filtre ou aucune action possible |
| `/actions?scope=syndic&tab=relance` | Relances, brouillons, statut et suivi externe clairs | Onglets incomplets mais brouillon prudent disponible | Route casse, envoi implicite, statut envoye non confirme |
| `/chantiers?section=ag` | Echeances AG visibles avec preuve et retour registre/memoire | Simple filtre memoire mais titre AG clair | Parametre sans effet visible ou liens cassants |

Decision produit:

| Niveau | Conditions | Decision |
|---|---|---|
| GO produit fini visuel | Toutes les routes primaires sont GO desktop et mobile; vues manquantes P0/P1 fermees; aucune fuite, aucun lien critique casse | Acceptation visuelle |
| GO demo encadree | Cockpit, Registre, Comptes, Memoire sont GO desktop; mobile a seulement des P2; vues manquantes documentees | Demo possible avec avertissement |
| NO-GO utilisateur novice | Une route primaire casse, une carte cockpit critique casse, mobile chevauche, ou preuve/action/memoire disparait | Retour dev/design avant test novice |
| NO-GO securite visuelle | Fuite privee, token perdu, document restreint telechargeable, export ambigu | Blocage immediat |

Severite des ecarts:

| Severite | Definition | Exemple |
|---|---|---|
| P0 | Bloque la recette ou expose un risque de securite/confidentialite | 500, chemin prive, token perdu, relance marquee envoyee |
| P1 | Bloque le parcours novice ou la promesse preuve/action/memoire | carte sans href, timeline absente, P1 sans action |
| P2 | Defaut visuel ou langage corrigeable apres GO encadre | spacing irregulier, icone differente, libelle long |

## Fiche de recette a remplir

Pour chaque capture, renseigner:

```text
Route:
URL complete:
Viewport:
Source comparee:
Date/heure:
Navigateur:
Token present: oui/non/cookie
Verdict: GO / GO reserves / NO-GO
Ecarts P0:
Ecarts P1:
Ecarts P2:
Decision mobile:
Decision desktop:
Commentaire novice:
```

## Prochain lot design/QA visuel propose

Lot 9 recommande: recette navigateur reelle avec captures annotees et arbitrage
des vues manquantes.

Objectifs:

1. Produire les captures `1440x900`, `1366x768` et `390x844` pour les quatre
   routes primaires.
2. Annoter les ecarts par blocs face aux quatre Canva.
3. Fermer ou confirmer les P0/P1 des vues `Actions en retard` et `Relance
   syndic`, car elles bloquent le depart depuis le cockpit.
4. Designer un blueprint dedie pour `Pieces manquantes`, `Relance syndic` et
   `Echeances AG`, afin de ne plus les deriver seulement des vues parentes.
5. Rejouer une recette novice courte: "je pars du cockpit, je trouve quoi faire,
   avec quelle preuve, puis je sais si je peux transmettre".
