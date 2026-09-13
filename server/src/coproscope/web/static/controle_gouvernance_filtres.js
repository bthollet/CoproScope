/* Filtre sur place de l'accueil du controle de gouvernance. `RM-2026-0183`.

   Ce script ne recalcule RIEN. Il ne lit aucune appartenance et n'applique
   aucun filtre: il charge l'adresse que le serveur a construite pour la
   pastille, et remplace les pastilles et la liste par celles de la reponse.
   Un filtre ecrit une seconde fois ici serait un second chemin de calcul -
   le defaut numero un du produit - et le canal de panne (`n=` compare au
   nombre trouve) cesserait de le voir.

   Sans script, ou si le chargement echoue, le lien fait une navigation
   ordinaire: meme page, meme rendu. */
(function () {
  "use strict";
  var ZONES = ["cs-constats", "cs-liste"];

  function zonesPresentes(doc) {
    return ZONES.every(function (id) { return doc.getElementById(id); });
  }

  function remplacer(doc) {
    ZONES.forEach(function (id) {
      var ancien = document.getElementById(id);
      var neuf = doc.getElementById(id);
      ancien.replaceWith(document.importNode(neuf, true));
    });
  }

  function annoncer() {
    var zone = document.querySelector("[data-cs-annonce]");
    var tete = document.querySelector("#cs-liste .panel-head span");
    if (zone && tete) { zone.textContent = tete.textContent.trim() + "."; }
  }

  function charger(href, cle, empiler) {
    return fetch(href, { credentials: "same-origin", headers: { "Accept": "text/html" } })
      .then(function (reponse) {
        if (!reponse.ok) { throw new Error("statut " + reponse.status); }
        return reponse.text();
      })
      .then(function (texte) {
        var doc = new DOMParser().parseFromString(texte, "text/html");
        if (!zonesPresentes(doc)) { throw new Error("zones absentes"); }
        remplacer(doc);
        if (empiler) { history.pushState({ csFiltre: cle }, "", href); }
        annoncer();
        // Sur un ecran etroit la liste est sous les pastilles: y amener le regard,
        // sinon le clic semble ne rien faire (tour 2 du novice).
        var etroit = window.matchMedia && window.matchMedia("(max-width: 760px)").matches;
        var retour = etroit ? document.getElementById("cs-liste")
          : cle && document.querySelector('[data-cs-filtre="' + cle + '"]');
        if (retour) { retour.focus(); }
      })
      .catch(function () { window.location.assign(href); });
  }

  if (!zonesPresentes(document) || !window.fetch || !window.DOMParser || !history.pushState) { return; }

  document.addEventListener("click", function (evenement) {
    var lien = evenement.target.closest("a[data-cs-filtre], #cs-liste .cs-provenance a");
    if (!lien || evenement.defaultPrevented || evenement.button !== 0
        || evenement.metaKey || evenement.ctrlKey || evenement.shiftKey || evenement.altKey) { return; }
    evenement.preventDefault();
    var cle = lien.getAttribute("data-cs-filtre") || "tout";
    charger(lien.href, cle, true);
  });

  window.addEventListener("popstate", function () {
    charger(window.location.href, "", false);
  });
})();
