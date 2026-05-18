"""
Tool 2 — Quiz Generator
Génère automatiquement des QCM à partir du contenu du cours.
Supporte 3 niveaux de difficulté : easy, medium, hard.
"""

import json
import re
from langchain.tools import tool
from typing import Literal


DIFFICULTY_PROMPTS = {
    "easy": """
Génère des questions FACILES sur les définitions et concepts de base.
- Questions directes sur le vocabulaire du cours
- Une seule notion testée par question
- Distracteurs clairs et différents de la bonne réponse
""",
    "medium": """
Génère des questions de DIFFICULTÉ MOYENNE sur la compréhension et l'application.
- Questions sur la compréhension des mécanismes
- Application des concepts à des exemples
- Distracteurs plausibles mais incorrects
""",
    "hard": """
Génère des questions DIFFICILES sur l'analyse et la synthèse.
- Questions nécessitant de croiser plusieurs notions
- Analyse de situations complexes
- Distracteurs très proches de la bonne réponse
"""
}


def parse_quiz_from_text(text: str) -> list:
    """Parse le JSON du quiz généré par le LLM."""
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
        if isinstance(data, dict) and "questions" in data:
            return data["questions"]
    except json.JSONDecodeError:
        pass
    return []


def format_quiz_output(questions: list, difficulty: str, show_answers: bool = False) -> str:
    """Formate le quiz pour l'affichage dans Gradio."""
    if not questions:
        return "❌ Impossible de générer le quiz. Réessayez."

    emoji_diff = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
    output = f"""✅ Quiz généré — Niveau {emoji_diff.get(difficulty, '⚪')} {difficulty.upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{len(questions)} questions générées
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    for i, q in enumerate(questions, 1):
        output += f"Q{i}. {q.get('question', 'N/A')}\n"
        options = q.get("options", [])
        letters = ["A", "B", "C", "D"]
        for j, opt in enumerate(options):
            output += f"   {letters[j]}. {opt}\n"
        if show_answers:
            correct_idx = q.get("correct", 0)
            output += f"   ✅ Réponse : {letters[correct_idx]}. {options[correct_idx] if options else 'N/A'}\n\n"
        else:
            output += "\n"

    return output


def generate_quiz_prompt(course_text: str, difficulty: str, num_questions: int) -> str:
    """Construit le prompt pour la génération du quiz."""
    diff_instruction = DIFFICULTY_PROMPTS.get(difficulty, DIFFICULTY_PROMPTS["medium"])

    return f"""Tu es un professeur expert. Voici le contenu d'un cours :

{course_text[:8000]}

{diff_instruction}

Génère exactement {num_questions} questions QCM. 
Réponds UNIQUEMENT avec un JSON valide, aucun texte avant ou après :

[
  {{
    "question": "Question ici ?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": 0,
    "explanation": "Explication courte de la bonne réponse"
  }}
]

Le champ "correct" est l'index 0-3 de la bonne réponse. {num_questions} questions exactement."""


@tool
def quiz_generator_tool(course_text: str, difficulty: str = "medium", num_questions: int = 8) -> str:
    """
    Génère un quiz QCM à partir du contenu d'un cours.
    
    Args:
        course_text: Le texte du cours extrait par pdf_reader_tool
        difficulty: Niveau de difficulté ('easy', 'medium', 'hard')
        num_questions: Nombre de questions à générer (défaut: 8)
        
    Returns:
        Quiz formaté avec questions, options et réponses correctes
    """
    # Validation des paramètres
    if not course_text or len(course_text) < 100:
        return "❌ Texte du cours trop court. Chargez d'abord un PDF avec pdf_reader_tool."

    if difficulty not in ["easy", "medium", "hard"]:
        difficulty = "medium"

    num_questions = max(3, min(20, num_questions))  # Entre 3 et 20

    prompt = generate_quiz_prompt(course_text, difficulty, num_questions)
    return prompt  # L'agent LangChain appelle le LLM avec ce prompt


def quiz_tool_standalone(llm, course_text: str, difficulty: str = "medium", num_questions: int = 8, show_answers: bool = False) -> tuple:
    """
    Version standalone qui appelle directement le LLM.
    Utilisée par app.py pour l'interface Gradio.
    
    Returns:
        (formatted_string, list_of_questions_dicts)
    """
    prompt = generate_quiz_prompt(course_text, difficulty, num_questions)
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

    questions = parse_quiz_from_text(raw_text)
    formatted = format_quiz_output(questions, difficulty, show_answers)
    return formatted, questions
