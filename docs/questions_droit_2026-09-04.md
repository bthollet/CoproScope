# Quatre questions de droit - reponses sourcees

Lot documentaire, `CONV-2026-2134`. Aucun code. Quatre questions posees par Brice
devant l'ecran, chacune confrontee au texte.

Toutes les sources ont ete lues sur Legifrance via PISTE le 2026-09-04, fonds
`LODA_DATE`, filtre de date pose au jour de la lecture. Aucune ne porte de date
de fin de vigueur. `VIGUEUR` signifie "en vigueur a la date demandee", jamais
"a jour": la date de version fait partie de la citation.

| Texte | Article | `LEGIARTI` | En vigueur depuis |
|---|---|---|---|
| Loi n. 65-557 du 10 juillet 1965 | 14-2-1 | `LEGIARTI000043967792` | 2023-01-01 |
| Loi n. 65-557 | 18 | `LEGIARTI000049398867` | 2024-04-11 |
| Loi n. 65-557 | 21 | `LEGIARTI000039313574` | 2020-06-01 |
| Loi n. 65-557 | 21-1 | `LEGIARTI000039301559` | 2020-06-01 |
| Loi n. 65-557 | 21-2 | `LEGIARTI000039301561` | 2020-06-01 |
| Loi n. 65-557 | 21-3 | `LEGIARTI000039301563` | 2020-06-01 |
| Loi n. 65-557 | 25 | `LEGIARTI000051749507` | 2025-06-18 |
| Loi n. 65-557 | 42 | `LEGIARTI000039329680` | 2020-06-01 |
| Loi n. 65-557 | 43 | `LEGIARTI000039313649` | 2020-06-01 |
| Decret n. 67-223 du 17 mars 1967 | 8 | `LEGIARTI000039345709` | 2020-01-01 |
| Decret n. 67-223 | 9 | `LEGIARTI000042078632` | 2020-07-04 |
| Decret n. 67-223 | 10 | `LEGIARTI000042078638` | 2020-07-04 |
| Decret n. 67-223 | 13 | `LEGIARTI000006488391` | 2004-09-01 |
| Decret n. 67-223 | 17 | `LEGIARTI000042078689` | 2020-07-04 |
| Decret n. 67-223 | 17-1 | `LEGIARTI000042076794` | 2020-07-04 |
| Decret n. 67-223 | 18 | `LEGIARTI000042078697` | 2020-07-04 |
| Decret n. 67-223 | 21 | `LEGIARTI000042078735` | 2020-07-04 |
| Decret n. 67-223 | 26 | `LEGIARTI000042078742` | 2020-07-04 |
| Decret n. 67-223 | 35 | `LEGIARTI000053191341` | 2025-12-25 |

Jurisprudence citee, texte integral lu:
Cass. 3e civ., 28 janvier 2015, n. 13-23.552, publie au Bulletin, cassation.

---

## Question 1 - Un seuil fixe par l'assemblee est-il seulement un montant ?

**Reponse. Cela depend du seuil, et la reponse est negative pour deux des
trois.** Pour la mise en concurrence et pour la consultation obligatoire du
conseil syndical, l'article 21 alinea 2 ne parle que d'un montant: l'assemblee,
a la majorite de l'article 25, "arrete un montant des marches et des contrats a
partir duquel" l'obligation joue - le texte ne prevoit ni n'interdit d'autres
conditions. Pour la delegation de pouvoirs, en revanche, le montant ne suffit
jamais: l'article 21 du decret impose que la delegation de l'article 25 a
"mentionne expressement l'acte ou la decision deleguee", l'article 21-1 de la
loi laisse l'assemblee deleguer "tout ou partie" des decisions de l'article 24 en
excluant trois matieres, et l'article 21-3 la borne a deux ans renouvelables par
decision expresse.

**Sources.** `LEGIARTI000039313574` (loi, art. 21 al. 2, les deux seuils),
`LEGIARTI000039301561` (loi, art. 21-2, montant maximum de la delegation),
`LEGIARTI000051749507` (loi, art. 25 a, "elle fixe le montant maximum des sommes
allouees a ce titre"), `LEGIARTI000039301559` et `LEGIARTI000039301563` (loi,
art. 21-1 et 21-3, perimetre et duree), `LEGIARTI000042078735` (decret, art. 21,
mention expresse de l'acte delegue), `LEGIARTI000039313649` (loi, art. 43,
clauses reputees non ecrites).

**Ce que le texte ne dit pas.** Il ne dit **rien** sur la faculte d'assortir les
deux seuils de l'article 21 de conditions par nature de depense, par
fournisseur, par periode ou par cumul. Ni autorisation, ni interdiction. Le
silence n'est pas une permission: une condition qui viderait l'obligation de sa
substance resterait contestable, et l'article 43 ne repute non ecrites que les
clauses contraires a la loi, ce qui vise le reglement de copropriete et non une
resolution. Aucune disposition ne fixe non plus de plancher ni de plafond au
montant lui-meme.

**Pratique constatee sur les deux cabinets, et elle tranche la question
produit.** Les resolutions de seuil ne se reduisent jamais a un nombre. Formes
relevees, aucune inventee: un seuil de mise en concurrence assorti de
`sauf pour les urgences`; une periodicite, `la mise en concurrence interviendra
tous les 3 ans`; une methode imposee, `sur la base d'un descriptif etabli par un
homme de l'art, obligeant a des reponses par prix unitaire pour chaque poste`;
une duree de validite du seuil, `pour une duree de 24 MOIS`; une modalite
d'execution, `il sera consulte systematiquement par le syndic`. Un ecran qui
n'afficherait que `1 000 EUR` perdrait les cinq.

**Ce que l'ecran doit en faire. Brice a raison, et c'est verifie des deux
cotes.** Le montant est un champ derive, jamais la donnee de reference. L'ecran
doit porter le **verbatim de la resolution** qui fixe le seuil, avec sa date
d'assemblee, son numero et l'article de majorite vise, et afficher le montant a
cote de ce verbatim et non a sa place. Trois champs structures s'ajoutent, parce
que le texte les impose pour la delegation et que la pratique les produit pour
les seuils: **perimetre** (les actes expressement mentionnes), **duree de
validite**, **conditions attachees**. Quand une condition est presente et non
modelisee, l'ecran doit le signaler plutot que de l'ignorer: un seuil affiche
sans sa reserve d'urgence est un seuil faux.

---

## Question 2 - Une depense de travaux doit-elle transiter par le fonds travaux ?

**Reponse. Non, ce n'est pas obligatoire: c'est une faculte de l'assemblee, et
elle est bornee.** L'article 14-2-1 I dispose que l'assemblee "**peut**, par un
vote a la meme majorite que celle applicable aux depenses concernees, affecter
tout ou partie des sommes deposees sur le fonds de travaux au financement des
depenses mentionnees aux 1. a 4." - le verbe est facultatif, la majorite est
celle de la depense elle-meme, et les emplois sont limitativement enumeres.
Le financement direct reste la voie ordinaire: l'article 35 du decret autorise
le syndic a appeler des provisions pour les depenses non comprises dans le budget
previsionnel, independamment du fonds.

**Sources.** `LEGIARTI000043967792` (loi, art. 14-2-1 I et III),
`LEGIARTI000053191341` (decret, art. 35, 3. provisions pour depenses hors budget
et 5. cotisations au fonds), `LEGIARTI000049398867` (loi, art. 18 II, compte
separe remunere dedie au fonds).

**Les quatre emplois autorises, et rien d'autre.** 1. elaboration du projet de
plan pluriannuel de travaux et, le cas echeant, du diagnostic technique global;
2. realisation des travaux prevus dans le plan pluriannuel **adopte par
l'assemblee**; 3. travaux decides par le syndic en cas d'urgence dans les
conditions du troisieme alinea du I de l'article 18; 4. travaux necessaires a la
sauvegarde de l'immeuble, a la preservation de la sante et de la securite des
occupants et a la realisation d'economies d'energie, non prevus dans le plan.
Une depense qui n'entre dans aucune des quatre ne peut pas etre payee par le
fonds, meme avec un vote.

**Trois conditions cumulatives** pour qu'une affectation soit reguliere: une
resolution d'affectation votee, prise **a la meme majorite que la depense
concernee** - une depense de l'article 25 exige une affectation de l'article 25 -
et une affectation qui "tient compte de l'existence de parties communes
speciales ou de clefs de repartition des charges".

**Ce que le texte ne dit pas.** Il ne dit pas dans quel ordre puiser quand
plusieurs sources sont disponibles, ni si une affectation peut etre votee apres
la depense, ni comment se traite un reliquat d'affectation superieur a la
depense reellement engagee. Il organise explicitement les virements **entrants**
vers le compte du fonds, "les virements en provenance du compte" ordinaire "sont
autorises", et reste muet sur le virement sortant, qui ne se deduit que de la
resolution d'affectation elle-meme.

**Ce que l'ecran doit en faire.** Ne **jamais** presenter le passage par le fonds
comme obligatoire ni comme un defaut quand il n'a pas eu lieu. Le controle utile
est un chainage a trois maillons, et il produit un constat seulement si un
maillon manque: **depense** -> **resolution d'affectation votee** -> **majorite
de l'affectation identique a celle de la depense**. Un quatrieme controle
verifie que la depense affectee entre bien dans l'un des quatre emplois: c'est
une qualification, donc un champ a valider par un humain, pas une deduction
automatique. Et l'ecran doit distinguer deux mouvements que le vocabulaire
courant confond: **affecter** (une decision d'assemblee, comptabilisee au compte
705) et **virer** (un mouvement bancaire depuis le compte separe remunere). Un
ecart entre les deux est exactement le genre de constat qui a deja servi sur ce
projet.

---

## Question 3 - La resolution faussement adoptee

**Reponse. Le texte ne qualifie pas la sanction, il organise l'action.** Aucune
disposition ne dit qu'une decision proclamee adoptee sans la majorite requise est
nulle, annulable ou reputee non prise; ce que la loi fixe, c'est une action en
contestation des decisions d'assemblee, ouverte aux seuls **coproprietaires
opposants ou defaillants**, dans un delai de **deux mois a compter de la
notification du proces-verbal**, "a peine de decheance" - le syndic devant
notifier dans le mois de l'assemblee. Il n'existe **aucun regime particulier a
l'insuffisance de majorite**: elle emprunte la voie de droit commun de l'article
42 alinea 2.

**Sources.** `LEGIARTI000039329680` (loi, art. 42 al. 2 - identifiant deja
verifie le 2026-09-03 par une autre voie, confirme ici),
`LEGIARTI000042078697` (decret, art. 18, point de depart du delai et contenu
obligatoire de la notification), `LEGIARTI000042078689` (decret, art. 17, le
proces-verbal comporte "sous l'intitule de chaque question inscrite a l'ordre du
jour, le resultat du vote" et les noms et nombre de voix des opposants, des
abstentionnistes et des defaillants), `LEGIARTI000042076794` (decret, art. 17-1).

**Deux verrous que le texte pose, et que l'ecran ne peut pas ignorer.**

1. **L'article 17-1 ne sauve pas ce cas.** Il dit qu'une irregularite formelle
   du proces-verbal ou de la feuille de presence relative aux conditions de vote
   ou a la computation des voix "n'entraine pas necessairement la nullite" -
   mais a deux conditions cumulatives: qu'on puisse reconstituer le sens du vote
   **et** que le resultat "n'en soit pas affecte". Une resolution proclamee
   adoptee sans la majorite est precisement le cas ou le resultat **est**
   affecte. L'article 17-1 est donc un argument contre la these du simple vice
   de forme, pas pour elle.
2. **Le delai de deux mois ne court pas d'une notification irreguliere.**
   L'article 18 du decret exige que la notification "mentionne les resultats du
   vote et reproduise le texte du deuxieme alinea de l'article 42". La Cour de
   cassation en tire que l'absence de reproduction de ce texte rend la
   notification irreguliere (Cass. 3e civ., 28 janvier 2015, n. 13-23.552,
   publie au Bulletin, cassation, texte integral lu). Un delai affiche comme
   expire sur la seule foi d'une date d'envoi peut donc etre faux.

**Ce que le texte ne dit pas.** Il ne qualifie pas la nature de la sanction, et
ne dit pas si le grief peut etre eleve au-dela des deux mois par voie
d'exception. Il ne dit pas non plus ce qu'il advient quand le proces-verbal ne
mentionne pas le decompte que l'article 17 impose: sans decompte publie,
l'insuffisance de majorite ne se lit pas sur la piece. **Ce point n'est pas
tranche ici et ne doit pas etre affirme dans un rapport.**

**Ce que l'ecran doit en faire.** Distinguer **trois etats**, jamais deux:
`REJETEE` (l'assemblee constate le rejet), `ADOPTEE` (proclamee adoptee et le
decompte le confirme), et un troisieme etat, `ADOPTEE_MAIS_DECOMPTE_INSUFFISANT`,
pour la resolution proclamee adoptee dont les voix publiees n'atteignent pas le
seuil de l'article vise. Un quatrieme etat est necessaire et il est different:
`DECOMPTE_ABSENT`, quand le proces-verbal ne publie pas les voix - c'est une
irregularite au regard de l'article 17, et c'est surtout l'aveu que le controle
ne peut pas etre conduit. Sur le delai, l'ecran ne doit **jamais** afficher
"delai expire" a partir d'une seule date: il lui faut la date de notification,
la mention des resultats du vote et la reproduction de l'article 42 alinea 2, et
il doit afficher `DELAI_NON_VERIFIABLE` tant que ces trois elements ne sont pas
etablis. Enfin, la qualite pour agir est un champ a part: seuls les opposants et
les defaillants peuvent contester, ce qui suppose de savoir comment chacun a
vote - donnee nominative, a manier sous la garde de confidentialite.

---

## Question 4 - La resolution demandee et jamais inscrite a l'ordre du jour

**Reponse. Le droit existe, il est clair, et l'omission est bien un manquement
du syndic.** L'article 10 du decret dispose qu'"a tout moment, un ou plusieurs
coproprietaires, ou le conseil syndical, peuvent notifier au syndic la ou les
questions dont ils demandent qu'elles soient inscrites a l'ordre du jour d'une
assemblee generale", et que "le syndic **porte** ces questions a l'ordre du jour
de la convocation de la prochaine assemblee generale" - l'indicatif vaut
obligation, sans condition de nombre de voix ni de quotite. La seule souplesse
accordee au syndic est temporelle: "si la ou les questions notifiees ne peuvent
etre inscrites a cette assemblee compte tenu de la date de reception de la
demande par le syndic, elles le sont a l'assemblee suivante".

**Sources.** `LEGIARTI000042078638` (decret, art. 10),
`LEGIARTI000042078632` (decret, art. 9, affichage prealable),
`LEGIARTI000006488391` (decret, art. 13, effet de la non-inscription),
`LEGIARTI000039345709` (decret, art. 8, voie de la convocation de droit),
`LEGIARTI000042078742` (decret, art. 26, l'ordre du jour est etabli en
concertation avec le conseil syndical).

**Conditions de forme et de delai.** Une **notification**, au sens du decret, et
non un simple echange oral. Aucun quorum de demandeurs: un seul coproprietaire
suffit. Aucune date butoir chiffree: le seul critere est la **date de reception
par le syndic**, appreciee au regard de la faisabilite de l'inscription. Une
piece jointe est exigee dans un cas: quand la question releve des 7. et 8. du I
de l'article 11, le demandeur doit notifier **le projet de resolution** avec sa
demande - une demande sans projet de resolution, dans ces matieres, est
incomplete, et c'est la premiere chose a verifier avant de qualifier un
manquement.

**Ce que le texte ne dit pas, et c'est la limite du grief.** Aucune sanction
n'est attachee a la non-inscription. Le decret est meme explicite en sens
inverse sur une formalite voisine: l'affichage par lequel le syndic informe les
coproprietaires de la possibilite de demander une inscription est prescrit
"**sans que cette formalite soit prescrite a peine de nullite de l'assemblee
generale**". Rien ne permet donc d'affirmer que l'omission annule l'assemblee.
Ce que le texte donne, c'est autre chose: l'article 13 prive l'assemblee de tout
pouvoir de decision sur une question non inscrite - "l'assemblee generale ne
prend de decision valide que sur les questions inscrites a l'ordre du jour",
elle peut seulement les examiner "sans effet decisoire". L'omission ne vicie pas
l'assemblee: elle empeche la decision demandee.

**Le recours existe et il ne passe pas par la contestation.** L'article 8 ouvre
une convocation **de droit** a la demande du conseil syndical, ou d'un ou
plusieurs coproprietaires representant au moins un quart des voix - moins si le
reglement le prevoit. Passe une mise en demeure au syndic restee infructueuse
plus de huit jours, le president du conseil syndical convoque lui-meme; a defaut
de conseil syndical ou de president, tout coproprietaire peut provoquer la
convocation. La voie utile est donc de reconvoquer, pas d'attaquer.

**Ce que l'ecran doit en faire.** C'est bien une non-conformite d'une autre
nature qu'une preuve manquante, et elle doit avoir son propre etat:
`DEMANDE_NON_INSCRITE`, distinct de `PIECE_ABSENTE`. Il lui faut quatre champs,
et le grief ne se soutient que si les quatre sont renseignes: **date de
notification au syndic**, **mode de notification** (une notification au sens du
decret, pas un courriel ordinaire), **texte de la question demandee** en
verbatim, et **projet de resolution joint** quand la matiere l'exige. L'ecran
calcule alors une seule chose: la ou les assemblees convoquees **apres** cette
date, et si la question y figure. Deux garde-fous obligatoires dans le rendu.
D'abord, la premiere assemblee suivante peut legitimement ne pas porter la
question si la demande est arrivee trop tard: le constat n'est solide qu'a
partir de la **deuxieme**. Ensuite, l'ecran ne doit jamais presenter l'omission
comme une cause de nullite de l'assemblee - il doit dire ce que le texte dit:
la decision demandee n'a pas pu etre prise, et la voie ouverte est la convocation
de droit de l'article 8.

---

## Ce qui reste ouvert

Trois points n'ont pas de reponse textuelle nette et ne doivent pas etre tranches
par un ecran ni affirmes dans un rapport:

- la faculte d'assortir de conditions les deux seuils de l'article 21
  (question 1): le texte est muet, la pratique des deux cabinets le fait;
- la qualification exacte de la sanction d'une majorite insuffisante - nullite,
  annulabilite, decision non prise (question 3): la loi organise l'action, pas
  la qualification;
- le sort d'une resolution dont le proces-verbal ne publie pas le decompte des
  voix que l'article 17 impose (question 3): sans decompte, le controle n'est pas
  conduit, et c'est tout ce que l'outil peut dire.

## Confidentialite

Aucun nom, aucun montant nominatif, aucun chemin local. Les cabinets sont
designes par alias. Les formulations de resolution citees a la question 1 sont
des clauses de portee collective, sans donnee personnelle. Les deux instances
sont restees en lecture seule.


## Verification a la source du 2026-09-08 - article 21, alinea 2

Lecture PISTE/Legifrance faite le 2026-09-08 sur le fonds `LODA_DATE`, texte
`LEGITEXT000006068256` (loi n° 65-557 du 10 juillet 1965), article 21, version
en vigueur au **2026-09-08**, identifiant **`LEGIARTI000039313574`**.

**Deux affirmations sont tranchees, et les deux dans le sens contraire de ce
qui etait attendu.**

### 1. Le constat C081 est REFUTE

L'audit du 2026-09-05 affirmait que l'alinea cite par le code etait faux dans
toutes ses occurrences, renvoi affiche a l'utilisateur compris. **Il ne l'est
pas.** L'alinea 2 de l'article 21 porte mot pour mot les deux seuils que le
produit modelise:

> « L'assemblee generale des coproprietaires, statuant a la majorite de
> l'article 25, arrete un montant des marches et des contrats a partir duquel
> la consultation du conseil syndical est rendue obligatoire. A la meme
> majorite, elle arrete un montant des marches et des contrats autres que celui
> de syndic a partir duquel une mise en concurrence est rendue obligatoire. »

`art. 21 al. 2` est la bonne citation, et `LEGIARTI000039313574` est bien
l'article 21 en vigueur. La note du depot avait raison contre l'audit.

**Ce que cela apprend sur la campagne d'audit:** un constat peut etre formule
avec precision - 36 occurrences comptees, le fichier nomme, le renvoi ecran
identifie - et etre faux sur le fond parce que personne n'a ouvert la source.
La precision du constat n'est pas la preuve de sa justesse.

### 2. L'intuition « l'avis du conseil syndical est facultatif pour les travaux »
est REFUTEE, avec deux nuances qui comptent

Question posee par Brice le 2026-09-07: « l'avis du conseil syndical, il est
facultatif pour les travaux, meme si on est au-dessus du seuil ». Le texte dit
l'inverse: au-dessus du montant arrete, « la consultation du conseil syndical
est **rendue obligatoire** », et l'article ne distingue pas les travaux des
autres marches et contrats.

Deux nuances, toutes deux dans le texte lu:

- **L'obligation n'existe que si l'assemblee a effectivement arrete un
  montant.** Sans deliberation fixant ce seuil, il n'y a pas d'obligation de
  consultation a faire respecter. Le produit doit donc distinguer « seuil non
  vote » de « seuil vote et non respecte » - ce sont deux constats differents.
- **C'est une consultation, pas un avis conforme.** Le conseil syndical doit
  etre consulte; son avis ne lie pas l'assemblee. Un ecran qui presenterait
  l'absence d'avis comme une irregularite de la decision elle-meme irait plus
  loin que le texte.

### Ce que cette verification ne couvre PAS

J'ai lu l'article 21. Une exemption propre aux travaux devrait venir d'un autre
texte - article 25, decret 67-223, ou une jurisprudence - et je ne les ai pas
depouilles. L'affirmation ci-dessus vaut donc contre l'article 21 seul, et non
contre l'ensemble du droit applicable. Cette skill verifie des sources, elle ne
donne pas de conseil juridique: l'interpretation d'un dossier releve d'un
avocat.
