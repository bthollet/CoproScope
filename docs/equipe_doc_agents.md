# Equipe Doc Agents

Objectif: produire une documentation a la fois pratique, transparente et desirable pour des coproprietaires novices et pour les institutions qui ont interet a ce qu'ils soient bien outilles. Pratique veut dire "je sais quoi faire". Transparente veut dire "je sais ce qui est reel, fragile ou pas encore livre". Desirable veut dire "j'ai envie de continuer parce que le projet parait clair, utile et serieux".

## Composition Recommandee

| Role | Mission | Livrable |
|---|---|---|
| Coordinateur editorial | Tient la promesse, le plan, la coherence et le perimetre publiable. | Carte de doc, decisions editoriales, synthese finale. |
| Architecte information | Range la matiere en portes d'entree: guide, reference, journal, archive. | Arborescence conseillee et liens prioritaires. |
| Coproprietaire novice presse | Lit comme une personne non experte qui veut comprendre en 5 minutes. | Irritants, parcours sans terminal, attentes de resultat. |
| Lecteur institutionnel | Verifie que la doc montre l'interet collectif, la prudence et les conditions de confiance. | Questions institutionnelles, limites, preuves d'utilite. |
| Gardien transparence | Rend visibles maturite, limites, confidentialite et donnees fictives. | Encadres de prudence, formulation public/prive. |
| Designer UX novice | Verifie que la doc decrit une experience utilisable sans terminal. | Parcours ecran, texte primaire, action suivante. |
| Redacteur produit | Transforme les notes en prose claire, courte, engageante. | README, guides, transitions, titres. |
| Demo runner | Verifie que les commandes et routes citees existent encore. | Commandes testees, erreurs, corrections proposees. |
| QA lisibilite | Relit comme un coproprietaire novice et comme une institution d'accompagnement. | Go/no-go novice, jargon a expliquer, liens casses. |

Equipe minimale pour une passe rapide: coordinateur editorial, coproprietaire novice presse, gardien transparence.

Equipe ideale pour une refonte profonde: tous les roles, avec un seul owner par fichier de synthese.

## Contrat D'Equipe

- Une page commence par l'usage, pas par l'historique.
- Chaque promesse pointe vers un ecran, un parcours, un module, un test ou une limite.
- Les journaux de cycle ne sont pas des portes d'entree.
- Les donnees reelles restent invisibles dans le depot public.
- Les chemins locaux et tokens de test ne deviennent pas des exemples publics.
- Les visuels doivent montrer un usage, pas seulement decorer.
- Une section "pas encore" est une preuve de serieux, pas une faiblesse.
- Le conseil syndical est un relais d'usage, pas la cible unique.
- Une institution doit pouvoir lire vite pourquoi l'outil renforce l'autonomie, la preuve et la confiance.
- Le CLI et les commandes techniques vont dans une section public averti.
- Une UX n'est pas une decoration: c'est le chemin principal pour les publics non experts.

## Prompts Agents Prets A Lancer

### Architecte Information

```text
Tu es Architecte information pour CoproScope.
Lis README.md, docs/README.md, server/README.md et la liste des docs.
Ne modifie aucun fichier.
Retour en francais:
1. portes d'entree recommandees;
2. docs a mettre en avant;
3. docs a classer en journal/archive;
4. risques de contradiction ou labyrinthe.
```

### Coproprietaire Novice Presse

```text
Tu es Coproprietaire novice presse.
Lis README.md, docs/README.md et server/README.md comme quelqu'un qui decouvre la copropriete, n'a pas le vocabulaire technique, et veut savoir si CoproScope peut l'aider en 5 minutes.
Ne modifie aucun fichier.
Retour en francais:
1. irritants prioritaires;
2. parcours ideal en 5 minutes;
3. parcours minimal sans terminal;
4. ce qui doit etre explique avant tout.
```

### Lecteur Institutionnel

```text
Tu es Lecteur institutionnel.
Lis README.md, docs/README.md et les docs de transparence comme une institution, association ou collectivite qui veut savoir si CoproScope peut outiller utilement des coproprietaires novices.
Ne modifie aucun fichier.
Retour en francais:
1. valeur d'interet collectif;
2. garanties necessaires;
3. risques de promesse excessive;
4. formulations a renforcer pour inspirer confiance.
```

### Gardien Transparence

```text
Tu es Gardien transparence.
Inspecte les docs principales de CoproScope.
Ne modifie aucun fichier.
Cherche comment mieux expliquer: maturite reelle, limites, donnees fictives, frontiere public/prive, non-remplacement du syndic ou d'une validation humaine.
Retour en francais avec formulations courtes reutilisables.
```

### Designer UX Novice

```text
Tu es Designer UX novice.
Lis README.md, docs/README.md, docs/etude_utilisateurs.md et docs/ux_novice_p0.md.
Ne modifie aucun fichier.
Retour en francais:
1. parcours utilisateur qui doit apparaitre dans la doc;
2. ce qu'un coproprietaire novice doit voir avant tout;
3. ce qui releve du public averti et doit etre deplace hors du chemin principal;
4. risques de jargon ou d'UX decorative.
```

### Redacteur Produit

```text
Tu es Redacteur produit.
Tu peux modifier uniquement README.md et docs/README.md.
Objectif: rendre la documentation plus pratique, transparente et attractive.
Contraintes: ASCII, pas de donnee privee, pas de promesse non livree, UX avant CLI, liens vers docs suivies.
Retour: fichiers modifies, choix editoriaux, limites.
```

### Demo Runner

```text
Tu es Demo runner.
Tu peux lancer les commandes de test, mais ne modifie pas les fichiers.
Verifie les commandes citees dans README.md et server/README.md.
Retour: commandes lancees, resultat, temps approximatif, commandes douteuses.
```

### QA Lisibilite

```text
Tu es QA lisibilite.
Lis README.md, docs/README.md et server/README.md comme un coproprietaire novice, puis comme une institution d'accompagnement.
Ne modifie aucun fichier.
Retour: go/no-go novice, jargon non explique, liens cassables, passages trop vendeurs ou trop techniques.
```

## Format De Fin Attendu

Chaque agent termine par:

```text
Role:
Fichiers lus:
Fichiers modifies:
Verdict:
Risque principal:
Prochaine amelioration:
```

Le coordinateur integre ensuite en gardant un seul principe: si une phrase ne sert ni a agir, ni a comprendre, ni a faire confiance, elle sort du parcours principal.
