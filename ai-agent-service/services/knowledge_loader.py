"""
Knowledge Base Loader
Loads and indexes PDF files for AI agent responses
"""
import os
from typing import List, Dict, Optional
from pathlib import Path
import PyPDF2
import pdfplumber
from loguru import logger
from config.settings import settings


class KnowledgeBaseLoader:
    """Loader for PDF knowledge base files"""

    def __init__(self):
        self.knowledge_base_path = Path(settings.KNOWLEDGE_BASE_PATH)
        self.cache_enabled = settings.PDF_CACHE_ENABLED
        self.cached_content = {}

    def extract_text_from_pdf_pypdf2(self, file_path: Path) -> str:
        """Extract text using PyPDF2"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed for {file_path}: {e}")
            return ""

    def extract_text_from_pdf_pdfplumber(self, file_path: Path) -> str:
        """Extract text using pdfplumber (better for tables)"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"pdfplumber extraction failed for {file_path}: {e}")
            return ""

    def extract_text_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF file using best available method

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content
        """
        # Try pdfplumber first (better for tables and complex layouts)
        text = self.extract_text_from_pdf_pdfplumber(file_path)

        # Fallback to PyPDF2 if pdfplumber fails
        if not text or len(text) < 100:
            logger.warning(f"pdfplumber extracted minimal text, trying PyPDF2")
            text = self.extract_text_from_pdf_pypdf2(file_path)

        # Clean text
        text = self.clean_text(text)

        return text

    def clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = ' '.join(text.split())

        # Remove special characters that might interfere
        text = text.replace('\x00', '')

        return text.strip()

    def load_all_pdfs(self) -> Dict[str, str]:
        """
        Load all PDF files from knowledge base directory

        Returns:
            Dictionary mapping filename to content
        """
        if not self.knowledge_base_path.exists():
            logger.warning(f"Knowledge base path does not exist: {self.knowledge_base_path}")
            self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
            return {}

        pdf_files = list(self.knowledge_base_path.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {self.knowledge_base_path}")
            return {}

        logger.info(f"Found {len(pdf_files)} PDF files in knowledge base")

        all_content = {}

        for pdf_file in pdf_files:
            try:
                # Check cache
                if self.cache_enabled and pdf_file.name in self.cached_content:
                    logger.debug(f"Using cached content for {pdf_file.name}")
                    all_content[pdf_file.name] = self.cached_content[pdf_file.name]
                    continue

                # Extract text
                logger.info(f"Extracting text from {pdf_file.name}...")
                text = self.extract_text_from_pdf(pdf_file)

                if text:
                    all_content[pdf_file.name] = text
                    # Cache it
                    if self.cache_enabled:
                        self.cached_content[pdf_file.name] = text
                    logger.success(f"Loaded {pdf_file.name} ({len(text)} chars)")
                else:
                    logger.warning(f"No text extracted from {pdf_file.name}")

            except Exception as e:
                logger.error(f"Error loading {pdf_file.name}: {e}")

        return all_content

    def get_full_knowledge(self) -> str:
        """
        Get all knowledge base content as a single string

        Returns:
            Combined text from all PDFs
        """
        all_pdfs = self.load_all_pdfs()

        if not all_pdfs:
            return "База знаний пуста. Используй общие знания для ответа."

        # Combine all content
        combined = ""
        for filename, content in all_pdfs.items():
            combined += f"\n\n=== {filename} ===\n{content}"

        return combined.strip()

    def search_knowledge(self, query: str) -> str:
        """
        Search for relevant information in knowledge base

        Args:
            query: Search query

        Returns:
            Relevant text snippets
        """
        all_pdfs = self.load_all_pdfs()

        if not all_pdfs:
            return ""

        # Simple keyword search (can be enhanced with embeddings later)
        query_lower = query.lower()
        relevant_snippets = []

        for filename, content in all_pdfs.items():
            # Split content into sentences
            sentences = content.split('.')

            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in query_lower.split()):
                    relevant_snippets.append(sentence.strip())

        if relevant_snippets:
            return '. '.join(relevant_snippets[:5])  # Return top 5 relevant snippets

        # If no specific match, return first 500 chars of each document
        return self.get_full_knowledge()[:2000]

    def index_content(self) -> Dict[str, List[str]]:
        """
        Create simple index for quick search

        Returns:
            Dictionary mapping keywords to document names
        """
        all_pdfs = self.load_all_pdfs()
        index = {}

        for filename, content in all_pdfs.items():
            # Extract keywords (simple word-based)
            words = content.lower().split()
            unique_words = set(words)

            for word in unique_words:
                if len(word) > 4:  # Only index words longer than 4 chars
                    if word not in index:
                        index[word] = []
                    if filename not in index[word]:
                        index[word].append(filename)

        logger.info(f"Created index with {len(index)} keywords")
        return index
