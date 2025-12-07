"""
PDF Processor - Extraction et chunking avec nettoyage intelligent
Traite les PDFs et les prépare pour l'indexation
Gère les documents scientifiques avec références
"""
import fitz  # PyMuPDF
from typing import List, Dict, Tuple
import os
import re

class PDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Patterns pour détecter les références bibliographiques
        self.reference_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\(\d{4}\)',  # (2023), (2024), etc.
            r'et al\.',  # et al.
            r'\bet\s+al\b',  # et al sans point
            r'doi:\s*\S+',  # DOI
            r'https?://\S+',  # URLs
        ]

        # Pattern pour détecter les sections de références
        self.reference_section_markers = [
            r'^references\s*$',
            r'^bibliography\s*$',
            r'^works cited\s*$',
            r'^literature cited\s*$',
        ]
    
    def process_pdf(self, pdf_path: str, filename: str) -> Dict:
        """Extrait le texte et crée des chunks avec nettoyage intelligent"""

        # Ouvre le PDF
        doc = fitz.open(pdf_path)

        chunks = []
        metadatas = []
        total_pages = len(doc)

        # Extrait et nettoie le texte page par page
        in_references_section = False

        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()

            # Nettoie le texte (headers, footers, metadata)
            cleaned_text = self._clean_text(text)

            # Détecte si on entre dans la section références
            if self._is_reference_section_start(cleaned_text):
                in_references_section = True
                print(f"📚 Detected references section at page {page_num + 1}")

            # Skip les pages de références pures
            if in_references_section and self._is_mostly_references(cleaned_text):
                print(f"⏭️  Skipping references page {page_num + 1}")
                continue

            # Allège les références inline sans les supprimer complètement
            cleaned_text = self._reduce_inline_references(cleaned_text)

            # Découpe en chunks sémantiques avec overlap
            page_chunks = self._create_semantic_chunks(cleaned_text)

            for chunk in page_chunks:
                if len(chunk.strip()) > 100:  # Évite les chunks trop courts
                    chunks.append(chunk)
                    metadatas.append({
                        "filename": filename,
                        "page": page_num + 1,
                        "total_pages": total_pages,
                        "in_references": in_references_section
                    })

        doc.close()

        print(f"✓ Processed {total_pages} pages → {len(chunks)} chunks")

        return {
            "filename": filename,
            "total_pages": total_pages,
            "chunks": chunks,
            "metadatas": metadatas
        }
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte des headers, footers et métadonnées"""
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip les lignes vides ou très courtes
            if len(line.strip()) < 3:
                continue

            # Skip les numéros de page isolés
            if re.match(r'^\d+\s*$', line.strip()):
                continue

            # Skip les headers/footers typiques (dates, copyright, etc.)
            if re.search(r'copyright|©|\d{4}\s+[A-Z][a-z]+|\bpage\s+\d+', line, re.IGNORECASE):
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _is_reference_section_start(self, text: str) -> bool:
        """Détecte le début d'une section de références"""
        first_lines = text.lower().split('\n')[:5]  # Vérifie les 5 premières lignes
        for line in first_lines:
            for pattern in self.reference_section_markers:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    return True
        return False

    def _is_mostly_references(self, text: str) -> bool:
        """Détermine si une page est principalement des références"""
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 10]
        if not lines:
            return False

        # Compte les lignes qui ressemblent à des références
        ref_count = 0
        for line in lines:
            # Ligne commence par un numéro ou contient beaucoup de patterns de référence
            # Aussi détecte les formats de références académiques (numéro + tab + auteurs)
            if (re.match(r'^\[\d+\]|^\d+\.|\t\d+\.', line) or
                sum(1 for p in self.reference_patterns if re.search(p, line)) >= 2 or
                re.search(r'\d{4}\)\.|\(\d{4}\)', line)):  # Années entre parenthèses typiques
                ref_count += 1

        # Si plus de 50% des lignes sont des références, skip la page
        return ref_count / len(lines) > 0.5

    def _reduce_inline_references(self, text: str) -> str:
        """Allège les références inline sans les supprimer complètement"""
        # Remplace les multiples citations [1,2,3,4,5] par [1-5]
        text = re.sub(r'\[(\d+),\s*\d+(?:,\s*\d+)+\]', r'[citations]', text)

        # Simplifie les longues listes d'auteurs "A et al., B et al., C et al." → "[multiple citations]"
        text = re.sub(r'(\w+\s+et al\.\s*,\s*){3,}', '[multiple citations] ', text)

        # Réduit les URLs longues
        text = re.sub(r'https?://[^\s]{50,}', '[URL]', text)

        return text

    def _create_semantic_chunks(self, text: str) -> List[str]:
        """Découpe le texte en chunks sémantiques (par paragraphes)"""
        # Split par double newline (paragraphes)
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Si ajouter ce paragraphe dépasse la taille, on crée un nouveau chunk
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Garde un overlap en gardant la dernière phrase du chunk précédent
                last_sentences = self._get_last_sentences(current_chunk, self.chunk_overlap)
                current_chunk = last_sentences + "\n\n" + para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Ajoute le dernier chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _get_last_sentences(self, text: str, max_length: int) -> str:
        """Récupère les dernières phrases d'un texte pour l'overlap"""
        sentences = re.split(r'[.!?]+\s+', text)
        result = ""
        for sentence in reversed(sentences):
            if len(result) + len(sentence) > max_length:
                break
            result = sentence + ". " + result
        return result.strip()

    def _create_chunks(self, text: str) -> List[str]:
        """Découpe le texte en chunks avec overlap (méthode legacy)"""

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            # Évite de couper au milieu d'un mot
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > self.chunk_size * 0.8:  # Si on trouve un espace dans les derniers 20%
                    end = start + last_space
                    chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk.strip())

            start = end - self.chunk_overlap

        return chunks

# Instance globale
pdf_processor = PDFProcessor()
