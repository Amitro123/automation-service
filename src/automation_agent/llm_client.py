"""LLM client supporting OpenAI, Anthropic, and Gemini."""

import logging
from typing import Optional, Dict, Any
import os
import asyncio

logger = logging.getLogger(__name__)


class LLMClient:
    """Universal LLM client supporting multiple providers."""

    def __init__(self, provider: str = "openai", model: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize LLM client.

        Args:
            provider: LLM provider ("openai", "anthropic", or "gemini")
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
        elif self.provider == "gemini":
            self._initialize_gemini()
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
            if not self.model:
                raise ValueError("Model must be specified for OpenAI")
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
            if not self.model:
                raise ValueError("Model must be specified for Anthropic")
            logger.info(f"Initialized AsyncAnthropic client with model {self.model}")
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")

    def _initialize_gemini(self):
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai
            self.api_key = self.api_key or os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("Gemini API key not provided")
            
            genai.configure(api_key=self.api_key)
            if not self.model:
                raise ValueError("Model must be specified for Gemini")
            self._client = genai.GenerativeModel(self.model)
            logger.info(f"Initialized Gemini client with model {self.model}")
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")

    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using the configured LLM with retry logic.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)

        Returns:
            Generated text

        Raises:
            Exception: If generation fails after retries
        """
        retries = 3
        last_exception = None

        for attempt in range(retries):
            try:
                if self.provider == "openai":
                    return await self._generate_openai(prompt, max_tokens, temperature)
                elif self.provider == "anthropic":
                    return await self._generate_anthropic(prompt, max_tokens, temperature)
                elif self.provider == "gemini":
                    return await self._generate_gemini(prompt, max_tokens, temperature)
                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")
            except Exception as e:
                last_exception = e
                if attempt < retries - 1:
                    wait_time = 1 * (attempt + 1)
                    logger.warning(f"Generation failed (attempt {attempt+1}/{retries}): {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Generation failed after {retries} attempts: {e}")
        
        raise last_exception

    async def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using OpenAI."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content

    async def _generate_anthropic(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using Anthropic."""
        response = await self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    async def _generate_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using Gemini."""
        # Gemini doesn't support max_tokens directly in generate_content in the same way, 
        # but we can pass generation_config.
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        response = await self._client.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        return response.text

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

    async def update_spec(self, commit_info: Dict[str, Any], diff: str, current_spec: str) -> str:
        """Update spec.md based on commit info.

        Args:
            commit_info: Commit information dictionary
            diff: Git diff content
            current_spec: Current spec.md content

        Returns:
            Updated spec.md content
        """
        commit_msg = commit_info.get("message", "")
        
        # Truncate diff if too long
        if len(diff) > 8000:
            diff = diff[:8000] + "\n\n[... diff truncated ...]"
        
        prompt = f"""
        Update the project specification (spec.md) based on the following commit:
        
        Commit Message: {commit_msg}
        Diff Summary: 
        ```diff
        {diff}
        ```
        
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
        5. DO NOT wrap the output in markdown code blocks (e.g. ```markdown). Just return the text content.
        """
        return await self.generate(prompt, max_tokens=4000)

    async def summarize_review(self, review_content: str, current_log: str) -> str:
        """Summarize a code review for the log.

        Args:
            review_content: Full review content
            current_log: Current log content for context

        Returns:
            Summary entry for code_review.md
        """
        prompt = f"""
        Summarize the following code review into a structured entry for the code review log.
        
        Full Review:
        {review_content[:4000]}...
        
        Current Log Context (last 1000 chars):
        {current_log[-1000:]}
        
        Instructions:
        1. Create a concise summary of the key findings (Strengths, Issues, Suggestions).
        2. Format as a log entry:
           ### [YYYY-MM-DD] Review Summary
           - **Score**: (Estimate a score 1-10 based on issues)
           - **Key Issues**: List top 3 critical/high issues
           - **Action Items**: Top recommendations
        3. RETURN ONLY THE NEW ENTRY. DO NOT wrap in markdown blocks.
        """
        return await self.generate(prompt, max_tokens=1000)