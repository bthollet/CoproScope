# Menage des instances locales - proposition, 2026-09-08

- Rattachement: regle de Brice du 2026-09-08 sur le coffre et les instances
  jetables, gravee dans `CLAUDE.md`.
- Statut: **proposition. Rien n'est supprime.** La suppression de donnees est
  irreversible et ces dossiers sont prives; le choix appartient a Brice.
- Mesure: 23 instances, environ **11 Go**.

---

## Ce que la regle dit

> « Tu peux copier une instance test si tu as besoin de pas refaire
> l'integration. Mais une fois que la branche ou que le chantier en cours est
> termine, on supprime. [...] Il faut desambiguiser, et du coup les appeler
> `test`, et quand une instance s'appelle `test`, elle peut etre supprimee sans
> perte de donnee personnelle. »

Le nom porte donc une **garantie**, pas une convention: `test_` ou `dev_` veut
dire *tout ce qu'il y a la-dedans existe ailleurs*.

---

## Le critere employe ici, et sa limite

Une instance a ete classee selon **deux mesures distinctes**, parce qu'elles ne
disent pas la meme chose:

- **citee par du CODE** (`server/src`, `server/tests`, `tools`): la supprimer
  casse quelque chose qui tourne;
- **citee par un DOCUMENT** (`docs/`): la citation est une **trace d'un travail
  passe**. Supprimer l'instance ne casse rien - le document raconte ce qui a ete
  fait, il ne le rejoue pas.

**Confondre les deux ferait garder 11 Go pour rien.** C'est la distinction qui
porte toute cette proposition, et c'est aussi elle qui peut la faire echouer: si
un document decrit une procedure que quelqu'un doit pouvoir **rejouer**, alors sa
citation vaut celle du code. Aucun des documents concernes ne semble etre dans ce
cas, mais je ne les ai pas tous relus ligne a ligne.

---

## A GARDER - references de verite

| Instance | Code | Docs | Pourquoi |
|---|---:|---:|---|
| `tests_ux` | 1 | 8 | **L'etalon etabli a la main avant tout traitement outil** (`RM-2026-0050`). C'est la seule reference de verite du depot; elle ne se regenere pas, elle se reconstruit a la main. |
| `erables_pseudo_test` | 2 | 9 | Le **second cabinet**. Sans lui, l'epreuve inter-cabinets exigee par la doctrine des axes est impossible, et trois lots s'en sont servis aujourd'hui. |

Ces deux-la portent deja des noms qui disent ce qu'elles sont. **Ne pas les
renommer `test_`**: elles ne sont pas supprimables sans perte, et le prefixe
promettrait le contraire.

---

## A CREER - l'instance mere

`tilleul_pseudo_mere` *(nomme `tilleul_source_dev` a la construction, renomme le 2026-09-08)* *(le prefixe est un pseudonyme)* - reconstruite depuis le
coffre, **jamais mutee par un lot**: on en copie, on n'y travaille pas.

Elle n'existe pas encore. Aujourd'hui chaque lot repart d'une instance
historique differente, ce qui est exactement ce que la regle de Brice supprime.

---

## A SUPPRIMER - lots clos, aucune citation de code

| Instance | Taille | Docs | Lot d'origine |
|---|---:|---:|---|
| `tilleul_pseudo_reconstruite_20260904` | 1,5 Go | 5 | reconstruction du 04/09, close |
| `tilleul_pseudo_20260906` | 1,6 Go | 0 | non citee du tout |
| `tilleul_pseudo_exploration_20260907` | 1,6 Go | 0 | exploration du 07/09, close |
| `tilleul_pseudo_vide_20260907` | 1,6 Go | 0 | epreuve instance vide du 07/09, close |
| `tilleul_pseudo_reconstruction_sim_20260523` | 2,9 Go | 2 | simulation de mai, **declaree non fiable par la doctrine** |
| `lot_resolutions_20260908` | 1,1 Go | 0 | lot cloture ce jour |
| `lot_factures_20260908` | 329 Mo | 0 | lot cloture ce jour |
| `phase0_verite_20260905` | 159 Mo | 0 | lot clos |
| `tilleul_pseudo_2exercices_20260904` | 159 Mo | 2 | lot clos |
| `corpus_caviarde_lot_20260904` | 59 Mo | 0 | lot clos |
| `chaine_decision` | 172 Mo | 3 | lot clos |
| `tests_ux_lot_20260907` | 33 Mo | 1 | **copie** de l'etalon; l'original est garde |
| `parcours_novice_20260907` | 18 Mo | 1 | lot clos |
| `design_interactions_20260907` | 5,4 Mo | 2 | lot clos |
| `factures_iter_20260903`, `factures_iter2_20260903` | 5,5 Mo | 0 | lots clos |
| `sequence_epreuve_20260907`, `branchement_pages_20260907` | 0,6 Mo | 0 | lots clos |
| `cc_it_010_viewer_demo`, `ui_docintake_smoke_20260523` | 0,3 Mo | 0 | smokes anciens |
| `verif_constats_20260908_*` | - | 2 | lot de verification cloture ce jour |

**Environ 10,5 Go.**

> **CORRECTION du 2026-09-08 au soir, apportee par le lot `RM-2026-0144`.**
> Cette ligne disait: *aucune n'est citee par du code qui tourne*. **C'est faux,
> et un grep d'une ligne le refute.** `lot_factures_20260908` est cite par
> **quatre** fichiers de `server/tests`, `tests_ux_lot_20260907` par un
> cinquieme - par chemin ABSOLU, ecrit en dur.
>
> **Ce que l'erreur a coute:** la suppression a rendu **douze preuves
> silencieuses**, les tests ignores passant de 2 a 18 sans qu'aucun `OK` ne
> change. Une suite qui se tait n'echoue pas: elle mesure moins, et le dit
> seulement a qui compte les sauts.
>
> **Et l'erreur est du meme genre que celles que ce document poursuit:** j'ai
> verifie qu'aucune instance n'etait citee dans le *produit*, et j'ai ecrit
> *aucun code qui tourne* - en oubliant que les tests sont du code qui tourne.
> Une affirmation dont le perimetre reel est plus etroit que sa formulation.
>
> Suites ouvertes: `RM-2026-0150` (une garde qui prend le dossier pour temoin
> au lieu de la piece) et la proposition de Brice - **parametrer l'instance sur
> laquelle les tests se deroulent**, plutot qu'un chemin absolu en dur.

**Deux meritent un mot avant d'etre supprimees.**
`tilleul_pseudo_reconstruction_sim_20260523` est celle que la doctrine cite
nommement comme **non fiable comme etalon**: la garder entretient le risque
qu'un lot la reprenne pour une reference. `tests_ux_lot_20260907` est une copie
de l'etalon faite pour ne pas muter l'original - son existence prouve que la
regle fonctionnait deja avant d'etre ecrite.

---

## Cas a part

`demo_fictive_tilleuls` (123 Ko). **Son nom contient `fictive` et un pseudonyme
qui, ailleurs dans le depot, designe des donnees reelles.** C'est precisement le
quiproquo du 2026-09-08, ou le nom d'emprunt a fait passer des donnees reelles
pour une demonstration. **A verifier avant toute decision**: si son contenu est
reellement fictif, la renommer pour lever l'ambiguite; s'il ne l'est pas, le nom
ment et c'est plus grave qu'un probleme de menage.

---

## Ce que cette proposition ne garantit pas

- **Je n'ai pas ouvert les instances.** Le classement repose sur les citations et
  sur le nom du lot, pas sur ce que chaque dossier contient. Une piece unique
  posee a la main dans un lot et nulle part ailleurs serait perdue.
- **La distinction code/document peut se tromper** dans le sens decrit plus haut.
- **Aucune verification que le coffre contient bien ce que ces instances
  portent.** Elle tourne au moment ou ce document est ecrit, et **c'est elle qui
  doit precéder la suppression** - pas l'inverse.

**Recommandation:** attendre le resultat de la verification du coffre avant de
supprimer quoi que ce soit. Si le coffre contient tout, la suppression est sans
risque par construction; sinon, elle deviendrait une perte reelle.
