# Recherche UX/UI - Comptes, sync et collaboration

Date de lancement: 2026-05-24 09:19 +02:00
Date de cloture: 2026-05-24 09:34 +02:00
Statut: recherche UX/UI cloturee, sans dev
Rattachement: `RM-2026-0033`
Chantier: `CH-20260524-091917-RM-2026-0033-comptes-sync-collaboration`
Conversation coordinatrice: `CONV-2026-1368`
Assets mission: `docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration/`

## BOT-START

```text
BOT-START - Orchestrateur UX/UI - 2026-05-24 09:19 +02:00
Roadmap: RM-2026-0033
Chantier: CH-20260524-091917-RM-2026-0033-comptes-sync-collaboration
Conversation: CONV-2026-1368
Role: Orchestrateur UX/UI
Mission: lancer une recherche UX/UI sans dev sur la gestion des comptes, la synchronisation et la collaboration.
Ownership modifiable: docs/recherche_ux_ui_2026-05-24_comptes-sync-collaboration.md, docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration/, docs/presence_agents.md, docs/roadmap_backlog_central.md.
Fichiers a eviter: code applicatif, templates, CSS, tests, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, serveurs locaux, RM-2026-0017 bloque.
Passerelle/registre de trace: ce livrable de mission et docs/presence_agents.md.
Dernier point lu: AGENTS.md, docs/orchestration_agents.md, docs/protocole_equipe_ux_ui_recherche.md, docs/consignes_bots_interconversations.md, docs/protocole_roadmap_presence_agents.md, docs/roadmap_backlog_central.md, docs/presence_agents.md, docs/point_coordination_live_8766_2026-05-21.md, docs/coordination_interconversations_2026-05-21.md.
Tests/preuves attendus: preuve documentaire, blueprint/image utile a decision, lignes de presence, heartbeat 10 minutes; pas de test applicatif car aucun code ne doit etre modifie.
Risque de collision: les relances UX/UI 09:16 et le cadrage WorksOps utilisent deja CONV-2026-1355 a 1367; cette mission utilise CONV-2026-1368 a 1373 et un RM dedie.
Lease ownership: jusqu'au 2026-05-25 09:19 +02:00.
Prochaine action: lancer les roles UX/UI en lecture seule, consolider parcours, directions UI, tests metier et novice.
```

## Objectif

Produire une decision UX/UI sur la maniere d'expliquer et d'utiliser:

- le compte local CoproScope;
- le compte cloud ou fournisseur de sync, s'il existe;
- le membre du coffre et son role;
- les appareils autorises;
- le statut du coffre signe;
- la synchronisation comme transport non fiable;
- l'invitation collaborative, les droits, la revocation et la recuperation.

Cette recherche ne produit ni patch, ni route, ni ticket technique detaille.

## Roles

| Conversation | Role | Statut | Sortie attendue |
|---|---|---|---|
| `CONV-2026-1368` | Orchestrateur UX/UI | `CLOTURE` | Cadrage, arbitrage, heartbeat, synthese finale. |
| `CONV-2026-1369` | Chercheur utilisateur | `CLOTURE` | Profils, besoins, irritants, scenarios et criteres de reussite integres. |
| `CONV-2026-1370` | Architecte UX | `CLOTURE` | Parcours, etats, priorites d'information et variantes integres. |
| `CONV-2026-1371` | Designer UI / generateur visuel | `CLOTURE` | Direction UI, critique blueprint et microcopy integrees. |
| `CONV-2026-1372` | Testeur metier expert | `CLOTURE` | Garde-fous droits, roles, sync, coffre signe, recuperation et cas limites integres. |
| `CONV-2026-1373` | Testeur accessibilite / novice | `CLOTURE` | Comprehension immediate, jargon, charge cognitive et risques de mauvaise action integres. |

## Sources de depart

| Source | Usage |
|---|---|
| `docs/bandeau_contexte_coffre_role_sync.md` | Contexte coffre, role, acces, sync, verification et prochaine action. |
| `docs/transition_vault_collaboratif.md` | Doctrine local-first, vault chiffre, sync transport et evenements signes. |
| `docs/vault_format.md` | Regles de sync, roles decryptables, verification et exclusions. |
| `docs/checklist_installable_drive_chiffre_noob.md` | Parcours noob creation coffre, compte cloud, partage et revocation. |
| `docs/enquete_collaboration_coedition_impact_2026-05-24.md` | Collaboration de gouvernance et limites de coedition. |
| `docs/ux_review_atelier_piece.md` | Manque actuel de visibilite vault, signatures, historique et conflits. |

## Hypotheses a challenger

| ID | Hypothese | Risque si faux |
|---|---|---|
| `H1` | Le novice distingue mal compte local, compte cloud, membre du coffre et role. | Il croit qu'un login cloud controle les droits metier. |
| `H2` | Le premier ecran doit dire "ce coffre est local" avant de parler sync. | Il pense que tout est deja publie ou sauvegarde ailleurs. |
| `H3` | La collaboration utile est asynchrone: invitation, validation, preuve, version et recuperation. | L'UI part vers un chat ou une coedition temps reel non prioritaire. |
| `H4` | La sync doit etre montree comme un transport a verifier, pas comme une source de verite. | L'utilisateur partage un dossier dangereux ou ignore les conflits. |
| `H5` | Les droits doivent etre exprimes par consequences: lire, ajouter, valider, signer, exporter, recuperer. | Les roles restent abstraits et les erreurs de diffusion augmentent. |

## Direction visuelle initiale

| Direction | Statut | Asset | Decision provisoire |
|---|---|---|---|
| `D1` Console comptes et partage | `rejetee mais instructive` | `docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration/01-console-comptes-sync-collaboration.svg` | Bons blocs, mais titre trop large, CTA invitation dangereux avant verification, charge novice trop forte et statuts incoherents. |
| `D2` Centre de confiance du coffre | `retenue` | `docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration/02-centre-confiance-coffre.svg` | Direction retenue: expliquer d'abord coffre local, transport Drive, acces des personnes, puis seulement l'invitation. |

Prompt/intention:

```text
Interface web professionnelle et dense pour CoproScope, local-first.
Ecran "Comptes et partage": bandeau coffre local, colonne statut sync,
liste des membres et roles, appareils autorises, invitations en attente,
conflits ou risques de transport, action principale prudente.
Le style doit etre sobre, lisible, non marketing, sans donnees reelles.
```

## Points a produire

- Profils cibles: president CS, membre novice, syndic benevole, expert externe,
  nouveau membre en passation, gardien de recuperation.
- Parcours principal: creer coffre, connecter transport, inviter, verifier,
  resoudre conflit, revoquer, recuperer.
- Etats: local seul, sync non configuree, sync a verifier, coffre verifie,
  conflit transport, invitation en attente, acces revoke, recuperation requise.
- Garde-fous: pas de promesse cloud, pas de partage de raw, pas de droits
  deduits du poste local seul, pas de signature forte implicite.
- Tests metier et novice: comprehension en moins de 30 secondes, zero confusion
  entre compte cloud et role CoproScope, action de partage non dangereuse.

## Synthese utilisateur

Les profils prioritaires sont le president ou secretaire du conseil syndical,
le membre CS novice, le syndic benevole ou l'autogestion, l'expert externe
ponctuel, le nouveau membre en passation, le gardien de recuperation et le
coproprietaire lecteur.

Le besoin central n'est pas un login. Il faut separer quatre objets:

- le coffre local;
- le compte cloud utilise comme transport;
- le membre du coffre avec son role CoproScope;
- l'appareil autorise.

Les irritants prioritaires sont la confusion entre compte Google et droits
CoproScope, la croyance qu'une sync active est automatiquement sure, les roles
trop abstraits, le jargon technique, et la peur de perdre ou confisquer la
memoire apres un depart du conseil syndical.

## Architecture UX

Objet de premier niveau recommande: `Coffre et partage`.

Parcours principal:

```text
Ouverture
  -> Coffre absent
      -> Creer coffre local
      -> Verifier coffre
  -> Coffre local existant
      -> Centre de confiance du coffre

Centre de confiance du coffre
  -> Sync non connectee
      -> Connecter Drive / transport cloud
      -> Verifier surface chiffree
  -> Sync a surveiller
      -> Voir risques transport
      -> Corriger / suspendre partage
  -> Coffre verifie
      -> Preparer invitation

Preparer invitation
  -> Choisir membre
  -> Choisir role par consequences
  -> Choisir compartiment / duree / recuperation
  -> Relire resume des droits
  -> Verification anti-fuite
      -> OK: invitation prete
      -> KO: partage bloque
```

Etats d'ecran a prevoir:

- `Local seul`;
- `Sync non configuree`;
- `Drive connecte, coffre non envoye`;
- `Sync a verifier`;
- `Partage bloque`;
- `Pret a partager`;
- `Invitation en attente`;
- `Collaboration active`;
- `Acces revoque`;
- `Recuperation requise`.

Priorite d'information:

1. vous etes dans ce coffre;
2. les documents lisibles restent locaux;
3. le coffre local verifie fait foi;
4. Drive est seulement un transport;
5. prochaine action sure;
6. membres et droits par consequences;
7. appareils autorises;
8. invitation, revocation et recuperation;
9. details experts en second niveau.

## Direction UI retenue

Retenir `D2 - Centre de confiance du coffre`.

Structure:

- bandeau: `Vous travaillez dans ce coffre`;
- trois zones: `Sur cet ordinateur`, `Transport Drive`, `Acces des personnes`;
- panneau d'action principal: `Verifier avant partage` tant que le coffre n'est
  pas verifie;
- checklist anti-fuite: documents lisibles absents, coffre chiffre verifie,
  compte Drive confirme, fichiers partiels ou conflits controles;
- section membres avec droits concrets: lire, ajouter, valider, exporter,
  recuperer;
- section appareils: proprietaire, statut, derniere verification, action
  prudente.

Microcopy recommandee:

- `Les documents lisibles restent sur cet ordinateur.`
- `Google Drive transporte seulement le coffre chiffre. Il ne decide pas des droits.`
- `CoproScope verifie que rien de lisible ne part dans Drive.`
- `Partage bloque: le coffre chiffre n'est pas encore verifie.`
- `Choisissez d'abord ce que cette personne peut lire.`
- `Ancien appareil: retirer l'acces aux prochaines versions.`
- `Google Drive n'est plus autorise. Vos donnees restent dans le coffre local.`

Jargon a masquer au premier niveau: `vault`, `sync_root`, `OAuth`, `scope`,
`token`, `blob`, `payload`, `hash`, `placeholder`, `quorum`.

## Test metier

NO-GO metier pour toute UX qui presente la sync ou le cloud comme source de
verite ou comme systeme de droits.

No-go:

- bouton de partage actif avant verification anti-fuite;
- confusion entre compte Drive et droits CoproScope;
- invitation sans choix explicite du role ou du compartiment;
- revocation presentee comme effacement des copies deja repliquees;
- signature interne presentee comme signature electronique qualifiee;
- diagnostic ou export contenant noms reels, chemins prives, OCR, documents
  bruts, commentaires ou statuts metier lisibles.

Conditions GO:

- l'utilisateur sait ce qui est local;
- il sait ce qui part dans le cloud;
- il sait qui peut lire quoi;
- il sait si le coffre est verifie ou non;
- il sait quelle version est signee ou validee;
- il sait ce qui peut etre diffuse hors CoproScope.

## Test novice

Verdict novice: NO-GO pour transformer `D1` en ecran activable. GO conditionnel
pour `D2` si l'action principale est unique et prudente.

Ordre de comprehension attendu:

1. ou suis-je ?
2. est-ce local ou partage ?
3. est-ce verifie ?
4. puis-je inviter quelqu'un ?
5. que pourra-t-il lire ?

Le bouton d'invitation doit etre desactive ou remplace par
`Choisir les droits, sans envoyer` tant que la verification n'est pas terminee.

## Decision

Decision UX/UI: ne pas partir d'un module `Compte` generique.

Le premier MVP UX doit etre un `Centre de confiance du coffre`, avec un flux
secondaire `Assistant prudent de partage`.

La collaboration cible reste asynchrone et probatoire: membres, roles,
appareils, versions, preuves, validations, signatures internes, revue de
diffusion, conflits et recuperation. Le chat et la coedition temps reel sont
hors premier niveau.

## Questions ouvertes

- Faut-il nommer la navigation `Coffre et partage`, `Acces au coffre` ou
  `Centre de confiance` ?
- Quelle action principale doit etre proposee quand la sync n'est pas encore
  verifiee ?
- Comment nommer le role d'un membre qui peut recuperer le coffre sans lire
  toutes les donnees ?
- Faut-il montrer les appareils comme des "postes de travail" ou comme des
  "cles de signature" ?
- Quel vocabulaire novice remplace `vault`, `sync_root`, `OAuth`, `scope` et
  `conflit de transport` au premier niveau ?

## BOT-END

```text
BOT-END - Orchestrateur UX/UI - 2026-05-24 09:34 +02:00
Roadmap: RM-2026-0033
Chantier: CH-20260524-091917-RM-2026-0033-comptes-sync-collaboration
Conversation: CONV-2026-1368
Statut: CLOTURE
Fichiers modifies: docs/recherche_ux_ui_2026-05-24_comptes-sync-collaboration.md, docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration/01-console-comptes-sync-collaboration.svg, docs/assets/ux-ui-recherche-2026-05-24-comptes-sync-collaboration/02-centre-confiance-coffre.svg, docs/presence_agents.md, docs/roadmap_backlog_central.md.
Fichiers volontairement evites: code applicatif, templates, CSS, tests, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, serveurs locaux, RM-2026-0017 bloque.
Tests/preuves: preuve documentaire et blueprints SVG; aucun test applicatif car aucun code produit.
Limites: synthese issue du corpus documentaire et de roles agents, pas d'entretiens terrain nouveaux.
Questions ouvertes: nom exact de la navigation, role de recuperation, statut des appareils et microcopy finale.
Prochain mouvement propose: ouvrir un chantier dev separe seulement si Brice valide le MVP `Centre de confiance du coffre`.
```

UXUI-DONE - equipe UX/UI a fini son job
