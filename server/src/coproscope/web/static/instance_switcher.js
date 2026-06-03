(function () {
  "use strict";

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  onReady(function () {
    var button = document.getElementById("cs-instance-switcher-button");
    var status = document.getElementById("cs-instance-switcher-status");

    if (!button) {
      return;
    }

    var style = document.createElement("style");
    style.textContent = [
      ".instance-switch-button{border:1px solid currentColor;border-radius:999px;background:#fff;padding:.35rem .65rem;cursor:pointer;font:inherit}",
      ".instance-switch-button:disabled{opacity:.55;cursor:not-allowed}",
      ".instance-switch-status{font-size:.85em;opacity:.8;margin-left:.35rem}"
    ].join("");
    document.head.appendChild(style);

    function setStatus(message) {
      if (status) {
        status.textContent = message || "";
      }
    }

    function switchApi() {
      if (
        window.pywebview &&
        window.pywebview.api &&
        typeof window.pywebview.api.choose_instance_root === "function"
      ) {
        return window.pywebview.api;
      }
      return null;
    }

    var attempts = 0;

    function refreshAvailability() {
      if (switchApi()) {
        button.disabled = false;
        button.title = "Choisir un autre dossier d'instance CoproScope";
        setStatus("");
        return;
      }

      attempts += 1;
      button.disabled = true;
      button.title = "Disponible dans la fenêtre CoproScope";

      if (attempts < 40) {
        window.setTimeout(refreshAvailability, 250);
      } else {
        setStatus("Disponible dans la fenêtre CoproScope.");
      }
    }

    button.addEventListener("click", function () {
      var api = switchApi();

      if (!api) {
        setStatus("Ouvre l'exe en mode fenêtre pour changer de coffre.");
        return;
      }

      button.disabled = true;
      setStatus("Choix du dossier...");

      Promise.resolve(api.choose_instance_root())
        .then(function (result) {
          if (!result || !result.ok) {
            button.disabled = false;
            setStatus((result && result.message) || "Changement annulé.");
            return;
          }
          setStatus(result.message || "Redémarrage sur le coffre choisi...");
        })
        .catch(function () {
          button.disabled = false;
          setStatus("Changement de coffre impossible depuis cette fenêtre.");
        });
    });

    refreshAvailability();
  });
}());
