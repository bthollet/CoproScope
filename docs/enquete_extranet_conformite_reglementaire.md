# Enquete et cadrage - inspection de l'extranet par plugin navigateur

Date: 2026-09-03.
Rattachement: `RM-2026-0047`.
Chantier: `CH-20260903-090000-RM-2026-0047-extranet-conformite`.
Statut du gate: `NO-GO DEV` en l'etat, voir la section finale.
Diffusion: interne projet.

Ce document applique le bloc d'enquete obligatoire de
`docs/methode_developpement_branches.md`. Il ne contient aucun code, et aucun
code applicatif ne doit etre ecrit avant la levee des conditions du gate.

## 1. Probleme utilisateur

Un conseiller syndical dispose d'un acces a l'espace en ligne securise impose
au syndic. Cet espace a trois defauts structurels du point de vue du controle:

1. **Il est sans memoire pour celui qui le consulte.** Un document peut etre
   ajoute, retire ou remplace sans laisser de trace visible. Personne dans la
   copropriete ne peut aujourd'hui affirmer "cette piece n'etait pas en ligne
   le 15 mars".
2. **Il est entierement sous le controle de l'observe.** La source qu'on
   inspecte est produite et modifiable par celui dont on controle l'action.
3. **Il ne se compare pas a la norme.** Rien n'indique a l'utilisateur quelles
   rubriques sont legalement obligatoires, ni lesquelles manquent.

Le besoin est donc: **confronter, de facon repetee et datee, ce que l'extranet
sert a ce que la reglementation impose de servir**, et transformer chaque ecart
en demande ecrite datee.

## 2. Ce qui rend ce controle possible, et rare

Pour les documents dont la loi impose la mise a disposition sur l'espace en
ligne, **l'absence sur l'extranet est le manquement lui-meme**, independamment
de l'existence du document ailleurs.

On sort ici du piege habituel "absence de preuve n'est pas preuve d'absence":
l'observable mesure est l'objet meme de l'obligation. C'est le seul endroit du
dossier copropriete ou l'observation directe suffit a qualifier, sous reserve
de la regle de couverture d'exploration.

## 3. Perimetre V1

Dans le perimetre:

- observation **passive** de ce que l'utilisateur ouvre lui-meme, avec ses
  propres droits, sur un extranet ou il est authentifie;
- confrontation au referentiel de conformite
  (`docs/referentiel_conformite_extranet_v0.md`);
- production d'un tableau de conformite avec, pour chaque ecart, un projet de
  demande ecrite;
- versement des observations dans le coffre local, avec provenance, empreinte
  et horodatage;
- un seul adaptateur d'editeur, derriere une interface concue pour en accueillir
  d'autres.

Hors perimetre V1, explicitement:

- **toute action emise vers l'extranet**: pas d'envoi de message, pas de vote,
  pas de clic automatise, pas de navigation programmee. Lecture seule stricte;
- toute automatisation de session ou pilotage de navigateur sans l'utilisateur;
- tout stockage ou transit distant: rien ne sort du poste;
- toute conclusion juridique automatique;
- tout partage de sortie sans passage par PrivacyOps et BiffageOps;
- le journal de bord des changements, les controles arithmetiques, la surcouche
  pedagogique et la preparation d'assemblee: retenus au produit, mais apres V1.

Arbitrage de doctrine a acter: `docs/strategie_coproscope_gestion_copro.md`
pose que CoproScope ne doit pas courir apres les extranets. Ce chantier ne
contredit pas cette decision, il s'y adosse. CoproScope ne devient pas un
extranet concurrent; il devient un instrument de mesure braque sur l'extranet.
La formulation retenue est: **instrument de mesure, pas extranet concurrent**.

## 4. Blueprint de service

```text
utilisateur authentifie ouvre une page de son extranet
    -> le plugin observe passivement ce qui s'affiche
        -> normalisation par l'adaptateur de l'editeur
            -> observation datee, empreintee, versee au coffre local
                -> confrontation au referentiel de conformite
                    -> verdict par rubrique, dont INDETERMINE par defaut
                        -> validation humaine obligatoire
                            -> tableau de conformite + projets de demande
```

Trois frontieres a ne jamais franchir dans ce flux:

- l'adaptateur normalise, il ne qualifie pas;
- la qualification propose, elle ne conclut pas;
- la conclusion est humaine, et elle est tracee comme telle.

## 5. Parcours-evenements

| Evenement | Emetteur | Charge utile essentielle |
|---|---|---|
| `extranet.page_observee` | plugin | horodatage, editeur, college, chemin, empreinte de la reponse |
| `extranet.rubrique_reperee` | adaptateur | identifiant de rubrique, libelle observe, date declaree, empreinte |
| `extranet.index_couvert` | adaptateur | categorie enumeree, nombre d'entrees vues |
| `extranet.adaptateur_en_echec` | adaptateur | version d'adaptateur, motif, capture brute conservee |
| `conformite.qualification_proposee` | referentiel | rubrique, verdict, criteres appliques, base legale et son statut |
| `conformite.qualification_validee` | humain | validateur, date, motif de confirmation ou d'infirmation |
| `conformite.demande_preparee` | SyndicOps | rubrique, texte de la demande, date d'envoi prevue |

`extranet.index_couvert` est l'evenement qui autorise un verdict `ABSENT`.
Sans lui, toute rubrique non vue reste `NON_EXPLORE`, donc `INDETERMINE`.

## 6. Contrat de donnees

Deux tables strictement separees. La separation entre observation et
interpretation est une exigence de methode, pas une commodite: une observation
doit rester relisible independamment du referentiel qui l'a qualifiee, et une
qualification doit pouvoir etre rejouee quand le referentiel change.

Table `extranet_observations`, append-only:

```text
observation_id, campagne_id, horodatage_observation, editeur_id,
adaptateur_version, college, rubrique_id, chemin_observe,
statut_observe [PRESENT|ABSENT|INACCESSIBLE|NON_EXPLORE],
libelle_observe, date_document_declaree, empreinte_sha256, taille_octets,
index_couvert [oui|non], capture_ref, notes
```

Table `conformite_qualifications`, derivee et rejouable:

```text
qualification_id, observation_id, rubrique_id, referentiel_version,
base_legale_ref, base_legale_statut [VERIFIE|SOURCE_A_VERIFIER],
criteres_appliques, verdict [CONFORME|NON_CONFORME|INDETERMINE|SANS_OBJET],
motif, preuve_ref, validateur_humain, date_validation
```

Interdits de contrat:

- aucun identifiant de session, jeton, cookie ou mot de passe n'entre dans ces
  tables, sous aucune forme;
- aucun nom de coproprietaire tiers dans `libelle_observe` ni dans `notes`;
- aucun chemin local de la machine dans les sorties diffusables;
- `verdict` ne peut valoir `NON_CONFORME` si `base_legale_statut` vaut
  `SOURCE_A_VERIFIER`, ou si `index_couvert` vaut `non`.

## 7. Options techniques et recommandation

| Option | Description | Verdict |
|---|---|---|
| A. Extension de navigateur passive | Enregistre ce que l'utilisateur consulte lui-meme; n'emet aucune requete. | Retenue pour la V1. |
| B. Export manuel du journal reseau | Export du journal des echanges d'une session, analyse hors ligne par CoproScope. | Retenue comme **enquete prealable**, avant d'ecrire l'extension. |
| C. Automate de navigation | Parcours programme avec les identifiants de l'utilisateur. | Ecartee: expose contractuellement, retire l'utilisateur des commandes. |

Sequence recommandee: **B d'abord, puis A**. L'option B est gratuite en risque
et produit la cartographie des donnees reelles de l'editeur. Ecrire
l'adaptateur avant d'avoir vu cette structure reviendrait a definir un
protocole d'echantillonnage sans avoir vu le terrain.

Notes de mise en oeuvre pour A:

- viser les **reponses structurees** que l'application recupere de son serveur,
  bien plus stables que l'apparence des pages; lire la page affichee est un
  secours, pas la cible;
- transmission vers CoproScope en local uniquement: point d'entree sur
  `127.0.0.1` avec jeton, ou messagerie native entre navigateur et application;
- distribution **hors magasin d'extensions**, pour rester compatible avec
  `docs/catalogue_plugins_officiels_v1.md`: pas de mise a jour silencieuse,
  code local hors vault, permissions declarees, activation signee;
- permissions limitees aux domaines d'editeurs explicitement declares.

## 8. Risques

| Risque | Nature | Traitement V1 |
|---|---|---|
| Conditions d'utilisation de l'extranet | Contractuel | La version passive n'emet aucune requete et n'accede qu'a un affichage auquel l'utilisateur a droit. Position defendable, a faire valider, et qui s'effondre si on passe a l'option C. |
| Donnees personnelles de tiers | Reglementaire | La balance nomme les coproprietaires debiteurs. Regle dure: aucune sortie sans PrivacyOps et BiffageOps. L'adaptateur s'arrete plutot que de capturer une fuite de cloisonnement. |
| Faux manquements | Produit, et le plus grave | Regle de couverture d'exploration, verdict `INDETERMINE` par defaut, blocage sur base legale non verifiee. |
| Rupture d'adaptateur | Maintenance | Mode degrade explicite: "je n'ai pas su lire cette page, voici la capture brute". Jamais `ABSENT`. Tests de non-regression sur captures figees anonymisees. |
| Securite du plugin | Securite | Permissions minimales, aucune collecte d'identifiants, code lisible et verifiable, pas de code telecharge. |
| Surestimation de la force probante | Produit | Une capture auto-produite n'est pas un constat de commissaire de justice. Etiquetage obligatoire. Voir section 9. |

## 9. Ce que le dispositif prouve, et ce qu'il ne prouve pas

Il ne produit pas de preuve opposable. Une capture auto-produite reste une
preuve a soi-meme, et un juge n'est pas tenu de la retenir.

Ses trois usages reels, et les seuls a promettre:

1. **fonder une demande ecrite precise et datee**, ce qui declenche une reponse
   la ou une remarque generale n'en declenche aucune;
2. **declencher un constat officiel au bon moment**: le dispositif dit quand et
   sur quelle page, ce qui evite de payer un constat au hasard;
3. **construire une chronologie lisible** pour l'assemblee ou la passation.

Cette limite doit apparaitre dans l'interface, conformement a la doctrine du
depot: une piece dit ce qu'elle prouve et ce qu'elle ne prouve pas.

## 10. Criteres d'acceptation V1

1. Aucune rubrique n'est qualifiee `NON_CONFORME` sans observation de l'index
   correspondant, empreinte, horodatage, et base legale au statut `VERIFIE`.
2. Une rubrique non exploree est `NON_EXPLORE`, jamais `ABSENT`.
3. Un adaptateur en echec produit `INACCESSIBLE` et conserve la capture brute;
   il ne produit jamais un manquement.
4. Chaque ecart produit un projet de demande ecrite, date et reference a la
   rubrique et a sa base legale.
5. Aucune sortie ne contient de nom de tiers, d'identifiant de session, de
   jeton ni de chemin local.
6. Le plugin n'emet aucune requete vers l'extranet.
7. Le referentiel est versionne et les qualifications sont rejouables apres
   mise a jour du referentiel.

## 11. Tests attendus

- jeu de captures figees et anonymisees par editeur, avec sortie de reference;
- test de rupture d'adaptateur: page modifiee, attendu `INACCESSIBLE`;
- test de couverture: rubrique non exploree, attendu `INDETERMINE`;
- test de blocage juridique: base legale `SOURCE_A_VERIFIER`, attendu
  `INDETERMINE` meme si l'observation est nette;
- test de rejouabilite: changement de version de referentiel, qualifications
  recalculees sans reobservation;
- test anti-fuite sur toutes les sorties;
- test de lecture seule: aucune requete sortante emise par le plugin.

## 12. Roles d'equipe attendus

Conformement a `docs/strategie_equipes_multi_agents.md`, equipe-type pressentie
`RECHERCHE_METIER` pour la passe de verification juridique, puis
`BACKEND_DOMAINE` pour l'adaptateur et le moteur de qualification.

Roles a faire rendre avant tout statut `PRET_A_INTEGRER`: expert metier
juridique copropriete, QA privacy, novice usage conseil syndical, dev backend.

## 13. Gate GO/NO-GO

Statut: **NO-GO DEV**.

Conditions de levee, dans l'ordre:

1. **Verification juridique du referentiel** avec la skill `piste-api` depuis
   le poste de Brice. Tant qu'une ligne reste `SOURCE_A_VERIFIER`, elle ne peut
   produire aucun verdict. C'est la condition bloquante principale: la valeur
   entiere de la V1 repose sur l'exactitude de la liste minimale.
2. **Enquete de structure** sur l'editeur cible par l'option B, pour cartographier
   les donnees reellement servies. Sans elle, l'adaptateur serait concu a l'aveugle.
3. **Confirmation de la ligne rouge lecture seule** par Brice.
4. **Arbitrage de doctrine** sur "instrument de mesure, pas extranet concurrent".
5. Rendus traces des roles d'equipe de la section 12.

Tant que 1 et 2 ne sont pas faites, le chantier reste documentaire.
