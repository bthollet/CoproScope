/*
 * Veille continue: observer sans qu'on le demande, et signaler ce qui bouge.
 *
 * Demande de Brice du 2026-09-06: *"je veux que ca tourne en continu"*. Elle est
 * dans sa regle, et c'est pour cela qu'elle s'applique sans discussion: la ligne
 * rouge autorise sans clic *parcourir, empreindre, telecharger, journaliser,
 * alerter*, et n'exige un geste humain que pour ce qui **sort vers le syndic**.
 * Le declenchement manuel de la premiere version etait une prudence
 * supplementaire, pas cette regle.
 *
 * ==================================================================
 * Ce que ce module signale, et ce qu'il se refuse a dire
 * ==================================================================
 *
 * Il compare deux passages et rend un nombre d'emplacements qui ont **bouge**.
 * Il ne dit jamais *retrait*, jamais *le syndic a supprime*, et il n'affiche
 * aucun verdict.
 *
 * Ce n'est pas de la timidite, c'est la seule chose qu'il puisse honnetement
 * dire. Un retrait ne s'affirme que si trois conditions sont reunies aux deux
 * dates - rubrique parcourue, cloture permettant de conclure a une absence, cle
 * injective - et ces regles vivent dans CoproScope ou elles sont testees. Les
 * reecrire ici produirait une seconde implantation qui divergerait, et la
 * divergence porterait sur le constat le plus accusatoire que l'outil sache
 * produire.
 *
 * L'extension mesure. CoproScope juge. La pastille compte, elle n'accuse pas.
 *
 * ==================================================================
 * Pourquoi une temporisation, et pourquoi elle n'est pas un detail
 * ==================================================================
 *
 * Observer a chaque chargement de page produirait des dizaines de passages
 * identiques par jour - et autant de fois 115 requetes de tete. Le journal
 * deviendrait illisible et la charge sur l'extranet injustifiable.
 *
 * Un passage par espace et par periode suffit: ce qu'on cherche est ce qui
 * change d'un jour a l'autre, pas d'un clic a l'autre.
 *
 * ==================================================================
 * Ce qui est garde, et pourquoi si peu
 * ==================================================================
 *
 * Le stockage d'une extension est limite. On garde donc, par espace:
 *
 * - **le dernier releve**, qui sert de point de comparaison;
 * - **les changements**, qui sont petits et sont toute la valeur du journal;
 * - **un historique borne** des derniers releves, pour pouvoir exporter plus
 *   qu'un instantane.
 *
 * L'histoire longue appartient a CoproScope. Une extension qui pretendrait la
 * tenir finirait par la perdre en silence, le jour ou le quota est atteint -
 * et une perte silencieuse est le defaut que tout ce lot cherche a eviter.
 */

"use strict";

var CS_VEILLE = (() => {
  const CLE_REGLAGES = "veille_reglages";
  const REGLAGES_DEFAUT = {
    active: true,
    intervalle_heures: 6,
    historique_max: 12,
    /* Ce que l'humain SAIT devoir exister, et que rien dans la page ne dit.
     *
     * Demande de Brice le 2026-09-06: *"coproscope doit prevoir une valeur
     * nombre de pieces du RC: je sais qu'il en manque 6 chez moi, sur 24"*.
     *
     * C'est un renseignement qu'aucune observation ne peut produire: seul
     * quelqu'un qui connait le dossier sait combien de pieces compte le
     * reglement de copropriete. L'attendu declare transforme donc un *je ne
     * sais pas* en ecart chiffre - et c'est exactement ce que le referentiel
     * appelle passer d'INDETERMINE a un constat.
     *
     * Il n'est jamais devine ni deduit d'un passage precedent: une valeur
     * deduite de l'observation ne pourrait, par construction, jamais reveler
     * un manque. */
    attendus: {},

    /* Ou chaque obligation du decret est servie chez CE syndic. Declare, et
     * jamais devine: aucune page d'extranet ne cite le decret, donc le
     * rattachement n'est pas observable. Vide par defaut - un editeur inconnu
     * rend dix-huit fois `NON_RATTACHE` et zero manque. */
    rattachements: {},

    /* Les obligations qui ne s'appliquent pas ici: dispense votee a la
     * majorite de l'article 25, syndic non professionnel, absence de fonds de
     * travaux. Aucune ne s'observe sur l'extranet. */
    sans_objet: [],
  };

  const cleEtat = (espace) => "veille_etat:" + espace;
  const cleHistorique = (espace) => "veille_historique:" + espace;
  const CLE_CHANGEMENTS = "veille_changements";

  async function reglages() {
    const stocke = await chrome.storage.local.get(CLE_REGLAGES);
    return Object.assign({}, REGLAGES_DEFAUT, stocke[CLE_REGLAGES] || {});
  }

  async function definirReglages(nouveaux) {
    const actuels = await reglages();
    await chrome.storage.local.set({
      [CLE_REGLAGES]: Object.assign({}, actuels, nouveaux),
    });
  }

  /* Les emplacements d'un releve, sous la meme forme que CoproScope les
   * construit. Le separateur doit etre le meme, sinon rien ne se recoupera. */

  function emplacements(releve, rubriquesRetenues) {
    const sortie = [];
    for (const rubrique of releve.rubriques || []) {
      if (!rubrique.presente) continue;
      if (rubriquesRetenues && !rubriquesRetenues.has(rubrique.rubrique_code)) continue;
      const pieces = rubrique.pieces || (rubrique.lignes || []).filter((l) => l.a_une_facture);
      for (const piece of pieces) {
        const { cle, qualifiee } = CS_CLE.emplacementDe(
          rubrique.rubrique_code,
          piece
        );
        if (!qualifiee) continue;
        sortie.push(cle);
      }
    }
    return sortie;
  }

  function parcourues(releve) {
    return new Set(
      (releve.rubriques || [])
        .filter((r) => r.presente)
        .map((r) => r.rubrique_code)
    );
  }

  /* Difference d'ensembles, et rien de plus.
   *
   * `parus` et `disparus` sont des CONSTATS DE PRESENCE, pas des verdicts. Une
   * piece disparue de cette liste peut avoir ete retiree, renommee, deplacee,
   * ou se trouver dans une rubrique que le passage n'a pas parcourue. Trancher
   * entre ces cas demande la couverture et l'injectivite, qui sont verifiees
   * dans CoproScope. */
  function comparer(avant, apres) {
    /* La regle de couverture, appliquee au niveau pauvre.
     *
     * Defaut trouve le 2026-09-06 en repondant a la question *qu'est-ce qu'un
     * changement pour lui*: la comparaison ignorait si une rubrique avait ete
     * parcourue **aux deux dates**. Une rubrique qui n'aurait pas charge une
     * fois aurait fait disparaitre toutes ses pieces d'un coup - une bouffee de
     * fausses alertes, et sur le constat le plus accusatoire de l'outil.
     *
     * On ne compare donc que les rubriques presentes des deux cotes. Les autres
     * ne produisent aucun changement, et leur liste est rendue pour que la
     * fenetre puisse dire ce qui n'a pas ete regarde plutot que de laisser
     * croire a un silence. */
    const ra = parcourues(avant);
    const rb = parcourues(apres);
    const communes = new Set([...ra].filter((c) => rb.has(c)));
    const a = new Set(emplacements(avant, communes));
    const b = new Set(emplacements(apres, communes));
    return {
      parus: [...b].filter((x) => !a.has(x)),
      disparus: [...a].filter((x) => !b.has(x)),
      hors_comparaison: [...new Set([...ra, ...rb])].filter((c) => !communes.has(c)),
    };
  }

  async function dernier(espace) {
    const stocke = await chrome.storage.local.get(cleEtat(espace));
    return stocke[cleEtat(espace)] || null;
  }

  async function doitObserver(espace, maintenant) {
    const config = await reglages();
    if (!config.active) return { oui: false, motif: "veille desactivee" };
    const etat = await dernier(espace);
    if (!etat) return { oui: true, motif: "premier passage" };
    const ecoule = (maintenant - Date.parse(etat.debut)) / 3600000;
    if (ecoule < config.intervalle_heures) {
      return {
        oui: false,
        motif: `dernier passage il y a ${ecoule.toFixed(1)} h`,
      };
    }
    return { oui: true, motif: "intervalle ecoule" };
  }

  /* Enregistre un releve, rend ce qui a bouge depuis le precedent.
   *
   * Le premier passage ne produit AUCUN changement: il constitue la reference.
   * Sans cette precaution, la pastille afficherait le jour de l'installation un
   * nombre egal a la totalite de l'index. */
  async function enregistrer(releve) {
    const espace = releve.espace;
    const precedent = await dernier(espace);
    const ecart = precedent ? comparer(precedent, releve) : null;

    const stocke = await chrome.storage.local.get(cleHistorique(espace));
    const historique = stocke[cleHistorique(espace)] || [];
    historique.push(releve);
    const config = await reglages();
    while (historique.length > config.historique_max) historique.shift();

    const a_ecrire = {
      [cleEtat(espace)]: releve,
      [cleHistorique(espace)]: historique,
    };

    if (ecart && (ecart.parus.length || ecart.disparus.length)) {
      const anciens = await chrome.storage.local.get(CLE_CHANGEMENTS);
      const changements = anciens[CLE_CHANGEMENTS] || [];
      changements.push({
        espace,
        avant: precedent.debut,
        apres: releve.debut,
        parus: ecart.parus.length,
        disparus: ecart.disparus.length,
        /* Ce qui n'a pas pu etre compare est rendu avec le reste: un compte de
         * changements sans son perimetre se lit comme une couverture complete. */
        hors_comparaison: ecart.hors_comparaison,
        /* Les emplacements sont gardes pour l'export, pas pour l'affichage:
         * un libelle a l'ecran donnerait l'illusion d'un constat etabli. */
        detail: ecart,
      });
      a_ecrire[CLE_CHANGEMENTS] = changements;
    }

    await chrome.storage.local.set(a_ecrire);
    return ecart;
  }

  /* Les manques: ce qui est attendu, ce qui est vu, et l'ecart.
   *
   * Trois etats seulement, et le troisieme est le plus important:
   *
   * - `MANQUE`  : moins de pieces que declare. Ecart chiffre, pas une opinion.
   * - `COMPLET` : autant ou plus. **Ne veut pas dire conforme.**
   * - `INCONNU` : aucun attendu declare. L'outil ne devine pas.
   *
   * La distinction entre COMPLET et conforme est la mise en garde de Brice, et
   * elle est fondamentale: *"attention au faux servi"*. Une rubrique peut
   * porter le bon nombre de pieces sans que ces pieces soient les bonnes - une
   * attestation perimee, un projet au lieu d'un contrat signe, un extrait au
   * lieu d'un proces-verbal. Trancher demande de LIRE les pieces, ce que fait
   * CoproScope et que l'extension ne fera jamais.
   *
   * D'ou le vocabulaire retenu a l'ecran: **servi en apparence**, jamais
   * *conforme*. */
  function manques(releve, attendus) {
    const sortie = [];
    for (const rubrique of releve.rubriques || []) {
      if (!rubrique.presente) {
        sortie.push({ code: rubrique.rubrique_code, etat: "NON_PARCOURUE" });
        continue;
      }
      const pieces = rubrique.pieces || (rubrique.lignes || []).filter((l) => l.a_une_facture);
      const attendu = (attendus || {})[rubrique.rubrique_code];
      if (attendu === undefined || attendu === null || attendu === "") {
        sortie.push({ code: rubrique.rubrique_code, observe: pieces.length, etat: "INCONNU" });
        continue;
      }
      const ecart = Number(attendu) - pieces.length;
      sortie.push({
        code: rubrique.rubrique_code,
        observe: pieces.length,
        attendu: Number(attendu),
        ecart: ecart > 0 ? ecart : 0,
        etat: ecart > 0 ? "MANQUE" : "COMPLET",
      });
    }
    return sortie;
  }

  /* ------------------------------------------------------------------ */
  /* Les manques au regard du decret, et non de l'editeur                 */
  /* ------------------------------------------------------------------ */

  /* Le compte par rubrique d'editeur ci-dessus ne sait pas exprimer deux des
   * trois manques que Brice a nommes le 2026-09-06. Les releves bancaires sont
   * ranges dans la categorie fourre-tout, donc un attendu pose sur elle les
   * melange a tout le reste; et la rubrique des contrats agrege QUATRE
   * obligations distinctes du decret. D'ou ce second etage, indexe sur les
   * obligations et non sur les rubriques.
   *
   * Miroir de `_extranet_conformite.etat_par_obligation`. Il rend les memes
   * etats, avec la meme prudence: un emplacement partage par plusieurs
   * obligations interdit de chiffrer un ecart, parce qu'un chiffre faux se
   * cite et nuit plus qu'une absence de chiffre. */
  function manquesLegaux(releve, rattachements, attendus, sansObjet) {
    rattachements = rattachements || {};
    attendus = attendus || {};
    /* Un identifiant inconnu etait avale en silence: une lettre en moins et
     * l'obligation qu'on croyait ecartee produisait un manquement contre un
     * syndic irreprochable. */
    const dispenses = new Set();
    for (const id of sansObjet || []) {
      if (!CS_REFERENTIEL.PAR_ID.has(id)) {
        throw new Error("Obligation inconnue dans sans_objet: " + id);
      }
      dispenses.add(id);
    }

    const vu = new Map();
    for (const rubrique of releve.rubriques || []) {
      const pieces =
        rubrique.pieces || (rubrique.lignes || []).filter((l) => l.a_une_facture);
      /* Le meme nettoyage que cote Python: un code entoure d'espaces doit
       * designer la meme rubrique des deux cotes. */
      vu.set(String(rubrique.rubrique_code || "").trim(), {
        parcourue: !!rubrique.presente,
        nb: (pieces || []).length,
      });
    }

    /* Un emplacement est partage des qu'il sert plus d'une obligation. C'est
     * mesure sur la declaration elle-meme, pas suppose. */
    const compte = new Map();
    for (const codes of Object.values(rattachements)) {
      for (const code of new Set(codes)) {
        compte.set(code, (compte.get(code) || 0) + 1);
      }
    }

    const sortie = [];
    for (const o of CS_REFERENTIEL.OBLIGATIONS) {
      const ligne = {
        id: o.id,
        college: o.college,
        intitule: o.intitule,
        fondement: o.fondement,
        reste_a_verifier: o.reste_a_verifier,
        emplacements: rattachements[o.id] || [],
      };
      if (dispenses.has(o.id)) {
        ligne.etat = "SANS_OBJET";
        sortie.push(ligne);
        continue;
      }
      /* Nettoyage de la declaration humaine, identique au Python. Un code vide
       * ou entoure d'espaces se serait deguise en *non parcourue* - donc *je
       * n'ai pas regarde* - alors que c'est *je ne sais pas ou c'est servi*. Et
       * un code declare deux fois aurait double le compte observe, ce qui
       * efface un manquement reel sans aucune alerte. */
      ligne.emplacements = [
        ...new Set(
          ligne.emplacements
            .map((c) => String(c === undefined || c === null ? "" : c).trim())
            .filter((c) => c !== "")
        ),
      ];
      if (!ligne.emplacements.length) {
        /* NON_RATTACHE veut dire *je ne sais pas ou c'est servi ici*, jamais
         * *ce n'est pas servi*. C'est ce qui fait qu'un editeur inconnu ne
         * produit aucun manquement. */
        ligne.etat = "NON_RATTACHE";
        ligne.compte = "AUCUN_EMPLACEMENT";
        sortie.push(ligne);
        continue;
      }
      const parcourus = ligne.emplacements.filter((c) => (vu.get(c) || {}).parcourue);
      if (!parcourus.length) {
        ligne.etat = "NON_PARCOURUE";
        ligne.compte = "AUCUN_EMPLACEMENT";
        sortie.push(ligne);
        continue;
      }
      const observe = parcourus.reduce((n, c) => n + vu.get(c).nb, 0);
      ligne.observe = observe;
      /* Les memes champs que le Python: sans eux, le test de conformite
       * comparerait deux rendus differents en croyant les trouver egaux. */
      ligne.emplacements_parcourus = parcourus;
      if (parcourus.length < ligne.emplacements.length) {
        ligne.emplacements_non_parcourus = ligne.emplacements.filter(
          (c) => !parcourus.includes(c)
        );
      }
      ligne.etat = observe ? "SERVI_EN_APPARENCE" : "NON_SERVI";
      if (o.condition) ligne.condition = o.condition;
      const partage = parcourus.some((c) => (compte.get(c) || 0) > 1);
      const incomplet = parcourus.length < ligne.emplacements.length;
      ligne.compte = partage
        ? "EMPLACEMENT_PARTAGE"
        : incomplet
          ? "COUVERTURE_INCOMPLETE"
          : "EMPLACEMENT_EXCLUSIF";

      let attendu = null;
      if (o.attendu_source === "TEXTE" && o.attendu !== undefined) {
        attendu = o.attendu;
        ligne.attendu_source = "TEXTE";
      } else if (CS_REFERENTIEL.NON_COMPTABLES.has(o.attendu_source)) {
        /* L'observation ne sait pas compter cette unite. Accepter un attendu
         * declare produirait un ecart chiffre sur autre chose que ce que le
         * texte demande de compter. */
        attendu = null;
      } else if (attendus[o.id] !== undefined && attendus[o.id] !== null
                 && String(attendus[o.id]).trim() !== "") {
        /* Tronque, comme `int()` cote Python: deux lectures qui arrondiraient
         * differemment produiraient deux ecarts differents pour la meme
         * saisie. */
        attendu = Math.trunc(Number(attendus[o.id]));
        if (!Number.isFinite(attendu)) {
          attendu = null;
        } else {
          ligne.attendu_source = "DECLARE";
        }
      }
      if (attendu !== null) {
        ligne.attendu = attendu;
        if (ligne.compte === "EMPLACEMENT_EXCLUSIF") {
          ligne.ecart = Math.max(0, attendu - observe);
          const reserve = CS_REFERENTIEL.RESERVES[o.attendu_source];
          if (reserve) ligne.reserve_sur_le_compte = reserve;
        } else if (partage) {
          /* Nommer les autres obligations, et pas seulement dire *plusieurs*:
           * *plusieurs* sonne comme une excuse, la liste se lit comme de
           * l'honnetete. */
          const voisines = [];
          for (const [id, autres] of Object.entries(rattachements)) {
            if (id === o.id) continue;
            if ((autres || []).some((c) => parcourus.includes(String(c).trim()))) {
              voisines.push(id);
            }
          }
          const noms = voisines
            .map((id) => (CS_REFERENTIEL.PAR_ID.get(id) || {}).intitule)
            .filter(Boolean);
          ligne.partage_avec = voisines;
          ligne.ecart_non_calculable =
            "On ne peut pas dire combien des " + observe +
            " pieces vues relevent de cette obligation." +
            (noms.length ? " Cette rubrique sert aussi: " + noms.join("; ") + "." : "");
        } else {
          /* La regle de couverture, appliquee a l'ecart. Chiffrer un manque
           * sur une rubrique qu'on n'a pas ouverte revient a compter comme
           * absentes des pieces qu'on n'a pas regardees. */
          const manquants = ligne.emplacements
            .filter((c) => !parcourus.includes(c))
            .join(", ");
          ligne.ecart_non_calculable =
            "Une partie des emplacements n'a pas ete parcourue (" +
            manquants + "): le compte observe est incomplet.";
        }
      }
      sortie.push(ligne);
    }
    return sortie;
  }

  /* Les obligations dont il manque des pieces, deduplication faite. */
  function manquantes(etats) {
    /* Un attendu declare a ZERO veut dire *aucune piece attendue ici*: c'est un
     * renseignement, pas une absence de renseignement. Zero observe sur zero
     * attendu est donc satisfait, et `NON_SERVI` seul ne suffit pas. */
    const candidats = new Set(
      etats
        .filter((e) => {
          /* Une obligation que le texte CONDITIONNE, et dont rien n'a ete vu,
           * ne devient jamais un manque: la condition ne s'observe pas. La
           * preuve qu'elle s'applique est la presence d'au moins une piece -
           * on ne sert pas la part d'un fonds de travaux qui n'existe pas. */
          if (e.condition && !(e.observe || 0)) return false;
          if (e.ecart > 0) return true;
          if (e.etat !== "NON_SERVI") return false;
          if (e.attendu !== undefined) return e.attendu > (e.observe || 0);
          if (e.condition) return false;
          return true;
        })
        .map((e) => e.id)
    );
    const gardes = CS_REFERENTIEL.dedupliquer(candidats);
    return etats.filter((e) => gardes.has(e.id));
  }

  async function changements() {
    const stocke = await chrome.storage.local.get(CLE_CHANGEMENTS);
    return stocke[CLE_CHANGEMENTS] || [];
  }

  /* Tout effacer. Le plugin savait ecrire douze passages d'historique et
   * n'avait AUCUNE commande pour les reprendre - constat d'une relecture de
   * doctrine le 2026-09-07. C'etait la garantie que toute fuite passee restait
   * permanente, y compris pour quelqu'un qui decouvrirait apres coup que la
   * liste de ses coproprietaires y dormait.
   *
   * Les reglages survivent: effacer les releves ne doit pas obliger a
   * redeclarer dix-huit rattachements. */
  async function effacerReleves() {
    const tout = await chrome.storage.local.get(null);
    const aJeter = Object.keys(tout).filter(
      (c) =>
        c.startsWith("veille_etat:") ||
        c.startsWith("veille_historique:") ||
        c.startsWith("sonde_etat:") ||
        c === CLE_CHANGEMENTS
    );
    if (aJeter.length) await chrome.storage.local.remove(aJeter);
    return { efface: aJeter.length };
  }

  async function oublierChangements() {
    await chrome.storage.local.set({ [CLE_CHANGEMENTS]: [] });
  }

  return {
    reglages,
    definirReglages,
    doitObserver,
    enregistrer,
    dernier,
    comparer,
    emplacements,
    parcourues,
    manques,
    manquesLegaux,
    manquantes,
    changements,
    oublierChangements,
    effacerReleves,
  };
})();
