from __future__ import annotations

import unittest

from coproscope.modules.biffageops import _fusionne_par_document


"""Une piece se biffe une fois, pas une fois par chemin ou elle est rangee.

Mesure du 2026-09-07 sur l'instance servie en 8788: la file de biffage comptait
564 lignes pour 559 `doc_id` distincts. Cause: le registre des documents garde
une ligne par CHEMIN, et un meme contenu depose sous deux noms y occupe deux
lignes avec le meme `doc_id` - celui-ci etant l'empreinte du contenu. C'est le
symetrique en aval de `RM-2026-0088`.

Donnees fictives.
"""


class FusionParDocument(unittest.TestCase):
    def test_deux_chemins_un_seul_document(self) -> None:
        docs = [
            {"doc_id": "DOC-AAA", "original_path": r"10_assemblees\pv.pdf", "required_transformations": "redaction"},
            {"doc_id": "DOC-AAA", "original_path": r"90_pieges\pv copie.pdf", "required_transformations": "redaction"},
        ]
        fusionnes, compte = _fusionne_par_document(docs)
        self.assertEqual(len(fusionnes), 1)
        self.assertEqual(compte, 1)

    def test_l_union_des_transformations_ne_sous_protege_jamais(self) -> None:
        """Deux lignes qui se contredisent: on garde les deux exigences.

        Trancher en choisissant une ligne sous-protegerait la piece une fois sur
        deux. L'union ne peut que sur-proteger, ce qui se corrige a la revue.
        """

        docs = [
            {"doc_id": "DOC-BBB", "required_transformations": "redaction"},
            {"doc_id": "DOC-BBB", "required_transformations": "aggregation;human_review"},
        ]
        fusionnes, _ = _fusionne_par_document(docs)
        self.assertEqual(len(fusionnes), 1)
        transformations = set(fusionnes[0]["required_transformations"].split(";"))
        self.assertEqual(transformations, {"redaction", "aggregation", "human_review"})

    def test_l_ordre_du_registre_est_conserve(self) -> None:
        docs = [
            {"doc_id": "DOC-CCC", "required_transformations": "redaction"},
            {"doc_id": "DOC-AAA", "required_transformations": "redaction"},
            {"doc_id": "DOC-CCC", "required_transformations": "redaction"},
            {"doc_id": "DOC-BBB", "required_transformations": "aggregation"},
        ]
        fusionnes, compte = _fusionne_par_document(docs)
        self.assertEqual([row["doc_id"] for row in fusionnes], ["DOC-CCC", "DOC-AAA", "DOC-BBB"])
        self.assertEqual(compte, 1)

    def test_une_ligne_sans_doc_id_est_ecartee(self) -> None:
        docs = [{"doc_id": "", "required_transformations": "redaction"}]
        fusionnes, compte = _fusionne_par_document(docs)
        self.assertEqual(fusionnes, [])
        self.assertEqual(compte, 0)

    def test_sans_doublon_rien_ne_bouge(self) -> None:
        docs = [
            {"doc_id": "DOC-AAA", "required_transformations": "redaction"},
            {"doc_id": "DOC-BBB", "required_transformations": "aggregation"},
        ]
        fusionnes, compte = _fusionne_par_document(docs)
        self.assertEqual(len(fusionnes), 2)
        self.assertEqual(compte, 0)


if __name__ == "__main__":
    unittest.main()
