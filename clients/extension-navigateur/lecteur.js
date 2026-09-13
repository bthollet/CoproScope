/*
 * Lecteur de page. Il extrait une structure neutre et rien d'autre.
 *
 * ------------------------------------------------------------------
 * Ce que ce script ne fait pas, et pourquoi
 * ------------------------------------------------------------------
 *
 * Il ne calcule aucune cle, ne rend aucun verdict, n'applique aucune regle de
 * droit. Tout cela vit dans CoproScope, en Python, ou c'est teste. Le lecteur
 * rend ce qu'il voit: des rubriques, des groupes, des libelles, et les noms que
 * le serveur donne a ses fichiers.
 *
 * Le motif est simple: deux implantations de la meme logique divergent
 * toujours, et la divergence se voit le jour ou l'on en a le plus besoin.
 * Ici, un seul endroit sait raisonner.
 *
 * ------------------------------------------------------------------
 * La ligne rouge, en pratique
 * ------------------------------------------------------------------
 *
 * Le plugin agit sur la machine de l'utilisateur autant qu'il le faut. Tout ce
 * qui sort vers le syndic passe par un clic humain.
 *
 * Ce script n'emet donc que des requetes de LECTURE - `GET` et `HEAD` - vers
 * des adresses **deja presentes dans la page**. Il ne construit aucune adresse,
 * ne soumet aucun formulaire, ne clique sur rien, n'ecrit rien dans la page.
 *
 * Il ne clique meme pas sur les onglets de rubrique, et ce n'est pas une
 * precaution abstraite: l'effet d'un clic sur un element sans lien n'est pas
 * observable a l'avance, et chez un autre editeur il pourrait valider ou
 * accuser reception. C'est possible ici parce que la mesure du 2026-09-04 a
 * montre que les huit rubriques sont **deja dans le DOM**, simplement masquees.
 * Chez un editeur qui chargerait a la demande, le lecteur declarera les
 * rubriques manquantes NON_EXPLOREE - et l'absence ne sera pas affirmable. Ce
 * comportement degrade est voulu.
 */

(() => {
  "use strict";

  /* Codes de rubrique de l'editeur observe. Ils sont declares et non deduits
   * des libelles affiches: la rubrique intitulee "Documents techniques" porte
   * le code DIA. Un lecteur qui deduirait l'un de l'autre se tromperait des la
   * premiere rubrique, en silence. */
  const CODES = ["ARR", "ASS", "CON", "DIV", "JUS", "REU", "REG", "DIA"];
  /* Ecrit sans sequence d'echappement pour qu'aucun outil ne l'altere en
   * silence: il doit valoir exactement celui de CoproScope. */
  /* Le separateur vient de `cle.js`: un seul endroit le declare. La cle
   * construite ici n'est PAS un emplacement - elle ne porte pas la rubrique et
   * ne sert qu'a dedoublonner les deux liens d'une meme piece A L'INTERIEUR
   * d'une rubrique. La distinction compte: une verification adverse du
   * 2026-09-07 a montre que la garde d'unicite, purement textuelle, ne voyait
   * pas cette seconde construction. */
  const SEP_CLE = CS_CLE.SEP;
  const MARQUEUR_LIEN = "documents/";
  const CLASSE_ICONE = "pj";
  const MARQUEURS_PAGINATION = ["pagin", "suivant", "page-suiv"];

  const texte = (n) => (n.textContent || "").replace(/\s+/g, " ").trim();

  const liensDe = (racine) =>
    [...racine.querySelectorAll("a[href]")].filter((a) =>
      (a.getAttribute("href") || "").includes(MARQUEUR_LIEN)
    );

  /* Le nom que le serveur donne au fichier, obtenu sans telecharger le corps.
   *
   * Mesure du 2026-09-04: ce nom est injectif sur la totalite de l'index - 115
   * pieces, 115 noms - et il distingue 40 pieces la ou le libelle affiche n'en
   * distingue que 8. Il sert a reconnaitre une piece deplacee ou renommee, ce
   * qui evite un faux retrait.
   *
   * Il ne quitte JAMAIS la machine tel quel: CoproScope ne l'exporte que sous
   * forme d'empreinte salee. Chez un autre editeur, un nom de fichier peut
   * porter un patronyme. */
  async function nomServeur(url) {
    try {
      const reponse = await fetch(url, { method: "HEAD", credentials: "include" });
      const entete = reponse.headers.get("content-disposition") || "";
      const trouve = entete.match(/filename\*?=(?:UTF-8''|")?([^";]+)/i);
      return trouve ? decodeURIComponent(trouve[1]).trim() : "";
    } catch (e) {
      return "";
    }
  }

  function pagine() {
    for (const noeud of document.querySelectorAll("[class]")) {
      const classe = (noeud.className || "").toString().toLowerCase();
      if (MARQUEURS_PAGINATION.some((m) => classe.includes(m))) return true;
    }
    return false;
  }

  /* Un index de documents: rubriques declarees, groupes portes par des lignes
   * sans lien, deux liens par piece dont un sans texte. */
  async function lireIndexDocuments(avecNoms) {
    const rubriques = [];
    for (const code of CODES) {
      const bloc = document.querySelector("div." + code);
      if (!bloc) {
        rubriques.push({ rubrique_code: code, presente: false, pieces: [] });
        continue;
      }
      let groupe = "";
      const pieces = [];
      const vues = new Set();
      for (const ligne of bloc.querySelectorAll("tr")) {
        const liens = liensDe(ligne);
        const cellules = [...ligne.children].filter((c) =>
          ["TD", "TH"].includes(c.tagName)
        );
        if (liens.length === 0) {
          if (cellules.length <= 2 && texte(ligne)) groupe = texte(ligne);
          continue;
        }
        const nommes = liens.filter((a) => !a.classList.contains(CLASSE_ICONE));
        const libelle = nommes.map(texte).find((t) => t) || "";
        const cle = groupe + SEP_CLE + libelle;
        if (libelle && vues.has(cle)) continue;
        if (libelle) vues.add(cle);
        const piece = { groupe, libelle, nom_serveur: "" };
        if (avecNoms && nommes.length) {
          piece.nom_serveur = await nomServeur(nommes[0].href);
        }
        pieces.push(piece);
      }
      rubriques.push({ rubrique_code: code, presente: true, pieces });
    }
    return rubriques;
  }

  /* Un etat de depenses: les cles de charges sont decouvertes et non declarees,
   * et toutes les colonnes entrent dans la ligne - le montant compris, parce
   * que c'est lui qui fait tomber a zero les 21 collisions mesurees. */
  /* La largeur d'une ligne de donnees, DECOUVERTE et non codee: dans un
   * tableau, les lignes de donnees partagent le meme nombre de colonnes et les
   * lignes de service en ont un autre. */
  function largeurModale(lignes) {
    const comptes = new Map();
    for (const ligne of lignes) {
      const n = [...ligne.children].filter((c) => ["TD", "TH"].includes(c.tagName)).length;
      if (n > 2) comptes.set(n, (comptes.get(n) || 0) + 1);
    }
    let meilleure = 0;
    let vus = -1;
    for (const [n, v] of comptes) if (v > vus) { vus = v; meilleure = n; }
    return meilleure;
  }

  async function lireDepenses(avecNoms) {
    const parCle = new Map();
    /* Les lignes rencontrees avant tout en-tete existent - mesure faite sur la
     * page reelle. Leur donner un nom plutot que la chaine vide evite une
     * rubrique muette, qui ne se lit pas a l'ecran et ne se cite pas dans une
     * question au syndic. */
    let cle = "(hors groupe)";
    let ignorees = 0;
    const lignes = [...document.querySelectorAll("tr")];
    const largeur = largeurModale(lignes);
    for (const ligne of lignes) {
      const liens = liensDe(ligne);
      const cellules = [...ligne.children]
        .filter((c) => ["TD", "TH"].includes(c.tagName));
      const textes = cellules.map(texte);
      const pleines = textes.filter((c) => c);
      /* Un en-tete de groupe se reconnait au nombre de CELLULES, pas au nombre
       * de cellules remplies. Defaut mesure le 2026-09-04 sur la page reelle:
       * 348 lignes de totaux portent deux valeurs et etaient prises pour des
       * en-tetes, faisant passer 42 cles de charges a 340. Les depenses
       * suivantes se rattachaient alors a une cle fantome PORTANT UN MONTANT,
       * qui change a chaque passage - donc un retrait et un ajout pour chaque
       * piece du groupe. */
      if (liens.length === 0 && cellules.length <= 2) {
        if (pleines.length) cle = pleines.join(" ");
        continue;
      }
      if (largeur && cellules.length !== largeur) { ignorees++; continue; }
      if (!pleines.length) continue;
      if (!parCle.has(cle)) parCle.set(cle, []);
      const entree = { colonnes: pleines, a_une_facture: liens.length > 0, nom_serveur: "" };
      if (avecNoms && liens.length) entree.nom_serveur = await nomServeur(liens[0].href);
      parCle.get(cle).push(entree);
    }
    const rubriques = [...parCle.entries()].map(([code, lignesCle]) => ({
      rubrique_code: code,
      presente: true,
      lignes: lignesCle,
    }));
    /* Compte rendu, jamais jete en silence: c'est le temoin que la largeur
     * modale est la bonne. */
    rubriques.lignes_ignorees = ignorees;
    return rubriques;
  }

  /* Quel index cette page porte-t-elle, si elle en porte un ?
   *
   * Defaut trouve a la premiere utilisation reelle, le 2026-09-06: un releve a
   * ete lance depuis `/espace-client`, qui ne porte aucun bloc de rubrique. Le
   * lecteur a fait ce qu'il fallait - huit rubriques NON_EXPLOREE, aucune
   * declaree vide - mais l'utilisateur n'a rien vu qui le lui dise, et a
   * recolte un journal sans matiere.
   *
   * Repondre `aucun` ici permet a la fenetre de le dire, et a la veille de ne
   * pas enregistrer un passage qui n'observe rien. Un passage vide dans le
   * journal n'est pas neutre: il ferait croire a une couverture qui n'a pas eu
   * lieu. */
  /* Quel espace d'acces cette page sert-elle ?
   *
   * Demande de Brice le 2026-09-06: afficher le type d'espace distinct
   * detecte. Ce n'est pas cosmetique - c'est le controle `EXT-001` du
   * referentiel: la loi, article 18 I, exige un acces **differencie** selon
   * que les documents s'adressent a tous les coproprietaires ou aux seuls
   * membres du conseil syndical.
   *
   * Mesure du 2026-09-04: chez cet editeur il n'y a que DEUX espaces, et la
   * zone collective sert dans une meme page des rubriques des deux colleges.
   * Le nommer a l'ecran, passage apres passage, est le seul moyen de voir si
   * cela change - et de savoir depuis quel acces une observation a ete faite,
   * ce dont depend tout recoupement avec un voisin. */
  function typeEspace() {
    const chemin = location.pathname;
    if (/espace-client/.test(chemin)) return "personnel";
    if (/espace-copropriete/.test(chemin)) return "collectif";
    return "inconnu";
  }

  function typeIndex() {
    if (/depenses/.test(location.pathname)) return "depenses";
    const aDesBlocs = CODES.some((c) => document.querySelector("div." + c));
    return aDesBlocs ? "documents" : "aucun";
  }

  /* ------------------------------------------------------------------ */
  /* Ce qui ne se releve jamais                                          */
  /* ------------------------------------------------------------------ */

  /* La liste de tous les coproprietaires porte l'etat civil, le domicile et
   * l'adresse electronique de chacun. Le referentiel l'ecrivait depuis le
   * debut - *a constater comme presente ou absente; son contenu ne se capture
   * jamais* - mais **rien ne l'appliquait**: une verification adverse du
   * 2026-09-07 a montre que le lecteur aurait conserve ces libelles en clair,
   * plus douze passages d'historique, sans qu'aucun clic soit necessaire.
   *
   * Une interdiction que seul un humain peut lire n'est pas une garde.
   *
   * Ce qui reste: le COMPTE. C'est tout ce dont la conformite a besoin - la
   * liste est due ou elle ne l'est pas - et sa completude se verifie ailleurs,
   * dans CoproScope, apres pseudonymisation et sur des alias.
   *
   * Le rattachement etant declare par l'utilisateur, un utilisateur qui ne
   * declare rien ne beneficie pas de la garde. C'est assume et dit a l'ecran:
   * le plugin ne peut pas deviner ou son syndic range cette liste. */
  function biffer(rubriques, interdites) {
    if (!interdites || !interdites.size) return rubriques;
    /* Comparaison insensible a la casse: une declaration saisie `div` au lieu
     * de `DIV` desarmait la garde en silence, et aucun ecran ne disait que le
     * rattachement n'avait pris sur rien. */
    const cherchees = new Set([...interdites].map((c) => c.toUpperCase()));
    return rubriques.map((rubrique) => {
      const code = String(rubrique.rubrique_code || "").trim().toUpperCase();
      if (!cherchees.has(code)) return rubrique;
      /* DEUX formes de rubrique, et l'oubli de la seconde detruisait le
       * compte. Un index porte `pieces`; un etat de depenses porte `lignes`.
       * En ne biffant que `pieces`, une rubrique de depenses ressortait a ZERO
       * piece - et le bandeau annoncait alors, en rouge, un manque fabrique
       * par la garde elle-meme. C'est le pire cas de la doctrine: l'accusation
       * la plus lourde, nee de la protection la plus stricte. */
      const combien = (rubrique.pieces || rubrique.lignes || []).length;
      const biffe = {
        ...rubrique,
        contenu_biffe: true,
        /* Une entree neutre par entree vue: le compte survit, le contenu non. */
        pieces: Array.from({ length: combien }, () => ({
          groupe: "",
          libelle: "(contenu non releve)",
          nom_serveur: "",
        })),
      };
      if (rubrique.lignes) {
        biffe.lignes = Array.from({ length: combien }, () => ({
          colonnes: ["(contenu non releve)"],
          a_une_facture: false,
          nom_serveur: "",
        }));
      }
      return biffe;
    });
  }

  async function observer(options) {
    const debut = new Date().toISOString();
    const type = typeIndex();
    const charge = {
      format: "coproscope.extranet.releve/1",
      editeur: "coprodirecte",
      espace: location.pathname,
      /* L'adresse a sonder plus tard, sans onglet. On garde l'origine et le
       * chemin, JAMAIS la requete: chez l'editeur mesure, l'adresse porte un
       * jeton qui change a chaque chargement de page. Le stocker reviendrait a
       * ecrire un secret de session dans le stockage du plugin, et a le voir
       * ressortir dans le moindre export. */
      url: (typeof location.origin === "string" ? location.origin : "")
        + location.pathname,
      type_espace: typeEspace(),
      debut,
      pagination: pagine(),
      type,
      rubriques: [],
    };
    if (type === "depenses") charge.rubriques = await lireDepenses(options.avecNoms);
    else if (type === "documents") charge.rubriques = await lireIndexDocuments(options.avecNoms);

    /* Le biffage AVANT tout retour, et donc avant tout stockage, tout export et
     * tout affichage. Le placer plus loin laisserait une fenetre pendant
     * laquelle le contenu existe en memoire du plugin. */
    const config = await CS_VEILLE.reglages();
    charge.rubriques = biffer(
      charge.rubriques,
      CS_REFERENTIEL.rubriquesInterdites(config.rattachements)
    );
    charge.fin = new Date().toISOString();
    return charge;
  }

  /* La veille continue. Elle ne demande rien et n'envoie rien au syndic: elle
   * parcourt, empreint et journalise - trois gestes que la ligne rouge du
   * chantier autorise explicitement sans clic.
   *
   * Elle s'abstient dans trois cas, et chacun compte: la page ne porte aucun
   * index, l'intervalle n'est pas ecoule, ou la surveillance est arretee. Le
   * motif est trace pour que la fenetre puisse le dire au lieu de laisser
   * croire a une panne. */
  async function veiller() {
    if (typeIndex() === "aucun") return;
    const verdict = await CS_VEILLE.doitObserver(location.pathname, Date.now());
    if (!verdict.oui) return;
    const config = await CS_VEILLE.reglages();
    const charge = await observer({ avecNoms: config.avec_noms !== false });
    const ecart = await CS_VEILLE.enregistrer(charge);
    await annoncer(charge);
    if (ecart && (ecart.parus.length || ecart.disparus.length)) {
      chrome.runtime.sendMessage({
        action: "signaler",
        nombre: ecart.parus.length + ecart.disparus.length,
      });
    }
  }

  /* Le bandeau dans la page.
   *
   * Il est en `shadow DOM` ferme et en position fixe: rien de ce que porte
   * l'extranet n'est modifie, aucune regle de style ne fuit dans un sens ni
   * dans l'autre. Le lecteur continue de ne rien ecrire dans la page de
   * l'editeur - il pose un calque a cote.
   *
   * Il ne s'affiche que s'il a quelque chose a dire: un manque, une rubrique
   * non parcourue, ou un espace dont on veut se rappeler qu'il est
   * personnel. Un bandeau permanent qui repete *tout va bien* cesse d'etre lu
   * en deux jours, et c'est le manque qu'on perdrait. */
  function poserBandeau(lignes, alerte) {
    if (!lignes.length) return;
    /* Un document sans corps ni fabrique d'elements: ce n'est pas une page de
     * navigateur. Le lecteur doit continuer a rendre son releve - sa raison
     * d'etre - plutot que d'echouer sur un affichage. */
    if (!document.body || typeof document.createElement !== "function") return;
    const ancien = document.getElementById("cs-bandeau");
    if (ancien) ancien.remove();
    const hote = document.createElement("div");
    hote.id = "cs-bandeau";
    const ombre = hote.attachShadow({ mode: "closed" });
    const style = document.createElement("style");
    style.textContent =
      ":host{all:initial}" +
      ".b{position:fixed;right:16px;bottom:16px;z-index:2147483647;max-width:320px;" +
      "font:13px/1.45 system-ui,sans-serif;background:#101418;color:#e8e8e8;" +
      "border-left:4px solid " + (alerte ? "#ff8a80" : "#4cc38a") + ";" +
      "border-radius:6px;padding:10px 12px;box-shadow:0 6px 24px rgba(0,0,0,.35)}" +
      ".t{font-weight:600;margin-bottom:4px}" +
      "ul{margin:4px 0 0;padding-left:16px}" +
      "button{margin-top:8px;font:inherit;background:transparent;color:inherit;" +
      "border:1px solid currentColor;border-radius:4px;padding:3px 8px;cursor:pointer}";
    const boite = document.createElement("div");
    boite.className = "b";
    const titre = document.createElement("div");
    titre.className = "t";
    titre.textContent = "CoproScope - " + lignes[0];
    const liste = document.createElement("ul");
    for (const l of lignes.slice(1)) {
      const li = document.createElement("li");
      li.textContent = l;
      liste.appendChild(li);
    }
    const fermer = document.createElement("button");
    fermer.textContent = "Fermer";
    fermer.addEventListener("click", () => hote.remove());
    boite.append(titre, liste, fermer);
    ombre.append(style, boite);
    document.body.appendChild(hote);
  }

  async function annoncer(charge) {
    const config = await CS_VEILLE.reglages();
    /* Le compte se fait par OBLIGATION du decret, et non par rubrique de
     * l'editeur. Deux des trois manques nommes par Brice le 2026-09-06 sont
     * inexprimables autrement: la rubrique des contrats agrege quatre
     * obligations, et les releves bancaires vivent dans la categorie
     * fourre-tout. */
    const etats = CS_VEILLE.manquesLegaux(
      charge, config.rattachements, config.attendus, config.sans_objet
    );
    const manquants = CS_VEILLE.manquantes(etats);
    const nonParcourues = etats.filter((e) => e.etat === "NON_PARCOURUE");
    const aRattacher = etats.filter((e) => e.etat === "NON_RATTACHE");
    const lignes = [];

    /* Le type d'espace, demande par Brice le 2026-09-06. Il est affiche a
     * chaque fois qu'il y a un bandeau: deux espaces distincts servent des
     * choses differentes, et lire un constat sans savoir ou il a ete pris rend
     * le constat inutilisable. */
    /* Trois valeurs, pas deux. Le ternaire d'origine ne testait que
     * `personnel`, donc un espace INCONNU - le cas d'un second editeur -
     * s'affichait *La copropriete*. C'est une reponse fausse en silence, dans
     * un module dont la doctrine dit qu'un constat lu sans savoir ou il a ete
     * pris est inutilisable. */
    const espaces = {
      personnel: "Mon espace",
      collectif: "La copropriete",
    };
    const espace = espaces[typeEspace()] || "Espace non reconnu";

    if (manquants.length) {
      lignes.push(`${manquants.length} obligation${manquants.length > 1 ? "s" : ""} incomplete${manquants.length > 1 ? "s" : ""} - ${espace}`);
      for (const m of manquants) {
        /* On nomme l'obligation, pas le code de rubrique: `CON: 12 vues` ne
         * dit pas de quoi il manque, `Contrats d'assurance` le dit. */
        const compte = m.attendu !== undefined
          ? `${m.observe} vue${m.observe > 1 ? "s" : ""} sur ${m.attendu}`
          : "aucune piece";
        lignes.push(`${m.intitule}: ${compte}`);
      }
    } else if (aRattacher.length === etats.length) {
      /* Premier passage chez un syndic inconnu. Le dire vaut mieux qu'un
       * silence que l'utilisateur lira comme *tout va bien*. */
      lignes.push(`${espace} - ${etats.length} obligations a rattacher`);
      lignes.push("Le plugin ne sait pas encore ou votre syndic range chaque piece.");
      lignes.push("Aucun manque n'est affirme tant que vous ne le lui avez pas dit.");
    } else if (nonParcourues.length) {
      lignes.push(`${espace} - ${nonParcourues.length} obligation(s) non parcourue(s)`);
      lignes.push("Aucune absence n'est affirmable sur ce qui n'a pas ete regarde.");
    } else {
      return;
    }
    /* Un compte de manques sans son perimetre se lit comme une couverture
     * complete. La branche des non-parcourues ne s'executait jamais des qu'il
     * existait un manque: le bandeau rouge annoncait un chiffre en taisant
     * qu'il n'avait pas tout regarde. `veille.js` fait pourtant exactement
     * l'effort inverse pour les changements. */
    if (manquants.length && nonParcourues.length) {
      lignes.push(
        `${nonParcourues.length} autre(s) obligation(s) n'ont pas ete regardees: ` +
          "aucune absence n'y est affirmable."
      );
    }
    /* Le mot de la fin, et il est deliberement prudent. */
    lignes.push("Servi en apparence n'est pas conforme: seul l'examen des pieces le dit.");
    poserBandeau(lignes, manquants.length > 0);
  }

  veiller();

  chrome.runtime.onMessage.addListener((message, _expediteur, repondre) => {
    if (message && message.action === "observer") {
      observer({ avecNoms: message.avecNoms !== false })
        .then((charge) => repondre({ ok: true, charge }))
        .catch((e) => repondre({ ok: false, erreur: String(e) }));
      return true; /* reponse asynchrone */
    }
    return false;
  });
})();
