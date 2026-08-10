import os

from dotenv import load_dotenv
from openai import OpenAI

from app.prompt.prompt_support import SUPPORT_PROMPT


load_dotenv()


client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = os.getenv("OPENROUTER_MODEL")


def analyze_ticket(context, texte, transcription, image):

    prompt = SUPPORT_PROMPT.format(
        context=context,
        texte=texte or "Aucune description écrite.",
        transcription=transcription or "Aucune transcription audio.",
        image=image or "Aucune analyse d'image."
    )

    print("\n========== CONTEXT ENVOYÉ AU LLM ==========")
    print(context)


    print("========== PROMPT ENVOYÉ AU LLM ==========")
    print(prompt)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content