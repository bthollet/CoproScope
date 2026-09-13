"""Les constats: les ruptures, nommees, datees, chiffrees - et **bornees**.

Separe de `_actes_vues` le 2026-09-04 pour deux raisons, dont une seule est la
taille du fichier.

La vraie raison est que ce module repond a une question que les autres vues ne
posent pas: **a qui ce controle s'applique-t-il ?** Une vue de lecture rend ce
qui est ecrit. Un constat affirme qu'une regle a ete rompue, et une affirmation
de ce genre ne vaut que si son destinataire y etait soumis.

Le defaut corrige ici a ete vu par Brice sur la maquette du 2026-09-03: les 55
resolutions d'une assemblee arrivaient sur le meme plan, et les controles de
seuil et d'avis du conseil syndical etaient appliques a toutes - y compris aux
vingt-deux elections, qui ne passent aucun marche. Un constat faux ne se contente
pas d'etre faux: il noie les vrais, et l'utilisateur cesse de lire la file.

La reponse n'est pas une exception codee en dur ici. C'est
`_actes_typologie.HORS_CONTROLE`, une matrice portee x controle ou chaque
retrait porte son motif et son article. Ce module ne fait que la traduire en
`IN (...)`: une egalite sur une colonne declaree, jamais une recherche de mots.

**Un controle qui ne peut pas s'exercer le dit.** Ajoute le 2026-09-04. Une
file de travail vide se lisait `tout a ete execute`, et la difference entre
`aucun manquement` et `le controle n'a pas pu s'exercer` n'etait portee nulle
part - alors que le modele a invente `FORCE_NON_APPLICABLE` precisement pour
tenir cette distinction sur les cellules. Mesure sur les 55 resolutions du
proces-verbal etalon: `ACTE_SANS_EXECUTION` etait inatteignable, 43 lignes
retirees par la portee, les restantes par l'exigence d'un montant lisible, et
`v_constats` rendait deux constats en tout. Les codes qui portent cet aveu -
`EXECUTION_NON_CONTROLABLE`, `ECHEANCE_INCALCULABLE`, `DELEGATION_SANS_PERIODE`
- ne reprochent rien a la copropriete: ils disent ce que le modele ne sait pas
faire avec ce qu'il a lu.
"""

from __future__ import annotations

from ._actes_typologie import CTRL_EXECUTION, CTRL_MAJORITE, portees_retirees, portees_soumises
from ._actes_vocabulaire import (
    IMPUTATION_BUDGET,
    IMPUTATION_INDETERMINEE,
    MAJORITE_NON_ENONCEE,
    PROV_CONTREDIT,
)
from ._actes_schema import TABLE_ACTES, TABLE_LIENS, sql_reel


def _liste(valeurs: tuple[str, ...]) -> str:
    """Les valeurs, litteralisees pour un `IN (...)`.

    Le vocabulaire est ferme et vient du code, pas d'une saisie: il n'y a donc
    pas de parametre a lier. Une vue SQLite ne prend de toute facon aucun
    parametre - c'est la contrainte qui a fait naitre ce module.
    """
    return ", ".join("'{0}'".format(v) for v in valeurs)


def _hors_controle(colonne: str, controle: str) -> str:
    """Le predicat qui retire ce controle aux portees qui en sont dispensees.

    **Un retrait, pas une admission.** La premiere version bornait par
    `portee IN (portees_soumises(...))`, ce qui parait equivalent et ne l'est
    pas: une portee absente du vocabulaire - le vide, qu'`_actes_store` admet
    a l'ecriture parce qu'une colonne non renseignee est un fait et pas une
    faute - n'est dans aucune liste, donc echouait le `IN` et sortait du
    constat sans qu'aucune ligne ne le dise.

    Mesure du 2026-09-05, deux actes dont la majorite annoncee porte la meme
    valeur de `MAJORITE_NON_ENONCEE`, l'un portee='ORDINAIRE' l'autre
    portee='': la borne `IN` rendait un constat, la borne `NOT IN` rend les
    deux. C'est le constat C017 de l'audit - une portee inconnue desactive les
    controles au lieu de les garder - et il etait ici arme sur trois constats.

    Rend la chaine vide quand aucune portee n'est retiree: il n'y a alors rien
    a ecrire, et un `NOT IN ()` ne s'ecrit pas en SQLite. Le predicat est donc
    concatene APRES un terme toujours present, jamais en tete d'un `WHERE`.
    """
    retirees = portees_retirees(controle)
    if not retirees:
        return ""
    return f"\n   AND {colonne} NOT IN ({_liste(retirees)})"


def vue_constats(lien_vivant: str) -> str:
    """La vue `v_constats`, bornee par la matrice des controles applicables.

    `lien_vivant` est le predicat partage de `_actes_vues`: un lien compte sauf
    si un humain a contredit cette paire precise. Il est passe en argument
    plutot qu'importe pour que la dependance aille dans un seul sens - les vues
    connaissent les constats, les constats ne connaissent pas les vues.
    """
    # Un RETRAIT, pas une admission: une portee absente du vocabulaire - le
    # vide, qu'`_actes_store` admet a l'ecriture parce qu'une colonne non
    # renseignee est un fait et pas une faute - n'est dans aucune liste, donc
    # echouait le `IN` et sortait du constat sans qu'aucune ligne ne le dise.
    # C'est le constat C017 de l'audit, et il etait arme sur trois constats.
    hors_execution = _hors_controle("e.portee", CTRL_EXECUTION)
    hors_majorite = _hors_controle("a.portee", CTRL_MAJORITE)
    return f"""
CREATE VIEW IF NOT EXISTS v_constats AS
SELECT 'ACTE_SANS_FONDEMENT' AS code, 'acte' AS sujet_kind, m.acte_id AS sujet_id,
       m.exercice, m.date_effet AS date_fait, '' AS date_echeance,
       {sql_reel('m.montant_autorise')} AS montant_en_jeu,
       -- L'objet ne va PAS dans le motif. Corrige le 2026-09-04: `objet` est
       -- du texte libre non contraint, et la resolution 35 de l'etalon est une
       -- demande individuelle dont l'intitule nomme le demandeur et son lot.
       -- Le schema pose qu'aucune colonne de texte integral n'existe pour que
       -- les noms de coproprietaires n'entrent pas dans ce magasin; la
       -- barriere portait sur la colonne texte et pas sur l'objet, alors que
       -- le motif d'un constat est destine a l'ecran et potentiellement a un
       -- export. L'identifiant, lui, est derive: il porte la date et le rang,
       -- rien d'autre, et il distingue deux constats du meme code.
       -- Une date vide ne s'interpole pas telle quelle. Le motif sortait
       -- `Decision du conseil syndical du  (...)`, un trou que le lecteur
       -- prend pour un defaut d'affichage alors qu'il enonce un fait: la date
       -- n'a pas ete lue.
       'Decision du conseil syndical ' ||
       CASE WHEN m.date_effet <> '' THEN 'du ' || m.date_effet
            ELSE 'dont la date n''a pas ete lue' END ||
       ' (' || m.acte_id || ') : aucune delegation en vigueur ne la fonde.'
       AS motif
  FROM v_liens_manquants m WHERE m.sens = 'ARRIERE'

UNION ALL
SELECT 'OBLIGATION_NON_TENUE', 'acte', m.acte_id, m.exercice,
       m.date_effet, m.echeance,
       {sql_reel('m.montant_autorise')},
       CASE m.regle
         WHEN 'AG_APPROBATION_COMPTES' THEN
           'Decision du ' || m.date_effet || ' : aucun compte rendu devant l''assemblee du '
           || m.echeance || ' qui a approuve les comptes (article 21-5).'
         ELSE
           'Depense engagee en urgence le ' || m.date_effet ||
           ' : elle n''a pas ete portee a l''assemblee du ' || m.echeance || '.'
       END
  FROM v_liens_manquants m WHERE m.sens = 'AVANT' AND m.echeance <> ''

UNION ALL
SELECT 'URGENCE_JAMAIS_PORTEE', 'acte', m.acte_id, m.exercice,
       m.date_effet, '',
       {sql_reel('m.montant_autorise')},
       'Depense engagee en urgence le ' || m.date_effet ||
       ' : aucune assemblee ne s''est tenue depuis. Elle n''a ete portee nulle part.'
  FROM v_liens_manquants m
 WHERE m.sens = 'AVANT' AND m.echeance = '' AND m.regle = 'AG_SUIVANTE'
   -- La date de l'acte est exigee ici depuis le 2026-09-04. Sans elle, le
   -- constat sortait avec un trou - `Depense engagee en urgence le  :` - et
   -- accusait le syndic de n'avoir tenu aucune assemblee, alors que la seule
   -- chose etablie etait que la date de l'engagement n'avait pas ete lue.
   -- Le cas est nomme juste en dessous, par ECHEANCE_INCALCULABLE.
   AND m.date_effet <> ''

UNION ALL
-- **L'echeance ne peut pas etre calculee, et ce n'est pas un manquement.**
-- Un acte soumis a une obligation datee dont la date propre n'a pas ete lue
-- ne peut etre ni tenu ni manque: il peut seulement etre indecidable. Sans ce
-- code, ces lignes tombaient soit dans OBLIGATION_NON_TENUE avec l'echeance de
-- la plus ANCIENNE assemblee connue - donc un manquement date d'avant l'acte -
-- soit dans URGENCE_JAMAIS_PORTEE avec un motif troue. 110 resolutions sur 173
-- du coffre reel sont rattachees a une assemblee sans date lue: c'est le cas
-- nominal, pas le cas limite.
SELECT 'ECHEANCE_INCALCULABLE', 'acte', m.acte_id, m.exercice,
       '', '',
       {sql_reel('m.montant_autorise')},
       'Acte ' || m.acte_id || ' : une obligation datee lui est attachee (' ||
       m.regle || '), et la date de l''acte n''a pas ete lue. Ni tenue ni ' ||
       'manquee ne peut etre etabli tant que cette date manque.'
  FROM v_liens_manquants m
 WHERE m.sens = 'AVANT' AND m.date_effet = ''

UNION ALL
SELECT 'DELEGATION_EXPIREE', 'acte', l.source_id, a.exercice,
       a.date_effet, d.valide_au,
       {sql_reel('a.montant_autorise')},
       'Decision du ' || a.date_effet || ' adossee a la delegation du ' ||
       d.date_effet || ', dont la validite s''arretait le ' || d.valide_au || '.'
  FROM {TABLE_LIENS} l
  JOIN v_actes a ON a.acte_id = l.source_id
  JOIN v_actes d ON d.acte_id = l.target_id
 WHERE l.relation = 'FONDE_PAR' AND l.provenance <> '{PROV_CONTREDIT}'
   AND d.valide_au <> '' AND a.date_effet <> '' AND a.date_effet > d.valide_au

UNION ALL
SELECT 'PLAFOND_DEPASSE', 'acte', c.delegation_id, c.exercice_vote,
       c.valide_du, c.valide_au, c.cumul - c.plafond,
       'Delegation votee le ' || c.delegation_votee_le || ' : ' ||
       CAST(c.depenses_cumulees AS TEXT) || ' depenses cumulees pour ' ||
       printf('%.2f', c.cumul) ||
       -- La phrase ne dit `sur la periode` que si une periode est connue.
       -- Elle le disait toujours, y compris quand les deux bornes etaient
       -- vides et que le cumul portait donc sur tous les temps. Dans le coffre
       -- reel, `valide_au` est renseigne sur 2 lignes sur 173.
       CASE WHEN c.periode_lue = 1
            THEN ' EUR sur la periode du ' || c.valide_du || ' au ' || c.valide_au
            ELSE ' EUR, toutes dates confondues faute de periode lue'
       END ||
       ', plafond arrete a ' || printf('%.2f', c.plafond) || ' EUR.'
  FROM v_cumul_delegation c
 WHERE c.plafond IS NOT NULL AND c.cumul > c.plafond

UNION ALL
-- **Le plafond ne se compare a rien tant que la periode manque.** Le cumul
-- affiche est celui de toutes les depenses rattachees, quelle que soit leur
-- date; il n'est ni le cumul de la delegation ni un cumul faux, il est un
-- cumul dont on ignore la borne. Mesure: une delegation de 2023 plafonnee a
-- 5 000 avec trois depenses de 2 000 datees 2023, 2024 et 2026 rendait 6 000 et
-- un depassement; la periode lue, la meme base rend 4 000 et rien.
SELECT 'DELEGATION_SANS_PERIODE', 'acte', c.delegation_id, c.exercice_vote,
       c.delegation_votee_le, '', c.cumul,
       'Delegation votee le ' || c.delegation_votee_le || ' : sa periode de ' ||
       'validite n''a pas ete lue (article 21-3, deux ans au plus). Le cumul ' ||
       'de ' || printf('%.2f', c.cumul) || ' EUR porte donc sur toutes les ' ||
       'depenses rattachees, sans borne de date, et ne peut pas etre oppose ' ||
       'au plafond.'
  FROM v_cumul_delegation c
 WHERE c.periode_lue = 0 AND c.depenses_cumulees > 0

UNION ALL
-- **Article 21-3: deux ans au plus.** Ce controle etait cite comme motif du
-- retrait du controle de seuil sur les delegations - `son controle propre est
-- ailleurs: deux ans au plus (art. 21-3)` - et n'existait nulle part: `21-3`
-- n'apparaissait que dans des docstrings, et aucune comparaison de duree
-- n'etait ecrite. Un controle desactive au nom d'un garde-fou inexistant est
-- pire qu'un controle absent, parce que son motif fait autorite a l'ecran.
-- 731 jours: deux annees dont une bissextile, la borne haute admissible.
SELECT 'DELEGATION_TROP_LONGUE', 'acte', c.delegation_id, c.exercice_vote,
       c.valide_du, c.valide_au, NULL,
       'Delegation votee le ' || c.delegation_votee_le || ' : elle court du ' ||
       c.valide_du || ' au ' || c.valide_au || ', soit ' ||
       CAST(CAST(julianday(c.valide_au) - julianday(c.valide_du) AS INTEGER) AS TEXT) ||
       ' jours. L''article 21-3 borne la delegation a deux ans.'
  FROM v_cumul_delegation c
 WHERE c.periode_lue = 1
   AND julianday(c.valide_au) - julianday(c.valide_du) > 731

UNION ALL
SELECT 'ACTE_SANS_EXECUTION', 'acte', e.acte_id, e.exercice,
       e.date_effet, '', e.montant_autorise,
       'Resolution du ' || e.date_effet || ' (' || e.acte_id ||
       ') adoptee pour ' || printf('%.2f', e.montant_autorise) ||
       ' EUR : aucune depense ne lui est rattachee.'
  FROM v_execution e
 WHERE e.etat = 'CONSTATEE' AND e.resultat = 'ADOPTEE'  -- jamais VOTE_SANS_FORMULE
   AND e.montant_autorise IS NOT NULL AND e.montant_autorise > 0
   AND e.depenses_rattachees = 0{hors_execution}

UNION ALL
-- **Le controle d'execution n'a pas pu s'exercer, et le dire n'est pas
-- l'exercer.** Le predicat `montant_autorise > 0` de ACTE_SANS_EXECUTION est
-- juste - sans montant, `rien de paye` ne veut rien dire - mais il retirait
-- les lignes en silence. Mesure sur le proces-verbal etalon: apres la portee,
-- six resolutions restaient soumises au controle, et les six sortaient par le
-- montant. Zero manquement, zero mention: une file vide se lisait `tout a ete
-- execute`.
SELECT 'EXECUTION_NON_CONTROLABLE', 'acte', e.acte_id, e.exercice,
       e.date_effet, '', NULL,
       'Resolution ' || e.acte_id ||
       CASE WHEN e.date_effet <> '' THEN ' du ' || e.date_effet ELSE '' END ||
       ' adoptee, ' ||
       'soumise au controle d''execution, et aucun montant n''a ete lu sur ' ||
       'elle. Le rapprochement entre ce qui a ete vote et ce qui a ete paye ' ||
       'ne peut pas etre conduit: ce n''est pas l''absence de manquement.'
  FROM v_execution e
 WHERE e.etat = 'CONSTATEE' AND e.resultat = 'ADOPTEE'
   AND 1 = 1{hors_execution}
   AND e.depenses_rattachees = 0
   AND (e.montant_autorise IS NULL OR e.montant_autorise <= 0)

UNION ALL
-- `montant_en_jeu` est la valeur ABSOLUE de l'ecart depuis le 2026-09-04. La
-- file est triee `montant_en_jeu DESC` et sa docstring promet un tri par
-- montant en jeu; avec l'ecart signe, un acte de 100 000 EUR votes dont
-- 1 000 seulement ont ete payes portait -99 000 et arrivait APRES un ecart de
-- 200 EUR. Le sens de l'ecart reste lisible dans le motif, qui affiche les
-- deux montants.
SELECT 'MONTANT_DIVERGENT', 'acte', e.acte_id, e.exercice,
       e.date_effet, '', ABS(e.montant_paye - e.montant_autorise),
       'Resolution du ' || e.date_effet || ' : ' || printf('%.2f', e.montant_paye) ||
       ' EUR payes pour ' || printf('%.2f', e.montant_autorise) || ' EUR votes.'
  FROM v_execution e
 WHERE e.montant_autorise IS NOT NULL AND e.montant_autorise > 0
   AND e.depenses_rattachees > 0
   AND ABS(e.montant_paye - e.montant_autorise) > 0.005{hors_execution}

UNION ALL
-- **La portee vide, seconde branche de C003.** Le vide est admis a l'ecriture
-- par conception - une portee que le document ne permet pas de lire est un
-- fait, pas une faute - mais il n'etait dit nulle part. Mesure du 2026-09-05,
-- le meme acte sous deux portees: avec `ORDINAIRE`, sept cellules dont cinq
-- interrogeables et un constat; avec `''`, la ligne reste dans la matrice, les
-- SEPT cellules passent a `NON_APPLICABLE` et le nombre de constats tombe a
-- zero. Un acte parfaitement muet, indiscernable d'un acte en regle.
--
-- `ORDINAIRE` n'est pas ce cas: il veut dire « portee non determinee » et
-- garde les sept controles. Le vide, lui, les eteint tous. La difference
-- devait donc etre visible, et elle ne l'etait pas.
SELECT 'PORTEE_NON_LUE', 'acte', a.acte_id, a.exercice,
       a.date_effet, '',
       {sql_reel('a.montant_effectif')},
       'Acte ' || a.acte_id ||
       CASE WHEN a.date_effet <> '' THEN ' du ' || a.date_effet ELSE '' END ||
       ' : aucune portee n''a ete lue sur cet acte. Les sept controles sont ' ||
       'donc affiches « ne s''applique pas », et l''absence de manquement ne ' ||
       'vaut ici aucune conformite: rien n''a ete verifie.'
  FROM v_acte_effectif a
 WHERE COALESCE(a.portee, '') = '' AND a.etat <> 'PROJETEE'

UNION ALL
SELECT 'ISSUE_NON_ENONCEE', 'acte', a.acte_id, a.exercice,
       a.date_effet, '',
       {sql_reel('a.montant_effectif')},
       'Resolution ' || a.numero || ' du ' || a.date_effet ||
       ' : les voix sont comptees, le proces-verbal '
       || 'n''enonce pas l''issue. Rien n''autorise a conclure a l''adoption.'
  FROM v_acte_effectif a
 WHERE a.resultat = 'VOTE_SANS_FORMULE' AND a.etat <> 'PROJETEE'

UNION ALL
-- **Cinquieme etat de resultat, jusqu'ici sans destination.** Le vocabulaire
-- declare `SANS_ISSUE_TRACEE` - ni vote, ni formule, ni mention - et aucune
-- branche de v_constats ne le visait: la matrice le rangeait en cellule
-- `ABSENT`, une case grise parmi mille autres, et le cas que l'etalon isole
-- explicitement traversait tout le modele sans produire une ligne de travail.
-- Le coffre reel en porte quatre. Distinct de ISSUE_NON_ENONCEE: la, des voix
-- ont ete comptees; ici, le proces-verbal ne dit rien du tout.
SELECT 'ISSUE_NON_TRACEE', 'acte', a.acte_id, a.exercice,
       a.date_effet, '',
       {sql_reel('a.montant_effectif')},
       'Resolution ' || a.numero || ' du ' || a.date_effet ||
       ' : le proces-verbal a ete lu et ne trace aucune issue - ni voix, ni '
       || 'formule d''adoption ou de rejet, ni mention d''absence de vote. '
       || 'C''est un constat sur le document, pas une piece manquante.'
  FROM v_acte_effectif a
 WHERE a.resultat = 'SANS_ISSUE_TRACEE' AND a.etat <> 'PROJETEE'

UNION ALL
-- **Sixieme etat de resultat, et le seul qui ne reproche rien a personne.**
-- `ISSUE_NON_LUE` dit que le proces-verbal ENONCE une issue et que la chaine
-- n'a pas su la lire - c'est le fait sur notre lecteur, pas sur l'assemblee.
-- Sans branche ici il produisait une cellule `AFFIRME_SANS_PIECE` et rien
-- d'autre: un « A confirmer » de plus dans une matrice qui en porte des
-- centaines, et le seul etat du vocabulaire dont la reparation soit a notre
-- portee ne faisait naitre aucune ligne de travail. C'est mot pour mot le
-- defaut decrit deux branches plus haut pour `SANS_ISSUE_TRACEE`.
--
-- Il ne rejoint donc PAS ses deux voisines: elles constatent ce que le
-- document ne dit pas et appellent une question au syndic, celle-ci constate
-- ce que nous n'avons pas lu et appelle une relecture. La pastille de l'ecran
-- le porte par `SOURCE_OUTIL`, la ou les deux autres sont `SOURCE_PIECES`.
--
-- La garde `etat <> 'PROJETEE'` est celle des deux voisines: une convocation
-- ne conclut rien, donc il n'y a rien a y avoir mal lu.
SELECT 'ISSUE_NON_LUE_A_RELIRE', 'acte', a.acte_id, a.exercice,
       a.date_effet, '',
       {sql_reel('a.montant_effectif')},
       -- Une date vide ne s'interpole pas. Les deux branches voisines
       -- concatenent `' du ' || a.date_effet` sans garde et sortent
       -- `Resolution 12 du  :` quand la date n'a pas ete lue; le trou se lit
       -- comme un defaut d'affichage alors qu'il enonce un fait. La garde est
       -- celle qu'`ACTE_SANS_FONDEMENT` porte deja en tete de cette vue.
       'Resolution ' || a.numero ||
       CASE WHEN a.date_effet <> '' THEN ' du ' || a.date_effet ELSE '' END ||
       ' : le proces-verbal dit bien ce que l''assemblee a decide sur cette '
       || 'resolution, et le logiciel n''a pas su lire sa conclusion. Ce '
       || 'n''est ni une piece manquante ni un silence du syndic : le '
       || 'document est au dossier, et il conclut. Le defaut est dans notre '
       || 'lecture, et il demande une relecture humaine - tant qu''elle n''est '
       || 'pas faite, cette resolution n''autorise aucune depense.'
  FROM v_acte_effectif a
 WHERE a.resultat = 'ISSUE_NON_LUE' AND a.etat <> 'PROJETEE'

UNION ALL
SELECT 'MAJORITE_NON_ENONCEE', 'acte', a.acte_id, a.exercice,
       a.date_effet, '',
       {sql_reel('a.montant_effectif')},
       'Resolution ' || a.numero || ' du ' || a.date_effet ||
       ' : aucune majorite n''est enoncee par le proces-verbal.'
  FROM v_acte_effectif a
 -- CTRL_MAJORITE etait declare comme septieme controle et n'etait consulte
 -- nulle part: `portees_soumises('MAJORITE')` rendait onze portees sans
 -- appelant, et la docstring de CONTROLES affirmait pourtant `Sept, pas plus:
 -- un controle qui n'a ni cellule ni constat n'existe pas`. Un controle
 -- declare et non branche est plus dangereux qu'un controle absent, parce que
 -- sa declaration fait croire qu'il tourne - et un retrait ecrit dans
 -- HORS_CONTROLE n'aurait eu aucun effet observable. Il en a un ici.
 -- **La garde d'etat manquait, et elle accusait un document inexistant.**
 -- Mesure du 2026-09-05 sur le coffre reel: sur 22 constats emis, 18 portaient
 -- sur un acte dont le seul etat est PROJETEE - un projet de resolution lu
 -- dans une CONVOCATION, pour lequel aucun proces-verbal n'existe. Le motif
 -- rendu disait pourtant "aucune majorite n'est enoncee par le
 -- proces-verbal". Les trois branches voisines de ce meme SQL portent la
 -- garde depuis leur ecriture; celle-ci ne l'avait pas, et c'est la fermeture
 -- de C061 qui a fait passer le compteur de 0 a 22 - donc qui a rendu le
 -- manque visible en le rendant nuisible.
 WHERE a.majorite_annoncee = '{MAJORITE_NON_ENONCEE}' AND a.etat <> 'PROJETEE'{hors_majorite}

UNION ALL
SELECT 'TVA_INCOHERENTE', 'dossier', t.dossier_id, t.exercice,
       t.date_depense, '',
       ABS(t.tva_comptable - t.tva_attendue),
       'Depense du ' || t.date_depense || ' (' || substr(t.libelle,1,50) ||
       ') : la comptabilite retient ' || printf('%.2f', t.tva_comptable) ||
       ' de T.V.A. quand la piece en annonce ' || printf('%.2f', t.tva_attendue)
       || CASE t.tva_regime
            WHEN 'NON_APPLICABLE' THEN ' - la piece porte T.V.A. non applicable.'
            WHEN 'EXONERE' THEN ' - cette depense ne supporte pas de T.V.A.'
            ELSE ' au taux de ' || t.taux_tva_annonce || ' %.' END
  FROM v_dossiers_tva t
 WHERE t.tva_attendue IS NOT NULL AND t.tva_comptable IS NOT NULL
   AND ABS(t.tva_comptable - t.tva_attendue) > 0.005

UNION ALL
SELECT 'EURO_SANS_ACTE', 'dossier', d.dossier_id, d.exercice,
       d.date_depense, '',
       {sql_reel('d.montant_ttc')},
       'Depense du ' || d.date_depense || ' (' || substr(d.libelle,1,60) ||
       ', ' || d.fournisseur || ') : imputee ' || d.imputation ||
       ', donc hors budget previsionnel, et aucun acte d''autorisation ne la couvre.'
  FROM v_dossiers d
 WHERE d.imputation NOT IN ('{IMPUTATION_BUDGET}', '{IMPUTATION_INDETERMINEE}')
   AND NOT EXISTS (
        SELECT 1 FROM {TABLE_LIENS} l
        WHERE l.relation = 'AUTORISE' AND l.target_kind = 'dossier'
          AND l.target_id = d.dossier_id AND ({lien_vivant}))

UNION ALL
SELECT 'IMPUTATION_A_TRANCHER', 'dossier', d.dossier_id, d.exercice,
       d.date_depense, '',
       {sql_reel('d.montant_ttc')},
       'Depense du ' || d.date_depense || ' (' || substr(d.libelle,1,60) ||
       ', ' || d.fournisseur || ') : aucun acte ne la couvre, et son imputation '
       || 'n''est pas tranchee. Deux reponses possibles, et une seule est un '
       || 'manquement : depense courante de maintenance couverte par le budget '
       || 'previsionnel deja vote (art. 14-1 I), ou depense de travaux exigeant '
       || 'un vote separe (decret art. 44). Le partage tient a la definition de '
       || 'la maintenance de l''article 45 et se tranche piece par piece.'
  FROM v_dossiers d
 WHERE d.imputation = '{IMPUTATION_INDETERMINEE}'
   AND NOT EXISTS (
        SELECT 1 FROM {TABLE_LIENS} l
        WHERE l.relation = 'AUTORISE' AND l.target_kind = 'dossier'
          AND l.target_id = d.dossier_id AND ({lien_vivant}))

UNION ALL
-- **Une correction humaine qui porte sur l'identite cree un second acte.**
-- `acte_id` derive de (date, numero, sous-numero): corriger l'un des trois -
-- c'est-a-dire exactement le defaut que le module documente comme mesure et
-- reel, la date d'assemblee non lue - donne un nouvel identifiant. L'acte
-- machine d'origine reste vivant dans `v_actes`, faute d'homologue humain sur
-- SON identifiant, et `v_divergences_humaines` ne montre rien puisqu'elle
-- joint sur `acte_id`. La promesse `la correction humaine gagne a la lecture,
-- et l'ecart reste visible` ne tenait que pour les champs hors identite.
-- Le doublon ne se repare pas ici - fusionner deux actes sur une ressemblance
-- serait la conclusion que tout ce lot refuse - mais il cesse d'etre muet.
SELECT 'ACTE_REIDENTIFIE_PAR_HUMAIN', 'acte', machine.acte_id, machine.exercice,
       machine.date_effet, '',
       {sql_reel('machine.montant_autorise')},
       'Acte ' || machine.acte_id || ' : un humain a corrige la date, le ' ||
       'numero ou le sous-numero de la meme resolution du meme document, ce ' ||
       'qui a produit un second acte (' || humain.acte_id || '). Les deux ' ||
       'restent lus. Un seul decrit la resolution: c''est a trancher.'
  FROM v_actes machine
  JOIN {TABLE_ACTES} humain
    ON humain.origine = 'CORRIGE_HUMAIN'
   AND humain.doc_id = machine.doc_id
   AND humain.etat = machine.etat
   AND humain.resolution_id <> '' AND humain.resolution_id = machine.resolution_id
   AND humain.acte_id <> machine.acte_id
 WHERE machine.origine = 'EXTRAIT'

UNION ALL
-- **L'assemblee existe, elle n'est pas typee, et l'obligation reste due.**
-- L'echeance de l'article 21-5 ne se calcule que si une assemblee posterieure
-- porte `portee = APPROBATION_COMPTES`. La docstring justifiait le silence par
-- `si aucune n'est encore lue, l'obligation n'est pas exigible` - ce qui
-- confond `aucune assemblee posterieure n'existe` et `aucune assemblee
-- posterieure n'a ete typee`. Dans le second cas l'obligation est bel et bien
-- exigible, et c'est le cas nominal: 154 resolutions sur 173 du coffre reel
-- n'obtiennent aucune portee.
SELECT 'REDDITION_NON_VERIFIABLE', 'acte', m.acte_id, m.exercice,
       m.date_effet, '',
       {sql_reel('m.montant_autorise')},
       'Decision du ' || m.date_effet || ' (' || m.acte_id || ') : une ' ||
       'assemblee s''est tenue depuis, et aucune n''est reconnue comme ayant ' ||
       'approuve les comptes. Le compte rendu de l''article 21-5 ne peut pas ' ||
       'etre rapproche d''une assemblee: ce n''est pas qu''il n''est pas du.'
  FROM v_liens_manquants m
 WHERE m.sens = 'AVANT' AND m.regle = 'AG_APPROBATION_COMPTES'
   AND m.echeance = '' AND m.date_effet <> ''
   AND EXISTS (SELECT 1 FROM v_actes x
                WHERE x.nature = 'RESOLUTION_AG' AND x.etat = 'CONSTATEE'
                  AND x.date_effet > m.date_effet)

UNION ALL
SELECT 'PV_SANS_DATE_LUE', 'document', a.doc_id, a.exercice,
       '', '', NULL,
       'Un proces-verbal a ete lu sans que sa date d''assemblee soit reconnue : '
       || CAST(COUNT(*) AS TEXT) || ' resolutions sont rattachees a une assemblee sans date.'
  FROM v_actes a
 WHERE a.nature = 'RESOLUTION_AG' AND a.date_effet = ''
 GROUP BY a.doc_id;
"""


#: Le nom de la vue, pour que `_actes_vues` puisse la declarer sans la
#: reconstruire.
NOM_VUE = "v_constats"
