# Audit cybersecurite IA et injection de code

Date: 2026-05-25.
Chantier: `CH-20260525-234417-RM-2026-0039-audit-cyber-ia-injection`.
Conversation: `CONV-2026-1783`.
Perimetre: repo produit local, sans instance privee, serveur live, document brut,
OCR brut, export brut, secret ou push GitHub.

## Synthese

CoproScope reste local-first sur les surfaces auditees. Les usages IA declares
sont des enrichissements locaux, optionnels, ou des notes de revue qui ne
valident pas seules une decision comptable, juridique ou de diffusion.

Le risque principal n'est pas une execution arbitraire deja visible dans les
routes utilisateur. Le risque principal est l'ajout futur d'un `eval`, `exec`,
`compile`, `subprocess` ou appel shell non relu, ou l'oubli de traiter une
preuve/piece comme donnee non fiable dans un prompt de generation.

Mesure ajoutee: `server/tests/test_security_code_injection_guards.py` inventorie
les exceptions actuelles et bloque toute nouvelle execution dynamique non
listee, tout `shell=True`, tout `eval`, et tout appel shell direct.

## Methode

Controles realises:

- scan statique des appels `exec`, `eval`, `compile`, `subprocess`, `os.system`
  et `shell=True` dans `server/src`, `server/tests` et `tools`;
- lecture des chargeurs de fragments internes;
- lecture des surfaces IA/document: `docai.py`, generation d'extracteur facture,
  revue visuelle facture et ajout de document;
- controle des routes et exports par les tests securite existants, sans serveur;
- ajout d'un garde-fou automatisable.

Limites:

- pas de scan reseau, pas de serveur live, pas de test sur instance privee;
- pas d'execution de modele IA local lourd;
- pas d'audit dependances complet type SCA dans ce lot court.

## Constats

### Execution dynamique Python

Constat: les `exec(compile(...))` visibles servent au decoupage interne de gros
modules en fragments suivis dans le repo. Les sources compilees viennent de
fichiers locaux du codebase, pas d'une entree utilisateur.

Risque: cette technique est puissante. Si elle est copiee dans une route ou sur
un contenu importe, elle deviendrait une injection de code.

Regle: `exec`, `compile` et tout chargeur de fragments doivent rester sur une
liste explicite. Aucun `eval` n'est autorise.

### Subprocess et commandes systeme

Constat: les appels `subprocess.run` actuels sont limites a trois familles:
inspection d'outils locaux, commandes Git locales d'instance, et superviseur
d'orchestration Codex.

Risque: un appel shell expose depuis une route ou avec `shell=True` permettrait
une commande arbitraire ou une fuite de chemin/secret.

Regle: pas de `shell=True`, pas de `os.system`, pas de `os.popen`, pas de
subprocess dans les routes web. Toute nouvelle commande externe doit avoir une
raison, un argv explicite, un perimetre de fichier et un test.

### Usages IA et prompts

Constat: les surfaces IA reperees sont:

- `DocAI`: OCR local, Docling local, hooks layout locaux, Qwen VL local-heavy et
  bloque par politique quand la piece exige un derive anonymise;
- generation d'extracteurs facture: le prompt traite fournisseur et preuve comme
  donnees non fiables, interdit code dynamique, imports, reseau, ecriture disque
  et secrets;
- revue visuelle facture: le niveau L4 IA/vision externe exige confirmation
  explicite et ne vaut jamais validation comptable finale;
- UI ajout document: le brut cloud est bloque et le texte est presente comme
  reconnu localement, sans IA/cloud externe.

Risque: prompt injection par preuve de facture ou piece importee, surtout si une
sortie de modele etait appliquee comme code ou decision finale.

Regle: toute preuve, piece, OCR, nom fournisseur ou note externe est une donnee
non fiable. Un modele peut proposer une piste; il ne peut pas executer du code,
decider seul une diffusion, valider une comptabilite ou lever un garde-fou de
confidentialite.

## Doctrine IA CoproScope

Autorise:

- extraction locale deterministe;
- OCR local ou sidecar;
- structure locale type Docling/layout;
- revue IA locale en mode explicite, evidence-only, avec derive anonymise si
  la politique privacy l'exige;
- prompts qui bornent les donnees comme non fiables et interdisent code,
  reseau, secrets et ecriture disque.

Interdit sans arbitrage explicite:

- envoyer un brut, OCR brut, chemin local, secret ou piece privee vers un cloud;
- appliquer une sortie IA comme code executable;
- utiliser IA/vision externe comme validation comptable, juridique ou de
  diffusion finale;
- ajouter `eval`, `exec`, `compile`, subprocess ou shell hors liste de revue;
- exposer une commande systeme depuis une route web.

## Garde-fou integre

Le test `test_security_code_injection_guards` verifie:

- absence de `eval`;
- aucun nouvel `exec` ou `compile` hors chargeurs listes;
- aucun `shell=True`;
- aucun `os.system` ou `os.popen`;
- aucun `subprocess.*` hors fichiers d'outillage listes;
- pas de `subprocess` dans `server/src/coproscope/web`;
- le prompt de generation d'extracteur rappelle que les preuves sont non
  fiables et interdit code dynamique, reseau, ecriture disque et secrets;
- les surfaces DocAI/generation ne declarent pas de client cloud LLM direct.

## Suite conseillee

1. Garder ce test dans le panier securite de chaque integration.
2. Refuser toute nouvelle exception dynamique sans note dans ce document ou dans
   une doctrine qui le remplace.
3. Si un vrai connecteur IA cloud est un jour demande, ouvrir un `RM-*` dedie
   avec privacy review, minimisation, derive anonymise et opt-in explicite.
4. Ajouter plus tard un audit dependances haute severite (`agent-check -Security`)
   quand le lot n'est plus borne a la nuit autonome.

## Verification

Resultat final 2026-05-25 23:54 +02:00:

- `tests.test_security_code_injection_guards`: 7 OK.
- Panier `tests.test_security_code_injection_guards`,
  `tests.test_invoice_extractors`, `tests.test_ui_security_routes`,
  `tests.test_security_no_private_sync_leaks`: 29 OK.
- `python ..\tools\check_code_line_limit.py`: OK.
- `git diff --check`: OK, avec warnings CRLF deja presents dans le worktree.
- `tools\agent-check.cmd -Security`: OK; 19 tests rapides OK, Bandit haute
  severite sans echec, `pip-audit` sans vulnerabilite connue.

## Trace finale

BOT-END - Coordinateur audit cybersecurite + garde-fous IA/injection -
2026-05-25 23:54 +02:00.

Statut: `INTEGRE`.
Fichiers modifies: cette note, `server/tests/test_security_code_injection_guards.py`,
`server/src/coproscope/extractors/invoices/generator.py`,
`docs/presence_agents.md`, `docs/roadmap_backlog_central.md`.
Fichiers evites: instances privees, documents bruts, OCR/logs, exports bruts,
secrets, routes UI, serveurs locaux, scans/kills, push GitHub, `RM-2026-0017`,
`ORD-P0-990`.
Limites: audit statique court, sans pentest reseau ni execution de modele IA
local lourd.
