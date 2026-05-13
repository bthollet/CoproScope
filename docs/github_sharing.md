# Politique de partage GitHub

Depot produit public: [bthollet/CoproScope](https://github.com/bthollet/CoproScope)

## But

Faciliter la remontee des ameliorations generiques issues du travail sur des instances privees, sans fuite de donnees, de secrets, de chemins sensibles ou de documents reels.

## Ce qui peut etre partage

- le code produit sous `server/` ;
- la documentation publique sous `docs/` ;
- les schemas, configurations, prompts et templates ;
- les tests ;
- les exemples synthetiques sous `examples/synthetic_copro/` ;
- les correctifs, ameliorations CLI/MCP et heuristiques vraiment generiques.

## Ce qui ne doit jamais etre partage

- `coproscope-instances/` ;
- les fichiers reels de copropriete ;
- les exports OCR/texte issus de fichiers prives ;
- les manifestes qui exposent des chemins prives ;
- `.env.local`, tokens, cles API et chemins de secrets ;
- les donnees nominatives, bancaires, contentieuses ou d'impayes.

## Workflow de remontee

1. implementer ou valider l'amelioration sur une instance privee ;
2. retirer toute dependance a une instance particuliere ;
3. deplacer la partie reusable vers `coproscope/server/`, `coproscope/docs/` ou `coproscope/examples/synthetic_copro/` ;
4. ajouter ou mettre a jour les tests ;
5. verifier le manifeste de partage et la frontiere public/prive ;
6. ouvrir une issue ou une PR sur le depot public.

## Commandes locales utiles

- `coprocs share-audit --repo-root .. --config src/coproscope/configs/github_sharing.default.yml`
- `coprocs share-export --repo-root .. --config src/coproscope/configs/github_sharing.default.yml --output-dir ../public-export --clean`

## Questions de revue obligatoires avant publication

- Le changement est-il vraiment generique ?
- Contient-il un chemin reel, un nom de fichier prive, une personne, un lot, une banque ou un detail contentieux ?
- Peut-on demontrer le comportement avec l'exemple synthetique uniquement ?
- Les attentes d'environnement sont-elles documentees via `.env.example` plutot que par des secrets ?

## Forme de PR recommande

- un changement generique a la fois ;
- etapes de validation explicites ;
- mention claire du travail de generalisation/redaction effectue ;
- rappel de la frontiere prive/public.
