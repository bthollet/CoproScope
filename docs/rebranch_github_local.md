# Rebranch GitHub local

Date de reference : 2026-05-20

Ce runbook explique comment rattacher prudemment le dossier local CoproScope au
depot GitHub `github.com/bthollet/coproscope`, sans ecrire sur Drive, sans
placer `.git` ou `.venv` dans une surface synchronisee, et sans muter les
remotes Git depuis cette procedure.

Precision de perimetre: ce rattachement GitHub concerne uniquement le noyau
`coproscope`. Les instances privees peuvent etre des depots Git locaux, mais
elles ne doivent pas avoir de remote GitHub.

Le principe est simple : on verifie d'abord, on travaille localement sur une
branche `codex/`, puis la publication et la PR restent une etape future.

## Perimetre

Ce runbook couvre uniquement le dossier local de travail :

```powershell
Set-Location C:\Users\brice\CoproScope\coproscope
```

Il ne couvre pas :

- la creation d'un nouveau depot GitHub ;
- la modification d'un remote existant ;
- l'ecriture dans Google Drive, OneDrive ou tout autre dossier synchronise ;
- la synchronisation d'un environnement virtuel, d'un cache ou d'un historique
  Git ;
- la publication immediate d'une branche ou d'une pull request.

Si le dossier local n'est pas deja un clone ou une copie Git coherent avec
`https://github.com/bthollet/coproscope.git`, on stoppe et on demande une
decision humaine. Cette procedure ne corrige pas le remote a la place de
l'operateur.

## Regles de securite

- ne jamais lancer de commande qui modifie `origin` ou un autre remote ;
- ne jamais deplacer le dossier `.git` vers Drive ;
- ne jamais placer `.venv`, `.git`, `__pycache__`, `.pytest_cache`, caches,
  logs ou exports temporaires dans un dossier de sync ;
- ne jamais utiliser Drive comme source de verite du noyau applicatif ;
- ne jamais ecraser des changements locaux non identifies ;
- ne jamais faire de `reset --hard`, checkout destructif ou nettoyage recursif
  sans revue explicite ;
- garder les documents d'instance separes des documents noyau.

Drive peut transporter des exports ou archives explicitement prepares, mais il
ne doit pas recevoir le working tree applicatif brut.

Une racine d'instance peut contenir son propre `.git` local pour historiser le
travail prive. Ce `.git` ne part pas en sync chiffree et n'implique aucune
publication distante.

## Checks non destructifs

Ces commandes lisent l'etat local. Elles ne changent ni branche, ni remote, ni
fichiers suivis.

```powershell
Set-Location C:\Users\brice\CoproScope\coproscope
git status --short
git branch --show-current
git remote -v
git rev-parse --show-toplevel
git rev-parse --is-inside-work-tree
```

Points a verifier :

- `git rev-parse --show-toplevel` pointe vers
  `C:\Users\brice\CoproScope\coproscope` ;
- le dossier parent de la racine Git n'est pas un dossier Drive synchronise ;
- `git status --short` est lu avant toute action pour reperer les changements
  d'autres personnes ;
- le remote affiche `https://github.com/bthollet/coproscope.git` ou
  `git@github.com:bthollet/coproscope.git` ;
- aucun fichier de travail ne depend d'un chemin local prive ou d'un secret.

Verifier aussi l'existence distante sans changer la configuration locale :

```powershell
git ls-remote https://github.com/bthollet/coproscope.git HEAD
```

Si `origin` est absent, pointe ailleurs, ou si `ls-remote` echoue, arreter ici.
La correction du remote est une decision separee, hors de ce runbook.

## Exclusions de sync

Avant toute copie, export ou automatisation, controler que les entrees suivantes
ne sont pas dans une surface synchronisee :

- `.git`
- `.venv`
- `__pycache__`
- `.pytest_cache`
- `.mypy_cache`
- `.ruff_cache`
- `.cache`
- `node_modules`
- `dist`
- `build`
- `*.log`
- `tmp_exports`
- `exports_tmp`
- `decrypted_blobs`
- `blobs_dechiffres`

Check local non destructif :

```powershell
Get-ChildItem -Force -Name .git, .venv, __pycache__, .pytest_cache -ErrorAction SilentlyContinue
```

La presence de `.git` et `.venv` dans le working tree local est normale. Le
probleme est leur presence dans un dossier synchronise ou dans une archive
diffusable.

## Branche locale codex

Quand les checks sont propres et que les changements locaux ont ete compris,
creer ou utiliser une branche locale prefixee `codex/`.

```powershell
git switch -c codex/rebranch-github-local
```

Si la branche existe deja :

```powershell
git switch codex/rebranch-github-local
```

Avant de commit, relire le statut :

```powershell
git status --short
git diff -- docs server/tests
```

Ne pas embarquer de changements inconnus. Les modifications d'autres personnes
restent en place et ne sont ni revert ni nettoyees par ce runbook.

## Remote GitHub attendu

Le depot distant attendu est :

```text
https://github.com/bthollet/coproscope.git
```

Forme SSH equivalente acceptee :

```text
git@github.com:bthollet/coproscope.git
```

Ce runbook autorise seulement la lecture du remote :

```powershell
git remote get-url origin
git remote -v
```

Il interdit de modifier le remote dans cette phase. Si la sortie ne correspond
pas au depot attendu, noter l'ecart et demander une validation humaine avant de
continuer.

## PR future

La pull request est future, apres revue du statut local, tests et validation du
contenu exact a publier.

Etapes futures possibles, hors execution automatique de ce runbook :

```powershell
git status --short
python -m pytest server/tests/test_docs_rebranch_github.py
git log --oneline -5
```

Quand une personne valide la publication, la branche `codex/rebranch-github-local`
pourra etre poussee et une PR brouillon pourra etre ouverte vers le depot
`bthollet/coproscope`. Cette etape ecrit sur GitHub et doit etre annoncee comme
telle avant execution.

## Separation docs instance et noyau

Les documents noyau appartiennent au depot GitHub. Ils decrivent le produit, les
contrats techniques, les tests, les runbooks generiques et les politiques qui ne
dependent pas d'une copropriete precise.

Exemples de documents noyau :

- `docs/rebranch_github_local.md` ;
- documentation de vault, sync, securite et orchestration ;
- tests statiques de documentation ;
- runbooks generiques sans donnees privees.

Les documents d'instance appartiennent a l'espace local ou au coffre de la
copropriete concernee. Ils peuvent contenir des noms, adresses, lots, pieces,
decisions, identifiants internes ou donnees confidentielles. Ils ne doivent pas
etre ajoutes au repo noyau sans anonymisation explicite.

Ces documents d'instance peuvent etre suivis dans le depot Git local de
l'instance. Cette historisation reste locale: pas de remote GitHub, pas de PR,
pas de publication.

Regle pratique :

- si le document explique comment CoproScope fonctionne, il peut etre noyau ;
- si le document raconte une copropriete reelle, il reste document d'instance ;
- si le doute existe, classer instance et demander une revue.

## Criteres d'acceptation

- le runbook mentionne `github.com/bthollet/coproscope` ;
- les checks initiaux sont non destructifs ;
- le remote est lu mais jamais modifie ;
- la branche de travail est prefixee `codex/` ;
- la PR est decrite comme future, pas automatique ;
- Drive n'est pas utilise comme cible d'ecriture du working tree ;
- `.git` et `.venv` sont exclus de toute sync ou archive diffusable ;
- les changements d'autres personnes ne sont jamais revert ;
- la separation documents d'instance et documents noyau est explicite ;
- aucun secret, chemin prive sensible ou donnee de copropriete reelle n'est
  requis pour appliquer la procedure.
