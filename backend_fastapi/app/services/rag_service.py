"""
RAG (Retrieval-Augmented Generation) Service
Handles question answering using retrieved context
"""

import json
import logging
import warnings
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.database import get_db
from app.services.embedding_service import get_embedding_service
from app.services.vector_store import get_vector_store

# Suppress deprecation warning for google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

logger = logging.getLogger(__name__)


class RAGService:
    """
    Implements RAG pipeline for question answering
    """

    DOCUMENT_UNAVAILABLE_ANSWER = "This information is not available in the provided document."

    def __init__(self):
        """
        Initialize RAG service
        """
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.chat_model = settings.GEMINI_CHAT_MODEL
        self.top_k = settings.TOP_K_RETRIEVAL
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self.session_id: Optional[str] = None

        logger.info(f"🤖 Initialized RAG Service (model: {self.chat_model})")

    def get_agent_tool_registry(self, session_id: str) -> List[Any]:
        """Return the functions Gemini can call."""
        self.session_id = session_id
        return [
            self.search_document,
            self.search_all_documents,
            self.generate_summary,
            self.extract_key_points,
            self.generate_questions,
            self.compare_documents,
            self.web_search_fallback,
        ]

    async def _get_document_chunks(self, document_id: str) -> List[Dict]:
        db = get_db()
        collection = db[settings.MONGODB_CHUNKS_COLLECTION]
        return await collection.find({
            "sessionId": self.session_id,
            "documentId": document_id,
        }).sort("chunkIndex", 1).to_list(length=None)

    async def _get_document_text(self, document_id: str) -> str:
        chunks = await self._get_document_chunks(document_id)
        return "\n\n".join(chunk.get("text", "") for chunk in chunks)

    async def _get_relevant_context(self, query: str, document_id: Optional[str] = None, top_k: Optional[int] = None) -> List[Dict]:
        embedding_service = get_embedding_service()
        vector_store = get_vector_store()
        query_embedding = await embedding_service.embed_query(query)

        results = await vector_store.search(
            query_embedding=query_embedding,
            session_id=self.session_id,
            top_k=top_k or self.top_k,
            similarity_threshold=self.similarity_threshold,
            document_id=document_id,
        )
        return results

    async def search_document(self, query: str, doc_id: str) -> Dict:
        """Search a specific uploaded document for relevant context."""
        matches = await self._get_relevant_context(query, document_id=doc_id, top_k=5)
        return {
            "tool": "search_document",
            "doc_id": doc_id,
            "query": query,
            "matches": [
                {
                    "documentId": item.get("documentId"),
                    "chunkIndex": item.get("chunkIndex"),
                    "text": item.get("text", ""),
                    "score": item.get("score"),
                }
                for item in matches
            ],
            "count": len(matches),
        }

    async def search_all_documents(self, query: str) -> Dict:
        """Search across all documents in the current session."""
        matches = await self._get_relevant_context(query, document_id=None, top_k=8)
        return {
            "tool": "search_all_documents",
            "query": query,
            "matches": [
                {
                    "documentId": item.get("documentId"),
                    "chunkIndex": item.get("chunkIndex"),
                    "text": item.get("text", ""),
                    "score": item.get("score"),
                }
                for item in matches
            ],
            "count": len(matches),
        }

    async def generate_summary(self, doc_id: str) -> Dict:
        """Generate a concise summary for a specific document."""
        full_text = await self._get_document_text(doc_id)
        prompt = (
            "Summarize the following document in 2-3 concise paragraphs. "
            "Highlight key ideas and outcomes.\n\n"
            f"{full_text[:6000]}"
        )
        result = await self.generate_direct_answer(prompt)
        return {
            "tool": "generate_summary",
            "doc_id": doc_id,
            "summary": result["answer"],
        }

    async def extract_key_points(self, doc_id: str) -> Dict:
        """Extract the main key points from a document."""
        full_text = await self._get_document_text(doc_id)
        prompt = (
            "Extract the main key points from the document as a bullet list. "
            "Be precise and avoid repetition.\n\n"
            f"{full_text[:6000]}"
        )
        result = await self.generate_direct_answer(prompt)
        return {
            "tool": "extract_key_points",
            "doc_id": doc_id,
            "key_points": result["answer"],
        }

    async def generate_questions(self, doc_id: str) -> Dict:
        """Generate important discussion or review questions from a document."""
        full_text = await self._get_document_text(doc_id)
        prompt = (
            "Generate 5 high-quality questions a user could ask about this document. "
            "Focus on understanding, risks, implications, and follow-up topics.\n\n"
            f"{full_text[:6000]}"
        )
        result = await self.generate_direct_answer(prompt)
        return {
            "tool": "generate_questions",
            "doc_id": doc_id,
            "questions": result["answer"],
        }

    async def compare_documents(self, doc_ids: List[str], aspect: str) -> Dict:
        """Compare documents on a specific aspect such as dates, risks, terms, or clauses."""
        docs = []
        for doc_id in doc_ids:
            docs.append({
                "doc_id": doc_id,
                "text": await self._get_document_text(doc_id),
            })

        prompt = (
            f"Compare the following documents on the aspect: {aspect}. "
            "Summarize similarities, differences, and notable findings.\n\n"
            + json.dumps(docs, ensure_ascii=False)[:12000]
        )
        result = await self.generate_direct_answer(prompt)
        return {
            "tool": "compare_documents",
            "doc_ids": doc_ids,
            "aspect": aspect,
            "comparison": result["answer"],
        }

    async def web_search_fallback(self, query: str) -> Dict:
        """General knowledge fallback when no relevant document content is found."""
        result = await self.generate_direct_answer(query)
        return {
            "tool": "web_search_fallback",
            "query": query,
            "answer": result["answer"],
        }

    async def retrieve_relevant_chunks(
        self,
        query: str,
        session_id: str,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve relevant chunks for a query
        """
        try:
            logger.info(f"🔍 Retrieving chunks for query: '{query}'")

            embedding_service = get_embedding_service()
            vector_store = get_vector_store()
            query_embedding = await embedding_service.embed_query(query)

            top_k = top_k or self.top_k
            results = await vector_store.search(
                query_embedding=query_embedding,
                session_id=session_id,
                top_k=top_k,
                similarity_threshold=self.similarity_threshold
            )

            logger.info(f"✅ Retrieved {len(results)} relevant chunks")
            return results

        except Exception as e:
            logger.error(f"❌ Error retrieving chunks: {e}")
            raise

    async def expand_context(
        self,
        chunks: List[Dict],
        session_id: str
    ) -> List[Dict]:
        """
        Expand context by including previous and next chunks
        """
        try:
            logger.info(f"📖 Expanding context for {len(chunks)} chunks...")

            db = get_db()
            collection = db[settings.MONGODB_CHUNKS_COLLECTION]

            expanded_chunks = []
            seen_chunk_ids = set()

            for chunk in chunks:
                chunk_index = chunk.get("chunkIndex", 0)
                document_id = chunk.get("documentId")

                context_chunks = await collection.find({
                    "sessionId": session_id,
                    "documentId": document_id,
                    "chunkIndex": {
                        "$gte": chunk_index - 1,
                        "$lte": chunk_index + 1
                    }
                }).sort("chunkIndex", 1).to_list(length=None)

                for ctx_chunk in context_chunks:
                    chunk_id = str(ctx_chunk.get("_id"))
                    if chunk_id not in seen_chunk_ids:
                        ctx_chunk["isMainChunk"] = (ctx_chunk.get("chunkIndex") == chunk_index)
                        expanded_chunks.append(ctx_chunk)
                        seen_chunk_ids.add(chunk_id)

            logger.info(f"✅ Expanded to {len(expanded_chunks)} chunks (with context)")
            return expanded_chunks

        except Exception as e:
            logger.error(f"❌ Error expanding context: {e}")
            return chunks

    async def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict]
    ) -> Dict:
        """
        Generate answer using Gemini with retrieved context
        """
        try:
            logger.info(f"💬 Generating answer for query: '{query}'")

            context_text = self._build_context(context_chunks)
            system_prompt = self._create_system_prompt(context_text)
            combined_prompt = f"{system_prompt}\n\nQuestion: {query}"

            response = self.client.models.generate_content(
                model=self.chat_model,
                contents=combined_prompt,
            )
            answer = response.text

            logger.info(f"✅ Generated answer ({len(answer)} chars)")

            return {
                "answer": answer,
                "context_used": len(context_chunks),
                "query": query,
                "model": self.chat_model,
                "status": (
                    "document_unavailable"
                    if self._is_document_unavailable_answer(answer)
                    else "success"
                )
            }

        except Exception as e:
            logger.error(f"❌ Error generating answer: {e}")
            raise

    def _build_context(self, chunks: List[Dict]) -> str:
        """
        Build context string from chunks
        """
        try:
            context_parts = []
            for i, chunk in enumerate(chunks):
                text = chunk.get("text", "")
                chunk_index = chunk.get("chunkIndex", i)
                is_main = chunk.get("isMainChunk", False)

                if is_main:
                    context_parts.append(f"[PRIMARY CHUNK {chunk_index}]\n{text}")
                else:
                    context_parts.append(f"[CONTEXT CHUNK {chunk_index}]\n{text}")

            return "\n\n---\n\n".join(context_parts)

        except Exception as e:
            logger.warning(f"⚠️  Error building context: {e}")
            return ""

    def _create_system_prompt(self, context: str) -> str:
        """
        Create system prompt with context
        """
        return f"""You are a helpful document analysis assistant. Answer questions based ONLY on the provided document context.

CRITICAL RULES:
1. Only use information from the provided document chunks.
2. If the answer is not in the document, respond with: "{self.DOCUMENT_UNAVAILABLE_ANSWER}"
3. Do not generate or assume data that is not explicitly stated.
4. Preserve tables, lists, and structured data from the document when presenting answers.
5. Use markdown formatting for better readability.
6. Include relevant quotes from the document when appropriate.

DOCUMENT CONTEXT:
{context}

---
Now answer the user's question using ONLY the above context."""

    def _is_document_unavailable_answer(self, answer: str) -> bool:
        """
        Detect when the document-grounded prompt could not answer the query.
        """
        normalized_answer = (answer or "").strip().strip('"').strip("'").rstrip(".").lower()
        normalized_unavailable = self.DOCUMENT_UNAVAILABLE_ANSWER.rstrip(".").lower()
        return normalized_answer == normalized_unavailable

    async def generate_direct_answer(self, query: str) -> Dict:
        """
        Generate answer using direct LLM query (no RAG context)
        """
        try:
            logger.info(f"💬 Generating direct LLM response for: '{query}'")

            system_prompt = """You are a helpful AI assistant. Provide accurate, helpful, and concise answers to user questions.
If you're unsure about something, say so rather than making up information.
Use markdown formatting for better readability when appropriate."""
            combined_prompt = f"{system_prompt}\n\nQuestion: {query}"

            response = self.client.models.generate_content(
                model=self.chat_model,
                contents=combined_prompt,
            )
            answer = response.text

            logger.info(f"✅ Generated direct LLM response ({len(answer)} chars)")

            return {
                "answer": answer,
                "context_used": 0,
                "query": query,
                "model": self.chat_model,
                "chunks_retrieved": 0,
                "chunks_with_context": 0,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"❌ Error generating direct answer: {e}")
            raise

    async def _grounding_self_check(self, query: str, answer: str, tool_results: List[Dict]) -> bool:
        """Check whether the answer is grounded in retrieved document snippets."""
        matches = []
        for item in tool_results:
            result = item.get("result") or {}
            matches.extend(result.get("matches", []))

        if not matches:
            return False

        context_text = json.dumps(matches, ensure_ascii=False)[:12000]
        prompt = (
            "Self-check only. Determine if the answer below is grounded in the retrieved document snippets. "
            "Respond with only: YES or NO.\n\n"
            f"Question: {query}\n\n"
            f"Answer: {answer}\n\n"
            f"Retrieved snippets:\n{context_text}"
        )

        resp = self.client.models.generate_content(
            model=self.chat_model,
            contents=prompt,
        )
        verdict = (resp.text or "").strip().upper()
        return verdict.startswith("YES")

    async def _execute_agent_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """Execute a Gemini tool call."""
        if tool_name == "search_document":
            return await self.search_document(**arguments)
        if tool_name == "search_all_documents":
            return await self.search_all_documents(**arguments)
        if tool_name == "generate_summary":
            return await self.generate_summary(**arguments)
        if tool_name == "extract_key_points":
            return await self.extract_key_points(**arguments)
        if tool_name == "generate_questions":
            return await self.generate_questions(**arguments)
        if tool_name == "compare_documents":
            return await self.compare_documents(**arguments)
        if tool_name == "web_search_fallback":
            return await self.web_search_fallback(**arguments)
        raise ValueError(f"Unsupported tool: {tool_name}")

    async def answer_question_agentic(self, query: str, session_id: str) -> Dict:
        """Use Gemini function calling to decide what tools to call."""
        self.session_id = session_id
        tool_trace: List[str] = []
        tool_results: List[Dict] = []
        tool_outputs = []

        tools = self.get_agent_tool_registry(session_id)
        system_prompt = (
            "You are an autonomous document analysis agent. "
            "Decide which tool or tools to call to answer the user's query. "
            "You may call multiple tools in sequence. "
            "Use the tools before answering. "
            "When the user asks for summary, key points, or questions, prefer the matching document tool. "
            "If the document does not contain enough evidence, say so and use web_search_fallback."
        )

        response = self.client.models.generate_content(
            model=self.chat_model,
            contents=f"{system_prompt}\n\nUser query: {query}",
            config=types.GenerateContentConfig(
                tools=tools,
                automatic_function_calling={"ignore_call_history": True},
            ),
        )

        while response.function_calls:
            for fc in response.function_calls:
                tool_name = fc.name
                tool_args = fc.args or {}
                tool_trace.append(f"{tool_name}({json.dumps(tool_args, ensure_ascii=False)})")

                result = await self._execute_agent_tool(tool_name, tool_args)
                tool_results.append({"name": tool_name, "args": tool_args, "result": result})
                tool_outputs.append({
                    "role": "user",
                    "parts": [{
                        "function_response": {
                            "name": tool_name,
                            "response": result,
                        }
                    }]
                })

            follow_up = (
                "Use the tool outputs below to answer the user's question. "
                "Do not invent facts. Ground your answer in the tool outputs. "
                f"User question: {query}\n\n"
                f"Tool outputs: {json.dumps(tool_results, ensure_ascii=False)[:12000]}"
            )

            response = self.client.models.generate_content(
                model=self.chat_model,
                contents=[{"role": "user", "parts": [{"text": follow_up}]}, *tool_outputs],
                config=types.GenerateContentConfig(
                    tools=tools,
                    automatic_function_calling={"ignore_call_history": True},
                ),
            )

        final_answer = response.text or "I could not produce a grounded answer."
        grounded = await self._grounding_self_check(query, final_answer, tool_results)

        if not grounded:
            fallback = await self.web_search_fallback(query)
            tool_trace.append("web_search_fallback")
            final_answer = fallback["answer"]
            grounded = False

        return {
            "answer": final_answer,
            "context_used": max(0, sum(
                1 for item in tool_results if item["name"] in {"search_document", "search_all_documents"}
            )),
            "chunks_retrieved": max(0, sum(
                len((item.get("result") or {}).get("matches", []))
                for item in tool_results
                if item["name"] in {"search_document", "search_all_documents"}
            )),
            "chunks_with_context": max(0, sum(
                len((item.get("result") or {}).get("matches", []))
                for item in tool_results
                if item["name"] in {"search_document", "search_all_documents"}
            )),
            "agent_trace": tool_trace,
            "tools_used": [item["name"] for item in tool_results],
            "grounded": grounded,
            "status": "success",
            "source": "AGENTIC_RAG",
            "model": self.chat_model,
        }

    async def answer_question(
        self,
        query: str,
        session_id: str
    ) -> Dict:
        """
        Backward-compatible RAG pipeline: retrieve -> expand -> generate answer
        Uses Gemini tool-calling when possible while preserving old behavior.
        """
        try:
            logger.info(f"🚀 Agentic RAG Pipeline: Answering '{query}'")
            return await self.answer_question_agentic(query, session_id)
        except Exception as e:
            logger.error(f"❌ Agentic RAG Pipeline error: {e}")
            raise


# Singleton instance
_rag_service = None


def get_rag_service() -> RAGService:
    """
    Get or create RAGService instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
