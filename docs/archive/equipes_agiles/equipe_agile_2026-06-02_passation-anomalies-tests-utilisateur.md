# Tests utilisateur - passation anomalies

Date: 2026-06-02
Conversation: CONV-2026-2090
Chantier: CH-20260602-231800-RM-2026-0016-passation-anomalies-tests
Route testee: /exports/passation

## Scenario metier

Un membre du conseil syndical prepare un dossier derive pour transmettre une
situation d'anomalies, d'actions ouvertes et de preuves manquantes. Il veut
comprendre ce qui sera repris, ce qui reste bloque, et pourquoi ce dossier ne
remplace pas les pieces originales.

## Retours des roles

Organisateur de test: le scenario est proche des suites d'audit et de controle
comptable, mais ne doit pas relancer la reconstruction ni ouvrir une nouvelle
analyse de donnees reelles.

Utilisateur expert-auditeur novice CoproScope: l'ecran initial etait sain sur
la confidentialite, mais trop technique. Les mots `export`, `JSON`, `TXT`,
`source_of_truth` et `telechargement` donnaient l'impression d'une sortie
officielle ou informatique, pas d'un dossier a relire.

Designer: les captures doivent rester accrochees a l'UI CoproScope existante.
Pas de refonte visuelle inventee. La correction cible la hierarchie de lecture:
titre metier, bandeau de prudence, versions a preparer, et bloc clair sur ce
qui ne sort pas.

Dev front: correction limitee aux libelles visibles du template passation et de
la fiche de blocage. Pas de changement de structure ni de nouvelle route.

Dev back: le contrat de securite reste inchange: jeton requis, liens avec
perimetre conserve, exports derives JSON/TXT maintenus, pas de chemin local ni
brut servi.

## Correction livree

- Le titre visible devient `Dossier a transmettre`.
- Les actions disent `Preparer version texte` et `Preparer version structuree`.
- Le bandeau explique `Dossier derive, non preuve officielle`.
- Le texte visible retire `source_of_truth` et `telechargement`.
- Le bloc `Elements exclus ou bloques` devient `Ce qui ne sort pas`.
- Les libelles de blocage parlent de preparation verrouillee, pas de
telechargement verrouille.

## Preuves

Artefacts:

- `docs/assets/passation-anomalies-tests-20260602/passation-anomalies-livraison.html`
- `docs/assets/passation-anomalies-tests-20260602/passation-anomalies-livraison-standalone.html`
- `docs/assets/passation-anomalies-tests-20260602/passation-anomalies-livraison-desktop.png`
- `docs/assets/passation-anomalies-tests-20260602/passation-anomalies-livraison-mobile.png`

Tests:

- `tests.test_ui_passation_export_route` : 20 OK.

Limites:

- Pas de serveur durable ouvert.
- Pas de donnee Beauvallon privee.
- Pas de nouvelle feature de performance `public_passation_v1`.
- La page reste un dossier derive; tout export officiel ou partage externe
  reste hors lot.
