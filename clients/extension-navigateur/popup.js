/*
 * La fenetre du plugin: l'etat de la veille, et les gestes manuels.
 *
 * La surveillance continue a ete demandee par Brice le 2026-09-06. Elle est
 * dans sa regle: la ligne rouge autorise sans clic parcourir, empreindre,
 * telecharger, journaliser et alerter, et n'exige un geste humain que pour ce
 * qui **sort vers le syndic**. Rien ici n'en sort.
 *
 * Ce qui reste manuel, et le restera: l'export destine a un voisin. Un fichier
 * qui quitte la machine part sur decision, jamais sur minuterie.
 */

"use strict";

const $ = (id) => document.getElementById(id);
let dernierReleve = null;

function dire(message, classe) {
  const etat = $("etat");
  etat.textContent = message;
  etat.className = "etat" + (classe ? " " + classe : "");
}

/* `chrome.tabs` est employe SANS que la permission `tabs` soit declaree, et
 * c'est deliberé. En MV3, `tabs.query`, `tabs.sendMessage` et la lecture de
 * `tab.url` fonctionnent sur les onglets couverts par `host_permissions` - ici
 * le seul domaine du syndic. Declarer `tabs` donnerait en plus l'acces au titre
 * et a l'adresse de TOUS les onglets ouverts, ce dont le plugin n'a aucun
 * besoin.
 *
 * Demander un acces inutile est precisement le defaut qui a motive la creation
 * de `test_extension_plomberie.py`, et c'est la premiere chose qu'un
 * utilisateur prudent regarde. */
async function ongletCourant() {
  const onglets = await chrome.tabs.query({ active: true, currentWindow: true });
  return onglets[0];
}

function resume(journal) {
  if (journal.type === "depenses") {
    let lignes = 0;
    journal.rubriques.forEach((r) => (lignes += (r.lignes || []).length));
    return lignes + " lignes, " + journal.noms.pieces + " avec facture";
  }
  return journal.noms.pieces + " pieces, " + journal.rubriques_parcourues + " rubriques";
}

function montrerNoms(journal) {
  const n = journal.noms;
  const zone = $("noms");
  const lignes = [];
  /* Le cas trouve a la premiere utilisation reelle: un releve lance depuis une
   * page qui ne porte aucun index. Le dire vaut mieux que rendre un journal
   * sans matiere que l'utilisateur croira complet. */
  if (journal.type === "aucun") {
    lignes.push("Cette page ne porte aucun index.");
    lignes.push("Allez sur La copropriete puis Documents, ou sur Depenses.");
  } else {
    lignes.push(`Noms de fichiers releves: ${n.avec_nom} sur ${n.pieces} (${n.couverture} %)`);
    lignes.push(`Noms distincts: ${n.noms_distincts}`);
    if (n.collisions) {
      lignes.push(`Collisions: ${n.collisions} - le nom ne distingue plus toutes les pieces.`);
    } else if (n.avec_nom) {
      lignes.push("Aucune collision: chaque piece a un nom propre.");
    }
    if (journal.cloture === "AUCUNE") {
      lignes.push("Liste peut-etre incomplete: aucune absence ne sera affirmable.");
    }
    if ((journal.rubriques_non_explorees || []).length) {
      lignes.push("Non parcourues: " + journal.rubriques_non_explorees.join(", "));
    }
  }
  zone.textContent = lignes.join("\n");
  zone.hidden = false;
  zone.className = "noms" + (n.collisions || journal.type === "aucun" ? " alerte" : "");
}

async function telecharger(objet, nom) {
  const url =
    "data:application/json;charset=utf-8," +
    encodeURIComponent(JSON.stringify(objet, null, 1));
  await chrome.downloads.download({ url, filename: nom, saveAs: false });
}

async function relever() {
  const onglet = await ongletCourant();
  if (!onglet || !/coprodirecte\.fr/.test(onglet.url || "")) {
    dire("Ouvrez d'abord une page de votre extranet.", "ko");
    return null;
  }
  dire("Lecture en cours...");
  let reponse;
  try {
    reponse = await chrome.tabs.sendMessage(onglet.id, {
      action: "observer",
      avecNoms: $("avecNoms").checked,
    });
  } catch (e) {
    dire("Page non lue. Rechargez-la, puis reessayez.", "ko");
    return null;
  }
  if (!reponse || !reponse.ok) {
    dire("Lecture impossible: " + ((reponse && reponse.erreur) || "page non lue"), "ko");
    return null;
  }
  dernierReleve = reponse.charge;
  return reponse.charge;
}

/* ------------------------------------------------------------------ */
/* Etat de la veille                                                    */
/* ------------------------------------------------------------------ */

async function rafraichir() {
  const config = await CS_VEILLE.reglages();
  $("veille").checked = config.active;
  $("intervalle").value = String(config.intervalle_heures);

  const tout = await chrome.storage.local.get(null);
  const espaces = Object.keys(tout)
    .filter((c) => c.startsWith("veille_etat:"))
    .map((c) => tout[c]);

  const lignes = [];
  if (!config.active) lignes.push("Surveillance arretee.");
  if (!espaces.length) {
    lignes.push("Aucun releve enregistre pour l'instant.");
  } else {
    for (const releve of espaces.sort((a, b) => a.espace.localeCompare(b.espace))) {
      const quand = new Date(releve.debut).toLocaleString("fr-FR");
      const pieces = (releve.rubriques || []).reduce(
        (n, r) =>
          n + ((r.pieces || (r.lignes || []).filter((l) => l.a_une_facture)).length),
        0
      );
      lignes.push(`${releve.espace}: ${pieces} pieces, le ${quand}`);
    }
  }
  /* Le dernier releve qui a reellement observe quelque chose. Un passage sur
   * une page sans index ne dit rien des manques, et l'afficher comme s'il le
   * faisait donnerait a lire un zero qui n'est pas une mesure. */
  const dernier = espaces.find((r) => (r.rubriques || []).some((x) => x.presente));
  if (dernier) {
    lignes.push("");
    lignes.push("Espace observe: " + (dernier.type_espace || "inconnu"));
    /* Le compte se fait par OBLIGATION du decret, et non par rubrique de
     * l'editeur. La rubrique des contrats en agrege quatre, et les releves
     * bancaires vivent dans la categorie fourre-tout: un compte par rubrique
     * ne pouvait exprimer ni les uns ni les autres. */
    /* Les codes REELLEMENT vus au dernier releve, ajoutes aux huit declares.
   * Sur une page de depenses les codes sont DECOUVERTS - ce sont les cles de
   * charges - et un rattachement exprime en codes d'index ne pouvait par
   * construction jamais y correspondre. La garde de biffage etait donc
   * inoperante sur toute une famille de pages. */
  const vus = (releve ? releve.rubriques || [] : [])
    .map((r) => String(r.rubrique_code || "").trim())
    .filter((c) => c && !RUBRIQUES.some(([code]) => code === c));
  const choix = RUBRIQUES.concat(
    [...new Set(vus)].map((c) => [c, c + " (vu sur cette page)"])
  );

  const etats = CS_VEILLE.manquesLegaux(
      dernier, config.rattachements, config.attendus, config.sans_objet
    );
    const manquants = CS_VEILLE.manquantes(etats);
    if (manquants.length) {
      lignes.push("");
      lignes.push("Il manque des pieces:");
      for (const m of manquants) {
        const compte = m.attendu !== undefined
          ? `${m.observe} vues sur ${m.attendu}`
          : "aucune piece";
        lignes.push(`  ${m.intitule}: ${compte}`);
      }
    } else if (etats.every((e) => e.etat === "NON_RATTACHE")) {
      /* Le cas du premier passage chez un syndic inconnu. Le dire vaut mieux
       * que rendre un ecran muet que l'utilisateur lira comme *tout va bien*. */
      lignes.push("");
      lignes.push(`${etats.length} obligations restent a rattacher.`);
      lignes.push("Aucun manque n'est affirme tant que ce n'est pas fait.");
    }
  }
  $("etatVeille").textContent = lignes.join("\n");

  await montrerSonde();

  const changements = await CS_VEILLE.changements();
  const total = changements.reduce((n, c) => n + c.parus + c.disparus, 0);
  const bloc = $("alerte");
  if (!total) {
    bloc.hidden = true;
    return;
  }
  /* Le mot compte. On dit *ont bouge*, jamais *retire*: trancher demande la
   * couverture et l'injectivite, qui sont verifiees dans CoproScope. */
  bloc.hidden = false;
  bloc.innerHTML = "";
  const titre = document.createElement("p");
  titre.innerHTML =
    `<strong>${total} emplacement${total > 1 ? "s ont" : " a"} bouge</strong> ` +
    `depuis le dernier point, sur ${changements.length} comparaison${changements.length > 1 ? "s" : ""}.`;
  const detail = document.createElement("p");
  detail.className = "note";
  detail.textContent =
    "Apparu ou disparu de son emplacement. Ce n'est pas un retrait: le dire " +
    "exigerait de verifier la couverture et l'unicite des reperes, ce que fait " +
    "CoproScope.";
  const exporter = document.createElement("button");
  exporter.textContent = "Enregistrer le journal des changements";
  exporter.addEventListener("click", async () => {
    await telecharger(
      { format: "coproscope.extranet.changements/1", changements },
      "coproscope-changements-" + new Date().toISOString().slice(0, 10) + ".json"
    );
    dire("Journal des changements enregistre.", "ok");
  });
  const vu = document.createElement("button");
  vu.textContent = "Marquer comme vu";
  vu.addEventListener("click", async () => {
    await CS_VEILLE.oublierChangements();
    await chrome.runtime.sendMessage({ action: "effacer_pastille" });
    await rafraichir();
  });
  bloc.append(titre, detail, exporter, vu);
}

/* ------------------------------------------------------------------ */
/* Ce que le decret exige, confronte a ce qui a ete vu                  */
/* ------------------------------------------------------------------ */

/* Les rubriques de l'editeur, avec leur intitule lisible. Les codes sont
 * declares et non deduits des libelles: chez cet editeur, *Documents
 * techniques* porte le code DIA. C'est de la topographie de page, pas du
 * droit - la liste legale, elle, vit dans `referentiel.js`. */
const RUBRIQUES = [
  ["ARR", "Arrete des comptes"],
  ["ASS", "Assemblees generales"],
  ["REG", "Reglement de copropriete"],
  ["CON", "Contrats"],
  ["DIV", "Documents divers"],
  ["DIA", "Documents techniques"],
  ["REU", "Reunion du conseil syndical"],
  ["JUS", "Assignations en justice"],
];

async function dessinerConformite() {
  const config = await CS_VEILLE.reglages();
  const tout = await chrome.storage.local.get(null);
  /* Le dernier releve qui a REELLEMENT observe quelque chose. Un passage sur
   * une page sans index ne dit rien des manques, et l'afficher comme s'il le
   * faisait donnerait a lire un zero qui n'est pas une mesure. */
  const releve = Object.keys(tout)
    .filter((c) => c.startsWith("veille_etat:"))
    .map((c) => tout[c])
    .find((r) => (r.rubriques || []).some((x) => x.presente));

  /* Les codes REELLEMENT vus au dernier releve, ajoutes aux huit declares.
   * Sur une page de depenses les codes sont DECOUVERTS - ce sont les cles de
   * charges - et un rattachement exprime en codes d'index ne pouvait par
   * construction jamais y correspondre. La garde de biffage etait donc
   * inoperante sur toute une famille de pages. */
  const vus = (releve ? releve.rubriques || [] : [])
    .map((r) => String(r.rubrique_code || "").trim())
    .filter((c) => c && !RUBRIQUES.some(([code]) => code === c));
  const choix = RUBRIQUES.concat(
    [...new Set(vus)].map((c) => [c, c + " (vu sur cette page)"])
  );

  const etats = CS_VEILLE.manquesLegaux(
    releve || { rubriques: [] },
    config.rattachements,
    config.attendus,
    config.sans_objet
  );
  const manques = CS_VEILLE.manquantes(etats);
  CS_PANNEAU.dessiner(
    $("conformite"),
    etats,
    manques,
    choix,
    {
      espace: releve ? releve.type_espace || releve.espace : "aucun releve",
      quand: releve ? new Date(releve.debut).toLocaleString("fr-FR") : "",
    },
    /* Enregistrement a chaque changement, et non au bouton.
     *
     * Une qualification novice du 2026-09-07 l'a nomme comme la deuxieme
     * raison d'abandonner: dix-huit lignes a remplir dans une fenetre de 380
     * pixels, et une fenetre d'extension se referme des qu'on clique ailleurs.
     * Le travail etait perdu au premier faux mouvement, et personne ne
     * recommence deux fois. */
    async () => {
      await CS_VEILLE.definirReglages(CS_PANNEAU.lire($("conformite")));
      dire("Enregistre.", "ok");
    }
  );
  return manques;
}

/* Le bouton reste, mais il ne sert plus qu'a RECALCULER: la saisie est deja
 * enregistree au fil de l'eau. Deux boutons nommes `Enregistrer` qui ne
 * faisaient pas la meme chose etaient l'une des ambiguites relevees. */
$("enregistrerConformite").addEventListener("click", async () => {
  await CS_VEILLE.definirReglages(CS_PANNEAU.lire($("conformite")));
  await dessinerConformite();
  await rafraichir();
  dire("Recalcule avec vos reponses.", "ok");
});

/* ------------------------------------------------------------------ */
/* Gestes                                                               */
/* ------------------------------------------------------------------ */

$("veille").addEventListener("change", async () => {
  await CS_VEILLE.definirReglages({ active: $("veille").checked });
  await chrome.runtime.sendMessage({ action: "regler_alarme" });
  await rafraichir();
  dire($("veille").checked ? "Surveillance activee." : "Surveillance arretee.", "ok");
});

$("intervalle").addEventListener("change", async () => {
  await CS_VEILLE.definirReglages({ intervalle_heures: Number($("intervalle").value) });
  await chrome.runtime.sendMessage({ action: "regler_alarme" });
  dire("Intervalle enregistre.", "ok");
});

/* L'effacement est irreversible et il n'y a pas de corbeille: on demande. */
let effacementArme = false;
$("effacer").addEventListener("click", async () => {
  if (!effacementArme) {
    effacementArme = true;
    $("effacer").textContent = "Confirmer: effacer definitivement";
    dire("Cliquez a nouveau pour confirmer. Rien n'est encore efface.", "ko");
    return;
  }
  const rendu = await CS_VEILLE.effacerReleves();
  effacementArme = false;
  $("effacer").textContent = "Effacer tous les releves";
  await rafraichir();
  await dessinerConformite();
  dire(`${rendu.efface} enregistrement(s) efface(s). Vos reponses sont gardees.`, "ok");
});

$("sonderMaintenant").addEventListener("click", async () => {
  dire("Verification en cours...");
  const rendu = await chrome.runtime.sendMessage({ action: "sonder_maintenant" });
  await rafraichir();
  dire(
    rendu && rendu.espaces
      ? `Connexion verifiee sur ${rendu.espaces} espace(s).`
      : "Aucun espace connu: passez d'abord sur votre extranet.",
    "ok"
  );
});

/* L'etat de la surveillance elle-meme, et c'est la garde numero 2 de
 * l'arbitrage A2: on affiche la derniere TENTATIVE et le dernier SUCCES.
 * Un ecran qui ne montrerait que le succes laisserait croire que rien n'a
 * change, alors que plus rien n'est observe depuis trois semaines. */
async function montrerSonde() {
  const tout = await chrome.storage.local.get(null);
  const etats = Object.keys(tout)
    .filter((c) => c.startsWith("sonde_etat:"))
    .map((c) => tout[c]);
  const zone = $("etatSonde");
  if (!etats.length) {
    zone.hidden = true;
    return;
  }
  const lignes = [];
  let alerte = false;
  for (const etat of etats) {
    const d = CS_SONDE.diagnostic(etat, Date.now());
    const tentative = etat.derniere_tentative;
    const quand = new Date(tentative.quand).toLocaleString("fr-FR");
    if (d.niveau === "VOIT") {
      lignes.push(`Connexion verifiee le ${quand}: l'extranet est visible.`);
    } else if (d.niveau === "AVEUGLE") {
      alerte = true;
      const jours = Math.floor(d.jours_sans_succes);
      lignes.push(`Derniere tentative le ${quand}: ${d.motif}.`);
      lignes.push(
        `Rien n'a ete observe depuis ${jours} jour${jours > 1 ? "s" : ""}. ` +
          "Reconnectez-vous a votre extranet, sinon la surveillance ne voit plus rien."
      );
    } else if (d.niveau === "JAMAIS_VU") {
      alerte = true;
      lignes.push(`Derniere tentative le ${quand}: ${d.motif}.`);
      lignes.push("La surveillance n'a encore jamais reussi a voir cet espace.");
    }
  }
  zone.textContent = lignes.join("\n");
  zone.className = "noms" + (alerte ? " alerte" : "");
  zone.hidden = false;
}

$("observer").addEventListener("click", async () => {
  const releve = await relever();
  if (!releve) return;
  const journal = construireJournal(releve);
  montrerNoms(journal);
  if (releve.type === "aucun") {
    dire("Rien a relever sur cette page.", "ko");
    return;
  }
  await telecharger(journal, nomFichier(releve, "journal"));
  await CS_VEILLE.enregistrer(releve);
  await rafraichir();
  await dessinerConformite();
  dire("Journal enregistre. " + resume(journal), "ok");
});

$("exporter").addEventListener("click", async () => {
  const sel = $("sel").value.trim();
  if (!sel) {
    dire(
      "Indiquez le secret de la copropriete: sans lui, l'export permettrait a " +
        "un tiers de deviner ce qu'il contient.",
      "ko"
    );
    return;
  }
  const releve = dernierReleve || (await relever());
  if (!releve || releve.type === "aucun") {
    dire("Faites d'abord un releve sur une page d'index.", "ko");
    return;
  }
  const observateur = $("observateur").value.trim() || "observateur";
  const paquet = await construireExport(releve, sel, observateur);
  await telecharger(paquet, nomFichier(releve, "export"));
  /* On memorise le TEMOIN du sel, jamais le sel. Le temoin est une empreinte
   * publique: il permet de dire *"ce n'est pas le secret de vos exports
   * precedents"* au lieu de laisser un voisin decouvrir un zero de concordance
   * et le lire comme un desaccord. Le sel lui-meme n'est ecrit nulle part -
   * ni ici, ni dans l'export, ni dans un journal. */
  const connu = (await chrome.storage.local.get(["temoin_sel"])).temoin_sel;
  await chrome.storage.local.set({ observateur, temoin_sel: paquet.temoin_sel });
  if (connu && connu !== paquet.temoin_sel) {
    dire(
      "Export produit, mais ce secret n'est pas celui de vos exports " +
        "precedents: ce fichier ne se recoupera pas avec eux.",
      "ko"
    );
    return;
  }
  dire(`Export produit: ${paquet.pieces.length} empreintes, aucun libelle.`, "ok");
});

chrome.storage.local.get(["observateur"]).then((r) => {
  $("observateur").value = r.observateur || "";
});
rafraichir();
dessinerConformite();
montrerSonde();
