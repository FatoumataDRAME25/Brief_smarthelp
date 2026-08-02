from functools import lru_cache
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


def load_rules_as_documents():
    with open("data/faq_cgv.txt", encoding="utf-8") as f:
        contenu = f.read()

    morceaux_bruts = contenu.split("\n- Règle")
    regles = ["- Règle" + morceau for morceau in morceaux_bruts[1:]]

    return [Document(page_content=regle) for regle in regles]


@lru_cache(maxsize=1)
def get_vector_store():
    chunks = load_rules_as_documents()

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    vector_store = Chroma.from_documents(chunks, embeddings)

    return vector_store


def search_knowledge_base(query: str) -> str:
    vector_store = get_vector_store()
    results = vector_store.similarity_search(query, k=3)

    for result in results:
        if "Statut associé" in result.page_content:
            return result.page_content

    return "Aucune règle applicable trouvée."