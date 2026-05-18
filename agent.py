"""
StudyMate AI — Agent Core
Agent LangChain avec raisonnement multi-étapes.
Orchestre les 4 tools pour analyser un cours et produire tous les livrables.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, SystemMessage

from tools import (
    ALL_TOOLS,
    extract_text_from_pdf,
    quiz_tool_standalone,
    flashcard_tool_standalone,
    planner_tool_standalone,
)

load_dotenv()


# ─────────────────────────────────────────────
# PROMPT SYSTÈME DE L'AGENT (ReAct)
# ─────────────────────────────────────────────

AGENT_SYSTEM_PROMPT = """Tu es StudyMate AI, un assistant pédagogique intelligent pour étudiants universitaires.
Tu raisonnes étape par étape avant d'agir, en utilisant les outils disponibles.

OUTILS DISPONIBLES :
{tools}

NOMS DES OUTILS : {tool_names}

RÈGLE DE RAISONNEMENT (ReAct) :
Thought: Je réfléchis à ce que l'étudiant a besoin
Action: [nom_de_l_outil]
Action Input: [paramètres de l'outil]
Observation: [résultat de l'outil]
... (répéter si nécessaire)
Thought: J'ai maintenant toutes les informations nécessaires
Final Answer: [réponse complète et structurée]

COMPORTEMENT :
- Toujours analyser d'abord le cours avant de générer du contenu
- Adapter le niveau de difficulté aux besoins de l'étudiant
- Être pédagogique, encourageant et précis
- Répondre en français sauf si l'utilisateur écrit en anglais
- Pour chaque question sur le cours, citer les concepts pertinents

Question de l'étudiant : {input}

Historique : {agent_scratchpad}
"""

AGENT_PROMPT = PromptTemplate.from_template(AGENT_SYSTEM_PROMPT)


# ─────────────────────────────────────────────
# CLASSE AGENT PRINCIPAL
# ─────────────────────────────────────────────

class StudyMateAgent:
    """
    Agent LangChain principal.
    Gère le raisonnement multi-étapes et l'orchestration des tools.
    """

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "❌ GOOGLE_API_KEY manquante !\n"
                "1. Copiez .env.example en .env\n"
                "2. Ajoutez votre clé API Gemini"
            )

        # LLM Gemini (gratuit pour étudiants)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            google_api_key=api_key,
            temperature=0.3,         # Précision > créativité pour le contenu pédagogique
            max_output_tokens=4096,
        )

        # Mémoire de conversation (fenêtre de 5 échanges)
        self.memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=True,
        )

        # Agent ReAct avec tous les tools
        self.agent = create_react_agent(
            llm=self.llm,
            tools=ALL_TOOLS,
            prompt=AGENT_PROMPT,
        )

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=ALL_TOOLS,
            memory=self.memory,
            verbose=True,           # Affiche le raisonnement step-by-step
            max_iterations=6,       # Max 6 étapes de raisonnement
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

        # Contexte du cours chargé
        self.course_text = ""
        self.course_filename = ""

    # ─── CHARGEMENT DU PDF ───────────────────

    def load_pdf(self, pdf_path: str) -> dict:
        """
        Étape 1 : Lit le PDF et stocke le texte en mémoire.
        Retourne les métadonnées du document.
        """
        result = extract_text_from_pdf(pdf_path)

        if "error" in result:
            return {"success": False, "message": result["error"]}

        self.course_text = result["full_text"]
        self.course_filename = result["filename"]

        return {
            "success": True,
            "filename": result["filename"],
            "pages": result["total_pages"],
            "words": result["word_count"],
            "chapters": result["chapters_detected"],
            "message": f"✅ Cours chargé : {result['filename']} ({result['total_pages']} pages, {result['word_count']:,} mots)"
        }

    # ─── GÉNÉRATION RÉSUMÉ ───────────────────

    def generate_summary(self) -> str:
        """
        Étape 2 : Génère un résumé structuré du cours.
        Multi-step : analyse → extraction → résumé
        """
        if not self.course_text:
            return "❌ Chargez d'abord un PDF."

        prompt = f"""Analyse ce cours universitaire et génère un résumé structuré complet :

{self.course_text[:10000]}

STRUCTURE REQUISE :
## 🎯 Vue d'ensemble
(2-3 phrases résumant le cours)

## 📚 Concepts clés
(Liste des 5-8 notions fondamentales avec définitions)

## 📖 Résumé par chapitre/section
(Pour chaque section identifiée)

## ⚠️ Points importants à retenir
(Ce qui tombera probablement à l'examen)

## 🔗 Connexions entre concepts
(Comment les notions s'articulent)

Sois précis, pédagogique et complet."""

        response = self.llm.invoke(prompt)
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

    # ─── GÉNÉRATION QUIZ ─────────────────────

    def generate_quiz(self, difficulty: str = "medium", num_questions: int = 8, show_answers: bool = False) -> tuple:
        """
        Étape 3 : Génère un quiz QCM.
        Returns: (formatted_text, list_of_questions)
        """
        if not self.course_text:
            return "❌ Chargez d'abord un PDF.", []

        return quiz_tool_standalone(self.llm, self.course_text, difficulty, num_questions, show_answers)

    # ─── GÉNÉRATION FLASHCARDS ───────────────

    def generate_flashcards(self, num_cards: int = 12) -> tuple:
        """
        Étape 4 : Génère des flashcards.
        Returns: (formatted_text, list_of_cards)
        """
        if not self.course_text:
            return "❌ Chargez d'abord un PDF.", []

        return flashcard_tool_standalone(self.llm, self.course_text, num_cards)

    # ─── GÉNÉRATION PLANNING ─────────────────

    def generate_planner(
        self,
        days: int = 7,
        hours_per_day: float = 2.0,
        difficulty: str = "medium"
    ) -> str:
        """
        Étape 5 : Génère un planning de révision personnalisé.
        """
        if not self.course_text:
            return "❌ Chargez d'abord un PDF."

        return planner_tool_standalone(self.llm, self.course_text, days, hours_per_day, difficulty)

    # ─── CHAT AVEC LE COURS ──────────────────

    def chat(self, user_message: str) -> str:
        """
        Chat interactif avec contexte du cours.
        L'agent raisonne en plusieurs étapes si nécessaire.
        """
        if not self.course_text:
            # Sans PDF, répondre en mode général
            response = self.llm.invoke([
                SystemMessage(content="Tu es StudyMate AI, assistant pédagogique. Réponds en français."),
                HumanMessage(content=user_message)
            ])
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

        # Avec PDF : répondre avec contexte du cours
        contextualized_prompt = f"""Tu es StudyMate AI. L'étudiant a chargé le cours : "{self.course_filename}"

CONTENU DU COURS (contexte) :
{self.course_text[:6000]}

QUESTION DE L'ÉTUDIANT :
{user_message}

Réponds de manière précise en t'appuyant sur le cours. 
Si la question dépasse le cours, indique-le clairement.
Sois pédagogique et utilise des exemples concrets."""

        try:
            # Tenter avec l'agent ReAct (raisonnement multi-étapes)
            result = self.executor.invoke({"input": contextualized_prompt})
            return result.get("output", "Désolé, je n'ai pas pu traiter votre demande.")
        except Exception:
            # Fallback : appel direct au LLM
            response = self.llm.invoke(contextualized_prompt)
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

    # ─── ANALYSE COMPLÈTE AUTOMATIQUE ────────

    def full_analysis(self, difficulty: str = "medium", days: int = 7, hours: float = 2.0) -> dict:
        """
        Pipeline complet d'analyse automatique.
        L'agent effectue toutes les étapes en séquence :
        PDF → Résumé → Quiz → Flashcards → Planning
        """
        if not self.course_text:
            return {"error": "Chargez d'abord un PDF."}

        results = {}

        print("[+] Etape 1/4 : Generation du resume...")
        results["summary"] = self.generate_summary()

        print("[+] Etape 2/4 : Generation du quiz...")
        results["quiz_text"], results["quiz_data"] = self.generate_quiz(difficulty)

        print("[+] Etape 3/4 : Generation des flashcards...")
        results["flashcards_text"], results["flashcards_data"] = self.generate_flashcards()

        print("[+] Etape 4/4 : Generation du planning...")
        results["planner"] = self.generate_planner(days, hours, difficulty)

        print("[+] Analyse complete terminee !")
        return results
