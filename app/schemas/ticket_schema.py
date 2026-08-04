from pydantic import BaseModel
from typing import Optional
from enum import Enum


class StatutTicket(str, Enum):
    REMBOURSABLE = "Remboursable"
    A_VERIFIER = "À vérifier"
    REFUSE = "Refusé"
    ECHANGE_GRATUIT = "Échange gratuit"
    EXPEDITION_PIECE = "Expédition de pièce"
    NON_REMBOURSABLE_RETARD_MINEUR = "Non remboursable - Retard mineur"
    DEDOMMAGEMENT_10 = "Dédommagement 10%"
    REMBOURSABLE_COLIS_PERDU = "Remboursable - Colis perdu"
    EN_ATTENTE_JUSTIFICATIFS = "En attente de justificatifs"


class TicketResponse(BaseModel):
    transcription: Optional[str] = None        #  str | None = None  (optionel)
    diagnostic_image: Optional[str] = None     #  str | None = None (optionel)
    regle_appliquee: str                       #  (le RAG trouve TOUJOURS une règle, donc pas optionnel)
    statut_propose: StatutTicket                #  (pas optionnel non plus, l'API doit toujours trancher)