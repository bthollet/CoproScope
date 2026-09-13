"""Un ecran nomme la copropriete dont il montre les donnees, ou n'en nomme aucune.

`RM-2026-0087`. Douze ecrans affichaient `Copropriete FICTIVE` au-dessus des
donnees de l'instance ouverte. Les chiffres etaient justes; c'est l'identite
seule qui etait inventee, ce qui la rend d'autant plus credible - rien a
l'ecran ne signale la substitution.

**L'axe, et pourquoi le compteur precedent n'etait pas dessus.**
`test_identite_coque.py` comptait les fichiers de `web/` contenant la chaine
exacte `"name": "Copropriete FICTIVE"`. Ce compteur donnait le bon chiffre le
jour ou il a ete ecrit, et il aurait laisse passer, sans un mot:

- un treizieme ecran ecrivant `'name': 'Residence du Parc'` - autre nom, meme
  defaut, aucune occurrence de `FICTIVE`;
- la meme ligne ecrite avec des apostrophes, ou sans l'espace apres les deux
  points;
- la meme ligne posee dans un sous-dossier de `web/`: son `glob("*.py")` est a
  plat, et **27 des 87 modules `.py` de `web/` lui sont invisibles** (mesure du
  2026-09-09 sur `ffac60c`).

Un grep sur une orthographe est une enumeration de modalites. Ce fichier
mesure la DIMENSION: **d'ou vient le nom qu'un ecran affiche.** Deux reponses
seulement sont admissibles - celui de l'instance ouverte, ou aucun. Toute
troisieme valeur echoue, quelle que soit son orthographe et son emplacement.

**Couverture mesuree le 2026-09-09 sur `ffac60c`**, a garder sous les yeux car
c'est elle qui dit si la garde mesure encore quelque chose: le parcours atteint
**65 pages HTML**, dont **31 pages de detail** - `/documents/<id>`,
`/actions/<id>`, `/chantiers/<id>` - qu'aucune route sans parametre n'expose et
dont les identifiants viennent des liens rendus par le produit. Les 65 portent
un titre lisible et une bande de coffre lisible. Les seuils poses plus bas
valent 20: un tiers du mesure, donc francs.

**Reserve declaree.** L'epreuve tourne sur `examples/synthetic_copro`, comme
toute la CI, qui n'a pas le droit de lire une instance privee. Elle prouve donc
que chaque ecran LIT l'identite de l'instance ouverte; elle ne prouve rien sur
la justesse des chiffres affiches a cote.

**Ce que cette garde ne couvre PAS, et qui reste a faire.** Elle verifie qu'un
ecran ne nomme pas une AUTRE copropriete. Elle ne verifie pas qu'un ecran nomme
la sienne de facon VISIBLE dans le corps de page: une page dont l'identite ne
vit que dans `<title>` passe ici, et c'est un defaut distinct - une capture
d'ecran ou une impression ne nomme alors aucune copropriete.
`tests/test_ui_nom_copropriete_pages_travail.py` tient cette seconde propriete,
mais sur **deux pages nommees en dur**, `/comptes` et `/ag-contentieux`. Les 63
autres pages atteintes ici ne sont couvertes par personne sur ce point.

**Refutation du 2026-09-09, sur `4140931`: les deux bras avaient un angle mort
COMMUN, et il n'etait pas theorique.**

Le bras structurel balayait `web/` par `rglob("*.py")`. Or `web/app.py` fait
SEPT lignes: tout `create_app` vit dans `_app_fragments/*.pyfrag`, concatenes
puis `exec`utes. **2956 lignes executees de `web/` etaient hors du balayage**,
et la route `/pieces/<id>` en fait partie. Une extension de fichier est une
modalite, pas un axe: la question est *quelle source Python execute-t-il*.

Le bras comportemental, lui, ne suivait que les liens rendus. `/pieces/<id>`
n'est lie par aucune page atteinte, donc jamais visite - alors qu'il rend 200
en HTML pour n'importe quel identifiant.

L'intersection etait servie et invisible. Mesure: en ecrivant
`{"instance": {"id": "PARC-01", "name": "Residence du Parc", ...}}` dans le
gestionnaire de `/pieces/<id>`, la page servait « Residence du Parc » et
« Coffre PARC-01 » au-dessus des donnees de « Residence Les Platanes », et les
quatre tests de ce fichier restaient VERTS - exactement le defaut que
`RM-2026-0087` nomme, reproduit sous sa propre garde.

Les deux bras ont ete elargis, chacun sur son axe et sans liste d'exceptions:
le balayage lit toute la source executee (`_sources_executees`), et le parcours
SONDE avec un jeton bidon tout patron de route parametree que personne ne lie.
Depuis, la meme injection fait tomber les trois controles en la nommant.
"""

from __future__ import annotations

import ast
import pathlib
import re
import unittest
from contextlib import ExitStack

from coproscope.source_fragments import fragment_sources
from tests._exemple_copie import exemple_copie

WEB = pathlib.Path(__file__).resolve().parent.parent / "src" / "coproscope" / "web"

#: Ce que la coque affiche quand aucune instance n'est ouverte. Ce n'est pas un
#: defaut: c'est alors la verite, et `base.html` la produit par ses `|default`.
TITRE_SANS_IDENTITE = "CoproScope"
COFFRE_SANS_IDENTITE = "local"

_TITRE = re.compile(r"<title>\s*CoproScope\s*-\s*(.*?)\s*</title>", re.S)
#: **La bande d'identite se reconnait a son MARQUEUR DECLARE, pas a une classe.**
#:
#: Cette garde s'ancrait sur `class="instance-meta"`. Un autre lot du meme jour
#: a deplace l'identite hors de ce conteneur, et **la garde est passee de 65
#: pages a 0 sans qu'un seul test de gabarit ne bronche**: elle aurait rendu
#: vert en ne mesurant plus rien, si son propre garde-fou anti-mesure-vide
#: (`vues > 20`) ne l'avait pas attrapee.
#:
#: **Une classe CSS est de la PRESENTATION: elle bouge des qu'on redessine.**
#: `data-cs-identite` est une DECLARATION: l'auteur du gabarit dit *ici se
#: trouve l'identite*. Le second survit a une refonte, le premier non - c'est la
#: meme difference qu'entre lire un statut et lire un nom de dossier.
#: La bande commence a la BALISE qui porte le marqueur, pas au marqueur: sinon
#: le `<span` ouvrant tombe hors du fragment, et `_COFFRE` - qui cherche ce
#: `<span` - ne trouve rien dans une bande pourtant presente. Un decoupage qui
#: coupe au milieu d'une balise n'est pas un decoupage.
_BANDE = re.compile(r'<span[^>]*data-cs-identite=.*?</div>', re.S)
#: Meme correction, meme raison: ce motif attendait un `<span>` NU. Le gabarit
#: porte desormais l'attribut de declaration, et le `<span>` nu n'existe plus.
#: **Deux motifs etaient lies a la presentation, pas un** - c'est ce qui rend
#: ce genre de garde fragile: elle lit la mise en forme au lieu de lire ce que
#: l'auteur du gabarit a DECLARE.
_COFFRE = re.compile(
    r'<span[^>]*data-cs-identite="copropriete"[^>]*>\s*Coffre\s+(.*?)\s*</span>', re.S
)
_LIEN = re.compile(r'href="(/[^"#]*)"')

#: Jeton pose a la place d'un parametre de route pour SONDER un patron que le
#: parcours par liens n'a jamais exerce. Il ne ressemble a aucun identifiant du
#: produit: une route qui ne sait pas le servir rend 404 et sort de la mesure.
SONDE = "sonde-garde-identite"


#: **L'instance est une COPIE** (`RM-2026-0107`). Ce module parcourt les ecrans
#: en servant une application REELLE: tout ce que cette application ecrirait
#: aurait atteint la reference versionnee, et une reference contre laquelle on
#: mesure ne se laisse pas ecrire. Le sens de la mesure est intact - ce qui est
#: mesure est le nom que les ecrans AFFICHENT, donc le contenu de l'instance,
#: que `copytree` reproduit a l'octet.


def _pages_atteignables(client, app) -> dict[str, str]:
    """Toute page HTML qu'un utilisateur peut atteindre en cliquant.

    Le parcours part des routes sans parametre, puis suit les liens rendus.
    Les pages de detail - `/documents/<id>`, `/actions/<id>` - n'ont donc pas
    d'identifiant devine ici: ils viennent du produit lui-meme.
    """
    file = [
        route.path for route in app.routes
        if "GET" in (getattr(route, "methods", set()) or set())
        and "{" not in route.path
    ]
    vus: set[str] = set()
    pages: dict[str, str] = {}
    while file:
        chemin = file.pop(0)
        if chemin in vus:
            continue
        vus.add(chemin)
        try:
            reponse = client.get(chemin)
        except Exception:  # noqa: BLE001  - une route en erreur n'est pas notre sujet
            continue
        if reponse.status_code != 200:
            continue
        if "html" not in reponse.headers.get("content-type", ""):
            continue
        pages[chemin] = reponse.text
        for lien in _LIEN.findall(reponse.text):
            cible = lien.split("?")[0]
            if cible and cible not in vus and not cible.startswith("/static"):
                file.append(cible)

    # Un patron parametre que personne ne lie reste invisible au parcours. Il
    # est sonde avec un jeton bidon: s'il rend une page, elle est mesuree comme
    # les autres; s'il ne sait pas le servir, il rend 404 et sort de lui-meme.
    # Aucune liste d'exceptions n'est necessaire, et aucune route ne peut se
    # soustraire a la mesure en n'etant liee nulle part.
    for patron in _patrons_parametres(app):
        vise = re.sub(r"\{[^}]+\}", SONDE, patron)
        if any(re.fullmatch(_motif(patron), page) for page in pages):
            continue
        try:
            reponse = client.get(vise)
        except Exception:  # noqa: BLE001
            continue
        if reponse.status_code == 200 and "html" in reponse.headers.get("content-type", ""):
            pages[vise] = reponse.text
    return pages


def _motif(patron: str) -> str:
    """Le patron de route, en expression reguliere, litteraux echappes.

    Les parties fixes d'un chemin peuvent porter des caracteres speciaux -
    `/exports/actions.csv` en porte un. Les laisser bruts ferait correspondre
    un chemin qui n'est pas le bon, et la sonde sauterait une route en croyant
    l'avoir deja vue: la garde cesserait de mesurer sans rien dire.
    """
    morceaux = re.split(r"(\{[^}]+\})", patron)
    return "".join("[^/]+" if m.startswith("{") else re.escape(m) for m in morceaux)


def _patrons_parametres(app) -> list[str]:
    return [
        route.path for route in app.routes
        if "GET" in (getattr(route, "methods", set()) or set())
        and "{" in route.path
    ]


class ChaqueEcranNommeLaCoproprieteQuIlMontreTests(unittest.TestCase):
    """La mesure de comportement: ce que la page AFFICHE, sur une vraie instance."""

    @classmethod
    def setUpClass(cls) -> None:
        from fastapi.testclient import TestClient

        from coproscope.web.app import create_app

        cls._pile = ExitStack()
        cls.instance = cls._pile.enter_context(exemple_copie("ecran_source"))
        cls.app = create_app(cls.instance, 2025)
        cls.pages = _pages_atteignables(TestClient(cls.app), cls.app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._pile.close()

    def test_le_parcours_atteint_bien_des_ecrans(self) -> None:
        """Une garde qui ne mesure rien est pire que pas de garde.

        Si le parcours cesse d'atteindre des pages - route d'accueil deplacee,
        jeton exige, gabarit sans lien - les deux tests suivants deviendraient
        verts en ne regardant rien. Ce test les en empeche.
        """
        self.assertGreater(
            len(self.pages), 20,
            "Le parcours n'atteint plus que "
            f"{len(self.pages)} page(s) HTML: la garde d'identite ne mesure "
            "presque plus rien. Reparer le parcours avant de lire les deux "
            "tests suivants comme des preuves.")

    def test_aucun_ecran_n_affiche_le_nom_d_une_autre_copropriete(self) -> None:
        attendu = str(getattr(self.instance, "display_name", "") or "")
        self.assertTrue(attendu, "L'instance d'epreuve n'a pas de display_name")

        sans_titre: list[str] = []
        fautifs: list[str] = []
        for chemin, html in sorted(self.pages.items()):
            trouve = _TITRE.search(html)
            if trouve is None:
                sans_titre.append(chemin)
                continue
            nom = trouve.group(1)
            if nom not in (attendu, TITRE_SANS_IDENTITE):
                fautifs.append(f"{chemin} affiche « {nom} »")

        self.assertEqual(
            sans_titre, [],
            "\n\n  Ces pages n'ont plus le titre que la garde sait lire; elle\n"
            "  ne mesure donc plus rien sur elles:\n    "
            + "\n    ".join(sans_titre) + "\n")
        self.assertEqual(
            fautifs, [],
            "\n\n  Un ecran nomme une copropriete qui n'est pas celle dont il\n"
            f"  montre les donnees. Instance ouverte: « {attendu} ».\n\n    "
            + "\n    ".join(fautifs)
            + "\n\n  Un ecran nomme la copropriete de ses donnees, ou n'en nomme\n"
            "  aucune. Le bloc `model[\"instance\"]` doit venir de\n"
            "  `identite_coque(instance, year)`, jamais d'un litteral.\n")

    def test_aucun_ecran_n_affiche_l_identifiant_d_un_autre_coffre(self) -> None:
        attendu = str(getattr(self.instance, "instance_id", "") or "")
        self.assertTrue(attendu, "L'instance d'epreuve n'a pas d'instance_id")

        fautifs: list[str] = []
        vues = 0
        for chemin, html in sorted(self.pages.items()):
            bande = _BANDE.search(html)
            if bande is None:
                continue
            coffre = _COFFRE.search(bande.group(0))
            if coffre is None:
                continue
            vues += 1
            valeur = coffre.group(1)
            if valeur not in (attendu, COFFRE_SANS_IDENTITE):
                fautifs.append(f"{chemin} affiche « Coffre {valeur} »")

        self.assertGreater(
            vues, 20,
            f"La bande d'identite n'est lisible que sur {vues} page(s): la "
            "garde d'identifiant de coffre ne mesure presque plus rien.")
        self.assertEqual(
            fautifs, [],
            "\n\n  Un ecran affiche l'identifiant d'un autre coffre que celui\n"
            f"  qui est ouvert (« {attendu} »):\n\n    "
            + "\n    ".join(fautifs) + "\n")


class AucuneIdentiteDeCoproprieteEcriteEnDurTests(unittest.TestCase):
    """La mesure de structure, en complement: personne ne REFABRIQUE l'identite.

    Le test de comportement ci-dessus ne voit que les pages atteignables. Celui-ci
    balaie **tout** `web/`, sous-dossiers compris, et ne cherche aucun mot: il
    cherche une FORME - un bloc `"instance"` dont le `"name"` est une chaine
    litterale. Un nouveau nom fabrique, quelle que soit son orthographe, tombe
    dessus.

    Il n'a **aucune liste d'exceptions**, et ne doit jamais en recevoir une:
    l'unique source autorisee est `identite_coque`, qui construit son bloc a
    partir de l'instance et non d'un litteral.
    """

    def test_aucun_module_de_web_ne_fabrique_un_bloc_instance(self) -> None:
        fautifs: list[str] = []
        sources = _sources_executees()
        for etiquette, source in sources:
            arbre = ast.parse(source)
            for noeud in ast.walk(arbre):
                if not isinstance(noeud, ast.Dict):
                    continue
                for cle, valeur in _cles(noeud).items():
                    if cle != "instance" or not isinstance(valeur, ast.Dict):
                        continue
                    nom = _cles(valeur).get("name")
                    if isinstance(nom, ast.Constant) and isinstance(nom.value, str):
                        fautifs.append(
                            f"{etiquette}:{noeud.lineno} "
                            f"ecrit name={nom.value!r}")

        self.assertGreater(
            len(sources), 50,
            f"Le balayage ne lit plus que {len(sources)} source(s) de "
            "`web/`: il ne mesure presque plus rien.")
        fragments = [etiq for etiq, _ in sources if etiq.endswith("#fragments")]
        self.assertTrue(
            fragments,
            "Le balayage ne lit AUCUN repertoire de fragments, alors que "
            "`web/` en contenait trois le 2026-09-09 - dont celui qui porte "
            "`create_app` et la route `/pieces/<id>`. Une garde qui a cesse "
            "de les lire rend vert sur du code qu'elle ne regarde pas.")
        self.assertEqual(
            fautifs, [],
            "\n\n  Un module de `web/` construit une identite de copropriete a\n"
            "  la main. Le nom affiche viendrait alors du code, pas des donnees\n"
            "  montrees:\n\n    "
            + "\n    ".join(fautifs)
            + "\n\n  Remplacer le litteral par `identite_coque(instance, year)`\n"
            "  et faire descendre `instance` jusqu'a la vue.\n")


def _sources_executees() -> list[tuple[str, str]]:
    """Toute la source que Python EXECUTE dans `web/`, etiquetee.

    Un `rglob("*.py")` decrit une EXTENSION, pas du code. Dans ce depot les
    modules trop longs sont decoupes en fragments que `app.py` concatene puis
    `exec`ute: `web/app.py` fait SEPT lignes, et tout `create_app` vit ailleurs.
    Mesure du 2026-09-09 sur `4140931`: 2956 lignes executees de `web/` sont
    hors de portee d'un balayage `*.py` - dont la route `/pieces/<id>`.

    Le suffixe n'est pas re-ecrit ici: il vient de `source_fragments`, qui est
    ce qui execute ces fichiers. Si le decoupage change, la garde suit au lieu
    de rester sur une valeur perimee.

    Un fragment n'est pas parsable seul - le decoupage tombe au milieu des
    expressions - donc l'unite lue est le repertoire concatene, exactement
    comme a l'execution.
    """
    sources = [
        (str(chemin.relative_to(WEB)),
         chemin.read_text(encoding="utf-8", errors="replace"))
        for chemin in sorted(WEB.rglob("*.py"))
    ]
    return sources + fragment_sources(WEB)


def _cles(noeud: ast.Dict) -> dict[str, ast.expr]:
    return {
        cle.value: valeur
        for cle, valeur in zip(noeud.keys, noeud.values)
        if isinstance(cle, ast.Constant) and isinstance(cle.value, str)
    }


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
