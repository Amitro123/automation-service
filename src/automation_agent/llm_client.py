"""LLM client supporting OpenAI and Anthropic."""

import logging
from typing import Optional, Dict, Any
import os
import json

logger = logging.getLogger(__name__)


class LLMClient:
    """Universal LLM client supporting multiple providers."""

    def __init__(self, provider: str = "openai", model: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize LLM client.

        Args:
            provider: LLM provider ("openai" or "anthropic")
            model: Model name (optional, uses provider defaults)
            api_key: API key (optional, reads from environment)
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate LLM client."""
        if self.provider == "openai":
            self._initialize_openai()
        elif self.provider == "anthropic":
            self._initialize_anthropic()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _initialize_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import AsyncOpenAI
            self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")
            
            self._client = AsyncOpenAI(api_key=self.api_key)
            self.model = self.model or "gpt-4-turbo-preview"
            logger.info(f"Initialized AsyncOpenAI client with model {self.model}")
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

    def _initialize_anthropic(self):
        """Initialize Anthropic client."""
        try:
            from anthropic import AsyncAnthropic
            self.api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("Anthropic API key not provided")
            
            self._client = AsyncAnthropic(api_key=self.api_key)
            self.model = self.model or "claude-3-opus-20240229"
            logger.info(f"Initialized AsyncAnthropic client with model {self.model}")
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")

    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using the configured LLM.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)

        Returns:
            Generated text

        Raises:
            Exception: If generation fails
        """
        if self.provider == "openai":
            return await self._generate_openai(prompt, max_tokens, temperature)
        elif self.provider == "anthropic":
            return await self._generate_anthropic(prompt, max_tokens, temperature)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using OpenAI."""
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def _generate_anthropic(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using Anthropic."""
        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise

    async def analyze_code(self, diff: str) -> str:
        """Analyze code changes and provide a review.

        Args:
            diff: Git diff content

        Returns:
            Code review text
        """
        # Truncate diff if too long
        if len(diff) > 8000:
            diff = diff[:8000] + "\n\n[... diff truncated ...]"

        prompt = f"""You are an expert code reviewer. Analyze the following code changes (git diff) and provide a comprehensive review.

Code Changes:
```diff
{diff}
```

Instructions:
1. Analyze code quality, potential bugs, security issues, and performance.
2. Provide specific, actionable feedback.
3. Structure the review with clear headings (Strengths, Issues, Suggestions).
4. Be constructive and professional.

Review:"""
        return await self.generate(prompt, max_tokens=2000)

    async def update_readme(self, diff: str, current_readme: str) -> str:
        """Generate updates for README.md based on code changes.

        Args:
            diff: Git diff content
            current_readme: Current README content

        Returns:
            Updated README content
        """
        if len(diff) > 8000:
            diff = diff[:8000] + "\n\n[... diff truncated ...]"

        prompt = f"""You are a technical documentation expert. Update the README.md based on the following code changes.

Code Changes:
```diff
{diff}
```

Current README:
```markdown
{current_readme}
```

Instructions:
1. Identify new features, configuration changes, or usage updates from the diff.
2. Update the README to reflect these changes.
3. Return the FULL updated README content in markdown format.
4. Do not include any conversational text, just the markdown.

Updated README:"""
        return await self.generate(prompt, max_tokens=4000)

    async def update_spec(self, commit_info: Dict[str, Any], current_spec: str) -> str:
        """Update spec.md based on commit info.

        Args:
            commit_info: Commit information dictionary
            current_spec: Current spec.md content

        Returns:
            Updated spec.md content
        """
        commit_msg = commit_info.get("message", "")
        diff_summary = commit_info.get("diff", "") # Assuming 'diff' might be part of commit_info
        
        prompt = f"""
        Update the project specification (spec.md) based on the following commit:
        
        Commit Message: {commit_msg}
        Diff Summary: {diff_summary[:2000]}...
        
        Current spec.md content:
        {current_spec[:2000]}...
        
        Instructions:
        1. Analyze the changes and how they affect the project status.
        2. Generate a NEW entry for the "Development Log" section.
        3. The entry should follow this format:
           ### [YYYY-MM-DD] {commit_msg}
           - **Summary**: Brief summary of changes.
           - **Decisions**: Key architectural decisions (if any).
           - **Next Steps**: Potential next steps (if any).
        4. RETURN ONLY THE NEW ENTRY. DO NOT return the full file.
        """
        return await self.generate(prompt, max_tokens=4000)