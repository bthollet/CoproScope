# CoproScope

> Transformer un dossier de copropriete opaque en preuves, actions et memoire
> transmissible.

CoproScope est un projet open source local-first pour aider des
coproprietaires, conseils syndicaux, syndics benevoles et acteurs
d'accompagnement a comprendre ce qui se passe dans une copropriete sans devenir
experts.

Le produit ne remplace ni un syndic, ni une comptabilite officielle, ni une
validation juridique. Il aide a relier les documents, demandes, decisions,
depenses, preuves, actions et restitutions partageables.

![Strategie cible Drive CoproScope](./docs/assets/showcase/drive-strategie-cible.svg)

## Pourquoi

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

## Pour Qui

| Public | Ce que CoproScope doit lui apporter |
|---|---|
| Coproprietaire novice | Comprendre les priorites sans apprendre tout le droit de la copropriete. |
| Conseil syndical | Suivre preuves, demandes, comptes, decisions et passation. |
| Syndic benevole | Tenir un mandat avec obligations, traces, messages et prudence. |
| Association ou collectivite | Accompagner des habitants avec une methode reproductible. |
| Sponsor ou partenaire | Soutenir un outil d'autonomie, de preuve et de confiance. |
| Developpeur | Contribuer a un noyau local-first, teste et documente. |

## Ce Que CoproScope Aide A Faire

### Gerer Drive Comme Un Transport Chiffre

Drive n'est pas le cerveau du produit. Dans la cible, CoproScope garde le
travail clair en local, controle ce qui peut etre prepare, chiffre le paquet,
puis utilise Drive comme transport vers les personnes autorisees.

![Garde-fous avant partage Drive](./docs/assets/showcase/drive-garde-fous-partage.svg)

L'interface cible doit dire simplement:

- ce qui reste dans le coffre local;
- ce qui va partir dans Drive;
- pourquoi l'envoi est autorise;
- ce qui bloque le partage en cas de doute.

### Controler Les Comptes Sans Se Pretendre Comptable

![Matrice de controle des comptes](./docs/assets/showcase/controle-comptes-matrice.png)

CoproScope aide a voir les sources disponibles, les sources absentes et les
questions a poser. Une ligne n'est pas declaree vraie sans preuve et validation
humaine.

### Ouvrir Une Preuve Avec Son Contexte

![Preuve document PDF](./docs/assets/showcase/preuve-document-pdf.png)

Une piece doit dire ce qu'elle prouve, ce qu'elle ne prouve pas, et pourquoi
elle est rattachee a une action, une depense ou un point.

### Demander, Relancer, Transmettre

Une absence de piece devient une demande suivie. Une decision devient une
action. Une action garde sa preuve attendue. La passation ne repose plus sur la
memoire d'une seule personne.

## Lire Selon Votre Profil

| Vous voulez | Commencer ici |
|---|---|
| Relire la vitrine en Markdown dans Codex | [Vitrine Markdown](./docs/public/vitrine.md) |
| Comprendre CoproScope sans technique | [Decouvrir CoproScope](./docs/public/README.md) |
| Voir les parcours en images | [Parcours demonstratifs](./docs/public/parcours-demonstratifs.md) |
| Evaluer l'interet pour une institution ou un sponsor | [Sponsors et partenaires](./docs/public/sponsors-et-partenaires.md) |
| Comprendre Drive, partage et confidentialite | [Strategie Drive et confidentialite](./docs/public/confiance-confidentialite.md) |
| Voir ce qui existe vraiment | [Maturite et limites](./docs/public/maturite-et-limites.md) |
| Installer, tester ou contribuer | [Documentation developpeurs](./docs/developpeurs/README.md) |

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

## Structure Du Depot

- [server/](./server): code produit, CLI, interface locale, configs, templates
  et tests.
- [docs/](./docs): documentation publique, technique, architecture, UX et
  archives.
- [examples/synthetic_copro/](./examples/synthetic_copro): instance fictive
  pour tests publics et demonstrations.

Pour installer et lancer techniquement CoproScope, lire
[server/README.md](./server/README.md).
