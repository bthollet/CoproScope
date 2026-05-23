# AG, contentieux et passation

Ce modele couvre la preparation d'assemblee generale, les dossiers de contentieux et la passation entre contributeurs. Il est volontairement leger: il structure les objets, les preuves, les restrictions de diffusion et les prochaines actions sans produire d'avis juridique automatique.

## Objets

- `DossierAG`: dossier de preparation d'AG, avec questions, pieces de convocation, statut, prochaine action et echeance.
- `QuestionAG`: question ou resolution a preparer, rattachee aux sources, preuves, decisions et actions.
- `PieceConvocation`: piece attendue ou verifiee pour la convocation.
- `ContentieuxCase`: dossier de suivi contentieux factuel, sans qualification juridique automatique.
- `LegalRiskNote`: note non juridique de vigilance operationnelle, limitee aux constats, signaux de risque et pieces a verifier.
- `EvidenceRef`: reference de preuve ou source, avec origine, hash optionnel, restriction, diffusion et statut.
- `EvidenceBundle`: paquet de preuves consolide pour AG, contentieux ou passation.
- `PassationPack`: paquet de transmission listant dossiers AG, contentieux, notes, preuves, points ouverts et actions.

## Champs communs

Chaque objet porte les informations necessaires pour devenir plus tard un evenement signe:

- identifiant stable;
- `source_refs` ou `source_ref`;
- `proof_refs` ou `evidence_id`;
- `restriction`;
- `diffusion`;
- `status`;
- `next_action`;
- `due_on`;
- `decision_refs`;
- `action_refs`;
- `event_refs`.

Le helper `event_payload(record)` produit un payload deterministe avec `schema_version`, `event_type`, `aggregate_id`, references sources/preuves, rattachements decisions/actions et donnees utiles. Il n'ajoute pas d'horodatage afin de laisser une couche de signature future gerer temps, auteur, hash et signature.

## Garde-fous

- Pas d'avis juridique automatique: `LegalRiskNote` reste une note non juridique de constats et points de vigilance. Les formulations de type avis juridique, chances de gagner ou consigne d'assigner bloquent le payload evenementiel.
- Pas de donnees privees: les champs texte sont controles contre des marqueurs simples comme email, telephone francais et NIR. Les donnees nominatives ou personnelles doivent rester dans les pieces protegees, pas dans le modele.
- Diffusion explicite: `cs`, `coproprietaires` ou `public_after_redaction`.
- Restriction explicite: `internal`, `restricted` ou `confidential`.
- Les paquets consolides heritent de la restriction la plus forte et de la diffusion la plus limitee des elements inclus.

## Usage cible

Le modele sert a preparer:

- un ordre du jour et les pieces de convocation;
- une liste d'actions issues de decisions AG;
- un dossier factuel de contentieux;
- une passation propre entre membres du conseil syndical ou contributeurs;
- des evenements signables dans une evolution ulterieure.

Il ne remplace pas une validation juridique, ne deplace pas de donnees privees hors des pieces protegees et ne modifie aucune interface globale.
