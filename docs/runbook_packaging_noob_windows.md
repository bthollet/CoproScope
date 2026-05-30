# Runbook packaging noob Windows

Roadmap: `RM-2026-0014` / chantier `CH-2026-0014`.

Objectif: livrer CoproScope comme application Windows installable par une
personne non technique. Le premier lancement doit ouvrir l'interface locale dans
une fenetre CoproScope dediee sans terminal visible, puis ne partager via Google
Drive que la surface deja chiffree du coffre.

Ce document cadre le packaging. Il ne demande pas de modification systeme
destructive: pas d'installation admin obligatoire, pas d'ecriture dans
`Program Files`, pas de service Windows, pas de tache planifiee, pas de
modification globale du `PATH`.

## Decision V1

- Build applicatif: PyInstaller `--onedir`, pas `--onefile` pour la premiere
  livraison novice. Le dossier est plus gros, mais le demarrage est plus rapide,
  les faux positifs antivirus sont plus faciles a diagnostiquer et les fichiers
  embarques restent inspectables.
- Installateur: installation par utilisateur sous
  `%LOCALAPPDATA%\Programs\CoproScope`. Un wrapper Inno Setup ou equivalent peut
  etre ajoute ensuite, mais il doit rester per-user et sans elevation.
- Raccourci: creation d'un raccourci `CoproScope` dans le menu Demarrer de
  l'utilisateur courant:
  `%APPDATA%\Microsoft\Windows\Start Menu\Programs\CoproScope\CoproScope.lnk`.
- Lancement: `CoproScope.exe` est un lanceur fenetre cachee. Il prepare le profil
  utilisateur, demarre l'UI locale sur `127.0.0.1`, ouvre une fenetre CoproScope
  via pywebview et garde les logs dans le profil utilisateur. Le mode navigateur
  reste disponible en secours avec `--browser`.
- Changement de coffre: dans la fenetre desktop, le bouton `Changer de coffre`
  ouvre le selecteur de dossiers Windows. Le dossier choisi doit contenir
  `instance.yml`; l'app le memorise localement, puis redemarre sur ce coffre
  avec un nouveau port et un nouveau jeton de session.
- Drive: l'app utilise l'API Google Drive avec bouton OAuth. Drive Desktop reste
  un transport tolere plus tard, pas le chemin noob V1.
- Upload Drive: un upload Drive ne peut lire que le dossier de sync chiffre
  valide par le gate anti-fuite. Aucun document brut, cache dechiffre, log, base
  SQLite locale ou chemin prive ne doit etre envoye.

## Emplacements utilisateur

Les chemins suivants sont la cible produit. Ils evitent les dossiers cloud
automatiques et separent les donnees claires locales de la surface partageable
chiffree.

| Usage | Chemin cible | Regle |
|---|---|---|
| Programme installe | `%LOCALAPPDATA%\Programs\CoproScope` | Ecrasable par mise a jour, aucune donnee utilisateur. |
| Profil app | `%APPDATA%\CoproScope\config\profile.json` | Parametres non secrets, pas dans Git, pas dans Drive. |
| OAuth token | `%APPDATA%\CoproScope\oauth\token.json` | Secret utilisateur local, jamais exporte, jamais loggue. |
| Client OAuth production | embarque par l'app ou pose par installateur sous `%APPDATA%\CoproScope\oauth\client_secret_prod.json` | Jamais demande a l'utilisateur final; le JSON dev reste hors Git. |
| Coffres locaux | `%LOCALAPPDATA%\CoproScope\coffres\<coffre_id>\local` | Etat de travail local, peut contenir des index/caches clairs controles. |
| Surface sync chiffree | `%LOCALAPPDATA%\CoproScope\coffres\<coffre_id>\sync_chiffre` | Seule source autorisee pour Drive apres verification. |
| Logs | `%LOCALAPPDATA%\CoproScope\logs` | Logs sanitises, sans token, sans contenu clair, sans chemins Drive prives. |
| Exports explicites | `%USERPROFILE%\CoproScope\exports` | Choix utilisateur; jamais synchronise automatiquement. |

Interdits pour les donnees de profil et de coffre: `Google Drive`, `OneDrive`,
`Dropbox`, depot Git, `.venv`, dossier temporaire partage, bureau synchronise.

## Lanceur Windows cible

Le lanceur PyInstaller ne doit pas exposer la CLI brute. Son contrat:

1. creer les dossiers de profil si absents;
2. refuser de demarrer si le profil ou le coffre pointe vers un dossier cloud
   detecte comme Drive/OneDrive/Dropbox;
3. choisir un port local disponible, en priorite `8765`;
4. generer un token de session local non persistant;
5. demarrer l'UI sur `127.0.0.1`;
6. ouvrir le navigateur officiel sur
   `http://127.0.0.1:<port>/?token=<token>`;
7. si une instance tourne deja, rouvrir l'URL existante au lieu de lancer un
   second serveur;
8. afficher une petite erreur Windows lisible si le serveur ne demarre pas;
9. ecrire un journal local sanitise.

L'utilisateur ne doit jamais voir `uvicorn`, `FastAPI`, `Python`, `pip`,
`OAuth scope`, `client_secret`, `token.json`, `vault`, `sync-root` ou une pile
d'erreur Python pendant le premier parcours.

## Commandes de build cible

Ces commandes sont a lancer depuis `C:\Users\brice\CoproScope\coproscope\server`
sur une machine de build. Elles sont non destructives et creent un environnement
dedie au packaging.

```powershell
py -3.11 -m venv .venv-packaging
.\.venv-packaging\Scripts\python.exe -m pip install --upgrade pip wheel
.\.venv-packaging\Scripts\python.exe -m pip install --upgrade pyinstaller
.\.venv-packaging\Scripts\python.exe -m pip install ".[ui,drive,executable]"
```

Commande PyInstaller cible, apres ajout du lanceur
`packaging\windows\coproscope_launcher.py`:

```powershell
.\.venv-packaging\Scripts\pyinstaller.exe `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --name CoproScope `
  --collect-all coproscope `
  ..\packaging\windows\coproscope_launcher.py
```

Sortie attendue:

```text
server\dist\CoproScope\CoproScope.exe
```

La livraison novice ne doit pas embarquer:

- instances reelles;
- fichiers `client_secret_dev.json`, `credentials.json`, `token.json`;
- `.git`, `.venv`, `.venv-packaging`;
- exports temporaires;
- caches OCR ou blobs dechiffres;
- logs de developpement;
- chemins absolus prives.

## POC executable du 2026-05-31

Le POC versionne ajoute:

- `coproscope.executable_app`: un lanceur noob qui ouvre l'UI locale sur
  `127.0.0.1` avec un jeton de session;
- pywebview: mode par defaut en fenetre CoproScope dediee;
- un switcher desktop `Changer de coffre`: selection de dossier local,
  validation `instance.yml`, memorisation locale et relance isolee;
- `server/packaging/windows/coproscope_launcher.py`: point d'entree PyInstaller;
- `server/packaging/windows/CoproScope.spec`: build `--onedir` qui embarque le
  paquet CoproScope et l'instance synthetique partageable;
- `server/packaging/windows/build-executable.ps1`: commande de build locale;
- `server/packaging/windows/smoke-executable.ps1`: recette standard de l'exe.

Commande de build recommandee depuis `server/`:

```powershell
.\packaging\windows\build-executable.ps1 -InstallBuildDeps
```

Si l'ancien dossier `server\dist\CoproScope` est verrouille par Windows, utiliser
un dossier de sortie frais sous `dist`:

```powershell
.\packaging\windows\build-executable.ps1 -DistPath .\dist\pywebview-20260531
```

Commande de recette standard depuis `server/`:

```powershell
.\packaging\windows\smoke-executable.ps1 -Mode http
.\packaging\windows\smoke-executable.ps1 -Mode window
```

Cette recette doit devenir le reflexe pour les lots desktop/installable: elle
lance l'executable, verifie l'UI locale, puis ferme seulement le processus
qu'elle a cree. Le serveur PowerShell visible reste utile pour developper une
route web, mais ne suffit pas comme preuve finale d'un executable.

## Raccourci menu Demarrer

Prototype per-user apres build, sans installateur:

```powershell
$InstallRoot = "$env:LOCALAPPDATA\Programs\CoproScope"
$StartMenu = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\CoproScope"

New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
New-Item -ItemType Directory -Force -Path $StartMenu | Out-Null
Copy-Item -Path ".\dist\CoproScope\*" -Destination $InstallRoot -Recurse -Force

$ShortcutPath = Join-Path $StartMenu "CoproScope.lnk"
$Shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $InstallRoot "CoproScope.exe"
$Shortcut.WorkingDirectory = $InstallRoot
$Shortcut.Description = "Ouvrir CoproScope"
$Shortcut.Save()
```

Le prototype ne supprime rien. Pour une vraie livraison, l'installateur doit
ecrire ces memes emplacements et proposer une desinstallation qui retire le
programme et le raccourci, mais conserve les coffres utilisateur sauf demande
explicite.

## Smoke test packaging

Avant tout test novice:

1. installer dans un profil Windows standard sans droits admin;
2. verifier que Python n'est pas necessaire dans le `PATH`;
3. lancer `CoproScope` depuis le menu Demarrer;
4. confirmer qu'aucune fenetre terminal ne reste ouverte;
5. confirmer que la fenetre CoproScope ouvre l'UI locale;
6. cliquer `Changer de coffre`, choisir un dossier de test contenant
   `instance.yml`, puis verifier que CoproScope redemarre sur ce coffre;
7. refaire le meme essai avec un dossier sans `instance.yml` et verifier que
   l'app refuse lisiblement sans creer de coffre implicite;
8. fermer puis relancer depuis le menu Demarrer;
9. verifier que le second lancement reutilise l'instance ou redemarre proprement;
10. inspecter `%LOCALAPPDATA%\CoproScope\logs` et confirmer absence de token,
   contenu clair, chemin Drive prive et secret OAuth;
11. inspecter `%LOCALAPPDATA%\CoproScope\coffres` et confirmer que la surface
   `sync_chiffre` ne contient aucun fichier brut.

## Test novice obligatoire

Profil test: personne qui sait installer une application Windows mais ne sait
pas utiliser un terminal.

Scenario:

1. telecharger l'installateur ou le dossier livre;
2. installer sans option avancee;
3. ouvrir CoproScope depuis le menu Demarrer;
4. creer un coffre de test;
5. cliquer sur `Connecter Google Drive`;
6. choisir son compte Google dans le navigateur;
7. voir `Drive connecte - coffre chiffre synchronise`;
8. partager ou copier le lien propose par l'app;
9. fermer puis rouvrir CoproScope.

Criteres de reussite:

- aucune commande n'est tapee par le testeur;
- aucun JSON OAuth n'est demande;
- aucun jargon technique n'est necessaire pour finir le parcours;
- le menu Demarrer suffit pour relancer l'app;
- l'UI s'ouvre en moins de 20 secondes au premier lancement;
- Drive ne contient que des fichiers chiffres, manifests non sensibles et
  metadonnees autorisees;
- l'utilisateur comprend l'etat courant: non connecte, connexion en cours,
  connecte, action requise ou hors ligne;
- une erreur reseau ou un refus OAuth affiche une phrase actionnable, pas une
  traceback.

No-go immediat:

- terminal visible ou instruction `pip/python`;
- demande de `credentials.json` a l'utilisateur final;
- upload d'un PDF, CSV, SQLite, log, OCR clair, cache dechiffre ou chemin local;
- dossier de coffre cree dans Google Drive/OneDrive/Dropbox;
- token OAuth ou secret dans les logs;
- raccourci Start Menu absent apres installation;
- desinstallation qui supprime les coffres sans confirmation explicite.

## Definition de fini

La livraison packaging est candidate seulement quand ces preuves existent:

- artefact PyInstaller `--onedir` reproductible;
- raccourci Start Menu per-user teste;
- lanceur windowed qui ouvre l'UI locale sans terminal;
- profil et coffres dans les emplacements ci-dessus;
- gate anti-fuite execute avant upload Drive;
- smoke OAuth Drive avec fichier chiffre fictif;
- test novice filme ou observe avec resultats notes;
- audit manuel du dossier Drive montrant l'absence de donnees claires;
- procedure de desinstallation non destructive documentee.
