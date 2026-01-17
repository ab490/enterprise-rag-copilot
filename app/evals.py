from typing import Dict, Any, List
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .config import settings

JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a strict evaluator for RAG answers."),
    ("human",
     "Question: {question}\n\nContext:\n{context}\n\nAnswer:\n{answer}\n\n"
     "Score faithfulness 0-5 where 5 means all claims are supported by context.\n"
     "Return JSON with keys: faithfulness_score, issues (list).")
])

def extract_citations(answer: str) -> List[str]:
    # matches [file:chunk_id]
    return re.findall(r"\[[^\[\]]+?:[^\[\]]+?\]", answer)

def run_eval(question: str, context: str, answer: str) -> Dict[str, Any]:
    llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)
    msg = JUDGE_PROMPT.format_messages(question=question, context=context, answer=answer)
    resp = llm.invoke(msg)

    citations = extract_citations(answer)
    return {
        "judge_raw": resp.content,
        "citations_found": citations,
        "citation_count": len(citations),
    }
