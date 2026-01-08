import json
import logging
import os

from strategies.spacing_type import SpacingType
from strategies.strategy_type import StrategyType

from .exceptions import ConfigFileNotFoundError, ConfigParseError
from .trading_mode import TradingMode


class ConfigManager:
    def __init__(self, config_file, config_validator):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = config_file
        self.config_validator = config_validator
        self.config = None
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.logger.error(f"Config file {self.config_file} does not exist.")
            raise ConfigFileNotFoundError(self.config_file)

        with open(self.config_file) as file:
            try:
                self.config = json.load(file)
                self.config_validator.validate(self.config)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse config file {self.config_file}: {e}")
                raise ConfigParseError(self.config_file, e) from e

    def get(self, key, default=None):
        return self.config.get(key, default)

    # --- General Accessor Methods ---
    def get_exchange(self):
        return self.config.get("exchange", {})

    def get_exchange_name(self):
        exchange = self.get_exchange()
        return exchange.get("name", None)

    def get_trading_fee(self):
        exchange = self.get_exchange()
        return exchange.get("trading_fee", 0)

    def get_trading_mode(self) -> TradingMode | None:
        exchange = self.get_exchange()
        trading_mode = exchange.get("trading_mode", None)

        if trading_mode:
            return TradingMode.from_string(trading_mode)

    def get_pair(self):
        return self.config.get("pair", {})

    def get_base_currency(self):
        pair = self.get_pair()
        return pair.get("base_currency", None)

    def get_quote_currency(self):
        pair = self.get_pair()
        return pair.get("quote_currency", None)

    def get_trading_pair(self):
        base = self.get_base_currency()
        quote = self.get_quote_currency()
        if base and quote:
            return f"{base}/{quote}"
        return None

    def get_trading_settings(self):
        return self.config.get("trading_settings", {})

    def get_timeframe(self):
        trading_settings = self.get_trading_settings()
        return trading_settings.get("timeframe", "1h")

    def get_period(self):
        trading_settings = self.get_trading_settings()
        return trading_settings.get("period", {})

    def get_start_date(self):
        period = self.get_period()
        return period.get("start_date", None)

    def get_end_date(self):
        period = self.get_period()
        return period.get("end_date", None)

    def get_initial_balance(self):
        trading_settings = self.get_trading_settings()
        return trading_settings.get("initial_balance", 10000)

    def get_initial_crypto_balance(self):
        trading_settings = self.get_trading_settings()
        return trading_settings.get("initial_crypto_balance", 0.0)

    def get_historical_data_file(self):
        trading_settings = self.get_trading_settings()
        return trading_settings.get("historical_data_file", None)

    # --- Grid Accessor Methods ---
    def get_grid_settings(self):
        return self.config.get("grid_strategy", {})

    def get_strategy_type(self) -> StrategyType | None:
        grid_settings = self.get_grid_settings()
        strategy_type = grid_settings.get("type", None)

        if strategy_type:
            return StrategyType.from_string(strategy_type)

    def get_spacing_type(self) -> SpacingType | None:
        grid_settings = self.get_grid_settings()
        spacing_type = grid_settings.get("spacing", None)

        if spacing_type:
            return SpacingType.from_string(spacing_type)

    def get_num_grids(self):
        grid_settings = self.get_grid_settings()
        return grid_settings.get("num_grids", None)

    def get_grid_range(self):
        grid_settings = self.get_grid_settings()
        return grid_settings.get("range", {})

    def get_top_range(self):
        grid_range = self.get_grid_range()
        return grid_range.get("top", None)

    def get_bottom_range(self):
        grid_range = self.get_grid_range()
        return grid_range.get("bottom", None)

    # --- Market Scanner Accessor Methods ---
    def get_market_scanner_config(self) -> dict:
        """Get market scanner configuration."""
        return self.config.get("market_scanner", {})

    # --- Risk management (Take Profit / Stop Loss) Accessor Methods ---
    def get_risk_management(self):
        return self.config.get("risk_management", {})

    def get_risk_management_config(self) -> dict:
        """Alias for get_risk_management for compatibility."""
        return self.get_risk_management()

    def get_take_profit(self):
        risk_management = self.get_risk_management()
        return risk_management.get("take_profit", {})

    def is_take_profit_enabled(self):
        take_profit = self.get_take_profit()
        return take_profit.get("enabled", False)

    def get_take_profit_threshold(self):
        take_profit = self.get_take_profit()
        return take_profit.get("threshold", None)

    def get_stop_loss(self):
        risk_management = self.get_risk_management()
        return risk_management.get("stop_loss", {})

    def is_stop_loss_enabled(self):
        stop_loss = self.get_stop_loss()
        return stop_loss.get("enabled", False)

    def get_stop_loss_threshold(self):
        stop_loss = self.get_stop_loss()
        return stop_loss.get("threshold", None)

    # --- Logging Accessor Methods ---
    def get_logging(self):
        return self.config.get("logging", {})

    def get_logging_level(self):
        logging = self.get_logging()
        return logging.get("log_level", {})

    def should_log_to_file(self) -> bool:
        logging = self.get_logging()
        return logging.get("log_to_file", False)

    # --- Multi-Timeframe Analysis Accessor Methods ---
    def get_multi_timeframe_analysis(self) -> dict:
        """Get multi-timeframe analysis configuration."""
        return self.config.get("multi_timeframe_analysis", {})

    def is_multi_timeframe_analysis_enabled(self) -> bool:
        """Check if multi-timeframe analysis is enabled."""
        mtf = self.get_multi_timeframe_analysis()
        return mtf.get("enabled", False)

    def get_mtf_timeframes(self) -> dict[str, str]:
        """Get configured timeframes for multi-timeframe analysis."""
        mtf = self.get_multi_timeframe_analysis()
        return mtf.get("timeframes", {"trend": "1d", "config": "4h", "execution": "1h"})

    def get_mtf_trend_filter(self) -> dict:
        """Get trend filter settings."""
        mtf = self.get_multi_timeframe_analysis()
        return mtf.get(
            "trend_filter",
            {
                "enabled": True,
                "pause_on_strong_trend": True,
                "strong_trend_threshold": 75,
                "warn_on_moderate_trend": True,
                "moderate_trend_threshold": 40,
            },
        )

    def is_trend_filter_enabled(self) -> bool:
        """Check if trend filter is enabled."""
        trend_filter = self.get_mtf_trend_filter()
        return trend_filter.get("enabled", True)

    def should_pause_on_strong_trend(self) -> bool:
        """Check if bot should pause on strong trends."""
        trend_filter = self.get_mtf_trend_filter()
        return trend_filter.get("pause_on_strong_trend", True)

    def get_strong_trend_threshold(self) -> float:
        """Get threshold for strong trend detection."""
        trend_filter = self.get_mtf_trend_filter()
        return trend_filter.get("strong_trend_threshold", 75)

    def get_moderate_trend_threshold(self) -> float:
        """Get threshold for moderate trend detection."""
        trend_filter = self.get_mtf_trend_filter()
        return trend_filter.get("moderate_trend_threshold", 40)

    def get_mtf_volatility_spacing(self) -> dict:
        """Get volatility-based spacing settings."""
        mtf = self.get_multi_timeframe_analysis()
        return mtf.get(
            "volatility_spacing",
            {
                "enabled": True,
                "high_volatility_multiplier": 1.5,
                "low_volatility_multiplier": 0.75,
                "high_volatility_percentile": 80,
                "low_volatility_percentile": 20,
            },
        )

    def is_volatility_spacing_enabled(self) -> bool:
        """Check if volatility-based spacing adjustment is enabled."""
        vol_spacing = self.get_mtf_volatility_spacing()
        return vol_spacing.get("enabled", True)

    def get_mtf_range_validation(self) -> dict:
        """Get range validation settings."""
        mtf = self.get_multi_timeframe_analysis()
        return mtf.get(
            "range_validation", {"enabled": True, "auto_suggest_range": True, "warn_if_price_outside_range": True}
        )

    def is_range_validation_enabled(self) -> bool:
        """Check if range validation is enabled."""
        range_val = self.get_mtf_range_validation()
        return range_val.get("enabled", True)

    def get_mtf_analysis_interval_minutes(self) -> int:
        """Get how often to run multi-timeframe analysis."""
        mtf = self.get_multi_timeframe_analysis()
        return mtf.get("analysis_interval_minutes", 30)
