# Instance synthetique de copropriete

Cette instance publique, non sensible, sert de terrain de validation pour CoproScope.

## A quoi elle sert

- verifier le comportement de la CLI ;
- faire tourner les tests publics ;
- demonstrer le pipeline sans utiliser de donnees reelles ;
- tester le screening confidentialite et la file de biffage sans risque ;
- exercer la frontiere entre depot public et travail prive.

## Ce qu'elle contient

- des documents de demonstration ;
- un `instance.yml` public ;
- des matrices et artefacts synthetiques utiles a la validation, y compris pour les sorties de type Audit360 ;
- des cas publics pour DocOps, PrivacyOps, FactureOps, ComptaScope et AGOps.

## Ce qu'elle ne doit pas contenir

- aucune donnee reelle de copropriete ;
- aucun secret ;
- aucun journal ou export local genere a l'execution dans Git.

Les contenus `logs/`, `outputs/`, `registers/` et `staging/` sont generes localement et doivent rester hors commit.

## Commandes utiles

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli pipeline run --instance-root .\examples\synthetic_copro
.\server\.venv\Scripts\python.exe -m coproscope.cli privacy screen-existing --instance-root .\examples\synthetic_copro
.\server\.venv\Scripts\python.exe -m coproscope.cli privacy redaction-queue --instance-root .\examples\synthetic_copro
.\server\.venv\Scripts\python.exe -m coproscope.cli invoices extract --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli accounting reconstruct --instance-root .\examples\synthetic_copro --year 2025
```
