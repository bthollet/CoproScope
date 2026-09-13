"""`RM-2026-0052` defaut (1): ce que le titre seul ne peut pas separer.

**Le defaut, tel que la recette live du 2026-09-03 l'a nomme** (trace
`CONV-2026-2101`): sur 15 documents classes `PV_AG`, onze etaient des fichiers
de travail produits par CoproScope lui-meme. La trace les nomme un par un -
`matrice_risques.csv`, `journal_decisions.md`, `signaux_alertes_*.csv`,
`synthese_sequence_*.md` - et la chaine absorbe ces extensions:
`TEXT_EXTENSIONS = {"txt", "md", "csv", "tsv", "json"}`.

**Ce que la signature de titre a repare, et c'est reel.** Une locution
GOUVERNEE par de la prose sur la meme ligne - `approbation du proces-verbal de
l assemblee`, `source=proces-verbal de l assemblee` - n'est plus lue comme un
titre. Mesure du 2026-09-09 sur les deux cabinets: 15 fichiers de texte
d'instance portent la locution en tete, les 15 sont de vrais proces-verbaux et
les 15 restent reconnus. Aucun faux negatif introduit.

**Ce qu'elle ne peut pas reparer, et pourquoi ce fichier existe.** La maniere
dont un document en CITE un autre est un degre de liberte: prose, cellule de
tableau, puce de liste, titre de niveau deux, `cle=valeur`. La regle
`un titre ouvre son enonce` couvre la prose et rien d'autre, parce qu'une
cellule, une puce et un titre markdown OUVRENT leur ligne exactement comme un
vrai titre. Sur la forme seule, un `## Proces-verbal ...` en tete d'une
synthese et un `PROCES-VERBAL ...` en tete d'un vrai PV sont indiscernables.

**Mesure du 2026-09-09, chaine `classify` complete, avant et apres le lot**
(`913d744` puis `ecacf12`): les quatre formes nommees par la trace sortent
`PV_AG` / `AUTO_CLASSIFIED`, notes VIDES, **a l'identique des deux cotes**.
Le verdict bascule sur la seule position de la colonne: la meme matrice de
risques est douteuse quand la description est en colonne 3, et affirmee
`PV_AG` quand elle est en colonne 1. Personne ne choisit un ordre de colonnes
pour dire de quel type est son fichier.

**LA DECISION QUI RESTE, et elle n'est pas technique.** Separer ces pieces
demande la PROVENANCE - *ce que CoproScope produit lui-meme ne doit jamais
etre classe comme piece emise par le syndic* - qui est le mandat de
`RM-2026-0056`, toujours `ACTIF`. Le gouvernail avait deja etabli que la cause
est structurelle (verdict `CONV-2026-2123`: 0 rattrape sur 11). Ce fichier ne
tranche pas cette decision: il BORNE le residu et le rend visible, pour qu'un
`RM-2026-0052` defaut (1) ne puisse pas etre declare clos tant que le compte
ci-dessous n'a pas bouge.

**Ce que ce fichier ne prouve pas.** Les quatre formes sont reconstruites
d'apres les noms de la trace: l'instance qui portait les onze fichiers
n'existe plus sur le poste. Elles valent pour le MECANISME, elles ne mesurent
pas un taux sur le corpus d'origine.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import (
    DEFAULT_DOCUMENT_FIELDS,
    RunContext,
    load_instance,
    read_csv,
    write_csv,
)
from coproscope.modules.docuscope import classify

INSTANCE_EXEMPLE = Path(__file__).resolve().parents[2] / "examples" / "synthetic_copro"

#: Assez de matiere pour passer le plancher d'extraction, sans un mot qui
#: nomme un type: ce qui decide ici doit etre la locution, et elle seule.
REMPLISSAGE = "suivi interne du conseil syndical, renvoi aux pieces du coffre. " * 60

LOCUTION = "proces-verbal de l assemblee generale"

#: Les quatre noms que la trace du 2026-09-03 cite, chacun dans la mise en
#: forme naturelle de son format. La locution y CITE une autre piece: aucun de
#: ces fichiers n'est un proces-verbal.
FICHIERS_DE_TRAVAIL: dict[str, str] = {
    "matrice_risques.csv": "risque,gravite,lot\n" + LOCUTION + " non depose,eleve,AG\n",
    "journal_decisions.md": "# Journal des decisions\n\n## " + LOCUTION + " du 3 juillet\n\n",
    "signaux_alertes_2026.csv": "signal\n" + LOCUTION + " absent du coffre\n",
    "synthese_sequence_absorption.md": (
        "# Synthese de sequence\n\nPieces examinees :\n\n- " + LOCUTION + " du 3 juillet\n"
    ),
}

#: Combien de ces formes la chaine affirme encore `PV_AG` SANS le moindre
#: doute. Mesure du 2026-09-09 sur `ecacf12`: quatre sur quatre, notes vides -
#: le meme compte qu'avant le lot, sur `913d744`.
RESIDU_MESURE = 4

#: **`notes` vides etait un PROXY, et il a ete satisfait sans rien reparer.**
#: Le 2026-09-12, `RM-2026-0080` a fait declarer l'absence de date lisible; les
#: quatre fichiers de travail ont donc recu une note, et le critere
#: `notes vides` les a sortis des `affirmes` - alors qu'ils sortent toujours
#: `PV_AG` / `AUTO_CLASSIFIED` et que **rien du defaut n'a bouge**.
#:
#: Le critere dit desormais ce qu'il veut dire: **un doute porte sur le TYPE**,
#: pas sur n'importe quel sujet. Les notes que le classement ecrit au sujet du
#: type nomment toutes l'une de ces trois choses - le type retenu, le titre lu
#: en tete, ou l'absence de texte utile sur laquelle le type reposerait. Une
#: note de DATE n'en nomme aucune, et c'est ce que le temoin ci-dessous
#: verifie.
SUJETS_DE_DOUTE_SUR_LE_TYPE = ("type", "titre", "texte utile")


def _doute_sur_le_TYPE(notes: str) -> bool:
    """Une note jette-t-elle un doute sur le TYPE de la piece ?"""
    lues = (notes or "").lower()
    return any(sujet in lues for sujet in SUJETS_DE_DOUTE_SUR_LE_TYPE)


class FichiersDeTravailClassesProcesVerbalTests(unittest.TestCase):
    """Le residu de `RM-2026-0052` defaut (1), borne et rendu visible."""

    def setUp(self) -> None:
        self.dossier = tempfile.TemporaryDirectory()
        self.racine = Path(self.dossier.name) / "instance"
        shutil.copytree(INSTANCE_EXEMPLE, self.racine)
        self.instance = load_instance(str(self.racine / "instance.yml"), None)

    def tearDown(self) -> None:
        self.dossier.cleanup()

    def _classer(self) -> dict[str, dict[str, str]]:
        dossier_texte = self.racine / "staging" / "text"
        dossier_texte.mkdir(parents=True, exist_ok=True)
        lignes = []
        for rang, (nom, tete) in enumerate(FICHIERS_DE_TRAVAIL.items()):
            doc_id = "DOC-TRAVAIL-" + str(rang)
            ligne = {champ: "" for champ in DEFAULT_DOCUMENT_FIELDS}
            ligne.update(
                {
                    "doc_id": doc_id,
                    "instance_id": self.instance.instance_id,
                    "file_name": nom,
                    "original_path": "raw/" + nom,
                    "text_path": "staging/text/" + doc_id + ".txt",
                }
            )
            (dossier_texte / (doc_id + ".txt")).write_text(
                tete + REMPLISSAGE, encoding="utf-8"
            )
            lignes.append(ligne)
        write_csv(
            self.instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), lignes
        )
        classify(
            self.instance, RunContext(self.instance, "residu-0052"), copy_files=False
        )
        _, sorties = read_csv(self.instance.register("documents"))
        return {
            ligne["file_name"]: ligne
            for ligne in sorties
            if ligne["doc_id"].startswith("DOC-TRAVAIL-")
        }

    def test_le_residu_est_borne_et_ne_grandit_pas(self) -> None:
        lignes = self._classer()
        self.assertEqual(
            len(lignes),
            len(FICHIERS_DE_TRAVAIL),
            "toutes les formes n'ont pas ete classees",
        )
        affirmes = sorted(
            nom
            for nom, ligne in lignes.items()
            if ligne["document_type"] == "PV_AG"
            and ligne["classification_status"] == "AUTO_CLASSIFIED"
            and not _doute_sur_le_TYPE(ligne["notes"])
        )
        self.assertLessEqual(
            len(affirmes),
            RESIDU_MESURE,
            "REGRESSION: une forme de fichier de travail de plus est affirmee"
            " proces-verbal sans aucun doute - " + repr(affirmes),
        )
        self.assertGreaterEqual(
            len(affirmes),
            RESIDU_MESURE,
            "Le residu de RM-2026-0052 defaut (1) a DIMINUE, et c'est une bonne"
            " nouvelle: seules " + repr(affirmes) + " restent affirmees."
            " Abaisser RESIDU_MESURE, et dire dans le gouvernail ce qui a"
            " repare le reste - la piste nommee est le filtre de PROVENANCE de"
            " RM-2026-0056.",
        )

    def test_une_note_de_DATE_n_est_PAS_un_doute_sur_le_type(self) -> None:
        """Le temoin qui protege le critere contre le proxy d'hier.

        La phrase exacte produite par `core.date_du_document` quand aucune date
        n'est lisible ne doit pas compter pour un doute sur le type: elle ne
        dit rien du type, et la prendre pour un doute ferait disparaitre le
        residu de cet item sans que rien ne soit repare.
        """
        de_la_date = (
            "Aucune date lisible dans le document, dans son nom ni dans son "
            "dossier de rangement. La date reste a etablir a la main: une "
            "cellule vide sans cette phrase se lirait comme une date non "
            "cherchee."
        )
        self.assertFalse(_doute_sur_le_TYPE(de_la_date))

    def test_une_note_de_CONFLIT_de_denomination_EST_un_doute(self) -> None:
        """Temoin symetrique: sans lui, le critere pourrait ne jamais mordre."""
        self.assertTrue(_doute_sur_le_TYPE(
            "Titre PV_AG lu en tete, mais le nom du fichier designe CR_CS:"
            " denominations en conflit, CR_CS conserve sans preuve qui tranche."
        ))
        self.assertTrue(_doute_sur_le_TYPE(
            "Aucun texte utile extrait: le type ne repose sur aucune lecture"
            " du contenu."
        ))

    def test_une_locution_gouvernee_par_de_la_prose_reste_bien_un_doute(self) -> None:
        """Contrepartie: ce que le lot du 2026-09-09 a reellement repare.

        Sans elle, ce fichier ne dirait que ce qui manque, et un futur lecteur
        pourrait croire que la signature de titre n'a rien apporte.
        """
        from coproscope.modules.docuscope import (
            DEFAULT_TITLE_HEAD_CHARS,
            DEFAULT_TITLE_SIGNATURES,
            DEFAULT_USEFUL_TEXT_FLOOR,
            title_signature_verdict,
        )

        gouvernee = "cette note reprend le " + LOCUTION + " du 3 juillet. " + REMPLISSAGE
        self.assertEqual(
            title_signature_verdict(
                gouvernee,
                DEFAULT_TITLE_SIGNATURES["PV_AG"],
                DEFAULT_TITLE_HEAD_CHARS,
                DEFAULT_USEFUL_TEXT_FLOOR,
            ),
            "A_RECLASSER",
        )


if __name__ == "__main__":
    unittest.main()
