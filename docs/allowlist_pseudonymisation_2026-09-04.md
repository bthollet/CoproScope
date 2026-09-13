# Allowlist justifiee de la garde de pseudonymisation

Lot `RM-2026-0062` / `CONV-2026-2127`, 2026-09-04.

Ce document ne contient aucune donnee personnelle, aucun motif reel, aucun nom
de coproprietaire, de fournisseur ou de fichier d'instance. Les motifs examines
et les tables de correspondance vivent hors depot, dans la zone privee de
l'instance concernee.

## Le probleme

L'outil local de pseudonymisation de PDF (`dev/tooling/scripts/`) se termine par
une garde de sortie. Deux pieces de reference du corpus de test ne pouvaient pas
entrer dans ce corpus: la garde detectait des motifs residuels et supprimait le
fichier produit, alors qu'aucun de ces motifs n'etait une identite. C'etaient des
references de pieces comptables et des intitules de postes du plan comptable.

Le probleme n'est pas propre a ces deux pieces. Une reference de facture
fournisseur a la meme forme qu'une reference de contrat, et un nombre de huit ou
neuf chiffres a la meme forme qu'une immatriculation d'entreprise. Le meme faux
positif se reproduira chez le prochain syndic, avec d'autres prefixes et d'autres
longueurs.

## Comment fonctionne la garde, en trois phrases

Une fois le PDF pseudonymise ecrit, la garde relit le texte selectionnable du
fichier produit et, si l'option de controle visuel est active, le texte rendu par
OCR, puis elle confronte chaque ligne a une table de familles de motifs
reglementaires: adresse electronique, telephone, civilite suivie d'un nom, IBAN,
SIRET, adresse postale, identifiant technique, reference de contrat,
immatriculation, code postal, et plusieurs familles qui verifient qu'une ligne
attendue comme masquee porte bien une etiquette de pseudonyme. Chaque famille est
une expression reguliere de forme, pas de sens: elle reconnait la silhouette d'un
identifiant, jamais son contexte comptable ou juridique. Des qu'une famille
compte au moins une occurrence, la garde supprime le fichier produit et rend un
statut d'echec, ce qui protege bien contre une fuite mais ne distingue pas une
identite d'une reference de piece qui lui ressemble.

## Ce que fait l'allowlist

Un journal declare, entree par entree, qu'un motif exact a ete examine sur une
piece precise et qu'il n'est pas une identite. Chaque entree porte cinq champs
obligatoires: la piece, la famille de motifs, le motif exact, la raison de son
innocuite et l'horodatage de l'examen; un sixieme champ nomme qui a examine.

- La garde continue de detecter et de signaler **tous** les motifs. L'allowlist
  n'intervient qu'apres la detection, pour trier ce qui bloque de ce qui ne
  bloque plus.
- Le rapport de sortie dit, par famille, combien de motifs ont ete detectes,
  combien ont ete leves et combien restent bloquants. Un lot ne peut donc pas
  faire disparaitre une famille du rapport en l'inscrivant.
- Une entree ne vaut que pour la piece ou elle a ete examinee. Le meme motif sur
  une autre piece bloque de nouveau et demande un nouvel examen.
- Une entree ne vaut que pour la famille ou elle a ete examinee.
- Le motif est compare litteralement, espaces normalises et casse respectee.
  Aucune entree ne peut lever une famille entiere.
- Une piece generique (`*`, `all`, `tous`, ...) est refusee au chargement. Une
  entree incomplete est refusee. Un journal illisible ou absent est signale et ne
  leve rien.
- Le statut de sortie devient explicite des qu'une entree a servi, et chaque
  application est ecrite dans un journal CSV d'application: quelle entree, quelle
  piece, combien d'occurrences, quand.

## Ce que l'allowlist ne fait pas

- Elle ne modifie aucune expression reguliere de detection. La garde d'une piece
  qui n'a pas de journal se comporte exactement comme avant.
- Elle n'accepte pas une famille de motifs par exception globale. C'etait l'issue
  ecartee par l'arbitrage: elle aurait affaibli la garde pour tous les documents a
  venir, y compris ceux ou un tel motif serait une vraie identite.
- Elle ne masque rien et ne repare rien dans le document. Un motif leve reste en
  clair dans la piece, ce qui est precisement l'objectif quand ce motif porte la
  mesure attendue du test.
- Elle ne dit pas qu'un motif est anodin. Elle dit qu'un humain ou un agent l'a
  regarde, a ecrit pourquoi, et a signe la date. La qualite de la protection
  reste celle de l'examen.
- Elle ne corrige pas les faux negatifs de la detection, voir plus bas.

## Generalisabilite: ce qui est suppose invariant, ce qui est traite comme variant

**Invariant, donc code en dur dans le mecanisme:**

- une garde de forme produit des faux positifs, et cela ne se corrige pas en
  ajoutant des formes;
- le contexte qui distingue une reference de piece d'une identite est local au
  document et n'est pas exprimable par une expression reguliere: il faut un
  examen;
- un examen non trace ne vaut rien; la raison et l'horodatage font partie de la
  decision, pas de sa documentation;
- une decision d'examen ne se generalise pas d'elle-meme d'un document a un
  autre: la portee par defaut est la piece;
- le detail examine est de la donnee d'instance et n'a rien a faire dans un
  depot partage.

**Variant, donc jamais fige:**

- les prefixes, longueurs et formats de references comptables, qui dependent du
  logiciel du syndic et changent d'un cabinet a l'autre;
- les intitules de postes du plan comptable, qui dependent du parametrage;
- les familles de motifs elles-memes, qui peuvent etre ajoutees ou reglees sans
  toucher au mecanisme d'allowlist;
- la composition d'un corpus de test et le nombre de motifs a examiner.

Consequence pratique pour un deploiement chez un autre syndic: le mecanisme se
transporte tel quel, le journal ne se transporte pas. Reprendre un journal d'une
copropriete pour une autre reviendrait a recreer l'exception globale que
l'arbitrage a refusee.

## Une limite mesuree: l'allowlist ne se transporte pas au controle OCR

La garde tourne a deux etages: le texte selectionnable du fichier produit, et,
quand le controle visuel est demande, le texte relu par OCR sur le rendu des
pages. Le mecanisme d'allowlist est branche sur les deux, mais il n'est utile que
sur le premier.

Mesure faite sur une piece comptable de trente-cinq pages: au premier etage, tous
les motifs residuels sont leves et rien ne bloque. Au second, vingt-trois motifs
supplementaires bloquent, et **aucun n'est une identite**: ce sont des lignes de
points de conduite lues comme des suites de chiffres, et des montants agglomeres
a leur ligne de total. Le motif exact n'est pas stable: il depend de la
resolution de rendu, de la version du moteur OCR et du hasard de la lecture.

Consequence a tenir: inscrire ces motifs reviendrait a remplir le journal de
bruit, et le bruit d'aujourd'hui ne serait plus celui de demain. Sur un document
dense en lignes de conduite, le controle visuel demande donc un autre reglage que
l'allowlist, par exemple ignorer les suites issues de caracteres de remplissage.
Tant que ce point n'est pas traite, une piece de ce type est produite et verifiee
au premier etage seulement, comme le reste du corpus, et le controle visuel reste
un `RM-*` a part.

## Un defaut distinct, et plus grave, constate au passage

Le mecanisme traite le cas ou la garde est trop stricte. L'examen des deux pieces
a montre l'autre bord du meme defaut: la garde est aussi **incomplete**. Un
patronyme ecrit en capitales, sans civilite ni ponctuation, au milieu d'un libelle
comptable, ne declenche aucune famille de motifs. Sur la premiere piece traitee,
trois patronymes reels se trouvaient dans ce cas: ni l'etape de masquage
automatique ni la garde ne les avaient vus. Ils n'ont ete masques que parce
qu'un examen manuel les a cherches, colonne par colonne.

Sur la seconde piece, un document d'assemblee de cent quarante-trois pages, le
meme defaut apparait a une tout autre echelle. Une de ses annexes est un tableau
nominatif des soldes de comptes: une ligne par coproprietaire, nom puis prenom
puis le solde individuel. Aucune civilite ne precede les noms. Ni la detection ni
la garde n'en voient un seul: **cent quarante-six patronymes y restent en clair,
chacun accole a la dette de la personne**, et le rapport de sortie n'en dit rien.
Ce n'est pas un effet de la table revue: le defaut est identique avec la chaine
automatique d'origine.

Trois consequences a tenir:

1. le corpus de test reste une donnee d'instance privee, non publiable, et le
   restera tant que la detection des patronymes sans civilite n'est pas traitee;
2. un statut de sortie favorable ne prouve pas l'absence d'identite. Il prouve
   l'absence de motif connu. C'est un `RM-*` distinct a ouvrir, et il est plus
   grave que celui-ci;
3. et surtout, pour cette piece precise, **les faux positifs de la garde sont
   aujourd'hui la seule chose qui l'empeche d'entrer dans le corpus avec ce
   tableau nominatif**. Ses motifs residuels ont donc ete examines, documentes
   dans le journal prive, et deliberement **non inscrits**: les inscrire aurait
   leve le seul verrou qui restait. Une allowlist se refuse aussi. C'est le cas
   ou l'examen conclut que le motif est anodin mais que la piece ne l'est pas.

Un second defaut, au stade du masquage cette fois, et de loin le plus couteux.
La detection automatique reconnait des formes, elle aussi, et elle se trompe dans
les deux sens. Sur une piece comptable dense, elle classe des references de
pieces fournisseurs comme immatriculations ou comme identifiants bancaires et les
remplace: le document sort ampute de ce que le test devait mesurer. Sur un
document de prose longue, c'est pire: mesure faite sur une convocation
d'assemblee de cent quarante-trois pages, **environ 5 400 des 6 099 etiquettes
posees remplacent du vocabulaire courant** et non des identites. Les deux
articles definis pluriels y passent pres de trois mille fois, le mot qui designe
l'acte de voter cent cinquante-neuf fois, et les deux articles de la loi de 1965
qui fixent les regles de majorite quatre-vingt-seize fois. Une convocation dont
les regles de majorite et le mot `vote` sont pseudonymises ne mesure plus rien.

La cause est cumulative: la table d'alias est partagee entre les pieces, et
chaque passe automatique y ajoute ses faux positifs, que la passe suivante
applique comme des regles etablies. Une valeur de trois lettres inscrite par
erreur devient une substitution appliquee partout, dans tous les documents
suivants.

Deux paliers de parade, employes ici, tous deux hors du mecanisme d'allowlist:

- sur la piece comptable, desactiver la detection automatique et declarer
  explicitement les identites a masquer, apres enumeration colonne par colonne;
- sur le document de prose, revoir la table d'alias avant emploi: garder les
  entrees de forme verifiable et les patronymes du registre, retirer les entrees
  de vocabulaire, et verifier automatiquement qu'aucune entree retiree ne
  contient un patronyme connu.

Ces deux parades sont manuelles et ne se generalisent pas. Ce qui se generalise,
c'est le constat: **une table d'alias partagee entre documents doit etre revue
avant d'etre reutilisee, et une entree auto-detectee ne devrait jamais entrer
dans la table partagee sans examen.** C'est un `RM-*` distinct, et il conditionne
la valeur de tout corpus construit avec cet outil.

## Ou vivent les journaux

Dans la zone privee `restricted/` de l'instance concernee, hors depot Git:

- le journal d'allowlist, au format JSON, qui porte les entrees examinees;
- le journal d'application, au format CSV, ecrit par l'outil a chaque fois
  qu'une entree leve effectivement un blocage;
- les tables de correspondance valeur reelle vers pseudonyme, comme avant.

Le rapport de sortie de l'outil, lui, ne recopie jamais un motif: il ne donne que
des noms de familles et des comptes. Il peut donc rester dans un manifeste non
sensible.

## Tests

Le mecanisme est couvert par des tests dedies, a cote de ceux de l'outil. Ils
verifient qu'un motif inscrit est leve, qu'un motif non inscrit bloque toujours,
qu'une entree inscrite pour une piece ne leve rien sur une autre piece, qu'une
entree inscrite pour une famille ne leve rien sur une autre famille, que les
entrees generiques ou incompletes sont refusees et signalees, que le rapport
compte correctement detectes, leves et bloquants, que l'application est
journalisee, et que le rapport ne recopie jamais le motif.

Commande:

```powershell
C:\Users\brice\CoproScope\coproscope\server\.venv\Scripts\python.exe `
  -m unittest test_pseudonymize_pdf_testbase test_pseudonymize_pdf_allowlist -v
```

a lancer depuis `dev/tooling/scripts/`.
