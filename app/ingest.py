import os
from typing import List, Tuple
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from .config import settings

SUPPORTED_EXTS = {".pdf", ".txt", ".md", ".csv"}


def _load_one_file(path: str) -> List[Document]:
    """
     Load a single file from disk and convert it into LangChain Document objects.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        docs = PyPDFLoader(path).load()
    elif ext in {".md", ".txt"}:
        docs = TextLoader(path, encoding="utf-8").load()
    elif ext == ".csv":
        df = pd.read_csv(path)
        # Convert rows to text blocks
        rows = []
        for i, row in df.iterrows():
            rows.append(Document(
                page_content=" | ".join([f"{c}: {row[c]}" for c in df.columns]),
                metadata={"source": os.path.basename(path), "row": int(i)}
            ))
        docs = rows
    else:
        return []

    # normalize metadata
    for d in docs:
        d.metadata = d.metadata or {}
        d.metadata["source"] = os.path.basename(path)
        d.metadata["path"] = path
    return docs


def load_raw_documents(raw_dir: str) -> List[Document]:
    """
    Recursively load all supported documents from a directory.
    """
    all_docs: List[Document] = []
    for root, _, files in os.walk(raw_dir):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in SUPPORTED_EXTS:
                all_docs.extend(_load_one_file(os.path.join(root, name)))
    return all_docs


def chunk_documents(docs: List[Document]) -> List[Document]:
    """
    Split documents into text chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
    )
    chunks = splitter.split_documents(docs)

    # Add chunk ids for citations
    for i, c in enumerate(chunks):
        c.metadata["chunk_id"] = i
    return chunks


def build_or_update_faiss(chunks: List[Document]) -> Tuple[int, str]:
    """
    Build or update a FAISS vector index from document chunks.
    """
    os.makedirs(settings.index_dir, exist_ok=True)
    embeddings = OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)

    index_path = settings.index_dir
    faiss_file = os.path.join(index_path, "index.faiss")

    if os.path.exists(faiss_file):
        vs = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        vs.add_documents(chunks)
    else:
        vs = FAISS.from_documents(chunks, embeddings)

    vs.save_local(index_path)
    return len(chunks), index_path


def ingest_all() -> dict:
    """
    Execute the full ingestion pipeline for all raw documents.
    """
    docs = load_raw_documents(settings.raw_data_dir)
    if not docs:
        raise RuntimeError("No documents were loaded from RAW_DATA_DIR")
    chunks = chunk_documents(docs)
    if not chunks:
        raise RuntimeError("Document loading succeeded but chunking produced 0 chunks")
    n, path = build_or_update_faiss(chunks)
    return {"documents_loaded": len(docs), "chunks_indexed": n, "index_dir": path}
