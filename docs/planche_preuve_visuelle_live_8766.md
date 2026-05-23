# Planche de preuve visuelle live 8766

Date: 2026-05-21
Serveur teste: `http://127.0.0.1:8766/?token=local-secret`

Cette planche sert de reference commune pour le cycle image -> dev -> test produit livre. Les images de gauche sont les cibles issues de l'enquete utilisateur. Les captures live initiales viennent de `docs/assets/ux-livraison-reelle-2026-05-21-8766/`. Les captures apres reprise viennent de `docs/assets/ux-livraison-reelle-2026-05-21-8766-apres-reprise/`.

## Cockpit Conseil Syndical

Image cible:

![Cockpit cible](assets/etude-utilisateurs/cockpit-conseil-syndical.png)

Capture live:

![Cockpit live 8766](assets/ux-livraison-reelle-2026-05-21-8766/01_cockpit.png)

Capture apres reprise:

![Cockpit live 8766 apres reprise](assets/ux-livraison-reelle-2026-05-21-8766-apres-reprise/01_cockpit.png)

Observation initiale: la cible affiche immediatement les cartes "A traiter" et les blocs metier. La livraison live initiale consacre la premiere vue au contexte/coffre/role/sync, ce qui repousse le cockpit utile. Apres reprise, le contexte devient compact et le contenu metier revient dans le premier ecran.

## Registre Decisions Actions Preuves

Image cible:

![Registre cible](assets/etude-utilisateurs/registre-decisions-actions-preuves.png)

Capture live:

![Registre live 8766](assets/ux-livraison-reelle-2026-05-21-8766/02_actions.png)

Capture apres reprise:

![Registre live 8766 apres reprise](assets/ux-livraison-reelle-2026-05-21-8766-apres-reprise/02_actions.png)

Observation initiale: la cible donne une vue maitre-detail dense, avec resolutions, action selectionnee, preuves, pieces, relance et historique visibles. La livraison live initiale commence par le meme bloc contexte puis seulement les compteurs et l'introduction. Apres reprise, la coque ne bloque plus le premier ecran, mais le registre doit encore etre rapproche du master-detail Canva.

## Controle Des Comptes

Image cible:

![Comptes cible](assets/etude-utilisateurs/controle-comptes-guide.png)

Capture live:

![Comptes live 8766](assets/ux-livraison-reelle-2026-05-21-8766/03_comptes.png)

Capture apres reprise:

![Comptes live 8766 apres reprise](assets/ux-livraison-reelle-2026-05-21-8766-apres-reprise/03_comptes.png)

Observation initiale: la cible montre des donnees operationnelles et un panneau de detail categorie. La livraison live initiale affiche plusieurs compteurs a zero ou "A calculer", ce qui fragilise la promesse metier. Apres reprise back, le modele expose des donnees non vides et des questions syndic, mais le front comptes doit encore consommer tous les champs pour rejoindre la cible.

## Memoire De Copropriete

Image cible:

![Memoire cible](assets/etude-utilisateurs/memoire-copropriete.png)

Capture live:

![Memoire live 8766](assets/ux-livraison-reelle-2026-05-21-8766/04_memoire.png)

Capture apres reprise:

![Memoire live 8766 apres reprise](assets/ux-livraison-reelle-2026-05-21-8766-apres-reprise/04_memoire.png)

Observation initiale: la cible met la ligne de vie et le panneau passation dans la premiere vue. La livraison live a la bonne intention, mais la zone utile descend et le panneau lateral de passation n'est pas encore visible dans la premiere capture. Apres reprise de coque, le premier ecran est moins parasite, mais le layout timeline + rail droit reste la prochaine reprise UX.
