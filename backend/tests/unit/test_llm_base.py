"""
Tests for LLM provider abstraction layer.

This module tests the abstract LLMProvider interface and the FakeLLM test double.
"""

import pytest
from abc import ABC, abstractmethod
from app.services.llm.base import (
    LLMMessage,
    LLMUsage,
    LLMResponse,
    LLMStreamChunk,
    LLMProvider,
    FakeLLM,
)


class TestLLMMessage:
    """Tests for the LLMMessage data class."""

    def test_create_message_with_role_and_content(self):
        """LLMMessage can be created with role and content."""
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_valid_roles(self):
        """Messages support system, user, and assistant roles."""
        for role in ["system", "user", "assistant"]:
            msg = LLMMessage(role=role, content="test")
            assert msg.role == role


class TestLLMUsage:
    """Tests for the LLMUsage data class."""

    def test_create_usage_with_defaults(self):
        """LLMUsage has default values of 0."""
        usage = LLMUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0

    def test_create_usage_with_values(self):
        """LLMUsage can be created with token counts."""
        usage = LLMUsage(prompt_tokens=10, completion_tokens=20)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20


class TestLLMResponse:
    """Tests for the LLMResponse data class."""

    def test_create_response_with_content_and_model(self):
        """LLMResponse contains content and model name."""
        response = LLMResponse(content="Hello", model="gpt-4")
        assert response.content == "Hello"
        assert response.model == "gpt-4"

    def test_response_has_usage_with_defaults(self):
        """LLMResponse includes usage stats with default values."""
        response = LLMResponse(content="Hello", model="gpt-4")
        assert response.usage.prompt_tokens == 0
        assert response.usage.completion_tokens == 0

    def test_response_with_usage_stats(self):
        """LLMResponse can include token usage statistics."""
        usage = LLMUsage(prompt_tokens=100, completion_tokens=50)
        response = LLMResponse(content="Hello", model="gpt-4", usage=usage)
        assert response.usage.prompt_tokens == 100
        assert response.usage.completion_tokens == 50


class TestLLMStreamChunk:
    """Tests for the LLMStreamChunk data class."""

    def test_create_chunk_with_content(self):
        """LLMStreamChunk contains partial content."""
        chunk = LLMStreamChunk(content="Hello")
        assert chunk.content == "Hello"

    def test_chunk_has_is_final_flag(self):
        """LLMStreamChunk has an is_final flag (default False)."""
        chunk = LLMStreamChunk(content="test")
        assert chunk.is_final is False

    def test_chunk_can_mark_final(self):
        """LLMStreamChunk can mark the final chunk."""
        chunk = LLMStreamChunk(content="final", is_final=True)
        assert chunk.is_final is True


class TestLLMProviderAbstractInterface:
    """Tests for the LLMProvider abstract interface."""

    def test_llm_provider_is_abstract(self):
        """LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider()

    def test_llm_provider_requires_name_property(self):
        """LLMProvider requires implementing name property."""

        class IncompleteLLM(LLMProvider):
            async def generate(self, messages, system_prompt=None, temperature=0.7, max_tokens=2000):
                pass

            async def stream(self, messages, system_prompt=None, temperature=0.7, max_tokens=2000):
                pass

        with pytest.raises(TypeError):
            IncompleteLLM()

    def test_llm_provider_requires_generate_method(self):
        """LLMProvider requires implementing generate method."""

        class IncompleteLLM(LLMProvider):
            @property
            def name(self) -> str:
                return "incomplete"

            async def stream(self, messages, system_prompt=None, temperature=0.7, max_tokens=2000):
                pass

        with pytest.raises(TypeError):
            IncompleteLLM()

    def test_llm_provider_requires_stream_method(self):
        """LLMProvider requires implementing stream method."""

        class IncompleteLLM(LLMProvider):
            @property
            def name(self) -> str:
                return "incomplete"

            async def generate(self, messages, system_prompt=None, temperature=0.7, max_tokens=2000):
                pass

        with pytest.raises(TypeError):
            IncompleteLLM()


class TestFakeLLMBasics:
    """Tests for FakeLLM implementation."""

    def test_fake_llm_can_be_instantiated(self):
        """FakeLLM can be instantiated."""
        fake = FakeLLM()
        assert isinstance(fake, LLMProvider)

    def test_fake_llm_has_name(self):
        """FakeLLM has a name property."""
        fake = FakeLLM()
        assert fake.name == "fake"

    @pytest.mark.asyncio
    async def test_fake_llm_generate_returns_response(self):
        """FakeLLM.generate returns an LLMResponse."""
        fake = FakeLLM(default_response="Test response")
        messages = [LLMMessage(role="user", content="Hello")]
        response = await fake.generate(messages)
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "fake"

    @pytest.mark.asyncio
    async def test_fake_llm_generate_with_defaults(self):
        """FakeLLM.generate accepts standard parameters."""
        fake = FakeLLM(default_response="Response")
        messages = [LLMMessage(role="user", content="Hello")]
        response = await fake.generate(
            messages,
            system_prompt="You are helpful",
            temperature=0.5,
            max_tokens=1000,
        )
        assert response.content == "Response"

    @pytest.mark.asyncio
    async def test_fake_llm_stream_yields_chunks(self):
        """FakeLLM.stream yields LLMStreamChunk objects."""
        fake = FakeLLM(default_chunks=["Hello", " ", "World"])
        messages = [LLMMessage(role="user", content="Hello")]
        chunks = []
        async for chunk in fake.stream(messages):
            chunks.append(chunk)
        assert len(chunks) == 3
        assert all(isinstance(c, LLMStreamChunk) for c in chunks)

    @pytest.mark.asyncio
    async def test_fake_llm_stream_final_chunk_marked(self):
        """FakeLLM.stream marks the last chunk as final."""
        fake = FakeLLM(default_chunks=["Hello", " ", "World"])
        messages = [LLMMessage(role="user", content="Hello")]
        chunks = []
        async for chunk in fake.stream(messages):
            chunks.append(chunk)
        assert chunks[-1].is_final is True
        for chunk in chunks[:-1]:
            assert chunk.is_final is False


class TestFakeLLMCallTracking:
    """Tests for FakeLLM call history tracking."""

    @pytest.mark.asyncio
    async def test_fake_llm_tracks_generate_calls(self):
        """FakeLLM tracks generate calls."""
        fake = FakeLLM(default_response="Response")
        messages = [LLMMessage(role="user", content="Hello")]
        await fake.generate(messages, system_prompt="You are helpful")
        assert len(fake.call_history) == 1
        call = fake.call_history[0]
        assert call["method"] == "generate"
        assert call["messages"] == messages

    @pytest.mark.asyncio
    async def test_fake_llm_tracks_system_prompt(self):
        """FakeLLM tracks system prompts in calls."""
        fake = FakeLLM(default_response="Response")
        messages = [LLMMessage(role="user", content="Hello")]
        system_prompt = "You are a helpful assistant"
        await fake.generate(messages, system_prompt=system_prompt)
        call = fake.call_history[0]
        assert call["system_prompt"] == system_prompt

    @pytest.mark.asyncio
    async def test_fake_llm_tracks_parameters(self):
        """FakeLLM tracks temperature and max_tokens."""
        fake = FakeLLM(default_response="Response")
        messages = [LLMMessage(role="user", content="Hello")]
        await fake.generate(messages, temperature=0.5, max_tokens=500)
        call = fake.call_history[0]
        assert call["temperature"] == 0.5
        assert call["max_tokens"] == 500

    @pytest.mark.asyncio
    async def test_fake_llm_tracks_stream_calls(self):
        """FakeLLM tracks stream calls."""
        fake = FakeLLM(default_chunks=["test"])
        messages = [LLMMessage(role="user", content="Hello")]
        async for _ in fake.stream(messages):
            pass
        assert len(fake.call_history) == 1
        call = fake.call_history[0]
        assert call["method"] == "stream"

    @pytest.mark.asyncio
    async def test_fake_llm_call_history_accumulates(self):
        """FakeLLM call history accumulates multiple calls."""
        fake = FakeLLM(default_response="Response", default_chunks=["test"])
        messages = [LLMMessage(role="user", content="Hello")]
        await fake.generate(messages)
        async for _ in fake.stream(messages):
            pass
        await fake.generate(messages)
        assert len(fake.call_history) == 3


class TestFakeLLMResponseMapping:
    """Tests for FakeLLM configurable response mapping."""

    @pytest.mark.asyncio
    async def test_fake_llm_uses_response_map(self):
        """FakeLLM can map input patterns to responses."""
        response_map = {
            "hello": "Hi there!",
            "goodbye": "See you later!",
        }
        fake = FakeLLM(response_map=response_map, default_response="Default")
        
        messages1 = [LLMMessage(role="user", content="hello")]
        response1 = await fake.generate(messages1)
        assert response1.content == "Hi there!"
        
        messages2 = [LLMMessage(role="user", content="goodbye")]
        response2 = await fake.generate(messages2)
        assert response2.content == "See you later!"

    @pytest.mark.asyncio
    async def test_fake_llm_returns_default_for_unmapped_input(self):
        """FakeLLM returns default response for unmapped inputs."""
        response_map = {"hello": "Hi there!"}
        fake = FakeLLM(response_map=response_map, default_response="Default response")
        
        messages = [LLMMessage(role="user", content="unknown")]
        response = await fake.generate(messages)
        assert response.content == "Default response"

    @pytest.mark.asyncio
    async def test_fake_llm_matches_message_content(self):
        """FakeLLM checks message content for response mapping."""
        response_map = {"barbarian": "SMASH!", "wizard": "Fireball!"}
        fake = FakeLLM(response_map=response_map, default_response="Invalid class")
        
        messages = [LLMMessage(role="user", content="What can a barbarian do?")]
        response = await fake.generate(messages)
        assert response.content == "SMASH!"


class TestFakeLLMUsageTracking:
    """Tests for FakeLLM token usage tracking."""

    @pytest.mark.asyncio
    async def test_fake_llm_response_includes_usage(self):
        """FakeLLM responses include token usage."""
        fake = FakeLLM(
            default_response="Test",
            prompt_tokens=10,
            completion_tokens=20,
        )
        messages = [LLMMessage(role="user", content="Hello")]
        response = await fake.generate(messages)
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20

    @pytest.mark.asyncio
    async def test_fake_llm_default_usage_is_zero(self):
        """FakeLLM responses default to zero token usage."""
        fake = FakeLLM(default_response="Test")
        messages = [LLMMessage(role="user", content="Hello")]
        response = await fake.generate(messages)
        assert response.usage.prompt_tokens == 0
        assert response.usage.completion_tokens == 0


class TestLLMMessageHistory:
    """Tests for message history and formatting."""

    def test_messages_maintain_order(self):
        """Message list maintains conversation order."""
        messages = [
            LLMMessage(role="system", content="You are helpful"),
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi there!"),
            LLMMessage(role="user", content="How are you?"),
        ]
        assert messages[0].role == "system"
        assert messages[1].role == "user"
        assert messages[2].role == "assistant"
        assert messages[3].role == "user"

    @pytest.mark.asyncio
    async def test_generate_accepts_message_history(self):
        """FakeLLM.generate accepts multiple messages."""
        fake = FakeLLM(default_response="Response")
        messages = [
            LLMMessage(role="system", content="You are helpful"),
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi!"),
            LLMMessage(role="user", content="What's next?"),
        ]
        response = await fake.generate(messages)
        assert response.content == "Response"
        call = fake.call_history[0]
        assert len(call["messages"]) == 4

    @pytest.mark.asyncio
    async def test_system_prompt_as_separate_param(self):
        """FakeLLM accepts system_prompt as separate parameter."""
        fake = FakeLLM(default_response="Response")
        messages = [LLMMessage(role="user", content="Hello")]
        await fake.generate(messages, system_prompt="You are a DM")
        call = fake.call_history[0]
        assert call["system_prompt"] == "You are a DM"
        # Messages should not include system prompt
        assert len(call["messages"]) == 1
        assert call["messages"][0].role == "user"


class TestLLMProviderContract:
    """Tests ensuring FakeLLM fulfills the LLMProvider contract."""

    @pytest.mark.asyncio
    async def test_generate_returns_llm_response(self):
        """generate() must return LLMResponse."""
        fake = FakeLLM(default_response="Test")
        messages = [LLMMessage(role="user", content="Hello")]
        response = await fake.generate(messages)
        assert isinstance(response, LLMResponse)

    @pytest.mark.asyncio
    async def test_stream_yields_llm_stream_chunk(self):
        """stream() must yield LLMStreamChunk objects."""
        fake = FakeLLM(default_chunks=["test"])
        messages = [LLMMessage(role="user", content="Hello")]
        async for chunk in fake.stream(messages):
            assert isinstance(chunk, LLMStreamChunk)

    @pytest.mark.asyncio
    async def test_generate_response_has_model_name(self):
        """generate() response must include model name."""
        fake = FakeLLM(default_response="Test")
        messages = [LLMMessage(role="user", content="Hello")]
        response = await fake.generate(messages)
        assert response.model == fake.name
