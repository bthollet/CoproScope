# Architecture

CoproScope sépare trois choses qui ne se mélangent jamais : **le code**, **les
pièces d'une copropriété**, et **ce que le code en déduit**.

```text
pièces reçues (lecture seule)
      │
      ▼
chaîne d'absorption locale ── inventaire, empreinte, texte, classement, complétude
      │
      ▼
registres et coffre SQLite ── reconstruits depuis les pièces, jamais saisis à la main
      │
      ▼
interface locale ── pages servies sur 127.0.0.1, avec un jeton de session
```

## Le dépôt

| Dossier | Contenu |
|---|---|
| `server/src/coproscope/` | le produit : CLI `coprocs`, modules métier, extracteurs, interface web |
| `server/tests/` | la suite de tests, sur des données fictives uniquement |
| `tools/` | outillage : lanceur de la suite, contrôle avant push, générateur de la démo |
| `clients/extension-navigateur/` | l'[observateur d'extranet](fonction-observateur-extranet.md) |
| `examples/synthetic_copro/` | une instance fictive pour les tests |
| `docs/` | les notes publiques, le registre de feuille de route et les documents de travail |

## Une instance par copropriété

Chaque copropriété vit dans un **dossier d'instance** en dehors du dépôt : ses
pièces, ses registres, son coffre. Supprimer ce dossier ne touche pas au code ;
le reconstruire depuis les pièces redonne le même état.

## Quelques règles de conception

- **Un magasin unique pour la gouvernance** : résolutions, seuils, délégations et
  liens entre objets s'écrivent dans le coffre SQLite local, pas dans un nouveau
  tableur.
- **Une donnée saisie par un humain ne se range pas avec une donnée calculée** :
  une nouvelle extraction remplace ce qu'elle a produit, jamais une correction
  humaine.
- **Un extracteur se conçoit sur des axes**, pas sur les valeurs vues chez un seul
  syndic : quand un troisième cabinet arrive, le code doit se dégrader proprement
  au lieu de répondre faux en silence.
- **Aucun fichier de code ne dépasse 600 lignes**, et une garde le vérifie.

## Pour aller plus loin

- [Architecture et flux](../architecture_et_flux.md)
- [Frontière entre noyau et instance](../documentation_noyau_vs_instance.md)
- [Format du coffre](../vault_format.md)
- [Objets métier et événements](../objets_metier_evenements_v1.md)

## Notes liées

- [Carte des notes](carte.md)
- [Développer](developper.md)
- [Le droit, jusque dans le code](ancrage-reglementaire.md)
- [Confidentialité](confidentialite.md)
