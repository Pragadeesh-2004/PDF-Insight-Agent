# PDF Insight Agent - AI-Powered Document Analysis System

A full-stack, modern AI-powered document analysis application that leverages Retrieval-Augmented Generation (RAG), MongoDB Atlas Vector Search, and Google Gemini 2.5 Flash API to provide intelligent document insights.

## 🚀 Features

### Core Capabilities

- **Document Upload**: Support for PDF and Word (.docx) documents
- **Text Extraction**: Automatic extraction and processing of document content
- **Smart Chunking**: Intelligent text segmentation for optimal processing
- **Embeddings Generation**: AI-powered embedding generation using Google Gemini
- **Vector Search**: MongoDB Atlas Vector Search for semantic similarity
- **RAG System**: Hybrid RAG + Direct LLM approach for intelligent responses
- **Document Analysis**:
  - Generate comprehensive summaries
  - Extract key points
  - Generate important questions/viva questions
- **Conversational AI**: Chat with your documents or use general knowledge

### UI/UX Features

- Modern glassmorphism design with blue gradient theme
- Responsive layout (mobile, tablet, desktop)
- Real-time typing animations
- Smooth transitions and interactions
- Session-based temporary storage (no authentication required)
- Automatic data cleanup with TTL indexes

## 🛠️ Tech Stack

### Frontend

- **Framework**: React.js 18+
- **Styling**: Tailwind CSS + custom animations
- **Icons**: Lucide React
- **Build Tool**: Vite
- **HTTP Client**: Axios

### Backend

- **Runtime**: Node.js 18+
- **Framework**: Express.js
- **Database**: MongoDB Atlas
- **Vector Search**: MongoDB Atlas Vector Search
- **LLM**: Google Gemini 2.5 Flash API
- **Document Processing**:
  - `pdf-parse` for PDF extraction
  - `mammoth` for Word document processing
- **File Upload**: Multer

### Deployment

- **Backend**: Render
- **Frontend**: Render/Vercel
- **Database**: MongoDB Atlas

## 📋 Project Structure

```
pdf-insight-agent/
├── backend/
│   ├── routes/
│   │   ├── upload.js          # Document upload routes
│   │   ├── chat.js            # Chat message routes
│   │   └── session.js         # Session management
│   ├── controllers/
│   │   ├── uploadController.js
│   │   ├── chatController.js
│   │   └── sessionController.js
│   ├── services/
│   │   ├── pdfService.js      # PDF text extraction
│   │   ├── docxService.js     # Word document extraction
│   │   ├── chunkingService.js # Text chunking logic
│   │   ├── embeddingService.js # Embedding generation
│   │   ├── vectorSearchService.js # Vector similarity search
│   │   ├── geminiService.js   # Gemini API integration
│   │   └── ragService.js      # RAG workflow
│   ├── utils/
│   │   └── database.js        # MongoDB connection & indexes
│   ├── middleware/
│   ├── models/
│   ├── .env.example           # Environment template
│   ├── server.js              # Express server
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── UploadModal.jsx
│   │   │   └── DocumentPanel.jsx
│   │   ├── pages/
│   │   ├── utils/
│   │   │   ├── api.js         # API client
│   │   │   └── constants.js   # Constants
│   │   ├── styles/
│   │   │   └── global.css     # Tailwind + animations
│   │   ├── App.jsx            # Main component
│   │   └── main.jsx           # Entry point
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── package.json
├── package.json               # Root package
├── .gitignore
└── README.md
```

## 📊 Database Schema

### Collections

#### `sessions`

```javascript
{
  sessionId: String (unique),
  agentType: String,
  createdAt: Date (TTL index),
  updatedAt: Date
}
```

#### `documents`

```javascript
{
  documentId: String (UUID),
  sessionId: String,
  fileName: String,
  fileType: String (PDF/DOCX),
  fileSize: Number,
  uploadedAt: Date,
  chunksCount: Number,
  metadata: Object,
  createdAt: Date (TTL index)
}
```

#### `chunks`

```javascript
{
  chunkId: String,
  documentId: String,
  sessionId: String,
  text: String,
  chunkIndex: Number,
  createdAt: Date (TTL index)
}
```

#### `embeddings`

```javascript
{
  embeddingId: String (UUID),
  chunkId: String,
  documentId: String,
  sessionId: String,
  vector: Array<Number> (embedding vector),
  createdAt: Date (TTL index)
}
```

#### `chatHistory`

```javascript
{
  messageId: String (UUID),
  sessionId: String,
  parentMessageId: String,
  role: String (user/assistant),
  content: String,
  agentType: String,
  usedRAG: Boolean,
  source: String,
  relevantDocuments: Array<String>,
  createdAt: Date (TTL index)
}
```

## 🔌 API Endpoints

### Upload Routes

- `POST /api/upload/document` - Upload PDF or Word document
- `POST /api/upload/summary` - Generate document summary
- `POST /api/upload/key-points` - Extract key points
- `POST /api/upload/important-questions` - Generate questions

### Chat Routes

- `POST /api/chat/message` - Send chat message
- `POST /api/chat/update-agent` - Switch between agents

### Session Routes

- `DELETE /api/session/clear` - Clear session data
- `GET /api/session/info` - Get session information

## 🎯 RAG Workflow

### Document Upload Flow

1. User uploads PDF/Word document
2. Extract text from document
3. Split text into overlapping chunks (2000 chars, 300 char overlap)
4. Generate embeddings for each chunk using Gemini API
5. Store chunks and embeddings in MongoDB

### Question Answering Flow

1. User asks question
2. Generate embedding for question
3. Perform vector similarity search (threshold: 0.7)
4. **Decision Logic**:
   - **If similarity ≥ 0.7**: Use RAG
     - Retrieve relevant chunks
     - Send chunks + question to Gemini
     - Generate document-based answer
   - **If similarity < 0.7**: Use Direct LLM
     - Send question directly to Gemini
     - Generate general knowledge answer

### Hybrid Approach Benefits

- **Document Questions**: Accurate, contextual answers from source material
- **General Questions**: Leverage Gemini's general knowledge
- **Cost Optimization**: Avoid unnecessary API calls
- **Relevance Scoring**: Only use RAG when confidence is high

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- MongoDB Atlas account
- Google Gemini API key

### Installation

1. **Clone repository**

```bash
cd "PDF Insight Agent"
```

2. **Install dependencies**

```bash
npm run install-all
```

3. **Setup Environment**

Create `.env` in `backend/` directory:

```env
PORT=5000
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/pdf_insight_agent
GEMINI_API_KEY=your_gemini_2_0_api_key
NODE_ENV=development
CORS_ORIGIN=http://localhost:3000
SESSION_TTL=3600000
EMBEDDING_MODEL=text-embedding-005
VECTOR_SEARCH_THRESHOLD=0.7
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

4. **Get Gemini API Key**
   - Visit [Google AI Studio](https://aistudio.google.com)
   - Create new API key
   - Add to `.env`

5. **Setup MongoDB Atlas**
   - Create MongoDB Atlas cluster
   - Create database `pdf_insight_agent`
   - Get connection string
   - Add to `.env`

### Running Locally

```bash
# Development mode (both frontend and backend)
npm run dev

# Backend only
cd backend && npm run dev

# Frontend only
cd frontend && npm run dev
```

Access application at `http://localhost:3000`

## 📦 Deployment to Render

### Backend Deployment

1. **Create Render Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Set Build Command: `npm install && cd backend && npm install`
   - Set Start Command: `npm start`

2. **Add Environment Variables**
   - Click "Environment"
   - Add all variables from `.env`:
     - `MONGODB_URI`
     - `GEMINI_API_KEY`
     - `PORT=5000`
     - etc.

3. **Deploy**
   - Click "Create Web Service"

### Frontend Deployment

1. **Build Frontend**

```bash
cd frontend
npm run build
```

2. **Deploy to Render (Static Site)**
   - Create new Static Site on Render
   - Connect GitHub repository
   - Build Command: `cd frontend && npm run build`
   - Publish Directory: `frontend/dist`

### Environment Variables on Render

```
MONGODB_URI: mongodb+srv://...
GEMINI_API_KEY: your_key
CORS_ORIGIN: https://your-frontend-domain.com
NODE_ENV: production
```

## 🔐 Security Considerations

1. **Session Management**
   - No authentication required
   - Temporary sessions only
   - TTL indexes auto-cleanup data
   - Sessions cleared on browser close

2. **API Key Protection**
   - Never commit `.env` files
   - Use environment variables
   - Rotate keys regularly

3. **File Upload**
   - File size limit: 10MB
   - Allowed types: PDF, DOCX only
   - Virus scanning recommended for production

4. **Database Security**
   - Use MongoDB Atlas IP whitelist
   - Enable authentication
   - Use connection strings with credentials

## 🎨 Customization

### Change Color Scheme

Edit `frontend/tailwind.config.js`:

```javascript
extend: {
  colors: {
    primary: '#YOUR_COLOR',
    secondary: '#YOUR_COLOR',
  }
}
```

### Adjust Chunk Size

Edit `backend/services/chunkingService.js`:

```javascript
const CHUNK_SIZE = 1000; // Adjust
const CHUNK_OVERLAP = 200; // Adjust
```

### Change Embedding Model

Edit `backend/services/embeddingService.js`:

```javascript
const model = client.getGenerativeModel({ model: "text-embedding-005" });
```

### Modify RAG Threshold

Edit `.env`:

```env
VECTOR_SEARCH_THRESHOLD=0.7
```

## 📊 Performance Optimization

1. **Database**
   - Indexes on frequently queried fields
   - Connection pooling
   - TTL indexes for auto-cleanup

2. **API**
   - Response compression
   - CORS optimization
   - Request validation

3. **Frontend**
   - Code splitting
   - Lazy loading
   - Smooth animations

## 🐛 Troubleshooting

### MongoDB Connection Issues

- Check connection string format
- Verify IP whitelist on MongoDB Atlas
- Ensure database exists

### Gemini API Errors

- Verify API key is valid
- Check API quota
- Review rate limits

### File Upload Issues

- Check file format (PDF/DOCX)
- Verify file size < 10MB
- Check CORS settings

### Frontend Not Loading

- Verify backend is running
- Check CORS_ORIGIN matches frontend URL
- Clear browser cache

## 📝 API Request Examples

### Upload Document

```bash
curl -X POST http://localhost:5000/api/upload/document \
  -F "file=@document.pdf" \
  -F "sessionId=session-id" \
  -F "agentType=PDF_INSIGHT_AGENT"
```

### Send Chat Message

```bash
curl -X POST http://localhost:5000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "session-id",
    "message": "Summarize the document",
    "agentType": "PDF_INSIGHT_AGENT"
  }'
```

### Generate Summary

```bash
curl -X POST http://localhost:5000/api/upload/summary \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "session-id",
    "documentId": "doc-id"
  }'
```

## 🤝 Contributing

Contributions welcome! Please follow:

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Submit pull request

## 📄 License

MIT License - See LICENSE file

## 📧 Support

For issues and questions:

- GitHub Issues
- Email: support@example.com

## 🙏 Acknowledgments

- Google Gemini Team
- MongoDB Atlas
- React.js Community
- Tailwind CSS

---

**Built with ❤️ using React, Node.js, MongoDB Atlas, and Google Gemini 2.0 API**
