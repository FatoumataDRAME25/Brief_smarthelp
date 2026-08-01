from functools import lru_cache
from transformers import pipeline
from PIL import Image

@lru_cache(maxsize=1)
def get_model_vit():
    return pipeline("image-classification", model="google/vit-base-patch16-224")  # on choisira le modèle ensemble juste après


def analyze_image(filepath: str) -> str:
    image = Image.open(filepath)                    # ouvrir le fichier avec Pillow
    model = get_model_vit()                    # récupérer le modèle chargé
    result = model(image)            # appeler le modèle avec l'image (pas le filepath !)
    label = result[0]["label"]
    score = result[0]["score"]
    return f"{label} (confiance: {score:.2f})"             