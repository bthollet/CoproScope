# Equipe agile - WorksOps recette navigateur

Date: 2026-05-25 09:55 +02:00.
Rattachement: `ORD-P0-040`, qualite live `RM-2026-0006`, travaux `RM-2026-0032`.
Chantier canonique: `CH-20260525-095500-RM-2026-0006-worksops-recette-navigateur`.

## BOT-START - Coordinateur-scribe - 2026-05-25 09:55 +02:00

Roadmap: `RM-2026-0006`, rattachement travaux `RM-2026-0032`.
Chantier: `CH-20260525-095500-RM-2026-0006-worksops-recette-navigateur`.
Conversation: `CONV-2026-1731`.
Role: coordinateur-scribe agile recette navigateur.
Mission: lancer l'equipe de recette live de `/travaux?token=<token-test>` sans rouvrir les roles d'integration `/travaux`.
Ownership modifiable: cette trace, `docs/presence_agents.md`, trace append-only `docs/roadmap_backlog_central.md`, heartbeat agile du fil courant.
Fichiers a eviter: code applicatif, tests applicatifs, instances privees, documents bruts, OCR/logs, exports bruts, secrets, push GitHub, `RM-2026-0017`, `ORD-P0-990`, serveurs non reserves, doublons `CH-20260525-091900-RM-2026-0032-worksops-integration-recette` et roles `CONV-2026-1710`..`CONV-2026-1729`.
Passerelle/registre de trace: ce fichier, `docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Dernier point lu: `AGENTS.md`, `docs/consignes_bots_interconversations.md`, `docs/orchestration_agents.md`, `docs/protocole_roadmap_presence_agents.md`, `docs/protocole_equipe_agile_agents.md`, `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`, `docs/equipe_agile_2026-05-25_worksops-integration-owner.md`, watchdog `.\tools\orchestration-watch.cmd --emit-prompt`.
Tests/preuves attendus: recette navigateur `/travaux?token=<token-test>` sur serveur visible reserve, captures desktop/tablette/mobile, token 200/403, absence de chevauchement texte, corpus fictif, liens token-safe, anti-fuite.
Risque de collision: `/travaux` est deja integre; tout nouveau role d'integration serait un doublon. Le gate restant est uniquement navigateur.
Lease ownership: 2026-05-25 12:04 +02:00.
Prochaine action: produire la recette navigateur sur le serveur visible reserve `8773`; si Browser in-app reste indisponible, tracer le NO-GO captures plutot que relancer une equipe concurrente.

## Point de coordination initial

- A tester maintenant: `/travaux?token=<token-test>` uniquement si un serveur visible et un port reserve sont disponibles; port reserve canonique WorksOps `8773`.
- En dev maintenant: rien; code integre localement.
- En enquete maintenant: designer, novice et QA verifient les criteres de recette live, sans patch.
- Commande prete: recette navigateur desktop/tablette/mobile de `/travaux`, avec token valide et capture du 403 sans token.
- Comparaison visuels enquete: reference = recherches UX travaux 2026-05-24 et trace WorksOps integration owner; ecart accepte = MVP synthetique `Travaux suivis`, pas WorksOps complet.
- Agents idle a relancer: aucun role d'integration; seulement les trois roles de recette lances en lecture seule.
- Decision requise: serveur visible reserve, port, instance de test et token de recette.
- Prochain mouvement: si serveur visible reserve, ouvrir navigateur et produire captures; sinon stationner sans serveur cache.
- Tests/preuves: 33 tests automatises, line-limit et diff-check deja OK; preuve manquante = navigateur.

## Roles lances - 2026-05-25 09:55 +02:00

| Conversation | Role | Agent | Statut |
|---|---|---|---|
| `CONV-2026-1732` | Designer service / facilitateur recette | Harvey `019e5e23-ab5c-7ad1-914a-2c6428a8e49d` | EN_COURS |
| `CONV-2026-1733` | Utilisateur novice / membre CS recette | Lovelace `019e5e23-dc5b-7f43-a7ee-f1f69f1aed06` | EN_COURS |
| `CONV-2026-1734` | QA navigateur / privacy / regression | Pasteur `019e5e24-1552-7fa1-96b6-d775329f815b` | EN_COURS |

## Retours supplementaires du fil courant - 2026-05-25 09:56 +02:00

Une relance locale parallele a rendu trois avis preparatoires sans modifier de fichier et sans lancer de serveur. Ces retours ne rouvrent pas l'integration `/travaux`; ils consolident seulement le gate navigateur.

- Designer: GO preparation recette; NO-GO lancement tant qu'aucun terminal PowerShell visible avec port reserve n'est disponible. Refus: `/travaux` 404, donnees reelles, libelles techniques, envoi/diffusion automatique ou statut faussement vert.
- Novice: en moins de 30 secondes, la page doit montrer les travaux suivis, le statut, l'urgence, la prochaine action et le responsable; NO-GO si token refuse a tort, page blanche, debordement mobile/tablette, donnees non synthetiques ou action introuvable.
- QA: panier pret: `200` avec token, `403` sans token/invalide, captures desktop/tablette/mobile, console sans erreur bloquante, anti-fuite visible et DOM/reseau sans donnee reelle, secret, OCR/log ni export brut.

AGILE-POINT: code `/travaux` integre localement; gate restant = recette navigateur sur serveur visible reserve. Aucun serveur n'a ete lance dans ce passage.

## DEDUP - 2026-05-25 09:57 +02:00

Une vague concurrente 09:55 a reserve Boyle, Socrates et Carver sur le meme
lot. Ces agents ont ete fermes avant livrable pour conserver les roles
canoniques ci-dessus: Harvey, Lovelace et Pasteur. Aucun fichier code, serveur
ou instance n'a ete touche par cette vague non canonique.

## Point live serveur - 2026-05-25 10:04 +02:00

Serveur WorksOps lance dans un terminal PowerShell visible:

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli ui open-test --instance-root "C:\Users\brice\CoproScope\instances\beauvallon_test" --year 2025 --port 8773 --token worksops-live-local
```

URL recette: `http://127.0.0.1:8773/travaux?token=worksops-live-local`.

Verifications HTTP locales:

- `GET /health` -> `200`.
- `GET /travaux` sans token -> `403`.
- `GET /travaux?token=worksops-live-local` -> `200`.
- Marqueurs HTML presents: `Travaux suivis`, `FICTIF`, `Preparer une demande`, `A verifier avant partage`.

Limites:

- Browser Codex in-app non disponible dans ce fil: le bootstrap Node/browser-client a expire, donc aucune capture desktop/tablette/mobile n'a encore ete produite.
- Les agents canoniques Harvey, Lovelace et Pasteur restent la source de recette; tentative `wait_agent` depuis ce fil = `not_found` pour leurs identifiants, probablement parce qu'ils ont ete lances par le heartbeat dans un autre contexte.
- Aucun nouveau role n'a ete lance pour eviter un doublon; la heartbeat agile 5 minutes doit reprendre ces roles vivants ou tracer leur blocage.

Verdict intermediaire: GO serveur/token sur checks HTTP; NO-GO produit complet tant que les captures navigateur desktop/tablette/mobile et la revue anti-chevauchement ne sont pas livrees.

## HEARTBEAT - 2026-05-25 10:05 +02:00

Watchdog execute: il remonte encore des conversations expirees/stale anciennes,
un arbitrage `EN_ATTENTE_USER` et le blocage general `ORD-P0-036`, mais rien ne
justifie de dupliquer les roles `/travaux`.

- A tester maintenant: `/travaux?token=<token-test>` sur serveur PowerShell visible reserve, port WorksOps `8773`.
- En dev maintenant: rien; code `/travaux` integre localement.
- En enquete maintenant: rien de nouveau; designer, novice et QA ont deja rendu leurs criteres.
- Commande prete: ouvrir la route tokenisee, verifier `200`, verifier `403` sans token/invalide, capturer desktop/tablette/mobile.
- Comparaison visuels enquete: MVP synthetique `Travaux suivis` accepte; WorksOps complet reste hors scope.
- Agents idle a relancer: aucun, roles de recette clos; ne pas rouvrir `CONV-2026-1710`..`CONV-2026-1729`.
- Decision requise: serveur visible reserve disponible pour la recette navigateur.
- Prochain mouvement: attendre ce serveur visible; ne pas lancer de serveur cache et ne pas scanner les ports.
- Tests/preuves: 33 tests automatises OK, line-limit OK, `git diff --check` OK; preuve manquante = captures navigateur.

Statut passage: `EN_ATTENTE_USER` cote coordinateur recette, `CLOTURE` pour les
trois roles preparatoires. NO-GO produit complet tant que la recette navigateur
n'a pas ete faite.

## Passage coordinateur - 2026-05-25 10:07 +02:00

Recette live reprise apres ouverture effective du serveur visible sur le port
reserve `8773`.

Preuves obtenues:

- `GET /health?token=worksops-live-local`: `200`;
- `GET /travaux?token=worksops-live-local`: `200`;
- `GET /travaux` sans token: `403`;
- `GET /travaux?token=bad`: `403`;
- captures desktop, tablette et mobile prises dans
  `C:\Users\brice\CoproScope\dev\captures\worksops-recette-20260525-0958`;
- controle navigateur: pas de debordement horizontal detecte dans le contenu
  principal, pas de chevauchement majeur detecte, route `/travaux` affiche
  `Travaux suivis`, `Scenario FICTIF` et `A verifier avant partage`.

Limites et vigilance:

- le CTA `Preparer une demande` repond en `200`, mais bascule vers le contexte
  de l'instance de test; aucune capture de cette cible n'est publiee;
- sur mobile, la navigation laterale devient une zone horizontale scrollable:
  ce n'est pas bloquant pour `/travaux`, mais a surveiller avant GO produit
  global.

Roles live relances car les anciennes reservations `CONV-2026-1732`..`1734`
avaient deja ete cloturees avant ouverture effective du serveur:

| Conversation | Role | Agent |
|---|---|---|
| `CONV-2026-1735` | QA navigateur desktop/tablette/mobile | Pauli `019e5e2c-1f84-7dc2-ab15-77c738107e3d` |
| `CONV-2026-1736` | Utilisateur novice live | Nietzsche `019e5e2c-208e-7b90-a9fd-ead71b549584` |
| `CONV-2026-1737` | Designer comparaison visuelle | Dirac `019e5e2c-21b0-7902-8d16-b035ea80118f` |

Prochain mouvement: attendre les trois retours, puis rendre GO/NO-GO final de
recette sans modifier le code.

## BOT-END - Coordinateur-scribe - 2026-05-25 10:12 +02:00

Statut: `CLOTURE`, verdict produit `NO-GO` tant que le responsive
navigationnel mobile/tablette n'est pas corrige. Aucun code, instance privee,
document brut, export brut, secret ou push GitHub n'a ete modifie par cette
recette.

Retours roles live:

- `CONV-2026-1735` QA navigateur: GO QA pour le MVP `/travaux`; HTTP live OK
  (`/health` 200, `/travaux?token=worksops-live-local` 200, sans token 403,
  mauvais token 403), captures desktop/tablette/mobile disponibles, anti-fuite
  OK sur l'inspection realisee. Risque P1: navigation mobile/tablette avec
  barre horizontale visible.
- `CONV-2026-1736` novice: GO comprehension conditionnel. Le membre CS comprend
  le chantier, l'etat `3 sur 5`, la preuve manquante et l'action humaine.
  NO-GO partage reel sans verification humaine.
- `CONV-2026-1737` designer: NO-GO produit. Le contenu WorksOps est conforme au
  MVP, mais le mobile montre un defilement horizontal et la tablette une
  navigation superieure trop haute/partiellement coupee.

GO/NO-GO consolide:

- GO technique live: route tokenisee, 403 sans/mauvais token, corpus fictif,
  pieces separees, CTA prudent, captures produites.
- NO-GO produit: premiere impression mobile/tablette insuffisante pour un
  membre CS novice.
- Commande future bornee si Brice valide un owner code dedie: corriger
  uniquement le responsive de la navigation/coque mobile-tablette, rejouer
  captures desktop 1280x720, tablette 768x1024, mobile 390x844, conserver
  token, anti-fuite, donnees fictives et aucun envoi automatique.

## Retours live agents - 2026-05-25 10:12 +02:00

`CONV-2026-1735` QA navigateur - Pauli:

- GO QA navigateur pour le MVP `/travaux`.
- Preuves prises en compte: `/health` 200, route tokenisee 200, sans token 403, mauvais token 403, apercu 200, captures desktop `1264x720`, tablette `752x1024`, mobile `374x844`.
- Aucun P0 releve; pas de chemin local, OCR brut, email, IBAN ou donnee privee observee dans le contenu inspecte.
- Risque P1: navigation haute mobile/tablette avec debordement horizontal visible; corps de page exploitable, mais correction attendue avant demo mobile soignee.

`CONV-2026-1736` novice live - Nietzsche:

- GO comprehension novice conditionnel: `Travaux suivis`, scenario fictif, statut `3 sur 5`, pieces confirmees/a verifier/manquantes et blocages sont compris.
- Action humaine comprise: obtenir ou controler l'autorisation d'echafaudage, puis verifier l'apercu avant partage.
- NO-GO partage reel tant que la preuve humaine manque; mobile percu serre avec debordement horizontal.

`CONV-2026-1737` designer comparaison - Dirac:

- GO recette desktop conditionnel: le cadrage principal est respecte, avec preuve manquante, action humaine, apercu avant partage et prudence de diffusion.
- NO-GO produit: mobile avec defilement horizontal/navigation tronquee; tablette avec navigation superieure trop haute et partiellement coupee.
- Ecarts reportables: portefeuille multi-operations, budget/mise en concurrence et chaine probatoire detaillee restent hors MVP.

Verdict coordinateur:

- GO technique et GO recette informative sur `/travaux` MVP.
- NO-GO produit complet tant que le responsive navigationnel mobile/tablette n'est pas corrige et recapture.
- Aucun code, instance privee, export brut, secret ou push GitHub n'a ete modifie par cette recette.
- Prochain mouvement recommande: ouvrir un owner front dedie pour corriger la navigation responsive, puis refaire uniquement les captures mobile/tablette et le panier token 200/403.

AGILE-DONE - equipe agile a fini son job pour la recette `/travaux`; verdict = GO MVP technique, NO-GO produit responsive mobile/tablette.
