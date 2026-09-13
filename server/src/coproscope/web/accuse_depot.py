"""L'accuse de depot: le seul endroit ou le nom depose est rendu, et une fois.

**La commande.** Brice, 2026-09-08, `RM-2026-0126`, verbatim au depot dans
`docs/arbitrage_brice_0126_verbatim_2026-09-08.md`:

    « Un accuse de depot montre le nom au deposant seul, juste apres le depot
    et nulle part ailleurs. »

**Pourquoi cet ecran, et pas un autre.** Le nom d'un fichier est ecrit par un
tiers et peut porter un patronyme; il ne doit donc traverser aucune page
diffusable. Mais un deposant qui vient d'envoyer douze pieces et lit
`Fichier 1 ... Fichier 12` ne peut pas verifier qu'il a envoye les bonnes.
L'accuse est la reponse: le nom apparait une fois, pour celui qui vient de
l'ecrire lui-meme et le connait deja, puis plus jamais.

**`juste apres le depot` est tenu par un COMPTAGE, pas par une duree.**
Premiere version de ce module, le 2026-09-08: l'accuse etait servi des que
l'URL nommait un depot. Un test existant l'a refute en une mesure -
`test_document_intake_upload_returns_to_intake_with_uploaded_files` recharge la
page apres la qualification, avec le meme `depot=` dans l'URL, et le nom
revenait. `nulle part ailleurs` etait faux: il revenait a chaque visite, sans
limite de temps.

La borne retenue n'est ni une liste d'ecrans ni un delai en secondes - un delai
serait un nombre choisi au hasard, et rendrait les tests dependants de
l'horloge. C'est une **conservation**: un depot donne au plus un accuse. Le
manifeste porte `accuse_rendu_le`; la premiere lecture le pose, les suivantes
ne rendent rien. Le compte des accuses servis ne peut pas depasser le compte des
depots, et cela se verifie en comptant.

**Effet de bord assume: cette lecture ecrit.** Un `GET` qui modifie l'etat est
normalement suspect. Ici c'est la semantique meme du `une seule fois`: sans
trace de consommation, `une fois` n'est pas une propriete du systeme mais un
espoir sur le comportement de l'utilisateur.

**LE RESIDU, et il est teste.** L'identifiant de depot est un horodatage UTC a
la seconde - `DEPOT-20260908T142233Z`, `web/depot.py:183`. Il n'est ni secret,
ni aleatoire, ni derive du deposant. Qui sait qu'un depot a eu lieu tel jour a
telle seconde reconstruit l'identifiant.

Le caractere a un coup borne le degat sans le supprimer, et deplace sa nature:
un tiers qui devine l'identifiant AVANT que le deposant n'arrive sur sa page de
retour consomme l'accuse a sa place. Le deposant ne verra alors jamais ses noms.
C'est une fuite qui se VOIT - la confirmation attendue manque - au lieu d'une
fuite muette, et c'est le seul progres qu'on revendique ici.

Sous l'hypothese monoutilisateur cela ne change rien: un seul jeton, un seul
lecteur, et ce lecteur est le deposant. La ou cela compte, c'est au deuxieme
utilisateur. Le remede - identifiant non devinable, ou accuse lie a une session
authentifiee - appartient au cahier
`docs/cdc_pseudonymisation_multiutilisateur_2026-09-08.md`, pas a ce POC.

**Second residu, trouve en relisant ce module contre lui-meme.** `une fois`
compte les LECTURES, pas les lectures HUMAINES. Un navigateur qui precharge le
lien, une extension qui le visite, un rechargement automatique, et l'accuse est
consomme sans que personne ne l'ait lu. Le deposant voit alors une page sans sa
confirmation, sans savoir pourquoi.

C'est le prix du choix fait ici: `une fois` est verifiable, `vu une fois` ne
l'est pas cote serveur. Le defaut penche du bon cote - on montre trop peu
plutot que trop - mais il se paie en confiance, et il faudra le reprendre quand
l'accuse aura un accuse de reception cote client.
"""

from __future__ import annotations

from typing import Any


CHAMP_CONSOMMATION = "accuse_rendu_le"


def lignes_accuse(manifest: dict[str, Any] | None) -> list[dict[str, str]]:
    """Les noms deposes et leur rang, sans decider s'il faut les montrer.

    Separee de la decision pour qu'un test puisse verifier le contenu sans
    consommer l'accuse, et pour que la regle de service reste au meme endroit.
    """

    if not manifest:
        return []
    fichiers = manifest.get("files")
    if not isinstance(fichiers, list):
        return []

    lignes: list[dict[str, str]] = []
    for rang, info in enumerate(fichiers, start=1):
        if not isinstance(info, dict):
            continue
        nom = str(info.get("original_name") or info.get("stored_name") or "").strip()
        if not nom:
            continue
        lignes.append({"rang": f"Fichier {rang}", "nom_depose": nom})
    return lignes


def servir_accuse(
    instance: Any,
    manifest: dict[str, Any] | None,
    *,
    depot_demande: str,
) -> list[dict[str, str]]:
    """Rend l'accuse si c'est la premiere lecture de ce depot, sinon rien.

    `depot_demande` est l'identifiant tel que l'APPELANT l'a fourni. Vide
    signifie que personne n'a nomme de depot: on ne rend rien, meme si un
    manifeste traine par ailleurs. C'est la difference avec `GET /depot`, qui
    se replie sur `latest_deposit_manifest` - un repli rendrait l'accuse
    atteignable par quelqu'un qui n'a rien depose, en ouvrant la page.

    **Si la trace de consommation ne peut pas s'ecrire, on ne montre rien.**
    Un accuse qu'on ne sait pas marquer comme rendu est un accuse qui se
    rejouera indefiniment: en cas de doute, la garantie l'emporte sur le
    confort.
    """

    if not (depot_demande or "").strip():
        return []
    if not manifest:
        return []
    if str(manifest.get(CHAMP_CONSOMMATION) or "").strip():
        return []

    lignes = lignes_accuse(manifest)
    if not lignes:
        return []

    from .depot import now_iso, write_deposit_manifest

    try:
        manifest[CHAMP_CONSOMMATION] = now_iso()
        write_deposit_manifest(instance, manifest)
    except Exception:  # noqa: BLE001 - voir la docstring: pas de trace, pas d'accuse
        manifest.pop(CHAMP_CONSOMMATION, None)
        return []
    return lignes
