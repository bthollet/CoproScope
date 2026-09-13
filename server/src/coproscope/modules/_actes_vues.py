"""Les vues du modele: ce qui est calcule, et qui ne doit donc jamais etre ecrit.

**Pourquoi des vues et pas des tables.** Un constat n'est pas une donnee, c'est
la lecture d'une absence. `OBLIGATION_NON_TENUE` derive du fait qu'aucune ligne
n'existe: aucune re-extraction ne peut le remplacer, parce que
`remplacer_pour_documents` supprime par `doc_id` et qu'une absence n'a pas de
document. Une table de constats serait donc soit jamais nettoyee, soit nettoyee
par une regle inventee - et dans les deux cas elle divergerait de ses sources.
C'est le cinquieme comptage concurrent que ce lot existe pour eviter.

Une vue, elle, ne peut pas diverger. Elle ne survit pas non plus a une
re-extraction: il n'y a rien a faire survivre.

**Consequence a tenir.** Une vue ne prend pas de parametre. Les vues ci-dessous
n'appellent donc jamais `date('now')`: elles rendent `date_fait` et
`date_echeance`, et le nombre de jours ecoules est calcule a la lecture, par
l'appelant, avec la date qu'il choisit. Deux benefices: les tests sont
deterministes, et la vue enonce un fait plutot qu'un age.
"""

from __future__ import annotations

from ._actes_citations import ORDRE_PROBANT as _ORDRE_PROBANT
from ._actes_constats import vue_constats
from ._actes_vues_matrice import VUE_TAUX, vue_matrice
from ._actes_schema import (
    ACTE_FIELDS,
    EXIGENCES_LIEN,
    PORTEE_APPROBATION_COMPTES,
    PORTEE_DELEGATION_CS,
    PROV_CONTREDIT,
    TABLE_ACTES,
    TABLE_DOSSIERS,
    TABLE_LIENS,
    sql_reel,
    sql_taux,
)

# --------------------------------------------------------------------------
# Fragments reutilises
# --------------------------------------------------------------------------

#: Un lien satisfait une exigence sauf si un humain a contredit **cette paire**.
#: Contredire une paire ne doit pas fermer l'exigence par un autre lien, et ne
#: doit pas non plus annuler un lien different vers une autre cible.
_LIEN_VIVANT = f"""
    l.provenance <> '{PROV_CONTREDIT}'
    AND NOT EXISTS (
        SELECT 1 FROM {TABLE_LIENS} c
        WHERE c.source_kind = l.source_kind AND c.source_id = l.source_id
          AND c.relation = l.relation
          AND c.target_kind = l.target_kind AND c.target_id = l.target_id
          AND c.provenance = '{PROV_CONTREDIT}'
    )
"""


#: Le jumeau de `_LIEN_VIVANT` pour le premier saut de la delegation. Meme
#: regle, autre alias: un fondement contredit par un humain ne porte plus la
#: chaine delegation -> decision -> depense.
_FONDEMENT_VIVANT = f"""
    f.provenance <> '{PROV_CONTREDIT}'
    AND NOT EXISTS (
        SELECT 1 FROM {TABLE_LIENS} c
        WHERE c.source_kind = f.source_kind AND c.source_id = f.source_id
          AND c.relation = f.relation
          AND c.target_kind = f.target_kind AND c.target_id = f.target_id
          AND c.provenance = '{PROV_CONTREDIT}'
    )
"""


def _valeurs_exigences() -> str:
    """La table des exigences, injectee en CTE plutot que persistee.

    Elle est du droit, pas de la donnee d'instance: elle doit etre versionnee
    avec le code et non pouvoir deriver dans une base locale. Une table
    persistee aurait exige une migration a chaque evolution de l'article 21.
    """
    lignes = ", ".join(
        "('{0}','{1}','{2}','{3}')".format(*ligne) for ligne in EXIGENCES_LIEN
    )
    return f"exigences(nature, relation, sens, regle) AS (VALUES {lignes})"


# --------------------------------------------------------------------------
# v_actes / v_dossiers - quelle ligne est lue quand deux coexistent
# --------------------------------------------------------------------------

#: La decision back n. 2 fait coexister `EXTRAIT` et `CORRIGE_HUMAIN`. Elle ne
#: dit pas laquelle est lue - et sans reponse unique, chaque vue et chaque ecran
#: trancherait a sa facon. Ici, une fois: **la correction humaine gagne a la
#: lecture**. Tout le reste du modele lit `v_actes`, jamais la table.
_V_ACTES = f"""
CREATE VIEW IF NOT EXISTS v_actes AS
SELECT a.* FROM {TABLE_ACTES} a
WHERE a.origine = 'CORRIGE_HUMAIN'
   OR NOT EXISTS (
        SELECT 1 FROM {TABLE_ACTES} h
        WHERE h.acte_id = a.acte_id AND h.etat = a.etat
          AND h.origine = 'CORRIGE_HUMAIN'
   );
"""

_V_DOSSIERS = f"""
CREATE VIEW IF NOT EXISTS v_dossiers AS
SELECT d.* FROM {TABLE_DOSSIERS} d
WHERE d.origine = 'CORRIGE_HUMAIN'
   OR NOT EXISTS (
        SELECT 1 FROM {TABLE_DOSSIERS} h
        WHERE h.dossier_id = d.dossier_id AND h.origine = 'CORRIGE_HUMAIN'
   );
"""

#: **Ce que la comptabilite a retenu, et ce que la piece annonce - cote a cote.**
#:
#: Trois ecarts reels ont ete constates dans les pieces de l'exercice 2025, et
#: ils ne sont pas fabriques: une T.V.A. extraite a 20 % d'une facture qui porte
#: 10 % (ecart de 126,19), une T.V.A. de 200,00 sur une facture portant
#: `T.V.A. non applicable`, et 3 693,90 extraits d'une prime d'assurance qui n'en
#: supporte pas.
#:
#: La vue ne corrige rien. Elle **calcule ce qui serait attendu au vu de la
#: piece** et le pose a cote de ce que la ligne comptable a retenu. Corriger la
#: valeur ferait disparaitre la question a poser au syndic - qui est le livrable,
#: pas un effet de bord.
#:
#: Lecture des colonnes, etablie par recoupement: le montant a repartir est un
#: montant **toutes taxes comprises**, et la T.V.A. y est **incluse** au taux
#: indique. D'ou `ttc * taux / (100 + taux)`, et non `ttc * taux / 100`: un outil
#: qui traiterait le montant a repartir comme un hors taxes surevaluerait chaque
#: ligne.
_V_DOSSIERS_TVA = f"""
CREATE VIEW IF NOT EXISTS v_dossiers_tva AS
SELECT
    d.*,
    CASE
        WHEN d.tva_regime IN ('NON_APPLICABLE', 'EXONERE') THEN 0.0
        WHEN d.taux_tva_annonce <> '' AND d.montant_ttc <> '' THEN
            ROUND({sql_reel('d.montant_ttc')} * {sql_taux('d.taux_tva_annonce')}
                  / (100.0 + {sql_taux('d.taux_tva_annonce')}), 2)
        ELSE NULL
    END                                                   AS tva_attendue,
    {sql_reel('d.tva_annoncee')}              AS tva_comptable
FROM v_dossiers d;
"""

#: **La vue qui refuse de supposer de quel cote du lien un fait se trouve.**
#:
#: Chez le syndic A, le montant et l'entreprise sont dans le corps de la
#: resolution. Chez le syndic B, la convocation n'a pas de corps de resolution:
#: l'ordre du jour porte le titre et la majorite, et le devis arrive en fichier
#: voisin nomme `Piece jointe N.10 pour la resolution 19.2`. Un predicat qui
#: lirait `actes_autorisation.entreprise` serait juste chez A et vide chez B.
#:
#: Aucun predicat de ce module ne lit donc ces colonnes directement. Ils lisent
#: `montant_effectif` / `entreprise_effective`, qui prennent la colonne de l'acte
#: quand elle est renseignee, et sinon ce que le lien vers le devis retenu
#: rapporte. `montant_lu_sur` et `entreprise_lue_sur` disent lequel des deux a
#: servi: l'hesitation est nommee, pas tranchee en silence.
_V_ACTE_EFFECTIF = f"""
CREATE VIEW IF NOT EXISTS v_acte_effectif AS
SELECT
    a.*,
    COALESCE(NULLIF(a.montant_autorise, ''), (
        SELECT l.montant_impute FROM {TABLE_LIENS} l
        WHERE l.source_kind = 'acte' AND l.source_id = a.acte_id
          AND l.relation = 'DEVIS_RETENU' AND l.montant_impute <> ''
          AND ({_LIEN_VIVANT})
        {_ORDRE_PROBANT.tri}
        LIMIT 1), '')                              AS montant_effectif,
    CASE
        WHEN a.montant_autorise <> ''
            THEN CASE WHEN a.montant_source <> '' THEN a.montant_source
                      ELSE 'CORPS_RESOLUTION' END
        WHEN EXISTS (SELECT 1 FROM {TABLE_LIENS} l
                     WHERE l.source_kind = 'acte' AND l.source_id = a.acte_id
                       AND l.relation = 'DEVIS_RETENU' AND l.montant_impute <> ''
                       AND ({_LIEN_VIVANT}))
            THEN 'DEVIS_LIE'
        ELSE 'ABSENT'
    END                                            AS montant_lu_sur,
    COALESCE(NULLIF(a.entreprise, ''), (
        SELECT l.libelle_cible FROM {TABLE_LIENS} l
        WHERE l.source_kind = 'acte' AND l.source_id = a.acte_id
          AND l.relation = 'DEVIS_RETENU' AND l.libelle_cible <> ''
          AND ({_LIEN_VIVANT})
        {_ORDRE_PROBANT.tri}
        LIMIT 1), '')                              AS entreprise_effective,
    CASE
        WHEN a.entreprise <> ''
            THEN CASE WHEN a.entreprise_source <> '' THEN a.entreprise_source
                      ELSE 'CORPS_RESOLUTION' END
        WHEN EXISTS (SELECT 1 FROM {TABLE_LIENS} l
                     WHERE l.source_kind = 'acte' AND l.source_id = a.acte_id
                       AND l.relation = 'DEVIS_RETENU' AND l.libelle_cible <> ''
                       AND ({_LIEN_VIVANT}))
            THEN 'DEVIS_LIE'
        ELSE 'ABSENT'
    END                                            AS entreprise_lue_sur
FROM v_actes a;
"""

#: **Les champs sur lesquels un ecart machine / humain est une information.**
#:
#: Tous les champs de l'acte sauf ceux qui portent son identite, sa provenance
#: ou sa mise en forme. Un ecart sur `acte_id`, `etat` ou `origine` n'existe
#: pas: ils sont dans la cle, donc deux valeurs differentes sont deux lignes
#: differentes et non une divergence.
#:
#: La liste etait de cinq champs jusqu'au 2026-09-04, sur vingt-six. La
#: promesse - `l'ecart entre ce que la machine a lu et ce qu'un humain a
#: corrige est lui-meme une information` - ne valait donc que pour un
#: cinquieme du modele: une correction humaine sur la majorite annoncee ou sur
#: l'entreprise gagnait bien a la lecture, et n'apparaissait dans aucune
#: divergence. Le produit perdait la trace de la ou la machine se trompe
#: systematiquement, c'est-a-dire exactement la valeur qu'il revendique.
CHAMPS_DIVERGEABLES: tuple[str, ...] = tuple(
    champ for champ in ACTE_FIELDS
    if champ not in (
        # Identite et cle: une difference y fait deux actes, pas un ecart.
        "acte_id", "etat", "origine",
        # Provenance et ancrage de la lecture, pas contenu de l'acte.
        "doc_id", "resolution_id", "page", "ancre", "confiance",
    )
)


def _divergence(champ: str) -> str:
    """Un membre du UNION ALL, pour un champ.

    Genere plutot que recopie: la liste des champs comparables se lit dans
    `ACTE_FIELDS`, donc une colonne ajoutee au noyau entre dans la vue sans
    edition, et l'ecart entre les deux ne peut pas s'installer - c'est le meme
    motif que `ensure_schema`, qui suit la liste de champs de l'appelant au
    lieu de la dupliquer.
    """
    return f"""
    SELECT '{champ}' AS nom, x.{champ} AS valeur_machine,
           y.{champ} AS valeur_humaine, x.acte_id AS aid, x.etat AS aetat
      FROM {TABLE_ACTES} x JOIN {TABLE_ACTES} y
        ON y.acte_id = x.acte_id AND y.etat = x.etat
       AND x.origine='EXTRAIT' AND y.origine='CORRIGE_HUMAIN'"""


#: La correction gagne, mais l'ecart ne disparait pas. "Une re-extraction ecrit
#: A COTE et signale la divergence" - la divergence est ici, nommee champ par
#: champ, et elle est l'une des informations les plus utiles du produit: elle
#: dit ou la machine se trompe systematiquement.
_V_DIVERGENCES = f"""
CREATE VIEW IF NOT EXISTS v_divergences_humaines AS
SELECT
    h.acte_id                AS sujet_id,
    'acte'                   AS sujet_kind,
    h.etat                   AS etat,
    champ.nom                AS champ,
    champ.valeur_machine     AS valeur_machine,
    champ.valeur_humaine     AS valeur_humaine
FROM {TABLE_ACTES} h
JOIN {TABLE_ACTES} m
  ON m.acte_id = h.acte_id AND m.etat = h.etat AND m.origine = 'EXTRAIT'
JOIN ({" UNION ALL".join(_divergence(c) for c in CHAMPS_DIVERGEABLES)}
) champ ON champ.aid = h.acte_id AND champ.aetat = h.etat
WHERE h.origine = 'CORRIGE_HUMAIN'
  AND champ.valeur_machine <> champ.valeur_humaine
GROUP BY h.acte_id, h.etat, champ.nom;
"""

# --------------------------------------------------------------------------
# v_liens_manquants - le lien obligatoire absent, et son echeance
# --------------------------------------------------------------------------

#: Une jointure entre les actes et les exigences de leur nature, moins les liens
#: qui existent. Pas de branche Python par nature: ajouter une nature derivee se
#: fait en ajoutant une ligne a `EXIGENCES_LIEN`.
#:
#: `echeance` est calculee ici et c'est ce qui transforme une piece manquante en
#: **manquement date sans qu'un humain la saisisse**:
#:
#: - `AG_APPROBATION_COMPTES` (art. 21-5): la premiere assemblee d'approbation
#:   des comptes posterieure a la decision. Si aucune n'est encore lue,
#:   l'echeance est vide - l'obligation n'est pas exigible, et le dire est plus
#:   honnete que de la compter comme tenue ou comme manquee.
#: - `AG_SUIVANTE` (decret art. 37): la premiere assemblee posterieure a la
#:   depense d'urgence. Vide signifie qu'aucune assemblee n'a suivi, ce qui est
#:   le seul plancher dur du modele: une urgence qui n'atteint aucune assemblee
#:   est un manquement quel que soit le montant.
#:
#: **Deux gardes ajoutees le 2026-09-04, toutes deux contre un manquement
#: fabrique.**
#:
#: `a.date_effet <> ''` dans les deux sous-requetes. Sans elle, une date d'acte
#: vide rendait toute date superieure, donc `MIN()` rendait la premiere
#: assemblee CONNUE au lieu de la premiere assemblee POSTERIEURE. Mesure: une
#: assemblee d'approbation des comptes de 2019 et une de 2025, plus une
#: decision de conseil syndical sans date lue -> echeance 2019-06-01 et le
#: constat `aucun compte rendu devant l'assemblee du 2019-06-01`, c'est-a-dire
#: un manquement date d'avant l'acte lui-meme. La valeur etait plausible - une
#: vraie date d'assemblee - et rien ne signalait que la date de l'acte
#: manquait. Le cas est nominal, pas limite: 110 resolutions sur 173 du coffre
#: reel sont rattachees a une assemblee sans date lue.
#:
#: `a.etat <> 'PROJETEE'`. Une resolution seulement proposee dans une
#: convocation ne peut pas avoir manque a une obligation qu'elle n'a pas encore
#: creee. Mesure: une decision CS `PROJETEE` du 2026-05-01 plus une assemblee
#: du 2026-06-01 produisaient `ACTE_SANS_FONDEMENT` et `OBLIGATION_NON_TENUE`.
#: `v_taux_gouvernance` filtrait deja `CONSTATEE`, et les deux cellules de la
#: matrice avaient recu la meme garde: c'etait la derniere porte ouverte.
_V_LIENS_MANQUANTS = f"""
CREATE VIEW IF NOT EXISTS v_liens_manquants AS
WITH {_valeurs_exigences()}
SELECT
    a.acte_id, a.nature, a.etat, a.portee, a.exercice, a.objet,
    a.date_effet, a.montant_effectif AS montant_autorise, a.doc_id,
    e.relation, e.sens, e.regle,
    CASE
        WHEN a.date_effet = '' THEN ''
        WHEN e.regle = 'AG_APPROBATION_COMPTES' THEN COALESCE((
            SELECT MIN(x.date_effet) FROM v_actes x
            WHERE x.portee = '{PORTEE_APPROBATION_COMPTES}'
              AND x.etat = 'CONSTATEE' AND x.date_effet <> ''
              AND x.date_effet > a.date_effet), '')
        WHEN e.regle = 'AG_SUIVANTE' THEN COALESCE((
            SELECT MIN(x.date_effet) FROM v_actes x
            WHERE x.nature = 'RESOLUTION_AG'
              AND x.etat = 'CONSTATEE' AND x.date_effet <> ''
              AND x.date_effet > a.date_effet), '')
        ELSE ''
    END AS echeance
FROM v_acte_effectif a
JOIN exigences e ON e.nature = a.nature
WHERE a.etat <> 'PROJETEE'
  AND NOT EXISTS (
    SELECT 1 FROM {TABLE_LIENS} l
    WHERE l.source_kind = 'acte' AND l.source_id = a.acte_id
      AND l.relation = e.relation
      AND ({_LIEN_VIVANT})
);
"""

# --------------------------------------------------------------------------
# v_cumul_delegation - le seul controle qui ne se voit pas ligne a ligne
# --------------------------------------------------------------------------

#: Article 21-2: l'assemblee fixe le montant maximum des sommes allouees au
#: conseil syndical. Le controle se fait **en cumul sur la periode**, jamais
#: depense par depense.
#:
#: La periode est celle de la delegation (`valide_du`, `valide_au`), et le
#: critere de rattachement est **la date de la depense**, pas son exercice
#: comptable. C'est la decision back n. 1 rendue operante: une delegation votee
#: en 2023 couvre une depense de 2024, et rien dans cette requete ne connait la
#: notion d'exercice.
#:
#: Le chemin est: delegation <- (FONDE_PAR) - decision de CS - (AUTORISE) ->
#: dossier de depense. Deux jointures, parce que le plafond porte sur ce que le
#: conseil a engage **au titre de** cette delegation, pas sur ce que la
#: delegation nomme.
_V_CUMUL = f"""
CREATE VIEW IF NOT EXISTS v_cumul_delegation AS
SELECT
    d.acte_id                                        AS delegation_id,
    d.objet                                          AS delegation_objet,
    d.date_effet                                     AS delegation_votee_le,
    d.valide_du, d.valide_au, d.exercice             AS exercice_vote,
    {sql_reel('d.montant_autorise')}      AS plafond,
    COUNT(DISTINCT dep.dossier_id)                   AS depenses_cumulees,
    COALESCE(SUM({sql_reel('dep.montant_ttc')}), 0.0) AS cumul,
    -- **La periode est-elle connue.** Ajoute le 2026-09-04. Les deux bornes
    -- vides ne bornent rien: le cumul devient celui de tous les temps, et le
    -- motif du constat disait quand meme `sur la periode`. Mesure: une
    -- delegation de 2023 plafonnee a 5 000, trois depenses de 2 000 datees
    -- 2023, 2024 et 2026 -> cumul 6 000 et PLAFOND_DEPASSE; la periode lue, le
    -- meme jeu rend 4 000 et aucun constat. Ce n'est pas le cas limite: dans le
    -- coffre reel, `valide_au` est renseigne sur 2 lignes sur 173. La colonne
    -- ne corrige pas le cumul - un cumul suppose serait pire - elle permet aux
    -- constats de dire lequel des deux faits ils enoncent.
    CASE WHEN d.valide_du <> '' AND d.valide_au <> '' THEN 1 ELSE 0 END
                                                     AS periode_lue
FROM v_actes d
LEFT JOIN (
    SELECT DISTINCT f.target_id AS delegation_id, l.target_id AS dossier_id
    FROM {TABLE_LIENS} f
    JOIN {TABLE_LIENS} l
      ON l.relation = 'AUTORISE'
     AND l.source_kind = 'acte' AND l.source_id = f.source_id
    WHERE f.relation = 'FONDE_PAR' AND f.target_kind = 'acte'
      AND ({_FONDEMENT_VIVANT})
      AND ({_LIEN_VIVANT})
) ld ON ld.delegation_id = d.acte_id
LEFT JOIN v_dossiers dep
       ON dep.dossier_id = ld.dossier_id
      AND (d.valide_du = '' OR dep.date_depense >= d.valide_du)
      AND (d.valide_au = '' OR dep.date_depense <= d.valide_au)
WHERE d.portee = '{PORTEE_DELEGATION_CS}'
GROUP BY d.acte_id, d.etat;
"""

# --------------------------------------------------------------------------
# v_execution - ce qui a ete vote a-t-il ete fait
# --------------------------------------------------------------------------

#: La sixieme source de la matrice, celle que le blueprint ajoute aux cinq
#: colonnes de la strategie. Elle porte les constats les plus chers du produit:
#: `votee, rien de paye`, `paye 23 460 pour 18 240 votes`.
_V_EXECUTION = f"""
CREATE VIEW IF NOT EXISTS v_execution AS
SELECT
    a.acte_id, a.nature, a.etat, a.portee, a.exercice, a.objet,
    a.entreprise_effective AS entreprise, a.entreprise_lue_sur, a.montant_lu_sur,
    a.date_effet, a.resultat,
    {sql_reel('a.montant_effectif')}      AS montant_autorise,
    COUNT(DISTINCT dep.dossier_id)                   AS depenses_rattachees,
    COALESCE(SUM({sql_reel('dep.montant_ttc')}), 0.0) AS montant_paye
FROM v_acte_effectif a
LEFT JOIN (
    SELECT DISTINCT l.source_id AS acte_id, l.target_id AS dossier_id
    FROM {TABLE_LIENS} l
    WHERE l.relation = 'AUTORISE' AND l.source_kind = 'acte'
      AND ({_LIEN_VIVANT})
) ld ON ld.acte_id = a.acte_id
LEFT JOIN v_dossiers dep ON dep.dossier_id = ld.dossier_id
GROUP BY a.acte_id, a.etat;
"""


VUES: tuple[str, ...] = (
    _V_ACTES,
    _V_DOSSIERS,
    _V_DOSSIERS_TVA,
    _V_ACTE_EFFECTIF,
    _V_DIVERGENCES,
    _V_LIENS_MANQUANTS,
    _V_CUMUL,
    _V_EXECUTION,
    vue_matrice(_LIEN_VIVANT),
    vue_constats(_LIEN_VIVANT),
    VUE_TAUX,
)

#: Les vues sont recreees a chaque ouverture: leur definition appartient au
#: code, pas a la base. Une base ouverte par une version plus recente doit voir
#: les vues de cette version, sinon la base porterait une regle de droit
#: perimee sans que rien ne le signale.
NOMS_VUES: tuple[str, ...] = (
    "v_actes",
    "v_dossiers",
    "v_dossiers_tva",
    "v_acte_effectif",
    "v_divergences_humaines",
    "v_liens_manquants",
    "v_cumul_delegation",
    "v_execution",
    "v_matrice_gouvernance",
    "v_constats",
    "v_taux_gouvernance",
)
