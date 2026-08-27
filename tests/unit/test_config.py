"""Unit tests for configuration loading."""

from apps.api.config import Settings


def test_settings_default_values():
    settings = Settings(_env_file=None)
    assert settings.API_PORT == 8000
    assert settings.API_V1_PREFIX == "/api/v1"
    assert "redis" in settings.REDIS_URL
    assert settings.APP_NAME == "RazorFlow-API"
