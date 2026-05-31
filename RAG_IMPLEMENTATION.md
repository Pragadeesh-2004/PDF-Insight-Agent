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
Generate Embedding
    ↓
Vector Similarity Search
    ↓
    ┌─────────────────────┐
    │ Similarity Score?   │
    └─────────────────────┘
           ↙         ↘
        HIGH        LOW
        (>0.7)      (<0.7)
        ↓           ↓
      USE RAG    USE GEMINI
      ↓           ↓
   Context     No Context
   ↓           ↓
   Gemini + Context  Gemini Only
      ↓           ↓
    ANSWER      ANSWER
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
│                    BACKEND (Express)                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Routes: /upload, /chat, /session                 │ │
│  │  Controllers: Upload, Chat, Session               │ │
│  │  Services:                                         │ │
│  │  ├─ PDF/DOCX Extraction                           │ │
│  │  ├─ Text Chunking                                 │ │
│  │  ├─ Embedding Generation (Gemini API)            │ │
│  │  ├─ Vector Search (MongoDB)                       │ │
│  │  ├─ Gemini Integration                            │ │
│  │  └─ RAG Orchestration                             │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                                   ↓
┌──────────────────┐          ┌──────────────────────┐
│   MongoDB Atlas  │          │  Google Gemini API   │
│                  │          │                      │
│ Collections:     │          │ • Embeddings         │
│ • sessions       │          │ • Text Generation    │
│ • documents      │          │ • Summarization      │
│ • chunks         │          │ • QA                 │
│ • embeddings     │          │                      │
│ • chatHistory    │          │                      │
│                  │          │                      │
│ Vector Search    │          │                      │
│ TTL Cleanup      │          │                      │
└──────────────────┘          └──────────────────────┘
```

## Workflow Details

### 1. Document Upload Flow

```
User uploads PDF/DOCX
        ↓
Validate file (type, size)
        ↓
Extract text
├─ PDF → pdf-parse.js
└─ DOCX → mammoth.js
        ↓
Split into chunks
├─ Character-based: 2000 chars, 300 overlap
└─ Results in ~20-50 chunks per document
        ↓
Generate embeddings
├─ Each chunk → Gemini API
├─ Returns 768-dimensional vector
└─ Results in ~20-50 embeddings
        ↓
Store in MongoDB
├─ Save document metadata
├─ Save chunks with text
└─ Save embeddings with vectors
        ↓
Ready for Q&A!
```

### 2. Question Processing Flow

```
User asks: "What is the main topic?"
        ↓
Generate question embedding
├─ Same model: text-embedding-005
├─ Returns 768-dimensional vector
└─ Used for similarity matching
        ↓
Vector Similarity Search
├─ Compare question vector
├─ With all document vectors
├─ Calculate cosine similarity
└─ Score: 0.0 to 1.0
        ↓
Sort by similarity score
        ↓
Filter by threshold (default 0.7)
        ↓
    Did we find matches?
       /      \
     YES      NO
      ↓        ↓
   USE RAG   DIRECT LLM
      ↓        ↓
   Get Top 5   No Context
   Chunks
      ↓
   Combine context
   "Here's relevant info:
    [chunk1]
    [chunk2]
    [chunk3]
    ...
    User question: ..."
      ↓
   Send to Gemini
      ↓
   Generate answer
      ↓
   Return answer + sources
```

### 3. Data Storage

```
Session Created
├─ sessionId: "session-12345"
├─ agentType: "PDF_INSIGHT_AGENT"
└─ TTL: 1 hour

Document Uploaded
├─ documentId: "uuid"
├─ sessionId: "session-12345"
├─ fileName: "research.pdf"
├─ fileType: "PDF"
├─ chunksCount: 25
└─ TTL: 1 hour

Chunks Stored
├─ chunkId: "uuid-chunk-0"
├─ documentId: "uuid"
├─ sessionId: "session-12345"
├─ text: "The document contains..."
├─ chunkIndex: 0
└─ TTL: 1 hour

Embeddings Stored
├─ embeddingId: "uuid"
├─ chunkId: "uuid-chunk-0"
├─ documentId: "uuid"
├─ sessionId: "session-12345"
├─ vector: [0.123, -0.456, 0.789, ...]
└─ TTL: 1 hour

Chat History Stored
├─ messageId: "uuid"
├─ sessionId: "session-12345"
├─ role: "user" or "assistant"
├─ content: "message text"
├─ usedRAG: true/false
├─ relevantDocuments: ["doc-id-1"]
└─ TTL: 1 hour
```

## Vector Search Deep Dive

### What is Vector Similarity?

Each text chunk is converted to a vector (array of numbers):

```
"The sky is blue" → [-0.12, 0.45, 0.89, -0.23, ...]  (768 dimensions)
```

When you ask a question, it's also converted to a vector:

```
"What color is the sky?" → [0.08, 0.42, 0.91, -0.19, ...]  (768 dimensions)
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

Score 0.7-0.9 : Relevant
  Example: "sky" vs "weather condition"

Score 0.5-0.7 : Somewhat related
  Example: "sky" vs "outdoor activity"

Score <0.5 : Not related
  Example: "sky" vs "cooking recipe"
```

### Default Threshold: 0.7

- **Why 0.7?** Balances precision and recall
- **Adjustments**:
  - ↑ Higher (0.8+): Stricter, fewer false positives
  - ↓ Lower (0.6-): Looser, more coverage but noise

## Embedding Model

### text-embedding-005 (Recommended)

- **Dimensions**: 768
- **Cost**: Free tier available
- **Speed**: ~100ms per chunk
- **Quality**: High
- **Optimization**: Optimized for semantic search

### Example Embedding Usage

```javascript
import { generateEmbedding } from "./embeddingService.js";

const text = "Python is a programming language";
const embedding = await generateEmbedding(text);
// Result: [0.123, -0.456, 0.789, ..., -0.234]  (768 numbers)

console.log(embedding.length); // 768
```

## Chunking Strategy

### Why Chunk?

- **Token Limits**: Gemini has max input tokens
- **Context Windows**: Smaller chunks, more precise retrieval
- **Efficiency**: Process only relevant parts
- **Scalability**: Handle large documents

### Chunking Methods

#### 1. Character-Based (Recommended)

```javascript
chunkTextByCharacters(text, (chunkSize = 2000), (overlap = 300));
```

**Example**:

```
Full Text: "The document contains information about AI... machine learning... neural networks..."

Chunk 1: "The document contains information about AI... machine learning..." (2000 chars)
          ↑ Start
                                                                    ↑ End (first 2000)

Chunk 2: "machine learning... neural networks..." (2000 chars)
          ↑ Start (overlaps 300 chars from chunk 1)
                                                   ↑ End

Chunk 3: "neural networks..." (remaining)
```

**Advantages**:

- Preserves sentence boundaries better
- Language-agnostic
- Consistent chunk sizes

#### 2. Word-Based

```javascript
chunkText(text, (chunkSize = 1000), (overlap = 200));
```

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

Edit `backend/services/ragService.js`:

```javascript
export async function answerQuestionWithRAG(
  sessionId,
  question,
  queryEmbedding,
) {
  console.log("🔍 RAG Query:", question);

  const relevantChunks = await vectorSearch(
    sessionId,
    queryEmbedding,
    5,
    threshold,
  );
  console.log(`📚 Found ${relevantChunks.length} relevant chunks`);
  console.log(
    "Similarity scores:",
    relevantChunks.map((c) => c.similarity),
  );

  // ... rest of code
}
```

### Check Embeddings in MongoDB

```bash
# View embeddings for a session
db.embeddings.find({ sessionId: "session-id" }).limit(1).pretty()

# Check embedding vector (should be 768 numbers)
db.embeddings.findOne({ sessionId: "session-id" })
  .vector.length  // Should be 768
```

### Test Vector Search Manually

```javascript
import { vectorSearch } from "./vectorSearchService.js";

const sessionId = "test-session";
const testEmbedding = await generateEmbedding("test query");

const results = await vectorSearch(sessionId, testEmbedding, 10, 0.5);

console.log("Results:", results);
results.forEach((r, i) => {
  console.log(
    `${i + 1}. Score: ${r.similarity}, Text: ${r.text.substring(0, 100)}...`,
  );
});
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
