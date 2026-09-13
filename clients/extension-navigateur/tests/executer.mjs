/*
 * Execute le JavaScript du plugin sur des gabarits, et rend le resultat.
 *
 * Appele par `server/tests/test_extension_javascript.py`, qui compare ce que
 * rend le lecteur JS a ce que rend le lecteur Python sur les MEMES gabarits.
 * C'est cette comparaison qui protege du risque repete tout au long du lot:
 * deux implantations de la meme logique divergent toujours, et la divergence
 * se voit le jour ou l'on en a le plus besoin.
 *
 * Usage: node executer.mjs <fichier-de-gabarits.json>
 * Rend sur la sortie standard un JSON: { <nom du gabarit>: <releve>, ... }
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

import { fabriquerDocument } from "./mini-dom.mjs";

const ICI = dirname(fileURLToPath(import.meta.url));
const SOURCE = join(ICI, "..");

/* Le lecteur s'enregistre aupres de `chrome.runtime.onMessage`. On lui fournit
 * juste de quoi le faire, et on capture la fonction pour l'appeler nous-memes:
 * on eprouve ainsi le chemin reel, celui qu'emprunte la fenetre du plugin. */
function executerLecteur(html, chemin, noms) {
  const document = fabriquerDocument(html);
  let ecouteur = null;
  const contexte = vm.createContext({
    document,
    location: { pathname: chemin },
    console,
    TextEncoder,
    crypto,
    Date,
    Set,
    Map,
    JSON,
    Math,
    String,
    Number,
    Array,
    Object,
    Promise,
    RegExp,
    Error,
    /* Le nom servi par le serveur arrive par une requete HEAD. Ici, il est
     * fourni par le gabarit: on eprouve ce que le lecteur FAIT du nom, pas la
     * capacite de Node a parler HTTP. */
    fetch: async (url) => ({
      headers: {
        get: (nom) =>
          nom.toLowerCase() === "content-disposition" && noms[url]
            ? `attachment; filename="${noms[url]}"`
            : null,
      },
    }),
    decodeURIComponent,
    /* Un stockage en memoire: la veille continue ecrit dedans au chargement de
     * la page, et on veut que ce chemin s'execute lui aussi sous test. */
    chrome: {
      runtime: { onMessage: { addListener: (f) => { ecouteur = f; }, }, sendMessage: async () => ({}) },
      storage: (() => {
        const boite = {};
        return {
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
          },
        };
      })(),
    },
  });

  /* `veille.js` est charge AVANT le lecteur, comme dans le manifeste: les deux
   * scripts de contenu partagent le meme monde isole. */
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
  vm.runInContext(readFileSync(join(SOURCE, "lecteur.js"), "utf8"), contexte, {
    filename: "lecteur.js",
  });
  if (!ecouteur) throw new Error("lecteur.js n'a enregistre aucun ecouteur");

  return new Promise((resoudre, rejeter) => {
    const rendu = ecouteur(
      { action: "observer", avecNoms: Object.keys(noms).length > 0 },
      null,
      (r) => (r.ok ? resoudre(r.charge) : rejeter(new Error(r.erreur)))
    );
    if (!rendu) rejeter(new Error("l'ecouteur n'a pas pris la main"));
  });
}

/* `journal.js` declare ses fonctions au premier niveau: on l'evalue dans un
 * contexte et on recupere ce qui nous interesse. */
function chargerJournal() {
  const contexte = vm.createContext({ TextEncoder, crypto, console, Set, Map, Math, String, JSON, Object, Array, Promise, Error });
  /* `cle.js` d'abord: il porte la construction de cle dont les autres
   * dependent, et le manifeste le charge lui aussi en premier. */
  vm.runInContext(readFileSync(join(SOURCE, "cle.js"), "utf8"), contexte, {
    filename: "cle.js",
  });
  vm.runInContext(readFileSync(join(SOURCE, "journal.js"), "utf8"), contexte, {
    filename: "journal.js",
  });
  return contexte;
}

const gabarits = JSON.parse(readFileSync(process.argv[2], "utf8"));
const journal = chargerJournal();
const sortie = {};

for (const [nom, g] of Object.entries(gabarits)) {
  const releve = await executerLecteur(g.html, g.chemin || "/espace-copropriete/documents", g.noms || {});
  const construit = vm.runInContext("construireJournal", journal)(releve);
  const paquet = g.sel
    ? await vm.runInContext("construireExport", journal)(releve, g.sel, "test")
    : null;
  sortie[nom] = {
    type: releve.type,
    pagination: releve.pagination,
    cloture: construit.cloture,
    rubriques_parcourues: construit.rubriques_parcourues,
    non_explorees: construit.rubriques_non_explorees,
    noms: construit.noms,
    /* Le releve NEUTRE, tel que le plugin le transmet. C'est lui que le test
     * de conformite fait passer dans la chaine Python, pour comparer ce que
     * les deux implantations produisent au bout - et non deux mises en forme
     * differentes, ce qui ne prouverait rien. */
    releve_brut: releve,
    pieces: releve.rubriques
      .filter((r) => r.presente)
      .flatMap((r) =>
        (r.pieces || (r.lignes || []).filter((l) => l.a_une_facture)).map((p) => ({
          rubrique: r.rubrique_code,
          groupe: p.groupe ?? (p.colonnes || [])[0] ?? "",
          libelle: p.libelle ?? (p.colonnes || []).slice(1).join(" | "),
          nom_serveur: p.nom_serveur || "",
        }))
      ),
    lignes_par_cle: releve.rubriques
      .filter((r) => r.lignes)
      .map((r) => [r.rubrique_code, r.lignes.length]),
    export: paquet
      ? {
          temoin_sel: paquet.temoin_sel,
          empreintes: paquet.pieces.map((p) => p.emp_emplacement),
          noms_empreintes: paquet.pieces.map((p) => p.emp_nom),
        }
      : null,
  };
}

process.stdout.write(JSON.stringify(sortie, null, 1));
