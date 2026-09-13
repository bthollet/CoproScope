/*
 * Service worker. Il est la SEULE main vers CoproScope local.
 *
 * Motif technique: le serveur local ne pose aucun en-tete CORS, donc un POST
 * emis depuis la page de l'extranet serait bloque par le navigateur. Le worker,
 * lui, passe - c'est pour cela que la transmission vit ici et non dans le
 * lecteur.
 *
 * Motif de conception, plus important: separer la main qui lit l'extranet de la
 * main qui parle a CoproScope. Le lecteur ne connait aucune adresse locale; le
 * worker ne sait rien lire d'un extranet. Aucune des deux ne peut donc, a elle
 * seule, faire circuler quoi que ce soit vers un tiers.
 *
 * Le jeton local voyage en en-tete, jamais en cookie ni dans l'adresse: le
 * cookie du serveur local n'isole pas par port, et une adresse finit toujours
 * dans un journal.
 */

/* ------------------------------------------------------------------
 * INERTE dans cette version, et deliberement conserve
 * ------------------------------------------------------------------
 *
 * L'integration a CoproScope est repoussee: la fenetre du plugin n'emet plus
 * l'action `transmettre`, et la permission d'atteindre `127.0.0.1` a ete
 * RETIREE du manifeste. Une extension ne doit pas demander un acces dont elle
 * ne se sert pas - c'est la premiere chose qu'un utilisateur prudent regarde,
 * et la premiere qu'un examen refuse.
 *
 * Le code reste ici parce qu'il est juste et qu'il sera rebranche tel quel. Le
 * rebranchement demandera trois gestes: reintroduire la permission, rappeler
 * `transmettre` depuis la fenetre, et verifier que le serveur local accepte la
 * requete. Tant que ces trois-la ne sont pas faits, ce fichier ne s'execute
 * jamais.
 */

"use strict";

/* Le service worker n'est pas un module: `importScripts` est la seule voie. */
importScripts("sonde.js");

/* ------------------------------------------------------------------
 * La veille continue - arbitrage A2, tranche par Brice le 2026-09-07
 * ------------------------------------------------------------------
 *
 * Sans minuterie, la couverture depend des habitudes de l'utilisateur: rien
 * pendant les vacances, or c'est la que le silence compte.
 *
 * CE QUE LA MINUTERIE FAIT: une requete de lecture par espace, et une seule
 * question - *est-ce que je vois encore l'index ?* Elle date la tentative et,
 * separement, le dernier succes.
 *
 * CE QU'ELLE NE FAIT PAS, ET POURQUOI: elle ne releve pas. Un service worker
 * MV3 n'a pas de DOM, donc pas de lecteur. Refaire un lecteur a coups
 * d'expressions regulieres reviendrait a coder les modalites d'un editeur, et
 * a entretenir deux lectures qui divergeraient - le defaut que ce lot vient
 * justement de corriger sur les cles d'emplacement. Le releve reste le travail
 * du script de contenu, quand une page s'ouvre.
 *
 * Ce partage met la seule chose qui doit tourner sans surveillance - *est-ce
 * que je vois encore* - dans le seul composant qui tourne sans onglet.
 *
 * Un releve complet sans onglet reste possible par un document hors ecran ou
 * par un onglet de fond. Les deux demandent une permission de plus et un
 * arbitrage: ce n'est pas ce qui a ete decide ici.
 */

const ALARME = "cs-veille";

/* L'ancre qui prouve qu'on regarde un index, par hote. C'est de la topographie
 * de page, pas du droit: elle est DECLAREE, jamais devinee. Un hote absent de
 * cette table rend `NON_EXPLORE` avec le motif *aucune ancre declaree* - la
 * sonde devient inutile, elle ne devient jamais menteuse. */
const ANCRES = {
  "coprodirecte.fr": "id=\"documents\"",
  "www.coprodirecte.fr": "id=\"documents\"",
};

function ancreDe(url) {
  try {
    return ANCRES[new URL(url).hostname] || "";
  } catch (e) {
    return "";
  }
}

async function reglerAlarme() {
  const stocke = await chrome.storage.local.get("veille_reglages");
  const config = stocke.veille_reglages || {};
  if (config.active === false) {
    await chrome.alarms.clear(ALARME);
    return { arretee: true };
  }
  const heures = Number(config.intervalle_heures) || 6;
  /* `periodInMinutes` a un plancher d'une minute cote navigateur. On reste
   * tres au-dessus: sonder plus souvent que l'intervalle de releve n'apprend
   * rien et fait du bruit chez le syndic. */
  await chrome.alarms.create(ALARME, { periodInMinutes: heures * 60 });
  return { arretee: false, minutes: heures * 60 };
}

/* Les espaces deja connus, c'est-a-dire ceux ou l'utilisateur est passe au
 * moins une fois. La sonde ne decouvre jamais d'adresse toute seule: elle ne
 * regarde que la ou on l'a deja menee. */
async function espacesConnus() {
  const tout = await chrome.storage.local.get(null);
  return Object.keys(tout)
    .filter((c) => c.startsWith("veille_etat:"))
    .map((c) => tout[c])
    .filter((r) => r && r.url)
    .map((r) => r.url);
}

async function passerLaSonde(maintenant) {
  const urls = await espacesConnus();
  const rendu = [];
  for (const url of urls) {
    const tentative = await CS_SONDE.sonder(url, ancreDe(url), maintenant);
    const cle = "sonde_etat:" + url;
    const stocke = await chrome.storage.local.get(cle);
    const fusion = CS_SONDE.fusionner(stocke[cle], tentative);
    await chrome.storage.local.set({ [cle]: fusion });
    rendu.push(fusion);
  }
  /* Devenir aveugle est un evenement en soi, et il doit se voir sur l'icone au
   * meme titre qu'un changement: un outil qui a cesse de voir et qui se tait
   * est pire qu'un outil absent. */
  const aveugles = rendu.filter(
    (f) => CS_SONDE.diagnostic(f, maintenant).niveau === "AVEUGLE"
  );
  if (aveugles.length) {
    await chrome.action.setBadgeText({ text: "!" });
    await chrome.action.setBadgeBackgroundColor({ color: "#7a5a12" });
  }
  return rendu;
}

chrome.alarms.onAlarm.addListener((alarme) => {
  if (alarme.name !== ALARME) return;
  passerLaSonde(Date.now());
});

chrome.runtime.onInstalled.addListener(() => {
  reglerAlarme();
});
chrome.runtime.onStartup.addListener(() => {
  reglerAlarme();
});

const DEFAUT = { hote: "http://127.0.0.1:8765", jeton: "" };

async function reglages() {
  const stocke = await chrome.storage.local.get(["hote", "jeton"]);
  return Object.assign({}, DEFAUT, stocke);
}

/* Les seules adresses qu'une transmission puisse viser: la machine de
 * l'utilisateur. Tout le reste est refuse, y compris le domaine du syndic. */
const HOTES_LOCAUX = /^https?:\/\/(127\.0\.0\.1|localhost|\[::1\])(:\d+)?$/;

async function transmettre(charge) {
  const { hote, jeton } = await reglages();
  if (!HOTES_LOCAUX.test(String(hote || "").replace(/\/+$/, ""))) {
    return {
      ok: false,
      erreur:
        "Adresse refusee: une transmission ne peut viser que votre propre "
        + "machine. Rien ne part vers votre syndic.",
    };
  }
  if (!jeton) {
    return {
      ok: false,
      erreur:
        "Aucun jeton local enregistre. Ouvrez les reglages du plugin et collez " +
        "le jeton affiche par CoproScope.",
    };
  }
  let reponse;
  try {
    reponse = await fetch(hote + "/extranet/releve", {
      method: "POST",
      headers: { "content-type": "application/json", "x-coproscope-token": jeton },
      body: JSON.stringify(charge),
    });
  } catch (e) {
    return {
      ok: false,
      erreur:
        "CoproScope ne repond pas sur " + hote + ". Est-il lance ? Le releve " +
        "n'est pas perdu: la fenetre du plugin sait le copier dans le " +
        "presse-papier.",
    };
  }
  if (!reponse.ok) {
    return { ok: false, erreur: "CoproScope a refuse le releve (" + reponse.status + ")." };
  }
  const resultat = await reponse.json().catch(() => ({}));
  return { ok: true, resultat };
}

/* La pastille sur l'icone. Elle COMPTE, elle n'accuse pas.
 *
 * Un content script ne peut pas la poser: seul le worker le peut. C'est aussi
 * le bon endroit, parce que le nombre porte sur l'ensemble des espaces et pas
 * sur la page ou l'on se trouve.
 *
 * Le libelle est un nombre nu, jamais un mot. "3" laisse ouvert ce qui a bouge;
 * "3 retraits" serait un verdict que rien ici ne permet d'etablir - il faut la
 * couverture et l'injectivite, qui sont verifiees dans CoproScope. */
async function signaler(nombre) {
  const stocke = await chrome.storage.local.get("veille_changements");
  const total = (stocke.veille_changements || []).reduce(
    (n, c) => n + c.parus + c.disparus,
    0
  );
  const texte = total > 0 ? String(total) : "";
  await chrome.action.setBadgeText({ text: texte });
  await chrome.action.setBadgeBackgroundColor({ color: "#b3261e" });
  return { ok: true, total };
}

chrome.runtime.onMessage.addListener((message, _expediteur, repondre) => {
  if (message && message.action === "signaler") {
    signaler(message.nombre).then(repondre);
    return true;
  }
  if (message && message.action === "effacer_pastille") {
    chrome.action.setBadgeText({ text: "" }).then(() => repondre({ ok: true }));
    return true;
  }
  if (message && message.action === "regler_alarme") {
    reglerAlarme().then(repondre);
    return true;
  }
  if (message && message.action === "sonder_maintenant") {
    passerLaSonde(Date.now()).then((r) => repondre({ ok: true, espaces: r.length }));
    return true;
  }
  if (message && message.action === "transmettre") {
    /* Le chemin est inerte - aucun emetteur, permission retiree du manifeste -
     * mais `hote` venait de `chrome.storage.local` SANS validation, et
     * `coprodirecte.fr` est dans les `host_permissions`. Un hote pointant vers
     * le syndic aurait fait partir en POST la charge complete, libelles
     * compris. La ligne rouge tenait sur une inertie; elle tient maintenant sur
     * une garde. */
    transmettre(message.charge).then(repondre);
    return true;
  }
  return false;
});
