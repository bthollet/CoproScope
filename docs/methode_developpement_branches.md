# Methode de developpement par branche

Date: 2026-05-31
Statut: regle commune referencee par `AGENTS.md`.

Cette note rend explicite la regle deja citee par `AGENTS.md`: une branche de
developpement ne demarre pas directement par le code quand le sujet est une
nouvelle feature, une feature transverse ou une zone sensible.

## Sequence obligatoire

1. Enquete et cadrage documentaire.
2. Routage dans `docs/strategie_equipes_multi_agents.md`.
3. Mobilisation d'une equipe d'agents adaptee au sujet.
4. Decision GO/NO-GO dev rendue par cette equipe, pas par l'owner seul.
5. Doc + dev sur un perimetre borne.
6. Tests, contre-tests et preuves.
7. Trace finale dans `docs/presence_agents.md` et le gouvernail.

## Gate nouvelle feature

Avant tout code applicatif, le cadrage doit contenir:

- probleme utilisateur;
- perimetre et hors perimetre;
- blueprint de service ou blueprint UI selon le cas;
- event storming ou parcours-evenements;
- contrat de donnees;
- risques privacy, securite, licence et maintenance;
- criteres d'acceptation;
- tests attendus;
- roles d'agents attendus;
- decision GO/NO-GO avant dev.

Si ces elements ne sont pas prets, les devs restent en lecture seule.

Si du code a deja ete esquisse avant ce gate, il reste hors validation produit
tant que la sequence de cadrage et d'equipe n'a pas ete reprise.

## Quand le code peut commencer

Le code commence seulement quand:

- le `RM-*`, le `CH-*` et le `CONV-*` sont declares;
- l'ownership des fichiers est clair;
- les fichiers a eviter sont nommes;
- les tests ou preuves sont connus;
- le cadrage a donne une coupe V1 precise;
- le routeur d'equipe a choisi une equipe-type;
- les roles d'agents utiles ont rendu ou sont explicitement traces comme
  indisponibles;
- le GO dev vient d'une synthese d'equipe, meme si un seul owner ecrit le code;
- aucune collision vivante ne bloque le perimetre.

Un owner unique peut implementer apres le GO, mais il ne remplace pas les
roles d'equipe prevus par la doctrine. Une nouvelle feature ne passe pas
`PRET_A_INTEGRER` sans retours d'equipe traces.

Pour une iteration UI, ajouter les gates du protocole agile:

- UI reelle cible nommee;
- visuel IA bitmap ou waiver trace;
- blueprint UI ou waiver trace;
- qualification novice avant dev.

## Sortie attendue

La fin du lot doit dire clairement:

- ce qui a ete livre;
- ce qui reste brouillon;
- les tests lances ou non lances;
- les limites et risques;
- le prochain mouvement propose.
