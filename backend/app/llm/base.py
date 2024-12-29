import logging
import os
from typing import Dict, List

from app.caching import OpenAIFileCache
from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseLlmEnsembler:
    """
    This loads LLM API keys from env. Then for each provider in the config, calls the
    appropriate models in parallel with the same messages.
    """

    def __init__(self, model_dict: Dict[str, List[str]], response_format: BaseModel):
        """
        model_dict example:
        {
          "OPENAI": ["o1-preview"],
          "GEMINI": ["gemini-2.0-flash-thinking-exp-1219"],
        }
        """

        self.model_dict = model_dict
        self.response_format = response_format
        self.cache = OpenAIFileCache()
        self.client = OpenAI()

        for provider_name in model_dict.keys():
            if not os.getenv(f"{provider_name}_API_KEY"):
                raise ValueError(f"Missing API key for {provider_name}")

    def call_providers(self, messages: List[dict]) -> Dict[str, List[BaseModel]]:
        """
        For each provider, call each model in parallel.
        Return a dict: {provider -> [BaseModel, ...]}, where each BaseModel is of the
        type specified in `response_format`.
        """

        result_map: Dict[str, List[BaseModel]] = dict()
        for provider, models in self.model_dict.items():
            responses = self._call_models_for_provider(
                provider=provider, models=models, messages=messages
            )
            result_map[provider] = responses

        return result_map

    def _call_models_for_provider(
        self,
        provider: str,
        models: List[str],
        messages: List[Dict[str, str]],
    ) -> List[BaseModel]:
        """
        Calls the models for a given provider with the provided messages.
        This method should be implemented by subclasses to define how to call
        the models for a specific provider.

        Args:
            provider (str): The name of the provider.
            models (List[str]): A list of model names to be called.
            messages (List[Dict[str, str]]): Messages to be sent to the models.

        Returns:
            List[BaseModel]: A list of model responses.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """

        raise NotImplementedError("Subclasses must implement this method")
