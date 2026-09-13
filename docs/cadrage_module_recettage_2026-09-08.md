# Cadrage: instrument de session pour la recette d'interface

**Statut: cadrage, non executoire.** Ce document decrit un outil de session qui vit
entierement hors du depot produit. Il ne declare aucun chantier, aucun owner et aucun port.
Il se termine par une gate GO/NO-GO dont la premiere condition appartient au coordinateur
qui prendra le relais.

**Rattachement gouvernail:** `RM-2026-0114`. Chevauchement declare avec `RM-2026-0006`
(qualite live, tests novice et regression UI) et avec `RM-2026-0111` (aucun moteur de rendu
dans la suite) - ce cadrage n'y touche pas, il en depend.

**Sources mesurees, reutilisees sans etre refaites:**

- [`docs/roadmap_backlog_central.md`](./roadmap_backlog_central.md) - `RM-2026-0111`,
  `RM-2026-0112`, `RM-2026-0113`, les trois defauts d'interface releves le 2026-09-07.
- [`docs/mode_recette_annotations_2026-05-31.md`](./mode_recette_annotations_2026-05-31.md) -
  le cadrage V1 du mode recette produit, et ses limites deja declarees.
- [`docs/cadrage_annuaire_verificateur_biffage_2026-09-07.md`](./cadrage_annuaire_verificateur_biffage_2026-09-07.md) -
  le moule de forme suivi ici.

---

## 1. Probleme utilisateur

Brice explore CoproScope sur ses donnees reelles pour en juger l'interface. Aujourd'hui,
tout retour passe par de l'ecrit: il doit interrompre son parcours, decrire ce qu'il
regarde, nommer un element dont il ne connait pas le nom technique. Le cout est tel qu'il ne
signale que les defauts qui l'arretent net.

Ce qui se perd est precisement ce qui vaut le plus cher: l'hesitation devant un libelle, le
va-et-vient entre deux blocs qu'il compare, le clic sur ce qui n'est pas cliquable, le
defilement en marche arriere parce qu'il a rate quelque chose, et l'endroit ou il abandonne.
Aucun de ces signaux ne se raconte apres coup, parce qu'on ne s'en souvient pas.

*Formulation novice:* « je veux pouvoir me promener dans l'outil en disant tout haut ce que
je pense, et qu'a la fin on sache de quoi je parlais a chaque phrase, sans que j'aie eu a
noter quoi que ce soit. »

Le mode recette du produit ne repond pas a ce besoin et n'a pas ete concu pour: il capte
une remarque a la fois, sur un element, sans sequence ni continuite entre les ecrans. Il a
ete corrige deux fois le 2026-09-07 sur signalement direct de Brice, qui a nomme le cout de
l'exercice - le fil a passe vingt minutes a reparer son propre outillage au lieu du produit.

---

## 2. Perimetre

**Dans le perimetre:**

- Enregistrer le parcours dans l'interface web locale: survols, clics, focus, defilements de
  page et de conteneur interne, largeur de fenetre, touches de navigation.
- Enregistrer la voix pendant que Brice pense a voix haute.
- Transcrire cette voix en local, avec horodatage au mot.
- Aligner les deux flux et rendre une chronologie ou chaque phrase porte l'element regarde.
- Purger l'audio et les libelles quand la session est close.

**Hors perimetre, et il faut le dire:**

- **Toute modification du code produit.** Raison technique en section 4, pas une preference.
- **La diarisation.** Arbitrage de Brice du 2026-09-07: pour une pensee a voix haute il n'y
  a qu'un locuteur. Consequence assumee en section 8.
- **Toute capture d'ecran, video ou instantane du DOM.** Un instantane du DOM est une
  capture d'ecran sous un autre nom: memes donnees reelles, meme piece a caviarder.
- **Tout texte saisi, toute valeur de champ, tout contenu de cellule.** Conserve du traceur
  existant, qui ne les capture deja pas.
- **Tout retour en temps reel.** Tout est post-hoc.
- **Tout envoi reseau sortant**, hors le telechargement du modele de transcription, une
  fois.
- **Toute comparaison entre sessions** ou suivi de regression UX. Le format machine de la
  section 5 le prepare; c'est un lot ulterieur.

---

## 3. Exigences

### Fonctionnelles

| # | Exigence |
|---|---|
| F1 | Le parcours est enregistre sans perte a travers plusieurs pages, y compris au moment de la navigation. |
| F2 | La voix est enregistree en continu sur toute la session, sans trou aux changements de page. |
| F3 | Les deux flux partagent une reference de temps prouvee, pas supposee. |
| F4 | Chaque phrase transcrite porte l'element regarde, sa confiance, et la liste des candidats ecartes. |
| F5 | Les signaux que la voix ne dit pas - clic mort, va-et-vient, defilement arriere, sejour long sans action, rupture de largeur - sont marques dans la chronologie meme sans phrase associee. |
| F6 | Une session close peut etre purgee de son audio et de ses libelles sans perdre sa chaine de preuve. |

### Non fonctionnelles

| # | Exigence | Raison |
|---|---|---|
| N1 | Aucun octet de ce module n'entre dans `server/`. | Le `.spec` PyInstaller embarquerait la pile de transcription. Mesure en section 4. |
| N2 | Aucun fichier de session n'entre dans Git ni dans un worktree. | Le corpus est reel. `CLAUDE.md`: instances privees hors depot, jamais commitees. |
| N3 | Aucune donnee ne quitte le poste. | Meme regle, et elle est la raison pour laquelle aucun outil de recette du commerce n'est utilisable ici: ils televersent tous une capture de la page. |
| N4 | Le traceur ne doit pas degrader la fluidite de l'application qu'il mesure. | Defaut mesure sur la version actuelle, section 6. Un instrument qui change ce qu'il mesure ne mesure plus. |
| N5 | L'outil dit ce qu'il ne sait pas au lieu de repondre faux. | Doctrine du depot sur les axes de generalisation. Applique a l'alignement en section 8. |

### Contraintes de contexte

- Poste Windows. Aucun `ffmpeg` dans le `PATH` systeme.
- Les seuls Python enregistres sont 3.14 et 3.8. Les environnements 3.12 utilisables vivent
  dans un cache de runtime Codex, qui peut etre efface sans preavis.
- La suite de tests du depot ne contient aucun moteur de rendu (`RM-2026-0111`), donc aucune
  mise en page n'y est evaluee.
- Brice a explicitement ecarte les tests pour ce module. Consequence en section 13.

---

## 4. Le pivot: la machinerie existe deja

Brice a autorise l'installation de la machinerie de transcription. **La mesure a renverse la
demande: elle est deja installee, et elle fait meme la diarisation.**

**Verifie le 2026-09-08 en lisant le disque:**

`C:\Users\brice\AppData\Local\Codex\audio-transcription\.venv` - Python 3.12.13 cree avec
`uv`, meme interpreteur que `server/.venv`.

| Role | Paquets presents |
|---|---|
| Reconnaissance | `faster_whisper` 1.2.1, `ctranslate2` 4.8.0, `av`, `onnxruntime` |
| Diarisation | `speechbrain` 1.1.0, `torch` 2.12.0, `torchaudio`, `scikit_learn` |
| Audio | `imageio_ffmpeg` 0.6.0, qui **embarque son propre binaire ffmpeg 7.1** |

Et le pilote existe: `dev/tooling/scripts/transcribe_diarize_audio.py`, **401 lignes**,
ecrit et utilise le 2026-06-08. Chaine: ffmpeg vers WAV 16 kHz mono PCM16, puis
`WhisperModel` CPU `int8` `large-v3-turbo` en francais avec filtre VAD, ecriture de
`segments_raw.jsonl` au fil de l'eau, puis empreintes ECAPA et clustering agglomeratif dont
le nombre de locuteurs est choisi par score de silhouette.

**Deux manques seulement:**

1. Le modele CT2 n'est plus en cache - `~/.cache` ne contient que `claude` et
   `codex-runtimes`. Un telechargement au premier usage.
2. **Le script n'a aucun lanceur et n'est reference nulle part** dans tout
   `C:\Users\brice\CoproScope`, contenu compris. C'est pourquoi il etait introuvable: un
   outil sans point d'entree est un outil qui n'existe pas.

### Pourquoi rien de tout cela ne peut vivre sous `server/`

`server/packaging/windows/CoproScope.spec` ne liste pas ses dependances, **il les
decouvre**. `source_declared_imports` (l.26-45) parse en AST **tous les `.py` et tous les
`.pyfrag`** de `server/src/coproscope/`, collecte chaque nom importe, et `available_imports`
(l.47-56) garde tout nom que `importlib.util.find_spec` resout. Puis `excludes=[]` (l.89).

**Consequence directe: un seul `import torch` ecrit n'importe ou sous `server/src/`, meme
dans une branche jamais executee, meme sous `try/except ImportError`, entre dans le
paquet.** Le venv de transcription pese 999 Mo; l'executable en pese 155.

Second verrou: `server/src/coproscope/web/static/recette_mode.js` est a **533 lignes sur un
plafond de 600**. La doctrine du depot impose d'extraire avant d'ajouter.

---

## 5. Blueprint

```text
   NAVIGATEUR                          HORS NAVIGATEUR
   ----------                          ---------------

   trace_parcours.js                   enregistrer_voix.py
   (signet, arme par page)                    |
        |                                     | ffmpeg -f dshow
        | survol / clic / focus               v
        | defilement / largeur          voix.wav  (16 kHz mono PCM16)
        | top sonore 1 kHz                    |
        v                                     |
   sendBeacon + fetch 5 s                     |
        |                                     |
        v                                     v
   collecteur.py  ------>  journal.jsonl   session.json  <---- horloge
   (port 8791)                    |         (3 estimations du zero)
                                  |              |
                                  |              v
                                  |        detecter_top.py
                                  |        (Goertzel 1 kHz)
                                  |              |
                                  |              v
                                  |        transcrire_session.py
                                  |        [ venv Codex existant ]
                                  |              |
                                  |              v
                                  |     voix.transcription.json
                                  |         (words[] horodates)
                                  v              v
                            +--------------------------+
                            |   fusionner_parcours.py  |
                            |   fenetre asymetrique    |
                            |   -2000 ms / +500 ms     |
                            +--------------------------+
                                       |
                    +------------------+------------------+
                    v                  v                  v
             chronologie.md     par_element.md       fusion.json
             (a lire)           (items de roadmap)   (machine)
```

### Les quatre decisions qui portent le reste

**5.1 L'audio s'enregistre hors du navigateur.**

| | `MediaRecorder` dans la page | ffmpeg `dshow` |
|---|---|---|
| Survie a une navigation | Non. Contexte detruit, flux coupe, blob en cours perdu. | Oui. Processus independant. |
| Ce que coute le contournement | Un fichier par vie de page, **avec un trou a l'instant du clic qui change de page et pendant le chargement** - les deux moments ou l'on commente le plus. | - |
| Format produit | webm/opus, donc une conversion en plus. | WAV 16 kHz mono PCM16 **directement**, le format que la transcription attend. |
| Horloge | Partagee avec le journal. Son seul avantage. | Deux processus, decalage a mesurer. Resolu en 5.2. |

Le seul avantage de `MediaRecorder` est un probleme soluble une fois pour toutes; sa
faiblesse est insoluble et frappe les moments les plus riches.

*Verifie:* le binaire embarque declare `dshow`, et l'enumeration rend **un** peripherique
audio sur ce poste. *Non verifie:* que l'ouverture reelle du flux reussisse - Windows peut
la refuser en silence et produire un enregistrement muet. C'est V2 du lot 0.

*Piege d'encodage:* le nom convivial du peripherique porte des accents et un symbole. On
n'utilise que le **nom alternatif** `@device_cm_{...}\wave_{...}`, ASCII pur, passe par une
liste `subprocess.run([...])` - jamais par un `.cmd` ni par un shell.

**5.2 L'horloge se prouve.**

Trois estimations de « a quel instant d'epoque correspond l'echantillon 0 du WAV », toutes
trois ecrites dans `session.json`:

1. **L'epoque relevee au lancement** - majore l'instant reel de toute la latence
   d'ouverture. Garde-fou, pas reference.
2. **La mediane des blocs `-progress`** de ffmpeg. A chaque bloc on releve l'epoque locale
   `L` et `out_time_us`, et on calcule `L - out_time_us/1000`. La mediane donne le decalage,
   l'ecart interquartile donne le jitter, **la pente revele une derive** entre l'horloge du
   peripherique et celle du systeme. Reference par defaut.
3. **Le repere audible.** Le navigateur emet un sinus 1 kHz par `AudioContext` et journalise
   son `Date.now()`; `detecter_top.py` le retrouve dans le WAV par filtre de Goertzel.

**Deux tops, pas un: un a l'ouverture, un a la fermeture.** Un seul top corrige le decalage;
deux mesurent en plus la derive. Sur 45 minutes, 0,1 % de derive fait 2,7 secondes - assez
pour rattacher une phrase au mauvais element. Deux tops autorisent une correction affine au
lieu d'une simple translation.

**Cas d'echec nomme: le casque.** Si Brice porte un casque, le haut-parleur n'atteint pas le
micro et le top n'est jamais capte. Repli, et il n'a aucune dependance materielle: **Brice
dit l'heure a voix haute** au debut et a la fin. Whisper la transcrit, elle est directement
comparable au journal, et elle reste lisible par un humain six mois plus tard.

**5.3 Le journal ne transite plus par `localStorage`.**

C'est le vrai levier, pas la reinjection: tant que le journal vit dans la page, chaque mort
de page est un risque de perte. `collecteur.py` ecoute en local; le traceur pousse toutes
les 5 s et **sur `beforeunload` par `navigator.sendBeacon`**, concu pour survivre au
dechargement. Le collecteur horodate chaque lot a reception, ce qui donne au passage un
controle independant que l'horloge du navigateur concorde avec celle des processus Python.

Des lors, l'injection n'a plus qu'a rearmer les ecouteurs, et **un signet suffit**: on perd
les quelques secondes entre l'affichage et le clic, plus rien d'autre. L'armement
automatique par CDP devient une amelioration, pas un prerequis.

**5.4 La fenetre de rattachement est asymetrique: `[debut - 2000 ms, fin + 500 ms]`.**

Motif, et il doit rester ecrit dans le code: **on nomme ce qu'on vient de voir, pas ce qu'on
va voir.** Le regard precede la phrase d'une a deux secondes. Une fenetre symetrique
rattacherait systematiquement les phrases a l'element suivant. Les deux marges sont des
parametres de ligne de commande - ce sont des hypotheses, pas des constantes - et le rendu
ecrit leurs valeurs dans son en-tete.

Cascade de rattachement quand plusieurs evenements tombent dans la fenetre:

1. **Un clic** - acte delibere, l'ancrage le plus fort. Deux clics: le dernier.
2. **Sinon un focus** - intention declaree sans engagement.
3. **Sinon le survol de plus longue duree de sejour**, deduite de l'ecart avec le survol
   suivant. **Le plus long regard gagne, pas le dernier** - c'est la difference entre
   l'element qu'il traversait et celui qu'il regardait.
4. **Sinon, seulement du defilement** - rattachement a la page.
5. **Sinon rien** - la phrase est conservee telle quelle. Une phrase orpheline est une
   donnee, pas une erreur: c'est souvent la phrase de synthese, celle qui vaut un item.

Chaque rattachement porte une confiance et **la liste complete des candidats avec leur
sejour**.

---

## 6. Les quatre defauts du traceur actuel

`dev/outils_recette/trace_parcours.js`, 128 lignes. Trouves en le relisant, pas supposes.
Ils cassent precisement l'usage multi-pages vise.

1. **`t` est incoherent d'une page a l'autre.** `depart` est reinitialise a chaque injection
   alors que le journal est recharge depuis `localStorage`. Les anciennes entrees gardent un
   `t` calcule sur un autre `depart`. **La colonne `t` est inexploitable des la deuxieme
   page;** seul `ms` l'est, et la fusion doit recalculer.
2. **Cout quadratique.** `JSON.stringify(journal.slice(-4000))` est execute **a chaque
   evenement**, y compris a chaque changement de cible de survol. En fin de session le
   traceur re-serialise des centaines de kilo-octets a chaque mouvement de souris. Ce n'est
   pas seulement lent: **il ralentit l'application qu'on juge sur sa fluidite, donc il
   contamine sa propre mesure.** Correction: ecriture par lot.
3. **Perte silencieuse.** `slice(-4000)` jette les entrees **les plus anciennes** sans le
   dire. Le debut de session - la decouverte, le premier viewport - est ce qui disparait en
   premier. Correction: marqueur de troncature visible.
4. **`lib` porte les noms.** `libelle()` prend `textContent` sur 70 caracteres. Sur une
   ligne de tableau de coproprietaires, `textContent` **est** un nom, un lot et un montant.
   L'en-tete du fichier affirme qu'un journal de parcours n'a aucune raison de porter des
   noms; le code, lui, en porte. Traite en R4.

---

## 7. Contrat de donnees

`sessions/<id>/session.json` - le contrat entre tous les lots.

| Champ | Sens |
|---|---|
| `session_id` | `AAAAMMJJ-HHMM-<slug>`, sans nom de personne ni donnee d'instance |
| `audio.chemin` / `sha256` / `hz` / `canaux` / `duree_s` / `arret` | `arret` vaut `propre` ou `brutal`; le sha256 survit a la purge |
| `peripherique.api` / `nom_alternatif` / `nom_convivial` | Le nom alternatif est celui reellement passe a ffmpeg |
| `commande_ffmpeg` | La liste d'arguments exacte, pour que la mesure soit rejouable |
| `horloge.epoch_lancement_ms` | Garde-fou |
| `horloge.epoch_zero_par_progress_ms` / `progress_jitter_ms` / `progress_echantillons` | Reference par defaut, avec sa dispersion |
| `horloge.tops[]` | `{role: ouverture\|fermeture, epoch_ms, audio_s, methode}` |
| `horloge.derive_ppm` | Non nul seulement si deux tops ont ete captes |
| `horloge.reference_retenue` | `progress` \| `top_unique` \| `deux_tops` \| `heure_dite` |
| `journal.entrees` / `premier_ms` / `dernier_ms` / `libelles_captures` | `libelles_captures` conditionne la purge R4 |
| `serveur.port` / `instance` | Le contrat de serveur du lot, comme tout port |

**`reference_retenue` est le champ le plus important du fichier.** Il rend visible, dans
tous les rendus, **sur quelle base l'alignement a ete fait**. Un alignement `progress` sans
top n'a pas la meme valeur qu'un alignement a deux tops, et le lecteur doit le savoir avant
d'en tirer un item de gouvernail.

---

## 8. Degradation: ne jamais repondre faux en silence

| Situation | Comportement exige |
|---|---|
| Aucun top capte | `reference_retenue = progress`, `derive_ppm = null`, et **une banniere en tete de chaque rendu** disant que l'alignement n'a pas de controle independant |
| Un seul top capte | Translation seule, derive non mesuree, dit dans la banniere |
| Jitter `progress` au-dela d'un seuil | Le rendu le publie en chiffre; il n'est jamais tu |
| Plusieurs candidats dans la fenetre | Confiance `faible`, **tous les candidats publies avec leur sejour** |
| Aucun evenement dans la fenetre | `ancrage: aucun`, la phrase est conservee |
| Le venv de transcription a disparu | Echec **fort et nomme** - « le venv de transcription est absent, chemin attendu X » - jamais un rendu partiel silencieux |
| Le journal s'arrete avant l'audio | Le rendu dit a partir de quelle minute il n'y a plus de parcours |

**Le cas interdit** est celui d'un rendu qui presente un rattachement sans dire qu'il repose
sur une horloge non controlee. C'est la forme, ici, du defaut que le depot combat partout
ailleurs: une valeur affichee dont on ne sait pas si elle est mesuree ou repliee.

---

## 9. Confidentialite

| # | Regle | Ou |
|---|---|---|
| R1 | **Un seul lieu d'ecriture:** `dev/outils_recette/sessions/<id>/`. Le collecteur et l'enregistreur **refusent de demarrer** si le chemin resolu contient `\coproscope\` ou `\worktrees\`. Garde-fou en dur, pas une consigne. | lots 1, 2 |
| R2 | **Le coffre Obsidian.** `C:\Users\brice\CoproScope` est un coffre avec le greffon Sync active et **aucun coffre distant configure** - risque latent, pas actif. Si un Sync est un jour raccorde, `dev/` entre dans le perimetre synchronise. Corollaire: le greffon `audio-recorder` d'Obsidian est active et ecrit ses `.webm` **dans le coffre** - ne jamais l'utiliser ici. | V1, lot 6 |
| R3 | **Ceinture et bretelles Git.** Un `.gitignore` dans `outils_recette/` - inerte aujourd'hui puisque `dev/` est hors depot, correct le jour ou quelqu'un y fait un `git init` ou copie le dossier dans un worktree. | lot 6 |
| R4 | **Le journal ne capture plus de libelles par defaut.** Scission: `role` - balise, premiere classe, `aria-label`, `title`, **jamais `textContent`** - toujours capture; `lib` seulement si arme explicitement. Defaut: desarme. Et `--sans-libelles` purge a posteriori. | lot 2 |
| R5 | **`location.pathname`, jamais `href` ni `search`** - le jeton d'acces vit dans la chaine de requete. | lot 2 |
| R6 | **Aucun dump d'environnement dans un fichier de session**, et le sous-processus de transcription est lance **avec `HF_TOKEN` retire**. Motif verifie: ce jeton est exporte en clair dans l'environnement du poste. Le modele est public. | lots 1, 3 |
| R7 | **L'audio se purge.** Le WAV ne sort jamais de `sessions/<id>/`. Chaque rendu porte en tete: *« Contient de la parole non relue. Peut nommer des personnes. Ne pas coller dans un ticket ou un document produit sans relecture ligne a ligne. »* `--purger-audio` supprime le WAV en conservant taille et sha256: la chaine reste auditable sans que la voix reste sur le disque. | lot 6 |

> **Signalement hors perimetre.** `HF_TOKEN` est defini en clair dans l'environnement
> utilisateur du poste - 37 caracteres, prefixe `hf_`, valeur jamais affichee. Tout
> processus lance sous cette session le lit, y compris un agent dote d'un shell. A revoquer
> et deplacer. Ce n'est pas un travail de ce lot: c'est le compte de Brice.

---

## 10. Criteres d'acceptation

| # | Critere | Mesure |
|---|---|---|
| A1 | ffmpeg ouvre reellement le micro et le WAV n'est pas muet | Capture de 5 s, pic non nul. **Non mesure a ce jour** - V2 du lot 0 |
| A2 | Un parcours de trois pages ne perd aucun evenement | Le nombre d'entrees de `journal.jsonl` egale le compteur du navigateur, et il porte trois `ouverture` |
| A3 | Le zero d'horloge est etabli et sa dispersion publiee | `session.json` porte `epoch_zero_*`, `progress_jitter_ms` et `reference_retenue` |
| A4 | L'ecart entre l'horodatage rendu et l'heure reelle notee a la main est sous la seconde | Session scenarisee de 3 min, une phrase convenue sur un element convenu |
| A5 | Le rattachement ambigu se degrade visiblement | Un cas construit ou deux survols se partagent la fenetre rend `confiance: faible` et publie les deux candidats |
| A6 | Aucun libelle dans les rendus quand les libelles sont desarmes | `grep -c` sur `lib` rend 0 |
| A7 | Rien n'entre dans Git | `git status --short` propre dans le depot et dans tous les worktrees, apres une session complete |

**Ce que ces criteres ne couvrent pas, et il faut le dire:** aucun ne verifie que la
transcription est fidele. Whisper peut se tromper, et rien ici ne le detecte. La relecture
humaine du rendu reste obligatoire avant d'en tirer un item de gouvernail - c'est ce que
dit la banniere de R7.

---

## 11. Les sept lots

**Apres les lots 0, 1 et 2, une vraie session est deja tenable:** un WAV, un journal continu
et une horloge commune, lisibles cote a cote a la main. Le lot 4 supprime le travail manuel;
il ne cree pas la capacite.

| Lot | Objectif | Fichiers | Preuve | Depend de |
|---|---|---|---|---|
| **0 · Verifications** | Repondre par la mesure aux six questions dont depend le reste. Aucun code. | `VERIFICATIONS.md` | Les six reponses avec leurs commandes exactes | - |
| **1 · Capture audio** | Un WAV et un zero date | `enregistrer_voix.py`, `config_poste.json` | Capture 60 s; le sidecar donne decalage et jitter; un claquement de mains a une heure notee se retrouve a moins d'une seconde | 0 (V2,V3,V4) |
| **2 · Traceur et collecteur** | Un parcours multi-pages sans perte | `trace_parcours.js` (modifie), `collecteur.py`, `construire_signet.py`, `README.md` | A2 | - *parallelisable avec 1* |
| **3 · Transcription** | Du WAV aux segments horodates **au mot** | `transcrire_session.py`; `transcribe_diarize_audio.py` (modifie) | 60 s de WAV rendent un JSON avec `words[]` peuple; temps mural note | 0 (V5), 1 |
| **4 · Fusion et rendu** | La chronologie alignee | `detecter_top.py`, `fusionner_parcours.py` | A4, A5 | 1, 2, 3 |
| **5 · Armement auto** | Supprimer le clic de rearmement | `armer_chrome.py`, `cdp_minimal.py` | Cinq navigations sans geste, cinq `ouverture` | 2 - **optionnel** |
| **6 · Cloture et purge** | Qu'une voix ne reste pas sur le disque | `cloturer_session.py`, `.gitignore` | A6, A7 | 4 |

### Lot 0 - les six verifications

| # | Question | Ce qu'elle decide |
|---|---|---|
| V1 | Le coffre Obsidian a-t-il un Sync raccorde ? | L'emplacement de `sessions/` |
| V2 | ffmpeg ouvre-t-il reellement le micro ? | Tout le lot 1 |
| V3 | Arret propre par `q` sur stdin; un WAV laisse par un processus tue reste-t-il decodable ? | La robustesse de la capture |
| V4 | Cadence et jitter des blocs `-progress` | Si le decalage suffit ou si le top devient obligatoire |
| V5 | **Cout de la transcription:** taille et temps du modele, puis facteur temps-reel sur 60 s | `large-v3-turbo` ou descendre a `small` - entre 45 min transcrites en 10 min ou en 2 h, l'outil n'a pas le meme usage |
| V6 | Haut-parleurs ou casque ? | Top sonore ou heure dite a voix haute |

### Deux points a assumer dans le lot 3

- **`--word-timestamps` n'est pas optionnel.** Sans horodatage au mot, une phrase de huit
  secondes n'a qu'un debut et une fin, et les marges de 5.4 perdent leur sens.
- **`--sans-diarisation` est le seul fichier hors `outils_recette/` que ce plan touche.** Le
  script diarise toujours, et le modele `spkrec-ecapa` est absent du poste: sans ce drapeau,
  chaque transcription declenche un telechargement pour une diarisation ecartee par
  arbitrage. Six lignes, dans un script hors depot.

### Une scission deliberee dans le lot 4

`detecter_top.py` tourne sur le venv Codex - il a besoin de `numpy` et `soundfile` - et
**ecrit son resultat dans `session.json`**. `fusionner_parcours.py` ne lit que
`session.json`: il est **en bibliotheque standard pure** et tourne sur le Python systeme.

Motif: la seule dependance fragile - un venv de cache Codex qui peut etre efface sans
preavis - reste confinee aux lots 3 et au detecteur. L'etape qu'on relance le plus souvent,
la fusion, n'en depend pas.

---

## 12. Arbitrages explicites

| Choix | Retenu | Rejete | **Cout du choix** |
|---|---|---|---|
| Emplacement | Hors depot, `dev/outils_recette/` | Produit `server/`; extension versionnee dans `clients/`; extension non versionnee | Aucun test, aucune relecture, aucune CI. La justesse ne repose que sur le repere d'horloge |
| Capture audio | ffmpeg hors navigateur | `MediaRecorder` | Deux horloges a reconcilier, resolu en 5.2 |
| Transport du journal | Collecteur local | `localStorage` seul | Un port de plus a declarer et a liberer |
| Injection | Signet | Extension; snippet DevTools; iframe; CDP | Les secondes entre l'affichage et le clic. DevTools rejete parce qu'il **retrecit la fenetre**, donc fausse la largeur qu'on mesure |
| Diarisation | Ecartee | speechbrain deja installe | Une voix tierce sera attribuee a Brice |
| Modele | `large-v3-turbo` par defaut | `small` | A rearbitrer sur V5: le facteur temps-reel decide de l'usage |
| Rattachement | Fenetre asymetrique, cascade, candidats publies | Fenetre symetrique; dernier evenement | Deux marges qui sont des hypotheses, donc parametrees et affichees |

**L'arbitrage central, et il ne tient pas a une preference.** Tout ce module aurait ete plus
solide dans le depot, teste par le banc Node qui existe deja pour
`clients/extension-navigateur`. Il n'y est pas parce que Brice a tranche, et sa raison est
recevable: il vient de passer vingt minutes a faire remonter des defauts de l'outillage au
lieu du produit. **La contrepartie est ecrite en section 13 et ne doit pas etre oubliee au
premier incident.**

---

## 13. Gate GO / NO-GO

**NO-GO tant que ces trois conditions ne sont pas remplies:**

1. **Un coordinateur declare son ownership** et ouvre un `CH-*` rattache a `RM-2026-0114`.
   L'item reste `A_QUALIFIER` jusque-la, comme l'impose la procedure du gouvernail.
2. **Le lot 0 est joue et ses six reponses sont ecrites.** Deux d'entre elles peuvent
   invalider une partie du cadrage: si V2 montre que Windows refuse l'ouverture du micro,
   tout le lot 1 change de forme; si V5 montre un facteur temps-reel prohibitif, le modele
   par defaut change.
3. **Le coordinateur tranche sur la gate complete de `docs/methode_developpement_branches.md`.**
   Ce cadrage couvre huit de ses dix elements. **Deux manquent:** le parcours-evenements
   formel, et surtout les **tests attendus** - ecartes par arbitrage de Brice. Ce document
   ne decide pas a la place du coordinateur s'il ouvre la gate produit complete pour un
   outil qui ne touche aucun code produit.

**Ce qui est deja leve:**

- La question de l'installation: la machinerie existe, mesuree en section 4.
- La question de l'emplacement: arbitree par Brice, et la mesure du `.spec` montre qu'aucun
  autre choix n'etait tenable.
- La question de la diarisation: ecartee, avec sa consequence ecrite.

**La reserve a ne pas perdre.** L'absence de test fait reposer toute la justesse de
l'alignement sur le repere d'horloge de la section 5.2. **Les deux tops ne sont donc pas une
decoration: ils sont la seule epreuve du module, et ils doivent etre joues a chaque session,
pas une fois pour toutes.** Un coordinateur qui les rendrait optionnels pour gagner du temps
retirerait le dernier controle de l'outil.
