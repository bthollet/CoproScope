# Tableau d'execution courant

Date de creation: 2026-05-28.
Rattachement: `RM-2026-0005`.

Statut: `ARCHIVE`.

Ce fichier decrit l'ancien modele par slots. Il est conserve pour comprendre
les traces historiques, mais il ne pilote plus le travail courant. Le modele
actif passe par le fil pilote, `ROUTAGE_EQUIPE` et les lignes de roles dans
`docs/presence_agents.md`. Aucun nouveau slot ne doit etre cree ici.

## Regle courte

- `docs/roadmap_backlog_central.md` est le backlog long et la source de
  verite strategique.
- `docs/tableau_execution_courant.md` est une archive historique, pas le
  tableau actif du chantier courant.
- `docs/presence_agents.md` est le registre technique des conversations,
  leases, owners et traces finales.
- Seul l'orchestrateur choisit un `ORD-*` dans le backlog long.
- Les agents recoivent leur mission du fil pilote et la tracent dans
  `docs/presence_agents.md`.
- Sans mission explicite, un agent s'arrete et attend le coordinateur.

## Vocabulaire humain

| Identifiant | Nom humain | Role |
|---|---|---|
| `RM-*` | Sujet produit | Intention stable, longue duree. |
| `ORD-*` | Tache backlog | Prochaine tranche actionnable, choisie par l'orchestrateur. |
| `CH-*` | Run / chantier | Execution ouverte sur une seule tache backlog. |
| `SLOT-*` | Ancien slot de role | Trace historique; ne plus creer ni prendre. |
| `CONV-*` | Conversation | Fil Codex qui coordonne ou execute un slot. |

## Lecture des traces historiques

Les anciennes lignes `SLOT-*` et les anciens statuts de slot restent lisibles
pour comprendre un run passe. Elles ne sont plus un mecanisme de distribution du
travail.

Quand une trace ancienne parle de `A_PRENDRE`, `EN_COURS`,
`PRET_A_INTEGRER`, `TERMINE` ou `ANNULE`, lire ces mots comme l'etat historique
d'un role a cette date, pas comme une consigne d'action actuelle.

## Modele actif a utiliser

1. Le fil pilote s'appuie sur l'objectif actif Codex (`/objectif`) et sur
   `docs/presence_agents.md`.
2. Il choisit ou reprend un seul `ORD-*` depuis le gouvernail, seulement si
   aucun arbitrage ou blocage vivant ne l'interdit.
3. Il ouvre ou reprend un seul `CH-*` horodate.
4. Il trace `ROUTAGE_EQUIPE` et les roles dans `docs/presence_agents.md`.
5. Les sous-agents recoivent leur mission directement depuis le fil pilote; si
   l'outil manque, les memes roles sont joues sequentiellement et nommes.
6. Les diagnostics `orchestration-watch` ou `orchestration-supervise` restent
   manuels et informatifs; ils ne creent pas de relance permanente.

## Interdits actuels

- Ne plus publier de nouveau `SLOT-*` dans ce fichier.
- Ne plus attendre qu'un agent prenne un slot ici.
- Ne pas creer de heartbeat canonique ou de watchdog permanent pour remplacer
  une ligne de presence.
- Ne pas lancer, cacher, scanner ou tuer un serveur depuis ce fichier.
- Ne pas utiliser cette archive pour choisir un nouveau `ORD-*`.

## Si une ancienne consigne cite ce tableau

Appliquer la traduction suivante:

| Ancienne consigne | Regle actuelle |
|---|---|
| Lire ce tableau pour prendre un slot | Lire `docs/presence_agents.md` et la mission donnee par le fil pilote |
| Publier des slots `A_PRENDRE` | Tracer les roles dans `docs/presence_agents.md` |
| Relancer une surveillance permanente | Utiliser `/objectif` et, si besoin, un diagnostic manuel |
| Surveiller un serveur depuis un slot | Reserver le serveur dans la trace `CONV-*`, avec port, instance, token et condition d'arret |
