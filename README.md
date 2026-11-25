# 🫐 ClueBerry

> **MCP-powered payment evidence investigation platform**  
> *wHACKiest 2026 — Track 1: Make MCP Matter*

---

## What is ClueBerry?

ClueBerry is an AI-powered document investigation assistant that helps individuals and small businesses verify payment evidence, detect fraud, and resolve financial disputes — using the **Model Context Protocol (MCP)** to retrieve, match, and cite real evidence from uploaded documents.

> **Demo scenario:** A vendor claims you haven't paid. You upload the invoice, your payment receipt, and the payment reminder. ClueBerry investigates and tells you — with cited evidence — whether you've already paid.

---

## Architecture

```
React + Vite (Frontend)
        │
        ▼
FastAPI Backend (Orchestrator)
        │
        ├──► Amazon S3 (Document Storage)
        ├──► Amazon Textract / PyMuPDF (Extraction)
        ├──► Amazon Bedrock (AI Reasoning)
        └──► MCP Server (Evidence Tools)
                │
                ├── search_evidence(query, doc_type, invoice_no)
                ├── read_source(doc_id, evidence_id)
                └── find_payment_match(invoice_no, vendor, amount)
                        │
                        ▼
                 DynamoDB (TrustTraceEvidence)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + TypeScript |
| Styling | Tailwind CSS |
| Backend | Python + FastAPI |
| MCP | Python MCP SDK |
| AI Reasoning | Amazon Bedrock (Claude) |
| Storage | Amazon S3 |
| Database | Amazon DynamoDB |
| OCR | Amazon Textract |
| PDF Extraction | PyMuPDF |
| Voice (optional) | ElevenLabs API |

---

## Quickstart

### Prerequisites
- Node.js 18+
- Python 3.11+
- AWS account with Bedrock access

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Fill in your AWS credentials
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`  
Backend API at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`

---

## MCP Integration

ClueBerry's core value is **evidence-grounded investigation**, not AI guesswork. The MCP server exposes three tools:

### `search_evidence`
Queries DynamoDB for structured evidence matching the user's investigation question.

### `read_source`  
Retrieves the original extracted text from a specific document, with source location.

### `find_payment_match`
Runs deterministic field-level matching between invoice records and payment receipts, returning match status and contradiction flags.

The AI **cannot fabricate** evidence — every claim in the report must resolve to a real `evidence_id` returned by an MCP tool call.

---

## Demo Flow

1. Upload `invoice_INV-1042.pdf`, `payment_receipt.pdf`, `reminder.eml`
2. Ask: *"A vendor is asking me to pay invoice INV-1042 again. Did I already pay it?"*
3. Watch ClueBerry call `search_evidence` → `find_payment_match` → `read_source`
4. View cited investigation report with timeline and draft reply

---

## Folder Structure

```
clueberry/
├── frontend/          # React + Vite dashboard
├── backend/           # FastAPI + MCP server
│   ├── app/
│   │   ├── api/       # REST endpoints
│   │   ├── services/  # Business logic
│   │   ├── mcp_server/# MCP tools
│   │   ├── models/    # Pydantic schemas
│   │   └── prompts/   # Bedrock prompts
│   └── requirements.txt
├── sample_data/       # Synthetic test documents
└── aws/               # Lambda handler
```

---

## Track Alignment — Make MCP Matter

ClueBerry demonstrates MCP as a **trust layer**, not a novelty:

- MCP tools are called with real parameters derived from user questions
- Retrieved evidence IDs are validated against the AI's citations
- Judges can see every tool call and its result in the investigation panel
- The matching engine is **deterministic Python**, not LLM guesswork

---

## Sponsor Integration

- **AWS**: S3 (storage), DynamoDB (evidence DB), Bedrock (reasoning), Textract (OCR)
- **ElevenLabs**: Optional spoken investigation report via `/report/speak` endpoint

---

*Built for wHACKiest 2026 — Team [Your Team Name]*
