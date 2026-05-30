# Exploration feature - Tracage PDF inspire Zotero

Date: 2026-05-31
Roadmap: `RM-2026-0045`
Chantier: `CH-20260531-005040-RM-2026-0045-tracage-pdf-zotero`
Conversation: `CONV-2026-1909`
Statut: exploration documentaire, sans dev.

## BOT-START

Role: coordinateur exploration feature.

Mission: verifier si la future fonction de tracage des informations dans les
PDF doit s'appuyer sur les briques utiles de Zotero plutot que sur le moteur
actuel.

Ownership modifiable: cette note, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`.

Fichiers evites: code produit, moteur PDF actuel, instances privees, documents
bruts, OCR/logs, exports bruts, secrets, serveurs, scans/kills, push GitHub et
lots Drive/Compta en cours.

Tests/preuves attendus: verification licence CoproScope/Zotero, lecture de
l'existant annotations/PDF, recommandation V1 non destructive.

## Synthese courte

La methode est adaptee, a condition de rester en exploration legere. Cette
fonction touche les preuves, les PDF et la confidentialite: il faut donc une
trace de decision avant de coder.

La recommandation est de ne pas remplacer tout le moteur actuel. Il faut garder
DocOps pour l'inventaire, l'extraction texte, l'OCR futur et les controles de
confidentialite. En revanche, pour le tracage visuel dans les PDF, Zotero donne
un tres bon modele: selection de texte, rectangles de surlignage, ordre des
annotations, commentaires et tags.

Le bon compromis est donc:

- CoproScope reste la source de verite.
- Le PDF original reste intact.
- Zotero inspire ou fournit la couche de lecture/selection.
- L'annotation finale est stockee dans CoproScope sous forme de donnees a cote
  du PDF, pas dans le PDF lui-meme.

## Point licence

CoproScope est maintenant indique en `AGPL-3.0-only` dans `LICENSE`, le README
racine et `server/pyproject.toml`.

Le lecteur Zotero officiel reste sous `AGPL-3.0` d'apres:

- `https://raw.githubusercontent.com/zotero/reader/master/package.json`
- `https://raw.githubusercontent.com/zotero/reader/master/COPYING`

Consequence simple: la licence n'est plus un mur comme elle l'etait si
CoproScope avait du rester ferme ou sous licence incompatible. Mais ce n'est
pas un feu vert aveugle. Si CoproScope integre du code Zotero, il faudra garder
les notices, tracer les modifications, publier le code correspondant et
respecter les marques Zotero.

Pour une V1, la meilleure pratique reste de commencer par un prototype isole,
sur documents fictifs, avec une frontiere claire entre:

- le lecteur PDF;
- l'adaptateur qui transforme une selection en annotation CoproScope;
- le registre CoproScope qui garde la preuve.

## Etat actuel CoproScope

L'existant va deja dans la bonne direction.

`annotationops` definit une annotation non destructive: page, zone normalisee,
commentaire, rattachement point/action/preuve, diffusion et confidentialite.
Il bloque aussi les chemins locaux et prepare un evenement futur
`pdf_annotation_created`.

Les docs actuelles disent deja que l'annotation doit rester une donnee sidecar:
elle est stockee a cote du PDF, sans modifier le fichier original.

DocOps extrait deja le texte des PDF avec PyMuPDF puis pypdf en secours. Cette
brique sert a inventorier, lire et indexer. Elle ne remplace pas une vraie
interaction de selection visuelle dans un lecteur PDF.

La vue document affiche deja l'idee d'un futur journal collaboratif, mais elle
ne permet pas encore de selectionner une zone dans le PDF et de la rejouer
visuellement.

## Ce que Zotero apporte vraiment

Les briques utiles ne sont pas "Zotero complet". Ce sont surtout:

- un lecteur PDF/EPUB/HTML deja pense pour annoter;
- un modele d'annotation avec type, couleur, commentaire, tags et dates;
- une position PDF par page et rectangles;
- un ordre de tri stable pour retrouver les annotations;
- une logique de selection qui transforme une selection utilisateur en zones
  exploitables.

Le point important: Zotero sait tres bien capter "ce que l'utilisateur a
selectionne dans le PDF". CoproScope sait mieux dire "pourquoi cette selection
compte dans un dossier de copropriete".

## Ecart a combler

Il y a une difference de vocabulaire technique entre les deux mondes:

| Sujet | CoproScope aujourd'hui | Zotero reader |
|---|---|---|
| Page | page humaine a partir de 1 | `pageIndex` a partir de 0 |
| Zone | rectangle normalise `x/y/width/height` | liste de rectangles PDF |
| Sens metier | point, action, preuve, diffusion | annotation, commentaire, tags |
| Source de verite | CoproScope / vault / sidecar | stockage Zotero ou callbacks reader |
| Confidentialite | centrale | a ajouter cote CoproScope |

Il faut donc un adaptateur, pas un remplacement brutal.

## Modele V1 conseille

Pour une annotation PDF V2, ajouter ou preparer les champs suivants:

| Champ | Pourquoi |
|---|---|
| `document_ref` | identifier le document sans chemin local |
| `document_hash` | verifier que le PDF vise est bien le meme |
| `page_index` | parler au lecteur PDF |
| `page_label` | afficher la page comme dans le document |
| `rects` | rejouer le surlignage avec precision |
| `selected_text_hash` | reconnaitre le texte sans recopier trop de contenu sensible |
| `selected_text_excerpt` | court extrait lisible, limite et passe au filtre privacy |
| `comment` | note humaine |
| `color` | lecture rapide visuelle |
| `tags` | tri simple, sans remplacer les liens metier |
| `sort_index` | ordre stable dans le document |
| `point_ref`, `action_ref`, `proof_ref` | chaine CoproScope fait -> preuve -> action |
| `diffusion`, `confidentiality` | eviter qu'une annotation sensible soit partagee |
| `source_engine` | savoir si l'ancre vient de Zotero, PDF.js ou CoproScope |

La V1 doit accepter que certains PDF n'aient pas de texte selectionnable. Dans
ce cas, l'utilisateur peut tracer une zone image, mais CoproScope doit afficher
"texte non confirme" au lieu d'inventer une citation.

## Prototype recommande

Prototype jetable, sur PDF fictifs uniquement:

1. Ouvrir un PDF de demo dans un lecteur inspire Zotero.
2. Selectionner une phrase ou une zone.
3. Enregistrer une annotation CoproScope sidecar avec page, rectangles,
   commentaire et rattachement optionnel a une preuve.
4. Fermer puis rouvrir le PDF.
5. Verifier que le surlignage revient au meme endroit.
6. Verifier que le hash du PDF original n'a pas change.
7. Verifier qu'aucun chemin local, contenu brut sensible ou extrait trop long
   ne sort dans l'UI ou les exports.

Ce prototype ne doit pas encore:

- remplacer l'extraction DocOps;
- modifier les PDF;
- importer toute une bibliotheque Zotero;
- ecrire dans une instance privee;
- publier d'annotation sans revue de diffusion.

## Risques a surveiller

| Risque | Pourquoi c'est important | Garde-fou |
|---|---|---|
| Copie de code Zotero mal encadree | AGPL compatible mais obligations reelles | notices, source, modifications tracees |
| PDF modifie par erreur | perte de confiance probatoire | hash avant/apres obligatoire |
| Mauvais emplacement au rechargement | preuve impossible a relire | tests sur pages tournees, zoom, multi-pages |
| PDF scanne sans texte | selection texte absente | mode zone image + statut "texte non confirme" |
| Extrait sensible dans le commentaire | fuite de donnees | limite d'extrait + PrivacyOps |
| Moteur trop lourd | dette maintenance | isoler en plugin/adaptateur |
| Confusion "piece" vs "preuve" | erreur metier | validation humaine avant preuve confirmee |

## Decision proposee

GO pour une exploration/prototype V1, mais pas pour un remplacement du moteur
PDF actuel.

Le bon intitule produit serait:

`Tracer une preuve dans un PDF`

et non:

`Remplacer le moteur PDF par Zotero`

En langage utilisateur, la promesse doit etre:

> Je selectionne un passage ou une zone dans une piece, j'explique pourquoi ca
> compte, puis CoproScope garde le lien vers la preuve sans modifier le PDF.

## Cadrage complet requis avant dev

Rectification du 2026-05-31: l'exploration legere ci-dessus ne suffit pas pour
demarrer une feature produit. Elle doit etre completee par le cadrage
documentaire:

`docs/archive/audits_recherches/cadrage_tracage_pdf_zotero_2026-05-31.md`

Ce cadrage ajoute le blueprint de service, le blueprint UI cible sans dev,
l'event storming, le parcours novice, le contrat de donnees, les risques, les
tests d'acceptation et le gate de reprise developpement.

Tout code commence avant ce gate doit etre considere comme brouillon local non
integrable tant que ce cadrage n'est pas relu ou accepte.

## Suite conseillee

Si Brice valide, ouvrir un petit chantier prototype sous `RM-2026-0045` avec
un owner unique et un corpus fictif. Le livrable attendu serait une preuve
simple: selectionner, enregistrer, rouvrir, revoir le tracage au meme endroit,
et prouver que le PDF n'a pas bouge.

Le developpement ne devrait commencer qu'apres un choix d'architecture:

- soit integration directe et assumee du lecteur Zotero, compatible AGPL;
- soit lecteur PDF.js avec modele d'annotation CoproScope inspire de Zotero;
- soit adaptateur separant strictement lecteur et registre CoproScope.

Recommandation: commencer par l'adaptateur. C'est le plus prudent, le plus
testable et le plus coherent avec la source de verite CoproScope.

## Sources consultees

Sources CoproScope:

- `docs/annotations_pdf_collaboratives.md`
- `docs/archive/notes_integration/integration_ui_annotations.md`
- `docs/veille_open_source_integration.md`
- `server/src/coproscope/modules/annotationops.py`
- `server/src/coproscope/modules/_docuscope_parts/01_inventory_and_extraction.py`
- `server/src/coproscope/web/_document_viewer_parts/01_detail_sections.py`
- `server/src/coproscope/vault/projection_events.py`

Sources Zotero officielles ou primaires:

- `https://www.zotero.org/support/pdf_reader`
- `https://www.zotero.org/support/kb/annotations_in_database`
- `https://www.zotero.org/support/dev/web_api/v3/basics`
- `https://www.zotero.org/support/dev/client_coding/javascript_api`
- `https://github.com/zotero/reader`
- `https://raw.githubusercontent.com/zotero/reader/master/package.json`
- `https://raw.githubusercontent.com/zotero/reader/master/COPYING`
