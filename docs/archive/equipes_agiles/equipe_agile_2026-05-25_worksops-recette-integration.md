# Equipe agile - WorksOps recette integration

Date: 2026-05-25 09:06 +02:00.
Rattachement: `ORD-P0-040`, `RM-2026-0032`.
Chantier: `CH-20260525-090648-RM-2026-0032-worksops-recette-integration`.

## BOT-START - Coordinateur-scribe - 2026-05-25 09:06 +02:00

Roadmap: `RM-2026-0032`.
Chantier: `CH-20260525-090648-RM-2026-0032-worksops-recette-integration`.
Conversation: `CONV-2026-1709`.
Role: coordinateur-scribe agile.
Mission: lancer une equipe agile sur `ORD-P0-040` pour relire le worktree WorksOps `/travaux` deja pret a integrer, qualifier la recette attendue et decider le prochain geste sans patch immediat.
Ownership modifiable: cette trace, `docs/presence_agents.md`, trace append-only `docs/roadmap_backlog_central.md`, heartbeat agile du fil courant.
Fichiers a eviter: code, tests applicatifs, routes, templates, CSS, worktree principal sale, instances privees reelles, documents bruts, OCR/logs, exports bruts, secrets, serveurs non reserves, push GitHub, `RM-2026-0017`, `ORD-P0-990` et reouverture de lots `AGILE-DONE`.
Passerelle/registre de trace: ce fichier et `docs/presence_agents.md`.
Dernier point lu: `AGENTS.md`, `docs/protocole_equipe_agile_agents.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/consignes_bots_interconversations.md`, `docs/orchestration_agents.md`, `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`, `docs/equipe_agile_2026-05-24_worksops-readiness.md`.
Tests/preuves attendus: verdict GO/NO-GO sur integration du worktree `C:\Users\brice\CoproScope\dev\worktrees\coproscope-worksops-travaux-v1-20260525`, panier de reprise, risques d'integration, recette navigateur attendue si un serveur visible est reserve plus tard.
Risque de collision: le travail code WorksOps est deja `PRET_A_INTEGRER`; ne pas le modifier ni l'integrer automatiquement. Le worktree principal est sale.
Lease ownership: 2026-05-25 11:06 +02:00.
Prochaine action: lancer designer, novice, front/integration, back/viewmodel et QA en lecture seule sur le worktree dedie et consolider le prochain geste.

## Point de coordination initial

- A tester maintenant: rien en navigateur tant qu'aucun port n'est reserve. UI cible reelle future: `/travaux`.
- En dev maintenant: aucun dev code; revue lecture seule du worktree WorksOps pret a integrer.
- En enquete maintenant: designer et novice qualifient la valeur utilisateur, le premier viewport, la preuve attendue et la diffusion prudente.
- Commande prete: worktree `/travaux` pret a integrer techniquement selon `CONV-2026-1625`; recette navigateur produit encore manquante.
- Comparaison visuels enquete: utiliser les recherches UX travaux du 2026-05-24 et le cadrage `docs/equipe_agile_2026-05-24_worksops-readiness.md`.
- Agents idle a relancer: designer, novice, front/integration, back/viewmodel et QA.
- Decision requise: aucune integration automatique. Le resultat attendu est un GO/NO-GO d'integration ou un plan de recette.
- Prochain mouvement: attendre les retours des roles; si consensus GO technique maintenu, proposer integration/revue separee, puis recette navigateur quand un serveur est reserve.
- Tests/preuves: `git diff --check` documentaire apres inscription.

## Roles ouverts

| Conversation | Role | Agent | Statut |
|---|---|---|---|
| `CONV-2026-1710` | Designer service / facilitateur | Popper `019e5df6-5a7b-7532-ba59-934680b91da6` | CLOTURE |
| `CONV-2026-1711` | Utilisateur novice / membre CS | Carson `019e5df6-5b2f-7653-94e0-f8d5b14f24c2` | CLOTURE |
| `CONV-2026-1712` | Dev front / integration lecture seule | Erdos `019e5df6-5f2d-7873-aebc-24d6263394a2` | CLOTURE |
| `CONV-2026-1713` | Dev back / viewmodel lecture seule | Hegel `019e5df6-63b3-7ce0-9d2f-0fa5650e93e9` | CLOTURE |
| `CONV-2026-1714` | QA privacy / regression | Meitner `019e5df6-5c4e-7bc0-9325-ff7394f19c9a` | CLOTURE |

## AGENTS-LAUNCHED - 2026-05-25 09:07 +02:00

Brice a redemande `lance une equipe agile`. Les agents ci-dessus ont ete lances
et rattaches aux roles deja reserves. Une premiere consigne ciblee `ORD-P0-036`
a ete interrompue pour eviter un doublon de chantier; tous les agents sont
recadres sur `ORD-P0-040` / WorksOps recette integration.

## Retours roles - 2026-05-25 09:12 +02:00

### Designer - `CONV-2026-1710`

Verdict: GO designer pour recetter `/travaux` comme MVP synthetique centre sur
un chantier fictif. NO-GO pour le presenter comme portefeuille WorksOps final.

Alignements: titre `Travaux suivis`, donnees fictives explicites, blocs
`Ce qui bloque`, `Ce qui manque pour continuer`, `A faire maintenant`, pieces
separees par statut, CTA prudent `Preparer une demande`, partage bloque par
`A verifier avant partage`.

Ecarts au blueprint: pas de vrai portefeuille multi-operations, budget compact
absent du premier ecran, seuils/mise en concurrence absents, chaine probatoire
reduite, premiere vue plus proche d'une fiche guidee que d'une console
portefeuille.

### Utilisateur novice - `CONV-2026-1711`

Verdict: NO-GO produit sur le live actuel. Le serveur deja ouvert renvoie
`/travaux` en 404 et expose plutot `/chantiers`, dont le contenu reste centre
sur `Memoire de copropriete`.

Pour un GO novice, le premier ecran doit montrer: nom du chantier, statut clair,
preuve attendue, prochaine action humaine et diffusion possible. Les CTA
naturels attendus sont `Voir les chantiers`, `Ouvrir le chantier`,
`Demander une piece`, `Voir les preuves`, `Preparer une relance`,
`Verifier avant diffusion`.

### Front / integration - `CONV-2026-1712`

Verdict: GO technique conditionnel pour revue d'integration, mais recette seule
insuffisante.

Fichiers front du worktree: route `/travaux` dans `part_003.pyfrag`, template
`travaux.html`, CSS `styles_part_14.css`, import dans `styles.css`, navigation
`Travaux suivis` dans `base.html`, dashboard `_dashboard.py`, tests
`test_ui_worksops_travaux.py`.

Risques: collisions avec le worktree principal sale sur `part_003.pyfrag`,
`base.html`, `styles.css`, `_dashboard.py` et `test_ui_demo.py`; import CSS
`styles_part_13.css` et `styles_part_14.css` a preserver; classe `grid three`
a verifier visuellement; recette responsive desktop/tablette/mobile obligatoire.

### Back / viewmodel - `CONV-2026-1713`

Verdict: GO technique conditionnel pour revue/integration, NO-GO produit complet
sans recette navigateur.

Constats: route `/travaux` tokenisee, read model 100 % synthetique marque
`FICTIF`, aucun brut lu, liens internes tokenises, tests 403/200 prevus. Limite:
pas de contrat formel `model.ux.worksops_travaux`; le template consomme un objet
`travaux` separe.

### QA privacy / regression - `CONV-2026-1714`

Verdict: GO technique pour revue/integration du worktree `/travaux`, sous
reserve d'une revue de diff par le coordinateur. NO-GO produit complet sans
recette navigateur avec captures desktop/mobile/tablette.

Tests rejoues dans le worktree dedie: `tests.test_ui_worksops_travaux`,
`tests.test_ui_security_routes`, `tests.test_ui_smoke_routes_expanded`,
`tests.test_security_no_private_sync_leaks`, `tests.test_code_line_limit` et
`tests.test_ui_demo`: 31 tests OK. `tools\check_code_line_limit.py` OK.
`git diff --check` OK.

## Point de coordination final - 2026-05-25 09:13 +02:00

- A tester maintenant: rien en live tant que `/travaux` n'est pas integre et
  servi sur un port reserve avec token de test.
- En dev maintenant: aucun dev dans le worktree principal sale.
- En enquete maintenant: terminee pour designer, novice, front, back et QA.
- Commande prete: revue/integration du worktree WorksOps en owner unique, puis
  recette navigateur `/travaux` desktop/tablette/mobile.
- Comparaison visuels enquete: GO pour MVP fiche synthetique, NO-GO portefeuille
  WorksOps complet.
- Agents idle a relancer: aucun role vivant; relancer seulement sur nouveau diff
  ou serveur live reserve.
- Decision requise: arbitrer integration du worktree dedie ou stationner le lot.
- Prochain mouvement: si integration validee, ouvrir un chantier owner unique
  d'integration; sinon garder `ORD-P0-040` en attente de decision.
- Tests/preuves: 31 tests OK, line-limit OK, `git diff --check` OK dans le
  worktree dedie; aucune capture navigateur.

AGILE-DONE - equipe agile a fini son job

## Contrats courts

Tous les roles travaillent en lecture seule. Ils ne modifient aucun fichier,
ne lancent aucun serveur et ne touchent aucune instance privee.

Worktree a inspecter: `C:\Users\brice\CoproScope\dev\worktrees\coproscope-worksops-travaux-v1-20260525`.
Branche: `codex/worksops-travaux-v1-20260525`.
UI cible: `/travaux`.
Donnees: corpus fictif uniquement; aucune donnee reelle, chemin local, OCR brut,
document brut, export brut, secret, token ou donnee personnelle dans les sorties.
Livrable: verdict GO/NO-GO, criteres d'acceptation, risques, tests attendus et
prochaine action bornee.

## ROLE-RETURNS - 2026-05-25 09:13 +02:00

### Designer service / facilitateur - CONV-2026-1710

Verdict: GO pour recetter `/travaux` comme MVP synthetique `Travaux suivis`
centre sur un chantier fictif; NO-GO pour le presenter comme portefeuille
WorksOps complet.

Alignements observes:

- titre utilisateur `Travaux suivis`;
- donnees fictives explicites;
- blocs `Ce qui bloque`, `Ce qui manque pour continuer`, `A faire maintenant`;
- pieces confirmees, a verifier et manquantes separees;
- CTA prudent `Preparer une demande`, sans envoi automatique;
- revue avant partage.

Ecarts a garder visibles avant GO produit: pas de portefeuille multi-operations,
budget compact absent, seuils/mise en concurrence absents, chaine probatoire
encore simplifiee.

### Utilisateur novice / membre CS - CONV-2026-1711

Verdict: NO-GO produit actuel. Le role novice a observe un live local
`127.0.0.1:8771` ou `/travaux?token=...` repond `404`, la navigation visible
affiche `10 Chantiers` vers `/chantiers`, et `/chantiers` montre surtout
`Memoire de copropriete` apres un chargement lent. Ce signal confirme que le
worktree `/travaux` n'est pas integre dans le principal live teste.

Attendu novice pour un GO: route ou libelle assume `Travaux suivis`, nom de
chantier, statut, preuve attendue, prochaine action humaine, detenteur/responsable
et prudence de diffusion visibles des le premier viewport.

### Dev front / integration - CONV-2026-1712

Verdict: GO technique conditionnel pour une revue d'integration, NO-GO sans
owner dedie. Le worktree contient route `/travaux`, template `travaux.html`,
CSS dedie `styles_part_14.css`, nav `Travaux suivis`, raccord dashboard et test
dedie `test_ui_worksops_travaux.py`.

Risques d'integration: le worktree principal est sale sur `part_003.pyfrag`,
`base.html`, `styles.css`, `_dashboard.py` et `test_ui_demo.py`; `styles_part_13`
existe deja dans le principal, il faudra conserver les imports 13 et 14; le
responsive desktop/tablette/mobile reste a verifier par captures.

### Dev back / viewmodel - CONV-2026-1713

Verdict: GO technique conditionnel pour revue/integration, NO-GO produit sans
recette navigateur. La route `/travaux` est protegee par token et s'appuie sur
un read model fictif, marque `FICTIF`, sans lecture d'instance ni brut. Les
liens internes sont tokenises et les champs sensibles sont absents du modele
synthetique.

Blocages avant integration: formaliser ou assumer le contrat public
`model.ux.worksops_travaux`, relire les collisions dans les fichiers partages,
et rejouer le panier cible apres merge.

### QA privacy / regression - CONV-2026-1714

Verdict: GO technique pour revue du worktree, NO-GO produit complet sans recette
navigateur sur serveur reserve.

Panier rejoue dans le worktree dedie: 31 tests OK sur
`test_ui_worksops_travaux`, `test_ui_security_routes`,
`test_ui_smoke_routes_expanded`, `test_security_no_private_sync_leaks`,
`test_code_line_limit` et `test_ui_demo`; `tools/check_code_line_limit.py` OK;
`git diff --check` OK.

Captures obligatoires avant GO produit: `/travaux?token=<token-test>` en
desktop, tablette et mobile, avec controle du premier viewport, nav active,
CTA `Preparer une demande`, CTA `Voir l'apercu avant partage`, absence de
chevauchement et absence de fuite.

## RESULTAT - 2026-05-25 09:13 +02:00

AGILE-DONE sans dev dans le worktree principal.

Commande future bornee seulement si Brice valide un owner integration dedie:

- reprendre le worktree
  `C:\Users\brice\CoproScope\dev\worktrees\coproscope-worksops-travaux-v1-20260525`;
- integrer manuellement `/travaux` avec route, template, CSS, nav, dashboard et
  tests dedies;
- resoudre les collisions du worktree principal sale;
- garder le corpus fictif et les libelles humains;
- interdire donnees reelles, bruts, chemins, OCR/logs, exports bruts et envoi
  automatique;
- rejouer le panier QA ci-dessus, line-limit et `git diff --check`;
- produire ensuite une recette navigateur desktop/tablette/mobile sur serveur
  visible reserve.

NO-GO produit actuel: `/travaux` n'est pas prouve dans le principal live teste,
aucune capture navigateur n'est fournie, et le parcours visible actuel reste
confus pour un novice.

## BOT-END - Coordinateur-scribe - 2026-05-25 09:13 +02:00

Roadmap: `RM-2026-0032`.
Chantier: `CH-20260525-090648-RM-2026-0032-worksops-recette-integration`.
Conversation: `CONV-2026-1709`.
Statut: `EN_ATTENTE_USER`.
Fichiers modifies: `docs/equipe_agile_2026-05-25_worksops-recette-integration.md`, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`, heartbeat agile du fil courant.
Fichiers volontairement evites: code, tests applicatifs, routes, templates, CSS, worktree principal sale, instances privees reelles, documents bruts, OCR/logs, exports bruts, secrets, serveurs non reserves, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Tests/preuves: retours agents Popper, Carson, Erdos, Hegel, Meitner; QA rapporte 31 tests OK, line-limit OK et diff whitespace OK dans le worktree dedie; `git diff --check` documentaire OK cote coordinateur.
Limites: pas d'integration automatique; `/travaux` absent du live actuel `8771`; pas de captures navigateur WorksOps; worktree principal sale; collisions front/back a traiter par owner unique.
Questions ouvertes: ouvrir un owner d'integration dedie pour integrer prudemment `/travaux`, ou laisser WorksOps en NO-GO produit.
Prochain mouvement propose: revue diff du worktree dedie, integration manuelle dans une branche/worktree propre, replay tests, reserve serveur WorksOps `8773` ou port documente, puis recette navigateur `/travaux` desktop/tablette/mobile.

AGILE-DONE - equipe agile a fini son job pour le cadrage/revue lecture seule `ORD-P0-040`; le lot reste en attente de decision d'integration, pas en GO produit.
