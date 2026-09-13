/* Volet de gauche rabattable. `RM-2026-0184`, recette de Brice du 2026-09-13.
 *
 * Replie, le menu garde ses entrees: seules les icones restent visibles, et
 * chaque lien porte deja un `aria-label` qui le nomme pour un lecteur d'ecran.
 * L'etat se memorise dans le navigateur; si le stockage est refuse (navigation
 * privee, reglage du poste), le bouton marche quand meme pour la page ouverte.
 */
(function () {
  "use strict";
  var CLE = "coproscope.menu.replie";
  var coque = document.querySelector(".cs-app-shell");
  var bouton = document.querySelector(".cs-volet-bascule");
  if (!coque || !bouton) {
    return;
  }

  function lire() {
    try { return window.localStorage.getItem(CLE) === "1"; } catch (erreur) { return false; }
  }

  function ecrire(replie) {
    try { window.localStorage.setItem(CLE, replie ? "1" : "0"); } catch (erreur) { /* etat de la page seulement */ }
  }

  function appliquer(replie) {
    coque.classList.toggle("cs-menu-replie", replie);
    bouton.setAttribute("aria-expanded", replie ? "false" : "true");
    var libelle = replie ? "Deplier le menu" : "Replier le menu";
    bouton.setAttribute("aria-label", libelle);
    bouton.setAttribute("title", libelle);
  }

  appliquer(lire());
  bouton.addEventListener("click", function () {
    var replie = !coque.classList.contains("cs-menu-replie");
    appliquer(replie);
    ecrire(replie);
  });
}());
