"""Ecriture des registres de convocation, confrontation comprise.

Une seule porte. L'extracteur est pur et ne sait rien des registres; ce module
est le seul a ecrire, et il ne PEUT pas ecrire sans avoir lu ce qui etait la.
La confrontation n'est donc pas une verification que l'appelant peut sauter:
il n'existe aucune autre fonction d'ecriture.

Ce que la confrontation protege: l'identite d'un devis cite est positionnelle -
(document, resolution, sous-numero). Elle est assumee comme une convention. Le
contenu, lui, est le TEMOIN de cette identite: si l'objet a cette position ne
porte plus la meme entreprise ni le meme montant, le lien n'est pas repointe en
silence, il est signale divergent.
"""

from __future__ import annotations

from pathlib import Path

from . import _convocation_store as store
from ._convocation_controles import controles
from ._convocation_calibrage import calibrer
from ._convocation_extraction import Convocation, parse_convocation
from ._convocation_nature import ETAT_CONSTATEE, ETAT_ILLISIBLE, nature_du_document
from ._convocation_motifs import (
    CONVOCATION_FIELDS,
    DECLARATION_FIELDS,
    DEVIS_CITE_FIELDS,
    ORIGINE_CORRIGE,
    ORIGINE_EXTRAIT,
)
from .lisibilite import pages_du_referentiel

TYPE_CONVOCATION = "Convocation_AG"

# Les types qui peuvent porter une convocation. Ils NARROWISSENT la recherche,
# ils ne decident pas: c'est la nature mesuree sur le texte qui tranche.
#
# La liste est large a dessein, parce que le classement se trompe: sur le corpus
# Erables (pseudo), un meme contenu d'annexe comptable est classe `Annexe_Comptable`
# en 2023 et `CR_CS` en 2024, 2025 et 2026 - le nom de fichier a change, pas la
# piece. Et `2023-06-19_AG_PV_Convoc.pdf` porte `PV` dans son nom sans etre un
# proces-verbal.
TYPES_CANDIDATS = frozenset(
    {
        "Convocation_AG",
        "PV_AG",
        "Annexe_AG",
        "A_CLASSER",
    }
)


# En deca de ce nombre de caracteres sur tout le document, il n'y a pas de
# couche texte, quoi qu'en dise le niveau d'extraction enregistre.
SEUIL_COUCHE_TEXTE = 50


def _porte_du_texte(pages: list[str]) -> bool:
    """Un document de vingt-sept pages vides n'est pas un document lu.

    Le piege est qu'une liste de vingt-sept chaines vides est un objet NON VIDE:
    sans ce controle, la convocation scannee du 21/02/2024 serait comptee comme
    "lue, zero devis" au lieu de "sans couche texte", et son absence de resultat
    passerait pour un fait sur la convocation plutot que sur notre lecture.

    C'est le meme defaut que celui releve sur cent onze documents du corpus,
    classes `L1_NATIVE_TEXT_PYMUPDF` alors qu'ils rendent zero caractere: le
    niveau d'extraction enregistre ne teste pas la densite. On mesure donc le
    texte, on ne fait pas confiance a l'etiquette.
    """
    return sum(len(page.strip()) for page in pages) >= SEUIL_COUCHE_TEXTE


def pages_du_document(instance, row: dict[str, str]) -> list[str]:
    r"""Le texte page par page, parce que la page est l'ancre.

    Deux sources, par ordre de fidelite decroissante: le PDF d'origine, puis le
    referentiel de position - `lisibilite.REFERENTIEL`, le fichier designe par
    `text_path`. Une liste vide signifie qu'il n'y a rien a lire.

    Le repli decoupe sur les bornes du referentiel, et sur elles seules. Il
    cherchait auparavant un saut de page `\f` et rendait le document entier en
    une page quand il n'en trouvait pas. Or l'extraction n'ecrit jamais de
    `\f`: elle ecrit des marqueurs `===== PAGE n =====`. Le repli rendait donc
    TOUJOURS une page unique, marqueurs compris, et la pagination annoncee etait
    fausse. Mesure du 2026-09-07 sur les 121 documents candidats de
    `tilleuls_20260906`: 57 passaient par ce repli, 57 rendaient une page,
    alors qu'ils portent de 3 a 124 bornes.

    Chercher le `\f` etait doublement faux: quatre fichiers du corpus en
    portent trois chacun, venus de leur propre contenu. Le repli aurait rendu
    quatre pages pour un document qui en compte 143.

    La densite se mesure desormais par `_porte_du_texte` sur les DEUX voies, et
    non plus par un `texte.strip()` propre au repli. Ce `strip()` comptait les
    marqueurs comme du contenu - le defaut meme que `lisibilite` ferme. Mesure
    du 2026-09-07: les 57 documents du repli rendent de 60 a 2741 caracteres au
    `strip()` et ZERO caractere de document. Ils ressortaient `INDETERMINE`,
    donc ni ecartes ni signales, puis etaient lus comme des convocations a zero
    devis. Ils rejoignent les 27 deja comptes sans couche texte, soit 84 sur
    121: une convocation scannee est un fait sur notre lecture, pas sur la
    convocation.
    """
    original = (row.get("original_path") or "").strip()
    if original and original.lower().endswith(".pdf"):
        chemin = Path(original)
        if not chemin.is_absolute():
            chemin = instance.root("workspace") / original
        if chemin.exists():
            pages = _pages_pdf(chemin)
            if _porte_du_texte(pages):
                return pages
    pages = pages_du_referentiel(_texte_extrait(instance, row))
    return pages if _porte_du_texte(pages) else []


def _pages_pdf(chemin: Path) -> list[str]:
    try:
        import fitz  # type: ignore
    except ImportError:
        return []
    try:
        document = fitz.open(chemin)
    except Exception:  # noqa: BLE001 - un PDF illisible est un fait, pas un plantage
        return []
    try:
        return [document[index].get_text() for index in range(len(document))]
    finally:
        document.close()


def _texte_extrait(instance, row: dict[str, str]) -> str:
    chemin_relatif = row.get("text_path")
    if not chemin_relatif:
        return ""
    chemin = instance.root("workspace") / chemin_relatif
    if not chemin.exists():
        return ""
    return chemin.read_text(encoding="utf-8", errors="ignore")


def _convocation_id(row: dict[str, str]) -> str:
    date = (row.get("suspected_date") or "").strip()
    return f"CONV-{date}" if date else f"CONV-{row.get('doc_id', 'INCONNU')}"


def lignes_devis(convocation: Convocation, *, convocation_id: str, doc_id: str) -> list[dict[str, str]]:
    return [
        {
            "devis_cite_id": f"{convocation_id}-D{devis.numero:03d}-{devis.sous_numero:02d}",
            "convocation_id": convocation_id,
            "doc_id": doc_id,
            "numero": str(devis.numero),
            "sous_numero": str(devis.sous_numero),
            "objet": devis.objet,
            "entreprise": devis.entreprise,
            "montant_ttc": devis.montant_ttc,
            "etat_prix": devis.etat_prix,
            "montant_intitule": devis.montant_intitule,
            "discordance_intitule_corps": "oui" if devis.discordance_intitule_corps else "non",
            "majorite_annoncee": devis.majorite_annoncee,
            "cle_repartition": devis.cle_repartition,
            "avis_cs_affirme": "oui" if devis.avis_cs_affirme else "non",
            "analyse_offres_affirmee": "oui" if devis.analyse_offres_affirmee else "non",
            "page": str(devis.page),
            "origine": ORIGINE_EXTRAIT,
        }
        for devis in convocation.devis
    ]


def lignes_declarations(convocation: Convocation, *, convocation_id: str, doc_id: str) -> list[dict[str, str]]:
    lignes = []
    for rang, declaration in enumerate(convocation.declarations, start=1):
        lignes.append(
            {
                "declaration_id": f"{convocation_id}-DECL{rang:02d}",
                "convocation_id": convocation_id,
                "doc_id": doc_id,
                "nature": declaration.nature,
                "ag_visee": declaration.ag_visee,
                "questions_visees": ";".join(declaration.questions_visees),
                "portee": declaration.portee,
                "page": str(declaration.page),
                "origine": ORIGINE_EXTRAIT,
            }
        )
    return lignes


# Les colonnes qui font foi pour dire qu'un objet est reste le meme. Le reste
# peut bouger sans que l'identite soit en cause.
TEMOIN_DEVIS = ("entreprise", "montant_ttc")


def confronter(
    anciennes: list[dict[str, str]],
    nouvelles: list[dict[str, str]],
    *,
    cle: str,
    temoin: tuple[str, ...],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Rend les lignes a ecrire et les divergences constatees.

    Une correction humaine n'est jamais ecrasee: elle est conservee telle quelle
    et la lecture divergente est signalee a cote. C'est la decision back n.2 de
    la strategie, appliquee ici a un objet entier.
    """
    par_cle = {ligne[cle]: ligne for ligne in anciennes if ligne.get(cle)}
    a_ecrire: list[dict[str, str]] = []
    divergences: list[dict[str, str]] = []
    for ligne in nouvelles:
        ancienne = par_cle.get(ligne[cle])
        if ancienne is None:
            a_ecrire.append(ligne)
            continue
        ecarts = {
            champ: (ancienne.get(champ, ""), ligne.get(champ, ""))
            for champ in temoin
            if ancienne.get(champ, "") != ligne.get(champ, "")
        }
        if not ecarts:
            a_ecrire.append(ancienne if ancienne.get("origine") == ORIGINE_CORRIGE else ligne)
            continue
        divergences.append(
            {
                "cle": ligne[cle],
                "origine_conservee": ancienne.get("origine", ORIGINE_EXTRAIT),
                "ecarts": "; ".join(f"{c}: {a!r} -> {n!r}" for c, (a, n) in ecarts.items()),
            }
        )
        # Une correction humaine reste; une lecture precedente cede a la nouvelle.
        a_ecrire.append(ancienne if ancienne.get("origine") == ORIGINE_CORRIGE else ligne)
    disparues = sorted(set(par_cle) - {ligne[cle] for ligne in nouvelles})
    for cle_disparue in disparues:
        divergences.append(
            {
                "cle": cle_disparue,
                "origine_conservee": par_cle[cle_disparue].get("origine", ORIGINE_EXTRAIT),
                "ecarts": "objet absent de la nouvelle lecture",
            }
        )
    return a_ecrire, divergences


def _motifs_convocations(sans_texte, ancrage_degrade, ecartes, divergences) -> list[str]:
    """Ce que cette etape a PERDU, dans ses propres termes.

    Les nombres existaient deja dans le resume; ils n'atteignaient pas le
    verdict du passage, qui concluait donc au succes.
    """
    motifs: list[str] = []
    if sans_texte:
        motifs.append(
            f"{len(sans_texte)} convocations sans couche texte: rien n'y a ete lu"
        )
    if ancrage_degrade:
        motifs.append(
            f"{len(ancrage_degrade)} ancrages degrades sur page unique: "
            "l'ordre du jour n'est pas situe dans le document"
        )
    if divergences:
        motifs.append(f"{len(divergences)} divergences entre l'intitule et le corps")
    ecartes_total = sum(len(v) if isinstance(v, (list, tuple)) else int(v or 0) for v in (ecartes or {}).values())
    if ecartes_total:
        motifs.append(f"{ecartes_total} documents ecartes par nature")
    return motifs


def build_register(instance, run=None) -> dict[str, object]:
    """Ecrit une ligne par devis cite et par declaration, pour chaque convocation.

    Le magasin est le coffre SQLite de gouvernance, jamais un nouveau registre
    CSV: arbitrage Brice du 2026-09-03, inscrit dans `CLAUDE.md`. Les trois
    tables vivent dans le meme fichier que les resolutions, pour la raison qui a
    motive l'arbitrage - trois conversations ecrivant dans trois magasins
    differents reproduiraient le defaut numero un du produit.

    Un document sans couche texte ne produit rien et est compte a part: une
    convocation illisible est un fait a remonter, pas une absence de devis.
    """
    from ..core.common import read_csv

    try:
        store.store_path(instance)
    except store.GouvernanceStoreIndisponible as absence:
        # Instance anterieure a la bascule SQLite: on le nomme, on ne l'invente
        # pas, et on n'echoue pas en silence.
        if run is not None:
            run.log_run("WARN", f"convocation: coffre de gouvernance indisponible - {absence}")
        return {"coffre_non_declare": True, "convocations_lues": 0, "devis_cites": 0}

    _, documents = read_csv(instance.register("documents"))
    lignes_conv: list[dict[str, str]] = []
    devis: list[dict[str, str]] = []
    declarations: list[dict[str, str]] = []
    doc_ids: list[str] = []
    sans_texte: list[str] = []
    ancrage_degrade: list[str] = []
    resume_controles: dict[str, object] = {}

    ecartes: dict[str, list[str]] = {}
    for row in documents:
        if row.get("document_type") not in TYPES_CANDIDATS:
            continue
        pages = pages_du_document(instance, row)
        doc_id = row.get("doc_id", "")
        if not pages:
            sans_texte.append(doc_id)
            continue
        # C'est le CONTENU qui decide, pas le type enregistre. Un document qui
        # rapporte des votes appartient au lot resolutions, pas a celui-ci: l'y
        # traiter fabriquerait des projets a partir de decisions actees.
        nature = nature_du_document(pages, calibrer(pages))
        # On ecarte ce qui rapporte des votes et ce qui n'est pas lisible. On
        # n'exige pas d'etre certain qu'il s'agisse d'une convocation: un
        # document sans vote et sans enumeration reconnue ne rendra rien, et
        # rien est le bon resultat. Exiger `PROJETEE` ecartait au contraire des
        # convocations reelles au seul motif que leur ordre du jour est court.
        if nature.etat in (ETAT_CONSTATEE, ETAT_ILLISIBLE):
            ecartes.setdefault(nature.etat, []).append(doc_id)
            continue
        if len(pages) == 1:
            ancrage_degrade.append(doc_id)
        doc_ids.append(doc_id)
        convocation_id = _convocation_id(row)
        lue = parse_convocation(pages, ag_date=(row.get("suspected_date") or "")[:10])
        verifs = controles(lue)
        resume_controles[convocation_id] = verifs
        devis.extend(lignes_devis(lue, convocation_id=convocation_id, doc_id=doc_id))
        declarations.extend(lignes_declarations(lue, convocation_id=convocation_id, doc_id=doc_id))
        lignes_conv.append(
            {
                "convocation_id": convocation_id,
                "doc_id": doc_id,
                "ag_date": lue.ag_date,
                "points_ordre_du_jour": str(lue.points_ordre_du_jour),
                "sous_points": str(lue.sous_points_ordre_du_jour),
                "devis_cites": str(len(lue.devis)),
                "devis_quantifies": str(verifs["quantification"]["quantifies"]),
                "annexes_citees": ";".join(str(n) for n in lue.annexes_citees),
                "declarations": str(len(lue.declarations)),
                "extraction_complete": "oui" if verifs["extraction_complete"] else "non",
                "origine": ORIGINE_EXTRAIT,
            }
        )

    # La confrontation reste avant l'ecriture, et il n'existe pas d'autre porte:
    # ce n'est pas une verification que l'appelant peut sauter.
    anciens_devis = store.lire(instance, "devis_cites")
    devis, divergences = confronter(
        anciens_devis, devis, cle="devis_cite_id", temoin=TEMOIN_DEVIS
    )

    store.remplacer_pour_documents(instance, "convocations", CONVOCATION_FIELDS, lignes_conv, doc_ids)
    store.remplacer_pour_documents(instance, "devis_cites", DEVIS_CITE_FIELDS, devis, doc_ids)
    store.remplacer_pour_documents(
        instance, "declarations_ag", DECLARATION_FIELDS, declarations, doc_ids
    )

    resume = {
        "convocations_lues": len(lignes_conv),
        "convocations_sans_couche_texte": sans_texte,
        "ancrage_degrade_page_unique": ancrage_degrade,
        "motifs_alerte": _motifs_convocations(sans_texte, ancrage_degrade, ecartes, divergences),
        "devis_cites": len(devis),
        "declarations": len(declarations),
        "ecartes_par_nature": ecartes,
        "divergences": divergences,
        "controles": resume_controles,
    }
    if run is not None:
        run.log_run(
            "OK",
            f"convocation: {len(lignes_conv)} lue(s), {len(devis)} devis, {len(divergences)} divergence(s)",
        )
    return resume
