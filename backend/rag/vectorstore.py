"""
ChromaDB vector store setup and retriever factory.
"""
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import settings

_vectorstore: Chroma | None = None
_embeddings: HuggingFaceEmbeddings | None = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def get_vectorstore() -> Chroma:
    """Return (and lazily initialise) the ChromaDB vector store."""
    global _vectorstore
    if _vectorstore is None:
        persist_dir = os.path.abspath(settings.chroma_persist_dir)
        _vectorstore = Chroma(
            collection_name="law_documents",
            embedding_function=_get_embeddings(),
            persist_directory=persist_dir,
        )
    return _vectorstore


def get_retriever():
    """Return a LangChain retriever backed by ChromaDB."""
    return get_vectorstore().as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.rag_top_k},
    )
