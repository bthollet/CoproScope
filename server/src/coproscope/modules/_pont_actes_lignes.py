"""Ce que le pont ECRIT: un acte, ses attributs, ses liens.

Moitie ecriture du pont. Elle ne lit aucun fichier et n'ouvre aucune base: elle
prend des `Candidat` et rend des dictionnaires prets pour `_actes_store.ecrire`.
C'est ce qui la rend testable sans instance et sans coffre.

----------------------------------------------------------------------
Les trois regles que ce module tient, et pourquoi elles sont ici
----------------------------------------------------------------------

**1. L'identite passe par `acte_id_resolution`, sous-numero compris.** Un
cabinet du corpus numerote `11-1`, `11-2`, `11-3`, `11-4`: quatre offres
concurrentes, quatre projets a voter. Le couple (date, numero) seul les aurait
ecrases sur un acte unique, et les trois montants ecartes auraient disparu sans
bruit. Mesure du 2026-09-04 sur l'instance a deux exercices: **78 sous-points
sur une seule convocation**, dont soixante-quatre portent un sous-numero.

**2. Aucun pourcentage de voix ne s'ecrit hors de `_decompte_voix`.** Ce module
n'a pas le droit de diviser deux nombres de voix. Il appelle
`decompte_resolution`, et il n'ecrit un pourcentage que si le verdict est
`affichable`, c'est-a-dire si une assiette a ete nommee. Sur l'assemblee etalon,
cela veut dire qu'un pourcentage sort pour les quarante-huit resolutions
appliquees sous l'article 24, et qu'il n'en sort aucun pour les six restees sous
l'article 25 - dont le denominateur est le total des voix du syndicat, que le
registre ne porte pas.

**3. Une force probatoire n'est jamais promue.** Le conseil syndical dont la
convocation affirme qu'il a ete consulte, sans qu'aucune piece soit jointe,
donne un lien `AFFIRME_SANS_PIECE` - `A confirmer` a l'ecran - et jamais
`PIECE_PRODUITE`. Mesure sur la meme convocation: **soixante-quatre avis
affirmes, zero piece produite.**
"""

from __future__ import annotations

from typing import Any, Iterable

from . import _decompte_voix as voix
from ._actes_schema import (
    acte_id_resolution,
    lien_id,
    montant_texte,
)
from ._actes_seuils_normes import norme_arretee
from ._montants import MontantIllisible
from ._actes_vocabulaire import (
    FORCE_AFFIRME,
    FORCE_PIECE,
    KIND_ACTE,
    KIND_DEVIS_CITE,
    KIND_DOCUMENT,
    NATURE_RESOLUTION_AG,
    ORIGINE_EXTRAIT,
    PORTEE_ENGAGEMENT_DEPENSE,
    PORTEE_ORDINAIRE,
    PORTEE_SEUIL,
    PROV_CALCUL,
    PROV_SYNDIC,
    REL_AVIS_CS,
    REL_DEVIS_RETENU,
    RESULTAT_ADOPTEE,
    SOURCE_ABSENTE,
    SOURCE_CORPS,
    SOURCE_ILLISIBLE,
    SOURCE_ORDRE_DU_JOUR,
)
from ._pont_actes_source import (
    _lu,
    Candidat,
    etat_du_candidat,
    exercice_de,
    exercice_vise,
    issue_acte,
    majorite_lue,
)

#: Les noms d'attribut que ce pont produit, en plus de ceux que
#: `_actes_schema.ATTRIBUTS_CONNUS` declarait deja. Ils sont nommes ici pour que
#: le meme fait ne soit pas range sous deux noms selon la source.
ATTR_EXERCICE_VISE = "exercice_vise"
ATTR_DISCORDANCE = "discordance_intitule_corps"
ATTR_PASSERELLE = "passerelle_25_1_utilisee"
ATTR_ASSIETTE = "assiette_du_decompte"
ATTR_PART_VOIX = "part_des_voix_pour"
ATTR_CONSTAT_DENOMINATEUR = "denominateur_imprime_divergent"
ATTR_ANALYSE_OFFRES = "analyse_offres_affirmee"
ATTR_PASSERELLE_CITEE = "passerelle_25_1_citee"
ATTR_PORTEE_MOTIF = "portee_non_reconnue_motif"
#: Sur une resolution de portee `SEUIL`, LAQUELLE des deux obligations de
#: l'article 21 alinea 2 elle arrete. Ecrit meme quand la reponse est
#: `non attribuee`, avec son motif: c'est ce qui permet de verifier a la main le
#: classement des liens de seuil sans relire le code, et de compter le residu.
ATTR_NORME_SEUIL = "norme_seuil_arretee"
ATTR_NORME_SEUIL_MOTIF = "norme_seuil_non_attribuee_motif"

#: Ce que le pont ecrit quand `portee_resolution` n'a rien trouve a dire. Une
#: portee `ORDINAIRE` sans motif est un blanc, et un blanc se lit a l'ecran
#: comme un type que l'outil aurait examine et rejete. Il ne l'a pas examine:
#: aucune des onze regles ne s'est declenchee sur ce corps.
MOTIF_AUCUNE_REGLE = (
    "aucune des onze regles de typage ne s'est declenchee sur le corps de "
    "cette resolution: le type n'est pas rejete, il n'est pas determine"
)

#: Les voix ENONCEES par le proces-verbal, colonne du registre -> nom d'attribut.
#: Ce ne sont pas des valeurs derivees: `_decompte_voix` les CONSOMME pour
#: produire une part, et jusqu'au 2026-09-04 il les consommait sans les laisser
#: derriere lui. Consequence mesuree: apres versement, le modele portait la part
#: des voix pour et plus les voix elles-memes, donc aucun moyen de refaire le
#: calcul ni de repondre a « cette resolution atteignait-elle la majorite de
#: l'article 25 ». On verse le fait brut a cote de la valeur derivee, avec deux
#: provenances distinctes: le syndic affirme, CoproScope calcule.
VOIX_VERSEES: tuple[tuple[str, str], ...] = (
    ("voix_pour", "voix_pour"),
    ("voix_contre", "voix_contre"),
    ("voix_abstention", "voix_abstention"),
    ("base_voix", "denominateur_imprime"),
    ("voix_relevees", "voix_relevees_brutes"),
)


def _entier(valeur: str) -> int | None:
    texte = (valeur or "").strip()
    if not texte.isdigit():
        return None
    return int(texte)


def acte_id_du_candidat(candidat: Candidat) -> str:
    ligne = candidat.ligne
    return acte_id_resolution(
        candidat.date_ag,
        ligne.get("numero", ""),
        sous_numero=ligne.get("sous_numero", ""),
        doc_id=ligne.get("doc_id", ""),
    )


def _ag_id(candidat: Candidat) -> str:
    ligne = candidat.ligne
    if candidat.source == "DEVIS_CITE":
        return f"AG-{candidat.date_ag}" if candidat.date_ag else ligne.get(
            "convocation_id", ""
        )
    return ligne.get("ag_id", "")


def _ancre(candidat: Candidat) -> str:
    """Ou la ligne a ete lue, en clair et sans citer de chemin local."""
    ligne = candidat.ligne
    if candidat.source == "DEVIS_CITE":
        numero = ligne.get("numero", "")
        sous = ligne.get("sous_numero", "")
        return f"sous-point {numero}-{sous}" if sous else f"point {numero}"
    return f"segment {ligne.get('position', '')}"


def _montant_et_source(candidat: Candidat) -> tuple[str, str]:
    """Le montant autorise, et **ou il a ete lu**.

    La colonne de localisation n'est pas un ornement: le meme fait vit dans le
    corps de la resolution chez un cabinet et dans une piece jointe chez
    l'autre. Une colonne qui presume le cote se trompe au deuxieme syndic; une
    colonne qui le nomme reste vraie chez les deux.

    Elle porte aussi `ILLISIBLE`, qui n'est pas `ABSENT`: un seuil ecrit
    `2.500` dans une resolution n'est pas un seuil qui manque, c'est un seuil
    qu'il faut aller relire sur la piece.

    **Ou s'arrete cet etat, au 2026-09-05.** Il est ecrit dans la colonne
    `montant_source` de la table des actes, et il s'arrete la. `v_acte_effectif`
    ne lit `montant_source` que dans sa branche `WHEN a.montant_autorise <> ''`;
    un montant illisible ayant par construction un `montant_autorise` vide,
    `montant_lu_sur` retombe sur `ABSENT` et l'ecran affiche "Aucun montant".
    C'est mesure, pas suppose. La ligne stockee est donc **vraie** - elle ne
    pretend plus qu'aucun montant n'etait ecrit - mais la distinction ne remonte
    pas encore aux vues: cette propagation appartient a la zone vues, qui
    possede `_actes_vues.py`. Ne pas ecrire ailleurs qu'ici du code qui suppose
    l'inverse tant que `v_acte_effectif` n'a pas ete ouverte.
    """
    ligne = candidat.ligne
    if candidat.source == "DEVIS_CITE":
        montant, illisible = _lu(ligne.get("montant_ttc", ""))
        if montant:
            return montant, SOURCE_ORDRE_DU_JOUR
        return "", SOURCE_ILLISIBLE if illisible else SOURCE_ABSENTE
    # Voie resolutions: le corps fait foi, l'intitule est conserve pour que la
    # divergence se voie - c'est deja la regle de `valeurs_seuil`.
    montant, illisible_corps = _lu(ligne.get("montant_seuil", ""))
    if montant:
        return montant, SOURCE_CORPS
    intitule, illisible_intitule = _lu(ligne.get("montant_intitule", ""))
    if intitule:
        return intitule, SOURCE_ORDRE_DU_JOUR
    if illisible_corps or illisible_intitule:
        return "", SOURCE_ILLISIBLE
    return "", SOURCE_ABSENTE


def ligne_acte(candidat: Candidat) -> dict[str, str]:
    """Un acte d'autorisation, derive d'une ligne de registre."""
    ligne = candidat.ligne
    montant, montant_source = _montant_et_source(candidat)
    entreprise = ligne.get("entreprise", "")
    issue_brute = (
        "PROJET" if candidat.source == "DEVIS_CITE" else ligne.get("resultat", "")
    )
    return {
        "acte_id": acte_id_du_candidat(candidat),
        "nature": NATURE_RESOLUTION_AG,
        "etat": etat_du_candidat(candidat),
        "portee": candidat.portee,
        "date_effet": candidat.date_ag,
        "exercice": exercice_de(candidat.date_ag),
        "ag_id": _ag_id(candidat),
        "numero": ligne.get("numero", ""),
        "sous_numero": ligne.get("sous_numero", ""),
        "objet": ligne.get("objet", ""),
        "montant_autorise": montant,
        "entreprise": entreprise,
        "montant_source": montant_source,
        "entreprise_source": SOURCE_ORDRE_DU_JOUR if entreprise else SOURCE_ABSENTE,
        "valide_du": ligne.get("valide_du", ""),
        "valide_au": ligne.get("valide_au", ""),
        "majorite_annoncee": majorite_lue(ligne.get("majorite_annoncee", "")),
        # Ce que la LOI exige pour cet objet. Le pont ne le sait pas: aucune
        # table du depot n'associe une portee a une majorite, et l'ecrire ici
        # serait poser du droit dans un module de transport. La colonne reste
        # vide, et le controle `annoncee contre requise` attend sa source.
        "majorite_requise": "",
        "majorite_appliquee": ligne.get("majorite_appliquee", ""),
        "resultat": issue_acte(issue_brute),
        "resolution_id": ligne.get("resolution_id", "")
        or ligne.get("devis_cite_id", ""),
        "page": ligne.get("page", ""),
        "ancre": _ancre(candidat),
        # Un acte type sur un enonce reconstitue ne vaut pas un acte type sur le
        # corps du document: la portee peut se tromper sur un objet tronque.
        "confiance": (
            "moyenne" if candidat.source == "DEVIS_CITE"
            else ligne.get("confiance", "moyenne")
        ),
        "doc_id": ligne.get("doc_id", ""),
        "origine": ORIGINE_EXTRAIT,
    }


# --------------------------------------------------------------------------
# Attributs
# --------------------------------------------------------------------------


def _attribut(
    acte: dict[str, str], nom: str, valeur: str, provenance: str
) -> dict[str, str]:
    return {
        "attribut_id": f"{acte['acte_id']}|{nom}",
        "acte_id": acte["acte_id"],
        "nom": nom,
        "valeur": valeur,
        "provenance": provenance,
        "page": acte.get("page", ""),
        "ancre": acte.get("ancre", ""),
        "doc_id": acte.get("doc_id", ""),
        "origine": ORIGINE_EXTRAIT,
    }


def _decompte(candidat: Candidat) -> voix.Verdict | None:
    """Le verdict du decompte des voix, ou `None` s'il n'y a rien a compter.

    **Le seul appel de tout le pont qui touche a des voix.** Aucune division
    n'est ecrite ailleurs, et c'est la promesse que porte `_decompte_voix`:
    aucun pourcentage ne sort d'une assiette inconnue.

    `voix_totales` n'est pas fourni, et ce n'est pas un oubli: le total des voix
    du syndicat n'est pas une colonne du registre, et le denominateur imprime
    n'en tient pas lieu - c'est exactement ce que le module refuse de confondre.
    Consequence tenue: les resolutions restees sous l'article 25 rendent
    `ASSIETTE_INDETERMINEE` au lieu d'un pourcentage faux.
    """
    ligne = candidat.ligne
    if candidat.source == "DEVIS_CITE":
        return None
    pour = _entier(ligne.get("voix_pour", ""))
    if pour is None:
        return None
    return voix.decompte_resolution(
        ligne.get("majorite_appliquee", "") or ligne.get("majorite_annoncee", ""),
        voix_pour=pour,
        voix_contre=_entier(ligne.get("voix_contre", "")),
        voix_abstention=_entier(ligne.get("voix_abstention", "")),
        denominateur_ecrit=_entier(ligne.get("base_voix", "")),
    )


def lignes_attributs(candidat: Candidat, acte: dict[str, str]) -> list[dict[str, str]]:
    """Les faits qui n'ont pas de colonne, et qui n'en meritent pas une.

    La zone d'extension recoit deux familles, et leur `provenance` les separe:
    ce que le document ENONCE (`SYNDIC_AFFIRME`) et ce que CoproScope CALCULE
    (`COPROSCOPE_CALCULE`). Le second usage etend l'intention d'origine - la
    zone a ete concue pour les variants d'ecriture - et il est assume: la
    solution alternative aurait ete d'ajouter au noyau une colonne par valeur
    derivee, c'est-a-dire de figer dans le schema ce qui doit pouvoir changer
    avec la regle. Le jour ou une de ces valeurs devient un controle exige
    partout, elle migre vers une colonne, comme le prescrit `ATTRIBUTS_CONNUS`.
    """
    ligne = candidat.ligne
    attributs: list[dict[str, str]] = []

    # Un type non reconnu dit POURQUOI il ne l'est pas. `portee_resolution`
    # calculait deja ses indices et le pont les jetait: le seul etat de l'ecran
    # ou le produit a le droit de se tromper etait aussi le seul qui ne
    # s'expliquait pas.
    if candidat.portee == PORTEE_ORDINAIRE:
        attributs.append(
            _attribut(
                acte,
                ATTR_PORTEE_MOTIF,
                " ; ".join(candidat.portee_indices) or MOTIF_AUCUNE_REGLE,
                PROV_CALCUL,
            )
        )

    # Une resolution qui ARRETE un seuil dit laquelle des deux obligations elle
    # arme. L'attribut est ecrit dans les deux cas - attribuee ou non - parce
    # qu'une absence d'attribut se lirait comme une absence de question posee.
    if candidat.portee == PORTEE_SEUIL:
        norme, motif = norme_arretee(ligne.get("qualifications", ""))
        attributs.append(
            _attribut(acte, ATTR_NORME_SEUIL, norme.relation, PROV_CALCUL)
        )
        if motif:
            attributs.append(
                _attribut(acte, ATTR_NORME_SEUIL_MOTIF, motif, PROV_CALCUL)
            )

    vise = exercice_vise(candidat.segment)
    if vise and vise != acte["exercice"]:
        # Une assemblee de 2024 arrete des comptes de 2023. Les deux annees sont
        # vraies, elles ne disent pas la meme chose, et une colonne unique aurait
        # fait perdre l'une des deux.
        attributs.append(_attribut(acte, ATTR_EXERCICE_VISE, vise, PROV_SYNDIC))

    if candidat.source == "DEVIS_CITE":
        if ligne.get("cle_repartition"):
            attributs.append(
                _attribut(acte, "cle_repartition", ligne["cle_repartition"], PROV_SYNDIC)
            )
        if ligne.get("montant_intitule") and ligne.get("discordance_intitule_corps"):
            attributs.append(
                _attribut(
                    acte, ATTR_DISCORDANCE,
                    ligne["discordance_intitule_corps"], PROV_SYNDIC,
                )
            )
        if (ligne.get("analyse_offres_affirmee") or "").lower() == "oui":
            attributs.append(
                _attribut(acte, ATTR_ANALYSE_OFFRES, "oui", PROV_SYNDIC)
            )
        return attributs

    if ligne.get("divergences"):
        attributs.append(
            _attribut(acte, ATTR_DISCORDANCE, ligne["divergences"], PROV_SYNDIC)
        )
    # Les voix, avant tout calcul. Une colonne vide n'ecrit rien: le registre
    # laisse `voix_pour` vide sur 44 lignes sur 173, et fabriquer un « 0 » y
    # transformerait « le PV ne chiffre pas » en « personne n'a vote pour ».
    for colonne, nom in VOIX_VERSEES:
        valeur = (ligne.get(colonne) or "").strip()
        if valeur:
            attributs.append(_attribut(acte, nom, valeur, PROV_SYNDIC))

    # `passerelle_citee` est renseignee sur 173 lignes sur 173 et n'avait aucune
    # destination. Elle ne dit pas la meme chose que `passerelle_utilisee`: la
    # premiere est ce que le proces-verbal ANNONCE comme regime possible, la
    # seconde ce que l'assemblee a FAIT. Les confondre, c'est perdre le seul
    # ecart qui distingue une passerelle offerte d'une passerelle empruntee.
    if (ligne.get("passerelle_citee") or "").lower() == "oui":
        attributs.append(_attribut(acte, ATTR_PASSERELLE_CITEE, "oui", PROV_SYNDIC))
    if (ligne.get("passerelle_utilisee") or "").lower() == "oui":
        # Le fait central de l'assemblee etalon: dix-huit resolutions annoncees
        # sous l'article 25 ont ete adoptees au second vote de l'article 25-1,
        # a la majorite de l'article 24. Sans cet attribut, la seule trace
        # serait l'ecart entre deux colonnes de majorite, qu'aucun filtre ne
        # nomme.
        attributs.append(_attribut(acte, ATTR_PASSERELLE, "oui", PROV_SYNDIC))

    verdict = _decompte(candidat)
    if verdict is None:
        return attributs
    if verdict.assiette:
        attributs.append(
            _attribut(acte, ATTR_ASSIETTE, verdict.assiette, PROV_CALCUL)
        )
    if verdict.affichable:
        attributs.append(
            _attribut(acte, ATTR_PART_VOIX, f"{verdict.pourcentage:.2f}", PROV_CALCUL)
        )
    for constat in verdict.constats:
        attributs.append(
            _attribut(acte, ATTR_CONSTAT_DENOMINATEUR, constat, PROV_CALCUL)
        )
    return attributs


def collisions(actes: Iterable[dict[str, str]]) -> dict[str, list[str]]:
    """Les identifiants d'acte revendiques par plusieurs documents.

    Une collision n'est pas un incident de programmation: c'est un fait du
    corpus, et il se mesure. Sur l'instance a deux exercices, le proces-verbal
    du 03/07/2024 existe en six exemplaires - un complet et cinq blocs decoupes
    par page - et chaque bloc renumerote ses resolutions a partir de 1. Le
    registre `resolutions` les a deja ecrasees en silence, par sa cle primaire:
    119 lignes ecrites, 63 conservees.

    Le pont refuse de reproduire ce silence. Il ne fusionne pas et ne choisit
    pas: il rend la liste, l'appelant la remonte, et un humain tranche quel
    exemplaire du proces-verbal fait foi.
    """
    par_id: dict[str, list[str]] = {}
    for acte in actes:
        docs = par_id.setdefault(acte["acte_id"], [])
        if acte["doc_id"] not in docs:
            docs.append(acte["doc_id"])
    return {cle: docs for cle, docs in par_id.items() if len(docs) > 1}


# --------------------------------------------------------------------------
# Liens
# --------------------------------------------------------------------------
# Ils vivent dans `_pont_actes_liens`. Ce module ne les reexporte PLUS: le
# reexport fermait un cycle d'import - `_pont_actes_liens` importait `_lu`
# d'ici, et d'ici on importait ses fonctions. `import _pont_actes_liens` seul
# echouait, et rien ne le voyait parce que `pont_actes` importe toujours ce
# module-ci en premier. `_lu` vit desormais dans `_pont_actes_source`, dont les
# deux dependent deja: le sens des imports est redevenu unique.

