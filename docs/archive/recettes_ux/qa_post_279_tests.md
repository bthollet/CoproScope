# QA post 279 - anti-fuite jargon novice

Objectif: empecher une regression de vocabulaire sur les surfaces novices. Le
texte visible utilisateur doit dire `coffre`, pas `vault`.

## Couverture statique ajoutee

Le test `server/tests/test_ui_no_jargon_primary.py` couvre volontairement un
perimetre court:

- template `/gouvernance`: `server/src/coproscope/web/templates/governance.html`;
- partial de bandeau contexte: `server/src/coproscope/web/templates/_context_banner.html`;
- chaines Python qui alimentent ces deux surfaces:
  `server/src/coproscope/web/governance.py` et
  `server/src/coproscope/web/context_banner.py`.

Il extrait le texte visible des templates, y compris les attributs
`aria-label`, `title`, `alt` et `placeholder`, puis cherche `vault` comme mot
anglais isole. Les expressions Jinja et les noms de variables sont exclus pour
ne pas confondre contrat UI et implementation.

## Regle de langage

Texte visible utilisateur: dire `coffre`, `coffre signe`, `coffre courant` ou
`coffre de donnees` selon le contexte. Eviter `vault` dans les titres, badges,
micro-textes, aides, libelles accessibles et messages de premier niveau.

## Exceptions acceptees

Les occurrences suivantes restent techniques et ne sont pas des fuites UI:

- config technique `settings.vault` et cle YAML `vault`;
- noms de modules, imports, fonctions, variables et champs internes lies au
  package `coproscope.vault`;
- identifiants de test `vault-*`, fixtures et chemins synthetiques;
- permissions techniques `vault.read.*` et codes de plugins;
- docs techniques comme `docs/vault_format.md`,
  `docs/transition_vault_collaboratif.md` ou notes d'architecture internes.

La couverture peut etre elargie aux autres pages principales apres migration
complete de leur vocabulaire novice.
