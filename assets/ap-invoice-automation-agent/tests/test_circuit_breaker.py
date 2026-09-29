"""Tests for circuit_breaker module."""
import asyncio
import pytest
from circuit_breaker import CircuitBreaker


@pytest.fixture
def breaker():
    return CircuitBreaker(failure_threshold=3, cooldown_seconds=1.0)


@pytest.mark.asyncio
async def test_circuit_breaker_allows_initially(breaker):
    """Circuit breaker allows requests when closed."""
    allowed = await breaker.allows("model-a")
    assert allowed is True


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold(breaker):
    """Circuit breaker opens after reaching failure threshold."""
    for _ in range(3):
        await breaker.record_failure("model-a")
    allowed = await breaker.allows("model-a")
    assert allowed is False


@pytest.mark.asyncio
async def test_circuit_breaker_success_resets_failures(breaker):
    """Recording a success resets the failure count."""
    await breaker.record_failure("model-a")
    await breaker.record_failure("model-a")
    await breaker.record_success("model-a")
    # After success, failure count resets — one more failure shouldn't open the breaker
    await breaker.record_failure("model-a")
    allowed = await breaker.allows("model-a")
    assert allowed is True


@pytest.mark.asyncio
async def test_circuit_breaker_different_models_isolated(breaker):
    """Circuit breaker state is isolated per model."""
    for _ in range(3):
        await breaker.record_failure("model-a")
    # model-b should not be affected
    allowed = await breaker.allows("model-b")
    assert allowed is True


@pytest.mark.asyncio
async def test_circuit_breaker_unknown_model_allowed(breaker):
    """Unknown (never-seen) model is allowed by default."""
    allowed = await breaker.allows("never-used-model")
    assert allowed is True


@pytest.mark.asyncio
async def test_circuit_breaker_recovers_after_cooldown(breaker):
    """Circuit breaker allows a probe request after cooldown period."""
    for _ in range(3):
        await breaker.record_failure("model-x")
    assert await breaker.allows("model-x") is False
    # Wait for cooldown
    await asyncio.sleep(1.1)
    # Should allow one probe attempt
    allowed = await breaker.allows("model-x")
    assert allowed is True
