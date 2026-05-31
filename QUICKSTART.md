# PDF Insight Agent - Quickstart

Current architecture:

- Backend: FastAPI (Python) in `backend_fastapi/` on `http://localhost:8000`
- Frontend: Vite React in `frontend/` on `http://localhost:5173`

## 1. Prerequisites

- Python 3.9+
- Node.js 18+
- MongoDB Atlas cluster + connection string
- Gemini API key (Google AI Studio)

## 2. Start Backend (FastAPI)

```powershell
cd backend_fastapi
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend_fastapi/.env` (do not commit secrets):

```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

MONGODB_URI=your_mongodb_atlas_connection_string
MONGODB_DATABASE=pdf_insight_agent

GEMINI_API_KEY=your_gemini_api_key
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
GEMINI_CHAT_MODEL=gemini-3.1-flash-lite
GEMINI_OCR_MODEL=gemini-3.1-flash-lite

CHUNK_SIZE=1500
CHUNK_OVERLAP=300
TOP_K_RETRIEVAL=10
SIMILARITY_THRESHOLD=0.3

EMBEDDING_DIMENSION=3072
MAX_PDF_SIZE_MB=100
SUPPORTED_FORMATS=pdf,docx
OCR_ENABLED=True
OCR_MIN_TEXT_CHARS=25
OCR_RENDER_DPI=200
```

Run:

```powershell
python main.py
```

Health:

```text
http://localhost:8000/health
```

## 3. Start Frontend (Vite)

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Frontend default API base URL:

```text
http://localhost:8000/api
```

Override with `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api
```

## 4. Use The App

1. Choose `PDF Insight Agent` in the sidebar.
2. Upload a `.pdf` or `.docx` document.
3. Scanned PDF pages are OCR-processed automatically when embedded text is missing.
4. Use Document Store buttons (summary/key points/questions).
5. Ask questions in chat.

## 5. API Field Names (Important)

Backend expects:

- `session_id` (not `sessionId`)
- `agent_type` (not `agentType`)

Upload multipart form fields:

- `file`
- `session_id`

Chat JSON body:

- `session_id`
- `message`
- `agent_type`
