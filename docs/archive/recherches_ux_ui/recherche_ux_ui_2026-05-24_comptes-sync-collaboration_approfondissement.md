# Recherche UX/UI - Comptes, synchronisation et collaboration - approfondissement

Date: 2026-05-24 09:45 +02:00
Roadmap: `RM-2026-0033`
Chantier: `CH-20260524-094556-RM-2026-0033-comptes-sync-approfondissement`
Conversation coordinatrice: `CONV-2026-1506`
Statut: `EN_COURS`

## BOT-START - Orchestrateur UX/UI - 2026-05-24 09:45 +02:00

Roadmap: `RM-2026-0033`

Chantier: `CH-20260524-094556-RM-2026-0033-comptes-sync-approfondissement`

Conversation: `CONV-2026-1506`

Role: Orchestrateur UX/UI.

Mission: relancer l'equipe UX/UI pour approfondir la recherche deja cloturee sur la gestion des comptes, la synchronisation et la collaboration. Le point de depart est le MVP recommande `Centre de confiance du coffre`; cette iteration doit preciser les decisions utilisateur, les limites de promesse, les parcours d'invitation, de roles, d'appareils, de recuperation et de revocation.

Ownership modifiable: ce fichier, `docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration-approfondissement/`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.

Fichiers a eviter: code applicatif, routes, templates, CSS, tests, serveurs locaux, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, donnees reelles et tout chantier `RM-2026-0017` bloque.

Passerelle/registre de trace: ce fichier de mission, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.

Dernier point lu: `AGENTS.md`, `docs/orchestration_agents.md`, `docs/protocole_equipe_ux_ui_recherche.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/consignes_bots_interconversations.md`, `docs/presence_agents.md` et `docs/roadmap_backlog_central.md` au 2026-05-24 09:45 +02:00.

Tests/preuves attendus: pas de test applicatif; preuve documentaire par mission, roles actifs, heartbeat 10 minutes, absence de `UXUI-DONE` tant que l'approfondissement n'est pas consolide, puis `git diff --check` sur les docs touchees.

Risque de collision: conversations `CONV-2026-1396`..`CONV-2026-1401`, `CONV-2026-1410`..`CONV-2026-1415` et `CONV-2026-1500`..`CONV-2026-1505` deja vivantes sur d'autres approfondissements UX/UI; cette mission reserve `CONV-2026-1506`..`CONV-2026-1511`.

Lease ownership: 24 heures, expiration 2026-05-25 09:45 +02:00.

Prochaine action: lancer cinq roles en lecture seule et consolider leurs retours dans cette mission.

## Source de depart

Recherche precedente: `docs/recherche_ux_ui_2026-05-24_comptes-sync-collaboration.md`.

Decision precedente: retenir le `Centre de confiance du coffre`, separer coffre local, transport Drive, membre, role et appareil, et traiter `Assistant prudent de partage` comme flux secondaire.

Cette iteration ne rouvre pas le resultat deja marque `UXUI-DONE`. Elle approfondit les zones encore trop implicites avant toute future commande dev.

## Questions d'approfondissement

1. Comment expliquer a un novice la difference entre le coffre local, le compte cloud de transport, les membres, les roles et les appareils sans jargon technique ?
2. Quel parcours exact precede l'invitation d'un membre: choix de la personne, justification, role, duree, appareil, recuperation, avertissement et trace ?
3. Comment afficher une revocation honnete: bloquer les futurs acces et les nouvelles synchronisations, sans promettre de supprimer les copies deja obtenues ?
4. Comment prevoir une recuperation sans creer un super-admin implicite ou un pouvoir cache de confiscation ?
5. Quels mots remplacer pour eviter `sync`, `vault`, `OAuth`, `scope`, `token`, `admin`, `device` au premier niveau ?
6. Quelle image cible permet de montrer le modele mental avant dev: coffre, transport, membres, roles, appareils, alertes et limites ?

## Roles actifs

| Conversation | Role | Attendu |
|---|---|---|
| `CONV-2026-1507` | Chercheur utilisateur | Besoins, moments de doute, scenarios d'invitation, depart, recuperation et collaboration. |
| `CONV-2026-1508` | Architecte UX | Parcours, etats, wireflow, priorites d'information et regles de decision. |
| `CONV-2026-1509` | Designer UI / generateur visuel | Direction visuelle et, si utile, blueprint du `Centre de confiance du coffre` approfondi. |
| `CONV-2026-1510` | Testeur metier expert | Challenge securite, responsabilite, copropriete, revocation, preuve et limites de promesse. |
| `CONV-2026-1511` | Testeur accessibilite / novice | Test comprehension immediate, vocabulaire, charge cognitive, mobile et microcopy. |

## A produire

- Parcours principal approfondi: comprendre l'etat du coffre, inviter, modifier un role, retirer un acces, changer d'appareil, gerer un depart, recuperer l'acces.
- Matrice novice: termes interdits au premier niveau, termes autorises, aide progressive.
- Etats critiques: seul utilisateur, plusieurs membres, appareil inconnu, compte cloud deconnecte, conflit de version, invitation en attente, membre retire, recuperation demandee.
- Limites affichees: ce que CoproScope sait prouver, ce qu'il ne peut pas promettre, ce qui depend du compte cloud ou des copies deja partagees.
- Image ou blueprint utile a decision, conserve seulement si elle apprend quelque chose.

## Synthese intermediaire - 2026-05-24 09:50 +02:00

Les cinq roles confirment que l'ecran ne doit pas etre une page `Comptes`. La direction produit devient `Coffre et partage`, avec `Centre de confiance du coffre` comme nom interne de cadrage.

Modele mental a montrer en premier:

1. Le coffre local fait foi.
2. Le cloud transporte seulement une version chiffree.
3. Les personnes ont des capacites CoproScope concretes.
4. Les postes autorises participent au coffre.

Action principale tant que l'etat n'est pas clair: `Verifier avant partage`. Le bouton d'invitation doit rester bloque tant que la verification anti-fuite, les droits et les limites ne sont pas relus.

## Profils et moments de doute

Profils prioritaires:

- President ou secretaire du conseil syndical, responsable des invitations, departs et traces.
- Membre novice du conseil syndical, qui veut participer sans diffuser par erreur.
- Syndic benevole ou autogestion, qui veut une memoire commune transmissible.
- Expert externe ponctuel, avec acces limite dans le temps et le perimetre.
- Nouveau membre en passation, qui doit comprendre ce qui existe et ce qu'il peut reprendre.
- Gardien de recuperation, qui aide sans devenir proprietaire cache.
- Coproprietaire lecteur, qui consulte sans administrer.

Moments de doute a traiter:

- Suis-je sur mon ordinateur, dans le cloud ou dans un espace partage ?
- Qu'est-ce qui part reellement en ligne ?
- Est-ce que j'invite une personne, un compte cloud ou un poste ?
- Que pourra cette personne lire, ajouter, valider, exporter ou recuperer ?
- Quelle version fait foi si deux postes divergent ?
- Que garde un ancien membre apres retrait ?
- Qui peut recuperer le coffre et avec quelles limites ?

## Parcours recommande

1. Arriver dans `Coffre et partage`.
2. Lire le statut global: local, transport cloud, personnes, postes, alertes.
3. Verifier avant toute action sensible.
4. Choisir une action prudente: inviter, modifier les capacites, retirer un acces, autoriser un poste, gerer un depart ou demander une recuperation.
5. Relire les consequences concretes.
6. Produire une trace: qui, quoi, quand, effet exact et limite eventuelle.

Invitation prudente:

1. Choisir la personne.
2. Dire pourquoi elle accede au coffre.
3. Choisir ce qu'elle peut lire.
4. Choisir ce qu'elle peut faire: lire, ajouter, valider, exporter, recuperer.
5. Fixer duree, perimetre et poste si necessaire.
6. Afficher un resume lisible.
7. Bloquer l'envoi tant que le coffre n'est pas verifie.

Retrait d'acces:

1. Expliquer l'effet reel.
2. Bloquer les futurs acces.
3. Retirer la personne des prochaines versions.
4. Dire clairement que les copies deja obtenues ne sont pas effacees.
5. Tracer la decision.

Recuperation:

1. Expliquer le motif.
2. Identifier les personnes ou preuves necessaires.
3. Valider sans creer de super-admin cache.
4. Restaurer un acces limite.
5. Tracer la recuperation.

## Etats critiques

- `Local seul`: le coffre existe ici, rien n'est pret pour le partage.
- `Transport non connecte`: aucun compte cloud n'est associe.
- `Transport connecte mais non verifie`: action principale = verifier.
- `Coffre verifie`: invitation possible, mais seulement apres relecture des droits.
- `Partage bloque`: risque de fichier lisible, conflit, transport ambigu ou poste inconnu.
- `Invitation en brouillon`: aucun envoi.
- `Invitation en attente`: personne invitee, pas encore active.
- `Collaboration active`: personnes, capacites, postes et derniere trace visibles.
- `Poste inconnu`: acces suspendu ou limite jusqu'a confirmation.
- `Compte cloud deconnecte`: le coffre local reste utilisable, le transport est interrompu.
- `Conflit de version`: ne pas inviter ni valider avant resolution.
- `Personne retiree`: acces futur bloque, sans promesse d'effacer les copies deja recues.
- `Recuperation demandee`: parcours separe, justifie et trace.

## Microcopy retenue

- `Ce coffre reste la reference locale.`
- `Google Drive sert seulement a transferer une version chiffree.`
- `Aucun document lisible ne doit partir dans le cloud.`
- `Partage bloque tant que la verification n'est pas terminee.`
- `Choisissez ce que cette personne pourra lire et faire.`
- `Retirer un acces bloque les prochaines versions. Cela ne supprime pas les copies deja obtenues.`
- `Ce poste n'est pas encore reconnu.`
- `La recuperation demande une validation visible, pas un pouvoir cache.`
- `Invitation prete, non envoyee. Relisez les droits avant envoi.`

Mots a eviter au premier niveau: `sync`, `vault`, `OAuth`, `scope`, `token`, `admin`, `device`, `revocation`, `recuperation` sans explication, `synchronise` comme statut rassurant.

## Retours metier et novice

Retour metier: GO recherche conditionnel, NO-GO dev immediat. Les droits CoproScope sont des capacites d'usage, pas des mandats juridiques. Le coffre appartient a la memoire de copropriete, pas au compte individuel. La revocation doit etre honnete: futurs acces bloques, copies deja obtenues non garanties. La recuperation ne doit jamais creer un super-admin implicite.

Retour novice: GO conditionnel pour `Coffre et partage` si le premier ecran montre local, partage et verification, avec invitation bloquee avant controle. NO-GO si l'ecran parle d'abord de compte, de sync, de Drive ou de roles abstraits. Mobile: privilegier une personne ou un poste par bloc, pas de tableau large.

## Blueprint retenu

Image retenue comme blueprint de cadrage:

`docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration-approfondissement/01-coffre-et-partage-approfondissement.svg`

Intention: montrer en moins de 30 secondes ce qui est local, ce qui part dans le cloud, qui peut lire ou agir, pourquoi l'invitation est bloquee et ce que le retrait d'acces promet vraiment.

Statut: `retenue`.

Decision orchestrateur: conserver cette direction comme image cible de recherche. Elle ne vaut pas commande dev; elle sert a stabiliser le modele mental, le vocabulaire et les no-go.

## Questions ouvertes pour la relance 10 minutes

- Faut-il conserver le titre visible `Coffre et partage` ou `Coffre et acces` ?
- Comment nommer le gardien de recuperation sans donner l'impression d'un pouvoir cache ?
- Quels droits minimums doivent etre visibles au premier niveau: lire, ajouter, valider, exporter, recuperer, inviter, retirer ?
- Comment resumer un conflit de version sans afficher de mecanique technique ?
- Quel niveau de trace suffit pour une validation interne CoproScope sans promettre une preuve juridique complete ?

## Point heartbeat - 2026-05-24 10:00 +02:00

A produire: micro-vague lecture seule sur les cinq questions ouvertes.

Images candidates: conserver le blueprint `01-coffre-et-partage-approfondissement.svg`; pas de nouvelle image tant que les libelles et les droits de premier niveau ne sont pas arbitres.

Decisions ouvertes: titre visible, nom du gardien de recuperation, droits exposes en premier niveau, formulation d'un conflit de version, niveau de trace interne.

Prochain mouvement: lancer trois agents lecture seule `CONV-2026-1512`..`CONV-2026-1514`, puis consolider leurs retours dans cette mission au prochain passage ou des que les sorties sont disponibles.

## Consolidation micro-vague - 2026-05-24 10:02 +02:00

Titre visible retenu: `Coffre et partage`.

Raison: `Partage` parle mieux a un novice que `acces`; il pose les questions naturelles: qui voit quoi, qui peut faire quoi, qu'est-ce qui part ou ne part pas. `Coffre et acces` reste un libelle interne possible pour les regles, pas le titre d'ecran.

Nom retenu pour le gardien de recuperation: `Referent de secours`.

Microcopy associee: `Cette personne aide a retrouver l'acces au coffre. Elle ne devient pas proprietaire et ne peut pas agir seule.`

Droits visibles au premier niveau:

- Lire le coffre.
- Ajouter des documents ou notes.
- Valider ou marquer comme verifie.
- Exporter ou sortir des informations du coffre.
- Voir si la personne peut gerer les acces, avec le libelle simple `Peut gerer les acces`.

Droits et reglages en second niveau:

- Inviter quelqu'un.
- Retirer ou bloquer un acces.
- Autoriser un nouveau poste.
- Demander ou valider une recuperation.
- Regler duree, perimetre fin et conditions speciales.
- Details cloud, chiffrement, compte, jeton, appareil et synchronisation.

Parcours de recuperation controle:

1. Entree separee: `Demander une recuperation`.
2. Motif obligatoire: perte de poste, depart, passation ou compte inaccessible.
3. Affichage de ce que la recuperation peut faire: restaurer un acces limite au coffre.
4. Affichage de ce qu'elle ne peut pas faire: prendre le controle, exclure les autres, effacer les copies deja obtenues.
5. Validation visible par personnes ou preuves prevues.
6. Acces restaure d'abord en mode limite: pas d'export, pas d'invitation, pas de retrait avant revalidation.
7. Trace obligatoire: demandeur, motif, validations, date, poste concerne, effet exact et limites.
8. Notification aux membres encore connus si le produit sait le gerer.
9. Retour au regime normal seulement apres verification du coffre et des acces.

Formulation novice du conflit de version:

`Deux versions du coffre existent. Partage bloque : choisissez la version de reference.`

Action sure associee:

- Bloquer le partage et la validation.
- Garder les deux versions.
- Demander a une personne habilitee de comparer, choisir ou reprendre les differences.
- Tracer la decision.

Trace interne suffisante pour un conflit:

- Qui a decide.
- Quand.
- Depuis quel poste.
- Quelles versions etaient en conflit.
- Quelle version a ete retenue.
- Ce qui a ete repris ou ignore.
- Pourquoi.

Limites a ne pas promettre:

- Retrouver automatiquement la vraie version.
- Effacer les copies deja obtenues.
- Prouver juridiquement toute la chaine.
- Garantir que le cloud ou les autres postes sont deja a jour.
- Donner un droit juridique implicite par un role CoproScope.

No-go confirme:

- Pas de role `admin` global.
- Pas de personne pouvant recuperer seule puis retirer les autres.
- Pas de recuperation par simple possession du compte cloud.
- Pas de promesse d'effacement retroactif.
- Pas d'invitation possible tant que coffre, droits, export et limites ne sont pas relus.
- Pas de statut rassurant `synchronise` si le coffre n'est pas verifie ou s'il existe un conflit.

Decisions restantes:

- Faut-il afficher `Peut gerer les acces` comme une pastille visible ou une alerte permanente ?
- Faut-il prevoir une contestation formelle apres notification de recuperation, ou seulement une trace de notification ?
- Le blueprint doit-il etre revise pour remplacer `Coffre et acces` par `Coffre et partage` et ajouter `Referent de secours` ?

## Point heartbeat - 2026-05-24 10:10 +02:00

A produire: micro-vague lecture seule sur les trois arbitrages restants.

Images candidates: reviser le blueprint uniquement si le retour designer confirme que le titre, le referent de secours ou l'affichage des droits changent la comprehension.

Decisions ouvertes: affichage de `Peut gerer les acces`, contestation apres recuperation, revision du blueprint.

Prochain mouvement: lancer `CONV-2026-1515`..`CONV-2026-1517`, consolider leurs sorties, puis decider si la mission peut etre cloturee ou si une derniere relance reste utile.

## Consolidation finale - 2026-05-24 10:14 +02:00

Affichage du droit sensible:

- Decision: afficher `Peut gerer les acces` comme un droit sensible explicite, pas comme alerte permanente.
- Format: ligne de droit dans `Ce que cette personne peut faire`, sous-bloc `Droits sensibles`, avec pastille secondaire `Droit sensible`.
- Aide courte: `Peut inviter, bloquer ou retirer des personnes et autoriser un nouveau poste.`
- Avertissement a la confirmation: `Ce droit change qui peut acceder au coffre. Il ne donne pas de mandat juridique et ne permet pas de recuperer seul le coffre.`
- Resume avant envoi: `Cette personne pourra gerer les acces au coffre. Relisez les droits avant invitation.`
- Dans la liste des membres: pastille sobre `Gere les acces`.
- Alerte en haut seulement en anomalie: aucun gestionnaire d'acces, seul gestionnaire, poste inconnu, conflit de version ou coffre non verifie.

Recuperation contestee:

- Decision: prevoir un signalement produit de recuperation contestee, pas une contestation juridique formelle et pas une simple trace passive.
- Libelle d'etat: `Recuperation a verifier`.
- Libelle action: `Signaler un probleme`.
- Libelle utilisateur: `Je ne reconnais pas cette recuperation`.
- Effet: actions sensibles bloquees jusqu'a revalidation, acces existants conserves autant que possible, trace complete.
- No-go: ne pas appeler cela `recours`, `opposition legale` ou `preuve complete`; ne pas restaurer automatiquement les pleins droits apres notification.

Blueprint:

- Decision: revision ciblee effectuee sur `docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration-approfondissement/01-coffre-et-partage-approfondissement.svg`.
- Changements integres: `Referent de secours`, capacites visibles `Lire`, `Ajouter`, `Valider`, `Exporter`, `Peut gerer les acces`, pastille `Droit sensible`, conflit de version, trace minimale.
- Statut: `retenue`.

## BOT-END - Orchestrateur UX/UI - 2026-05-24 10:14 +02:00

Roadmap: `RM-2026-0033`

Chantier: `CH-20260524-094556-RM-2026-0033-comptes-sync-approfondissement`

Conversation: `CONV-2026-1506`

Statut: `PRET_A_INTEGRER`

Fichiers modifies: `docs/recherche_ux_ui_2026-05-24_comptes-sync-collaboration_approfondissement.md`, `docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration-approfondissement/01-coffre-et-partage-approfondissement.svg`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.

Fichiers volontairement evites: code applicatif, routes, templates, CSS, tests applicatifs, serveurs locaux, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, `RM-2026-0017` bloque.

Tests/preuves: recherche documentaire sans dev; retours des roles integres; blueprint SVG revise; `git diff --check` a lancer sur les docs touchees.

Limites: pas de recette UI reelle, pas de validation juridique, pas de specification technique dev; un futur chantier dev doit reprendre ces decisions en commande separee.

Questions ouvertes: aucune question bloquante pour la recherche UX/UI. Les arbitrages restants deviennent des decisions de futur chantier dev ou produit.

Prochain mouvement propose: si Brice valide, ouvrir un chantier dev separe pour un ecran `Coffre et partage`, sans reutiliser cette equipe de recherche comme owner code.

UXUI-DONE - equipe UX/UI a fini son job

## Cadence

Heartbeat demande: toutes les 10 minutes sur le fil courant.

Regle d'arret: ne stopper la relance que lorsque cette mission contient explicitement le marqueur final du protocole, ajoute dans une future section de cloture.
