# Runbook installable Drive chiffre OAuth

Objectif prioritaire: livrer CoproScope comme application installable pour une
personne non-geek. L'utilisateur final ne doit pas ouvrir Google Cloud, creer un
client OAuth, manipuler un fichier JSON, choisir un scope, lancer un terminal ou
comprendre la difference entre vault, sync et API.

Rattachement roadmap: `RM-2026-0014` / `CH-2026-0014`.

Checklist release noob et anti-fuite:
`docs/checklist_installable_drive_chiffre_noob.md`.

## Decision produit

Le partage Drive est un transport de fichiers deja chiffres, pas une source de
verite. CoproScope doit produire localement la surface synchronisable du coffre,
la verifier, puis envoyer uniquement cette surface chiffree dans Drive.

Le parcours utilisateur vise:

1. installer CoproScope;
2. ouvrir l'application depuis le menu Demarrer;
3. cliquer sur `Connecter Google Drive`;
4. choisir son compte Google dans le navigateur officiel;
5. valider l'autorisation;
6. voir `Drive connecte - coffre chiffre synchronise`;
7. copier un lien ou inviter une personne, sans jamais choisir un fichier brut.

Interdits UX:

- pas de console Google Cloud pour l'utilisateur final;
- pas de fichier `credentials.json` demande a l'utilisateur final;
- pas de terminal;
- pas de jargon OAuth/scope/API dans le premier parcours;
- pas de document brut, OCR clair, logs, secrets, cartes de biffage ou blobs
  dechiffres dans Drive.

Frontiere de ce runbook:

- ce document debloque l'identite OAuth developpeur et le smoke technique;
- la checklist noob anti-fuite est la reference pour declarer un installable
  livrable;
- aucun bouton de partage final ne doit etre considere GO tant que la checklist
  n'a pas un verdict explicite `GO`;
- toute incertitude sur la surface envoyee a Drive doit bloquer l'upload.

## Ce que Brice doit faire maintenant

Cette etape debloque le prototype developpeur et l'identite de l'app. Elle ne
doit pas devenir une etape utilisateur final.

1. Ouvrir la console Google Cloud.
2. Creer un projet: `CoproScope Dev`.
3. Activer `Google Drive API`.
4. Configurer l'ecran de consentement:
   - nom app: `CoproScope Dev`;
   - email support: email de Brice;
   - audience: `External` si compte Gmail personnel, `Internal` seulement si
     Google Workspace controle;
   - mode test: ajouter Brice comme test user;
   - scope declare pour le MVP: `https://www.googleapis.com/auth/drive.file`.
5. Creer un client OAuth:
   - type: `Desktop app`;
   - nom: `CoproScope Local Dev`.
6. Telecharger le JSON du client.
7. Le placer hors Git, par exemple:

```text
C:\Users\brice\AppData\Roaming\CoproScope\oauth\client_secret_dev.json
```

8. Ne pas coller le contenu du JSON dans une conversation et ne pas le commit.
   Le depot ignore maintenant `credentials.json`, `client_secret*.json`,
   `token.json`, `**/oauth/*.json`, `**/.oauth/` et `**/.secrets/`.

## Pourquoi ce scope

Pour le MVP, CoproScope doit creer et mettre a jour ses propres fichiers
chiffres. Le scope `drive.file` donne un acces etroit aux fichiers crees ou
ouverts avec l'app. Il evite l'acces large a tout le Drive.

Scopes exclus du MVP:

- `drive`: trop large;
- `drive.readonly`: trop large;
- `drive.metadata` ou `drive.metadata.readonly`: inutile pour le premier partage
  chiffre et plus contraignant;
- Gmail/Calendar/Docs: hors chemin critique installable.

## Ce que CoproScope doit implementer ensuite

Ordre obligatoire:

1. verrou anti-fuite avant tout appel Drive;
2. smoke upload d'un fichier chiffre fictif;
3. assistant premiere ouverture sans jargon;
4. installateur Windows avec demarrage menu Demarrer;
5. test novice et verdict `GO/NO-GO`.

### Prototype developpeur

- commande `coprocs drive auth --client-secrets <path>`:
  - ouvre le navigateur officiel;
  - lance le flux OAuth desktop/local;
  - stocke le token hors Git, dans le profil utilisateur;
  - affiche un message lisible en cas de refus/revocation.
- commande `coprocs drive smoke`:
  - cree un dossier Drive de test `CoproScope Dev`;
  - envoie un petit fichier chiffre fictif;
  - relit ses metadonnees autorisees;
  - supprime ou archive le fichier de test selon option.
- commande disponible maintenant:

```powershell
.\.venv\Scripts\python.exe -m coproscope.cli drive smoke --sync-root <surface_sync_chiffree>
```

  Cette commande prepare le smoke, verifie le gate anti-fuite et n'appelle pas
  encore Drive. Le champ `upload_attempted` doit rester `false`.

### Installable noob

- assistant premiere ouverture:
  - `Creer un coffre`;
  - `Choisir un dossier local`;
  - `Connecter Google Drive`;
  - `Partager le coffre chiffre`.
- etats visibles:
  - `Non connecte`;
  - `Connexion en cours`;
  - `Drive connecte`;
  - `Verification anti-fuite`;
  - `Pret a partager`;
  - `Derniere sync OK`;
  - `Action requise`;
  - `Hors ligne, reprise automatique possible`.
- erreurs en langage humain:
  - `Google a refuse l'autorisation. Reessayez ou changez de compte.`;
  - `Drive est connecte mais le fichier chiffre n'est pas encore envoye.`;
  - `Un fichier non chiffre serait partage: action bloquee.`;
  - `Partage bloque: le coffre chiffre n'est pas verifie.`;
  - `CoproScope verifie que rien de lisible ne part dans Drive.`;
  - `La connexion a expire: reconnectez Google Drive.`

## Gate anti-fuite avant tout upload

Avant d'appeler Drive:

1. verifier que la sortie vient de la surface vault synchronisable;
2. refuser `raw`, `restricted`, `logs`, `private`, `.git`, `.venv`, caches et
   exports temporaires;
3. refuser les fichiers dechiffres;
4. verifier signature/hash si disponible;
5. ecrire un manifeste local lisible: quoi a ete envoye, taille, hash, date,
   jamais le contenu clair;
6. afficher `Pret a partager` seulement apres ce gate.

La surface Drive doit exclure en toutes circonstances:

- documents sources et pieces jointes brutes;
- textes OCR, extractions, rapports et exports clairs;
- exports biffes non rechiffres pour le coffre Drive;
- noms de copropriete, personnes, documents, chemins locaux ou commentaires
  metier dans des fichiers lisibles;
- secrets OAuth, tokens, cles privees, seeds et parts de recuperation en clair;
- logs, caches, fichiers temporaires, `.git`, `.venv`, `node_modules`;
- fichiers dechiffres, blobs dechiffres et indexes lisibles;
- pointeurs ou fichiers instables Drive Desktop: `.gdoc`, `.gsheet`,
  `.gslides`, `.tmp`, `.partial`, copies conflictuelles.

Messages bloquants minimum:

- `Partage bloque: un fichier lisible a ete detecte.`;
- `Partage bloque: le coffre chiffre n'est pas verifie.`;
- `Partage bloque: choisissez d'abord ce que cette personne a le droit de lire.`;
- `Ce dossier contient des fichiers qui ne doivent pas etre partages. Choisissez un autre dossier ou laissez CoproScope en creer un.`

## Decisions bloquantes avant release noob

- Identite OAuth finale: nom public, ecran de consentement, proprietaire,
  statut test/production et verification Google si necessaire.
- Scope Drive: rester sur `drive.file` sauf decision explicite et documentee.
- Mode Drive V1: API Drive via bouton OAuth en parcours principal; Drive
  Desktop seulement comme fallback documente.
- Format de publication: surface vault synchronisable directe ou paquet chiffre
  opaque, mais jamais contenu metier clair dans Drive.
- Nommage distant: noms opaques ou techniques, sans copropriete, personne,
  document, statut ou chemin local.
- Cles et invitations: qui peut dechiffrer quoi, comment revoquer un acces,
  comment recuperer sans stocker de secret clair dans Drive.
- Support: diagnostic expurge par defaut, sans chemins prives, noms de
  documents, tokens ou payloads dechiffres.
- Installateur: demarrage menu Demarrer, stockage profil utilisateur,
  desinstallation sans suppression silencieuse du coffre.

## Criteres GO/NO-GO synthese

GO seulement si:

- une personne non-geek installe, ouvre, cree un coffre, connecte Drive et voit
  `Drive connecte - coffre chiffre synchronise` sans terminal;
- un canari clair place dans la source locale est absent des octets Drive apres
  retelechargement;
- Drive ne contient aucun document brut, OCR, export clair, log, secret, token,
  cle privee, chemin local, nom humain ou blob dechiffre;
- le bouton de partage reste inactif tant que le gate anti-fuite n'est pas vert;
- les erreurs de chiffrement, signature, hash, compte ou scope bloquent
  l'upload.

NO-GO immediat si:

- l'utilisateur final doit ouvrir Google Cloud ou manipuler un JSON OAuth;
- le scope Drive est plus large que le besoin sans decision tracee;
- un fichier lisible de copropriete peut arriver dans Drive;
- un diagnostic support expose des donnees metier claires;
- le test novice exige repo, Python, PowerShell ou vocabulaire OAuth/API.

## References Google verifiees

- Quickstart Drive Python:
  https://developers.google.com/workspace/drive/api/quickstart/python
  Creation d'un client OAuth `Desktop app`, API Drive a activer, stockage local
  du token apres consentement.
- OAuth desktop/native apps:
  https://developers.google.com/identity/protocols/oauth2/native-app
  Le flux desktop ouvre le navigateur systeme et revient par une boucle locale.
- Scopes Drive:
  https://developers.google.com/workspace/drive/api/guides/api-specific-auth
  `drive.file` est le scope non sensible recommande pour creer ou modifier les
  fichiers choisis/crees par l'app.
- Politiques OAuth:
  https://developers.google.com/identity/protocols/oauth2/policies
  Demander le plus petit jeu de scopes, ne jamais committer les secrets client,
  et prevoir verification plus tard si l'app devient publique a grande echelle.

## Prochaines decisions

- Installable Windows: decision V1 cadree dans
  `docs/runbook_packaging_noob_windows.md`:
  - PyInstaller `--onedir`;
  - installation per-user sous `%LOCALAPPDATA%\Programs\CoproScope`;
  - raccourci menu Demarrer utilisateur;
  - lanceur windowed qui ouvre l'UI locale sans terminal;
  - profil et coffres sous `%APPDATA%` / `%LOCALAPPDATA%`;
  - Google Drive limite a la surface `sync_chiffre` verifiee.
- Drive direct API ou Drive Desktop:
  - V1 noob recommandee: API Drive avec bouton OAuth;
  - fallback possible: Drive Desktop comme dossier transport, moins fluide et
    plus difficile a expliquer.
- Partage multi-personnes:
  - MVP: un utilisateur publie des fichiers chiffres;
  - etape suivante: invitation d'un autre coproprietaire avec procedure de cle
    comprensible et recuperation testee.
