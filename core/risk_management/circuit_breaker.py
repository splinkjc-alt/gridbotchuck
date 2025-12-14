"""
Circuit Breaker - Stops trading when too many failures occur.
Protects against cascading failures and runaway losses.
"""

import asyncio
from enum import Enum
import logging
import time
from typing import Callable, Any


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking all operations
    HALF_OPEN = "half_open"  # Testing if system recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Circuit breaker pattern for protecting against cascading failures.

    When failures exceed threshold, circuit "opens" and blocks all operations.
    After recovery timeout, allows test operations ("half-open").
    If test succeeds, circuit "closes" and normal operation resumes.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        name: str = "CircuitBreaker",
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            success_threshold: Consecutive successes needed to close circuit from half-open
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.name = name
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()
        self.total_failures = 0
        self.total_successes = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute (can be sync or async)
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result of function call

        Raises:
            CircuitBreakerError: If circuit is open
        """
        # Check current state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self.logger.info(f"🔧 Circuit {self.name} entering HALF-OPEN state (testing recovery)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                time_until_recovery = self.recovery_timeout - (time.time() - self.last_failure_time)
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Will retry in {time_until_recovery:.0f}s. "
                    f"({self.failure_count} failures)"
                )

        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self):
        """Handle successful operation."""
        self.total_successes += 1

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            self.logger.debug(
                f"Circuit {self.name} half-open success " f"({self.success_count}/{self.success_threshold})"
            )

            if self.success_count >= self.success_threshold:
                self.logger.info(
                    f"✅ Circuit {self.name} CLOSED (recovered after " f"{self.total_failures} total failures)"
                )
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.last_state_change = time.time()
        else:
            # In CLOSED state, reset failure count on success
            if self.failure_count > 0:
                self.logger.debug(f"Circuit {self.name} success, resetting failure count from {self.failure_count} to 0")
                self.failure_count = 0

    def _on_failure(self, error: Exception):
        """Handle failed operation."""
        self.failure_count += 1
        self.total_failures += 1
        self.last_failure_time = time.time()

        self.logger.warning(f"Circuit {self.name} failure #{self.failure_count}: {error}")

        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery test - go back to OPEN
            self.logger.error(
                f"❌ Circuit {self.name} OPENED (recovery test failed). " f"Will retry in {self.recovery_timeout}s"
            )
            self.state = CircuitState.OPEN
            self.success_count = 0
            self.last_state_change = time.time()

        elif self.failure_count >= self.failure_threshold:
            # Too many failures - open the circuit
            self.logger.error(
                f"🚨 Circuit {self.name} OPENED ({self.failure_count} failures). " f"Trading halted for {self.recovery_timeout}s"
            )
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True

        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        self.logger.info(f"🔄 Circuit {self.name} manually reset to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        uptime = time.time() - self.last_state_change

        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "success_rate": (
                self.total_successes / (self.total_successes + self.total_failures) * 100
                if (self.total_successes + self.total_failures) > 0
                else 0
            ),
            "time_in_current_state": uptime,
            "recovery_timeout": self.recovery_timeout,
        }


class TradingCircuitBreaker(CircuitBreaker):
    """
    Specialized circuit breaker for trading operations.
    Monitors losses and stops trading if losses exceed threshold.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 300,  # 5 minutes
        max_loss_percent: float = 10.0,  # Stop if 10% loss
        max_loss_absolute: float = None,  # Stop if losing this much $
        name: str = "TradingBreaker",
    ):
        super().__init__(failure_threshold, recovery_timeout, name=name)
        self.max_loss_percent = max_loss_percent
        self.max_loss_absolute = max_loss_absolute
        self.initial_balance = None
        self.current_balance = None

    def check_balance(self, current_balance: float, initial_balance: float = None):
        """
        Check if current balance triggers circuit breaker.

        Args:
            current_balance: Current account balance
            initial_balance: Starting balance (optional, uses first value if not set)
        """
        if initial_balance:
            self.initial_balance = initial_balance

        if self.initial_balance is None:
            self.initial_balance = current_balance

        self.current_balance = current_balance
        loss = self.initial_balance - current_balance
        loss_percent = (loss / self.initial_balance) * 100 if self.initial_balance > 0 else 0

        # Check percentage loss
        if self.max_loss_percent and loss_percent >= self.max_loss_percent:
            self.logger.error(
                f"🚨 LOSS LIMIT EXCEEDED: {loss_percent:.1f}% loss " f"(${loss:.2f}). Opening circuit breaker!"
            )
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()
            self.last_state_change = time.time()
            return False

        # Check absolute loss
        if self.max_loss_absolute and loss >= self.max_loss_absolute:
            self.logger.error(
                f"🚨 LOSS LIMIT EXCEEDED: ${loss:.2f} loss " f"(limit: ${self.max_loss_absolute}). Opening circuit breaker!"
            )
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()
            self.last_state_change = time.time()
            return False

        return True

    def get_stats(self) -> dict:
        """Get trading circuit breaker statistics."""
        stats = super().get_stats()

        if self.initial_balance and self.current_balance:
            loss = self.initial_balance - self.current_balance
            loss_percent = (loss / self.initial_balance) * 100

            stats.update(
                {
                    "initial_balance": self.initial_balance,
                    "current_balance": self.current_balance,
                    "loss": loss,
                    "loss_percent": loss_percent,
                    "max_loss_percent": self.max_loss_percent,
                    "max_loss_absolute": self.max_loss_absolute,
                }
            )

        return stats
