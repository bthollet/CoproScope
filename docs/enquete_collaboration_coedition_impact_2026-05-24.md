# Etude UX - Collaboration et coedition de gouvernance

Date de reference : 2026-05-24

Statut : protocole d'etude rigoureux + synthese provisoire issue du corpus
interne CoproScope. Ce document ne pretend pas presenter des entretiens terrain
nouveaux. Il pose la methode pour les produire proprement, puis formule les
hypotheses produit a valider.

Rattachement: `RM-2026-0023` / `CH-2026-0024`
Conversation de reprise methodologique: `CONV-2026-1203`

## Synthese executive

La coedition a impact pour CoproScope n'est pas un clone de Google Docs. C'est
un atelier de gouvernance pour le conseil syndical et, selon les cas, pour un
syndic benevole.

Le coeur a etudier et a prototyper en premier est:

- preparation de resolutions, questions et annexes d'assemblee generale;
- preparation ou relecture de supports de convocation selon le role exact de
  l'utilisateur;
- avis du conseil syndical;
- comptes rendus de reunions du conseil syndical;
- signature ou validation a distance d'une version precise;
- lien entre chaque phrase engageante et les pieces qui la justifient.

Le principe produit retenu est donc:

> Un document coedite dans CoproScope doit montrer qui propose, qui relit, qui
> signe, quelles preuves soutiennent le texte, quelle version est partageable,
> et ce qui reste seulement interne.

Les commentaires et les actions restent utiles, mais ils ne sont pas le centre
de l'etude. Ils sont des mecanismes de support autour des documents de
gouvernance.

## Sources internes utilisees

Cette reprise s'appuie sur le corpus local suivant:

| Source | Usage dans cette etude |
|---|---|
| `docs/etude_utilisateurs.md` | Modele initial: preuve, action, memoire, conseil syndical novice. |
| `docs/audit_adequation_ux_ui_enquete_2026-05-22.md` | Gates novice et alignement produit. |
| `docs/ux_ecarts_enquete_vs_produit_2026-05-20.md` | Ecarts entre concepts d'enquete et produit. |
| `docs/etude_utilisateurs_syndics_benevoles.md` | Cas ou l'utilisateur porte aussi des fonctions de syndic. |
| `docs/roadmap_backlog_central.md` | Rattachement produit et priorites actives. |
| `docs/presence_agents.md` | Trace des lots et collisions recentes. |

Limite importante: ces sources ne remplacent pas une enquete terrain. Elles
servent a construire une methode, des hypotheses et un protocole de validation.

## Questions de recherche

L'etude doit repondre a huit questions.

| ID | Question | Decision produit visee |
|---|---|---|
| `RQ1` | Quels documents de gouvernance sont vraiment coedites par les CS ? | Choisir les premiers types de documents. |
| `RQ2` | Qui a autorite pour proposer, relire, signer, envoyer ou archiver ? | Definir les roles et les garde-fous. |
| `RQ3` | Quelles preuves doivent etre rattachees a chaque resolution, avis ou CR ? | Concevoir le lien document -> preuve. |
| `RQ4` | Comment les versions, corrections et conflits sont geres aujourd'hui ? | Choisir entre verrouillage, suggestions, versions ou sections. |
| `RQ5` | Quelle valeur les utilisateurs attendent d'une signature a distance ? | Distinguer validation interne, signature simple et signature juridiquement forte. |
| `RQ6` | Qu'est-ce qui peut etre partage hors du coffre, et avec qui ? | Concevoir la revue de diffusion. |
| `RQ7` | Quels risques de confusion juridique ou metier sont les plus dangereux ? | Fixer les libelles et no-go. |
| `RQ8` | Quel premier lot donne un gain net sans alourdir des benevoles ? | Prioriser le MVP. |

## Hypotheses a valider

| ID | Hypothese | Indice qui la confirme | Indice qui la refute |
|---|---|---|---|
| `H1` | Les resolutions et questions d'AG sont le premier cas de coedition utile. | Plusieurs participants racontent des allers-retours de texte, pieces et corrections avant AG. | Les CS ne preparent presque jamais ces textes eux-memes. |
| `H2` | Les avis CS ont plus de valeur si chaque position pointe vers une preuve. | Les participants demandent "sur quoi se base-t-on ?" ou "quelle piece joindre ?". | Ils veulent seulement un traitement de texte partage. |
| `H3` | Le compte rendu CS signe est un objet de memoire plus actionnable qu'un simple commentaire. | Les participants perdent decisions internes, presents, actions ou reserves. | Les reunions CS sont deja parfaitement tracees ailleurs. |
| `H4` | La signature a distance attendue est d'abord une validation interne tracee. | Les participants veulent savoir qui a valide quelle version, meme sans signature qualifiee. | Ils exigent une signature electronique qualifiee des le depart. |
| `H5` | La confusion entre projet CS, demande au syndic et convocation officielle est un risque majeur. | Les participants citent des cas ou un document a ete pris pour plus officiel qu'il ne l'etait. | Tous les roles et statuts sont deja compris sans aide. |
| `H6` | Les commentaires doivent etre rattaches a une section ou une preuve, pas au document global seulement. | Les retours portent sur des phrases, montants, pieces ou resolutions precises. | Les participants raisonnent surtout en discussion generale. |
| `H7` | Le premier lot doit etre asynchrone, pas de la coedition temps reel. | Les participants travaillent par mails, relectures decalees et signatures a distance. | Ils ont besoin d'ecrire simultanement a plusieurs en reunion. |
| `H8` | La revue de diffusion est un passage obligatoire avant export. | Les participants craignent de partager des pieces internes ou des donnees personnelles. | Les documents vises sont toujours publics ou deja diffuses. |

## Perimetre de l'etude

### Inclus

- Projets de resolutions et questions a inscrire a l'ordre du jour.
- Supports de convocation ou dossier de convocation selon le role.
- Avis du conseil syndical.
- Comptes rendus de reunions du conseil syndical.
- Validation et signature a distance de versions.
- Revue de diffusion et export partageable.
- Rattachement des preuves et pieces sources.

### Exclus au premier cycle

- Chat general de copropriete.
- Portail large pour tous les coproprietaires.
- Signature electronique qualifiee integree a un prestataire externe.
- Coedition temps reel type traitement de texte complet.
- Envoi automatique juridiquement engageant.
- Remplacement du syndic, du droit ou d'une validation humaine.

## Echantillonnage

Objectif: couvrir les situations qui changent vraiment la conception produit,
pas obtenir une representativite statistique.

| Segment | Cible | Pourquoi |
|---|---:|---|
| President ou secretaire de CS actif | 3 a 4 | Porte souvent avis, CR, relances et preparation AG. |
| Membre CS novice ou intermittent | 3 a 4 | Teste la comprehension, la charge et les libelles. |
| Syndic benevole ou copro en autogestion | 2 a 3 | Cas critique convocation, signatures et responsabilite. |
| Coproprietaire contributeur non CS | 2 a 3 | Acces limite, contribution sans coffre complet. |
| Expert externe ponctuel | 1 a 2 | Relecture bornee, avis technique/comptable/juridique. |
| Nouveau membre reprenant un dossier | 2 | Passation, lisibilite des validations et historique. |

Taille recommandee: 13 a 18 entretiens semi-directifs. Arret possible si deux
entretiens consecutifs n'apportent plus de nouveau risque majeur sur les
parcours P0.

## Materiaux a collecter

Tous les exemples doivent etre anonymises ou fictifs avant d'entrer dans le
depot produit.

| Materiau | But | Garde-fou |
|---|---|---|
| Exemple de resolution preparee | Comprendre structure, corrections et preuves. | Supprimer noms, lots, montants sensibles si non necessaires. |
| Exemple d'avis CS | Comprendre validation collective et diffusion. | Remplacer personnes par roles. |
| Exemple de compte rendu CS | Comprendre presents, decisions, actions et signatures. | Ne pas importer de CR brut dans Git. |
| Exemple de convocation ou demande d'ordre du jour | Comprendre frontiere projet/officiel. | Utiliser derive anonymise ou modele fictif. |
| Capture de circuit actuel | Voir outils utilises et ruptures. | Flouter emails, chemins, telephones, signatures. |
| Liste de documents partages par erreur ou a risque | Identifier no-go diffusion. | Formuler en categories, pas en pieces reelles. |

## Protocole d'entretien

Format: 60 minutes, semi-directif, en visioconference ou en presence. La
personne peut montrer son processus, mais aucune piece brute ne doit etre
conservee sans anonymisation explicite.

### Deroule

| Temps | Activite | Objectif |
|---:|---|---|
| 5 min | Contexte, role, copropriete type, limites de confidentialite. | Situer la reponse sans collecter de donnees inutiles. |
| 10 min | Dernier document prepare a plusieurs. | Repartir d'un fait, pas d'une opinion generale. |
| 10 min | Preparation AG ou resolution. | Comprendre sources, corrections, relecteurs, envoi. |
| 10 min | Avis CS ou compte rendu CS. | Comprendre validation, signatures, statut interne/externe. |
| 10 min | Signature ou validation a distance. | Comprendre preuve attendue et niveau d'engagement. |
| 10 min | Revue de diffusion et droits. | Comprendre ce qui peut sortir, a qui, sous quelle forme. |
| 5 min | Classement des besoins. | Prioriser l'impact percu. |

### Questions principales

1. Racontez le dernier document que vous avez prepare a plusieurs pour la copropriete.
2. Qui a propose le texte initial ?
3. Qui avait le droit de modifier, relire, valider ou signer ?
4. Quelles pieces ont servi a justifier le texte ?
5. Ou les corrections se sont-elles faites: mail, Word, PDF, Drive, reunion, autre ?
6. Qu'est-ce qui a ete le plus fragile: version, preuve, responsabilite, delai, diffusion ?
7. Comment savez-vous qu'une version est la bonne ?
8. Comment savez-vous qu'un avis ou un compte rendu est valide par le CS ?
9. Qu'attendez-vous d'une signature a distance ?
10. Qu'est-ce qui ne doit jamais etre partage avec tous les coproprietaires ?
11. Dans quel cas un projet de convocation pourrait etre confondu avec une convocation officielle ?
12. Quel premier outil vous ferait gagner du temps sans ajouter de charge ?

## Test de concept

Apres les entretiens, tester un prototype basse fidelite avec 6 a 8 personnes.

### Scenarios

| Scenario | Tache utilisateur | Reussite attendue |
|---|---|---|
| `S1` Resolution AG | Creer une resolution, rattacher deux pieces, demander relecture. | L'utilisateur comprend le statut `Projet CS` et la preuve liee. |
| `S2` Convocation | Relire un support de convocation et identifier ce qui est officiel ou non. | L'utilisateur ne confond pas projet, demande au syndic et convocation emise. |
| `S3` Avis CS | Coediter un avis, resoudre un commentaire, demander signature. | L'utilisateur sait qui doit signer et quelle version sortira. |
| `S4` CR CS | Rediger un compte rendu, noter presents, decisions et actions. | L'utilisateur distingue CR CS et PV d'AG. |
| `S5` Signature | Signer a distance une version. | L'utilisateur voit version, date, role, empreinte et consequence. |
| `S6` Diffusion | Exporter une version partageable. | L'utilisateur voit ce qui sort et ce qui reste prive. |

### Mesures

| Mesure | Seuil GO |
|---|---|
| Comprehension du statut du document | 6/8 participants expliquent correctement projet, valide, signe, diffuse. |
| Confusion juridique critique | 0 cas de confusion projet CS / convocation officielle / PV d'AG dans le test. |
| Rattachement preuve | 6/8 participants trouvent la preuve source sans aide. |
| Signature a distance | 6/8 participants comprennent quelle version ils signent. |
| Revue de diffusion | 6/8 participants identifient au moins un element prive non exporte. |
| Charge percue | Majorite juge le flux plus clair que mail + pieces jointes. |

## Methode d'analyse

L'analyse ne doit pas seulement produire une liste d'idees. Elle doit conduire a
des decisions produit.

| Etape | Methode | Sortie |
|---|---|---|
| Transcription selective | Notes structurees par episode reel. | Fiches anonymisees par participant. |
| Codage thematique | Codes: version, preuve, role, signature, diffusion, conflit, temps, confiance. | Matrice de frequences et verbatims courts anonymises. |
| Cartographie de parcours | Avant / pendant / apres document. | Cycle de vie des documents de gouvernance. |
| Analyse des roles | RACI simplifie: propose, modifie, relit, signe, envoie, archive. | Matrice de droits utilisateur. |
| Analyse des risques | Confusion, fuite, signature, version, usurpation, surcharge. | No-go et garde-fous. |
| Priorisation | Impact utilisateur x frequence x risque reduit x faisabilite. | P0/P1/P2 argumentes. |

## Grille de codage

| Code | Definition | Exemple de signal |
|---|---|---|
| `VERSION_PERDUE` | On ne sait plus quelle version est valide. | Plusieurs fichiers suffixes `final`, `final2`, `corrige`. |
| `PREUVE_DECONNECTEE` | Le texte cite un fait sans piece rattachee. | "On sait que", sans document source. |
| `ROLE_FLOU` | On ne sait pas qui peut signer ou envoyer. | Confusion CS, syndic, coproprietaire demandeur. |
| `OFFICIALITE_FLOUE` | Projet pris pour document officiel. | Projet de convocation lu comme convocation emise. |
| `SIGNATURE_FAIBLE` | Validation a distance peu prouvable. | Accord par SMS, mail ou image de signature non rattachee. |
| `DIFFUSION_RISQUEE` | Donnees internes ou personnelles exposables. | Piece jointe brute envoyee a trop de monde. |
| `ACTION_NON_SUIVIE` | Decision ou avis sans responsable ni echeance. | "A faire" sans suite. |
| `CHARGE_BENEVOLE` | Flux trop lourd pour un CS non expert. | Trop de champs, trop de statuts, jargon. |

## Synthese provisoire issue du corpus

Ce qui est deja assez solide dans le corpus existant:

1. Le produit doit rester centre sur **preuve + action + memoire**.
2. La preparation AG est un moment fort, deja present dans les parcours
   critiques.
3. Les exports et documents diffusables doivent passer par une revue de
   confidentialite.
4. Les roles doivent etre comprehensibles par un membre de CS novice.
5. Les documents de gouvernance ne doivent pas se confondre avec des pieces
   brutes ou des discussions informelles.

Ce qui reste a valider par terrain:

1. Le poids relatif entre resolutions AG, avis CS et comptes rendus CS.
2. Le niveau de signature attendu: validation interne, signature simple ou
   besoin de signature electronique forte.
3. Le degre de coedition necessaire: commentaires asynchrones, suggestions, ou
   edition simultanee.
4. La premiere tranche qui produit un gain net sans alourdir les benevoles.
5. Les libelles exacts qui evitent les confusions juridiques.

## Implications produit provisoires

### P0 recommande

| Fonction | Contenu minimal | No-go |
|---|---|---|
| Atelier AG | Resolution/question, pieces sources, statut, relecteurs, version partageable. | Afficher une demande comme convocation officielle. |
| Avis CS | Brouillon, sections sourcees, relecteurs, signatures, export derive. | Avis non source ou partage sans revue. |
| Compte rendu CS | Presents, ordre du jour, decisions, actions, signatures. | Confusion avec PV d'AG. |
| Signature a distance | Signataire, role, date, version, empreinte, intention de validation. | Faire croire a une signature qualifiee si ce n'est pas le cas. |
| Revue de diffusion | Ce qui sort, ce qui reste prive, statut et signataires. | Export de pieces brutes sensibles. |

### P1

- Suggestions et corrections par section.
- Mentions et notifications limitees au document ou a la resolution.
- Paquet de revue externe borne.
- Tableau des contributions et blocages.
- Conversion d'une decision de CR ou d'avis en action suivie.

### P2

- Coedition temps reel.
- Portail coproprietaires large.
- Integration a un prestataire de signature electronique forte.
- Workflows d'approbation avances.

## Cycle de vie cible des documents

| Etat | Sens utilisateur | Sortie possible |
|---|---|---|
| `Brouillon interne` | Le CS travaille, rien n'est valide. | Aucune sortie publique par defaut. |
| `En relecture` | Des membres ou relecteurs doivent commenter. | Export de travail marque comme tel. |
| `Pret a signer` | Le texte est stable, attente signatures. | Pas encore diffuse. |
| `Signe / valide` | Une version precise a ete validee. | Version diffusable apres revue. |
| `Envoye hors CoproScope` | L'utilisateur confirme un envoi externe. | Trace du canal et de la date. |
| `Archive / memoire` | Le document sert a la passation. | Lecture et export historique. |

## Garde-fous

- Ne jamais promettre qu'une validation interne vaut signature electronique
  qualifiee.
- Ne jamais afficher `convocation officielle` si le role ne le permet pas.
- Ne jamais confondre compte rendu CS et proces-verbal d'AG.
- Toujours afficher la version signee.
- Toujours afficher qui signe et en quelle qualite.
- Toujours rattacher les documents de gouvernance aux pieces sources.
- Toujours separer version de travail, version signee et version diffusee.
- Toujours passer par une revue anti-fuite avant export.

## Livrables de l'etude terrain

L'etude ne sera complete qu'avec:

- 13 a 18 fiches d'entretien anonymisees;
- une matrice de codage;
- une cartographie de cycle de vie des documents;
- une matrice des roles;
- une matrice des risques;
- un rapport de synthese;
- une recommandation P0/P1/P2 mise a jour;
- une commande dev testable seulement apres validation des hypotheses P0.

## Decision actuelle

Decision documentaire provisoire: il faut arreter de parler de "collaboration"
au sens large. Le bon objet produit est:

**Atelier de gouvernance CS/AG avec coedition, preuves, signatures et diffusion
controlee.**

La commande dev ne doit pas partir d'un module de commentaires generique. Elle
doit partir d'un document de gouvernance concret, probablement l'un de ces deux
premiers fils:

1. atelier AG: resolution/question + pieces sources + relecture + statut;
2. compte rendu CS: presents + decisions + actions + signatures.

Le choix entre ces deux fils doit etre decide apres les premiers entretiens ou,
si Brice tranche produit, par une commande dev bornee et testable.

## Trace de reprise

BOT-END - Reprise methodologique UX collaboration - 2026-05-24 02:00 +02:00

Roadmap: `RM-2026-0023`
Chantier: `CH-2026-0024`
Conversation: `CONV-2026-1203`
Statut: `INTEGRE`
Fichiers modifies: `docs/enquete_collaboration_coedition_impact_2026-05-24.md`,
`docs/roadmap_backlog_central.md`, `docs/presence_agents.md`.
Fichiers volontairement evites: code applicatif, templates, tests, instances
privees et passerelles UX/DB.
Tests/preuves: relecture documentaire, verification ASCII et `git diff --check`.
Limites: protocole et synthese provisoire; pas encore d'entretiens terrain.
Prochain mouvement propose: lancer 6 premiers entretiens exploratoires ou
choisir directement le fil MVP entre atelier AG et compte rendu CS.
