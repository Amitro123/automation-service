"""Configuration management for GitHub Automation Agent."""

import os
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # GitHub Configuration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    REPOSITORY_OWNER: str = os.getenv("REPOSITORY_OWNER", "")
    REPOSITORY_NAME: str = os.getenv("REPOSITORY_NAME", "")

    # LLM Configuration (supports both OpenAI and Anthropic)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # "openai", "anthropic", "gemini"
    LLM_MODEL: str = os.getenv(
        "LLM_MODEL",
        "gpt-4-turbo-preview" if LLM_PROVIDER == "openai" else
        ("claude-3-opus-20240229" if LLM_PROVIDER == "anthropic" else "gemini-2.0-flash")
    )

    # Review Provider Configuration
    REVIEW_PROVIDER: str = os.getenv("REVIEW_PROVIDER", "llm").lower()  # "llm" or "jules"
    JULES_API_KEY: Optional[str] = os.getenv("JULES_API_KEY")
    JULES_API_URL: str = os.getenv("JULES_API_URL", "https://jules.googleapis.com/v1alpha")
    JULES_SOURCE_ID: Optional[str] = os.getenv("JULES_SOURCE_ID")  # e.g., "sources/github/owner/repo"
    JULES_PROJECT_ID: Optional[str] = os.getenv("JULES_PROJECT_ID")  # Optional project ID

    # Webhook Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")  # nosec
    PORT: int = int(os.getenv("PORT", "8080"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Automation Behavior
    CREATE_PR: bool = os.getenv("CREATE_PR", "True").lower() == "true"
    POST_REVIEW_AS_ISSUE: bool = os.getenv("POST_REVIEW_AS_ISSUE", "False").lower() == "true"
    AUTO_COMMIT: bool = os.getenv("AUTO_COMMIT", "False").lower() == "true"
    ARCHITECTURE_FILE: str = os.getenv("ARCHITECTURE_FILE", "ARCHITECTURE.md")

    # Mutation Testing Configuration
    ENABLE_MUTATION_TESTS: bool = os.getenv("ENABLE_MUTATION_TESTS", "False").lower() == "true"
    MUTATION_MAX_RUNTIME_SECONDS: int = int(os.getenv("MUTATION_MAX_RUNTIME_SECONDS", "600"))
    MUTATION_MIN_DIFF_LINES: int = int(os.getenv("MUTATION_MIN_DIFF_LINES", "10"))

    # PR-Centric Trigger Configuration
    # TRIGGER_MODE: "pr" = PR events only, "push" = push events only, "both" = both
    TRIGGER_MODE: str = os.getenv("TRIGGER_MODE", "both").lower()
    ENABLE_PR_TRIGGER: bool = os.getenv("ENABLE_PR_TRIGGER", "True").lower() == "true"
    ENABLE_PUSH_TRIGGER: bool = os.getenv("ENABLE_PUSH_TRIGGER", "True").lower() == "true"

    # Trivial Change Filter Configuration
    TRIVIAL_CHANGE_FILTER_ENABLED: bool = os.getenv("TRIVIAL_CHANGE_FILTER_ENABLED", "True").lower() == "true"
    TRIVIAL_MAX_LINES: int = int(os.getenv("TRIVIAL_MAX_LINES", "10"))
    # Comma-separated list of glob patterns for doc files
    TRIVIAL_DOC_PATHS: List[str] = [
        p.strip() for p in os.getenv(
            "TRIVIAL_DOC_PATHS",
            "README.md,*.md,docs/**,CHANGELOG.md,CONTRIBUTING.md,LICENSE"
        ).split(",") if p.strip()
    ]

    # PR-Centric Automation Behavior
    # Group automation updates into single PR per source PR
    GROUP_AUTOMATION_UPDATES: bool = os.getenv("GROUP_AUTOMATION_UPDATES", "True").lower() == "true"
    # Post code review as PR comment instead of commit comment when triggered by PR
    POST_REVIEW_ON_PR: bool = os.getenv("POST_REVIEW_ON_PR", "True").lower() == "true"

    # Gemini Rate Limiting Configuration
    # Maximum requests per minute for Gemini API (free tier: 15 RPM)
    GEMINI_MAX_RPM: int = int(os.getenv("GEMINI_MAX_RPM", "10"))
    # Minimum delay between consecutive Gemini API calls (seconds)
    GEMINI_MIN_DELAY_SECONDS: float = float(os.getenv("GEMINI_MIN_DELAY_SECONDS", "2.0"))
    # Maximum concurrent Gemini requests (optional hard cap)
    GEMINI_MAX_CONCURRENT_REQUESTS: int = int(os.getenv("GEMINI_MAX_CONCURRENT_REQUESTS", "3"))

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
    def get_config_summary(cls) -> dict:
        """Get a summary of current configuration for debugging.
        
        Returns:
            dict: Configuration summary with masked sensitive values
        """
        return {
            "repository": f"{cls.REPOSITORY_OWNER}/{cls.REPOSITORY_NAME}",
            "llm_provider": cls.LLM_PROVIDER,
            "llm_model": cls.LLM_MODEL,
            "review_provider": cls.REVIEW_PROVIDER,
            "trigger_mode": cls.TRIGGER_MODE,
            "auto_commit": cls.AUTO_COMMIT,
            "create_pr": cls.CREATE_PR,
            "trivial_filter_enabled": cls.TRIVIAL_CHANGE_FILTER_ENABLED,
        }

    @classmethod
    def get_repo_full_name(cls) -> str:
        """Get full repository name in owner/repo format."""
        return f"{cls.REPOSITORY_OWNER}/{cls.REPOSITORY_NAME}"