# Preparation AG UX

Date de reference: 2026-05-20

Ce document fusionne les plans existants autour d'AGOps, de l'UI
AG/contentieux/passation, du registre decisions-actions-preuves et du cockpit.
Il reste generique et ne contient aucune donnee Drive privee.

## Objectif produit

La preparation d'assemblee generale doit devenir un atelier de travail, pas un
simple dossier de fichiers. CoproScope doit aider le conseil syndical a passer
de documents et demandes disperses a un ordre du jour, des questions, des
preuves, des restrictions de diffusion et des actions post-AG suivies.

L'utilisateur doit comprendre:

- ce qui doit etre demande avant l'AG;
- quelles pieces de convocation ou justificatifs manquent;
- quelles questions sont pretes, a completer ou sensibles;
- quelles resolutions devront devenir actions suivies apres le PV;
- ce qui peut etre partage avec les coproprietaires.

## Parcours V1

1. Avant convocation: collecter demandes, points ouverts, contrats, comptes,
   travaux, incidents, suggestions et productions de commission.
2. Preparation ODJ: transformer les sujets en questions AG ou resolutions
   candidates, avec preuve attendue et responsable.
3. Reception convocation: pointer les pieces recues, manquantes ou a verifier.
4. Consultation justificatifs: rattacher factures, contrats, devis et questions
   syndic sans exposer de donnees individuelles inutiles.
5. Pendant AG: marquer les decisions attendues, les votes ou les points a
   confirmer, sans remplacer le PV officiel.
6. Apres AG: transformer chaque decision en action, preuve attendue, echeance,
   responsable et niveau de diffusion.

## Objets metier

- `DossierAG`: periode, date cible, statut, echeance, prochaines actions.
- `QuestionAG`: question ou resolution candidate, source, preuve, statut,
  diffusion, responsable.
- `PieceConvocation`: piece attendue, recue, verifiee ou manquante.
- `ConsultationJustificatif`: demande de consultation, preuve liee, relance et
  resultat.
- `ResolutionCandidate`: formulation candidate a valider humainement.
- `DecisionFollowUp`: action post-AG issue du PV, avec preuve de cloture.
- `AGExport`: version diffusable controlee, jamais source de verite.

Evenements futurs: `ag_folder_created`, `ag_question_created`,
`ag_evidence_linked`, `ag_export_created`, `ag_decision_followup_created`,
`ag_followup_closed`.

## UX attendue

Page `Atelier AG`:

- bandeau: AG cible, coffre actif, role courant, niveau d'acces et derniere
  verification;
- cartes `A faire maintenant`: piece manquante, question a relancer,
  resolution a valider, restriction a verifier;
- timeline: demande ODJ, convocation, annexes, questions, AG, PV, actions
  post-AG;
- tableau des questions avec preuve, statut, prochaine action, diffusion et
  rattachement;
- panneau `Pieces de convocation`;
- panneau `Sortie post-AG`: decisions, actions, preuves attendues;
- bouton d'export controle, soumis au masquage et aux droits.

Le premier niveau evite le jargon: `preuve verifiee` avant `hash`, `coffre de
copro` avant `vault`, `information masquee` avant `biffage`. Les details
techniques restent disponibles.

## Liens avec les autres lots

- Demandes multicanal: une demande peut devenir question AG ou relance syndic.
- Contentieux: un sujet litigieux peut rester hors diffusion copro et etre
  mentionne seulement par une trace restreinte.
- Comptes utilisateurs: les droits AG dependent du role dans le coffre, pas du
  compte local.
- Commissions: une commission produit une note ou question avec mandat, referent
  CS, preuves et diffusion.
- Anti-confiscation: l'historique AG, les decisions et les preuves doivent etre
  reconstructibles depuis l'archive autorisee.
- Multi-coffres: une AG appartient a un seul coffre; aucun document d'une autre
  copro ne peut etre rattache implicitement.
- Sync cloud et pair-a-pair: les dossiers AG voyagent comme evenements et blobs
  chiffres, pas comme exports ou caches dechiffres.
- Indicateurs: decisions sans preuve, questions en retard, pieces manquantes et
  actions post-AG alimentent le cockpit.
- Veille open source: les briques PDF/OCR/recherche peuvent aider la lecture des
  annexes, mais restent plugins ou outils evalues avant adoption.
- Suggestions: avant AG, les suggestions acceptees peuvent devenir questions ou
  resolutions candidates.

## Accessibilite et langage

Definitions courtes a afficher au moment utile:

- `ordre du jour`: liste officielle des sujets soumis a l'AG;
- `resolution`: decision proposee au vote;
- `justificatif`: piece permettant de verifier une charge ou une decision;
- `quorum`: condition de presence ou de voix selon le vote;
- `tantiemes`: parts utilisees pour repartir certaines charges ou voix.

Les aides doivent fonctionner au clavier et au tactile. Les tableaux ont une
caption, les actions ont des libelles concrets, les etats vides indiquent quoi
deposer ou rattacher.

## Garde-fous

- CoproScope ne remplace pas la convocation, le PV officiel ou le syndic.
- Une resolution candidate n'est pas une decision.
- Une analyse comptable ou contentieuse ne devient pas avis juridique.
- Aucun export AG ne contient de donnees individuelles sans controle de
  diffusion et masquage.
- Les sources restent dans le coffre; les exports sont derives et historises.

## Tests d'acceptation

- Une demande peut etre transformee en question AG avec preuve et prochaine
  action.
- Une piece de convocation manquante apparait dans `A faire maintenant`.
- Une resolution post-AG cree une action suivie sans masquer la decision source.
- Un export AG diffusable exclut les informations restreintes.
- Une production de commission affiche mandat, referent CS et preuves.
- Les indicateurs AG citent periode, source et prochaine action.
- Deux coffres ne melangent jamais AG, pieces, exports ou caches.
- Une archive permet de reconstruire les decisions et actions autorisees.
