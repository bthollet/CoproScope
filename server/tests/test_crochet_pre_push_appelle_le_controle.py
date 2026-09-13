# -*- coding: utf-8 -*-
"""Le crochet `pre-push` appelle le controle de confidentialite, et refuse.

**Le defaut que cette garde ferme est nomme par le gouvernail lui-meme**
(`RM-2026-0137`): *« la garde `prefixes_jamais_partager` fonctionne [...] mais
elle gouverne le module de publication, pas `git push` [...] les deux chemins
n'ont rien en commun, et rien ne relie le second a la doctrine »*.

Mesure du 2026-09-10: le crochet EXISTAIT, il etait ACTIF - `core.hooksPath`
pointe sur `.githooks` - et l'outil de controle existait aussi. **Personne
n'avait relie les deux.** Le crochet ne verifiait qu'une chose: que la branche
ne soit pas en retard sur son amont.

**Deux proprietes gardees ici, et la seconde est celle qu'on oublie.**

1. Le crochet **appelle** le verificateur. Sans cela, un `git push` part sans
   qu'aucun controle ne se declenche au moment ou la donnee sort.
2. Il l'appelle **avant toute sortie anticipee**. Le crochet sortait `0` quand
   aucun amont n'est configure - c'est-a-dire **au premier push d'une branche**,
   celui qui publie tout d'un coup, et donc le plus dangereux. Un controle place
   apres cette ligne aurait ete parfaitement inutile la ou il sert le plus.

**Et le troisieme etat compte autant que les deux autres.** Le verificateur rend
`0` rien trouve, `1` quelque chose trouve, `2` **le controle n'a pas pu etre
fait**. Un controle qui n'a pas pu se faire n'est pas un controle qui passe: le
crochet doit refuser dans les deux cas.

**Ce que cette garde ne fait pas:** elle ne lance pas `git push`, et elle ne
verifie pas que `core.hooksPath` est configure sur ce poste - c'est une
configuration locale, pas un fait du depot. Le residu se declare: un poste dont
le `core.hooksPath` ne pointe pas sur `.githooks` n'execute ce crochet pour
aucune raison que ce fichier puisse constater.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


RACINE = Path(__file__).resolve().parents[2]
CROCHET = RACINE / ".githooks" / "pre-push"
OUTIL = RACINE / "tools" / "verifier_avant_push.py"


class LeCrochetEstReliéAuControle(unittest.TestCase):
    """Le lien lui-meme, et sa place dans le fichier."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.source = CROCHET.read_text(encoding="utf-8")

    def test_le_crochet_et_l_outil_existent_tous_les_deux(self) -> None:
        self.assertTrue(CROCHET.is_file(), "le crochet pre-push a disparu")
        self.assertTrue(OUTIL.is_file(), "le verificateur a disparu")

    def test_LE_CROCHET_APPELLE_LE_VERIFICATEUR(self) -> None:
        self.assertIn("tools/verifier_avant_push.py", self.source)

    def test_L_APPEL_PRECEDE_TOUTE_SORTIE_ANTICIPEE(self) -> None:
        """La propriete qu'on oublie, et qui decide de tout.

        Le crochet sort `0` quand aucun amont n'est configure - donc au PREMIER
        push d'une branche, celui qui publie tout d'un coup. Un controle place
        apres cette ligne ne servirait a rien la ou il sert le plus.
        """
        appel = self.source.index("tools/verifier_avant_push.py")
        sorties = [m.start() for m in re.finditer(r"^\s*exit 0\s*$", self.source, re.M)]
        self.assertTrue(sorties, "le crochet ne sort plus jamais: forme inattendue")
        self.assertLess(
            appel, min(sorties),
            "le controle de confidentialite est place APRES une sortie anticipee: "
            "un premier push, sans amont, passerait sans etre controle",
        )

    def test_IL_CONTROLE_CE_QUE_LE_PUSH_ENVOIE_ET_PAS_SEULEMENT_L_ARBRE(self) -> None:
        """**La propriete que ce fichier ne gardait pas: l'OBJET du controle.**

        Cette garde verifiait que le crochet APPELLE le verificateur, jamais
        sur quoi. L'appel portait sur `git ls-files`, donc l'arbre courant -
        alors qu'un push publie des commits. Deux consequences mesurees le
        2026-09-12, sur un depot PUBLIC:

        - `git push origin main` depuis une autre branche passait: l'arbre
          courant etait propre, `main` portait 41 constats;
        - un nom efface dans un commit reste lisible dans le precedent, et un
          push publie les deux: 0 constat sur l'arbre, 44 sur ce que le push
          de la branche aurait envoye.

        C'est la meme faute que celle d'en haut, d'un cran plus haut: on avait
        relie le crochet a l'outil sans relier l'outil a ce qui part.
        """
        self.assertIn(
            "--pousse", self.source,
            "le crochet ne controle que l'arbre suivi: un push d'une autre "
            "reference, ou d'un commit dont l'arbre a ete nettoye depuis, "
            "partirait sans que rien de ce qu'il publie ne soit regarde")
        self.assertIn(
            '--pousse "$remote_name"', self.source,
            "le crochet ne dit pas au controle vers QUEL distant le push va: "
            "sans cela, ce qui est deja publie ne peut pas etre exclu")

    def test_LE_CONTROLE_DU_PUSH_N_EST_PAS_PRIVE_DE_SON_ENTREE(self) -> None:
        """`git push` annonce les references sur stdin, et rien d'autre ne le dit.

        Un controle prive de cette entree ne lit aucune reference, rend `2` -
        *pas regarde* - et refuserait donc TOUS les pushes. Un garde qui refuse
        toujours se contourne par `--no-verify` des le deuxieme jour, et on se
        retrouve avec un garde-fou nominal. La redirection est donc une faute,
        pas un detail de style.
        """
        lignes = [l for l in self.source.splitlines() if "--pousse" in l]
        self.assertTrue(lignes, "aucun appel `--pousse` dans le crochet")
        for ligne in lignes:
            self.assertNotIn(
                "<", ligne,
                "l'appel `--pousse` est prive de son entree standard: il ne "
                "lira aucune reference et refusera tout: %s" % ligne.strip())

    def test_LES_DEUX_ETATS_D_ECHEC_REFUSENT_LE_PUSH(self) -> None:
        """`1` a trouve quelque chose, `2` n'a pas pu chercher. Aucun ne passe."""
        self.assertIn('"$code" = "2"', self.source)
        self.assertIn("n'a PAS PU etre fait", self.source)
        self.assertIn("rien n'est pousse", self.source)

    def test_le_contournement_est_NOMME_au_lieu_d_etre_devine(self) -> None:
        """Un refus sans issue ecrite se contourne quand meme, et en silence."""
        self.assertIn("--no-verify", self.source)

    def test_le_crochet_ne_recopie_jamais_un_terme_cherche(self) -> None:
        """Le crochet imprime des chemins et des codes, jamais une valeur.

        Ecrire le terme cherche dans un message serait la premiere fuite - et
        c'est l'outil, pas le crochet, qui connait ces termes.
        """
        self.assertNotIn("noms_interdits.txt", self.source.replace(
            "COPROSCOPE_NOMS_INTERDITS", ""))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
