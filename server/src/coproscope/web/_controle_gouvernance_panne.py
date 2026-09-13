# -*- coding: utf-8 -*-
"""Le canal par lequel l'ecran de controle dit que c'est LUI qui est casse.

Extrait de `controle_gouvernance_view.py`, qui passait a 601 lignes en accueillant
ce bloc. Le decoupage suit l'objet mesure et non la taille: ce module ne parle
jamais de la copropriete, seulement de la coherence de l'instrument qui la
regarde. C'est precisement la separation que `RM-2026-0117` demande de tenir.

Brice, revue du 2026-09-07 a 12:08: << ce n'est pas possible. Ou alors vraiment
sous forme de message d'erreur, que l'instance est cassee, il faut la refaire. >>
"""
from __future__ import annotations

from typing import Any

#: Ce que l'ecran sait dire quand c'est LUI qui se contredit, et non les pieces.
#:
#: La cle est une `nature` et non un booleen, parce qu'une autre contradiction
#: de l'instrument se rangera ici plutot que d'inventer un troisieme canal. Une
#: nature inconnue tombe sur le repli plus bas: l'ecran dit qu'il se contredit
#: sans pretendre savoir comment.
NATURES_PANNE: dict[str, dict[str, str]] = {
    "comptes_contradictoires": {
        "titre": "Cet ecran se contredit. Ne vous fiez a aucun des deux nombres.",
        "explication": (
            "La synthese a annonce {attendu} lignes et le tableau en trouve {trouve}, "
            "pour exactement le meme filtre. Les deux viennent du meme calcul: ils ne "
            "peuvent pas differer si l'instance est coherente."
        ),
        "consigne": (
            "Reconstruisez l'instance, puis rouvrez cet ecran. Si l'ecart persiste, "
            "c'est un defaut du logiciel et non de vos documents."
        ),
    },
}

#: La seule autre cause possible, et l'ecran ne sait pas la distinguer de la
#: premiere. Le dire est le contraire d'une precaution de style: affirmer une
#: instance cassee sur un signet perime serait une fausse alerte, donc
#: exactement le defaut que ce bloc corrige.
RESERVE_PANNE = (
    "Une autre cause est possible et cet ecran ne sait pas les distinguer: un lien "
    "ancien ou modifie a la main transporte un nombre perime. Si vous etes arrive "
    "ici par un signet, revenez par la synthese avant de conclure."
)


def panne_instrument(
    attendu: int | None,
    trouve: int,
    nature: str = "comptes_contradictoires",
) -> dict[str, Any] | None:
    """L'ecran se contredit-il lui-meme ?

    **La distinction que `RM-2026-0117` demande de tenir:** un desaccord entre
    deux SOURCES - le syndic affirme, CoproScope calcule - est une information
    sur la copropriete et merite une sortie concue. Une contradiction entre deux
    VUES du meme calcul n'apprend rien sur la copropriete: elle dit que
    l'instrument est casse. Les deux sortaient par le meme bandeau, donc le
    lecteur ne pouvait pas savoir ce qu'il regardait.

    Rend `None` quand il n'y a rien a signaler - le cas de loin le plus frequent -
    et sinon une panne nommee, que le gabarit rend dans un canal d'alerte separe
    a la place de la phrase ordinaire, jamais a cote d'elle.

    **Pourquoi `nature` est un parametre et non une constante interne.** La
    premiere version le figeait, ce qui rendait le repli du bas INATTEIGNABLE:
    une garde qu'aucune entree ne peut declencher n'est pas une garde, c'est un
    commentaire qui se fait passer pour du code. Le parametre existe donc pour
    que la branche du bas soit joignable, testee, et disponible le jour ou une
    autre contradiction de l'instrument doit sortir par ce canal.
    """
    if attendu is None or attendu == trouve:
        return None
    modele = NATURES_PANNE.get(nature)
    if modele is None:
        return {
            "nature": nature,
            "titre": "Cet ecran se contredit.",
            "explication": (
                "Deux vues du meme calcul ne rendent pas la meme chose, et cette page "
                "ne sait pas decrire cette contradiction-la."
            ),
            "consigne": "Reconstruisez l'instance, puis rouvrez cet ecran.",
            "reserve": RESERVE_PANNE,
            "attendu": attendu,
            "trouve": trouve,
        }
    return {
        "nature": nature,
        "titre": modele["titre"],
        "explication": modele["explication"].format(attendu=attendu, trouve=trouve),
        "consigne": modele["consigne"],
        "reserve": RESERVE_PANNE,
        "attendu": attendu,
        "trouve": trouve,
    }


