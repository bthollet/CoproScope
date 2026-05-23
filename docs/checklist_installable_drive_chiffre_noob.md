# Checklist installable Drive chiffre noob

Rattachement: `RM-2026-0014` / `CH-2026-0014`.

Objectif: livrer CoproScope comme application Windows installable par une
personne non-geek, avec partage Google Drive limite a une surface produite par
CoproScope, chiffree, signee/verifiee et sans donnees metier lisibles.

Regle absolue: Drive est un transport. Drive ne recoit jamais le dossier de
travail, les documents sources, les OCR, les logs, les exports clairs, les
secrets ou les fichiers dechiffres.

## Definition de la surface Drive autorisee

Surface autorisee pour le MVP:

- fichiers de coffre produits par CoproScope apres verification;
- blobs chiffres;
- evenements signes dont le payload metier est chiffre;
- snapshots ou indexes seulement s'ils sont chiffres ou opaques;
- cles publiques de verification non sensibles;
- enveloppes de cles chiffrees pour destinataires autorises;
- metadata technique minimale si elle ne contient aucun nom de copropriete,
  nom de personne, nom de document, chemin local, commentaire, OCR ou statut
  metier lisible.

Surface non autorisee:

- dossier instance local complet;
- dossier `raw`, `restricted`, `private`, `logs`, `tmp`, `cache`, `exports`,
  `decrypted`, `blobs_dechiffres` ou equivalent;
- documents originaux: PDF, DOCX, XLSX, images, archives, mails, pieces jointes;
- textes extraits, OCR, Markdown, CSV, JSON metier clair, rapports d'audit;
- exports biffes ou agreges non rechiffres pour le coffre Drive;
- indexes lisibles contenant noms, statuts, commentaires, chemins, OCR ou
  decisions;
- manifeste distant contenant contenu clair, chemins locaux ou noms humains;
- secrets OAuth: `credentials.json`, `client_secret*.json`, `token.json`;
- cles privees, seeds, phrases de recuperation, parts de recuperation en clair;
- `.git`, `.venv`, `node_modules`, caches, fichiers temporaires et crash dumps;
- fichiers fournisseur instables: `.gdoc`, `.gsheet`, `.gslides`, `.tmp`,
  `.partial`, copies conflictuelles, placeholders, liens symboliques;
- captures d'ecran ou journaux support contenant des donnees de copropriete.

## Parcours noob cible

Chaque etape doit etre faisable sans terminal, sans Google Cloud, sans fichier
JSON et sans vocabulaire OAuth/API/scope.

### 1. Installer

- [ ] L'utilisateur lance un installateur Windows signe ou identifiable.
- [ ] Un raccourci `CoproScope` apparait dans le menu Demarrer.
- [ ] Le premier lancement ne demande ni terminal, ni Python, ni chemin de repo.
- [ ] Message succes: `CoproScope est pret sur cet ordinateur.`
- [ ] Message blocage: `L'installation n'est pas complete. Relancez l'installateur ou contactez la personne qui vous accompagne.`

GO: l'application s'ouvre depuis le menu Demarrer sur une machine propre.

NO-GO: l'utilisateur doit lancer PowerShell, installer Python, copier un depot,
modifier un fichier de configuration ou ouvrir Google Cloud.

### 2. Creer le coffre local

- [ ] L'assistant propose `Creer un coffre`.
- [ ] Le dossier local propose par defaut est dans le profil utilisateur.
- [ ] Le choix d'un autre dossier est possible mais controle.
- [ ] CoproScope refuse un dossier deja synchronise contenant des interdits.
- [ ] Message succes: `Votre coffre chiffre est cree sur cet ordinateur.`
- [ ] Message blocage: `Ce dossier contient des fichiers qui ne doivent pas etre partages. Choisissez un autre dossier ou laissez CoproScope en creer un.`

GO: le coffre local est cree, verifie et isole des dossiers de travail bruts.

NO-GO: le coffre est cree dans le repo, dans une instance privee brute, dans un
dossier Drive Desktop non controle ou a cote de logs/secrets.

### 3. Connecter Google Drive

- [ ] L'assistant affiche `Connecter Google Drive`.
- [ ] Le navigateur officiel s'ouvre pour choisir le compte Google.
- [ ] L'utilisateur ne voit pas `client secret`, `scope`, `API`, `token` ou
  `credentials`.
- [ ] Le scope reste le plus etroit possible pour le MVP: `drive.file`.
- [ ] Le token est stocke hors Git et hors coffre synchronise.
- [ ] Message succes: `Google Drive est connecte.`
- [ ] Message refus: `Google a refuse l'autorisation. Reessayez ou choisissez un autre compte.`
- [ ] Message expiration: `La connexion Google Drive a expire. Reconnectez Google Drive.`
- [ ] Message compte: `Ce coffre etait connecte a un autre compte Google. Confirmez avant de changer de compte.`

GO: un utilisateur test connecte Drive sans manipuler de secret ni de console.

NO-GO: l'utilisateur final doit creer un projet Google Cloud, telecharger un
JSON, choisir un scope ou coller un token.

### 4. Verrou anti-fuite avant upload

- [ ] CoproScope construit une surface Drive separee du dossier de travail.
- [ ] CoproScope verifie l'allow-list des chemins racine du coffre.
- [ ] CoproScope refuse les extensions, dossiers et marqueurs interdits.
- [ ] CoproScope refuse tout fichier dont le contenu clair est detecte comme
  lisible ou dechiffre.
- [ ] CoproScope verifie hash/signature quand disponible.
- [ ] CoproScope ecrit un manifeste local seulement: quoi a ete envoye, taille,
  hash, date, compte Drive, jamais contenu clair ni chemin prive.
- [ ] Aucun bouton de partage n'est actif avant ce verrou.
- [ ] Message attente: `CoproScope verifie que rien de lisible ne part dans Drive.`
- [ ] Message succes: `Pret a partager: seuls des fichiers chiffres seront envoyes.`
- [ ] Message blocage: `Partage bloque: un fichier lisible a ete detecte.`
- [ ] Message blocage: `Partage bloque: le coffre chiffre n'est pas verifie.`

GO: le verrou bloque volontairement un fichier canari clair place dans la
surface candidate.

NO-GO: un upload Drive peut partir sans verification, ou l'UI affiche
`Pret a partager` avant la fin du verrou.

### 5. Premier envoi chiffre

- [ ] Le premier upload cree un dossier Drive CoproScope dedie avec un nom non
  metier, ou utilise un dossier deja cree par l'app.
- [ ] Les noms de fichiers distants ne revelent pas copropriete, personne,
  document, action ou statut sensible.
- [ ] CoproScope upload seulement la surface autorisee.
- [ ] CoproScope relit les metadata autorisees et compare tailles/hashes locaux.
- [ ] Message succes: `Drive connecte - coffre chiffre synchronise.`
- [ ] Message partiel: `Drive est connecte mais le coffre chiffre n'est pas encore envoye.`
- [ ] Message reseau: `Hors ligne. CoproScope reprendra l'envoi quand la connexion reviendra.`

GO: apres telechargement de ce qui est sur Drive, aucun contenu metier clair,
nom de document, OCR, chemin local ou secret n'est visible.

NO-GO: Drive contient un PDF/DOCX/XLSX source, un OCR, un rapport clair, un nom
humain dans une metadata visible ou un manifeste distant trop bavard.

### 6. Partager le coffre chiffre

- [ ] Le bouton principal dit `Partager le coffre chiffre`.
- [ ] L'invitation explique que l'autre personne pourra telecharger le coffre,
  mais ne lira que ce que ses cles autorisent.
- [ ] CoproScope ne partage pas de document individuel brut via Drive.
- [ ] CoproScope confirme le role ou le compartiment avant de produire
  l'invitation.
- [ ] Message succes: `Invitation prete. Le lien ne contient pas de document lisible.`
- [ ] Message role: `Cette personne ne pourra lire que les informations autorisees pour son role.`
- [ ] Message blocage: `Partage bloque: choisissez d'abord ce que cette personne a le droit de lire.`

GO: l'utilisateur comprend qu'il partage un coffre chiffre, pas un dossier de
documents bruts.

NO-GO: l'UI encourage `Partager le dossier Drive` sans expliquer les droits de
dechiffrement, ou propose de choisir des fichiers sources.

### 7. Reprise, revocation et support

- [ ] La reconnexion Drive est proposee sans jargon.
- [ ] Une revocation Google bloque les prochains uploads et garde le coffre
  local intact.
- [ ] Les journaux support sont expurges avant export.
- [ ] Les diagnostics ne contiennent ni chemins prives, ni noms de documents,
  ni tokens, ni payloads dechiffres.
- [ ] Message revocation: `Google Drive n'est plus autorise. Vos donnees restent dans le coffre local.`
- [ ] Message diagnostic: `Le diagnostic ne contient pas vos documents.`

GO: une panne reseau, une expiration de token ou une revocation n'entraine pas
de fuite et reste comprehensible.

NO-GO: un diagnostic ou une capture support exporte des donnees metier claires.

## Decisions bloquantes

Ces decisions doivent etre tranchees avant de declarer un installable noob
livrable:

1. Identite OAuth finale: nom public, ecran de consentement, proprietaire,
   statut test/production, verification Google si necessaire, scope `drive.file`
   maintenu sauf decision documentee.
2. Mode Drive V1: API Drive via bouton OAuth par defaut; Drive Desktop seulement
   comme fallback explicite et plus difficile a expliquer.
3. Format de publication: surface vault synchronisable directe ou paquet
   chiffre opaque; dans les deux cas, aucun contenu metier clair dans Drive.
4. Nommage distant: noms opaques ou techniques, sans copropriete, personne,
   document, statut ou chemin local.
5. Manifeste: local et lisible pour l'utilisateur; pas de manifeste Drive
   contenant donnees metier ou chemins prives.
6. Cles et invitations: qui peut dechiffrer quoi, comment recuperer une cle,
   comment revoquer un acces, et comment tester la perte d'un terminal.
7. Erreurs bloquantes: fail-closed obligatoire si chiffrement, signature,
   hash, scope, compte, dossier ou detection anti-fuite echoue.
8. Packaging Windows: installateur, raccourci, stockage profil utilisateur,
   mise a jour et desinstallation sans supprimer silencieusement le coffre.
9. Support: format de diagnostic expurge et message clair avant tout partage
   avec un humain.
10. Test novice: profil de test, machine propre, compte Google de test,
    criteres de temps et consignes d'observation.

## Criteres GO/NO-GO release

### GO securite

- [ ] Aucune donnee metier claire n'est presente dans Drive apres upload et
  retelechargement.
- [ ] Un canari clair place dans la source locale ne se retrouve pas dans les
  octets Drive.
- [ ] Les secrets OAuth et tokens restent hors Git, hors coffre et hors Drive.
- [ ] Les cles privees et parts de recuperation en clair restent hors Drive.
- [ ] Le verrou anti-fuite est teste avec au moins un fichier interdit, un
  fichier dechiffre, un log, un export temporaire et un index lisible.
- [ ] Le partage echoue par defaut en cas d'incertitude.

### GO novice

- [ ] Une personne non-geek installe, ouvre, cree le coffre, connecte Drive et
  obtient `Drive connecte - coffre chiffre synchronise` sans aide terminal.
- [ ] Elle comprend les trois etats: non connecte, pret a partager, bloque pour
  protection.
- [ ] Elle ne voit pas OAuth, scope, API, client secret, token, vault ou sync au
  premier niveau.
- [ ] Les messages de blocage disent quoi faire sans exposer de details
  sensibles.

### GO Drive

- [ ] Le scope effectif est controle et reste minimal.
- [ ] Le dossier Drive cree par l'app ne contient que la surface autorisee.
- [ ] La reconnexion apres expiration fonctionne sans recreer de coffre.
- [ ] Le changement de compte Google demande confirmation.
- [ ] Un upload interrompu ne laisse pas d'etat `Pret a partager` mensonger.

### GO packaging

- [ ] L'app demarre depuis le menu Demarrer.
- [ ] Le stockage applicatif est dans le profil utilisateur.
- [ ] Le chemin des secrets, tokens et journaux est documente hors Git.
- [ ] La desinstallation ne supprime pas le coffre sans confirmation explicite.
- [ ] Le diagnostic support est expurge par defaut.

### NO-GO immediat

Release refusee si au moins un point est vrai:

- l'utilisateur final doit ouvrir Google Cloud ou manipuler un JSON OAuth;
- Drive contient un document source, OCR, export clair, log, secret, token,
  cle privee ou blob dechiffre;
- un nom de copropriete, personne, document, chemin local ou commentaire metier
  apparait dans un fichier Drive lisible;
- le scope Drive est plus large que le besoin sans decision documentee;
- le bouton de partage s'active avant le verrou anti-fuite;
- une erreur de chiffrement, signature, hash ou compte Drive produit un warning
  mais laisse uploader;
- un diagnostic support contient des donnees metier claires;
- le test novice exige terminal, repo, Python, console Google ou vocabulaire
  OAuth/API.

## Preuve attendue a chaque livraison

Pour chaque livraison candidate:

- chemin de l'installateur ou methode de lancement testee;
- compte Google de test utilise, sans secret dans le compte rendu;
- capture ou note d'observation du parcours novice;
- resultat du verrou anti-fuite avec cas autorises et cas bloques;
- liste des fichiers Drive observes apres retelechargement;
- scan canari: chaine claire absente des octets Drive;
- verdict final `GO`, `GO conditionnel` ou `NO-GO`, avec la raison courte.
