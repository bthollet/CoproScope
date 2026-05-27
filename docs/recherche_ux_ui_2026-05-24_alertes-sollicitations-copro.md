# Recherche UX/UI - alertes et sollicitations coproprietaires

Date de lancement: 2026-05-24 03:28 +02:00.
Roadmap: `RM-2026-0031`.
Chantier: `CH-20260524-032804-RM-2026-0031-alertes-sollicitations-copro`.
Conversation coordinatrice: `CONV-2026-1349`.

## BOT-START - Orchestrateur UX/UI - 2026-05-24 03:28 +02:00

Roadmap: `RM-2026-0031`
Chantier: `CH-20260524-032804-RM-2026-0031-alertes-sollicitations-copro`
Conversation: `CONV-2026-1349`
Role: Orchestrateur UX/UI
Mission: lancer une recherche UX/UI sans dev sur l'integration d'alertes ou sollicitations des coproprietaires.
Ownership modifiable: ce livrable, le dossier `docs/assets/ux-ui-recherche-2026-05-24-alertes-sollicitations-copro/`, `docs/roadmap_backlog_central.md` et `docs/presence_agents.md`.
Fichiers a eviter: code applicatif, tests applicatifs, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, `RM-2026-0017` bloque.
Passerelle/registre de trace: ce livrable et `docs/presence_agents.md`.
Dernier point lu: `AGENTS.md`, `docs/orchestration_agents.md`, `docs/protocole_equipe_ux_ui_recherche.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/consignes_bots_interconversations.md`, `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`, `docs/point_coordination_live_8766_2026-05-21.md`, `docs/coordination_interconversations_2026-05-21.md`.
Tests/preuves attendus: pas de test applicatif; preuve attendue = synthese UX/UI, decisions, retours testeurs, images retenues ou justification d'absence d'image, et marqueur final `UXUI-DONE`.
Risque de collision: plusieurs equipes UX/UI sont actives; cette mission est separee et ne modifie pas leurs livrables.
Lease ownership: 2026-05-25 04:12 +02:00.
Prochaine action: consolider les sorties des roles et archiver seulement les images utiles a decision.

## Cadre

La recherche porte sur une surface entrante: alertes, signalements, questions ou sollicitations venant de coproprietaires, a traiter par un conseil syndical, un syndic benevole ou une personne chargee du suivi.

La mission ne produit pas de code. Elle doit clarifier:

- ce qui distingue une alerte, une demande, une question, un incident, une piece et une action;
- comment l'entree est capturee sans exposer de donnees privees;
- comment l'utilisateur qualifie l'urgence, la diffusion, le rattachement et la suite;
- comment la sollicitation devient un point, une action, une preuve, une reponse ou une archive;
- quels cas doivent rester hors automatisation ou demander arbitrage humain.

## Roles actifs

| Conversation | Role | Sortie attendue |
|---|---|---|
| `CONV-2026-1350` | Chercheur utilisateur | Profils, besoins, irritants, scenarios et criteres de reussite. |
| `CONV-2026-1351` | Architecte UX | Parcours, hierarchie d'information, etats, wireflows et points de friction. |
| `CONV-2026-1352` | Designer UI / generateur visuel | Directions UI, prompts/images candidates, principes visuels et interactions. |
| `CONV-2026-1353` | Testeur metier expert | Justesse domaine, cas limites, vocabulaire, mandat de reponse et risques. |
| `CONV-2026-1354` | Testeur accessibilite / novice | Lisibilite, comprehension immediate, charge cognitive et risques de blocage. |

## Sources initiales

- `docs/ui_demandes_coproprietaires.md`: base existante pour demandes coproprietaires multi-canaux.
- `RM-2026-0026`: fichier des coproprietaires relie aux AG.
- `RM-2026-0028`: communication officielle, boite mail et LRAR.
- `RM-2026-0027`: syndics benevoles, communication et demandes terrain.
- `docs/test_novice_live_8766_2026-05-21.md`: signaux sur demandes, relances, alertes et comprehension novice.
- `docs/ux_ecarts_enquete_vs_produit_2026-05-20.md`: intention produit demande -> action -> preuve.

## Questions de recherche

1. Quelle entree doit etre traitee comme alerte prioritaire plutot que simple demande?
2. Quels champs minimaux permettent de qualifier une sollicitation sans formulaire lourd?
3. Comment eviter qu'une boite d'arrivee coproprietaires devienne une liste anxiogene ou juridiquement risquee?
4. Quand faut-il repondre, demander une piece, creer une action, rattacher une preuve ou escalader vers AG/CS/syndic?
5. Quelle preuve de traitement doit etre visible pour le coproprietaire, et laquelle doit rester interne?
6. Quels garde-fous privacy et mandat sont obligatoires avant diffusion ou reponse?

## Hypotheses de depart

- Une vue unique "Entrees coproprietaires" doit separer reception, qualification, rattachement et reponse.
- Une alerte utile combine sujet, impact, echeance, source et action suivante; une alerte sans suite est bruit.
- L'utilisateur novice a besoin de verbes simples: qualifier, rattacher, demander une preuve, preparer une reponse, classer.
- Les sollicitations doivent etre reliees a des objets existants: lot, personne ou alias, document, point AG/CS, action, preuve, incident, travaux ou compte.
- Les communications engageantes doivent rester brouillon + validation humaine, sans envoi automatique implicite.

## Images retenues

| Image | Intention | Statut | Decision |
|---|---|---|---|
| `docs/assets/ux-ui-recherche-2026-05-24-alertes-sollicitations-copro/blueprint_entrees_coproprietaires.svg` | Blueprint de decision pour une boite d'entrees coproprietaires avec liste priorisee, detail, preuve/action et reponse brouillon. | retenue | Sert de direction de reference: inbox priorisee + panneau de qualification, historique en second niveau. |

## Journal de mission

| Heure | Signal | Detail |
|---|---|---|
| 2026-05-24 03:28 +02:00 | START | Mission ouverte, gouvernail et presence mis a jour, roles UX/UI lances en lecture/documentation. |
| 2026-05-24 04:12 +02:00 | RENUMBER | Collision detectee avec l'equipe gouvernance sur `CONV-2026-1319`..`1324`; mission renumerotee une premiere fois. Le premier lancement agent a echoue par limite de credits, sans sortie exploitable. |
| 2026-05-24 04:13 +02:00 | RELANCE | Roles relances: Boole chercheur, Harvey architecte UX, Russell designer UI, Archimedes testeur metier, Mill testeur novice. |
| 2026-05-24 04:18 +02:00 | RENUMBER_FINAL | Collision tardive avec la mission gouvernance renumerotee en `CONV-2026-1343`..`1348`; mission alertes fixee en `CONV-2026-1349`..`1354`. |
| 2026-05-24 04:17 +02:00 | END | Sorties consolidees, blueprint retenu, roles clotures. Aucun code applicatif modifie. |

## Synthese finale

Objectif: definir sans dev la bonne integration UX/UI des messages, alertes,
questions, signalements et demandes venant de coproprietaires.

Limite importante: la surface n'est pas une messagerie ni un reseau social. Elle
sert a reprendre une trace entrante, la qualifier, la lier a un dossier, garder
la preuve et preparer une suite humaine.

## Profils cibles

- Membre de conseil syndical novice: veut savoir quoi traiter, quoi prouver et quoi partager.
- Syndic benevole: doit repondre, relancer, garder trace et preparer la passation.
- Referent incident/travaux: recoit des signalements urgents et doit prioriser.
- Referent AG/gouvernance: transforme questions et contestations en points instruits.
- Coproprietaire emetteur: attend accuse de reception, suite prudente et trace.

## Parcours principal

1. Reception: email resume, oral, courrier, AG, portail, document, incident ou commission.
2. Tri: `A traiter maintenant`, `A qualifier`, `En attente`, `A relancer`, `Non rattachees`, `Restreintes`, `Cloturees`.
3. Qualification: nature, urgence, preuve, diffusion, prochaine suite.
4. Rattachement: point CS/AG, action, preuve, document, incident, travaux, comptes ou contentieux.
5. Reponse: brouillon local ou note de reponse, jamais envoi implicite.
6. Suivi: journal de diligence pour qualification, preuve, relance, reponse, diffusion et cloture.
7. Cloture: uniquement avec preuve, motif, escalade ou sans-suite motivee.

## Problemes prioritaires

- Le terme `alerte` doit rester reserve aux entrees avec impact, echeance et action suivante.
- Une demande entrante ne doit pas etre confondue avec une demande sortante au syndic.
- La preuve doit etre separee: source, envoi, reception, diligence, cloture.
- La diffusion doit distinguer original restreint, synthese diffusable et pieces jointes.
- Une reponse au nom du CS, du syndic benevole ou du syndic professionnel n'a pas le meme mandat.
- Les messages conflictuels ou nominatifs demandent moderation: original restreint + synthese neutre.

## Recommandations

P0 - Ecran principal: `Messages recus des coproprietaires` ou `Entrees coproprietaires`, avec file priorisee a gauche et panneau de qualification a droite.

P0 - Vocabulaire novice: `message recu`, `comprendre et classer`, `lier a un dossier`, `qui peut voir ?`, `piece qui peut servir de preuve`, `noter un envoi fait hors CoproScope`.

P0 - Gates humains: identite/mandat, qualification, reponse, diffusion, preuve, moderation, AG/CS, mail/LRAR.

P1 - Historique: onglet ou mode secondaire centre sur la passation et le journal de diligence.

P1 - V1 sans connecteur: saisie locale et resume manuel assumes; mail/LRAR plus tard, apres mandat et preuve.

P2 - Vue coproprietaire: limitee a l'etat, la reponse et les pieces effectivement diffusables.

## Direction UI retenue

Direction retenue: inbox priorisee + panneau de qualification.

Structure:

- colonne gauche: files de travail et lignes compactes avec canal, sujet fictif, raison de priorite, echeance, preuve et diffusion;
- panneau central/droite: raison d'attention, action primaire, preuve/source, diffusion, rattachement, brouillon, journal;
- historique/passation: second niveau, pas ecran principal.

Prompt image retenu:

```text
Interface web professionnelle et dense pour conseil syndical, inbox priorisee de messages coproprietaires a gauche, panneau de qualification a droite, libelles francais novices, donnees entierement fictives, badges preuve/action/diffusion, palette sobre claire avec accents vert, bleu, ambre et rouge, sidebar sombre, aucun effet marketing, aucune carte imbriquee.
```

## Retours testeurs

Testeur metier expert: GO recherche, mais NO-GO pour toute interface qui confond recevoir, qualifier, repondre, diffuser, envoyer officiellement et cloturer. Les cas sensibles doivent passer par `original restreint + synthese neutre`; mail/LRAR exige mandat, confirmation et preuve depot/reception.

Testeur accessibilite / novice: NO-GO conceptuel si l'interface garde ensemble `alerte`, `demande`, `action`, `preuve`, `piece`, `reponse` et `diffusion` sans definition operationnelle. En moins d'une minute, l'utilisateur doit savoir d'ou vient le message, pourquoi il compte, quelle preuve existe, qui peut voir, et ce que fait le bouton principal.

## Decisions

- Le nom produit provisoire est `Messages recus des coproprietaires`; `Entrees coproprietaires` reste acceptable pour les experts.
- Le mot `sollicitation` n'est pas un libelle principal novice.
- Le MVP ne contient pas d'envoi automatique.
- Une alerte sans action suivante est rejetee comme bruit.
- Le premier ecran montre une action principale par ligne.
- Les donnees brutes personnelles ne sont pas affichables a tous les coproprietaires.

## Questions ouvertes

- Faut-il distinguer deux entrees de menu: `Messages recus` et `Demandes au syndic`, ou garder une seule surface avec deux files?
- Quelle granularite minimale pour le fichier coproprietaires/mandats avant d'activer les reponses?
- Quel statut exact pour une question candidate AG: `a instruire`, `a inscrire`, `hors delai`, `decision AG requise`?
- Quel format de preuve de diligence est suffisant sans alourdir le travail humain?
- Quand l'original doit-il rester restreint meme si une synthese est diffusable?

## BOT-END - Orchestrateur UX/UI - 2026-05-24 04:17 +02:00

Roadmap: `RM-2026-0031`
Chantier: `CH-20260524-032804-RM-2026-0031-alertes-sollicitations-copro`
Conversation: `CONV-2026-1349`
Statut: `CLOTURE`
Fichiers modifies: ce livrable, `docs/assets/ux-ui-recherche-2026-05-24-alertes-sollicitations-copro/blueprint_entrees_coproprietaires.svg`, `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`.
Fichiers volontairement evites: code applicatif, tests applicatifs, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, `RM-2026-0017` bloque.
Tests/preuves: pas de test applicatif car recherche sans dev; preuves = sorties roles, synthese, blueprint SVG retenu.
Limites: aucun test navigateur, aucun prototype interactif, aucune integration mail/LRAR.
Questions ouvertes: voir section precedente.
Prochain mouvement propose: arbitrer le MVP `Messages recus des coproprietaires`, puis ouvrir un chantier dev separe seulement si cette direction est validee.

Aucun code n'a ete produit.

UXUI-DONE - equipe UX/UI a fini son job
