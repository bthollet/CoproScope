"""Lecture d'un etat de depenses, ou le syndic declare lui-meme ses rattachements.

Ce module lit la page qui liste les depenses d'une copropriete et, pour
chacune, la piece justificative que le syndic y rattache.

======================================================================
Pourquoi cette page compte plus que les autres
======================================================================

Le rapprochement d'une facture a une ligne de depenses est un chantier de
CoproScope, reconstruit par calcul a partir des pieces. Or l'extranet le sert
deja: c'est **l'assertion du syndic lui-meme**, ligne par ligne. Mesure du
2026-09-04: 729 des 1 286 lignes portent exactement un lien de facture, aucune
n'en portant deux.

Ce n'est donc pas une donnee de plus, c'est la **provenance manquante**. Trois
assertions peuvent coexister sur le meme couple facture-depense:

- `SYNDIC`: ce que l'extranet declare;
- `CALCUL`: ce que le rapprochement de CoproScope propose;
- `CORRIGE_HUMAIN`: ce qu'un humain confirme ou contredit.

Et leur desaccord devient un **constat mesurable** au lieu d'une opinion: le
syndic rattache cette facture a cette ligne, le calcul en propose une autre,
voila une question a poser - formulee sans accusation.

Rappel du contexte, donne par Brice: c'est precisement cette matiere qui bouge,
parce qu'un autre coproprietaire en fait le suivi. Trois sources de changement
s'y melangent. Le journal enregistre l'etat, jamais l'auteur.

======================================================================
Axes de generalisation
======================================================================

----------------------------------------------------------------------
Axe 5 - ce qui distingue deux lignes de depenses homonymes
----------------------------------------------------------------------

*Valeurs observees*: mesure sur les 729 lignes portant une facture. La cle
(cle de charges, date, nature, libelle) laisse **21 collisions**; en ajoutant le
**montant**, elle tombe a **zero**.

*Invariant*: deux depenses distinctes different par au moins un de leurs
attributs affiches - sinon l'utilisateur lui-meme ne pourrait pas les
distinguer, et le syndic non plus.

*Ce que le code en fait*: la cle prend toutes les colonnes de la ligne, montant
compris.

*Hors des valeurs observees*: deux lignes reellement identiques sur toutes leurs
colonnes - un doublon comptable, ou deux factures du meme montant le meme jour
au meme fournisseur - restent en collision. Elles sont alors detectees a chaque
passage par `_extranet_journal.collisions` et passent `INDETERMINE`. C'est le
bon comportement: si rien a l'ecran ne les distingue, l'outil ne doit pas
pretendre le faire.

*Ce qui a ete ecarte*: la cle par **rang dans le groupe** est injective elle
aussi - mesuree, zero collision sur 729 - et elle est **inutilisable**. Une
ligne inseree en tete de groupe decale toutes les suivantes, et le journal
verrait un remaniement complet la ou rien n'a bouge. Deux cles affichent le
meme zero et une seule tient: c'est une distinction que la mesure seule ne
donne pas.

----------------------------------------------------------------------
Axe 7 - ce qui distingue une ligne de donnees d'une ligne de service
----------------------------------------------------------------------

*Defaut trouve le 2026-09-04 en executant le lecteur sur la page reelle, et
c'est le plus grave du lot.* La premiere version reconnaissait un en-tete de
groupe au nombre de cellules **non vides**. Or l'etat de depenses contient 348
lignes de **totaux** - `TOTAL <intitule> | <montant>` - qui ont exactement deux
cellules non vides. Elles etaient donc prises pour des en-tetes, et **chaque
total devenait une cle de charges**: 42 cles reelles lues comme 340.

La consequence n'est pas cosmetique. Les depenses suivant un total se voyaient
rattacher a une cle fantome **portant un montant**. Ce montant change d'un
passage a l'autre; l'emplacement de chaque piece du groupe changeait donc avec
lui, et le journal aurait produit au passage suivant un retrait ET un ajout pour
chacune. Le mode de defaillance redoute, a l'echelle d'une page entiere.

*Invariant*: dans un tableau, les lignes de donnees partagent le meme nombre de
colonnes. Les lignes de service - en-tetes, sous-totaux - en ont un autre.

*Ce que le code en fait*: il **decouvre** la largeur des lignes de donnees comme
la largeur la plus frequente du tableau, au lieu de la coder. Une ligne de deux
cellules ou moins est un en-tete; une ligne a la largeur modale est une donnee;
tout le reste est **ignore et compte**, jamais silencieusement.

*Hors des valeurs observees*, et il y a deux cas distincts:

- un tableau ou les lignes de service seraient aussi nombreuses que les donnees
  rendrait une largeur modale fausse. Le compte des lignes ignorees le
  montrerait immediatement - c'est pourquoi il est rendu a l'appelant plutot que
  jete;
- **un editeur qui emettrait ses sous-totaux a la largeur des donnees ne serait
  pas rattrape par cette regle.** La largeur ne les distinguerait plus, et ils
  seraient comptes comme des depenses sans piece justificative - une surestime
  visible, et du bon cote: elle fait poser une question de trop, pas passer un
  manquement sous silence. Le remede, s'il devient necessaire, est un temoin de
  plus au profil - une classe de ligne, un intitule - et non une exception dans
  le code.

----------------------------------------------------------------------
Axe 6 - comment les rubriques sont connues
----------------------------------------------------------------------

*Valeurs observees*: sur l'index des documents, les rubriques sont un ensemble
**ferme et declarable** - huit codes. Sur les depenses, les cles de charges sont
**decouvertes dans la page** - 42 relevees, dont 36 partagees avec le budget.

*Invariant*: une depense est imputee a quelque chose, et cette imputation est
affichee.

*Ce que le code en fait*: il ne declare rien et prend les cles telles qu'elles
viennent. Consequence voulue: une cle presente a une date et absente a la
suivante n'apparait tout simplement pas dans la couverture du second passage,
donc `_extranet_journal` rend `INDETERMINE` pour ses pieces au lieu de conclure
au retrait. Une cle disparue peut vouloir dire *plus aucune depense dessus* ou
*cle supprimee*, et rien dans la page ne tranche.

*Hors des valeurs observees*: un editeur sans regroupement du tout produirait
une cle de charges vide. Toutes les lignes tomberaient dans une rubrique unique,
la comparaison resterait valable, et seule la granularite du constat baisserait.
Degradation propre.
"""

from __future__ import annotations

from typing import Any, Sequence

from ._extranet_adaptateur import Noeud, ProfilEditeur, analyser
from ._extranet_schema import (
    CLOTURE_AUCUNE,
    CLOTURE_CONSTATEE,
    CONTENU_NON_VERIFIE,
    EMPLACEMENT_QUALIFIE,
    ORIGINE_EXTRAIT,
    RUBRIQUE_PARCOURUE,
    SEPARATEUR_EMPLACEMENT,
)

#: Provenance d'un rattachement facture / ligne de depenses.
PROVENANCE_SYNDIC = "SYNDIC"

#: Cle des lignes rencontrees avant tout en-tete de groupe. Mesuree sur la page
#: reelle: elles existent. Leur donner un nom explicite plutot que la chaine
#: vide evite une rubrique muette dans la couverture - une rubrique sans nom ne
#: se lit pas a l'ecran, ne se cite pas dans une question au syndic, et se
#: confondrait avec une lecture ratee.
CLE_HORS_GROUPE = "(hors groupe)"


def _largeur_modale(lignes: Sequence[Noeud]) -> int:
    """La largeur d'une ligne de donnees, decouverte et non codee.

    Dans un tableau, les lignes de donnees partagent le meme nombre de colonnes;
    les lignes de service en ont un autre. La largeur la plus frequente est donc
    celle des donnees - sur l'etat mesure, 872 lignes a cinq cellules contre 348
    lignes de totaux a trois ou quatre.
    """
    comptes: dict[int, int] = {}
    for ligne in lignes:
        n = len([c for c in ligne.enfants if c.tag in ("td", "th")])
        if n > 2:
            comptes[n] = comptes.get(n, 0) + 1
    if not comptes:
        return 0
    return max(comptes.items(), key=lambda kv: kv[1])[0]


def _cellules(ligne: Noeud) -> list[str]:
    return [c.texte_total() for c in ligne.enfants if c.tag in ("td", "th")]


def _a_une_facture(ligne: Noeud, profil: ProfilEditeur) -> bool:
    return any(
        profil.marqueur_lien in (a.attrs.get("href") or "")
        for a in ligne.descendants("a")
    )


def lire_depenses(
    html: str,
    profil: ProfilEditeur,
    passage_id: str,
    *,
    cellules_max_groupe: int = 2,
) -> dict[str, Any]:
    """Analyse un etat de depenses et rend `rubriques`, `pieces` et `liens`.

    **Aucun appelant en production, et c'est voulu.** Cette fonction est
    l'**etalon** contre lequel le lecteur JavaScript du plugin est confronte:
    `test_extension_javascript.py` fait lire la meme page aux deux et compare
    les emplacements produits. Sans elle, la seule garantie que les deux
    implantations lisent pareil serait la relecture humaine - et une divergence
    ne se verrait qu'au recoupement entre voisins, sous la forme d'un zero de
    concordance que deux personnes liraient comme un desaccord entre elles.

    Ne pas la supprimer parce qu'elle parait morte: elle est mesurante.

    `pieces` a exactement la forme attendue par le journal: une facture
    rattachee est une piece observee a un emplacement, et son emplacement est
    la **ligne de depenses** qui la porte. Un rattachement retire est donc un
    `RETRAIT` au sens du journal, sans code supplementaire.

    `liens` porte la meme information sous l'angle du rapprochement: pour
    chaque ligne, ce que le syndic declare. Les deux vues partagent la cle,
    donc rien ne peut diverger entre elles.

    **Les lignes sans facture sont enregistrees aussi**, dans `liens`, avec
    `a_une_facture` a faux. Sans elles, une piece justificative apparue entre
    deux passages serait indiscernable d'une ligne de depenses nouvelle - or ce
    n'est pas la meme chose: la premiere comble une lacune, la seconde est une
    depense de plus.
    """
    racine = analyser(html)
    cloture = CLOTURE_CONSTATEE
    for noeud in racine.descendants():
        classe = (noeud.attrs.get("class") or "").lower()
        if any(m in classe for m in profil.marqueurs_pagination):
            cloture = CLOTURE_AUCUNE
            break

    cle_charge = CLE_HORS_GROUPE
    pieces: list[dict[str, str]] = []
    liens: list[dict[str, str]] = []
    vues: set[str] = set()
    par_rubrique: dict[str, int] = {}
    rang = 0
    ignorees = 0

    lignes = list(racine.descendants("tr"))
    largeur = _largeur_modale(lignes)

    for ligne in lignes:
        cellules = _cellules(ligne)
        porte_facture = _a_une_facture(ligne, profil)

        # Un en-tete de groupe se reconnait au nombre de CELLULES, pas au nombre
        # de cellules remplies: une ligne de total porte deux valeurs et n'est
        # pas un groupe. Voir l'axe 7.
        if not porte_facture and len(cellules) <= cellules_max_groupe:
            texte = " ".join(c for c in cellules if c).strip()
            if texte:
                cle_charge = texte
            continue

        if largeur and len(cellules) != largeur:
            # Ligne de service - sous-total, sur-titre. Comptee, jamais jetee en
            # silence: son nombre est le temoin que la largeur modale est juste.
            ignorees += 1
            continue

        colonnes = [c.strip() for c in cellules if c.strip()]
        if not colonnes:
            continue

        # Toutes les colonnes entrent dans la cle, montant compris: c'est le
        # montant qui fait tomber les 21 collisions mesurees a zero.
        cle = SEPARATEUR_EMPLACEMENT.join([cle_charge, *colonnes])
        par_rubrique[cle_charge] = par_rubrique.get(cle_charge, 0) + 1

        liens.append(
            {
                "passage_id": passage_id,
                "cle_charge": cle_charge,
                "emplacement": cle,
                "colonnes": " | ".join(colonnes),
                "a_une_facture": "oui" if porte_facture else "non",
                "provenance": PROVENANCE_SYNDIC,
                "origine": ORIGINE_EXTRAIT,
            }
        )

        if not porte_facture or cle in vues:
            continue
        vues.add(cle)
        pieces.append(
            {
                "passage_id": passage_id,
                "rubrique_code": cle_charge,
                "rang": str(rang),
                "groupe": colonnes[0] if colonnes else "",
                "libelle": " | ".join(colonnes[1:]) if len(colonnes) > 1 else colonnes[0],
                "emplacement": cle,
                "emplacement_qualite": EMPLACEMENT_QUALIFIE,
                "nom_serveur": "",
                "empreinte": "",
                "contenu_etat": CONTENU_NON_VERIFIE,
                "doc_id": "",
                "origine": ORIGINE_EXTRAIT,
            }
        )
        rang += 1

    rubriques = [
        {
            "passage_id": passage_id,
            "rubrique_code": code,
            "rubrique_libelle": code,
            "etat": RUBRIQUE_PARCOURUE,
            "cloture": cloture,
            "nb_pieces": str(nb),
            "motif": "",
            "doc_id": "",
            "origine": ORIGINE_EXTRAIT,
        }
        for code, nb in sorted(par_rubrique.items())
    ]
    return {
        "rubriques": rubriques,
        "pieces": pieces,
        "liens": liens,
        "lignes_ignorees": ignorees,
        "largeur_donnees": largeur,
    }


def lignes_sans_facture(liens: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    """Les depenses qu'aucune piece justificative n'appuie, selon le syndic.

    C'est un **constat**, pas un manquement: une ligne peut etre appuyee par une
    piece que l'extranet ne publie pas, ou relever d'une categorie qui n'en
    appelle pas. L'outil mesure et date; il ne conclut pas.

    L'usage attendu est la question, pas l'accusation: *ces lignes n'ont pas de
    piece jointe dans l'espace en ligne, sur quoi reposent-elles ?*
    """
    return [lien for lien in liens if lien.get("a_une_facture") != "oui"]
