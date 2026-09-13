# Contentieux UX

Date de reference: 2026-05-20

Ce document fusionne les plans existants autour des dossiers contentieux,
AG/contentieux/passation, droits, restrictions, archives et UX novice. Il reste
factuel, generique et sans donnee Drive privee.

## Objectif produit

CoproScope doit permettre de suivre un dossier contentieux ou precontentieux
comme un dossier probatoire restreint. Le produit doit aider a conserver les
faits, dates, pieces, demandes, reponses, echeances et restrictions, sans
produire d'avis juridique automatique.

L'utilisateur doit voir:

- le dossier sensible concerne;
- la chronologie factuelle;
- les pieces disponibles ou manquantes;
- les prochaines actions;
- les restrictions d'acces;
- ce qui peut etre partage, masque ou seulement signale comme existant.

## Principes V1

- Factuel seulement: constats, pieces, dates, montants synthetiques si
  necessaire, demandes et reponses.
- Pas d'avis juridique: pas de probabilite de succes, pas de consigne
  d'assigner, pas de qualification automatique.
- Restriction par defaut: un contentieux n'est pas visible au niveau copro sans
  decision explicite de diffusion.
- Journal append-only: correction par nouvel evenement, pas suppression
  silencieuse.
- Preuve avant synthese: toute note doit citer une piece, une source ou un
  motif `preuve a obtenir`.

## Objets metier

- `ContentieuxCase`: dossier factuel, statut, restriction, responsable,
  prochaine action.
- `ContentieuxTimelineEntry`: fait date, source, preuve, action ou relance.
- `LegalRiskNote`: note de vigilance non juridique, limitee aux constats et
  pieces a verifier.
- `EvidenceRef`: reference de piece avec restriction, diffusion et statut.
- `EvidenceBundle`: paquet de preuves pour revue, export controle ou passation.
- `RestrictionDecision`: justification de restriction, auteur, date, motif,
  duree ou revue attendue.
- `ContentieuxExport`: version controlee pour avocat, syndic, assurance, CS ou
  copro, selon droits.

Evenements futurs: `contentieux_case_created`, `contentieux_fact_logged`,
`contentieux_evidence_linked`, `contentieux_restriction_changed`,
`contentieux_export_created`, `legal_risk_note_recorded`.

## UX attendue

Page `Contentieux` ou section dediee de `AG/contentieux`:

- bandeau: coffre actif, role courant, niveau d'acces, restriction et derniere
  verification;
- cartes `A faire maintenant`: echeance, piece manquante, relance, restriction
  a revoir, export a valider;
- chronologie factuelle;
- liste des preuves avec statut: recue, a verifier, manquante, restreinte;
- panneau `Qui peut voir quoi`;
- panneau `Ce qui existe mais reste restreint` pour les profils autorises a
  verifier la presence sans lire le contenu;
- export controle avec masquage obligatoire quand la diffusion sort du cercle
  restreint.

Les libelles de premier niveau restent simples: `dossier sensible`, `preuve`,
`date importante`, `qui peut voir`, `a faire`. Les termes `hash`, `payload`,
`ACL` ou `enveloppe de cle` restent dans les details techniques.

## Liens avec les autres lots

- Demandes multicanal: une demande litigieuse bascule en dossier restreint avec
  trace de canal et preuve d'origine.
- Preparation AG: un sujet contentieux peut alimenter une question AG sous forme
  controlee ou rester hors diffusion selon decision.
- Comptes utilisateurs: acces par role, membre du coffre, appareil et
  autorisation explicite; l'administrateur local technique n'a pas acces
  implicite au contenu.
- Commissions: une commission n'accede a un contentieux que si son mandat et un
  `AccessGrant` l'autorisent.
- Anti-confiscation: les dossiers restreints existent dans l'archive complete
  chiffree; leur presence et integrite sont verifiables sans lecture.
- Multi-coffres: un contentieux ne traverse jamais les coffres; exports et
  caches restent separes.
- Sync cloud et pair-a-pair: seul le vault chiffre est synchronise; aucun export
  contentieux dechiffre ne part dans le dossier sync.
- Indicateurs: echeances, pieces manquantes, montants exposes et retards
  peuvent alimenter le cockpit avec niveau de restriction visible.
- Veille open source: PDF, OCR et recherche peuvent aider a indexer les pieces,
  mais sans modifier les originaux et apres revue licence/securite.
- Suggestions: une suggestion peut recommander de demander une preuve ou de
  revoir une restriction, jamais de lancer une procedure.

## Anti-confiscation et archives

Un coproprietaire autorise a telecharger l'archive complete doit pouvoir:

- verifier que le dossier contentieux existe;
- verifier les empreintes et la continuite des evenements;
- voir qu'une restriction a ete decidee, par qui, quand et pourquoi;
- ne pas dechiffrer les pieces si son role ne le permet pas.

Les cles de compartiment contentieux doivent avoir des filets de recuperation:
quorum, rotation, revocation et ceremonie de recuperation historisee.

## Accessibilite et langage

Definitions courtes a afficher au moment utile:

- `contentieux`: dossier lie a un desaccord ou une procedure possible ou en
  cours;
- `precontentieux`: situation a suivre avant eventuelle procedure;
- `restriction`: acces limite pour proteger une information sensible;
- `chronologie`: liste datee des faits et pieces;
- `export controle`: copie partageable apres verification des droits et
  masquage.

Les alertes doivent indiquer le probleme, la cause probable et l'action de
correction. Les restrictions ne doivent pas etre signalees par la couleur seule.

## Tests d'acceptation

- Un contentieux est restreint par defaut.
- Une note de risque contenant une consigne juridique automatique est refusee.
- Une chronologie ne peut pas citer une piece inexistante sans statut `preuve a
  obtenir`.
- Un export copro masque ou retire les elements sensibles.
- Une commission sans mandat explicite ne voit pas le dossier.
- L'archive complete permet de verifier la presence d'un dossier restreint sans
  le lire.
- Une suppression locale d'une piece ou d'un evenement est detectee au verify.
- Deux coffres ne melangent jamais dossiers, preuves, exports ou cles.
