# DocOps actionnable

DocOps ne produit plus seulement un inventaire documentaire. La commande `missing-docs` construit une lecture de travail pour conseil syndical :

- `rapport_completude_documentaire.md` : synthese lisible, matrice actionnable et pieces a demander ;
- `matrice_completude_documentaire.csv` : une ligne par piece attendue, avec statut et preuves locales ;
- `pieces_a_demander.csv` : file courte des relances ou verifications a traiter.

## Statuts

| Statut | Sens operationnel |
|---|---|
| `PRESENT` | Une piece locale correspond au type attendu. |
| `ABSENT` | Aucune piece locale suffisante n'a ete trouvee. |
| `OBSOLETE` | Une piece existe, mais elle est plus ancienne que le seuil configure. |
| `A_CLASSER` | Une piece candidate existe, mais le classement est incertain. |

## Configuration

Les preuves attendues viennent de la matrice d'instance `matrice_preuves_attendues.csv` quand elle existe, sinon de `document_completeness.default.yml`.

Champs utiles :

- `proof_id` / `preuve_id` ;
- `lot` ;
- `expected_label` / `libelle_attendu` ;
- `document_type` / `type_document` ;
- `criticality` / `criticite` ;
- `freshness_months` / `fraicheur_mois`.

Les seuils de fraicheur restent optionnels. Sans seuil, une piece presente n'est pas marquee obsolete.

## Integration UI

La future vue documents peut consommer `matrice_completude_documentaire.csv` pour afficher "ce qu'on a" et `pieces_a_demander.csv` pour la liste priorisee des demandes au syndic.
