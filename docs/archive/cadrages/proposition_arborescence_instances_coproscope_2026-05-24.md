# Proposition - arborescence standard des instances CoproScope

Date: 2026-05-24
Rattachement: `RM-2026-0022` / `CH-2026-0022`
Revision: voie temporaire apres challenge de l'inbox reconstruction Beauvallon

## Voie temporaire retenue

L'arbitrage serieux sur le modele d'arborescence est renvoye a une exploration
roadmap dediee. Pour avancer pragmatiquement, la v1 temporaire pose une regle
simple: l'utilisateur peut deplacer les pieces dans le coffre visible sans
casser CoproScope.

La consequence technique est non negociable: CoproScope ne doit pas identifier
une piece par son chemin. L'identite stable d'une piece vient du hash, du
manifeste, du `doc_id` et des evenements de rattachement. Le chemin visible est
une localisation courante, pas une verite metier.

## Decision produit temporaire

La racine d'une instance doit assumer deux choses differentes:

1. `01 - Deposez les nouveaux fichiers ici` est le depot physique novice:
   l'endroit ou l'utilisateur met vraiment les originaux a ajouter.
2. Les dossiers metier visibles ne sont pas le stockage de reference: ce sont
   des zones de rangement utilisateur que CoproScope doit pouvoir rebalayer,
   resynchroniser et rapprocher par hash.

Le survol de l'inbox reconstruction Beauvallon confirme ce besoin. Elle contient
586 fichiers, environ 565 Mio, tous a plat, avec chemins d'origine encodes dans
les noms. Les familles documentaires sont fortement melangees: factures,
redditions, reglements, AG, diagnostics, courriers, ITE, donnees restreintes.
Une arborescence de classement qui ferait du chemin la verite documentaire
serait fragile et risquerait les doublons.

## Arborescence cible v1 temporaire

```text
<instance>/
  instance.yml
  00 - Lire avant de partager/
    README.md
  01 - Deposez les nouveaux fichiers ici/
    A deposer ici/
    Importes par CoproScope/
    A reprendre/
  02 - A verifier avant partage/
    Classement a confirmer/
    Confidentialite a confirmer/
    Doublons possibles/
  03 - Dossiers du moment/
  04 - Classement metier - raccourcis/
    Referentiel de la copropriete/
    Assemblees generales/
    Comptes finances/
    Contrats fournisseurs/
    Travaux projets/
    Sinistres litiges/
    Conseil syndical syndic/
  08 - Versions partageables/
    Pour coproprietaires/
    Pour conseil syndical/
  09 - Rapports et syntheses/
  99 - Archives/
  .coproscope/
    config/
    depot/
      manifests/
      receipts/
    raw/
      copies_controlees/
      uploads_ui/
    restricted/
    registers/
    staging/
    system/
    outputs/
    vault/
      local/
      sync/
      projections/
    logs/
    models/
    backups/
    tmp/
```

## Role exact de `01`

`01 - Deposez les nouveaux fichiers ici` sert a l'action utilisateur: deposer,
scanner, glisser-deposer, importer depuis une cle USB ou un dossier local. Le
nom doit dire explicitement que ce dossier accepte les nouveaux fichiers.

Regle de fonctionnement proposee:

- `A deposer ici/`: entree libre, surveillee ou importee par action explicite.
- Apres import, CoproScope calcule hash, taille, extension, provenance relative
  et statut de confidentialite.
- CoproScope conserve une copie controlee ou un pointeur verifie sous
  `.coproscope/raw/`, selon la politique disque choisie.
- `Importes par CoproScope/` contient des recus lisibles ou des fiches, pas
  forcement les originaux.
- `A reprendre/` contient ce que CoproScope refuse ou ne sait pas traiter:
  fichier vide, format non accepte, doublon ambigu, chemin trop long, etc.

Le dossier `01` est donc physique, mais pas un classement. Il est un sas
tolerant: si l'utilisateur deplace ensuite les fichiers ailleurs dans le
coffre visible, CoproScope doit les retrouver par hash lors du prochain scan.

## Pourquoi les dossiers metier ne doivent pas etre canoniques

L'inbox Beauvallon montre le probleme d'une arborescence physique:

- une meme piece peut relever de plusieurs contextes: AG, finances, contrat,
  contentieux, preuve d'une action;
- certaines pieces sont sensibles, mais leur famille metier est banale;
- les factures dominent fortement et rendraient `Comptes finances` illisible
  si tout etait copie physiquement;
- les noms d'origine encodent deja une provenance utile, qu'il ne faut pas
  perdre par renommage manuel;
- un deplacement physique ne doit pas casser les hashes, les comparaisons et
  les preuves de reconstruction.

Les dossiers metier peuvent contenir des fichiers deplaces par l'utilisateur,
mais CoproScope ne doit jamais les considerer comme canoniques par leur chemin.
Ils peuvent aussi contenir des raccourcis CoproScope:

- fiches `.md` generees avec `doc_id`, titre lisible, statut, action suivante;
- liens locaux controles par l'UI;
- eventuellement raccourcis Windows, si l'usage final le justifie;
- jamais de copies brutes automatiques imposees par CoproScope.

Autrement dit: l'utilisateur peut ranger physiquement, CoproScope observe et
rapproche. CoproScope ne doit pas exiger que le fichier reste dans un dossier
precis apres import.

## Lecture novice

- `00 - Lire avant de partager`: message court: "Ce dossier complet ne se
  partage pas. Pour envoyer un document, utilisez seulement
  `08 - Versions partageables`."
- `01 - Deposez les nouveaux fichiers ici`: endroit ou mettre les nouveaux
  documents.
- `02 - A verifier avant partage`: file de securite visible. Le survol
  Beauvallon montre que c'est indispensable: une grande partie des documents
  exige biffage, aggregation ou validation humaine.
- `03 - Dossiers du moment`: vues de travail, pas duplication des originaux.
- `04 - Classement metier - raccourcis`: navigation humaine par themes.
- `08 - Versions partageables`: uniquement des derives explicitement autorises.
- `09 - Rapports et syntheses`: sorties lisibles produites ou validees.
- `99 - Archives`: conservation lisible de dossiers clos.

Les termes `raw`, `outputs`, `registers`, `staging`, `audit`, `agent`,
`worktree` et `vault` restent hors du premier niveau.

## Mapping technique `instance.yml`

Pour la v1, `instance.yml` reste a la racine. C'est le compromis compatible:
le CLI cherche aujourd'hui `<instance>/instance.yml`, et beaucoup de code
utilise `instance.path.parent` comme racine de travail.

Deux variantes sont possibles.

### Variante A - coffre visible comme source raw

```json
{
  "roots": {
    "workspace": ".",
    "raw": ".",
    "system": "./.coproscope/system",
    "outputs": "./.coproscope/outputs",
    "staging": "./.coproscope/staging",
    "logs": "./.coproscope/logs",
    "restricted": ["./.coproscope/restricted"]
  }
}
```

Avantage: l'utilisateur peut ranger librement dans le coffre visible.
Risque: le pipeline doit exclure `.coproscope/`, `08 - Versions partageables`,
les recus, les rapports et les raccourcis pour ne pas les reintegrer comme
originaux.

### Variante B - depot visible comme sas, raw canonique sous `.coproscope`

```json
{
  "roots": {
    "workspace": ".",
    "raw": "./.coproscope/raw/copies_controlees",
    "system": "./.coproscope/system",
    "outputs": "./.coproscope/outputs",
    "staging": "./.coproscope/staging",
    "logs": "./.coproscope/logs",
    "restricted": ["./.coproscope/restricted"]
  },
  "settings": {
    "layout": {
      "version": "instance-standard-v1-temp",
      "technical_root": "./.coproscope",
      "physical_deposit": "./01 - Deposez les nouveaux fichiers ici/A deposer ici",
      "user_moves_allowed": true
    }
  }
}
```

Avantage: les originaux controles sont stables et separes du sas novice.
Risque: CoproScope doit expliquer clairement que le depot visible est importe,
puis reference par recu, fiche ou scan de mouvement.

Recommandation temporaire: variante B pour les nouvelles instances, mais avec
un scan du coffre visible qui reconnait les fichiers deplaces par hash. Variante
A reste une piste d'exploration serieuse, car elle exige des exclusions solides.

## Parcours ajout document

1. L'utilisateur depose physiquement des fichiers dans
   `01 - Deposez les nouveaux fichiers ici/A deposer ici` ou passe par l'UI.
2. CoproScope importe par lot, calcule hash et cree un manifeste de depot.
3. Les originaux controles sont copies ou references sous `.coproscope/raw/`.
4. L'utilisateur voit des statuts lisibles: `A classer`, `A verifier avant
   partage`, `Acces limite`, `Pret a partager`.
5. Si l'utilisateur deplace ensuite le fichier dans un dossier metier visible,
   CoproScope le reconnait au prochain scan par hash et met a jour son chemin
   courant.
6. Les sorties partageables sont generees seulement apres gate privacy.

## Impacts du challenge inbox Beauvallon

- `01` doit etre physique et nomme `Deposez les nouveaux fichiers ici`.
- `02 - A verifier avant partage` doit remonter tres haut dans la racine.
- `04 - Classement metier` doit annoncer qu'il s'agit de raccourcis.
- `Comptes finances` doit etre subdivise dans l'UI: factures, redditions,
  consommations, impayes acces limite.
- Les imports massifs doivent garder la provenance d'origine dans les registres,
  pas dans des noms de fichiers aplatis visibles.

## Gates obligatoires

- Le dossier complet d'instance n'est jamais partageable tel quel.
- `08 - Versions partageables` ne contient que des derives autorises.
- `doctor` doit refuser une instance de travail avec remote GitHub.
- `doctor` doit detecter une racine cloud non chiffree ou non bornee.
- `share` et les exports doivent bloquer `.coproscope/`, `raw`, `restricted`,
  `logs`, chemins absolus, `file://`, secrets et mappings de biffage.
- Les dossiers metier visibles ne doivent pas contenir de copies brutes
  automatiques.
- Le deplacement d'un fichier par l'utilisateur dans le coffre visible ne doit
  pas casser le `doc_id`, le hash, les rattachements ou les preuves.
- Une migration doit produire un manifeste avant/apres et ne jamais supprimer
  les originaux sans sauvegarde et GO humain.

## Plan de migration

1. Creer une fixture synthetique avec `01` comme depot physique et
   `.coproscope/raw` comme stockage controle.
2. Ajouter `settings.layout.physical_deposit` et `user_moves_allowed` au schema
   instance.
3. Ajouter un scan de coffre visible qui detecte les moves par hash et met a
   jour le chemin courant sans creer de nouveau document.
4. Adapter le depot UI pour ecrire dans le meme modele: sas visible ou
   `.coproscope/raw/uploads_ui` selon le mode choisi.
5. Generer des fiches/raccourcis dans `04 - Classement metier - raccourcis`.
6. Etendre `doctor` pour detecter les cas dangereux: doublons divergents,
   fichiers introuvables, chemins cloud non bornes.
7. Tester sur une instance smoke, puis seulement sur `beauvallon_test`.

## Recommandation

Retenir temporairement le principe suivant: `01 - Deposez les nouveaux fichiers
ici` est le depot physique, `.coproscope/` est le controle technique, et
l'utilisateur peut ranger/deplacer les pieces dans le coffre visible sans
consequence fonctionnelle pour CoproScope. L'exploration roadmap devra definir
jusqu'ou cette promesse peut aller dans les cas de doublons, renommages, copies
et suppressions.
