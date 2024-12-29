from typing import Any, List, Optional

from pydantic import BaseModel, Field


class CalculationSpec(BaseModel):
    """Specification for a calculation, generated by LLM."""

    code: str = Field(description="Python code to execute")
    explanation: str = Field(description="How the calculation works")


class CalculationResult(BaseModel):
    """Result of executing a calculation."""

    code: str = Field(description="Code that was executed")
    explanation: str = Field(description="How the calculation works")
    warnings: List[str] = Field(
        default_factory=list, description="Any warnings generated"
    )
    result: Optional[Any] = Field(
        None, description="The calculation result if successful"
    )