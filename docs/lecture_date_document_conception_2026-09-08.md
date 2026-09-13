# Lire la date d'un document: note de conception

**Campagne de mesure du 2026-09-08.** Cinq sondes sur le corpus reel, chaque
constat attaque par un agent charge de le refuter, puis synthese. Aucun fichier
du depot ni des instances n'a ete modifie. Le corpus est designe par son
pseudonyme.

**Ce que cette note n'est pas.** Elle mesure des proprietes de FORME du texte.
Elle ne mesure aucune justesse: aucun etalon etabli a la main n'existe pour ce
corpus. Un taux de bonne lecture ne pourra etre annonce qu'apres constitution
d'un etalon manuel.

---

NOTE DE CONCEPTION - LE LECTEUR DE DATE D'UN DOCUMENT

Etat: synthese de cinq sondes de mesure et des attaques menees contre leurs constats. Aucun fichier du depot ni des deux instances n'a ete modifie. Mes propres verifications sont dans quatre scripts jetables du scratchpad (`s1.py` a `s4.py`), lances depuis `C:\Users\brice\CoproScope\coproscope\server` avec `PYTHONIOENCODING=utf-8 PYTHONPATH=src .venv\Scripts\python.exe`.

Corpus: `Tilleuls (pseudo)`, 858 documents, dans `C:\Users\brice\CoproScope\instances\test_identite_ag_20260908`. Second cabinet: `C:\Users\brice\CoproScope\instances\erables_pseudo_test`, 22 documents.

---

## Avant tout: le chiffre de depart du briefing ne se reproduit pas

Le briefing annonce "133 documents dates sur 858, soit 16%". Trois passages independants trouvent autre chose, et le mien aussi.

Le lecteur actuel rend, sur les 858 documents: **140 dates lues dans le texte, 47 lues dans le nom du fichier, 671 absences** (`s2.py`, qui appelle la vraie fonction `date_du_document` du module de production sur les 858 textes). Le registre porte 187 valeurs, ce qui est exactement 140 + 47.

Et surtout, le denominateur est faux dans l'autre sens: **149 des 858 documents ont un texte extrait entierement vide** - ce sont des PDF scannes jamais passes a la reconnaissance de caracteres. **159 ne contiennent aucune annee nulle part** (`s1.py`). Aucun lecteur de date, aussi bon soit-il, ne peut rien pour eux: le probleme est en amont, dans l'extraction du texte, pas dans la lecture de la date.

Le vrai denominateur de la question "sait-on lire la date d'un document?" est donc **709**, pas 858. C'est une nuance qui change le diagnostic: on ne rate pas 84% des documents, on rate environ 80% de ceux qui ont un texte, et 17% du corpus n'a meme pas de texte a lire.

---

## 1. L'AXE

Ce qui varie d'un document a l'autre n'est pas une liste de formes. C'est **neuf degres de liberte**, dont huit portent sur la maniere d'ECRIRE la date, et un - le neuvieme - porte sur ce que la suite de chiffres SIGNIFIE dans la phrase. C'est celui-la qui manque entierement au lecteur actuel, et c'est lui qui coute le plus cher.

**Axe 1 - le separateur entre les champs.** Valeurs vues: barre oblique, point, tiret, souligne, espace ordinaire, espace insecable, retour a la ligne, et rien du tout. Un separateur se CAPTURE, il ne s'enumere pas.

**Axe 2 - l'ordre des champs.** Jour-mois-annee (massif) et annee-mois-jour (rare). Mois-jour-annee: zero occurrence sur 880 documents.

**Axe 3 - la largeur des champs.** L'annee sur quatre chiffres ou sur deux; le jour et le mois avec ou sans zero de tete.

**Axe 4 - la substance du mois.** Le mois est le seul champ qui change de nature: un nombre, un mot entier, un mot tronque a une longueur libre (`jan.`, `janv.`, `sept.`, `dec.`), ou un mot epele en toutes lettres.

**Axe 5 - la casse et les accents.** Quinze ecritures differentes pour les seuls mois de juillet, decembre et aout.

**Axe 6 - la granularite.** Jour+mois+annee, mois+annee, jour+mois sans annee, trimestre, semestre, annee seule.

**Axe 7 - la continuite de la chaine.** Une date peut etre coupee par un retour a la ligne (`aout` puis `2024`) ou collee a son voisin (`DECEMBRE2025`): 195 documents concernes.

**Axe 8 - la fidelite des caracteres.** La chaine de lecture abime les caracteres: `O3/07/2026` avec un O majuscule dans un champ etiquete "Date", `jui!let`, `Mai.`. C'est un axe de degradation, pas de forme.

**Axe 9 - LE ROLE DU JETON DANS LA PHRASE.** Une suite de chiffres qui ressemble a une date est, dans ce corpus: une date, un numero de decret ou de loi, un numero de devis ou de facture, un numero de compte bancaire, un numero de telephone, un tantieme de copropriete, une heure, un numero de resolution, une plage de numeros de rue, un montant comptable, ou un nom de fichier cite dans le texte.

Mesure de l'axe 9 sur les 140 dates que le lecteur lit aujourd'hui dans le texte (`s3.py`, qui classe chaque premier resultat par ce qui le precede): **106 sont precedees d'un marqueur de numerotation** (`decret n°`, `Devis n°`, `Ref :`, `Facture n°`), **10 sont une heure** (le caractere `:` suit immediatement), et sur les 24 restantes, la lecture a la main de l'echantillon montre presque uniquement des **noms de fichiers cites dans le corps du texte**. Autrement dit: **le lecteur actuel ne lit pas des dates, il lit des numeros de piece.**

Le cas le plus lourd, un seul motif: 49 documents sont dates de novembre 2012 parce qu'ils citent la clause standard `decret n° 2012-1115`. Ce sont des factures de 2024 a 2026.

---

## 2. L'INVARIANT

Ce qui reste vrai tout le long de ces axes, et qui ne depend d'aucun cabinet.

**1. Une date est un triplet ordonne (quantieme, mois, millesime) dont des champs peuvent manquer, jamais se repeter ni s'inverser entre eux.** Ce qui varie, c'est comment les champs sont ecrits et separes. Ce qui ne varie pas, c'est qu'il y a au plus un quantieme, au plus un mois, au plus un millesime, et que le mois est encadre par les deux autres quand les trois sont presents.

**2. Le domaine de chaque champ est ferme par le calendrier, pas par l'observation.** Un quantieme est entre 1 et 31, un mois entre 1 et 12, et la date doit exister reellement (il n'y a pas de 31 fevrier). C'est le seul filtre qui n'a pas besoin d'avoir vu le corpus.

**3. Un mot de mois est toujours un prefixe d'un des douze noms du calendrier**, une fois les accents et la casse mis de cote. Un cabinet inconnu qui ecrirait `sep.` ou `juill.` tombe dedans sans qu'on ait rien ajoute. Une liste d'abreviations codee en dur, elle, les rate.

**4. Un jeton n'est une date que si rien dans son voisinage ne le designe comme autre chose.** Cet invariant se formule en negatif a dessein: on ne peut pas enumerer tout ce qu'un numero peut etre, mais on peut exiger qu'un jeton retenu comme date ne soit pas colle a un marqueur de numerotation ni noye dans une suite de chiffres plus longue.

**5. Pour l'ordre jour/mois, l'invariant n'est pas "le jour est en premier". C'est: un champ superieur a 12 est forcement un quantieme.** Cette regle est arithmetique et vraie partout.

---

## 3. CE QUE LE CODE DOIT EN FAIRE

Six etapes, dans cet ordre.

**Etape 1 - normaliser sans perdre la position.** Travailler sur une copie du texte ou les accents sont retires, la casse abaissee, l'espace insecable ramene a un espace ordinaire, et le retour a la ligne traite comme un separateur possible. Garder la correspondance avec le texte d'origine, pour pouvoir citer la chaine reellement ecrite.

**Etape 2 - proposer des CANDIDATS par la forme generique.** Un candidat est: un champ, un separateur quelconque (capture, jamais choisi dans une liste), un champ, un separateur quelconque, un champ. Le champ du milieu est soit un nombre, soit un mot dont on teste s'il est prefixe d'un des douze noms de mois. On ne cherche pas "les formes connues": on cherche la structure.

**Etape 3 - fermer par le calendrier.** Un candidat dont la date n'existe pas est jete. C'est ce que le module fait deja pour le mois et le jour; il faut l'etendre a la validite reelle de la date.

**Etape 4 - filtrer par le role (l'axe 9).** Jeter tout candidat qui est precede immediatement d'un marqueur de numerotation, colle a d'autres chiffres, ou suivi d'un `:` (c'est une heure). Ce filtre est le plus important du dispositif, et il doit compter ce qu'il jette, avec la raison.

**Etape 5 - choisir, et non prendre le premier.** Voir la section 6.

**Etape 6 - rendre une reponse qui se defend.** La sortie n'est jamais une date nue. Elle porte: la valeur, sa granularite (jour, mois, trimestre, annee), la chaine exactement telle qu'elle est ecrite dans le document, sa position, la regle qui l'a retenue, et **les hypotheses employees** (pivot de siecle, convention jour-en-premier). Quand rien ne sort, la reponse est une absence nommee - ce que le module fait deja aujourd'hui, et c'est son point fort.

---

## 4. HORS DES VALEURS OBSERVEES

Ce qui se passe si un troisieme syndic ecrit ses dates autrement.

**Separateur inconnu** (point median, barre verticale, tiret long). Un code qui capture le separateur continue de lire. Un code qui liste `[-_. ]` - c'est le code actuel - ne lit rien, et le document tombe dans le tas des sans-date. Degradation acceptable, a condition que ce tas soit compte et visible.

**Ordre annee/mois/jour avec barres obliques.** Zero occurrence dans les deux corpus, mais la forme existe. Un code qui decide l'ordre par la LARGEUR des champs (quatre chiffres = millesime) la lit sans l'avoir jamais vue.

**Ordre mois-jour-annee.** C'est le seul point ou l'echec serait silencieux ET faux: `03/07/2024` serait lu 3 juillet au lieu du 7 mars, sans aucun signal. La protection est mesurable et elle est decrite en section 5.

**Abreviation de mois inconnue** (`sep`, `juill.`). Le test de prefixe l'absorbe sans modification. Il rejette proprement `7bre` et les mois en langue etrangere: il rend une absence, pas une erreur.

**Millesime epele autrement** (`mil neuf cent quatre-vingt-cinq`, formule notariale classique). Zero occurrence dans les deux corpus. Un lecteur qui traite l'epellation comme un axe la lit; un lecteur qui a code le mot `deux mille` rend une absence - degradation propre.

**Annee sur deux chiffres avant 2000.** Il n'existe pas d'invariant qui sauve ce cas, et il est deja present: `loi du 10/07/65` devient 2065. Voir section 7.

**Role du jeton, valeur inconnue.** Un nouveau syndic numerotera ses pieces d'une facon qu'aucun garde-fou ne prevoit; neuf familles de faux amis ont deja ete mesurees, la dixieme arrivera. C'est pourquoi la reconnaissance doit **preferer l'absence au doute**, et pourquoi le nombre de documents laisses sans date est un indicateur a publier, pas un echec a cacher.

---

## 5. LA QUESTION DE L'ORDRE JOUR/MOIS: tranchee pour 553 documents, indecidable pour 107

Mesure directe sur les 858 documents (`s1.py`), sur toutes les dates ecrites avec des barres obliques:

- **6269 occurrences, dans 553 documents, ont un premier champ superieur a 12.** Elles prouvent, arithmetiquement, que le jour est ecrit en premier.
- **0 occurrence prouve l'inverse.** Aucune.
- **5165 occurrences ne prouvent rien**: leurs deux premiers champs sont inferieurs ou egaux a 12, donc les deux lectures sont possibles.
- **198 documents ne contiennent aucune date a barres obliques.**
- **107 documents contiennent des dates a barres obliques dont AUCUNE ne tranche.** Pour ceux-la, l'ordre repose sur une convention supposee, jamais sur une mesure.

Le second cabinet donne le meme resultat: 273 occurrences dans 17 documents prouvent le jour en premier, 0 prouve l'inverse.

Une deuxieme ressource existe et elle est mesuree: dans 143 documents, une date ecrite en chiffres est aussi ecrite en lettres ailleurs dans le meme document; la lecture jour-mois-annee concorde 259 fois, la lecture mois-jour-annee 0 fois.

**Decision proposee.** L'ordre se decide **document par document**, pas une fois pour toutes:

1. si une date du document tranche d'elle-meme (un champ superieur a 12), cet ordre s'applique a tout le document - 553 documents sur 858;
2. sinon, si une date en lettres confirme une date en chiffres, elle tranche;
3. sinon seulement, la convention francaise s'applique, **et la date porte la mention de cette hypothese** - 107 documents.

Cette construction est aussi la defense contre le syndic anglo-saxon: dans un document en convention americaine, ce sont les DEUXIEMES champs qui depasseraient 12. L'etape 1 le detecterait et basculerait, au lieu de se tromper en silence. Un lot qui ne compte pas cela livre une lecture qui a seulement l'air juste.

---

## 6. QUELLE DATE EST CELLE DU DOCUMENT: "la premiere" est refutee

"La premiere date rencontree" est le choix actuel. Trois mesures independantes le refutent.

**Preuve 1.** Sur les 140 dates lues aujourd'hui dans le texte, 106 sont precedees d'un marqueur de numerotation et 10 sont une heure (`s3.py`).

**Preuve 2.** Test de corroboration: pour chacune des 140 valeurs, on cherche ailleurs dans le meme document une date ecrite comme une date qui la confirme. **82 sur 140, soit 59%, ne sont confirmees par aucune** (25 le sont au jour pres, 33 au mois seulement) - `s2.py`. Et une valeur non corroboree sort aujourd'hui avec exactement le meme statut qu'une valeur juste.

**Preuve 3, la plus parlante.** Sur les 639 documents qui portent la forme dominante, la premiere date a barres obliques est precedee **108 fois** de `A REGLER AVANT LE`: c'est une echeance de paiement. Exemple litteral d'une facture: `N° 780000518262 - 2 mai 2026 [...] A REGLER AVANT LE 18/05/2026`. La date du document est le 2 mai, ecrite trente caracteres plus tot, dans une AUTRE forme. Chez le second cabinet, **12 des 17 documents** portant cette forme ont pour premiere occurrence une date qui n'est demonstrablement pas celle du document (`delivree le`, `comptes arretes au`, `Etat financier apres repartition au`).

**Le cas le plus dangereux n'est pas la valeur absurde, c'est la valeur VOISINE.** `Devis N° : JR D2025.04.26  Date : 25/04/2025`: le lecteur rend le 26 avril, le document dit le 25 avril. Un jour d'ecart. Aucun controle de vraisemblance ne peut detecter cela: la valeur est une date possible, proche, du bon mois.

**Par quoi la remplacer.** Par un choix entre candidats, en trois temps:

1. **eliminer** les candidats disqualifies par leur voisinage (axe 9);
2. **preferer** ceux qui se trouvent dans la zone d'en-tete du document - un courrier, une facture, une convocation portent leur date d'emission en tete - et ceux qui sont annonces par une etiquette d'emission (`Date :`, `Marseille, le`, `fait a ... le`, `L'an ...`, `Ce jour ...`);
3. **s'abstenir** si plusieurs candidats survivants sont en desaccord, en listant les candidats au lieu d'en elire un.

**Le prix, mesure.** J'ai implemente cette regle en prototype (`s4.py`: candidats bien formes dans les 800 premiers caracteres du corps, apres disqualification du voisinage) sur les 858 documents:

- **311 documents rendent un candidat unique** - contre 140 aujourd'hui, dont la quasi-totalite sont faux;
- **76 documents rendent plusieurs candidats en desaccord**: ils doivent etre declares ambigus, pas arbitres au hasard;
- **471 documents ne rendent rien**, dont les 149 qui n'ont aucun texte.

Sur le second cabinet: 7 uniques, 5 ambigus, 10 sans candidat sur 22.

**Ce prototype n'est pas la solution, et il faut le dire.** Sa liste de disqualification (`n°`, `decret`, `devis`, `avant le`, `periode`...) est **elle-meme une liste de modalites observees** - exactement ce que la regle du depot interdit. Elle ne tient que si chaque disqualification est comptee et publiee: le jour ou un nouveau cabinet numerotera autrement, le signal doit etre une hausse du nombre de documents "sans candidat", jamais une date fausse rendue en silence.

---

## 7. CE QUI RESTE INDECIDABLE, ET CE QUE CA COUTE

1. **107 documents ou l'ordre jour/mois n'est prouve par rien.** La convention francaise leur donnera une reponse dans 100% des cas et une reponse fausse dans un pourcentage inconnu. Ils doivent porter la mention de l'hypothese, pas une date nue.

2. **Le pivot de siecle des annees sur deux chiffres.** Environ 275 documents en dependent. Le corpus melange des millesimes 2015-2027 et des millesimes 1965, 1967, 1985 dans la MEME forme: `la loi du 10/07/65` deviendrait 2065. Aucune regle de pivot ne separe les deux - tout pivot est une modalite. Cout mesure: sur 11 documents qui s'annoncent proces-verbal, 5 portent cette forme et 3 rendraient une annee posterieure a 2030.

3. **Les formes a deux champs.** `48/1995` dans une liste d'opposants a une assemblee est un **tantieme de copropriete**, pas un mois/annee. Aucun signal de forme ne les separe; seul le voisinage le fait, et le voisinage n'est pas un invariant.

4. **149 documents sans aucun texte et 159 sans aucune annee.** Ce residu appartient a l'extraction, pas a la lecture. Il doit etre compte separement, sinon il gonfle le score d'echec du lecteur et masque le vrai probleme.

5. **L'axe 9 n'a pas de liste fermee.** On peut demontrer qu'un jeton EST une date; on ne peut pas demontrer qu'il n'est PAS un numero.

6. **La degradation de lecture n'est pas bornee.** Toute tolerance ajoutee echange des faux negatifs contre des faux positifs, et ce troc doit etre mesure avant d'etre livre, pas suppose favorable.

7. **Aucun etalon etabli a la main n'existe pour ce corpus.** Les vraies dates n'ont jamais ete relevees independamment avant traitement. Tout ce qui est ecrit ici est une propriete de FORME du texte, verifiable en relisant les exemples cites. **Rien ici n'est une mesure de justesse.** Un taux de bonne lecture ne pourra etre annonce qu'apres constitution d'un etalon manuel, sur le modele de `docs/etalon_corpus_tests_ux.md`.

8. **Deux cabinets seulement**, et l'un ecrase l'autre en volume (858 contre 22). Le second corpus a servi a REFUTER, pas a mesurer une frequence. Aucun pourcentage du premier ne doit etre presente comme une propriete du metier.

---

## 8. LES CONSTATS REFUTES: ce qu'il ne faut PAS croire

**Refute - "133 documents dates sur 858, soit 16%".** Ne se reproduit pas. Le lecteur rend 140 dates lues dans le texte, 47 lues dans le nom du fichier, 671 absences (`s2.py`). Et le denominateur pertinent est 709, pas 858, puisque 149 documents n'ont aucun texte.

**Refute - "857 documents".** Le corpus en compte 858: 858 fichiers texte, 858 lignes de registre, aucun orphelin (`s1.py`). Trois passages independants le confirment. L'ecart est sans consequence, mais un denominateur cite doit etre celui d'un comptage reel.

**Refute - "l'annee sur deux chiffres est la DEUXIEME forme du corpus".** Elle est la **quatrieme**. Classement mesure en nombre de documents: jour/mois/annee sur quatre chiffres **659**, mois en lettres + annee **396**, jour + mois en lettres + annee **376**, annee sur deux chiffres **275**, annee-mois-jour **78** (`s1.py`, et le comptage borne de la contre-mesure).

**Refute - "le separateur point est une difference de cabinet".** Il sert a citer un texte de droit chez LES DEUX cabinets: 13 documents au total portent une date a points a l'interieur d'une citation (`decret du 14.03.2005`, `loi du 10.07.1965`). L'usage partage est l'invariant. Et opposer 4% a 41% compare deux compositions de corpus - 858 documents melanges contre 22 documents choisis - pas deux cabinets.

**Refute - l'idee qu'ajouter des formes ameliore la lecture.** C'est le resultat le plus important de toute la campagne. Une contre-mesure a etendu le vrai lecteur avec la forme a points, en gardant sa regle "premiere correspondance": **41 reponses changent, dont 10 deviennent une citation juridique**. Trois proces-verbaux d'assemblee et trois convocations se retrouvent dates au 14 mars 2005 (le decret comptable), deux pieces du second cabinet au 10 juillet 1965 (la loi). **Deux de ces cas remplacent une date deja correcte par une date fausse.** Aucun test ne tombe. Comme `_ag_id` construit l'identifiant d'assemblee a partir de la date, ces proces-verbaux se rangeraient sous une assemblee `AG-2005-03-14` qui n'est l'assemblee de personne - c'est exactement le defaut que ce module a ete ecrit pour tuer, avec un autre faux nom.

**Conclusion operationnelle:** tant que l'axe 9 - le role du jeton - n'est pas traite, **toute forme ajoutee elargit la surface sur laquelle on se trompe en silence**. L'ordre des travaux n'est donc pas "reconnaitre plus de formes puis choisir mieux". C'est: d'abord le filtre de role et la regle de choix, avec leurs compteurs publies; les formes ensuite, une par une, chacune mesuree sur ce qu'elle change de bon ET de mauvais.

**A conserver malgre tout:** la meme contre-mesure montre que sur ces 41 changements, 31 vont dans le bon sens - 24 factures sans aucune date en gagnent une plausible, 9 voient un faux positif remplace par la vraie date. La forme a points merite d'etre reconnue. Ce qu'elle ne peut pas etre, c'est reconnue par un lecteur qui rend la premiere correspondance.

**Corrige, sans etre refute - "un document pese 72 Mo sur 78 et represente 91% des occurrences".** Le poids est exact (72,2 Mo sur 79,2 Mo, soit 91% des octets; c'est un export open-data de registre professionnel, sans rapport avec la copropriete). Mais le "91% des occurrences" accole un numerateur "horodatages" a un denominateur "annees"; recalcule a mesure constante, c'est 92,8%. La conclusion tient, l'arithmetique etait fausse. Surtout, ce biais est **inerte** pour ce qui nous occupe: en nombre de documents, retirer ce fichier deplace chaque forme d'exactement un document et ne change aucun classement. Le biais qu'il fallait declarer en premier n'est pas celui-la, c'est les 149 documents sans texte.
