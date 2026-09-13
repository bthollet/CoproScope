r"""Un dossier synchronise avec un nuage n'est pas un endroit ou ecrire.

**Pourquoi c'est un garde-fou et pas un detail.** Une instance CoproScope ecrit
des registres, des sorties et un coffre. Si ces fichiers vivent dans un dossier
synchronise, trois choses arrivent sans qu'aucune erreur ne soit levee: ils
partent chez un tiers, ils sont modifies par une machine que nous ne pilotons
pas, et ils reviennent dans un etat que nous n'avons pas ecrit. Sur une
copropriete en procedure, cela suffit a rendre une mesure incontestable.

Le depot en a fait l'experience: son propre code a vecu dans un Drive partage,
et des chemins `G:\Mon Drive\...` sont encore dans des fichiers versionnes.

----------------------------------------------------------------------
L'axe, et la modalite qu'il remplace
----------------------------------------------------------------------

`drive_local_setup` portait deja une garde, mais sur une **liste de noms**:
`("google drive", "mon drive", "my drive", "onedrive", "dropbox", "icloud
drive")`. C'est une modalite observee, pas un axe: un Drive monte sur `G:\`
dont le chemin ne contient aucun de ces mots la traverse sans bruit, et c'est
exactement le cas de ce poste.

La question generale est: **ce dossier est-il tenu par un logiciel de
synchronisation ?** Windows y repond de deux facons structurelles, et une
troisieme par defaut:

1. **L'attribut de fichier fantome.** Un fichier dont le contenu n'est pas
   local porte `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS` ou
   `FILE_ATTRIBUTE_RECALL_ON_OPEN`. C'est le mecanisme meme des « fichiers a la
   demande »: il ne depend d'aucun nom.
2. **Le type de volume.** Un montant reseau ou un lecteur virtuel n'est pas un
   disque fixe. `GetDriveType` le dit.
3. **Le nom, en dernier recours.** Un dossier synchronise peut vivre sur un
   disque fixe avec tout son contenu local - un OneDrive dans le profil, par
   exemple. Aucun signal structurel ne le distingue alors, et la liste de noms
   reste le seul indice. Elle est gardee pour cela, et **etiquetee comme tel**:
   elle ne pretend plus etre la regle.

Hors de Windows, seuls les signaux 2 et 3 sont evalues, et le module le dit
plutot que de faire croire a une verification complete.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

#: Les deux attributs que Windows pose sur un fichier dont le contenu vit
#: ailleurs. Ce sont des constantes du systeme, pas des noms de produits.
_RECALL_ON_DATA_ACCESS = 0x00400000
_RECALL_ON_OPEN = 0x00040000

#: `DRIVE_FIXED` de l'API Windows. Tout le reste - reseau, amovible, inconnu -
#: n'est pas un disque local.
_DRIVE_FIXED = 3

#: **Dernier recours, pas la regle.** Un dossier synchronise pose sur un disque
#: fixe, contenu entierement local, ne se distingue par aucun signal
#: structurel. Cette liste le rattrape, et elle sera toujours incomplete.
NOMS_CONNUS = (
    "google drive", "mon drive", "my drive", "googledrive",
    "onedrive", "dropbox", "icloud drive", "icloud", "box sync",
    "pcloud", "mega", "nextcloud", "sync.com", "tresorit",
)


def _attribut_fantome(chemin: Path) -> bool:
    """Le chemin, ou un de ses parents, est-il un fichier a la demande ?"""
    if not hasattr(os, "stat"):  # pragma: no cover - defensif
        return False
    for candidat in (chemin, *chemin.parents):
        try:
            attributs = os.stat(candidat).st_file_attributes  # type: ignore[attr-defined]
        except (OSError, AttributeError):
            continue
        if attributs & (_RECALL_ON_DATA_ACCESS | _RECALL_ON_OPEN):
            return True
    return False


def _volume_non_fixe(chemin: Path) -> str:
    """Le nom du volume s'il n'est pas un disque local, sinon une chaine vide."""
    if sys.platform != "win32":
        return ""
    try:
        import ctypes

        racine = chemin.anchor or str(chemin)
        type_volume = ctypes.windll.kernel32.GetDriveTypeW(str(racine))
    except Exception:  # pragma: no cover - API indisponible
        return ""
    return "" if type_volume == _DRIVE_FIXED else (chemin.anchor or str(chemin))


def raison_de_refus(chemin: Path | str) -> str:
    """La raison pour laquelle ce chemin ne peut pas accueillir de donnees.

    Rend une chaine vide quand le chemin est acceptable. La raison est destinee
    a etre lue par un humain: elle nomme le dossier ET le signal qui a
    declenche, pour qu'un faux positif se diagnostique sans lire ce module.
    """
    resolu = Path(chemin).expanduser()
    try:
        resolu = resolu.resolve()
    except OSError:  # pragma: no cover - chemin inaccessible
        pass

    if _attribut_fantome(resolu):
        return (
            f"« {resolu} » est dans un dossier synchronise: le systeme y marque "
            "des fichiers comme « disponibles a la demande », donc leur contenu "
            "vit ailleurs."
        )
    volume = _volume_non_fixe(resolu)
    if volume:
        return (
            f"« {resolu} » est sur le volume {volume}, qui n'est pas un disque "
            "local. Un lecteur reseau ou virtuel peut etre monte, demonte ou "
            "reecrit par un logiciel tiers."
        )
    bas = str(resolu).lower()
    for nom in NOMS_CONNUS:
        if nom in bas:
            return (
                f"« {resolu} » porte « {nom} » dans son chemin. Ce signal est "
                "un dernier recours et il peut se tromper: si ce dossier n'est "
                "pas synchronise, renommez-le ou deplacez l'instance."
            )
    return ""
