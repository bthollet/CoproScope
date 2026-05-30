# Bandeau contexte coffre / role / sync

## Objectif

Lever le no-go novice en affichant, avant toute action sensible, le contexte que l'utilisateur doit comprendre:

- coffre courant: copro ou instance ouverte;
- role: personne ou mandat suppose pour l'ecran;
- niveau acces: college maximal affiche dans ce contexte;
- etat du coffre signe: absent, a initialiser, pret ou en protection;
- etat sync: non branchee, propre, a surveiller ou en incident;
- derniere verification: date explicite si elle existe, sinon verification a faire;
- prochaine action: consigne courte avant lecture, partage ou publication.

## Perimetre livre

Le code est volontairement isole dans `server/src/coproscope/web/context_banner.py` et le partial Jinja `server/src/coproscope/web/templates/_context_banner.html`.

Il n'est pas branche dans `base.html`. Contrat de ce lot: pas branche dans base.html, pour laisser l'integration finale a un lot separe et eviter une collision avec les routes et templates en cours.

## Contrat d'integration

Construire le modele cote route ou viewmodel:

```python
from coproscope.web.context_banner import build_context_banner

context_banner = build_context_banner(instance, role_hint="conseil_syndical")
```

Puis inclure le partial dans le template choisi:

```jinja
{% include "_context_banner.html" %}
```

Le partial attend uniquement une variable `context_banner`. S'il n'y en a pas, il ne rend rien.

## Langage novice

Le bandeau doit dire "vous etes dans ce coffre" avant d'afficher les details techniques. Les libelles evitent les abreviations seules: `conseil syndical`, `coproprietaires`, `sync a surveiller`, `coffre signe a initialiser`.

La prochaine action doit rester concrete:

- declarer le cache local et le dossier sync;
- preparer le coffre signe;
- suspendre le partage en cas de risque;
- confirmer le role;
- verifier la sync;
- continuer vers les actions et les preuves.

## Risques restants

Le modele lit les reglages deja disponibles mais ne modifie aucune route. Il ne remplace pas encore une vraie selection multi-coffres, une authentification de role, ni une verification cryptographique complete lancee par l'utilisateur. Ces raccordements devront rester explicites et visibles.
