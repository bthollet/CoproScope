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

  function toggleAdjustHelp(section, visible) {
    Array.prototype.forEach.call(
      section.querySelectorAll("[data-pdf-trace-adjust-help]"),
      function (node) {
        node.hidden = !visible;
      }
    );
    Array.prototype.forEach.call(
      section.querySelectorAll("[data-pdf-trace-fallback-help]"),
      function (node) {
        node.hidden = visible;
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

  function unitFrom(value) {
    var parsed = parseFloat(value);
    return Number.isFinite(parsed) ? Math.max(0, Math.min(1, parsed)) : null;
  }

  function setSubmitEnabled(button, enabled) {
    if (!button) {
      return;
    }
    button.disabled = !enabled;
    button.setAttribute("aria-disabled", enabled ? "false" : "true");
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function orderedRect(left, top, right, bottom) {
    return {
      left: Math.min(left, right),
      top: Math.min(top, bottom),
      right: Math.max(left, right),
      bottom: Math.max(top, bottom)
    };
  }

  function rectFromPoints(start, current) {
    return orderedRect(start.x, start.y, current.x, current.y);
  }

  function rectSize(rect) {
    return {
      width: Math.max(0, rect.right - rect.left),
      height: Math.max(0, rect.bottom - rect.top)
    };
  }

  function isUsableRect(rect) {
    var size = rectSize(rect);
    return size.width >= MIN_SIZE_PX && size.height >= MIN_SIZE_PX;
  }

  function boundedResizeRect(original, handle, point, layerWidth, layerHeight) {
    var left = original.left;
    var top = original.top;
    var right = original.right;
    var bottom = original.bottom;
    var x = clamp(point.x, 0, layerWidth);
    var y = clamp(point.y, 0, layerHeight);

    if (handle.indexOf("w") !== -1) {
      left = clamp(x, 0, right - MIN_SIZE_PX);
    }
    if (handle.indexOf("e") !== -1) {
      right = clamp(x, left + MIN_SIZE_PX, layerWidth);
    }
    if (handle.indexOf("n") !== -1) {
      top = clamp(y, 0, bottom - MIN_SIZE_PX);
    }
    if (handle.indexOf("s") !== -1) {
      bottom = clamp(y, top + MIN_SIZE_PX, layerHeight);
    }
    return orderedRect(left, top, right, bottom);
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
    var readyLabel = workbench.getAttribute("data-pdf-trace-ready-label") || "Zone ajustable sur la page 1";
    var pageCount = numberFrom(workbench.getAttribute("data-pdf-trace-page-count"), 1);
    var currentPage = numberFrom(workbench.getAttribute("data-pdf-trace-current-page"), 1);
    var pageInput = section.querySelector("[data-pdf-trace-page-input]");
    var pagePrev = section.querySelector("[data-pdf-trace-page-prev]");
    var pageNext = section.querySelector("[data-pdf-trace-page-next]");
    var pageStatus = section.querySelector("[data-pdf-trace-page-status]");
    var pdfObject = section.querySelector("[data-pdf-trace-pdf-object]");
    var resumeSelection = {
      page: numberFrom(workbench.getAttribute("data-pdf-trace-resume-page"), 0),
      x: unitFrom(workbench.getAttribute("data-pdf-trace-resume-x")),
      y: unitFrom(workbench.getAttribute("data-pdf-trace-resume-y")),
      width: unitFrom(workbench.getAttribute("data-pdf-trace-resume-width")),
      height: unitFrom(workbench.getAttribute("data-pdf-trace-resume-height")),
      label: workbench.getAttribute("data-pdf-trace-resume-label") || ""
    };
    var replayLinks = document.querySelectorAll("[data-pdf-trace-replay]");
    var drag = null;
    var selection = null;

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
      selection = null;
      drag = null;
      box.hidden = true;
      setSubmitEnabled(submit, false);
      toggleAdjustHelp(section, false);
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

    function renderSelection(rect) {
      var size = rectSize(rect);
      box.hidden = false;
      box.style.left = rect.left + "px";
      box.style.top = rect.top + "px";
      box.style.width = size.width + "px";
      box.style.height = size.height + "px";
    }

    function syncFields(rect, layerWidth, layerHeight) {
      if (!layerWidth || !layerHeight || !isUsableRect(rect)) {
        setSubmitEnabled(submit, false);
        toggleAdjustHelp(section, false);
        return;
      }
      var size = rectSize(rect);
      field(form, "page").value = String(currentPage);
      field(form, "x").value = formatUnit(rect.left / layerWidth);
      field(form, "y").value = formatUnit(rect.top / layerHeight);
      field(form, "width").value = formatUnit(size.width / layerWidth);
      field(form, "height").value = formatUnit(size.height / layerHeight);
      setSubmitEnabled(submit, true);
      toggleAdjustHelp(section, true);
      setStatus(section, readyForPage());
    }

    function applySavedTrace(trigger, updateUrl) {
      var x = unitFrom(trigger.getAttribute("data-pdf-trace-x"));
      var y = unitFrom(trigger.getAttribute("data-pdf-trace-y"));
      var width = unitFrom(trigger.getAttribute("data-pdf-trace-width"));
      var height = unitFrom(trigger.getAttribute("data-pdf-trace-height"));
      if (x === null || y === null || width === null || height === null || !width || !height) {
        return;
      }
      setCurrentPage(trigger.getAttribute("data-pdf-trace-page"));
      var bounds = layer.getBoundingClientRect();
      if (!bounds.width || !bounds.height) {
        return;
      }
      var rect = orderedRect(
        x * bounds.width,
        y * bounds.height,
        (x + width) * bounds.width,
        (y + height) * bounds.height
      );
      previewRect(rect, { width: bounds.width, height: bounds.height });
      setSubmitEnabled(submit, false);
      toggleAdjustHelp(section, false);
      setStatus(section, trigger.getAttribute("data-pdf-trace-label") || "Zone enregistree a verifier sur la page " + currentPage);
      if (updateUrl && window.history && trigger.href) {
        window.history.replaceState(null, "", trigger.href);
      }
    }

    function restoreSavedSelection() {
      if (
        !resumeSelection.page ||
        resumeSelection.page !== currentPage ||
        resumeSelection.x === null ||
        resumeSelection.y === null ||
        resumeSelection.width === null ||
        resumeSelection.height === null ||
        !resumeSelection.width ||
        !resumeSelection.height
      ) {
        return;
      }
      var bounds = layer.getBoundingClientRect();
      if (!bounds.width || !bounds.height) {
        return;
      }
      var rect = orderedRect(
        resumeSelection.x * bounds.width,
        resumeSelection.y * bounds.height,
        (resumeSelection.x + resumeSelection.width) * bounds.width,
        (resumeSelection.y + resumeSelection.height) * bounds.height
      );
      previewRect(rect, { width: bounds.width, height: bounds.height });
      setSubmitEnabled(submit, false);
      toggleAdjustHelp(section, false);
      setStatus(section, resumeSelection.label || "Point de reprise ouvert");
    }

    function previewRect(rect, current) {
      if (!current.width || !current.height) {
        return;
      }
      selection = rect;
      renderSelection(rect);
      syncFields(rect, current.width, current.height);
    }

    function commitRect(rect, current) {
      if (!current.width || !current.height || !isUsableRect(rect)) {
        resetSelection("Zone trop petite : recommencez la selection");
        return;
      }
      previewRect(rect, current);
    }

    function handleFromEvent(event) {
      if (!event.target || !event.target.closest) {
        return null;
      }
      return event.target.closest("[data-pdf-trace-handle]");
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

    Array.prototype.forEach.call(replayLinks, function (link) {
      link.addEventListener("click", function (event) {
        event.preventDefault();
        applySavedTrace(link, true);
        layer.focus();
      });
    });

    layer.addEventListener("pointerdown", function (event) {
      if (event.button !== undefined && event.button !== 0) {
        return;
      }
      event.preventDefault();
      var handle = handleFromEvent(event);
      var point = pointInLayer(layer, event);
      if (layer.setPointerCapture) {
        layer.setPointerCapture(event.pointerId);
      }
      if (handle && selection) {
        drag = {
          kind: "resize",
          handle: handle.getAttribute("data-pdf-trace-handle"),
          rect: {
            left: selection.left,
            top: selection.top,
            right: selection.right,
            bottom: selection.bottom
          }
        };
        return;
      }
      drag = {
        kind: "draw",
        start: point
      };
      previewRect(rectFromPoints(point, point), point);
    });

    layer.addEventListener("pointermove", function (event) {
      if (!drag) {
        return;
      }
      event.preventDefault();
      var current = pointInLayer(layer, event);
      if (drag.kind === "resize") {
        previewRect(boundedResizeRect(drag.rect, drag.handle, current, current.width, current.height), current);
      } else {
        previewRect(rectFromPoints(drag.start, current), current);
      }
    });

    layer.addEventListener("pointerup", function (event) {
      if (!drag) {
        return;
      }
      event.preventDefault();
      var current = pointInLayer(layer, event);
      if (drag.kind === "resize") {
        commitRect(boundedResizeRect(drag.rect, drag.handle, current, current.width, current.height), current);
      } else {
        commitRect(rectFromPoints(drag.start, current), current);
      }
      drag = null;
    });

    layer.addEventListener("pointercancel", function () {
      drag = null;
    });

    layer.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") {
        return;
      }
      resetSelection(emptyForPage());
    });

    if (resumeSelection.page) {
      if (window.requestAnimationFrame) {
        window.requestAnimationFrame(restoreSavedSelection);
      } else {
        window.setTimeout(restoreSavedSelection, 0);
      }
      window.setTimeout(restoreSavedSelection, 120);
    } else if (window.URLSearchParams) {
      var requested = new URLSearchParams(window.location.search).get("trace_id");
      Array.prototype.some.call(replayLinks, function (link) {
        if (requested && link.getAttribute("data-pdf-trace-id") === requested) {
          window.setTimeout(function () {
            applySavedTrace(link, false);
          }, 0);
          return true;
        }
        return false;
      });
    }
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-pdf-trace-workbench]"),
    wireWorkbench
  );
}());
