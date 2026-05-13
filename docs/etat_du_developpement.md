# Etat du developpement

## Resume franc

CoproScope n'est plus une simple intention. Le produit public dispose deja d'un noyau logiciel, d'une CLI, d'une instance synthetique et d'un outillage de publication vers GitHub sans fuite de donnees privees.

## Ce qui est deja en place

- depot public initialise et branche sur GitHub ;
- paquet `server/` avec CLI `coprocs` ;
- pipeline v1: inventaire, extraction texte, classement, completude, KPI, AG, synthese due diligence ;
- serveur MCP minimal ;
- schemas, configs, prompts et templates versionnes ;
- instance synthetique publique pour les tests ;
- politique et outillage de partage (`share-audit`, `share-export`) ;
- premiere couche explicite de francophonie fonctionnelle.

## Ce qui reste volontairement en chantier

- enrichir les heuristiques de DocOps sur corpus reels ;
- muscler SyndicOps pour les relances et la traçabilite fine ;
- affiner AGOps sur les annexes, majorites et suites post-AG ;
- preparer les futurs modules ContractOps, WorksOps et CommsOps ;
- poursuivre la francisation la ou elle apporte de la clarte sans casser les interfaces techniques.

## Niveau de maturite par bloc

| Sujet | Niveau actuel | Commentaire |
|---|---|---|
| Frontiere public / prive | bon | garde-fous presents, export public outille |
| CLI | bon socle | surface stable, encore perfectible |
| DocOps | bon socle | deja utile, heuristiques a enrichir |
| SyndicOps | embryon utile | base en place, workflows a epaissir |
| AGOps | premiere version | signaux utiles, couverture encore partielle |
| Documentation produit | en progression | vision plus claire, a maintenir vivante |
| Francophonie | en cours d'inscription | preference devenue explicite |

## Prochaine phase logique

La suite naturelle est de consolider les couches deja presentes plutot que d'ouvrir trop tot de nouveaux blocs:

1. enrichir les regles et les sorties DocOps ;
2. densifier les chaines de preuve SyndicOps ;
3. fiabiliser AGOps sur de vrais cas de preparation ;
4. continuer a extraire vers le public ce qui est vraiment reutilisable.
