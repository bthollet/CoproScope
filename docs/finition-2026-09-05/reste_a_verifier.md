# Les 54 constats sans trace de correction citee

Liste produite le 2026-09-05 apres integration des six zones. Un constat est
ici parce qu'aucun fichier du depot ne cite son numero - ce qui n'est PAS la
meme chose que non corrige: C001 est ferme depuis le 2026-09-04 et n'y figure
sous aucun numero. Chacun est donc a verifier contre le code, jamais contre
une reference.

### C001 - Le contrat de filtrage se contourne par le parametre `ordre`, qui est du SQL brut



- **Fichier** : `server/src/coproscope/modules/_actes_requetes.py`

- **Silencieux** : oui

- **Preuve** : _actes_requetes.construire_requete: `sql += f" ORDER BY {ordre}"`, sans aucune validation. _actes_store.lire_vue expose ce parametre et sa docstring affirme 'Aucune chaine SQL ne vient de l'appelant'. Mesure: lire_vue(inst, 'v_actes', [('nature','eq','RESOLUTION_AG')], ordre="CASE WHEN objet LIKE '%facade%' THEN 0 ELSE 1 END, acte_id") s'execute et rend 2 lignes; une sous-requete arbitraire (SELECT COUNT(*) ... WHERE objet LIKE ...) dans ORDER BY passe aussi. Le test test_aucun_filtre_ne_balaie_du_texte (test_actes_autorisation.py:421-434) n'inspecte que les criteres, jamais `ordre`: le contournement ne casse aucun test.

- **Consequence** : La liste fermee d'operateurs et le test qui la defend ne couvrent pas le seul endroit ou du SQL d'appelant entre dans la requete. Un dev UI qui veut trier une colonne passera par `ordre` - c'est deja ce que font matrice() et constats() - et pourra y reintroduire le balayage de texte de _decision_cell_status, precisement ce que le module existe pour interdire.

### C004 - Deux assertions concurrentes sur la meme paire doublent le montant, jamais le compte



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py`

- **Silencieux** : oui

- **Preuve** : _actes_vues.py:326-341 (v_execution) et 292-317 (v_cumul_delegation): COUNT(DISTINCT dep.dossier_id) mais SUM(CAST(dep.montant_ttc AS REAL)) sur la meme jointure. Mesure: 2 liens AUTORISE (SYNDIC_AFFIRME + COPROSCOPE_CALCULE) sur la paire (A1,D1), facture unique 18 240,00 -> depenses_rattachees=1, montant_paye=36480.0. Sur le cumul: 3 depenses de 2 000,00, deux assertions chacune -> depenses_cumulees=2, cumul=8000.0. Or _actes_schema.lien_id met la provenance DANS l'identifiant a dessein ('Trois lignes, trois identifiants, aucun ecrasement'): le schema est concu pour que ce cas se produise.

- **Consequence** : Le constat emis est 'Resolution du 2024-07-03 : 36480.00 EUR payes pour 18240.00 EUR votes' - une accusation de surpaiement fabriquee par le modele lui-meme. Et 'Delegation votee le 2023-01-15 : 2 depenses cumulees pour 8000.00 EUR', phrase qui se contredit dans sa propre ligne (2 x 2 000 = 4 000), avec un faux PLAFOND_DEPASSE de 3 000,00. C'est le defaut des quatre comptages concurrents, reproduit dans le code ecrit pour le rendre impossible.

### C005 - La contradiction humaine est honoree par la matrice et ignoree par les montants: deux reponses opposees sur la meme ligne



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py`

- **Silencieux** : oui

- **Preuve** : _LIEN_VIVANT (_actes_vues.py:43-52) ajoute un NOT EXISTS sur la paire contredite. Il est applique par _cellule(), v_liens_manquants et EURO_SANS_ACTE. Il n'est PAS applique par v_execution (ligne 339), v_cumul_delegation (lignes 306, 310) ni SQL_ACTES_DU_DOSSIER (_actes_requetes.py), qui se contentent de provenance <> 'HUMAIN_CONTREDIT'. Mesure: un lien COPROSCOPE_CALCULE plus un HUMAIN_CONTREDIT sur la meme paire (A1,D1) -> cel_execution=PIECE_PRODUITE, depenses_rattachees=1, montant_paye=18240.0, actes_du_dossier('D1') rend encore l'acte, et en meme temps le constat EURO_SANS_ACTE est emis.

- **Consequence** : Sur une seule ligne d'ecran, la cellule 'execution' affirme que la depense est rattachee et le constat affirme qu'aucun acte ne la couvre. L'humain qui a tranche voit sa correction appliquee a une colonne et ignoree par la colonne d'a cote, sans qu'aucune des deux ne se signale.

### C006 - La contradiction humaine ne franchit pas les vues de montant : la base se contredit elle-meme au meme instant



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py (_V_EXECUTION, _V_CUMUL vs _LIEN_VIVANT)`

- **Silencieux** : oui

- **Preuve** : Mesure. Apres qu'un humain a ecrit un lien de provenance HUMAIN_CONTREDIT sur la paire acte/dossier : v_cumul_delegation reste a cumul 24 000,0, v_execution reste a montant_paye 12 000,0, v_matrice_gouvernance.cel_execution reste 'PIECE_PRODUITE' - et au meme moment v_constats emet EURO_SANS_ACTE sur ce meme dossier (« aucun acte d'autorisation ne la couvre »). Cause : _LIEN_VIVANT (le NOT EXISTS qui neutralise la paire) est employe par _V_ACTE_EFFECTIF, _V_LIENS_MANQUANTS, _cellule() et v_constats, mais _V_EXECUTION et _V_CUMUL n'ecrivent que « l.provenance <> 'HUMAIN_CONTREDIT' », qui exclut la ligne de contradiction et pas la paire ; et cel_execution ne lit pas les liens, il lit e.depenses_rattachees.

- **Consequence** : Un humain qui contredit un rattachement croit avoir tranche. Le compteur d'execution, le cumul de delegation et la cellule Execution de la matrice ne bougent pas. Deux ecrans nourris par la meme base affichent simultanement « paye 12 000 au titre de cet acte » et « aucun acte ne couvre cette depense ». C'est le defaut numero un du produit - des comptages concurrents pour la meme notion - reproduit a l'interieur du modele cense l'empecher, et il n'y a aucun message pour le dire.

### C007 - Deux assertions concurrentes sur la meme paire multiplient les euros au lieu de coexister



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py (_V_EXECUTION, _V_CUMUL)`

- **Silencieux** : oui

- **Preuve** : Mesure sur base neuve. Un acte, une facture de 18 240,00, puis N assertions AUTORISE sur la MEME paire (aucune contradiction, les provenances disent la meme chose) : 1 assertion -> montant_paye = 18 240,0 ; 2 -> 36 480,0 ; 3 -> 54 720,0, avec depenses_rattachees = 1 dans les trois cas. Cause : v_execution fait LEFT JOIN liens_gouvernance l ... AND l.provenance <> 'HUMAIN_CONTREDIT' puis SUM(dep.montant_ttc) ; chaque assertion cree une ligne de jointure de plus, alors que depenses_rattachees est un COUNT(DISTINCT). v_cumul_delegation multiplie deux fois : une delegation plafonnee a 10 000,00, une seule facture de 6 000,00, un lien FONDE_PAR et un lien AUTORISE -> cumul 6 000,0, aucun constat ; le syndic affirme le meme rattachement -> cumul 12 000,0 et PLAFOND_DEPASSE ; le syndic affirme aussi le meme FONDE_PAR -> cumul 24 000,0. Le facteur est le produit du nombre d'assertions FONDE_PAR par le nombre d'assertions AUTORISE. Le constat produit : « 1 depenses cumulees pour 24000.00 EUR sur la periode, plafond arrete a 10000.00 EUR ». Le test tests/test_actes_autorisation.py:172 construit exactement ce cas a deux assertions et ne verifie que le nombre de lignes de lien ; les 52 tests du lot passent.

- **Consequence** : La propriete centrale vendue par le schema - « plusieurs assertions concurrentes coexistent sans qu'aucune contrainte ne les oppose » - fabrique des montants. Un accord entre le syndic et CoproScope, pas un desaccord, suffit a doubler le montant paye et a declencher un faux depassement du plafond de l'article 21-2. La ligne est visiblement incoherente avec elle-meme (1 depense cumulee, 24 000 EUR) mais aucune erreur n'est levee et le motif interpole est une phrase credible, chiffree, prete a partir dans une note au conseil syndical.

### C008 - L'article 25-1 est accepte comme majorite d'entree, et le tiers qui l'ouvre n'est jamais verifie



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : oui

- **Preuve** : REGIMES["25-1"] a pour assiette ASSIETTE_VOIX_EXPRIMEES (l.102-114). La branche `if regime.assiette == ASSIETTE_VOIX_EXPRIMEES` (l.432-468) ne lit jamais voix_totales et n'appelle jamais passerelle_25_1_ouverte(). Mesure: decompte_resolution(majorite="25-1", voix_pour=3000, voix_contre=100, voix_totales=10000) rend ADOPTEE_CONFIRMEE, pourcentage 96.77, 0 constat - alors que 3 000 est sous le tiers de 3 334 et que le second vote n'etait donc pas ouvert. Les memes chiffres sous "25" rendent ADOPTEE_MAIS_DECOMPTE_INSUFFISANT a 30.0. L'enonce du regime porte pourtant la condition mot pour mot: "ouvert seulement si le projet a recueilli au moins le tiers des voix de tous les coproprietaires" (l.106-109).

- **Consequence** : C'est le cas demande: le module autorise un pourcentage a tort. Il proclame une adoption confirmee a 96,77 % sur une resolution que la loi interdisait de soumettre a un second vote. L'ecran affiche un chiffre juste sur une assiette dont l'acces etait illegal, sans un constat.

### C010 - Le comparateur de mots-cles ne neutralise pas les accents, alors que son module frere le fait : le vocabulaire francais correct est ecarte en silence



- **Fichier** : `server/src/coproscope/modules/_docuscope_parts/02_classification.py:38`

- **Silencieux** : oui

- **Preuve** : `_normalized_search_text` = `re.sub(r"[^a-z0-9]+", " ", value.lower())`. Les lettres accentuees ne sont pas dans [a-z0-9] : elles deviennent des espaces. `Proces-verbal de l'assemblee generale` correctement accentue se normalise en `proc s verbal de l assembl e g n rale`. Test direct : mot-cle `assemblee generale` contre le texte `Assemblee Generale ordinaire` -> True ; contre `Assemblée Générale ordinaire` -> False. Idem `reglement de copropriete`, `etat des depenses`, `proces-verbal`. Le module voisin 03_title_signature.py:57 fait exactement l'inverse : `unicodedata.normalize("NFKD", ...)` puis suppression des combinants. Mesure sur le corpus : 1595 des 2533 textes lisibles (63,0 %) portent au moins un caractere accentue dans les 6000 premiers caracteres. Comptage des declenchements de chacun des 112 mots-cles sur 3447 documents, tel quel puis accents neutralises : `reglement de copropriete` 30 -> 171, `assemblee generale` 70 -> 159, `proces-verbal` 15 -> 56, `net a payer` 43 -> 111, `impayes` 33 -> 67, `tantiemes` 17 -> 52, `budget previsionnel` 3 -> 22, `lettre recommandee` 7 -> 25, `marche de travaux` 0 -> 16, `reception des travaux` 0 -> 5. Total 4657 -> 5325 (+668, +14 %). Rejeu du classifieur avec accents neutralises : 179 lignes sur 3447 (5,2 %) changent de type.

- **Consequence** : La preuve la plus discriminante - la locution francaise qui nomme le document - est precisement celle qui porte un accent, donc celle qui est jetee. Ce qui survit est le vocabulaire le moins discriminant : `convocation` 281 declenchements, `facture` 486, `devis` 240, `recouvrement` 221, `contentieux` 196, `iban` 175, `honoraires` 145, `pouvoirs` 90. Le classifieur ne reconnait pas un vocabulaire metier : il reconnait le sous-ensemble sans accent de ce vocabulaire, qui est presque toujours le mot commun. `resolution adoptee`, le seul mot-cle de PV_AG capable de separer un proces-verbal d'une convocation, se declenche 0 fois sur un corpus qui contient un proces-verbal de 55 resolutions, parce que le document ecrit `résolution`.

### C011 - La signature de titre du proces-verbal n'est consultee que si le type retenu est deja PV_AG : elle ne peut jamais corriger, seulement douter



- **Fichier** : `server/src/coproscope/modules/_docuscope_parts/02_classification.py:84`

- **Silencieux** : oui

- **Preuve** : Lignes 84-85 : `title_pattern = title_signatures.get(doc_type, "")` puis `if row["classification_status"] == "AUTO_CLASSIFIED" and title_pattern:`. Comme la table ne contient que la cle `PV_AG`, `title_pattern` vaut `""` pour tout autre type et le controle est saute. J'ai applique la signature en test positif sur les 3447 documents (meme normalisation, meme fenetre de 300 caracteres utiles, meme plancher de 200) : elle designe exactement 3 documents, et les 3 sont bien le proces-verbal du 03/07/2024. Deux des trois sont etiquetes Convocation_AG et ne sont donc jamais examines. Le plus net : la piece dont le nom de fichier est `DIVERS_pv 03072024.pdf`, 58 813 caracteres, dont le texte extrait commence au caractere 0 par `PROCES-VERBAL DE L'ASSEMBLEE GENERALE de la RESIDENCE`. Motif declencheur mesure : `MOT:convocation;MOT:ordre du jour;MOT:assemblee generale`, score 15, contre 15 aussi pour PV_AG ; Convocation_AG est ecrite avant PV_AG dans le fichier, elle gagne l'egalite. Corollaire mesure : le statut `TEXTE_INSUFFISANT`, l'etat "je ne sais pas" que ce module a ete ecrit pour exprimer, est emis 0 fois sur 3447 lignes.

- **Consequence** : Le seul controle de forme du produit - celui documente comme ayant 5 vrais positifs et 0 faux positif sur 37 documents de deux cabinets - est cable en aval de la decision qu'il devrait arbitrer. Il rattrape 9 fausses etiquettes PV_AG sur 10 (bon), et laisse passer les 2 vrais proces-verbaux ranges ailleurs (rappel : 1 sur 3). Une regle qui n'a le droit de parler que quand la reponse est deja juste ne mesure rien.

### C013 - Cinq votes du second cabinet sortent de tous les comptages, sans drapeau, parce qu'un mot de clôture n'est pas dans la liste



- **Fichier** : `server/src/coproscope/modules/_resolutions_extraction.py:85`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/modules/_resolutions_extraction.py:85, fonction _issue : après avoir essayé les neuf préfixes de ISSUE_PREFIXES, la ligne est `return mot.upper()`. Mesuré sur les deux corpus : le cabinet A écrit « cette résolution est adoptée / rejetée » ; le cabinet B (second corpus, 22 PDF) écrit cinq fois « cette résolution est DEVENUE sans objet ». CLOTURE_RE ne capture que le premier mot, `devenue`, aucun préfixe ne matche, et le résultat stocké devient la chaîne « DEVENUE ». J'ai vérifié les trois conséquences une par une : « DEVENUE » n'est pas une clé de LIBELLES_RESULTAT (resolutions_view.py:54), donc l'écran affiche le mot brut ; il n'est dans aucun des trois compteurs de _comptages (resolutions_view.py:163-170) ; il n'est pas dans RESULTATS_A_RELIRE (resolutions_view.py:52). Et la confiance de ces cinq lignes vaut « moyenne », pas « faible », donc a_relire reste faux. Le commentaire de _resolutions_motifs.py:142 dit d'où vient la liste : « vocabulaire relevé sur neuf assemblées de 2021 à 2026 » - d'un seul cabinet. La valeur correcte, SANS_OBJET, existe déjà dans le code et n'est simplement jamais atteinte.

- **Consequence** : Sur une assemblée du second cabinet, l'écran annonce 91 résolutions et n'en compte que 86 dans ses trois totaux. Les cinq manquantes s'affichent avec le mot « DEVENUE » en guise d'issue, aucune n'est proposée à la relecture, et rien ne dit que 5 votes ne sont dans aucun compteur. Un conseiller syndical qui additionne les trois chiffres et ne retombe pas sur le total n'a aucun moyen de savoir pourquoi. C'est le mode de défaillance exact que vous décrivez : une valeur plausible, aucune exception, aucune trace.

### C015 - Le proces-verbal etalon du 03/07/2024 est eclate sur quatre types differents ; ses resolutions ne sont pas la ou le modele ira les chercher



- **Silencieux** : oui

- **Preuve** : Le proces-verbal existe au registre sous trois formes. (1) `PVAG_PVAG20240703.pdf.md`, 59 130 caracteres, PV_AG, AUTO_CLASSIFIED - la seule ligne juste. (2) `DIVERS_pv 03072024.pdf`, 58 813 caracteres, le PDF du syndic : Convocation_AG. (3) Le meme PV decoupe en 5 sections, toutes dans le dossier AG du 03/07/2024, section PV : `..._ouverture_et_bureau.pdf` (texte : `PROCES-VERBAL DE L'ASSEMBLEE GENERALE...`) -> Convocation_AG, score 15 ; `..._elections_conseil_syndical_et_resolutions_generales.pdf` -> CR_CS, score 55 sur `NOM:conseil.*syndical` ; `..._travaux_et_appels_de_fonds.pdf` (texte : `Pas de vote car la resolution est rejetee. 40 - Vote des travaux ... Article 24`) -> Appel_Fonds, score 50 sur `NOM:appel.*fonds` ; `..._clause_aggravation_des_charges.pdf` -> PV_AG mais A_RECLASSER ; `..._cloture_et_signatures.pdf` -> Convocation_AG, score 5 sur le seul `MOT:ordre du jour`. Enfin le tableau extrait des decisions, `decisions_AG_20240703.csv` (colonnes numero_question, intitule, decision_estimee) -> Convocation_AG, sur 3 lignes de registre partageant le meme doc_id.

- **Consequence** : Un modele de gouvernance qui filtre `document_type = PV_AG` pour reconstituer les 55 resolutions trouve 10 lignes dont 1 seule est un proces-verbal, et manque : le PDF source du syndic, les 5 sections a granularite page, et le tableau de decisions deja extrait. La section qui porte les votes nominatifs et les tantiemes - la piece la plus sensible du corpus - est rangee en compte rendu de conseil syndical, donc sous un autre regime de diffusion que celui d'un PV d'assemblee.

### C016 - Les voix comptées et la passerelle de l'article 25-1 n'ont aucune colonne dans le modèle des actes : le fait étalon du 04/09 devient irrecalculable après versement



- **Silencieux** : oui

- **Preuve** : Comparaison des schémas, sur données réelles (173 lignes). Le registre `resolutions` porte 29 colonnes, `_actes_schema.ACTE_FIELDS` en porte 26. Seize colonnes du registre n'ont AUCUNE destination : passerelle_citee (renseignée 173/173), passerelle_utilisee (173/173), voix_pour (129/173), base_voix (129/173), voix_contre (99/173), voix_relevees (78/173), duree_mois (57/173), duree_intitule (57/173), decision_actee (27/173), qualifications (19/173), voix_abstention (9/173), montant_seuil (6/173), montant_intitule (6/173), divergences (6/173), position (173/173), numerotation (173/173). Elles ne sont pas non plus dans la zone d'extension : `ATTRIBUTS_CONNUS` déclare sept noms ('base_repartition', 'cle_repartition', 'reference_dossier', 'libelle_majorite_brut', 'piece_jointe_nommee', 'penalite_retard', 'duree_contrat'), aucun ne concerne un vote. Et le commentaire de `attributs_acte` interdit explicitement d'y ranger un invariant : « un fait qui devient invariant [...] doit migrer vers une colonne du noyau ». Un décompte de voix est présent chez les deux cabinets : il n'est ni un variant ni une colonne du noyau. Il n'a nulle part où aller.

- **Consequence** : Le fait établi le 2026-09-04 - avec 4 899 présents sur 10 000, l'article 25 était arithmétiquement hors d'atteinte, aucune des 21 résolutions chiffrées n'atteignant 5 001 - est aujourd'hui reconstituable depuis le registre et ne le sera plus depuis le modèle. C'est le seul contrôle qui aurait distingué « adoptée » de « déclarée adoptée sans atteindre la majorité ». Brancher l'UX sur le modèle avant d'ouvrir ces colonnes revient à câbler l'écran sur la seule couche d'où la preuve a été retirée.

### C018 - Sur donnees reelles, le magasin porte deja trois representations concurrentes de la meme assemblee, et la seule datee est la moins juste



- **Fichier** : `instance reconstruite du 2026-09-04, table `resolutions` de gouvernance.sqlite3 (lecture seule)`

- **Silencieux** : oui

- **Preuve** : Mesure sur copie en lecture seule. 173 lignes pour 55 + 8 resolutions reelles, reparties en quatre ag_id : AG-2024-07-03 (55 lignes, 5 doc_id differents), AG-DOC-7139EDAD85E4 (55), AG-DOC-729CCCF88863 (55), AG-2026-02-26 (8). Les numeros 1 a 7 existent dans 4 groupes a la fois. Comparaison a l'etalon (39 adoptees, 7 rejetees, 8 « Pas de vote », 1 sans issue enoncee) : les deux groupes SANS date tombent exactement juste - 39 / 7 / 8 / 1 VOTE_SANS_FORMULE chacun ; le groupe DATE AG-2024-07-03 rend 38 adoptees, 7 rejetees, 7 « Pas de vote », 2 VOTE_SANS_FORMULE, 1 SANS_ISSUE_TRACEE, soit trois ecarts a l'etalon. La cle primaire (resolution_id, etat, origine) ne voit pas la duplication puisque resolution_id contient l'ag_id. La meme instance en version `tilleul_pseudo_test` donne l'ag_id AG-2024-07-03 au doc_id que l'instance reconstruite appelle AG-DOC-7139EDAD85E4 : le meme document a deux identites d'assemblee selon l'instance.

- **Consequence** : Le probleme que le nouveau modele dit resoudre est deja installe dans la base qu'il va lire, et la version qui obtiendra un acte_id propre et stable est celle qui s'ecarte de l'etalon. Portee dans le lot actes, cette base produira ACTE-AG-2024-07-03-R001, ACTE-AG-SANS-DATE-DOC-7139EDAD85E4-R001 et ACTE-AG-SANS-DATE-DOC-729CCCF88863-R001 : trois actes, deux constats PV_SANS_DATE_LUE, et aucune structure capable de dire qu'ils decrivent la meme assemblee ni laquelle est juste. Un ecran qui compte les resolutions de cette base annoncera un nombre entre 55 et 173 selon la requete.

### C019 - Annexe_AG n'existe pas dans le registre : le motif de nom de fichier `annexe` du type comptable absorbe toutes les annexes d'assemblee



- **Fichier** : `server/src/coproscope/configs/taxonomy.default.yml:112`

- **Silencieux** : oui

- **Preuve** : La regle Annexe_Comptable porte `"motifs_nom_fichier": ["annexe.*comptable", "annexe", "etat_financier"]` - le motif nu `annexe` capture tout nom contenant ce mot, pour 50 points. La regle Annexe_AG (priorite 94, superieure a 78, donc jamais appliquee puisque les priorites sont mortes) porte `annexe.*ag` et `annexe.*assemblee`, qui ne matchent pas `01_Annexe01_...`. Resultat mesure : sur 54 lignes dont le nom contient `annexe`, 52 sont Annexe_Comptable et 2 Convocation_AG ; 0 sont Annexe_AG. Le type Annexe_AG compte 1 seule ligne dans tout le registre canonique, et cette ligne est `matrice_preuves_attendues.csv`, un fichier de travail de CoproScope declenche par `MOT:annexe ag`. 39 des 58 Annexe_Comptable sont declenchees par le seul `NOM:annexe`. Parmi elles : `01_annexe_wegroup.pdf`, `02_annexe_batimex.pdf`, `03_annexe_citerenov.pdf` (des annexes d'entreprises), `index_documents_annexes.csv`, `_analysis_annexes_text_coverage.csv`, `README.md`, une fiche juridique sur la comptabilite de copropriete.

- **Consequence** : Les annexes comptables 1 a 5 du decret comptable, les annexes techniques d'entreprises et les index de travail sont dans le meme sac. Un modele qui compte les annexes comptables d'un exercice compte aussi les devis d'entreprises annexes et ses propres fichiers d'index.

### C027 - La colonne `portee`, dont depend toute la matrice HORS_CONTROLE, n'existe pas dans la source qui alimentera le modele



- **Fichier** : `server/src/coproscope/modules/_actes_typologie.py`

- **Silencieux** : oui

- **Preuve** : Le seul coffre reel des deux instances (tilleul_pseudo_reconstruite, .../vault_local/gouvernance.sqlite3, lu en copie lecture seule) contient UNE table, `resolutions`, 173 lignes, et zero des cinq tables actes_* et zero des onze vues. Ses colonnes: resolution_id, ag_id, doc_id, numero, objet, majorite_annoncee, passerelle_citee, passerelle_utilisee, majorite_appliquee, resultat, voix_*, base_voix, position, numerotation, decision_actee, qualifications, duree_mois, montant_seuil, montant_intitule, duree_intitule, divergences, valide_du, valide_au, etat, origine, confiance. Ni `portee`, ni `montant_autorise`, ni `entreprise`. Mesure de l'effet: 55 actes laisses a portee='ORDINAIRE' rendent 275 cellules ABSENT et 55 NON_APPLICABLE; les memes typees rendent 195 NON_APPLICABLE et 135 ABSENT.

- **Consequence** : Au premier chargement reel, 275 cellules afficheront 'Source manquante' la ou 195 devraient afficher 'Ne s'applique pas'. Le livrable du lot - ne plus mettre les 55 resolutions sur le meme plan - est annule par une colonne absente, sans erreur ni signal. C'est la forme exacte du defaut 'une colonne manquante a rendu 0 constat au lieu de 818'.

### C037 - Le total des charges lu dans une annexe est celui de la dernière colonne, quelle qu'elle soit - sur l'exercice 2025 c'est la colonne 2027



- **Fichier** : `server/src/coproscope/modules/_comptes_extraction_annexe.py:136`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/modules/_comptes_extraction_annexe.py:136 : `total_charges=totaux[-1] if totaux else None`. Mesuré sur les annexes réelles de l'instance reconstruite. Annexe de l'exercice 01/01/2025 → 31/12/2025, cinq colonnes : exercices ['2024','2025','2025','2026','2027'], totaux ['290117.06','300000.00','295349.10','303000.00','303500.00']. La valeur retenue dans `total_charges` est 303 500,00 - la projection 2027 - alors que le réalisé 2025 de cette même annexe est 295 349,10. Écart 8 150,90 EUR, et surtout ce n'est pas un total 2025. Ce qui rend le défaut certain plutôt que probable : la fonction calcule douze lignes plus haut `colonnes[].usage` (« vote du budget » / « approbation des comptes ») et _usage_de:187 refuse prudemment de nommer un usage quand il y a deux libellés pour cinq colonnes - mesuré : les cinq `usage` sont vides. Puis la ligne 136 prend `[-1]` quand même. La prudence de la ligne 127 est annulée par la ligne 136.

- **Consequence** : `total_charges` est la seule valeur que consomment B-4 (égalité des annexes), B-5 (plancher de 5 % du fonds de travaux), B-6 (avance de réserve au sixième du budget) et B-7. Le plancher légal du fonds de travaux serait donc calculé sur 303 500 au lieu du budget de l'exercice contrôlé : 15 175 EUR au lieu de 14 767,46, et un écart réel de 300 EUR passerait pour conforme. Le nombre affiché est un vrai nombre du document : rien à l'écran ne peut le trahir. Le test test_comptes_extraction.py:468 vérifie les cinq totaux de `total_charges_par_colonne` et commente même que « deux colonnes portent 2029 : le budget voté et le réalisé » - puis n'assure jamais `total_charges`. Le test connaît l'ambiguïté et ne teste pas le champ qui la tranche.

### C039 - voix_abstention est un parametre mort



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : oui

- **Preuve** : `voix_abstention` apparait exactement une fois dans le fichier, l.344, dans la signature. Aucune lecture. Mesure: art.24, pour=100 contre=50 abstention=99999, presentes=4899 -> ADOPTEE_CONFIRMEE 66.67 %, identique au cas sans abstention, 0 constat.

- **Consequence** : Le module ne peut pas verifier pour + contre + abstention contre la feuille de presence - le seul controle croise dont il aurait les elements, et celui qui a valide le cabinet B dans la doc (30 725 + 4 570 + 741 = 36 036, arithmetique que j'ai rejouee et qui tombe juste). Un appelant qui passe l'abstention croit legitimement qu'elle sert a quelque chose.

### C040 - DECOMPTE_ABSENT accuse le syndic d'une irregularite pour des resolutions ou il n'y a simplement pas eu de vote



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : oui

- **Preuve** : Le motif rendu l.381-385 est: "le proces-verbal ne publie pas les voix; l'article 17 du decret impose pourtant le resultat du vote sous chaque question". issue_annoncee est recu mais n'est teste que par `.startswith("adopt")` (l.514), et seulement dans la branche article 25. Mesure sur le PV etalon: 11 resolutions sur 55 tombent en DECOMPTE_ABSENT, dont 7 que l'extracteur a qualifiees PAS_DE_VOTE (4 sous l'article 24, 3 sous l'article 25). L'etalon manuel compte 8 "Pas de vote".

- **Consequence** : Une note destinee aux coproprietaires imprimerait 7 irregularites inventees contre le syndic, avec citation d'article a l'appui. C'est exactement la confusion constat/interpretation que le CLAUDE.md interdit dans un rapport d'audit, et elle est produite par le code, pas par le redacteur.

### C041 - Le vote par correspondance amende n'a aucune existence dans le code



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : oui

- **Preuve** : SOURCE_CORRESPONDANCE_AMENDEE et SOURCE_CORRESPONDANCE_PRESENT ont chacune 1 occurrence dans le fichier: leur propre definition. Signature de decompte_resolution: 10 parametres, aucun pour l'amendement en seance ni pour les defaillants assimiles. La doc tranche pourtant (l.211-215): "il faut recalculer, et non refuser de conclure - mais uniquement quand le proces-verbal publie la ligne des defaillants assimiles. Sans cette ligne [...] l'ecran doit alors dire que le controle n'est pas conduit." Mesure de l'ecart, sur les 741 voix du cas cabinet B cite par la doc: art.24 pour=15400 contre=15325 -> ADOPTEE_CONFIRMEE, base 30 725, seuil 15 363, 50.12 %. Apres retrait des 741 favorables devenus defaillants: REJET_CONFIRME, base 29 984, seuil 14 993, 48.89 %.

- **Consequence** : Reponse a la question posee: non, le module ne traite pas le cas ou le PV ne publie pas la ligne des defaillants assimiles - il ne traite pas le cas du tout. Il ne peut ni recalculer quand la ligne existe, ni refuser quand elle manque. Il calcule normalement, et le verdict bascule de l'adoption au rejet sur une variation de 2,4 % de l'assiette, sans un mot. La doctrine est ecrite dans la doc et dans deux constantes; rien ne l'execute.

### C042 - Deux implémentations concurrentes de « quel seuil est en vigueur », dont la seule testée n'est appelée par personne



- **Fichier** : `server/src/coproscope/modules/_resolutions_registre.py:301`

- **Silencieux** : oui

- **Preuve** : `seuils_en_vigueur` (server/src/coproscope/modules/_resolutions_registre.py:301) porte tout le raisonnement calendaire : expiration, seuils concurrents actifs simultanément, drapeau `reprise_seuil_anterieur` qui signale sans la trancher la question juridique du seuil ancien qui reprendrait la main. Elle est couverte par dix assertions dans test_resolutions.py (lignes 262 à 437). Grep sur tout src/ : aucun appelant en production. En face, l'écran appelle sa propre `_seuils_en_vigueur` (server/src/coproscope/web/controle_gouvernance_view.py:122), qui lit la vue `v_actes`, prend `valide_au` et l'imprime comme « butoir ». Elle ne rend aucun verdict d'expiration, ne connaît pas les seuils concurrents, et ne porte pas `reprise_seuil_anterieur`.

- **Consequence** : Le constat mesuré et documenté dans le code - le seuil de consultation du conseil syndical voté pour 24 mois expire, trois assemblées passent dont une seize jours avant, aucune ne le revote - est calculé par la fonction que personne n'appelle. L'écran affiche une date butoir sans dire si elle est franchie. Et sur la période où deux seuils adoptés sont actifs ensemble, l'écran en montre un sans dire qu'il a choisi. C'est le défaut numéro un du produit reproduit en avance, sur la notion qui arme tous les autres contrôles : deux comptages concurrents de la même chose, dont le bon est mort. Un test ne l'attrapera jamais, puisque les tests couvrent justement la branche morte.

### C045 - L'écran annonce 157 points à instruire là où le modèle contient 6 constats ; 154 d'entre eux viennent d'une table de liens vide, et la pastille affirme une exigibilité sur un type non reconnu



- **Fichier** : `server/src/coproscope/web/_controle_gouvernance_constats.py`

- **Silencieux** : oui

- **Preuve** : Versement mesuré (173 actes, table `liens_gouvernance` vide comme dans le produit). `v_constats` rend 6 lignes : 4 ISSUE_NON_ENONCEE, 2 PV_SANS_DATE_LUE. L'écran rend `lead = « 157 points à instruire sur 173 décisions lues »`. Décomposition des pastilles : issue_non_enoncee n=4 (constat réel), avis_manquant n=154 (filtre `{'avis': 'manquante'}`, c'est-à-dire cel_avis_cs='ABSENT'), rejetee n=21, pas_de_vote n=23. Les 154 sont exactement les 154 actes de portée ORDINAIRE, dont la cellule est ABSENT parce qu'aucune ligne n'existe dans `liens_gouvernance`. Le texte de la pastille dit : « décisions soumises à l'avis du conseil syndical sans avis rattaché - la consultation préalable est exigible sur ce type. Aucune pièce ne l'établit. » Or le type n'a justement pas été reconnu. La pastille voisine `acte_sans_execution` dit correctement « le lien entre un acte et un euro n'existe pas encore » : l'honnêteté est présente sur une pastille et absente sur celle qui porte le plus gros chiffre. `lignes_marquees` compte les pastilles de ton 'warn', donc les 154 lignes sont marquées `rompu` et le tableau les affiche en chaîne rompue.

- **Consequence** : Le nombre le plus visible de l'écran, celui du titre et de l'onglet, mesure le vide d'une table du produit et l'énonce comme un manquement de la copropriété, avec un fondement juridique affirmé. Un conseil syndical qui écrit au syndic sur cette base réclame 154 avis pour des résolutions dont beaucoup - les désignations, l'approbation des comptes - n'en exigent aucun. C'est le défaut que la typologie disait avoir corrigé, réintroduit par le chemin du versement.

### C046 - Feuille_Presence_AG : 51 lignes sur 51 sont fausses, toutes declenchees par le seul mot `pouvoirs`



- **Silencieux** : oui

- **Preuve** : Trace de declenchement sur les 51 lignes : `MOT:pouvoirs`, 51 fois sur 51, score 5. Aucune ligne n'est declenchee par `feuille de presence`. Ouverture de 6 pieces : 3 sont des pages OCR du reglement de copropriete de 1956/1960 (`page_001.md` : `ACTE MODIFICATIF du Reglement de copropriete de tilleul_pseudo...`, `page_033.md` : `Les parties elisent domicile...`), 1 est un aide-memoire interne de due diligence syndic, 1 est `matrice_risques.csv` (une matrice de risques d'audit), 1 est `registre_sources_juridiques.csv` dont la ligne loi de 1965 contient `pouvoirs des organes`. Verification complementaire : 0 ligne du registre porte `feuille` et `presence` dans son nom de fichier ; le mot-cle `feuille de presence` ne se declenche que 4 fois dans tout le corpus.

- **Consequence** : Le registre affirme 51 feuilles de presence ; le corpus n'en contient aucune. Le fait etabli qui rend l'article 25 arithmetiquement hors d'atteinte le 03/07/2024 - 4 899 presents sur 10 000 - n'a aucune piece justificative dans le registre. Une interface qui compte les pieces par type annoncera que la presence est abondamment documentee.

### C047 - Releve_Bancaire : 5 lignes sur 5 sont fausses ; la carte professionnelle du syndic devient un releve de compte



- **Silencieux** : oui

- **Preuve** : Les 5 lignes ouvertes une par une. Deux lignes (meme doc_id, deux noms de fichier) : `CHAVISSIMMO / CARTE PROFESSIONNELLE / PERMETTANT L'EXERCICE DE L'ACTIVITE DE : (Loi n 70-9 du 02/01/1970)` - la carte professionnelle du syndic, declenchee par `MOT:compte bancaire` (la garantie financiere la mentionne). Une ligne `CONTRAT_rib 0250.pdf` : un releve d'identite bancaire (`Ce releve est destine a etre remis, sur leur demande, a vos creanciers ou debiteurs...`), declenchee par `NOM:rib` + `MOT:releve bancaire` + `MOT:iban`. Deux lignes sont des CSV de travail interne de l'audit (`flux_rib_commissions_batch4...csv`, `grille_banque.csv` - une grille de points de controle qui contient la chaine `Releve_Bancaire` dans une colonne). Le motif `rib` est de 3 caracteres alphanumeriques, donc `_pattern_matches` le traite en mot entier - ce qui evite `attribution` mais n'evite pas le RIB.

- **Consequence** : Zero releve bancaire dans un corpus de 3447 pieces portant sur la comptabilite d'une copropriete, et le registre en affirme 5. Le controle du compte bancaire separe, qui est le point de controle nomme dans `grille_banque.csv`, s'appuierait sur une carte professionnelle et sur sa propre grille de controle.

### C048 - Convocation_AG : le type absorbe 151 lignes dont 15 seulement portent `convocation` dans leur nom ; echantillon de 16 pieces ouvertes, 0 convocation



- **Silencieux** : oui

- **Preuve** : Distribution des declencheurs sur les 151 lignes : 54 par le seul `MOT:convocation`, 20 par le seul `MOT:ordre du jour`, 26 par `convocation`+`ordre du jour`, 25 par `convocation`+`assemblee generale` ; 7 seulement ont `convocation` dans le nom de fichier. Echantillon aleatoire de 16 lignes, ouvertes : un projet de contrat de pret EcoPTZ, 3 images PNG de page sans aucun texte, un signalement DDPP/DGCCRF, une note d'analyse juridique, un plan d'audit prestataires, deux versions d'un signalement ACPR, un compte rendu de reunion du conseil syndical de fevrier 2023, un texte SignalConso, 4 pages OCR du reglement de 1956, une note de preparation, un dossier technique. Aucune convocation. Les vraies convocations existent bien (5 fichiers dates 2024-02-21, 2025-12-03, 2026-04-29) mais representent moins de 5 % du type. Cas note : `2024-02-21_pouvoir.pdf` et `2024-02-21_formulaire_vote_par_correspondance.pdf` sont classes Convocation_AG avec 0 caractere de texte extrait.

- **Consequence** : Compter les convocations par ce type donne 151 au lieu d'environ 6. Toute regle de completude documentaire ou de comparaison AG precedente / AG actuelle qui s'appuie sur ce type compare des objets qui ne sont pas des convocations.

### C049 - Le meme document, sur quatre exercices consecutifs du second cabinet, tombe dans deux types differents selon un mot present ou absent, l'egalite etant tranchee par la position d'une ligne dans le fichier de configuration



- **Silencieux** : oui

- **Preuve** : Instance du second cabinet, 22 pieces. Quatre paquets comptables de convocation, meme syndic, meme forme : `2023-06-19_AG_PV_Convoc-comptes.pdf` -> Annexe_Comptable ; `2024-06-17_AG_Convoc-comptes.pdf`, `2025-06-30_AG_Convoc-comptes.pdf`, `2026-06-29_AG_Convoc-Comptes.pdf` -> CR_CS. Verification mot par mot : les quatre contiennent `etat financier` (Annexe_Comptable, 5 points) ; les trois derniers contiennent aussi `conseil syndical` (CR_CS, 5 points). Egalite a 5-5 ; CR_CS est ecrite avant Annexe_Comptable dans taxonomy.default.yml, donc `score > best[2]` la conserve. Leur texte commence par `SYNDICAT DES COPROPRIETAIRES (209) / Etat financier apres repartition au 31/12/2024`. Mon rejeu reproduit les 22 lignes du registre a l'identique, donc le mecanisme est bien celui-la.

- **Consequence** : Une serie comptable de quatre exercices se coupe en deux types au milieu, sans aucun signal. Une comparaison annee sur annee - exactement ce qu'un audit de convocation doit produire - portera sur des ensembles differents selon l'exercice, et l'ecart sera lu comme un fait comptable.

### C051 - 69,3 % des lignes du registre sont des derives de traitement, pas des pieces recues, et 400 d'entre elles portent un type documentaire affirme



- **Silencieux** : oui

- **Preuve** : Comptage sur les 3447 lignes : 1835 pages eclatees `page_NNN.*`, 455 sorties de moteur OCR `.tesseract.txt` / `.rapidocr.txt`, 54 images de page `pNN.png`, 26 conversions `.pdf.md` / `.docx.md`, 18 `.ocr.txt`. Total 2388 lignes (69,3 %). Types qu'elles portent : 1988 A_CLASSER, mais aussi 161 Reglement_Copropriete, 60 Convocation_AG, 40 Feuille_Presence_AG, 33 Avoir, 27 Contentieux_Nominatif, 7 PV_AG. Un meme document apparait ainsi jusqu'a trois fois : le PDF, son `.pdf.md`, et une page `page_002.md` accompagnee de son `page_002.tesseract.txt`. Sur les 51 Feuille_Presence_AG, 40 sont des derives.

- **Consequence** : Tout comptage par type mele des pieces et des fragments de traitement de ces memes pieces. `Reglement_Copropriete` compte 179 lignes pour un reglement de 1956 et ses modificatifs : ce sont les pages. Un indicateur "nombre de pieces par type" affiche un volume de traitement, pas un volume documentaire.

### C052 - doc_id n'est pas une cle : 3447 lignes pour 3105 identifiants, 528 lignes partagent leur doc_id avec une autre



- **Silencieux** : oui

- **Preuve** : 3447 lignes, 3105 doc_id distincts, 3105 sha256 distincts : le doc_id derive du contenu, donc deux fichiers de contenu identique mais de nom different produisent deux lignes de meme doc_id. 186 doc_id portent plusieurs lignes, soit 528 lignes concernees. Exemples mesures : `decisions_AG_20240703.csv`, `_clean.csv` et `_clean_utf8.csv` -> 3 lignes, un seul doc_id ; `REDDITION_2023010120230101_1 Etat depenses detaillees.pdf` et `REDDITION_2023010120231231_...` -> 2 lignes, un doc_id ; deux fichiers du dump Gmail portant le meme PDF -> 2 lignes. Deux doc_id portent meme deux types differents : l'un A_CLASSER et Contrat_Maintenance, l'autre A_CLASSER et Contrat_Syndic.

- **Consequence** : Une jointure du modele de gouvernance sur doc_id demultiplie 528 lignes, et pour deux d'entre elles renvoie deux types contradictoires pour le meme identifiant. C'est le meme defaut que les quatre comptages concurrents deja constates : la meme notion, plusieurs valeurs, aucune erreur levee.

### C053 - Deux registres documentaires concurrents coexistent dans l'instance, de schemas et de vocabulaires incompatibles ; un seul est lu par le code



- **Silencieux** : oui

- **Preuve** : `900_Systeme_Audit/.../registers/registre_documents.csv` : 3447 lignes, 47 colonnes - c'est celui que `instance.yml` designe sous la cle `registers.documents`, donc le seul que `classify()` ouvre. `010_Pilotage_Audit/registre_documents.csv` : 309 lignes, 20 colonnes, jamais reference. 3447 + 309 = 3756, le total annonce. Les totaux par type annonces sont eux aussi la somme des deux : PV_AG 10+8=18, Convocation_AG 151+33=184, Facture 401+11=412, Annexe_Comptable 58+45=103, Annexe_AG 1+99=100, A_CLASSER 2111+7=2118. Le registre orphelin porte 7 types que la taxonomie ne sait pas produire : Attestation_Entretien, Compte_Rendu_CS, Contentieux_Sinistre, Etat_Depenses_Detaillees, Etat_Impayes, Fiche_Synthetique, RIB_Compte_Separe. Symetriquement, 8 types definis par la taxonomie ne figurent dans aucun des deux registres : Attestation_Assurance, DOE_Travaux, Declaration_Assurance, Marche_Travaux, Ordre_Service, Photo_Incident, Preuve_Envoi, Reception_Travaux. Les "38 types" sont une coincidence : la taxonomie en definit 38, l'union des deux registres en contient 38, mais ce ne sont pas les memes 38.

- **Consequence** : Le chiffre de reference du corpus (3756 lignes, 38 types) additionne un registre vivant et un registre mort. Annexe_AG en est l'illustration : 99 de ses 100 lignes sont dans le registre que le code n'ouvre jamais ; le registre canonique en contient 1, et c'est un fichier de travail. Brancher l'interface sur le registre canonique fera disparaitre 99 annexes d'AG sans message.

### C056 - Sur données réelles, 154 résolutions sur 173 n'obtiennent aucune portée, et cinq portées du modèle n'ont aucun producteur



- **Silencieux** : oui

- **Preuve** : Colonne `qualifications` du registre réel : vide sur 154 lignes, APPROBATION_COMPTES 7, BUDGET_PREVISIONNEL 6, SEUIL_CONSULTATION_CS 3, SEUIL_MISE_EN_CONCURRENCE 3. Soit 19/173 typées, 11 %. Les deux vocabulaires ne coïncident pas : `_resolutions_qualification.QUALIFICATIONS` déclare 8 noms, `_actes_vocabulaire.PORTEES` en déclare 11, et seuls 4 portent le même nom. MISE_EN_CONCURRENCE_PRODUITE et MANDAT_SYNDIC n'ont pas de portée correspondante ; SEUIL_CONSULTATION_CS et SEUIL_MISE_EN_CONCURRENCE doivent être repliés à la main sur 'SEUIL' (je l'ai fait, rien dans le code ne le fait). Cinq portées n'ont aucun producteur, mesuré à zéro sur le corpus : DESIGNATION_SYNDIC, DESIGNATION_ORGANE, ENGAGEMENT_DEPENSE, AUTORISATION_COPROPRIETAIRE, MODALITES. Or `portees_soumises` montre que ENGAGEMENT_DEPENSE est, avec ORDINAIRE, la seule portée soumise aux contrôles SEUIL_APPLICABLE, DEVIS_RETENU et EXECUTION. Résultat du versement : 154 ORDINAIRE, 7 APPROBATION_COMPTES, 6 BUDGET_PREVISIONNEL, 6 SEUIL, 0 ENGAGEMENT_DEPENSE, 0 DELEGATION_CS.

- **Consequence** : Deux effets opposés et tous deux faux. Les 154 non typées reçoivent les sept contrôles, y compris les vingt-deux désignations, ce que la typologie a précisément été écrite pour empêcher. Et aucune résolution n'est jamais classée ENGAGEMENT_DEPENSE, donc le contrôle d'exécution et le rattachement d'un devis n'ont, sur le corpus réel, aucun sujet : `v_cumul_delegation` rend 0 ligne et le plafond de l'article 21-2 n'est calculé sur rien. La typologie est un raffinement posé sur une couche qui ne sait pas encore typer.





## MOYEN

### C057 - Sur les deux résolutions « sans objet légal », une seule tient pour les deux cabinets



- **Fichier** : `docs/typologie_resolutions_2026-09-04.md`

- **Silencieux** : non

- **Preuve** : Vérifié sur la source. La **clause d'aggravation des charges** : art. 10-1 (LEGIARTI000039313543) commence par « Par dérogation aux dispositions du deuxième alinéa de l'article 10, sont imputables au seul copropriétaire concerné » - imputation de plein droit. Elle est bien votée par les deux cabinets, et encore en 2026 : le PV 2026 du cabinet B porte « RESOLUTION 14 : VOTE DE LA CLAUSE D'AGGRAVATION DES CHARGES / Majorité : Article24 », le PV 2024 du même cabinet aussi, et le PV étalon du cabinet A porte « Adoption de la clause d'aggravation des charges de copropriété », adoptée. Le constat tient. **Les modalités de consultation des pièces justificatives** : décret art. 9-1 (LEGIARTI000038702079) dit « Le syndic fixe le lieu de la consultation des pièces justificatives des charges […] le ou les jours et les heures auxquels elle s'effectue ». Le cabinet A la vote toujours. Le cabinet B ne l'a votée qu'une fois, dans la convocation de 2023 (« Résolution n°20 : Modalités de consultation des pièces comptables (Article 24 - Général) / Conformément à l'article 18-1 de la loi du 10 juillet 1965, l'assemblée générale fixe la consultation… ») ; dans les convocations 2024, 2025 et 2026 le même sujet apparaît sous « Modalités de vérification des pièces justificatives des charges : » comme paragraphe d'information, hors de la liste des résolutions, et il ne figure dans aucun des deux PV exploitables.

- **Consequence** : La note écrit « Les deux cabinets continuent pourtant de les soumettre au vote » pour les deux points. C'est exact pour l'un, dépassé pour l'autre : le second cabinet a cessé de le voter après 2023. Publié tel quel dans une note au conseil syndical, ce serait un reproche adressé à un syndic qui a déjà corrigé - le genre d'erreur qui coûte la crédibilité des reproches fondés.

### C058 - 29 des 112 mots-cles de la taxonomie ne se declenchent jamais sur 3447 documents



- **Fichier** : `server/src/coproscope/configs/taxonomy.default.yml`

- **Silencieux** : oui

- **Preuve** : Comptage exhaustif des declenchements par mot-cle sur les 3447 documents : 29 mots-cles a 0. Parmi eux, ceux qui portent l'essentiel du sens de leur type : `resolution adoptee` (PV_AG), `annexe a la convocation` et `document joint a l'assemblee` (Annexe_AG), `mandats de vote` (Feuille_Presence_AG), `compte rendu du conseil syndical` (CR_CS), `coproprietaire debiteur` (Impayes), `appel de charges` (Appel_Fonds), `fonds alur` (Fonds_Travaux), `journal comptable` (Grand_Livre), `liste des depenses` (Etat_Depenses), `budget propose` (Budget_Previsionnel), `declaration de sinistre` et `sinistre assurance` (Declaration_Assurance, type qui n'existe dans aucun registre), `dossier des ouvrages executes` et `garantie de parfait achevement` (DOE_Travaux, idem), `cahier des clauses` et `marche de travaux` (Marche_Travaux, idem), `reception des travaux` et `proces-verbal de reception` (Reception_Travaux, idem). Six de ces 29 se declencheraient si les accents etaient neutralises (`marche de travaux` 16 fois, `reception des travaux` 5, `proces-verbal de reception` 3).

- **Consequence** : Chaque type repose en pratique sur un ou deux mots communs et non sur la locution qui le definit. Le bareme donne l'apparence d'un faisceau d'indices ; la mesure montre un seul indice, souvent le plus faible. C'est ce qui rend 520 lignes (15,1 %) decidees par 5 points.

### C061 - Deux vocabulaires de résultat se ratent : 7 résolutions sans majorité énoncée produisent 0 constat, et 4 résolutions sans issue tracée n'ont aucun constat du tout



- **Fichier** : `server/src/coproscope/modules/_actes_constats.py`

- **Silencieux** : oui

- **Preuve** : Le constat MAJORITE_NON_ENONCEE filtre `WHERE a.majorite_annoncee = 'NON_ENONCEE'` - la valeur déclarée `MAJORITE_NON_ENONCEE` du vocabulaire des actes. Le registre réel écrit la chaîne vide : 7 lignes sur 173 ont `majorite_annoncee = ''`, aucune ne vaut 'NON_ENONCEE'. Mesuré après versement : `v_constats` rend 4 ISSUE_NON_ENONCEE et 2 PV_SANS_DATE_LUE, et zéro MAJORITE_NON_ENONCEE, alors que 7 résolutions n'annoncent aucune majorité. Le commentaire de `_actes_schema` cite pourtant ce cas comme mesuré : « y compris sa valeur NON_ENONCEE, mesurée une fois sur 55 au 03/07/2024 ». Séparément : le vocabulaire déclare `RESULTAT_SANS_ISSUE = 'SANS_ISSUE_TRACEE'` (4 lignes réelles), et aucune branche de `v_constats` ne le vise ; la matrice le range en cel_resolution='ABSENT', une cellule grise parmi 1 038 autres.

- **Consequence** : Le seul cas que l'étalon isole explicitement - la résolution dont le procès-verbal n'énonce jamais l'issue - traverse tout le modèle sans produire une seule ligne de travail. Et l'absence de majorité annoncée, qui est la condition préalable de tout contrôle de majorité, ne se signale pas non plus. Deux constats déclarés, testés dans le code, et muets sur les données réelles parce que la chaîne attendue n'est pas celle qui est écrite en amont.

### C062 - Le type « fonds de travaux » cite l'article du plan pluriannuel, pas celui du fonds de travaux



- **Fichier** : `server/src/coproscope/modules/_actes_typologie.py`

- **Silencieux** : oui

- **Preuve** : `FONDEMENT_PORTEE[PORTEE_FONDS_TRAVAUX]` = (« alimente le fonds de travaux ou arrete le plan pluriannuel de travaux », ((« loi 65-557 art. 14-2 », « LEGIARTI000043977289 »),)) - une seule source pour deux objets. Lu sur Légifrance, LEGIARTI000043977289 est bien l'article 14-2, dont la première phrase est « A l'expiration d'un délai de quinze ans à compter de la date de réception des travaux de construction de l'immeuble, un projet de plan pluriannuel de travaux est élaboré ». La cotisation annuelle au fonds de travaux est l'article 14-2-1 (LEGIARTI000043967792), qui n'est cité nulle part dans le dépôt.

- **Consequence** : Mesuré : 5 résolutions du cabinet B sont typées FONDS_TRAVAUX, majoritairement sur des libellés du genre « vote de la dotation fonds de travaux loi ALUR : 5 % » - c'est-à-dire sur la moitié du type qui n'a pas de source. Ces 5 résolutions perdent seuil, avis, devis, exécution et rapport CS. Le retrait reste défendable au fond (une réserve ne passe pas de marché), mais la pièce censée le rendre vérifiable renvoie à autre chose.

### C070 - La branche article 26 ne confronte aucun denominateur imprime et ne signale aucun seuil hors d'atteinte



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : oui

- **Preuve** : _constat_denominateur n'est appele qu'aux l.454 et 485. La branche ASSIETTE_DOUBLE (l.392-429) ne l'appelle pas, et n'appelle pas non plus majorite_25_atteignable. Mesure: art.26, voix_pour=7000, voix_totales=10000, denominateur_ecrit=4899, membres=120, votants_pour=80 -> ADOPTEE_CONFIRMEE, 70.0 %, 0 constat. Idem avec voix_presentes=4899: toujours 0 constat.

- **Consequence** : La promesse centrale du module - "le denominateur imprime est confronte et produit un constat en cas d'ecart", doc l.473 - tient sur 3 regimes sur 4. L'article 26 est justement celui ou le seuil est le plus haut (deux tiers) et ou une presence faible le rend le plus surement inatteignable. Aucun avertissement.

### C071 - "CONFIRMEE" affirme un accord avec le proces-verbal qui n'est teste que sous l'article 25



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : oui

- **Preuve** : issue_annoncee n'est lu qu'a la l.514, dans la seule branche TOUTES_LES_VOIX. Mesure: art.24, voix_pour=100, voix_contre=10, issue_annoncee="Rejetee" -> ETAT_ADOPTEE_CONFIRMEE. Sur le PV etalon la contradiction ne se realise pas: 27 accords ADOPTEE/ADOPTEE_CONFIRMEE, 1 REJETEE/REJET_CONFIRME sous l'article 24, 3 sous l'article 25, 0 desaccord.

- **Consequence** : Le mot CONFIRMEE promet une comparaison qui n'a pas eu lieu. Il n'existe aucun etat pour "le decompte contredit l'issue proclamee" hors article 25, alors que c'est le constat le plus utile qu'un outil de controle puisse produire. Defaut latent: reel dans le code, non declenche sur cette piece.

### C072 - Le vocabulaire des majorites n'est pas celui de l'extracteur, et le refus ment sur son motif



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : oui

- **Preuve** : REGIMES reconnait 4 cles: "24", "25", "25-1", "26". MAJORITE_RE dans _resolutions_motifs.py capture `2[3456](?:-1)?`, donc aussi "23", "24-1", "26-1". L'etalon compte par ailleurs 1 resolution sous "article 25B". Mesure: regime_de_majorite() rend None pour "25B", "25 B", "25b", "23", "24-1", "26-1", "Article 24", "art. 25". Le verdict rendu est alors ASSIETTE_INDETERMINEE, motif "la majorite applicable n'est pas enoncee; l'assiette du decompte en depend et ne peut pas etre supposee" (l.369-372).

- **Consequence** : Le refus est prudent, mais son motif est faux: la majorite EST enoncee au proces-verbal, elle n'est pas reconnue par la table. Un lecteur conclut a un defaut du document alors que le defaut est dans l'outil - la meme inversion que le classement qui etiquette 15 PV_AG pour une assemblee. Une seule cle de dictionnaire manquante suffit a transformer un controle en accusation.

### C073 - 24 des 55 resolutions du proces-verbal etalon ne rendent aucun chiffre, et 12 perdent au passage un denominateur qui etait lu



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : oui

- **Preuve** : Rejoue sur le PV du 03/07/2024 avec voix_totales=10000 et voix_presentes=4899: 24 verdicts sur 55 (43,6 %) ont pourcentage=None - 13 ASSIETTE_INDETERMINEE, 11 DECOMPTE_ABSENT. Parmi ces 24, 12 avaient un denominateur imprime correctement extrait (base_voix) qu'aucun verdict ne restitue: les returns de refus l.435-452 et l.377-387 ne passent pas `constats` et n'appellent jamais _constat_denominateur. Les 11 ASSIETTE_INDETERMINEE sous l'article 24 viennent tous d'une meme cause: les voix contre ne sont pas publiees.

- **Consequence** : Chiffre a connaitre avant de brancher l'UX: sur la piece de reference, pres d'un ecran de resolution sur deux n'a rien a afficher. Et l'information qui existait - le denominateur imprime, les 5 bases distinctes relevees sur ce seul PV: 10000 (25 fois), 4899 (6), 1155 (10), 968 (2), absent (12) - est jetee au lieu d'etre montree au lecteur comme piste.

### C075 - Le sondage ne lit que les 6000 premiers caracteres et y melange nom de fichier, chemin et contenu dans une seule chaine



- **Fichier** : `server/src/coproscope/modules/_docuscope_parts/01_inventory_and_extraction.py:558`

- **Silencieux** : oui

- **Preuve** : `_text_sample` construit `parts = [row["file_name"], row["original_path"]]` puis y ajoute `path.read_text(...)[:6000]` du texte et 6000 caracteres du docling, et retourne la concatenation en minuscules. `_classify` passe cette chaine unique a `_keyword_matches` : un mot present dans un segment de chemin compte donc comme preuve de contenu, au meme poids. Mesure : dans le registre canonique, 227 lignes (6,6 %) se trouvent sous les zones de travail internes de l'audit (290_Audit_360, 010_Pilotage_Audit, 900_Systeme_Audit, 000_LIRE_AVANT_USAGE) et 198 d'entre elles portent un type documentaire affirme - dont 24 CR_CS, 20 Contrat_Syndic, 17 Convocation_AG, 9 Facture, 8 Feuille_Presence_AG. Par ailleurs le PV de 59 130 caracteres et la convocation de 426 608 caracteres sont juges sur leurs 6000 premiers.

- **Consequence** : Les fichiers de travail de l'audit lui-meme entrent dans le corpus documentaire avec le meme statut que les pieces recues du syndic. Une grille de controle qui contient la chaine `Releve_Bancaire` devient un releve bancaire ; une matrice de risques devient une feuille de presence.

### C076 - La majorité « 25B » est ramenée à « 25 » : la lettre qui sépare les régimes de l'article 25 est effacée sans trace



- **Fichier** : `server/src/coproscope/modules/_resolutions_motifs.py`

- **Silencieux** : oui

- **Preuve** : `_resolutions_motifs.py:120` : `MAJORITE_RE = re.compile(r"articles?\s*(?:n[°o]\s*)?(2[3456](?:-1)?)", re.IGNORECASE)`. Le PV étalon écrit, sur la résolution d'autorisation à un copropriétaire, « Article 25B) majorité absolue des tantièmes de… » ; la résolution ressort avec `majorite_annoncee == '25'`. Mesure sur les 55 : 29 fois '24', 24 fois '25', 2 fois ''. L'étalon établi à la main attend 30 article 24, 23 articles 25 et 25-1, **1 article 25B**, 1 non énoncée. Le 25B a été absorbé dans le 25, et une majorité article 24 est ressortie vide.

- **Consequence** : Toute la typologie repose sur la distinction entre l'article 25 b (autorisation donnée à un copropriétaire, qui perd quatre contrôles) et l'article 25 c (désignation, qui en perd d'autres). Le seul champ capable de porter cette distinction telle que le procès-verbal l'écrit l'a effacée. Le contrôle « majorité annoncée contre majorité requise » que le schéma annonce en commentaire ne pourra jamais les séparer, et le comptage des majorités ne correspond plus à l'étalon.

### C077 - Un except Exception nu rend « aucune autorisation identifiée » pour toute dépense, quelle que soit la panne



- **Fichier** : `server/src/coproscope/modules/actes_autorisation.py:194`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/modules/actes_autorisation.py:194-195 : `except Exception: return []`. C'est la fonction qui répond à « cet euro, qui l'a autorisé ? ». Son propre docstring, quatre lignes plus haut, dit : « Une liste vide n'est pas *pas d'autorisation* : c'est *aucune autorisation identifiée* ». Le except avale les deux. À quarante lignes de là, _actes_store.lire_vue:150-162 fait exactement l'inverse : il ne rattrape que `no such table` et laisse remonter le reste, en expliquant qu'un `no such column` avalé « rend une liste vide indiscernable d'une absence de résultat ». La bonne règle est écrite dans le module voisin et n'a pas été appliquée ici. Accessoirement, `connexion()` appelle `_connect` qui fait `mkdir` puis `sqlite3.connect` : ouvrir cette page sur une instance sans coffre crée un fichier de base vide, ce qui fait basculer `diagnostiquer` de « aucun procès-verbal déposé » vers « le modèle n'a jamais été alimenté ». Une lecture change l'état affiché.

- **Consequence** : Après une dérive de schéma, chaque fiche de dépense affichera « aucune autorisation identifiée » - une phrase qui a l'air d'un constat sur la copropriété alors que c'est une panne de l'outil. C'est le précédent que vous citez : un return [] d'une ligne qui vide des écrans.

### C078 - _reset_schema n'efface pas une table etrangere : le motif ecrit dans la doctrine est faux



- **Fichier** : `server/src/coproscope/vault/_reconstruction_parts/02_schema.py, cite par CLAUDE.md et par les docstrings de gouvernance_store.py et _actes_schema.py`

- **Silencieux** : oui

- **Preuve** : Mesure. _reset_schema execute une liste fermee de 25 DROP TABLE IF EXISTS nommes, puis recree ; aucun code du dossier vault ne supprime le fichier de cache (0 occurrence de unlink/os.remove). Test : base reconstruite a vide, ajout d'une table `resolutions_hors_journal` avec une ligne, puis rebuild complet par rebuild_cache_from_events -> la table existe toujours et sa ligne est conservee. La meme structure vaut pour local_reconstruction (liste de 5 DROP nommes).

- **Consequence** : L'arbitrage « SQLite dedie, jamais la base de reconstruction » reste juste, mais il est tenu pour un motif que la mesure contredit : une table etrangere n'est pas effacee, elle SURVIT et se desynchronise des donnees rebaties autour d'elle. Le risque reel est une table rescapee qui continue de repondre avec des donnees d'avant le rebuild - plus difficile a voir qu'une disparition. Une doctrine defendue par une raison fausse cede des qu'on la reexamine.

### C081 - L'alinéa cité est faux dans les 36 occurrences, y compris dans le renvoi affiché à l'écran



- **Fichier** : `server/src/coproscope/web/_controle_gouvernance_source.py`

- **Silencieux** : oui

- **Preuve** : Lu sur Légifrance, l'article 21 de la loi 65-557 a pour deuxième alinéa « En outre, il donne son avis au syndic ou à l'assemblée générale sur toutes questions concernant le syndicat, pour lesquelles il est consulté ou dont il se saisit lui-même. » Le seuil de consultation du conseil syndical est l'alinéa suivant, la mise en concurrence celui d'après. Le dépôt cite « art. 21 al. 2 » ou « article 21 alinéa 2 » 36 fois dans `server/src` et dans la note de lot : dans `FONDEMENT_PORTEE[PORTEE_SEUIL]`, dans huit motifs de `HORS_CONTROLE`, dans `_actes_vues.py`, `_actes_requetes.py`, `_resolutions_qualification.py`, et dans `web/_controle_gouvernance_source.py` où la chaîne `legifrance="Loi 65-557, article 21 alinéa 2"` est portée par la bulle que le lecteur voit.

- **Consequence** : Un conseil syndical qui suit le renvoi tombe sur l'avis général du conseil syndical et non sur le seuil, et conclut que l'outil se trompe - sur une cellule où il a raison. Le coût est la crédibilité de l'ensemble des cellules, y compris les fondées.

### C082 - Le dédoublonnage des lectures concurrentes d'un même procès-verbal vit dans une seule vue, pas dans le magasin



- **Fichier** : `server/src/coproscope/web/_resolutions_assemblees.py:114`

- **Silencieux** : oui

- **Preuve** : Mesuré sur le coffre réel : la table `resolutions` porte 173 lignes, dont 165 sont trois lectures de la même assemblée du 03/07/2024 sous trois `ag_id` différents. L'un d'eux, `AG-2024-07-03`, est une mosaïque de quatre documents de quatre types différents - un fragment étiqueté PV_AG (9 résolutions), un compte-rendu de conseil syndical (23), une convocation (7) et un appel de fonds (16) - dont la somme fait 55 et annonce 38/7/7. Les deux autres sont des lectures complètes à 39/7/8. `_resolutions_assemblees` fait le travail correctement et l'écran rend 39/7/8 : c'est mesuré, et c'est pourquoi ce n'est pas un bloquant. Mais le regroupement est du code de vue (server/src/coproscope/web/_resolutions_assemblees.py), pas du code de magasin. `gouvernance_store.lire` rend les 173 lignes brutes à qui les demande.

- **Consequence** : Tout futur consommateur - un export, un rapport, un décompte de voix, l'écran de contrôle - qui appelle `lire()` sans passer par `_resolutions_assemblees` triple-comptera la même assemblée, et son total sera 173 là où l'écran des résolutions dit 63. La coïncidence rend le piège plus sûr : la mosaïque totalise exactement 55, le chiffre de l'étalon, et ne diverge que sur deux résolutions. Un développeur qui vérifie « 55, c'est bon » validera une valeur juste obtenue en soudant un compte-rendu de conseil syndical et un appel de fonds sur un fragment de procès-verbal.

### C083 - traces_controle est lue par la colonne « Ma conclusion » et aucune route n'écrit dedans : il n'existe qu'un GET



- **Fichier** : `server/src/coproscope/web/controle_gouvernance_route.py`

- **Silencieux** : non

- **Preuve** : `register_controle_gouvernance_routes` ne déclare qu'un `@app.get("/controle-gouvernance")`. Aucun POST, aucun formulaire d'écriture dans le module. `controle_gouvernance_view.py:96` lit `A.lire_table(instance, A.TABLE_TRACES)` et `_controle_gouvernance_source.CONCLUSIONS` déclare quatre valeurs ('a_instruire', 'QUESTION_POSEE', 'CONTROLE_TRACE', 'RESERVE') ; la ligne 460 replie toute valeur inconnue sur 'a_instruire'. Mesuré après versement : 0 ligne dans `traces_controle`, `conclus=0` sur toutes les pastilles. `_actes_store.ecrire` accepterait la table (doc_ids vide n'efface rien, le mécanisme est prévu) mais rien ne l'appelle.

- **Consequence** : L'utilisateur qui a instruit une ligne - appelé le syndic, obtenu la pièce, posé une réserve - ne peut rien en dire à l'outil. Au rechargement, les 157 points sont toujours 157. Le compteur « conclus » de chaque pastille affichera éternellement 0, ce qui se lit comme « personne n'a rien traité » et non comme « l'outil ne sait pas l'enregistrer ». C'est la sortie de la boucle de travail qui manque, pas une commodité.

### C085 - Le garde-fou « pas de citation de mémoire » ne vérifie que la forme de l'identifiant, et les motifs de retrait n'en portent aucun



- **Fichier** : `server/tests/test_resolutions_typage.py`

- **Silencieux** : oui

- **Preuve** : `tests/test_resolutions_typage.py`, classe PasDeCitationDeMemoireTests : `MOTIF = re.compile(r"LEGIARTI\d{12}")` puis `self.assertRegex(ident, self.MOTIF)`. Une chaîne comme LEGIARTI000000000000 passerait. Ce test n'a attrapé aucun des constats 1, 4 et 5. Par ailleurs les motifs de `HORS_CONTROLE` - la partie opératoire, celle qui retire effectivement le contrôle et qui s'affiche à l'écran - ne portent aucun identifiant : ils citent « l'article 21 al. 2 », « l'article 18 II », « le decret art. 11 I », « decret art. 22 al. 2 » en clair. Seules les définitions de type, qui ne décident rien, sont sourcées.

- **Consequence** : Le dispositif de vérification est placé là où il ne décide de rien, et absent là où il décide. C'est exactement pourquoi le motif faux du constat 1 a pu être écrit et testé sans qu'aucun contrôle ne le rencontre.

### C087 - La discordance intitulé/corps que le registre vient d'apprendre à détecter n'a aucune place dans le modèle : le montant retenu s'affiche seul



- **Silencieux** : oui

- **Preuve** : Registre réel, colonne `divergences`, 6 lignes renseignées, toutes sur deux résolutions : n°26 « montant: intitule 2000.00 / corps 1000 » et n°27 « duree: intitule 24 mois / corps 36 mois ». `ACTE_FIELDS` ne contient ni `divergences`, ni `montant_intitule`, ni `duree_intitule`, ni `duree_mois`, et `ATTRIBUTS_CONNUS` ne les nomme pas. Mesure du panneau des seuils après versement : la résolution 26 s'affiche « 1 000,00 EUR », sans aucune mention que le même document annonce 2 000 dans son intitulé ; la résolution 27 s'affiche avec « butoir 2027-07-03 », soit une fenêtre de 36 mois, sans mention que l'intitulé dit 24 mois. Par ailleurs `grep -rn divergences` montre qu'aucun écran ni aucune vue d'actes ne lit cette colonne aujourd'hui : elle est écrite et consommée nulle part. (`v_divergences_humaines` porte un nom voisin mais traite d'autre chose : l'écart EXTRAIT / CORRIGE_HUMAIN.)

- **Consequence** : Le commit le plus récent de la voie résolutions - « le corps fait foi sur le seuil, la discordance devient un constat » - produit une information que la couche suivante ne sait pas recevoir. Elle est déjà perdue avant l'écran, et elle le sera définitivement au versement. Un seuil affiché comme un fait unique, quand le document en énonce deux, est précisément la valeur plausible que ce produit doit refuser de rendre.

### C088 - Deux des six constats réels ne sont affichés nulle part : PV_SANS_DATE_LUE n'a ni pastille ni rubrique hors écran



- **Silencieux** : oui

- **Preuve** : Après versement, `v_constats` rend 6 lignes dont 2 PV_SANS_DATE_LUE (sujet_kind='document', une par document sans date lue, portant 110 actes au total). L'écran : `C.CONSTATS` déclare douze pastilles, aucune ne filtre sur PV_SANS_DATE_LUE ; `CONSTATS_HORS_ECRAN` en déclare trois (EURO_SANS_ACTE, IMPUTATION_A_TRANCHER, TVA_INCOHERENTE) et n'inclut pas non plus PV_SANS_DATE_LUE. Mesuré : `_hors_ecran()` rend une liste vide. Le fait n'est pas totalement muet - le bloc « limites » ajoute une phrase « N actes sont rattachés à une assemblée dont la date n'a pas été lue » - mais il est rangé en note de bas de page, hors du décompte des points à instruire, alors que 110 actes sur 173 sont concernés.

- **Consequence** : Le constat qui explique la triple présence de la même assemblée est celui qui ne remonte pas. Un lecteur voit trois fois la résolution n°7 dans le tableau et n'a, dans la file de travail, aucune ligne qui lui dise pourquoi. Un constat produit par le modèle et jamais routé vers l'écran est une perte inter-couche pure : il coûte le calcul et ne rend rien.

### C089 - Aucune ancre de preuve ne peut être versée : page et ancre sont vides sur 173 lignes, et « Source disponible » est affiché sur 165 d'entre elles



- **Silencieux** : oui

- **Preuve** : `ACTE_FIELDS` déclare `page` et `ancre`. Le registre `resolutions` n'a ni l'une ni l'autre parmi ses 29 colonnes : le versement les laisse vides, mesuré 0/173. Or `v_matrice_gouvernance` fixe `cel_resolution = 'PIECE_PRODUITE'` sur le seul examen de `a.resultat` (ADOPTEE, REJETEE ou PAS_DE_VOTE) : mesuré, 165 lignes sur 173 affichent « Source disponible ». `grep -n 'ancre'` dans `controle_gouvernance_view.py` et `_controle_gouvernance_source.py` ne rend aucune occurrence : l'écran ne lit pas ces colonnes et n'offre donc aucun renvoi à la page du procès-verbal.

- **Consequence** : « Source disponible » signifie ici « le document a écrit un mot que la machine a reconnu », pas « voici où le vérifier ». Un contrôleur qui clique n'a rien à ouvrir. Pour un produit dont la promesse est la traçabilité pièce par pièce, l'affirmation la plus fréquente à l'écran est celle qui n'est adossée à aucune référence - et rien ne le signale, puisque la colonne vide n'est jamais rendue.





## MINEUR

### C091 - Le module des constats désigne le mauvais module comme source de la matrice, et n'en applique qu'un septième



- **Fichier** : `server/src/coproscope/modules/_actes_constats.py`

- **Silencieux** : non

- **Preuve** : Docstring de `_actes_constats.py` : « La reponse n'est pas une exception codee en dur ici. C'est `_actes_vocabulaire.HORS_CONTROLE`, une matrice portee x controle […] Ce module ne fait que la traduire en `IN (...)` ». HORS_CONTROLE est dans `_actes_typologie`, pas dans `_actes_vocabulaire`. Et l'import réel du module est `from ._actes_typologie import CTRL_EXECUTION, portees_soumises` : un seul contrôle sur sept borne effectivement un constat. Les cinq autres n'existent que comme cellules de matrice, et MAJORITE n'est borné par rien.

- **Consequence** : Un lecteur qui veut prendre la matrice en défaut va au mauvais fichier, et croit que les sept contrôles sont bornés alors qu'un seul l'est. C'est le genre d'écart entre le commentaire et le code qui rend un audit ultérieur plus lent qu'il ne devrait l'être.

### C092 - Les operateurs `vide` et `non_vide` ignorent silencieusement la valeur fournie



- **Fichier** : `server/src/coproscope/modules/_actes_requetes.py`

- **Silencieux** : oui

- **Preuve** : _actes_requetes.construire_where: le gabarit de `vide` est "= ''" et ne contient pas de '?', donc la valeur n'est ni liee ni refusee. Mesure: construire_requete([('date_effet','vide','2024-07-03')]) rend ("SELECT * FROM \"v_actes\" WHERE \"date_effet\" = ''", []).

- **Consequence** : Un appelant qui se trompe d'operateur obtient une requete valide qui repond a une autre question que la sienne. Le module refuse un filtre non declare et un operateur non autorise, mais accepte un critere dont la valeur est jetee.

### C094 - Trois vocabulaires du même schéma partagent des valeurs, et la traduction vers l'écran retombe silencieusement sur « Source manquante »



- **Fichier** : `server/src/coproscope/modules/_actes_vocabulaire.py`

- **Silencieux** : oui

- **Preuve** : Croisement mesuré des onze vocabulaires de `_actes_vocabulaire` : `PORTEES ∩ IMPUTATIONS = {'BUDGET_PREVISIONNEL', 'FONDS_TRAVAUX'}`, `SOURCES_AFFIRMATION ∩ FORCES = {'ABSENT'}`, `FORCES ∩ TVA_REGIMES = {'NON_APPLICABLE'}`. Côté écran, `web/_controle_gouvernance_source.py` : `statut = FORCE_VERS_STATUT.get(valeur, "manquante")` - toute valeur inconnue devient « Source manquante ». Et `_fonde` appelle `_cellule(ligne["cel_resolution"], portee, "RESOLUTION", …)` avec un nom de contrôle qui n'est pas dans `CONTROLES`.

- **Consequence** : Le point demandé - nature contre portée - est propre. Mais une valeur venue du mauvais vocabulaire ne lève rien : elle devient une pièce manquante plausible, c'est-à-dire une diligence à faire là où il n'y en a pas. Aujourd'hui les colonnes concernées vivent sur des tables différentes, donc l'effet n'est pas atteint ; c'est un piège posé, pas un défaut actif.

### C095 - Aucune vue n'expose le desaccord entre deux assertions, et la colonne `doute` n'est lue par aucune vue



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py (NOMS_VUES) et _actes_schema.py (LIEN_FIELDS)`

- **Silencieux** : oui

- **Preuve** : Mesure : les 11 vues creees sont exactement les 11 declarees dans NOMS_VUES (aucune vue orpheline non re-creee), et aucune ne porte sur la contradiction entre provenances. Quand deux assertions divergent sur force_probatoire, _cellule() en choisit une par ORDER BY sur la provenance puis sur la force, LIMIT 1 : la cellule affiche un statut unique et rien ne dit qu'une autre provenance en affirmait un autre. La colonne `doute` de liens_gouvernance n'apparait que dans une requete brute de _actes_requetes.py:244, dans aucune des 11 vues et dans aucun constat.

- **Consequence** : v_divergences_humaines rend visible le desaccord machine/humain sur un acte ; il n'existe pas d'equivalent pour le desaccord syndic/CoproScope/humain sur un lien, alors que c'est le motif explicite de la provenance dans la cle. Le desaccord est stocke, puis tranche en silence a l'affichage.

### C099 - Deux except Exception et un except ValueError qui dégradent l'élection de la version qui fait foi



- **Fichier** : `server/src/coproscope/web/_resolutions_assemblees.py:216`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/web/_resolutions_assemblees.py:216 et 222 : `except Exception: return {}` sur la lecture du registre documentaire. Le dictionnaire vide fait traiter toutes les pièces comme des originaux (ligne 230 : `formes.get(doc_id, PIECE_ORIGINE)`), ce qui désactive silencieusement le deuxième critère d'élection - l'original prime sur sa conversion texte. Ligne 249 : `except ValueError: continue` sur `int(ligne.get("numero"))` retire la résolution de `objets`, donc de `numeros`, donc de la couverture de série qui est le premier critère d'élection (ligne 160).

- **Consequence** : Sur une instance dont le registre documentaire est illisible, l'élection se fait sur des critères dégradés sans que rien ne le dise, et c'est peut-être la conversion markdown qui l'emporte sur le PDF d'origine. Un numéro non numérique fait sous-estimer la couverture d'une attestation et peut faire élire un document moins complet. La ligne reste dans `lignes` et s'affiche : l'incohérence est interne, invisible.

### C100 - Les deux résolutions non typées du PV étalon sortent sans aucun indice, et le test qui couvre ce cas ne reproduit pas le corpus



- **Fichier** : `server/tests/test_resolutions_typage.py`

- **Silencieux** : oui

- **Preuve** : `test_des_travaux_sans_prix_ecrit_restent_non_determines` utilise le libellé « 33 - Vote des travaux de deplacement d'un ouvrage situe sur l'ancienne entree de la residence » et vérifie l'indice « aucun montant ». Le procès-verbal réel écrit « Vote de la décision de reculer la barrière qui se trouve avant le jeu de boules… » : mesuré sur le segment réel, aucune occurrence de « travaux », aucun montant, `ENGAGEMENT_RE` ne déclenche pas, et `portee_resolution` rend `('ORDINAIRE', [])` - liste d'indices vide. Idem pour la résolution 34. La note de lot dit d'ailleurs correctement que ces deux résolutions n'écrivent pas le mot « travaux » ; c'est le fixture du test qui l'ajoute.

- **Consequence** : Les 2 seules résolutions non typées du PV étalon arrivent à l'écran en « Type non reconnu » sans une ligne expliquant pourquoi, alors que le module promet « c'est le seul cas où l'écran a le droit de se tromper, et il doit le dire ». La branche qui dit quelque chose est testée ; la branche que le corpus emprunte ne l'est pas.

### C101 - Facture (401 lignes) tient, mais par une convention de nommage d'un seul versement, pas par le classifieur



- **Silencieux** : non

- **Preuve** : Echantillon aleatoire de 14 lignes ouvertes : 14 sont bien des factures fournisseurs (entreprises de travaux, telephonie, controle d'acces, ventilation). Toutes proviennent d'un meme dump, avec des noms de la forme `Facture_<horodatage>.pdf`. Declencheurs mesures sur les 401 lignes : 244 par `NOM:facture`+`MOT:facture`, 107 en ajoutant `total ttc`, 43 en ajoutant `net a payer`, et 7 par le seul `MOT:facture` sans le nom. Sur les 14 ouvertes, 3 n'ont aucun texte exploitable (uniquement des marqueurs de page) et sont pourtant AUTO_CLASSIFIED ; au total 73 Facture sont typees sans aucun texte lu.

- **Consequence** : La bonne tenue de ce type ne prouve rien sur le classifieur : elle prouve qu'un versement a ete nomme proprement en amont. Le jour ou les factures arrivent sous un autre nom, le type retombe sur le mot `facture` present dans le corps, qui se declenche 486 fois dans tout le corpus, y compris dans des devis, des courriers et des grilles de controle.