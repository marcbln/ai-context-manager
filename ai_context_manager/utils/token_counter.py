"""Token counting utilities for AI Context Manager."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Union


class TokenCounter:
    """Token counter for estimating token usage in text files."""
    
    # Approximate token counts for common languages
    LANGUAGE_TOKEN_RATES = {
        'python': 0.7,
        'javascript': 0.8,
        'typescript': 0.8,
        'java': 0.7,
        'c': 0.6,
        'cpp': 0.7,
        'csharp': 0.7,
        'go': 0.7,
        'rust': 0.7,
        'php': 0.8,
        'ruby': 0.8,
        'html': 0.9,
        'css': 0.9,
        'json': 0.5,
        'yaml': 0.5,
        'xml': 0.9,
        'markdown': 0.8,
        'text': 0.75,
    }
    
    def __init__(self):
        """Initialize token counter."""
        pass
    
    def count_tokens(self, text: str, language: str = 'text') -> int:
        """Count tokens in text using language-specific rules.
        
        Args:
            text: Text to count tokens for.
            language: Language identifier for token rate adjustment.
            
        Returns:
            Estimated token count.
        """
        if not text:
            return 0
        
        # Clean text
        text = text.strip()
        if not text:
            return 0
        
        # Split into words and count
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        
        # Count special characters and symbols
        symbol_count = len(re.findall(r'[^\w\s]', text))
        
        # Count numbers
        number_count = len(re.findall(r'\b\d+\b', text))
        
        # Base token count
        base_tokens = word_count + symbol_count + (number_count * 0.5)
        
        # Apply language-specific rate
        rate = self.LANGUAGE_TOKEN_RATES.get(language.lower(), 0.75)
        estimated_tokens = int(base_tokens * rate)
        
        return max(1, estimated_tokens)
    
    def count_file_tokens(self, file_path: Union[str, Path], language: Optional[str] = None) -> int:
        """Count tokens in a file.
        
        Args:
            file_path: Path to the file.
            language: Language identifier (auto-detected if None).
            
        Returns:
            Estimated token count for the file.
        """
        file_path = Path(file_path)
        
        if not file_path.exists() or not file_path.is_file():
            return 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return 0
        
        if language is None:
            language = self.detect_language(file_path)
        
        return self.count_tokens(content, language)
    
    def count_directory_tokens(self, directory: Union[str, Path], 
                             include_patterns: List[str] = None,
                             exclude_patterns: List[str] = None) -> Dict[str, int]:
        """Count tokens for all files in a directory.
        
        Args:
            directory: Directory to scan.
            include_patterns: File patterns to include.
            exclude_patterns: File patterns to exclude.
            
        Returns:
            Dictionary mapping file paths to token counts.
        """
        from .file_utils import collect_files
        
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            return {}
        
        token_counts = {}
        
        # Collect all files
        files = collect_files(
            directory,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            recursive=True
        )
        
        for file_path in files:
            tokens = self.count_file_tokens(file_path)
            if tokens > 0:
                token_counts[str(file_path)] = tokens
        
        return token_counts
    
    def detect_language(self, file_path: Union[str, Path]) -> str:
        """Detect programming language from file extension.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Language identifier string.
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'css',
            '.sass': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.md': 'markdown',
            '.txt': 'text',
            '.sh': 'text',
            '.bash': 'text',
            '.zsh': 'text',
            '.fish': 'text',
            '.sql': 'text',
            '.dockerfile': 'text',
            '.cfg': 'text',
            '.ini': 'text',
            '.toml': 'text',
        }
        
        return language_map.get(extension, 'text')
    
    def get_total_tokens(self, token_counts: Dict[str, int]) -> int:
        """Get total token count from dictionary.
        
        Args:
            token_counts: Dictionary mapping file paths to token counts.
            
        Returns:
            Total token count.
        """
        return sum(token_counts.values())
    
    def estimate_cost(self, token_counts: Dict[str, int], 
                     model: str = 'gpt-4') -> Dict[str, float]:
        """Estimate API cost based on token count.
        
        Args:
            token_counts: Dictionary mapping file paths to token counts.
            model: AI model identifier.
            
        Returns:
            Dictionary with cost information.
        """
        total_tokens = self.get_total_tokens(token_counts)
        
        # Pricing per 1K tokens (as of 2024)
        pricing = {
            'gpt-4': 0.03,      # $0.03 per 1K tokens
            'gpt-3.5-turbo': 0.0015,  # $0.0015 per 1K tokens
            'claude-3-opus': 0.015,
            'claude-3-sonnet': 0.003,
            'gemini-pro': 0.0005,
        }
        
        rate = pricing.get(model, 0.03)
        estimated_cost = (total_tokens / 1000) * rate
        
        return {
            'total_tokens': total_tokens,
            'estimated_cost': estimated_cost,
            'model': model,
            'rate_per_1k': rate
        }


# Global instance for convenience
_default_counter = TokenCounter()

def count_tokens(text: str, language: str = 'text') -> int:
    """Convenience function to count tokens in text."""
    return _default_counter.count_tokens(text, language)

def count_file_tokens(file_path: Union[str, Path], language: Optional[str] = None) -> int:
    """Convenience function to count tokens in a file."""
    return _default_counter.count_file_tokens(file_path, language)

def count_directory_tokens(directory: Union[str, Path], 
                         include_patterns: List[str] = None,
                         exclude_patterns: List[str] = None) -> Dict[str, int]:
    """Convenience function to count tokens in directory."""
    return _default_counter.count_directory_tokens(directory, include_patterns, exclude_patterns)