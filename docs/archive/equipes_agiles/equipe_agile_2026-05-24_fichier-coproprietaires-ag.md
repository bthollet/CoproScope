# Equipe agile - Fichier coproprietaires relie aux AG

Date de lancement: 2026-05-24 22:05 +02:00.
Roadmap: `RM-2026-0026`.
Chantier: `CH-20260524-220538-RM-2026-0026-fichier-copro-ag-cadrage`.
Conversations: `CONV-2026-1597` a `CONV-2026-1601`.
Mode: cadrage agile sans dev, sans serveur, sans instance privee.
Statut: pret a integrer.

## BOT-START

BOT-START - Coordinateur-scribe fichier coproprietaires AG - 2026-05-24
22:05 +02:00.

Mission: qualifier la brique minimale `members_ag_rights_v1`: coproprietaires,
lots, mandats, droits de diffusion, feuille de presence, pouvoirs, votes,
resolutions et suivis AG.

Ownership modifiable:

- ce document;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers a eviter: code applicatif, schemas, registres, instances privees,
exports bruts, secrets, connecteurs mail/LRAR, serveurs locaux et
`RM-2026-0017`.

Sources publiques relues le 2026-05-24:

- Service-Public, deroulement d'une AG de coproprietaires, verifie le
  2026-03-16: https://www.service-public.gouv.fr/particuliers/vosdroits/F2619
- Service-Public, regles de vote en AG: https://www.service-public.gouv.fr/particuliers/vosdroits/F2137
- Service-Public, convocation AG: https://www.service-public.gouv.fr/particuliers/vosdroits/F2615
- Legifrance, decret 67-223 article 14, feuille de presence:
  https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000042078670
- Legifrance, loi 65-557 article 22, droits de vote et mandats:
  https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000039313531

## Roles

| Conversation | Role | Sortie |
|---|---|---|
| `CONV-2026-1597` | Coordinateur-scribe | Arbitrage, modele minimal, commande future. |
| `CONV-2026-1598` | Designer service | Parcours novice et ecrans cibles. |
| `CONV-2026-1599` | Utilisateur novice / CS | GO/NO-GO comprehension. |
| `CONV-2026-1600` | Data/privacy AG | Objets, droits, sources et anti-fuite. |
| `CONV-2026-1601` | QA privacy / regression | Tests futurs et limites. |

Note anti-collision: les identifiants `CONV-2026-1592` a `1596` avaient ete
prepares localement, puis `CONV-2026-1592` a ete pris par le chantier vivant
`RM-2026-0009` onboarding. Ce cycle est donc renumerote en `1597` a `1601`.

## Decision produit

Verdict: `GO_CADRAGE`, `NO-GO_DEV_IMMEDIAT`.

La V1 ne doit pas etre un annuaire social. Elle doit etre un dossier de droits
AG, utile pour preparer et verifier:

- qui est coproprietaire ou represente un lot;
- qui peut etre convoque ou suivre un point;
- qui peut voter, etre present, donner pouvoir ou voter par correspondance;
- quelles voix et tantiemes doivent etre pris en compte;
- quelles resolutions/action suites sont rattachees a quelles personnes ou lots;
- quelles informations restent internes au CS ou au syndic.

Le nom novice recommande est `Participants et droits AG`. Le nom technique
interne est `members_ag_rights_v1`.

## Modele minimal V1

| Objet | Champs minimaux | Regle privacy |
|---|---|---|
| `Owner` | `owner_id`, nom affiche, role, statut actif/inactif | Pas d'adresse complete dans les vues diffuses. |
| `LotHolding` | `lot_ref`, `owner_id`, quote-part, voix AG, periode | Ref lot opaque si sortie hors CS. |
| `ContactPreference` | canal choisi, consentement, derniere verification | Aucun OAuth ni carnet brut en V1. |
| `RepresentativeMandate` | mandant, mandataire, AG, date, statut, limite | Piece source restreinte, synthese derivee. |
| `AgAttendance` | AG, present, represente, distance, vote correspondance | Feuille de presence traitee comme piece probatoire sensible. |
| `AgVoteRight` | AG, resolution, voix attendues, voix exprimees | Calcul explicable, pas de recalcul silencieux. |
| `ResolutionFollowUp` | resolution, personnes/lots impactes, action, preuve | Rattacher a DecisionOps/ActionOps, pas aux contacts bruts. |

Identifiants recommandes: `OWN-*`, `LOT-*`, `MAND-*`, `AGP-*`, `VOTE-*`.
Les noms reels, adresses, emails et telephones ne doivent jamais sortir dans
un export generique; ils restent en vue restreinte et en source locale.

## Parcours cible

1. Ouvrir `Participants et droits AG` depuis Gouvernance ou Atelier AG.
2. Voir trois compteurs: coproprietaires a verifier, pouvoirs recus, votes ou
   presences incomplets.
3. Importer ou saisir localement une liste restreinte, avec confirmation
   humaine de la source.
4. Rattacher une AG et ses resolutions.
5. Verifier pouvoirs, presence, votes par correspondance et voix attendues.
6. Produire seulement une synthese derivee: trous, incoherences, suites a
   demander, sans annuaire diffusable.

## GO/NO-GO novice

GO si l'ecran parle d'une tache concrete: preparer l'AG, verifier les pouvoirs,
voir les votes incomplets, rattacher une resolution.

NO-GO si le premier ecran ressemble a un fichier contacts, si l'utilisateur
croit pouvoir envoyer un message officiel, ou si les mots `tantiemes`,
`mandataire`, `indivision` et `demembrement` apparaissent sans explication
courte.

Microcopy obligatoire:

- `Voix AG`: nombre de voix utilise pour voter une resolution.
- `Pouvoir`: document par lequel un coproprietaire confie son vote.
- `Mandataire`: personne qui vote pour un coproprietaire absent.
- `Feuille de presence`: preuve de qui etait present, represente ou a vote par
  correspondance.

## Commande future

Commande dev proposee si `RM-2026-0026` devient prioritaire:

```text
Construire `members_ag_rights_v1` en lecture/saisie locale:
- route future: `/gouvernance/participants-ag`;
- template dedie, CSS dedie, tests dedies;
- donnees fictives uniquement;
- aucun connecteur mail, OAuth, Drive, LRAR ou carnet d'adresses;
- sources brutes restreintes; exports uniquement derives;
- lien avec `RM-2026-0024` Compte rendu CS et futur Atelier AG;
- tests anti-fuite sur noms, adresses, emails, telephones, chemins locaux,
  raw/restricted/logs et tokens.
```

## QA future

Panier minimal avant tout GO:

- route 200 tokenisee;
- libelles novice presents;
- aucun chemin local, email ou telephone dans la vue publique;
- import/saisie rejette les chemins prives;
- export derive marque `source_of_truth=false`;
- feuille de presence et pouvoirs jamais inclus bruts dans un export large;
- tests line-limit et `git diff --check`.

## Questions ouvertes

- Source V1: saisie manuelle, CSV synthetique, ou import depuis une piece AG
  deja biffee?
- Faut-il gerer l'indivision et le demembrement en V1 ou les marquer comme
  `a verifier par humain`?
- Quel niveau de detail est acceptable pour une synthese diffusable aux
  coproprietaires?
- Le lien avec `RM-2026-0028` doit rester borne aux brouillons humains tant que
  les mandats d'envoi ne sont pas qualifies.

## BOT-END

BOT-END - Coordinateur-scribe fichier coproprietaires AG - 2026-05-24
22:09 +02:00.

Statut: `PRET_A_INTEGRER`.

Fichiers modifies: ce document, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`.

Fichiers volontairement evites: code, schemas, registres, instances privees,
exports bruts, secrets, connecteurs, serveurs locaux et `RM-2026-0017`.

Tests/preuves: sources officielles relues; `git diff --check` documentaire a
lancer apres mise a jour des registres.

Limites: aucun test applicatif, aucune preuve navigateur, aucun arbitrage
juridique final. Le cadrage ne remplace pas une verification juridique si la
fonction devient engageante.

AGILE-DONE - equipe agile a fini son job.
