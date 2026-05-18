"""
StudyMate AI — Tools Package
Exporte tous les outils disponibles pour l'agent LangChain.
"""

from .pdf_reader import pdf_reader_tool, extract_text_from_pdf
from .quiz_tool import quiz_generator_tool, quiz_tool_standalone
from .flashcard_tool import flashcard_generator_tool, flashcard_tool_standalone
from .planner_tool import study_planner_tool, planner_tool_standalone

# Liste de tous les tools pour LangChain Agent
ALL_TOOLS = [
    pdf_reader_tool,
    quiz_generator_tool,
    flashcard_generator_tool,
    study_planner_tool,
]

__all__ = [
    "pdf_reader_tool",
    "quiz_generator_tool",
    "flashcard_generator_tool",
    "study_planner_tool",
    "extract_text_from_pdf",
    "quiz_tool_standalone",
    "flashcard_tool_standalone",
    "planner_tool_standalone",
    "ALL_TOOLS",
]
