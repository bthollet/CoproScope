# -*- coding: utf-8 -*-
"""La date d'un document se lit dans le DOCUMENT, jamais dans le dossier.

**Le fait mesure le 2026-09-08 sur une instance vide reconstruite.** 270
documents portaient la meme date. Aucun ne la portait dans son nom de fichier,
et **aucun de leurs textes extraits ne la contenait nulle part**. Elle venait du
dossier qui les range - un dossier de *captation*, dont le nom enregistre le
jour ou le lot a ete collecte.

**Le mecanisme, et il est pire qu'un repli.** L'echantillon servant au
classement est construit ainsi:

    parts = [file_name, original_path]  +  [le texte extrait]

puis la date etait cherchee dans cet echantillon avec `detect_date`, qui rend la
**premiere** correspondance. Le chemin etant concatene AVANT le texte, une date
presente dans l'arborescence **gagne systematiquement contre le document**. Ce
n'etait donc pas un dernier recours quand rien n'est lisible: c'etait la source
prioritaire.

**Consequence en aval.** `_ag_id` construit `AG-<date>`, si bien que tous les
proces-verbaux d'un meme lot de collecte devenaient **une seule assemblee**,
celle du jour de la collecte - 96 resolutions empilees sous une date qui n'est
celle d'aucune assemblee.

**L'axe.** Ce qui varie, c'est la maniere dont un fonds est range: par date de
reception, par exercice, par sujet, par expediteur. Ce qui reste invariant,
c'est qu'**un dossier decrit un RANGEMENT et jamais le contenu d'une piece**.
Une date lue dans une arborescence renseigne donc sur le classement, pas sur le
document.

**Ce qui se passe hors des valeurs observees.** Un cabinet qui range par
exercice aurait produit une assemblee par exercice; un rangement mensuel, une
assemblee par mois. Le defaut ne fait echouer aucun test - il change le nombre
d'assemblees, ce que rien ne verifie.

**Ce que ce module ne fait pas.** Il ne cherche pas a deviner mieux. Quand ni le
texte ni le nom du fichier ne portent de date, il rend une date **vide** et dit
pourquoi. Une absence nommee vaut mieux qu'une date empruntee au classement.
"""

from __future__ import annotations

import re
from typing import Any

from ._date_candidats import (
    ROLE_DATE,
    annonce_une_emission,
    candidats_du_texte,
    compte_par_role,
    normalise,
    ordre_du_document,
    role_du_candidat,
)

__all__ = [
    "SOURCE_ABSENTE",
    "SOURCE_NOM_DE_FICHIER",
    "SOURCE_TEXTE",
    "date_du_document",
    "SOURCE_AMBIGU",
    "date_lisible_dans",
    "lire_date",
]

SOURCE_TEXTE = "texte"
SOURCE_NOM_DE_FICHIER = "nom_de_fichier"
SOURCE_ABSENTE = ""

#: Meme forme que le detecteur historique, avec DEUX bornes en plus, chacune
#: mesuree sur le corpus reel du 2026-09-08:
#:
#: - le mois doit exister. L'ancien motif acceptait `[01]\d`, donc `00` et `13`
#:   a `19`: le registre portait des valeurs comme `2009-13` et `2016 00`;
#: - le jour, quand il est present, doit exister aussi.
#:
#: La borne porte sur la VALEUR du champ, pas sur une liste de cas rencontres.
_MOTIF = re.compile(r"(20\d{2})[-_. ](0[1-9]|1[0-2])(?:[-_. ](0[1-9]|[12]\d|3[01]))?")


def date_lisible_dans(valeur: str) -> str:
    """La premiere date valide du texte donne, ou une chaine vide."""
    trouve = _MOTIF.search(str(valeur or ""))
    if not trouve:
        return ""
    annee, mois, jour = trouve.groups()
    return f"{annee}-{mois}-{jour}" if jour else f"{annee}-{mois}"


#: Un document annonce sa date en TETE. La zone d'en-tete est bornee par un
#: nombre de caracteres et non par une balise: le texte extrait n'a plus de
#: structure. 1 200 caracteres couvrent l'en-tete d'une facture et le bandeau
#: d'un courrier sans atteindre le corps.
#: La zone du TITRE, plus etroite que l'en-tete. Un document y annonce sa
#: nature et y date son objet. Mesure du 2026-09-09: sans ce palier, un
#: proces-verbal dont le titre porte la date restait AMBIGU parce qu'une date
#: de periode, plus bas dans le meme en-tete, la contredisait.
ZONE_TITRE = 400

ZONE_ENTETE = 1200

#: Ce que la lecture rend quand plusieurs candidats survivent et se contredisent.
SOURCE_AMBIGU = "ambigu"


def lire_date(texte: str, nom_de_fichier: str = "") -> dict[str, Any]:
    """La date du document, et de quoi la defendre.

    Rend toujours les memes cles, meme quand rien ne sort: `valeur`, `source`,
    `chaine` telle qu'elle est ecrite, `granularite`, `role_ecartes` (le
    comptage qui tient lieu de garde sur les vocabulaires), `hypotheses`, et
    `candidats` quand ils se contredisent.

    **La regle de choix, en trois temps.** Eliminer par le role; preferer
    l'en-tete et les etiquettes d'emission; s'abstenir quand il reste un
    desaccord - en listant, jamais en elisant.
    """
    brut = str(texte or "")
    normal = normalise(brut)
    tous = candidats_du_texte(normal)
    ecartes = compte_par_role(normal, tous)
    retenus = [c for c in tous if role_du_candidat(normal, c) == ROLE_DATE]
    hypotheses: list[str] = []

    if not retenus:
        depuis_nom = date_lisible_dans(nom_de_fichier)
        return {
            "valeur": depuis_nom,
            "source": SOURCE_NOM_DE_FICHIER if depuis_nom else SOURCE_ABSENTE,
            "chaine": depuis_nom,
            "granularite": "jour" if len(depuis_nom) == 10 else ("mois" if depuis_nom else ""),
            "role_ecartes": {k: v for k, v in ecartes.items() if k != ROLE_DATE},
            "hypotheses": hypotheses,
            "candidats": [],
        }

    ordre = ordre_du_document(retenus)
    if ordre == "presume":
        hypotheses.append(
            "aucune date du document ne tranche l'ordre jour/mois: convention francaise presumee"
        )

    annonces = [c for c in retenus if annonce_une_emission(normal, c)]
    # **Le titre l'emporte sur le reste de l'en-tete.** Un document annonce ce
    # qu'il est dans sa premiere phrase, et il y date son objet: un
    # proces-verbal ecrit `PROCES-VERBAL DE L'ASSEMBLEE GENERALE ... le
    # Mercredi 3 decembre 2025`. Le critere est purement POSITIONNEL - il ne
    # nomme aucune nature de document, donc aucun cabinet ne peut le refuter
    # par un vocabulaire different.
    titre = [c for c in retenus if c.debut < ZONE_TITRE]
    en_tete = [c for c in retenus if c.debut < ZONE_ENTETE]
    # **Le titre passe AVANT l'etiquette, et l'ordre est le fond du sujet.**
    # Une etiquette d'emission - `le`, `date :`, `ce jour` - se repete partout
    # dans un document; la position du titre ne se repete pas. Mesure du
    # 2026-09-09: le proces-verbal de l'assemblee en double portait UN SEUL
    # candidat dans sa zone de titre, et c'etait le bon - mais des etiquettes
    # plus bas le mettaient en minorite, et la lecture rendait AMBIGU.
    prefere = titre or annonces or en_tete or retenus

    # **La corroboration tranche, et elle n'invente rien.** Deux porteurs
    # independants - le texte et le nom du fichier - qui disent la meme chose
    # valent mieux qu'un seul. Mesure du 2026-09-09: sans cette regle, cinq
    # documents dont le nom portait la reponse etaient rendus vides parce que
    # leur texte hesitait. La borne est stricte: le nom ne DEPARTAGE que s'il
    # designe un candidat deja present dans le texte. Un nom qui dit autre
    # chose que tout le texte ne gagne pas - il ne fait que confirmer.
    du_nom = date_lisible_dans(nom_de_fichier)
    if du_nom:
        corrobores = [c for c in prefere if c.valeur == du_nom]
        if corrobores:
            prefere = corrobores

    # **REFUTEE ET RETIREE le 2026-09-09: la repetition ne corrobore pas.**
    # J'avais ajoute ici une regle de majorite - une date ecrite plusieurs fois
    # l'emporte sur ses concurrentes - en la presentant comme le meme invariant
    # que la corroboration par le nom du fichier. **Elle est fausse**, et la
    # mesure l'a montree en deux minutes: sur les proces-verbaux, elle rendait
    # `2024-01-01`, `2026-01-01`, `2024-10-01`. Ce sont des PREMIERS DU MOIS,
    # signature d'une periode d'exercice repetee dans un tableau. Sur le
    # proces-verbal de l'assemblee du 3 juillet 2024, elle rendait le 1er
    # janvier.
    #
    # Deux occurrences ne sont INDEPENDANTES que si elles viennent de deux
    # endroits differents du document. Un tableau repete n'est qu'une seule
    # source ecrite plusieurs fois - la repetition y recompense la periode
    # contre la date propre. Sur l'etalon le troc etait deja defavorable,
    # +1 juste contre +3 fausses et une inventee.
    #
    # Ce que la mesure a rendu visible en revanche: **sept proces-verbaux sur
    # dix restent AMBIGU**, et leur date propre est ecrite dans leur TITRE -
    # `PROCES-VERBAL DE L'ASSEMBLEE GENERALE ... le Mercredi 3 decembre 2025`.
    # C'est ce signal-la qu'il faut lire, et il se mesurera separement.
    valeurs = {c.valeur for c in prefere}
    if len(valeurs) > 1:
        # On n'elit pas. Le desaccord est un fait, et le taire serait choisir.
        return {
            "valeur": "",
            "source": SOURCE_AMBIGU,
            "chaine": "",
            "granularite": "",
            "role_ecartes": {k: v for k, v in ecartes.items() if k != ROLE_DATE},
            "hypotheses": hypotheses,
            "candidats": [{"valeur": c.valeur, "chaine": brut[c.debut:c.fin]} for c in prefere[:6]],
        }

    choisi = prefere[0]
    return {
        "valeur": choisi.valeur,
        "source": SOURCE_TEXTE,
        "chaine": brut[choisi.debut:choisi.fin],
        "granularite": choisi.granularite,
        "role_ecartes": {k: v for k, v in ecartes.items() if k != ROLE_DATE},
        "hypotheses": hypotheses,
        "candidats": [],
    }


def date_du_document(texte: str, nom_de_fichier: str) -> tuple[str, str]:
    """La date du document et **ce sur quoi elle repose**.

    L'ordre est celui de l'autorite: ce que le document dit, puis ce que son nom
    dit. Le chemin n'est pas un argument de cette fonction - c'est la seule
    facon sure de garantir qu'il ne sera pas lu, plutot que de compter sur
    l'appelant pour ne pas le passer.

    **Depuis le 2026-09-08, ce n'est plus la premiere forme trouvee.** La
    premiere correspondance rendait des numeros de decret et des heures de
    courriel: 9 justes sur 75 a l'etalon. Le detail du choix est dans
    `lire_date`; cette fonction en garde la forme courte, parce que le
    classement et `agscope` l'appellent ainsi.
    """
    lecture = lire_date(texte, nom_de_fichier)
    if lecture["source"] == SOURCE_AMBIGU:
        # Un desaccord n'est pas une date. On rend vide, et `lire_date` dit
        # pourquoi a qui le demande.
        return "", SOURCE_ABSENTE
    return lecture["valeur"], lecture["source"]


def note_de_date(date: str, source: str, chemin_de_rangement: str) -> str:
    """La phrase a joindre au document: ce qui a ete lu, ou ce qui ne l'a pas ete.

    Elle sert d'abord a empecher la regression par bonne intention: quelqu'un
    qui verra un document sans date a cote d'un dossier date sera tente de
    recopier l'une dans l'autre. La note dit que c'est un choix, et lequel.

    **`RM-2026-0080`, corrige le 2026-09-12: une date absente se declare, meme
    quand le dossier n'en porte aucune.** La note ne sortait que si le dossier
    de rangement portait une date DIFFERENTE. Un document dont ni le texte, ni
    le nom, ni le dossier ne portent de date - *un PV isole*, dit l'item -
    rendait donc une cellule VIDE et **aucune phrase**: rien ne distinguait
    *pas de date lisible* de *date non cherchee*. C'est l'etat 2 des controles
    a trois etats - le controle n'a pas pu etre fait - et il ne doit jamais se
    lire comme un silence.

    La condition de sortie muette porte donc desormais sur la DATE TROUVEE, qui
    se suffit a elle-meme, et non sur ce que le dossier porte par hasard.
    """
    du_rangement = date_lisible_dans(chemin_de_rangement)
    if date:
        # Une date lue n'a rien a declarer, sauf si le rangement en contredit
        # une autre: c'est la seule tentation de recopie.
        if not du_rangement or du_rangement == date:
            return ""
        return (
            f"Date {date} lue dans le {source}; le dossier de rangement en porte "
            f"une autre ({du_rangement}), non retenue: un dossier decrit un "
            f"classement, pas un document."
        )
    if du_rangement:
        return (
            f"Aucune date lisible dans le document ni dans son nom. Le dossier de "
            f"rangement porte {du_rangement}, non retenue: un dossier decrit un "
            f"classement, pas un document."
        )
    return (
        "Aucune date lisible dans le document, dans son nom ni dans son dossier "
        "de rangement. La date reste a etablir a la main: une cellule vide sans "
        "cette phrase se lirait comme une date non cherchee."
    )


def applique_date(row: dict[str, Any], texte: str) -> tuple[str, str]:
    """Pose la date sur une ligne de registre sans jamais lire son chemin."""
    date, source = date_du_document(texte, str(row.get("file_name") or ""))
    return date, source
