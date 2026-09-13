# Accessibilite et registre de langage CoproScope

Date de reference: 2026-05-20

Objectif: rendre CoproScope comprehensible par les publics de l'enquete utilisateur, y compris des personnes qui decouvrent la copropriete. Le produit doit rester precis pour les membres du conseil syndical et les contributeurs techniques, mais le premier niveau de lecture doit parler a des novices.

## Publics cibles

- Coproprietaire novice: veut comprendre ce qui le concerne, ce qui est partageable, et pourquoi certains elements sont limites.
- Membre de conseil syndical benevole: veut savoir quoi traiter maintenant, avec quelle preuve et quelle prochaine action.
- Referent de commission: suit un theme precis, produit une synthese et doit citer ses sources sans acceder automatiquement a tout.
- Contributeur technique: maintient imports, plugins, vault et tests, sans imposer le jargon technique dans l'UI novice.

## Registre de langage stable

| Terme UI | Definition simple | Regle |
|---|---|---|
| Coffre de copro | Espace local et chiffre d'une copro, comparable a un vault Obsidian. | Dire `coffre` en UI, `vault` en detail technique. |
| Document | Fichier ajoute: facture, contrat, PV, courrier, photo, devis. | Terme general. |
| Piece | Document utilise pour comprendre ou prouver un sujet. | Terme de travail probatoire. |
| Preuve | Justificatif qui confirme une date, un montant, une decision ou une action. | Toujours preciser preuve de quoi. |
| Point | Sujet concret a suivre. | Relier a action et preuve. |
| Action | Ce qu'il faut faire ensuite, par qui et avant quand. | Chaque ecran principal doit en proposer une. |
| Diffusion | Partage controle a un public donne. | Toujours dire le public. |
| Restriction | Limite d'acces justifiee. | Toujours dire pourquoi. |
| Masquage | Information cachee avant partage. | Preferer a `biffage` pour novices. |
| Depot local | Ajout de fichiers dans le coffre de l'ordinateur, sans publication automatique. | Ne jamais laisser croire a une synchronisation cloud. |
| Empreinte technique | Code qui verifie qu'un fichier n'a pas change. | Preferer a `hash` en premier niveau. |
| Signature technique | Verification de l'auteur et de l'integrite d'un evenement. | Ne pas confondre avec signature manuscrite. |

## Termes a expliquer au moment utile

- Tantiemes: parts utilisees pour repartir les charges et certains votes.
- Fonds travaux: reserve de la copro pour financer certains travaux.
- Quorum: nombre minimum de voix ou de personnes pour certaines decisions.
- Biffage: masquage d'informations sensibles.
- Vault: terme technique pour coffre.
- P1/P2/OK: priorite critique, attention, conforme ou sans alerte.
- Plugin: module local optionnel, installe hors coffre.
- Sync: copie de fichiers chiffres entre appareils ou dossiers cloud.

## Regles UI

- Chaque page doit commencer par ce que l'utilisateur peut faire maintenant.
- Chaque carte importante doit montrer: pourquoi, preuve, prochaine action, partage possible.
- Les termes rares doivent avoir une infobulle ou une micro-definition proche.
- Les aides doivent aussi fonctionner sans souris: texte visible, lien adjacent, `details/summary` ou contenu accessible au clavier/tactile.
- Les textes techniques doivent etre replies dans `Details techniques`.
- Les erreurs doivent dire: probleme, cause probable, action de correction.
- Les tableaux doivent avoir un titre ou une `caption`, des en-tetes clairs et une action de ligne lisible.
- Ne pas utiliser la couleur seule pour un statut.
- Le focus clavier doit etre visible sur liens, boutons, champs et onglets.
- Les boutons doivent nommer l'action reelle: `Ajouter un document`, `Preparer une version diffusable`, `Demander une preuve`.
- La navigation globale doit utiliser des mots utilisateur ou expliquer les mots produit: `Cockpit` devient l'accueil des priorites, `Gouvernance` devient droits et roles, `Depot` reste local.

## Infobulles

Les infobulles doivent etre courtes, accessibles au clavier/tactile et non indispensables seules.

Exemples:

- `Tantiemes`: parts utilisees pour repartir les charges.
- `Information masquee`: une donnee sensible est cachee avant diffusion.
- `Empreinte technique`: permet de verifier que le fichier n'a pas ete modifie.
- `Coffre de copro`: espace local separe pour une copro.
- `Quorum de cles`: nombre minimum de personnes necessaires pour recuperer une cle.

## Checklist UX novice

- Le titre de page dit ce qu'on peut faire.
- La prochaine action est visible sans scroller longtemps.
- Un novice comprend les statuts sans formation.
- Les restrictions disent qui peut voir quoi et pourquoi.
- Les boutons disent la consequence de l'action.
- Les informations sensibles sont signalees avant diffusion.
- Les tables ne sont pas le seul mode de comprehension.
- Les termes techniques visibles sont expliques.
- Le parcours est faisable au clavier.
- Un etat vide explique quoi faire ensuite.

## Test de comprehension en 10 minutes

1. Ouvrir le cockpit et demander: quels sont les trois sujets urgents ?
2. Ouvrir une piece et demander: quelle preuve avons-nous ?
3. Demander ce qui peut etre partage et avec qui.
4. Faire expliquer un statut `a verifier`.
5. Faire trouver une prochaine action.
6. Montrer une restriction et demander pourquoi elle existe.
7. Ouvrir le depot et verifier que la personne ne confond pas depot, publication et sync.
8. Demander a la personne de resumer le dossier en une phrase.

Le test est reussi si la personne identifie une action legitime, comprend au moins quatre statuts sur cinq, distingue document ajoute/verifie/diffusable, et ne confond pas une restriction avec une panne.
