(function () {
  "use strict";

  var MIN_SIZE_PX = 8;

  function formatUnit(value) {
    var bounded = Math.max(0, Math.min(1, value));
    return bounded.toFixed(6).replace(/0+$/, "").replace(/\.$/, "");
  }

  function setStatus(section, text) {
    Array.prototype.forEach.call(
      section.querySelectorAll("[data-pdf-trace-status]"),
      function (node) {
        node.textContent = text;
      }
    );
  }

  function pointInLayer(layer, event) {
    var rect = layer.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(rect.width, event.clientX - rect.left)),
      y: Math.max(0, Math.min(rect.height, event.clientY - rect.top)),
      width: rect.width,
      height: rect.height
    };
  }

  function field(form, name) {
    return form.querySelector("[data-pdf-trace-field='" + name + "']");
  }

  function setSubmitEnabled(button, enabled) {
    if (!button) {
      return;
    }
    button.disabled = !enabled;
    button.setAttribute("aria-disabled", enabled ? "false" : "true");
  }

  function wireWorkbench(workbench) {
    var section = workbench.closest("section");
    if (!section) {
      return;
    }
    var layer = section.querySelector("[data-pdf-trace-selection]");
    var box = section.querySelector("[data-pdf-trace-box]");
    var form = section.querySelector("[data-pdf-trace-form]");
    var submit = section.querySelector("[data-pdf-trace-submit]");
    if (!layer || !box || !form) {
      return;
    }

    var emptyLabel = workbench.getAttribute("data-pdf-trace-empty-label") || "Zone a selectionner";
    var readyLabel = workbench.getAttribute("data-pdf-trace-ready-label") || "Zone selectionnee page 1";
    var start = null;
    setSubmitEnabled(submit, false);
    setStatus(section, emptyLabel);

    function draw(current) {
      if (!start || !current.width || !current.height) {
        return;
      }
      var left = Math.min(start.x, current.x);
      var top = Math.min(start.y, current.y);
      var width = Math.abs(current.x - start.x);
      var height = Math.abs(current.y - start.y);
      box.hidden = false;
      box.style.left = left + "px";
      box.style.top = top + "px";
      box.style.width = width + "px";
      box.style.height = height + "px";
    }

    function commit(current) {
      if (!start || !current.width || !current.height) {
        return;
      }
      var left = Math.min(start.x, current.x);
      var top = Math.min(start.y, current.y);
      var width = Math.abs(current.x - start.x);
      var height = Math.abs(current.y - start.y);
      if (width < MIN_SIZE_PX || height < MIN_SIZE_PX) {
        field(form, "x").value = "";
        field(form, "y").value = "";
        field(form, "width").value = "";
        field(form, "height").value = "";
        box.hidden = true;
        setSubmitEnabled(submit, false);
        setStatus(section, emptyLabel);
        return;
      }
      field(form, "page").value = "1";
      field(form, "x").value = formatUnit(left / current.width);
      field(form, "y").value = formatUnit(top / current.height);
      field(form, "width").value = formatUnit(width / current.width);
      field(form, "height").value = formatUnit(height / current.height);
      setSubmitEnabled(submit, true);
      setStatus(section, readyLabel);
    }

    layer.addEventListener("pointerdown", function (event) {
      if (event.button !== undefined && event.button !== 0) {
        return;
      }
      event.preventDefault();
      start = pointInLayer(layer, event);
      if (layer.setPointerCapture) {
        layer.setPointerCapture(event.pointerId);
      }
      draw(start);
    });

    layer.addEventListener("pointermove", function (event) {
      if (!start) {
        return;
      }
      event.preventDefault();
      draw(pointInLayer(layer, event));
    });

    layer.addEventListener("pointerup", function (event) {
      if (!start) {
        return;
      }
      event.preventDefault();
      commit(pointInLayer(layer, event));
      start = null;
    });

    layer.addEventListener("pointercancel", function () {
      start = null;
    });

    layer.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") {
        return;
      }
      field(form, "x").value = "";
      field(form, "y").value = "";
      field(form, "width").value = "";
      field(form, "height").value = "";
      box.hidden = true;
      setSubmitEnabled(submit, false);
      setStatus(section, emptyLabel);
    });
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-pdf-trace-workbench]"),
    wireWorkbench
  );
}());
