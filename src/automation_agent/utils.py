"""Shared utilities for GitHub Automation Agent."""

import logging
import re

logger = logging.getLogger(__name__)

def clean_markdown_code_block(text: str) -> str:
    """Remove markdown code block delimiters from text.

    Args:
        text: Input text potentially containing markdown code blocks

    Returns:
        Cleaned text
    """
    # Remove markdown code block wrappers if present
    text = re.sub(r'^```\w*\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```\s*$', '', text, flags=re.MULTILINE)
    return text.strip()
