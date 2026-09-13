/*
 * La sonde: savoir, sans onglet, si l'extranet est encore visible.
 *
 * Elle repond a la ligne que le document de conception designait comme *la plus
 * grave et pas encore traitee*: *la session peut expirer sans que personne le
 * voie*. Un outil de surveillance qui a cesse de voir, et qui ne le dit pas,
 * est pire qu'un outil absent - son silence se lit *rien n'a change*.
 *
 * ======================================================================
 * Ce que la sonde fait, et ce qu'elle ne fait pas
 * ======================================================================
 *
 * Elle fait UNE requete de lecture par espace surveille, et elle en tire une
 * seule chose: **est-ce que je vois encore l'index ?**
 *
 * Elle ne releve rien. Un service worker MV3 n'a pas de DOM, donc pas de
 * lecteur - et fabriquer un second lecteur a coups d'expressions regulieres
 * reviendrait a coder les modalites d'un editeur, ce que la regle du depot
 * interdit. Le releve reste le travail du script de contenu, quand une page
 * s'ouvre.
 *
 * Ce partage n'est pas un pis-aller: il place la seule chose qui doit tourner
 * sans surveillance - *est-ce que je vois encore ?* - dans le seul composant
 * qui peut tourner sans onglet.
 *
 * ======================================================================
 * AXE - la maniere dont un editeur signale une session finie
 * ======================================================================
 *
 * **Valeurs observees.** Une seule, chez Coprodirecte: la page de connexion est
 * servie en 200, a la place de l'index.
 *
 * **Ce qui reste invariant le long de l'axe.** Les facons de dire *vous n'etes
 * plus connecte* sont innombrables - redirection, 401, 403, page de connexion
 * en 200, corps JSON d'erreur, page vide. Ce qui ne varie pas: **une reponse
 * qui ne porte pas l'ancre de l'index ne prouve aucune absence de piece.** Elle
 * prouve seulement qu'on n'a pas vu l'index.
 *
 * **Ce que le code en fait.** Il ne cherche pas a reconnaitre une page de
 * connexion - il y en a autant que d'editeurs. Il cherche l'**ancre de
 * l'index**, declaree dans le profil. Presente: `VU`. Absente, quelle qu'en
 * soit la raison: `NON_EXPLORE`, avec le motif.
 *
 * **Hors des valeurs observees.** Un editeur dont le profil ne declare pas
 * d'ancre rend `NON_EXPLORE` a chaque sonde, avec le motif *aucune ancre
 * declaree*. La sonde devient inutile, elle ne devient jamais menteuse.
 */

"use strict";

const CS_SONDE = (() => {
  /* Les etats d'une tentative. Aucun ne conclut a une absence de piece: c'est
   * toute la difference entre *je n'ai pas vu* et *il n'y a rien*. */
  const VU = "VU";
  const NON_EXPLORE = "NON_EXPLORE";

  /* Pourquoi on n'a pas vu. Le motif voyage avec l'etat parce qu'un compteur
   * de tentatives ratees sans leur cause ne permet aucune action. */
  const SESSION_PERDUE = "session probablement finie";
  const INJOIGNABLE = "serveur injoignable";
  const REFUSE = "acces refuse";
  const SANS_ANCRE = "aucune ancre declaree pour cet editeur";

  /* Decide a partir d'une reponse deja obtenue. Fonction pure: c'est elle qui
   * porte le jugement, et c'est elle qu'on peut eprouver hors navigateur. */
  function juger(statut, corps, ancre) {
    if (!ancre) {
      return { etat: NON_EXPLORE, motif: SANS_ANCRE };
    }
    if (statut === 401 || statut === 403) {
      return { etat: NON_EXPLORE, motif: REFUSE, statut };
    }
    if (statut >= 500 || statut === 0) {
      return { etat: NON_EXPLORE, motif: INJOIGNABLE, statut };
    }
    if (typeof corps === "string" && corps.includes(ancre)) {
      return { etat: VU, statut };
    }
    /* Statut 200 mais pas d'index: chez l'editeur mesure, c'est la page de
     * connexion. Ailleurs ce sera autre chose - et le mot reste prudent
     * (*probablement*) parce qu'on ne l'a pas verifie. */
    return { etat: NON_EXPLORE, motif: SESSION_PERDUE, statut };
  }

  /* Une tentative datee, qu'elle ait abouti ou non.
   *
   * C'est la garde numero 2 de l'arbitrage A2: un ecran qui ne montrerait que
   * le dernier SUCCES laisserait croire que rien n'a change, alors que plus
   * rien n'est observe depuis trois semaines. La tentative et le succes sont
   * donc deux dates distinctes, et les deux s'affichent. */
  async function sonder(url, ancre, quand, chercher) {
    const recuperer = chercher || fetch;
    let verdict;
    /* Sans ancre declaree, le verdict est connu d'avance: `NON_EXPLORE`. Emettre
     * quand meme la requete serait du trafic sur la session authentifiee de
     * l'utilisateur, toutes les six heures, chez un editeur dont on ne sait
     * rien - a valeur informationnelle nulle **par construction**. Constat
     * d'une relecture de doctrine du 2026-09-07. */
    if (!ancre) {
      return { url, quand, etat: NON_EXPLORE, motif: SANS_ANCRE };
    }
    try {
      /* `credentials: include` emploie la session que l'utilisateur a lui-meme
       * ouverte. La sonde n'authentifie rien et ne connait aucun mot de passe:
       * elle regarde avec les yeux qu'on lui a laisses. */
      const reponse = await recuperer(url, {
        credentials: "include",
        redirect: "follow",
        method: "GET",
      });
      const corps = await reponse.text();
      verdict = juger(reponse.status, corps, ancre);
    } catch (e) {
      verdict = { etat: NON_EXPLORE, motif: INJOIGNABLE, erreur: String(e) };
    }
    return { url, quand, ...verdict };
  }

  /* Le journal des tentatives, borne. On garde le dernier succes SEPAREMENT
   * de la derniere tentative: c'est l'ecart entre les deux qui dit qu'on est
   * devenu aveugle, et cet ecart disparaitrait si une seule date etait tenue. */
  function fusionner(etat, tentative, maxHistorique) {
    const precedent = etat || {};
    const historique = [tentative, ...(precedent.historique || [])].slice(
      0,
      maxHistorique || 20
    );
    return {
      derniere_tentative: tentative,
      dernier_succes:
        tentative.etat === VU ? tentative : precedent.dernier_succes || null,
      historique,
      /* Combien de tentatives ratees d'affilee. Au-dela de deux, ce n'est plus
       * un incident, c'est un etat - et l'ecran doit le dire autrement. */
      echecs_consecutifs:
        tentative.etat === VU ? 0 : (precedent.echecs_consecutifs || 0) + 1,
    };
  }

  /* Ce que l'ecran doit dire de l'etat de la surveillance. Rendu en donnees,
   * pour que le texte vive dans la fenetre et le jugement ici. */
  function diagnostic(etat, maintenant) {
    if (!etat || !etat.derniere_tentative) {
      return { niveau: "AUCUNE", jours_sans_succes: null };
    }
    const succes = etat.dernier_succes;
    if (!succes) {
      return {
        niveau: "JAMAIS_VU",
        motif: etat.derniere_tentative.motif,
        jours_sans_succes: null,
      };
    }
    const jours = (maintenant - Date.parse(succes.quand)) / 86400000;
    if (etat.echecs_consecutifs >= 2) {
      return {
        niveau: "AVEUGLE",
        motif: etat.derniere_tentative.motif,
        echecs: etat.echecs_consecutifs,
        jours_sans_succes: jours,
      };
    }
    return { niveau: "VOIT", jours_sans_succes: jours };
  }

  return {
    VU,
    NON_EXPLORE,
    SESSION_PERDUE,
    INJOIGNABLE,
    REFUSE,
    SANS_ANCRE,
    juger,
    sonder,
    fusionner,
    diagnostic,
  };
})();

/* Le service worker n'a pas de modules: on expose sur `globalThis` quand on y
 * est, et on laisse la constante visible quand on est charge en script. */
if (typeof globalThis !== "undefined") globalThis.CS_SONDE = CS_SONDE;
