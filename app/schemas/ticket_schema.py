from pydantic import BaseModel
from typing import Optional
from enum import Enum


class StatutTicket(str, Enum):
    REMBOURSABLE = "Remboursable"
    A_VERIFIER = "À vérifier"
    REFUSE = "Refusé"


class TicketResponse(BaseModel):
    transcription: Optional[str] = None        #  str | None = None  (optionel)
    diagnostic_image: Optional[str] = None     #  str | None = None (optionel)
    regle_appliquee: str                       #  (le RAG trouve TOUJOURS une règle, donc pas optionnel)
    statut_propose: StatutTicket                #  (pas optionnel non plus, l'API doit toujours trancher)