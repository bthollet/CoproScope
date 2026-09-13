"""La liste minimale du decret 2019-502, en donnee plutot qu'en prose.

Sert `RM-2026-0091`. Jusqu'au 2026-09-07, les 18 rubriques legales des trois
colleges vivaient uniquement dans `docs/referentiel_conformite_extranet_v1.md`.
Un `git grep` sur l'etat anterieur au lot rend **ZERO** occurrence de
`2019-502`, `EXT-A-`, `EXT-B-`, `EXT-C-` ou `33-1-1` dans les `.py`, `.js`,
`.json` et `.csv`. Le code savait donc dire *"ce qui etait la n'y est plus"* et
pas *"ce qui devrait etre la n'y a jamais ete"*.

*(La premiere version de cette phrase annoncait une occurrence dans un
commentaire. C'etait faux: j'avais mesure sur l'arbre COURANT, qui portait deja
un commentaire ecrit par ce lot meme. Trouve le 2026-09-07 par un sous-agent
charge de me refuter. Le constat de fond en sort renforce, pas affaibli - mais
un chiffre publie doit etre reproductible, et celui-la ne l'etait pas.)*

Le document reste la source. Ce module en est la transcription executable, et
un test verifie que les deux portent les memes identifiants.

======================================================================
Ce qui a rendu ce module necessaire, et qui n'est pas un confort
======================================================================

Brice a nomme trois manques le 2026-09-06: **reglement de copropriete**,
**contrats**, **banque**. Deux des trois etaient inexprimables:

- *banque* n'est pas une rubrique de l'editeur. La cartographie du 2026-09-04
  l'a mesure: les releves du compte separe sont ranges dans **Documents
  divers**, la categorie fourre-tout. Un attendu pose sur le code `DIV`
  melangerait les releves bancaires avec tout le reste;
- *contrats* recouvre **quatre** obligations distinctes qu'un seul code `CON`
  agrege: assurances de l'immeuble, ensemble des contrats et marches en cours,
  contrats d'entretien des equipements communs, et contrat de syndic.

Un compte par rubrique d'editeur ne peut donc pas exprimer ce que l'utilisateur
a demande. C'est le motif du module, et il est mesure.

======================================================================
Les deux axes de generalisation
======================================================================

----------------------------------------------------------------------
Axe 1 - la maniere dont un editeur decoupe la liste legale
----------------------------------------------------------------------

**Valeurs observees.** Chez Coprodirecte: 8 codes d'interface pour 18
obligations. La relation n'est ni injective ni surjective - `CON` porte quatre
obligations, `EXT-C-02` vit dans `DIV`, `REU` n'en porte aucune de la liste
minimale, et le college B vit dans un autre espace.

**Ce qui reste invariant le long de l'axe.** Le droit enumere des
**obligations**; l'editeur enumere des **emplacements**. Les deux ensembles ne
coincident jamais par construction. Ce qui reste vrai: *toute piece observee
occupe exactement un emplacement, et toute obligation est satisfaite par zero,
un ou plusieurs emplacements.* La relation est n-n, et elle **n'est pas
observable dans la page**, parce qu'aucune page ne cite le decret.

**Ce que le code en fait.** Il ne la devine jamais. Il la traite comme une
donnee **absente par defaut**, exactement comme une rubrique jamais ouverte est
`NON_EXPLOREE` et non `ABSENTE`. Le rattachement est **declare par un humain**,
au meme titre que le nombre de pieces attendu. Aucune fonction de ce module ne
lit un code d'editeur en dur.

**Hors des valeurs observees.** Un second editeur avec 23 rubriques, 3
rubriques ou une page fourre-tout arrive sans rattachement: les 18 obligations
ressortent `NON_RATTACHE`, l'ecran dit *aucun rattachement declare pour cet
editeur* et propose de les declarer. **Zero faux manquement, zero reponse
fausse en silence.**

----------------------------------------------------------------------
Axe 2 - l'unite de comptage d'une obligation
----------------------------------------------------------------------

**Valeurs observees.** `EXT-A-08` exige **trois** proces-verbaux, nombre fixe
par le texte. `EXT-B-04` exige les appels de fonds **sur trois annees**, une
duree. `EXT-C-02` exige une **serie mensuelle sans trou**, une continuite.
`EXT-C-05` exige **trois** documents nommes. `EXT-A-01` exige *les* actes
publies - un nombre que seul le coproprietaire connait, et c'est exactement le
cas de Brice: 24 pieces, dont 6 manquent.

**Ce qui reste invariant le long de l'axe.** Une obligation dit toujours **ce
qu'il faut compter**; elle ne dit pas toujours **combien**.

**Ce que le code en fait.** Chaque rubrique porte `attendu_source`. Pour
`TEXTE`, la valeur est pre-remplie et citee avec sa base - on ne laisse pas
saisir cinq proces-verbaux la ou le texte en exige trois. Pour `DECLARE`, le
champ est ouvert, parce que personne d'autre que l'occupant ne sait.

**Hors des valeurs observees.** Une obligation dont l'unite ne rentre dans
aucune des quatre porte `INCONNU`: aucun compte attendu, etat `INDETERMINE`.

======================================================================
Ce que ce module ne fera jamais: conclure
======================================================================

`CONFORME` et `NON_CONFORME` sont **declares et reserves**. Les emettre exige
de **lire la piece**, ce que l'observation ne fait pas: une attestation
d'assurance perimee, un projet de contrat au lieu du contrat signe, un extrait
au lieu du proces-verbal complet occupent la rubrique aussi bien que la bonne
piece. C'est la mise en garde de Brice du 2026-09-06 - *attention au faux
servi* - et c'est `RM-2026-0093`.

Un test verifie qu'aucun producteur ne les ecrit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Les sources, et pourquoi elles portent une date de lecture
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Source:
    """Un article, dans la version qui a ete effectivement lue.

    `VIGUEUR` signifie *en vigueur a la date demandee*, jamais *a jour*: c'est
    precisement pourquoi la date de lecture fait partie de la citation. Meme
    patron que `_budget_previsionnel_sources.Source`, et meme motif: sert
    `RM-2026-0089`.
    """

    cle: str
    texte: str
    article: str
    legiarti: str
    version_debut: str
    lue_le: str

    def citation(self) -> str:
        return (
            f"{self.texte}, {self.article} ({self.legiarti}, "
            f"version du {self.version_debut}, lue le {self.lue_le})"
        )


_LOI = "loi 65-557 du 10 juillet 1965"
_D67 = "decret 67-223 du 17 mars 1967"
_D19 = "decret 2019-502 du 23 mai 2019"
_D70 = "loi 70-9 du 2 janvier 1970"

#: Les textes relus le 2026-09-03 depuis le poste local avec la skill
#: `piste-api`, en lecture seule. La passe a trouve cinq corrections de fond,
#: dont quatre auraient produit des faux manquements et une aurait masque cinq
#: obligations reelles.
SOURCES: dict[str, Source] = {
    "loi.18-I": Source(
        "loi.18-I", _LOI, "article 18 I", "LEGIARTI000049398867",
        "2024-04-11", "2026-09-03",
    ),
    "d67.33-1-1": Source(
        "d67.33-1-1", _D67, "article 33-1-1", "LEGIARTI000038503801",
        "2019-07-01", "2026-09-03",
    ),
    "d19.1": Source(
        "d19.1", _D19, "article 1er", "LEGIARTI000042412719",
        "2020-12-31", "2026-09-03",
    ),
    "d19.2": Source(
        "d19.2", _D19, "article 2", "LEGIARTI000038503795",
        "2019-07-01", "2026-09-03",
    ),
    "d19.3": Source(
        "d19.3", _D19, "article 3", "LEGIARTI000038503789",
        "2019-07-01", "2026-09-03",
    ),
    "loi70.3": Source(
        "loi70.3", _D70, "article 3", "LEGIARTI000006480362",
        "1972-01-01", "2026-09-03",
    ),
}


def source(cle: str) -> Source:
    """La source d'une cle, ou une erreur nommee.

    Un `KeyError` silencieux produirait un controle affiche **sans fondement**,
    ce qui est pire qu'un controle absent: il serait cite devant un syndic.
    """
    try:
        return SOURCES[cle]
    except KeyError:
        raise KeyError(
            f"Source inconnue: {cle!r}. Un controle sans identifiant LEGIARTI "
            f"n'entre pas dans le referentiel. Sources declarees: "
            f"{', '.join(sorted(SOURCES))}."
        ) from None


# ---------------------------------------------------------------------------
# Vocabulaire
# ---------------------------------------------------------------------------

#: Les colleges du decret. `PREALABLE` et `TRANSVERSAL` n'en sont pas: ce sont
#: les controles qui conditionnent ou traversent les trois autres.
COLLEGE_A = "A"
COLLEGE_B = "B"
COLLEGE_C = "C"
PREALABLE = "PREALABLE"
TRANSVERSAL = "TRANSVERSAL"

#: L'unite de comptage d'une obligation - l'axe 2.
ATTENDU_TEXTE = "TEXTE"          # le texte fixe un nombre
ATTENDU_DUREE = "DUREE"          # le texte fixe une periode
ATTENDU_CONTINUITE = "CONTINUITE"  # une serie sans trou
ATTENDU_DECLARE = "DECLARE"      # seul l'occupant sait
#: Le texte fixe un nombre de JUSTIFICATIONS, pas de fichiers - et plusieurs
#: peuvent tenir dans un seul document. Ajoute le 2026-09-07 apres une epreuve
#: sur un second cabinet: chez lui, la carte professionnelle, l'assurance et la
#: garantie financiere de `EXT-C-05` sont trois mentions d'un MEME contrat de
#: syndic. Compter les fichiers y produisait un manquement chiffre a deux, sur
#: un emplacement que le module croyait exclusif - donc sans garde-fou.
ATTENDU_MENTIONS = "MENTIONS"
ATTENDU_INCONNU = "INCONNU"      # hors des cinq: aucun compte attendu

#: Les unites que l'observation ne sait pas compter **du tout**, et qui ne
#: produisent donc jamais d'ecart chiffre.
#:
#: La distinction a ete affinee le 2026-09-07, et c'est un test qui l'a
#: imposee. Avoir range les quatre unites non-`TEXTE` ensemble faisait perdre
#: *banque* - l'un des trois manques que Brice avait nommes: un humain PEUT
#: dire *j'attends douze releves mensuels*, et compter douze fichiers a du
#: sens. Ce que l'observation ne sait pas y faire, c'est verifier l'absence de
#: TROU dans la serie - ce qui est une reserve a afficher, pas une raison de
#: refuser le compte.
#:
#: Restent vraiment non comptables:
#: - `MENTIONS`, parce que plusieurs justifications tiennent dans un seul
#:   document, et compter les fichiers mesure alors autre chose;
#: - `INCONNU`, qui est par definition hors de l'axe.
ATTENDUS_NON_COMPTABLES = (ATTENDU_MENTIONS, ATTENDU_INCONNU)

#: Les unites dont le compte est possible mais **incomplet**: il dit combien de
#: pieces, il ne dit pas si la periode est couverte ni si la serie est continue.
#: La reserve voyage avec l'etat.
ATTENDUS_AVEC_RESERVE = {
    ATTENDU_DUREE: "le compte ne verifie pas que la periode exigee est couverte",
    ATTENDU_CONTINUITE: "le compte ne verifie pas que la serie est sans trou",
}

#: Ce qu'une **observation** sait rendre.
SERVI_EN_APPARENCE = "SERVI_EN_APPARENCE"
NON_SERVI = "NON_SERVI"
NON_RATTACHE = "NON_RATTACHE"
NON_PARCOURUE = "NON_PARCOURUE"
SANS_OBJET = "SANS_OBJET"
INDETERMINE = "INDETERMINE"

#: Ce qu'elle ne sait pas rendre, et ne saura pas. Declares ici pour que le
#: vocabulaire soit complet et que la reserve soit ecrite, jamais produits.
#: Les emettre exige de lire la piece: c'est `RM-2026-0093`.
CONFORME = "CONFORME"
NON_CONFORME = "NON_CONFORME"

#: Les seuls etats qu'un producteur a le droit d'ecrire. Un test scanne les
#: producteurs et le verifie.
ETATS_OBSERVABLES = (
    SERVI_EN_APPARENCE,
    NON_SERVI,
    NON_RATTACHE,
    NON_PARCOURUE,
    SANS_OBJET,
    INDETERMINE,
)
ETATS_RESERVES = (CONFORME, NON_CONFORME)


# ---------------------------------------------------------------------------
# Les rubriques
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Rubrique:
    """Une obligation du referentiel, avec son fondement et son unite."""

    identifiant: str
    college: str
    intitule: str
    critere_presence: str
    #: Ce qui distingue une piece servie d'une piece valable. Jamais evalue par
    #: l'observation: c'est le texte a montrer a cote du compte, pour que le
    #: lecteur sache ce qui reste a verifier a la main.
    critere_complementaire: str
    source: str
    attendu_source: str = ATTENDU_DECLARE
    #: Le nombre fixe par le texte, quand il y en a un. Sinon `None`.
    attendu: int | None = None
    #: Les autres obligations avec lesquelles celle-ci se recouvre. Sans cette
    #: donnee, une seule piece absente compterait plusieurs manquements.
    recouvre: tuple[str, ...] = field(default_factory=tuple)
    #: La condition d'application, quand le texte en pose une. Vide veut dire
    #: *toujours due*. Ajoute le 2026-09-07: sans ce champ, une copropriete sans
    #: fonds de travaux et sans compte separe recoltait deux manquements rouges
    #: **contre un syndic irreprochable** - exactement ce que la doctrine du lot
    #: interdit, et pour une raison que le texte lui-meme donne.
    condition: str = ""
    #: **Le contenu de cette rubrique ne se capture jamais.** Ajoute le
    #: 2026-09-07 apres une verification adverse: l'interdiction n'existait
    #: qu'en prose, et le lecteur aurait conserve en clair l'etat civil des
    #: coproprietaires, plus douze passages d'historique. Une interdiction que
    #: seul un humain peut lire n'est pas une garde.
    contenu_interdit: bool = False

    def citation(self) -> str:
        return source(self.source).citation()


def _r(*args, **kwargs) -> Rubrique:
    return Rubrique(*args, **kwargs)


#: Etape 0 - ce qui conditionne tout le reste.
#:
#: `EXT-002` et `EXT-003` sont les deux facteurs de confusion a ecarter avant
#: de conclure quoi que ce soit: le texte reserve l'obligation au syndic
#: professionnel et la soumet a une dispense votable a la majorite de l'article
#: 25. Ni l'un ni l'autre ne s'observe sur l'extranet.
PREALABLES: tuple[Rubrique, ...] = (
    _r("EXT-000", PREALABLE,
       "Un espace en ligne securise existe et est accessible au compte",
       "Connexion aboutie, arborescence lisible.",
       "Manquement de premier rang: le reste devient sans objet.",
       "loi.18-I", ATTENDU_INCONNU),
    _r("EXT-001", PREALABLE,
       "Un espace distinct est servi au conseil syndical",
       "Zone dont le contenu depasse le college tous coproprietaires.",
       "Indeterminable depuis un seul compte: exige de comparer avec un compte "
       "hors conseil syndical.",
       "d19.3", ATTENDU_INCONNU),
    _r("EXT-002", PREALABLE,
       "Aucune resolution d'assemblee ne dispense le syndic de l'espace en ligne",
       "Lecture des proces-verbaux.",
       "Dispense votable a la majorite de l'article 25. Si votee, tout le "
       "referentiel bascule en SANS_OBJET.",
       "loi.18-I", ATTENDU_INCONNU),
    _r("EXT-003", PREALABLE,
       "Le syndic est un syndic professionnel",
       "Contrat de syndic, carte professionnelle.",
       "Si syndic benevole ou cooperatif, l'obligation ne s'applique pas.",
       "loi.18-I", ATTENDU_INCONNU),
)

#: Criteres transversaux - ils s'appliquent a **toute** rubrique des trois
#: colleges. `EXT-X-02` est le controle le plus rentable du dispositif: binaire,
#: observable en une interaction, sans interpretation.
TRANSVERSAUX: tuple[Rubrique, ...] = (
    _r("EXT-X-01", TRANSVERSAL,
       "Acces par code personnel securise, identification fiable",
       "Presence d'une authentification personnelle.",
       "Le texte exige que le code garantisse la fiabilite de l'identification "
       "des coproprietaires.",
       "d67.33-1-1", ATTENDU_INCONNU),
    _r("EXT-X-02", TRANSVERSAL,
       "Documents telechargeables et imprimables",
       "Un document consulte peut etre telecharge et imprime.",
       "Un extranet qui affiche sans laisser telecharger est un cas frequent, "
       "et c'est un manquement au texte.",
       "d67.33-1-1", ATTENDU_INCONNU),
    _r("EXT-X-03", TRANSVERSAL,
       "Actualisation au moins annuelle, dans les trois mois suivant "
       "l'assemblee annuelle des comptes",
       "Millesime le plus recent coherent avec la derniere assemblee des comptes.",
       "Regle unique d'actualisation, et non une regle de fraicheur par "
       "document. Mesurable seulement par observation repetee.",
       "d67.33-1-1", ATTENDU_INCONNU),
)

#: College A - accessible a tous les coproprietaires. Neuf rubriques, dans
#: l'ordre du texte.
COLLEGE_A_RUBRIQUES: tuple[Rubrique, ...] = (
    _r("EXT-A-01", COLLEGE_A,
       "Reglement de copropriete, etat descriptif de division et actes les modifiant",
       "Documents servis et ouvrables.",
       "Uniquement s'ils ont ete publies: la condition de publication ecarte "
       "les actes non publies, qui ne sont pas dus.",
       "d19.1", ATTENDU_DECLARE, None, (),
       "seuls les actes PUBLIES sont dus"),
    _r("EXT-A-02", COLLEGE_A,
       "Derniere fiche synthetique de la copropriete",
       "Document servi.",
       "Millesime coherent avec la mise a jour annuelle de l'article 8-2.",
       "d19.1", ATTENDU_TEXTE, 1),
    _r("EXT-A-03", COLLEGE_A,
       "Carnet d'entretien de l'immeuble",
       "Document servi.",
       "Derniere mise a jour datee.",
       "d19.1", ATTENDU_TEXTE, 1),
    _r("EXT-A-04", COLLEGE_A,
       "Diagnostics techniques des parties communes",
       "Chaque diagnostic applicable servi.",
       "En cours de validite: le texte ne vise que ceux-la. Le nombre depend "
       "des equipements de l'immeuble.",
       "d19.1", ATTENDU_DECLARE, None, (),
       "seuls les diagnostics APPLICABLES a cet immeuble sont dus"),
    _r("EXT-A-05", COLLEGE_A,
       "Contrats d'assurance de l'immeuble conclus par le syndic",
       "Documents servis.",
       "En cours de validite. Une attestation echue ne satisfait pas le texte, "
       "et occupe pourtant la rubrique.",
       "d19.1", ATTENDU_DECLARE),
    _r("EXT-A-06", COLLEGE_A,
       "Ensemble des contrats et marches en cours signes par le syndic",
       "Liste servie et documents ouvrables.",
       "Se recouvre avec les contrats d'entretien: un contrat d'entretien est "
       "aussi un contrat en cours.",
       "d19.1", ATTENDU_DECLARE, None, ("EXT-A-07",)),
    _r("EXT-A-07", COLLEGE_A,
       "Contrats d'entretien et de maintenance des equipements communs en cours",
       "Liste servie et documents ouvrables.",
       "Rapprochement possible avec les charges. Se recouvre avec l'ensemble "
       "des contrats en cours.",
       "d19.1", ATTENDU_DECLARE, None, ("EXT-A-06",)),
    _r("EXT-A-08", COLLEGE_A,
       "Proces-verbaux des trois dernieres assemblees generales annuelles "
       "appelees a connaitre des comptes",
       "Trois proces-verbaux servis.",
       "L'unite est l'assemblee appelee a connaitre des comptes, pas "
       "l'exercice ni l'assemblee. Deux assemblees dans l'annee dont une seule "
       "sur les comptes n'en comptent qu'une.",
       "d19.1", ATTENDU_TEXTE, 3),
    _r("EXT-A-09", COLLEGE_A,
       "Contrat de syndic en cours",
       "Document servi.",
       "Periode de mandat couvrant la date d'observation.",
       "d19.1", ATTENDU_TEXTE, 1),
)

#: College B - propre a chaque coproprietaire. Vit chez l'editeur observe dans
#: un espace different du college A: un passage sur l'un ne dit rien de l'autre.
COLLEGE_B_RUBRIQUES: tuple[Rubrique, ...] = (
    _r("EXT-B-01", COLLEGE_B,
       "Compte individuel du coproprietaire",
       "Situation de compte servie.",
       "Arrete apres approbation des comptes par l'assemblee annuelle, et non "
       "a jour du dernier appel.",
       "d19.2", ATTENDU_TEXTE, 1),
    _r("EXT-B-02", COLLEGE_B,
       "Charges courantes et hors budget previsionnel des deux derniers "
       "exercices clos, payees par le coproprietaire",
       "Montants servis pour deux exercices.",
       "Le texte vise ce qui a ete paye, pas ce qui a ete appele. Deux "
       "exercices peuvent tenir sur une meme page: l'unite est l'exercice, pas "
       "le fichier.",
       "d19.2", ATTENDU_MENTIONS, 2),
    _r("EXT-B-03", COLLEGE_B,
       "Part du fonds de travaux rattachee au lot",
       "Montant servi.",
       "Du seulement si le syndicat dispose d'un fonds de travaux.",
       "d19.2", ATTENDU_TEXTE, 1, (),
       "du seulement si le syndicat dispose d'un fonds de travaux"),
    _r("EXT-B-04", COLLEGE_B,
       "Avis d'appel de fonds",
       "Documents servis.",
       "Sur les trois dernieres annees: duree fixee par le texte.",
       "d19.2", ATTENDU_DUREE),
)

#: College C - reserve aux membres du conseil syndical. Le texte le rattache
#: expressement aux missions d'assistance et de controle de l'article 21.
COLLEGE_C_RUBRIQUES: tuple[Rubrique, ...] = (
    _r("EXT-C-01", COLLEGE_C,
       "Balances generales des comptes du syndicat, et releve general des "
       "charges et produits de l'exercice echu",
       "Balance servie, et releve general servi.",
       "Deux membres, et non un seul: le releve general est le second, oublie "
       "par la premiere version du referentiel. Rien n'oblige a deux fichiers "
       "distincts.",
       "d19.3", ATTENDU_MENTIONS, 2),
    _r("EXT-C-02", COLLEGE_C,
       "Releves periodiques des comptes bancaires separes",
       "Releves servis, serie sans trou.",
       "Le cas echeant: une absence de compte separe est a ecarter avant de "
       "conclure. Chez l'editeur observe, ces releves sont ranges dans la "
       "categorie fourre-tout, donc introuvables par le nom de la rubrique.",
       "d19.3", ATTENDU_CONTINUITE, None, (),
       "du seulement si la copropriete a un compte bancaire separe"),
    _r("EXT-C-03", COLLEGE_C,
       "Assignations en justice en cours, et decisions de justice dont les "
       "delais de recours n'ont pas expire",
       "Documents servis.",
       "Seule rubrique qui revele un contentieux en cours. A fort enjeu pour "
       "un conseil syndical.",
       "d19.3", ATTENDU_DECLARE),
    _r("EXT-C-04", COLLEGE_C,
       "Liste de tous les coproprietaires",
       "Liste servie: presence ou absence, jamais le contenu.",
       "Contient etat civil, domicile et adresse electronique de chaque "
       "coproprietaire. A constater comme presente ou absente; son contenu ne "
       "se capture jamais. Sa completude se verifie ailleurs, apres "
       "pseudonymisation, par recoupement d'alias - RM-2026-0095.",
       # Les champs sont NOMMES ici, et pas positionnels. L'insertion du champ
       # `condition` le 2026-09-07 avait decale le `True` de `contenu_interdit`
       # vers `condition`, **desarmant le biffage en silence** - et aucun test
       # ne l'a vu, parce qu'ils passaient tous par `CONTENU_INTERDIT`, qui
       # etait devenu vide. Une garde qui se desarme sans bruit est exactement
       # le defaut que ce lot passe sa nuit a corriger ailleurs.
       "d19.3", ATTENDU_TEXTE, 1, (),
       condition="", contenu_interdit=True),
    _r("EXT-C-05", COLLEGE_C,
       "Carte professionnelle du syndic, attestation d'assurance "
       "responsabilite civile professionnelle, attestation de garantie financiere",
       "Trois justifications servies - eventuellement portees par un seul "
       "document.",
       "En cours de validite. Mesure du 2026-09-07 sur un second cabinet: les "
       "trois y sont trois MENTIONS en tete du contrat de syndic, pas trois "
       "fichiers. Compter les fichiers produisait un manquement imaginaire.",
       "loi70.3", ATTENDU_MENTIONS, 3),
)

#: Les 18 obligations de la liste minimale, plus les prealables et les
#: transversaux. L'ordre suit le texte.
RUBRIQUES: tuple[Rubrique, ...] = (
    PREALABLES
    + TRANSVERSAUX
    + COLLEGE_A_RUBRIQUES
    + COLLEGE_B_RUBRIQUES
    + COLLEGE_C_RUBRIQUES
)

#: La liste minimale seule - ce que le decret 2019-502 enumere.
LISTE_MINIMALE: tuple[Rubrique, ...] = (
    COLLEGE_A_RUBRIQUES + COLLEGE_B_RUBRIQUES + COLLEGE_C_RUBRIQUES
)

_PAR_IDENTIFIANT: dict[str, Rubrique] = {r.identifiant: r for r in RUBRIQUES}


def rubrique(identifiant: str) -> Rubrique:
    """La rubrique d'un identifiant, ou une erreur nommee."""
    try:
        return _PAR_IDENTIFIANT[identifiant]
    except KeyError:
        raise KeyError(
            f"Rubrique inconnue: {identifiant!r}. Le referentiel porte "
            f"{len(RUBRIQUES)} entrees, dont {len(LISTE_MINIMALE)} obligations."
        ) from None


def par_college(college: str) -> tuple[Rubrique, ...]:
    return tuple(r for r in RUBRIQUES if r.college == college)


#: Les obligations dont le contenu ne doit jamais etre releve. La liste est
#: DECLAREE ici, pas devinee dans le lecteur: une interdiction dispersee dans
#: le code de lecture se perd au premier refactor.
#: Les obligations que le texte conditionne. Une observation ne peut pas savoir
#: si la condition est remplie: seul l'occupant le sait.
CONDITIONNELLES: tuple[str, ...] = tuple(
    r.identifiant for r in RUBRIQUES if r.condition
)

CONTENU_INTERDIT: tuple[str, ...] = tuple(
    r.identifiant for r in RUBRIQUES if r.contenu_interdit
)


def dedupliquer(identifiants: set[str]) -> set[str]:
    """Retire d'un ensemble de manques ceux qui doublonnent un recouvrement.

    Le referentiel l'exige explicitement: `EXT-A-06` et `EXT-A-07` se
    recouvrent, un contrat d'entretien etant aussi un contrat en cours. Sans
    cette passe, une seule piece absente compterait **deux** manquements - et
    un compte de manquements gonfle detruit la credibilite de celui qui s'en
    sert devant un syndic, ce qui est exactement l'inverse du but.

    On garde le premier de chaque groupe dans l'ordre du texte, parce que
    l'ordre du texte est le seul ordre qui ne depende pas de nous.
    """
    garde: set[str] = set()
    for candidat in RUBRIQUES:
        if candidat.identifiant not in identifiants:
            continue
        if any(autre in garde for autre in candidat.recouvre):
            continue
        garde.add(candidat.identifiant)
    return garde
