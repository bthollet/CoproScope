(function () {
  "use strict";

  var configNode = document.getElementById("cs-recette-config");
  if (!configNode) {
    return;
  }

  var config = {};
  try {
    config = JSON.parse(configNode.textContent || "{}");
  } catch (error) {
    return;
  }

  var defaultEnabled = config.recetteModeEnabled === true;
  var cookieName = String(config.cookieName || "coproscope_recette_mode");
  var state = {
    mode: "",
    target: null,
    start: null,
    box: null,   // en coordonnees de DOCUMENT
    cible: null, // l'element pointe, remesure a chaque deplacement
  };

  var toggleButton = document.getElementById("cs-recette-mode-toggle");
  var status = document.getElementById("cs-recette-mode-status");

  var root = document.createElement("aside");
  root.className = "recette-panel";
  root.hidden = true;
  root.setAttribute("aria-label", "Mode test de l'interface");
  root.innerHTML = [
    '<div class="recette-panel__bar">',
    '<strong>Mode test actif</strong>',
    '<button type="button" data-recette-mode="object">Pointer un element</button>',
    '<button type="button" data-recette-mode="zone">Dessiner une zone</button>',
    '<a href="' + escapeAttr(config.pageUrl || "/recette") + '">Voir les remarques</a>',
    '<p class="recette-panel__note" role="status"></p>',
    "</div>",
    '<form class="recette-panel__form" hidden>',
    '<label>Que faut-il corriger ?',
    '<textarea name="comment" rows="3" maxlength="500" placeholder="Ex. ce bouton n\'est pas clair, ce bloc deborde, il manque une explication"></textarea>',
    "</label>",
    '<label>Gravite',
    '<select name="severity">',
    '<option value="important">Important</option>',
    '<option value="bloquant">Bloquant</option>',
    '<option value="detail">Detail</option>',
    "</select>",
    "</label>",
    '<div class="recette-panel__actions">',
    '<button type="submit">Enregistrer la remarque</button>',
    '<button type="button" data-recette-cancel>Annuler</button>',
    "</div>",
    '<p class="recette-panel__status" role="status"></p>',
    "</form>",
    '<div class="recette-zone-box" hidden></div>',
  ].join("");
  document.body.appendChild(root);

  var form = root.querySelector("form");
  var note = root.querySelector(".recette-panel__note");

  // Les deux marques sortent du panneau, qui est `position: fixed`: un enfant
  // absolu d'un parent fixe se placerait par rapport a la FENETRE, et suivrait
  // donc l'oeil au lieu de suivre le contenu. Attachees au corps, elles se
  // placent par rapport au DOCUMENT.
  var zoneBox = root.querySelector(".recette-zone-box");
  document.body.appendChild(zoneBox);

  var cibleBox = document.createElement("div");
  cibleBox.className = "recette-cible-box";
  cibleBox.hidden = true;
  document.body.appendChild(cibleBox);

  //: Ce sur quoi on peut pointer. Une seule definition, partagee par le survol
  //: et par le clic: sans cela on surligne un element et on en enregistre un autre.
  var CIBLES = "button, a, input, select, textarea, [role], article, section, tr, li, .card";

  root.addEventListener("click", function (event) {
    var modeButton = event.target.closest("[data-recette-mode]");
    if (modeButton) {
      event.preventDefault();
      startMode(modeButton.getAttribute("data-recette-mode"));
      return;
    }
    if (event.target.closest("[data-recette-cancel]")) {
      event.preventDefault();
      reset();
    }
  });

  document.addEventListener("click", function (event) {
    if (state.mode !== "object" || root.contains(event.target)) {
      return;
    }
    var target = event.target.closest(CIBLES);
    if (!target) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    state.target = elementPayload(target, "object");
    suivre(target, true);
    showForm("Objet pointe: " + state.target.target_label);
  }, true);

  // Sans surlignage, on ne sait pas ce qu'on va designer avant de l'avoir
  // designe: le libelle n'arrive qu'apres le clic, et il est souvent ambigu.
  document.addEventListener("mouseover", function (event) {
    if (state.mode !== "object" || state.target || root.contains(event.target)) {
      return;
    }
    suivre(event.target.closest(CIBLES), false);
  }, true);

  document.addEventListener("pointerdown", function (event) {
    if (state.mode !== "zone" || root.contains(event.target)) {
      return;
    }
    event.preventDefault();
    state.start = versDocument(event.clientX, event.clientY);
    state.box = null;
    drawBox(event.clientX, event.clientY);
  }, true);

  document.addEventListener("pointermove", function (event) {
    if (state.mode !== "zone" || !state.start) {
      return;
    }
    event.preventDefault();
    drawBox(event.clientX, event.clientY);
  }, true);

  document.addEventListener("pointerup", function (event) {
    if (state.mode !== "zone" || !state.start) {
      return;
    }
    event.preventDefault();
    drawBox(event.clientX, event.clientY);
    state.target = zonePayload();
    state.start = null;
    showForm("Zone selectionnee");
  }, true);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && state.mode) {
      reset();
      return;
    }
    if (isTextInput(event.target)) {
      return;
    }
    if (isModeShortcut(event)) {
      event.preventDefault();
      toggleMode();
      return;
    }
  }, true);

  if (toggleButton) {
    toggleButton.addEventListener("click", function (event) {
      event.preventDefault();
      toggleMode();
    });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    saveAnnotation();
  });

  syncMode();

  function toggleMode() {
    var enabled = !readModeEnabled();
    setModeEnabled(enabled);
  }

  function setModeEnabled(enabled) {
    setCookie(cookieName, enabled ? "1" : "0", 30);
    applyModeVisibility(enabled);
  }

  function syncMode() {
    var enabled = readModeEnabled();
    applyModeVisibility(enabled);
  }

  function readModeEnabled() {
    var value = readCookie(cookieName);
    if (value === "1" || value === "true" || value === "on") {
      return true;
    }
    if (value === "0" || value === "false" || value === "off") {
      return false;
    }
    return defaultEnabled;
  }

  function applyModeVisibility(enabled) {
    root.hidden = !enabled;
    if (!toggleButton) {
      if (enabled) {
        annonce("Mode test actif");
      }
      return;
    }

    if (enabled) {
      toggleButton.textContent = "Mode test actif";
      toggleButton.setAttribute("aria-pressed", "true");
      toggleButton.setAttribute("title", "Desactiver le mode test (Alt + Shift + T)");
      annonce("Mode test actif");
      return;
    }

    reset(false);
    toggleButton.textContent = "Mode test";
    toggleButton.setAttribute("aria-pressed", "false");
    toggleButton.setAttribute("title", "Activer le mode test (Alt + Shift + T)");
    annonce("");
  }

  function startMode(mode) {
    reset(false);
    state.mode = mode;
    document.body.classList.add("recette-is-selecting");
    message(mode === "zone" ? "Dessinez une zone sur l'ecran." : "Cliquez sur un element a signaler.");
  }

  function showForm(text) {
    form.hidden = false;
    message(text);
    form.querySelector("textarea").focus();
  }

  function reset(clearMessage) {
    state = { mode: "", target: null, start: null, box: null, cible: null };
    document.body.classList.remove("recette-is-selecting");
    form.hidden = true;
    form.reset();
    zoneBox.hidden = true;
    cibleBox.hidden = true;
    cibleBox.classList.remove("is-pointe");
    if (clearMessage !== false) {
      message("");
    }
  }

  function saveAnnotation() {
    var comment = form.querySelector("textarea").value.trim();
    if (!comment) {
      message("Ajoutez une remarque courte.");
      return;
    }
    var payload = Object.assign(basePayload(), state.target || {});
    payload.comment = comment;
    payload.severity = form.querySelector("select").value;
    fetch(config.saveUrl || "/recette/annotations", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-coproscope-token": config.token || "",
      },
      body: JSON.stringify(payload),
    }).then(function (response) {
      if (!response.ok) {
        throw new Error("save failed");
      }
      return response.json();
    }).then(function () {
      reset(false);
      message("Remarque enregistree.");
    }).catch(function () {
      message("Enregistrement impossible.");
    });
  }

  function basePayload() {
    return {
      url: window.location.pathname + window.location.search,
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
      scroll_x: window.scrollX,
      scroll_y: window.scrollY,
    };
  }

  function elementPayload(element, kind) {
    var rect = element.getBoundingClientRect();
    return {
      target_kind: kind,
      target_label: labelFor(element),
      target_role: element.getAttribute("role") || element.tagName.toLowerCase(),
      target_selector: selectorFor(element),
      target_text: (element.innerText || element.value || "").trim().slice(0, 180),
      box_x: rect.left,
      box_y: rect.top,
      box_width: rect.width,
      box_height: rect.height,
    };
  }

  function zonePayload() {
    var box = state.box || { x: 0, y: 0, width: 0, height: 0 };
    return {
      target_kind: "zone",
      target_label: "Zone libre",
      target_role: "zone",
      target_selector: "viewport-zone",
      target_text: "",
      // `state.box` est en coordonnees de document depuis ce lot, mais le
      // registre range `box_*` en coordonnees de FENETRE a cote de `scroll_*`,
      // et `elementPayload` fait de meme. On reconvertit donc ici plutot que de
      // changer en silence le sens d'une colonne deja ecrite: une migration de
      // schema ne se glisse pas dans un correctif visuel.
      box_x: box.x - window.scrollX,
      box_y: box.y - window.scrollY,
      box_width: box.width,
      box_height: box.height,
    };
  }

  /* -- Ou vit une marque -------------------------------------------------
   *
   * L'axe: une marque designe un endroit du DOCUMENT. La fenetre est un cadre
   * mobile pose dessus, donc une marque exprimee en coordonnees de fenetre
   * n'est vraie qu'a l'instant ou elle a ete posee - elle reste sur place des
   * que la page bouge. C'est le defaut signale par Brice le 2026-09-07: *ta
   * zone de selection reste fixe quand on se deplace dans la page*.
   *
   * Deux marques, deux ancrages, parce qu'elles ne designent pas la meme chose:
   * la zone libre designe une REGION du document, donc des coordonnees de
   * document suffisent; l'objet pointe designe un ELEMENT, qui peut bouger sans
   * que la page defile - dans un tableau qui defile a l'interieur de son cadre,
   * par exemple - donc sa marque se remesure au lieu de se calculer une fois.
   *
   * Reserve assumee: une zone libre tracee au-dessus d'une region qui defile
   * pour son compte reste solidaire de la PAGE, pas du contenu de cette region.
   * Une zone est une region de la page; pour designer une ligne d'un tableau,
   * c'est `Pointer un element` qui est l'outil juste.
   */

  /* On ne suppose pas que le corps est `static`: s'il est positionne, une boite
   * absolue s'y refere et non au document.
   *
   * Mesure une fois par armement, jamais par image. Premiere version: un
   * `getComputedStyle` a chaque image - sur la page de gouvernance et ses 363
   * lignes, ce recalcul de style force a 60 Hz a suffi a figer le rendu. Le
   * positionnement du corps ne change pas pendant qu'on pointe; le relire une
   * fois par armement est exact en pratique, et c'est la reserve a connaitre.
   */
  var origineCorps = { x: 0, y: 0 };
  function mesurerOrigineDuCorps() {
    if (window.getComputedStyle(document.body).position === "static") {
      origineCorps = { x: 0, y: 0 };
      return;
    }
    var rect = document.body.getBoundingClientRect();
    origineCorps = { x: rect.left + window.scrollX, y: rect.top + window.scrollY };
  }

  function versDocument(clientX, clientY) {
    return { x: clientX + window.scrollX, y: clientY + window.scrollY };
  }

  function poser(boite, x, y, width, height) {
    boite.hidden = false;
    boite.style.left = (x - origineCorps.x) + "px";
    boite.style.top = (y - origineCorps.y) + "px";
    boite.style.width = width + "px";
    boite.style.height = height + "px";
  }

  function suivre(element, pointe) {
    state.cible = element || null;
    cibleBox.classList.toggle("is-pointe", pointe === true);
    majCible();
    lancerSuivi();
  }

  function majCible() {
    var element = state.cible;
    if (!element || !document.contains(element)) {
      cibleBox.hidden = true;
      return;
    }
    var rect = element.getBoundingClientRect();
    if (!rect.width && !rect.height) {
      cibleBox.hidden = true;
      return;
    }
    poser(cibleBox, rect.left + window.scrollX, rect.top + window.scrollY, rect.width, rect.height);
  }

  function majZone() {
    if (!state.box) {
      return;
    }
    poser(zoneBox, state.box.x, state.box.y, state.box.width, state.box.height);
  }

  /* On ne s'abonne pas aux evenements qui DEPLACENT l'element: ce serait
   * enumerer les causes auxquelles on a pense. Premiere version de ce
   * correctif: `scroll` en capture et `resize`. Elle a tenu sur le defilement
   * et rate le cas suivant, observe dans la minute - pointer un element insere
   * son libelle dans la barre haute, la barre grandit, toute la page descend
   * de 110 px, et ni `scroll` ni `resize` ne se declenchent. La marque restait
   * 40 px au-dessus de sa cible.
   *
   * L'invariant est: *la marque est sur sa cible*. La seule facon de le tenir
   * quelle que soit la cause du deplacement est de remesurer a chaque image,
   * tant qu'il y a quelque chose a marquer. La boucle s'arrete d'elle-meme des
   * qu'aucune marque n'est posee, donc elle ne coute rien au repos.
   */
  var suiviActif = false;
  function lancerSuivi() {
    if (suiviActif) {
      return;
    }
    suiviActif = true;
    mesurerOrigineDuCorps();
    window.requestAnimationFrame(function boucle() {
      if (!state.cible && !state.box) {
        suiviActif = false;
        return;
      }
      majCible();
      majZone();
      window.requestAnimationFrame(boucle);
    });
  }

  function drawBox(clientX, clientY) {
    var point = versDocument(clientX, clientY);
    var start = state.start || point;
    var left = Math.min(start.x, point.x);
    var top = Math.min(start.y, point.y);
    var width = Math.abs(start.x - point.x);
    var height = Math.abs(start.y - point.y);
    state.box = { x: left, y: top, width: width, height: height };
    poser(zoneBox, left, top, width, height);
    lancerSuivi();
  }

  function labelFor(element) {
    return (
      element.getAttribute("aria-label") ||
      element.getAttribute("title") ||
      element.innerText ||
      element.value ||
      element.tagName
    ).trim().slice(0, 120);
  }

  function selectorFor(element) {
    if (element.id) {
      return "#" + element.id;
    }
    if (element.getAttribute("data-testid")) {
      return '[data-testid="' + element.getAttribute("data-testid") + '"]';
    }
    return element.tagName.toLowerCase();
  }

  /* Le message du mode test se lit DANS le panneau, pas dans la barre haute.
   *
   * Il ecrivait dans `#cs-recette-mode-status`, qui vit dans `.instance-meta`.
   * Deux consequences mesurees le 2026-09-07: un libelle un peu long faisait
   * grandir la barre haute et DESCENDRE toute la page de 110 px - la marque se
   * retrouvait 40 px au-dessus de sa cible -, et sous 1281 px ce conteneur est
   * masque (`RM-2026-0111`), donc aucun message n'etait lisible. Le panneau est
   * fixe: ce qu'on y ecrit ne deplace rien et reste visible a toute largeur.
   */
  function message(text) {
    if (note) {
      note.textContent = text || "";
    }
  }

  //: La barre haute ne garde que l'etat marche/arret, court et stable.
  function annonce(text) {
    if (status) {
      status.textContent = text || "";
    }
  }

  function escapeAttr(value) {
    return String(value || "").replace(/[&<>\"]/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[char];
    });
  }

  function readCookie(name) {
    if (!name) {
      return "";
    }
    var rawCookies = document.cookie ? document.cookie.split(";") : [];
    var search = name + "=";
    for (var i = 0; i < rawCookies.length; i += 1) {
      var cookie = rawCookies[i].trim();
      if (cookie.indexOf(search) === 0) {
        return decodeURIComponent(cookie.substring(search.length));
      }
    }
    return "";
  }

  function setCookie(name, value, maxDays) {
    var maxAge = Math.max(0, parseInt(maxDays, 10) || 0) * 24 * 60 * 60;
    var expires = maxAge > 0 ? "; Max-Age=" + maxAge : "";
    document.cookie = name + "=" + encodeURIComponent(value) + "; Path=/; SameSite=Lax" + expires;
  }

  function isModeShortcut(event) {
    return ((event.altKey || event.ctrlKey) && event.shiftKey && (event.key === "T" || event.key === "t" || event.code === "KeyT"));
  }

  function isTextInput(target) {
    if (!target || !target.tagName) {
      return false;
    }
    var tag = target.tagName.toLowerCase();
    return (
      target.isContentEditable ||
      tag === "input" ||
      tag === "textarea" ||
      tag === "select"
    );
  }
}());
