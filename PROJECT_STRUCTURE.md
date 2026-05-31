# PDF Insight Agent - Project Structure

This document reflects the current repository layout for the PDF Insight Agent project.

```text
PDF Insight Agent/
|-- backend_fastapi/                         # FastAPI backend application
|   |-- app/
|   |   |-- api/
|   |   |   |-- routes/
|   |   |   |   |-- chat.py                  # Chat and RAG query endpoints
|   |   |   |   |-- documents.py             # Document listing, lookup, and deletion endpoints
|   |   |   |   |-- session.py               # Session lifecycle endpoints
|   |   |   |   |-- upload.py                # PDF/DOCX upload and document action endpoints
|   |   |   |   `-- __init__.py
|   |   |   `-- __init__.py
|   |   |-- core/
|   |   |   |-- config.py                    # Environment-backed application settings
|   |   |   |-- database.py                  # MongoDB connection and index setup
|   |   |   `-- __init__.py
|   |   |-- models/
|   |   |   |-- schemas.py                   # Pydantic request/response models
|   |   |   `-- __init__.py
|   |   |-- services/
|   |   |   |-- chunking_service.py          # LangChain text chunking
|   |   |   |-- embedding_service.py         # Gemini embedding generation
|   |   |   |-- pdf_processor.py             # PDF and DOCX text extraction
|   |   |   |-- rag_service.py               # RAG orchestration and answer generation
|   |   |   |-- vector_store.py              # MongoDB vector storage/search helpers
|   |   |   `-- __init__.py
|   |   `-- __init__.py
|   |-- .env                                 # Local backend secrets/config, do not commit
|   |-- .env.example                         # Environment variable template
|   |-- .gitignore                           # Backend ignore rules
|   |-- main.py                              # FastAPI app entrypoint and router registration
|   |-- README.md                            # Backend documentation
|   |-- requirements.txt                     # Python dependencies
|   |-- setup.bat                            # Windows backend setup script
|   `-- setup.sh                             # Unix backend setup script
|
|-- frontend/                                # Vite React frontend application
|   |-- src/
|   |   |-- components/
|   |   |   |-- ChatInterface.jsx            # Chat window and message input
|   |   |   |-- ConfirmDialog.jsx            # Confirmation and success dialogs
|   |   |   |-- DocumentPanel.jsx            # Document store and document action buttons
|   |   |   |-- MessageBubble.jsx            # Chat message rendering
|   |   |   |-- Sidebar.jsx                  # Agent/sidebar navigation
|   |   |   `-- UploadModal.jsx              # PDF/DOCX upload modal
|   |   |-- styles/
|   |   |   `-- global.css                   # Tailwind and global styles
|   |   |-- utils/
|   |   |   |-- api.js                       # Axios client and API helper functions
|   |   |   `-- constants.js                 # API endpoints, agents, and constants
|   |   |-- App.jsx                          # Main frontend state and layout
|   |   `-- main.jsx                         # React app bootstrap
|   |-- index.html                           # Vite HTML entrypoint
|   |-- package-lock.json                    # Frontend dependency lockfile
|   |-- package.json                         # Frontend scripts and dependencies
|   |-- postcss.config.cjs                   # PostCSS configuration
|   |-- tailwind.config.js                   # Tailwind configuration
|   |-- tsconfig.json                        # TypeScript/Vite tooling config
|   |-- tsconfig.node.json                   # Node-side TypeScript tooling config
|   `-- vite.config.js                       # Vite configuration
|
|-- .gitignore                               # Root ignore rules
|-- GETTING_STARTED.md                       # Getting started guide
|-- Procfile                                 # Deployment process definition
|-- PROJECT_STRUCTURE.md                     # This file
|-- QUICKSTART.md                            # Quickstart guide
|-- RAG_IMPLEMENTATION.md                    # RAG implementation notes
`-- README.md                                # Main project documentation
```

## Runtime Flow

```text
Browser
  -> frontend/src/App.jsx
  -> frontend/src/utils/api.js
  -> FastAPI routes in backend_fastapi/app/api/routes/
  -> Services in backend_fastapi/app/services/
  -> MongoDB Atlas collections and vector search
  -> Gemini API for embeddings and chat generation
```

## Main Backend Routes

```text
POST   /api/session/create                   # Create session
GET    /api/session/{session_id}             # Get session info
DELETE /api/session/{session_id}             # Delete session and all related data
POST   /api/session/{session_id}/clear-documents

POST   /api/upload/document                  # Upload and process PDF/DOCX
POST   /api/upload/summary                   # Generate document summary
POST   /api/upload/key-points                # Extract document key points
POST   /api/upload/important-questions       # Generate important questions

POST   /api/chat/message                     # Send chat/RAG query
GET    /api/chat/history/{session_id}        # Get chat history

GET    /api/documents/{session_id}           # List session documents
GET    /api/documents/{session_id}/{document_id}
DELETE /api/documents/{session_id}/{document_id}
```

## Generated Or Local-Only Folders

These folders are not part of the source structure and should normally stay out of version control:

```text
node_modules/
frontend/node_modules/
frontend/dist/
backend_fastapi/venv/
backend_fastapi/__pycache__/
backend_fastapi/app/**/__pycache__/
```

