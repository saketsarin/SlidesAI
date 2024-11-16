from nltk.tokenize import sent_tokenize
import nltk

class TextProcessor:
    @staticmethod
    def initialize():
        nltk.download('punkt', quiet=True)
    
    @staticmethod
    def summarize_long_content(text, max_sentences=3):
        """Summarize long content using NLTK"""
        try:
            sentences = sent_tokenize(text)
            if len(sentences) <= max_sentences:
                return text
            return ' '.join(sentences[:max_sentences])
        except Exception:
            return text