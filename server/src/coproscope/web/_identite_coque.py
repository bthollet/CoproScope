"""L'identite que la coque affiche: celle de l'instance, jamais une constante.

**Le defaut que ce module ferme.** Treize ecrans construisaient leur bloc
`model["instance"]` a la main, et dix le faisaient sans condition:

    "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", ...}

Mesure du 2026-09-05 sur `examples/synthetic_copro`, dont le `display_name` est
`Residence Les Platanes`: `/controle-gouvernance` rendait « Residence Les
Platanes » et `/comptes/rapprochement` rendait « Copropriete FICTIVE ». Deux
pages de la meme session, la meme instance, deux coproprietes a l'ecran.

Ce n'est pas un defaut d'affichage. Un coproprietaire qui ouvre le controle des
comptes de SA copropriete et lit le nom d'une autre ne sait plus de qui sont les
chiffres qu'il regarde - et l'ecran ne lui donne aucun moyen de trancher. Les
donnees, elles, etaient correctes: les lignes de repli sont bien gardees par
`instance is None`. C'est l'identite seule qui etait inventee, ce qui la rend
d'autant plus credible.

**L'axe, et pas la liste.** Le correctif n'est pas dix retouches. La question
generale est: ou un ecran lit-il l'identite de la copropriete qu'il affiche. La
reponse est ici, une fois. Un quatorzieme ecran ecrit demain appellera cette
fonction ou reproduira le defaut, et la difference se voit a la revue.

Le nom fictif reste la valeur de repli quand aucune instance n'est chargee -
c'est alors la verite: aucune copropriete n'est ouverte, et le dire vaut mieux
que d'afficher un nom vide.
"""

from __future__ import annotations

from typing import Any

#: Ce que la coque affiche quand aucune instance n'est chargee. Le mot
#: `FICTIVE` est garde a dessein: il se lit a l'ecran et il est vrai.
SANS_INSTANCE = {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": ""}


def identite_coque(instance: Any | None, year: int) -> dict[str, Any]:
    """Le bloc `instance` du modele de coque, lu sur l'instance ouverte.

    Tolerante par conception: plusieurs vues recoivent `instance` sous des
    formes differentes - `InstanceConfig`, dictionnaire, ou `None` - et une
    identite manquante ne doit jamais lever au milieu du rendu d'une page. Un
    nom absent retombe sur le nom de repli, qui dit la verite.
    """
    if instance is None:
        return {**SANS_INSTANCE, "year": year}

    def lire(nom: str) -> str:
        valeur = getattr(instance, nom, None)
        if valeur is None and isinstance(instance, dict):
            valeur = instance.get(nom)
        return str(valeur) if valeur else ""

    nom = lire("display_name")
    if not nom:
        return {**SANS_INSTANCE, "year": year}

    return {
        "id": lire("instance_id") or SANS_INSTANCE["id"],
        "name": nom,
        # **`root` reste vide, toujours.** La premiere version y mettait le
        # chemin absolu de l'instance, et le garde-fou de confidentialite
        # `test_ui_comptes_rapprochement` l'a refuse le 2026-09-05 en trouvant
        # `C:\` dans le modele rendu. Il avait raison: un chemin local n'a rien
        # a faire dans une page destinee a des coproprietaires, et il fuit le
        # nom du poste et de l'utilisateur. La cle est gardee pour la forme du
        # modele; sa valeur ne doit pas revenir.
        "root": "",
        "year": year,
    }
