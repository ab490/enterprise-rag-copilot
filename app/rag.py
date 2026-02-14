import time
from typing import Dict, Any, List
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from .config import settings
from .ai_providers import get_llm, get_embeddings


SYSTEM = """You are an enterprise operations copilot.
Use ONLY the provided context to answer.
If the answer is not in the context, say you don't know and ask a follow-up question.
Always include citations as [source:chunk_id]."""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", "Question: {question}\n\nContext:\n{context}\n\nAnswer with citations:")
])


def load_vectorstore() -> FAISS:
    """
    Load the FAISS vector store from disk.
    """
    embeddings = get_embeddings()
    return FAISS.load_local(settings.index_dir, embeddings, allow_dangerous_deserialization=True)


def format_context(docs: List[Document]) -> str:
    """
    Format retrieved Documents into a single context string for the LLM.
    """
    blocks = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        cid = d.metadata.get("chunk_id", "na")
        blocks.append(f"[{src}:{cid}] {d.page_content}")
    return "\n\n".join(blocks)


def ask(question: str) -> Dict[str, Any]:
    """
    Answer a user question using Retrieval-Augmented Generation (RAG).

    This function implements the end-to-end RAG flow:
    1) Load the FAISS vector store.
    2) Retrieve the top-k most relevant document chunks for the question.
    3) Construct a prompt containing the question and retrieved context.
    4) Invoke the configured LLM to generate a grounded answer with citations.
    5) Return the answer, source metadata, and latency metrics.
    """
    vs = load_vectorstore()
    retriever = vs.as_retriever(search_kwargs={"k": settings.top_k})

    t0 = time.time()
    docs = retriever.invoke(question)
    retrieval_ms = int((time.time() - t0) * 1000)
    
    llm = get_llm()

    context = format_context(docs)

    t1 = time.time()
    msg = PROMPT.format_messages(question=question, context=context)
    resp = llm.invoke(msg)
    gen_ms = int((time.time() - t1) * 1000)

    # Return sources cleanly
    sources = [{
        "source": d.metadata.get("source"),
        "chunk_id": d.metadata.get("chunk_id"),
        "path": d.metadata.get("path"),
        "score": d.metadata.get("score")  # may be None depending on retriever
    } for d in docs]

    return {
        "answer": resp.content,
        "sources": sources,
        "latency_ms": {"retrieval": retrieval_ms, "generation": gen_ms, "total": retrieval_ms + gen_ms},
    }