# Recherche UX/UI - Audit360 anomalies approfondissement

Date de lancement: 2026-05-24 09:39 +02:00.
Mode: equipe UX/UI recherche visuelle sans dev.

## BOT-START

```text
BOT-START - Orchestrateur UX/UI - 2026-05-24 09:39 +02:00
Roadmap: RM-2026-0008 principal; liens RM-2026-0003, RM-2026-0006, RM-2026-0010, RM-2026-0016, RM-2026-0029, RM-2026-0030. RM-2026-0017 reste bloque et n'est pas relance.
Chantier: CH-20260524-093955-RM-2026-0008-audit360-anomalies-approfondissement
Conversation: CONV-2026-1410
Role: Orchestrateur UX/UI
Mission: approfondir la recherche UX/UI Audit360/anomalies apres le premier run cloture, en travaillant sur les cas limites, les preuves minimales, la validation humaine, les impacts proposes par nouveaux documents et la lisibilite novice.
Ownership modifiable: docs/recherche_ux_ui_2026-05-24_audit360-anomalies_approfondissement.md; docs/assets/ux-ui-recherche-2026-05-24-audit360-anomalies-approfondissement/; docs/presence_agents.md; trace append-only de docs/roadmap_backlog_central.md.
Fichiers a eviter: code applicatif, tests, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, serveurs locaux, ancien livrable cloture sauf reference, chantier reconstruction bloque RM-2026-0017.
Passerelle/registre de trace: ce document et docs/presence_agents.md.
Dernier point lu: AGENTS.md; docs/orchestration_agents.md; docs/protocole_equipe_ux_ui_recherche.md; docs/protocole_roadmap_presence_agents.md; docs/consignes_bots_interconversations.md; docs/roadmap_backlog_central.md; docs/presence_agents.md; docs/coordination_interconversations_2026-05-21.md; docs/point_coordination_live_8766_2026-05-21.md; docs/recherche_ux_ui_2026-05-24_audit360-anomalies.md.
Tests/preuves attendus: synthese multi-roles, approfondissement des familles d'anomalies et preuves minimales, wireflow ou blueprint de decision, retours metier et novice, images candidates utiles a decision, mention explicite qu'aucun code n'a ete produit.
Risque de collision: ancien run Audit360/anomalies est cloture avec UXUI-DONE; ce run est separe. Equipes UX/UI ajout-docs, alertes, gouvernance, travaux et comptes-sync restent separees. Ne pas dupliquer un role vivant d'un autre chantier.
Lease ownership: jusqu'au 2026-05-25 09:39 +02:00.
Prochaine action: lancer les roles UX/UI en lecture/recherche, puis consolider le point d'approfondissement.
```

## Pourquoi un second run

Le premier run a tranche la direction generale: fiche pivot `Point a verifier`,
impact propose par les nouveaux documents, validation humaine obligatoire et
timeline probatoire. Ce second run ne rouvre pas ces decisions comme si elles
etaient vierges. Il les approfondit pour rendre la suite plus robuste avant
tout chantier dev separe.

## Objectif d'approfondissement

- Clarifier les familles d'anomalies et la preuve minimale attendue pour chacune.
- Distinguer les impacts de documents: preuve candidate, preuve validee, levee proposee, levee partielle, criticite relevee, conflit, hors sujet et surveillance.
- Preciser le role de l'automatisation locale ou de l'IA: suggerer, classer, comparer, jamais conclure seule.
- Definir la validation humaine: qui valide quoi, avec quel motif, quelle reserve et quelle trace.
- Tester la comprehension novice du vocabulaire `Point a verifier`, `ce document change quoi`, `preuve candidate`, `a valider`, `reste a verifier`.
- Produire ou selectionner une image/blueprint utile a la decision d'ecran suivant.

## Sources de depart

- `docs/recherche_ux_ui_2026-05-24_audit360-anomalies.md`
- `docs/assets/ux-ui-recherche-2026-05-24-audit360-anomalies/audit360_anomalies_atelier_blueprint.svg`
- `docs/audit360.md`
- `docs/commande_cycle9_module_audit_boite_reprise_probatoire.md`
- `docs/factureops.md`
- `docs/fonctions_cibles.md`
- `docs/architecture_et_flux.md`
- `docs/indicateurs_pilotage_copro.md`
- `docs/roadmap_backlog_central.md`
- `docs/presence_agents.md`

## Roles actifs

| Conversation | Role | Mission | Statut |
|---|---|---|---|
| `CONV-2026-1410` | Orchestrateur UX/UI | Cadre, relance, consolide et livre la synthese d'approfondissement. | En cours |
| `CONV-2026-1411` | Chercheur utilisateur | Approfondir profils, moments de decision, objections et criteres de reussite. | Termine - agent Peirce `019e58ef-3b04-7d72-a52b-f16310ba3364` |
| `CONV-2026-1412` | Architecte UX | Approfondir familles d'anomalies, etats, transitions et wireflow decisionnel. | Termine - agent Lagrange `019e58ef-3c9d-7061-bb09-393b1b3c9d4b` |
| `CONV-2026-1413` | Designer UI / generateur visuel | Proposer image/blueprint et microcopy pour le flux `nouveau document -> impact propose`. | Termine - agent Mendel `019e58ef-3d77-71d2-b97a-dc5ed1cd12c5` |
| `CONV-2026-1414` | Testeur metier expert | Challenger preuve minimale, validation, reserves, cas limites et vocabulaire audit/copro. | Termine - agent Zeno `019e58ef-3ed4-71d2-8d7d-3fac8df06d70` |
| `CONV-2026-1415` | Testeur accessibilite / novice | Tester comprehension immediate, charge cognitive, mobile et libelles non anxiogenes. | Repris par l'orchestrateur apres limite de threads |

## Questions a approfondir

- Quelle preuve minimale permet de passer de `preuve candidate` a `preuve validee` selon la famille d'anomalie?
- Qui peut valider une levee, une levee partielle, une reserve ou une criticite relevee?
- Comment montrer un conflit de sources sans faire paniquer ni accuser?
- Comment presenter le role de l'IA ou de l'automatisation locale sans effet de verdict automatique?
- Quel est le premier ecran utile: file d'anomalies, fiche active, panneau nouveau document ou timeline?
- Quelles informations doivent rester repliees pour un novice mais accessibles a un referent avance?

## Contraintes non negociables

- Aucun code, route, template, test applicatif, serveur local ou instance privee n'est modifie.
- Aucune donnee brute, chemin local, source nominative, secret, log ou export prive n'est copie dans le livrable.
- L'IA ou l'automatisation ne leve ni n'aggrave une anomalie toute seule.
- Toute decision d'etat conserve l'avant/apres, la source, le validateur humain, le motif et la reserve eventuelle.
- Le run s'arrete seulement avec le marqueur final `UXUI-DONE - equipe UX/UI a fini son job`.

## Point initial - 2026-05-24 09:39 +02:00

- A produire: retours des quatre agents lances, reprise du test accessibilite/novice bloque par limite de threads, carte des familles d'anomalies, matrice preuve minimale / validation / reserve, blueprint ou image candidate.
- En test: aucun ecran reel ni serveur; recherche documentaire uniquement.
- Images candidates: blueprint precedent a reprendre comme base; nouvelle image ou annotation attendue si elle aide a trancher.
- Decisions ouvertes: preuve minimale par famille; validateur humain; niveau de detail visible au novice; traitement des conflits de sources; statut `a soumettre au syndic`.
- Prochain mouvement: attendre les quatre retours agents, reprendre le test novice si la limite de threads persiste, puis consolider le premier point de relance.

## A completer par l'equipe

- Retours du Chercheur utilisateur.
- Retours de l'Architecte UX.
- Images candidates et decision Designer UI.
- Retours du Testeur metier expert.
- Retours du Testeur accessibilite / novice.
- Decisions d'approfondissement.
- Questions ouvertes restantes.

## Retours du Chercheur utilisateur

Profils prioritaires:

- Membre CS novice: veut savoir si le point est regle, a surveiller ou a demander au syndic, sans conclure ni accuser trop vite.
- Referent CS avance: arbitre les preuves, prepare questions, reserves et points AG; il a besoin d'un avant/apres defensible.
- Responsable preuve/action: rattache documents, reponses, relances et decisions; il doit savoir preuve de quoi, periode, limite et source.
- Relecteur diffusion/confidentialite: verifie qu'un statut partageable ne revele pas une piece restreinte.
- Preparateur rapport/AG: transforme les points ouverts, regles avec reserve ou sous surveillance en synthese comprehensible.

Scenarios critiques:

| Scenario | Risque UX | Reussite attendue |
|---|---|---|
| Nouveau document propose une levee | Croire que l'IA a clos le point | Afficher `Levee proposee, validation humaine requise`, source, perimetre, boutons valider/refuser |
| Nouveau document ne couvre qu'une partie | Transformer une preuve partielle en cloture | Statut `En partie regle`, bloc `reste a verifier`, prochaine action obligatoire |
| Nouveau document releve la criticite | Ton accusatoire ou panique | Dire `Risque reevalue`, expliquer ce qui a change, proposer demande de confirmation |
| Nouveau document contredit une source | L'utilisateur ne sait plus quoi croire | Statut `Documents contradictoires`, deux sources conservees, validation humaine |
| Nouveau document impose une surveillance | Point oublie ou fausse cloture | Statut `A suivre jusqu'au...`, responsable, echeance et preuve attendue |

Criteres de reussite:

- En 30 secondes, un novice comprend le statut, la raison, la preuve, la limite et la prochaine action.
- Aucun document ne change seul l'etat final d'un point.
- Toute levee, levee partielle ou criticite relevee affiche validateur humain, date, source, motif et reserve eventuelle.
- Chaque preuve dit explicitement `preuve de quoi`.
- L'avant/apres reste visible sans effacer l'etat precedent.
- Un point non clos a toujours une prochaine action ou une date de surveillance.

## Retours de l'Architecte UX

Familles d'anomalies a distinguer:

| Famille | Lecture utilisateur | Preuve minimale attendue | Impacts possibles |
|---|---|---|---|
| Piece attendue manquante ou inexploitable | Il manque une preuve lisible | Document identifie, periode, objet, source, lisibilite | Preuve candidate, hors sujet, doublon, preuve partielle |
| Facture ou piece comptable a consolider | La piece ne suffit pas encore a prouver le flux | Fournisseur, date, montant, exercice, coherence HT/TVA/TTC, non-doublon | Preuve validable, conflit, criticite relevee, rattachement a verifier |
| Rapprochement comptable ou budgetaire | Montant ou imputation a controler | Etat de depense, facture, budget ou decision de reference nommes ensemble | Levee proposee, non levee, levee partielle, question syndic |
| Decision, action ou preuve de suivi | Decision ou demande existe, preuve d'execution manque | Decision source, responsable, echeance, action attendue, preuve de cloture | Action ouverte, preuve candidate, cloture avec reserve |
| Contrat, prestation ou execution | Service rendu a rapprocher du contrat ou terrain | Contrat/devis, periode, obligation, facture ou preuve d'execution | Surveillance, criticite relevee, preuve partielle |
| Confidentialite ou diffusion bloquante | Preuve existe peut-etre, pas montrable telle quelle | Niveau d'acces, restriction, transformation attendue, version diffusable | Validation restreinte, demande de biffage, blocage diffusion |
| Chronologie, conflit ou doublon | Deux sources ne disent pas la meme chose | Sources datees, perimetre compare, raison du conflit | Conflit de sources, doublon, mauvais exercice, revue humaine requise |

Cycle de vie retenu:

`Signal detecte -> A qualifier -> Point qualifie -> Action ouverte / Preuve attendue -> Preuve candidate recue -> Impact propose -> Revue humaine requise -> Levee validee / Levee partielle / Non levee / Criticite relevee / Conflit de sources / Surveillance`.

Regle d'architecture: priorite, cycle de vie et diffusion/confiance restent trois dimensions separees. La priorite parle d'urgence, le cycle de vie parle de decision, la diffusion parle de ce qui peut etre partage.

Wireflow:

1. L'utilisateur arrive depuis cockpit, comptes, documents ou actions sur une fiche `Point a verifier`.
2. La fiche affiche ce qui est constate, pourquoi cela compte, preuve actuelle, preuve attendue et prochaine action.
3. Un nouveau document arrive ou est rattache.
4. CoproScope affiche `Ce document change quoi ?` avec un impact propose, pas une decision.
5. L'utilisateur confirme, corrige, refuse, rattache sans conclure, demande avis ou soumet au syndic.
6. Si l'impact touche une levee, une levee partielle ou une criticite relevee, la validation demande validateur, motif, reserve eventuelle et prochaine action.
7. La fiche met a jour l'etat visible mais conserve l'avant/apres.

## Images candidates et decision Designer UI

| Image | Statut | Intention | Decision |
|---|---|---|---|
| `docs/assets/ux-ui-recherche-2026-05-24-audit360-anomalies-approfondissement/audit360_anomalies_decision_blueprint.svg` | Retenue | Blueprint centre sur `nouveau document -> impact propose -> validation humaine -> timeline probatoire`. | Retenue comme image de decision pour l'approfondissement; le blueprint precedent reste reference d'architecture globale. |

Prompt si une image haute fidelite est generee plus tard:

```text
High-fidelity French SaaS product UI mockup for "CoproScope - Point a verifier", desktop 1440x960. Focus on the workflow "Nouveau document -> Impact propose -> Validation humaine -> Timeline probatoire". Professional restrained interface, neutral background, clear hierarchy, no decorative hero.

Layout: left queue "Points a verifier"; center active "Point a verifier" with "Pourquoi cela compte", "Ce que l'on sait", "Ce qui manque", "Etat actuel"; right decision drawer "Nouveau document recu" and "Ce document change quoi ?" with fields "Preuve de quoi ?", "Limite constatee", "Validateur humain", "Motif obligatoire", "Reserve eventuelle"; bottom timeline with five steps max: "Signal detecte", "Preuve attendue", "Document recu", "Decision humaine", "Suivi".

Use only synthetic labels. No real names, no addresses, no file paths, no OCR preview, no private amounts. Status must use text plus icon, not color only. Avoid "verdict IA", "levee automatique" and "aggravation".
```

Microcopy retenue:

- `Ce document change quoi ?`
- `Impact propose, a valider`
- `Preuve candidate recue`
- `Le document semble couvrir une partie du point, mais ne le clot pas seul.`
- `Validation humaine requise`
- `Preuve de quoi exactement ?`
- `Ajouter un motif`
- `Ajouter une reserve`
- `Valider avec reserve`, `Corriger l'impact`, `Refuser le lien`, `Demander une piece`

## Retours du Testeur metier expert

Verdict: GO recherche, mais NO-GO pour figer une commande dev tant que la matrice preuve minimale / validateur / reserve n'est pas integree.

Corrections P0:

- Remplacer `anomalie` par `point a verifier` tant que la qualification humaine n'est pas faite.
- Interdire tout etat `levee` sans source datee, perimetre couvert, validateur humain, motif et reserve eventuelle.
- Ajouter `conflit de sources` quand deux pieces ne racontent pas la meme chose.
- Distinguer `preuve candidate`, `preuve suffisante pour suivi local`, `preuve opposable a verifier`, `preuve officielle`.
- Ne pas laisser un membre CS valider seul ce qui releve du syndic, d'un PV d'AG, d'un professionnel ou d'une appreciation juridique.
- Afficher une reserve obligatoire des qu'une preuve est partielle, tardive, non officielle, restreinte ou contradictoire.

Matrice metier minimale:

| Famille | Preuve minimale | Validateur | Reserve type |
|---|---|---|---|
| Piece manquante ou incomplete | Document identifie, date, lisible, rattache au bon exercice | Referent CS documentaire | Piece recue, contenu non analyse |
| Facture suspecte ou incomplete | Facture complete: fournisseur, date, numero, TTC, objet, periode | Referent compta CS, puis syndic si impact comptes | Extraction automatique a confirmer |
| Ecart facture / etat depenses | Facture + ligne comptable + exercice + montant rapproche | Referent compta CS ou syndic | Rapprochement local, comptabilite officielle a confirmer |
| Budget, appels, fonds travaux | Annexe comptable ou appel officiel + exercice + cle concernee | Syndic ou document AG officiel | Impact lot/tantiemes non recalcule |
| Contrat ou prestation | Contrat/avenant + facture ou preuve de passage/execution | Referent CS, syndic si obligation contractuelle | Execution constatee partiellement |
| Travaux | PV AG/devis accepte + facture + preuve d'execution/reception | CS pour suivi, syndic/maitrise d'oeuvre selon sujet | Reception ou reserves non soldees |
| Decision AG / gouvernance | Convocation, resolution, PV ou notification officielle | AG/PV, pas l'IA | Interpretation a verifier |
| Demande syndic / relance | Message envoye + accuse/reponse + date + objet | Referent CS relation syndic | Reponse hors outil ou incomplete |
| Confidentialite / diffusion | Screening PrivacyOps + biffage ou version diffusable | Relecteur confidentialite humain | Diffusable seulement apres masquage |
| Contentieux, impayes, donnees nominatives | Piece restreinte identifiee, sans exposition publique | Revue humaine restreinte, avis competent si besoin | Ne pas diffuser, qualification non juridique |

## Retours accessibilite / novice

Le thread dedie n'a pas pu etre ouvert, faute de capacite de threads. L'orchestrateur reprend donc le test novice.

Test 30 secondes:

- GO si l'ecran commence par `Point a verifier`, `Validation humaine requise`, `Ce document change quoi ?`, `Preuve de quoi ?` et une prochaine action.
- NO-GO si l'utilisateur voit d'abord `Audit360`, `P1/P2`, `aggravation`, un score IA ou un tableau dense.
- GO si le document est presente comme une aide a decider, pas comme une decision.
- NO-GO si `Levee proposee` apparait sans `a valider`, validateur, motif et reserve.

Ordre mobile recommande:

1. Statut humain: `Validation humaine requise`.
2. Phrase courte: `Ce document peut aider, mais ne clot pas le point seul.`
3. `Ce que l'on sait`.
4. `Ce qui manque`.
5. `Ce document change quoi ?`
6. Choix: valider avec reserve, corriger, refuser, demander une piece.
7. Timeline repliee a cinq evenements maximum.

Libelles preferables:

- `Document qui peut aider` au lieu de `preuve candidate` pour le premier niveau novice.
- `Peut etre regle, a valider` au lieu de `levee candidate`.
- `En partie regle` au lieu de `levee partielle`.
- `Documents qui ne disent pas la meme chose` au lieu de `conflit de sources` en premier niveau.
- `A suivre jusqu'au...` au lieu de `surveillance`.

## Decisions d'approfondissement

- Le produit doit raisonner par familles d'anomalies; aucune preuve minimale unique n'est acceptable.
- Le premier ecran reste une fiche `Point a verifier`, pas un tableau Audit360.
- Le flux critique est `nouveau document -> impact propose -> validation humaine -> historique avant/apres`.
- `Conflit de sources` devient un etat explicite, neutre, non accusatoire.
- `A soumettre au syndic` doit rester une option visible quand le CS ne peut pas conclure seul.
- Les reserves deviennent obligatoires pour preuves partielles, tardives, non officielles, restreintes ou contradictoires.
- Le blueprint decisionnel ajoute dans ce run devient l'image retenue pour l'approfondissement.
- Aucun code applicatif, serveur, test applicatif ou instance privee n'a ete modifie.

## Questions ouvertes restantes

- Qui valide selon chaque famille: referent CS, president CS, syndic, AG, expert, avocat ou revue interne?
- Faut-il un statut separe `preuve suffisante pour suivi CS` distinct de `preuve officielle`?
- Les points leves avec reserve doivent-ils apparaitre dans le rapport AG ou seulement dans l'historique interne?
- Comment afficher un statut partageable quand la preuve source est restreinte?
- Quand un point `regle avec preuve` doit-il etre rouvert?
- Comment gerer un document qui impacte plusieurs points a la fois?

## BOT-END

```text
BOT-END - Orchestrateur UX/UI - 2026-05-24 09:45 +02:00
Roadmap: RM-2026-0008
Chantier: CH-20260524-093955-RM-2026-0008-audit360-anomalies-approfondissement
Conversation: CONV-2026-1410
Statut: CLOTURE
Fichiers modifies: docs/recherche_ux_ui_2026-05-24_audit360-anomalies_approfondissement.md; docs/assets/ux-ui-recherche-2026-05-24-audit360-anomalies-approfondissement/audit360_anomalies_decision_blueprint.svg; docs/presence_agents.md; docs/roadmap_backlog_central.md.
Fichiers volontairement evites: code applicatif, tests applicatifs, instances privees, secrets, exports bruts, passerelles hors mission, serveurs locaux, RM-2026-0017 bloque.
Tests/preuves: retours chercheur utilisateur, architecte UX, designer UI et testeur metier; test novice repris par orchestrateur; blueprint SVG archive; aucune execution applicative requise.
Limites: pas de validation juridique, comptable ou AG; pas de test sur UI reelle; pas de bitmap genere; thread novice dedie bloque par limite de threads.
Questions ouvertes: autorites de validation par famille, preuve CS vs preuve officielle, rapport AG des levees avec reserve, statut partageable si source restreinte, reouverture, documents multi-points.
Prochain mouvement propose: si Brice valide cet approfondissement, ouvrir un chantier dev separe pour une fiche `Point a verifier` sur donnees fictives ou instance de test.
```

UXUI-DONE - equipe UX/UI a fini son job
