from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
from app.services.asr_service import transcribe_audio
from app.services.vision_service import analyze_image
from app.services.rag_service import search_knowledge_base
from app.schemas.ticket_schema import StatutTicket, TicketResponse
import shutil


router = APIRouter()


def save_temp_file(upload_file: UploadFile, destination: str):
    with open(destination, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)


@router.post("/support-ticket")
async def support_ticket(
    audio_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    texte: Optional[str] = Form(None)
):
    if not audio_file and not image_file and not texte:
        raise HTTPException(
            status_code=400,
            detail="Vous devez fournir au moins un audio, une image ou un texte descriptif."
        )
    
    

    transcription = None
    diagnostic_image = None
    audio_path = None
    image_path = None
    
    
    try:
        if audio_file:
            audio_path = f"temp/{audio_file.filename}"
            save_temp_file(audio_file, audio_path)  # sauvegarder le fichier
            transcription = transcribe_audio(audio_path)  # appeler le service ASR

        if image_file:
            image_path = f"temp/{image_file.filename}"
            save_temp_file(image_file, image_path)
            diagnostic_image = analyze_image(image_path)

        elements_valides = [e for e in [transcription, diagnostic_image, texte] if e]
        texte_final = " ".join(elements_valides)
        
        regle = search_knowledge_base(texte_final)  # appeler le RAG

        statut_final = StatutTicket.A_VERIFIER
        for statut in StatutTicket:
            if statut.value in regle:
                statut_final = statut
                break

        return TicketResponse(
            transcription=transcription,
            diagnostic_image=diagnostic_image,
            regle_appliquee=regle,
            statut_propose=statut_final
        )
    finally:
        
        if audio_file and os.path.exists(audio_path):
            os.remove(audio_path)
        if image_file and os.path.exists(image_path):
            os.remove(image_path) # nettoyage des fichiers temp