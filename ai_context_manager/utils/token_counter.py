"""Token counting utilities for AI Context Manager."""

import re
from typing import Optional


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Estimate the number of tokens in a text string.
    
    This is a rough approximation using the rule of thumb that:
    - 1 token ≈ 4 characters for English text
    - 1 token ≈ ¾ words
    
    Args:
        text: The text to count tokens for
        model: The AI model to estimate for (currently only used for logging)
    
    Returns:
        Estimated number of tokens
    """
    if not text:
        return 0
    
    # Simple approximation: 1 token ≈ 4 characters
    char_count = len(text)
    token_estimate = char_count // 4
    
    # More refined approximation for code
    if _is_likely_code(text):
        # Code tends to have more tokens due to symbols and structure
        token_estimate = int(char_count * 0.35)  # ~2.85 chars per token
    
    # Count words as additional check
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    word_based_estimate = int(word_count * 1.3)  # ~0.75 words per token
    
    # Take the average of character and word estimates
    final_estimate = max(token_estimate, word_based_estimate)
    
    return max(1, int(final_estimate))


def _is_likely_code(text: str) -> bool:
    """Determine if text is likely to be source code."""
    code_indicators = [
        r'\b(def|function|class|import|from|const|let|var)\b',
        r'[{}()\[\];]',
        r'//|/\*|#|"""|\'\'\'',
        r'\b(if|else|for|while|return|try|catch)\b',
    ]
    
    indicator_count = 0
    for pattern in code_indicators:
        if re.search(pattern, text):
            indicator_count += 1
    
    # If we find multiple code indicators, it's probably code
    return indicator_count >= 2


def format_token_count(tokens: int) -> str:
    """Format token count for human readability."""
    if tokens < 1000:
        return f"{tokens} tokens"
    elif tokens < 1000000:
        return f"{tokens / 1000:.1f}k tokens"
    else:
        return f"{tokens / 1000000:.1f}M tokens"


def get_token_limits(model: str = "gpt-4") -> dict:
    """Get token limits for different AI models."""
    limits = {
        "gpt-3.5-turbo": {
            "max_input": 4096,
            "max_output": 4096,
            "max_total": 4096
        },
        "gpt-4": {
            "max_input": 8192,
            "max_output": 8192,
            "max_total": 8192
        },
        "gpt-4-turbo": {
            "max_input": 128000,
            "max_output": 4096,
            "max_total": 128000
        },
        "gpt-4o": {
            "max_input": 128000,
            "max_output": 4096,
            "max_total": 128000
        },
        "claude-3-haiku": {
            "max_input": 200000,
            "max_output": 4096,
            "max_total": 200000
        },
        "claude-3-sonnet": {
            "max_input": 200000,
            "max_output": 4096,
            "max_total": 200000
        },
        "claude-3-opus": {
            "max_input": 200000,
            "max_output": 4096,
            "max_total": 200000
        },
        "claude-3.5-sonnet": {
            "max_input": 200000,
            "max_output": 8192,
            "max_total": 200000
        },
    }
    
    return limits.get(model, limits["gpt-4"])


def check_token_limits(tokens: int, model: str = "gpt-4") -> dict:
    """Check if token count is within model limits."""
    limits = get_token_limits(model)
    
    is_within_limits = tokens <= limits["max_input"]
    percentage = (tokens / limits["max_input"]) * 100
    
    return {
        "is_within_limits": is_within_limits,
        "percentage": percentage,
        "tokens": tokens,
        "limit": limits["max_input"],
        "model": model,
        "warning": f"{percentage:.1f}% of {model} limit" if not is_within_limits else None
    }


def estimate_context_size(files: list, base_path: str = None) -> dict:
    """
    Estimate the total token count for a list of files.
    
    Args:
        files: List of file paths or file objects
        base_path: Base directory path for relative paths
    
    Returns:
        Dictionary with token estimates and file information
    """
    from pathlib import Path
    
    total_tokens = 0
    file_info = []
    
    for file_item in files:
        if isinstance(file_item, (str, Path)):
            file_path = Path(file_item)
            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    tokens = count_tokens(content)
                    total_tokens += tokens
                    
                    file_info.append({
                        "path": str(file_path),
                        "tokens": tokens,
                        "size": file_path.stat().st_size
                    })
                except (UnicodeDecodeError, OSError):
                    # Skip binary files or files that can't be read
                    continue
        else:
            # Handle file objects with content
            content = str(file_item)
            tokens = count_tokens(content)
            total_tokens += tokens
            
            file_info.append({
                "tokens": tokens,
                "size": len(content.encode('utf-8'))
            })
    
    return {
        "total_tokens": total_tokens,
        "total_formatted": format_token_count(total_tokens),
        "files": file_info,
        "model_warnings": {
            "gpt-4": check_token_limits(total_tokens, "gpt-4"),
            "gpt-4-turbo": check_token_limits(total_tokens, "gpt-4-turbo"),
            "claude-3.5-sonnet": check_token_limits(total_tokens, "claude-3.5-sonnet"),
        }
    }