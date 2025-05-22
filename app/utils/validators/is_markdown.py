import mistune
import re
from typing import Optional

def contains_markdown_indicators(text: str) -> bool:
    """
    Check if the text contains common markdown indicators.
    
    Args:
        text (str): Text to check for markdown indicators
        
    Returns:
        bool: True if any markdown indicators are found
    """
    # Common markdown patterns to check for
    markdown_patterns = [
        r'^#\s+',  # Headers
        r'\*\*[^*]+\*\*',  # Bold
        r'\*[^*]+\*',  # Italics
        r'`[^`]+`',  # Inline code
        r'```[\s\S]+?```',  # Code blocks
        r'\[[^\]]+\]\([^)]+\)',  # Links
        r'!\[[^\]]+\]\([^)]+\)',  # Images
        r'^[\s]*[-*+]\s+',  # Unordered lists
        r'^[\s]*\d+\.\s+',  # Ordered lists
        r'^>\s+',  # Blockquotes
        r'\~\~[^~]+\~\~',  # Strikethrough
        r'_{2}[^_]+_{2}',  # Underline (some markdown variants)
        r'\|.*\|.*\|',  # Tables
        r'^---[\s\S]*?---',  # Front matter
    ]
    
    return any(re.search(pattern, text, re.MULTILINE) for pattern in markdown_patterns)

def is_markdown(text: Optional[str]) -> bool:
    """
    Determine if the given text is markdown.
    
    Args:
        text (Optional[str]): Text to check for markdown formatting
    
    Returns:
        bool: True if the text appears to be markdown, False otherwise
    """
    # Handle None or empty string cases
    if not text or not text.strip():
        return False
    
    # First check for explicit markdown indicators
    if not contains_markdown_indicators(text):
        return False
    
    # If we found indicators, validate it's proper markdown
    try:
        markdown = mistune.create_markdown()
        parsed = markdown(text)
        return bool(parsed.strip())
    except Exception:
        return False
