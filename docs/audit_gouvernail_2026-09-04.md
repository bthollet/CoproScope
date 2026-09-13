# Audit de veracite du gouvernail

`RM-2026-0084` / `CONV-2026-2136` / audit du 2026-09-04.
Perimetre: `docs/roadmap_backlog_central.md`, 974 lignes a l'ouverture du lot,
1 025 apres les rectifications - aucune ligne n'a ete supprimee, seules des
rectifications datees ont ete ajoutees.
Regle tenue: aucune ligne effacee. Les corrections appliquees sont adossees a une
preuve citee. Les suppressions, fusions et changements de structure sont proposes,
pas appliques.

---

## 1. Synthese

Le gouvernail ne dit pas la verite, mais pas la ou on l'attendait.

Le desordre n'est pas un desordre de volume. C'est un desordre de **nature**: un
seul tableau, avec une seule colonne de statut, sert a la fois a porter des
regles qui ne se terminent jamais, des chantiers qui ont un porteur et une fin,
et des constats mesures qui n'ont ni l'un ni l'autre. Quand le debit de
decouverte augmente, ce sont les constats qui explosent, et comme le format les
oblige a devenir des chantiers, la file d'execution devient illisible en deux
jours. Le probleme de granularite precede donc largement le lot de septembre; le
debit l'a seulement rendu visible.

Le defaut le plus grave est anterieur et il est mesurable: **le statut confond
"le code est merge" et "la fonction marche".** Huit pages du produit sont
servies par une fonction de construction qui ne prend que l'annee en argument et
retourne un dictionnaire ecrit a la main, sans un seul acces a l'instance, au
coffre ou a la base. Elles sont declarees `INTEGRE` ou `PRET_A_INTEGRER` au
gouvernail. Un lecteur du gouvernail croit que sept fonctions produit existent.

Quatre statuts sont corriges sur preuve ou sur arbitrage, et vingt-quatre
lignes recoivent une rectification datee. Six items `ACTIF` sont orphelins par
construction. Cinq items citent comme preuve un fichier renomme le 2026-09-02 et
qui n'existe plus. Et un item bloque en mai a ete redecouvert par la mesure en
septembre sous quatre identifiants neufs, sans que personne ne fasse le lien -
parce que rien dans le document ne permettait de le faire.

---

## 2. Ce que le compte reel dit, et ou le brief se trompait

Le brief d'ouverture annoncait 98 items et une numerotation allant jusqu'a
`RM-2026-0083`. La mesure ne le confirme pas.

| Grandeur | Annonce au brief | Mesure |
|---|---:|---:|
| Items au registre actif | 98 | **78** |
| Identifiant le plus haut | `RM-2026-0083` | `RM-2026-0080` |
| Items ouverts en 24 h | 31 | **31** (`RM-2026-0049` a `RM-2026-0080`, moins `0073`) |
| Items anterieurs | 67 | **47** (`RM-2026-0001` a `RM-2026-0048`) |
| `ACTIF` | 37 | **37** |
| dont anterieurs a `RM-2026-0049` | - | **10** |

Deux identifiants existent hors du registre et n'ont donc pas de ligne
pilotable: `RM-2026-0046` n'apparait que dans le journal (deux entrees du
2026-05-31 sur le changement de coffre dans l'executable), et `RM-2026-0073` ne
vit que dans `docs/corpus_caviarde_2026-09-04.md`. Ce sont deux trous, pas deux
doublons.

Le compte des statuts ne tombait pas juste pour une raison unique et
corrigeable: `RM-2026-0067` porte `P1` dans la colonne `Statut`, c'est-a-dire
une priorite a la place d'un statut. C'est le seul item sans statut lisible.

**Consequence directe sur l'hypothese du coordinateur.** Les 37 `ACTIF` ne sont
pas majoritairement une cohorte orpheline de mai: ce sont **27 items de
septembre et 10 items anterieurs**. L'hypothese de la cohorte orpheline est
vraie, mais elle porte sur dix lignes, pas sur trente-sept. Le desordre du vieux
gouvernail n'est pas dans sa colonne `ACTIF`. Il est dans sa colonne `INTEGRE`.

---

## 3. Classement par la preuve

### 3.1 Vrai et vivant - 9 items

Un porteur existe, verifie contre `docs/presence_agents.md` (6 lignes actives au
lint) et contre l'etat du depot.

| Item | Preuve de vie |
|---|---|
| `RM-2026-0003`, `RM-2026-0006` | `CONV-2026-2090`, `PRET_A_INTEGRER` au registre de presence |
| `RM-2026-0016` | Parking P2 decide explicitement par Brice le 2026-05-25; dormance voulue, pas subie |
| `RM-2026-0048` | `CONV-2026-2100`; module `convocation` present dans l'arbre de travail |
| `RM-2026-0049`, `RM-2026-0050`, `RM-2026-0051` | `CONV-2026-2120`, `2121`, `2122`; livrables presents dans `docs/` |
| `RM-2026-0062`, `RM-2026-0068` | `CONV-2026-2127` |

### 3.2 Vrai et fait - 26 items

`INTEGRE` confirme par le code ou par un document present. Ces items n'ont pas
besoin de changer: `RM-2026-0001`, `0002`, `0009`, `0010`, `0011`, `0013`,
`0015`, `0018`, `0019`, `0020`, `0021`, `0022`, `0023`, `0029`, `0034`, `0035`,
`0036`, `0039`, `0040`, `0043`, `0077`, `0078`, `0079`, plus `0005` (voir 3.5),
`0030` (voir 3.6) et `0044` (corrige, voir 4.1).

Verification faite pour les routes revendiquees: `/travaux`, `/incidents`,
`/contrats`, `/pilotage`, `/pilotage/activite`, `/messages/entrants`,
`/coffre/partage`, `/gouvernance/compte-rendu-cs`, `/gouvernance/atelier-ag`,
`/gouvernance/participants-ag`, `/courriers/preuves`,
`/documents/tri-feedback`, `/comptes/rapprochement`, `/exports/passation`,
`/instances` existent toutes dans `server/src`. Aucune route revendiquee n'est
absente. Le probleme n'est pas l'existence des routes.

### 3.3 Le vrai defaut du vieux gouvernail: sept fonctions annoncees, huit ecrans creux

**Mesure.** Huit fonctions de construction de vue portent exactement la signature
`def build_*(year: int = 2025) -> dict[str, Any]` et ne contiennent **aucun**
appel a `open(`, `Path(`, `read_text`, `sqlite`, ni aucun import de module de
donnees:

| Fichier (`server/src/coproscope/web/`) | Lignes | Acces donnees | Item au gouvernail | Statut declare |
|---|---:|---:|---|---|
| `governance_cr_cs_view.py` | 130 | 0 | `RM-2026-0024` | `INTEGRE` |
| `governance_atelier_ag_view.py` | 166 | 0 | `RM-2026-0024` | `INTEGRE` |
| `messages_entrants_view.py` | 182 | 0 | `RM-2026-0031` | `INTEGRE` |
| `worksops_travaux_view.py` | 145 | 0 | `RM-2026-0032` | `INTEGRE` |
| `participants_ag_view.py` | 189 | 0 | `RM-2026-0026` | `PRET_A_INTEGRER` |
| `roles_commissions_view.py` | 188 | 0 | `RM-2026-0026` / `ORD-P2-040` | `PRET_A_INTEGRER` |
| `courriers_preuves_view.py` | 164 | 0 | `RM-2026-0028` | `PRET_A_INTEGRER` |
| `coffre_partage_view.py` | 122 | 0 | `RM-2026-0033` | `PRET_A_INTEGRER` |

Contre-epreuve, qui montre que ce n'est pas un defaut general: dans le meme
dossier, `incidentops_view.py` et `contractops_view.py` prennent une `instance`
en argument et lisent reellement des donnees. `pilotage_view.py` aussi. Les
items `RM-2026-0034`, `RM-2026-0035` et `RM-2026-0036` sont donc `INTEGRE` a
juste titre. La liste des huit est exacte et bornee.

**Confirmation independante.** L'audit `docs/audit_pages_controle_2026-09-03.md`
section 4.1 a mesure quatre de ces huit sans connaitre les autres, et a note que
deux d'entre elles se contredisent elles-memes: `/gouvernance/atelier-ag`
annonce trois questions au-dessus d'un tableau qui en contient deux;
`/gouvernance/participants-ag` annonce deux pouvoirs recus puis un seul a
relire. Des compteurs ecrits a la main qui ne s'accordent pas entre eux prouvent
mieux que n'importe quel test que rien n'est calcule.

**Origine, datee.** Le journal du gouvernail montre que sept de ces huit ecrans
ont ete produits dans une seule sequence, entre le 2026-05-25 23:06 et le
2026-05-26 00:34, sous l'enchainement automatique intitule `nuit autonome` et
sous la heartbeat `relance-equipe-agile-gouvernail-autonome`. Chaque lot y est
inscrit `INTEGRE` moins de dix minutes apres son `START`. Le format de
cloture etait honnete sur les mots employes - il dit `modele synthetique FICTIF`
- mais il n'a jamais eu de champ pour dire que la fonction ne lit rien. Le
gouvernail a donc enregistre huit livraisons vraies au sens du code merge, et
sept fonctions produit fausses au sens de l'usage.

**C'est la reponse a la question de Brice.** Le menage a faire dans ce qui
precedait le lot de septembre n'est pas un menage de lignes mortes. C'est que
sept lignes annoncent une capacite produit qui n'existe pas.

### 3.4 Contradiction interne: trois items que leur propre journal contredit

| Item | Statut au registre | Ce que dit le journal du meme fichier |
|---|---|---|
| `RM-2026-0026` | `PRET_A_INTEGRER` | `INTEGRATE_PARTICIPANTS_AG_DEV`, 2026-05-25 23:23 |
| `RM-2026-0028` | `PRET_A_INTEGRER` | `INTEGRATE_COURRIERS_PREUVES_DEV`, 2026-05-25 23:28 |
| `RM-2026-0033` | `PRET_A_INTEGRER` | `INTEGRATE_COFFRE_PARTAGE_DEV`, 2026-05-25 23:06 |

Les trois routes existent dans `server/src`. La colonne `Prochaine action` de
ces trois lignes dit encore `Ouvrir un chantier dev separe seulement si ... devient
prioritaire`, c'est-a-dire l'etat d'avant le developpement. La ligne du registre
n'a jamais ete relue apres que le journal l'a rendue fausse. Deux vues du meme
fichier se contredisent, et c'est la vue de tete - celle qu'on lit - qui a tort.

Je ne les bascule pas en `INTEGRE`: ce serait remplacer un mensonge par un
autre, puisque leur livrable est creux. J'inscris la contradiction mesuree dans
la ligne, sans toucher au statut, en attendant l'arbitrage de structure.

### 3.5 Vrai et mort par decision - la couche d'orchestration

Le commit `56fe402` du 2026-09-02, `orchestration: retrait du watchdog et du
superviseur Codex`, a retire `tools/orchestration_watchdog.py`,
`tools/orchestration_supervisor.py`, leurs lanceurs et leurs tests. Verification:
`tools/` ne contient plus aucun de ces fichiers.

Consequences a inscrire, aucune n'est une negligence:

- `RM-2026-0005` reste `INTEGRE` et sa doctrine reste valide, mais une partie de
  ce qu'il decrit - heartbeats, detection de conversations `stale`, relance
  automatique, superviseur - n'existe plus. L'item n'est pas mort; sa premisse a
  ete partiellement retiree par decision.
- **`RM-2026-0012` est le cas dur.** Il est `INTEGRE`, sa route
  `/pilotage/activite` est bien livree, et pourtant elle affiche aujourd'hui une
  chose fausse. `server/src/coproscope/web/activity_view.py:86` lit
  `docs/roadmap_backlog_central.md` et sa fonction `_heartbeat_rows` ne retient
  que les lignes contenant la chaine litterale
  `relance-equipe-agile-gouvernail-autonome`. Il y a 22 lignes de ce type au
  journal, toutes de mai et juin, et la heartbeat qui les ecrivait a ete
  demantelee. La page produit affiche donc les quatre derniers battements d'un
  coeur arrete.

Cette derniere mesure est aussi **une contrainte dure sur toute restructuration**:
le gouvernail n'est pas seulement un document, c'est une entree d'execution d'une
page livree. Deplacer le journal casse `/pilotage/activite` en silence. Aucun
autre code du depot ne lit ce fichier: verification faite, seuls
`activity_view.py`, `tools/presence_lint.py` (qui ne fait que verifier sa
presence) et deux tests le citent.

### 3.6 Faux, ou premisse refutee par une mesure posterieure

Le precedent `RM-2026-0079` n'est pas isole. Trois autres items disent quelque
chose que la mesure a contredit:

- **`RM-2026-0030`**, `INTEGRE`, annonce le rapprochement compta multi-sources
  comme maintenu. Trois items de septembre mesurent que le module comptable
  tourne a vide: `RM-2026-0074` etablit que l'extracteur d'etat des depenses
  n'existe pas et que `_load_expense_statement_lines` attend un CSV
  pre-existant; `RM-2026-0075` etablit que le total des charges retombe en
  silence sur un substitut affiche sous le meme libelle; `RM-2026-0064` etablit
  que la colonne `montant a repartir` est un TTC. Le `INTEGRE` de mai n'est pas
  un mensonge sur le code, c'est un `INTEGRE` sur une chaine dont le premier
  maillon manque.
- **`RM-2026-0013`**, `INTEGRE`, inscrit la doctrine de confidentialite
  conversationnelle. `RM-2026-0068` mesure que la garde de pseudonymisation ne
  voit pas 146 identites listees sans civilite, et `RM-2026-0065` qu'une part
  des patronymes passe. La doctrine est ecrite et integree; l'outil qui devrait
  la tenir ne la tient pas. L'item n'est pas faux, mais lu seul il rassure a
  tort.
- **`RM-2026-0067`** ne porte pas de statut: sa colonne `Statut` contient `P1`.

### 3.6 bis - Le gisement le plus rentable: les livrables verifiables en une commande

Sur ces items-la il n'y a rien a juger. On verifie. J'ai extrait les 89 chemins
de fichiers cites en colonne `Prochaine action` ou `Preuve/livrable` du registre
et teste leur existence. Resultat en trois classes.

**Classe A - la preuve est morte parce que le fichier a ete renomme.**
Cinq items citent `AGENTS.md` comme leur livrable ou leur preuve:
`RM-2026-0001`, `RM-2026-0011`, `RM-2026-0013`, `RM-2026-0018`, `RM-2026-0021`.
**Ce fichier n'existe plus**, ni dans le depot ni a la racine du workspace. Le
commit `f421193` du 2026-09-02, `doctrine: AGENTS.md devient CLAUDE.md`, l'a
renomme - et son propre message de commit annonce avoir mis a jour les
references `dans les documents de protocole, la configuration de partage GitHub
et le gouvernail`. La verification dit autre chose: **le gouvernail porte encore
15 occurrences de `AGENTS.md`**, et sept autres documents de `docs/` aussi. La
doctrine, elle, survit intacte dans `CLAUDE.md`. Ce sont les citations qui sont
mortes, pas les items: les cinq restent `INTEGRE` a juste titre.

**Classe B - le fichier est absent, et c'est normal.**
Les cinq livrables de `RM-2026-0047` sont absents de Git parce que sa ligne dit
qu'ils vivent dans le coffre prive. Les trois rapports d'audit cites par
`RM-2026-0008` sont absents pour la meme raison: ce sont des documents
d'instance. Les deux fichiers de `RM-2026-0053` sont absents parce qu'ils vivent
sur une branche non mergee, ce que l'item annonce. Et
`expense_statement_lines_<annee>.csv` cite par `RM-2026-0074` est un gabarit de
nom, dont l'absence est precisement le defaut mesure.

**Classe C - le livrable existe, l'item est vrai.**
Verifie un par un: `tools/check_code_line_limit.py` existe et son execution rend
`OK: no scoped code file exceeds 600 lines` (`RM-2026-0018`); `.githooks/pre-push`
et `tools/git/install-local-guardrails.cmd` existent (`RM-2026-0015`);
`server/tests/test_security_code_injection_guards.py` existe (`RM-2026-0039`);
`server/src/coproscope/modules/instance_layout.py` existe (`RM-2026-0022`);
`docs/veille_malfacons_fraudes_erreurs_copro_matrice_2026-05-27.csv` existe
(`RM-2026-0043`); les cinq modules `pdftrace*` existent (`RM-2026-0045`); et les
quinze routes revendiquees par le registre existent toutes dans `server/src`.

**Ce que cette classe coute a ne pas faire.** `RM-2026-0044` a porte
`PRET_A_INTEGRER` pendant plus de trois mois alors que `LICENSE` disait deja
AGPL. Personne ne pouvait s'en apercevoir sans ouvrir le fichier. Un gouvernail
qui cite un livrable verifiable devrait etre relu contre le disque a chaque
reprise: c'est trente secondes, et cela aurait economise un item mort-vivant et
cinq preuves fantomes.

### 3.7 Cohorte orpheline - 10 items `ACTIF` anterieurs

Le depot a une interruption de trois mois: dernier commit avant l'ete
2026-06-11, reprise 2026-09-02. Aucun commit entre les deux. Ces dix items
portent `ACTIF` sans aucune ligne vivante au registre de presence.

| Item | Derniere MAJ | Etat reel |
|---|---|---|
| `RM-2026-0004` | 2026-05-22 | Orphelin. Prochaine action = recette navigateur jamais faite. |
| `RM-2026-0007` | 2026-05-27 | Orphelin, subordonne a `RM-2026-0014`. |
| `RM-2026-0008` | 2026-05-25 | Orphelin. Reclasse P1 le 2026-06-01, jamais repris. |
| `RM-2026-0014` | 2026-05-27 | Orphelin. Descendant vivant en septembre: `RM-2026-0057`. |
| `RM-2026-0017` | 2026-05-31 | **Cas particulier, voir 5.1.** |
| `RM-2026-0045` | 2026-05-31 | Livrable partiellement merge (`pdftraceops.py`, `pdftrace_contracts.py`, `pdftrace_registry.py`, `pdftrace_zone_text.py`, `pdftrace_preannotation.py` sont presents). Orphelin sur la suite. |
| `RM-2026-0047` | 2026-08-20 | **Non verifiable depuis le depot, voir 5.2.** |
| `RM-2026-0003`, `RM-2026-0006` | 2026-05-22/25 | Non orphelins: `CONV-2026-2090`. |
| `RM-2026-0048` | 2026-09-03 | Non orphelin: `CONV-2026-2100`. |

Six items sont donc reellement orphelins: `0004`, `0007`, `0008`, `0014`,
`0017`, `0045`. Ils ne sont pas morts - le travail reste souhaitable - mais leur
`ACTIF` est faux depuis au moins le 2026-06-11, et il l'etait deja avant le
retrait de l'orchestration.

### 3.8 Doublons, dont le plus couteux traverse les trois mois

**`RM-2026-0041` est l'ancetre direct de quatre items de septembre.** Ouvert le
2026-05-28, `Challenge formats d'ingestion et typologie documentaire metier`,
statut `BLOQUE`, motif: `ne pas executer sans ordre explicite de Brice`. Il
gelait quatre sous-taches `ORD-P1-161` a `ORD-P1-164` sur la taxonomie
documentaire et la promotion d'une piece candidate en preuve.

Trois mois plus tard, la mesure a redecouvert exactement cette matiere, en
quatre items neufs et sans lien vers `0041`:

| Item de septembre | Ce qu'il mesure |
|---|---|
| `RM-2026-0052` defaut (1) | 15 documents classes `PV_AG` pour une seule assemblee reelle, dont 11 fichiers de travail de CoproScope lui-meme |
| `RM-2026-0053` | Evaluer la branche `codex/20260611-coherence-type-contenu`, commit `4bf0e07` |
| `RM-2026-0056` | Remplacer le vocabulaire de domaine par des signatures de forme |
| `RM-2026-0076` | La signature de titre declasse mais ne promeut jamais |

Le commit `4bf0e07` porte la date du **2026-06-11**, c'est-a-dire le dernier jour
d'activite avant l'interruption. Verification: il n'est contenu que dans
`codex/20260611-coherence-type-contenu` et
`integration/20260903-coherence-type-contenu`, jamais dans la ligne principale.
Un correctif ecrit en juin pour un defaut bloque en mai a attendu septembre pour
etre redecouvert par la mesure et redocumente sous quatre identifiants.

Le gouvernail n'offrait aucun moyen de faire ce lien: `RM-2026-0041` est range
`Hors file d'execution` avec la mention `source de cadrage`, donc invisible pour
qui cherche le prochain travail.

**Autres grappes, a une seule cause chacune:**

| Grappe | Items | Cause unique |
|---|---|---|
| Classement documentaire | `0041`, `0052`(1), `0053`, `0056`, `0076` | Le type d'un document est decide sur son etiquette et son vocabulaire, pas sur sa forme ni sur sa provenance |
| Pseudonymisation | `0013`, `0062`, `0065`, `0068`, `0069` | Une seule garde, a la fois trop stricte sur des motifs anodins et aveugle sur des identites sans civilite |
| Etat des depenses | `0030`, `0064`, `0074`, `0075` | L'extracteur d'etat des depenses n'existe pas; tout le module comptable tourne sur des substituts |
| Ecrans qui ne lisent rien | `0024`, `0026`, `0028`, `0031`, `0032`, `0033`, `0059`, `0070` | Une vue peut etre routee, testee et declaree livree sans jamais lire une donnee |
| Provenance | `0056`(2e moitie), `0061` | Rien n'estampille un artefact au moment ou CoproScope l'ecrit |

`RM-2026-0038` (`DecisionOps`, `ROADMAP` depuis mai) est par ailleurs l'ancetre
non cite de `RM-2026-0054` et `RM-2026-0072`, qui construisent le modele
relationnel decision -> depense.

### 3.9 Ce que le lot de septembre fait bien, et ce qu'il fait mal

**Bien.** Chaque item de septembre porte une mesure chiffree et reproductible.
`RM-2026-0058` cite 4 lignes sur 601 portant 94,5 % du total. `RM-2026-0079`
cite 2 209 fichiers sans un seul caractere de remplacement. `RM-2026-0056` cite
0 faux positif sur 37 documents et deux cabinets. Ces lignes sont plus vraies
que la moyenne des lignes de mai. Il ne faut pas les raccourcir.

**Mal.** Elles sont inscrites au mauvais rang. Un constat mesure n'est pas un
chantier: il n'a ni porteur, ni fin, ni ordre. En le promouvant `RM-*` de
premier rang avec un statut `ACTIF`, on lui fait consommer une place dans la
file d'execution qu'il ne peut pas occuper. D'ou les 27 `ACTIF` de septembre
sans porteur.

Deux items de septembre ne sont pas des constats et sont mal ranges pour la
raison inverse: `RM-2026-0060` (generalisabilite comme critere d'acceptation) et
`RM-2026-0063` (tracer une provenance fautive) sont des **doctrines**, du meme
genre que `RM-2026-0013` ou `RM-2026-0018`. Elles ne se terminent pas.

---

## 4. Ce qui a ete applique

Toutes les corrections ci-dessous sont adossees a une preuve citee et
verifiable. Aucune ligne n'a ete supprimee.

### 4.1 Corrections de statut

| Item | Avant | Apres | Preuve |
|---|---|---|---|
| `RM-2026-0044` | `PRET_A_INTEGRER` | `INTEGRE` | `LICENSE` a la racine contient `GNU AFFERO GENERAL PUBLIC LICENSE Version 3`; `server/pyproject.toml:11` porte `license = { text = "AGPL-3.0-only" }` et la ligne 27 le classifieur OSI correspondant. Bascule effectuee dans le commit `b1f9abb` du 2026-05-31; le `LICENSE` du commit initial `ccbd698` etait `Mozilla Public License Version 2.0`. Le livrable est merge depuis plus de trois mois. |
| `RM-2026-0067` | `P1` | `ACTIF` | La colonne `Statut` contenait une priorite. La colonne `Priorite` de la meme ligne porte deja `P1`. Correction de forme, sans jugement sur le fond de l'item. |
| `RM-2026-0017` | `ACTIF` P0 | `ABANDONNE` | Decision de Brice du 2026-09-04. La ligne conserve toute sa trace et inscrit ce qui en est sorti: `instances/tilleul_pseudo_reconstruite_20260904`, 3 447 documents, pipeline complet en 13 minutes, 55 resolutions sur 55 conformes a l'etalon - travail qui vit sous `RM-2026-0071`. `ORD-P0-990` est marque clos en consequence, et **la file `P0` du gouvernail est desormais vide**. |
| `RM-2026-0047` | `ACTIF` | `BACKLOG` | Arbitrage de Brice du 2026-09-04: pour plus tard. `BACKLOG` au sens du tableau des statuts - a suivre, non planifie - et non `ABANDONNE`: attente assumee. Livrables hors depot, avancement non mesurable ici. |

### 4.2 Rectifications datees inscrites dans la ligne, statut inchange

Format repris du precedent `RM-2026-0079`, qui inscrit sa rectification dans sa
propre ligne sans etre efface.

| Item | Ce qui est inscrit |
|---|---|
| `RM-2026-0012` | La route livree affiche une heartbeat demantelee le 2026-09-02 (`56fe402`); `activity_view.py:86` lit ce gouvernail. |
| `RM-2026-0024` | Les deux routes livrees sont des dictionnaires constants; compteurs internes contradictoires. |
| `RM-2026-0026` | Journal `INTEGRATE` du 2026-05-25 contre registre `PRET_A_INTEGRER`; deux vues creuses. |
| `RM-2026-0028` | Journal `INTEGRATE` du 2026-05-25 contre registre `PRET_A_INTEGRER`; vue creuse. |
| `RM-2026-0031` | Vue creuse. |
| `RM-2026-0032` | Vue creuse. |
| `RM-2026-0033` | Journal `INTEGRATE` du 2026-05-25 contre registre `PRET_A_INTEGRER`; vue creuse. |
| `RM-2026-0030` | Chaine comptable dependante d'un extracteur inexistant (`RM-2026-0074`). |
| `RM-2026-0041` | Ancetre bloque des items `0052`, `0053`, `0056`, `0076`. |
| `RM-2026-0047` | Livrables hors depot: avancement non verifiable ici, l'absence de preuve dans le code n'est pas une preuve d'abandon. |
| `RM-2026-0004`, `0007`, `0008`, `0014`, `0045` | Cohorte orpheline: `ACTIF` sans porteur depuis l'interruption du 2026-06-11. `RM-2026-0017`, sixieme membre de la cohorte, est traite par l'arbitrage ci-dessus. |
| `RM-2026-0001`, `0011`, `0013`, `0018`, `0021` | Preuve morte: ces cinq lignes citent `AGENTS.md`, renomme `CLAUDE.md` le 2026-09-02 (`f421193`). Statut inchange, seule la citation est a corriger. |

### 4.3 Bloc d'etat en tete et entrees au journal

Un bloc `Etat de veracite au 2026-09-04` est ajoute apres `Lecture rapide`. Il ne
contient que des grandeurs mesurees et renvoie a la presente note. Neuf entrees
sont ajoutees au journal append-only, en fin de tableau, du `START` au `BOT_END`.

### 4.4 Etat du registre apres application

| Statut | Avant | Apres |
|---|---:|---:|
| `ACTIF` | 37 | 36 |
| `INTEGRE` | 29 | 30 |
| `PRET_A_INTEGRER` | 6 | 5 |
| `ROADMAP` | 3 | 3 |
| `BLOQUE` | 1 | 1 |
| `A_QUALIFIER` | 1 | 1 |
| `BACKLOG` | 0 | 1 |
| `ABANDONNE` | 0 | 1 |
| `P1` (statut invalide) | 1 | 0 |
| **Total** | **78** | **78** |

Controles passes apres application: les 78 lignes du registre ont toutes onze
colonnes; les 24 lignes modifiees sont les seules a differer de la version
d'origine et aucune n'a disparu; les 22 lignes de heartbeat lues par
`activity_view.py` sont intactes; `python tools/presence_lint.py` s'execute; les
tests `tests.test_ui_activityops` et `tests.test_presence_lint` passent, 12 OK.

---

## 5. Les trois cas a ne pas liquider mecaniquement

### 5.1 `RM-2026-0017`, la reconstruction Tilleuls (pseudo) - ABANDONNE, applique

Arbitrage de Brice du 2026-09-04: abandon. Applique, trace conservee, rien
d'efface.

Mon analyse avant arbitrage disait: ni fait ni mort, mais **transforme, et son
identifiant a change sans que personne ne l'ecrive.** L'item designait
l'instance `tilleul_pseudo_reconstruction_sim_20260523/instance`; `RM-2026-0071`,
ouvert le 2026-09-04, decrit une reabsorption depuis les sources primaires dans
une instance fraiche, `tilleul_pseudo_reconstruite_20260904`. Les deux instances
existent cote a cote sous `instances/`.

La precision inscrite dans la ligne, et il faut la lire avec l'abandon: le lot
du 2026-09-04 a produit une instance neuve exploitable - 3 447 documents
absorbes depuis les sources primaires, pipeline complet en 13 minutes, page de
gouvernance servant 55 resolutions sur 55 conformes a l'etalon. **L'abandon
porte sur la sidequest de reconstruction progressive, pas sur l'instance qui en
a resulte**, laquelle vit sous `RM-2026-0071`, actif et distinct.

**Consequence a ne pas manquer: la file `P0` du gouvernail est desormais vide.**
Elle ne contenait que `ORD-P0-990`, qui pointait vers cet item; cette ligne est
close. C'etait le plus gros item du document - `P0` et `ACTIF` depuis le
2026-05-31, sans conversation vivante depuis l'interruption du 2026-06-11. La
prochaine priorite P0 doit etre arbitree, pas deduite.

### 5.2 `RM-2026-0047`, l'audit juridique des comptes bancaires

Sa ligne dit elle-meme que ses livrables vivent hors depot, dans le coffre
prive: `GRILLE_juridique_audit_comptes.md`, `convertir_releves_csv.py`,
`PROTOCOLE_conversion_csv.md`, `controle_arithmetique_releves.py`,
`ocr_releves.py`. Aucun de ces fichiers n'a a etre dans Git, et c'est correct.

**Je ne peux pas mesurer son avancement, et je le dis plutot que de le classer
mort faute de preuve.** Sa date de mise a jour, 2026-08-20, tombe d'ailleurs en
plein dans l'interruption du depot: c'est un travail qui a eu lieu sans laisser
de trace de code, ce qui est exactement ce que sa ligne annonce.

Arbitrage de Brice du 2026-09-04: **pour plus tard**. Applique en `BACKLOG` au
sens du tableau des statuts du gouvernail - a suivre, non planifie - et non en
`ABANDONNE`: c'est une attente assumee. Ma reserve est levee par cet arbitrage.

Il reste un manque de structure a corriger avant reprise, et il n'est pas propre
a cet item: **un item dont les preuves vivent hors depot doit declarer une
source de verite et une date de dernier point**, sinon le prochain auditeur le
reclassera mort faute de preuve, ce qui serait faux. C'est la proposition P8.

### 5.3 `RM-2026-0044`, la bascule AGPL - INTEGRE, applique

Verifiable en une commande, et deja faite depuis le depart. Voir 4.1 pour les
preuves, et 3.6 bis pour ce que ce cas enseigne au-dela de l'item.

---

## 6. Structure cible

**En une phrase.** Separer le gouvernail en trois registres de durees de vie
differentes - **doctrines** (des regles qui ne se terminent pas), **chantiers**
(un porteur, un livrable, une fin) et **constats mesures** (un fait date et
prouve, sans porteur, qui alimente un chantier) - et ne laisser le statut
d'avancement que sur le registre des chantiers.

**Pourquoi elle survit a un debit eleve.** Parce qu'un debit eleve produit
massivement des constats et tres peu de chantiers. Un constat coute une ligne,
n'a besoin ni de porteur ni de conversation, et sa seule question est
`toujours vrai / refute / solde par tel chantier`. Aujourd'hui le format oblige
chaque constat a devenir un chantier `ACTIF`, donc a occuper une place dans la
file d'execution qu'il ne peut pas tenir. Trente constats vrais valent mieux
qu'un item vague - mais pas au rang de chantier. Le lot de septembre a produit
de la bonne matiere mal rangee; le rangement, lui, etait deja casse en mai.

**Une seconde dimension, obligatoire, qui repare le defaut anterieur.** Ajouter
a chaque chantier un `NIVEAU_DE_REEL` independant du statut:

| Niveau | Sens | Test |
|---|---|---|
| `MAQUETTE` | La vue retourne un contenu ecrit a la main | La fonction de construction ne prend pas d'instance |
| `BRANCHE` | La vue lit une source reelle de l'instance | Un acces coffre, base ou fichier existe |
| `EPROUVE` | Le traitement a tourne sur un second jeu de donnees | Un second syndic, un second exercice |

Les huit vues du 3.3 deviennent immediatement lisibles comme `MAQUETTE`, sans
qu'aucune ligne soit supprimee ni aucun travail renie. Le niveau `EPROUVE` est
exactement le critere que `RM-2026-0060` demande deja - il n'y a rien a
inventer, seulement une colonne a creer.

---

## 7. Propositions, ordonnees par gain, avec leur cout

Aucune n'est appliquee. Brice tranche.

### P1 - Marquer les huit ecrans `MAQUETTE` et decider un par un: brancher ou retirer
**Gain: le plus eleve du lot.** Sept lignes du gouvernail cessent d'annoncer une
capacite produit inexistante. Le compte des fonctions reellement disponibles
devient juste.
**Cout:** il faut assumer que sept fonctions annoncees depuis mai ne sont pas
faites, et arbitrer sept fois. Trois de ces ecrans pesent 400+ lignes de contenu
ecrit a la main qui seront perdues si on retire au lieu de brancher.
**Perimetre exact:** `RM-2026-0024`, `0026`, `0028`, `0031`, `0032`, `0033`, plus
`ORD-P2-040`. Recoupe `RM-2026-0059`, qui demande deja cette decision pour
quatre d'entre eux.

### P2 - Sortir le journal du gouvernail
**Gain: -560 lignes environ, soit 61 % du fichier.** Le journal fait 596 lignes
sur 974. Ses entrees s'arretent en juin sauf deux; 122 lignes datent d'une seule
journee, le 2026-05-25. Il porte 22 references a une heartbeat demantelee.
**Cout, et il est reel:** `server/src/coproscope/web/activity_view.py:86` lit ce
fichier et `_heartbeat_rows` filtre sur la chaine litterale
`relance-equipe-agile-gouvernail-autonome`. Deplacer le journal vide en silence
le bloc heartbeats de `/pilotage/activite`. **Cette proposition doit donc etre
un lot code + doc, rattache a `RM-2026-0012`, jamais un simple deplacement de
document.** Garder dans le gouvernail les entrees des 30 derniers jours.

### P3 - Fusionner les cinq items de classement documentaire en un chantier et quatre constats
**Gain: la grappe la plus couteuse du document se lit d'un coup, et le lien avec
`RM-2026-0041` bloque en mai devient visible.** Un correctif ecrit le 2026-06-11
(`4bf0e07`) dort sur une branche pendant que quatre items le redecouvrent.
**Cout:** `RM-2026-0041` est `BLOQUE` avec la mention `ne pas executer sans
ordre explicite de Brice`. Le debloquer est une decision, pas un rangement. Et
les quatre constats de septembre portent chacun une mesure precise qu'il ne faut
pas fondre dans un resume.
**Perimetre:** `RM-2026-0041` + `0052`(1) + `0053` + `0056` + `0076`.

### P4 - TRANCHE le 2026-09-04, et il en reste une question ouverte
`RM-2026-0017` est `ABANDONNE`, `ORD-P0-990` est clos, **la file `P0` du
gouvernail est vide.**
**Ce qui reste a decider, et qui n'est pas un rangement:** quelle est la
prochaine priorite P0 du produit. Elle doit etre arbitree explicitement. En
l'etat, un agent qui applique la regle du gouvernail - `prendre le plus petit
ORD-* actionnable dans la priorite la plus haute` - descend directement en P1
sur `ORD-P1-010`, une tache de mai dont l'item porteur `RM-2026-0024` est l'un
des sept ecrans creux. **Sans arbitrage, la regle de choix du prochain travail
renvoie aujourd'hui vers une maquette.**
**Reserve conservee:** le perimetre residuel de `0017` - file OCR visible,
doublons, fiche detail protegee, pre-file factures 2025 - n'a pas ete verifie un
par un dans `tilleul_pseudo_reconstruite_20260904`. L'abandon est une decision, pas
un constat d'equivalence; si l'un de ces points manque, il doit rouvrir sous un
identifiant propre.

### P5 - Reclasser les constats de septembre au rang de constats
**Gain:** les 27 `ACTIF` de septembre sans porteur cessent de saturer la file.
Le compte des chantiers reellement ouverts devient lisible.
**Cout: nul en information, mais il change la lecture.** Un constat n'apparait
plus dans la file d'execution; il faut donc que le registre des constats soit
lu a chaque ouverture de chantier, sinon on perd le benefice de la mesure. C'est
un changement d'habitude, pas de fichier.

### P6 - Deplacer `RM-2026-0060` et `RM-2026-0063` au registre des doctrines
**Gain:** deux items qui ne peuvent pas se terminer cessent de porter `ACTIF`.
**Cout:** negligeable.

### P7 - Retirer de la file `ORD-*` les lignes dont l'item n'a plus de porteur
**Gain: environ -60 lignes**, et la file cesse de proposer du travail que
personne ne peut prendre. Les `ORD-P1-161` a `ORD-P1-164` sont bloques depuis le
2026-05-28 mais restent dans le tableau d'ordre.
**Cout:** la file est la seule vue ordonnee du document. La vider trop la rend
inutile; il faut y garder les chunks encore vises meme sans porteur, en les
marquant `SANS PORTEUR` plutot qu'en les retirant.

### P8 - Declarer une source de verite pour les items dont les preuves sont hors depot
**Gain:** `RM-2026-0047` et `RM-2026-0008` cessent d'etre invisibles a tout audit
mene depuis le depot. Aujourd'hui, la seule facon de les classer est de dire
`je ne sais pas`.
**Cout:** il faut nommer, dans la ligne, un artefact du coffre prive et une date
de dernier point - sans jamais recopier son contenu dans le depot.

### P9 - Corriger les cinq citations de `AGENTS.md`
**Gain:** cinq preuves fantomes redeviennent verifiables, et la classe entiere
des livrables verifiables en une commande redevient fiable. Le meme defaut
existe dans sept autres documents de `docs/`, hors perimetre de ce lot.
**Cout: quasi nul, et c'est precisement ce qui le rend embarrassant.** Le commit
`f421193` annoncait deja avoir fait ce travail.

### Volume apres application

| Etape | Lignes |
|---|---:|
| Aujourd'hui | 974 |
| P2, journal sorti (30 derniers jours gardes) | ~414 |
| P7, file `ORD-*` elaguee | ~354 |
| P1/P3/P5/P6, en-tetes des trois registres et rectifications | ~410 |

**Cible: environ 410 lignes**, soit 42 % du volume actuel, avec strictement plus
d'information vraie qu'aujourd'hui: rien n'est efface, tout ce qui est deplace
l'est vers un fichier nomme et cite.

---

## 8. Limites de ce controle

- Les livrables de `RM-2026-0047` sont hors depot: aucune conclusion sur son
  avancement.
- Le classement `vrai et fait` repose sur l'existence du code et des documents
  cites, pas sur une recette navigateur. Une route peut exister, lire des
  donnees, et rester inutilisable: c'est ce que `RM-2026-0051` mesure par
  ailleurs.
- Les huit vues creuses ont ete mesurees par lecture statique - signature de la
  fonction de construction et absence d'acces donnees. Quatre d'entre elles sont
  confirmees independamment par `docs/audit_pages_controle_2026-09-03.md`; les
  quatre autres n'ont pas ete ouvertes dans un navigateur.
- La vivacite des conversations vient de `tools/presence_lint.py`, qui compte
  les lignes declarees actives. Il ne prouve pas qu'un agent tourne.
- Aucune donnee d'instance, aucun nom de coproprietaire, aucun chemin local
  sensible n'apparait dans cette note.
