# Etat du developpement

## Resume franc

CoproScope n'est plus une simple intention. Le depot public contient deja un noyau logiciel, une CLI exploitable, une instance synthetique, un outillage de publication propre vers GitHub, et une premiere couche documentaire suffisamment solide pour soutenir une vraie relecture.

L'enjeu n'est plus de prouver que le projet existe. L'enjeu est maintenant de le rendre plus net, plus contributif et plus robuste.

## Ce qui est deja livre

- depot public initialise et relie a GitHub ;
- paquet `server/` avec CLI `coprocs` ;
- pipeline v1: inventaire, extraction texte, classement, completude, KPI, AG, synthese de diligence publique ;
- serveur MCP minimal ;
- schemas, configs, prompts et templates versionnes ;
- premiere extraction publique de la couche Audit360 sous forme de doc, schemas et gabarits ;
- instance synthetique publique pour les tests ;
- garde-fous de partage (`share-audit`, `share-export`) ;
- documentation publique structuree en francais.

## Ce qui est en cours

- enrichir DocOps sur de vrais corpus ;
- epaissir SyndicOps sur les relances et la tracabilite fine ;
- affiner AGOps sur les annexes, majorites et suites post-AG ;
- outiller davantage Audit360 comme couche transverse de controles et diligences ;
- pousser plus loin la francisation la ou elle apporte une vraie clarte sans casser les interfaces techniques.

## Ce qui vient ensuite

- ContractOps ;
- WorksOps ;
- CommsOps ;
- consolidation des conventions de contribution publique.

## Niveau de maturite par bloc

| Sujet | Niveau actuel | Commentaire |
|---|---|---|
| Frontiere public / prive | bon | garde-fous presents, export public outille |
| CLI | bon socle | surface stable, encore perfectible |
| DocOps | bon socle | deja utile, heuristiques a enrichir |
| SyndicOps | embryon utile | base en place, workflows a epaissir |
| AGOps | premiere version | signaux utiles, couverture encore partielle |
| Audit360 | extraction publique amorcee | formes generiques visibles, outillage encore a epaissir |
| Documentation produit | bon socle | suffisamment claire pour une vraie relecture |
| Francophonie | en cours d'inscription | preference explicite, chantier encore ouvert |

## Ce qu'un relecteur doit retenir

- le produit a deja une forme coherente ;
- la separation entre depot public et instances privees est un principe central, pas un detail ;
- le projet vise d'abord l'utilite operationnelle, ensuite l'extension fonctionnelle ;
- les choix de structure ne sont pas encore tous figes, mais la direction est deja nette.

## Ce qu'une bonne relecture peut apporter maintenant

- dire si la promesse produit se comprend vite ;
- verifier si les priorites fonctionnelles semblent justes ;
- pointer les zones encore trop implicites ;
- aider a rendre le depot plus accueillant pour les futures contributions.

## Prochaine phase logique

La suite naturelle est de consolider les couches deja presentes plutot que d'ouvrir trop tot de nouveaux blocs:

1. enrichir les regles et sorties DocOps ;
2. densifier les chaines de preuve SyndicOps ;
3. fiabiliser AGOps sur de vrais cas de preparation ;
4. epaissir Audit360 sur les controles, preuves attendues et diligences ;
5. continuer a extraire vers le public uniquement ce qui est proprement genericisable.
