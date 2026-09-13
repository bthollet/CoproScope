/*
 * Eprouve la comparaison de la veille, hors navigateur.
 *
 * `veille.js` decide ce qui compte comme changement. C'est le module le plus
 * exposé du plugin: son resultat s'affiche sur l'icone, et un nombre affiche a
 * tort est une fausse alerte sur le constat le plus accusatoire de l'outil.
 *
 * Usage: node executer-veille.mjs <scenarios.json>
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const ICI = dirname(fileURLToPath(import.meta.url));
const SOURCE = join(ICI, "..");

function chargerVeille() {
  const boite = {};
  const contexte = vm.createContext({
    console,
    Set,
    Map,
    Math,
    String,
    Number,
    JSON,
    Object,
    Array,
    Promise,
    Date,
    Error,
    chrome: {
      storage: {
        local: {
          get: async (cles) => {
            if (cles === null || cles === undefined) return { ...boite };
            const liste = Array.isArray(cles) ? cles : [cles];
            const sortie = {};
            for (const c of liste) if (c in boite) sortie[c] = boite[c];
            return sortie;
          },
          set: async (valeurs) => {
            Object.assign(boite, valeurs);
          },
          remove: async (cles) => {
            for (const c of Array.isArray(cles) ? cles : [cles]) delete boite[c];
          },
        },
      },
    },
  });
  /* `cle.js` d'abord: il porte la construction de cle dont les autres
   * dependent, et le manifeste le charge lui aussi en premier. */
  vm.runInContext(readFileSync(join(SOURCE, "cle.js"), "utf8"), contexte, {
    filename: "cle.js",
  });
  vm.runInContext(readFileSync(join(SOURCE, "referentiel.js"), "utf8"), contexte, {
    filename: "referentiel.js",
  });
  vm.runInContext(readFileSync(join(SOURCE, "veille.js"), "utf8"), contexte, {
    filename: "veille.js",
  });
  return contexte;
}

const scenarios = JSON.parse(readFileSync(process.argv[2], "utf8"));
const contexte = chargerVeille();
const comparer = vm.runInContext("CS_VEILLE.comparer", contexte);
const manques = vm.runInContext("CS_VEILLE.manques", contexte);
const sortie = {};

for (const [nom, s] of Object.entries(scenarios)) {
  if (s.attendus !== undefined) {
    sortie[nom] = { manques: manques(s.releve, s.attendus) };
    continue;
  }
  const ecart = comparer(s.avant, s.apres);
  sortie[nom] = {
    parus: ecart.parus.length,
    disparus: ecart.disparus.length,
    hors_comparaison: ecart.hors_comparaison,
  };
}

process.stdout.write(JSON.stringify(sortie, null, 1));
