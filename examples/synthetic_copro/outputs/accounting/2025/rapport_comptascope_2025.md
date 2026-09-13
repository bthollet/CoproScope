# Rapport ComptaScope 2025

Ce rapport explique ce que ComptaScope a rapproche localement, ce qui reste candidat, et ce qui doit etre controle en priorite.

## Synthese

- Factures candidates: 1
- Anomalies facture: 0
- Ecritures candidates: 1
- Total TTC facture: 1200.00 EUR
- Lignes d'etat des depenses exploitees: 1
- Rapprochements locaux suffisants: 1
- Candidats a confirmer P2: 0
- Points de rapprochement P1: 0
- Controles comptables ouverts: 0
- Controles comptables P0: 0
- Controles comptables P1: 0
- Controles comptables P2: 0
- Diligences fournisseur rattachees: 0
- Alias fournisseurs proposes: 0
- Alias auto-appliques: 0

## Lecture rapide

- `OK`: ComptaScope a une preuve locale suffisante pour rapprocher automatiquement.
- `P2`: ComptaScope a trouve un candidat local plausible; une confirmation humaine suffit souvent.
- `P1`: ComptaScope n'a pas assez d'indices locaux; il faut controler le grand livre, l'etat des depenses ou la piece.
- Les statuts P2 ne sont pas des erreurs: ce sont des traitements locaux avances qui evitent de demander une interpretation IA.

## Entrees FactureOps

FactureOps est la couche amont qui detecte les factures, extrait les champs utiles et signale les anomalies de piece. ComptaScope consomme ensuite ces factures candidates pour produire les ecritures et rapprochements.

| Niveau d'intensite | Factures | Role |
| --- | ---: | --- |
| L1_NATIVE_TEXT | 1 | Texte natif et parseurs deterministes |

## Anomalies facture

| Priorite | Anomalie | Nombre | Traitement attendu |
| --- | --- | ---: | --- |
| - | Aucune anomalie facture | 0 | - |

## Controles comptables

- Controles comptables ouverts: 0
- Controles comptables P0: 0
- Controles comptables P1: 0
- Controles comptables P2: 0
- Anomalies facture P0: 0
- Anomalies facture P1: 0

## Diligences fournisseur

ComptaScope ne relance pas une enquete fournisseur lorsqu'une diligence recente existe deja. Il rattache les factures marquees `DILIGENCE_REQUISE` au plan `DIL-DD-*`, aux worklists et aux resultats deja produits, puis limite les suites aux pieces manquantes ou aux recoupements prudents.

- Lignes de diligence facture: 0
- Deja couvertes par un resultat recent a recouper: 0
- Deja dans une worklist existante: 0
- A traiter selon la methodologie existante: 0

| Statut | Fournisseur | Facture | TTC | Diligences | Couverture existante | Action |
| --- | --- | --- | ---: | --- | --- | --- |
| - | - | - | 0.00 | - | Aucune facture marquee diligence | - |

## Etat des rapprochements facture / etat des depenses

| Statut | Libelle clair | Priorite | Nombre | Ce que cela veut dire | Traitement local applique | Confirmation attendue |
| --- | --- | --- | ---: | --- | --- | --- |
 | MATCH_AMOUNT_ALIAS | Montant exact + alias fournisseur | OK | 1 | Une seule ligne porte le meme TTC et un alias fournisseur configure ou deduit. | Application des alias locaux confirmes ou auto-applicables. | Conserver la trace de l'alias utilise. | 

## Traitements locaux appliques

ComptaScope applique ces traitements dans l'ordre, sans interpretation externe:

1. reference de facture dans l'etat des depenses ;
2. montant TTC exact avec fournisseur reconnu ;
3. montant TTC exact avec alias fournisseur configure ou deduit ;
4. montant TTC exact avec nom fournisseur tres similaire ;
5. montant TTC exact avec famille comptable compatible ;
6. division d'une facture en plusieurs lignes egales ;
7. somme de plusieurs lignes vers une facture ;
8. regroupement de plusieurs factures vers une ligne ;
9. qualification des cas restants en candidats P2 ou non-rapproches P1.

Un `NON_RAPPROCHE` ne veut donc pas dire que la facture est absente de la comptabilite. Cela veut dire qu'aucun traitement local n'a produit de preuve suffisante.

## Causes a traiter par ordre de priorite

| Priorite | Cause locale | Nombre | Action type |
| --- | --- | ---: | --- |
| - | Aucune cause ouverte | 0 | - |

## Fournisseurs a prioriser

| Fournisseur | Points ouverts | Total TTC ouvert | Priorite de lecture |
| --- | ---: | ---: | --- |
| - | 0 | 0.00 | Aucun point ouvert |

## Alias fournisseurs deduits

| Statut | Fournisseur | Alias propose | Preuves | Total TTC | Exemple |
| --- | --- | --- | ---: | ---: | --- |
| - | - | - | 0 | 0.00 | Aucun alias deduit |

## Exemples prioritaires a expliquer

| Priorite | Statut | Libelle clair | Fournisseur | Facture | TTC | Cause locale | Action demandee |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| - | - | - | - | - | - | Aucun point prioritaire | - |

## Prochaines actions automatisees

- Completer les alias fournisseurs locaux lorsque le montant existe mais le libelle differe.
- Departager les montants ambigus par reference, date, compte ou cle de repartition.
- Controler les ventilations multi-lignes avant de les traiter comme rapprochements forts.
- Comparer les blocages P1 restants avec le grand livre et les pieces manquantes.
