import json

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
from app.services.asr_service import transcribe_audio
from app.services.vision_service import analyze_image
from app.services.rag_service import search_knowledge_base
from app.services.llm_service import analyze_ticket
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

            try:
                transcription = transcribe_audio(audio_path) # appeler le service ASR
            except Exception as e:
                raise HTTPException(
                status_code=422,
                detail=f"Le fichier audio fourni est invalide ou corrompu : {str(e)}"
            )

        if image_file:
            image_path = f"temp/{image_file.filename}"
            save_temp_file(image_file, image_path)

            try:
                diagnostic_image = analyze_image(image_path)
            except Exception as e:
                raise HTTPException(
                status_code=422,
                detail=f"Le fichier image fourni est invalide ou corrompu : {str(e)}"
            )


        elements_valides = [e for e in [transcription, diagnostic_image, texte] if e]
        texte_final = " ".join(elements_valides)
        
        context = search_knowledge_base(texte_final)
        print("========== CONTEXT RAG ==========")
        print(context)

        resultat_llm = analyze_ticket(
            context=context,
            texte=texte,
            transcription=transcription,
            image=diagnostic_image
        )

        resultat_llm = json.loads(resultat_llm)

        print("========== RÉPONSE DU LLM ==========")
        print(resultat_llm)

        return {
            "transcription": transcription,
            "diagnostic_image": diagnostic_image,
            "resultat_llm": resultat_llm
        }
    finally:
        
        if audio_file and os.path.exists(audio_path):
            os.remove(audio_path)
        if image_file and os.path.exists(image_path):
            os.remove(image_path) # nettoyage des fichiers temp