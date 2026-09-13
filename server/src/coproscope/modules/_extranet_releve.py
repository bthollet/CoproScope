"""Reception d'un releve transmis par l'extension de navigateur.

L'extension **n'interprete rien**: elle rend une structure neutre - rubriques,
groupes, libelles, noms servis par le serveur - et c'est ici que cette matiere
devient des observations comparables.

Le partage est delibere. Deux implantations de la meme logique divergent
toujours, et la divergence se voit le jour ou l'on en a le plus besoin. Un seul
endroit sait donc raisonner, et il est teste.

----------------------------------------------------------------------
Ce que ce module refuse
----------------------------------------------------------------------

Il refuse un releve dont le format n'est pas celui qu'il connait, plutot que de
lire au mieux. Un releve mal lu ne produit pas une erreur: il produit des
observations fausses qui, au passage suivant, deviennent de faux retraits.

Il refuse aussi les codes de rubrique que le profil de l'editeur ne declare pas.
Une rubrique inventee par une version future de l'extension entrerait sinon dans
le journal sans que rien ne la relie a la grille de conformite, et sa
disparition ulterieure serait lue comme un retrait.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from ._extranet_adaptateur import ProfilEditeur
from ._extranet_schema import (
    CLOTURE_AUCUNE,
    CLOTURE_CONSTATEE,
    CONTENU_NON_VERIFIE,
    EMPLACEMENT_QUALIFIE,
    ORIGINE_EXTRAIT,
    RUBRIQUE_NON_EXPLOREE,
    RUBRIQUE_PARCOURUE,
    SEPARATEUR_EMPLACEMENT,
    emplacement as construire_emplacement,
)

FORMAT = "coproscope.extranet.releve/1"


class ReleveInvalide(ValueError):
    """Le releve n'a pas la forme attendue et n'est pas interprete au mieux."""


def _controler(charge: Mapping[str, Any]) -> None:
    if not isinstance(charge, Mapping):
        raise ReleveInvalide("Le releve doit etre un objet.")
    if charge.get("format") != FORMAT:
        raise ReleveInvalide(
            f"Format de releve inconnu: {charge.get('format')!r}. Attendu {FORMAT!r}. "
            "Un releve lu au mieux produirait des observations fausses, donc de "
            "faux retraits au passage suivant."
        )
    if charge.get("type") not in ("documents", "depenses"):
        raise ReleveInvalide(f"Type de releve inconnu: {charge.get('type')!r}.")
    if not isinstance(charge.get("rubriques"), Sequence):
        raise ReleveInvalide("Le releve ne porte aucune rubrique.")


def convertir(
    charge: Mapping[str, Any],
    profil: ProfilEditeur,
    passage_id: str,
) -> dict[str, Any]:
    """Transforme un releve en `passage`, `rubriques` et `pieces`."""
    _controler(charge)
    cloture = CLOTURE_AUCUNE if charge.get("pagination") else CLOTURE_CONSTATEE
    est_depenses = charge.get("type") == "depenses"

    rubriques: list[dict[str, str]] = []
    pieces: list[dict[str, str]] = []
    rang = 0

    for brute in charge.get("rubriques", ()):
        code = str(brute.get("rubrique_code", "")).strip()
        if not code:
            continue
        if not est_depenses and code not in profil.rubriques:
            raise ReleveInvalide(
                f"Rubrique inconnue pour le profil {profil.code!r}: {code!r}. "
                "Une rubrique non declaree entrerait dans le journal sans lien "
                "avec la grille de conformite, et sa disparition serait lue "
                "comme un retrait."
            )

        if not brute.get("presente"):
            rubriques.append(
                _rubrique(passage_id, code, profil, RUBRIQUE_NON_EXPLOREE,
                          CLOTURE_AUCUNE, 0, "rubrique absente de la page")
            )
            continue

        entrees = brute.get("lignes" if est_depenses else "pieces") or []
        vues = 0
        for entree in entrees:
            piece = (
                _piece_depense(entree, code, passage_id, rang)
                if est_depenses
                else _piece_document(entree, code, passage_id, rang)
            )
            if piece is None:
                continue
            pieces.append(piece)
            rang += 1
            vues += 1
        rubriques.append(
            _rubrique(passage_id, code, profil, RUBRIQUE_PARCOURUE, cloture, vues, "")
        )

    passage = {
        "passage_id": passage_id,
        "editeur": str(charge.get("editeur", "")),
        "espace": str(charge.get("espace", "")),
        "debut": str(charge.get("debut", "")),
        "fin": str(charge.get("fin", "")),
        "profil": profil.code,
        "doc_id": "",
        "origine": ORIGINE_EXTRAIT,
    }
    return {"passage": passage, "rubriques": rubriques, "pieces": pieces}


def _rubrique(
    passage_id: str,
    code: str,
    profil: ProfilEditeur,
    etat: str,
    cloture: str,
    nb: int,
    motif: str,
) -> dict[str, str]:
    return {
        "passage_id": passage_id,
        "rubrique_code": code,
        "rubrique_libelle": profil.rubriques.get(code, code),
        "etat": etat,
        "cloture": cloture,
        "nb_pieces": str(nb),
        "motif": motif,
        "doc_id": "",
        "origine": ORIGINE_EXTRAIT,
    }


def _commun(passage_id: str, code: str, rang: int) -> dict[str, str]:
    return {
        "passage_id": passage_id,
        "rubrique_code": code,
        "rang": str(rang),
        "empreinte": "",
        "contenu_etat": CONTENU_NON_VERIFIE,
        "doc_id": "",
        "origine": ORIGINE_EXTRAIT,
    }


def _piece_document(
    entree: Mapping[str, Any], code: str, passage_id: str, rang: int
) -> dict[str, str] | None:
    groupe = str(entree.get("groupe", "") or "").strip()
    libelle = str(entree.get("libelle", "") or "").strip()
    cle, qualite = construire_emplacement(code, groupe, libelle)
    ligne = _commun(passage_id, code, rang)
    ligne.update(
        {
            "groupe": groupe,
            "libelle": libelle,
            "emplacement": cle if qualite == EMPLACEMENT_QUALIFIE else "",
            "emplacement_qualite": qualite,
            "nom_serveur": str(entree.get("nom_serveur", "") or "").strip(),
        }
    )
    return ligne


def _piece_depense(
    entree: Mapping[str, Any], code: str, passage_id: str, rang: int
) -> dict[str, str] | None:
    # Une ligne sans piece jointe n'est pas une piece observee: elle sera
    # comparee comme absence a l'emplacement, ce qui est exactement ce qu'on
    # veut - une facture ajoutee comble une lacune, elle ne cree pas une
    # depense.
    if not entree.get("a_une_facture"):
        return None
    colonnes = [str(c).strip() for c in (entree.get("colonnes") or []) if str(c).strip()]
    if not colonnes:
        return None
    # Toutes les colonnes entrent dans la cle, le montant compris: c'est lui qui
    # fait tomber a zero les 21 collisions mesurees sur 729 lignes.
    cle = SEPARATEUR_EMPLACEMENT.join([code, *colonnes])
    ligne = _commun(passage_id, code, rang)
    ligne.update(
        {
            "groupe": colonnes[0],
            "libelle": " | ".join(colonnes[1:]) if len(colonnes) > 1 else colonnes[0],
            "emplacement": cle,
            "emplacement_qualite": EMPLACEMENT_QUALIFIE,
            "nom_serveur": str(entree.get("nom_serveur", "") or "").strip(),
        }
    )
    return ligne
