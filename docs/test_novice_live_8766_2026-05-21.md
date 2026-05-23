# Test novice live - CoproScope

Date: 2026-05-21
Serveur teste: http://127.0.0.1:8766/?token=local-secret
Role simule: membre du conseil syndical novice, non technique
Support de controle: routes live + captures `docs/assets/ux-livraison-reelle-2026-05-21-8766/`

Note de methode: je n'ai pas modifie le code, je n'ai pas soumis de depot de fichier et je n'ai pas declenche d'action destructive. Les clics testes sont des liens/exports GET et les formulaires de recherche/filtre.

## Synthese priorisee

Verdict global: **GO partiel**. Le produit montre bien une logique conseil syndical: actions, preuves, relances, comptes, depot local, passation. En revanche, un membre CS novice reste bloque sur plusieurs actions de base: creer une demande, ajouter un document depuis la page dediee, ouvrir un brouillon de relance, exporter certaines listes, comprendre quel ecran est vraiment actionnable.

Priorites bloquantes:

1. **Ajouter un document est un NO-GO sur `/documents/ajouter`**: la route explique le parcours mais ne propose aucun champ fichier, bouton ou lien evident vers le depot.
2. **Nouvelle demande est un NO-GO sur `/demandes`**: le bouton global `+ Nouvelle demande` renvoie vers une page statique sans formulaire.
3. **Exports casses**: `/actions?priority=P1` propose `Exporter une liste de travail apres apercu`, mais le lien `/exports/passation?scope=open-actions&token=local-secret` repond 404. Dans `/depot`, `Actions CSV` et `Actions Markdown` n'embarquent pas le token et repondent 403.
4. **Creation d'action trompeuse**: dans `/actions`, `Rattacher a une decision AG` et `Action libre du conseil syndical` rechargent le registre sans afficher de formulaire de creation.
5. **Relance syndic fragile**: `Ouvrir le brouillon` mene a une fiche action sans brouillon visible; `Copier le brouillon` n'a pas de retour de succes; `Marquer comme envoye hors CoproScope` ne demande pas la date/le canal alors que la page dit que c'est requis.
6. **Orientation novice instable**: plusieurs routes ont comme H1 technique `Cockpit Conseil Syndical` au lieu du titre de la page (`Demandes`, `Pilotage`, `Ajout de document`, `Depot`). Le bandeau de contexte et les alertes coffre/sync prennent beaucoup de place avant l'action concrete.

## Constats transverses

- Toutes les routes demandees repondent en 200.
- Le menu lateral aide a se reperer, mais certains libelles ne correspondent pas au titre reel: `Chantiers` ouvre `Memoire de copropriete`; `Demandes syndic` ouvre une boite de demandes generale; `AG contentieux novice` affiche 0 dans le menu mais la page contient 1 question AG, 1 piece de convocation et 3 echeances.
- Les captures montrent une action globale en haut a droite partiellement coupee (`Nouvelle demande`) sur plusieurs pages. Pour un novice, c'est un bouton important qui doit rester entierement visible.
- Les blocs `Role a confirmer`, `Coffre signe a declarer`, `Sync non branchee` sont utiles, mais ils dominent trop souvent le premier ecran. Les transformer en bandeau compact ou en checklist refermable aiderait a atteindre plus vite l'action.
- Les pages conceptuelles sont pedagogiques, mais sans CTA, elles ressemblent a une documentation plutot qu'a un produit livre.

## Route `/`

Verdict: **GO partiel**

Ce que je crois pouvoir faire: comprendre la situation de la copropriete, voir les sujets urgents, aller vers les actions, les pieces manquantes, les demandes syndic, les chantiers et les comptes.

Ce que j'attends en cliquant:

- `A faire maintenant` ou `Voir toutes les actions`: ouvrir le registre des actions.
- `3 Actions en retard`: voir uniquement les actions prioritaires.
- `Pieces manquantes`: aller vers la liste des preuves ou documents attendus.
- `Demandes syndic`: preparer ou suivre les relances.

Ce qui marche: les cartes principales menent bien vers des routes live en 200.

Ce qui me bloque comme novice:

- Le premier ecran insiste beaucoup sur le contexte technique local (`role`, `sync`, `coffre`) avant de me dire quoi faire concrètement.
- Plusieurs compteurs a 0 restent cliquables et donnent l'impression qu'il y a quelque chose a traiter.
- `Prochaine action: declarer le cache local...` me semble etre une tache d'administrateur, pas une tache CS novice.
- Le bouton global `Nouvelle demande` est visuellement coupe dans les captures.

Corrections attendues:

- Mettre l'action humaine prioritaire en haut: `3 actions en retard - preparer une relance`.
- Reduire les alertes techniques dans un bandeau `Configuration locale a terminer`.
- Pour les compteurs a 0, afficher un etat vide non ambigu: `Rien a faire ici pour l'instant`.
- Garantir que le CTA global reste visible a 1000 px de large.

## Route `/actions`

Verdict: **GO partiel**

Ce que je crois pouvoir faire: consulter le registre decisions-actions-preuves, chercher une action, filtrer par perimetre, exporter le registre, ouvrir une fiche, ajouter une preuve ou preparer une relance.

Ce que j'attends en cliquant:

- `Nouvelle action > Rattacher a une decision AG`: ouvrir un formulaire guide.
- `Action libre du conseil syndical`: ouvrir un formulaire simple.
- Les cartes `a verifier`, `a arbitrer`, etc.: filtrer la liste.
- Une fiche `Piece documentaire`: ouvrir le detail de l'action.
- `Exporter CSV/Markdown`: telecharger le registre filtre.

Ce qui marche: les filtres, la recherche et les exports registre CSV/Markdown repondent. Les fiches action sont accessibles.

Ce qui me bloque:

- Les deux choix de `Nouvelle action` ne font pas apparaitre de formulaire; je reviens au meme registre. Pour moi, le bouton ne marche pas.
- La page est tres dense: decisions, preuves, pieces, relances, historique, exports et filtres sont visibles en meme temps.
- Beaucoup de libelles generiques `Piece documentaire` se repetent; je ne sais pas distinguer les sujets.
- Les actions `Mettre a jour l'avancement`, `Ajouter une preuve`, `Ajouter une piece liee` semblent etre des liens de mode, mais je ne vois pas toujours un vrai formulaire ensuite.

Corrections attendues:

- Afficher un formulaire reel ou un panneau guide apres `Nouvelle action`.
- Donner un titre humain unique a chaque action, pas seulement `Piece documentaire`.
- Masquer les zones secondaires tant qu'une fiche n'est pas selectionnee.
- Ajouter une phrase de resultat apres chaque filtre: `3 actions affichees`.

## Route `/comptes`

Verdict: **GO partiel**

Ce que je crois pouvoir faire: verifier les factures et pieces avant AG, filtrer par exercice/statut/fournisseur, voir les questions au syndic, exporter un rapport.

Ce que j'attends en cliquant:

- `Exporter le rapport`: obtenir un fichier ou une page clairement exportable.
- Les tuiles `P1`, `P2`, `Pieces manquantes`: filtrer les controles.
- `Questions au syndic`: ouvrir les relances liees aux comptes.
- `Filtrer`: appliquer les criteres saisis.

Ce qui marche: les tuiles et filtres repondent, la recherche fournisseur charge une page filtree, les liens vers actions/pieces fonctionnent.

Ce qui me bloque:

- `Total charges: A calculer` est anxiogene: je ne sais pas si je dois calculer, importer ou attendre.
- `Exporter le rapport` renvoie une page HTML, pas un telechargement evident. Le libelle promet plus qu'il ne livre.
- Les compteurs sont tous a 0 sauf une facture conforme visible plus bas; la synthese ne m'aide pas a savoir si les comptes sont vraiment prets.
- Les termes `P1`, `P2`, `rapprochement`, `preuve rattachee` ne sont pas toujours traduits en prochaine action.

Corrections attendues:

- Remplacer `A calculer` par une instruction: `Importer les lignes comptables` ou `Aucune donnee chargee`.
- Renommer `Exporter le rapport` en `Voir l'apercu du rapport` si ce n'est pas un fichier.
- Afficher un statut global novice: `Comptes prets / incomplets / a verifier`.
- Lier chaque anomalie ou absence de donnees a une action precise.

## Route `/chantiers`

Verdict: **GO partiel**

Ce que je crois pouvoir faire: consulter la memoire de copropriete, filtrer les evenements, exporter la passation, ajouter un evenement, rattacher un document.

Ce que j'attends en cliquant:

- `Ajouter un evenement`: ouvrir une saisie courte.
- `Rattacher un document`: aller vers l'ajout/depot avec l'intention memoire.
- `Passation JSON/Texte`: telecharger un export.
- Les filtres categories/statuts/preuves: reduire la timeline.

Ce qui marche: la recherche, les filtres, les exports passation et le formulaire `Ajouter un evenement` sont presents. La saisie indique qu'elle prepare une fiche sans ajouter automatiquement.

Ce qui me bloque:

- Le menu dit `Chantiers`, mais la page s'appelle `Memoire de copropriete`; je ne sais pas si je suis dans les travaux, la passation ou l'historique.
- Beaucoup d'elements ont `Date a confirmer` ou `A verifier`; je ne sais pas par lequel commencer.
- `Ajouter un evenement` est dans un menu deroulant; l'action est moins directe que prevu.
- `Rattacher un document` mene a `/documents/ajouter`, qui n'est pas actionnable.

Corrections attendues:

- Harmoniser le nom de navigation: `Memoire / Chantiers` ou separer les deux.
- Mettre en avant une liste `A faire maintenant pour la passation`.
- Si `Ajouter un evenement` est disponible, en faire un CTA primaire visible.
- Corriger la route d'ajout de document ou envoyer directement vers `/depot?intent=memory`.

## Route `/actions?priority=P1`

Verdict: **GO partiel**

Ce que je crois pouvoir faire: voir les actions en retard, preparer une relance, rattacher une piece, exporter une liste de travail.

Ce que j'attends en cliquant:

- `Exporter une liste de travail apres apercu`: obtenir l'export des actions ouvertes.
- `Preparer une relance`: aller vers les brouillons syndic.
- `Rattacher une piece`: ouvrir les pieces attendues pour cette action.
- `Voir dans la memoire`: consulter le document ou l'historique lie.

Ce qui marche: les liens de relance, rattachement et memoire repondent en 200.

Ce qui me bloque:

- Le CTA d'export principal repond 404 avec `Export introuvable`.
- La page parle d'`apercu`, mais je ne vois pas clairement l'etape d'aperçu avant export.
- Les trois retards sont surtout des `Piece documentaire`; je ne comprends pas immediatement la difference entre eux.
- Les tuiles `Sans preuve 0` et `Relance syndic prete 0` restent cliquables malgre le zero.

Corrections attendues:

- Brancher ou retirer l'export `/exports/passation?scope=open-actions`.
- Afficher une liste de travail lisible avant export, avec titre humain, responsable, echeance, prochaine action.
- Ne pas rendre les compteurs a 0 aussi prioritaires visuellement.
- Differencier les actions par leur piece/source ou par la question a resoudre.

## Route `/actions?scope=syndic&tab=relance`

Verdict: **GO partiel**

Ce que je crois pouvoir faire: preparer les messages au syndic, copier un brouillon, rattacher la reponse du syndic, suivre ce qui est envoye hors CoproScope.

Ce que j'attends en cliquant:

- `Ouvrir le brouillon`: afficher le texte du brouillon choisi.
- `Copier le brouillon`: copier le texte et me confirmer que c'est fait.
- `Marquer comme envoye hors CoproScope`: demander date, canal, destinataire ou au moins une confirmation.
- `Rattacher la reponse du syndic`: ouvrir le depot avec le contexte de l'action.

Ce qui marche: la page relance affiche des brouillons et un bouton de copie; les liens vers depot et pieces repondent.

Ce qui me bloque:

- `Ouvrir le brouillon` mene a une fiche action ou le brouillon n'est plus visible. Je perds le texte que je voulais ouvrir.
- `Copier le brouillon` ne donne aucun feedback visible; je ne sais pas si le presse-papier a fonctionne.
- La page dit que marquer comme envoye exige une date et un canal hors outil, mais le lien `Marquer comme envoye hors CoproScope` ne les demande pas.
- Les brouillons se ressemblent beaucoup: meme type `Piece documentaire`, meme derniere trace `Aucune demande tracee`.

Corrections attendues:

- Faire de `Ouvrir le brouillon` une vraie vue brouillon avec textarea, contexte, piece attendue et actions.
- Ajouter un toast ou message `Brouillon copie`.
- Remplacer le lien `Marquer comme envoye` par un mini-formulaire date + canal + note.
- Donner un objet de relance humain: `Demander le contrat X`, `Demander la facture Y`, etc.

## Route `/pieces?proof=missing`

Verdict: **GO partiel**

Ce que je crois pouvoir faire: voir les pieces manquantes, demander au syndic, consulter des pieces candidates, ajouter une preuve depuis le depot.

Ce que j'attends en cliquant:

- `Demander au syndic`: preparer une relance.
- `Voir les pieces candidates`: passer en revue les fichiers possibles.
- `Ajouter depuis le depot`: deposer ou choisir un fichier.
- Les groupes `AG`, `Contrats`, `Travaux`, etc.: filtrer les manques.

Ce qui marche: les liens principaux repondent et menent vers relance, candidates ou depot.

Ce qui me bloque:

- La page annonce `0 pieces`, mais affiche encore plusieurs actions `Demander au syndic` ou `Preparer la demande syndic`.
- `Completude passation 0` est ambigu: 0 manquant, 0 rapproche, ou 0 complet?
- S'il n'y a rien a demander, je ne sais pas pourquoi cette page est signalee dans le menu.

Corrections attendues:

- Si la liste est vide, afficher un vrai etat vide: `Aucune piece manquante detectee`.
- Masquer ou de-prioriser `Demander au syndic` quand il n'y a aucun manque selectionnable.
- Clarifier les compteurs: `0 piece manquante`, `0 candidate`, `5 actions liees`.

## Route `/demandes`

Verdict: **NO-GO**

Ce que je crois pouvoir faire: creer ou suivre des demandes coproprietaires/syndic, rattacher une preuve, inscrire une suite.

Ce que j'attends en cliquant:

- `+ Nouvelle demande`: ouvrir un formulaire de creation.
- Les cartes `Comprendre la demande`, `Garder la preuve`, `Inscrire la suite`: soit m'expliquer le flux, soit ouvrir l'etape correspondante.
- Un registre: permettre d'ouvrir, filtrer ou creer une demande.

Ce qui marche: la page charge et donne de bons reperes pedagogiques.

Ce qui me bloque:

- Il n'y a aucun bouton, lien ou formulaire dans le contenu principal.
- Le CTA global `+ Nouvelle demande` renvoie a la meme page, sans creation.
- Les sections indiquent 0 canal, 0 public, 0 registre; je ne peux rien faire pour corriger.
- Le H1 technique reste `Cockpit Conseil Syndical`, ce qui affaiblit l'orientation.

Corrections attendues:

- Ajouter un formulaire `Nouvelle demande` minimal: sujet, canal, preuve/reference, diffusion, prochaine action.
- Faire du CTA global un vrai point d'entree vers ce formulaire.
- Si le module n'est pas branche, afficher explicitement `Module en lecture seule` et proposer une action disponible.
- Donner un exemple de demande pre-rempli ou un brouillon guidant le novice.

## Route `/pilotage`

Verdict: **GO partiel**

Ce que je crois pouvoir faire: surveiller des indicateurs et identifier ce qui doit etre verifie avant decision.

Ce que j'attends en cliquant:

- Une carte KPI: ouvrir le detail de la source ou creer une action de verification.
- Un domaine suivi: filtrer les indicateurs du domaine.
- Une alerte `a verifier`: me dire quelle preuve manque.

Ce qui marche: les cartes KPI sont lisibles et donnent domaine, periode, valeur, source et prochaine action textuelle.

Ce qui me bloque:

- Il n'y a aucun lien ou bouton dans le contenu principal.
- Les `prochaines actions` sont du texte, pas des actions.
- Les indicateurs a 0% peuvent etre bons ou mauvais; sans seuil, je ne sais pas interpreter.
- Le H1 reste `Cockpit Conseil Syndical` au lieu de `Pilotage`.

Corrections attendues:

- Ajouter `Creer une action de verification` sur chaque KPI a verifier.
- Ajouter `Voir la source` quand une source est citee.
- Afficher le seuil ou la lecture novice: `OK`, `a completer`, `risque`.
- Mettre le titre route en H1 visible.

## Route `/documents/ajouter`

Verdict: **NO-GO**

Ce que je crois pouvoir faire: ajouter un document, verifier sa confidentialite, le rattacher a une action/preuve.

Ce que j'attends en cliquant:

- Un bouton `Choisir un fichier` ou `Deposer un document`.
- Un parcours etape par etape: fichier, type, confidentialite, rattachement.
- Eventuellement un lien vers le depot local deja pret.

Ce qui marche: la page explique bien les notions de confidentialite, rattachement et statuts runtime.

Ce qui me bloque:

- Aucun bouton, aucun champ fichier, aucun formulaire.
- La page s'appelle `Ajout de document`, mais je ne peux pas ajouter.
- Le contenu dit `Aucune route web n'est declaree dans cette couche`, phrase technique qui confirme que je suis bloque.
- Les documents a ajouter sont affiches comme une liste/preparation, pas comme un flux utilisateur.

Corrections attendues:

- Ajouter un vrai champ fichier ou un CTA primaire vers `/depot?intent=document`.
- Si l'ajout se fait seulement via `/depot`, renommer la page en `Preparer le rattachement` et mettre le depot en premier.
- Supprimer les phrases techniques non actionnables du parcours novice.
- Afficher `Etape 1 sur 4` avec l'action concrete attendue.

## Route `/ag-contentieux`

Verdict: **GO partiel**

Ce que je crois pouvoir faire: preparer l'AG, verifier les pieces de convocation, suivre les dossiers contentieux et transmettre une passation limitee.

Ce que j'attends en cliquant:

- Les cartes `Question AG`, `Piece de convocation`, `Dossier contentieux`, `Pack passation`: aller a la section correspondante.
- Une ligne de question ou piece: ouvrir le detail, rattacher une preuve ou creer une action.
- `Pack passation`: preparer ou exporter un pack.

Ce qui marche: les cartes ancrent bien vers des sections et la page reste prudente sur les dossiers sensibles.

Ce qui me bloque:

- Les cartes ne sont que des ancres dans la page; je ne peux pas creer, corriger, rattacher ou exporter depuis les sections.
- Le menu annonce `AG contentieux novice 0`, alors que la page affiche 1 question AG, 1 piece de convocation et 3 echeances.
- Le H1 visible reste `Cockpit Conseil Syndical`, puis le vrai titre arrive dans le contenu.
- Le `Pack passation` est un brouillon, mais je ne vois pas le bouton pour le generer.

Corrections attendues:

- Ajouter des actions par section: `Formuler la question`, `Verifier la piece`, `Ajouter une preuve`, `Preparer le pack`.
- Aligner le compteur de menu avec les objets reels de la page.
- Afficher `AG, contentieux, passation` comme H1 de route.
- Donner une checklist finale exportable avec statut `pret / incomplet`.

## Route `/depot`

Verdict: **GO partiel**

Ce que je crois pouvoir faire: deposer des fichiers localement, lancer le traitement local, recuperer des exports, voir l'historique de depot.

Ce que j'attends en cliquant:

- `Choisir un fichier` + `Deposer`: envoyer un fichier local dans l'instance.
- `Actions CSV` et `Actions Markdown`: telecharger les exports.
- `Pack local prive`: telecharger un zip local prive.

Ce qui marche: le formulaire de depot existe. `Pack local prive` repond en 200 avec un zip.

Ce qui me bloque:

- `Actions CSV` et `Actions Markdown` n'incluent pas `token=local-secret`; ils repondent 403 `Jeton local requis`.
- Le depot ne precise pas les formats acceptes ni la taille limite avant selection de fichier.
- `Depot selectionne: aucun` et `0 depots traces` ne me disent pas quoi faire apres un depot.
- Je dois venir ici pour ajouter un document, mais la page `/documents/ajouter` ne m'y envoie pas.

Corrections attendues:

- Ajouter le token aux liens d'export ou passer par une route d'export autorisee.
- Afficher les formats acceptes et un avertissement confidentialite juste au-dessus du champ fichier.
- Apres depot, afficher une etape suivante claire: `Verifier classification`, `Rattacher a une action`, `Voir pieces candidates`.
- Relier explicitement `/documents/ajouter` et `/depot`.

## Verdicts par route

| Route | Verdict |
| --- | --- |
| `/` | GO partiel |
| `/actions` | GO partiel |
| `/comptes` | GO partiel |
| `/chantiers` | GO partiel |
| `/actions?priority=P1` | GO partiel |
| `/actions?scope=syndic&tab=relance` | GO partiel |
| `/pieces?proof=missing` | GO partiel |
| `/demandes` | NO-GO |
| `/pilotage` | GO partiel |
| `/documents/ajouter` | NO-GO |
| `/ag-contentieux` | GO partiel |
| `/depot` | GO partiel |
