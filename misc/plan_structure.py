import asyncio
from pydantic import BaseModel
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


class Step(BaseModel):
    step_number: int
    description: str
    estimated_complexity: str  # 'low', 'medium', 'high'


class FeaturePlan(BaseModel):
    feature_name: str
    summary: str
    steps: list[Step]
    risks: list[str]


async def main():
    async for message in query(
        prompt="Plan how to add dark mode support to a React app. Break it into implementation steps.",
        options=ClaudeAgentOptions(
            output_format={
                "type": "json_schema",
                "schema": FeaturePlan.model_json_schema(),
            }
        ),
    ):
        if isinstance(message, ResultMessage) and message.structured_output:
            # Validate and get fully typed result
            plan = FeaturePlan.model_validate(message.structured_output)
            print(f"Feature: {plan.feature_name}")
            print(f"Summary: {plan.summary}")
            for step in plan.steps:
                print(
                    f"{step.step_number}. [{step.estimated_complexity}] {step.description}"
                )


if __name__ == "__main__":
    asyncio.run(main())