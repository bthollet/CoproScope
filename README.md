# CoproScope

> La copropriete lisible: preuves, actions, memoire, partage prudent.

CoproScope est un projet open source local-first pour aider des
coproprietaires, conseils syndicaux, syndics benevoles, associations,
collectivites et partenaires a comprendre un dossier de copropriete sans devoir
devenir experts.

Le produit ne remplace ni un syndic, ni une comptabilite officielle, ni une
validation juridique. Il aide a relier les documents, demandes, decisions,
depenses, preuves, actions et restitutions partageables.

![Strategie cible Drive CoproScope](./docs/assets/showcase/drive-strategie-cible.svg)

## Choisir Son Entree

| Vous etes | Lire | Ce que vous y trouvez |
|---|---|---|
| Coproprietaire, conseil syndical, futur utilisateur | [Decouvrir CoproScope](./docs/public/README.md) | Promesse, usages, limites, vocabulaire simple. |
| Sponsor, collectivite, association | [Sponsors et partenaires](./docs/public/sponsors-et-partenaires.md) | Interet collectif, prevention, autonomie, soutenabilite. |
| Lecteur qui veut voir les parcours | [Parcours demonstratifs](./docs/public/parcours-demonstratifs.md) | Comptes, preuves, demandes, Drive cible, points a verifier. |
| Lecteur inquiet sur les donnees | [Strategie Drive et confidentialite](./docs/public/confiance-confidentialite.md) | Coffre local, Drive chiffre, controle avant partage. |
| Lecteur qui veut l'etat reel | [Maturite et limites](./docs/public/maturite-et-limites.md) | Ce qui existe, ce qui reste a stabiliser, ce qui n'est pas promis. |
| Developpeur ou contributeur | [Documentation developpeurs](./docs/developpeurs/README.md) | Installation, tests, architecture, publication prudente. |

## Le Probleme

Dans beaucoup de coproprietes, l'information existe deja, mais elle est:

- dispersee entre documents, mails, Drive, extranet, tableurs et memoires
  personnelles;
- difficile a lire pour des coproprietaires non experts;
- fragile quand un benevole fatigue ou passe la main;
- sensible a partager sans revue ni validation;
- rarement reliee a une action concrete.

CoproScope cherche a rendre visible la chaine:

```text
document -> preuve -> point a verifier -> action -> decision -> memoire -> partage prudent
```

## Ce Que CoproScope Montre

### Drive Comme Transport Chiffre

Drive n'est pas le cerveau du produit. Dans la cible, CoproScope garde le
travail clair en local, controle ce qui peut etre prepare, chiffre le paquet,
puis utilise Drive comme transport vers les personnes autorisees.

![Garde-fous avant partage Drive](./docs/assets/showcase/drive-garde-fous-partage.svg)

Lire la page detaillee:
[Strategie Drive et confidentialite](./docs/public/confiance-confidentialite.md)

### Comptes Lisibles Sans Se Pretendre Comptable

![Matrice de controle des comptes](./docs/assets/showcase/controle-comptes-matrice.png)

CoproScope aide a voir les sources disponibles, les sources absentes et les
questions a poser. Une ligne n'est pas declaree vraie sans preuve et validation
humaine.

### Preuve Avec Contexte

![Preuve document PDF](./docs/assets/showcase/preuve-document-pdf.png)

Une piece doit dire ce qu'elle prouve, ce qu'elle ne prouve pas, et pourquoi
elle est rattachee a une action, une depense ou un point.

## Ce Que Le Projet Apporte

| Besoin | Reponse CoproScope |
|---|---|
| Comprendre vite | Une lecture par preuves, points a verifier et prochaines actions. |
| Controler sans surpromettre | Des questions guidees, des reserves visibles, une validation humaine. |
| Demander et relancer | Une piece manquante devient une demande suivie, pas une remarque perdue. |
| Partager prudemment | Les sorties passent par revue, biffage si besoin et controle avant partage. |
| Transmettre | La memoire ne repose plus uniquement sur une personne ou un dossier eparpille. |

## Maturite Reelle

| Bloc | Etat |
|---|---|
| Interface locale | V0 utile: actions, comptes, demandes, documents, preuves et passation. |
| Donnees de demonstration | Instance fictive publique sous `examples/synthetic_copro`. |
| DocOps | Inventaire, hash, extraction, classement et completude. |
| PrivacyOps / BiffageOps | Socle de revue, biffage et diffusion prudente. |
| ComptaScope | Rapprochements candidats et questions guidees. |
| Demandes / actions / preuves | En consolidation dans les vues produit. |
| Coffre et Drive chiffre | Cap cible clair, parcours complet encore a stabiliser. |
| Installation noob | Cible documentee, pas encore experience finale. |

## Ce Que CoproScope N'Est Pas

- pas un syndic;
- pas une comptabilite officielle;
- pas un avis juridique personnalise;
- pas un SaaS multi-tenant pret a vendre;
- pas un coffre cloud de documents bruts;
- pas une IA qui decide seule.

## Aller Plus Loin

| Sujet | Lien |
|---|---|
| Index complet de la documentation | [docs/README.md](./docs/README.md) |
| Parcours publics | [docs/public](./docs/public/README.md) |
| Parcours demonstratifs | [docs/public/parcours-demonstratifs.md](./docs/public/parcours-demonstratifs.md) |
| Sponsors et partenaires | [docs/public/sponsors-et-partenaires.md](./docs/public/sponsors-et-partenaires.md) |
| Drive et confidentialite | [docs/public/confiance-confidentialite.md](./docs/public/confiance-confidentialite.md) |
| Developpeurs | [docs/developpeurs/README.md](./docs/developpeurs/README.md) |

## Structure Du Depot

- [server/](./server): code produit, CLI, interface locale, configs, templates
  et tests.
- [docs/](./docs): documentation publique, technique, architecture, UX et
  archives.
- [examples/synthetic_copro/](./examples/synthetic_copro): instance fictive
  pour tests publics et demonstrations.

Pour installer et lancer techniquement CoproScope, lire
[server/README.md](./server/README.md).
