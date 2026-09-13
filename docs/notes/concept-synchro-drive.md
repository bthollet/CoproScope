# Concept : une synchronisation chiffrée, Drive comme simple transport

**Statut : sans écran. Des commandes expérimentales existent en ligne de
commande, hors de l'installation proposée.**

## L'idée

Le travail en clair reste sur le poste. Pour partager, CoproScope prépare un
paquet, le **chiffre**, et se sert d'un service comme Drive uniquement pour le
transporter jusqu'aux personnes autorisées. Drive ne voit jamais le contenu.

## Pourquoi il n'y a pas d'écran

Le parcours complet — chiffrement, destinataires, révocation, reprise après
erreur — n'est pas terminé. Tant qu'il ne l'est pas, aucun écran ne l'active.
Les commandes `coprocs drive …`, elles, envoient réellement vers Drive si l'on
installe leur module et qu'on les lance : elles servent au développement, et
cette note ne dit pas qu'elles chiffrent.

## Notes liées

- [Carte des notes](carte.md)
- [Confidentialité](confidentialite.md)
- [Multi-utilisateur et coffre partagé](concept-multi-utilisateur-coffre-partage.md)
