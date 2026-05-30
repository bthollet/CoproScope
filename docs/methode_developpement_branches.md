# Methode de developpement par branche

Date: 2026-05-31
Statut: regle commune referencee par `AGENTS.md`.

Cette note rend explicite la regle deja citee par `AGENTS.md`: une branche de
developpement ne demarre pas directement par le code quand le sujet est une
nouvelle feature, une feature transverse ou une zone sensible.

## Sequence obligatoire

1. Enquete et cadrage documentaire.
2. Decision GO/NO-GO dev.
3. Doc + dev sur un perimetre borne.
4. Tests et preuves.
5. Trace finale dans `docs/presence_agents.md` et le gouvernail.

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
- decision GO/NO-GO avant dev.

Si ces elements ne sont pas prets, les devs restent en lecture seule.

Si du code a deja ete esquisse avant ce gate, il doit etre marque comme
brouillon non integrable. Il peut aider a comprendre, mais il ne devient pas la
source de verite de la feature.

## Quand le code peut commencer

Le code commence seulement quand:

- le `RM-*`, le `CH-*` et le `CONV-*` sont declares;
- l'ownership des fichiers est clair;
- les fichiers a eviter sont nommes;
- les tests ou preuves sont connus;
- le cadrage a donne une coupe V1 precise;
- aucune collision vivante ne bloque le perimetre.

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
