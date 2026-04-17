"""Pydantic models for the PromptQA REST API."""

from pydantic import BaseModel


class CriterionResponse(BaseModel):
    type: str
    passed: bool
    description: str
    detail: str = ""


class TestResultResponse(BaseModel):
    test_name: str
    passed: bool
    response_text: str
    duration_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    criteria: list[CriterionResponse] = []


class RunSummaryResponse(BaseModel):
    id: str
    suite_name: str
    provider: str
    total: int
    passed: int
    failed: int
    duration_ms: float
    created_at: str


class RunDetailResponse(RunSummaryResponse):
    results: list[dict[str, object]] = []


class RunRequest(BaseModel):
    yaml_content: str
    provider: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
