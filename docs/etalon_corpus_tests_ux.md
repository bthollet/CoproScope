# Etalon du corpus de test `tests_ux`

Date d'etablissement: 2026-09-03.
Item gouvernail: RM-2026-0050.
Parent: [`parcours_utilisateur_tests_ux.md`](./parcours_utilisateur_tests_ux.md) et
[`parcours_b_controle_comptes.md`](./parcours_b_controle_comptes.md).

## A quoi sert ce document

Il fige, **avant tout traitement CoproScope**, ce qu'un lecteur humain lit dans
les pieces du corpus de test. Il sert de reference unique pour mesurer un ecart.
Un etalon produit par l'outil ne mesure pas l'outil: la sequence lecture humaine
d'abord, execution ensuite, n'est pas negociable.

Ce document ne contient aucun nom de personne, aucune adresse, aucun contact,
aucun nom de fichier brut, aucun chemin local et aucun extrait de texte extrait.
Les pieces sont designees par un identifiant stable `P-x-nn`. La table qui relie
ces identifiants aux fichiers reels reste dans l'instance de test, hors Git.

## Regle de source appliquee

Les pieces sont copiees depuis les **sources primaires** du coffre prive: la
zone de collecte brute non modifiee (export de l'extranet du syndic) et la boite
de reception non triee. Les arborescences reclassees, les fichiers scindes, les
versions dites reparees et les instances de recette anterieures sont **exclues
comme origine de copie**: elles portent l'historique de retraitements successifs,
et une piece qui en vient ferait mesurer l'outil contre lui-meme.

Deux exceptions sont assumees et signalees: la convocation de decembre 2025 et
l'etat des depenses 2025 n'existent au coffre que sous un chemin reclasse. Leurs
metadonnees PDF montrent qu'il s'agit des fichiers d'origine produits par le
prestataire d'envoi et par le logiciel comptable du syndic, non de re-rendus.
Elles sont retenues avec cette reserve explicite.

## Composition du corpus

Cible du parcours: 35 pieces, dont 30 reelles et 5 leurres deliberes.

| Bloc | Cible | Place | Ecart |
|---|---:|---:|---|
| Parcours A - gouvernance AG | 8 | 1 | 6 pieces indisponibles en source primaire, 1 bloquee |
| Parcours B - comptes | 16 | 16 | 0, l'etat des depenses 2025 a ete debloque le 2026-09-03 |
| Parcours D - typologie | 6 | 8 | complete pour tenir le volume |
| Leurres | 5 | 5 | 0 |
| **Total** | **35** | **30** | **-5** |

**La cible de 35 est inatteignable telle qu'ecrite, et il faut le dire ici**
plutot que de laisser un ecart permanent passer pour un retard. Quatre des cinq
pieces manquantes n'existent pas en source primaire: le proces-verbal du
21/02/2024 n'existe pas du tout, ses convocations n'existent qu'en versions
scindees sans couche de texte, et aucun devis autonome n'existe - tous sont des
extraits scindes d'une convocation. **La cible reelle de ce corpus est 30.** La
cinquieme, la convocation de decembre 2025, est refusee pour un motif de fond
expose plus bas.

### Ce qui manque, et pourquoi

1. **Le proces-verbal de l'assemblee du 21/02/2024 n'existe pas au dossier.**
   Ni en source primaire, ni ailleurs. Le registre de constats du coffre le
   reclame d'ailleurs lui-meme comme piece a demander au syndic. Consequence
   directe: l'etalon publie sur cette assemblee ne peut etre confronte a aucun
   proces-verbal (voir la section Parcours A).
2. **Les pieces de convocation du 21/02/2024 n'existent qu'en versions scindees,
   sans couche de texte et sans metadonnees.** Elles sont donc derivees, et de
   plus illisibles sans OCR. Exclues.
3. **Aucun devis autonome n'est disponible en source primaire.** Les devis du
   dossier sont tous des extraits scindes d'une convocation. Le piege 2 du
   parcours B (un devis presente comme une facture) n'est donc pas pose.
4. **Deux pieces n'ont pas pu etre placees**, l'etat des depenses 2025 et la
   convocation de decembre 2025, pour la meme raison. Voir la section blocage.

## Blocage tranche le 2026-09-03, et les deux pieces ont recu des verdicts opposes

*Section reecrite le 2026-09-09. Elle presentait trois issues comme ouvertes;
elles ont ete tranchees le lendemain de sa redaction, et **dans deux sens
contraires**. Un lecteur de l'etalon pouvait donc croire, six jours durant, la
piece etalon du parcours B absente alors qu'elle est placee.*

Deux pieces portent des noms de personnes, leur pseudonymisation est donc
obligatoire. L'outil local applique bien les pseudonymes, puis **sa garde de
sortie detectait des motifs residuels, supprimait le fichier produit et rendait
`FAILED_PRIVACY_PATTERN`**.

### L'etat des depenses 2025, piece etalon du parcours B: PLACEE

Motifs residuels a l'origine du refus: 20 references de factures fournisseurs
prises pour des references de contrat, et 3 intitules de sous-poste comptable
contenant le mot `intervention`. **Aucun n'est une identite**: ce sont des
references documentaires et des intitules comptables.

Verdict rendu par `RM-2026-0062`: **allowlist justifiee piece par piece et
journalisee**, 58 motifs examines, 0 refuse. La piece a ete placee le 2026-09-03
a 02h56. Sa ligne de manifeste, restee due pendant six jours parce que le
manifeste avait ete ferme douze minutes plus tot par un autre lot, a ete ecrite
le 2026-09-09 sous l'identifiant `P-B-E01`, empreinte recalculee sur le fichier
et chemin d'origine retrouve par empreinte, non suppose.

### La convocation de decembre 2025, piece pivot du parcours A: REFUSEE

**Le refus est maintenu, mais pour un motif MEILLEUR que celui d'origine, et
c'est le point qui compte.**

Le motif d'origine etait faible: 23 mentions contenant le mot `intervention`,
4 references de contrat, 2 codes postaux suivis d'un nom de commune, 2 lignes de
numero d'immatriculation d'entreprise - aucune identite, exactement comme pour
l'autre piece.

Le vrai motif a ete etabli ensuite, et il est porte par `RM-2026-0068`: cette
piece contient **une liste de coproprietaires nommes sans civilite**, que la
chaine de pseudonymisation **ne voit pas**. La garde refusait pour de mauvaises
raisons une piece qu'il fallait refuser pour une bonne. Tant que `RM-2026-0068`
est ouvert, aucune sortie tiree de ce corpus n'est diffusable.

### Ce que cet episode a etabli, et qui vaut au-dela du corpus

Une garde qui bloque sur des references documentaires et laisse passer une liste
de patronymes sans civilite **n'est pas trop stricte: elle regarde au mauvais
endroit**. Le nombre de refus ne dit rien de sa justesse - deux pieces sur
trente refusees, et le compte etait faux dans les deux sens a la fois.

Deux des motifs residuels cites plus haut, *codes postaux suivis d'un nom de
commune*, sont devenus le 2026-09-09 la regle d'un garde du depot
(`server/tests/test_aucune_adresse_reelle.py`) - apres qu'une adresse postale
reelle a traverse le pseudonymat dans une fixture de test. Le motif etait bon;
c'est le perimetre ou on l'appliquait qui ne l'etait pas.

**Les valeurs de l'etalon comptable ci-dessous ont ete etablies a la main**, par
lecture en seule lecture de la source, ce qui n'exige aucune copie.

## Parcours A - ce que dit l'assemblee, et ce qui a ete vote

### Verification de l'etalon publie: il est faux

`parcours_utilisateur_tests_ux.md` annonce un etalon connu au detail pres:
34 resolutions a l'assemblee du 21/02/2024, toutes sous la majorite de
l'article 24, resolution 29 rejetee, resolutions 30 et 33 portant `Pas de vote`,
devis a 22 200,00 rejete et devis a 18 240,00 adopte.

Lecture faite, **cet etalon ne tient pas**. Point par point:

| Affirmation publiee | Ce que montre la lecture |
|---|---|
| Un proces-verbal du 21/02/2024 existe et compte 34 resolutions | Aucun proces-verbal de cette assemblee n'existe au dossier. Le coffre le reclame lui-meme comme piece manquante. |
| Toutes les resolutions relevent de l'article 24 | Sur le seul proces-verbal reellement disponible, celui de l'assemblee du 03/07/2024, 30 resolutions relevent de l'article 24, 23 des articles 25 et 25-1, 1 de l'article 25B et 1 n'enonce aucune majorite. |
| La resolution 29 est rejetee | Sur ce meme proces-verbal, la resolution 29 est adoptee: c'est le vote du budget previsionnel 2025, arrete a 280 000,00. |
| Les resolutions 30 et 33 portent `Pas de vote` | La resolution 30 est adoptee. La resolution 33 est rejetee. Aucune des deux ne porte `Pas de vote`. |
| Le devis a 22 200,00 est rejete, celui a 18 240,00 adopte | Ces deux montants ne figurent dans aucun proces-verbal du dossier. Ils proviennent de la convocation de fevrier 2024, qui est un document scanne sans aucune couche de texte. La note d'audit qui les cite renvoie a des numeros de ligne d'un fichier d'extraction qui ne contient, lui, aucun texte extrait. |

Autrement dit, l'etalon publie melange deux assemblees differentes, attribue a
un proces-verbal inexistant des issues qui appartiennent a un autre document, et
s'appuie pour les montants sur une citation qui ne renvoie a rien de lisible.
**Il ne peut pas servir de reference de mesure et doit etre retire ou corrige
dans `parcours_utilisateur_tests_ux.md`.**

Cette conclusion vaut aussi comme signal sur la methode: une affirmation
chiffree qui circule de note en note sans etre reverifiee sur la piece source
finit par etre traitee comme un fait.

### Etalon reel: proces-verbal de l'assemblee du 03/07/2024 (piece `P-A-01`)

Piece originale, produite par le syndic, 10 pages, texte selectionnable integral.

Reperes chiffres verifiables:

- comptes de l'exercice 2023 approuves: 263 803,64 de depenses courantes et
  4 350,56 de depenses hors budget;
- honoraires de gestion courante du syndic: 21 300,00 hors taxes,
  soit 25 560,00 toutes taxes comprises, pour un mandat de 24 mois;
- budget previsionnel 2024: 280 000,00; budget previsionnel 2025: 280 000,00;
- deux bases de tantiemes coexistent dans le meme proces-verbal: certains votes
  sont exprimes sur 4 899 et d'autres sur 10 000. Un outil qui normalise sans le
  dire produira des pourcentages faux.

Comptage attendu:

| Mesure | Valeur attendue |
|---|---:|
| Resolutions numerotees | 55 |
| Adoptees | 39 |
| Rejetees | 7 |
| Portant `Pas de vote` | 8 |
| Issue non enoncee par le proces-verbal | 1 |
| Majorite article 24 | 30 |
| Majorite articles 25 et 25-1 | 23 |
| Majorite article 25B | 1 |
| Majorite non enoncee | 1 |

Cas particuliers a ne pas manquer:

- **Resolution 28**, budget previsionnel 2024: les trois lignes de vote sont
  presentes, mais le proces-verbal n'ecrit jamais la phrase d'issue. Un outil
  correct rend `issue non enoncee` et ne conclut pas a l'adoption.
- **Resolution 23**: aucune majorite enoncee, et la mention porte que les
  coproprietaires ne votent pas, seuls les membres elus le font.
- **Resolution 35**: majorite de l'article 25B, et l'issue est `Pas le quorum.
  Pas de vote.`
- Les quatre resolutions rejetees portant sur des travaux d'entree sont chacune
  suivies d'une resolution d'appel de fonds portant `Pas de vote car la
  resolution est rejetee`. Le lien de dependance entre les deux doit etre rendu.

Detail resolution par resolution:

| Nº | Majorite (article) | Issue | Objet |
|---:|---|---|---|
| 1 | 24 | ADOPTEE | Bureau de seance - president |
| 2 | 24 | ADOPTEE | Bureau de seance - 1er scrutateur |
| 3 | 24 | ADOPTEE | Bureau de seance - 2e scrutateur |
| 4 | 24 | ADOPTEE | Bureau de seance - secretaire |
| 5 | 24 | ADOPTEE | Approbation des comptes de l'exercice 2023 |
| 6 | 24 | ADOPTEE | Modalites de consultation des pieces justificatives |
| 7 | 25 et 25-1 | ADOPTEE | Election du syndic et honoraires de gestion courante |
| 8 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 1 |
| 9 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 2 |
| 10 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 3 |
| 11 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 4 |
| 12 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 5 |
| 13 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 6 |
| 14 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 7 |
| 15 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 8 |
| 16 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 9 |
| 17 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 10 |
| 18 | 25 et 25-1 | REJETEE | Election au conseil syndical - candidature 11 |
| 19 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 12 |
| 20 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 13 |
| 21 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 14 |
| 22 | 25 et 25-1 | ADOPTEE | Election au conseil syndical - candidature 15 |
| 23 | non enoncee | PAS DE VOTE | Election du president du conseil syndical par les membres elus |
| 24 | 25 et 25-1 | PAS DE VOTE | Designation du representant au syndicat principal - candidature 1 |
| 25 | 25 et 25-1 | REJETEE | Designation du representant au syndicat principal - candidature 2 |
| 26 | 25 et 25-1 | ADOPTEE | Seuil de consultation obligatoire du conseil syndical |
| 27 | 25 et 25-1 | ADOPTEE | Seuil de mise en concurrence des entreprises |
| 28 | 24 | ISSUE NON ENONCEE | Budget previsionnel de l'exercice 2024 |
| 29 | 24 | ADOPTEE | Budget previsionnel de l'exercice 2025 |
| 30 | 24 | ADOPTEE | Modalites de recouvrement des charges |
| 31 | 24 | ADOPTEE | Clause d'aggravation des charges |
| 32 | 25 et 25-1 | ADOPTEE | Autorisation permanente donnee a la police municipale |
| 33 | 25 et 25-1 | REJETEE | Recul d'une barriere de la residence |
| 34 | 25 et 25-1 | PAS DE VOTE | Remplacement d'un portail battant par un portillon |
| 35 | 25B | PAS DE VOTE | Demande individuelle - installation d'un moteur de climatiseur |
| 36 | 24 | REJETEE | Travaux boites aux lettres - entree 21 |
| 37 | 24 | PAS DE VOTE | Appels de fonds exceptionnels - entree 21 |
| 38 | 24 | REJETEE | Travaux boites aux lettres - entree 22 |
| 39 | 24 | PAS DE VOTE | Appels de fonds exceptionnels - entree 22 |
| 40 | 24 | ADOPTEE | Travaux boites aux lettres - entree 23 |
| 41 | 24 | ADOPTEE | Appels de fonds exceptionnels - entree 23 |
| 42 | 24 | REJETEE | Travaux boites aux lettres - entree 24 |
| 43 | 24 | PAS DE VOTE | Appels de fonds exceptionnels - entree 24 |
| 44 | 24 | ADOPTEE | Travaux boites aux lettres - entree 25 |
| 45 | 24 | ADOPTEE | Appels de fonds exceptionnels - entree 25 |
| 46 | 24 | ADOPTEE | Travaux boites aux lettres - entree 26 |
| 47 | 24 | ADOPTEE | Appels de fonds exceptionnels - entree 26 |
| 48 | 24 | REJETEE | Travaux boites aux lettres - entree 27 |
| 49 | 24 | PAS DE VOTE | Appels de fonds exceptionnels - entree 27 |
| 50 | 24 | ADOPTEE | Travaux boites aux lettres - entree 28 |
| 51 | 24 | ADOPTEE | Appels de fonds exceptionnels - entree 28 |
| 52 | 24 | ADOPTEE | Travaux boites aux lettres - entree 29 |
| 53 | 24 | ADOPTEE | Appels de fonds exceptionnels - entree 29 |
| 54 | 24 | ADOPTEE | Travaux boites aux lettres - entree 30 |
| 55 | 24 | ADOPTEE | Appels de fonds exceptionnels - entree 30 |

## Parcours B - controler les comptes avant l'assemblee

### Totaux de l'etat des depenses de l'exercice 2025

Etablis a la main sur l'etat detaille des depenses du 01/01/2025 au 31/12/2025,
35 pages, edite le 06/05/2026 par le logiciel comptable du syndic.

| Agregat | Montant a repartir | Dont charges locatives | T.V.A. |
|---|---:|---:|---:|
| Total charges courantes | 304 021,37 | 226 205,97 | 37 930,82 |
| Total charges travaux et operations exceptionnelles | 53 471,73 | - | 6 393,77 |
| **T O T A L   G E N E R A L** | **357 493,10** | **226 205,97** | **44 324,59** |

Controles de coherence interne, verifies a la main et tous justes:

- 304 021,37 + 53 471,73 = 357 493,10;
- 37 930,82 + 6 393,77 = 44 324,59.

**C'est ce montant de 357 493,10 qui est l'etalon du premier chiffre affiche par
l'ecran des comptes, une fois ce corpus charge.** Les chiffres cites au
2026-09-02, 21 994 060,46 au cockpit et 22 368 660,47 au grand livre reconstitue,
ont ete releves sur une instance beaucoup plus volumineuse: ils ne se comparent
pas terme a terme a l'etalon ci-dessus. Ce qu'ils disent quand meme, et qui reste
a expliquer, c'est que deux ecrans du meme outil affichaient deux totaux
differents pour la meme notion.

Sous-totaux par cle de repartition, utiles pour localiser une erreur:

| Cle de repartition | Charges courantes | Travaux et exceptionnel |
|---|---:|---:|
| Charges generales (10 000 parts) | 180 238,54 | 11 889,64 |
| Charges compteurs (196 parts) | 8 813,07 | - |
| Charges syndicat principal (1 500 parts) | 20 790,11 | - |
| Ascenseurs (8 cles) | 23 965,80 | 15 401,06 |
| Blocs 1 a 4 | 1 387,67 | 14 871,02 |
| Entrees 21 a 30 | 21 790,17 | 11 740,11 |
| Eau par entree (10 cles) | 47 036,01 | - |
| Parts egales par entree | 0,00 | -430,10 |
| **Somme des cles** | **304 021,37** | **53 471,73** |

Les deux colonnes ont ete recalculees cle par cle et retombent exactement sur les
agregats de la page de synthese. C'est le seul controle qui permet d'affirmer que
la lecture manuelle n'a rien oublie.

### Rattachement attendu des 12 factures a une ligne de l'etat

Chaque rattachement a ete verifie deux fois: par la reference de piece portee par
la ligne comptable, et par le montant.

Lecture des colonnes, etablie par recoupement sur plusieurs lignes: le montant a
repartir est un montant **toutes taxes comprises**, et la colonne T.V.A. donne la
taxe **incluse** dans ce montant au taux indique. Verification: 1 200,00 au taux
de 20 % donne bien 200,00, et 770,00 au taux de 10 % donne bien 70,00. Un outil
qui traiterait le montant a repartir comme un hors taxes surevaluerait chaque
ligne.

| Piece | Date de la ligne | Compte | Montant a repartir | Taux | T.V.A. |
|---|---|---|---:|---:|---:|
| P-B-F01 | 09/01/2025 | 616000 Primes d'assurances | 22 163,40 | 20,00 | 3 693,90 |
| P-B-F02 | 27/01/2025 | 614000 Contrats de maintenance | 117,32 | 20,00 | 19,55 |
| P-B-F03 | 28/03/2025 | 615000 Entretien et petites reparations | 1 665,66 | 20,00 | 277,61 |
| P-B-F04 | 15/02/2025 | 615000 Entretien et petites reparations | 770,00 | 10,00 | 70,00 |
| P-B-F05 | 24/02/2025 | 615000 Entretien et petites reparations | 880,00 | 10,00 | 80,00 |
| P-B-F06 | 24/07/2025 | 615000 Entretien et petites reparations | 1 914,00 | 10,00 | 174,00 |
| P-B-F07 | 25/04/2025 | 615000 Entretien et petites reparations | 561,00 | 10,00 | 51,00 |
| P-B-F08 | 06/11/2025 | 672000 Travaux urgents | 2 977,50 | 10,00 | 270,68 |
| P-B-F09 | 18/03/2025 | 601000 Eau | 232,12 | 10,00 | 21,10 |
| P-B-F10 | 01/09/2025 | 602000 Electricite | 101,90 | 20,00 | 16,98 |
| P-B-F11 | 18/04/2025 | 622300 Autres honoraires | 600,00 | 20,00 | 100,00 |
| P-B-F12 | 20/01/2025 | 615000 Entretien et petites reparations | 1 200,00 | 20,00 | 200,00 |

Trois ecarts reels, constates a la lecture et a poser comme questions au syndic.
Ils ne sont pas des pieges fabriques: ils sont dans les pieces. Tous les trois
portent sur le taux de T.V.A. retenu par la comptabilite.

- **P-B-F03**: la piece porte 1 514,24 hors taxes, une T.V.A. a 10 % de 151,42 et
  un total de 1 665,66. La ligne comptable reprend bien 1 665,66, mais en extrait
  une T.V.A. de 277,61 au taux de 20 %. L'ecart de T.V.A. est de 126,19.
- **P-B-F12**: la piece indique expressement que la T.V.A. n'est pas applicable,
  pour un total de 1 200,00. La ligne comptable en extrait pourtant 200,00 de
  T.V.A. au taux de 20 %. Une taxe est constatee sur une piece qui n'en porte
  aucune.
- **P-B-F01**: il s'agit d'une prime d'assurance, dont le detail est 19 570,25 de
  prime, 2 563,15 de taxes d'assurance et 30,00 de frais, soit 22 163,40. La
  ligne comptable reprend 22 163,40 et en extrait 3 693,90 de T.V.A. au taux de
  20 %. Une prime d'assurance ne supporte pas de T.V.A. mais une taxe sur les
  conventions d'assurance, deja comprise dans le montant.

Ces trois constats sont a presenter comme des questions, pas comme des
conclusions: seul le syndic peut dire s'il s'agit d'un parametrage de compte ou
d'une erreur d'imputation.

### Les 3 pieces sans ligne correspondante

| Piece | Nature | Montant | Pourquoi elle n'a pas de ligne |
|---|---|---:|---|
| P-B-S01 | Appel de fonds emis par le syndicat principal, periode du 01/10/2025 au 31/12/2025 | 353,10 | Ce n'est pas une facture fournisseur du syndicat secondaire. Aucun de ses montants ne figure dans l'etat. |
| P-B-S02 | Appel de fonds emis par le syndicat principal, periode du 01/04/2025 au 30/06/2025 | 409,90 | Idem. |
| P-B-S03 | Facture de ramonage de l'exercice 2023 | 1 540,00 | Exercice anterieur. Ne peut pas figurer dans l'etat 2025. |

Attendu: ces trois pieces sortent en `sans rapprochement`. Les deux appels de
fonds doivent en outre etre qualifies autrement que `facture`.

### Les 5 pieges, et la reponse attendue

| Nº | Piege | Ou | Reponse attendue |
|---:|---|---|---|
| 1 | Une meme facture presente deux fois, en PDF et en conversion markdown | P-B-F02 et L-04 | Une seule piece comptable. La conversion est un doublon, elle ne cree ni une seconde facture ni un second montant. |
| 2 | Un devis presente parmi des factures | **non pose** | Aucun devis autonome n'existe en source primaire. Piege a poser dans un lot ulterieur. |
| 3 | Une facture d'un autre exercice | P-B-S03 | Exclue de l'exercice 2025, signalee comme hors periode, jamais integree au total. |
| 4 | Une facture sans SIREN ni SIRET | P-B-F12 | Signalee comme mention obligatoire manquante. La diligence fournisseur ne peut pas etre conduite sur cette piece. |
| 5 | Un montant abime a la lecture, chiffre des milliers perdu | P-B-F03 | La couche de texte de cette piece a ete alteree volontairement: le total lit 665,66 alors que la piece porte 1 514,24 hors taxes et 151,42 de T.V.A. La somme ne tombe pas. L'outil doit detecter l'incoherence hors taxes + T.V.A. differente du total, et ne pas integrer 665,66 en silence. |

Le piege 5 est la seule alteration volontaire du corpus. Elle est tracee dans le
manifeste de l'instance. Toutes les autres pieces sont conformes a leur source,
a la pseudonymisation pres.

### Volume attendu

Sur 15 pieces comptables, le parcours fixe un plafond de 20 points a traiter. Les
ecarts reellement portes par le corpus sont au nombre de **sept**: les trois
ecarts de taux de T.V.A. ci-dessus, les trois pieces sans rapprochement, et
l'incoherence du piege 5. Un compte a trois chiffres sur ce corpus signalerait une
regle de generation defaillante, pas un probleme de volume.

## Parcours D - typologie attendue, piece par piece

`Texte` indique que la piece porte une couche de texte selectionnable.
`Image` indique une piece scannee sans texte: aucune qualification ne peut en
etre tiree sans reconnaissance de caracteres, et un outil qui la classe quand
meme invente.

| Piece | Type attendu | Lisibilite | Remarque de mesure |
|---|---|---|---|
| P-A-01 | Proces-verbal d'assemblee generale | Texte | 10 pages, 55 resolutions |
| P-A-02 | Convocation d'assemblee generale avec annexes | Texte partiel | 143 pages. Non placee: refusee par la garde de pseudonymisation. |
| P-B-F01 | Avis d'echeance de prime d'assurance | Texte | ce n'est pas une facture fournisseur |
| P-B-F02 | Facture - contrat de maintenance | Texte | duplique par L-04 |
| P-B-F03 | Facture - entretien | Texte | couche de texte alteree, piege 5 |
| P-B-F04 | Facture - entretien | Texte | |
| P-B-F05 | Facture - entretien | Texte | |
| P-B-F06 | Facture - entretien | Texte | |
| P-B-F07 | Facture - entretien | Texte | |
| P-B-F08 | Facture - travaux urgents | Texte | |
| P-B-F09 | Facture - eau | Texte | |
| P-B-F10 | Facture - electricite | Texte | |
| P-B-F11 | Note de frais du syndic | Texte | ce n'est pas une facture fournisseur |
| P-B-F12 | Facture - espaces verts | Texte | sans SIREN ni SIRET, piege 4 |
| P-B-S01 | Appel de fonds du syndicat principal | Texte | ne doit pas sortir en `Facture` |
| P-B-S02 | Appel de fonds du syndicat principal | Texte | ne doit pas sortir en `Facture` |
| P-B-S03 | Facture - exercice 2023 | Texte | piege 3 |
| P-D-01 | Contrat de syndic | Image | 9 pages sans texte |
| P-D-02 | Contrat d'assurance | Texte | |
| P-D-03 | Contrat de maintenance ascenseur | Image | 20 pages sans texte |
| P-D-04 | Diagnostic technique | Image | 11 pages sans texte |
| P-D-05 | Carnet d'entretien | Texte | |
| P-D-06 | Reglement de copropriete | Image | 10 pages sans texte |
| P-D-07 | Etat des depenses de l'exercice 2024 | Texte | ne doit pas etre confondu avec l'exercice 2025 |
| P-D-08 | Compte rendu de reunion du conseil syndical | Texte | |
| L-01 | Fichier d'index de coffre | - | `A_CLASSER` ou rejete |
| L-02 | Tableau de bord au format tableur | - | `A_CLASSER` ou rejete. Ne doit produire aucune pseudo-facture. |
| L-03 | Script d'outillage | - | `A_CLASSER` ou rejete |
| L-04 | Conversion markdown d'une facture deja presente | - | `A_CLASSER` ou doublon. Ne cree pas de seconde piece comptable. |
| L-05 | Artefact d'extraction texte d'un proces-verbal deja present | - | `A_CLASSER` ou doublon. Ne cree pas un second proces-verbal. |

Seuils du parcours D:

- aucun des 5 leurres ne ressort en `Contrat_Syndic` ni en `Devis`;
- aucun leurre n'entre dans un total comptable;
- les 6 pieces sans couche de texte ne recoivent pas une qualification affirmative
  produite a partir de rien.

## Parcours E - ce qui peut sortir, ce qui doit rester

Trois pieces du corpus portaient des noms de personnes et ont ete pseudonymisees
par l'outil local: le proces-verbal, la convocation et le compte rendu de
conseil syndical. Deux factures et deux appels de fonds portaient des noms de
salaries du syndic ou de l'agence: pseudonymises egalement.

Limite mesuree et a connaitre: sur le proces-verbal, la pseudonymisation
automatique laisse passer une petite proportion de patronymes, notamment les noms
composes et ceux qui apparaissent dans une forme differente de leur premiere
occurrence. Le corpus reste donc une donnee d'instance privee. Il ne doit pas
etre publie, ni servir de base a une capture diffusable.

Attendu du parcours E: un faux negatif, c'est-a-dire une piece sensible qui
passe, compte davantage qu'un faux positif sur un fichier d'index.

## Ce qui n'a pas pu etre etabli a la main

1. **Les resolutions de l'assemblee du 21/02/2024.** Aucun proces-verbal
   n'existe. Les documents de convocation de cette assemblee sont scannes sans
   couche de texte et n'existent qu'en versions scindees. Aucun etalon n'est
   possible sans obtenir la piece aupres du syndic, ou sans reconnaissance de
   caracteres assumee comme telle.
2. **Les montants des deux devis d'etude energetique** cites par l'etalon publie.
   Ils ne sont lisibles dans aucune piece primaire du dossier.
3. **Les resolutions de l'assemblee de decembre 2025.** Il existe une convocation,
   donc des projets de resolutions, mais aucun proces-verbal. On peut mesurer ce
   qui a ete propose, pas ce qui a ete vote.
4. **Le rattachement des 12 factures a un vote ou a un contrat.** La chaine
   decision - engagement - facture - paiement n'a pas ete reconstituee: elle
   suppose les contrats fournisseurs et les votes correspondants, qui ne sont pas
   tous au corpus.
5. **Le controle des mentions obligatoires des factures autre que SIREN/SIRET.**
   Seul le piege 4 a ete verifie piece par piece.

## Regles de tenue de ce document

- Toute correction d'un chiffre doit citer la piece et le controle qui l'a
  etablie.
- Un chiffre etabli par l'outil n'entre jamais ici. Ce document precede l'outil.
- La confrontation etalon / sortie CoproScope est conduite par un autre lot, par
  quelqu'un qui n'a pas etabli l'etalon.
