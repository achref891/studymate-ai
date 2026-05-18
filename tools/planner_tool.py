"""
Tool 4 — Study Planner
Génère un planning de révision intelligent et personnalisé.
Adapte le planning selon les jours disponibles, les heures/jour et la difficulté du cours.
"""

from langchain.tools import tool
from datetime import datetime, timedelta


def calculate_study_blocks(days: int, hours_per_day: float, difficulty: str) -> dict:
    """
    Calcule la structure optimale du planning selon les paramètres.
    Retourne la répartition recommandée des activités.
    """
    total_hours = days * hours_per_day

    # Répartition selon la difficulté
    ratios = {
        "easy":   {"lecture": 0.30, "quiz": 0.25, "flashcards": 0.25, "review": 0.20},
        "medium": {"lecture": 0.35, "quiz": 0.25, "flashcards": 0.20, "review": 0.20},
        "hard":   {"lecture": 0.40, "quiz": 0.20, "flashcards": 0.20, "review": 0.20},
    }
    ratio = ratios.get(difficulty, ratios["medium"])

    return {
        "total_hours": round(total_hours, 1),
        "lecture_hours": round(total_hours * ratio["lecture"], 1),
        "quiz_hours": round(total_hours * ratio["quiz"], 1),
        "flashcard_hours": round(total_hours * ratio["flashcards"], 1),
        "review_hours": round(total_hours * ratio["review"], 1),
        "sessions_per_day": max(1, round(hours_per_day / 1.5)),
    }


def generate_planner_prompt(
    course_text: str,
    days: int,
    hours_per_day: float,
    difficulty: str
) -> str:
    """Construit le prompt pour la génération du planning."""

    blocks = calculate_study_blocks(days, hours_per_day, difficulty)
    today = datetime.now()
    exam_date = today + timedelta(days=days)

    difficulty_fr = {"easy": "Facile", "medium": "Moyen", "hard": "Difficile"}.get(difficulty, "Moyen")

    return f"""Tu es un expert en méthodes de révision universitaire. Voici un cours à réviser :

RÉSUMÉ DU COURS (extrait) :
{course_text[:5000]}

PARAMÈTRES DE L'ÉTUDIANT :
- Jours avant l'examen : {days} jours (examen le {exam_date.strftime('%d/%m/%Y')})
- Disponibilité : {hours_per_day}h par jour
- Niveau de difficulté du cours : {difficulty_fr}
- Temps total disponible : {blocks['total_hours']}h

RÉPARTITION OPTIMALE CALCULÉE :
- Lecture/Compréhension : {blocks['lecture_hours']}h
- Entraînement Quiz : {blocks['quiz_hours']}h
- Flashcards : {blocks['flashcard_hours']}h
- Révision finale : {blocks['review_hours']}h
- Sessions recommandées/jour : {blocks['sessions_per_day']}

GÉNÈRE un planning jour par jour avec :
1. **Titre du jour** (ex: "Jour 1 — Fondations")
2. **Objectif du jour** (ce que l'étudiant doit maîtriser)
3. **Activités planifiées** avec horaires et durées
4. **Concepts à réviser** (extraits du cours)
5. **Méthode recommandée** (techniques de mémorisation)
6. **Conseil du jour** (motivation + astuce)

Termine avec :
- 3 conseils généraux pour l'examen
- Checklist de révision finale
- Message de motivation personnalisé

Sois CONCRET, PRÉCIS et MOTIVANT. Adapte les révisions à la difficulté {difficulty_fr}."""


@tool
def study_planner_tool(
    course_text: str,
    days_before_exam: int = 7,
    hours_per_day: float = 2.0,
    difficulty: str = "medium"
) -> str:
    """
    Génère un planning de révision intelligent et personnalisé.
    
    Args:
        course_text: Texte du cours extrait du PDF
        days_before_exam: Nombre de jours avant l'examen (défaut: 7)
        hours_per_day: Heures disponibles par jour (défaut: 2.0)
        difficulty: Difficulté du cours ('easy', 'medium', 'hard')
        
    Returns:
        Planning détaillé jour par jour avec conseils
    """
    if not course_text or len(course_text) < 100:
        return "❌ Chargez d'abord un cours avec pdf_reader_tool."

    days_before_exam = max(1, min(60, days_before_exam))
    hours_per_day = max(0.5, min(12.0, hours_per_day))

    return generate_planner_prompt(course_text, days_before_exam, hours_per_day, difficulty)


def planner_tool_standalone(
    llm,
    course_text: str,
    days: int = 7,
    hours_per_day: float = 2.0,
    difficulty: str = "medium"
) -> str:
    prompt = generate_planner_prompt(course_text, days, hours_per_day, difficulty)
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
    return raw_text
