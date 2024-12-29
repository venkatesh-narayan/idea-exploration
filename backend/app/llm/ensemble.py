import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from app.caching import OpenAICallRecord
from app.llm.base import BaseLlmEnsembler
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class NormalLlmEnsembler(BaseLlmEnsembler):
    """
    Use this for normal LLM's (e.g. "gpt-4o").
    There can be one or many, from as many providers as you like.
    """

    def _call_models_for_provider(
        self,
        provider: str,
        models: List[str],
        messages: List[Dict[str, str]],
    ) -> List[BaseModel]:
        def call_model(model_name: str) -> BaseModel:
            cache_key = self.cache.make_key_for_messages(model_name, messages)
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit for {model_name}")
                return self.response_format.model_validate(
                    cached.structured_output_dict
                )

            logger.info(f"Calling model {model_name}...")
            self.client.api_key = os.getenv(f"{provider}_API_KEY")
            response = self.client.beta.chat.completions.parse(
                model=model_name,
                messages=messages,
                temperature=0,
                response_format=self.response_format,
            )

            output = response.choices[0].message.parsed

            record = OpenAICallRecord(
                model=model_name,
                messages=messages,
                structured_output_dict=output.model_dump(),
            )

            self.cache.set(cache_key, record)

            return output

        responses = []
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = [executor.submit(call_model, m) for m in models]

        for future in as_completed(futures):
            responses.append(future.result())

        return responses


class ReasoningLlmEnsembler(BaseLlmEnsembler):
    """
    Use this specifically for reasoning models (e.g. "o1-preview").
    There can be one or many, from as many providers as you like.
    """

    def _call_models_for_provider(
        self,
        provider: str,
        models: List[str],
        messages: List[Dict[str, str]],
    ) -> List[BaseModel]:
        def call_model(model_name: str) -> BaseModel:
            cache_key = self.cache.make_key_for_messages(model_name, messages)
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit for {model_name}")
                return self.response_format.model_validate(
                    cached.structured_output_dict
                )

            logger.info(f"Calling reasoning model {model_name}...")
            self.client.api_key = os.getenv(f"{provider}_API_KEY")
            reasoning_response = self.client.chat.completions.create(
                model=model_name,
                messages=self._format_reasoning_messages(messages),
                # temperature=0,
                # response_format=self.response_format,
            )

            # Use GPT-4o to get structured output from the reasoning models.
            # Currently, reasoning models don't allow using structured outputs.
            logger.info("Calling GPT-4o for structured output...")
            self.client.api_key = os.getenv("OPENAI_API_KEY")
            structured_response = self.client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Given the following data, format it with the given "
                            "response format:\n"
                            + reasoning_response.choices[0].message.content
                        ),
                    }
                ],
                temperature=0,
                response_format=self.response_format,
            )

            output = structured_response.choices[0].message.parsed
            if not output:
                raise ValueError("Failed to parse structured output")

            record = OpenAICallRecord(
                model=model_name,
                messages=messages,
                structured_output_dict=output.model_dump(),
                reasoning_output=reasoning_response.choices[0].message.content,
            )

            self.cache.set(cache_key, record)

            return output

        responses = []
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = [executor.submit(call_model, m) for m in models]

        for future in as_completed(futures):
            responses.append(future.result())

        return responses

    def _format_reasoning_messages(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        # Currently, reasoning models only allow us to use a single user message.
        # It also doesn't support structured outputs.
        # So, we pack system + user messages and schema into a single user message.
        return [
            {
                "role": "user",
                "content": (
                    "INSTRUCTIONS:\n"
                    + messages[0]["content"]  # system message
                    + "\n\n"
                    + messages[1]["content"]  # user message
                    + f"\nReturn your answer with schema: {self.response_format.model_json_schema()}"  # noqa: E501
                ),
            },
        ]
