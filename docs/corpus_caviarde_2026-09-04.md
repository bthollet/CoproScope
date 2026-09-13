# Corpus caviarde: le derive Markdown, le sel et l'annuaire

`RM-2026-0073` / `CONV-2026-2130` / branche `chantier/corpus-caviarde`.
Lot du 2026-09-04. Ce document dit ce que le code fait, ce qu'il protege, et ce
qu'il ne protege pas.

## Le probleme, en une phrase

CoproScope doit pouvoir etre branche sur Claude Code ou Codex pour repondre a
une question de fond, sans qu'un nom de coproprietaire sorte du poste. Il faut
donc un second corpus, a cote des pieces d'origine: du Markdown ou les identites
ont ete remplacees, et ou tout le reste est intact.

## Ce que le pipeline produit, fichier par fichier

Pour un document `DOC-XXXX` du registre documents:

| Fichier | Ou | Contenu |
|---|---|---|
| la piece d'origine | `raw/...` | jamais modifiee |
| `DOC-XXXX.caviarde.md` | `<redacted_dir>/corpus_md/` | le derive: en-tete YAML + texte caviarde |
| `corpus_caviarde_couverture.csv` | `<privacy_dir>/` | une ligne par document: derive, ou raison nommee |
| `annuaire_personnes.csv` | zone `restricted` (C8) | nom, prenom, compte, pseudonyme attribue |
| `table_correspondance_biffage.csv` | zone `restricted` (C8) | chaque valeur remplacee et son alias, par document |
| `corpus_caviarde_suspects.csv` | zone `restricted` (C8) | ce que le caviardage a peut-etre rate |
| `sel_alias.key` | `settings.vault.local_root/corpus_caviarde/` | le sel, hors Git |

Trois colonnes sont ajoutees au registre documents: `corpus_md_statut`,
`corpus_md_path`, `corpus_md_sha256`.

L'en-tete du derive porte le `doc_id`, l'empreinte du sel, le schema d'alias, le
nombre d'identites remplacees, le nombre de suspects residuels, et la regle de
lecture ci-dessous.

## Couverture: aucun document silencieux

Chaque ligne du registre recoit un statut. Un document sans derive porte une
raison explicite: `PDF_SANS_COUCHE_TEXTE`, `FORMAT_SANS_TEXTE:<extension>`,
`SOURCE_ABSENTE`, `TEXTE_VIDE`, `ECHEC_DERIVATION:<exception>`. La couverture ne
depend pas de `required_transformations`: un document mal qualifie en amont
recoit quand meme son derive.

Mesure: 32/32 documents sur le corpus Tilleuls (pseudo) de test, 22/22 sur Erables (pseudo).

## Les pseudonymes

`PERSONNE_AUBEPINE` designe une famille. `PERSONNE_AUBEPINE_INDIGO` designe une
personne de cette famille. La racine est un nom d'arbre ou de plante tire d'une
liste fermee de 218 mots; le suffixe est une couleur tiree d'une liste fermee de
83 mots. Les deux listes sont dans le code, dans `03_corpus_sel.py`.

**Comment un lecteur distingue un pseudonyme d'un vrai nom.** Un pseudonyme
commence toujours par `PERSONNE_`, `EMAIL_`, `TELEPHONE_`, `IBAN_` ou `SECRET_`.
Le corps d'un pseudonyme de personne est un nom de plante, eventuellement suivi
d'une couleur. Aucun de ces mots n'est un patronyme francais. Tout ce qui
ressemble a un nom sans ce prefixe est un nom reel que le caviardage n'a pas vu:
c'est un signalement, pas un pseudonyme.

Les identifiants techniques - email, telephone, IBAN, secret - gardent une
empreinte hexadecimale (`EMAIL_3F1A9C22`). Un lecteur n'a pas besoin de les
prononcer, et la forme hexadecimale dit d'un coup d'oeil que ce n'est pas un nom.

Une collision - deux familles differentes tirant le meme mot - est arbitree par
un suffixe numerique (`AUBEPINE2`), inscrit dans l'annuaire et donc stable.

## Le schema de sel

Un sel de 32 octets aleatoires est cree au premier passage sous
`settings.vault.local_root/corpus_caviarde/sel_alias.key`, a defaut dans la zone
`restricted`, a defaut dans `system/private/`. Il est ignore par Git.

Le pseudonyme est choisi par `blake2b(nom_normalise, key=sel)`, dont le resultat
sert d'index dans la liste de mots. Le nom est normalise sans accent et sans
ponctuation, de sorte que `Dupont`, `DUPONT` et `Dupont ` donnent le meme alias.

### Ce que ce schema protege

- **Le retournement d'un alias.** Sans le sel, un attaquant qui voit
  `PERSONNE_AUBEPINE` ne peut pas essayer tous les patronymes de France pour
  retrouver lequel donne `AUBEPINE`: la fonction est a clef, la clef fait 256
  bits, elle n'est pas devinable.
- **La correlation entre deux coffres.** Deux coproprietaires ont deux sels
  aleatoires distincts. La meme personne recoit deux pseudonymes differents dans
  les deux instances. On ne peut pas recouper deux corpus caviardes par leurs
  alias.
- **La continuite de raisonnement.** Dans une instance, la meme personne recoit
  toujours le meme pseudonyme, d'un document a l'autre. Un agent peut suivre
  `PERSONNE_AUBEPINE_INDIGO` du PV a l'annexe des soldes sans jamais savoir qui
  c'est.

### Ce que ce schema ne protege pas

- **L'analyse de frequence et de structure.** Un corpus de copropriete est
  petit. Un alias qui apparait 37 fois reste un alias qui apparait 37 fois. Une
  annexe des soldes donne 204 entites distinctes, dans un ordre stable, avec
  leurs montants. Quelqu'un qui detient la liste des coproprietaires et les
  soldes peut reidentifier par appariement de montants ou par rang alphabetique.
  Le sel n'y change rien.
- **Le lien familial.** Deux personnes de meme nom partagent la racine du
  pseudonyme. C'est un choix: il rend le derive analysable. C'est aussi une
  information, et elle est reidentifiante dans une petite copropriete.
- **Ce que la detection rate.** Un nom non detecte reste en clair. Le sel ne
  protege que ce qui a ete remplace.
- **La table de correspondance.** L'annuaire et la table sont la clef de
  reversion. Ils vivent en C8. Un derive n'est donc pas anonyme au sens du RGPD:
  c'est un pseudonyme, et un pseudonyme reste une donnee personnelle.
- **Un attaquant qui a le sel.** Le sel et le corpus ne doivent jamais voyager
  ensemble.
- **Une instance sans zone `restricted` declaree.** L'annuaire retombe alors
  dans `staging/privacy_dir`, qui n'est pas une zone C8. A corriger dans la
  configuration d'instance, pas dans le code.

## L'annuaire d'abord, l'appariement ensuite

Reconnaitre un patronyme dans un texte quelconque est mal pose: `M. Dupont`,
`Monsieur Dupont`, `DUPONT Jean` et `Jean Dupont` sont la meme personne, et rien
dans la forme ne dit qu'un mot en majuscules est un nom.

La piece qui porte le plus grand risque retourne le probleme. L'annexe des
soldes **est** un annuaire: un numero de compte, un nom, un prenom, un solde, en
colonne propre. Le module l'extrait par une regle structurelle - une ligne tout
en majuscules, precedee d'une ligne qui n'est qu'un numero de compte, suivie
d'une ligne qui n'est qu'un montant - puis apparie les variantes de ces chaines
connues dans tout le reste du corpus, sans accent et sans egard a la casse.

L'ancrage est volontairement strict. Sans lui, `- EAU ARROSAGE` d'un etat des
depenses, suivi de son montant, passerait pour une personne.

Deux passes, dans cet ordre:

1. **Annuaire.** Les variantes des personnes connues: `NOM Prenom`,
   `Prenom NOM`, `NOM P.`, et le nom seul. Le nom seul n'est tente que s'il fait
   au moins 4 lettres et n'appartient pas au vocabulaire du domaine.
2. **Regles generiques**, sur ce qui reste en clair: civilite suivie d'un nom,
   `NOM Prenom`, `Prenom NOM`, ligne `nom + montant`, puis les noms nus une fois
   qu'un nom de famille a ete etabli ailleurs dans le document. Email, telephone,
   IBAN et secrets sont traites au passage.

Les pseudonymes deja poses sont masques avant la seconde passe, sinon
`M.PERSONNE_AUBEPINE` fait lire `PERSONNE` comme un nom apres une civilite et
l'alias se replie sur lui-meme.

## Le curseur: ce qui doit survivre

L'incident du 2026-09-03 - une table d'alias qui avait remplace `Article 24`,
`Article 25` et `Vote`, environ 5 400 etiquettes sur 6 099 - detruisait
exactement ce que le parcours d'analyse doit extraire. Trois gardes:

1. Un lexique de vocabulaire protege: articles, resolutions, votes, majorites,
   organes, postes comptables, natures de charges, mois, particules, formes
   sociales. Un candidat qui contient un de ces mots n'est pas une personne.
2. Une garde de sortie: un alias de personne ne recouvre jamais une valeur qui
   commence par un chiffre ou par `article`, `resolution`, `vote`, `annexe`,
   `lot`, `loi`, `decret`, `page`, `compte`.
3. Les categories retenues sont uniquement des identites. `LOT`,
   `ACCOUNT_INDIVIDUAL`, `IMPAID`, `CONTENTIOUS` - presentes dans
   `redaction_signals` historique - sont **exclues** du corpus caviarde: ce sont
   du vocabulaire, pas des identites.

Les particules font exception au lexique: `DE`, `EL`, `DA`, `VAN` sont des mots
vides isoles mais font partie du nom dans `DE VERNAZOUX` ou `EL ORFA`. Un
candidat n'est juge que sur ses tokens porteurs.

## Les mesures

Deux cabinets, conformement au critere de generalisabilite.

### Tilleuls (pseudo) (corpus `instances/tests_ux` + l'annexe des soldes 2024)

| Mesure | Valeur |
|---|---|
| documents avec derive | 32/32 |
| annuaire | 296 personnes, dont 200 extraites de la liste nominative |
| annexe des soldes: lignes nominatives | 204 |
| annexe: noms attrapes | **200 (98,0 %)** |
| annexe: noms rates | 4 |
| PV du 2024-07-03: personnes de l'annuaire nommees dans la source | 216 |
| PV: encore en clair dans le derive | 10 |
| PV: **rappel** | **95,4 %** |
| `article NN` dans le PV: source / derive | 139 / 139 |
| montants dans le PV: source / derive | 307 / 307 |
| montants dans l'annexe: source / derive | 528 / 528 |
| suspects residuels signales sur tout le corpus | 582 formes distinctes, 4 140 occurrences |

### Erables (pseudo) (`instances/erables_pseudo_test`)

| Mesure | Valeur |
|---|---|
| documents avec derive | 22/22 |
| annuaire | 330 personnes, dont 0 issues d'une liste nominative |
| identites remplacees | 1 099 |
| motifs | nom_nu 156, civilite 141, nom_prenom 139, prenom_nom 65, telephone 41, email 30, iban 6 |
| suspects residuels signales | 1 046 formes distinctes, 5 742 occurrences |

Erables (pseudo) n'a pas d'annexe des soldes dans son corpus. Aucun annuaire n'y
est donc extrait, et tout repose sur les regles generiques. C'est le cas
defavorable, et il faut le lire comme tel: le rappel n'y est pas mesurable faute
de verite terrain, et la precision n'y est pas garantie.

Le compteur de suspects residuels est volontairement large: il signale toute
forme de nom encore en clair, y compris des raisons sociales, des noms de lieu
et des intitules comptables en capitales. C'est une mesure du trou, pas une
liste de fuites. Elle est ecrite en C8 parce qu'elle contient, par construction,
des noms non caviardes.

## Ce qui reste rate, et pourquoi

- **Les 4 lignes de l'annexe.** Formes que la regle tout-en-majuscules ne
  reconnait pas: tokens capitalises melanges, ou plus de six mots.
- **Les 10 personnes du PV.** Essentiellement des noms courts, des noms
  appartenant au vocabulaire protege, et des variantes que l'annuaire ne genere
  pas encore (nom de jeune fille, `epouse X`, indivisions).
- **Un corpus sans liste nominative.** Sans annuaire, la detection redevient
  heuristique. La bonne reponse produit n'est pas une meilleure heuristique:
  c'est d'exiger l'annexe des soldes a l'absorption.
- **Les prenoms isoles.** Un prenom seul, loin de son nom, n'est pas remplace.

## Configuration

```json
"settings": {
  "corpus_caviarde": {
    "enabled": true,
    "output_dir": "./outputs/redacted/corpus_md",
    "salt_path": "./coffre/corpus_caviarde/sel_alias.key"
  }
}
```

`enabled` est **faux par defaut**. `core/pipeline.py` appelle
`biffageops.build_markdown_corpus_if_enabled()`, qui ne fait rien tant que le
reglage est absent. Une instance qui sert de base de travail a un autre chantier
ne voit donc aucun changement de comportement d'absorption. `output_dir` et
`salt_path` sont optionnels.

## Ce qui n'est pas fait

- **La couche de texte dans le PDF d'origine.** Abandonnee dans ce lot, sur
  arbitrage: l'OCR est une decision de packaging, pas de module. Le derive
  Markdown se contente de la couche de texte quand elle existe, et nomme
  `PDF_SANS_COUCHE_TEXTE` quand elle manque.
- **Le branchement de `redact_required_documents()`.** Inchange. Le corpus
  caviarde est une voie distincte de la file de biffage historique, qui reste en
  place.
- **La synchronisation entre postes.** Hors lot.
