# Veille risques copro - malfacons, fraudes suspectees et erreurs

Date: 2026-05-27.
Rattachement: `RM-2026-0043` / `ORD-P1-042`.
Chantier: `CH-20260527-233650-RM-2026-0043-veille-risques-copro`.
Diffusion: CS seulement, a verifier avant partage.

## Synthese

Cette veille ne donne pas un avis juridique, comptable ou assurantiel. Elle
classe des risques recurrents en copropriete pour aider CoproScope a transformer
un signal faible en point a verifier, preuve attendue et action humaine.

Les risques les plus actionnables pour CoproScope sont:

- travaux et malfacons: reception floue, reserves non suivies, garanties mal
  identifiees, assurance dommages-ouvrage ou decennale absente du dossier;
- gouvernance: ordre du jour incomplet, pieces d'AG manquantes, votes ou delais
  mal controles, decisions executees sans trace lisible;
- comptes et charges: appels de fonds difficiles a relier au budget vote, aux
  cles, aux factures, a la banque et au fonds travaux;
- impayes et tresorerie: dette qui grossit, relances non tracees, risque de
  report sur les coproprietaires a jour;
- syndic et contrats: obligations non prouvees, mise en concurrence peu lisible,
  contrat ou prestation difficilement comparable;
- sinistres et incidents: origine commune/privative incertaine, declaration
  tardive, expertises et relances dispersees;
- preuves: photos, mails, factures et constats utiles mais non rattaches a un
  fait, une date, une decision ou une action.

La reponse produit recommandee est toujours la meme chaine:

```text
fait constate -> preuve attendue -> regle/process a verifier -> action humaine
```

## Methode

L'equipe a croise cinq angles en lecture seule:

- sources juridiques et administratives publiques;
- jurisprudence et analyses juridiques publiques;
- politiques publiques sur coproprietes fragiles ou degradees;
- signaux d'usage et forums publics, traites uniquement comme signaux faibles
  anonymises et non representatifs;
- mapping produit CoproScope: Audit360, ComptaScope, WorksOps, SyndicOps,
  DecisionOps, ContractOps, IncidentOps, PrivacyOps et CommsOps.

Aucune donnee d'instance ni piece nominative ou brute n'a ete utilisee; la
veille repose sur des sources publiques.

## Sources principales

Sources consultees le 2026-05-27:

- Service-Public, charges de copropriete:
  https://www.service-public.fr/particuliers/vosdroits/F2590
- Service-Public, assemblee generale:
  https://www.service-public.fr/particuliers/vosdroits/N31341
- Service-Public, convocation AG:
  https://www.service-public.fr/particuliers/vosdroits/F2615
- Service-Public, contestation d'une decision d'AG:
  https://www.service-public.fr/particuliers/vosdroits/F35288
- Service-Public, syndic de copropriete:
  https://www.service-public.fr/particuliers/vosdroits/F2608
- Service-Public, plan pluriannuel de travaux:
  https://www.service-public.fr/particuliers/vosdroits/F36760
- Service-Public, garanties apres reception des travaux:
  https://www.service-public.fr/particuliers/vosdroits/F2958
- Legifrance, Code civil article 1792:
  https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006443502
- Legifrance, Code civil article 1792-6:
  https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006443552
- Legifrance, loi du 10 juillet 1965, article 18:
  https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049398867
- Legifrance, loi du 10 juillet 1965, article 14-2:
  https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000043977289
- ANIL, travaux en copropriete:
  https://www.anil.org/votre-besoin/gerer-un-bien/copropriete/travaux-de-la-prise-de-decision-a-la-realisation/
- ANIL, charges:
  https://www.anil.org/votre-besoin/gerer-un-bien/copropriete/charges/
- Ministere charge du logement, aide aux coproprietes fragiles ou degradees:
  https://www.ecologie.gouv.fr/politiques-publiques/aide-aux-coproprietes-fragiles-degradees
- Anah, coproprietes fragiles:
  https://www.anah.gouv.fr/actualites/coproprietes-fragiles-anticiper-pour-agir-efficacement
- Anah, plan Initiative Coproprietes:
  https://www.anah.gouv.fr/action/plans-nationaux/plan-initiative-coproprietes
- Service-Public, mandataire ad hoc:
  https://www.service-public.fr/particuliers/vosdroits/F20388
- Service-Public, conseil syndical:
  https://www.service-public.fr/particuliers/vosdroits/F2610
- Data.gouv, registre national d'immatriculation des coproprietes:
  https://www.data.gouv.fr/datasets/registre-national-dimmatriculation-des-coproprietes
- Insee, logements en copropriete:
  https://www.insee.fr/fr/statistiques/fichier/2586040/LOGFRA17h3_F3.3.pdf
- DGCCRF, syndic de copropriete:
  https://www.economie.gouv.fr/dgccrf/les-fiches-pratiques-et-les-faq/le-syndic-de-copropriete-son-role-et-ses-obligations

## Constats

### 1. Travaux et malfacons

Constat: les difficultes naissent souvent avant le contentieux. Le dossier ne
permet pas toujours de savoir ce qui a ete vote, quel devis a ete retenu, qui a
suivi le chantier, si la reception existe, quelles reserves ont ete notifiees
et quelles garanties sont mobilisables.

Preuves attendues: resolution AG, devis, ordre de service, attestation
d'assurance, comptes rendus chantier, photos datees, PV de reception, reserves,
notifications ecrites, factures et preuve de levee des reserves.

Regle/process a verifier: la reception declenche les garanties; les reserves
doivent etre rattachees a une date et a une entreprise. Les desordres doivent
etre distingues: finition, non-conformite, dommage de bon fonctionnement,
dommage rendant l'ouvrage impropre ou atteignant la solidite.

Action CoproScope: `WorksOps` doit produire une fiche par desordre, avec
statut `a constater`, `reserve`, `a notifier`, `expertise demandee`,
`reparation suivie` ou `preuve de levee attendue`.

### 2. Assemblee generale et decisions

Constat: un risque frequent est la perte de chaine entre convocation, pieces,
vote, PV, delai de contestation et execution. Un coproprietaire novice voit
souvent seulement le resultat, pas la base de decision.

Preuves attendues: ordre du jour, convocation, annexes, pouvoirs, feuille de
presence, resultat des votes, PV notifie, delai de contestation, action
d'execution, devis et appels de fonds lies.

Regle/process a verifier: l'AG est le point de decision collectif. La
convocation, les pieces jointes, la majorite applicable, la notification du PV
et le delai de contestation doivent rester lisibles.

Action CoproScope: `DecisionOps` doit relier chaque decision a ses pieces, a sa
preuve d'execution et a sa diffusion prudente. Une decision sans preuve
attendue reste incomplete.

### 3. Charges, comptes et impayes

Constat: les charges deviennent contestables ou incomprises quand les appels de
fonds ne sont pas relies au budget vote, aux cles, aux factures, aux contrats,
aux comptes bancaires et aux travaux.

Les signaux structurels sont a surveiller tot: hausse du solde debiteur,
fournisseurs payes en retard, rejet des comptes, appels exceptionnels, ou
travaux votes mais non lances faute de tresorerie. Les sources publiques
identifient les impayes et la gouvernance comme marqueurs de fragilite; les
seuils de mandataire ad hoc doivent etre verifies au dossier avant toute
qualification.

Preuves attendues: budget, annexes comptables, grand livre, appels de fonds,
factures, contrats, releves bancaires, cle de repartition, etat des impayes,
fonds travaux.

Regle/process a verifier: les charges financent administration, conservation,
entretien ou services/equipements; le recouvrement des impayes est pilote par le
syndic et doit etre trace sans exposer inutilement les identites.

Action CoproScope: `ComptaScope` doit afficher le chemin `appel -> budget vote
-> cle -> facture/contrat -> banque -> ecart`. Les impayes doivent etre
agreges et actionnables, avec identites masquees par defaut.

### 4. Syndic, contrats et mise en concurrence

Constat: beaucoup de tensions viennent d'un flou sur ce que le syndic devait
faire, ce qui a ete fait, ce qui attend une decision d'AG et ce qui releve d'un
prestataire.

Le conseil syndical est un point de controle central: acces aux pieces,
verification de la comptabilite, suivi des contrats, preparation des questions
au syndic et detection des documents manquants. CoproScope doit donc tracer les
demandes CS -> syndic sans transformer le CS en organe d'envoi automatique ou
en autorite juridique.

Preuves attendues: contrat de syndic, fiche de prestations, seuil de mise en
concurrence, devis concurrents, contrat prestataire, PV d'AG, relances,
justificatifs extranet.

Regle/process a verifier: le syndic administre et execute les decisions; il
doit gerer les documents, les comptes, les travaux urgents selon le cadre
applicable et les actions en recouvrement. La comparaison de contrats suppose
un perimetre et des exclusions lisibles.

Action CoproScope: `ContractOps` et `SyndicOps` doivent transformer les
obligations en echeances, pieces attendues et demandes humaines; aucun bouton
ne doit promettre un envoi automatique sans validation.

### 5. Coproprietes fragiles ou degradees

Constat: les sources publiques decrivent des fragilites cumulatives: impayes,
batiment vieillissant, difficultes de gouvernance, travaux lourds, reste a
charge, conflits, manque de suivi documentaire et capacite limitee a voter puis
financer les travaux.

Les donnees RNIC et les observatoires publics servent au reperage, pas a une
conclusion automatique. Une copropriete peut cumuler des signaux faibles sans
etre juridiquement qualifiee de degradee; inversement, un dossier local peut
etre critique meme si le signal public est incomplet ou non a jour.

Preuves attendues: taux ou montant d'impayes, travaux urgents ou programmes,
PPT/PPPT, diagnostics, procedures, aides sollicitees, echeancier, reste a
charge, decisions AG, pieces de securite.

Regle/process a verifier: le registre national des coproprietes et les
dispositifs publics servent au reperage et a l'accompagnement. CoproScope ne
doit pas diagnostiquer seul une copropriete degradee, mais peut structurer les
preuves et alertes.

Action CoproScope: `Audit360` doit produire un niveau de vigilance, pas un
verdict. Chaque alerte doit dire ce qui est constate, suppose ou a verifier.

### 6. Sinistres, incidents et preuve

Constat: les sinistres se bloquent quand l'origine est incertaine, que les
assureurs ne sont pas clairement identifies ou que les preuves sont dispersees.

Preuves attendues: declaration, constat, photos datees, recherche de fuite,
rapport expert, police d'assurance, courriers assureur, devis, facture,
attestation de reparation.

Regle/process a verifier: le dossier doit distinguer origine supposee, origine
constatee, partie commune/privative, assureur saisi et action humaine suivante.

Action CoproScope: `IncidentOps` doit tenir une chronologie probatoire: signal,
urgence, preuve, acteur saisi, prochaine relance, statut de cloture.

## Leviers produit

| Levier | Utilite | Garde-fou |
|---|---|---|
| `Audit360` | transformer un signal en point a verifier | pas de verdict juridique automatique |
| `WorksOps` | suivre malfacons, reserves, entreprises et preuves chantier | reception et garanties qualifiees prudemment |
| `ComptaScope` | rapprocher budget, appels, factures, banque et impayes | donnees nominatives masquees par defaut |
| `SyndicOps` | tracer demandes, relances et preuves de reponse | aucun envoi automatique |
| `DecisionOps` | relier AG/CS, decision, action et preuve | decision sans preuve attendue = incomplete |
| `ContractOps` | comparer contrats, obligations et echeances | pas d'interpretation juridique definitive |
| `IncidentOps` | suivre sinistres et incidents jusqu'a preuve | origine supposee distincte de l'origine constatee |
| `PrivacyOps` | verifier qui peut voir quoi avant diffusion | blocage si piece brute ou identite inutile |

## Priorisation proposee

1. `ORD-P0-061` - matrice formats/capabilities DocOps.
   Raison: les risques ci-dessus reposent sur des pieces heterogenes. Avant
   d'automatiser plus de tri ou de preuve, CoproScope doit dire clairement quel
   format est lu, converti en texte, structure, refuse ou envoye en revue
   humaine.
2. `ORD-P0-062` - taxonomie canonique.
   Raison: les familles documentaires doivent rester comprehensibles pour un
   membre CS novice: AG officielle, CS, syndic, compta, banque, contrats,
   travaux, incidents, communications, contentieux.
3. `ORD-P0-063` - preuve validee.
   Raison: beaucoup de risques viennent d'une piece candidate traitee comme une
   preuve. La validation humaine et la diffusion doivent etre explicites.

## Limites

- Cette veille ne remplace pas une consultation juridique, comptable,
  assurantielle ou technique.
- Les forums publics ne sont pas cites individuellement et ne prouvent pas une
  frequence statistique. Ils servent seulement a reperer des irritants et mots
  naturels.
- Les sources officielles donnent le cadre general; chaque copropriete depend
  de son reglement, de ses votes, de ses contrats, de ses pieces et de ses
  delais.
- Toute utilisation sur une instance reelle doit rester locale et privee tant
  que PrivacyOps n'a pas valide la diffusion.

## Verification finale

- Matrice CSV creee et enrichie: 37 scenarios importables au schema attendu.
- Validation locale: `Import-Csv` OK sur les colonnes `famille`, `scenario`,
  `sources`, `signaux`, `preuves_attendues`, `regle_process`,
  `module_coproscope`, `levier_prevention`, `validation_humaine`, `priorite`,
  `limites`.
- Verification documentaire: `git diff --check` OK sur le rapport, la matrice,
  le registre de presence et le gouvernail.
- Prochaine tache identifiee avant rendu: `ORD-P0-061` matrice
  formats/capabilities DocOps; alternative `ORD-P0-062` taxonomie canonique.

BOT-END - RM-2026-0043 / CONV-2026-1810 - rapport et matrice livres, sans code
produit ni donnee d'instance.
