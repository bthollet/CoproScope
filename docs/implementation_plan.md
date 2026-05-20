# Plan d'implementation CoproScope v1

Ce document ancre le contrat d'execution du produit. La priorisation produit detaillee vit dans la [Feuille de route](./feuille_de_route.md).

## Resume

- construire CoproScope comme un produit separe ;
- conserver les donnees reelles de copropriete hors depot public ;
- livrer d'abord un backend local-first, des registres, des controles et des sorties ;
- rendre ensuite ces objets accessibles par un cockpit conseil syndical.

## Decisions d'architecture

- Le code produit, les configurations par defaut, les schemas, les prompts et les templates vivent dans `server/`.
- Les instances privees vivent hors depot produit et exposent leurs chemins via `instance.yml`.
- Une instance synthetique publique sert de validation et de demonstration.
- Aucune migration destructive n'est autorisee.
- Les bruts restent en lecture seule.
- Les ecritures sont limitees au staging, registres, sorties, rapports, privacy et biffages.
- Les ameliorations genericisables peuvent remonter vers le depot public apres controle.

## Surface de commande v1

- `coprocs doctor`
- `coprocs inventory`
- `coprocs extract-text`
- `coprocs classify`
- `coprocs missing-docs`
- `coprocs kpi`
- `coprocs privacy screen-existing`
- `coprocs privacy redaction-queue`
- `coprocs privacy redact`
- `coprocs privacy redact-required`
- `coprocs ag analyze`
- `coprocs due-diligence summarize`
- `coprocs pipeline run`
- `coprocs tools status`
- `coprocs invoices extract`
- `coprocs accounting reconstruct`
- `coprocs accounting controls`
- `coprocs grist sync`
- `coprocs evidence build`
- `coprocs workers run`
- `coprocs ui serve`
- `coprocs demo build`
- `coprocs strategy export`
- `coprocs share-audit`
- `coprocs share-export`

Alias francais importants :

- `coprocs confidentialite scanner-existant`
- `coprocs confidentialite file-biffage`
- `coprocs confidentialite biffer`
- `coprocs confidentialite biffer-requis`
- `coprocs factures extraire`
- `coprocs compta reconstituer`
- `coprocs compta controles`
- `coprocs interface servir`
- `coprocs demonstration construire`

## Perimetre v1

- Coeur generique pour copropriete simple, avec points d'extension.
- Configuration des chemins par instance.
- CLI stable et serveur MCP minimal.
- Schemas structures, configurations par defaut, prompts, templates et journaux.
- DocOps produit le registre documentaire et la completude.
- PrivacyOps enrichit les documents avec une politique d'acces.
- BiffageOps construit la file de biffage et produit des versions biffees quand possible.
- FactureOps produit les factures candidates et anomalies facture.
- ComptaScope consomme FactureOps, rapproche les etats de depenses configures et explique chaque echec.
- AGOps produit un premier registre AG.
- Audit360 expose des formes generiques de controle.
- GristOps/EvidenceOps produisent des sorties locales.

## Non-objectifs explicites v1

- Pas encore d'application web complete multi-parcours ; une interface locale v0 est autorisee pour rendre visibles les objets metier et les chantiers.
- Pas de SaaS multi-tenant.
- Pas de pile RAG obligatoire.
- Pas de vote electronique complet.
- Pas de moteur natif multi-entites complet.
- Pas de publication de donnees reelles.

## Garde-fous

- Pas de secret dans Git.
- Pas de document reel dans le depot produit.
- Pas de carte de pseudonymisation dans le depot public.
- Pas d'ecriture dans les racines brutes.
- Pas de table comptable exportee sans rapport explicatif.
- Pas de sortie diffusable sans controle confidentialite.
- Pas de publication d'une copro seulement pseudonymisee : la demo partageable doit etre fictive ou suffisamment transformee.

## Execution multi-agents

Les prochains sprints peuvent etre executes par plusieurs agents en parallele, mais uniquement avec des worktrees et des perimetres de fichiers explicites.

Document de reference : [Orchestration multi-agents](./orchestration_agents.md).

Regles minimales :

- un agent = une branche `codex/<sprint>-<scope>` = un worktree dedie ;
- un agent ne modifie que les fichiers dont il a l'ownership ;
- `viewmodel.py`, `cli.py`, les schemas partages et les README de synthese ont un seul owner a la fois ;
- les agents UI utilisent des ports differents ;
- le coordinateur integre les branches une par une et relance la suite de tests ;
- les instances privees restent hors depot, meme en travail parallele.
