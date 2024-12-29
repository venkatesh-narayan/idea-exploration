from typing import List

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    """A specific recommendation with supporting information."""

    title: str = Field(description="Short description of the recommendation")
    approach: str = Field(description="Detailed description of recommended approach")
    rationale: str = Field(description="Why this is recommended")
    key_benefits: List[str] = Field(description="Main benefits of this approach")
    challenges: List[str] = Field(description="Potential challenges to consider")
    next_steps: List[str] = Field(description="Concrete steps to move forward")
    supporting_facts: List[str] = Field(
        description="Key information that supports this recommendation"
    )


class RecommendationSet(BaseModel):
    """Complete set of recommendations for a goal."""

    primary_recommendation: Recommendation = Field(
        description="The main recommended approach"
    )
    alternative_recommendations: List[Recommendation] = Field(
        description="Other viable approaches to consider"
    )
    rejected_approaches: List[str] = Field(
        description="Approaches considered but rejected, with reasons"
    )
    general_insights: List[str] = Field(
        description="Overall insights from the analysis"
    )
