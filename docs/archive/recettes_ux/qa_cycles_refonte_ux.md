# QA cycles refonte UX

Date de reference: 2026-05-21.

Mission: QA routes reelles lancee sur la base verte UX principale, puis
go/no-go lot peripherique, Memoire et Cycle 5 au fil des livraisons.

Perimetre modifie: ce journal QA uniquement. Aucun code applicatif modifie.

## Point QA courant - 2026-05-21 06:27 +02:00

Etat reel connu transmis au coordinateur: 33 tests UX principaux verts. Les
demandes ne rendent plus de chemins locaux et `base.html` est robuste aux vues
isolees. Le lot peripherique est quasiment vert; seule correction active connue:
`/actions?status=a_demander` quand aucune action n'est selectionnee. Cet etat
supersede les no-go historiques de reprise ci-dessous pour le point courant; les
anciennes notes restent utiles comme trace de ce qui avait ete corrige ou
surveille.

| Flux QA | Etat courant | Decision | Prochaine action |
|---|---|---|---|
| Base regression | 33 tests UX principaux verts | GO base | Conserver la liste comme reference et signaler seulement les regressions P0/P1/P2 |
| Demandes | Chemins locaux nettoyes du rendu | GO cible | Surveiller absence de `raw`, `restricted`, `file://`, chemins Windows, `/Users` ou `/home` |
| Base templates | `base.html` robuste aux vues isolees | GO cible | Garder en regression les routes rendues seules, sans contexte complet |
| Lot peripherique | Quasiment vert sauf `/actions?status=a_demander` selection vide | CORRECTION | Relancer le lot peripherique apres correction et publier GO/NO-GO |
| Routes reelles | QA routes reelles active | EN_QA | Tester par URL/clic/token, pas par intention |
| Cycle 4 Memoire | Front Memoire toujours actif | QA amont | Preparer go/no-go `/chantiers` des que la tranche visible existe |
| Cycle 5 vues manquantes | Back vues manquantes toujours actif | QA amont | Demander contrat, donnees synthetiques et route cible avant acceptation |
| Cycle 8A | Designer a livre `Cycle 8A - Boite de reprise`; novice peripherique relance | QA amont / EN_ENQUETE | Verifier comprehension novice: reprise, action suivante, preuve et diffusion |

## Commandes lancees / pretes

Depuis `server/`:

```powershell
# Lot principal UX vert connu au point courant: 33 tests.
.\.venv\Scripts\python.exe -m unittest tests.test_ui_cockpit -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_registre_actions -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_comptes_guide -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_smoke_routes_expanded -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_novice_language_static -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_requests -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_memoire -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_passation_export_route -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_security_routes -v

# Relance cible apres correction Registre selection vide.
.\.venv\Scripts\python.exe -m unittest tests.test_ui_registre_actions -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_smoke_routes_expanded -v
.\.venv\Scripts\python.exe -m unittest tests.test_ui_security_routes -v

# Lot peripherique a rejouer apres correction.
.\.venv\Scripts\python.exe -m unittest tests.test_ui_requests tests.test_ui_context_banner_routes tests.test_ui_depot_flow tests.test_ui_document_viewer -v
```

## Prochain mouvement QA anti-idle

| Priorite | Declencheur | Action QA | Decision attendue |
|---:|---|---|---|
| 1 | Correction `/actions?status=a_demander` annoncee | Relancer Registre + smoke + securite, verifier etat vide sans erreur et hrefs token-safe | GO/NO-GO lot peripherique |
| 2 | Tranche front Memoire visible | Tester `/chantiers` par route reelle, token, instance vide, preuves, passation, anti-fuite | GO/NO-GO Memoire |
| 3 | Contrat Cycle 5 nomme | Tester route cible vues manquantes avec donnees synthetiques et langage novice | GO/NO-GO Cycle 5 |
| 4 | Role QA libere | Prendre `Cycle 8A - Boite de reprise` cote novice: reprise, action, preuve, diffusion | No-go utilisateur ou GO amont |

## Resultats QA historiques de reprise

| Surface | Resultat | Decision |
|---|---:|---|
| Cockpit `/` | 5 tests OK | GO cible |
| Registre dedie `/actions` | 6 OK, 1 fail apres strictification | GO scenario seed, NO-GO route simple |
| Comptes `/comptes` | 6 OK, 1 skip front Cycle 3 | GO back, NO-GO front/final |
| Smoke routes elargi | 2 erreurs sur `/actions` | NO-GO Registre utilisateur |
| Langage novice statique | 6 tests OK | GO garde-fou langage |
| Memoire `/chantiers` | 3 tests OK | GO amont Cycle 4 |
| Exports passation | 3 tests OK | GO export derive |
| Securite routes | 3 OK, 1 erreur via `/actions` | NO-GO tant que Registre casse |

## Historique regression Registre

P0: arrivee simple sur `/actions` casse avec instance synthetique et aussi avec
token valide.

Symptome vu dans smoke et securite:

```text
jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'action'
server/src/coproscope/web/templates/actions.html, ligne 79
```

Lecture QA: le parcours Registre avec donnees seed et filtres cibles passe, mais
un utilisateur qui ouvre simplement `/actions` peut recevoir une erreur serveur
au lieu d'un etat vide ou d'une fiche par defaut.

Action QA faite: ajout d'un test dedie dans
`server/tests/test_ui_registre_actions.py` pour rendre cette regression visible
dans la suite Registre, pas seulement dans le smoke transversal.

Attente dev avant GO utilisateur:

- `/actions?token=local-secret` retourne 200 sur instance synthetique par defaut;
- l'etat vide ou la selection par defaut expose `Registre decisions - actions -
  preuves`;
- aucun chemin prive, `raw`, `restricted`, `logs`, `file://` ou chemin absolu
  utilisateur n'est rendu;
- les hrefs restent locaux et token-safe.

## Historique Cycle 3 Comptes

La route actuelle conserve le socle guide:

- token requis si configure;
- labels actuels: `P1 a traiter`, `P2 a confirmer`,
  `OK avec preuve rattachee`, `Prochain geste humain`, `Questions syndic`,
  `Preuves et blocages`, `Mode prive local`;
- pas de `P1 Prioritaire` ou `P2 Prioritaire` dans le scenario teste;
- anti-fuite public verifie par les tests actuels.

Etat Cycle 3: le back cible est assez livre pour passer les tests stricts
`model.ux.comptes` avec donnees seedees; le front Canva `/comptes` n'est pas
encore livre.

Labels Canva / cible manquants dans `/comptes`:

- `Exporter le rapport`;
- `Factures rapprochees`;
- `Depenses par categorie`;
- `Afficher aussi les categories sans alerte`;
- `Questions au syndic`;
- `Detail`;
- `Rapport AG`.

Decision: GO back Cycle 3, NO-GO front/final. Les assertions modele Cycle 3
sont strictes et passent; le dernier blocage est la presence des labels et zones
Canva dans la route rendue.

## Preparation QA Cycle 4 Memoire

La base UX principale est verte dans l'etat courant connu avec 33 tests. La QA
bascule donc sur le lot peripherique, Memoire, puis Cycle 5, sans attendre de
nouvelle reprise Comptes.

Tests existants verts:

- `tests.test_ui_memoire`: `/chantiers` rend la surface Memoire/passation, y
  compris instance vide;
- `tests.test_ui_passation_export_route`: exports JSON/TXT derives, token requis
  et absence de brut prive.

Checklist QA Memoire a activer des que front/back livrent la cible:

- `/chantiers` affiche `Memoire de copropriete` comme titre principal et label
  actif, pas `Chantiers` en premier niveau visible;
- recherche: `Rechercher un evenement, un contrat, un document...`;
- filtres/segments: `5 ans`, `10 ans`, `Tout`;
- timeline centrale avec date, titre, categorie, statut, href local token-safe;
- panneau `Passation CS` avec progression, sujets ouverts et action de detail;
- panneau `A transmettre` avec documents essentiels et restrictions de
  diffusion;
- detail evenement: documents/preuves, action liee, restrictions, note de
  passation;
- export passation: annonce `export derive`, inclusions, omissions et blocages;
- instance vide: `Aucun evenement dans la memoire`, `Passation a preparer`,
  `Aucun document transmissible`;
- anti-fuite: aucun `raw`, `restricted`, `logs`, `file://`, chemin Windows ou
  `/Users`/`/home`;
- token: tous les liens internes et exports conservent le token local quand il
  est requis;
- langage novice: pas de `vault`, `hash`, `ACL`, `RBAC`, `Workstreams` en
  premier niveau.

Decision Cycle 4: GO amont QA, NO-GO final tant que la timeline, le detail
evenement et le pack passation complet ne sont pas livres.
