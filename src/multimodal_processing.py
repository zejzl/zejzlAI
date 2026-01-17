"""
Multi-Modal Message Processing Layer
Unifies text and multi-modal message handling in ZEJZL.NET
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from .multimodal_ai import (
    MultiModalMessage, MultiModalContent, MultiModalProvider,
    ModalityType, create_multimodal_message, combine_responses
)
from .ai_framework import Message, TokenUsage

logger = logging.getLogger("MultiModalProcessing")


class MultiModalProcessor:
    """
    Processes multi-modal messages and coordinates with multi-modal AI providers
    """

    def __init__(self):
        self.multimodal_providers: Dict[str, MultiModalProvider] = {}
        self.text_providers = {}  # Reference to existing text providers

    def register_multimodal_provider(self, provider: MultiModalProvider):
        """Register a multi-modal capable provider"""
        self.multimodal_providers[provider.name.lower()] = provider
        logger.info(f"Registered multi-modal provider: {provider.name}")

    def has_multimodal_provider(self, provider_name: str) -> bool:
        """Check if a multi-modal provider is available"""
        return provider_name.lower() in self.multimodal_providers

    def get_provider_capabilities(self, provider_name: str) -> List[ModalityType]:
        """Get supported modalities for a provider"""
        provider = self.multimodal_providers.get(provider_name.lower())
        if provider:
            return provider.supported_modalities
        return [ModalityType.TEXT]  # Default for text-only providers

    async def process_multimodal_message(
        self,
        message: Union[Message, MultiModalMessage],
        provider_name: str = "gpt4vision"
    ) -> Union[Message, MultiModalMessage]:
        """
        Process a message through multi-modal providers

        Args:
            message: Either traditional Message or MultiModalMessage
            provider_name: Name of the provider to use

        Returns:
            Response message in the same format as input
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Convert to MultiModalMessage if needed
            if isinstance(message, Message):
                multimodal_msg = self._convert_to_multimodal(message)
            else:
                multimodal_msg = message

            # Get the appropriate provider
            provider = self.multimodal_providers.get(provider_name.lower())
            if not provider:
                raise ValueError(f"Multi-modal provider '{provider_name}' not found")

            # Check if provider supports the modalities in the message
            required_modalities = set(c.modality for c in multimodal_msg.content)
            supported_modalities = set(provider.supported_modalities)

            if not required_modalities.issubset(supported_modalities):
                unsupported = required_modalities - supported_modalities
                raise ValueError(f"Provider {provider_name} does not support modalities: {unsupported}")

            # Generate response
            response_content, token_usage = await provider.generate_response(multimodal_msg)

            # Create response message
            response_msg = MultiModalMessage(
                id=f"response_{multimodal_msg.id}",
                content=response_content,
                timestamp=datetime.now(),
                sender="assistant",
                provider=provider.name,
                response_time=asyncio.get_event_loop().time() - start_time,
                token_usage=token_usage,
                conversation_id=multimodal_msg.conversation_id
            )

            # Convert back to original format if needed
            if isinstance(message, Message):
                return self._convert_from_multimodal(response_msg)
            else:
                return response_msg

        except Exception as e:
            logger.error(f"Multi-modal processing failed: {e}")

            # Return error response in appropriate format
            if isinstance(message, Message):
                return Message(
                    id=f"error_{message.id}",
                    content=message.content,
                    timestamp=datetime.now(),
                    sender="system",
                    provider=provider_name,
                    response=f"Multi-modal processing error: {str(e)}",
                    response_time=asyncio.get_event_loop().time() - start_time,
                    error=str(e),
                    conversation_id=message.conversation_id
                )
            else:
                return MultiModalMessage(
                    id=f"error_{message.id}",
                    content=[MultiModalContent.from_text(f"Multi-modal processing error: {str(e)}")],
                    timestamp=datetime.now(),
                    sender="system",
                    provider=provider_name,
                    response_time=asyncio.get_event_loop().time() - start_time,
                    error=str(e),
                    conversation_id=message.conversation_id
                )

    def _convert_to_multimodal(self, message: Message) -> MultiModalMessage:
        """Convert traditional Message to MultiModalMessage"""
        content = [MultiModalContent.from_text(message.content)]

        return MultiModalMessage(
            id=message.id,
            content=content,
            timestamp=message.timestamp,
            sender=message.sender,
            provider=message.provider,
            conversation_id=message.conversation_id,
            metadata={"original_format": "text_only"}
        )

    def _convert_from_multimodal(self, message: MultiModalMessage) -> Message:
        """Convert MultiModalMessage back to traditional Message"""
        # Extract text content
        text_content = message.get_text_content()
        if not text_content:
            text_content = "[Multi-modal response: see attached content]"

        # Convert token usage
        token_usage = None
        if message.token_usage:
            token_usage = TokenUsage(
                provider=message.token_usage.provider,
                model=message.token_usage.model,
                prompt_tokens=getattr(message.token_usage, 'prompt_tokens', 0),
                completion_tokens=getattr(message.token_usage, 'completion_tokens', 0),
                total_tokens=getattr(message.token_usage, 'total_tokens', 0)
            )

        return Message(
            id=message.id,
            content=text_content,
            timestamp=message.timestamp,
            sender=message.sender,
            provider=message.provider,
            response=text_content,
            response_time=message.response_time,
            token_usage=token_usage,
            conversation_id=message.conversation_id
        )

    async def process_image_analysis(
        self,
        image_content: MultiModalContent,
        query: str = "Describe this image",
        provider_name: str = "gpt4vision"
    ) -> str:
        """
        Specialized method for image analysis

        Args:
            image_content: Image content to analyze
            query: Question about the image
            provider_name: Provider to use

        Returns:
            Text description/analysis of the image
        """
        multimodal_msg = create_multimodal_message([
            image_content,
            MultiModalContent.from_text(query)
        ])

        response = await self.process_multimodal_message(multimodal_msg, provider_name)

        if isinstance(response, MultiModalMessage):
            return response.get_text_content()
        else:
            return response.response or "No response generated"

    async def process_audio_transcription(
        self,
        audio_content: MultiModalContent,
        provider_name: str = "whisper"  # Would need audio provider
    ) -> str:
        """
        Transcribe audio content (placeholder - would need audio-capable provider)

        Args:
            audio_content: Audio content to transcribe
            provider_name: Provider to use (would need audio support)

        Returns:
            Transcribed text
        """
        # This is a placeholder - real implementation would require audio-capable providers
        # For now, return a mock response
        return f"[Audio transcription not yet implemented] Audio file: {audio_content.metadata.get('filename', 'unknown')}"

    async def generate_image_description(
        self,
        image_content: MultiModalContent,
        style: str = "detailed",
        provider_name: str = "gpt4vision"
    ) -> str:
        """
        Generate a detailed description of an image

        Args:
            image_content: Image to describe
            style: Description style ("brief", "detailed", "technical")
            provider_name: Vision-capable provider to use

        Returns:
            Image description
        """
        prompts = {
            "brief": "Provide a brief description of this image.",
            "detailed": "Provide a detailed description of this image, including objects, colors, composition, and any text visible.",
            "technical": "Analyze this image technically, including composition, lighting, colors, and visual elements."
        }

        query = prompts.get(style, prompts["detailed"])

        return await self.process_image_analysis(image_content, query, provider_name)

    def get_supported_providers(self) -> List[str]:
        """Get list of available multi-modal providers"""
        return list(self.multimodal_providers.keys())

    def get_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all multi-modal providers"""
        info = {}
        for name, provider in self.multimodal_providers.items():
            info[name] = {
                "name": provider.name,
                "model": provider.model,
                "supported_modalities": [m.value for m in provider.supported_modalities]
            }
        return info


# Global multi-modal processor instance
multimodal_processor = MultiModalProcessor()

# Convenience functions
async def process_multimodal_message(
    message: Union[Message, MultiModalMessage],
    provider: str = "gpt4vision"
) -> Union[Message, MultiModalMessage]:
    """Convenience function for multi-modal processing"""
    return await multimodal_processor.process_multimodal_message(message, provider)

async def analyze_image(
    image_path: str,
    query: str = "What's in this image?",
    provider: str = "gpt4vision"
) -> str:
    """Convenience function for image analysis"""
    try:
        from .multimodal_ai import MultiModalContent, ImageFormat
        image_content = MultiModalContent.from_image_file(image_path)
        return await multimodal_processor.process_image_analysis(image_content, query, provider)
    except Exception as e:
        return f"Image analysis failed: {e}"

async def describe_image(
    image_path: str,
    style: str = "detailed",
    provider: str = "gpt4vision"
) -> str:
    """Convenience function for image description"""
    try:
        from .multimodal_ai import MultiModalContent
        image_content = MultiModalContent.from_image_file(image_path)
        return await multimodal_processor.generate_image_description(image_content, style, provider)
    except Exception as e:
        return f"Image description failed: {e}"

logger.info("Multi-modal message processing layer initialized")