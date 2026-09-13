# Coordination cycle N+2 - Pieces manquantes puis detail action

Date: 2026-05-21.

Role: designer de service / visuels.
Perimetre: preparation image-first du prochain bloc, sans modification du code
applicatif.

## Images pretes

Images sources corrigees, a utiliser avant dev:

- `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\09_pieces_manquantes_n2_liste_coherente.png`
- `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\07_pieces_manquantes_n2.png`
- `C:\Users\brice\CoproScope\coproscope\docs\assets\ux-visuels-fictifs-2026-05-21\08_detail_action_n2.png`

Les visuels historiques restent conserves:

- `docs/assets/ux-visuels-fictifs-2026-05-21/02_pieces_manquantes.png`
- `docs/assets/ux-visuels-fictifs-2026-05-21/04_detail_action.png`

Corrections apportees dans les variantes N+2:

- suppression des libelles de boutons tronques;
- objet principal visible dans le premier fold;
- raisons utilisateur visibles ligne par ligne;
- rappel explicite: CoproScope prepare ou trace, il n'envoie pas
  automatiquement;
- ordre de travail force: `Pieces manquantes` puis `Detail action`.

Ajout designer apres test novice: la relance est validee, mais
`Pieces manquantes` est refusee si la liste semble vide, generique ou
incoherente. La priorite dev devient donc la page `Pieces manquantes`, avec
cartes remplies et coherentes avant de reprendre le detail action.

## Pieces manquantes - attentes bouton par bouton

Route cible: `/pieces?proof=missing`.

Attente generale: un membre CS novice doit pouvoir dire quelle piece manque,
pourquoi elle compte, a qui la demander, et quel bouton lance la prochaine
action sans croire a un envoi automatique.

Image prioritaire apres retour novice:
`docs/assets/ux-visuels-fictifs-2026-05-21/09_pieces_manquantes_n2_liste_coherente.png`.

Chaque carte de piece doit afficher:

- `Pourquoi`: raison simple du manque;
- `Detenteur`: syndic, conseil syndical, prestataire ou coproprietaire fictif;
- `Lien`: action, compte, demande ou dossier rattache;
- boutons utiles: `Relancer syndic`, `Ajouter reponse recue`, puis lien
  `Ouvrir action` ou `Ouvrir compte`.

| Bouton | Attente utilisateur avant clic | Resultat attendu apres clic | No-go |
| --- | --- | --- | --- |
| `Creer demandes syndic` | Je pense preparer les demandes pour les pieces visibles. | Ouvre une preparation groupee de demandes, avec recapitulatif avant creation et mention aucun envoi automatique. | Creation silencieuse, envoi implicite, perte du token local. |
| `Voir pieces privees` | Je veux filtrer les pieces non diffusables ou a verifier. | Affiche seulement les lignes marquees privees/fictives avec raison de restriction et action possible. | Filtre sans explication ou confusion entre prive et erreur. |
| `Demander` | Je dois demander une piece absente. | Ouvre une demande syndic pre-remplie avec piece attendue, raison, source et retour a la liste. | Le bouton ouvre seulement un fichier ou change le statut sans confirmation. |
| `Relancer` | Une demande existe deja; je dois preparer une relance. | Ouvre une relance copiable ou une fiche demande avec historique, canal, derniere relance et trace externe. | Le bouton laisse croire que CoproScope a envoye un message. |
| `Ajouter` | J'ai une piece candidate a rattacher. | Ouvre le depot/rattachement avec contexte conserve: action, demande, piece attendue, confidentialite. | Depot generique sans rattachement ni prochaine etape. |
| `Ajouter reponse recue` | J'ai recu une reponse du syndic hors outil. | Ouvre le depot/rattachement sur la piece selectionnee, avec statut `reponse recue a verifier`. | Reponse importee comme preuve finale sans verification. |
| `Ouvrir action` | Je veux comprendre le suivi lie a cette piece. | Ouvre le detail action selectionne avec retour vers `Pieces manquantes`. | Page action generique ou perte du contexte piece. |
| `Ouvrir compte` | La piece manque parce qu'un point comptable doit etre explique. | Ouvre le point comptes lie, avec question syndic et piece attendue. | Retour vers `/comptes` non filtre ou jargon comptable seul. |
| `Question` | La piece manque parce qu'une clarification syndic est necessaire. | Ouvre une question syndic neutre, copiable, rattachee au point comptable ou a la decision. | Langage accusatoire ou question sans preuve attendue. |

Etat vide exige: si aucune piece ne manque, la page doit afficher `Aucune piece
a demander pour le moment`, puis proposer `Voir toutes les pieces` et `Retour au
cockpit`, sans tableau vide brut.

## Detail action - attentes bouton par bouton

Route cible: `/actions/{id}` ou route equivalente selectionnee depuis
`/actions?priority=P1`.

Attente generale: depuis une ligne de retard, le membre CS novice ouvre une fiche
unique qui raconte le contexte, l'etat, la preuve attendue, la relance possible,
l'historique et la note de passation.

| Bouton | Attente utilisateur avant clic | Resultat attendu apres clic | No-go |
| --- | --- | --- | --- |
| `Retour aux retards` | Je reviens a la liste filtree d'ou je viens. | Retour vers `/actions?priority=P1` avec token et selection conserves si possible. | Retour cockpit ou perte du filtre sans indication. |
| `Exporter fiche` | Je prepare une version partageable de cette fiche. | Ouvre un apercu d'export derive avec inclus/exclus, biffage, pas de chemin prive. | Telechargement direct sans controle de public ni confidentialite. |
| `Cloturer si preuve OK` | Je ne peux clore que si la preuve finale est validee. | Bouton actif seulement si preuve finale presente; sinon message expliquant la piece manquante. | Cloture possible alors que `Reponse syndic` manque. |
| `Preparer relance` | Je prepare un message, pas un envoi. | Ouvre onglet/route relance avec brouillon copiable, piece attendue, canal et trace externe. | Promesse d'envoi automatique ou absence d'historique. |
| `Ajouter preuve` | Je rattache la piece recue a cette action. | Ouvre depot/rattachement avec action deja selectionnee et statut `preuve candidate` avant validation. | Piece importee comme preuve finale sans verification. |
| `Changer statut` | Je mets a jour l'etat de suivi. | Ouvre choix simples: en attente syndic, preuve recue a verifier, bloque, clos si preuve OK. | Codes internes seuls ou changement sans journal. |
| `Marquer attente` | Je note qu'une reponse externe est attendue. | Ajoute une attente avec date, canal, responsable et prochaine verification. | Statut vague sans echeance ni responsable. |
| `Deposer preuve` | J'ajoute une preuve locale candidate. | Ouvre depot avec controle prive/fictif, rattachement a la demande et retour detail action. | Depot generique ou fuite chemin raw. |
| `Demander piece` | Je retourne vers la piece manquante liee. | Ouvre `/pieces?proof=missing` filtre sur cette action/piece. | Liste complete non filtree ou doublon de demande. |
| `Copier brouillon` | Je copie le message pour l'envoyer hors CoproScope. | Copie le texte et affiche un rappel: envoi externe a tracer ensuite. | Message marque envoye alors qu'il est seulement copie. |
| `Tracer envoi` | J'enregistre ce qui a ete fait hors outil. | Ouvre saisie date, canal, destinataire, prochain controle. | Trace sans date/canal ou confusion avec envoi reel. |

Etat vide exige: si l'action n'est pas trouvee, afficher une fiche vide utile
avec `Retour aux retards`, `Voir actions ouvertes`, et une phrase simple:
`Cette action n'est pas disponible dans ce coffre local fictif`.

## Commande dev prete

```text
Role: dev CoproScope cycle N+2.
Objectif: livrer d'abord /pieces?proof=missing comme page prioritaire,
puis le detail action /actions/{id} ou equivalent, en suivant les PNG:
- docs/assets/ux-visuels-fictifs-2026-05-21/09_pieces_manquantes_n2_liste_coherente.png
- docs/assets/ux-visuels-fictifs-2026-05-21/07_pieces_manquantes_n2.png
- docs/assets/ux-visuels-fictifs-2026-05-21/08_detail_action_n2.png

Contraintes:
- conserver token local sur tous les liens et formulaires;
- aucune action ne doit envoyer un message automatiquement;
- distinguer piece manquante, preuve candidate, preuve finale validee;
- remplir les cartes Pieces manquantes avec pourquoi, detenteur, lien
  comptes/action, relance syndic et ajout de reponse recue;
- chaque bouton doit avoir un etat vide utile et une action retour;
- ne pas exposer chemins raw ni donnees personnelles brutes;
- conserver les donnees fictives FICTIF deja utilisees:
  REQ-FICTIF-ASSURANCE-B12, DOC-FICTIF-B12-ASSUR,
  DOC-FICTIF-SYNDIC-ASSUR, DOC-FICTIF-C31-INFILT.

Tests attendus depuis server/:
.\.venv\Scripts\python.exe -m unittest tests.test_ui_pieces_viewmodel tests.test_ui_action_detail_route tests.test_ui_registre_actions tests.test_ui_smoke_routes_expanded -v

Acceptation utilisateur:
un membre CS novice doit pouvoir partir d'une liste Pieces manquantes remplie,
identifier le detenteur de la piece, relancer le syndic, ajouter une reponse
recue, puis ouvrir le compte ou l'action liee sans perdre le contexte.
```

## Prochain test image CS novice

Support de test: afficher d'abord
`09_pieces_manquantes_n2_liste_coherente.png`, puis seulement apres acceptation
`08_detail_action_n2.png`, sans expliquer les libelles.

Script en 7 minutes:

1. Demander: `Quelle piece manque en premier, et pourquoi ?`
2. Demander: `Qui detient cette piece ?`
3. Demander: `Quel bouton cliqueriez-vous pour relancer le syndic ?`
4. Demander: `Si vous recevez une reponse du syndic, ou l'ajoutez-vous ?`
5. Demander: `Quel lien ouvre le compte ou l'action rattachee ?`
6. Montrer le detail action, puis demander: `Pourquoi l'action ne peut-elle pas
   etre cloturee maintenant ?`
7. Demander: `Quel bouton prepare la relance et quel bouton trace ce qui a ete
   fait hors CoproScope ?`
8. Phrase de validation attendue: `Je sais quelle piece manque, qui l'a, quoi
   relancer, ou ajouter la reponse recue, et quel compte ou action ouvrir.`

Go image: le novice cite `Relancer syndic`, `Ajouter reponse recue`,
`Ouvrir action` ou `Ouvrir compte`, et explique pourquoi la piece manque.

No-go image: le novice trouve la liste vide/generique, ne voit pas qui detient
la piece, ne trouve pas `Ajouter reponse recue`, ou ne voit aucun lien
comptes/action.
