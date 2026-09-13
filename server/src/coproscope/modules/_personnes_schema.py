from __future__ import annotations


"""Le schema de la base des personnes, des lots et de leurs rattachements.

**Pourquoi une base, alors qu'un annuaire existe deja.** `annuaire_personnes.csv`
porte un nom, un prenom, un alias et un numero de compte. Il ne porte ni lot, ni
tantieme, ni date, ni la moindre relation entre deux entites. Or le droit de la
copropriete en impose au moins trois:

- **l'indivision**: plusieurs personnes sur un meme lot, avec des quotes-parts;
- **le demembrement**: usufruitier et nu-proprietaire sur un meme lot;
- **la detention indirecte**: une SCI detient le lot, et son gerant est une
  personne physique nommee ailleurs dans le corpus.

**Ce qui porte les droits n'est pas la personne, c'est le LOT.** Les tantiemes
sont attaches au lot; la personne s'y rattache par un droit, et ce droit est
date - l'assemblee de 2019 concerne le proprietaire de 2019.

**Ce que la base debloque au-dela du masquage.** L'article 25 n'est aujourd'hui
pas calculable: `_pont_actes_lignes` rend `ASSIETTE_INDETERMINEE` faute de
connaitre le total des voix du syndicat. Ce total vient des tantiemes, donc de
cette base.

**Un choix a assumer, pas a contourner.** Le depot refuse deliberement de
stocker les noms de coproprietaires dans le magasin de gouvernance -
`_pont_actes_source` dit qu'une colonne `texte` "les aurait aspires sans
qu'aucun ecran ne le demande". Cette base inverse ce choix, et le motif est
ecrit: ce n'est plus une aspiration accidentelle au detour d'un extrait, c'est
un objet demande, dont chaque ligne est justifiee par un document, et qui vit
dans le coffre local sous le meme plafond de diffusion que l'annuaire.

**Ou ca vit.** Dans `gouvernance.sqlite3`, le magasin dedie qui n'est PAS
reconstruit. La base de reconstruction voit ses 24 tables droppees a chaque
rebuild: une table de personnes ajoutee la-bas serait effacee, et la perte
serait differee donc invisible.
"""


#: Le traitement de masquage se decide PAR ENTITE, jamais par nature juridique.
#: `physique ou morale` n'est pas l'axe: une SARL fournisseur ne doit pas etre
#: masquee - la masquer detruit l'analyse de mise en concurrence -, une SCI qui
#: porte deux patronymes doit l'etre, et une entreprise individuelle EST une
#: personne physique. L'axe est: ce nom permet-il de remonter a une personne
#: physique identifiable.
MASQUER = "MASQUER"
PRESERVER = "PRESERVER"
MASQUAGE_A_DECIDER = "A_DECIDER"
MASQUAGES = (MASQUER, PRESERVER, MASQUAGE_A_DECIDER)

NATURE_PHYSIQUE = "physique"
NATURE_MORALE = "morale"
NATURES = (NATURE_PHYSIQUE, NATURE_MORALE)

#: Les droits qu'une personne peut detenir sur un lot. Liste fermee: une valeur
#: nouvelle est un arbitrage juridique, pas une commodite d'appel.
DROIT_PLEINE_PROPRIETE = "pleine_propriete"
DROIT_INDIVISION = "indivision"
DROIT_USUFRUIT = "usufruit"
DROIT_NUE_PROPRIETE = "nue_propriete"
DROITS = (DROIT_PLEINE_PROPRIETE, DROIT_INDIVISION, DROIT_USUFRUIT, DROIT_NUE_PROPRIETE)

#: Les relations entre entites. `nom_commercial` couvre le cas mesure au corpus:
#: `T Services` est le nom commercial de l'entreprise individuelle `Tanore`, et
#: les deux graphies apparaissent.
RELATIONS_PERSONNES = ("nom_commercial", "gerant", "associe", "representant", "indivision")

#: Seuls deux gestes creent une entite. Une detection generique n'en cree
#: JAMAIS: elle cree un candidat, que seul un humain promeut. Aujourd'hui elle
#: en cree une, definitive et sans chemin de suppression, que le caviardage
#: propage ensuite a tout le corpus - un faux positif devient une regle.
SOURCE_LISTE = "LISTE_NOMINATIVE"
SOURCE_HUMAINE = "SAISIE_HUMAINE"
SOURCES_ENTITE = (SOURCE_LISTE, SOURCE_HUMAINE)

#: Etats d'un candidat en quarantaine.
CANDIDAT_EN_ATTENTE = "EN_ATTENTE"
CANDIDAT_RATTACHE = "RATTACHE"
CANDIDAT_CREE = "CREE"
CANDIDAT_EXCLU = "EXCLU"
CANDIDAT_ETATS = (CANDIDAT_EN_ATTENTE, CANDIDAT_RATTACHE, CANDIDAT_CREE, CANDIDAT_EXCLU)


TABLE_PERSONNES = "personnes"
PERSONNE_FIELDS = (
    "personne_id",
    "doc_id",            # exige par gouvernance_store: piece qui porte l'assertion
    "origine",           # exige: protege les lignes CORRIGE_HUMAIN du remplacement
    "nature",
    "alias",
    "racine",
    "nom_normalise",
    "prenom_normalise",
    "nom_source",
    "prenom_source",
    "masquage",
    "compte",
    "source",
    "vu_le",
)
PERSONNE_CLES = ("personne_id", "origine")
PERSONNE_ORDRE = "nom_normalise, prenom_normalise"


TABLE_LOTS = "lots_copropriete"
LOT_FIELDS = (
    "lot_id",
    "doc_id",
    "origine",
    "reference",
    "cle_repartition",   # `generale`, ou le libelle de la cle speciale
    "tantiemes",
    "base_tantiemes",    # 10 000, 100 000... la base sur laquelle la cle compte
    "vu_le",
)
#: La cle entre dans la cle primaire: un meme lot porte des tantiemes
#: DIFFERENTS selon la cle de repartition. Les tantiemes generaux et ceux d'une
#: cle speciale ne sont pas deux facons d'ecrire la meme chose.
LOT_CLES = ("lot_id", "cle_repartition", "origine")
LOT_ORDRE = "reference, cle_repartition"


TABLE_RATTACHEMENTS = "rattachements_lot"
RATTACHEMENT_FIELDS = (
    "rattachement_id",
    "doc_id",
    "origine",
    "personne_id",
    "lot_id",
    "droit",
    "quote_part",        # pour une indivision; vide sinon
    "date_piece",        # date du DOCUMENT, jamais date de saisie
    "source",
    "vu_le",
)
RATTACHEMENT_CLES = ("rattachement_id", "origine")
RATTACHEMENT_ORDRE = "date_piece DESC, lot_id"


TABLE_LIENS_PERSONNES = "liens_personnes"
LIEN_PERSONNE_FIELDS = (
    "lien_id",
    "doc_id",
    "origine",
    "personne_source",
    "relation",
    "personne_cible",
    "date_piece",
    "vu_le",
)
LIEN_PERSONNE_CLES = ("lien_id", "origine")
LIEN_PERSONNE_ORDRE = "personne_source, relation"


TABLE_CANDIDATS = "candidats_personnes"
CANDIDAT_FIELDS = (
    "candidat_id",
    "doc_id",
    "origine",
    "forme",
    "racine_normalisee",
    "occurrences",
    "nb_documents",      # partition primaire de la file, pas cle de tri
    "motif",
    "appariement_propose",
    "etat",
    "personne_id",       # renseigne quand le candidat est rattache ou promu
    "justification",     # obligatoire pour un rejet `pas une personne`
    "vu_le",
)
CANDIDAT_CLES = ("candidat_id", "origine")
CANDIDAT_ORDRE = "CAST(nb_documents AS INTEGER) DESC, CAST(occurrences AS INTEGER) DESC"


TABLES = {
    TABLE_PERSONNES: (PERSONNE_FIELDS, PERSONNE_CLES, PERSONNE_ORDRE),
    TABLE_LOTS: (LOT_FIELDS, LOT_CLES, LOT_ORDRE),
    TABLE_RATTACHEMENTS: (RATTACHEMENT_FIELDS, RATTACHEMENT_CLES, RATTACHEMENT_ORDRE),
    TABLE_LIENS_PERSONNES: (LIEN_PERSONNE_FIELDS, LIEN_PERSONNE_CLES, LIEN_PERSONNE_ORDRE),
    TABLE_CANDIDATS: (CANDIDAT_FIELDS, CANDIDAT_CLES, CANDIDAT_ORDRE),
}
