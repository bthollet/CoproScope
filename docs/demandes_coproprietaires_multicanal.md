# Demandes coproprietaires multicanal

Date de reference: 2026-05-20

Ce document fusionne les plans existants autour de RequestOps, de l'UI demandes
et de la roadmap produit fini. Il reste generique: aucune donnee Drive, aucun
message prive, aucun nom reel et aucun connecteur externe ne sont requis pour la
V1.

## Objectif produit

CoproScope doit offrir une boite de demandes claire pour le conseil syndical et
les coproprietaires. Une demande peut arriver par plusieurs canaux, mais elle
devient toujours une trace locale normalisee, rattachee a une preuve, une
prochaine action et un niveau de diffusion.

Les questions utilisateur a rendre visibles sont:

- d'ou vient la demande;
- de quoi elle parle;
- quelle preuve ou source locale existe;
- ou elle en est;
- qui doit faire quoi maintenant;
- qui peut voir la synthese.

## Canaux V1

Canaux normalises:

- `email`: courriel importe ou resume manuellement;
- `oral`: permanence, appel, reunion ou echange verbal transforme en trace;
- `courrier`: lettre papier ou numerisee;
- `ag`: question, resolution ou suite d'assemblee generale;
- `portail_syndic`: ticket ou message recopie depuis un portail;
- `document`: demande detectee ou rattachee depuis une piece locale;
- `incident`: suite d'un signalement ou d'un incident;
- `commission`: question ou production issue d'une commission thematique;
- `contentieux`: demande liee a un dossier sensible, visible seulement selon
  droits explicites.

La V1 ne lit pas les boites mail, ne se connecte pas aux portails syndic et ne
synchronise pas de messagerie. Le canal indique l'origine de la trace choisie
par un humain ou produite par un module local.

## Modele de demande

Champs minimaux:

- `request_id`: identifiant stable;
- `received_at`: date de reception;
- `author_label`: libelle non nominatif;
- `author_role`: coproprietaire, CS, syndic, prestataire, commission ou inconnu;
- `channel`: canal normalise;
- `subject`: sujet court;
- `summary`: resume sans donnee personnelle inutile;
- `proof_ref`: preuve ou piece locale;
- `source_ref`: source locale ou objet origine;
- `status`: nouvelle, a qualifier, en cours, en attente, relance, cloturee ou
  sans suite;
- `next_action`: prochaine action concrete;
- `owner_role`: role charge du suivi;
- `due_on`: echeance ou date de relance;
- `visibility`: copro, conseil syndical, commission ou restreint;
- `related_point_id`, `related_action_id`, `related_ag_id`,
  `related_contentieux_id`: rattachements metier;
- `language_level`: novice, standard ou technique pour guider les libelles.

Les donnees personnelles restent dans les pieces protegees. Les champs de
synthese ne stockent pas volontairement email, telephone, adresse, nom complet
ou contenu sensible.

## Journal d'actions

Chaque demande ouverte doit avoir un journal lisible:

- qualification;
- demande de preuve;
- rattachement a une action ou a un point AG;
- relance syndic;
- reponse recue;
- restriction ou changement de diffusion;
- transformation en action, indicateur, suggestion ou dossier contentieux;
- cloture avec preuve ou motif.

Le journal est append-only dans l'esprit du vault: corriger ne veut pas dire
effacer. Un futur evenement signe pourra reprendre `request_created`,
`request_classified`, `request_action_logged`, `request_linked`,
`request_visibility_changed` et `request_closed`.

## UX attendue

Page `Demandes`:

- compteur des demandes ouvertes, en retard, sans preuve et non rattachees;
- filtres par canal, statut, domaine, diffusion, echeance et responsable;
- cartes `A traiter maintenant` avec pourquoi, preuve, prochaine action et
  prudence de diffusion;
- registre complet des demandes;
- journal d'actions par demande;
- etat vide indiquant comment noter une premiere demande sans promettre de
  synchronisation externe.

Le vocabulaire de premier niveau doit rester novice: `canal`, `preuve`,
`prochaine action`, `qui peut voir`, `a relancer`. Les mots techniques comme
`hash`, `vault`, `event payload` ou `plugin` restent dans les details.

## Liens avec les autres lots

- Comptes utilisateurs: l'identite locale ne suffit pas; les droits viennent du
  membre dans le coffre et des roles dates.
- Commissions: une commission peut emettre ou suivre une demande dans son
  mandat, sans acces automatique a tout le niveau CS.
- Preparation AG: une demande peut devenir question AG, resolution candidate ou
  piece a joindre.
- Contentieux: une demande sensible bascule en dossier restreint avec preuve et
  chronologie.
- Anti-confiscation: les demandes et leurs preuves doivent etre incluses dans
  les archives verifiables selon droits.
- Multi-coffres: aucune demande ne traverse un coffre; les recherches
  transversales sont opt-in et affichent le coffre source.
- Sync cloud et pair-a-pair: seuls les evenements et blobs chiffres du coffre
  sont transportes; les caches, exports et traces dechiffrees restent exclus.
- Indicateurs: volume par canal, retard moyen, demandes sans preuve et demandes
  recurrentes peuvent alimenter le cockpit si la source et la periode sont
  affichees.
- Suggestions: une recurrence ou un retard peut proposer une action, jamais la
  creer sans validation humaine.

## Accessibilite et registre de langage

Chaque terme rare doit avoir une aide accessible au clavier ou visible a
proximite:

- `relance`: nouvelle demande de reponse apres une echeance;
- `diffusion`: personnes autorisees a voir la synthese;
- `restriction`: raison pour laquelle certains details ne sont pas visibles;
- `preuve`: document ou trace qui confirme un fait.

Les tableaux ont des titres, des en-tetes explicites et des etats vides utiles.
La couleur seule ne suffit jamais a signaler un retard ou une restriction.

## Tests d'acceptation

- Une demande peut etre creee depuis chaque canal V1 sans connecteur externe.
- Une demande ouverte affiche toujours une prochaine action ou un motif
  d'attente.
- Une demande sans preuve est visible comme `preuve a rattacher`.
- Une demande sensible n'est pas visible au niveau copro par defaut.
- Une commission ne voit que les demandes de son mandat.
- Les indicateurs de demandes citent periode, source, preuve et seuil.
- Un export diffusable ne contient pas de contact prive non masque.
- Deux coffres ouverts sur le meme poste ne melangent jamais leurs demandes.
- Une archive coproprietaire permet de verifier la presence d'une demande
  restreinte sans en lire le contenu.
