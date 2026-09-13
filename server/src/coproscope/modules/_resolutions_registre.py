"""Comptages, controle de coherence et ecriture du registre."""

from __future__ import annotations

import re

from pathlib import Path

from ._resolutions_calibrage import _blocs, _marqueurs
from ._resolutions_cloture import CLOTURE_LARGE_RE, ancres, issues_muettes
from ._resolutions_extraction import Resolution, parse_resolutions, sequence_gaps
from ._resolutions_qualification import fenetre_validite
# Les seuils de l'article 21 vivent desormais dans `_resolutions_seuils`: ce
# fichier depassait 600 lignes. Ils restent importables par ce chemin, parce que
# `pont_actes` et plusieurs tests les y prennent - deplacer un fichier ne doit
# pas casser un appelant qui n'a rien demande.
from ._resolutions_seuils import SEUILS_SUIVIS, seuils_en_vigueur  # noqa: F401
from .lisibilite import texte_utile
from ._resolutions_motifs import (
    ETAT_CONSTATEE,
    TETE_DOCUMENT,
    TITRE_PV_RE,
    ETAT_PROJETEE,
    ISSUE_ENONCEE_NON_LUE,
    ISSUE_NON_RECONNUE,
    MINIMUM_SERIE,
    ORIGINE_EXTRAIT,
    RESULTAT_PROJET,
    PAS_DE_VOTE,
    REPORTEE,
    RESOLUTION_FIELDS,
    SANS_ISSUE,
    SANS_OBJET,
    VOTE_SANS_FORMULE,
)

def coherence(text: str, resolutions: list[Resolution]) -> dict[str, object]:
    """L'extraction a-t-elle vu tout ce que le texte contient.

    Deux defauts distincts, que le simple ecart de comptage confondait:

    - une cloture hors de tout segment est une resolution PERDUE;
    - un segment portant plusieurs clotures est une resolution FUSIONNEE avec
      sa voisine, faute d'avoir vu la numerotation qui les separe.

    Un segment sans cloture n'est pas un defaut: c'est le cas normal d'une
    resolution non soumise au vote. Sur l'AGE du 21/02/2024, les resolutions 30
    a 34 sont dans ce cas apres le rejet de la 29, et l'audit manuel d'aout 2026
    confirme les 34 resolutions.
    """
    marques = _marqueurs(text)
    positions = [pos for _, pos in marques]
    clotures = len(ancres(text)[0])
    # Une issue enoncee et non lue est un defaut d'extraction au meme titre
    # qu'une cloture perdue: le document a parle de cette resolution, et le
    # registre n'en porte rien. Sans cette ligne, `extraction_complete` restait
    # vrai sur un proces-verbal dont AUCUNE issue n'avait ete comprise.
    non_lues = sum(1 for r in resolutions if r.resultat == ISSUE_ENONCEE_NON_LUE)
    if not positions:
        return {
            "clotures_dans_le_texte": clotures,
            "clotures_perdues": clotures,
            "segments_fusionnes": 0,
            "issues_enoncees_non_lues": non_lues,
            "extraction_complete": clotures == 0,
        }
    perdues = len(ancres(text[: positions[0]])[0])
    # **A l'echelle d'un bloc, on compte avec l'anneau LARGE, pas avec
    # `ancres`.** `ancres` choisit son anneau sur la SERIE, notion qui n'a pas
    # de sens dans un bloc: un bloc en porte une, ou il en porte deux et alors
    # deux resolutions ont fusionne. Preferer l'anneau strict a cette echelle
    # rend la fusion invisible des que la seconde formule est ecrite autrement.
    # Mesure du 2026-09-08: sur les douze proces-verbaux des deux cabinets, 491
    # segments, l'anneau large voit 7 fusions contre 6 - la septieme est reelle
    # (`Cette resolution sera reportee ... RESOLUTION 21.2 ... est devenue sans
    # objet`, deux votes dans un segment) et il n'ajoute aucun faux.
    fusionnes = sum(
        1 for bloc in _blocs(text, positions) if len(CLOTURE_LARGE_RE.findall(bloc)) > 1
    )
    return {
        "clotures_dans_le_texte": clotures,
        "clotures_perdues": perdues,
        "segments_fusionnes": fusionnes,
        "issues_enoncees_non_lues": non_lues,
        "extraction_complete": perdues == 0 and fusionnes == 0 and non_lues == 0,
    }


def summarize(resolutions: list[Resolution]) -> dict[str, object]:
    """Comptages verifiables, destines au controle et non a l'affichage."""
    return {
        "total": len(resolutions),
        "adoptees": sum(1 for r in resolutions if r.resultat == "ADOPTEE"),
        "rejetees": sum(1 for r in resolutions if r.resultat == "REJETEE"),
        "sans_objet": sum(1 for r in resolutions if r.resultat == SANS_OBJET),
        "reportees": sum(1 for r in resolutions if r.resultat == REPORTEE),
        "pas_de_vote": sum(1 for r in resolutions if r.resultat == PAS_DE_VOTE),
        "vote_sans_formule": sum(1 for r in resolutions if r.resultat == VOTE_SANS_FORMULE),
        "sans_issue": sum(1 for r in resolutions if r.resultat == SANS_ISSUE),
        # Le document DIT quelque chose et la chaine ne le lit pas. Compte a
        # part de `sans_issue`, ou il ne dit rien: confondre les deux est
        # exactement ce qui rendait un ecran a zero indiscernable d'un document
        # vide.
        "issue_enoncee_non_lue": sum(
            1 for r in resolutions if r.resultat == ISSUE_ENONCEE_NON_LUE
        ),
        "issue_non_reconnue": sum(
            1 for r in resolutions if r.resultat == ISSUE_NON_RECONNUE
        ),
        "passerelle_citee": sum(1 for r in resolutions if r.passerelle_citee),
        "passerelle_utilisee": sum(1 for r in resolutions if r.passerelle_utilisee),
        "trous_sequence": sequence_gaps(resolutions),
        "confiance_faible": sum(1 for r in resolutions if r.confiance == "faible"),
    }


def to_rows(
    resolutions: list[Resolution],
    *,
    ag_id: str,
    doc_id: str,
    date_ag: str = "",
    etat: str = ETAT_CONSTATEE,
    origine: str = ORIGINE_EXTRAIT,
) -> list[dict[str, str]]:
    """Lignes de registre pour une assemblee.

    `etat` distingue ce qui a ete vote de ce qui a seulement ete propose. Une
    resolution projetee ne porte JAMAIS d'issue ni de decompte de voix: la
    contrainte est appliquee ici plutot que laissee a la vigilance de
    l'appelant, parce que c'est exactement l'erreur qui faisait rendre quatorze
    "adoptees" a une convocation.
    """
    projet = etat == ETAT_PROJETEE
    rows: list[dict[str, str]] = []
    for res in resolutions:
        if date_ag and res.qualifications:
            res.valide_du, res.valide_au = fenetre_validite(date_ag, res.duree_mois)
        rows.append(
            {
                # Le degre entre dans l'identifiant, sinon 11.1 a 11.8 rendent
                # huit fois `AG-...-R011` et sept lignes disparaissent dans
                # `INSERT OR REPLACE` sans qu'aucune erreur ne soit levee.
                "resolution_id": (
                    f"{ag_id}-R{res.numero:03d}"
                    + (f".{int(res.sous_numero):02d}" if res.sous_numero else "")
                ),
                "ag_id": ag_id,
                "doc_id": doc_id,
                "numero": str(res.numero),
                "sous_numero": res.sous_numero,
                "objet": res.objet,
                "majorite_annoncee": res.majorite_annoncee,
                "passerelle_citee": "oui" if res.passerelle_citee else "non",
                "passerelle_utilisee": "oui" if res.passerelle_utilisee else "non",
                "majorite_appliquee": res.majorite_appliquee,
                "resultat": RESULTAT_PROJET if projet else res.resultat,
                "voix_relevees": "" if projet else ";".join(res.voix_relevees),
                "voix_pour": "" if projet else res.voix_pour,
                "voix_contre": "" if projet else res.voix_contre,
                "voix_abstention": "" if projet else res.voix_abstention,
                "base_voix": "" if projet else res.base_voix,
                "position": str(res.position),
                "numerotation": res.numerotation,
                "decision_actee": res.decision_actee,
                "qualifications": ";".join(res.qualifications),
                "duree_mois": "" if res.duree_mois is None else str(res.duree_mois),
                "montant_seuil": res.montant_seuil,
                "montant_intitule": res.montant_intitule,
                "duree_intitule": "" if res.duree_intitule is None else str(res.duree_intitule),
                "divergences": " | ".join(res.divergences),
                "valide_du": res.valide_du,
                "valide_au": res.valide_au,
                "etat": etat,
                "origine": origine,
                "confiance": res.confiance,
            }
        )
    return rows


def parse_file(path: Path) -> list[Resolution]:
    return parse_resolutions(Path(path).read_text(encoding="utf-8", errors="replace"))


def _text_of(instance, row: dict[str, str]) -> str:
    """Texte deja extrait du document, ou chaine vide s'il n'y en a pas.

    Les marqueurs `===== PAGE n =====` sont retires: ils sont ecrits meme pour
    une page qui ne livre rien, si bien qu'un scan de 27 pages produit 584
    caracteres et passait ici pour un document lu. Voir `lisibilite`.
    """
    text_path = row.get("text_path")
    if not text_path:
        return ""
    path = instance.root("workspace") / text_path
    if not path.exists():
        return ""
    return texte_utile(path.read_text(encoding="utf-8", errors="ignore"))


def _ag_id(row: dict[str, str]) -> str:
    date = (row.get("suspected_date") or "").strip()
    return f"AG-{date}" if date else f"AG-{row.get('doc_id', 'INCONNU')}"


NATURE_PV = "PV_AG"
NATURE_CONVOCATION = "CONVOCATION"
NATURE_DEMANDE = "DEMANDE_INSCRIPTION"
NATURE_AUTRE = "AUTRE"

#: Le document VOTE, en serie, et la chaine ne sait pas lire comment. C'est la
#: nature qui manquait, et son absence produisait le pire des deux mondes: un
#: proces-verbal redige autrement portait des numeros de resolution sans aucune
#: formule reconnue, donc il tombait dans la branche `CONVOCATION` et sortait du
#: registre comme un ordre du jour. Un vote accompli disparaissait sous
#: l'etiquette d'un vote a venir, sans un compteur.
NATURE_PV_ISSUES_NON_LUES = "PV_AG_ISSUES_NON_LUES"

# Sous ce nombre d'ancres, on n'a pas affaire a un document d'assemblee: une
# lettre ou une note peuvent citer une resolution sans en porter la serie.
MINIMUM_ANCRES = MINIMUM_SERIE

# --------------------------------------------------------------------------
# L'axe: comment un document d'assemblee se nomme lui-meme
# --------------------------------------------------------------------------
#
# **Axe de generalisation.** Ce qui varie d'un cabinet a l'autre, c'est la
# formule de cloture citee dans le CORPS. Ce qui ne varie pas, c'est qu'une
# piece d'assemblee se declare en TETE: le decret 67-223 fait dresser un
# proces-verbal (art. 17), porter un ordre du jour a la convocation (art. 9 et
# 11), et notifier par un coproprietaire une demande d'inscription de questions
# a cet ordre du jour (art. 10). Trois actes, trois auto-declarations.
#
# **L'invariant tenu.** Le corps d'une piece peut CITER n'importe quelle
# formule; la tete dit ce que la piece EST. Une demande d'inscription qui
# redige le texte exact qu'elle veut faire voter ecrit mot pour mot « cette
# resolution est adoptee a la majorite de l'article 24 » - et `CLOTURE_RE` la
# lit comme un vote accompli. Mesure du 2026-09-04: une demande de cinq
# questions rend `PV_AG`, cinq resolutions, cinq `ADOPTEE`, qui remontent a
# l'ecran en actes CONSTATES. Aucune exception, aucun compteur.
#
# **Hors des valeurs observees.** Un cabinet qui n'ecrirait pas cette
# declaration en tete retombe sur la regle des cloture en serie: la degradation
# est celle d'aujourd'hui, pas pire. Et la fenetre est bornee a la tete
# precisement pour qu'un proces-verbal qui VOTE sur une demande d'inscription -
# cas reel - reste un proces-verbal.


#: Une piece qui se declare demande d'inscription a l'ordre du jour redige
#: les projets qu'elle veut faire voter, formule de cloture comprise. La lire
#: comme un proces-verbal fabrique des adoptions a partir d'une lettre.
DEMANDE_INSCRIPTION_RE = re.compile(
    r"(?i)(?:demande|demandent?|sollicite|notification)[^.\n]{0,80}"
    r"inscription[^.\n]{0,80}ordre\s+du\s+jour"
    r"|inscription\s+(?:de\s+|des\s+)?(?:questions?|r[ée]solutions?|points?)"
    r"[^.\n]{0,60}ordre\s+du\s+jour"
)


def nature_assemblee(text: str) -> str:
    """Nature du document lue dans le TEXTE, jamais dans son etiquette.

    Le classement des documents n'est pas fiable, et l'etiquette etait la seule
    porte d'entree de ce module. Mesure du 2026-09-03 sur `tilleuls_test`:
    parmi 15 documents etiquetes `PV_AG`, onze etaient des fichiers de travail
    de CoproScope lui-meme - `matrice_risques.csv`, `journal_decisions.md` -
    tandis que trois quarts du seul proces-verbal reel etaient ailleurs, un
    morceau etant meme classe `Devis`. Le meme registre annonce 108
    `Convocation_AG` pour une copropriete qui a tenu huit assemblees.

    Le nom de fichier ne vaut pas mieux: `2023-06-19_AG_PV_Convoc.pdf` ne
    contient aucune occurrence de "adopte", "rejete" ou "refuse".

    Le contenu, lui, se reconnait seul:

    - des formules de cloture en serie = le vote a eu lieu, c'est un
      proces-verbal;
    - une serie de numeros de resolution SANS aucune cloture = les projets sont
      la mais le vote n'a pas eu lieu, c'est une convocation.

    Une convocation ne rend rien ici: elle porte des projets, et fabriquer des
    adoptions a partir d'elle est precisement le defaut que ce module evite.
    """
    if "solution" not in text and "SOLUTION" not in text:
        return NATURE_AUTRE
    tete = text[:TETE_DOCUMENT]
    if DEMANDE_INSCRIPTION_RE.search(tete) and not TITRE_PV_RE.search(tete):
        # Une demande d'inscription redige les projets qu'elle veut faire
        # voter, formule de cloture comprise. Les compter comme des votes
        # accomplis fabrique des adoptions a partir d'une lettre: c'est le
        # defaut exact que ce module existe pour empecher, dit une piece plus
        # loin dans la chaine. On rend une nature NOMMEE et non `AUTRE`, pour
        # que le resume puisse dire ce qui a ete ecarte et pourquoi.
        return NATURE_DEMANDE
    if len(ancres(text)[0]) >= MINIMUM_ANCRES:
        return NATURE_PV
    marques = _marqueurs(text)
    # Avant de dire "convocation", verifier que le document ne VOTE pas. Une
    # convocation porte des projets et n'enonce pas d'issue: mesure du
    # 2026-09-08 sur le second cabinet, 77 resolutions projetees pour 3
    # participes d'issue, soit 4 % des segments. Un proces-verbal dont la
    # redaction n'est pas lue en porte un par resolution. C'est ce rapport, et
    # non un mot du vocabulaire, qui separe les deux.
    if issues_muettes(text, marques, [r.resultat for r in parse_resolutions(text)])["muet"]:
        return NATURE_PV_ISSUES_NON_LUES
    if len(marques) >= MINIMUM_ANCRES:
        return NATURE_CONVOCATION
    return NATURE_AUTRE


#: Les colonnes qui forment la cle primaire d'une ligne de registre, telles que
#: la couche de stockage les declare. Repetees ici parce que ce module doit
#: savoir CE QUI SE PERD avant de le confier a la base, et pas parce qu'il
#: prendrait la main sur le schema.
CLES_RESOLUTIONS = ("resolution_id", "etat", "origine")


def collisions_de_cle(
    lignes: list[dict[str, str]],
    cles: tuple[str, ...] = CLES_RESOLUTIONS,
) -> dict[tuple[str, ...], int]:
    """Les cles primaires revendiquees par plus d'une ligne construite.

    **Une collision de cle n'est pas une erreur de la base: c'est une perte de
    donnee silencieuse.** `INSERT OR REPLACE` garde la derniere ligne et jette
    les precedentes sans rien lever. Mesure du 2026-09-04 sur l'assemblee de
    fevrier 2026: un document produit neuf resolutions dont deux portent le
    numero 3 - une ligne parasite decrivant un lot, et le vote sur le
    non-renouvellement du mandat du syndic. Les deux fabriquent la meme cle, le
    journal ecrivait `resolutions: 9`, et le coffre en contenait huit.

    Cette fonction ne tranche pas laquelle survit - ce n'est pas son role. Elle
    NOMME la cle en collision pour que le resume la rapporte au lieu de compter
    des lignes qui n'existent plus.
    """
    vues: dict[tuple[str, ...], int] = {}
    for ligne in lignes:
        cle = tuple(str(ligne.get(nom, "") or "") for nom in cles)
        vues[cle] = vues.get(cle, 0) + 1
    return {cle: n for cle, n in vues.items() if n > 1}


def build_register(instance, run) -> dict[str, object]:
    """Ecrit une ligne par resolution pour chaque proces-verbal lu.

    Le tri se fait sur le CONTENU des documents, pas sur leur etiquette
    `document_type` - voir `nature_assemblee` pour les mesures qui ont impose
    ce changement.

    Les documents sans couche texte ne produisent rien et sont comptes a part:
    un PV illisible est un fait a remonter, pas une absence de resolutions.
    """
    import sqlite3

    from ..core.common import read_csv
    from ..vault.gouvernance_store import (
        GouvernanceStoreIndisponible,
        remplacer_pour_documents,
    )

    _, docs = read_csv(instance.register("documents"))
    rows: list[dict[str, str]] = []
    lus = 0
    sans_texte = 0
    sans_resolution = 0
    incomplets: list[tuple[str, int]] = []
    doc_ids: list[str] = []
    convocations = 0
    demandes: list[str] = []
    issues_non_lues: list[str] = []
    verdicts_issues: list[str] = []
    etiquetes_pv = 0
    ecartes_malgre_etiquette: list[str] = []
    for doc in docs:
        text = _text_of(instance, doc)
        etiquette_pv = doc.get("document_type") == "PV_AG"
        etiquetes_pv += 1 if etiquette_pv else 0
        if not text.strip():
            # Un document sans texte n'est compte comme PV illisible que si son
            # etiquette le pretendait: sinon on compterait toute la copropriete.
            sans_texte += 1 if etiquette_pv else 0
            continue
        nature = nature_assemblee(text)
        if nature == NATURE_CONVOCATION:
            # Elle porte des projets, jamais des votes. La conversation
            # convocations en a la charge; ici on la compte et on passe.
            convocations += 1
            continue
        if nature == NATURE_DEMANDE:
            # Une demande d'inscription a l'ordre du jour redige les projets
            # qu'elle veut faire voter, formule de cloture comprise. Elle etait
            # lue comme un proces-verbal et rendait des resolutions ADOPTEES
            # qui n'avaient jamais ete soumises au vote. Ecartee, et NOMMEE.
            demandes.append(doc.get("doc_id", ""))
            continue
        if nature not in (NATURE_PV, NATURE_PV_ISSUES_NON_LUES):
            if etiquette_pv:
                ecartes_malgre_etiquette.append(doc.get("doc_id", ""))
            continue
        found = parse_resolutions(text)
        # **Le diagnostic ne depend PAS de la nature retenue.** Un document
        # peut porter quatre formules lisibles et quarante-six illisibles: il
        # est alors classe `PV_AG` sans detour par la nature de secours, et une
        # alerte branchee sur la seule nature ne se declenche jamais. Mesure du
        # 2026-09-08 sur un proces-verbal reel dont on avait reecrit la formule:
        # 55 resolutions, 46 issues non lues, run `OK`. Le diagnostic est donc
        # pose sur TOUT document dont on lit des resolutions.
        #
        # Les lignes sont ecrites dans les deux cas: numeros et objets sont
        # lisibles, seule l'issue manque, et chaque ligne la porte nommee
        # `ISSUE_ENONCEE_NON_LUE` avec une confiance faible. Les jeter aurait
        # rendu zero, c'est-a-dire l'ecran d'un document vide.
        diagnostic = issues_muettes(
            text, _marqueurs(text), [r.resultat for r in found]
        )
        if diagnostic["muet"]:
            issues_non_lues.append(doc.get("doc_id", ""))
            verdicts_issues.append(diagnostic["verdict"])
        if not found:
            sans_resolution += 1
            continue
        lus += 1
        doc_ids.append(doc.get("doc_id", ""))
        coh = coherence(text, found)
        if not coh["extraction_complete"]:
            # `coherence` distingue depuis le 02/09 les clotures PERDUES des
            # segments FUSIONNES; l'ancienne cle `ecart` n'existe plus. Le
            # defaut ne se voyait pas: aucun document du corpus etiquete n'avait
            # d'extraction incomplete, donc cette ligne n'etait jamais atteinte.
            incomplets.append(
                (doc.get("doc_id", ""), coh["clotures_perdues"] + coh["segments_fusionnes"])
            )
        rows.extend(
            to_rows(
                found,
                ag_id=_ag_id(doc),
                doc_id=doc.get("doc_id", ""),
                date_ag=(doc.get("suspected_date") or "")[:10],
            )
        )

    # Ce que la cle primaire va jeter. `INSERT OR REPLACE` garde la derniere
    # ligne d'une cle et efface les precedentes sans rien lever: le journal
    # annoncait le nombre de lignes CONSTRUITES, et le coffre en contenait
    # moins. Mesure du 2026-09-04: neuf resolutions construites sur l'assemblee
    # de fevrier 2026, huit stockees, la ligne perdue etant l'une des deux qui
    # portaient le numero 3. On compte ce qui est stocke, et on NOMME ce qui a
    # ete ecrase - une perte silencieuse est pire qu'une perte annoncee.
    ecrasees = collisions_de_cle(rows)
    try:
        soumises = remplacer_pour_documents(instance, RESOLUTION_FIELDS, rows, doc_ids)
    except GouvernanceStoreIndisponible as exc:
        # Le coffre local n'est pas declare: on le dit, on ne l'invente pas.
        if run is not None:
            run.log_run("WARN", f"resolutions: {exc}")
        return {"coffre_non_declare": True, "resolutions": 0}
    except sqlite3.OperationalError as exc:
        # Le cas mesure est `no such column`: le coffre porte une table
        # `resolutions` ecrite avant qu'une colonne n'entre dans le modele, et
        # `CREATE TABLE IF NOT EXISTS` ne dit rien d'une table qui existe deja
        # avec MOINS de colonnes. Elargir une table existante appartient a la
        # couche de stockage, pas a ce module. Ce qui appartient a ce module,
        # c'est de ne pas laisser l'erreur devenir un registre vide: le lecteur
        # rattrape `OperationalError` et rend une liste, si bien que 173
        # resolutions se lisaient « aucune resolution ». On la NOMME.
        if run is not None:
            run.log_run("WARN", f"resolutions: ecriture refusee par le coffre - {exc}")
        return {"coffre_refuse_l_ecriture": str(exc), "resolutions": 0}
    resume = {
        "pv_lus": lus,
        "pv_sans_couche_texte": sans_texte,
        "pv_sans_resolution_detectee": sans_resolution,
        # Ce qui a survecu a la cle primaire, pas ce qui a ete soumis. Le
        # calcul est fait ici et non dans la couche de stockage: le nombre de
        # lignes ecrasees se deduit des lignes construites, sans rien demander
        # de plus a la base.
        "resolutions": soumises - sum(n - 1 for n in ecrasees.values()),
        "resolutions_construites": len(rows),
        "resolutions_ecrasees": sorted(
            f"{cle[0]} ({n} lignes pour une seule cle)" for cle, n in ecrasees.items()
        ),
        "pv_extraction_incomplete": [d for d, _ in incomplets],
        "convocations_ecartees": convocations,
        # Ecartees parce qu'elles se declarent demandes d'inscription en tete:
        # elles portent des projets rediges, pas des votes accomplis.
        "demandes_inscription_ecartees": demandes,
        # Le document VOTE et la chaine ne sait pas lire sa redaction. Ses
        # resolutions sont ecrites avec une issue nommee non lue, et le run
        # passe en WARN: c'est la ligne qui remplace le zero muet.
        "pv_issues_non_lues": issues_non_lues,
        "verdicts_issues_non_lues": verdicts_issues,
        # Ecart entre ce que dit l'etiquette et ce que dit le contenu. Non nul
        # = le classement des documents merite d'etre repris, et le dire est
        # plus utile que de le corriger en silence.
        "etiquetes_pv_ag": etiquetes_pv,
        "etiquetes_pv_sans_resolution": ecartes_malgre_etiquette,
    }
    resume["motifs_alerte"] = _motifs_alerte(resume)
    if run is not None:
        niveau = "WARN" if resume["motifs_alerte"] else "OK"
        cause = " ; ".join(resume["motifs_alerte"])
        entete = f"resolutions ({cause})" if cause else "resolutions"
        run.log_run(niveau, f"{entete}: {resume}")
    return resume


def _motifs_alerte(resume: dict[str, object]) -> list[str]:
    """Ce qui a ete PERDU pendant ce run, nomme et compte.

    Le niveau ne passait en `WARN` que sur une collision de cle. Un document
    ecarte comme demande d'inscription - donc, quand la lecture du titre se
    trompe, un proces-verbal entier - etait annonce au meme niveau qu'un run
    sans incident: le resume nommait la piece, le niveau disait que tout allait
    bien, et c'est le niveau qui remonte. Le journal porte desormais la cause,
    pour qu'un `WARN` n'oblige pas a relire tout le resume.

    **Ce qui n'entre PAS ici, et pourquoi.** `etiquetes_pv_sans_resolution`
    compte les documents que l'etiquette `PV_AG` annonce et que le contenu
    dement. Sur le corpus de reference, onze documents sur quinze sont dans ce
    cas - des fichiers de travail de CoproScope lui-meme. Les compter comme une
    alerte ferait passer chaque run en `WARN`, et un niveau toujours allume ne
    dit plus rien. Ce sont deja des faits nommes dans le resume; l'ecart entre
    etiquette et contenu est un defaut de classement connu, pas une perte de ce
    run.
    """
    motifs: list[str] = []
    ecrasees = resume.get("resolutions_ecrasees") or []
    if ecrasees:
        motifs.append(f"{len(ecrasees)} cles de resolution ecrasees")
    demandes = resume.get("demandes_inscription_ecartees") or []
    if demandes:
        motifs.append(f"{len(demandes)} demandes d'inscription ecartees")
    muets = resume.get("pv_issues_non_lues") or []
    if muets:
        # C'est le motif qui manquait. Un proces-verbal dont aucune issue n'est
        # lue rendait un run `OK` et un ecran a zero; le niveau est ce qui
        # remonte, et il disait que tout allait bien.
        motifs.append(
            f"{len(muets)} proces-verbaux enoncent des issues que la chaine ne lit pas"
        )
    return motifs
