from __future__ import annotations

import re

from ..modules import document_intake


CANONICAL_DOCUMENT_TYPE_OPTIONS = (
    {"value": "Reglement_Copropriete", "label": "Reglement de copropriete"},
    {"value": "EDD", "label": "Etat descriptif de division"},
    {"value": "Fiche_Synthetique", "label": "Fiche synthetique"},
    {"value": "Carnet_Entretien", "label": "Carnet d'entretien"},
    {"value": "Diagnostic_Technique", "label": "Diagnostic"},
    {"value": "Plan", "label": "Plan"},
    {"value": "Convocation_AG", "label": "Assemblee generale"},
    {"value": "Annexe_AG", "label": "Annexe d'AG"},
    {"value": "Feuille_Presence_AG", "label": "Presence et pouvoirs"},
    {"value": "PV_AG", "label": "Proces-verbal d'AG"},
    {"value": "CR_CS", "label": "Compte rendu du conseil syndical"},
    {"value": "Contrat_Syndic", "label": "Contrat du syndic"},
    {"value": "Contrat_Assurance", "label": "Assurance"},
    {"value": "Attestation_Assurance", "label": "Attestation"},
    {"value": "Contrat_Fournisseur", "label": "Contrat fournisseur"},
    {"value": "Contrat_Maintenance", "label": "Maintenance"},
    {"value": "Contrat_Travail", "label": "Contrat de travail"},
    {"value": "Annexe_Comptable", "label": "Comptes annuels"},
    {"value": "Budget_Previsionnel", "label": "Budget"},
    {"value": "Grand_Livre", "label": "Grand livre"},
    {"value": "Etat_Depenses", "label": "Depenses"},
    {"value": "Appel_Fonds", "label": "Appel de fonds"},
    {"value": "Fonds_Travaux", "label": "Fonds travaux"},
    {"value": "Facture", "label": "Facture"},
    {"value": "Avoir", "label": "Avoir"},
    {"value": "Note_Honoraires", "label": "Note d'honoraires"},
    {"value": "Devis", "label": "Devis"},
    {"value": "Releve_Bancaire", "label": "Banque"},
    {"value": "Impayes", "label": "Impayes"},
    {"value": "Dossier_Travaux", "label": "Travaux"},
    {"value": "Dossier_ITE_Travaux", "label": "Isolation / ravalement"},
    {"value": "Marche_Travaux", "label": "Marche travaux"},
    {"value": "Ordre_Service", "label": "Ordre de service"},
    {"value": "Situation_Travaux", "label": "Avancement travaux"},
    {"value": "Reception_Travaux", "label": "Reception travaux"},
    {"value": "Reserve_Travaux", "label": "Reserve a lever"},
    {"value": "DOE_Travaux", "label": "Dossier de fin de travaux"},
    {"value": "Photo_Incident", "label": "Photo d'incident"},
    {"value": "Declaration_Assurance", "label": "Declaration assurance"},
    {"value": "Expertise", "label": "Expertise"},
    {"value": "Dossier_Sinistre", "label": "Dossier sinistre"},
    {"value": "Courrier", "label": "Courrier"},
    {"value": "Email", "label": "Email"},
    {"value": "LRAR", "label": "Lettre recommandee"},
    {"value": "Accuse_Reception", "label": "Accuse de reception"},
    {"value": "Preuve_Envoi", "label": "Preuve d'envoi"},
    {"value": "Reponse_Syndic", "label": "Reponse du syndic"},
    {"value": "Communication", "label": "Communication"},
    {"value": "Mise_En_Demeure", "label": "Mise en demeure"},
    {"value": "Recouvrement", "label": "Recouvrement"},
    {"value": "Contentieux_Nominatif", "label": "Dossier contentieux"},
    {"value": "Dossier_Contentieux", "label": "Contentieux"},
    {"value": "Piece_Sensible", "label": "Piece sensible"},
)

LEGACY_DOCUMENT_TYPE_OPTIONS = (
    {"value": "AG", "label": "Assemblee generale"},
    {"value": "FACTURE_COMPTE", "label": "Facture ou compte"},
    {"value": "TRAVAUX", "label": "Travaux"},
    {"value": "CONTRAT_ASSURANCE_SYNDIC", "label": "Contrat, assurance ou syndic"},
    {"value": "COURRIER_REPONSE", "label": "Courrier ou reponse"},
    {"value": "CONTENTIEUX_INCIDENT", "label": "Contentieux ou incident"},
    {"value": "AUTRE_PREUVE", "label": "Autre preuve"},
)

DOCUMENT_TYPE_OPTIONS = (
    {"value": "A_CLASSER", "label": "Je ne sais pas encore"},
    *CANONICAL_DOCUMENT_TYPE_OPTIONS,
    *LEGACY_DOCUMENT_TYPE_OPTIONS,
)

DOCUMENT_TYPE_VALUES = frozenset(option["value"] for option in DOCUMENT_TYPE_OPTIONS)
DOCUMENT_TYPE_TOKEN_ALIASES = {
    re.sub(r"[^A-Z0-9_]+", "_", value.upper()).strip("_"): value
    for value in DOCUMENT_TYPE_VALUES
}


def normalize_document_type_value(value: object, default: str = "A_CLASSER") -> str:
    token = re.sub(r"[^A-Z0-9_]+", "_", str(value or "").strip().upper()).strip("_")
    return DOCUMENT_TYPE_TOKEN_ALIASES.get(token, default)

PRIVACY_OPTIONS = (
    {"value": document_intake.PRIVACY_ARBITRATE, "label": "A decider"},
    {"value": document_intake.PRIVACY_RAW, "label": "Peut etre partage tel quel"},
    {"value": document_intake.PRIVACY_REDACT, "label": "A masquer avant partage"},
    {"value": document_intake.PRIVACY_CS_ONLY, "label": "Reserve au conseil syndical"},
    {"value": document_intake.PRIVACY_BLOCKED, "label": "Ne pas partager"},
)

POINT_KIND_OPTIONS = (
    {"value": "preuve_libre", "label": "Preuve libre"},
    {"value": "ag", "label": "AG"},
    {"value": "decision", "label": "Decision"},
    {"value": "demande", "label": "Demande"},
    {"value": "facture", "label": "Facture"},
    {"value": "incident", "label": "Incident"},
    {"value": "chantier", "label": "Chantier"},
    {"value": "contentieux", "label": "Contentieux"},
)

ACTION_KIND_OPTIONS = (
    {"value": "verifier", "label": "Verifier"},
    {"value": "demander", "label": "Demander"},
    {"value": "relancer", "label": "Relancer"},
    {"value": "biffer", "label": "Biffer"},
    {"value": "transmettre", "label": "Transmettre"},
    {"value": "classer", "label": "Classer"},
)

PROOF_INTENT_OPTIONS = (
    {"value": "presence", "label": "Presence"},
    {"value": "decision", "label": "Decision"},
    {"value": "reception", "label": "Reception"},
    {"value": "execution", "label": "Execution"},
    {"value": "paiement", "label": "Paiement"},
    {"value": "refus", "label": "Refus"},
    {"value": "cloture", "label": "Cloture"},
)
