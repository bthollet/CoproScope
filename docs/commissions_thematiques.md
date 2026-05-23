# Commissions thematiques

Date de reference: 2026-05-20

Ce document decrit le modele V1 des commissions thematiques. Il complete les
objets comptes et accessops sans remplacer leurs controles de droits.

## Objectif V1

Une commission doit etre lisible par une personne novice:

- qui participe;
- qui valide;
- sur quelle periode et quel sujet le mandat existe;
- quelles productions sont liees a des preuves ou actions;
- ce qui peut etre partage, et a quel niveau.

La V1 reste volontairement legere. Elle ne cree pas de gouvernance parallele:
la commission aide le conseil syndical a travailler sur un sujet borne, avec un
referent CS et des droits limites.

## Objets

`Commission`

- identifie la commission, son libelle et son sujet;
- cite le referent CS;
- garde une liste simple de membres attendus;
- porte une periode et une revocation eventuelle;
- definit un niveau de diffusion par defaut.

`CommissionMandate`

- rattache la commission a un sujet et une periode;
- cite le corps de validation, par defaut le conseil syndical;
- peut nommer des validateurs;
- garde la decision, action ou evenement source.

`CommissionProduction`

- decrit une note, synthese, rapport, avis ou export produit par la commission;
- cite son mandat;
- rattache des preuves (`proof_refs`) et des actions (`action_refs`);
- indique un droit de diffusion: `commission`, `cs`, `copro`, `public`;
- devient partageable seulement si elle est validee et tracable.

## Droits

CommissionOps s'appuie sur `core.accounts`:

- `VaultMember` represente la personne dans le coffre;
- `CommissionMembership` borne la participation par commission, sujet et dates;
- `RoleGrant` donne les roles globaux comme `conseil_syndical`;
- `AccessGrant` peut ouvrir explicitement une ressource;
- `can_member_access_resource` reste le helper de decision d'acces.

Les niveaux de diffusion sont traduits vers les niveaux comptes:

- `commission` -> niveau `commission`, visible aux membres de la commission ou au CS;
- `cs` -> niveau `cs`, visible au conseil syndical ou via acces explicite;
- `copro` -> niveau `copro`, visible aux coproprietaires autorises;
- `public` -> niveau `copro` cote droits V1, avec obligation produit de redaction avant sortie externe.

## Validation

Une production peut etre validee par:

- le referent CS nomme dans la commission;
- un validateur nomme dans le mandat;
- un membre ayant le role `conseil_syndical`;
- un membre actif de la commission avec le role `referent_commission`.

La validation est refusee si la commission est inactive, si le mandat est expire
ou si le sujet du mandat ne correspond pas au sujet de la commission.

## Resume novice

Le helper `novice_summary` repond avec trois listes:

- `qui_participe`: referent CS et membres actifs;
- `qui_valide`: corps de validation, validateurs nommes et referent CS;
- `ce_qui_peut_etre_partage`: productions validees, avec preuve ou action rattachee, et niveau de diffusion.

Il ajoute des avertissements quand une commission ou un mandat est inactif,
qu'une production sort du perimetre, ou qu'une production n'a pas de preuve ou
d'action rattachee.

## Limites V1

- Une production partageable n'est pas une preuve juridique autonome.
- Les pieces brutes restent gouvernees par leurs droits propres.
- La diffusion `public` ne dispense jamais d'une version redactee.
- La revocation bloque les acces futurs mais conserve l'historique auditable.
