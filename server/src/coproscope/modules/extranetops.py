"""Journal d'observation d'un extranet de syndic - facade du module.

Sert `RM-2026-0091`. Le referentiel de conformite repond a *"le syndic
publie-t-il ce qu'il doit ?"*; ce journal repond a *"qu'est-ce qui a change, et
quand ?"*. La seconde question a une propriete que la premiere n'a pas: elle
produit une preuve qu'aucun audit ponctuel ne peut produire, parce qu'un audit
est une photo et qu'une piece presente en mars et absente en juin ne laisse
aucune trace dans une photo prise en juin.

----------------------------------------------------------------------
Ce que ce module fait, et ce qu'il ne fera jamais
----------------------------------------------------------------------

Il **lit** du HTML deja obtenu, il **enregistre** ce qui a ete vu et ou l'on a
regarde, et il **derive** les changements entre deux passages.

Il n'emet aucune requete reseau. C'est deliberé: la ligne rouge du chantier dit
que tout ce qui sort vers le syndic passe par un clic humain, et la maniere la
plus sure de tenir cette regle est que la couche qui sait raisonner ne sache pas
parler. Le composant qui parcourt - une extension de navigateur - reste
exterieur et ne fait que fournir du HTML.

Il n'ecrit jamais d'auteur. Trois sources de changement se melangent sur un
extranet de copropriete, et l'extranet n'expose pas qui a agi.
"""

from __future__ import annotations

import base64
import binascii
import hmac
from typing import Any, Sequence

from . import _extranet_conformite as conformite_mod
from . import _extranet_depenses as depenses
from . import _extranet_echange as echange
from . import _extranet_journal as journal
from . import _extranet_releve as releve
from . import _extranet_store as store
from ._extranet_adaptateur import PROFILS, ProfilEditeur, lire_index
from . import _extranet_referentiel as referentiel_mod
from ._extranet_schema import ORIGINE_EXTRAIT

__all__ = [
    "SelInterdit",
    "profils",
    "referentiel",
    "conformite",
    "depenses_sans_justificatif",
    "enregistrer_releve",
    "exporter_passage",
    "recouper",
    "enregistrer_index",
    "comparer_passages",
    "dernier_ecart",
    "etat",
]


def profils() -> dict[str, ProfilEditeur]:
    """Les editeurs connus."""
    return dict(PROFILS)


def enregistrer_index(
    instance: Any,
    html: str,
    passage_id: str,
    *,
    profil: str = "coprodirecte",
    espace: str = "",
    debut: str = "",
    fin: str = "",
    rubriques_visitees: Sequence[str] | None = None,
    remplacer: bool = False,
) -> dict[str, int]:
    """Analyse un index et enregistre le passage. Rend les comptes ecrits.

    `passage_id` et les horodatages sont fournis par l'appelant plutot que
    calcules ici: un journal doit pouvoir etre rejoue, importe et teste, et une
    horloge cachee dans la couche de donnees rend tout cela impossible.
    """
    if profil not in PROFILS:
        raise ValueError(
            f"Profil d'editeur inconnu: {profil!r}. Connus: {sorted(PROFILS)}. "
            "Un editeur s'ajoute par un profil, pas par une exception dans le code."
        )
    lu = lire_index(
        html, PROFILS[profil], passage_id, rubriques_visitees=rubriques_visitees
    )
    entete = {
        "passage_id": passage_id,
        "editeur": profil,
        "espace": espace,
        "debut": debut,
        "fin": fin,
        "profil": profil,
        "doc_id": "",
        "origine": ORIGINE_EXTRAIT,
    }
    return store.ecrire_passage(
        instance, entete, lu["rubriques"], lu["pieces"], remplacer=remplacer
    )


def enregistrer_releve(
    instance: Any,
    charge: Any,
    passage_id: str,
    *,
    profil: str = "coprodirecte",
    remplacer: bool = False,
) -> dict[str, int]:
    """Enregistre un releve transmis par l'extension de navigateur.

    L'extension rend une structure neutre; l'interpretation - cles, couverture,
    verdicts - vit ici, ou elle est testee. Deux implantations de la meme
    logique divergeraient, et la divergence se verrait le jour ou l'on en a le
    plus besoin.
    """
    if profil not in PROFILS:
        raise ValueError(f"Profil d'editeur inconnu: {profil!r}.")
    converti = releve.convertir(charge, PROFILS[profil], passage_id)
    return store.ecrire_passage(
        instance,
        converti["passage"],
        converti["rubriques"],
        converti["pieces"],
        remplacer=remplacer,
    )



class SelInterdit(ValueError):
    """Le sel propose pour un export est celui des alias de l'instance.

    CoproScope emploie deux sels, et **leurs buts sont opposes**. Le sel des
    alias (`sel_alias.key`, BiffageOps) est propre a une instance, precisement
    pour que deux coffres de coproprietaires voisins ne produisent JAMAIS le
    meme alias pour la meme personne. Le sel d'echange est partage entre les
    voisins d'une meme copropriete, precisement pour que leurs empreintes
    COINCIDENT.

    Employer le premier a la place du second ne produirait aucune erreur
    visible: il rendrait zero concordance, que deux personnes liraient comme un
    desaccord entre elles. Employer le second a la place du premier rendrait
    deux coffres chainables et ferait tomber la garantie que BiffageOps existe
    pour tenir. Les deux fautes sont silencieuses; c'est pourquoi elles sont
    refusees ici plutot que documentees.
    """


def _refuser_sel_d_instance(instance: Any, sel: str) -> None:
    """Refuse un sel d'echange qui serait le sel d'alias de cette instance.

    Cette verification vit ici et non dans `_extranet_echange`, parce que c'est
    la seule couche qui voit **a la fois** l'instance et le sel - et que le
    module d'echange doit rester ignorant du coffre.

    `create=False` n'est pas un detail: sans lui, exporter un journal
    d'extranet **creerait** un sel d'alias sur une instance qui n'en a pas, et
    fabriquerait donc en silence le materiau d'une pseudonymisation que
    personne n'a demandee.
    """
    if not sel:
        return
    try:
        from . import biffageops
    except Exception:  # noqa: BLE001 - BiffageOps est optionnel
        return
    try:
        alias = biffageops.load_corpus_salt(instance, create=False)
    except FileNotFoundError:
        return  # pas de sel d'alias sur cette instance: rien a confondre
    except Exception:  # noqa: BLE001 - un sel illisible n'est pas notre sujet
        return
    # Normaliser AVANT de comparer. Une relecture adverse du 2026-09-07 a
    # montre que la garde se contournait par le geste le plus banal qui soit:
    # `sel_alias.key` porte un en-tete puis une ligne base64, et une copie de
    # cette ligne emporte presque toujours son saut de ligne. `validate=True`
    # refusait alors le decodage, l'erreur etait avalee, et la garde laissait
    # passer. Un espace, une majuscule ou l'ecriture hexadecimale faisaient de
    # meme.
    nu = sel.strip()
    candidats = [sel.encode("utf-8"), nu.encode("utf-8")]
    for forme in (nu, nu.replace(" ", "").replace("\n", "")):
        try:
            candidats.append(base64.b64decode(forme, validate=True))
        except (ValueError, binascii.Error):
            pass
        try:
            candidats.append(bytes.fromhex(forme))
        except ValueError:
            pass
    for candidat in candidats:
        if len(candidat) == len(alias) and hmac.compare_digest(candidat, alias):
            raise SelInterdit(
                "Ce secret est celui des alias de cette instance. Il ne peut pas "
                "servir a l'echange entre voisins: il est propre a votre coffre, "
                "et son role est justement que deux coffres ne produisent jamais "
                "la meme valeur pour la meme personne. Le secret d'echange est "
                "l'inverse: il se partage entre voisins pour que vos empreintes "
                "coincident. Choisissez-en un autre, decide par le conseil "
                "syndical."
            )
    # L'empreinte du sel est PUBLIEE dans les rapports de pseudonymisation.
    # S'en servir comme secret d'echange rendrait l'export attaquable par
    # dictionnaire - l'oracle que tout ce module sert a ecarter. La comparaison
    # ignore la casse et les espaces, parce qu'un copier-coller les emporte.
    if nu.lower() == biffageops.corpus_salt_fingerprint(alias).lower():
        raise SelInterdit(
            "Ce secret est l'empreinte du sel d'alias de cette instance, publiee "
            "dans les rapports de pseudonymisation. Un secret d'echange ne doit "
            "figurer dans aucun fichier."
        )

def exporter_passage(
    instance: Any, passage_id: str, *, sel: str, observateur: str
) -> dict[str, Any]:
    """Le paquet transmissible d'un passage, pour recoupement entre voisins.

    Ne sortent que des empreintes salees, des codes de rubrique et des dates.
    Aucun libelle, aucun nom de fichier, aucune adresse de piece: un extranet de
    copropriete porte des donnees de tiers, et un fichier d'echange se retrouve
    toujours quelque part.
    """
    _refuser_sel_d_instance(instance, sel)
    lu = store.lire_passage(instance, passage_id)
    return echange.exporter(
        lu["passage"], lu["rubriques"], lu["pieces"], sel=sel, observateur=observateur
    )


def referentiel() -> tuple[Any, ...]:
    """Les 18 obligations de la liste minimale du decret 2019-502.

    Chacune porte son fondement avec son identifiant `LEGIARTI`, la version lue
    et la date de lecture. C'est ce que `docs/referentiel_conformite_extranet_v1.md`
    declare, transcrit en donnee; un test verifie que les deux ne derivent pas.
    """
    return referentiel_mod.LISTE_MINIMALE


def conformite(
    instance: Any,
    passage_id: str,
    *,
    rattachements: Any = None,
    attendus: Any = None,
    sans_objet: Any = (),
) -> dict[str, Any]:
    """Ce que le decret exige, confronte a ce qui a ete observe au passage.

    Ne rend **aucun verdict de conformite**: l'observation ne lit pas les
    pieces, et une rubrique peut porter le bon nombre de documents sans que ce
    soient les bons. Chaque etat voyage donc avec ce qui reste a verifier a la
    main.

    Sans rattachement declare, les dix-huit obligations ressortent
    `NON_RATTACHE` et le rendu ne contient aucun manquement. C'est voulu: le
    rattachement d'une obligation a une rubrique d'editeur n'est pas
    observable, aucune page ne citant le decret.
    """
    lu = store.lire_passage(instance, passage_id)
    etats = conformite_mod.etat_par_obligation(
        {"rubriques": lu["rubriques"]},
        rattachements=rattachements,
        attendus=attendus,
        sans_objet=sans_objet,
    )
    return {
        "passage": lu["passage"],
        "etats": etats,
        "manques": conformite_mod.manques(etats),
        "resume": conformite_mod.resume(etats),
    }

def depenses_sans_justificatif(html: str) -> dict[str, Any]:
    """Les lignes de depenses qu'aucune piece jointe n'appuie, sur cette page.

    C'est le seul manque que l'observation sait produire **sans qu'un humain
    ait rien declare**: il ne demande ni rattachement, ni nombre attendu. Il
    suffit de lire la page.

    C'est un **constat**, jamais un manquement. Une ligne peut etre appuyee par
    une piece que l'extranet ne publie pas, ou relever d'une categorie qui n'en
    appelle pas. La formulation utile est la question - *ces lignes n'ont pas
    de piece jointe en ligne, sur quoi reposent-elles ?* - et non l'accusation.

    Le total sert de perimetre: un compte de lignes sans justificatif, sans le
    nombre de lignes lues, se lit comme une couverture complete.

    Les lignes rendues portent les libelles et les montants tels que la page
    les affiche. Ce rendu est donc **local**: il n'est pas un paquet d'echange,
    et rien ici ne doit partir vers un voisin sans passer par les empreintes
    salees de `exporter_passage`.
    """
    lu = depenses.lire_depenses(html, PROFILS["coprodirecte"], "P0")
    liens = lu.get("liens", [])
    sans = depenses.lignes_sans_facture(liens)
    return {
        "lignes_lues": len(liens),
        "sans_justificatif": len(sans),
        "cles_de_charges": sorted(
            {l.get("cle_charge", "") for l in sans if l.get("cle_charge")}
        ),
        "lignes": sans,
    }

def recouper(mien: dict[str, Any], sien: dict[str, Any]) -> dict[str, Any]:
    """Confronte deux observations de la meme copropriete, faites en parallele.

    Un journal seul est une allegation; deux journaux concordants sont une
    preuve. Et un desaccord n'est pas une panne: c'est le constat que l'extranet
    ne sert pas la meme chose aux deux comptes.
    """
    return echange.recouper(mien, sien)


def comparer_passages(instance: Any, avant: str, apres: str) -> dict[str, Any]:
    """Les constats entre deux passages nommes, tries du plus grave au plus anodin."""
    resultat = journal.comparer(
        store.lire_passage(instance, avant), store.lire_passage(instance, apres)
    )
    resultat["constats"] = journal.trier(resultat["constats"])
    return resultat


def dernier_ecart(instance: Any) -> dict[str, Any]:
    """Les constats entre les deux passages les plus recents.

    Avec un seul passage enregistre, rend une structure vide portant
    `reference_seule`. **Un premier passage ne produit aucun constat**: il
    constitue la reference. Sans cette precaution, un ecran presenterait la
    totalite de l'index comme autant d'ajouts, le jour de l'installation.
    """
    avant, apres = store.deux_derniers(instance)
    if not apres:
        return {"aucun_passage": True, "constats": [], "comptes": {}}
    if not avant:
        return {
            "reference_seule": True,
            "passage_apres": apres,
            "constats": [],
            "comptes": {},
        }
    return comparer_passages(instance, avant, apres)


def etat(instance: Any) -> dict[str, Any]:
    """De quoi remplir un ecran sans le faire mentir.

    Distingue les trois situations que le blueprint impose de ne pas confondre:
    pas de coffre, coffre vide, aucun resultat. Un ecran qui les melange affiche
    un vide silencieux, et l'utilisateur conclut que l'outil est casse.
    """
    try:
        passages = store.lister_passages(instance)
    except store.GouvernanceStoreIndisponible:
        return {
            "disponible": False,
            "motif": "Le coffre local n'est pas declare pour cette instance.",
            "passages": [],
        }
    return {
        "disponible": True,
        "motif": "",
        "passages": passages,
        "nb_passages": len(passages),
    }
