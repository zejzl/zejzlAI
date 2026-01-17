"""
Multi-Modal AI Integration for ZEJZL.NET Phase 8
Supports images, audio, video, and text in unified AI interactions.
"""

import base64
import io
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import asyncio
import logging

logger = logging.getLogger("MultiModal")


class ModalityType(Enum):
    """Types of content modalities supported"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    CODE = "code"


class ImageFormat(Enum):
    """Supported image formats"""
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"
    BMP = "bmp"


class AudioFormat(Enum):
    """Supported audio formats"""
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    M4A = "m4a"
    OGG = "ogg"


@dataclass
class MultiModalContent:
    """Unified content structure for multi-modal AI interactions"""
    modality: ModalityType
    content: Union[str, bytes]
    metadata: Dict[str, Any] = field(default_factory=dict)
    encoding: Optional[str] = None  # For binary content (e.g., "base64")

    def __post_init__(self):
        # Auto-detect encoding for binary content
        if isinstance(self.content, bytes) and not self.encoding:
            self.encoding = "bytes"
        elif isinstance(self.content, str) and self.modality in [ModalityType.IMAGE, ModalityType.AUDIO, ModalityType.VIDEO]:
            # Assume base64 encoded if it's a string for binary modalities
            self.encoding = "base64"

    @classmethod
    def from_text(cls, text: str) -> 'MultiModalContent':
        """Create text content"""
        return cls(
            modality=ModalityType.TEXT,
            content=text,
            metadata={"length": len(text)}
        )

    @classmethod
    def from_image_file(cls, file_path: Union[str, Path], format: Optional[ImageFormat] = None) -> 'MultiModalContent':
        """Create image content from file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        with open(path, 'rb') as f:
            content = f.read()

        # Auto-detect format if not specified
        if not format:
            ext = path.suffix.lower().lstrip('.')
            try:
                format = ImageFormat(ext)
            except ValueError:
                format = ImageFormat.JPEG  # Default

        return cls(
            modality=ModalityType.IMAGE,
            content=content,
            encoding="bytes",
            metadata={
                "format": format.value,
                "filename": path.name,
                "size": len(content)
            }
        )

    @classmethod
    def from_image_base64(cls, base64_string: str, format: ImageFormat = ImageFormat.JPEG) -> 'MultiModalContent':
        """Create image content from base64 string"""
        return cls(
            modality=ModalityType.IMAGE,
            content=base64_string,
            encoding="base64",
            metadata={"format": format.value}
        )

    @classmethod
    def from_audio_file(cls, file_path: Union[str, Path], format: Optional[AudioFormat] = None) -> 'MultiModalContent':
        """Create audio content from file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        with open(path, 'rb') as f:
            content = f.read()

        # Auto-detect format if not specified
        if not format:
            ext = path.suffix.lower().lstrip('.')
            try:
                format = AudioFormat(ext)
            except ValueError:
                format = AudioFormat.MP3  # Default

        return cls(
            modality=ModalityType.AUDIO,
            content=content,
            encoding="bytes",
            metadata={
                "format": format.value,
                "filename": path.name,
                "size": len(content),
                "duration": None  # Would need audio processing library to detect
            }
        )

    def to_base64(self) -> str:
        """Convert content to base64 string"""
        if self.encoding == "base64":
            return self.content
        elif self.encoding == "bytes":
            return base64.b64encode(self.content).decode('utf-8')
        else:
            # Assume it's already a string
            return self.content

    def get_bytes(self) -> bytes:
        """Get content as bytes"""
        if self.encoding == "bytes":
            return self.content
        elif self.encoding == "base64":
            return base64.b64decode(self.content)
        else:
            # Assume it's a string
            return self.content.encode('utf-8')


@dataclass
class MultiModalMessage:
    """Message structure supporting multiple modalities"""
    id: str
    content: List[MultiModalContent]
    timestamp: Any  # datetime
    sender: str
    provider: str
    response: Optional[List[MultiModalContent]] = None
    response_time: Optional[float] = None
    token_usage: Optional[Any] = None  # TokenUsage
    error: Optional[str] = None
    conversation_id: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_modality(self, modality: ModalityType) -> bool:
        """Check if message contains specific modality"""
        return any(c.modality == modality for c in self.content)

    def get_text_content(self) -> str:
        """Extract all text content from message"""
        text_parts = []
        for content in self.content:
            if content.modality == ModalityType.TEXT:
                text_parts.append(content.content)
        return " ".join(text_parts)

    def get_image_content(self) -> List[MultiModalContent]:
        """Get all image content from message"""
        return [c for c in self.content if c.modality == ModalityType.IMAGE]

    def get_audio_content(self) -> List[MultiModalContent]:
        """Get all audio content from message"""
        return [c for c in self.content if c.modality == ModalityType.AUDIO]


class MultiModalProvider:
    """Base class for multi-modal AI providers"""

    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or self.default_model
        self.session = None
        self.supported_modalities = [ModalityType.TEXT]  # Default to text-only

    @property
    def name(self) -> str:
        """Provider name"""
        raise NotImplementedError

    @property
    def default_model(self) -> str:
        """Default model for this provider"""
        raise NotImplementedError

    async def initialize(self):
        """Initialize the provider"""
        raise NotImplementedError

    async def generate_response(self, message: MultiModalMessage) -> Tuple[List[MultiModalContent], Any]:
        """
        Generate multi-modal response to a multi-modal message

        Args:
            message: MultiModalMessage with content

        Returns:
            Tuple of (response_content_list, token_usage)
        """
        raise NotImplementedError

    def supports_modality(self, modality: ModalityType) -> bool:
        """Check if provider supports a specific modality"""
        return modality in self.supported_modalities

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()


class GPT4VisionProvider(MultiModalProvider):
    """OpenAI GPT-4 Vision provider for images and text"""

    def __init__(self, api_key: str):
        super().__init__(api_key, "gpt-4-vision-preview")
        self.supported_modalities = [ModalityType.TEXT, ModalityType.IMAGE]

    @property
    def name(self) -> str:
        return "GPT4Vision"

    @property
    def default_model(self) -> str:
        return "gpt-4-vision-preview"

    async def initialize(self):
        from aiohttp import ClientSession
        self.session = ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    async def generate_response(self, message: MultiModalMessage) -> Tuple[List[MultiModalContent], Any]:
        """Generate response using GPT-4 Vision"""
        if not self.session:
            await self.initialize()

        # Convert multi-modal content to OpenAI format
        messages = self._convert_to_openai_format(message)

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000
        }

        try:
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result["choices"][0]["message"]["content"]

                    # Extract token usage
                    usage = result.get("usage", {})
                    token_usage = type('TokenUsage', (), {
                        'provider': self.name,
                        'model': self.model,
                        'prompt_tokens': usage.get('prompt_tokens', 0),
                        'completion_tokens': usage.get('completion_tokens', 0),
                        'total_tokens': usage.get('total_tokens', 0)
                    })()

                    response_content = [MultiModalContent.from_text(response_text)]
                    return response_content, token_usage
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            raise

    def _convert_to_openai_format(self, message: MultiModalMessage) -> List[Dict]:
        """Convert MultiModalMessage to OpenAI chat format"""
        messages = []

        # Build user message with multi-modal content
        content = []

        for modal_content in message.content:
            if modal_content.modality == ModalityType.TEXT:
                content.append({
                    "type": "text",
                    "text": modal_content.content
                })
            elif modal_content.modality == ModalityType.IMAGE:
                # Convert image to base64 data URL
                base64_data = modal_content.to_base64()
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_data}"
                    }
                })

        messages.append({
            "role": "user",
            "content": content
        })

        return messages


class GeminiVisionProvider(MultiModalProvider):
    """Google Gemini Vision provider for images and text"""

    def __init__(self, api_key: str):
        super().__init__(api_key, "gemini-pro-vision")
        self.supported_modalities = [ModalityType.TEXT, ModalityType.IMAGE]

    @property
    def name(self) -> str:
        return "GeminiVision"

    @property
    def default_model(self) -> str:
        return "gemini-pro-vision"

    async def initialize(self):
        from aiohttp import ClientSession
        self.session = ClientSession()

    async def generate_response(self, message: MultiModalMessage) -> Tuple[List[MultiModalContent], Any]:
        """Generate response using Gemini Vision"""
        if not self.session:
            await self.initialize()

        # Convert to Gemini format
        contents = self._convert_to_gemini_format(message)

        data = {
            "contents": contents
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result["candidates"][0]["content"]["parts"][0]["text"]

                    # Gemini doesn't provide token usage, estimate
                    token_usage = type('TokenUsage', (), {
                        'provider': self.name,
                        'model': self.model,
                        'prompt_tokens': len(message.get_text_content()) // 4,
                        'completion_tokens': len(response_text) // 4,
                        'total_tokens': (len(message.get_text_content()) + len(response_text)) // 4
                    })()

                    response_content = [MultiModalContent.from_text(response_text)]
                    return response_content, token_usage
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            raise

    def _convert_to_gemini_format(self, message: MultiModalMessage) -> List[Dict]:
        """Convert MultiModalMessage to Gemini format"""
        parts = []

        for modal_content in message.content:
            if modal_content.modality == ModalityType.TEXT:
                parts.append({"text": modal_content.content})
            elif modal_content.modality == ModalityType.IMAGE:
                # Gemini expects base64 encoded images
                base64_data = modal_content.to_base64()
                parts.append({
                    "inline_data": {
                        "mime_type": f"image/{modal_content.metadata.get('format', 'jpeg')}",
                        "data": base64_data
                    }
                })

        return [{"role": "user", "parts": parts}]


# Utility functions for multi-modal processing
def create_multimodal_message(
    content: Union[str, List[MultiModalContent]],
    sender: str = "user",
    provider: str = "multimodal",
    conversation_id: str = "default"
) -> MultiModalMessage:
    """Create a MultiModalMessage from various input types"""
    import uuid
    from datetime import datetime

    # Convert string content to MultiModalContent
    if isinstance(content, str):
        content = [MultiModalContent.from_text(content)]
    elif isinstance(content, MultiModalContent):
        content = [content]

    return MultiModalMessage(
        id=str(uuid.uuid4()),
        content=content,
        timestamp=datetime.now(),
        sender=sender,
        provider=provider,
        conversation_id=conversation_id
    )


def combine_responses(responses: List[MultiModalMessage]) -> MultiModalMessage:
    """Combine multiple multi-modal responses into one"""
    if not responses:
        return None

    combined_content = []
    for response in responses:
        if response.response:
            combined_content.extend(response.response)

    if not combined_content:
        return None

    # Create combined response
    import uuid
    from datetime import datetime

    return MultiModalMessage(
        id=str(uuid.uuid4()),
        content=combined_content,
        timestamp=datetime.now(),
        sender="system",
        provider="combined",
        conversation_id=responses[0].conversation_id if responses else "default"
    )


logger.info("Multi-modal AI integration initialized")