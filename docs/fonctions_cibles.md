# Fonctions cibles

Cette page distingue clairement ce qui existe, ce qui est en cours, ce qui est cible, et ce qui n'est pas prioritaire.

## Vue d'ensemble

| Bloc | But | Entrees typiques | Sorties attendues | Etat |
|---|---|---|---|---|
| DocOps | Reconstituer un registre documentaire fiable | bruts Drive, extranet, dossiers locaux | inventaire, hash, texte, classement, completude | deja exploitable |
| PrivacyOps | Qualifier le risque de diffusion | registre documents, chemins, texte extrait | screening confidentialite, colleges d'acces, transformations | nouveau socle |
| BiffageOps | Produire des versions biffees ou pseudonymisees | documents a transformer, signaux sensibles | file de biffage, registre biffages, versions biffees | nouveau socle |
| SyndicOps | Structurer la relation documentaire avec le syndic | demandes, reponses, pieces attendues | registre demandes, relances, preuves, diligences | embryon utile |
| FactureOps | Extraire et qualifier les factures | pieces detectees, texte, OCR, sources structurees | factures candidates, anomalies facture, intensite L0-L4 | amorce v1 |
| ComptaScope | Controler et expliquer les flux comptables | factures, annexes, etats de depenses, contrats | rapprochements, controles, rapport, exports | amorce v1 forte |
| AGOps | Aider la preparation et le suivi AG | convocations, PV, annexes, resolutions | registre AG, points d'attention | premiere version |
| Audit360 | Transformer signaux en controles actionnables | pieces, demandes, AG, compta, travaux | constats, risques, preuves attendues, actions | couche transverse |
| GristOps | Donner des tables locales de pilotage | registres CSV, sorties metier | exports locaux consultables | socle local |
| EvidenceOps | Produire des rapports reproductibles | CSV/DuckDB, Markdown, SQL | pages de rapport locales | socle local |
| ContractOps | Suivre contrats et obligations | contrats, avenants, attestations | registre contrats, alertes, clauses clefs | cible |
| WorksOps | Suivre devis, travaux, reception | devis, assurances, decisions, factures | comparatifs, chronologies, garanties | cible prioritaire |
| IncidentOps | Suivre incidents et sinistres | signalements, photos, assurances | tickets, statuts, preuves de cloture | cible prioritaire |
| CommsOps | Produire des sorties diffusables | notes, rapports, versions biffees | syntheses, PDF, messages propres | cible prioritaire |
| Interface locale | Rendre le produit accessible | registres et rapports stabilises | cockpit CS, vues metier | pas encore |

## Ce qui existe deja

### DocOps

DocOps est le socle. Il sert a savoir ce que l'on a, ce qui manque et ce qui peut etre cite comme preuve.

Fonctions deja presentes ou amorcees :

- inventaire des pieces brutes ;
- empreintes SHA-256 ;
- extraction de texte natif ;
- classement assiste ;
- rapport de completude ;
- KPI documentaires ;
- integration de champs confidentialite dans le registre documents.

### PrivacyOps et BiffageOps

Ces deux briques rendent la promesse local-first plus credible.

Fonctions presentes :

- screening des documents existants ;
- detection de signaux sensibles ;
- college d'acces brut et derive ;
- transformations requises ;
- file de biffage ;
- biffage local de textes/PDF/DOCX selon dependances ;
- registre des biffages ;
- table de correspondance pour pseudonymisation tracee.

Voir : [Confidentialite et biffage](./confidentialite_et_biffage.md).

### FactureOps

FactureOps transforme des pieces documentaires en factures candidates.

Fonctions presentes :

- detection de factures ;
- extraction fournisseur, numero, date, montants ;
- anomalies de piece ;
- intensite d'outil `L0` a `L4` ;
- separation entre anomalie facture et controle comptable.

### ComptaScope

ComptaScope ne remplace pas la comptabilite officielle. Il produit une lecture candidate, controlee et explicable.

Fonctions presentes :

- ecritures candidates ;
- rapprochements facture / etat des depenses ;
- statuts `OK`, `P2`, `P1` ;
- alias fournisseurs ;
- similarites, divisions, sommes multi-lignes, regroupements ;
- rapport explicatif local ;
- exports DuckDB/Grist/Evidence.

### AGOps

AGOps aide a preparer les assemblees generales.

Fonctions presentes :

- reperage des convocations, PV, annexes ;
- registre AG ;
- resolutions detectees ;
- points d'attention.

## Ce qui existe mais doit devenir plus utilisable

| Bloc | Probleme UX actuel | Direction |
|---|---|---|
| DocOps | Produit des registres, mais pas encore une vue CS simple. | Vue documents attendus/manquants/obsoletes. |
| PrivacyOps | Puissant mais technique. | Vue "peut-on diffuser ?" avec preuves et actions. |
| SyndicOps | Socle present, workflow incomplet. | Statuts, echeances, relances, preuves, modeles. |
| ComptaScope | Tres utile mais expert. | Controle comptes guide, questions au syndic, rapport AG. |
| AGOps | Prepare l'AG, suit peu l'apres-AG. | Registre decisions-actions-preuves. |
| Audit360 | Concept fort, encore abstrait. | Tableaux faits/preuves/risques/actions par parcours. |

## Ce qui n'existe pas encore

| Bloc | Pourquoi c'est important |
|---|---|
| Registre decision -> action -> preuve | Transformer les PV d'AG en travail suivi. |
| WorksOps | Gros besoin sur travaux, devis, reception, garanties. |
| IncidentOps | Les sinistres et incidents sont des douleurs quotidiennes. |
| ContractOps | Les contrats structurent charges, obligations et mises en concurrence. |
| CommsOps | Le CS doit produire des syntheses claires sans fuite de donnees. |
| Passation CS | La memoire du conseil syndical est fragile. |
| Interface locale | Le produit doit devenir utilisable sans lire des CSV. |

## Hors perimetre court terme

- SaaS multi-tenant.
- Application mobile native complete.
- Vote electronique complet.
- Reseau social de coproprietaires.
- Chatbot IA autonome sans sources.
- Remplacement de la comptabilite officielle ou du syndic.

## Regle de priorisation

L'ordre de construction recommande :

1. stabiliser les registres et preuves ;
2. rendre les modules existants visibles dans un cockpit ;
3. construire les chaines manquantes : decisions, travaux, incidents, passation ;
4. produire des sorties diffusables biffees ou agregees ;
5. seulement ensuite, enrichir l'interface et les automatisations.

