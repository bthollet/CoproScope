# Etat du developpement

## Resume franc

CoproScope n'est plus une intention. Le depot contient un noyau logiciel local-first, une CLI, une instance synthetique, des modules documentaires et comptables, une premiere couche de confidentialite/biffage, des exports locaux et une documentation produit structuree.

Le chantier principal n'est plus "prouver que l'idee existe". Le chantier principal est maintenant de rendre ce noyau lisible et utilisable par un conseil syndical, pas seulement par un utilisateur technique.

## Ce qui est livre ou deja exploitable

- Depot public structure.
- Paquet `server/` avec CLI `coprocs`.
- Instance synthetique publique pour tests et demonstrations.
- Pipeline v1 : inventaire, extraction texte, classement, screening confidentialite, file de biffage, completude, KPI, AG, synthese de diligence.
- Serveur MCP minimal.
- Schemas, configs, prompts et templates versionnes.
- DocOps : inventaire, hash, extraction, classement, completude.
- PrivacyOps : screening confidentialite et politiques d'acces.
- BiffageOps : file de biffage et versions biffees/pseudonymisees lorsque possible.
- FactureOps v1 : factures candidates, anomalies facture, intensite `L0` a `L4`.
- ComptaScope v1 : ecritures candidates, controles, rapprochements explicables, `OK`/`P2`/`P1`, rapports et exports.
- AGOps : premiere lecture des convocations, PV, annexes, resolutions.
- Audit360 : gabarits generiques de constats, controles, preuves attendues, syntheses.
- GristOps / EvidenceOps : exports locaux et rapports reproductibles.
- Interface locale v0 : cockpit web, vues metier, actions et exports CSV/Markdown.
- Copro demo fictive : generation d'une instance publiable separee des donnees reelles.
- `share-audit` et `share-export` : frontiere public/prive.
- Documentation mise a jour avec etude utilisateurs, feuille de route et concepts UX.

## Ce qui est en cours ou a epaissir

| Sujet | Etat |
|---|---|
| DocOps | Bon socle ; doit devenir une vue utilisateur simple. |
| PrivacyOps / BiffageOps | Nouveau socle ; file de revue humaine et garde-fous presents, UX a epaissir. |
| SyndicOps | Embryon utile ; doit devenir workflow complet de demandes et relances. |
| ComptaScope | Amorce forte ; doit devenir lisible par non-comptables. |
| AGOps | Premiere version ; doit s'ouvrir au suivi post-AG. |
| Audit360 | Tres prometteur ; doit etre decline par parcours concrets. |
| Grist/Evidence | Utile pour experts ; doit etre mieux guide. |

## Ce qui n'existe pas encore

- Cockpit conseil syndical.
- Registre decision -> action -> preuve.
- WorksOps travaux/devis/reception.
- IncidentOps sinistres/signalements.
- ContractOps contrats/obligations.
- CommsOps syntheses diffusables.
- Dossier de passation conseil syndical.
- Experience "grand public" complete.

## Ce qui n'est pas prioritaire

- SaaS multi-tenant.
- Application mobile native complete.
- Vote electronique complet.
- Reseau social de coproprietaires.
- Chatbot IA autonome sans preuves citees.
- Jumeau numerique 3D.

## Niveau de maturite par bloc

| Bloc | Niveau actuel | Commentaire |
|---|---|---|
| Frontiere public / prive | Bon | Garde-fous presents, export public outille. |
| CLI | Bon socle | Surface large, encore a stabiliser autour des nouvelles commandes. |
| DocOps | Bon socle | Deja utile, encore trop technique pour un CS non expert. |
| PrivacyOps | Nouveau socle | Screening, regles et file de revue humaine presents ; parcours utilisateur a renforcer. |
| BiffageOps | Nouveau socle | File et biffage presents, tests et UX a renforcer. |
| SyndicOps | Embryon utile | Besoin fort, workflow a epaissir. |
| FactureOps | Amorce v1 | Extraction et anomalies separees de la compta. |
| ComptaScope | Amorce v1 forte | Tres differenciant, mais doit etre rendu pedagogique. |
| AGOps | Premiere version | A prolonger vers suivi des decisions. |
| Audit360 | Couche transverse | Forme generique claire, usages a instancier. |
| Interface locale | V0 locale | Cockpit web en lecture prioritaire ; a transformer en parcours de travail complet. |

## Prochaine phase logique

1. Stabiliser et integrer les livraisons de lots dans une branche propre.
2. Mettre ComptaScope en forme "controle comptes guide".
3. Transformer DocOps en vue pieces presentes/manquantes/obsoletes.
4. Construire le registre decision -> action -> preuve.
5. Ouvrir WorksOps et IncidentOps en mode minimal.
6. Faire converger les demandes vers SyndicOps.
7. Preparer CommsOps pour produire des syntheses biffees ou agregees.
