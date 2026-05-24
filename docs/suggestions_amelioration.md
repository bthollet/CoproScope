# Suggestions d'amelioration

Date de reference: 2026-05-20

Ce module pose un modele leger pour transformer les signaux CoproScope en
suggestions d'amelioration utiles au conseil syndical. Il suit la roadmap
issue de l'enquete utilisateur et la strategie Obsidian-like: chaque suggestion
doit rester locale, sourciee, reliee a une preuve et orientee vers une prochaine
action humaine.

## Intention

Une suggestion d'amelioration n'est pas une decision automatique. Elle sert a
dire:

- pourquoi un sujet merite attention;
- quelle preuve ou piece permet de le verifier;
- quelle source CoproScope a produit le signal;
- quelle prochaine action humaine est raisonnable;
- quel impact, effort, niveau de confiance et public sont envisages.

Le module `SuggestionOps` ne remplace ni le conseil syndical, ni le syndic, ni
une revue juridique. Il prepare une fiche claire pour que les humains puissent
qualifier, refuser, completer ou transformer la suggestion.

## Objets

`SuggestionTrigger`

- Signal source detecte par un module, un registre ou une revue manuelle.
- Champs clefs: `source`, `proof`, `why`, `kind`, `object_ref`, `confidence`,
  `public`.
- Il doit etre sourcie et prouvable avant de produire une suggestion.

`ImprovementSuggestion`

- Fiche candidate affichee dans le cockpit, l'atelier piece, le registre ou la
  memoire.
- Champs clefs: `why`, `proof`, `source`, `next_action`, `impact`, `effort`,
  `confidence`, `public`.
- Statut initial: `a_revoir`, meme si la confiance est haute.

`SuggestionReview`

- Revue humaine explicite.
- Decisions possibles: `pending`, `accepted`, `rejected`,
  `needs_more_proof`.
- Une decision autre que `pending` exige un relecteur et un motif.

`SuggestionOutcome`

- Resultat cree apres revue humaine acceptee.
- Types cibles: `action`, `demande`, `point`, `indicateur`, `export`.
- L'outcome conserve toujours le pourquoi, la preuve, la source, la prochaine
  action et le public de diffusion.

## Regles produit

- Une suggestion sans `source` ou sans `proof` est invalide.
- Une suggestion conserve toujours un `why` et une `next_action`.
- Une confiance haute ne transforme jamais automatiquement la suggestion.
- Une transformation exige une `SuggestionReview` acceptee par un humain.
- Les exports restent soumis a revue de diffusion et biffage si necessaire.
- Les champs sont simples et serialisables pour rester compatibles avec CSV,
  Markdown, SQLite reconstruit ou evenements de vault futurs.
- Aucune dependance lourde n'est introduite.

## Transformations

Une suggestion acceptee peut devenir:

- `action`: tache suivie dans le registre action/preuve;
- `demande`: question ou demande au syndic, avec preuve attendue;
- `point`: point de suivi dans l'atelier piece ou la memoire;
- `indicateur`: carte de pilotage periodisee a completer;
- `export`: brouillon diffusable, soumis a controle de confidentialite.

Ces transformations restent des objets derives. La source de verite future doit
etre l'evenement signe du vault ou le registre metier qui cree vraiment l'objet.

## Position dans la roadmap

Le module aide a relier les priorites produit:

- cockpit conseil syndical: afficher les sujets qui demandent attention;
- atelier piece: transformer une piece en point, action ou preuve;
- registre: relier decision, action, demande et preuve;
- controle comptes guide: produire des questions, pas des jugements definitifs;
- memoire de copropriete: conserver les sujets ouverts et les preuves utiles;
- Obsidian-like: garder des objets locaux, lisibles, exportables et
  reconstruisibles.

## Limites actuelles

- Le module ne persiste pas encore dans le vault.
- Il ne signe pas les revues ni les outcomes.
- Il ne branche pas encore l'UI cockpit ou atelier piece.
- Les niveaux d'impact et d'effort restent textuels pour eviter un faux score.
- Les politiques de diffusion fines seront raccordees a PrivacyOps/BiffageOps.
