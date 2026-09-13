"""La matrice de gouvernance: une ligne par acte, une colonne par source.

Extrait de `_actes_vues` le 2026-09-08. Ce module-la etait a 585 lignes pour
une limite dure de 600, et la separation des deux normes de seuil (`RM-2026-0144`)
y ajoutait deux cellules de plus. La regle du depot est d'extraire avant
d'ajouter; la coupure suit la barre de section qui etait deja la.

**Pourquoi cette coupure et pas une autre.** Les vues qui restent dans
`_actes_vues` decrivent le MODELE - ce qu'est un acte, ce qu'est un lien vivant,
ce qu'une correction humaine remplace. La matrice, elle, decrit un ECRAN: elle
met une colonne en face de chaque controle, et son contrat est celui du filtrage
- une cellule se filtre par egalite sur une colonne, jamais par une recherche de
mots dans un texte. Les deux sujets bougent pour des raisons differentes.

**Ce que ce module ne decide pas.** Ni l'ordre qui retient un lien
(`_actes_citations`), ni les portees auxquelles un controle s'applique
(`_actes_typologie`), ni quelles normes de seuil existent
(`_actes_seuils_normes`). Il les assemble, et le fait qu'il n'ait aucune liste
en dur est ce qui empeche l'ecart de s'installer entre ces registres et les
colonnes reellement produites.
"""

from __future__ import annotations

from ._actes_citations import colonnes_citation, lien_retenu, ordre_de
from ._actes_seuils_normes import ENTREES_SEUIL
from ._actes_schema import FORCE_NON_APPLICABLE, TABLE_LIENS
from ._actes_seuils_applicabilite import portees_exclues
from ._actes_typologie import CTRL_SEUIL, portees_soumises


# --------------------------------------------------------------------------
# v_matrice - une ligne par acte, une colonne par source
# --------------------------------------------------------------------------

#: Une cellule de detail, en **une colonne de force probatoire**. C'est le coeur
#: du contrat de filtrage: une cellule se filtre par egalite sur une colonne,
#: jamais par une recherche de mots dans un texte. Elles etaient six; la
#: separation des deux normes de seuil en a fait huit le 2026-09-08, et leur
#: nombre n'est plus ecrit nulle part - il se lit au registre.
#:
#: `controle` permet a plusieurs relations de partager un meme gate de portee.
#: Les trois relations de seuil sont dans ce cas: savoir si un acte est
#: justiciable d'un seuil ne depend pas de la norme, donc `CTRL_SEUIL` decide
#: pour les trois. Sans ce parametre, chaque relation aurait du etre son propre
#: controle, donc porter ses propres motifs de retrait dans `HORS_CONTROLE`.
#:
#: Une cellule sans lien vaut `ABSENT`, ce qui est un statut a part entiere et
#: non un NULL: "une absence est une information de premier niveau".
def cellule(relation: str, *, lien_vivant: str, controle: str = "") -> str:
    # **Le gate compose DEUX granularites, et c'est le lot `RM-2026-0144`.**
    # `portees_soumises` retire un CONTROLE a une portee; les trois relations
    # de seuil partagent `CTRL_SEUIL`, donc ce retrait vaut pour les trois.
    # L'exclusion de l'article 21 alinea 2 ne vaut que pour la mise en
    # concurrence: elle se declare par RELATION et se retranche ici.
    soumises = [
        p for p in portees_soumises(controle or relation)
        if p not in portees_exclues(relation)
    ]
    portees = ", ".join("'{0}'".format(p) for p in soumises)
    if not portees:  # pragma: no cover - aucun controle n'est vide aujourd'hui
        return f"'{FORCE_NON_APPLICABLE}'"
    # La force affichee et la source citee sortent du MEME sous-select, ecrit
    # une seule fois dans `_actes_citations`. Une seconde requete, meme tres
    # proche, pourrait retenir une autre assertion: l'ecran citerait alors la
    # page d'un devis affirme a cote du mot `au dossier`.
    #
    # `ordre_de` va chercher l'ordre DECLARE pour cette relation, il n'en
    # suppose aucun: un constat sur une piece se tranche par la force
    # probatoire, une norme votee par la date de la deliberation. Une relation
    # ajoutee sans ordre declare leve ici plutot que de devenir probante en
    # silence.
    retenue = lien_retenu(
        relation, "force_probatoire",
        table=TABLE_LIENS, lien_vivant=lien_vivant,
        ordre=ordre_de(relation), defaut="ABSENT",
    )
    return f"""CASE WHEN a.portee NOT IN ({portees})
    THEN '{FORCE_NON_APPLICABLE}' ELSE {retenue} END"""


_portees_execution = ", ".join(
    "'{0}'".format(p) for p in portees_soumises('EXECUTION')
)


def cellules_seuil(lien_vivant: str) -> str:
    """Une cellule par entree du registre des normes de seuil.

    **Generees, jamais recopiees**, et c'est la garde qui empeche le defaut
    corrige le 2026-09-08 de revenir a l'affichage apres avoir ete corrige dans
    le modele. Une seule ligne ecrivait `cel_seuil` pour une relation qui
    portait deux normes; ecrire aujourd'hui deux lignes a la main rendrait la
    troisieme entree - le residu - invisible, puis la quatrieme le jour ou une
    norme s'ajouterait.

    Le nom de colonne porte le prefixe de la norme, donc **la cellule dit
    laquelle des deux elle rapporte**: `cel_seuil_consultation_cs`,
    `cel_seuil_concurrence`, et `cel_seuil` pour ce dont la norme n'a pas ete
    attribuee. Ce dernier garde son nom d'origine parce que c'est ce que les
    lignes deja ecrites disent d'elles-memes, et parce qu'un lecteur existant
    de `cel_seuil` continue de lire quelque chose de vrai.

    Le gate de portee passe par `CTRL_SEUIL`, un seul controle pour les trois:
    savoir si un acte est justiciable d'un seuil ne depend pas de la norme.
    L'alinea porte pourtant une asymetrie reelle - il exclut le contrat de
    syndic de la seule mise en concurrence - et ce lot ne la traite pas: elle
    est nommee comme residu au lieu d'etre appliquee a moitie.
    """
    return "".join(
        "    {0} AS cel_{1},\n{2}".format(
            cellule(entree.relation, lien_vivant=lien_vivant, controle=CTRL_SEUIL),
            entree.prefixe,
            montant_du_seuil(entree, lien_vivant=lien_vivant),
        )
        for entree in ENTREES_SEUIL
    )


def montant_du_seuil(entree, *, lien_vivant: str) -> str:
    """Le montant ARRETE par la deliberation retenue, a cote de celui de l'acte.

    **Sans lui, l'ecran ne pouvait pas comparer, et il le disait** - c'est le
    trou T9, laisse ouvert et ecrit dans une phrase ajoutee a chaque cellule de
    seuil: *le franchissement lui-meme n'est pas calcule*. La matrice portait le
    montant de l'ACTE (`a.montant_effectif`) et pas celui du SEUIL, donc les
    deux termes de la comparaison n'etaient jamais au meme endroit.

    Le montant est pris **sur le lien retenu**, dans le meme sous-select que la
    force et la citation. Un second sous-select, meme identique, pourrait
    retenir une autre deliberation: l'ecran comparerait alors un montant a un
    seuil arrete un autre jour.

    La chaine vide dit *pas de montant lisible sur la deliberation retenue*, et
    l'appelant doit la distinguer de zero. Un seuil a zero euro voudrait dire
    que tout y est soumis; une absence ne veut rien dire du tout.

    **Le montant lu est celui que l'assemblee a ARRETE, pas un montant
    `effectif`.** L'acte, lui, porte `montant_effectif`, qui prefere le montant
    d'un devis rattache quand il en existe un - c'est juste pour une depense,
    dont la valeur reelle est celle du devis retenu. Un SEUIL n'a pas de devis:
    il est arrete par un vote, et le montant qui fait foi est celui que la
    resolution enonce. Prendre ici un montant `effectif` ferait dependre un
    seuil d'une piece qui ne le concerne pas.
    """
    valeur = lien_retenu(
        entree.relation, "t.montant_autorise",
        table=TABLE_LIENS, lien_vivant=lien_vivant,
        ordre=ordre_de(entree.relation), defaut="",
    )
    return "    {0} AS montant_{1},\n".format(valeur, entree.prefixe)


def vue_matrice(lien_vivant: str) -> str:
    """Le SQL de `v_matrice_gouvernance`, monte sur le fragment de lien vivant.

    `lien_vivant` reste un parametre plutot qu'un import: c'est lui qui porte
    la regle *un humain a contredit cette paire*, elle appartient au modele, et
    la matrice ne doit pas pouvoir en avoir une seconde version.
    """
    return f"""
CREATE VIEW IF NOT EXISTS v_matrice_gouvernance AS
SELECT
    a.acte_id, a.nature, a.etat, a.portee, a.exercice, a.ag_id, a.numero,
    a.sous_numero, a.objet, a.date_effet, a.resultat,
    a.montant_effectif AS montant_autorise, a.montant_lu_sur,
    a.entreprise_effective, a.entreprise_lue_sur, a.doc_id,
    -- La position de l'ACTE lui-meme, distincte de celle de ses liens. Le
    -- texte de la resolution n'est pas un controle: il rapporte ce que le
    -- document dit, et sa source est le document ou l'acte a ete lu.
    a.page AS src_acte_page, a.ancre AS src_acte_ancre,
    -- Trois colonnes de source et un compteur par cellule liee, generes le
    -- 2026-09-07. Sans elles la matrice affirmait sans jamais dire d'ou:
    -- 229 liens sur 229 d'un coffre mesure portaient une page ET une ancre,
    -- et le mot `ancre` n'apparaissait dans aucun gabarit.
{colonnes_citation(table=TABLE_LIENS, lien_vivant=lien_vivant)}{cellules_seuil(lien_vivant)}    {cellule('AVIS_CS', lien_vivant=lien_vivant)}          AS cel_avis_cs,
    -- Septieme cellule, ajoutee le 2026-09-04. Elle n'est pas un doublon de
    -- `cel_avis_cs`: l'avis est la consultation prealable sur un marche
    -- (art. 21 al. 2), le rapport est le compte rendu annuel d'execution de
    -- mission (decret art. 22 al. 2, joint a l'ordre du jour par l'art. 11 II
    -- 4). C'est le rattachement que Brice demandait pour l'approbation des
    -- comptes, a la place d'un seuil qui n'a jamais eu d'objet la.
    {cellule('RAPPORT_CS', lien_vivant=lien_vivant)}       AS cel_rapport_cs,
    CASE
        -- Ajoute le 2026-09-04, quand le pont registre -> modele a verse les
        -- premiers actes PROJETEE reels: soixante-dix-huit sous-points lus dans
        -- une convocation. Une convocation ne vote pas. Ecrire `ABSENT` sur leur
        -- cellule d'issue annoncait une piece manquante la ou aucune piece
        -- n'etait due, et l'ecran affichait `issue non tracee` sur des projets
        -- dont l'assemblee ne s'etait pas encore tenue. `Ne s'applique pas` est
        -- exactement ce que le quatrieme etat de force probatoire dit.
        WHEN a.etat = 'PROJETEE' THEN '{FORCE_NON_APPLICABLE}'
        -- Le proces-verbal enonce ce qui s'est passe, y compris quand ce qui
        -- s'est passe est qu'il n'y a pas eu de vote. La source est disponible.
        WHEN a.resultat = 'ADOPTEE' THEN 'PIECE_PRODUITE'
        WHEN a.resultat = 'REJETEE' THEN 'PIECE_PRODUITE'
        WHEN a.resultat = 'PAS_DE_VOTE' THEN 'PIECE_PRODUITE'
        -- Des voix sont comptees et l'issue n'est pas enoncee: la piece existe
        -- et ne conclut pas. C'est exactement `A confirmer`, et surtout pas
        -- une adoption deduite du fait qu'on a vote.
        WHEN a.resultat = 'VOTE_SANS_FORMULE' THEN 'AFFIRME_SANS_PIECE'
        -- Ni vote, ni formule, ni mention: le proces-verbal a bien ete lu et
        -- ne trace aucune issue. C'est un fait CONSTATE SUR le document, pas
        -- un document manquant. Jusqu'au 2026-09-04 cette valeur tombait dans
        -- l'`ELSE 'ABSENT'` ci-dessous et s'affichait `Source manquante`,
        -- c'est-a-dire comme un probleme de piece - la distinction que le
        -- vocabulaire pose en tete de module (`le document ne le dit pas`
        -- n'est pas `on ne sait pas`) etait perdue au dernier metre. Le coffre
        -- reel porte 4 lignes dans ce cas.
        WHEN a.resultat = 'SANS_ISSUE_TRACEE' THEN 'AFFIRME_SANS_PIECE'
        -- Le document conclut et la chaine n'a pas su lire sa conclusion. La
        -- piece existe: `ABSENT` annoncerait un proces-verbal manquant, et
        -- reprocherait au syndic un defaut qui est le notre.
        WHEN a.resultat = 'ISSUE_NON_LUE' THEN 'AFFIRME_SANS_PIECE'
        ELSE 'ABSENT'
    END                            AS cel_resolution,
    {cellule('ANNEXE_VISEE', lien_vivant=lien_vivant)}     AS cel_annexe,
    {cellule('DEVIS_RETENU', lien_vivant=lien_vivant)}     AS cel_devis,
    CASE WHEN a.portee NOT IN ({_portees_execution})
         THEN '{FORCE_NON_APPLICABLE}'
         -- Meme motif que la cellule d'issue: une resolution seulement proposee
         -- ne peut pas avoir ete payee. `Rien de paye a ce jour` sur un projet
         -- de convocation est un reproche adresse a une assemblee qui ne s'est
         -- pas tenue. Le constat `ACTE_SANS_EXECUTION` posait deja la garde
         -- `etat = CONSTATEE`; la cellule ne la posait pas.
         WHEN a.etat = 'PROJETEE' THEN '{FORCE_NON_APPLICABLE}'
         WHEN e.depenses_rattachees > 0 THEN 'PIECE_PRODUITE' ELSE 'ABSENT' END
                                   AS cel_execution,
    e.depenses_rattachees, e.montant_paye
FROM v_acte_effectif a
JOIN v_execution e ON e.acte_id = a.acte_id AND e.etat = a.etat;
"""

#: Les deux sorties propres du modele (section 10), qui tombent de la meme
#: jointure lue dans l'autre sens. Ce sont des agregats: aucune ligne ne les
#: porte, et c'est pour cela que le contrat de filtrage les classe a part.
VUE_TAUX = """
CREATE VIEW IF NOT EXISTS v_taux_gouvernance AS
SELECT
    e.exercice,
    COUNT(*)                                                       AS actes,
    SUM(CASE WHEN e.depenses_rattachees > 0 THEN 1 ELSE 0 END)     AS actes_executes,
    SUM(CASE WHEN e.montant_autorise IS NOT NULL AND e.entreprise <> ''
             THEN 1 ELSE 0 END)                                    AS actes_quantifies
FROM v_execution e
WHERE e.etat = 'CONSTATEE'
GROUP BY e.exercice;
"""
