# src/services/pdf_service.py
import os
import re
from pathlib import Path
from src.logger import setup_logger

logger = setup_logger(__name__)


class PDFService:
    @staticmethod
    def convert_to_pdf(txt_path: Path, pdf_path: Path):
        """Convertit un fichier texte en PDF en préservant la mise en forme."""
        try:
            from fpdf import FPDF
        except ImportError:
            logger.error("La bibliothèque fpdf n'est pas installée. Installez-la avec 'pip install fpdf'.")
            raise ImportError("fpdf is required for PDF export")

        # Lire le contenu texte
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier texte : {e}")
            raise

        # Nettoyer le contenu : remplacer les emojis et caractères non-latin1
        content = PDFService._sanitize_for_pdf(content)

        # Créer le PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Utiliser une police qui supporte plus de caractères
        # Tenter d'utiliser une police Unicode si disponible
        try:
            # Essayer d'utiliser fpdf2 avec une police Unicode
            from fpdf import FPDF

            # Vérifier si la version supporte les polices Unicode
            if hasattr(pdf, 'add_font') and PDFService._is_fpdf2():
                # FPDF2 (plus récent) supporte mieux Unicode
                pdf.set_font('Courier', size=8)
            else:
                # FPDF classique : utiliser une police standard
                pdf.set_font('Courier', size=8)
        except Exception:
            # Fallback
            pdf.set_font('Courier', size=8)

        # Découper en lignes et ajouter au PDF avec gestion des lignes trop longues
        lines = content.splitlines()
        for line in lines:
            # Tronquer les lignes trop longues pour éviter les débordements
            # La largeur de page est de 210mm, la marge à 10mm => 190mm disponibles
            # En police Courier 8, environ 6.5 caractères par mm => ~1235 caractères max
            if len(line) > 1200:
                # Découper la ligne en plusieurs morceaux
                chunks = [line[i:i+1200] for i in range(0, len(line), 1200)]
                for chunk in chunks:
                    pdf.cell(0, 5, txt=chunk, ln=True)
            else:
                try:
                    pdf.cell(0, 5, txt=line, ln=True)
                except UnicodeEncodeError:
                    # Si une ligne pose encore problème, on la nettoie plus agressivement
                    safe_line = PDFService._remove_non_latin1(line)
                    pdf.cell(0, 5, txt=safe_line, ln=True)

        pdf.output(str(pdf_path))
        logger.info(f"PDF généré : {pdf_path}")
        return pdf_path

    @staticmethod
    def _sanitize_for_pdf(content: str) -> str:
        """Remplace les emojis et caractères problématiques par des équivalents texte."""
        # Mapping des emojis Unicode vers des équivalents texte
        emoji_map = {
            '📁': '[DIR] ',
            '📄': '[FILE] ',
            '🐍': '[PY] ',
            '🌐': '[PO] ',
            '📦': '[MO] ',
            '📝': '[TXT] ',
            '🌍': '[HTML] ',
            '🎨': '[CSS] ',
            '⚡': '[JS] ',
            '├──': '├── ',
            '└──': '└── ',
            '│': '|',
            '✅': '[OK] ',
            '❌': '[ERR] ',
            '⚠️': '[WARN] ',
            '🔍': '[SRCH] ',
            '✓': '[OK] ',
            '✗': '[ERR] ',
            '→': '->',
            '☐': '☐',
            '☑': '☑',
            '◐': '◐',
        }

        # Remplacer les emojis
        for emoji, replacement in emoji_map.items():
            content = content.replace(emoji, replacement)

        # Supprimer les autres caractères non-latin1
        return PDFService._remove_non_latin1(content)

    @staticmethod
    def _remove_non_latin1(text: str) -> str:
        """Supprime les caractères qui ne sont pas encodables en latin-1."""
        # Définir l'ensemble des caractères valides en latin-1
        # (0x20 à 0x7E sont ASCII imprimables, 0xA0 à 0xFF sont étendus latin-1)
        def is_latin1_char(char):
            code = ord(char)
            # Lettres, chiffres, ponctuation ASCII
            if 0x20 <= code <= 0x7E:
                return True
            # Caractères étendus latin-1 (valides)
            if 0xA0 <= code <= 0xFF:
                return True
            # Tabulation et sauts de ligne
            if code in (0x09, 0x0A, 0x0D):
                return True
            return False

        # Remplacer les caractères invalides
        result = []
        for char in text:
            if is_latin1_char(char):
                result.append(char)
            else:
                # Remplacer par un caractère proche si possible
                replacement = PDFService._get_ascii_equivalent(char)
                if replacement:
                    result.append(replacement)
                else:
                    # Sinon, remplacer par '?'
                    result.append('?')

        return ''.join(result)

    @staticmethod
    def _get_ascii_equivalent(char: str) -> str:
        """Retourne un équivalent ASCII pour un caractère Unicode si possible."""
        equivalents = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c',
            'ñ': 'n',
            'œ': 'oe', 'æ': 'ae',
            '«': '"', '»': '"', '“': '"', '”': '"',
            '‘': "'", '’': "'",
            '–': '-', '—': '-',
            '…': '...',
        }
        return equivalents.get(char, None)

    @staticmethod
    def _is_fpdf2() -> bool:
        """Vérifie si fpdf2 est installé (version plus récente)."""
        try:
            from fpdf import FPDF
            # fpdf2 a la classe FPDF avec des fonctionnalités Unicode améliorées
            return hasattr(FPDF, 'add_font')
        except ImportError:
            return False