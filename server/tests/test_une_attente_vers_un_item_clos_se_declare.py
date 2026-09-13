# -*- coding: utf-8 -*-
"""Un item vivant qui attend un item CLOS le dit, ou son attente est levee.

**Le motif, et il a coute plus de trois mois chacun a deux items.**
`RM-2026-0003` et `RM-2026-0008` attendaient `RM-2026-0017`, **ABANDONNE depuis
le 2026-05-31** - donc un evenement qui n'arriverait jamais. Aucun des deux ne
le savait, et **rien ne le signalait**: une dependance vers un chantier clos
n'immobilise pas bruyamment, elle immobilise **en silence**. Les deux ont ete
debloques a la main le 2026-09-09, par un tri qui a eu lieu parce que quelqu'un
a pense a le faire.

C'est la forme exacte de `RM-2026-0125` - le lanceur approuve qui mourait sans
rien dire - et de la consigne canonique qui a nomme cinq fois une instance
disparue: **une reference qui ne repond plus coute plus cher qu'une reference
absente, parce qu'elle est suivie.**

----------------------------------------------------------------------
L'axe, l'invariant, et ce qui se passe hors des valeurs observees
----------------------------------------------------------------------

- **L'axe.** *Une dependance declaree entre deux items.* Le degre de liberte est
  la TOURNURE - `depend de`, `attend`, `ne pas ouvrir avant`, `bloque par`,
  `subordonne a`, et toutes celles que personne n'a encore ecrites.
- **L'invariant le long de l'axe.** Un item VIVANT qui cite un item CLOS dans
  une tournure d'attente doit, **a proximite de la citation**, dire que cette
  attente est levee - ou pourquoi elle tient malgre la cloture.
- **Ce que le code en fait.** Il ne juge pas la dependance: il exige qu'elle
  soit **RACONTEE**. Un item qui dit *j'attendais X, X est abandonne, donc rien
  ne me bloque* passe; un item qui dit *depend de X* alors que X est integre
  echoue, en nommant les deux.
- **Hors des valeurs observees.** Une tournure inconnue n'est pas detectee. Le
  compte de cette garde est donc un **PLANCHER, jamais un inventaire**, et c'est
  ecrit ici parce qu'un plancher presente comme un total est la faute que ce
  depot nomme *un chiffre qui a l'air d'une preuve*. La degradation est du bon
  cote: on rate une attente muette, on n'en invente pas.

**CE QU'ELLE NE FAIT PAS, et il faut le dire.** Elle ne verifie pas qu'une
dependance declaree est VRAIE - seulement qu'elle n'est pas perimee. Un item
peut dependre d'un item vivant qui, en fait, ne le bloque pas: cette garde-la
n'existe pas, et elle demanderait de lire le fond de chaque couple.

**LA PROXIMITE EST UN CHOIX, et elle est le meme que celui de
`test_une_instance_jetable_citee_se_declare`:** la mention doit etre pres de la
citation, parce qu'une cellule de plusieurs milliers de caracteres peut parler
de tout autre chose a l'autre bout, et un lecteur qui tombe sur *depend de X*
ne remonte pas la cellule pour verifier si quelqu'un l'a dementi ailleurs.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

GOUVERNAIL = (
    Path(__file__).resolve().parents[2] / "docs" / "roadmap_backlog_central.md"
)
TITRE_REGISTRE = "## Registre actif par identifiant"

#: Une barre NUE separe deux cellules; une barre echappee est du texte.
_BARRE_NUE = re.compile(r"(?<!\\)\|")

#: Les statuts qui closent un item: plus rien n'en sortira.
CLOS = frozenset({"INTEGRE", "ABANDONNE", "CLOTURE"})

#: Les tournures qui ENONCENT une attente. **Enumeration assumee**, et c'est
#: pour cela que le compte est un plancher: voir l'en-tete.
ATTENTE = re.compile(
    r"(?:d[eé]pend(?:ance)?\s+(?:de|du|des)|attend(?:re)?|"
    r"ne pas ouvrir avant|bloqu[eé]\s+par|subordonn[eé]\s+[àa]|"
    r"conditionn[eé]\s+[àa]|apr[èe]s\s+l(?:'|e\s)integration)"
    r"[^.;]{0,90}?(RM-\d{4}-\d{4})",
    re.I,
)

#: Ce qui RACONTE la cloture au lieu de la subir. Le mot `DEBLOQUE` et ses
#: voisins disent qu'on a vu, et c'est tout ce qu'on demande.
DECLARE = re.compile(
    r"DEBLOQU|ABANDONN|INTEGRE|CLOTUR|lev[eé]e?\b|n(?:'|e )existe plus|"
    r"n'arrivera jamais|attendait|est clos|deja satisfait|sans objet",
    re.I,
)

#: Fenetre, en caracteres, autour de la citation. Meme ordre de grandeur que la
#: garde soeur sur les instances jetables: assez large pour une phrase, trop
#: etroite pour qu'un dementi a l'autre bout de la cellule compte.
PROXIMITE = 260


def _cellules(ligne: str) -> list[str]:
    brut = _BARRE_NUE.split(ligne)
    if len(brut) < 3:
        return []
    return [c.strip() for c in brut]


def registre() -> dict[str, dict[str, str]]:
    """Les items du registre actif, par identifiant."""
    texte = GOUVERNAIL.read_text(encoding="utf-8")
    lignes = texte.splitlines()
    debut = next((i for i, l in enumerate(lignes)
                  if l.startswith(TITRE_REGISTRE)), None)
    if debut is None:
        raise LookupError(
            "titre %r introuvable: le registre a ete renomme ou deplace, et "
            "une mesure qui rendrait zero item passerait pour un registre sain"
            % TITRE_REGISTRE)
    fin = next((i for i, l in enumerate(lignes[debut + 1:], debut + 1)
                if l.startswith("## ")), len(lignes))
    items: dict[str, dict[str, str]] = {}
    for ligne in lignes[debut:fin]:
        if not ligne.startswith("| `RM-"):
            continue
        c = _cellules(ligne)
        if len(c) < 12:
            continue
        ident = c[1].strip("`")
        items[ident] = {
            "statut": c[4].strip("`"),
            "prose": c[8] + " " + c[10],
        }
    return items


def attentes_perimees(items: dict[str, dict[str, str]]) -> list[tuple[str, str, str]]:
    """Les couples (item vivant, item clos, extrait) dont la cloture est MUETTE."""
    muettes: list[tuple[str, str, str]] = []
    vus: set[tuple[str, str]] = set()
    for ident, item in items.items():
        if item["statut"] in CLOS:
            continue
        prose = item["prose"]
        for trouve in ATTENTE.finditer(prose):
            cite = trouve.group(1)
            if cite == ident or (ident, cite) in vus:
                continue
            etat = items.get(cite, {}).get("statut")
            if etat not in CLOS:
                continue
            voisinage = prose[max(0, trouve.start() - PROXIMITE):
                              trouve.end() + PROXIMITE]
            if DECLARE.search(voisinage):
                continue
            vus.add((ident, cite))
            muettes.append((ident, cite, " ".join(voisinage.split())[:200]))
    return muettes


class UNE_ATTENTE_VERS_UN_ITEM_CLOS_SE_DECLARE(unittest.TestCase):
    def test_l_instrument_lit_bien_le_registre(self) -> None:
        """Sans lecture, le compte ci-dessous serait vide et vert.

        Le defaut que ce temoin ferme est celui du `0/7`: un instrument casse
        n'epargne aucun cas, donc son zero ressemble a une bonne nouvelle.
        """
        items = registre()
        self.assertGreater(len(items), 100, "registre anormalement court")
        statuts = {item["statut"] for item in items.values()}
        self.assertTrue(
            statuts & CLOS,
            "aucun item clos dans le registre: la garde ne peut rien mesurer, "
            "et son silence ne prouverait donc rien")
        self.assertTrue(
            any(ATTENTE.search(item["prose"]) for item in items.values()),
            "aucune tournure d'attente reconnue dans tout le registre: le "
            "motif a probablement cesse de correspondre a ce qui s'ecrit")

    def test_l_instrument_RECONNAIT_des_cas_dont_la_reponse_est_connue(self) -> None:
        """La sonde, et elle n'est pas decorative.

        Une garde dont la dette tombe a zero peut aussi bien avoir cesse de
        mesurer. On lui passe donc trois cas construits: une attente muette vers
        un item clos DOIT etre vue; la meme attente racontee ne doit PAS l'etre;
        une attente vers un item VIVANT ne doit pas l'etre non plus.
        """
        socle = {
            "RM-2026-9001": {"statut": "INTEGRE", "prose": "rien"},
            "RM-2026-9002": {"statut": "BACKLOG", "prose": "rien"},
        }

        muet = dict(socle)
        muet["RM-2026-9100"] = {
            "statut": "BACKLOG",
            "prose": "Depend de `RM-2026-9001` pour la lecture des pieces.",
        }
        self.assertEqual(
            [("RM-2026-9100", "RM-2026-9001")],
            [(a, b) for a, b, _ in attentes_perimees(muet)],
            "une attente muette vers un item INTEGRE n'est plus vue: la dette "
            "vide de cette garde ne prouverait alors rien")

        raconte = dict(socle)
        raconte["RM-2026-9101"] = {
            "statut": "BACKLOG",
            "prose": ("Cet item attendait `RM-2026-9001`, INTEGRE depuis, donc "
                      "l'attente est levee et rien ne le bloque."),
        }
        self.assertEqual(
            [], attentes_perimees(raconte),
            "une attente RACONTEE est signalee comme muette: la garde "
            "deviendrait une nuisance qu'on fait taire, et une garde qu'on "
            "fait taire ne garde plus rien")

        vivant = dict(socle)
        vivant["RM-2026-9102"] = {
            "statut": "BACKLOG",
            "prose": "Depend de `RM-2026-9002`, qui n'est pas encore livre.",
        }
        self.assertEqual(
            [], attentes_perimees(vivant),
            "une attente vers un item VIVANT est signalee: la garde confond "
            "une dependance normale avec une dependance perimee")

    def test_aucune_attente_vers_un_item_clos_ne_reste_muette(self) -> None:
        """Le coeur de la garde.

        **Deux issues, jamais une troisieme.** Soit l'attente est levee et la
        cellule le DIT - au passe, en nommant la cloture; soit elle tient
        malgre la cloture, et la cellule explique pourquoi. Ce qui est interdit
        est le silence, parce que le silence se lit comme une attente vivante.
        """
        muettes = attentes_perimees(registre())
        self.assertEqual(
            [], [(a, b) for a, b, _ in muettes],
            "ces items VIVANTS declarent attendre un item CLOS sans le dire. "
            "Une dependance vers un item clos n'immobilise pas bruyamment: "
            "elle immobilise en silence, et c'est ce qui a fige "
            "`RM-2026-0003` et `RM-2026-0008` plus de trois mois chacun. "
            "Deux issues: dire que l'attente est levee, ou dire pourquoi elle "
            "tient. Detail: %s"
            % [(a, b, extrait) for a, b, extrait in muettes])

    def test_toute_attente_cite_un_item_QUI_EXISTE(self) -> None:
        """Une citation qui ne designe rien n'est pas une dependance.

        Ce cas ne se confond pas avec le precedent et ne doit jamais passer
        pour lui: un identifiant absent du registre n'est pas une attente
        levee, c'est une attente **invérifiable**. L'etat 2 d'un controle a
        trois etats n'est jamais un feu vert.
        """
        items = registre()
        fantomes: list[tuple[str, str]] = []
        for ident, item in items.items():
            for trouve in ATTENTE.finditer(item["prose"]):
                cite = trouve.group(1)
                if cite != ident and cite not in items:
                    fantomes.append((ident, cite))
        self.assertEqual(
            [], sorted(set(fantomes)),
            "ces items declarent attendre un identifiant ABSENT du registre "
            "actif. Ce n'est pas une attente levee, c'est une attente qu'on ne "
            "peut pas verifier: soit l'item cite a ete renumerote et la "
            "citation doit suivre, soit il n'a jamais existe. %s"
            % sorted(set(fantomes)))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
