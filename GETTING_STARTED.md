# Getting Started

PDF Insight Agent is a local full-stack app with:

- FastAPI backend for sessions, uploads, document processing, RAG, and chat.
- Vite React frontend for document upload, document actions, and chat UI.
- MongoDB Atlas for sessions, documents, chunks, chat history, and vector search.
- Gemini for embeddings and answer generation.

## Prerequisites

Install these before running the project:

- Python 3.9 or newer
- npm
- MongoDB Atlas cluster
- Google Gemini API key

## Project Layout

```text
PDF Insight Agent/
|-- backend_fastapi/          # FastAPI backend
|-- frontend/                 # Vite React frontend
|-- PROJECT_STRUCTURE.md      # Detailed file map
|-- README.md                 # Main documentation
```

## Backend Setup

Open a terminal in the project root:

```powershell
cd backend_fastapi
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create or update `backend_fastapi/.env`:

```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

MONGODB_URI=your_mongodb_atlas_connection_string
MONGODB_DATABASE=pdf_insight_agent
MONGODB_CHUNKS_COLLECTION=chunks
MONGODB_DOCUMENTS_COLLECTION=documents
MONGODB_SESSIONS_COLLECTION=sessions
MONGODB_CHAT_HISTORY_COLLECTION=chat_history

GEMINI_API_KEY=your_gemini_api_key
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
GEMINI_CHAT_MODEL=gemini-3.1-flash-lite
GEMINI_OCR_MODEL=gemini-3.1-flash-lite

CHUNK_SIZE=1500
CHUNK_OVERLAP=300
TOP_K_RETRIEVAL=10
SIMILARITY_THRESHOLD=0.3

EMBEDDING_DIMENSION=3072
VECTOR_SEARCH_SIMILARITY=cosine

SESSION_EXPIRY_HOURS=24
DOCUMENT_CLEANUP_ENABLED=True

MAX_PDF_SIZE_MB=100
SUPPORTED_FORMATS=pdf,docx
OCR_ENABLED=True
OCR_MIN_TEXT_CHARS=25
OCR_RENDER_DPI=200
```

Start the backend:

```powershell
python main.py
```

Backend URL:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

## Frontend Setup

Open a second terminal in the project root:

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

The frontend uses this default API base URL:

```text
http://localhost:8000/api
```

To override it, create a frontend environment file and set:

```env
VITE_API_URL=http://localhost:8000/api
```

## MongoDB Atlas Notes

The backend stores data in these collections:

```text
sessions
documents
chunks
chat_history
```

Vector search uses embeddings with this dimension:

```text
3072
```

Create a MongoDB Atlas Vector Search index on the chunks collection for the embedding field used by the backend. The backend expects MongoDB Atlas vector search to be available before document chat works correctly.

## Basic Usage

1. Start the backend.
2. Start the frontend.
3. Open `http://localhost:5173`.
4. Select the PDF Insight Agent.
5. Upload a PDF or DOCX document.
6. Use the Document Store buttons:
   - Generate Summary
   - Extract Key Points
   - Generate Questions
7. Ask questions in chat.

The app currently supports up to 5 uploaded documents per active frontend session.

## Useful Commands

Backend:

```powershell
cd backend_fastapi
.\venv\Scripts\activate
python main.py
```

Frontend:

```powershell
cd frontend
npm run dev
```

Frontend production build:

```powershell
cd frontend
npm run build
```

## Common Issues

### Session not found

Create a new session by refreshing the app. If the error remains, clear browser local storage for `localhost:5173` and restart the backend.

### Upload says only PDF/DOCX supported

Use a modern `.pdf` or `.docx` file. Legacy `.doc` files are not supported.

### Scanned PDF text is missing

OCR runs automatically when a PDF page has very little embedded text. Check `OCR_ENABLED=True` and make sure `GEMINI_API_KEY` is valid.

### Chat cannot answer from documents

Check:

- MongoDB connection string is correct.
- Gemini API key is valid.
- Vector Search index exists.
- Uploaded document created chunks successfully.

### Frontend cannot reach backend

Check:

- Backend is running on `http://localhost:8000`.
- Frontend `VITE_API_URL`, if set, points to `http://localhost:8000/api`.
- Browser console/network tab does not show CORS or connection errors.
