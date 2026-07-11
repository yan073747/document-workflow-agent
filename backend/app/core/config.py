from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMSettings:
    provider: str = "local"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "LLMSettings":
        return cls(
            provider=os.getenv("LLM_PROVIDER", "local").strip().lower() or "local",
            api_key=os.getenv("LLM_API_KEY", "").strip(),
            base_url=os.getenv("LLM_BASE_URL", "").strip(),
            model=os.getenv("LLM_MODEL", "").strip(),
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
        )

    @property
    def is_remote_provider(self) -> bool:
        return self.provider in {"deepseek", "openai", "openai-compatible"}

    @property
    def is_enabled(self) -> bool:
        return self.is_remote_provider and bool(self.api_key)

    @property
    def resolved_base_url(self) -> str:
        if self.base_url:
            return self.base_url.rstrip("/")
        if self.provider == "deepseek":
            return "https://api.deepseek.com"
        if self.provider == "openai":
            return "https://api.openai.com/v1"
        return ""

    @property
    def resolved_model(self) -> str:
        if self.model:
            return self.model
        if self.provider == "deepseek":
            return "deepseek-chat"
        if self.provider == "openai":
            return "gpt-4o-mini"
        return "local-rules"

    def status(self) -> dict[str, object]:
        reason = ""
        if self.provider == "local":
            reason = "LLM_PROVIDER=local，使用本地规则。"
        elif not self.is_remote_provider:
            reason = f"未知 provider：{self.provider}，使用本地规则。"
        elif not self.api_key:
            reason = "未配置 LLM_API_KEY，使用本地规则回退。"
        else:
            reason = "远程 LLM 已启用。"

        return {
            "provider": self.provider,
            "model": self.resolved_model,
            "base_url": self.resolved_base_url,
            "enabled": self.is_enabled,
            "fallback_reason": reason,
        }
