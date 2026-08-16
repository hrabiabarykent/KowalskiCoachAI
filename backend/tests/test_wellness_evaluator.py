import pytest
from unittest.mock import AsyncMock, patch
from app.domain.wellness_evaluator import WellnessEvaluator, WellnessEvaluationResult

@pytest.mark.asyncio
async def test_wellness_evaluator_empty_data():
    needs_revision, reason, decision, overrides = await WellnessEvaluator.evaluate_daily_readiness([], [], [])
    assert needs_revision is False
    assert "Brak danych" in reason

@pytest.mark.asyncio
async def test_wellness_evaluator_ai_success():
    mock_result = WellnessEvaluationResult(
        needs_revision=True,
        reason="Niska zmienność HRV oraz bardzo wysoki odczuwalny trud."
    )
    
    mock_llm = AsyncMock()
    mock_llm.generate_structured.return_value = mock_result

    with patch("app.domain.wellness_evaluator.GeminiClient", return_value=mock_llm):
        wellness_sample = [{"id": "2026-08-01", "hrv": 60, "restingHR": 50, "sleepQuality": 2, "feeling": 2}]
        needs_revision, reason, decision, overrides = await WellnessEvaluator.evaluate_daily_readiness(
            wellness_data=wellness_sample,
            activities_data=[],
            planned_today=[]
        )
        assert needs_revision is True
        assert "Niska zmienność HRV" in reason

@pytest.mark.asyncio
async def test_wellness_evaluator_fallback_on_exception():
    mock_llm = AsyncMock()
    mock_llm.generate_structured.side_effect = Exception("API Unavailable")

    with patch("app.domain.wellness_evaluator.GeminiClient", return_value=mock_llm):
        # Symulacja złego samopoczucia w wpisie (feeling = 4)
        wellness_sample = [{"id": "2026-08-01", "hrv": 60, "restingHR": 50, "sleepQuality": 4, "feeling": 4}]
        needs_revision, reason, decision, overrides = await WellnessEvaluator.evaluate_daily_readiness(
            wellness_data=wellness_sample,
            activities_data=[],
            planned_today=[]
        )
        assert needs_revision is True
        assert "POOR_SUBJECTIVE_WELLNESS" in overrides or "Fallback" in reason

