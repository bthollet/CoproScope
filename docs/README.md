# Documentation CoproScope

Cette documentation est ecrite pour etre **pedagogique**, **franche** et **utile**.

Son role n'est pas seulement de decrire le projet. Elle doit aussi aider quelqu'un qui arrive avec peu de contexte a comprendre vite:

- ce que CoproScope essaie de resoudre ;
- ce qui est deja solide ;
- ou une relecture peut vraiment faire progresser le projet.

## Parcours de lecture

### Pour comprendre l'idee

1. [Concept et philosophie](./concept_et_philosophie.md)
2. [Fonctions cibles](./fonctions_cibles.md)
3. [Etat du developpement](./etat_du_developpement.md)

### Pour relire le repo

1. [Architecture et flux](./architecture_et_flux.md)
2. [Plan d'implementation](./implementation_plan.md)
3. [Politique de partage GitHub](./github_sharing.md)

### Pour contribuer

1. relire le [README racine](../README.md) ;
2. verifier la [Politique de partage GitHub](./github_sharing.md) ;
3. utiliser l'instance publique [`examples/synthetic_copro/`](../examples/synthetic_copro/) pour les demonstrations et validations.

## Selon le temps disponible

| Temps | Lire d'abord | Ce que ca apporte |
|---|---|---|
| 5 min | [Concept et philosophie](./concept_et_philosophie.md) + [Etat du developpement](./etat_du_developpement.md) | une vision nette du produit et de sa maturite |
| 15 min | ajouter [Fonctions cibles](./fonctions_cibles.md) + [Architecture et flux](./architecture_et_flux.md) | une base suffisante pour faire une vraie revue |
| 30 min | tout le bloc + [Plan d'implementation](./implementation_plan.md) | une base solide pour challenger les choix et contribuer |

## Carte de la doc

| Document | A quoi il sert |
|---|---|
| [Concept et philosophie](./concept_et_philosophie.md) | comprendre le probleme vise et la promesse produit |
| [Fonctions cibles](./fonctions_cibles.md) | voir les blocs fonctionnels recherches et leur priorisation |
| [Etat du developpement](./etat_du_developpement.md) | distinguer ce qui est livre, en cours et plus tard |
| [Architecture et flux](./architecture_et_flux.md) | lire rapidement la separation code / instance / sorties |
| [Plan d'implementation](./implementation_plan.md) | garder le contrat de construction du produit |
| [Politique de partage GitHub](./github_sharing.md) | proteger la frontiere entre travail prive et depot public |

## Ligne editoriale

La documentation publique de CoproScope privilegie:

- le francais quand il sert la comprehension ;
- la clarte operationnelle plutot qu'un ton marketing ;
- la distinction nette entre **livre**, **en cours** et **vise** ;
- des formulations qui aident autant un relecteur qu'un contributeur.
