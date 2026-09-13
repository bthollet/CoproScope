# Surveillance de l'extranet Coprodirecte — synthese technique du lot

Etat du lot : **49 propositions ecrites, 49 refutees, 0 retenue.** Ce document ne livre pas une conception validee. Il livre ce que les mesures autorisent, ce qu'elles interdisent, et la liste des mesures qui manquent. C'est un resultat utile : le lot a elimine des chemins qui auraient fabrique de faux constats contre le syndic.

---

## 1. La decision technique centrale

**Aucune cle d'identite n'est qualifiee aujourd'hui : le nom de fichier servi par `content-disposition` est la seule prise stable trouvee, mais il a ete mesure sur un document, deux jetons, une session, quelques secondes — donc l'outil doit pouvoir dire "je ne sais pas" sur sa propre cle, et le premier lot livre une campagne de mesure et un etat de couverture, pas un moteur de verdicts.**

Pourquoi les mesures l'imposent :

- L'URL est exclue. Le jeton de 108 a 151 caracteres change integralement a chaque chargement de la meme page (mesure trois fois). Indexer dessus produit 100 % de faux "nouveaux" a chaque passage.
- Il ne reste rien d'autre dans la page. Les liens `class="pj pdf"` ne portent aucun attribut `data-*` ni identifiant. Les 8 categories sont des `<div class="labelDoc">` sans `href`. Aucune API JSON interne n'a ete reperee.
- Le nom de `content-disposition` est donc la seule prise. Ce qui a ete mesure de lui : 40 caracteres, extension `.pdf`, contient des chiffres, identique entre deux jetons differents du meme document, obtenu par `HEAD` donc sans telecharger le corps.
- Ce qui n'a **jamais** ete mesure de lui : son unicite (deux documents distincts portent-ils deux noms distincts ?), sa survie entre deux passages separes de jours, son comportement quand le syndic remplace une piece, son comportement entre deux comptes.

Les deux proprietes non mesurees sont exactement celles dont dependent les verdicts AJOUT et RETRAIT. Un nom non unique fait disparaitre un retrait reel en silence. Un nom regenere fabrique un lot complet de faux retraits — soit le constat le plus accusatoire que l'outil sache produire, a partir d'un artefact de mesure.

Le meme raisonnement vaut pour l'empreinte du contenu. La byte-identite mesuree (SHA-256 identique sur 51318 octets entre deux jetons) porte sur **une session, un compte, un document, quelques secondes**. Elle ne dit rien de la stabilite entre deux passages ni entre deux comptes — et la consolidation entre coproprietaires repose entierement sur cette seconde propriete.

---

## 2. L'architecture retenue

### Comment on identifie

Deux cles, jamais confondues, chacune avec son etat de qualification ecrit dans le journal :

| Cle | Obtention | Cout | Sert a | Etat par defaut |
|---|---|---|---|---|
| `nom_serveur` (`content-disposition`) | HEAD | tres faible | presence : apparition / disparition | `IDENTITE_NON_QUALIFIEE` |
| `empreinte_octets_recus` (SHA-256 du corps) | GET complet | corps entier | contenu : le fichier servi a-t-il change | `CONTENU_NON_VERIFIE` |

`nom_serveur` est une cle **strictement locale**. Elle ne quitte jamais la machine : la contrainte RM interdit le nom de fichier dans une empreinte echangeable, et chez un autre editeur ce nom peut porter un patronyme.

L'empreinte n'est pas une identite, c'est un **attribut de version**. Le coffre a deja tranche dans ce sens : `documents.document_id` est l'identite, `source_sha256` et `blob_sha256` sont des attributs, et `document_versions` porte l'empreinte par version. Promouvoir l'empreinte en identite rendrait inexprimable "meme document, deux etats", qui est l'objet meme de l'outil.

`blob_sha256` est mecaniquement disqualifie : le chiffrement tire un nonce aleatoire, donc les memes octets produisent deux `blob_sha256` distincts.

### Comment on detecte

Deux canaux separes, jamais fondus en un verdict scalaire.

- **Presence** : HEAD sur chaque lien reellement rendu, comparaison des `nom_serveur` entre deux passages. Cout tres faible. N'autorise aucune conclusion sur le contenu.
- **Contenu** : GET complet, empreinte des octets recus. Il n'existe aucun palier intermediaire : `etag`, `last-modified` et `content-length` sont absents, et `accept-ranges` est annonce mais **non honore** (une demande `Range: bytes=0-2047` rend 200 et 51318 octets, soit le fichier entier). Aucun raccourci d'empreinte partielle n'est disponible.

Un `nom_serveur` inchange ne dit **jamais** "contenu inchange". L'etat correspondant est `CONTENU_NON_VERIFIE`, pas "identique".

### Ou tourne le code

- **Content script** : seule main vers l'extranet. Il detient les jetons frais rendus par la page et le contexte de session. Il fait les HEAD et les GET.
- **Service worker** : seule main vers CoproScope local (`127.0.0.1`). Aucun middleware CORS n'existe cote serveur, donc un POST depuis une page serait bloque ; le worker, lui, passe. Le jeton local voyage en en-tete `x-coproscope-token`, jamais en cookie (le cookie du serveur local est pose en `samesite=lax` et n'isole pas par port).
- **Pas de document offscreen** : `crypto.subtle` existe dans le service worker et le content script tourne en contexte securise.
- **Pas de native messaging, pas de File System Access.** Motifs en section 5.

### Actuation des panneaux

**Le premier passage sur un editeur est supervise par l'humain.** L'utilisateur ouvre lui-meme les 8 panneaux, le plugin observe les mutations du DOM et enregistre ce qu'il a vu. Aucun clic synthetique en aveugle.

Motif : l'effet d'un clic sur un `div.labelDoc` n'a jamais ete observe. Six propositions raisonnaient dessus. Un element sans `href` peut, chez un autre editeur, valider, accepter ou accuser reception — et la ligne rouge tomberait sans bruit. Le garde-fou ne peut pas etre "toute methode differente de GET est une ecriture" : un GET peut porter un effet de bord, et `sendBeacon`, la navigation et les insertions dynamiques passent ce filtre.

Cout assume : une rubrique non ouverte par l'humain reste `NON_EXPLORE`, et aucun retrait n'y est affirmable. C'est une contrainte de l'editeur, pas un defaut de l'outil.

### Comment ca arrive dans CoproScope

Par le **recorder du journal d'evenements SQLite**, jamais par une table posee a cote. `_reset_schema` fait `DROP TABLE` sur toutes les projections a chaque reconstruction, complete comme incrementale : une table hors journal disparait au rebuild suivant et la perte est differee, donc invisible.

Ne pas passer non plus par `remplacer_pour_documents` : sa semantique est un remplacement par document (`DELETE ... WHERE doc_id IN (...) AND origine <> 'CORRIGE_HUMAIN'`), destructrice de l'historique — or un journal d'observations n'a de valeur que si la ligne du 15 survit jusqu'au 22.

Jointure avec le coffre : quand les octets sont recuperes, on interroge `documents.source_sha256`. Une correspondance est une assertion ("ces octets sont ceux de ce document du coffre"). **Une non-correspondance est INDETERMINE, jamais "piece inconnue"** : la meme piece entree par une autre porte (scan, piece jointe, re-export) porte d'autres octets.

---

## 3. Le schema du journal

### Familles d'evenements

| Evenement | Porte | Ecrit meme quand rien n'a ete vu |
|---|---|---|
| `extranet.passage.ouvert` / `.clos` | perimetre declare, horodatages | oui |
| `extranet.rubrique.observee` | rubrique, etat, exhaustivite, preuve, nb vus, nb annonces | **oui** |
| `extranet.piece.observee` | rang dans l'index, `nom_serveur`, multiplicite, statut HEAD | non |
| `extranet.piece.contenu` | empreinte, taille comptee sur les octets recus, `nom_serveur` et rubrique du meme passage | non |
| `extranet.identite.qualifiee` | injectivite mesuree, stabilite mesuree, source de la cle | oui |

`extranet.piece.contenu` reporte la rubrique et le `nom_serveur` observes **au meme passage**, pour que la relation se reconstruise depuis le seul journal apres `_reset_schema`.

La taille se compte sur les octets recus. `content-length` est absent : elle ne se lit pas dans un en-tete.

Aucun champ d'auteur du changement. `author_key_id` et `device_id`, presents dans les tables existantes, designent **l'observateur local**, jamais qui a agi sur l'extranet. Aucune vue ne les affiche a cote d'un constat de disparition.

Une correction humaine s'ecrit sur son **propre champ**, avec son `origine`, jamais sur le champ machine — sinon le passage automatique suivant l'ecrase dans la vue derivee.

### Projections

```
extranet_passages   (passage_id, perimetre_id, ouvert_le, clos_le, etat, event_id)
extranet_couverture (passage_id, perimetre_id, rubrique, observee_le, etat,
                     exhaustivite, preuve, nb_vus, nb_annonces, event_id)
extranet_pieces     (passage_id, perimetre_id, rubrique, rang, nom_serveur,
                     multiplicite_nom, statut_head, event_id)
extranet_contenus   (passage_id, perimetre_id, rubrique, nom_serveur,
                     empreinte_octets, taille_octets, lectures_concordantes, event_id)
extranet_identite   (passage_id, perimetre_id, source_cle, injectivite,
                     stabilite, event_id)
```

`etat` ∈ `VU | NON_EXPLORE | ECHEC_OUVERTURE`.
`exhaustivite` ∈ `ATTESTEE | NON_ATTESTEE`. Defaut : `NON_ATTESTEE`. `ATTESTEE` exige une preuve positive nommee (total annonce egal au nombre vu, ou fin de liste constatee), jamais l'absence de bouton de pagination.

### La requete "qu'est-ce qui a change entre A et B"

```sql
WITH couv AS (
  SELECT rubrique,
    MAX(CASE WHEN passage_id=:A AND etat='VU' THEN 1 ELSE 0 END)              AS vue_a,
    MAX(CASE WHEN passage_id=:A AND exhaustivite='ATTESTEE' THEN 1 ELSE 0 END) AS pleine_a,
    MAX(CASE WHEN passage_id=:B AND etat='VU' THEN 1 ELSE 0 END)              AS vue_b,
    MAX(CASE WHEN passage_id=:B AND exhaustivite='ATTESTEE' THEN 1 ELSE 0 END) AS pleine_b
  FROM extranet_couverture
  WHERE perimetre_id=:P AND passage_id IN (:A,:B)
  GROUP BY rubrique
),
cle AS (
  SELECT MIN(CASE WHEN injectivite='UNIQUE' AND stabilite='CONFIRMEE'
                  THEN 1 ELSE 0 END) AS qualifiee
  FROM extranet_identite
  WHERE perimetre_id=:P AND passage_id IN (:A,:B)
),
pa AS (SELECT rubrique, nom_serveur, multiplicite_nom
       FROM extranet_pieces WHERE perimetre_id=:P AND passage_id=:A),
pb AS (SELECT rubrique, nom_serveur, multiplicite_nom
       FROM extranet_pieces WHERE perimetre_id=:P AND passage_id=:B),
ca AS (SELECT rubrique, nom_serveur, empreinte_octets
       FROM extranet_contenus WHERE perimetre_id=:P AND passage_id=:A),
cb AS (SELECT rubrique, nom_serveur, empreinte_octets
       FROM extranet_contenus WHERE perimetre_id=:P AND passage_id=:B)

SELECT
  COALESCE(pa.rubrique, pb.rubrique)       AS rubrique,
  COALESCE(pa.nom_serveur, pb.nom_serveur) AS cle_locale,

  CASE
    WHEN (SELECT qualifiee FROM cle) = 0            THEN 'INDETERMINE_IDENTITE'
    WHEN COALESCE(pa.multiplicite_nom,1) > 1
      OR COALESCE(pb.multiplicite_nom,1) > 1        THEN 'INDETERMINE_CLE_AMBIGUE'
    WHEN couv.vue_a = 0 OR couv.vue_b = 0           THEN 'NON_EXPLORE'
    WHEN pb.nom_serveur IS NULL AND couv.pleine_b=1 THEN 'PLUS_LISTE_AU_PASSAGE_B'
    WHEN pb.nom_serveur IS NULL                     THEN 'INDETERMINE_COUVERTURE'
    WHEN pa.nom_serveur IS NULL AND couv.pleine_a=1 THEN 'APPARU_AU_PASSAGE_B'
    WHEN pa.nom_serveur IS NULL                     THEN 'PREMIERE_OBSERVATION'
    ELSE 'PRESENT_AUX_DEUX_DATES'
  END AS verdict_presence,

  CASE
    WHEN ca.empreinte_octets IS NULL
      OR cb.empreinte_octets IS NULL                          THEN 'CONTENU_NON_VERIFIE'
    WHEN ca.empreinte_octets = cb.empreinte_octets            THEN 'OCTETS_IDENTIQUES'
    ELSE 'OCTETS_DIFFERENTS'
  END AS verdict_contenu

FROM pa
FULL OUTER JOIN pb USING (rubrique, nom_serveur)
LEFT JOIN couv ON couv.rubrique = COALESCE(pa.rubrique, pb.rubrique)
LEFT JOIN ca   ON ca.rubrique=pa.rubrique AND ca.nom_serveur=pa.nom_serveur
LEFT JOIN cb   ON cb.rubrique=pb.rubrique AND cb.nom_serveur=pb.nom_serveur;
```

Chaque garde est imposee par une mesure :

- `qualifiee = 0` → la mesure du 2026-09-04 ne porte que sur un document et une session.
- `multiplicite_nom > 1` → l'unicite du nom entre documents n'a jamais ete mesuree ; l'index se compte en multi-ensemble, pas en ensemble.
- `vue_a = 0 OR vue_b = 0` → une rubrique non cliquee est mecaniquement invisible.
- `pleine_b = 0` → sans preuve positive de fin d'enumeration, une disparition peut etre une troncature.
- Deux colonnes de verdict → un deplacement ne doit jamais masquer un changement d'octets.

Le verdict de presence s'ecrit `PLUS_LISTE_AU_PASSAGE_B`, jamais `RETIRE`. "Retire" est un verbe transitif : il suppose un agent, et l'extranet n'en expose aucun.

**Garde-fou de masse, hors requete** : si, dans une rubrique a cardinalite comparable, la quasi-totalite des cles disparait pendant qu'un nombre comparable de cles inconnues apparait, le diagnostic economique est "la cle a tourne", pas "le syndic a tout remplace". La rubrique entiere passe `INDETERMINE_IDENTITE` et aucun constat individuel n'est emis.

---

## 4. La politique de surveillance par defaut

**Par defaut : HEAD seul, sur les rubriques que l'humain a ouvertes pendant sa visite normale.**

- Aucun clic automatique de panneau.
- Aucun telechargement systematique de corps.
- Corps recuperes uniquement pour un petit ensemble de pieces designe par l'humain, plus toute piece dont la cle a bouge.
- Sonde de stabilite du corps **sur alarme seulement** : quand une empreinte differe, relire immediatement la meme piece une seconde fois. Deux lectures identiques entre elles et differentes du stock → changement reel. Deux lectures differentes entre elles → `CONTENU_INSTABLE_A_LA_SOURCE`, verdict suspendu pour cette piece.

### Ce que ca sacrifie, nommement

- **Couverture.** Tout ce que l'humain n'ouvre pas reste `NON_EXPLORE`. Aucun retrait n'y est affirmable, jamais.
- **Modification.** Toute piece dont les octets ne sont pas repris est `CONTENU_NON_VERIFIE`. Le journal ne dira jamais "inchange" pour elle.
- **Latence.** Le premier passage n'affirme ni ajout ni retrait : il n'a pas de reference anterieure. Il produit la couverture et la base de comparaison.

### Les couts, chiffres ou declares inconnus

| Poste | Cout |
|---|---|
| Un passage de presence | 1 chargement d'index + 1 activation par rubrique + 1 HEAD par lien |
| Un HEAD | corps a verifier — `accept-ranges` ment deja, la nature sans corps du HEAD n'est pas mesuree |
| Un verdict de contenu sur une piece | le corps entier ; aucun raccourci partiel |
| Volume d'un passage complet en contenu | **inconnu avant telechargement** : `content-length` est absent. Le seul document mesure pese 51318 octets ; un PV scanne avec annexes est d'un autre ordre |
| Sonde de stabilite | 1 corps supplementaire, uniquement sur alarme |

### Ce que le conseiller syndical lit

Personne ne l'avait ecrit. Regles retenues :

- Chaque constat nomme son observateur et refuse son agent. Aucune tournure passive sans complement d'agent : "a ete retire" est interdit, le lecteur francais y fournit le syndic.
- Chaque constat porte trois blocs : ce que j'ai observe, ce que ce constat ne dit pas, ce qu'on peut faire.
- L'en-tete porte la couverture et son denominateur, ou l'aveu qu'il est inconnu : *"3 rubriques comparables, c'est-a-dire ouvertes aux deux dates. Ce qui suit ne parle que de ces 3 rubriques."*
- Avant tout courrier au syndic, une verification est prescrite : rouvrir la rubrique et chercher un titre proche. Une piece republiee sous un autre nom se presente comme une disparition.
- Le code machine (`PLUS_LISTE_AU_PASSAGE_B`) n'atteint jamais l'ecran. Une phrase l'atteint.
- Echelle d'opposabilite affichee : ce que la machine locale atteste (date, provenance) est de force faible ; ce que l'emetteur a produit (octets, metadonnees internes du PDF **si elles existent**, verifiees et pas supposees) est de force superieure.

---

## 5. Ce qui a ete elimine, et pourquoi

### Identite

| Ecarte | Motif |
|---|---|
| Indexer sur l'URL | Jeton renouvele integralement a chaque chargement, mesure trois fois. 100 % de faux nouveaux. |
| Faire du nom de fichier une identite acquise | Mesure sur un document, deux jetons, une session. Ni l'unicite ni la survie inter-passage ne sont mesurees. Nom reutilise → un retrait disparait en silence ; nom regenere → lot complet de faux retraits. |
| Faire de l'empreinte du contenu l'identite | Le coffre a tranche dans l'autre sens. Une empreinte-identite donne deux identites a un document modifie, donc rend inexprimable "meme document, deux etats". |
| `blob_sha256` comme identite | Nonce aleatoire au chiffrement : memes octets, deux valeurs. Mecaniquement disqualifie. |
| Lire un horodatage ou un SHA-1 dans les chiffres du nom | L'arithmetique n'est pas mesuree — les 40 caracteres incluent-ils `.pdf` ? L'alphabet n'est pas mesure. Et sous l'hypothese vraie, le nom change avec le contenu, donc l'identite disparait au moment ou on en a besoin. |
| Deriver un identifiant du libelle affiche | Champs enumerables : un tiers teste une hypothese en un hachage. Le depot sale deja ses alias de personnes exactement pour cette raison. |

### Detection

| Ecarte | Motif |
|---|---|
| `etag`, `last-modified`, `content-length` | Absents des en-tetes mesures. |
| Empreinte partielle par `Range` | `accept-ranges` est annonce et non honore : 200 et 51318 octets pour une demande de 2048. L'en-tete ment. |
| "Nom inchange donc contenu inchange" | Sans temoin de fraicheur, un nom stable ne dit rien du contenu. |
| Deux telechargements a quelques secondes comme preuve de stabilite | Mesure la variance **par requete**. Un filigrane date a la journee ou a la session passe le test, puis fabrique une vague de fausses modifications au passage suivant. |
| Un temoin unique generalise a toute la passe | Un editeur peut servir statiques ses archives et regenerer ses etats de compte. Un temoin tire des archives donne le feu vert a la population instable. |
| Canaris "pieces qui ne peuvent pas changer" | Choisies sur une modalite, et anti-correlees a la panne qu'elles doivent voir. |
| Un verdict scalaire unique | Un deplacement de rubrique masquait un changement d'octets. |

### Couverture

| Ecarte | Motif |
|---|---|
| Deduire un retrait d'une absence de ligne | Une rubrique non cliquee est mecaniquement invisible. |
| Couverture au grain de la page ou du passage | Les 8 rubriques partagent une seule URL. Deux passages qui ouvrent des panneaux differents seraient reputes comparables. |
| `EXPLORE` par defaut, degrade seulement si un signe de pagination est detecte | Codage de modalites. Un editeur a defilement paresseux ou a filtre par exercice ne declenche aucun signe et se declare complet. Defaut correct : `NON_ATTESTEE`. |
| Verdict d'ajout sans exhaustivite a la date **anterieure** | Un ajout est une conjonction : vu en B **et** absent en A. La negation porte sur A. |

### Actuation et ligne rouge

| Ecarte | Motif |
|---|---|
| Clic synthetique en aveugle sur les panneaux | L'effet d'un clic `labelDoc` n'a jamais ete mesure. Un element sans `href` peut valider ou accuser reception chez un autre editeur. |
| Garde-fou "methode differente de GET/HEAD = ecriture" | La methode HTTP est une modalite, pas l'axe. Un GET peut porter un effet ; `sendBeacon`, la navigation, l'insertion d'image passent le filtre. |
| Se declarer indistinguable d'un clic humain | Objectif nuisible : rend un effet non desire non detricotable, et `event.isTrusted` expose de toute facon le clic synthetique. |

### Pont et stockage

| Ecarte | Motif |
|---|---|
| Native messaging | Identifiant d'extension lie au chemin hors magasin, deux schemas de registre incompatibles, second binaire dans la chaine PyInstaller. |
| File System Access | `showDirectoryPicker` indisponible en service worker, handle qui retombe en `prompt` au redemarrage, absent de Firefox. |
| Pont fichier seul (dossier surveille) | Ne transporte pas une observation negative : `NON_EXPLORE` et un echec de telechargement ne sont pas des fichiers. Et `conflictAction: uniquify` anti-deduplique par construction. |
| Table `extranet_*` posee a cote de la base de reconstruction | `_reset_schema` fait `DROP` a chaque reconstruction, complete et incrementale. Perte differee, donc invisible. |
| Ecrire par `remplacer_pour_documents` | Remplacement par document : detruit l'observation anterieure, celle-la meme qui prouve le changement. |
| Jeton d'appairage persistant reutilisant `access_token` | Ouvre toutes les routes, pas la route d'ingestion ; et le middleware repose le jeton en cookie `samesite=lax` sur `127.0.0.1`, tous ports confondus. |

### Perimetre et privacy

| Ecarte | Motif |
|---|---|
| Deduire le perimetre (quel immeuble) du recouvrement de noms | Depend de l'ordre de decouverte. Une seule piece generique de cabinet suffit a rattacher un second immeuble au premier, et l'union glissante scelle l'erreur au passage suivant. |
| Fabriquer un `compte_id` localement | Identifie une installation, pas un compte. Deux machines pour un compte : compte double. Deux comptes sur une machine : comptes fusionnes. |
| Echanger un SHA-256 nu entre coproprietaires | Oracle de confirmation : qui detient une piece candidate teste la possession. Le detenteur de tout le corpus est le syndic. |
| Echanger le nom de fichier | Interdit par la contrainte RM ; et chez un autre editeur il peut porter un patronyme. |
| Journaliser le voisinage textuel d'un lien, l'URL complete, l'hote, un chemin local | Donnees de tiers, ou jeton d'acces encore vivant. |
| Etendre l'echange a `/espace-client` | College B, personnel. Une empreinte de piece a faible entropie (gabarit + nom + solde) se force par dictionnaire. |

### Seuils

Tous les seuils numeriques proposes ont ete ecartes : "au moins 2 jetons partages", "30 % de documents changes", "10 temoins concordants", "au moins 1 nom en commun". Meme faute que le cas d'ecole maison — `au moins 2 signatures = PV`, refute en une mesure par un second cabinet. Un seuil cale sur une population observee n'est pas un axe.

---

## 6. Les mesures live encore a faire

Toutes en lecture seule (HEAD/GET), a coller dans la console de l'onglet extranet, session ouverte. Aucune n'emet quoi que ce soit vers le syndic.

**Avertissement de lecture** : la mesure M8 affiche du texte de page qui peut contenir des noms de tiers. Elle se lit a l'ecran et ne se recopie nulle part.

### M1 — Les liens sont-ils deja dans le DOM avant le clic ?

```js
document.querySelectorAll('a.pj.pdf').length
```
Relever, puis ouvrir les 8 panneaux a la main et relancer.

- **Egaux** : les liens sont deja servis, masques. Le mode passif couvre tout, le clic automatique devient sans objet.
- **Le premier est plus petit** : le clic est indispensable, la couverture partielle est structurelle, et le compte de panneaux ouverts doit etre journalise par rubrique.
- **Variable selon la rubrique** : c'est l'axe reel, et la couverture doit etre enregistree par rubrique et non par page.

### M2 — Que fait un clic sur un panneau ?

```js
window.__t = [];
const _f = window.fetch;
window.fetch = function(...a){ __t.push(['fetch', String(a[0]).slice(0,80), (a[1]&&a[1].method)||'GET']); return _f.apply(this,a); };
const _o = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(m,u,...r){ __t.push(['xhr', String(u).slice(0,80), m]); return _o.call(this,m,u,...r); };
if (navigator.sendBeacon) navigator.sendBeacon = function(u){ __t.push(['beacon', String(u).slice(0,80), 'POST']); return true; };
addEventListener('beforeunload', () => console.warn('NAVIGATION DECLENCHEE'));
// cliquer UN panneau a la main, puis :
__t
```

- **Tableau vide, DOM change** : le panneau est purement local. Le clic automatique devient defendable pour cet editeur, et seulement pour lui.
- **Un GET meme origine** : chargement paresseux. Acceptable en lecture, a journaliser.
- **Un POST, un beacon, une navigation** : le clic automatique est interdit ici. Mode supervise definitif.

### M3 — Le nom de fichier est-il discriminant ?

```js
const liens = [...document.querySelectorAll('a.pj.pdf')].map(a=>a.href);
const noms = [];
for (const u of liens) {
  const r = await fetch(u, {method:'HEAD'});
  noms.push(r.headers.get('content-disposition'));
}
console.log('liens', liens.length, '| noms distincts', new Set(noms).size);
```

- **Egaux** : injectivite corroboree sur cet index. Pas prouvee, corroboree.
- **Noms distincts < liens** : la cle collisionne. AJOUT et RETRAIT sont desactives pour cette rubrique, verdict `INDETERMINE`.
- **`content-disposition` absent** : aucune prise. La rubrique ne produit ni ajout ni retrait, et on ne se rabat jamais sur l'URL.

### M4 — Longueur exacte et alphabet du nom

```js
const rad = noms.map(n => (n||'').match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i)?.[1] || '')
                .map(f => f.replace(/\.[^.]+$/, ''));
console.log('longueurs radical', [...new Set(rad.map(r=>r.length))]);
console.log('hex pur ?', rad.every(r=>/^[0-9a-f]+$/.test(r)));
console.log('alphabet', [...new Set(rad.join(''))].sort().join(''));
```

- **36 caracteres** : ce n'est pas un SHA-1. L'hypothese "le nom est une empreinte du contenu" meurt ici, gratuitement.
- **40 caracteres et hexadecimal pur** : hypothese ouverte, a trancher par M5.
- **Alphabet mixte ou tirets** : cle de stockage. Le nom ne dit rien du contenu, ce qui est le cas favorable pour l'identite.

### M5 — Le nom est-il derive du contenu ?

```js
async function sha1(buf){ const h = await crypto.subtle.digest('SHA-1', buf);
  return [...new Uint8Array(h)].map(x=>x.toString(16).padStart(2,'0')).join(''); }
const u = liens[0];
const b = await (await fetch(u)).arrayBuffer();
console.log(await sha1(b), '|', rad[0]);
```

- **Egaux** : le nom suit le contenu. Consequence lourde : un remplacement fait perdre au document sa seule identite persistante. La modification devient `INDETERMINE`, pas gratuite.
- **Differents** : le nom est independant du contenu. C'est le cas ou la surveillance de presence a un sens.

### M6 — Le HEAD renvoie-t-il vraiment un corps vide ?

```js
const r = await fetch(liens[0], {method:'HEAD'});
console.log('octets recus sur HEAD :', (await r.arrayBuffer()).byteLength);
```

- **0** : le budget "un HEAD par lien" est valide.
- **Non nul** : la surveillance de presence coute autant qu'un telechargement complet. Toute la fiche de cout est a refaire, et le passage quotidien n'est plus tenable.

### M7 — Les octets sont-ils stables, sur plusieurs documents ?

```js
async function sha(b){ const h=await crypto.subtle.digest('SHA-256', b);
  return [...new Uint8Array(h)].map(x=>x.toString(16).padStart(2,'0')).join(''); }
for (const u of liens.slice(0,5)) {
  const a1 = await (await fetch(u)).arrayBuffer();
  const a2 = await (await fetch(u)).arrayBuffer();
  console.log(u.slice(-14), a1.byteLength, (await sha(a1)) === (await sha(a2)));
}
```

- **Tous `true`** : la mesure du 2026-09-04 se generalise a l'interieur d'une session. Ne dit toujours rien de l'inter-session.
- **Un `false`** : cette piece est regeneree. Le verdict de contenu est desactive pour elle, pas pour la passe.
- **Tous `false`** : l'editeur fabrique a la demande. La detection de modification par empreinte est impossible ici, et il faut le dire au lieu de crier au remplacement.

### M8 — L'index affiche-t-il une date declaree ?

```js
[...document.querySelectorAll('a.pj.pdf')].slice(0,10).forEach(a => {
  const l = (a.closest('tr,li,div') || a.parentElement);
  console.log(l.innerText.replace(/\s+/g,' ').trim().slice(0,160));
});
```
A lire a l'ecran, sans rien recopier.

- **Une date visible** : source d'anteriorite bien meilleure que toute deduction, mais son referent est inconnu (depot ? seance ? echeance ?) et doit etre etabli avant tout calcul de delai.
- **Aucune date** : le journal n'a pas de passe. Une piece vue au premier passage est "en ligne au plus tard le <date du passage>", et rien de plus.

### M9 — Existe-t-il une preuve d'exhaustivite ?

```js
const z = document.body.innerText;
console.log(z.match(/\b\d+\s*(document|piece|pi.ce|r.sultat)/gi));
console.log('controles de pagination :',
  document.querySelectorAll('[class*=pagin],[class*=suivant],[aria-label*=age]').length);
```

- **Un total annonce** : `exhaustivite = ATTESTEE` devient calculable, et le RETRAIT devient affirmable.
- **Rien** : aucune preuve de cloture disponible chez cet editeur. Consequence a assumer : la detection de retrait reste `INDETERMINE` tant qu'aucun signal n'est trouve. Ce silence vaut mieux qu'un "complet" presume.

### M10 — Duree de validite d'un jeton

```js
window.__j = { u: liens[0], t0: Date.now() };
// plus tard, SANS recharger la page :
const r = await fetch(__j.u, {method:'HEAD'});
console.log(Math.round((Date.now()-__j.t0)/60000)+' min |', r.status, '|', r.headers.get('content-type'));
```
A rejouer a 1, 5, 15, 60 minutes, puis a 24 h.

- **200 + `application/pdf` a 60 min** : un passage long peut reutiliser ses jetons.
- **Non-200 ou `text/html` a 5 min** : il faut recharger l'index juste avant chaque rafale de HEAD, ce qui ajoute un chargement par rubrique. A budgeter.

### M11 — Un jeton perime, ca ressemble a quoi ?

Rejouer M10 apres deconnexion, en notant `status`, `content-type` et la presence de `content-disposition`.

- **Non-200** : `ECHEC_ACCES` est detectable proprement.
- **200 avec du HTML** : il faut un predicat d'acceptation — `content-disposition` present **et** type non-HTML — sans quoi une page de session expiree serait empreintee comme si c'etait le document.

### M12 — L'editeur trace-t-il la consultation ?

Lecture humaine : chercher dans l'interface une mention de type "consulte le", un historique d'acces ou un accuse de lecture.

- **Oui** : un HEAD automatique laisse une trace cote syndic sur des pieces jamais ouvertes par l'utilisateur. L'arbitrage "lire est invisible" tombe et doit etre repris.
- **Non trouve** : reste `INDETERMINE`. On ne conclut pas a l'absence depuis une absence de mention.

---

## 7. Ce qui reste indetermine tant qu'une decision humaine n'est pas prise

1. **Ouvrir une seconde session coproprietaire.** La stabilite des octets entre deux comptes n'est pas mesurable depuis un seul compte, et c'est la propriete dont depend toute consolidation entre voisins. Si les octets sont personnalises, une divergence d'empreinte entre deux coproprietaires ne signifie rien. La mesure exige l'accord d'un tiers : c'est une decision de Brice, pas une decision technique.

2. **Conserver ou non les octets telecharges.** Garder les corps donne une piece opposable ; garder les corps signifie stocker durablement, sur le poste, des documents portant l'etat civil et les soldes d'autres coproprietaires. Il faut trancher : perimetre, duree, purge, exclusion de toute synchronisation cloud. En attendant, on ne conserve rien au-dela du calcul de l'empreinte.

3. **Surveiller ou non `/espace-client`.** L'espace personnel n'a pas d'interet de consolidation (personne d'autre ne detient les memes pieces) et concentre le risque d'oracle. Par defaut : hors perimetre.

4. **Autoriser ou non le clic automatique des panneaux.** Depend de M2. Meme si M2 est propre pour Coprodirecte, l'autorisation reste par editeur et ne se generalise pas.

5. **Comment le perimetre est declare.** Rien dans les pages mesurees n'identifie l'immeuble ni le compte. La seule voie sure est une declaration humaine au moment ou le plugin s'attache a une session, enregistree comme telle. Deduire le perimetre des donnees fusionne deux immeubles en silence.

6. **Ce que le conseiller syndical a le droit d'ecrire au syndic, et dans quels termes.** Le tableau de phrases existe maintenant en principe, pas en texte valide. Il doit etre relu par quelqu'un qui sait ce qu'un conseil syndical peut opposer.

7. **Le numero de gouvernail** - *tranche le 2026-09-07.* Le soupcon etait fonde, et plus large que prevu: `RM-2026-0085`, `RM-2026-0086` et `RM-2026-0087` etaient portes en meme temps par ce lot et par des lots voisins deja presents sur `main` (venv partage, seize constats d'audit, nom de copropriete fabrique). `RM-2026-0085` a meme connu un troisieme sens, dans un lot de systeme de design anterieur. Les trois items de ce lot sont renumerotes en `RM-2026-0091`, `RM-2026-0092` et `RM-2026-0093`; `RM-2026-0090` a ete saute, car deja employe par un lot reel jamais inscrit au gouvernail. Vingt-sept renvois ont ete repris fichier par fichier, en laissant intact le fichier du lot de design qui ne nous appartient pas.

8. **La consolidation entre coproprietaires elle-meme.** Elle n'est pas concevable tant que le point 1 n'est pas mesure et que le format d'echange n'est pas tranche : une empreinte nue est un oracle, une empreinte clee suppose un secret partage hors bande, avec les questions de rotation et de revocation qui vont avec. Rien de tout cela n'est decide.