# ComptaScope

ComptaScope est la brique comptable de CoproScope. Elle ne remplace pas une comptabilite officielle: elle reconstruit des ecritures candidates a partir des factures candidates produites par FactureOps et des sources comptables disponibles, afin d'aider un conseil syndical a controler, rapprocher et expliquer.

Frontiere metier:

- DocOps produit la preuve documentaire brute.
- FactureOps extrait les factures et signale les anomalies de piece.
- ComptaScope reconstruit les ecritures candidates, rapproche l'etat des depenses et signale les controles comptables.

## Donnees produites

- `invoice_evidence_<annee>.csv`: factures candidates produites par FactureOps.
- `invoice_anomalies_<annee>.csv`: anomalies facture produites par FactureOps.
- `ledger_reconstruction_<annee>.csv`: ecritures candidates debit charge / credit fournisseur.
- `accounting_controls_<annee>.csv`: controles comptables et rapprochements a traiter.
- `expense_statement_lines_<annee>.csv`: lignes d'etat des depenses normalisees quand une source est configuree.
- `invoice_expense_matches_<annee>.csv`: rapprochements factures / etat des depenses, avec cause et prochaine action.
- `non_rapproches_prioritaires_<annee>.csv`: non-rapprochements et candidats ambigus classes par montant.
- `supplier_alias_suggestions_<annee>.csv`: alias fournisseurs deduits ou proposes a partir des montants et familles comptables.
- `controle_comptes_guide_<annee>.csv`: parcours de controle par facture, avec priorite, detail de ligne candidate, motif, action suivante et question syndic.
- `regroupement_controle_comptes_<annee>.csv`: synthese par priorite, fournisseur, anomalie facture et statut de rapprochement.
- `questions_syndic_comptascope_<annee>.md`: questions syndic pretes a relire/copier pour les points `P1` et `P2`.
- `rapport_comptascope_<annee>.md`: rapport explicatif local, avec synthese, priorites, causes, traitements locaux appliques et exemples a traiter.
- `coproscope_accounting_<annee>.duckdb`: base analytique locale si DuckDB est disponible.

Ces sorties sont un contrat de production: meme lorsqu'aucun etat des depenses n'est configure, ComptaScope cree les rapports et tables vides correspondantes. Les commandes `accounting controls`, `grist sync` et `evidence build` verifient que le rapport ComptaScope existe et relancent la reconstruction si une sortie de rapport manque.

## Commandes

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli invoices extract --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli accounting reconstruct --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli accounting controls --instance-root .\examples\synthetic_copro --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli grist sync --instance-root .\examples\synthetic_copro --dataset demo --year 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli evidence build --instance-root .\examples\synthetic_copro --dataset demo --year 2025
```

Alias francais:

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli factures extraire --instance-root .\examples\synthetic_copro --annee 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli compta reconstituer --instance-root .\examples\synthetic_copro --annee 2025
.\server\.venv\Scripts\python.exe -m coproscope.cli compta controles --instance-root .\examples\synthetic_copro --annee 2025
```

## Statuts

- `PROBABLE`: extraction coherente mais non validee officiellement.
- `INCERTAIN`: extraction utile mais incomplete.
- `A_CONTROLER`: anomalie P0 ou information indispensable manquante.

## Rapprochement facture / etat des depenses

Les anomalies facture et les controles comptables sont volontairement separes. Une anomalie facture dit que la piece ou son extraction est incomplete. Un controle comptable dit qu'une ecriture, un rapprochement ou une preuve comptable doit etre traite.

ComptaScope ne considere plus `NON_RAPPROCHE` comme une conclusion comptable. C'est un signal d'explication: l'automate n'a pas encore trouve de preuve deterministe suffisante.

Le rapport utilise trois niveaux de lecture:

- `OK`: preuve locale suffisante pour rapprocher sans demander d'interpretation supplementaire.
- `P2`: candidat plausible trouve par traitement local; confirmation humaine attendue, mais ce n'est pas un blocage prioritaire.
- `P1`: aucun indice local suffisant; controle prioritaire du grand livre, de l'etat des depenses, de l'OCR ou de la piece.

Les statuts de rapprochement principaux sont:

- `MATCH_REFERENCE`: la reference de facture apparait dans une ligne de depense.
- `MATCH_AMOUNT_SUPPLIER`: montant TTC exact et fournisseur reconnu.
- `MATCH_AMOUNT_ALIAS`: montant TTC exact et alias fournisseur configure.
- `CANDIDAT_MONTANT_FAMILLE`: montant TTC exact et compte/famille compatible, fournisseur a confirmer (`P2`).
- `CANDIDAT_SOMME_MULTI_LIGNES`: plusieurs lignes compatibles totalisent exactement la facture (`P2`).
- `CANDIDAT_NOM_SIMILAIRE`: montant, famille et nom fournisseur tres proche concordent (`P2`).
- `CANDIDAT_DIVISION_EGALE`: le TTC d'une facture se divise exactement en lignes de meme montant (`P2`).
- `CANDIDAT_REGROUPEMENT_FACTURES`: plusieurs factures du meme fournisseur totalisent une ligne de depense (`P2`).
- `CANDIDAT_MONTANT_AMBIGU` ou `CANDIDAT_VENTILATION_AMBIGUE`: ComptaScope peut avancer, mais plusieurs choix restent possibles (`P2`).
- `CANDIDAT_MONTANT_SANS_NOM`, `CANDIDAT_FOURNISSEUR_SANS_MONTANT` ou `CANDIDAT_FAMILLE_SEULE`: un indice local existe, mais il ne suffit pas seul (`P2`).
- `NON_RAPPROCHE`: reference, montant, fournisseur, alias, similarite de nom et famille comptable ne suffisent pas (`P1`).

Les traitements locaux sont volontairement explicites et ordonnes:

1. reference de facture dans l'etat des depenses ;
2. montant TTC exact avec fournisseur reconnu ;
3. montant TTC exact avec alias fournisseur configure ou deduit ;
4. montant TTC exact avec nom fournisseur tres similaire ;
5. montant TTC exact avec famille comptable compatible ;
6. division d'une facture en lignes egales ;
7. somme de plusieurs lignes vers une facture ;
8. regroupement de plusieurs factures vers une ligne ;
9. classement des cas restants en candidats `P2` ou blocages `P1`.

Une similarite de nom evidente ne doit donc plus remonter comme blocage dur: elle devient un candidat `P2` a confirmer. L'outil ne valide pas le rapprochement a la place du conseil syndical, mais il produit une cause locale, une action attendue et une priorite.

## Controle guide et questions syndic

Le fichier `controle_comptes_guide_<annee>.csv` est la vue actionnable pour conseil syndical. Une ligne correspond a une facture candidate et rassemble:

- la priorite `OK`, `P2` ou `P1` ;
- le fournisseur, la facture, le montant, le niveau de preuve et les anomalies facture ;
- la ligne d'etat des depenses candidate quand elle existe ;
- l'ecriture candidate reconstruite ;
- le motif local, la prochaine action et la question syndic.

Le fichier `regroupement_controle_comptes_<annee>.csv` sert de table de lecture rapide avant assemblee generale: il regroupe les lignes du guide par priorite, fournisseur, anomalie facture et statut de rapprochement. Il donne le nombre de factures, le total TTC, le nombre de questions syndic et quelques exemples de factures a ouvrir en premier.

Le fichier `questions_syndic_comptascope_<annee>.md` reprend uniquement les lignes ouvertes. Les blocs `Objet / Bonjour / question / action attendue` sont faits pour etre relus puis copies dans un mail ou une demande de piece. Les lignes `OK` ne generent pas de question.

Les alias et sources de lignes se configurent dans `settings.comptascope`:

```json
{
  "comptascope": {
    "invoice_evidence_csv": "./system/accounting/invoice_evidence_2025.csv",
    "expense_statement_lines": "./system/accounting/expense_statement_lines_2025.csv",
    "auto_infer_supplier_aliases": true,
    "auto_alias_min_evidence": 2,
    "supplier_aliases": [
      {"supplier": "JARDINS EXEMPLE SERVICES", "aliases": ["JEX"]}
    ]
  }
}
```

Si `invoice_evidence_csv` est renseigne, ComptaScope repart de ce registre deja extrait au lieu de rescanner les bruts. C'est le mode adapte aux reprises d'audit: on peut enrichir les rapprochements, les alias et les rapports sans refaire toute l'extraction documentaire.

Le mecanisme d'alias automatique reste prudent: un alias n'est auto-applique que lorsqu'au moins deux factures du meme fournisseur ont un montant exact, une famille comptable compatible, et le meme indice fournisseur structure dans l'etat des depenses. Les alias deduits seulement d'un libelle libre ou d'un cas unitaire restent proposes en `A_CONTROLER`.

## Methode agile de recette Comptes

Les petites iterations ComptaScope se font sur une route reelle, avec une
equipe agile tracee: coordinateur, designer/facilitateur, utilisateur novice,
expert CS/compta, dev front/back et QA. Quand la route existe deja et que la
tranche corrige seulement le vocabulaire ou la prudence metier, le visuel IA et
le blueprint peuvent etre annules avec `VISUEL_IA_WAIVED` et
`BLUEPRINT_WAIVED`. Si la structure de l'ecran change, ils redeviennent
obligatoires avant dev.

Regles generalisables issues de l'iteration `CC-IT-016`:

- le code courant et les tests priment sur une trace documentaire ancienne;
- une source absente doit etre nommee explicitement, par exemple banque ou
  grand livre non fourni;
- les actions utilisent des verbes de controle: tracer, verifier, garder une
  reserve, preparer une question;
- une question syndic reste un brouillon a relire et copier, jamais un envoi;
- la trace conseil syndical ne valide ni paiement ni comptabilite officielle;
- les tests de route doivent verifier les mots que le membre du conseil
  syndical novice voit vraiment.

Complement UI issu de `CC-IT-017`: un ecran ComptaScope de bon niveau ne doit
pas afficher les noms techniques internes. Les sources doivent etre scannables,
et chaque absence de source doit etre aussi visible qu'une preuve presente.
Les termes `CS`, `AG`, `append-only`, `read model` ou equivalents restent hors
premier niveau UI; on parle de conseil syndical, assemblee generale, journal
local et controles locaux.

Complement recette issu de `CC-IT-018`: des qu'un `CoproScope.exe` existe, la
preuve finale de la route Controle des comptes se fait dans cet executable,
pas dans un executable separe et pas seulement sur le serveur de developpement.
Le smoke Windows doit pouvoir cibler la route reelle avec
`-ProbePath /comptes/rapprochement` et des textes visibles comme
`Controle des comptes`, `Sources du controle` et `Lignes a controler`. Une
recette serveur peut aider a iterer vite, mais elle ne suffit plus pour dire
que le module est integre. Les frottements vus dans la fenetre executable ou
dans le navigateur integre, par exemple une navigation qui coupe les mots, sont
a corriger avant de donner un lien de recettage.

Complement UI issu de `CC-IT-019`: une iteration utile peut retirer des blocs.
Les tableaux bas de page `Decision avant rapport`, `Diffusion` et
`Historique local` ont ete supprimes de la route Controle des comptes, car ils
repetaient les garde-fous sans guider l'action principale. La regle
generalisable est de garder les garde-fous au plus pres de la ligne controlee
et de tester explicitement l'absence du bruit retire.

Complement UI issu de `CC-IT-020`: le rapprochement d'une ligne doit se lire
comme une matrice de quatre sources, toujours dans le meme ordre:
`Comptabilite`, `Banque`, `Facture`, `Decision / devis`. Une source absente
est une information de premier niveau, pas une note de bas de page. En
particulier, si le corpus ne contient pas d'extrait bancaire, la colonne
`Banque` affiche `Banque non fournie` et rappelle qu'aucun paiement n'est
confirme. Les liens vers DocOps sont autorises seulement sur les cellules qui
portent une piece identifiable; ils ne remplacent pas la reserve metier.

Complement executable issu de `CC-IT-020b`: la recette doit utiliser les memes
chemins de donnees que l'executable ouvre en situation reelle. Les sorties
ComptaScope peuvent etre rangees directement dans `outputs/accounting` ou dans
un sous-dossier d'exercice comme `outputs/accounting/2025`; la route doit lire
les deux formes avant de conclure qu'aucune ligne n'existe. Un smoke positif
sur le serveur de developpement ne suffit pas si `CoproScope.exe` charge une
instance differente.

Complement UI issu de `CC-IT-021`: une longue file de controle ne doit jamais
enterrer la ligne selectionnee. Le poste de controle vient avant les KPI et les
definitions, puis la file devient un panneau borne avec scroll interne. En
largeur etroite, le detail reste avant la file; en largeur desktop, la file et
le detail forment un poste de travail cote a cote. Les barres d'action du
header ne doivent pas reserver de grand vide invisible. La recette finale doit
se faire dans `CoproScope.exe` avec un jeu volumineux, ici 827 lignes, pour
prouver que l'ergonomie tient sous charge.

Complement UI issu de `CC-IT-022`: le detail de ligne doit afficher la suite a
faire avant la matrice quatre sources. Le bloc `Action immediate` reste
prudent: il propose de tracer le controle local, sans valider le paiement ni la
comptabilite officielle. La matrice conserve ensuite les preuves et reserves.
La recette de cette tranche est validee dans l'executable `CoproScope.exe`, pas
dans un serveur web separe.

Complement executable/UI issu de `CC-IT-023`: le premier viewport compte comme
un vrai critere de recette dans `CoproScope.exe`. En largeur etroite, la coque
ne doit pas repousser le controle metier sous la ligne de flottaison: le lien
actif de navigation remonte en premier, la navigation reste compacte sur une
ligne au chargement, puis se deploie au survol ou au focus clavier. La preuve
finale doit mesurer l'ecran reel de l'executable, pas seulement lire le CSS.

Complement UI issu de `CC-IT-024`: dans une file de controle, la priorite
visuelle est `action prudente -> preuves -> contexte de piece`. La fiche PDF,
le fournisseur et le montant restent visibles, mais ils ne doivent pas
repousser l'action sous le premier ecran. Les libelles de retour evitent de
repeter le titre courant; ils disent ou l'utilisateur revient.

Complement executable/UI issu de `CC-IT-025`: la recette Controle des comptes
ne doit plus jamais etre presentee comme un module ComptaScope separe. Elle se
fait dans `CoproScope.exe`, avec la route `/comptes/rapprochement` ouverte par
l'executable. Le titre global peut rester `Controle des comptes`, mais le
header de travail doit nommer l'objet courant, par exemple `Ligne selectionnee
et preuves`, pour eviter de repeter deux fois le meme titre dans le premier
ecran. Les actions du header restent sur une ligne aux largeurs intermediaires
afin de ne pas repousser le bloc `Action immediate`.

Complement UI issu de `CC-IT-026`: un panneau repliable ne doit pas exposer le
marqueur technique natif du navigateur (`v`, triangle ou chevron non explique)
comme seule indication. Le libelle visible doit dire l'action utilisateur:
`Masquer le detail` quand le panneau est ouvert, `Afficher le detail` quand il
est replie. Cette regle vaut pour les autres modules: chaque repli utile au
premier ecran doit etre lisible par un membre novice du conseil syndical sans
comprendre les conventions HTML.

Complement UI/executable issu de `CC-IT-027`: aucun libelle principal visible
ne doit reprendre un nom de fichier brut ou un marqueur OCR/vide. Les exemples
rejetes sont `*.pdf`, `*.doc`, `*.xlsx`, `Facture Vid`, `Facture vide` et les
colonnes techniques comme `sha256,count,doc_ids,paths`. La page remplace ces
fragments par un libelle metier neutre (`Piece comptable a qualifier`) et garde
les identifiants de preuve internes (`DOC-*`) seulement comme ancrage
technique. La recette doit verifier l'instance reelle chargee par
`CoproScope.exe`, car les fuites de libelles apparaissent souvent dans la file
longue et pas seulement sur la ligne de demonstration.

Complement UI/executable issu de `CC-IT-028`: le tableau `Rapprochement 4
sources` est le coeur du controle. Dans le premier ecran de `CoproScope.exe`,
il doit commencer avant la fiche source detaillee: ordre cible `Action
immediate`, puis matrice quatre sources, puis contexte de piece. Le contexte de
piece reste disponible, mais il ne doit pas repousser la comparaison compta /
banque / facture / decision sous la ligne de flottaison. La recette mesure la
position reelle dans le navigateur integre et garde l'absence de libelles bruts.

Complement UI/executable issu de `CC-IT-029`: une matrice dite quatre sources
doit rester visuellement en quatre colonnes dans la fenetre executable quand la
largeur utile le permet. Le repli a deux colonnes est reserve aux largeurs
tres etroites, pas au poste de recette desktop. La recette verifie le style
calcule, les positions des quatre premieres cellules, l'absence de scroll
horizontal et l'absence de colonnes techniques visibles comme `doc_ids`.

Complement `CC-IT-030`: quand la fenetre est etroite mais encore exploitable en
desktop, la priorite est de montrer plus que le seul bord haut des cartes
source. Les textes longs de l'action et de la matrice peuvent etre contenus sur
une ou deux lignes, tant que les signaux utiles restent presents: action
immediate, reserve sur le paiement, quatre sources, banque non fournie et aucun
libelle technique.

Complement `CC-IT-031`: le haut de l'ecran ne doit pas consommer la hauteur
gagnee par la matrice. Sous 760px, l'en-tete de travail peut devenir plus dense
et limiter son texte d'aide a une ligne, tant que les signaux utiles restent
visibles: controle humain ouvert, retour aux comptes, action immediate, aucune
validation de paiement et banque non fournie. La recette de ce type de
changement doit verifier le paquet `CoproScope.exe`: un test source ou un
serveur web peut passer alors que le paquet embarque encore un ancien cache CSS.
Preuve cible de `CC-IT-031`: a 716 x 695 dans l'executable, en-tete de travail
61 px, matrice a 506 px, quatre colonnes de 155 px et aucun debordement
horizontal.

Complement `CC-IT-032`: sur `/comptes/rapprochement`, la barre du haut doit
servir le controle en cours. Elle remplace l'action globale `Nouvelle demande`
par `Tracer le controle` vers la zone de validation et masque la recherche
globale de documents sur cette route. Les autres pages gardent la recherche et
l'action globale.

## Limites

- Pas de saisie comptable complete.
- Pas de validation humaine simulee.
- Pas d'export de donnees reelles vers GitHub.
- Les comptes proposes sont des hypotheses de controle, pas une imputation definitive.
- Un rapprochement automatique reste une preuve candidate: les statuts `PROBABLE` et `PROBABLE_FORT` ne remplacent pas le grand livre ni la validation du conseil syndical.
