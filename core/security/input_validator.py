"""
Input validation and sanitization utilities.
Protects against injection attacks and invalid data.
"""

import re
from pathlib import Path
from typing import Any


class InputValidator:
    """Validates and sanitizes user inputs."""
    
    # Trading pair validation pattern (e.g., BTC/USD, ETH/USDT)
    PAIR_PATTERN = re.compile(r'^[A-Z0-9]{2,10}/[A-Z0-9]{2,10}$')
    
    # Safe filename pattern (alphanumeric, dash, underscore, dot)
    FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
    
    # Numeric patterns
    POSITIVE_NUMBER_PATTERN = re.compile(r'^\d+\.?\d*$')
    
    @staticmethod
    def validate_trading_pair(pair: str) -> str:
        """
        Validate and sanitize a trading pair.
        
        Args:
            pair: Trading pair string (e.g., 'BTC/USD')
            
        Returns:
            Validated trading pair
            
        Raises:
            ValueError: If pair is invalid
        """
        if not isinstance(pair, str):
            raise ValueError("Trading pair must be a string")
        
        pair = pair.strip().upper()
        
        if not InputValidator.PAIR_PATTERN.match(pair):
            raise ValueError(
                f"Invalid trading pair format: {pair}. "
                "Expected format: SYMBOL/SYMBOL (e.g., BTC/USD)"
            )
        
        return pair
    
    @staticmethod
    def validate_positive_number(value: Any, name: str = "value") -> float:
        """
        Validate a positive number.
        
        Args:
            value: Value to validate
            name: Name of the parameter for error messages
            
        Returns:
            Validated float value
            
        Raises:
            ValueError: If value is not a positive number
        """
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{name} must be a number")
        
        if num <= 0:
            raise ValueError(f"{name} must be positive")
        
        if not isinstance(num, (int, float)) or num != num:  # Check for NaN
            raise ValueError(f"{name} must be a valid number")
        
        return num
    
    @staticmethod
    def validate_percentage(value: Any, name: str = "value") -> float:
        """
        Validate a percentage value (0-100).
        
        Args:
            value: Value to validate
            name: Name of the parameter for error messages
            
        Returns:
            Validated float value
            
        Raises:
            ValueError: If value is not a valid percentage
        """
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{name} must be a number")
        
        if num < 0 or num > 100:
            raise ValueError(f"{name} must be between 0 and 100")
        
        if not isinstance(num, (int, float)) or num != num:  # Check for NaN
            raise ValueError(f"{name} must be a valid number")
        
        return num
    
    @staticmethod
    def validate_integer(value: Any, name: str = "value", min_val: int | None = None, max_val: int | None = None) -> int:
        """
        Validate an integer value.
        
        Args:
            value: Value to validate
            name: Name of the parameter for error messages
            min_val: Minimum allowed value (optional)
            max_val: Maximum allowed value (optional)
            
        Returns:
            Validated integer value
            
        Raises:
            ValueError: If value is not a valid integer
        """
        try:
            num = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{name} must be an integer")
        
        if min_val is not None and num < min_val:
            raise ValueError(f"{name} must be at least {min_val}")
        
        if max_val is not None and num > max_val:
            raise ValueError(f"{name} must be at most {max_val}")
        
        return num
    
    @staticmethod
    def validate_path(file_path: str, base_dir: str | None = None) -> Path:
        """
        Validate a file path and protect against path traversal attacks.
        
        Args:
            file_path: Path to validate
            base_dir: Base directory to restrict paths to (optional)
            
        Returns:
            Validated Path object
            
        Raises:
            ValueError: If path is invalid or attempts traversal
        """
        if not isinstance(file_path, str):
            raise ValueError("File path must be a string")
        
        # Prevent path traversal
        if ".." in file_path or file_path.startswith("/"):
            raise ValueError("Invalid file path: path traversal not allowed")
        
        path = Path(file_path).resolve()
        
        # If base directory is specified, ensure path is within it
        if base_dir:
            base = Path(base_dir).resolve()
            try:
                path.relative_to(base)
            except ValueError:
                raise ValueError(f"Path must be within {base_dir}")
        
        return path
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename to prevent injection attacks.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
            
        Raises:
            ValueError: If filename contains invalid characters
        """
        if not isinstance(filename, str):
            raise ValueError("Filename must be a string")
        
        filename = filename.strip()
        
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        if not InputValidator.FILENAME_PATTERN.match(filename):
            raise ValueError(
                "Filename contains invalid characters. "
                "Only alphanumeric, dash, underscore, and dot allowed."
            )
        
        # Additional security checks
        if filename in (".", ".."):
            raise ValueError("Invalid filename")
        
        return filename
    
    @staticmethod
    def validate_json_object(data: Any) -> dict:
        """
        Validate that data is a dictionary.
        
        Args:
            data: Data to validate
            
        Returns:
            Validated dictionary
            
        Raises:
            ValueError: If data is not a dictionary
        """
        if not isinstance(data, dict):
            raise ValueError("Expected JSON object")
        
        return data
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize a string input.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
            
        Raises:
            ValueError: If value is not a string or exceeds max length
        """
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        
        value = value.strip()
        
        if len(value) > max_length:
            raise ValueError(f"String exceeds maximum length of {max_length}")
        
        return value
