# Pilotage indicateurs actionnables

Date de reference: 2026-05-20

Ce cadrage decrit la couche `pilotageops`: elle ne remplace pas `indicatorops`, elle compose ses definitions, observations et seuils en cartes de pilotage utilisables par un conseil syndical novice.

## Intention

Une carte de pilotage doit repondre a trois questions simples:

- Que faut-il regarder maintenant ?
- Sur quelle preuve et quelle periode s'appuie-t-on ?
- Quelle est la prochaine action, et a quel point ou action est-elle rattachee ?

La carte n'est pas un template UI. C'est un objet metier serialisable, pret a etre affiche, exporte ou relie a un registre.

## Domaines V1

Les domaines canoniques sont volontairement courts:

- `consommations`
- `entretien`
- `amortissement/investissements`
- `espaces verts`
- `travaux`
- `gouvernance`
- `demandes`
- `risques`

Des alias pratiques sont acceptes en entree, par exemple `maintenance` vers `entretien`, `fonds travaux` vers `amortissement/investissements`, `AG` vers `gouvernance`, `contentieux` vers `risques`.

## Champs obligatoires

Chaque carte doit contenir:

- domaine
- periode
- source
- preuve
- seuil lisible
- statut
- niveau de confiance
- lecture novice
- prochaine action
- diffusion
- rattachement a un point ou a une action

Une carte sans preuve ou source n'est pas bloquee, mais son statut passe en `a_verifier` via `indicatorops` et la mention manquante reste visible.

## Statuts et seuils

`pilotageops` conserve les statuts de `indicatorops`:

- `OK`
- `attention`
- `alerte`
- `a_verifier`

Le seuil est expose sous forme courte, par exemple:

- `attention >= 10; alerte >= 20`
- `cible 50; attention <= 30; alerte <= 15`
- `seuil non renseigne`

## Diffusion

Les diffusions normalisees sont:

- `conseil_syndical`
- `conseil_syndical_et_syndic`
- `restreint_cs`
- `assemblee_generale`

Par defaut, les risques restent en `restreint_cs`. Une alerte non risquee est diffusable au syndic. Les autres cartes restent en conseil syndical.

## Rattachement

La carte porte `point_ref` et `action_ref`. Au moins l'un des deux doit etre renseigne.

Si aucun rattachement n'est fourni a la composition, `pilotageops` genere un `point_ref` stable de type `POINT-...` pour eviter une carte orpheline. Ce point est une suggestion de rattachement logique, pas une creation persistante dans un registre.

## Usage attendu

Flux minimal:

1. Normaliser les definitions, observations et seuils dans `indicatorops`.
2. Appeler `build_pilotage_card` ou `build_pilotage_cards`.
3. Valider la carte avec `validate_pilotage_card`.
4. Afficher ou exporter l'objet sans recalculer le statut dans la couche UI.

Exemple de sortie logique:

```json
{
  "domain": "consommations",
  "period": "2026-05",
  "source": "FactureOps",
  "proof_ref": "FACT-EAU-2026-05",
  "threshold": "attention >= 10; alerte >= 20",
  "status": "alerte",
  "next_action": "Demander le releve compteur et comparer au contrat.",
  "diffusion": "conseil_syndical_et_syndic",
  "point_ref": "POINT-EAU-2026-05",
  "action_ref": "ACT-RELANCE-RELEVE-EAU"
}
```

## Garde-fous CS novice

- Le vocabulaire reste stable: preuve, source, seuil, statut, prochaine action.
- Une carte ne doit pas dire `conforme` quand la preuve manque.
- Le domaine `risques` evite une diffusion large par defaut.
- Les contextes `vault_id`, `instance_id`, `scope_id` servent au matching et ne doivent pas etre melanges entre coproprietes.
- La couche ne modifie aucun template UI et ne cree pas de registre persistant.
