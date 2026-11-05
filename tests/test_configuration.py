from pathlib import Path

from config import Settings


def test_empty_credentials_use_safe_defaults(tmp_path: Path):
    settings = Settings.load(tmp_path / "missing.env")
    assert settings.gemini_api_key == ""
    assert settings.minimum_match_score == 7
    assert settings.require_approval is True
    assert settings.status()["AI"].startswith("Mock mode")
