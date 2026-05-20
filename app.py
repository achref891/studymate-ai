"""
StudyMate AI — Interface Gradio
Point d'entrée principal de l'application.
Lance l'interface utilisateur avec tous les modules.
"""

import gradio as gr
import os
import json
import tempfile
from agent import StudyMateAgent

# ─── INITIALISATION DE L'AGENT ───────────────
agent = StudyMateAgent()

# ─── ÉTAT GLOBAL (Quiz) ──────────────────────
quiz_state = {"questions": [], "current": 0, "score": 0, "answers": []}
flashcard_state = {"cards": [], "current": 0, "known": [], "review": []}


# ═══════════════════════════════════════════════
# FONCTIONS DE CALLBACK GRADIO
# ═══════════════════════════════════════════════

def load_pdf_callback(pdf_file):
    """Charge un PDF et retourne le statut."""
    if pdf_file is None:
        return "⬆️ Uploadez un fichier PDF pour commencer.", ""

    result = agent.load_pdf(pdf_file.name)

    if not result["success"]:
        return f"❌ Erreur : {result['message']}", ""

    chapters_text = ""
    if result["chapters"]:
        chapters_text = "\n".join([
            f"  • Page {c['page']} — {c['title']}"
            for c in result["chapters"][:10]
        ])

    status = f"""{result['message']}

📄 Pages      : {result['pages']}
📝 Mots       : {result['words']:,}
📚 Chapitres  : {len(result['chapters'])} détectés
{chapters_text}"""

    return status, f"✅ Cours chargé : {result['filename']}"


def generate_summary_callback():
    """Génère le résumé du cours."""
    if not agent.course_text:
        return "❌ Chargez d'abord un PDF !"
    return agent.generate_summary()


def generate_quiz_callback(difficulty, num_questions):
    """Génère un quiz et initialise l'état."""
    global quiz_state
    if not agent.course_text:
        return "❌ Chargez d'abord un PDF !", gr.update(visible=False)

    formatted, questions = agent.generate_quiz(difficulty, int(num_questions), show_answers=False)

    if questions:
        quiz_state = {
            "questions": questions,
            "current": 0,
            "score": 0,
            "answers": [],
            "difficulty": difficulty
        }
        q = questions[0]
        options_text = format_question_display(q, 0, len(questions))
        return options_text, gr.update(choices=q["options"], value=None, visible=True)
    
    return "Impossible de générer le quiz. Réessayez.", gr.update(visible=False)


def format_question_display(question: dict, current: int, total: int) -> str:
    """Formate l'affichage d'une question de quiz."""
    q = question
    return f"""━━━━━━━━━━━━━━━━━━━━━━━━
Question {current + 1} / {total}
━━━━━━━━━━━━━━━━━━━━━━━━

{q.get('question', 'N/A')}"""


def submit_quiz_answer(selected_option):
    """Traite une réponse de quiz et passe à la suivante."""
    global quiz_state
    q_list = quiz_state["questions"]

    if not q_list or quiz_state["current"] >= len(q_list):
        return "Quiz terminé !", "", gr.update(visible=False), gr.update(visible=False)

    current_idx = quiz_state["current"]
    q = q_list[current_idx]
    options = q.get("options", [])
    correct_idx = q.get("correct", 0)
    correct_answer = options[correct_idx] if options else ""

    # Évaluation
    is_correct = (selected_option == correct_answer)
    if is_correct:
        quiz_state["score"] += 1
    quiz_state["answers"].append(selected_option)
    quiz_state["current"] += 1

    feedback = "✅ Bonne réponse !" if is_correct else f"❌ Incorrect. Réponse : {correct_answer}"
    if q.get("explanation"):
        feedback += f"\n💡 {q['explanation']}"

    # Question suivante ou résultat final
    next_idx = quiz_state["current"]
    if next_idx < len(q_list):
        next_q = q_list[next_idx]
        question_text = format_question_display(next_q, next_idx, len(q_list))
        return (
            feedback,
            question_text,
            gr.update(choices=next_q["options"], value=None, visible=True),
            gr.update(visible=True)
        )
    else:
        score = quiz_state["score"]
        total = len(q_list)
        pct = round(score / total * 100)
        final_msg = f"""━━━━━━━━━━━━━━━━━━━
🏁 Quiz terminé !
━━━━━━━━━━━━━━━━━━━
Score : {score}/{total} ({pct}%)
{'🏆 Excellent !' if pct >= 80 else '📚 Continuez à réviser !'}"""
        
        return feedback, final_msg, gr.update(visible=False), gr.update(visible=False)


def generate_flashcards_callback(num_cards):
    """Génère les flashcards et affiche le résultat simple."""
    if not agent.course_text:
        return "❌ Chargez d'abord un PDF !"

    formatted, cards = agent.generate_flashcards(int(num_cards))
    return formatted


def generate_planner_callback(days, hours, difficulty):
    """Génère le planning de révision."""
    if not agent.course_text:
        return "❌ Chargez d'abord un PDF !"
    return agent.generate_planner(int(days), float(hours), difficulty)


def chat_callback(message, history):
    """Callback pour le chat Gradio."""
    if not message.strip():
        return history, ""
    response = agent.chat(message)
    # Gradio 6 format: list of dicts with role and content keys
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    return history, ""



# ═══════════════════════════════════════════════
# INTERFACE GRADIO
# ═══════════════════════════════════════════════

CSS = """
.gradio-container { font-family: 'Segoe UI', sans-serif; }
.header-box { background: linear-gradient(135deg, #7C3AED, #5B21B6); padding: 20px; border-radius: 12px; color: white; text-align: center; margin-bottom: 16px; }
.tool-card { border: 1px solid #DDD6FE; border-radius: 10px; padding: 12px; background: #FAFAFA; }
.score-box { background: #EDE9FE; border-radius: 8px; padding: 10px; text-align: center; font-weight: bold; color: #5B21B6; }
"""

with gr.Blocks(
    title="StudyMate AI",
    css=CSS,
    theme=gr.themes.Soft(primary_hue="violet"),
) as app:

    # ── HEADER ──────────────────────────────────
    gr.HTML("""
    <div class="header-box">
        <h1>🎓 StudyMate AI</h1>
        <p>Votre assistant intelligent pour réviser efficacement</p>
    </div>
    """)

    with gr.Row():

        # ── COLONNE GAUCHE : Upload + Paramètres ──
        with gr.Column(scale=1, min_width=260):

            gr.Markdown("### 📤 Chargement du cours")
            pdf_input = gr.File(
                label="Fichier PDF",
                file_types=[".pdf"],
                type="filepath",
            )
            pdf_status = gr.Textbox(
                label="Statut",
                lines=8,
                interactive=False,
                placeholder="Uploadez un PDF pour commencer...",
            )
            pdf_label = gr.Textbox(label="Cours actif", interactive=False)

            pdf_input.change(
                fn=load_pdf_callback,
                inputs=[pdf_input],
                outputs=[pdf_status, pdf_label],
            )


        # ── COLONNE CENTRALE + DROITE : Tabs ────────
        with gr.Column(scale=3):

            with gr.Tabs():

                # TAB 1 : CHAT
                with gr.TabItem("💬 Chat avec le cours"):
                    chatbot = gr.Chatbot(height=400, label="Conversation")
                    with gr.Row():
                        chat_input = gr.Textbox(
                            placeholder="Pose une question sur le cours...",
                            label="",
                            scale=4,
                        )
                        chat_btn = gr.Button("Envoyer ➤", scale=1, variant="primary")

                    chat_btn.click(
                        fn=chat_callback,
                        inputs=[chat_input, chatbot],
                        outputs=[chatbot, chat_input],
                    )
                    chat_input.submit(
                        fn=chat_callback,
                        inputs=[chat_input, chatbot],
                        outputs=[chatbot, chat_input],
                    )

                # TAB 2 : RÉSUMÉ
                with gr.TabItem("📋 Résumé"):
                    summary_btn = gr.Button("📋 Générer le résumé", variant="primary")
                    summary_output = gr.Markdown(value="*Cliquez sur le bouton pour générer le résumé.*")
                    summary_btn.click(fn=generate_summary_callback, outputs=[summary_output])

                # TAB 3 : QUIZ
                with gr.TabItem("❓ Quiz interactif"):
                    with gr.Row():
                        quiz_difficulty = gr.Radio(
                            ["easy", "medium", "hard"], value="medium", label="Niveau"
                        )
                        quiz_num = gr.Slider(3, 20, value=8, step=1, label="Nombre de questions")
                    quiz_gen_btn = gr.Button("❓ Générer le Quiz", variant="primary")

                    quiz_question = gr.Textbox(label="Question en cours", lines=3, interactive=False)
                    quiz_options = gr.Radio(choices=[], label="Choisissez une réponse", visible=False)
                    quiz_submit = gr.Button("✅ Valider", visible=False, variant="primary")
                    quiz_feedback = gr.Textbox(label="Résultat", lines=3, interactive=False)

                    quiz_gen_btn.click(
                        fn=generate_quiz_callback,
                        inputs=[quiz_difficulty, quiz_num],
                        outputs=[quiz_question, quiz_options],
                    )
                    quiz_submit.click(
                        fn=submit_quiz_answer,
                        inputs=[quiz_options],
                        outputs=[quiz_feedback, quiz_question, quiz_options, quiz_submit],
                    )
                    quiz_options.change(lambda x: gr.update(visible=True), inputs=[quiz_options], outputs=[quiz_submit])

                # TAB 4 : FLASHCARDS
                with gr.TabItem("🃏 Flashcards"):
                    fc_num = gr.Slider(5, 30, value=12, step=1, label="Nombre de flashcards")
                    fc_gen_btn = gr.Button("🃏 Générer les Flashcards", variant="primary")
                    fc_output = gr.Textbox(label="Cartes générées", lines=15, interactive=False)

                    fc_gen_btn.click(
                        fn=generate_flashcards_callback,
                        inputs=[fc_num],
                        outputs=[fc_output],
                    )

                # TAB 5 : PLANNING
                with gr.TabItem("📅 Planning de révision"):
                    with gr.Row():
                        pl_days = gr.Slider(1, 30, value=7, step=1, label="Jours avant l'examen")
                        pl_hours = gr.Slider(0.5, 8, value=2, step=0.5, label="Heures/jour")
                        pl_diff = gr.Radio(["easy", "medium", "hard"], value="medium", label="Difficulté")
                    pl_btn = gr.Button("📅 Générer le Planning", variant="primary")
                    pl_output = gr.Markdown(value="*Configurez les paramètres et générez votre planning.*")
                    pl_btn.click(
                        fn=generate_planner_callback,
                        inputs=[pl_days, pl_hours, pl_diff],
                        outputs=[pl_output],
                    )


    gr.Markdown("""
    ---
    **StudyMate AI** | LangChain + Groq | Tools: PDF Reader · Quiz Generator · Flashcard Generator · Study Planner
    """)


# ═══════════════════════════════════════════════
# LANCEMENT
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    print("""
+--------------------------------------+
|        [+] StudyMate AI              |
|   Intelligent Learning Assistant     |
+--------------------------------------+
|  Tools   : 4 (PDF, Quiz, FC, Plan)   |
|  Agent   : LangChain ReAct           |
|  LLM     : Groq Llama 3.3            |
|  Frontend: Gradio                    |
+--------------------------------------+

Demarrage de l'interface...
""")
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,        # Mettre True pour un lien public temporaire
        show_error=True,
        favicon_path=None,
    )