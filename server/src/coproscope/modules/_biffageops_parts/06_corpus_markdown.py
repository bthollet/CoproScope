from __future__ import annotations


"""Le derive Markdown caviarde, produit pour tout document porteur de texte.

Deux corpus coexistent. D'un cote la piece d'origine, qui circule entre
coproprietaires authentifies. De l'autre ce derive: du Markdown, ou les
identites sont remplacees par des pseudonymes derives d'un sel d'instance, et ou
tout le reste - vocabulaire juridique, montants, dates, numeros d'article,
raisons sociales - est preserve tel quel. C'est le corpus sur lequel un agent
peut travailler sans fuite.

La couverture est universelle: chaque ligne du registre documents recoit soit un
derive, soit une raison nommee de ne pas en avoir. Rien n'est silencieux.

Deux passes. La premiere lit tous les textes et en extrait l'annuaire des
personnes. La seconde caviarde, en commencant par les variantes des personnes
connues, puis en repassant les regles generiques sur ce qui reste.
"""


CORPUS_COVERAGE_FIELDS = [
    "doc_id",
    "file_name",
    "original_path",
    "extension",
    "statut",
    "raison",
    "markdown_path",
    "markdown_sha256",
    "source_sha256",
    "char_count",
    "identites_remplacees",
    "remplacements_annuaire",
    "alias_distincts",
    "categories",
    "suspects_residuels",
    "genere_le",
]


CORPUS_MARKDOWN_EXTENSIONS = TEXT_EXTENSIONS | {"pdf", "docx", "doc", "rtf", "odt"}
CORPUS_TEXTE_BRUT_EXTENSIONS = {"ps1", "py", "sh", "cmd", "bat", "ini", "cfg", "conf", "log", "sql", "xml", "srt"}


def corpus_markdown_enabled(instance: InstanceConfig) -> bool:
    """Le corpus caviarde ne se declenche pas tout seul.

    Tant qu'une instance sert de base de travail a un autre chantier, une
    absorption qui se met soudain a ecrire des derives change le comportement
    observe. On l'active par reglage, instance par instance.
    """

    value = _corpus_settings(instance).get("enabled")
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "vrai", "yes", "oui", "on"}
    return bool(value)


def _corpus_markdown_dir(instance: InstanceConfig) -> Path:
    configured = _corpus_settings(instance).get("output_dir")
    if configured:
        resolved = instance.resolve_path(str(configured))
        if resolved is not None:
            resolved.mkdir(parents=True, exist_ok=True)
            return resolved
    path = _redacted_dir(instance) / "corpus_md"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _corpus_coverage_path(instance: InstanceConfig) -> Path:
    return _privacy_dir(instance) / "corpus_caviarde_couverture.csv"


def _corpus_suspects_path(instance: InstanceConfig) -> Path:
    path = _redaction_map_path(instance).with_name("corpus_caviarde_suspects.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _texte_brut_lisible(path: Path) -> str:
    try:
        if path.stat().st_size > 4 * 1024 * 1024:
            return ""
        brut = path.read_bytes()
    except OSError:
        return ""
    if b"\x00" in brut:
        return ""
    try:
        return brut.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return brut.decode("cp1252")
        except UnicodeDecodeError:
            return ""


def _corpus_document_text(instance: InstanceConfig, row: dict[str, str]) -> tuple[str, str]:
    """Le texte du document, et la raison nommee quand il n'y en a pas."""

    source = _source_path(instance, row)
    extension = Path(row.get("original_path") or row.get("file_name", "")).suffix.lower().lstrip(".")
    text = ""
    if source.exists():
        try:
            text = _source_text(source)
        except Exception:  # noqa: BLE001 - une source illisible ne casse pas le lot
            text = ""
        if not text.strip() and extension in CORPUS_TEXTE_BRUT_EXTENSIONS:
            text = _texte_brut_lisible(source)
    if not text.strip():
        text = _registered_text(instance, row)
    if text.strip():
        return text, ""
    if not source.exists():
        return "", "SOURCE_ABSENTE"
    if extension == "pdf":
        return "", "PDF_SANS_COUCHE_TEXTE"
    if extension not in CORPUS_MARKDOWN_EXTENSIONS | CORPUS_TEXTE_BRUT_EXTENSIONS:
        return "", f"FORMAT_SANS_TEXTE:{extension or 'sans_extension'}"
    return "", "TEXTE_VIDE"


def _csv_en_markdown(text: str) -> str:
    lignes = [ligne for ligne in text.splitlines() if ligne.strip()]
    if not lignes:
        return ""
    delimiteur = "\t" if "\t" in lignes[0] else ";" if lignes[0].count(";") > lignes[0].count(",") else ","
    try:
        table = list(csv.reader(lignes, delimiter=delimiteur))
    except Exception:  # noqa: BLE001
        return "```\n" + text.strip() + "\n```"
    if not table or len(table[0]) > 40:
        return "```\n" + text.strip() + "\n```"
    largeur = max(len(row) for row in table)
    rendu = []
    entete = [cell.replace("|", r"\|") for cell in table[0]] + [""] * (largeur - len(table[0]))
    rendu.append("| " + " | ".join(entete) + " |")
    rendu.append("| " + " | ".join(["---"] * largeur) + " |")
    for row in table[1:]:
        cells = [cell.replace("|", r"\|").replace("\n", " ") for cell in row]
        cells += [""] * (largeur - len(cells))
        rendu.append("| " + " | ".join(cells) + " |")
    return "\n".join(rendu)


def _corps_markdown(text: str, extension: str) -> str:
    if extension in {"md", "markdown"}:
        corps = text
    elif extension in {"csv", "tsv"}:
        corps = _csv_en_markdown(text)
    elif extension in {"json", "yml", "yaml", "html", "htm"}:
        corps = "```" + (extension if extension != "htm" else "html") + "\n" + text.strip() + "\n```"
    else:
        corps = text
    corps = re.sub(r"[ \t]+\n", "\n", corps)
    corps = re.sub(r"\n{4,}", "\n\n\n", corps)
    return corps.strip() + "\n"


def _remplacements_pour(
    instance: InstanceConfig,
    row: dict[str, str],
    identites: list[IdentiteCandidate],
    salt: bytes,
    registre: RegistrePseudonymes,
    map_state: tuple[list[str], list[dict[str, str]], dict[tuple[str, str], str]],
) -> tuple[dict[str, str], bool]:
    """Alias par identite, avec ecriture dans la table de correspondance C8."""

    fields, rows, index = map_state
    _ = fields
    now = now_iso()
    doc_id = row.get("doc_id", "")
    source_sha256 = row.get("sha256", "")
    remplacements: dict[str, str] = {}
    change = False
    for identite in identites:
        cle = (identite.categorie, identite.valeur)
        alias = index.get(cle)
        if not alias:
            if identite.categorie == "PERSONNE":
                # Une detection generique ne cree JAMAIS d'entite d'annuaire.
                # Elle en creait une, definitive et sans chemin de suppression,
                # que `applique_annuaire` propageait ensuite a tout le corpus:
                # un faux positif devenait une regle et se renforcait a chaque
                # passage. Seule une entite DEJA connue - lue d'une liste
                # nominative structurelle, ou saisie par un humain - rend son
                # alias stable. Les autres recoivent un alias ephemere, propre
                # a ce document, et entrent dans la file d'arbitrage.
                alias = registre.alias_connu(identite.nom, identite.prenom)
                if not alias:
                    alias = alias_ephemere(salt, doc_id, identite.nom, identite.prenom)
            else:
                alias = value_alias(salt, identite.categorie, identite.valeur)
            if not alias:
                continue
            index[cle] = alias
        remplacements[identite.valeur] = alias
        deja = any(
            item.get("category") == identite.categorie
            and item.get("original_value") == identite.valeur
            and item.get("doc_id") == doc_id
            and item.get("source_sha256") == source_sha256
            for item in rows
        )
        if not deja:
            rows.append(
                {
                    "map_id": f"MAP-{doc_id}-{identite.categorie}-{len(rows) + 1:04d}",
                    "created_at": now,
                    "doc_id": doc_id,
                    "source_sha256": source_sha256,
                    "category": identite.categorie,
                    "alias": alias,
                    "original_value": identite.valeur,
                    "reason": f"corpus_caviarde:{identite.motif}",
                    "storage_college": "C8_Restreint_Critique",
                    "retention_class": "preuve_reidentification_limitee",
                }
            )
            change = True
    return remplacements, change


_MOTIF_SUSPECT_MAJ = re.compile(rf"\b[{_MAJ}][{_MAJ}'’\-]{{3,}}\b")
_MOTIF_SUSPECT_MIXTE = re.compile(
    rf"\b[{_MAJ}][{_MIN}]{{2,}}\s+[{_MAJ}][{_MAJ}'’\-]{{2,}}\b|\b[{_MAJ}][{_MAJ}'’\-]{{2,}}\s+[{_MAJ}][{_MIN}]{{2,}}\b"
)


def _ecrit_markdown(
    instance: InstanceConfig,
    row: dict[str, str],
    corps: str,
    salt: bytes,
    stats: dict[str, object],
) -> Path:
    doc_id = row.get("doc_id") or "DOC"
    sortie = _corpus_markdown_dir(instance) / f"{doc_id}.caviarde.md"
    entete = [
        "---",
        "coproscope_corpus: caviarde",
        f"doc_id: {doc_id}",
        # `fichier_source: {file_name}` figurait ici. Un nom de fichier est
        # ecrit par le syndic et peut porter un patronyme - c'etait donc la
        # meme fuite que sur les ecrans, mais dans l'artefact destine a etre lu
        # par un agent. Le sha256 identifie la source sans la nommer.
        f"source_libelle: {libelle_public_document(row)}",
        f"source_sha256: {row.get('sha256', '')}",
        f"schema_alias: {ALIAS_SCHEMA}",
        f"sel_empreinte: {corpus_salt_fingerprint(salt)}",
        f"genere_le: {stats.get('genere_le', '')}",
        f"identites_remplacees: {stats.get('identites_remplacees', 0)}",
        f"remplacements_annuaire: {stats.get('remplacements_annuaire', 0)}",
        f"alias_distincts: {stats.get('alias_distincts', 0)}",
        f"categories: {stats.get('categories', '')}",
        f"suspects_residuels: {stats.get('suspects_residuels', 0)}",
        "lecture: >-",
        "  Tout pseudonyme commence par PERSONNE_, EMAIL_, TELEPHONE_, IBAN_ ou",
        "  SECRET_. Le corps d'un pseudonyme de personne est un nom d'arbre ou de",
        "  plante, suivi le cas echeant d'une couleur pour distinguer deux membres",
        "  d'une meme famille. Tout ce qui ressemble a un nom sans ce prefixe est",
        "  un nom reel que le caviardage n'a pas vu.",
        "avertissement: >-",
        "  Derive caviarde. Les pseudonymes sont des pseudonymes, pas de",
        "  l'anonymat: la table de correspondance vit en C8 et permet la",
        "  reidentification. Ne pas publier.",
        "protege_contre: >-",
        "  Un lecteur EXTERIEUR a la copropriete. Pas un coproprietaire: celui",
        "  qui detient l'etat date relie un pseudonyme a un lot en croisant le",
        "  numero de lot, les tantiemes, les montants et les dates, qui sont",
        "  conserves ici parce que sans eux le derive n'est plus analysable.",
        "ne_couvre_pas: >-",
        "  Les pieces sans couche texte, qui ne produisent aucun derive et",
        "  n'apparaissent donc pas dans ce corpus; les personnes absentes de",
        f"  l'annuaire, remplacees par un alias ephemere; et les {stats.get('suspects_residuels', 0)}",
        "  formes encore en clair signalees comme suspectes pour cette piece,",
        "  qui attendent un arbitrage humain.",
        "---",
        "",
    ]
    write_text(sortie, "\n".join(entete) + corps)
    return sortie


def build_person_directory(
    instance: InstanceConfig,
    run: RunContext,
    *,
    textes: dict[str, str] | None = None,
) -> dict[str, object]:
    """Extrait l'annuaire des personnes des listes nominatives du corpus."""

    salt = load_corpus_salt(instance)
    registre = RegistrePseudonymes(instance, salt)
    if textes is None:
        _, documents = read_csv(instance.register("documents"))
        textes = {}
        for row in documents:
            texte, _raison = _corpus_document_text(instance, row)
            if texte.strip():
                textes[row.get("doc_id", "")] = texte
    avant = len(registre.entrees())
    sources: dict[str, int] = {}
    for doc_id, texte in textes.items():
        entrees = extrait_entrees_annuaire(texte)
        if entrees:
            sources[doc_id] = len(entrees)
        for compte, nom_complet in entrees:
            nom, prenom = _decoupe_nom(nom_complet)
            registre.alias_pour(nom, prenom, compte=compte, source_doc_id=doc_id)
    chemin = registre.sauvegarde()
    resultat = {
        "status": "ok",
        "personnes": len(registre.entrees()),
        "nouvelles": len(registre.entrees()) - avant,
        "documents_sources": sources,
        "annuaire": str(annuaire_path(instance)),
    }
    run.log_action(
        "corpus_caviarde_annuaire",
        chemin or annuaire_path(instance),
        f"personnes={resultat['personnes']}; nouvelles={resultat['nouvelles']}",
    )
    return resultat


def build_markdown_corpus(
    instance: InstanceConfig,
    run: RunContext,
    *,
    limit: int | None = None,
    doc_ids: list[str] | None = None,
) -> dict[str, object]:
    """Produit le derive Markdown caviarde pour tout document porteur de texte."""

    _, documents = read_csv(instance.register("documents"))
    if doc_ids:
        cible = set(doc_ids)
        documents = [row for row in documents if row.get("doc_id", "") in cible]
    salt = load_corpus_salt(instance)
    registre = RegistrePseudonymes(instance, salt)
    map_path = _redaction_map_path(instance)
    map_state = _corpus_map_rows(map_path)
    now = now_iso()

    # Passe 1: lire les textes une fois, et en extraire l'annuaire.
    textes: dict[str, str] = {}
    raisons_sans_texte: dict[str, str] = {}
    for row in documents:
        texte, raison = _corpus_document_text(instance, row)
        doc_id = row.get("doc_id", "")
        if raison:
            raisons_sans_texte[doc_id] = raison
        else:
            textes[doc_id] = texte
    build_person_directory(instance, run, textes=textes)
    registre = RegistrePseudonymes(instance, salt)
    entrees_annuaire = registre.entrees()
    # Savoir si une chaine est ambigue avec le lexique commun se decide sur le
    # CORPUS, pas sur la piece: la piece ou le mot se lit en minuscules et la
    # piece ou il faut trancher ne sont pas la meme piece.
    bas_de_casse_corpus = vocabulaire_bas_de_casse_corpus(textes)

    couverture: list[dict[str, str]] = []
    suspects_rows: list[dict[str, str]] = []
    map_change = False
    produits = 0

    for row in documents:
        if limit is not None and produits >= limit:
            break
        doc_id = row.get("doc_id", "")
        extension = Path(row.get("original_path") or row.get("file_name", "")).suffix.lower().lstrip(".")
        base = {
            "doc_id": doc_id,
            "file_name": row.get("file_name", ""),
            "original_path": row.get("original_path", ""),
            "extension": extension,
            "source_sha256": row.get("sha256", ""),
            "genere_le": now,
        }
        if doc_id in raisons_sans_texte:
            couverture.append(
                {**base, "statut": "SANS_DERIVE", "raison": raisons_sans_texte[doc_id], "char_count": "0"}
            )
            _update_document_row(
                instance,
                doc_id,
                {"corpus_md_statut": "SANS_DERIVE", "corpus_md_path": "", "corpus_md_sha256": ""},
            )
            continue
        text = textes.get(doc_id, "")
        try:
            # Passe 2a: les variantes des personnes deja connues de l'annuaire.
            partiel, compteurs_annuaire = applique_annuaire(
                text, entrees_annuaire, bas_de_casse_corpus=bas_de_casse_corpus
            )
            # Ce que la passe 2a a REFUSE de masquer, et qui reste donc en
            # clair. Sans ce releve, le refus serait un `continue` muet - le
            # defaut meme que `RM-2026-0065` nomme.
            ambigus = formes_seules_retenues(
                text, entrees_annuaire, bas_de_casse_corpus=bas_de_casse_corpus
            )
            # Passe 2b: les regles generiques, sur ce qui reste en clair.
            identites = detecte_identites(partiel)
            remplacements, change = _remplacements_pour(
                instance, row, identites, salt, registre, map_state
            )
            map_change = map_change or change
            caviarde, compteurs = applique_alias(partiel, remplacements)
            corps = _corps_markdown(caviarde, extension)
            residuels = suspects_residuels(corps)
            alias_utilises = set(remplacements.values()) | {
                entree.get("alias", "")
                for entree in entrees_annuaire
                if entree.get("alias") and entree.get("alias") in corps
            }
            stats = {
                "genere_le": now,
                "identites_remplacees": sum(compteurs.values()) + sum(compteurs_annuaire.values()),
                "remplacements_annuaire": sum(compteurs_annuaire.values()),
                "alias_distincts": len(alias_utilises),
                "categories": ";".join(sorted({item.categorie for item in identites})),
                "suspects_residuels": len(residuels) + len(ambigus),
            }
            sortie = _ecrit_markdown(instance, row, corps, salt, stats)
        except Exception as exc:  # noqa: BLE001 - un document ne bloque pas le corpus
            couverture.append(
                {
                    **base,
                    "statut": "ECHEC_DERIVATION",
                    "raison": f"{type(exc).__name__}: {exc}",
                    "char_count": str(len(text)),
                }
            )
            _update_document_row(
                instance,
                doc_id,
                {"corpus_md_statut": "ECHEC_DERIVATION", "corpus_md_path": "", "corpus_md_sha256": ""},
            )
            run.log_error(f"corpus_caviarde {doc_id}: {exc}")
            continue
        digest = sha256_file(sortie)
        relatif = relative_to(instance.root("workspace"), sortie)
        couverture.append(
            {
                **base,
                "statut": "MARKDOWN_OK",
                "raison": "",
                "markdown_path": relatif,
                "markdown_sha256": digest,
                "char_count": str(len(corps)),
                "identites_remplacees": str(stats["identites_remplacees"]),
                "remplacements_annuaire": str(stats["remplacements_annuaire"]),
                "alias_distincts": str(stats["alias_distincts"]),
                "categories": str(stats["categories"]),
                "suspects_residuels": str(stats["suspects_residuels"]),
            }
        )
        for forme, occurrences in sorted(residuels.items(), key=lambda item: -item[1]):
            suspects_rows.append(
                {
                    "doc_id": doc_id,
                    "genere_le": now,
                    "forme": forme,
                    "occurrences": str(occurrences),
                    "motif": "suspect_non_caviarde",
                    "racine_normalisee": racine_de_forme(forme),
                    # Rempli en fin de passe: le nombre de documents n'est
                    # connu qu'une fois tout le corpus parcouru.
                    "nb_documents": "",
                    "appariement_propose": "",
                }
            )
        # Un patronyme de l'annuaire dont la forme seule a ete retenue faute de
        # pouvoir la distinguer d'un mot courant DANS CETTE PIECE. Motif
        # distinct: contrairement a `suspect_non_caviarde`, la personne est
        # connue, donc `complete_la_file` saura proposer son alias.
        for forme, occurrences in sorted(ambigus.items(), key=lambda item: -item[1]):
            suspects_rows.append(
                {
                    "doc_id": doc_id,
                    "genere_le": now,
                    "forme": forme,
                    "occurrences": str(occurrences),
                    "motif": "patronyme_ambigu_lexique",
                    "racine_normalisee": racine_de_forme(forme),
                    "nb_documents": "",
                    "appariement_propose": "",
                }
            )
        _update_document_row(
            instance,
            doc_id,
            {
                "corpus_md_statut": "MARKDOWN_OK",
                "corpus_md_path": relatif,
                "corpus_md_sha256": digest,
            },
        )
        produits += 1

    registre.sauvegarde()
    if map_change:
        write_csv(map_path, map_state[0], map_state[1])
    couverture_path = _corpus_coverage_path(instance)
    write_csv(couverture_path, CORPUS_COVERAGE_FIELDS, couverture)
    if suspects_rows:
        suspects_rows = complete_la_file(suspects_rows, entrees_annuaire)
        write_csv(_corpus_suspects_path(instance), CORPUS_SUSPECT_FIELDS, suspects_rows)
    statuts = Counter(item.get("statut", "") for item in couverture)
    raisons = Counter(item.get("raison", "") for item in couverture if item.get("raison"))
    run.log_action(
        "corpus_caviarde_markdown",
        couverture_path,
        f"documents={len(couverture)}; derives={produits}; sans_derive={statuts.get('SANS_DERIVE', 0)}",
    )
    return {
        "status": "ok",
        "documents": len(couverture),
        "markdown_count": produits,
        "sans_derive": statuts.get("SANS_DERIVE", 0) + statuts.get("ECHEC_DERIVATION", 0),
        "statuts": dict(statuts),
        "raisons": dict(raisons),
        "couverture": str(couverture_path),
        "corpus_dir": str(_corpus_markdown_dir(instance)),
        "annuaire": str(annuaire_path(instance)),
        "annuaire_personnes": len(entrees_annuaire),
        "sel_empreinte": corpus_salt_fingerprint(salt),
        "identites_remplacees": sum(int(item.get("identites_remplacees") or 0) for item in couverture),
        "remplacements_annuaire": sum(int(item.get("remplacements_annuaire") or 0) for item in couverture),
        "alias_distincts": len({row.get("alias", "") for row in map_state[1] if row.get("alias")}),
        "suspects_residuels": sum(int(item.get("suspects_residuels") or 0) for item in couverture),
    }


def build_markdown_corpus_if_enabled(
    instance: InstanceConfig,
    run: RunContext,
) -> dict[str, object]:
    """Point d'appel du pipeline: ne fait rien tant que le reglage est absent."""

    if not corpus_markdown_enabled(instance):
        return {"status": "DESACTIVE", "raison": "settings.corpus_caviarde.enabled absent ou faux"}
    return build_markdown_corpus(instance, run)


def _corpus_map_rows(path: Path) -> tuple[list[str], list[dict[str, str]], dict[tuple[str, str], str]]:
    fields, rows = _load_map(path)
    index = {
        (row.get("category", ""), row.get("original_value", "")): row.get("alias", "")
        for row in rows
    }
    return fields, rows, index
