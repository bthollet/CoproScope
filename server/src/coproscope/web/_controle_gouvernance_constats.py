"""Les constats de la synthese: des filtres nommes, jamais des comptages.

**Un constat n'ouvre pas une page, il pose un filtre sur la seule page qui
existe.** C'est le principe pose apres avoir constate trois configurations de
page differentes selon le constat clique. Il n'y a donc qu'une vue tableau,
toujours la meme - memes colonnes, meme barre de filtres, meme comportement - et
le constat n'agit que sur les filtres. Consequence voulue: on les desactive un
par un et on revoit la globalite par degres.

**Aucun nombre n'est compte ici.** Chaque nombre est
`len(appliquer_filtres(lignes, filtre))`, c'est-a-dire la taille exacte de la
selection que le tableau ouvrira. Le lien emporte le filtre ET le nombre
annonce; le tableau compare. Avec un predicat unique la comparaison ne peut pas
echouer - et c'est precisement pourquoi elle est faite: le jour ou un second
chemin de calcul apparait, l'ecran le dit au lieu de mentir.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from ._controle_gouvernance_source import (
    EXIGENCE_AUCUN_SEUIL,
    EXIGENCE_SEUIL_RATTACHE,
    appliquer_filtres,
)

#: D'ou vient un constat, et c'est la distinction la plus importante de cet
#: ecran.
#:
#: `PIECES` : le proces-verbal, la convocation ou une facture ETABLIT le fait.
#: Le constat porte sur la copropriete, il commande une question au syndic.
#:
#: `OUTIL` : le fait n'est pas etabli, il est ABSENT DU MODELE parce qu'aucun
#: code du produit ne l'ecrit encore. Ce n'est pas un manquement de la
#: copropriete, c'est un trou de l'outil.
#:
#: Le defaut corrige le 2026-09-04: l'ecran annonçait « 157 points a instruire
#: sur 173 decisions lues » alors que le modele contenait SIX constats. Les 154
#: autres etaient des cellules `ABSENT` produites par une table de liens que
#: rien n'alimente - et la pastille qui portait le plus gros chiffre affirmait
#: en plus un fondement de droit, « la consultation prealable est exigible sur
#: ce type », sur des actes dont le type n'avait justement pas ete reconnu. Un
#: conseil syndical qui ecrit au syndic sur cette base reclame 154 avis pour des
#: resolutions dont beaucoup n'en exigent aucun.
#:
#: La pastille voisine `acte_sans_execution` disait deja correctement « le lien
#: entre un acte et un euro n'existe pas encore »: l'honnetete etait presente
#: sur une pastille et absente sur celle qui comptait le plus. Elle est
#: maintenant declaree, pas laissee a la redaction.
SOURCE_PIECES = "pieces"
SOURCE_OUTIL = "outil"

#: Chaque constat porte son INTENTION: ce que le lecteur est cense faire une
#: fois arrive. Un constat sans intention est une alerte qui ne demande rien.
CONSTATS: tuple[dict[str, Any], ...] = (
    {"cle": "acte_sans_fondement", "ton": "danger", "source": SOURCE_PIECES,
     "titre": "décisions du conseil syndical qu'aucune délégation ne fonde",
     "aide": "Une décision déléguée suppose une délégation en vigueur à sa date. Aucune n'est rattachée.",
     "intention": "Demander au syndic la délégation invoquée, et sa date de vote.",
     "filtre": {"constat": "ACTE_SANS_FONDEMENT"}},
    {"cle": "urgence_jamais_portee", "ton": "danger", "source": SOURCE_PIECES,
     "titre": "dépenses d'urgence qu'aucune assemblée n'a jamais ratifiées",
     "aide": "L'avis du conseil et la mise en concurrence n'y sont pas exigés. L'assemblée de ratification, si.",
     "intention": "Chercher la ratification dans l'assemblée qui a suivi les travaux.",
     "filtre": {"constat": "URGENCE_JAMAIS_PORTEE"}},
    {"cle": "issue_non_enoncee", "ton": "danger", "source": SOURCE_PIECES,
     # Tour 2 de l'expert, 2026-09-13: « conclusion » est reserve au verdict humain,
     # et demander le PV « tel qu'il aurait du etre ecrit » inviterait a faire
     # reecrire une piece signee. Aucune cle du registre ne fonde son contenu.
     "titre": "résolutions dont les voix sont comptées et l'issue non énoncée",
     "aide": "Les lignes de vote sont au procès-verbal, la phrase qui énonce l'issue n'y est pas.",
     "intention": "Demander au syndic la copie du procès-verbal signé, et l'issue qu'il retient "
                  "pour exécuter cette résolution.",
     "filtre": {"constat": "ISSUE_NON_ENONCEE"}},
    {"cle": "plafond_depasse", "ton": "danger", "source": SOURCE_PIECES,
     "titre": "délégations dont le plafond voté est franchi en cumul",
     "aide": "Ce contrôle se fait en cumul sur la période : aucune décision prise isolément ne le montre.",
     "intention": "Porter le dépassement à l'ordre du jour de la prochaine assemblée.",
     "filtre": {"constat": "PLAFOND_DEPASSE"}},
    {"cle": "delegation_expiree", "ton": "danger", "source": SOURCE_PIECES,
     "titre": "décisions prises après l'expiration de la délégation",
     "aide": "Une délégation vaut deux ans au plus, article 21-3.",
     "intention": "Vérifier ce qui a été engagé après la date d'expiration.",
     "filtre": {"constat": "DELEGATION_EXPIREE"}},
    {"cle": "obligation_non_tenue", "ton": "danger", "source": SOURCE_PIECES,
     "titre": "obligations nées après la décision et non tenues",
     "aide": "Compte rendu devant l'assemblée qui approuve les comptes, ratification d'une urgence : leur échéance est datée.",
     "intention": "Demander la pièce à l'échéance nommée, ou constater le manquement.",
     "filtre": {"constat": "OBLIGATION_NON_TENUE"}},
    {"cle": "montant_divergent", "ton": "danger", "source": SOURCE_PIECES,
     "titre": "décisions payées autrement qu'elles n'ont été votées",
     "aide": "Le montant payé et le montant voté ne coïncident pas.",
     "intention": "Demander le détail des factures, et ce qui explique l'écart.",
     "filtre": {"constat": "MONTANT_DIVERGENT"}},
    {"cle": "majorite_non_enoncee", "ton": "warn", "source": SOURCE_PIECES,
     "titre": "résolutions dont aucune majorité n'est énoncée",
     "aide": "Le procès-verbal ne dit pas quelle majorité a été appliquée : l'outil ne peut pas "
             "comparer les voix à la règle.",
     "intention": "Demander au syndic sous quelle majorité cette résolution a été traitée.",
     "filtre": {"constat": "MAJORITE_NON_ENONCEE"}},
    {"cle": "acte_sans_execution", "ton": "warn", "source": SOURCE_OUTIL,
     "titre": "décisions votées auxquelles aucune dépense n'est rattachée",
     "aide": "Ce n'est pas une preuve que rien n'a été payé : le lien entre un acte et un euro "
             "n'existe pas encore dans l'outil.",
     "intention": "Vérifier dans les comptes ce qui a été engagé sur ces objets.",
     "filtre": {"constat": "ACTE_SANS_EXECUTION"}},
    {"cle": "avis_manquant", "ton": "warn", "source": SOURCE_OUTIL,
     "titre": "décisions dont aucun avis du conseil syndical n'est rattaché dans l'outil",
     # Ce que cette pastille N'AFFIRME PLUS. Elle disait « la consultation
     # préalable est exigible sur ce type. Aucune pièce ne l'établit. » Les deux
     # phrases étaient fausses : le type n'est pas reconnu sur la plupart de ces
     # lignes, donc l'exigibilité n'est pas établie ; et aucune pièce ne peut
     # l'établir, puisque aucun code du produit n'écrit ce lien pour une
     # résolution d'assemblée. Seule une convocation qui affirme la consultation
     # en pose un.
     "aide": "Aucun code n'écrit encore ce lien pour une résolution d'assemblée : la cellule est "
             "vide parce que l'outil ne la remplit pas, pas parce qu'un avis manquerait. Et sur un "
             "type non reconnu, l'exigibilité elle-même n'est pas établie.",
     "intention": "Demander les comptes rendus de conseil syndical de la période, sans en déduire "
                  "un manquement.",
     "filtre": {"avis": "manquante", "exigence_avis": EXIGENCE_SEUIL_RATTACHE}},
    # **Le partage que `RM-2026-0164` reclamait, et il repose enfin sur une
    # donnee.** Mesure du 2026-09-10 sur une instance reabsorbee a vide: les 293
    # lignes sans avis se partagent en **219 dont un seuil de consultation est
    # rattache** et **74 qui n'en portent aucun**. Les melanger faisait lire 74
    # absences qu'aucun texte n'exige comme des pieces a reclamer - le defaut
    # que l'item nomme, et qui avait deja ete corrige EN PAROLES le 2026-09-04
    # sans que le NOMBRE change.
    #
    # Le ton n'est pas `warn`: il n'y a rien a surveiller. Une piece que rien
    # n'exige n'est pas une piece qui manque.
    {"cle": "avis_sans_exigence", "ton": "info", "source": SOURCE_OUTIL,
     # Tour 2 de l'expert: « non exige » et « pas un manquement » etaient des
     # verdicts de droit, ranges parmi ce que l'outil ne sait pas. Un seuil peut
     # avoir ete LU sans que son adoption soit etablie: l'outil ne conclut pas.
     "titre": "décisions sans avis du conseil syndical, pour lesquelles l'outil n'a établi aucun seuil applicable",
     "aide": "L'outil n'a établi aucun seuil de consultation applicable à la date de ces décisions. "
             "Il ne conclut ni à un manquement ni à une conformité.",
     "intention": "Ne rien réclamer à ce stade. Les compter parmi les pièces à demander "
                  "noierait celles qui comptent.",
     "filtre": {"avis": "manquante", "exigence_avis": EXIGENCE_AUCUN_SEUIL}},
    {"cle": "type_non_reconnu", "ton": "warn", "source": SOURCE_OUTIL,
     "titre": "décisions dont l'outil n'a pas reconnu le type",
     # Le pendant honnête de la pastille précédente. Les 154 lignes qui gonflaient
     # « avis manquant » sont d'abord des lignes non typées : les nommer par ce
     # qu'elles sont vaut mieux que de les compter sous un fondement de droit
     # qu'on ne peut pas leur opposer.
     "aide": "Les sept contrôles leur restent appliqués : sur ces lignes, certains peuvent ne pas "
             "avoir d'objet. Relisez la résolution.",
     "intention": "Relire le corps de ces résolutions : c'est le typage qui manque, pas une pièce.",
     "filtre": {"type": "ORDINAIRE"}},
    {"cle": "issue_non_lue_a_relire", "ton": "warn", "source": SOURCE_OUTIL,
     "titre": "résolutions dont le procès-verbal conclut, sans que le logiciel ait lu sa conclusion",
     # La pastille voisine `issue_non_enoncee` est en `SOURCE_PIECES` et son
     # intention est d'écrire au syndic. Celle-ci ne doit surtout pas le faire :
     # la phrase de conclusion est au procès-verbal, et la réclamer reviendrait
     # à demander au syndic une pièce qu'il a déjà fournie. Les deux titres se
     # ressemblent, les deux gestes sont opposés.
     "aide": "Le procès-verbal énonce bien une issue : c'est notre lecture qui a échoué, "
             "pas le document qui se tait. Rien ici ne se reproche à la copropriété.",
     "intention": "Relire ces résolutions au procès-verbal et y inscrire l'issue : "
                  "tant qu'elle n'est pas lue, ces lignes n'autorisent rien.",
     "filtre": {"constat": "ISSUE_NON_LUE_A_RELIRE"}},
    {"cle": "rejetee", "ton": "warn", "source": SOURCE_PIECES,
     # Tour 2 de l'expert: « aucun euro ne devait etre engage » etait une regle sans
     # source, et trop large - une depense peut avoir un autre fondement.
     "titre": "résolutions rejetées : l'assemblée n'a pas autorisé ces objets",
     "aide": "Le refus est un acte, énoncé par le document. Ce n'est pas une irrégularité, et une "
             "dépense peut avoir un autre fondement.",
     "intention": "Rapprocher ces objets des dépenses, sans en déduire un manquement.",
     "filtre": {"issue": "REJETEE"}},
    {"cle": "pas_de_vote", "ton": "warn", "source": SOURCE_PIECES,
     "titre": "résolutions que l'assemblée n'a pas votées",
     "aide": "Rien n'autorise et rien n'interdit : l'acte n'existe pas.",
     "intention": "Vérifier ce qui a suivi, notamment les appels de fonds.",
     "filtre": {"issue": "PAS_DE_VOTE"}},
    {"cle": "adoptee", "ton": "ok", "source": SOURCE_PIECES,
     "titre": "décisions adoptées que rien ne contredit dans les pièces lues",
     "aide": "Les pièces établissent l'adoption, pas l'absence de défaut.",
     "intention": "Rien à signaler par l'outil. Elles sont là pour que le reste ait une échelle.",
     "filtre": {"issue": "ADOPTEE", "fonde": "disponible"}},
)

CONSTAT_PAR_CLE = {constat["cle"]: constat for constat in CONSTATS}


def url_vue(
    base: str, vue: str, filtres: dict[str, str], *, constat: str = "", attendu: int | None = None,
    ligne: str = "", token: str = "",
) -> str:
    """L'etat vit dans l'adresse, comme `?tab=` ailleurs dans le produit.

    Un filtre pose survit a un aller en synthese et a un retour: il n'a jamais
    quitte l'URL.
    """
    params: list[tuple[str, str]] = [("vue", vue)]
    for cle in sorted(filtres or {}):
        valeur = filtres[cle]
        if valeur and valeur != "toutes":
            params.append(("f_" + cle, valeur))
    if constat:
        params.append(("constat", constat))
    if attendu is not None:
        params.append(("n", str(attendu)))
    if ligne:
        params.append(("ligne", ligne))
    if token:
        params.append(("token", token))
    return base + "?" + urlencode(params)


def url_sans_filtre(
    base: str, filtres: dict[str, str], cle: str, *, constat: str = "", token: str = "",
    vue: str = "tableau",
) -> str:
    """Retirer UN filtre en gardant les autres, pour revoir la globalite par
    degres. C'est la demande explicite: desactiver un filtre a la fois."""
    reste = {k: v for k, v in (filtres or {}).items() if k != cle}
    return url_vue(base, vue, reste, constat=constat if reste else "", token=token)


def mesurer(lignes: list[dict[str, Any]], constat: dict[str, Any]) -> dict[str, Any]:
    """Le nombre du constat EST la longueur du resultat filtre."""
    selection = appliquer_filtres(lignes, constat["filtre"])
    conclus = sum(1 for l in selection if l["conclusion"] != "a_instruire")
    return {"constat": constat, "n": len(selection), "conclus": conclus}


def arithmetique(lignes: list[dict[str, Any]]) -> dict[str, int]:
    """Pourquoi la somme des constats depasse le nombre de lignes.

    Les constats **se recoupent**: une meme ligne peut etre au-dessus du seuil
    et sans conclusion de vote. La somme est donc toujours superieure, et la
    cacher fait croire a une incoherence. On affiche les deux nombres et leur
    ecart. Le nombre de points a instruire est le nombre de lignes distinctes.

    Seuls les constats `SOURCE_PIECES` entrent dans cette arithmetique: c'est
    celle du courrier au syndic, et un trou de l'outil ne se reclame a personne.
    """
    marques: dict[str, int] = {}
    total = 0
    for constat in CONSTATS:
        if constat["ton"] == "ok" or constat["source"] != SOURCE_PIECES:
            continue
        selection = appliquer_filtres(lignes, constat["filtre"])
        total += len(selection)
        for ligne in selection:
            marques[ligne["id"]] = marques.get(ligne["id"], 0) + 1
    return {
        "marques": total,
        "lignes": len(marques),
        "doubles": sum(1 for n in marques.values() if n > 1),
    }


def lignes_marquees(
    lignes: list[dict[str, Any]], *, source: str | None = None
) -> set[str]:
    """Les lignes qu'au moins un constat non neutre marque.

    **Une seule definition du point a instruire**, et elle est derivee des
    constats eux-memes. Une version anterieure en avait deux - un drapeau pose a
    la main sur chaque ligne, et le comptage des constats - qui donnaient 23 et
    59 sur le meme corpus.

    `source` restreint aux constats d'une provenance. Sans elle, l'ecran
    comptait ensemble ce que les pieces etablissent et ce que l'outil n'a pas
    encore ecrit, et annonçait « 157 points a instruire » sur un modele qui en
    portait six. Le point a instruire, celui qui commande le courrier au syndic,
    est desormais `SOURCE_PIECES`; le reste est nomme a part.
    """
    marquees: set[str] = set()
    for constat in CONSTATS:
        if constat["ton"] == "ok":
            continue
        if source is not None and constat["source"] != source:
            continue
        for ligne in appliquer_filtres(lignes, constat["filtre"]):
            marquees.add(ligne["id"])
    return marquees
