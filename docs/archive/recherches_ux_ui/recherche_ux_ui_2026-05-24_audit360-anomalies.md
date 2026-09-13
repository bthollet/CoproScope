# Recherche UX/UI - Audit360 et cycle de vie des anomalies

Date de lancement: 2026-05-24 03:30 +02:00.
Mode: equipe UX/UI recherche visuelle sans dev.

## BOT-START

```text
BOT-START - Orchestrateur UX/UI - 2026-05-24 03:30 +02:00
Roadmap: RM-2026-0008 principal; liens RM-2026-0003, RM-2026-0006, RM-2026-0010, RM-2026-0016, RM-2026-0029, RM-2026-0030. RM-2026-0017 reste bloque et n'est pas relance.
Chantier: CH-20260524-033000-RM-2026-0008-audit360-anomalies-ux
Conversation: CONV-2026-1325
Role: Orchestrateur UX/UI
Mission: lancer une recherche UX/UI sans dev sur l'integration Audit360 dans CoproScope, le suivi des anomalies et la prise en compte de nouveaux documents dans la levee, l'aggravation ou le suivi des anomalies.
Ownership modifiable: docs/recherche_ux_ui_2026-05-24_audit360-anomalies.md; docs/assets/ux-ui-recherche-2026-05-24-audit360-anomalies/; docs/presence_agents.md; trace append-only de docs/roadmap_backlog_central.md.
Fichiers a eviter: code applicatif, tests, instances privees, secrets, exports bruts, passerelles hors mission, chantier reconstruction bloque RM-2026-0017.
Passerelle/registre de trace: ce document et docs/presence_agents.md.
Dernier point lu: AGENTS.md, docs/orchestration_agents.md, docs/protocole_equipe_ux_ui_recherche.md, docs/protocole_roadmap_presence_agents.md, docs/consignes_bots_interconversations.md, docs/roadmap_backlog_central.md, docs/presence_agents.md, docs/coordination_interconversations_2026-05-21.md, docs/point_coordination_live_8766_2026-05-21.md.
Tests/preuves attendus: synthese multi-roles, wireflow ou image de decision, retours metier et novice, decisions UX/UI, questions ouvertes, mention explicite qu'aucun code n'a ete produit.
Risque de collision: equipes UX/UI ajout-docs et gouvernance deja actives; cette mission reste separee et ne modifie pas leurs livrables sauf decision explicite du coordinateur.
Lease ownership: jusqu'au 2026-05-25 03:30 +02:00.
Prochaine action: lancer les roles UX/UI en sous-agents de lecture/recherche.
```

## Objectif de la recherche

Clarifier comment CoproScope doit presenter et piloter trois choses liees:

- l'integration d'Audit360 comme couche transverse qui transforme constats, risques, preuves attendues et suites a donner en objets comprehensibles;
- le suivi des anomalies, avec etats lisibles entre signal brut, anomalie qualifiee, action ouverte, preuve attendue, levee, levee partielle, aggravation et surveillance;
- l'arrivee de nouveaux documents, traites localement ou par IA selon les garde-fous, qui peuvent lever une anomalie, l'aggraver, la documenter, ou seulement demander une validation humaine.

Le livrable attendu est une decision produit documentee, pas une commande dev. Si une suite dev devient utile, elle devra etre ouverte ensuite comme chantier distinct avec owner code unique.

## Sources de depart

- `docs/audit360.md`
- `docs/commande_cycle9_module_audit_boite_reprise_probatoire.md`
- `docs/factureops.md`
- `docs/fonctions_cibles.md`
- `docs/architecture_et_flux.md`
- `docs/indicateurs_pilotage_copro.md`
- `docs/roadmap_backlog_central.md`
- `docs/presence_agents.md`
- `docs/recherche_ux_ui_2026-05-24_ajout-docs.md`
- `docs/recherche_ux_ui_2026-05-24_gouvernance.md`

## Roles actifs

| Conversation | Role | Mission | Statut |
|---|---|---|---|
| `CONV-2026-1325` | Orchestrateur UX/UI | Cadre, trace, arbitre et livre la synthese. | En cours |
| `CONV-2026-1326` | Chercheur utilisateur | Profils, besoins, irritants, scenarios et criteres de reussite. | En cours |
| `CONV-2026-1327` | Architecte UX | Parcours, etats, priorites d'information et wireflows. | En cours |
| `CONV-2026-1328` | Designer UI / generateur visuel | Directions UI, images candidates et principes d'interaction. | En cours |
| `CONV-2026-1329` | Testeur metier expert | Justesse audit/copro/anomalies, cas limites et vocabulaire. | En cours |
| `CONV-2026-1330` | Testeur accessibilite / novice | Comprehension immediate, lisibilite, charge cognitive et blocages. | En cours |

## Questions de recherche

- Quel est le vocabulaire utilisateur pour une anomalie qui n'est pas encore prouvee, une anomalie confirmee, une anomalie levee et une anomalie aggravee?
- Quelle vue pivot relie le mieux Audit360, les anomalies, les pieces, les actions, les preuves et les decisions?
- Comment montrer qu'un nouveau document a change l'etat d'une anomalie sans faire croire a une decision automatique?
- Quand faut-il demander une validation humaine explicite, notamment si l'IA locale ou cloud propose une levee ou une aggravation?
- Comment separer les signaux techniques d'Audit360 des messages utiles a un membre de conseil syndical novice?
- Quels etats vides, alertes et traces rendent le suivi probatoire credible sans exposer de donnees privees?

## Hypothese de parcours principal

1. L'utilisateur ouvre une anomalie ou un constat Audit360 depuis le cockpit, les comptes, les documents ou les actions.
2. CoproScope affiche le statut courant, la raison du signal, les preuves deja rattachees, ce qui manque et la prochaine action utile.
3. Un nouveau document arrive par depot, inbox, import local ou analyse assistee.
4. CoproScope propose un impact possible: preuve ajoutee, levee candidate, aggravation candidate, doublon, hors sujet ou besoin de revue.
5. L'utilisateur confirme, corrige ou refuse l'impact. La trace garde source, date, niveau de confiance, decision humaine et prochaine action.
6. La vue anomalie se met a jour sans effacer l'historique: ce qui etait vrai avant, ce que le document change, ce qui reste a verifier.

## Contraintes non negociables

- Aucun document brut, chemin prive, nom local, `raw`, `restricted`, `logs`, secret ou URL locale ne doit etre rendu diffusable.
- La levee ou l'aggravation d'une anomalie ne doit pas etre presentee comme une certitude IA sans validation humaine.
- Les coproprietaires novices doivent voir une phrase courte: pourquoi cela compte, quelle preuve existe, qui doit agir et ce qui a change.
- Audit360 doit rester relie a DocOps, ComptaScope, DecisionOps, AGOps et aux actions; il ne doit pas devenir un ecran isole.
- Les documents nouveaux peuvent suggerer un changement d'etat, mais le produit doit conserver l'ancien etat comme historique probatoire.

## A completer par l'equipe

- Profils utilisateurs cibles.
- Parcours principal et variantes.
- Etats d'anomalie proposes.
- Problemes UX/UI priorises.
- Recommandations classees par impact.
- Wireflow ou images retenues avec chemins locaux.
- Prompts ou intentions de generation.
- Retours du Testeur metier expert.
- Retours du Testeur accessibilite / novice.
- Decisions prises.
- Questions ouvertes.

## Point relance - 2026-05-24 04:03 +02:00

- A produire: retours des roles Chercheur utilisateur, Architecte UX, Designer UI et Testeur metier expert; test accessibilite/novice a couvrir des qu'un thread se libere ou par l'orchestrateur.
- En test: aucun ecran reel ni serveur; recherche documentaire uniquement.
- Images candidates: aucune image retenue pour l'instant; le designer doit proposer des directions visuelles et prompts avant generation/archivage.
- Decisions ouvertes: vocabulaire des etats d'anomalie; vue pivot Audit360/anomalies/documents; place exacte de la validation humaine avant levee ou aggravation; niveau de detail historique visible au premier ecran.
- Prochain mouvement: attendre les quatre retours agents, puis consolider la synthese et produire le test novice manquant si la limite de threads persiste.

## Profils utilisateurs cibles

- Membre de conseil syndical novice: veut comprendre quoi verifier, quelle preuve manque et quelle action lancer sans lire un registre technique.
- Referent conseil syndical avance: suit plusieurs constats, arbitre les preuves et prepare les demandes au syndic, les reserves ou les points d'AG.
- Responsable preuve/action: rattache documents, reponses, decisions et relances a une anomalie sans perdre l'historique.
- Relecteur prudent: controle confidentialite, diffusion, niveau de certitude et trace humaine avant partage ou export.

## Parcours principal et variantes

Parcours principal retenu:

1. Ouvrir un point depuis cockpit, comptes, documents ou actions.
2. Lire une fiche pivot `Point a verifier`: ce qui est constate, pourquoi cela compte, preuve actuelle, preuve attendue, prochaine action.
3. Recevoir ou ajouter un document par DocOps ou depot local.
4. Voir un impact propose: preuve candidate, levee proposee, levee partielle, criticite relevee, conflit, doublon, hors sujet ou revue humaine requise.
5. Confirmer, corriger ou refuser l'impact avec motif.
6. Conserver un historique probatoire: etat avant, document source, proposition, decision humaine, etat apres, prochaine action.

Variantes:

- Vue novice: une anomalie a la fois, une action principale, vocabulaire court.
- Vue standard conseil syndical: file d'anomalies, fiche active, panneau nouveau document et timeline.
- Vue expert: table dense avec filtres et panneau detail, jamais comme premier ecran novice.
- Flux document-first: partir de `Documents a examiner`, puis rattacher un document a une ou plusieurs anomalies impactees.

## Etats d'anomalie proposes

Decision de recherche: separer trois dimensions.

- Priorite: `P1 a traiter`, `P2 a confirmer`, `OK avec preuve locale`.
- Cycle de vie: `Signal detecte`, `A qualifier`, `Anomalie qualifiee`, `Action ouverte`, `Preuve attendue`, `Preuve candidate recue`, `Revue humaine requise`, `Levee proposee`, `Levee validee`, `Levee partielle`, `Non levee`, `Criticite relevee`, `Conflit de sources`, `Surveillance`, `Cloturee avec reserve`, `Faux positif`.
- Confiance / diffusion: preuve locale suffisante, traitement local ou IA a confirmer, document restreint, version diffusable apres masquage, blocage confidentialite.

Regle UX P0: un nouveau document ne leve jamais une anomalie tout seul. Il propose un impact que l'humain valide, corrige ou refuse.

## Problemes UX/UI priorises

- P0: confusion entre `document recu`, `preuve candidate`, `preuve validee` et `anomalie levee`.
- P0: risque de faire croire qu'Audit360 ou l'IA decide juridiquement ou comptablement.
- P0: absence d'historique avant/apres, qui rend la levee peu credible.
- P1: surcharge des grands tableaux Audit360, surtout pour un membre CS novice.
- P1: vocabulaire trop dur: `Audit360`, `L4`, `controle`, `probatoire`, `aggravation`, `P1/P2/OK`.
- P1: preuve non qualifiee: une piece doit dire preuve de quoi, avec quelle limite.
- P2: niveau de confiance utile au metier mais potentiellement anxiogene au premier niveau.

## Recommandations classees par impact

- Impact tres fort: creer une fiche pivot `Point a verifier` plutot qu'un ecran Audit360 autonome.
- Impact tres fort: afficher `Impact propose` puis `Validation humaine requise` pour toute levee, levee partielle ou criticite relevee.
- Impact fort: remplacer `aggravation` au premier niveau par `criticite relevee` ou `risque reevalue`.
- Impact fort: montrer `ce que l'on sait`, `ce qui manque`, `ce qui a change`, `prochaine action`.
- Impact fort: garder une timeline probatoire courte et lisible.
- Impact moyen: proposer une vue document-first pour les lots DocOps.
- Impact moyen: reserver le cockpit dense aux experts et aux traitements par lots.

## Images retenues

| Image | Statut | Intention | Decision |
|---|---|---|---|
| `docs/assets/ux-ui-recherche-2026-05-24-audit360-anomalies/audit360_anomalies_atelier_blueprint.svg` | Retenue | Blueprint de l'atelier anomalies: file, fiche pivot, nouveau document, validation humaine et timeline. | Retenue comme image de decision, a tester avant tout dev. |

Prompt prioritaire propose par le designer:

```text
High-fidelity French SaaS product UI mockup for "CoproScope Audit360 - Anomalies", desktop 1440x960. Three-column workbench: left anomaly queue, center active anomaly review, right new document impact panel, bottom evidence timeline. Use only synthetic labels: "Preuve attendue", "Levee candidate - validation humaine requise", "Aggravation candidate", "Demander avis". No real names, no addresses, no amounts, no file paths, no document preview, no raw OCR. Restrained professional palette: neutral background, charcoal text, amber warning, teal proof, red aggravation, green lifted state. Status must use text plus icon, not color only.
```

## Retours du Testeur metier expert

Verdict: NO-GO metier pour une livraison en l'etat, GO conditionnel pour continuer la recherche UX.

Corrections P0:

- Remplacer toute logique `document recu = anomalie levee` par `impact propose`.
- Ne pas afficher `Levee` sans validateur humain, date, source, perimetre couvert et reserve eventuelle.
- Preferer `Levee proposee`, `Levee validee`, `Levee partielle`, `Non levee`, `Cloturee avec reserve`.
- Renommer `aggravation` en premier niveau en `criticite relevee` ou `risque reevalue`.
- Separer anomalie de piece, controle comptable, point AG/gouvernance et risque juridique.
- Toute preuve doit dire preuve de quoi: montant, date, decision AG, execution, reception travaux, relance, consultation ou identite fournisseur.
- Les actions restent humaines: preparer question syndic, demander piece, rattacher reponse recue, valider avec reserve, ajouter au rapport AG.

Cas limites a couvrir:

- document contradictoire;
- preuve partielle ou restriction de diffusion;
- facture, avoir, devis, bon de commande, contrat et PV AG non equivalents;
- document rattache au mauvais exercice ou fournisseur;
- reponse syndic hors outil;
- document posterieur a l'AG;
- donnees individuelles, impayes, contentieux ou lots nominatifs;
- base juridique suggeree par IA, toujours a verifier.

## Retours accessibilite / novice

Le thread dedie n'a pas pu etre ouvert, faute de capacite de threads. L'orchestrateur reprend donc le test novice minimal.

Verdict novice: GO de comprehension seulement si le premier ecran evite les mots `Audit360`, `aggravation`, `levée` non expliquee et `P1/P2` non traduit. NO-GO si l'utilisateur voit d'abord un tableau, un score IA ou un verdict automatique.

Libelles preferables:

- `Point a verifier`
- `Ce document change quoi ?`
- `Preuve candidate recue`
- `Validation humaine requise`
- `Risque reevalue`
- `Reste a verifier`
- `OK avec preuve locale`
- `Cloture avec reserve`

Blocages probables:

- `Levee candidate` peut etre compris comme deja regle; ajouter `a valider`.
- `Aggravation` parait accusatoire; preferer `criticite relevee`.
- `Preuve` parait definitive; preferer `preuve candidate` tant que l'humain n'a pas valide.
- Une timeline trop detaillee doit rester lisible: garder cinq etapes maximum au premier niveau.

## Decisions prises

- La direction retenue est l'atelier de reprise par fiche pivot, pas un dashboard de scores.
- La vue principale part d'une anomalie ou d'un point a verifier; la vue document-first reste une variante DocOps.
- Le vocabulaire d'etat doit distinguer priorite, cycle de vie et diffusion/confiance.
- Toute levee ou criticite relevee demande une validation humaine avec motif.
- L'historique avant/apres est obligatoire pour la credibilite probatoire.
- Aucun code n'a ete produit et aucun chantier dev n'est ouvert par cette recherche.

## Questions ouvertes

- Qui peut valider une levee: referent CS, president CS, syndic, AG ou simple note interne?
- Quels etats doivent rester visibles au novice et lesquels doivent etre replies en detail?
- Quelle preuve minimale permet de passer de `preuve candidate` a `preuve validee` selon la famille d'anomalie?
- Les rapports AG doivent-ils inclure les levees avec reserve ou seulement les points ouverts?
- Faut-il un statut separe `a soumettre au syndic` quand le CS ne peut pas conclure seul?
- Faut-il afficher un niveau de confiance chiffre, ou seulement `a verifier humainement`?

## BOT-END

```text
BOT-END - Orchestrateur UX/UI - 2026-05-24 04:11 +02:00
Roadmap: RM-2026-0008
Chantier: CH-20260524-033000-RM-2026-0008-audit360-anomalies-ux
Conversation: CONV-2026-1325
Statut: CLOTURE
Fichiers modifies: docs/recherche_ux_ui_2026-05-24_audit360-anomalies.md; docs/assets/ux-ui-recherche-2026-05-24-audit360-anomalies/audit360_anomalies_atelier_blueprint.svg; docs/presence_agents.md; docs/roadmap_backlog_central.md.
Fichiers volontairement evites: code applicatif, tests, instances privees, secrets, exports bruts, passerelles hors mission, RM-2026-0017 bloque.
Tests/preuves: contributions chercheur, architecte UX, designer UI, testeur metier; test novice repris par orchestrateur; blueprint SVG archive; aucune execution applicative requise.
Limites: pas de validation juridique, comptable ou AG; pas de test sur UI reelle; aucun bitmap genere; thread novice dedie bloque par limite de threads.
Questions ouvertes: role de validation, preuve minimale par famille, etats visibles au novice, statut a soumettre au syndic.
Prochain mouvement propose: si Brice valide la direction, ouvrir un chantier dev separe pour une fiche pivot `Point a verifier` sur donnees fictives ou instance de test.
```

UXUI-DONE - equipe UX/UI a fini son job
