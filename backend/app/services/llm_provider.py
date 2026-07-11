from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import LLMSettings


class LLMUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str


class LLMClient:
    """Small OpenAI-compatible adapter with local fallback handled by callers."""

    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings.from_env()

    def status(self) -> dict[str, object]:
        return self.settings.status()

    def complete(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> LLMResult:
        if not self.settings.is_enabled:
            raise LLMUnavailableError(str(self.settings.status()["fallback_reason"]))

        base_url = self.settings.resolved_base_url
        if not base_url:
            raise LLMUnavailableError("LLM_BASE_URL is required for this provider.")

        url = f"{base_url}/chat/completions"
        payload = {
            "model": self.settings.resolved_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.settings.timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMUnavailableError(f"LLM request failed: {exc}") from exc

        data = response.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMUnavailableError("LLM response does not match OpenAI-compatible format.") from exc

        if not isinstance(text, str) or not text.strip():
            raise LLMUnavailableError("LLM returned empty content.")

        return LLMResult(
            text=text.strip(),
            provider=self.settings.provider,
            model=self.settings.resolved_model,
        )
