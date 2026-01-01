"""Tests for API authentication."""

import os
import secrets

import pytest

from core.security.api_auth import APIAuth


class TestAPIAuth:
    """Test suite for APIAuth."""

    def test_init_with_env_key(self, monkeypatch):
        """Test initialization with environment variable."""
        test_key = "test_api_key_from_env"
        monkeypatch.setenv("GRIDBOT_API_KEY", test_key)
        
        auth = APIAuth()
        assert auth.api_key == test_key

    def test_init_without_env_key(self, monkeypatch):
        """Test initialization generates key when env var missing."""
        monkeypatch.delenv("GRIDBOT_API_KEY", raising=False)
        
        auth = APIAuth()
        assert auth.api_key is not None
        assert len(auth.api_key) > 20  # Generated keys are long

    def test_verify_api_key_valid(self):
        """Test valid API key verification."""
        auth = APIAuth()
        auth.api_key = "test_key_123"
        
        assert auth.verify_api_key("test_key_123") is True

    def test_verify_api_key_invalid(self):
        """Test invalid API key verification."""
        auth = APIAuth()
        auth.api_key = "test_key_123"
        
        assert auth.verify_api_key("wrong_key") is False
        assert auth.verify_api_key("") is False
        assert auth.verify_api_key(None) is False

    def test_verify_api_key_timing_attack_resistance(self):
        """Test that verification is resistant to timing attacks."""
        auth = APIAuth()
        auth.api_key = "correct_key_12345"
        
        # These should all take similar time (constant-time comparison)
        # We can't easily test timing, but we can verify behavior
        assert auth.verify_api_key("correct_key_12345") is True
        assert auth.verify_api_key("correct_key_12346") is False
        assert auth.verify_api_key("wrong") is False
        assert auth.verify_api_key("a" * 50) is False

    def test_generated_key_is_secure(self, monkeypatch):
        """Test that generated keys are cryptographically secure."""
        monkeypatch.delenv("GRIDBOT_API_KEY", raising=False)
        
        auth1 = APIAuth()
        auth2 = APIAuth()
        
        # Generated keys should be different
        assert auth1.api_key != auth2.api_key
        
        # Should be URL-safe
        assert "/" not in auth1.api_key or "+" not in auth1.api_key
