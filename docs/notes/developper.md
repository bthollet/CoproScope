# Développer

## Installer

Python 3.11 ou plus récent. Depuis `server/` :

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[ui,accounting]"      # Linux, macOS
.venv\Scripts\python.exe -m pip install -e ".[ui,accounting]"   # Windows
```

## Lancer l'interface sur la copropriété fictive

Les commandes du [README](../../README.md#installer-et-lancer) fabriquent la
copropriété fictive de la démo dans un dossier voisin du dépôt, la font lire par
la chaîne, puis ouvrent l'interface. L'exemple `examples/synthetic_copro` sert aux
tests : ne pas lancer l'interface directement dessus, elle écrirait dans un
dossier versionné.

## Exécutable Windows

Le lanceur de bureau `coproscope.executable_app` ouvre l'interface dans une
fenêtre dédiée (pywebview) ; `--browser` sert de secours, `--no-browser` de test
sans interface. Depuis `server/` :

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ui,drive,executable]"
.\packaging\windows\build-executable.ps1 -PythonExe .\.venv\Scripts\python.exe
.\packaging\windows\smoke-executable.ps1 -Mode http
```

La couche fenêtre ne porte aucune logique métier : elle ouvre la fenêtre et
encadre le serveur local.

## Jouer les tests

**Une seule commande pour la suite complète**, depuis la racine du dépôt :

```bash
python tools/lancer_la_suite.py
```

Elle nomme les tests collectés mais jamais démarrés et rend un verdict lu dans
`unittest`, pas un code de sortie composé. La CI GitHub l'appelle aussi.

Pour un seul module, depuis `server/` :

```bash
PYTHONPATH=src python -m unittest tests.test_le_module_que_je_touche
```

Les tests n'utilisent que des données fictives. Ils ne doivent dépendre ni d'une
instance privée, ni d'un chemin local, ni d'un secret. Quelques tests portent encore
un chemin du poste de développement : c'est un reste à retirer, pas un modèle.

## Contribuer

1. Une tranche cohérente par proposition, avec ses tests.
2. **Aucune donnée réelle dans Git** : ni pièce, ni nom, ni adresse, ni chemin
   local.
3. Activer le contrôle avant push : `git config core.hooksPath .githooks`.
4. Expliquer dans la demande de fusion ce qui a été généralisé.

Le fondement juridique d'un contrôle suit la règle décrite dans
[Le droit, jusque dans le code](ancrage-reglementaire.md).

## Documents de travail

Le dossier `docs/` contient aussi les documents de travail du projet : cadrages,
vérifications, registres. Ils ne sont pas écrits pour le grand public, et
certains sont datés. Le registre
[`docs/roadmap_backlog_central.md`](../roadmap_backlog_central.md) est la référence
quand deux documents se contredisent.

## Notes liées

- [Carte des notes](carte.md)
- [Architecture](architecture.md)
- [Démo](demo.md)
- [Confidentialité](confidentialite.md)
