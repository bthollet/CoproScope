# Recherche UX/UI - ajout docs relance

Date de relance: 2026-05-24 09:16 +02:00.
Mode: equipe UX/UI recherche visuelle sans dev.
Source principale: `docs/recherche_ux_ui_2026-05-24_ajout-docs.md`.

## BOT-START

```text
BOT-START - Orchestrateur UX/UI - 2026-05-24 09:16 +02:00
Roadmap: RM-2026-0003 principal; liens RM-2026-0006, RM-2026-0010, RM-2026-0029.
Chantier: CH-20260524-091656-RM-2026-0003-ajout-docs-relance-ux-ui
Conversation: CONV-2026-1355
Role: Orchestrateur UX/UI
Mission: relancer une iteration UX/UI sans dev sur les questions ouvertes du parcours ajout docs.
Ownership modifiable: docs/recherche_ux_ui_2026-05-24_ajout-docs_relance.md; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance/; docs/presence_agents.md.
Fichiers a eviter: code applicatif, tests, instances privees, secrets, exports bruts, passerelles hors mission, chantier reconstruction bloque RM-2026-0017.
Passerelle/registre de trace: ce document et docs/presence_agents.md.
Dernier point lu: AGENTS.md, docs/orchestration_agents.md, docs/protocole_equipe_ux_ui_recherche.md, docs/presence_agents.md, docs/recherche_ux_ui_2026-05-24_ajout-docs.md.
Tests/preuves attendus: synthese multi-roles, decision matrix confidentialite, microcopy novice, retours metier et novice, mention explicite qu'aucun code n'a ete produit.
Risque de collision: depot deja charge par d'autres travaux; rester en documentation uniquement.
Lease ownership: jusqu'au 2026-05-25 09:16 +02:00.
Prochaine action: relancer les roles UX/UI en lecture seule.
```

## Objectif de relance

La premiere recherche a tranche la direction generale: atelier guide, une piece active a la fois, avec tri DocOps par lot en variante separee.

Cette relance doit trancher les zones encore ouvertes:

- regle de decision entre diffusable, a masquer, reserve CS, non diffusable et a decider;
- obligation de justification pour `A masquer`;
- niveau d'indice neutre acceptable sans exposer le contenu sensible;
- cas d'un PDF partiellement diffusable;
- microcopy novice et ordre des decisions dans les 5 premieres minutes;
- frontiere entre parcours ponctuel et tri de lot.

## Sources a reprendre

- `docs/recherche_ux_ui_2026-05-24_ajout-docs.md`
- `docs/assets/ux-ui-recherche-2026-05-24-ajout-docs/01-atelier-qualification-novice.svg`
- `docs/assets/ux-ui-recherche-2026-05-24-ajout-docs/02-tri-docops-lot-rejete-instructif.svg`
- `docs/ux_workflow_ajout_document.md`
- `docs/commandes/commande_interface_tri_docops_feedback_2026-05-24.md`

## Roles relances

| Conversation | Role | Mission | Statut |
|---|---|---|---|
| `CONV-2026-1355` | Orchestrateur UX/UI | Cadre, trace, arbitre et consolide. | En cours |
| `CONV-2026-1356` | Chercheur utilisateur | Prioriser les questions ouvertes selon usage novice et lot. | En cours |
| `CONV-2026-1357` | Architecte UX | Formaliser decision matrix, etats et micro-parcours. | En cours |
| `CONV-2026-1358` | Designer UI / generateur visuel | Proposer blueprint de decision matrix et recapitulatif final. | En cours |
| `CONV-2026-1359` | Testeur metier expert | Verrouiller regles de confidentialite, motifs et PDF partiel. | En cours |
| `CONV-2026-1360` | Testeur accessibilite / novice | Verifier microcopy, charge cognitive et comprehension 0-5 minutes. | En cours |

## Decisions consolidees

- La relance confirme l'atelier guide: une piece active a la fois.
- Le premier ecran doit rester minimal: `Ajouter depuis mon ordinateur` et `Le fichier reste local. Rien n'est partage.`
- La confidentialite devient une etape centrale avec une matrice dediee, pas un simple selecteur technique.
- Le motif est obligatoire pour `A masquer avant partage`, `Reserve conseil syndical` et `Non diffusable`.
- Un PDF mixte ne peut jamais etre considere diffusable en brut. Il bascule vers `A masquer`, `Reserve CS`, `Non diffusable` ou `A decider`.
- La vue de lot reste separee: proposee apres depot multiple, file DocOps ou environ dix documents; jamais comme premier ecran apres un ajout simple.

## Regle de decision confidentialite

| Decision UI | Quand l'utiliser | Motif requis | Effet |
|---|---|---|---|
| `Diffusable sans masquage apres verification` | Document communicable, sans signal sensible detecte ou connu. | Recommande; obligatoire si diffusion large ou signal PrivacyOps. | Peut etre rattache et cite dans un espace autorise, sans valoir validation juridique. |
| `A masquer avant partage` | Document utile avec donnees personnelles, RIB, impayes, pages mixtes ou element a retirer. | Oui. | Cree une prochaine action: preparer ou verifier une version masquee. Le brut reste local. |
| `Reserve conseil syndical` | Document utile au CS mais non diffusable largement a ce stade: negociation, contentieux, strategie, situation nominative. | Oui. | Visible seulement en contexte CS; interdit comme categorie de confort. |
| `Non diffusable - motif obligatoire` | Brut trop sensible, interdit, doute fort, cible cloud brute ou masquage insuffisant. | Oui. | Bloque toute sortie/export; reference locale seulement. |
| `A decider plus tard` | Incertitude, OCR faible, scan incomplet ou PDF mixte non arbitre. | Non au depart. | Sauvegarde l'etat local sans diffusion. |

Le motif doit etre une categorie metier courte, sans recopier de contenu sensible: `donnees personnelles`, `RIB`, `impayes nominatifs`, `contentieux en cours`, `donnees salarie`, `negociation prestataire`, `pages mixtes`, `autre`.

## Microcopy retenue

### Premier niveau

- `Ajouter depuis mon ordinateur`
- `Le fichier reste local. Rien n'est partage.`
- `Fichier ajoute localement`
- `Quel type de document est-ce ?`
- `Je ne sais pas encore`
- `Qui pourra voir ce document ?`
- `A quel sujet ce document sert-il ?`
- `Que doit-il aider a verifier ?`
- `Enregistrer localement`

### Confidentialite

- `Visible tel quel apres verification`
- `A masquer avant partage`
- `Reserve au conseil syndical`
- `Non diffusable - motif obligatoire`
- `A decider plus tard`
- `Pourquoi ce document ne peut-il pas etre visible tel quel ?`
- `Rien n'est partage maintenant`

### A masquer au premier niveau

- `DocOps local`
- `DIFFUSABLE_BRUT`
- `A_CLASSER`
- `A_ARBITRER`
- `Point concerne`
- `Preuve attendue`
- `Pret`
- `Pret a partager`
- hash complet, OCR, score DocOps, logs, chemins locaux, nom de fichier brut, checklist runtime.

## Micro-parcours 0-5 minutes

| Minute | Focus | Message | Action |
|---|---|---|---|
| 0 | Etat vide | `Ajouter depuis mon ordinateur`; `Le fichier reste local.` | Choisir un fichier. |
| 1 | Depot | `Ajout local en cours. Rien n'est partage.` | Attendre. |
| 2 | Confirmation | `Fichier ajoute localement`; reference neutre. | Continuer. |
| 3 | Type | `Quel type de document est-ce ?` | Choisir ou `Je ne sais pas encore`. |
| 4 | Confidentialite | `Qui pourra voir ce document ?` | Choisir un statut humain. |
| 5 | Rattachement leger | `A quel sujet ce document sert-il ?` | Choisir sujet/action ou enregistrer a completer. |

## Image retenue

- Chemin: `docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance/01-matrice-confidentialite-recapitulatif.svg`
- Statut: `retenue`
- Intention: completer l'atelier novice par une matrice de confidentialite accessible et un recapitulatif final.
- Retour metier: GO conditionnel si les motifs obligatoires et le traitement des PDF mixtes sont respectes.
- Retour novice/accessibilite: GO conditionnel si l'ecran arrive au bon moment, apres depot et type, avec une seule prochaine action dominante.

## Retours metier et novice

### Metier

GO conditionnel. NO-GO si l'interface permet encore de marquer un PDF mixte comme diffusable brut, de reserver au CS sans motif, ou de presenter OCR/classification/hash comme validation juridique.

### Novice/accessibilite

GO conditionnel. NO-GO si le blueprint initial est repris avec trop d'informations visibles des le depart. Le focus apres depot doit aller sur la confirmation puis la premiere decision, pas sur les compteurs.

## Questions restantes

- Quels types documentaires afficher dans la liste courte initiale ?
- Qui arbitre la frontiere entre `Reserve conseil syndical` et droit d'acces coproprietaire ?
- Quel niveau d'extrait masque devient acceptable apres premier arbitrage confidentialite ?
- Faut-il materialiser les pages sensibles avant le futur outil d'annotation PDF ?
- Le seuil lot doit-il etre fixe a 10 documents ou rester declenche par choix utilisateur ?

## BOT-END

```text
BOT-END - Orchestrateur UX/UI - 2026-05-24 09:30 +02:00
Roadmap: RM-2026-0003 principal; liens RM-2026-0006, RM-2026-0010, RM-2026-0029.
Chantier: CH-20260524-091656-RM-2026-0003-ajout-docs-relance-ux-ui
Conversation: CONV-2026-1355
Statut: CLOTURE
Fichiers modifies: docs/recherche_ux_ui_2026-05-24_ajout-docs_relance.md; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance/.gitkeep; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance/01-matrice-confidentialite-recapitulatif.svg; docs/presence_agents.md.
Fichiers volontairement evites: code applicatif, tests, instances privees, secrets, exports bruts, passerelles hors mission, RM-2026-0017 bloque.
Tests/preuves: syntheses Boole, Ampere, Galileo, Dewey et Tesla; blueprint SVG archive; aucune execution applicative car recherche sans dev.
Limites: pas de test navigateur ni modification UI; verdict produit = GO conditionnel recherche, pas GO livraison.
Questions ouvertes: liste courte des types, arbitrage Reserve CS/droit coproprietaire, extraits masques, pages sensibles avant annotation, seuil lot.
Prochain mouvement propose: ouvrir un chantier dev separe pour simplifier `/documents/ajouter` si Brice valide cette relance.
```

Aucun code applicatif n'a ete produit. Aucun serveur local n'a ete lance. Aucune instance privee n'a ete modifiee.

UXUI-DONE - equipe UX/UI a fini son job
