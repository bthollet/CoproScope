# Documentation Developpeurs

Cette section regroupe les informations pour installer, tester, contribuer et
publier prudemment CoproScope.

La documentation grand public est separee: voir
[docs/public](../public/README.md).

## Demarrer

Pour installer le serveur local, lire:

- [server/README](../../server/README.md)

Le serveur contient:

- la CLI `coprocs`;
- l'interface locale;
- les modules metier;
- les tests;
- les configurations par defaut.

## Commandes Utiles

Depuis la racine du depot:

```powershell
.\tools\agent-check.cmd
```

Depuis `server/`, pour toute la suite:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Avant publication ou export public:

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli share-audit --repo-root . --config .\server\src\coproscope\configs\github_sharing.default.yml
```

## Architecture Et Contrats

| Besoin | Lire |
|---|---|
| Separation public / prive | [Architecture et flux](../architecture_et_flux.md) |
| Frontiere noyau / instance | [Documentation noyau vs instance](../documentation_noyau_vs_instance.md) |
| Politique de partage GitHub | [Politique de partage GitHub](../github_sharing.md) |
| Evenements metier | [Objets metier et evenements V1](../objets_metier_evenements_v1.md) |
| Vault local | [Format vault](../vault_format.md) |
| Confidentialite | [Confidentialite et biffage](../confidentialite_et_biffage.md) |

## Qualite Et Tests

Les tests publics utilisent `examples/synthetic_copro`.

Ils ne doivent pas dependre:

- d'une instance privee;
- d'un chemin local personnel;
- d'un secret;
- d'un document brut;
- d'un token OAuth;
- d'un export OCR prive.

La CI GitHub lance les tests unitaires et les controles de securite principaux.

## Contribution

Avant de contribuer:

1. travailler sur une tranche coherente;
2. garder les donnees reelles hors Git;
3. ajouter ou mettre a jour les tests;
4. verifier les liens et la documentation;
5. lancer l'audit de partage;
6. expliquer dans la PR ce qui a ete generalise ou expurge.

Le modele de PR demande explicitement:

- ce qui change;
- pourquoi c'est utile;
- si `examples/synthetic_copro` a ete teste;
- si aucune donnee reelle, secret ou chemin prive n'a ete ajoute.

## Documentation Interne Et Agents

Les journaux d'equipes agiles, traces d'orchestration et anciennes roadmaps sont
utiles pour comprendre l'histoire du projet, mais ils ne doivent pas devenir le
parcours principal d'un lecteur public.

Pour travailler avec les agents:

- [Equipe doc agents](../equipe_doc_agents.md)
- [Orchestration agents](../orchestration_agents.md)
- [Protocole roadmap et presence](../protocole_roadmap_presence_agents.md)
- [Archive documentaire](../archive/README.md)
