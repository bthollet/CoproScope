"""Lire un montant ecrit a la main, ou refuser de le lire. Jamais deviner.

**Pourquoi ce module existe.** La couche partagee stocke tout en TEXT, et les
vues comparaient ce TEXT avec `CAST(... AS REAL)`. SQLite ne leve pas: il lit
les caracteres tant qu'ils forment un nombre et jette le reste. Mesure du
2026-09-04:

    '18 240,00 EUR' -> 18.0        '2 000'  -> 2.0
    '1.234,56'      -> 1.234       '20%'    -> 20.0
    'environ 2000'  -> 0.0

Un plafond de 10 000 EUR devenait 10,00 EUR, et le controle du plafond de
l'article 21-2 - le seul controle du produit qui ne se voit pas ligne a ligne -
affichait un ecran vert sur une delegation franchie d'un facteur mille.

**La regle tenue ici.** Trois etats, jamais deux:

- *absent*: `None` ou la chaine vide. Rend `""`. Ce n'est pas zero.
- *lisible*: rend la forme canonique `-?\\d+\\.\\d\\d`, celle que le `CAST`
  rend telle qu'on la croit.
- *illisible*: leve `MontantIllisible`. **C'est le coeur du correctif.** Le
  defaut d'origine n'etait pas de mal calculer, c'etait de rendre un nombre
  plausible - 18,00 EUR est un nombre, 0,00 EUR aussi - la ou la bonne reponse
  etait "un montant est ecrit et je ne sais pas le lire".

**L'ambigu est illisible.** `2.500` peut valoir 2,5 ou 2 500 selon le pays qui
a tape la ligne, et rien dans la chaine ne tranche. La version precedente
choisissait 2,50 en silence. Ici elle refuse, en nommant l'ambiguite. Un point
suivi d'exactement trois chiffres, ou une virgule suivie d'exactement trois
chiffres, sans autre separateur, n'est jamais lu au jugé.
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal

__all__ = [
    "MontantIllisible",
    "montant_normalise",
    "montant_decimal",
    "montant_lisible",
    "taux_normalise",
    "est_canonique",
    "sql_reel",
    "sql_taux",
]


class MontantIllisible(ValueError):
    """Un montant est ecrit, et aucune regle ne sait le lire sans deviner.

    L'exception porte la valeur et le motif parce qu'elle est destinee a etre
    **affichee**, pas seulement journalisee: la phrase juste a l'ecran est
    "un montant est ecrit et n'a pas ete lu", jamais une cellule vide.
    """

    def __init__(self, valeur: object, motif: str) -> None:
        self.valeur = valeur
        self.motif = motif
        super().__init__(
            f"montant illisible {valeur!r}: {motif}. Un montant qu'on ne sait "
            "pas lire est un fait a nommer, pas un nombre a inventer."
        )


#: Tous les blancs qu'un document francais met entre les milliers: espace
#: normale, insecable, insecable etroite, fine, cadratin.
_BLANCS = " \u00a0\u202f\u2009\u2007\u2008\u2005\t"

#: Ce qu'on retire avant de lire: le symbole et le mot, sous leurs formes.
_MONNAIES = ("EUROS", "EURO", "EUR", "€")

#: Groupement par blancs: `357 493,10`, `1 200 000`. Le premier groupe fait 1 a
#: 3 chiffres, les suivants exactement 3. `environ 2000` n'entre pas ici - il
#: est deja refuse par le controle de caracteres.
_GROUPES_BLANCS = re.compile(r"^\d{1,3}(?: \d{3})+(?:[.,]\d+)?$")

#: Groupement par un separateur de milliers explicite: `1.234.567`, `1,234,567`.
_GROUPES = "^\\d{{1,3}}(?:\\{sep}\\d{{3}})+$"

#: Milliers puis decimales: `1.234,56` ou `1,234.56`.
_GROUPES_ET_DECIMALES = "^\\d{{1,3}}(?:\\{mille}\\d{{3}})+\\{dec}\\d+$"

_CANONIQUE = re.compile(r"^-?\d+\.\d\d$")


def _refus(valeur: object, motif: str) -> None:
    raise MontantIllisible(valeur, motif)


def _sans_monnaie(texte: str) -> str:
    """Retire le symbole monetaire, quelle que soit sa casse et sa place."""
    reste = texte
    for mot in _MONNAIES:
        reste = re.sub(re.escape(mot), " ", reste, flags=re.IGNORECASE)
    return reste


def _decimal_depuis_chiffres(brut: str, valeur: object) -> Decimal:
    """`brut` ne contient plus que des chiffres, des points et des virgules."""
    a_point = "." in brut
    a_virgule = "," in brut

    if a_point and a_virgule:
        # Le dernier separateur rencontre est le separateur decimal: c'est vrai
        # de `1.234,56` comme de `1,234.56`. L'autre doit alors grouper par
        # milliers de facon reguliere, sinon la chaine n'est pas un montant.
        dec = "." if brut.rfind(".") > brut.rfind(",") else ","
        mille = "," if dec == "." else "."
        if not re.match(_GROUPES_ET_DECIMALES.format(mille=mille, dec=dec), brut):
            _refus(
                valeur,
                "deux separateurs sans groupement regulier des milliers",
            )
        return Decimal(brut.replace(mille, "").replace(dec, "."))

    if not a_point and not a_virgule:
        if not brut.isdigit():
            _refus(valeur, "caractere inattendu dans le nombre")
        return Decimal(brut)

    sep = "." if a_point else ","
    if brut.count(sep) > 1:
        if not re.match(_GROUPES.format(sep=sep), brut):
            _refus(valeur, f"plusieurs '{sep}' sans groupement regulier des milliers")
        return Decimal(brut.replace(sep, ""))

    entier, _, apres = brut.partition(sep)
    if not entier.isdigit() or not apres.isdigit():
        _refus(valeur, "caractere inattendu autour du separateur")
    if len(apres) == 3:
        # Le defaut C023, refuse plutot que devine: `2.500` vaut 2,5 chez un
        # cabinet et 2 500 chez l'autre. La version precedente rendait 2,50 et
        # faisait tomber le plafond de l'article 21-2 sur toutes les depenses.
        _refus(
            valeur,
            f"'{sep}' suivi de trois chiffres: separateur decimal ou de "
            "milliers, la chaine ne le dit pas",
        )
    if not apres:
        _refus(valeur, "separateur en fin de chaine")
    return Decimal(f"{entier}.{apres}")


def montant_normalise(valeur: object, *, pourcentage_admis: bool = False) -> str:
    """La forme canonique d'un montant: `18 240,00 EUR` -> `18240.00`.

    Rend `""` quand le montant est **absent**, jamais `0`: `rien de paye a ce
    jour` n'est pas `paye zero euro`, et un `0` implicite fausserait le cumul.
    Leve `MontantIllisible` quand il est **ecrit et non lisible**.
    """
    if valeur is None:
        return ""
    if isinstance(valeur, bool):
        _refus(valeur, "un booleen n'est pas un montant")
    if isinstance(valeur, (int, Decimal)):
        return f"{Decimal(valeur):.2f}"
    if isinstance(valeur, float):
        return f"{Decimal(str(valeur)):.2f}"
    if not isinstance(valeur, str):
        _refus(valeur, f"type {type(valeur).__name__} non lisible comme montant")

    origine = valeur
    texte = unicodedata.normalize("NFKC", valeur).strip()
    if not texte:
        return ""

    texte = _sans_monnaie(texte)
    if pourcentage_admis:
        texte = texte.replace("%", " ")
    texte = texte.strip()

    negatif = False
    if texte.startswith("(") and texte.endswith(")"):
        # Convention comptable: les parentheses portent le signe. Elle est
        # explicite, donc lisible; c'est l'ambiguite qu'on refuse, pas la
        # notation.
        negatif = True
        texte = texte[1:-1].strip()
    if texte.startswith("-"):
        negatif = not negatif
        texte = texte[1:].strip()
    elif texte.startswith("+"):
        texte = texte[1:].strip()

    for blanc in _BLANCS:
        texte = texte.replace(blanc, " ")
    texte = re.sub(r" +", " ", texte).strip()
    if not texte:
        _refus(origine, "aucun chiffre apres retrait du symbole monetaire")

    if re.search(r"[^0-9 .,]", texte):
        _refus(origine, "caractere qui n'appartient pas a un montant")

    if " " in texte:
        if not _GROUPES_BLANCS.match(texte):
            _refus(origine, "des blancs sans groupement regulier des milliers")
        texte = texte.replace(" ", "")

    montant = _decimal_depuis_chiffres(texte, origine)
    if negatif:
        montant = -montant
    return f"{montant:.2f}"


def montant_decimal(valeur: object) -> Decimal | None:
    """Le montant en `Decimal`, ou `None` s'il est **absent**.

    Leve `MontantIllisible` s'il est ecrit et non lisible. `Decimal` et non
    `float`: un euro n'a pas de representation binaire exacte, et deux
    controles du budget se comparaient deja a travers cette couture.
    """
    texte = montant_normalise(valeur)
    return Decimal(texte) if texte else None


def montant_lisible(valeur: object) -> bool:
    """Vrai si la valeur est un montant ecrit **et** lisible.

    Un montant absent rend `False` comme un montant illisible: la question
    "faut-il afficher un nombre" a la meme reponse. La question "pourquoi il
    n'y en a pas" se pose avec `montant_normalise`, qui distingue les deux.
    """
    try:
        return bool(montant_normalise(valeur))
    except MontantIllisible:
        return False


def taux_normalise(valeur: object) -> str:
    """Un taux de T.V.A.: `5,5 %` -> `5.50`, `20` -> `20.00`.

    Meme regle que les montants, au `%` pres. Un taux mal lu se propage dans
    `ttc * taux / (100 + taux)` et fabrique un ecart de T.V.A. qui n'existe pas.
    """
    return montant_normalise(valeur, pourcentage_admis=True)


def est_canonique(texte: str) -> bool:
    """La chaine est-elle deja la forme que le `CAST` rend telle qu'on la croit."""
    return bool(_CANONIQUE.match(texte))


def sql_reel(colonne: str) -> str:
    """Le `CAST` d'une colonne de montant, mais **seulement** sur la forme canonique.

    `CAST('18 240,00 EUR' AS REAL)` rend 18.0 sans rien signaler. Cette
    expression rend `NULL` sur tout ce qui n'est pas `-?\\d+\\.\\d\\d`, parce
    qu'un montant absent se lit "non lu" a l'ecran alors qu'un 18,00 fabrique
    se lit comme un fait.

    La vraie garantie est la normalisation a l'ecriture, dans
    `_actes_store.ecrire`: cette expression est la ceinture qui reste utile sur
    une base ecrite par une version anterieure, ou par une main.

    **Pourquoi quatre conditions et non une.** La premiere version n'en portait
    qu'une, `GLOB '[0-9]*.[0-9][0-9]'`, et sa docstring affirmait deja le
    contrat ci-dessus. C'etait faux, mesure du 2026-09-05: dans un motif GLOB,
    `*` avale **tout**, y compris un blanc de milliers et un second separateur.
    La ceinture rendait donc, sur le seul cas pour lequel elle existe - une base
    ecrite par une version anterieure ou a la main:

        '18 240.00'  -> 18.0        '357 493.10' -> 357.0
        '2.500.00'   -> 2.5

    C'est-a-dire exactement l'erreur de trois ordres de grandeur qu'elle est
    censee arreter, et elle restait muette. Les trois `NOT GLOB` ferment chacun
    une porte que `*` laissait ouverte:

    - `'*[^0-9.-]*'` : aucun caractere etranger. C'est lui qui arrete le blanc
      de milliers, le symbole monetaire et la virgule decimale.
    - `'*.*.*'` : un seul point. C'est lui qui arrete `2.500.00`.
    - `'?*-*'` : le signe est en tete ou nulle part, jamais au milieu.
    """
    return (
        f"CASE WHEN (({colonne}) GLOB '[0-9]*.[0-9][0-9]' "
        f"OR ({colonne}) GLOB '-[0-9]*.[0-9][0-9]') "
        f"AND ({colonne}) NOT GLOB '*[^0-9.-]*' "
        f"AND ({colonne}) NOT GLOB '*.*.*' "
        f"AND ({colonne}) NOT GLOB '?*-*' "
        f"THEN CAST(({colonne}) AS REAL) END"
    )


def sql_taux(colonne: str) -> str:
    """Le `CAST` d'une colonne de **taux**, sur toutes ses formes ecrites.

    Un taux n'est pas un montant, et leur imposer la meme forme canonique a
    eteint un controle qui marchait. Mesure du 2026-09-05 sur une base non
    migree portant `taux_tva_annonce = '10'`, la forme la plus normale qui
    soit pour un taux:

        avant  CAST nu    -> tva_attendue = 151.45, ecart 0.03, TVA_INCOHERENTE emis
        apres  sql_reel   -> tva_attendue = NULL,   le WHERE ne retient plus rien

    Le constat disparaissait sans exception, sans compteur et sans mention a
    l'ecran - un defaut silencieux de plus, introduit par le correctif meme.

    **Ce qui distingue un taux d'un montant.** L'ambiguite que `sql_reel`
    refuse est celle du separateur de milliers: `2.500` peut valoir 2,5 ou
    2 500. Un taux de T.V.A. n'a pas de milliers - il vit entre 0 et 100 - donc
    `10` et `5.5` se lisent sans rien deviner. On accepte donc `\\d+` et
    `\\d+\\.\\d+`, et rien d'autre: `20%`, `10,5` et `abc` restent NULL, parce
    que la ils portent bien une forme qu'on ne sait pas lire sans supposer.
    """
    return (
        f"CASE WHEN ({colonne}) GLOB '[0-9]*' "
        f"AND ({colonne}) NOT GLOB '*[^0-9.]*' "
        f"AND ({colonne}) NOT GLOB '*.*.*' "
        f"AND ({colonne}) NOT GLOB '*.' "
        f"THEN CAST(({colonne}) AS REAL) END"
    )
