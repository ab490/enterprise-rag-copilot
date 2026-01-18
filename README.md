# Enterprise RAG Copilot

A production-style **Retrieval-Augmented Generation (RAG)** system for enterprise
operations, built with **LangChain**, **FAISS**, and **FastAPI**.

The system ingests public, enterprise-style operational documents and enables
**citation-backed question answering**, along with basic **evaluation** and
**latency monitoring**.

This project is designed to resemble how RAG systems are built and evaluated
in real enterprise environments.

---

## Features

- Ingests **PDF, Markdown, TXT, and CSV** documents
- Builds a **persistent FAISS vector index**
- Answers questions with **grounded, citation-backed responses**
- Logs **retrieval and generation latency**
- Includes a basic **evaluation endpoint (LLM-as-judge)**
- Supports **local development and Docker-based deployment**

---

## Data Sources

The `data/raw/` directory contains **publicly available, enterprise-style
operational documents** used to demonstrate realistic Retrieval-Augmented
Generation (RAG) workflows.

No proprietary, private, or personally identifiable data is included.

The current dataset consists of **seven public documents** related to incident
handling and customer support, spanning multiple file formats
(**CSV, PDF, Markdown**). These documents represent different layers of
enterprise operations, including industry standards, organizational policies,
and hands-on operational runbooks.

### Included Files

- **`customer_support_tickets.csv`**  
  An anonymized dataset of customer support tickets containing semi-structured
  metadata and free-text issue descriptions. This file simulates real-world
  enterprise support data commonly used for retrieval over operational issues
  and recurring customer problems.

- **`incident_handling_nist.pdf`**  
  The NIST SP 800-61 Computer Security Incident Handling Guide, an
  industry-standard reference defining best practices and lifecycle phases
  for incident response.

- **`incident_management_guide_enisa.pdf`**  
  A public incident management guide published by ENISA, outlining structured
  approaches to incident classification, coordination, and resolution.

- **`incident_management_guide_google.pdf`**  
  A publicly available incident management guide based on Site Reliability
  Engineering (SRE) practices, describing roles, communication models, and
  response workflows during incidents.

- **`incident_response_policy_gtel.pdf`**  
  A high-level incident response policy document defining organizational
  responsibilities, escalation paths, and governance for incident handling.

- **`incident_response_plan_hack23ab.md`**  
  A process-oriented incident response plan describing how policies are
  operationalized across preparation, detection, containment, recovery, and
  post-incident review phases.

- **`incident_response_runbook.md`**  
  A step-by-step operational runbook providing concrete actions to be taken
  during active incidents, representing hands-on guidance used by on-call and
  operations teams.

These documents are intentionally diverse in **format** (CSV, PDF, Markdown)
and **abstraction level** (policy, process, runbook) to reflect real enterprise
knowledge bases and to stress-test document ingestion, retrieval accuracy,
citation grounding, and end-to-end RAG behavior.

> Additional public or synthetic documents can be added to `data/raw/` to further
> expand the knowledge base and evaluate the system’s behavior under different
> document distributions.

---

## Project Structure

```text
enterprise-rag-copilot/
├── app/
│   ├── main.py            # FastAPI entrypoint
│   ├── config.py          # App configuration (Pydantic + env vars)
│   ├── ingest.py          # Document ingestion + indexing
│   ├── rag.py             # Retrieval + generation logic
│   ├── evals.py           # LLM-based evaluation utilities
│   └── logging_utils.py   # Structured logging helpers
├── data/
│   ├── raw/               # Public raw documents
│   ├── index/             # FAISS index
│   └── logs/              # JSONL logs
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```
---

## Setup

You can run the service in **one of two ways**:

- **Option A: Docker**
- **Option B: Virtual environment**


## A. Docker


### 1. Configure environment variables
```bash
cp .env.example .env
```

Edit .env and set OPENAI_API_KEY
```bash
OPENAI_API_KEY=your_api_key_here
```

### 2. Build and run with Docker Compose
```bash
docker compose up --build
```

The service will be available at ```http://localhost:8000```

## B. Virtual environment

### 1. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
```

Edit .env and set OPENAI_API_KEY
```bash
OPENAI_API_KEY=your_api_key_here
```

### 4. Start the API
```bash
uvicorn app.main:app --reload
```

The service will be available at ```http://localhost:8000```

The following commands work for both Docker and Virtualenv once the service is running:

## Ingest Documents
Once the API is running, ingest all documents in ```data/raw/``:
```bash
curl -X POST http://localhost:8000/ingest
```
This builds or updates the FAISS vector index.

## Ask a Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the phases of incident handling?"}'
```
The response includes:
- A grounded answer
- Source citations
- Latency metrics

## Evaluate an Answer
```bash
curl -X POST http://localhost:8000/eval \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the phases of incident handling?", "answer":"..."}'
```
This endpoint uses an LLM-as-judge to estimate answer faithfulness and citation
behavior.


## Notes on Evaluation and Limitations

- LLM outputs are not deterministic; evaluation scores are approximate.

- The evaluation endpoint prioritizes faithfulness and citation grounding
rather than exact answer matching.

- This project focuses on system design and workflow realism, not model
fine-tuning or benchmarking.

### Example Use Cases

- What are the phases of incident response according to NIST?

- What should happen after a P0 incident is resolved?

- What responsibilities are defined in the incident response policy?

- What types of issues appear most frequently in customer support tickets?


This repository demonstrates how production-style RAG systems are built in
practice, including:

- Multi-format document ingestion
- Vector-based retrieval
- Citation-grounded generation
- Basic evaluation and observability