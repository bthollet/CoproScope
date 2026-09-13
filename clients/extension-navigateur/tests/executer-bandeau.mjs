/*
 * Eprouve le bandeau pose dans la page, hors navigateur.
 *
 * Ce harnais existe a cause d'un defaut trouve le 2026-09-07: le code du
 * bandeau n'avait **jamais** ete execute sous test. `mini-dom.mjs` ne rendait
 * ni `body`, ni `createElement`, ni `attachShadow`, de sorte que
 * `poserBandeau` sortait a chaque fois par sa propre garde - celle qui est la
 * pour proteger la production, et qui masquait donc l'absence de couverture.
 *
 * Un bandeau qui echouerait en silence est le pire cas: c'est la seule surface
 * que l'utilisateur voit sans ouvrir la fenetre du plugin.
 *
 * Usage: node executer-bandeau.mjs <scenarios.json>
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

import { fabriquerDocument } from "./mini-dom.mjs";

const ICI = dirname(fileURLToPath(import.meta.url));
const SOURCE = join(ICI, "..");

/* Charge les quatre scripts de contenu dans l'ordre du manifeste, avec un
 * stockage prealablement garni: la veille lit ses reglages au chargement, et
 * c'est elle qui decide de poser le bandeau. */
async function poser(html, chemin, reglages, effacer) {
  const document = fabriquerDocument(html);
  const boite = { veille_reglages: reglages };
  const contexte = vm.createContext({
    document,
    location: { pathname: chemin },
    console, TextEncoder, crypto, Date, Set, Map, JSON, Math, String, Number,
    Array, Object, Promise, RegExp, Error, decodeURIComponent,
    fetch: async () => ({ headers: { get: () => null } }),
    chrome: {
      runtime: {
        sendMessage: async () => {},
        onMessage: { addListener: () => {} },
      },
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

  for (const nom of ["cle.js", "referentiel.js", "veille.js", "lecteur.js"]) {
    vm.runInContext(readFileSync(join(SOURCE, nom), "utf8"), contexte, {
      filename: nom,
    });
  }

  /* `veiller()` est lance au chargement et il est asynchrone. On laisse la
   * file de micro-taches se vider avant de regarder la page. */
  for (let i = 0; i < 40; i += 1) await Promise.resolve();
  await new Promise((r) => setTimeout(r, 0));
  for (let i = 0; i < 40; i += 1) await Promise.resolve();

  const hote = document.getElementById("cs-bandeau");
  /* L'etat du stockage AVANT tout effacement: sans lui, un test qui verifie
   * qu'un nom a disparu ne prouve pas qu'il y etait. */
  const avant = JSON.stringify(boite);

  let apresEffacement = null;
  if (effacer) {
    const CS_VEILLE = vm.runInContext("CS_VEILLE", contexte);
    await CS_VEILLE.effacerReleves();
    apresEffacement = JSON.stringify(boite);
  }

  return {
    apres_effacement: apresEffacement,
    /* Tout ce que la veille a effectivement ECRIT sur le disque du navigateur.
     * C'est la seule mesure qui compte pour le biffage: ce qui n'est pas
     * stocke ne peut pas fuiter. */
    stockage: avant,
    /* `null` veut dire *aucun bandeau pose*, ce qui est un resultat attendu
     * quand il n'y a rien a annoncer - et non une panne du harnais. */
    presence: !!hote,
    texte: hote ? hote.texteProfond : "",
    /* Un seul noeud ajoute au corps: un bandeau qui s'empilerait a chaque
     * passage rendrait la page inutilisable au bout de quelques visites. */
    noeuds_ajoutes: document.body.enfants.length,
    /* L'ombre est fermee: la page hote ne doit pas pouvoir lire ni styler ce
     * que le plugin affiche. */
    ombre: hote ? !!hote.shadow : false,
  };
}

const scenarios = JSON.parse(readFileSync(process.argv[2], "utf8"));
const sortie = {};
for (const [nom, s] of Object.entries(scenarios)) {
  sortie[nom] = await poser(
    s.html,
    s.chemin || "/espace-copropriete/documents",
    s.reglages || {},
    !!s.effacer
  );
}
process.stdout.write(JSON.stringify(sortie, null, 1));
