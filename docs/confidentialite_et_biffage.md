# Confidentialite et biffage

Cette page documente les briques recentes `PrivacyOps` et `BiffageOps`. Elles sont importantes parce que CoproScope ne peut pas seulement produire de bonnes analyses : il doit aussi aider a savoir ce qui peut etre vu, partage, biffe ou garde strictement local.

## Idee centrale

Une copropriete manipule des documents tres heterogenes :

- documents communicables aux coproprietaires ;
- pieces utiles au conseil syndical ;
- factures et devis parfois diffusables apres retraitement ;
- releves bancaires, impayes, contentieux, donnees personnelles ou secrets a proteger.

CoproScope doit donc distinguer :

1. le document brut ;
2. la version de travail locale ;
3. la version biffee ou agregee ;
4. la sortie diffusable.

## PrivacyOps

`PrivacyOps` scanne les documents deja presents dans une instance et enrichit le registre documentaire avec une politique d'acces.

Sorties principales :

- registre de screening confidentialite ;
- rapport de screening ;
- champs de politique dans le registre documents ;
- college d'acces maximum brut ;
- college d'acces maximum derive ;
- transformations requises ;
- statut de revue humaine.

La revue humaine utilise cinq statuts :

| Statut | Sens |
|---|---|
| `DIFFUSABLE_BRUT` | Le document peut etre partage tel quel, avec justification tracee si la diffusion est large. |
| `DIFFUSABLE_APRES_BIFFAGE` | Une version biffee doit etre produite ou verifiee avant diffusion. |
| `DIFFUSABLE_APRES_AGREGATION` | Seule une synthese agregee ou suffisamment transformee doit sortir. |
| `BLOQUE` | La sortie est bloquee tant que le document reste dans cet etat ou ce chemin. |
| `A_ARBITRER` | Le CS doit decider explicitement avant toute diffusion. |

Pour toute decision de diffusion vers un college large (`C0`, `C1` ou `C2`), CoproScope demande une justification. Une decision `DIFFUSABLE_BRUT` est refusee si PrivacyOps a detecte qu'un biffage, une aggregation ou une sortie `metadata_only` est requise.

Commande :

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli privacy screen-existing --instance-root .\examples\synthetic_copro
```

Alias francais :

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli confidentialite scanner-existant --instance-root .\examples\synthetic_copro
```

## BiffageOps

`BiffageOps` construit une file de biffage puis produit, quand c'est possible localement, des versions biffees ou pseudonymisees.

Il ne modifie pas les originaux.

Sorties principales :

- file de biffage ;
- registre des biffages ;
- chemin de document biffe ;
- hash de document biffe ;
- table de correspondance en cas de pseudonymisation tracee.

Commandes :

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli privacy redaction-queue --instance-root .\examples\synthetic_copro
.\server\.venv\Scripts\python.exe -m coproscope.cli privacy redact --instance-root .\examples\synthetic_copro --doc-id DOC-EXEMPLE
.\server\.venv\Scripts\python.exe -m coproscope.cli privacy redact-required --instance-root .\examples\synthetic_copro --limit 10
```

Alias francais :

```powershell
.\server\.venv\Scripts\python.exe -m coproscope.cli confidentialite file-biffage --instance-root .\examples\synthetic_copro
.\server\.venv\Scripts\python.exe -m coproscope.cli confidentialite biffer --instance-root .\examples\synthetic_copro --doc-id DOC-EXEMPLE
.\server\.venv\Scripts\python.exe -m coproscope.cli confidentialite biffer-requis --instance-root .\examples\synthetic_copro --limit 10
```

## Colleges d'acces

La configuration par defaut introduit des colleges indicatifs, par exemple :

| College | Idee |
|---|---|
| `C1_Occupants_Usagers` | Informations utiles aux occupants/usagers. |
| `C2_Coproprietaires` | Pieces communicables ou utiles aux coproprietaires. |
| `C4_Conseil_Syndical` | Travail du conseil syndical. |
| `C8_Restreint_Critique` | Pieces sensibles : contentieux, impayes, banque, donnees critiques. |

Ces colleges ne remplacent pas une validation juridique. Ils aident a rendre visible le risque avant diffusion.

## Dans le pipeline

Le pipeline v1 integre maintenant :

1. inventaire ;
2. extraction texte ;
3. classement ;
4. screening confidentialite ;
5. file de biffage ;
6. completude documentaire ;
7. KPI ;
8. analyse AG ;
9. synthese de diligence.

Cette place est volontaire : on ne doit pas produire de sorties diffusables sans savoir si les documents sources portent des risques de confidentialite.

## Ce qui existe

| Fonction | Etat |
|---|---|
| Regles de confidentialite par defaut | Existe. |
| Screening local de documents existants | Existe. |
| Enrichissement du registre documents | Existe. |
| Rapport de screening | Existe. |
| File de revue humaine | Existe. |
| File de biffage | Existe. |
| Biffage texte/PDF/DOCX selon dependances disponibles | Existe comme socle. |
| Table de correspondance pour pseudonymisation tracee | Existe. |

## Ce qui reste a consolider

| Fonction | Etat |
|---|---|
| Interface de revue confidentialite | Premiere version. |
| Validation humaine guidee avant diffusion | Socle present, commandes dediees a ajouter. |
| Tests visuels de biffage PDF complexes | A renforcer. |
| Politique fine par copropriete | A documenter et tester. |
| Exports CommsOps bases sur versions biffees | A construire. |

## Regle produit

Aucune sortie diffusable ne devrait etre consideree comme sure simplement parce qu'elle est bien ecrite.

Elle doit aussi etre reliee a :

- une source ;
- une politique d'acces ;
- un statut de biffage, d'agregation ou de blocage ;
- une trace de validation.
