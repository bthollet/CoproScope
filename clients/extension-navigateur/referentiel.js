/*
 * Les 18 obligations du decret 2019-502, cote navigateur.
 *
 * FICHIER GENERE. Ne pas le modifier a la main: relancer
 * `tools/generer_referentiel_js.py`. La source est
 * `server/src/coproscope/modules/_extranet_referentiel.py`, et
 * `server/tests/test_extension_conformite.py` verifie que les deux listes
 * coincident champ par champ - un fondement qui derive serait cite devant un
 * syndic sous une version que personne n'a lue.
 *
 * Le plugin en a besoin parce que l'integration a CoproScope est reportee: la
 * fenetre doit pouvoir dire ce qui manque sans qu'aucun serveur ne tourne.
 *
 * CE QUE CE FICHIER NE PORTE PAS. Le rattachement d'une obligation a une
 * rubrique d'editeur n'y est pas, et n'y sera jamais: il n'est pas observable,
 * aucune page d'extranet ne citant le decret. Il est declare par l'utilisateur
 * et vit dans `chrome.storage.local`. Un editeur sans rattachement declare rend
 * 18 fois `NON_RATTACHE` - *je ne sais pas ou c'est servi ici* - et zero
 * manquement.
 */

"use strict";

const CS_REFERENTIEL = (() => {
  const OBLIGATIONS = [
    {"id": "EXT-A-01", "college": "A", "intitule": "Reglement de copropriete, etat descriptif de division et actes les modifiant", "reste_a_verifier": "Uniquement s'ils ont ete publies: la condition de publication ecarte les actes non publies, qui ne sont pas dus.", "fondement": "decret 2019-502 du 23 mai 2019, article 1er (LEGIARTI000042412719, version du 2020-12-31, lue le 2026-09-03)", "attendu_source": "DECLARE", "condition": "seuls les actes PUBLIES sont dus"},
    {"id": "EXT-A-02", "college": "A", "intitule": "Derniere fiche synthetique de la copropriete", "reste_a_verifier": "Millesime coherent avec la mise a jour annuelle de l'article 8-2.", "fondement": "decret 2019-502 du 23 mai 2019, article 1er (LEGIARTI000042412719, version du 2020-12-31, lue le 2026-09-03)", "attendu_source": "TEXTE", "attendu": 1},
    {"id": "EXT-A-03", "college": "A", "intitule": "Carnet d'entretien de l'immeuble", "reste_a_verifier": "Derniere mise a jour datee.", "fondement": "decret 2019-502 du 23 mai 2019, article 1er (LEGIARTI000042412719, version du 2020-12-31, lue le 2026-09-03)", "attendu_source": "TEXTE", "attendu": 1},
    {"id": "EXT-A-04", "college": "A", "intitule": "Diagnostics techniques des parties communes", "reste_a_verifier": "En cours de validite: le texte ne vise que ceux-la. Le nombre depend des equipements de l'immeuble.", "fondement": "decret 2019-502 du 23 mai 2019, article 1er (LEGIARTI000042412719, version du 2020-12-31, lue le 2026-09-03)", "attendu_source": "DECLARE", "condition": "seuls les diagnostics APPLICABLES a cet immeuble sont dus"},
    {"id": "EXT-A-05", "college": "A", "intitule": "Contrats d'assurance de l'immeuble conclus par le syndic", "reste_a_verifier": "En cours de validite. Une attestation echue ne satisfait pas le texte, et occupe pourtant la rubrique.", "fondement": "decret 2019-502 du 23 mai 2019, article 1er (LEGIARTI000042412719, version du 2020-12-31, lue le 2026-09-03)", "attendu_source": "DECLARE"},
    {"id": "EXT-A-06", "college": "A", "intitule": "Ensemble des contrats et marches en cours signes par le syndic", "reste_a_verifier": "Se recouvre avec les contrats d'entretien: un contrat d'entretien est aussi un contrat en cours.", "fondement": "decret 2019-502 du 23 mai 2019, article 1er (LEGIARTI000042412719, version du 2020-12-31, lue le 2026-09-03)", "attendu_source": "DECLARE", "recouvre": ["EXT-A-07"]},
    {"id": "EXT-A-07", "college": "A", "intitule": "Contrats d'entretien et de maintenance des equipements communs en cours", "reste_a_verifier": "Rapprochement possible avec les charges. Se recouvre avec l'ensemble des contrats en cours.", "fondement": "decret 2019-502 du 23 mai 2019, article 1er (LEGIARTI000042412719, version du 2020-12-31, lue le 2026-09-03)", "attendu_source": "DECLARE", "recouvre": ["EXT-A-06"]},
    {"id": "EXT-A-08", "college": "A", "intitule": "Proces-verbaux des trois dernieres assemblees generales annuelles appelees a connaitre des comptes", "reste_a_verifier": "L'unite est l'assemblee appelee a connaitre des comptes, pas l'exercice ni l'assemblee. Deux assemblees dans l'annee dont une seule sur les comptes n'en comptent qu'une.", "fondement": "decret 2019-502 du 23 mai 2019, article 1er (LEGIARTI000042412719, version du 2020-12-31, lue le 2026-09-03)", "attendu_source": "TEXTE", "attendu": 3},
    {"id": "EXT-A-09", "college": "A", "intitule": "Contrat de syndic en cours", "reste_a_verifier": "Periode de mandat couvrant la date d'observation.", "fondement": "decret 2019-502 du 23 mai 2019, article 1er (LEGIARTI000042412719, version du 2020-12-31, lue le 2026-09-03)", "attendu_source": "TEXTE", "attendu": 1},
    {"id": "EXT-B-01", "college": "B", "intitule": "Compte individuel du coproprietaire", "reste_a_verifier": "Arrete apres approbation des comptes par l'assemblee annuelle, et non a jour du dernier appel.", "fondement": "decret 2019-502 du 23 mai 2019, article 2 (LEGIARTI000038503795, version du 2019-07-01, lue le 2026-09-03)", "attendu_source": "TEXTE", "attendu": 1},
    {"id": "EXT-B-02", "college": "B", "intitule": "Charges courantes et hors budget previsionnel des deux derniers exercices clos, payees par le coproprietaire", "reste_a_verifier": "Le texte vise ce qui a ete paye, pas ce qui a ete appele. Deux exercices peuvent tenir sur une meme page: l'unite est l'exercice, pas le fichier.", "fondement": "decret 2019-502 du 23 mai 2019, article 2 (LEGIARTI000038503795, version du 2019-07-01, lue le 2026-09-03)", "attendu_source": "MENTIONS", "attendu": 2},
    {"id": "EXT-B-03", "college": "B", "intitule": "Part du fonds de travaux rattachee au lot", "reste_a_verifier": "Du seulement si le syndicat dispose d'un fonds de travaux.", "fondement": "decret 2019-502 du 23 mai 2019, article 2 (LEGIARTI000038503795, version du 2019-07-01, lue le 2026-09-03)", "attendu_source": "TEXTE", "attendu": 1, "condition": "du seulement si le syndicat dispose d'un fonds de travaux"},
    {"id": "EXT-B-04", "college": "B", "intitule": "Avis d'appel de fonds", "reste_a_verifier": "Sur les trois dernieres annees: duree fixee par le texte.", "fondement": "decret 2019-502 du 23 mai 2019, article 2 (LEGIARTI000038503795, version du 2019-07-01, lue le 2026-09-03)", "attendu_source": "DUREE"},
    {"id": "EXT-C-01", "college": "C", "intitule": "Balances generales des comptes du syndicat, et releve general des charges et produits de l'exercice echu", "reste_a_verifier": "Deux membres, et non un seul: le releve general est le second, oublie par la premiere version du referentiel. Rien n'oblige a deux fichiers distincts.", "fondement": "decret 2019-502 du 23 mai 2019, article 3 (LEGIARTI000038503789, version du 2019-07-01, lue le 2026-09-03)", "attendu_source": "MENTIONS", "attendu": 2},
    {"id": "EXT-C-02", "college": "C", "intitule": "Releves periodiques des comptes bancaires separes", "reste_a_verifier": "Le cas echeant: une absence de compte separe est a ecarter avant de conclure. Chez l'editeur observe, ces releves sont ranges dans la categorie fourre-tout, donc introuvables par le nom de la rubrique.", "fondement": "decret 2019-502 du 23 mai 2019, article 3 (LEGIARTI000038503789, version du 2019-07-01, lue le 2026-09-03)", "attendu_source": "CONTINUITE", "condition": "du seulement si la copropriete a un compte bancaire separe"},
    {"id": "EXT-C-03", "college": "C", "intitule": "Assignations en justice en cours, et decisions de justice dont les delais de recours n'ont pas expire", "reste_a_verifier": "Seule rubrique qui revele un contentieux en cours. A fort enjeu pour un conseil syndical.", "fondement": "decret 2019-502 du 23 mai 2019, article 3 (LEGIARTI000038503789, version du 2019-07-01, lue le 2026-09-03)", "attendu_source": "DECLARE"},
    {"id": "EXT-C-04", "college": "C", "intitule": "Liste de tous les coproprietaires", "reste_a_verifier": "Contient etat civil, domicile et adresse electronique de chaque coproprietaire. A constater comme presente ou absente; son contenu ne se capture jamais. Sa completude se verifie ailleurs, apres pseudonymisation, par recoupement d'alias - RM-2026-0095.", "fondement": "decret 2019-502 du 23 mai 2019, article 3 (LEGIARTI000038503789, version du 2019-07-01, lue le 2026-09-03)", "attendu_source": "TEXTE", "attendu": 1, "contenu_interdit": true},
    {"id": "EXT-C-05", "college": "C", "intitule": "Carte professionnelle du syndic, attestation d'assurance responsabilite civile professionnelle, attestation de garantie financiere", "reste_a_verifier": "En cours de validite. Mesure du 2026-09-07 sur un second cabinet: les trois y sont trois MENTIONS en tete du contrat de syndic, pas trois fichiers. Compter les fichiers produisait un manquement imaginaire.", "fondement": "loi 70-9 du 2 janvier 1970, article 3 (LEGIARTI000006480362, version du 1972-01-01, lue le 2026-09-03)", "attendu_source": "MENTIONS", "attendu": 3}
  ];

  const PAR_ID = new Map(OBLIGATIONS.map((o) => [o.id, o]));

  /* Les obligations dont le contenu ne se releve JAMAIS. Aujourd'hui la seule
   * est la liste de tous les coproprietaires: elle porte l'etat civil, le
   * domicile et l'adresse electronique de chacun. On constate qu'elle est
   * presente ou absente, et on s'arrete la. */
  /* Les unites que l'observation ne sait pas compter: une duree, une serie
   * sans trou, des justifications qui peuvent tenir dans un seul document.
   * Accepter un attendu declare sur l'une d'elles produirait un ecart chiffre
   * sur un comptage qui ne mesure pas la bonne chose. */
  const NON_COMPTABLES = new Set(["MENTIONS", "INCONNU"]);

  /* Comptables, mais le compte ne dit pas tout: la reserve voyage avec l'etat
   * pour qu'un ecart nul ne se lise pas comme une conformite. */
  const RESERVES = {
    DUREE: "le compte ne verifie pas que la periode exigee est couverte",
    CONTINUITE: "le compte ne verifie pas que la serie est sans trou",
  };

  const CONTENU_INTERDIT = new Set(
    OBLIGATIONS.filter((o) => o.contenu_interdit).map((o) => o.id)
  );

  /* Retire d'un ensemble de manques ceux qui doublonnent un recouvrement: un
   * contrat d'entretien etant aussi un contrat en cours, une seule piece
   * absente compterait sinon deux fois. Un compte gonfle detruit la
   * credibilite de celui qui s'en sert devant un syndic. */
  function dedupliquer(identifiants) {
    const garde = new Set();
    for (const o of OBLIGATIONS) {
      if (!identifiants.has(o.id)) continue;
      if ((o.recouvre || []).some((autre) => garde.has(autre))) continue;
      garde.add(o.id);
    }
    return garde;
  }

  /* Les codes de rubrique de l'editeur dont le contenu ne doit pas etre
   * conserve, d'apres les rattachements declares par l'utilisateur. */
  function rubriquesInterdites(rattachements) {
    const codes = new Set();
    for (const [id, liste] of Object.entries(rattachements || {})) {
      if (!CONTENU_INTERDIT.has(id)) continue;
      for (const code of liste || []) {
        /* En capitales: les codes de l'editeur le sont, et une declaration
         * saisie en minuscules desarmait la garde en silence. */
        const propre = String(code || "").trim().toUpperCase();
        if (propre) codes.add(propre);
      }
    }
    return codes;
  }

  return {
    OBLIGATIONS, PAR_ID, CONTENU_INTERDIT, NON_COMPTABLES, RESERVES,
    dedupliquer, rubriquesInterdites,
  };
})();

if (typeof globalThis !== "undefined") globalThis.CS_REFERENTIEL = CS_REFERENTIEL;
