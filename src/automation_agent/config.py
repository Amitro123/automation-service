"""Configuration management for GitHub Automation Agent."""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class ConfigMeta(type):
    """Metaclass to allow class-level properties for Config."""
    
    @property
    def GITHUB_TOKEN(cls) -> str: return cls._get("GITHUB_TOKEN", "")
    @property
    def GITHUB_WEBHOOK_SECRET(cls) -> str: return cls._get("GITHUB_WEBHOOK_SECRET", "")
    @property
    def REPOSITORY_OWNER(cls) -> str: return cls._get("REPOSITORY_OWNER", "")
    @property
    def REPOSITORY_NAME(cls) -> str: return cls._get("REPOSITORY_NAME", "")

    # LLM Configuration
    @property
    def OPENAI_API_KEY(cls) -> Optional[str]: return cls._get("OPENAI_API_KEY")
    @property
    def ANTHROPIC_API_KEY(cls) -> Optional[str]: return cls._get("ANTHROPIC_API_KEY")
    @property
    def GEMINI_API_KEY(cls) -> Optional[str]: return cls._get("GEMINI_API_KEY")
    @property
    def LLM_PROVIDER(cls) -> str: return cls._get("LLM_PROVIDER", "openai")
    
    @property
    def LLM_MODEL(cls) -> str:
        default_model = "gpt-4-turbo-preview" if cls.LLM_PROVIDER == "openai" else \
                       ("claude-3-opus-20240229" if cls.LLM_PROVIDER == "anthropic" else "gemini-2.0-flash")
        return cls._get("LLM_MODEL", default_model)

    # Review Provider Configuration
    @property
    def REVIEW_PROVIDER(cls) -> str: return cls._get("REVIEW_PROVIDER", "llm").lower()
    @property
    def JULES_API_KEY(cls) -> Optional[str]: return cls._get("JULES_API_KEY")
    @property
    def JULES_API_URL(cls) -> str: return cls._get("JULES_API_URL", "https://jules.googleapis.com/v1alpha")
    @property
    def JULES_SOURCE_ID(cls) -> Optional[str]: return cls._get("JULES_SOURCE_ID")
    @property
    def JULES_PROJECT_ID(cls) -> Optional[str]: return cls._get("JULES_PROJECT_ID")

    # Webhook Server Configuration
    @property
    def HOST(cls) -> str: return cls._get("HOST", "127.0.0.1")
    @property
    def PORT(cls) -> int: return cls._get_int("PORT", "8080")
    @property
    def DEBUG(cls) -> bool: return cls._get_bool("DEBUG", "False")

    # Automation Behavior
    @property
    def CREATE_PR(cls) -> bool: return cls._get_bool("CREATE_PR", "True")
    @property
    def POST_REVIEW_AS_ISSUE(cls) -> bool: return cls._get_bool("POST_REVIEW_AS_ISSUE", "False")
    @property
    def AUTO_COMMIT(cls) -> bool: return cls._get_bool("AUTO_COMMIT", "False")
    @property
    def ARCHITECTURE_FILE(cls) -> str: return cls._get("ARCHITECTURE_FILE", "ARCHITECTURE.md")

    # Mutation Testing Configuration
    @property
    def ENABLE_MUTATION_TESTS(cls) -> bool: return cls._get_bool("ENABLE_MUTATION_TESTS", "False")
    @property
    def MUTATION_MAX_RUNTIME_SECONDS(cls) -> int: return cls._get_int("MUTATION_MAX_RUNTIME_SECONDS", "600")
    @property
    def MUTATION_MIN_DIFF_LINES(cls) -> int: return cls._get_int("MUTATION_MIN_DIFF_LINES", "10")

    # PR-Centric Trigger Configuration
    @property
    def TRIGGER_MODE(cls) -> str: return cls._get("TRIGGER_MODE", "both").lower()
    @property
    def ENABLE_PR_TRIGGER(cls) -> bool: return cls._get_bool("ENABLE_PR_TRIGGER", "True")
    @property
    def ENABLE_PUSH_TRIGGER(cls) -> bool: return cls._get_bool("ENABLE_PUSH_TRIGGER", "True")

    # Trivial Change Filter Configuration
    @property
    def TRIVIAL_CHANGE_FILTER_ENABLED(cls) -> bool: return cls._get_bool("TRIVIAL_CHANGE_FILTER_ENABLED", "True")
    @property
    def TRIVIAL_MAX_LINES(cls) -> int: return cls._get_int("TRIVIAL_MAX_LINES", "10")
    @property
    def TRIVIAL_DOC_PATHS(cls) -> List[str]: 
        return cls._get_list("TRIVIAL_DOC_PATHS", "README.md,*.md,docs/**,CHANGELOG.md,CONTRIBUTING.md,LICENSE")

    # PR-Centric Automation Behavior
    @property
    def GROUP_AUTOMATION_UPDATES(cls) -> bool: return cls._get_bool("GROUP_AUTOMATION_UPDATES", "True")
    @property
    def POST_REVIEW_ON_PR(cls) -> bool: return cls._get_bool("POST_REVIEW_ON_PR", "True")

    # Gemini Rate Limiting Configuration
    @property
    def GEMINI_MAX_RPM(cls) -> int: return cls._get_int("GEMINI_MAX_RPM", "10")
    @property
    def GEMINI_MIN_DELAY_SECONDS(cls) -> float: return cls._get_float("GEMINI_MIN_DELAY_SECONDS", "2.0")
    @property
    def GEMINI_MAX_CONCURRENT_REQUESTS(cls) -> int: return cls._get_int("GEMINI_MAX_CONCURRENT_REQUESTS", "3")

    # Prompt Configuration
    @property
    def CODE_REVIEW_SYSTEM_PROMPT(cls) -> str:
        default = """You are an expert code reviewer. Analyze the following code changes (git diff) and provide a comprehensive review.

Instructions:
1. Analyze code quality, potential bugs, security issues, and performance.
2. Provide specific, actionable feedback.
3. Structure the review with clear headings (Strengths, Issues, Suggestions).
4. Be constructive and professional."""
        return cls._get("CODE_REVIEW_SYSTEM_PROMPT", default)
    
    @property
    def DOCS_UPDATE_SYSTEM_PROMPT(cls) -> str:
        default = """You are a technical documentation expert. Update the README.md based on the following code changes.

Instructions:
1. Identify new features, configuration changes, or usage updates from the diff.
2. Update the README to reflect these changes.
3. Return the FULL updated README content in markdown format.
4. Do not include any conversational text, just the markdown."""
        return cls._get("DOCS_UPDATE_SYSTEM_PROMPT", default)


class Config(metaclass=ConfigMeta):
    """Application configuration loaded from env vars and studioai.config.json."""

    # Config file path
    CONFIG_FILE = "studioai.config.json"
    _file_config: Dict[str, Any] = {}

    @classmethod
    def load_config_file(cls) -> Dict[str, Any]:
        """Load configuration from studioai.config.json."""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {cls.CONFIG_FILE}")
                    return config
            except Exception as e:
                logger.error(f"Failed to load {cls.CONFIG_FILE}: {e}")
        return {}

    @classmethod
    def load(cls):
        """Force reload of configuration."""
        cls._file_config = cls.load_config_file()

    @classmethod
    def _get(cls, key: str, default: Any = None) -> Any:
        """Get config value with precedence: Env > Config File > Default."""
        # 1. Environment Variable
        env_val = os.getenv(key)
        if env_val is not None:
            return env_val
        
        # 2. Config File
        if not cls._file_config:
            cls._file_config = cls.load_config_file()
        
        # Map env var keys to config file keys (lowercase usually)
        file_key = key.lower()
        if file_key in cls._file_config:
            return cls._file_config[file_key]
            
        # 3. Default
        return default

    @classmethod
    def _get_bool(cls, key: str, default: str) -> bool:
        """Get boolean value."""
        val = str(cls._get(key, default)).lower()
        return val == "true"

    @classmethod
    def _get_int(cls, key: str, default: str) -> int:
        """Get integer value."""
        return int(cls._get(key, default))
        
    @classmethod
    def _get_float(cls, key: str, default: str) -> float:
        """Get float value."""
        return float(cls._get(key, default))

    @classmethod
    def _get_list(cls, key: str, default: str) -> List[str]:
        """Get list from comma-separated string or list in json."""
        val = cls._get(key)
        if val is None:
            val = default
            
        if isinstance(val, list):
            return val
        
        return [p.strip() for p in str(val).split(",") if p.strip()]

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not cls.GITHUB_TOKEN:
            errors.append("GITHUB_TOKEN is required")
        if not cls.GITHUB_WEBHOOK_SECRET:
            errors.append("GITHUB_WEBHOOK_SECRET is required")
        if not cls.REPOSITORY_OWNER:
            errors.append("REPOSITORY_OWNER is required")
        if not cls.REPOSITORY_NAME:
            errors.append("REPOSITORY_NAME is required")

        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when using OpenAI")
        elif cls.LLM_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required when using Anthropic")
        elif cls.LLM_PROVIDER == "gemini" and not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required when using Gemini")
        elif cls.LLM_PROVIDER not in ["openai", "anthropic", "gemini"]:
            errors.append("LLM_PROVIDER must be 'openai', 'anthropic', or 'gemini'")

        if cls.REVIEW_PROVIDER == "jules":
            if not cls.JULES_API_KEY:
                errors.append("JULES_API_KEY is required when using Jules review provider")
            if not cls.JULES_SOURCE_ID:
                errors.append("JULES_SOURCE_ID is required when using Jules review provider (e.g., 'sources/github/owner/repo')")

        return errors

    @classmethod
    def get_repo_full_name(cls) -> str:
        """Get full repository name in owner/repo format."""
        return f"{cls.REPOSITORY_OWNER}/{cls.REPOSITORY_NAME}"