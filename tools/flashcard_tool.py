"""
Tool 3 — Flashcard Generator
Crée des cartes mémoire Question/Réponse à partir du cours.
Format optimisé pour la mémorisation active (méthode Leitner).
"""

import json
import re
from langchain.tools import tool


def parse_flashcards_from_text(text: str) -> list:
    """Parse le JSON des flashcards générées par le LLM."""
    try:
        # Tenter d'extraire le bloc de code json s'il est spécifié par des backticks
        json_block_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if json_block_match:
            clean = json_block_match.group(1).strip()
        else:
            # Sinon, extraire tout ce qui est entre les crochets ou accolades extérieurs
            match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
            if match:
                clean = match.group(1).strip()
            else:
                clean = text.strip()
                
        data = json.loads(clean)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "flashcards" in data:
            return data["flashcards"]
    except json.JSONDecodeError:
        pass
    return []


def format_flashcards_output(cards: list) -> str:
    """Formate les flashcards pour l'affichage."""
    if not cards:
        return "❌ Impossible de générer les flashcards."

    output = f"""🃏 {len(cards)} Flashcards générées
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Méthode : Question → Réponse
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    for i, card in enumerate(cards, 1):
        output += f"Carte {i:02d}\n"
        output += f"❓ {card.get('question', 'N/A')}\n"
        output += f"💡 {card.get('answer', 'N/A')}\n"
        if card.get("category"):
            output += f"🏷️  {card['category']}\n"
        output += "\n"

    return output


def generate_flashcards_prompt(course_text: str, num_cards: int) -> str:
    return f"""Tu es un expert en pédagogie. Voici un cours universitaire :

{course_text[:8000]}

Crée exactement {num_cards} flashcards pour révision active.
Chaque flashcard doit :
- Tester UN concept précis
- Avoir une réponse concise (1-3 phrases max)
- Couvrir les notions importantes du cours

Réponds UNIQUEMENT avec un JSON valide :

[
  {{
    "question": "Qu'est-ce que X ?",
    "answer": "X est... (réponse courte et claire)",
    "category": "Notion fondamentale"
  }}
]

{num_cards} flashcards exactement, variées et couvrant tout le cours."""


@tool
def flashcard_generator_tool(course_text: str, num_cards: int = 12) -> str:
    """
    Génère des flashcards Question/Réponse à partir d'un cours.
    
    Args:
        course_text: Texte du cours extrait du PDF
        num_cards: Nombre de cartes à générer (défaut: 12)
        
    Returns:
        Flashcards formatées avec questions et réponses
    """
    if not course_text or len(course_text) < 100:
        return "❌ Texte du cours trop court. Utilisez d'abord pdf_reader_tool."

    num_cards = max(5, min(30, num_cards))
    return generate_flashcards_prompt(course_text, num_cards)


def flashcard_tool_standalone(llm, course_text: str, num_cards: int = 12) -> tuple:
    """
    Version standalone pour Gradio.
    Returns: (formatted_string, list_of_cards_dicts)
    """
    prompt = generate_flashcards_prompt(course_text, num_cards)
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else response
    if isinstance(content, list):
        raw_text = ""
        for block in content:
            if isinstance(block, str):
                raw_text += block
            elif isinstance(block, dict) and "text" in block:
                raw_text += block["text"]
            elif hasattr(block, "text"):
                raw_text += block.text
            elif hasattr(block, "get") and block.get("text"):
                raw_text += block.get("text")
            else:
                raw_text += str(block)
    else:
        raw_text = str(content)

    cards = parse_flashcards_from_text(raw_text)
    formatted = format_flashcards_output(cards)
    return formatted, cards
