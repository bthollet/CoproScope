# Backlog agents continu

> Statut gouvernail: `SOURCE_HISTORIQUE`.
> La source de verite roadmap est `docs/roadmap_backlog_central.md`
> (`RM-2026-0005`). Aucun agent ne prend un lot sans ligne `CH-*` active.

Date de reference: 2026-05-20.

Ce backlog sert a relancer la vague CoproScope sans attendre un jalon horaire.
Il liste des lots terminables sans decision humaine, tant que les agents
respectent les ownerships et les garde-fous de `docs/orchestration_live.md`.

Regle de lecture:

- `PRET` signifie lancable maintenant.
- `RESERVER OWNER` signifie lancable seulement si la zone convergente est libre.
- `ATTENTE` signifie qu'une decision humaine ou une integration precedente est
  necessaire.

## Files actives a maintenir

| File | Etat | Pourquoi elle reste utile |
|---|---|---|
| UX novice et accessibilite | PRET | Elle reduit le risque principal: un conseil syndical comprend mal coffre, depot, preuve ou prochaine action. |
| Atelier piece-point-action-preuve | RESERVER OWNER | C'est le poste de travail qui relie documents, demandes, actions et preuves. |
| Workflow ajout de document | PRET | Le depot doit devenir un parcours local et probatoire, pas un simple upload. |
| Coffre signe anti-confiscation | PRET | La promesse de memoire non confiscable doit etre visible, prudente et testable. |
| Sync transport | PRET | La sync externe doit etre qualifiee comme transport risque, jamais comme garantie cloud. |
| Comptes et commissions | PRET | Les droits et commissions conditionnent la comprehension de qui voit, valide et recupere. |
| Indicateurs | PRET | Le pilotage doit rester rare, sourcie, periodise et actionnable. |
| Suggestions | PRET | Les suggestions doivent aider sans declencher d'effet automatique. |

## Lots prets sans decision humaine

### L1 - UX novice P0

Statut: PRET.

But: rendre les pages principales comprehensibles par un utilisateur non expert.

Ownership conseille:

- `server/src/coproscope/web/templates/_context_banner.html`
- templates pages ciblees, un petit groupe a la fois;
- `server/src/coproscope/web/static/styles.css` seulement pour focus visible,
  labels, captions ou lisibilite.

Hors perimetre:

- schemas metier;
- nouvelles routes;
- refonte graphique globale;
- promesse de signature ou sync finale.

Travail attendu:

- remplacer les fuites de vocabulaire interne dans le texte visible;
- ajouter ou renforcer focus visible, labels, captions, aides courtes;
- montrer clairement depot local, export derive, coffre verifiable, sync
  transport;
- faire apparaitre une prochaine action concrete sur les pages principales.

Validation:

- tests UI statiques existants ou nouveaux selon la page;
- recette clavier courte sur `ui open-test` si l'agent touche l'interface;
- rapport separant tests automatises et recette navigateur.

Definition de fini:

- aucun jargon bloquant sur les surfaces novices touchees;
- aucun texte ne promet cloud, signature finale ou conseil juridique;
- la prochaine action est visible sans lire une documentation externe.

### L2 - Atelier piece-point-action-preuve

Statut: RESERVER OWNER.

But: transformer `/pieces` en file actionnable, pas seulement en recapitulatif.

Ownership conseille:

- `server/src/coproscope/web/templates/pieces.html`;
- `server/tests/test_ui_atelier_piece.py`;
- `server/src/coproscope/web/viewmodel.py` uniquement si l'agent est owner
  unique de cette zone.

Hors perimetre:

- refonte cockpit;
- nouvelles mutations non signees;
- modification des documents originaux;
- changements globaux de navigation.

Travail attendu:

- rendre chaque ligne ouvrable vers document, action, demande ou preuve;
- afficher badge diffusion: brut, apres biffage, reserve, bloque, a arbitrer;
- filtrer par priorite, statut, source, preuve presente et diffusion;
- mettre une action primaire par ligne: demander, verifier, rattacher,
  arbitrer, cloturer;
- garder ensemble les quatre questions: piece, point, action, preuve.

Validation:

- `test_ui_atelier_piece.py`;
- route `/pieces` en 200 avec token;
- controle visuel que les longues preuves ne cassent pas la lecture.

Definition de fini:

- un novice sait quoi faire sur au moins cinq items synthetiques;
- une piece sensible ne peut pas etre interpretee comme diffusable;
- aucune annotation PDF n'est presentee comme modifiant l'original.

### L3 - Workflow ajout de document

Statut: PRET.

But: cadrer et/ou implementer le parcours `depot local -> classification ->
confidentialite -> piece -> point -> action -> preuve`.

Ownership conseille:

- `server/src/coproscope/web/templates/depot.html`;
- tests depot/documents associes;
- `server/src/coproscope/modules/document_intake.py` si le lot reste dans le
  contrat deja existant;
- docs de workflow si le lot est documentaire.

Hors perimetre:

- cloud upload;
- copie de raw dans exports ou dossiers sync;
- annotation PDF comme fonction livree si elle n'existe pas;
- signature finale si elle n'est pas effective.

Travail attendu:

- expliciter depot local, hash/doublon, statut de lecture;
- proposer classification corrigeable et `A_CLASSER`;
- demander confidentialite avant sortie;
- rattacher la piece a point/action/preuve sans duplication physique;
- afficher recapitulatif de fin avec limites: OCR absent, signature non
  verifiee, biffage a produire.

Validation:

- tests depot/documents;
- test documentaire des invariants de `docs/ux_workflow_ajout_document.md`;
- route `/depot` protegee par token.

Definition de fini:

- un document ajoute ne devient jamais automatiquement diffusable;
- le brut reste local;
- le parcours permet `je ne sais pas encore` via classement ou arbitrage.

### L4 - Coffre signe anti-confiscation

Statut: PRET.

But: rendre visible la promesse prudente de coffre verifiable et non
confiscable.

Ownership conseille:

- `server/src/coproscope/vault/resilience.py`;
- `server/src/coproscope/vault/reconstruction_archive.py`;
- tests resilience/reconstruction;
- bandeau ou page gouvernance seulement si l'ownership UI est libre.

Hors perimetre:

- nouveau protocole cryptographique non decide;
- recuperation miracle si toutes les parts sont perdues;
- contournement de restrictions legitimes;
- promesse de lecture complete pour tous.

Travail attendu:

- distinguer archive complete chiffree et corpus lisible autorise;
- exposer existence des objets restreints par hash/manifestes;
- signaler quorum, gardiens, rotation et risque de confiscation;
- journaliser recuperation comme evenement futur/signe ou prototype explicite;
- garder le langage novice `coffre`, pas seulement `vault`.

Validation:

- tests vault resilience/reconstruction;
- verification qu'une suppression d'evenement/blob est detectee;
- verification qu'un lecteur ne lit pas les compartiments non autorises.

Definition de fini:

- la copro peut comprendre ce qui est preservable, verifiable et restreint;
- la recuperation par quorum est visible comme condition, pas garantie absolue.

### L5 - Sync transport

Statut: PRET.

But: classer la synchronisation comme transport local a risque et declencher les
actions prudentes.

Ownership conseille:

- `server/src/coproscope/vault/sync_profiles.py`;
- `server/src/coproscope/vault/sync_alerts.py`;
- `server/src/coproscope/vault/notifications.py`;
- tests sync profiles/alerts/notifications.

Hors perimetre:

- scan de processus, ports ou fournisseurs en direct;
- promesse de cloud fiable;
- publication automatique;
- exposition de chemins locaux sensibles.

Travail attendu:

- classifier information, attention, protection, incident;
- appliquer precedence incident > protection > attention > information;
- associer no_lock, suspend_publication, lock_readonly, notify_internal;
- produire un evenement interne abstrait sans dependance email/SMS;
- documenter ce qui bloque publication mais permet nettoyage.

Validation:

- tests `test_vault_sync_profiles.py`, `test_vault_sync_alerts.py`,
  `test_vault_notifications.py`;
- scenarios `.git`, `.venv`, caches, conflits fournisseur, signature/hash/blob
  invalide.

Definition de fini:

- le transport ne peut pas etre confondu avec une source de verite;
- un incident d'integrite met le coffre en lecture seule;
- une protection suspend la publication sans bloquer le nettoyage.

### L6 - Comptes et commissions

Statut: PRET.

But: permettre a un novice de comprendre qui il est, ce qu'il peut voir, ce
qu'il peut faire et qui valide les productions de commission.

Ownership conseille:

- `server/src/coproscope/core/accounts.py`;
- `server/src/coproscope/modules/accessops.py`;
- `server/src/coproscope/modules/commissionops.py`;
- `server/src/coproscope/web/governance.py`;
- `server/src/coproscope/web/templates/governance.html`;
- tests comptes, accessops, commissions, UI gouvernance.

Hors perimetre:

- compte cloud obligatoire;
- droit implicite donne par un administrateur local;
- suppression d'historique par revocation;
- commission qui remplace le conseil syndical.

Travail attendu:

- separer compte local, profil local, membre du coffre et appareil signataire;
- montrer role copro/CS/commission et acces proportionnes;
- afficher referent CS, mandat, periode, validateurs et productions;
- expliquer revocation et limites des copies deja dechiffrees;
- signaler quorum de recuperation si disponible.

Validation:

- tests `test_accounts_identity.py`, `test_accessops_commissions.py`,
  `test_commissionops.py`, `test_ui_governance.py`;
- route `/gouvernance` en 200.

Definition de fini:

- une commission est bornee par sujet, periode, referent et validation;
- une production partageable a preuve/action et niveau de diffusion;
- les droits ne sont pas deduits du poste local seul.

### L7 - Indicateurs actionnables

Statut: PRET.

But: limiter le pilotage a des cartes rares, sourcees et orientees action.

Ownership conseille:

- `server/src/coproscope/modules/indicatorops.py`;
- `server/src/coproscope/modules/pilotageops.py`;
- `server/src/coproscope/web/pilotage_view.py`;
- `server/src/coproscope/web/templates/pilotage.html`;
- tests indicatorops/pilotage/UI.

Hors perimetre:

- tableau de bord decoratif sans action;
- aggregation qui expose une donnee restreinte;
- formule mutable sans trace;
- melange de plusieurs coffres.

Travail attendu:

- garder 6 a 10 cartes maximum;
- afficher periode, source, preuve, qualite/confiance, seuil et action;
- produire des questions de gestion vers syndic, AG, commission ou prestataire;
- expliquer les termes rares par micro-aides;
- exclure du cockpit principal les cartes sans action.

Validation:

- tests `test_indicatorops.py`, `test_pilotageops.py`,
  `test_ui_pilotage.py`, `test_ui_pilotage_route.py`;
- route `/pilotage` protegee en 200.

Definition de fini:

- chaque indicateur repond a "quoi regarder, pourquoi, preuve, prochaine
  action";
- aucune carte ne fuit une donnee restreinte par precision excessive.

### L8 - Suggestions sous revue humaine

Statut: PRET.

But: faire remonter des suggestions utiles sans jamais automatiser la decision.

Ownership conseille:

- `server/src/coproscope/modules/suggestionops.py`;
- `server/src/coproscope/modules/suggestionview.py`;
- tests suggestionops/suggestionview;
- cockpit uniquement si owner UI libre.

Hors perimetre:

- transformation automatique en action, demande, point, indicateur ou export;
- suggestion sans preuve ou sans source;
- conseil juridique;
- export sans revue de diffusion.

Travail attendu:

- filtrer suggestions incompletes, rejetees, non acceptees ou non sourcees;
- exiger `why`, `proof`, `source`, `next_action`, `public`, `confidence`,
  `effort`;
- conserver `automatic_effect = False`;
- afficher destination possible seulement apres revue humaine acceptee;
- garder les outcomes comme derives, pas source de verite.

Validation:

- tests `test_suggestionops.py`, `test_suggestionview.py`;
- controle qu'aucune carte ne contient `outcome_id` ou payload de mutation.

Definition de fini:

- une suggestion aide a qualifier;
- elle ne cree rien sans revue humaine explicite;
- les exports restent soumis a confidentialite/biffage.

## Lots a garder en attente

| Lot | Etat | Raison d'attente |
|---|---|---|
| Signature collaborative finale | ATTENTE | Decision cryptographique et UX de confiance a trancher avant promesse finale. |
| Cloud/sync automatique | ATTENTE | Risque de sur-promesse et de fuite; la V1 traite le transport et les alertes. |
| Mutations collaboratives multi-appareils | ATTENTE | Necessite evenements signes et resolution de conflits claire. |
| Conseil juridique AG/contentieux | ATTENTE | CoproScope organise preuves/risques, ne donne pas d'avis juridique autonome. |
| Refonte UI globale | ATTENTE | Trop de collisions avec les lots fonctionnels en cours. |

## Ordre conseille de lancement

1. UX novice P0.
2. Atelier piece-point-action-preuve, avec owner unique si `viewmodel.py` est
   necessaire.
3. Workflow ajout de document.
4. Sync transport.
5. Coffre signe anti-confiscation.
6. Comptes et commissions.
7. Indicateurs.
8. Suggestions.

Cet ordre garde toujours plus de cinq files utiles disponibles. Si un lot est
bloque par ownership, lancer le suivant dans la liste sans modifier la zone
convergente disputee.

## Phrase de lancement courte

```text
Prendre le lot Lx dans docs/agent_backlog_continu.md. Travailler dans C:\Users\brice\CoproScope\coproscope. Commencer par git status --short, declarer ownership, ne reverter personne, ne modifier que les fichiers du lot, lancer les tests cibles, et finir avec fichiers modifies, tests, limites, go/no-go integration.
```
