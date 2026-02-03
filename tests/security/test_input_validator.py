"""Tests for input validation."""

import pytest

from core.security.input_validator import InputValidator


class TestInputValidator:
    """Test suite for InputValidator."""

    def test_validate_trading_pair_valid(self):
        """Test valid trading pairs."""
        assert InputValidator.validate_trading_pair("BTC/USD") == "BTC/USD"
        assert InputValidator.validate_trading_pair("btc/usd") == "BTC/USD"
        assert InputValidator.validate_trading_pair("ETH/USDT") == "ETH/USDT"
        assert InputValidator.validate_trading_pair("XRP123/USD456") == "XRP123/USD456"

    def test_validate_trading_pair_invalid(self):
        """Test invalid trading pairs."""
        with pytest.raises(ValueError, match="Invalid trading pair format"):
            InputValidator.validate_trading_pair("BTCUSD")
        
        with pytest.raises(ValueError, match="Invalid trading pair format"):
            InputValidator.validate_trading_pair("BTC/USD/EUR")
        
        with pytest.raises(ValueError, match="Invalid trading pair format"):
            InputValidator.validate_trading_pair("BTC-USD")
        
        with pytest.raises(ValueError, match="must be a string"):
            InputValidator.validate_trading_pair(123)

    def test_validate_positive_number_valid(self):
        """Test valid positive numbers."""
        assert InputValidator.validate_positive_number(1.5) == 1.5
        assert InputValidator.validate_positive_number("2.5") == 2.5
        assert InputValidator.validate_positive_number(100) == 100.0

    def test_validate_positive_number_invalid(self):
        """Test invalid numbers."""
        with pytest.raises(ValueError, match="must be positive"):
            InputValidator.validate_positive_number(0)
        
        with pytest.raises(ValueError, match="must be positive"):
            InputValidator.validate_positive_number(-1.5)
        
        with pytest.raises(ValueError, match="must be a number"):
            InputValidator.validate_positive_number("invalid")

    def test_validate_percentage_valid(self):
        """Test valid percentages."""
        assert InputValidator.validate_percentage(50) == 50
        assert InputValidator.validate_percentage(0.5) == 0.5
        assert InputValidator.validate_percentage(100) == 100

    def test_validate_percentage_invalid(self):
        """Test invalid percentages."""
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            InputValidator.validate_percentage(150)
        
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            InputValidator.validate_percentage(-10)

    def test_validate_integer_valid(self):
        """Test valid integers."""
        assert InputValidator.validate_integer(5) == 5
        assert InputValidator.validate_integer("10") == 10
        assert InputValidator.validate_integer(7, min_val=5, max_val=10) == 7

    def test_validate_integer_invalid(self):
        """Test invalid integers."""
        with pytest.raises(ValueError, match="must be an integer"):
            InputValidator.validate_integer("invalid")
        
        with pytest.raises(ValueError, match="must be at least 5"):
            InputValidator.validate_integer(3, min_val=5)
        
        with pytest.raises(ValueError, match="must be at most 10"):
            InputValidator.validate_integer(15, max_val=10)

    def test_validate_path_valid(self):
        """Test valid paths."""
        path = InputValidator.validate_path("config/test.json")
        assert path.name == "test.json"

    def test_validate_path_traversal(self):
        """Test path traversal protection."""
        with pytest.raises(ValueError, match="path traversal not allowed"):
            InputValidator.validate_path("../etc/passwd")
        
        with pytest.raises(ValueError, match="path traversal not allowed"):
            InputValidator.validate_path("/etc/passwd")

    def test_sanitize_filename_valid(self):
        """Test valid filenames."""
        assert InputValidator.sanitize_filename("test.json") == "test.json"
        assert InputValidator.sanitize_filename("my-config_v1.0.json") == "my-config_v1.0.json"

    def test_sanitize_filename_invalid(self):
        """Test invalid filenames."""
        with pytest.raises(ValueError, match="invalid characters"):
            InputValidator.sanitize_filename("test/file.json")
        
        with pytest.raises(ValueError, match="invalid characters"):
            InputValidator.sanitize_filename("test<script>.json")
        
        with pytest.raises(ValueError, match="Invalid filename"):
            InputValidator.sanitize_filename("..")

    def test_sanitize_string_valid(self):
        """Test valid strings."""
        assert InputValidator.sanitize_string("  test  ") == "test"
        assert InputValidator.sanitize_string("valid string", max_length=20) == "valid string"

    def test_sanitize_string_invalid(self):
        """Test invalid strings."""
        with pytest.raises(ValueError, match="exceeds maximum length"):
            InputValidator.sanitize_string("a" * 1001)
        
        with pytest.raises(ValueError, match="must be a string"):
            InputValidator.sanitize_string(123)

    def test_sql_injection_protection(self):
        """Test that malicious SQL is not executed."""
        # These should raise validation errors, not execute SQL
        malicious_pairs = [
            "'; DROP TABLE orders; --",
            "BTC/USD' OR '1'='1",
            "' UNION SELECT * FROM users --"
        ]
        
        for pair in malicious_pairs:
            with pytest.raises(ValueError):
                InputValidator.validate_trading_pair(pair)
