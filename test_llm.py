from app.services.llm_service import analyze_ticket

context = """
- Règle 1.1 (Casse / Dommage visible) : Si le client signale un produit cassé,
fissuré ou endommagé, et fournit une photo probante dans les 48 heures suivant
la réception, le dossier est éligible à un remboursement intégral ou à un renvoi
gratuit. Statut associé : "Remboursable".
"""

texte = "Mon produit est cassé et je viens de le recevoir."

transcription = None

image = "La photo montre un produit visiblement cassé."

resultat = analyze_ticket(
    context=context,
    texte=texte,
    transcription=transcription,
    image=image
)

print("===== RÉPONSE DU LLM =====")
print(resultat)