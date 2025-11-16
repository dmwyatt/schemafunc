"""
Provider system for converting intermediate schema to provider-specific formats.

This module defines the intermediate schema representation and provider interfaces
for converting function schemas to different LLM provider formats (OpenAI, Anthropic, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Type, Optional


@dataclass
class IntermediateSchema:
    """
    Provider-agnostic intermediate representation of a function schema.
    
    This format captures the essential information about a function that can be
    transformed into any provider-specific format.
    
    Attributes:
        name: The function name
        description: The function description
        parameters: JSON Schema properties for the function parameters
        required: List of required parameter names
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str]


class SchemaProvider(ABC):
    """
    Abstract base class for schema providers.
    
    Providers convert the intermediate schema format into provider-specific
    formats required by different LLM APIs (OpenAI, Anthropic, etc.).
    """
    
    @abstractmethod
    def format_schema(self, intermediate: IntermediateSchema) -> Dict[str, Any]:
        """
        Convert intermediate schema to provider-specific format.
        
        Args:
            intermediate: The intermediate schema representation
            
        Returns:
            Provider-specific schema dictionary
        """
        pass
    
    @abstractmethod
    def format_tool_kwargs(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate provider-specific kwargs for API calls.
        
        Args:
            schema: The provider-specific schema
            
        Returns:
            Dictionary of kwargs to pass to the provider's API
        """
        pass


class OpenAIProvider(SchemaProvider):
    """Provider for OpenAI's function calling format."""
    
    def format_schema(self, intermediate: IntermediateSchema) -> Dict[str, Any]:
        """
        Convert to OpenAI's nested function schema format.
        
        OpenAI format:
        {
            "type": "function",
            "function": {
                "name": "...",
                "description": "...",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        }
        """
        return {
            "type": "function",
            "function": {
                "name": intermediate.name,
                "description": intermediate.description,
                "parameters": {
                    "type": "object",
                    "properties": intermediate.parameters,
                    "required": intermediate.required,
                }
            }
        }
    
    def format_tool_kwargs(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate OpenAI-specific tool kwargs.
        
        Returns kwargs that can be unpacked into openai.chat.completions.create()
        """
        return {
            "tools": [schema],
            "tool_choice": {
                "type": "function",
                "function": {"name": schema["function"]["name"]},
            },
        }


class AnthropicProvider(SchemaProvider):
    """Provider for Anthropic's function calling format."""
    
    def format_schema(self, intermediate: IntermediateSchema) -> Dict[str, Any]:
        """
        Convert to Anthropic's flattened schema format.
        
        Anthropic format:
        {
            "name": "...",
            "description": "...",
            "input_schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
        """
        return {
            "name": intermediate.name,
            "description": intermediate.description,
            "input_schema": {
                "type": "object",
                "properties": intermediate.parameters,
                "required": intermediate.required,
            }
        }
    
    def format_tool_kwargs(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Anthropic-specific tool kwargs.
        
        Returns kwargs that can be unpacked into anthropic API calls.
        """
        return {
            "tools": [schema],
        }


# Provider Registry
_provider_registry: Dict[str, Type[SchemaProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def register_provider(name: str, provider_class: Type[SchemaProvider]) -> None:
    """
    Register a custom provider for use with schemafunc.
    
    This allows third-party code to add support for additional LLM providers
    without modifying the schemafunc codebase.
    
    Args:
        name: Unique identifier for the provider (e.g., "gemini", "cohere")
        provider_class: A class that inherits from SchemaProvider
        
    Example:
        >>> class GeminiProvider(SchemaProvider):
        ...     def format_schema(self, intermediate):
        ...         return {"gemini_format": ...}
        ...     def format_tool_kwargs(self, schema):
        ...         return {"tools": [schema]}
        >>> register_provider("gemini", GeminiProvider)
    """
    if not issubclass(provider_class, SchemaProvider):
        raise TypeError(f"{provider_class} must inherit from SchemaProvider")
    _provider_registry[name.lower()] = provider_class


def get_provider(name: str) -> Optional[Type[SchemaProvider]]:
    """
    Get a registered provider class by name.
    
    Args:
        name: The provider name (case-insensitive)
        
    Returns:
        The provider class, or None if not found
        
    Example:
        >>> provider_class = get_provider("openai")
        >>> provider = provider_class()
        >>> schema = provider.format_schema(intermediate)
    """
    return _provider_registry.get(name.lower())


def list_providers() -> List[str]:
    """
    List all registered provider names.
    
    Returns:
        List of provider names that can be used with get_provider()
        
    Example:
        >>> list_providers()
        ['openai', 'anthropic']
    """
    return list(_provider_registry.keys())

