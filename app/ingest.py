import os
from typing import List, Tuple
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from .config import settings
from .ai_providers import get_embeddings


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

    # Normalize metadata
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
    chunks = [c for c in chunks if c.page_content and c.page_content.strip()]    # Filter empty chunks

    # Add chunk ids for citations
    for i, c in enumerate(chunks):
        c.metadata["chunk_id"] = i
    return chunks


def build_or_update_faiss(chunks: List[Document]) -> Tuple[int, str]:
    """
    Build or update a FAISS vector index from document chunks.
    Robust to partial embedding failures (Vertex returning fewer vectors).
    """
    os.makedirs(settings.index_dir, exist_ok=True)
    emb = get_embeddings()

    index_path = settings.index_dir
    faiss_file = os.path.join(index_path, "index.faiss")

    texts = [c.page_content for c in chunks]
    metadatas = [c.metadata for c in chunks]

    BATCH_SIZE = 64
    kept_texts: List[str] = []
    kept_metas: List[dict] = []
    kept_vecs: List[list] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_metas = metadatas[i:i + BATCH_SIZE]

        try:
            batch_vecs = emb.embed_documents(batch_texts)
        except Exception:
            for t, m in zip(batch_texts, batch_metas):
                try:
                    v1 = emb.embed_documents([t])
                    if v1 and len(v1) == 1:
                        kept_texts.append(t)
                        kept_metas.append(m)
                        kept_vecs.append(v1[0])
                except Exception:
                    continue
            continue

        n = min(len(batch_texts), len(batch_vecs))
        for j in range(n):
            kept_texts.append(batch_texts[j])
            kept_metas.append(batch_metas[j])
            kept_vecs.append(batch_vecs[j])

    if not kept_texts:
        raise RuntimeError("No chunks could be embedded (all embedding attempts failed).")

    if os.path.exists(faiss_file):
        vs = FAISS.load_local(index_path, emb, allow_dangerous_deserialization=True)
        vs.add_embeddings(text_embeddings=list(zip(kept_texts, kept_vecs)), metadatas=kept_metas)
    else:
        vs = FAISS.from_embeddings(
            text_embeddings=list(zip(kept_texts, kept_vecs)),
            embedding=emb,
            metadatas=kept_metas,
        )

    vs.save_local(index_path)
    return len(kept_texts), index_path


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