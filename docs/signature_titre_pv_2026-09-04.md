# Reconnaitre un proces-verbal d'assemblee: ce qui est invariant, ce qui varie

Rattachement: `RM-2026-0056` / `CH-20260904-CONV-2026-2126` / `CONV-2026-2126`.

## En deux phrases

CoproScope range parfois en proces-verbal d'assemblee generale des documents qui
n'en sont pas: des fichiers de travail, des propositions d'honoraires, des
convocations. Cette note explique la regle ajoutee pour signaler ces cas, ce
qu'elle suppose vrai partout, ce qu'elle refuse de supposer, et ce qui n'est pas
encore verifie.

## Le probleme, en clair

Le classement automatique s'appuyait sur le nom du fichier, son chemin, et un
vocabulaire de domaine: copropriete, syndic, resolution, vote. Dans le coffre
d'une copropriete, ce vocabulaire est partout. Mesure sur un corpus reel: sur
1090 documents, 539 contiennent au moins un de ces mots. Un controle fonde sur
ce vocabulaire ne separe donc rien: il demande "ce texte parle-t-il de
copropriete ?", pas "ce texte est-il un proces-verbal ?".

Consequence concrete pour un coproprietaire: si des matrices de risques et des
journaux de decisions sont comptes comme des proces-verbaux d'assemblee, tout
comptage qui en depend est faux, y compris sur les pages de controle de la
gouvernance et des comptes.

## Ce que fait la regle

Apres le classement automatique, pour un document range en `PV_AG`:

1. lire le texte extrait seul, sans le nom du fichier ni son chemin;
2. retirer les marqueurs de pagination que l'extraction injecte (`page 1`,
   `page 2 sur 26`), qui ne sont pas de la matiere;
3. si ce qui reste fait moins de 200 caracteres, s'arreter et repondre
   **`TEXTE_INSUFFISANT`**;
4. sinon, chercher le titre `proces-verbal de l'assemblee` dans les 300 premiers
   caracteres. S'il y est, le document est confirme. Sinon, repondre
   **`A_RECLASSER`**.

Le type du document n'est **jamais** change automatiquement. La regle pose un
doute; c'est un humain qui tranche.

### Deux etats, et pourquoi ils ne se confondent pas

- `A_RECLASSER` veut dire: *il y a du texte, et le titre attendu n'y est pas.*
- `TEXTE_INSUFFISANT` veut dire: *il n'y a rien a juger, je ne sais pas.*

C'est la distinction la plus importante de cette note. Une version anterieure du
controle les confondait: sur les 6 documents qu'elle signalait comme douteux,
4 n'etaient que des echecs d'extraction, c'est-a-dire des pages scannees dont
le texte n'avait pas ete lu. Traiter un scan illisible comme "ce n'est pas un
proces-verbal" est une erreur qui se propage en silence. Un vrai proces-verbal
mal numerise doit ressortir comme *inconnu*, jamais comme *rejete*.

## Ce que la regle suppose invariant

**Un proces-verbal d'assemblee porte son titre en tete.** C'est la seule chose
que la regle tient pour vraie chez tous les syndics. Deux raisons:

- la forme est imposee par le decret 67-223 pris pour la loi 65-557, pas par les
  habitudes d'un cabinet;
- elle s'est verifiee a l'identique chez deux cabinets differents: 5 vrais
  positifs, **0 faux positif sur 37 documents**.

## Ce que la regle traite comme variant, et refuse d'utiliser

Cinq autres signatures de forme ont ete mesurees, puis **ecartees**. Elles
avaient l'air d'invariants et n'en sont pas:

| signature | cabinet A | cabinet B | pourquoi ecartee |
|---|---|---|---|
| resolution numerotee | absente, meme des vrais PV | presente sur les PV **et** les convocations | varie, et ne separe pas |
| issue de vote (adoptee a la majorite) | absente, meme des vrais PV | presente sur les seuls PV | varie d'un cabinet a l'autre |
| tantiemes | sur la matiere d'AG | sur les PV, les convocations, un devis | ne separe pas |
| article 24/25/26 | sur la matiere d'AG | sur les PV, les convocations, 5 annexes | ne separe pas |
| votants / pouvoirs | absente | 1 PV et 2 annexes | varie, et bruyante |

Une version anterieure de cette piste proposait un seuil "au moins 2 signatures
sur 6 = proces-verbal". Le second cabinet l'a cassee: ses quatre convocations
marquent 2 a 3 sur 6, et auraient donc ete prises pour des proces-verbaux. La
regle a ete reduite a la seule signature qui a tenu. Les cinq autres ne sont pas
ecrites "au cas ou": une regle qui ne discrimine pas ajoute du bruit, pas de la
prudence.

Le vocabulaire de domaine est lui aussi traite comme variant. C'est un variant
deguise en invariant: il varie avec le corpus, et il est present presque partout.

## D'ou viennent les deux nombres

Ils sont mesures, pas choisis, et ils sont configurables dans
`taxonomy.default.yml` sous `signature_titre` car ils varieront au troisieme
syndic.

**Fenetre de tete, 300 caracteres.** Le titre apparait aux positions 0, 0, 26 et
94 sur les quatre proces-verbaux des deux cabinets. Le premier marqueur d'ordre
du jour d'une convocation apparait au plus tot a 389. 300 tient dans cet
intervalle, avec de la marge des deux cotes. Chercher le titre n'importe ou, et
non en tete, ferait passer pour un proces-verbal une convocation qui porte
"approbation du proces-verbal de l'assemblee precedente" a son ordre du jour.

**Plancher de texte, 200 caracteres utiles.** Les six echecs d'extraction des
deux cabinets tombent a 0 caractere utile une fois les marqueurs de pagination
retires. Ils valaient pourtant 13 a 258 caracteres bruts, ce qui suffisait a
tromper un seuil pose sur le texte brut. Le plus petit document reellement
porteur de texte en compte 251. 200 separe les deux. En cas de doute, mieux vaut
un plancher trop haut: il fait dire "je ne sais pas", alors qu'un plancher trop
bas fait dire "ce n'est pas un proces-verbal" a une page scannee.

## Resultat mesure sur les deux cabinets

| | cabinet A | cabinet B | total |
|---|---:|---:|---:|
| documents confrontes | 15 | 22 | 37 |
| confirmes proces-verbal | 3 | 2 | **5** |
| `A_RECLASSER` | 12 | 17 | 29 |
| `TEXTE_INSUFFISANT` | 0 | 3 | 3 |
| **faux positifs** | 0 | 0 | **0** |

Un cas merite d'etre nomme: chez le cabinet A, un extrait de resolution ressort
en `A_RECLASSER` alors qu'il s'agit bien de matiere d'assemblee. C'est un
extrait, pas un proces-verbal complet: demander confirmation est defendable,
mais c'est le seul cas ou la regle met en doute une piece authentique.

Chez le cabinet B, un vrai proces-verbal ressort en `TEXTE_INSUFFISANT` parce
que son extraction n'a rendu que 86 caracteres. C'est le comportement voulu: la
regle dit qu'elle ne sait pas, elle ne le declare pas faux.

## Ce qui n'est pas verifie

A lire avant de faire confiance a cette regle ailleurs:

- **Deux cabinets restent deux.** Rien ne garantit qu'un troisieme redige ses
  titres pareil. C'est precisement pour cela que la fenetre et le plancher sont
  configurables plutot que figes.
- **Aucun proces-verbal d'assemblee extraordinaire n'a ete teste.** Le corpus ne
  contient que des assemblees ordinaires.
- **Aucun proces-verbal scanne correctement mais sans texte** n'a pu etre teste,
  en dehors du seul cas a 86 caracteres.
- **Rien n'a ete mesure sur les autres types a enjeu** - convocation, facture,
  annexe comptable. Les convocations du cabinet B seraient le banc d'essai
  naturel pour leur chercher un titre equivalent; ce travail n'est pas fait.
- **La verite terrain du cabinet B** repose sur les noms de fichiers recoupes
  par la lecture des en-tetes, pas sur une expertise juridique piece par piece.
- **Le raccordement en aval n'est pas fait.** Les deux nouveaux etats ne sont pas
  encore compris par la boite de reception, la visionneuse et la matrice de
  completude; ils y sont lus comme "a traiter", ce qui est sans danger mais pas
  explicite. C'est un lot separe.

## La piste de provenance, et pourquoi elle n'est pas ici

Neuf des onze fichiers mal ranges chez le cabinet A viennent des dossiers ou
CoproScope produit lui-meme ses documents de travail. L'invariant sous-jacent
est solide: **ce que CoproScope a produit ne doit jamais etre classe comme piece
emise par le syndic.**

Mais le produit ne sait pas encore l'exprimer, et ce n'est donc pas une regle de
classement:

- les champs qui devraient porter la provenance, `source_kind` et `source_zone`,
  sont derives du chemin et sont degeneres en pratique: 1090 documents sur 1090
  chez le cabinet A, et 22 sur 22 chez le cabinet B, portent la meme valeur;
- le journal d'ecriture du produit existe, mais **aucun** des onze fichiers n'y
  figure: ils ont ete produits hors des executions journalisees.

Fonder un filtre sur une liste de noms de dossiers reviendrait a coder
l'arborescence d'une seule instance. Le jour ou le produit posera une estampille
au moment ou il ecrit un fichier, le classement pourra la consulter et refuser
d'emblee de ranger un artefact maison en piece de syndic. Ce changement est
ouvert en `RM-2026-0061`.

## Configuration

```json
"signature_titre": {
  "motifs": { "PV_AG": "proces verbal de l assemblee" },
  "fenetre_tete": 300,
  "plancher_texte_utile": 200
}
```

Alias anglais acceptes: `title_signature`, `patterns`, `head_window`,
`useful_text_floor`. Cle absente: valeurs par defaut du code. `"motifs": {}`:
controle desactive. Les motifs sont compares sur texte translitere sans accents
et en minuscules, donc `proces verbal de l assemblee` reconnait aussi la forme
accentuee et apostrophee du titre.

## Tests

`server/tests/test_docuscope_signature_titre.py`, 21 cas, corpus synthetique
uniquement - aucune donnee d'instance privee n'entre dans le depot. Les cas
reproduisent les formes mesurees: les positions de titre relevees, la convocation
qui porte l'approbation du proces-verbal precedent a son ordre du jour, le
bourrage de marqueurs de pagination, les trois extractions quasi vides, et le
plus petit document reellement porteur de texte.
