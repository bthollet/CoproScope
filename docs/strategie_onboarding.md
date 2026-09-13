# Strategie onboarding CoproScope

Date de reference: 2026-05-21

Statut: etude initiale pour inscription roadmap.

## Diagnostic

CoproScope dispose deja des surfaces necessaires a un conseil syndical:
cockpit, actions, pieces, demandes, comptes, depot, memoire, pilotage et
passation. Le probleme d'onboarding n'est donc pas l'absence d'ecrans. Le
probleme est l'absence d'un premier succes guide et verifiable.

Les tests novices montrent trois ruptures:

- l'utilisateur voit beaucoup de contexte technique avant l'action humaine;
- plusieurs portes importantes expliquent le parcours sans permettre de le
  realiser immediatement;
- les notions coffre, role, sync, preuve, action et diffusion sont comprises
  separement, mais pas encore comme une boucle de travail unique.

L'onboarding doit donc transformer la premiere ouverture en progression utile:
comprendre le contexte, choisir une intention, accomplir une action limitee,
voir la preuve ou la trace produite, puis savoir quoi faire ensuite.

## Principe produit

L'onboarding CoproScope ne doit pas etre une visite guidee du logiciel. Il doit
etre un parcours de travail court, local-first et prudent.

Phrase cible:

> En moins de 10 minutes, un membre de conseil syndical novice sait dans quel
> coffre il agit, ce qu'il peut voir, quelle action faire maintenant, quelle
> preuve regarder, et ce qui peut etre partage.

Ce parcours doit rester valable sans compte cloud, sans serveur central et sans
donnees reelles dans les exemples publics.

## Publics cibles

| Public | Besoin d'entree | Risque si l'onboarding echoue |
|---|---|---|
| Nouveau membre CS | Reprendre les sujets ouverts, preuves et relances | Perte de memoire, action au mauvais endroit, diffusion imprudente |
| Coproprietaire lecteur | Comprendre ce qui le concerne et ce qui reste restreint | Confusion entre restriction legitime et panne ou retention |
| Referent commission | Travailler un sujet sans acceder a tout | Acces trop large, production non rattachee a une preuve |
| Administrateur local benevole | Ouvrir le bon coffre et verifier la sync | Melange de coffres, cache ou export dans le mauvais dossier |

## Parcours d'onboarding recommande

### 1. Premier repere: contexte compact

Avant une action sensible, afficher un bandeau compact:

- coffre actif;
- role courant;
- niveau d'acces;
- sync: locale, externe a verifier ou non configuree;
- derniere verification du coffre.

Ce bloc doit rassurer sans repousser l'action principale. Les alertes techniques
longues deviennent une checklist `Configuration locale a terminer`.

### 2. Choix d'intention

Au lieu de faire decouvrir toutes les routes, proposer quatre intentions:

- `Je dois traiter une priorite`;
- `Je dois ajouter ou rattacher un document`;
- `Je dois demander une piece ou relancer le syndic`;
- `Je dois transmettre ou reprendre la memoire`.

Chaque intention ouvre directement une action disponible, pas une page
explicative sans formulaire.

### 3. Premier succes guide

Le premier succes doit produire un artefact visible:

- une demande creee ou preparee;
- un document depose avec statut local;
- une action creee ou rattachee;
- une preuve ajoutee ou une piece manquante qualifiee;
- un apercu de passation avec blocages explicites.

L'utilisateur doit voir le resultat, la prochaine etape et la prudence de
diffusion.

### 4. Boucle canonique

Toutes les surfaces d'onboarding doivent reprendre la meme boucle:

1. Pourquoi ce sujet est la.
2. Quelle preuve ou source existe.
3. Quelle action est possible maintenant.
4. Qui peut voir ou recevoir le resultat.
5. Quelle trace restera dans la memoire.

Cette boucle doit etre visible dans le cockpit, les actions, les demandes, le
depot, les pieces manquantes, les comptes et la passation.

### 5. Reprise sans tutoriel

Au retour suivant, l'utilisateur ne doit pas revoir une visite generale. Il doit
retrouver:

- `Continuer ce que vous aviez commence`;
- `A faire maintenant`;
- `Derniere trace creee`;
- `Blocage a lever`.

L'onboarding est donc une checklist de progression et non une couche modale
jetable.

## Surfaces a raccorder

| Surface | Changement attendu |
|---|---|
| Cockpit | Mettre une action humaine prioritaire avant les alertes de configuration. |
| `/documents/ajouter` | Offrir un champ fichier ou un CTA primaire vers `/depot?intent=document`. |
| `/demandes` | Ajouter un formulaire minimal de demande avec sujet, canal, preuve/source, diffusion et prochaine action. |
| `/actions` | Rendre `Nouvelle action` reellement createur: choix source, responsable, echeance, preuve attendue. |
| `/depot` | Apres depot, proposer `Classer`, `Verifier diffusion`, `Rattacher a une action`, `Voir pieces candidates`. |
| `/pieces?proof=missing` | Clarifier les compteurs zero et guider vers demande, relance ou depot seulement si un manque existe. |
| `/chantiers` / memoire | Mettre en avant `A transmettre maintenant` et le pack passation avec blocages. |
| Gouvernance | Introduire plus tard `Mes coffres`, `Membres et droits`, `Recuperation` comme onboarding de confiance. |

## Contrats de sortie

Un onboarding est livrable quand:

- un utilisateur novice accomplit une premiere action en moins de 10 minutes;
- aucun ecran d'entree ne promet une action sans formulaire, lien ou resultat;
- les compteurs a zero ne restent pas des CTA prioritaires;
- les termes coffre, role, sync, preuve, action et diffusion sont expliques au
  moment utile;
- toute action mutable produit ou prepare une trace lisible;
- le parcours distingue local, export, sync et diffusion;
- les erreurs disent probleme, cause probable et correction;
- le test novice peut rejouer les quatre intentions sans accompagnement.

## Non-objectifs

- Pas de landing page marketing.
- Pas de tour produit qui masque les blocages reels.
- Pas de compte cloud obligatoire pour comprendre le produit local.
- Pas d'exemples publics avec donnees d'instance reelles.
- Pas de simplification qui cache les restrictions ou les preuves manquantes.

## Implication roadmap

L'onboarding doit etre traite comme un chantier transverse rattache au produit
fini UX, aux tests novices et au futur packaging. Il doit arriver avant une
distribution non accompagnee, car il conditionne la capacite d'un conseil
syndical a utiliser CoproScope sans assistance technique.
