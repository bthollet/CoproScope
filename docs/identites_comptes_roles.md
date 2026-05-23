# Identites, comptes et roles

Date de reference: 2026-05-20

Ce document fixe le vocabulaire et le modele V1 du lot priorite haute
`comptes utilisateurs / identites`. Il complete la roadmap produit fini sans
brancher encore l'UI, la synchronisation de vault ou la cryptographie reelle.

## Objectif V1

Un utilisateur novice doit comprendre rapidement:

- qui je suis sur ce poste;
- qui je suis dans ce coffre de copro;
- ce que je peux voir;
- ce que je peux faire;
- qui peut recuperer les cles collectives si un membre du CS disparait.

Le modele separe volontairement quatre notions souvent confondues:

- `UserAccount`: la personne connue par l'application locale;
- `LocalProfile`: le profil de cette personne sur ce poste;
- `VaultMember`: son identite dans un coffre donne;
- `DeviceIdentity`: l'appareil qui signe des evenements pour ce membre.

Un compte local n'est pas une preuve de droit dans un coffre. Le coffre decide
les membres, les appareils, les roles, les acces et les revocations par des
evenements signes.

## Strategie retenue

La V1 est `local-first` et sans serveur central obligatoire.

- Le compte cloud est hors perimetre V1.
- Un compte local peut ouvrir plusieurs coffres, mais les droits sont propres a
  chaque coffre.
- Un membre du coffre peut avoir plusieurs appareils signataires.
- Un appareil peut etre revoque sans supprimer l'historique qu'il a signe.
- Les roles et acces sont dates, expirables et revocables.
- La revocation bloque les acces futurs. Elle n'efface pas ce qui a deja ete
  dechiffre, replique ou signe legitimement.

Options locales Windows a garder compatibles:

- mot de passe de coffre;
- secret membre ou phrase de secours;
- Windows Hello / DPAPI comme confort local, jamais comme seule source de
  recuperation collective;
- fichier de secours chiffre;
- invitation hors ligne par QR ou fichier.

## Niveaux de droits

Les niveaux produit V1 sont:

- `copro`: information collective ouverte aux coproprietaires;
- `cs`: information du conseil syndical;
- `commission`: information limitee a une commission thematique et a son mandat.

Ces niveaux ne remplacent pas les colleges de confidentialite existants. Ils
donnent un langage lisible pour les parcours comptes et commissions.

Roles de depart:

- `coproprietaire`: voit le corpus collectif autorise et peut contribuer dans
  les limites prevues;
- `conseil_syndical`: voit et agit sur le niveau CS;
- `referent_commission`: membre CS responsable d'une commission donnee;
- `contributeur_commission`: contributeur ponctuel sur un mandat de commission;
- `auditeur_lecture`: lecture limitee, sans pouvoir de modification;
- `administrateur_local`: aide technique locale, sans acces contenu implicite;
- `syndic`: interlocuteur ou contributeur selon mandat explicite, pas
  administrateur global automatique.

Une commission thematique n'est pas automatiquement le conseil syndical. Ses
droits doivent citer un sujet, une duree, un referent CS et les ressources
ouvertes.

## Objets noyau

`UserAccount`

- identifie la personne dans l'application locale;
- stocke un nom d'affichage et un contact facultatif;
- peut etre desactive localement sans toucher aux coffres.

`LocalProfile`

- lie un `UserAccount` a un poste;
- note le mode de protection local;
- ne donne aucun droit dans un coffre par lui-meme.

`VaultMember`

- identifie une personne dans un coffre;
- porte le rattachement au coffre, les lots facultatifs et l'etat de revocation;
- reste dans l'historique apres revocation.

`DeviceIdentity`

- identifie un appareil signataire par cle publique;
- peut signer seulement s'il est actif et non revoque;
- sa revocation n'invalide pas les signatures historiques valides.

`RoleGrant`

- donne un role a un membre sur un niveau `copro`, `cs` ou `commission`;
- peut commencer plus tard, expirer ou etre revoque;
- conserve l'evenement source pour audit.

`AccessGrant`

- ouvre explicitement une ressource ou un type de ressource;
- sert aux exceptions proportionnees: contentieux, lot privatif, export,
  action, preuve ou commission;
- expire ou se revoque sans suppression de l'historique.

`CommissionMembership`

- rattache un membre a une commission, un theme et un role;
- ne vaut que pour la commission nommee;
- doit etre borne par mandat ou date d'expiration quand c'est ponctuel.

`RecoveryShare`

- decrit une part de recuperation de cle sans exposer le secret;
- indique le groupe, le seuil et le detenteur;
- permet d'afficher si un quorum existe.

## Helpers attendus

Le noyau expose des helpers lisibles:

- `identity_summary`: repond a `qui suis-je`, `ce que je peux voir`, `ce que je
  peux faire`, `qui peut recuperer`;
- `can_member_access_resource`: explique une decision d'acces ponctuelle;
- `recovery_groups_for`: liste les groupes de recuperation et leur quorum;
- methodes `is_active` sur les objets dates.

Les helpers ne doivent pas promettre une securite cryptographique. Ils decrivent
les droits V1 et les effets de revocation pour guider l'UI et les futurs
evenements signes.

## Audit et limites

Toute modification future de membre, role, acces, appareil ou part de
recuperation devra produire un evenement signe dans le vault.

Limites assumee V1:

- une revocation n'efface pas les copies locales deja dechiffrees;
- un administrateur du poste peut casser son installation locale, mais ne doit
  pas pouvoir confisquer la memoire collective si les exports et replicas
  existent;
- la recuperation de cle demande un quorum, pas une seule personne;
- les connecteurs email ou messagerie restent des plugins officiels futurs.
