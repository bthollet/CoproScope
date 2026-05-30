# Strategie Drive Et Confidentialite

Navigation:
[README GitHub](../../README.md) |
[Decouvrir](./README.md) |
[Galerie](./galerie-visuelle.md) |
[Parcours](./parcours-demonstratifs.md) |
[Supports ecran](./supports-ecran.md) |
[Sponsors](./sponsors-et-partenaires.md) |
[Maturite](./maturite-et-limites.md) |
[Index docs](../README.md)

CoproScope manipule des sujets sensibles: comptes, travaux, contrats, impayes,
contentieux, demandes au syndic, documents personnels et preuves internes.

La confiance repose donc sur une separation simple: le travail clair reste dans
le coffre local; Drive transporte seulement une version chiffree et controlee.

![Confiance par conception](../assets/showcase/confiance-par-conception-16x9.png)

Ouvrir le visuel:
[confiance par conception](../assets/showcase/confiance-par-conception-16x9.png)

## Le Principe

Dans le modele cible:

- CoproScope travaille d'abord localement;
- les originaux restent dans le coffre de travail;
- le partage passe par une zone preparee;
- CoproScope controle la zone avant envoi;
- Drive transporte un paquet chiffre;
- la lecture se fait apres verification sur un poste autorise.

Drive reste donc un moyen de transport. Il ne decide pas qui a le droit de lire,
il ne remplace pas le coffre local et il ne devient pas la source de verite.

## Ce Que L'Utilisateur Doit Voir

L'interface cible doit afficher clairement:

- le compte Drive utilise;
- le dossier CoproScope dedie;
- les objets qui vont etre envoyes;
- le resultat du controle anti-fuite;
- le statut du paquet chiffre;
- les conflits ou doutes qui bloquent l'envoi.

Une personne non technique doit pouvoir comprendre l'etat du partage sans ouvrir
une console ou inspecter un dossier cache.

![Coffre et partage Drive chiffre](../assets/showcase/coffre-partage-drive-chiffre.png)

Ouvrir le visuel:
[coffre et partage Drive chiffre](../assets/showcase/coffre-partage-drive-chiffre.png)

## Strategie Cible Drive

```mermaid
flowchart LR
    A["Coffre local<br/>documents clairs"] --> B["Controle CoproScope<br/>revue et blocage si doute"]
    B --> C["Paquet chiffre<br/>aucun clair dans Drive"]
    C --> D["Drive<br/>transport seulement"]
    D --> E["Poste autorise<br/>verification locale"]
    E --> F["Lecture<br/>memoire et actions"]
```

Le message a garder: Drive aide a transporter, mais il ne devient ni le coffre,
ni le juge des droits, ni la source de verite.

## PrivacyOps Et BiffageOps

Deux briques aident a preparer une diffusion prudente:

- `PrivacyOps` repere les signaux sensibles et propose une politique d'acces;
- `BiffageOps` prepare des versions biffees ou pseudonymisees quand c'est
  possible.

Un document bien ecrit n'est pas automatiquement partageable. Il faut aussi
savoir qui peut le lire, ce qui doit etre masque et quelle validation humaine
reste necessaire.

## Validation Humaine

CoproScope peut aider a reperer, classer et expliquer. Il ne doit pas transformer
un signal en verdict final sans revue.

Une preuve doit dire:

- preuve de quoi;
- depuis quelle source;
- avec quelle periode;
- avec quelle limite;
- pour quel public.

## Regle De Prudence

Si le controle echoue ou si le doute subsiste, le partage reste bloque. Cette
prudence n'est pas un frein commercial: c'est la condition pour travailler sur
des dossiers sensibles sans banaliser le risque.
