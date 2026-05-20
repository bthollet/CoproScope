# Plan d'implementation CoproScope v1

Ce document ancre le plan d'implementation sur disque afin que le contrat d'execution du produit ne depenne pas de l'historique du chat.

## Resume

- construire CoproScope comme un produit separe, avec un backend local-first dans `server/` ;
- conserver les donnees reelles de copropriete hors du depot produit, via des instances privees ;
- livrer un premier ensemble utile autour de DocOps, du socle SyndicOps, de ComptaScope et d'AGOps.

## Decisions d'architecture

- le code produit, les configurations par defaut, les schemas, les prompts et les templates vivent dans `coproscope/server/` ;
- les instances privees vivent hors du depot produit et exposent leurs chemins via `instance.yml` ;
- une instance pilote privee valide le workflow reel ; `examples/synthetic_copro/` sert d'instance publique de validation ;
- les ameliorations genericisables sont preparees pour le depot public `https://github.com/bthollet/CoproScope` ;
- aucune migration destructive n'est autorisee ; les bruts restent en lecture seule ; les ecritures sont limitees au staging, aux sorties et aux registres.

## Surface de commande v1

- `coprocs doctor`
- `coprocs inventory`
- `coprocs extract-text`
- `coprocs classify`
- `coprocs missing-docs`
- `coprocs kpi`
- `coprocs ag analyze`
- `coprocs due-diligence summarize`
- `coprocs pipeline run`
- `coprocs tools status`
- `coprocs accounting reconstruct`
- `coprocs accounting controls`
- `coprocs grist sync`
- `coprocs evidence build`
- `coprocs workers run`
- `coprocs strategy export`
- `coprocs share-audit`
- `coprocs share-export`

## Perimetre v1

- coeur generique pour copropriete simple, avec points d'extension pour plus tard ;
- configuration des chemins par instance ;
- CLI stable et serveur MCP minimal pour l'automatisation sure ;
- schemas structures, configurations par defaut, prompts, templates et journaux d'ecriture.
- ComptaScope rapproche les factures candidates avec les etats de depenses configures, deduit les alias fournisseurs repetes et explique chaque echec de rapprochement au lieu de le traiter comme une anomalie certaine.
- Les rapprochements ComptaScope doivent etre classes en `OK`, `P2` ou `P1`: similarites de noms, divisions egales, sommes multi-lignes et regroupements de factures sont des candidats `P2` a confirmer, tandis que `NON_RAPPROCHE` reste reserve aux cas sans indice local suffisant.
- Toute levee ou requalification de rapprochement doit produire le rapport ComptaScope dans la meme passe; les exports Grist/Evidence ne doivent jamais copier des tables comptables sans rapport explicatif a jour.

## Non-objectifs explicites pour v1

- pas encore d'application web ;
- pas de SaaS ni de serveur multi-tenant ;
- pas de pile RAG obligatoire ;
- pas encore de moteur natif multi-entites recursif.

## Garde-fous

- pas de secret dans Git ;
- pas de document reel de copropriete dans le depot produit ;
- pas d'ecriture dans les racines brutes ;
- toute ecriture dans les registres et sorties doit etre journalisee.
