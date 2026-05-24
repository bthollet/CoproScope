# Commande Cycle 4 - Memoire de copropriete

Mission: transformer la route existante `/chantiers` en surface visuelle
`Memoire de copropriete`, alignee sur l'image d'enquete
`docs/assets/etude-utilisateurs/memoire-copropriete.png`.

Le nom technique de route peut rester `/chantiers` pour compatibilite, mais
l'utilisateur ne doit plus avoir l'impression d'ouvrir un tableau de "chantiers".
La page doit raconter l'histoire utile de l'immeuble, montrer ce qui reste ouvert
et preparer une passation de conseil syndical sans fuite de documents sensibles.

## Intention utilisateur confirmee

Un membre du conseil syndical, nouveau ou fatigue, doit pouvoir repondre en moins
de deux minutes:

- quels sont les evenements importants des 5, 10 dernieres annees ou de toute la
  vie disponible de la copropriete;
- quels sujets restent ouverts et qui doit les reprendre;
- quels documents/preuves sont disponibles pour comprendre la situation;
- quels elements sont transmissibles, restreints ou a arbitrer;
- comment exporter une synthese de passation qui n'est pas une source de verite.

La promesse produit reste: preuve + action + memoire.

## Perimetre dev

Route cible:

- `GET /chantiers`

Libelle visuel obligatoire:

- `Memoire de copropriete`

Libelles a eviter dans l'UI visible de cette route:

- `Chantiers`
- `Workstreams`
- `modules a lancer`

Exceptions acceptees:

- noms internes, tests, commentaires ou compatibilite de route;
- URLs existantes tant que les liens restent token-safe.

La route `/chantiers` devient donc une URL historique qui sert la page
`Memoire de copropriete`.

## Enquete sur image

### Layout global

La source visuelle montre une application dense et calme:

- barre laterale sombre fixe a gauche;
- entete de page blanc, titre fort, sous-titre court;
- actions globales en haut a droite;
- barre de recherche/filtres sous l'entete;
- grande timeline centrale;
- colonne droite composee de panneaux de passation;
- pas de page marketing, pas de hero, pas de carte decorative inutile.

La page doit etre lisible en mode travail repete. Elle ne doit pas donner
l'impression d'un rapport statique.

### Navigation laterale

La navigation de l'image est organisee ainsi:

- marque produit: `Cockpit Conseil Syndical`;
- bloc principal:
  - `Tableau de bord`;
  - `Documents`;
  - `Communications`;
  - `Taches` avec badge `8`;
- section `PATRIMOINE`:
  - `Immeuble`;
  - `Lots & coproprietaires`;
  - `Fournisseurs & contrats`;
- section `PILOTAGE`:
  - `Comptabilite`;
  - `Budgets`;
  - `Travaux`;
  - `Sinistres`;
  - `AG`;
  - `Memoire de copropriete` actif;
- section `PARAMETRES`:
  - `Reglages`;
- bouton bas: `Aide & ressources`.

Adaptation CoproScope:

- conserver le shell existant si necessaire;
- renommer l'entree active de `/chantiers` en `Memoire copropriete` ou
  `Memoire de copropriete`;
- l'etat actif doit etre visible dans la navigation;
- le lien doit rester `token_href('/chantiers')`;
- l'aria-label ne doit plus parler de "chantiers en cours" mais de memoire et
  passation.

### Haut de page

Elements visibles dans l'image:

- titre: `Memoire de copropriete`;
- sous-titre: `L'historique de votre immeuble, centralise et consultable dans le temps.`;
- bouton secondaire `Exporter` avec icone telechargement;
- bouton primaire split `Ajouter un evenement`;
- bouton adjacent chevron bas pour ouvrir les variantes d'ajout.

Adaptation CoproScope:

- titre exact: `Memoire de copropriete`;
- sous-titre conseille:
  `L'historique utile de l'immeuble, les sujets ouverts et les preuves a transmettre.`;
- le bouton `Exporter` ouvre un choix d'exports derives:
  - `Passation JSON`;
  - `Passation texte`;
  - `Apercu de passation`;
- le bouton `Ajouter un evenement` ouvre un drawer/modal local;
- le chevron propose des raccourcis d'ajout:
  - `Ajouter un evenement`;
  - `Rattacher un document`;
  - `Noter un sujet ouvert`;
  - `Noter un changement de syndic`;
  - `Importer depuis les registres`.

Le bouton principal ne doit pas ecrire directement un fichier brut sans
validation. Il declenche une saisie ou une projection derivee.

### Barre recherche et filtres

Elements visibles dans l'image:

- champ de recherche pleine largeur:
  `Rechercher un evenement, un contrat, un document...`;
- bouton `Filtres` avec icone entonnoir;
- controle segmente:
  - `5 ans`;
  - `10 ans` actif;
  - `Tout`.

Adaptation CoproScope:

- placeholder exact ou tres proche:
  `Rechercher un evenement, un contrat, un document...`;
- recherche sur:
  - titre evenement;
  - description;
  - categorie;
  - document rattache;
  - fournisseur/contrat;
  - AG/resolution;
  - action ou demande syndic;
- filtres attendus:
  - categorie: `AG`, `Travaux`, `Sinistres`, `Contrats`, `Documents`,
    `Syndic`, `Comptes`, `Demandes`, `Contentieux`;
  - statut: `ouvert`, `clos`, `a confirmer`, `restreint`;
  - diffusion: `transmissible`, `apres biffage`, `conseil syndical`,
    `confidentiel`;
  - periode: 5 ans, 10 ans, tout;
  - preuve: avec preuve, preuve manquante, preuve restreinte;
- etat URL recommande:
  `/chantiers?q=<texte>&periode=10ans&categorie=travaux&statut=ouvert`;
- tous les liens generes conservent le token UI existant quand requis.

### Timeline centrale

La timeline image est une carte large avec:

- colonne date a gauche;
- ligne verticale grise;
- point couleur par evenement;
- ligne evenement avec icone carree douce;
- titre;
- sous-titre;
- badge categorie a droite;
- chevron d'ouverture;
- separateur horizontal discret;
- pied `Charger plus d'evenements`.

Evenements visibles dans l'image:

| Date | Point | Icone | Titre | Sous-titre | Badge |
| --- | --- | --- | --- | --- | --- |
| 15 mai 2025 | vert | document/contrat | Contrat d'entretien ascenseur | Nouveau contrat signe avec le prestataire. | Contrats |
| 28 avril 2025 | bleu | outils | Refection de l'etancheite toiture-terrasse | Travaux votes en AG du 10/04/2025 - Debut des travaux. | Travaux |
| 03 mars 2025 | orange | alerte | Degat des eaux - Cage B | Sinistre declare aupres de l'assurance de l'immeuble. | Sinistres |
| 10 fevrier 2025 | vert | groupe | Assemblee Generale Ordinaire 2024 | Approbation des comptes, budget previsionnel et travaux. | AG |
| 12 novembre 2024 | bleu | immeuble | Changement de syndic | Nouveau syndic designe en remplacement du precedent. | Syndic |
| 30 septembre 2024 | gris | dossier | Mise a jour du Dossier Technique | Documents techniques mis a jour et archives. | Documents |
| 18 juillet 2024 | vert | groupe | Assemblee Generale Extraordinaire | Vote pour la renovation du hall d'entree et du visiophone. | AG |
| 05 juin 2024 | bleu | outils | Renovation du hall d'entree | Fin des travaux et reception. | Travaux |

Adaptation CoproScope:

- la timeline doit etre l'element central, pas un tableau de synthese;
- afficher au moins les evenements disponibles, limites par defaut a 10 ou 12;
- ordonner du plus recent au plus ancien;
- les dates doivent etre comprehensibles en francais;
- les dots couleur doivent correspondre a la categorie ou gravite;
- chaque ligne est cliquable et ouvre le detail evenement;
- `Charger plus d'evenements` ajoute la page suivante ou bascule vers une
  periode plus large;
- les evenements sans date precise sont regroupes en bas dans `Date a confirmer`
  avec un style moins prioritaire.

### Panneau droit - Passation CS

Premier panneau de l'image:

- titre: `Passation CS`;
- pictogramme groupe;
- texte:
  `Preparez la transmission des informations aux nouveaux membres du conseil syndical.`;
- compteur: `6 / 9 elements completes`;
- barre de progression verte;
- bloc `Sujets ouverts` avec badge `3`;
- checklist:
  - coche verte `Contrats en cours a suivre`;
  - coche verte `Travaux en cours ou a venir`;
  - case vide `Litiges et sinistres en cours` avec alerte rouge;
  - coche verte `Points de vigilance financiere`;
  - case vide `Demandes en attente au syndic` avec alerte rouge;
  - coche verte `Documents cles a transmettre`;
- lien bas: `Voir le detail de la passation` avec chevron.

Adaptation CoproScope:

- le panneau doit etre visible sans scroll sur desktop standard;
- la progression est derivee des donnees, pas uniquement declarative;
- les cases cochees peuvent etre des statuts derives;
- les cases non cochees ouvrent une action corrective ou un detail;
- les alertes rouges signalent un blocage de passation;
- `Voir le detail de la passation` ouvre la vue detail/panel `Pack passation`.

### Panneau droit - A transmettre

Second panneau de l'image:

- titre: `A transmettre`;
- badge `7`;
- liste de documents avec icone type fichier;
- documents visibles:
  - `Reglement de copropriete`, `PDF - Mis a jour le 12/03/2024`;
  - `Dernier PV d'AG`, `PDF - Mis a jour le 15/05/2025`;
  - `Budget previsionnel 2025`, `XLSX - Mis a jour le 10/02/2025`;
  - `Contrat entretien ascenseur`, `PDF - Mis a jour le 15/05/2025`;
- icone telechargement a droite de chaque ligne;
- lien bas: `Voir tous les documents` avec chevron.

Adaptation CoproScope:

- les documents proviennent d'une selection derivee "essentiels passation";
- afficher le type, la fraicheur et l'etat de diffusion;
- un document restreint ne doit pas avoir de bouton telechargement direct;
- le clic telechargement passe par les routes d'export ou de document autorisees;
- `Voir tous les documents` pointe vers une vue filtree documents/passation ou
  vers un panneau dedie dans `/chantiers`.

### Bouton par bouton

`Exporter`

- ouvre un menu ou drawer d'export;
- propose au minimum JSON et TXT passation derives;
- doit utiliser les routes existantes:
  - `/exports/passation.json`;
  - `/exports/passation.txt`;
- affiche la mention:
  `export derive, non source collaborative`;
- bloque ou degrade l'export si un document sensible n'est pas arbitre;
- ne doit pas servir de fichier brut, dossier `raw`, `restricted`, `logs`,
  chemin absolu local ou donnees privees.

`Ajouter un evenement`

- ouvre un formulaire avec type, date, titre, resume, categorie, documents
  rattaches, statut passation et niveau de diffusion;
- le formulaire peut etre non persistant au premier cycle si le backend n'a pas
  encore de registre d'evenements editable, mais l'UI doit l'indiquer clairement;
- si la creation est disponible, l'evenement cree doit devenir une entree
  metier testable, pas une note libre perdue.

Chevron du bouton ajouter

- ouvre les variantes d'ajout;
- les choix doivent etre explicites et courts;
- chaque choix mene a un formulaire prefiltre ou a une route existante.

Recherche

- filtre la timeline et la liste `A transmettre`;
- garde un etat vide `Aucun resultat` avec option `Effacer la recherche`;
- n'efface pas le filtre de periode sans action de l'utilisateur.

`Filtres`

- ouvre un panneau de filtres;
- indique le nombre de filtres actifs;
- propose `Reinitialiser`;
- garde les choix dans l'URL.

Segments `5 ans`, `10 ans`, `Tout`

- changent la periode de timeline;
- `10 ans` est l'etat par defaut si aucune preference n'existe;
- `Tout` peut paginer si la memoire est longue.

Chevron de ligne timeline

- ouvre le detail evenement memoire;
- conserve la position de scroll si possible;
- ne remplace pas silencieusement la timeline par une page vide.

`Charger plus d'evenements`

- charge les evenements suivants;
- disparait ou se desactive quand tout est charge;
- garde un libelle clair en etat chargement:
  `Chargement des evenements...`.

Cases du panneau `Passation CS`

- coche verte: statut complet, clic vers les sources;
- case vide: sujet incomplet, clic vers le detail et l'action attendue;
- alerte rouge: blocage ou vigilance qui empeche une passation propre.

`Voir le detail de la passation`

- ouvre la vue `Pack passation`;
- met en avant sujets ouverts, omissions, restrictions et prochaines actions.

Telechargement document `A transmettre`

- autorise uniquement si la diffusion est validee;
- sinon ouvrir l'arbitrage confidentialite ou afficher la raison du blocage;
- tous les liens doivent rester token-safe.

`Voir tous les documents`

- ouvre la liste complete des documents transmissibles;
- conserve le contexte passation.

## Structure visuelle attendue pour `/chantiers`

La route `/chantiers` doit afficher:

1. Shell/navigateur avec entree active `Memoire de copropriete`.
2. Entete:
   - titre;
   - sous-titre;
   - bouton `Exporter`;
   - bouton split `Ajouter un evenement`.
3. Barre outils:
   - recherche;
   - filtres;
   - periode 5 ans / 10 ans / tout.
4. Corps en deux zones:
   - timeline centrale majoritaire;
   - colonne droite passation.
5. Vues secondaires:
   - detail evenement;
   - pack passation;
   - export passation.

Sur desktop, viser une repartition proche:

- sidebar: largeur existante du shell;
- timeline: 65 a 70% de la zone utile;
- colonne droite: 30 a 35%;
- pas de carte imbriquee dans une autre carte.

Sur mobile:

- entete compact;
- boutons en ligne ou menu;
- recherche puis filtres;
- timeline pleine largeur;
- panneau passation sous la timeline ou en onglets;
- detail evenement en route ou drawer plein ecran.

## Composants

### `MemoireHeader`

Props attendues:

- `title`;
- `subtitle`;
- `exportAction`;
- `addEventAction`;
- `addEventMenuItems`;
- `summaryLabel` optionnel.

Responsabilites:

- poser le vocabulaire de la page;
- exposer les actions globales;
- rester stable si aucune donnee n'est chargee.

### `MemoireToolbar`

Props attendues:

- `search`;
- `filters`;
- `activeFiltersCount`;
- `periodOptions`;
- `activePeriod`;
- `resultCount`;

Responsabilites:

- recherche;
- panneau filtres;
- periode;
- etats de recherche vides.

### `MemoireTimeline`

Props attendues:

- `events`;
- `selectedEventId`;
- `loadMore`;
- `hasMore`;
- `emptyState`;

Responsabilites:

- rendu ligne de vie;
- groupement par date;
- selection;
- chargement progressif;
- accessibilite clavier.

### `MemoireEventRow`

Props attendues:

- `dateLabel`;
- `dotTone`;
- `icon`;
- `title`;
- `subtitle`;
- `categoryLabel`;
- `categoryTone`;
- `href`;
- `statusLabel`;
- `restrictionLabel`;

Responsabilites:

- ressembler aux lignes de l'image;
- donner un signal visuel categorie;
- ouvrir le detail au clic ou clavier.

### `PassationPanel`

Props attendues:

- `completedCount`;
- `totalCount`;
- `progressPct`;
- `checklist`;
- `openTopicsCount`;
- `detailHref`;

Responsabilites:

- rendre l'etat de passation lisible;
- distinguer complet, ouvert, bloquant;
- orienter vers le detail passation.

### `TransmitPanel`

Props attendues:

- `documents`;
- `totalCount`;
- `allHref`;

Responsabilites:

- afficher les documents cles;
- montrer type et date de mise a jour;
- proteger les telechargements;
- orienter vers la liste complete.

### `MemoireEventDetail`

Vue manquante a ajouter.

Contenu attendu:

- titre evenement;
- date et categorie;
- resume actionnable;
- raison de presence dans la memoire;
- documents/preuves rattaches;
- actions ou demandes liees;
- decisions AG/resolutions liees;
- notes de passation;
- restrictions de diffusion;
- historique des modifications ou signatures;
- boutons:
  - `Ouvrir les documents`;
  - `Voir l'action liee`;
  - `Ajouter une note de passation`;
  - `Exporter cette fiche` si autorise.

Route recommandee:

- `GET /chantiers?selected=<event_id>`

Alternative acceptable:

- `GET /chantiers/evenements/<event_id>`

Le choix doit rester coherent avec les autres cycles. Si une route dediee est
ajoutee, les liens depuis la timeline et les tests doivent la couvrir.

### `PassationPackDetail`

Vue manquante a ajouter.

Contenu attendu:

- titre `Pack passation`;
- perimetre de passation;
- statut de generation;
- progression checklist;
- sujets ouverts;
- documents inclus;
- documents omis avec raison;
- restrictions de diffusion;
- prochaines actions;
- horodatage et auteur/provenance derivee si disponible;
- liens vers exports JSON/TXT.

Route recommandee:

- `GET /chantiers?panel=passation`

Le pack n'est pas une source de verite. Il est reconstruit depuis les objets
metier et exports derives.

### `PassationExportPanel`

Vue manquante a ajouter.

Contenu attendu:

- titre `Exporter la passation`;
- rappel `export derive, non source collaborative`;
- formats disponibles:
  - JSON;
  - texte;
  - apercu lisible;
- statut de securite:
  - export pret;
  - export bloque;
  - export partiel avec omissions;
- omissions;
- liens:
  - `/exports/passation.json`;
  - `/exports/passation.txt`;
- message de refus si l'export contient des marqueurs interdits.

Route recommandee:

- `GET /chantiers?panel=export`

Les routes d'export existantes restent la source de telechargement. Le panneau
explique ce qui va sortir et pourquoi certains elements sont exclus.

## Contrat donnees `model.ux.memoire`

Le dev back/viewmodel doit stabiliser `model.ux.memoire` sans casser les champs
existants utilises ailleurs. La route `/chantiers` doit consommer ce bloc plutot
que recomposer directement des donnees heterogenes dans le template.

Structure cible:

```python
model.ux.memoire = {
    "context": {...},
    "summary": {...},
    "toolbar": {...},
    "filters": {...},
    "timeline": [...],
    "selected_event": {...},
    "passation": {...},
    "transmit": {...},
    "pack": {...},
    "export": {...},
    "empty_states": {...},
}
```

### `context`

```python
{
    "route": "/chantiers",
    "visual_name": "Memoire de copropriete",
    "title": "Memoire de copropriete",
    "subtitle": "L'historique utile de l'immeuble, les sujets ouverts et les preuves a transmettre.",
    "active_nav_label": "Memoire copropriete",
    "coffre": "Copropriete",
    "role": "Conseil syndical",
    "exercise": 2025,
    "as_of_label": "Situation 2025",
    "default_period": "10ans",
}
```

Contraintes:

- aucune donnee personnelle brute dans `context`;
- titre et label coherents avec la navigation;
- route stable `/chantiers`.

### `summary`

```python
{
    "event_count": 42,
    "visible_event_count": 10,
    "open_topics_count": 3,
    "handover_completed_count": 6,
    "handover_total_count": 9,
    "handover_progress_pct": 67,
    "transmit_count": 7,
    "restricted_count": 2,
    "missing_proof_count": 4,
    "last_event_label": "15 mai 2025",
}
```

Contraintes:

- les compteurs doivent etre numeriques;
- `handover_progress_pct` est derive de completed/total;
- `restricted_count` sert a avertir avant export.

### `toolbar`

```python
{
    "search_placeholder": "Rechercher un evenement, un contrat, un document...",
    "query": "",
    "active_period": "10ans",
    "period_options": [
        {"id": "5ans", "label": "5 ans", "href": "/chantiers?periode=5ans"},
        {"id": "10ans", "label": "10 ans", "href": "/chantiers?periode=10ans"},
        {"id": "tout", "label": "Tout", "href": "/chantiers?periode=tout"},
    ],
    "active_filters_count": 0,
}
```

### `filters`

```python
{
    "categories": [
        {"id": "ag", "label": "AG", "count": 4, "is_active": False},
        {"id": "travaux", "label": "Travaux", "count": 6, "is_active": False},
        {"id": "sinistres", "label": "Sinistres", "count": 2, "is_active": False},
    ],
    "statuses": [
        {"id": "ouvert", "label": "Ouvert", "count": 3, "is_active": False},
        {"id": "clos", "label": "Clos", "count": 12, "is_active": False},
    ],
    "diffusion": [
        {"id": "transmissible", "label": "Transmissible", "count": 7, "is_active": False},
        {"id": "restreint", "label": "Restreint", "count": 2, "is_active": False},
    ],
    "reset_href": "/chantiers",
}
```

### `timeline`

```python
[
    {
        "id": "evt-contrat-ascenseur-2025-05-15",
        "date_iso": "2025-05-15",
        "date_label": "15 mai 2025",
        "year": 2025,
        "dot_tone": "green",
        "icon": "file-check",
        "title": "Contrat d'entretien ascenseur",
        "subtitle": "Nouveau contrat signe avec le prestataire.",
        "kind": "contract",
        "category_label": "Contrats",
        "category_tone": "green",
        "status": "clos",
        "is_open_topic": False,
        "risk_level": "low",
        "restriction_level": "coproprietaires",
        "href": "/chantiers?selected=evt-contrat-ascenseur-2025-05-15",
        "detail_href": "/chantiers?selected=evt-contrat-ascenseur-2025-05-15",
        "document_refs": ["doc-contrat-ascenseur"],
        "action_refs": [],
        "decision_refs": [],
        "can_export": True,
    }
]
```

Categories et tons recommandes:

- `ag`: vert, icone groupe/calendrier;
- `travaux`: bleu, icone outils;
- `sinistres`: orange/rouge, icone alerte;
- `contrats`: vert, icone document signe;
- `syndic`: bleu, icone immeuble/personne morale;
- `documents`: gris, icone dossier;
- `comptes`: violet sobre ou bleu fonce, icone graphique;
- `demandes`: bleu, icone message;
- `contentieux`: rouge, icone balance/alerte.

Contraintes:

- `id` stable et testable;
- `href` token-safe via helper existant;
- pas de chemin local brut dans `document_refs`;
- pas de contenu confidentiel dans `subtitle`.

### `selected_event`

```python
{
    "id": "evt-degat-eaux-cage-b-2025-03-03",
    "title": "Degat des eaux - Cage B",
    "date_label": "03 mars 2025",
    "category_label": "Sinistres",
    "status_label": "En cours",
    "summary": "Sinistre declare aupres de l'assurance de l'immeuble.",
    "why_in_memory": "Sujet a reprendre tant que la preuve de cloture manque.",
    "next_action": "Obtenir le bon d'intervention et la confirmation assurance.",
    "owner_label": "Conseil syndical / syndic",
    "proofs": [
        {
            "id": "proof-sinistre-cage-b",
            "label": "Declaration assurance",
            "status": "a verifier",
            "href": "/documents?doc=proof-sinistre-cage-b",
            "diffusion_label": "Conseil syndical",
        }
    ],
    "linked_actions": [
        {"id": "action-sinistre-cage-b", "label": "Relancer le syndic", "href": "/actions?selected=action-sinistre-cage-b"}
    ],
    "linked_documents": [],
    "linked_decisions": [],
    "linked_requests": [],
    "passation_note": "Ne pas clore sans preuve photo et accord assurance.",
    "restriction": {
        "level": "conseil_syndical",
        "label": "Diffusion limitee",
        "reason": "Sinistre nominatif ou sensible possible.",
        "review_href": "/confidentialite"
    },
    "history": [
        {"date_label": "03 mars 2025", "label": "Signalement enregistre"}
    ],
    "actions": {
        "primary": {"label": "Ouvrir les documents", "href": "/documents?scope=sinistres"},
        "secondary": {"label": "Voir l'action liee", "href": "/actions?selected=action-sinistre-cage-b"},
        "export": {"label": "Exporter cette fiche", "href": "/exports/passation.txt", "disabled": True, "disabled_reason": "Diffusion a arbitrer"}
    }
}
```

Contraintes:

- si aucun evenement n'est selectionne, `selected_event` vaut `{}` ou `None`
  et le template n'affiche pas de detail fantome;
- si l'id est inconnu, afficher l'etat vide `event_not_found`.

### `passation`

```python
{
    "title": "Passation CS",
    "description": "Preparez la transmission des informations aux nouveaux membres du conseil syndical.",
    "completed_count": 6,
    "total_count": 9,
    "progress_pct": 67,
    "open_topics_count": 3,
    "detail_href": "/chantiers?panel=passation",
    "checklist": [
        {
            "id": "contrats",
            "label": "Contrats en cours a suivre",
            "is_done": True,
            "needs_attention": False,
            "count": 1,
            "href": "/chantiers?categorie=contrats"
        },
        {
            "id": "sinistres",
            "label": "Litiges et sinistres en cours",
            "is_done": False,
            "needs_attention": True,
            "alert_label": "A traiter",
            "count": 1,
            "href": "/chantiers?categorie=sinistres&statut=ouvert"
        }
    ],
    "open_topics": [
        {
            "id": "topic-sinistre-cage-b",
            "label": "Litiges et sinistres en cours",
            "title": "Degat des eaux - Cage B",
            "next_step": "Obtenir la preuve de cloture.",
            "severity": "P1",
            "href": "/chantiers?selected=evt-degat-eaux-cage-b-2025-03-03"
        }
    ]
}
```

Checklist minimale:

- `Contrats en cours a suivre`;
- `Travaux en cours ou a venir`;
- `Litiges et sinistres en cours`;
- `Points de vigilance financiere`;
- `Demandes en attente au syndic`;
- `Documents cles a transmettre`.

### `transmit`

```python
{
    "title": "A transmettre",
    "count": 7,
    "all_href": "/chantiers?panel=documents",
    "items": [
        {
            "id": "doc-reglement-copropriete",
            "title": "Reglement de copropriete",
            "file_type": "PDF",
            "updated_label": "Mis a jour le 12/03/2024",
            "icon": "file-pdf",
            "href": "/documents?doc=doc-reglement-copropriete",
            "download_href": "/documents?doc=doc-reglement-copropriete&download=1",
            "diffusion_label": "Coproprietaires",
            "restriction_label": "",
            "can_download": True,
        }
    ]
}
```

Contraintes:

- `download_href` vide ou disabled si document restreint;
- afficher la raison si non telechargeable;
- limiter la liste visible a 4 ou 5 items comme l'image;
- `count` correspond au total, pas seulement aux items visibles.

### `pack`

```python
{
    "id": "passation-2025",
    "title": "Pack passation",
    "scope": "Memoire de copropriete, sujets ouverts, preuves essentielles et restrictions",
    "status": "partiel",
    "status_label": "Pret avec omissions",
    "generated_at_label": "Genere depuis les donnees locales",
    "source_of_truth": False,
    "watermark": "export derive, non source collaborative",
    "included_sections": [
        "Sujets ouverts",
        "Timeline",
        "Documents cles",
        "Restrictions",
        "Prochaines actions"
    ],
    "omissions": [
        {
            "id": "omission-contentieux",
            "label": "Piece contentieux exclue",
            "reason": "Diffusion restreinte"
        }
    ],
    "latest_export": {
        "json_href": "/exports/passation.json",
        "text_href": "/exports/passation.txt",
        "preview_href": "/chantiers?panel=export"
    },
    "safety": {
        "has_private_path": False,
        "has_raw_payload": False,
        "blocked_reason": ""
    }
}
```

Contraintes:

- `source_of_truth` toujours `False`;
- watermark obligatoire;
- ne pas stocker le pack comme registre source;
- le pack se reconstruit depuis les objets metier et projections;
- toute omission doit etre visible.

### `export`

```python
{
    "title": "Exporter la passation",
    "watermark": "export derive, non source collaborative",
    "source_of_truth": False,
    "json_href": "/exports/passation.json",
    "text_href": "/exports/passation.txt",
    "preview_href": "/chantiers?panel=export",
    "status": "ready",
    "disabled": False,
    "disabled_reason": "",
    "formats": [
        {"id": "json", "label": "JSON", "href": "/exports/passation.json"},
        {"id": "txt", "label": "Texte", "href": "/exports/passation.txt"}
    ],
    "omissions": []
}
```

Statuts possibles:

- `ready`;
- `partial`;
- `blocked`;
- `empty`.

### `empty_states`

```python
{
    "timeline_empty": {
        "title": "Aucun evenement dans la memoire",
        "detail": "Ajoutez une piece, une decision ou un sujet ouvert pour construire la ligne de vie.",
        "primary_action": {"label": "Ajouter un evenement", "href": "/chantiers?add=event"},
        "secondary_action": {"label": "Ajouter une piece", "href": "/depot"}
    },
    "search_empty": {
        "title": "Aucun resultat",
        "detail": "Essayez une autre periode ou retirez un filtre.",
        "reset_href": "/chantiers"
    },
    "passation_empty": {
        "title": "Passation a preparer",
        "detail": "Aucun sujet ouvert n'est encore identifie."
    },
    "transmit_empty": {
        "title": "Aucun document transmissible",
        "detail": "Les documents cles apparaitront apres rattachement et arbitrage de diffusion."
    },
    "event_not_found": {
        "title": "Evenement introuvable",
        "detail": "La selection ne correspond plus a un evenement disponible.",
        "href": "/chantiers"
    },
    "export_blocked": {
        "title": "Export bloque",
        "detail": "Des restrictions de diffusion doivent etre arbitrees avant export."
    }
}
```

## Sources de donnees attendues

La projection `model.ux.memoire` peut agreger:

- registres decisions/actions/preuves;
- AG et resolutions;
- incidents/sinistres ouverts;
- contrats/fournisseurs;
- travaux;
- demandes syndic;
- documents cles et atelier pieces;
- revue confidentialite;
- evenements vault ou timelineops;
- exports passation derives existants.

Priorite d'integration:

1. Deriver une timeline stable depuis les objets existants.
2. Relier chaque evenement a ses preuves/actions quand elles existent.
3. Construire passation et documents a transmettre.
4. Ajouter detail evenement.
5. Ajouter panneaux pack/export.
6. Brancher la creation d'evenement seulement si une source metier stable existe.

## Interactions attendues

### Arrivee sur `/chantiers`

- La page affiche le titre `Memoire de copropriete`.
- La periode `10 ans` est selectionnee par defaut.
- Les evenements les plus recents sont visibles.
- Le panneau `Passation CS` affiche une progression.
- Le panneau `A transmettre` affiche les documents essentiels ou son etat vide.

### Recherche

- Taper dans le champ filtre la timeline.
- Le nombre de resultats visibles est mis a jour.
- Si aucun resultat, afficher `Aucun resultat` et `Effacer la recherche`.
- La recherche ne doit pas casser les liens de passation.

### Filtres

- `Filtres` ouvre un panneau accessible.
- Cocher une categorie met a jour la timeline et l'URL.
- `Reinitialiser` revient a `/chantiers`.
- Les filtres actifs sont visibles.

### Periode

- `5 ans` limite aux evenements recents.
- `10 ans` est actif par defaut.
- `Tout` affiche toute la memoire disponible avec pagination si necessaire.

### Detail evenement

- Clic sur une ligne ou chevron ouvre le detail.
- Le detail affiche preuves, actions, restrictions et note de passation.
- Retour a la timeline conserve la periode et les filtres.
- Un evenement restreint affiche la restriction avant tout export.

### Ajouter un evenement

- Le bouton ouvre un formulaire/drawer.
- Champs minimum:
  - type;
  - date;
  - titre;
  - resume;
  - categorie;
  - statut ouvert/clos;
  - documents rattaches;
  - niveau de diffusion;
  - note de passation;
- Si la sauvegarde n'est pas encore implementee, le CTA doit etre neutralise avec
  un message produit clair, pas un bouton mort.

### Passation CS

- Le clic sur une checklist complete ouvre les sources.
- Le clic sur une checklist incomplete ouvre les sujets ouverts correspondants.
- Le clic sur une alerte ouvre l'action corrective ou l'arbitrage.
- `Voir le detail de la passation` ouvre `Pack passation`.

### A transmettre

- Les documents telechargeables ont une action explicite.
- Les documents non telechargeables affichent `Diffusion a arbitrer` ou equivalent.
- `Voir tous les documents` ouvre une liste complete filtree passation.

### Export passation

- `Exporter` ouvre le panneau d'export.
- JSON et TXT appellent les routes existantes.
- Le panneau rappelle que l'export est derive.
- Si l'export est bloque, le bouton affiche la raison.
- Les omissions sont visibles et comprehensibles.

## Etats vides

### Instance vide

Afficher:

- titre `Memoire de copropriete`;
- timeline vide;
- explication courte;
- CTA `Ajouter un evenement`;
- CTA secondaire `Ajouter une piece`;
- panneau passation en etat `Passation a preparer`;
- panneau transmission en etat `Aucun document transmissible`.

Pas de tableau technique vide.

### Aucun resultat de recherche

Afficher:

- `Aucun resultat`;
- rappel de la recherche ou des filtres actifs;
- action `Effacer la recherche`.

### Pas de sujets ouverts

Afficher un etat positif:

- `Aucun sujet ouvert identifie`;
- checklist passation majoritairement complete;
- lien pour verifier les documents cles.

### Passation incomplete

Afficher:

- progression partielle;
- sujets bloquants;
- prochaine action;
- lien vers detail.

### Export bloque

Afficher:

- raison lisible;
- liste des restrictions ou omissions;
- lien vers confidentialite ou detail document;
- aucun telechargement direct.

### Evenement introuvable

Afficher:

- message `Evenement introuvable`;
- lien retour timeline;
- pas d'erreur 500.

## Criteres d'acceptation

- `/chantiers` affiche visuellement `Memoire de copropriete` comme titre et
  entree active.
- Le mot `Chantiers` ne domine plus la page visible.
- La structure reprend l'image: entete, recherche/filtres/periode, timeline,
  panneau `Passation CS`, panneau `A transmettre`.
- La timeline affiche des evenements avec date, point couleur, icone, titre,
  sous-titre, badge categorie et chevron/detail.
- Les categories visibles couvrent au minimum AG, travaux, sinistres, contrats,
  syndic et documents quand les donnees existent.
- Le panneau `Passation CS` affiche compteur, progression, checklist et sujets
  ouverts.
- Le panneau `A transmettre` affiche documents cles, type, fraicheur,
  telechargement autorise ou raison de blocage.
- Le detail evenement memoire existe et relie preuves, actions, documents,
  restrictions et note de passation.
- Le pack passation existe comme vue/panneau derive, avec inclusions, omissions,
  restrictions et prochaines actions.
- L'export passation existe comme panneau explicatif et utilise les routes
  `/exports/passation.json` et `/exports/passation.txt`.
- Les exports affichent ou transportent le watermark
  `export derive, non source collaborative`.
- `source_of_truth` reste `False` pour le pack/export derive.
- Aucun chemin `raw`, `restricted`, `logs`, chemin absolu local, email prive ou
  payload brut ne fuit dans la page ou l'export.
- Tous les liens internes conservent le token UI existant quand la route est
  protegee.
- Une instance vide rend la page sans exception avec des etats vides lisibles.
- La page reste navigable au clavier et expose des labels accessibles pour les
  boutons icones, chevrons, filtres et telechargements.

## Tests attendus

Tests viewmodel:

- `model.ux.memoire` contient les cles:
  `context`, `summary`, `toolbar`, `filters`, `timeline`, `passation`,
  `transmit`, `pack`, `export`, `empty_states`;
- `model.ux.memoire.context.title == "Memoire de copropriete"`;
- `summary.handover_progress_pct` est coherent avec completed/total;
- les events timeline ont `id`, `date_label`, `title`, `subtitle`,
  `category_label`, `href`;
- les hrefs generes pour `/chantiers`, `/exports/passation.json` et
  `/exports/passation.txt` sont token-safe;
- aucun event ne transporte de chemin prive ou payload brut;
- `pack.source_of_truth is False`;
- `export.source_of_truth is False`.

Tests route/template:

- `GET /chantiers` retourne 200;
- le HTML contient `Memoire de copropriete`;
- le HTML contient `Passation CS`;
- le HTML contient `A transmettre`;
- le HTML contient la recherche avec placeholder attendu;
- le HTML contient les segments `5 ans`, `10 ans`, `Tout`;
- le HTML contient au moins une ligne timeline quand des donnees seed sont
  presentes;
- le HTML contient un lien vers le detail evenement;
- le HTML ne presente pas `Chantiers` comme titre principal;
- les chevrons et boutons icones ont des labels accessibles.

Tests interactions:

- `/chantiers?periode=5ans` limite les evenements affiches;
- `/chantiers?periode=10ans` selectionne `10 ans`;
- `/chantiers?periode=tout` garde la page stable;
- `/chantiers?q=ascenseur` filtre les evenements/documents;
- `/chantiers?categorie=sinistres` affiche les sinistres et leur alerte;
- `/chantiers?selected=<event_id>` affiche le detail evenement;
- `/chantiers?selected=inconnu` affiche `Evenement introuvable`;
- `/chantiers?panel=passation` affiche le pack passation;
- `/chantiers?panel=export` affiche les formats d'export.

Tests export/passation:

- `/exports/passation.json` retourne un export derive avec watermark;
- `/exports/passation.txt` retourne une version lisible avec watermark;
- les exports refusent ou omettent les marqueurs interdits:
  `raw`, `restricted`, `logs`, `file://`, chemins Windows absolus, chemins
  `/Users/...`, `/home/...`;
- les elements restreints apparaissent en omissions ou restrictions, pas en
  contenu brut;
- le pack est reconstruit depuis les donnees, pas lu comme source primaire.

Tests etats vides:

- instance vide: `/chantiers` retourne 200;
- timeline vide affiche `Aucun evenement dans la memoire`;
- passation vide affiche `Passation a preparer`;
- transmission vide affiche `Aucun document transmissible`;
- export vide affiche un statut explicite, pas une erreur 500.

Tests accessibilite/UI:

- le bouton `Exporter` est atteignable au clavier;
- le bouton split `Ajouter un evenement` expose un nom accessible;
- le panneau filtres est ouvrable et refermable au clavier;
- les lignes timeline ont un role/lien exploitable;
- les badges categorie ne sont pas la seule source d'information;
- les contrastes des alertes rouges et coches vertes restent lisibles;
- sur largeur mobile, la timeline et les panneaux ne se chevauchent pas.

## Definition de pret pour dev

Le cycle 4 est pret a lancer quand:

- cette commande est validee;
- les devs savent que la route reste `/chantiers` mais le nom visible devient
  `Memoire de copropriete`;
- le contrat `model.ux.memoire` est accepte comme cible;
- les vues manquantes sont incluses dans le ticket:
  - detail evenement memoire;
  - pack passation;
  - export passation;
- les tests attendus sont ajoutes ou adaptes avant livraison.

## Points de vigilance

- Ne pas confondre memoire et stockage documentaire: la memoire est une lecture
  actionnable, reliee aux preuves.
- Ne pas faire du pack passation une source de verite.
- Ne pas afficher des chemins locaux ou contenus sensibles.
- Ne pas masquer les omissions: un nouveau CS doit savoir ce qui manque.
- Ne pas supprimer la compatibilite `/chantiers` sans migration explicite.
- Ne pas bloquer le cycle 4 sur la creation d'evenement editable: la timeline
  derivee et la passation priment.

---

# Commande Cycle 5 - Vues manquantes prioritaires

Mission suivante a lancer apres Cycle 4: rendre actionnables les trois entrees
prioritaires du cockpit et de la memoire:

- `Toutes les actions en retard`;
- `Pieces manquantes`;
- `Relance syndic`.

Objectif: un membre du conseil syndical doit pouvoir partir du cockpit, ouvrir
une vue dediee, comprendre quoi faire maintenant, puis revenir vers la memoire
ou la fiche action sans passer par un tableau brut.

Cette commande ne remplace pas Cycle 2. Elle specialise les vues manquantes les
plus utiles pour travailler au quotidien.

## Perimetre Cycle 5

Routes cible recommandees:

- `GET /actions?view=retards` pour `Toutes les actions en retard`;
- `GET /pieces?proof=missing` pour `Pieces manquantes`;
- `GET /actions?scope=syndic&tab=relance` pour `Relance syndic`.

Alternatives acceptables si elles s'integrent mieux au code existant:

- `GET /actions?due=late`;
- `GET /actions?scope=missing-proof`;
- `GET /demandes?type=syndic`.

Contraintes:

- conserver les routes existantes tant que possible;
- ne pas creer de logique metier dupliquee dans les templates;
- garder les liens token-safe;
- ne pas envoyer de mail depuis CoproScope sans confirmation explicite;
- ne pas afficher de chemin local, contenu brut, secret, donnees restreintes ou
  information nominative inutile.

## Intention utilisateur

L'utilisateur ne cherche pas "un module". Il cherche trois reponses:

1. Qu'est-ce qui est en retard et bloque la copropriete?
2. Quelles pieces faut-il obtenir ou rattacher pour avancer?
3. Quel message peut-on envoyer au syndic, avec quelle preuve demandee et quelle
   trace garder?

Chaque vue doit donc afficher:

- pourquoi le point remonte;
- depuis quand il attend;
- quelle preuve manque;
- qui doit agir;
- quelle action concrete est proposee;
- quelle prudence de diffusion s'applique;
- ou le point restera visible dans la memoire.

## Vue 1 - Toutes les actions en retard

### Route

Route cible:

- `/actions?view=retards`

Liens entrants:

- carte cockpit `Actions en retard`;
- badge nav ou notification;
- detail memoire quand un evenement a une action en retard;
- pack passation pour les sujets ouverts.

### Structure visuelle

La vue doit etre une liste de travail priorisee, pas un tableau exhaustif:

- entete `Toutes les actions en retard`;
- sous-titre: `Ce qui depasse son echeance ou bloque une preuve attendue.`;
- cartes resume:
  - `En retard`;
  - `Critiques`;
  - `Sans preuve`;
  - `Relance syndic prete`;
- barre outils:
  - recherche;
  - filtres priorite, domaine, responsable, retard, preuve;
  - tri `plus ancien`, `plus critique`, `plus proche AG`;
- liste d'actions;
- panneau de detail ou drawer au clic.

### Ligne d'action en retard

Chaque ligne doit afficher:

- titre;
- domaine: AG, comptes, travaux, sinistre, contrat, demande, contentieux;
- priorite;
- statut retard: `En retard depuis X jours`;
- echeance initiale;
- responsable/referent;
- preuve attendue;
- prochaine action;
- badges:
  - `preuve manquante`;
  - `relance syndic`;
  - `diffusion a verifier`;
- liens:
  - `Ouvrir la fiche`;
  - `Preparer relance`;
  - `Rattacher une piece`;
  - `Voir dans la memoire`.

### Detail action retard

Le detail doit reprendre le socle Cycle 2:

- decision/source;
- action attendue;
- pourquoi c'est en retard;
- historique court;
- preuves disponibles;
- preuve manquante;
- relances syndic deja tracees;
- note de passation;
- prudence diffusion;
- CTA principal selon le cas:
  - `Preparer la relance`;
  - `Rattacher une preuve`;
  - `Marquer a verifier`;
  - `Reporter avec justification`.

### Contrat donnees

Ajouter ou stabiliser:

```python
model.ux.priority_views = {
    "late_actions": {
        "context": {
            "route": "/actions?view=retards",
            "title": "Toutes les actions en retard",
            "subtitle": "Ce qui depasse son echeance ou bloque une preuve attendue.",
        },
        "summary": {
            "total": 12,
            "critical_count": 5,
            "missing_proof_count": 8,
            "syndic_ready_count": 4,
            "oldest_delay_label": "42 jours",
        },
        "filters": {...},
        "items": [...],
        "selected": {...},
        "empty_state": {...},
    }
}
```

Item minimal:

```python
{
    "id": "action-r12-toiture",
    "title": "Obtenir ordre de service toiture",
    "domain_label": "Travaux",
    "priority": "P1",
    "due_date": "2025-09-30",
    "delay_label": "En retard depuis 18 jours",
    "owner": "Commission travaux",
    "expected_proof": "Ordre de service et planning",
    "next_step": "Relancer le syndic et rattacher la reponse.",
    "href": "/actions?selected=action-r12-toiture",
    "followup_href": "/actions?selected=action-r12-toiture&tab=relance",
    "piece_href": "/pieces?missing_for=action-r12-toiture",
    "memory_href": "/chantiers?selected=evt-toiture-2025",
    "diffusion_label": "Conseil syndical",
    "can_close": False,
}
```

### Etats vides

- Aucun retard:
  `Aucune action en retard. Les prochaines echeances restent visibles dans la memoire.`
- Donnees insuffisantes:
  `Aucune echeance exploitable. Ajoutez une date ou une preuve attendue sur les actions ouvertes.`
- Aucun resultat filtre:
  `Aucune action ne correspond a ces filtres.`

## Vue 2 - Pieces manquantes

### Route

Route cible:

- `/pieces?proof=missing`

Liens entrants:

- carte cockpit `Pieces manquantes`;
- onglet action `Pieces liees`;
- onglet action `Preuves`;
- detail memoire;
- panneau `A transmettre`.

### Structure visuelle

La vue doit aider a demander ou rattacher les pieces, pas seulement lister des
documents absents:

- entete `Pieces manquantes`;
- sous-titre: `Les pieces a obtenir, verifier ou rattacher comme preuve.`;
- indicateur completude;
- regroupement par rubrique:
  - AG/PV/resolutions;
  - contrats;
  - travaux;
  - comptes/factures;
  - sinistres;
  - contentieux;
  - passation;
- filtres:
  - criticite;
  - rubrique;
  - source attendue;
  - demande syndic prete;
  - diffusion;
- liste compacte de pieces attendues;
- panneau detail piece manquante.

### Ligne piece manquante

Chaque ligne doit afficher:

- piece attendue;
- rubrique;
- raison du besoin;
- action conseillee;
- criticite;
- rattachement attendu:
  - action;
  - evenement memoire;
  - AG/resolution;
  - fournisseur/contrat;
- statut:
  - `absente`;
  - `a demander`;
  - `candidate a verifier`;
  - `presente mais non rattachee`;
  - `restreinte`;
- CTA:
  - `Demander au syndic`;
  - `Rattacher une piece existante`;
  - `Ajouter depuis depot`;
  - `Marquer non applicable` avec justification.

### Detail piece manquante

Le detail doit distinguer:

- piece utile;
- preuve validee;
- document candidat;
- restriction de diffusion.

Contenu obligatoire:

- pourquoi la piece manque;
- ce qu'elle doit prouver;
- source probable: syndic, prestataire, coproprietaire, archive locale;
- action associee;
- demande syndic prete si applicable;
- documents candidats deja trouves;
- niveau de diffusion attendu;
- impact passation.

### Contrat donnees

Etendre `model.ux.priority_views`:

```python
model.ux.priority_views["missing_pieces"] = {
    "context": {
        "route": "/pieces?proof=missing",
        "title": "Pieces manquantes",
        "subtitle": "Les pieces a obtenir, verifier ou rattacher comme preuve.",
    },
    "summary": {
        "total": 18,
        "critical_count": 6,
        "candidate_count": 4,
        "to_request_count": 10,
        "completion_pct": 72,
    },
    "groups": [...],
    "items": [...],
    "selected": {...},
    "empty_state": {...},
}
```

Item minimal:

```python
{
    "id": "missing-contrat-syndic",
    "expected_piece": "Contrat syndic signe",
    "rubric_label": "Contrats",
    "reason": "Necessaire pour reprendre les obligations et honoraires.",
    "proof_purpose": "Prouver le mandat et les conditions applicables.",
    "criticality": "P1",
    "status": "absente",
    "status_label": "A demander",
    "source_label": "Syndic",
    "related_action_id": "action-contrat-syndic",
    "related_event_id": "evt-changement-syndic-2024",
    "request_href": "/actions?selected=action-contrat-syndic&tab=relance",
    "deposit_href": "/depot",
    "candidate_docs": [],
    "diffusion_label": "Conseil syndical",
}
```

### Etats vides

- Aucune piece manquante:
  `Aucune piece manquante prioritaire n'est remontee.`
- Aucun document candidat:
  `Aucun document candidat trouve. Deposez une piece ou preparez une demande.`
- Tout est restreint:
  `Les pieces existent mais leur diffusion doit etre arbitree avant passation.`

## Vue 3 - Relance syndic

### Route

Route cible:

- `/actions?scope=syndic&tab=relance`

Route detail possible:

- `/actions?selected=<id>&tab=relance`

Liens entrants:

- carte cockpit `Demandes syndic`;
- vue retards;
- vue pieces manquantes;
- onglet action `Relance syndic`;
- detail evenement memoire;
- pack passation.

### Structure visuelle

La vue doit etre un atelier de relance:

- entete `Relance syndic`;
- sous-titre:
  `Brouillons, relances a envoyer et reponses a verifier.`;
- onglets:
  - `A preparer`;
  - `Pretes a envoyer`;
  - `Envoyees hors CoproScope`;
  - `Reponses a verifier`;
  - `Cloturees`;
- liste de demandes;
- panneau de brouillon;
- historique de relance;
- bloc preuve attendue.

### Ligne relance

Chaque ligne doit afficher:

- objet;
- action ou piece rattachee;
- derniere demande;
- relance proposee;
- canal;
- statut;
- preuve attendue;
- priorite;
- risque de retard;
- CTA:
  - `Ouvrir le brouillon`;
  - `Copier le message`;
  - `Marquer envoye hors CoproScope`;
  - `Rattacher la reponse`;
  - `Reporter`.

### Brouillon de relance

Le brouillon doit etre copiable et sobre:

- destinataire;
- objet;
- contexte;
- demande precise;
- piece/preuve attendue;
- echeance souhaitee;
- rappel de source si disponible;
- signature/conseil syndical;
- note interne non copiee.

No-go absolu:

- ne jamais afficher `Envoyee` sans confirmation utilisateur ou preuve d'envoi;
- ne pas envoyer de mail automatiquement;
- ne pas inclure de donnees restreintes dans un brouillon diffusable;
- ne pas confondre demande coproprietaire entrante et demande portee au syndic.

### Statuts

Statuts attendus:

- `draft`: brouillon a relire;
- `ready_to_copy`: pret a copier;
- `copied`: copiee, envoi non prouve;
- `sent_external`: envoyee hors CoproScope, confirmation utilisateur;
- `answer_received`: reponse recue a verifier;
- `closed`: cloturee avec preuve;
- `blocked`: bloquee par diffusion ou piece manquante.

### Contrat donnees

Etendre `model.ux.priority_views`:

```python
model.ux.priority_views["syndic_followups"] = {
    "context": {
        "route": "/actions?scope=syndic&tab=relance",
        "title": "Relance syndic",
        "subtitle": "Brouillons, relances a envoyer et reponses a verifier.",
    },
    "summary": {
        "total_open": 7,
        "draft_count": 2,
        "ready_count": 3,
        "sent_external_count": 1,
        "answers_to_verify_count": 1,
        "blocked_count": 0,
    },
    "tabs": [...],
    "items": [...],
    "selected": {...},
    "empty_state": {...},
}
```

Item minimal:

```python
{
    "id": "followup-contrat-syndic",
    "title": "Demander le contrat syndic signe",
    "related_action_id": "action-contrat-syndic",
    "related_piece_id": "missing-contrat-syndic",
    "status": "ready_to_copy",
    "status_label": "Pret a copier",
    "priority": "P1",
    "channel_label": "Email syndic",
    "last_request_label": "Aucune demande tracee",
    "proposed_followup_label": "A envoyer maintenant",
    "expected_proof": "Contrat syndic signe",
    "draft": {
        "subject": "Demande de transmission du contrat syndic signe",
        "body": "Bonjour, pouvez-vous nous transmettre le contrat syndic signe applicable a l'exercice en cours, afin de verifier les obligations et honoraires du mandat ?",
        "internal_note": "Verifier diffusion avant partage hors CS."
    },
    "copy_action": {"label": "Copier le message", "disabled": False},
    "mark_sent_action": {"label": "Marquer envoye hors CoproScope", "requires_confirmation": True},
    "answer_href": "/depot?intent=syndic-answer",
    "memory_href": "/chantiers?selected=evt-changement-syndic-2024",
}
```

### Etats vides

- Aucune relance:
  `Aucune relance syndic n'est en attente.`
- Brouillon bloque:
  `Relance bloquee: verifier la diffusion ou preciser la preuve demandee.`
- Reponse recue mais non rattachee:
  `Reponse a verifier: rattachez la piece comme preuve ou gardez la demande ouverte.`

## Interactions transverses Cycle 5

### Depuis le cockpit

- `Actions en retard` ouvre `/actions?view=retards`;
- `Pieces manquantes` ouvre `/pieces?proof=missing`;
- `Demandes syndic` peut rester libelle cockpit, mais la vue ouverte doit
  afficher `Relance syndic` si l'onglet relance est actif;
- chaque carte conserve son compteur et son ton.

### Depuis une fiche action

- l'onglet `Preuves` pointe vers les pieces candidates;
- l'onglet `Pieces liees` distingue piece utile et preuve validee;
- l'onglet `Relance syndic` affiche le brouillon et l'historique;
- fermer une action en retard exige une preuve ou une justification.

### Depuis la memoire

- un evenement memoire affiche les actions en retard liees;
- les pieces manquantes liees a l'evenement sont visibles;
- la relance syndic liee peut etre ouverte;
- la note de passation mentionne ce qui reste a faire.

### Depuis le depot

- deposer une reponse syndic propose de la rattacher a une relance;
- deposer une piece propose de la rattacher a une piece manquante;
- le depot ne cloture pas automatiquement sans validation preuve.

## Criteres d'acceptation Cycle 5

- Les trois vues existent ou sont accessibles par routes filtrees stables.
- Le cockpit ouvre les vues dediees sans perdre le token UI.
- `Toutes les actions en retard` affiche une liste priorisee avec retard,
  preuve attendue, prochaine action et liens relance/piece/memoire.
- `Pieces manquantes` affiche les pieces attendues groupees par rubrique, avec
  raison, preuve visee, criticite et action conseillee.
- `Relance syndic` affiche brouillons, statuts, preuve demandee et historique.
- Aucune relance n'est marquee envoyee sans confirmation utilisateur.
- Une piece candidate n'est pas presentee comme preuve validee sans validation.
- Les donnees sensibles sont signalees par restriction ou omission, pas exposees
  en brut.
- Les etats vides guident vers une action concrete.
- La memoire et les fiches actions restent reliees aux vues Cycle 5.

## Tests attendus Cycle 5

Tests routes:

- `GET /actions?view=retards` retourne 200;
- `GET /pieces?proof=missing` retourne 200;
- `GET /actions?scope=syndic&tab=relance` retourne 200;
- les trois routes conservent le token quand il est exige;
- une instance vide retourne 200 pour les trois vues.

Tests contenu:

- la vue retards contient `Toutes les actions en retard`;
- la vue pieces contient `Pieces manquantes`;
- la vue relance contient `Relance syndic`;
- une action en retard seedee affiche son retard, sa preuve attendue et son lien
  de relance;
- une piece manquante seedee affiche raison, criticite et action conseillee;
- une relance seedee affiche brouillon, statut et preuve attendue.

Tests securite:

- aucun chemin `raw`, `restricted`, `logs`, `file://`, chemin absolu local ou
  payload brut n'apparait;
- une relance `draft` ou `ready_to_copy` n'est pas rendue comme `Envoyee`;
- un document restreint n'a pas de telechargement direct;
- le texte copiable de relance n'inclut pas la note interne.

Tests UX/accessibilite:

- les filtres sont atteignables au clavier;
- les cartes/lignes ont des libelles accessibles;
- le bouton `Copier le message` indique un etat apres copie;
- les CTA disabled donnent une raison;
- sur mobile, les listes et panneaux detail ne se chevauchent pas.

## Definition de pret dev Cycle 5

La prochaine commande dev est prete quand:

- Cycle 4 Memoire est transmis;
- les devs acceptent les routes filtrees ci-dessus;
- `model.ux.priority_views` ou un bloc equivalent est choisi;
- les tests route/template/security sont ajoutes avant livraison;
- les libelles visibles restent en vocabulaire conseil syndical:
  `Toutes les actions en retard`, `Pieces manquantes`, `Relance syndic`.
