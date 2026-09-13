"""Les etats explicites de l'ecran: jamais d'ecran vide silencieux.

Zero rupture et zero preuve produisent le meme ecran vide. Les distinguer est la
difference entre un outil de controle et un outil qui rassure a tort - c'est le
quatrieme cas du blueprint, le plus important et le plus facile a rater.

Un sixieme cas s'ajoute aux cinq du blueprint: **le modele relationnel existe et
rien ne l'alimente**. Sur une instance qui porte 173 resolutions au registre,
l'ecran trouverait alors zero acte, et le taire ferait dire a l'ecran
`aucune rupture` la ou il faut lire `aucune lecture n'a encore ete versee`.

**Ce paragraphe disait faux, et la correction est la lecon.** Il affirmait, au
2026-09-04, que les tables `actes_autorisation`, `liens_gouvernance` et
`dossiers_depense` etaient creees par `_actes_store.preparer` et qu'*aucun code
du produit n'y ecrit hors des tests*. La mesure du 2026-09-09, par observation
SQLite d'une absorption complete sur `913d744`, refute la phrase pour deux des
trois: `pont_actes.verser` ecrit `actes_autorisation` **et** `liens_gouvernance`
a chaque passage de `run_gouvernance_sequence`. Seule `dossiers_depense` reste
sans chemin. La phrase etait vraie quand elle a ete ecrite, le pont l'a rendue
fausse, et rien ne l'a signale pendant cinq jours parce qu'une prose ne se
verifie pas. C'est pour cela que la liste des tables sans chemin vit desormais
dans `_ecrans_promesses`, ou une garde la compare a ce que la chaine ecrit
reellement.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date
from typing import Any

from ..modules import actes_autorisation as A
from ..vault import gouvernance_store
from . import _ecrans_promesses as _promesses
from ._controle_gouvernance_acces_piece import acces_aux_pieces

COFFRE_ABSENT = "coffre_absent"
COFFRE_VIDE = "coffre_vide"
MODELE_NON_ALIMENTE = "modele_non_alimente"
MODELE_VIDE = "modele_vide"
PRET = "pret"

#: La seule table du coffre qui sache donner un nom lisible a une piece citee.
#: Elle est ecrite par le registre des convocations et non par le modele
#: d'actes: elle peut donc etre absente, et son absence n'est pas une erreur.
TABLE_CONVOCATIONS = "convocations"


def _compter(chemin: Any, table: str) -> int | None:
    """Le nombre de lignes d'une table, ou `None` si la table n'existe pas.

    La distinction compte: une table absente dit `rien n'a jamais ete ecrit
    ici`, une table vide dit `l'ecriture a eu lieu et n'a rien produit`. Les
    confondre est exactement le defaut T10.
    """
    with closing(gouvernance_store._connect(chemin)) as cx:  # noqa: SLF001
        try:
            return int(cx.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
        except sqlite3.OperationalError:
            return None


def _date_lisible(brut: str) -> str:
    """`2026-04-29` -> `29/04/2026`, et chaine vide si ce n'est pas une date.

    Ce n'est pas de la defense abstraite. Mesure du 2026-09-07 sur un coffre
    reel: une ligne du registre porte `2016-00` comme date d'assemblee. La
    mettre en forme sans la lire rendrait `00/00/2016`, c'est-a-dire une date
    inventee a partir d'une valeur que personne n'a su lire.
    """
    try:
        return date.fromisoformat(str(brut)).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return ""


def nommer_pieces(chemin: Any) -> dict[str, str]:
    """Quel nom lisible porte chaque piece que l'ecran peut avoir a citer.

    **Nommer ce qu'on ne sait pas, plutot que combler.** Mesure du 2026-09-07:
    sur 32 lignes du registre d'un coffre reel, 24 n'ont pas de date - ce sont
    des reglements de copropriete, des contrats, des annexes de reddition, et
    leur identifiant est de la forme `CONV-DOC-<empreinte>`. Ecrire
    `convocation du ...` pour elles serait fabriquer un fait. Et 6 des 8 lignes
    datees n'ont produit aucun sous-point a la lecture: la piece est au coffre
    et rien n'en a ete lu, ce qui n'est pas la meme chose qu'une piece absente.

    Trois axes gouvernent le nom, et rien d'autre: la piece est-elle connue du
    registre, sa date est-elle lisible, quelque chose en a-t-il ete lu. Une
    valeur inattendue sur l'un des trois degrade vers le cas moins precis, pas
    vers une affirmation.

    Une piece absente du registre n'a PAS d'entree ici: l'appelant doit pouvoir
    dire `le registre ne la nomme pas`, ce qu'une chaine vide dans le
    dictionnaire ne distinguerait pas d'un nom vide.
    """
    with closing(gouvernance_store._connect(chemin)) as cx:  # noqa: SLF001
        try:
            lignes = cx.execute(
                f'SELECT doc_id, ag_date, sous_points, origine '
                f'FROM "{TABLE_CONVOCATIONS}" ORDER BY origine'
            ).fetchall()
        except sqlite3.OperationalError:
            # Aucune convocation n'a jamais ete lue sur cette copropriete. Le
            # modele d'actes, lui, peut etre alimente: l'ecran doit continuer a
            # afficher ses cellules, en disant qu'il ne sait pas nommer la piece.
            return {}

    noms: dict[str, str] = {}
    for ligne in lignes:
        doc_id = str(ligne[0] or "")
        # `ORDER BY origine` met CORRIGE_HUMAIN avant EXTRAIT: la correction
        # humaine gagne a la lecture, comme partout ailleurs dans le modele.
        if not doc_id or doc_id in noms:
            continue
        jour = _date_lisible(str(ligne[1] or ""))
        brut = str(ligne[1] or "").strip()
        if jour:
            nom = f"convocation du {jour}"
        elif brut:
            nom = "document dont la date n'a pas pu être lue"
        else:
            nom = "document non daté"
        try:
            lu = int(str(ligne[2] or "0") or 0)
        except ValueError:
            lu = 0
        noms[doc_id] = nom if lu > 0 else nom + ", dont rien n'a été lu"
    return noms


def diagnostiquer(instance: Any) -> dict[str, Any]:
    """L'etat du coffre pour cet ecran, avec le geste exact qui le fait avancer."""
    try:
        chemin = gouvernance_store.store_path(instance)
    except gouvernance_store.GouvernanceStoreIndisponible:
        return {
            "etat": COFFRE_ABSENT,
            "titre": "Le coffre local n'est pas configuré pour cette copropriété.",
            "corps": "Sans coffre local, aucune lecture n'est conservée : l'écran n'a rien à "
                     "montrer, et ce n'est pas un constat sur la copropriété.",
            "geste": "Déclarez « settings.vault.local_root » dans instance.yml, puis redéposez "
                     "un procès-verbal.",
            "resolutions": 0,
            "actes": 0,
            "pieces": {},
            "acces": {},
        }
    if not chemin.exists():
        return {
            "etat": COFFRE_VIDE,
            "titre": "Aucun procès-verbal n'a encore été déposé.",
            "corps": "Le coffre local est déclaré mais vide. C'est le procès-verbal de la "
                     "dernière assemblée qui pose le mandat : sans lui, il n'y a rien à "
                     "contrôler.",
            "geste": "Déposez le procès-verbal de la dernière assemblée.",
            "resolutions": 0,
            "actes": 0,
            "pieces": {},
            "acces": {},
        }

    resolutions = _compter(chemin, gouvernance_store.TABLE_RESOLUTIONS) or 0
    actes = _compter(chemin, A.TABLE_ACTES)
    # Le nom lisible des pieces que les cellules vont citer. Il est lu ici,
    # avec le reste de l'etat du coffre, parce que c'est le seul endroit de
    # l'ecran qui tient le chemin du coffre - et parce qu'une citation sans nom
    # de piece retomberait sur une reference interne de fichier, ce que le
    # produit s'interdit au premier niveau.
    pieces = nommer_pieces(chemin)
    # **Nommer et atteindre sont deux axes distincts** (`RM-2026-0157`): la
    # ligne du dessus dit comment APPELER une piece, celle-ci dit si on peut
    # l'OUVRIR - et le corpus du lot porte 400 citations nommables par aucune
    # convocation dont les 400 documents sont pourtant au registre.
    acces = acces_aux_pieces(instance)

    if actes is None:
        return {
            "etat": MODELE_NON_ALIMENTE,
            "titre": "Le modèle relationnel n'a jamais été alimenté sur cette copropriété.",
            "corps": _corps_non_alimente(resolutions),
            "geste": "Exigence back : écrire le versement du registre des résolutions vers "
                     "« actes_autorisation », avec la portée, le résultat et le montant "
                     "effectif. Tant qu'il n'existe pas, cet écran n'a aucun acte à lire.",
            "resolutions": resolutions,
            "actes": 0,
            "pieces": pieces,
            "acces": acces,
        }
    if not actes:
        return {
            "etat": MODELE_VIDE,
            "titre": "Le modèle relationnel existe et ne contient aucun acte.",
            "corps": _corps_non_alimente(resolutions),
            "geste": "Vérifiez qu'un procès-verbal lisible a été déposé, puis relancez la "
                     "lecture. Si le registre porte des résolutions et le modèle aucun acte, "
                     "c'est le versement entre les deux qui manque.",
            "resolutions": resolutions,
            "actes": 0,
            "pieces": pieces,
            "acces": acces,
        }
    return {
        "etat": PRET,
        "titre": "",
        "corps": "",
        "geste": "",
        "resolutions": resolutions,
        "actes": actes,
        "pieces": pieces,
        "acces": acces,
    }


def _corps_non_alimente(resolutions: int) -> str:
    if resolutions:
        return (
            f"{resolutions} résolutions ont été lues et rangées dans le registre, et "
            "aucune n'a été versée dans le modèle relationnel qui porte les contrôles. "
            "Ce n'est donc pas « aucune rupture » : c'est « aucune lecture à contrôler ». "
            "Les deux se ressemblent à l'écran et ne veulent pas du tout dire la même chose."
        )
    return (
        "Aucune résolution n'est lue au registre, et aucun acte n'est versé dans le "
        "modèle relationnel. Un procès-verbal a peut-être été déposé sans couche texte "
        "lisible : rien n'en a été lu, et rien ne lui est attribué ici."
    )


#: Ce que l'ecran attend du back pour cesser de dire ce qu'il ne sait pas.
#: Chaque ligne est une exigence verifiee, pas une intention. Elle est affichee a
#: l'ecran, sous le tableau, parce qu'une limite qui ne se voit pas est une
#: limite que personne ne leve.
#:
#: **Deux de ces lignes ne sont plus ecrites ici.** Celles qui portent sur une
#: TABLE que l'ecran lit et que personne n'ecrit viennent de
#: `_ecrans_promesses`, ou une garde les recoupe avec ce que la chaine de
#: production ecrit reellement. Une exigence redigee a la main s'est deja
#: perimee en silence - la ligne *rien n'ecrit dans `actes_autorisation` hors
#: des tests* a survecu cinq jours au pont qui l'ecrivait.
#:
#: Les lignes qui restent ici ne portent pas sur une table: un calcul absent, un
#: objet du modele qui n'existe pas. Rien ne peut les mesurer, et les inventer
#: une table pour les rendre mesurables serait mentir sur ce qui manque.
EXIGENCES_BACK: tuple[tuple[str, str], ...] = (
    # **Cette exigence a ete TENUE le 2026-09-10**, et sa disparition est un
    # resultat en soi. Elle disait: *le modele rattache un seuil a un acte; il
    # ne calcule aucun franchissement*. La comparaison existe desormais - la
    # matrice porte le montant arrete par la deliberation a cote de celui de
    # l'acte, et chaque ligne dit *depasse*, *ne depasse pas*, ou *pas
    # calculable, il manque tel montant*.
    #
    # **Ce qui restait n'etait pas le calcul, c'etaient les MONTANTS**, et c'est
    # la ligne ci-dessous qui le dit maintenant. Laisser l'ancienne ferait
    # reclamer du code la ou il manque une donnee - et personne n'obtient un
    # montant en ecrivant du code.
    ("Lire le montant de chaque décision",
     "La comparaison au seuil se fait depuis le 2026-09-10, mais elle demande deux "
     "montants. Sur le corpus reconstruit, le montant de la décision n'est pas lisible "
     "sur la plus grande part des lignes soumises à un seuil : celles-là disent qu'elles "
     "ne savent pas, au lieu de conclure qu'aucune obligation ne s'applique."),
    ("Grouper les factures en marchés",
     "La ligne doit être le marché, pas la facture isolée. L'objet « marché » et sa clé de "
     "regroupement n'existent pas : cinq factures d'entretien produiraient cinq constats."),
    # **Cette exigence a ete TENUE le 2026-09-09**, sur l'arbitrage de Brice
    # (« bien evidemment on trace le controle »). Elle disait: *la table
    # traces_controle est lue par la colonne Ma conclusion et aucun geste de
    # l'application ne l'ecrit*. Le geste existe desormais, et la laisser ici
    # ferait lire a l'utilisateur qu'il ne peut pas conclure alors qu'il le
    # peut - la meme prose perimee que le lot `RM-2026-0059` a trouvee deux
    # lignes plus bas sur `actes_autorisation`.
    ("Nommer l'auteur d'une conclusion",
     "La conclusion d'un contrôle s'enregistre depuis le 2026-09-09, mais sa colonne "
     "« auteur » reste vide par décision : on ne sait donc pas QUI a conclu, et deux "
     "conclusions successives sur la même ligne sont indiscernables de ce côté. "
     "Voir « RM-2026-0161 »."),
    ("Deux états de résultat que le corpus impose",
     "Marquée adoptée sans atteindre la majorité — il faut stocker les voix comptées et la "
     "majorité requise. Et demandée, jamais mise à l'ordre du jour — il faut enregistrer les "
     "demandes d'inscription des copropriétaires, objet qui n'existe pas."),
) + _promesses.exigences()
