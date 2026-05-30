# Equipe agile - Tracage PDF inspire Zotero

Date: 2026-05-31
Roadmap: `RM-2026-0045`
Ordre: `ORD-P1-043`
Chantier: `CH-20260531-011534-RM-2026-0045-pdf-trace-page-map`
Conversation: `CONV-2026-1912`

Statut courant: cadrage relu; dev backend V1 reouvert uniquement pour la
brique interne de carte PDF texte. L'UI reste en NO-GO avant visuel IA,
blueprint UI dedie et qualification novice.

## Objectif

Livrer progressivement l'integration des briques pertinentes de Zotero dans
CoproScope, sans remplacer DocOps et sans modifier les PDF originaux.

Le premier geste utilisateur cible est:

```text
Ouvrir un PDF -> tracer une preuve -> garder la zone et le sens metier.
```

## Routage equipe

ROUTAGE_EQUIPE

Preflight: OK, avec collisions connues evitees.

Equipe-type iteration 1: `BACKEND_DOMAINE`.

Raison: avant l'UI de tracage, CoproScope doit savoir produire une carte de
page: mots, rectangles, hash du texte selectionne et position rejouable.

Iteration suivante prevue: `AGILE_UI_PRODUIT` sur la fiche document, avec le
bouton novice `Tracer une preuve dans ce PDF`.

Owner code unique iteration 1:

- `server/src/coproscope/modules/pdftraceops.py`
- `server/tests/test_pdftraceops.py`

Fichiers evites:

- UI document/detail pendant cette tranche;
- `annotationops.py`, sauf usage par les tests de pont;
- moteur PDF historique;
- instances privees;
- documents bruts;
- OCR/logs;
- exports bruts;
- secrets;
- serveurs;
- scans/kills;
- push GitHub.

## Retours agents

Franklin, exploration backend lecture seule:

- confirmer une brique pure separee de `annotationops.py`;
- produire une carte visuelle PDF texte;
- garder `document_ref + document_hash`;
- convertir seulement ensuite vers annotation sidecar CoproScope.

Bernoulli, exploration UX/QA lecture seule:

- cible UI: bouton `Tracer une preuve dans ce PDF` dans `/documents/{doc_id}`;
- statut utilisateur: `Preuve candidate a verifier`;
- message obligatoire: le PDF original ne sera pas modifie;
- prochaine iteration UI doit rejouer le rectangle apres rechargement.

## Decision produit

La feature a deux couches:

1. Couche DocOps: retrouver ou pointer l'information dans la page.
2. Couche CoproScope: rattacher cette information a un point, une action, une
   preuve candidate et une regle de diffusion.

Pour les PDF texte, la position peut etre deduite sans IA vision, a partir des
coordonnees des mots.

Pour les scans ou pages image, une future lecture OCR/vision devra produire a
la fois l'information lue et sa zone. Elle devra rester candidate tant qu'un
humain n'a pas valide.

## Rectification methode

Le demarrage backend a ete trop rapide. Pour une nouvelle feature transverse,
la methode attend d'abord une exploration documentaire complete:

- blueprint de service;
- event storming;
- parcours novice;
- contrat de donnees;
- risques, privacy, licence;
- criteres d'acceptation;
- gate clair avant dev.

Ce cadrage est maintenant porte par:

`docs/archive/audits_recherches/cadrage_tracage_pdf_zotero_2026-05-31.md`

## Commande dev candidate iteration 1

Creer une brique pure `pdftraceops` qui:

- extrait une carte de page PDF texte via PyMuPDF quand disponible;
- accepte aussi une carte de mots fournie par tests ou par un futur moteur;
- retrouve une phrase dans les mots d'une page;
- produit une position proche du modele Zotero: `pageIndex`, `pageLabel`,
  `rects`, `sortIndex`;
- produit une ancre CoproScope: page humaine, zone normalisee, hash du texte;
- convertit la trace en ligne compatible `annotationops.normalize_annotation`;
- masque l'extrait si un chemin local ou marqueur sensible apparait;
- ne lit ni n'ecrit aucune instance privee;
- ne modifie jamais le PDF.

Cette commande est executable depuis la revue de cadrage du 2026-05-31 01:25.
Elle reste bornee au backend interne: pas de route UI, pas de lecteur PDF
integre, pas de copie de code Zotero.

## Criteres d'acceptation iteration 1

- Une phrase peut etre retrouvee dans une page fictive et convertie en
  rectangles normalises.
- La position exposee reste compatible avec un lecteur type Zotero.
- La conversion vers annotation CoproScope produit une annotation valide.
- Le plan sidecar interdit explicitement l'ecriture dans la source.
- Un texte contenant un chemin local est masque dans le payload public.
- Le payload de carte de page ne contient pas le chemin du PDF.
- Les tests dedies passent.

## Iteration suivante

Equipe-type cible: `AGILE_UI_PRODUIT`.

UI cible:

```text
/documents/{doc_id} -> bouton "Tracer une preuve dans ce PDF"
```

Wording novice retenu:

- `Tracer une preuve dans ce PDF`
- `Encadrez le passage utile. CoproScope gardera le lien, sans changer le PDF.`
- `Ce passage prouve que...`
- `Preuve candidate a verifier`
- `Qui peut voir cette trace ?`
- `Le fichier a change depuis la trace. Verifiez avant de vous en servir.`
- `Texte non confirme : seule la zone encadree est gardee.`

## Garde-fous

- Pas de copie de code Zotero dans cette tranche.
- La licence AGPL rend l'integration possible, mais n'annule pas les notices,
  obligations de source et traces de modification si du code Zotero est repris
  plus tard.
- Toute preuve reste candidate tant qu'un humain ne l'a pas validee.
- Toute ancre devient `a verifier` si le hash du PDF ne correspond plus.
