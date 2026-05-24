# Strategie anti-confiscation des cles

Date de reference : 2026-05-20

## Intention produit

CoproScope doit empecher qu'une personne, un conseil syndical sortant, un
prestataire, un compte cloud ou un appareil unique puisse confisquer la memoire
de la copropriete.

La promesse testable est la suivante :

- tout coproprietaire peut telecharger l'archive complete chiffree ;
- l'archive complete contient aussi les contenus restreints sous forme chiffree ;
- le coproprietaire peut verifier l'integrite et la completude sans tout lire ;
- seuls les contenus autorises par son role et ses cles deviennent lisibles ;
- les cles critiques ont un quorum de secours documente ;
- une revocation honnete bloque les acces futurs sans falsifier l'historique ;
- des copies lectrices permettent de survivre a une capture ou suppression ;
- les alertes distinguent risque de capture, suppression malveillante et simple
  retard de synchronisation.

Cette strategie reste generique. Elle ne stocke aucun nom de personne, aucune
adresse, aucun identifiant de lot, aucun secret et aucune donnee privee.

## Menaces traitees

### Capture de gouvernance

Un groupe disposant d'un acces d'administration tente d'empecher les autres
coproprietaires d'obtenir une archive complete, de verifier les trous ou de
reconstruire le corpus commun. Le produit doit rendre cette capture visible :
absence de copie lectrice recente, quorum de cle absent, export refuse, manifestes
manquants, historique tronque ou changement de gardiens non signe.

### Suppression malveillante

Un acteur supprime un blob, un evenement, un snapshot, une enveloppe de cle ou un
rapport de verification. Le produit doit detecter le trou par hash, sequence,
preuve d'existence ou comparaison avec une copie lectrice. La reconstruction doit
echouer explicitement au lieu de produire une memoire silencieusement incomplete.

### Fausse promesse de lecture

L'archive complete ne donne pas un droit de lecture universel. Les contenus
restreints restent inaccessibles sans cle de compartiment. Le coproprietaire
obtient la preuve que ces contenus existent, pas leur contenu clair.

### Confiscation de cles

Une cle collective ne doit pas dependre d'un seul appareil ou d'une seule
personne. Les cles critiques doivent avoir un partage de secours par quorum, avec
parts inutilisables seules, gardiens distincts et rotation apres depart, perte ou
revocation.

## Archive complete chiffree

Chaque coproprietaire dispose d'un parcours `Telecharger l'archive complete
chiffree`. Le paquet contient :

- `vault.json` public ou non sensible ;
- les evenements signes append-only ;
- les manifestes de blobs et snapshots ;
- les blobs chiffres, y compris ceux qui restent restreints ;
- les enveloppes de cles et politiques de recuperation, sans cle en clair ;
- les cles publiques de verification ;
- un rapport machine d'integrite ;
- un rapport novice expliquant ce qui est lisible, restreint ou incomplet.

Les contenus restreints sous forme chiffree font partie du paquet complet afin
que leur presence soit verifiable sans ouvrir le contenu clair.

L'archive complete peut etre remise sous forme de fichier local, support externe
ou copie lectrice. Le canal de transport n'est jamais presente comme une garantie
cloud : la garantie vient du manifeste, des signatures, des hashes, des copies
independantes et de la capacite de reconstruction.

## Verification sans tout lire

Le coproprietaire doit pouvoir verifier l'archive sans ouvrir tous les contenus.
La verification s'appuie sur des metadonnees non sensibles :

- hash canonique du manifeste ;
- hash et taille de chaque payload chiffre ;
- preuve d'existence par entree ;
- chainage des evenements signes ;
- presence des cles publiques de signature ;
- presence des enveloppes de cles attendues ;
- compteur d'evenements, blobs, snapshots et compartiments ;
- liste des trous, doublons ou incoherences.

Le rapport novice doit separer clairement :

- `ce_que_je_peux_reconstruire` ;
- `ce_qui_existe_mais_reste_restreint` ;
- `ce_qui_est_manquant_ou_suspect` ;
- `qui_peut_aider_a_recuperer` ;
- `actions_recommandees`.

Une verification valide ne signifie pas que tout est lisible. Elle signifie que
la structure complete annoncee est coherente et que les restrictions sont
reperees.

## Reconstruction autorisee

La reconstruction locale part d'un cache vide et n'ecrit que les elements
autorisables :

1. verifier le manifeste, les signatures, les hashes et les sequences ;
2. reconstruire les index non sensibles ;
3. tenter l'ouverture des compartiments pour lesquels le role et la cle sont
   presents ;
4. produire des preuves de presence pour les compartiments restreints ;
5. refuser les contenus dont la cle est absente, revoquee ou incoherente ;
6. produire un rapport final signable ou exportable.

Le resultat attendu est une memoire lisible partielle mais verifiable : le
coproprietaire voit ce qu'il peut ouvrir, sait ce qui existe, et peut prouver
qu'une partie restreinte ou manquante n'a pas ete ignoree.

## Contenus restreints

Les contenus restreints sont inclus dans l'archive sous forme chiffree pour
eviter la confiscation par omission. Ils restent inaccessibles sans cle.

Regles minimales :

- aucun payload restreint dans le manifeste clair ;
- aucune donnee personnelle dans les libelles publics de preuve ;
- aucune cle de compartiment stockee en clair ;
- aucune tentative de contournement par export novice ;
- une raison de restriction lisible et non sensible ;
- une preuve d'existence verifiable par hash ;
- un contact ou groupe de recuperation quand la politique l'autorise.

Cette separation protege simultanement le droit de preservation et la
confidentialite legitime.

## Quorum et partage de secours

Les cles critiques doivent avoir une politique de recuperation :

- seuil minimal de quorum superieur ou egal a 2 ;
- nombre de parts distinctes superieur ou egal au quorum ;
- parts inutilisables seules ;
- gardiens de categories differentes quand c'est possible ;
- absence de gardien unique lie au meme compte cloud ;
- rotation apres depart, perte, compromission ou revocation ;
- verification periodique de l'existence des parts ;
- ceremonie de recuperation signee, historisee et notifiee.

Un quorum peut recuperer ou reenvelopper une cle collective, mais il ne doit pas
effacer l'historique des acces passes. La recuperation produit un evenement
`key_recovery_performed` contenant au minimum le compartiment, le motif, la
preuve de quorum, les nouvelles enveloppes de cle, la date et le statut de
notification.

## Revocation honnete

La revocation doit etre honnete, c'est-a-dire explicite sur ses limites.

Elle doit :

- bloquer les nouveaux dechiffrements et nouvelles signatures de l'acteur revoque ;
- conserver les signatures et evenements valides produits avant revocation ;
- conserver les copies deja repliquees dans l'historique verifiable ;
- declencher une rotation ou un reenveloppement des cles concernees ;
- signaler les copies deja dechiffrees comme risque residuel ;
- documenter la date d'effet, le motif et l'autorite de revocation ;
- ne jamais supprimer silencieusement une partie de l'historique.

Elle ne peut pas :

- effacer une copie locale deja dechiffree ;
- prouver qu'un ancien lecteur a detruit ses fichiers ;
- transformer une restriction future en disparition du passe.

Cette limite doit etre visible dans l'interface pour eviter une fausse promesse
de securite.

## Copies lectrices

Une copie lectrice est une replique verifiable qui peut conserver l'archive
complete chiffree et verifier son integrite, sans disposer forcement de toutes
les cles de lecture.

Objectifs :

- multiplier les points de preservation ;
- detecter les suppressions par comparaison de manifestes ;
- permettre une reconstruction locale du corpus autorise ;
- survivre a la perte d'un compte cloud ou d'un appareil principal ;
- garder une trace horodatee des archives recues et verifiees.

Une copie lectrice n'est pas une delegation d'administration. Elle ne peut pas
modifier le vault, inventer une signature, lire les compartiments restreints sans
cle, ni imposer une recuperation de cle sans quorum.

## Alertes de capture et suppression

Le produit doit produire des alertes actionnables, non alarmistes et testables :

- `capture_possible` : aucun coproprietaire lecteur actif, gardiens concentres,
  quorum absent, refus d'archive complete ou changement de politique non signe ;
- `suppression_suspecte` : evenement, blob, snapshot, enveloppe ou preuve attendu
  manquant dans une archive ou dans une copie lectrice ;
- `archive_incomplete` : manifeste incoherent, hash faux, sequence cassee ou
  compteur incompatible ;
- `cle_a_risque` : cle critique sans quorum, parts insuffisantes, part expiree
  ou absence de rotation apres revocation ;
- `copie_lectrice_obsolete` : derniere verification trop ancienne ou ecart de
  manifeste non explique ;
- `revocation_incomplete` : acces futur bloque mais rotation de cle non prouvee.

Chaque alerte doit indiquer une action simple : verifier une archive, demander
une nouvelle copie, reunir un quorum, tourner une cle, recreer une copie lectrice
ou consigner une contestation.

## UX attendue

Le parcours doit rester comprehensible pour un coproprietaire non technicien :

- bouton `Telecharger l'archive complete chiffree` ;
- bouton `Verifier une archive` ;
- bouton `Reconstruire mon corpus autorise` ;
- panneau `Ce que je peux lire` ;
- panneau `Ce qui existe mais reste restreint` ;
- panneau `Cles et quorum de secours` ;
- panneau `Copies lectrices` ;
- panneau `Alertes anti-confiscation` ;
- journal des recuperations, rotations, revocations et verifications.

Les libelles doivent eviter les promesses absolues. On parle de verification,
preuve, reconstruction autorisee et risque residuel, pas de recuperation garantie
dans tous les cas.

## Criteres d'acceptation testables

- un coproprietaire peut telecharger une archive complete chiffree ;
- l'archive complete inclut les payloads restreints chiffres ;
- le manifeste ne contient aucun payload restreint en clair ;
- la verification detecte un blob, evenement, snapshot ou manifeste manquant ;
- la verification peut confirmer l'existence d'un contenu restreint sans le lire ;
- la reconstruction depuis cache vide ne rend que le corpus autorise ;
- une cle absente, fausse ou revoquee ne revele pas le payload ;
- une seule part de secours ne recupere jamais une cle critique ;
- un quorum valide produit une recuperation historisee et notifiee ;
- une revocation bloque les acces futurs sans effacer l'historique passe ;
- une copie lectrice peut verifier et conserver l'archive complete chiffree ;
- une copie lectrice ne peut pas modifier le vault ni contourner les restrictions ;
- une suppression malveillante produit une alerte visible ;
- une capture possible produit une alerte visible ;
- les rapports restent generiques et ne contiennent aucune donnee privee.

## Non-objectifs

- promettre la destruction des copies deja dechiffrees ;
- donner acces aux compartiments restreints sans cle ;
- centraliser la recuperation chez une seule personne ;
- presenter un compte cloud comme source de verite suffisante ;
- exposer des donnees privees dans les rapports, tests ou fixtures ;
- definir un algorithme cryptographique definitif dans cette note.
