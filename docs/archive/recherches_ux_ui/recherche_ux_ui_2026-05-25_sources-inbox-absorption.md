# Recherche UX/UI - sources d'absorption et inbox multiples

Date: 2026-05-25
Roadmap: `RM-2026-0003`, appui `RM-2026-0029`
Chantier: `CH-20260525-233914-RM-2026-0003-sources-inbox-absorption`
Conversation: `CONV-2026-1782`

## Mission

Unifier l'experience d'arrivee des informations sur `/documents/ajouter`:
inbox du coffre, dossier local, Drive Desktop local, glisser-deposer, mailbox
future et autres canaux. Le moteur peut prequalifier localement, mais
l'utilisateur confirme toujours avant classement, rattachement, diffusion ou
envoi.

## Benchmark retenu

- Paperless-ngx: consumption directory, upload web, email rules, Inbox/TODO et
  workflows. Retenu: separer absorption, traitement et revue humaine.
- USWDS file input: upload accessible, fallback fichier standard, erreurs
  explicites. Retenu: le drag/drop est une amelioration, pas l'unique chemin.
- Dropbox File Requests: collecte vers une destination sans exposer le reste du
  dossier. Retenu pour futurs canaux externes.
- Google Drive/Gmail scopes: permissions minimales, consentement explicite,
  revocation. Retenu: aucun connecteur cloud/mail implicite en v1.

## Equipe UX/UI

- Orchestrateur UX/UI: hub unique `Absorber des informations` sur
  `/documents/ajouter`.
- Chercheur utilisateur: besoin novice = voir ce qui est arrive, depuis quelle
  source, et quoi confirmer ensuite.
- Architecte UX: file commune `Toutes les sources`, filtres `Inbox du coffre`,
  `Glisser-deposer`, `Dossier local`, `Drive Desktop`, `Mailbox`.
- Designer UI: cartes de sources en premier niveau, puis depot, puis file a
  qualifier document par document.
- Testeur metier expert: mailbox et Drive restent etats futurs/a configurer,
  sans promesse de synchronisation active.
- Testeur accessibilite/novice: upload fichier standard conserve; drag/drop
  global affiche un overlay et renvoie vers la meme file.

## Decisions d'interface

- Le titre produit devient `Absorber des informations`, tout en conservant le
  repere historique `Ajouter des pieces au coffre local`.
- Les cartes de sources n'affichent jamais de chemin local, nom de fichier brut
  sensible, dossier `raw`, `restricted`, `logs`, `private` ou `file://`.
- `Toutes les sources` combine les fichiers uploadees et les lignes inbox du
  registre; les filtres gardent le token local.
- Chaque ligne affiche `Source`, `Proposition locale`, confidentialite,
  diffusion et prochaine action.
- Le drag/drop global poste vers `/depot` avec `return=document_intake` et
  revient sur `/documents/ajouter`.

## Critere de fin

- `/documents/ajouter` montre les sources configurees et l'inbox du coffre.
- Une ligne inbox physique est visible sans fuite de `200_INBOX`, nom brut ou
  chemin local.
- Les sources mailbox/Drive cloud natif ne sont pas actives sans lot connecteur
  separe.
- La prequalification locale reste une proposition, jamais une validation
  automatique.

UXUI-DONE - equipe UX/UI a fini son job
