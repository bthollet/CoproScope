# Protocole equipe UX/UI recherche visuelle sans dev

Date de creation: 2026-05-24.
Rattachement: `RM-2026-0005`.

Ce protocole s'applique quand Brice dit:

```text
lance une equipe UX/UI
```

La commande est equivalente avec ou sans accent sur `equipe`.

Il s'applique aussi quand le routeur
[`strategie_equipes_multi_agents.md`](./strategie_equipes_multi_agents.md)
classe automatiquement le travail en `UXUI_RECHERCHE`.

Il lance une recherche UX/UI visuelle, sans developpement. Le resultat attendu
est une decision produit documentee: parcours, hypotheses, arbitrages,
recommandations, images retenues et questions ouvertes.

Ce protocole est distinct de l'equipe agile dev. Il ne produit ni patch, ni
ticket technique detaille, ni commande front/back. Si une suite dev devient
necessaire, elle est ouverte ensuite comme chantier separe.

## Equipe maximum

L'equipe contient 6 roles maximum:

| Role | Mission |
|---|---|
| Orchestrateur UX/UI | Cadre la recherche, distribue les roles, relance les agents, arbitre, tient la trace et livre la synthese. |
| Chercheur utilisateur | Formalise profils, besoins, irritants, hypotheses, scenarios et criteres de reussite. |
| Architecte UX | Structure les parcours, la navigation, les priorites d'information, les wireflows et les etats d'ecran. |
| Designer UI / generateur visuel | Produit directions UI, prompts, images generees, variantes visuelles, compositions d'ecran et principes d'interaction. |
| Testeur metier expert | Challenge la justesse domaine, le vocabulaire professionnel, les cas limites et les attentes d'un utilisateur competent. |
| Testeur accessibilite / novice | Challenge la comprehension immediate, la lisibilite, la charge cognitive, les ambiguites et les risques de blocage. |

Si le sujet est court, l'Orchestrateur peut fusionner Chercheur utilisateur et
Architecte UX, mais il garde toujours au moins un testeur metier expert et un
testeur accessibilite/novice.

## Cadrage de lancement

Avant de lancer l'equipe, l'Orchestrateur:

1. lit `AGENTS.md`, `docs/orchestration_agents.md`, le present protocole,
   `docs/roadmap_backlog_central.md` et `docs/presence_agents.md`;
2. rattache la recherche a un `RM-*` existant ou cree un `RM-*` si la demande
   introduit une intention nouvelle;
3. cree un `CH-*` horodate et une ligne `CONV-*` de coordination dans
   `docs/presence_agents.md`;
4. publie les slots de role UX/UI dans `docs/tableau_execution_courant.md`;
   les workers prennent ces slots et ne choisissent pas dans le backlog long;
5. definit le livrable de mission, par defaut
   `docs/recherche_ux_ui_<date>_<slug>.md`;
6. definit le dossier d'images retenues, par defaut
   `docs/assets/ux-ui-recherche-<date>-<slug>/`;
7. declare que le code applicatif, les instances privees, les secrets, les
   exports bruts et les passerelles hors mission sont evites.

Si des outils de sous-agents sont disponibles, l'Orchestrateur lance les roles
comme agents separes avec ownership lecture seule ou documentaire. Sinon, il
execute les roles sequentiellement dans le fil courant, avec des sections
nommees par role.

## Relance automatique

Au lancement effectif de l'equipe UX/UI, l'Orchestrateur cree une heartbeat
automation Codex rattachee au fil courant, cadencee toutes les 10 minutes.

Cette relance continue tant que l'equipe n'a pas emis le marqueur final:

```text
UXUI-DONE - equipe UX/UI a fini son job
```

A chaque relance, l'Orchestrateur:

1. relit la derniere trace de mission et `docs/presence_agents.md`;
2. verifie si le marqueur `UXUI-DONE` est deja present;
3. si le marqueur est absent, relance uniquement les roles manquants, idle,
   bloques sans prochain geste ou expires;
4. evite de dupliquer un role dont le lease est vivant;
5. produit un point court: `a produire`, `en test`, `images candidates`,
   `decisions ouvertes`, `prochain mouvement`;
6. si le marqueur final est present, stoppe la relance en supprimant ou en
   mettant en pause l'automation.

Le prompt de relance doit rester borne: reprendre la recherche UX/UI active,
ne pas lancer de dev, ne pas ouvrir de serveur, ne pas modifier d'instance
privee, ne pas creer une deuxieme equipe si une equipe vivante existe deja.

## Images

Le Designer UI / generateur visuel peut generer des images quand elles aident a
trancher une direction UX/UI: composition d'ecran, ambiance d'interface,
wireframe visuel, variante de densite, etat vide, flux principal ou comparaison
avant/apres.

Les images retenues sont enregistrees dans le dossier d'assets de la mission et
integrees au livrable markdown. Pour chaque image retenue, la doc indique:

- le chemin du fichier;
- l'intention ou le prompt de generation;
- le parcours, l'ecran ou la decision associee;
- le statut: `retenue`, `a tester` ou `rejetee mais instructive`;
- le retour du Testeur metier expert;
- le retour du Testeur accessibilite / novice;
- la decision de l'Orchestrateur.

Une image jolie mais fausse metier est rejetee. Une image claire mais
incomplete peut etre conservee en `a tester`. Une image rejetee n'est gardee
dans la doc que si son echec enseigne quelque chose d'utile.

## Cycle de travail

1. **Cadrage**: objectif, public, contexte, contraintes, sources et livrables.
2. **Recherche**: profils, besoins, irritants, scenarios et hypotheses.
3. **Architecture UX**: parcours, hierarchie, etats, variantes et points de
   friction.
4. **Exploration visuelle**: prompts, images candidates, variantes et principes
   UI.
5. **Double test**: test metier expert puis test accessibilite/novice.
6. **Convergence**: arbitrage, selection des images retenues, decisions et
   questions ouvertes.
7. **Cloture**: livrable final avec marqueur `UXUI-DONE`.

## Livrable final obligatoire

Le livrable de mission contient:

- objectif de la recherche;
- roles actifs et limites;
- profils utilisateurs cibles;
- parcours principal et variantes;
- problemes UX/UI priorises;
- recommandations classees par impact;
- images retenues avec liens locaux;
- prompts ou intentions de generation;
- retours du Testeur metier expert;
- retours du Testeur accessibilite / novice;
- decisions prises;
- questions ouvertes;
- mention explicite qu'aucun code n'a ete produit.

La reponse finale de l'equipe se termine par:

```text
UXUI-DONE - equipe UX/UI a fini son job
```

Ce marqueur autorise l'arret de la relance automatique.

## No-go

- Dev, patch, route, template, CSS ou test applicatif.
- Ticket dev detaille deguise en livrable UX.
- Image conservee sans decision, apprentissage ou test associe.
- Donnee privee ou chemin local d'instance dans une image ou une doc diffusable.
- Relance automatique qui duplique une equipe vivante.
- Cloture sans synthese et sans marqueur `UXUI-DONE`.
