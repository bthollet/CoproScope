# Demandes coproprietaires multicanaux

## Intention V1

RequestOps fournit un modele leger pour noter et suivre les demandes de coproprietaires ou du conseil syndical, quel que soit le canal d'arrivee. La V1 ne se connecte a aucun service externe et ne collecte aucune donnee privee: elle normalise uniquement des traces deja choisies par un humain ou produites par un autre module local.

Public vise:

- un coproprietaire novice qui veut comprendre ou en est sa demande;
- un conseil syndical qui doit prioriser, relancer et conserver des preuves;
- une future couche evenementielle signee, sans imposer la signature des maintenant.

## Canaux couverts

Les canaux normalises sont:

- `email`: demande recue par courriel, importee ou resumee manuellement;
- `oral`: permanence, reunion, appel ou echange verbal transforme en trace;
- `courrier`: lettre papier ou courrier numerise;
- `ag`: point, resolution ou question issue d'une assemblee generale;
- `portail_syndic`: ticket ou message dans un portail syndic;
- `document_docops`: demande detectee depuis un document indexe par DocOps;
- `incident`: suite a donner depuis IncidentOps.

La V1 ne lit pas les boites mail, ne se connecte pas aux portails syndic et ne recupere aucun contenu distant. Le canal indique seulement l'origine de la trace.

## Demande normalisee

Une demande contient volontairement peu de champs:

- `request_id`: identifiant stable, calculable si absent;
- `received_at`: date ou horodatage de reception si disponible;
- `author_label`: libelle non nominatif, par exemple `coproprietaire_lot_12`, `conseil_syndical`, `syndic`;
- `author_role`: role fonctionnel, sans contact personnel;
- `channel`: canal normalise;
- `subject`: sujet lisible;
- `summary`: resume court, sans donnees privees;
- `proof_ref`: reference de preuve, piece, message, PV, photo, ticket;
- `source_ref`: reference de source locale;
- `status`: `nouvelle`, `a_qualifier`, `en_cours`, `en_attente`, `relance`, `cloturee`, `sans_suite`;
- `next_action`: prochaine action concrete pour toute demande ouverte;
- `related_point_id`: rattachement a un point AG, CS ou ordre du jour;
- `related_action_id`: rattachement a une action existante;
- `visibility`: `copro`, `conseil_syndical`, `restreint`;
- `origin_kind` et `origin_id`: lien vers l'objet d'origine local, par exemple DocOps ou IncidentOps;
- `notes`: commentaire court non prive.

La normalisation supprime les champs evidemment prives comme email, telephone, adresse, nom ou prenom lorsqu'ils arrivent dans des donnees additionnelles. Les emails et numeros de telephone presents dans du texte sont remplaces par des marqueurs de biffage.

## Journal d'actions

Le journal capture des actions concretes, pas des intentions vagues:

- `journal_id`: identifiant stable;
- `request_id`: demande rattachee;
- `occurred_at`: date ou horodatage;
- `actor_role`: role de l'acteur, sans nom personnel;
- `action_type`: `qualification`, `relance`, `reponse`, `rattachement`, `cloture`, `note` ou autre libelle controle;
- `summary`: fait observe ou action realisee;
- `proof_ref` et `source_ref`: preuve ou source de cette action;
- `status_after`: statut apres l'action si applicable;
- `next_action`: suite concrete;
- `visibility`: niveau de diffusion;
- `event_hash`: hash canonique du futur evenement non signe.

Cette separation permet de montrer a un novice ce qui s'est passe, et au conseil syndical ce qui reste a faire.

## Preparation aux evenements signes

RequestOps produit une forme `coproscope.unsigned_event.v1`:

- `event_type`: `request_created` pour la demande ou
  `request_action_recorded` pour une action de suivi;
- `object_id`: identifiant de la demande ou de l'action;
- `payload`: donnees nettoyees, sans champs vides ni contacts prives;
- `signature`: vide en V1.

Le hash est calcule sur un JSON canonique trie. Il ne vaut pas signature, mais il rend la transition vers une signature future plus simple: le contenu a signer sera deja stable.

## Limites assumées

- Aucun connecteur reel en V1.
- Aucune synchronisation email, portail syndic ou messagerie.
- Aucun stockage volontaire de donnees privees.
- Aucun arbitrage automatique: le modele structure, il ne decide pas.
- Le niveau `restreint` doit etre choisi des qu'une demande touche un conflit, un impaye, un litige ou une situation personnelle.
