# Registre de langage UI

Date de reference: 2026-05-20

Ce registre fixe le langage de premier niveau pour CoproScope. Il sert aux ecrans, aux libelles accessibles, aux infobulles et aux tests statiques du lot L1 UX novice P0.

## Principe P0

Le premier niveau de lecture doit etre compris par une personne qui decouvre la copropriete et CoproScope. Sont consideres comme premier niveau:

- titres, navigation, boutons et liens;
- cartes de priorite, badges et compteurs;
- en-tetes de tableau et cellules d'action;
- `aria-label`, `title`, `alt`, `placeholder`;
- messages d'etat vide ou d'erreur.

Le jargon peut exister dans les details techniques, les chemins, les variables, les exports et les tests, mais il ne doit pas etre le seul mot visible pour expliquer une action.

## Grille de traduction obligatoire

| Concept | Dire en premier niveau | Definition novice | Terme technique accepte | Infobulle ou aide courte |
|---|---|---|---|---|
| Coffre | coffre de copro, coffre local, coffre chiffre | Espace local separe qui contient les donnees d'une copro. | vault | Un coffre est l'espace de donnees chiffre d'une copro. |
| Sync | synchronisation a verifier, sync externe, dossier de synchronisation | Copie technique entre dossiers ou appareils; elle ne publie rien toute seule. | sync provider, cloud sync | Cette page reste locale et ne lance pas de synchronisation externe. |
| Role | role, mandat, qui agit | Personne ou groupe au nom duquel l'action est faite. | RBAC, ACL, actor role | Le role indique qui peut voir ou faire cette action. |
| Preuve | preuve, source, justificatif | Element qui confirme une date, un montant, une decision ou une action. | proof, evidence | Toujours dire preuve de quoi et ou la retrouver. |
| Action | prochaine action, action attendue, relance | Ce qu'il faut faire ensuite, par qui et pourquoi. | task, action item | Une action doit etre concrete et verifiable. |
| Diffusion | partage controle, public destinataire | Ce qui peut etre envoye ou montre, et a qui. | visibility, export scope | Preciser le public avant tout export. |
| Restriction | restriction, acces limite, interne | Limite de lecture justifiee par une donnee sensible ou un mandat. | permission, policy | Dire qui ne voit pas et pourquoi. |
| Masquage | masquage, information cachee | Donnee sensible cachee avant partage. | biffage, redaction | Preferer masquage; garder biffage pour le pipeline ou les details. |
| Empreinte | empreinte technique | Code de verification qui signale si un fichier a change. | hash, sha256 | Ne pas confondre avec une signature manuscrite. |
| Signature | signature technique, coffre signe | Verification de l'auteur et de l'integrite d'un evenement. | cryptographic signature | Dire ce qui est verifie et ce qui reste a controler. |
| Priorite | a traiter maintenant, a verifier, conforme | Niveau d'attention lisible sans connaitre P1/P2. | P1, P2, OK | P1/P2 peut rester visible si une aide proche explique le sens. |
| Plugin | module local optionnel | Brique ajoutee localement pour produire un traitement. | plugin | Ne jamais laisser croire a une activation cloud automatique. |

## Registres de langue

| Registre | Public | Forme attendue | Exemple accepte |
|---|---|---|---|
| Novice | coproprietaire, nouveau membre CS | phrases courtes, action visible, pas d'acronyme seul | `Verifier la preuve avant diffusion` |
| Conseil syndical | benevole qui suit un dossier | vocabulaire copro avec preuve, periode, responsable et suite | `Rattacher la facture au point travaux` |
| Technique | mainteneur, export, journal | termes internes autorises, mais replies ou separes du premier niveau | `Details techniques: hash sha256, vault id` |

## Jargon primaire interdit sans traduction

Les mots suivants ne doivent pas apparaitre seuls dans le premier niveau: `vault`, `hash`, `ACL`, `RBAC`, `redaction`, `provider`, `event hash`, `DocOps`, `PrivacyOps`, `P1`, `P2`, `OK`.

Exceptions acceptees:

- variables Jinja, noms de champs Python, routes, chemins et commandes;
- exports techniques ou journaux internes;
- docs techniques comme `docs/vault_format.md`;
- badges courts si une aide proche donne le sens utilisateur;
- `sync` si la meme zone dit explicitement `synchronisation`, `local`, `cloud`, `a verifier` ou `ne synchronise rien`.

## Infobulles

Une infobulle ou aide courte doit:

- tenir en une phrase;
- etre utile mais non indispensable;
- etre accessible via `title`, texte adjacent, `details/summary`, ou contenu visible au clavier/tactile;
- expliquer le risque ou la consequence, pas seulement renommer le terme;
- eviter les acronymes non developpes.

Exemples attendus:

- `Coffre`: Un coffre est l'espace de donnees chiffre d'une copro.
- `Role`: Le role indique qui peut voir ou faire cette action.
- `Preuve`: Justificatif qui confirme le point suivi.
- `Sync`: Cette page reste locale et ne lance pas de synchronisation externe.
- `Action`: Suite concrete a faire avant de clore le sujet.

## Controle statique L1

Le test `server/tests/test_ui_novice_language_static.py` verifie:

- la presence de cette grille dans les docs;
- les traductions coffre, sync, role, preuve et action dans les templates existants;
- l'absence de `vault` dans le texte primaire des templates cibles;
- la presence d'aides proches pour les mots qui restent courts ou techniques.

Templates cibles du lot: `base.html`, `_context_banner.html`, `overview.html`, `governance.html`, `depot.html`, `actions.html`, `pieces.html`, `requests.html`, `agcontentieux.html`.

Templates hors perimetre de modification L1: `document_intake.html`. Les tests ne doivent pas exiger une modification de ce fichier.
