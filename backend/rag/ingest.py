"""
Document ingestion script.

Usage:
    python ingest.py                     # ingest all files in rag/documents/
    python ingest.py --path /some/file   # ingest a specific file
"""
import argparse
import glob
import os
import sys

# Ensure the backend root is on the path when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rag.vectorstore import get_vectorstore


def load_file(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(path)
    else:
        loader = TextLoader(path, encoding="utf-8")
    return loader.load()


def ingest(paths: list[str]) -> int:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
    )
    all_docs = []
    for p in paths:
        print(f"Loading: {p}")
        docs = load_file(p)
        chunks = splitter.split_documents(docs)
        for chunk in chunks:
            chunk.metadata["source"] = os.path.basename(p)
        all_docs.extend(chunks)
        print(f"  → {len(chunks)} chunks")

    if not all_docs:
        print("No documents to ingest.")
        return 0

    vs = get_vectorstore()
    vs.add_documents(all_docs)
    print(f"\n✅ Ingested {len(all_docs)} chunks into ChromaDB.")
    return len(all_docs)


def main():
    parser = argparse.ArgumentParser(description="Ingest law documents into ChromaDB")
    parser.add_argument("--path", type=str, default=None, help="File or directory to ingest")
    args = parser.parse_args()

    if args.path:
        target = args.path
        if os.path.isdir(target):
            paths = glob.glob(os.path.join(target, "**", "*.*"), recursive=True)
            paths = [p for p in paths if os.path.splitext(p)[1].lower() in {".txt", ".pdf", ".md"}]
        else:
            paths = [target]
    else:
        base = os.path.join(os.path.dirname(__file__), "documents")
        paths = glob.glob(os.path.join(base, "**", "*.*"), recursive=True)
        paths = [p for p in paths if os.path.splitext(p)[1].lower() in {".txt", ".pdf", ".md"}]

    if not paths:
        print("No files found to ingest.")
        return

    ingest(paths)


if __name__ == "__main__":
    main()
