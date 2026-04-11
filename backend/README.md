# InsureFlow AI Sales Assistant

A real-time AI-powered backend designed to assist human sales agents during live phone calls. Built with FastAPI, WebSockets, and OpenAI, this backend processes live call transcription, provides actionable "next-best-response" suggestions, handles objection detection, and monitors compliance in real-time.

## Tech Stack
* **Framework:** Python, FastAPI, Uvicorn
* **Database:** SQLite (via async SQLAlchemy) - Production ready for PostgreSQL
* **Real-time:** WebSockets for live frontend dashboard updates
* **AI Provider:** OpenAI API (GPT-4o / GPT-4o-mini)
* **Telephony Placeholder:** Twilio Webhook / Media Streams structure

## Features

1. **Call Session Management:** Start, track, and end call sessions.
2. **Real-time AI Ingestion:** Stream transcript chunks into the API; get structured suggestions instantly.
3. **Objection Detection:** Dual-pipeline (fast Rule-based + AI fallback) to detect customer hesitation.
4. **Compliance Monitoring:** Flags risky agent promises (e.g. "I guarantee this...").
5. **Call Stage Detection:** Automatically determines the progress of the call.
6. **Live WebSocket Broadcasting:** Push AI suggestions directly to a dashboard UI.
7. **Post-Call Summary:** Generate a concise manager-style summary upon call completion.

---

## Directory Structure

```text
InsureFlowAi/
├── app/
│   ├── main.py                     # FastAPI entry point
│   ├── api/
│   │   └── routes/                 # FastAPI routers (REST & WS)
│   ├── core/                       # Configs, DB connect, Logging
│   ├── models/                     # SQLAlchemy ORM models
│   ├── schemas/                    # Pydantic validation schemas
│   ├── services/                   # Business logic (AI, Twilio, DB operations)
│   ├── prompts/                    # Advanced system prompts
│   ├── rag/                        # RAG pipeline (loader, chunker, embeddings, retriever)
│   └── utils/                      # Helper & time functions
├── knowledge/
│   ├── raw/                        # Source DOCX files for ingestion
│   ├── processed/                  # Processed text files
│   └── vector_store/               # FAISS index and metadata
├── tests/                          # Basic test suite
├── .env.example                    # Env var template
└── requirements.txt                # Python dependencies
```

---

## Local Setup Instructions

1. **Clone & move into the project dir:**
   ```bash
   cd InsureFlowAi
   ```

2. **Create a virtual environment & install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   **Crucial:** Add your `OPENAI_API_KEY` to the `.env` file. You can leave Twilio credentials blank for local AI testing.

4. **Run the Application:**
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at: http://localhost:8000
   API Docs (Swagger): http://localhost:8000/docs

---

## How to Test the Full Flow Manually

Once the server is running, you can test the pipeline using `curl` or Postman.

### 1. Check API Health
```bash
curl -X GET http://localhost:8000/health
```

### 2. Start a New Call Session
```bash
curl -X POST http://localhost:8000/api/calls/start \
-H "Content-Type: application/json" \
-d '{
  "agent_name": "Sarah Agent",
  "customer_name": "Bob Client",
  "customer_phone": "+123456789"
}'
```
*(Note the returned `id`, you will need it. Let's assume `id: 1`)*

### 3. Connect to WebSocket
Open a WebSocket client (like Postman or a browser console script) to:
`ws://localhost:8000/ws/calls/1`
You will see live updates pushed here during step 4.

### 4. Send Live Transcript Chunks
Simulate the conversation happening:

**Agent:**
```bash
curl -X POST http://localhost:8000/api/transcripts \
-H "Content-Type: application/json" \
-d '{
  "session_id": 1,
  "speaker": "agent",
  "text": "Hi Bob, I can 100% guarantee we will save you money on insurance.",
  "timestamp": "2024-03-20T10:00:00Z"
}'
```
*(Notice the compliance warning triggered by the agent's risky claim!)*

**Customer:**
```bash
curl -X POST http://localhost:8000/api/transcripts \
-H "Content-Type: application/json" \
-d '{
  "session_id": 1,
  "speaker": "customer",
  "text": "I dont know, that sounds a bit too expensive for me right now.",
  "timestamp": "2024-03-20T10:00:15Z"
}'
```
*(Notice the objection detection labeling this as "price" and the AI generating an objection handling suggestion!)*

### 5. Review past suggestions via REST API
```bash
curl -X GET http://localhost:8000/api/calls/1/suggestions
```

### 6. End the Call Session (Triggers Summary)
```bash
curl -X POST http://localhost:8000/api/calls/1/end \
-H "Content-Type: application/json" \
-d ''
```
*(Check the WebSocket client, or the response body, for the generated post-call AI summary)*

---

## RAG (Retrieval-Augmented Generation)

This backend includes a local RAG pipeline for knowledge retrieval during live calls. The RAG system loads DOCX documents, generates embeddings, and retrieves relevant context to improve AI suggestions.

### What the RAG Module Does

- Loads sales and compliance documents from `knowledge/raw/`
- Extracts and cleans text from DOCX files
- Chunks text into semantic segments (default: 1000 chars with 150 overlap)
- Generates OpenAI embeddings for each chunk
- Stores embeddings in a local FAISS vector index
- Retrieves relevant chunks at runtime based on transcript context

### Where to Place DOCX Files

Place your knowledge documents in:
```
knowledge/
  raw/
    sales_guide.docx      # Sales techniques and objection handling
    compliance_guide.docx # Compliance guidelines and policies
```

The system automatically infers document type from filename:
- Files containing "sales" → `doc_type: sales`
- Files containing "compliance" → `doc_type: compliance`
- Others → `doc_type: general`

### Required Environment Variables

Add these to your `.env` file:

```bash
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
RAG_ENABLED=true
RAG_TOP_K=4
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=150
RAG_VECTOR_DIR=knowledge/vector_store
RAG_RAW_DOCS_DIR=knowledge/raw
```

### How to Run Ingestion

Before using RAG, you must ingest your documents:

```bash
python -m app.rag.ingest
```

This will:
1. Scan `knowledge/raw/` for `.docx` files
2. Extract and clean text
3. Create chunks with metadata
4. Generate embeddings via OpenAI
5. Build FAISS index in `knowledge/vector_store/`

### Checking RAG Status

```bash
curl -X GET http://localhost:8000/api/rag/status
```

### RAG Integration Points

The RAG system is used in:

1. **Live Response Suggestions** - Retrieves sales/general chunks to improve suggestions
2. **Objection Handling** - Retrieves sales chunks when handling objections
3. **Compliance Monitoring** - Retrieves compliance chunks when checking for risks
4. **Post-Call Summary** - Optionally retrieves both sales and compliance chunks

### Testing Retrieval Locally

You can test the retrieval directly using the ingest script output. After running ingest, use the API to trigger a call flow:

```bash
# Start a session
curl -X POST http://localhost:8000/api/calls/start \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "Agent", "customer_name": "Customer", "customer_phone": "+123456789"}'

# Send a transcript with context from your documents
curl -X POST http://localhost:8000/api/transcripts \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "speaker": "customer",
    "text": "I am worried about the policy coverage for pre-existing conditions.",
    "timestamp": "2024-03-20T10:00:00Z"
  }'
```

The AI will retrieve relevant chunks from your knowledge base and use them in generating suggestions.

### Example Transcript Query and Retrieved Context

**Query:** "I am worried about the policy coverage for pre-existing conditions."

**Retrieved Context (example):**
```
=== KNOWLEDGE CONTEXT ===

[Source: sales_guide.docx (sales)]
Our comprehensive health insurance plans provide coverage for pre-existing conditions 
after a 12-month waiting period. This applies to all major medical policies.

[Source: compliance_guide.docx (compliance)]
Pre-existing condition disclosures are required by state law. Agents must inform 
customers of any waiting periods before policy issuance.

=== END CONTEXT (2 chunks) ===
```

The model then uses this context to provide accurate, grounded suggestions without hallucinating policy details.

### Troubleshooting

- **No chunks retrieved:** Ensure you've run `python -m app.rag.ingest` first
- **RAG not working:** Check that `RAG_ENABLED=true` in your `.env`
- **Import errors:** Verify all dependencies are installed (`pip install -r requirements.txt`)

---

## CRM Integration (GoHighLevel)

The system optionally integrates with GoHighLevel (GHL) CRM to enrich AI suggestions with customer context.

### What CRM Integration Does

- Looks up contacts by phone number or email during calls
- Provides customer name, tags, notes, pipeline stage, and opportunities
- Includes CRM context in AI prompts for personalized suggestions
- Helps AI avoid repeating questions the customer already answered

### Required Environment Variables

Add to your `.env` file:

```bash
CRM_ENABLED=true
CRM_PROVIDER=gohighlevel
GHL_API_BASE_URL=https://services.leadconnectorhq.com
GHL_PRIVATE_INTEGRATION_TOKEN=your-ghl-token
GHL_LOCATION_ID=your-location-id
GHL_API_VERSION=2021-07-28
```

### How to Get GHL Credentials

1. Go to your GoHighLevel dashboard
2. Navigate to Settings > Integrations > Private Integrations
3. Create a new private integration with contact access permissions
4. Copy the Integration Token
5. Get your Location ID from the URL or dashboard

### Testing CRM Lookup

```bash
# Check CRM status
curl -X GET http://localhost:8000/api/crm/status

# Look up by phone
curl -X GET "http://localhost:8000/api/crm/contact/by-phone?phone=+15551234567"

# Look up by email
curl -X GET "http://localhost:8000/api/crm/contact/by-email?email=john@example.com"
```

### How CRM Context Is Used

When a call session starts, the system looks up the customer by phone:
- If found, CRM data is included in the AI prompt
- AI uses customer name, tags, and notes to personalize suggestions
- Pipeline stage helps AI understand where the lead is in the sales process
- Notes help avoid repeating already-answered questions

Example CRM context in prompt:
```
=== CRM CONTEXT ===
Name: John Doe
Pipeline Stage: Qualified
Tags: warm, interested
Notes: Already compared competitors | Budget: $200/mo
=== END CRM CONTEXT ===
```

### Fallback Behavior

If CRM is disabled, missing token, or contact not found:
- System continues with transcript + RAG + AI only
- No errors are raised to the agent
- Safe defaults are returned

---

## Future Improvements for Production
1. **Database Migration:** Update `DATABASE_URL` in `.env` to a PostgreSQL connection string. Alembic should be set up to manage database migrations.
2. **Twilio Endpoints:** Wire `twilio_service.py` to the live `twilio` Python SDK to accept real webhooks and media streams.
3. **Security:** Require API Keys or Bearer tokens to hit REST endpoints. Validate Twilio's X-Twilio-Signature on the incoming webhook.
