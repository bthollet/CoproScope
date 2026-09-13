"""Ce qu'un statut de classement AFFIRME, et ce qui doit remonter a l'humain.

Ce module existe pour une raison mesuree, et il ne faut pas la perdre.

Le tri du classement produit deux etats de doute - `A_RECLASSER` quand le texte
est lu mais que le titre attendu manque, `TEXTE_INSUFFISANT` quand il n'y a rien
a lire. Le 2026-09-08, aucun des deux n'atteignait l'humain: la boite de
reception decidait ce qu'elle montrait avec une liste de statuts douteux -
`{"", "PENDING", "A_CLASSER", "UNCLASSIFIED", "TO_CLASSIFY", "PROPOSED"}` - et
les deux nouveaux etats n'y figuraient pas. Le doute produit par la regle livree
tombait dans le silence.

**Le defaut n'etait pas l'oubli de deux chaines, et c'est tout l'objet de ce
module.** Cette liste enumerait des MODALITES OBSERVEES. Elle devinait meme deux
valeurs que le code ne produit nulle part - `UNCLASSIFIED` et `TO_CLASSIFY` -
pendant qu'elle en manquait deux bien reelles. Y ajouter les deux manquantes
aurait fait passer ce cas et laisse le statut SUIVANT tomber dans le meme trou,
en silence.

AXE
    Ce qu'un statut affirme sur l'etat de la decision de classement.

INVARIANT LE LONG DE L'AXE
    Un document dont le classement n'est pas affirme comme ETABLI est un
    document que quelqu'un doit regarder. Seule la solidite de la decision varie
    le long de l'axe; le besoin de relecture quand elle n'est pas etablie, jamais.

CE QUE LE CODE EN FAIT
    Il declare la liste FERMEE des statuts qui affirment un classement etabli,
    chacun avec sa raison. Le critere de remontee est le COMPLEMENT de cette
    liste: doute, texte absent, attente, proposition non acceptee, valeur vide,
    ET tout statut que cette version ne connait pas.

HORS DES VALEURS OBSERVEES
    Un statut inconnu remonte, et il est NOMME comme non interprete au lieu
    d'etre range en silence dans "classe". La degradation va vers le
    signalement, jamais vers une couverture affirmee a tort. C'est la propriete
    que `server/tests/test_doute_classement_remonte.py` mesure avec un statut
    invente, que le code n'a jamais vu.

Ce module est la seule source de ce critere. Toute couche qui redemande "faut-il
montrer ce document" passe par ici, sinon la liste de modalites se reconstitue
ailleurs.
"""

from __future__ import annotations

# --- Les statuts qui AFFIRMENT un classement etabli --------------------------
#
# Liste fermee, et chaque entree porte ce qu'elle affirme. Un statut n'entre ici
# que s'il affirme les deux a la fois: le type est decide, ET la decision est
# posee. "En cours", "propose" et "je ne sais pas" n'y ont pas leur place.

#: Le classement a lu le contenu du document et en a conclu un type.
STATUT_LU_ET_DECIDE = "AUTO_CLASSIFIED"

#: Un humain a accepte la proposition de type. La decision lui appartient.
STATUT_ACCEPTE_PAR_UN_HUMAIN = "ACCEPTED"

#: Piece fictive engendree par le generateur de demonstration, qui ecrit
#: lui-meme le type qu'il vient de fabriquer. Il n'y a rien a relire: le type
#: n'est pas deduit, il est constitutif de la piece.
STATUT_PIECE_DE_DEMONSTRATION = "DEMO_CLASSIFIED"

CLASSEMENT_ETABLI: frozenset[str] = frozenset(
    {
        STATUT_LU_ET_DECIDE,
        STATUT_ACCEPTE_PAR_UN_HUMAIN,
        STATUT_PIECE_DE_DEMONSTRATION,
    }
)

# --- Pourquoi un document remonte -------------------------------------------
#
# Les raisons connues, et une raison par defaut pour ce que cette version ne
# sait pas lire. La raison par defaut n'est pas un filet de securite decoratif:
# c'est elle qui transforme un statut inconnu en signalement nomme.

MOTIF_STATUT_INCONNU = (
    "Statut de classement non interprete par cette version: a verifier a la main."
)

MOTIFS_DE_REMONTEE: dict[str, str] = {
    "": "Aucun statut de classement enregistre pour cette piece.",
    "PENDING": "Aucune proposition de type n'a encore ete faite.",
    "A_CLASSER": "Aucun type n'a pu etre decide. Piece a identifier a la main.",
    "PROPOSED": "Type propose, pas encore accepte par un humain.",
    "A_RECLASSER": "Contenu lu, mais le titre attendu manque: type a confirmer.",
    "TEXTE_INSUFFISANT": (
        "Aucun texte exploitable a lire: le type n'est ni confirme, ni infirme."
    ),
}


def normaliser_statut(statut: object) -> str:
    """Rend le statut en forme comparable: sans espaces, en majuscules."""
    return str(statut or "").strip().upper()


def classement_est_etabli(statut: object) -> bool:
    """Vrai seulement si le statut AFFIRME un classement etabli.

    Tout le reste - y compris un statut que cette version n'a jamais vu - rend
    Faux. C'est deliberement le sens sur - un document montre a tort coute une
    relecture, un document tu a tort ne coute rien de visible et fausse le
    compte des pieces restantes.
    """
    return normaliser_statut(statut) in CLASSEMENT_ETABLI


def doit_remonter_a_l_humain(statut: object) -> bool:
    """Complement de `classement_est_etabli`: le critere de la boite de reception."""
    return not classement_est_etabli(statut)


def motif_de_remontee(statut: object) -> str:
    """Dit POURQUOI le document remonte, ou "" si son classement est etabli.

    Un statut inconnu recoit `MOTIF_STATUT_INCONNU`: il remonte en disant qu'il
    n'a pas ete compris, au lieu de remonter sans explication - ce qui ferait
    porter a l'humain le travail de deviner ce que le code n'a pas su lire.
    """
    normalise = normaliser_statut(statut)
    if normalise in CLASSEMENT_ETABLI:
        return ""
    return MOTIFS_DE_REMONTEE.get(normalise, MOTIF_STATUT_INCONNU)


def statut_est_connu(statut: object) -> bool:
    """Vrai si cette version sait interpreter le statut, quel que soit son sens.

    Sert aux couches qui veulent distinguer "je doute" de "je ne comprends pas
    ce statut". Les deux remontent; elles ne se disent pas de la meme facon.
    """
    normalise = normaliser_statut(statut)
    return normalise in CLASSEMENT_ETABLI or normalise in MOTIFS_DE_REMONTEE

# ---------------------------------------------------------------------------
# Le TYPE du document, meme question, meme reponse
# ---------------------------------------------------------------------------
#
# **`RM-2026-0056`, residu mesure le 2026-09-11.** Ce module avait resolu la
# question pour le STATUT de classement. La meme question se posait pour le
# TYPE - *ce document a-t-il un type etabli ?* - et elle etait tranchee a
# **six endroits differents, chacun avec sa propre ecriture**:
#
#   `04_completeness_and_kpis:196`   `document_type in {"", "A_CLASSER"}`
#   `04_completeness_and_kpis:228`   `status == "A_CLASSER"`
#   `document_intake_route:202`      `document_type == "A_CLASSER"`
#   `document_intake_route:282`      `document_type == "A_CLASSER"`
#   `document_intake_route:333`      `document_type.upper() == "A_CLASSER"`
#   `_document_selection:8`          `document_type not in {"", "Document"}`
#
# **Elles divergent deja par ecrit**: l'une compte le type VIDE, une autre non,
# une troisieme normalise la casse, une quatrieme ajoute `Document`.
#
# **Sur le corpus, elles donnent pourtant le meme nombre - 83 sur 858 - et
# c'est precisement ce qui rend le defaut dangereux.** Elles coincident par
# ACCIDENT: aucun document de ce corpus ne porte un type vide. Or le modele
# admet explicitement le vide a l'ecriture. Le jour ou un document arrive sans
# type, `in {"", "A_CLASSER"}` le compte et `== "A_CLASSER"` ne le compte pas -
# deux compteurs pour la meme notion, divergeant en silence.
#
# **C'est le meme choix que le cas d'egalite du franchissement et que
# l'exclusion du contrat de syndic, tranches le meme jour: l'ecrire tant qu'il
# ne coute rien, plutot que le jour ou il decidera d'un chiffre affiche.**

#: Le type que le classement pose quand il n'a pas su decider. Il est DECLARE
#: ici parce que trois modules l'ecrivaient en litteral.
TYPE_A_CLASSER = "A_CLASSER"

#: Les valeurs de type qui n'affirment RIEN. La casse et les blancs sont
#: normalises avant comparaison: `a_classer` et `A_CLASSER ` disent la meme
#: chose, et un module qui l'oubliait comptait autrement que ses voisins.
TYPES_SANS_AFFIRMATION = frozenset({"", TYPE_A_CLASSER})


def normaliser_type(document_type: object) -> str:
    """Le type sous sa forme comparable: sans blancs, en capitales."""
    return str(document_type or "").strip().upper()


def type_est_etabli(document_type: object) -> bool:
    """Ce document porte-t-il un type que quelqu'un a decide ?

    **Le complement, comme pour le statut**: tout ce qui n'affirme pas un type
    doit remonter. Un type vide et un `A_CLASSER` disent la meme chose - *on ne
    sait pas* - et les compter differemment ferait diverger deux ecrans qui
    parlent du meme document.
    """
    return normaliser_type(document_type) not in {
        normaliser_type(valeur) for valeur in TYPES_SANS_AFFIRMATION
    }


def type_doit_remonter_a_l_humain(document_type: object) -> bool:
    """Complement de `type_est_etabli`, ecrit pour se lire a l'appel."""
    return not type_est_etabli(document_type)
