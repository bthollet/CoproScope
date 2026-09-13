"""L'ecran de controle de gouvernance: deux vues, une source.

Il remplace `/ag-contentieux` dans la navigation. Ce n'est pas une vingt-sixieme
entree: c'est la meme, qui cesse de rendre quatre parcours illustratifs et rend
le controle reel du mandat vers l'execution.

**Les trois questions auxquelles l'ecran repond**, et pas une de plus
(blueprint 3.1):

1. Ce qui a ete vote a-t-il ete fait ?
2. Ce qui a ete fait l'a-t-il ete comme il avait ete vote ?
3. Ce qui autorise aujourd'hui - seuils, delegations - est-il encore en vigueur ?

**La frontiere entre les deux vues**, et c'est elle qui justifie deux vues
plutot qu'une page longue: la synthese agit sur l'ENSEMBLE et jamais sur une
ligne; le tableau agit sur une LIGNE et jamais sur l'ensemble.

**Ce que ce module refuse de faire.** Il ne compte rien deux fois. Tout nombre
affiche par la synthese est `len(appliquer_filtres(...))`, et le tableau rend
`appliquer_filtres(...)` avec le meme filtre. Le lien porte le nombre annonce et
le tableau le compare: si un second chemin de calcul apparait un jour, l'ecran
le dit au lieu de mentir.
"""

from __future__ import annotations

from typing import Any

from ._controle_gouvernance_acces_piece import resumer_acces
from ._controle_gouvernance_accueil import habiller_pastilles, poser_signaux
from ._controle_gouvernance_panne import panne_instrument
from ..core.common import InstanceConfig
from ..modules import actes_autorisation as A
from . import _controle_gouvernance_constats as C
from ._controle_gouvernance_etat import (
    EXIGENCES_BACK,
    PRET,
    diagnostiquer,
)
from ._controle_gouvernance_source import (
    CHAMPS_BARRE,
    CHAMP_PAR_CLE,
    CONCLUSIONS,
    CONSTATS_HORS_ECRAN,
    NATURES,
    PORTEES,
    RESULTATS,
    STATUTS_BULLE,
    appliquer_filtres,
    construire_lignes,
    euros,
    libelle_filtres,
)

ROUTE = "/controle-gouvernance"

#: L'ordre des colonnes ne change jamais, quel que soit l'etat (CC-IT-020).
#: Six colonnes, pas huit: `Annexe visee`, `Mise en concurrence` et `Obligation
#: a echeance` ont fusionne dans `Ce qui la fonde`, qui porte plusieurs bulles.
#: L'annexe n'est pas une colonne - elle est une sous-bulle de la resolution qui
#: y renvoie, parce qu'une annexe n'existe pas en soi.
COLONNES = (
    ("Décision", "cs-col-decision"),
    ("Montant", "cs-col-montant"),
    ("Ce qui la fonde", "cs-col-fonde"),
    ("Seuils franchis", "cs-col-declencheur"),
    ("Exécution", "cs-col-execution"),
    ("Ma conclusion", "cs-col-conclusion"),
)


def lire_etat_url(params: Any) -> dict[str, Any]:
    """L'etat vit dans l'adresse. Un filtre pose survit a un aller-retour."""
    filtres: dict[str, str] = {}
    for cle, valeur in (params or {}).items():
        if cle.startswith("f_") and valeur and valeur != "toutes":
            court = cle[2:]
            if court in CHAMP_PAR_CLE:
                filtres[court] = str(valeur)
    attendu: int | None = None
    brut = str((params or {}).get("n") or "")
    if brut.isdigit():
        attendu = int(brut)
    return {
        "vue": "tableau" if str((params or {}).get("vue") or "") == "tableau" else "synthese",
        "filtres": filtres,
        "attendu": attendu,
        "constat": str((params or {}).get("constat") or ""),
        "ligne": str((params or {}).get("ligne") or ""),
    }


def _charger(instance: InstanceConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    diagnostic = diagnostiquer(instance)
    if diagnostic["etat"] != PRET:
        return diagnostic, []
    matrice = A.matrice(instance)
    constats = A.constats(instance)
    traces = A.lire_table(instance, A.TABLE_TRACES)
    return diagnostic, construire_lignes(matrice, constats, traces)


def _hors_ecran(instance: InstanceConfig, diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    """Les constats qui portent sur une depense ou un document.

    Ils ne font pas de ligne ici - l'aiguillage 44/45 et la T.V.A. vivent sur
    l'ecran comptes. Les compter et les nommer evite le pire des deux mondes:
    les afficher au mauvais endroit, ou les faire disparaitre.
    """
    if diagnostic["etat"] != PRET:
        return []
    compte: dict[str, int] = {}
    for constat in A.constats(instance):
        if constat.get("sujet_kind") == "acte":
            continue
        code = str(constat.get("code"))
        if code in CONSTATS_HORS_ECRAN:
            compte[code] = compte.get(code, 0) + 1
    return [
        {"n": compte[code], "libelle": CONSTATS_HORS_ECRAN[code]}
        for code in sorted(compte, key=lambda c: -compte[c])
    ]


def _a_valider_seuil(confiance: str) -> str:
    """Ce que le lecteur doit faire de ce montant, selon la confiance de lecture.

    Trois phrases pour trois etats, et jamais la meme pour deux etats
    differents. La version precedente testait le mot `haute`, qu'aucun
    extracteur n'ecrit: les six seuils reels, tous lus `forte`, portaient
    l'avertissement du montant mal lu, et un montant dont la confiance n'avait
    pas ete lue n'en portait aucun.
    """
    if confiance == A.CONFIANCE_FORTE:
        return ""
    if confiance in A.CONFIANCES:
        return (
            f"Le montant a été lu avec une confiance {confiance} : relisez la résolution et "
            "confirmez-le. Tant qu'il n'est pas confirmé, le seuil est une hypothèse."
        )
    return (
        "L'outil n'a pas noté avec quelle assurance ce montant a été lu. Relisez la "
        "résolution avant de vous appuyer sur ce seuil."
    )


def _seuils_en_vigueur(instance: InstanceConfig, diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    """Le rappel des seuils, en tete du tableau.

    Les seuils arment tous les autres controles: ils sont donc rappeles avant
    eux, chacun portant sa source - la resolution qui l'arrete, sa date butoir,
    son article. Un montant seul ne suffit pas: une resolution peut poser des
    conditions plus fines qu'un nombre.
    """
    if diagnostic["etat"] != PRET:
        return []
    lignes = A.lire_vue(instance, "v_actes", [("portee", "eq", "SEUIL")], ordre="date_effet DESC")
    seuils = []
    for row in lignes:
        montant = str(row.get("montant_autorise") or "")
        confiance = str(row.get("confiance") or "")
        seuils.append({
            "nom": str(row.get("objet") or "Seuil arrêté par l'assemblée"),
            "valeur": euros(montant) if montant else "montant non lu",
            # Le vocabulaire est celui de l'extracteur: forte, moyenne, faible.
            # Une confiance non renseignee n'est pas une confiance forte: on ne
            # sait pas avec quelle assurance la valeur a ete lue, donc la
            # cellule le dit au lieu de laisser croire qu'elle est confirmee.
            "incertain": confiance != A.CONFIANCE_FORTE,
            "resolution": (
                f"Résolution {row.get('numero') or '?'} de l'assemblée du {row.get('date_effet')}"
                if row.get("date_effet") else "Résolution dont la date d'assemblée n'a pas été lue"
            ),
            # Tour 2 de l'expert: un seuil lu sur une resolution dont l'issue n'est
            # pas l'adoption n'est pas « en vigueur ». L'en-tete le dit au lieu
            # de l'affirmer contre la ligne.
            "adoption": "" if str(row.get("resultat") or "") == "ADOPTEE" else "adoption non établie",
            "butoir": str(row.get("valide_au") or "") or "non applicable",
            "legifrance": "Loi 65-557, article 21 alinéa 2",
            "a_valider": _a_valider_seuil(confiance),
        })
    return seuils


def _delegations(instance: InstanceConfig, diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    """Le seul controle qui ne se voit pas ligne a ligne: le cumul de la
    delegation contre son plafond, sur la periode et jamais sur l'exercice."""
    if diagnostic["etat"] != PRET:
        return []
    sorties = []
    for row in A.cumul_delegations(instance):
        plafond = row.get("plafond")
        cumul = float(row.get("cumul") or 0.0)
        if plafond in (None, ""):
            sorties.append({
                "objet": str(row.get("delegation_objet") or "Délégation au conseil syndical"),
                "plafond": "", "cumul": euros(cumul), "part": 0, "depasse": False,
                "phrase": "Aucun montant maximum n'a été lu sur cette délégation. "
                          "L'article 21-2 en exige un : son absence est une question, pas un blanc.",
            })
            continue
        plafond = float(plafond)
        sorties.append({
            "objet": str(row.get("delegation_objet") or "Délégation au conseil syndical"),
            "plafond": euros(plafond),
            "cumul": euros(cumul),
            "part": min(100, int(cumul / plafond * 100)) if plafond else 0,
            "depasse": cumul > plafond,
            "phrase": (
                f"{int(row.get('depenses_cumulees') or 0)} dépenses cumulées sur la période du "
                f"{row.get('valide_du') or '?'} au {row.get('valide_au') or '?'}. "
                + ("Le plafond voté est franchi. Ce contrôle se fait en cumul : aucune décision "
                   "prise isolément ne le montre." if cumul > plafond
                   else "Le plafond n'est pas atteint.")
            ),
        })
    return sorties


def _limites(diagnostic: dict[str, Any], lignes: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Ce que la lecture automatique n'a pas pu etablir.

    Chaque ligne est un COMPTE fait sur le coffre local et refait a chaque
    ouverture. Aucune n'est tenue a la main: une limite ecrite une fois ment a
    la premiere donnee qui change.

    Une limite est rendue en **fragments**, pas en HTML pre-assemble. Le gabarit
    du produit est en echappement automatique et un `|safe` y est refuse par un
    test de securite: une phrase composee cote Python avec des balises devrait
    etre desechappee pour s'afficher, ce qui ouvrirait la porte a l'injection
    sur la premiere donnee d'instance qui passerait par la.
    """
    total = len(lignes)
    sans_montant = sum(1 for l in lignes if l["montant"]["etat"] == "absent")
    sans_execution = sum(1 for l in lignes if l["statut_execution"] == "manquante")
    sans_date = sum(1 for l in lignes if not l["date_effet"])
    non_reconnu = sum(1 for l in lignes if l["portee"] == "ORDINAIRE")

    def phrase(*fragments: Any) -> list[dict[str, Any]]:
        return [
            {"texte": str(f[1]), "gras": True} if isinstance(f, tuple)
            else {"texte": str(f), "gras": False}
            for f in fragments
        ]

    limites = [
        phrase(
            ("n", diagnostic["resolutions"]),
            " résolutions sont lues au registre, et ",
            ("n", total),
            " actes sont versés dans le modèle relationnel qui porte les contrôles. Quand ces "
            "deux nombres diffèrent, c'est le versement entre les deux qui est incomplet, pas "
            "la copropriété qui est en défaut.",
        ),
        phrase(
            ("n", sans_montant), " décisions sur ", ("n", total),
            " n'énoncent aucun montant. Aucun contrôle de seuil ne leur a été appliqué, et "
            "cette absence n'est pas une conformité.",
        ),
        phrase(
            ("n", sans_execution),
            " décisions n'ont aucune dépense rattachée. Le lien entre un acte et un euro n'est "
            "posé par aucun code aujourd'hui : c'est un état de l'outil, pas un constat sur la "
            "copropriété.",
        ),
    ]
    if non_reconnu:
        limites.append(phrase(
            ("n", non_reconnu),
            " décisions n'ont aucun type reconnu. Tous les contrôles leur restent appliqués : "
            "c'est le seul cas où l'écran a le droit de se tromper, et il doit le dire.",
        ))
    if sans_date:
        limites.append(phrase(
            ("n", sans_date),
            " actes sont rattachés à une assemblée dont la date n'a pas été lue. Le titre "
            "affiché le dit ; il ne le remplace jamais par un identifiant de fichier.",
        ))
    # C054. Le pont nommait deja les copies concurrentes dans son resume de run;
    # l'ecran, lui, affichait trois fois la meme resolution avec deux issues
    # contradictoires sans jamais le dire. Un journal que personne n'ouvre n'est
    # pas un signalement.
    copies = sum(1 for l in lignes if l["copies"])
    if copies:
        rangs = len({l["copies"]["rang"] for l in lignes if l["copies"]})
        limites.append(phrase(
            ("n", copies),
            " décisions se partagent ", ("n", rangs),
            " numéros de résolution avec au moins une assemblée dont la date n'a pas été lue. "
            "Il peut s'agir du même procès-verbal lu plusieurs fois, ou d'assemblées "
            "différentes : rien dans les pièces ne permet de trancher, et CoproScope n'élit "
            "aucune copie. Chaque ligne concernée le dit sous son titre.",
        ))
    # **Cette limite disait le contraire jusqu'au 2026-09-10**: *aucun
    # franchissement n'est calcule, le modele ne compare aucun montant*. La
    # comparaison existe maintenant. Ce qui manque, ce n'est plus le calcul,
    # c'est le montant de la decision - et une page qui reclame du code la ou
    # il manque une donnee envoie son lecteur au mauvais endroit.
    limites.append(phrase(
        "Le franchissement d'un seuil est calculé quand les deux montants sont lisibles : "
        "celui de la décision et celui arrêté par l'assemblée. Quand l'un des deux manque, "
        "la ligne dit qu'elle ne sait pas — ce n'est pas un « non ». Un montant illisible lu "
        "comme « sous le seuil » affirmerait qu'aucune obligation ne s'applique.",
    ))
    return limites


# --------------------------------------------------------------------------
# Les deux vues
# --------------------------------------------------------------------------


def build_controle_gouvernance_view(
    instance: InstanceConfig,
    year: int,
    params: Any = None,
    *,
    token: str = "",
) -> dict[str, Any]:
    """Le modele d'affichage des deux vues. Un seul calcul, deux rendus."""
    etat = lire_etat_url(params)
    diagnostic, lignes = _charger(instance)
    filtres = etat["filtres"]
    visibles = appliquer_filtres(lignes, filtres)
    # Deux ensembles, jamais un seul. `marquees` est ce que les PIECES
    # etablissent - c'est le nombre qui commande le courrier au syndic.
    # `marquees_outil` est ce que l'outil n'a pas encore ecrit. Les additionner
    # faisait annoncer « 157 points a instruire » sur un modele qui portait six
    # constats, et presentait le vide d'une table du produit comme un
    # manquement de la copropriete, fondement de droit a l'appui.
    marquees = C.lignes_marquees(lignes, source=C.SOURCE_PIECES)
    marquees_outil = C.lignes_marquees(lignes, source=C.SOURCE_OUTIL)
    for ligne in lignes:
        # La chaine n'est ROMPUE que par une piece. Une cellule vide parce
        # qu'aucun code ne la remplit n'est pas une rupture de chaine.
        ligne["rompu"] = ligne["id"] in marquees
        ligne["outil"] = ligne["id"] in marquees_outil
    poser_signaux(lignes)

    # Un arret de tabulation par ligne, et il porte la meme decision que la
    # ligne: le tableau montre, le panneau agit. Trois boutons par ligne
    # coutaient trois arrets, soit plusieurs centaines sur un exercice complet.
    for ligne in visibles:
        ligne["href"] = C.url_vue(
            ROUTE, "tableau", filtres,
            constat=etat["constat"], ligne=ligne["id"], token=token,
        )

    constats = []
    constats_outil = []
    for constat in C.CONSTATS:
        mesure = C.mesurer(lignes, constat)
        if not mesure["n"]:
            continue
        # `RM-2026-0183`: la pastille filtre la liste de l'ACCUEIL, sur place.
        mesure["lien"] = C.url_vue(
            ROUTE, "synthese", constat["filtre"],
            constat=constat["cle"], attendu=mesure["n"], token=token,
        ) + "#cs-liste"
        if constat["source"] == C.SOURCE_OUTIL:
            constats_outil.append(mesure)
        else:
            constats.append(mesure)

    constats = habiller_pastilles(constats, etat["constat"], filtres)
    constats_outil = habiller_pastilles(constats_outil, etat["constat"], filtres)
    selection = next((l for l in lignes if l["id"] == etat["ligne"]), None)
    arithmetique = C.arithmetique(lignes)
    calme = [l for l in lignes if not l["rompu"]]
    couverture = _couverture(year, lignes)

    return {
        "route": ROUTE,
        "vue": etat["vue"],
        "diagnostic": diagnostic,
        # Ce que les pieces citees montreront, dit UNE fois (`RM-2026-0157`).
        # La phrase par citation aurait ete rendue 621 fois a l'identique sur le
        # corpus du lot, et l'information utile est un nombre de pieces a
        # arbitrer, pas un rappel repete sous chaque cellule.
        "acces_pieces": resumer_acces(lignes, diagnostic.get("acces") or {}),
        "disponible": diagnostic["etat"] == PRET and bool(lignes),
        "exigences_back": EXIGENCES_BACK,
        "identite": {
            "nom": instance.display_name,
            "exercice_courant": str(year),
            "exercices": couverture["exercices"],
            "couverture": couverture["phrase"],
            "total": len(lignes),
            "resolutions": diagnostic["resolutions"],
        },
        "onglets": [
            {"cle": "synthese", "label": "Liste", "n": len(marquees),
             "actif": etat["vue"] == "synthese",
             "href": C.url_vue(ROUTE, "synthese", filtres, token=token)},
            {"cle": "tableau", "label": "Tableau détaillé", "n": len(visibles),
             "actif": etat["vue"] == "tableau",
             "href": C.url_vue(ROUTE, "tableau", filtres, token=token)},
        ],
        # Le titre ne nomme plus un exercice. Le parametre `year` de la route ne
        # filtrait rien: 2024 et 2026 rendaient les memes lignes sous deux
        # titres differents. Et il ne DOIT pas filtrer - les controles de cet
        # ecran traversent les exercices par construction, un seuil vote en 2024
        # pour vingt-quatre mois s'appliquant a une depense de 2026. Ce qui
        # etait faux n'etait pas l'absence de filtre, c'etait le titre.
        "titre": (
            "Ce que les pièces établissent, et ce qu'il reste à faire"
            if etat["vue"] == "synthese"
            else (f"{selection['titre']} — {selection['objet']}" if selection
                  else "Décisions et marchés versés dans le modèle")
        ),
        "lead": _lead(etat["vue"], lignes, marquees, marquees_outil, visibles, selection),
        "constats": constats,
        "constats_par_cle": C.CONSTAT_PAR_CLE,
        "accueil": {"tout_href": C.url_vue(ROUTE, "synthese", {}, token=token) + "#cs-liste"},
        "constats_outil": constats_outil,
        "a_outiller": len(marquees_outil),
        "arithmetique": arithmetique,
        "a_demander": len(marquees),
        "calme": len(calme),
        "hors_ecran": _hors_ecran(instance, diagnostic),
        "delegations": _delegations(instance, diagnostic),
        "seuils": _seuils_en_vigueur(instance, diagnostic),
        "colonnes": COLONNES,
        "champs": [
            {
                "cle": champ["cle"],
                "label": champ["label"],
                "actif": bool(filtres.get(champ["cle"])),
                "valeur": filtres.get(champ["cle"], "toutes"),
                "options": [("toutes", "Toutes")] + list(champ["options"].items()),
            }
            for champ in CHAMPS_BARRE
        ],
        "provenance": _provenance(etat, filtres, lignes, visibles, token),
        "lignes": visibles,
        "total": len(lignes),
        "ruptures_visibles": sum(1 for l in visibles if l["rompu"]),
        "selection": selection,
        # **Le retour apres ecriture d'une conclusion.** Il ramene a CETTE
        # ligne, filtres compris, parce que l'etat de cet ecran vit dans
        # l'adresse: sans lui, conclure ferait perdre le filtre pose et la
        # ligne ouverte, et l'utilisateur devrait refaire son chemin.
        "retour": C.url_vue(
            ROUTE, etat["vue"], filtres,
            constat=etat["constat"], ligne=etat["ligne"], token=token,
        ),
        # Le sort de la derniere tentative, repris de l'adresse. Un formulaire
        # qui rejette sans le dire fait croire a l'utilisateur qu'il a conclu.
        "conclusion_ecrite": str(params.get("conclusion_ecrite") or ""),
        "conclusion_refus": str(params.get("conclusion_refus") or ""),
        "fermer_url": C.url_vue(ROUTE, "tableau", filtres, constat=etat["constat"], token=token),
        "limites": _limites(diagnostic, lignes),
        "conclusions": CONCLUSIONS,
        "statuts": STATUTS_BULLE,
        "natures": NATURES,
        "portees": PORTEES,
        "resultats": RESULTATS,
        "token": token,
    }


def _couverture(year: int, lignes: list[dict[str, Any]]) -> dict[str, Any]:
    """Quels exercices l'écran couvre RÉELLEMENT, dit en toutes lettres.

    Le paramètre `year` de la route ne filtre rien sur cet écran, et il ne doit
    pas le faire : un seuil voté en 2024 pour vingt-quatre mois arme le contrôle
    d'une dépense de 2026, et `liens_seuil` a été écrit pour que ce lien
    traverse les exercices sans qu'aucune requête ne prenne d'année en
    paramètre. Ce qui était faux, c'était le titre : « L'exercice 2026 » sur des
    lignes de 2024, mesuré identique pour `year=2024` et `year=2026`.

    On affiche donc l'exercice courant de l'application ET les exercices que les
    lignes portent, pour que l'écart se voie au lieu d'être caché par un titre.
    """
    exercices = sorted({l["exercice"] for l in lignes if l["exercice"]})
    hors = sum(1 for l in lignes if not l["exercice"])
    if not lignes:
        return {"exercices": [], "phrase": ""}
    if exercices:
        etendue = (
            f"exercice {exercices[0]}" if len(exercices) == 1
            else "exercices " + ", ".join(exercices)
        )
    else:
        etendue = "aucun exercice lisible"
    phrase = (
        f"Tous exercices confondus : {etendue}. Les contrôles traversent les "
        f"exercices — un seuil voté une année arme le contrôle des années "
        f"suivantes — donc cet écran ne se limite pas à l'exercice {year} de "
        f"l'application."
    )
    if hors:
        phrase += (
            f" {hors} actes n'ont aucun exercice lisible : leur date d'assemblée "
            "n'a pas été lue."
        )
    return {"exercices": exercices, "phrase": phrase}


def _lead(
    vue: str,
    lignes: list[dict[str, Any]],
    marquees: set[str],
    marquees_outil: set[str],
    visibles: list[dict[str, Any]],
    selection: dict[str, Any] | None,
) -> str:
    if vue == "synthese":
        if not lignes:
            return "Aucun acte n'est encore versé dans le modèle"
        # Deux nombres, jamais leur somme. Le premier se réclame au syndic, le
        # second se réclame à l'outil : les additionner faisait annoncer 157
        # points sur un modèle qui en portait six.
        # La seconde phrase, sur les lignes de l'outil, vit dans les pastilles.
        return f"{len(marquees)} points à instruire sur {len(lignes)} décisions lues, établis par les pièces."
    if selection:
        montant = selection["montant"]
        return (
            f"{NATURES.get(selection['nature'], 'Acte')} — {selection['source']} — "
            + (montant["valeur"] if montant["etat"] != "absent" else "aucun montant énoncé")
        )
    rompues = sum(1 for l in visibles if l["rompu"])
    return f"{len(visibles)} lignes affichées, {rompues} avec une chaîne rompue"




def _provenance(
    etat: dict[str, Any],
    filtres: dict[str, str],
    lignes: list[dict[str, Any]],
    visibles: list[dict[str, Any]],
    token: str,
) -> dict[str, Any]:
    """D'ou l'on vient, et comment revenir.

    Le titre du constat clique est affiche, chaque filtre pose est une puce que
    l'on retire une par une, et deux sorties sont permanentes. Le nombre annonce
    par la synthese est compare a celui que le tableau trouve: avec un predicat
    unique la comparaison ne peut pas echouer, et c'est pour cela qu'elle est
    faite.
    """
    puces = libelle_filtres(filtres)
    constat = C.CONSTAT_PAR_CLE.get(etat["constat"])
    panne = panne_instrument(etat["attendu"], len(visibles))
    return {
        "actif": bool(puces),
        "panne": panne,
        "divergent": panne is not None,
        "attendu": etat["attendu"],
        "trouve": len(visibles),
        "titre": constat["titre"] if constat else "",
        "aide": constat["aide"] if constat else "",
        "intention": constat["intention"] if constat else "",
        "total": len(lignes),
        "puces": [
            {**puce, "href": C.url_sans_filtre(
                ROUTE, filtres, puce["cle"], constat=etat["constat"], token=token, vue=etat["vue"])}
            for puce in puces
        ],
        # Retirer un filtre ne change pas de vue: sur l'accueil, on reste sur la liste.
        "tout_href": C.url_vue(ROUTE, etat["vue"], {}, token=token),
        "retour_href": C.url_vue(ROUTE, "synthese", filtres, token=token),
    }
