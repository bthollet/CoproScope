# Equipe agile - Communication officielle LRAR et boite mail

Date de lancement: 2026-05-24 22:10 +02:00.
Roadmap: `RM-2026-0028`.
Chantier: `CH-20260524-221000-RM-2026-0028-communication-officielle-cadrage`.
Conversations: `CONV-2026-1612` a `CONV-2026-1616`.
Mode: cadrage agile sans dev, sans connecteur, sans secret.
Statut: pret a integrer.

## BOT-START

BOT-START - Coordinateur-scribe communication officielle - 2026-05-24
22:10 +02:00.

Mission: qualifier une V1 prudente pour les envois officiels, LRAR, boite mail
connectee et preuves, sans ouvrir d'envoi automatique ni connecter un compte.

Ownership modifiable:

- ce document;
- `docs/presence_agents.md`;
- `docs/roadmap_backlog_central.md`.

Fichiers a eviter: code applicatif, plugins/connecteurs, secrets OAuth/IMAP,
instances privees, exports bruts, serveurs locaux et `RM-2026-0017`.

Sources publiques relues le 2026-05-24:

- Legifrance, code des postes et communications electroniques, article L100:
  https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000033207397
- Service-Public, convocation AG et formes de notification:
  https://www.service-public.gouv.fr/particuliers/vosdroits/F2615
- Service-Public, conservation des originaux papier/electroniques:
  https://www.service-public.fr/particuliers/vosdroits/F31215

## Roles

| Conversation | Role | Sortie |
|---|---|---|
| `CONV-2026-1612` | Coordinateur-scribe | Decision V1, limites et commande future. |
| `CONV-2026-1613` | Designer service | Parcours brouillon -> validation -> preuve. |
| `CONV-2026-1614` | Utilisateur novice / CS | GO/NO-GO comprehension et risques. |
| `CONV-2026-1615` | Privacy/securite | Mandats, consentements, secrets, preuve. |
| `CONV-2026-1616` | QA regression | Tests futurs et no-go d'envoi. |

Note anti-collision: `CONV-2026-1602` a ete pris par un chantier vivant
`RM-2026-0013` pendant ce cycle. La mission communication est donc renumerotee
en `CONV-2026-1612` a `1616`.

## Decision produit

Verdict: `GO_CADRAGE`, `NO-GO_CONNECTEUR_IMMEDIAT`, `NO-GO_ENVOI_AUTO`.

La V1 doit s'appeler `Courriers et preuves`, pas `Envoyer une LRAR`. Le premier
objectif est de preparer, valider et rattacher une preuve d'envoi ou de
reception. L'envoi effectif reste humain et hors CoproScope tant que le mandat,
le prestataire et les secrets ne sont pas qualifies.

La logique produit:

1. Rediger un brouillon depuis une demande, une resolution ou une action.
2. Choisir le type de suite: information simple, demande au syndic, mise en
   demeure, convocation, notification AG, reponse a coproprietaire.
3. Verifier le destinataire et le mandat d'envoi.
4. Afficher un avertissement clair: `CoproScope prepare, ne transmet pas`.
5. Enregistrer la preuve recue hors CoproScope: depot, accuse, reception,
   reponse, refus ou echec.
6. Rattacher la preuve a l'action, la resolution ou le point AG.

## Modele minimal V1

| Objet | Champs minimaux | Regle |
|---|---|---|
| `OfficialDraft` | `draft_id`, sujet, corps, source, statut, validateur | Brouillon local seulement. |
| `RecipientTarget` | role, libelle, adresse masquee, canal voulu | Pas de carnet brut dans l'UI. |
| `SendMandate` | qui envoie, au nom de qui, base de mandat, limite | Obligatoire avant toute suite engageante. |
| `HumanApproval` | validateur, date, decision, commentaire | Pas de validation implicite. |
| `DeliveryProof` | type preuve, date depot, date reception, reference opaque | Original conserve hors export large. |
| `InboundReply` | canal, date, resume, piece rattachee | Import local ou saisie manuelle en V1. |
| `ActionLink` | action/resolution/demande, preuve, prochaine suite | Trace probatoire derivee. |

Statuts recommandes:

- `BROUILLON`;
- `A_VALIDER`;
- `VALIDE_HUMAINEMENT`;
- `ENVOYE_HORS_COPROSCOPE`;
- `PREUVE_A_RATTACHER`;
- `RECEPTION_CONFIRMEE`;
- `ECHEC_OU_REFUS`;
- `CLOTURE`.

## Garde-fous

- Aucun bouton `Envoyer` en V1.
- Aucun OAuth, IMAP, SMTP, Drive ou API prestataire sans decision explicite de
  Brice et stockage de secret hors Git.
- Aucun destinataire deduit depuis un fichier coproprietaires sans verification
  humaine.
- Les convocations, PV et mises en demeure ont des exigences propres; CoproScope
  doit afficher une checklist, pas promettre la validite juridique.
- L'envoi recommande electronique peut etre equivalent a la lettre recommandee
  seulement si le cadre applicable est respecte; pour un destinataire non
  professionnel, le consentement a l'electronique doit etre verifie.
- Les originaux papier ou electroniques restent la preuve; les exports
  CoproScope sont des derives.

## Parcours novice

Ecran cible futur: `/courriers/preuves`.

Structure:

- file gauche: brouillons a valider, preuves a rattacher, reponses recues;
- panneau central: brouillon, source, destinataire, mandat, avertissement;
- panneau droit: checklist preuve et rattachement action/resolution;
- barre de decision: `Marquer valide`, `Copier le brouillon`, `Rattacher une
  preuve`, `Annuler`.

Microcopy obligatoire:

- `Brouillon`: texte prepare localement, pas encore transmis.
- `Mandat`: raison qui autorise quelqu'un a agir ou ecrire.
- `Preuve de depot`: trace que l'envoi a ete depose chez un service.
- `Preuve de reception`: trace que le destinataire ou son representant a recu
  ou refuse.

## Commande future

Commande dev proposee si priorisee:

```text
Construire `official_comms_evidence_v1` sans envoi:
- route future `/courriers/preuves`;
- template/CSS/tests dedies;
- donnees fictives;
- brouillons locaux, validation humaine, copie manuelle;
- rattachement de preuves d'envoi/reception sous reference opaque;
- aucun connecteur OAuth/IMAP/SMTP/LRAR;
- exports derives seulement, marques `source_of_truth=false`;
- tests anti-fuite sur emails, telephones, adresses, chemins, tokens, raw,
  restricted, logs et secrets.
```

## QA future

Panier minimal:

- route tokenisee;
- aucun bouton `Envoyer`;
- creation de brouillon sans transmission;
- validation humaine requise avant statut `VALIDE_HUMAINEMENT`;
- preuve rattachee par reference opaque;
- aucun email/adresse/telephone dans les sorties diffuses;
- exports derives non source de verite;
- line-limit et `git diff --check`.

## Questions ouvertes

- Qui peut etre mandataire d'envoi pour chaque type de courrier?
- Quels prestataires LRAR sont admissibles et comment verifier leurs preuves?
- Quel consentement est disponible pour l'electronique, surtout cote
  coproprietaires non professionnels?
- Quelle boite mail peut etre connectee sans exposer tous les messages?
- Quelle conservation des originaux est attendue par copropriete?

## BOT-END

BOT-END - Coordinateur-scribe communication officielle - 2026-05-24
22:13 +02:00.

Statut: `PRET_A_INTEGRER`.

Fichiers modifies: ce document, `docs/presence_agents.md`,
`docs/roadmap_backlog_central.md`.

Fichiers evites: code, connecteurs, secrets, instances privees, exports bruts,
serveurs locaux et `RM-2026-0017`.

Tests/preuves: sources officielles relues; `git diff --check` documentaire a
lancer apres mise a jour des registres.

Limites: pas d'avis juridique final, pas de choix prestataire, pas de secret
OAuth/IMAP, pas d'envoi reel.

AGILE-DONE - equipe agile a fini son job.
