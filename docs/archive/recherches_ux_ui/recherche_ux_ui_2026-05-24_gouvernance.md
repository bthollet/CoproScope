# Recherche UX/UI - Gouvernance CS/AG

Date de lancement: 2026-05-24 03:27 +02:00
Date de cloture: 2026-05-24 04:12 +02:00
Statut: recherche UX/UI cloturee, sans dev
Rattachement: `RM-2026-0024`
Chantier: `CH-20260524-032712-RM-2026-0024-gouvernance-ux-ui`
Conversation coordinatrice: `CONV-2026-1343`
Assets mission: `docs/assets/ux-ui-recherche-2026-05-24-gouvernance/`

## BOT-START

```text
BOT-START - Orchestrateur UX/UI - 2026-05-24 03:27 +02:00
Roadmap: RM-2026-0024
Chantier: CH-20260524-032712-RM-2026-0024-gouvernance-ux-ui
Conversation: CONV-2026-1343
Role: Orchestrateur UX/UI
Mission: lancer une recherche UX/UI sans dev sur l'atelier de gouvernance CS/AG.
Ownership modifiable: docs/recherche_ux_ui_2026-05-24_gouvernance.md, docs/assets/ux-ui-recherche-2026-05-24-gouvernance/, docs/presence_agents.md, docs/roadmap_backlog_central.md.
Fichiers a eviter: code applicatif, templates, CSS, tests, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, RM-2026-0017 bloque.
Passerelle/registre de trace: ce livrable de mission et docs/presence_agents.md.
Dernier point lu: AGENTS.md, docs/protocole_equipe_ux_ui_recherche.md, docs/orchestration_agents.md, docs/roadmap_backlog_central.md, docs/presence_agents.md, docs/point_coordination_live_8766_2026-05-21.md, docs/coordination_interconversations_2026-05-21.md.
Tests/preuves attendus: preuve documentaire, lignes de presence, heartbeat 10 minutes; pas de test applicatif car aucun code ne doit etre modifie.
Risque de collision: equipe UX/UI ajout docs active sur RM-2026-0003; mission gouvernance separee sur RM-2026-0024. Collision d'identifiants detectee ensuite avec un autre chantier, mission renumerotee en CONV-2026-1343 a CONV-2026-1348.
Lease ownership: jusqu'au 2026-05-25 03:27 +02:00.
Prochaine action: lancer les roles UX/UI en lecture seule/documentation, consolider parcours, images candidates, tests metier et novice.
```

## Objectif

Produire une decision UX/UI documentee pour l'atelier de gouvernance CS/AG:
preparation de resolutions et questions d'assemblee generale, avis du conseil
syndical, comptes rendus CS, preuves rattachees, validation ou signature a
distance et revue de diffusion.

Cette recherche ne produit ni patch, ni commande dev detaillee, ni serveur. Elle
converge vers un choix de parcours MVP et des directions UI testables par un
membre de conseil syndical novice.

## Roles

| Conversation | Role | Agent | Statut | Sortie |
|---|---|---|---|---|
| `CONV-2026-1343` | Orchestrateur UX/UI | fil courant | `CLOTURE` | Cadrage, arbitrage, mission, heartbeat et synthese finale. |
| `CONV-2026-1344` | Chercheur utilisateur | Nash `019e579b-1266-7f21-958b-1f3c128ae083` | `CLOTURE` | Profils, besoins, irritants, scenarios et criteres de reussite integres. |
| `CONV-2026-1345` | Architecte UX | Ohm `019e579b-15b8-7920-85d7-794eaf9e0fc3` | `CLOTURE` | Parcours, etats d'ecran, priorites d'information et wireflows integres. |
| `CONV-2026-1346` | Designer UI / generateur visuel | agent bloque par limite; reprise orchestrateur | `CLOTURE` | Directions UI, prompts et blueprints SVG integres. |
| `CONV-2026-1347` | Testeur metier expert | agent bloque par limite; reprise orchestrateur | `CLOTURE` | No-go metier, vocabulaire et cas limites integres. |
| `CONV-2026-1348` | Testeur accessibilite / novice | agent bloque par limite; reprise orchestrateur | `CLOTURE` | Verdict novice, libelles a simplifier et conditions d'acceptation integres. |

## Sources

| Source | Usage |
|---|---|
| `docs/enquete_collaboration_coedition_impact_2026-05-24.md` | Etude source pour la gouvernance collaborative. |
| `docs/ag_contentieux_passation.md` | Objets metier AG, contentieux, passation et garde-fous. |
| `docs/ui_ag_contentieux_passation.md` | Surface UI AG/contentieux/passation existante et limites. |
| `docs/ux_ecarts_enquete_vs_produit_2026-05-20.md` | Ecarts connus sur AG, decisions, preuves et roles. |
| `docs/test_novice_live_8766_2026-05-21.md` | Signaux de confusion novice sur AG/contentieux et libelles. |
| `docs/roadmap_backlog_central.md` | Gouvernail produit et rattachement `RM-2026-0024`. |

## Synthese Utilisateur

Les profils prioritaires sont le president ou secretaire de conseil syndical,
le membre CS novice, le syndic benevole, le coproprietaire contributeur hors CS,
l'expert externe ponctuel et le nouveau membre en passation.

Le besoin commun n'est pas une coedition temps reel. Il faut travailler un
document de gouvernance avec un statut clair, une preuve rattachee, une version,
un responsable, une echeance, une diffusion autorisee et une trace
transmissible.

Le risque utilisateur principal est la confusion entre `projet CS`, `demande au
syndic`, `convocation officielle`, `avis CS`, `compte rendu CS` et `PV d'AG`.
Le seuil de reussite est zero confusion critique en test novice.

## Architecture UX

Les deux parcours partagent le meme contrat d'ecran:

- statut clair: `Brouillon interne`, `En relecture`, `Pret a valider`,
  `Valide CS`, `Revue diffusion`, `Export confirme`;
- objet travaille: question AG, resolution, reunion CS ou decision;
- preuve/source visible: piece liee, preuve manquante, preuve a verifier;
- prochaine action: qui fait quoi, pour quand;
- version et validation: version precise, validateur, role, date;
- diffusion: interne CS, coproprietaires, apres biffage, bloque;
- journal: modifications, validations, exports et actions generees.

### Parcours A - Atelier AG

`Cockpit > Atelier AG > Choisir ou creer une question > Cadrer le texte >
Rattacher preuves > Demander relecture > Stabiliser version > Validation interne
CS > Revue diffusion > Export de travail ou version diffusable`

La mention `Projet CS - non officiel` doit rester visible jusqu'a la sortie de
l'atelier. La validation est bloquee si une preuve attendue manque ou si la
diffusion est bloquee.

### Parcours B - Compte Rendu CS

`Cockpit > Reunion CS > Saisir presents et sujets > Noter decisions/actions >
Rattacher preuves > Relire par membres CS > Valider une version > Validation
interne > Generer actions > Archiver memoire`

Toute correction apres validation cree une nouvelle version. Le CR CS ne doit
jamais etre presente comme un PV d'AG ou comme un acte officiel externe.

## Directions UI

| Direction | Statut | Asset | Decision |
|---|---|---|---|
| `D1` Atelier AG | `a tester` | `docs/assets/ux-ui-recherche-2026-05-24-gouvernance/atelier-ag-blueprint.svg` | Forte valeur avant AG, mais risque metier plus eleve. |
| `D2` Compte rendu CS valide en interne | `retenue` | `docs/assets/ux-ui-recherche-2026-05-24-gouvernance/compte-rendu-cs-blueprint.svg` | MVP recommande car boucle plus complete: reunion, decision, action, preuve, version, memoire. |

Prompt D1:

```text
Interface web professionnelle et sobre pour un atelier AG de conseil syndical.
Vue desktop dense: colonne gauche liste des questions/resolutions, centre texte
de resolution avec blocs sourcees, droite preuves, relecteurs, statut et revue
de diffusion. Bandeau tres visible "Projet CS - non officiel". Pas de donnees
reelles, pas de style marketing.
```

Prompt D2:

```text
Interface web professionnelle et sobre pour compte rendu du conseil syndical.
Vue desktop dense: colonne ordre du jour, centre decisions/actions/preuves,
droite version, validateurs internes, limites de signature et diffusion.
Montrer "Validation interne CS" et "Ne vaut pas signature qualifiee". Pas de
donnees reelles, pas de style marketing.
```

## Test Metier

No-go metier:

- promettre une convocation officielle, un PV d'AG, un avis juridique ou une
  signature electronique qualifiee;
- laisser signer ou diffuser une version dont les preuves ou restrictions sont
  encore ambigues;
- melanger avis CS, CR CS, demande au syndic et document emis officiellement;
- transformer un commentaire ou une opinion non sourcee en position du CS.

Vocabulaire conseille:

- `Projet CS - non officiel`;
- `Validation interne CS`;
- `Version de travail`;
- `Revue de diffusion`;
- `Piece source`;
- `Preuve a verifier`;
- `Envoye hors CoproScope`.

Vocabulaire deconseille:

- `convocation officielle` si CoproScope ne l'emet pas;
- `signature` seule, sans qualifier sa portee;
- `PV d'AG` pour un compte rendu CS;
- `avis juridique`;
- `publier` sans revue de diffusion.

## Test Novice

Verdict provisoire:

- `D1 Atelier AG`: GO recherche, NO-GO MVP immediat si le statut non officiel
  n'est pas visible en permanence.
- `D2 Compte rendu CS`: GO concept pour MVP, car le novice comprend plus vite
  la boucle reunion -> decision -> action -> preuve -> validation -> memoire.

Questions qu'un novice poserait:

- Est-ce que ce document est officiel ou seulement un brouillon du CS ?
- Qui doit valider cette version ?
- Est-ce que je signe juridiquement quelque chose ?
- Quelle piece prouve cette phrase ?
- Qu'est-ce qui sera visible par les coproprietaires ?
- Si je corrige apres validation, que devient l'ancienne version ?

Conditions d'acceptation novice:

- en moins de 30 secondes, identifier statut, prochaine action, preuve et
  diffusion;
- zero confusion entre CR CS et PV d'AG;
- zero confusion entre validation interne et signature qualifiee;
- au moins une preuve ou une preuve manquante visible sans ouvrir une annexe;
- revue de diffusion obligatoire avant export.

## Decision

Recommandation UX/UI: demarrer par `Compte rendu CS valide en interne`.

Raison: c'est la boucle la plus maitrisable et la plus utile comme socle de
gouvernance: reunion, decision, action, preuve, validation, version et memoire.
Elle alimente ensuite naturellement l'Atelier AG, sans commencer par le cas le
plus risque en confusion officielle.

L'Atelier AG reste la direction suivante, a tester avec le bandeau permanent
`Projet CS - non officiel`, le rattachement phrase -> preuve et la revue de
diffusion.

## Questions Ouvertes

- Brice veut-il prioriser le gain avant AG malgre le risque metier, ou accepter
  le CR CS comme socle MVP plus prudent ?
- Quel niveau de validation interne suffit: un clic horodate, une signature
  manuscrite importee, ou un futur mecanisme cryptographique ?
- Qui peut exporter une version diffusable: president CS, secretaire, syndic
  benevole, ou tout membre autorise ?
- Faut-il lier tout de suite les coproprietaires, lots, pouvoirs et feuilles de
  presence de `RM-2026-0026`, ou garder ce lien pour un lot suivant ?

## BOT-END

```text
BOT-END - Orchestrateur UX/UI - 2026-05-24 04:12 +02:00
Roadmap: RM-2026-0024
Chantier: CH-20260524-032712-RM-2026-0024-gouvernance-ux-ui
Conversation: CONV-2026-1343
Statut: CLOTURE
Fichiers modifies: docs/recherche_ux_ui_2026-05-24_gouvernance.md, docs/assets/ux-ui-recherche-2026-05-24-gouvernance/atelier-ag-blueprint.svg, docs/assets/ux-ui-recherche-2026-05-24-gouvernance/compte-rendu-cs-blueprint.svg, docs/presence_agents.md, docs/roadmap_backlog_central.md.
Fichiers volontairement evites: code applicatif, templates, CSS, tests, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, RM-2026-0017 bloque.
Tests/preuves: preuve documentaire et blueprints SVG; pas de test applicatif car aucun code produit.
Limites: trois sous-agents bloques par limite d'usage; roles designer, metier et novice repris par l'orchestrateur dans la trace.
Questions ouvertes: arbitrage Brice entre CR CS MVP prudent et Atelier AG plus impactant mais plus risque.
Prochain mouvement propose: si GO produit, ouvrir un chantier dev separe sur le MVP `Compte rendu CS valide en interne`, avec gates anti-confusion et anti-fuite.
```

UXUI-DONE - equipe UX/UI a fini son job
