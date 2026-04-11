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
│   └── utils/                      # Helper & time functions
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

## Future Improvements for Production
1. **Database Migration:** Update `DATABASE_URL` in `.env` to a PostgreSQL connection string. Alembic should be set up to manage database migrations.
2. **Twilio Endpoints:** Wire `twilio_service.py` to the live `twilio` Python SDK to accept real webhooks and media streams.
3. **Security:** Require API Keys or Bearer tokens to hit REST endpoints. Validate Twilio's X-Twilio-Signature on the incoming webhook.
