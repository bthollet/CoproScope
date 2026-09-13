/*
 * Eprouve la sonde de session, hors navigateur.
 *
 * La sonde est le seul composant qui parle au serveur du syndic sans que
 * personne regarde. Son jugement doit donc etre eprouvable sans navigateur, et
 * c'est pour cela que `juger`, `fusionner` et `diagnostic` sont des fonctions
 * pures: la seule chose qui reste non testable ici est la requete elle-meme.
 *
 * Usage: node executer-sonde.mjs <scenarios.json>
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const ICI = dirname(fileURLToPath(import.meta.url));
const SOURCE = join(ICI, "..");

const contexte = vm.createContext({
  console, Set, Map, Math, String, Number, JSON, Object, Array, Promise, Date,
  Error, URL, globalThis: {},
});
vm.runInContext(readFileSync(join(SOURCE, "sonde.js"), "utf8"), contexte, {
  filename: "sonde.js",
});
const S = vm.runInContext("CS_SONDE", contexte);

const scenarios = JSON.parse(readFileSync(process.argv[2], "utf8"));
const sortie = {};

for (const [nom, s] of Object.entries(scenarios)) {
  if (s.reponses) {
    /* Une suite de reponses successives, pour eprouver ce que devient l'etat
     * au fil des passages: c'est la que se joue la garde numero 2, la
     * distinction entre la derniere tentative et le dernier succes. */
    let etat = null;
    const etapes = [];
    for (const r of s.reponses) {
      const tentative = await S.sonder(
        s.url || "https://coprodirecte.fr/espace-copropriete/documents",
        s.ancre === undefined ? "id=\"documents\"" : s.ancre,
        r.quand,
        async () => ({
          status: r.statut,
          text: async () => r.corps || "",
        })
      );
      etat = S.fusionner(etat, tentative);
      etapes.push({
        etat: tentative.etat,
        motif: tentative.motif || null,
        derniere_tentative: etat.derniere_tentative.quand,
        dernier_succes: etat.dernier_succes ? etat.dernier_succes.quand : null,
        echecs_consecutifs: etat.echecs_consecutifs,
        diagnostic: S.diagnostic(etat, Date.parse(r.maintenant || r.quand)),
      });
    }
    sortie[nom] = { etapes, etat_final: etat };
    continue;
  }
  if (s.compter_requetes !== undefined) {
    /* Combien de requetes partent REELLEMENT vers le syndic. Une garde qui
     * decide apres avoir emis ne protege de rien. */
    let emises = 0;
    const t = await S.sonder(
      s.url || "https://inconnu.example/espace",
      s.ancre === undefined ? "" : s.ancre,
      s.quand || "2026-09-07T09:00:00Z",
      async () => {
        emises += 1;
        return { status: 200, text: async () => "" };
      }
    );
    sortie[nom] = { requetes_emises: emises, etat: t.etat, motif: t.motif || null };
    continue;
  }
  if (s.erreur) {
    const t = await S.sonder(s.url || "https://x/y", "ancre", s.quand, async () => {
      throw new Error(s.erreur);
    });
    sortie[nom] = t;
    continue;
  }
  sortie[nom] = S.juger(s.statut, s.corps, s.ancre);
}

process.stdout.write(JSON.stringify(sortie, null, 1));
