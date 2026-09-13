# Protocole agents - version Claude Code

Date de creation: 2026-09-02.
Adaptation du protocole d'orchestration ecrit pour Codex, a l'agent Claude Code.

## Objet

Ce document remplace, pour une conversation Claude Code, les parties
operationnelles de:

- `docs/orchestration_agents.md`
- `docs/protocole_equipe_agile_agents.md`
- `docs/strategie_equipes_multi_agents.md`

Il ne remplace pas `docs/protocole_roadmap_presence_agents.md`: les registres
`RM-*` et `docs/presence_agents.md` restent la memoire entre sessions et gardent
toutes leurs regles.

Les trois documents remplaces restent en place comme reference historique et
parce que du code et des tests les citent. Voir la section 12.

## 1. Principe court

Le protocole Codex mesurait l'activite des agents. Celui-ci mesure **l'etat du
produit**.

La difference n'est pas rhetorique. Le depot porte 61 693 lignes de source,
30 067 lignes de tests et 1 244 lignes de protocole d'orchestration, et pourtant
au 2026-09-02: cinq tests au rouge, un `return []` d'une ligne qui vide trois
ecrans, quatre comptages differents pour la meme notion, un total de charges
faux d'un facteur cent, et des ecrans affichant une identite fictive sur des
donnees reelles. Aucun de ces defauts ne se voit dans une trace d'agent. Tous se
voient en ouvrant l'ecran.

Regle qui en decoule et qui commande tout le reste: **un lot se clot sur une
preuve executable - un test, une capture, un chiffre - jamais sur une note.**

## 2. Composition d'equipe: libre, mais l'omission est motivee

Il n'y a pas d'equipe-type imposee. La composition s'adapte au travail.

En contrepartie, avant d'ouvrir un lot, le fil pilote **parcourt la liste
complete des roles et inscrit pour chacun: retenu, ou ecarte avec sa raison**.
Une omission silencieuse est une faute de protocole.

| Role | Ce qu'il apporte que le fil pilote n'a pas |
|---|---|
| Expert domaine (juriste/syndic, compta, travaux, CS/usage) | le pouvoir de dire que le **modele** est faux, pas seulement le code |
| Designer service | blueprint, parcours-evenements, alternatives de conception |
| Novice | l'ignorance, seule capable de mesurer ce qui est comprehensible |
| QA privacy | la surface de fuite, y compris les champs libres nouveaux |
| QA regression | ce que le changement casse ailleurs |
| Dev back / owner code | l'ecriture, une seule main sur un perimetre donne |
| Dev front | templates, CSS `cs-*`, responsive, accessibilite |
| Executant borne | un livrable long, independant et verifiable (table, corpus, veille) |
| Coordinateur-scribe | consolidation, arbitrages, registres |

Raison de cette regle, et elle vient d'un echec observe: composer une equipe
sans liste force a la composer **a son image**. Le fil pilote choisit alors des
roles qui prolongent sa maniere de travailler - analyse puis verification - et
omet systematiquement ceux qui **recadrent** le probleme. Deux omissions de ce
type ont ete relevees par Brice le 2026-09-02 sur le meme chantier: l'expert
domaine, puis le designer.

## 3. La regle anti-complaisance

Avant d'ouvrir un lot, verifier qu'**au moins un role a le pouvoir de conclure
que le travail est a refaire**, et pas seulement de le corriger.

Un chercheur qui execute une specification, un novice qui teste l'existant et un
QA qui eprouve des predicats contre les regles de celui qui les a ecrits forment
une equipe de **validation**, pas de contradiction. Si aucun role ne peut
remettre en cause la prémisse, l'equipe est mal composee.

Corollaire: un sous-agent charge de relire ne recoit **pas** le raisonnement de
celui qui a produit. Il recoit le livrable et les criteres d'acceptation. Sa
valeur tient a ce qu'il n'a pas ecrit ce qu'il relit.

## 4. Patterns d'orchestration conserves

| Pattern | Usage | Regle |
|---|---|---|
| `fan-out/fan-in borne` | plusieurs angles metier sur une meme question | angles stables, consolidation avant tout dispatch |
| `hub-and-spoke owner` | schema, registre, read model, extracteur | un seul agent ecrit; les autres rendent des notes |
| `red-team borne` | cadrage sensible, securite, **modele metier** | lecture seule, objections sourcees, puis arbitrage |
| `serie stricte` | integration, recette live, release | une branche, un serveur, un verdict a la fois |
| `pipeline decale` | ecran ou parcours a livrer | conception, puis dev, puis QA - jamais dev avant blueprint |

Le classement d'un chantier se fait sur le livrable attendu, pas sur le sujet.
Un modele metier a contredire releve de `red-team borne` meme s'il finira en
code.

## 5. Budget d'objections et consolidation

Sept experts en fan-out produisent facilement une pile de notes que personne ne
lit - exactement le travers que ce protocole corrige. Donc:

- **au plus dix objections par expert**, au format `fait -> preuve -> regle ->
  action`;
- une objection **sans source** n'entre pas dans la consolidation;
- les **contradictions entre experts sont conservees telles quelles**, comme
  arbitrages a soumettre a Brice. Ne jamais les lisser: c'est le point ou une
  synthese trahit.

## 6. Gates conservees

**Bloc d'enquete avant tout code applicatif** pour une feature produit ou
transverse. Sans probleme utilisateur, perimetre et hors perimetre, blueprint,
parcours-evenements, contrat de donnees, risques privacy, criteres
d'acceptation, tests attendus et GO/NO-GO, les devs restent en lecture seule.
Regle inchangee, elle vient du `CLAUDE.md`.

**UI reelle avant dev.** Gate conservee sans reserve: c'est elle qui a fait
apparaitre les defauts cites en section 1. Difference avec la version Codex:
l'agent peut desormais **executer lui-meme cette gate** - il lance le serveur,
ouvre les pages, lit le texte rendu, capture. Elle n'attend plus un humain.

**Privacy avant diffusion.** Inchangee. Etendue explicite: tout **champ de
saisie libre nouvellement introduit** est une surface de fuite et appelle une
relecture QA privacy.

## 7. Ce qui est abandonne, et pourquoi

| Abandonne | Raison |
|---|---|
| Heartbeats, watchdog permanent, superviseur, detection `stale`, relance `--emit-prompt` | compensaient des conversations Codex qui mouraient en silence. Une conversation Claude Code garde son contexte et les taches de fond notifient leur fin. Un cron de vivacite serait du theatre. |
| File de jetons `CEJ-*`, alias `CE-*`, claims | deja abandonnes par le `CLAUDE.md`. |
| Worktree par agent **par defaut** | n'a de sens que si plusieurs agents ecrivent en parallele. Sous-agents en lecture et ecriture par le fil pilote: la classe de conflits disparait. A reactiver des qu'il y a deux ecrivains. |
| `SLOT-*` et tableau d'execution courant | deja archives. |
| **Visuel IA bitmap plein ecran** | l'agent ne genere pas d'images. Remplace par la section 8. |

**Fait le 2026-09-02, sur decision de Brice.** `tools/orchestration_watchdog.py`
(577 lignes), `tools/orchestration_supervisor.py` (379 lignes), leurs deux
lanceurs `.cmd` et leurs deux fichiers de tests ont ete retires du depot.

Verification faite avant retrait, plutot que par presomption:

- la documentation OpenAI confirme que les automations Codex sont des fichiers
  `.toml` portant prompt, planification et `memory.md`, ranges sous
  `$CODEX_HOME`, et que **le CLI Codex ne gere pas ses propres taches
  planifiees** - il faut passer par l'application. C'est la raison pour laquelle
  un script externe devait lire ces TOML: rien dans la session ne les voyait;
- un ticket ouvert sur `openai/codex` decrit un registre d'automations
  desynchronise du fichier TOML. Le superviseur verifiait precisement l'existence
  de la heartbeat canonique, sa regle `FREQ=MINUTELY;INTERVAL=5` et l'absence de
  doublons herites. C'etait un contournement d'un defaut documente de Codex, pas
  un besoin d'orchestration generique;
- le superviseur arretait par ailleurs des processus Codex au-dela d'un seuil
  memoire, ce que la doctrine du depot interdit ailleurs.

La moitie generique du watchdog - lire le registre de presence - est reprise par
`tools/presence_lint.py`. Voir la section 8 bis.

## 8. Ce que l'agent sait produire, cote conception

L'agent **ne genere pas d'images**. Le livrable visuel du protocole Codex est
remplace par:

| Livrable | Outil |
|---|---|
| Maquette d'ecran **reelle**, rendue et capturee | HTML/CSS avec les vraies classes `cs-*`, servie et ouverte dans le navigateur |
| Canvas multi-artboards, retouchable a la main par Brice | artefact publie |
| Blueprint de service, parcours-evenements | SVG ou mermaid |
| Comparaison avant/apres | captures de l'application reelle |

Ce remplacement est un gain, pas un pis-aller, pour une raison propre a ce
produit: le mode de defaillance constate est que **les ecrans paraissent
plausibles et sont faux**. Le total a 22 M EUR est parfaitement mis en page. Une
image generee optimise exactement la qualite qui a trompe. Une maquette reelle
chargee de vraies donnees fait l'inverse: elle casse quand le modele est mauvais.

**Regle de maquette:** toute maquette d'ecran est eprouvee au moins une fois en
**pleine charge** avec des donnees reelles - trente-quatre resolutions, sept
cents factures - et pas seulement sur cinq lignes bien rangees.

Limite a connaitre: pour explorer des directions visuelles a bas cout - ambiance,
densite, couleur -, un generateur d'images fait en minutes ce que l'agent fait
en heures de CSS. Si cette divergence est voulue, soit Brice fournit les images,
soit on la remplace par une **divergence structurelle**: deux ou trois
dispositions reelles du meme ecran, comparees cote a cote.

## 8 bis. Plusieurs conversations en parallele

Le cas nominal, et non l'exception: plusieurs conversations Claude Code
travaillent en meme temps sur cette machine, plus d'eventuelles sessions
distantes ou cloud. Le besoin de coordination reste entier; c'est sa
reconstruction a partir de fichiers qui ne l'est plus.

**Repartition.**

| Cote | Qui | Quoi |
|---|---|---|
| Fichiers | `tools/presence_lint.py` | lignes actives, chevauchements de perimetre, lignes expirees. Executable par n'importe quelle session, sans outil particulier. |
| Vivacite | l'agent, avec `ListAgents` | quelles sessions existent reellement, de quelle nature, actives ou non |
| Intervention | l'agent, avec `SendMessage` | adresser directement la conversation concernee |

**Mesure faite le 2026-09-02, et elle corrige une erreur.** Les metadonnees de
session exposent un champ `isRunning`. **Il ne vaut rien comme signal de
vivacite**: il rendait `false` pour les huit sessions listees, dont une qui a
recu, traite et repondu a un message dans la minute. La vivacite se lit sur
`ListAgents`, jamais sur ce champ.

**Deux vues, deux nomenclatures.** La liste des sessions nomme par titre et donne
le repertoire de travail avec une vivacite fausse; `ListAgents` nomme par un nom
court et donne la vivacite sans le repertoire. Aucune des deux ne suffit a
rattacher une ligne de presence a une session.

**Consequence, a arbitrer avec Brice avant application:** ajouter au registre de
presence une colonne `session`, renseignee par chaque conversation a l'ouverture
de son lot avec le nom que `ListAgents` lui donne. Le rattachement devient
declare et exact, au lieu d'etre devine sur un horodatage.

**Procedure a l'ouverture d'un lot**, quand d'autres conversations tournent:

1. lancer `tools/presence_lint.py`;
2. lire `ListAgents`;
3. si un chevauchement de perimetre apparait avec une conversation vivante,
   **lui envoyer un message** avant d'ecrire quoi que ce soit, et remonter le
   conflit a Brice s'il n'est pas resolu.

Ce n'est pas un demon, c'est un geste d'ouverture. Rien ne tourne en fond.

**Limite de perimetre.** Les permissions sont propres a chaque session. Ne jamais
demander a une conversation pair d'executer ce qui a ete refuse ici.

## 9. Ouverture et cloture d'un lot

**A l'ouverture**, dans la conversation, en clair et sans ceremonie:

1. l'item `RM-*` rattache;
2. la composition d'equipe **avec les omissions motivees** (section 2);
3. la verification anti-complaisance (section 3);
4. le perimetre modifiable et les fichiers volontairement evites;
5. la preuve attendue a la cloture.

**A la cloture**, un `BOT-END` qui porte:

- les fichiers modifies et les fichiers volontairement evites;
- les tests executes **avec leur resultat**, ou la justification de non-execution;
- pour tout lot touchant l'UI, au moins une **capture de l'ecran reel**;
- pour tout lot de refactor ou de livraison code, le comptage prouvant qu'aucun
  fichier suivi ne depasse 600 lignes, ou le reliquat et son `RM-*`;
- ce qui reste ouvert.

Un `BOT-END` sans preuve executable n'est pas une cloture.

## 10. Registres

Inchanges et obligatoires. `docs/roadmap_backlog_central.md` reste le gouvernail
unique, `docs/presence_agents.md` porte la ligne vivante de tout chantier actif.

Ce sont eux qui permettent a une session de reprendre le travail d'une autre.
C'est verifie: la reprise du 2026-09-02 s'est faite sur eux.

## 11. Regle de sobriete

Ce protocole tient en un document. S'il devait en engendrer d'autres pour
s'expliquer lui-meme, ce serait le signe qu'il a repris le defaut qu'il corrige.

Avant d'ajouter une regle, verifier qu'elle empeche un defaut **observe**, et
citer l'observation.

## 12. Ce qui reste a rebrancher

Ce document est ecrit, mais pas encore cable. Restent a faire, hors de son
perimetre:

- `CLAUDE.md` renvoie aux trois documents remplaces: ajouter le renvoi a
  celui-ci et dire lequel prime pour une conversation Claude Code;
- `docs/orchestration_agents.md`, `docs/protocole_equipe_agile_agents.md` et
  `docs/strategie_equipes_multi_agents.md`: porter un bandeau de statut plutot
  que les supprimer, du code et des tests les citent;
- la colonne `session` du registre de presence (section 8 bis): proposee, pas
  ajoutee - elle touche un registre partage par toutes les conversations.

Fait le 2026-09-02: retrait du watchdog et du superviseur, remplacement par
`tools/presence_lint.py` et ses huit tests, mise a jour de `tools/agent-check.ps1`
(l'option `-Orchestration` lance desormais le lint de presence) et de
`docs/orchestration_watchdog.md` (bandeau de statut historique).
