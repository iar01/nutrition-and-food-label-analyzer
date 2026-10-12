"""Smoke test for LLM connectivity using OpenAI-compatible endpoint."""

import pytest
from labellens.config import get_settings
from openai import APIConnectionError, NotFoundError, OpenAI


@pytest.mark.smoke
def test_ollama_llm_smoke() -> None:
    """Smoke test: send a 1-sentence prompt to the OpenAI-compatible endpoint."""
    settings = get_settings()
    client = OpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        timeout=30.0,
    )

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": "Respond with the word 'READY' only."}],
            temperature=0.0,
            max_tokens=10,
        )
        content = response.choices[0].message.content or ""
        print(f"\n[Smoke Test Success] Model '{settings.llm_model}' reply: {content.strip()}")
        assert len(content.strip()) > 0
    except (APIConnectionError, NotFoundError) as exc:
        pytest.skip(
            f"LLM endpoint at {settings.llm_base_url} is not ready or model '{settings.llm_model}' not found: {exc}. "
            f"Start Ollama and pull model with 'ollama pull {settings.llm_model}'."
        )


if __name__ == "__main__":
    test_ollama_llm_smoke()
