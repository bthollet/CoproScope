# Recherche UX/UI - ajout docs relance 2

Date de relance: 2026-05-24 09:26 +02:00.
Mode: equipe UX/UI recherche visuelle sans dev.
Sources principales:

- `docs/recherche_ux_ui_2026-05-24_ajout-docs.md`
- `docs/recherche_ux_ui_2026-05-24_ajout-docs_relance.md`
- `docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance/01-matrice-confidentialite-recapitulatif.svg`

## BOT-START

```text
BOT-START - Orchestrateur UX/UI - 2026-05-24 09:26 +02:00
Roadmap: RM-2026-0003 principal; liens RM-2026-0006, RM-2026-0010, RM-2026-0029.
Chantier: CH-20260524-092621-RM-2026-0003-ajout-docs-relance2-ux-ui
Conversation: CONV-2026-1374
Role: Orchestrateur UX/UI
Mission: relancer l'equipe UX/UI ajout-docs pour trancher les arbitrages restants.
Ownership modifiable: docs/recherche_ux_ui_2026-05-24_ajout-docs_relance2.md; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance2/; docs/presence_agents.md.
Fichiers a eviter: code applicatif, tests, instances privees, secrets, exports bruts, passerelles hors mission, serveurs locaux, chantier reconstruction bloque RM-2026-0017.
Passerelle/registre de trace: ce document et docs/presence_agents.md.
Dernier point lu: docs/recherche_ux_ui_2026-05-24_ajout-docs_relance.md, docs/presence_agents.md.
Tests/preuves attendus: synthese multi-roles, arbitrages finaux, blueprint si utile, mention explicite qu'aucun code n'a ete produit.
Risque de collision: equipes UX/UI gouvernance et comptes/sync actives; rester sur ajout-docs uniquement.
Lease ownership: jusqu'au 2026-05-25 09:26 +02:00.
Prochaine action: lancer les roles UX/UI en lecture seule.
```

## Objectif

Clore les cinq questions encore ouvertes apres la relance precedente:

- liste courte des types documentaires de premier niveau;
- frontiere entre `Reserve conseil syndical` et droit d'acces coproprietaire;
- niveau d'extrait masque acceptable apres premier arbitrage confidentialite;
- materialisation des pages sensibles avant le futur outil d'annotation PDF;
- seuil ou declencheur de bascule vers le tri de lot.

## Roles actifs

| Conversation | Role | Mission | Statut |
|---|---|---|---|
| `CONV-2026-1374` | Orchestrateur UX/UI | Cadre, trace, arbitre et consolide. | En cours |
| `CONV-2026-1375` | Chercheur utilisateur | Prioriser les arbitrages restants. | En cours |
| `CONV-2026-1376` | Architecte UX | Structurer wireflow final et etats. | En cours |
| `CONV-2026-1377` | Designer UI / generateur visuel | Proposer blueprint final si utile. | En cours |
| `CONV-2026-1378` | Testeur metier expert | Arbitrer droit coproprietaire, Reserve CS et pages sensibles. | En cours |
| `CONV-2026-1379` | Testeur accessibilite / novice | Tester comprehension des arbitrages. | En cours |

## Arbitrages finaux

- La liste courte de types reste limitee a sept familles plus `Je ne sais pas encore`.
- `Reserve conseil syndical` n'est jamais un reflexe de prudence. En cas de doute sur le droit d'acces coproprietaire, choisir `A decider plus tard`.
- Les extraits visibles ne sont jamais affiches au premier niveau. Apres arbitrage, seuls un resume ou un extrait local masque peuvent etre montres.
- Les pages sensibles sont materialisees avant l'outil futur d'annotation PDF, mais comme metadonnees locales de revue, pas comme annotation promise.
- Le mode lot est propose a partir de 5 documents, recommande a partir de 10 ou depuis une file DocOps, jamais active automatiquement.

## Liste courte de types

- `Assemblee generale / decision`
- `Comptes / budget / appels`
- `Facture / devis / contrat`
- `Travaux / maintenance`
- `Incident / sinistre`
- `Contentieux / impayes / litige`
- `Courrier / demande autre`
- `Je ne sais pas encore`

La liste courte sert seulement au premier niveau. Les precisions plus fines viennent ensuite.

## Regle `Reserve conseil syndical`

La regle produit reste l'ouverture par defaut aux coproprietaires autorises, apres verification et biffage si necessaire.

`Reserve conseil syndical` est autorise seulement avec un motif trace:

- strategie ou negociation;
- contentieux en cours;
- situation nominative ou dossier personnel;
- salarie, prestataire ou donnees de tiers;
- impayes nominatifs;
- document interne temporaire qui doit etre requalifie ensuite.

Si le document est communicable apres masquage, choisir `A masquer avant partage`, pas `Reserve conseil syndical`.

## Extraits masques et pages sensibles

### Extraits

Aucun extrait au premier niveau. Apres un premier arbitrage de confidentialite, un extrait peut etre affiche seulement s'il est local, court, masque et marque `a verifier`.

Interdits dans l'extrait: nom propre, lot privatif precis, RIB, adresse, mail, telephone, reference bancaire, OCR brut, chemin local, nom de fichier original.

### Pages sensibles

Pour un PDF mixte, le brut n'est jamais diffusable tel quel.

Avant le futur outil d'annotation PDF, les pages sensibles sont de simples metadonnees locales:

- `pages a verifier`;
- `pages a masquer`;
- `motif: RIB`;
- `motif: donnees personnelles`;
- `motif: impayes nominatifs`;
- `motif: contentieux`.

Le detail page/range est demande apres choix `A masquer` ou avant creation d'un derive, pas des le depot.

## Bascule lot

- 1 a 3 documents: parcours guide, une piece active a la fois.
- 4 a 9 documents: proposer `Passer en tri de lot`, sans l'imposer.
- 10 documents ou plus: recommander le tri de lot, avec retour possible au guide.
- File DocOps existante: ouvrir le tri de lot si l'intention est de corriger vite une file.
- Actions groupees interdites pour `Diffusable` si risque PrivacyOps, OCR faible, PDF mixte ou motif manquant.

## Blueprint retenu

- Chemin: `docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance2/01-qualification-finale-type-pages-lot.svg`
- Statut: `retenue`
- Intention: completer la matrice de confidentialite avec le choix de type court, le signalement des pages sensibles et la bascule lot non automatique.
- Retour metier: GO conditionnel, avec ouverture par defaut aux coproprietaires autorises et motifs stricts pour restrictions.
- Retour novice/accessibilite: GO conditionnel, si l'ecran reste sequentiel et si les pages sensibles sont presentees comme une revue, pas une annotation automatique.

## Verdict

GO recherche consolide pour passer a une suite dev separee si Brice valide.

NO-GO livraison si l'interface:

- reserve au conseil syndical sans motif;
- diffuse un PDF mixte brut;
- affiche un extrait non masque;
- active automatiquement le mode lot;
- montre des codes techniques au premier niveau;
- laisse croire que hash, OCR ou classification valident juridiquement le contenu.

## Questions restantes minimales

- Qui valide en dernier recours la frontiere `Reserve conseil syndical` vs droit d'acces coproprietaire ?
- Quels motifs structures exacts seront dans la liste fermee de la premiere version ?
- Le marquage des pages sensibles est-il obligatoire des le statut `A masquer`, ou seulement avant creation du derive ?

## BOT-END

```text
BOT-END - Orchestrateur UX/UI - 2026-05-24 09:38 +02:00
Roadmap: RM-2026-0003 principal; liens RM-2026-0006, RM-2026-0010, RM-2026-0029.
Chantier: CH-20260524-092621-RM-2026-0003-ajout-docs-relance2-ux-ui
Conversation: CONV-2026-1374
Statut: CLOTURE
Fichiers modifies: docs/recherche_ux_ui_2026-05-24_ajout-docs_relance2.md; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance2/.gitkeep; docs/assets/ux-ui-recherche-2026-05-24-ajout-docs-relance2/01-qualification-finale-type-pages-lot.svg; docs/presence_agents.md.
Fichiers volontairement evites: code applicatif, tests, instances privees, secrets, exports bruts, passerelles hors mission, serveurs locaux, RM-2026-0017 bloque.
Tests/preuves: syntheses Boyle, Bernoulli, Confucius, Bacon et Dalton; blueprint SVG archive; aucune execution applicative car recherche sans dev.
Limites: pas de test navigateur ni modification UI; verdict produit = GO recherche, pas GO livraison.
Questions ouvertes: arbitre final Reserve CS/droit coproprietaire, liste fermee de motifs, moment exact du marquage pages sensibles.
Prochain mouvement propose: ouvrir un chantier dev separe sur `/documents/ajouter` si Brice valide l'ensemble des trois recherches ajout-docs.
```

Aucun code applicatif n'a ete produit. Aucun serveur local n'a ete lance. Aucune instance privee n'a ete modifiee.

UXUI-DONE - equipe UX/UI a fini son job
