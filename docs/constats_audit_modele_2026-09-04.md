# Les 101 constats de l'audit du modele - 2026-09-04



Source: audit adversarial de sept dimensions, 312 agents. Chaque constat a ete

soumis a trois sceptiques sous des angles differents - refaire la mesure, verifier

que la consequence suit du fait, chercher si le defaut est deja traite ailleurs.

49 ont survecu, 52 ont ete refutes. La synthese n'a pas tourne, la limite de

session ayant ete atteinte; ce fichier est la reprise du journal.



**101 constats** - 17 bloquants, 39 graves, 33 moyens, 12 mineurs. **96 silencieux.**





## BLOQUANT



### C001 - Le contrat de filtrage se contourne par le parametre `ordre`, qui est du SQL brut



- **Fichier** : `server/src/coproscope/modules/_actes_requetes.py`

- **Silencieux** : oui

- **Preuve** : _actes_requetes.construire_requete: `sql += f" ORDER BY {ordre}"`, sans aucune validation. _actes_store.lire_vue expose ce parametre et sa docstring affirme 'Aucune chaine SQL ne vient de l'appelant'. Mesure: lire_vue(inst, 'v_actes', [('nature','eq','RESOLUTION_AG')], ordre="CASE WHEN objet LIKE '%facade%' THEN 0 ELSE 1 END, acte_id") s'execute et rend 2 lignes; une sous-requete arbitraire (SELECT COUNT(*) ... WHERE objet LIKE ...) dans ORDER BY passe aussi. Le test test_aucun_filtre_ne_balaie_du_texte (test_actes_autorisation.py:421-434) n'inspecte que les criteres, jamais `ordre`: le contournement ne casse aucun test.

- **Consequence** : La liste fermee d'operateurs et le test qui la defend ne couvrent pas le seul endroit ou du SQL d'appelant entre dans la requete. Un dev UI qui veut trier une colonne passera par `ordre` - c'est deja ce que font matrice() et constats() - et pourra y reintroduire le balayage de texte de _decision_cell_status, precisement ce que le module existe pour interdire.



### C002 - Une vue absente ou périmée rend 0 ligne sans distinction d'une base vide, et rien dans le produit ne rafraîchit jamais les vues



- **Fichier** : `server/src/coproscope/modules/_actes_store.py`

- **Silencieux** : oui

- **Preuve** : Mesuré sur la copie contenant 173 actes versés. Scénario A, `DROP VIEW v_matrice_gouvernance` : `diagnostiquer` rend toujours `pret` avec actes=173, `A.matrice()` rend 0 ligne, et l'écran affiche `lead = « Aucun acte n'est encore versé dans le modèle »` alors que la table en contient 173. Aucune exception. Cause : `lire_vue` fait `if "no such table" in str(exc): return []` - or SQLite dit exactement « no such table: v_matrice_gouvernance » pour une VUE manquante. Le garde-fou écrit juste au-dessus (« une colonne manquante dans une vue a rendu zéro constat au lieu de 818, en silence ») ne couvre donc pas le cas des vues. Scénario B, vue remplacée par une définition d'une version antérieure : l'écran passe de 157 à 48 points à instruire, diagnostic toujours `pret`, aucun signalement. Et la seule fonction qui régénère les vues, `preparer()`, n'est appelée que depuis `ecrire()` : `grep -rn 'preparer(' src/` ne rend que cette ligne. Comme rien n'écrit, `preparer()` est inatteignable en production et le commentaire « une base ouverte par une version plus récente doit voir les vues de cette version » n'a aucun chemin d'exécution.

- **Consequence** : Le jour où le versement existera, une base écrite par une version antérieure gardera ses vues - donc sa règle de droit - indéfiniment, et l'écran rendra des nombres cohérents entre eux et faux. Et une vue absente affiche « aucun acte versé » sur une base qui en porte des centaines. C'est le défaut « colonne manquante, 0 constat au lieu de 818 » reproduit à l'identique, un niveau plus haut.



### C003 - Aucun vocabulaire n'est verifie a l'ecriture : une faute de frappe sur `portee` eteint sept controles et affiche « Ne s'applique pas »



- **Fichier** : `server/src/coproscope/modules/_actes_store.py (ecrire) et _actes_vocabulaire.py`

- **Silencieux** : oui

- **Preuve** : Mesure. _actes_store.ecrire ne verifie que les NOMS de colonnes (« colonnes inconnues ... serait ecrit nulle part »). Aucune valeur n'est validee : grep sur src/ montre 0 appel a resultat_valide (elle n'est appelee que par tests/test_actes_etalon.py:122 sur elle-meme) et NATURES, PORTEES, RELATIONS, PROVENANCES, FORCES, KINDS, RESULTATS, TVA_REGIMES ne sont que re-exportes par actes_autorisation.py. Consequences mesurees sur quatre actes ecrits sans erreur : nature='DECISION_CS' (au lieu de DECISION_CS_DELEGUEE) -> 0 ligne dans v_liens_manquants, 0 ACTE_SANS_FONDEMENT, l'acte derive echappe entierement a EXIGENCES_LIEN ; portee='ENGAGEMENT_DEPENSES' (pluriel) -> cel_seuil, cel_avis_cs, cel_devis, cel_execution = 'NON_APPLICABLE' ; nature='' et portee='' -> ligne presente dans la matrice, tous controles NON_APPLICABLE, aucun constat du tout. Une origine hors vocabulaire ('EXTRAIT_V2') donne 2 lignes dans v_actes pour un acte, 2 lignes identiques dans v_matrice_gouvernance et montant_paye double a 36 480,0.

- **Consequence** : Le schema fait reposer tout son pouvoir de controle sur des egalites de chaines (`a.portee NOT IN (...)`, `JOIN exigences e ON e.nature = a.nature`, `v_actes WHERE origine = 'CORRIGE_HUMAIN'`). Une valeur hors vocabulaire ne leve rien, ne loge rien, et se traduit a l'ecran par le message le plus rassurant du produit : FORCE_NON_APPLICABLE, « Ne s'applique pas », dont le vocabulaire dit explicitement qu'il « retire une diligence ». Un extracteur qui ecrira une seule valeur de trop desactivera des controles en les faisant passer pour sans objet.



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



### C009 - La cle de priorite du bareme n'est jamais lue : les 39 priorites de la taxonomie valent 0



- **Fichier** : `server/src/coproscope/modules/_docuscope_parts/02_classification.py:32`

- **Silencieux** : oui

- **Preuve** : Ligne 32 : `score += int(rule.get("priority", 0))`. Le fichier livre server/src/coproscope/configs/taxonomy.default.yml ecrit `"priorite"` 39 fois (115, 112, 108, 104, 100, 98, 94, 92, 90 ... 36) et jamais `"priority"`. Aucune autre taxonomie du depot ne definit `priority`. Tous les autres champs de la meme fonction ont pourtant leur alias francais : `rule.get("filename_patterns", rule.get("motifs_nom_fichier", []))`, `rule.get("keywords", rule.get("mots_cles", []))`, `rule.get("document_type", rule.get("type_document", ...))`, `rule.get("filename_weight", rule.get("poids_nom_fichier", 50))`. Seul `priority` n'a pas le sien. Preuve par rejeu : j'ai reimplemente `_classify` a l'identique avec priorite = 0 et l'ai passe sur les 3447 lignes du registre canonique et les 22 lignes du second cabinet : 0 desaccord sur 3469 lignes. Le registre existant est donc exactement le produit d'un bareme sans priorites. Contre-epreuve : si la cle `priorite` etait lue, 148 lignes (4,3 %) changeraient de type.

- **Consequence** : Le seul mecanisme d'arbitrage entre regles concurrentes est mort. Il ne reste que 50 points par motif de nom de fichier et 5 points par mot-cle, ce qui produit des egalites massives : 271 lignes (7,9 %) ont au moins deux regles a egalite au sommet, et l'egalite est tranchee par `if score > best[2]`, donc par la position de la regle dans le fichier de configuration. Les egalites les plus frequentes : Appel_Fonds = Reglement_Copropriete (44), Contentieux_Nominatif = Convocation_AG (12), Convocation_AG = Courrier (11), Convocation_AG = PV_AG (9). 520 lignes (15,1 %) sont gagnees par un score de 5, c'est-a-dire par un seul mot-cle.



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



### C012 - La passerelle est tranchee en amont par une regex, et l'etat PASSERELLE_25_1_REQUISE ne sort jamais du pipeline reel



- **Fichier** : `server/src/coproscope/modules/_resolutions_extraction.py`

- **Silencieux** : oui

- **Preuve** : _majorite_appliquee() (l.102-110) rend "24" des que PASSERELLE_UTILISEE_RE matche, avant que le module de decompte voie quoi que ce soit. Rejoue sur le PV du 03/07/2024 (55 resolutions extraites): 18 resolutions passerelle. Etiquetees "24" (ce que l'extracteur envoie) -> ADOPTEE_CONFIRMEE x18. Etiquetees "25" (ce que le PV annonce) -> PASSERELLE_25_1_REQUISE x18. Sur les 55 resolutions du PV, l'etat PASSERELLE_25_1_REQUISE est produit 0 fois.

- **Consequence** : L'etat que docs/decompte_des_voix_2026-09-04.md l.511 presente comme le resultat du jour - "l'adoption ne s'explique que par un second vote a l'article 24; verifier qu'il a eu lieu" - est injoignable a travers la chaine reelle. Les 18 adoptions arrivent a l'ecran en ADOPTEE_CONFIRMEE, c'est-a-dire "rien a verifier". Et si la regex rate un libelle, la meme resolution bascule en REJET_CONFIRME: deux verdicts opposes pour les memes chiffres, arbitres par un re.search que personne ne voit.



### C013 - Cinq votes du second cabinet sortent de tous les comptages, sans drapeau, parce qu'un mot de clôture n'est pas dans la liste



- **Fichier** : `server/src/coproscope/modules/_resolutions_extraction.py:85`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/modules/_resolutions_extraction.py:85, fonction _issue : après avoir essayé les neuf préfixes de ISSUE_PREFIXES, la ligne est `return mot.upper()`. Mesuré sur les deux corpus : le cabinet A écrit « cette résolution est adoptée / rejetée » ; le cabinet B (second corpus, 22 PDF) écrit cinq fois « cette résolution est DEVENUE sans objet ». CLOTURE_RE ne capture que le premier mot, `devenue`, aucun préfixe ne matche, et le résultat stocké devient la chaîne « DEVENUE ». J'ai vérifié les trois conséquences une par une : « DEVENUE » n'est pas une clé de LIBELLES_RESULTAT (resolutions_view.py:54), donc l'écran affiche le mot brut ; il n'est dans aucun des trois compteurs de _comptages (resolutions_view.py:163-170) ; il n'est pas dans RESULTATS_A_RELIRE (resolutions_view.py:52). Et la confiance de ces cinq lignes vaut « moyenne », pas « faible », donc a_relire reste faux. Le commentaire de _resolutions_motifs.py:142 dit d'où vient la liste : « vocabulaire relevé sur neuf assemblées de 2021 à 2026 » - d'un seul cabinet. La valeur correcte, SANS_OBJET, existe déjà dans le code et n'est simplement jamais atteinte.

- **Consequence** : Sur une assemblée du second cabinet, l'écran annonce 91 résolutions et n'en compte que 86 dans ses trois totaux. Les cinq manquantes s'affichent avec le mot « DEVENUE » en guise d'issue, aucune n'est proposée à la relecture, et rien ne dit que 5 votes ne sont dans aucun compteur. Un conseiller syndical qui additionne les trois chiffres et ne retombe pas sur le total n'a aucun moyen de savoir pourquoi. C'est le mode de défaillance exact que vous décrivez : une valeur plausible, aucune exception, aucune trace.



### C014 - Une colonne renommée fait disparaître 173 résolutions et l'écran accuse l'OCR d'un document parfaitement lisible



- **Fichier** : `server/src/coproscope/vault/gouvernance_store.py:191`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/vault/gouvernance_store.py:191-192 : `except sqlite3.OperationalError: return []`. Toute erreur SQL, y compris `no such column`, devient une liste vide. Preuve de bout en bout, faite sur une copie de la base réelle dans un dossier de travail : avant, l'écran rend 2 assemblées et 63 lignes ; après un simple `ALTER TABLE resolutions RENAME COLUMN position TO rang` (la colonne est dans le ORDER BY par défaut, ligne 174), l'écran passe à `registre_vide`, 0 assemblée, alors que `select count(*)` sur la même base rend toujours 173. Le module voisin server/src/coproscope/modules/_actes_store.py:150-162 a corrigé exactement ce défaut pour lui-même, en ne rattrapant que `no such table` et en laissant tout le reste remonter - son commentaire dit « une colonne manquante dans une vue a rendu zéro constat au lieu de 818, en silence ». La couche partagée, elle, n'a pas été corrigée, et trois appelants passent par elle : resolutions_view.py:130, _actes_store.py:119 (lire_table), _convocation_store.py:67, plus lisibilite.py:178.

- **Consequence** : L'utilisateur lit : « Le registre existe mais ne contient aucune résolution. Un procès-verbal a peut-être été déposé sans couche texte lisible. Vérifiez sa qualité d'extraction dans les documents. » C'est faux sur les trois points, et c'est actionnable : il ira vérifier l'OCR d'un document qui n'a rien. Le même chemin vide aussi lisibilite.decisions(), c'est-à-dire les refus déjà exprimés par l'utilisateur - le produit se remet alors à reposer des questions auxquelles il a déjà été répondu. Aucun test ne couvre cette branche : test_gouvernance_store.py teste la base absente (ligne 88), jamais la colonne absente.



### C015 - Le proces-verbal etalon du 03/07/2024 est eclate sur quatre types differents ; ses resolutions ne sont pas la ou le modele ira les chercher



- **Silencieux** : oui

- **Preuve** : Le proces-verbal existe au registre sous trois formes. (1) `PVAG_PVAG20240703.pdf.md`, 59 130 caracteres, PV_AG, AUTO_CLASSIFIED - la seule ligne juste. (2) `DIVERS_pv 03072024.pdf`, 58 813 caracteres, le PDF du syndic : Convocation_AG. (3) Le meme PV decoupe en 5 sections, toutes dans le dossier AG du 03/07/2024, section PV : `..._ouverture_et_bureau.pdf` (texte : `PROCES-VERBAL DE L'ASSEMBLEE GENERALE...`) -> Convocation_AG, score 15 ; `..._elections_conseil_syndical_et_resolutions_generales.pdf` -> CR_CS, score 55 sur `NOM:conseil.*syndical` ; `..._travaux_et_appels_de_fonds.pdf` (texte : `Pas de vote car la resolution est rejetee. 40 - Vote des travaux ... Article 24`) -> Appel_Fonds, score 50 sur `NOM:appel.*fonds` ; `..._clause_aggravation_des_charges.pdf` -> PV_AG mais A_RECLASSER ; `..._cloture_et_signatures.pdf` -> Convocation_AG, score 5 sur le seul `MOT:ordre du jour`. Enfin le tableau extrait des decisions, `decisions_AG_20240703.csv` (colonnes numero_question, intitule, decision_estimee) -> Convocation_AG, sur 3 lignes de registre partageant le meme doc_id.

- **Consequence** : Un modele de gouvernance qui filtre `document_type = PV_AG` pour reconstituer les 55 resolutions trouve 10 lignes dont 1 seule est un proces-verbal, et manque : le PDF source du syndic, les 5 sections a granularite page, et le tableau de decisions deja extrait. La section qui porte les votes nominatifs et les tantiemes - la piece la plus sensible du corpus - est rangee en compte rendu de conseil syndical, donc sous un autre regime de diffusion que celui d'un PV d'assemblee.



### C016 - Les voix comptées et la passerelle de l'article 25-1 n'ont aucune colonne dans le modèle des actes : le fait étalon du 04/09 devient irrecalculable après versement



- **Silencieux** : oui

- **Preuve** : Comparaison des schémas, sur données réelles (173 lignes). Le registre `resolutions` porte 29 colonnes, `_actes_schema.ACTE_FIELDS` en porte 26. Seize colonnes du registre n'ont AUCUNE destination : passerelle_citee (renseignée 173/173), passerelle_utilisee (173/173), voix_pour (129/173), base_voix (129/173), voix_contre (99/173), voix_relevees (78/173), duree_mois (57/173), duree_intitule (57/173), decision_actee (27/173), qualifications (19/173), voix_abstention (9/173), montant_seuil (6/173), montant_intitule (6/173), divergences (6/173), position (173/173), numerotation (173/173). Elles ne sont pas non plus dans la zone d'extension : `ATTRIBUTS_CONNUS` déclare sept noms ('base_repartition', 'cle_repartition', 'reference_dossier', 'libelle_majorite_brut', 'piece_jointe_nommee', 'penalite_retard', 'duree_contrat'), aucun ne concerne un vote. Et le commentaire de `attributs_acte` interdit explicitement d'y ranger un invariant : « un fait qui devient invariant [...] doit migrer vers une colonne du noyau ». Un décompte de voix est présent chez les deux cabinets : il n'est ni un variant ni une colonne du noyau. Il n'a nulle part où aller.

- **Consequence** : Le fait établi le 2026-09-04 - avec 4 899 présents sur 10 000, l'article 25 était arithmétiquement hors d'atteinte, aucune des 21 résolutions chiffrées n'atteignant 5 001 - est aujourd'hui reconstituable depuis le registre et ne le sera plus depuis le modèle. C'est le seul contrôle qui aurait distingué « adoptée » de « déclarée adoptée sans atteindre la majorité ». Brancher l'UX sur le modèle avant d'ouvrir ces colonnes revient à câbler l'écran sur la seule couche d'où la preuve a été retirée.



### C017 - Une portée inconnue n'active pas tous les contrôles, elle les désactive tous : le typage est disponible et n'est appliqué nulle part à l'écriture



- **Silencieux** : oui

- **Preuve** : Test exécuté sur une copie du coffre. `A.ecrire` accepte une ligne portant nature='CE_QUE_JE_VEUX', etat='N_IMPORTE_QUOI', portee='PORTEE_INEXISTANTE', resultat='PEUT_ETRE', origine='PAS_UNE_ORIGINE', montant_autorise='beaucoup' : 1 ligne écrite, relue telle quelle, aucune exception. Cette ligne apparaît ensuite dans `v_matrice_gouvernance` avec cel_seuil, cel_avis_cs, cel_rapport_cs, cel_annexe, cel_devis et cel_execution tous à 'NON_APPLICABLE' - six cellules sur sept affichées « Ne s'applique pas ». Motif : `_actes_constats` et `_actes_vues` bornent chaque contrôle par `portee IN (liste des portées soumises)`, et une portée hors vocabulaire n'est dans aucune liste. `PORTEE_ORDINAIRE` est documentée comme le repli où « tous les contrôles restent appliqués » ; une portée fautive fait exactement l'inverse. Les validateurs existent - `resultat_valide('PEUT_ETRE')` rend False, `diffusable()` existe - et `grep -rn 'resultat_valide|diffusable(' src/ tests/` ne trouve aucun appelant hors des tests `test_actes_autorisation.py` et `test_actes_etalon.py`.

- **Consequence** : Une faute de frappe dans la portée, ou un versement écrit par une autre conversation avec un vocabulaire voisin, exempte silencieusement l'acte de six contrôles sur sept et l'affiche en « Ne s'applique pas », c'est-à-dire rassurant. Aucun message, aucune ligne de journal, aucune cellule différente d'un acte réellement hors contrôle. C'est le pire cas possible du produit : une valeur plausible produite par une erreur.





## GRAVE



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



### C020 - ACTE_SANS_EXECUTION est inatteignable sur l'etalon: 49 resolutions sur 55 retirees par la portee, les 6 restantes par le montant



- **Fichier** : `server/src/coproscope/modules/_actes_constats.py`

- **Silencieux** : oui

- **Preuve** : Mesure sur les 55 resolutions du 03/07/2024, typees d'apres le tableau resolution par resolution de docs/etalon_corpus_tests_ux.md (22 DESIGNATION_ORGANE, 14 MODALITES, 12 ENGAGEMENT_DEPENSE, 2 SEUIL, 2 BUDGET, 1 APPROBATION_COMPTES, 1 DESIGNATION_SYNDIC, 1 AUTORISATION_COPROPRIETAIRE): portees_soumises('EXECUTION') ne retient que ('ORDINAIRE','ENGAGEMENT_DEPENSE'), donc 43/55 sont hors controle; croise avec resultat='ADOPTEE', il reste 6/55; la condition `e.montant_autorise > 0` (_actes_constats.py:117) en retire 6 de plus, aucune resolution de l'etalon ne portant de montant. Total emis par v_constats sur les 55 lignes: 2 constats (1 ISSUE_NON_ENONCEE, 1 MAJORITE_NON_ENONCEE). Aucun compteur, aucune colonne, aucun constat ne mentionne qu'un controle a ete neutralise faute de donnee.

- **Consequence** : Une file de travail vide se lit 'tout a ete execute'. La difference entre 'aucun manquement' et 'le controle n'a pas pu s'exercer' n'est portee nulle part - alors que le modele a invente FORCE_NON_APPLICABLE precisement pour tenir cette distinction sur les cellules, et ne la tient pas sur les constats.



### C021 - MAJORITE_NON_ENONCEE cherche une valeur que la source ne produit pas: 0 constat la ou l'etalon en etablit 1



- **Fichier** : `server/src/coproscope/modules/_actes_constats.py`

- **Silencieux** : oui

- **Preuve** : _actes_constats.py:149: `WHERE a.majorite_annoncee = 'NON_ENONCEE'`. Mesure sur le coffre reel: 0 ligne a 'NON_ENONCEE', 7 lignes a chaine vide, dont 1 sur l'assemblee AG-2024-07-03 (majorites: '' -> 1, '24' -> 30, '25' -> 24). L'etalon etablit 1 majorite non enoncee sur cette assemblee (resolution 23). _actes_vocabulaire pose en tete 'aucune valeur signifiante n'est NULL ni la chaine vide' - la source la viole deja. _actes_store.ecrire valide les NOMS de colonnes (lignes 96-103) et jamais les valeurs; resultat_valide() existe mais n'est appelee nulle part dans le lot.

- **Consequence** : Le constat rend zero sur donnees reelles et un sur la fixture de test, sans qu'aucun des deux ne signale l'ecart. Un vocabulaire declare ferme mais jamais verifie a l'ecriture ne protege rien: il donne seulement l'impression d'etre protege.



### C022 - Le constat « aucune majorité énoncée » ne peut jamais se déclencher : le producteur écrit la chaîne vide, le consommateur cherche NON_ENONCEE



- **Fichier** : `server/src/coproscope/modules/_actes_constats.py`

- **Silencieux** : oui

- **Preuve** : `_actes_vocabulaire.py:226` : `MAJORITE_NON_ENONCEE = "NON_ENONCEE"`. `_actes_constats.py:149` : ` WHERE a.majorite_annoncee = 'NON_ENONCEE'`. Seul producteur du champ dans tout le dépôt, `_resolutions_extraction.py:33` (`majorite_annoncee: str = ""`) et `:176` (`annoncee = next((m for m in majorites if m != "25-1"), "")`). Rien ne convertit "" en NON_ENONCEE. Mesure sur le PV étalon : 29 résolutions à '24', 24 à '25', **2 à ''**, **0 à 'NON_ENONCEE'**. La seule écriture de la valeur dans le dépôt est un fixture de test : `tests/test_actes_etalon.py:61`, `lignes[22]["majorite_annoncee"] = "NON_ENONCEE"`.

- **Consequence** : L'étalon attend 1 constat de majorité non énoncée sur 55. La chaîne réelle en produirait 0, sans erreur, sans trace. Et le test qui garde cette promesse s'appelle `test_une_majorite_non_enoncee_est_un_fait_pas_une_colonne_vide` : il passe parce qu'il injecte à la main la valeur que la chaîne n'écrit jamais, alors qu'en production c'est précisément une colonne vide. C'est le défaut « colonne manquante, 0 constat au lieu de 818 », posé une seconde fois.



### C023 - montant_texte rend 2,50 EUR pour un seuil écrit « 2.500 » : un point de milliers divise par mille, sans exception et sans trace



- **Fichier** : `server/src/coproscope/modules/_actes_schema.py`

- **Silencieux** : oui

- **Preuve** : Fonction `montant_texte`, branche `if "," in texte and "..." in texte` : quand il n'y a QUE des points, aucune normalisation n'a lieu et `Decimal` les lit comme séparateur décimal. Mesuré : '2.500' → '2.50' ; '5.000' → '5.00' ; '10.000' → '10.00' ; '1,234.56' → '1.23'. Les formes correctes passent bien ('357 493,10' → '357493.10', '2.500,00' → '2500.00', '18 240,00 EUR' → '18240.00'). Aucun retour d'erreur : la fonction rend une chaîne valide, `montant_nombre` rend un flottant valide, et la vue `v_constats` l'imprime en `printf('%.2f')`.

- **Consequence** : Cette valeur alimente `montant_autorise`, c'est-à-dire le seuil de mise en concurrence de l'article 21 al. 2 et le plafond de délégation de l'article 21-2. Un plafond de 10 000 EUR lu « 10.000 » devient 10,00 EUR et fait tomber le constat PLAFOND_DEPASSE sur toutes les dépenses ; un seuil de 5 000 EUR lu « 5.000 » devient 5,00 EUR. Le montant faux est ensuite réaffiché à l'écran comme un fait, avec sa citation Légifrance à côté.



### C024 - La cle primaire des actes n'a pas `etat` : le proces-verbal ecrase le projet de resolution de la convocation



- **Fichier** : `server/src/coproscope/modules/_actes_schema.py (ACTE_CLES = ("acte_id", "origine"))`

- **Silencieux** : oui

- **Preuve** : Mesure. _actes_vocabulaire declare deux etats, ETAT_PROJETEE (lu dans une convocation) et ETAT_CONSTATEE (lu dans un PV), et acte_id_resolution derive le meme identifiant pour les deux (meme date d'AG, meme numero, meme sous-numero). Ecriture du projet depuis DOC-CONVOC : 1 ligne, PROJETEE, montant 18 240,00 issu du devis. Ecriture du constat depuis DOC-PV : la table contient 1 seule ligne, CONSTATEE, montant vide. Le montant du devis est perdu ; v_divergences_humaines ne montre rien (elle ne compare que EXTRAIT contre CORRIGE_HUMAIN). Ce n'est pas la suppression par doc_id qui detruit : les doc_id different ; c'est l'INSERT OR REPLACE sur la cle (acte_id, origine). La table `resolutions` de la meme base met justement `etat` dans sa cle (CLES_RESOLUTIONS = ('resolution_id','etat','origine')) « pour que l'ecart entre ce qui etait propose et ce qui a ete vote soit un tri ».

- **Consequence** : L'ecart projet/constat - ce qui etait propose contre ce qui a ete vote - est structurellement impossible dans le nouveau modele, alors qu'il existe deja dans la table voisine. Chez le cabinet ou le devis n'est nomme que par la convocation, c'est le montant lui-meme qui disparait a la lecture du PV, sans suppression tracee et sans divergence affichee.



### C025 - acte_id : deux assemblees le meme jour se confondent, et une date non normalisee cree une assemblee de plus



- **Fichier** : `server/src/coproscope/modules/_actes_schema.py (acte_id_resolution)`

- **Silencieux** : oui

- **Preuve** : Mesure. Deux assemblees du 2024-07-03 (une principale, une de syndicat secondaire), meme numero de resolution, deux doc_id distincts : acte_id identique ACTE-AG-2024-07-03-R12, et apres les deux ecritures la table contient 1 ligne - la seconde a ecrase la premiere, sans exception. La date n'est pas normalisee : acte_id_resolution('03/07/2024','12') rend ACTE-AG-03-07-2024-R12 et acte_id_resolution('2024-07-03','12') rend ACTE-AG-2024-07-03-R12, soit deux actes pour la meme resolution. Cas date manquante : les identifiants restent document-dependants (ACTE-AG-SANS-DATE-DOC-AAA-R12 vs ...-DOC-BBB-R12), donc deux lectures du meme PV font deux actes ; le sous-numero apparaissant apres coup change l'identifiant (R19 -> R19-2), l'ancien acte survit. Collisions de jeton verifiees : numero='19' + sous='2', numero='19.2' et numero='19-2' rendent le meme identifiant (probablement voulu) ; numero='' et numero='0' aussi (moins).

- **Consequence** : La decision n.3 protege contre un doublon ne d'une empreinte de texte, pas contre les trois cas reels : deux AG un meme jour, une date ecrite autrement, une date absente. Le premier cas est une perte de donnee silencieuse ; les deux autres sont des duplications silencieuses. Aucun des trois ne leve d'erreur et aucun constat ne les nomme.



### C026 - Aucune normalisation des montants a l'ecriture : « 18 240,00 EUR » vaut 18 EUR pour toutes les vues



- **Fichier** : `server/src/coproscope/modules/_actes_schema.py (montant_texte) et _actes_store.py (ecrire)`

- **Silencieux** : oui

- **Preuve** : Mesure. montant_texte existe et produit la forme canonique, mais ecrire() ne l'appelle jamais : la valeur brute part en base et les vues font CAST(... AS REAL). Trois actes ecrits sans erreur : montant_autorise='18 240,00 EUR' -> v_execution.montant_autorise = 18,0 et le constat produit « adoptee pour 18.00 EUR : aucune depense ne lui est rattachee » ; montant_autorise='voir devis' -> 0,0, ce qui le fait sortir du constat ACTE_SANS_EXECUTION (predicat montant_autorise > 0) : aucun constat du tout ; montant_autorise='' -> NULL, correctement traite. La fonction elle-meme a deux replis muets mesures : montant_texte('1.234') rend '1.23' et montant_texte('1,234.56') rend '1.23' - un separateur de milliers divise la valeur par mille sans trace ; montant_texte('abc'), ('1.2.3') et ('(1 200,00)') rendent '' , donc « montant absent », indistinguable d'un montant reellement absent.

- **Consequence** : Un facteur mille sur un montant vote, ou un montant illisible qui fait disparaitre l'acte du controle d'execution. Les deux rendent une valeur plausible : 18,00 EUR est un nombre, 0,00 EUR aussi, et la phrase de constat les affiche avec deux decimales comme si elles avaient ete lues.



### C027 - La colonne `portee`, dont depend toute la matrice HORS_CONTROLE, n'existe pas dans la source qui alimentera le modele



- **Fichier** : `server/src/coproscope/modules/_actes_typologie.py`

- **Silencieux** : oui

- **Preuve** : Le seul coffre reel des deux instances (tilleul_pseudo_reconstruite, .../vault_local/gouvernance.sqlite3, lu en copie lecture seule) contient UNE table, `resolutions`, 173 lignes, et zero des cinq tables actes_* et zero des onze vues. Ses colonnes: resolution_id, ag_id, doc_id, numero, objet, majorite_annoncee, passerelle_citee, passerelle_utilisee, majorite_appliquee, resultat, voix_*, base_voix, position, numerotation, decision_actee, qualifications, duree_mois, montant_seuil, montant_intitule, duree_intitule, divergences, valide_du, valide_au, etat, origine, confiance. Ni `portee`, ni `montant_autorise`, ni `entreprise`. Mesure de l'effet: 55 actes laisses a portee='ORDINAIRE' rendent 275 cellules ABSENT et 55 NON_APPLICABLE; les memes typees rendent 195 NON_APPLICABLE et 135 ABSENT.

- **Consequence** : Au premier chargement reel, 275 cellules afficheront 'Source manquante' la ou 195 devraient afficher 'Ne s'applique pas'. Le livrable du lot - ne plus mettre les 55 resolutions sur le meme plan - est annule par une colonne absente, sans erreur ni signal. C'est la forme exacte du defaut 'une colonne manquante a rendu 0 constat au lieu de 818'.



### C028 - Le controle 'deux ans au plus' (art. 21-3) sert de motif a un retrait de controle et n'existe nulle part



- **Fichier** : `server/src/coproscope/modules/_actes_typologie.py`

- **Silencieux** : oui

- **Preuve** : _actes_typologie.py:298-303 retire CTRL_SEUIL de PORTEE_DELEGATION_CS au motif que 'son controle propre est ailleurs: deux ans au plus (art. 21-3), montant maximum (art. 21-2)...'. Grep sur les modules _actes_*: '21-3' n'apparait que dans des docstrings (schema l.58 et l.176, typologie l.118, l.122, l.301); aucune comparaison de duree n'est ecrite. Par ailleurs (mesure): ACTE_SANS_FONDEMENT ne teste que l'absence de lien FONDE_PAR alors que son motif affirme 'aucune delegation en vigueur ne la fonde'; DELEGATION_EXPIREE exige d.valide_au <> '', or sur le coffre reel valide_au est renseigne sur 2 lignes sur 173 et valide_du sur 7 sur 173. Decision CS de 2026 adossee a une delegation de 2020 sans periode lue: aucun des deux constats n'est emis.

- **Consequence** : Un controle est desactive en pointant vers un controle qui n'a jamais ete ecrit, et le controle de substitution est inerte sur 171 lignes sur 173. Le motif de retrait est lisible a l'ecran et fait autorite: il affirme qu'un autre garde-fou tient, alors qu'aucun ne tient.



### C029 - Le retrait de l'avis du conseil syndical sur la désignation du syndic repose sur un motif que l'article cité contredit



- **Fichier** : `server/src/coproscope/modules/_actes_typologie.py`

- **Silencieux** : oui

- **Preuve** : `server/src/coproscope/modules/_actes_typologie.py`, PORTEE_DESIGNATION_SYNDIC / CTRL_AVIS_CS : « la consultation obligatoire de l'al. 2 porte sur les memes marches et contrats que le seuil, et le contrat de syndic en est sorti par le meme alinea ». Lu sur Légifrance, LEGIARTI000039313574 (loi 65-557 art. 21) porte DEUX phrases distinctes : « L'assemblée générale des copropriétaires, statuant à la majorité de l'article 25, arrête un montant des marchés et des contrats à partir duquel la consultation du conseil syndical est rendue obligatoire. » puis « A la même majorité, elle arrête un montant des marchés et des contrats autres que celui de syndic à partir duquel une mise en concurrence est rendue obligatoire. » L'exclusion n'existe que sur la seconde ; ce n'est pas le même alinéa, et le seuil de consultation ne sort pas le contrat de syndic. Le même article porte en outre « Le conseil syndical peut se prononcer, par un avis écrit, sur tout projet de contrat de syndic. »

- **Consequence** : Mesuré : 5 résolutions des deux corpus sont typées DESIGNATION_SYNDIC (1 cabinet A, 4 cabinet B). Sur chacune, l'écran affiche « Avis du conseil syndical : non exigé ici » avec, en renvoi source, « Loi 65-557, article 21 alinéa 2 » - l'article qui dit l'inverse. Ce n'est pas un contrôle en trop : c'est un contrôle retiré, donc une question au syndic qui ne sera jamais posée, sous une référence légale qui la fait paraître réglée.



### C030 - Une faute de frappe d'un caractère sur un nom de contrôle restaure en silence le défaut que le lot a corrigé



- **Fichier** : `server/src/coproscope/modules/_actes_typologie.py`

- **Silencieux** : oui

- **Preuve** : Mesuré : `portees_soumises('AVIS_CS')` rend 3 portées ; `portees_soumises('AVIS_CS ')` en rend 11 ; `portees_soumises('CONTROLE_QUI_NEXISTE_PAS')` en rend 11. `controle_applicable(portee, controle)` s'écrit `return controle not in HORS_CONTROLE.get(portee, {})` : tout nom inconnu rend True partout, et `motif_hors_controle` rend la chaîne vide. Aucune assertion `controle in CONTROLES` n'existe. Ce nom est ensuite interpolé directement dans le SQL de la vue : `_actes_vues.py`, `_cellule(relation)` construit `a.portee NOT IN (…)` à partir de son résultat.

- **Consequence** : L'inversion « ce qui n'est pas listé s'applique » protège contre l'oubli d'un motif, mais elle ne protège pas contre un nom erroné : celui-ci rallume le contrôle sur les 11 portées, ce qui redonne 55 cellules « Source manquante » au lieu de 12 sur le PV étalon - exactement l'état d'avant le lot, avec la même apparence qu'après. La seule preuve à l'écran serait le motif générique « Ce contrôle n'a pas d'objet sur ce type. » qui, lui, ne s'affiche plus du tout puisque la cellule n'est plus NON_APPLICABLE. Les 44 tests passent.



### C031 - Le contrôle MAJORITE est déclaré, exclu portée par portée, et appliqué nulle part : ni cellule, ni constat, ni producteur de majorite_requise



- **Fichier** : `server/src/coproscope/modules/_actes_typologie.py`

- **Silencieux** : oui

- **Preuve** : `CONTROLES` déclare sept contrôles dont `CTRL_MAJORITE = "MAJORITE"`, et `portees_soumises('MAJORITE')` rend 11 portées - le contrôle est donc réputé applicable partout. Mais `grep -rn "CTRL_MAJORITE|'MAJORITE'" src/` ne rend que sa définition et son entrée dans le tuple : aucun consommateur. `v_matrice_gouvernance` a sept cellules (cel_seuil, cel_avis_cs, cel_rapport_cs, cel_resolution, cel_annexe, cel_devis, cel_execution) et aucune n'est la majorité. `v_constats` ne contient aucune comparaison entre `majorite_annoncee`, `majorite_requise` et `majorite_appliquee` - le seul constat de majorité est MAJORITE_NON_ENONCEE, qui teste l'absence. Et `majorite_requise` n'a aucun producteur : 0/173 après versement, aucune colonne du registre ne peut la remplir. Le registre porte pourtant la matière : `majorite_annoncee` (91 fois '24', 75 fois '25') et `majorite_appliquee` (145 fois '24', 21 fois '25'), soit 54 résolutions annoncées à l'article 25 et traitées à l'article 24 - la passerelle de l'article 25-1, dont les deux colonnes de traçage n'ont pas de destination dans le modèle.

- **Consequence** : Le seul contrôle qui aurait pu produire le constat « déclarée adoptée sans atteindre la majorité requise » est présent dans le vocabulaire, discuté dans les motifs d'exclusion, et n'existe dans aucun chemin d'exécution. Son absence ne peut pas se voir : il n'y a pas de cellule vide à regarder, il n'y a pas de cellule du tout. Un contrôle déclaré et non branché est plus dangereux qu'un contrôle absent, parce que sa déclaration fait croire qu'il tourne.



### C032 - Quand la date de l'acte est absente, l'echeance rendue est la plus ANCIENNE assemblee de la base



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py`

- **Silencieux** : oui

- **Preuve** : _actes_vues.py:252-261: `AND x.date_effet > a.date_effet`. Si a.date_effet vaut '', toute date lui est superieure, donc MIN() rend la premiere assemblee connue, pas la premiere posterieure. Mesure: base contenant une AG d'approbation des comptes du 2019-06-01 et une du 2025-06-01, plus une decision CS sans date lue -> echeance='2019-06-01' et constat OBLIGATION_NON_TENUE 'Decision du : aucun compte rendu devant l'assemblee du 2019-06-01'. Meme mesure sur URGENCE_SYNDIC sans date: echeance='2019-06-01' et le constat bascule silencieusement de URGENCE_JAMAIS_PORTEE vers OBLIGATION_NON_TENUE, avec le motif troue 'Depense engagee en urgence le : ...'.

- **Consequence** : Le modele date un manquement a une assemblee anterieure a l'acte lui-meme. La valeur est plausible - c'est une vraie date d'assemblee - et rien ne signale que la date de l'acte manquait. Le cas n'est pas theorique: le coffre reel porte 110 resolutions sur 173 rattachees a des assemblees sans date lue (ag_id AG-DOC-7139EDAD85E4 et AG-DOC-729CCCF88863).



### C033 - Un montant non normalise est tronque de trois ordres de grandeur par le CAST, sans exception



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py`

- **Silencieux** : oui

- **Preuve** : Les vues comparent par CAST(NULLIF(colonne,'') AS REAL). Mesure: montant_autorise='18 240,00 EUR' (la forme exacte que montant_texte est cense normaliser) -> v_execution.montant_autorise = 18.0, et le constat emis est 'adoptee pour 18.00 EUR : aucune depense ne lui est rattachee', montant_en_jeu=18.0. montant_autorise='non chiffre' -> 0.0, donc IS NOT NULL, donc compte par v_taux_gouvernance.actes_quantifies (mesure: 3 actes 'quantifies' pour un seul montant reellement lisible).

- **Consequence** : Une resolution de 18 240 EUR entre dans la file a 18 EUR et tombe au dernier rang d'un tri par montant. Le seul garde-fou est que tout ecrivain appelle montant_texte(); ni le schema, ni le store, ni les vues ne le verifient ou ne le detectent.



### C034 - v_acte_effectif choisit son devis par LIMIT 1 sans ORDER BY, et retient l'assertion la moins probante



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py`

- **Silencieux** : oui

- **Preuve** : _actes_vues.py:146-151 et 163-168: `SELECT l.montant_impute FROM liens_gouvernance l WHERE ... LIMIT 1`, sans ORDER BY, alors que _cellule() (lignes 363-369) trie explicitement par provenance puis par force probatoire. Mesure: deux DEVIS_RETENU concurrents sur le meme acte, l'un SYNDIC_AFFIRME/AFFIRME_SANS_PIECE a 22 200,00, l'autre HUMAIN_CONFIRME/PIECE_PRODUITE a 18 240,00 -> montant_effectif=22200.00, entreprise_effective='CHER', pendant que cel_devis de la MEME ligne rend PIECE_PRODUITE. Ce sont les deux montants de l'etalon (devis 22 200,00 rejete, 18 240,00 adopte).

- **Consequence** : Deux ordres de tri pour un meme ensemble de liens dans une meme vue: la cellule dit 'confirme par un humain' a cote d'un montant pris chez le syndic. Le choix depend de l'ordre de lignes de SQLite et peut basculer a une reconstruction sans changement de code. De plus montant_lu_sur ne porte ni provenance ni force probatoire: la barriere diffusable() ne peut pas empecher un montant AFFIRME_SANS_PIECE d'alimenter montant_paye, PLAFOND_DEPASSE, MONTANT_DIVERGENT et la colonne montant de la matrice.



### C035 - Aucune contrainte de format de date, et toutes les regles de droit sont des comparaisons de chaines



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py (_V_LIENS_MANQUANTS, _V_CUMUL) et _actes_constats.py (DELEGATION_EXPIREE)`

- **Silencieux** : oui

- **Preuve** : Mesure sur dates au format jj/mm/aaaa, accepte partout (ACTE_FIELDS annote « ISO » en commentaire, rien ne le verifie ; acte_id_resolution accepte n'importe quelle chaine). Cas 1 : depense d'urgence le 15/11/2024, assemblee suivante le 05/01/2025 -> echeance calculee vide et constat URGENCE_JAMAIS_PORTEE « aucune assemblee ne s'est tenue depuis. Elle n'a ete portee nulle part », parce que '05/01/2025' > '15/11/2024' est faux en comparaison textuelle. Le meme jeu en ISO produit le constat correct OBLIGATION_NON_TENUE avec l'echeance 2025-01-05. Cas 2 : delegation valide du 03/07/2024 au 03/07/2026, depense de 6 000,00 le 15/09/2024, plafond 5 000,00 -> v_cumul_delegation rend depenses_cumulees 0 et cumul 0,0, aucun PLAFOND_DEPASSE, parce que '15/09/2024' <= '03/07/2026' est faux.

- **Consequence** : Deux erreurs de sens oppose, toutes deux muettes : une accusation fausse portee contre le syndic (une AG a bien eu lieu), et un depassement de plafond reel rendu invisible avec un cumul affiche a 0,00 EUR. Le meme jeu de donnees en ISO donne les bonnes reponses : la justesse du modele depend d'une convention qu'aucune couche n'impose ni ne verifie.



### C036 - CAST AS REAL sur un montant écrit à la française : 18 240,00 EUR devient 18 euros, et le plafond de l'article 21-2 ne se déclenche plus



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py:301`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/modules/_actes_vues.py:301 : `COALESCE(SUM(CAST(NULLIF(dep.montant_ttc,'') AS REAL)), 0.0) AS cumul`. `NULLIF(x,'')` ne protège que de la chaîne vide. Mesuré sur SQLite avec les formes de montant que le corpus produit : '18 240,00 EUR' → 18.0 ; '2 000' (espace de milliers) → 2.0 ; '1.234,56' → 1.234 ; 'environ 2000' → 0.0 ; '20%' → 20.0. Somme de ['1000','environ 2000','18 240,00 EUR'] = 1018.0 au lieu de 21 240. Le même motif est aux lignes 121-122 (taux de TVA), 332 et 334 (montant_payé). La défense existe : `montant_texte` (_actes_schema.py:461) normalise « 18 240,00 EUR » en « 18240.00 » et son docstring dit qu'elle « garantit que le CAST rende ce qu'on croit ». Elle n'est appelée nulle part en production - vérifié par grep, elle n'apparaît que dans l'import et le __all__ de la façade ; `_actes_store.ecrire` ne l'applique pas.

- **Consequence** : controle_gouvernance_view.py:170 compare `cumul > plafond` et affiche « Le plafond n'est pas atteint » sur une délégation qui l'a franchi d'un facteur vingt. C'est le seul contrôle du produit qui ne se voit pas ligne à ligne - chaque dépense peut être régulière et le cumul dépasser quand même - et c'est précisément celui qu'un montant mal casté neutralise. Aucune exception, aucune ligne rouge : un écran vert. Le garde-fou est écrit, documenté, testé, et rien ne l'impose au point d'écriture. C'est la couture que le branchement UX va traverser en premier.



### C037 - Le total des charges lu dans une annexe est celui de la dernière colonne, quelle qu'elle soit - sur l'exercice 2025 c'est la colonne 2027



- **Fichier** : `server/src/coproscope/modules/_comptes_extraction_annexe.py:136`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/modules/_comptes_extraction_annexe.py:136 : `total_charges=totaux[-1] if totaux else None`. Mesuré sur les annexes réelles de l'instance reconstruite. Annexe de l'exercice 01/01/2025 → 31/12/2025, cinq colonnes : exercices ['2024','2025','2025','2026','2027'], totaux ['290117.06','300000.00','295349.10','303000.00','303500.00']. La valeur retenue dans `total_charges` est 303 500,00 - la projection 2027 - alors que le réalisé 2025 de cette même annexe est 295 349,10. Écart 8 150,90 EUR, et surtout ce n'est pas un total 2025. Ce qui rend le défaut certain plutôt que probable : la fonction calcule douze lignes plus haut `colonnes[].usage` (« vote du budget » / « approbation des comptes ») et _usage_de:187 refuse prudemment de nommer un usage quand il y a deux libellés pour cinq colonnes - mesuré : les cinq `usage` sont vides. Puis la ligne 136 prend `[-1]` quand même. La prudence de la ligne 127 est annulée par la ligne 136.

- **Consequence** : `total_charges` est la seule valeur que consomment B-4 (égalité des annexes), B-5 (plancher de 5 % du fonds de travaux), B-6 (avance de réserve au sixième du budget) et B-7. Le plancher légal du fonds de travaux serait donc calculé sur 303 500 au lieu du budget de l'exercice contrôlé : 15 175 EUR au lieu de 14 767,46, et un écart réel de 300 EUR passerait pour conforme. Le nombre affiché est un vrai nombre du document : rien à l'écran ne peut le trahir. Le test test_comptes_extraction.py:468 vérifie les cinq totaux de `total_charges_par_colonne` et commente même que « deux colonnes portent 2029 : le budget voté et le réalisé » - puis n'assure jamais `total_charges`. Le test connaît l'ambiguïté et ne teste pas le champ qui la tranche.



### C038 - Aucun controle de coherence entre les voix pour, la presence et le total du syndicat



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : oui

- **Preuve** : voix_presentes n'est lu que par majorite_25_atteignable() (l.489), voix_totales que comme denominateur. Mesures: art.24, voix_pour=6000 avec voix_presentes=4899 -> ADOPTEE_CONFIRMEE, base 6100, 98.36 %, 0 constat. Art.25, voix_pour=49000 sur voix_totales=10000 -> ADOPTEE_CONFIRMEE, 490.0 %. Art.24, voix_pour=-100 contre=200 -> REJET_CONFIRME, -100.0 %.

- **Consequence** : Un decompte OCRise de travers - un chiffre colle, un separateur de milliers avale - produit un verdict de forme normale. 6 000 voix pour dans une assemblee ou 4 899 seulement sont presentes donne 98,36 % d'adoption confirmee: parfaitement plausible a l'ecran, arithmetiquement impossible. Le module dispose de la donnee qui le detecterait et ne s'en sert pas.



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



### C043 - Un Decimal déposé dans un champ déclaré float : un contrôle du budget passe CONFORME, le suivant lève, sur la même entrée



- **Fichier** : `server/src/coproscope/modules/comptes_extraction.py:254`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/modules/comptes_extraction.py:254 construit `BudgetPrevisionnel(total_charges=annexe.total_charges)`. Or `AnnexeComptable.total_charges` est déclaré `Decimal | None` (_comptes_extraction_modele.py:193) et `BudgetPrevisionnel.total_charges` est déclaré `float | None` (_budget_previsionnel_modele.py:44). Le dataclass est frozen, sans validation : le Decimal passe. Mesuré en passant les seize contrôles sur un Dossier construit exactement comme le fait comptes_extraction, avec Decimal('357493.10') : B-4 rend CONFORME (Decimal se compare à un float sans broncher), et b6_avance_reserve lève `TypeError: unsupported operand type(s) for +: 'decimal.Decimal' and 'float'` sur `_budget_previsionnel_controles_b.py:283`, `avance > plafond + _TOLERANCE`. `evaluer()` (budget_previsionnel.py:66) est un tuple-comprehension sans garde : l'évaluation entière meurt à B-6. Les tests ne peuvent pas le voir : test_budget_previsionnel.py:110 et 181 alimentent des floats (303500.0, 300000.0), tandis que test_comptes_extraction.py:529 assure `Decimal("1300.00")` de l'autre côté de la couture. Deux suites vertes de part et d'autre d'un raccord cassé.

- **Consequence** : Aujourd'hui, rien n'appelle `evaluer` en production - c'est ce qui masque le défaut. Le jour du branchement UX, l'écran budget lève une TypeError sur la seule instance réelle disponible ; ou, s'il est branché derrière un `except Exception` comme il en existe déjà deux dans la chaîne, il rend « aucun constat » sur seize contrôles. Et le vrai piège est B-4 : il ne lève pas, il rend CONFORME. Un lecteur verrait donc « les deux totaux coïncident » produit par un chemin de types que personne n'a validé.



### C044 - Une résolution détruite par collision de clé primaire, pendant que le résumé annonce le nombre de lignes construites



- **Fichier** : `server/src/coproscope/vault/gouvernance_store.py:167`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/vault/gouvernance_store.py:163-167 : `INSERT OR REPLACE` puis `return len(lignes)` - le nombre de lignes soumises, jamais le nombre de lignes stockées. Et server/src/coproscope/modules/_resolutions_registre.py:274 appelle `remplacer_pour_documents(...)` sans lire son retour, puis ligne 284 rapporte `"resolutions": len(rows)`. Cas réel mesuré : sur l'assemblée de février 2026, un document produit 9 résolutions dont deux portent le numéro 3 - une ligne parasite décrivant un lot, et la vraie résolution 3, qui est le vote sur le non-renouvellement du mandat du syndic. Les deux fabriquent le même `resolution_id`, la même clé (resolution_id, etat, origine). Ma réplique en lecture seule de build_register mesure 174 lignes construites pour 173 clés distinctes. La base réelle porte bien 8 lignes pour cette assemblée. Reproduit isolément : `remplacer_pour_documents` a rendu 3 pour 2 lignes stockées.

- **Consequence** : Le journal de traitement écrit « resolutions: 9 » et le coffre en contient 8. La ligne perdue est l'une des deux en collision, c'est-à-dire potentiellement le vote sur le mandat du syndic. Aucun avertissement, aucun compteur ne bouge, et le seul module capable de voir le problème - `coherence`, qui détecte bien le segment fusionné - n'influence que la liste `pv_extraction_incomplete` et jamais le comptage. Aucun test n'assure que le retour de remplacer_pour_documents égale le nombre réellement stocké : test_gouvernance_store.py n'écrit jamais deux lignes de même clé.



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



### C050 - 178 lignes recoivent un type affirme `AUTO_CLASSIFIED` sans qu'aucun texte n'ait ete lu, et rien dans le registre ne les distingue des autres



- **Silencieux** : oui

- **Preuve** : 1128 lignes sur 3447 (32,7 %) ont `text_char_count` vide ou nul ; parmi elles 178 portent `classification_status = AUTO_CLASSIFIED` : 73 Facture, 38 Convocation_AG, 36 Contentieux_Nominatif, 9 CR_CS, 5 Annexe_Comptable, 4 Devis, 3 Diagnostic_Technique, et 10 autres. Leur `status_ocr` est `OCR_REQUIRED` pour 1039 des 1128. Le type vient donc uniquement du nom de fichier et du chemin, via `_text_sample` (01_inventory_and_extraction.py:558) qui empile `file_name`, `original_path` puis le texte, et retourne la concatenation - un segment de chemin compte comme preuve de contenu. Dans le second cabinet, `2026-06-29_AG_Convoc-Courrier.pdf` est classe Courrier alors que son texte extrait ne contient que des marqueurs de pagination. Aucune de ces 178 lignes n'a le statut `TEXTE_INSUFFISANT`, qui n'est emis 0 fois.

- **Consequence** : Le registre ne distingue pas "j'ai lu et j'affirme" de "je n'ai rien lu et j'affirme". Les deux s'ecrivent AUTO_CLASSIFIED. Une interface qui affiche le type sans afficher sur quoi il repose presente une inference de nom de fichier avec la meme assurance qu'une lecture.



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



### C054 - Le registre porte trois copies de la même assemblée avec trois comptages différents, et la seule copie datée est celle qui contredit l'étalon



- **Silencieux** : oui

- **Preuve** : Instance tilleul_pseudo_reconstruite, table `resolutions`, 173 lignes. Groupement par ag_id : AG-2024-07-03 (55 lignes, 4 doc_id), AG-DOC-7139EDAD85E4 (55 lignes), AG-DOC-729CCCF88863 (55 lignes), AG-2026-02-26 (8). Les trois premiers groupes portent chacun les numéros 1 à 55. Issues par groupe - AG-DOC-7139 : 39 ADOPTEE / 7 REJETEE / 8 PAS_DE_VOTE / 1 VOTE_SANS_FORMULE, ce qui est l'étalon exact. AG-DOC-729C : identique. AG-2024-07-03 : 38 / 7 / 7 / 2 / 1 SANS_ISSUE_TRACEE - soit une adoptée de moins que l'étalon. Comparaison résolution par résolution : les trois copies divergent sur 3 des 55 (n°7 : VOTE_SANS_FORMULE contre ADOPTEE ×2 ; n°39 : SANS_ISSUE_TRACEE contre PAS_DE_VOTE ×2 ; n°28 : majorité annoncée perdue dans une copie). Les deux copies non datées ont aussi perdu valide_du et valide_au (0/55 chacune, contre 6 et 2 pour la copie datée). Rien ne les oppose : les clés (resolution_id, etat, origine) diffèrent par le doc_id, donc les trois coexistent sans conflit. Après mon versement, `acte_id_resolution` produit 173 identifiants distincts - 0 collision, donc 3×55 lignes à l'écran pour une seule assemblée réelle.

- **Consequence** : Quatre comptages concurrents pour la même notion, exactement le défaut numéro un du produit, reproduit dans le magasin qui devait le rendre impossible. Et le choix par défaut est le mauvais : la copie que le modèle sait dater est celle qui dit 38 adoptées là où le procès-verbal en porte 39. L'écran affichera trois fois la résolution n°7 avec deux issues contradictoires, sans jamais dire que c'est le même document.



### C055 - Le second cabinet numérote 11.1 à 11.8 ; le registre n'a pas de colonne sous_numero et douze résolutions se réduisent à quatre actes



- **Silencieux** : oui

- **Preuve** : Mesure sur les 22 textes du second cabinet (staging/text, lecture seule). 59 références « Résolution n°X[.Y] » distinctes, dont 8 hiérarchiques : 1.1, 11.1, 11.2, 11.6, 11.7, 11.8, 13.1, 22.1. La regex du registre, `_resolutions_motifs.NUMERO_RE_PREFIXE = r"(?i)r[ée]solution\s*n[°o]\s*(\d{1,3})"`, ne capture que la partie entière : 51 numéros distincts au lieu de 59. Le registre n'a aucune colonne `sous_numero` (29 colonnes vérifiées). Conséquence sur l'identité : `acte_id_resolution(date, '11')` appelé pour 11, 11.1, 11.2, 11.6, 11.7 et 11.8 rend six fois 'ACTE-AG-2026-06-29-R11'. Regroupements écrasés mesurés : {1, 1.1} → 1 acte_id ; {11, 11.1, 11.2, 11.6, 11.7, 11.8} → 1 ; {13, 13.1} → 1 ; {22, 22.1} → 1. Douze résolutions pour quatre identifiants, et l'écriture se fait en `INSERT OR REPLACE` : les huit autres disparaissent. Le paradoxe est écrit dans le code lui-même : le commentaire de `acte_id_resolution` dit que le sous-numéro a été ajouté « imposé par le second corpus » parce que sinon « 19.0, 19.2 et 19.4 » se seraient écrasés - la garde existe à l'arrivée, la source ne peut pas l'armer.

- **Consequence** : Chez le second syndic, deux résolutions sur onze disparaissent au versement, sans erreur et sans compteur d'écart. Et ce sont précisément les sous-résolutions qui portent chacune leur devis en pièce jointe nommée, donc les seules qui auraient pu répondre à « cet euro, qui l'a autorisé ». Le produit se présente comme généralisable à un autre cabinet : c'est le premier cabinet suivant qui le casse.



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



### C059 - La file 'triee par montant en jeu' met le plus gros ecart en dernier



- **Fichier** : `server/src/coproscope/modules/_actes_constats.py`

- **Silencieux** : oui

- **Preuve** : _actes_constats.py:122 fait porter a MONTANT_DIVERGENT la valeur signee `e.montant_paye - e.montant_autorise`, et actes_autorisation.constats() trie ordre='montant_en_jeu IS NULL, montant_en_jeu DESC, code, sujet_id'. Mesure: acte A-PETIT 500 votes / 700 payes -> montant_en_jeu=200.0, rang 1; acte A-GROS 100 000 votes / 1 000 payes -> montant_en_jeu=-99000.0, rang 2.

- **Consequence** : Le cas le plus couteux pour la copropriete - 99 000 EUR votes et non depenses, avec une depense symbolique rattachee qui empeche ACTE_SANS_EXECUTION de porter - arrive apres un ecart de 200 EUR dans une file dont la docstring promet un tri par montant en jeu.



### C060 - L'obligation de reddition de comptes est muette quand l'assemblee existe mais n'est pas typee



- **Fichier** : `server/src/coproscope/modules/_actes_constats.py`

- **Silencieux** : oui

- **Preuve** : OBLIGATION_NON_TENUE exige `m.echeance <> ''` (_actes_constats.py:75), et il n'existe pas de pendant a URGENCE_JAMAIS_PORTEE pour la regle AG_APPROBATION_COMPTES (le constat ligne 84 exige regle='AG_SUIVANTE'). L'echeance ne se calcule que si une AG posterieure porte portee='APPROBATION_COMPTES'. Mesure: decision CS du 2024-03-01 plus une AG du 2025-06-01 laissee a portee='ORDINAIRE' -> echeance='' et codes emis: ACTE_SANS_EXECUTION, ACTE_SANS_FONDEMENT, aucun constat de reddition. La docstring justifie le silence par 'Si aucune n'est encore lue, l'echeance est vide - l'obligation n'est pas exigible'.

- **Consequence** : La justification confond 'aucune assemblee posterieure n'existe' et 'aucune assemblee posterieure n'a ete typee APPROBATION_COMPTES'. Dans le second cas l'obligation de l'article 21-5 est bel et bien exigible, et le modele ne dit rien. La ligne existe pourtant dans v_liens_manquants: elle est filtree juste avant d'atteindre l'ecran.



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



### C063 - CTRL_MAJORITE est déclaré comme septième contrôle mais n'est branché nulle part



- **Fichier** : `server/src/coproscope/modules/_actes_typologie.py`

- **Silencieux** : oui

- **Preuve** : `CONTROLES` en compte sept, dont `CTRL_MAJORITE = "MAJORITE"`. La vue `v_matrice_gouvernance` produit `cel_seuil`, `cel_avis_cs`, `cel_rapport_cs`, `cel_resolution`, `cel_annexe`, `cel_devis`, `cel_execution` - six contrôles plus la résolution, aucune `cel_majorite`. Grep sur tout `server/src` : `CTRL_MAJORITE` n'apparaît que dans sa propre définition et dans le tuple. Mesuré : `any('MAJORITE' in v for v in HORS_CONTROLE.values())` rend False, et `portees_soumises('MAJORITE')` rend 11 sans qu'aucun appelant existe. Le constat MAJORITE_NON_ENONCEE n'est borné par aucune portée : `_actes_constats.py` ne passe la matrice qu'à un seul contrôle, EXECUTION.

- **Consequence** : La note de lot annonce « les sept contrôles du modèle » et écrit « S'applique : majorité » pour cinq types, comme si la matrice gouvernait ce contrôle. Elle ne le gouverne pas. Un retrait de MAJORITE écrit dans HORS_CONTROLE n'aurait aucun effet observable, et personne ne le saurait. Le docstring du module, « Sept, pas plus : un controle qui n'a ni cellule ni constat n'existe pas », décrit un invariant que le module ne tient pas.



### C064 - L'invariant « une portée inconnue garde tous ses contrôles » est faux pour la seule portée inconnue qui existe, et le test le contourne



- **Fichier** : `server/src/coproscope/modules/_actes_typologie.py`

- **Silencieux** : oui

- **Preuve** : Le commentaire de fin de `HORS_CONTROLE` dit : « PORTEE_ENGAGEMENT_DEPENSE et PORTEE_ORDINAIRE n'ont aucune exclusion ». La boucle placée juste après (`for _portee in PORTEES: if _portee not in RAPPORT_CS_EXIGIBLE: HORS_CONTROLE.setdefault(_portee, {})[CTRL_RAPPORT_CS] = …`) ajoute RAPPORT_CS à ORDINAIRE. Mesuré : `HORS_CONTROLE['ORDINAIRE'] == {'RAPPORT_CS'}`. Le test censé garder l'invariant, `test_une_portee_inconnue_garde_tous_ses_controles`, interroge la chaîne « PORTEE_INVENTEE » - une valeur qui n'existe dans aucun vocabulaire et que le code n'écrit jamais - au lieu de PORTEE_ORDINAIRE, qui vaut 2 lignes sur 55 et 36 sur 91 dans le corpus.

- **Consequence** : Le commentaire décrit le contraire de ce que la ligne suivante fait, et le test protège une valeur qui n'arrive jamais pendant que la valeur réelle perd un contrôle. Le fond est défendable ; la contradiction entre le texte, le code et le test ne l'est pas, parce qu'elle rend l'invariant invérifiable au moment où on voudra s'y fier.



### C065 - Le cumul de delegation devient illimite quand la periode n'est pas lue, et le motif parle quand meme d'une periode



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py`

- **Silencieux** : oui

- **Preuve** : _actes_vues.py:313-314: `AND (d.valide_du = '' OR dep.date_depense >= d.valide_du) AND (d.valide_au = '' OR dep.date_depense <= d.valide_au)`. Mesure: delegation votee le 2023-01-15, plafond 5 000, valide_du et valide_au vides, trois depenses de 2 000 datees 2023, 2024 et 2026 -> depenses_cumulees=3, cumul=6000.0, constat PLAFOND_DEPASSE 'Delegation votee le 2023-01-15 : 3 depenses cumulees pour 6000.00 EUR sur la periode, plafond arrete a 5000.00 EUR', date_fait vide. Avec la periode lue (2023-01-15..2025-01-14) la meme base rend cumul=4000.0 et aucun constat - la vue est correcte des que la periode existe.

- **Consequence** : Un plafond de deux ans est compare a un cumul de tous les temps, et la phrase du constat dit 'sur la periode' alors qu'aucune periode n'est connue. Comme valide_au n'est renseigne que sur 2 lignes sur 173 dans le coffre reel, c'est le cas nominal, pas le cas limite.



### C066 - SANS_ISSUE_TRACEE n'a ni cellule distincte ni constat: il se confond avec une piece manquante



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py`

- **Silencieux** : oui

- **Preuve** : _actes_vocabulaire.RESULTATS declare cinq etats. _actes_vues.py:393-404 (cel_resolution) en traite quatre et renvoie l'`ELSE 'ABSENT'` pour le cinquieme. ISSUE_NON_ENONCEE (_actes_constats.py:139) ne couvre que VOTE_SANS_FORMULE. Mesure: un acte a resultat='SANS_ISSUE_TRACEE' rend cel_resolution='ABSENT' et zero constat. Le coffre reel porte 4 lignes SANS_ISSUE_TRACEE (dont 1 sur AG-2024-07-03 et 3 sur AG-2026-02-26).

- **Consequence** : Une resolution dont le proces-verbal ne trace aucune issue est affichee comme une resolution dont la source est manquante - c'est-a-dire comme un probleme de document, pas comme un fait constate sur le document. La distinction que _actes_vocabulaire pose en tete de module ('le document ne le dit pas' n'est pas 'on ne sait pas') est perdue au dernier metre.



### C067 - Un acte PROJETE porte deja des manquements dates



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py`

- **Silencieux** : oui

- **Preuve** : _V_LIENS_MANQUANTS (_actes_vues.py:244-271) joint les exigences sur la seule `nature` et ne filtre jamais `etat`, alors que v_taux_gouvernance filtre etat='CONSTATEE' et que les sous-requetes d'echeance le font aussi. Mesure: decision CS etat='PROJETEE' du 2026-05-01, plus une AG d'approbation des comptes du 2026-06-01 -> constats ACTE_SANS_FONDEMENT et OBLIGATION_NON_TENUE 'Decision du 2026-05-01 : aucun compte rendu devant l'assemblee du 2026-06-01'.

- **Consequence** : Une resolution seulement proposee dans une convocation - le cas d'usage explicite de l'etat PROJETEE - est declaree en manquement avant que la decision existe. Le modele affirme qu'une obligation n'a pas ete tenue par un acte qui n'a pas encore ete pris.



### C068 - Une correction humaine qui porte sur la date, le numero ou le sous-numero cree un second acte au lieu de corriger le premier



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py (_V_ACTES, _V_DIVERGENCES)`

- **Silencieux** : oui

- **Preuve** : Mesure. Acte extrait sans date (ACTE-AG-SANS-DATE-DOC-PV-R12), puis correction humaine qui renseigne la date : l'identifiant devient ACTE-AG-2024-07-03-R12. Resultat : v_actes rend 2 lignes (l'acte SANS-DATE en EXTRAIT reste vivant, il n'a pas d'homologue CORRIGE_HUMAIN sur son propre acte_id), et v_divergences_humaines est vide puisqu'elle joint sur acte_id. Le cas contraire tient : une correction sur `resultat` ou `montant_autorise` survit bien a une re-extraction et la divergence apparait (mesure : montant 23 460,00 machine contre 18 240,00 humain, resultat ADOPTEE contre REJETEE).

- **Consequence** : La promesse « la correction humaine gagne a la lecture, et l'ecart reste visible » ne tient que pour les champs qui n'entrent pas dans l'identifiant. Corriger la date - c'est-a-dire exactement le defaut que le module documente comme mesure et reel - double l'acte au lieu de le reparer, et le double n'est signale nulle part.



### C069 - La vue de divergence ne couvre que 5 des 26 champs de l'acte



- **Fichier** : `server/src/coproscope/modules/_actes_vues.py (_V_DIVERGENCES)`

- **Silencieux** : oui

- **Preuve** : Mesure : ACTE_FIELDS compte 26 champs, _V_DIVERGENCES en compare 5 (date_effet, montant_autorise, resultat, portee, valide_au). Non couverts, entre autres : nature, numero, sous_numero, entreprise, majorite_annoncee, majorite_requise, majorite_appliquee, montant_source, entreprise_source, etat, exercice, valide_du, objet.

- **Consequence** : « L'ecart entre ce que la machine a lu et ce qu'un humain a corrige est lui-meme une information » ne vaut que pour un cinquieme du modele. Une correction humaine sur la majorite annoncee ou sur l'entreprise gagne bien a la lecture mais n'apparait dans aucune divergence : le produit perd la trace de la ou la machine se trompe systematiquement, alors que c'est la valeur qu'il revendique.



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



### C074 - Le module qui sait dire si une majorité était atteignable n'est branché sur rien, et son contrat de types ne correspond pas au registre



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py:340`

- **Silencieux** : oui

- **Preuve** : Grep sur tout server/ : `decompte_resolution`, `regime_de_majorite` et `majorite_25_atteignable` n'ont qu'un appelant, tests/test_decompte_voix.py. 564 lignes, aucun consommateur en production. Et la couture est piégée : `decompte_resolution` déclare `voix_pour: Optional[int]` et distingue `None` (« le procès-verbal ne publie pas les voix » → ETAT_DECOMPTE_ABSENT) de 0. Or le registre stocke tout en TEXT et `Resolution.voix_pour` est déclaré `str = ""` (_resolutions_extraction.py:39), la chaîne vide signifiant justement « non publié ». Le convertisseur qui reste à écrire est exactement celui où `int(x or 0)` transforme « non publié » en « zéro voix pour ».

- **Consequence** : Le fait établi le 2026-09-04 - avec 4 899 voix présentes sur 10 000, aucune des 21 résolutions chiffrées n'atteint 5 001, donc l'article 25 était arithmétiquement hors d'atteinte - est calculable par ce module et affiché nulle part. L'écran des résolutions montre « Adoptée » et « article 25 » côte à côte sans jamais dire que le seuil ne pouvait pas être franchi. Et si l'adaptateur est écrit à l'économie au moment du branchement, 55 résolutions sans voix publiées deviendront 55 rejets confirmés à 0 voix, ce qui est une conclusion, pas une absence.



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



### C079 - gouvernance_store.lire avale toute OperationalError et rend une liste vide, y compris pour une colonne manquante



- **Fichier** : `server/src/coproscope/vault/gouvernance_store.py`

- **Silencieux** : oui

- **Preuve** : Dans `lire()` : `except sqlite3.OperationalError: return []`, sans distinction du message, sur un `SELECT * FROM table ORDER BY {ordre}` où `ordre` a pour défaut `"ag_id DESC, CAST(position AS INTEGER)"`. Une table de gouvernance dépourvue de `position` ou d'`ag_id` - c'est le cas de `traces_controle`, `liens_gouvernance` et `dossiers_depense`, dont aucune ne porte ces deux colonnes - rendrait 0 ligne sans erreur si l'appelant oublie de passer `ordre`. Le module voisin `_actes_store.lire_vue` a explicitement corrigé ce motif (« un no such column avalé par un except OperationalError large rend une liste vide indiscernable d'une absence de résultat ») ; la couche partagée sous-jacente ne l'a pas.

- **Consequence** : Le défaut que `_actes_store` documente comme déjà vécu - une colonne manquante rendant zéro au lieu de huit cent dix-huit - reste ouvert d'un cran plus bas, dans la couche que tous les objets de gouvernance partagent. Il ne se déclenche pas aujourd'hui parce que chaque appelant passe son `ordre` ; il se déclenchera au premier appelant qui ne le fera pas, et il rendra une liste vide.



### C080 - gouvernance_store : le risque du patch non applique est arme mais nul aujourd'hui, et il n'est silencieux que sur un des trois points



- **Fichier** : `server/src/coproscope/vault/gouvernance_store.py et gouvernance_store.PROPOSITION.patch`

- **Silencieux** : oui

- **Preuve** : Mesures. (a) Etendue reelle sur les deux bases d'instance existantes : la seule table presente est `resolutions`, 29 colonnes contre 29 dans RESOLUTION_FIELDS, aucune manquante, aucune en trop, cle primaire en base ('resolution_id','etat','origine') identique au code. Les tables convocations/devis_cites/declarations_ag et les cinq tables du lot actes n'existent dans aucune des deux bases. Verification systematique : aucun `ordre` de lecture declare (4 tables convocations/resolutions + 5 tables actes) ne cite une colonne absente de sa liste de champs. Risque realise a ce jour : nul. (b) Point 2 du patch : une colonne ajoutee apres creation ne provoque PAS d'ecriture partielle, elle leve « OperationalError: table t has no column named montant_vote », et la transaction est annulee - la ligne anterieure est intacte. C'est donc un echec bruyant, contrairement a ce que le patch redoute (« ou, pire selon le chemin, ecrit sans la colonne »). (c) Point 3 : lire() avale bien tout. Mesure sur trois appels : table absente -> [], ordre citant une colonne absente -> [], table presente et correcte -> 1 ligne. Deux des trois cas sont des erreurs et rendent la meme valeur qu'un registre vide. (d) Defaut non mentionne par le patch : changer la cle primaire dans le code est silencieusement ignore sur une base existante. Mesure : base creee avec cles ('id','origine'), puis ecriture avec cles ('id','etat','origine') de deux lignes qui ne different que par `etat` -> 1 seule ligne en base, la seconde a ecrase la premiere, DDL inchangee.

- **Consequence** : L'ordre d'application recommande par le patch (1 puis 2 puis 3) est le bon, mais la hierarchie de danger est a corriger : le point 2 protege d'une panne bruyante, le point 3 est le seul qui ferme un silence, et le trou (d) - non couvert par le patch - est le plus proche du besoin reel, puisque distinguer les trois representations concurrentes de l'AG du 03/07/2024 supposerait justement d'elargir la cle de `resolutions`, ce qui n'aurait aucun effet sur la base de Brice.



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



### C084 - Le vocabulaire de confiance diffère entre le registre et l'écran : les six seuils réels sont tous affichés « lu avec une confiance faible, relisez »



- **Fichier** : `server/src/coproscope/web/controle_gouvernance_view.py`

- **Silencieux** : oui

- **Preuve** : Registre réel : `confiance` vaut 'forte' (125 lignes), 'moyenne' (40), 'faible' (8) - mesuré. `controle_gouvernance_view.py:140` teste `"incertain": confiance not in ("haute", "")`, et la ligne 150 déclenche sur le même test le message « Le montant a été lu avec une confiance faible : relisez la résolution [...] Tant qu'il n'est pas confirmé, le seuil est une hypothèse. » `grep -rn '"haute"' server/src/` ne trouve aucun producteur de cette valeur pour la gouvernance. Mesure du panneau des seuils après versement : 6 seuils affichés, `incertain=True` sur les 6, alors que les deux résolutions sources portent toutes deux `confiance='forte'`. Le test traite par ailleurs la chaîne vide comme certaine : une confiance jamais lue s'affiche comme confirmée.

- **Consequence** : La polarité est inversée dans les deux sens à la fois. Le seuil le mieux lu porte l'avertissement du seuil mal lu, et le seuil dont la confiance n'a pas été lue n'en porte aucun. Le badge qui devait distinguer les deux les rend indistinguables. C'est le motif exact des deux jetons CSS jamais définis : deux vocabulaires qui ne se rencontrent jamais, et un rendu toujours plausible.



### C085 - Le garde-fou « pas de citation de mémoire » ne vérifie que la forme de l'identifiant, et les motifs de retrait n'en portent aucun



- **Fichier** : `server/tests/test_resolutions_typage.py`

- **Silencieux** : oui

- **Preuve** : `tests/test_resolutions_typage.py`, classe PasDeCitationDeMemoireTests : `MOTIF = re.compile(r"LEGIARTI\d{12}")` puis `self.assertRegex(ident, self.MOTIF)`. Une chaîne comme LEGIARTI000000000000 passerait. Ce test n'a attrapé aucun des constats 1, 4 et 5. Par ailleurs les motifs de `HORS_CONTROLE` - la partie opératoire, celle qui retire effectivement le contrôle et qui s'affiche à l'écran - ne portent aucun identifiant : ils citent « l'article 21 al. 2 », « l'article 18 II », « le decret art. 11 I », « decret art. 22 al. 2 » en clair. Seules les définitions de type, qui ne décident rien, sont sourcées.

- **Consequence** : Le dispositif de vérification est placé là où il ne décide de rien, et absent là où il décide. C'est exactement pourquoi le motif faux du constat 1 a pu être écrit et testé sans qu'aucun contrôle ne le rencontre.



### C086 - Sur le second cabinet, un proces-verbal sur quatre exercices est simplement invisible : extraction vide, score 0, aucun signal



- **Silencieux** : oui

- **Preuve** : Instance du second cabinet, 22 pieces, 4 exercices. `2025-06-30_AG_PV.pdf` : texte extrait reduit aux marqueurs `===== PAGE 2 =====`, score 0, `document_type = A_CLASSER`, `classification_status = A_CLASSER`. Les trois autres PV sont bien vus : `2026-06-29_AG_PV.pdf` -> PV_AG score 15, `PV AG 17062024.pdf` -> PV_AG score 65. Meme cas pour `2024-06-17_AG_Demandes-individuelles.pdf` et `2025-06-30_AG_Demandes-individuelles-.pdf`, score 0.

- **Consequence** : Le PV d'un exercice sur quatre n'existe pas pour le modele, et sa disparition prend la forme la plus benigne du registre : une ligne A_CLASSER parmi 2111 autres. Rien ne dit "ce PDF est un proces-verbal que je n'ai pas su lire" ; le statut TEXTE_INSUFFISANT, ecrit pour ce cas, ne peut pas etre emis puisqu'il exige que le type soit deja PV_AG.



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



### C090 - L'objet d'une resolution est recopie tel quel dans le motif d'un constat



- **Fichier** : `server/src/coproscope/modules/_actes_constats.py`

- **Silencieux** : oui

- **Preuve** : _actes_constats.py utilise substr(m.objet,1,60) et substr(e.objet,1,60) dans les motifs de ACTE_SANS_FONDEMENT et ACTE_SANS_EXECUTION. Mesure: un objet de la forme 'Demande individuelle de Mme [NOM] lot 214 - moteur de climatiseur' ressort integralement dans le motif du constat. _actes_schema pose explicitement qu'aucune colonne de texte integral n'existe pour que les noms de coproprietaires n'entrent pas dans le magasin de gouvernance; `objet` est du texte libre non contraint.

- **Consequence** : La barriere de confidentialite porte sur la colonne texte et pas sur l'objet, alors que la resolution 35 de l'etalon est precisement une demande individuelle et que ce genre d'intitule nomme couramment le demandeur. Le motif d'un constat est une chaine destinee a l'ecran et potentiellement a un export.



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



### C093 - CTRL_MAJORITE est declare parmi les sept controles et n'est consulte nulle part



- **Fichier** : `server/src/coproscope/modules/_actes_typologie.py`

- **Silencieux** : oui

- **Preuve** : _actes_typologie.py:166 declare CTRL_MAJORITE et l'inclut dans CONTROLES. Grep sur server/src: portees_soumises() n'est appele qu'avec des relations de lien et avec 'EXECUTION'; ni MAJORITE_NON_ENONCEE ni ISSUE_NON_ENONCEE (_actes_constats.py:132-149) ne consultent HORS_CONTROLE. La docstring de CONTROLES affirme pourtant 'Sept, pas plus: un controle qui n'a ni cellule ni constat n'existe pas'.

- **Consequence** : Sans effet mesurable aujourd'hui (portees_soumises('MAJORITE') rend 11/11), mais la barriere annoncee n'est pas branchee: le jour ou une portee devra sortir du controle de majorite, l'ecrire dans HORS_CONTROLE ne changera rien et personne ne le verra.



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



### C096 - Le contrat de types avec l'extracteur n'est pas defendu, et le garde None ne couvre pas la chaine vide



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : non

- **Preuve** : Les champs de Resolution (_resolutions_extraction.py l.33-36) sont des str, vides par defaut. Mesures: voix_pour="" franchit le garde `if voix_pour is None` (l.377) puis leve ValueError; voix_totales="10000" leve TypeError sur `voix_totales <= 0`; voix_pour="4746" fonctionne normalement; voix_pour=100.9 est tronque a 100 par int() sans un mot.

- **Consequence** : Bruyant, donc a moitie corrige - sauf sur un point: la chaine "4746" marche. Un pipeline branche sur des chaines paraitra fonctionner jusqu'au premier champ vide, et l'exception tombera alors sur une resolution particuliere, pas au branchement. Le garde qui devait rendre DECOMPTE_ABSENT rend une trace.



### C097 - Cinq des six constantes de source sont mortes, et l'unanimite de l'article 26 n'existe pas



- **Fichier** : `server/src/coproscope/modules/_decompte_voix.py`

- **Silencieux** : oui

- **Preuve** : Comptage des occurrences dans le fichier: SOURCE_VOIX 1, SOURCE_CLE_SPECIALE 1, SOURCE_FEUILLE_PRESENCE 1, SOURCE_CORRESPONDANCE_AMENDEE 1, SOURCE_CORRESPONDANCE_PRESENT 1 - soit leur seule definition. Seule SOURCE_FEUILLE_ANNEXEE est reellement attachee a un verdict. Mesure: un verdict article 24 rendu sur une cle speciale (denominateur_ecrit=1155) porte sources = (('loi 65-557, art. 24 I', ...),) uniquement; l'article 10, fondement du scrutin restreint, n'y figure pas. Par ailleurs 0 occurrence de "unanim" dans le module, alors que la doc note (l.116-117) que l'article 26 ajoute des cas d'unanimite.

- **Consequence** : Une UI qui affiche verdict.sources ne montrera jamais le fondement du scrutin par cle speciale, ni celui de la feuille de presence, ni celui du vote par correspondance. Et une resolution soumise a l'unanimite passe en ADOPTEE_CONFIRMEE des les deux tiers atteints.



### C098 - Un montant de seuil illisible s'affiche comme une cellule vide, pas comme un montant illisible



- **Fichier** : `server/src/coproscope/web/_controle_gouvernance_source.py:158`

- **Silencieux** : oui

- **Preuve** : server/src/coproscope/web/_controle_gouvernance_source.py:158-162, `euros()` : `except (TypeError, ValueError): return ""`. En face, controle_gouvernance_view.py:133 écrit `euros(montant) if montant else "montant non lu"`. Une chaîne non vide mais non convertible - « environ 2 000 EUR », un montant océrisé - passe le test de vérité, puis `euros` rend la chaîne vide. Le libellé « montant non lu », qui existe et qui est juste, n'est pas atteint. Voisin : ligne 454, `_nombre(...) or 0.0` écrase à la fois l'absence de montant et un vrai 0,00 EUR ; l'usage est limité au tri (ligne 472), donc l'impact est faible.

- **Consequence** : Le rappel des seuils en tête du tableau - celui qui arme tous les autres contrôles - affiche un seuil dont la valeur est un blanc. Un blanc se lit comme « pas de seuil » ou comme un défaut d'affichage, jamais comme « un montant est écrit et je ne sais pas le lire ». La phrase juste est déjà écrite dans le code, à un test de vérité près.



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

