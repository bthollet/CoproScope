/*
 * La cle d'emplacement d'une piece, ecrite une seule fois.
 *
 * Ce fichier existe a cause d'un defaut trouve le 2026-09-07. Trois
 * constructions coexistaient pour une meme ligne de depenses:
 *
 *   _extranet_releve.py  code | c0 | c1 | c2      toutes les colonnes
 *   veille.js            code | c0 | "c1 | c2"    trois composantes
 *   journal.js           code | c0 | "c0|c1|c2"   la premiere colonne DEUX FOIS
 *
 * Sur les documents les trois coincidaient, ce qui explique que personne ne
 * l'ait vu. Sur les depenses elles divergeaient - et c'est `journal.js` qui
 * produit les empreintes salees destinees au voisin. Le defaut n'aurait pas
 * leve d'erreur: il aurait rendu **zero concordance** entre deux journaux,
 * exactement sur la matiere que le voisin qui suit les factures met en commun,
 * et deux personnes auraient lu ce zero comme un desaccord entre elles.
 *
 * La reference est le Python, pour un motif mesure et non par convention:
 * toutes les colonnes entrent dans la cle, le montant compris, et c'est lui
 * qui fait tomber a zero les 21 collisions mesurees sur 729 lignes.
 *
 * AXE. La maniere dont un editeur decrit une piece est un degre de liberte:
 * ici un couple groupe/libelle pour un index de documents, la une ligne de
 * tableau de largeur inconnue pour un etat de depenses. Ce qui reste vrai le
 * long de l'axe: **une piece est decrite soit par un libelle, soit par une
 * suite de cellules, et la cle est la concatenation de ce qui la decrit,
 * precedee de sa rubrique**. Hors de ces deux formes, la fonction rend une cle
 * vide plutot qu'une cle fausse: une piece sans emplacement exploitable sort
 * de la comparaison, elle n'y entre pas sous un mauvais nom.
 */

"use strict";

const CS_CLE = (() => {
  /* Le meme separateur que `_extranet_schema.SEPARATEUR_EMPLACEMENT`. Ecrit
   * par code de caractere: un 0x1F colle dans une source est invisible a la
   * relecture, et une relecture qui ne voit pas un caractere ne le protege
   * pas. */
  const SEP = String.fromCharCode(31);

  function propres(valeurs) {
    return (valeurs || [])
      .map((v) => String(v === undefined || v === null ? "" : v).trim())
      .filter((v) => v !== "");
  }

  /* Rend `{cle, qualifiee}`. `qualifiee` faux veut dire *je n'ai pas de quoi
   * situer cette piece*, jamais *cette piece n'existe pas*. */
  function emplacementDe(rubriqueCode, piece) {
    const code = String(rubriqueCode || "").trim();
    if (!code) return { cle: "", qualifiee: false };

    /* Une ligne de tableau: toutes ses cellules pleines entrent dans la cle. */
    if (Array.isArray(piece.colonnes)) {
      const colonnes = propres(piece.colonnes);
      if (!colonnes.length) return { cle: "", qualifiee: false };
      return { cle: [code, ...colonnes].join(SEP), qualifiee: true };
    }

    /* Une piece d'index: rubrique, groupe, libelle. Le groupe est facultatif -
     * une seule rubrique sur huit en emploie sur l'index mesure - mais le
     * libelle est indispensable. */
    const groupe = String(piece.groupe || "").trim();
    const libelle = String(piece.libelle || "").trim();
    if (!libelle) return { cle: "", qualifiee: false };
    return { cle: [code, groupe, libelle].join(SEP), qualifiee: true };
  }

  return { SEP, emplacementDe };
})();
