# Securite routes et exports - livraison testable 21h15

Date de reference: 2026-05-20 21h15.

## Perimetre traite

- Routes UI et exports FastAPI.
- Token local de session UI.
- Refus de service direct des racines privees.
- Commande `ui open-test` visible au premier plan.

## Regles confirmees

- Sans token configure dans `create_app`, les routes de demo restent ouvertes pour ne pas casser les tests et usages existants.
- Avec token configure, toute route UI non publique exige le token local.
- Le token est accepte via `?token=...`, header `x-coproscope-token` ou cookie HTTP-only local pose apres une requete tokenisee valide.
- `/health` et `/static/*` restent publics: ils ne servent pas les donnees d'instance.
- Les exports `/exports/actions.csv`, `/exports/actions.md` et `/exports/local.zip` sont proteges quand un token est configure.
- Les chemins directs vers `raw`, `restricted`, `logs`, `private`, `.env` et `.git` ne sont pas servis.
- Les exports ad hoc vers des racines ou parties interdites retournent 404.
- Le ZIP local reste limite aux sorties autorisees et exclut bruts, restreints, logs, private, secrets, mappings et tables de correspondance.

## Open-test

`coprocs ui open-test` reste un lancement serveur au premier plan:

- pas d'ouverture automatique de navigateur;
- pas de `Start-Process` cache;
- pas de `taskkill`;
- pas de scan de ports;
- arret attendu avec `Ctrl+C`.

La commande passe toujours par `coproscope.web.app.serve`, qui refuse une ecoute hors loopback sauf option explicite `--unsafe-lan`.

## Verification ajoutee

Tests cibles ajoutes dans `server/tests/test_ui_security_routes.py`:

- protection token des pages UI et exports quand un token est configure;
- propagation locale par cookie apres acces tokenise;
- refus des racines privees et chemins d'exports bruts;
- exclusion des fichiers interdits dans le ZIP local;
- dispatch `ui open-test` vers un serveur foreground sans appel navigateur/process cache.

## Risques restants

- Les templates contiennent encore des liens internes non tokenises; le cookie local compense apres une premiere entree avec token, mais une correction template serait plus lisible.
- La validation manuelle navigateur n'a pas ete faite dans cette passe.
