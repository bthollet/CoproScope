/*
 * Production du journal exportable, et etage de surveillance des noms.
 *
 * Le plugin produit ici un fichier autonome. Il ne depend d'aucune application
 * lancee, d'aucun compte, d'aucun reseau: c'est un releve date que l'on garde,
 * que l'on transmet, et que l'on comparera plus tard.
 *
 * ==================================================================
 * L'etage des noms de fichiers
 * ==================================================================
 *
 * Un extranet expose deux noms pour la meme piece, et ils ne disent pas la
 * meme chose.
 *
 * Le **libelle affiche** est ecrit pour l'oeil: il se repete volontiers d'un
 * exercice a l'autre. Mesure du 2026-09-04 sur un index reel: 115 pieces pour
 * seulement 83 libelles distincts, et dans la rubrique des arretes de comptes,
 * 40 pieces pour 8 libelles.
 *
 * Le **nom servi par le serveur** - l'en-tete `content-disposition`, obtenu par
 * une requete sans corps - s'est revele injectif sur la totalite du meme index:
 * 115 pieces, 115 noms, et 40 noms distincts la ou le libelle n'en donne que 8.
 *
 * D'ou cet etage. Suivre les noms n'est pas un doublon du suivi des libelles,
 * c'est une **seconde mesure independante**. Deux mesures qui s'accordent
 * affermissent un constat; deux mesures qui divergent apprennent quelque chose.
 *
 * Ce qu'il permet concretement, et que le libelle seul ne permet pas:
 *
 * - reconnaitre une piece **renommee** au lieu de croire qu'elle a disparu et
 *   qu'une autre est apparue - c'est-a-dire ne pas fabriquer un faux retrait;
 * - distinguer des pieces que l'affichage confond, comme cinq exercices
 *   d'annexes comptables portant tous le meme intitule;
 * - reperer qu'un fichier a change de nom **sans** changer de place, ce qui
 *   n'est pas anodin: c'est souvent le signe d'un remplacement.
 *
 * Le journal porte donc, a chaque passage, la sante de cette mesure: combien de
 * pieces ont livre un nom, combien de noms sont distincts, et s'il existe des
 * collisions. Une degradation de ces chiffres est elle-meme une information -
 * elle dit que la seconde mesure devient moins fiable, avant qu'on s'en
 * apercoive sur un constat faux.
 *
 * ==================================================================
 * Deux fichiers, deux usages
 * ==================================================================
 *
 * `complet` reste sur la machine. Il porte les libelles et les noms tels
 * qu'affiches, parce que c'est ce qui rend un constat lisible par un humain.
 *
 * `empreintes` se transmet. Il ne porte que des empreintes salees, des codes de
 * rubrique et des dates. Un extranet de copropriete expose des donnees de tiers
 * - la liste des coproprietaires y figure avec leur etat civil - et un fichier
 * d'echange se retrouve toujours quelque part.
 *
 * Le sel est un secret partage par les observateurs d'une meme copropriete, et
 * par eux seuls. Sans lui, une empreinte serait un **oracle**: qui detient le
 * fichier pourrait tester une hypothese - *"cette copropriete detient-elle un
 * document intitule ainsi ?"* - en calculant l'empreinte de sa supposition. Le
 * nombre d'intitules plausibles est petit; l'attaque tient sur un portable.
 */

"use strict";

/* Separateurs ecrits sans sequence d'echappement, pour qu'aucun outil de
 * transformation de fichier ne puisse les alterer en silence: ils doivent etre
 * identiques a ceux de CoproScope, sans quoi les empreintes ne se recoupent
 * pas. */
const NUL = String.fromCharCode(0);

const FORMAT_JOURNAL = "coproscope.extranet.journal/1";
const FORMAT_EXPORT = "coproscope.extranet.observation/3";

/* Le domaine cryptographique de l'echange entre voisins, identique a
 * `_extranet_echange.DOMAINE`. CoproScope emploie deux sels aux buts OPPOSES:
 * celui-ci est partage entre les voisins d'une meme copropriete pour que leurs
 * empreintes COINCIDENT, tandis que le sel d'alias de BiffageOps est propre a
 * une instance pour que deux coffres ne produisent JAMAIS le meme alias. Le
 * domaine garantit qu'aucune empreinte de ce module ne peut etre confondue
 * avec une valeur produite ailleurs dans le produit, meme a sel egal. */
const DOMAINE = "coproscope-extranet-recoupement-v1" + NUL;

/* ------------------------------------------------------------------ */
/* Empreintes                                                          */
/* ------------------------------------------------------------------ */

async function empreinte(valeur, sel) {
  if (!sel) throw new Error("sel manquant");
  const octets = new TextEncoder().encode(DOMAINE + sel + NUL + valeur);
  const digest = await crypto.subtle.digest("SHA-256", octets);
  return [...new Uint8Array(digest)]
    .map((o) => o.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 32);
}

async function temoinSel(sel) {
  const octets = new TextEncoder().encode(DOMAINE + "temoin" + NUL + sel);
  const digest = await crypto.subtle.digest("SHA-256", octets);
  return [...new Uint8Array(digest)]
    .map((o) => o.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 16);
}

/* ------------------------------------------------------------------ */
/* Etage des noms                                                      */
/* ------------------------------------------------------------------ */

function piecesDe(rubrique) {
  if (rubrique.pieces) return rubrique.pieces;
  return (rubrique.lignes || []).filter((l) => l.a_une_facture);
}

function libelleDe(entree) {
  if (typeof entree.libelle === "string") return entree.libelle;
  return (entree.colonnes || []).join(" | ");
}

/* La sante de la mesure par les noms, globale et rubrique par rubrique.
 *
 * `collisions` est le chiffre a surveiller: tant qu'il vaut zero, le nom
 * distingue chaque piece et peut servir a reconnaitre un renommage. Des qu'il
 * monte, cette seconde mesure perd sa force - et il vaut mieux le lire ici que
 * le decouvrir sur un constat faux. */
function surveillanceNoms(rubriques) {
  const tous = [];
  const parRubrique = {};
  for (const rubrique of rubriques) {
    if (!rubrique.presente) continue;
    const pieces = piecesDe(rubrique);
    const noms = pieces.map((p) => (p.nom_serveur || "").trim()).filter((n) => n);
    tous.push(...noms);
    parRubrique[rubrique.rubrique_code] = {
      pieces: pieces.length,
      avec_nom: noms.length,
      noms_distincts: new Set(noms).size,
      collisions: noms.length - new Set(noms).size,
      libelles_distincts: new Set(pieces.map(libelleDe)).size,
    };
  }
  const distincts = new Set(tous).size;
  const pieces = rubriques
    .filter((r) => r.presente)
    .reduce((n, r) => n + piecesDe(r).length, 0);
  return {
    pieces,
    avec_nom: tous.length,
    sans_nom: pieces - tous.length,
    noms_distincts: distincts,
    collisions: tous.length - distincts,
    injectif: tous.length > 0 && tous.length === distincts,
    couverture: pieces ? Math.round((tous.length / pieces) * 100) : 0,
    par_rubrique: parRubrique,
  };
}

/* ------------------------------------------------------------------ */
/* Production                                                          */
/* ------------------------------------------------------------------ */

function construireJournal(releve) {
  const rubriques = releve.rubriques || [];
  return {
    format: FORMAT_JOURNAL,
    editeur: releve.editeur,
    espace: releve.espace,
    type: releve.type,
    debut: releve.debut,
    fin: releve.fin,
    pagination: releve.pagination,
    /* Sans preuve de cloture, aucune absence n'est affirmable plus tard. Le
     * dire dans le fichier evite qu'un lecteur futur conclue a tort. */
    cloture: releve.pagination ? "AUCUNE" : "CONSTATEE",
    rubriques_parcourues: rubriques.filter((r) => r.presente).length,
    rubriques_non_explorees: rubriques
      .filter((r) => !r.presente)
      .map((r) => r.rubrique_code),
    noms: surveillanceNoms(rubriques),
    rubriques,
  };
}

async function construireExport(releve, sel, observateur) {
  const rubriques = releve.rubriques || [];
  const pieces = [];
  for (const rubrique of rubriques) {
    if (!rubrique.presente) continue;
    for (const piece of piecesDe(rubrique)) {
      /* Une seule construction de cle dans tout le plugin, et c'est celle de
       * `cle.js`. Une piece sans emplacement exploitable part avec une
       * empreinte vide, exactement comme cote Python: elle sort de la
       * comparaison au lieu d'y entrer sous un mauvais nom. */
      const { cle: emplacement, qualifiee } = CS_CLE.emplacementDe(
        rubrique.rubrique_code,
        piece
      );
      pieces.push({
        /* Empreint et non en clair depuis le 2026-09-07. Sur un index le code
         * serait anodin - `ARR`, `CON` - mais sur une page de depenses il est
         * DECOUVERT et non declare: c'est l'en-tete du groupe de charges, donc
         * un libelle ET un montant. Le recoupement n'y perd rien: deux voisins
         * qui partagent le sel obtiennent la meme valeur. */
        emp_rubrique: await empreinte(rubrique.rubrique_code, sel),
        emp_emplacement: qualifiee ? await empreinte(emplacement, sel) : "",
        emp_nom: (piece.nom_serveur || "").trim()
          ? await empreinte(piece.nom_serveur.trim(), sel)
          : "",
        emp_contenu: "",
      });
    }
  }
  return {
    format: FORMAT_EXPORT,
    temoin_sel: await temoinSel(sel),
    observateur,
    editeur: releve.editeur,
    espace: releve.espace,
    debut: releve.debut,
    fin: releve.fin,
    /* La couverture voyage avec les pieces, et ce n'est pas un detail: sans
     * elle, un ecart entre deux voisins ne peut pas etre trie entre "il n'a
     * pas regarde la" et "l'extranet ne lui sert pas la meme chose". */
    rubriques: await Promise.all(
      rubriques.map(async (r) => ({
        /* Empreint, pour la meme raison que les pieces: sur une page de
         * depenses le code de rubrique est un en-tete de groupe de charges,
         * donc un libelle et un montant. */
        emp_rubrique: await empreinte(r.rubrique_code, sel),
        etat: r.presente ? "PARCOURUE" : "NON_EXPLOREE",
        cloture: r.presente && !releve.pagination ? "CONSTATEE" : "AUCUNE",
        nb_pieces: String(r.presente ? piecesDe(r).length : 0),
      }))
    ),
    pieces,
    noms: (() => {
      const s = surveillanceNoms(rubriques);
      /* On transmet la sante de la mesure, jamais les noms eux-memes. */
      return {
        pieces: s.pieces, avec_nom: s.avec_nom, noms_distincts: s.noms_distincts,
        collisions: s.collisions, injectif: s.injectif, couverture: s.couverture,
      };
    })(),
  };
}

function nomFichier(releve, suffixe) {
  const jour = (releve.debut || "").slice(0, 10) || "sans-date";
  const heure = (releve.debut || "").slice(11, 16).replace(":", "") || "0000";
  const espace = (releve.type || "index").replace(/[^a-z]/gi, "");
  return `coproscope-${espace}-${jour}-${heure}-${suffixe}.json`;
}
