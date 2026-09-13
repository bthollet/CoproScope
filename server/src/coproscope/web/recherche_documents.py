from __future__ import annotations

import re
import unicodedata

from ..core.common import InstanceConfig, read_csv


"""Retrouver une piece sans jamais rendre son nom de fichier.

**Le conflit, et il est reel des deux cotes.** Le deposant doit pouvoir remettre
la main sur la piece qu'il vient de deposer: c'est le seul geste qui referme la
boucle depot -> coffre. Et la page `/documents` est diffusable: un nom de
fichier ecrit par un tiers - syndic, fournisseur, scanner - y porte souvent un
patronyme, donc il ne doit pas y etre imprime. Voir
`core/libelle_public.py` pour la doctrine du libelle.

**L'axe.** Le degre de liberte n'est pas *quel nom afficher*, il est **ou vit la
donnee**. Un champ peut etre LU par le serveur pour decider, et rester HORS du
rendu. Retrouver n'est pas afficher: le nom de fichier entre dans le predicat de
selection, jamais dans la reponse HTTP.

**Ce qui reste invariant le long de cet axe.** Une piece est retrouvable par
n'importe quel fragment de son identite - le nom que le deposant lui a donne, le
type que CoproScope a deduit, sa date, sa reference. La ligne retrouvee, elle,
est toujours rendue avec son libelle derive et son identifiant public.

**Ce que le code en fait.** Les termes tapes et l'identite de chaque piece sont
normalises de la meme facon - minuscules, accents retires, ponctuation ramenee a
des espaces - puis tous les termes doivent apparaitre dans l'identite. Aucune
valeur privee ne ressort de ce module: `doc_ids_correspondants` ne rend que des
identifiants publics.

**Hors des valeurs observees.** Un registre sans colonne `file_name` cherche sur
ce qu'il a et se degrade en silence acceptable: moins de pieces retrouvees,
jamais une piece fausse ni un nom rendu. Un terme qui ne correspond a rien donne
zero ligne AVEC son bandeau, pas la liste entiere: l'utilisateur voit qu'il a
cherche, ce qui etait precisement le defaut du 2026-09-07 - la barre de
recherche ne filtrait rien et rendait la meme page.
"""


#: Champs LUS pour retrouver et JAMAIS rendus. Cette liste est le pendant exact
#: de `_CHAMPS_NON_EXPOSES` dans `viewmodels/_source_models.py`: ce que l'un
#: interdit d'afficher, l'autre autorise a interroger. Les deux listes disent la
#: meme regle vue de ses deux cotes, elles ne se contredisent pas.
CHAMPS_PRIVES_INTERROGEABLES = ("file_name", "filename", "original_path")

#: Champs deja publics, cherchables sans precaution particuliere.
CHAMPS_PUBLICS_INTERROGEABLES = (
    "doc_id",
    "document_type",
    "suspected_date",
    "source_zone",
    "title",
    "subject",
)

#: Un terme d'un seul caractere ramene tout le coffre: ce n'est pas une
#: recherche, c'est du bruit.
LONGUEUR_MINIMALE_TERME = 2

#: Bornes defensives sur une entree utilisateur libre.
LONGUEUR_MAXIMALE_REQUETE = 200
NOMBRE_MAXIMAL_TERMES = 8


def _normalise(valeur: object) -> str:
    """Minuscules, sans accents, ponctuation ramenee a des espaces.

    `zz_ma_convocation.txt` et `Convocation` se rencontrent ici, et c'est tout
    ce qu'on demande a cette fonction: mettre les deux cotes de la comparaison
    dans la meme forme.
    """

    texte = unicodedata.normalize("NFKD", str(valeur or ""))
    texte = "".join(char for char in texte if not unicodedata.combining(char))
    return " ".join(re.split(r"[^0-9a-z]+", texte.lower())).strip()


def termes_de_recherche(requete: object) -> list[str]:
    """Les termes exploitables d'une requete, ou une liste vide."""

    normalisee = _normalise(str(requete or "")[:LONGUEUR_MAXIMALE_REQUETE])
    termes = [mot for mot in normalisee.split(" ") if len(mot) >= LONGUEUR_MINIMALE_TERME]
    return termes[:NOMBRE_MAXIMAL_TERMES]


def _identite_interrogeable(ligne: dict[str, str]) -> str:
    """La botte de foin d'une piece. Elle ne quitte jamais ce module."""

    morceaux = [
        ligne.get(champ, "")
        for champ in (*CHAMPS_PUBLICS_INTERROGEABLES, *CHAMPS_PRIVES_INTERROGEABLES)
    ]
    return _normalise(" ".join(str(morceau or "") for morceau in morceaux))


def _lignes_du_registre(instance: InstanceConfig) -> list[dict[str, str]]:
    try:
        chemin = instance.register("documents")
    except KeyError:
        return []
    _, lignes = read_csv(chemin)
    return lignes


def doc_ids_correspondants(instance: InstanceConfig, termes: list[str]) -> set[str]:
    """Les identifiants PUBLICS des pieces dont l'identite porte tous les termes.

    Rien d'autre ne sort d'ici. Le nom de fichier a servi a decider, il ne
    remonte pas.
    """

    if not termes:
        return set()
    trouves: set[str] = set()
    for ligne in _lignes_du_registre(instance):
        doc_id = str(ligne.get("doc_id", "") or "").strip()
        if not doc_id:
            continue
        identite = _identite_interrogeable(ligne)
        if all(terme in identite for terme in termes):
            trouves.add(doc_id)
    return trouves


def modele_recherche(
    instance: InstanceConfig,
    lignes_publiques: list[dict[str, str]],
    requete: object,
    plafond: int = 12,
) -> dict[str, object]:
    """Ce que le gabarit recoit. Aucune cle ne porte la requete ni un nom brut.

    La requete elle-meme n'est pas renvoyee au gabarit: la reafficher dans le
    champ de recherche remettrait le nom tape par le deposant dans une page
    diffusable, par la porte de derriere.
    """

    termes = termes_de_recherche(requete)
    if not termes:
        return {"active": False, "total": 0, "lignes": [], "plafond": plafond}
    identifiants = doc_ids_correspondants(instance, termes)
    lignes = [
        ligne
        for ligne in lignes_publiques
        if str(ligne.get("doc_id", "") or "").strip() in identifiants
    ]
    return {
        "active": True,
        "total": len(lignes),
        "lignes": lignes[:plafond],
        "plafond": plafond,
    }
