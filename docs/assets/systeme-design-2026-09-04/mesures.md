# Mesures brutes - audit systeme de design 2026-09-04

Serveur de recette : port 8796, instance de recette locale. Aucune donnee nominative
n'est reportee ici. Toutes les hauteurs sont en pixels CSS, mesurees par
`getBoundingClientRect()` dans le navigateur, pas deduites de la feuille de style.

## 1. Navigation entre deux vues - cout en hauteur (viewport 716 x 695)

Sondes injectees dans `.cs-main` de la page reelle, puis retirees.

| Candidat | 2 vues | 3 vues | Etat ouvert |
|---|---:|---:|---:|
| `cs-comptes-tabs` (barre nue) | 37 | 37 | n/a |
| `cs-reprise-tabs` (barre encadree) | 60 | 60 | n/a |
| `<details>` / `<summary>` | 44 | 44 | 99 |
| `<select>` dans une barre | 42 | 42 | n/a |
| Deroulant dans le bandeau lateral | 46 (bande repliee) | 46 | 224 a 566 |

Barre laterale, viewport 716 x 695 :

| Mesure | Valeur |
|---|---:|
| Hauteur de la bande repliee | 46 |
| Entrees visibles dans la bande | 2 sur 25 |
| Entrees masquees | 23 |
| Hauteur deployee, page `/comptes/rapprochement` | 224 |
| Hauteur deployee, page `/incidents` | 566 |
| Bandeau complet deploye, `/incidents` | 637 |
| Position de `.cs-main` apres deploiement | y = 744 (hors viewport 695) |
| `aria-expanded` sur la navigation | absent |

Barre laterale, viewport 1280 x 695 :

| Mesure | Valeur |
|---|---:|
| Hauteur du rail | 1484 |
| Debordement sous la ligne de flottaison | 789 |
| Entrees visibles sans defilement | 11 sur 25 |
| Largeur du rail | 276 |

## 2. En-tete

| Page | Viewport | Hauteur `.cs-topbar` |
|---|---|---:|
| `/comptes/rapprochement` | 716 x 695 | 58 |
| `/comptes` | 716 x 695 | 108 |
| `/actions` | 716 x 695 | 108 |
| `/incidents` | 716 x 695 | 108 |

Budget annonce : 61. Depassement mesure : 47 sur trois pages sur quatre.
Cause : `.cs-search` (38 px) passe sur sa propre ligne sous le titre (41 px).
A 716 px, `.instance-meta` et `.cs-top-action` passent en `display: none`.

## 3. Familles de ton - valeurs calculees sur element reel

| Classe | color | background | border-left-color |
|---|---|---|---|
| `cs-tone-ok` | #13976b | #edfdf7 | #13976b |
| `cs-tone-warn` | #f28705 | #fff7ed | #f28705 |
| `cs-tone-danger` | #df2f24 | #fff1f0 | #df2f24 |
| `cs-tone-info` | #1d5fd8 | #eef4ff | #1d5fd8 |
| `cs-card-tone-ok` | herite (#101828) | #edfdf7 | #13976b |
| `cs-reprise-tone-ok` | herite (#101828) | #f0fdf8 | #13976b |

`cs-tone-*` est defini deux fois : `styles_part_05.css` (couleur de texte seule)
et `styles_part_07.css` (fond + filet). Les deux s'appliquent.

## 4. Contraste mesure sur la page d'accueil, viewport 716

Balayage de tous les noeuds texte, fond calcule en remontant les ancetres.

| Combinaison | Ratio | Seuil | Verdict |
|---|---:|---:|---|
| #ffffff sur #2f73f6 (entree de navigation active) | 4.28 | 4.5 | echec |
| #138866 sur #eaf7f1 (pastille verte) | 4.02 | 4.5 | echec |
| #f28705 sur #fff7ed (`cs-status-dot` + `cs-tone-warn`) | 2.40 | 4.5 | echec, 3 occurrences |
| #1d5fd8 sur #eef4ff (onglet actif `cs-reprise-tabs`) | 5.17 | 4.5 | conforme |
| #1d5fd8 sur #ffffff | 5.71 | 4.5 | conforme |

Total sur la seule page d'accueil : 5 occurrences en echec, 3 combinaisons distinctes.

## 5. Poste de travail `cs-rappro-*`

| Mesure | 716 x 695 | 1280 x 800 |
|---|---:|---:|
| `.cs-rappro-workbench` colonnes | 1 (692) | 2 (430 + 491) |
| `.cs-rappro-matrix` largeur | 654 | 438 |
| `.cs-rappro-matrix-grid` | 4 x 159 | 4 x 105 |
| `.cs-rappro-source-cell` hauteur | 127 | 277 |
| `.cs-rappro-action` hauteur | 107 | 309 |
| Hauteur totale du poste | 1536 | 704 |

La cellule de matrice est plus haute sur ecran large que sur ecran etroit :
127 puis 277. La file `minmax(300px, 430px)` prend 430 px fixes et etrangle
la matrice a 105 px par colonne.

## 6. RM-2026-0067 - verification

| Mesure a 360 x 695 | Valeur |
|---|---:|
| `.cs-rappro-action` colonnes | 1 |
| `.cs-rappro-action` hauteur | 180 |
| Position haute de `.cs-rappro-matrix` | 737 |
| Hauteur totale de la page | 3915 |
| `document.documentElement.scrollWidth` | 360 |

Le repli etroit existe : `@media (max-width: 560px) { .cs-rappro-action { grid-template-columns: 1fr } }`
dans `styles_part_30.css`. Les valeurs 1740 et 2201 ne sont plus reproductibles.

## 7. Recensement du langage visuel

| Mesure | Valeur |
|---|---:|
| Fichiers CSS | 32 + 1 manifeste |
| Lignes de CSS | 10 490 |
| Classes `cs-*` distinctes | 354 |
| Classes non `cs-*` distinctes | 288 |
| Prefixes prives par ecran | 17 |
| Litteraux hexadecimaux | 653 |
| Valeurs hexadecimales distinctes | 122 |
| Appels `var(--*)` | 314 |
| Jetons definis dans `:root` | 20 |
| Jetons utilises mais jamais definis | 2 (`--border`, `--text`) |
| Declarations cassees par ces jetons | 38 (19 raccourcis, 19 longues) |
