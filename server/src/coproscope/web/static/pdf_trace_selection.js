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

  function formatLabel(template, page) {
    return String(template || "").replace("{page}", String(page));
  }

  function numberFrom(value, fallback) {
    var parsed = parseInt(value, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
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
    var readyLabel = workbench.getAttribute("data-pdf-trace-ready-label") || "Zone selectionnee sur la page 1";
    var pageCount = numberFrom(workbench.getAttribute("data-pdf-trace-page-count"), 1);
    var currentPage = numberFrom(workbench.getAttribute("data-pdf-trace-current-page"), 1);
    var pageInput = section.querySelector("[data-pdf-trace-page-input]");
    var pagePrev = section.querySelector("[data-pdf-trace-page-prev]");
    var pageNext = section.querySelector("[data-pdf-trace-page-next]");
    var pageStatus = section.querySelector("[data-pdf-trace-page-status]");
    var pdfObject = section.querySelector("[data-pdf-trace-pdf-object]");
    var start = null;

    function emptyForPage() {
      return formatLabel(emptyLabel, currentPage);
    }

    function readyForPage() {
      return formatLabel(readyLabel, currentPage);
    }

    function updatePdfObject() {
      if (!pdfObject) {
        return;
      }
      var base = pdfObject.getAttribute("data-pdf-trace-pdf-src") || pdfObject.getAttribute("data") || "";
      pdfObject.setAttribute("data", base.split("#")[0] + "#page=" + currentPage);
    }

    function resetSelection(message) {
      field(form, "x").value = "";
      field(form, "y").value = "";
      field(form, "width").value = "";
      field(form, "height").value = "";
      box.hidden = true;
      setSubmitEnabled(submit, false);
      setStatus(section, message || emptyForPage());
    }

    function setCurrentPage(nextPage) {
      currentPage = Math.max(1, Math.min(pageCount, numberFrom(nextPage, currentPage)));
      field(form, "page").value = String(currentPage);
      if (pageInput) {
        pageInput.value = String(currentPage);
      }
      if (pagePrev) {
        pagePrev.disabled = currentPage <= 1;
      }
      if (pageNext) {
        pageNext.disabled = currentPage >= pageCount;
      }
      if (pageStatus) {
        pageStatus.textContent = "Page " + currentPage + " sur " + pageCount;
      }
      updatePdfObject();
      resetSelection(emptyForPage());
    }

    setSubmitEnabled(submit, false);
    setCurrentPage(currentPage);

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
        resetSelection(emptyForPage());
        return;
      }
      field(form, "page").value = String(currentPage);
      field(form, "x").value = formatUnit(left / current.width);
      field(form, "y").value = formatUnit(top / current.height);
      field(form, "width").value = formatUnit(width / current.width);
      field(form, "height").value = formatUnit(height / current.height);
      setSubmitEnabled(submit, true);
      setStatus(section, readyForPage());
    }

    if (pagePrev) {
      pagePrev.addEventListener("click", function () {
        setCurrentPage(currentPage - 1);
      });
    }

    if (pageNext) {
      pageNext.addEventListener("click", function () {
        setCurrentPage(currentPage + 1);
      });
    }

    if (pageInput) {
      pageInput.addEventListener("change", function () {
        setCurrentPage(pageInput.value);
      });
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
      resetSelection(emptyForPage());
    });
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-pdf-trace-workbench]"),
    wireWorkbench
  );
}());
