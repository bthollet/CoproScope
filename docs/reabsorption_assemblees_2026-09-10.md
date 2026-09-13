# Réabsorption sur instance vide : ce que la chaîne fait vraiment

`RM-2026-0077` et `RM-2026-0164`, mesure du 2026-09-10.

## Le montage, et pourquoi il est le seul valable ici

Instance `test_reabsorption_ag_20260910`, **vide**, avec pour seul contenu
`instance.yml` et **68 pièces sources d'assemblée (288 Mo)** copiées depuis le
`raw/` de l'instance mère. `registers/`, `staging/`, `outputs/` et
`vault_local/` vides : la chaîne reconstruit tout. Le coffre n'est pas touché.

Dès qu'un lot touche la chaîne d'absorption, une base existante ne peut pas
servir de preuve : elle porte la **sortie** de la version précédente du code.
Cette mesure-là le démontre sur pièce, et pas seulement en principe.

**Restriction déclarée d'avance :** seules les pièces d'assemblée sont
réabsorbées, pas les 858 documents de la mère. Ce n'est donc pas une remesure
des dénombrements globaux.

## Ce que la comparaison établit

| | base fossile (858 pièces) | base fraîche (68 pièces) |
|---|---|---|
| assemblées | 12 | 6 |
| **titrées par un identifiant technique** | **8** | **1** |
| date de la convocation | `2026-04-29` | **`2026-04-03`** |
| résolutions écrasées en silence | — | **0** |
| liens `SEUIL_*_APPLICABLE` | 0 | **0** |

**La date fausse est prouvée, pas supposée.** Le document `DOC-827D11D51208`
est byte-identique dans les deux bases — 427 547 caractères — et le lecteur y
lit `03/04/2026`, la chaîne écrite dans le texte. La base fossile porte
`2026-04-29`, qui ne s'y trouve pas : elle vient d'ailleurs, très probablement
du dossier de collecte, c'est-à-dire exactement le défaut corrigé le
2026-09-08. **Le correctif fonctionne, et la base existante conserve l'erreur
qu'il a supprimée.**

## Le blocage de `RM-2026-0164` se réduit à UN document

Sur les quatre procès-verbaux et comptes rendus du corpus :

| document | type | date lue | candidats |
|---|---|---|---|
| `DOC-44C3D847DF7F` | PV_AG | `2024-10-01` | — |
| `DOC-060F5926BFAB` | PV_AG | `2024-07-03` | — |
| `DOC-4E67E59351D2` | PV_AG | **ambiguë** | 2 |
| `DOC-8FCF5BE8BD54` | CR_CS | **ambiguë** | **6** |

Le dernier porte **23 actes, dont les deux seuils de l'article 21** — 1 000 €
et 2 000 €, adoptés. Sa date étant ambiguë, `valide_du` reste vide,
`liens_seuil` l'écarte, et **aucune relation `SEUIL_*_APPLICABLE` n'est
écrite**. Tout le blocage de `RM-2026-0164` tient donc à **un document**.

**Et la bonne réponse n'est pas de faire élire une date au lecteur.** Six
candidats qui se disputent, c'est une ambiguïté réelle ; en élire une
fabriquerait un fait. C'est le cas d'usage exact de l'écran d'ancrage manuel,
`RM-2026-0158` : un humain tranche, la trace porte qui l'affirme, et la
ré-extraction ne l'écrase pas.

Second fait à signaler : ce `CR_CS` est un compte rendu de conseil syndical, et
il porte 23 actes rangés sous une pseudo-assemblée. Qu'un compte rendu de
conseil syndical devienne une assemblée est une question de typage, distincte
de celle de la date.

## Une incohérence interne, et sa limite

Une déclaration de la base fraîche vise l'assemblée `2025-12-03`, et **aucune
assemblée de cette base ne porte cette date** — elle contient `AG-2025-11-06`.
Deux lectures possibles, et le corpus restreint ne permet pas de trancher : le
procès-verbal du 03/12/2025 n'est peut-être simplement pas dans mes 68 pièces.
À reprendre sur une réabsorption complète.

## Ce que je corrige de mon propre passage précédent

J'avais écrit que « la date absente n'est pas reproductible avec le code
d'aujourd'hui » et j'en avais conclu qu'aucun défaut vivant n'était établi.
La première moitié est juste — le lecteur lit bien ces dates — **mais la
conclusion était trop forte** : sur données fraîches, une assemblée sur six
reste sans date lisible, et c'est précisément celle qui porte les seuils. Le
bilan de la chaîne le disait de lui-même, `sans_date_lisible: 9` sur 26
documents d'assemblée. Il fallait la réabsorption pour le voir ; l'appel isolé
du lecteur ne pouvait pas.
