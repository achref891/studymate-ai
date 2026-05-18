"""
Tool 1 — PDF Reader
Lit et extrait le texte d'un fichier PDF uploadé.
Utilise PyMuPDF (fitz) pour une extraction propre page par page.
"""

import fitz  # PyMuPDF
from langchain.tools import tool
from typing import Optional
import os


def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extrait le texte complet d'un PDF avec métadonnées.
    Retourne un dictionnaire avec le texte, le nombre de pages, et les chapitres détectés.
    """
    if not os.path.exists(pdf_path):
        return {"error": f"Fichier non trouvé : {pdf_path}"}

    try:
        doc = fitz.open(pdf_path)
        pages_text = []
        chapters = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            pages_text.append({
                "page": page_num + 1,
                "content": text.strip()
            })

            # Détection simple des chapitres (lignes courtes en majuscules ou numérotées)
            for line in text.split("\n"):
                line = line.strip()
                if line and len(line) < 80:
                    if (line.isupper() and len(line) > 5) or \
                       (line[:7].lower().startswith(("chapitre", "chapter", "partie", "section"))):
                        chapters.append({"page": page_num + 1, "title": line})

        full_text = "\n\n".join([p["content"] for p in pages_text if p["content"]])
        doc.close()

        return {
            "success": True,
            "filename": os.path.basename(pdf_path),
            "total_pages": len(pages_text),
            "word_count": len(full_text.split()),
            "chapters_detected": chapters,
            "full_text": full_text[:15000],  # Limite pour le contexte LLM
            "pages": pages_text
        }

    except Exception as e:
        return {"error": f"Erreur lecture PDF : {str(e)}"}


@tool
def pdf_reader_tool(pdf_path: str) -> str:
    """
    Lit un fichier PDF et retourne son contenu textuel structuré.
    Utilise pour extraire le cours avant toute autre opération.
    
    Args:
        pdf_path: Chemin complet vers le fichier PDF
        
    Returns:
        Texte extrait avec métadonnées (pages, chapitres, nombre de mots)
    """
    result = extract_text_from_pdf(pdf_path)

    if "error" in result:
        return f"❌ {result['error']}"

    output = f"""✅ PDF lu avec succès : {result['filename']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Pages        : {result['total_pages']}
📝 Mots         : {result['word_count']:,}
📚 Chapitres    : {len(result['chapters_detected'])} détectés
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHAPITRES DÉTECTÉS :
"""
    for ch in result["chapters_detected"]:
        output += f"  • Page {ch['page']} — {ch['title']}\n"

    output += f"\n\nCONTENU DU COURS :\n{result['full_text']}"
    return output
