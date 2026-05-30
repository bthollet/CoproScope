# Recherche UX/UI WorksOps travaux

Date de lancement: 2026-05-24 03:32 +02:00.
Roadmap: `RM-2026-0032`.
Chantier: `CH-20260524-033252-RM-2026-0032-travaux-ux-ui`.
Conversation coordination: `CONV-2026-1331`.
Mode: equipe UX/UI recherche visuelle sans dev.

## BOT-START

BOT-START - Orchestrateur UX/UI - 2026-05-24 03:32 +02:00

Roadmap: `RM-2026-0032`
Chantier: `CH-20260524-033252-RM-2026-0032-travaux-ux-ui`
Conversation: `CONV-2026-1331`
Role: Orchestrateur UX/UI
Mission: lancer et coordonner une recherche UX/UI sans dev sur la partie travaux / WorksOps.
Ownership modifiable: `docs/recherche_ux_ui_2026-05-24_travaux.md`, `docs/assets/ux-ui-recherche-2026-05-24-travaux/`, lignes de presence et gouvernail liees a `RM-2026-0032`.
Fichiers a eviter: code applicatif, routes, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, `RM-2026-0017` bloque.
Passerelle/registre de trace: cette mission et `docs/presence_agents.md`.
Dernier point lu: `AGENTS.md`, `docs/orchestration_agents.md`, `docs/protocole_equipe_ux_ui_recherche.md`, `docs/protocole_roadmap_presence_agents.md`, gouvernail, presence, point live historique et coordination interconversations lus le 2026-05-24 03:32 +02:00.
Tests/preuves attendus: livrable de recherche, directions UI/images candidates, retours testeur metier et novice; aucun test applicatif car aucun code.
Risque de collision: plusieurs recherches UX/UI sont actives; la mission travaux reste separee par `RM-2026-0032`, son livrable et son dossier d'assets.
Lease ownership: 2026-05-25 03:32 +02:00.
Prochaine action: lancer les cinq roles de recherche en lecture/documentation et consolider leurs sorties.

## Objectif

Definir la direction UX/UI d'un dossier travaux minimal mais probatoire pour un conseil syndical:

- voir en une page ou en est chaque operation;
- comprendre quelle preuve manque;
- relier decision, devis, fournisseur, assurance, facture, reception, garantie, ecarts et preuves;
- distinguer les faits constates, les alertes et les prochaines demandes au syndic ou fournisseur;
- eviter toute confusion avec ComptaScope, DecisionOps et PrivacyOps tant que l'integration n'est pas arbitree.

## Roles actifs

| Role | Conversation | Statut | Sortie attendue |
|---|---|---|---|
| Orchestrateur UX/UI | `CONV-2026-1331` | `EN_COURS` | Synthese, arbitrages, images retenues et cloture. |
| Chercheur utilisateur | `CONV-2026-1332` / Pascal `019e57c1-f17a-7cb3-a194-d071e22d1b92` | `EN_COURS` | Profils, besoins, irritants, scenarios et criteres de reussite. |
| Architecte UX | `CONV-2026-1333` / Erdos `019e57c2-72b5-7210-991b-3bec25c00e24` | `EN_COURS` | Parcours, hierarchie d'information, etats, wireflows. |
| Designer UI / generateur visuel | `CONV-2026-1334` / Epicurus `019e57c2-731c-7660-9493-a1258b54b108` | `EN_COURS` | Directions UI, prompts, images candidates et principes d'interaction. |
| Testeur metier expert | `CONV-2026-1335` / Meitner `019e57c2-7398-7e43-be99-391fe4d63393` | `EN_COURS` | Challenge travaux, reception, garanties, assurances, preuves, cas limites. |
| Testeur accessibilite / novice | `CONV-2026-1336` / Ramanujan `019e57c2-741d-7982-8d62-2717e286ab52` | `EN_COURS` | Lisibilite, charge cognitive, comprehension immediate, risques de blocage. |

## Sources de cadrage

- `docs/agent_briefs/lot-f-worksops.md`
- `docs/fonctions_cibles.md`
- `docs/roadmap_produit_fini_visuels_enquete.md`
- `docs/etude_utilisateurs.md`
- `docs/etude_utilisateurs_syndics_benevoles.md`
- `server/src/coproscope/web/viewmodels/_dashboard.py` en lecture seule pour le statut WorksOps actuel

## Contraintes

- Aucun code produit dans cette mission.
- Aucune instance privee lue ou modifiee par les roles UX/UI.
- Les images candidates ne doivent afficher ni chemin local, ni nom de copro reelle, ni donnee personnelle.
- Toute suite dev devra etre ouverte comme chantier separe, avec owner code unique.

## Questions initiales

1. Quel est le premier ecran WorksOps utile: portefeuille d'operations, fiche operation, ou timeline decision-preuve?
2. Quelle preuve manquante doit apparaitre en premier pour un membre de conseil syndical novice?
3. Comment relier devis, factures, AG et reception sans creer une matrice trop dense?
4. Quels statuts travaux sont comprehensibles sans jargon: vote, devis choisi, commande, en cours, reception, reserves, garantie, clos?
5. Quelles alertes doivent etre bloquees par test metier avant d'etre visibles comme recommandations?

## Images retenues

| Image | Statut | Intention | Decision |
|---|---|---|---|
| `docs/assets/ux-ui-recherche-2026-05-24-travaux/01-console-travaux-portefeuille-fiche.svg` | retenue | Blueprint de l'ecran principal `Travaux`: portefeuille des operations, preuve bloquante, prochaine action et fiche probatoire laterale. | Direction retenue pour une future commande UX/dev separee. |

## Profils utilisateurs cibles

- Membre de conseil syndical batisseur: suit devis, vote, chantier, reception et reserves.
- Syndic benevole: doit prouver ses diligences sans promettre une automatisation ou une decision juridique.
- Referent commission travaux: contribue sur un perimetre borne, sans acces a tout le coffre.
- Coproprietaire novice: veut comprendre pourquoi on paie, ou en est le chantier et ce qui est prouve.
- Conseil syndical en passation: doit retrouver garanties, reserves, decisions et pieces sans fouiller partout.

## Parcours principal retenu

Le premier ecran n'est pas une fiche isolee ni une timeline generale. C'est un portefeuille d'operations travaux.

Wireflow retenu:

`Cockpit CS` -> carte `Travaux a suivre` -> page `Travaux - portefeuille des operations` -> filtre par defaut `Preuves bloquantes` -> selection d'une operation -> fiche probatoire laterale -> action primaire prudente -> retour a la fiche -> export de synthese seulement apres arbitrage diffusion.

La page doit repondre en premier a une question simple:

```text
Pour chaque operation, ou en est-on et quelle preuve bloque la suite ?
```

## Architecture UX retenue

Premier niveau:

- bandeau resume: operations ouvertes, preuves bloquantes, receptions a prouver, reserves ouvertes, garanties a surveiller;
- liste centrale des operations, triee par preuve manquante la plus bloquante;
- une ligne par operation: nom, phase, fournisseur, montant vote/engage/facture, preuve manquante, prochaine action, echeance, diffusion;
- panneau de detail lateral ou dessous: chronologie, preuves validees/candidates/manquantes, documents lies, actions syndic, factures, reserves, garanties.

Second niveau:

- fiche operation probatoire;
- frise courte: `Vote` -> `Devis choisi` -> `Commande` -> `En cours` -> `Reception` -> `Reserves` -> `Garantie` -> `Clos`;
- chaque etape porte un etat: `preuve validee`, `preuve candidate`, `preuve manquante`, `non applicable`;
- action primaire contextuelle: `Preparer une demande au syndic`, `Rattacher une piece`, `Verifier la preuve candidate`, `Noter une reserve`.

## Etats d'ecran

- `A qualifier`: documents presents, operation pas encore fiable.
- `Vote a retrouver`: devis ou facture trouves, decision absente.
- `Devis a choisir`: plusieurs devis, decision fournisseur manquante.
- `Commande a confirmer`: fournisseur choisi, commande ou assurance manquante.
- `Travaux en cours`: suivi chantier, factures intermediaires, ecarts.
- `Reception a prouver`: chantier annonce termine, PV ou preuve de reception absente.
- `Reserves ouvertes`: reception faite mais reserves non levees.
- `Garantie a surveiller`: operation close au sens chantier, garantie active.
- `Clos avec preuves`: decision, devis, facture, reception et garantie traces.
- `Diffusion bloquee`: synthese exportable seulement apres arbitrage confidentialite.

## Problemes UX/UI priorises

1. Ne pas afficher `WorksOps` comme nom utilisateur principal: utiliser `Travaux` et `Suivi des travaux`.
2. Eviter la matrice complete a neuf colonnes au premier niveau: elle devient illisible pour un novice.
3. Ne pas confondre `piece liee`, `preuve candidate` et `preuve validee`.
4. Ne pas clore une operation sur une facture seule: reception, reserves et garantie doivent rester visibles.
5. Ne pas promettre d'envoi automatique: preferer `Preparer une demande au syndic`.
6. Garder les montants utiles sans refaire ComptaScope: vote, engage, facture, paye, reste a financer.
7. Garder les garanties dans une file de surveillance apres cloture operationnelle.

## Recommandations classees par impact

P0 - Direction produit:

- Retenir la console `Travaux - portefeuille des operations` avec fiche laterale.
- Trier par preuve bloquante plutot que par date ou par montant.
- Afficher quatre informations au premier coup d'oeil: travaux, etat, preuve manquante, prochaine action.
- Interdire l'etat `Clos` sans preuve de reception, reserves levees ou justification explicite.

P1 - Vocabulaire:

- Imposer: `operation travaux`, `devis recu`, `devis retenu`, `commande signee`, `reception avec reserves`, `reserve a lever`, `preuve candidate`, `preuve validee`, `reste a financer`, `diffusion a arbitrer`.
- Eviter: `travaux OK`, `assurance OK`, `facture validee`, `devis choisi` seul, `reception faite` sans PV, `clos` sans preuve.

P1 - Interaction:

- CTA primaires: `Preparer une demande au syndic`, `Rattacher un devis`, `Rattacher la facture`, `Ajouter une photo de reception`, `Noter une reserve`, `Voir l'historique`.
- `Exporter la synthese travaux` reste bloque ou remplace par `Voir l'apercu` tant que la diffusion n'est pas arbitree.

P2 - Vues secondaires:

- Fiche operation probatoire pour les cas sensibles.
- Matrice jalons/preuves reservee a une vue expert ou a un test de densite, pas au premier ecran.

## Retours du Testeur metier expert

Verdict: GO pour continuer la recherche UX/UI, NO-GO pour toute suite dev tant que le modele metier travaux n'est pas verrouille.

Garde-fous metier:

- Une decision d'assemblee generale ne cloture rien seule: elle doit porter resolution, majorite, PV, notification, delai de contestation, montant autorise, financement, cle de repartition, mandat syndic et devis retenu ou non.
- `Devis choisi` ne vaut pas commande: distinguer devis recu, compare, retenu, ordre de service ou bon de commande signe, avenant.
- `Assurance OK` est interdit comme badge unique: distinguer responsabilite civile decennale, activites couvertes, validite a l'ouverture du chantier, dommages-ouvrage si applicable.
- Une facture peut etre acompte, situation, solde ou regularisation; elle ne prouve ni reception ni levee des reserves.
- La reception doit etre un evenement date avec PV, signataires, acceptation avec ou sans reserves, echeances de reprise et levee prouvee.
- Le budget doit separer vote, engage, facture, paye, reste a financer, appels de fonds, fonds travaux, subventions ou emprunt eventuels.

Sources officielles verifiees le 2026-05-24:

- Service-Public, assemblee generale des coproprietaires: https://www.service-public.gouv.fr/particuliers/vosdroits/N31341
- Service-Public, regles de vote en assemblee generale: https://www.service-public.fr/particuliers/vosdroits/F2137
- Service-Public, convocation AG et devis joints: https://www.service-public.gouv.fr/particuliers/vosdroits/F2615
- Legifrance, article 21 de la loi du 10 juillet 1965: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000039313574
- Service-Public Entreprendre, garantie decennale: https://entreprendre.service-public.gouv.fr/vosdroits/F2034

## Retours du Testeur accessibilite / novice

Verdict: GO conditionnel si le premier ecran reste lisible en 30 secondes; NO-GO si l'interface ressemble a un tableau expert ou si `WorksOps` devient le titre visible.

Libelles recommandes:

- Navigation: `Travaux`
- Titre: `Suivi des travaux`
- Sous-titre: `Voir l'etat, la preuve manquante et la prochaine demande`

Gates novice:

- Le novice doit pouvoir dire quel chantier est prioritaire, ce qui manque, qui relancer et ce que le bouton va faire.
- Les statuts ne doivent pas reposer sur la couleur seule.
- Les infobulles doivent rester accessibles sans souris.
- La version mobile doit empiler les cartes avec un CTA primaire visible.
- Les compteurs a zero ne doivent pas devenir des urgences cliquables.

## Decisions prises

- Direction retenue: `console travaux portefeuille + fiche probatoire`.
- Premiere route ou surface future a explorer: `Travaux`, distincte de `Chantiers` deja lie a memoire/passation.
- Image retenue: blueprint SVG `01-console-travaux-portefeuille-fiche.svg`.
- Toute suite dev doit etre un chantier separe avec modele metier verrouille avant template ou route.
- Aucun code n'a ete produit dans cette mission.

## Questions ouvertes

- Quel modele minimal de donnees WorksOps evite de dupliquer ComptaScope tout en affichant vote, engage, facture, paye et reste a financer?
- Comment representer les travaux urgents hors AG sans inciter a valider trop vite?
- Quels seuils de mise en concurrence et consultation du conseil syndical doivent etre parametres par instance?
- Comment rattacher un devis ou une facture trouvee sans decision AG: operation `A qualifier`, demande syndic ou controle comptable?
- Quel export travaux est diffusable aux coproprietaires sans exposer negociation, contentieux ou donnees personnelles?

## BOT-END

BOT-END - Orchestrateur UX/UI - 2026-05-24 04:17 +02:00

Roadmap: `RM-2026-0032`
Chantier: `CH-20260524-033252-RM-2026-0032-travaux-ux-ui`
Conversation: `CONV-2026-1331`
Statut: `CLOTURE`
Fichiers modifies: `docs/recherche_ux_ui_2026-05-24_travaux.md`, `docs/assets/ux-ui-recherche-2026-05-24-travaux/README.md`, `docs/assets/ux-ui-recherche-2026-05-24-travaux/01-console-travaux-portefeuille-fiche.svg`, `docs/roadmap_backlog_central.md`, `docs/presence_agents.md`.
Fichiers volontairement evites: code applicatif, routes, templates, CSS, tests applicatifs, instances privees, secrets, exports bruts, passerelles UX/DB hors mission, `RM-2026-0017` bloque.
Tests/preuves: recherche documentaire et blueprint SVG; verification applicative non lancee car aucun code.
Limites: sources juridiques utilisees comme garde-fous UX, pas comme avis juridique; aucune validation utilisateur terrain reelle; aucune image bitmap generee.
Questions ouvertes: modele metier minimal, seuils instance, statut travaux urgents, export diffusable.
Prochain mouvement propose: ouvrir un chantier de cadrage metier WorksOps avant tout dev UI.

UXUI-DONE - equipe UX/UI a fini son job

## Journal

| Heure | Conversation | Evenement | Note |
|---|---|---|---|
| 2026-05-24 03:32 +02:00 | `CONV-2026-1331` | `BOT-START` | Equipe UX/UI travaux lancee en recherche sans dev. |
| 2026-05-24 03:33 +02:00 | `CONV-2026-1332`..`CONV-2026-1336` | `AGENTS_LAUNCHED` | Agents Beauvoir, Nietzsche, Russell, Jason et Heisenberg lances en lecture seule. |
| 2026-05-24 04:13 +02:00 | `CONV-2026-1332`..`CONV-2026-1336` | `AGENTS_RESTARTED` | Anciennes tentatives fermees sans sortie exploitable; agents de remplacement Pascal, Erdos, Epicurus, Meitner et Ramanujan lances. |
| 2026-05-24 04:17 +02:00 | `CONV-2026-1331`..`CONV-2026-1336` | `UXUI_DONE` | Recherche consolidee, blueprint SVG archive, aucun code applicatif modifie. |
