# PDF Insight Agent - RAG Implementation Guide

## What is RAG?

**RAG** = **Retrieval-Augmented Generation**

It's an AI technique that combines:

1. **Retrieval**: Finding relevant documents/chunks
2. **Augmentation**: Adding context to the query
3. **Generation**: Creating an answer using LLM

### Why RAG?

- **Accuracy**: Answers based on actual document content
- **Traceability**: Can point to source material
- **Cost-effective**: Reduces hallucinations
- **Up-to-date**: Uses your documents as source of truth

## How PDF Insight Agent Uses RAG

### Hybrid Approach: RAG + Gemini

```
User Question
    ↓
Generate Embedding (Gemini text-embedding-001)
    ↓
Vector Similarity Search (MongoDB Atlas)
    ↓
    ┌──────────────────────────────┐
    │ Similarity Score? (threshold) │
    └──────────────────────────────┘
           ↙                  ↘
        HIGH                 LOW
        (>0.3)               (<0.3)
        ↓                    ↓
      USE RAG            USE GEMINI
      ↓                    ↓
   Retrieve Top 10   No Context
   Chunks + Context
      ↓                    ↓
   Gemini + Context    Gemini Only
      ↓                    ↓
    ANSWER              ANSWER
```

## Architecture

### System Components

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│  • Upload Modal                                          │
│  • Chat Interface                                        │
│  • Document Panel                                        │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Routes: /upload, /chat, /session, /documents     │ │
│  │  Services:                                         │ │
│  │  ├─ PDF Extraction (PyMuPDF)                      │ │
│  │  ├─ OCR Processing (Gemini Vision API)           │ │
│  │  ├─ Text Chunking (LangChain)                    │ │
│  │  ├─ Embedding Generation (Gemini Embeddings)     │ │
│  │  ├─ Vector Search (MongoDB Atlas)                │ │
│  │  ├─ Context Expansion                            │ │
│  │  └─ RAG Orchestration (Gemini API)               │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                                   ↓
┌──────────────────┐          ┌──────────────────────┐
│   MongoDB Atlas  │          │  Google Gemini APIs  │
│                  │          │                      │
│ Collections:     │          │ • Embeddings         │
│ • sessions       │          │ • Text Generation    │
│ • documents      │          │ • OCR/Vision API     │
│ • chunks         │          │ • Summarization      │
│ • chat_history   │          │ • QA/Chat            │
│                  │          │                      │
│ Vector Search    │          │                      │
│ TTL Cleanup      │          │                      │
└──────────────────┘          └──────────────────────┘
```

## Workflow Details

### 1. Document Upload Flow

```
User uploads PDF
        ↓
Validate file (type, size)
        ↓
Extract text with PyMuPDF
├─ Standard text extraction
├─ Page-by-page processing
└─ Preserve page metadata
        ↓
Check if OCR needed?
├─ If embedded text < OCR_MIN_TEXT_CHARS (25 chars)
├─ Trigger Gemini Vision API for OCR
└─ Merge OCR text with extracted text
        ↓
Split into chunks (LangChain)
├─ RecursiveCharacterTextSplitter
├─ Chunk size: 1500 chars
├─ Overlap: 300 chars
└─ Results in ~20-50 chunks per document
        ↓
Generate embeddings (Gemini)
├─ Model: gemini-embedding-001
├─ Dimensions: 3072 per chunk
├─ Includes page metadata
└─ Results in ~20-50 embeddings (3072-dim vectors)
        ↓
Store in MongoDB Atlas
├─ Save document metadata
├─ Save chunks with text and page numbers
├─ Save 3072-dim embeddings with vectors
└─ Create vector search index
        ↓
Ready for Q&A!
```

### 2. Question Processing Flow

```
User asks: "What is the main topic?"
        ↓
Generate question embedding (Gemini)
├─ Model: gemini-embedding-001
├─ Returns 3072-dimensional vector
└─ Used for similarity matching
        ↓
Vector Similarity Search (MongoDB Atlas)
├─ Compare question vector (3072-dim)
├─ With all document vectors (3072-dim)
├─ Calculate cosine similarity
└─ Score: 0.0 to 1.0
        ↓
Sort by similarity score
        ↓
Filter by threshold (default 0.3)
        ↓
    Did we find matches?
       /              \
     YES               NO
      ↓                ↓
   USE RAG        DIRECT LLM
      ↓                ↓
   Get Top 10      No Context
   Chunks
      ↓
   Expand Context
   ├─ Get prev/current/next chunks
   ├─ Mark primary chunks
   └─ Merge duplicates
      ↓
   Combine context
   "[PRIMARY CHUNK]
    The study examined...

    [CONTEXT CHUNK]
    Previous research...

    User question: ..."
      ↓
   Send to Gemini
   (with system prompt for accuracy)
      ↓
   Generate answer
      ↓
   Return answer + sources
```

### 3. Data Storage

```
Session Created
├─ sessionId: "session-12345"
└─ TTL: 24 hours (SESSION_EXPIRY_HOURS=24)

Document Uploaded
├─ documentId: "uuid"
├─ sessionId: "session-12345"
├─ filename: "research.pdf"
├─ page_count: 25
├─ chunk_count: 25
└─ TTL: 24 hours (auto-delete via session expiry)

Chunks Stored
├─ _id: ObjectId
├─ documentId: "uuid"
├─ sessionId: "session-12345"
├─ text: "The document contains..."
├─ chunkIndex: 0
├─ pageNumber: 1
└─ TTL: 24 hours (auto-delete via session expiry)

Embeddings Stored (with Chunks)
├─ _id: ObjectId
├─ documentId: "uuid"
├─ sessionId: "session-12345"
├─ chunkIndex: 0
├─ text: "The document contains..."
├─ embedding: [0.123, -0.456, 0.789, ...] (3072-dim vector)
└─ TTL: 24 hours (auto-delete via session expiry)

Chat History Stored
├─ _id: ObjectId
├─ sessionId: "session-12345"
├─ role: "user" or "assistant"
├─ content: "message text"
├─ timestamp: Date
└─ TTL: 24 hours (auto-delete via session expiry)
```

## Vector Search Deep Dive

### What is Vector Similarity?

Each text chunk is converted to a 3072-dimensional vector:

```
"The sky is blue" → [-0.12, 0.45, 0.89, -0.23, ..., 0.34]  (3072 dimensions)
```

When you ask a question, it's also converted to a 3072-dimensional vector:

```
"What color is the sky?" → [0.08, 0.42, 0.91, -0.19, ..., 0.29]  (3072 dimensions)
```

**Similarity is calculated** using cosine similarity:

```
Similarity = (Vector1 · Vector2) / (|Vector1| × |Vector2|)
Result: 0.0 to 1.0
```

### Similarity Scores Explained

```
Score 0.9+ : Highly relevant
  Example: "sky" vs "sky color"

Score 0.7-0.9 : Very relevant
  Example: "sky" vs "weather prediction"

Score 0.5-0.7 : Moderately related
  Example: "sky" vs "outdoor activities"

Score 0.3-0.5 : Weakly related
  Example: "sky" vs "atmosphere science"

Score <0.3 : Not related
  Example: "sky" vs "cooking recipe"
```

### Default Threshold: 0.3

- **Why 0.3?** Balances precision and recall for broader document coverage
- **Adjustments**:
  - ↑ Higher (0.5+): Stricter, fewer results but higher quality
  - ↓ Lower (0.1-0.3): Broader, more coverage with potential noise
  - **Recommendation**: Keep at 0.3 for general queries

### MongoDB Atlas Vector Search Configuration

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "similarity": "cosine",
      "dimensions": 3072
    },
    {
      "type": "filter",
      "path": "sessionId"
    }
  ]
}
```

## Embedding Model

### gemini-embedding-001 (Recommended)

- **Dimensions**: 3072
- **Cost**: Free tier available (generous quota)
- **Speed**: ~100-200ms per chunk
- **Quality**: High semantic understanding
- **Optimization**: Optimized for semantic search across documents
- **Update frequency**: Regularly improved by Google

### Example Embedding Usage

```python
from app.services.embedding_service import EmbeddingService

text = "Python is a programming language"
embedding = await EmbeddingService.generate_embedding(text)
# Result: [0.123, -0.456, 0.789, ..., -0.234]  (3072 numbers)

print(len(embedding))  # 3072
```

## Chunking Strategy

### Why Chunk?

- **Token Limits**: Gemini has max input tokens
- **Context Windows**: Smaller chunks, more precise retrieval
- **Efficiency**: Process only relevant parts
- **Scalability**: Handle large documents
- **Better Indexing**: Optimize vector search performance

### Chunking Method: RecursiveCharacterTextSplitter (LangChain)

```python
from app.services.chunking_service import ChunkingService

text = "The document contains information about AI... machine learning... neural networks..."

chunks = await ChunkingService.chunk_text(
    text,
    chunk_size=1500,      # Default characters per chunk
    chunk_overlap=300     # Default overlap between chunks
)
```

### Configuration

```env
CHUNK_SIZE=1500           # Characters per chunk
CHUNK_OVERLAP=300         # Characters that overlap between chunks
```

### Example Chunking

```
Full Text: "The document contains information about AI... machine learning... neural networks... deep learning..."

Chunk 1: [chars 0-1500]
         "The document contains information about AI... machine learning..."
         ↑ Start
                                                                    ↑ End

Chunk 2: [chars 1200-2700]  (overlaps with Chunk 1 by 300 chars)
         "...machine learning... neural networks... deep learning..."
         ↑ Overlap area ───────↑
```

Chunk 2: "machine learning... neural networks..." (2000 chars)
↑ Start (overlaps 300 chars from chunk 1)
↑ End

Chunk 3: "neural networks..." (remaining)

````

**Advantages**:

- Preserves sentence boundaries better
- Language-agnostic
- Consistent chunk sizes

#### 2. Word-Based

```javascript
chunkText(text, (chunkSize = 1000), (overlap = 200));
````

**Advantages**:

- Exact control over word count
- Good for non-continuous text

### Overlap Strategy

**Why overlap?**

- Preserves context across chunks
- Ensures important sentences don't get cut off
- Improves retrieval relevance

```
Without Overlap:
Chunk 1: "...........|"
Chunk 2:           "|.........."

With Overlap:
Chunk 1: "...........|---overlap---|"
Chunk 2:           "|---overlap---|.........."

When searching for "X in overlap",
both chunks are found!
```

## RAG Prompting

### System Prompt

```
You are a helpful AI assistant that answers questions based on provided documents.

When answering:
1. Only use information from the provided context
2. If the answer is not in the context, say "Not found in document"
3. Always cite which part of the document you're referring to
4. Be accurate and specific
5. If there are multiple relevant sections, consider all of them
```

### Example RAG Prompt Construction

```javascript
const ragPrompt = `
Here is relevant information from the document:

---START CONTEXT---
${relevantChunks.map((c) => c.text).join("\n---\n")}
---END CONTEXT---

Based on the above context, answer the following question:

Question: ${userQuestion}

Answer:
`;

// Send to Gemini
const answer = await gemini.generateContent(ragPrompt);
```

## Performance Optimization

### 1. Embedding Generation

```javascript
// ❌ Slow: One at a time
for (let chunk of chunks) {
  await generateEmbedding(chunk);
}

// ✅ Fast: Batch processing
const embeddings = await generateEmbeddings(chunks);
```

### 2. Vector Search

```javascript
// ❌ Slow: No filtering
const results = await vectorSearch(sessionId, embedding, 100);

// ✅ Fast: Limit results
const results = await vectorSearch(sessionId, embedding, 5);

// ✅ Faster: Higher threshold
const results = await vectorSearch(sessionId, embedding, 5, 0.8);
```

### 3. Chunk Size Tuning

```
Small chunks (500 chars):
+ More precise retrieval
- More API calls
- More storage

Large chunks (5000 chars):
+ Fewer API calls
- Less precise retrieval
- Larger storage

Sweet Spot: 2000-3000 chars
```

## Error Handling

### Document Upload Errors

```
❌ File too large
→ Check MAX_FILE_SIZE env var
→ Compress document or split into multiple files

❌ File format not supported
→ Only PDF and DOCX allowed
→ Convert file to supported format

❌ Text extraction failed
→ May be scanned image or corrupted file
→ Try re-saving the document

❌ Embedding generation failed
→ API quota exceeded
→ Check GEMINI_API_KEY validity
```

### Search Errors

```
❌ No relevant documents found
→ Threshold too high
→ Lower VECTOR_SEARCH_THRESHOLD
→ Upload more relevant documents

❌ Wrong answers to questions
→ Chunk size might be too small
→ Increase chunk overlap
→ Add more documents
```

## Monitoring & Debugging

### Enable Debug Logging

Edit `backend_fastapi/app/services/rag_service.py`:

```python
from app.core.config import settings

async def answer_question_with_rag(
    session_id: str,
    question: str,
    query_embedding: list[float],
):
    logger.info(f"🔍 RAG Query: {question}")

    relevant_chunks = await vector_store.search(
        query_embedding,
        session_id,
        top_k=10,
        similarity_threshold=settings.SIMILARITY_THRESHOLD
    )
    logger.info(f"📚 Found {len(relevant_chunks)} relevant chunks")
    logger.info(f"Similarity scores: {[c['score'] for c in relevant_chunks]}")

    # ... rest of code
```

### Check Embeddings in MongoDB

```bash
# View embeddings for a session
db.embeddings.find({ sessionId: "session-id" }).limit(1).pretty()

# Check embedding vector (should be 3072 numbers)
db.chunks.findOne({ sessionId: "session-id" })
  .embedding.length  // Should be 3072
```

### Test Vector Search Manually

Use MongoDB Compass or MongoDB Shell:

```javascript
// View a sample chunk with embedding
db.chunks.findOne({ sessionId: "test-session" }).pretty()

// Verify vector search index exists
db.chunks.getIndexes()

// Test $vectorSearch aggregation pipeline
db.chunks.aggregate([
  {
    $vectorSearch: {
      index: "vector_index",
      path: "embedding",
      queryVector: [0.123, -0.456, ...],  // 3072-dim vector
      k: 10,
      numCandidates: 100
    }
  },
  {
    $match: { sessionId: "test-session" }
  }
])
```

## Advanced Topics

### Custom Similarity Metrics

Currently using cosine similarity. Could implement:

```javascript
// Euclidean distance
const euclidean = Math.sqrt(
  vector1.reduce((sum, v1, i) => sum + Math.pow(v1 - vector2[i], 2), 0),
);

// Manhattan distance
const manhattan = vector1.reduce(
  (sum, v1, i) => sum + Math.abs(v1 - vector2[i]),
  0,
);

// Dot product
const dotProduct = vector1.reduce((sum, v1, i) => sum + v1 * vector2[i], 0);
```

### Hybrid Search

Combine vector search with keyword search:

```javascript
// Get results from both
const vectorResults = await vectorSearch(...);
const keywordResults = await keywordSearch(question, ...);

// Merge and rank
const combinedResults = mergeAndRank(vectorResults, keywordResults);
```

### Reranking Results

```javascript
// Use smaller, faster model to rerank
const rerankedResults = await reranker.rank(results, question);
```

## Best Practices

### ✅ Do's

- Use appropriate chunk size (1500-3000 chars)
- Set reasonable overlap (20-30% of chunk size)
- Filter by threshold before using context
- Cite sources in responses
- Monitor token usage
- Test with real documents
- Collect user feedback

### ❌ Don'ts

- Use very small chunks (<500 chars)
- Store entire documents as single chunk
- Use raw documents without chunking
- Ignore embedding quality
- Disable TTL (causes storage bloat)
- Trust low similarity scores
- Use expensive embedding models without need

---

**Complete RAG Implementation Reference for PDF Insight Agent!**
