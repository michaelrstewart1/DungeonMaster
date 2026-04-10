"""
LLM Provider abstraction layer for D&D 5e AI Dungeon Master.

This module provides the abstract interface for LLM providers and a test double
(FakeLLM) for use in testing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional


@dataclass
class LLMMessage:
    """A single message in an LLM conversation.
    
    Attributes:
        role: The role of the message sender ("system", "user", or "assistant")
        content: The text content of the message
    """
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMUsage:
    """Token usage statistics for an LLM response.
    
    Attributes:
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
    """
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class LLMResponse:
    """Response from an LLM provider.
    
    Attributes:
        content: The generated text content
        model: The model name/identifier
        usage: Token usage statistics
    """
    content: str
    model: str
    usage: LLMUsage = field(default_factory=LLMUsage)


@dataclass
class LLMStreamChunk:
    """A chunk of streamed content from an LLM.
    
    Attributes:
        content: Partial content of this chunk
        is_final: Whether this is the final chunk
    """
    content: str
    is_final: bool = False


class LLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    All LLM provider implementations should inherit from this class and
    implement the abstract methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this LLM provider."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            messages: List of message objects with role and content
            system_prompt: Optional system prompt to guide the LLM
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in the response
            
        Returns:
            LLMResponse containing the generated content and metadata
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream a response from the LLM.
        
        Args:
            messages: List of message objects with role and content
            system_prompt: Optional system prompt to guide the LLM
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in the response
            
        Yields:
            LLMStreamChunk objects representing partial responses
        """
        pass


class FakeLLM(LLMProvider):
    """Test double for LLM providers.
    
    FakeLLM allows for deterministic testing by returning canned responses.
    It also tracks all calls made to it for assertion purposes.
    """

    def __init__(
        self,
        default_response: str = "Default test response",
        default_chunks: Optional[list[str]] = None,
        response_map: Optional[dict[str, str]] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ):
        """Initialize FakeLLM with default responses.
        
        Args:
            default_response: Default response for generate()
            default_chunks: Default chunks for stream() (list of strings)
            response_map: Mapping of input patterns to responses
            prompt_tokens: Token count for prompts
            completion_tokens: Token count for completions
        """
        self._default_response = default_response
        self._default_chunks = default_chunks or []
        self._response_map = response_map or {}
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self._call_history: list[dict] = []

    @property
    def name(self) -> str:
        """Return the name of this test double."""
        return "fake"

    @property
    def call_history(self) -> list[dict]:
        """Return the list of tracked method calls."""
        return self._call_history

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate a response using the response map or default response.
        
        Args:
            messages: List of message objects
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            LLMResponse with canned content
        """
        # Track the call
        self._call_history.append({
            "method": "generate",
            "messages": messages,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })

        # Get the response content
        content = self._get_response_for_messages(messages)

        # Create and return response
        usage = LLMUsage(
            prompt_tokens=self._prompt_tokens,
            completion_tokens=self._completion_tokens,
        )
        return LLMResponse(content=content, model=self.name, usage=usage)

    async def stream(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream a response using configured chunks.
        
        Args:
            messages: List of message objects
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Yields:
            LLMStreamChunk objects, with the last one marked as final
        """
        # Track the call
        self._call_history.append({
            "method": "stream",
            "messages": messages,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })

        # Get chunks to stream
        chunks = self._default_chunks if self._default_chunks else []

        # Yield each chunk
        for i, chunk_content in enumerate(chunks):
            is_final = (i == len(chunks) - 1)
            yield LLMStreamChunk(content=chunk_content, is_final=is_final)

    def _get_response_for_messages(self, messages: list[LLMMessage]) -> str:
        """Get response content based on message content.
        
        Checks if any message content contains a key from the response_map.
        If a match is found, returns the mapped response. Otherwise returns
        the default response.
        
        Args:
            messages: List of message objects to check
            
        Returns:
            Response string
        """
        # Check messages for response map matches
        for message in messages:
            for pattern, response in self._response_map.items():
                if pattern.lower() in message.content.lower():
                    return response

        # Return default if no match found
        return self._default_response
