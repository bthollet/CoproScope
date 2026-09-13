# Equipe agile - Confidentialite conversationnelle des audits

Date de lancement: 2026-05-24 20:46 +02:00.
Roadmap: `RM-2026-0013`.
Chantier: `CH-20260524-204545-RM-2026-0013-confidentialite-conversationnelle-audits`.
Conversation coordination: `CONV-2026-1561`.
Mode: equipe agile gouvernail, cadrage documentaire sans dev.
Statut: pret a integrer - doctrine sans dev.

## BOT-START

BOT-START - Coordinateur-scribe privacy audits - 2026-05-24 20:46 +02:00

Roadmap: `RM-2026-0013`.
Chantier: `CH-20260524-204545-RM-2026-0013-confidentialite-conversationnelle-audits`.
Conversation: `CONV-2026-1561`.
Role: Coordinateur-scribe privacy audits.
Mission: produire une garde de confidentialite conversationnelle pour les audits CoproScope: regle de redaction assistant, gabarit de rapport anonymise, checklist avant envoi final et criteres de test anti-fuite, sans manipuler de donnees reelles.
Ownership modifiable: ce document, `docs/presence_agents.md`, ligne gouvernail `RM-2026-0013`.
Fichiers a eviter: code applicatif, tests applicatifs, serveurs locaux, instances privees, documents bruts, derives OCR, exports locaux, noms reels, emails, telephones, lots nominatifs, secrets, `RM-2026-0017` bloque et serveur `CONV-2026-1525`.
Passerelle/registre de trace: ce document, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/protocole_equipe_agile_agents.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/consignes_bots_interconversations.md`, `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`, `docs/audit360.md` au 2026-05-24 20:46 +02:00.
Tests/preuves attendus: retours privacy, redacteur audit, novice et QA; synthese exploitable; `git diff --check` sur docs; aucun test applicatif sans code.
Risque de collision: aucune equipe vivante sur `RM-2026-0013`; `CONV-2026-1556`..`1558` sont deja pris par DocOps feedback dev dans un worktree dedie; `RM-2026-0017` reste bloque; `CONV-2026-1525` garde un serveur local; cette vague reserve `CONV-2026-1561`..`1565`.
Lease ownership: 2026-05-24 22:46 +02:00.
Prochaine action: lancer quatre roles en lecture seule et consolider une doctrine utilisable par les audits futurs.

## Choix Gouvernail

Les P0 dev-ready recents (`RM-2026-0030`, `RM-2026-0032`, `RM-2026-0033`) sont
prets a integrer mais restent no-go dev dans le worktree principal. `RM-2026-0003`
/ `RM-2026-0029` et `RM-2026-0017` restent bloques. Le prochain P0 actionnable
sans serveur, instance privee ni code est donc `RM-2026-0013`.

## Artefact Cible

- Artefact reel: cette mission, avec une section finale pouvant etre extraite
  ensuite vers `docs/confidentialite_conversationnelle_audits.md`.
- Produit attendu: doctrine courte et opposable pour les fils d'audit.
- Non-objectifs: biffer de vrais documents, relancer un audit reel, publier des
  noms, tester une instance, modifier un prompt systeme ou toucher au code.

## Roles

| Role | Conversation | Statut | Sortie attendue |
|---|---|---|---|
| Coordinateur-scribe | `CONV-2026-1561` | `PRET_A_INTEGRER` | Registres, arbitrage et synthese; equipe cloturee. |
| Privacy lead | `CONV-2026-1562` / McClintock `019e5b52-074c-7fb1-b9a7-f857a4422c1b` | `CLOTURE` | Regle de minimisation conversationnelle, alias et exceptions integres. |
| Redacteur audit novice | `CONV-2026-1563` | `CLOTURE` | Gabarit de rapport lisible consolide localement faute de thread disponible. |
| QA anti-fuite | `CONV-2026-1564` | `CLOTURE` | Checklist et tests documentaires consolides localement faute de thread disponible. |
| Integrateur gouvernance | `CONV-2026-1565` | `CLOTURE` | Points d'insertion et no-go consolides localement faute de thread disponible. |

## Point Court Initial

A produire: doctrine assistant, gabarit anonymise, checklist de rendu final,
criteres de test et points d'insertion gouvernance.

En dev maintenant: rien.

En test maintenant: seulement controle documentaire et diff-check.

En enquete maintenant: relire les garde-fous audit et privacy deja presents.

Commande prete: non; elle doit etre consolidee par les roles.

Decision requise: aucune decision Brice bloquante pour produire une doctrine
sans donnees reelles.

Prochain mouvement: attendre les quatre retours, consolider, puis passer au
prochain P0 actionnable si `AGILE-DONE` est atteint.

## Retours Consolides Provisoires

### Privacy lead

Regle de minimisation: dans une conversation d'audit, l'assistant ne conserve et
ne reformule que ce qui sert directement la chaine `fait -> preuve -> regle ->
action`. Par defaut, il parle en roles, pieces, periodes, montants agreges et
statuts, pas en identites reelles.

Toute identite reelle doit etre remplacee des la premiere reformulation par un
alias stable dans la conversation. Les noms, emails, telephones, adresses
precises, numeros de lots nominatifs, chemins locaux, extraits OCR et noms de
fichiers bruts ne sont pas recopies dans les messages, sauf exception stricte.

Schema d'alias:

- personnes physiques: `PERS-01`, ou alias metier `COPRO-01`, `CS-01`,
  `GEST-01`, `AVOCAT-01`;
- syndic et organisations: `ORG-01`, `SYNDIC-01`, `PREST-01`, `ASSUREUR-01`;
- lots et lieux: `LOT-01`, `BAT-A`, `ADDR-01`, sans melanger avec le nom d'un
  coproprietaire;
- pieces: `PIECE-AG-2026-01`, `PIECE-COMPTA-2025-01`, `PIECE-TRAVAUX-01`;
- montants: conserver le montant seulement s'il est necessaire au controle;
  sinon utiliser `montant global`, `ecart significatif`, `poste concerne`;
- stabilite: alias stable dans une meme conversation ou un meme rapport; pas de
  reutilisation inter-conversations sans registre explicite valide.

Exceptions strictes: une identite peut rester visible uniquement si elle est
indispensable a une diligence concrete, si la sortie reste privee et locale, et
si l'identite visible est limitee au segment necessaire. Le resume
conversationnel revient aux alias des que l'identite complete n'est plus utile.

No-go privacy: nom reel non indispensable, email, telephone, adresse complete,
chemin local prive, nom de fichier brut sensible, extrait OCR, document
raw/restricted/logs, correspondance nominative lot-personne, secret ou donnee
d'instance presentee comme exemple generique.

### Redacteur audit novice

Gabarit recommande pour un rapport d'audit conversationnel anonymise:

1. Synthese novice: ce qui est constate, ce qui est seulement suppose, ce qui
   reste a verifier, et l'impact concret pour les coproprietaires.
2. Methode: controles realises, limites, sources derivees utilisees et raison
   pour laquelle les pieces brutes ne sont pas reprises dans le fil.
3. Sources: references par alias de piece, par exemple `PIECE-AG-001`,
   `PIECE-COMPTA-002`, `PIECE-TRAVAUX-003`, sans nom de fichier brut ni chemin.
4. Constats: formules courtes, separees des interpretations, avec role ou alias
   au lieu de personne nommee.
5. Risques et preuves attendues: preuve minimale, validateur humain, reserve ou
   condition de diffusion.
6. Actions proposees: demande a preparer, question a poser, piece a rattacher,
   arbitrage CS/AG, sans envoi automatique.
7. Annexe d'alias: optionnelle et locale seulement; ne pas la publier si elle
   relie alias et personnes reelles.

Libelles preferes: `le coproprietaire demandeur`, `le syndic`, `le conseil
syndical`, `l'entreprise citee dans la piece`, `la resolution`, `la facture`,
`la piece source`, `le lot concerne` si le lot est indispensable et aliasse.

Libelles a eviter dans le fil: noms propres de personnes, adresses, emails,
telephones, numeros de lot reels, noms de fichiers bruts, chemins locaux,
extraits OCR longs, montants nominativement rattaches et allegations formulees
comme certitudes.

### QA anti-fuite

Checklist avant rendu final:

- aucun chemin local (`C:\`, `/Users`, `/home`, `file://`) ni nom de dossier
  prive;
- aucun email, telephone, IBAN/RIB, token, secret, hash de document prive ou
  table de correspondance alias -> personne;
- aucun nom de personne physique sauf demande explicite et necessite juridique
  documentee;
- aucune citation longue de document brut; preferer resume source et reference
  d'alias;
- aucun fichier joint brut, OCR brut, log, export local ou derive non biffe;
- chaque montant sensible affiche son contexte sans rattacher inutilement a une
  personne;
- chaque allegation distingue `constate`, `suppose`, `a verifier`;
- chaque diffusion indique si elle est `CS seulement`, `a verifier avant
  partage`, `bloquee` ou `diffusable apres controle`.

Tests documentaires a lancer manuellement ou par script futur:

- scan de motifs: chemins locaux, emails, telephones, IBAN, tokens et `file://`;
- scan de mots interdits: `raw`, `restricted`, `logs`, `private`,
  `payload_json`, `ocr_text`, `source_path`, `absolute_path`;
- controle d'alias: toute personne physique doit etre remplacee par un role ou
  un alias stable;
- controle de citations: pas de bloc long issu d'une piece brute;
- controle de statut: aucun rapport ne conclut sans preuve minimale et reserve
  explicite.

No-go QA: si le rapport contient une donnee personnelle inutile, un chemin
local, une piece brute, une table de correspondance ou une allegation non
sourcee, il reste en brouillon local et ne doit pas etre diffuse.

### Integrateur gouvernance

Points d'insertion futurs:

- `AGENTS.md`: ajouter un rappel court pour les audits et rapports sensibles;
- `docs/consignes_bots_interconversations.md`: ajouter la checklist avant rendu
  final;
- `docs/protocole_equipe_agile_agents.md`: ajouter un gate privacy
  conversationnelle pour toute equipe qui manipule audit, contentieux,
  coproprietaires ou documents bruts;
- `docs/audit360.md`: relier la couche Audit360 a cette doctrine de restitution
  conversationnelle;
- futurs tests docs: ajouter un check anti-fuite sur rapports d'audit
  publiables.

Limites a ne pas automatiser: decider qu'une personne doit etre nommee dans un
rapport, qualifier juridiquement une accusation, diffuser une piece litigieuse,
lever une reserve de biffage ou publier une table alias -> identite reelle.

## Decision de cloture

Commande prete: oui, sous forme de doctrine documentaire.

En dev maintenant: rien.

Tests/preuves: pas de test applicatif car aucun code n'est modifie. Verification
documentaire: `git diff --check`.

Prochain mouvement: extraire ou integrer cette doctrine dans `AGENTS.md`,
`docs/consignes_bots_interconversations.md` et `docs/audit360.md` lors d'un
chantier docs dedie, puis ajouter un check docs anti-fuite si Brice valide.

BOT-END - Coordinateur-scribe privacy audits - 2026-05-24 20:50 +02:00

AGILE-DONE - equipe agile a fini son job

## Journal

| Heure | Acteur | Evenement | Detail |
|---|---|---|---|
| 2026-05-24 20:46 +02:00 | `CONV-2026-1561` | `BOT-START` | Vague agile documentaire ouverte sur `RM-2026-0013`; aucun code, serveur, instance privee, donnee reelle ni `RM-2026-0017`. |
| 2026-05-24 20:46 +02:00 | `CONV-2026-1561` | `RENUMBER_AFTER_COLLISION` | `CONV-2026-1556`..`1558` etaient deja pris par DocOps feedback dev; cette vague utilise `CONV-2026-1561`..`1565`. |
| 2026-05-24 20:47 +02:00 | `CONV-2026-1562` | `AGENT_LAUNCHED` | McClintock lance en lecture seule; les autres roles restent locaux faute de thread disponible. |
| 2026-05-24 20:50 +02:00 | `CONV-2026-1562` | `PRIVACY_RETURN_INTEGRATED` | Regle de minimisation, schema d'alias, exceptions strictes et no-go privacy integres. |
| 2026-05-24 20:50 +02:00 | `CONV-2026-1561`..`CONV-2026-1565` | `AGILE_DONE` | Doctrine conversationnelle cloturee sans dev: gabarit, checklist, tests docs, points d'insertion et no-go consolides. |
