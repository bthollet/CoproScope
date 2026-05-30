# Revue correspondances coproprietaires vers conseil syndical

Date: 2026-05-27
Roadmap: `RM-2026-0042`
Chantier: `CH-20260527-233542-RM-2026-0042-correspondances-copro-cs`
Conversation: `CONV-2026-1809`
Statut: memoire integree, sans dev

## BOT-START - Coordinateur memoire produit - 2026-05-27 23:35 +02:00

Roadmap: `RM-2026-0042`
Chantier: `CH-20260527-233542-RM-2026-0042-correspondances-copro-cs`
Conversation: `CONV-2026-1809`
Role: coordinateur memoire produit, coproprietaires -> conseil syndical.
Mission: conserver la revue forums et sciences humaines et sociales sur les
correspondances adressees au conseil syndical.
Ownership modifiable: ce fichier, `docs/roadmap_backlog_central.md`,
`docs/presence_agents.md`.
Fichiers a eviter: code applicatif, routes, templates, CSS, tests, vault DB,
Drive, instances privees, documents bruts, OCR/logs, exports bruts, secrets,
serveurs, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Passerelle/registre de trace: gouvernail et presence.
Dernier point lu: presence/gouvernail a 2026-05-27 23:35 +02:00; `CONV-2026-1808`
reste actif sur DB/vault.
Tests/preuves attendus: `git diff --check` documentaire.
Risque de collision: faible mais present sur les docs de coordination; aucun
dev ouvert et aucune reprise des fichiers DB/vault.
Lease ownership: cloture immediate.
Prochaine action: ajouter la memoire comme suite future de `Messages entrants`
et `SyndicOps`, sans ouvrir de dev maintenant.

## Synthese

Les coproprietaires ecrivent au conseil syndical quand un fait vecu doit devenir
un sujet collectif: probleme materiel, trouble de voisinage, doute comptable,
travaux contestes, demande de piece, demande d'ordre du jour, alerte sur le
syndic, ou conflit de gouvernance.

Le conseil syndical n'est ni le syndic ni le juge. Son role produit cible doit
donc etre: qualifier, demander preuve, relayer, suivre, moderer, restreindre la
diffusion et preparer une action humaine. Il ne doit pas promettre d'envoyer,
trancher juridiquement, voter, publier ou sanctionner seul.

## Sources retenues

- Cadre officiel conseil syndical: Service-Public, `F2610`.
  https://www.service-public.gouv.fr/particuliers/vosdroits/F2610
- Cadre assemblee generale et ordre du jour: Service-Public, `F2615`.
  https://www.service-public.gouv.fr/particuliers/vosdroits/F2615
- Mission de controle et assistance du conseil syndical: loi de 1965, article
  21, via Legifrance.
  https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000039313574/
- Sciences humaines et sociales: travaux de Marie-Pierre Lefeuvre sur confiance,
  risques et copropriete.
  https://shs.cairn.info/revue-cahiers-internationaux-de-sociologie-2003-1-page-73
- Panorama SHS sur les coproprietes.
  https://portail.documentation.developpement-durable.gouv.fr/pub/PCAOUV00261130-coproprietes-panorama-des-recherches-sciences-soci.html
- Signaux forums non exhaustifs: Reddit `r/conseiljuridique`, Legavox et forums
  copropriete consultes comme indices d'usage, pas comme sources juridiques.

## Typologie metier cible

| Type de correspondance | Fait declare | Preuve attendue | Action CS cible |
|---|---|---|---|
| `signalement_materiel` | Fuite, panne, porte, eclairage, menage, securite | Photo, date, lieu, relance precedente, contrat concerne | Constater, relayer au syndic, suivre intervention |
| `trouble_voisinage` | Bruit, odeur, encombrants, stationnement, usage parties communes | Chronologie neutre, reglement, temoins prudents | Mediation, rappel regle, escalade prudente |
| `demande_piece` | Facture, contrat, PV, devis, releve, appel de fonds demande | Objet precis, periode, finalite | Demander au syndic ou orienter vers consultation |
| `contestation_charge` | Montant, cle, erreur, hausse, ligne incomprise | Appel, annexe, ligne comptable, comparaison | Qualifier, rattacher comptes, demander explication |
| `alerte_travaux` | Devis conteste, urgence, cout, mise en concurrence | Devis, vote, contrat, photo, jalon travaux | Rattacher WorksOps, demander pieces, preparer question |
| `projet_resolution_ag` | Demande d'ordre du jour ou resolution | Texte propose, justificatif, delai, destinataire syndic | Verifier forme, signaler que l'envoi officiel reste au syndic |
| `sinistre_assurance` | Degat, infiltration, responsabilite, declaration | Photos, dates, declarations, expertises, assurance | Qualifier urgence, restreindre, suivre preuve de cloture |
| `mise_en_cause_syndic` | Absence de reponse, soupcon, frais, retard | Courriers, relances, piece de gestion | Controler, demander explication, garder reserve |
| `mise_en_cause_cs` | Favoritisme, abus, silence, confusion de mandat | Message, decision contestee, contexte | Clarifier role CS, prevenir diffusion conflictuelle |
| `message_hors_mandat` | Sujet prive ou demande non traitable par CS | Raison du hors mandat | Repondre prudemment, classer, orienter |

## Lecture forums

Les forums montrent moins des "tickets" propres que des demandes melees:
technique, confiance, reconnaissance et preuve. Les motifs recurrents sont:

- le syndic ne repond pas ou filtre une demande;
- une resolution AG serait modifiee, refusee ou mal formulee;
- un devis ou chantier parait trop cher ou insuffisamment mis en concurrence;
- un coproprietaire veut comprendre une charge ou obtenir une piece;
- un trouble de voisinage devient collectif faute de solution directe;
- le conseil syndical est soupconne de couvrir le syndic ou de decider seul;
- une information personnelle ou conflictuelle ne doit pas etre diffusee trop
  largement.

Consequence produit: un message entrant ne doit pas etre range seulement par
canal. Il doit porter un fait, une preuve, une action attendue, un degre de
diffusion et une limite de mandat.

## Lecture sciences humaines et sociales

Les travaux SHS sur la copropriete insistent sur la confiance fragile, la
delegation imparfaite et le "travail pour l'immeuble" supporte par quelques
acteurs. Quand la confiance baisse, les coproprietaires demandent plus de
traces, plus de pieces, plus d'explications et plus de reconnaissance du risque.

Pour CoproScope, cela donne trois regles:

- ne pas traiter la correspondance comme un simple formulaire technique;
- rendre visible le passage de la plainte individuelle au sujet collectif;
- separer ce qui est constate, suppose, a verifier, a relayer, et hors mandat.

## Contrat produit futur

Un message coproprietaire vers CS devrait avoir au minimum:

- `message_id`, date, canal, auteur pseudonyme ou role;
- type metier cible parmi la typologie ci-dessus;
- fait declare en une phrase neutre;
- piece jointe candidate ou preuve attendue;
- destinataire reel: CS, syndic, AG, commission, prestataire, aucun;
- action attendue: classer, demander piece, relayer, preparer resolution,
  rattacher a action, rattacher a travaux, rattacher a compta, repondre hors
  CoproScope;
- diffusion: CS seulement, coproprietaires apres verification, restreint,
  bloque, a arbitrer;
- statut: nouveau, a qualifier, preuve demandee, relaye hors CoproScope,
  en attente, clos, hors mandat;
- trace de validation humaine.

## Backlog derive

| Priorite | Item | Action |
|---|---|---|
| P1 | Typologie correspondances CS | Ajouter les types ci-dessus a `Messages entrants` et `SyndicOps` quand le lot sera repris. |
| P1 | Privacy gate message entrant | Exiger motif de diffusion et restriction avant partage hors CS. |
| P1 | Rattachements metier | Relier un message a travaux, compta, incident, demande syndic, ordre du jour ou piece. |
| P2 | UX novice | Libelles simples: "A verifier", "A relayer au syndic", "A mettre a l'ordre du jour", "Hors mandat du CS". |
| P2 | Corpus fictif | Creer messages synthetiques couvrant trouble, charge, travaux, resolution AG, sinistre et mise en cause. |

## BOT-END - Coordinateur memoire produit - 2026-05-27 23:35 +02:00

Roadmap: `RM-2026-0042`
Chantier: `CH-20260527-233542-RM-2026-0042-correspondances-copro-cs`
Conversation: `CONV-2026-1809`
Statut: `INTEGRE`
Fichiers modifies: ce fichier, `docs/roadmap_backlog_central.md`,
`docs/presence_agents.md`.
Fichiers volontairement evites: code, tests applicatifs, routes, templates, CSS,
vault DB, Drive, instances privees, documents bruts, OCR/logs, exports bruts,
secrets, serveurs, scans/kills, push GitHub, `RM-2026-0017`, `ORD-P0-990`.
Tests/preuves: `git diff --check` documentaire attendu.
Limites: revue exploratoire, forums utilises comme signaux d'usage et non comme
sources normatives.
Questions ouvertes: priorisation future entre `Messages entrants`, `SyndicOps`
et `DecisionOps`.
Prochain mouvement propose: ouvrir un owner dedie seulement quand les lots actifs
DB/DocOps/Drive le permettent.
