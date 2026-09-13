# -*- coding: utf-8 -*-
"""Une instance d'exemple qu'on peut mesurer sans mettre la reference a portee.

`RM-2026-0107`. Le defaut vise n'est pas qu'un test SALISSE l'instance
versionnee: c'est qu'il la mette **a portee d'ecriture** pendant qu'on mesure
contre elle. Un test peut etre en lecture seule aujourd'hui et appeler demain
une fonction de production qui ecrit - et alors la reference devient
silencieusement la sortie du dernier passage. Le fait observe le 2026-09-07:
trois fichiers suivis de `examples/synthetic_copro` trouves modifies, sans que
personne reproduise la mutation.

**Pourquoi une COPIE conserve le sens de la mesure, et c'est la question que
le residu posait.** Les trois tests concernes mesurent le nom d'affichage de la
copropriete, ses ecrans, et le fait qu'aucune piece n'est inventee quand il n'y
a rien. Aucune de ces proprietes ne depend du CHEMIN: elles dependent du
CONTENU, que `copytree` reproduit a l'octet. Ce qui changerait de sens serait
une mesure portant sur l'emplacement lui-meme - aucune des trois n'en fait.

**Ce que cette copie n'est pas.** Ce n'est pas une instance de lot au sens de
la doctrine - pas de nom en `lot_`, pas de trace dans le contrat d'agent:
c'est un dossier temporaire, detruit a la sortie du contexte, et qui ne survit
pas au test. La regle de l'instance jetable porte sur les lots de dev et de
mesure; ici il s'agit d'isoler une reference pendant une seconde.

**La limite se declare, comme partout ailleurs:** l'exemple synthetique reste
un exemple. Une epreuve menee dessus prouve que la chaine tourne et vaut pour
la non-regression, jamais pour la justesse - ses pieces ont ete ecrites pour
passer.
"""
from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from coproscope.core.common import load_instance

#: La reference versionnee. Elle n'est JAMAIS ouverte par ce module: elle est
#: lue par `copytree`, qui ne fait que copier.
EXEMPLE_VERSIONNE = (
    Path(__file__).resolve().parents[2] / "examples" / "synthetic_copro"
)


@contextmanager
def exemple_copie(nom: str = "exemple") -> Iterator[object]:
    """Une instance chargee depuis une COPIE fraiche de l'exemple.

    Rend l'objet instance, comme `load_instance`. Le dossier est detruit a la
    sortie, donc aucune trace ne survit au test - ce qui est la difference avec
    une instance de lot, qu'on nomme et qu'on jette explicitement.
    """
    with TemporaryDirectory(prefix="coproscope_%s_" % nom) as dossier:
        racine = Path(dossier) / "synthetic_copro"
        shutil.copytree(EXEMPLE_VERSIONNE, racine)
        yield load_instance(None, str(racine))


@contextmanager
def racine_copiee(nom: str = "exemple") -> Iterator[Path]:
    """La meme copie, rendue comme un CHEMIN.

    Pour les appelants qui construisent eux-memes leur instance, ou qui ont
    besoin du dossier avant de charger.
    """
    with TemporaryDirectory(prefix="coproscope_%s_" % nom) as dossier:
        racine = Path(dossier) / "synthetic_copro"
        shutil.copytree(EXEMPLE_VERSIONNE, racine)
        yield racine
