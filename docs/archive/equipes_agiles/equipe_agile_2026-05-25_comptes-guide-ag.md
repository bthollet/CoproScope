# Equipe agile - ORD-P0-020 Comptes guide AG

Date de lancement: 2026-05-25 02:38 +02:00.
Mode: equipe agile de cadrage produit, lecture seule, sans dev.

## BOT-START

```text
BOT-START - Coordinateur-scribe agile - 2026-05-25 02:38 +02:00
Roadmap: RM-2026-0003 / RM-2026-0030 / RM-2026-0006
Ordre: ORD-P0-020 / COMPTES-GUIDE-AG
Chantier: CH-20260525-023800-RM-2026-0003-comptes-guide-ag
Conversation: CONV-2026-1666
Role: Coordinateur-scribe agile
Mission: cadrer le prochain lot P0 actionnable apres Audit360: guide de controle des comptes avant AG sur /comptes, avec P1/P2/OK en langage humain, preuve attendue, question syndic et synthese AG prudente.
Ownership modifiable: docs/equipe_agile_2026-05-25_comptes-guide-ag.md, docs/presence_agents.md, trace append-only docs/roadmap_backlog_central.md et heartbeat relance-equipe-agile-gouvernail-autonome.
Fichiers a eviter: code applicatif, tests applicatifs, templates, CSS, worktree principal sale, worktrees prets a integrer sans decision, instances privees, donnees comptables reelles, documents bruts, OCR/logs, exports bruts, secrets, serveurs locaux, push GitHub, RM-2026-0017 / ORD-P0-990, reouverture ORD-P0-010/011/012 sans nouveau diff ou decision Brice.
Dernier point lu: AGENTS.md, protocoles equipe agile/orchestration/roadmap/presence, consignes interconversations, gouvernail, presence, mission ORD-P0-012 cloturee, docs/commande_cycle3_controle_comptes.md, docs/comptascope.md, docs/equipe_agile_2026-05-24_compta-multisources-verrouillage.md.
Tests/preuves attendus: retours designer/novice/front/back/QA, GO/NO-GO novice, cible UI reelle /comptes, comparaison au visuel controle-comptes-guide, contrat model.ux.comptes borne, panier security/privacy/no-private/line-limit/smoke, decision explicite avant tout owner code.
Risque de collision: worktree principal sale; RM-2026-0030 contient deja un cadrage PRET_A_INTEGRER sur /comptes/rapprochement. Ce lot reste borne a /comptes guide AG et ne lance aucun dev.
Lease ownership: jusqu'au 2026-05-25 04:38 +02:00.
Prochaine action: lancer les roles designer, novice, front, back/viewmodel et QA en lecture seule, puis consolider une commande future bornee ou un NO-GO dev.
```

## Etat initial

- A tester maintenant: pas de recette live; aucun serveur reserve.
- En dev maintenant: aucun dev; aucun owner code ouvert.
- En enquete maintenant: roles a lancer en lecture seule sur `/comptes`.
- Commande prete: ancienne commande Cycle 3 existe, mais elle doit etre
  requalifiee contre le gouvernail `ORD-P0-020` et les cadrages compta recents.
- Comparaison visuels enquete: reference obligatoire
  `docs/assets/etude-utilisateurs/controle-comptes-guide.png`.
- Agents idle a relancer: designer, novice, front, back/viewmodel et QA.
- Decision requise: aucune decision Brice immediate. Un owner code futur doit
  etre explicite et en worktree dedie.
- Prochain mouvement: lancer les roles et recuperer les retours.
- Tests/preuves: `git diff --check` documentaire; aucun test applicatif tant
  qu'aucun code n'est livre.

## Roles

| Conversation | Role | Statut | Agent |
|---|---|---|---|
| `CONV-2026-1666` | Coordinateur-scribe agile | CLOTURE | local |
| `CONV-2026-1667` | Designer service / facilitateur | CLOTURE | Fermat `019e5c94-f9fb-7753-8455-5d66bde9e2e1` |
| `CONV-2026-1668` | Utilisateur novice / membre CS | CLOTURE | Bohr `019e5c94-fa59-7783-98cf-cc1fcfc4412a` |
| `CONV-2026-1669` | Dev front lecture seule | CLOTURE | Huygens `019e5c94-fac8-7e61-81b6-3ac47a7b436e` |
| `CONV-2026-1670` | Dev back / viewmodel lecture seule | CLOTURE | local, reprise faute capacite threads |
| `CONV-2026-1671` | QA privacy / regression | CLOTURE | local, reprise faute capacite threads |

## Contraintes produit

- `/comptes` doit aider un membre CS non comptable a preparer l'AG.
- Le produit ne valide pas une comptabilite officielle.
- Les codes `P1`, `P2` et `OK` ne doivent jamais porter seuls la comprehension.
- Chaque ligne ouverte doit dire: quoi verifier, quelle preuve manque ou existe,
  quelle question syndic preparer et si le point peut entrer dans une synthese
  AG.
- Les questions syndic restent des brouillons relus/copies humainement; aucun
  bouton ne pretend envoyer un mail.
- Les exports ou rapports AG sont des derives prudents, avec diffusion et
  blocages visibles.
- Les donnees de cadrage restent fictives, publiques de test ou deja
  anonymisees.

## Retour designer - CONV-2026-1667

Verdict: GO design pour `/comptes` guide AG. NO-GO dev immediat tant que le
retour novice, l'owner front/back unique et le contrat `model.ux.comptes` ne
sont pas verrouilles.

Reference a conserver: `docs/assets/etude-utilisateurs/controle-comptes-guide.png`.
La structure utile est: sidebar sombre, KPI cliquables, tableau central,
inspecteur droit et carte rapport AG.

Premier viewport recommande:

- titre `Controle des comptes`;
- exercice visible;
- bouton `Exporter le rapport`, mais derriere une revue de perimetre;
- bandeau `Suggestions de controle, pas comptabilite officielle`;
- KPI cliquables;
- tableau `Depenses par categorie`;
- inspecteur droit ouvert sur la premiere categorie non OK.

Microcopy statuts:

- `OK`: `Preuve locale suffisante`, avec lien vers la preuve ou raison de
  non-question;
- `P2 a confirmer`: `Indice plausible, confirmation syndic ou piece attendue`;
- `P1 a traiter avant AG`: `Preuve manquante ou blocage a verifier en priorite`.

Interactions attendues:

- clic categorie -> inspecteur `Detail`;
- clic alerte -> pieces concernees ou question associee;
- onglet `Pieces` -> justificatifs, preuves candidates, preuves verifiees et
  pieces a demander;
- onglet `Questions au syndic` -> brouillons editables/copiables, jamais
  envoyes automatiquement;
- carte `Rapport AG` -> inclure seulement les points ouverts selectionnes avec
  niveau de diffusion obligatoire.

No-go design:

- statut porte par couleur ou code seul;
- bouton qui laisse croire a un envoi syndic;
- rapport AG exportant notes internes, chemins locaux ou conclusions comptables
  definitives;
- tirets muets visibles: remplacer par `Montant non charge`,
  `Aucun ecart detecte`, `Date non lue` ou equivalent.

## Retour novice - CONV-2026-1668

Verdict: GO cadrage conditionnel, NO-GO dev complet pour l'instant.

Un membre CS non comptable comprend `/comptes` en moins d'une minute seulement
si la page parle en actions humaines, pas en codes. Si l'ecran affiche surtout
`P1`, `P2`, `OK`, categories comptables et ratios, il ne sait pas assez vite
quoi faire.

Lecture attendue:

- `P1` doit devenir `A traiter avant AG`: preuve ou explication bloquante
  manquante, avec action visible;
- `P2` doit devenir `A confirmer avec le syndic ou une piece`: point plausible
  mais non valide;
- `OK` doit devenir `OK avec preuve`: preuve locale ou raison explicite de ne
  pas poser de question.

Libelles qui marchent: `Controle des comptes`, `lignes de comptes regardees`,
`factures retrouvees`, `a traiter avant AG`, `a confirmer`,
`OK avec preuve`, `piece qui peut servir de preuve`, `preuve rattachee`,
`piece a demander`, `copier la question`, `marquer envoyee hors CoproScope`,
`ajouter une note AG`, `preparer le rapport AG`.

Mots dangereux: `P1` seul, `P2` seul, `NON_RAPPROCHE` seul, `anomalie` sans
prudence, `validation comptable`, `comptabilite officielle`, `envoyee` sans
confirmation humaine, `preuve validee` pour une simple piece candidate,
`exporter` sans public de lecture, chemins locaux ou bruts sensibles.

Question syndic: chaque point ouvert doit produire une question lisible et
prudente avec contexte, piece attendue, facture/ligne si disponible et
consequence si la reponse manque avant AG. CoproScope prepare, copie et trace;
il n'envoie pas.

Rapport AG: reprendre seulement les points selectionnes, avec diffusion
lisible: interne CS, diffusable AG, a relire ou bloque. Ne pas copier chemins,
commentaires internes, bruts ou transformer un indice local en accusation.

Phrase-cle a garder: CoproScope aide le conseil syndical a controler et
expliquer; il ne remplace pas le grand livre, l'etat officiel des depenses ni
la validation humaine.

Conditions avant dev: UI cible explicite, test novice centre sur la question
`quelle demande au syndic puis-je preparer ?`, ownership front/back arbitre,
contrat `model.ux.comptes` stabilise et tests anti-jargon/anti-fuite/export
prudent prevus.

## Retour back/viewmodel - CONV-2026-1670

Verdict: contrat public deja partiellement livre et testable en lecture seule.
Le role n'a pas pu etre lance comme sub-agent faute de capacite; reprise locale
par le coordinateur, sans patch code.

Surface lue:

- `server/src/coproscope/web/viewmodels/_comptes_builder.py`;
- `server/src/coproscope/web/viewmodels/_comptes_builder_fragments/`;
- `server/src/coproscope/web/viewmodels/_comptes_common.py`;
- `server/src/coproscope/web/viewmodels/_comptes_fields.py`;
- `server/src/coproscope/web/viewmodels/_accounting_questions.py`;
- `server/src/coproscope/web/templates/accounting.html`;
- `server/tests/test_ui_comptes_guide.py`.

Contrat cible a conserver: `model.ux.comptes`.

Objets publics attendus et deja couverts par les tests existants:

- `context`: coffre, mode prive local, role CS, exercice, periode, source et
  date;
- `summary` et `kpis`: total, factures rapprochees, P1/P2, pieces manquantes,
  questions, rapport AG et hrefs;
- `facets` / `filters`: exercice, categorie, statut, fournisseur, preuve,
  piece, alerte, inclusion AG, rapprochement;
- `categories[]`: libelle, montant, ratio, statut humain, alertes, questions,
  prochaine action, href;
- `selected`: resume novice, alertes, pieces, questions, diffusion, historique
  et note memoire;
- `questions_syndic[]`: brouillons copiables avec statut, preuve attendue,
  diffusion et href;
- `ag_report`: inclus/exclus, P1/P2, pieces manquantes, questions ouvertes,
  notes, preview, diffusion et export;
- `empty_states` et `export`: etats vides actionnables et export derive.

Sources autorisees pour un futur owner code: sorties ComptaScope synthetiques
ou test (`invoice_evidence`, `invoice_anomalies`, `accounting_controls`,
`controle_comptes_guide`, `regroupement_controle_comptes`,
`questions_syndic_comptascope`, `rapport_comptascope`), fixtures unitaires et
`examples/synthetic_copro`. Les instances privees et donnees comptables reelles
restent exclues.

Champs et marqueurs interdits dans JSON/HTML/export/test fixture public:
chemins locaux, `file://`, `raw`, `restricted`, `logs`, `private`, tokens,
secrets, emails, telephones, IBAN/RIB, OCR brut, exports bruts,
`source_path`, `source_file`, `original_path`, `original_name`,
`payload_json`, hash/source SHA prive, notes internes non nettoyees.

Tests back cibles: `tests.test_ui_comptes_guide` couvre deja la projection
`model.ux.comptes`, masquage de chemins, hrefs locaux, P1/P2 non seuls,
questions, rapport AG et etats vides. Ajouter un futur test dedie seulement si
un owner code modifie le contrat.

## Retour QA - CONV-2026-1671

Verdict: GO technique local sur tests existants, NO-GO produit complet sans
recette navigateur live et captures desktop/mobile/tablette. Le role n'a pas
pu etre lance comme sub-agent faute de capacite; reprise locale par le
coordinateur, sans patch code.

Preuves executees:

```text
python tools/check_code_line_limit.py
OK: no scoped code file exceeds 600 lines.

Depuis server/:
.\.venv\Scripts\python.exe -m unittest tests.test_ui_comptes_guide -v
10 tests OK.

Depuis server/:
.\.venv\Scripts\python.exe -m unittest tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v
12 tests OK.
```

Panier QA futur si un owner code touche `/comptes`:

- token: `/comptes`, hrefs internes, exports et routes liees conservent le
  token et font 403 sans token configure;
- anti-fuite: aucun chemin local, `file://`, `raw`, `restricted`, `logs`,
  `private`, secret, email, telephone, IBAN/RIB, OCR brut ou export brut;
- langage novice: `P1`, `P2`, `NON_RAPPROCHE` jamais seuls;
- non-comptabilite-officielle: affichage permanent que CoproScope aide le CS
  mais ne valide pas les comptes officiels;
- questions syndic: brouillons a relire/copier/tracer, aucun envoi automatique;
- rapport AG: derive, perimetre selectionne, diffusion lisible et blocage des
  notes internes;
- responsive: capture desktop/mobile/tablette du premier viewport et de
  l'inspecteur, sans chevauchement ni scroll horizontal;
- line-limit: tous fichiers code/templates/tests sous 600 lignes;
- smoke/regression: `test_ui_comptes_guide`, security, no-private,
  smoke routes, passation exports si rapport/exports sont touches.

Limite QA: aucun serveur reserve, aucune capture navigateur et aucune recette
utilisateur live pendant ce lot.

## Retour front - CONV-2026-1669

Verdict: GO cadrage, NO-GO dev immediat dans ce fil. `/comptes` existe deja et
le contrat `model.ux.comptes` est present, mais le template consomme encore
surtout `model.accounting.*`. Aucun fichier modifie, aucun serveur lance.

UI actuelle:

- route `/comptes` dans `server/src/coproscope/web/_app_fragments/part_003.pyfrag`;
- template `server/src/coproscope/web/templates/accounting.html`;
- navigation `Controle comptes` dans `server/src/coproscope/web/templates/base.html`;
- CSS principal dans `styles_part_07.css`, media queries dans
  `styles_part_08.css`;
- `model.ux.comptes` construit par `viewmodels/_comptes_builder.py` et ses
  fragments;
- tests dedies dans `server/tests/test_ui_comptes_guide.py`.

Risques front:

- `part_003.pyfrag` est proche du plafond, annonce a 597 lignes par Huygens:
  ne rien ajouter dedans sans extraction de route;
- les hrefs de `model.ux.comptes` sont sans token: le rendu doit toujours
  passer par `token_href`;
- mismatch query: template utilise `status`, `exercise`, `show_empty`, tandis
  que l'UX model genere aussi `statut`, `exercice`, `show_solded_lines`;
- toute future sous-route `/comptes/...` doit etre declaree avant le catch-all;
- mobile actuel empile et garde des tableaux en scroll horizontal, alors que la
  cible demande une liste de categories et un inspecteur en tiroir ou page.

Commande front future bornee:

- garder `/comptes` comme cible unique du premier lot;
- utiliser `?categorie=<id>&tab=detail|pieces|questions|rapport-ag&status=p1|p2|ok&proof_state=missing`;
- faire consommer `model.ux.comptes` par le template au lieu de dupliquer
  `model.accounting.*`;
- extraire `accounting.html` en includes `_comptes_*.html` si le patch devient
  significatif;
- creer un fichier CSS dedie, par exemple `styles_part_14.css`, plutot que
  grossir les parts existantes;
- eviter `part_003.pyfrag` sauf extraction route dediee;
- couvrir route 200/403, token conserve, KPI cliquables, onglets actifs par
  `tab`, libelles P1/P2 humains, anti-fuite et mobile.

No-go front: pas de patch dans ce fil, pas d'instance privee, pas d'export brut,
pas de secret, pas de chemin prive, pas de `RM-2026-0017`, pas d'ajout dans
`part_003.pyfrag` sans extraction, pas de bouton qui pretend envoyer au syndic
et pas d'export rapport AG sans revue de diffusion.

## Consolidation ORD-P0-020

Verdict equipe: `AGILE-DONE - equipe agile a fini son job`.

- A tester maintenant: pas de serveur live reserve; tests unitaires cibles OK.
- En dev maintenant: aucun dev ouvert; aucun patch code.
- En enquete maintenant: tous les roles canoniques sont clotures.
- Commande prete: oui, comme commande future bornee, pas executee.
- Comparaison visuels enquete: le lot reprend
  `docs/assets/etude-utilisateurs/controle-comptes-guide.png`.
- Agents idle a relancer: aucun sans nouveau diff ou decision d'owner code.
- Decision requise: Brice doit decider explicitement s'il veut une reprise code
  dediee de `/comptes`; sinon le heartbeat passe au prochain `ORD-*`
  actionnable.
- Prochain mouvement: prochain heartbeat = lire la file `ORD-*` et choisir le
  prochain P0 actionnable, en excluant les lots `PRET_A_INTEGRER` sans decision
  d'integration et les lots `AGILE-DONE` sans nouveau diff.
- Tests/preuves: `test_ui_comptes_guide` 10 OK, security/no-private 12 OK,
  `tools/check_code_line_limit.py` OK, `git diff --check` documentaire a
  lancer.

Commande future bornee:

```text
Roadmap/chantier:
RM-2026-0003 / RM-2026-0030 / RM-2026-0006 / nouveau CH owner code dedie a
creer si Brice valide.

Objectif:
Stabiliser /comptes comme guide de controle des comptes avant AG pour un membre
CS non comptable: action humaine, preuve attendue, question syndic et synthese
AG prudente.

UI cible:
Route /comptes. Premier viewport: Controle des comptes, exercice, bandeau
Suggestions de controle - pas comptabilite officielle, KPI cliquables, tableau
Depenses par categorie, inspecteur droit sur la premiere categorie non OK.

Contrat donnees:
model.ux.comptes comme source UI: context, summary/kpis, facets/filters,
categories, selected, pieces, questions_syndic, ag_report, tabs, empty_states
et export. Ne pas dupliquer depuis model.accounting.* dans le template.

Interactions:
Filtrer P1/P2/OK, ouvrir une categorie, voir detail/pieces/questions/rapport,
copier une question, marquer envoyee hors CoproScope, rattacher une reponse,
ajouter une note AG et preparer un rapport derive. Aucun envoi automatique.

Front:
Extraire si besoin route/template avant ajout: part_003.pyfrag est proche du
plafond. Template accounting.html a reduire en includes _comptes_*.html si le
patch est large. CSS dedie possible styles_part_14.css.

Garde-fous:
P1/P2 jamais seuls; OK = OK avec preuve; CoproScope ne remplace pas la
comptabilite officielle; export AG derive avec diffusion interne CS / diffusable
AG / a relire / bloque; token conserve; aucun chemin prive ni brut.

Tests:
test_ui_comptes_guide, test_ui_security_routes,
test_security_no_private_sync_leaks, test_ui_smoke_routes_expanded,
test_code_line_limit, tools/check_code_line_limit.py, git diff --check,
captures desktop/mobile/tablette sur port reserve si recette live demandee.
```

## Sources de decision

- `docs/commande_cycle3_controle_comptes.md`
- `docs/comptascope.md`
- `docs/assets/etude-utilisateurs/controle-comptes-guide.png`
- `docs/equipe_agile_2026-05-24_compta-multisources.md`
- `docs/equipe_agile_2026-05-24_compta-multisources-verrouillage.md`
- `docs/roadmap_backlog_central.md`
- `docs/presence_agents.md`

## Journal

| Horodatage | Conversation | Evenement | Trace |
|---|---|---|---|
| 2026-05-25 02:38 +02:00 | `CONV-2026-1666` | `START_AGILE_COMPTES_GUIDE_AG` | `ORD-P0-012` est `AGILE-DONE`; nouveau chantier P0 ouvert sur `ORD-P0-020` en lecture/cadrage uniquement, sans code ni serveur. |
| 2026-05-25 02:38 +02:00 | `CONV-2026-1667`..`CONV-2026-1671` | `ROLES_RESERVED_COMPTES_GUIDE_AG` | Designer, novice, front, back/viewmodel et QA reserves en lecture seule; aucun code, serveur, instance privee, donnee comptable reelle, export brut, secret ou `RM-2026-0017`. |
| 2026-05-25 02:39 +02:00 | `CONV-2026-1667`..`CONV-2026-1669` | `AGENTS_LAUNCH_PARTIAL_COMPTES_GUIDE_AG` | Designer Fermat, novice Bohr et front Huygens lances en lecture seule; back/viewmodel et QA restent reserves faute de capacite de threads. Aucun code, serveur, instance privee, donnee comptable reelle, export brut, secret ou `RM-2026-0017`. |
| 2026-05-25 02:40 +02:00 | `CONV-2026-1667` | `DESIGNER_RETURN_COMPTES_GUIDE_AG` | Fermat cloture: GO design, NO-GO dev immediat; conserver la structure du visuel `controle-comptes-guide.png`, microcopy P1/P2/OK humaine, questions syndic sans envoi auto, rapport AG avec diffusion obligatoire. |
| 2026-05-25 02:40 +02:00 | `CONV-2026-1668` | `NOVICE_RETURN_COMPTES_GUIDE_AG` | Bohr cloture: GO cadrage conditionnel, NO-GO dev complet si l'ecran reste centre sur codes P1/P2/OK, ratios et categories; chaque point doit dire action, preuve, question syndic et diffusion AG. |
| 2026-05-25 02:41 +02:00 | `CONV-2026-1670` | `BACK_LOCAL_RETURN_COMPTES_GUIDE_AG` | Reprise locale faute de thread: contrat `model.ux.comptes` deja present et teste; sources synthetiques/test autorisees, champs interdits et tests back futurs consolides. |
| 2026-05-25 02:41 +02:00 | `CONV-2026-1671` | `QA_LOCAL_RETURN_COMPTES_GUIDE_AG` | Reprise locale faute de thread: line-limit OK, `test_ui_comptes_guide` 10 OK, security/no-private 12 OK; NO-GO produit complet sans recette navigateur et captures. |
| 2026-05-25 02:44 +02:00 | `CONV-2026-1669` | `FRONT_RETURN_COMPTES_GUIDE_AG` | Huygens cloture: `/comptes` existe, `model.ux.comptes` existe, mais le template consomme surtout `model.accounting.*`; commande future = basculer proprement vers `model.ux.comptes`, normaliser query params, garder token et extraire avant tout ajout dans `part_003.pyfrag`. |
| 2026-05-25 02:44 +02:00 | `CONV-2026-1666`..`CONV-2026-1671` | `AGILE_DONE_COMPTES_GUIDE_AG` | Equipe cloturee sans dev: commande future `/comptes` guide AG prete pour owner code dedie si Brice valide; aucun code, serveur, instance privee, donnee comptable reelle, export brut, secret, push GitHub ni `RM-2026-0017`. |
