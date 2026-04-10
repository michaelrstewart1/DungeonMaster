"""LLM provider package.

This package provides the abstraction layer for LLM interactions,
including:
- LLMProvider: Abstract base class for LLM implementations
- FakeLLM: Test double for testing without actual LLM calls
- Prompt templates for D&D 5e specific interactions
"""

from .base import (
    LLMMessage,
    LLMUsage,
    LLMResponse,
    LLMStreamChunk,
    LLMProvider,
    FakeLLM,
)
from .prompts import PromptTemplates

__all__ = [
    "LLMMessage",
    "LLMUsage",
    "LLMResponse",
    "LLMStreamChunk",
    "LLMProvider",
    "FakeLLM",
    "PromptTemplates",
]
