# Parcours utilisateur a tester de bout en bout - instance tests_ux

Date de creation: 2026-09-02.
Demande Brice du 2026-09-02: eprouver le produit sur un volume restreint de
pieces, avec une double entree par parcours.

Nommage: les parcours sont designes par une LETTRE (`Parcours A` a
`Parcours E`). Ne pas les numeroter: `V1`, `V2` se confondent avec les versions,
et `P1`, `P2` sont deja pris par les priorites de controle.

## Regle de mesure

Chaque parcours porte deux entrees, tenues separement:

- **Entree confrontation**: ce que CoproScope produit est compare a un resultat
  deja etabli a la main dans le dossier tilleul_pseudo. Sans etalon connu, la
  confrontation ne mesure rien.
- **Entree voie UX**: l'utilisateur peut-il aller au bout du parcours, sans
  aide, et sortir avec un livrable utilisable.

Un parcours n'est pas juge sur l'allure des ecrans mais sur ces deux sorties.

## Instance de test

- Emplacement: `C:\Users\brice\CoproScope\instances\tests_ux`.
- Mise en page `examples/synthetic_copro` (plate: `raw/`, `registers/`,
  `outputs/`), pas la structure en dossiers numerotes de tilleul_pseudo.
- Volume: 35 pieces. 30 vraies pieces copiees depuis Tilleuls (pseudo), 5 leurres
  deliberes.
- Les 5 leurres ne sont pas un accident: un `00_Index*.md`, un CSV de tableau de
  bord, un `.ps1`, un doublon `.md` d'un PDF deja present, un
  `DOC-xxxx.native.txt`. Ils mesurent le filtre a bruit, premier defaut constate.
- Pseudonymisation par `dev/tooling/scripts/pseudonymize_pdf_testbase.py` pour
  toute piece portant des noms de coproprietaires.
- Tilleuls (pseudo) reste en LECTURE SEULE. On copie, on ne monte jamais l'instance
  reelle dans le serveur.

Recueil des observations: le `Mode test` de la barre superieure est deja
l'instrument. Il ouvre `/recette`, permet d'annoter chaque page en cours de
parcours et exporte en JSON et Markdown. Rien a construire.

## Parcours A - Que dit cette AG, et qu'est-ce qui a ete vote

- Chemin: depot d'un PV, qualification, `/ag-contentieux`, registre des
  resolutions, rattachement d'une preuve, export.
- Pieces: 3 PV (AGE 21/02/2024, AGO 03/07/2024, AG 03/12/2025) et leurs
  convocations.
- Confrontation: **etalon corrige le 2026-09-04**. L'etalon publie ci-dessous
  etait FAUX sur tous ses points; voir la rectification qui suit. L'etalon reel,
  etabli a la main sur les sources primaires, est dans
  [`etalon_corpus_tests_ux.md`](./etalon_corpus_tests_ux.md): **55 resolutions au
  PV du 03/07/2024**, majorites 30 article 24, 23 articles 25 et 25-1, 1 article
  25B, 1 non enoncee. Issues: 39 adoptees, 7 rejetees, 8 `Pas de vote`, et **1
  dont le PV n'enonce jamais l'issue** - la resolution 28, budget 2024, dont les
  trois lignes de vote figurent mais dont la phrase de conclusion manque. Ce
  dernier cas est le piege naturel du parcours: un outil qui conclurait a
  l'adoption inventerait un vote. Mesure resolution par resolution: retrouvees,
  inventees, majorites correctes.

> **Rectification du 2026-09-04** - `RM-2026-0050`, lot `CONV-2026-2121`.
> Le texte precedent annoncait: 34 resolutions a l'AGE du 21/02/2024, toutes
> sous l'article 24, resolution 29 rejetee, resolutions 30 et 33 portant
> `Pas de vote`, devis BATIMEX 22 200,00 rejete et WE GROUP 18 240,00 adopte.
> Verification faite sur les sources primaires du coffre, **aucun de ces points
> ne tient**:
>
> - **le PV de l'AG du 21/02/2024 n'existe pas au dossier**, ni en source
>   primaire ni ailleurs. Le registre de constats du coffre le reclame lui-meme
>   comme piece a demander au syndic. Les `34 resolutions` ne reposent donc sur
>   rien;
> - le seul PV reellement disponible, celui du 03/07/2024, porte **55**
>   resolutions et non 34, et ses majorites ne sont pas toutes sous l'article 24;
> - la resolution 29 est **adoptee** - budget 2025 a 280 000,00 - et non rejetee;
>   la 30 est adoptee; la 33 est rejetee; **aucune** ne porte `Pas de vote`;
> - les montants 22 200,00 et 18 240,00 ne figurent dans **aucun** PV. Ils
>   proviennent de la convocation de fevrier 2024, un document scanne **sans
>   aucune couche de texte**, et la note d'audit qui les cite renvoie a des
>   numeros de ligne d'un fichier d'extraction qui ne contient aucun texte
>   extrait. C'est une citation sans source lisible.
>
> L'etalon publie melangeait donc deux assemblees et attribuait a un PV
> inexistant des issues appartenant a un autre document. Il est conserve ici
> barre plutot que supprime, parce que plusieurs documents s'y sont adosses -
> `strategie_lot_gouvernance.md` section 2, et le blueprint `RM-2026-0049`.
- Voie UX: 223 lignes AG en base et l'ecran `/actions` affiche
  `Aucune decision AG chargee`. Verifier que le parcours est franchissable.

## Parcours B - Controler les comptes avant l'AG

Priorite Brice au 2026-09-02. Detail du cheminement et des tests dans
[`parcours_b_controle_comptes.md`](./parcours_b_controle_comptes.md).

- Chemin: `/comptes`, rapprochement, factures a revoir, questions au syndic,
  export du rapport.
- Pieces: etat des depenses 2025, 12 factures qui s'y rapportent, 3 sans ligne
  correspondante.
- Confrontation: le total des charges est verifiable a la main sur l'annexe.
  L'interface annonce aujourd'hui 21 994 060,46 EUR.
- Voie UX: avec 15 pieces au lieu de 1 090, combien de points `P1 a traiter`.
  Si le compte reste a trois chiffres, le probleme n'est pas le volume mais la
  regle.

## Parcours C - Une piece manque: la demander, relancer, clore avec la preuve

- Chemin: `/pieces`, creer une demande syndic, `/demandes`, relance,
  `ajouter reponse recue`, cloture avec preuve.
- Pieces: 3 presentes, 4 deliberement absentes du corpus.
- Confrontation: le tableau doit lister exactement les 4 absentes, ni plus ni
  moins. Second etalon: la liste de pieces reclamees au syndic dans le dossier
  tilleul_pseudo.
- Voie UX: c'est la boucle qui fait tenir le produit et c'est la plus vide
  aujourd'hui, 0 partout alors que la barre laterale annonce 46 demandes.
  Verifier qu'une demande creee survit au rechargement, que la relance produit
  un brouillon copiable, que la reponse se rattache a la piece d'origine.

## Parcours D - Absorber un lot sans laisser entrer le bruit

- Chemin: `/documents/ajouter`, les 4 etapes annoncees, qualification,
  classement.
- Pieces: les 35, leurres compris, deposees d'un coup.
- Confrontation: matrice de confusion type par type contre la typologie etablie
  a la main. Les 5 leurres doivent finir en `A_CLASSER` ou rejetes. Aucun ne
  doit ressortir en `Contrat_Syndic` ni en `Devis`.
- Voie UX: l'ecran annonce `ETAPE 1 SUR 4`. Verifier que les quatre etapes
  s'enchainent et que les trois compteurs de documents convergent apres depot.

## Parcours E - Ce qui peut sortir, ce qui doit rester

- Chemin: `/confidentialite`, file de biffage, `/depot`, export.
- Pieces: 5, dont 2 portant des donnees personnelles pseudonymisees et 1 leurre.
- Confrontation: les 4 blocages affiches au tableau de bord sont aujourd'hui 4
  faux positifs sur des fichiers d'index. Mesurer faux positifs et surtout faux
  negatifs, une piece sensible qui passerait.
- Voie UX: le blocage est-il comprehensible et levable par un humain, ou est-ce
  un mur sans porte.

## Ordre recommande

Parcours A d'abord, parce que c'est le seul dont la verite est etablie ligne a
ligne et qu'il donne une mesure plutot qu'une impression. Parcours B ensuite,
parce que le total a 22 millions est le defaut qui detruit la confiance en une
seconde et que sa cause est bornee.

## Reserve prealable

Trois defauts constates ne sont pas des defauts d'UX mais de donnees, et ils
fausseront toute mesure de parcours tant qu'ils tiennent:

1. `server/src/coproscope/vault/public_actions_read_model.py:73` retourne `[]`
   quand la base de projection est absente, au lieu de lever
   `PublicReadModelUnavailable`. Le modele public vide gagne alors sur le modele
   construit sur les registres. C'est ce qui vide `/actions`, `/pieces` et
   `/exports/actions.csv` pendant que le cockpit annonce 93 actions.
2. Les fichiers d'outillage du coffre entrent au registre comme pieces: 199
   `.md`, 115 `.csv`, 21 `.json`, 8 `.ps1`.
3. La meme piece compte quatre fois: le PDF, sa conversion `.md`, son extraction
   `DOC-xxxx.native.txt` et une seconde copie.

A trancher avant de lancer: corriger ces trois points d'abord, ou les mesurer
tels quels pour disposer d'un point de depart chiffre.
