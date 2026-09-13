# La démo : une copropriété entièrement inventée

**Démo en ligne, en lecture seule :** <https://bthollet.github.io/CoproScope/>

## Ce que vous regardez

La *Résidence Les Glycines (fictive)* n'existe pas. Ses procès-verbaux, devis,
factures, contrats et courriers ont été **fabriqués par un générateur**, puis lus
par la vraie chaîne de CoproScope, exactement comme le seraient les pièces
envoyées par un syndic.

Les pièces se répondent d'un écran à l'autre : la résolution de travaux cite un
devis, la facture cite l'ordre de service, et la lettre du conseil syndical
réclame le procès-verbal de réception qui manque au dossier.

**Limite, dite franchement :** ces pièces ont été écrites pour que la chaîne les
lise. La démo prouve que la chaîne tourne ; elle ne prouve pas que CoproScope lit
juste les documents d'un vrai syndic.

## Par où commencer

1. **Contrôle › Gouvernance** : les décisions lues dans les procès-verbaux. Cliquez sur
   une pastille, par exemple « Résolution rejetée » : la liste se filtre sur place.
2. **Documents** : les pièces classées par famille ; ouvrez-en une.
3. **Pièces manquantes** et **Demandes au syndic** : ce qui manque au dossier.

L'écran **Contrôle › Comptes** reste vide sur la démo : la copropriété fictive n'a pas
encore d'état des dépenses.

## Ce que la version en ligne ne fait pas

C'est un export statique : les pages sont figées, les formulaires sont
neutralisés, rien n'est enregistré. Pour essayer l'application complète, la
lancer sur votre poste ([Développer](developper.md)).

## Reproduire la démo

```bash
python tools/pool_fictif/generer.py /tmp/demo-glycines
coprocs pipeline run --instance-root /tmp/demo-glycines
python tools/demo_statique/exporter.py --instance-root /tmp/demo-glycines --sortie /tmp/site
```

Le générateur est déterministe : mêmes pièces, mêmes octets, à chaque passage.
La page GitHub Pages est reconstruite ainsi par
[`.github/workflows/pages.yml`](../../.github/workflows/pages.yml).

## Notes liées

- [Carte des notes](carte.md)
- [Confidentialité](confidentialite.md)
- [Développer](developper.md)
