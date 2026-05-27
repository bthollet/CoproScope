# Recherche UX/UI - ajout docs approfondissement

Date de relance: 2026-05-24 09:38 +02:00.
Mode: equipe UX/UI recherche visuelle sans dev.
Sources principales:

- `docs/recherche_ux_ui_2026-05-24_ajout-docs.md`
- `docs/recherche_ux_ui_2026-05-24_ajout-docs_relance.md`
- `docs/recherche_ux_ui_2026-05-24_ajout-docs_relance2.md`

## BOT-START

```text
BOT-START - Orchestrateur UX/UI - 2026-05-24 09:38 +02:00
Roadmap: RM-2026-0003 principal; liens RM-2026-0006, RM-2026-0010, RM-2026-0029.
Chantier: CH-20260524-093819-RM-2026-0003-ajout-docs-approfondissement-ux-ui
Conversation: CONV-2026-1396
Role: Orchestrateur UX/UI
Mission: approfondir l'equipe UX/UI ajout-docs et preparer un cadrage de decision final sans dev.
Ownership modifiable: docs/recherche_ux_ui_2026-05-24_ajout-docs_approfondissement.md; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-approfondissement/; docs/presence_agents.md.
Fichiers a eviter: code applicatif, tests, instances privees, secrets, exports bruts, passerelles hors mission, serveurs locaux, chantier reconstruction bloque RM-2026-0017.
Passerelle/registre de trace: ce document et docs/presence_agents.md.
Dernier point lu: docs/recherche_ux_ui_2026-05-24_ajout-docs_relance2.md, docs/presence_agents.md.
Tests/preuves attendus: synthese multi-roles, protocole de decision final, readiness/no-go dev, mention explicite qu'aucun code n'a ete produit.
Risque de collision: equipes UX/UI comptes/sync et gouvernance peuvent etre actives; rester sur ajout-docs uniquement.
Lease ownership: jusqu'au 2026-05-25 09:38 +02:00.
Prochaine action: lancer les roles UX/UI en lecture seule.
```

## Objectif

Approfondir les trois questions encore ouvertes avant toute suite dev:

- qui tranche en dernier ressort la frontiere `Reserve conseil syndical` vs droit d'acces coproprietaire;
- quels motifs structures exacts retenir en premiere version;
- quand rendre obligatoire le marquage des pages sensibles.

La relance doit aussi dire si les blueprints existants suffisent ou si une image supplementaire est utile.

## Roles actifs

| Conversation | Role | Mission | Statut |
|---|---|---|---|
| `CONV-2026-1396` | Orchestrateur UX/UI | Cadre, trace, arbitre et consolide. | En cours |
| `CONV-2026-1397` | Chercheur utilisateur | Scenario de decision humaine et reprise apres doute. | En cours |
| `CONV-2026-1398` | Architecte UX | Protocole d'ecran final, motifs et pages sensibles. | En cours |
| `CONV-2026-1399` | Designer UI / generateur visuel | Image supplementaire ou annotation des blueprints existants. | En cours |
| `CONV-2026-1400` | Testeur metier expert | Arbitrage metier final et no-go dev. | En cours |
| `CONV-2026-1401` | Testeur accessibilite / novice | Comprehension novice et decisions bloquees. | En cours |

## Synthese de convergence

L'equipe confirme la doctrine suivante: un document ajoute reste local tant
qu'une decision humaine n'a pas valide sa visibilite. L'ouverture aux
coproprietaires autorises est le defaut produit, apres verification et masquage
si necessaire. `Reserve conseil syndical` n'est pas une case de prudence: elle
demande un motif metier explicite. En cas de doute sur le droit d'acces,
l'utilisateur choisit `A decider plus tard`.

## Parcours recommande

1. `Ajouter depuis mon ordinateur` avec le rappel `Le fichier reste local. Rien
   n'est partage.`
2. Confirmation neutre: `Fichier ajoute localement`, reference opaque seulement.
3. Choix du type court: les 7 familles deja retenues + `Je ne sais pas encore`.
4. Choix obligatoire de visibilite: `Qui pourra voir ce document ?`
5. Motif obligatoire si le statut l'exige.
6. Pages sensibles a renseigner si `A masquer avant partage`, PDF mixte ou
   doute de diffusion.
7. Rattachement leger: sujet, action suivie, ce que le document aide a verifier.
8. Recapitulatif final: local, visibilite, motif/pages, rattachement, reste a
   faire.
9. Sortie unique: `Enregistrer localement`.

## Motifs fermes v1

Motif obligatoire pour `A masquer avant partage`, `Reserve au conseil syndical`
et `Non diffusable`.

- `donnees personnelles`
- `RIB ou coordonnees bancaires`
- `impayes nominatifs`
- `contentieux en cours`
- `salarie ou prestataire`
- `negociation ou strategie`
- `pages mixtes`
- `qualite ou OCR insuffisant`
- `autre motif prudent a requalifier`

Le motif reste categoriel. Il ne doit pas recopier de nom, extrait OCR, numero
de compte, chemin local ou donnee sensible.

## Regle `Reserve conseil syndical`

`Reserve conseil syndical` est autorise seulement si un motif metier justifie
de ne pas ouvrir l'acces a ce stade: contentieux, negociation, strategie,
impayes nominatifs, salarie/prestataire, situation personnelle ou risque
comparable.

Si le document peut devenir communicable par masquage, choisir `A masquer avant
partage`, pas `Reserve conseil syndical`. Si le droit d'acces est incertain,
choisir `A decider plus tard`, pas `Reserve conseil syndical`.

## Pages sensibles

Ne pas demander les pages sensibles des le depot. Les demander apres le choix
`A masquer avant partage`, en cas de PDF mixte, ou quand le document reste `A
decider plus tard` faute de verification suffisante.

Avant toute creation de derive diffusable, exiger pages ou ranges precis, motif
categoriel et confirmation humaine. Un PDF avec une seule page sensible n'est
jamais diffusable brut.

## Images et assets

Decision designer: pas de nouvelle image. Les blueprints existants suffisent,
avec annotations conceptuelles.

- `docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance/01-matrice-confidentialite-recapitulatif.svg`
  reste la reference pour l'etape `Qui pourra voir ce document ?`.
- `docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance2/01-qualification-finale-type-pages-lot.svg`
  reste la reference pour type court, pages sensibles et bascule lot.

Annotations a retenir: une decision a la fois, brut local, PDF mixte jamais
diffusable tel quel, mode lot propose mais jamais impose, `Reserve CS` avec
motif metier.

## Retours testeurs

Retour metier: GO recherche si les regles deviennent bloquantes dans la future
UI. NO-GO si `Reserve CS` est possible sans motif, si un PDF mixte devient
diffusable brut, si des extraits non masques apparaissent, ou si hash/OCR/type
sont presentes comme validation juridique.

Retour accessibilite/novice: l'utilisateur doit comprendre en 30 secondes que
`ajoute localement` ne veut pas dire `diffusable`. Le parcours doit garder une
decision dominante par ecran, eviter les codes internes et proposer des sorties
normales `Je ne sais pas encore` et `A decider plus tard`.

## Readiness pour suite dev

GO recherche pour ouvrir un chantier dev separe si Brice valide ce cadrage.
NO-GO livraison tant que la future interface ne bloque pas:

- `Reserve CS` sans motif;
- PDF mixte diffusable brut;
- diffusion avec statut `A decider plus tard`;
- motif contenant une donnee sensible;
- confusion entre depot local et partage;
- chemins locaux, noms de fichiers prives, OCR brut ou hash au premier niveau.

## BOT-END

```text
BOT-END - Orchestrateur UX/UI - 2026-05-24 09:55 +02:00
Roadmap: RM-2026-0003 principal; liens RM-2026-0006, RM-2026-0010, RM-2026-0029.
Chantier: CH-20260524-093819-RM-2026-0003-ajout-docs-approfondissement-ux-ui
Conversation: CONV-2026-1396
Statut: CLOTURE
Fichiers modifies: docs/recherche_ux_ui_2026-05-24_ajout-docs_approfondissement.md; docs/presence_agents.md.
Fichiers volontairement evites: code applicatif, tests, instances privees, secrets, exports bruts, passerelles hors mission, serveurs locaux, RM-2026-0017 bloque.
Tests/preuves: cinq roles UX/UI relances sans duplication et consolides; aucune image nouvelle necessaire; verification markdown/diff-check a lancer.
Limites: pas de test navigateur, pas de validation juridique externe, pas de dev.
Questions ouvertes: arbitrage Brice pour ouvrir ou non un chantier dev separe.
Prochain mouvement propose: si valide, cadrer une suite dev distincte avec ces regles comme contraintes bloquantes.
```

UXUI-DONE - equipe UX/UI a fini son job
