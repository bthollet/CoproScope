# Integration bandeau contexte

## Contrat minimal

Le socle UI inclut le partial `_context_banner.html` depuis `base.html` seulement quand la variable de template `context_banner` est definie et non vide. Les pages qui ne transmettent pas cet objet n'affichent aucun bandeau et continuent a rendre la base sans preparation particuliere.

Cette integration reste volontairement cote template: elle ne cree pas de nouvelle route et se fait sans modifier app.py ni viewmodel.py. Le producteur de donnees garde donc la responsabilite de fournir `context_banner` quand une page connait le coffre, le role, le niveau d'acces, l'etat du vault, l'etat de sync et la prochaine action utile.

## Emplacement et accessibilite

Le bandeau est place apres la navigation principale et avant l'aide rapide. Le partial expose un `aside` avec un libelle ARIA explicite pour que le contexte du coffre, du role et de la synchronisation soit annonce comme information complementaire.

Le style ajoute dans `styles.css` reste sobre: fond clair, bordure visible, tons `ok`, `review` et `risk`, lien de prochaine action souligne, et grille responsive pour eviter les chevauchements sur mobile.

## Tests

`server/tests/test_ui_context_banner_integration.py` couvre trois points:

- rendu de `base.html` sans `context_banner`, y compris avec `StrictUndefined`;
- rendu de `base.html` avec un objet `context_banner` minimal;
- presence des styles et de ce document de contrat.
