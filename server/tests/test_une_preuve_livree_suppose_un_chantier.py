# -*- coding: utf-8 -*-
"""Une cellule ne peut pas livrer une preuve ET declarer son chantier a ouvrir.

**LA CONTRADICTION EST INTERNE, et c'est ce qui rend cette garde defendable.**
Elle ne confronte pas la cellule au monde: elle confronte **deux colonnes de la
meme ligne**.

- la colonne `preuve` cite un fichier de test qui EXISTE dans `server/tests`;
- la colonne `chantier` dit `a ouvrir`.

Les deux ne peuvent pas etre vraies ensemble. Une preuve livree suppose un
travail, donc un chantier - et la doctrine du depot l'exige en propres termes:
*tout chantier actif doit avoir une ligne vivante dans
`docs/presence_agents.md`*.

----------------------------------------------------------------------
Pourquoi CE predicat, apres en avoir jete un autre
----------------------------------------------------------------------

La premiere mesure du 2026-09-12 annonçait **47** items, sur le predicat *un
commit cite l'item*. **Ce predicat est faux**, et le depot porte le contre-exemple:
`2e65d2b` est un commit de TRIAGE qui cite cinq items sans travailler sur aucun.
C'est exactement la faute que le `CLAUDE.md` nomme - `la chaine apparait quelque
part` pris pour `le numero designe un travail` - et dont il dit que
**l'exhaustivite de la recherche rend la conclusion plus credible, pas moins**.

Le predicat retenu n'a aucun terme externe. Il ne peut donc pas etre elargi par
accident, et son chiffre ne bouge que si une cellule change.

----------------------------------------------------------------------
Axe, invariant, degradation
----------------------------------------------------------------------

- **L'axe.** *Le rapport entre ce qu'une cellule declare LIVRE et ce qu'elle
  declare OUVERT.* Le degre de liberte est la facon de nommer un chantier -
  `CH-YYYYMMDD-HHMMSS-RM-...`, le format historique `CH-YYYY-NNNN`, plusieurs
  chantiers, une phrase.
- **L'invariant.** Une cellule qui cite une preuve existante ne declare pas son
  chantier `a ouvrir`. La garde ne demande PAS un format: elle demande que la
  colonne ne dise pas *rien n'a commence* quand la colonne voisine dit
  *voici la preuve*.
- **Degradation hors des valeurs observees.** Seule la mention exacte
  `a ouvrir` est reconnue. Une cellule qui ecrirait `chantier a creer` ou
  laisserait la colonne vide passerait: **le compte est un PLANCHER**, et il est
  ecrit ici pour la meme raison que dans la garde soeur - un plancher presente
  comme un total est un chiffre qui a l'air d'une preuve.

----------------------------------------------------------------------
Ce que la dette recouvre, et qui est pire que la contradiction
----------------------------------------------------------------------

**Sur les 28 contradictions mesurees, TROIS seulement avaient un `CH-*` nomme
quelque part.** Les 25 autres ont produit des tests livres et **aucun chantier
n'a jamais ete trace, ni dans la cellule ni dans `docs/presence_agents.md`**.
La colonne ne se trompait donc pas: elle disait vrai sur un point que la
doctrine interdit. C'est le meme constat que celui deja inscrit ailleurs - la
table *vivante* des chantiers est perimee pendant que le travail reel n'y
figure pas.

Les trois repérables ont ete repares depuis ce que `presence_agents.md`
declarait deja; les 25 autres depuis **git**, par la derivation decrite sur
`DETTE_2026_09_12` - avec les deux ecueils qu'elle a fallu ecarter, et le
discriminant qui les ecarte.

**CE QUI RESTE VRAI APRES LA DETTE VIDE, et qui est le vrai sujet.** Cette
garde empeche desormais qu'une cellule se contredise. Elle **ne fait pas** que
les chantiers soient traces au moment ou ils tournent - ils ne l'etaient pas,
et la reconstruction depuis git ne remplace pas une coordination vivante. Elle
rend seulement le mensonge de la colonne impossible a maintenir en silence.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
TESTS = Path(__file__).resolve().parent
GOUVERNAIL = RACINE / "docs" / "roadmap_backlog_central.md"
TITRE_REGISTRE = "## Registre actif par identifiant"

_BARRE_NUE = re.compile(r"(?<!\\)\|")

#: Les statuts d'un item encore en vie. Un item clos peut garder une colonne
#: `a ouvrir` sans consequence: plus personne ne la lira pour decider.
VIVANT = frozenset({
    "BACKLOG", "ACTIF", "A_ARBITRER", "BLOQUE", "A_QUALIFIER", "ROADMAP",
    "PRET_A_INTEGRER",
})

#: La colonne COMMENCE par la mention. **Elargi le 2026-09-12 par une mutation
#: qui ne mordait pas:** le motif exigeait auparavant que la cellule soit
#: EXACTEMENT `a ouvrir` (`...\s*$`), si bien qu'une cellule disant
#: `a ouvrir (voir plus bas)` echappait a la garde sans que rien ne le signale.
#: C'est la meme faute que celles que cette garde traque - une condition plus
#: etroite que ce qu'elle pretend couvrir - et c'est la campagne de mutation qui
#: l'a trouvee, pas la relecture. La degradation declaree en en-tete reste
#: vraie: une cellule qui ecrirait `chantier a creer` passe encore, donc le
#: compte est un plancher.
A_OUVRIR = re.compile(r"^\s*a\s+ouvrir\b", re.I)
NOM_DE_TEST = re.compile(r"(test_[a-z0-9_]+)\.py")

#: **DETTE VIDEE LE 2026-09-12, et un identifiant de chantier ne s'est toujours
#: pas invente: il s'est DERIVE.**
#:
#: La dette a d'abord ete posee a 25 items, avec pour motif *reparer demande de
#: nommer le chantier qui a produit la preuve, et un identifiant de chantier ne
#: s'invente pas*. C'etait vrai et **incomplet**: le format du depot est
#: `CH-YYYYMMDD-HHMMSS-RM-YYYY-NNNN-slug`, et son horodatage vit dans git -
#: c'est le commit qui a AJOUTE le fichier de preuve. Rien n'a donc ete
#: invente; on a lu.
#:
#: **ET LA PREMIERE DERIVATION RENDAIT 25 SUR 25, CE QUI ETAIT FAUX.** Elle
#: prenait la plus ANCIENNE trace du fichier cite. Trois items derivaient alors
#: vers des tests crees en mai ou juin, bien avant eux: le fichier n'avait pas
#: ete ecrit pour l'item, la cellule se reclamait d'une garde **preexistante**.
#: Le discriminant retenu n'est donc pas la date mais l'ATTRIBUTION: **le commit
#: qui a ajoute la preuve cite-t-il l'item dans son message ?**
#:
#: Ce discriminant a corrige la derivation au lieu de la confirmer:
#: `RM-2026-0135` et `RM-2026-0174` citent plusieurs tests, et prendre le plus
#: ancien designait la garde empruntee quand prendre celui dont le commit nomme
#: l'item designe la bonne.
#:
#: **Resultat: 23 chantiers reconstruits depuis git, avec leur sha**, et **2
#: items qui n'en recoivent pas** - `RM-2026-0106` (preuve du 2026-05-22) et
#: `RM-2026-0132` (preuve du 2026-09-08) - parce qu'y ecrire un chantier
#: fabriquerait une trace fausse. Leur colonne porte la raison a la place.
#:
#: **Ce que la dette vide ne veut PAS dire.** Elle ne dit pas que les 23
#: chantiers ont ete tracés a l'epoque: ils ne l'ont pas ete, et c'est le
#: constat de fond - la table de `docs/presence_agents.md` est restee muette
#: pendant que le travail se faisait. Aucune ligne de presence retroactive n'a
#: ete ecrite: cette table sert la coordination entre agents concurrents, et 23
#: lignes pour du travail fini n'y coordonnent rien.
DETTE_2026_09_12: frozenset[str] = frozenset()


def _cellules(ligne: str) -> list[str]:
    brut = _BARRE_NUE.split(ligne)
    return [c.strip() for c in brut] if len(brut) >= 3 else []


def registre() -> dict[str, dict[str, str]]:
    lignes = GOUVERNAIL.read_text(encoding="utf-8").splitlines()
    debut = next((i for i, l in enumerate(lignes)
                  if l.startswith(TITRE_REGISTRE)), None)
    if debut is None:
        raise LookupError(
            "titre %r introuvable: une mesure qui rendrait zero item "
            "passerait pour un registre sain" % TITRE_REGISTRE)
    fin = next((i for i, l in enumerate(lignes[debut + 1:], debut + 1)
                if l.startswith("## ")), len(lignes))
    items: dict[str, dict[str, str]] = {}
    for ligne in lignes[debut:fin]:
        if not ligne.startswith("| `RM-"):
            continue
        c = _cellules(ligne)
        if len(c) < 12:
            continue
        items[c[1].strip("`")] = {
            "statut": c[4].strip("`"),
            "chantier": c[9],
            "preuve": c[10],
        }
    return items


def preuves_presentes(preuve: str, racine: Path | None = None) -> list[str]:
    """Les noms de test cites par la colonne `preuve` qui EXISTENT."""
    dossier = racine if racine is not None else TESTS
    return sorted({
        nom for nom in NOM_DE_TEST.findall(preuve)
        if (dossier / (nom + ".py")).is_file()
    })


def se_contredit(item: dict[str, str], racine: Path | None = None) -> bool:
    """La cellule livre une preuve ET declare son chantier a ouvrir."""
    if item["statut"] not in VIVANT:
        return False
    if not A_OUVRIR.match(item["chantier"]):
        return False
    return bool(preuves_presentes(item["preuve"], racine))


def contradictions() -> set[str]:
    return {ident for ident, item in registre().items() if se_contredit(item)}


class UNE_PREUVE_LIVREE_SUPPOSE_UN_CHANTIER(unittest.TestCase):
    def test_l_instrument_lit_bien_le_registre(self) -> None:
        """Sans lecture, le compte serait vide et vert."""
        items = registre()
        self.assertGreater(len(items), 100, "registre anormalement court")
        vivants = [i for i in items.values() if i["statut"] in VIVANT]
        self.assertGreater(len(vivants), 40, "aucun item vivant mesurable")
        self.assertTrue(
            any(A_OUVRIR.match(i["chantier"]) for i in items.values()),
            "plus aucune colonne `a ouvrir` dans tout le registre: le motif a "
            "probablement cesse de correspondre a ce qui s'ecrit")

    def test_l_instrument_DISCRIMINE_au_lieu_de_tout_accuser(self) -> None:
        """La question du `0/7`, posee dans l'autre sens.

        Un instrument qui accuse TOUT est aussi inutile qu'un instrument qui
        n'accuse rien. Mesure du 2026-09-12: 28 contradictions contre 25
        colonnes `a ouvrir` SANS preuve livree - donc la preuve compte
        reellement dans la decision, elle n'est pas decorative.
        """
        items = registre()
        a_ouvrir = [i for i in items.values()
                    if i["statut"] in VIVANT and A_OUVRIR.match(i["chantier"])]
        sans_preuve = [i for i in a_ouvrir if not preuves_presentes(i["preuve"])]
        self.assertTrue(
            sans_preuve,
            "toutes les colonnes `a ouvrir` portent une preuve livree: la "
            "condition sur la preuve ne discrimine plus rien, et la garde "
            "reviendrait a interdire la mention `a ouvrir`")

    def test_l_instrument_RECONNAIT_des_cas_dont_la_reponse_est_connue(self) -> None:
        """Trois cas construits, parce qu'une dette stable peut cacher un arret.

        Le test d'acceptation du depot: le chiffre changerait-il si la chose
        comptee disparaissait ? On le verifie au lieu de l'esperer.
        """
        vrai = {"statut": "BACKLOG", "chantier": "a ouvrir",
                "preuve": "`server/tests/test_arbre_teste.py`, 3 tests"}
        self.assertTrue(
            se_contredit(vrai),
            "une contradiction franche n'est plus vue: la dette de cette garde "
            "ne prouverait alors rien")

        sans_preuve = {"statut": "BACKLOG", "chantier": "a ouvrir",
                       "preuve": "Aucune preuve attendue a ce stade."}
        self.assertFalse(
            se_contredit(sans_preuve),
            "un item sans preuve livree est accuse: la garde interdit la "
            "mention `a ouvrir` au lieu de mesurer une contradiction")

        preuve_fantome = {"statut": "BACKLOG", "chantier": "a ouvrir",
                          "preuve": "`server/tests/test_qui_n_existe_pas.py`"}
        self.assertFalse(
            se_contredit(preuve_fantome),
            "une preuve INTROUVABLE compte comme livree: la garde confondrait "
            "une citation morte avec un travail fait - et les citations mortes "
            "sont deja gardees ailleurs, par "
            "`test_une_preuve_citee_se_trouve`")

        chantier_nomme = {"statut": "BACKLOG",
                          "chantier": "`CH-20260903-090000-RM-2026-0047-x`",
                          "preuve": "`server/tests/test_arbre_teste.py`"}
        self.assertFalse(
            se_contredit(chantier_nomme),
            "un chantier NOMME est encore accuse: la garde ne lit plus la "
            "colonne qu'elle pretend lire")

    def test_la_dette_est_bornee_et_se_redit_quand_elle_change(self) -> None:
        """Egalite d'ensembles, dans les DEUX sens.

        Une borne haute laisse la frontiere reculer; une dette qu'on ne retire
        jamais devient un cimetiere. Un item qui la quitte doit en sortir, et un
        item neuf ne peut pas la rejoindre en silence.
        """
        self.assertEqual(
            sorted(DETTE_2026_09_12), sorted(contradictions()),
            "l'ensemble des cellules qui se contredisent - preuve livree ET "
            "chantier `a ouvrir` - ne coincide plus avec la dette declaree. "
            "Si elle a MONTE: la cellule neuve doit nommer le chantier qui a "
            "produit sa preuve, et un identifiant de chantier ne s'invente "
            "pas - il se trouve dans `docs/presence_agents.md`. Si elle a "
            "BAISSE: retirer l'entree d'ici et le dire au gouvernail.")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
