import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .config import settings
from .ingest import ingest_all
from .rag import ask, load_vectorstore, format_context
from .evals import run_eval
from .logging_utils import log_event

app = FastAPI(title="Enterprise RAG Copilot", version="1.0.0")

class AskRequest(BaseModel):
    question: str
    user_id: str | None = None

class EvalRequest(BaseModel):
    question: str
    answer: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest")
def ingest():
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="Missing OPENAI_API_KEY")
    result = ingest_all()
    log_event({"type": "ingest", "result": result})
    return result

@app.post("/ask")
def ask_q(req: AskRequest):
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="Missing OPENAI_API_KEY")

    result = ask(req.question)

    log_event({
        "type": "ask",
        "user_id": req.user_id,
        "question": req.question,
        "answer_preview": result["answer"][:200],
        "latency_ms": result["latency_ms"],
        "sources": result["sources"],
    })

    return result

@app.post("/eval")
def eval_answer(req: EvalRequest):
    vs = load_vectorstore()
    retriever = vs.as_retriever(search_kwargs={"k": settings.top_k})
    docs = retriever.get_relevant_documents(req.question)
    context = format_context(docs)

    out = run_eval(req.question, context, req.answer)

    log_event({
        "type": "eval",
        "question": req.question,
        "answer_preview": req.answer[:200],
        "eval": out,
    })

    return {"retrieved_docs": len(docs), **out}
