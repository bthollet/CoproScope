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

  var state = { mode: "", target: null, start: null, box: null };
  var root = document.createElement("aside");
  root.className = "recette-panel";
  root.setAttribute("aria-label", "Mode test de l'interface");
  root.innerHTML = [
    '<div class="recette-panel__bar">',
    '<strong>Mode test actif</strong>',
    '<button type="button" data-recette-mode="object">Pointer un element</button>',
    '<button type="button" data-recette-mode="zone">Dessiner une zone</button>',
    '<a href="' + escapeAttr(config.pageUrl || "/recette") + '">Voir les remarques</a>',
    "</div>",
    '<form class="recette-panel__form" hidden>',
    '<label>Que faut-il corriger ?',
    '<textarea name="comment" rows="3" maxlength="500" placeholder="Ex. ce bouton n\\'est pas clair, ce bloc deborde, il manque une explication"></textarea>',
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
  var status = root.querySelector(".recette-panel__status");
  var zoneBox = root.querySelector(".recette-zone-box");

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
    var target = event.target.closest("button, a, input, select, textarea, [role], article, section, tr, li, .card");
    if (!target) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    state.target = elementPayload(target, "object");
    showForm("Objet pointe: " + state.target.target_label);
  }, true);

  document.addEventListener("pointerdown", function (event) {
    if (state.mode !== "zone" || root.contains(event.target)) {
      return;
    }
    event.preventDefault();
    state.start = { x: event.clientX, y: event.clientY };
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
    }
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    saveAnnotation();
  });

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
    state = { mode: "", target: null, start: null, box: null };
    document.body.classList.remove("recette-is-selecting");
    form.hidden = true;
    form.reset();
    zoneBox.hidden = true;
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
      box_x: box.x,
      box_y: box.y,
      box_width: box.width,
      box_height: box.height,
    };
  }

  function drawBox(x, y) {
    var start = state.start || { x: x, y: y };
    var left = Math.min(start.x, x);
    var top = Math.min(start.y, y);
    var width = Math.abs(start.x - x);
    var height = Math.abs(start.y - y);
    state.box = { x: left, y: top, width: width, height: height };
    zoneBox.hidden = false;
    zoneBox.style.left = left + "px";
    zoneBox.style.top = top + "px";
    zoneBox.style.width = width + "px";
    zoneBox.style.height = height + "px";
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

  function message(text) {
    status.textContent = text || "";
  }

  function escapeAttr(value) {
    return String(value || "").replace(/[&<>"]/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[char];
    });
  }
}());
