import pytest

from app.services.rag_service import RAGService


def test_agentic_tool_registry_contains_expected_document_tools():
    service = RAGService.__new__(RAGService)

    tool_registry = service.get_agent_tool_registry(session_id="session-123")
    tool_names = [tool.__name__ for tool in tool_registry]

    expected = {
        "search_document",
        "search_all_documents",
        "generate_summary",
        "extract_key_points",
        "generate_questions",
        "compare_documents",
        "web_search_fallback",
    }

    assert expected.issubset(set(tool_names))
