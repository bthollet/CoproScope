"""Etat des seuils de l'article 21 a une date donnee.

Extrait de `_resolutions_registre` le 2026-09-08: ce fichier depassait la limite
de 600 lignes du depot des que l'axe de cloture y a ajoute son diagnostic. La
coupure n'est pas arbitraire - lire un registre et dater un seuil sont deux
questions differentes, et cette seconde n'a besoin que des lignes deja ecrites.
"""

from __future__ import annotations

SEUILS_SUIVIS = ("SEUIL_CONSULTATION_CS", "SEUIL_MISE_EN_CONCURRENCE")


def seuils_en_vigueur(lignes: list[dict[str, str]], date: str) -> list[dict[str, object]]:
    """Etat de chaque seuil de l'article 21 a une date donnee.

    L'article 21 confie a l'assemblee le soin d'arreter les montants au-dela
    desquels la consultation du conseil syndical et la mise en concurrence
    deviennent obligatoires. Ces montants ont un terme. Un seuil expire et non
    renouve n'est pas un detail d'archive: il n'y a alors plus de montant
    arrete.

    Le controle est purement calendaire - il ne demande que les dates et les
    durees - donc il fonctionne des la premiere assemblee lue.

    Constat mesure le 2026-09-03 sur le corpus Tilleuls (pseudo): le seuil de
    consultation du conseil syndical, vote le 03/07/2024 pour 24 mois, expire le
    03/07/2026. Trois assemblees se sont tenues entre les deux dates, dont une
    seize jours avant l'expiration, et aucune ne l'a revote - alors que cette
    derniere a bien renouvele le seuil de mise en concurrence.

    **Nuance ajoutee le meme jour, apres correction d'un defaut d'extraction.**
    Une resolution de 2022 fixant ce meme seuil a 500 EUR etait lue SANS_OBJET
    a cause d'un decalage d'une resolution; retablie en ADOPTEE, elle n'enonce
    aucun terme. Passe le 03/07/2026 la fonction la rend donc "en vigueur", ce
    qui revient a decider qu'un seuil ancien reprend la main quand un seuil plus
    recent expire. Cette question est juridique, pas calendaire: le drapeau
    `reprise_seuil_anterieur` la signale au lieu de la trancher, et `expire_le`
    donne alors la date du seuil qui, lui, a bien expire.

    **Portee elargie, signalee le 2026-09-03 par la conversation factures.** La
    question ne commence pas a l'expiration: elle commence au second vote. Du
    04/07/2024 au 03/07/2026, deux seuils adoptes sont actifs ensemble sur ce
    corpus - 500 EUR sans terme et 1 000 EUR pour 24 mois. Rendre le plus recent
    est un usage raisonnable, mais c'est un choix, et il portait en silence sur
    deux exercices entiers. Si le seuil de 2022 n'a jamais cesse, le montant
    applicable sur cette periode serait 500 EUR, donc plus strict que suppose.
    `seuils_concurrents` rend les autres seuils actifs pour que ce choix soit
    visible avant qu'un calcul s'appuie dessus.

    Ce module CONSTATE l'expiration. Il n'en tire aucune conclusion de droit:
    dire ce qu'emporte l'absence de montant arrete n'est pas son office.
    """
    etats: list[dict[str, object]] = []
    for seuil in SEUILS_SUIVIS:
        portant = [
            ligne
            for ligne in lignes
            if seuil in (ligne.get("qualifications") or "")
            and ligne.get("resultat") == "ADOPTEE"
            and ligne.get("valide_du")
        ]
        portant.sort(key=lambda ligne: ligne.get("valide_du", ""))
        actif = [
            ligne
            for ligne in portant
            if ligne.get("valide_du", "") <= date
            and (not ligne.get("valide_au") or date <= ligne["valide_au"])
        ]
        dernier = portant[-1] if portant else None
        expire = [
            ligne for ligne in portant
            if ligne.get("valide_au") and ligne["valide_au"] < date
        ]
        # Un seuil ancien peut rester "actif" par la seule absence de terme,
        # alors qu'un seuil plus recent a expire. Dire qu'il reprend la main
        # serait une conclusion de droit; on se contente de le signaler.
        reprise = bool(
            actif
            and expire
            and expire[-1].get("valide_du", "") > actif[-1].get("valide_du", "")
        )
        # Deux seuils adoptes peuvent etre actifs a la meme date: un ancien sans
        # terme et un recent avec terme. Prendre le plus recent est un usage
        # raisonnable, pas une regle de droit - donc on rend aussi les autres.
        concurrents = [
            {
                "montant": ligne.get("montant_seuil", ""),
                "valide_du": ligne.get("valide_du", ""),
                "valide_au": ligne.get("valide_au", ""),
            }
            for ligne in actif[:-1]
        ]
        etats.append(
            {
                "seuil": seuil,
                "en_vigueur": bool(actif),
                "montant": actif[-1].get("montant_seuil", "") if actif else "",
                "valide_au": actif[-1].get("valide_au", "") if actif else "",
                "dernier_vote": dernier.get("valide_du", "") if dernier else "",
                "expire_sans_renouvellement": bool(expire) and not actif,
                "expire_le": (
                    expire[-1].get("valide_au", "") if expire and (not actif or reprise) else ""
                ),
                # Le montant rendu vient d'une resolution ANTERIEURE a un seuil
                # expire: l'appelant doit poser la question au lieu de conclure.
                "reprise_seuil_anterieur": reprise,
                # Les autres seuils adoptes encore actifs a cette date. Non vide
                # = le montant rendu resulte d'un choix, pas d'un calcul.
                "seuils_concurrents": concurrents,
                # Sans terme enonce, on ne sait pas: ce n'est ni en vigueur ni
                # expire, et ce doute se remonte au lieu d'etre tranche.
                "sans_terme": bool(portant) and not any(l.get("valide_au") for l in portant),
            }
        )
    return etats
