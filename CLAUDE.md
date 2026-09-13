# Consignes agents CoproScope

Ce depot peut etre travaille par plusieurs agents en parallele, a condition de ne pas partager le meme arbre de travail pour des modifications concurrentes.

## Regle courte

- Un agent = une branche `codex/<sprint>-<scope>` = un worktree dedie.
- Un agent possede un perimetre de fichiers explicite.
- Non-blocage par defaut: un chantier isole dans son worktree, sa branche ou
  son perimetre ne doit pas arreter les autres chantiers. Un agent se gare
  seulement sur conflit concret: `main` sale dans son propre arbre de travail,
  fichier partage effectivement touche par deux owners, protocole `WAIT_MERGE`
  reel, serveur durable ambigu, instance privee affectee, ou demande explicite
  du coordinateur. Ne pas attendre "tous les autres chantiers" si ces conditions
  ne sont pas reunies.
- Aucun fichier de code ne doit depasser 600 lignes. Cette limite s'applique
  aux sources applicatives, tests, templates, CSS, scripts et configurations
  maintenus dans le depot. Si un fichier depasse 600 lignes, le chantier
  prioritaire est de l'extraire en modules/includes/helpers coherents avant
  d'ajouter de nouvelles fonctionnalites. Les documents historiques longs et
  assets binaires ne sont pas du code, mais tout nouveau document de pilotage
  doit rester aussi decoupe que possible.
- Tout BOT-END de refactor ou de livraison code doit inclure un comptage final
  prouvant qu'aucun fichier code suivi par le garde-fou local ne depasse 600
  lignes, ou signaler explicitement le reliquat et son `RM-*`.
- Les instances privees restent hors depot et ne sont jamais commitees.
- Les sorties publiables utilisent l'instance synthetique ou une copro demo fictive hors Drive.
- Le packaging desktop courant est un executable Windows PyInstaller avec
  pywebview: `CoproScope.exe` ouvre une fenetre CoproScope dediee, tout en
  gardant `--browser` comme secours et `--no-browser` pour les smokes. Ne pas
  migrer vers Electron/Tauri ni restructurer le repo sans arbitrage explicite.
  La reference dev est `docs/runbook_packaging_noob_windows.md`.
- **Instance fraiche par lot, et aucune instance historique comme etalon.**
  Convention Brice du 2026-09-03. Un lot de dev ou de mesure cree son instance
  dediee au lieu de reutiliser une instance existante. Instance fraiche ne veut
  pas dire vide: quand l'epreuve en pleine charge est exigee, copier une
  instance chargee vers un dossier propre au lot et travailler sur la copie.
  L'instance appartient au lot comme le port et les fichiers: elle est nommee
  dans le contrat d'agent, tracee dans `docs/presence_agents.md` et citee dans
  le `BOT-END`.
  Motif verifie le 2026-09-03: une instance de recette partagee portait au meme
  moment un serveur de recette qui ecrivait 110 lignes dans
  `vault_local/gouvernance.sqlite3`, un audit de pages et une confrontation de
  classement. Un compteur qui bouge entre deux passages sans que l'observateur
  ait rien fait rend la mesure ininterpretable, et reproduit le defaut numero
  un du produit: plusieurs comptages concurrents pour la meme notion.
- **Gros changement: instance VIDE et reabsorption des documents, jamais une
  copie chargee.** Convention Brice du 2026-09-07, qui precise la regle
  precedente au lieu de la remplacer. Pour une correction bornee, copier une
  instance chargee vers un dossier propre au lot reste valable. Des qu'un lot
  touche la chaine d'absorption - classement, extraction, completude, typage,
  liens, biffage, identite des documents ou des personnes - la copie chargee
  devient une preuve creuse.
  **Motif, et il est le meme que celui du venv partage:** une instance chargee
  porte la SORTIE de la version precedente du code. La reutiliser fait entrer
  cette sortie comme si elle etait une entree, donc le lot mesure son propre
  ancetre au lieu de mesurer les pieces. Le defaut ne fait echouer aucun test:
  il deplace la base. Une instance vide qui reabsorbe les pieces d'origine est
  la seule qui eprouve la chaine entiere, du document brut au chiffre affiche.
  **Instance vide ne veut pas dire instance fictive.** Precision de Brice du
  2026-09-07: `examples/synthetic_copro` est un exemple partageable, pas un
  etalon. Une instance fraiche est une instance VIDE que l'on RECONSTRUIT a
  partir du corpus reel de travail - `Tilleuls (pseudo)` - en n'y copiant que la
  configuration et les pieces SOURCES, jamais les registres ni les sorties.
  Une epreuve menee sur l'instance synthetique prouve que la chaine tourne;
  elle ne prouve rien sur ce qu'elle lit, parce que les pieces synthetiques
  ont ete ecrites pour passer. Les tests du depot restent sur l'instance
  synthetique - la CI n'a pas le droit de lire une instance privee - et cette
  limite se declare au lieu d'etre presentee comme une preuve de justesse.
  **Consequence pratique:** le `BOT-END` d'un lot qui touche l'absorption doit
  citer l'instance creee, les pieces reabsorbees et leur nombre. Une preuve
  obtenue sur `examples/synthetic_copro` ou sur une copie chargee se declare
  comme telle et ne vaut que pour la non-regression, jamais pour la justesse.
- **Un extracteur se concoit sur des AXES de generalisation, jamais sur des
  modalites observees.** Regle dure posee par Brice le 2026-09-04. Elle
  s'applique a tout extracteur, tout classifieur et toute regle de
  reconnaissance.
  Deux observations ne definissent pas une enumeration, elles revelent une
  **dimension**. Ecrire `si le separateur est "." ou ")"` code deux points vus
  et casse au troisieme syndic. Nommer l'axe - `la maniere dont le numero est
  separe de son objet est un degre de liberte` - puis dire ce qui reste vrai le
  long de l'axe - `un numero precede toujours un objet` - produit un code qui
  tient.
  **Test d'acceptation, a appliquer avant de livrer:** si un troisieme syndic
  arrivait demain avec une valeur inconnue sur cet axe, le code se degrade-t-il
  proprement, ou produit-il une reponse fausse en silence ? La seconde reponse
  signifie qu'on a code des modalites.
  **Livrable obligatoire de tout lot d'extraction:** une section nommant, pour
  chaque difference constatee entre coproprietes, (1) l'axe, (2) ce qui reste
  invariant le long de l'axe, (3) ce que le code en fait, (4) ce qui se passe
  hors des valeurs observees.
  **LA MEME REGLE VAUT POUR CE QUI VERIFIE, et elle y est plus dangereuse.**
  `RM-2026-0106`. Ce qui precede est redige pour les EXTRACTEURS; la regle
  s'applique identiquement aux tests, aux gardes, aux controles et aux
  garde-fous d'outillage. **Le mode de defaillance n'est pas le meme des deux
  cotes:** un extracteur qui code des modalites rend une reponse fausse, ce qui
  finit par se voir; une garde qui code des modalites rend une **fausse
  tranquillite**, et celle-la est indetectable par construction. Sur sept
  occurrences recensees en une nuit, quatre n'ont ete trouvees que parce
  qu'autre chose avait casse a cote.
  **Seconde question du test d'acceptation, propre aux gardes: quand cette
  garde cessera d'etre vraie, comment l'apprendra-t-on ?** Si la reponse est
  *un autre test tombera* ou *quelqu'un le remarquera*, la garde est ecrite sur
  des modalites. Une garde mesure ce qu'elle protege LA OU cela vit - le
  `<main>` d'une page et non son document, le type d'un volume et non le nom
  d'un dossier, la valeur d'un scope et non le mot - et **sa portee se derive
  de l'arborescence reelle, jamais d'une liste ecrite une fois.**
  **Corollaire operationnel: le silence d'une garde n'est une preuve que si
  l'on sait ou elle regarde.**
  **UNE AUTRE FAUTE, DE MEME FAMILLE: reduire a un SCALAIRE ce qui est une
  TABLE.** `RM-2026-0160`, formulation retenue avec `CONV-2026-2172`. Coder une
  modalite, c'est enumerer les valeurs vues sur un axe; reduire a un scalaire,
  c'est **effacer un axe entier** en le faisant tenir dans un seul nombre ou un
  seul libelle.
  **Trois cas mesures dans ce depot, a deux etages differents:**
  - une colonne *Execution* qui confond l'argent et la chose, alors que
    *toutes les combinaisons existent* - paye non fait, fait non paye,
    partiellement l'un et l'autre - et qu'aucune ne se deduit de l'autre;
  - une colonne *reste a financer* qui ecrase un plan de financement, lequel
    est une table assemblant plusieurs sources sur une meme depense - aides,
    pret 46-1, eco-PTZ (`RM-2026-0166`);
  - un `max()` applique a des quantites de sens different, qui rend un nombre
    en **effacant la source gagnante** (`RM-2026-0134`, corrige le 2026-09-12:
    la valeur est gardee, et **tous les candidats avec elle**).
  **TEST D'ACCEPTATION, a appliquer a toute valeur affichee:** *deux etats
  differents du dossier peuvent-ils produire le meme affichage, sans qu'on
  puisse remonter de l'affichage aux etats ?* Si oui, une table a ete reduite a
  un scalaire, et **ce qui manque ne se voit pas** - c'est ce qui distingue
  cette faute d'une simple imprecision.
  **Ce qui ne repare pas:** ajouter une seconde colonne au hasard. La reparation
  consiste a **nommer les dimensions independantes**, puis a garder de quoi
  remonter - la source, les candidats, le detail - a cote de la valeur
  composee.
  **Cas d'ecole du 2026-09-12, et il produit la panne SYMETRIQUE - la fausse
  alerte.** `server/tests/test_fondements_juridiques.py` designait le registre
  des sources legales **par son chemin**. Le depot en portait deux. La garde
  n'a jamais signale qu'elle n'en lisait qu'un: elle a simplement compte
  **24 identifiants en dette** la ou il y en avait **19**, les cinq autres
  etant declares, avec version et date de lecture, dans le registre qu'elle
  ignorait. Reparation conforme a la regle: les registres se decouvrent par
  leur **forme** - un module exposant un `SOURCES: dict[str, Source]` - et un
  temoin de mutation verifie qu'un troisieme registre, que rien ne nomme, est
  lu le jour de sa creation.
  **ET LA REGLE VAUT POUR LES INSTRUMENTS DE MESURE, ou elle est plus
  dangereuse encore.** Un extracteur faux produit des lignes fausses qu'on peut
  relire; **un compteur faux produit un chiffre qui a l'air d'une preuve.**
  **Test a appliquer a tout compteur avant de publier son resultat:
  le chiffre changerait-il si la chose comptee disparaissait ?** Si la reponse
  est non,
  l'instrument mesure sa propre definition. Deux cas attestes: un comptage dont
  les mots-cles incluaient `sources`, colonne presente presque partout - il
  mesurait sa propre liste et concluait 52 sur 52; et une recherche exhaustive
  menee avec un predicat faux - `la chaine apparait quelque part` pris pour
  `le numero designe un item` - dont **l'exhaustivite rendait la conclusion
  plus credible, pas moins**. La contre-mesure n'est donc pas d'elargir la
  recherche, c'est deja ce qui trompe: **enoncer le predicat avant de
  chercher**, et verifier qu'il porte sur ce qu'on veut savoir.
  **Troisieme cas, du 2026-09-12: un zero total est un symptome d'instrument,
  pas un resultat.** Une mesure de sept mises en page a rendu `0/7`; le point
  d'entree etait le bon, mais sa sortie - des couples `(compte, nom)` - etait
  mal lue. La vraie valeur etait `7/7`, et le chiffre faux allait inscrire une
  regression inexistante. Un defaut reel epargne des cas; un instrument casse
  n'en epargne aucun. **Avant de publier un zero uniforme, faire passer a
  l'instrument un cas dont la reponse est connue.**
  Corpus disponibles pour l'epreuve: le corpus de travail `Tilleuls (pseudo)` et
  le corpus `Erables (pseudo)`
  (22 PDF d'un second cabinet, quatre exercices; son dossier local se nomme dans
  le contrat d'agent, jamais ici). Travailler sur le premier sans
  eprouver sur le second n'est pas conforme.
  **Cas d'ecole verifie, un echec puis sa correction.** Le lot classement du
  2026-09-04 avait mesure 0 signature sur 6 pour les faux PV du corpus de travail
  contre 2 a 3 sur 6 pour la vraie matiere d'assemblee, et en avait tire un
  seuil `au moins 2 signatures = PV`. C'etait une variable a modalites. Le
  second cabinet l'a refute en une mesure: ses quatre convocations marquent 2 a
  3 sur 6, exactement dans la plage. Ce qui a survecu est l'invariant trouve
  ensuite - le titre `proces-verbal de l'assemblee` ancre dans les premiers
  caracteres, fonde sur le decret 67-223 et non sur l'habitude d'un cabinet:
  zero faux positif sur 37 documents et deux cabinets.
  Corollaire deja constate: un temoin de vocabulaire de domaine est un
  **variant deguise en invariant**. `copropri`, `syndic`, `resolution`, `vote`
  apparaissent dans 539 des 1090 documents d'un coffre - ils ne discriminent
  rien.
- **Les instances historiques ne sont pas fiables.** Arbitrage Brice du
  2026-09-03: les instances de recette accumulees depuis mai 2026 et
  les instances de recette accumulees depuis mai 2026 ont subi de tres
  nombreuses variations. Elles ne peuvent pas servir d'etalon.
  Y restent mesurables les defauts qui ne dependent pas de la verite des
  donnees: hauteur de page et premier viewport, identite fictive sur donnees
  reelles, formats de montants incoherents, ecran vide silencieux, motif
  repete a l'identique, coherence interne des compteurs, vocabulaire et
  accessibilite.
  N'y sont PAS mesurables: la justesse d'un total, le nombre de resolutions
  d'une assemblee, le rattachement d'une facture a une ligne de depenses, le
  taux de faux positifs d'un classement. Tout constat de cette nature se
  publie avec sa reserve, jamais nu.
  La seule reference de verite est un corpus construit pour cela, avec son
  etalon etabli **a la main avant tout traitement outil**: `instances/tests_ux`
  et `docs/etalon_corpus_tests_ux.md` (`RM-2026-0050`). Les pieces d'un tel
  corpus se copient depuis les sources primaires, jamais depuis une instance
  deja retraitee.
- Pour une recette live ou un agent qui ne mesure aucune justesse, l'instance
  de depart est **une copie fraiche de l'instance privee de travail**, choisie
  copiee vers une instance de lot; l'instance Platanes
  `examples/synthetic_copro` reste reservee aux tests publics/CI et aux
  exemples partageables.
- Le coordinateur integre les branches une par une et relance les tests.
- Toute branche de developpement suit
  [`docs/methode_developpement_branches.md`](./docs/methode_developpement_branches.md):
  d'abord un bloc d'enquete, puis un bloc doc + dev en mode plan et objectifs.
- Pour une nouvelle feature produit ou une feature transverse, le bloc
  d'enquete est obligatoire avant tout code applicatif. Il doit produire au
  minimum: probleme utilisateur, perimetre/hors perimetre, blueprint de service
  ou blueprint UI selon le cas, event storming ou parcours-evenements, contrat
  de donnees, risques privacy/licence, criteres d'acceptation, tests attendus et
  gate GO/NO-GO avant dev. Si ces elements manquent, les devs restent en
  lecture seule; tout code deja esquisse reste hors validation produit jusqu'a
  reprise de la sequence correcte.
- Apres ce cadrage, une nouvelle feature doit mobiliser une equipe d'agents
  selon `docs/strategie_equipes_multi_agents.md`. Le fait qu'un fichier ait un
  owner unique ne remplace pas l'equipe: expert domaine, QA/privacy, novice ou
  designer selon le routage doivent rendre un retour trace avant tout statut
  `PRET_A_INTEGRER`.
- **Magasin unique des donnees de gouvernance: SQLite, jamais un nouveau
  registre CSV.** Arbitrage Brice du 2026-09-03. Les resolutions d'assemblee,
  les seuils, les delegations et les liens entre objets s'ecrivent dans le
  coffre SQLite local, sous `settings.vault.local_root`. Les registres CSV
  existants restent en place et ne sont pas migres sans demande explicite; la
  regle porte sur ce qui est ajoute.
  Motif verifie: la table de liens `object_links` vit deja en SQLite avec
  `event_id` dans sa contrainte UNIQUE, ce qui laisse coexister plusieurs
  assertions sur un meme couple - le syndic affirme, CoproScope calcule, un
  humain confirme ou contredit. Une colonne de registre ne sait pas faire cela.
  Et trois conversations qui ecriraient chacune dans un magasin different
  reproduiraient le defaut numero un du produit, constate le 2026-09-02 sur
  l'interface reelle: quatre comptages concurrents pour la meme notion.
  Deux consequences a tenir:
  - ne pas ecrire dans la base de reconstruction ce qui ne passe pas par le
    journal d'evenements. **Correction mesuree le 2026-09-08, cette consigne
    disait faux et le vrai danger est pire.** `_reset_schema` est bien appele a
    chaque reconstruction, mais c'est une **liste explicite de
    `DROP TABLE IF EXISTS`**, et la base n'est jamais supprimee: une table
    absente de cette liste **survit a tous les rebuilds**, verifie sur deux
    reconstructions successives. Le defaut n'est donc pas une perte differee -
    ce serait presque une chance, une perte finit par se voir. C'est une
    **desynchronisation muette**: la table garde ses lignes pendant que tout
    autour se reconstruit depuis les evenements, et rien ne signale la
    divergence. Corollaire: cette liste de `DROP` est **elle-meme une
    enumeration de modalites**, donc la prochaine table ajoutee a la projection
    sans etre ajoutee a la liste tombera dans le meme trou;
  - une donnee derivee et une donnee saisie par un humain ne se rangent pas
    ensemble. Une re-extraction remplace ce qu'elle a produit et rien d'autre:
    les lignes d'origine `CORRIGE_HUMAIN` survivent.
- Le gouvernail roadmap unique est
  [`docs/roadmap_backlog_central.md`](./docs/roadmap_backlog_central.md).
  Toute demande "ajoute ceci a la roadmap" y est inscrite en `RM-*`.
  Les anciennes roadmaps/backlogs ne sont plus des sources de pilotage actives.
- Tout chantier actif doit avoir une ligne vivante dans
  [`docs/presence_agents.md`](./docs/presence_agents.md), avec owner,
  worktree/branche, lease ou point de reprise et statut.
- Le travail multi-agent n'utilise plus de couche CO/CE ni de file de jetons.
  La conversation courante reste le fil pilote: elle lit le gouvernail
  [`docs/roadmap_backlog_central.md`](./docs/roadmap_backlog_central.md),
  verifie `docs/presence_agents.md`, choisit ou reprend une seule tache du
  backlog `ORD-*`, puis cree des sous-agents avec des roles explicites si
  l'outil de sous-agents est disponible. Un sous-agent recoit directement:
  role, mission, ownership modifiable, fichiers evites, tests/preuves attendus,
  format de rendu et condition d'arret. Aucun jeton `CEJ-*`, alias `CE-*`,
  claim ou file intermediaire ne doit etre cree. Si la capacite de sous-agents
  manque, le fil pilote le dit clairement et execute les roles sequentiellement
  dans des sections nommees, sans pretendre qu'ils sont actifs.
  L'identifiant interne `ORD-*` designe une tache du backlog et doit etre
  explique comme tel a Brice.
  [`docs/tableau_execution_courant.md`](./docs/tableau_execution_courant.md)
  est archive: ne plus publier ni attendre de `SLOT-*`.
- Quand Brice dit `lance un orchestrateur`, `lance une equipe`, `lance une
  equipe agile`, `lance une equipe UX/UI` ou une variante proche, appliquer
  [`docs/orchestration_agents.md`](./docs/orchestration_agents.md):
  le fil pilote s'appuie d'abord sur l'objectif actif Claude (`/objectif`) et
  sur `docs/presence_agents.md`. Les outils `orchestration-watch` et
  `orchestration-supervise` sont des diagnostics manuels, pas des relances
  permanentes. Le fil reprend le `CH-*` vivant si le travail n'est pas fini, ou
  choisit la prochaine tache du backlog si le dispatch est autorise. Il
  applique le routeur d'equipe, trace `ROUTAGE_EQUIPE` dans
  `docs/presence_agents.md`, puis genere les sous-agents correspondant aux
  roles du type d'equipe demande. Quand un ancien prompt dit `lance un worker`
  ou `lance une CE`, le convertir en sous-agent role dans le fil pilote; ne
  jamais recreer de file de jetons ni de conversation esclave.
- Les commandes `ceci est une CE`, `ceci est une CE coproscope`,
  `active le protocole CE`, `lance le protocole CO` et `active le protocole CO`
  sont des commandes legacy. Elles doivent etre recadrees vers le modele
  actuel: fil pilote + sous-agents par roles, sans script `ce-claim`, sans
  alias CE et sans jeton.
- Quand Brice demande une equipe multi-agents, appliquer d'abord
  [`docs/strategie_equipes_multi_agents.md`](./docs/strategie_equipes_multi_agents.md):
  preflight anti-collision, choix automatique de l'equipe-type
  `INCIDENT_STATIONNEMENT`, `FANIN_CONSOLIDATION`, `RECHERCHE_METIER`,
  `UXUI_RECHERCHE`, `AGILE_UI_PRODUIT`, `BACKEND_DOMAINE`,
  `RECETTE_LIVE_QA`, `INTEGRATION_RELEASE` ou `DOCTRINE_SIDEQUEST`, puis un
  seul `CH-*` par tache du backlog, des owners vivants uniques et une trace
  `ROUTAGE_EQUIPE` dans `docs/presence_agents.md`. Le routeur donne ensuite
  les sous-agents correspondant aux roles du type d'equipe retenu, avec mission,
  ownership, fichiers evites, condition d'arret et format de rendu. Si le
  routeur choisit
  `AGILE_UI_PRODUIT`, appliquer
  [`docs/protocole_equipe_agile_agents.md`](./docs/protocole_equipe_agile_agents.md):
  coordinateur-scribe, designer/facilitateur, utilisateur novice, dev front,
  dev back/viewmodel, QA et, si la capacite de threads le permet, testeur
  expert metier juridique/compta/process chantier/syndic, avec flux decale UI
  reelle -> visuel IA et blueprint designer -> qualification novice -> dev ->
  test produit. A chaque iteration UI, le designer/facilitateur produit un
  visuel genere par IA et un blueprint visuel avant le dev. Le visuel IA est une
  brouillon HTML de l'ecran complet, cliquable, pas un SVG, pas une icone
  et pas un schema partiel; le blueprint est le livrable structurel separe. Les
  screenshots de livraison servent seulement de preuve QA apres dev et ne
  remplacent jamais ces livrables cibles. Le coordinateur peut annuler le
  visuel, le blueprint, ou les deux, uniquement avec justification tracee:
  `VISUEL_IA_WAIVED`, `BLUEPRINT_WAIVED`, ou les deux. Les agents comparent
  regulierement avec les visuels de l'enquete utilisateur. La continuite entre
  passages est portee par `/objectif` et les traces `docs/presence_agents.md`:
  ne pas creer ni reparer de heartbeat canonique ou de watchdog permanent par
  defaut. Un heartbeat Claude ne revient que sur demande explicite de Brice pour
  un reveil horodate; il doit rester borne a un `CH-*` existant, ne pas choisir
  de nouveau `ORD-*` seul et etre mis en pause des que le besoin de reveil
  disparait. Si Brice signale que plusieurs conversations prennent la meme
  tache, tout chainage automatique s'arrete: pause des dispatchers concurrents,
  abandon/attente des lots ouverts par course, reprise seulement des roles
  manquants d'un `CH-*` deja declare, puis nouveau dispatch uniquement apres
  arbitrage explicite de Brice.
- Quand Brice dit "lance une equipe UX/UI" avec ou sans accent sur `equipe`,
  appliquer
  [`docs/protocole_equipe_ux_ui_recherche.md`](./docs/protocole_equipe_ux_ui_recherche.md):
  equipe de recherche sans dev, 6 roles maximum dont Testeur metier expert et
  Testeur accessibilite/novice, generation d'images, images retenues archivees
  dans la doc de mission. La reprise se fait par `/objectif`; une relance Claude
  horodatee n'est creee que si Brice la demande explicitement.
- Dans une conversation orientee vers un but, comme un audit ou une livraison,
  le coordinateur garde le chemin critique. Les demandes ponctuelles de
  generalisation, doctrine, cadrage transverse ou side-quest bornee sont
  confiees a des sous-agents si la capacite de threads le permet.

**Ne pas figer un nom d'instance dans cette consigne.** Mesure du 2026-09-08:
l'instance designee ici **cinq fois** comme l'instance de depart **n'existe plus
sur le poste**. Une consigne canonique qui pointe vers rien coute plus cher
qu'une consigne absente, parce qu'elle est suivie: l'agent qui l'applique
echoue, ou choisit une autre instance sans le dire - ce qui reproduit exactement
le defaut que la consigne existait pour empecher. C'est le meme motif que le
lanceur approuve qui mourait en silence (`RM-2026-0125`). L'instance du lot se
**choisit au moment du lot** et se **nomme dans le contrat d'agent**; elle ne se
code pas dans la doctrine.

## Le coffre est la source, et on ne l'ecrit jamais

**Grave a la demande de Brice le 2026-09-08. Ce point ne se rediscute pas.**

> « Je veux que tu graves dans le marbre que la source des donnees, c'est mon
> coffre, et le coffre, tu y accedes uniquement en lecture seule. [...] La source
> originale des donnees, c'est le coffre. »

**Une seule source, un seul mode d'acces.** Le coffre personnel de Brice est la
source originale de tout document. **Lecture seule, toujours, sans exception.**
Aucun lot n'y ecrit, n'y renomme, n'y deplace ni n'y supprime quoi que ce soit -
pas meme pour ranger, pas meme pour corriger une evidence.

**Deux facons legitimes de repartir, et une seule interdite.**

1. **Garder une instance deja integree.** Le tri et le typage des documents qu'elle
   contient ont coute du travail et ont de la valeur en eux-memes: les refaire
   pour rien est une perte, et les refaire *differemment* est pire, parce que la
   difference passe alors pour un resultat.
2. **Repartir des documents bruts, depuis le coffre** - mais **pas de tout le
   coffre**. Precision mesuree le 2026-09-08 et elle n'est pas un detail: le
   coffre porte, melees aux pieces recues, les **sorties d'une version anterieure
   du produit** - une base, des exports tabulaires, des images de pages, des
   milliers de fichiers d'extraction. Une reabsorption qui reprendrait le coffre
   tel quel ferait donc rentrer la SORTIE de la version precedente comme si
   c'etait une entree, ce qui est exactement le defaut que la regle de l'instance
   vide existe pour empecher. **Ne reprendre que les formats scelles** - ce qu'un
   syndic transmet, pas ce qu'un traitement fabrique. C'est la voie quand un lot
   touche la chaine d'absorption et doit eprouver la chaine entiere.
3. **Jamais: repartir d'une instance historique en la prenant pour un etalon.**
   Elle porte la SORTIE d'une version precedente du code.

**Le nom porte la garantie, et c'est ce qui met fin aux hesitations.**

- Une instance dont le nom commence par **`test_`** ou **`dev_`** est un
  duplicata de travail. **Elle peut etre supprimee sans aucune perte de donnee
  personnelle**, parce que tout ce qu'elle contient existe ailleurs, dans le
  coffre ou dans l'instance mere. C'est une garantie, pas une convention de
  politesse: le nom dit ce qu'on a le droit de faire du dossier.
- L'instance **mere** porte un nom reconnaissable et distinct - `instances/tilleul_pseudo_mere`
  (le prefixe est un pseudonyme, voir la section suivante). Elle est reconstruite
  depuis le coffre, et **aucun lot ne la mute**: on en copie, on n'y travaille pas.
  **Elle se reconnait sans faire confiance a ce nom:** elle porte a sa racine un
  fichier `LIRE_AVANT_USAGE.md`, un `MANIFEST_SOURCE.csv` et un `ECARTES.csv`, et
  ses dossiers `staging/`, `registers/` et `outputs/` sont **vides**. Un agent qui
  ne trouve pas le dossier nomme ici **ne choisit pas une autre instance en
  silence**: il cherche celle qui porte ces marques, et il dit que le nom a bouge.
  **Ce paragraphe s'est deja trompe une fois:** l'instance a ete renommee le
  2026-09-08 et le nom ecrit ici a survecu au dossier pendant une journee, alors
  meme que la regle du dessus interdit de figer un nom d'instance.
- **A la fin du chantier, le duplicata se supprime.** Ce n'est pas du menage
  optionnel: une instance de lot qui survit devient, quelques semaines plus tard,
  une instance historique que quelqu'un prendra pour une reference.

**Consequence directe pour un agent.** Le contrat d'agent nomme l'instance du lot,
et ce nom **commence par `test_`**. Le `BOT-END` dit si elle a ete supprimee, ou
pourquoi elle ne l'a pas ete. Une instance de lot laissee en place sans raison
ecrite est un defaut du lot, au meme titre qu'un port non libere.

**Ce qui a ete verifie une fois, et qu'on ne reverifie plus.** Brice a demande
que l'on s'assure une bonne fois que le coffre contient bien tous les documents
presents dans CoproScope: *« une fois que ca, c'est regle, je ne veux plus qu'on
y revienne »*. Le resultat de cette verification vit dans le gouvernail; il ne
se rejoue pas a chaque lot.

## Sur quelles donnees on developpe

Regle de Brice du 2026-09-08. **Par defaut, le developpement s'appuie sur le
corpus reel de l'instance privee de travail, dans des instances JETABLES faites
de COPIES, sans jamais toucher aux originaux - et on les jette quand le lot est
fini.**

L'instance synthetique ne sert que dans un cas: quand on a *vraiment besoin de
donnees artificiellement faciles a reconnaitre*. C'est `examples/synthetic_copro`,
publique et partageable.

**Deuxieme regle, donnee le meme jour: on n'ecrit pas de nom reel dans le code.**
Ses mots: *« Tilleuls (pseudo) - comme ca on n'inscrit pas de traces de
patronyme dans le code »*. Un document, un commentaire ou un message de commit
qui doit designer la copropriete de travail emploie donc son **pseudonyme, suivi
de la mention `(pseudo)`**, et ne dit jamais ce qu'il recouvre. Une phrase qui
relie un pseudonyme a une identite reelle est une table de correspondance a une
ligne, meme quand elle sert a prevenir d'un risque - cette section elle-meme a
du etre corrigee pour cette raison, le jour ou elle a ete ecrite.

**La mention `(pseudo)` porte plus que la politesse, et un incident du meme jour
le montre.** Brice a designe le jeu pseudonymise comme s'il etait le jeu
artificiel, avant de se reprendre. Le 2026-09-07, une etiquette annoncait
*copropriete de demonstration* sur ces memes donnees, et quatre relecteurs
successifs s'en sont servis pour declarer des captures publiables; l'etiquette a
ete corrigee le 2026-09-08 en *DONNEES REELLES, identite pseudonymisee*. **Mais
un nom d'emprunt continue de tromper apres la correction du libelle**: il
protege l'identite et deguise en meme temps la NATURE de la donnee. D'ou la
mention accolee: le nom ne dira jamais qu'il est un nom d'emprunt, il faut
l'ecrire.

Consequences pratiques:

- une instance de lot est **jetable**, et se jette a la fin du lot; son nom la
  designe comme telle (`instances/lot_<sujet>_<date>`);
- elle est faite de **copies**: les sources primaires restent en lecture seule;
- les tests du depot restent sur `examples/synthetic_copro` - la CI n'a pas le
  droit de lire une instance privee - et **cette limite se declare** au lieu
  d'etre presentee comme une preuve de justesse;
- une preuve obtenue sur l'instance synthetique vaut pour la non-regression,
  jamais pour la justesse: ses pieces ont ete ecrites pour passer.

## Fondement juridique d'un choix de code

Consigne de Brice du 2026-09-08. **Tout identifiant Legifrance qui fonde un
choix de code se declare, avec la date de la version qui a ete lue.**

Le code ne cite pas un texte: il cite une **cle** du registre
`server/src/coproscope/modules/_budget_previsionnel_sources.py`. Le registre
cite le texte, avec son identifiant `LEGIARTI`, sa version, et `lu_le`.

**Pourquoi la date de version est constitutive de la citation et non un
ornement.** Le meme article existe en plusieurs versions successives, et
**toutes portent `VIGUEUR`** - ce qui veut dire *en vigueur a la date demandee*,
jamais *a jour*. Trois versions de l'article 25 de la loi de 1965 ont ete lues,
de longueurs differentes, toutes `VIGUEUR`. Le statut ne dit donc jamais si l'on
regarde le bon texte. Un identifiant sans date de version n'est pas une
citation, c'est une reference.

`server/tests/test_fondements_juridiques.py` fait respecter la regle: il balaie
tout `server/src`, sans aucune liste de fichiers, et echoue en nommant
l'identifiant non declare et le fichier qui le porte. Une dette de 24
identifiants encore en litteraux y est bornee et nommee; elle ne doit pas
grandir.

**Ne pas ecrire une regle de droit de memoire.** La skill `piste-api` donne
acces a Legifrance et Judilibre; elle documente aussi les approximations des
deux moteurs, qui elargissent silencieusement les requetes qu'ils ne peuvent pas
satisfaire. Quand un controle echoue - requete elargie, article introuvable -
le dire, au lieu de proposer le resultat approchant que l'API a renvoye.

## Rapports d'audit et notes coproprietaires

Tout rapport ou note d'audit destine au dossier de copropriete doit etre
redige pour un coproprietaire novice: phrases courtes, vocabulaire explique,
sigles developpes a la premiere occurrence, et distinction nette entre ce qui
est constate, ce qui est seulement suppose, et ce qui reste a verifier.

Structure minimale obligatoire:

- synthese en tete, lisible sans connaissance comptable, juridique ou
  informatique;
- methode employee, avec les controles realises et les limites du controle;
- sources utilisees, datees et identifiables;
- constats, separes des interpretations;
- conclusions et questions/actions proposees pour le conseil syndical ou l'AG.
- impact concret pour les coproprietaires, notamment sur les appels de fonds,
  les budgets, le fonds travaux, les impayes, la tresorerie et les risques de
  rattrapage ou d'appel exceptionnel.

Le detail technique peut etre mis plus bas ou en annexe, mais le corps du
rapport doit rester comprehensible par un coproprietaire qui decouvre le sujet.

Lorsqu'une demande d'audit inclut une nouvelle convocation d'assemblee generale,
la partie comptabilite doit etre traitee systematiquement: annexes comptables,
comptes a approuver, budgets votes ou proposes, fonds travaux, impayes,
fournisseurs, travaux et operations exceptionnelles, ainsi que les ecarts avec
les audits ou documents comptables deja connus.

Lorsque des montants globaux peuvent toucher le portefeuille des
coproprietaires, le rapport doit les traduire en consequences pratiques:
hausse probable des appels, reste a financer, risque de tension de tresorerie,
avance temporaire possible, et ordre de grandeur par tantiemes ou par 1 % des
charges, en precisant toujours que le montant exact depend des cles de
repartition du lot.

Toute comparaison doit nommer explicitement les deux references comparees:
document, date, montant ou etat "avant / apres". Eviter les formulations comme
"plus lourd", "en baisse", "plus eleve" ou "ameliore" si les deux bases de
comparaison ne sont pas affichees dans le rapport.

Garde de confidentialite conversationnelle pour audits et notes sensibles:

- structurer le raisonnement en `fait -> preuve -> regle -> action`;
- remplacer les personnes, organisations, lots et lieux par des roles ou alias
  stables des la premiere reformulation, sauf necessite explicite;
- ne pas recopier emails, telephones, adresses completes, chemins locaux, noms
  de fichiers bruts, OCR brut, logs, secrets, tables alias -> identite ou
  correspondances nominatives;
- afficher un montant ou une identite seulement si c'est indispensable au
  controle ou a une diligence concrete, puis revenir aux alias;
- bloquer le rendu final si une donnee personnelle inutile, une piece brute, un
  chemin local ou une allegation non sourcee reste dans le texte.

Pour une nouvelle convocation d'AG, la comparaison principale doit etre faite
entre l'AG precedente disponible au dossier et l'AG actuelle. Les documents de
travail du conseil syndical peuvent etre cites comme pieces de circulation ou de
controle, mais ils doivent etre presentes comme references secondaires et ne
doivent jamais etre confondus avec une convocation officielle ou un document
soumis au vote.

## Regle zero interconversations

Tout bot doit lire [`docs/consignes_bots_interconversations.md`](./docs/consignes_bots_interconversations.md)
avant de modifier le depot.

Il lit aussi
[`docs/protocole_roadmap_presence_agents.md`](./docs/protocole_roadmap_presence_agents.md)
pour rattacher son travail a un item `RM-*`, un chantier `CH-*` et une
conversation `CONV-*`.

Tout nouveau chantier doit suivre le format anti-collision
`CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug-court`. Le format historique
`CH-YYYY-NNNN` est conserve uniquement pour les chantiers deja ouverts.

Avant toute modification, il declare:

- identifiants `RM-*`, `CH-*` et `CONV-*`;
- role et mission;
- ownership modifiable;
- fichiers a eviter;
- passerelle ou registre de trace;
- dernier point de coordination lu;
- tests ou preuves attendus.
- lease d'ownership et prochaine action.

Sans declaration claire, le bot reste en lecture seule et publie une question de
coordination. Les passerelles UX/DB restent separees: UX ecrit dans
`docs/passerelle_ux_vers_db_2026-05-21.md`, DB repond dans
`docs/passerelle_db_vers_ux_2026-05-21.md`, le coordinateur consolide dans
`docs/coordination_interconversations_2026-05-21.md`.

## Demarrage recommande

Depuis la racine du depot principal, apres avoir stabilise ou commite les changements en cours :

```powershell
git fetch origin
git switch codex/bootstrap-coproscope-server
git pull --ff-only

git worktree add ..\coproscope-agent-sprint2-actions -b codex/sprint2-actions
git worktree add ..\coproscope-agent-sprint3-compta -b codex/sprint3-compta
git worktree add ..\coproscope-agent-sprint4-privacy -b codex/sprint4-privacy
```

Si une branche existe deja, retirer `-b <branche>` et indiquer la branche existante a la fin de la commande.

## Le venv n'installe plus le paquet: PYTHONPATH est obligatoire

Purge faite le 2026-09-05 a la demande de Brice. `server/.venv` portait un
install editable dont le `.pth` codait en dur un chemin ABSOLU vers le
`server/src` de l'arbre principal. Un agent qui travaillait dans un worktree et
lancait `python -m unittest` depuis son propre `server/` obtenait une suite
verte qui avait teste le code de l'arbre PRINCIPAL. Le defaut ne cassait aucun
test: il en faisait passer. Constate par un agent de la campagne de finition,
dans ses propres mots: « mes premiers passages verts etaient donc faux ».

Le venv reconstruit **n'installe plus le paquet du tout**. Le piege n'est plus
detecte, il est **impossible**: sans chemin explicite rien ne s'importe, et avec
un chemin explicite c'est forcement l'arbre courant.

```powershell
cd <ton arbre>\server
$env:PYTHONPATH = "src"; .venv\Scripts\python.exe -m unittest tests.test_le_module_que_je_touche
```

**Cette commande est le chemin RAPIDE, sur un module nomme. Elle ne rend pas le
verdict de la suite complete, et la variante `discover -s tests` ne le rend pas
non plus:** elle place `server/tests` en tete de `sys.path` et change le nom
d'import des modules, donc **elle n'est pas la meme invocation** et rien ne
garantit qu'elle voit la meme suite. Pour la suite complete, une seule commande,
depuis la racine du depot:

```powershell
.venv\Scripts\python.exe tools\lancer_la_suite.py
```

Elle se place elle-meme au bon endroit, **nomme les tests collectes et jamais
DEMARRES** - un saut pose au niveau d'une classe n'apparait dans aucun compteur
standard - et rend un code lu du verdict d'`unittest`, jamais d'un code compose.
`tools/agent-check.cmd -Full` et la CI l'appellent, et une garde du depot
verifie qu'ils continuent de le faire.

**LE CHIFFRE QUI JUSTIFIAIT CETTE REGLE A ETE REMESURE LE 2026-09-12, ET IL
N'EST PLUS VRAI - la regle, elle, ne bouge pas.** Ce paragraphe affirmait, au
present, que `discover -s tests` *joue environ 330 tests de MOINS* et *sort sur
`1` pendant qu'`unittest` imprime `OK`*. C'etait la mesure du 2026-09-10
(`RM-2026-0173`): 2 533 contre 2 201. Remesure du 2026-09-12, par collecte seule
sous les deux jeux de conditions: **2 999 contre 2 999, ecart nul**, et un
passage complet par l'invocation refutee a rendu `OK` avec le code `0`. Les deux
defauts decrits ne se reproduisent donc plus.
**Pourquoi la prescription survit a la disparition de sa preuve.** Elle ne
repose pas sur l'ecart: elle repose sur le fait qu'il existe **deux invocations
dont on ne sait pas, a la lecture d'un `Ran N tests ... OK`, laquelle a produit
le chiffre** - la ligne qu'on recopie est imprimee a l'identique par les deux.
Un lanceur unique n'est pas une precaution contre un bug connu, c'est ce qui
rend un verdict attribuable. Et le lanceur nomme en plus les tests **collectes
et jamais demarres**, ce que ni l'une ni l'autre invocation ne fait.
**Ce que cette correction a coute, et c'est la raison de l'ecrire ici.** Un
agent a lu la version au present, a conclu que son propre verdict vert etait
faux, et l'a annonce comme tel - avant de mesurer. Une justification perimee
laissee au present ne fait pas douter de la regle: elle fait **rejeter des
mesures justes**.

**Deux pieges de mesure mesures le 2026-09-08, qui rendent VERT ce qui ne l'est
pas.** Ils s'ajoutent au piege du venv ci-dessus et ont la meme forme.

- **Le code de sortie que tu lis n'est pas toujours celui de Python.** Ne juge
  jamais un succes a travers un pipe - `| tail` rend le code de `tail` - ni sur
  un code remonte par une commande composee, `; echo`, `; tail` compris. Un lot
  a annonce une suite verte sur un `exit code 0` qui etait celui de son
  enveloppe shell, alors que Python rendait `FAILED` sous dessous. **Lis le
  verdict dans le journal lui-meme.**
- **Un module qui passe seul ne prouve pas que la suite passe.** Ce depot joue
  ses tests de DEUX facons - `discover -s tests`, a plat, et `-m unittest
  tests.X`, en paquet. Un import relatif ne tient que dans la seconde: le module
  passait en isolation pendant que la suite entiere cassait, donc le defaut
  etait invisible a tous les passages cibles.
- **Ne lance pas deux suites completes en meme temps dans le meme arbre.** Deux
  passages concurrents se sont bloques au meme point, sans verdict et sans
  message. Un blocage est pire qu'un echec: la CI expire sans rien nommer.

`tools/agent-check.cmd` pose ce chemin lui-meme et imprime le dossier de sources
a cote de l'interpreteur. `server/tests/test_arbre_teste.py` reste en tete du
chemin rapide: il echoue en nommant les deux arbres si la suite mesure un autre
code.

Deux points a connaitre:

- **Le venv est cree avec `uv`, pas avec `pip`.** Il n'embarque donc pas `pip`:
  `python -m pip freeze` rend zero ligne, ce qui n'est pas un defaut. Utiliser
  `uv pip freeze` avec `VIRTUAL_ENV` pointe sur le venv.
- **L'interpreteur 3.12.13 vit dans un cache de runtime Codex**
  (`~/.cache/codex-runtimes/...`). C'est fragile: si ce cache est nettoye, le
  venv devient inutilisable et il faudra le reconstruire sur un Python 3.12
  installe ailleurs. Les seuls Python enregistres sur le poste sont 3.14 et 3.8.

## Check rapide agent

Pour une reprise ou une fin de lot courte, lancer depuis la racine du depot:

```powershell
.\tools\agent-check.cmd
```

Options utiles:

- `.\tools\agent-check.cmd -Ui` pour ajouter les smoke tests UI et routes de
  securite;
- `.\tools\agent-check.cmd -Security` pour ajouter Bandit haute severite et
  pip-audit;
- `.\tools\agent-check.cmd -Orchestration` pour afficher les diagnostics
  orchestration, conversations expirees, blocages, arbitrages et hygiene des processus Codex (nom conserve a dessein: l'outil inspecte les processus OpenAI Codex reellement presents sur le poste)
  sans exiger de heartbeat permanente;
- `.\tools\agent-check.cmd -Full` pour lancer toute la suite `unittest`.

Pour diagnostiquer l'orchestration sans tests applicatifs:

```powershell
.\tools\orchestration-watch.cmd
.\tools\orchestration-supervise.cmd --read-codex-processes
```

Le check rapide ne remplace pas la verification d'integration complete quand le
coordinateur integre une branche, mais il donne un signal fiable avant de rendre
un lot.

## Lancement serveur local approuve

Pour demarrer une interface CoproScope locale, utiliser le lanceur stable du
workspace au lieu d'inventer une commande PowerShell `Start-Process`:

```powershell
C:\Users\brice\CoproScope\dev\tooling\scripts\start-coproscope-ui-server.cmd
```

Il accepte les options utiles pour une recette temporaire:

```powershell
C:\Users\brice\CoproScope\dev\tooling\scripts\start-coproscope-ui-server.cmd --instance-root C:\Users\brice\CoproScope\coproscope\examples\synthetic_copro --port 8786 --token drive-publish-demo-local
```

Pour la recette "publication Drive demo" sur l'instance synthetique, utiliser
la commande stable sans argument:

```powershell
C:\Users\brice\CoproScope\dev\tooling\scripts\start-coproscope-drive-publish-demo.cmd
```

Ce lanceur est approuve dans Claude Code. Les commandes PowerShell variables avec
`Start-Process` redemandent une autorisation et doivent etre evitees si le
lanceur suffit.

## Contrat a inscrire pour chaque agent

Inscrire une fiche courte dans le registre de coordination avant le lancement.
Pour un sous-agent, cette fiche est donnee directement par le fil pilote et
reportee dans `docs/presence_agents.md`: pas de file de jetons ni de relais
manuel par copier-coller.

```text
Mission: Sprint <numero> - <objectif>
Role/filiere: <UX | DB | QA | front | back | docs | coordinateur>
Roadmap/chantier/conversation: RM-YYYY-NNNN / CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug-court / CONV-YYYY-NNNN
Branche/worktree: <branche> / <chemin>
Tu n'es pas seul dans le codebase. Ne revert jamais les changements des autres.
Ownership fichiers: <liste de dossiers/fichiers modifiables>
Fichiers a eviter: <liste>
Passerelle/registre de trace: <fichier>
Dernier point coordination lu: <fichier + heure>
Lease ownership: <expiration + fuseau> ; point de reprise dans docs/presence_agents.md
Donnees: pas de donnees privees dans Git ; instance privee uniquement en lecture locale.
Instance du lot: <chemin de l'instance fraiche creee pour ce lot>, copiee depuis
une copie fraiche de l'instance privee de travail si l'epreuve en pleine
charge est requise. Ne pas travailler directement dans une instance historique,
et ne jamais s'en servir comme etalon.
Verification attendue: <commandes de test ou checks UI>
Livrable final: resume, fichiers modifies, limites, tests lances.
```

## Methode equipe agile multi-agents

Avant de supposer qu'une equipe agile standard est le bon format, appliquer le
routeur de [`docs/strategie_equipes_multi_agents.md`](./docs/strategie_equipes_multi_agents.md).
L'equipe agile UI produit est un cas de routage, pas le mode par defaut pour
toute demande multi-agents.

La methode canonique est
[`docs/protocole_equipe_agile_agents.md`](./docs/protocole_equipe_agile_agents.md).
Elle est obligatoire quand une conversation demande une equipe agile,
des agents UX/dev/QA, ou des iterations rapides avec utilisateurs.

Depuis le recadrage `/objectif` du 2026-05-30, le fil pilote ne cree plus de
heartbeat canonique ni de watchdog permanent par defaut. La continuite est
portee par l'objectif actif Claude, les traces `docs/presence_agents.md` et les
leases declares. Les anciennes heartbeats `relance-worker-*`, `worker-*`,
`ce-*`, `relance-ce-*` et la heartbeat canonique doivent rester pausees ou
etre supprimees, sauf demande explicite de Brice pour un reveil horodate
strictement borne.
Le fil pilote laisse un point de reprise persistant dans
`docs/presence_agents.md` quand il suspend ou cloture un passage.
`AGILE-DONE - equipe agile a fini son job` ferme seulement le lot courant: si
tous les roles du lot sont clos, le fil pilote choisit la prochaine tache actionnable du
gouvernail uniquement quand aucun arbitrage `EN_ATTENTE_USER`, blocage non
stationne ou incident de doublon n'est actif. En mode incident
anti-chevauchement, le fil ne lance aucune nouvelle equipe: il met en pause les
dispatchers concurrents, marque les lots ouverts par course `ABANDONNE` ou
`EN_ATTENTE_USER`, trace le verrou dans `docs/presence_agents.md`, relance
seulement les roles manquants d'un `CH-*` deja declare et attend un arbitrage
explicite de Brice avant toute nouvelle tache.

Resume d'execution:

1. le coordinateur rattache le travail au gouvernail `RM-*` et cree un `CH-*`
   horodate selon `docs/protocole_roadmap_presence_agents.md`;
2. il publie son `BOT-START`, reserve la tache du backlog dans
   `docs/presence_agents.md`, trace `ROUTAGE_EQUIPE`, puis genere les
   sous-agents de roles disponibles et ajoute une ligne `CONV-*` ou
   `SUBAGENT-*` par role actif;
3. les roles standards sont coordinateur-scribe, designer/facilitateur,
   utilisateur novice, dev front, dev back/viewmodel et QA; si le budget de
   threads le permet, ajouter un testeur expert metier
   juridique/compta/process chantier/syndic, sinon faire reprendre sa checklist
   par QA et le coordinateur;
4. le travail tourne en double flux: `N-1` teste le produit livre avec
   screenshots/captures de recette, `N` developpe la commande validee, `N+1`
   produit le visuel IA, le blueprint cible et la commande suivante;
5. chaque cycle nomme une UI reelle: route, ecran, modale, artefact HTML ou
   parcours local. Si l'UI manque, le premier objectif est de la rendre
   testable, pas de raisonner sur une intention abstraite;
6. a chaque iteration UI, le designer produit une brouillon HTML de l'ecran
   complet et un blueprint visuel cible, puis le novice donne un GO/NO-GO avant
   tout dev; l'un et/ou l'autre peuvent etre annules seulement avec
   justification tracee, et une capture de livraison ne remplace pas cette
   etape;
7. le designer, le novice et la QA comparent souvent l'UI reelle aux visuels
   d'enquete utilisateur ou au visuel designer derive, et tracent les ecarts
   acceptes/refuses avant GO;
8. des qu'un lot livre un bout de page visible, route, template, fragment,
   CSS, composant, modale, premier viewport ou interaction, QA et novice
   testent la page reelle via un serveur local reserve; les tests unitaires ou
   TestClient restent des preuves de regression, pas une preuve produit
   suffisante;
9. les devs restent en lecture tant que le blueprint, la commande dev, la
   qualification novice et le contrat `model.ux.*` ne sont pas stabilises;
10. chaque point annonce: a tester, en dev, en enquete, commande prete, agents
   idle, decision requise, prochain mouvement et preuves.

Dans ce cadre, le coordinateur ne quitte pas la piste critique pour traiter une
generalisation ou une side-quest nee d'une orientation ponctuelle. Si un thread
est disponible, il lance un sous-agent avec objectif borne, ownership explicite,
fichiers evites, trace et critere de fin. Si aucun thread n'est disponible, il
note la demande comme reprise ulterieure ou question d'arbitrage, sauf si elle
bloque directement le but principal.

## Methode equipe UX/UI sans dev

Quand la commande naturelle est `lance une equipe UX/UI`, avec ou sans accent
sur `equipe`, utiliser
[`docs/protocole_equipe_ux_ui_recherche.md`](./docs/protocole_equipe_ux_ui_recherche.md).
Cette equipe ne code pas: elle produit recherche, parcours, wireflows,
directions UI, images generees et decisions UX/UI. Le Designer UI / generateur
visuel produit les images candidates; seules les images retenues ou utiles a
une decision sont archivees dans `docs/assets/...` et referencees dans la doc
de mission.

Au lancement effectif, le coordinateur ne cree pas de heartbeat automatique par
defaut. Il s'appuie sur `/objectif` et sur une ligne de reprise dans
`docs/presence_agents.md`. Si Brice demande explicitement un reveil horodate,
la relance Claude doit etre bornee a la mission UX/UI courante, relancer
seulement les roles idle ou bloques sans les dupliquer, puis etre mise en pause
quand la trace finale contient `UXUI-DONE - equipe UX/UI a fini son job`.

## Ports locaux

Ne pas lancer deux interfaces sur le meme port. Le port fait partie de
l'ownership de l'agent au meme titre que les fichiers: il est annonce dans le
contrat agent, reporte dans `docs/presence_agents.md`, puis libere explicitement
dans le `BOT-END`.

Regles obligatoires:

- Pour les lots desktop, packaging, installable ou recette utilisateur generale,
  tester en priorite l'executable avec
  `server\packaging\windows\smoke-executable.ps1`. Le serveur PowerShell visible
  reste l'outil de developpement web fin, pas la recette cible par defaut.
- Le smoke executable peut choisir un port loopback libre fourni par Windows,
  lancer son propre processus `CoproScope.exe`, puis fermer uniquement ce
  processus. Il ne doit jamais tuer un PID qu'il n'a pas cree.
- Quand Brice demande explicitement de tester la derniere version de l'exe, le
  coordinateur peut lancer `CoproScope.exe` en recette interactive, avec PID
  trace, URL tokenisee et consigne d'arret. Ce lancement n'est ni un serveur
  durable ni un heartbeat: il reste ouvert seulement pour la recette de Brice,
  puis il est arrete sur demande ou en fin de lot. Preferer la plage `8780` a
  `8799`; si elle est occupee ou douteuse, utiliser le prochain port documente
  et noter la raison dans `docs/presence_agents.md`.
- reserver un port avant de demarrer un serveur, avec `CONV-*`, role, instance,
  token de test et commande prevue;
- choisir l'instance de recette la moins sensible possible: `examples/synthetic_copro`
  pour les preuves partageables, une copie fraiche de l'instance privee de travail
  dediee au lot seulement quand le scenario
  local l'exige, jamais une instance privee brute pour une capture diffusable;
- quand un serveur de developpement est lance manuellement, le garder dans un
  terminal PowerShell visible, identifiable par le port et le `CONV-*`; arret
  par `Ctrl+C` uniquement;
- un serveur de recette appartient a un seul owner et a un seul lot. Si le code
  a change ou si l'owner change, repartir d'un port reserve frais dans `8780`
  a `8799` au lieu de reutiliser un serveur ambigu;
- ne pas scanner les ports ou processus, ne pas tuer de PID, ne pas utiliser
  `taskkill`, `Start-Process` cache ou ouverture navigateur automatique, sauf
  ouverture explicite d'une URL de recette quand Brice a demande a tester
  l'executable;
- si le port prevu est occupe ou douteux, ne pas enqueter par scan: publier le
  conflit dans la trace, choisir un autre port documente dans la plage de
  secours, et mettre a jour `presence_agents.md`;
- une URL live citee dans un test doit toujours indiquer port, instance cible et
  token attendu;
- pour toute livraison de bout de page visible par une equipe agile, la trace de
  fin cite l'URL exacte, le role qui a teste, le scenario clique, les captures
  desktop/mobile ou le waiver explicite `RECETTE_PAGE_REELLE_WAIVED`;
- conserver seulement les captures utiles a la decision; les logs, `.pid`,
  caches et sorties temporaires restent hors Git;
- a la fin du lot, dire si le serveur a ete arrete ou s'il reste volontairement
  ouvert pour recette, avec la raison, l'owner et la consigne d'arret.

Ports reserves par defaut:

| Usage | Port conseille |
|---|---:|
| Coordinateur | 8765 |
| UI/actions | 8766 |
| ComptaScope | 8767 |
| Privacy/DocOps | 8768 |
| Demo/docs | 8769 |
| SyndicOps | 8770 |
| DocOps actionnable | 8771 |
| Decision-action-preuve | 8772 |
| WorksOps | 8773 |
| IncidentOps | 8774 |
| Comms/passation | 8775 |

La plage `8780` a `8799` est reservee aux recettes temporaires, gates live et
serveurs de comparaison. Chaque utilisation de cette plage doit etre nommee
dans le point de coordination ou la trace `CONV-*`; elle ne devient jamais un
defaut implicite.

## Perimetres qui se parallelisent bien

| Agent | Ownership principal |
|---|---|
| UI/actions | `server/src/coproscope/web/`, `server/tests/test_ui_demo*.py` (quatre fichiers depuis le decoupage du 2026-09-07) |
| ComptaScope guide | `server/src/coproscope/web/viewmodel.py`, templates comptes, docs ComptaScope |
| Privacy/DocOps | `server/src/coproscope/modules/privacyops.py`, templates confidentialite/documents, tests privacy |
| Decision-action-preuve | nouveau module/registre dedie, tests dedies, docs fonctions cibles |
| Documentation/orchestration | `docs/`, `README.md`, registres de suivi |

Quand deux agents doivent toucher `viewmodel.py`, le coordinateur tranche avant lancement : un seul agent possede ce fichier, les autres produisent une note d'integration ou travaillent sur des templates/tests.

## Refonte UX depuis les visuels d'enquete

La refonte UX Canva suit le protocole
[`docs/refonte_ux_cycles_image_dev_test.md`](./docs/refonte_ux_cycles_image_dev_test.md):
enquete sur image, commande dev, developpement, test produit livre, correction
ou cloture.

Regles supplementaires:

- garder un bloc en test, un bloc en dev et un bloc en enquete quand c'est possible;
- ne pas demarrer le dev sans commande validee;
- ne pas laisser les devs inventer une vue manquante sans blueprint designer;
- ne pas lancer un dev UI sans route/ecran/artefact reel cible et, si pertinent,
  sans image designer qualifiee par le novice;
- produire un visuel IA et un blueprint designer pour chaque iteration UI avant
  le dev; le visuel est un brouillon HTML de l'ecran complet, jamais un SVG;
  l'un et/ou l'autre peuvent etre annules seulement avec justification tracee;
  les screenshots de livraison sont des preuves de recette, pas la source
  d'intention UX;
- comparer regulierement l'UI livree aux visuels de l'enquete utilisateur ou au
  visuel designer derive; un GO UI sans comparaison explicite est refuse sauf
  justification de non-pertinence;
- tester une route livree, pas une intention abstraite;
- tenir [`docs/registre_cycles_refonte_ux.md`](./docs/registre_cycles_refonte_ux.md)
  et utiliser les prompts de
  [`docs/prompts_agents_refonte_ux.md`](./docs/prompts_agents_refonte_ux.md).

## Integration

Le coordinateur :

1. verifie `git status --short` dans chaque worktree ;
2. relit les diffs ;
3. integre une branche a la fois ;
4. resout les conflits sans supprimer le travail d'un autre agent ;
5. lance la suite complete par son **unique** lanceur, depuis la racine du depot : `.venv\Scripts\python.exe tools\lancer_la_suite.py` ; l'ancienne commande `-m unittest discover -s tests` jouait environ 330 tests de moins en imprimant `OK` (`RM-2026-0173`) ;
6. met a jour le gouvernail `docs/roadmap_backlog_central.md` et `docs/presence_agents.md` ;
7. pousse seulement les changements genericisables.

Voir aussi : [`docs/orchestration_agents.md`](./docs/orchestration_agents.md).
