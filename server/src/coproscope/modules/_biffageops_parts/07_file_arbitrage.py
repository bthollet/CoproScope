from __future__ import annotations


"""La file d'arbitrage: ce que le caviardage n'a pas su masquer.

Extrait de `06_corpus_markdown.py` le 2026-09-07, quand ce fichier a franchi les
600 lignes. La doctrine du depot fait de l'extraction le chantier prioritaire
avant tout ajout, et le decoupage tombe juste: produire un derive et arbitrer ce
qu'il a manque sont deux gestes distincts, faits par deux acteurs differents -
la machine, puis un humain.

**Ce que la mesure du 2026-09-07 a etabli**, `tools/mesure_file_arbitrage.py`,
sur deux corpus de cabinets differents:

- regrouper les formes suspectes par racine ne reduit la file que de 7 % et 9 %.
  La distribution est plate: il faut encore 336 et 665 decisions pour couvrir
  95 % des occurrences. Le groupement n'est pas le levier;
- la partition sur le nombre de DOCUMENTS la reduit de 66 % et 64 %. Une
  personne recurre de piece en piece; un intitule comptable ponctuel non.

**Et c'est une partition, jamais une exclusion.** Une fuite dans une seule piece
reste une fuite: le second lot garde une priorite basse, et le derive dit dans
sa reserve qu'il reste a traiter.
"""


CORPUS_SUSPECT_FIELDS = [
    "doc_id",
    "genere_le",
    "forme",
    "occurrences",
    "motif",
    # Les trois champs qui rendent la file consommable. Mesure du 2026-09-07,
    # `tools/mesure_file_arbitrage.py`: regrouper les formes par racine ne
    # reduit la file que de 7 % et 9 % sur les deux corpus - la distribution est
    # plate. Ce qui la reduit de 66 % et 64 %, c'est la partition sur le nombre
    # de DOCUMENTS: une personne recurre de piece en piece, un intitule
    # comptable ponctuel non.
    "racine_normalisee",
    "nb_documents",
    "appariement_propose",
]


def suspects_residuels(markdown: str) -> dict[str, int]:
    """Ce que le caviardage a pu rater: formes de nom encore en clair.

    Volontairement plus large que la detection: le but est de mesurer le trou,
    pas de le boucher en silence. Beaucoup de ces formes sont des faux positifs
    - une raison sociale, un nom de lieu, un intitule comptable en capitales.
    """

    sans_alias = ALIAS_PATTERN.sub(" ", markdown)
    trouves: dict[str, int] = {}
    for motif in (_MOTIF_SUSPECT_MIXTE, _MOTIF_SUSPECT_MAJ):
        for match in motif.finditer(sans_alias):
            valeur = match.group(0).strip()
            if not _nom_recevable(valeur):
                continue
            trouves[valeur] = trouves.get(valeur, 0) + 1
    return trouves


def racine_de_forme(forme: str) -> str:
    """La cle de regroupement d'une forme: ses tokens normalises, tries.

    **Pourquoi pas `le token le plus long`.** C'etait ma premiere version, et
    elle encodait une hypothese fausse - que le patronyme est plus long que le
    prenom. `VALLIOT Clemence` rendait `CLEMENCE`. Le test l'a attrape.

    Il n'existe pas de moyen fiable de designer le patronyme dans une chaine
    isolee: c'est precisement pour cela que l'annuaire existe. La cle renonce
    donc a le deviner et se contente de ce qui est vrai sans hypothese:
    `DUPONT Jean` et `Jean DUPONT` portent les memes tokens.

    Ce que ca ne groupe pas: `DUPONT J.`, dont le token abrege differe. La
    mesure du 2026-09-07 dit que ce n'est pas grave - le groupement ne reduit la
    file que de 7 a 9 %, il n'est pas le levier. Le levier est la partition sur
    le nombre de documents.
    """

    tokens = [cle for cle in (normalize_identity_key(mot) for mot in forme.split()) if cle]
    return "|".join(sorted(tokens))


def complete_la_file(
    suspects_rows: list[dict[str, str]],
    entrees_annuaire: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Donne a chaque forme suspecte de quoi etre priorisee et proposee.

    **`nb_documents` est la partition PRIMAIRE de la file, pas une cle de tri.**
    Mesure du 2026-09-07 sur les deux corpus: 543 groupes tombent a 182, et 952
    a 346, quand on ne garde d'abord que les formes vues dans au moins deux
    pieces. Le motif n'est pas arbitraire: une personne recurre de piece en
    piece, un intitule comptable ponctuel non.

    **C'est une partition, jamais une exclusion.** Une fuite dans une seule
    piece reste une fuite; le second lot garde sa priorite basse, et le derive
    dit dans sa reserve qu'il reste a traiter.

    `appariement_propose` reste VIDE quand plusieurs entites de l'annuaire
    portent la meme racine: proposer l'une des deux serait trancher entre
    homonymes, ce que la machine ne fait jamais.
    """

    documents_par_racine: dict[str, set[str]] = {}
    for row in suspects_rows:
        racine = row.get("racine_normalisee", "")
        if racine:
            documents_par_racine.setdefault(racine, set()).add(row.get("doc_id", ""))

    entites_par_racine: dict[str, set[str]] = {}
    for entree in entrees_annuaire:
        nom = entree.get("nom_normalise", "")
        alias = entree.get("alias", "")
        if nom and alias:
            entites_par_racine.setdefault(nom, set()).add(alias)

    completees = []
    for row in suspects_rows:
        racine = row.get("racine_normalisee", "")
        # On ne sait pas lequel des tokens est le patronyme - c'est justement ce
        # que l'annuaire sait. On demande donc a l'annuaire: l'un de ces tokens
        # est-il un patronyme connu ?
        aliases: set[str] = set()
        for token in racine.split("|"):
            aliases |= entites_par_racine.get(token, set())
        completees.append(
            {
                **row,
                "nb_documents": str(len(documents_par_racine.get(racine, set()))),
                # Un seul candidat: on propose. Zero ou plusieurs: rien.
                "appariement_propose": next(iter(aliases)) if len(aliases) == 1 else "",
            }
        )
    return completees
