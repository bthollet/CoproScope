"""Les six colonnes de la matrice, cellule par cellule.

Extrait de `_controle_gouvernance_source` le 2026-09-06, avant les lots qui
touchent cet ecran: le module etait a 587 lignes pour une limite de 600, et
quatre lots a venir y ecrivent. La coupure suit la barre de section qui etait
deja la.

**Ce que ce module decide, et c'est plus lourd qu'il n'y parait.** Chaque
fonction ici traduit une force probatoire en une phrase que lira un
coproprietaire. « Le devis retenu est au dossier » et « Devis cite,
rattachement a confirmer » ne disent pas la meme chose au conseil syndical, et
la difference entre les deux ne se voit pas dans la base: elle se voit ici.

C'est donc l'endroit ou une affirmation du produit devient opposable a un
syndic. Une phrase ajoutee ici doit pouvoir etre defendue devant lui.
"""

from __future__ import annotations

from typing import Any

from ..modules import actes_autorisation as A
from ..modules._actes_dates import DateNonOrdonnable, date_iso
from ..modules._actes_seuils_normes import (
    NORME_CONCURRENCE,
    NORME_CONSULTATION_CS,
    NORME_NON_ATTRIBUEE,
    NORMES_SEUIL,
)
from ..modules._actes_typologie import (
    CTRL_ANNEXE,
    CTRL_AVIS_CS,
    CTRL_DEVIS,
    CTRL_EXECUTION,
    CTRL_RAPPORT_CS,
    CTRL_SEUIL,
    controle_applicable,
    motif_hors_controle,
)

from ._controle_gouvernance_franchissement import (
    franchissement,
    phrase_de_franchissement,
)
from ._controle_gouvernance_acces_piece import chemin_de_piece
from ._controle_gouvernance_vocabulaire import (
    FORCE_VERS_STATUT,
    NATURES,
    RESULTATS,
    _bulle,
    _cellule,
    euros,
)


# --------------------------------------------------------------------------
# Les six colonnes, cellule par cellule
# --------------------------------------------------------------------------

_L_RESOLUTION = {
    "nom": "Texte de la résolution",
    "disponible": "Le procès-verbal énonce ce qui s'est passé, y compris quand ce qui s'est passé est qu'il n'y a pas eu de vote.",
    "confirmer": "Des voix sont comptées et l'issue n'est pas énoncée. La pièce existe et ne conclut pas : rien n'autorise à conclure à l'adoption.",
    "manquante": "Aucun acte d'autorisation trouvé pour cet objet.",
}
_L_ANNEXE = {
    "nom": "Annexe visée",
    "disponible": "L'annexe visée par la résolution est au dossier.",
    "confirmer": "Annexe citée, correspondance à confirmer.",
    "manquante": "La résolution renvoie à une annexe qui n'est pas au dossier.",
}
_L_AVIS = {
    "nom": "Avis du conseil syndical",
    "disponible": "Compte rendu fourni, rattaché à cette décision.",
    "confirmer": "Avis déclaré, sans pièce à l'appui.",
    "manquante": "Aucun avis rattaché. La consultation préalable de l'article 21 alinéa 2 n'est établie par aucune pièce.",
}
_L_RAPPORT = {
    "nom": "Rapport annuel du conseil syndical",
    "disponible": "Le rapport annuel est rattaché.",
    "confirmer": "Rapport déclaré, sans pièce à l'appui.",
    "manquante": "Aucun rapport rattaché. Il est notifié avec l'ordre du jour.",
}
#: **Le devis n'est pas obligatoire, et le libelle le disait le contraire.**
#: `RM-2026-0164`, point (2), demande de Brice: *« devis associes » plutot que
#: « devis retenu », ou mieux « presence du devis, oui ou non », puisque le
#: devis, il n'est pas obligatoire*. Et la consequence de surete qu'il en tire:
#: **une absence de devis n'est PAS un manquement** et ne doit pas etre
#: presentee parmi les pieces a reclamer.
#:
#: **Deux mots faisaient tout le defaut.** `retenu` presuppose qu'un choix a eu
#: lieu entre plusieurs devis - le lot precedent avait d'ailleurs compte
#: `89 faux positifs` sur cette base - et `Aucun devis rattache`, sec, se lit
#: comme le constat d'une piece qui manque. Mesure du 2026-09-11 sur
#: l'instance reabsorbee, 550 actes: **206 portent `ABSENT`**, donc 206 lignes
#: annoncaient un vide sous un mot qui promettait un choix.
#:
#: **L'axe, et c'est celui de toute la colonne:** un controle dont l'objet
#: n'est pas obligatoire ne rend pas une absence comme un manquement. Ce qui
#: varie d'une copropriete a l'autre est le nombre de devis produits - zero, un,
#: quatre; ce qui reste invariant est qu'aucun texte n'en impose.
_L_DEVIS = {
    "nom": "Devis associé",
    "disponible": "Un devis est rattaché à cette décision.",
    "confirmer": "Devis cité, rattachement à confirmer.",
    "manquante": "Aucun devis n'est rattaché. Le devis n'est pas obligatoire : "
                 "son absence n'est pas un manquement.",
}
#: **Un jeu de libelles par norme, et le nom dit laquelle.** Corrige le
#: 2026-09-08 (`RM-2026-0144`). Un libelle unique `Seuil applicable` aurait
#: reproduit a l'affichage le defaut qu'on venait de corriger dans le modele:
#: deux montants arretes le meme jour pour deux obligations differentes
#: arrivaient sous le meme mot, et le lecteur n'avait aucun moyen de savoir
#: lequel des deux la cellule lui rapportait.
#:
#: Le libelle decrit la FORCE de la piece, jamais le nombre de seuils: le
#: nombre est mesure ailleurs, et `_seuil` reecrit alors le detail. Jusqu'au
#: 2026-09-08 le libelle `confirmer` disait `Plusieurs montants de seuil
#: coexistent`, ce qui annoncait une pluralite sur un acte qui pouvait n'en
#: porter qu'un seul, seulement declare.
_L_SEUIL_CONSULTATION_CS = {
    "nom": "Seuil de consultation du conseil syndical",
    "disponible": "Le montant à partir duquel la consultation du conseil syndical est obligatoire est rattaché à cet acte.",
    "confirmer": "Seuil de consultation déclaré, sans pièce à l'appui.",
    "manquante": "Aucun montant déclenchant la consultation du conseil syndical n'est rattaché à cet acte.",
}
_L_SEUIL_CONCURRENCE = {
    "nom": "Seuil de mise en concurrence",
    "disponible": "Le montant à partir duquel la mise en concurrence est obligatoire est rattaché à cet acte.",
    "confirmer": "Seuil de mise en concurrence déclaré, sans pièce à l'appui.",
    "manquante": "Aucun montant déclenchant la mise en concurrence n'est rattaché à cet acte.",
}
#: Le residu. Cette cellule ne s'affiche **que** lorsqu'un seuil est rattache
#: sans que l'obligation qu'il declenche ait ete identifiee. La montrer vide
#: partout aurait ajoute une troisieme ligne de bruit sous les deux vraies.
_L_SEUIL_NON_ATTRIBUE = {
    "nom": "Seuil rattaché, norme non attribuée",
    "disponible": "Un montant de seuil est rattaché à cet acte, sans que l'obligation qu'il déclenche ait été identifiée.",
    "confirmer": "Un montant de seuil est déclaré sans pièce, et sans que l'obligation qu'il déclenche ait été identifiée.",
    "manquante": "Aucun montant de seuil n'est rattaché à cet acte.",
}
#: prefixe de norme -> les quatre phrases ecrites pour elle.
#:
#: **Ce que cette table ne doit PAS faire: borner la liste des bulles.** Le
#: premier jet de ce lot enumerait les deux prefixes en dur dans `_seuil`. Une
#: troisieme norme declaree dans `_actes_seuils_normes` aurait alors recu sa
#: relation, ses liens et ses colonnes de matrice - et **aucune bulle**. Le
#: defaut corrige dans le modele serait revenu au dernier metre, sous la forme
#: la plus difficile a voir: pas une phrase fausse, une absence.
#:
#: `_seuil` boucle donc sur le registre, et cette table ne fait que fournir les
#: phrases quand elles ont ete ecrites.
_PHRASES_PAR_NORME: dict[str, dict[str, str]] = {}

#: La phrase de non-applicabilite est commune aux trois: `CTRL_SEUIL` est un
#: seul controle, et son retrait vaut pour les deux normes a la fois. Elle porte
#: donc un nom generique, et c'est le seul endroit ou il reste legitime.
_L_SEUIL_RETIRE = {
    "nom": "Seuils de l'article 21 alinéa 2",
    "disponible": "",
    "confirmer": "",
    "manquante": "",
}

_PHRASES_PAR_NORME.update({
    NORME_CONSULTATION_CS.prefixe: _L_SEUIL_CONSULTATION_CS,
    NORME_CONCURRENCE.prefixe: _L_SEUIL_CONCURRENCE,
    NORME_NON_ATTRIBUEE.prefixe: _L_SEUIL_NON_ATTRIBUE,
})


def _phrases(norme) -> dict[str, str]:
    """Les phrases de cette norme, ecrites ou derivees de son nom.

    Une norme declaree sans phrases reste **visible**, sous un libelle derive.
    Le repli est generique et le dit; il n'est pas silencieux, et surtout il
    n'efface pas la norme de l'ecran. C'est la degradation propre que le depot
    exige hors des valeurs observees: on perd la qualite de la formulation, pas
    l'existence du controle.
    """
    ecrites = _PHRASES_PAR_NORME.get(norme.prefixe)
    if ecrites:
        return ecrites
    return {
        "nom": norme.libelle,
        "disponible": "Un montant arrêté par l'assemblée pour cette obligation "
                      "est rattaché à cet acte.",
        "confirmer": "Montant déclaré pour cette obligation, sans pièce à l'appui.",
        "manquante": "Aucun montant n'est rattaché à cet acte pour cette obligation.",
    }


#: **La phrase qui disait que le modele ne comparait pas a ete retiree le
#: 2026-09-10, parce qu'elle etait devenue fausse de deux facons.** Elle
#: s'ecrivait: *le franchissement lui-meme n'est pas calcule; la comparaison du
#: montant au seuil n'existe pas encore dans le modele*. La comparaison existe
#: desormais - la matrice porte le montant arrete par la deliberation retenue a
#: cote de celui de l'acte. Et ce qui manquait n'etait pas le calcul, c'etaient
#: les MONTANTS: 550 liens de seuil, 124 comparables, 426 dont le montant de
#: l'acte n'est pas lisible. Dire *le modele ne compare pas* laissait croire a
#: un manque de code la ou il y a un manque de donnee.


def citation(ligne: dict[str, Any], prefixe: str) -> dict[str, Any] | None:
    """D'ou vient ce que la cellule affirme: piece, page, endroit dans la page.

    **La source citee est celle du lien QUE LA CELLULE RETIENT.** La matrice
    designe le lien le plus probant par un `ORDER BY ... LIMIT 1` et en tire la
    force probatoire; elle en tire, du meme sous-select, `doc_id`, `page` et
    `ancre`. Une seconde requete aurait pu retenir une autre assertion, et
    l'ecran aurait cite la page d'un devis seulement affirme a cote du mot
    `au dossier`.

    Rend `None` quand aucune assertion vivante ne porte ce controle: il n'y a
    alors rien a citer, et la cellule dit deja l'absence.

    Chacun des trois elements manque independamment des autres. Mesure du
    2026-09-07: sur un coffre, 10 des 65 seuils retenus n'ont pas de page mais
    ont une ancre (`segment 38`); et une piece citee sur trois n'a aucune ligne
    dans le registre des convocations, donc aucun nom lisible. On rend ce qu'on
    a, jamais une position reconstituee.
    """
    try:
        concurrentes = int(ligne.get(f"nb_{prefixe}") or 0)
    except (TypeError, ValueError):
        concurrentes = 0
    if concurrentes < 1:
        return None
    page = str(ligne.get(f"src_{prefixe}_page") or "").strip()
    ancre = str(ligne.get(f"src_{prefixe}_ancre") or "").strip()
    doc_id = str(ligne.get(f"src_{prefixe}_doc_id") or "").strip()
    return {
        "doc_id": doc_id,
        "situe": ", ".join(x for x in (f"page {page}" if page else "", ancre) if x),
        "concurrentes": concurrentes,
        # Ce que la cellule nomme devient un chemin (`RM-2026-0157`). Il est
        # calcule ici, avec la page BRUTE - `situe` est deja une phrase, et
        # reconstruire un nombre depuis une phrase est le genre de detour qui
        # marche jusqu'au jour ou la phrase change.
        "href": chemin_de_piece(doc_id, page),
    }


def citation_acte(ligne: dict[str, Any]) -> dict[str, Any] | None:
    """Ou l'ACTE lui-meme a ete lu, pour la cellule qui rapporte son texte.

    Le texte de la resolution n'est pas un des sept controles: il ne verifie
    rien, il rapporte ce que le document dit. Sa source n'est donc pas un lien
    mais l'acte, avec sa propre page et sa propre ancre - `page 16`,
    `sous-point 11-1` sur les deux coffres mesures le 2026-09-07, renseignees
    sur 157 actes sur 157.

    `concurrentes` vaut 1 parce que la lecture de l'acte est deja tranchee en
    amont: `v_actes` fait gagner la correction humaine sur l'extraction. Les
    deux lectures ne sont pas perdues pour autant - `v_divergences_humaines`
    les oppose champ par champ - mais ce n'est pas ce que cette cellule montre.
    """
    page = str(ligne.get("src_acte_page") or "").strip()
    ancre = str(ligne.get("src_acte_ancre") or "").strip()
    doc_id = str(ligne.get("doc_id") or "").strip()
    if not (page or ancre or doc_id):
        return None
    return {
        "doc_id": doc_id,
        "situe": ", ".join(x for x in (f"page {page}" if page else "", ancre) if x),
        "concurrentes": 1,
        "href": chemin_de_piece(doc_id, page),
    }


def _fonde(ligne: dict[str, Any], portee: str) -> list[dict[str, Any]]:
    """Ce qui fonde la decision: plusieurs bulles, et des sous-bulles.

    Trois colonnes de la premiere version fusionnent ici. L'annexe n'est pas une
    colonne: elle est une **sous-bulle de la resolution**, parce qu'une annexe
    n'existe pas en soi - elle existe parce qu'une resolution y renvoie.
    """
    resolution = _cellule(ligne["cel_resolution"], portee, "", _L_RESOLUTION)
    resultat = str(ligne.get("resultat") or "")
    if resultat in RESULTATS:
        resolution["texte"] = _titre_acte(ligne) + ", " + RESULTATS[resultat].lower()
    # Pas de source sur une cellule `manquante`: elle dit qu'aucun acte n'a ete
    # trouve pour cet objet, et pointer une page a cote se contredirait.
    if resolution["statut"] not in ("manquante", "non_applicable"):
        resolution["citation"] = citation_acte(ligne)
    annexe = _cellule(ligne["cel_annexe"], portee, CTRL_ANNEXE, _L_ANNEXE,
                      citation=citation(ligne, "annexe"))
    resolution["sous"] = [annexe]

    bulles = [resolution]
    for valeur, controle, libelles, article, prefixe in (
        (ligne["cel_avis_cs"], CTRL_AVIS_CS, _L_AVIS,
         "Loi 65-557, article 21 alinéa 2", "avis_cs"),
        (ligne["cel_rapport_cs"], CTRL_RAPPORT_CS, _L_RAPPORT,
         "Décret 67-223, article 22 alinéa 2", "rapport_cs"),
        (ligne["cel_devis"], CTRL_DEVIS, _L_DEVIS,
         "Loi 65-557, article 21 alinéa 2", "devis"),
    ):
        # Le rapport annuel du conseil syndical n'est exigible que de deux
        # portees sur onze - l'approbation des comptes et la delegation. Ecrire
        # `non exige ici` sur les neuf autres serait du bruit et non une
        # information: un controle qui ne vise presque personne n'a pas a
        # s'annoncer chez tout le monde. Les quatre autres controles, eux,
        # visent la plupart des types: leur retrait EST une nouvelle, et il
        # reste affiche avec son motif de droit.
        if controle == CTRL_RAPPORT_CS and not controle_applicable(portee, controle):
            continue
        bulles.append(_cellule(valeur, portee, controle, libelles, legifrance=article,
                               citation=citation(ligne, prefixe)))
    return bulles


def _seuil(ligne: dict[str, Any], portee: str) -> list[dict[str, Any]]:
    """La colonne `Seuils franchis`: ce qu'elle retient, et ce qu'elle refuse.

    Le modele rattache un seuil a un acte; il ne compare **aucun** montant a
    aucun seuil. C'est le trou T9 du blueprint, ouvert. La colonne l'ecrit au
    lieu de colorier un franchissement qui n'a pas ete calcule.

    **Ce que cette cellule a cesse d'avouer, le 2026-09-08.** Elle ecrivait
    `l'outil retient le premier par ordre d'identifiant, ce qui n'est pas une
    regle` - une phrase exacte, et c'est bien le probleme: un ecran qui decrit
    son propre defaut ne le corrige pas, il le publie. Le choix ne se faisait
    pas ici mais dans l'ordre de tri du modele, qui departageait deux seuils
    egaux par leur identifiant de lien, c'est-a-dire par le rang de la
    resolution dans la convocation.

    La regle est celle de Brice, donnee deux fois le 2026-09-08: **le seuil
    applicable est le dernier vote**. Le modele l'applique maintenant par une
    date de deliberation (`ORDRE_CHRONOLOGIQUE`), et cette cellule rapporte
    l'une des deux issues possibles - le seuil retenu AVEC sa date, ou le fait
    que rien n'est tranchable ET pourquoi. Elle ne rapporte plus un tirage.

    **Ce que la separation des deux normes a change, le 2026-09-08.** Le detail
    precedent affirmait que les seuils concurrents `se contredisent`. Mesure du
    2026-09-08 sur deux coffres reels: les 299 liens de seuil visent deux
    resolutions du meme jour, l'une fixant le montant a partir duquel la
    consultation du conseil syndical devient obligatoire, l'autre celui a
    partir duquel la mise en concurrence l'est. **Deux normes distinctes, pas
    deux reponses a la meme question.** Le modele les separe desormais
    (`RM-2026-0144`), et cette colonne rend **une bulle par norme**, chacune
    nommant l'obligation qu'elle rapporte. Sur le meme corpus, les 121 actes
    qui se declaraient `non tranche` sont tous tranches sans qu'aucune regle
    d'arbitrage n'ait ete ajoutee: il n'y avait jamais eu de conflit, seulement
    une question mal posee.

    **Ce que la colonne montre encore quand la norme n'est pas attribuee.** Une
    troisieme bulle, et seulement dans ce cas. Un seuil rattache dont on ignore
    l'obligation qu'il declenche n'est pas une absence de seuil: le taire
    reviendrait a faire disparaitre le residu au lieu de le nommer.
    """
    if FORCE_VERS_STATUT.get(ligne["cel_seuil"]) == "non_applicable":
        # Un seul controle, donc un seul retrait et une seule phrase. Repeter
        # `non exige ici` par norme triplerait le bruit sur les cinquante-cinq
        # designations et modalites d'une assemblee, sans rien ajouter.
        bulle = _cellule(
            ligne["cel_seuil"], portee, CTRL_SEUIL, _L_SEUIL_RETIRE,
            legifrance="Loi 65-557, article 21 alinéa 2",
        )
        # `norme` vide: le retrait vaut pour les deux, il n'en designe aucune.
        bulle["norme"] = ""
        return [bulle]

    # Une bulle par norme DECLAREE, lue au registre et jamais enumeree ici.
    bulles = [
        _bulle_seuil(ligne, portee, norme.prefixe, _phrases(norme))
        for norme in NORMES_SEUIL
    ]
    # Le residu ne s'affiche que lorsqu'il existe. Une bulle
    # « norme non attribuée » vide sous chaque ligne serait du bruit; la meme
    # bulle tue quand un seuil y tombe serait un residu efface.
    if int(_nombre(ligne.get(f"nb_{NORME_NON_ATTRIBUEE.prefixe}")) or 0) >= 1:
        bulles.append(
            _bulle_seuil(ligne, portee, NORME_NON_ATTRIBUEE.prefixe,
                         _phrases(NORME_NON_ATTRIBUEE))
        )
    return bulles


def _bulle_seuil(
    ligne: dict[str, Any], portee: str, prefixe: str, libelles: dict[str, str]
) -> dict[str, Any]:
    """Une bulle de seuil, pour UNE norme nommee.

    Le prefixe designe a la fois la cellule, sa source, son nombre d'assertions
    et ce qui a tranche: `cel_seuil_concurrence`, `src_seuil_concurrence_page`,
    `nb_seuil_concurrence`, `cle_seuil_concurrence`. Un seul mot pour les
    quatre familles de colonnes, ce qui rend impossible d'afficher la force
    d'une norme a cote de la page d'une autre.
    """
    bulle = _cellule(
        ligne[f"cel_{prefixe}"], portee, CTRL_SEUIL, libelles,
        legifrance="Loi 65-557, article 21 alinéa 2",
        citation=citation(ligne, prefixe),
    )
    # **Le nom de la norme, en clair machine.** Le libelle affiche est accentue
    # et peut etre reecrit demain par un lot d'ecriture; ce champ ne l'est pas.
    # Sans lui, un lecteur - gabarit ou test - designerait la bulle par son RANG
    # dans la liste, et l'ajout d'une norme deplacerait silencieusement ce que
    # tout le monde croit lire.
    bulle["norme"] = prefixe
    rattaches = int(_nombre(ligne.get(f"nb_{prefixe}")) or 0)
    if rattaches >= 1:
        bulle["texte"], bulle["statut"], bulle["detail"] = _verdict_seuil(
            rattaches,
            _nombre(ligne.get(f"nb_{prefixe}_ex_aequo")),
            _date_de_deliberation(ligne.get(f"cle_{prefixe}")),
            bulle["texte"],
            bulle["statut"],
        )
    # Trois etats, et le troisieme n'est jamais un feu vert: un montant
    # illisible ne se lit pas comme *sous le seuil*.
    etat, motif = franchissement(
        ligne.get("montant_autorise"), ligne.get(f"montant_{prefixe}")
    )
    bulle["franchissement"] = etat
    bulle["detail"] += phrase_de_franchissement(etat, motif)
    return bulle


def _date_de_deliberation(valeur: Any) -> str:
    """La date qui a tranche, ou la chaine vide - jamais autre chose.

    **Trouve par le controle negatif du lot, et il n'etait pas theorique.** En
    remettant l'ordre probant sur les seuils, la cellule a imprime `Seuil arrete
    par la deliberation du HUMAIN_CONFIRME/PIECE_PRODUITE`: elle recopiait la
    valeur qui avait tranche en supposant que c'etait une date. Sous un ordre
    chronologique c'en est une; sous un autre ordre c'est une force probatoire,
    et rien dans la colonne ne le dit.

    La verification passe par `date_iso`, qui porte deja l'invariant du modele -
    une date a un jour, un mois et une annee de quatre chiffres, quelle que
    soit la maniere dont un cabinet l'ecrit. Une valeur qui n'est pas
    ordonnable n'est pas remplacee par une autre, ni reformatee: elle disparait,
    et l'appelant retombe sur la phrase `date non lue`, qui est vraie.
    """
    try:
        return date_iso(str(valeur or "").strip())
    except DateNonOrdonnable:
        return ""


def _verdict_seuil(
    rattaches: int,
    a_egalite: float | None,
    votee_le: str,
    texte: str,
    statut: str,
) -> tuple[str, str, str]:
    """Le seuil est-il tranche, et sinon pourquoi - en une phrase verifiable.

    `a_egalite` est le nombre de deliberations distinctes restees a egalite au
    sommet de l'ordre chronologique. `None` veut dire que la colonne n'a pas
    ete fournie: la degradation est alors le doute, jamais la confiance - on ne
    proclame pas tranchee une question dont on n'a pas la mesure.

    `votee_le` est la date de la deliberation retenue, ou la chaine vide quand
    elle n'a pas ete lue. **Une date vide n'est jamais remplacee par une autre
    date**: ni celle de l'acte, ni celle du jour. Le classement `le dernier
    vote l'emporte` se fait sur cette date ou ne se fait pas.

    Un seul seuil rattache est tranche par construction: il n'y a pas de
    depart a faire. Sa date peut manquer, et la phrase le dit alors au lieu de
    presenter une date qu'elle n'a pas.
    """
    tranche = rattaches == 1 or (a_egalite is not None and int(a_egalite) == 1)
    if tranche and votee_le:
        rang = (
            f", la plus récente des {rattaches} rattachées à cet acte"
            if rattaches > 1 else ", seule rattachée à cet acte"
        )
        return (
            texte, statut,
            f"Seuil arrêté par la délibération du {votee_le}{rang} : c'est le "
            "dernier vote qui fixe le seuil applicable."
        )
    if tranche:
        return (
            texte, statut,
            "Un seul montant de seuil est rattaché à cet acte. La date de la "
            "délibération qui l'a arrêté n'a pas été lue : il est retenu parce "
            "qu'il est seul, et non parce qu'il serait le plus récent."
        )
    combien = int(a_egalite) if a_egalite is not None else rattaches
    if votee_le:
        cause = (
            f"{combien} montants de seuil ont été arrêtés le même jour, le "
            f"{votee_le}. Le seuil applicable est le dernier voté : deux "
            "délibérations du même jour ne se départagent pas."
        )
    else:
        cause = (
            f"{rattaches} montants de seuil sont rattachés à cet acte, et la "
            "date de la délibération qui les a arrêtés n'a pas été lue. Le "
            "seuil applicable est le dernier voté : sans date, ce classement "
            "ne peut pas être fait."
        )
    return (
        texte + " : non tranché",
        "confirmer",
        cause + " Lequel s'applique n'est donc pas tranché, et l'outil ne "
        "choisit pas à la place de l'assemblée. La source citée ci-dessous "
        "est celle de l'une d'elles.",
    )


def _execution(ligne: dict[str, Any], portee: str) -> list[dict[str, Any]]:
    """La sixieme source: ce qui a ete vote a-t-il ete fait."""
    if FORCE_VERS_STATUT.get(ligne["cel_execution"]) == "non_applicable":
        return [_bulle(
            "non_applicable",
            "Exécution : non exigée ici",
            motif_hors_controle(portee, CTRL_EXECUTION) or "Ce contrôle n'a pas d'objet sur ce type.",
        )]
    rattachees = int(ligne.get("depenses_rattachees") or 0)
    vote = _nombre(ligne.get("montant_autorise"))
    paye = _nombre(ligne.get("montant_paye"))
    if not rattachees:
        return [_bulle(
            "manquante",
            "Rien de payé à ce jour",
            "Aucune dépense n'est rattachée à cet acte. Le lien entre un acte et un euro "
            "n'existe pas encore dans l'outil : c'est un état de l'outil, pas un constat "
            "sur la copropriété.",
        )]
    detail = f"{rattachees} dépense" + ("s rattachées" if rattachees > 1 else " rattachée")
    if vote is not None and paye is not None and abs(paye - vote) > 0.005:
        return [_bulle(
            "confirmer",
            f"Payé {euros(paye)} pour {euros(vote)} votés",
            detail + ". L'écart n'est pas conclu : il est posé.",
        )]
    return [_bulle("disponible", f"Facture rattachée, {euros(paye)}", detail + ".")]


def _nombre(valeur: Any) -> float | None:
    if valeur in (None, ""):
        return None
    try:
        return float(valeur)
    except (TypeError, ValueError):
        return None


def _titre_acte(ligne: dict[str, Any]) -> str:
    """Un titre lisible, jamais une reference interne de fichier (T13)."""
    nature = str(ligne.get("nature") or "")
    numero = str(ligne.get("numero") or "")
    if nature == "RESOLUTION_AG":
        sous = str(ligne.get("sous_numero") or "")
        marque = f"{numero}.{sous}" if sous else numero
        return f"Résolution {marque}" if marque else "Résolution sans numéro lu"
    return NATURES.get(nature, "Acte d'autorisation")


def _source_acte(ligne: dict[str, Any]) -> str:
    date = str(ligne.get("date_effet") or "")
    nature = str(ligne.get("nature") or "")
    if not date:
        return "Assemblée dont la date n'a pas été lue"
    if nature == "RESOLUTION_AG":
        return f"Assemblée du {date}"
    if nature == "DECISION_CS_DELEGUEE":
        return f"Décision du {date}"
    return f"Dépense engagée le {date}"


def _montant(ligne: dict[str, Any]) -> dict[str, Any]:
    """La colonne montant. **La couleur ne porte jamais l'information seule**:
    un pictogramme la nomme et un mot la double.
    """
    vote = _nombre(ligne.get("montant_autorise"))
    paye = _nombre(ligne.get("montant_paye"))
    rattachees = int(ligne.get("depenses_rattachees") or 0)
    if vote is None:
        return {
            "ton": "gris", "picto": "?", "valeur": "Aucun montant",
            "verdict": "Aucun montant lu sur la pièce",
            "lu_sur": "", "etat": "absent",
        }
    lu = {"CORPS_RESOLUTION": "lu dans le corps de la résolution",
          "ORDRE_DU_JOUR": "lu sur l'ordre du jour",
          "DEVIS_LIE": "lu sur le devis rattaché",
          "ANNEXE": "lu sur une annexe"}.get(str(ligne.get("montant_lu_sur") or ""), "")
    if rattachees and paye is not None and abs(paye - vote) > 0.005:
        return {"ton": "rouge", "picto": "X", "valeur": euros(vote),
                "verdict": f"{euros(paye)} payés pour ce montant voté",
                "lu_sur": lu, "etat": "divergent"}
    # 2026-09-13: un seuil ou un budget ne se paie pas; l'etat reste, le mot change.
    if not rattachees and vote > 0 and str(ligne.get("portee") or "") in ("SEUIL", "BUDGET_PREVISIONNEL"):
        return {"ton": "gris", "picto": "i", "valeur": euros(vote),
                "verdict": "Montant de référence, pas une dépense",
                "lu_sur": lu, "etat": "sans_execution"}
    if not rattachees and vote > 0:
        return {"ton": "orange", "picto": "?", "valeur": euros(vote),
                "verdict": "Aucune dépense rattachée par l'outil",
                "lu_sur": lu, "etat": "sans_execution"}
    return {"ton": "vert", "picto": "OK", "valeur": euros(vote),
            "verdict": "Voté et payé pour le même montant",
            "lu_sur": lu, "etat": "execute"}
