# Integration export passation derive

## Routes

L'UI locale expose deux exports de consultation, tous deux proteges par le jeton UI existant:

- `GET /exports/passation.json`
- `GET /exports/passation.txt`

Le jeton peut etre fourni comme pour les autres routes locales: parametre `token`, en-tete `x-coproscope-token` ou cookie `coproscope_ui_token` deja pose.

## Contenu

Les routes construisent un document en memoire avec `coproscope.modules.passation_exports`, depuis les objets derives AG/contentieux/passation et les demandes normalisees quand elles existent. Elles ne servent ni fichier source, ni ZIP, ni registre brut.

Watermark obligatoire:

```text
export dérivé, non source collaborative
```

Le JSON conserve `source_of_truth: false` et une structure de cartes derivees: passation, AG, contentieux, preuves, vigilance, demandes, prochaines actions et omissions.

## Refus et non-fuites

Les routes refusent le rendu si le payload final contient un marqueur interdit ou un chemin prive:

- `raw`
- `restricted`
- `logs`
- `file://`
- chemin Windows absolu ou UNC
- chemin utilisateur `/Users/...` ou `/home/...`
- racines relatives `raw/`, `restricted/`, `logs/`, `private/`

Le catch-all `/exports/{export_path:path}` reste actif: les chemins d'export contenant `raw`, `restricted`, `logs` ou `private` retournent `404` et ne lisent pas le disque.

## Limites

Cet export est volontairement derive et non collaboratif. Il sert a relire ou transmettre une synthese de passation; il ne doit pas etre reutilise comme registre de reference pour modifier les objets metier.
