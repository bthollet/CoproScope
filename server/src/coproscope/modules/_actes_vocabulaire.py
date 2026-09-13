"""Le vocabulaire du modele: les valeurs que les colonnes ont le droit de prendre.

Separe de `_actes_schema` pour une raison qui n'est pas la taille du fichier: un
vocabulaire est **du droit rendu enumerable**, et il doit pouvoir etre lu, cite
et compare a un texte de loi sans traverser des declarations de tables.

Regle qui traverse tout ce module: **aucune valeur signifiante n'est `NULL` ni
la chaine vide.** Un fait constate sur un document - "le proces-verbal n'enonce
pas l'issue", "aucune majorite n'est enoncee" - est une valeur nommee. Un `NULL`
ne se distingue pas d'un oubli d'extraction, et une colonne nullable finit
toujours par etre lue comme "on ne sait pas" alors qu'elle disait "le document
ne le dit pas".
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Vocabulaires
# --------------------------------------------------------------------------

#: Les trois natures du modele. UNE SEULE est autonome, et cela se lit dans le
#: schema: `RESOLUTION_AG` est absente de `EXIGENCES_LIEN`.
NATURE_RESOLUTION_AG = "RESOLUTION_AG"
NATURE_DECISION_CS = "DECISION_CS_DELEGUEE"
NATURE_URGENCE = "URGENCE_SYNDIC"
NATURES = (NATURE_RESOLUTION_AG, NATURE_DECISION_CS, NATURE_URGENCE)

#: Les deux etats de cycle de vie du modele section 9. Pas de promotion: une
#: `PROJETEE` ne devient jamais `CONSTATEE`, le constat s'ecrit a cote.
ETAT_CONSTATEE = "CONSTATEE"
ETAT_PROJETEE = "PROJETEE"
ETATS = (ETAT_CONSTATEE, ETAT_PROJETEE)

#: Portee d'un acte: **sur quoi il porte**. C'est un axe distinct de `nature`,
#: qui dit d'ou vient l'autorisation - une assemblee, une delegation, l'urgence.
#: Les deux se croisent et ne se remplacent pas: une `RESOLUTION_AG` de portee
#: `DESIGNATION_SYNDIC` et une `DECISION_CS_DELEGUEE` de portee
#: `ENGAGEMENT_DEPENSE` sont deux points differents du meme plan.
#:
#: Elle sert aux predicats, pas a l'affichage: c'est elle qui dit si un acte est
#: une delegation, un seuil, une approbation des comptes - donc si un autre acte
#: peut s'y adosser, a quelle echeance, et **quels controles lui sont
#: applicables**. Ce dernier point est le sujet de `HORS_CONTROLE`, plus bas.
PORTEE_ORDINAIRE = "ORDINAIRE"
PORTEE_DELEGATION_CS = "DELEGATION_CS"
PORTEE_SEUIL = "SEUIL"
PORTEE_BUDGET = "BUDGET_PREVISIONNEL"
PORTEE_APPROBATION_COMPTES = "APPROBATION_COMPTES"
PORTEE_FONDS_TRAVAUX = "FONDS_TRAVAUX"
#: Les cinq portees ajoutees le 2026-09-04. Elles ne sont pas des categories
#: d'affichage: chacune existe parce qu'elle **retire ou ajoute un controle**.
#: Voir `HORS_CONTROLE` - une portee qui ne changerait aucun controle n'aurait
#: pas de raison d'exister, et `MODALITES` absorbe pour cette raison l'
#: habilitation a agir en justice et le mandat d'execution au syndic.
PORTEE_DESIGNATION_SYNDIC = "DESIGNATION_SYNDIC"
PORTEE_DESIGNATION_ORGANE = "DESIGNATION_ORGANE"
PORTEE_ENGAGEMENT_DEPENSE = "ENGAGEMENT_DEPENSE"
PORTEE_AUTORISATION_COPROPRIETAIRE = "AUTORISATION_COPROPRIETAIRE"
PORTEE_MODALITES = "MODALITES"
PORTEES = (
    PORTEE_ORDINAIRE,
    PORTEE_DELEGATION_CS,
    PORTEE_SEUIL,
    PORTEE_BUDGET,
    PORTEE_APPROBATION_COMPTES,
    PORTEE_FONDS_TRAVAUX,
    PORTEE_DESIGNATION_SYNDIC,
    PORTEE_DESIGNATION_ORGANE,
    PORTEE_ENGAGEMENT_DEPENSE,
    PORTEE_AUTORISATION_COPROPRIETAIRE,
    PORTEE_MODALITES,
)

#: Le vocabulaire des liens. Deux familles, et la distinction est celle du
#: modele section 2: un lien ARRIERE est une **condition de validite**, un lien
#: AVANT est une **obligation a echeance** dont l'absence est un manquement
#: date. Les sept dernieres relations sont les sept sources de la matrice - six
#: jusqu'au 2026-09-08, ou la relation de seuil s'est scindee en deux normes
#: plus un residu nomme.
REL_FONDE_PAR = "FONDE_PAR"
REL_REND_COMPTE_A = "REND_COMPTE_A"
REL_RATIFIE_PAR = "RATIFIE_PAR"
REL_AUTORISE = "AUTORISE"
#: **Deux normes, deux relations.** Ajoutees le 2026-09-08 (`RM-2026-0144`).
#: L'article 21 alinea 2 fait arreter par l'assemblee DEUX montants sur des
#: objets differents: celui a partir duquel la consultation du conseil syndical
#: est obligatoire, et celui a partir duquel la mise en concurrence l'est. Une
#: relation unique les portait, donc l'ecran opposait deux votes qui ne
#: repondaient pas a la meme question. Voir `_actes_seuils_normes` pour l'axe,
#: le fondement commun et ce qui distingue reellement les deux.
REL_SEUIL_CONSULTATION_CS = "SEUIL_CONSULTATION_CS_APPLICABLE"
REL_SEUIL_CONCURRENCE = "SEUIL_CONCURRENCE_APPLICABLE"
#: Le residu: un montant de seuil est rattache et l'obligation qu'il declenche
#: n'a pas ete identifiee. **La valeur reste `SEUIL_APPLICABLE` a dessein** -
#: c'est ce que portent toutes les lignes deja ecrites, et c'est exactement ce
#: qu'elles disent. La renommer les aurait fait disparaitre de l'ecran sans
#: qu'aucun compteur ne bouge, ce qui est la seule chose que ce lot n'a pas le
#: droit de faire.
REL_SEUIL_NON_ATTRIBUE = "SEUIL_APPLICABLE"
REL_AVIS_CS = "AVIS_CS"
REL_ANNEXE_VISEE = "ANNEXE_VISEE"
REL_DEVIS_RETENU = "DEVIS_RETENU"
#: Ajoutee le 2026-09-04, et c'est une distinction de droit, pas un synonyme de
#: `AVIS_CS`. `AVIS_CS` est la **consultation prealable** que l'article 21 rend
#: obligatoire au-dela d'un montant arrete par l'assemblee: elle porte sur un
#: marche ou un contrat, avant qu'il soit passe. `RAPPORT_CS` est le **compte
#: rendu annuel d'execution de mission** du decret art. 22 al. 2, notifie avec
#: l'ordre du jour (decret art. 11 II 4). Il ne porte sur aucun marche: il porte
#: sur la gestion d'un exercice. Les confondre revient a reprocher a une
#: approbation des comptes de n'avoir pas ete precedee d'une consultation sur un
#: marche qui n'existe pas.
REL_RAPPORT_CS = "RAPPORT_CS"
RELATIONS = (
    REL_FONDE_PAR,
    REL_REND_COMPTE_A,
    REL_RATIFIE_PAR,
    REL_AUTORISE,
    REL_SEUIL_CONSULTATION_CS,
    REL_SEUIL_CONCURRENCE,
    REL_SEUIL_NON_ATTRIBUE,
    REL_AVIS_CS,
    REL_RAPPORT_CS,
    REL_ANNEXE_VISEE,
    REL_DEVIS_RETENU,
)

#: Qui affirme. C'est le champ qui permet a plusieurs assertions concurrentes de
#: coexister sur la MEME paire: le syndic affirme, CoproScope calcule, un humain
#: confirme ou contredit. `object_links` obtient la meme propriete en mettant
#: `event_id` dans sa contrainte UNIQUE; ici c'est `provenance`, parce que ce
#: magasin n'a pas de journal d'evenements.
PROV_SYNDIC = "SYNDIC_AFFIRME"
PROV_CALCUL = "COPROSCOPE_CALCULE"
PROV_CONFIRME = "HUMAIN_CONFIRME"
PROV_CONTREDIT = "HUMAIN_CONTREDIT"
PROVENANCES = (PROV_SYNDIC, PROV_CALCUL, PROV_CONFIRME, PROV_CONTREDIT)

#: Les deux bouts d'un lien. `target_kind` est **polymorphe a dessein**: aucune
#: cle etrangere ne fige la forme de la cible, parce que la forme change d'un
#: syndic a l'autre. Un `DEVIS_RETENU` vise une ligne de `devis_cites` chez le
#: syndic qui cite ses devis dans la convocation, et un `document` chez celui
#: qui les joint en fichiers voisins. Figer la cible aurait rendu le schema
#: correct pour un syndic et faux pour le suivant.
KIND_ACTE = "acte"
KIND_DOSSIER = "dossier"
KIND_DOCUMENT = "document"
KIND_DEVIS_CITE = "devis_cite"
KIND_ASSEMBLEE = "assemblee"
KINDS = (KIND_ACTE, KIND_DOSSIER, KIND_DOCUMENT, KIND_DEVIS_CITE, KIND_ASSEMBLEE)

#: Ou une affirmation a ete lue. Ce vocabulaire remplit `montant_source` et
#: `entreprise_source`.
SOURCE_CORPS = "CORPS_RESOLUTION"
SOURCE_ORDRE_DU_JOUR = "ORDRE_DU_JOUR"
SOURCE_DEVIS_LIE = "DEVIS_LIE"
SOURCE_ANNEXE = "ANNEXE"
SOURCE_ABSENTE = "ABSENT"
#: Le document ecrit un montant, et aucune regle ne sait le lire sans deviner.
#: C'est un troisieme etat, et il ne se confond ni avec `ABSENT` ni avec un
#: nombre. Mesure du 2026-09-04: sans lui, `2.500` devenait 2,50 EUR et
#: `environ 2 000` devenait 0,00 EUR - deux nombres plausibles, affiches avec
#: deux decimales comme s'ils avaient ete lus, et le plafond de l'article 21-2
#: ne se declenchait plus jamais.
SOURCE_ILLISIBLE = "ILLISIBLE"
SOURCES_AFFIRMATION = (
    SOURCE_CORPS, SOURCE_ORDRE_DU_JOUR, SOURCE_DEVIS_LIE, SOURCE_ANNEXE,
    SOURCE_ABSENTE, SOURCE_ILLISIBLE,
)

#: Force probatoire d'un lien. Les trois etats de l'avis du conseil syndical du
#: modele section 8 se projettent exactement sur les trois statuts publics
#: livres cote comptes. On generalise: TOUT lien porte sa force probatoire, donc
#: le statut public d'une cellule de matrice est une **lecture de colonne**,
#: jamais un calcul refait dans chaque vue.
FORCE_PIECE = "PIECE_PRODUITE"      # -> "Source disponible"
FORCE_AFFIRME = "AFFIRME_SANS_PIECE"  # -> "A confirmer"
FORCE_ABSENT = "ABSENT"             # -> "Source manquante"
#: Quatrieme etat, ajoute le 2026-09-04. Il ne dit pas qu'une source manque: il
#: dit que **la question ne se pose pas ici**. `ABSENT` sur la cellule seuil
#: d'une election de conseil syndical etait un mensonge poli - il annoncait une
#: piece manquante la ou aucune piece n'etait due. Les deux etats se lisent tres
#: differemment dans une file de travail: l'un appelle une diligence, l'autre la
#: retire. Voir `HORS_CONTROLE` pour le motif, qui se lit toujours a cote.
FORCE_NON_APPLICABLE = "NON_APPLICABLE"  # -> "Ne s'applique pas"
FORCES = (FORCE_PIECE, FORCE_AFFIRME, FORCE_ABSENT, FORCE_NON_APPLICABLE)

#: Regle dure du modele section 8: un `AFFIRME_SANS_PIECE` ne franchit jamais la
#: frontiere vers une sortie destinee a un tiers en tant que preuve. La regle
#: est **derivee**, donc jamais stockee: une colonne `diffusable` pourrait etre
#: mise a vrai par erreur, un predicat non.
def diffusable(force_probatoire: str) -> bool:
    """Ce lien peut-il servir de preuve dans une sortie destinee a un tiers."""
    return force_probatoire == FORCE_PIECE


ORIGINE_EXTRAIT = "EXTRAIT"
ORIGINE_CORRIGE = "CORRIGE_HUMAIN"

#: Aiguillage des articles 44 et 45 du decret. Le test lui-meme n'est pas de ce
#: lot (trou T4); ce qui est de ce lot, c'est que sa reponse ait ou se ranger
#: sans reecrire la table le jour ou elle existera.
IMPUTATION_BUDGET = "BUDGET_PREVISIONNEL"
IMPUTATION_VOTE_SEPARE = "VOTE_SEPARE"
IMPUTATION_FONDS_TRAVAUX = "FONDS_TRAVAUX"
IMPUTATION_INDETERMINEE = "INDETERMINE"

#: La liste fermee, pour que les quatre valeurs soient verifiables ensemble.
#: Quatre constantes sans liste ne se comparent a rien: rien n'empeche une
#: cinquieme d'apparaitre dans une vue sans etre declaree ici.
IMPUTATIONS = (
    IMPUTATION_BUDGET,
    IMPUTATION_VOTE_SEPARE,
    IMPUTATION_FONDS_TRAVAUX,
    IMPUTATION_INDETERMINEE,
)


# --------------------------------------------------------------------------
# L'issue d'une resolution - six etats, aucun n'est NULL
# --------------------------------------------------------------------------

#: Etalon du proces-verbal du 03/07/2024, etabli a la main sur la source
#: primaire: 55 resolutions, 39 adoptees, 7 rejetees, 8 portant `Pas de vote`,
#: **1 dont le proces-verbal n'enonce jamais l'issue** (resolution 28, budget
#: previsionnel 2024: les trois lignes de vote sont presentes, la phrase de
#: conclusion manque).
#:
#: **`PAS_DE_VOTE` et `VOTE_SANS_FORMULE` ne sont pas le meme etat, et aucun des
#: deux n'est un `NULL`.** Le premier dit que l'assemblee n'a pas vote, et le
#: proces-verbal l'ecrit. Le second dit que l'assemblee a vote et que le document
#: ne dit pas le resultat. Les confondre, ou les laisser tomber dans une colonne
#: nullable, fabriquerait un vote: un outil qui conclurait a l'adoption
#: inventerait un resultat que le proces-verbal ne porte pas.
#:
#: Ce vocabulaire n'est pas invente ici. Il est celui de `_resolutions_motifs`,
#: deja en service sur la voie resolutions, et le reprendre tel quel est
#: l'application directe de la quatrieme decision back: pas de troisieme source
#: de verite - y compris pour les mots.
RESULTAT_ADOPTEE = "ADOPTEE"
RESULTAT_REJETEE = "REJETEE"
RESULTAT_PAS_DE_VOTE = "PAS_DE_VOTE"            # le PV l'ecrit explicitement
RESULTAT_VOTE_SANS_FORMULE = "VOTE_SANS_FORMULE"  # des voix, aucune issue enoncee
RESULTAT_SANS_ISSUE = "SANS_ISSUE_TRACEE"       # ni vote, ni formule, ni mention

#: Le document ENONCE une issue, et la chaine ne sait pas la lire.
#:
#: Sixieme valeur, ajoutee le 2026-09-08. Elle ne dedouble aucune des cinq
#: autres: aucune ne pouvait la porter, et les trois candidats plausibles
#: disaient tous quelque chose de faux.
#:
#: - `SANS_ISSUE_TRACEE` affirme que le document ne dit RIEN. C'est l'exact
#:   contraire du fait constate, et c'est pourtant la valeur que le pont rendait
#:   par defaut: deux etats de la voie resolutions - `ISSUE_NON_RECONNUE` et
#:   `ISSUE_ENONCEE_NON_LUE` - n'etaient pas declares dans sa table de
#:   traduction et retombaient tous les deux ici, sans erreur et sans trace;
#: - `VOTE_SANS_FORMULE` affirme que des voix sont comptees et qu'AUCUNE issue
#:   n'est enoncee. Faux de la meme facon: elle est enoncee, elle n'est pas lue;
#: - `ADOPTEE` ou `REJETEE` fabriqueraient le vote que le document porte et que
#:   personne n'a lu.
#:
#: **Les deux etats amont se traduisent par cette valeur unique, et c'est
#: volontaire.** Ils different par la MANIERE dont la lecture a echoue -
#: vocabulaire de cloture inconnu d'un cote, aucune formule reconnue de l'autre.
#: C'est un fait sur l'extracteur, que la voie resolutions garde et compte
#: separement. Le modele des actes, lui, n'a besoin que du fait sur l'acte, et
#: il est le meme dans les deux cas: rien n'est autorise, rien n'est reproche,
#: la piece existe et demande une relecture humaine.
RESULTAT_ISSUE_NON_LUE = "ISSUE_NON_LUE"
RESULTATS = (
    RESULTAT_ADOPTEE,
    RESULTAT_REJETEE,
    RESULTAT_PAS_DE_VOTE,
    RESULTAT_VOTE_SANS_FORMULE,
    RESULTAT_SANS_ISSUE,
    RESULTAT_ISSUE_NON_LUE,
)

#: Les seules issues qui autorisent une depense. `VOTE_SANS_FORMULE` n'y est pas,
#: et c'est le point: une resolution dont l'issue n'est pas enoncee ne fonde
#: rien, et elle ne produit pas non plus de constat d'inexecution - on ne
#: reproche pas une inexecution a une decision dont on ignore si elle a ete
#: prise.
RESULTATS_AUTORISANTS = (RESULTAT_ADOPTEE,)

#: `1 majorite non enoncee` sur 55, mesure sur la meme source: la resolution 23
#: porte que les coproprietaires ne votent pas, seuls les membres elus du conseil
#: syndical le font, et aucun article n'est cite. C'est un fait constate sur le
#: document, donc une valeur nommee - pas une colonne vide.
MAJORITE_NON_ENONCEE = "NON_ENONCEE"

#: Avec quelle assurance la valeur a ete lue sur la piece. **Trois mots, ceux
#: que l'extracteur ecrit** - `_resolutions_extraction._confiance` ne rend rien
#: d'autre, et le registre reel ne porte rien d'autre: 125 `forte`, 40
#: `moyenne`, 8 `faible` sur 173 lignes.
#:
#: Mesure du 2026-09-04: l'ecran des seuils testait `confiance not in
#: ("haute", "")`. Le mot `haute` n'a aucun producteur dans tout le depot. Les
#: six seuils reels, tous lus `forte`, portaient donc l'avertissement
#: « lu avec une confiance faible, relisez » - et une confiance jamais
#: renseignee, elle, passait pour confirmee. La polarite etait inversee dans
#: les deux sens a la fois, sans qu'aucune erreur ne soit levee.
CONFIANCE_FORTE = "forte"
CONFIANCE_MOYENNE = "moyenne"
CONFIANCE_FAIBLE = "faible"
CONFIANCES = (CONFIANCE_FORTE, CONFIANCE_MOYENNE, CONFIANCE_FAIBLE)


def resultat_valide(valeur: str) -> bool:
    """Une issue doit etre l'une des six, jamais vide.

    Cette fonction existe pour etre appelee par l'extracteur au moment ou il
    ecrit, pas par une vue. Un schema SQLite en colonnes TEXT ne peut pas porter
    la contrainte; la porter en Python au point d'ecriture est ce qui reste, et
    c'est mieux que de ne la porter nulle part.
    """
    return valeur in RESULTATS


# --------------------------------------------------------------------------
# Regime de T.V.A. d'une piece
# --------------------------------------------------------------------------

#: Trois ecarts reels ont ete constates dans les pieces de l'exercice 2025: une
#: T.V.A. extraite a 20 % d'une facture qui porte 10 %, une T.V.A. de 200,00 sur
#: une facture portant `T.V.A. non applicable`, et 3 693,90 de T.V.A. extraits
#: d'une prime d'assurance qui n'en supporte pas.
#:
#: **Un ecart de ce genre se porte comme un constat rattache a une piece, jamais
#: comme une correction silencieuse de la valeur.** Le schema garde donc les deux
#: nombres cote a cote - ce que la comptabilite a retenu, et ce que la piece
#: annonce - et laisse la vue dire qu'ils divergent. Corriger la valeur ferait
#: disparaitre la question a poser au syndic, qui est le livrable.
TVA_NORMAL = "NORMAL"
TVA_NON_APPLICABLE = "NON_APPLICABLE"
TVA_EXONERE = "EXONERE"
TVA_REGIMES = (TVA_NORMAL, TVA_NON_APPLICABLE, TVA_EXONERE)
