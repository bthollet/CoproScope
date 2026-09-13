/*
 * Eprouve la lecture par obligation legale, hors navigateur.
 *
 * Deux implantations de la meme regle divergent toujours. Ici la divergence
 * serait particulierement couteuse: le plugin annoncerait un manque que
 * CoproScope ne verrait pas, ou l'inverse, et c'est sur ce genre de constat
 * qu'un conseil syndical ecrit a son syndic.
 *
 * Usage: node executer-conformite.mjs <scenarios.json>
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const ICI = dirname(fileURLToPath(import.meta.url));
const SOURCE = join(ICI, "..");

function charger() {
  const boite = {};
  const contexte = vm.createContext({
    console, Set, Map, Math, String, Number, JSON, Object, Array, Promise,
    Date, Error,
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
  /* Meme ordre que le manifeste: la cle, puis le referentiel, puis la veille
   * qui les emploie. Un ordre different ferait echouer le harnais la ou le
   * navigateur, lui, fonctionnerait - ou l'inverse, ce qui serait pire. */
  for (const nom of ["cle.js", "referentiel.js", "veille.js"]) {
    vm.runInContext(readFileSync(join(SOURCE, nom), "utf8"), contexte, {
      filename: nom,
    });
  }
  return contexte;
}

const scenarios = JSON.parse(readFileSync(process.argv[2], "utf8"));
const contexte = charger();
const manquesLegaux = vm.runInContext("CS_VEILLE.manquesLegaux", contexte);
const manquantes = vm.runInContext("CS_VEILLE.manquantes", contexte);
const obligations = vm.runInContext("CS_REFERENTIEL.OBLIGATIONS", contexte);

const sortie = {
  /* La liste elle-meme voyage, pour que le test Python la compare a la sienne
   * entree par entree plutot que de faire confiance a deux comptages. */
  obligations: obligations.map((o) => ({
    id: o.id,
    college: o.college,
    intitule: o.intitule,
    fondement: o.fondement,
    attendu_source: o.attendu_source,
    attendu: o.attendu === undefined ? null : o.attendu,
    recouvre: o.recouvre || [],
  })),
  scenarios: {},
};

for (const [nom, s] of Object.entries(scenarios)) {
  const etats = manquesLegaux(s.releve, s.rattachements, s.attendus, s.sans_objet);
  sortie.scenarios[nom] = {
    etats,
    manques: manquantes(etats).map((e) => e.id),
  };
}

process.stdout.write(JSON.stringify(sortie, null, 1));
