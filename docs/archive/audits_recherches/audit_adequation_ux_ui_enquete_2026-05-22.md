# Audit adequation UX/UI a l'enquete utilisateur

Date: 2026-05-22 01:16 +02:00
Declencheur: automatisation `audit-ux-ui-coproscope`
Statut: trace consolidee, integree au gouvernail `docs/roadmap_backlog_central.md`

## Methode

Six analyses specialisees ont ete lancees en lecture seule:

| Role | Angle |
|---|---|
| Agent 1 | Synthese UX research et besoins stables |
| Agent 2 | Heuristiques UI et architecture d'information |
| Agent 3 | Tests utilisabilite, accessibilite et langage novice |
| Agent 4 | Adequation produit-strategie |
| Agent 5 | Priorisation roadmap 0-90 jours |
| Agent 6 | Qualite des scenarios de test et recette |

Sources principales: `docs/etude_utilisateurs.md`,
`docs/ux_ecarts_enquete_vs_produit_2026-05-20.md`,
`docs/strategie_obsidian_like_enquete_utilisateur.md`,
`docs/test_novice_*.md`, `docs/recette_visuelle_refonte_ux.md`,
`docs/roadmap_backlog_central.md`, `docs/feuille_de_route.md`,
`docs/roadmap_produit_fini_visuels_enquete.md`, les templates web et les tests
`server/tests/test_ui_*.py`.

## Verdict consolide

CoproScope reste strategiquement aligne avec l'enquete: le cap correct est
toujours `preuve + action + memoire`, dans un produit local-first pour conseil
syndical. Le probleme prioritaire n'est plus l'absence de vision ni l'absence
de surfaces UI. Le risque principal est la dispersion: trop de modules, de
routes, de tables et de termes techniques peuvent masquer la boucle de travail
attendue par un membre de conseil syndical.

Une fonctionnalite est alignée seulement si elle aide a repondre sans
documentation:

1. Quel sujet demande attention ?
2. Quelle preuve regarder ?
3. Quelle action est legitime maintenant ?
4. Que peut-on partager, avec qui et sous quelle prudence ?
5. Comment la trace sera retrouvee ou transmise plus tard ?

## Conclusions principales

### UX research

- Le besoin stable n'est pas le stockage documentaire mais la chaine
  `piece -> demande/decision -> action -> preuve -> restitution`.
- Les demandes syndic, les pieces manquantes, les comptes avant AG et la
  passation sont les boucles a prouver avant d'elargir.
- Les concepts techniques `vault`, `hash`, `sync`, `plugin`, `signature` ne
  valent en UX que s'ils se traduisent en confiance visible et actionnable.

### UI et architecture d'information

- La navigation reste trop fragmentee pour un novice.
- Les trois entrees a stabiliser sont: `Aujourd'hui`, `Travailler un sujet`,
  `Transmettre`.
- Les pages doivent mettre l'objet de travail dans le premier viewport:
  cockpit avec 3 a 5 cartes, actions en master-detail, comptes avec panneau de
  lecture, memoire avec timeline et rail de passation.
- Les tableaux restent utiles en mode audit, mais ne doivent pas etre le
  premier niveau de comprehension.

### Tests, accessibilite et langage

- Les tests actuels couvrent surtout routes, libelles, tokens et absence de
  fuite de chemins. C'est utile mais insuffisant pour un GO novice.
- Il manque une recette navigateur multi-viewport avec captures, overflow,
  focus clavier, aides non limitees a `title`, H1 coherent et CTA non coupe.
- Les tests doivent couvrir des parcours complets, pas seulement des pages:
  creer une demande, ajouter une piece, ouvrir un brouillon, rattacher une
  preuve, verifier la trace.

### Produit et strategie

- Le cap `preuve + action + memoire` est coherent.
- L'anti-confiscation est differenciante mais encore trop technique. Elle doit
  devenir visible sous forme d'archive verifiable, droits compréhensibles,
  recuperation et restrictions auditees.
- La passation doit etre traitee comme preuve de valeur proche, pas comme un
  export final repousse.

## Arbitrage 0-90 jours

| Horizon | Decision |
|---|---|
| 0-30 jours | Lever les NO-GO novices et prouver les boucles courtes: cockpit/action inbox, navigation 3 intentions, ajout document, demande syndic, piece manquante, relance, preuve, export prudent. |
| 30-60 jours | Transformer les signaux en chaines metier: demandes/SyndicOps, decision -> action -> preuve, ComptaScope guide AG, memoire/passation MVP, membres/droits minimaux. |
| 60-90 jours | Consolider confiance et collaboration: vault/sync lisibles, anti-confiscation traduite en produit, multi-coffres isoles, indicateurs actionnables limites, packaging seulement si UI/vault sont stabilises. |

## Gates novice obligatoires

Aucun chantier UI ne doit etre declare `INTEGRE` ou GO produit uniquement sur
la base de tests HTML ou de routes 200. La cloture doit fournir au minimum:

- route(s) reelles testees;
- scenario utilisateur en une phrase;
- preuve navigateur ou justification explicite si non applicable;
- verification desktop et mobile, ou ticket de dette explicite;
- absence de CTA trompeur ou coupe;
- H1/titre/menu coherents;
- aide accessible autrement que par `title` seul;
- verdict GO/NO-GO novice;
- preuve que l'action est reliee a preuve, diffusion et trace.

## Impacts gouvernail

- `RM-2026-0003` reste le chantier produit central, mais sa prochaine action
  devient l'action inbox/cockpit et les boucles courtes issues de l'enquete.
- `RM-2026-0006` passe en P0 actif: la qualite live doit prouver
  l'utilisabilite novice, pas seulement la stabilite serveur.
- `RM-2026-0009` passe de l'etude a la roadmap: l'onboarding devient le cadre
  novice des 30 prochains jours, rattache a `RM-2026-0003` et `RM-2026-0006`.
- Les anciennes roadmaps restent des sources historiques. Le sequencement
  actif est celui du gouvernail.
