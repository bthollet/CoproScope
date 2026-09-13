"""La typologie des resolutions: ce qui fonde chaque type, et ce qu'il controle.

Separe de `_actes_vocabulaire` parce que ce module ne declare pas un
vocabulaire, il declare une **regle**: quels controles ont un objet sur quel
type d'acte, et pour quel motif de droit ils n'en ont pas. Le vocabulaire dit
quelles valeurs une colonne a le droit de prendre; ici on dit ce qu'on a le
droit d'en conclure.

Le defaut corrige a ete vu par Brice sur la maquette du 2026-09-03: les 55
resolutions d'une assemblee arrivaient sur le meme plan, et les controles de
seuil et d'avis du conseil syndical etaient appliques a toutes - y compris aux
vingt-deux designations, qui ne passent aucun marche. Un constat faux ne se
contente pas d'etre faux: il noie les vrais, et la file de travail cesse d'etre
lue.

La dependance va dans un seul sens: ce module lit `_actes_vocabulaire`, jamais
l'inverse.
"""

from __future__ import annotations

from ._actes_vocabulaire import (
    PORTEE_APPROBATION_COMPTES,
    PORTEE_AUTORISATION_COPROPRIETAIRE,
    PORTEE_BUDGET,
    PORTEE_DELEGATION_CS,
    PORTEE_DESIGNATION_ORGANE,
    PORTEE_DESIGNATION_SYNDIC,
    PORTEE_ENGAGEMENT_DEPENSE,
    PORTEE_FONDS_TRAVAUX,
    PORTEE_MODALITES,
    PORTEE_ORDINAIRE,
    PORTEE_SEUIL,
    PORTEES,
    REL_ANNEXE_VISEE,
    REL_AVIS_CS,
    REL_DEVIS_RETENU,
    REL_RAPPORT_CS,
    REL_SEUIL_NON_ATTRIBUE,
)

# --------------------------------------------------------------------------
# Le fondement legal de chaque portee
# --------------------------------------------------------------------------

#: portee -> (ce qui la definit, ((article, identifiant Legifrance), ...)).
#:
#: **Ce que definit une portee est ce que la LOI exige d'elle, jamais la maniere
#: dont un syndic l'ecrit.** La regle a ete posee par Brice le 2026-09-04 et
#: elle se verifie ici: deux cabinets du corpus ecrivent `Election du syndic` et
#: `Designation du syndic`. Le verbe est une modalite de cabinet; la fonction -
#: le syndic - est nommee par l'article 25 c, donc les deux cabinets doivent
#: l'ecrire. On type sur la fonction et sur l'objet nommes par le texte, pas sur
#: le verbe employe pour les annoncer.
#:
#: Les identifiants sont ceux des versions en vigueur au 2026-09-03, relevees
#: sur Legifrance ce jour-la. Une regle de majorite ou un regime special ne se
#: cite pas de memoire.
FONDEMENT_PORTEE: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
    PORTEE_DESIGNATION_SYNDIC: (
        "designe la personne qui represente legalement le syndicat",
        (("loi 65-557 art. 25 c", "LEGIARTI000051749507"),
         ("decret 67-223 art. 11 I 4 - projet de contrat joint",
          "LEGIARTI000053191281")),
    ),
    PORTEE_DESIGNATION_ORGANE: (
        "designe une personne a une fonction du syndicat autre que le syndic: "
        "membres et president du conseil syndical, bureau de l'assemblee, "
        "representant du syndicat secondaire au conseil du syndicat principal",
        (("loi 65-557 art. 21 - conseil syndical", "LEGIARTI000039313574"),
         ("loi 65-557 art. 25 c - majorite", "LEGIARTI000051749507"),
         ("decret 67-223 art. 15 - bureau de l'assemblee",
          "LEGIARTI000022124075"),
         ("decret 67-223 art. 24 - representant au syndicat principal",
          "LEGIARTI000006488509")),
    ),
    PORTEE_APPROBATION_COMPTES: (
        "porte sur un exercice CLOS: elle arrete des comptes deja executes, "
        "elle n'engage rien",
        (("loi 65-557 art. 24 I", "LEGIARTI000051749514"),
         ("decret 67-223 art. 11 I 1 - etat financier et compte de gestion",
          "LEGIARTI000053191281"),
         ("decret 2005-240 art. 8 - cinq annexes obligatoires",
          "LEGIARTI000006239516")),
    ),
    PORTEE_BUDGET: (
        "vote l'enveloppe des depenses courantes d'un exercice A VENIR; ce vote "
        "vaut autorisation de ces depenses, sans resolution ligne a ligne",
        (("loi 65-557 art. 14-1 I", "LEGIARTI000043977299"),
         ("decret 67-223 art. 11 I 2 - projet de budget joint",
          "LEGIARTI000053191281")),
    ),
    PORTEE_FONDS_TRAVAUX: (
        "alimente le fonds de travaux ou arrete le plan pluriannuel de travaux",
        # Deux objets, donc deux sources. Jusqu'au 2026-09-04 le type n'en
        # citait qu'une, l'article 14-2, dont la premiere phrase porte le plan
        # pluriannuel de travaux et non la cotisation. La moitie du type - le
        # vote de la dotation, qui est ce que les cinq resolutions mesurees du
        # second cabinet libellent - renvoyait donc a autre chose. La cotisation
        # annuelle au fonds de travaux est l'article 14-2-1.
        (("loi 65-557 art. 14-2 - plan pluriannuel de travaux",
          "LEGIARTI000043977289"),
         ("loi 65-557 art. 14-2-1 - cotisation au fonds de travaux",
          "LEGIARTI000043967792")),
    ),
    PORTEE_ENGAGEMENT_DEPENSE: (
        "engage l'argent du syndicat sur un marche, un contrat ou des travaux "
        "non compris dans le budget previsionnel: un montant, un beneficiaire",
        (("loi 65-557 art. 14-1 II - renvoi au decret",
          "LEGIARTI000043977299"),
         ("decret 67-223 art. 44 - liste des depenses hors budget",
          "LEGIARTI000006488761"),
         ("decret 67-223 art. 45 - definition de la maintenance",
          "LEGIARTI000006488770"),
         ("decret 67-223 art. 11 I 3 - conditions essentielles du contrat",
          "LEGIARTI000053191281")),
    ),
    PORTEE_AUTORISATION_COPROPRIETAIRE: (
        "autorise un coproprietaire a faire A SES FRAIS des travaux affectant "
        "les parties communes: le syndicat n'engage aucune depense",
        (("loi 65-557 art. 25 b", "LEGIARTI000051749507"),
         ("loi 65-557 art. 25-1 - passerelle au second vote",
          "LEGIARTI000049398359")),
    ),
    PORTEE_DELEGATION_CS: (
        "delegue au conseil syndical des decisions relevant de l'article 24, "
        "pour deux ans au plus et sous un montant maximum",
        (("loi 65-557 art. 21-1 - conditions et matieres exclues",
          "LEGIARTI000039301559"),
         ("loi 65-557 art. 21-2 - montant maximum", "LEGIARTI000039301561"),
         ("loi 65-557 art. 21-3 - deux ans au plus", "LEGIARTI000039301563"),
         ("loi 65-557 art. 21-5 - compte rendu et rapport",
          "LEGIARTI000039301567")),
    ),
    PORTEE_SEUIL: (
        "arrete le montant des marches et contrats au-dela duquel la "
        "consultation du conseil syndical, ou la mise en concurrence, devient "
        "obligatoire",
        (("loi 65-557 art. 21 al. 2", "LEGIARTI000039313574"),),
    ),
    PORTEE_MODALITES: (
        "regle une modalite d'organisation ou de financement sans engager de "
        "depense propre: appels de fonds, exigibilite, recouvrement, "
        "habilitation a agir en justice, pouvoir d'execution donne au syndic",
        (("loi 65-557 art. 14-1 I al. 2 et 3, et II - exigibilite",
          "LEGIARTI000043977299"),
         ("decret 67-223 art. 35 - les huit fondements d'un appel de fonds",
          "LEGIARTI000053191341"),
         ("decret 67-223 art. 55 - habilitation a agir en justice",
          "LEGIARTI000053191360"),
         ("loi 65-557 art. 24 II h - autorisation permanente police municipale",
          "LEGIARTI000051749514")),
    ),
    PORTEE_ORDINAIRE: (
        "portee non determinee: aucun type n'a ete reconnu, et il n'est pas "
        "suppose. Tous les controles restent appliques - c'est le seul cas ou "
        "l'ecran a le droit de se tromper, et il doit le dire",
        (),
    ),
}


# --------------------------------------------------------------------------
# Quels controles s'appliquent, et lesquels ne s'appliquent pas
# --------------------------------------------------------------------------

#: Les controles que le modele sait poser sur un acte. Sept, pas plus: un
#: controle qui n'a ni cellule ni constat n'existe pas.
#: **Un seul controle pour les trois relations de seuil.** Savoir si un acte est
#: justiciable d'un seuil ne depend pas de la norme: c'est la question *cet acte
#: passe-t-il un marche ou un contrat*, et elle se pose une fois. La valeur est
#: celle de la relation residuelle, donc la chaine `SEUIL_APPLICABLE`, pour que
#: les neuf motifs de `HORS_CONTROLE` deja ecrits gardent leur cle.
#:
#: **Ce que ce choix laisse ouvert, et il est reel.** L'article 21 alinea 2
#: n'exclut le contrat de syndic que de la mise en concurrence: la consultation
#: prealable du conseil syndical, elle, n'a pas cette reserve. Un controle
#: unique retire donc les DEUX normes a une designation de syndic, ce qui est
#: exact pour l'une et faux pour l'autre. Nomme comme residu du lot du
#: 2026-09-08 plutot que corrige a moitie: le corriger demande de scinder aussi
#: le controle, donc de toucher des modules hors du perimetre de ce lot.
CTRL_SEUIL = REL_SEUIL_NON_ATTRIBUE
CTRL_AVIS_CS = REL_AVIS_CS
CTRL_RAPPORT_CS = REL_RAPPORT_CS
CTRL_DEVIS = REL_DEVIS_RETENU
CTRL_ANNEXE = REL_ANNEXE_VISEE
CTRL_EXECUTION = "EXECUTION"
CTRL_MAJORITE = "MAJORITE"
CONTROLES = (
    CTRL_SEUIL,
    CTRL_AVIS_CS,
    CTRL_RAPPORT_CS,
    CTRL_DEVIS,
    CTRL_ANNEXE,
    CTRL_EXECUTION,
    CTRL_MAJORITE,
)

#: portee -> {controle non applicable: pourquoi il ne l'est pas}.
#:
#: **C'est le livrable de ce lot.** Le defaut de l'ecran n'etait pas de manquer
#: des constats, c'etait d'en produire sur des resolutions auxquelles le
#: controle ne s'appliquait pas. Reprocher a une election de conseil syndical de
#: n'avoir pas respecte un seuil de mise en concurrence produit un constat faux,
#: et un constat faux noie les vrais - c'est exactement ce que Brice a vu sur la
#: maquette, ou 55 resolutions arrivaient toutes sur le meme plan.
#:
#: Ce qui n'est PAS liste est applicable. L'inversion est deliberee: elle oblige
#: a ecrire un motif pour chaque retrait, et un retrait sans motif ne passe pas
#: le test qui exige que chaque exclusion cite son fondement.
HORS_CONTROLE: dict[str, dict[str, str]] = {
    PORTEE_DESIGNATION_SYNDIC: {
        # **`CTRL_SEUIL` N'EST PLUS RETIRE ICI, et le motif ecrit le disait
        # deja.** Il visait *le seuil de mise en concurrence* - une seule des
        # deux normes de l'alinea - alors que `CTRL_SEUIL` couvre les TROIS
        # relations de seuil, consultation du conseil syndical comprise. Le
        # retrait etait donc plus large que sa propre justification, et il
        # emportait une obligation que l'article ne retire pas.
        #
        # **C'est le residu sur lequel `RM-2026-0144` a ete refuse a
        # l'integration:** *la separation s'arrete aux relations, elle
        # n'atteint pas le controle qui decide de leur applicabilite*. Le lot
        # avait separe deux normes jusqu'aux relations; le gate d'applicabilite
        # restait a la granularite du CONTROLE, donc la separation ne
        # l'atteignait pas.
        #
        # **Le meme raisonnement avait deja ete tenu ici pour `CTRL_AVIS_CS`,
        # le 2026-09-04** - voir le commentaire ci-dessous, qui cite
        # `LEGIARTI000039313574` et ses deux phrases distinctes. L'exclusion ne
        # porte que sur la seconde. Ce lot applique la meme lecture au seuil.
        #
        # L'exclusion elle-meme n'est pas perdue: elle est declaree par
        # RELATION dans `_actes_seuils_applicabilite.PORTEES_EXCLUES`, ou elle
        # ne vise que la mise en concurrence, et le gate de vue compose les deux
        # granularites. Comparer avec `PORTEE_DESIGNATION_ORGANE` juste en
        # dessous, dont le motif dit explicitement *les deux seuils*: celui-la
        # reste au niveau du controle, parce qu'il y est vrai.
        # CTRL_AVIS_CS n'est PAS retire ici. Le retrait a existe jusqu'au
        # 2026-09-04, au motif que "le contrat de syndic est sorti par le meme
        # alinea" - et l'article cite dit l'inverse. Releve sur Legifrance,
        # LEGIARTI000039313574 porte deux phrases distinctes: l'assemblee
        # "arrete un montant des marches et des contrats a partir duquel la
        # consultation du conseil syndical est rendue obligatoire", puis, "a la
        # meme majorite", un montant "des marches et des contrats AUTRES QUE
        # CELUI DE SYNDIC" pour la mise en concurrence. L'exclusion ne porte que
        # sur la seconde. Le meme article ajoute que le conseil syndical "peut
        # se prononcer, par un avis ecrit, sur tout projet de contrat de
        # syndic".
        # Consequence du retrait, mesuree sur cinq resolutions des deux corpus:
        # l'ecran affichait "Avis du conseil syndical: non exige ici" en
        # renvoyant a l'article qui dit le contraire. Ce n'etait pas un
        # controle en trop, c'etait une question au syndic que le produit
        # empechait de poser, sous une reference legale qui la faisait paraitre
        # reglee.
        CTRL_DEVIS: "une designation ne retient pas un devis",
        CTRL_EXECUTION: (
            "les honoraires du syndic sont une charge du budget previsionnel, "
            "pas une depense rattachee a la resolution qui le designe"
        ),
    },
    PORTEE_DESIGNATION_ORGANE: {
        CTRL_SEUIL: (
            "l'article 21 al. 2 fait porter les deux seuils sur les marches et "
            "les contrats. Une designation de personne n'est ni l'un ni l'autre"
        ),
        CTRL_AVIS_CS: (
            "on ne consulte pas le conseil syndical sur l'election de ses "
            "propres membres"
        ),
        CTRL_DEVIS: "une designation ne retient pas un devis",
        CTRL_ANNEXE: (
            "le decret art. 11 I n'exige de piece de validite que pour la "
            "designation du syndic (4), pas pour les autres fonctions"
        ),
        CTRL_EXECUTION: "une designation n'engage aucun euro",
    },
    PORTEE_APPROBATION_COMPTES: {
        CTRL_SEUIL: (
            "les seuils de l'article 21 al. 2 portent sur des marches et des "
            "contrats a passer. L'approbation des comptes porte sur un exercice "
            "clos: elle n'en passe aucun"
        ),
        CTRL_AVIS_CS: (
            "ce n'est pas la consultation prealable de l'article 21 al. 2 qui "
            "s'y rattache, c'est le compte rendu annuel du conseil syndical - "
            "voir CTRL_RAPPORT_CS, qui lui s'y applique"
        ),
        CTRL_DEVIS: "un exercice clos ne retient pas de devis",
        CTRL_EXECUTION: (
            "les depenses de l'exercice sont deja executees: leur rattachement "
            "se controle piece par piece, pas contre la resolution qui les "
            "arrete"
        ),
    },
    PORTEE_BUDGET: {
        CTRL_SEUIL: (
            "un budget previsionnel n'est ni un marche ni un contrat: "
            "l'article 14-1 I le vote globalement, pour les depenses courantes"
        ),
        CTRL_AVIS_CS: (
            "l'article 18 II fait etablir le budget en concertation avec le "
            "conseil syndical, en amont; ce n'est pas la consultation par seuil "
            "de l'article 21 al. 2"
        ),
        CTRL_DEVIS: "une enveloppe annuelle ne retient pas un devis",
        CTRL_EXECUTION: (
            "une enveloppe ne se rapproche pas d'une depense: elle se compare a "
            "un realise. Exiger une depense rattachee a un budget de 280.000 "
            "EUR produirait un constat a chaque exercice"
        ),
    },
    PORTEE_FONDS_TRAVAUX: {
        CTRL_SEUIL: (
            "une cotisation au fonds de travaux constitue une reserve; elle ne "
            "passe ni marche ni contrat, seuls objets des seuils de l'art. 21 "
            "al. 2"
        ),
        CTRL_AVIS_CS: (
            "aucun marche n'est passe, donc la consultation prealable de "
            "l'art. 21 al. 2 n'a pas d'objet. Le conseil syndical intervient "
            "ici en aval, au titre du controle de gestion"
        ),
        CTRL_DEVIS: "aucun devis n'est retenu par une cotisation",
        CTRL_EXECUTION: (
            "le fonds est une reserve: sa contrepartie est un solde, pas une "
            "depense rattachee"
        ),
    },
    PORTEE_AUTORISATION_COPROPRIETAIRE: {
        CTRL_SEUIL: (
            "l'article 25 b autorise des travaux faits A LEURS FRAIS par "
            "certains coproprietaires. Le syndicat ne passe aucun marche, donc "
            "aucun seuil de l'article 21 n'a d'objet"
        ),
        CTRL_AVIS_CS: (
            "aucun marche du syndicat n'est passe: le coproprietaire contracte "
            "pour son compte, et la consultation de l'art. 21 al. 2 porte sur "
            "les marches du syndicat"
        ),
        CTRL_DEVIS: (
            "le devis, s'il existe, lie le coproprietaire a son entreprise; il "
            "n'engage pas le syndicat"
        ),
        CTRL_EXECUTION: (
            "aucun euro du syndicat n'est engage: exiger une depense rattachee "
            "reviendrait a reprocher au syndicat de n'avoir pas paye ce qu'il "
            "n'a pas a payer"
        ),
    },
    PORTEE_DELEGATION_CS: {
        # Le motif de ce retrait nomme quatre controles de substitution. Il
        # faisait autorite a l'ecran, et jusqu'au 2026-09-04 le premier -
        # `deux ans au plus` - n'existait nulle part: `21-3` n'apparaissait que
        # dans des docstrings, et aucune comparaison de duree n'etait ecrite.
        # Un controle desactive au nom d'un garde-fou inexistant est pire qu'un
        # controle absent. Les constats DELEGATION_TROP_LONGUE et
        # DELEGATION_SANS_PERIODE de `_actes_constats` le rendent effectif.
        CTRL_SEUIL: (
            "la delegation de l'article 21-1 n'est pas un marche. Son controle "
            "propre est ailleurs: deux ans au plus (art. 21-3), montant maximum "
            "(art. 21-2), matieres exclues (art. 21-1 al. 2) et compte rendu "
            "devant l'assemblee votant les comptes (art. 21-5)"
        ),
        CTRL_DEVIS: "une delegation ne retient pas un devis",
        CTRL_EXECUTION: (
            "une delegation ne se consomme pas ligne a ligne mais en cumul sur "
            "sa periode: c'est v_cumul_delegation qui la controle"
        ),
    },
    PORTEE_SEUIL: {
        CTRL_SEUIL: (
            "une resolution qui ARRETE un seuil ne se controle pas contre un "
            "seuil: elle est la source du controle, pas son sujet"
        ),
        CTRL_AVIS_CS: (
            "meme renversement: la resolution qui arrete le montant declenchant "
            "la consultation du conseil syndical n'est pas elle-meme soumise a "
            "cette consultation"
        ),
        CTRL_DEVIS: "un seuil ne retient pas un devis",
        CTRL_EXECUTION: "un seuil n'engage aucune depense; il a une echeance",
    },
    PORTEE_MODALITES: {
        CTRL_SEUIL: (
            "une modalite d'appel de fonds, de recouvrement ou de consultation "
            "des pieces ne passe aucun marche. La depense qu'elle finance a ete "
            "votee par une AUTRE resolution, qui porte le controle"
        ),
        CTRL_AVIS_CS: (
            "la consultation prealable porte sur le marche, donc sur la "
            "resolution qui l'engage, pas sur celle qui en regle l'exigibilite"
        ),
        CTRL_DEVIS: "aucun devis n'est retenu par une modalite",
        CTRL_EXECUTION: (
            "rattacher la depense a la modalite qui l'appelle la compterait "
            "deux fois: une fois sur la resolution qui l'a votee, une fois ici"
        ),
    },
    # PORTEE_ENGAGEMENT_DEPENSE et PORTEE_ORDINAIRE n'ont aucune exclusion
    # ECRITE DANS CETTE TABLE: le premier parce que tous les controles le
    # visent, la seconde parce que ne pas savoir n'est pas une raison de ne pas
    # controler.
    #
    # Ce n'est PAS la meme chose que « aucune exclusion ». La boucle placee
    # juste apres cette table ajoute CTRL_RAPPORT_CS a toute portee absente de
    # RAPPORT_CS_EXIGIBLE, ces deux-la comprises: apres import,
    # HORS_CONTROLE['ORDINAIRE'] vaut {'RAPPORT_CS'}, et celui de
    # l'engagement de depense aussi. La phrase d'avant disait le contraire de
    # ce que la ligne suivante faisait, et le test cense garder l'invariant
    # interrogeait 'PORTEE_INVENTEE' - une valeur que le code n'ecrit jamais -
    # au lieu d'ORDINAIRE, qui est le repli reellement ecrit. L'invariant
    # devenait invérifiable au moment precis ou on voudrait s'y fier.
    #
    # L'invariant exact, tenu par `controle_applicable` et par le test
    # correspondant, est donc: une portee HORS VOCABULAIRE garde ses sept
    # controles; PORTEE_ORDINAIRE, qui est DANS le vocabulaire, en garde six
    # et perd le rapport du conseil syndical, pour la raison ecrite ci-dessous.
}

#: Le rapport annuel du conseil syndical n'est pas exigible partout. Il l'est de
#: l'assemblee qui approuve les comptes (decret art. 22 al. 2, notifie avec
#: l'ordre du jour par decret art. 11 II 4) et de la delegation qui en rend
#: compte (loi art. 21-5). Ailleurs, l'exiger fabriquerait le meme faux constat
#: que le seuil applique a une election.
RAPPORT_CS_EXIGIBLE = (PORTEE_APPROBATION_COMPTES, PORTEE_DELEGATION_CS)

for _portee in PORTEES:
    if _portee not in RAPPORT_CS_EXIGIBLE:
        HORS_CONTROLE.setdefault(_portee, {})[CTRL_RAPPORT_CS] = (
            "le compte rendu annuel du conseil syndical est rattache a "
            "l'assemblee qui approuve les comptes (decret art. 22 al. 2) et a "
            "la delegation qui en rend compte (loi art. 21-5), pas a chaque "
            "resolution"
        )
del _portee


for _portee, _retraits in HORS_CONTROLE.items():
    if _portee not in PORTEES:
        raise ValueError(
            f"HORS_CONTROLE: portee inconnue {_portee!r}. Une portee qui n'est "
            "pas dans le vocabulaire ne sera jamais rencontree, et le retrait "
            "qu'elle porte ne s'appliquerait a rien."
        )
    for _controle in _retraits:
        if _controle not in CONTROLES:
            raise ValueError(
                f"HORS_CONTROLE[{_portee!r}]: controle inconnu {_controle!r}. "
                f"Attendu l'un de {sorted(CONTROLES)}. Un nom errone n'exclut "
                "rien: il laisse le controle s'appliquer partout, en silence."
            )
del _portee, _retraits, _controle


def _exiger_controle(controle: str) -> None:
    """Refuse un nom de controle hors liste, au point d'interrogation.

    Mesure du 2026-09-04: `portees_soumises('AVIS_CS ')` - un espace de trop -
    rendait les 11 portees au lieu de 3, exactement comme un nom inconnu. Le
    controle se rallumait donc partout, ce qui redonne 55 cellules
    « Source manquante » la ou le lot en avait ramene 12, avec l'apparence de
    l'etat corrige. L'inversion « ce qui n'est pas liste s'applique » protege
    de l'oubli d'un motif; elle ne protege pas d'une faute de frappe. C'est
    cette garde-ci qui le fait, et elle parle.
    """
    if controle not in CONTROLES:
        raise ValueError(
            f"Controle inconnu: {controle!r}. Attendu l'un de {sorted(CONTROLES)}. "
            "Un nom hors liste rallumerait le controle sur toutes les portees "
            "sans qu'aucune cellule ne change d'apparence."
        )


def controle_applicable(portee: str, controle: str) -> bool:
    """Ce controle a-t-il un objet sur un acte de cette portee.

    Une portee inconnue rend `True`: on ne desactive pas un controle sur la foi
    d'une valeur qu'on ne sait pas lire. Le doute penche du cote du controle,
    jamais du cote du classement sans suite.

    Un CONTROLE inconnu, lui, leve. La dissymetrie est voulue: une portee vient
    de la donnee lue, un nom de controle vient du code. Le premier peut etre
    surprenant, le second est une faute de frappe.
    """
    _exiger_controle(controle)
    return controle not in HORS_CONTROLE.get(portee, {})


def motif_hors_controle(portee: str, controle: str) -> str:
    """Pourquoi ce controle ne s'applique pas ici. Chaine vide s'il s'applique.

    C'est ce motif qui va a l'ecran a la place du constat retire. Retirer un
    constat sans dire pourquoi serait la meme faute que de l'afficher a tort:
    dans les deux cas l'utilisateur ne peut pas prendre le controle en defaut.

    Un nom de controle hors liste leve plutot que de rendre la chaine vide: un
    blanc se lit « ce controle s'applique », ce qui est la reponse la plus
    rassurante et la moins verifiable.
    """
    _exiger_controle(controle)
    return HORS_CONTROLE.get(portee, {}).get(controle, "")


def portees_soumises(controle: str) -> tuple[str, ...]:
    """Les portees auxquelles ce controle s'applique, dans l'ordre du
    vocabulaire.

    Sert a construire un `IN (...)` de vue: une egalite sur une colonne
    declaree, jamais une recherche de mots dans un texte.

    Le nom du controle est verifie: c'est de cette fonction que sortait la
    liste des 11 portees quand le nom etait mal orthographie.

    **A ne pas utiliser pour borner une vue.** `IN (portees_soumises(...))`
    exclut aussi ce qui n'est dans AUCUNE des deux listes - une portee vide ou
    mal ecrite - donc eteint le controle sur la seule donnee dont on ne sait
    rien. C'est `portees_retirees` qu'il faut, en `NOT IN`.
    """
    _exiger_controle(controle)
    return tuple(p for p in PORTEES if controle_applicable(p, controle))


def portees_retirees(controle: str) -> tuple[str, ...]:
    """Les portees declarees a qui ce controle est retire, motif a l'appui.

    Complement de `portees_soumises` **sur les portees declarees seulement**, et
    c'est toute la difference: une portee hors vocabulaire - le vide compris,
    que `_actes_store` admet explicitement a l'ecriture - n'appartient a
    aucune des deux listes.

    Borner une vue par `portee IN (soumises)` la met donc hors controle sans un
    mot, ce qui est l'inverse exact de ce que `controle_applicable` promet deux
    fonctions plus haut. Mesure du 2026-09-05, deux actes identiques a
    majorite_annoncee='NON_ENONCEE', l'un portee='ORDINAIRE' l'autre portee='':
    `IN (soumises)` en rend un, `NOT IN (retirees)` rend les deux.

    Rendre le doute au controle coute un faux positif lisible; le rendre au
    classement sans suite coute un acte qui disparait de la file en affichant
    « ne s'applique pas », c'est-a-dire rassurant.
    """
    _exiger_controle(controle)
    return tuple(p for p in PORTEES if not controle_applicable(p, controle))
