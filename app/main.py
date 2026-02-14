from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .config import settings
from .ingest import ingest_all
from .rag import ask, load_vectorstore, format_context
from .evals import run_eval
from .logging_utils import log_event


def _validate_vertex():
    if not settings.vertex_project:
        raise HTTPException(status_code=400, detail="Missing VERTEX_PROJECT")


app = FastAPI(
    title="Enterprise RAG Copilot",
    docs_url="/",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


class AskRequest(BaseModel):
    question: str
    user_id: str | None = None


class EvalRequest(BaseModel):
    question: str
    answer: str


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/ingest")
async def ingest():
    _validate_vertex()
    result = ingest_all()
    log_event({"type": "ingest", "result": result})
    return result


@app.post("/ask")
async def ask_q(req: AskRequest):
    _validate_vertex()
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
async def eval_answer(req: EvalRequest):
    vs = load_vectorstore()
    retriever = vs.as_retriever(search_kwargs={"k": settings.top_k})
    docs = retriever.invoke(req.question)
    context = format_context(docs)

    out = run_eval(req.question, context, req.answer)

    log_event({
        "type": "eval",
        "question": req.question,
        "answer_preview": req.answer[:200],
        "eval": out,
    })

    return {"retrieved_docs": len(docs), **out}