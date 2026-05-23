# Audit gouvernail - maturite proche issue des retours agiles

Date: 2026-05-23

Perimetre: challenge du gouvernail `docs/roadmap_backlog_central.md` au regard
des retours equipes agiles, tests novices, QA live et tests locaux relances.

## Verdict

Le gouvernail est pertinent sur le cap: `preuve + action + memoire`, avec
qualite novice et socle DB comme verrous P0. Son risque actuel est la surcharge:
trop d'items P0 ou ACTIF peuvent donner la meme valeur a une fonctionnalite
presque livrable, un chantier bloque, une ambition structurante et un audit
specialise.

Pour piloter la maturite, il faut donc separer:

- priorite strategique: important pour le produit;
- maturite technique: code, tests, perf et anti-fuite solides;
- maturite utilisateur: un novice peut accomplir une boucle courte sans aide;
- maturite de diffusion: export, partage ou sync ne fuite pas de donnees.

Une fonctionnalite approche de la maturite seulement si elle tient ces quatre
questions: quoi traiter, quelle preuve, quelle action, quelle trace ou diffusion
prudente.

## Fonctionnalites proches de maturite

| Rang | Fonctionnalite | Maturite actuelle | Pourquoi elle est proche | Dernier verrou avant GO |
|---:|---|---|---|---|
| 1 | Couloir `piece manquante -> detail piece -> relance -> depot` | Release candidate conditionnelle | Boucle utilisateur concrete, routes reelles, token conserve, detail compact, depot contextualise, gate live et tests cibles verts. | Rejouer en navigateur sur instance reelle avec temps cible 3-5 s et preuve multi-viewport stable. |
| 2 | Relance syndic locale sans envoi automatique | Proche produit | Le brouillon est prudent, contextualise depuis demande ou piece, et ne pretend pas envoyer. Les tests couvrent token, etat vide, pre-remplissage et absence de faux envoi. | Consolider la trace d'envoi hors CoproScope: date, canal, personne, prochaine verification, puis rattacher proprement a action/preuve. |
| 3 | Read model public `pieces manquantes` | Mature technique sur un premier cas | Allowlist publique, pas de `SELECT *`, pas de FTS/MATCH, fallback vide prudent, pas de build dashboard au GET; tests relances localement OK. | Generaliser au read model `/actions` sans perdre l'anti-fuite ni recreer la lenteur du dashboard global. |
| 4 | Passation prudente avec blocages | Proche sur l'apercu et les blocages | Exports derives JSON/TXT, blocages explicites, liens token-safe, non-source-de-verite, tests anti-fuite solides. | Ne pas declarer la passation globale mature tant que `/exports/passation` reste lente sur instance reelle; garder le GO aux sous-surfaces rapides. |
| 5 | AG/contentieux precontentieux derive | Proche pour usage expert borne | Plan actionnable, rapports anonymises, controles privacy/audit, route specialisee allegee et rapide. | Ne pas la vendre comme assistant juridique autonome; rester sur aide a pieces, reserves, demandes et seuils de decision humaine. |
| 6 | Frontiere publication `share-audit` / `share-export` | Mature comme garde-fou | Les sorties publiables sont scannees et bloquent chemins locaux, tokens, secrets et contenus interdits. | Ajouter une recette utilisateur: que comprend un non-tech quand une publication est bloquee ? |

## Fonctionnalites a ne pas surestimer

| Fonctionnalite | Statut reel | Challenge gouvernail |
|---|---|---|
| Installable noob Drive chiffre | Strategique, pas proche release | Le bootstrap CLI et la checklist existent, mais OAuth, vraie connexion Drive, assistant et parcours sans terminal restent bloquants. |
| Onboarding | Cadre produit pertinent, pas encore fonctionnalite mature | Il fixe les criteres de sortie, mais les quatre intentions ne sont pas encore toutes rejouables sans aide. |
| Registre `/actions` complet | Stable en consultation, pas mature en creation | Les routes passent, mais `Nouvelle action`, rattachement decision, preuve, echeance et responsable doivent devenir un vrai flux createur. |
| Controle comptes guide | Amorce forte | La lecture et les questions syndic sont utiles, mais le parcours anomalie -> question -> relance/preuve -> rapport AG reste incomplet. |
| Memoire/passation complete | Direction claire | Il existe une passation amont et des details, pas encore une timeline centrale de reprise avec pack transmissible complet. |
| Gouvernance complexe, multi-coffres, anti-confiscation UI | Differenciant long terme | A garder haut dans la vision, mais pas a melanger avec les candidats a maturite proche. |

## Challenge des priorites du gouvernail

1. `RM-2026-0003`, `RM-2026-0006` et `RM-2026-0016` forment le bon triangle de
   maturite proche: UX utile, gates novice, performance/read models.
2. `RM-2026-0014` est bien P0 strategique, mais ne doit pas aspirer les cycles
   de maturite tant que le JSON OAuth, le vrai upload Drive et l'assistant noob
   ne sont pas debloques.
3. `RM-2026-0008` est tres utile pour l'urgence audit/AG, mais doit rester un
   couloir borne. S'il devient le centre produit, il risque de detourner la
   maturite du coeur reutilisable: pieces, demandes, actions, preuves,
   passation.
4. `RM-2026-0017` peut etre excellent comme banc de preuve reel/test, mais il
   ne doit pas remplacer la maturation des read models. Sa valeur est de
   verifier la robustesse, pas d'ouvrir un second produit.

## Challenge sans IA cloud

Objectif produit: maximiser ce qui peut etre fait en local, sans envoyer les
pieces, textes OCR, noms, chemins, mails ou rapports vers une IA cloud.

| Fonctionnalite | Potentiel sans IA cloud | Ce qui doit rester local/deterministe | Risque si on la confie trop vite au cloud |
|---|---|---|---|
| `piece manquante -> detail -> relance -> depot` | Tres eleve | Completeness par registres, checklist pieces attendues, liens action/preuve, templates de relance, depot contextualise, OCR local si besoin. | Envoyer des pieces ou raisons de manque sensibles pour obtenir une reformulation qui peut etre produite par gabarit. |
| Relance syndic locale | Tres eleve | Brouillons par modele, variables controlees, ton factuel, copie manuelle, journal d'envoi externe. | Transformer une relance probatoire en texte IA non source, trop assertif ou juridiquement imprudent. |
| Read model public `pieces manquantes` | Maximal | SQLite/projections locales, allowlist de colonnes, statuts, liens, fallback vide, tests anti-fuite. | Aucun besoin cloud; si du cloud intervient ici, c'est un signal d'architecture trop floue. |
| Passation prudente avec blocages | Eleve | Export structure, listes de sujets ouverts, blocages, restrictions, preuves manquantes, biffage local, validation humaine. | Generer une synthese cloud contenant trop de contexte ou donnant une fausse certitude sur ce qui est diffusable. |
| AG/contentieux precontentieux | Moyen a eleve si borne | Extraction locale, checklists AG, pieces P1, reserves, echeances, preuves citees, rapports a trous avec prudence. | Faire porter au cloud le raisonnement juridique ou exposer une convocation/requete sensible, meme anonymisee imparfaitement. |
| `share-audit` / `share-export` | Maximal | Scans de contenu, denylist/allowlist, biffage, blocage, manifestes bornes, tests canari. | Faire du cloud un juge de confidentialite; il doit au mieux recevoir une derive deja anonymisee, jamais decider seul. |

Conclusion: les candidats les plus compatibles avec l'objectif "sans IA cloud"
sont, dans l'ordre, les read models publics, la boucle pieces/relance/depot, la
relance locale et les frontieres de publication. Le module AG/contentieux et les
syntheses de passation doivent rester utiles sans cloud, avec l'IA eventuelle
limitee a un second regard sur derives anonymisees, jamais au chemin critique.

Regle d'arbitrage proposee: une fonctionnalite monte en priorite si elle
remplace un appel IA cloud potentiel par une primitive locale verifiable:
projection SQLite, OCR local, gabarit, checklist, extraction citee, biffage,
journal d'action ou export derive.

## Recommandation de sequence

### Lot A - Passer en maturite produit courte

- Verrouiller le couloir `pieces -> detail -> relance -> depot`.
- Exiger navigateur multi-viewport + instance reelle + cible 3-5 s.
- Nettoyer tout vocabulaire `demo`, `fictif`, `test` au premier niveau.
- Produire un verdict GO/NO-GO novice verbalise.

### Lot B - Transformer le socle DB en maturite reutilisable

- Construire `/actions` en read model public versionne.
- Garder les memes exigences que `pieces manquantes`: allowlist, projection
  meta, fallback vide, pas de DDL au GET, pas de fuite `source_file`/`chemin`.
- Mesurer `/actions?priority=P1`, `/actions?scope=syndic` et
  `/actions?status=a_demander`.

### Lot C - Fermer la boucle produit

- Relier `comptes -> question syndic -> relance -> preuve attendue`.
- Faire de `/actions` le pivot createur minimal.
- Declarer la passation mature seulement quand les sujets ouverts, blocages,
  preuves et restrictions sont transmissibles sans lenteur ni ambiguite.

## Verification locale

Panier relance depuis `server/` le 2026-05-23:

```text
python -m unittest tests.test_public_read_models tests.test_ui_piece_detail_route tests.test_ui_requests_route tests.test_ui_agcontentieux_route tests.test_ui_passation_export_route tests.test_ui_smoke_routes_expanded -v
Ran 49 tests in 25.022s
OK
```

Ce resultat confirme une maturite technique forte sur les surfaces ciblees. Il
ne suffit pas a lui seul pour un GO produit global: le gate novice navigateur,
les temps reponse reels et la boucle complete restent les juges finaux.

## Resultat equipe agile lancee

Le 2026-05-23, trois lots ont ete lances et integres dans le workspace
principal sous contrainte "sans IA cloud":

- Rawls / lot A: lecteur public `public_actions_v1` ajoute, avec allowlist,
  controle `projection_meta`, fallback vide, pas de `SELECT *`, pas de
  FTS/MATCH, pas de DDL persistant au GET. Verdict: GO technique lecteur,
  GO produit reporte tant que la route `/actions` n'est pas branchee dessus.
- Meitner / lot B: couloir novice `piece -> relance -> depot` clarifie; piece
  concernee, raison, prochaine action, relance non envoyee, depot/reponse et
  prudence diffusion sont visibles sans vocabulaire demo/fictif/DocAI au premier
  niveau. Verdict: GO technique local-first, live navigateur encore a faire.
- Chandrasekhar / lot C: passation/share renforces contre secrets OAuth,
  refresh token, OpenAI `sk-*`, Bearer token et elargissement prive
  `scope=event -> global`. Verdict: GO technique anti-fuite.

Verification commune depuis `server/`:

```text
python -m unittest tests.test_public_read_models tests.test_code_line_limit tests.test_vault tests.test_ui_piece_detail_route tests.test_ui_requests_route tests.test_ui_depot_flow tests.test_ui_live_ux_contract tests.test_ui_passation_export_route tests.test_security_no_private_sync_leaks tests.test_pipeline tests.test_privacy tests.test_audit360_import tests.test_gdriveops tests.test_ui_smoke_routes_expanded -v
Ran 117 tests in 39.835s
OK (skipped=1)
```

Le skip est attendu: aucun serveur live n'etait lance sur `127.0.0.1:8766`.
Le prochain verrou produit est donc net: brancher `/actions` sur son read model
public, puis faire une passe navigateur live/multi-viewport sur le couloir
novice complet.
