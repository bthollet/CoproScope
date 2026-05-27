# Equipe agile - Suite ajout documents apres integration DocOps feedback

Date de lancement: 2026-05-24 21:52 +02:00.
Roadmap: `RM-2026-0003`.
Chantier: `CH-20260524-215200-RM-2026-0003-post-docops-ajout-docs`.
Conversation coordination: `CONV-2026-1581`.
Mode: micro-equipe agile lecture seule, sans dev, sans serveur, sans instance privee.
Statut: pret a integrer.

## BOT-START

BOT-START - Coordinateur-scribe suite ajout-docs - 2026-05-24 21:52 +02:00.

Mission: apres integration locale de `/documents/tri-feedback`, choisir le
prochain increment fonctionnel utile pour le parcours novice ajout de documents:
recette future, lien atelier ajout -> tri feedback, explication des restrictions
et sortie testable.

Ownership modifiable: ce document, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`.

Fichiers a eviter: code applicatif, tests, CSS, templates, serveurs locaux,
ports, instances privees, documents bruts, exports bruts, secrets,
`RM-2026-0017`, et tout fichier sale hors documentation de coordination.

Roles:

- `CONV-2026-1581`: coordinateur-scribe local;
- `CONV-2026-1582`: designer service / parcours novice;
- `CONV-2026-1583`: utilisateur novice / membre conseil syndical;
- `CONV-2026-1584`: QA privacy / regression produit.

Livrable attendu: commande courte du prochain increment, GO/NO-GO novice,
risques privacy, preuves/tests attendus et decision explicite sur l'absence de
preuve navigateur dans ce cycle.

## Journal

| Heure | Acteur | Evenement | Detail |
|---|---|---|---|
| 2026-05-24 21:52 +02:00 | `CONV-2026-1581` | `BOT-START` | Micro-equipe ouverte apres `CONV-2026-1580`; aucun code, serveur, instance privee, secret, export brut ni `RM-2026-0017`. |
| 2026-05-24 21:56 +02:00 | `CONV-2026-1582` | `DESIGNER_SERVICE` | Parcours recommande: garder `/documents/ajouter` comme point de depart, puis proposer un pont explicite vers `/documents/tri-feedback` quand plusieurs documents ou corrections DocOps sont a traiter. |
| 2026-05-24 21:56 +02:00 | `CONV-2026-1583` | `GO_NOVICE_CONDITIONNEL` | GO si le choix reste volontaire, local et lisible; NO-GO si l'app force le tri, expose chemins/hash/OCR, ou presente `Reserve CS` et `A masquer` comme des libelles techniques non expliques. |
| 2026-05-24 21:56 +02:00 | `CONV-2026-1584` | `QA_PRIVACY` | Panier futur borne aux routes ajout-docs, tri-feedback, securite, anti-fuite et garde-fou 600 lignes; aucune preuve navigateur dans ce cycle car aucun port n'a ete reserve. |
| 2026-05-24 21:56 +02:00 | `CONV-2026-1581` | `AGILE_DONE_POST_DOCOPS_AJOUT_DOCS` | Commande `ajout_docs_tri_bridge_v1` consolidee; aucun code, serveur, instance privee, secret, export brut ni `RM-2026-0017`. |

## Synthese roles

Designer service: ne pas creer une nouvelle page de promesse. Le bon geste est
un pont court dans l'atelier d'ajout: titre `Corriger une file de documents`,
explication en une phrase, action principale `Ouvrir le tri de lot`, action
secondaire `Continuer document par document`.

Utilisateur novice: GO conditionnel. Le membre du conseil syndical comprend si
le fichier reste local, si DocOps propose et si lui confirme. Il bloque si
l'ecran parle de hash, d'OCR, de registre interne, de chemin local ou de
restriction sans resultat concret.

QA privacy/regression: le pont doit etre purement declaratif et volontaire. Il
ne doit pas relancer DocOps, deplacer un fichier, creer un export, ni modifier
une instance privee. Les libelles sensibles doivent expliquer les consequences:
`Reserve CS demande un motif`, `A masquer demande des pages ou plages`, `A
decider plus tard ne diffuse rien`.

## Commande prete

`ajout_docs_tri_bridge_v1`

Ajouter dans `/documents/ajouter` un pont vers le prototype deja integre
`/documents/tri-feedback`.

Comportement attendu:

- afficher le pont apres le depot local ou quand l'atelier contient plusieurs
  documents a classer;
- ne jamais rediriger automatiquement vers le tri de lot;
- garder `Continuer document par document` comme sortie visible;
- rappeler que le fichier reste local et que rien n'est partage;
- reutiliser le registre de feedback DocOps existant, sans nouvelle
  persistance;
- si l'etat d'ajout connait une file ou une source inbox, revenir vers
  `/documents/ajouter?source=inbox` apres tri incomplet ou sensible.

Hors scope explicite:

- pas de colonnes drag/drop;
- pas de relance DocOps automatique;
- pas de refonte globale de l'atelier;
- pas de serveur live;
- pas d'instance privee;
- pas de reprise de `RM-2026-0017`.

## Gates

GO novice pour ouvrir un chantier dev separe si:

- le pont nomme clairement le tri de lot;
- le choix reste volontaire;
- les restrictions sont traduites en consequences pratiques;
- l'ecran ne montre aucun chemin local, secret, hash brut, identifiant OCR ou
  donnee d'instance.

NO-GO si:

- le tri est force;
- `Reserve CS` devient une option de securite fourre-tout;
- `A masquer` peut etre valide sans pages ou plages;
- `A decider plus tard` laisse croire a une diffusion;
- le pont ajoute une nouvelle source de verite concurrente au registre DocOps.

## Preuves attendues

Si un chantier dev ou recette s'ouvre, rejouer au minimum:

- `server.tests.test_ui_docops_feedback_route`;
- `server.tests.test_ui_document_intake`;
- `server.tests.test_ui_document_intake_route`;
- `server.tests.test_ui_security_routes`;
- `server.tests.test_security_no_private_sync_leaks`;
- `server.tests.test_code_line_limit`;
- `tools\check_code_line_limit.py`;
- `git diff --check`.

Preuve navigateur: non produite dans ce cycle. Aucun serveur ni port n'a ete
reserve.

## Point court

A produire: commande `ajout_docs_tri_bridge_v1`.
En test: aucun test applicatif lance dans ce cycle documentaire.
Images candidates: aucune nouvelle image; le besoin est un pont UI court, pas
une direction visuelle.
Decisions ouvertes: ouvrir un owner code unique pour le pont, ou reserver un
port pour une preuve navigateur du prototype integre.
Prochain mouvement: chantier separe sur `/documents/ajouter` et
`/documents/tri-feedback`, sans reconstruction Beauvallon reel.

## BOT-END

BOT-END - 2026-05-24 21:56 +02:00.

Livrable pret: commande `ajout_docs_tri_bridge_v1`, GO novice conditionnel,
panier QA et limites privacy. Aucun code, serveur, port, instance privee,
document brut, export brut, secret ou `RM-2026-0017` n'a ete touche.

AGILE-DONE - equipe agile a fini son job.
