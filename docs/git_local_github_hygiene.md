# Hygiene Git local et GitHub

Date: 2026-05-22.

## Etat constate

- Le depot Git reel est `C:\Users\brice\CoproScope\coproscope`.
- Le dossier parent `C:\Users\brice\CoproScope` est une instance privee candidate a un depot Git local.
- La branche active est `codex/integration-livraisons`.
- L'upstream est `origin/codex/integration-livraisons`.
- `origin` pointe vers `https://github.com/bthollet/CoproScope.git`.
- GitHub CLI est authentifie sur le compte `bthollet`.
- Le working tree contient beaucoup de modifications et de fichiers non suivis: ne pas pousser automatiquement sans tri.

## Regle d'or

Il y a deux familles de depots, avec deux politiques differentes:

- `coproscope`: depot noyau public, seul depot relie a GitHub;
- instances: depots Git locaux, sans remote GitHub, sans publication automatique.

Le lien local/GitHub du noyau doit rester serre mais prudent:

1. on synchronise les refs distantes au debut;
2. on garde des commits petits, publics et relisibles;
3. on tire depuis GitHub uniquement en fast-forward;
4. on pousse uniquement une branche propre et rattachee a son upstream;
5. on ouvre une PR quand le changement doit etre relu ou integre;
6. on ne publie jamais de donnees reelles, secrets, chemins prives ou exports bruts.

Une instance peut et doit avoir son propre `.git` local pour historiser son
travail. Cette racine d'instance ne doit pas avoir de remote GitHub. Si une
instance a besoin d'etre transportee entre machines, on utilise le vault/sync
chiffre ou une sauvegarde controlee, pas un depot GitHub.

## Instances en Git local

Initialiser ou verifier une instance:

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli instance git-init --instance-root C:\Users\brice\CoproScope
.\server\.venv\Scripts\python.exe -m coproscope.cli instance git-status --instance-root C:\Users\brice\CoproScope
```

La commande `git-init`:

- cree un `.git` dans la racine d'instance si necessaire;
- ajoute des exclusions pour secrets, caches, environnements virtuels et checkout `coproscope/`;
- configure `pull.ff=only` et `push.default=nothing`;
- echoue si elle detecte une remote GitHub dans le depot d'instance.

Le diagnostic `doctor` applique la meme doctrine:

- une instance de travail sans Git local est signalee comme `A_INITIALISER`;
- une instance avec remote GitHub est signalee comme `REMOTE_GITHUB_INTERDITE`;
- les fixtures synthetiques et demos publiques restent exemptees pour les tests publics.

La presence de `.git` est normale dans une racine d'instance locale. Elle reste
interdite dans le dossier de synchronisation chiffre, dans Drive/OneDrive brut,
et dans toute archive diffusable.

## Installation locale

Depuis la racine du depot:

```powershell
.\tools\git\install-local-guardrails.cmd
```

Cette commande configure seulement ce depot:

- `fetch.prune=true`;
- `remote.origin.prune=true`;
- `pull.ff=only`;
- `push.default=simple`;
- `rerere.enabled=true`;
- `core.hooksPath=.githooks`.

Le hook `pre-push` rafraichit `origin` et bloque un push si la branche locale est en retard sur son upstream.

## Rituel quotidien

Au debut d'une session:

```powershell
.\tools\git\sync.cmd
```

Si le script indique que la branche est en retard et que le working tree est propre:

```powershell
.\tools\git\sync.cmd -Pull
```

Apres commit, si la branche est propre et en avance:

```powershell
.\tools\git\sync.cmd -Push
```

Le script ne fait ni pull ni push par defaut. Il donne d'abord l'etat local, l'upstream, les commits ahead/behind, le statut GitHub CLI et la presence de modifications locales.

## Avant chaque commit

1. Verifier `git status --short`.
2. Relire `git diff --check`.
3. Stager par paquet coherent: `git add <fichiers>`.
4. Relire ce qui part: `git diff --cached`.
5. Committer avec un message court et explicite.

Ne pas melanger dans le meme commit:

- code applicatif et rapport d'audit prive;
- correction produit et gros lot de captures;
- doc de coordination et secrets locaux;
- fichiers synthetiques publics et instance reelle.

## Avant chaque push

Executer:

```powershell
.\tools\git\sync.cmd
git diff --check
git status --short --branch
```

Puis pousser seulement si:

- la branche suit bien `origin/<branche>`;
- `behind=0`;
- les fichiers non suivis ont ete tries;
- le changement est genericisable et public;
- les tests pertinents sont passes ou la limite est explicite.

## Si le push est bloque

- `behind > 0`: faire `.\tools\git\sync.cmd -Pull` apres avoir committe ou mis de cote les changements locaux.
- Pas d'upstream: utiliser `git push -u origin <branche>` pour le premier push.
- Working tree charge: faire un commit cible, ou separer les fichiers hors perimetre.
- Donnee privee suspecte: retirer du commit, ajouter a `.gitignore` si c'est un artefact local, puis recommencer.

## Cote GitHub

Bonnes pratiques recommandees pour le depot distant:

- garder `main` protegee;
- travailler via branches `codex/<scope>`;
- ouvrir des PR petites et relisibles;
- exiger la CI GitHub Actions avant merge;
- supprimer les branches distantes integrees;
- garder les issues/PR comme trace des decisions qui depassent le local.

Ces reglages GitHub ne sont pas changes automatiquement par les scripts locaux.

## Multi-agents et worktrees

Pour un travail en parallele:

- un agent = une branche = un worktree;
- chaque agent declare son ownership dans `docs/presence_agents.md`;
- le coordinateur integre une branche a la fois;
- chaque branche est synchronisee avec `.\tools\git\sync.cmd` avant integration;
- les fichiers sensibles ne sont jamais modifies par deux writers en meme temps.

## Frontiere public/prive

Relire aussi `docs/github_sharing.md` avant de pousser. GitHub recoit uniquement le code, la documentation publique, les tests, les exemples synthetiques et les outils generiques. Les instances reelles et leurs derives restent hors depot public.
