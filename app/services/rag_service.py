from functools import lru_cache
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


@lru_cache(maxsize=1)
def get_vector_store():
    # 1. Charger le fichier texte
    loader = TextLoader("data/faq_cgv.txt", encoding="utf-8")
    documents = loader.load()

    # 2. Découper en morceaux (séparateur = tiret "- Règle" pour isoler chaque règle)
    splitter = CharacterTextSplitter(separator="\n- Règle", chunk_size=500, chunk_overlap=0)
    chunks = splitter.split_documents(documents)

    # 3. Générer les embeddings et les stocker dans Chroma
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = Chroma.from_documents(chunks, embeddings)

    return vector_store


def search_knowledge_base(query: str) -> str:
    vector_store = get_vector_store()
    results = vector_store.similarity_search(query, k=1)  # k=1 : on veut la règle la plus proche
    return results[0].page_content