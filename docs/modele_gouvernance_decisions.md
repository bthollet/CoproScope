# Modele de gouvernance des decisions et d'autorisation des depenses

Date de creation: 2026-09-02.
Issu du travail de conception Brice / agent du 2026-09-02.
Statut au 2026-09-02: **modele soumis a contradiction**, non implemente. Aucun
code ecrit a ce jour. Il a ete concu par un seul agent en dialogue avec Brice;
aucun expert metier ne l'a encore attaque. Six trous sont deja identifies par
l'auteur lui-meme et listes en section 13 bis. Ne pas le traiter comme une
specification tant que la phase `red-team borne` prevue par
[`protocole_agents_claude_code.md`](./protocole_agents_claude_code.md) n'a pas
eu lieu.

Ce document fixe le noyau du produit: **tout euro depense doit trouver son acte
d'autorisation, ou l'absence d'autorisation est nommee.**

Toutes les references legales ci-dessous ont ete lues sur Legifrance le
2026-09-02 via l'API PISTE, dans leur version en vigueur a cette date. Les
identifiants `LEGIARTI` sont donnes au paragraphe 10. Ne pas les reecrire de
memoire.

---

## 1. L'atome

L'atome n'est pas le document, ni la depense. C'est **l'acte d'autorisation**.

Il a trois natures, dont **une seule est autonome**:

| Nature | Autonome | Ce qui la fonde |
|---|---|---|
| `RESOLUTION_AG` | oui | elle-meme, une fois adoptee a la majorite requise |
| `DECISION_CS_DELEGUEE` | non | une resolution de delegation en vigueur a la date |
| `URGENCE_SYNDIC` | non | rien en amont: c'est precisement le point |

Les deux natures derivees ne tirent pas leur validite d'une propriete propre
mais d'un **predicat calculable sur leurs liens**. Une seule table, une colonne
`nature`, et des liens obligatoires dont la direction et les contraintes
dependent de la nature.

Consequence: on ne cree pas deux objets concurrents `resolution AG` et
`decision CS`. On cree un objet `acte d'autorisation` avec trois natures.

## 2. Les liens et leur direction

Toute autorisation qui n'est pas une resolution d'AG porte **deux liens
obligatoires**. L'absence de l'un ou de l'autre est un constat distinct.

| Nature | Lien arriere | Lien avant |
|---|---|---|
| `RESOLUTION_AG` | elle-meme | aucun |
| `DECISION_CS_DELEGUEE` | la delegation en vigueur a la date de la decision | le compte rendu devant l'AG votant l'approbation des comptes (art. 21-5) |
| `URGENCE_SYNDIC` | aucun | une AG convoquee immediatement (decret art. 37) |

Le lien arriere est une **condition de validite**. Le lien avant est une
**obligation a echeance**: son absence n'est pas une piece manquante, c'est un
manquement date.

Regle de datation, a ne pas simplifier en decalage d'exercice: le critere est
**la delegation en vigueur a la date de la depense**, pas la delegation de
l'annee precedente. L'article 21-3 donne deux ans, donc une delegation votee en
2023 couvre une depense de 2024, et une delegation votee en mars 2025 ne couvre
pas une depense de janvier 2024. Une regle en `annee N-1` produirait des faux
positifs et des faux negatifs a la fois.

## 3. Controles de la delegation au conseil syndical

Sources: loi 65-557 articles 21-1, 21-2, 21-3, 21-5.

Conditions de validite de la delegation elle-meme:

- conseil syndical d'au moins **trois membres**;
- vote a la **majorite des voix de tous les coproprietaires**;
- porte uniquement sur des decisions relevant de la **majorite simple**;
- **duree maximale de deux ans**, renouvelable par decision **expresse**;
- l'AG fixe le **montant maximum des sommes allouees**.

Trois interdictions absolues, qui rendent la decision nulle quelle que soit la
delegation. La delegation ne peut jamais porter sur:

1. l'approbation des comptes;
2. la determination du budget previsionnel;
3. les adaptations du reglement de copropriete rendues necessaires par les
   evolutions legislatives et reglementaires.

Controles executables:

| Controle | Constat si echec |
|---|---|
| decision de CS rattachee a une delegation en vigueur a sa date | decision prise sans pouvoir |
| decision de CS plus de deux ans apres le vote, sans renouvellement expres | delegation expiree |
| **cumul** des depenses deleguees sur la periode contre le plafond de l'art. 21-2 | plafond depasse |
| objet de la decision hors des trois matieres exclues | decision nulle |
| compte rendu du CS devant l'AG d'approbation des comptes | obligation de rendre compte non tenue |

Le controle de plafond se fait **en cumul sur la periode de delegation**, pas
depense par depense. C'est le seul qui ne se voit pas ligne a ligne.

## 4. Controles de l'urgence

Source: decret 67-223 article 37.

L'article a **deux etages**, et cette structure fournit la gradation qu'il ne
faut donc pas inventer.

**Etage 1, toujours applicable.** Le syndic informe les coproprietaires et
**convoque immediatement une assemblee generale**.

**Etage 2, seulement si le syndic appelle une provision.** Il peut, par
derogation a l'article 35 et **apres avoir pris l'avis du conseil syndical**
s'il en existe un, demander une provision **qui ne peut exceder le tiers du
montant du devis estimatif**. Toute provision suivante exige une decision d'AG.

Consequence pratique voulue par Brice: une petite depense d'urgence payee sur le
compte courant, sans appel de provision, **n'engage jamais l'etage 2**. Le bruit
disparait de lui-meme, sans tolerance inventee.

L'etage 2 apporte trois controles supplementaires, qui supposent l'existence
d'un devis estimatif - ce que personne n'attend d'une urgence:

- avis du conseil syndical pris avant la provision;
- provision initiale inferieure ou egale au tiers du devis estimatif;
- aucune provision suivante sans decision d'AG intercalaire.

Pour l'etage 1, l'outil enonce un **fait date, jamais un verdict**:

| Situation | Sortie |
|---|---|
| AG convoquee sans delai anormal | conforme |
| Portee a l'AG ordinaire suivante | signale, avec le delai en clair: `portee a l'AG ordinaire du 12 juin, soit 287 jours apres la depense`; priorite selon montant et delai |
| Jamais portee a aucune AG | **manquement, quel que soit le montant** |

Le plancher est la seule regle dure: une depense d'urgence qui n'atteint aucune
assemblee est un manquement. Entre les deux, l'outil affiche et laisse juger.

Raison de cette prudence, et elle est operationnelle autant que juridique: un
outil qui crie au manquement sur une reparation de cinquante euros est detruit
par le premier professionnel qui le lit, et tout le reste tombe avec.

## 5. Le test d'aiguillage: budget previsionnel ou vote separe

C'est le controle qui vaut le plus, et il resout le probleme de deploiement de
la resolution budgetaire.

Point de depart a ne pas confondre: **un ecart entre le realise et le
previsionnel n'est pas un defaut**. L'article 14-1 organise un budget estimatif
finance par des provisions egales au quart du budget vote, et l'ecart se
regularise a l'approbation des comptes. Controler que le realise correspond au
previsionnel signalerait le fonctionnement normal.

Le vrai controle est le suivant. L'article 14-1 II exclut du budget previsionnel
les depenses pour travaux dont la liste est fixee par decret. L'article 44 du
decret donne cette liste:

1. travaux de conservation ou d'entretien **autres que ceux de maintenance**;
2. travaux sur les elements d'equipement communs **autres que ceux de
   maintenance**;
3. travaux d'amelioration;
4. **etudes techniques, telles que les diagnostics et consultations**;
5. plus generalement, tout ce qui ne concourt pas a la maintenance et a
   l'administration des parties communes.

L'article 45 fixe la frontiere. La maintenance, c'est l'entretien courant et les
menues reparations. Avec deux precisions decisives:

- le **remplacement** d'une chaudiere ou d'un ascenseur n'est assimile a de la
  maintenance **que si son prix est compris forfaitairement dans le contrat de
  maintenance**. Sinon, article 44, donc vote separe. Ce controle exige de lire
  le contrat: il branche directement la colonne contrat sur la colonne decision.
- les **verifications periodiques reglementaires** sont de la maintenance, mais
  les **diagnostics et consultations** ne le sont pas. Un diagnostic impute au
  budget courant est un ecart, et c'est frequent.

**Regle:** une depense relevant de l'article 44 imputee au budget previsionnel
est une depense engagee sans le vote qu'elle exigeait. C'est le moyen le plus
simple de depenser sans faire voter.

**Ce que ce test resout.** La resolution qui vote le budget previsionnel reste
une resolution comme les autres dans la table. Son execution ne se controle pas
facture par facture mais en deux temps:

1. au niveau du **poste**: ecart poste par poste, provisions, regularisation;
2. par un **test unitaire bon marche sur chaque facture**: cette depense a-t-elle
   sa place dans le budget previsionnel au sens des articles 44 et 45.

Une facture qui echoue au test n'appartient pas a la resolution budgetaire: elle
doit trouver sa propre autorisation, et si elle n'en a pas, c'est un constat. Il
n'y a donc pas deux regimes de rattachement, mais un seul, plus un aiguillage.

## 6. Controles budgetaires complementaires

Par ordre d'interet decroissant, apres le test d'aiguillage:

- **ecart poste par poste**, jamais seulement global. Un total qui tombe juste
  avec des postes qui se compensent cache une reaffectation.
- **provisions appelees contre budget vote**: le quart, sauf modalites
  differentes votees par l'AG.
- **regularisation effective** du solde a l'approbation des comptes.
- **delai de six mois**: l'AG appelee a voter le budget previsionnel est reunie
  dans les six mois du dernier jour de l'exercice comptable precedent. Controle
  purement calendaire, il ne demande que les dates des PV, donc il fonctionne
  des le premier jour sur une instance presque vide.

## 7. La chaine de decision et l'ecran gouvernance

L'ecran de gouvernance se lit de gauche a droite comme la chronologie d'une
decision legitime. Cinq colonnes.

| Colonne | Contenu |
|---|---|
| Seuils | trois cellules: seuil de consultation du CS, seuil de mise en concurrence, regime propre du contrat de syndic |
| Avis du conseil syndical | requis au-dela du seuil de consultation, et aussi pour la provision d'urgence |
| Resolution | numero, objet, majorite appliquee, majorite requise, resultat |
| Annexes | a minima les conditions essentielles, idealement les devis |
| Devis retenu | le devis effectivement adopte, distingue des devis ecartes |

Chaque cellule renvoie a la zone exacte du PDF source.

Un trou dans chaque colonne porte un nom different, et c'est l'interet du
decoupage: `au-dessus du seuil sans consultation du CS`, `votee sans devis`,
`votee par renvoi a une annexe absente`, `devis paye different du devis vote`.

**Les seuils, source verifiee.** Article 21 de la loi: l'AG, statuant a la
majorite de l'article 25, arrete un montant des marches et contrats a partir
duquel **la consultation du conseil syndical** est obligatoire; a la meme
majorite, elle arrete un montant des marches et contrats **autres que celui de
syndic** a partir duquel **une mise en concurrence** est obligatoire. Le contrat
de syndic a son regime propre: mise en concurrence par le conseil syndical,
dispense possible votee a la majorite des voix de tous les coproprietaires, la
demande etant inscrite a l'ordre du jour de l'AG **precedente**. Sans conseil
syndical institue, cette mise en concurrence n'est pas obligatoire.

**Le modele est recursif.** Les seuils de la colonne de gauche sont eux-memes
une resolution de l'AG de l'annee precedente. Le controle de l'annee N produit
le referentiel de l'annee N+1.

## 8. Les trois etats de la colonne avis du conseil syndical

Beaucoup de conseils syndicaux n'ont pas de compte rendu: la concertation se
fait par courriel, parfois oralement. Refuser de modeliser cette realite rendrait
l'outil inutilisable. Mais une case a cocher transformerait une colonne
probatoire en declaration.

Trois etats, donc, et pas deux:

| Etat | Sens |
|---|---|
| `PIECE_PRODUITE` | l'avis existe et il est rattache |
| `AFFIRME_SANS_PIECE` | quelqu'un declare que la decision a eu lieu, sans document |
| `ABSENT` | rien |

Pour l'etat intermediaire, un **champ de saisie libre en mode degrade**, retenu
comme premiere intention pour la beta. Le glisser-un-courriel et la connexion a
une messagerie viendront plus tard.

Texte affiche a l'utilisateur, a reprendre tel quel:

> Je declare qu'une decision du conseil syndical a bien eu lieu, mais je n'ai
> pas de document pour l'etablir.

Consequence affichee juste en dessous:

> Utile au conseil syndical pour se reperer. Ne vaut pas preuve dans un document
> transmis a un tiers.

L'outil enregistre qui l'a ecrit et quand. Le verbe est **declarer** et non
certifier: certifier a un poids juridique, et cette phrase est mise dans la
bouche d'un benevole qui peut se tromper de bonne foi.

**Regle dure:** un `AFFIRME_SANS_PIECE` ne franchit jamais la frontiere vers une
sortie destinee a un tiers en tant que preuve.

Infobulle a afficher dans la colonne, pour expliquer la delegation:

> Par principe, c'est l'assemblee generale qui decide des depenses du syndicat.
> Elle peut cependant deleguer au conseil syndical le pouvoir de prendre tout ou
> partie des decisions relevant de la majorite simple, si le conseil compte au
> moins trois membres et si la delegation est votee a la majorite des voix de
> tous les coproprietaires. Elle en fixe le montant maximum et la duree, qui ne
> peut exceder deux ans. La delegation ne peut jamais porter sur l'approbation
> des comptes ni sur le budget previsionnel. Le conseil syndical rend compte de
> son usage devant l'assemblee qui approuve les comptes.
> Articles 21-1 a 21-5 de la loi n. 65-557 du 10 juillet 1965, version en
> vigueur au 2 septembre 2026.

## 9. Deux etats de cycle de vie: constatee et projetee

Controler l'AG passee et preparer l'AG suivante ne sont pas deux directions de
lecture d'un meme objet. Ce sont **deux objets de nature differente qui
partagent une forme**.

| Etat | Nature |
|---|---|
| `CONSTATEE` | extraite d'un PV recu, **non editable**, ancree a sa source, autorite externe |
| `PROJETEE` | editable, locale, sans aucune autorite |

Meme schema, deux etats, et une regle dure: une `PROJETEE` n'apparait jamais
comme preuve dans une sortie destinee a un tiers.

**Interdiction de promotion.** Quand le PV revient, on ne transforme pas la
projetee en constatee. On cree le constat **a cote** du projet, et on les
**compare**. L'ecart entre ce que le conseil syndical a propose et ce que le PV
rapporte est l'un des constats les plus precieux du produit: resolution modifiee
en seance, montant change, point retire de l'ordre du jour, entreprise
substituee. Une fusion ferait disparaitre cet ecart sans laisser de trace.

C'est donc une boucle a deux voies paralleles, pas un objet qui se transforme.

## 10. Sorties propres au modele

Deux mesures qu'aucun syndic ne produit, et qui tombent de la meme jointure lue
dans l'autre sens:

- **taux d'execution des resolutions**: combien de resolutions votees ont une
  execution tracee, combien sont restees lettre morte, combien ont ete executees
  autrement qu'il n'avait ete vote;
- **taux de resolutions quantifiees**: combien nomment un montant et une
  entreprise, combien renvoient a une annexe introuvable.

Elles correspondent aux deux missions du conseil syndical enoncees a l'article
21: assister et controler. C'est la meme table lue dans les deux sens.

## 11. Etat du code au 2026-09-02

**Ce qui existe et sert directement.** Le module `pdftrace` fabrique l'ancrage
d'une valeur vers une zone de PDF: pre-annotation, desambiguisation de ligne,
file `/pdf-traces`, traces par document. Ce sont les trois derniers commits de
la branche `codex/20260611-pdftrace-preannotation`. C'est la primitive dont les
renvois de l'ecran gouvernance ont besoin.

Le vocabulaire de qualification porte deja les 52 types necessaires, dont
`PV_AG`, `CR_CS`, `Devis`, `Facture`, `Releve_Bancaire`, `Grand_Livre`,
`Etat_Depenses`, `Ordre_Service`, `Situation_Travaux`, `Reception_Travaux`.

**Ce qui manque, et c'est la fondation.** La resolution n'existe pas comme
objet. Le registre AG est **une ligne par document**, avec `resolution_count`,
`annex_hits`, `majority_terms`, c'est-a-dire des compteurs agreges. Le fichier
`server/src/coproscope/schemas/ag_resolution.schema.json` porte le titre
`CoproScope AG Register Row`, decrit ce meme agregat, et **n'est reference par
aucun code Python**: une intention restee a l'etat de nom de fichier.

Le modele exige une ligne par resolution portant: numero, objet, majorite
appliquee, majorite requise, resultat, montant, entreprise, annexe visee et
ancre PDF. Tant que cet objet n'existe pas, aucune des cinq colonnes ne peut
etre remplie.

L'entree, elle, range par **provenance** (`inbox`, `glisser-deposer`, `Drive`)
et non par **role probatoire**. Le rapprochement quatre sources ne peut pas
remplir quatre colonnes qui n'ont jamais ete collectees comme quatre.

## 12. References verifiees

Lues sur Legifrance le 2026-09-02 via l'API PISTE, versions en vigueur a cette
date. A citer avec leur date de version.

| Texte | Objet | Identifiant |
|---|---|---|
| Loi 65-557 art. 14-1 | budget previsionnel, provisions au quart, delai de six mois, exclusion des travaux | `LEGIARTI000043977299` |
| Loi 65-557 art. 21 | conseil syndical, deux seuils votes a la majorite de l'art. 25, regime du contrat de syndic, penalites de retard | `LEGIARTI000039313574` |
| Loi 65-557 art. 21-1 | delegation au CS: conditions et matieres exclues | `LEGIARTI000039301559` |
| Loi 65-557 art. 21-2 | montant maximum alloue au CS | `LEGIARTI000039301561` |
| Loi 65-557 art. 21-3 | duree maximale de deux ans, renouvellement expres | `LEGIARTI000039301563` |
| Loi 65-557 art. 21-5 | majorite au sein du CS, compte rendu devant l'AG d'approbation des comptes | `LEGIARTI000039301567` |
| Decret 67-223 art. 37 | urgence: informer et convoquer immediatement, provision au tiers du devis | `LEGIARTI000053191357` |
| Decret 67-223 art. 44 | liste des depenses non comprises dans le budget previsionnel | `LEGIARTI000006488761` |
| Decret 67-223 art. 45 | definition de la maintenance et cas assimiles | `LEGIARTI000006488770` |

## 13. Points ouverts

- **Table objet vers majorite requise** (articles 24, 25, 25-1, 26). Necessaire
  au controle de majorite. Se verifie texte par texte, ne s'infere pas. A
  construire avant tout controle automatique de vote. Rappel de methode: mene a
  la main sur un cas reel, ce controle a **ecarte** un soupcon plutot que d'en
  produire un. Un controle dont la valeur se mesure autant a ce qu'il innocente
  qu'a ce qu'il signale merite d'etre construit avec soin.
- **Rattachement automatique facture vers decision**: sur quoi il s'appuie. Le
  montant et le fournisseur sont fragiles - un devis vote a 22 200 donne une
  facture a 23 460 apres avenant, et le nom commercial differe de la raison
  sociale. Position retenue: l'outil **propose** un rattachement avec son motif
  et son doute, il ne rattache jamais silencieusement. A eprouver, car cela
  change le volume de gestes humains.
- **Selection du devis retenu**: proposition automatique depuis le PV, qui nomme
  le titulaire et le montant votes, mais **confirmation humaine obligatoire**.
  Une designation automatique erronee contamine tout le dossier de depense en
  aval sans que l'utilisateur sache d'ou vient l'erreur.
- **Renvoi vers le compte rendu de CS de l'annee precedente**: reporte a une
  version ulterieure pour l'automatisme, mais **le champ doit exister des
  maintenant**, meme rempli a la main. Sinon la structure devra etre refaite.

## 13 bis. Trous identifies par l'auteur du modele

Point de methode: ceux qui suivent sont ceux que l'auteur sait nommer, donc
**precisement ceux qui ne sont pas dangereux**. Les dangereux sont ceux qu'il ne
voit pas. Cette liste est un point de depart pour le `red-team`, pas un
inventaire.

1. **Le fonds de travaux.** Une depense payee sur le fonds exige une
   **affectation votee**, en plus de son autorisation. Le modele n'en porte
   aucune trace. Manque le plus grave, la matiere existant deja dans le travail
   d'audit d'aout 2026.
2. **La repartition des charges.** Une facture parfaitement autorisee peut etre
   imputee a la mauvaise cle, au mauvais poste, ou faire supporter a tous une
   charge speciale. Dimension de controle entiere, absente.
3. **La passerelle de l'article 25-1.** Une resolution rejetee a la majorite de
   l'article 25 peut etre remise au vote a l'article 24 dans la meme assemblee.
   Le controle `majorite appliquee contre majorite requise` les signalerait
   toutes comme anomalies. Faux positifs garantis.
4. **Decisions de justice et obligations legales** - travaux ordonnes, PPPT, DPE
   collectif, individualisation des frais de chauffage. Le vote porte parfois sur
   les modalites et non sur le principe.
5. **Travaux d'interet collectif sur parties privatives.**
6. **Avances et provisions**, qui ne se confondent pas.

## 14. Suite

Les deux documents de parcours de test,
[`parcours_utilisateur_tests_ux.md`](./parcours_utilisateur_tests_ux.md) et
[`parcours_b_controle_comptes.md`](./parcours_b_controle_comptes.md), sont
anterieurs a ce modele et commencent apres lui. Ils sont a reprendre sur cette
base.
