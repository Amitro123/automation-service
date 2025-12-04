"""Shared utilities for the automation agent."""

import logging
import json
from typing import Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def get_timestamp() -> str:
    """Get current timestamp in ISO format.
    
    Returns:
        ISO formatted timestamp string
    """
    return datetime.utcnow().isoformat() + "Z"

def setup_logging(level: int = logging.INFO) -> None:
    """Setup basic logging configuration.
    
    Args:
        level: Logging level
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_json_safe(json_str: str) -> Dict[str, Any]:
    """Safely parse JSON string.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Parsed dictionary or empty dict on failure
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return {}

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to a maximum length with a custom suffix.
    
    Args:
        text: The string to truncate
        max_length: Maximum length (default 100)
        suffix: Suffix to append when truncated (default "...")
        
    Returns:
        Truncated string with suffix if it was shortened
        
    Example:
        >>> truncate_string("Hello World", 8)
        'Hello...'
    """
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
