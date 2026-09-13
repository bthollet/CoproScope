# -*- coding: utf-8 -*-
"""Une fixture ne bouge pas sous les tests qui mesurent contre elle.

**Le fait qui ouvre `RM-2026-0107`.** Trois fichiers SUIVIS de l'instance
d'exemple ont ete trouves modifies dans un arbre partage - le registre des
documents et les deux registres de confidentialite - un document y basculant de
`raw / none` a `redaction_required / RGPD;vie_privee`. Personne n'a reproduit la
mutation, ni le signaleur ni le fil qui a verifie. **Cette garde ne cherche donc
pas le coupable: elle rend la prochaine mutation impossible a manquer.**

**Un faux positif rencontre le 2026-09-09, et il faut savoir le reconnaitre.**
Cette garde compare les OCTETS DU DISQUE. Or `.gitattributes` declare
`* text=auto eol=lf` depuis le 2026-05-23, alors que les fichiers de la
reference datent des 20 et 21 mai: dans un arbre de travail cree AVANT cette
declaration, dix-huit d'entre eux portent encore des fins de ligne Windows, et
git les considere identiques parce qu'il normalise a la lecture. La garde a
donc annonce *contenu modifie (18)* sur des fichiers que `git status` disait
propres, avec des ecarts de 1 a 117 octets - exactement leur nombre de lignes.

**L'arbre etait l'anomalie, pas la reference.** Tout clone recent rend ces
fichiers en LF, et c'est ce que la reference porte. La remise en conformite se
fait sur l'ARBRE - supprimer les fichiers suivis concernes puis
`git checkout -- <dossier>` - et `git status` doit rester vide apres, ce qui
prouve qu'on n'a rien change de ce que git stocke. `git add --renormalize` ne
suffit pas: il ne reecrit que l'index.

**Ce residu n'est pas corrige ici, et c'est un choix.** Empreindre le contenu
normalise rendrait la garde insensible a la plateforme, mais lui ferait mesurer
autre chose que ce qui est sur le disque - or la mutation d'origine, elle,
etait bien sur le disque. Le signe distinctif est nomme a la place: **des
ecarts de quelques octets sur des fichiers que `git status` dit propres sont
des fins de ligne, jamais une mutation.**

**Pourquoi le defaut est grave alors qu'il ne casse rien.** Il ne fait echouer
aucun test: il DEPLACE LA BASE. Un `git status` sali a chaque passage appelle le
`git add -A`, et si quelqu'un commite la mutation, la reference devient
silencieusement le resultat du dernier passage. Plus personne ne mesure contre
l'etalon; tout le monde mesure contre sa derniere sortie. Meme famille que le
venv partage qui faisait passer des tests verts sur le code d'un autre arbre.

## Les deux proprietes gardees, et pourquoi ce sont des axes

**(1) La reference est immuable tant qu'on mesure contre elle.** L'empreinte de
chaque fichier versionne est arretee dans un fichier compagnon. Toute
divergence est nommee, fichier par fichier, avec l'empreinte d'avant et celle
d'apres.

*Ce qui distingue cette garde d'un controle de proprete de l'arbre de travail,
et c'est le coeur du lot:* un `git status` en fin de suite attrape la mutation
NON COMMITEE, et devient muet pour toujours des qu'elle est commitee - c'est-a-
dire au moment exact ou elle devient dangereuse. L'empreinte, elle, vit hors du
dossier qu'elle garde: un `git add -A` emporte la fixture mutee et n'emporte pas
l'empreinte, donc le passage suivant rougit. Pour faire taire cette garde il
faut regenerer l'empreinte a la main, ce qui inscrit dans le diff que la
reference a change **parce qu'on l'a voulu**.

**(2) Un document porte l'empreinte de ce qu'il represente.** Le produit forge
ses identifiants de document par `DOC-{sha256[:12].upper()}`, en **cinq**
endroits de `server/src` - comptage refait le 2026-09-09, la premiere version de
ce texte en annoncait six. L'identifiant EST donc l'empreinte du contenu, et
c'est ce qui rend la mutation d'une piece silencieuse pour les tests: treize
modules de test citent des identifiants de cette forme; changer les octets du
fichier sans changer son nom leur fait mesurer un autre document sous le meme
nom, sans une seule assertion en echec.

## Deux trous mesures le 2026-09-09, et ce qu'ils ont appris

La premiere version de ce module rendait `Ran 8 tests OK` sur trois etats
FAUX, ou le contenu d'une piece ne correspondait plus a son identifiant. Les
trois sont rejoues en mutation, et les deux causes ont la meme forme: **la
portee et la forme etaient ecrites, pas derivees.**

1. **La forme de l'identifiant codait deux modalites.** Le motif etait
   `^DOC-([0-9A-F]{12})$`, donc `DOC-4e884d06e0ad` (meme regle, autre casse) et
   `DOC-4E884D06E0AD2AF7` (meme regle, seize caracteres) tombaient dans le sac
   des etiquettes ecrites a la main. Un identifiant faux en sortait sans un mot.
   L'axe est *une tete hexadecimale est une pretention de derivation*; la
   longueur et la casse sont des degres de liberte, et la comparaison se fait
   desormais par PREFIXE, sans casse.
2. **La portee du controle d'identite etait un nom d'instance ecrit en dur.**
   Une seconde instance posee sous `examples/` - manifeste declarant un sha256
   faux, une taille fausse, un `DOC-AAAAAAAAAAAA` qui ne derivait de rien -
   passait entierement au travers. La portee vient maintenant de git, comme
   celle de l'empreinte: **toute instance versionnee** est controlee, et une
   instance versionnee qui ne declare aucun manifeste echoue en se nommant.

**Ce qui se degrade proprement le long de l'axe (2).** Tous les identifiants ne
sont pas derives: certains sont des etiquettes ecrites a la main. La garde ne
les enumere pas - une liste de noms serait une modalite, morte au premier
identifiant suivant. Elle applique la regle **a ce qui a la FORME d'une
pretention de derivation**, compte le reste, et refuse de conclure si plus rien
n'a cette forme. Une etiquette inconnue arrivant demain n'est donc pas jugee a
tort tant qu'elle porte une lettre non hexadecimale - ce que font toutes celles
que le produit ecrit, verifie dans `FORMES_NON_DERIVEES_ATTESTEES`.

## Ce que cette garde ne detecte pas

- **Une mutation faite puis defaite pendant le meme passage.** L'empreinte est
  comparee a un instant, pas en continu. Un test qui ecrit dans la fixture et
  restaure avant la fin reste invisible.
- **Une mutation commise par un test qui s'execute APRES ce module.** L'ordre
  de `unittest` est alphabetique, et quatre des cinq modules qui lisent
  l'instance sans la copier passent apres celui-ci. Une fixture salie par eux
  n'est vue qu'au passage suivant - jamais jamais, mais pas tout de suite.
- **Une regeneration deliberee mais irreflechie.** Regenerer l'empreinte est un
  geste explicite; rien ne juge s'il etait justifie. La garde deplace la
  question du silence vers le diff, elle ne la tranche pas.
- **Le contenu lui-meme.** Elle prouve qu'une fixture n'a pas bouge, jamais
  qu'elle etait juste au depart.
- **Une etiquette reutilisee pour un autre contenu.** Un identifiant qui ne
  porte pas de tete hexadecimale ne dit rien de ce qu'il designe; seul son hash
  le protege.
- **Une etiquette ecrite a la main qui serait, par hasard, purement
  hexadecimale sur huit caracteres ou plus.** Elle serait jugee comme une
  pretention de derivation et signalee a tort. C'est un faux positif BRUYANT et
  diagnosticable en une ligne, choisi contre le silence de l'inverse.
- **Un corpus versionne qui ne serait pas sous `examples/`.** La portee de
  l'empreinte est ce dossier, comme le demande `RM-2026-0107`. Aujourd'hui c'est
  exact - un seul `instance.yml` est versionne dans le depot - mais rien ne le
  redit si cela change.
"""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path

from coproscope.core.common import load_instance

from tests._empreinte_fixtures import (
    divergences,
    empreinte_constatee,
    empreinte_du_fichier,
    empreinte_enregistree,
    fichiers_non_suivis_non_ignores,
    fichiers_suivis,
    instances_versionnees,
)

#: La forme d'un identifiant qui PRETEND deriver du contenu: le prefixe du
#: produit, puis une tete hexadecimale.
#:
#: **Ce motif a ete elargi le 2026-09-09 apres deux mesures.** Il s'ecrivait
#: `^DOC-([0-9A-F]{12})$`, ce qui codait deux modalites observees - la casse et
#: la longueur - au lieu de l'axe. Sur l'instance de reference laissee dans un
#: etat FAUX, contenu desaccorde de son identifiant, le controle rendait
#: `Ran 8 tests OK` des que l'identifiant s'ecrivait `DOC-4e884d06e0ad`
#: (meme regle, autre casse) ou `DOC-4E884D06E0AD2AF7` (meme regle, prefixe de
#: seize caracteres). Dans les deux cas l'identifiant tombait dans le sac des
#: etiquettes ecrites a la main et sortait du controle sans un mot.
#:
#: L'axe est: *une tete hexadecimale est une pretention de derivation*. La
#: longueur et la casse sont des degres de liberte le long de cet axe, et le
#: controle compare desormais un PREFIXE, sans casse, quelle que soit sa
#: longueur.
FORME_IDENTIFIANT_DERIVE = re.compile(r"^DOC-([0-9A-Fa-f]{8,64})$")

#: Le seuil separe deux familles que le code produit reellement, et il se situe
#: strictement entre elles: les compteurs forgent `DOC-{n:04d}` et
#: `DOC-SCAN-{n:04d}` (quatre chiffres), les empreintes forgent
#: `DOC-{sha256[:12].upper()}` (douze). Tout seuil de 5 a 12 les separe; 8 est
#: pris au milieu. `test_la_forme_derivee_separe_les_deux_familles` echoue si
#: cette separation cesse d'etre vraie.
LONGUEUR_MINIMALE_TETE_HEXADECIMALE = 8

#: Ce que le produit ecrit et qui n'est PAS une pretention de derivation: des
#: compteurs et des etiquettes. Ces valeurs sont relevees dans `server/src`;
#: elles ne servent pas de portee au controle - elles servent a prouver que le
#: motif ci-dessus ne les avale pas.
FORMES_NON_DERIVEES_ATTESTEES = (
    "DOC-0001",
    "DOC-SCAN-0001",
    "DOC-UNKNOWN",
    "DOC-A-NOMMER-003",
    "DOC-FICTIF-B12-ASSUR",
    "DEMO-DOC-003",
)


def _lignes_du_manifeste(chemin: Path) -> list[dict[str, str]]:
    with chemin.open(encoding="utf-8", newline="") as flux:
        return [dict(ligne) for ligne in csv.DictReader(flux)]


class ReferenceVersionneeImmuable(unittest.TestCase):
    """Axe (1): la reference ne bouge pas sans qu'on l'ait decide."""

    def setUp(self) -> None:
        self.enregistree = empreinte_enregistree()
        self.constatee = empreinte_constatee()

    def test_la_garde_mesure_quelque_chose(self) -> None:
        """Non-vacuite. Une boucle sur un ensemble vide rend vert et aveugle.

        Ce test n'est pas de la ceinture et bretelles: c'est le mode de panne
        le plus discret du depot - `Ran 14 tests, OK` sur quatorze boucles qui
        n'ont execute aucune assertion, parce que la collection parcourue etait
        vide. Ici, un `examples/` vide ou une empreinte videe ferait passer tous
        les autres tests de ce module.
        """
        self.assertGreater(
            len(self.constatee),
            0,
            "aucun fichier suivi sous examples/: les tests suivants ne "
            "compareraient rien et rendraient vert",
        )
        self.assertGreater(
            len(self.enregistree),
            0,
            "l'empreinte enregistree est vide: elle ne peut rien contredire",
        )

    def test_aucun_fichier_de_la_reference_n_a_change(self) -> None:
        ecarts = divergences(self.enregistree, self.constatee)
        messages: list[str] = []
        if ecarts["contenu"]:
            messages.append(
                "contenu modifie (%d):\n  %s"
                % (len(ecarts["contenu"]), "\n  ".join(ecarts["contenu"]))
            )
        if ecarts["entres"]:
            messages.append(
                "entres dans la reference sans etre inscrits a l'empreinte (%d):\n  %s"
                % (len(ecarts["entres"]), "\n  ".join(ecarts["entres"]))
            )
        if ecarts["sortis"]:
            messages.append(
                "sortis de la reference (%d):\n  %s"
                % (len(ecarts["sortis"]), "\n  ".join(ecarts["sortis"]))
            )
        self.assertEqual(
            [],
            messages,
            "la reference versionnee a bouge, donc les tests qui mesurent "
            "contre elle ne mesurent plus la meme chose.\n"
            + "\n".join(messages)
            + "\n\nSi le changement est VOULU, arreter la nouvelle reference:\n"
            "  python server/tests/_empreinte_fixtures.py --ecrire\n"
            "et le diff dira que la reference a change parce qu'on l'a decide.",
        )

    def test_rien_ne_s_ajoute_a_cote_de_la_reference(self) -> None:
        """Le piege du `git add -A`, mesure avant qu'il ne se referme.

        Un fichier non suivi et non ignore, pose sous `examples/` par une
        execution, entre dans le depot au premier `git add -A`. La reference
        grandit alors sans decision, et personne ne saura dire quel passage l'a
        ecrit.
        """
        intrus = fichiers_non_suivis_non_ignores()
        self.assertEqual(
            [],
            intrus,
            "des fichiers non suivis et non ignores se sont poses dans la "
            "reference; un `git add -A` les ferait entrer:\n  "
            + "\n  ".join(intrus),
        )

    def test_l_empreinte_couvre_exactement_ce_que_git_suit(self) -> None:
        """La portee est DERIVEE de git, jamais recopiee dans l'empreinte.

        Sans ce test, l'empreinte pourrait devenir une liste ecrite une fois:
        un fichier ajoute a la reference n'y figurerait pas, et son absence
        passerait pour une conformite.
        """
        suivis = set(fichiers_suivis())
        inscrits = set(self.enregistree)
        self.assertEqual(
            sorted(suivis - inscrits),
            [],
            "des fichiers suivis echappent a l'empreinte: elle ne les garde pas",
        )
        self.assertEqual(
            sorted(inscrits - suivis),
            [],
            "l'empreinte garde des fichiers que git ne suit plus",
        )


class IdentiteDeriveeDuContenu(unittest.TestCase):
    """Axe (2): un identifiant derive doit rester l'empreinte de son contenu."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.instances: list[tuple[Path, Path, list[dict[str, str]]]] = []
        cls.sans_manifeste: list[str] = []
        for racine in instances_versionnees():
            config = load_instance(None, str(racine))
            try:
                chemin = config.register("manifest")
            except KeyError:
                cls.sans_manifeste.append(racine.name)
                continue
            if not chemin.exists():
                cls.sans_manifeste.append(racine.name)
                continue
            cls.instances.append((racine, config.root("raw"), _lignes_du_manifeste(chemin)))

    def _lignes(self):
        for racine, _, lignes in self.instances:
            for ligne in lignes:
                yield racine, ligne

    def test_toute_instance_versionnee_declare_son_manifeste(self) -> None:
        """La portee vient de git; une instance sans manifeste ne s'ignore pas.

        Une instance de reference dont aucune ligne ne declare l'empreinte de
        ses pieces n'est pas gardee. Le silence serait la mauvaise reponse: on
        la nomme, et on echoue.
        """
        self.assertEqual(
            [],
            self.sans_manifeste,
            "des instances versionnees ne declarent aucun manifeste lisible, "
            "donc rien ne garde l'identite de leurs pieces: %s"
            % ", ".join(self.sans_manifeste),
        )

    def test_le_manifeste_declare_quelque_chose(self) -> None:
        """Non-vacuite, et elle a deja manque ailleurs dans ce depot."""
        self.assertGreater(
            len(self.instances),
            0,
            "aucune instance versionnee trouvee sous la reference: les tests "
            "suivants boucleraient sur rien et rendraient vert",
        )
        lignes = list(self._lignes())
        self.assertGreater(
            len(lignes),
            0,
            "les manifestes des instances de reference sont vides: les tests "
            "suivants boucleraient sur rien et rendraient vert",
        )
        derives = [
            ligne
            for _, ligne in lignes
            if FORME_IDENTIFIANT_DERIVE.match((ligne.get("doc_id") or "").strip())
        ]
        self.assertGreater(
            len(derives),
            0,
            "plus aucun identifiant des manifestes n'a la forme derivee: le "
            "controle d'identite ne porte plus sur rien",
        )

    def test_la_forme_derivee_separe_les_deux_familles(self) -> None:
        """Le motif nomme un axe, et on verifie qu'il ne code pas des modalites.

        Sans ce test, le motif redevient silencieusement une enumeration: c'est
        ce qui s'est passe le 2026-09-08, ou `^DOC-([0-9A-F]{12})$` laissait
        passer sans un mot un identifiant faux ecrit en minuscules ou sur seize
        caracteres. Les deux formes ci-dessous sont donc jouees explicitement.
        """
        for pretention in (
            "DOC-4e884d06e0ad",
            "DOC-4E884D06E0AD",
            "DOC-4E884D06E0AD2AF7",
            "DOC-" + "a" * 64,
        ):
            self.assertIsNotNone(
                FORME_IDENTIFIANT_DERIVE.match(pretention),
                "%s a une tete hexadecimale: c'est une pretention de derivation "
                "et elle doit etre controlee, pas rangee parmi les etiquettes"
                % pretention,
            )
        for etiquette in FORMES_NON_DERIVEES_ATTESTEES:
            self.assertIsNone(
                FORME_IDENTIFIANT_DERIVE.match(etiquette),
                "%s est une forme que le produit ecrit sans deriver de rien; la "
                "juger comme derivee serait une fausse alerte" % etiquette,
            )
        self.assertLess(
            4,
            LONGUEUR_MINIMALE_TETE_HEXADECIMALE,
            "le seuil doit rester au-dessus des compteurs a quatre chiffres",
        )
        self.assertLessEqual(
            LONGUEUR_MINIMALE_TETE_HEXADECIMALE,
            12,
            "le seuil doit rester au niveau ou en dessous du prefixe de douze "
            "caracteres que le produit forge, sinon il exclut la famille meme "
            "que ce controle existe pour surveiller",
        )

    def test_chaque_ligne_du_manifeste_correspond_au_fichier_declare(self) -> None:
        """L'empreinte DECLAREE doit egaler l'empreinte CONSTATEE.

        Le manifeste est le seul controle d'integrite que l'instance porte
        elle-meme. Rien ne le jouait: il etait une declaration, pas une preuve.
        """
        fautes: list[str] = []
        for racine, ligne in self._lignes():
            relatif = (ligne.get("original_path") or "").replace("\\", "/")
            nomme = "%s/%s" % (racine.name, relatif or "?")
            if not relatif:
                fautes.append("%s: aucun chemin declare" % ligne.get("doc_id"))
                continue
            constatee = empreinte_du_fichier(racine / relatif)
            if constatee.get("absent"):
                fautes.append("%s: %s absent du disque" % (ligne.get("doc_id"), nomme))
                continue
            if constatee.get("sha256") != (ligne.get("sha256") or "").strip():
                fautes.append(
                    "%s: le manifeste declare %s, le fichier vaut %s"
                    % (
                        nomme,
                        (ligne.get("sha256") or "?")[:12],
                        str(constatee.get("sha256"))[:12],
                    )
                )
            declaree = (ligne.get("size_bytes") or "").strip()
            if declaree and declaree != str(constatee.get("octets")):
                fautes.append(
                    "%s: le manifeste declare %s octets, le fichier en fait %s"
                    % (nomme, declaree, constatee.get("octets"))
                )
        self.assertEqual(
            [],
            fautes,
            "le manifeste de l'instance ne decrit plus ses propres pieces:\n  "
            + "\n  ".join(fautes),
        )

    def test_un_identifiant_de_forme_derivee_est_bien_derive(self) -> None:
        """Ce que le nom AFFIRME est verifie sur les octets du fichier.

        Treize modules de test citent des identifiants de cette forme. Si le
        contenu bouge sous l'identifiant, ils continuent de passer en mesurant
        autre chose - le defaut exact que `RM-2026-0107` decrit.
        """
        fautes: list[str] = []
        etiquettes: list[str] = []
        verifies = 0
        for racine, ligne in self._lignes():
            identifiant = (ligne.get("doc_id") or "").strip()
            forme = FORME_IDENTIFIANT_DERIVE.match(identifiant)
            if forme is None:
                etiquettes.append(identifiant)
                continue
            relatif = (ligne.get("original_path") or "").replace("\\", "/")
            nomme = "%s/%s" % (racine.name, relatif or "?")
            constatee = empreinte_du_fichier(racine / relatif)
            if constatee.get("absent"):
                fautes.append("%s: %s absent du disque" % (identifiant, nomme))
                continue
            # Comparaison par PREFIXE et sans casse: la longueur de la tete et
            # sa casse sont des degres de liberte de la regle de forge, pas des
            # valeurs a reconnaitre. Une tete de seize caracteres ou ecrite en
            # minuscules reste donc jugee, au lieu de sortir du controle.
            tete = forme.group(1).lower()
            empreinte = str(constatee["sha256"]).lower()
            verifies += 1
            if not empreinte.startswith(tete):
                fautes.append(
                    "%s designe %s, dont le contenu vaut DOC-%s: l'identifiant "
                    "n'est plus l'empreinte de ce qu'il nomme"
                    % (identifiant, nomme, empreinte[: len(tete)].upper())
                )
        self.assertGreater(
            verifies,
            0,
            "aucun identifiant derive n'a pu etre verifie: le test ne mesure rien",
        )
        self.assertEqual(
            [],
            fautes,
            "un document a change de contenu sans changer de nom (%d etiquettes "
            "non derivees hors portee de ce controle: %s):\n  %s"
            % (len(etiquettes), ", ".join(sorted(etiquettes)) or "aucune", "\n  ".join(fautes)),
        )

    def test_toute_piece_source_est_couverte_par_le_manifeste(self) -> None:
        """Une piece hors manifeste est une piece sans empreinte declaree.

        La portee est derivee de la racine que l'instance DECLARE pour ses
        sources, pas d'une liste de noms de fichiers.
        """
        orphelines: list[str] = []
        vues = 0
        for racine, racine_raw, lignes in self.instances:
            declares = {
                (ligne.get("original_path") or "").replace("\\", "/")
                for ligne in lignes
            }
            for chemin in sorted(racine_raw.rglob("*")):
                if not chemin.is_file():
                    continue
                vues += 1
                relatif = chemin.relative_to(racine).as_posix()
                if relatif not in declares:
                    orphelines.append("%s/%s" % (racine.name, relatif))
        self.assertGreater(
            vues,
            0,
            "aucune piece source sous les racines declarees: le test ne mesure rien",
        )
        self.assertEqual(
            [],
            orphelines,
            "des pieces sources ne sont couvertes par aucune ligne du "
            "manifeste, donc rien ne declare leur empreinte:\n  "
            + "\n  ".join(orphelines),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
