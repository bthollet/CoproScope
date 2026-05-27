# Audit gouvernail - maturite proche issue des retours agiles

Date initiale: 2026-05-23
Mise a jour: 2026-05-24

Perimetre: challenge du gouvernail `docs/roadmap_backlog_central.md` au
regard des retours equipes agiles, tests novices, QA live, tests locaux et
filtre "maximiser ce qui peut etre fait sans IA cloud".

## Synthese 2026-05-24

Le diagnostic a change depuis l'audit initial: le lot local-first proche de
maturite n'est plus seulement candidat, il est integre techniquement.

- `RM-2026-0019` est `INTEGRE`: `/actions` public est branche, le couloir
  `piece -> relance -> depot` est clarifie, passation/share sont durcis contre
  fuites de secrets et elargissement prive de scope.
- `RM-2026-0016` reste `ACTIF`, mais le verrou a change: il ne s'agit plus de
  construire les premiers read models publics, mais de mesurer `/actions`,
  `/pieces?proof=missing` et les exports sur instance metier reelle.
- `RM-2026-0017` est le P0 operationnel courant: reconstruction progressive
  Beauvallon, simulation comparee au reel, pieces primaires filtrees et
  pipeline local.
- `RM-2026-0020` est `INTEGRE`: le choix d'instance locale existe et simplifie
  la recette reelle.

Conclusion: le gouvernail est coherent. La priorite immediate ne doit pas
rouvrir un chantier IA ou UI generaliste; elle doit utiliser la reconstruction
Beauvallon comme banc de preuve reel pour mesurer performance, robustesse et
qualite utilisateur.

## Verdict actualise

Le cap `preuve + action + memoire` reste le bon. Le risque principal n'est plus
la pertinence fonctionnelle des lots proches; il est maintenant la confusion
entre:

- fonctionnalite integree techniquement;
- fonctionnalite recettee sur fixture;
- fonctionnalite validee sur instance metier reelle;
- fonctionnalite diffusable/partageable sans fuite.

Le gouvernail doit donc garder une regle stricte: une fonctionnalite peut etre
marquee `INTEGRE` quand le code et les gates sont verts, mais le GO produit
reel exige encore mesure sur donnees metier, temps de reponse, absence de fuite
et comprehension novice.

## Fonctionnalites proches de maturite

| Rang | Fonctionnalite | Statut actualise | Ce qui est acquis | Dernier verrou produit |
|---:|---|---|---|---|
| 1 | Read models publics `/pieces?proof=missing` et `/actions` | Integre technique | Projections locales allowlistees, controle schema/version, fallback vide, pas de `SELECT *`, pas de FTS/MATCH, pas de dashboard global quand le vault public est configure. | Mesurer sur instance metier reelle et surveiller que les nouveaux filtres n'elargissent pas la surface publique. |
| 2 | Couloir `piece -> detail -> relance -> depot` | GO technique local-first | Routes reelles, token conserve, relance non envoyee, depot contextualise, labels novice visibles, navigateur desktop/mobile OK sur fixture. | Rejouer sur instance Beauvallon reconstruite, avec temps cible et donnees non synthetiques. |
| 3 | Relance syndic locale sans envoi automatique | Proche produit | Brouillon prudent, contextualise depuis piece/action, aucune promesse d'envoi automatique, rattachement depot/reponse. | Consolider la trace d'envoi hors CoproScope: date, canal, personne, prochaine verification. |
| 4 | Frontiere publication `share-audit` / `share-export` | GO technique anti-fuite | Blocage chemins, tokens, OAuth, refresh token, OpenAI `sk-*`, Bearer token, redaction maps et contenus interdits. | Ajouter une UX explicite de blocage: pourquoi c'est bloque et quoi faire pour produire une derive partageable. |
| 5 | Passation prudente avec blocages | Proche sur sous-surfaces | Exports derives, blocages explicites, liens token-safe, protection `scope=event` prive. | Ne pas declarer la passation globale mature tant que les exports restent lents sur instance reelle. |
| 6 | AG/contentieux precontentieux derive | Utilisable si borne | Rapports derives, controles privacy/audit, aide a pieces/reserves/demandes. | Ne pas vendre comme assistant juridique autonome; garder decision humaine et sources citees. |

## Fonctionnalites a ne pas surestimer

| Fonctionnalite | Statut reel | Challenge gouvernail |
|---|---|---|
| Installable noob Drive chiffre (`RM-2026-0014`) | Strategique, encore bloque cote OAuth/JSON | Ne pas le melanger avec les lots local-first deja integres. Le partage Drive doit rester chiffrement/transport, pas source de raisonnement cloud. |
| Reconstruction Beauvallon (`RM-2026-0017`) | P0 operationnel actif | C'est le banc de preuve reel/test, pas un second produit. Sa valeur est de demontrer que le systeme reconstruit une base fiable depuis les pieces primaires. |
| Passation globale | Direction correcte, pas GO complet | Les sous-surfaces sont durcies; le verrou restant est perf et lisibilite sur instance reelle. |
| Registre `/actions` createur | Consultation/read model integres | La creation complete d'action, echeance, preuve, responsable et decision rattachee reste un futur flux produit. |
| Controle comptes guide | Amorce forte | Le parcours complet anomalie -> question -> relance/preuve -> rapport AG doit encore etre ferme. |
| Gouvernance multi-coffres / anti-confiscation UI | Differenciant long terme | A garder dans la vision, mais hors maturite proche tant que les flux simples ne sont pas prouves sur reel. |

## Challenge sans IA cloud

Objectif produit: maximiser ce qui peut etre fait en local, sans envoyer les
pieces, textes OCR, noms, chemins, mails ou rapports vers une IA cloud.

| Fonctionnalite | Potentiel sans IA cloud | Primitive locale retenue | Statut |
|---|---|---|---|
| Read models publics | Maximal | SQLite/projections locales, allowlist, schema/version, fallback vide, tests anti-fuite. | Integre pour `/pieces?proof=missing` et `/actions`. |
| Couloir piece/relance/depot | Tres eleve | Completeness locale, gabarits de relance, depot contextualise, journal d'action. | GO technique; recette reelle a faire. |
| Relance syndic | Tres eleve | Brouillon controle, copie manuelle, envoi hors outil, trace locale. | Proche produit. |
| Passation/share | Eleve | Exports derives, biffage, blocage secrets, validation humaine. | Sous-surfaces durcies; perf reelle a mesurer. |
| AG/contentieux | Moyen a eleve si borne | Checklists, rapports a trous, sources citees, derives anonymisees. | Usage expert borne seulement. |
| Drive chiffre | Transport uniquement | Chiffrement local puis upload minimal. | Bloque tant que le client OAuth n'est pas fourni. |

Regle d'arbitrage maintenue: une fonctionnalite monte en priorite si elle
remplace un appel IA cloud potentiel par une primitive locale verifiable:
projection SQLite, OCR local, gabarit, checklist, extraction citee, biffage,
journal d'action ou export derive.

## Sequence recommandee actualisee

### Lot 1 - Recette reelle sur Beauvallon

- Utiliser `RM-2026-0017` comme banc de preuve.
- Comparer l'instance simulation triee par CoproScope avec l'instance reelle.
- Mesurer `/actions`, `/pieces?proof=missing`, detail piece, relance, depot et
  passation sur donnees metier.
- Produire un GO/NO-GO separe: performance, non-fuite, comprehension novice,
  couverture des pieces primaires.

### Lot 2 - Fermer les flux createurs

- Transformer `/actions` de registre consultable en flux createur minimal:
  action, responsable, echeance, preuve attendue, decision/source rattachee.
- Relier `comptes -> question syndic -> relance -> preuve attendue`.
- Garder l'envoi hors CoproScope tant que la chaine probatoire n'est pas
  totalement auditable.

### Lot 3 - Partage et installable

- Ne reprendre `RM-2026-0014` que lorsque le JSON OAuth Desktop app est place
  hors Git.
- Garder le partage Drive comme transport chiffre, jamais comme traitement IA.
- Ajouter l'UX de blocage publication: expliquer la cause et la correction
  attendue sans exposer le secret bloque.

## Verifications acquises

Panier local final depuis `server/`:

```text
python -m unittest tests.test_public_read_models tests.test_code_line_limit tests.test_vault tests.test_ui_piece_detail_route tests.test_ui_requests_route tests.test_ui_depot_flow tests.test_ui_live_ux_contract tests.test_ui_passation_export_route tests.test_security_no_private_sync_leaks tests.test_pipeline tests.test_privacy tests.test_audit360_import tests.test_gdriveops tests.test_ui_smoke_routes_expanded -v
Ran 119 tests in 38.406s
OK (skipped=1)
```

Recette live separee avec serveur `127.0.0.1:8766`:

```text
python -m unittest tests.test_ui_live_ux_contract -v
Ran 6 tests in 2.077s
OK
```

Passe navigateur in-app: desktop 1280x720 et mobile 390x844 sur
`/pieces?proof=missing`, detail piece, relance, depot et `/actions?priority=P1`.
Labels utiles presents, aucun debordement horizontal.

## Decision gouvernail

`RM-2026-0019` peut rester `INTEGRE`. Le prochain travail prioritaire n'est pas
un nouveau lot IA ou un nouvel ecran abstrait: c'est la validation metier via
`RM-2026-0017`, avec mesures reelles et comparaison simulation/reel.
