# -*- coding: utf-8 -*-
"""Les pieces d'une copropriete ENTIEREMENT INVENTEE, telles qu'un syndic les transmet.

Aucune personne, aucune adresse, aucun cabinet reel: des noms d'exemple. Les
montants et les dates sont choisis pour que les pieces se REPONDENT d'un ecran a
l'autre - la resolution de travaux cite le devis, l'ordre de service cite la
resolution, la facture cite l'ordre de service, et la lettre du conseil syndical
reclame le PV de reception qui manque au dossier.

Ce corpus est ecrit pour que la chaine le lise. Il prouve qu'elle tourne et sert
de vitrine; il ne prouve rien sur sa justesse.
"""
from __future__ import annotations

COPRO = "Residence Les Glycines (fictive)"
SYNDIC = "Cabinet Exemple Gestion (fictif)"
ADRESSE = "12 rue de l'Exemple, Ville-Exemple"
ENTREPRISE = "Facades Exemple SARL (fictive)"
ASCENSORISTE = "Ascenseurs Exemple (fictif)"

ENTETE = COPRO + "\n" + ADRESSE + "\nSyndic : " + SYNDIC + "\n\n"
MENTION = "\n\nDocument fictif, cree pour la demonstration de CoproScope."


def _fait(date_longue: str) -> str:
    """La date d'emission, en tete: c'est la que la chaine la cherche d'abord."""
    return "Ville-Exemple, le " + date_longue + "\n\n"


def _pv(date_longue: str, resolutions: str) -> str:
    return (
        "PROCES-VERBAL DE L'ASSEMBLEE GENERALE ORDINAIRE DU " + date_longue.upper() + "\n" + ENTETE
        + "Le " + date_longue + " a 18 heures, les coproprietaires de la " + COPRO
        + " se sont reunis en assemblee generale ordinaire sur convocation du syndic.\n"
        "Il a ete etabli une feuille de presence. Presents ou representes : 7 546 / 10 000 tantiemes.\n\n"
        + resolutions + MENTION
    )


def _vote(pour: str, contre: str, abstention: str) -> str:
    return "Ont vote pour : %s / 10 000 tantiemes. Ont vote contre : %s. Se sont abstenus : %s.\n" % (pour, contre, abstention)


ADOPTEE = "En consequence, cette resolution est adoptee.\n\n"
REJETEE = "En consequence, cette resolution est rejetee.\n\n"

RESOLUTIONS_2025 = (
    "Resolution n°1 : Election du president de seance\nMajorite de l'article 24.\n"
    + _vote("7 546", "0", "0") + ADOPTEE
    + "Resolution n°2 : Approbation des comptes de l'exercice 2024\nMajorite de l'article 24.\n"
    + _vote("6 912", "412", "222") + ADOPTEE
    + "Resolution n°3 : Budget previsionnel de l'exercice 2026 pour un montant de 48 000 euros\nMajorite de l'article 24.\n"
    + _vote("7 120", "426", "0") + ADOPTEE
    + "Resolution n°4 : Travaux de ravalement des facades selon le devis D-2025-041 de Facades Exemple SARL (fictive) pour 84 000 euros TTC\n"
    "Majorite de l'article 25.\n"
    + _vote("5 830", "1 204", "512") + ADOPTEE
    # Majorite NON ENONCEE, a dessein: le controle doit la signaler.
    + "Resolution n°5 : Renouvellement du contrat d'entretien de l'ascenseur avec Ascenseurs Exemple (fictif) pour 2 880 euros par an\n"
    + _vote("6 480", "1 066", "0") + ADOPTEE
    # Issue NON ENONCEE, a dessein: des voix comptees, aucune formule d'adoption.
    + "Resolution n°6 : Montant des marches a partir duquel la consultation du conseil syndical est obligatoire, fixe a 1 500 euros\n"
    "Majorite de l'article 25.\n"
    + _vote("7 010", "536", "0") + "\n"
    + "Resolution n°7 : Pose de compteurs d'eau individuels\nMajorite de l'article 24.\n"
    + _vote("2 910", "4 636", "0") + REJETEE
)

RESOLUTIONS_2024 = (
    "Resolution n°1 : Election du president de seance\nMajorite de l'article 24.\n"
    + _vote("7 204", "0", "0") + ADOPTEE
    + "Resolution n°2 : Approbation des comptes de l'exercice 2023\nMajorite de l'article 24.\n"
    + _vote("6 700", "504", "0") + ADOPTEE
    + "Resolution n°3 : Mandat donne au syndic de faire etablir des devis pour le ravalement des facades\nMajorite de l'article 24.\n"
    + _vote("6 950", "254", "0") + ADOPTEE
)

CONVOCATION_2025 = (
    "CONVOCATION A L'ASSEMBLEE GENERALE ORDINAIRE\n" + ENTETE + _fait("15 mai 2025")
    + "Vous etes convoque a l'assemblee generale ordinaire qui se tiendra le 12 juin 2025 a 18 heures, salle commune de la residence.\n\n"
    "ORDRE DU JOUR\n"
    "1- Election du president de seance (article 24)\n"
    "2- Approbation des comptes de l'exercice 2024 (article 24)\n"
    "3- Budget previsionnel de l'exercice 2026 (article 24)\n"
    "4- Travaux de ravalement des facades, devis joint D-2025-041 pour 84 000 euros TTC (article 25)\n"
    "5- Renouvellement du contrat d'entretien de l'ascenseur (article 24)\n"
    "6- Montant de consultation obligatoire du conseil syndical (article 25)\n"
    "7- Pose de compteurs d'eau individuels (article 24)\n\n"
    "Pieces jointes : comptes de l'exercice 2024, budget previsionnel 2026, devis de ravalement." + MENTION
)

#: (nom de fichier, texte). Le nom porte la date et la nature, comme un syndic
#: nomme ses envois - et c'est un indice que la chaine a le droit de lire.
PIECES: list[tuple[str, str]] = [
    ("2024-06-20_proces_verbal_ag_2024.pdf", _pv("20 juin 2024", RESOLUTIONS_2024)),
    ("2025-05-15_convocation_ag_2025.pdf", CONVOCATION_2025),
    ("2025-06-12_proces_verbal_ag_2025.pdf", _pv("12 juin 2025", RESOLUTIONS_2025)),
    ("2025-04-02_devis_ravalement_facades.pdf",
     "DEVIS N° D-2025-041\n" + ENTREPRISE + "\nZone d'activite Exemple, Ville-Exemple\n" + _fait("2 avril 2025")
     + "Client : syndicat des coproprietaires de la " + COPRO + ", represente par " + SYNDIC + "\n"
     "Objet : ravalement des facades sur rue et sur cour\n\n"
     "Echafaudage et protections : 18 500,00 euros HT\n"
     "Nettoyage et reprise des fissures : 21 300,00 euros HT\n"
     "Peinture deux couches : 30 200,00 euros HT\n\n"
     "Total HT : 70 000,00 euros\nTVA 20 % : 14 000,00 euros\nTotal TTC : 84 000,00 euros\n\n"
     "Validite : trois mois. Bon pour accord." + MENTION),
    ("2025-07-10_ordre_de_service_ravalement.pdf",
     "ORDRE DE SERVICE\n" + ENTETE + _fait("10 juillet 2025") + "Destinataire : " + ENTREPRISE + "\n\n"
     "En execution de la resolution n°4 votee le 12 juin 2025, le syndic donne ordre de demarrage des travaux "
     "de ravalement conformement au devis D-2025-041, pour un montant de 84 000 euros TTC.\n"
     "Demarrage des travaux : 1er septembre 2025. Duree previsionnelle : dix semaines." + MENTION),
    ("2025-09-15_facture_acompte_ravalement.pdf",
     "FACTURE N° F-2025-0915\n" + ENTREPRISE + "\n" + _fait("15 septembre 2025")
     + "Client : syndicat des coproprietaires de la " + COPRO + "\n"
     "Objet : acompte de 30 % sur les travaux de ravalement, devis D-2025-041, ordre de service du 10 juillet 2025\n\n"
     "Montant HT : 21 000,00 euros\nTVA 20 % : 4 200,00 euros\nTotal TTC : 25 200,00 euros\nNet a payer : 25 200,00 euros" + MENTION),
    ("2025-01-01_contrat_entretien_ascenseur.pdf",
     "CONTRAT D'ENTRETIEN D'ASCENSEUR\n" + ENTETE + _fait("1er janvier 2025") + "Prestataire : " + ASCENSORISTE + "\n\n"
     "Contrat de maintenance d'un ascenseur de 630 kg : visites mensuelles, depannage 24 heures sur 24.\n"
     "Duree : un an renouvelable. Redevance annuelle : 2 880,00 euros TTC." + MENTION),
    ("2025-02-03_declaration_sinistre_degat_des_eaux.pdf",
     "DECLARATION DE SINISTRE\n" + ENTETE + _fait("3 fevrier 2025")
     + "Nature : degat des eaux constate le 1er fevrier 2025 dans la cage d'escalier B, infiltration depuis la toiture-terrasse.\n"
     "Declaration de sinistre adressee a l'assureur multirisque immeuble le 3 fevrier 2025.\n"
     "Mesure conservatoire : bache posee le 2 fevrier 2025. Expertise a programmer." + MENTION),
    ("2025-10-01_courrier_demande_pieces_au_syndic.pdf",
     "LETTRE DU CONSEIL SYNDICAL AU SYNDIC\nConseil syndical de la " + COPRO + "\n" + _fait("1er octobre 2025")
     + "Destinataire : " + SYNDIC + "\n\n"
     "Objet : demande de communication de pieces\n\n"
     "Nous vous demandons de nous communiquer, pour les travaux de ravalement des facades en cours :\n"
     "- le PV de reception des travaux, s'il a ete signe ;\n"
     "- l'attestation d'assurance dommages-ouvrage souscrite pour ces travaux ;\n"
     "- le rapport d'expertise du degat des eaux du 1er fevrier 2025.\n"
     "Nous vous remercions de votre reponse sous quinze jours." + MENTION),
    ("2025-03-31_annexe_comptable_etat_financier_2024.pdf",
     "ANNEXE COMPTABLE N°1 - ETAT FINANCIER APRES REPARTITION DE L'EXERCICE 2024\n" + ENTETE + _fait("31 mars 2025")
     + "Exercice du 1er janvier 2024 au 31 decembre 2024\n\n"
     "Charges et produits de l'exercice\n"
     "Total des charges pour operations courantes : 46 210,00 euros\n"
     "Total des produits pour operations courantes : 46 210,00 euros\n"
     "Fonds travaux : 7 400,00 euros\n"
     "Tresorerie au 31 decembre 2024 : 18 930,00 euros" + MENTION),
    ("2025-01-10_attestation_assurance_multirisque.pdf",
     "ATTESTATION D'ASSURANCE\n" + ENTETE + _fait("10 janvier 2025")
     + "L'assureur Exemple Assurances (fictif) atteste que le syndicat des coproprietaires de la " + COPRO
     + " est titulaire d'un contrat d'assurance multirisque immeuble du 1er janvier 2025 au 31 decembre 2025." + MENTION),
]
