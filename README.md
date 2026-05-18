# 🎓 StudyMate AI — Intelligent Learning Assistant

Un agent IA intelligent qui aide les étudiants à comprendre leurs cours,
générer des quiz, créer des flashcards et planifier leurs révisions.

---

## Architecture du projet

```
studymate-ai/
│
├── app.py              ← Interface Gradio (point d'entrée)
├── agent.py            ← Agent LangChain ReAct (raisonnement multi-étapes)
│
├── tools/
│   ├── __init__.py     ← Export de tous les tools
│   ├── pdf_reader.py   ← Tool 1 : Extraction PDF (PyMuPDF)
│   ├── quiz_tool.py    ← Tool 2 : Génération de QCM
│   ├── flashcard_tool.py ← Tool 3 : Génération de flashcards
│   └── planner_tool.py ← Tool 4 : Planning de révision intelligent
│
├── data/               ← PDFs uploadés temporairement
├── reports/            ← Exports générés (résumés, quiz...)
│
├── requirements.txt    ← Dépendances Python
├── .env                ← Template configuration API
└── README.md           ← Ce fichier
```

---

## Installation

### 1. Cloner le projet
```bash
git clone https://github.com/achref891/studymate-ai
cd studymate-ai
```

### 2. Créer l'environnement virtuel
```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate          # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer la clé API
```bash
cp .env.example .env
# Éditez .env et ajoutez votre GOOGLE_API_KEY
```

Obtenez une clé gratuite sur : https://aistudio.google.com/

### 5. Lancer l'application
```bash
python app.py
```

Ouvrez votre navigateur sur : **http://localhost:7860**

---

## Technologies utilisées

| Composant     | Technologie             | Rôle                            |
|---------------|-------------------------|---------------------------------|
| Frontend      | Gradio 4.x              | Interface utilisateur web       |
| Backend       | Python 3.10+            | Logique métier                  |
| Agent IA      | LangChain (ReAct)       | Raisonnement multi-étapes       |
| LLM           | Gemini 1.5 Flash        | Génération de contenu           |
| PDF           | PyMuPDF (fitz)          | Extraction de texte             |
| Vectorstore   | FAISS                   | Recherche sémantique (RAG)      |

---

## Les 4 Tools de l'Agent

### Tool 1 — PDF Reader (`tools/pdf_reader.py`)
- Lit les fichiers PDF page par page
- Détecte automatiquement les chapitres
- Retourne : texte complet, métadonnées, structure

### Tool 2 — Quiz Generator (`tools/quiz_tool.py`)
- Génère des QCM personnalisés (3-20 questions)
- 3 niveaux : easy, medium, hard
- Format JSON structuré avec explications

### Tool 3 — Flashcard Generator (`tools/flashcard_tool.py`)
- Crée des cartes Question/Réponse
- Catégorisation automatique par notion
- Mode session avec suivi "connu / à revoir"

### Tool 4 — Study Planner (`tools/planner_tool.py`)
- Planning jour par jour personnalisé
- Adapte selon les jours disponibles et heures/jour
- Calcule la répartition optimale des activités

---

## Raisonnement Multi-Étapes (ReAct)

L'agent suit ce processus automatique :

```
Étudiant : "J'ai un examen dans 3 jours sur les réseaux."
    │
    ▼
Thought : L'étudiant a besoin d'un plan complet
    │
    ├─ Action 1 : pdf_reader_tool → Extrait le cours
    ├─ Action 2 : quiz_generator_tool → Génère 8 QCM
    ├─ Action 3 : flashcard_generator_tool → 12 cartes
    └─ Action 4 : study_planner_tool → Planning 3 jours
    │
    ▼
Final Answer : Résumé + Quiz + Flashcards + Planning
```

---

## Fonctionnalités

- ✅ Upload PDF avec extraction automatique
- ✅ Résumé structuré par chapitre
- ✅ Quiz interactif avec score
- ✅ Flashcards avec mode session
- ✅ Planning de révision personnalisé
- ✅ Chat avec contexte du cours
- ✅ Analyse complète en un clic
- ✅ 3 niveaux de difficulté

---

## Auteurs

Projet réalisé dans le cadre d'un cours d'Intelligence Artificielle.
