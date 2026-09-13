from __future__ import annotations

# --- Ce sur quoi un type repose ---------------------------------------------
#
# Trois separations tiennent ce module, et chacune repare un fait mesure:
#
#   1. Un mot-cle est une preuve de CONTENU. Le nom de fichier et le chemin ont
#      leurs propres motifs, avec leurs propres poids. Melanger les trois dans
#      une seule chaine faisait entrer les dossiers de travail de l'audit dans
#      le corpus documentaire: une grille de controle contenant la chaine
#      `Releve_Bancaire` devenait un releve bancaire.
#   2. Deux orthographes du meme mot francais sont le meme mot. Le comparateur
#      neutralise les accents, comme le fait deja la signature de titre. Sans
#      cela, `proces-verbal de l'assemblee generale` correctement accentue - la
#      locution qui NOMME le document - etait la seule a etre jetee.
#   3. Une decision doit dire sur quoi elle repose. Une egalite de score au
#      sommet, un titre lu en tete, un texte utile absent: chacun de ces faits
#      s'ecrit dans le registre. Un type affirme sans qu'aucun texte n'ait ete
#      lu ne doit pas ressembler a un type lu.

# Fenetre de contenu soumise aux mots-cles, en caracteres.
CLASSIFICATION_CONTENT_CHARS = 6000

#: Champs d'une regle qui la documentent sans peser sur son score.
#:
#: `fondement` porte la regle de droit qui justifie un motif retenu ou retire.
#: Il ne se lit pas au classement: il se lit par-dessus l'epaule de qui doute
#: d'une regle, et c'est la seule trace qui distingue un motif pese d'un motif
#: recopie. Toute garde a liste fermee posee sur les noms de champs d'une regle
#: doit donc l'accepter, sans quoi la taxonomie livree par defaut devient
#: illisible pour le classifieur lui-meme.
CHAMPS_REGLE_DOCUMENTAIRES = frozenset({"fondement"})


def _rule_type(rule: dict) -> str:
    return str(rule.get("document_type", rule.get("type_document", "A_CLASSER")))


def _rule_lot(rules: list[dict], document_type: str) -> str:
    for rule in rules:
        if _rule_type(rule) == document_type:
            return str(rule.get("lot", ""))
    return ""


def _rule_score(
    rule: dict, content: str, file_text: str, path_text: str
) -> tuple[bool, int]:
    """(au moins une preuve, score) pour une seule regle.

    Isole du parcours pour que le score d'un type puisse etre recalcule apres
    coup. Sans cela, une ligne dont le titre change le type gardait le score
    accumule par le type ecarte, et le registre affichait un chiffre qui ne
    repondait plus du type affiche.
    """
    score = 0
    matched = False
    # Les six champs passent par l'accesseur de la zone vocabulaire, qui connait
    # les alias francais de la configuration livree. La priorite ci-dessous en
    # depend directement: la taxonomie ecrit `priorite` trente-neuf fois quand
    # ce code lisait `priority`, donc les trente-neuf priorites valaient zero et
    # le seul arbitrage entre regles concurrentes etait mort.
    filename_patterns = _champ_regle(rule, "filename_patterns", [])
    path_patterns = _champ_regle(rule, "path_patterns", [])
    keywords = _champ_regle(rule, "keywords", [])
    filename_weight = int(_champ_regle(rule, "filename_weight", 50))
    path_weight = int(_champ_regle(rule, "path_weight", 80))
    keyword_weight = int(_champ_regle(rule, "keyword_weight", 5))
    for pattern in filename_patterns:
        if _pattern_matches(pattern, file_text):
            matched = True
            score += filename_weight
    for pattern in path_patterns:
        if _pattern_matches(pattern, path_text):
            matched = True
            score += path_weight
    for keyword in keywords:
        if _keyword_matches(content, str(keyword)):
            matched = True
            score += keyword_weight
    if matched:
        score += int(_champ_regle(rule, "priority", 0))
    return matched, score


def _named_types(rules: list[dict], file_text: str, path_text: str) -> set[str]:
    """Types que le NOM du fichier, ou son chemin, designent directement.

    Le nom d'un fichier est une denomination, au meme titre qu'un titre lu en
    tete du texte. Quand les deux se contredisent, aucune ne tranche seule.
    """
    named: set[str] = set()
    for rule in rules:
        filename_patterns = rule.get("filename_patterns", rule.get("motifs_nom_fichier", []))
        path_patterns = rule.get("path_patterns", rule.get("motifs_chemin", []))
        if any(_pattern_matches(pattern, file_text) for pattern in filename_patterns) or any(
            _pattern_matches(pattern, path_text) for pattern in path_patterns
        ):
            named.add(_rule_type(rule))
    return named


def _content_evidence(rules: list[dict], document_type: str, content: str) -> bool:
    """Un mot du CONTENU soutient-il ce type, ou seulement son nom de fichier ?

    C'est la question que "le type repose-t-il sur une lecture" pose vraiment.
    La longueur du texte n'y repond pas: mesure, une trace de courriel de 150
    caracteres utiles declenche deux mots-cles de son propre type - elle est
    courte et pourtant lue - tandis qu'un remplissage de 110 caracteres sous un
    nom de facture n'en declenche aucun, et son type ne tient qu'au nom.
    """
    for rule in rules:
        if _rule_type(rule) != document_type:
            continue
        keywords = rule.get("keywords", rule.get("mots_cles", []))
        if any(_keyword_matches(content, str(keyword)) for keyword in keywords):
            return True
    return False


def _type_score(
    rules: list[dict], document_type: str, content: str, file_text: str, path_text: str
) -> int:
    """Score que les regles d'un type donne obtiennent sur cette piece."""
    total = 0
    for rule in rules:
        if _rule_type(rule) == document_type:
            total = max(total, _rule_score(rule, content, file_text, path_text)[1])
    return total


def _classify(
    content: str, file_name: str, original_path: str, rules: list[dict]
) -> tuple[str, str, int, list[str]]:
    """(lot, type, score, types ex aequo au sommet).

    `content` est le texte extrait seul: ni nom de fichier, ni chemin. Ceux-ci
    ont leurs propres motifs ci-dessous.
    """
    best = ("A_CLASSER", "A_CLASSER", 0)
    tops: list[str] = []
    file_text = file_name.lower()
    path_text = original_path.lower().replace("\\", "/")
    for rule in rules:
        document_type = _rule_type(rule)
        _, score = _rule_score(rule, content, file_text, path_text)
        if score > best[2]:
            # `rule["lot"]` et non `_champ_regle(..., "A_CLASSER")`: un defaut
            # de configuration doit rester bruyant ici. Avec un defaut, une
            # regle sans `lot` rendait ('A_CLASSER', 'PV_AG', 5) - un type
            # documentaire AFFIRME, range dans un lot invente, sans erreur.
            # `_verifier_regles` refuse cette regle au chargement; cette ligne
            # est la seconde barriere, pour les appels directs.
            best = (str(rule["lot"]), document_type, score)
            tops = [document_type]
        elif score == best[2] and score > 0 and document_type not in tops:
            tops.append(document_type)
    return best[0], best[1], best[2], tops


def _normalized_search_text(value: str) -> str:
    """Minuscules, sans accents, tout caractere non alphanumerique en espace.

    `_signature_text` est definie par 03_title_signature.py, charge apres ce
    fichier mais avant tout appel. Une seule normalisation pour les deux
    modules: c'est leur divergence qui ecartait le vocabulaire accentue.
    """
    return _signature_text(value or "")


def _keyword_matches(text: str, keyword: str) -> bool:
    normalized = _normalized_search_text(keyword or "")
    if not normalized:
        return False
    haystack = _normalized_search_text(text)
    parts = [re.escape(part) for part in normalized.split() if part]
    if not parts:
        return False
    pattern = r"(?<![a-z0-9])" + r"\s+".join(parts) + r"(?![a-z0-9])"
    return re.search(pattern, haystack, flags=re.IGNORECASE) is not None


#: `` de la bibliotheque regulière compte le tiret bas comme une lettre. Or
#: le tiret bas est le separateur de jetons dominant des noms de fichiers, donc
#: `dtg` ne trouve JAMAIS `2024-09-19_DTG_Tilleuls_WeGroup.pdf` - le
#: DTG reel d'un coffre de production, mesure le 2026-09-06. Cinq motifs de la
#: taxonomie etaient morts de cette facon: `edd`, `dtg`, `dpe`, `os`, `doe`.
#:
#: Dans ce classeur, une frontiere de mot veut dire une frontiere de JETON, et
#: un jeton de nom de fichier se termine a tout ce qui n'est ni lettre ni
#: chiffre. La reecriture porte l'axe; corriger les cinq motifs un par un
#: n'aurait porte que les modalites observees.
_FRONTIERE_DEBUT = "(?<![a-z0-9])"
_FRONTIERE_FIN = "(?![a-z0-9])"


def _en_frontiere_de_jeton(motif: str) -> str:
    """Traduit les `` d'un motif en frontieres de jeton de nom de fichier."""
    if "\b" not in motif:
        return motif
    morceaux = motif.split("\b")
    rendu = morceaux[0]
    for i, suite in enumerate(morceaux[1:], start=1):
        avant = rendu[-1:] if rendu else ""
        # Un `` place avant du texte ouvre un jeton; place apres, il le ferme.
        ouvre = bool(suite) and (suite[0].isalnum() or suite[0] == "\\")
        rendu += (_FRONTIERE_DEBUT if ouvre and not avant.isalnum()
                  else _FRONTIERE_FIN) + suite
    return rendu


def _pattern_matches(pattern: object, text: str) -> bool:
    raw = str(pattern or "").strip()
    if not raw:
        return False
    if re.fullmatch(r"[A-Za-z0-9]{1,3}", raw):
        return _keyword_matches(text, raw)
    return re.search(_en_frontiere_de_jeton(raw), text, flags=re.IGNORECASE) is not None


def classify(instance, run: RunContext, copy_files: bool = True) -> Path:
    registry_path = instance.register("documents")
    fields, rows = _read_rows(registry_path)
    taxonomy = _load_taxonomy(instance)
    _verifier_taxonomie(taxonomy, journal=run.log_error)
    rules = taxonomy.get("rules", taxonomy.get("regles", []))
    # Un champ non lu ne bloque pas le classement, mais il ne passe pas non
    # plus sans laisser de trace: il part au journal d'erreurs de la course.
    _verifier_regles(rules, journal=run.log_error)
    classified_dir = instance.artifact("classified_dir")
    workspace_root = instance.root("workspace")
    title_signatures = _title_signatures(taxonomy)
    head_chars = _title_head_chars(taxonomy)
    useful_floor = _useful_text_floor(taxonomy)

    processed = 0
    doubts = 0
    without_text = 0
    promotions = 0
    conflicts = 0
    ties = 0
    for row in rows:
        sample = _text_sample(instance, row)
        extracted = _extracted_text(instance, row)
        titled, useful = title_signature_matches(
            extracted, title_signatures, head_chars, useful_floor
        )
        content = extracted[:CLASSIFICATION_CONTENT_CHARS]
        file_text = row.get("file_name", "").lower()
        path_text = row.get("original_path", "").lower().replace("\\", "/")
        lot, doc_type, score, tops = _classify(
            content, row.get("file_name", ""), row.get("original_path", ""), rules
        )

        # Le titre lu en tete NOMME le document. Il ne decide pourtant que si
        # rien d'autre ne le nomme: le nom du fichier et son chemin sont eux
        # aussi des denominations, et ils portent la leur.
        #
        # La mesure des deux cabinets - 5 vrais positifs, 0 faux positif sur 37
        # documents - porte sur la SIGNATURE, pas sur la promotion. La fenetre
        # de tete de 300 caracteres a ete calibree pour un role de garde, sur
        # des lignes deja typees PV_AG. Employee comme discriminant sur tout le
        # registre, elle retypait en proces-verbal une convocation dont l'ordre
        # du jour porte "approbation du proces-verbal precedent": mesure, le
        # titre y tombe en position 252 pour une fenetre de 300. Le cas est la
        # forme dominante du corpus, dont 69,3 % des lignes sont des fragments
        # de pages sans preambule.
        titre_en_conflit = False
        if len(titled) == 1 and titled[0] != doc_type:
            promu = titled[0]
            named = _named_types(rules, file_text, path_text)
            if doc_type in named and promu not in named:
                # Deux denominations se contredisent: le nom du fichier porte un
                # type, le titre lu en tete en porte un autre. Aucune ne tranche
                # en silence. Le type acquis est conserve - c'est le moins
                # destructif - et le desaccord devient un fait ecrit.
                titre_en_conflit = True
                conflicts += 1
                row["notes"] = append_note(
                    row.get("notes", ""),
                    f"Titre {promu} lu en tete, mais le nom du fichier designe {doc_type}:"
                    f" denominations en conflit, {doc_type} conserve sans preuve qui tranche.",
                )
            else:
                ancien = doc_type
                doc_type = promu
                lot = _rule_lot(rules, doc_type) or lot
                # Le score suit le type: celui du type ecarte ne repond de rien.
                score = max(_type_score(rules, doc_type, content, file_text, path_text), 1)
                tops = [doc_type]
                row["notes"] = append_note(
                    row.get("notes", ""),
                    f"Titre {doc_type} lu en tete du texte extrait: type retenu contre {ancien}.",
                )
                promotions += 1

        row["lot"] = lot
        row["document_type"] = doc_type
        if not row.get("suspected_date"):
            # La date se lit dans le DOCUMENT, puis dans son nom. Jamais dans
            # `sample`: cet echantillon commence par `original_path`, donc une
            # date presente dans l'arborescence gagnait SYSTEMATIQUEMENT contre
            # le document. Mesure du 2026-09-08: 270 pieces datees par leur
            # dossier de collecte, 0 par leur contenu. Voir `core.date_du_document`.
            date_lue, source_date = date_du_document(extracted, row.get("file_name", ""))
            row["suspected_date"] = date_lue
            precision = note_de_date(date_lue, source_date, row.get("original_path", ""))
            if precision:
                row["notes"] = append_note(row.get("notes", ""), precision)
        row["classification_status"] = "AUTO_CLASSIFIED" if score else "A_CLASSER"

        if not useful:
            # Aucun texte utile: le type ne repose sur aucune lecture, quel
            # qu'il soit. C'est un fait nomme, pas un type comme les autres.
            row["classification_status"] = CLASSIFICATION_NO_TEXT_STATUS
            row["notes"] = append_note(
                row.get("notes", ""),
                "Aucun texte utile extrait: le type ne repose sur aucune lecture du contenu.",
            )
            without_text += 1
        elif len(useful) < useful_floor and not _content_evidence(rules, doc_type, content):
            # Trop court pour juger, ET rien dans ce peu de texte ne soutient le
            # type: il ne tient qu'au nom du fichier. Ce n'est pas la longueur
            # seule qui condamne - une trace de courriel de 150 caracteres
            # utiles declenche deux mots-cles de son propre type, et elle est
            # bel et bien lue. C'est l'absence de toute preuve de contenu qui
            # fait qu'un type est affirme sans lecture.
            row["classification_status"] = CLASSIFICATION_NO_TEXT_STATUS
            row["notes"] = append_note(
                row.get("notes", ""),
                f"Texte utile trop court pour juger ({len(useful)} caracteres,"
                f" plancher {useful_floor}) et aucun mot du contenu ne soutient"
                f" {doc_type}: le type ne repose que sur le nom du fichier.",
            )
            without_text += 1
        elif titre_en_conflit:
            row["classification_status"] = CLASSIFICATION_DOUBT_STATUS
            doubts += 1
        elif len(titled) > 1:
            row["classification_status"] = CLASSIFICATION_DOUBT_STATUS
            row["notes"] = append_note(
                row.get("notes", ""),
                "Plusieurs titres reconnus en tete (" + ", ".join(sorted(titled)) + "): type a confirmer.",
            )
            doubts += 1
        elif title_signatures.get(doc_type, "") and not titled:
            verdict = title_signature_verdict(
                extracted, title_signatures[doc_type], head_chars, useful_floor
            )
            if verdict == CLASSIFICATION_NO_TEXT_STATUS:
                row["classification_status"] = verdict
                row["notes"] = append_note(
                    row.get("notes", ""),
                    "Texte extrait insuffisant pour juger le type: ni confirme, ni infirme.",
                )
                without_text += 1
            elif verdict == CLASSIFICATION_DOUBT_STATUS:
                row["classification_status"] = verdict
                row["notes"] = append_note(
                    row.get("notes", ""),
                    f"Titre {doc_type} absent de la tete du texte extrait: type a confirmer.",
                )
                doubts += 1

        if len(tops) > 1:
            # L'egalite est tranchee par l'ordre des regles dans le fichier de
            # configuration. C'est un arbitrage sans preuve: il se dit.
            row["notes"] = append_note(
                row.get("notes", ""),
                "Egalite de score entre " + ", ".join(sorted(tops))
                + f": {doc_type} retenu par l'ordre des regles, pas par une preuve.",
            )
            ties += 1

        apply_access_policy(row, text=sample, instance=instance)
        if copy_files:
            source = workspace_root / row["original_path"]
            target_dir = classified_dir / lot
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"{row['doc_id']}__{safe_name(row['file_name'])}"
            if source.exists() and not target.exists():
                shutil.copy2(source, target)
                run.log_action("write", target, f"classified copy from {source}")
        processed += 1

    # Jusqu'ici chaque ligne a ete jugee seule. Deux lignes de meme empreinte
    # portent pourtant le MEME contenu: leurs verdicts se confrontent, sinon un
    # contenu unique sort du classement avec deux types et deux dates, chacun
    # affirme sans que rien ne signale l'autre.
    #
    # La confrontation porte sur TOUT champ non exempte, y compris ceux que
    # `apply_access_policy` vient de poser quelques lignes plus haut sans
    # passer par `row[...] = `. Mesure du 2026-09-09: ces 13 champs-la
    # divergeaient en silence entre deux exemplaires d'un meme contenu, jusqu'au
    # college de confidentialite. Voir `02b_empreintes_concurrentes.py`.
    empreintes = reconcilier_par_empreinte(rows)
    if empreintes["lignes_sans_empreinte"]:
        # Residu nomme: sans empreinte, aucune confrontation n'est possible.
        # Ces lignes ne sont pas reconciliees, et le taire les ferait passer
        # pour reconciliees.
        run.log_error(
            f"reconciliation par empreinte impossible sur"
            f" {empreintes['lignes_sans_empreinte']} ligne(s) sans sha256"
        )

    write_csv(registry_path, fields, rows)
    run.log_action(
        "write",
        registry_path,
        f"classification processed={processed} doubt={doubts} no_text={without_text}"
        f" title_promoted={promotions} title_conflict={conflicts} ties={ties}"
        f" empreintes_partagees={empreintes['groupes']}"
        f" desaccords_empreinte={empreintes['desaccords']}"
        f" champs_en_desaccord={empreintes['champs_en_desaccord'] or '-'}"
        f" lectures_partielles={empreintes['lectures_partielles']}"
        f" sans_empreinte={empreintes['lignes_sans_empreinte']}",
    )
    return registry_path

