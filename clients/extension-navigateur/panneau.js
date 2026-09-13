/*
 * Le panneau de conformite: dix-huit obligations, et ce qu'on peut en dire.
 *
 * Blueprint: `docs/blueprint_popup_conformite_2026-09-07.md`.
 * Brouillon: `docs/assets/brouillon_popup_conformite_2026-09-07.html`.
 *
 * Il remplace le panneau qui listait les huit rubriques de l'editeur. Celui-la
 * ne savait exprimer qu'un des trois manques nommes par Brice le 2026-09-06:
 * la rubrique des contrats agrege quatre obligations distinctes, et les
 * releves bancaires sont ranges dans la categorie fourre-tout.
 *
 * TROIS REFUS, et ce sont eux la matiere de l'ecran.
 *
 * 1. Ne pas chiffrer un ecart sur un emplacement partage. Douze pieces dans
 *    *Contrats* ne disent pas combien sont des assurances. On affiche le
 *    compte et on dit pourquoi on ne le repartit pas: un chiffre faux se cite,
 *    une absence de chiffre ne nuit pas.
 * 2. Ne pas deviner un rattachement. Aucune page d'extranet ne cite le decret.
 *    Chez un syndic inconnu, l'ecran affiche dix-huit obligations a rattacher
 *    et ZERO manque affirme.
 * 3. Ne pas lire la liste des coproprietaires. Elle se constate presente ou
 *    absente; sa completude se verifie ailleurs, apres pseudonymisation.
 */

"use strict";

const CS_PANNEAU = (() => {
  const COLLEGES = [
    ["A", "Accessible a tous les coproprietaires"],
    ["B", "Propre a votre lot"],
    ["C", "Reserve au conseil syndical"],
  ];

  /* Le mot affiche pour chaque etat. Il est choisi, pas derive: `COMPLET` ne
   * doit jamais se lire `conforme`, et `NON_RATTACHE` ne doit jamais se lire
   * `manquant`. */
  const MOTS = {
    /* Neutre, pas vert. Le vert dit *c'est bon* et contredit tout le texte
     * prudent qui l'entoure: une rubrique peut porter le bon nombre de pieces
     * sans que ce soient les bonnes. Le vert doit rester pour ce qui a ete
     * verifie pour de vrai - donc, aujourd'hui, pour rien. */
    SERVI_EN_APPARENCE: ["servi en apparence", "e-inconnu"],
    NON_SERVI: ["aucune piece", "e-manque"],
    NON_RATTACHE: ["a rattacher", "e-inconnu"],
    NON_PARCOURUE: ["non parcourue", "e-attente"],
    SANS_OBJET: ["sans objet", "e-inconnu"],
  };

  function texte(parent, balise, contenu, classe) {
    const n = document.createElement(balise);
    if (contenu) n.textContent = contenu;
    if (classe) n.className = classe;
    parent.appendChild(n);
    return n;
  }

  function etiquette(etat) {
    if (etat.ecart > 0) {
      const n = etat.ecart;
      return [n + (n > 1 ? " manquent" : " manque"), "e-manque"];
    }
    return MOTS[etat.etat] || [etat.etat, "e-inconnu"];
  }

  /* La synthese: un nombre, sa base, et ce qui n'a pas ete regarde. Un compte
   * de manques sans son perimetre se lit comme une couverture complete. */
  function synthese(zone, etats, manques, espace, quand) {
    const bloc = texte(zone, "div", "", "synthese");
    const total = manques.length;
    const aRattacher = etats.filter((e) => e.etat === "NON_RATTACHE").length;
    const titre = texte(bloc, "b");

    /* Le premier ecran, et le moment ou tout se joue.
     *
     * Une qualification novice du 2026-09-07 s'est arretee ici: le titre
     * disait *Aucun manque affirme sur 18 obligations*, sur fond gris
     * tranquille. Le lecteur retenait *aucun manque*, refermait, et allait
     * dire que son syndic etait en regle. C'est l'inverse exact de ce que
     * l'outil veut dire, et c'etait le mot le plus dangereux du produit.
     *
     * Quand RIEN n'est rattache, on ne parle donc pas de manques du tout: on
     * dit ce qu'on ignore, et ce qu'on attend de la personne. */
    if (aRattacher === etats.length) {
      titre.textContent = `${etats.length} obligations : je ne sais pas encore ou votre syndic les range`;
      bloc.className = "synthese action";
      texte(bloc, "p",
        "Aucune page d'extranet ne cite le decret. Tant que vous ne me l'aurez "
        + "pas dit, je ne peux affirmer aucun manque - ce serait inventer.");
      const geste = texte(bloc, "button", "Commencer le rattachement", "primaire");
      geste.addEventListener("click", () => {
        const premiere = zone.querySelector("details.obligation");
        if (premiere) {
          premiere.open = true;
          premiere.scrollIntoView({ block: "start" });
        }
      });
      return;
    }

    titre.textContent = total
      ? `${total} obligation${total > 1 ? "s" : ""} incomplete${total > 1 ? "s" : ""} sur ${etats.length}`
      : `Aucun manque sur les ${etats.length - aRattacher} obligations que vous m'avez situees`;
    if (!total) bloc.className = "synthese calme";

    const contexte = texte(bloc, "p");
    contexte.textContent =
      (espace || "espace inconnu") + (quand ? " - releve du " + quand : "");

    const compteurs = texte(bloc, "div", "", "compteurs");
    const par = {};
    for (const e of etats) par[e.etat] = (par[e.etat] || 0) + 1;
    const lignes = [
      [total, "incomplete", "incompletes"],
      [par.SERVI_EN_APPARENCE || 0, "servie en apparence", "servies en apparence"],
      [par.NON_RATTACHE || 0, "a rattacher", "a rattacher"],
      [par.NON_PARCOURUE || 0, "non parcourue", "non parcourues"],
    ];
    for (const [n, un, plusieurs] of lignes) {
      if (!n) continue;
      texte(compteurs, "span", `${n} ${n > 1 ? plusieurs : un}`, "puce");
    }
  }

  /* Une obligation repliee ne montre que trois choses: son intitule, son
   * identifiant, son etat. C'est ce qui rend dix-huit lignes balayables. */
  function obligation(zone, etat, rubriques, surChangement) {
    const bloc = texte(zone, "details", "", "obligation");
    const tete = texte(bloc, "summary");
    const titre = texte(tete, "span", etat.intitule, "titre");
    texte(titre, "span", " " + etat.id, "ident");
    const [mot, classe] = etiquette(etat);
    texte(tete, "span", mot, "etat " + classe);

    const detail = texte(bloc, "div", "", "detail");

    if (etat.etat === "NON_PARCOURUE") {
      texte(detail, "p",
        "Cette rubrique n'a pas ete ouverte au dernier passage. Aucune absence "
        + "n'est affirmable tant qu'on n'a pas regarde.");
    } else if (etat.etat === "NON_RATTACHE") {
      texte(detail, "p",
        "Le plugin ne sait pas ou votre syndic range cette piece: aucune page "
        + "d'extranet ne cite le decret. Tant que vous ne le lui dites pas, "
        + "cette obligation ne compte ni comme servie ni comme manquante.");
    } else if (etat.observe !== undefined) {
      const ou = (etat.emplacements_parcourus || etat.emplacements || []).join(", ");
      let phrase = `${etat.observe} piece${etat.observe > 1 ? "s" : ""} vue${etat.observe > 1 ? "s" : ""}`;
      if (etat.attendu !== undefined) {
        /* D'ou vient le chiffre. L'outil savait deja le dire quand il vient de
         * la loi - *le texte en exige 3* - et se taisait quand il venait de
         * l'utilisateur. C'est l'inverse de ce qu'il faut: c'est avec SON
         * propre chiffre qu'il ira reprocher quelque chose a son syndic. */
        const origine = etat.attendu_source === "TEXTE"
          ? " exigees par le texte"
          : " que vous avez indiquees";
        phrase += ` sur ${etat.attendu}${origine}`;
      }
      if (ou) phrase += `, dans ${ou}`;
      texte(detail, "p", phrase + ".");
    }

    if (etat.ecart_non_calculable) {
      texte(detail, "div",
        "Le compte n'est pas attribuable. " + etat.ecart_non_calculable,
        "avert");
    }

    /* Le rattachement. Multiple, parce qu'une obligation peut etre servie a
     * plusieurs endroits - et une rubrique peut servir plusieurs obligations. */
    const champRat = texte(detail, "div", "", "champ");
    const labelRat = texte(champRat, "label", "Ou est-ce servi chez votre syndic ?");
    const choix = document.createElement("select");
    choix.multiple = true;
    choix.size = Math.min(4, Math.max(2, rubriques.length));
    choix.dataset.role = "rattachement";
    choix.dataset.id = etat.id;
    labelRat.setAttribute("for", "rat-" + etat.id);
    choix.id = "rat-" + etat.id;
    for (const [code, libelle] of rubriques) {
      const o = document.createElement("option");
      o.value = code;
      o.textContent = libelle;
      o.selected = (etat.emplacements || []).includes(code);
      choix.appendChild(o);
    }
    choix.addEventListener("change", surChangement);
    champRat.appendChild(choix);

    /* L'attendu. Ouvert seulement quand le texte ne le fixe pas: on ne laisse
     * pas saisir cinq proces-verbaux la ou l'article en exige trois. */
    if (etat.attendu_source === "TEXTE") {
      texte(detail, "p",
        `Le texte en exige ${etat.attendu}. Ce nombre ne se saisit pas.`);
    } else {
      const champAtt = texte(detail, "div", "", "champ");
      const l = texte(champAtt, "label", "Combien devrait-il y en avoir ?");
      const n = document.createElement("input");
      n.type = "number";
      n.min = "0";
      n.placeholder = "?";
      n.dataset.role = "attendu";
      n.dataset.id = etat.id;
      n.id = "att-" + etat.id;
      l.setAttribute("for", n.id);
      if (etat.attendu !== undefined) n.value = String(etat.attendu);
      n.addEventListener("change", surChangement);
      champAtt.appendChild(n);
    }

    texte(detail, "p", etat.fondement, "fondement");
    if (etat.reste_a_verifier) {
      const a = texte(detail, "div", "", "avert");
      texte(a, "strong", "Servi en apparence n'est pas conforme. ");
      a.appendChild(document.createTextNode(
        "Reste a verifier a la main: " + etat.reste_a_verifier));
    }
  }

  /* Dessine tout le panneau. `rubriques` est la liste des couples
   * (code, libelle) de l'editeur observe - donnee de profil, pas devinee. */
  function dessiner(zone, etats, manques, rubriques, contexte, surChangement) {
    zone.innerHTML = "";
    synthese(zone, etats, manques, contexte.espace, contexte.quand);
    for (const [code, nom] of COLLEGES) {
      const duCollege = etats.filter((e) => e.college === code);
      if (!duCollege.length) continue;
      texte(zone, "h2", nom);
      for (const etat of duCollege) {
        obligation(zone, etat, rubriques, surChangement);
      }
    }
  }

  /* Relit l'ecran. Un champ vide reste vide: on n'inscrit pas zero a la place
   * d'un inconnu - zero voudrait dire *aucune piece attendue ici*, ce qui est
   * un renseignement et non son absence. */
  function lire(zone) {
    const rattachements = {};
    const attendus = {};
    for (const el of zone.querySelectorAll("[data-role=rattachement]")) {
      const codes = [...el.selectedOptions].map((o) => o.value);
      if (codes.length) rattachements[el.dataset.id] = codes;
    }
    for (const el of zone.querySelectorAll("[data-role=attendu]")) {
      const v = el.value.trim();
      if (v !== "") attendus[el.dataset.id] = Number(v);
    }
    return { rattachements, attendus };
  }

  return { dessiner, lire, COLLEGES, MOTS };
})();
