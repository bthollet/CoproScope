"""Regenere `clients/extension-navigateur/referentiel.js` depuis le module Python.

Ce script existe parce qu'un message de commit du 2026-09-07 affirmait que le
fichier JavaScript etait **genere**, alors qu'il avait ete produit une fois par
un script jetable et maintenu a la main ensuite. Un agent charge de me refuter
l'a mesure: aucun generateur n'existait dans `tools/`.

L'affirmation est donc rendue vraie au lieu d'etre corrigee a la baisse: c'est
le geste le moins couteux, et le doublon a la main etait precisement le risque
que le reste du message decrivait.

Usage, depuis la racine du depot:

    PYTHONPATH=server/src python tools/generer_referentiel_js.py

`server/tests/test_extension_conformite.py` verifie de toute facon que les deux
listes coincident, champ par champ.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "server" / "src"))

from coproscope.modules import _extranet_referentiel as R  # noqa: E402

CIBLE = RACINE / "clients" / "extension-navigateur" / "referentiel.js"

TETE = '''/*
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
'''

PIED = '''
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
'''


def entree(r) -> dict:
    e = {
        "id": r.identifiant,
        "college": r.college,
        "intitule": r.intitule,
        "reste_a_verifier": r.critere_complementaire,
        "fondement": r.citation(),
        "attendu_source": r.attendu_source,
    }
    if r.attendu is not None:
        e["attendu"] = r.attendu
    if r.recouvre:
        e["recouvre"] = list(r.recouvre)
    if r.contenu_interdit:
        e["contenu_interdit"] = True
    if r.condition:
        e["condition"] = r.condition
    return e


def main() -> int:
    corps = ",\n".join(
        "    " + json.dumps(entree(r), ensure_ascii=False, sort_keys=False)
        for r in R.LISTE_MINIMALE
    )
    CIBLE.write_text(TETE + corps + PIED, encoding="utf-8", newline="\n")
    print(f"{CIBLE.relative_to(RACINE)}: {len(R.LISTE_MINIMALE)} obligations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
