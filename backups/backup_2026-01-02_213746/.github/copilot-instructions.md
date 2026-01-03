# Grid Trading Bot AI Instructions

## 🏗️ Architecture Overview

This project is a modular, event-driven cryptocurrency grid trading bot.

- **Core Orchestrator**: `GridTradingBot` (`core/bot_management/grid_trading_bot.py`) initializes components and manages the lifecycle.
- **Event System**: `EventBus` (`core/bot_management/event_bus.py`) decouples components. Use `event_bus.subscribe(Events.EVENT_NAME, callback)` and `event_bus.publish(Events.EVENT_NAME, data)`.
- **Configuration**: `ConfigManager` (`config/config_manager.py`) validates and provides typed access to `config.json`.
- **Strategies**: Implement `TradingStrategyInterface` (`strategies/trading_strategy_interface.py`). Logic resides in `strategies/`.
- **Order Management**: `OrderManager` handles placement/cancellation. `OrderStatusTracker` polls for updates. `BalanceTracker` maintains local state.
- **API**: `BotAPIIntegration` (`core/bot_management/bot_api_integration.py`) provides a REST API for the dashboard.

## 🚀 Key Workflows

- **Run Bot**: `python main.py --config config/config.json`
- **Run Dashboard**: `python dashboard_launcher.py` or `./dashboard_launcher.ps1`
- **Run Tests**: `pytest` (Async tests supported via `pytest-asyncio`)
- **Linting**: `pre-commit run --all-files`

## 🧩 Coding Conventions & Patterns

- **Asyncio**: The bot is heavily async. Use `async/await` for I/O bound operations (API calls, DB).
- **Dependency Injection**: Pass dependencies (ConfigManager, EventBus, etc.) via `__init__`. Avoid global state.
- **Factories**: Use factories for creating complex objects (e.g., `ExchangeServiceFactory`).
- **Type Hinting**: Use Python type hints strictly.
- **Logging**: Use `logging.getLogger(self.__class__.__name__)`.
- **Configuration**: Do not hardcode values. Add them to `config.json` and expose via `ConfigManager`.

## 📂 Important Files

- `main.py`: Application entry point.
- `config/config.json`: Main configuration file.
- `core/bot_management/event_bus.py`: Event definitions and bus implementation.
- `core/grid_management/grid_manager.py`: Grid level calculation logic.
- `strategies/grid_trading_strategy.py`: Implementation of the grid strategy.

## 🧪 Testing

- Place tests in `tests/`.
- Use `pytest` fixtures for `EventBus` and `ConfigManager`.
- Mock external exchange calls using `unittest.mock` or custom mocks.
