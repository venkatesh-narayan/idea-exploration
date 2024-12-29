from typing import Any, Dict, List

from app.llm.ensemble import NormalLlmEnsembler
from app.models.calculation import CalculationResult, CalculationSpec
from app.prompts import PROMPTS


class CalculationHandler:
    """
    Handles generating and executing calculations safely.
    Best to use the NormalLlmEnsembler for this.
    """

    def __init__(self, model_dict: Dict[str, List[str]]):
        """Initialize calculation components."""

        assert len(model_dict.keys()) == 1, "Only one provider supported now"
        assert len(list(model_dict.values())[0]) == 1, "Only one model supported now"

        # The code shouldn't be that complex, so we can use the normal LLM ensembler.
        self.llm_ensembler = NormalLlmEnsembler(
            model_dict=model_dict, response_format=CalculationSpec
        )

        # Load prompts
        self.system_prompt = PROMPTS["system"]["calculation"]
        self.user_prompt = PROMPTS["user"]["calculation"]

    def generate_calculation(
        self, question: str, available_data: Dict[str, Any]
    ) -> CalculationSpec:
        """
        Generate code to perform a calculation using available data.

        Args:
            question: What we're trying to calculate
            available_data: Data available for the calculation, as {name: value}

        Returns:
            CalculationSpec with code and explanation
        """

        # Have LLM generate calculation code
        response = self.llm_ensembler.call_providers(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": self.user_prompt.format(
                        question=question,
                        available_data=self._format_data(available_data),
                    ),
                },
            ]
        )

        assert len(response.values()) == 1
        provider_response = list(response.values())[0]
        assert len(provider_response) == 1
        calculation_spec = provider_response[0]
        assert calculation_spec.code and calculation_spec.explanation
        return calculation_spec

    def execute_calculation(
        self, spec: CalculationSpec, input_data: Dict[str, Any]
    ) -> CalculationResult:
        """
        Safely execute a calculation.

        Args:
            spec: The calculation specification
            input_data: Input data for the calculation

        Returns:
            CalculationResult with output and any warnings
        """
        # Create sandbox environment with only safe operations
        sandbox_globals = {
            "input_data": input_data,
            "print": print,  # For debugging
            "__builtins__": {
                "abs": abs,
                "float": float,
                "int": int,
                "len": len,
                "max": max,
                "min": min,
                "pow": pow,
                "round": round,
                "sum": sum,
            },
        }

        try:
            # Execute in sandbox
            exec(spec.code, sandbox_globals)

            # Get result
            if "result" not in sandbox_globals:
                raise ValueError("Calculation code must set a 'result' variable")

            return CalculationResult(
                code=spec.code,
                explanation=spec.explanation,
                warnings=[],
                result=sandbox_globals["result"],
            )

        except Exception as e:
            print("Calculation failed: ", str(e))
            return CalculationResult(
                code=spec.code,
                explanation=spec.explanation,
                warnings=[f"Calculation failed: {str(e)}"],
                result=None,
            )

    def _format_data(self, data: Dict[str, Any]) -> str:
        """Format data dictionary for prompt."""
        lines = []
        for name, value in data.items():
            lines.append(f"{name}: {value}")
        return "\n".join(lines)
