"""Lecture d'un etat des depenses depuis sa couche de texte.

Le tableau arrive aplati: un jeton par ligne, l'ordre de lecture du PDF. Le
lecteur ne peut donc pas s'appuyer sur des colonnes, et **c'est heureux**: une
lecture positionnelle serait un moulage du cabinet observe. Il s'appuie sur
trois invariants qui, eux, ne dependent d'aucun cabinet.

1. **Un total se declare.** Une ligne de total porte le mot `TOTAL` et aucun
   taux. C'est ce qui ferme un enregistrement.
2. **Le premier nombre d'un enregistrement est le montant a repartir.** C'est
   la premiere colonne chiffree de tout etat des depenses lu.
3. **Le taux se prouve, il ne se reconnait pas.** Un nombre n'est retenu comme
   taux que si la taxe voisine retombe dessus au centime. Cette regle unique
   remplace toute connaissance de l'ordre des colonnes, et c'est elle qui
   permet de lire un enregistrement a trois nombres sans savoir a l'avance si
   la colonne des charges locatives est presente ou absente.

Ce que le lecteur fait hors des valeurs observees: il ne devine pas. Un
enregistrement dont les nombres ne se lient a aucune combinaison connue est
conserve avec son montant a repartir seul, et un constat `COLONNES_NON_LIABLES`
nomme la ligne. Aucune valeur n'est inventee pour completer un gabarit.
"""

from __future__ import annotations

import re
from decimal import Decimal

from ._comptes_extraction_lexique import (
    detecter_separateur_decimal,
    est_compte,
    est_date,
    est_taux_plausible,
    identite_taxe_tient,
    lire_montant,
    marqueur_de,
    taxe_incluse,
)
from ._comptes_extraction_mise_en_page import (
    _MOT_TOTAL,
    _PARTS,
    _TOTAL_COURANTES,
    _TOTAL_GENERAL,
    _TOTAL_TRAVAUX,
    _COMPTE_ET_LIBELLE,
    _CODE_SEUL,
    _colonnes_annoncees,
    _compacte,
    _est_bruit,
    _est_reference,
    _exercice,
    _libelle_de_total,
    _marqueur_de_ligne,
)
from ._comptes_extraction_modele import (
    CLE,
    COLONNES_NON_LIABLES,
    COMPTE,
    CONVENTION_INCONNUE,
    COURANTES,
    DETAILLE,
    GENERAL,
    HT_TAXE_AJOUTEE,
    SEPARATEUR_INDECIDABLE,
    SOUS_POSTE,
    SYNTHESE,
    TAXE_DISCORDANTE,
    TOTAL_ABSENT,
    TOTAL_GENERAL_ABSENT,
    TOTAL_LIGNE,
    TRAVAUX,
    TTC_TAXE_INCLUSE,
    ConstatExtraction,
    EtatDepenses,
    LigneEtat,
    ProfilTableau,
    TotalEtat,
)





class _Enregistrement:
    """Accumulateur d'un enregistrement en cours de lecture."""

    def __init__(self) -> None:
        self.date = ""
        self.reference = ""
        self.libelle_mots: list[str] = []
        self.nombres: list[str] = []

    def vide(self) -> bool:
        return not self.nombres and not self.libelle_mots and not self.date








def _granularite(lignes: list[LigneEtat]) -> str:
    """`DETAILLE` si la majorite des lignes porte sa propre date de piece.

    La granularite n'est pas un nom de fichier: le corpus montre un etat dit
    detaille dans un fichier qui ne le dit pas, et l'inverse. Elle se mesure
    donc sur le contenu. Le seuil est la majorite, parce qu'un etat de synthese
    porte quand meme quelques dates isolees, et qu'un etat detaille en porte
    partout. Entre les deux, la mesure est rendue telle quelle et l'appelant
    voit la proportion dans le fait que les deux formes coexistent.
    """
    if not lignes:
        return SYNTHESE
    datees = sum(1 for ligne in lignes if ligne.date)
    return DETAILLE if datees * 2 > len(lignes) else SYNTHESE


def _lier(
    bruts: list[str],
    separateur: str,
) -> tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None, bool]:
    """Lie les nombres d'un enregistrement aux colonnes, par preuve.

    Rend `(montant, locatives, taux, taxe, liaison_sure)`. La liaison est faite
    par l'identite de taxe incluse et non par une position: c'est ce qui rend le
    lecteur independant de l'ordre des colonnes du cabinet.
    """
    valeurs = [lire_montant(brut, separateur) for brut in bruts]
    valeurs = [valeur for valeur in valeurs if valeur is not None]
    if not valeurs:
        return None, None, None, None, True
    montant = valeurs[0]
    if len(valeurs) == 1:
        return montant, None, None, None, True

    # Le taux ne peut occuper que l'avant-derniere place, et seulement si la
    # taxe qui le suit retombe sur lui. Deux conventions sont testees; celle qui
    # tient nomme la convention du document.
    taux_candidat = valeurs[-2]
    taxe_candidate = valeurs[-1]
    if len(valeurs) >= 3 and est_taux_plausible(taux_candidat):
        for incluse in (True, False):
            if identite_taxe_tient(montant, taux_candidat, taxe_candidate, incluse=incluse):
                locatives = valeurs[1] if len(valeurs) == 4 else None
                if len(valeurs) > 4:
                    return montant, None, taux_candidat, taxe_candidate, False
                return montant, locatives, taux_candidat, taxe_candidate, True
        # Le taux est plausible mais la taxe ne retombe pas: c'est justement
        # l'ecart que le lot doit faire ressortir. La liaison reste sure, le
        # constat est emis par l'appelant qui connait la reference de piece.
        if len(valeurs) <= 4:
            locatives = valeurs[1] if len(valeurs) == 4 else None
            return montant, locatives, taux_candidat, taxe_candidate, True

    if len(valeurs) == 2:
        return montant, valeurs[1], None, None, True
    if len(valeurs) == 3:
        return montant, valeurs[1], None, valeurs[2], True
    return montant, None, None, None, False


def _portee_du_total(libelle: str, dans_cle: bool, apres_compte: bool) -> str:
    """Portee d'un total, deduite de sa nature puis, a defaut, de sa place.

    La nature prime: un total de charges courantes reste un total de charges
    courantes quelle que soit la ligne ou il tombe. La place ne sert qu'aux
    totaux intermediaires, que rien ne nomme.
    """
    compact = _compacte(libelle)
    if _TOTAL_GENERAL in compact:
        return GENERAL
    if _TOTAL_COURANTES in compact:
        return COURANTES
    if _TOTAL_TRAVAUX in compact:
        return TRAVAUX
    if "***" in libelle or _PARTS.search(libelle):
        return CLE
    if libelle.strip().startswith("---"):
        return COMPTE
    if apres_compte:
        return SOUS_POSTE
    return CLE if dans_cle else COMPTE


def lire_etat_depenses(texte: str) -> EtatDepenses:
    """Lit un etat des depenses depuis sa couche de texte aplatie."""
    lignes = texte.splitlines()
    separateur = detecter_separateur_decimal(lignes)
    constats: list[ConstatExtraction] = []
    if separateur is None:
        constats.append(
            ConstatExtraction(
                code=SEPARATEUR_INDECIDABLE,
                message=(
                    "Le separateur decimal du document n'a pas pu etre etabli. "
                    "Aucun montant n'est lu: une lecture au hasard vaudrait un "
                    "facteur mille sans signe visible."
                ),
            )
        )
        return EtatDepenses(constats=tuple(constats))

    debut, fin = _exercice(lignes)
    etat = _Lecteur(lignes, separateur).lire()
    profil = ProfilTableau(
        separateur_decimal=separateur,
        colonnes=_colonnes_annoncees(lignes),
        convention_montant=etat.convention,
        granularite=_granularite(etat.lignes_lues),
        reference_piece_presente=etat.references_vues,
        emplacement_total_general=(
            TOTAL_LIGNE if any(item.portee == GENERAL for item in etat.totaux) else TOTAL_ABSENT
        ),
        colonne_charges_locatives=any(ligne.charges_locatives is not None for ligne in etat.lignes_lues),
        colonne_taux=any(ligne.taux_taxe is not None for ligne in etat.lignes_lues),
        marqueurs_de_cle_observes=tuple(sorted(etat.marqueurs)),
    )
    constats.extend(etat.constats)
    if profil.emplacement_total_general == TOTAL_ABSENT:
        constats.append(
            ConstatExtraction(
                code=TOTAL_GENERAL_ABSENT,
                message=(
                    "Le document ne porte pas de total general imprime. Les "
                    "totaux disponibles sont ceux des portees plus fines."
                ),
            )
        )
    return EtatDepenses(
        exercice_debut=debut,
        exercice_fin=fin,
        profil=profil,
        lignes=tuple(etat.lignes_lues),
        totaux=tuple(etat.totaux),
        constats=tuple(constats),
    )


class _Lecteur:
    """Automate de lecture. Sort des listes brutes, sans jugement."""

    def __init__(self, lignes: list[str], separateur: str) -> None:
        self.lignes = lignes
        self.separateur = separateur
        self.lignes_lues: list[LigneEtat] = []
        self.totaux: list[TotalEtat] = []
        self.constats: list[ConstatExtraction] = []
        self.marqueurs: set[str] = set()
        self.dates_vues = False
        self.references_vues = False
        self.convention = CONVENTION_INCONNUE
        self.cle = ""
        self.compte = ""
        self.compte_libelle = ""
        self.sous_poste = ""
        self.attend_cle = True
        self.code_en_attente = ""
        self.total_en_cours: tuple[str, str] | None = None
        # Index de la premiere ligne du bloc courant. Un bloc se ferme sur un
        # total de charges courantes ou de travaux; c'est la seule facon de
        # recouper un total de bloc avec les lignes qui le composent.
        self.debut_du_bloc = 0
        self.enregistrement = _Enregistrement()

    # -- API ----------------------------------------------------------------

    def lire(self) -> "_Lecteur":
        for brut in self.lignes:
            self._consommer(brut)
        self._fermer()
        return self

    # -- automate -----------------------------------------------------------

    def _consommer(self, brut: str) -> None:
        nu = brut.strip()
        if _est_bruit(brut):
            return
        if lire_montant(nu, self.separateur) is not None:
            self.enregistrement.nombres.append(nu)
            marqueur = marqueur_de(nu)
            if marqueur:
                self.marqueurs.add(marqueur)
            return
        # Tout jeton non numerique ferme l'enregistrement chiffre en cours.
        if self.enregistrement.nombres:
            self._fermer()
        if _MOT_TOTAL.search(nu):
            self._ouvrir_total(nu)
            return
        trouve = _COMPTE_ET_LIBELLE.match(brut)
        if trouve and est_compte(trouve.group(1)):
            self._nouveau_compte(trouve.group(1), trouve.group(2).strip())
            return
        code = _CODE_SEUL.match(nu)
        if code is not None:
            self.code_en_attente = code.group(1)
            return
        if self.code_en_attente:
            self._nouveau_code(self.code_en_attente, nu)
            self.code_en_attente = ""
            return
        if est_date(nu):
            self._fermer()
            self.enregistrement.date = nu
            self.dates_vues = True
            return
        if self.enregistrement.date and not self.enregistrement.reference and _est_reference(nu):
            self.enregistrement.reference = nu
            self.references_vues = True
            return
        if nu.startswith("-") and not self.enregistrement.libelle_mots:
            self._fermer()
            self.enregistrement.libelle_mots.append(nu.lstrip("- ").strip())
            return
        self.enregistrement.libelle_mots.append(nu)

    def _ouvrir_total(self, libelle: str) -> None:
        self._fermer()
        portee = _portee_du_total(libelle, bool(self.cle), bool(self.compte))
        self.total_en_cours = (portee, libelle)
        self.enregistrement = _Enregistrement()

    def _nouveau_compte(self, numero: str, libelle: str) -> None:
        self._fermer()
        self.compte = numero
        self.compte_libelle = libelle
        self.sous_poste = ""
        self.attend_cle = False
        self.code_en_attente = ""

    def _nouveau_code(self, code: str, libelle: str) -> None:
        """Un code suivi d'un libelle: cle de repartition, ou sous-poste.

        La distinction ne se lit pas sur le code, qui a la meme forme dans les
        deux cas. Elle se lit sur la place: un code rencontre avant tout compte,
        ou juste apres un total de cle, ouvre une cle; sinon il ouvre un
        sous-poste. C'est un axe, pas une convention de cabinet.
        """
        self._fermer()
        if self.attend_cle or not self.compte:
            self.cle = f"{code} {libelle}".strip()
            self.compte = ""
            self.compte_libelle = ""
            self.sous_poste = ""
            self.attend_cle = False
        else:
            self.sous_poste = f"{code} {libelle}".strip()

    def _fermer(self) -> None:
        enregistrement = self.enregistrement
        self.enregistrement = _Enregistrement()
        if self.total_en_cours is not None:
            portee, libelle = self.total_en_cours
            self.total_en_cours = None
            if enregistrement.nombres:
                self._ajouter_total(portee, libelle, enregistrement.nombres)
            if portee == CLE:
                self.attend_cle = True
                self.compte = ""
            if portee in {COURANTES, TRAVAUX}:
                self.debut_du_bloc = len(self.lignes_lues)
            return
        if enregistrement.vide() or not enregistrement.nombres:
            return
        montant, locatives, taux, taxe, sure = _lier(enregistrement.nombres, self.separateur)
        libelle = " ".join(enregistrement.libelle_mots).strip()
        reference = enregistrement.reference
        if not sure:
            self.constats.append(
                ConstatExtraction(
                    code=COLONNES_NON_LIABLES,
                    message=(
                        "Les nombres de cette ligne ne se lient a aucune "
                        "combinaison de colonnes prouvable. Seul le montant a "
                        "repartir est retenu."
                    ),
                    reference_piece=reference,
                    compte=self.compte,
                    valeur_document=" ".join(enregistrement.nombres),
                )
            )
        self._noter_convention(montant, taux, taxe, reference)
        self.lignes_lues.append(
            LigneEtat(
                cle_repartition=self.cle,
                compte=self.compte,
                compte_libelle=self.compte_libelle,
                sous_poste=self.sous_poste,
                date=enregistrement.date,
                reference_piece=reference,
                libelle=libelle,
                montant_a_repartir=montant,
                charges_locatives=locatives,
                taux_taxe=taux,
                montant_taxe=taxe,
                marqueur_cle=_marqueur_de_ligne(enregistrement.nombres),
            )
        )

    def _noter_convention(
        self,
        montant: Decimal | None,
        taux: Decimal | None,
        taxe: Decimal | None,
        reference: str,
    ) -> None:
        """Etablit la convention du document, et signale toute discordance.

        La convention est etablie par la premiere ligne qui la prouve, puis
        n'est plus revue: un document qui melangerait les deux conventions
        produirait des discordances, et une discordance est un constat, pas une
        raison de changer d'avis sur le document.
        """
        if montant is None or taux is None or taxe is None or taux <= 0:
            return
        if identite_taxe_tient(montant, taux, taxe, incluse=True):
            if self.convention == CONVENTION_INCONNUE:
                self.convention = TTC_TAXE_INCLUSE
            return
        if identite_taxe_tient(montant, taux, taxe, incluse=False):
            if self.convention == CONVENTION_INCONNUE:
                self.convention = HT_TAXE_AJOUTEE
            return
        attendue = taxe_incluse(montant, taux)
        self.constats.append(
            ConstatExtraction(
                code=TAXE_DISCORDANTE,
                message=(
                    "La taxe portee par la ligne ne retombe pas sur le taux "
                    "affiche. Les deux valeurs sont conservees; seul le syndic "
                    "peut dire s'il s'agit d'un parametrage de compte ou d'une "
                    "erreur d'imputation."
                ),
                reference_piece=reference,
                compte=self.compte,
                valeur_document=str(taxe),
                valeur_calculee=str(attendue),
            )
        )

    def _ajouter_total(self, portee: str, libelle: str, bruts: list[str]) -> None:
        """Enregistre un total imprime, en liant ses nombres par recoupement.

        Un total ne porte jamais de taux. Ses nombres se lient donc par leur
        seul nombre, avec une ambiguite reelle a deux nombres: montant plus
        charges locatives, ou montant plus taxe. Elle est tranchee par les
        lignes deja lues, pas par une convention de cabinet.
        """
        valeurs = [lire_montant(brut, self.separateur) for brut in bruts]
        valeurs = [valeur for valeur in valeurs if valeur is not None]
        parts = ""
        trouve = _PARTS.search(libelle)
        if trouve is not None:
            parts = trouve.group(1).strip()
        montant = valeurs[0] if valeurs else None
        locatives: Decimal | None = None
        taxe: Decimal | None = None
        if len(valeurs) == 2:
            if self._second_nombre_est_locatif(portee, valeurs[1]):
                locatives = valeurs[1]
            else:
                taxe = valeurs[1]
        elif len(valeurs) >= 3:
            locatives = valeurs[1]
            taxe = valeurs[2]
        self.totaux.append(
            TotalEtat(
                portee=portee,
                libelle=_libelle_de_total(libelle),
                montant_a_repartir=montant,
                charges_locatives=locatives,
                montant_taxe=taxe,
                parts=parts,
            )
        )

    def _second_nombre_est_locatif(self, portee: str, valeur: Decimal) -> bool:
        """Tranche l'ambiguite d'un total a deux nombres, par recoupement.

        Un total qui n'imprime que deux nombres peut etre `montant + charges
        locatives` ou `montant + taxe`: rien dans sa forme ne le dit. Le
        depart se fait sur les lignes deja lues, en comparant la valeur aux
        deux sommes candidates. C'est un recoupement, pas une convention: sur
        un cabinet non observe, la meme comparaison s'applique.

        Quand aucune des deux sommes ne retombe, la reponse par defaut suit la
        seule chose etablie sur ce document: si ses lignes ne portent aucune
        charge locative, le second nombre ne peut pas en etre une.
        """
        if portee in {COURANTES, TRAVAUX}:
            lignes = self.lignes_lues[self.debut_du_bloc :]
        elif portee == GENERAL:
            lignes = self.lignes_lues
        else:
            lignes = self.lignes_lues[-40:]
        somme_locatives = sum(
            (ligne.charges_locatives or Decimal("0")) for ligne in lignes
        )
        somme_taxe = sum((ligne.montant_taxe or Decimal("0")) for ligne in lignes)
        ecart_locatif = abs(somme_locatives - valeur)
        ecart_taxe = abs(somme_taxe - valeur)
        if ecart_locatif != ecart_taxe:
            return ecart_locatif < ecart_taxe
        return any(ligne.charges_locatives is not None for ligne in lignes)




__all__ = ["lire_etat_depenses"]
