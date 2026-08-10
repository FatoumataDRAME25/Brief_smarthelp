from functools import lru_cache
import os
import re
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


def load_rules_as_documents():
    with open("data/faq_cgv.txt", encoding="utf-8") as f:
        contenu = f.read()

    regles = re.findall(r"(?m)^- Règle.*$", contenu)

    print("Nombre de règles :", len(regles))
    

    for i, regle in enumerate(regles):
        print(f"\n===== RÈGLE {i + 1} =====")
        print(regle)


    return [
        Document(page_content=regle)
        for regle in regles
    ]


@lru_cache(maxsize=1)
def get_vector_store():
    chunks = load_rules_as_documents()

    embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-mpnet-base-v2")
    if os.path.exists("./store"):
        print("========== CHARGEMENT DE LA BASE EXISTANTE ==========")

        vector_store = Chroma(
            persist_directory="./store",
            embedding_function=embeddings
        )

    else:
        print("========== CRÉATION DE LA BASE VECTORIELLE ==========")

        chunks = load_rules_as_documents()

        vector_store = Chroma.from_documents(
            chunks,
            embeddings,
            persist_directory="./store"
        )

    print(
        "Nombre de documents dans Chroma :",
        vector_store._collection.count()
    )
    return vector_store


def search_knowledge_base(query: str) -> str:
    vector_store = get_vector_store()
    results = vector_store.similarity_search(query, k=6)

    print("Nombre de documents Chroma :", vector_store._collection.count())
    print("\n========== REQUÊTE ==========")
    print(query)

    print("\n========== RÉSULTATS CHROMA ==========")

    if not results:
        return "Aucune règle applicable trouvée."

    context = "\n\n".join(
        result.page_content
        for result in results
    )

    return context