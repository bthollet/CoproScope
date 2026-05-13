# Instance synthetique de copropriete

Cette instance publique, non sensible, sert de terrain de validation pour CoproScope.

## A quoi elle sert

- verifier le comportement de la CLI ;
- faire tourner les tests publics ;
- demonstrer le pipeline sans utiliser de donnees reelles ;
- exercer la frontiere entre depot public et travail prive.

## Ce qu'elle contient

- des documents de demonstration ;
- un `instance.yml` public ;
- des matrices et artefacts synthetiques utiles a la validation.

## Ce qu'elle ne doit pas contenir

- aucune donnee reelle de copropriete ;
- aucun secret ;
- aucun journal ou export local genere a l'execution dans Git.

Les contenus `logs/`, `outputs/`, `registers/` et `staging/` sont generes localement et doivent rester hors commit.
