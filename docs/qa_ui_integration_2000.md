# QA UI integration - livraison test 20h

Audit rapide realise le 2026-05-20 depuis le worktree local
`C:\Users\brice\CoproScope\_worktrees\vault-qa-livraison-2000`, branche
`codex/vault-qa-livraison-2000`.

Scope lu en priorite:
- `server/src/coproscope/web/templates/overview.html`
- `server/src/coproscope/web/templates/actions.html`
- `server/src/coproscope/web/templates/depot.html`
- `server/src/coproscope/web/viewmodel.py`
- `server/src/coproscope/web/app.py`
- `server/src/coproscope/web/depot.py`
- comparaison lecture seule avec `C:\Users\brice\CoproScope\coproscope`

Limite de verification: les tests UI n'ont pas pu etre lances dans ce worktree
car ni le Python global ni `server/.venv` ne fournissent `pytest`
(`python -m pytest ...` => `No module named pytest`, `server/.venv` absent).

## Synthese executive

Pas de P0 confirme dans le worktree audite: les trois templates cibles semblent
coherents avec le viewmodel local et les routes FastAPI existantes. Les risques
principaux avant 20h sont:

- P1: divergence possible avec l'integration UI du repo principal, qui ajoute
  des champs de viewmodel et des sections Jinja non presents dans ce worktree.
- P1: experience novice encore fragile sur le depot, car le parcours ne rend pas
  assez explicite local/vault/sync et les actions lourdes sont toutes cliquables.
- P2: tables et chemins longs peuvent rester difficiles a lire sur petit ecran
  malgre les protections CSS.

## Findings P0

Aucun P0 confirme dans le worktree audite.

Point de controle P0 avant livraison: si les templates du repo principal sont
livres sans le `viewmodel.py` correspondant, `overview.html` depend maintenant
de `model.cockpit_alerts`, `model.evidence_summary` et `model.trust_summary`.
Dans ce cas, la page cockpit peut casser au rendu Jinja. Dans le repo principal
lu en lecture seule, ces champs existent bien dans `build_dashboard_model`, donc
le risque est surtout un risque de merge/deploiement partiel.

## Findings P1

### P1 - Risque de livraison partielle template/viewmodel

Dans le worktree, `overview.html` utilise encore `model.priorities`. Dans le repo
principal, `overview.html` utilise `model.cockpit_alerts`, `model.evidence_summary`
et `model.trust_summary`, ajoutes dans `viewmodel.py`. Toute livraison qui prend
les templates integres sans prendre le viewmodel associe expose une erreur Jinja
ou une page vide au premier chargement du cockpit.

Verification manuelle:
- ouvrir `/` sur la build livree;
- verifier HTTP 200 et absence de traceback;
- verifier que les blocs "Alertes cockpit", "Decisions, actions, preuves" et
  "Confiance, signature, vault" affichent des valeurs coherentes si cette UI est
  bien la version integree.

### P1 - Depot: ambiguuite local / vault / sync

Dans le worktree, `depot.html` presente "Depot & exports" et "pipeline leger auto",
mais n'explique pas encore clairement la difference entre depot local, pack local
exporte, vault chiffre/signe et synchronisation externe. Le repo principal ajoute
des textes de securite utiles, mais ils doivent etre verifies en rendu final.

Risque utilisateur: un novice peut croire que "deposer" synchronise ou publie les
pieces, ou inversement croire que le pack local est deja compatible vault/sync.
C'est critique pour une livraison test centree vault/local/sync.

Verification manuelle:
- ouvrir `/depot`;
- confirmer que le texte dit explicitement: depot local, pas de sync cloud,
  bruts/restricted/secrets exclus des exports UI;
- telecharger `/exports/local.zip` et verifier l'absence de `raw/`, `restricted/`,
  `logs/`, `.env`, mappings de biffage ou chemins prives non attendus.

### P1 - Actions de pipeline non protegees contre double clic / mauvaise attente

Les boutons `DocAI local-heavy`, `DocOps`, `Compta`, `Tout hors DocAI` sont des
POST simples. Le code trace les erreurs dans le manifeste au lieu de les masquer,
ce qui est bon, mais l'UI ne montre pas de duree, d'etat "en cours", ni de garde
contre clics repetes. Pour une demo 15 min, le risque est moins technique que
perceptif: impression de blocage ou doublons d'etapes.

Verification manuelle:
- deposer un petit `.txt`;
- cliquer une seule fois sur chaque pipeline;
- verifier la redirection 303 puis la presence des etapes dans "Etapes";
- eviter DocAI local-heavy pendant la demo sauf backend local pret et annonce.

## Findings P2

### P2 - Debordements visuels possibles dans Actions

`actions.html` affiche jusqu'a 80 lignes avec `title`, `next_step`, `evidence`,
`owner`, `source` et `channel`. Le CSS a `table-layout: fixed`,
`overflow-wrap: anywhere` et `.table-band { overflow: auto; }`, donc le risque
de casse franche est limite. Il reste un risque de lisibilite sur mobile ou avec
des chemins/phrases tres longs.

Verification manuelle:
- tester `/actions`, `/actions?scope=comptes`, `/actions?scope=syndic`;
- inspecter desktop et largeur mobile;
- verifier les colonnes "Action" et "Preuve" avec chemins longs.

### P2 - Filtres Actions: liens incomplets avec token

Dans le worktree, la nav globale porte `ui_token_query`, mais plusieurs liens
internes des templates utilisent `/actions?...`, `/pieces`, `/chantiers` sans
propager le token. Aujourd'hui `/actions` n'appelle pas `_require_token`, donc ce
n'est pas bloquant. Si le controle d'acces est etendu avant 20h a toute l'UI,
ces liens deviendront des 403 ou casseront le parcours.

Verification manuelle:
- lancer avec token;
- ouvrir `/depot?token=...`;
- naviguer via tous les boutons et liens secondaires;
- confirmer que le token reste present pour toutes les routes protegees.

### P2 - Depot: chemins locaux visibles et longs

`depot.html` affiche `selected_deposit.target_dir`, `file.path` et les sorties
`step.after`. Le CSS casse les mots longs, mais l'information peut etre anxiogene
pour un novice et occuper beaucoup d'espace. C'est acceptable pour QA/dev, moins
pour une premiere lecture produit.

Verification manuelle:
- deposer un fichier avec nom long;
- verifier que le bloc "Depot selectionne" reste lisible;
- confirmer qu'aucun chemin absolu prive n'est affiche si la demo est partagee.

### P2 - Statuts Jinja tolerants mais dependants du manifeste

`depot.html` lit `step.after.documents`, `step.after.doc_ids`, `step.error` et
`selected_deposit.steps`. Les manifestes crees par `depot.py` contiennent bien
`before`, `after`, `error`, `status`, `doc_ids`. Le risque apparait surtout si un
ancien manifeste incomplet est present dans `outputs/deposits`.

Verification manuelle:
- supprimer/mettre de cote les manifestes anciens de l'instance de demo;
- ouvrir `/depot` avec aucun depot, puis avec un depot neuf;
- verifier absence de traceback avec un depot selectionne.

## Parcours novice 15 min recommande

1. Ouvrir `/` et expliquer uniquement trois nombres: actions, pieces a demander,
   incidents/decisions suivies.
2. Cliquer "Voir toutes les actions"; filtrer `Comptes`, puis `Syndic`, puis
   revenir a `Tous`.
3. Ouvrir `/documents` ou `/pieces` pour montrer le lien piece -> action -> preuve.
4. Ouvrir `/depot`; deposer un petit fichier texte synthetique.
5. Montrer le manifeste de depot, les etapes locales et le fait que les bruts ne
   sont pas servis par `/raw/_depot_ui/...`.
6. Telecharger le pack local, lister rapidement son contenu, confirmer absence
   de raw/restricted/secrets.
7. Conclure sur vault/sync: "l'UI locale prepare les traces; le statut vault
   chiffre/signe reste a inspecter explicitement avant toute synchro externe."

## Points critiques a inspecter avant 20h

- Rendu HTTP 200 de `/`, `/actions`, `/actions?scope=comptes`,
  `/actions?scope=syndic`, `/depot`, `/exports/actions.csv`,
  `/exports/actions.md`, `/exports/local.zip`.
- Si la version du repo principal est livree: verifier que les nouveaux champs
  `cockpit_alerts`, `evidence_summary`, `trust_summary` sont bien dans le
  viewmodel de la build.
- Verifier le contenu de `/exports/local.zip`: pas de `raw/`, `restricted/`,
  `logs/`, `.git`, `.env`, `table_correspondance`, `redaction_map`, `mapping`.
- Tester un depot neuf avec un fichier court et un nom long.
- Tester largeur mobile: nav horizontale, filtres Actions, tableau Actions,
  tableau Etapes Depot.
- Decider le message demo pour DocAI local-heavy: pret a cliquer ou a montrer
  comme option avancee non lancee.

## Recommandations de test manuel

Commande de test a relancer des que l'environnement Python est pret:

```powershell
cd C:\Users\brice\CoproScope\_worktrees\vault-qa-livraison-2000\server
python -m pytest tests\test_ui_demo.py tests\test_ui_atelier_piece.py -q
```

Checklist navigateur minimale:

- Desktop: 1366x768, puis 1920x1080.
- Mobile: largeur 390 px.
- Routes: `/`, `/actions`, `/actions?scope=comptes`, `/actions?scope=syndic`,
  `/pieces`, `/depot`.
- Interaction: upload `.txt`, pipeline leger auto, export zip.
- Donnees sensibles: verifier visuellement et dans le zip qu'aucune zone raw,
  restricted, private, logs ou mapping de biffage n'est exposee.
